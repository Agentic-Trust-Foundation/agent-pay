# V2 Virtual Cards

Virtual cards are an instrument profile, not an authority source.

Lifecycle:
REQUESTED -> PROVISIONED -> ACTIVE -> SUSPENDED -> EXPIRED/REVOKED.

Rules:
- card material never enters agent prompts or discovery metadata
- instrument is bound to an account/policy context
- dynamic limits cannot exceed upstream financial policy
- provider/issuer references are stored separately from sensitive card material
- lifecycle events are auditable
- revocation is fail-closed for new execution