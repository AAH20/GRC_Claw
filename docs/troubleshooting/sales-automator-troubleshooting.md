# Sales Automator — Troubleshooting Guide

> **Project:** `sales-automator`
> **Description:** Agentic AI sales automation platform with Prospecting, Outreach, Qualification, Demo Scheduling, Follow-up, and Sales Forecasting agents.
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

This troubleshooting guide covers the most common issues encountered when operating the **Sales Automator** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Prospecting Agent | Prospecting Agent | `/api/v1/agents/prospecting-agent/health` |
| Outreach Agent | Outreach Agent | `/api/v1/agents/outreach-agent/health` |
| Qualification Agent | Qualification Agent | `/api/v1/agents/qualification-agent/health` |
| Demo Scheduler | Demo Scheduler | `/api/v1/agents/demo-scheduler/health` |
| Follow-up Agent | Follow-up Agent | `/api/v1/agents/follow-up-agent/health` |
| Sales Forecaster | Sales Forecaster | `/api/v1/agents/sales-forecaster/health` |

### Key Integrations

- **Salesforce**
- **HubSpot**
- **LinkedIn Sales Navigator**
- **Google Calendar**
- **Zoom**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Outreach sequences stalling

**Symptoms:**
- Prospects not receiving follow-up emails
- Sequence state not advancing
- Bounce handling not triggering exits

**Solutions:**
1. Verify email sending infrastructure
1. Check sequence state machine logic
1. Validate bounce processing workflow
1. Review sequence timing configuration

**Debugging Steps:**
```bash
Check sequence status: GET /api/v1/sales/sequences/{id}/status
```

```bash
Verify email delivery: GET /api/v1/sales/email-status
```

```bash
Review bounce logs: GET /api/v1/sales/bounces
```

```bash
Test sequence advancement: POST /api/v1/sales/sequences/{id}/test-advance
```

---

### Issue 2: Demo scheduling conflicts

**Symptoms:**
- Double-booked meetings
- Calendar sync failures
- Timezone mismatches

**Solutions:**
1. Verify calendar API connectivity
1. Check timezone conversion logic
1. Validate availability window configuration
1. Review conflict detection algorithm

**Debugging Steps:**
```bash
Check calendar sync: GET /api/v1/sales/calendar/sync-status
```

```bash
Verify timezone config: GET /api/v1/config/timezones
```

```bash
Test availability: POST /api/v1/sales/availability/test
```

```bash
Review conflict detection: GET /api/v1/sales/conflicts
```

---

### Issue 3: Lead qualification scoring inconsistent

**Symptoms:**
- Similar leads scored differently
- Qualification criteria not applied uniformly
- Score threshold misalignment

**Solutions:**
1. Verify qualification model version
1. Check scoring criteria configuration
1. Validate data input consistency
1. Review model training data quality

**Debugging Steps:**
```bash
Check model version: GET /api/v1/models/qualification/version
```

```bash
Review scoring criteria: GET /api/v1/sales/qualification-criteria
```

```bash
Test scoring consistency: POST /api/v1/sales/qualification/test
```

```bash
Check training data: GET /api/v1/models/qualification/training-data
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
docker logs --tail 500 sales-automator-app

# Filter for errors
docker logs sales-automator-app 2>&1 | grep -i error

# Search for specific patterns
docker logs sales-automator-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs sales-automator-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats sales-automator-app

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
psql -h localhost -U sales-automator -d sales-automator_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/sales-automator` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull sales-automator:latest` |
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
