# Batch 1 — Stages 10–12 Completion

Status: COMPLETE on main.

## Stage 10 — Policy Engine

Implemented and aligned:

- deterministic V1 spending-policy evaluator;
- fail-closed default when no usable transaction limit exists;
- amount, currency, merchant-domain, and category controls;
- allow/deny precedence;
- approval and notification thresholds;
- immutable policy-version reference;
- machine-readable decision evidence containing decision, policy version, reasons, and evaluated rules;
- unit tests and conformance vectors.

## Stage 11 — Approval / Human-in-the-loop

Implemented and aligned:

- explicit approval state machine;
- approval expiration;
- terminal-state protection;
- deterministic intent binding digest;
- binding across payment request, account, agent, amount, currency, merchant, policy version, and authorization evidence;
- approval cannot expand authorization or bypass policy;
- approval records are persisted and linked to the payment request;
- API approval path validates expiry and intent binding.

## Stage 12 — ATF ↔ Agent-Pay Contract

Implemented and documented:

- normalized authorization context;
- upstream evidence reference and issuer;
- agent/account binding;
- delegation reference;
- scope;
- amount and currency constraints;
- validity/expiry;
- evidence digest/version references;
- fail-closed validation;
- no universal cryptographic token format frozen inside Agent-Pay V1;
- authorization evidence is persisted by reference/metadata rather than primary credentials.

## Conformance

V1 conformance vectors now explicitly cover:

- reconstructable policy decisions;
- normalized ATF authorization context;
- invalid/expired authority failing closed;
- exact-intent approval binding.

## Boundary

ATF remains the authority for identity, delegation, authorization, trust,
capability, consent, provenance, and revocation. Agent-Pay remains responsible
for financial policy, approval, budget, payment execution, transaction,
settlement, reconciliation, and ledger controls.

The next implementation batch can proceed to the payment/ledger/outbox core:
Stages 13, 15, 16, 17, and 18.
