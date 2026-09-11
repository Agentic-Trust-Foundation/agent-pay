# Agent-Pay Financial Control Invariants

These invariants are non-negotiable properties of the Agent-Pay design and implementation.

## Authority

1. An Agent never owns user funds.
2. An Agent never receives primary financial credentials.
3. A payment requires verifiable authorization context.
4. Approval cannot expand authority beyond the applicable delegation and policy boundary.

## Policy

5. Policy evaluation is deterministic for a fixed policy snapshot and evaluation context.
6. Explicit denial and hard constraints cannot be bypassed by broader allow rules.
7. Policy evaluation has no direct financial side effects.
8. Policy failures fail closed.

## Budget

9. Budget capacity is distinct from wallet funds.
10. Active budget reservations reduce available budget capacity.
11. Budget reservation is atomic under concurrency.
12. Budget reservation, consumption, and release are idempotent.
13. A child/narrow budget cannot expand a parent or delegation limit.

## Payment

14. Payment Request is intent; Payment is execution; Transaction is financial effect.
15. Payment operations are idempotent.
16. Provider timeouts do not automatically mean payment failure.
17. Ambiguous external outcomes require recovery or reconciliation.
18. Authentication/challenge states are explicit.
19. Refund, reversal, and dispute are distinct financial operations.

## Ledger

20. Ledger is the financial source of truth.
21. Historical financial entries are immutable.
22. Corrections use compensating entries or adjustments.
23. Financial state changes and corresponding internal ledger effects are atomic.
24. Money uses exact decimal semantics; floating-point arithmetic is not authoritative.
25. Currency conversion is never implicit.

## Events

26. Critical state changes are durably represented before event publication.
27. Event consumers tolerate duplicate delivery.
28. External webhook consumers tolerate delayed and out-of-order events.
29. Event retries cannot duplicate financial effects.
30. Notifications never determine financial truth.

## Security

31. Payment credentials are isolated behind opaque references/tokenization.
32. Secrets are never written to normal logs, events, or audit records.
33. Every financial API operation enforces authorization at the resource boundary.
34. Replay protection and idempotency are required for financial operations.
35. Webhooks are authenticated and verified before state changes.

## Recovery

36. Every external operation has a recoverable provider reference when available.
37. Recovery paths are first-class, not exceptional scripts.
38. Reconciliation can identify mismatched internal/provider state.
39. Financial history remains explainable after retries, failures, refunds, and adjustments.

## Architecture

40. V1 remains a modular monolith until scale or operational evidence justifies extraction.
41. Module boundaries are explicit even when modules share a deployment.
42. Redis/cache layers never become the financial source of truth.
43. Provider-specific behavior remains behind adapters.
44. Agent-Pay does not become a general identity/trust or commerce protocol.
