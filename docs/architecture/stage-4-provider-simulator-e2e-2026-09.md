# Stage 4 — Provider Simulator and End-to-End Failure Recovery

## Purpose

The reference implementation now contains a deterministic provider simulator for validating the most important asynchronous payment failure boundary without depending on a real PSP.

## Canonical scenario

```text
Payment Request
      |
      v
Provider Charge
      |
      +---- provider succeeds, caller sees TIMEOUT
      |
      v
UNKNOWN_EXTERNAL_OUTCOME
      |
      v
Signed Provider Webhook
      |
      v
Webhook Verification / Deduplication
      |
      v
Payment Resolution
      |
      v
Ledger Posting
      |
      v
Provider Settlement Report
      |
      v
Reconciliation
      |
      +---- MATCHED
      |
      +---- DISCREPANCY -> investigation; no automatic ledger mutation
```

## Simulator guarantees

- Stable operation identity per payment.
- A timeout can hide a successful provider outcome from the caller.
- A later webhook exposes the provider reference and final outcome.
- Webhook signatures use the same HMAC verification primitive as the provider-event path.
- A successful provider operation can produce a settlement report.
- Settlement amount/currency are reconciled against the expected payment.
- Failed provider operations cannot produce a settlement report.
- Repeated charge requests are provider-idempotent.

## What this test does not claim

The simulator is deterministic test infrastructure, not a production PSP adapter. Production adapters still require provider-specific authentication, signature schemes, replay protection, key rotation, webhook ordering rules, retry/dead-letter handling, provider-reference binding, and operational reconciliation controls.

The PostgreSQL webhook resolver and settlement repository remain the durable implementation path. The simulator is intentionally small so the conformance suite can exercise ambiguous external outcomes without external network dependencies.
