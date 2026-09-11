# Tokenization and Credential Boundary

## Purpose

Agent-Pay must prevent agents and the core payment decision engine from handling primary payment credentials unnecessarily.

## Rule

> Agents receive payment authority, not payment credentials.

The preferred architecture is:

```text
Agent
  |
  | Payment Intent
  v
Agent-Pay Core
  |
  | instrument reference / token
  v
Credential / Token Boundary
  |
  v
Payment Provider / Rail
```

## Sensitive data

Depending on the payment instrument, sensitive data may include:

- card PAN
- security code
- bank credentials
- provider secrets
- private cryptographic keys
- authentication secrets

These must not appear in agent-facing API responses, logs, audit records, traces, or ordinary domain objects unless strictly required.

## Tokenization

A payment instrument should normally be represented inside Agent-Pay using a non-sensitive reference:

```text
instrument_id
provider_reference
token_reference
instrument_type
status
```

The exact tokenization mechanism belongs to the payment-provider adapter or a dedicated secure credential boundary.

## Logging

Sensitive payment credentials must never be logged. Structured logs should use identifiers, hashes, redacted values, or opaque references as appropriate.

## PCI boundary

If a future implementation handles cardholder data directly, PCI DSS scope must be assessed explicitly. A hosted/tokenized provider integration may reduce the data-handling surface, but does not automatically eliminate all compliance obligations.

## V1 boundary

The V1 wallet implementation does not require storage of card PAN/CVV or bank passwords. The domain model remains instrument-agnostic and ready for tokenized virtual-card adapters later.
