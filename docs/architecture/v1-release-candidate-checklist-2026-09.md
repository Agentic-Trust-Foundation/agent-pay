# Agent-Pay V1 Release Candidate Checklist

## Implemented baseline

- [x] Canonical domain model
- [x] PostgreSQL convergence migrations 001-007
- [x] Double-entry-ready ledger journals/postings
- [x] Policy and policy-version model
- [x] Budget reservation with row locking
- [x] Approval workflow
- [x] Payment orchestration
- [x] Provider operation idempotency
- [x] UNKNOWN_EXTERNAL_OUTCOME
- [x] Provider event persistence and deduplication
- [x] Signed provider webhook HTTP boundary
- [x] Settlement ingestion and reconciliation
- [x] Deterministic provider simulator
- [x] Simulator timeout/webhook/settlement E2E tests
- [x] V1 behavioral conformance vectors
- [x] Machine-readable conformance validation
- [x] Docker Compose migration convergence
- [x] CI schema convergence through migration 007
- [x] Threat model baseline
- [x] Protocol V1 baseline

## Remaining release gates

- [ ] Execute PostgreSQL-backed full E2E test against a clean database.
- [ ] Execute lifecycle integration tests for capture/void/refund, including concurrent refunds.
- [ ] Execute HTTP webhook integration tests for duplicate, invalid-signature and out-of-order events.
- [ ] Execute the complete CI workflow and record a green run.
- [ ] Replace development authentication with production OIDC/JWT configuration for deployment environments.
- [ ] Complete provider-specific replay protection and key rotation adapters.
- [ ] Complete cryptographic authorization-evidence verification for ATF integration.
- [ ] Review regulatory/compliance requirements for the target deployment jurisdiction.
- [ ] Freeze V1 public API and publish compatibility policy.

## Release rule

Agent-Pay must not be labeled production-ready merely because the reference implementation starts. V1 RC requires passing financial integrity, idempotency, concurrency, provider ambiguity, webhook, settlement, reconciliation, security and clean-environment CI gates.
