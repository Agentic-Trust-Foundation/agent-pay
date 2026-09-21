# Phase 15 — Durable payment lifecycle and idempotency hardening

**Status:** Implemented on the reference-implementation branch.
**V1 contract:** unchanged and remains frozen.

## Findings

### 1. Provider-operation idempotency was too permissive

The PostgreSQL uniqueness boundary prevents duplicate provider-operation idempotency keys, but the previous repository behavior treated every conflict as the same operation. A key reused for another payment or operation type could therefore be rebound to the current payment.

**Fix:** an existing key is accepted only when both `payment_id` and `operation_type` match the original operation. Conflicts fail closed.

### 2. Terminal lifecycle replays did not validate intent

Capture and void returned the terminal result before checking the replayed amount/currency.

**Fix:** terminal replays validate the same payment amount and currency before returning the existing terminal outcome.

### 3. Partial refund replay could report the wrong terminal state

A previously posted partial refund was returned as `REFUNDED` even when refundable captured value remained.

**Fix:** replay now returns `SUCCEEDED` while refundable value remains and `REFUNDED` only when the captured amount has been fully refunded.

## Regression coverage

- Provider-operation replay with the same payment and operation type.
- Provider-operation key conflict across operation types.
- Provider-operation key conflict across payments.
- Exact amount/currency validation on terminal capture/void replay.
- Partial versus full refund replay status.

## Residual boundaries

This phase does not claim live PSP behavior, provider-specific retry guarantees, issuer/card-network semantics, or production deployment controls. Those remain provider/deployment profiles.

## Verification

The branch must pass the repository Validation, Conformance, and Docker clean-start workflows before merge.
