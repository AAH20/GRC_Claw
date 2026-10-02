# Healthcare Marketing — Monitoring Guide

## Overview

**Project:** healthcare-marketing
**Description:** Healthcare provider marketing, patient acquisition, and engagement
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Patient Acquisition Cost (PAC) | Cost to acquire new patient | < $150 | Monthly |
| Appointment Request Rate | Percentage of visitors requesting appointments | > 5% | Weekly |
| Patient Satisfaction (HCAHPS) | Patient experience scores | > 80th percentile | Quarterly |
| Provider Utilization Rate | Percentage of available appointments filled | > 85% | Weekly |
| Patient Retention Rate | Percentage of patients returning | > 75% | Annually |
| Referral Rate | Percentage of patients referring others | > 20% | Quarterly |
| Campaign ROI | Revenue generated vs. marketing spend | > 3x | Quarterly |
| Compliance Adherence | HIPAA and regulatory compliance score | 100% | Continuous |

---

## 2. Dashboards

### 2.1 Healthcare Marketing Overview

Patient acquisition, satisfaction, utilization, and compliance

### 2.2 Patient Journey Analytics

Awareness-to-appointment funnel, touchpoints, and conversion

### 2.3 Provider Performance Dashboard

Provider ratings, appointment volume, and patient feedback

### 2.4 Campaign Performance Tracker

Campaign metrics, ROI, and channel effectiveness

### 2.5 Compliance Monitor

HIPAA compliance, consent management, and audit status

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Compliance Violation | Any HIPAA or regulatory compliance issue | PagerDuty + Slack #compliance-urgent |
| Patient Acquisition Cost Spike | PAC exceeds $200 | PagerDuty + Slack #healthcare-ops |
| Appointment Request Drop | Rate falls below 3% | PagerDuty + Slack #healthcare-ops |
| Patient Satisfaction Decline | HCAHPS falls below 70th percentile | PagerDuty + Slack #quality-ops |
| Provider Utilization Drop | Rate falls below 75% | Slack #healthcare-ops |
| Referral Rate Decline | Rate falls below 15% | Slack #healthcare-ops |

---

## 4. Troubleshooting

### 4.1 Compliance issues

Immediate review, staff training, and process remediation. Engage legal counsel.

### 4.2 High acquisition costs

Optimize marketing channels, improve targeting, and enhance referral programs.

### 4.3 Low appointment requests

Simplify scheduling process, improve online presence, and enhance patient communication.

### 4.4 Patient satisfaction decline

Address care quality issues, improve communication, and enhance patient experience.

### 4.5 Low provider utilization

Optimize scheduling, expand marketing, and improve patient access options.

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
