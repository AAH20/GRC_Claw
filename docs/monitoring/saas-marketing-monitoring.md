# SaaS Marketing — Monitoring Guide

## Overview

**Project:** saas-marketing
**Description:** SaaS marketing automation, pipeline management, and growth optimization
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Monthly Recurring Revenue (MRR) Growth | Month-over-month MRR growth | > 10% | Monthly |
| Customer Acquisition Cost (CAC) | Cost to acquire new customer | < $200 | Monthly |
| Lead-to-Trial Conversion | Percentage of leads starting trial | > 15% | Monthly |
| Trial-to-Paid Conversion | Percentage of trials converting to paid | > 25% | Monthly |
| Net Revenue Retention (NRR) | Revenue retention including expansion | > 110% | Quarterly |
| Marketing Qualified Leads (MQLs) | MQLs generated per month | Growth 10% MoM | Monthly |
| Pipeline Coverage Ratio | Pipeline value vs. revenue target | > 3x | Monthly |
| CAC Payback Period | Months to recover CAC | < 12 months | Quarterly |

---

## 2. Dashboards

### 2.1 SaaS Marketing Overview

MRR growth, pipeline, conversion, and retention metrics

### 2.2 Growth Funnel Analytics

Visitor-to-customer journey, conversion rates, and drop-off analysis

### 2.3 Pipeline Dashboard

Pipeline value, coverage ratio, and forecast accuracy

### 2.4 Campaign Performance Tracker

Campaign metrics, MQL generation, and channel ROI

### 2.5 Customer Lifetime Value Analytics

CLV, CAC ratio, payback period, and cohort analysis

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| MRR Growth Decline | Growth falls below 5% | PagerDuty + Slack #saas-leadership |
| CAC Spike | CAC exceeds $300 | PagerDuty + Slack #saas-ops |
| Trial Conversion Drop | Rate falls below 15% | PagerDuty + Slack #saas-ops |
| NRR Decline | NRR falls below 100% | PagerDuty + Slack #saas-leadership |
| Pipeline Coverage Gap | Coverage falls below 2x | PagerDuty + Slack #saas-ops |
| MQL Volume Drop | MQLs fall below 80% of target | Slack #saas-ops |

---

## 4. Troubleshooting

### 4.1 Slow MRR growth

Analyze funnel conversion, improve trial experience, and optimize pricing strategy.

### 4.2 Rising CAC

Optimize marketing channels, improve targeting, and enhance conversion rates.

### 4.3 Low trial conversion

Improve onboarding, enhance product value demonstration, and optimize trial length.

### 4.4 Declining NRR

Focus on customer success, implement expansion revenue strategies, and reduce churn.

### 4.5 Pipeline coverage gap

Increase lead generation, improve conversion rates, and expand market reach.

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
