# Broker Enablement — Troubleshooting Guide

> **Project:** `broker-enablement`
> **Description:** Multi-tenant AI-powered broker enablement platform for training, compliance, and performance tracking.
> **Last Updated:** 2026-10-02

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Common Issues & Solutions](#common-issues--solutions)
4. [Debugging Steps](#debugging-steps)
5. [Preventive Measures](#preventive-measures)
6. [Escalation Procedures](#escalation-procedures)
7. [Additional Resources](#additional-resources)

---

## Overview

This troubleshooting guide covers the most common issues encountered when operating the **Broker Enablement** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

### Quick Health Check

```bash
# Check overall system health
curl -s http://localhost:8080/api/v1/health | jq .

# Check agent status
curl -s http://localhost:8080/api/v1/agents/status | jq .

# Check recent errors
curl -s "http://localhost:8080/api/v1/logs?level=error&limit=20" | jq .
```

---

## Architecture

### Core Agents

| Agent | Role | Health Endpoint |
|-------|------|-----------------|
| Training Agent | Training Agent | `/api/v1/agents/training-agent/health` |
| Compliance Monitor | Compliance Monitor | `/api/v1/agents/compliance-monitor/health` |
| Performance Tracker | Performance Tracker | `/api/v1/agents/performance-tracker/health` |
| Content Curator | Content Curator | `/api/v1/agents/content-curator/health` |
| Communication Agent | Communication Agent | `/api/v1/agents/communication-agent/health` |

### Key Integrations

- **LMS Platforms**
- **CRM Systems**
- **Compliance Databases**
- **Document Management**
- **Communication Platforms**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Multi-tenant data isolation breaches

**Symptoms:**
- Broker seeing another tenant's data
- Cross-tenant reporting errors
- Permission escalation vulnerabilities

**Solutions:**
1. Verify tenant isolation in database queries
1. Check RBAC implementation
1. Validate API tenant context propagation
1. Review data access audit logs

**Debugging Steps:**
```bash
Check tenant context: GET /api/v1/broker/tenant-context
```

```bash
Verify RBAC policies: GET /api/v1/broker/rbac
```

```bash
Test data isolation: POST /api/v1/broker/isolation-test
```

```bash
Review access logs: GET /api/v1/broker/access-logs
```

---

### Issue 2: Training content not personalizing

**Symptoms:**
- All brokers receiving same content
- Skill gap analysis inaccurate
- Learning path not adapting

**Solutions:**
1. Verify broker profile data completeness
1. Check personalization algorithm
1. Validate skill assessment accuracy
1. Review content tagging system

**Debugging Steps:**
```bash
Check broker profiles: GET /api/v1/broker/profiles
```

```bash
Test personalization: POST /api/v1/broker/personalization/test
```

```bash
Verify skill assessment: GET /api/v1/broker/skills
```

```bash
Review content tags: GET /api/v1/broker/content-tags
```

---

### Issue 3: Compliance tracking gaps

**Symptoms:**
- Expired certifications not flagged
- Compliance deadlines missed
- Audit trail incomplete

**Solutions:**
1. Verify certification expiry tracking
1. Check compliance rule engine
1. Validate notification system
1. Review audit logging completeness

**Debugging Steps:**
```bash
Check certifications: GET /api/v1/broker/certifications
```

```bash
Verify compliance rules: GET /api/v1/broker/compliance-rules
```

```bash
Test notifications: POST /api/v1/broker/notifications/test
```

```bash
Review audit trail: GET /api/v1/broker/audit-trail
```

---

## Debugging Steps

### General Diagnostic Procedure

1. **Identify the symptom** — Determine which of the common issues above matches the observed behavior.
2. **Check system health** — Run the quick health check commands to verify overall system status.
3. **Review logs** — Examine application logs for error patterns and stack traces.
4. **Verify integrations** — Test connectivity to all external services and APIs.
5. **Isolate the component** — Narrow down whether the issue is in the agent, API, data layer, or integration.
6. **Apply the solution** — Follow the specific solution steps for the identified issue.
7. **Verify resolution** — Confirm the issue is resolved and monitor for recurrence.

### Log Analysis

```bash
# View recent application logs
docker logs --tail 500 broker-enablement-app

# Filter for errors
docker logs broker-enablement-app 2>&1 | grep -i error

# Search for specific patterns
docker logs broker-enablement-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs broker-enablement-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats broker-enablement-app

# Check database connection pool
curl -s http://localhost:8080/api/v1/db/pool-status | jq .

# Check cache hit rates
curl -s http://localhost:8080/api/v1/cache/stats | jq .

# Profile agent execution time
curl -s http://localhost:8080/api/v1/agents/execution-times | jq .
```

### Network Diagnostics

```bash
# Test external API connectivity
curl -s -o /dev/null -w "%{http_code}" https://api.example.com/health

# Check DNS resolution
dig +short api.example.com

# Verify firewall rules
sudo iptables -L -n | grep 8080

# Test database connectivity
psql -h localhost -U broker-enablement -d broker-enablement_db -c "SELECT 1"
```

---

## Preventive Measures

### Monitoring & Alerting

- Set up health check endpoints with automated alerting
- Monitor agent execution times and failure rates
- Track API response times and error rates
- Alert on resource utilization thresholds (CPU > 80%, memory > 85%)
- Monitor queue depths and processing lag

### Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| Log rotation | Daily | `logrotate /etc/logrotate.d/broker-enablement` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull broker-enablement:latest` |
| Backup verification | Weekly | `/opt/scripts/verify-backup.sh` |

### Configuration Management

- Version control all configuration files
- Use environment-specific config overrides
- Implement configuration validation on startup
- Maintain configuration change audit trail
- Use feature flags for gradual rollouts

---

## Escalation Procedures

### Severity Levels

| Level | Description | Response Time | Escalation Path |
|-------|-------------|---------------|-----------------|
| P1 — Critical | System down or data loss | 15 minutes | On-call → Engineering Lead → CTO |
| P2 — High | Major feature impaired | 1 hour | On-call → Engineering Lead |
| P3 — Medium | Minor feature issue | 4 hours | Support → Engineering |
| P4 — Low | Cosmetic or enhancement | 24 hours | Support queue |

### Escalation Contacts

- **L1 Support:** support@grc-claw.com
- **L2 Engineering:** engineering@grc-claw.com
- **L3 On-Call:** oncall@grc-claw.com
- **Emergency:** +1-555-GRC-CLAW

### Information to Collect When Escalating

1. Exact error messages and stack traces
2. Timestamp of when the issue started
3. Recent deployments or configuration changes
4. Affected user/customer count
5. System resource utilization metrics
6. Relevant log excerpts
7. Steps already attempted

---

## Additional Resources

- [GRC_Claw Documentation](../README.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [API Reference](../api-reference.md)
- [Deployment Guide](../deployment.md)
- [Security Audit](../SECURITY-AUDIT.md)
- [Performance Benchmarks](../PERFORMANCE-V17.md)

---

*This guide is maintained by the GRC_Claw engineering team. For contributions or corrections, please submit a pull request or contact the team.*
