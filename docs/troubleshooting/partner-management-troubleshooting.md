# Partner Management — Troubleshooting Guide

> **Project:** `partner-management`
> **Description:** Agentic AI system for managing partner relationships, deals, communications, analytics, enablement, and compliance.
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

This troubleshooting guide covers the most common issues encountered when operating the **Partner Management** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Partner Onboarder | Partner Onboarder | `/api/v1/agents/partner-onboarder/health` |
| Deal Tracker | Deal Tracker | `/api/v1/agents/deal-tracker/health` |
| Communication Agent | Communication Agent | `/api/v1/agents/communication-agent/health` |
| Analytics Agent | Analytics Agent | `/api/v1/agents/analytics-agent/health` |
| Enablement Agent | Enablement Agent | `/api/v1/agents/enablement-agent/health` |
| Compliance Agent | Compliance Agent | `/api/v1/agents/compliance-agent/health` |

### Key Integrations

- **CRM Systems**
- **PRM Platforms**
- **Communication Tools**
- **Contract Management**
- **Compliance Databases**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Partner data sync failures

**Symptoms:**
- Partner records not updating in CRM
- Deal status mismatches
- Communication history gaps

**Solutions:**
1. Verify CRM integration
1. Check data sync job status
1. Validate field mapping
1. Review sync conflict resolution

**Debugging Steps:**
```bash
Check CRM: GET /api/v1/partners/crm-status
```

```bash
Verify sync jobs: GET /api/v1/partners/sync-jobs
```

```bash
Test field mapping: POST /api/v1/partners/field-mapping/test
```

```bash
Review conflicts: GET /api/v1/partners/conflicts
```

---

### Issue 2: Deal registration approval delays

**Symptoms:**
- Deals stuck in approval
- Notification failures
- Partner frustration with process

**Solutions:**
1. Verify approval workflow configuration
1. Check notification system
1. Validate deal registration form
1. Review approval SLA monitoring

**Debugging Steps:**
```bash
Check workflow: GET /api/v1/partners/workflow
```

```bash
Verify notifications: GET /api/v1/partners/notifications
```

```bash
Test form: POST /api/v1/partners/form/test
```

```bash
Review SLA: GET /api/v1/partners/sla
```

---

### Issue 3: Partner enablement content not delivering

**Symptoms:**
- Training materials not accessible
- Certification tracking failures
- Enablement progress not updating

**Solutions:**
1. Verify content delivery system
1. Check LMS integration
1. Validate progress tracking
1. Review content access permissions

**Debugging Steps:**
```bash
Check delivery: GET /api/v1/partners/delivery
```

```bash
Verify LMS: GET /api/v1/partners/lms
```

```bash
Test progress: POST /api/v1/partners/progress/test
```

```bash
Review permissions: GET /api/v1/partners/permissions
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
docker logs --tail 500 partner-management-app

# Filter for errors
docker logs partner-management-app 2>&1 | grep -i error

# Search for specific patterns
docker logs partner-management-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs partner-management-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats partner-management-app

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
psql -h localhost -U partner-management -d partner-management_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/partner-management` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull partner-management:latest` |
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
