# Stage 14 — Settlement / Reconciliation

## V1 contract

Settlement is an external financial assertion. Agent-Pay records the provider
report and reconciles it against the durable provider operation; it does not
silently rewrite payment, budget, or ledger truth because a report arrived.

The reference flow is:

    Provider settlement report
             |
             v
    Settlement identity (provider + settlement reference)
             |
             v
    Provider operation lookup
             |
             +--> unknown reference ------> DISCREPANCY
             |
             +--> operation not succeeded -> STATUS_MISMATCH
             |
             +--> succeeded
                     |
                     v
             amount + currency comparison
                     |
               +-----+------+
               |            |
            MATCHED     DISCREPANCY

## Idempotency

`(provider_name, settlement_reference)` is the settlement idempotency boundary.
The database unique constraint is the source of truth and ingestion uses
`ON CONFLICT DO NOTHING`, so concurrent duplicate reports resolve safely to
`DUPLICATE` instead of creating two settlement records.

Different settlement references may refer to the same provider operation. This
supports corrected/repeated provider reports while keeping each report's
reconciliation conclusion explicit.

## Discrepancies

V1 records, at minimum:

- `UNKNOWN_PROVIDER_REFERENCE`
- `STATUS_MISMATCH`
- `AMOUNT_MISMATCH`
- `CURRENCY_MISMATCH`

A discrepancy is observational. V1 does not automatically adjust payment,
budget, or ledger state. Any financial correction must be an explicit later
operation with its own audit/idempotency boundary.

## Tests

The reference tests cover:

- exact match;
- amount mismatch;
- currency mismatch;
- provider-operation status mismatch;
- unknown provider reference;
- duplicate settlement report;
- multiple settlement reports for one provider operation.

## V1 boundary

V1 does not implement a live bank/PSP settlement feed, automated exception
queue, chargeback/dispute operations, or automatic accounting adjustments.
Those require provider-specific integrations and operational policy beyond the
reference protocol.
