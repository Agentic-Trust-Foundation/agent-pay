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
Agent-Pay Core
 ├── Agent / Delegation / Authorization Context
 ├── Policy / Policy Version
 ├── Budget / Reservation
 ├── Approval
 ├── Payment / Authentication / Provider Operation
 ├── Payment Router / Instruments
 ├── Transaction / Ledger
 ├── Settlement / Reconciliation
 └── Audit / Notification
 ↓
PostgreSQL + Outbox
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

The Master Project Schema is now the architecture baseline and Stage 3 aligns the implementation artifacts around it.

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

The additive SQL migration is intentionally separate from the original draft schema so the project can migrate safely rather than silently rewriting historical assumptions.

## Current Status

The repository is still **not a production payment system**. The architecture/specification baseline is substantially converged, while executable reference implementation, real provider adapters, production cryptographic/vault controls, regulatory/compliance work, operational hardening, and full dispute/chargeback capability remain implementation stages.

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

### Out of scope

- General agent identity/trust network
- General delegation protocol
- Enterprise IAM replacement
- Complete commerce/catalog/fulfillment protocol
- Mandatory blockchain/cryptocurrency
- Mandatory payment provider

## Repository Structure

```text
agent-pay/
├── docs/{vision,architecture,protocol,security,governance,integration}/
├── specs/v1/
├── reference/implementation/
├── conformance/
├── schemas/
├── examples/
├── test-vectors/
└── tools/
```

## Security Principles

- Agent never owns user funds.
- No primary financial credentials to agents.
- Server-side financial authorization and fail-closed decisions.
- Approval bound to the exact payment intent.
- Provider credentials isolated behind protected adapters.
- Financial operations idempotent and concurrency-safe.
- Provider events authenticated, persisted, deduplicated, and replay-safe.
- Financial history append-oriented with compensating corrections.
- Ambiguous external outcomes reconciled rather than guessed.

## License

License and governance terms will be established before the first normative protocol release.
