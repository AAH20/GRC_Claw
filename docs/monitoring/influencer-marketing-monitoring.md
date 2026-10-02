# Influencer Marketing — Monitoring Guide

## Overview

**Project:** influencer-marketing
**Description:** Influencer discovery, campaign management, and performance tracking
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Influencer Discovery Accuracy | Relevance score of identified influencers | > 0.80 | Weekly |
| Campaign Reach | Total audience reached through influencer content | Growth 20% QoQ | Quarterly |
| Engagement Rate | Likes, comments, shares per follower | > 4% | Per campaign |
| Cost Per Engagement (CPE) | Average cost per engagement | < $0.50 | Per campaign |
| Brand Safety Score | Influencer content brand alignment rating | > 85/100 | Weekly |
| ROI | Revenue generated vs. influencer spend | > 3x | Per campaign |
| Content Approval Rate | Percentage of content approved without revision | > 70% | Monthly |
| Audience Authenticity | Percentage of genuine followers | > 80% | Weekly |

---

## 2. Dashboards

### 2.1 Influencer Marketing Overview

Campaign performance, reach, engagement, and ROI

### 2.2 Influencer Discovery Matrix

Identified influencers, relevance scores, and audience overlap

### 2.3 Campaign Performance Tracker

Individual campaign metrics, content performance, and deliverables

### 2.4 Brand Safety Monitor

Content compliance, sentiment analysis, and risk flags

### 2.5 ROI Attribution Dashboard

Revenue attribution, cost analysis, and program ROI

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Brand Safety Violation | Influencer content flagged for brand misalignment | PagerDuty + Slack #pr-team |
| Engagement Rate Drop | Campaign engagement falls below 2% | Slack #influencer-ops |
| Influencer Fraud Detected | Audience authenticity falls below 60% | PagerDuty + Slack #influencer-ops |
| Campaign Underperformance | ROI falls below 1.5x | Slack #influencer-ops |
| Content Approval Delays | Approval time exceeds 72 hours | Slack #influencer-ops |
| Influencer Availability Loss | Key influencer becomes unavailable | Slack #influencer-ops |

---

## 4. Troubleshooting

### 4.1 Low engagement rates

Review influencer selection, content quality, and audience alignment. Test different content formats.

### 4.2 Brand safety issues

Strengthen content guidelines, improve vetting process, and implement pre-approval workflows.

### 4.3 Fraud detection

Use third-party verification tools, review follower quality metrics, and blacklist fraudulent accounts.

### 4.4 Poor ROI

Renegotiate contracts, improve tracking implementation, and optimize campaign targeting.

### 4.5 Content approval bottlenecks

Streamline approval process, provide clearer guidelines, and set SLA expectations.

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
