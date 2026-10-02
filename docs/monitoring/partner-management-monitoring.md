# Partner Management — Monitoring Guide

## Overview

**Project:** partner-management
**Description:** Partner relationship management, co-marketing, and channel enablement
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Partner Satisfaction Score | Partner feedback and satisfaction rating | > 4.0/5 | Quarterly |
| Partner-Generated Revenue | Revenue attributed to partner channel | Growth 15% QoQ | Quarterly |
| Partner Onboarding Time | Time from signing to productive partner | < 30 days | Per partner |
| Co-Marketing Campaign Success | Joint campaign performance vs. targets | > 80% | Per campaign |
| Partner Enablement Completion | Percentage completing training/certification | > 75% | Quarterly |
| Partner Churn Rate | Percentage of partners leaving program | < 10% | Annually |
| Deal Registration Accuracy | Percentage of registrations validated | > 90% | Monthly |
| Partner Portal Adoption | Active portal users / total partners | > 70% | Monthly |

---

## 2. Dashboards

### 2.1 Partner Ecosystem Overview

Partner count, revenue, satisfaction, and program health

### 2.2 Partner Performance Dashboard

Individual partner metrics, tier status, and growth trends

### 2.3 Co-Marketing Campaign Tracker

Joint campaign performance, ROI, and deliverables

### 2.4 Partner Enablement Monitor

Training progress, certification status, and readiness

### 2.5 Partner Portal Analytics

Portal usage, feature adoption, and engagement metrics

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Partner Churn Risk | Partner satisfaction drops below 3.5 | PagerDuty + Slack #partner-ops |
| Revenue Decline | Partner revenue drops by > 20% QoQ | PagerDuty + Slack #partner-leadership |
| Onboarding Delay | Partner onboarding exceeds 45 days | Slack #partner-ops |
| Enablement Non-Completion | Completion rate falls below 60% | Slack #partner-ops |
| Deal Registration Dispute | Dispute rate exceeds 10% | PagerDuty + Slack #partner-ops |
| Portal Adoption Drop | Active users fall below 50% | Slack #partner-ops |

---

## 4. Troubleshooting

### 4.1 Partner dissatisfaction

Conduct partner interviews, address pain points, and improve program value.

### 4.2 Revenue decline

Analyze partner performance, identify underperformers, and provide additional support.

### 4.3 Slow onboarding

Streamline onboarding process, provide dedicated support, and set clear milestones.

### 4.4 Low enablement completion

Improve training content, provide incentives, and offer flexible learning options.

### 4.5 Deal registration disputes

Clarify registration rules, improve validation process, and establish clear policies.

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
