# Reference Production Deployment Profile

```
Internet -> WAF/TLS -> API -> queue -> workers -> PostgreSQL
                         \-> callback ingress -> provider verification
API/workers -> provider adapter -> PSP/bank
```

Minimum production profile:
- two API instances
- two workers
- PostgreSQL with tested backups
- separate callback ingress
- secret manager
- centralized logs/metrics
- alerting
- restore procedure

Provider credentials are never exposed to browser clients or discovery metadata. HA is a deployment property and must be tested in the target environment.