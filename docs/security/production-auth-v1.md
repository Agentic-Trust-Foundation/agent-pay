# Production Authentication V1

The reference implementation supports two modes:

- `development`: deterministic local bearer token for tests and local Compose only.
- `oidc`: production JWT verification using provider JWKS.

## Required OIDC configuration

```text
AGENT_PAY_AUTH_MODE=oidc
AGENT_PAY_OIDC_JWKS_URL=<issuer JWKS endpoint>
AGENT_PAY_OIDC_ISSUER=<expected issuer>
AGENT_PAY_OIDC_AUDIENCE=<Agent-Pay API audience>
```

The verifier requires `exp`, `iat`, `sub`, `iss`, and `aud`, accepts only RS256/ES256 signatures, validates issuer and audience, and requires `agent_id`, `account_id`, and a `scope` claim for the Agent-Pay principal.

The authenticated principal is then bound server-side to the payment request's `agent_id` and `account_id`. A token with identity but without `payments:create` cannot create a payment.

## Approval authentication

Human approval remains a separate trust boundary. The development approval token is not a production mechanism. Production deployments must connect approval to a user-authentication system and bind the decision to the exact payment intent digest/effective policy context.

## Operational requirements

- use short-lived access tokens
- rotate signing keys through the issuer JWKS
- keep issuer/audience configuration explicit per environment
- fail closed on missing or invalid authentication configuration
- never log bearer tokens
- revoke/disable the Agent identity at the authorization layer when required
