# Agency Marketing — Monitoring Guide

## Overview

**Project:** agency-marketing
**Description:** Marketing agency operations, client management, and service delivery
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Client Retention Rate | Percentage of clients retained annually | > 90% | Annually |
| Utilization Rate | Percentage of billable hours vs. capacity | 75-85% | Monthly |
| Gross Margin | Revenue minus direct costs | > 40% | Monthly |
| Client Satisfaction (CSAT) | Client feedback and satisfaction | > 4.3/5 | Quarterly |
| New Business Win Rate | Percentage of pitches won | > 30% | Quarterly |
| Project Delivery On-Time | Percentage of projects delivered on schedule | > 85% | Monthly |
| Revenue Per Employee | Average revenue generated per team member | Growth 10% YoY | Annually |
| Employee Retention Rate | Percentage of team members retained | > 85% | Annually |

---

## 2. Dashboards

### 2.1 Agency Performance Overview

Revenue, margin, utilization, and client metrics

### 2.2 Client Portfolio Dashboard

Client health, satisfaction, revenue, and growth potential

### 2.3 Project Delivery Monitor

Project status, timelines, and delivery performance

### 2.4 Team Utilization Tracker

Individual and team utilization, capacity, and allocation

### 2.5 New Business Pipeline

Opportunities, win rates, and revenue forecast

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Client Churn Risk | Client satisfaction drops below 4.0 | PagerDuty + Slack #agency-leadership |
| Utilization Drop | Rate falls below 65% | PagerDuty + Slack #agency-ops |
| Margin Compression | Gross margin falls below 35% | PagerDuty + Slack #finance-ops |
| Delivery Delay Pattern | On-time delivery falls below 75% | Slack #agency-ops |
| New Business Drought | No new clients in 60 days | PagerDuty + Slack #agency-leadership |
| Employee Turnover | Retention rate falls below 80% | PagerDuty + Slack #hr-ops |

---

## 4. Troubleshooting

### 4.1 Client retention issues

Improve client communication, demonstrate value, and address service gaps.

### 4.2 Low utilization

Optimize resource allocation, improve project estimation, and balance workload.

### 4.3 Margin compression

Review pricing, optimize service delivery, and reduce non-billable time.

### 4.4 Delivery delays

Improve project management, set realistic timelines, and enhance resource planning.

### 4.5 New business challenges

Refine value proposition, improve pitch process, and expand lead generation.

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
