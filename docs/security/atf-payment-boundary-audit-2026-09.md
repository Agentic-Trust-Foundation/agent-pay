# ATF ↔ Agent-Pay Code Audit (2026-09)

## Scope

This is a focused source review of the reference implementation's authorization context, in-memory payment service, and persistence-backed orchestrator. It is not a complete security audit. CI was reported green by the maintainer; this document does not claim independent execution of CI.

## Files reviewed

- `reference/implementation/src/agent_pay/authorization.py`
- `reference/implementation/tests/test_authorization.py`
- `reference/implementation/src/agent_pay/service.py`
- `reference/implementation/src/agent_pay/orchestrator.py`

## Findings

### F-01 — Persistence-backed orchestration does not enforce ATF authorization context (critical)

`PaymentOrchestrator.prepare()` accepts payment/request/budget IDs and amount/currency, but no normalized ATF authorization context or verified decision. `execute_external()` likewise charges based only on payment ID, amount, and currency. `finalize()` accepts a caller-supplied provider outcome and financial ledger account IDs without itself proving that the payment was authorized or that the outcome came from a trusted provider adapter.

**Risk:** if these methods are reachable without a strongly enforced, separate authorization boundary, callers may reserve/charge/finalize a payment without the ATF scope, subject, expiry, or revocation checks documented by the integration contract. This is a source-level boundary gap; exploitability depends on the actual API/call graph and access controls, which were not fully reviewed here.

**Required remediation:** require an immutable, validated authorization decision/evidence reference at the orchestration boundary; bind it to agent, principal/account, action, resource/payment request, amount, currency, validity and evidence version; reject missing/invalid/indeterminate evidence before reservation and again before external execution where appropriate. Persist the evidence reference/version with the payment. Ensure provider outcomes can only enter finalization through a trusted adapter/reconciliation path, not an arbitrary request field.

### F-02 — AuthorizationContext currently permits omitted scope and omitted amount/currency bounds

`AuthorizationContext.validate()` checks the action only when `scope` is non-empty, and checks amount/currency only when those bounds are non-null. The existing tests cover mismatched identities, amount over the supplied maximum, currency mismatch, and expiry, but do not cover empty scope or absent financial bounds.

**Risk:** the context can act as broader authority than a fail-closed contract intends unless adapters guarantee these fields are always present and validated.

**Required remediation:** define requiredness explicitly for payment authorization (at minimum explicit payment action/scope, amount ceiling, and currency); reject missing bounds for payment operations. Add tests for absent/empty scope, missing max amount/currency, zero/negative amount, and evidence revocation/indeterminate state.

### F-03 — In-memory service and persistence-backed orchestrator are separate execution paths

`PaymentService.create_payment()` uses its own policy/budget/provider flow and does not accept `AuthorizationContext`. `PaymentOrchestrator` is a separate persistence-backed path and also does not accept it. This review did not establish which path is exposed by the production/API entrypoint.

**Risk:** fixing only one path could leave an alternate payment path without the same authorization enforcement.

**Required remediation:** map every entrypoint to its execution path; centralize the authorization gate or enforce the same contract in every path; add integration tests proving unauthorized requests cannot reach any provider adapter.

### F-04 — State-transition and finalization trust boundaries need explicit verification

The reviewed orchestrator's `finalize()` has no visible state/precondition check preventing repeated or out-of-order finalization, and accepts `outcome` as a method argument. Ledger posting uses an idempotency key, but budget consumption and status/event transitions also need transactionality and duplicate-call tests.

**Required remediation:** enforce allowed state transitions under database transaction/locking; authenticate and correlate provider operation results; make repeated finalization safe across budget, ledger, status, and outbox; test duplicate, stale, contradictory, and out-of-order outcomes.

## Recommended order

1. Trace API/worker entrypoints and prove which payment execution path is reachable.
2. Close F-01: make authorization evidence mandatory at the persistence-backed orchestration boundary and persist the evidence binding.
3. Close F-02: fail closed on missing scope and missing financial bounds; add focused tests.
4. Close F-04: harden transition guards and provider outcome provenance/idempotency.
5. Close F-03: ensure all execution paths share the same gate; add end-to-end negative tests.
6. Re-run CI and report the exact workflow/run and test results.

## Limitations

This review did not inspect every API route, repository, migration, provider adapter, worker, or test suite. No exploit was executed. Findings are based on the source files listed above and should be confirmed against the complete call graph before release decisions.