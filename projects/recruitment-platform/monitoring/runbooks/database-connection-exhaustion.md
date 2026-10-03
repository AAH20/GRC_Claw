# Runbook: Database Connection Exhaustion

## Trigger
- Alert: `db_connections_active / db_connections_max > 0.85` for 3 minutes
- Severity: P1

## Diagnosis
1. Check active connections: `SELECT count(*) FROM pg_stat_activity;`
2. Identify long-running queries: `SELECT * FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '30 seconds';`
3. Check connection pool metrics in Prometheus
4. Review recent schema changes or migrations

## Mitigation
1. Kill idle connections: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '10 minutes';`
2. Increase pool size temporarily: update `DB_POOL_MAX` env var
3. If connection leak suspected: restart affected pods
4. Enable PgBouncer transaction mode if not already active

## Escalation
- Page DBA if connections cannot be freed
- Consider read replica for read-heavy workloads

## Post-Incident
- Audit connection pool configuration
- Add connection leak detection
- Review connection timeout settings
