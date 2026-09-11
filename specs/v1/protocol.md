# Agent-Pay V1 Protocol

## Purpose

Agent-Pay is a financial control and payment layer for AI agents. The agent submits financial intent; Agent-Pay determines whether the intent is authorized and financially permitted, then executes through an abstract payment instrument or provider rail.

## Boundary

- Agentic Trust Foundation establishes identity, delegation, authorization, trust and related evidence.
- Agent-Pay evaluates financial policy, budget, approval and payment execution.
- Payment rails execute external financial operations.
- The ledger records financial truth.

Agent-Pay is not a general identity network, trust registry, merchant order system, or fulfillment system.

## Canonical request flow

```text
Agent
  -> Payment Request
  -> Authentication / Authorization Context
  -> Policy Evaluation
  -> Budget Reservation
  -> Approval when required
  -> Payment Execution
  -> Provider Operation
  -> Transaction
  -> Double-entry Ledger
  -> Settlement / Reconciliation
```

## Payment states

`REQUESTED`, `POLICY_CHECK`, `BUDGET_CHECK`, `APPROVAL_REQUIRED`, `APPROVED`, `AUTHENTICATION_REQUIRED`, `AUTHENTICATED`, `PAYMENT_PENDING`, `PROCESSING`, `UNKNOWN_EXTERNAL_OUTCOME`, `SUCCEEDED`, `FAILED`, `CANCELLED`.

Capture/void/refund and settlement outcomes remain distinct lifecycle concepts.

## Control rules

- A delegation does not bypass policy.
- Policy does not create budget capacity.
- Budget reservation is distinct from wallet hold and available balance.
- Approval is bound to the exact payment intent.
- A PaymentRequest is not a Payment.
- A Payment is not a Transaction.
- Transaction history is append-oriented.
- Double-entry journals must balance per currency.
- Provider timeouts resolve through query/webhook/reconciliation rather than being assumed failed.
- Provider events are verified, persisted, deduplicated and processed idempotently.

## Idempotency

Every financial mutation has a stable idempotency boundary. Reusing an API idempotency key with materially different request data is a conflict. Provider operations use stable operation-specific keys. Provider events and settlement references are deduplicated.

## Interoperability

The protocol accepts commerce context and authorization evidence references without making those external protocols part of the Agent-Pay system of record. Implementations may integrate UCP, ACP, ATF, OAuth/OIDC, AP2, A2A or other ecosystems through adapters and explicit evidence mappings.
