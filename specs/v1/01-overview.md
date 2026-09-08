# v1 Overview

## Status

Draft architecture and protocol planning document. Not normative.

## Design goals

- Permit agents to request financial operations safely.
- Keep financial authority bounded and explicit.
- Separate trust authorization from spending authorization.
- Support automatic, notification, and human-approved execution.
- Support multiple payment instruments and rails.
- Make transaction state and financial outcomes auditable.
- Preserve interoperability across independent implementations.

## Decision pipeline

```text
Payment Intent
  -> Authority Evidence Check
  -> Spending Policy
  -> Risk
  -> Approval
  -> Payment Decision
  -> Execution
  -> Transaction
  -> Settlement
  -> Ledger
```
