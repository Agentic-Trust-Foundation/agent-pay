# Contributing

Thank you for contributing to Agent-Pay.

## Before opening a PR

- Read the repository README and relevant architecture/specification documents.
- Keep changes scoped to one coherent problem.
- Add or update tests, schemas, conformance vectors, or documentation when behavior changes.
- Never commit credentials, payment secrets, private keys, tokens, or personal data.
- Treat financial state and ledger behavior as security- and correctness-sensitive.

## Pull requests

Describe what changed, why, how it was tested, and any compatibility, migration, accounting, or security impact.

Changes affecting payment lifecycle, policy, budgets, reservations, authentication, provider operations, settlement, reconciliation, or ledgering should include corresponding tests and documentation.

## Design principles

Preserve explicit delegated authority, least privilege, fail-closed controls, idempotency, auditable state transitions, separation of authorization from execution, and financial-source-of-truth boundaries.

Agent-Pay is a reference platform, not a production payment processor. Do not describe simulated or local integrations as live financial infrastructure.

## Security

Do not disclose vulnerabilities in public issues. Follow `SECURITY.md`.
