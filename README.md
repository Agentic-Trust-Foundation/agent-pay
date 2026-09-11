# Agent-Pay

Agent-Pay is the financial control and payment layer for the agentic internet.

It enables agents to initiate payments under explicit delegated authority, financial policies, budgets, approvals, risk controls, and payment constraints without giving agents unrestricted access to money or primary financial credentials.

## Role in the Agentic Internet

Agent-Pay is intentionally separate from the [Agentic Trust Foundation](https://github.com/Agentic-Trust-Foundation/agentic-trust).

- **Agentic Trust Foundation** establishes authority: identity, delegation, authorization, trust, capability, consent, revocation, provenance, and related evidence.
- **Agent-Pay** applies financial control and executes financial intent: wallets, funding, payment instruments, spending policy, budgets, approval, payment routing, payment execution, transactions, settlement, refunds, reconciliation, and financial ledgering.

> **Trust Foundation answers: "Is this agent authorized?"**
>
> **Agent-Pay answers: "Can this authorized agent spend this money for this transaction, under these financial constraints, and how should it be executed?"**

## Core Principle

> **The Agent should receive spending authority, not financial credentials.**

> **Agent requests; Agent-Pay decides; Payment Rail executes; Ledger records financial truth.**

## Design Position

Agent-Pay follows a **protocol-first, implementation-backed, service-optional** approach. The protocol remains vendor-neutral and interoperable. No single wallet provider, bank, payment processor, blockchain, or identity provider is mandatory.

Agent-Pay is not intended to become a general identity/trust protocol or a complete agentic commerce protocol. It integrates with those ecosystems through explicit adapters and references.

## Core Flow

```text
User → Agent
        ↓ payment intent + authorization evidence
     Agent-Pay
        ├── Authorization Evidence / Delegation Context
        ├── Spending Policy
        ├── Budget / Reservation
        ├── Risk / Authentication
        └── Approval
              ↓
        Payment Router
          ├── Wallet
          ├── Virtual Card
          ├── Bank / PSP
          └── Other Instrument
              ↓
        Merchant / Payment Rail
              ↓ async events / webhooks
        Transaction → Settlement / Reconciliation → Ledger
```

## Financial Control Model

```text
Policy    = Is this spending permitted?
Budget    = Is enough allocated capacity available?
Wallet    = Is enough actual money available?
Approval  = Is explicit human approval required?
Payment   = How is the financial operation executed?
Ledger    = What is the authoritative financial record?
```

Passing one control never implies passing the others.

## V1 Architecture

V1 is a **modular monolith** backed by PostgreSQL, with a transactional outbox and asynchronous worker.

```text
API
 ↓
Agent-Pay Core
 ├── Authorization Context
 ├── Policy
 ├── Budget
 ├── Approval
 ├── Payment Orchestrator
 ├── Payment Router / Adapters
 ├── Wallet / Ledger
 ├── Transaction
 ├── Reconciliation
 ├── Audit
 └── Notification
 ↓
PostgreSQL + Outbox
```

Redis may support ephemeral concerns such as rate limiting or caching, but never becomes the financial source of truth.

## Scope

### In scope

- Funding, wallets and wallet accounts
- Payment instruments and future virtual-card integration
- Payment Intent / Payment Request
- Spending Policy
- Budgets and reservations
- Approval workflows
- Payment authentication boundary
- Payment routing and provider integration
- Transaction lifecycle
- Settlement and reconciliation
- Refunds and reversals
- Financial ledger
- Provider webhooks and asynchronous events
- Audit and notifications
- Integration with agentic commerce protocols
- Integration with Agentic Trust Foundation authorization evidence

### Out of scope

- General agent identity
- General-purpose authorization protocol
- General agent reputation/trust network
- General delegation protocol
- Healthcare/cloud authorization
- Enterprise IAM replacement
- Central global trust authority
- Mandatory blockchain or cryptocurrency
- Mandatory payment provider
- Full product catalog / fulfillment / commerce protocol

## Payment Lifecycle

```text
REQUESTED
 → VALIDATING
 → AUTHENTICATION_REQUIRED / AUTHENTICATED
 → POLICY_CHECK
 → BUDGET_CHECK
 → APPROVAL_REQUIRED / APPROVED
 → PAYMENT_PENDING
 → PROCESSING
 → SUCCEEDED / FAILED
 → SETTLEMENT / RECONCILIATION
```

Refunds, reversals, disputes, chargebacks, and provider reconciliation are separate auditable financial operations.

## Current Status

The repository is in the architecture/specification phase. V1 domain, ledger, database, API, security, authorization-evidence, routing, asynchronous events/webhooks, settlement/reconciliation, financial lifecycle, idempotency/concurrency, tokenization, budget reservation, policy, budget, approval, payment state machine, authentication, commerce boundary, financial invariants, and reference-implementation architecture are defined.

It is **not yet a production payment system**. Provider integrations, production security controls, regulatory/compliance analysis, operational hardening, and the executable reference implementation remain implementation work.

## Relationship with Agentic Trust Foundation

Agent-Pay consumes trust decisions and authorization evidence rather than redefining them.

- Trust policy: *Can this agent perform this kind of action?*
- Spending policy: *Can this agent spend this amount, from this account/instrument, with these financial constraints?*

## Integration with Agentic Commerce

Agent-Pay may consume order, checkout, cart, or merchant references from agentic commerce protocols such as UCP, ACP, or future standards. Those references provide commerce context; Agent-Pay remains responsible for financial authorization and execution rather than becoming the catalog or fulfillment system.

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

- Least privilege and explicit authorization evidence
- No primary financial credentials to agents
- Tokenized/opaque payment instrument references
- Server-side policy enforcement and fail-closed decisions
- Multi-layer idempotency and replay protection
- Authenticated provider webhooks
- Immutable financial history and compensating corrections
- Reconciliation for ambiguous external outcomes

## License

License and governance terms will be established before the first normative protocol release.
