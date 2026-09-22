# Phase 22 — Cross-Repository Conformance Evidence

**Status:** COMPLETE  
**ATF producer revision:** `07f3e991ae0eb10ca4d838025f345467ab6684f3`  
**ATF vector blob:** `11b6939b65906aa0efc768d678b2356db383f7ec`  
**Local consumer vectors:** `conformance/v1/atf-agent-pay-contract-vectors.yaml`

Phase 22 makes the existing ATF ↔ Agent-Pay conformance check reproducible by pinning the producer revision and verifying the producer artifact identity.

## Verification behavior

`tools/check_cross_repo_conformance.py` now:

1. reads the canonical ATF vector from the pinned commit;
2. verifies the returned Git blob SHA;
3. normalizes and compares producer and consumer vectors;
4. exits non-zero on unavailable, mismatched, or altered producer evidence;
5. reports the pinned revision, blob identity, vector count, and local SHA-256.

The consumer therefore no longer follows a moving ATF `main` reference for conformance evidence.

## Scope

The 15 shared vectors cover authority ownership, PAYMENT scope, financial bounds, policy/approval non-expansion, evidence retention, expiry, revocation, audience/subject/action binding, replay, required evidence, and monotonic attenuation.

## Boundary

This is conformance evidence only. It does not claim a live PSP/bank/card integration, regulatory certification, HSM deployment, or production payment readiness.

## Maintenance rule

When the canonical ATF vector artifact changes, update the pinned ATF commit and blob SHA in the checker in the same change, refresh the local vector copy, and rerun the conformance workflow.

A semantic change to the V1 contract requires explicit versioning rather than silently changing the Phase 22 vector suite.
