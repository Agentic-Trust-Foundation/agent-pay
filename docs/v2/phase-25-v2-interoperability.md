# Phase 25 — Agent-Pay V2 Interoperability Profile

Agent-Pay consumes the shared ATF V2 interoperability semantics as an authority input.

The financial layer may restrict authority further through policy, budget, approval and provider controls. It MUST NOT broaden ATF authority.

Agent-Pay MUST:
- reject unsupported protocol versions;
- preserve subject, audience, action, amount/currency, validity, revocation and depth bounds;
- fail closed on ambiguous or unverifiable required authority;
- bind evidence to the final payment request;
- record the stable conformance evidence fields defined by Phase 25.

The two-implementation rule is mandatory before any V2 semantic feature is promoted to a normative interoperability requirement.
