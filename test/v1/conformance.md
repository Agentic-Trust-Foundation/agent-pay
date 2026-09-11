# V1 Executable Conformance Plan

The V1 conformance suite MUST execute the vectors in `conformance/v1/payment-control-vectors.yaml` against the reference implementation.

## Required test groups

- authority and delegation
- policy decision
- budget reservation and concurrent reservation
- approval intent binding
- payment authentication
- provider timeout / unknown outcome
- provider event deduplication and replay protection
- idempotency
- double-entry ledger balance
- transactional outbox
- settlement/reconciliation separation
- credential boundary

## Gate

A V1 implementation is not conformant merely because it exposes the documented API. Every normative financial-control invariant must have at least one executable test.
