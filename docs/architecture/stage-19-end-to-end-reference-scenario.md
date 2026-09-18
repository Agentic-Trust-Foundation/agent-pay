# Stage 19 — End-to-End Reference Scenario

## Purpose

Stage 19 defines one canonical V1 path from upstream Agentic Trust Foundation (ATF)
authorization evidence to a financially controlled payment and external settlement.

The scenario is provider-neutral and does not freeze a universal ATF token or signature format.

## Canonical flow

    Agent
      |
      | payment intent + ATF evidence reference
      v
    ATF
      |
      | normalized authorization context
      v
    Agent-Pay
      |
      +--> validate authority (fail closed)
      +--> evaluate spending policy
      +--> require/record approval when policy says so
      +--> reserve budget
      +--> execute provider operation
      +--> finalize payment / transaction / ledger / audit
      +--> async notification via outbox
      v
    Provider settlement assertion
      |
      +--> MATCHED
      +--> DISCREPANCY (observational)

## Scenario inputs

- account: acct-demo
- agent: agent-demo
- authorization evidence: atf-evidence-001
- scope: PAYMENT
- maximum authorized amount: 100.00 USD
- requested amount: 75.00 USD
- merchant: example.com
- policy version: policy-v1
- budget: budget-demo
- human approval: required above 50.00 USD
- payment provider: reference/simulator provider

The example uses illustrative identifiers only.

## Required decision sequence

1. ATF authority exists and is represented by a normalized authorization context.
2. Agent-Pay validates authority and fails closed on missing, expired, mismatched, or insufficient authority.
3. Spending policy is evaluated. Policy cannot create authority.
4. Approval is evaluated. Approval cannot expand ATF authority and is bound to the exact intent.
5. Budget is reserved before external execution.
6. Provider execution occurs outside the database transaction.
7. Success consumes the reservation and records balanced financial effects.
8. Failure releases the reservation.
9. Ambiguous external outcome remains UNKNOWN_EXTERNAL_OUTCOME until resolved.
10. Audit and outbox effects accompany the financial state transition.
11. Settlement is reconciled separately from payment execution.
12. Settlement discrepancies are recorded for investigation and do not silently rewrite financial truth.

## Security invariants

- The agent never receives raw payment credentials.
- ATF evidence is referenced and validated; Agent-Pay does not mint general authorization.
- Policy decisions are reconstructable from a policy version and evaluation evidence.
- Approval is cryptographically bound to the exact payment intent.
- Provider credentials and secrets remain inside the provider boundary.
- Financial truth is recorded in the ledger.
- Provider timeouts are not silently converted into failures.
- Settlement is an external assertion, not a replacement for the transaction record.

## Machine-readable trace

See examples/v1/end-to-end-agent-payment.yaml. The trace is a reference scenario,
not a universal wire format.

## V1 boundary

This scenario does not require a live bank or PSP, a production card issuer,
a universal ATF cryptographic token format, an Agent-Pay merchant/order system
of record, or automatic chargeback/dispute handling.
