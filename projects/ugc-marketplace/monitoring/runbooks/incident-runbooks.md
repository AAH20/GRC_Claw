# Incident Response Runbooks for UGC Marketplace

## Runbook: API Service Down

### Alert: APIServiceDown
**Severity:** Critical
**Detection:** `up{job="ugc-marketplace-api"} == 0` for 30s

### Immediate Actions (First 5 minutes)

1. **Verify the alert**
   ```bash
   curl -s http://localhost:8000/api/v1/health
   curl -s http://localhost:9090/api/v1/query?query=up{job="ugc-marketplace-api"}
   ```

2. **Check service status**
   ```bash
   docker-compose ps api
   docker logs --tail 100 api
   kubectl get pods -l app=ugc-marketplace-api
   kubectl describe pod -l app=ugc-marketplace-api
   ```

3. **Check recent deployments**
   ```bash
   # Check if a recent deployment caused the issue
   kubectl rollout history deployment/ugc-marketplace-api
   kubectl rollout status deployment/ugc-marketplace-api
   ```

4. **Check resource utilization**
   ```bash
   kubectl top pod -l app=ugc-marketplace-api
   # Check if OOMKilled
   kubectl get pod -l app=ugc-marketplace-api -o jsonpath='{.items[0].status.containerStatuses[0].lastState}'
   ```

### Recovery Steps

**If OOMKilled:**
```bash
# Increase memory limit
kubectl set resources deployment/ugc-marketplace-api --containers=api --limits=memory=2Gi --requests=memory=1Gi
# Or scale horizontally
kubectl scale deployment/ugc-marketplace-api --replicas=3
```

**If crash looping:**
```bash
# Check error logs
kubectl logs -l app=ugc-marketplace-api --tail=200
# Rollback to previous version
kubectl rollout undo deployment/ugc-marketplace-api
```

**If resource exhaustion:**
```bash
# Scale up
kubectl scale deployment/ugc-marketplace-api --replicas=5
# Check HPA
kubectl get hpa ugc-marketplace-api
```

### Escalation
- If not resolved in 15 minutes: Escalate to Platform Team Lead
- If not resolved in 30 minutes: Escalate to Engineering Manager
- If data loss suspected: Escalate to DBA Team

### Post-Incident
- [ ] Document timeline in incident tracker
- [ ] Identify root cause
- [ ] Create follow-up tickets for preventive measures
- [ ] Update runbook if gaps found

---

## Runbook: High Error Rate

### Alert: HighErrorRate
**Severity:** Critical
**Detection:** 5xx rate > 5% for 2 minutes

### Immediate Actions

1. **Identify affected endpoints**
   ```bash
   # Check which endpoints are returning 5xx
   curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(http_requests_total{job="ugc-marketplace-api",status=~"5.."}[5m])) by (path)'
   ```

2. **Check error logs**
   ```bash
   # Search for recent errors in Kibana
   # Index: ugc-marketplace-*
   # Query: level:ERROR AND @timestamp:[now-10m TO now]
   ```

3. **Check database connectivity**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=up{job="postgres-exporter"}'
   curl -s 'http://localhost:9090/api/v1/query?query=pg_stat_activity_count'
   ```

4. **Check Redis connectivity**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=up{job="redis-exporter"}'
   ```

5. **Check Kafka connectivity**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=up{job="kafka-exporter"}'
   ```

### Recovery Steps

**If database issue:**
- Check for long-running queries: `SELECT * FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '5 minutes';`
- Kill blocking queries if necessary
- Check connection pool exhaustion

**If Redis issue:**
- Check memory usage: `redis-cli INFO memory`
- Check for evictions: `redis-cli INFO stats | grep evicted`
- Consider restarting Redis if memory is full

**If Kafka issue:**
- Check consumer lag: `kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --all-groups`
- Check for offline partitions
- Restart consumers if needed

**If code issue:**
- Rollback to previous stable version
- Enable feature flags to disable problematic features

### Escalation
- If not resolved in 10 minutes: Escalate to Platform Team
- If data corruption suspected: Escalate to Data Team immediately

---

## Runbook: Database Down

### Alert: DatabaseDown
**Severity:** Critical
**Detection:** `up{job="postgres-exporter"} == 0` for 30s

### Immediate Actions

1. **Verify database status**
   ```bash
   docker-compose ps db
   docker logs --tail 100 db
   pg_isready -U postgres -h localhost
   ```

2. **Check disk space**
   ```bash
   df -h /var/lib/postgresql/data
   # If disk full, check for large WAL files
   du -sh /var/lib/postgresql/data/pg_wal/
   ```

3. **Check connections**
   ```bash
   psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
   psql -U postgres -c "SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';"
   ```

### Recovery Steps

**If disk full:**
```bash
# Clean up old WAL files
# Archive and vacuum
psql -U postgres -c "VACUUM FULL;"
# If needed, increase disk size
```

**If too many connections:**
```bash
# Kill idle connections
psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '1 hour';"
# Increase max_connections if needed
```

**If PostgreSQL won't start:**
```bash
# Check logs
cat /var/lib/postgresql/data/log/postgresql-*.log
# Try recovery mode
pg_ctl start -D /var/lib/postgresql/data -o "-c recovery_target=immediate"
```

### Escalation
- If not resolved in 5 minutes: Escalate to DBA Team
- If data loss suspected: Escalate to Engineering Manager + DBA Team

---

## Runbook: High Latency

### Alert: HighLatencyP99
**Severity:** Critical
**Detection:** P99 latency > 5s for 5 minutes

### Immediate Actions

1. **Identify slow endpoints**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="ugc-marketplace-api"}[5m])) by (le, path))'
   ```

2. **Check for slow database queries**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=rate(pg_slow_queries_total[5m])'
   ```

3. **Check Jaeger for trace analysis**
   - Open Jaeger UI: http://localhost:16686
   - Search for slow traces
   - Identify bottleneck spans

### Recovery Steps

**If database slow:**
- Check for missing indexes
- Check for lock contention
- Consider read replicas for read-heavy workloads

**If external API slow:**
- Check if LLM API (OpenAI) is slow
- Consider circuit breaker pattern
- Add caching for external API responses

**If resource constrained:**
- Scale up API instances
- Increase CPU/memory limits
- Check for noisy neighbors

---

## Runbook: Kafka Consumer Lag

### Alert: KafkaConsumerLag
**Severity:** Warning
**Detection:** Consumer lag > 10,000 for 5 minutes

### Immediate Actions

1. **Identify affected consumer groups**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=kafka_consumergroup_lag'
   ```

2. **Check consumer status**
   ```bash
   kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --all-groups
   ```

3. **Check consumer logs**
   ```bash
   kubectl logs -l app=ugc-marketplace-consumer --tail=200
   ```

### Recovery Steps

**If consumers are down:**
```bash
# Restart consumer deployments
kubectl scale deployment/ugc-marketplace-consumer --replicas=0
kubectl scale deployment/ugc-marketplace-consumer --replicas=3
```

**If consumers are slow:**
```bash
# Scale up consumers
kubectl scale deployment/ugc-marketplace-consumer --replicas=10
# Check partition assignment
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group <group>
```

**If processing is stuck:**
```bash
# Check for poison pill messages
# Consider skipping problematic messages
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group <group> --topic <topic> --reset-offsets --to-latest --execute
```

---

## Runbook: Moderation Queue Backlog

### Alert: ModerationQueueBacklog
**Severity:** Warning
**Detection:** `moderation_queue_depth > 500` for 10 minutes

### Immediate Actions

1. **Check queue depth**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=moderation_queue_depth'
   ```

2. **Check moderation service status**
   ```bash
   kubectl get pods -l app=ugc-marketplace-moderation
   kubectl logs -l app=ugc-marketplace-moderation --tail=100
   ```

3. **Check LLM API status**
   - Moderation uses LLM for content analysis
   - Check if OpenAI API is experiencing issues

### Recovery Steps

**If moderation service is down:**
```bash
kubectl scale deployment/ugc-marketplace-moderation --replicas=0
kubectl scale deployment/ugc-marketplace-moderation --replicas=3
```

**If LLM API is slow:**
- Consider fallback to rule-based moderation
- Reduce sampling rate
- Add request queuing with backoff

**If queue is growing:**
```bash
# Scale up moderation workers
kubectl scale deployment/ugc-marketplace-moderation --replicas=10
# Check for poison pill messages
```

---

## Runbook: Fraud Detection Spike

### Alert: HighFraudDetectionRate
**Severity:** Critical
**Detection:** Fraud detection rate > 15% for 10 minutes

### Immediate Actions

1. **Check fraud detection metrics**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(ugc_fraud_detection_total[10m])) by (detection_type)'
   ```

2. **Check for false positives**
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=sum(rate(ugc_content_appeals_total{outcome="overturned"}[1h])) / sum(rate(ugc_content_appeals_total[1h]))'
   ```

3. **Check recent model deployments**
   ```bash
   kubectl rollout history deployment/ugc-marketplace-fraud-detection
   ```

### Recovery Steps

**If false positive rate is high:**
- Rollback model to previous version
- Adjust detection thresholds
- Enable manual review for borderline cases

**If actual fraud spike:**
- Enable stricter rate limiting
- Increase fraud detection sensitivity
- Notify Trust & Safety team

**If model is misbehaving:**
```bash
# Rollback model
kubectl rollout undo deployment/ugc-marketplace-fraud-detection
# Or disable ML-based detection and use rule-based only
```

---

## Runbook: Disk Will Fill Soon

### Alert: DiskWillFillIn4Hours
**Severity:** Critical
**Detection:** `predict_linear(node_filesystem_avail_bytes[6h], 4 * 3600) < 0` for 1h

### Immediate Actions

1. **Check disk usage**
   ```bash
   df -h
   du -sh /var/lib/docker/*
   docker system df
   ```

2. **Check large files**
   ```bash
   find / -type f -size +1G 2>/dev/null
   ```

### Recovery Steps

**Clean up Docker resources:**
```bash
# Remove unused images
docker image prune -a --filter "until=168h"
# Remove unused volumes
docker volume prune
# Remove build cache
docker builder prune
```

**Clean up old logs:**
```bash
# Truncate large log files
find /var/log -type f -size +100M -exec truncate -s 0 {} \;
```

**If database is large:**
```bash
# Archive old data
# Run VACUUM FULL
psql -U postgres -c "VACUUM FULL;"
```

**If persistent volume is too small:**
- Increase PV size
- Migrate to larger storage

---

## Runbook: Log Pipeline Down

### Alert: LogPipelineDown
**Severity:** Critical
**Detection:** `up{job="fluentd"} == 0` for 1m

### Immediate Actions

1. **Check Fluentd status**
   ```bash
   docker-compose ps fluentd
   docker logs --tail 100 fluentd
   ```

2. **Check Elasticsearch status**
   ```bash
   curl -s http://localhost:9200/_cluster/health
   curl -s http://localhost:9200/_cat/indices?v
   ```

### Recovery Steps

**If Fluentd is down:**
```bash
docker-compose restart fluentd
# Check buffer files
ls -la /var/log/fluent/buffer/
```

**If Elasticsearch is down:**
```bash
# Check ES logs
docker logs elasticsearch
# Check disk space (ES won't start if disk > 90%)
df -h
# Increase heap size if OOM
```

**If logs are not appearing in Kibana:**
- Check index pattern: Management → Index Patterns → ugc-marketplace-*
- Check Fluentd buffer queue: `curl -s http://localhost:24231/metrics`
- Verify Elasticsearch connection: `curl -s http://localhost:9200/_cat/indices?v`

---

## Runbook: Jaeger Tracing Down

### Alert: JaegerAgentDown
**Severity:** Warning
**Detection:** `up{job="jaeger"} == 0` for 1m

### Immediate Actions

1. **Check Jaeger status**
   ```bash
   curl -s http://localhost:14269/
   curl -s http://localhost:16686/
   ```

2. **Check Jaeger collector**
   ```bash
   kubectl get pods -l app=jaeger
   kubectl logs -l app=jaeger-collector --tail=100
   ```

### Recovery Steps

**If Jaeger collector is down:**
```bash
kubectl scale deployment/jaeger-collector --replicas=0
kubectl scale deployment/jaeger-collector --replicas=1
```

**If Elasticsearch storage is full:**
```bash
# Check Jaeger indices
curl -s http://localhost:9200/_cat/indices?v | grep jaeger
# Delete old indices
curl -X DELETE http://localhost:9200/jaeger-span-$(date -d '7 days ago' +%Y-%m-%d)
```

**If traces are not appearing:**
- Check sampling configuration
- Verify application instrumentation
- Check Jaeger agent connectivity
