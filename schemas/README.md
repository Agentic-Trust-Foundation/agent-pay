# Schemas

This directory contains machine-readable protocol/domain schemas that must remain aligned with `specs/v1/openapi.yaml`, the Master Project Schema, and conformance vectors.

## V1 schema families

- Payment Intent
- Payment State / Decision
- Spending Policy / Policy Version
- Budget Reservation
- Authorization Evidence
- Approval
- Payment Authentication
- Provider Operation
- Transaction
- Settlement / Reconciliation
- Domain Event / Provider Event
- Problem Details

## Rules

1. Schemas are versioned explicitly.
2. Schemas describe protocol/domain contracts, not database implementation details.
3. Financial amounts use decimal strings and explicit ISO-style currency codes.
4. Provider credentials and authentication secrets are never represented as agent-facing schema fields.
5. Changes must be checked against the Master Project Schema and conformance vectors.
