# Workflow Automation — Troubleshooting Guide

> **Project:** `workflow-automation`
> **Description:** Agentic AI marketing workflow automation platform integrating with n8n, Zapier, and Make.
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

This troubleshooting guide covers the most common issues encountered when operating the **Workflow Automation** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Workflow Designer | Workflow Designer | `/api/v1/agents/workflow-designer/health` |
| Trigger Manager | Trigger Manager | `/api/v1/agents/trigger-manager/health` |
| Action Executor | Action Executor | `/api/v1/agents/action-executor/health` |
| Error Handler | Error Handler | `/api/v1/agents/error-handler/health` |
| Performance Monitor | Performance Monitor | `/api/v1/agents/performance-monitor/health` |

### Key Integrations

- **n8n**
- **Zapier**
- **Make**
- **Webhooks**
- **API Connectors**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Workflow triggers not firing

**Symptoms:**
- Events not starting workflows
- Webhook deliveries failing
- Scheduled triggers missing executions

**Solutions:**
1. Verify trigger configuration
1. Check webhook endpoint health
1. Validate scheduler status
1. Review event source connectivity

**Debugging Steps:**
```bash
Check triggers: GET /api/v1/workflows/triggers
```

```bash
Verify webhooks: GET /api/v1/workflows/webhooks
```

```bash
Test scheduler: POST /api/v1/workflows/scheduler/test
```

```bash
Review event sources: GET /api/v1/workflows/event-sources
```

---

### Issue 2: Workflow execution failures

**Symptoms:**
- Actions failing mid-workflow
- Error handling not recovering
- Partial workflow completion

**Solutions:**
1. Verify action configuration
1. Check error handling rules
1. Validate retry logic
1. Review workflow state persistence

**Debugging Steps:**
```bash
Check actions: GET /api/v1/workflows/actions
```

```bash
Verify error handling: GET /api/v1/workflows/error-handling
```

```bash
Test retry: POST /api/v1/workflows/retry/test
```

```bash
Review state: GET /api/v1/workflows/state
```

---

### Issue 3: Integration connector failures

**Symptoms:**
- n8n/Zapier/Make connections dropping
- API authentication expiring
- Data format mismatches between systems

**Solutions:**
1. Verify connector credentials
1. Check API token refresh mechanism
1. Validate data transformation mapping
1. Review connector health monitoring

**Debugging Steps:**
```bash
Check connectors: GET /api/v1/workflows/connectors
```

```bash
Verify credentials: GET /api/v1/workflows/credentials
```

```bash
Test transformations: POST /api/v1/workflows/transform/test
```

```bash
Review health: GET /api/v1/workflows/health
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
docker logs --tail 500 workflow-automation-app

# Filter for errors
docker logs workflow-automation-app 2>&1 | grep -i error

# Search for specific patterns
docker logs workflow-automation-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs workflow-automation-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats workflow-automation-app

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
psql -h localhost -U workflow-automation -d workflow-automation_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/workflow-automation` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull workflow-automation:latest` |
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
