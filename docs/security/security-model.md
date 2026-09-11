# Agent-Pay Security Model

## Security Objective

Agent-Pay must allow an AI agent to initiate financial actions without giving the agent unrestricted access to the user's money or primary financial credentials.

## Security Boundary

```text
Agent
  |
  | identity + delegation evidence
  v
Agent-Pay API
  |
  +--> Authentication
  +--> Delegation verification
  +--> Policy evaluation
  +--> Budget controls
  +--> Approval controls
  +--> Risk controls
  |
  v
Payment Router
  |
  v
Payment Instrument / Rail
```

The Agent is an untrusted execution actor from the perspective of financial authority. Authorization must be evaluated server-side for every payment request.

## Core Security Principles

1. **No primary credentials to Agents.** Agent-Pay must not expose bank credentials, primary card credentials, or equivalent secrets to an Agent.
2. **Least privilege.** Delegations and spending policies must grant only the authority required for the task.
3. **Explicit financial authorization.** A valid Agent identity alone is never sufficient to spend funds.
4. **Server-side enforcement.** Policies, budgets, approval requirements, and instrument eligibility are enforced by Agent-Pay, not by Agent code.
5. **Immutable audit intent.** Security and financial decisions must produce auditable events.
6. **Idempotency.** Financial execution APIs must protect against duplicate requests and retries.
7. **Fail closed.** Missing, invalid, expired, or ambiguous authorization context must result in denial or an approval-required state rather than implicit authorization.
8. **Secret isolation.** Provider credentials and payment instrument secrets belong to protected adapters/services and are never included in normal Agent API responses.

## Authorization Context

A payment decision should be explainable through a chain such as:

```text
Account
  -> Agent
  -> Delegation
  -> Policy
  -> Budget
  -> Approval (if required)
  -> Payment
  -> Transaction
```

External trust and delegation evidence may be supplied by Agentic Trust Foundation. Agent-Pay validates the evidence relevant to the financial action and applies its own financial controls.

## API Security

V1 APIs should support:

- authenticated Agent requests
- scoped credentials or tokens
- request correlation IDs
- idempotency keys for financial operations
- strict request validation
- replay protection where applicable
- rate limiting
- structured authorization failures
- secure transport only

## Sensitive Data

The system should minimize storage of payment secrets and personally sensitive information.

Examples of data that must receive stronger protection:

- payment credentials
- provider access tokens
- virtual card data
- bank account credentials
- approval authentication factors
- personally identifiable information

Where possible, Agent-Pay should store provider references or tokenized representations rather than raw financial credentials.

## Approval Security

Approval actions must be bound to the exact payment intent being approved.

An approval should include or reference:

- payment request ID
- amount
- currency
- merchant
- purpose/context
- expiry
- approving principal
- approval timestamp

A stale or materially modified payment request must not reuse an earlier approval.

## Ledger Security

The ledger is financial source of truth. Normal application operations must not overwrite historical financial entries.

Corrections should use explicit compensating entries such as:

```text
DEBIT -> CREDIT adjustment
HOLD -> RELEASE
PAYMENT -> REFUND
```

Every correction must be auditable.

## Threats to Address

V1 threat modeling should explicitly consider:

- compromised or malicious Agent
- stolen Agent credentials
- replayed payment requests
- duplicate payment submission
- policy bypass
- budget race conditions
- approval replay
- privilege escalation through delegation
- merchant manipulation
- payment provider failure or timeout
- webhook spoofing
- secret leakage
- unauthorized administrative actions
- ledger tampering

## Race Conditions

Financial checks and state transitions must be atomic where required. In particular, concurrent payment requests must not be able to spend the same available budget or wallet balance twice.

Database transactions, row-level locking, reservation/hold semantics, and idempotency records should be used where appropriate.

## Trust Boundary with Agentic Trust Foundation

Agent-Pay should consume trust/delegation evidence rather than implement a second general-purpose identity or trust network.

```text
Agentic Trust Foundation
  Identity / Delegation / Authorization / Trust
                    |
                    v
                Agent-Pay
          Financial Authorization
          Policy / Budget / Approval
                    |
                    v
                 Payment
```

This boundary prevents the financial system from becoming a replacement for general agent identity and trust infrastructure.
