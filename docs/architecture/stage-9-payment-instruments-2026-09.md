# Stage 9 — Payment Instruments

**Status:** Implementation started

## Goal

Turn the payment-instrument abstraction into an explicit, enforceable V1 domain boundary.

Stage 8 established provider routing and rail adapters. Stage 9 makes the instrument selected by Agent-Pay a first-class controlled object with lifecycle, eligibility, account binding, and credential-isolation rules.

## Scope

### In scope

- canonical payment-instrument types and lifecycle;
- wallet and virtual-card reference instruments;
- instrument eligibility checks before execution;
- account ownership binding;
- currency compatibility;
- deterministic instrument selection;
- PostgreSQL integrity constraints;
- reference implementation tests;
- credential/provider-reference isolation.

### Explicitly out of scope

- real card issuance;
- PAN/CVV storage;
- bank credentials;
- live PSP/bank integrations;
- production vault implementation;
- risk/fraud scoring.

## Canonical model

```text
Account
  |
  +--> Wallet --------------------+
  |                                |
  +--> Funding Source              |
  |                                v
  +--> Payment Instrument --> Instrument Selector --> Payment Router --> Rail
                                    |
                                    +--> Policy/Budget/Approval already passed
```

## Rules

1. An Agent references an instrument; it never receives the instrument's financial credentials.
2. An instrument belongs to exactly one Agent-Pay account.
3. A wallet instrument must reference a wallet owned by the same account.
4. An instrument must be ACTIVE to execute a payment.
5. Currency compatibility is checked before provider execution.
6. Instrument selection cannot bypass policy, budget, approval, authentication, or authorization checks.
7. Provider references are opaque identifiers; secrets are never persisted in the instrument record.
8. Deactivation is a control decision and must not mutate historical payment or ledger records.

## Lifecycle

```text
ACTIVE <-> SUSPENDED
   |
   v
 CLOSED
```

`CLOSED` is terminal for execution. Historical references remain valid for audit and reconciliation.

## Selection

The selector evaluates candidate instruments deterministically. The first eligible instrument in configured priority order wins. If no candidate is eligible, payment execution must stop without creating a provider-side operation.

Eligibility includes:

- account binding;
- active status;
- supported currency;
- instrument type capability;
- optional merchant/domain constraints;
- optional provider availability.

## V1 completion criteria

Stage 9 is complete when:

- instrument state/type semantics are documented and represented in code;
- PostgreSQL enforces account and wallet binding invariants;
- selection is deterministic and side-effect free;
- inactive/mismatched instruments are rejected before provider execution;
- no credential material is accepted by the reference model;
- unit and PostgreSQL integration tests cover the invariants;
- validation and Docker CI are green on the Stage 9 commit.
