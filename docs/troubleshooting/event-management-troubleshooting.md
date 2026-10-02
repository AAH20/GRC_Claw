# Event Management — Troubleshooting Guide

> **Project:** `event-management`
> **Description:** Agentic AI event management system for planning, promotion, execution, and post-event analysis.
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

This troubleshooting guide covers the most common issues encountered when operating the **Event Management** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Event Planner | Event Planner | `/api/v1/agents/event-planner/health` |
| Promotion Agent | Promotion Agent | `/api/v1/agents/promotion-agent/health` |
| Logistics Coordinator | Logistics Coordinator | `/api/v1/agents/logistics-coordinator/health` |
| Attendee Engagement Agent | Attendee Engagement Agent | `/api/v1/agents/attendee-engagement-agent/health` |
| Post-Event Analyzer | Post-Event Analyzer | `/api/v1/agents/post-event-analyzer/health` |

### Key Integrations

- **Event Platforms**
- **Email Marketing**
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

### Issue 1: Event promotion campaigns underperforming

**Symptoms:**
- Low registration rates
- Email open rates dropping
- Social media engagement low

**Solutions:**
1. Verify promotion campaign configuration
1. Check audience targeting accuracy
1. Validate email deliverability
1. Review social media scheduling

**Debugging Steps:**
```bash
Check campaigns: GET /api/v1/events/campaigns
```

```bash
Verify targeting: GET /api/v1/events/targeting
```

```bash
Test deliverability: POST /api/v1/events/deliverability/test
```

```bash
Review scheduling: GET /api/v1/events/scheduling
```

---

### Issue 2: Attendee engagement tracking failures

**Symptoms:**
- Session attendance not tracked
- Engagement scores inaccurate
- Networking recommendations not generating

**Solutions:**
1. Verify tracking pixel deployment
1. Check engagement scoring algorithm
1. Validate recommendation engine
1. Review real-time analytics pipeline

**Debugging Steps:**
```bash
Check tracking: GET /api/v1/events/tracking
```

```bash
Verify scoring: GET /api/v1/events/scoring
```

```bash
Test recommendations: POST /api/v1/events/recommendations/test
```

```bash
Review analytics: GET /api/v1/events/analytics
```

---

### Issue 3: Post-event analysis incomplete

**Symptoms:**
- Survey responses not collected
- ROI calculations missing data
- Follow-up campaigns not triggered

**Solutions:**
1. Verify survey distribution
1. Check data collection completeness
1. Validate ROI calculation inputs
1. Review follow-up automation

**Debugging Steps:**
```bash
Check surveys: GET /api/v1/events/surveys
```

```bash
Verify data: GET /api/v1/events/data-completeness
```

```bash
Test ROI: POST /api/v1/events/roi/test
```

```bash
Review follow-up: GET /api/v1/events/follow-up
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
docker logs --tail 500 event-management-app

# Filter for errors
docker logs event-management-app 2>&1 | grep -i error

# Search for specific patterns
docker logs event-management-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs event-management-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats event-management-app

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
psql -h localhost -U event-management -d event-management_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/event-management` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull event-management:latest` |
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
