# Batch 2 — Financial Execution Core

## Stage 13 — Complete Payment Lifecycle

The reference lifecycle remains explicitly split:

PaymentRequest -> Payment -> Transaction.

Budget reservation is created before provider execution. Provider calls occur
outside the database transaction. A successful outcome consumes the reservation
and posts a balanced journal. Failed outcomes release the reservation.
Ambiguous outcomes remain UNKNOWN_EXTERNAL_OUTCOME.

Capture, void, and refund are separate provider operations with independent
idempotency keys and transaction records.

## Stage 15 — Ledger

The authoritative financial record is the double-entry journal/posting model.
post_journal rejects empty, unbalanced, mixed-currency, and non-positive
postings and is idempotent by journal key.

## Stage 16 — Outbox / Worker

The transactional outbox is committed with the business transaction. The
outbox worker claims rows with SKIP LOCKED, commits the claim, processes events
after the claim transaction, and marks them published or retryable.

Payment provider execution is also separated from the API transaction.

## Stage 17 — Audit / Notification

Audit is an append-only evidence stream. Notifications are durable work items
and are deduplicated by source event. Notification delivery never determines
financial success.

## Stage 18 — Security Boundaries

Agents receive payment decisions and next actions, not PAN, CVV, private keys,
provider secrets, or other primary financial credentials. Provider events are
deduplicated before processing. Authorization evidence is referenced rather
than treated as a financial secret.

## V1 Boundary

Kafka, distributed microservices, live bank/PSP integrations, production card
issuance, and a universal ATF cryptographic token format remain outside V1.
