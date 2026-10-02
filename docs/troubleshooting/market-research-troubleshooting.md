# Market Research — Troubleshooting Guide

> **Project:** `market-research`
> **Description:** Agentic AI market research platform for data collection, analysis, and insight generation.
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

This troubleshooting guide covers the most common issues encountered when operating the **Market Research** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Data Collector | Data Collector | `/api/v1/agents/data-collector/health` |
| Survey Designer | Survey Designer | `/api/v1/agents/survey-designer/health` |
| Competitor Analyzer | Competitor Analyzer | `/api/v1/agents/competitor-analyzer/health` |
| Trend Forecaster | Trend Forecaster | `/api/v1/agents/trend-forecaster/health` |
| Report Generator | Report Generator | `/api/v1/agents/report-generator/health` |

### Key Integrations

- **Survey Platforms**
- **Social Media APIs**
- **News APIs**
- **Industry Databases**
- **Analytics Tools**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Survey response rates declining

**Symptoms:**
- Low completion rates
- Survey abandonment increasing
- Sample representativeness dropping

**Solutions:**
1. Verify survey design quality
1. Check survey distribution channels
1. Validate incentive mechanism
1. Review survey length and complexity

**Debugging Steps:**
```bash
Check survey design: GET /api/v1/research/surveys
```

```bash
Verify distribution: GET /api/v1/research/distribution
```

```bash
Test incentives: POST /api/v1/research/incentives/test
```

```bash
Review length: GET /api/v1/research/survey-length
```

---

### Issue 2: Competitor analysis data gaps

**Symptoms:**
- Missing competitor information
- Pricing data outdated
- Feature comparison incomplete

**Solutions:**
1. Verify competitor data sources
1. Check data collection frequency
1. Validate competitor tracking coverage
1. Review data enrichment pipeline

**Debugging Steps:**
```bash
Check data sources: GET /api/v1/research/sources
```

```bash
Verify frequency: GET /api/v1/research/frequency
```

```bash
Test coverage: POST /api/v1/research/coverage/test
```

```bash
Review enrichment: GET /api/v1/research/enrichment
```

---

### Issue 3: Trend forecasts not materializing

**Symptoms:**
- Predicted trends not emerging
- Forecast confidence low
- Market shifts not anticipated

**Solutions:**
1. Verify trend detection algorithm
1. Check data source diversity
1. Validate forecasting model
1. Review external factor integration

**Debugging Steps:**
```bash
Check algorithm: GET /api/v1/research/algorithm
```

```bash
Verify sources: GET /api/v1/research/source-diversity
```

```bash
Test model: POST /api/v1/research/model/test
```

```bash
Review factors: GET /api/v1/research/factors
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
docker logs --tail 500 market-research-app

# Filter for errors
docker logs market-research-app 2>&1 | grep -i error

# Search for specific patterns
docker logs market-research-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs market-research-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats market-research-app

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
psql -h localhost -U market-research -d market-research_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/market-research` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull market-research:latest` |
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
