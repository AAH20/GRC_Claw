# Influencer Marketing — Troubleshooting Guide

> **Project:** `influencer-marketing`
> **Description:** Agentic AI platform for end-to-end influencer marketing campaign management.
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

This troubleshooting guide covers the most common issues encountered when operating the **Influencer Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Influencer Discovery Agent | Influencer Discovery Agent | `/api/v1/agents/influencer-discovery-agent/health` |
| Campaign Manager | Campaign Manager | `/api/v1/agents/campaign-manager/health` |
| Outreach Agent | Outreach Agent | `/api/v1/agents/outreach-agent/health` |
| Performance Tracker | Performance Tracker | `/api/v1/agents/performance-tracker/health` |
| Compliance Checker | Compliance Checker | `/api/v1/agents/compliance-checker/health` |

### Key Integrations

- **Social Media APIs**
- **Influencer Platforms**
- **CRM Systems**
- **Payment Platforms**
- **Analytics Tools**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Influencer discovery returning low-quality matches

**Symptoms:**
- Influencers with fake followers
- Poor audience alignment
- Engagement rate misrepresentation

**Solutions:**
1. Verify influencer vetting algorithm
1. Check audience quality scoring
1. Validate engagement authenticity detection
1. Review influencer database freshness

**Debugging Steps:**
```bash
Check vetting algorithm: GET /api/v1/influencer/vetting
```

```bash
Verify audience quality: GET /api/v1/influencer/audience-quality
```

```bash
Test authenticity: POST /api/v1/influencer/authenticity/test
```

```bash
Review database: GET /api/v1/influencer/database
```

---

### Issue 2: Campaign deliverables not tracked

**Symptoms:**
- Missing influencer content
- Deadline tracking failures
- Approval workflow stuck

**Solutions:**
1. Verify deliverable tracking system
1. Check deadline notification system
1. Validate approval workflow
1. Review influencer communication logs

**Debugging Steps:**
```bash
Check tracking: GET /api/v1/influencer/deliverables
```

```bash
Verify notifications: GET /api/v1/influencer/notifications
```

```bash
Test approval workflow: POST /api/v1/influencer/approval/test
```

```bash
Review comms: GET /api/v1/influencer/comms
```

---

### Issue 3: Influencer payment disputes

**Symptoms:**
- Payment amount mismatches
- Contract terms not reflected in payments
- Late payment complaints

**Solutions:**
1. Verify contract-to-payment mapping
1. Check payment calculation logic
1. Validate payment approval workflow
1. Review payment history accuracy

**Debugging Steps:**
```bash
Check contract mapping: GET /api/v1/influencer/contracts
```

```bash
Verify payment calc: GET /api/v1/influencer/payments/calculation
```

```bash
Test approval: POST /api/v1/influencer/payments/approval/test
```

```bash
Review history: GET /api/v1/influencer/payments/history
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
docker logs --tail 500 influencer-marketing-app

# Filter for errors
docker logs influencer-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs influencer-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs influencer-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats influencer-marketing-app

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
psql -h localhost -U influencer-marketing -d influencer-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/influencer-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull influencer-marketing:latest` |
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
