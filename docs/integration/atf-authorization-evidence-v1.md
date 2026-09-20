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

## V1 verification profile

The financial lifecycle now requires **cryptographically verified** authority evidence. The reference implementation provides a JWT/JWKS verification adapter configured with:

- trusted ATF issuer;
- Agent-Pay audience;
- trusted JWKS endpoint;
- `atf/v1` protocol version;
- explicit `ALLOW` decision;
- `PAYMENT` action/scope;
- agent/account binding;
- positive maximum amount and matching currency;
- expiry;
- `VALID` revocation status;
- stable evidence ID and version.

The JWT/JWKS profile is an implementation adapter, not a claim that ATF V1 has frozen one universal credential format.

Unverified evidence cannot be bound to a payment request. PostgreSQL also rejects a payment request that references anything other than `VERIFIED` authorization evidence.

This preserves the V1 boundary: ATF remains responsible for producing/verifying authority, while Agent-Pay requires a trusted verifier at its integration seam and never mints or expands general authorization.
