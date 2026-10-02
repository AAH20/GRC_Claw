# Sales Forecaster — Monitoring Guide

## Overview

**Project:** sales-forecaster
**Description:** AI-powered sales forecasting and revenue prediction system
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Forecast Accuracy (MAPE) | Mean absolute percentage error | < 10% | Monthly |
| Forecast Bias | Systematic over/under prediction | < ±5% | Monthly |
| Prediction Interval Coverage | Actuals falling within confidence intervals | > 90% | Monthly |
| Model Refresh Latency | Time to retrain and update forecasts | < 24 hours | Per cycle |
| Scenario Analysis Coverage | Percentage of products/regions with scenarios | > 80% | Monthly |
| Forecast Consensus Alignment | AI vs. rep forecast agreement | > 75% | Monthly |
| Data Completeness | Percentage of required input data available | > 95% | Daily |
| Forecast Horizon Accuracy | Accuracy at 30/60/90-day horizons | < 15% MAPE | Monthly |

---

## 2. Dashboards

### 2.1 Forecast Overview

Predicted vs. actual revenue, accuracy trends, and bias analysis

### 2.2 Accuracy by Segment

Forecast performance by product, region, and sales team

### 2.3 Scenario Planning Dashboard

Best/base/worst case scenarios with probability weightings

### 2.4 Model Performance Monitor

MAPE, bias, coverage, and feature importance trends

### 2.5 Forecast vs. Actual Tracker

Real-time comparison with variance analysis and alerts

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Forecast Accuracy Degradation | MAPE exceeds 15% | PagerDuty + Slack #data-science |
| Significant Forecast Bias | Bias exceeds ±10% | PagerDuty + Slack #data-science |
| Model Retraining Failure | Scheduled retraining fails | PagerDuty + Slack #engineering |
| Data Input Missing | Critical input data unavailable | PagerDuty + Slack #data-engineering |
| Forecast Variance Alert | Actual deviates > 20% from forecast | Slack #sales-leadership |
| Coverage Gap | Products/regions without forecasts exceeds 25% | Slack #sales-ops |

---

## 4. Troubleshooting

### 4.1 Declining accuracy

Review model features, check for market shifts, and validate training data quality.

### 4.2 Persistent bias

Investigate systematic errors, review data sources, and adjust model parameters.

### 4.3 Missing forecasts

Check data pipeline connectivity, verify input completeness, and review model coverage rules.

### 4.4 Wide prediction intervals

Improve data quality, add relevant features, and review model confidence calibration.

### 4.5 Slow retraining

Optimize training pipeline, review data volume, and assess infrastructure capacity.

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
