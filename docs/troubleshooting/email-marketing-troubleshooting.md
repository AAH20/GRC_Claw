# Email Marketing — Troubleshooting Guide

> **Project:** `email-marketing`
> **Description:** Agentic AI email marketing platform for campaign creation, personalization, sending, and analytics.
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

This troubleshooting guide covers the most common issues encountered when operating the **Email Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Campaign Designer | Campaign Designer | `/api/v1/agents/campaign-designer/health` |
| Copywriter | Copywriter | `/api/v1/agents/copywriter/health` |
| Segmentation Agent | Segmentation Agent | `/api/v1/agents/segmentation-agent/health` |
| Send Optimizer | Send Optimizer | `/api/v1/agents/send-optimizer/health` |
| Analytics Agent | Analytics Agent | `/api/v1/agents/analytics-agent/health` |

### Key Integrations

- **SendGrid**
- **Mailchimp**
- **AWS SES**
- **SparkPost**
- **CRM Systems**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Email deliverability dropping

**Symptoms:**
- Increased bounce rates
- Emails landing in spam
- Sender reputation declining

**Solutions:**
1. Verify SPF, DKIM, and DMARC records
1. Check sender score with reputation monitors
1. Review email content for spam triggers
1. Implement gradual IP warmup for new sending domains

**Debugging Steps:**
```bash
Check sender reputation: GET /api/v1/email/reputation
```

```bash
Verify DNS records: dig TXT _dmarc.example.com
```

```bash
Review bounce logs: GET /api/v1/email/bounces
```

```bash
Test spam score: POST /api/v1/email/spam-check
```

---

### Issue 2: Personalization tokens not resolving

**Symptoms:**
- Raw template variables visible in sent emails
- Fallback values used incorrectly
- Merge tag errors in email client

**Solutions:**
1. Verify contact data field mapping
1. Check template syntax against email client requirements
1. Validate data source connectivity
1. Review personalization fallback rules

**Debugging Steps:**
```bash
Check contact data: GET /api/v1/contacts/{id}/fields
```

```bash
Test template rendering: POST /api/v1/email/test-render
```

```bash
Verify data source: GET /api/v1/data-sources/status
```

```bash
Review fallback config: GET /api/v1/config/personalization
```

---

### Issue 3: Campaign send throttling and timeouts

**Symptoms:**
- Large campaigns taking hours to send
- Send API rate limit errors
- Partial campaign delivery

**Solutions:**
1. Implement chunked sending with rate limiting
1. Verify email service provider quotas
1. Optimize email rendering pipeline
1. Add retry logic with exponential backoff

**Debugging Steps:**
```bash
Check send queue: GET /api/v1/email/send-queue
```

```bash
Verify ESP quotas: GET /api/v1/email/quotas
```

```bash
Monitor send rate: GET /api/v1/metrics/send-rate
```

```bash
Review timeout config: GET /api/v1/config/timeouts
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
docker logs --tail 500 email-marketing-app

# Filter for errors
docker logs email-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs email-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs email-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats email-marketing-app

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
psql -h localhost -U email-marketing -d email-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/email-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull email-marketing:latest` |
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
