# Real Estate Marketing — Monitoring Guide

## Overview

**Project:** real-estate-marketing
**Description:** Real estate marketing, lead generation, and property promotion
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Lead Response Time | Time from inquiry to first contact | < 5 minutes | Per lead |
| Cost Per Lead (CPL) | Average cost per qualified lead | < $25 | Monthly |
| Lead-to-Client Conversion | Percentage of leads becoming clients | > 12% | Monthly |
| Property Listing Views | Average views per listing | Growth 15% QoQ | Quarterly |
| Email Open Rate | Property alert and newsletter open rate | > 25% | Weekly |
| Agent Utilization | Percentage of leads followed up by agents | > 90% | Weekly |
| Campaign ROI | Revenue generated vs. marketing spend | > 5x | Quarterly |
| Listing Syndication Accuracy | Percentage of listings correctly distributed | > 98% | Weekly |

---

## 2. Dashboards

### 2.1 Real Estate Marketing Overview

Lead volume, CPL, conversion, and campaign performance

### 2.2 Property Marketing Dashboard

Listing performance, views, inquiries, and agent follow-up

### 2.3 Lead Management Monitor

Lead status, response times, and conversion tracking

### 2.4 Agent Performance Tracker

Agent lead handling, conversion rates, and client satisfaction

### 2.5 Campaign ROI Dashboard

Campaign metrics, channel performance, and revenue attribution

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Lead Response Delay | Response time exceeds 15 minutes | PagerDuty + Slack #realestate-ops |
| Lead Volume Drop | Lead generation falls below 70% of target | PagerDuty + Slack #realestate-ops |
| CPL Spike | CPL exceeds $40 | PagerDuty + Slack #realestate-ops |
| Conversion Rate Drop | Rate falls below 8% | Slack #realestate-ops |
| Listing Distribution Failure | Syndication accuracy falls below 95% | PagerDuty + Slack #engineering |
| Agent Follow-up Gap | Utilization rate falls below 80% | Slack #realestate-ops |

---

## 4. Troubleshooting

### 4.1 Slow lead response

Implement auto-responders, optimize lead routing, and establish response SLAs.

### 4.2 Low lead volume

Expand marketing channels, improve listing SEO, and enhance property presentation.

### 4.3 High CPL

Optimize ad targeting, improve landing pages, and test different lead magnets.

### 4.4 Low conversion rates

Improve lead nurturing, enhance agent training, and provide better property information.

### 4.5 Listing distribution issues

Verify syndication feeds, check API connections, and validate listing data quality.

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
