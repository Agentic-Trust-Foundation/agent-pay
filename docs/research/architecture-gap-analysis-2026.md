# Agent-Pay Architecture Gap Analysis

## Purpose

This review cross-checks the current Agent-Pay architecture against current payment-security, API-security, OAuth, payment messaging, and agentic-commerce standards and practices. It is intended to prevent architectural omissions before the Policy/Budget and reference-implementation phases.

This is an architecture review, not a legal, regulatory, PCI assessment, or payment-processor certification.

## Executive Conclusion

The current architecture has the correct high-level separation:

```text
Agent / Trust Context
        ↓
Agent-Pay financial controls
        ↓
Payment Router
        ↓
Payment Instrument / Provider
        ↓
Merchant / Rail
        ↓
Transaction / Settlement / Ledger
```

The core model should be retained. However, several capabilities need to become explicit before the design is considered implementation-complete.

### Highest-priority gaps

1. **Mandate / authorization evidence and transaction binding**
2. **Asynchronous provider/webhook processing**
3. **Reconciliation and settlement lifecycle**
4. **Disputes / chargebacks / reversals**
5. **Payment authentication such as 3-D Secure where card rails require it**
6. **Payment credential/token boundary and PCI scope minimization**
7. **True accounting semantics / double-entry journal model**
8. **Budget reservation lifecycle and concurrency semantics**
9. **User identity/account ownership model**
10. **API error, pagination, versioning, correlation and event contracts**
11. **Agent authorization protocol interoperability**
12. **Operational controls: risk decisions, rate limits, observability, key rotation and incident response**

## 1. Agent Authorization Evidence

The current model correctly separates Agentic Trust Foundation authority from Agent-Pay spending policy. The next design step must make the authorization evidence carried into a payment explicit.

Current concept:

```text
User → Agent → Delegation → Policy → Budget → Approval → Payment
```

Required future concept:

```text
Trust / Delegation Evidence
        ↓
Payment Authorization Context
        ↓
Specific Payment Intent
        ↓
Policy + Budget + Risk + Approval
        ↓
Execution
```

AP2 is especially relevant here: it defines user-approved mandates, transaction-bound authorization, cryptographic mandate chains and receipts. Agent-Pay does not need to adopt AP2 wholesale, but its domain model should leave a first-class place for authorization evidence, mandate references, proof-of-possession/binding, and verifier receipts.

**Decision:** Add an `authorization_evidence` / `mandate_reference` concept to the payment authorization context. Keep the protocol adapter-neutral so ATF/AP2/other authorization systems can be integrated later.

## 2. Asynchronous Payment Processing

The current Payment model is too synchronous if interpreted as a generic provider integration.

Real payment systems can produce later events such as authorization, capture, failure, dispute, bank confirmation, or other asynchronous state changes. Webhooks/events are therefore part of the payment architecture, not merely an integration convenience.

Required model:

```text
Payment
  ↓
Provider Request
  ↓
PENDING / PROCESSING
  ↓
Provider Event / Webhook
  ↓
Verified Event
  ↓
State Transition
  ↓
Transaction / Ledger / Audit
```

**Decision:** Add provider event ingestion, signature verification, replay protection, event idempotency, event ordering strategy, and dead-letter/retry semantics to the payment integration architecture.

## 3. Reconciliation and Settlement

The current architecture mentions Settlement but does not yet model it.

Payment execution and financial settlement are not necessarily the same event. Agent-Pay needs a reconciliation boundary between:

```text
Internal Payment / Transaction
        ↕
Provider / Rail Reference
        ↕
Settlement Record
        ↕
Ledger
```

Required future concepts:

- settlement batch
- settlement reference
- provider statement/import
- reconciliation status
- unmatched item
- reconciliation adjustment
- settlement date/value date where relevant

**Decision:** Add a Settlement/Reconciliation module to the future architecture before production payment rails.

## 4. Refunds, Reversals, Disputes and Chargebacks

Refunds are already modeled, but the design should distinguish at least:

- refund initiated by merchant/system
- payment reversal/void
- provider failure
- dispute
- chargeback
- chargeback reversal/representment outcome

A chargeback is not simply a refund initiated by Agent-Pay. It can arrive asynchronously and can require evidence and financial adjustments.

**Decision:** Extend the future Transaction lifecycle to include `DISPUTED`, `CHARGEBACK`, `CHARGEBACK_REVERSED` or equivalent domain events rather than forcing every negative payment outcome into `REFUND`.

## 5. Card Authentication / 3-D Secure

For card-not-present payments, authentication can be an independent step from authorization and capture. EMV 3-D Secure defines frictionless and challenge flows and supports out-of-band authentication.

Required future abstraction:

```text
Payment
  ↓
Risk / Provider Decision
  ↓
Authentication Required?
  ├── No → Authorization
  └── Yes → 3DS / Other Authentication
                    ↓
                Authorization
```

**Decision:** Payment Router and Payment State Machine must permit an intermediate `AUTHENTICATION_REQUIRED` state without assuming that every payment is immediately executable.

## 6. Payment Credentials, Tokenization and PCI Scope

The existing principle that Agents never receive primary financial credentials is correct and should be strengthened.

Agent-Pay should prefer:

```text
Agent
  ↓
Payment Intent
  ↓
Agent-Pay
  ↓
Token / Provider Reference
  ↓
Payment Provider
```

rather than storing raw PAN or sensitive authentication data in the core application.

PCI DSS v4.0.1 is the current PCI DSS revision. PCI SSC guidance emphasizes protection of payment data and provides tokenization guidance; scope depends on the actual architecture and responsibilities.

**Decision:** Add an explicit PCI/data-classification boundary and tokenization strategy before implementing real card storage or virtual cards.

## 7. Ledger: Move From Ledger Entries Toward a Journal Model

The current V1 ledger is directionally correct, but a single wallet-centric entry table cannot by itself enforce accounting equality.

The production-oriented direction should be:

```text
Journal / Transaction
        ↓
Journal Lines
   ├── Debit Account
   └── Credit Account
```

with the wallet balance derived from posted entries.

The current `ledger_entries` abstraction can remain as the first implementation layer, but the design should explicitly preserve a path to double-entry accounting and reconciliation.

**Decision:** Before production settlement, introduce a journal/balance-account model that can enforce balanced financial movements.

## 8. Budget Reservation

Wallet holds and spending-budget reservations are different resources.

Example:

```text
Wallet available: $1000
Budget remaining: $500

Payment request: $300

Wallet Hold:       $300
Budget Reserve:    $300
```

Both reservations must be released or consumed consistently.

**Decision:** Model budget reservation as a first-class state transition. Do not infer budget consumption only from successful ledger debits.

## 9. User / Account Ownership

The domain model has a User entity, but the current SQL schema begins with `accounts.owner_reference` rather than a first-class User table.

This is acceptable as an implementation placeholder, but it should not silently become the final ownership model.

**Decision:** Define an explicit Account Owner / User identity boundary before authentication and production account management are implemented. The identity provider remains external to Agent-Pay.

## 10. API Contract Improvements

The current API contract should eventually add:

- RFC 9457 `application/problem+json` error representation
- pagination conventions
- filtering/sorting conventions
- `request_id` / `correlation_id`
- provider references where appropriate
- webhook/event endpoints
- explicit authentication schemes
- explicit authorization scopes
- `Retry-After` behavior for retryable operations
- rate-limit semantics
- optimistic/concurrency semantics where needed
- API deprecation/versioning policy

The current payment status enum also needs to remain synchronized with the domain state machine; the current OpenAPI draft omits `BUDGET_CHECK` even though the domain lifecycle includes it.

## 11. Idempotency Must Cover More Than HTTP POST

Idempotency is already present and is correct as a principle. The next implementation should distinguish:

```text
API idempotency
Provider idempotency
Ledger operation idempotency
Webhook/event idempotency
```

A single HTTP idempotency key does not automatically protect downstream provider retries or duplicated webhooks.

The implementation should store enough request fingerprint/result metadata to reject key reuse with materially different financial parameters.

## 12. OAuth / Token Security

Agent-Pay should use modern OAuth security practices where OAuth is selected for API authorization. RFC 9700 is the current OAuth 2.0 Security BCP and emphasizes stronger practices such as PKCE and reduced token authority. Resource/audience binding should be considered for high-value payment APIs.

For agent ecosystems, short-lived, narrowly scoped, audience-bound credentials are preferable to broad long-lived bearer credentials.

**Decision:** Keep authentication externalizable, but make token audience, scopes, expiry, rotation, and sender-constrained credentials part of the security requirements.

## 13. Agentic Commerce Protocol Interoperability

The ecosystem has moved beyond a generic "agent calls payment API" model.

Current relevant standards/projects include:

- AP2 for agent payment authorization and mandate evidence
- UCP for agentic commerce journeys
- ACP for agent/merchant checkout interactions
- MCP for tool/API authorization
- OAuth security profiles for protected APIs

Agent-Pay should not become a duplicate commerce protocol. It should expose a financial execution/control layer that can be invoked by these ecosystems.

**Decision:** Add an explicit interoperability layer:

```text
UCP / ACP / A2A / MCP / Direct API
                ↓
        Agent-Pay Adapter
                ↓
        Agent-Pay Core
```

## 14. Merchant and Order Context

A payment should not assume that `merchant + amount` is enough forever.

Future integrations may require:

- order reference
- cart/checkout reference
- merchant transaction reference
- fulfillment reference
- invoice reference
- tax/shipping totals
- payment method constraints
- return/refund policy reference

**Decision:** Preserve an extensible `commerce_context` / `merchant_reference` area without coupling the core financial ledger to a specific commerce protocol.

## 15. Risk Engine

Risk is present in the architecture but not yet modeled as a domain component.

The design should distinguish:

```text
Policy Decision
      ≠
Risk Decision
      ≠
Payment Provider Decision
```

A payment can be policy-allowed but risk-blocked; a payment can be low-risk but require user approval; a provider can still decline it.

**Decision:** Create a versioned Risk Decision record with reason codes and decision provenance before implementing advanced fraud logic.

## 16. Audit vs Financial Ledger

The current architecture correctly separates them.

Keep:

```text
Ledger      = financial truth
Audit Event = operational/security evidence
```

Do not use audit events as a financial ledger and do not put arbitrary operational metadata into ledger entries merely to avoid creating audit records.

## 17. Events and Outbox

The internal event model should eventually use a transactional outbox pattern for events that must reflect committed database state.

Example:

```text
DB Transaction
 ├── Payment state change
 ├── Ledger change
 └── Outbox event
          ↓ commit
       Event Worker
          ↓
 Notification / Webhook / Queue
```

This avoids publishing a `PaymentSucceeded` event when the database transaction later rolls back.

**Decision:** Add an outbox table to the implementation architecture before introducing external asynchronous events.

## 18. Observability and Operations

Production payment systems require more than application logs.

Required architecture areas:

- structured logs
- metrics
- distributed tracing
- correlation IDs
- provider request IDs
- financial reconciliation metrics
- alerting
- audit retention
- security event monitoring
- dead-letter queues
- replay tooling
- incident response

No sensitive payment credentials should appear in logs, traces, metrics, or error payloads.

## 19. Reliability and Failure Modes

The state machine must explicitly handle:

- timeout after provider acceptance
- client timeout after server acceptance
- duplicate request
- duplicate webhook
- webhook arriving before synchronous response
- provider retry
- provider outage
- partial internal failure
- database failover
- worker retry
- approval expiration during payment processing
- wallet hold expiration
- budget reservation expiration

A timeout must not automatically mean payment failure.

## 20. Compliance / Jurisdiction Boundary

Agent-Pay is intentionally vendor-neutral and jurisdiction-neutral at the protocol level. A production financial service may nevertheless become subject to requirements such as licensing, KYC/AML, sanctions screening, consumer protection, privacy, money transmission, card-network rules, and local payment regulations depending on its business model and jurisdiction.

**Decision:** Keep compliance as a pluggable policy/control boundary and do not encode one jurisdiction's legal assumptions into the core protocol.

## 21. Recommended Revised Architecture

```text
                    Agent / Commerce Ecosystem
            ┌──────────┬─────────┬─────────┬─────────┐
            │ UCP      │ ACP     │ A2A     │ MCP/API │
            └──────────┴─────────┴─────────┴─────────┘
                              ↓
                     Agent-Pay Adapter Layer
                              ↓
                    ┌─────────────────────┐
                    │ Agent-Pay Core      │
                    │                     │
                    │ Authorization       │
                    │ Policy              │
                    │ Budget              │
                    │ Risk                │
                    │ Approval            │
                    │ Payment Intent      │
                    │ Payment Router      │
                    └──────────┬──────────┘
                               ↓
                    Payment Instrument Layer
                               ↓
                 Provider / Rail / 3DS / Token
                               ↓
                         Merchant / Bank
                               ↓
                    Provider Events / Webhooks
                               ↓
                 Transaction / Settlement / Dispute
                               ↓
                 Journal / Ledger / Reconciliation
                               ↓
                    Audit / Outbox / Notification
```

## 22. Priority Before Continuing Implementation

### P0 — must be resolved before production-oriented implementation

- authorization evidence / mandate binding
- asynchronous payment events
- ledger journal semantics
- budget reservation semantics
- idempotency across API/provider/webhook layers
- payment credential/token boundary
- reconciliation/settlement model
- failure and timeout state machine

### P1 — should be designed before reference implementation expands

- Risk Decision model
- 3DS/authentication state
- disputes/chargebacks
- User/Account ownership boundary
- outbox/event model
- API error/pagination/auth conventions
- merchant/order context
- observability requirements

### P2 — future interoperability / scale

- AP2/UCP/ACP adapters
- ISO 20022 mapping where a payment rail requires it
- multi-currency/FX
- advanced fraud/risk models
- multi-provider routing optimization
- regulatory/compliance profiles

## Final Architectural Judgment

The existing Agent-Pay direction is sound and should not be replaced. The main risk is not the high-level architecture; it is allowing implementation to proceed while treating payment execution as a simple synchronous `Payment → Provider → Transaction` flow.

The architecture should therefore retain the current modular-monolith approach while adding explicit boundaries for authorization evidence, asynchronous provider events, reconciliation, settlement, disputes, authentication, tokenization, budget reservations, and a stronger accounting model.

These additions do not require premature microservices. They are domain and protocol boundaries first; deployment boundaries can remain inside the modular monolith until scale or organizational needs justify extraction.
