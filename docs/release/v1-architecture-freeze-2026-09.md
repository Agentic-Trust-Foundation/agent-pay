# Agent-Pay V1 Architecture Freeze

Status: FROZEN  
Freeze date: 2026-09  
Pre-freeze baseline: 6c2507fd90e100d383aeea66ec690ee83b33c7d2

## Purpose

This document freezes the Agent-Pay V1 architecture, ownership boundaries,
financial invariants, reference behavior, and conformance surface. New work after
this point is treated as V2/production evolution unless it is a compatibility,
security, correctness, or documentation fix.

## Frozen V1 architecture

The reference architecture is:

    Agent
      |
      v
    ATF authorization evidence
      |
      v
    Agent-Pay normalized authorization
      |
      v
    Policy -> Budget -> Approval
      |
      v
    Payment -> Provider Operation
      |
      +--> Transaction
      +--> Ledger
      +--> Audit
      +--> Outbox / Notification
      |
      v
    Settlement / Reconciliation

Core implementation choices:

- PostgreSQL is the financial source of truth.
- The reference implementation is a modular monolith.
- Provider calls occur outside database transactions.
- Transactional outbox is used for durable asynchronous effects.
- Redis is not financial truth.
- Ambiguous provider outcomes remain UNKNOWN_EXTERNAL_OUTCOME.
- Payment, transaction, and settlement are distinct concepts.
- Approval cannot expand upstream authority.
- Policy cannot create upstream authority.
- Agents do not receive raw primary payment credentials.

## Frozen V1 responsibility boundary

ATF owns identity, delegation, authorization, capability, trust, consent,
provenance, revocation, and related interoperability concerns.

Agent-Pay owns spending policy, budgets, financial approval, payment instruments,
payment execution, transaction lifecycle, settlement/reconciliation, ledger,
audit, notifications, and financial control.

Agent-Pay does not become a general authorization system.

## Frozen V1 lifecycle

1. Receive normalized authority.
2. Validate authority.
3. Evaluate spending policy.
4. Reserve budget.
5. Require and validate approval when policy requires it.
6. Execute provider operation.
7. Finalize success/failure/ambiguous outcome.
8. Record transaction and balanced ledger effects.
9. Emit durable audit/outbox effects.
10. Reconcile external settlement separately.

## Frozen V1 conformance surface

The following are part of the V1 compatibility surface:

- conformance/v1/payment-control-vectors.yaml
- conformance/v1/atf-agent-pay-contract-vectors.yaml
- examples/v1/end-to-end-agent-payment.yaml
- ATF-Agent-Pay cross-repository vector agreement
- policy and authorization fail-closed behavior
- approval exact-intent binding
- budget reservation invariants
- provider idempotency and ambiguous-outcome handling
- balanced ledger behavior
- outbox atomicity/retry behavior
- audit and notification integrity
- settlement discrepancy semantics
- credential redaction boundaries

## V1 explicitly excludes

- live bank/PSP production integration
- production card issuing
- universal ATF cryptographic token/signature format
- Kafka or mandatory distributed microservices
- automatic chargeback/dispute lifecycle
- Agent-Pay as the merchant/order system of record
- universal fraud/risk scoring
- legal/regulatory certification
- mandatory cloud deployment topology

These are not accidental gaps; they are explicit V1 boundaries.

## Change-control rule

After the freeze:

- compatibility, security, correctness, and documentation fixes may land without
  changing the V1 contract;
- a change to a frozen invariant, schema contract, protocol surface, state machine,
  ownership boundary, or conformance vector requires a new version decision;
- additive V2 work must not silently change V1 semantics;
- V2/production work should be documented separately rather than modifying this
  freeze document retroactively.

## Validation evidence

Immediately before this freeze, the Batch 4 head passed:

- Agent-Pay Validation: run 35405712899
- Agent-Pay Conformance: run 35405712924
- Agent-Pay Docker Clean Start: run 35405712921

The cross-repository conformance check fetched the ATF vector file from the public
ATF main branch and passed.

The freeze commit itself must also pass all repository CI before being treated as
the operational V1 baseline.

## Definition of frozen

V1 is frozen when the freeze document is present on main and the resulting commit
has successful Validation, Conformance, and Docker Clean Start workflows.

No production readiness claim is implied by this architecture freeze.
