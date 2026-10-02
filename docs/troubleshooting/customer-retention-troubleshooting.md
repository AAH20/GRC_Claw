# Customer Retention — Troubleshooting Guide

> **Project:** `customer-retention`
> **Description:** AI-powered customer retention platform for churn prediction, intervention automation, and campaign optimization.
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

This troubleshooting guide covers the most common issues encountered when operating the **Customer Retention** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Churn Predictor | Churn Predictor | `/api/v1/agents/churn-predictor/health` |
| Intervention Agent | Intervention Agent | `/api/v1/agents/intervention-agent/health` |
| Campaign Optimizer | Campaign Optimizer | `/api/v1/agents/campaign-optimizer/health` |
| Loyalty Manager | Loyalty Manager | `/api/v1/agents/loyalty-manager/health` |
| Feedback Analyzer | Feedback Analyzer | `/api/v1/agents/feedback-analyzer/health` |

### Key Integrations

- **CRM Systems**
- **Email Platforms**
- **SMS Gateways**
- **Customer Feedback Tools**
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

### Issue 1: Churn predictions not triggering interventions

**Symptoms:**
- High-risk customers not receiving outreach
- Intervention queue not processing
- Workflow automation failures

**Solutions:**
1. Verify churn score threshold configuration
1. Check intervention trigger conditions
1. Validate workflow automation engine
1. Review intervention delivery logs

**Debugging Steps:**
```bash
Check churn thresholds: GET /api/v1/retention/churn-thresholds
```

```bash
Verify triggers: GET /api/v1/retention/triggers
```

```bash
Test workflow: POST /api/v1/retention/workflow/test
```

```bash
Review delivery logs: GET /api/v1/retention/delivery-logs
```

---

### Issue 2: Retention campaigns underperforming

**Symptoms:**
- Low engagement on retention offers
- Redemption rates declining
- Customer fatigue from over-communication

**Solutions:**
1. Verify offer personalization
1. Check communication frequency caps
1. Validate A/B test results
1. Review customer journey timing

**Debugging Steps:**
```bash
Check offer performance: GET /api/v1/retention/offers/performance
```

```bash
Verify frequency caps: GET /api/v1/retention/frequency
```

```bash
Review A/B tests: GET /api/v1/retention/ab-tests
```

```bash
Check journey timing: GET /api/v1/retention/journey-timing
```

---

### Issue 3: Loyalty program integration failures

**Symptoms:**
- Points not accruing correctly
- Reward redemption failures
- Tier calculation errors

**Solutions:**
1. Verify loyalty API connectivity
1. Check points calculation logic
1. Validate tier progression rules
1. Review reward catalog sync

**Debugging Steps:**
```bash
Check loyalty API: GET /api/v1/retention/loyalty/status
```

```bash
Verify points calc: GET /api/v1/retention/points/calculation
```

```bash
Test tier progression: POST /api/v1/retention/tiers/test
```

```bash
Review reward sync: GET /api/v1/retention/rewards/sync
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
docker logs --tail 500 customer-retention-app

# Filter for errors
docker logs customer-retention-app 2>&1 | grep -i error

# Search for specific patterns
docker logs customer-retention-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs customer-retention-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats customer-retention-app

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
psql -h localhost -U customer-retention -d customer-retention_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/customer-retention` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull customer-retention:latest` |
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
