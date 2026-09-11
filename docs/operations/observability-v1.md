# Agent-Pay V1 Observability

## Goals

Every financial operation must be reconstructable by correlation ID, payment ID, provider operation ID, transaction ID, and ledger journal ID without exposing payment credentials or secrets.

## Required metrics

- payment requests by outcome: `requested`, `denied`, `approval_required`, `processing`, `succeeded`, `failed`, `unknown_external_outcome`
- provider operations by outcome and provider
- provider webhook events by type, signature result, duplicate, and processing result
- settlement records by `MATCHED` / `DISCREPANCY`
- budget reservation failures and releases
- ledger posting failures
- outbox enqueue, retry, and dead-letter counts
- payment processing latency

## Required structured fields

`correlation_id`, `payment_id`, `payment_request_id`, `agent_id`, `account_id`, `provider_operation_id`, `provider_reference`, `transaction_id`, `ledger_journal_id`, `event_id`, and `idempotency_key` (hashed or otherwise non-sensitive when exported).

## Security rules

Never log CVV, OTP, PAN, private keys, bearer tokens, webhook secrets, provider credentials, or raw authorization headers. Provider payloads must be redacted before operational logging.

## Alerts

At minimum alert on:

1. sustained `UNKNOWN_EXTERNAL_OUTCOME`
2. reconciliation discrepancies
3. duplicate/idempotency conflicts above baseline
4. repeated webhook signature failures
5. outbox retry exhaustion
6. ledger posting failures
7. budget reservation invariant violations
8. payment state transition failures

The reference implementation exposes dependency-free metric primitives in `reference/implementation/src/agent_pay/observability.py`; production deployments may bind them to Prometheus/OpenTelemetry without changing the financial domain model.
