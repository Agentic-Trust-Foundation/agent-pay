# Agent-Pay API V1 Contract

## Status

Draft V1 contract. This document defines the initial resource and operation boundary; it is not yet a production payment specification.

## Design Principles

- Payment APIs are intent-oriented.
- Agents submit payment intent; they do not select or receive raw financial credentials.
- Financial operations require idempotency.
- Authorization and spending controls are evaluated server-side.
- Payment state is separate from transaction/ledger state.
- Provider-specific details remain behind adapters.

## Primary Operations

```text
POST /v1/agents
POST /v1/delegations
POST /v1/wallets
POST /v1/wallets/{walletId}/fund
POST /v1/policies
POST /v1/payments

GET  /v1/payments/{paymentId}
POST /v1/approvals/{approvalId}/approve
POST /v1/approvals/{approvalId}/deny
GET  /v1/transactions/{transactionId}
```

## Payment Intent

The primary financial operation is:

```http
POST /v1/payments
Idempotency-Key: req_abc123
```

The request identifies:

- Agent
- Account
- Merchant
- Amount
- Currency
- Purpose
- Optional line items
- Optional preferred instrument

The response represents the state of the payment request. It does not imply that money has already moved.

Example:

```json
{
  "id": "pay_123",
  "status": "APPROVAL_REQUIRED",
  "agent_id": "agt_123",
  "account_id": "acc_123",
  "amount": "850.00",
  "currency": "USD",
  "approval_id": "apr_123"
}
```

## Idempotency

Every operation that can create or change financial state must support an idempotency key.

For a repeated request with the same key and equivalent request payload, the server should return the original operation result rather than create a second financial effect.

Reusing an idempotency key with materially different request data must result in a conflict.

## Authorization Sequence

A payment request should be processed in this logical order:

```text
Authenticate
    ↓
Verify Agent
    ↓
Verify Delegation
    ↓
Evaluate Policy
    ↓
Evaluate Budget
    ↓
Evaluate Risk
    ↓
Evaluate Approval Requirement
    ↓
Route Payment
    ↓
Execute Payment
    ↓
Create Transaction
    ↓
Post Ledger Effects
    ↓
Emit Audit / Notification Events
```

## API vs Financial Truth

The API response is not the ledger. A successful HTTP response means that the requested operation was accepted according to the endpoint contract; final financial state is represented by Payment, Transaction, and Ledger records.

## Error Model

Errors should be stable, machine-readable, and include a correlation ID where possible.

Example:

```json
{
  "code": "BUDGET_EXCEEDED",
  "message": "Payment exceeds the available budget.",
  "correlation_id": "corr_123"
}
```

Initial error categories should include:

- `INVALID_REQUEST`
- `AUTHENTICATION_REQUIRED`
- `DELEGATION_INVALID`
- `POLICY_DENIED`
- `BUDGET_EXCEEDED`
- `APPROVAL_REQUIRED`
- `PAYMENT_NOT_ALLOWED`
- `INSUFFICIENT_FUNDS`
- `PAYMENT_PROVIDER_ERROR`
- `DUPLICATE_REQUEST`
- `STATE_CONFLICT`

## Versioning

V1 uses the `/v1` URL prefix. Breaking changes require a new API version. Additive changes should remain backward compatible wherever practical.

The normative machine-readable API contract is maintained in `specs/v1/openapi.yaml`.
