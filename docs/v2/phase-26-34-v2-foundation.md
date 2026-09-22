# Agent-Pay V2 Consumption Contract — Phases 26–34

Agent-Pay consumes ATF V2 authority semantics and may further restrict them through financial policy, budgets, approvals, provider controls, and transaction state. It MUST NOT broaden ATF authority.

For Phase 26, trust negotiation establishes context only; it does not authorize payment.
For Phase 27, financial constraints are intersected with upstream authority.
For Phase 28, delegated principals inherit the complete effective authority chain.
For Phase 29, payment requests bind to verified authorization evidence.
For Phase 30, revoked/expired credentials fail closed and key rotation cannot broaden authority.
For Phase 31, only minimum necessary provenance is retained while required authority evidence remains verifiable.
For Phase 32, enterprise assurance can be required by policy but never substitutes for authority.
For Phase 33, Agent-Pay accepts ATF vectors produced by independent implementations without changing their semantics.
For Phase 34, the financial layer runs the shared suite and records stable evidence.

Unknown, malformed, ambiguous, stale, expired, revoked, or unverifiable authority is not converted into payment authorization.
