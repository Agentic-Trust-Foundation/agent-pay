# Authorization Evidence

## Purpose

Agent-Pay must be able to establish why an agent is permitted to request a financial operation without becoming a general-purpose identity or trust system.

The system therefore consumes **authorization evidence** produced by an upstream trust/delegation system such as Agentic Trust Foundation (ATF), AP2, or another compatible authority.

## Core principle

> Agent-Pay evaluates financial authority; it does not invent general agent authority.

A successful authentication of an agent is not sufficient to authorize a payment.

A payment decision should be bound to evidence covering, as applicable:

- subject / agent identity
- account or principal
- delegation or mandate reference
- authorized scope
- validity period
- relevant capabilities
- constraints
- issuer / authority
- evidence identifier
- evidence version
- revocation status or freshness information

## Conceptual model

```text
User / Principal
      |
      | delegates authority
      v
Trust / Delegation System
      |
      | Authorization Evidence
      v
Agent
      |
      | Payment Intent + Evidence
      v
Agent-Pay
      |
      +--> validate evidence
      +--> evaluate spending policy
      +--> evaluate budget
      +--> evaluate risk
      +--> approval decision
      v
Payment
```

## Binding

Authorization evidence must be bound strongly enough to prevent replay or substitution between payment requests.

At minimum, the payment decision context should be able to reference:

- evidence ID
- agent ID
- account ID
- requested action / payment purpose
- merchant context where applicable
- amount and currency where the authority is amount-bound
- request identifier
- issued-at / expiry information

The exact cryptographic mechanism is protocol-specific and should not be hard-coded into the Agent-Pay core.

## Evidence lifecycle

```text
PRESENTED
   |
   v
VALIDATED
   |
   +----> REJECTED
   |
   v
ACCEPTED
   |
   v
USED / RECORDED
   |
   v
EXPIRED / REVOKED
```

Agent-Pay must fail closed when required evidence is missing, malformed, expired, revoked, outside scope, or otherwise unverifiable.

## ATF boundary

ATF remains responsible for general identity, delegation, authorization, trust, capability, consent, provenance, and revocation.

Agent-Pay consumes the resulting evidence and applies financial controls. Agent-Pay may cache validation results where safe, but cached evidence must have an explicit freshness policy.

## Audit

The payment audit record should preserve references to the authorization evidence used for the decision without unnecessarily copying sensitive credentials or full upstream assertions.

Recommended references:

```text
authorization_evidence_id
authorization_issuer
authorization_version
authorization_decision_reference
```

## V1 boundary

V1 does not mandate a single authorization protocol. The core must support an internal normalized authorization context while adapters translate external evidence into that context.

This keeps Agent-Pay compatible with ATF, AP2, and future authorization protocols without coupling the financial engine to one trust protocol.
