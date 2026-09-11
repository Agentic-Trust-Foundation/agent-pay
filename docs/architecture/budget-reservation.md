# Budget Reservation

## Purpose

A budget represents spending capacity. It is distinct from wallet funds and from the wallet's payment hold.

## Three distinct resources

```text
Budget capacity
    ≠
Wallet available funds
    ≠
Provider authorization / hold
```

Example:

```text
Wallet available: $1,000
Budget remaining: $500
Payment request:  $300
```

The request may reserve $300 of budget capacity and later place a separate $300 wallet/provider hold.

## Reservation lifecycle

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

## Atomicity

Budget availability must be checked and reserved atomically. Two concurrent requests must not consume the same remaining capacity.

The reservation must be idempotent by payment request / reservation identity.

## Approval interaction

For an approval-required payment, V1 should distinguish:

1. policy decision
2. budget availability
3. budget reservation
4. user approval
5. wallet/provider hold
6. final consumption

A policy may reject before reservation. An approval flow may reserve budget capacity to prevent a second request from consuming the same budget while the user decides.

The exact reservation timing is an implementation policy, but the invariant is that approved execution cannot silently exceed the budget.

## Failure handling

If a payment is denied, cancelled, expires, or definitively fails before budget consumption, the reservation is released.

If the payment succeeds, the reservation becomes consumed.

## Periodic budgets

Budget windows may be:

- per transaction
- daily
- weekly
- monthly
- custom validity period

The system must define whether an active reservation counts against the window until released or consumed. V1 should count active reservations against available capacity.

## Currency

A budget is currency-bound unless a future FX-aware budget explicitly defines conversion rules. V1 must not silently convert currencies.

## Relationship to Policy

Policy answers:

> Is this type of spending permitted?

Budget answers:

> Is there enough allocated spending capacity remaining?

Wallet answers:

> Is there enough actual money available?

These checks must remain separate.
