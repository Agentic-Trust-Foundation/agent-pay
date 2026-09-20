# End-to-End Reference Flow V1

Agent -> Site Adapter (ATF evidence) -> ALLOW + context hash -> Agent-Pay -> evidence re-verification -> policy/budget/approval -> provider adapter -> provider callback -> provider verification -> transaction/ledger/outbox -> result -> reconciliation.

Every hop preserves subject, resource/audience, amount, currency, request ID, idempotency key, and authorization-context hash. No layer may broaden authority.

DENY at Site Adapter prevents financial handoff. Failed Agent-Pay evidence verification prevents provider execution. Timeouts remain non-terminal until verified. Duplicate callbacks cannot create a second financial effect. Reconciliation mismatches create explicit cases.