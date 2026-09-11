# Extended Financial Lifecycle

## Purpose

The financial lifecycle extends beyond a successful payment. Agent-Pay must preserve distinct states and records for authorization, authentication, execution, settlement, refund, reversal, and dispute.

## Lifecycle

```text
Payment Request
      |
      v
Authorization
      |
      v
Policy / Budget / Risk
      |
      v
Approval
      |
      v
Payment Authentication (optional)
      |
      v
Authorization at Rail
      |
      v
Capture / Execution
      |
      v
Provider Processing
      |
      v
Settlement
      |
      +----> Refund
      |
      +----> Reversal
      |
      +----> Dispute / Chargeback
```

## Authentication

Card-based payment instruments may require an authentication step such as EMV 3-D Secure. This is represented as a payment state, not hidden inside a synchronous API call.

```text
PROCESSING
   |
   v
AUTHENTICATION_REQUIRED
   |
   v
AUTHENTICATED
   |
   v
PROCESSING
```

## Refund

A refund is a new financial event and must create explicit records. Partial refunds are supported conceptually.

## Reversal

A reversal represents undoing or reversing a prior financial operation and must reference the original transaction.

## Dispute / Chargeback

A dispute or chargeback is not equivalent to a merchant refund. It may be initiated externally and may have its own lifecycle and evidence.

V1 should preserve the model boundary even if production dispute automation is deferred.

## State-machine rule

Historical financial states are immutable. New information creates a new event, transition, or compensating transaction rather than rewriting history.

## V1 boundary

The core domain model must be extensible for authentication, settlement, refund, reversal, and dispute even when only wallet payments are implemented initially.
