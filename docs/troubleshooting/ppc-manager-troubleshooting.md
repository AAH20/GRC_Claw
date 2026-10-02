# PPC Manager — Troubleshooting Guide

> **Project:** `ppc-manager`
> **Description:** AI-powered PPC campaign management across Google Ads, Meta Ads, LinkedIn Ads, and TikTok Ads.
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

This troubleshooting guide covers the most common issues encountered when operating the **PPC Manager** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Bid Optimizer | Bid Optimizer | `/api/v1/agents/bid-optimizer/health` |
| Keyword Manager | Keyword Manager | `/api/v1/agents/keyword-manager/health` |
| Ad Copy Agent | Ad Copy Agent | `/api/v1/agents/ad-copy-agent/health` |
| Budget Allocator | Budget Allocator | `/api/v1/agents/budget-allocator/health` |
| Quality Score Monitor | Quality Score Monitor | `/api/v1/agents/quality-score-monitor/health` |

### Key Integrations

- **Google Ads API**
- **Meta Marketing API**
- **LinkedIn Campaign Manager API**
- **TikTok Ads API**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: API authentication failures across platforms

**Symptoms:**
- OAuth token expiration errors
- API calls returning 401/403
- Campaign data not syncing

**Solutions:**
1. Verify OAuth token refresh mechanism
1. Check API credential rotation schedule
1. Validate platform-specific API permissions
1. Review token storage and encryption

**Debugging Steps:**
```bash
Check token status: GET /api/v1/ppc/tokens/status
```

```bash
Test API connectivity: POST /api/v1/ppc/test-auth
```

```bash
Review OAuth config: GET /api/v1/config/oauth
```

```bash
Check credential vault: GET /api/v1/vault/credentials
```

---

### Issue 2: Bid optimization causing budget drain

**Symptoms:**
- CPC increasing rapidly
- Daily budget exhausted in early hours
- ROAS dropping below target

**Solutions:**
1. Verify bid strategy configuration
1. Check for competitor bid wars
1. Review budget pacing algorithm
1. Implement bid change rate limiting

**Debugging Steps:**
```bash
Check bid history: GET /api/v1/ppc/bids/history
```

```bash
Review budget pacing: GET /api/v1/ppc/budget/pacing
```

```bash
Analyze competitor activity: GET /api/v1/ppc/competition
```

```bash
Verify bid limits: GET /api/v1/config/bid-limits
```

---

### Issue 3: Campaign structure sync issues

**Symptoms:**
- Ad groups not matching between platforms
- Keyword lists out of date
- Negative keyword conflicts

**Solutions:**
1. Verify campaign structure sync job
1. Check for API schema changes
1. Validate campaign hierarchy mapping
1. Review sync conflict resolution rules

**Debugging Steps:**
```bash
Check sync status: GET /api/v1/ppc/sync/status
```

```bash
Compare campaign structures: GET /api/v1/ppc/structure-diff
```

```bash
Review sync logs: grep 'sync' logs/ppc-manager.log
```

```bash
Force full sync: POST /api/v1/ppc/sync/full
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
docker logs --tail 500 ppc-manager-app

# Filter for errors
docker logs ppc-manager-app 2>&1 | grep -i error

# Search for specific patterns
docker logs ppc-manager-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs ppc-manager-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats ppc-manager-app

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
psql -h localhost -U ppc-manager -d ppc-manager_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/ppc-manager` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull ppc-manager:latest` |
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
