# Onboarding & Training — Troubleshooting Guide

> **Project:** `onboarding-training`
> **Description:** Agentic AI onboarding and training platform for personalized courses, LMS delivery, and cohort analysis.
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

This troubleshooting guide covers the most common issues encountered when operating the **Onboarding & Training** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Course Builder | Course Builder | `/api/v1/agents/course-builder/health` |
| Learner Profiler | Learner Profiler | `/api/v1/agents/learner-profiler/health` |
| Content Optimizer | Content Optimizer | `/api/v1/agents/content-optimizer/health` |
| Assessment Engine | Assessment Engine | `/api/v1/agents/assessment-engine/health` |
| Cohort Analyzer | Cohort Analyzer | `/api/v1/agents/cohort-analyzer/health` |

### Key Integrations

- **LMS Platforms**
- **SCORM Players**
- **Video Platforms**
- **Assessment Tools**
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

### Issue 1: Course content not personalizing to learner

**Symptoms:**
- All learners receiving same content
- Skill gap analysis inaccurate
- Learning path not adapting

**Solutions:**
1. Verify learner profile data
1. Check personalization algorithm
1. Validate skill assessment accuracy
1. Review content tagging system

**Debugging Steps:**
```bash
Check learner profiles: GET /api/v1/onboarding/profiles
```

```bash
Verify personalization: GET /api/v1/onboarding/personalization
```

```bash
Test assessment: POST /api/v1/onboarding/assessment/test
```

```bash
Review content tags: GET /api/v1/onboarding/content-tags
```

---

### Issue 2: LMS integration failures

**Symptoms:**
- Course progress not syncing
- SCORM communication errors
- Completion certificates not generating

**Solutions:**
1. Verify LMS API connectivity
1. Check SCORM wrapper configuration
1. Validate completion tracking
1. Review certificate generation logic

**Debugging Steps:**
```bash
Check LMS API: GET /api/v1/onboarding/lms-status
```

```bash
Verify SCORM: GET /api/v1/onboarding/scorm
```

```bash
Test completion: POST /api/v1/onboarding/completion/test
```

```bash
Review certificates: GET /api/v1/onboarding/certificates
```

---

### Issue 3: Cohort performance analysis inaccurate

**Symptoms:**
- Completion rates miscalculated
- Engagement metrics not aggregating
- Benchmark comparisons invalid

**Solutions:**
1. Verify cohort definition logic
1. Check metric calculation accuracy
1. Validate benchmark data
1. Review data aggregation pipeline

**Debugging Steps:**
```bash
Check cohort definitions: GET /api/v1/onboarding/cohorts
```

```bash
Verify metrics: GET /api/v1/onboarding/metrics
```

```bash
Test benchmarks: POST /api/v1/onboarding/benchmarks/test
```

```bash
Review aggregation: GET /api/v1/onboarding/aggregation
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
docker logs --tail 500 onboarding-training-app

# Filter for errors
docker logs onboarding-training-app 2>&1 | grep -i error

# Search for specific patterns
docker logs onboarding-training-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs onboarding-training-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats onboarding-training-app

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
psql -h localhost -U onboarding-training -d onboarding-training_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/onboarding-training` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull onboarding-training:latest` |
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
