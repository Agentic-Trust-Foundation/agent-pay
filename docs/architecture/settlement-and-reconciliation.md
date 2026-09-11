# Settlement and Reconciliation

## Purpose

Payment authorization, payment execution, settlement, and ledger accounting are related but distinct concerns.

Agent-Pay must be able to compare internal financial records with external provider or payment-rail records without treating a provider response as the final accounting truth.

## Model

```text
Payment Intent
      |
      v
Payment Execution
      |
      v
Provider Transaction
      |
      v
Settlement Observation
      |
      v
Internal Transaction / Ledger
      |
      v
Reconciliation
```

## References

External and internal records should be correlated using durable references such as:

- payment_id
- transaction_id
- provider_reference
- provider_event_id
- settlement_reference
- idempotency_key

## Reconciliation outcomes

A reconciliation process should classify records as:

- MATCHED
- PENDING
- UNMATCHED_INTERNAL
- UNMATCHED_PROVIDER
- AMOUNT_MISMATCH
- CURRENCY_MISMATCH
- STATUS_MISMATCH
- REFERENCE_MISMATCH
- DUPLICATE
- REQUIRES_REVIEW

## Important rule

A mismatch must never be silently corrected by mutating historical ledger entries.

Corrections should use explicit compensating entries or controlled adjustments with an audit trail.

## Settlement is not authorization

A payment may be:

```text
AUTHORIZED
PROCESSING
SUCCEEDED
SETTLED
```

without these states being interchangeable.

The exact provider lifecycle may vary. Agent-Pay therefore keeps provider status mapping in the payment adapter layer and exposes normalized internal states.

## Reconciliation cadence

V1 can support:

- event-driven reconciliation after provider events
- scheduled status verification for ambiguous payments
- periodic provider statement reconciliation

The architecture must not require continuous real-time settlement feeds.

## Mismatch handling

```text
Provider record
      |
      v
Reconciliation
   /    |     \
 MATCH  PENDING  MISMATCH
                 |
                 v
             Review Queue
                 |
                 v
        Compensating Adjustment
```

Manual review is acceptable for V1. Automated correction is not permitted unless the correction rule is deterministic, auditable, and explicitly authorized.

## V1 boundary

V1 defines the data model and interfaces for reconciliation but does not attempt to implement bank settlement, network settlement, FX accounting, chargeback accounting, or jurisdiction-specific regulatory reporting.
