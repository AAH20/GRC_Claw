# Email Marketing — Monitoring Guide

## Overview

**Project:** email-marketing
**Description:** Email campaign management, automation, and deliverability platform
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Deliverability Rate | Percentage of emails reaching inbox | > 95% | Daily |
| Open Rate | Percentage of delivered emails opened | > 25% | Per campaign |
| Click-Through Rate | Percentage of opens resulting in clicks | > 3% | Per campaign |
| Conversion Rate | Percentage of clicks resulting in desired action | > 2% | Per campaign |
| Bounce Rate | Percentage of emails that bounce | < 2% | Daily |
| Unsubscribe Rate | Percentage unsubscribing per campaign | < 0.5% | Per campaign |
| List Growth Rate | Net new subscribers per month | > 5% | Monthly |
| Spam Complaint Rate | Percentage marking as spam | < 0.1% | Daily |

---

## 2. Dashboards

### 2.1 Email Performance Overview

Campaign-level metrics: delivery, opens, clicks, and conversions

### 2.2 Deliverability Monitor

Inbox placement, bounce rates, and sender reputation

### 2.3 Automation Flow Performance

Trigger-based email metrics and funnel analysis

### 2.4 List Health Dashboard

Growth, engagement segmentation, and churn analysis

### 2.5 A/B Testing Results

Subject line, content, and send time experiment outcomes

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Deliverability Drop | Inbox placement falls below 90% | PagerDuty + Slack #email-ops |
| Bounce Rate Spike | Bounce rate exceeds 5% | PagerDuty + Slack #email-ops |
| Spam Complaint Surge | Spam rate exceeds 0.3% | PagerDuty + Slack #email-ops |
| Campaign Send Failure | Bulk send fails or is throttled | PagerDuty + Slack #engineering |
| Unsubscribe Spike | Unsubscribe rate exceeds 1% for any campaign | Slack #marketing-ops |
| Sender Reputation Drop | Sender score falls below 70 | PagerDuty + Slack #email-ops |

---

## 4. Troubleshooting

### 4.1 Low deliverability

Check sender reputation, verify SPF/DKIM/DMARC, review list quality, and assess content triggers.

### 4.2 High bounce rates

Clean email list, verify list source quality, and implement double opt-in validation.

### 4.3 Low open rates

Test subject lines, optimize send times, and improve sender name recognition.

### 4.4 Low click rates

Review email design, CTA placement, and content relevance. Test mobile responsiveness.

### 4.5 Spam folder placement

Audit content for spam triggers, verify authentication, and review sending infrastructure.

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
