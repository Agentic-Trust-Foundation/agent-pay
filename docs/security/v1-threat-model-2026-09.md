# Agent-Pay V1 Threat Model

## Scope

This model covers the Agent-Pay financial-control boundary: authenticated agents, delegated authority references, policy and budget enforcement, approval, payment execution, provider webhooks, settlement, reconciliation, ledger posting, and auditability.

## Primary threats

| Threat | Impact | V1 control |
|---|---|---|
| Compromised agent | Unauthorized spending | Server-side delegation + policy + budget checks |
| Credential theft | Agent impersonation | Short-lived, scoped, audience-bound production credentials |
| Replay | Duplicate payment | API/provider idempotency and event deduplication |
| Idempotency-key abuse | Request substitution | Request fingerprint binding and conflict on material changes |
| Budget race | Overspending | Row locks and atomic reservations |
| Approval substitution | User approves different intent | Approval bound to exact payment intent |
| Forged webhook | False financial outcome | Signature verification before mutation |
| Duplicate webhook | Duplicate debit/credit | Provider-event deduplication + idempotent ledger journal |
| Provider timeout | Incorrect failure or duplicate charge | UNKNOWN_EXTERNAL_OUTCOME |
| Settlement mismatch | Silent financial drift | Explicit reconciliation discrepancy |
| Provider secret exposure | Rail compromise | Provider credentials remain outside agent boundary |
| Ledger corruption | Incorrect financial truth | Double-entry balanced journals + append-oriented corrections |
| Admin abuse | Unauthorized privileged change | Separate authorization and audit requirements |

## Security invariants

1. An agent never owns user funds.
2. An agent never receives primary financial credentials.
3. Identity alone never grants spending authority.
4. Invalid or expired authorization fails closed.
5. Financial mutations are idempotent.
6. Provider input is untrusted until verified.
7. Approval is bound to the exact payment intent.
8. External timeout is not treated as automatic failure.
9. Historical financial records are not overwritten.
10. Reconciliation discrepancies do not silently mutate the ledger.

## Production hardening still required

- Replace development bearer tokens with OIDC/JWT validation and key rotation.
- Add provider-specific signature adapters and replay-window checks.
- Store sensitive provider credentials only in a secret/tokenization boundary.
- Add rate limiting and abuse detection.
- Add privileged-admin authorization and tamper-evident audit export.
- Add formal cryptographic authorization-evidence verification when ATF integration is enabled.
