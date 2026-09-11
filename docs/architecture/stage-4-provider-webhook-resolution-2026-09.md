# Stage 4 — Signed Provider Webhook Resolution

This layer closes the ambiguous external-outcome loop.

```text
Provider
   |
   | signed event
   v
Webhook Ingestion
   |
   +--> verify signature
   |
   +--> durable provider_events dedupe
   |
   v
Provider Operation Resolver
   |
   +--> SUCCESS -> finalize payment + consume reservation + ledger
   +--> FAILURE -> fail payment + release reservation
   |
   v
Financial Truth
```

## Rules

1. An external provider event is untrusted until its signature is verified.
2. The event is durably recorded before financial processing.
3. `(provider_name, provider_event_id)` is the deduplication identity.
4. A duplicate event must not create another financial effect.
5. A verified success for an unknown charge resolves `UNKNOWN_EXTERNAL_OUTCOME` using the original provider operation identity.
6. A verified failure releases the original budget reservation exactly once.
7. The provider idempotency key remains stable across retries.
8. Ledger posting is independently idempotent.
9. Provider events never become the financial ledger of record.
10. Out-of-order and unsupported events must not silently rewrite a terminal financial state.

The reference resolver is deliberately provider-neutral. Provider-specific signature formats and event schemas belong at the adapter boundary; the financial resolver consumes a normalized, verified outcome.

## Remaining production work

The current reference layer demonstrates durable resolution and signature rejection, but production deployments still need provider-specific signed webhook adapters, replay-window protection, key rotation, provider reference binding, event-order rules, persistent error/retry handling, and end-to-end integration tests against a realistic provider simulator.
