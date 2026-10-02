# Healthcare Marketing — Troubleshooting Guide

> **Project:** `healthcare-marketing`
> **Description:** HIPAA-compliant agentic AI marketing platform for healthcare organizations.
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

This troubleshooting guide covers the most common issues encountered when operating the **Healthcare Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Compliance Checker | Compliance Checker | `/api/v1/agents/compliance-checker/health` |
| Patient Engagement Agent | Patient Engagement Agent | `/api/v1/agents/patient-engagement-agent/health` |
| Content Reviewer | Content Reviewer | `/api/v1/agents/content-reviewer/health` |
| Appointment Scheduler | Appointment Scheduler | `/api/v1/agents/appointment-scheduler/health` |
| Outcome Tracker | Outcome Tracker | `/api/v1/agents/outcome-tracker/health` |

### Key Integrations

- **EHR Systems**
- **HIPAA-Compliant Email**
- **Patient Portals**
- **Scheduling Systems**
- **CRM Systems**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: HIPAA compliance violations in marketing content

**Symptoms:**
- PHI appearing in marketing materials
- Consent management gaps
- Audit trail incomplete

**Solutions:**
1. Verify PHI detection in content
1. Check consent management workflow
1. Validate audit logging
1. Review HIPAA compliance rules

**Debugging Steps:**
```bash
Check PHI detection: GET /api/v1/healthcare/phi-detection
```

```bash
Verify consent: GET /api/v1/healthcare/consent
```

```bash
Test audit: POST /api/v1/healthcare/audit/test
```

```bash
Review rules: GET /api/v1/healthcare/rules
```

---

### Issue 2: Patient communication preferences not respected

**Symptoms:**
- Patients receiving unwanted communications
- Channel preferences not honored
- Opt-out requests not processed

**Solutions:**
1. Verify preference management system
1. Check opt-out processing
1. Validate communication consent
1. Review preference enforcement

**Debugging Steps:**
```bash
Check preferences: GET /api/v1/healthcare/preferences
```

```bash
Verify opt-out: GET /api/v1/healthcare/opt-out
```

```bash
Test consent: POST /api/v1/healthcare/consent/test
```

```bash
Review enforcement: GET /api/v1/healthcare/enforcement
```

---

### Issue 3: Appointment scheduling integration failures

**Symptoms:**
- Appointments not syncing with EHR
- Double-booking occurrences
- Reminder notifications not sending

**Solutions:**
1. Verify EHR integration
1. Check scheduling conflict detection
1. Validate notification system
1. Review appointment reminder workflow

**Debugging Steps:**
```bash
Check EHR: GET /api/v1/healthcare/ehr
```

```bash
Verify conflicts: GET /api/v1/healthcare/conflicts
```

```bash
Test notifications: POST /api/v1/healthcare/notifications/test
```

```bash
Review reminders: GET /api/v1/healthcare/reminders
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
docker logs --tail 500 healthcare-marketing-app

# Filter for errors
docker logs healthcare-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs healthcare-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs healthcare-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats healthcare-marketing-app

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
psql -h localhost -U healthcare-marketing -d healthcare-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/healthcare-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull healthcare-marketing:latest` |
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
