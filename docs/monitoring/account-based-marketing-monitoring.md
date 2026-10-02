# Account-Based Marketing — Monitoring Guide

## Overview

**Project:** account-based-marketing
**Description:** ABM strategy execution, account targeting, and engagement platform
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Target Account Engagement | Percentage of target accounts showing activity | > 40% | Monthly |
| Account Coverage | Percentage of target accounts with active campaigns | > 90% | Monthly |
| Pipeline Generated | Opportunities created from ABM campaigns | Growth 15% QoQ | Quarterly |
| Account Progression Rate | Movement through ABM funnel stages | > 25% | Monthly |
| Personalization Coverage | Percentage of accounts with personalized content | > 80% | Monthly |
| Multi-Threading Depth | Average contacts engaged per account | > 3 | Monthly |
| ABM ROI | Revenue generated vs. ABM investment | > 5x | Quarterly |
| Intent Data Accuracy | Predicted vs. actual buying intent | > 70% | Monthly |

---

## 2. Dashboards

### 2.1 ABM Program Overview

Target account list, engagement levels, and pipeline impact

### 2.2 Account Engagement Tracker

Individual account activity, engagement scores, and progression

### 2.3 Campaign Performance by Segment

ABM campaign metrics by industry, tier, and persona

### 2.4 Intent Data Monitor

Buying signals, intent trends, and predictive scoring

### 2.5 ABM ROI Dashboard

Revenue attribution, pipeline influence, and program ROI

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Engagement Drop | Target account engagement falls below 25% | PagerDuty + Slack #abm-ops |
| Pipeline Stagnation | No new opportunities from ABM for 30 days | PagerDuty + Slack #abm-leadership |
| Personalization Failure | Coverage drops below 60% | Slack #abm-ops |
| Intent Data Inaccuracy | Accuracy drops below 50% | PagerDuty + Slack #data-science |
| Account Churn Risk | High-value target accounts showing disengagement | PagerDuty + Slack #abm-ops |
| Campaign Underperformance | Campaign engagement below 10% for 2 weeks | Slack #abm-alerts |

---

## 4. Troubleshooting

### 4.1 Low account engagement

Review targeting criteria, personalize outreach, and align sales and marketing efforts.

### 4.2 Stalled pipeline

Analyze account progression, identify blockers, and adjust campaign messaging.

### 4.3 Poor intent data quality

Validate data sources, review scoring models, and integrate additional intent providers.

### 4.4 Low personalization coverage

Expand content library, improve account research, and leverage dynamic content.

### 4.5 Multi-threading challenges

Identify additional stakeholders, provide contact-specific content, and coordinate sales outreach.

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
