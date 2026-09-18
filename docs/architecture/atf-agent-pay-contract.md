# ATF to Agent-Pay Contract

## Boundary

Agentic Trust Foundation (ATF) establishes identity, delegation, authorization,
capability, trust, consent, provenance, and revocation. Agent-Pay consumes a
normalized authorization context and applies financial controls.

Agent-Pay must not mint general authorization or infer financial authority from
authentication alone.

## Normalized authorization context

The V1 reference contract is:

- evidence_id: stable upstream evidence reference.
- issuer: authority that produced the evidence.
- agent_id: authorized agent.
- account_id: principal/account receiving the financial authority.
- delegation_id: optional delegation/mandate reference.
- scope: permitted action set; PAYMENT is the V1 payment action.
- max_amount: optional hard amount ceiling.
- currency: optional currency restriction.
- valid_until: upstream expiry when available.
- digest: optional evidence/content digest.
- version: optional evidence version.

Agent-Pay fails closed when required identity, account, scope, amount, currency,
or validity constraints cannot be established.

## Financial decision boundary

ATF
  |
  | authorization evidence
  v
Agent-Pay
  |
  +--> validate normalized authority
  +--> evaluate spending policy
  +--> reserve budget
  +--> require/record approval when policy says so
  +--> execute payment
  +--> record transaction + ledger + audit

An approval cannot expand the authority represented by ATF evidence. A policy
decision cannot create authorization. A successful authentication cannot by
itself authorize spending.

## Cryptographic mechanism

V1 intentionally does not freeze a universal ATF token/signature format.
Protocol-specific adapters may verify signatures/tokens and then construct the
normalized context above. The financial core stores references and evidence
metadata rather than raw credentials.

## Replay and binding

Payment decisions should reference the evidence identifier and request identity.
Approval additionally binds the exact payment request, account, agent, amount,
currency, merchant reference, policy version, and authorization evidence through
an immutable digest.

## Versioning

Changes to the upstream evidence contract require a new evidence version or
adapter contract. Historical payment decisions retain the references used at
decision time.
