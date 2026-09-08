# Project Boundaries

## Agentic Trust Foundation

Owns authority and trust concerns: identity, credentials, delegation, authorization, capability, trust, consent, revocation, provenance, and auditability.

## Agent-Pay

Owns financial execution concerns: funding, wallets, payment instruments, payment intent, spending policy, risk, approval, routing, processing, transaction lifecycle, settlement, refunds, and financial ledgering.

## Boundary

```text
Trust Foundation
    |
    | authorization/delegation decision + evidence
    v
Agent-Pay
    |
    | financial decision + execution
    v
Payment Rail
```

Neither project should silently absorb the other's core responsibilities.
