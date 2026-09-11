# Agent-Pay V1 Final Gap Audit — 2026-09

This audit is the final control checklist for the current reference implementation. A feature is only considered complete when the repository contains the implementation, persistence model, test coverage, and documentation needed for the V1 boundary.

## Completed in the current build line

- canonical V1 domain/state model and financial-control invariants
- PostgreSQL convergence migrations through settlement/reconciliation integrity, including migration 008 for multiple settlement reports per provider operation
- double-entry-ready ledger journals/postings
- policy versioning and budget reservations
- approval history/concurrency hardening
- provider operation idempotency
- provider webhook persistence, signature verification, deduplication, and outcome resolution
- provider settlement ingestion and reconciliation
- capture / void / refund lifecycle primitives with refund serialization
- provider simulator covering ambiguous external outcomes
- transactional outbox primitives with PostgreSQL claim, publication, and retry semantics
- API authentication and server-side Agent/account binding
- production OIDC/JWT verification boundary with fail-closed validation tests
- RFC 9457-style API error responses
- OpenAPI lifecycle/webhook/settlement surface
- machine-readable V1 control vectors and selective `pytest -m conformance`
- PostgreSQL integration classification and ledger/outbox integration gate
- provider-neutral observability primitives and operational guidance
- ATF authorization-evidence integration boundary
- threat model, protocol baseline, execution plan, and release checklist
- clean Docker Compose bootstrap path with base schema + migrations 001–008

## Mandatory final validation gates

| # | Gate | Status |
|---|---|---|
| 1 | clean checkout + dependency installation | PASS in CI baseline |
| 2 | PostgreSQL base schema + migrations 001–008 | PASS in clean Docker smoke; final full validation pending |
| 3 | full pytest suite | FAILED once on settlement-mismatch constraint; fix committed, final re-run pending |
| 4 | `pytest -m conformance` | PASS — run `34637806354` |
| 5 | PostgreSQL end-to-end payment path | covered by `test_postgres_e2e.py`; final re-run pending |
| 6 | timeout → unknown outcome → signed webhook resolution | covered; replay strengthened |
| 7 | duplicate webhook no-op | covered by resolver replay test |
| 8 | settlement match and mismatch | implementation fix committed; final full-suite re-run pending |
| 9 | duplicate settlement no-op | covered |
| 10 | capture / void / refund idempotency | covered by lifecycle tests |
| 11 | concurrent budget reservation | PASS in latest verified validation baseline |
| 12 | concurrent refund protection | covered by lifecycle concurrency tests |
| 13 | balanced ledger journals | PASS in PostgreSQL integration baseline |
| 14 | outbox atomicity/retry behavior | retry + atomicity tests added; final re-run pending |
| 15 | OpenAPI parse and HTTP surface contract | PASS in latest verified validation baseline |
| 16 | production OIDC fail-closed behavior | fail-closed + JWT validation tests added; final re-run pending |
| 17 | security/threat-model review | PASS as architecture gate; production provider-specific review remains deployment-specific |
| 18 | clean Docker Compose environment | PASS — clean-start run `34637806390` reached all smoke steps successfully |
| 19 | final CI run on the release candidate commit | PENDING |

## Current release gate

The repository is **not yet declared V1-ready**. The previous full validation run exposed a real reconciliation-schema issue: `reconciliation_records.provider_operation_id` was incorrectly unique, preventing a second settlement report from recording a legitimate mismatch. Migration 008 removes that uniqueness and keeps settlement identity as the idempotency boundary.

The latest conformance run is green and the clean Docker smoke path is green. A fresh full validation pass on the corrected migration line is still required. Only a commit whose validation workflows are green will be promoted to the release-candidate ref.

## Deliberately outside V1 implementation

- live bank/PSP integrations
- production virtual-card issuer integration
- a universal ATF cryptographic evidence token format before ATF freezes it
- full dispute/chargeback operational workflow
- Kafka/event-bus dependency
- mandatory microservice decomposition
- merchant/order/fulfillment system-of-record behavior

These are not omissions from the V1 architecture; they are explicit scope boundaries. V1 remains protocol-first, provider-neutral, and implementable as a modular monolith.
