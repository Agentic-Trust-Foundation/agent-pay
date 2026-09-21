# Contributing

Thank you for contributing to Agent-Pay.

## Before opening a PR

- Read the repository README and relevant architecture/specification documents.
- Read docs/governance/repository-governance.md and docs/governance/change-control.md.
- Keep changes scoped to one coherent problem.
- Classify the change as documentation clarification, implementation hardening, provider/deployment profile, optional extension/profile, or V2 semantic change.
- Add or update tests, schemas, conformance vectors, or documentation when behavior changes.
- Never commit credentials, payment secrets, private keys, tokens, or personal data.
- Treat financial state and ledger behavior as security- and correctness-sensitive.

## Pull requests

Use the repository PR template. Describe what changed, why, how it was tested, and any compatibility, migration, accounting, security, or conformance impact.

Changes affecting payment lifecycle, policy, budgets, reservations, authentication, provider operations, settlement, reconciliation, or ledgering should include corresponding tests and documentation.

V1 is frozen by default. V2 semantic changes must be explicitly identified and must not be presented as V1-compatible hardening.

## Design principles

Preserve explicit delegated authority, least privilege, fail-closed controls, idempotency, auditable state transitions, separation of authorization from execution, and financial-source-of-truth boundaries.

Agent-Pay is a reference platform, not a production payment processor. Do not describe simulated or local integrations as live financial infrastructure.

## Security

Do not disclose vulnerabilities in public issues. Follow SECURITY.md.
