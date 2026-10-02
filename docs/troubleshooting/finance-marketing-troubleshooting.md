# Finance Marketing — Troubleshooting Guide

> **Project:** `finance-marketing`
> **Description:** Agentic AI marketing platform for financial services with FINRA/SEC compliance.
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

This troubleshooting guide covers the most common issues encountered when operating the **Finance Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Compliance Reviewer | Compliance Reviewer | `/api/v1/agents/compliance-reviewer/health` |
| Content Approver | Content Approver | `/api/v1/agents/content-approver/health` |
| Audience Segmenter | Audience Segmenter | `/api/v1/agents/audience-segmenter/health` |
| Campaign Manager | Campaign Manager | `/api/v1/agents/campaign-manager/health` |
| Disclosure Manager | Disclosure Manager | `/api/v1/agents/disclosure-manager/health` |

### Key Integrations

- **FINRA Databases**
- **SEC Filing Systems**
- **CRM Systems**
- **Email Platforms**
- **Ad Platforms**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: FINRA/SEC compliance review bottlenecks

**Symptoms:**
- Marketing content stuck in compliance review
- Approval SLA breaches
- Compliance check false positives

**Solutions:**
1. Verify compliance review workflow
1. Check regulatory rule configuration
1. Validate pre-approval templates
1. Review compliance reviewer capacity

**Debugging Steps:**
```bash
Check workflow: GET /api/v1/finance/workflow
```

```bash
Verify rules: GET /api/v1/finance/rules
```

```bash
Test templates: POST /api/v1/finance/templates/test
```

```bash
Review capacity: GET /api/v1/finance/capacity
```

---

### Issue 2: Required disclosures missing from content

**Symptoms:**
- Ad content missing required disclaimers
- Risk disclosures not appended
- Regulatory text outdated

**Solutions:**
1. Verify disclosure management system
1. Check disclosure template library
1. Validate disclosure insertion logic
1. Review regulatory update process

**Debugging Steps:**
```bash
Check disclosures: GET /api/v1/finance/disclosures
```

```bash
Verify templates: GET /api/v1/finance/templates
```

```bash
Test insertion: POST /api/v1/finance/insertion/test
```

```bash
Review updates: GET /api/v1/finance/updates
```

---

### Issue 3: Audience targeting compliance issues

**Symptoms:**
- Marketing to restricted audiences
- Accredited investor verification gaps
- Suitability requirements not enforced

**Solutions:**
1. Verify audience targeting rules
1. Check investor accreditation validation
1. Validate suitability requirements
1. Review targeting compliance audit

**Debugging Steps:**
```bash
Check targeting: GET /api/v1/finance/targeting
```

```bash
Verify accreditation: GET /api/v1/finance/accreditation
```

```bash
Test suitability: POST /api/v1/finance/suitability/test
```

```bash
Review audit: GET /api/v1/finance/audit
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
docker logs --tail 500 finance-marketing-app

# Filter for errors
docker logs finance-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs finance-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs finance-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats finance-marketing-app

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
psql -h localhost -U finance-marketing -d finance-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/finance-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull finance-marketing:latest` |
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
