# Agent-Pay Project Status & Roadmap — V1 Final / V2 Forward Plan

**Baseline date:** 2026-09-21  
**Status:** **V1 FINAL — frozen baseline**  
**Repository:** `Agentic-Trust-Foundation/agent-pay`

> This document is the project memory and navigation point for future work. It records the completed V1 scope, security/integrity work, CI evidence, deployment-specific work remaining, and the V2 direction. Future contributors should start here before re-opening any V1 review.

## 1. Executive status

Agent-Pay V1 is complete as an **open financial-control/payment protocol baseline + conformance suite + reference implementation**.

V1 is provider-neutral. It does not claim live PSP/bank/card production integration, regulatory certification, HSM deployment, or universal dispute/chargeback support.

**Rule:** Do not restart a full V1 architecture/security review unless new evidence shows a regression, a security defect, a violated invariant, or a change to the V1 contract.

## 2. What V1 delivers

### Authority boundary
- Authenticated Agent-Pay principal.
- Agent/account binding.
- Cryptographically verified ATF authorization evidence.
- Explicit `PAYMENT` authority scope.
- Positive maximum amount and matching currency.
- Validity/expiry and revocation checks.
- Fail-closed authorization bounds.

### Financial controls
- Policy and immutable policy versions.
- Budget and concurrency-safe reservations.
- Human approval workflow and exact-intent binding.
- Payment authentication boundary.
- Payment instruments and routing.
- Provider operation identity and idempotency.
- Explicit `UNKNOWN_EXTERNAL_OUTCOME` handling.
- Durable provider events and deduplication.
- Signed webhook boundary.
- Transaction lifecycle.
- Double-entry-ready journal/posting persistence.
- Settlement and reconciliation.
- Append-only audit protection.
- Transactional outbox and worker primitives.

### Integrity boundary
- Authorization evidence is cryptographically verified before use.
- Payment requests cannot bind unverified evidence.
- PostgreSQL enforces `VERIFIED` evidence at the payment-request boundary.
- Execution paths verify payment/request/evidence binding and amount/currency consistency.
- Terminal-state and repeated-outcome handling is explicit and idempotent.

## 3. Key V1 hardening completed

The final V1 hardening cycle closed the previously identified integrity risks:

- **Authority enforcement:** execution requires verified ATF evidence bound to the payment request.
- **Fail-closed bounds:** missing/invalid amount, currency, maximum amount, or expiry cannot authorize payment.
- **State integrity:** prepare/finalize lock and validate the payment/request/evidence relationship.
- **Database integrity:** PostgreSQL rejects payment requests with non-`VERIFIED` authority evidence.
- **Migration/bootstrap integrity:** Docker PostgreSQL migration targets are lexicographically ordered and include migrations 009–011.
- **CI diagnostics:** clean-start workflow exposes PostgreSQL bootstrap errors.
- **Reference implementation version:** V1 reference implementation is version `1.0.0`.
- **Contract alignment:** OpenAPI and ATF integration documentation reflect the verified-evidence boundary.

## 4. V1 verification evidence

Final Agent-Pay commit:
`d823e2924113f1ec6a64ad6223c8eac83ad67884`

Verified GitHub Actions at that baseline:
- Validation — **success**
- Conformance — **success**
- Docker clean-start — **success**
- Required persistence tables — **success**
- Worker startup — **success**

The Docker clean-start fix specifically corrected PostgreSQL migration ordering; the old failure is historical and must not be treated as the current V1 state.

## 5. Canonical documentation order

Start here:

1. This document — project memory and roadmap.
2. `docs/release/v1-final-2026-09.md` — V1 release contract.
3. `docs/architecture/v1-release-candidate-checklist-2026-09.md` — completed gates and deployment-specific gates.
4. `docs/architecture/agent-pay-integration-boundary.md` — ATF boundary.
5. `docs/integration/atf-authorization-evidence-v1.md` — verified ATF evidence profile.
6. `docs/protocol/api-v1.md` and `specs/v1/openapi.yaml` — API contract.
7. `specs/v1/migrations/` — database evolution.
8. `conformance/v1/` — behavioral expectations.
9. `reference/implementation/` — implementation and bootstrap.

## 6. Deployment-specific work — NOT V1 protocol gaps

These may be required for a real production deployment:
- production OIDC/JWT issuer, audience, JWKS and key rotation;
- production ATF trust domain and revocation source;
- provider-specific webhook signing/key rotation;
- real PSP/bank/card issuer integration and certification;
- production secrets/vault/HSM controls and PCI scope review where applicable;
- jurisdiction-specific legal/regulatory/compliance review;
- production SLO, incident response, fraud/risk and operational controls;
- full dispute/chargeback workflows where required.

Do not move these items into the V1 protocol backlog. They belong to deployment/provider profiles.

## 7. V1 change-control rule

Classify every future change:

1. **Documentation clarification** — no semantic change.
2. **Implementation hardening** — preserves V1 contract/invariants.
3. **Provider/deployment profile** — external integration without redefining V1.
4. **Extension/profile** — optional capability.
5. **V2 semantic change** — changes the normative protocol.

Only the first four should normally land without reopening V1. V2 semantic changes require an explicit versioned design.

## 8. V2 roadmap

### V2-A — Payment provider profiles
- Real PSP/bank/card-rail adapters.
- Provider capability discovery.
- Provider-specific idempotency and webhook profiles.
- Settlement and reconciliation adapters.
- Failure/retry matrices.

### V2-B — Financial policy
- More expressive policy language.
- Multi-dimensional limits.
- Merchant/category/region constraints.
- Time-windowed budgets.
- Delegated approval chains.
- Risk signals without changing ATF authority semantics.

### V2-C — Agentic commerce
- Purchase/order lifecycle integration.
- Merchant authorization profiles.
- Booking and service transactions.
- Refund and cancellation profiles.
- Cross-system transaction correlation.

### V2-D — Virtual cards and instruments
- Issuer integration profiles.
- Instrument lifecycle.
- Per-agent/per-merchant controls.
- Dynamic limits and temporary credentials.
- Secure vault/HSM deployment profiles.

### V2-E — Disputes, fraud and operations
- Chargeback/dispute lifecycle.
- Fraud/risk decision integration.
- Operational reconciliation tooling.
- Incident and recovery workflows.
- Production SLO and observability profiles.

### V2-F — Cross-agent delegation
- Consume richer ATF agent-to-agent delegation.
- Preserve upstream authority bounds.
- Propagate revocation and constraints.
- Bind financial authority to delegated principals.

## 9. Work that can proceed without changing V1

- More tests and conformance vectors.
- Documentation/examples.
- Provider-neutral hardening.
- Deployment manifests and observability.
- Simulator improvements.
- Language/runtime ports.
- Real provider adapters as separate profiles.
- Production security/compliance work.
- Integration experiments with ATF and commerce systems.

## 10. Definition of done for a future production profile

A production/provider profile should document:
- provider/issuer scope;
- authentication and key lifecycle;
- webhook verification;
- idempotency and ambiguous outcomes;
- settlement/reconciliation;
- secrets/HSM controls;
- fraud/risk;
- operational SLOs;
- incident/recovery;
- compliance/legal assumptions;
- conformance tests;
- deployment runbook.

## 11. Anti-regression checklist

Before restarting a V1 review, check:
- Did the V1 contract change?
- Did verified ATF evidence enforcement regress?
- Can an unverified evidence record reach payment execution?
- Can an invalid amount/currency/expiry pass?
- Can Agent-Pay expand upstream authority?
- Did payment state transitions become non-idempotent?
- Did a conformance/CI regression appear?
- Is the issue actually provider/deployment-specific?

If none apply, continue from this baseline.

## 12. Project map

```text
ATF VERIFIED AUTHORITY
          │
          ▼
   AGENT-PAY CONTROL
   ├── Policy
   ├── Budget
   ├── Approval
   ├── Payment Authentication
   ├── Instruments / Routing
   ├── Provider Operation
   ├── Transaction / Ledger
   ├── Settlement / Reconciliation
   └── Audit / Outbox
          │
          ▼
   PROVIDER / PAYMENT RAIL
```

## 13. Current next action

V1 is done. Select the next workstream from the V2 roadmap or from the deployment-specific profile list; do not recreate the V1 implementation from scratch.
