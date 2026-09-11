# Agent-Pay V1 Final Gap Audit — 2026-09

This audit is the final control checklist for the current reference implementation. A feature is only considered complete when the repository contains the implementation, persistence model, test coverage, and documentation needed for the V1 boundary.

## Completed in the current build line

- canonical V1 domain/state model and financial-control invariants
- PostgreSQL convergence migrations through settlement/reconciliation integrity
- double-entry-ready ledger journals/postings
- policy versioning and budget reservations
- approval history/concurrency hardening
- provider operation idempotency
- provider webhook persistence, signature verification, deduplication, and outcome resolution
- provider settlement ingestion and reconciliation
- capture / void / refund lifecycle primitives with refund serialization
- provider simulator covering ambiguous external outcomes
- transactional outbox primitives
- API authentication and server-side Agent/account binding
- production OIDC/JWT verification boundary
- RFC 9457-style API error responses
- OpenAPI lifecycle/webhook/settlement surface
- machine-readable V1 control vectors and selective `pytest -m conformance`
- PostgreSQL integration classification and ledger/outbox integration gate
- provider-neutral observability primitives and operational guidance
- ATF authorization-evidence integration boundary
- threat model, protocol baseline, execution plan, and release checklist

## Mandatory final validation gates

1. clean checkout + dependency installation
2. PostgreSQL base schema + migrations 001–007
3. full pytest suite
4. `pytest -m conformance`
5. PostgreSQL end-to-end payment path
6. timeout → unknown outcome → signed webhook resolution
7. duplicate webhook no-op
8. settlement match and mismatch
9. duplicate settlement no-op
10. capture / void / refund idempotency
11. concurrent budget reservation
12. concurrent refund protection
13. balanced ledger journals
14. outbox atomicity/retry behavior
15. OpenAPI parse and HTTP surface contract
16. production OIDC fail-closed behavior
17. security/threat-model review
18. clean Docker Compose environment
19. final CI run on the release candidate commit

## Deliberately outside V1 implementation

- live bank/PSP integrations
- production virtual-card issuer integration
- a universal ATF cryptographic evidence token format before ATF freezes it
- full dispute/chargeback operational workflow
- Kafka/event-bus dependency
- mandatory microservice decomposition
- merchant/order/fulfillment system-of-record behavior

These are not omissions from the V1 architecture; they are explicit scope boundaries. V1 remains protocol-first, provider-neutral, and implementable as a modular monolith.
