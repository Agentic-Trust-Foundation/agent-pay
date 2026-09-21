# Repository Governance

## Purpose

Agent-Pay is maintained as an open, vendor-neutral, protocol-first project with a reference implementation. Repository governance exists to protect interoperability, financial correctness, security, and transparent evolution.

## Authority and boundaries

- **Agentic Trust Foundation (ATF)** owns the upstream identity, delegation, authorization, trust, consent, revocation, provenance, and authority-evidence concepts.
- **Agent-Pay** consumes verified authority context and applies financial policy, budgets, approval, payment execution, settlement, reconciliation, and ledger controls.
- Agent-Pay must never expand upstream authority.
- V1 protocol semantics are frozen unless a documented regression, security defect, violated invariant, or intentional contract change requires reopening them.
- V2 work is non-normative until its semantic behavior, security invariants, negative vectors, and interoperability requirements satisfy the V2 gates.

## Artifact classes

| Class | Meaning | Review expectation |
| --- | --- | --- |
| Normative protocol | Contract that independent implementations must follow | Maintainer review + conformance impact |
| Conformance artifact | Observable behavior/vector used to establish interoperability | Test/vector review |
| Reference implementation | Executable example of the protocol | Tests + security/invariant review |
| Architecture/design | Project design rationale or boundary | Architecture review |
| Deployment/provider profile | Environment or provider-specific integration | Deployment/security review |
| Documentation | Clarification with no semantic change | Documentation review |
| Governance | Rules for project evolution | Maintainer review |

A document must not become normative merely because it exists in the repository. Normative status must be stated explicitly.

## Change classes

Every PR should identify one primary change class:

1. Documentation clarification
2. Implementation hardening
3. Provider/deployment profile
4. Optional extension/profile
5. V2 semantic change

V1 semantic changes require explicit justification and must not be smuggled in as documentation or implementation cleanup.

## Review ownership

CODEOWNERS establishes repository-wide maintainer review ownership. Security-sensitive and financial-state changes should receive maintainer review even when they are otherwise small.

## Main branch policy

The intended main baseline is:

- pull requests required for changes;
- required CI checks must pass before merge;
- no force-pushes or deletion of main;
- direct pushes disabled for ordinary development;
- squash merge preferred to keep one coherent change record;
- stale approvals invalidated when relevant code changes;
- conversation resolution required;
- security-sensitive changes require explicit maintainer review;
- releases and normative protocol changes require documented evidence.

The connected GitHub integration can inspect repository rulesets but does not expose administration writes for this repository. Therefore these settings are documented here as the governance target and must be enforced in GitHub repository settings/rulesets when administrative access is available.

## Security reporting

Do not use public issues for undisclosed vulnerabilities. Follow SECURITY.md.

## Release discipline

A release or normative protocol version must identify:

- exact source commit/tag;
- conformance status;
- compatibility statement;
- security review status;
- migration/database implications where applicable;
- known deployment/provider boundaries.

No release note may imply live banking, PSP, issuer, regulatory, or compliance support that the repository does not actually provide.
