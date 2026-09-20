# Provider Webhooks and Events V1

## Ingress pipeline

```
Provider callback
  -> TLS / edge controls
  -> parse + schema validation
  -> signature/authentication when provider supports it
  -> lookup by provider reference
  -> verify against provider
  -> deduplicate
  -> append immutable event
  -> transaction state transition
  -> outbox
```

## Rules
- Never trust callback status without provider verification where the provider supports verification.
- Duplicate callbacks are normal and must be idempotent.
- Unknown payment references do not create a payment.
- Amount/currency mismatches fail closed and create reconciliation work.
- Terminal states are immutable except for explicitly modeled reconciliation corrections.
- Raw provider payloads are retained with secrets and sensitive fields redacted from ordinary logs.

## Key rotation
Provider signature keys, when applicable, are versioned and rotated without changing payment semantics.
