# Cross-Project Orchestrator — Monitoring Guide

## Overview

**Project:** cross-project-orchestrator
**Description:** Cross-project coordination, resource allocation, and dependency management
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Project On-Time Delivery | Percentage of projects delivered on schedule | > 85% | Monthly |
| Resource Utilization Rate | Percentage of available capacity utilized | 75-85% | Weekly |
| Cross-Project Dependency Resolution | Percentage of dependencies resolved on time | > 90% | Weekly |
| Stakeholder Satisfaction | Cross-project stakeholder feedback | > 4.0/5 | Quarterly |
| Budget Variance | Deviation from planned budget | < ±10% | Monthly |
| Scope Change Frequency | Number of scope changes per project | < 2 per month | Monthly |
| Integration Success Rate | Percentage of cross-project integrations succeeding | > 95% | Monthly |
| Communication Effectiveness | Meeting and update compliance | > 90% | Weekly |

---

## 2. Dashboards

### 2.1 Orchestration Overview

All projects: status, health, resources, and timelines

### 2.2 Resource Allocation Matrix

Resource distribution across projects and capacity planning

### 2.3 Dependency Map

Cross-project dependencies, critical paths, and resolution status

### 2.4 Risk & Issue Monitor

Cross-project risks, issues, and mitigation status

### 2.5 Stakeholder Communication Dashboard

Communication frequency, satisfaction, and engagement

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Project Delay Risk | Project timeline exceeds 80% without completion | PagerDuty + Slack #orchestrator |
| Resource Overallocation | Any resource allocated > 100% capacity | PagerDuty + Slack #orchestrator |
| Dependency Block | Critical dependency unresolved for > 48 hours | PagerDuty + Slack #orchestrator |
| Budget Overrun | Project budget exceeds 110% | PagerDuty + Slack #finance-ops |
| Scope Creep | Scope changes exceed 3 in a month | Slack #orchestrator |
| Integration Failure | Cross-project integration fails | PagerDuty + Slack #engineering |

---

## 4. Troubleshooting

### 4.1 Project delays

Reassess timelines, reallocate resources, and escalate blockers to leadership.

### 4.2 Resource conflicts

Prioritize projects, negotiate deadlines, and consider additional hiring or outsourcing.

### 4.3 Dependency blocks

Identify alternative solutions, escalate to stakeholders, and adjust project sequences.

### 4.4 Budget overruns

Review scope, negotiate additional funding, and implement cost control measures.

### 4.5 Scope creep

Implement change control process, assess impact, and communicate trade-offs to stakeholders.

---

## 5. Escalation Procedures

1. **Level 1 (L1):** On-call engineer investigates and attempts resolution within 30 minutes.
2. **Level 2 (L2):** Senior engineer or team lead engages if L1 cannot resolve within 30 minutes.
3. **Level 3 (L3):** Engineering manager and product owner engage for critical issues affecting production.
4. **Level 4 (L4):** Executive leadership engagement for business-critical incidents.

---

## 6. Runbook References

- [Incident Response Runbook](../runbooks/incident-response.md)
- [Escalation Matrix](../runbooks/escalation-matrix.md)
- [Communication Templates](../runbooks/communication-templates.md)

---

## 7. Review Cadence

| Review Type | Frequency | Participants |
|-------------|-----------|--------------|
| Metrics Review | Weekly | Marketing Ops, Data Team |
| Alert Tuning | Bi-weekly | Engineering, Marketing Ops |
| Dashboard Audit | Monthly | All Stakeholders |
| Comprehensive Review | Quarterly | Leadership, All Teams |

---

*This document is maintained by the Marketing Operations team. For questions or updates, contact #marketing-ops.*
