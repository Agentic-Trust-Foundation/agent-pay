# Agent-Pay V1 Release Candidate Checklist

## RC gate

The release candidate is promoted from a clean `main` commit only when all mandatory validation workflows are green.

### Functional and integrity gates

- [x] Clean checkout and dependency installation
- [x] PostgreSQL base schema and migrations 001–009
- [x] Full `pytest -q`
- [x] `pytest -q -m conformance`
- [x] PostgreSQL end-to-end payment path
- [x] Provider timeout → `UNKNOWN_EXTERNAL_OUTCOME`
- [x] Signed webhook resolution
- [x] Provider webhook replay is a no-op
- [x] Settlement match
- [x] Settlement amount mismatch
- [x] Settlement currency mismatch
- [x] Unknown provider reference discrepancy
- [x] Duplicate settlement is a no-op
- [x] Capture / void / refund lifecycle idempotency
- [x] Concurrent budget reservation protection
- [x] Concurrent refund protection
- [x] Balanced double-entry ledger journals
- [x] Outbox atomicity
- [x] Outbox publication retry
- [x] OpenAPI parse and HTTP-surface contract
- [x] Production OIDC/JWT fail-closed validation
- [x] Threat-model/security gate reviewed
- [x] Clean Docker Compose bootstrap
- [x] API health check from clean Docker stack
- [x] Required Stage 4 persistence tables present
- [x] Worker starts from clean Docker stack

## Validation evidence

The current release-candidate commit is:

`f66c963bcd3e367061e4ca048154e1af6fd03c1b`

All three required CI workflows are green for this commit:

- Agent-Pay Validation — run `35394357602`
- Agent-Pay Conformance — run `35394357581`
- Agent-Pay Docker Clean Start — run `35394357595`

## Scope confirmation

The following remain explicitly outside V1: live bank/PSP integrations, production virtual-card issuer integration, universal ATF cryptographic evidence token format before ATF freezes it, full dispute/chargeback workflow, Kafka/event-bus dependency, mandatory microservice decomposition, and merchant/order/fulfillment system-of-record behavior.

## Promotion state

The repository is at **V1 release-candidate validation complete**. This is a reference implementation gate, not a claim of production payment-processing readiness.
