# Agentic Trust Foundation → Agent-Pay Authorization Evidence

Agent-Pay does not become a second identity or trust network. The Agentic Trust Foundation (ATF) may establish agent identity, delegation, authorization, trust, consent, and revocation. Agent-Pay consumes the resulting evidence as input to a financial decision.

## Required financial binding

Authorization evidence presented to Agent-Pay must be bound to:

- authenticated agent identity
- account/user context
- intended operation or transaction class
- permitted scope and constraints
- issuer
- issued-at / expiry
- revocation status or a verifiable revocation reference
- evidence identifier and digest

## Evidence lifecycle

```text
ATF authorization/delegation
        ↓
verifiable evidence
        ↓
Agent-Pay authentication
        ↓
financial authorization context
        ↓
policy + budget + approval
        ↓
payment
```

Identity or delegation evidence alone never grants spending capacity. Agent-Pay still evaluates its own financial policy and budget controls.

## Storage rule

The financial operation stores a stable evidence reference/digest and the effective authorization context used for the decision. Historical evidence references are not silently rewritten when the upstream delegation changes.

## V1 boundary

V1 defines the persistence and binding boundary but does not freeze an ATF cryptographic token format. Once ATF's protocol evidence format is finalized, the reference implementation can add a verifier adapter without changing the Agent-Pay financial lifecycle.
