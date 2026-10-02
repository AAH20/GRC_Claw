# Content Generator — Troubleshooting Guide

> **Project:** `content-generator`
> **Description:** Multi-agent AI content generation pipeline with Researcher, Strategist, Writer, SEO Editor, and Atomizer agents.
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

This troubleshooting guide covers the most common issues encountered when operating the **Content Generator** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Researcher | Researcher | `/api/v1/agents/researcher/health` |
| Strategist | Strategist | `/api/v1/agents/strategist/health` |
| Writer | Writer | `/api/v1/agents/writer/health` |
| SEO Editor | SEO Editor | `/api/v1/agents/seo-editor/health` |
| Atomizer | Atomizer | `/api/v1/agents/atomizer/health` |

### Key Integrations

- **CMS Platforms**
- **SEO Tools**
- **Translation Services**
- **Image Generation APIs**
- **Plagiarism Checkers**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Content generation timeout or hanging

**Symptoms:**
- Generation requests timing out
- Partial content returned
- Agent stuck in research phase

**Solutions:**
1. Increase agent timeout configuration
1. Check LLM API rate limits and quotas
1. Verify research tool connectivity
1. Implement circuit breaker for external API calls

**Debugging Steps:**
```bash
Check LLM API status: GET /api/v1/llm/health
```

```bash
Monitor generation queue: GET /api/v1/generation/queue
```

```bash
Review agent execution logs: grep 'timeout' logs/content-generator.log
```

```bash
Test research tools: POST /api/v1/research/test
```

---

### Issue 2: Generated content failing SEO checks

**Symptoms:**
- SEO score below threshold
- Keyword density issues
- Meta descriptions missing or malformed

**Solutions:**
1. Verify SEO Editor agent configuration
1. Check keyword research data quality
1. Validate content template structure
1. Review SEO scoring algorithm weights

**Debugging Steps:**
```bash
Check SEO scores: GET /api/v1/content/{id}/seo-score
```

```bash
Review keyword data: GET /api/v1/keywords/research
```

```bash
Validate content structure: GET /api/v1/content/{id}/structure
```

```bash
Test SEO Editor: POST /api/v1/seo/test-review
```

---

### Issue 3: Multi-language content quality issues

**Symptoms:**
- Arabic content with dialect inconsistencies
- Translation artifacts in output
- RTL formatting problems

**Solutions:**
1. Verify language model supports target dialect
1. Check translation service configuration
1. Validate RTL rendering in templates
1. Review dialect-specific prompt engineering

**Debugging Steps:**
```bash
Check language detection: GET /api/v1/content/{id}/language
```

```bash
Test translation service: POST /api/v1/translation/test
```

```bash
Validate RTL rendering: GET /api/v1/templates/rtl-test
```

```bash
Review dialect configuration: GET /api/v1/config/languages
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
docker logs --tail 500 content-generator-app

# Filter for errors
docker logs content-generator-app 2>&1 | grep -i error

# Search for specific patterns
docker logs content-generator-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs content-generator-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats content-generator-app

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
psql -h localhost -U content-generator -d content-generator_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/content-generator` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull content-generator:latest` |
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
