# Market Research — Monitoring Guide

## Overview

**Project:** market-research
**Description:** Market research, survey management, and consumer insights platform
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Survey Response Rate | Percentage of surveys completed | > 25% | Per survey |
| Data Quality Score | Completeness and accuracy of responses | > 90% | Per survey |
| Insight Generation Latency | Time from data collection to insights | < 48 hours | Per project |
| Sample Representativeness | Demographic alignment with target population | > 85% | Per survey |
| Research Project On-Time Delivery | Percentage of projects delivered on schedule | > 90% | Monthly |
| Insight Actionability | Percentage of insights leading to decisions | > 60% | Quarterly |
| Panel Health Score | Research panel engagement and quality | > 75/100 | Monthly |
| Competitive Intelligence Coverage | Percentage of competitors monitored | > 80% | Quarterly |

---

## 2. Dashboards

### 2.1 Research Project Overview

Active projects, timelines, and delivery status

### 2.2 Survey Performance Dashboard

Response rates, data quality, and completion metrics

### 2.3 Insights Library

Generated insights, action items, and impact tracking

### 2.4 Panel Health Monitor

Panel size, engagement, quality scores, and churn

### 2.5 Competitive Intelligence Dashboard

Competitor tracking, market dynamics, and strategic insights

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Low Response Rate | Response rate falls below 15% | PagerDuty + Slack #research-ops |
| Data Quality Issue | Quality score falls below 80% | PagerDuty + Slack #research-ops |
| Project Delay Risk | Project timeline exceeds 80% without completion | Slack #research-ops |
| Panel Attrition | Panel size drops below minimum threshold | PagerDuty + Slack #research-ops |
| Insight Delivery Breach | Insights not delivered within 72 hours | Slack #research-ops |
| Sample Bias Detected | Representativeness falls below 70% | PagerDuty + Slack #research-ops |

---

## 4. Troubleshooting

### 4.1 Low response rates

Optimize survey design, improve incentives, and test different distribution channels.

### 4.2 Poor data quality

Implement attention checks, review question wording, and improve validation rules.

### 4.3 Project delays

Review scope, allocate additional resources, and adjust timelines with stakeholders.

### 4.4 Panel attrition

Improve engagement, offer better incentives, and expand recruitment channels.

### 4.5 Sample bias

Review sampling methodology, implement quotas, and weight responses appropriately.

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
