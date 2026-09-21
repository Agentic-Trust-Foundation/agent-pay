# Change Control

## V1 frozen boundary

Agent-Pay V1 is frozen on main. The default assumption for future work is that V1 behavior remains unchanged.

Do not reopen a full V1 review unless at least one of these is true:

- a regression is demonstrated;
- a security defect is found;
- a financial invariant is violated;
- conformance behavior changes intentionally;
- the V1 contract itself is intentionally versioned.

## Decision matrix

| Proposed change | Default path | V1 contract impact |
| --- | --- | --- |
| Typo/clarification | Documentation PR | None |
| Additional regression test | Test/hardening PR | None |
| Runtime hardening preserving behavior | Hardening PR | None |
| Provider-specific adapter | Provider profile | None |
| Optional V2 capability | Extension/profile | Must be isolated |
| New normative semantics | V2 design + conformance | Explicit version change |

## Required evidence

Changes touching any of the following must include the corresponding evidence:

- payment lifecycle → lifecycle tests and idempotency behavior;
- policy → negative/boundary vectors and deterministic evaluation;
- authorization → authority-binding and fail-closed tests;
- provider operations/webhooks → idempotency, authentication, and ambiguous-outcome handling;
- ledger/accounting → persistence and accounting invariants;
- API/schema → contract and compatibility review;
- security controls → threat/risk rationale and regression coverage.

## Normative V2 gate

A V2 feature is not normative merely because the reference implementation supports it.

Before a V2 feature becomes normative, the repository must have:

1. defined semantic behavior;
2. documented security invariants;
3. negative/conformance vectors;
4. compatibility/versioning rules;
5. at least two interoperable implementations, as required by the V2 roadmap.

## PR classification

PR authors should state:

- **Change class:** one of the five classes in repository-governance.md;
- **Contract impact:** none / V1 hardening / V2 extension / V2 semantic;
- **Security impact:** none / reviewed;
- **Conformance impact:** none / vectors changed;
- **Migration impact:** none / described;
- **Operational impact:** none / described.

## Revert principle

If a change introduces a regression in a financial invariant, security boundary, or conformance contract, restoring the last known-good behavior takes precedence over preserving the new implementation. Follow-up redesign can occur in a separate, explicitly classified change.
