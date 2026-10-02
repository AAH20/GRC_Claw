# Website Optimization — Troubleshooting Guide

> **Project:** `website-optimization`
> **Description:** Agentic AI platform for website optimization with A/B testing, personalization, SEO, performance, and analytics.
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

This troubleshooting guide covers the most common issues encountered when operating the **Website Optimization** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| A/B Testing Agent | A/B Testing Agent | `/api/v1/agents/a/b-testing-agent/health` |
| Personalization Agent | Personalization Agent | `/api/v1/agents/personalization-agent/health` |
| SEO Agent | SEO Agent | `/api/v1/agents/seo-agent/health` |
| Performance Agent | Performance Agent | `/api/v1/agents/performance-agent/health` |
| Analytics Agent | Analytics Agent | `/api/v1/agents/analytics-agent/health` |

### Key Integrations

- **Google Analytics**
- **A/B Testing Tools**
- **CDN Services**
- **Tag Managers**
- **Heatmap Tools**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: A/B tests not reaching significance

**Symptoms:**
- Tests running indefinitely
- Sample size insufficient
- Variant allocation uneven

**Solutions:**
1. Verify statistical significance calculation
1. Check sample size requirements
1. Validate traffic splitting algorithm
1. Review test duration limits

**Debugging Steps:**
```bash
Check significance: GET /api/v1/website/ab-tests
```

```bash
Verify sample size: GET /api/v1/website/sample-size
```

```bash
Test allocation: POST /api/v1/website/allocation/test
```

```bash
Review limits: GET /api/v1/website/test-limits
```

---

### Issue 2: Page performance degradation after changes

**Symptoms:**
- Core Web Vitals declining
- Page load time increasing
- Largest Contentful Paint worsening

**Solutions:**
1. Verify performance monitoring
1. Check resource optimization
1. Validate caching strategy
1. Review third-party script impact

**Debugging Steps:**
```bash
Check performance: GET /api/v1/website/performance
```

```bash
Verify resources: GET /api/v1/website/resources
```

```bash
Test caching: POST /api/v1/website/caching/test
```

```bash
Review scripts: GET /api/v1/website/scripts
```

---

### Issue 3: Personalization causing layout issues

**Symptoms:**
- Content overlapping after personalization
- Mobile layout breaking
- Personalization flash of unstyled content

**Solutions:**
1. Verify personalization CSS scoping
1. Check responsive design handling
1. Validate content injection points
1. Review personalization loading sequence

**Debugging Steps:**
```bash
Check CSS scoping: GET /api/v1/website/css-scoping
```

```bash
Verify responsive: GET /api/v1/website/responsive
```

```bash
Test injection: POST /api/v1/website/injection/test
```

```bash
Review loading: GET /api/v1/website/loading
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
docker logs --tail 500 website-optimization-app

# Filter for errors
docker logs website-optimization-app 2>&1 | grep -i error

# Search for specific patterns
docker logs website-optimization-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs website-optimization-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats website-optimization-app

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
psql -h localhost -U website-optimization -d website-optimization_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/website-optimization` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull website-optimization:latest` |
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
