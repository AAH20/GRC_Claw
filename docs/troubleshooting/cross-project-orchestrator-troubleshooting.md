# Cross-Project Orchestrator — Troubleshooting Guide

> **Project:** `cross-project-orchestrator`
> **Description:** Unified orchestration layer for multi-project agentic AI marketing systems with centralized discovery, dependency resolution, and health monitoring.
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

This troubleshooting guide covers the most common issues encountered when operating the **Cross-Project Orchestrator** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Project Discovery Agent | Project Discovery Agent | `/api/v1/agents/project-discovery-agent/health` |
| Dependency Resolver | Dependency Resolver | `/api/v1/agents/dependency-resolver/health` |
| Resource Allocator | Resource Allocator | `/api/v1/agents/resource-allocator/health` |
| Health Monitor | Health Monitor | `/api/v1/agents/health-monitor/health` |
| Cost Optimizer | Cost Optimizer | `/api/v1/agents/cost-optimizer/health` |

### Key Integrations

- **All Marketing AI Projects**
- **Kubernetes**
- **Docker**
- **Cloud Providers**
- **Monitoring Systems**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Project discovery not finding all services

**Symptoms:**
- New projects not appearing in registry
- Service health checks failing
- Dependency graph incomplete

**Solutions:**
1. Verify service discovery mechanism
1. Check project registration process
1. Validate health check endpoints
1. Review dependency mapping configuration

**Debugging Steps:**
```bash
Check discovery: GET /api/v1/orchestrator/discovery
```

```bash
Verify registration: GET /api/v1/orchestrator/registration
```

```bash
Test health: POST /api/v1/orchestrator/health/test
```

```bash
Review dependencies: GET /api/v1/orchestrator/dependencies
```

---

### Issue 2: Resource allocation conflicts across projects

**Symptoms:**
- CPU/memory contention between projects
- GPU allocation starvation
- Storage quota exceeded

**Solutions:**
1. Verify resource quota configuration
1. Check resource scheduling algorithm
1. Validate priority-based allocation
1. Review resource usage monitoring

**Debugging Steps:**
```bash
Check quotas: GET /api/v1/orchestrator/quotas
```

```bash
Verify scheduling: GET /api/v1/orchestrator/scheduling
```

```bash
Test priority: POST /api/v1/orchestrator/priority/test
```

```bash
Review monitoring: GET /api/v1/orchestrator/monitoring
```

---

### Issue 3: Cross-project dependency deadlocks

**Symptoms:**
- Circular dependency detected
- Project startup failures
- Cascading failure across projects

**Solutions:**
1. Verify dependency graph acyclicity
1. Check startup order configuration
1. Validate circuit breaker implementation
1. Review failure isolation boundaries

**Debugging Steps:**
```bash
Check graph: GET /api/v1/orchestrator/graph
```

```bash
Verify startup: GET /api/v1/orchestrator/startup
```

```bash
Test circuit breaker: POST /api/v1/orchestrator/circuit-breaker/test
```

```bash
Review isolation: GET /api/v1/orchestrator/isolation
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
docker logs --tail 500 cross-project-orchestrator-app

# Filter for errors
docker logs cross-project-orchestrator-app 2>&1 | grep -i error

# Search for specific patterns
docker logs cross-project-orchestrator-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs cross-project-orchestrator-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats cross-project-orchestrator-app

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
psql -h localhost -U cross-project-orchestrator -d cross-project-orchestrator_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/cross-project-orchestrator` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull cross-project-orchestrator:latest` |
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
