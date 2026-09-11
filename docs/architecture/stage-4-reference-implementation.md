# Stage 4 — Reference Implementation

## Purpose

The reference implementation demonstrates the protocol's financial-control invariants without making implementation details part of the protocol specification.

## Current implementation shape

V1 is a modular monolith with explicit boundaries for:

- authenticated agent principal binding
- payment domain/state transitions
- policy evaluation
- PostgreSQL repositories
- database transaction boundaries
- budget reservation with row-level locking
- double-entry journal/posting persistence
- provider operations and external adapter boundary
- payment execution worker semantics
- capture / void / refund lifecycle
- idempotency across API, provider operations and transaction history
- transactional outbox
- provider webhook/event integration primitives
- settlement/reconciliation primitives

The external provider call is deliberately outside the database transaction. A payment is reserved and marked for processing first; the provider is called; the result is then finalized in a new transaction. This prevents long-running database transactions while preserving explicit handling of ambiguous external outcomes.

## Implemented controls

1. policy decisions: auto, notify, approval, deny
2. PostgreSQL-backed payment requests and payments
3. fail-closed authentication boundary for agent callers
4. authenticated principal must match claimed agent/account
5. concurrency-safe budget reservation using `SELECT ... FOR UPDATE`
6. reservation consumption/release is idempotent
7. provider-neutral execution through an adapter interface
8. explicit `UNKNOWN_EXTERNAL_OUTCOME` for ambiguous provider results
9. double-entry journal/posting validation and persistence
10. ledger idempotency keys
11. transactional outbox persistence
12. outbox row claiming with `FOR UPDATE SKIP LOCKED`
13. provider operation idempotency persistence
14. capture, void and refund operations use distinct stable provider idempotency keys
15. transaction history is separate from payment state
16. refunds are bounded by captured-minus-refunded amount under the database transaction
17. refund ledger postings reverse the capture direction
18. voids do not create a compensating ledger movement because an authorization is not a capture
19. local Docker PostgreSQL bootstrap
20. CI validation against PostgreSQL 16

## Deliberate limitations

This remains a reference implementation, not a production payment processor. It does not yet provide:

- cryptographic verification of external authorization evidence
- production OIDC/JWT verification and key rotation
- real payment credentials or PCI-grade tokenization
- provider-specific authorization/capture/void/refund semantics
- end-to-end signed webhook resolution of `UNKNOWN_EXTERNAL_OUTCOME`
- settlement/reconciliation workers
- a complete policy DSL and policy-version evaluation engine
- distributed job scheduling/queue infrastructure
- production risk/fraud controls
- full approval UI/notification channels

These are the next implementation layers and must be added without weakening the invariants in `docs/architecture/financial-control-invariants.md`.

## Local execution

From `reference/implementation/`:

```bash
docker compose up --build
```

The PostgreSQL container bootstraps the base schema and Stage 4 migrations. The API listens on port 8000. Development authentication is enabled only for the local reference stack and uses the explicitly configured development principal.

## Validation

The implementation has executable unit and PostgreSQL integration tests under `reference/implementation/tests/`. GitHub Actions starts PostgreSQL 16, applies the canonical schema plus Stage 4 migrations, and runs the complete test suite on pushes to `main` and pull requests.
