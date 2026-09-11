# Agent-Pay Ledger Model V1

## Purpose

The ledger is the financial source of truth for Agent-Pay. Wallet balances, available balances, holds, releases, debits, credits, refunds, and adjustments must be explainable from ledger state.

## Core Rule

> **Never treat a mutable wallet balance field as the authoritative financial record.**

A wallet may cache derived balances for performance, but the ledger remains authoritative.

## Ledger Concepts

```text
Wallet
  ↓
Ledger Account
  ↓
Ledger Entries
  ├── CREDIT
  ├── DEBIT
  ├── HOLD
  ├── RELEASE
  ├── REFUND
  └── ADJUSTMENT
```

### Ledger Account

A ledger account represents a balance-bearing financial account inside the Agent-Pay ledger. A Wallet maps to a ledger account for V1.

### Ledger Entry

A ledger entry is an immutable record of a financial state transition. Corrections are represented by compensating entries rather than editing historical financial facts.

Each entry should include at minimum:

```text
id
ledger_account_id
entry_type
amount
currency
reference_type
reference_id
status
created_at
metadata
```

Amounts are represented using exact decimal semantics. Floating-point arithmetic must not be used for monetary calculations.

## Balance Semantics

For a wallet:

```text
balance
  = posted credits
  - posted debits
  + posted refunds
  + adjustments
```

Available balance must additionally exclude funds reserved by active holds:

```text
available_balance
  = balance - active_hold_amount
```

The exact accounting implementation may use double-entry ledger accounts internally, but the public Wallet abstraction must preserve these semantics.

## Holds

A hold reserves funds before the final debit is posted.

Example:

```text
Initial balance:          1000

HOLD:                       200
-------------------------------
Balance:                  1000
Available balance:         800
```

A hold is not a completed payment. It prevents another concurrent operation from consuming the same available funds.

### Successful Capture

```text
Initial available: 1000
HOLD:                200
CAPTURE/DEBIT:       200

Final balance:       800
Available balance:   800
```

The implementation must ensure that the hold and its conversion to a debit cannot leave the wallet in an inconsistent intermediate financial state.

### Failed Payment

```text
Initial balance: 1000
HOLD:              200
PAYMENT FAILED
RELEASE:           200

Final balance:     1000
Available balance: 1000
```

A failed external payment must never silently consume the held funds.

## Funding

Funding creates a credit against the wallet ledger account after the funding operation has been accepted according to the funding-source contract.

```text
Funding source
      ↓
   CREDIT
      ↓
Wallet ledger account
```

Funding must be idempotent and must retain an external reference when the funding source provides one.

## Payment Debit

A successful wallet-funded payment produces a debit effect:

```text
Wallet
  ↓
DEBIT 100 USD
  ↓
Payment / Transaction reference
```

The debit must be linked to the Payment and Transaction records so an operator can trace the complete financial chain.

## Refunds

Refunds do not mutate the original debit. They create a new financial record linked to the original transaction.

```text
Original payment
      ↓
Original DEBIT
      ↓
Refund
      ↓
REFUND CREDIT
```

Partial refunds must be supported by the domain model. The aggregate refunded amount must never exceed the refundable amount of the original transaction.

## Adjustments

Adjustments are exceptional corrective financial entries. They must require privileged authorization and an auditable reason.

Historical entries must not be edited or deleted to correct a financial mistake.

## Atomicity and Concurrency

Wallet financial state transitions must be atomic at the database level.

For a hold operation:

```text
BEGIN
  lock wallet/ledger account
  verify active balance
  verify available funds
  create HOLD entry
  update/derive reservation state
COMMIT
```

Concurrent payment attempts must not both succeed against the same available funds.

Database transactions and row-level locking or an equivalent concurrency mechanism must be used where required.

## Idempotency

Financial commands must be safely retryable.

A command should retain an idempotency key and a deterministic operation reference. A repeated request must resolve to the original financial result instead of creating another credit, hold, debit, release, or refund.

Reusing a key with different financial parameters must fail with a conflict.

## State Rules

Valid high-level hold lifecycle:

```text
ACTIVE
 ├── CAPTURED
 ├── RELEASED
 └── EXPIRED
```

Valid payment-related ledger lifecycle:

```text
REQUESTED
   ↓
HOLD
   ├── DEBIT
   └── RELEASE
```

A released hold cannot later be captured. A captured hold cannot later be released as if it were still available.

## Currency

Each ledger account has a defined currency for V1. Cross-currency operations require an explicit conversion/FX model and are outside the initial wallet ledger scope.

No implicit currency conversion is allowed.

## Double-Entry Direction

The V1 domain model exposes a wallet-centric ledger, but the implementation should be compatible with double-entry accounting.

Conceptually:

```text
Funding:
External Funding Account  →  Wallet Account

Payment:
Wallet Account            →  Settlement/Provider Account

Refund:
Settlement/Provider      →  Wallet Account
```

This gives Agent-Pay a path toward stronger financial reconciliation without coupling the public API to accounting implementation details.

## Auditability

Every financial mutation must be traceable to:

```text
actor
operation
payment/request/reference
idempotency key
correlation ID
ledger entry
created_at
```

Ledger history should be append-oriented and operationally protected from unauthorized modification.

## V1 Boundary

V1 requires:

- exact monetary arithmetic
- immutable ledger entries
- wallet-to-ledger mapping
- credit/debit/hold/release/refund/adjustment semantics
- atomic financial transitions
- idempotency
- concurrency protection
- transaction references
- audit linkage

V1 does not yet define:

- production bank settlement
- multi-currency accounting
- FX pricing
- chargebacks
- card-network settlement
- regulatory accounting requirements for a specific jurisdiction

Those belong to later payment-rail and compliance specifications.
