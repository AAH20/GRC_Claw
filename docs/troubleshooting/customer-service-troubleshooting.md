# Customer Service — Troubleshooting Guide

> **Project:** `customer-service`
> **Description:** Agentic AI customer service platform integrating with Zendesk, Intercom, and Salesforce Service Cloud.
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

This troubleshooting guide covers the most common issues encountered when operating the **Customer Service** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Ticket Router | Ticket Router | `/api/v1/agents/ticket-router/health` |
| Response Generator | Response Generator | `/api/v1/agents/response-generator/health` |
| Sentiment Analyzer | Sentiment Analyzer | `/api/v1/agents/sentiment-analyzer/health` |
| Escalation Manager | Escalation Manager | `/api/v1/agents/escalation-manager/health` |
| Knowledge Base Agent | Knowledge Base Agent | `/api/v1/agents/knowledge-base-agent/health` |

### Key Integrations

- **Zendesk API**
- **Intercom API**
- **Salesforce Service Cloud**
- **Slack**
- **WhatsApp Business API**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Ticket routing misclassification

**Symptoms:**
- Tickets assigned to wrong teams
- Priority levels incorrect
- Language detection failures

**Solutions:**
1. Verify routing rules configuration
1. Check NLP classification model accuracy
1. Validate language detection service
1. Review routing feedback loop

**Debugging Steps:**
```bash
Check routing rules: GET /api/v1/cs/routing-rules
```

```bash
Test classification: POST /api/v1/cs/classify/test
```

```bash
Verify language detection: GET /api/v1/cs/language-detection
```

```bash
Review misrouted tickets: GET /api/v1/cs/misrouted
```

---

### Issue 2: AI responses flagged as inappropriate

**Symptoms:**
- Customer complaints about AI tone
- Responses containing hallucinated information
- Brand voice inconsistencies

**Solutions:**
1. Review response generation prompts
1. Implement response validation layer
1. Check knowledge base accuracy
1. Add human-in-the-loop review for sensitive topics

**Debugging Steps:**
```bash
Check response logs: GET /api/v1/cs/responses/recent
```

```bash
Review prompt templates: GET /api/v1/cs/prompts
```

```bash
Validate knowledge base: GET /api/v1/cs/kb/health
```

```bash
Check moderation filters: GET /api/v1/cs/moderation
```

---

### Issue 3: Escalation triggers not firing

**Symptoms:**
- High-priority tickets not escalated
- SLA breaches not detected
- Escalation notifications not sent

**Solutions:**
1. Verify escalation rule configuration
1. Check SLA timer accuracy
1. Validate notification delivery
1. Review escalation threshold settings

**Debugging Steps:**
```bash
Check escalation rules: GET /api/v1/cs/escalation-rules
```

```bash
Verify SLA timers: GET /api/v1/cs/sla/status
```

```bash
Test notifications: POST /api/v1/cs/notifications/test
```

```bash
Review escalation history: GET /api/v1/cs/escalations/recent
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
docker logs --tail 500 customer-service-app

# Filter for errors
docker logs customer-service-app 2>&1 | grep -i error

# Search for specific patterns
docker logs customer-service-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs customer-service-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats customer-service-app

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
psql -h localhost -U customer-service -d customer-service_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/customer-service` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull customer-service:latest` |
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
