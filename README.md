# Agent-Pay

Agent-Pay is the financial control and payment layer for the agentic internet.

It enables agents to initiate payments under explicit delegated authority, financial policies, budgets, approvals, risk controls, and payment constraints without giving agents unrestricted access to money or primary financial credentials.

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
Agent-Pay Core
 ├── Agent / Delegation / Authorization Context
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

Redis may support operational acceleration but never becomes financial source of truth.

## Financial Control Model

```text
Delegation = What authority was granted?
Policy     = Under what conditions may it be spent?
Budget     = How much allocated capacity remains?
Approval   = Does this exact intent require human approval?
Payment    = How is the financial operation executed?
Transaction= What economic operation occurred?
Ledger     = What is the authoritative accounting record?
```

Passing one control never implies passing the others.

## Canonical Payment Lifecycle

```text
REQUESTED
 → VALIDATING
 → AUTHENTICATION_REQUIRED / AUTHENTICATED
 → POLICY_CHECK
 → BUDGET_CHECK
 → APPROVAL_REQUIRED / APPROVED
 → PAYMENT_PENDING
 → PROCESSING
 → SUCCEEDED / FAILED / UNKNOWN_EXTERNAL_OUTCOME
```

External timeout does not automatically mean failure. Refund, reversal/void, settlement, dispute, and reconciliation are separate auditable financial operations.

## Stage 3 — Consistency Convergence

The Master Project Schema is the architecture baseline and Stage 3 aligned the implementation artifacts around it.

Implemented on `main`:

- canonical consistency/convergence gate;
- converged OpenAPI lifecycle and RFC 9457-style errors;
- first-class persistence migration for authorization evidence;
- immutable policy-version model;
- budget reservations;
- payment authentication records;
- provider operation/event persistence;
- settlement and reconciliation persistence;
- transactional outbox persistence;
- double-entry-ready ledger journal/posting model;
- behavioral V1 conformance vectors;
- V1 payment-intent JSON Schema.

## Stage 4 — Executable Reference Platform

The reference implementation now contains the first executable platform layers:

- PostgreSQL connection and repository layer;
- explicit Unit of Work / transaction boundaries;
- row-locked budget reservations;
- persistent double-entry journals and postings;
- provider operation idempotency;
- fail-closed authentication boundary and agent/account principal binding;
- external provider adapter boundary;
- payment execution worker primitive with external calls outside DB transactions;
- explicit `UNKNOWN_EXTERNAL_OUTCOME` handling;
- transactional outbox and `FOR UPDATE SKIP LOCKED` claiming;
- local Docker Compose PostgreSQL bootstrap;
- PostgreSQL-backed CI validation and integration tests.

The reference stack can therefore exercise the core control path against real PostgreSQL rather than only an in-memory model.

## Current Status

The repository is **an executable reference platform, not a production payment processor**. The protocol and architecture baseline are substantially converged. Remaining implementation layers include production OIDC/JWT verification, cryptographic authorization-evidence verification, secure tokenization/vault boundaries, real provider adapters, signed webhook ingestion, settlement/reconciliation workers, complete policy DSL evaluation, approval/notification UX, risk/fraud controls, and regulatory/compliance hardening.

## Scope

### In scope

- Wallets and funding
- Payment instruments and future virtual-card integration
- Payment Intent / Payment Request
- Spending Policy and Policy Versioning
- Budgets and reservations
- Approval workflows
- Payment authentication boundary
- Payment routing and provider integration
- Transaction lifecycle
- Settlement and reconciliation
- Refunds and reversals
- Financial ledger
- Provider webhooks/events
- Audit and notifications
- Agentic commerce context integration
- Agentic Trust Foundation authorization-evidence integration
