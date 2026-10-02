# Customer Segmentation — Monitoring Guide

## Overview

**Project:** customer-segmentation
**Description:** AI-driven customer segmentation and persona development platform
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Segment Stability | Consistency of segment assignments over time | > 85% | Monthly |
| Segment Size Balance | Distribution across segments | No segment > 40% | Monthly |
| Segmentation Accuracy | Predicted vs. actual segment behavior alignment | > 80% | Monthly |
| Persona Coverage | Percentage of customers assigned to personas | > 95% | Weekly |
| Segment Migration Rate | Customers moving between segments | < 10%/month | Monthly |
| Actionable Insight Rate | Segments with clear differentiation | > 75% | Quarterly |
| Data Freshness | Recency of segmentation data | < 7 days | Weekly |
| Segment Performance Lift | Campaign performance improvement from targeting | > 20% | Quarterly |

---

## 2. Dashboards

### 2.1 Segmentation Overview

Segment sizes, stability, and performance characteristics

### 2.2 Segment Migration Flow

Customer movement between segments over time

### 2.3 Persona Performance

Segment-level engagement, conversion, and value metrics

### 2.4 Segmentation Model Health

Stability, accuracy, and feature importance trends

### 2.5 Actionability Matrix

Segment differentiation, campaign performance, and opportunity sizing

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Segment Instability | Stability score drops below 70% | PagerDuty + Slack #data-science |
| Segment Imbalance | Any segment exceeds 50% of customer base | Slack #data-science |
| Model Accuracy Decline | Accuracy drops below 70% | PagerDuty + Slack #data-science |
| Data Staleness | Segmentation data older than 14 days | PagerDuty + Slack #data-engineering |
| Persona Coverage Gap | Coverage falls below 90% | Slack #marketing-ops |
| High Migration Rate | Migration exceeds 15% in a month | Slack #data-science |

---

## 4. Troubleshooting

### 4.1 Unstable segments

Review clustering parameters, check for data quality issues, and validate feature selection.

### 4.2 Imbalanced segments

Adjust clustering algorithm, review feature weights, and consider hierarchical segmentation.

### 4.3 Poor segment differentiation

Add behavioral features, review data sources, and validate segment definitions with business teams.

### 4.4 High migration rates

Investigate external factors, review segment definitions, and assess data collection changes.

### 4.5 Low actionability

Collaborate with marketing teams, refine segment criteria, and develop segment-specific strategies.

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
