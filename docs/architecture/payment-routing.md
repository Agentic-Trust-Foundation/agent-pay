# Payment Routing

## Purpose

Payment routing separates the Agent's financial intent from the payment instrument and external payment rail used to execute it.

## Core Rule

> **The Agent requests a payment; Agent-Pay selects and controls the payment instrument.**

The Agent must not need to know whether a payment is executed from a wallet, virtual card, bank account, PSP, or a future instrument.

## Routing Flow

```text
Agent
  |
  | Payment Request
  v
Agent-Pay Core
  |
  +--> Authentication / Trust Context
  +--> Delegation Check
  +--> Spending Policy
  +--> Budget Check
  +--> Approval
  +--> Risk
  |
  v
Payment Router
  |
  +--> Wallet Adapter
  +--> Virtual Card Adapter
  +--> Bank / PSP Adapter
  +--> Future Instrument Adapter
  |
  v
Payment Rail
  |
  v
Merchant
```

## Payment Instrument Abstraction

A payment instrument should expose a stable execution contract rather than provider-specific details:

```text
authorize()
capture()
void()
refund()
```

The concrete adapter owns provider-specific authentication, API formats, retries, and error mapping.

## Routing Decision Inputs

The router may consider:

- approved payment amount and currency
- account and wallet availability
- policy constraints
- permitted payment instruments
- merchant requirements
- instrument status
- supported currencies
- provider availability
- risk decision
- transaction limits
- idempotency key

Routing must never bypass an already-evaluated financial control.

## Example

```text
Payment Request: USD 850
        |
        v
Policy: allowed
Budget: sufficient
Approval: approved
        |
        v
Router
  |
  +-- Wallet: insufficient
  |
  +-- Virtual Card: eligible
  |
  +-- Bank: eligible but lower priority
        |
        v
Virtual Card Adapter
        |
        v
Payment Provider
        |
        v
Merchant
```

## Failure Handling

Provider failures must not silently create a successful financial state.

Typical lifecycle:

```text
PAYMENT_REQUESTED
        |
        v
AUTHORIZED
        |
        v
ROUTING
        |
        v
PROCESSING
   +----+----+
   |         |
   v         v
SUCCESS    FAILURE
   |         |
   v         v
CAPTURED   RELEASE / RETRY / FAILED
   |
   v
TRANSACTION
   |
   v
LEDGER
```

Retries must be idempotent and provider-specific retry behavior must not produce duplicate charges.

## Separation of Concerns

| Concern | Owner |
|---|---|
| Agent identity | Agentic Trust Foundation / caller identity layer |
| Delegated authority | Agentic Trust Foundation |
| Spending policy | Agent-Pay |
| Budget | Agent-Pay |
| Human approval | Agent-Pay |
| Instrument selection | Agent-Pay |
| Provider integration | Payment Adapter |
| Payment execution | Payment Rail / Provider |
| Financial truth | Agent-Pay Ledger |
| Merchant trust/reputation | Agentic Trust Foundation / ecosystem |

## V1 Boundary

V1 should implement the routing abstraction without requiring multiple live payment providers. A reference wallet adapter can be used first, while the interface remains ready for virtual cards and external payment rails.

This prevents V1 from becoming coupled to a single provider while keeping the architecture implementable.
