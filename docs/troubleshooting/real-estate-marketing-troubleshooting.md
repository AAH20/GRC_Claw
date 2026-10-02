# Real Estate Marketing — Troubleshooting Guide

> **Project:** `real-estate-marketing`
> **Description:** AI-powered real estate marketing automation platform for property promotion, lead management, and client engagement.
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

This troubleshooting guide covers the most common issues encountered when operating the **Real Estate Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Property Promoter | Property Promoter | `/api/v1/agents/property-promoter/health` |
| Lead Nurturer | Lead Nurturer | `/api/v1/agents/lead-nurturer/health` |
| Virtual Tour Agent | Virtual Tour Agent | `/api/v1/agents/virtual-tour-agent/health` |
| Market Analyst | Market Analyst | `/api/v1/agents/market-analyst/health` |
| Client Communicator | Client Communicator | `/api/v1/agents/client-communicator/health` |

### Key Integrations

- **MLS Systems**
- **Zillow**
- **Realtor.com**
- **CRM Systems**
- **Virtual Tour Platforms**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Property listing syndication failures

**Symptoms:**
- Listings not appearing on portals
- MLS sync errors
- Photo upload failures

**Solutions:**
1. Verify MLS integration
1. Check portal API connectivity
1. Validate photo processing pipeline
1. Review syndication rules

**Debugging Steps:**
```bash
Check MLS: GET /api/v1/realestate/mls
```

```bash
Verify portals: GET /api/v1/realestate/portals
```

```bash
Test photos: POST /api/v1/realestate/photos/test
```

```bash
Review rules: GET /api/v1/realestate/rules
```

---

### Issue 2: Lead response time too slow

**Symptoms:**
- Inquiry notifications delayed
- Lead routing failures
- Follow-up sequences not starting

**Solutions:**
1. Verify lead capture forms
1. Check notification system
1. Validate lead routing rules
1. Review follow-up automation

**Debugging Steps:**
```bash
Check capture: GET /api/v1/realestate/capture
```

```bash
Verify notifications: GET /api/v1/realestate/notifications
```

```bash
Test routing: POST /api/v1/realestate/routing/test
```

```bash
Review follow-up: GET /api/v1/realestate/follow-up
```

---

### Issue 3: Market analysis data inaccuracies

**Symptoms:**
- Comparable sales data outdated
- Price trend predictions off
- Neighborhood statistics incorrect

**Solutions:**
1. Verify data source freshness
1. Check comparable sales selection
1. Validate price trend model
1. Review neighborhood data sources

**Debugging Steps:**
```bash
Check freshness: GET /api/v1/realestate/freshness
```

```bash
Verify comps: GET /api/v1/realestate/comps
```

```bash
Test trends: POST /api/v1/realestate/trends/test
```

```bash
Review neighborhoods: GET /api/v1/realestate/neighborhoods
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
docker logs --tail 500 real-estate-marketing-app

# Filter for errors
docker logs real-estate-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs real-estate-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs real-estate-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats real-estate-marketing-app

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
psql -h localhost -U real-estate-marketing -d real-estate-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/real-estate-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull real-estate-marketing:latest` |
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
