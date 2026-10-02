# Social Media Manager — Monitoring Guide

## Overview

**Project:** social-media-manager
**Description:** Multi-platform social media management and analytics system
**Last Updated:** 2026-10-02
**Owner:** Marketing Operations Team

---

## 1. Key Metrics

| Metric | Description | Target | Frequency |
|--------|-------------|--------|-----------|
| Post Publishing Success Rate | Percentage of scheduled posts published successfully | > 98% | Daily |
| Engagement Rate | Likes, comments, shares per follower | > 3% | Weekly |
| Follower Growth Rate | Net new followers per week | > 2% | Weekly |
| Response Time to Mentions | Average time to respond to mentions/DMs | < 1 hour | Daily |
| Content Calendar Adherence | Percentage of posts published on schedule | > 95% | Weekly |
| Sentiment Score | Overall brand sentiment across platforms | > 0.6 (positive) | Daily |
| Social Share of Voice | Brand mentions vs. competitors | > 25% | Weekly |
| Ad Campaign ROAS | Return on social advertising spend | > 3.0x | Weekly |

---

## 2. Dashboards

### 2.1 Social Media Command Center

Unified view of all platforms: engagement, mentions, and publishing status

### 2.2 Content Calendar Dashboard

Scheduled posts, publishing queue, and calendar adherence

### 2.3 Audience Analytics

Follower growth, demographics, and engagement patterns

### 2.4 Sentiment Analysis Monitor

Real-time brand sentiment, trending topics, and crisis detection

### 2.5 Competitive Social Benchmark

Share of voice, engagement comparison, and competitive positioning

---

## 3. Alerts

| Alert Name | Trigger Condition | Notification Channel |
|------------|-------------------|---------------------|
| Publishing Failure | Post fails to publish to any platform | PagerDuty + Slack #social-team |
| Negative Sentiment Spike | Sentiment score drops below 0.3 | PagerDuty + Slack #pr-team |
| Engagement Rate Drop | Engagement falls below 1% for 3 consecutive days | Slack #social-team |
| API Rate Limit Warning | Approaching platform API rate limits | Slack #engineering-alerts |
| Viral Content Detected | Post engagement exceeds 10x baseline | Slack #social-team |
| Account Security Alert | Unusual login activity or permission changes | PagerDuty + Slack #security |

---

## 4. Troubleshooting

### 4.1 Posts not publishing

Verify platform API tokens, check content policy compliance, and review scheduling configuration.

### 4.2 Engagement declining

Analyze content performance patterns, review posting times, and assess audience relevance.

### 4.3 Negative sentiment surge

Identify root cause, prepare response strategy, and escalate to PR team if needed.

### 4.4 API connection failures

Check token expiration, verify app permissions, and review platform status pages.

### 4.5 Follower growth stagnation

Review content strategy, analyze competitor tactics, and assess hashtag performance.

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
