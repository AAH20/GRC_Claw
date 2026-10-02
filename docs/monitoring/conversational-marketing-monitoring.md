# Conversational Marketing — Monitoring Guide

## Overview

**Project:** conversational-marketing
**Description:** Chatbot, live chat, and conversational AI marketing platform
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Bot Resolution Rate | Percentage of conversations resolved by bot | > 65% | Daily |
| Conversation-to-Lead Rate | Percentage of chats generating leads | > 15% | Daily |
| Customer Satisfaction (Chat) | Post-chat satisfaction rating | > 4.0/5 | Weekly |
| Average Response Time | Time to first bot/agent response | < 10 seconds | Per conversation |
| Handoff Rate | Percentage escalated to human agents | < 35% | Daily |
| Engagement Rate | Percentage of visitors engaging with chat | > 8% | Daily |
| Lead Quality Score | Quality of leads from conversations | > 70/100 | Weekly |
| Conversation Completion Rate | Percentage reaching natural conclusion | > 80% | Daily |

---

## 2. Dashboards

### 2.1 Conversational Marketing Overview

Volume, resolution rates, lead generation, and satisfaction

### 2.2 Bot Performance Monitor

Resolution rates, intent recognition, and fallback analysis

### 2.3 Agent Performance Dashboard

Response times, resolution rates, and quality scores

### 2.4 Conversation Flow Analysis

Common paths, drop-off points, and optimization opportunities

### 2.5 Lead Attribution Dashboard

Lead quality, conversion rates, and revenue impact

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Bot Resolution Drop | Resolution rate falls below 50% | PagerDuty + Slack #convo-ops |
| Response Time Spike | Average response exceeds 30 seconds | PagerDuty + Slack #convo-ops |
| Handoff Rate Surge | Handoff rate exceeds 50% | PagerDuty + Slack #convo-ops |
| Low Satisfaction Score | CSAT falls below 3.5 | PagerDuty + Slack #convo-ops |
| Bot Failure | Chatbot unavailable or error rate exceeds 10% | PagerDuty + Slack #engineering |
| Lead Quality Decline | Quality score falls below 60 | Slack #convo-ops |

---

## 4. Troubleshooting

### 4.1 Low bot resolution

Expand intent coverage, improve training data, and refine conversation flows.

### 4.2 Slow response times

Optimize bot performance, review server capacity, and implement queue management.

### 4.3 High handoff rates

Improve bot capabilities, add self-service options, and enhance knowledge base.

### 4.4 Low satisfaction

Analyze conversation transcripts, improve response quality, and personalize interactions.

### 4.5 Poor lead quality

Refine qualification questions, improve lead scoring, and align with sales criteria.

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
