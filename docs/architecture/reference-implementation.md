# Agent-Pay V1 Reference Implementation

## Goal

V1 should prove the financial-control model end to end without prematurely splitting the system into microservices.

## Architecture

```text
                 AGENT
                   |
                   | HTTPS / API
                   v
              API Layer
                   |
                   v
        +-----------------------+
        |   Agent-Pay Core      |
        |    Modular Monolith   |
        |-----------------------|
        | Agent / Delegation    |
        | Authorization Context |
        | Policy Engine         |
        | Budget Engine         |
        | Approval Engine       |
        | Payment Orchestrator  |
        | Payment Router        |
        | Transaction           |
        | Wallet / Ledger       |
        | Audit                 |
        | Notification          |
        | Reconciliation       |
        +-----------+-----------+
                    |
             +------+------+
             |             |
             v             v
        PostgreSQL       Redis
             |
             v
          Outbox
             |
             v
        Async Worker
             |
             v
      Provider / Rail Adapter
```

## Module Boundaries

### Identity / Delegation Adapter

Consumes trusted identity and delegation evidence. It does not become a general identity provider.

### Policy

Pure/deterministic evaluation where possible. Produces a decision and trace without financial side effects.

### Budget

Owns budget capacity, reservations, consumption, and release. Uses transactional concurrency controls.

### Approval

Owns approval lifecycle and binding to the payment request.

### Payment Orchestrator

Coordinates the lifecycle without putting provider-specific logic into the API layer.

### Payment Router

Selects a payment instrument adapter according to policy, request constraints, availability, and routing rules.

### Wallet / Ledger

Owns financial state and immutable accounting records. Ledger remains the financial source of truth.

### Event / Outbox

Reliably publishes domain events after successful database transactions.

### Reconciliation

Resolves ambiguous provider outcomes and compares internal state with provider reports.

## Request Flow

```text
POST /v1/payments
       |
       v
Create Payment Request
       |
       v
Validate + Idempotency
       |
       v
Verify Authorization Evidence
       |
       v
Policy Evaluation
       |
       v
Budget Reservation
       |
       v
Approval Decision
       |
       +---- approval required ----> wait
       |
       v
Payment Router
       |
       v
Instrument Adapter
       |
       v
Provider / Rail
       |
       v
Async Result / Webhook
       |
       v
Transaction + Ledger
       |
       +--> Outbox --> Notification / Audit / Reconciliation
```

## Transactional Rules

The following operations must be atomic within PostgreSQL transactions where applicable:

- budget reservation
- budget release
- budget consumption
- wallet ledger posting
- approval state transition
- payment state transition
- outbox insertion

External provider calls are never assumed to be part of the database transaction.

## Recovery

If a provider call times out:

```text
PROCESSING
   ↓
unknown external outcome
   ↓
provider query / webhook / reconciliation
   ↓
final internal state
```

The system must not retry an ambiguous payment as a new payment unless the provider operation is known to be safely idempotent.

## Adapter Contract

A payment instrument adapter should conceptually support:

```text
authorize(payment_context)
capture(operation)
void(operation)
refund(operation, amount)
get_status(operation)
```

Authentication/challenge results should be represented explicitly rather than hidden inside an adapter-specific error.

## V1 Adapter

The first concrete adapter may be an internal Wallet Adapter. The interface must remain generic enough for:

- Virtual Card
- Bank/PSP
- Payment Gateway
- future payment instruments

No Agent-facing API should expose the underlying instrument implementation.

## Data Stores

### PostgreSQL

Authoritative store for:

- accounts
- agents
- delegations
- policies
- budgets
- reservations
- payment requests
- approvals
- payments
- transactions
- ledger
- provider events
- reconciliation records
- audit events
- outbox

### Redis

Optional V1 support for:

- short-lived locks where justified
- rate limiting
- ephemeral workflow state
- caching

Redis must not become the financial source of truth.

## Security

The reference implementation must enforce:

- scoped authentication
- authorization on every financial operation
- short-lived credentials where appropriate
- secret isolation
- tokenized/opaque payment instrument references
- no PAN/CVV or primary bank credentials in Agent requests
- replay protection
- idempotency
- audit logging
- fail-closed behavior
- secure webhook verification

## Observability

Every payment flow should carry a correlation ID across:

```text
API
 → Payment Request
 → Policy
 → Budget
 → Approval
 → Provider Operation
 → Webhook
 → Transaction
 → Ledger
 → Audit
```

Metrics should distinguish:

- policy denials
- budget denials
- approval latency
- payment success/failure
- authentication challenges
- provider timeouts
- ambiguous outcomes
- reconciliation mismatches
- webhook failures

## Testing Strategy

V1 should include:

### Unit tests

- policy precedence
- policy determinism
- budget arithmetic
- reservation lifecycle
- approval transitions
- payment state transitions

### Integration tests

- concurrent budget reservations
- wallet/ledger atomicity
- idempotent payment requests
- duplicate webhook delivery
- out-of-order webhook handling
- provider timeout recovery
- approval expiry
- refund/reversal handling

### Contract tests

- OpenAPI validation
- provider adapter contract
- event envelope contract

### Security tests

- broken object-level authorization
- replay attacks
- privilege escalation
- webhook forgery
- secret leakage
- idempotency-key abuse

## V1 Delivery Sequence

```text
1. Domain model
2. PostgreSQL schema
3. Policy evaluator
4. Budget + reservation
5. Approval state machine
6. Payment state machine
7. Wallet/ledger service
8. Wallet payment adapter
9. Outbox + worker
10. Webhook/provider-event ingestion
11. Reconciliation
12. API integration
13. Security hardening
14. End-to-end test suite
```

The implementation should remain a modular monolith until operational evidence demonstrates a real need for service extraction.
