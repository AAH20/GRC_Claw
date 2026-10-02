# Brand Monitoring — Troubleshooting Guide

> **Project:** `brand-monitoring`
> **Description:** AI-powered brand monitoring platform for social media, news, and online platform monitoring.
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

This troubleshooting guide covers the most common issues encountered when operating the **Brand Monitoring** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Mention Tracker | Mention Tracker | `/api/v1/agents/mention-tracker/health` |
| Sentiment Analyzer | Sentiment Analyzer | `/api/v1/agents/sentiment-analyzer/health` |
| Response Generator | Response Generator | `/api/v1/agents/response-generator/health` |
| Trend Detector | Trend Detector | `/api/v1/agents/trend-detector/health` |
| Report Builder | Report Builder | `/api/v1/agents/report-builder/health` |

### Key Integrations

- **Social Media APIs**
- **News APIs**
- **Review Sites**
- **Forums**
- **Alerting Systems**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Brand mentions not being captured

**Symptoms:**
- Mentions missing from dashboard
- Social media API gaps
- Keyword matching too narrow

**Solutions:**
1. Verify keyword configuration
1. Check social media API coverage
1. Validate mention detection algorithm
1. Review data source connectivity

**Debugging Steps:**
```bash
Check keywords: GET /api/v1/brand/keywords
```

```bash
Verify API coverage: GET /api/v1/brand/api-coverage
```

```bash
Test detection: POST /api/v1/brand/detection/test
```

```bash
Review sources: GET /api/v1/brand/sources
```

---

### Issue 2: Sentiment analysis missing context

**Symptoms:**
- Sarcasm misclassified
- Industry-specific language misinterpreted
- Multi-language sentiment errors

**Solutions:**
1. Verify sentiment model training data
1. Check industry-specific model fine-tuning
1. Validate multi-language support
1. Review context window configuration

**Debugging Steps:**
```bash
Check training data: GET /api/v1/brand/training-data
```

```bash
Verify fine-tuning: GET /api/v1/brand/fine-tuning
```

```bash
Test multi-language: POST /api/v1/brand/language/test
```

```bash
Review context: GET /api/v1/brand/context
```

---

### Issue 3: Alert fatigue from false positives

**Symptoms:**
- Too many irrelevant alerts
- Team ignoring notifications
- Critical alerts buried in noise

**Solutions:**
1. Verify alert threshold configuration
1. Check relevance scoring algorithm
1. Validate alert grouping logic
1. Review notification routing rules

**Debugging Steps:**
```bash
Check thresholds: GET /api/v1/brand/thresholds
```

```bash
Verify relevance: GET /api/v1/brand/relevance
```

```bash
Test grouping: POST /api/v1/brand/grouping/test
```

```bash
Review routing: GET /api/v1/brand/routing
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
docker logs --tail 500 brand-monitoring-app

# Filter for errors
docker logs brand-monitoring-app 2>&1 | grep -i error

# Search for specific patterns
docker logs brand-monitoring-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs brand-monitoring-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats brand-monitoring-app

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
psql -h localhost -U brand-monitoring -d brand-monitoring_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/brand-monitoring` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull brand-monitoring:latest` |
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
