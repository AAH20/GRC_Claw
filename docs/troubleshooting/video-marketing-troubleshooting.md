# Video Marketing — Troubleshooting Guide

> **Project:** `video-marketing`
> **Description:** Agentic AI video marketing platform for video creation, optimization, distribution, and analytics.
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

This troubleshooting guide covers the most common issues encountered when operating the **Video Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Script Writer | Script Writer | `/api/v1/agents/script-writer/health` |
| Video Editor | Video Editor | `/api/v1/agents/video-editor/health` |
| Thumbnail Generator | Thumbnail Generator | `/api/v1/agents/thumbnail-generator/health` |
| Distribution Agent | Distribution Agent | `/api/v1/agents/distribution-agent/health` |
| Analytics Agent | Analytics Agent | `/api/v1/agents/analytics-agent/health` |

### Key Integrations

- **YouTube API**
- **TikTok API**
- **Instagram API**
- **Video Hosting**
- **Social Media Platforms**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Video rendering failures

**Symptoms:**
- Videos stuck in rendering queue
- Export errors
- Quality degradation in output

**Solutions:**
1. Verify rendering service capacity
1. Check video encoding configuration
1. Validate asset availability
1. Review rendering queue priority

**Debugging Steps:**
```bash
Check rendering: GET /api/v1/video/rendering
```

```bash
Verify encoding: GET /api/v1/video/encoding
```

```bash
Test assets: POST /api/v1/video/assets/test
```

```bash
Review queue: GET /api/v1/video/queue
```

---

### Issue 2: Video distribution failures

**Symptoms:**
- Uploads failing to platforms
- API rate limit errors
- Thumbnail sync issues

**Solutions:**
1. Verify platform API credentials
1. Check upload rate limiting
1. Validate thumbnail generation
1. Review distribution scheduling

**Debugging Steps:**
```bash
Check credentials: GET /api/v1/video/credentials
```

```bash
Verify rate limits: GET /api/v1/video/rate-limits
```

```bash
Test thumbnails: POST /api/v1/video/thumbnails/test
```

```bash
Review scheduling: GET /api/v1/video/scheduling
```

---

### Issue 3: Video analytics not tracking

**Symptoms:**
- View counts not updating
- Engagement metrics missing
- Attribution data gaps

**Solutions:**
1. Verify analytics API connectivity
1. Check tracking pixel implementation
1. Validate metric collection
1. Review data pipeline for video metrics

**Debugging Steps:**
```bash
Check analytics API: GET /api/v1/video/analytics
```

```bash
Verify tracking: GET /api/v1/video/tracking
```

```bash
Test metrics: POST /api/v1/video/metrics/test
```

```bash
Review pipeline: GET /api/v1/video/pipeline
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
docker logs --tail 500 video-marketing-app

# Filter for errors
docker logs video-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs video-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs video-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats video-marketing-app

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
psql -h localhost -U video-marketing -d video-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/video-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull video-marketing:latest` |
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
