# Marketing Compliance — Troubleshooting Guide

> **Project:** `marketing-compliance`
> **Description:** AI-powered marketing compliance monitoring and enforcement platform.
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

This troubleshooting guide covers the most common issues encountered when operating the **Marketing Compliance** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Policy Engine | Policy Engine | `/api/v1/agents/policy-engine/health` |
| Content Auditor | Content Auditor | `/api/v1/agents/content-auditor/health` |
| Consent Manager | Consent Manager | `/api/v1/agents/consent-manager/health` |
| Regulatory Tracker | Regulatory Tracker | `/api/v1/agents/regulatory-tracker/health` |
| Violation Handler | Violation Handler | `/api/v1/agents/violation-handler/health` |

### Key Integrations

- **CMS Platforms**
- **Ad Platforms**
- **Email Platforms**
- **CRM Systems**
- **Legal Databases**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Compliance rules not catching violations

**Symptoms:**
- Non-compliant content published
- Missing consent records
- Regulatory deadline missed

**Solutions:**
1. Verify compliance rule configuration
1. Check content scanning coverage
1. Validate consent management integration
1. Review regulatory update frequency

**Debugging Steps:**
```bash
Check rule config: GET /api/v1/compliance/rules
```

```bash
Verify scanning coverage: GET /api/v1/compliance/scanning
```

```bash
Test consent integration: POST /api/v1/compliance/consent/test
```

```bash
Review regulatory updates: GET /api/v1/compliance/regulatory-updates
```

---

### Issue 2: False positive compliance flags

**Symptoms:**
- Compliant content blocked
- Overly aggressive content filtering
- Legitimate marketing claims flagged

**Solutions:**
1. Review compliance rule thresholds
1. Check content classification model accuracy
1. Validate whitelist configuration
1. Review appeal process effectiveness

**Debugging Steps:**
```bash
Check rule thresholds: GET /api/v1/compliance/thresholds
```

```bash
Verify classification accuracy: GET /api/v1/compliance/classification-accuracy
```

```bash
Review whitelist: GET /api/v1/compliance/whitelist
```

```bash
Check appeal process: GET /api/v1/compliance/appeals
```

---

### Issue 3: Consent management sync failures

**Symptoms:**
- Consent preferences not propagating
- Cross-platform consent mismatches
- Consent audit trail gaps

**Solutions:**
1. Verify consent API connectivity
1. Check consent data transformation
1. Validate cross-platform sync
1. Review consent audit logging

**Debugging Steps:**
```bash
Check consent API: GET /api/v1/consent/status
```

```bash
Verify transformations: GET /api/v1/consent/transformations
```

```bash
Test cross-platform sync: POST /api/v1/consent/sync/test
```

```bash
Review audit logs: GET /api/v1/consent/audit-logs
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
docker logs --tail 500 marketing-compliance-app

# Filter for errors
docker logs marketing-compliance-app 2>&1 | grep -i error

# Search for specific patterns
docker logs marketing-compliance-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs marketing-compliance-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats marketing-compliance-app

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
psql -h localhost -U marketing-compliance -d marketing-compliance_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/marketing-compliance` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull marketing-compliance:latest` |
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
