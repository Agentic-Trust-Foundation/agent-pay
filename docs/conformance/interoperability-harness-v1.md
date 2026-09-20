# V1 Interoperability Harness

Participants:
- ATF evidence producer/verifier
- Site Adapter integration
- Agent-Pay verifier
- provider test adapter
- negative-test runner

Scenarios:
1. valid bounded authority
2. missing/expired/revoked authority
3. wrong audience/resource
4. amount over limit
5. consent mismatch
6. duplicate payment request
7. duplicate callback
8. provider timeout
9. verification mismatch
10. reconciliation mismatch
11. worker restart
12. stale authorization context

Each scenario records expected decision/state and evidence.