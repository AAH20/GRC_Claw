# GRC_Claw Disaster Recovery Runbook

## Overview

This runbook covers disaster recovery procedures for GRC_Claw, including component failure, zone failure, and region failure scenarios.

## Recovery Objectives

| Data Store | RPO | RTO | Replication | Failover |
|-----------|-----|-----|-------------|----------|
| PostgreSQL (policies, enforcement) | ≤ 5 min | ≤ 1 hour | Synchronous streaming | Automatic (Patroni) |
| PostgreSQL (analytics) | ≤ 30 min | ≤ 4 hours | Asynchronous streaming | Manual |
| Redis (cache, sessions) | ≤ 1 min | ≤ 5 min | Sentinel async | Automatic |
| Kafka (events) | ≤ 1 sec | ≤ 15 min | MirrorMaker2 | Automatic |
| MinIO (WORM evidence) | ≤ 30 min | ≤ 4 hours | Bucket replication | Manual |
| Neo4j (graph) | ≤ 30 min | ≤ 4 hours | Causal cluster | Automatic |
| immudb (audit) | ≤ 5 min | ≤ 1 hour | Read replica | Manual |
| Vault (secrets) | ≤ 1 min | ≤ 15 min | Performance replica | Automatic |

---

## Scenario 1: Single Component Failure (Automatic)

### Detection
- Kubernetes liveness probe fails (3 consecutive failures)
- Pod status changes to `CrashLoopBackOff` or `Error`

### Recovery Steps
1. Kubernetes detects failure via liveness probe
2. Pod rescheduled to healthy node (< 2 minutes)
3. Istio reroutes traffic to healthy instances (< 5 seconds)
4. Alert fired to on-call engineer via PagerDuty
5. Post-incident review scheduled

### Verification
```bash
# Check pod status
kubectl get pods -n grc-claw-control-plane -l app=pdp-service

# Check service endpoints
kubectl get endpoints -n grc-claw-control-plane pdp-service

# Check Istio routing
istioctl proxy-config routes deploy/pdp-service -n grc-claw-control-plane
```

---

## Scenario 2: Zone Failure (Automatic)

### Detection
- Load balancer health checks fail for zone
- Multiple pods in same zone become unavailable

### Recovery Steps
1. Load balancer detects zone failure
2. Traffic routed to remaining zones (< 30 seconds)
3. HPA scales up replicas in remaining zones (< 5 minutes)
4. Patroni promotes PostgreSQL replica in healthy zone (< 30 seconds)
5. Redis Sentinel promotes replica (< 10 seconds)
6. Kafka reassigns partitions (< 2 minutes)
7. Alert fired to on-call engineer

### Verification
```bash
# Check node status
kubectl get nodes --label-columns=topology.kubernetes.io/zone

# Check pod distribution
kubectl get pods -n grc-claw-control-plane -o wide --sort-by='.spec.nodeName'

# Check Patroni cluster
kubectl exec -it postgresql-0 -n grc-claw-data -- patronictl list

# Check Redis cluster
kubectl exec -it redis-0 -n grc-claw-data -- redis-cli cluster info

# Check Kafka partition status
kubectl exec -it kafka-0 -n grc-claw-data -- kafka-topics.sh --describe --bootstrap-server localhost:9092
```

---

## Scenario 3: Region Failure (Manual)

### Prerequisites
- DR cluster is running with data services (microservices scaled to 0)
- Cross-region replication is healthy
- Runbook is accessible

### Recovery Steps

#### Step 1: Declare Region Failure
```bash
# Update DNS to point to DR region
aws route53 change-resource-record-sets   --hosted-zone-id Z123456789   --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.grc-claw.internal",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "dr-lb.us-west-2.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

#### Step 2: Promote DR Cluster
```bash
# Scale up microservices in DR region
kubectl --context dr-us-west-2 scale deployment pdp-service -n grc-claw-control-plane --replicas=3
kubectl --context dr-us-west-2 scale deployment pep-gateway -n grc-claw-control-plane --replicas=3
kubectl --context dr-us-west-2 scale deployment policy-api -n grc-claw-control-plane --replicas=3
kubectl --context dr-us-west-2 scale deployment agent-identity -n grc-claw-control-plane --replicas=3
kubectl --context dr-us-west-2 scale deployment evidence-collector -n grc-claw-evidence --replicas=3
kubectl --context dr-us-west-2 scale deployment compliance-mapping -n grc-claw-evidence --replicas=2
kubectl --context dr-us-west-2 scale deployment analytics-engine -n grc-claw-analytics --replicas=2
kubectl --context dr-us-west-2 scale deployment reporting-engine -n grc-claw-analytics --replicas=2
```

#### Step 3: Promote PostgreSQL Replica
```bash
# Promote PostgreSQL replica to primary in DR
kubectl --context dr-us-west-2 exec -it postgresql-0 -n grc-claw-data -- \
  patronictl failover grc-claw-db --group 0 --force

# Verify promotion
kubectl --context dr-us-west-2 exec -it postgresql-0 -n grc-claw-data -- \
  patronictl list grc-claw-db
```

#### Step 4: Promote Redis Replica
```bash
# Redis Sentinel should auto-promote; verify
kubectl --context dr-us-west-2 exec -it redis-0 -n grc-claw-data -- \
  redis-cli -p 26379 sentinel get-master-addr-by-name mymaster
```

#### Step 5: Reverse Kafka MirrorMaker2
```bash
# Stop MirrorMaker2
kubectl --context dr-us-west-2 scale deployment mirror-maker-2 -n grc-claw-data --replicas=0

# Promote DR Kafka to primary
kubectl --context dr-us-west-2 exec -it kafka-0 -n grc-claw-data -- \
  kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --entity-default --alter --add-config min.insync.replicas=2
```

#### Step 6: Promote MinIO Bucket Replication
```bash
# Reverse bucket replication direction
mc replicate reverse dr-minio/evidence-bucket --remote arn:minio:primary
```

#### Step 7: Promote Vault Performance Replica
```bash
# Vault should auto-promote; verify
kubectl --context dr-us-west-2 exec -it vault-0 -n grc-claw-data -- \
  vault operator raft list-peers
```

#### Step 8: Verify Services
```bash
# Check all pods are running
kubectl --context dr-us-west-2 get pods -n grc-claw-control-plane
kubectl --context dr-us-west-2 get pods -n grc-claw-evidence
kubectl --context dr-us-west-2 get pods -n grc-claw-analytics

# Check service health
curl -s https://api.grc-claw.internal/healthz
curl -s https://api.grc-claw.internal/readyz

# Check ArgoCD sync status
argocd app list
```

### Total RTO: < 4 hours

---

## Backup Verification

### PostgreSQL (pgBackRest)
```bash
# Verify latest backup
pgbackrest --stanza=grc-claw info

# Test restore to staging
pgbackrest --stanza=grc-claw restore --type=time --target="2026-10-01 12:00:00" --target-action=promote
```

### Redis
```bash
# Verify RDB snapshot exists
kubectl exec -it redis-0 -n grc-claw-data -- ls -la /data/dump.rdb

# Test restore
kubectl exec -it redis-0 -n grc-claw-data -- redis-cli restore key 0 /data/dump.rdb
```

### Kafka
```bash
# Verify topic snapshot
aws s3 ls s3://grc-claw-backups/kafka-snapshots/

# Test restore
kafka-replica-verification.sh --bootstrap-server kafka:9092 --topic evidence-events
```

### MinIO
```bash
# Verify object versioning
mc ls --versions dr-minio/evidence-bucket/

# Test restore
mc cp dr-minio/evidence-bucket/audit-2026-10-01.json /tmp/restore-test/
```

### immudb
```bash
# Verify backup
kubectl exec -it immudb-0 -n grc-claw-data -- immuadmin backup

# Test restore
kubectl exec -it immudb-0 -n grc-claw-data -- immuadmin restore /var/lib/immudb/backup/
```

---

## DR Testing Schedule

| Test | Frequency | Scope | Success Criteria |
|------|-----------|-------|------------------|
| Component failure | Weekly | Kill single pod | Recovery < 2 min, zero data loss |
| Zone failure | Monthly | Simulate zone loss | Recovery < 15 min, RPO < 5 min |
| Region failure | Quarterly | Full region failover | RTO < 4 hours, RPO < 30 min |
| Backup restore | Monthly | Restore to staging | Data integrity verified |
| Chaos engineering | Monthly | Random component kills | Graceful degradation |

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| On-call Engineer | PagerDuty | https://grc-claw.pagerduty.com |
| Platform Lead | TBD | TBD |
| Security Team | TBD | TBD |
| Management | TBD | TBD |
