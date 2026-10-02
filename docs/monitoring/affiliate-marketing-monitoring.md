# Affiliate Marketing — Monitoring Guide

## Overview

**Project:** affiliate-marketing
**Description:** Affiliate program management, tracking, and commission platform
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Active Affiliate Count | Number of affiliates generating sales | Growth 10% QoQ | Quarterly |
| Affiliate Conversion Rate | Percentage of affiliate traffic converting | > 3% | Weekly |
| Cost Per Acquisition (CPA) | Average cost per affiliate acquisition | < $30 | Weekly |
| Affiliate Fraud Rate | Percentage of fraudulent transactions | < 1% | Monthly |
| Commission Accuracy | Percentage of commissions calculated correctly | > 99.5% | Monthly |
| Affiliate Satisfaction Score | Affiliate feedback and satisfaction rating | > 4.0/5 | Quarterly |
| Program ROI | Revenue generated vs. affiliate costs | > 4x | Quarterly |
| Cookie/Attribution Accuracy | Percentage of sales correctly attributed | > 95% | Weekly |

---

## 2. Dashboards

### 2.1 Affiliate Program Overview

Active affiliates, sales, commissions, and program ROI

### 2.2 Affiliate Performance Leaderboard

Top affiliates, conversion rates, and earnings

### 2.3 Fraud Detection Monitor

Suspicious activity, fraud alerts, and prevention metrics

### 2.4 Commission Tracking Dashboard

Commission calculations, payments, and accuracy

### 2.5 Attribution Analytics

Touchpoint analysis, cookie performance, and attribution accuracy

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Fraud Detected | Fraud rate exceeds 2% | PagerDuty + Slack #affiliate-ops |
| Conversion Rate Drop | Rate falls below 1.5% | PagerDuty + Slack #affiliate-ops |
| Commission Calculation Error | Accuracy falls below 98% | PagerDuty + Slack #affiliate-ops |
| Attribution Failure | Attribution accuracy falls below 90% | PagerDuty + Slack #engineering |
| Affiliate Churn | Active affiliate count drops by > 15% | Slack #affiliate-ops |
| Payment Delay | Commission payments exceed 30 days | PagerDuty + Slack #finance-ops |

---

## 4. Troubleshooting

### 4.1 Fraud activity

Investigate suspicious patterns, implement fraud detection rules, and blacklist fraudulent affiliates.

### 4.2 Low conversion rates

Review affiliate traffic quality, improve landing pages, and optimize commission structure.

### 4.3 Commission errors

Audit calculation logic, review tracking implementation, and validate payment processes.

### 4.4 Attribution issues

Verify cookie implementation, review cross-domain tracking, and test attribution models.

### 4.5 Affiliate churn

Improve communication, enhance support, and optimize commission competitiveness.

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
