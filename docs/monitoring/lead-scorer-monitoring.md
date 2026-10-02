# Lead Scorer — Monitoring Guide

## Overview

**Project:** lead-scorer
**Description:** AI-powered lead scoring and qualification system
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Scoring Accuracy | Correlation between score and actual conversion | > 0.75 AUC-ROC | Weekly |
| Lead Processing Latency | Time from lead capture to score assignment | < 30 seconds | Per event |
| Score Distribution Health | Spread of scores across the lead population | Normal distribution | Daily |
| False Positive Rate | High-scoring leads that do not convert | < 15% | Weekly |
| Model Drift Score | Deviation from baseline scoring patterns | < 0.1 PSI | Daily |
| Lead Enrichment Success Rate | Percentage of leads successfully enriched | > 85% | Daily |
| Scoring Coverage | Percentage of leads receiving a score | > 98% | Daily |
| Hot Lead Identification Rate | Percentage of leads marked as sales-ready | 5-15% | Weekly |

---

## 2. Dashboards

### 2.1 Lead Scoring Overview

Score distribution, model health, and processing volume

### 2.2 Scoring Model Performance

AUC-ROC, precision-recall, and calibration metrics

### 2.3 Lead Quality Funnel

Score tiers mapped to conversion rates and sales outcomes

### 2.4 Real-Time Scoring Stream

Live lead scoring events with score breakdowns

### 2.5 Model Drift Monitor

PSI, feature importance shifts, and retraining triggers

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Model Accuracy Degradation | AUC-ROC drops below 0.65 | PagerDuty + Slack #data-science |
| Scoring Latency Spike | P95 latency exceeds 60 seconds | Slack #engineering-alerts |
| Score Distribution Anomaly | PSI exceeds 0.2 indicating significant drift | PagerDuty + Slack #data-science |
| Enrichment Service Failure | Enrichment success rate drops below 70% | Slack #engineering-alerts |
| Scoring Pipeline Down | No scores generated for more than 5 minutes | PagerDuty + Slack #engineering |
| False Positive Spike | False positive rate exceeds 25% for 24 hours | Slack #sales-ops |

---

## 4. Troubleshooting

### 4.1 Scores not updating

Check data pipeline connectivity, verify CRM sync status, and review feature computation jobs.

### 4.2 All leads receiving same score

Investigate feature extraction failures, check for null values in key fields, and verify model version.

### 4.3 Sudden drop in scoring accuracy

Review recent data source changes, check for schema migrations, and validate training data freshness.

### 4.4 Enrichment failures

Verify third-party API keys, check rate limits, and review data provider status pages.

### 4.5 High false positive rate

Retrain model with recent conversion data, review feature weights, and adjust threshold calibration.

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
