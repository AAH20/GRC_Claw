# Agency Marketing — Troubleshooting Guide

> **Project:** `agency-marketing`
> **Description:** Agentic AI marketing platform for agency workflows with multi-client operations and white-label capabilities.
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

This troubleshooting guide covers the most common issues encountered when operating the **Agency Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Client Manager | Client Manager | `/api/v1/agents/client-manager/health` |
| Campaign Orchestrator | Campaign Orchestrator | `/api/v1/agents/campaign-orchestrator/health` |
| White-Label Engine | White-Label Engine | `/api/v1/agents/white-label-engine/health` |
| Reporting Agent | Reporting Agent | `/api/v1/agents/reporting-agent/health` |
| Resource Allocator | Resource Allocator | `/api/v1/agents/resource-allocator/health` |

### Key Integrations

- **Agency CRM**
- **Ad Platforms**
- **Client Portals**
- **White-Label Platforms**
- **Reporting Tools**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Multi-client data isolation breaches

**Symptoms:**
- Client A seeing Client B's data
- Cross-client reporting errors
- White-label branding inconsistencies

**Solutions:**
1. Verify client isolation in database queries
1. Check RBAC implementation
1. Validate white-label configuration
1. Review client context propagation

**Debugging Steps:**
```bash
Check isolation: GET /api/v1/agency/isolation
```

```bash
Verify RBAC: GET /api/v1/agency/rbac
```

```bash
Test white-label: POST /api/v1/agency/white-label/test
```

```bash
Review context: GET /api/v1/agency/context
```

---

### Issue 2: White-label reporting failures

**Symptoms:**
- Reports showing wrong client branding
- Report generation timeouts
- Client portal access issues

**Solutions:**
1. Verify white-label configuration
1. Check report generation performance
1. Validate client portal authentication
1. Review report template mapping

**Debugging Steps:**
```bash
Check config: GET /api/v1/agency/config
```

```bash
Verify performance: GET /api/v1/agency/performance
```

```bash
Test portal: POST /api/v1/agency/portal/test
```

```bash
Review templates: GET /api/v1/agency/templates
```

---

### Issue 3: Resource allocation across clients unfair

**Symptoms:**
- Some clients getting more agent attention
- Resource contention causing delays
- Agent utilization imbalanced

**Solutions:**
1. Verify resource allocation algorithm
1. Check client priority configuration
1. Validate agent capacity planning
1. Review workload balancing rules

**Debugging Steps:**
```bash
Check algorithm: GET /api/v1/agency/algorithm
```

```bash
Verify priorities: GET /api/v1/agency/priorities
```

```bash
Test capacity: POST /api/v1/agency/capacity/test
```

```bash
Review balancing: GET /api/v1/agency/balancing
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
docker logs --tail 500 agency-marketing-app

# Filter for errors
docker logs agency-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs agency-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs agency-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats agency-marketing-app

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
psql -h localhost -U agency-marketing -d agency-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/agency-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull agency-marketing:latest` |
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
