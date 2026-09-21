# Agent-Pay

Agent-Pay is the financial control and payment layer for the agentic internet.

## V1 Status

**Agent-Pay Protocol V1 and its reference implementation are FINAL and frozen on `main`.**

V1 is a protocol + conformance + reference-implementation release. It is **not** a claim that a live PSP, bank, card issuer, regulatory environment, HSM/vault, or production payment deployment has been integrated.

**Project memory and complete roadmap:** `docs/roadmap/v1-complete-and-v2-roadmap-2026-09.md`

## Core Principle

> **The Agent should receive spending authority, not financial credentials.**

> **Agent requests; Agent-Pay decides; Payment Rail executes; Ledger records financial truth.**

## Boundary with Agentic Trust Foundation

ATF establishes identity, delegation, general authorization, trust, capabilities, consent, revocation, provenance, and authority evidence.

Agent-Pay consumes that authority context and applies financial controls: policy, budget, approval, payment authentication, instrument routing, payment execution, transaction, settlement, reconciliation, and ledgering.

**Agent-Pay never expands upstream authority.**

## Design Position

Agent-Pay is **protocol-first, implementation-backed, and service-optional**. It is not a general identity/trust protocol, a complete commerce protocol, a merchant catalog, or a replacement for banking/payment rails.

## V1 Architecture

V1 is a **modular monolith** backed by PostgreSQL, with a transactional outbox and asynchronous worker.

```text
API
 ↓
Authenticated Agent Principal
 ↓
Verified ATF Authority
 ↓
Agent-Pay Core
 ├── Policy / Policy Version
 ├── Budget / Reservation
 ├── Approval
 ├── Payment / Authentication / Provider Operation
 ├── Payment Router / Instruments
 ├── Transaction / Double-Entry Ledger
 ├── Settlement / Reconciliation
 └── Audit / Notification
 ↓
PostgreSQL + Transactional Outbox
 ↓
Provider / Payment Rail Adapters
```

## V1 Assets

- normative protocol and architecture documents;
- OpenAPI V1 contract;
- PostgreSQL schema plus ordered convergence migrations 001–014;
- V1 JSON Schema / conformance vectors;
- PostgreSQL-backed reference implementation v1.0.0;
- cryptographic ATF evidence verification adapter;
- OIDC/JWT agent authentication boundary;
- budget, approval, provider-operation, webhook, settlement, reconciliation and ledger integrity tests;
- database enforcement requiring `VERIFIED` authority evidence;
- Docker Compose clean-environment bootstrap;
- GitHub Actions validation and conformance.

## V1 Completion Evidence

Final Agent-Pay baseline commit:

`d823e2924113f1ec6a64ad6223c8eac83ad67884`

Verified at that baseline:

- Validation — success
- Conformance — success
- Docker clean-start — success
- persistence-table checks — success
- worker-startup checks — success

The migration-ordering issue encountered during clean-start was fixed by lexicographically ordered PostgreSQL migration mounts. The current clean-start profile applies migrations 001–013 in order.

## V1 Boundary

V1 intentionally does **not** freeze a universal ATF credential/token format. The reference implementation defines a JWT/JWKS verification profile as an adapter. Independent implementations may use another credential format as long as they produce the same normalized ATF authority semantics.

V1 also does not include live PSP/bank integrations, production card issuance, universal dispute/chargeback operations, or jurisdiction-specific compliance certification.

## Documentation Order

Start here:

1. `docs/roadmap/v1-complete-and-v2-roadmap-2026-09.md`
2. `docs/release/v1-final-2026-09.md`
3. `docs/architecture/v1-release-candidate-checklist-2026-09.md`
4. `docs/architecture/project-boundaries.md`
5. `docs/integration/atf-authorization-evidence-v1.md`
6. `docs/protocol/api-v1.md` and `specs/v1/openapi.yaml`
7. `specs/v1/migrations/`
8. `conformance/v1/`
9. `reference/implementation/`

## Change Control

Do not restart a full V1 review unless new evidence shows a regression, security defect, violated invariant, conformance failure, or intentional contract change.

Future work should be classified as documentation clarification, implementation hardening, provider/deployment profile, optional extension/profile, or V2 semantic change.

## License

Apache-2.0.
