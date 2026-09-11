# Agent-Pay Budget Model

## Purpose

A Budget is a quantitative spending-capacity constraint. It limits how much an Agent or Account may allocate to spending during a defined scope and period.

> **Budget answers: is enough allocated spending capacity available?**

Budget is distinct from Policy and Wallet funds.

```text
Policy = may this payment happen?
Budget = is enough allocated capacity available?
Wallet = is enough actual money available?
```

## Resource Separation

```text
Budget Capacity
      ≠
Wallet Available Funds
      ≠
Provider Authorization / Hold
```

A payment can satisfy policy and have sufficient wallet funds while still exceeding its assigned budget.

## Core Model

A budget should conceptually contain:

```text
Budget
├── id
├── account_id
├── scope
├── currency
├── limit
├── consumed
├── reserved
├── available
├── period
├── status
├── starts_at
├── ends_at
├── policy_reference
└── metadata
```

The authoritative financial meaning is:

```text
available = limit - consumed - reserved
```

The implementation may cache derived values, but concurrent updates must preserve this invariant transactionally.

## Scope

V1 should support enough structure for future dimensions without coupling the budget to a specific commerce protocol.

Possible scopes include:

- account
- agent
- delegation
- merchant category
- merchant
- payment purpose
- instrument class

A budget may be associated with an Agent and constrained by a Delegation while remaining owned by the Account.

## Periods

Supported conceptual windows:

- per transaction
- daily
- weekly
- monthly
- custom validity period

Each budget must define its timezone semantics when calendar periods are used. The system must not silently interpret local calendar boundaries using an arbitrary server timezone.

## Reservation

A budget reservation temporarily consumes capacity while a Payment Request is being processed or awaiting approval.

```text
AVAILABLE
   |
   v
RESERVED
   |
   +----> CONSUMED
   |
   +----> RELEASED
   |
   +----> EXPIRED
```

Active reservations count against available capacity.

The reservation must have its own identity and be idempotent against the Payment Request or equivalent reservation key.

## Approval Interaction

For an approval-required request:

```text
Payment Request
   ↓
Policy
   ↓
Budget Check
   ↓
Budget Reservation
   ↓
Approval
   ├── DENIED / EXPIRED / CANCELLED → Release
   └── APPROVED → Continue
```

The reservation prevents two concurrent requests from both assuming the same capacity.

A wallet/provider hold is a separate financial resource and must not be represented as a budget reservation.

## Consumption

On successful financial execution, the budget reservation becomes consumed.

```text
reserved += amount

success:
  reserved -= amount
  consumed += amount

failure/cancel:
  reserved -= amount
```

The transition must be atomic and idempotent.

## Concurrency

Budget capacity is a shared resource and is subject to race conditions.

V1 should use PostgreSQL transactional locking and/or a conditional update that guarantees:

```text
consumed + reserved + requested_amount <= limit
```

Two concurrent requests must never both succeed against the same remaining capacity.

The database is the authority for the atomic reservation operation.

## Idempotency

Budget operations must tolerate retries.

At minimum, the system needs a stable reservation identity such as:

```text
budget_id + payment_request_id
```

Repeated reservation requests for the same payment request must return the existing reservation rather than allocate capacity again.

Consumption and release operations must likewise be idempotent.

## Currency

V1 budgets are currency-bound.

```text
USD budget → USD payment
EUR budget → EUR payment
```

No implicit FX conversion is allowed.

A future multi-currency budget must explicitly define:

- FX source
- rate timestamp
- rounding
- tolerance
- accounting currency
- conversion risk

## Budget Hierarchy

A future implementation may support hierarchical budgets:

```text
Account monthly budget: $10,000
        |
        +-- Agent A: $3,000
        |      +-- Electronics: $1,000
        |
        +-- Agent B: $2,000
```

V1 should avoid unnecessarily complex hierarchy semantics, but the domain model must not prevent them.

If multiple applicable budgets exist, all required constraints must pass. A child budget must never expand a parent budget.

## Policy Interaction

Policy and Budget are complementary:

```text
Policy
  ↓
permitted?
  ↓ yes
Budget
  ↓
capacity available?
  ↓ yes
Funds / Instrument
```

A policy decision cannot grant additional budget capacity.

A budget cannot override a policy denial.

## Wallet Interaction

Budget capacity is an authorization constraint, not money.

Example:

```text
Wallet available: $1,000
Budget remaining: $250
Request: $300
```

The request fails budget evaluation even though the wallet has sufficient funds.

Conversely:

```text
Wallet available: $100
Budget remaining: $500
Request: $300
```

The request passes budget evaluation but fails later because actual funds are insufficient.

## Failure and Recovery

Reservations must be released when a payment is definitively denied, cancelled, expired, or failed before financial consumption.

If the external provider outcome is ambiguous, the budget reservation must remain protected until recovery or reconciliation determines the financial result.

Timeout alone must not automatically release capacity if an external payment may have succeeded.

## Auditability

Every budget state transition should be traceable to:

- budget identifier
- payment request
- reservation identifier
- actor/system component
- previous state
- new state
- amount
- timestamp
- idempotency key
- correlation identifier

Historical budget decisions must remain reconstructable.

## V1 Boundaries

V1 does not attempt to implement:

- FX-aware budgets
- predictive budget optimization
- credit facilities
- overdraft
- cross-account lending
- complex tax accounting
- external bank settlement

The model remains extensible for these capabilities later.
