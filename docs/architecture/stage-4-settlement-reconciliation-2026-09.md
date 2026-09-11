# Stage 4 — Settlement and Reconciliation Workflow (2026-09)

## Purpose

This stage turns settlement/reconciliation from a comparison primitive into a durable PostgreSQL workflow.

The V1 boundary is intentionally conservative:

> A provider settlement report is an external assertion to reconcile against recorded provider operations. It is not, by itself, permission to mutate financial truth.

## Flow

```text
Provider Settlement Report
          |
          v
  Settlement Ingestion
          |
          v
  Idempotent Persistence
          |
          v
 Provider Operation Match
          |
          v
 Amount / Currency / Status Check
          |
     +----+----+
     |         |
     v         v
  MATCHED   DISCREPANCY
     |         |
     v         v
RECONCILED  Investigation
```

## V1 workflow

`SettlementRepository.ingest()` performs one database transaction that:

1. deduplicates `(provider_name, settlement_reference)`;
2. persists the settlement report;
3. matches the provider reference to the latest provider operation;
4. validates provider operation status;
5. compares expected and observed amount/currency;
6. persists a `reconciliation_records` conclusion;
7. marks the settlement `RECONCILED` or `DISCREPANCY`.

## Discrepancy classes

- `UNKNOWN_PROVIDER_REFERENCE`
- `STATUS_MISMATCH`
- `AMOUNT_MISMATCH`
- `CURRENCY_MISMATCH`
- `PROVIDER_REFERENCE_MISMATCH`

A discrepancy does **not** automatically reverse, refund, debit, credit, or rewrite the ledger.

## Idempotency

Settlement reports are uniquely identified by `(provider_name, settlement_reference)`.

Reprocessing the same report returns `DUPLICATE` and creates no second settlement or reconciliation record.

A reconciliation record is also unique per settlement and per provider operation in V1.

## Financial boundary

```text
Provider execution
      |
      +--> Payment / Transaction / Ledger truth
      |
      +--> Settlement report
               |
               v
        Reconciliation
               |
        +------+------+
        |             |
      MATCHED     DISCREPANCY
        |             |
      status       investigation
```

Settlement reconciliation is therefore an observability/control process around financial truth, not a second ledger.

## Tests

The reference implementation covers:

- matched settlement;
- amount mismatch;
- duplicate settlement report;
- unknown provider reference;
- preservation of payment status when reconciliation detects a mismatch.

The CI workflow applies migration `007_settlement_reconciliation_integrity.sql` before the PostgreSQL integration tests.

## Deliberate V1 limitations

V1 treats one settlement report as an operation-level report. A future provider-specific adapter may support batch settlement files, settlement windows, fees, net/gross amounts, multi-operation reports, partial settlement, and provider-specific status semantics.

Investigation and discrepancy resolution remain explicit workflows and are not silently automated by reconciliation.
