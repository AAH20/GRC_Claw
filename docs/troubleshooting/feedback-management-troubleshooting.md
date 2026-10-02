# Feedback Management — Troubleshooting Guide

> **Project:** `feedback-management`
> **Description:** Agentic AI feedback management system for collecting, analyzing, and responding to customer feedback.
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

This troubleshooting guide covers the most common issues encountered when operating the **Feedback Management** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Feedback Collector | Feedback Collector | `/api/v1/agents/feedback-collector/health` |
| Sentiment Analyzer | Sentiment Analyzer | `/api/v1/agents/sentiment-analyzer/health` |
| Theme Extractor | Theme Extractor | `/api/v1/agents/theme-extractor/health` |
| Response Generator | Response Generator | `/api/v1/agents/response-generator/health` |
| Action Tracker | Action Tracker | `/api/v1/agents/action-tracker/health` |

### Key Integrations

- **Survey Platforms**
- **Review Sites**
- **Social Media**
- **CRM Systems**
- **Ticketing Systems**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Sentiment analysis misclassifying feedback

**Symptoms:**
- Positive feedback marked as negative
- Sarcasm not detected
- Mixed sentiment handled incorrectly

**Solutions:**
1. Verify sentiment model training data
1. Check language model fine-tuning
1. Validate sentiment threshold calibration
1. Review human review queue

**Debugging Steps:**
```bash
Check model training: GET /api/v1/feedback/model-training
```

```bash
Verify fine-tuning: GET /api/v1/feedback/fine-tuning
```

```bash
Test thresholds: POST /api/v1/feedback/thresholds/test
```

```bash
Review queue: GET /api/v1/feedback/review-queue
```

---

### Issue 2: Feedback response delays

**Symptoms:**
- Customers not receiving responses
- Response queue backlog
- Auto-response rules not triggering

**Solutions:**
1. Verify response generation pipeline
1. Check response queue processing
1. Validate auto-response rules
1. Review response template configuration

**Debugging Steps:**
```bash
Check pipeline: GET /api/v1/feedback/pipeline
```

```bash
Verify queue: GET /api/v1/feedback/queue
```

```bash
Test auto-response: POST /api/v1/feedback/auto-response/test
```

```bash
Review templates: GET /api/v1/feedback/templates
```

---

### Issue 3: Theme extraction missing emerging topics

**Symptoms:**
- New issue categories not detected
- Trending topics not surfaced
- Theme clustering too broad

**Solutions:**
1. Verify theme extraction algorithm
1. Check topic modeling configuration
1. Validate trend detection sensitivity
1. Review theme taxonomy

**Debugging Steps:**
```bash
Check algorithm: GET /api/v1/feedback/algorithm
```

```bash
Verify topic modeling: GET /api/v1/feedback/topic-modeling
```

```bash
Test trend detection: POST /api/v1/feedback/trends/test
```

```bash
Review taxonomy: GET /api/v1/feedback/taxonomy
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
docker logs --tail 500 feedback-management-app

# Filter for errors
docker logs feedback-management-app 2>&1 | grep -i error

# Search for specific patterns
docker logs feedback-management-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs feedback-management-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats feedback-management-app

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
psql -h localhost -U feedback-management -d feedback-management_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/feedback-management` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull feedback-management:latest` |
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
