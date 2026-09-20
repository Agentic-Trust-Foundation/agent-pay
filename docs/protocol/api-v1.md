# Agent-Pay API V1 Contract

## Status

**Normative V1 machine-readable contract:** `specs/v1/openapi.yaml`.

This document explains the contract; it does not override the OpenAPI file.

## Primary Operations

```text
POST /v1/payments
GET  /v1/payments/{paymentId}
POST /v1/approvals/{approvalId}/approve
POST /v1/approvals/{approvalId}/deny
POST /v1/payments/{paymentId}/capture
POST /v1/payments/{paymentId}/void
POST /v1/payments/{paymentId}/refund
POST /v1/providers/{providerName}/webhooks
POST /v1/providers/{providerName}/settlements
```

## Required payment controls

A payment request requires:

1. authenticated Agent-Pay caller;
2. server-side binding of the authenticated principal to `agent_id` and `account_id`;
3. cryptographically verified ATF authorization evidence;
4. explicit `PAYMENT` authority, amount and currency bounds, validity and revocation status;
5. Agent-Pay spending policy;
6. budget reservation;
7. human approval where policy requires it;
8. provider idempotency and explicit ambiguous-outcome handling;
9. transaction/ledger integrity and audit/outbox effects.

Authentication alone is never financial authority.

## Idempotency

Financially mutating operations use idempotency boundaries appropriate to the operation: API request, provider operation, transaction/ledger posting, approval decision, and provider event/settlement ingestion.

Reusing an API idempotency key with materially different intent is a conflict.

## Error model

HTTP errors use `application/problem+json` semantics. Implementations may add stable Agent-Pay error codes and correlation identifiers.

## Versioning

V1 is exposed under `/v1`. Breaking API changes require a new major protocol/API version. Additive changes must remain backward compatible where practical.