# Sales Automator — Monitoring Guide

## Overview

**Project:** sales-automator
**Description:** Sales process automation and pipeline management system
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Pipeline Velocity | Average deal progression speed | > 15% improvement | Monthly |
| Automation Coverage | Percentage of sales tasks automated | > 70% | Monthly |
| Lead Response Time | Time from lead creation to first contact | < 5 minutes | Per lead |
| Quote Generation Time | Time to generate accurate quotes | < 2 hours | Per quote |
| Forecast Accuracy | Deviation from predicted vs. actual revenue | < ±10% | Monthly |
| Task Completion Rate | Percentage of automated tasks completing successfully | > 95% | Daily |
| Sales Cycle Length | Average days from opportunity to close | < 30 days | Monthly |
| Automation ROI | Revenue impact vs. automation cost | > 5x | Quarterly |

---

## 2. Dashboards

### 2.1 Sales Automation Overview

Pipeline metrics, automation coverage, and velocity trends

### 2.2 Lead Response Monitor

Response time tracking, SLA compliance, and distribution metrics

### 2.3 Quote & Proposal Tracker

Generation time, approval rates, and conversion metrics

### 2.4 Forecast Accuracy Dashboard

Predicted vs. actual revenue, confidence intervals, and variance analysis

### 2.5 Automation Workflow Health

Active automations, success rates, and failure analysis

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Lead Response SLA Breach | Response time exceeds 10 minutes | PagerDuty + Slack #sales-ops |
| Pipeline Velocity Drop | Deal progression slows by > 20% | Slack #sales-leadership |
| Forecast Variance | Actual revenue deviates > 15% from forecast | PagerDuty + Slack #sales-ops |
| Automation Failure | Critical sales automation stops executing | PagerDuty + Slack #engineering |
| Quote Generation Delay | Quote generation exceeds 4 hours | Slack #sales-ops |
| Task Completion Drop | Task completion rate falls below 90% | Slack #engineering-alerts |

---

## 4. Troubleshooting

### 4.1 Leads not routing correctly

Verify routing rules, check assignment logic, and review territory definitions.

### 4.2 Slow pipeline progression

Analyze stage conversion rates, identify bottlenecks, and review approval processes.

### 4.3 Inaccurate forecasts

Review historical data quality, check for data entry issues, and validate prediction models.

### 4.4 Automation not executing

Check trigger conditions, verify system connectivity, and review error logs.

### 4.5 Quote generation failures

Verify pricing rules, check product catalog sync, and review approval workflows.

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
