# Phase 16 — Multidimensional Policy Evaluation

Phase 16 introduces the first V2 policy-engine extension while preserving the existing four-value decision contract:

- ALLOW_AUTO
- ALLOW_NOTIFY
- REQUIRE_APPROVAL
- DENY

## Evaluation context

PaymentIntent now optionally carries merchant category, region, payment instrument class, and request timestamp. Existing callers remain valid because these fields are optional.

## Policy dimensions

The reference evaluator supports amount and currency, merchant domain, merchant category, region, payment instrument class, allowed weekdays, and start/end time windows.

Dimensions are normalized before comparison. Domains, categories, and instrument classes are case-insensitive; regions and currencies are normalized to uppercase.

## Precedence and fail-closed behavior

Any deny or unmet allow constraint produces DENY before approval/notification thresholds are considered.

A time-dependent rule without a request timestamp produces DENY with REQUEST_TIME_REQUIRED.

Malformed schedule configuration raises a configuration error rather than silently producing an allow decision.

Cross-midnight windows such as 22:00 → 02:00 are treated as a single deterministic window spanning midnight.

## Snapshot boundary

The evaluator remains a pure function of the supplied policy object and immutable payment context. It does not fetch merchant, geo, clock, or provider state during evaluation.

The caller is responsible for constructing the versioned policy snapshot and context. A production integration must record the policy version and evaluation timestamp with the resulting decision evidence.

## V2 status

This is an implementation/reference extension, not a new normative protocol requirement. The V2 gate remains: semantic behavior, security invariants, negative vectors, and interoperable implementations must be established before standardization.
