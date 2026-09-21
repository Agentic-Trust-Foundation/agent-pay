# Governance

Agent-Pay evolves as an open, vendor-neutral protocol and reference implementation.

## Governance goals

- Interoperability
- Backward compatibility
- Transparent versioning
- Security review
- Conformance-based claims
- Separation between protocol and hosted services
- No single-vendor dependency
- Explicit separation between frozen V1 semantics and V2 evolution

## Documents

- Repository Governance (repository-governance.md) — ownership, artifact classes, review expectations, and main-branch policy.
- Change Control (change-control.md) — V1 frozen boundary, change classification, required evidence, and V2 normative gates.

## Core rule

A repository artifact is not normative merely because it exists. Normative behavior must be explicitly versioned and backed by semantic definitions, security invariants, conformance evidence, compatibility rules, and the applicable interoperability gate.

## GitHub enforcement

The intended GitHub branch-governance baseline is documented in repository-governance.md. The connected GitHub integration can inspect rulesets but cannot administer repository rulesets for this repository, so enforcement settings remain an administrative GitHub task rather than an implicit repository claim.
