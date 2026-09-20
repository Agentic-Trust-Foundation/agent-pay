# AGENTS.md

## Repository mission

Agent-Pay is the financial control and payment execution layer for the agentic internet. It consumes delegated authority and authorization context and applies financial policy, budgets, approvals, authentication, payment routing, transaction handling, settlement, reconciliation, and ledgering.

## Working rules

- Read the README and relevant architecture/specification documents before changing behavior.
- Treat financial state transitions and ledger invariants as contracts.
- Preserve separation between authorization, payment execution, and accounting truth.
- Use explicit idempotency for externally repeatable operations.
- Treat unknown external payment outcomes as distinct from failure.
- Never make Redis or an operational cache the financial source of truth.
- Keep provider calls outside database transactions when the architecture requires it.
- Add tests/conformance vectors for externally observable lifecycle behavior.
- Never commit credentials, payment secrets, private keys, or generated tokens.
- Do not represent local reference adapters as production payment rails.

## Change discipline

For lifecycle or schema changes, update migrations, domain behavior, tests, documentation, and conformance artifacts together. Record backward-compatibility and accounting implications.
