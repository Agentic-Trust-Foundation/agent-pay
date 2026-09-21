# Phase 14 — Initial Security Review

**Status:** Initial source review; remediation and CI validation remain pending.

## Confirmed findings

### S14-01 — Development credentials have implicit defaults

`reference/implementation/src/agent_pay/auth.py` accepts `local-agent-token` and `local-approval-token` when the corresponding environment variables are unset. If development mode is enabled outside an isolated local environment, known credentials can authenticate agents or approve actions.

**Required remediation:** remove implicit credential defaults; require explicit development secrets; prevent development mode in production deployment configurations; add regression tests for missing configuration and production-mode refusal.

### S14-02 — Webhook replay protection is disabled by default

`reference/implementation/src/agent_pay/webhooks.py::_enforce_replay_window` defaults `AGENT_PAY_WEBHOOK_REPLAY_WINDOW_SECONDS` to `0`, and treats non-positive values as disabling the time check. Signed old payloads are therefore accepted unless deployment configuration explicitly enables the window. Event-ID deduplication does not establish freshness or prevent replay under changed identifiers.

**Required remediation:** require a positive configured window or provide a safe default; validate timestamp presence, format, and timezone; test stale, future, malformed, missing, and disabled-window cases.

### S14-03 — Provider identity is not bound to webhook operation lookup

The webhook route accepts `provider_name`, but operation lookup selects by `provider_reference` alone, ordered by creation time with `LIMIT 1`. The ledger-account lookup also hardcodes provider name `mock`. A signed event from one provider could resolve against another provider's operation if references collide, and ambiguous matches are selected arbitrarily.

**Required remediation:** scope operation and account resolution by provider identity; reject ambiguous matches; test cross-provider reference collisions.

### S14-04 — Webhook body and JSON validation need hardening

The endpoints read the entire request body before applying a size limit. The settlement endpoint does not first ensure decoded JSON is an object before calling `.get`.

**Required remediation:** enforce a bounded request body and consistent JSON object/type validation before field access or persistence.

## Review limitations

This is a source-level review of `auth.py` and `webhooks.py`, not a complete security audit. No remediation has been committed and no CI/test success is claimed.