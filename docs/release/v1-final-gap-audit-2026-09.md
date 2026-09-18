# Agent-Pay V1 Final Gap Audit — 2026-09

This audit is the final control checklist for the current reference implementation. A feature is only considered complete when the repository contains the implementation, persistence model, test coverage, and documentation needed for the V1 boundary.

## Completed in the current build line

- canonical V1 domain/state model and financial-control invariants
- PostgreSQL convergence migrations through settlement/reconciliation integrity, including migration 008 for multiple settlement reports per provider operation
- payment-instrument integrity migration 009
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
- clean Docker Compose bootstrap path with base schema + migrations 001–009

## Mandatory final validation gates

| # | Gate | Status |
|---|---|---|
| 1 | clean checkout + dependency installation | PASS |
| 2 | PostgreSQL base schema + migrations 001–009 | PASS — validation run `35394357602` |
| 3 | full `pytest -q` | PASS — validation run `35394357602` |
| 4 | `pytest -q -m conformance` | PASS — run `35394357581` |
| 5 | PostgreSQL end-to-end payment path | PASS — included in validation suite |
| 6 | timeout → unknown outcome → signed webhook resolution | PASS — covered by lifecycle/resolution tests |
| 7 | duplicate webhook no-op | PASS |
| 8 | settlement match and mismatch | PASS — migration 008 correction validated |
| 9 | duplicate settlement no-op | PASS |
| 10 | capture / void / refund idempotency | PASS |
| 11 | concurrent budget reservation | PASS |
| 12 | concurrent refund protection | PASS |
| 13 | balanced ledger journals | PASS |
| 14 | outbox atomicity/retry behavior | PASS |
| 15 | OpenAPI parse and HTTP surface contract | PASS |
| 16 | production OIDC fail-closed behavior | PASS |
| 17 | security/threat-model review | PASS as architecture gate; provider-specific deployment review remains deployment-specific |
| 18 | clean Docker Compose environment | PASS — run `35394357595` |
| 19 | final CI validation on release-candidate commit | PASS — commit `f66c963bcd3e367061e4ca048154e1af6fd03c1b` |

## Current release gate

The release-candidate validation gate is **green** on `main` commit `f66c963bcd3e367061e4ca048154e1af6fd03c1b`.

The corrected settlement schema, migration 009, full reference test suite, conformance suite, and clean Docker bootstrap all passed in the CI runs associated with that commit.

This establishes the repository as a **V1 release-candidate reference implementation**. It does not make the project a production payment processor: live bank/PSP integrations, production issuer integration, regulatory approval, and deployment-specific security/compliance controls remain outside this repository gate.

## Deliberately outside V1 implementation

- live bank/PSP integrations
- production virtual-card issuer integration
- a universal ATF cryptographic evidence token format before ATF freezes it
- full dispute/chargeback operational workflow
- Kafka/event-bus dependency
- mandatory microservice decomposition
- merchant/order/fulfillment system-of-record behavior

These are explicit scope boundaries. V1 remains protocol-first, provider-neutral, and implementable as a modular monolith.
