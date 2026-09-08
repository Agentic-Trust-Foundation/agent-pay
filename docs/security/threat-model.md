# Threat Model

## Assets

- Funds
- Spending limits and policies
- Payment instruments
- Authorization evidence
- Transaction state
- Settlement state
- Financial ledger
- Sensitive merchant and user data

## Threats

### Agent impersonation
An attacker acts as an authorized agent. Mitigations include strong identity binding and verifiable authority evidence.

### Replay
A valid payment request is reused. Mitigations include unique request identifiers, freshness constraints, idempotency, and replay detection.

### Privilege escalation
An agent attempts to spend beyond delegated or financial limits. Mitigations include independent trust and spending-policy evaluation.

### Confused deputy
An agent causes a more privileged payment service to perform an unintended operation. Mitigations include explicit intent binding and resource/action constraints.

### Policy bypass
A transaction reaches a payment rail without passing required policy or approval checks. The execution boundary must fail closed.

### Duplicate execution
Retries produce multiple financial transactions. Payment operations require idempotency and durable transaction state.

### Ledger integrity failure
Financial truth diverges from payment execution. Ledger events must be append-oriented, traceable, and reconciled with external settlement state.

### Compromised agent
An authorized agent becomes malicious. Authority must remain bounded by delegation and spending policies, with rapid revocation and anomaly controls.
