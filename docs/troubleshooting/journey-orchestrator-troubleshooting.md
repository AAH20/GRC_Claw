# Journey Orchestrator — Troubleshooting Guide

> **Project:** `journey-orchestrator`
> **Description:** Multi-agent system for designing, personalizing, timing, and optimizing customer journeys across channels.
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

This troubleshooting guide covers the most common issues encountered when operating the **Journey Orchestrator** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Journey Design Agent | Journey Design Agent | `/api/v1/agents/journey-design-agent/health` |
| Personalization Agent | Personalization Agent | `/api/v1/agents/personalization-agent/health` |
| Timing Agent | Timing Agent | `/api/v1/agents/timing-agent/health` |
| Channel Orchestration Agent | Channel Orchestration Agent | `/api/v1/agents/channel-orchestration-agent/health` |
| Optimization Agent | Optimization Agent | `/api/v1/agents/optimization-agent/health` |

### Key Integrations

- **Email Platforms**
- **SMS Gateways**
- **Push Notification Services**
- **CRM Systems**
- **CDP Platforms**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Journey steps executing out of order

**Symptoms:**
- Customers receiving emails before triggers
- Journey state machine showing invalid transitions
- Step execution timestamps out of sequence

**Solutions:**
1. Verify journey state machine configuration
1. Check for race conditions in event processing
1. Validate step dependency graph
1. Review event ordering guarantees in message queue

**Debugging Steps:**
```bash
Inspect journey state: GET /api/v1/journeys/{id}/state
```

```bash
Check event queue ordering: GET /api/v1/events/sequence
```

```bash
Validate step dependencies: GET /api/v1/journeys/{id}/dependencies
```

```bash
Review state machine logs: grep 'transition' logs/journey.log
```

---

### Issue 2: Personalization data not populating

**Symptoms:**
- Template variables showing as blank
- Fallback content being served
- Personalization API returning errors

**Solutions:**
1. Verify CDP data sync status
1. Check template variable syntax
1. Validate customer profile data completeness
1. Review personalization service health

**Debugging Steps:**
```bash
Check CDP sync: GET /api/v1/cdp/sync-status
```

```bash
Test template rendering: POST /api/v1/templates/test-render
```

```bash
Verify customer profile: GET /api/v1/customers/{id}/profile
```

```bash
Check personalization service: GET /api/v1/personalization/health
```

---

### Issue 3: Journey performance degradation at scale

**Symptoms:**
- Step execution latency increasing
- Message queue backlog growing
- Journey completion rates dropping

**Solutions:**
1. Scale journey execution workers
1. Optimize database queries for journey state
1. Implement journey-level caching
1. Review and optimize agent LLM call patterns

**Debugging Steps:**
```bash
Monitor execution latency: GET /api/v1/metrics/latency
```

```bash
Check queue backlog: GET /api/v1/queue/backlog
```

```bash
Profile agent execution: GET /api/v1/agents/profile
```

```bash
Review database query performance: GET /api/v1/db/slow-queries
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
docker logs --tail 500 journey-orchestrator-app

# Filter for errors
docker logs journey-orchestrator-app 2>&1 | grep -i error

# Search for specific patterns
docker logs journey-orchestrator-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs journey-orchestrator-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats journey-orchestrator-app

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
psql -h localhost -U journey-orchestrator -d journey-orchestrator_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/journey-orchestrator` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull journey-orchestrator:latest` |
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
