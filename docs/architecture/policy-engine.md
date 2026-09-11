# Agent-Pay Policy Engine

## Purpose

The Policy Engine determines whether a Payment Request is financially permitted under the policies attached to an Account, Agent, delegation, or spending context.

> **Policy answers: may this payment happen?**

The Policy Engine does not own money, mutate the ledger, reserve wallet funds, execute payment rails, or replace Agentic Trust Foundation authorization.

## Boundary

```text
Agent
  |
  v
Authorization Evidence / Delegation
  |
  v
Payment Request
  |
  v
Policy Engine
  |
  +--> ALLOW_AUTO
  +--> ALLOW_NOTIFY
  +--> REQUIRE_APPROVAL
  +--> DENY
  |
  v
Budget Engine
```

ATF establishes identity, delegation, authorization, trust, and related evidence. Agent-Pay consumes the resulting authorization context and applies financial spending policy.

## Inputs

A policy evaluation should receive a normalized, immutable evaluation context containing at least:

- account identifier
- agent identifier
- delegation/authorization evidence reference
- payment request identifier
- amount and currency
- merchant identity/reference
- merchant category when available
- requested payment instrument class
- request timestamp
- frequency/context counters when available
- applicable budget references
- risk/authentication signals when available
- location only when legitimately supplied and policy-relevant

The evaluator must not fetch mutable external state halfway through a decision without recording the versioned inputs used for the decision.

## Decision Model

```text
ALLOW_AUTO
ALLOW_NOTIFY
REQUIRE_APPROVAL
DENY
```

`ALLOW_NOTIFY` means the payment may proceed while a user notification is generated. It is not equivalent to explicit approval.

`REQUIRE_APPROVAL` pauses financial execution until the required approval is obtained.

`DENY` is terminal for that Payment Request unless a new request or explicitly supported policy re-evaluation is created.

## Evaluation Order

The conceptual order is:

```text
1. Validate request
2. Validate authorization evidence / delegation context
3. Resolve applicable policies
4. Evaluate explicit deny rules
5. Evaluate allow rules and constraints
6. Determine approval mode
7. Produce deterministic decision + trace
8. Pass the result to Budget evaluation
```

Authorization failure is not a policy approval. Missing, expired, revoked, malformed, or unverifiable authority must fail closed.

## Rule Dimensions

V1 policy rules may cover:

- per-transaction amount
- daily/weekly/monthly amount
- merchant/domain
- merchant category
- currency
- time/day-of-week
- frequency/count
- location when available
- payment instrument class
- approval thresholds
- explicit allowlists
- explicit denylists

The model must permit additional dimensions without changing the core decision contract.

## Precedence

Explicit deny rules have precedence over allow rules at the same policy scope.

More restrictive applicable constraints must not be weakened by a broader allow rule.

A suggested precedence model is:

```text
Revoked / invalid authority
        ↓
Explicit DENY
        ↓
Hard limits / mandatory constraints
        ↓
Specific allow rules
        ↓
General allow rules
        ↓
Default decision
```

The exact policy-composition algorithm is versioned and must be deterministic.

## Policy Composition

Policies may be attached at different scopes, for example:

```text
Account
  ↓
Agent
  ↓
Delegation
  ↓
Payment context
```

Composition must be monotonic with respect to restriction: a narrower scope may restrict authority, but must not silently expand authority beyond the effective delegation.

The evaluator should calculate an effective policy snapshot rather than repeatedly evaluating mutable policy records during execution.

## Versioning

Every decision must identify:

- policy identifier(s)
- policy version(s)
- evaluation timestamp
- evaluation context/reference
- decision
- reason codes
- decision trace/reference

Policy changes must not rewrite historical decisions. A later payment investigation must be able to reconstruct which policy version was used.

## Decision Trace

The engine should produce a machine-readable trace suitable for audit and debugging without exposing unnecessary sensitive data.

Example:

```json
{
  "decision": "REQUIRE_APPROVAL",
  "policy_version": "pol_123:v7",
  "reasons": [
    "AMOUNT_EXCEEDS_AUTO_APPROVAL_LIMIT"
  ],
  "evaluated_rules": [
    "amount.auto <= 100",
    "amount.approval > 100"
  ]
}
```

The trace is explanatory evidence; it is not itself authorization.

## Policy vs Budget vs Wallet

These are intentionally separate:

```text
Policy = Is this spending permitted?
Budget = Is enough allocated spending capacity available?
Wallet = Is enough actual money available?
```

A policy `ALLOW_AUTO` result does not imply budget availability or sufficient funds.

## Approval Interaction

The policy engine determines whether approval is required. It does not itself perform the approval workflow.

```text
Policy
  |
  +--> AUTO ---------> Budget -> Funds -> Execute
  |
  +--> NOTIFY --------> Budget -> Funds -> Execute + Notify
  |
  +--> APPROVAL ------> Budget Reservation -> Approval Engine
  |
  +--> DENY ----------> Stop
```

For approval-required payments, budget reservation may occur before user approval to prevent concurrent requests from consuming the same capacity.

## Fail-Closed Requirements

The evaluator must fail closed when:

- authorization evidence cannot be verified
- required policy data is unavailable
- policy version is invalid
- required constraint data is malformed
- currency rules cannot be evaluated safely
- policy composition is ambiguous

No infrastructure error may accidentally become an `ALLOW_AUTO` decision.

## Determinism and Idempotency

Given the same policy snapshot and evaluation context, the evaluator should return the same decision.

A Payment Request may be evaluated more than once during retries or recovery. Re-evaluation must be explicitly identified and must not create duplicate financial side effects.

## Non-Responsibilities

The Policy Engine does not:

- authenticate users
- establish general agent identity
- mint financial credentials
- own wallet balances
- write ledger entries
- call external payment providers
- settle transactions
- perform general merchant trust/reputation

## V1 Direction

V1 should implement a deterministic policy evaluator inside the modular monolith, backed by PostgreSQL policy versions and JSONB rule definitions where appropriate. A future standalone policy service can reuse the same decision contract.
