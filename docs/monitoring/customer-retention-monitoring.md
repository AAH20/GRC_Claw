# Customer Retention — Monitoring Guide

## Overview

**Project:** customer-retention
**Description:** Customer churn prediction, retention campaigns, and loyalty management
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Churn Rate | Percentage of customers canceling per month | < 3% | Monthly |
| Customer Lifetime Value (CLV) | Predicted revenue per customer | Growth 10% QoQ | Quarterly |
| Retention Campaign Effectiveness | Churn reduction from campaigns | > 15% | Monthly |
| Net Revenue Retention (NRR) | Revenue retention including expansion | > 110% | Quarterly |
| Customer Health Score | Composite engagement and satisfaction metric | > 70/100 | Weekly |
| Win-Back Success Rate | Percentage of churned customers returning | > 10% | Quarterly |
| Loyalty Program Engagement | Active loyalty members / total customers | > 40% | Monthly |
| Proactive Intervention Success | At-risk customers saved by interventions | > 30% | Monthly |

---

## 2. Dashboards

### 2.1 Retention Overview

Churn rate, CLV, NRR, and health score trends

### 2.2 Churn Risk Monitor

At-risk customer list, risk scores, and intervention status

### 2.3 Retention Campaign Performance

Campaign effectiveness, ROI, and customer response rates

### 2.4 Customer Health Distribution

Health score segments, trends, and early warning indicators

### 2.5 Loyalty Program Analytics

Enrollment, engagement, redemption rates, and program ROI

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Churn Rate Spike | Monthly churn exceeds 5% | PagerDuty + Slack #retention-urgent |
| Health Score Drop | Average health score falls below 60 | PagerDuty + Slack #customer-success |
| NRR Decline | Net revenue retention falls below 100% | PagerDuty + Slack #executive |
| At-Risk Customer Surge | High-risk customer count exceeds 20% of base | Slack #customer-success |
| Retention Campaign Underperformance | Campaign shows < 5% churn reduction | Slack #marketing-ops |
| Win-Back Failure | Win-back rate falls below 5% | Slack #retention-team |

---

## 4. Troubleshooting

### 4.1 Rising churn rates

Analyze churn reasons, identify common patterns, and improve customer onboarding and support.

### 4.2 Low health scores

Investigate engagement drops, review product usage patterns, and implement re-engagement campaigns.

### 4.3 Ineffective retention campaigns

Review targeting criteria, test different offers, and personalize messaging.

### 4.4 Declining CLV

Identify upsell opportunities, improve customer experience, and enhance product value delivery.

### 4.5 Poor win-back results

Test different incentives, improve timing of win-back offers, and refine customer segmentation.

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
