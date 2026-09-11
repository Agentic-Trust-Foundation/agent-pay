# Stage 4 — Reference Implementation

## Purpose

The reference implementation demonstrates the protocol's financial-control invariants without making implementation details part of the protocol specification.

## V1 implementation shape

V1 uses a modular monolith with explicit boundaries for:

- payment domain/state transitions
- policy evaluation
- budget reservation
- payment-provider adapters
- idempotency
- financial state recording
- future outbox/event integration

A production deployment may later extract these modules into services. That extraction is an operational decision and must not change protocol semantics.

## Current implemented controls

The initial executable core demonstrates:

1. policy decisions: auto, notify, approval, deny
2. concurrency-safe budget reservation using a lock in the in-memory reference model
3. provider-neutral execution through an adapter interface
4. explicit `UNKNOWN_EXTERNAL_OUTCOME` for ambiguous provider results
5. idempotency replay and idempotency-key conflict detection
6. reservation release on a definitive provider failure
7. budget consumption only after successful execution

## Deliberate limitations

This is not a production payment processor. It does not yet provide:

- PostgreSQL persistence
- real double-entry journal/posting persistence
- cryptographic authorization evidence verification
- real payment credentials or tokenization
- provider webhooks and durable event ingestion
- settlement/reconciliation workers
- transactional outbox persistence
- distributed concurrency control
- real authentication/authorization middleware

Those capabilities are next Stage 4 execution layers and must be added without weakening the architectural invariants in `docs/architecture/financial-control-invariants.md`.

## Validation

The implementation has executable tests under `reference/implementation/tests/` and is validated by GitHub Actions on pushes to `main` and pull requests.
