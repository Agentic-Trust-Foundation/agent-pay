# Agent-Pay Payment Authentication

## Purpose

Payment authentication is the step required by a payment rail, issuer, provider, or Agent-Pay risk control before a payment can be completed.

It is distinct from:

- agent authentication
- user authentication to Agent-Pay
- authorization/delegation
- policy evaluation
- approval

## Principle

Authentication must be represented explicitly in the financial lifecycle. A provider challenge is not a payment failure.

```text
PAYMENT_PENDING
      ↓
AUTHENTICATION_REQUIRED
      ↓
AUTHENTICATED
      ↓
PROCESSING
```

## Examples

Future payment instruments may require:

- 3-D Secure challenge
- issuer authentication
- step-up user authentication
- provider-specific customer action
- risk-based authentication

Agent-Pay should expose a provider-neutral abstraction while preserving the provider's challenge/reference data needed to complete the flow.

## Security Boundary

Agents must not receive primary card, bank, or authentication credentials.

An agent may receive a safe action result such as:

```text
authentication_required
challenge_reference
next_action
status
```

The user-facing authentication step should occur through a trusted Agent-Pay or provider-controlled channel.

## Binding

Authentication must bind to the exact payment operation, including where applicable:

- payment ID
- amount
- currency
- merchant/provider reference
- account
- instrument reference
- authentication transaction reference

A challenge for one payment must not be reusable for another payment.

## State and Retry

Authentication completion requests must be idempotent.

Repeated callbacks or user submissions must not trigger duplicate payment execution.

Expired or cancelled challenges must fail closed.

## Audit

Record authentication lifecycle events without storing secrets:

```text
AuthenticationRequired
AuthenticationStarted
AuthenticationCompleted
AuthenticationFailed
AuthenticationExpired
```

Store references and outcomes, not passwords, OTP values, CVV, private keys, or equivalent secrets.

## Provider Webhooks

Authentication results may arrive asynchronously. Provider webhook verification, deduplication, ordering protection, and replay handling follow the payment-events-and-webhooks architecture.

## V1 Boundary

V1 does not implement a specific 3-D Secure provider. It defines the domain state and integration boundary so future instruments can add provider-specific authentication without changing the Agent-Pay financial model.
