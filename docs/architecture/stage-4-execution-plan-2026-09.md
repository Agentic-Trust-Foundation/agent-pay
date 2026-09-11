# Stage 4 — Execution Plan

Stage 4 converts the Stage 3 converged specification into an executable reference implementation and conformance gate.

## Workstreams

### A. Domain core
- canonical identifiers
- payment state machine
- approval state machine
- budget reservation lifecycle
- policy evaluation

### B. Financial integrity
- double-entry journal validation
- balanced posting transaction
- wallet availability derived from authoritative ledger state
- compensating corrections only

### C. Payment orchestration
- request idempotency
- provider operation idempotency
- explicit UNKNOWN_EXTERNAL_OUTCOME
- authentication pause/resume
- refund/void separation

### D. External provider boundary
- adapter interface
- opaque provider references
- webhook verification
- provider event persistence before processing
- duplicate/out-of-order event handling

### E. Async reliability
- transactional outbox
- retry policy
- poison-event quarantine
- settlement ingestion
- reconciliation worker

### F. Conformance
- execute all normative V1 vectors
- map every financial-control invariant to an executable test
- fail CI on OpenAPI/schema/state/event drift

## Definition of done

Stage 4 is complete only when a clean environment can run the reference implementation, execute the V1 conformance suite, and demonstrate that financial-control invariants hold under retries, concurrent requests, duplicate provider events, ambiguous provider outcomes, and policy/approval changes.
