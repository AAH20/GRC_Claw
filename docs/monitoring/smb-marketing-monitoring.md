# SMB Marketing — Monitoring Guide

## Overview

**Project:** smb-marketing
**Description:** Small and medium business marketing automation and management
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Client Acquisition Rate | New SMB clients acquired per month | Growth 10% MoM | Monthly |
| Client Retention Rate | Percentage of SMB clients retained | > 85% | Quarterly |
| Campaign Performance vs. Goals | Percentage of campaigns meeting targets | > 75% | Monthly |
| Average Revenue Per Client (ARPC) | Monthly revenue per SMB client | Growth 5% QoQ | Quarterly |
| Service Delivery Time | Average time to deliver marketing services | < 5 days | Per campaign |
| Client Satisfaction (CSAT) | SMB client satisfaction score | > 4.2/5 | Quarterly |
| Marketing ROI for Clients | Client marketing return on investment | > 3x | Quarterly |
| Platform Adoption Rate | Percentage of clients actively using platform | > 80% | Monthly |

---

## 2. Dashboards

### 2.1 SMB Marketing Overview

Client count, revenue, retention, and service delivery metrics

### 2.2 Client Performance Dashboard

Individual client metrics, campaign performance, and satisfaction

### 2.3 Service Delivery Monitor

Delivery times, capacity utilization, and backlog

### 2.4 Client Acquisition Funnel

Lead-to-client conversion, pipeline, and acquisition costs

### 2.5 Platform Usage Analytics

Feature adoption, engagement, and value realization

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Client Churn Risk | Retention rate falls below 80% | PagerDuty + Slack #smb-ops |
| Acquisition Decline | New client acquisition drops by > 20% | PagerDuty + Slack #smb-ops |
| Delivery Delay | Service delivery exceeds 7 days | Slack #smb-ops |
| Client Satisfaction Drop | CSAT falls below 3.8 | PagerDuty + Slack #smb-ops |
| Platform Adoption Issue | Adoption rate falls below 70% | Slack #smb-ops |
| Campaign Underperformance | Success rate falls below 60% | Slack #smb-ops |

---

## 4. Troubleshooting

### 4.1 Client churn

Identify at-risk clients, improve service quality, and enhance value communication.

### 4.2 Acquisition decline

Review marketing channels, improve lead quality, and optimize sales process.

### 4.3 Delivery delays

Optimize workflows, allocate additional resources, and improve capacity planning.

### 4.4 Low satisfaction

Gather client feedback, address pain points, and improve communication.

### 4.5 Low platform adoption

Provide training, improve onboarding, and demonstrate platform value.

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
