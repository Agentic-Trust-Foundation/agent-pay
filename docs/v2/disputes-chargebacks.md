# V2 Disputes and Chargebacks

A dispute is a separate lifecycle from the original payment.

Required references:
- payment ID
- provider reference
- dispute/case ID
- evidence bundle reference
- deadlines
- state history
- settlement impact

States:
OPEN -> EVIDENCE_REQUIRED -> SUBMITTED -> PROVIDER_REVIEW -> WON/LOST/CLOSED.

Corrections use explicit journal entries; historical payment evidence is never rewritten.