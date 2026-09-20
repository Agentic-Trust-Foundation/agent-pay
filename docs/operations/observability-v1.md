# Observability V1

Every operation carries request_id, authorization_evidence_id, authorization_context_hash, payment_id, payment_request_id, idempotency_key, provider_reference, transaction_id, and reconciliation_case_id when applicable.

Metrics include authorization outcomes, approval latency, provider latency/errors, callback duplicates, verification failures, state transitions, reconciliation drift, outbox lag, worker failures, and recovery duration.

Logs are structured and redacted. Payment credentials, bearer tokens, card secrets, and sensitive provider payloads are never logged.

Tracing connects authorization -> policy -> provider -> verification -> ledger -> reconciliation.