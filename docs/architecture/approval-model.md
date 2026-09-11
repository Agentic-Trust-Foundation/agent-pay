# Agent-Pay Approval Model

## Purpose

The Approval Engine manages explicit human approval when financial policy requires a user decision before payment execution.

> **Approval is a control point, not a substitute for authorization, policy, or budget evaluation.**

## Boundary

```text
Authorization Evidence
        ↓
Policy Decision
        ↓
Budget Reservation
        ↓
Approval Engine
        ↓
Payment Execution
```

Approval cannot expand delegation, override a hard policy denial, or create wallet funds.

## Approval Modes

Policy may produce:

```text
AUTO
NOTIFY
REQUIRE_APPROVAL
DENY
```

Only `REQUIRE_APPROVAL` enters the approval workflow.

## State Model

```text
NOT_REQUIRED

PENDING
  ├── APPROVED
  ├── DENIED
  ├── EXPIRED
  └── CANCELLED
```

Approval decisions must be terminal for the specific approval instance. A new decision after expiry or denial requires a new approval instance or an explicitly defined re-approval operation.

## Approval Request

Conceptual fields:

```text
Approval
├── id
├── payment_request_id
├── account_id
├── requested_by_agent
├── decision
├── requested_at
├── expires_at
├── decided_at
├── decided_by
├── reason
├── policy_version
├── authorization_evidence_reference
└── metadata
```

The approval record must bind to the exact Payment Request and relevant authorization/policy context.

## What the User Approves

The approval UI/API should present a stable payment summary, including where available:

- merchant
- amount
- currency
- purpose
- item summary
- agent identity/reference
- applicable policy/authority context
- payment instrument class, without exposing credentials
- expiration
- risk or authentication requirement when relevant

The approval must not silently change the financial intent between display and execution.

## Binding

An approval is valid only for the exact payment context for which it was created.

At minimum, binding should cover:

```text
payment_request_id
amount
currency
merchant/reference
account
agent
policy version
authorization evidence reference
```

Material changes require a new approval.

## Expiration

Every approval request should have an expiration time.

If the approval expires while the external payment state is ambiguous, the system must not blindly release all financial controls until reconciliation establishes whether execution occurred.

## Budget Interaction

For approval-required payments, budget capacity may be reserved before requesting approval.

```text
Policy
 ↓
Budget reservation
 ↓
Approval request
 ↓
APPROVED → execute
DENIED/EXPIRED/CANCELLED → release reservation
```

This prevents concurrent requests from consuming the same budget while the user is deciding.

## Idempotency and Replay Protection

Approval endpoints must be idempotent.

Repeated approval or denial requests for the same approval instance must not create duplicate execution attempts.

A stale approval must not be accepted after the approval has reached a terminal state.

## Authentication and Step-Up

The approval mechanism must authenticate the approving user and may require step-up authentication for higher-risk transactions.

Examples of triggers:

- high amount
- new merchant
- unusual location
- sensitive payment instrument
- elevated risk score
- provider authentication requirement

Authentication is separate from approval semantics.

## Audit

Record at least:

- approval requested
- approval presented
- approval approved/denied
- approver reference
- authentication/step-up outcome when applicable
- timestamp
- payment request reference
- correlation ID
- policy and authorization evidence references

Do not store unnecessary secrets or authentication credentials in audit records.

## Notification

Approval requests may generate notifications through user-configured channels. Notification delivery does not itself constitute approval.

```text
Notification delivered ≠ Approval granted
```

## Fail-Closed

If the system cannot safely determine that a valid approval exists, payment execution must not proceed when approval is required.

## Non-Responsibilities

The Approval Engine does not:

- establish agent identity
- create delegation
- decide general merchant trust
- mutate ledger balances directly
- select arbitrary payment instruments
- bypass policy
- bypass budget controls

## V1 Direction

V1 should implement an approval state machine in the modular monolith with PostgreSQL persistence, authenticated approval endpoints, immutable audit records, expiration handling, and strict binding to Payment Request state.
