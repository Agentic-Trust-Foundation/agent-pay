# Agent-Pay V2 Implementation Plan

V1 remains frozen.

## Workstreams
1. multidimensional financial policy
2. merchant/category/region/time restrictions
3. delegated approval chains
4. commerce and booking lifecycle support
5. refunds/cancellation
6. virtual-card integration profile
7. issuer/instrument lifecycle
8. fraud/risk signal interface
9. disputes/chargebacks
10. advanced agent delegation
11. provider capability discovery
12. recovery and reconciliation edge cases

## Virtual cards
V2 should define a provider-neutral instrument lifecycle:
REQUESTED -> PROVISIONED -> ACTIVE -> SUSPENDED -> EXPIRED/REVOKED.

Sensitive card material remains outside ordinary application logs and agent context.

## Fraud/risk
Risk signals may influence policy outcomes but must not override ATF authority or create authority. Risk is an additional financial control.

## Disputes
Dispute/chargeback workflows need explicit states, evidence references, provider case identifiers, deadlines, and immutable audit history.

## Delegated approvals
Approval chains may require multiple humans or policy authorities. Every approval is bound to the transaction/request and cannot broaden upstream authority.

## V2 gates
No feature becomes normative until semantic behavior, security invariants, negative vectors, and at least two interoperable implementations are defined.
