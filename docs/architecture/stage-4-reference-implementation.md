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
- double-entry ledger
- transactional outbox
- PostgreSQL persistence

A production deployment may later extract these modules into services. That extraction is an operational decision and must not change protocol semantics.

## Current implemented controls

The executable reference now demonstrates:

1. policy decisions: auto, notify, approval, deny
2. concurrency-safe budget reservation in the in-memory domain and row-locked PostgreSQL repository
3. provider-neutral execution through an adapter interface
4. explicit `UNKNOWN_EXTERNAL_OUTCOME` for ambiguous provider results
5. idempotency replay and idempotency-key conflict detection
6. reservation release on a definitive provider failure
7. budget consumption only after successful execution
8. PostgreSQL transaction boundaries through a Unit of Work
9. balanced double-entry journal validation and persistence primitives
10. transactional outbox persistence with duplicate-tolerant event semantics
11. FastAPI `POST /v1/payments` and payment lookup endpoints
12. PostgreSQL-backed local Docker Compose environment
13. CI validation against PostgreSQL 16 with the canonical schema plus Stage 4 migration

## Persistence convergence

`specs/v1/migrations/001_stage4_convergence.sql` adds the persistence models required by the Master Project Schema, including:

- authorization evidence
- policy versions
- budget reservations
- payment authentication
- provider operations/events
- settlement and reconciliation records
- transactional outbox events
- ledger journals and postings

The legacy `ledger_entries` table remains for compatibility. New financial mutations are expected to converge on `ledger_journals` + `ledger_postings` as the authoritative double-entry model.

## Deliberate limitations

This is not a production payment processor. It does not yet provide:

- cryptographic authorization evidence verification
- real payment credentials or tokenization
- production provider webhooks and durable event processing workers
- production settlement/reconciliation workers
- a distributed message broker
- production-grade authentication/authorization middleware
- a full provider execution saga with asynchronous external outcome reconciliation
- database-enforced cross-row journal balance constraints

Those are the remaining Stage 4 hardening layers and must be added without weakening the architectural invariants in `docs/architecture/financial-control-invariants.md`.

## Validation

The implementation has executable tests under `reference/implementation/tests/` and GitHub Actions validates the reference implementation against PostgreSQL 16 on pushes to `main` and pull requests.
