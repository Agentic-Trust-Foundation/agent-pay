# Phase 18 Final Audit — V1/V2 Baseline

**Audit date:** 2026-09-21  
**Audited main commit:** `eb2f06d6d3da5c14de269e3da92d068cb515ad65`  
**Issue:** #18  
**Classification:** Final audit / documentation-only

## Executive result

**V1 baseline: PASS for the repository's declared protocol/reference scope.**

No new V1 semantic blocker was identified in this audit. The repository contains the declared protocol artifacts, reference implementation, conformance vectors, persistence/bootstrap assets, security/governance documentation, and the Phase 14–17 hardening chain.

The V1 claim remains intentionally limited to a provider-neutral protocol, conformance suite, and reference implementation. It does **not** claim production PSP/bank/card-issuer integration, regulatory certification, HSM/vault deployment, or jurisdiction-specific compliance.

## Evidence baseline

Current `main`:

`eb2f06d6d3da5c14de269e3da92d068cb515ad65`

Post-Phase-17 GitHub Actions on this commit:

- Agent-Pay Validation — **success**
- Agent-Pay Conformance — **success**
- Agent-Pay Docker Clean Start — **success**
- Dependabot GitHub Actions update — **success**
- Dependabot Python update — **success**

The Phase 14, 15, and 16 merge commits also have successful required CI records in the repository history.

## Audit matrix

| Area | Result | Evidence / conclusion |
| --- | --- | --- |
| Product boundary | PASS | README and release docs keep Agent-Pay separate from ATF identity/trust and from commerce/catalog concerns. |
| ATF authority boundary | PASS | Verified authority evidence is required; Agent-Pay must not expand upstream authority. |
| Authentication | PASS | Explicit agent/account binding and production adapter boundaries are documented; implicit development credentials were removed in Phase 14. |
| Authorization evidence | PASS | Cryptographic verification and database/execution binding are covered by the V1 release checklist and implementation tests. |
| Policy | PASS | Immutable policy model exists; Phase 16 adds opt-in multidimensional context without changing the V1 decision enum. |
| Budget/reservations | PASS | Concurrency-safe reservations and lifecycle controls are present and tested. |
| Approval | PASS | Approval history and exact-intent binding are represented and tested. |
| Payment lifecycle | PASS | Durable lifecycle, terminal replay validation, provider-operation identity, capture/void/refund semantics, and idempotency were hardened in Phase 15. |
| Provider operations | PASS | Provider-operation identity is durable and idempotency conflicts are rejected rather than silently rewritten. |
| Webhooks/events | PASS | Signed webhook boundary, bounded bodies, replay controls, provider scoping, event validation, and deduplication are implemented. |
| UNKNOWN external outcome | PASS | Explicit ambiguous-outcome handling remains part of the lifecycle. |
| Ledger | PASS | Journal/posting persistence and idempotent financial effects are present; V1 describes the ledger as double-entry-ready. |
| Settlement/reconciliation | PASS | Settlement and reconciliation persistence/flows are part of the declared V1 implementation and tested baseline. |
| Audit/outbox | PASS | Append-only audit and transactional outbox/worker primitives are present. |
| PostgreSQL bootstrap | PASS | Clean-start workflow is green on current main. Migration ordering issue is historical and documented. |
| API/conformance | PASS | OpenAPI, V1 vectors, reference implementation tests, and required CI are present. |
| Security governance | PASS | SECURITY.md, security-sensitive review expectations, and Phase 14 hardening are present. |
| Repository governance | PASS | Phase 17 added governance, CODEOWNERS, PR/issue templates, and Dependabot configuration. |
| V1/V2 separation | PASS | V1 is explicitly frozen; V2 work is non-normative until defined gates are satisfied. |

## GitHub governance finding

The repository contains the intended governance artifacts, but the connected GitHub integration exposes no repository rulesets and does not provide administration writes for this repository.

Therefore:

- repository-side governance documentation is **PASS**;
- CODEOWNERS/templates/Dependabot are **PASS**;
- actual GitHub branch-protection/ruleset enforcement is **FOLLOW-UP / administrative**.

The project must not claim that required-PR, required-check, no-force-push, approval, or conversation-resolution rules are enforced until those settings are actually enabled in GitHub repository administration.

## Open work observed during audit

A Dependabot PR was open at audit time:

- PR #17 — Python `mypy` dependency update.

Its existence was not a V1 protocol defect. It was normal maintenance work and remains subject to normal CI/governance handling.

The Phase 18 audit issue was the final V1 audit issue; subsequent maintenance is tracked through normal issues and dependency updates.

## Deployment/provider boundaries

These remain intentionally outside the V1 protocol claim:

- production OIDC/JWT issuer, audience, JWKS and rotation;
- production ATF trust/revocation infrastructure;
- provider-specific webhook keys and rotation;
- live PSP/bank/card-issuer integration and certification;
- production secrets/vault/HSM and applicable PCI scope;
- jurisdiction-specific legal/regulatory/compliance review;
- production SLO, incident response, fraud/risk and operational controls;
- full dispute/chargeback workflows where required by a selected rail.

These are deployment/provider profiles, not reasons to reopen the frozen V1 architecture.

## Residual risks

1. **GitHub enforcement is administrative:** repository documentation cannot substitute for branch-protection/ruleset configuration.
2. **Production financial integrations remain unvalidated:** the reference implementation uses provider-neutral/simulator boundaries.
3. **Compliance is deployment-specific:** no universal regulatory or PCI claim is made.
4. **V2 interoperability is not yet normative:** a V2 implementation must satisfy the documented semantic/security/conformance/interoperability gates before becoming a normative protocol extension.
5. **Dependabot maintenance remains ongoing:** automated dependency updates should continue to pass the same required CI before merge.

## Final conclusion

The repository has crossed the intended V1 completion boundary.

The appropriate next work is **not another V1 architecture redesign**. Future work should be selected from:

- V2 workstreams;
- provider/deployment profiles;
- production security/compliance work;
- additional non-breaking hardening;
- ATF/Agent-Pay cross-repository interoperability work.

Any future change that modifies V1 semantics must be explicitly versioned and governed as a protocol change.

## Audit disposition

**PASS — V1 frozen baseline verified.**

**FOLLOW-UP — configure/enforce GitHub repository rulesets administratively when repository administration access is available.**

No V1 semantic changes are included in this audit.
