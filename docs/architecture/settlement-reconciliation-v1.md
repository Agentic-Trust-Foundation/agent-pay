# Settlement and Reconciliation V1

## Three ledgers of truth
1. Agent-Pay internal transaction/journal state.
2. Provider transaction state.
3. Settlement/bank statement state.

Reconciliation compares them rather than assuming any one source is always correct.

## States
- MATCHED
- MISSING_PROVIDER
- MISSING_INTERNAL
- AMOUNT_MISMATCH
- CURRENCY_MISMATCH
- DUPLICATE_PROVIDER
- UNSETTLED
- UNKNOWN

## Process
- import provider settlement records
- normalize identifiers and timestamps
- match by stable provider references and local IDs
- compare amount/currency/status
- create reconciliation cases
- never silently mutate historical financial evidence
- resolve through explicit correction/compensation workflows

## Recovery
A worker restart, timeout, or duplicate event must not create a second financial effect. Re-running reconciliation must be safe.
