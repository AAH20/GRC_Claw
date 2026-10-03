# Runbook: High Error Rate

## Trigger
- Alert: `error_rate > 5%` for 5 consecutive minutes
- Severity: P1

## Diagnosis
1. Check Kibana dashboard: `recruitment-logs-*` filtered by `level:ERROR`
2. Identify top error patterns via aggregation on `msg` field
3. Check Jaeger for failing trace spans — look for error tags
4. Review recent deployments: `kubectl rollout history deployment/`

## Mitigation
1. If error rate > 20%: rollback last deployment
2. If specific service failing: scale replicas `kubectl scale deployment/<svc> --replicas=5`
3. If database connection pool exhausted: increase pool size in config
4. If downstream dependency failing: enable circuit breaker

## Escalation
- Page on-call engineer if not resolved in 15 minutes
- Engage service owner if error persists > 30 minutes

## Post-Incident
- Document root cause in incident tracker
- Add regression test for failure mode
- Update alert thresholds if needed
