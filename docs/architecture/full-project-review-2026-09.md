# Agent-Pay Full Project Review — 2026-09

## Status

Architecture review only. This document records the repository-wide consistency review before the Master Project Schema and V1 freeze.

Review target: `main` at commit `41e118cc53f6a7449cfbb3bd410e81adc545800d`.

## Executive Summary

The project direction is coherent and the core boundary is strong:

- Agent-Pay is a financial control and payment layer, not a general trust or commerce protocol.
- Agentic Trust Foundation owns identity, delegation, authorization and trust evidence.
- Agent-Pay owns spending policy, budget, approval, payment execution, transaction lifecycle, settlement/reconciliation and ledgering.
- V1 modular-monolith architecture is appropriate.
- PostgreSQL is correctly treated as financial source of truth.
- Transactional outbox, provider events, reconciliation, idempotency, credential isolation and explicit authentication states are correctly identified.

However, the repository is **not yet internally consistent enough for a V1 freeze**. The main gaps are no longer conceptual; they are contract/data-model consistency gaps.

The most important finding is:

> The architecture documents describe a more mature lifecycle than the current OpenAPI and PostgreSQL schema actually implement.

The project should therefore enter a **consistency-correction phase** before implementation starts.

---

## Review Classification

| Area | Status | Severity | Finding |
|---|---|---:|---|
| Vision / Positioning | Correct | — | Core product boundary is clear and consistent. |
| ATF Boundary | Correct | — | Trust/delegation responsibility is cleanly separated. |
| Modular Monolith | Correct | — | Appropriate V1 topology. |
| Domain Model | Mostly correct | Medium | Core entities are right, but several operational entities are missing from the DB model. |
| Authorization Evidence | Incomplete | High | Evidence is described but not first-class in the database/API. |
| Policy Engine | Incomplete | High | Versioning is required by the architecture but absent from the DB schema. |
| Budget | Incomplete | Critical | Reservation lifecycle is documented but no reservation table exists. |
| Approval | Incomplete | High | DB permits only one approval instance per payment request; this conflicts with re-approval/history semantics. |
| Payment State Machine | Inconsistent | Critical | OpenAPI/DB enums do not match the documented lifecycle. |
| Payment Authentication | Incomplete | High | State is documented but no persistent authentication operation model exists. |
| Payment Routing | Mostly correct | Medium | Adapter abstraction is clear; provider operation persistence is missing. |
| Wallet / Ledger | Incomplete | Critical | Current DB is wallet-centric single-sided entries, not yet double-entry-ready at schema level. |
| Transaction Lifecycle | Incomplete | High | Refund/reversal/dispute semantics are documented but weakly represented in DB/API. |
| Events / Webhooks | Incomplete | Critical | Outbox/provider-event persistence is described but absent from current DB schema. |
| Settlement / Reconciliation | Incomplete | Critical | Reconciliation is documented but no DB model exists. |
| Security | Mostly correct | High | Principles are good; concrete API auth, token audience/scope, webhook trust and approval authentication contracts remain unspecified. |
| Commerce Boundary | Correct | — | Order/payment separation is clear. |
| API Contract | Inconsistent | Critical | OpenAPI lags behind architecture and state model. |
| PostgreSQL Schema | Incomplete | Critical | Several required entities and lifecycle states are missing. |
| Conformance | Missing implementation | Medium | Only a planned README exists. |
| Test Vectors | Missing implementation | Medium | Directory contains only a placeholder README. |
| Reference Implementation | Not started | Medium | Architecture README exists; executable implementation does not. |
| Governance | Incomplete | Medium | Governance/license release process remains future work. |

---

# 1. What Is Already Strong

## 1.1 Product boundary

The README and architecture documents consistently define Agent-Pay as financial control + payment execution, not as a general agent identity/trust system or full commerce protocol.

This should remain frozen as a core principle.

## 1.2 Authority model

The distinction between:

- identity
- delegation
- authorization evidence
- spending policy
- budget
- approval
- payment instrument
- payment
- transaction
- ledger

is conceptually correct.

The rule that an Agent receives spending authority rather than primary financial credentials is also consistently reflected in the security and tokenization documents.

## 1.3 Policy / budget / wallet separation

The project correctly distinguishes:

```text
Policy  = may this spending happen?
Budget  = is capacity available?
Wallet  = is actual money available?
```

This is one of the most important architectural decisions and should be retained.

## 1.4 Ambiguous provider outcomes

The state-machine and reference-implementation documents correctly reject the dangerous assumption that a timeout means payment failure.

`UNKNOWN_EXTERNAL_OUTCOME` and reconciliation are necessary concepts and should be promoted into the normative model.

## 1.5 Outbox/event architecture

The decision to use PostgreSQL transactional outbox instead of introducing Kafka/NATS in V1 is appropriate.

## 1.6 Credential boundary

The repository consistently prohibits raw PAN/CVV, bank credentials, provider secrets and similar material from Agent-facing flows.

---

# 2. Critical Consistency Findings

## C1 — Payment State Machine vs OpenAPI vs Database

### Architecture says

The normative lifecycle includes:

```text
REQUESTED
VALIDATING
AUTHENTICATION_REQUIRED
AUTHENTICATED
POLICY_CHECK
BUDGET_CHECK
APPROVAL_REQUIRED / APPROVED
PAYMENT_PENDING
PROCESSING
UNKNOWN_EXTERNAL_OUTCOME
SUCCEEDED / FAILED
SETTLEMENT / SETTLED
```

Refunds, reversals and disputes have additional lifecycles.

### OpenAPI currently exposes

```text
REQUESTED
VALIDATING
POLICY_CHECK
APPROVAL_REQUIRED
APPROVED
PAYMENT_PENDING
PROCESSING
SUCCEEDED
FAILED
CANCELLED
REFUND_REQUESTED
REFUNDED
```

### PostgreSQL currently exposes

The same reduced enum, with `BUDGET_CHECK` present but without authentication, unknown-outcome, settlement and dispute states.

### Required correction

Create one canonical state taxonomy and make:

1. state-machine document
2. OpenAPI enum
3. PostgreSQL enum
4. event model
5. reference implementation state machine

derive from the same lifecycle definition.

Do not maintain five independent copies of the state vocabulary.

---

## C2 — Budget Reservation Is Architectural but Not Persistent

The budget documents require a durable reservation identity and explicitly describe:

```text
RESERVED → CONSUMED
RESERVED → RELEASED
RESERVED → EXPIRED
```

The current `budgets` table has only `reserved_amount` as an aggregate field. There is no `budget_reservations` table.

### Risk

Without a reservation record, the system cannot safely answer:

- which payment reserved capacity?
- who created the reservation?
- when does it expire?
- was it consumed or released?
- is a retry the same reservation?
- which reservation is associated with an ambiguous external payment?

### Required correction

Add a first-class `budget_reservations` model with stable identity, payment request reference, amount, state, expiration, idempotency key, timestamps and audit/correlation references.

---

## C3 — Transactional Outbox Is Documented but Missing from DB

The event architecture requires the outbox row to commit atomically with the business transaction.

The current PostgreSQL schema contains no `outbox_events` table.

### Required correction

Add a durable outbox model with at least:

- event_id
- event_type
- event_version
- aggregate_type
- aggregate_id
- correlation_id
- causation_id
- idempotency_key
- payload
- status
- attempts
- next_attempt_at
- published_at
- created_at

The outbox is not optional if V1 claims reliable event publication.

---

## C4 — Provider Webhook/Event Persistence Is Missing

The architecture requires provider events to be persisted before processing so that replay, deduplication and forensic investigation are possible.

The current schema has no provider event table.

### Required correction

Add a `provider_events` / `provider_webhook_events` model containing:

- provider
- provider_event_id
- event_type
- received_at
- signature verification result
- payload/reference
- processing state
- processed_at
- error information
- payment/provider operation references
- deduplication identity

Raw sensitive payload retention must be governed by a separate data-retention policy.

---

## C5 — Reconciliation Is Defined but Not Persisted

Settlement/reconciliation documentation defines multiple reconciliation outcomes, but there is no corresponding database model.

### Required correction

Add at least:

```text
reconciliation_records
settlement_observations
```

or an equivalent normalized model.

It must be possible to record both matched and mismatched observations without changing historical ledger entries.

---

# 3. High-Priority Domain/Data Model Findings

## H1 — Authorization Evidence Needs a First-Class Reference

`payment_requests.authorization_context` is useful as a snapshot, but it should not be the only representation of upstream authority evidence.

The architecture explicitly requires evidence ID, issuer, version, freshness/revocation information and binding to the payment context.

### Required direction

Introduce an `authorization_evidence` reference/model or an equivalent immutable evidence record.

The payment request should retain:

- evidence ID/reference
- issuer
- evidence version
- validation result
- validated_at
- expiry/freshness information
- decision/reference hash where applicable

The actual cryptographic assertion should remain behind the integration/security boundary unless required.

---

## H2 — Policy Versioning Is Missing from PostgreSQL

The policy architecture explicitly says every decision must identify policy version(s), but `policies` currently has no version field or policy-version table.

### Required direction

Prefer:

```text
policies
policy_versions
policy_evaluations
```

rather than mutating one JSON document in place.

Historical payment decisions must point to immutable policy versions.

---

## H3 — Approval History Is Too Narrow

Current schema has:

```sql
UNIQUE(payment_request_id)
```

on `approvals`.

But the approval architecture explicitly allows a new approval instance after expiry/denial and requires historical reconstruction.

### Required direction

Allow multiple approval instances per payment request while enforcing only one active approval when appropriate.

A partial uniqueness rule or explicit lifecycle constraint is preferable to a permanent one-to-one relationship.

---

## H4 — Payment Authentication Has No Data Model

The authentication document defines a distinct lifecycle and references authentication transaction/challenge data, but there is no table for it.

### Required direction

Add a payment-authentication operation model containing:

- payment_id
- provider/instrument reference
- authentication type
- status
- challenge reference
- next action metadata
- created/expired/completed timestamps
- provider authentication reference
- correlation ID

Secrets and OTP values must never be stored.

---

## H5 — Provider Operation Identity Is Missing

The state-machine documents correctly require durable provider operation identifiers, but `payments.provider_reference` is too weak for retries, authorization/capture/void/refund operations and ambiguous outcomes.

### Required direction

Introduce a provider operation abstraction, for example:

```text
provider_operations
```

with operation type, provider, provider operation ID, payment/transaction reference, state, idempotency key and timestamps.

---

## H6 — Ledger Is Not Yet True Double-Entry

The current schema has one `ledger_account_id` per ledger entry and an entry type of CREDIT/DEBIT/HOLD/etc.

The architecture document itself acknowledges that the V1 model is wallet-centric and only double-entry-compatible.

### Finding

This is acceptable for an architecture draft, but it is not sufficient if Agent-Pay is eventually intended to hold authoritative financial truth at serious scale.

### Required V1 decision

Before implementation, explicitly choose one:

**Option A — Double-entry-ready V1:**
Keep public wallet semantics but implement journal + journal-line primitives internally.

**Option B — Simplified ledger V1:**
Keep current model, explicitly label it as a controlled sub-ledger and define the upgrade path.

Recommendation: **Option A**. The project is payment/financial infrastructure; accounting correctness should not be retrofitted after live money exists.

---

# 4. Important Lifecycle Findings

## H7 — Payment vs Transaction vs Ledger Needs One Canonical Relationship

The conceptual relationship is correct:

```text
Payment Request → Payment → Transaction → Ledger
```

But refunds, reversals, partial captures and disputes require multiple financial operations related to one payment.

### Required direction

Treat `Transaction` as an accounting/economic operation rather than assuming one payment always maps to exactly one transaction.

Support:

- authorization
- capture/debit
- void/reversal
- refund
- adjustment
- dispute/chargeback
- settlement observation

with explicit operation type and parent/original references.

---

## H8 — Refund, Reversal and Dispute Need Separate Semantics

The documentation correctly says they are distinct, but the DB `transactions.type` is unrestricted `TEXT`.

### Required direction

Replace uncontrolled text with a documented enum or constrained reference model.

Partial refunds must have aggregate limits so total refunded amount cannot exceed refundable amount.

---

## H9 — Settlement State Must Not Be Confused with Payment Success

The repository correctly distinguishes execution from settlement, but the DB/API do not yet represent settlement clearly.

### Required direction

Keep payment execution state separate from settlement/reconciliation state.

Do not force `SUCCEEDED` to mean `SETTLED`.

---

# 5. API Contract Findings

## A1 — OpenAPI Is Behind the Architecture

The OpenAPI document is currently the biggest normative mismatch.

It should be updated only after the canonical state/data model is finalized.

Required additions include:

- budget-related states/results
- authentication states
- unknown external outcome
- settlement/reconciliation representation where externally exposed
- explicit refund/reversal operations where supported
- authorization evidence reference
- budget reservation result
- provider operation/reference
- challenge/next-action representation
- event/webhook contract if Agent-Pay exposes callbacks

## A2 — Error Model Should Move to RFC 9457 Problem Details

The current API uses a custom object:

```json
{"code":"...","message":"...","correlation_id":"..."}
```

The architecture should standardize on `application/problem+json` semantics while retaining an Agent-Pay-specific stable error code and correlation/reference fields.

## A3 — Authentication/Authorization Contract Is Too Abstract

The security document says scoped credentials/tokens, but the API does not specify the authentication scheme, audience, scopes, or how the caller is bound to `agent_id`.

The final V1 contract must prevent a caller from simply placing another agent ID in a request body.

## A4 — Idempotency Needs Multi-Layer Semantics

The API correctly requires `Idempotency-Key`, but the final specification must distinguish:

- API request idempotency
- payment operation idempotency
- provider operation idempotency
- webhook event deduplication
- approval decision idempotency
- ledger posting idempotency

One header alone does not solve all of these.

---

# 6. Security Findings

## S1 — Good architecture, insufficient normative detail

The security model identifies the correct threats, but the implementation contract still needs explicit definitions for:

- caller authentication mechanism
- token audience/resource binding
- required scopes
- agent-to-account binding
- administrative roles
- approval authentication
- webhook signature verification
- replay window
- secret storage boundary
- key rotation
- audit integrity protection
- rate limits
- abuse controls

These should be specified before executable implementation.

## S2 — Approval Authentication Must Be Separate from Agent Authentication

The approval document correctly distinguishes approval from authorization and authentication. The API must preserve that distinction.

An Agent credential must never be sufficient to approve its own payment.

## S3 — Account Ownership Boundary Needs Explicit Naming

The DB currently has `accounts.owner_reference` rather than a local `users` table.

This is compatible with the ATF boundary if intentionally designed as an external principal reference.

The final schema should rename/document this explicitly as an external principal/subject reference rather than leaving ambiguity about whether Agent-Pay owns User identity.

---

# 7. Commerce Boundary Findings

The commerce boundary is one of the strongest parts of the project.

The repository correctly avoids turning Payment into Order and keeps order/cart/checkout references as context.

One required addition is to make **amount binding** normative:

```text
commerce expected amount
        ↓
financial authorized amount
        ↓
final provider amount
```

A material change must trigger re-evaluation and potentially re-approval.

Agent-Pay should not become the system of record for catalog, inventory or fulfillment.

---

# 8. Repository Maturity Findings

## R1 — Conformance is planned, not implemented

The conformance directory currently contains only a README describing planned categories.

This is acceptable before V1 implementation, but it means the project cannot yet claim protocol conformance.

## R2 — Test vectors are planned, not implemented

The `test-vectors` directory currently contains only a placeholder README.

The next phase should add deterministic vectors for:

- policy decisions
- budget reservation races
- approval transitions
- state transitions
- idempotency
- refunds
- webhook deduplication
- reconciliation mismatches
- authorization evidence validation

## R3 — Executable reference implementation has not started

The reference directory currently contains architectural guidance rather than executable code.

This is consistent with the current project status.

## R4 — Schemas directory is still placeholder-level

The schemas directory currently contains only a README. Once the master schema is approved, reusable JSON Schemas should be generated/maintained for normative protocol objects rather than duplicating structures independently across documents.

## R5 — Test directory contains only a connection test

The current test tree contains a GitHub connection test rather than domain/conformance tests. This confirms that the project has not yet crossed into executable implementation.

---

# 9. Normative Source-of-Truth Problem

The repository currently repeats important definitions in multiple places:

- README
- domain model
- transaction lifecycle
- payment state machine
- OpenAPI
- PostgreSQL schema
- event model
- reference implementation

This is normal during architecture work, but it becomes dangerous once implementation starts.

## Required V1 rule

Create a Master Project Schema that becomes the semantic source of truth.

Then define ownership:

```text
Master Project Schema
        |
        +--> OpenAPI
        +--> PostgreSQL schema
        +--> State machine
        +--> Event catalog
        +--> JSON schemas
        +--> Conformance vectors
        +--> Reference implementation
```

Derived artifacts must not silently redefine domain semantics.

---

# 10. Recommended V1 Canonical Entity Set

The review recommends the following canonical model before implementation:

```text
External Principal Reference
Account
Agent
Delegation
Authorization Evidence

Policy
Policy Version
Policy Evaluation

Budget
Budget Reservation

Wallet
Ledger Account
Journal
Journal Line

Funding Source
Payment Instrument
Provider Operation
Payment Authentication

Merchant
Payment Request
Approval
Payment
Transaction

Settlement Observation
Reconciliation Record
Provider Event

Outbox Event
Audit Event
Notification
```

Not every item must be a public API resource. Some are internal persistence/processing entities.

---

# 11. Recommended V1 Lifecycle

```text
REQUESTED
   ↓
VALIDATING
   ↓
AUTHENTICATION_REQUIRED ──→ AUTHENTICATED
   ↓
AUTHORIZATION_VALIDATED
   ↓
POLICY_CHECK
   ├── DENIED
   ↓
BUDGET_CHECK
   ├── DENIED
   ↓
BUDGET_RESERVED
   ↓
APPROVAL_CHECK
   ├── AUTO
   ├── NOTIFY
   └── APPROVAL_REQUIRED
             ↓
          APPROVED
             ↓
       PAYMENT_PENDING
             ↓
          PROCESSING
        ┌─────┴──────────┐
        ↓                ↓
AUTHENTICATION_REQUIRED  UNKNOWN_EXTERNAL_OUTCOME
        ↓                ↓
    AUTHENTICATED     Recovery/Reconciliation
        ↓                ↓
        └──────→ PROCESSING
                    ↓
             SUCCEEDED / FAILED
                    ↓
             SETTLEMENT_PENDING
                    ↓
                  SETTLED
```

Refund, reversal and dispute must be represented as related financial operations, not forced into one linear payment enum.

This lifecycle is a proposed canonical target and must be reconciled with the final API before V1 freeze.

---

# 12. V1 Freeze Blockers

The following should be considered blockers for declaring the architecture internally frozen:

1. Canonical payment state vocabulary not yet synchronized.
2. Budget reservation persistence missing.
3. Outbox persistence missing.
4. Provider event persistence missing.
5. Reconciliation persistence missing.
6. Policy version persistence missing.
7. Authorization evidence persistence/reference missing.
8. Payment authentication persistence missing.
9. Provider operation model missing.
10. Ledger accounting model not yet explicitly finalized as simplified vs double-entry-ready.
11. Approval history model needs correction.
12. API authentication/binding contract needs normative definition.
13. Error contract should be standardized.

---

# 13. Non-Blockers / Later Phases

These do not need to block V1 architecture freeze if their boundaries are explicit:

- Kafka/NATS adoption
- microservice extraction
- multi-currency/FX
- chargeback automation
- advanced risk ML
- multiple live payment providers
- complex hierarchical budgets
- mobile application
- broad notification channels
- jurisdiction-specific compliance implementation
- production-grade bank settlement integrations

---

# 14. Review Verdict

## Overall

**Architecture direction: APPROVED WITH REQUIRED CONSISTENCY CORRECTIONS.**

The project does not need another conceptual redesign. It needs one disciplined normalization pass.

The correct next step is:

```text
FULL PROJECT REVIEW
        ↓
MASTER PROJECT SCHEMA
        ↓
CORRECT OPENAPI + DB + STATE + EVENTS
        ↓
V1 ARCHITECTURE FREEZE
        ↓
REFERENCE IMPLEMENTATION
        ↓
CONFORMANCE + TEST VECTORS
```

The most important principle for the next phase is:

> **Do not add more architecture documents until the existing documents are normalized into one canonical model.**

That is the point at which Agent-Pay should move from architecture accumulation to architecture convergence.
