# Phase 24 — Agent-Pay Consumption of Agent-to-Agent Delegation

**Status:** V2 integration profile  
**V1 impact:** None. Agent-Pay V1 remains frozen.

Agent-Pay MAY consume an ATF V2 agent-to-agent delegation as upstream authority. It MUST treat the resulting authority as input to financial policy, budget, approval, authentication, and execution controls.

## Rules

1. Agent-Pay MUST verify the complete relevant delegation chain before using delegated financial authority.
2. Effective financial authority is bounded by the intersection of all upstream scopes and constraints.
3. Agent-Pay MUST NOT increase amount, currency, merchant/resource, audience, action, validity, or delegation depth.
4. A revoked, expired, invalid, ambiguous, or unverifiable required parent MUST fail closed.
5. The final financial request MUST bind to the final delegate and the verified chain.
6. Human approval can satisfy a financial approval requirement but cannot expand ATF authority.
7. Provider execution MUST remain downstream of the verified authority and Agent-Pay financial controls.
8. Audit evidence MUST retain the delegation-chain reference and the effective constraints used for the decision.

## Example boundary

ATF root authority → Agent A → Agent B → Agent-Pay policy → budget → approval → payment rail

Agent-Pay owns the financial decision after receiving valid authority; it does not become an authority issuer.

## Acceptance

- V2 ATF delegation semantics are consumed without semantic expansion.
- Positive/negative chain cases are represented in integration tests.
- Agent-Pay financial limits remain no broader than the effective ATF authority.
- V1 contracts and conformance vectors remain unchanged.
