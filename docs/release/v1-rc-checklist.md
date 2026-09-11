# Agent-Pay V1 Release Candidate Checklist

## RC gate

A release candidate may be promoted only from a clean `main` commit for which all mandatory validation workflows are green.

### Functional and integrity gates

- [ ] Clean checkout and dependency installation
- [ ] PostgreSQL base schema and migrations 001–007
- [ ] Full `pytest -q`
- [ ] `pytest -q -m conformance`
- [ ] PostgreSQL end-to-end payment path
- [ ] Provider timeout → `UNKNOWN_EXTERNAL_OUTCOME`
- [ ] Signed webhook resolution
- [ ] Provider webhook replay is a no-op
- [ ] Settlement match
- [ ] Settlement amount mismatch
- [ ] Settlement currency mismatch
- [ ] Unknown provider reference discrepancy
- [ ] Duplicate settlement is a no-op
- [ ] Capture / void / refund lifecycle idempotency
- [ ] Concurrent budget reservation protection
- [ ] Concurrent refund protection
- [ ] Balanced double-entry ledger journals
- [ ] Outbox atomicity
- [ ] Outbox publication retry
- [ ] OpenAPI parse and HTTP-surface contract
- [ ] Production OIDC/JWT fail-closed validation
- [ ] Threat-model/security gate reviewed
- [ ] Clean Docker Compose bootstrap
- [ ] API health check from clean Docker stack
- [ ] Required Stage 4 persistence tables present
- [ ] Worker starts from clean Docker stack

## Scope confirmation

The following remain explicitly outside V1: live bank/PSP integrations, production virtual-card issuer integration, universal ATF cryptographic evidence token format before ATF freezes it, full dispute/chargeback workflow, Kafka/event-bus dependency, mandatory microservice decomposition, and merchant/order/fulfillment system-of-record behavior.

## Promotion rule

Do not mark this checklist complete, publish a V1 release, or claim V1-ready status until the final RC commit has green validation, conformance, and Docker clean-start workflows.
