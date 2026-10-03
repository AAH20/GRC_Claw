# Runbook: Memory Leak Detection

## Trigger
- Alert: `container_memory_usage_bytes > 80%` for 10 minutes with upward trend
- Severity: P2

## Diagnosis
1. Check memory usage trend in Prometheus: `rate(container_memory_usage_bytes[1h])`
2. Compare across replicas to isolate affected instance
3. Check GC logs in Kibana for increasing pause times
4. Review recent code changes for object retention patterns

## Mitigation
1. Restart affected pod: `kubectl delete pod/<pod-name>`
2. If leak confirmed: capture heap dump before restart
   - `kubectl exec <pod> -- jmap -dump:format=b,file=/tmp/heap.hprof <pid>`
3. Scale horizontally to maintain capacity during investigation
4. Rollback recent deployment if leak correlates with release

## Escalation
- Engage service owner with heap dump for analysis
- If leak rate > 10MB/hour: escalate to P1

## Post-Incident
- Analyze heap dump with Eclipse MAT or similar
- Add memory profiling to CI pipeline
- Set memory limits with headroom for growth
