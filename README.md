# Agent-Pay

Agent-Pay is the financial control and payment layer for the agentic internet.

## V1 Status

**Agent-Pay Protocol V1 and its reference implementation are frozen on `main` as the V1 baseline.**

V1 is a protocol + conformance + reference-implementation release. It is **not** a claim that a live PSP, bank, card issuer, regulatory environment, or production key-management deployment has been integrated.

Release scope and verification gates are recorded in `docs/release/v1-final-2026-09.md`.

## Core Principle

> **The Agent should receive spending authority, not financial credentials.**

> **Agent requests; Agent-Pay decides; Payment Rail executes; Ledger records financial truth.**

## Boundary with Agentic Trust Foundation

Agentic Trust Foundation establishes identity, delegation, authorization, trust, capability, consent, revocation, provenance, and related evidence.

Agent-Pay consumes that authority context and applies financial controls: policy, budget, approval, payment authentication, instrument routing, payment execution, transaction, settlement, reconciliation, and ledgering.

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

## Financial Control Model

```text
ATF Authority = Is the agent authorized to act?
Policy        = Under what financial conditions may it spend?
Budget        = How much allocated capacity remains?
Approval      = Does this exact intent require human approval?
Payment       = How is the financial operation executed?
Transaction   = What economic operation occurred?
Ledger        = What is the authoritative accounting record?
```

Passing one control never implies passing the others.

## V1 Assets

- normative protocol and architecture documents;
- OpenAPI V1 contract;
- PostgreSQL schema plus ordered convergence migrations 001–011;
- V1 JSON Schema / conformance vectors;
- PostgreSQL-backed reference implementation;
- cryptographic ATF evidence verification adapter;
- OIDC/JWT agent authentication boundary;
- budget, approval, provider-operation, webhook, settlement, reconciliation and ledger integrity tests;
- Docker Compose clean-environment bootstrap;
- GitHub Actions validation.

## V1 Boundary

V1 intentionally does **not** freeze a universal ATF credential/token format. The reference implementation defines a JWT/JWKS verification profile as an adapter. Independent implementations may use another credential format as long as they produce the same normalized ATF authority semantics.

V1 also does not include live PSP/bank integrations, production card issuance, universal dispute/chargeback operations, or jurisdiction-specific compliance certification.

## License

Apache-2.0.