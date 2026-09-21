# Phase 20 — ATF ↔ Agent-Pay Contract Mapping

**Status:** implementation track  
**V1 rule:** this document consumes the frozen V1 semantics; it does not redefine them.

## Pinned baseline

- ATF main at Phase 20 start: `a5ea54d9a9cc9f9aa3a1f140e75370996471076c`
- Agent-Pay main at Phase 20 start: `0701a77e72a9378ec23ad264dfc1e78101bff690`
- ATF integration boundary: `docs/architecture/agent-pay-integration-boundary.md`
- Agent-Pay integration profile: `docs/integration/atf-authorization-evidence-v1.md`
- Shared vectors: `conformance/v1/atf-agent-pay-contract-vectors.yaml`

## Normalized authority consumed by Agent-Pay

| Semantic field | Financial use | Failure rule |
|---|---|---|
| subject_agent | bind request to authorized agent | mismatch → DENY |
| delegating_principal | retain upstream authority provenance | missing when required → DENY |
| issuer/trust_domain | identify verification authority | unknown/untrusted → DENY |
| decision | require explicit upstream authorization | missing/indeterminate → DENY |
| action | bind authority to requested financial action | mismatch → DENY |
| resource | bind account/merchant/payment scope | mismatch → DENY |
| constraints | intersect amount/currency/purpose/time bounds | exceed bound → DENY |
| issued_at/expires_at | validity window | expired/invalid → DENY |
| revocation_status | current authority state | revoked/indeterminate → DENY |
| evidence_ref/evidence_version | reconstruct decision evidence | missing → DENY |

## Effective-authority rule

The effective financial permission is the intersection of:

1. upstream ATF authority;
2. requested payment intent;
3. account/instrument constraints;
4. Agent-Pay financial policy;
5. required human approval conditions.

Agent-Pay may restrict the result, never expand it.

## Positive paths

- valid authority + valid financial policy → eligible for execution;
- valid authority + financial policy requires approval → REQUIRE_HUMAN;
- narrower downstream financial policy → restricted execution within the intersection.

## Negative paths

- expired authority → DENY;
- revoked authority → DENY;
- subject mismatch → DENY;
- audience/trust-domain mismatch → DENY;
- action/resource mismatch → DENY;
- missing required evidence → DENY;
- payment amount/currency beyond upstream bound → DENY;
- approval attempting to exceed upstream bound → DENY;
- replay/conflicting reuse → DENY or explicit revalidation according to implementation semantics;
- malformed/unknown required claims → DENY.

## Evidence requirement

Phase 20 is complete only when these semantics are represented by executable conformance vectors and the repository CI runs for a specific commit. CI success does not imply live-provider or production readiness.
