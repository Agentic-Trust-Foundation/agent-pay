"""Persistent financial-control repositories for policy and approval decisions."""
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

from .approval import ApprovalBinding
from .domain import Decision, Money, PaymentIntent
from .policy import PolicyDecision, SpendingPolicy


class ControlRepository:
    def __init__(self, conn):
        self.conn = conn

    def active_policy(self, account_id: UUID, policy_id: UUID | None = None):
        if policy_id:
            return self.conn.execute(
                """SELECT p.id, pv.id, pv.version, pv.rules FROM policies p
                   JOIN policy_versions pv ON pv.policy_id=p.id
                   WHERE p.id=%s AND p.account_id=%s AND p.status='ACTIVE' AND pv.status='ACTIVE'
                   ORDER BY pv.version DESC LIMIT 1""", (policy_id, account_id)).fetchone()
        return self.conn.execute(
            """SELECT p.id, pv.id, pv.version, pv.rules FROM policies p
               JOIN policy_versions pv ON pv.policy_id=p.id
               WHERE p.account_id=%s AND p.status='ACTIVE' AND pv.status='ACTIVE'
               ORDER BY p.updated_at DESC, pv.version DESC LIMIT 1""", (account_id,)).fetchone()

    def evaluate_policy(self, *, account_id: UUID, policy_id: UUID | None,
                        payment_request_id: UUID, agent_id: UUID, payment_id: UUID,
                        amount: Decimal, currency: str, merchant_domain: str,
                        category: str | None):
        row = self.active_policy(account_id, policy_id)
        if not row:
            return Decision.DENY, None, None, {"decision": "DENY", "reasons": ["NO_ACTIVE_POLICY"], "evaluated_rules": []}
        _, version_id, version, rules = row
        intent = PaymentIntent(str(payment_id), str(agent_id), Money(amount, currency), merchant_domain, "")
        result: PolicyDecision = SpendingPolicy.from_rules(rules).evaluate_with_trace(
            intent, category=category, policy_version=f"{version_id}:v{version}"
        )
        self.conn.execute("UPDATE payment_requests SET policy_version_id=%s WHERE id=%s", (version_id, payment_request_id))
        return result.decision, version_id, version, result.evidence()

    def select_budget(self, account_id: UUID, budget_id: UUID | None, currency: str, policy_id: UUID | None):
        if budget_id:
            row = self.conn.execute(
                """SELECT id FROM budgets WHERE id=%s AND account_id=%s AND currency=%s
                   AND status='ACTIVE' AND (policy_id=%s OR policy_id IS NULL)""",
                (budget_id, account_id, currency, policy_id)).fetchone()
            return row[0] if row else None
        rows = self.conn.execute(
            """SELECT id FROM budgets WHERE account_id=%s AND currency=%s AND status='ACTIVE'
               AND (policy_id=%s OR policy_id IS NULL) ORDER BY created_at""",
            (account_id, currency, policy_id)).fetchall()
        return rows[0][0] if len(rows) == 1 else None

    def bind_budget(self, payment_request_id: UUID, budget_id: UUID) -> None:
        self.conn.execute("UPDATE payment_requests SET budget_id=%s WHERE id=%s", (budget_id, payment_request_id))

    def create_approval(self, payment_request_id: UUID, *, reason: str | None = None,
                        expires_minutes: int = 15) -> UUID:
        req = self.conn.execute(
            """SELECT pr.account_id, pr.agent_id, pr.amount, pr.currency, pr.policy_version_id,
                      pr.authorization_evidence_id, m.domain
               FROM payment_requests pr LEFT JOIN merchants m ON m.id=pr.merchant_id
               WHERE pr.id=%s""", (payment_request_id,)).fetchone()
        if not req:
            raise LookupError("payment request not found")
        binding = ApprovalBinding(
            str(payment_request_id), str(req[0]), str(req[1]), Decimal(str(req[2])),
            req[3].strip(), req[6], str(req[4]) if req[4] else None,
            str(req[5]) if req[5] else None,
        )
        digest = binding.digest()
        return self.conn.execute(
            """INSERT INTO approvals
               (payment_request_id, status, expires_at, reason, intent_digest)
               VALUES (%s, 'PENDING', now() + (%s * interval '1 minute'), %s, %s)
               RETURNING id""",
            (payment_request_id, expires_minutes, reason, digest)).fetchone()[0]

    def get_approval(self, approval_id: UUID):
        return self.conn.execute(
            """SELECT id, payment_request_id, status, expires_at, approved_at, approved_by, intent_digest
               FROM approvals WHERE id=%s FOR UPDATE""",
            (approval_id,)).fetchone()

    def set_approval(self, approval_id: UUID, status: str, approved_by: str | None, reason: str | None):
        self.conn.execute(
            """UPDATE approvals SET status=%s::approval_status,
                   decided_at=now(),
                   approved_at=CASE WHEN %s='APPROVED' THEN now() ELSE approved_at END,
                   approved_by=CASE WHEN %s='APPROVED' THEN %s ELSE approved_by END,
                   reason=COALESCE(%s, reason)
               WHERE id=%s""",
            (status, status, status, approved_by, reason, approval_id))

    def payment_request(self, payment_request_id: UUID):
        return self.conn.execute(
            """SELECT pr.id, pr.account_id, pr.agent_id, pr.amount, pr.currency, pr.purpose,
                      pr.items, pr.policy_version_id, pr.budget_id, pr.budget_reservation_id,
                      p.id, p.status, m.domain, m.category, pr.authorization_evidence_id
               FROM payment_requests pr JOIN payments p ON p.payment_request_id=pr.id
               LEFT JOIN merchants m ON m.id=pr.merchant_id WHERE pr.id=%s FOR UPDATE""",
            (payment_request_id,)).fetchone()

    def approval_binding_digest(self, payment_request_id: UUID) -> str:
        req = self.payment_request(payment_request_id)
        if not req:
            raise LookupError("payment request not found")
        binding = ApprovalBinding(
            str(req[0]), str(req[1]), str(req[2]), Decimal(str(req[3])),
            req[4].strip(), req[12], str(req[7]) if req[7] else None,
            str(req[14]) if req[14] else None,
        )
        return binding.digest()
