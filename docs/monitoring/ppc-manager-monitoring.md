# PPC Manager — Monitoring Guide

## Overview

**Project:** ppc-manager
**Description:** Pay-per-click advertising management across search and display networks
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Return on Ad Spend (ROAS) | Revenue per dollar spent on PPC | > 4.0x | Weekly |
| Cost Per Click (CPC) | Average cost per click | < $2.50 | Daily |
| Click-Through Rate (CTR) | Percentage of impressions resulting in clicks | > 3% | Daily |
| Quality Score | Google Ads quality score average | > 7/10 | Weekly |
| Conversion Rate | Percentage of clicks converting | > 4% | Daily |
| Impression Share | Percentage of available impressions captured | > 70% | Daily |
| Budget Utilization | Percentage of daily budget spent | 85-100% | Daily |
| Ad Relevance Score | Landing page and ad relevance rating | > 8/10 | Weekly |

---

## 2. Dashboards

### 2.1 PPC Performance Overview

Campaign-level ROAS, CPC, CTR, and conversion metrics

### 2.2 Quality Score Tracker

Quality score trends by campaign and keyword

### 2.3 Budget Management Dashboard

Spend pacing, utilization, and forecast vs. actual

### 2.4 Keyword Performance Matrix

Search term analysis, keyword-level ROI, and opportunity identification

### 2.5 Competitive Positioning

Auction insights, impression share, and competitive benchmarks

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| ROAS Critical Drop | ROAS falls below 2.0x for 2 hours | PagerDuty + Slack #ppc-urgent |
| Budget Overspend | Daily spend exceeds 110% of budget | PagerDuty + Slack #ppc-ops |
| Quality Score Drop | Average quality score falls below 5 | Slack #ppc-ops |
| CPC Spike | Average CPC exceeds $5.00 | Slack #ppc-alerts |
| Conversion Tracking Failure | No conversions recorded for 4+ hours | PagerDuty + Slack #engineering |
| Impression Share Loss | Impression share drops below 50% | Slack #ppc-alerts |

---

## 4. Troubleshooting

### 4.1 Sudden ROAS drop

Check for conversion tracking issues, review recent bid changes, and analyze competitor activity.

### 4.2 Rising CPCs

Review keyword competition, improve quality scores, and adjust bidding strategies.

### 4.3 Low impression share

Increase budgets, improve quality scores, and expand keyword coverage.

### 4.4 Poor conversion rates

Audit landing page experience, review ad-to-landing page relevance, and test CTA placement.

### 4.5 Budget pacing issues

Adjust bid strategies, review dayparting settings, and check for delivery throttling.

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
