# Agent-Pay V1 Final Release Checklist

**Status: V1 FINAL — protocol/reference baseline frozen**

> **Project memory / roadmap:** `docs/roadmap/v1-complete-and-v2-roadmap-2026-09.md`

## Repository and protocol gates

- [x] Canonical domain model
- [x] ATF ↔ Agent-Pay responsibility boundary
- [x] OpenAPI V1 contract
- [x] PostgreSQL schema and ordered migrations 001–011
- [x] Double-entry-ready ledger journals/postings
- [x] Immutable policy-version model
- [x] Concurrency-safe budget reservations
- [x] Appendable approval history and exact-intent binding
- [x] Payment authentication persistence
- [x] Provider operation identity/idempotency
- [x] UNKNOWN_EXTERNAL_OUTCOME lifecycle
- [x] Durable provider-event persistence and deduplication
- [x] Signed webhook verification/replay controls
- [x] Settlement ingestion and reconciliation
- [x] Transactional outbox and retry worker primitives
- [x] Append-only audit protection
- [x] Payment-instrument integrity
- [x] OIDC/JWT agent authentication boundary
- [x] Cryptographic ATF authorization-evidence verification adapter
- [x] Database enforcement that payment requests require VERIFIED authority evidence
- [x] Execution-time payment/request/evidence binding and amount/currency checks
- [x] Reference simulator and end-to-end timeout → webhook → settlement scenario
- [x] V1 behavioral conformance vectors
- [x] Cross-repository ATF/Agent-Pay conformance
- [x] Docker Compose clean-environment bootstrap
- [x] GitHub Actions validation

## What V1 means

V1 is complete as an **open protocol baseline, conformance suite, and reference implementation**.

It is not a claim of production payment-rail readiness. The reference implementation deliberately stops at provider-neutral and simulator boundaries.

## Final V1 verification record

Baseline commit:

`d823e2924113f1ec6a64ad6223c8eac83ad67884`

Verified green at this baseline:

- Agent-Pay Validation
- Agent-Pay Conformance
- Docker Clean Start
- persistence-table verification
- worker-startup verification

## Deployment-specific gates outside the V1 protocol release

These remain deployment/provider work rather than missing V1 protocol semantics:

- [ ] Configure production OIDC/JWT issuer, audience, JWKS and key rotation.
- [ ] Configure production ATF evidence verifier/trust domain and revocation source.
- [ ] Implement provider-specific webhook signing, replay and key-rotation adapters.
- [ ] Integrate a real PSP/bank/card issuer and perform provider certification.
- [ ] Implement production secrets/vault/HSM controls and PCI scope review where applicable.
- [ ] Complete jurisdiction-specific legal/regulatory/compliance review.
- [ ] Complete production SLO, incident response, fraud/risk and operational controls.
- [ ] Implement full dispute/chargeback workflow if the chosen payment rail requires it.

These items must not be described as V1 protocol gaps.

## Historical failure note

An earlier Docker clean-start run failed because PostgreSQL migration mount targets were not lexicographically ordered. The migration targets were corrected to zero-padded order and migrations 009–011 were included. A subsequent clean-start run passed all required checks.

## Release rule

Do not label the reference implementation a production payment processor. The V1 release claim is limited to the protocol, conformance assets, reference implementation, financial-control invariants, and tested provider-neutral lifecycle.
