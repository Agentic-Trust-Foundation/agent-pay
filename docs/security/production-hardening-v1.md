# Production Security Hardening V1

Required before production:
- TLS validation
- authenticated service-to-service calls
- cryptographic ATF evidence verification
- real revocation source
- secret manager
- key rotation
- replay protection
- durable idempotency
- rate limiting
- SSRF-safe metadata retrieval
- least-privilege database access
- encrypted backups
- dependency/SBOM scanning
- redacted structured logs
- incident response
- restore testing

Evidence is verified again at the Agent-Pay boundary. Payment/provider secrets never enter discovery manifests, agent prompts, ordinary logs, or client-side state.