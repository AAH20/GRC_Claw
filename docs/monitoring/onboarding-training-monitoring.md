# Onboarding & Training — Monitoring Guide

## Overview

**Project:** onboarding-training
**Description:** Employee onboarding, training delivery, and learning management system
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Onboarding Completion Rate | Percentage completing onboarding program | > 90% | Monthly |
| Time to Productivity | Days from start to full productivity | < 30 days | Per employee |
| Training Completion Rate | Percentage of assigned training completed | > 85% | Monthly |
| Knowledge Retention Score | Assessment scores 30 days post-training | > 80% | Monthly |
| Training Satisfaction | Participant feedback rating | > 4.2/5 | Per course |
| Certification Pass Rate | Percentage passing certification exams | > 80% | Per cohort |
| Content Freshness | Percentage of training content updated quarterly | > 70% | Quarterly |
| Manager Satisfaction | Manager rating of new hire readiness | > 4.0/5 | Quarterly |

---

## 2. Dashboards

### 2.1 Onboarding Progress Overview

Cohort progress, completion rates, and time-to-productivity

### 2.2 Training Effectiveness Dashboard

Completion rates, assessment scores, and knowledge retention

### 2.3 Content Quality Monitor

Content freshness, relevance scores, and update status

### 2.4 Learner Engagement Tracker

Activity, participation, and satisfaction metrics

### 2.5 Manager Feedback Dashboard

New hire readiness ratings and manager satisfaction

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Onboarding Drop-off | Completion rate falls below 75% | PagerDuty + Slack #hr-ops |
| Training Non-Completion | Completion rate falls below 70% | Slack #training-ops |
| Knowledge Retention Issue | Retention score falls below 70% | PagerDuty + Slack #training-ops |
| Certification Failure Spike | Pass rate falls below 60% | PagerDuty + Slack #training-ops |
| Content Staleness | Content older than 6 months exceeds 30% | Slack #training-ops |
| Low Satisfaction Score | Training satisfaction falls below 3.5 | Slack #training-ops |

---

## 4. Troubleshooting

### 4.1 Low onboarding completion

Simplify onboarding flow, provide clearer milestones, and assign onboarding buddies.

### 4.2 Poor knowledge retention

Implement spaced repetition, add practical exercises, and improve content engagement.

### 4.3 Low certification pass rates

Review exam difficulty, provide additional preparation resources, and offer retake opportunities.

### 4.4 Content becoming stale

Establish content review schedule, assign content owners, and implement update reminders.

### 4.5 Low satisfaction scores

Gather detailed feedback, improve content quality, and enhance delivery methods.

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
