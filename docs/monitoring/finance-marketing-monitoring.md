# Finance Marketing — Monitoring Guide

## Overview

**Project:** finance-marketing
**Description:** Financial services marketing, lead generation, and compliance
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Lead Generation Volume | Qualified leads generated per month | Growth 10% MoM | Monthly |
| Cost Per Lead (CPL) | Average cost per qualified lead | < $75 | Monthly |
| Lead-to-Customer Conversion | Percentage of leads becoming customers | > 8% | Monthly |
| Customer Acquisition Cost (CAC) | Total cost to acquire customer | < $500 | Monthly |
| Compliance Approval Rate | Percentage of marketing materials approved | > 95% | Weekly |
| Campaign ROI | Revenue generated vs. marketing spend | > 4x | Quarterly |
| Email Engagement Rate | Open and click rates for financial content | > 20% open | Weekly |
| Ad Disapproval Rate | Percentage of ads rejected by platforms | < 5% | Weekly |

---

## 2. Dashboards

### 2.1 Finance Marketing Overview

Lead volume, CPL, conversion, and campaign performance

### 2.2 Compliance Dashboard

Material approval status, regulatory compliance, and audit trail

### 2.3 Lead Funnel Analytics

Lead-to-customer journey, conversion rates, and drop-off analysis

### 2.4 Campaign Performance Tracker

Campaign metrics, ROI, and channel effectiveness

### 2.5 Customer Value Analytics

Customer lifetime value, product penetration, and revenue

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Compliance Violation | Marketing material violates regulations | PagerDuty + Slack #compliance-urgent |
| Lead Volume Drop | Lead generation falls below 80% of target | PagerDuty + Slack #finance-ops |
| CPL Spike | CPL exceeds $100 | PagerDuty + Slack #finance-ops |
| Conversion Rate Drop | Rate falls below 5% | PagerDuty + Slack #finance-ops |
| Ad Disapproval Spike | Disapproval rate exceeds 10% | Slack #finance-ops |
| Campaign Underperformance | ROI falls below 2x | Slack #finance-ops |

---

## 4. Troubleshooting

### 4.1 Compliance violations

Review material, consult compliance team, and implement pre-approval workflows.

### 4.2 Low lead volume

Expand channels, improve targeting, and optimize landing pages and forms.

### 4.3 High CPL

Optimize ad spend, improve lead quality, and test different messaging and offers.

### 4.4 Low conversion rates

Improve lead nurturing, enhance follow-up process, and align sales and marketing.

### 4.5 Ad disapprovals

Review platform policies, modify ad content, and implement compliance checks.

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
