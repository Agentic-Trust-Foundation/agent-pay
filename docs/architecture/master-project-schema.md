# Agent-Pay Master Project Schema

**Status:** Architecture baseline for V1 convergence

**Date:** 2026-09-11

**Purpose:** This document is the canonical architecture model used to align the Agent-Pay domain model, API, PostgreSQL schema, state machine, event model, security model, reference implementation, and conformance suite.

> **Core principle:** The Agent should receive spending authority, not financial credentials.

> **System rule:** Agent requests; Agent-Pay decides; Payment Rail executes; Ledger records financial truth.

---

## 1. Product Definition

Agent-Pay is a financial control and payment layer for AI agents. It enables an agent to transact on behalf of an account within delegated authority, spending policies, budgets, approval rules, and payment-instrument controls without exposing primary financial credentials to the agent.

Agent-Pay is **protocol-first, implementation-backed, and service-optional**. V1 uses a modular-monolith reference implementation; protocol compatibility does not require a particular deployment topology.

Agent-Pay is not:

- a general agent identity or trust protocol;
- a general commerce protocol;
- a merchant catalog or fulfillment system;
- a replacement for payment rails or banking infrastructure;
- a wallet-only product.

---

## 2. Architectural Boundary

```text
                    Agentic Trust Foundation
              Identity / Delegation / Trust Evidence
                              |
                              v
Agent -> Payment Intent -> Agent-Pay Financial Control
                              |
            +-----------------+------------------+
            |                 |                  |
         Policy             Budget            Approval
            |                 |                  |
            +-----------------+------------------+
                              |
                       Payment Decision
                              |
                       Payment Router
                              |
              +---------------+---------------+
              |               |               |
            Wallet       Virtual Card      Future Rail
                              |
                              v
                       Payment Provider/Rail
                              |
                              v
                    Transaction / Settlement
                              |
                              v
                       Financial Ledger
```

### Boundary ownership

| Concern | Owner |
|---|---|
| Agent identity | ATF / external identity provider |
| General delegation/trust | ATF |
| Financial authorization | Agent-Pay |
| Spending policy | Agent-Pay |
| Budget and reservation | Agent-Pay |
| Human payment approval | Agent-Pay |
| Payment instrument abstraction | Agent-Pay |
| Provider credentials | Protected provider adapter / vault boundary |
| Payment execution | External rail/provider through Agent-Pay adapter |
| Financial ledger | Agent-Pay |
| Product/order/fulfillment state | Commerce system |
| Merchant trust/reputation | ATF or merchant ecosystem |

---

## 3. Actors

### User / Account Owner
The principal whose account, money, policies, and delegated authority are being used. Agent-Pay may reference an external identity rather than owning the complete user identity system.

### Agent
An AI execution actor. The agent can request financial actions but does not own funds and must not receive primary payment credentials.

### Agent-Pay
The authoritative financial-control decision point.

### Payment Provider / Rail
External system that authorizes, captures, settles, refunds, or otherwise executes a payment.

### Merchant
The payment counterparty. Merchant trust is not a core Agent-Pay responsibility.

### Administrator / Operator
Operational actor subject to separate privileged authorization and audit controls.

---

## 4. Canonical Domain Model

```text
Account
├── Agents
├── Delegations
├── Wallets
├── Funding Sources
├── Payment Instruments
├── Policies
└── Budgets

Agent
└── Delegation
    └── Authorization Evidence

Payment Request
├── Authorization Context
├── Commerce Context
├── Policy Evaluation
├── Budget Reservation
├── Approval(s)
└── Payment
    ├── Payment Authentication
    ├── Provider Operations
    ├── Transaction(s)
    └── Settlement / Reconciliation

Wallet
└── Ledger Account
    └── Journal / Ledger Entries

Payment
└── Transaction
    ├── Refund
    ├── Reversal / Void
    └── Dispute / Chargeback (future)
```

### Canonical entities

- `Account`
- `Agent`
- `Delegation`
- `AuthorizationEvidence`
- `Wallet`
- `LedgerAccount`
- `LedgerJournal` / `LedgerEntry`
- `FundingSource`
- `PaymentInstrument`
- `Merchant`
- `Policy`
- `PolicyVersion`
- `Budget`
- `BudgetReservation`
- `PaymentRequest`
- `Approval`
- `Payment`
- `PaymentAuthentication`
- `ProviderOperation`
- `Transaction`
- `Settlement`
- `ReconciliationRecord`
- `ProviderEvent`
- `AuditEvent`
- `OutboxEvent`
- `Notification`

---

## 5. Identity and Authorization

Agent-Pay does not recreate a general-purpose identity network.

Every executable payment must be explainable through:

```text
Caller Authentication
       -> Agent Identity
       -> Account Relationship
       -> Delegation
       -> Authorization Evidence
       -> Policy
       -> Budget
       -> Approval (if required)
       -> Payment
```

`identity_reference`, `owner_reference`, and external authorization evidence may point to ATF or another trusted identity system.

Authorization evidence must be bound to the requested financial operation and must include enough provenance to support later audit. It must not be treated as a permanent bearer permission.

---

## 6. Policy Model

Policy answers: **under what conditions may this financial action occur?**

Policy may constrain:

- per-transaction amount;
- daily/monthly/period limits;
- merchant/domain;
- merchant category;
- currency;
- location;
- time window;
- frequency;
- payment instrument;
- purpose/category;
- approval threshold;
- allowed/denied conditions.

Policies are versioned. A payment stores the effective policy version/evaluation reference used for the decision so a later policy change cannot rewrite historical authorization.

Policy evaluation returns a structured decision, not only boolean allow/deny:

```text
ALLOW_AUTO
ALLOW_NOTIFY
REQUIRE_APPROVAL
DENY
```

---

## 7. Budget Model

Policy and Budget are different controls.

```text
Policy: Electronics allowed
Budget: USD 1,000/month
Consumed: USD 750
Reserved: USD 100
Available: USD 150
```

Budget state must distinguish:

- limit;
- consumed amount;
- reserved amount;
- available amount;
- period;
- status.

### Budget reservation

A reservation is not the same as a wallet hold.

```text
Budget available
      |
      v
Reservation
  /       \
release   consume
```

Concurrent payment requests must not be able to reserve the same remaining budget twice.

A reservation is linked to the Payment Request and has its own lifecycle and idempotency semantics.

---

## 8. Approval Model

Approval is a decision on an exact payment intent.

```text
PENDING -> APPROVED
        -> DENIED
        -> EXPIRED
        -> CANCELLED
```

An approval must bind to at least:

- payment request;
- amount;
- currency;
- merchant;
- relevant commerce context;
- account/principal;
- expiry;
- approving principal;
- authorization/approval version or digest.

Approval records must support history. A single Payment Request must not be limited to one immutable approval row if re-approval or replacement is required.

A material change to the payment intent invalidates prior approval.

---

## 9. Payment Intent

`PaymentRequest` is the agent's financial intent. It is not a financial transaction.

Canonical request fields include:

```text
id
account_id
agent_id
merchant
amount
currency
purpose
items / commerce references
idempotency key
authorization context
correlation id
created_at
```

The API should remain intent-oriented. The agent does not select raw provider credentials.

Commerce context may include order ID, cart ID, checkout session, merchant order reference, and commerce protocol reference, but Agent-Pay does not become the order/fulfillment system of record.

---

## 10. Payment Lifecycle

Canonical V1 lifecycle:

```text
REQUESTED
  -> VALIDATING
  -> AUTHENTICATION_REQUIRED / AUTHENTICATED   (when payment authentication is needed)
  -> POLICY_CHECK
  -> BUDGET_CHECK
  -> APPROVAL_REQUIRED -> APPROVED
  -> PAYMENT_PENDING
  -> PROCESSING
       |-> SUCCEEDED
       |-> FAILED
       |-> UNKNOWN_EXTERNAL_OUTCOME
```

Cancellation is permitted only from explicitly cancellable states.

Post-execution financial operations are separate from the primary payment lifecycle:

```text
SUCCEEDED
  -> REFUND_REQUESTED -> REFUND_PROCESSING -> REFUNDED / REFUND_FAILED

AUTHORIZED
  -> VOID_REQUESTED -> VOIDED / VOID_FAILED

SETTLEMENT_PENDING -> SETTLED / SETTLEMENT_FAILED

DISPUTED -> CHARGEBACK / RESOLVED     (future capability)
```

An external timeout must never be interpreted automatically as payment failure. The state `UNKNOWN_EXTERNAL_OUTCOME` exists for ambiguous provider outcomes until reconciliation/webhook/query resolves the result.

---

## 11. Payment Authentication

Payment authentication is distinct from:

- Agent authentication;
- Agent authorization;
- spending policy;
- human approval.

Examples include 3-D Secure, issuer challenge, or provider step-up authentication.

Authentication is bound to the exact payment operation and must never expose OTPs, CVVs, primary card data, bank credentials, or equivalent secrets to the agent.

---

## 12. Payment Instrument Abstraction

Agent-Pay exposes an abstract payment instrument interface:

```text
authorize()
capture()
void()
refund()
```

Potential implementations:

- Wallet;
- Virtual Card;
- Bank Account / bank rail;
- Payment Gateway;
- future payment instrument.

Provider credentials remain behind a protected adapter/tokenization boundary.

The Agent API should express financial intent, not instrument credentials.

---

## 13. Transaction Model

Payment and Transaction are separate.

```text
Payment Request
    |
  Payment
    |
 Transaction(s)
    |
 Ledger / Settlement
```

Transaction types must distinguish economic operations such as:

- payment/debit;
- funding/credit;
- hold/reservation effect where applicable;
- release;
- refund;
- reversal/void;
- adjustment.

Refund is not the same as reversal/void, and neither is the same as dispute/chargeback.

---

## 14. Ledger and Accounting

The ledger is the financial source of truth.

V1 must be **double-entry-ready** and should converge toward explicit journal/posting semantics before production financial execution.

Conceptually:

```text
Journal
├── Posting A: DEBIT  account X  100
└── Posting B: CREDIT account Y 100
```

Every journal must balance by currency.

Historical financial records are append-oriented. Corrections use compensating entries; historical postings are not overwritten.

Wallet cached balance and available balance are derived/operational state, not the ultimate accounting authority.

---

## 15. Settlement and Reconciliation

Payment execution and settlement are separate lifecycle concerns.

```text
Payment Execution
      |
      v
External Provider
      |
      v
Settlement Event / Report
      |
      v
Reconciliation
      |
      v
Ledger Truth
```

Agent-Pay must retain provider references and enough information to reconcile internal payment/transaction state with external outcomes.

Reconciliation must detect:

- missing provider events;
- duplicate provider events;
- amount mismatch;
- currency mismatch;
- status mismatch;
- unknown provider references;
- late settlement;
- refund mismatch.

---

## 16. Provider Events and Outbox

Provider webhooks/events are untrusted external input until verified.

Processing requirements:

1. verify authenticity/signature where supported;
2. persist raw-safe event metadata and deduplication identity;
3. make processing idempotent;
4. protect against replay;
5. tolerate out-of-order delivery;
6. reconcile ambiguous outcomes;
7. emit internal domain events only after authoritative state transitions.

Internal event publication uses a PostgreSQL transactional outbox in V1.

The outbox transaction must commit with the corresponding financial state change so an event cannot be silently lost after a successful database commit.

---

## 17. Event Model

Core domain events include:

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

Provider events include:

```text
ProviderWebhookReceived
ProviderPaymentAuthorized
ProviderPaymentCaptured
ProviderPaymentFailed
ProviderPaymentRefunded
ProviderPaymentDisputed
ProviderSettlementReported
```

Events are immutable, have stable IDs, and consumers must tolerate duplicates.

---

## 18. Idempotency and Concurrency

Idempotency exists at multiple layers:

```text
API request
  -> Payment Request
  -> Provider operation
  -> Provider event
  -> Ledger posting
  -> Outbox publication
```

The same idempotency key must not be reused with materially different request data.

Concurrency controls must protect:

- wallet available balance;
- budget available amount;
- payment state transitions;
- approval decisions;
- provider operations;
- ledger postings.

Database transactions and row-level locking/reservation semantics are preferred for V1 financial critical sections.

---

## 19. Security Model

Non-negotiable rules:

1. Agent never owns user funds.
2. Agent never receives primary financial credentials.
3. Financial authorization is evaluated server-side.
4. Least privilege applies to delegation, credentials, and policy.
5. Missing/invalid/expired authorization fails closed.
6. Provider secrets remain isolated from normal Agent API responses.
7. Approval is bound to the exact payment intent.
8. Financial operations are idempotent.
9. Financial records are append-oriented and auditable.
10. Privileged administrative operations require separate authorization and audit.

API authentication should use short-lived, scoped, audience-bound credentials appropriate to the deployment and should bind the authenticated caller to the claimed Agent identity.

---

## 20. API Contract

The normative machine-readable API contract remains:

```text
specs/v1/openapi.yaml
```

Primary financial operation:

```http
POST /v1/payments
Idempotency-Key: <unique-key>
```

The API response describes operation state; it is not itself the financial ledger.

Errors should converge on RFC 9457-style Problem Details using `application/problem+json`, with stable machine-readable error types/codes and correlation IDs.

V1 API must eventually represent the canonical payment states and asynchronous next actions without leaking provider secrets.

---

## 21. PostgreSQL Canonical Persistence Model

The implementation-oriented schema should converge toward these logical tables:

```text
accounts
agents
delegations
authorization_evidence
wallets
ledger_accounts
ledger_journals
ledger_postings
funding_sources
payment_instruments
merchants
policies
policy_versions
budgets
budget_reservations
payment_requests
approvals
payments
payment_authentications
provider_operations
transactions
settlements
reconciliation_records
provider_events
audit_events
outbox_events
notifications
```

Not every table must be exposed through the public API.

`users` need not be duplicated in Agent-Pay if identity is externally owned; `accounts.owner_reference` is the explicit integration boundary.

---

## 22. Reference Implementation Topology

V1 deployment:

```text
API
 |
 v
Agent-Pay Modular Monolith
 |-- Agent / Delegation
 |-- Authorization Context
 |-- Policy / Budget
 |-- Approval
 |-- Payment
 |-- Instrument / Provider Adapters
 |-- Transaction / Ledger
 |-- Settlement / Reconciliation
 |-- Audit / Notification
 |
 +--> PostgreSQL
 +--> Redis (optional operational acceleration)
 +--> Outbox Worker
```

Microservice decomposition is a future operational decision, not a protocol requirement.

---

## 23. Observability

Every financial flow should carry a correlation ID and, where applicable, a causation ID.

Metrics should cover:

- payment request rate;
- policy denials;
- budget denials;
- approval latency;
- payment success/failure;
- unknown external outcomes;
- provider latency/error rate;
- webhook verification failures;
- reconciliation mismatches;
- ledger posting failures;
- outbox backlog;
- notification delivery failures.

Logs must not expose payment credentials, authentication secrets, or sensitive financial data unnecessarily.

---

## 24. Conformance and Testing

Conformance must verify behavior rather than implementation technology.

Minimum categories:

- payment intent validation;
- authentication/delegation evidence handling;
- policy decisions;
- budget reservation/concurrency;
- approval binding and replay prevention;
- payment state transitions;
- authentication challenge lifecycle;
- idempotency;
- provider event verification/deduplication;
- settlement/reconciliation;
- refund/reversal distinction;
- ledger integrity and balance rules;
- RFC 9457 error behavior;
- security invariants.

Test vectors should include success, denial, retry, duplicate, timeout, webhook replay, out-of-order event, approval replay, budget race, refund, and reconciliation mismatch scenarios.

---

## 25. V1 Scope

### V1 must include

- Account/Agent/Delegation boundary;
- authorization context/evidence reference;
- policy evaluation;
- budget and reservation semantics;
- approval workflow;
- payment intent API;
- wallet abstraction;
- payment instrument abstraction;
- idempotent payment processing;
- explicit payment lifecycle;
- transaction records;
- append-oriented ledger with double-entry-ready model;
- provider adapter boundary;
- provider event persistence/deduplication;
- transactional outbox;
- audit;
- basic settlement/reconciliation model;
- conformance tests for core financial controls.

### V1 does not require

- a specific payment provider;
- a specific 3-D Secure implementation;
- full merchant/order/fulfillment infrastructure;
- general merchant trust/reputation;
- general-purpose agent identity infrastructure;
- microservices;
- Kafka or another mandatory event broker.

---

## 26. V2 / Future Expansion

Potential future capabilities:

- virtual cards;
- multiple payment providers and routing optimization;
- advanced risk/fraud engine;
- disputes/chargebacks;
- richer settlement and multi-currency accounting;
- direct bank/payment-rail integrations;
- UCP/ACP and other commerce adapters;
- richer ATF authorization evidence integration;
- policy composition/hierarchies;
- family/business multi-principal controls;
- stronger compliance and regulated-finance deployment profiles.

---

## 27. Architectural Invariants

The following are non-negotiable:

1. Agent is never owner of user money.
2. Agent never receives primary financial credentials.
3. Identity alone never grants spending authority.
4. Delegation alone does not bypass financial policy.
5. Policy alone does not create budget capacity.
6. Budget reservation is separate from wallet hold.
7. Approval is bound to an exact payment intent.
8. Payment Request is not Payment.
9. Payment is not Transaction.
10. Transaction is not Ledger truth by itself; ledger postings are authoritative accounting effects.
11. Refund is distinct from reversal/void and dispute.
12. External timeout does not automatically equal failure.
13. Financial mutations are idempotent.
14. Concurrent requests cannot overspend the same budget or wallet balance.
15. Provider credentials remain outside the Agent boundary.
16. External events are untrusted until verified.
17. Events are duplicate-tolerant.
18. Outbox publication is atomic with the state change it represents.
19. Historical financial records are not overwritten.
20. Every executable payment has reconstructable authorization/control context.
21. API responses do not replace financial truth.
22. Commerce context does not make Agent-Pay a commerce system of record.
23. Agent-Pay does not become a second general trust/identity network.
24. V1 implementation topology does not define protocol interoperability.

---

## 28. Consistency Gate Before V1 Freeze

The following artifacts must be reconciled against this document before V1 is frozen:

- `specs/v1/openapi.yaml`
- `specs/v1/database-schema.sql`
- `docs/architecture/payment-state-machine.md`
- `docs/architecture/event-model.md`
- `docs/security/security-model.md`
- `docs/protocol/api-v1.md`
- JSON schemas under `schemas/`
- conformance suite
- test vectors
- reference implementation

No implementation should be considered V1-conformant until these artifacts agree on entity names, lifecycle states, error semantics, idempotency behavior, and financial invariants.

---

## 29. Unresolved Decisions for the Next Gate

These are intentionally explicit rather than silently decided:

1. Exact double-entry journal/posting schema.
2. Exact authorization-evidence persistence format and ATF integration contract.
3. Exact policy versioning representation.
4. Exact budget reservation lifecycle and concurrency strategy.
5. Exact provider-operation model for authorize/capture/void/refund.
6. Exact settlement/reconciliation persistence model.
7. Exact API state exposure for asynchronous provider authentication.
8. Exact RFC 9457 error type catalog.
9. Whether Redis is required or merely optional in V1.
10. Which payment provider/rail, if any, is used by the first reference implementation.

These decisions are the subject of the next consistency-correction stage; they do not invalidate the architectural boundary established here.
