# Marketing Attribution — Monitoring Guide

## Overview

**Project:** marketing-attribution
**Description:** Multi-touch attribution modeling and marketing ROI analysis
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Attribution Coverage | Percentage of conversions with full touchpoint data | > 90% | Weekly |
| Model Accuracy | Predicted vs. actual conversion alignment | > 0.8 R² | Monthly |
| Data Completeness | Percentage of touchpoints tracked | > 95% | Weekly |
| Attribution Consensus | Agreement across attribution models | > 70% | Monthly |
| Channel ROI Accuracy | Predicted vs. actual channel ROI | < ±15% variance | Monthly |
| Cross-Device Tracking Rate | Percentage of users tracked across devices | > 60% | Weekly |
| Attribution Latency | Time from conversion to attribution completion | < 24 hours | Per conversion |
| Incrementality Measurement | Lift from controlled experiments | > 10% confidence | Quarterly |

---

## 2. Dashboards

### 2.1 Attribution Overview

Model performance, coverage, and data quality metrics

### 2.2 Multi-Touch Attribution Dashboard

Touchpoint influence, path analysis, and credit distribution

### 2.3 Channel ROI Comparison

ROI by channel across different attribution models

### 2.4 Data Quality Monitor

Tracking coverage, completeness, and gap analysis

### 2.5 Incrementality Test Results

Controlled experiment outcomes and lift measurements

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Attribution Data Gap | Coverage falls below 80% | PagerDuty + Slack #analytics-ops |
| Model Accuracy Decline | R² drops below 0.6 | PagerDuty + Slack #data-science |
| Tracking Failure | Touchpoint tracking drops below 90% | PagerDuty + Slack #engineering |
| Cross-Device Tracking Loss | Tracking rate falls below 40% | PagerDuty + Slack #analytics-ops |
| Attribution Latency Breach | Processing exceeds 48 hours | Slack #engineering-alerts |
| Model Consensus Breakdown | Cross-model variance exceeds 30% | Slack #data-science |

---

## 4. Troubleshooting

### 4.1 Missing touchpoints

Audit tracking implementation, verify tag firing, and review cross-domain configuration.

### 4.2 Model disagreement

Review model assumptions, validate data inputs, and consider ensemble approaches.

### 4.3 Low cross-device tracking

Implement user ID matching, improve identity resolution, and review privacy compliance.

### 4.4 Attribution latency issues

Optimize data pipeline, review processing bottlenecks, and check for queue backlogs.

### 4.5 Poor incrementality results

Review test design, ensure proper control groups, and extend test duration.

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
