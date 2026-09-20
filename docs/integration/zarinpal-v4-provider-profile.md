# ZarinPal REST V4 Provider Profile

Status: deployment profile, not a protocol change.

The provider adapter follows the current public ZarinPal REST V4 sample shape:
- `POST /pg/v4/payment/request.json`
- `POST /pg/v4/payment/verify.json`
- provider authority returned by request
- browser redirect to StartPay

## Agent-Pay mapping

| Agent-Pay concept | Provider field |
|---|---|
| payment intent | local payment ID |
| idempotency key | local idempotency record |
| provider reference | authority |
| provider settlement reference | ref_id |
| provider verification | verify response |
| callback | deployment callback endpoint |

The provider callback is never treated as proof of successful payment by itself. Agent-Pay verifies against provider state before committing the terminal payment result.

## Deployment requirements
- merchant credential injected from a secret manager
- outbound TLS verification
- public HTTPS callback endpoint
- durable transaction state
- duplicate callback handling
- provider timeout/retry policy
- reconciliation job
- provider contract/test-account validation

Live activation remains environment-specific.
