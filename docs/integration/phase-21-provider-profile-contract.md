# Phase 21 — Production & Provider Profiles

**Status:** implementation/operations track  
**Boundary:** provider-neutral; no live-provider claim.

## Provider contract

A provider adapter MUST expose normalized operations for:
- create/initiate payment;
- query/reconcile operation;
- verify callback/event;
- settle/finalize when the provider supports a separate settlement state;
- refund/reversal where supported.

Provider-specific request/response fields remain inside the profile adapter.

## Secrets

Secrets are deployment inputs, never protocol data:
- load from an external secret mechanism;
- never commit credentials;
- separate sandbox and production credentials;
- support rotation without changing payment semantics;
- redact secrets from logs and audit records;
- fail closed when required credentials are absent.

## Webhooks/events

A provider profile MUST define:
- authenticity verification;
- event-to-provider-operation binding;
- timestamp/replay policy;
- idempotent event identity;
- duplicate handling;
- malformed/unknown event behavior;
- ordering assumptions, if any.

A callback must not mutate financial state before required verification and binding succeed.

## Timeout/retry/unknown outcome

Timeout does not mean failure. The normalized state is `UNKNOWN_EXTERNAL_OUTCOME` until the provider operation can be reconciled.

Retries MUST:
- preserve the original idempotency identity where safe;
- never silently change the payment intent;
- distinguish transport retry from provider operation creation;
- reconcile unknown outcomes before creating a new non-idempotent operation.

## Reconciliation

Reconciliation compares internal financial state with provider assertions and records:
- provider operation ID;
- provider event IDs;
- observed provider state;
- internal state;
- discrepancy classification;
- reconciliation timestamp;
- resolution/evidence reference.

Settlement is a separate assertion from payment initiation.

## Observability

Minimum structured signals:
- request/payment/operation IDs;
- provider profile/version;
- outcome state;
- retry count;
- latency;
- callback/event ID;
- reconciliation result;
- redacted failure category.

No secret, primary credential, OTP, CVV or private key belongs in logs.

## Deployment gates

Before target activation:
1. configuration validated;
2. secrets present and rotation path tested;
3. callback endpoint bound and protected;
4. retry/idempotency behavior tested;
5. unknown-outcome reconciliation tested;
6. backup/restore procedure verified;
7. observability and alerting verified;
8. incident/runbook ownership documented.

**Evidence levels:** documented → implemented → CI-tested → target-validated → production/live-verified. Never infer a higher level from a lower one.
