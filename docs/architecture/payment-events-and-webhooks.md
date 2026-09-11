# Payment Events and Webhooks

## Purpose

Payment execution is asynchronous by default at the architecture level. A provider may acknowledge a request before the final payment outcome is known, and final state may arrive through a webhook or other event channel.

## Core principle

> A provider response is an observation; the Agent-Pay state machine is the system of record for payment state.

Provider callbacks must be authenticated, validated, deduplicated, correlated, and applied through explicit state transitions.

## Flow

```text
Payment Intent
     |
     v
Agent-Pay
     |
     v
Provider / Rail
     |
     +---- synchronous response
     |
     +---- webhook / event
              |
              v
       Webhook Ingestion
              |
              +--> authenticate
              +--> validate signature
              +--> deduplicate
              +--> correlate
              +--> state transition
              +--> audit
              +--> outbox/event publication
```

## Webhook requirements

A provider webhook handler must:

1. authenticate the source
2. verify signature or equivalent integrity proof
3. enforce timestamp / replay protections where supported
4. identify the provider event uniquely
5. persist the event receipt before irreversible processing where needed
6. apply the event idempotently
7. validate that the event is compatible with the current payment state
8. record the provider reference
9. emit an internal domain event after the state transition

## Duplicate delivery

Webhook delivery is at-least-once unless a specific provider guarantees otherwise. Duplicate events must not create duplicate payments, ledger entries, refunds, or notifications.

Use a unique provider-event identifier and an internal processing record.

## Out-of-order events

Events may arrive out of order. The state machine must reject impossible transitions and safely handle known reorderings.

For example:

```text
PROCESSING -> SUCCEEDED
```

is valid, while a late `PROCESSING` event after `SUCCEEDED` must not move the payment backwards.

## Timeout ambiguity

A provider timeout does not mean payment failure.

```text
Agent-Pay -> Provider
              |
              X timeout

Payment = UNKNOWN / PROCESSING
```

Agent-Pay must support a recovery path through provider status lookup, reconciliation, or a later event.

## Provider event record

A future implementation should persist at least:

- provider
- provider_event_id
- event_type
- received_at
- signature verification result
- raw reference or securely stored payload reference
- correlation/payment reference
- processing status
- processed_at
- failure reason

Sensitive provider payloads must not be retained unnecessarily.

## Internal events

Important domain events include:

- PaymentRequested
- PaymentAuthorized
- PaymentAuthenticationRequired
- PaymentProcessing
- PaymentSucceeded
- PaymentFailed
- PaymentCancelled
- RefundRequested
- RefundSucceeded
- RefundFailed
- ProviderEventReceived
- SettlementObserved
- ReconciliationMismatch

## V1 boundary

V1 may use an internal transactional outbox and a simple worker rather than Kafka/NATS/RabbitMQ. The abstraction must remain compatible with later external event infrastructure.
