# Social Media Manager — Troubleshooting Guide

> **Project:** `social-media-manager`
> **Description:** Agentic AI social media management platform for scheduling, publishing, monitoring, and engagement.
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

This troubleshooting guide covers the most common issues encountered when operating the **Social Media Manager** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Content Scheduler | Content Scheduler | `/api/v1/agents/content-scheduler/health` |
| Engagement Monitor | Engagement Monitor | `/api/v1/agents/engagement-monitor/health` |
| Sentiment Analyzer | Sentiment Analyzer | `/api/v1/agents/sentiment-analyzer/health` |
| Trend Detector | Trend Detector | `/api/v1/agents/trend-detector/health` |
| Community Manager | Community Manager | `/api/v1/agents/community-manager/health` |

### Key Integrations

- **Twitter/X API**
- **Facebook Graph API**
- **Instagram Graph API**
- **LinkedIn API**
- **TikTok API**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Social media posts failing to publish

**Symptoms:**
- Posts stuck in 'pending' status
- API rate limit errors
- Authentication token expired

**Solutions:**
1. Verify API credentials and token validity
1. Check platform-specific rate limits
1. Validate post content against platform policies
1. Review publishing queue for stuck items

**Debugging Steps:**
```bash
Check API token status: GET /api/v1/social/tokens/status
```

```bash
Review publishing queue: GET /api/v1/social/queue
```

```bash
Test platform connectivity: POST /api/v1/social/test-connection
```

```bash
Check rate limit headers: GET /api/v1/social/rate-limits
```

---

### Issue 2: Engagement monitoring missing mentions

**Symptoms:**
- Brand mentions not appearing in dashboard
- Sentiment analysis not running
- Alert notifications not firing

**Solutions:**
1. Verify streaming API connections
1. Check keyword/hashtag monitoring configuration
1. Validate webhook endpoint for real-time updates
1. Review sentiment analysis model deployment

**Debugging Steps:**
```bash
Check streaming connections: GET /api/v1/social/streams/status
```

```bash
Verify monitoring keywords: GET /api/v1/social/monitoring/config
```

```bash
Test webhook endpoint: POST /api/v1/webhooks/test
```

```bash
Check sentiment model: GET /api/v1/models/sentiment/status
```

---

### Issue 3: Scheduling conflicts and duplicate posts

**Symptoms:**
- Same content posted multiple times
- Posts scheduled at wrong times
- Timezone handling errors

**Solutions:**
1. Implement distributed locking for scheduling
1. Verify timezone configuration across services
1. Check for clock skew between servers
1. Review scheduling algorithm for edge cases

**Debugging Steps:**
```bash
Check scheduler locks: GET /api/v1/scheduler/locks
```

```bash
Verify timezone config: GET /api/v1/config/timezone
```

```bash
Compare server times: GET /api/v1/system/clock
```

```bash
Review scheduling logs: grep 'schedule' logs/scheduler.log
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
docker logs --tail 500 social-media-manager-app

# Filter for errors
docker logs social-media-manager-app 2>&1 | grep -i error

# Search for specific patterns
docker logs social-media-manager-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs social-media-manager-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats social-media-manager-app

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
psql -h localhost -U social-media-manager -d social-media-manager_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/social-media-manager` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull social-media-manager:latest` |
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
