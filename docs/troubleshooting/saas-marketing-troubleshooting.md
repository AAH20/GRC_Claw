# SaaS Marketing — Troubleshooting Guide

> **Project:** `saas-marketing`
> **Description:** Agentic AI marketing platform optimized for SaaS Product-Led Growth (PLG).
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

This troubleshooting guide covers the most common issues encountered when operating the **SaaS Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| PLG Optimizer | PLG Optimizer | `/api/v1/agents/plg-optimizer/health` |
| Trial Converter | Trial Converter | `/api/v1/agents/trial-converter/health` |
| Onboarding Agent | Onboarding Agent | `/api/v1/agents/onboarding-agent/health` |
| Expansion Revenue Agent | Expansion Revenue Agent | `/api/v1/agents/expansion-revenue-agent/health` |
| Churn Preventer | Churn Preventer | `/api/v1/agents/churn-preventer/health` |

### Key Integrations

- **Product Analytics**
- **CRM Systems**
- **Email Platforms**
- **In-App Messaging**
- **Billing Systems**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Free trial to paid conversion low

**Symptoms:**
- Trial users not converting
- Onboarding drop-off high
- Feature adoption below threshold

**Solutions:**
1. Verify trial conversion funnel
1. Check onboarding flow effectiveness
1. Validate feature adoption tracking
1. Review conversion optimization experiments

**Debugging Steps:**
```bash
Check funnel: GET /api/v1/saas/funnel
```

```bash
Verify onboarding: GET /api/v1/saas/onboarding
```

```bash
Test adoption: POST /api/v1/saas/adoption/test
```

```bash
Review experiments: GET /api/v1/saas/experiments
```

---

### Issue 2: Product-qualified lead (PQL) scoring inaccurate

**Symptoms:**
- High-intent users not identified
- PQL threshold misalignment
- Sales handoff timing wrong

**Solutions:**
1. Verify PQL scoring model
1. Check product usage signal weighting
1. Validate sales handoff triggers
1. Review PQL feedback loop

**Debugging Steps:**
```bash
Check model: GET /api/v1/saas/model
```

```bash
Verify signals: GET /api/v1/saas/signals
```

```bash
Test handoff: POST /api/v1/saas/handoff/test
```

```bash
Review feedback: GET /api/v1/saas/feedback
```

---

### Issue 3: Expansion revenue identification gaps

**Symptoms:**
- Upsell opportunities missed
- Usage-based expansion signals not captured
- Account health scores inaccurate

**Solutions:**
1. Verify expansion signal detection
1. Check usage pattern analysis
1. Validate account health scoring
1. Review expansion playbook triggers

**Debugging Steps:**
```bash
Check signals: GET /api/v1/saas/signals
```

```bash
Verify patterns: GET /api/v1/saas/patterns
```

```bash
Test health: POST /api/v1/saas/health/test
```

```bash
Review playbooks: GET /api/v1/saas/playbooks
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
docker logs --tail 500 saas-marketing-app

# Filter for errors
docker logs saas-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs saas-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs saas-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats saas-marketing-app

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
psql -h localhost -U saas-marketing -d saas-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/saas-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull saas-marketing:latest` |
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
