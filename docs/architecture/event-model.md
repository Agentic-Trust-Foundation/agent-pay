# Agent-Pay Event Model

## Purpose

Agent-Pay uses durable events to connect payment state changes, notifications, audit, webhooks, reconciliation, and future asynchronous components without requiring synchronous coupling between every module.

## Event Principles

1. Events describe facts that happened; commands request actions.
2. Events are immutable.
3. Events have stable identifiers.
4. Consumers must tolerate duplicate delivery.
5. Consumers must tolerate delayed and out-of-order external events.
6. Financial state changes remain authoritative in PostgreSQL and the ledger.
7. Publishing an event must not be lost when the corresponding database transaction commits.

## V1 Outbox

V1 uses a transactional outbox inside the modular monolith.

```text
Application Transaction
      |
      +--> Domain state change
      |
      +--> Ledger/state record
      |
      +--> Outbox event
      |
      +--> COMMIT
             |
             v
        Outbox Worker
             |
             v
      Internal Consumers
```

The outbox row is committed atomically with the state change. A worker publishes or processes it after commit.

## Event Envelope

A common event envelope should contain:

```json
{
  "event_id": "evt_123",
  "event_type": "PaymentSucceeded",
  "event_version": 1,
  "occurred_at": "2026-09-11T12:00:00Z",
  "producer": "agent-pay-core",
  "aggregate_type": "payment",
  "aggregate_id": "pay_123",
  "correlation_id": "cor_123",
  "causation_id": "cmd_123",
  "idempotency_key": "idem_123",
  "payload": {}
}
```

Sensitive credentials and raw payment secrets must never be placed in event payloads.

## Core V1 Events

```text
PaymentRequested
PolicyEvaluated
BudgetReservationCreated
BudgetReservationReleased
BudgetConsumed
ApprovalRequested
PaymentApproved
PaymentDenied
PaymentStarted
PaymentAuthenticationRequired
PaymentAuthenticationCompleted
PaymentSucceeded
PaymentFailed
PaymentCancelled
PaymentRefundRequested
PaymentRefunded
WalletCredited
WalletDebited
LedgerEntryCreated
NotificationRequested
AuditEventRecorded
```

Additional events may be introduced without changing the meaning of existing events.

## Provider Events

External provider webhooks are first-class input events.

```text
ProviderWebhookReceived
ProviderPaymentAuthorized
ProviderPaymentCaptured
ProviderPaymentFailed
ProviderPaymentRefunded
ProviderPaymentDisputed
ProviderSettlementReported
```

The provider event should be persisted before domain processing so replay and forensic investigation are possible.

## Event Ordering

Internal events for a single aggregate should carry enough information for consumers to detect stale or duplicate transitions.

External provider events must not be assumed to arrive in order.

Example:

```text
captured webhook
    arrives before
authorized webhook
```

The consumer must validate whether the state transition is legal and either apply, defer, or quarantine the event.

## Deduplication

Consumers must maintain an idempotency/deduplication record keyed by a stable provider event identifier when available.

If the provider has no reliable event ID, a carefully defined fingerprint may be used, but it must not be based solely on mutable payload fields without safeguards.

## Retry

Failed event processing should use bounded retry with backoff.

Poison events must eventually move to a review/dead-letter mechanism rather than retry forever.

A retry must not duplicate:

- ledger postings
- budget consumption
- payment execution
- notifications with financial meaning

## Audit vs Event

Events and audit records are related but different:

```text
Event = durable fact for system processing
Audit = durable evidence for investigation/accountability
```

A critical financial event may produce both.

## Notification

Notification should consume internal events rather than being embedded directly in every financial transaction path.

```text
PaymentSucceeded
      ↓
NotificationRequested
      ↓
Push / Email / SMS / Webhook / App
```

Notification delivery is not part of the payment transaction and must never block ledger correctness.

## Reconciliation

Reconciliation jobs may consume provider settlement/events and compare them with internal payments and transactions.

Mismatches produce explicit reconciliation records and review events rather than silently mutating financial history.

## V1 Non-Goals

V1 does not require Kafka, NATS, or another distributed event platform.

The modular monolith should use PostgreSQL outbox processing first. A future broker can consume the same event contract when scale or deployment topology requires it.
