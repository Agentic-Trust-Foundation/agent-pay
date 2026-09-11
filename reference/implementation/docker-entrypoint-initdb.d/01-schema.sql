-- Local reference stack bootstrap.
-- The official postgres image executes this on first database initialization.
\i /docker-entrypoint-initdb.d/10-base-schema.sql
\i /docker-entrypoint-initdb.d/20-stage4-convergence.sql
\i /docker-entrypoint-initdb.d/30-ledger-accounts.sql
