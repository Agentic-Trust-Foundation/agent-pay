"""PostgreSQL repositories used by the reference API."""
from uuid import UUID


class PaymentRepository:
    def __init__(self, conn):
        self.conn = conn

    def create_request(self, *, account_id: UUID, agent_id: UUID, amount: str,
                       currency: str, purpose: str, items: list, idempotency_key: str) -> UUID:
        row = self.conn.execute(
            """INSERT INTO payment_requests
               (account_id, agent_id, amount, currency, purpose, items, idempotency_key)
               VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
               RETURNING id""",
            (account_id, agent_id, amount, currency, purpose, __import__('json').dumps(items), idempotency_key),
        ).fetchone()
        return row[0]

    def find_by_idempotency(self, account_id: UUID, key: str):
        return self.conn.execute(
            "SELECT id, amount, currency, purpose, items FROM payment_requests WHERE account_id=%s AND idempotency_key=%s",
            (account_id, key),
        ).fetchone()

    def get_payment(self, payment_id: UUID):
        return self.conn.execute(
            """SELECT p.id, p.payment_request_id, p.amount, p.currency, p.status,
                      p.provider_reference, p.created_at, p.completed_at
               FROM payments p WHERE p.id=%s""",
            (payment_id,),
        ).fetchone()

    def create_payment(self, *, request_id: UUID, amount: str, currency: str, status: str):
        return self.conn.execute(
            """INSERT INTO payments (payment_request_id, amount, currency, status)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (request_id, amount, currency, status),
        ).fetchone()[0]

    def update_status(self, payment_id: UUID, status: str, provider_reference: str | None = None):
        self.conn.execute(
            """UPDATE payments SET status=%s, provider_reference=COALESCE(%s, provider_reference),
                      completed_at=CASE WHEN %s IN ('SUCCEEDED','FAILED') THEN now() ELSE completed_at END,
                      updated_at=now() WHERE id=%s""",
            (status, provider_reference, status, payment_id),
        )


class BudgetRepository:
    def __init__(self, conn):
        self.conn = conn

    def reserve(self, budget_id: UUID, payment_request_id: UUID, amount: str) -> UUID | None:
        row = self.conn.execute(
            "SELECT id, limit_amount, consumed_amount, reserved_amount, currency FROM budgets WHERE id=%s FOR UPDATE",
            (budget_id,),
        ).fetchone()
        if not row:
            return None
        available = row[1] - row[2] - row[3]
        if available < amount:
            return None
        reservation = self.conn.execute(
            """INSERT INTO budget_reservations (budget_id, payment_request_id, amount, currency)
               VALUES (%s,%s,%s,%s) RETURNING id""",
            (budget_id, payment_request_id, amount, row[4]),
        ).fetchone()[0]
        self.conn.execute("UPDATE budgets SET reserved_amount=reserved_amount+%s, updated_at=now() WHERE id=%s", (amount, budget_id))
        return reservation

    def consume(self, reservation_id: UUID):
        row = self.conn.execute(
            "SELECT budget_id, amount FROM budget_reservations WHERE id=%s FOR UPDATE", (reservation_id,)
        ).fetchone()
        if not row:
            raise ValueError("budget reservation not found")
        self.conn.execute(
            "UPDATE budget_reservations SET status='CONSUMED', consumed_at=now() WHERE id=%s AND status='RESERVED'",
            (reservation_id,),
        )
        self.conn.execute(
            """UPDATE budgets SET reserved_amount=reserved_amount-%s,
                      consumed_amount=consumed_amount+%s, updated_at=now() WHERE id=%s""",
            (row[1], row[1], row[0]),
        )

    def release(self, reservation_id: UUID):
        row = self.conn.execute(
            "SELECT budget_id, amount FROM budget_reservations WHERE id=%s FOR UPDATE", (reservation_id,)
        ).fetchone()
        if not row:
            raise ValueError("budget reservation not found")
        self.conn.execute(
            "UPDATE budget_reservations SET status='RELEASED', released_at=now() WHERE id=%s AND status='RESERVED'",
            (reservation_id,),
        )
        self.conn.execute("UPDATE budgets SET reserved_amount=reserved_amount-%s, updated_at=now() WHERE id=%s", (row[1], row[0]))
