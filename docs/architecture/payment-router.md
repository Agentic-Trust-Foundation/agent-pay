# Payment Router

Stage 8 defines the Agent-Pay payment-routing boundary between payment orchestration and external payment rails.

## Responsibilities

The router selects a payment provider using explicit, deterministic route constraints such as merchant domain and currency. The selected provider owns the external payment operation; the router does not hold or expose merchant credentials.

```text
PaymentRequest
    |
    v
Policy / Budget / Approval
    |
    v
PaymentService
    |
    v
PaymentRouter
   / \
  /   \
Wallet  Virtual Card
 Rail      Rail
  |          |
  +---- Payment Rail ----+
```

## Routing rules

1. A route may constrain merchant domains and/or currencies.
2. Routes are evaluated in registration order; the first matching route wins.
3. A default route is represented by an unconstrained route.
4. If no route matches, the payment must not be sent to an external provider.
5. Provider idempotency keys remain stable (`payment:{payment_id}:charge`).
6. External `UNKNOWN_EXTERNAL_OUTCOME` remains unknown; the router must not convert it to failure.

## Reference rails

The reference implementation includes deterministic simulated `WalletRail` and `VirtualCardRail` adapters. They are conformance/test adapters, not production financial providers and do not contain real credentials.

Production integrations should implement `PaymentProvider` as separate adapters for each PSP, card processor, wallet, bank, or future payment rail.

## Security boundary

Agent-Pay receives delegated spending authority and payment intent data. Provider credentials remain behind the provider adapter boundary. Agent credentials and financial credentials are never interchangeable.

## V1 completion criteria

- explicit provider registration and route selection
- deterministic no-route failure
- multiple reference rails
- provider idempotency preserved
- payment service integrated with routing
- routing tests covering selection, fallback, rejection, and idempotency
