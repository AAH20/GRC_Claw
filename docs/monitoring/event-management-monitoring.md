# Event Management — Monitoring Guide

## Overview

**Project:** event-management
**Description:** Event planning, execution, and analytics platform
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Registration Conversion Rate | Percentage of invitees who register | > 40% | Per event |
| Attendance Rate | Percentage of registrants who attend | > 70% | Per event |
| Event Satisfaction Score | Post-event attendee rating | > 4.2/5 | Per event |
| Lead Generation Count | Qualified leads captured per event | Growth 15% YoY | Per event |
| Event ROI | Revenue generated vs. event cost | > 3x | Per event |
| Check-in Processing Time | Average time to check in attendee | < 30 seconds | Per attendee |
| Engagement Score | Session attendance, app usage, and interactions | > 60/100 | Per event |
| Sponsor Satisfaction | Sponsor feedback and ROI rating | > 4.0/5 | Per event |

---

## 2. Dashboards

### 2.1 Event Performance Overview

Registration, attendance, satisfaction, and ROI metrics

### 2.2 Real-Time Event Monitor

Live attendance, engagement, and session analytics

### 2.3 Lead Capture Dashboard

Lead quality, follow-up status, and conversion tracking

### 2.4 Sponsor ROI Tracker

Sponsor deliverables, exposure metrics, and satisfaction

### 2.5 Event Comparison Analysis

Cross-event performance trends and benchmarking

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Registration Rate Drop | Registration falls below 25% of target | PagerDuty + Slack #event-ops |
| Attendance Rate Concern | Attendance falls below 50% | PagerDuty + Slack #event-ops |
| Low Satisfaction Score | Post-event rating falls below 3.5 | PagerDuty + Slack #event-ops |
| Lead Capture Failure | Lead scanning/check-in system failure | PagerDuty + Slack #engineering |
| Engagement Drop | Real-time engagement falls below 40% | Slack #event-ops |
| Sponsor Deliverable Miss | Sponsor commitment not fulfilled | PagerDuty + Slack #sponsor-ops |

---

## 4. Troubleshooting

### 4.1 Low registration rates

Improve event marketing, optimize registration page, and leverage speaker promotion.

### 4.2 Poor attendance

Send reminders, offer incentives, and improve event value proposition.

### 4.3 Low satisfaction

Gather detailed feedback, identify pain points, and improve event logistics.

### 4.4 Lead capture issues

Test equipment before event, provide backup processes, and train staff.

### 4.5 Low engagement

Improve session content, add interactive elements, and optimize event app.

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
