# Conversational Marketing — Troubleshooting Guide

> **Project:** `conversational-marketing`
> **Description:** Agentic AI conversational marketing platform for WhatsApp, Facebook Messenger, and Slack.
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

This troubleshooting guide covers the most common issues encountered when operating the **Conversational Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Conversation Handler | Conversation Handler | `/api/v1/agents/conversation-handler/health` |
| Intent Classifier | Intent Classifier | `/api/v1/agents/intent-classifier/health` |
| Response Generator | Response Generator | `/api/v1/agents/response-generator/health` |
| Handoff Manager | Handoff Manager | `/api/v1/agents/handoff-manager/health` |
| Analytics Agent | Analytics Agent | `/api/v1/agents/analytics-agent/health` |

### Key Integrations

- **WhatsApp Business API**
- **Facebook Messenger**
- **Slack API**
- **CRM Systems**
- **Chatbot Platforms**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Intent classification accuracy dropping

**Symptoms:**
- User queries misrouted
- Fallback responses increasing
- Conversation completion rates declining

**Solutions:**
1. Verify intent model training data
1. Check NLU model version
1. Validate training data freshness
1. Review intent definition coverage

**Debugging Steps:**
```bash
Check training data: GET /api/v1/conversational/training-data
```

```bash
Verify model version: GET /api/v1/conversational/model-version
```

```bash
Test freshness: POST /api/v1/conversational/freshness/test
```

```bash
Review intents: GET /api/v1/conversational/intents
```

---

### Issue 2: Conversation handoff to human failing

**Symptoms:**
- Transfers not reaching agents
- Handoff context lost
- Agent queue not receiving conversations

**Solutions:**
1. Verify handoff API connectivity
1. Check context passing mechanism
1. Validate agent availability detection
1. Review handoff routing rules

**Debugging Steps:**
```bash
Check handoff API: GET /api/v1/conversational/handoff
```

```bash
Verify context: GET /api/v1/conversational/context
```

```bash
Test availability: POST /api/v1/conversational/availability/test
```

```bash
Review routing: GET /api/v1/conversational/routing
```

---

### Issue 3: Multi-language conversation handling errors

**Symptoms:**
- Language detection failures
- Translation quality issues
- RTL language rendering problems

**Solutions:**
1. Verify language detection service
1. Check translation API configuration
1. Validate RTL text handling
1. Review multi-language prompt templates

**Debugging Steps:**
```bash
Check detection: GET /api/v1/conversational/detection
```

```bash
Verify translation: GET /api/v1/conversational/translation
```

```bash
Test RTL: POST /api/v1/conversational/rtl/test
```

```bash
Review templates: GET /api/v1/conversational/templates
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
docker logs --tail 500 conversational-marketing-app

# Filter for errors
docker logs conversational-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs conversational-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs conversational-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats conversational-marketing-app

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
psql -h localhost -U conversational-marketing -d conversational-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/conversational-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull conversational-marketing:latest` |
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
