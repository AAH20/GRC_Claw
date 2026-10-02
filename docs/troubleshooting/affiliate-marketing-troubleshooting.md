# Affiliate Marketing — Troubleshooting Guide

> **Project:** `affiliate-marketing`
> **Description:** Agentic AI affiliate marketing platform for partner management, commission tracking, and campaign optimization.
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

This troubleshooting guide covers the most common issues encountered when operating the **Affiliate Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Affiliate Recruiter | Affiliate Recruiter | `/api/v1/agents/affiliate-recruiter/health` |
| Commission Tracker | Commission Tracker | `/api/v1/agents/commission-tracker/health` |
| Campaign Optimizer | Campaign Optimizer | `/api/v1/agents/campaign-optimizer/health` |
| Fraud Detector | Fraud Detector | `/api/v1/agents/fraud-detector/health` |
| Payout Manager | Payout Manager | `/api/v1/agents/payout-manager/health` |

### Key Integrations

- **Affiliate Networks**
- **Payment Gateways**
- **CRM Systems**
- **Tracking Platforms**
- **Ad Platforms**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Commission calculation discrepancies

**Symptoms:**
- Affiliate payouts incorrect
- Commission rates not applied consistently
- Multi-tier commissions miscalculated

**Solutions:**
1. Verify commission rule configuration
1. Check tracking pixel accuracy
1. Validate attribution for commissions
1. Review commission calculation logic

**Debugging Steps:**
```bash
Check commission rules: GET /api/v1/affiliate/commission-rules
```

```bash
Verify tracking: GET /api/v1/affiliate/tracking
```

```bash
Test attribution: POST /api/v1/affiliate/attribution/test
```

```bash
Review calculation: GET /api/v1/affiliate/calculation
```

---

### Issue 2: Affiliate fraud not detected

**Symptoms:**
- Suspicious click patterns not flagged
- Self-referral fraud
- Cookie stuffing not caught

**Solutions:**
1. Verify fraud detection rules
1. Check IP-based filtering
1. Validate click pattern analysis
1. Review fraud scoring algorithm

**Debugging Steps:**
```bash
Check fraud rules: GET /api/v1/affiliate/fraud-rules
```

```bash
Verify IP filtering: GET /api/v1/affiliate/ip-filtering
```

```bash
Test patterns: POST /api/v1/affiliate/patterns/test
```

```bash
Review scoring: GET /api/v1/affiliate/scoring
```

---

### Issue 3: Affiliate onboarding delays

**Symptoms:**
- New affiliates not receiving welcome materials
- Tracking links not generated
- Approval workflow stuck

**Solutions:**
1. Verify onboarding workflow
1. Check tracking link generation
1. Validate approval process
1. Review affiliate communication system

**Debugging Steps:**
```bash
Check workflow: GET /api/v1/affiliate/onboarding
```

```bash
Verify link generation: GET /api/v1/affiliate/links
```

```bash
Test approval: POST /api/v1/affiliate/approval/test
```

```bash
Review comms: GET /api/v1/affiliate/comms
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
docker logs --tail 500 affiliate-marketing-app

# Filter for errors
docker logs affiliate-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs affiliate-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs affiliate-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats affiliate-marketing-app

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
psql -h localhost -U affiliate-marketing -d affiliate-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/affiliate-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull affiliate-marketing:latest` |
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
