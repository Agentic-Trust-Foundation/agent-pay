# Stage 20 — Cross-Repository Conformance

## Objective

Stage 20 verifies that the two repositories agree on the V1 financial boundary.

- Agentic Trust Foundation defines identity, delegation, authorization, capability,
  trust, consent, provenance, and revocation.
- Agent-Pay consumes normalized authority and owns financial control and execution.
- Neither repository may silently move responsibility across that boundary.

## Shared contract

ATF publishes:
- docs/architecture/agent-pay-integration-boundary.md
- conformance/v1/agent-pay-contract-vectors.yaml

Agent-Pay consumes:
- docs/architecture/atf-agent-pay-contract.md
- conformance/v1/atf-agent-pay-contract-vectors.yaml

The Agent-Pay conformance workflow fetches the ATF vector file from the ATF main
branch and compares version, suite, vector identifiers, invariants, and outcomes.

## Boundary matrix

| Rule | ATF | Agent-Pay |
|---|---|---|
| General identity and authorization | Owns | Consumes |
| Delegation and authority | Owns | Validates normalized result |
| Spending policy | Outside core | Owns |
| Financial budget | Outside core | Owns |
| Payment approval | Authority/consent may originate upstream; financial approval is recorded here | Owns financial control |
| Payment execution | Outside core | Owns orchestration |
| Ledger | Outside core | Owns |
| Settlement and reconciliation | Outside core | Owns |
| Universal ATF token/signature format | Not frozen in V1 | Does not infer one |
| Cross-repository vectors | Publishes | Executes |

## Fail-closed conditions

The check fails if the ATF vector suite is missing, versions differ, vector identifiers
differ, expected outcomes differ, or the implementation contradicts the stated
authority boundary.

## Non-goals

This does not prove production cryptographic interoperability, live PSP/bank
compatibility, legal/regulatory compliance, network availability, or semantic
equivalence of future ATF specifications.
