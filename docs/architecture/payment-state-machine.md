# Agent-Pay Payment State Machine

## Purpose

The payment state machine defines the lifecycle of a Payment Request and its execution without treating a synchronous provider response as the only source of truth.

## Lifecycle

```text
REQUESTED
   ↓
VALIDATING
   ↓
AUTHENTICATION_REQUIRED ──→ AUTHENTICATED
   ↓
POLICY_CHECK
   ├── DENIED
   ↓
BUDGET_CHECK
   ├── DENIED
   ↓
APPROVAL_CHECK
   ├── AUTO
   ├── NOTIFY
   └── APPROVAL_REQUIRED
             ↓
          APPROVED
             ↓
      PAYMENT_PENDING
             ↓
        PROCESSING
             ↓
      ┌──────┴────────┐
      ↓               ↓
   SUCCEEDED        FAILED
      ↓
   SETTLEMENT
```

The implementation may combine internal technical states, but externally observable transitions must preserve the financial meaning above.

## Authentication

Authentication can be required by the payment rail or by Agent-Pay risk controls.

`AUTHENTICATION_REQUIRED` must be explicit so the API does not incorrectly report a payment as failed when the provider requires a challenge or additional user action.

Examples include 3-D Secure or another provider-specific authentication step.

## Policy and Budget

Policy and budget checks are separate:

```text
Policy → permitted?
Budget → capacity available?
Wallet/instrument → funds/authorization available?
```

A policy denial is not a budget failure and a budget failure is not a provider failure.

## Approval

The approval state is derived from policy and risk requirements.

```text
AUTO
  → continue

NOTIFY
  → continue + notification

REQUIRE_APPROVAL
  → APPROVAL_REQUIRED
  → APPROVED
  → continue
```

An approval decision is bound to the exact payment request and authorization context.

## Provider Execution

Provider execution is asynchronous by nature even when an API call returns synchronously.

A timeout or connection failure may leave the external state unknown.

```text
PROCESSING
   ↓
UNKNOWN_EXTERNAL_OUTCOME
   ↓
Webhook / Query / Reconciliation
   ├── SUCCEEDED
   └── FAILED
```

Agent-Pay must not infer `FAILED` solely from a client/provider timeout when the provider may have accepted the payment.

## Settlement

Settlement is distinct from authorization/capture.

A future provider integration may produce:

```text
AUTHORIZED
 → CAPTURED
 → SETTLEMENT_PENDING
 → SETTLED
```

V1 may collapse some provider-specific states internally, but the domain must remain extensible for settlement reconciliation.

## Refunds

Refund is a separate lifecycle from the original payment:

```text
SUCCEEDED
   ↓
REFUND_REQUESTED
   ↓
REFUND_PROCESSING
   ├── REFUNDED
   └── REFUND_FAILED
```

Partial refunds must be supported by the transaction model even if V1 UI exposes only a simple refund operation.

## Reversal

A reversal/void is distinct from a refund because it may occur before settlement or capture is finalized.

The system must preserve the original operation and create an auditable compensating effect rather than rewriting history.

## Dispute / Chargeback

A future payment rail may report:

```text
SUCCEEDED / SETTLED
   ↓
DISPUTED
   ↓
CHARGEBACK
```

These states are not equivalent to a merchant refund and must remain extensible in the transaction lifecycle.

## Terminal States

Typical terminal states include:

- `SUCCEEDED`
- `FAILED`
- `CANCELLED`
- `REFUNDED`
- `EXPIRED`

Provider-specific and reconciliation states may remain non-terminal until financial truth is established.

## Idempotent Transitions

Each transition must be safe to retry.

Invalid duplicate transitions must not create duplicate ledger postings or duplicate provider operations.

The system should persist provider operation identifiers and internal transition/event identifiers.

## Ledger Interaction

Payment state changes and financial ledger effects must be coordinated transactionally for internal state.

External provider calls cannot participate in the PostgreSQL transaction. Therefore:

```text
DB transaction
  → persist intent / operation
  → commit
  → call provider
  → persist result/event
  → ledger posting when financial outcome is established
```

Recovery and reconciliation handle ambiguous external outcomes.

## V1 Direction

V1 should use a durable Payment state machine in the modular monolith, PostgreSQL persistence, explicit transition validation, idempotency keys, provider references, and event-driven recovery through the outbox/webhook architecture.
