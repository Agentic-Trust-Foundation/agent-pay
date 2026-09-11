# Agent-Pay Transaction Lifecycle

## Overview

A payment starts as an Agent intent and becomes a financial transaction only after identity/delegation context, spending policy, budget, approval, and payment execution have been evaluated.

```text
Agent
  ↓
Payment Request
  ↓
Authenticate Agent
  ↓
Verify Delegation
  ↓
Policy Check
  ↓
Budget Check
  ↓
Risk Check
  ↓
Approval Decision
  ├── AUTO ───────────────┐
  ├── NOTIFY ─────────────┤
  └── APPROVAL_REQUIRED → User Approval
                           │
                           ▼
                    Payment Router
                           ↓
                    Payment Instrument
                           ↓
                      Payment Rail
                           ↓
                       Merchant
                           ↓
                     Transaction
                           ↓
                   Ledger / Audit
                           ↓
                      Notification
```

## Request States

The logical state progression is:

```text
REQUESTED
   ↓
VALIDATING
   ↓
POLICY_CHECK
   ├── DENIED
   ↓
BUDGET_CHECK
   ├── DENIED
   ↓
APPROVAL_CHECK
   ├── AUTO ───────────────────┐
   ├── NOTIFY ─────────────────┤
   └── APPROVAL_REQUIRED       │
             ↓                 │
          APPROVED              │
             └──────────────────┘
                    ↓
             PAYMENT_PENDING
                    ↓
                PROCESSING
                 ┌──┴──┐
                 ↓     ↓
            SUCCEEDED  FAILED
                 ↓
          REFUND_REQUESTED
                 ↓
              REFUNDED
```

## Approval Modes

Agent-Pay supports three conceptual policy outcomes:

- **AUTO** — payment may execute immediately when all controls pass.
- **NOTIFY** — payment may execute, followed by a user notification.
- **APPROVAL_REQUIRED** — execution pauses until an authorized user approves.

Thresholds are configurable policy data and are not hard-coded into the protocol.

## Wallet Holds

When a wallet is used, authorization should reserve the required amount before execution where appropriate:

```text
Available Balance
       ↓
     HOLD
       ↓
 Payment Execution
    ┌──┴──┐
    ↓     ↓
 SUCCESS  FAILURE
    ↓       ↓
  DEBIT   RELEASE
```

A successful payment converts the reserved amount into a ledger debit. A failed or cancelled payment releases the hold.

## Idempotency

Payment creation must accept an idempotency key. Repeating the same request with the same key must not create duplicate financial effects.

Idempotency applies especially to retries around network failures and external payment-provider timeouts.

## Financial Truth

The authoritative sequence is:

```text
Payment Request
      ↓
Payment
      ↓
Transaction
      ↓
Ledger Entry
```

The ledger is the source of truth for financial state. Cached balances or payment status fields must not become an independent financial authority.

## Auditability

The lifecycle should produce correlated audit events such as:

- `PaymentRequested`
- `PolicyEvaluated`
- `BudgetReserved`
- `ApprovalRequested`
- `PaymentApproved`
- `PaymentDenied`
- `PaymentStarted`
- `PaymentSucceeded`
- `PaymentFailed`
- `WalletCredited`
- `WalletDebited`
- `RefundCreated`

A correlation identifier should allow an investigator to reconstruct the complete lifecycle of a payment request.
