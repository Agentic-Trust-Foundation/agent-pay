# Agent-Pay

Agent-Pay is the financial execution layer for the agentic internet.

It enables agents to initiate payments under explicit financial policies, risk controls, approvals, and payment constraints without giving agents unrestricted access to money or payment instruments.

## Role in the Agentic Internet

Agent-Pay is intentionally separate from the [Agentic Trust Foundation](https://github.com/Agentic-Trust-Foundation/agentic-trust).

- **Agentic Trust Foundation** establishes authority: identity, delegation, authorization, trust, capability, consent, revocation, provenance, and auditability.
- **Agent-Pay** executes financial intent: funding, wallets, payment instruments, spending policy, risk, approval, routing, payment execution, transactions, settlement, refunds, and financial ledgering.

The boundary is simple:

> **Trust Foundation answers: "Is this agent authorized?"**
>
> **Agent-Pay answers: "Can this authorized agent spend this money for this transaction, and how should it be executed?"**

## Design Position

Agent-Pay follows a **protocol-first, implementation-backed, service-optional** approach.

The protocol should remain interoperable and vendor-neutral. A reference implementation may be provided, but no single hosted service, wallet provider, bank, payment processor, blockchain, or identity provider is mandatory.

## Core Flow

```text
User
  |
  | delegates authority
  v
Agent
  |
  | payment intent
  v
Agentic Trust Foundation
  |
  | authorization / delegation decision
  v
Agent-Pay
  |
  +--> Spending Policy
  +--> Risk
  +--> Approval
  |
  v
Payment Decision
  |
  v
Payment Router
  |
  +--> Wallet
  +--> Virtual Card
  +--> Other Payment Instrument
  |
  v
Merchant / Payment Rail
  |
  v
Transaction -> Settlement -> Ledger
```

## Core Principle

> **Agent requests; Agent-Pay decides; Payment Rail executes; Ledger records financial truth.**

## Scope

### In scope

- Funding
- Wallets and wallet accounts
- Payment instruments
- Virtual cards
- Payment Intent
- Spending Policy
- Risk evaluation
- Approval workflows
- Payment routing
- Payment processing integration
- Transaction lifecycle
- Settlement
- Refunds
- Financial ledger
- Merchant payment integration
- Notifications and financial events

### Out of scope

- General agent identity
- General-purpose authorization
- General agent reputation/trust network
- General delegation protocol
- Healthcare authorization
- Cloud authorization
- Enterprise IAM replacement
- Central global trust authority
- Mandatory blockchain or cryptocurrency
- Mandatory payment provider

## Repository Structure

```text
agent-pay/
├── docs/
│   ├── vision/
│   ├── architecture/
│   ├── protocol/
│   ├── security/
│   ├── governance/
│   └── integration/
├── specs/
│   └── v1/
├── reference/
│   └── implementation/
├── conformance/
├── schemas/
├── examples/
├── test-vectors/
└── tools/
```

## Current Status

The repository is currently establishing the architecture, protocol boundaries, terminology, security model, and conformance direction. It is not yet a production payment system.

## Relationship with Agentic Trust Foundation

Agent-Pay consumes trust decisions rather than redefining them. A payment request can carry evidence of the agent's identity, delegation, authorization, and relevant capabilities established through the Trust Foundation protocol.

Financial controls remain local to Agent-Pay. In particular, **trust policy** and **spending policy** are different concerns:

- Trust policy: *Can this agent perform this kind of action?*
- Spending policy: *Can this agent spend this amount, from this funding source, with these constraints?*

## License

License and governance terms will be established before the first normative protocol release.
