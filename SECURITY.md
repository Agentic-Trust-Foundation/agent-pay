# Security Policy

## Scope

This policy covers Agent-Pay's reference implementation, protocol artifacts, payment lifecycle, policy controls, provider adapters, ledgering, and related tooling.

## Reporting a vulnerability

Do not open a public issue for an undisclosed vulnerability. Use GitHub's private vulnerability reporting/security advisory mechanism when available, or contact the maintainers through the private security contact configured for this project.

Include the affected component/version or commit, reproduction steps, security impact, and sanitized evidence. Never include credentials, payment secrets, private keys, or unnecessary personal data.

## Security-sensitive areas

Treat delegated authority, policy evaluation, budget reservations, approval, authentication, idempotency, provider operation state, external outcome uncertainty, settlement, reconciliation, ledger posting, and audit records as security- and correctness-sensitive.

The repository is a validated reference platform, not a production payment processor. Production use requires provider/issuer integrations, deployment-specific threat modeling, regulatory and compliance controls, key management, monitoring, and operational readiness.
