# Brand Monitoring — Monitoring Guide

## Overview

**Project:** brand-monitoring
**Description:** Brand reputation tracking, mention monitoring, and sentiment analysis
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Brand Mention Volume | Total mentions across all channels | Growth 10% MoM | Monthly |
| Sentiment Score | Overall brand sentiment rating | > 0.6 (positive) | Daily |
| Share of Voice | Brand mentions vs. competitors | > 25% | Weekly |
| Response Time to Mentions | Average time to respond to brand mentions | < 2 hours | Daily |
| Crisis Detection Accuracy | Correct identification of potential crises | > 90% | Weekly |
| Brand Health Index | Composite brand strength metric | > 70/100 | Weekly |
| Influencer Mention Quality | Quality score of influencer brand mentions | > 75/100 | Weekly |
| Review Site Rating | Average rating across review platforms | > 4.0/5 | Weekly |

---

## 2. Dashboards

### 2.1 Brand Health Overview

Mention volume, sentiment, share of voice, and brand health index

### 2.2 Real-Time Mention Monitor

Live brand mentions across social, news, and review sites

### 2.3 Sentiment Analysis Dashboard

Sentiment trends, emotion detection, and topic analysis

### 2.4 Competitive Brand Tracker

Share of voice, competitive positioning, and market presence

### 2.5 Crisis Alert Monitor

Potential crisis detection, severity assessment, and response status

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Negative Sentiment Spike | Sentiment drops below 0.3 | PagerDuty + Slack #pr-urgent |
| Crisis Detection | Potential brand crisis identified | PagerDuty + Slack #pr-urgent |
| Mention Volume Surge | Mention volume exceeds 300% of baseline | PagerDuty + Slack #pr-team |
| Share of Voice Loss | SOV falls below 15% | Slack #brand-team |
| Review Rating Drop | Average rating falls below 3.5 | PagerDuty + Slack #customer-success |
| Response Time Breach | Response time exceeds 4 hours | Slack #social-team |

---

## 4. Troubleshooting

### 4.1 Negative sentiment surge

Identify root cause, prepare response strategy, and engage with affected communities.

### 4.2 Missed brand mentions

Expand monitoring sources, review keyword coverage, and improve filtering rules.

### 4.3 Slow response times

Implement alert routing, establish response protocols, and increase team coverage.

### 4.4 Declining share of voice

Increase content production, improve SEO, and expand channel presence.

### 4.5 Review rating decline

Address negative reviews promptly, improve customer experience, and encourage positive reviews.

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
