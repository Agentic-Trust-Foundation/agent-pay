# Agent-Pay V1 Reference Implementation

This directory is the executable, provider-neutral reference implementation for Agent-Pay Protocol V1.

## Guarantees demonstrated by V1

- authenticated Agent principal binding;
- cryptographically verified ATF authorization evidence through a configurable JWT/JWKS adapter profile;
- fail-closed authority bounds and expiry;
- deterministic spending policy and immutable policy-version references;
- concurrency-safe budget reservation;
- exact-intent human approval;
- payment/provider operation idempotency;
- external execution outside database transactions;
- explicit UNKNOWN_EXTERNAL_OUTCOME;
- signed provider webhook boundary and durable event deduplication;
- capture, void and refund lifecycle;
- double-entry-ready ledger journals/postings;
- transactional outbox;
- settlement/reconciliation observations;
- append-only audit protections;
- PostgreSQL integration and end-to-end tests.

## Run locally

```bash
cd reference/implementation
python -m pip install -e '.[test]'
pytest -q
```

For the PostgreSQL integration suite:

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_pay
pytest -q -m integration
```

The canonical clean-environment bootstrap is in `docker-compose.yml` and applies the V1 migrations through `011_authorization_evidence_integrity.sql`.

## Production boundary

This is a reference implementation, not a production payment processor. Production deployments must provide real provider adapters, production key management, deployment-specific authentication/revocation configuration, operational controls, and applicable compliance/security review.

The implementation must not be treated as the protocol specification. The normative API and semantics are maintained under `specs/v1/` and `docs/`.