# Idempotency and Concurrency

## Purpose

Financial operations must remain correct under retries, duplicate requests, concurrent agents, provider retries, and delayed events.

## Idempotency layers

Agent-Pay uses multiple idempotency boundaries:

```text
API Request
   |
   v
Payment Intent Idempotency
   |
   v
Payment Execution Idempotency
   |
   v
Provider Idempotency
   |
   v
Ledger Posting Idempotency
   |
   v
Webhook Event Idempotency
```

These keys are related but are not assumed to be identical.

## Requirements

A retry of the same logical operation must not:

- create a second payment
- debit a wallet twice
- reserve a budget twice
- capture a provider payment twice
- create duplicate ledger entries
- process the same provider event twice
- send duplicate irreversible notifications

## Concurrency

Financial constraints must be checked and reserved atomically.

Example:

```text
Budget remaining = 100

Agent A requests 80
Agent B requests 80
```

A naive read/check/write sequence can incorrectly approve both requests.

The implementation must serialize or atomically coordinate the relevant budget reservation and ledger/hold operations.

## Transaction boundaries

At minimum, the database transaction should protect each critical state transition and its corresponding financial reservation/posting.

External provider calls must not be assumed to participate in the PostgreSQL transaction. Ambiguous external outcomes are resolved through provider status lookup, webhook events, or reconciliation.

## Recovery

```text
DB commit succeeded + provider call uncertain
                 |
                 v
              UNKNOWN
                 |
       status lookup / webhook
                 |
        +--------+--------+
        v                 v
     SUCCEEDED          FAILED
```

## V1 boundary

PostgreSQL row-level locking, unique constraints, transactional state transitions, and an outbox are sufficient for the first implementation. Distributed locks or a distributed transaction coordinator are not required.
