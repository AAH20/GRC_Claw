# Monitoring & Observability Architecture for Agentic AI Marketing

**Version:** 1.0  
**Date:** 2026-10-01  
**Owner:** Ahmed Hassan  
**Status:** Draft  
**Related Docs:** `ARCHITECTURE.md`, `grc-claw-reliability-implementation-guide.md`, `grc-claw-reporting-implementation-guide.md`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Agent Performance Monitoring](#3-agent-performance-monitoring)
4. [Campaign Performance Tracking](#4-campaign-performance-tracking)
5. [Real-Time Dashboards](#5-real-time-dashboards)
6. [Alerting & Notification System](#6-alerting--notification-system)
7. [Anomaly Detection](#7-anomaly-detection)
8. [Cost Tracking & Optimization](#8-cost-tracking--optimization)
9. [Integration with Existing Observability Stack](#9-integration-with-existing-observability-stack)
10. [Data Flow Diagrams](#10-data-flow-diagrams)
11. [Implementation Roadmap](#11-implementation-roadmap)
12. [Appendix](#12-appendix)

---

## 1. Executive Summary

Agentic AI marketing systems operate as autonomous, multi-step pipelines that plan, execute, and optimize marketing campaigns with minimal human intervention. This autonomy introduces unique observability challenges: non-deterministic behavior, cascading failures across tool calls, cost variability from LLM token usage, and the need to correlate agent decisions with business outcomes.

This document defines a comprehensive monitoring and observability layer that provides:

- **Full-fidelity tracing** of every agent decision, tool call, and LLM interaction
- **Real-time campaign performance** visibility with sub-second latency
- **Intelligent alerting** that distinguishes between expected variance and true anomalies
- **Cost governance** with per-agent, per-campaign, and per-token budget enforcement
- **Seamless integration** with existing Prometheus/Grafana/Loki/Tempo stacks

The architecture follows a **four-layer model**: Collection → Processing → Storage → Presentation, with cross-cutting concerns for security, privacy, and compliance.

---

## 2. Architecture Overview

### 2.1 Design Principles

| Principle | Rationale |
|-----------|-----------|
| **Agent-Native Observability** | Traditional APM assumes deterministic request/response cycles. Agent systems require tracing that captures reasoning chains, tool orchestration, and multi-turn planning. |
| **Business-Outcome Correlation** | Technical metrics (latency, token count) must be linked to business metrics (ROAS, CPA, conversion rate) to enable true optimization. |
| **Cost-Aware by Design** | LLM token costs are the primary variable cost. Every metric pipeline must capture and attribute costs at the most granular level. |
| **Privacy-Preserving** | Marketing data often contains PII. All observability pipelines must support field-level redaction and GDPR-compliant retention. |
| **Progressive Enhancement** | Start with basic metrics, add tracing, then anomaly detection. Each layer delivers independent value. |

### 2.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Real-Time   │  │  Campaign    │  │   Agent      │  │   Cost     │ │
│  │  Dashboards  │  │  Analytics   │  │  Health      │  │  Explorer  │ │
│  │  (Grafana)   │  │  (Grafana)   │  │  (Grafana)   │  │  (Custom)  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │                 │        │
│  ┌──────┴─────────────────┴─────────────────┴─────────────────┴──────┐ │
│  │                    ALERTING & NOTIFICATION                         │ │
│  │         Alertmanager → PagerDuty / Slack / Email / Webhook         │ │
│  └──────────────────────────────┬────────────────────────────────────┘ │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                        STORAGE LAYER                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Prometheus  │  │    Loki      │  │    Tempo     │  │  ClickHouse │ │
│  │  (Metrics)   │  │   (Logs)     │  │  (Traces)    │  │  (Events)   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │                 │        │
│  ┌──────┴─────────────────┴─────────────────┴─────────────────┴──────┐ │
│  │                    ANOMALY DETECTION ENGINE                        │ │
│  │              (Isolation Forest + Statistical + Rules)              │ │
│  └──────────────────────────────┬────────────────────────────────────┘ │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                       PROCESSING LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Fluent     │  │   Vector     │  │  Stream      │  │  Feature   │ │
│  │   Bit        │  │  (Log Ship)  │  │  Processor   │  │  Store     │ │
│  │  (Collect)   │  │              │  │  (Flink)     │  │  (Redis)   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │                 │        │
│  ┌──────┴─────────────────┴─────────────────┴─────────────────┴──────┐ │
│  │                    COST AGGREGATION PIPELINE                      │ │
│  │         Token Counter → Cost Calculator → Budget Enforcer          │ │
│  └──────────────────────────────┬────────────────────────────────────┘ │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────┐
│                        COLLECTION LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Agent SDK   │  │  Campaign    │  │   LLM        │  │  External  │ │
│  │  Instrumentor│  │  Tracker     │  │  Call Logger │  │  API Mon.  │ │
│  │  (OpenTelemetry│  │  (Events)    │  │  (Tokens)    │  │  (Uptime)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Metrics** | Prometheus + Mimir | Industry standard, long-term storage with Mimir, PromQL for complex queries |
| **Logs** | Loki | Label-based log aggregation, cost-effective at scale, native Grafana integration |
| **Traces** | Tempo | OpenTelemetry-native, object-storage backend, cost-effective for high-cardinality agent traces |
| **Events** | ClickHouse | Columnar storage for high-volume event streams, sub-second analytical queries |
| **Dashboards** | Grafana | Unified visualization, extensive plugin ecosystem, alerting integration |
| **Alerting** | Alertmanager + PagerDuty | Multi-channel routing, escalation policies, on-call management |
| **Stream Processing** | Apache Flink | Stateful stream processing for real-time anomaly detection and cost aggregation |
| **Feature Store** | Redis | Low-latency feature serving for ML-based anomaly detection |
| **Collection** | OpenTelemetry SDK | Vendor-neutral instrumentation, auto-instrumentation for common frameworks |

---

## 3. Agent Performance Monitoring

### 3.1 What to Monitor

Agent performance monitoring tracks the health, efficiency, and effectiveness of individual AI agents and multi-agent orchestrations.

#### 3.1.1 Agent Lifecycle Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `agent_execution_total` | Counter | Total agent executions | `agent_id`, `agent_type`, `status` |
| `agent_execution_duration_seconds` | Histogram | End-to-end execution time | `agent_id`, `agent_type` |
| `agent_planning_duration_seconds` | Histogram | Time spent in planning/reasoning | `agent_id` |
| `agent_tool_call_duration_seconds` | Histogram | Time per tool call | `agent_id`, `tool_name` |
| `agent_tool_calls_total` | Counter | Total tool invocations | `agent_id`, `tool_name`, `status` |
| `agent_llm_calls_total` | Counter | Total LLM API calls | `agent_id`, `model`, `provider` |
| `agent_llm_tokens_total` | Counter | Total tokens consumed | `agent_id`, `model`, `token_type` (input/output) |
| `agent_llm_cost_dollars` | Counter | Total LLM cost | `agent_id`, `model`, `provider` |
| `agent_retry_total` | Counter | Retry attempts | `agent_id`, `retry_reason` |
| `agent_error_total` | Counter | Error occurrences | `agent_id`, `error_type`, `error_source` |
| `agent_queue_wait_seconds` | Histogram | Time waiting in orchestration queue | `agent_id`, `priority` |
| `agent_context_window_utilization` | Gauge | % of context window used | `agent_id`, `model` |
| `agent_tool_success_rate` | Gauge | Rolling success rate per tool | `agent_id`, `tool_name` |

#### 3.1.2 Agent Reasoning Quality Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `agent_plan_steps_total` | Counter | Number of steps in generated plan |
| `agent_plan_revision_total` | Counter | Plan revisions during execution |
| `agent_goal_achievement_rate` | Gauge | % of goals successfully achieved |
| `agent_human_intervention_total` | Counter | Times human intervention was required |
| `agent_tool_selection_accuracy` | Gauge | % of appropriate tool selections |
| `agent_output_quality_score` | Gauge | LLM-judged output quality (0-1) |

### 3.2 Instrumentation Strategy

#### 3.2.1 OpenTelemetry-Based Agent Tracing

Every agent execution is traced as a root span with child spans for each phase:

```
agent_execution (root span)
├── planning_phase
│   ├── llm_call (model: gpt-4, tokens: 1200)
│   ├── llm_call (model: gpt-4, tokens: 800)
│   └── plan_validation
├── execution_phase
│   ├── tool_call: search_competitors
│   │   ├── api_request
│   │   └── response_parsing
│   ├── tool_call: generate_content
│   │   ├── llm_call (model: gpt-4, tokens: 2400)
│   │   └── content_validation
│   └── tool_call: publish_campaign
│       ├── api_request
│       └── confirmation
├── evaluation_phase
│   ├── llm_call (model: gpt-4, tokens: 600)
│   └── quality_scoring
└── cleanup_phase
```

#### 3.2.2 SDK Integration Pattern

```python
from grc_claw.observability import AgentTracer, trace_agent

class MarketingAgent:
    def __init__(self, agent_id: str, config: AgentConfig):
        self.tracer = AgentTracer(
            agent_id=agent_id,
            agent_type="campaign_optimizer",
            config=config
        )
    
    @trace_agent(
        capture_llm_io=True,
        capture_tool_io=True,
        redact_pii=True
    )
    async def execute(self, task: AgentTask) -> AgentResult:
        # Agent logic here — automatically traced
        plan = await self.planner.create_plan(task)
        results = await self.executor.run(plan)
        return self.evaluator.score(results)
```

#### 3.2.3 Auto-Instrumentation Hooks

For agents built on common frameworks, auto-instrumentation is provided:

| Framework | Hook Point | Auto-Captured |
|-----------|-----------|--------------|
| LangChain | `BaseCallbackHandler` | Chain execution, LLM calls, tool usage |
| AutoGPT | `CommandRegistry` | Command execution, file I/O |
| CrewAI | `AgentExecutor` | Agent delegation, task completion |
| Custom | Decorator/Context Manager | Any async function |

### 3.3 Agent Health Score

A composite health score (0-100) is computed per agent, updated every 60 seconds:

```
Health Score = w1 * SuccessRate + w2 * (1 - ErrorRate) + w3 * (1 - LatencyScore) 
             + w4 * CostEfficiency + w5 * GoalAchievementRate

Where:
  w1 = 0.25  (SuccessRate: rolling 1h window)
  w2 = 0.20  (ErrorRate: rolling 1h window)
  w3 = 0.20  (LatencyScore: p95 latency vs SLA)
  w4 = 0.15  (CostEfficiency: actual cost vs budget)
  w5 = 0.20  (GoalAchievementRate: rolling 24h window)
```

Health score thresholds:
- **90-100**: Healthy — no action needed
- **70-89**: Degraded — investigate during business hours
- **50-69**: Unhealthy — page on-call engineer
- **0-49**: Critical — immediate escalation, consider circuit breaker

---

## 4. Campaign Performance Tracking

### 4.1 Campaign Metrics Framework

Campaign tracking bridges the gap between agent actions and business outcomes.

#### 4.1.1 Campaign Lifecycle Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `campaign_created_total` | Counter | Campaigns created | `agent_id`, `channel`, `objective` |
| `campaign_activated_total` | Counter | Campaigns activated | `agent_id`, `channel` |
| `campaign_paused_total` | Counter | Campaigns paused | `agent_id`, `pause_reason` |
| `campaign_completed_total` | Counter | Campaigns completed | `agent_id`, `outcome` |
| `campaign_budget_spend_dollars` | Counter | Budget consumed | `campaign_id`, `channel` |
| `campaign_budget_remaining_dollars` | Gauge | Budget remaining | `campaign_id` |
| `campaign_roas` | Gauge | Return on ad spend | `campaign_id`, `channel` |
| `campaign_cpa_dollars` | Gauge | Cost per acquisition | `campaign_id`, `channel` |
| `campaign_ctr` | Gauge | Click-through rate | `campaign_id`, `creative_id` |
| `campaign_conversion_rate` | Gauge | Conversion rate | `campaign_id`, `funnel_stage` |
| `campaign_impressions_total` | Counter | Impressions served | `campaign_id`, `placement` |
| `campaign_clicks_total` | Counter | Clicks received | `campaign_id`, `placement` |
| `campaign_conversions_total` | Counter | Conversions achieved | `campaign_id`, `conversion_type` |
| `campaign_revenue_attributed_dollars` | Counter | Attributed revenue | `campaign_id`, `attribution_model` |

#### 4.1.2 Agent-Attribution Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `campaign_agent_actions_total` | Counter | Actions taken by agent on campaign |
| `campaign_agent_optimization_total` | Counter | Optimization decisions made |
| `campaign_agent_override_total` | Counter | Times agent overrode default settings |
| `campaign_agent_recommendation_acceptance` | Gauge | % of agent recommendations accepted |
| `campaign_agent_lift_vs_baseline` | Gauge | Performance lift vs non-agent baseline |

### 4.2 Attribution Models

The system supports multiple attribution models, switchable per campaign:

| Model | Description | Use Case |
|-------|-------------|----------|
| **Last-Click** | 100% credit to last touchpoint | Simple funnel analysis |
| **First-Click** | 100% credit to first touchpoint | Awareness campaign evaluation |
| **Linear** | Equal credit across touchpoints | Balanced view |
| **Time-Decay** | Exponential decay from conversion | Short conversion windows |
| **Data-Driven** | ML-based attribution (Markov chains) | Complex multi-channel journeys |
| **Agent-Attribution** | Credit based on agent decision impact | Isolating agent contribution |

### 4.3 Campaign Funnel Tracking

```
Impression → Click → Landing Page → Engagement → Lead → Opportunity → Conversion
    │            │           │              │          │          │           │
    ▼            ▼           ▼              ▼          ▼          ▼           ▼
  CTR      Bounce Rate   Time on Page   Form Fill   MQL Rate   SQL Rate   Win Rate
  CPC      CPV           Scroll Depth   CTA Clicks  Lead Score  Deal Size  Revenue
```

Each funnel stage is tracked with:
- **Volume counts** at each stage
- **Conversion rates** between stages
- **Drop-off reasons** (auto-classified by agent)
- **Agent interventions** at each stage
- **Time-in-stage** distributions

### 4.4 Custom Event Schema

All campaign events follow a unified schema:

```json
{
  "event_id": "evt_abc123",
  "event_type": "campaign.conversion",
  "timestamp": "2026-10-01T14:32:00.000Z",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "agent_id": "agent_campaign_optimizer_01",
  "campaign_id": "cmp_summer_sale_2026",
  "channel": "paid_social",
  "metadata": {
    "conversion_type": "purchase",
    "revenue": 149.99,
    "currency": "USD",
    "attribution_model": "data_driven",
    "agent_decision_id": "dec_xyz789",
    "funnel_stage": "conversion"
  },
  "pii_fields_redacted": true
}
```

---

## 5. Real-Time Dashboards

### 5.1 Dashboard Inventory

#### 5.1.1 Executive Dashboard

**Purpose:** High-level business performance for C-suite and marketing leadership.

| Panel | Data Source | Refresh Rate |
|-------|------------|--------------|
| Total Revenue Attributed | ClickHouse | 5s |
| Active Campaigns | Prometheus | 10s |
| Agent-Generated Revenue | ClickHouse | 30s |
| ROAS by Channel | ClickHouse | 30s |
| Cost per Acquisition Trend | Prometheus | 30s |
| Agent Health Overview | Prometheus | 10s |
| Budget Utilization | Prometheus | 10s |
| Top Performing Campaigns | ClickHouse | 60s |

#### 5.1.2 Agent Operations Dashboard

**Purpose:** Real-time agent health and performance for ML/AI operations team.

| Panel | Data Source | Refresh Rate |
|-------|------------|--------------|
| Agent Health Scores | Prometheus | 10s |
| Agent Execution Rate | Prometheus | 5s |
| LLM Token Consumption | Prometheus | 5s |
| LLM Cost per Minute | Prometheus | 5s |
| Tool Call Success Rates | Prometheus | 10s |
| Error Rate by Type | Prometheus | 10s |
| Context Window Utilization | Prometheus | 10s |
| Queue Depth by Agent | Prometheus | 5s |
| Retry Rate | Prometheus | 10s |
| Agent Dependency Graph | Tempo | 30s |

#### 5.1.3 Campaign Performance Dashboard

**Purpose:** Campaign-level analytics for marketing operations team.

| Panel | Data Source | Refresh Rate |
|-------|------------|--------------|
| Campaign Funnel Visualization | ClickHouse | 10s |
| Impressions/Clicks/Conversions | ClickHouse | 5s |
| Spend vs Budget | Prometheus | 10s |
| ROAS by Campaign | ClickHouse | 30s |
| Creative Performance | ClickHouse | 60s |
| Audience Segment Performance | ClickHouse | 60s |
| A/B Test Results | ClickHouse | 60s |
| Agent Optimization Timeline | Tempo | 30s |

#### 5.1.4 Cost Explorer Dashboard

**Purpose:** Granular cost analysis and optimization for finance and operations.

| Panel | Data Source | Refresh Rate |
|-------|------------|--------------|
| Total LLM Cost (Real-Time) | Prometheus | 5s |
| Cost by Agent | Prometheus | 10s |
| Cost by Model | Prometheus | 10s |
| Cost by Campaign | ClickHouse | 30s |
| Cost per Conversion | ClickHouse | 30s |
| Token Usage Breakdown | Prometheus | 10s |
| Budget Forecast | ClickHouse | 300s |
| Cost Anomaly Flags | Anomaly Engine | 60s |

#### 5.1.5 Trace Explorer Dashboard

**Purpose:** Deep-dive into individual agent executions for debugging.

| Panel | Data Source | Refresh Rate |
|-------|------------|--------------|
| Trace Waterfall | Tempo | On-demand |
| LLM Call Details | Tempo | On-demand |
| Tool Call Timeline | Tempo | On-demand |
| Token Usage per Call | Tempo | On-demand |
| Error Stack Traces | Loki | On-demand |
| Agent Decision Log | Loki | On-demand |

### 5.2 Dashboard Implementation

All dashboards are defined as code (JSON) and stored in version control:

```json
{
  "dashboard": {
    "title": "Agent Operations — Real-Time",
    "uid": "agent-ops-realtime",
    "refresh": "5s",
    "time": {"from": "now-1h", "to": "now"},
    "panels": [
      {
        "id": 1,
        "title": "Agent Health Scores",
        "type": "stat",
        "targets": [{
          "expr": "grc_agent_health_score",
          "legendFormat": "{{agent_id}}"
        }],
        "thresholds": [
          {"color": "red", "value": 0},
          {"color": "yellow", "value": 50},
          {"color": "green", "value": 70}
        ]
      },
      {
        "id": 2,
        "title": "LLM Cost per Minute",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(grc_agent_llm_cost_dollars_total[1m]) * 60",
          "legendFormat": "{{agent_id}} — {{model}}"
        }]
      }
    ]
  }
}
```

### 5.3 Real-Time Data Pipeline

For sub-second dashboard refresh rates, the data pipeline uses:

1. **Agent SDK** → emits metrics via Prometheus remote write (push-based, 5s interval)
2. **Campaign Events** → Kafka → Flink → ClickHouse (end-to-end < 2s)
3. **LLM Token Counters** → in-memory aggregation → Prometheus exporter (5s flush)
4. **Trace Spans** → OpenTelemetry Collector → Tempo (streaming, < 1s)

---

## 6. Alerting & Notification System

### 6.1 Alert Taxonomy

Alerts are classified by severity and domain:

#### 6.1.1 Severity Levels

| Level | Name | Response SLA | Notification Channel |
|-------|------|-------------|---------------------|
| P0 | Critical | 5 minutes | PagerDuty + Phone Call + Slack |
| P1 | High | 15 minutes | PagerDuty + Slack |
| P2 | Medium | 1 hour | Slack + Email |
| P3 | Low | 4 hours | Slack |
| P4 | Info | Next business day | Email digest |

#### 6.1.2 Alert Categories

| Category | Examples | Default Severity |
|----------|---------|-----------------|
| **Agent Failure** | Agent crash, unresponsive, stuck in loop | P0 |
| **LLM Provider** | API down, rate limited, elevated latency | P1 |
| **Cost Anomaly** | Spend > 150% of forecast, token spike | P1 |
| **Campaign Performance** | ROAS < threshold, CPA > budget | P2 |
| **Data Quality** | Missing events, schema mismatch | P2 |
| **Security** | PII leak detected, unauthorized access | P0 |
| **Dependency** | External API down, DB connection lost | P1 |
| **SLA Violation** | p95 latency > SLA, availability < 99.9% | P1 |

### 6.2 Alert Rules

#### 6.2.1 Prometheus Alert Rules

```yaml
groups:
  - name: agent_critical
    rules:
      - alert: AgentDown
        expr: up{job="grc-agents"} == 0
        for: 1m
        labels:
          severity: critical
          team: ai-ops
        annotations:
          summary: "Agent {{ $labels.agent_id }} is down"
          description: "Agent {{ $labels.agent_id }} has been unreachable for more than 1 minute."
          runbook: "https://wiki.internal/runbooks/agent-down"
          
      - alert: AgentHighErrorRate
        expr: |
          rate(grc_agent_error_total[5m]) 
          / rate(grc_agent_execution_total[5m]) > 0.1
        for: 2m
        labels:
          severity: high
          team: ai-ops
        annotations:
          summary: "Agent {{ $labels.agent_id }} error rate > 10%"
          
      - alert: AgentStuckInLoop
        expr: |
          grc_agent_retry_total - grc_agent_retry_total offset 5m > 20
        for: 0m
        labels:
          severity: critical
          team: ai-ops
        annotations:
          summary: "Agent {{ $labels.agent_id }} appears stuck in retry loop"
          
      - alert: AgentContextWindowNearLimit
        expr: grc_agent_context_window_utilization > 0.9
        for: 30s
        labels:
          severity: high
          team: ai-ops
        annotations:
          summary: "Agent {{ $labels.agent_id }} context window > 90%"

  - name: cost_alerts
    rules:
      - alert: LLMCostSpike
        expr: |
          (
            rate(grc_agent_llm_cost_dollars_total[5m]) 
            > 2 * rate(grc_agent_llm_cost_dollars_total[1h] offset 1h)
          ) and (
            rate(grc_agent_llm_cost_dollars_total[5m]) > 10
          )
        for: 2m
        labels:
          severity: high
          team: finops
        annotations:
          summary: "LLM cost spike detected for {{ $labels.agent_id }}"
          
      - alert: CampaignBudgetExceeded
        expr: |
          grc_campaign_budget_spend_dollars 
          / grc_campaign_budget_total_dollars > 1.0
        for: 0m
        labels:
          severity: high
          team: marketing-ops
        annotations:
          summary: "Campaign {{ $labels.campaign_id }} exceeded budget"
          
      - alert: DailyBudgetForecastExceeded
        expr: |
          predict_linear(grc_agent_llm_cost_dollars_total[6h], 86400) 
          > grc_budget_daily_limit
        for: 5m
        labels:
          severity: medium
          team: finops
        annotations:
          summary: "Daily LLM cost forecast exceeds budget"

  - name: campaign_performance
    rules:
      - alert: CampaignROASBelowThreshold
        expr: grc_campaign_roas < 1.5
        for: 15m
        labels:
          severity: medium
          team: marketing-ops
        annotations:
          summary: "Campaign {{ $labels.campaign_id }} ROAS below 1.5"
          
      - alert: CampaignCPAExceeded
        expr: grc_campaign_cpa_dollars > grc_campaign_target_cpa * 1.5
        for: 15m
        labels:
          severity: medium
          team: marketing-ops
        annotations:
          summary: "Campaign {{ $labels.campaign_id }} CPA 50% above target"
          
      - alert: CampaignZeroConversions
        expr: |
          rate(grc_campaign_conversions_total[30m]) == 0
          and grc_campaign_budget_spend_dollars > 100
        for: 30m
        labels:
          severity: high
          team: marketing-ops
        annotations:
          summary: "Campaign {{ $labels.campaign_id }} has zero conversions with significant spend"
```

#### 6.2.2 Multi-Channel Notification Routing

```yaml
# Alertmanager configuration
route:
  group_by: ['alertname', 'severity', 'team']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default-slack'
  
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      group_wait: 0s
      repeat_interval: 15m
      
    - match:
        severity: high
      receiver: 'pagerduty-high'
      group_wait: 15s
      repeat_interval: 30m
      
    - match:
        team: finops
      receiver: 'finops-slack'
      
    - match:
        team: marketing-ops
      receiver: 'marketing-slack'

receivers:
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_CRITICAL_KEY}'
        severity: critical
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        
  - name: 'pagerduty-high'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_HIGH_KEY}'
        severity: warning
        
  - name: 'default-slack'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#ai-ops-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'
        send_resolved: true
        
  - name: 'finops-slack'
    slack_configs:
      - api_url: '${SLACK_FINOPS_WEBHOOK_URL}'
        channel: '#finops-alerts'
        
  - name: 'marketing-slack'
    slack_configs:
      - api_url: '${SLACK_MARKETING_WEBHOOK_URL}'
        channel: '#marketing-ops-alerts'
```

### 6.3 Alert Enrichment

Every alert is automatically enriched with contextual information:

```json
{
  "alert_id": "alert_20261001_001",
  "alert_name": "AgentHighErrorRate",
  "severity": "high",
  "fingerprint": "agent_campaign_optimizer_01:high_error_rate",
  "enrichment": {
    "recent_traces": ["trace_id_1", "trace_id_2", "trace_id_3"],
    "recent_errors": [
      {"type": "LLMTimeout", "count": 12, "last_seen": "2026-10-01T14:30:00Z"},
      {"type": "ToolFailure", "count": 3, "last_seen": "2026-10-01T14:28:00Z"}
    ],
    "affected_campaigns": ["cmp_summer_sale_2026"],
    "cost_impact_1h": 45.23,
    "similar_past_incidents": [
      {"date": "2026-09-15", "resolution": "Increased timeout", "duration_min": 23}
    ],
    "suggested_runbook": "https://wiki.internal/runbooks/agent-high-error-rate",
    "dashboard_link": "https://grafana.internal/d/agent-ops?var-agent=agent_campaign_optimizer_01"
  }
}
```

### 6.4 Alert Suppression & Grouping

To prevent alert fatigue:

| Mechanism | Description |
|-----------|-------------|
| **Grouping** | Alerts with same fingerprint are grouped; only first fires |
| **Inhibition** | `AgentDown` inhibits `AgentHighErrorRate` for same agent |
| **Silencing** | Maintenance windows auto-silence non-critical alerts |
| **Threshold Escalation** | P3 → P2 → P1 if unacknowledged for 30/60/120 min |
| **Flapping Detection** | Alerts firing > 5 times in 10 min are auto-suppressed with summary |

---

## 7. Anomaly Detection

### 7.1 Detection Methods

The anomaly detection engine uses a multi-layer approach:

#### 7.1.1 Layer 1: Rule-Based Detection (Real-Time, < 1s)

Simple threshold and pattern rules evaluated in-stream by Flink:

```python
class RuleBasedDetector:
    """Evaluated on every event, sub-millisecond latency"""
    
    RULES = [
        Rule(
            name="token_spike",
            condition="token_count > 3 * rolling_mean(token_count, '1h')",
            severity="high",
            cooldown="5m"
        ),
        Rule(
            name="cost_burst",
            condition="cost_in_window('5m') > 5 * cost_in_window('1h') / 12",
            severity="high",
            cooldown="10m"
        ),
        Rule(
            name="zero_conversion_streak",
            condition="conversions == 0 AND spend > 100 AND duration > '30m'",
            severity="medium",
            cooldown="30m"
        ),
        Rule(
            name="error_rate_spike",
            condition="error_rate('5m') > 3 * error_rate('1h')",
            severity="high",
            cooldown="5m"
        ),
        Rule(
            name="latency_degradation",
            condition="p95_latency('5m') > 2 * p95_latency('1h')",
            severity="medium",
            cooldown="10m"
        ),
    ]
```

#### 7.1.2 Layer 2: Statistical Detection (Near Real-Time, < 30s)

Statistical models computed on sliding windows:

| Model | Algorithm | Window | Metrics |
|-------|-----------|--------|---------|
| **Z-Score** | Modified Z-score (MAD-based) | 5m, 15m, 1h | Token count, cost, latency |
| **IQR** | Interquartile range outliers | 1h, 6h | Error rate, success rate |
| **EWMA** | Exponentially weighted moving average | 1h, 24h | All rate metrics |
| **Seasonal Decomposition** | STL decomposition | 7d baseline | Campaign performance metrics |
| **Grubbs' Test** | Outlier detection | 1h | Cost per execution |

#### 7.1.3 Layer 3: ML-Based Detection (Batch, 5-15 min)

ML models for complex pattern detection:

| Model | Type | Features | Detection Target |
|-------|------|----------|-----------------|
| **Isolation Forest** | Unsupervised | 25+ agent/campaign features | Multi-dimensional anomalies |
| **LSTM Autoencoder** | Deep Learning | Time-series of metrics | Temporal pattern anomalies |
| **Prophet** | Time-Series Forecasting | Historical metric values | Forecast deviations |
| **DBSCAN** | Clustering | Agent behavior embeddings | Behavioral drift |
| **Bayesian Changepoint** | Sequential Analysis | Metric streams | Sudden distribution shifts |

### 7.2 Feature Engineering

Features are computed and stored in Redis for low-latency serving:

```python
FEATURES = {
    # Real-time features (updated every 5s)
    "realtime": [
        "token_count_5m", "token_count_1h", "token_count_24h",
        "cost_5m", "cost_1h", "cost_24h",
        "error_rate_5m", "error_rate_1h",
        "latency_p50_5m", "latency_p95_5m", "latency_p99_5m",
        "success_rate_5m", "success_rate_1h",
        "tool_call_count_5m", "tool_call_count_1h",
        "queue_depth", "active_executions",
    ],
    
    # Derived features (updated every 60s)
    "derived": [
        "token_count_zscore_1h", "cost_zscore_1h",
        "error_rate_delta_1h", "latency_trend_1h",
        "cost_per_success_1h", "cost_per_conversion_1h",
        "tool_diversity_score", "plan_complexity_score",
    ],
    
    # Contextual features (updated every 300s)
    "contextual": [
        "hour_of_day", "day_of_week", "is_holiday",
        "active_campaign_count", "total_budget_remaining",
        "model_availability", "dependency_health_score",
    ]
}
```

### 7.3 Anomaly Scoring & Alerting

Each anomaly receives a composite score:

```
AnomalyScore = w1 * Severity + w2 * Confidence + w3 * BusinessImpact + w4 * Novelty

Where:
  w1 = 0.30  (Severity: 0-1 based on deviation magnitude)
  w2 = 0.25  (Confidence: model confidence 0-1)
  w3 = 0.30  (BusinessImpact: estimated revenue/cost impact)
  w4 = 0.15  (Novelty: inverse of historical frequency)
```

Score thresholds:
- **0.0-0.3**: Log only — no alert
- **0.3-0.6**: Info alert — Slack notification
- **0.6-0.8**: Warning alert — Slack + Email
- **0.8-1.0**: Critical alert — PagerDuty

### 7.4 Anomaly Feedback Loop

Analysts can label anomalies as true/false positive, which feeds back into model retraining:

```sql
-- ClickHouse table for feedback
CREATE TABLE anomaly_feedback (
    anomaly_id String,
    timestamp DateTime64(3),
    model_name String,
    anomaly_score Float32,
    is_true_positive UInt8,
    feedback_comment String,
    analyst_id String,
    campaign_id Nullable(String),
    agent_id Nullable(String)
) ENGINE = MergeTree()
ORDER BY (timestamp, model_name);
```

Models are retrained weekly using the feedback data, with A/B testing of new model versions.

---

## 8. Cost Tracking & Optimization

### 8.1 Cost Attribution Model

Every dollar spent is attributed through a multi-dimensional model:

```
Total Cost
├── LLM API Costs (by model, by provider, by agent, by campaign)
│   ├── Input Tokens
│   ├── Output Tokens
│   ├── Cached Tokens (discounted)
│   └── Fine-tuning Costs (amortized)
├── Infrastructure Costs
│   ├── Compute (CPU/GPU for agent execution)
│   ├── Memory
│   ├── Storage (logs, traces, metrics)
│   └── Network Egress
├── Tool/API Costs
│   ├── External API calls (search, social, ad platforms)
│   ├── Database operations
│   └── Third-party SaaS
└── Human Costs
    ├── On-call incident response
    ├── Manual campaign interventions
    └── Agent development/maintenance
```

### 8.2 Real-Time Cost Tracking

#### 8.2.1 Token-Level Cost Pipeline

```
LLM Response
    │
    ▼
Token Counter (per response)
    │
    ├── input_tokens, output_tokens, cached_tokens
    │
    ▼
Cost Calculator (per model pricing table)
    │
    ├── cost = (input_tokens * input_price) 
    │        + (output_tokens * output_price)
    │        + (cached_tokens * cached_price)
    │
    ▼
Cost Aggregator (per agent, per campaign, per time window)
    │
    ├── Prometheus counter: grc_agent_llm_cost_dollars_total
    ├── ClickHouse event: cost_event (for analytics)
    └── Redis gauge: real-time cost for budget enforcement
    │
    ▼
Budget Enforcer (per agent, per campaign, per time period)
    │
    ├── Soft limit: 80% → warning alert
    ├── Hard limit: 100% → circuit breaker (pause agent)
    └── Forecast limit: predicted exceedance → proactive alert
```

#### 8.2.2 Cost Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `grc_cost_llm_total_dollars` | Counter | Total LLM cost (all agents) |
| `grc_cost_llm_by_agent_dollars` | Counter | LLM cost per agent |
| `grc_cost_llm_by_model_dollars` | Counter | LLM cost per model |
| `grc_cost_llm_by_campaign_dollars` | Counter | LLM cost per campaign |
| `grc_cost_per_conversion_dollars` | Gauge | LLM cost per conversion |
| `grc_cost_per_click_dollars` | Gauge | LLM cost per click |
| `grc_cost_efficiency_score` | Gauge | Revenue / Total Cost ratio |
| `grc_budget_utilization_ratio` | Gauge | Spent / Budget |
| `grc_budget_forecast_dollars` | Gauge | Predicted total cost at current burn rate |
| `grc_cost_anomaly_score` | Gauge | Anomaly detection score for cost |

### 8.3 Budget Management

#### 8.3.1 Budget Hierarchy

```
Organization Budget ($50,000/month)
├── Agent Budgets
│   ├── Campaign Optimizer Agent ($15,000/month)
│   ├── Content Generation Agent ($10,000/month)
│   ├── Audience Research Agent ($8,000/month)
│   └── Analytics Agent ($7,000/month)
├── Infrastructure Budget ($5,000/month)
└── Reserve ($5,000/month)
    └── Auto-reallocated from underutilized budgets
```

#### 8.3.2 Budget Enforcement Policies

| Policy | Trigger | Action |
|--------|---------|--------|
| **Soft Limit** | 80% of budget consumed | Slack warning to team |
| **Hard Limit** | 100% of budget consumed | Pause agent, require manual approval to resume |
| **Rate Limit** | Burn rate > 2x forecast | Throttle agent execution rate |
| **Daily Cap** | Daily spend > daily/30 budget | Pause until next day |
| **Per-Campaign Cap** | Campaign spend > campaign budget | Pause specific campaign |
| **Emergency Stop** | Total spend > 120% of org budget | Stop all agents, page on-call |

#### 8.3.3 Budget Configuration

```yaml
budgets:
  organization:
    monthly_limit: 50000
    currency: USD
    alert_thresholds: [0.5, 0.8, 0.95, 1.0]
    
  agents:
    campaign_optimizer:
      monthly_limit: 15000
      daily_limit: 500
      per_campaign_limit: 2000
      models:
        - gpt-4
        - claude-3-opus
      enforcement: hard_stop
      
    content_generator:
      monthly_limit: 10000
      daily_limit: 333
      models:
        - gpt-4
        - claude-3-sonnet
      enforcement: throttle
      
  campaigns:
    summer_sale_2026:
      total_budget: 5000
      daily_budget: 200
      max_cpa: 25.00
      auto_pause_on_breach: true
```

### 8.4 Cost Optimization Recommendations

The system generates automated optimization recommendations:

| Recommendation Type | Trigger | Action |
|---------------------|---------|--------|
| **Model Downgrade** | Task complexity < model capability | Suggest cheaper model (GPT-4 → GPT-3.5) |
| **Prompt Optimization** | High token count for simple tasks | Suggest prompt compression |
| **Caching** | Repeated similar prompts | Enable semantic caching |
| **Batch Processing** | Many small requests | Batch into fewer larger requests |
| **Rate Limiting** | Unnecessary frequency | Reduce execution frequency |
| **Campaign Pause** | ROAS < 1.0 for > 24h | Recommend campaign pause |
| **Budget Reallocation** | Underutilized budget | Reallocate to high-performing agent |

---

## 9. Integration with Existing Observability Stack

### 9.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXISTING STACK                                │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │Prometheus│  │  Grafana │  │  ELK/Loki│  │  Jaeger      │   │
│  │(Metrics) │  │(Dashboard)│  │  (Logs)  │  │  (Traces)    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │
│       │              │              │               │           │
│  ┌────┴──────────────┴──────────────┴───────────────┴───────┐  │
│  │              OpenTelemetry Collector                      │  │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ Receivers│  │Processors│  │ Exporters│  │ Connectors│  │  │
│  │  │ OTLP    │  │ Batch    │  │ Prometheus│  │  Span→   │  │  │
│  │  │ Jaeger  │  │ Memory   │  │ Loki     │  │  Metric  │  │  │
│  │  │ Zipkin  │  │ Tail-    │  │ Tempo    │  │  Metric→ │  │  │
│  │  │         │  │ Sampling │  │          │  │  Span    │  │  │
│  │  └─────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │         GRC CLAW AGENT LAYER                              │  │
│  │                           │                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │  Agent   │  │ Campaign │  │   LLM    │  │  Cost    │  │  │
│  │  │  SDK     │  │  Tracker │  │  Logger  │  │ Tracker  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 OpenTelemetry Collector Configuration

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  
  prometheus:
    config:
      scrape_configs:
        - job_name: 'grc-agents'
          scrape_interval: 5s
          static_configs:
            - targets: ['agent-01:9090', 'agent-02:9090']
            
  jaeger:
    protocols:
      grpc:
        endpoint: 0.0.0.0:14250
      thrift_http:
        endpoint: 0.0.0.0:14268

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
    
  memory_limiter:
    limit_mib: 512
    spike_limit_mib: 128
    
  tail_sampling:
    decision_wait: 10s
    num_traces: 100000
    expected_new_traces_per_sec: 1000
    policies:
      - name: errors
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow
        type: latency
        latency: {threshold_ms: 1000}
      - name: agent-critical
        type: string_attribute
        string_attribute: {key: agent.critical, values: [true]}
        
  resource:
    attributes:
      - key: service.namespace
        value: grc-claw
        action: upsert
      - key: deployment.environment
        from_attribute: k8s.namespace.name
        action: insert
        
  filter/metrics:
    metrics:
      exclude:
        match_type: regexp
        metric_names:
          - "go_.*"
          - "process_.*"

exporters:
  prometheusremotewrite:
    endpoint: http://mimir:9090/api/v1/push
    headers:
      X-Scope-OrgID: grc-claw
      
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
    labels:
      attributes:
        service.name: "service"
        agent.id: "agent_id"
        campaign.id: "campaign_id"
        
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true
      
  clickhouse:
    endpoint: tcp://clickhouse:9000
    database: grc_observability
    logs_table: agent_logs
    traces_table: agent_traces
    metrics_table: agent_metrics
    
  logging:
    loglevel: warn

connectors:
  spanmetrics:
    histogram:
      explicit:
        buckets: [10ms, 50ms, 100ms, 200ms, 500ms, 1s, 2s, 5s, 10s]
    dimensions:
      - name: tool.name
        default: unknown
      - name: model.name
        default: unknown

service:
  pipelines:
    traces:
      receivers: [otlp, jaeger]
      processors: [memory_limiter, tail_sampling, resource, batch]
      exporters: [otlp/tempo, clickhouse]
      
    metrics:
      receivers: [otlp, prometheus, spanmetrics]
      processors: [memory_limiter, filter/metrics, resource, batch]
      exporters: [prometheusremotewrite, clickhouse]
      
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [loki, clickhouse]
```

### 9.3 Integration Points

#### 9.3.1 Prometheus Integration

| Aspect | Integration |
|--------|------------|
| **Metric Format** | Prometheus exposition format via remote write |
| **Naming Convention** | `grc_{domain}_{metric}_{unit}` (e.g., `grc_agent_llm_cost_dollars`) |
| **Label Cardinality** | Max 50 labels per metric; high-cardinality dimensions (user_id) go to ClickHouse |
| **Scrape Interval** | 5s for agent metrics, 15s for campaign metrics |
| **Long-Term Storage** | Mimir for 13-month retention, S3 for indefinite |
| **Recording Rules** | Pre-aggregate common queries (1m, 5m, 1h rollups) |

#### 9.3.2 Grafana Integration

| Aspect | Integration |
|--------|------------|
| **Dashboard Provisioning** | GitOps — dashboards as code in `dashboards/` directory |
| **Data Source** | Prometheus (metrics), Loki (logs), Tempo (traces), ClickHouse (events) |
| **Annotations** | Auto-annotate deployments, agent version changes, campaign launches |
| **Variables** | Global variables: `$agent`, `$campaign`, `$channel`, `$time_range` |
| **Alerting** | Grafana Alerting → Alertmanager → PagerDuty/Slack |

#### 9.3.3 Jaeger/Tempo Integration

| Aspect | Integration |
|--------|------------|
| **Trace Format** | OpenTelemetry (OTLP) native |
| **Context Propagation** | W3C Trace Context standard |
| **Span Links** | Link agent spans to campaign spans |
| **Trace Retention** | 7 days hot (Tempo), 90 days cold (S3) |
| **Tail Sampling** | 100% errors, 10% slow (>1s), 1% normal |

#### 9.3.4 ELK/Loki Integration

| Aspect | Integration |
|--------|------------|
| **Log Format** | JSON with trace_id/span_id correlation |
| **Log Levels** | DEBUG (dev), INFO (staging), WARN (production) |
| **PII Redaction** | Field-level redaction via processor before shipping |
| **Log Retention** | 30 days hot, 1 year cold (S3) |
| **Label Schema** | `service`, `agent_id`, `campaign_id`, `level`, `trace_id` |

#### 9.3.5 PagerDuty Integration

| Aspect | Integration |
|--------|------------|
| **Service Creation** | Auto-create PagerDuty services per agent |
| **Event API** | v2 Events API for alert routing |
| **Escalation Policies** | Per-team escalation with time-based rules |
| **On-Call Sync** | Sync with PagerDuty schedules for rotation awareness |
| **Incident Correlation** | Group related alerts into single incident |

### 9.4 Backward Compatibility

For teams with existing monitoring investments:

| Existing Tool | Migration Path |
|--------------|---------------|
| **Datadog** | OTLP → Datadog Agent → Datadog. Use Datadog's OTLP ingestion. |
| **New Relic** | OTLP → New Relic OTLP endpoint. Map `grc_*` metrics to NR. |
| **Splunk** | HEC endpoint for logs, OTel Collector → Splunk Observability. |
| **CloudWatch** | OTel Collector → CloudWatch agent → CloudWatch metrics/logs. |
| **Custom** | OTLP is vendor-neutral; any OTLP-compatible backend works. |

---

## 10. Data Flow Diagrams

### 10.1 End-to-End Data Flow

```
┌─────────┐     ┌──────────┐     ┌───────────┐     ┌──────────┐
│  Agent  │────▶│  Agent   │────▶│  OpenTelemetry │────▶│  Tempo   │
│Execution│     │  SDK     │     │  Collector    │     │ (Traces) │
└─────────┘     └────┬─────┘     └─────┬─────┘     └──────────┘
                     │                  │
                     │                  ├──────────▶ ┌──────────┐
                     │                  │            │  Loki    │
                     │                  │            │  (Logs)  │
                     │                  │            └──────────┘
                     │                  │
                     │                  ├──────────▶ ┌──────────┐
                     │                  │            │Prometheus│
                     │                  │            │(Metrics) │
                     │                  │            └──────────┘
                     │                  │
                     │                  └──────────▶ ┌──────────┐
                     │                               │ClickHouse│
                     │                               │ (Events)  │
                     │                               └──────────┘
                     │
                     ▼
              ┌──────────┐     ┌───────────┐     ┌──────────┐
              │  Kafka   │────▶│  Flink    │────▶│  Redis   │
              │ (Events) │     │ (Process) │     │(Features)│
              └──────────┘     └─────┬─────┘     └──────────┘
                                     │
                                     ▼
                              ┌───────────┐
                              │  Anomaly  │
                              │  Engine   │
                              └─────┬─────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              ┌──────────┐  ┌──────────┐   ┌──────────┐
              │Alertmanager│ │ Grafana  │   │  Cost    │
              │          │  │(Dashboard)│   │ Enforcer │
              └────┬─────┘  └──────────┘   └──────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
  ┌──────────┐ ┌──────┐ ┌──────┐
  │PagerDuty │ │Slack │ │Email │
  └──────────┘ └──────┘ └──────┘
```

### 10.2 Agent Execution Trace Flow

```
User Request
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ Agent Orchestrator                                          │
│                                                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐  │
│  │ Planner │──▶│ Executor│──▶│Evaluator│──▶│ Reporter│  │
│  │         │   │         │   │         │   │         │  │
│  │ LLM Call│   │Tool Calls│  │LLM Call │   │  Emit   │  │
│  │         │   │         │   │         │   │  Event  │  │
│  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘  │
│       │             │             │             │        │
│       ▼             ▼             ▼             ▼        │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Span Context (trace_id)                 │ │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐ │ │
│  │  │Span 1│─▶│Span 2│─▶│Span 3│─▶│Span 4│─▶│Span 5│ │ │
│  │  │plan  │  │tool  │  │tool  │  │eval  │  │report│ │ │
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘ │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
OpenTelemetry Collector
    │
    ├──▶ Tempo (full trace)
    ├──▶ Prometheus (span metrics)
    ├──▶ Loki (structured logs)
    └──▶ ClickHouse (analytics events)
```

### 10.3 Campaign Event Flow

```
Campaign Event (impression, click, conversion)
    │
    ▼
┌──────────┐
│  Agent   │ (enriches with agent context)
│  SDK     │
└────┬─────┘
     │
     ▼
┌──────────┐
│  Kafka   │ (topic: campaign.events)
│  Topic   │
└────┬─────┘
     │
     ├──────────────────────────────────────┐
     │                                      │
     ▼                                      ▼
┌──────────┐                         ┌──────────┐
│  Flink   │                         │ClickHouse│
│  Stream  │                         │ (raw)    │
│  Process │                         └──────────┘
└────┬─────┘
     │
     ├──▶ Real-time aggregations → Redis
     │
     ├──▶ Anomaly detection → Alertmanager
     │
     ├──▶ Cost calculation → Prometheus
     │
     └──▶ Feature engineering → Feature Store
              │
              ▼
         ┌──────────┐
         │  ML      │
         │  Models  │
         └──────────┘
```

### 10.4 Cost Tracking Flow

```
LLM API Response
    │
    ▼
┌──────────────────┐
│  Token Counter   │
│  (per response)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Cost Calculator │
│  (model pricing) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│  Cost Aggregator │────▶│  Redis           │
│  (multi-dim)     │     │  (real-time)     │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐     ┌──────────────────┐
│  Prometheus      │     │  Budget Enforcer │
│  (time-series)   │     │  (circuit breaker)│
└──────────────────┘     └──────────────────┘
         │
         ▼
┌──────────────────┐
│  ClickHouse      │
│  (analytics)     │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│  Cost Explorer   │
│  Dashboard       │
└──────────────────┘
```

### 10.5 Alert Flow

```
Metric/Event/Anomaly
    │
    ▼
┌──────────────────┐
│  Alert Rule      │
│  Evaluation      │
│  (Prometheus/    │
│   Flink/ML)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Alert Grouping  │
│  & Deduplication │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Alert Enrichment│
│  (traces, logs,  │
│   runbooks)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Alertmanager   │
│  (routing)       │
└────────┬─────────┘
         │
    ┌────┼────┬────────┐
    │    │    │        │
    ▼    ▼    ▼        ▼
 PagerDuty Slack Email Webhook
    │    │    │        │
    ▼    ▼    ▼        ▼
┌──────────────────────┐
│  Acknowledgment &    │
│  Resolution Tracking │
└──────────────────────┘
```

---

## 11. Implementation Roadmap

### 11.1 Phase Overview

```
Phase 1 (Weeks 1-4)     Phase 2 (Weeks 5-8)     Phase 3 (Weeks 9-12)    Phase 4 (Weeks 13-16)
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  FOUNDATION     │────▶│  VISIBILITY     │────▶│  INTELLIGENCE   │────▶│  OPTIMIZATION   │
│                 │     │                 │     │                 │     │                 │
│ • Instrumentation│    │ • Dashboards    │     │ • Anomaly Det.  │     │ • Auto-Optimize │
│ • Basic Metrics │     │ • Alerting      │     │ • Cost Optimize │     │ • ML Models     │
│ • Logging       │     │ • Tracing       │     │ • Forecasting   │     │ • Self-Healing  │
│ • CI/CD Integration│  │ • Log Pipeline  │     │ • Recommendations│    │ • Advanced UI   │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 11.2 Phase 1: Foundation (Weeks 1-4)

**Goal:** Basic visibility into agent operations.

| Week | Task | Deliverable | Owner |
|------|------|-------------|-------|
| 1 | Set up OpenTelemetry Collector | Collector deployed in K8s | Platform |
| 1 | Deploy Prometheus + Mimir | Metrics storage ready | Platform |
| 1 | Deploy Loki | Log aggregation ready | Platform |
| 2 | Instrument agent SDK with OTel | SDK v0.1 with tracing | AI Eng |
| 2 | Implement token/cost counter | Cost tracking in SDK | AI Eng |
| 2 | Define metric naming convention | `METRICS.md` spec | AI Eng |
| 3 | Deploy Tempo | Trace storage ready | Platform |
| 3 | Implement campaign event schema | Event schema v1 | AI Eng |
| 3 | Set up Kafka for event streaming | Kafka cluster ready | Platform |
| 4 | Deploy Grafana + datasources | Grafana with 4 datasources | Platform |
| 4 | Create basic agent health dashboard | Dashboard v1 | AI Eng |
| 4 | Set up Alertmanager + PagerDuty | Basic alerting live | Platform |
| 4 | **Phase 1 Review** | Demo: agent metrics visible end-to-end | All |

**Phase 1 Exit Criteria:**
- [ ] Every agent execution generates a trace
- [ ] Token consumption and cost tracked per agent
- [ ] Basic dashboards show agent health
- [ ] Alerts fire for agent downtime
- [ ] All metrics follow naming convention

### 11.3 Phase 2: Visibility (Weeks 5-8)

**Goal:** Comprehensive dashboards, alerting, and log pipeline.

| Week | Task | Deliverable | Owner |
|------|------|-------------|-------|
| 5 | Deploy ClickHouse | Event analytics DB ready | Platform |
| 5 | Build Flink stream processor | Real-time aggregations | Data Eng |
| 5 | Implement campaign tracker | Campaign event pipeline | AI Eng |
| 6 | Create campaign performance dashboard | Dashboard v2 | AI Eng |
| 6 | Create cost explorer dashboard | Dashboard v3 | AI Eng |
| 6 | Implement log correlation (trace_id in logs) | Unified log search | AI Eng |
| 7 | Build alert rule library | 25+ alert rules | AI Eng |
| 7 | Implement alert enrichment | Contextual alerts | AI Eng |
| 7 | Set up Slack/Email notification channels | Multi-channel alerting | Platform |
| 8 | Implement trace explorer dashboard | Trace debugging UI | AI Eng |
| 8 | Create executive dashboard | Dashboard v4 | AI Eng |
| 8 | **Phase 2 Review** | Demo: full observability stack live | All |

**Phase 2 Exit Criteria:**
- [ ] All 5 dashboards operational
- [ ] 25+ alert rules active
- [ ] Log-trace-metric correlation working
- [ ] Campaign performance tracked end-to-end
- [ ] Cost per agent/campaign visible in real-time

### 11.4 Phase 3: Intelligence (Weeks 9-12)

**Goal:** Anomaly detection, cost optimization, and forecasting.

| Week | Task | Deliverable | Owner |
|------|------|-------------|-------|
| 9 | Deploy Redis feature store | Feature serving ready | Data Eng |
| 9 | Implement rule-based anomaly detector | Real-time rules in Flink | Data Eng |
| 9 | Build statistical anomaly detector | Z-score, IQR, EWMA models | Data Eng |
| 10 | Train ML anomaly models | Isolation Forest + LSTM | ML Eng |
| 10 | Implement anomaly scoring & alerting | Composite anomaly score | ML Eng |
| 10 | Build anomaly feedback loop | Feedback table + retraining | ML Eng |
| 11 | Implement budget management system | Budget config + enforcement | AI Eng |
| 11 | Build cost optimization recommendations | Recommendation engine | AI Eng |
| 11 | Implement budget forecasting | Prophet-based forecasting | ML Eng |
| 12 | Create anomaly investigation dashboard | Dashboard v5 | AI Eng |
| 12 | Implement cost anomaly detection | Cost-specific anomaly rules | Data Eng |
| 12 | **Phase 3 Review** | Demo: anomaly detection catching issues | All |

**Phase 3 Exit Criteria:**
- [ ] Anomaly detection catches injected test anomalies
- [ ] Budget enforcement pauses agents at limits
- [ ] Cost optimization recommendations generated
- [ ] Forecast accuracy > 80% for daily cost
- [ ] Feedback loop operational

### 11.5 Phase 4: Optimization (Weeks 13-16)

**Goal:** Automated optimization, self-healing, and advanced analytics.

| Week | Task | Deliverable | Owner |
|------|------|-------------|-------|
| 13 | Implement auto-scaling for agents | KEDA-based autoscaling | Platform |
| 13 | Build self-healing runbooks | Automated remediation | AI Eng |
| 13 | Implement A/B testing for agent versions | Experiment framework | AI Eng |
| 14 | Build advanced cost analytics | Unit economics dashboard | AI Eng |
| 14 | Implement multi-agent correlation | Cross-agent impact analysis | Data Eng |
| 14 | Create SLA/SLO dashboard | SLO tracking + error budgets | AI Eng |
| 15 | Implement predictive scaling | ML-based capacity planning | ML Eng |
| 15 | Build natural language query interface | "Ask Grafana" for metrics | AI Eng |
| 15 | Implement compliance reporting | GDPR/CCPA audit reports | Compliance |
| 16 | Performance tuning & optimization | < 5s dashboard latency | All |
| 16 | Documentation & runbooks | Complete ops documentation | All |
| 16 | **Phase 4 Review** | Demo: self-healing in action | All |

**Phase 4 Exit Criteria:**
- [ ] Auto-scaling responds to load changes
- [ ] Self-healing resolves common issues without human
- [ ] SLO dashboards track error budgets
- [ ] Compliance reports generated automatically
- [ ] Full documentation complete

### 11.6 Resource Requirements

| Phase | Engineers | Duration | Key Dependencies |
|-------|-----------|----------|-----------------|
| Phase 1 | 2 Platform + 2 AI Eng | 4 weeks | K8s cluster, cloud account |
| Phase 2 | 2 Platform + 2 AI Eng + 1 Data Eng | 4 weeks | Phase 1 complete |
| Phase 3 | 2 Data Eng + 2 ML Eng + 1 AI Eng | 4 weeks | Phase 2 complete |
| Phase 4 | 2 AI Eng + 1 ML Eng + 1 Platform | 4 weeks | Phase 3 complete |

### 11.7 Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Metric cardinality explosion | Medium | High | Strict label limits, high-cardinality to ClickHouse |
| Alert fatigue | High | Medium | Careful threshold tuning, grouping, suppression |
| LLM cost of monitoring itself | Medium | Medium | Tail sampling, metric aggregation, log level control |
| Data pipeline latency | Medium | High | Flink tuning, Redis caching, backpressure handling |
| Model drift in anomaly detection | Medium | Medium | Weekly retraining, feedback loop, A/B testing |
| PII leakage in observability data | Low | Critical | Field-level redaction, encryption, access controls |

---

## 12. Appendix

### 12.1 Metric Naming Convention

```
grc_{domain}_{subdomain}_{metric_name}_{unit}

Domains:
  agent    — Agent execution metrics
  campaign — Campaign performance metrics
  cost     — Cost and budget metrics
  llm      — LLM-specific metrics
  system   — Infrastructure metrics

Examples:
  grc_agent_execution_duration_seconds
  grc_campaign_roas_ratio
  grc_cost_llm_total_dollars
  grc_llm_tokens_total_count
  grc_system_cpu_usage_ratio
```

### 12.2 Label Standards

| Label | Description | Example Values |
|-------|-------------|---------------|
| `agent_id` | Unique agent identifier | `agent_campaign_optimizer_01` |
| `agent_type` | Agent category | `optimizer`, `generator`, `researcher` |
| `campaign_id` | Campaign identifier | `cmp_summer_sale_2026` |
| `channel` | Marketing channel | `paid_social`, `email`, `display` |
| `model` | LLM model name | `gpt-4`, `claude-3-opus` |
| `provider` | LLM provider | `openai`, `anthropic` |
| `tool_name` | Tool identifier | `search_competitors`, `publish_campaign` |
| `status` | Execution status | `success`, `failure`, `timeout` |
| `environment` | Deployment environment | `production`, `staging` |
| `version` | Agent version | `v1.2.3` |

### 12.3 Retention Policies

| Data Type | Hot Storage | Warm Storage | Cold Storage |
|-----------|------------|-------------|-------------|
| Metrics | 15 days (Prometheus) | 13 months (Mimir) | Indefinite (S3) |
| Logs | 30 days (Loki) | 90 days (S3) | 1 year (Glacier) |
| Traces | 7 days (Tempo) | 30 days (S3) | 90 days (Glacier) |
| Events | 90 days (ClickHouse) | 1 year (S3 Parquet) | Indefinite (S3) |
| Anomaly Data | 30 days (Redis) | 1 year (ClickHouse) | Indefinite (S3) |

### 12.4 Security & Compliance

| Control | Implementation |
|---------|---------------|
| **PII Redaction** | Field-level redaction in OTel Collector processor before any export |
| **Encryption** | TLS 1.3 in transit, AES-256 at rest |
| **Access Control** | RBAC via Grafana teams, K8s RBAC for infrastructure |
| **Audit Logging** | All access to observability data logged to immutable audit trail |
| **Data Residency** | Region-specific storage buckets, no cross-region replication |
| **Retention Enforcement** | Automated lifecycle policies, no manual deletion |
| **Secret Management** | All API keys, tokens in HashiCorp Vault, never in config files |

### 12.5 Glossary

| Term | Definition |
|------|-----------|
| **Agent** | An autonomous AI system that plans, executes, and optimizes marketing tasks |
| **Span** | A single operation within a trace (e.g., one LLM call) |
| **Trace** | A complete end-to-end execution path across multiple spans |
| **Mimir** | Prometheus-compatible long-term metrics storage (Grafana Labs) |
| **Tempo** | OpenTelemetry-native distributed tracing backend (Grafana Labs) |
| **Loki** | Label-based log aggregation system (Grafana Labs) |
| **OTel** | OpenTelemetry — vendor-neutral observability framework |
| **ROAS** | Return on Ad Spend — revenue generated per dollar spent on advertising |
| **CPA** | Cost Per Acquisition — cost to acquire one customer |
| **SLO** | Service Level Objective — target reliability metric |
| **SLA** | Service Level Agreement — contractual reliability commitment |

---

*End of document.*
