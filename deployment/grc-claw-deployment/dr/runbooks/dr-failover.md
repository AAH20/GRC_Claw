# GRC_Claw Disaster Recovery - Failover Runbook

## Overview
This runbook covers the procedures for failing over GRC_Claw from the primary region to the DR region.

## Prerequisites
- [ ] DR cluster is running and healthy
- [ ] Cross-region replication is operational
- [ ] ArgoCD is configured for DR cluster
- [ ] DNS is configured for failover
- [ ] On-call engineer has access to all systems

## RTO/RPO Targets
- **RTO**: < 4 hours
- **RPO**: < 30 minutes

## Failover Procedures

### Scenario 1: Single Component Failure (Automatic)
**Detection**: Kubernetes health checks, Istio outlier detection
**Recovery Time**: < 2 minutes

1. Kubernetes detects failure (liveness probe fails)
2. Pod rescheduled to healthy node (< 2 minutes)
3. Istio reroutes traffic to healthy instances (< 5 seconds)
4. Alert fired to on-call engineer
5. Post-incident review scheduled

### Scenario 2: Zone Failure (Automatic)
**Detection**: Load balancer health checks
**Recovery Time**: < 15 minutes

1. Load balancer detects zone failure
2. Traffic routed to remaining zones (< 30 seconds)
3. HPA scales up replicas in remaining zones (< 5 minutes)
4. Patroni promotes PostgreSQL replica in healthy zone (< 30 seconds)
5. Redis Sentinel promotes replica (< 10 seconds)
6. Kafka reassigns partitions (< 2 minutes)
7. Alert fired to on-call engineer

### Scenario 3: Region Failure (Manual)
**Detection**: GSLB health check failure
**Recovery Time**: < 4 hours

#### Step 1: Declare Region Failure
```bash
# Verify primary region is actually down
curl -s https://prod-us-east-1.grc-claw.internal/healthz
# Confirm with cloud provider status page

# Declare incident
incident create --severity P1 --title "Region Failure: us-east-1"
```

#### Step 2: Promote DR Cluster
```bash
# Scale up microservices in DR region
kubectl --context dr-us-west-2 scale deployment pdp-service --replicas=3 -n grc-claw-control-plane
kubectl --context dr-us-west-2 scale deployment pep-gateway --replicas=3 -n grc-claw-control-plane
kubectl --context dr-us-west-2 scale deployment policy-api --replicas=3 -n grc-claw-control-plane
kubectl --context dr-us-west-2 scale deployment agent-identity --replicas=3 -n grc-claw-control-plane
kubectl --context dr-us-west-2 scale deployment evidence-collector --replicas=3 -n grc-claw-evidence
```

#### Step 3: Promote Data Stores
```bash
# PostgreSQL: Promote replica to primary
kubectl --context dr-us-west-2 exec -it postgresql-0 -- pg_ctl promote

# Redis: Promote replica
kubectl --context dr-us-west-2 exec -it redis-0 -- redis-cli SLAVEOF NO ONE

# Kafka: Reverse MirrorMaker2
kubectl --context dr-us-west-2 apply -f dr/kafka-mm2-reverse.yaml

# MinIO: Reverse bucket replication
mc replicate reverse dr-minio/evidence grc-claw-evidence

# Vault: Promote performance replica
vault operator step-down  # On primary (if reachable)
vault operator raft promote  # On DR
```

#### Step 4: Update DNS
```bash
# Update Route 53 / Cloudflare DNS
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch file://dr/dns-failover.json

# Verify DNS propagation
dig grc-claw.internal
```

#### Step 5: Verify Services
```bash
# Check all pods are running
kubectl --context dr-us-west-2 get pods -A

# Run smoke tests
./scripts/smoke-tests.sh dr

# Verify enforcement decisions
curl -X POST https://grc-claw.internal/api/v1/enforce \
  -H "Content-Type: application/json" \
  -d '{"action": "test", "agent": "dr-test"}'
```

#### Step 6: Notify Stakeholders
```bash
# Update status page
statuspage update --status degraded --message "Failover to DR region in progress"

# Notify Slack
slack post --channel "#incidents" --message "DR failover initiated for us-east-1"
```

## Failback Procedures
1. Verify primary region is healthy
2. Sync data from DR to primary
3. Update DNS to point back to primary
4. Scale down DR microservices
5. Verify all services operational
6. Close incident

## Testing Schedule
| Test | Frequency | Scope | Success Criteria |
|------|-----------|-------|------------------|
| Component failure | Weekly | Kill single pod | Recovery < 2 min, zero data loss |
| Zone failure | Monthly | Simulate zone loss | Recovery < 15 min, RPO < 5 min |
| Region failure | Quarterly | Full region failover | RTO < 4 hours, RPO < 30 min |
| Backup restore | Monthly | Restore to staging | Data integrity verified |
| Chaos engineering | Monthly | Random component kills | Graceful degradation |
