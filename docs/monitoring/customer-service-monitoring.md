# Customer Service — Monitoring Guide

## Overview

**Project:** customer-service
**Description:** Customer support ticketing, chatbot, and service quality management
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| First Response Time (FRT) | Average time to first agent response | < 2 hours | Daily |
| Average Handle Time (AHT) | Average time to resolve a ticket | < 4 hours | Daily |
| Customer Satisfaction (CSAT) | Post-interaction satisfaction score | > 4.2/5 | Weekly |
| Net Promoter Score (NPS) | Customer loyalty metric | > 50 | Quarterly |
| Ticket Resolution Rate | Percentage resolved without escalation | > 80% | Weekly |
| Chatbot Deflection Rate | Percentage of inquiries resolved by bot | > 40% | Daily |
| Service Level Agreement (SLA) Compliance | Percentage meeting SLA targets | > 95% | Daily |
| Agent Utilization Rate | Percentage of time spent on customer interactions | 75-85% | Daily |

---

## 2. Dashboards

### 2.1 Service Performance Overview

FRT, AHT, CSAT, and SLA compliance across all channels

### 2.2 Ticket Volume & Trends

Ticket inflow, backlog, resolution rates, and category breakdown

### 2.3 Chatbot Performance

Deflection rate, resolution accuracy, and escalation patterns

### 2.4 Agent Productivity Monitor

Individual and team performance, utilization, and quality scores

### 2.5 Customer Satisfaction Tracker

CSAT, NPS, sentiment analysis, and feedback trends

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| SLA Breach | SLA compliance falls below 90% | PagerDuty + Slack #support-ops |
| Ticket Backlog Surge | Open ticket count exceeds 200% of normal | PagerDuty + Slack #support-ops |
| CSAT Drop | CSAT falls below 3.8 | Slack #support-leadership |
| Chatbot Failure | Chatbot unavailable or error rate exceeds 10% | PagerDuty + Slack #engineering |
| Agent Availability Crisis | Available agents below minimum threshold | PagerDuty + Slack #support-ops |
| Escalation Rate Spike | Escalations exceed 30% of total tickets | Slack #support-alerts |

---

## 4. Troubleshooting

### 4.1 Rising ticket volume

Identify root causes, check for product issues, and review self-service options.

### 4.2 Long resolution times

Analyze ticket complexity, review knowledge base coverage, and assess agent training needs.

### 4.3 Low CSAT scores

Review interaction recordings, identify common complaints, and improve response quality.

### 4.4 Chatbot poor performance

Review training data, expand intent coverage, and improve fallback handling.

### 4.5 SLA compliance issues

Adjust staffing levels, optimize routing rules, and review SLA definitions.

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
