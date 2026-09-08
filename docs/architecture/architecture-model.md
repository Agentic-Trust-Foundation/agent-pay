# Architecture Model

```text
Agent
  |
  | Payment Intent
  v
Agentic Trust Foundation
  |
  | identity + delegation + authorization evidence
  v
Agent-Pay
  |
  +--> Spending Policy
  +--> Risk Engine
  +--> Approval Engine
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
Payment Rail / Merchant
  |
  v
Transaction -> Settlement -> Ledger
```

## Logical boundaries

The architecture describes logical responsibilities, not a mandatory microservice topology. An initial implementation may be a modular monolith and split into services when operational or organizational needs justify it.

## Core rule

**Agent requests; Agent-Pay decides; Payment Rail executes; Ledger records financial truth.**

## Separation of policies

- Trust policy: whether the agent has authority to perform the requested action.
- Spending policy: whether the requested financial operation is permitted under monetary, merchant, instrument, timing, and contextual constraints.

A successful trust decision does not automatically imply a successful payment decision.
