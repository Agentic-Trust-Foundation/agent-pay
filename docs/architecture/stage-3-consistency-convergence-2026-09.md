# Agent-Pay Stage 3 — Consistency Convergence

**Date:** 2026-09-11  
**Status:** Active convergence baseline  
**Authority:** `docs/architecture/master-project-schema.md`

## Purpose

Stage 3 turns the Master Project Schema into an implementation-alignment gate. The goal is to remove contradictions between the domain model, API, PostgreSQL persistence, state machine, event model, security model, conformance assets, and reference implementation.

## Canonical authority

When documents disagree, precedence is:

1. Financial-control invariants
2. Master Project Schema
3. Payment State Machine / Event Model / Security Model
4. OpenAPI and protocol documentation
5. PostgreSQL implementation schema
6. Reference implementation and examples

Implementation artifacts must converge upward; they must not silently redefine the architecture.

## Stage 3 findings

| Area | Required V1 direction |
|---|---|
| Payment states | Explicit authentication and ambiguous-provider outcome states |
| Authorization evidence | First-class persistence and operation binding |
| Policy versioning | Immutable PolicyVersion reference |
| Budget reservation | Dedicated entity with concurrency/idempotency semantics |
| Approval history | Appendable approval attempts/history |
| Payment authentication | Durable authentication record |
| Provider operation | Explicit operation/idempotency lifecycle |
| Provider events | Durable verified-input record |
| Settlement | Settlement + reconciliation records |
| Outbox | Transactional outbox persistence |
| Ledger | Journal/posting model, double-entry-ready |
| Errors | RFC 9457 Problem Details |
| Commerce boundary | Explicit optional commerce context |
| API authentication | Authenticated caller bound to claimed Agent |

## Non-negotiable convergence rules

1. `PaymentRequest` is intent; `Payment` is execution; `Transaction` is an economic record; ledger postings are accounting truth.
2. An Agent never owns an Account, Wallet, or primary payment credential merely by being registered.
3. Delegation does not bypass financial policy or budget.
4. Budget reservation is separate from wallet hold/available balance.
5. Approval is bound to the exact payment intent; material changes invalidate prior approval.
6. External provider timeout produces an ambiguous outcome, not an automatic financial failure.
7. Provider events are persisted before domain processing and are deduplicated.
8. Outbox publication is atomic with the corresponding internal state change.
9. Financial mutations are idempotent and concurrency-safe.
10. Historical financial records are append-oriented and corrected by compensating records.
11. Provider credentials remain outside the Agent API trust boundary.
12. Agent-Pay consumes general identity/trust evidence from ATF or another trusted source; it does not become a second general identity network.

## API convergence checklist

The OpenAPI contract must represent caller authentication expectations, Agent/account/delegation references, authorization evidence, effective policy version, budget reservation, canonical payment states, payment authentication and safe next actions, approval history, provider operation state, unknown external outcome, refund/void semantics, optional commerce references, RFC 9457 errors, and idempotency behavior.

## PostgreSQL convergence checklist

The canonical persistence model is:

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

The implementation may add operational indexes and cached fields, but it must not omit a canonical financial-control entity without a documented reason.

## State/event convergence

The state machine and event model must agree on every externally observable financial transition. Events are facts, not commands. Provider events are untrusted input until authenticated and validated.

## Reference implementation gate

Before production financial execution, the reference implementation must demonstrate idempotent payment creation, policy decision, budget reservation/release/consume, exact-intent approval, authentication pause/resume, provider-operation idempotency, unknown-outcome recovery, durable provider-event ingestion, double-entry-ready ledger posting, transactional outbox, reconciliation mismatch recording, and append-only audit.

## Conformance gate

V1 conformance is behavioral. Passing an API schema check alone is insufficient; vectors must verify the financial-control invariants and failure/retry behavior.

## Intentionally deferred

The following remain explicit architecture decisions rather than hidden assumptions:

1. first payment provider/rail;
2. exact ATF authorization-evidence wire format;
3. Redis in the minimal reference profile;
4. provider adapter implementation;
5. production cryptographic key/vault integration;
6. full dispute/chargeback workflow.

These decisions must not weaken V1 invariants.

## Exit criterion

Stage 3 is complete only when the Master Project Schema, OpenAPI, PostgreSQL schema, state machine, event model, security model, conformance vectors, and reference implementation describe the same financial lifecycle without material contradiction.
