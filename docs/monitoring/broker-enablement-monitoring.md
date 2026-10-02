# Broker Enablement — Monitoring Guide

## Overview

**Project:** broker-enablement
**Description:** Broker onboarding, training, and performance enablement platform
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Onboarding Completion Rate | Percentage of brokers completing onboarding | > 90% | Monthly |
| Time to First Deal | Days from onboarding to first closed deal | < 30 days | Per broker |
| Training Completion Rate | Percentage of assigned training modules completed | > 85% | Monthly |
| Broker Satisfaction Score | Broker feedback and satisfaction rating | > 4.0/5 | Quarterly |
| Deal Flow Volume | Total deals processed through platform | Growth 10% MoM | Monthly |
| Broker Retention Rate | Percentage of brokers remaining active | > 80% | Quarterly |
| Content Engagement | Platform content usage and interaction rates | > 60% | Monthly |
| Support Ticket Resolution | Average time to resolve broker issues | < 24 hours | Weekly |

---

## 2. Dashboards

### 2.1 Broker Enablement Overview

Onboarding status, training progress, and performance metrics

### 2.2 Onboarding Funnel

Stage-by-stage completion rates and drop-off analysis

### 2.3 Training Effectiveness

Module completion, assessment scores, and knowledge retention

### 2.4 Broker Performance Leaderboard

Deal volume, revenue generated, and activity rankings

### 2.5 Broker Health Score

Composite score: activity, satisfaction, performance, and engagement

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Onboarding Drop-off Spike | Completion rate falls below 70% | Slack #broker-ops |
| Training Non-Compliance | Completion rate falls below 60% | Slack #broker-ops |
| Broker Churn Risk | Health score drops below 40 for any broker | PagerDuty + Slack #broker-success |
| Deal Flow Decline | Monthly deal volume drops by > 15% | Slack #broker-leadership |
| Platform Adoption Drop | Active broker count falls below 75% | Slack #broker-ops |
| Support SLA Breach | Resolution time exceeds 48 hours | Slack #support-alerts |

---

## 4. Troubleshooting

### 4.1 Low onboarding completion

Simplify onboarding flow, provide clearer instructions, and offer live support sessions.

### 4.2 Training engagement issues

Gamify training, reduce module length, and provide completion incentives.

### 4.3 Broker performance decline

Provide coaching, review market conditions, and assess lead quality distribution.

### 4.4 Platform adoption challenges

Improve UX, provide tool training, and gather broker feedback for enhancements.

### 4.5 High broker churn

Conduct exit interviews, improve value proposition, and enhance support responsiveness.

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
