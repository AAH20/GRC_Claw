# AI-Powered Customer Segmentation Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Stack:** LangChain DeepAgents, Python 3.11+, OpenAI GPT-4o, Pinecone, PostgreSQL, Redis, FastAPI

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Data Collection Agent](#2-data-collection-agent-implementation)
3. [Analysis Agent](#3-analysis-agent-implementation)
4. [Segment Builder Agent](#4-segment-builder-agent-implementation)
5. [Marketing Strategist Agent](#5-marketing-strategist-agent-implementation)
6. [Reviewer Agent](#6-reviewer-agent-implementation)
7. [Performance Analytics Agent](#7-performance-analytics-agent-implementation)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The customer segmentation system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. Six specialized agents collaborate in a pipeline to transform raw customer data into actionable marketing segments with strategies and performance tracking.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (DeepAgents)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │   Data   │→ │ Analysis │→ │ Segment  │→ │  Marketing       │   │
│  │Collection│  │  Agent   │  │ Builder  │  │  Strategist      │   │
│  │  Agent   │  │          │  │  Agent   │  │     Agent        │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
│       ↑                                              │              │
│       │         ┌──────────┐  ┌──────────────────┐  │              │
│       │         │Reviewer  │← │  Performance     │←─┘              │
│       └─────────│  Agent   │  │  Analytics Agent │                 │
│                 └──────────┘  └──────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Agent Communication Protocol

All agents communicate via a shared **state store** (Redis + PostgreSQL) using a typed message envelope:

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid


class AgentRole(str, Enum):
    DATA_COLLECTOR = "data_collector"
    ANALYST = "analyst"
    SEGMENT_BUILDER = "segment_builder"
    STRATEGIST = "strategist"
    REVIEWER = "reviewer"
    ANALYTICS = "analytics"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass
class AgentMessage:
    """Standard inter-agent communication envelope."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: AgentRole = AgentRole.DATA_COLLECTOR
    recipient: Optional[AgentRole] = None  # None = broadcast
    task_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_message_id: Optional[str] = None  # For threading
```

### 1.3 Shared State Schema

```python
from pydantic import BaseModel, Field
from typing import Literal


class CustomerRecord(BaseModel):
    customer_id: str
    email: str | None = None
    age: int | None = None
    gender: str | None = None
    location: dict | None = None  # {country, city, region}
    signup_date: str | None = None
    total_orders: int = 0
    total_revenue: float = 0.0
    avg_order_value: float = 0.0
    last_order_date: str | None = None
    preferred_categories: list[str] = []
    engagement_score: float = 0.0  # 0-100
    churn_risk: float = 0.0  # 0-1
    lifetime_value: float = 0.0
    tags: list[str] = []
    custom_attributes: dict = {}


class SegmentDefinition(BaseModel):
    segment_id: str
    name: str
    description: str
    criteria: dict  # Structured query criteria
    estimated_size: int
    avg_ltv: float
    avg_engagement: float
    churn_risk_level: Literal["low", "medium", "high"]
    recommended_actions: list[str] = []
    created_by: AgentRole = AgentRole.SEGMENT_BUILDER
    version: int = 1
    status: Literal["draft", "approved", "active", "archived"] = "draft"


class MarketingStrategy(BaseModel):
    strategy_id: str
    segment_id: str
    objective: Literal["retention", "acquisition", "upsell", "reactivation", "loyalty"]
    channels: list[str]  # email, sms, push, social, direct_mail
    messaging: dict  # {headline, body, cta, tone}
    offer_details: dict | None = None
    budget_allocation: dict[str, float]  # channel -> percentage
    timeline: dict  # {start_date, end_date, phases}
    expected_roi: float
    created_by: AgentRole = AgentRole.STRATEGIST


class PipelineState(BaseModel):
    """Top-level pipeline state shared across all agents."""
    pipeline_id: str
    status: Literal["initialized", "collecting", "analyzing", "segmenting",
                     "strategizing", "reviewing", "completed", "failed"]
    raw_data: list[CustomerRecord] = []
    analysis_results: dict = {}
    segments: list[SegmentDefinition] = []
    strategies: list[MarketingStrategy] = []
    review_feedback: list[dict] = []
    analytics: dict = {}
    errors: list[dict] = []
    created_at: str = ""
    updated_at: str = ""
```

### 1.4 Orchestrator Implementation

```python
from langchain_deepagents import DeepAgent, Tool
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
import redis
import json


class SegmentationOrchestrator:
    """Central orchestrator that manages the agent pipeline."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.agents: dict[AgentRole, DeepAgent] = {}
        self._register_agents()

    def _register_agents(self):
        """Initialize all six agents with their tools and system prompts."""
        self.agents[AgentRole.DATA_COLLECTOR] = DataCollectorAgent(self.llm)
        self.agents[AgentRole.ANALYST] = AnalysisAgent(self.llm)
        self.agents[AgentRole.SEGMENT_BUILDER] = SegmentBuilderAgent(self.llm)
        self.agents[AgentRole.STRATEGIST] = MarketingStrategistAgent(self.llm)
        self.agents[AgentRole.REVIEWER] = ReviewerAgent(self.llm)
        self.agents[AgentRole.ANALYTICS] = PerformanceAnalyticsAgent(self.llm)

    async def run_pipeline(self, config: dict) -> PipelineState:
        """Execute the full segmentation pipeline."""
        state = PipelineState(
            pipeline_id=str(uuid.uuid4()),
            status="initialized",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )

        try:
            # Phase 1: Data Collection
            state.status = "collecting"
            state = await self._execute_phase(
                AgentRole.DATA_COLLECTOR, state, config
            )

            # Phase 2: Analysis
            state.status = "analyzing"
            state = await self._execute_phase(
                AgentRole.ANALYST, state, config
            )

            # Phase 3: Segment Building
            state.status = "segmenting"
            state = await self._execute_phase(
                AgentRole.SEGMENT_BUILDER, state, config
            )

            # Phase 4: Strategy Generation
            state.status = "strategizing"
            state = await self._execute_phase(
                AgentRole.STRATEGIST, state, config
            )

            # Phase 5: Review
            state.status = "reviewing"
            state = await self._execute_phase(
                AgentRole.REVIEWER, state, config
            )

            # Phase 6: Analytics Setup
            state.status = "completed"
            state = await self._execute_phase(
                AgentRole.ANALYTICS, state, config
            )

        except Exception as e:
            state.status = "failed"
            state.errors.append({
                "phase": state.status,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })

        # Persist final state
        self._persist_state(state)
        return state

    async def _execute_phase(
        self, role: AgentRole, state: PipelineState, config: dict
    ) -> PipelineState:
        """Execute a single pipeline phase with retry logic."""
        agent = self.agents[role]
        message = AgentMessage(
            sender=AgentRole.DATA_COLLECTOR,  # Orchestrator acts as collector
            recipient=role,
            task_id=state.pipeline_id,
            status=TaskStatus.IN_PROGRESS,
            payload={"state": state.model_dump(), "config": config},
        )

        # Store message for agent pickup
        self.redis.setex(
            f"agent_queue:{role.value}",
            3600,  # 1 hour TTL
            json.dumps(message.model_dump(), default=str),
        )

        # Execute agent (with timeout and retry)
        result = await self._run_agent_with_retry(agent, message, max_retries=3)

        # Merge result back into state
        if result and "state_update" in result:
            for key, value in result["state_update"].items():
                setattr(state, key, value)

        state.updated_at = datetime.utcnow().isoformat()
        return state

    async def _run_agent_with_retry(
        self, agent: DeepAgent, message: AgentMessage, max_retries: int = 3
    ) -> dict | None:
        """Run an agent with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                result = await agent.arun(
                    message.model_dump(),
                    config=RunnableConfig(
                        recursion_limit=25,
                        tags=["segmentation_pipeline"],
                    ),
                )
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait = 2 ** attempt
                await asyncio.sleep(wait)
        return None

    def _persist_state(self, state: PipelineState):
        """Persist pipeline state to Redis and PostgreSQL."""
        key = f"pipeline:{state.pipeline_id}"
        self.redis.setex(key, 86400 * 30, json.dumps(state.model_dump(), default=str))
        # Also persist to PostgreSQL for long-term storage
        # (implementation depends on your ORM choice)
```

---

## 2. Data Collection Agent Implementation

### 2.1 Purpose

The Data Collector Agent is responsible for gathering customer data from multiple sources (CRM, e-commerce platform, analytics, support tickets), normalizing it into a unified `CustomerRecord` schema, and enriching it with computed fields.

### 2.2 Tools

```python
from langchain_deepagents import Tool
from langchain_core.tools import tool
import httpx
import asyncio
from typing import Annotated


@tool
async def fetch_crm_data(
    crm_endpoint: Annotated[str, "CRM API endpoint"],
    api_key: Annotated[str, "API key for CRM"],
    batch_size: Annotated[int, "Number of records per batch"] = 500,
) -> dict:
    """Fetch customer data from CRM system (Salesforce, HubSpot, etc.)."""
    records = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        offset = 0
        while True:
            response = await client.get(
                f"{crm_endpoint}/contacts",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"limit": batch_size, "offset": offset},
            )
            response.raise_for_status()
            batch = response.json().get("records", [])
            if not batch:
                break
            records.extend(batch)
            offset += batch_size
    return {"source": "crm", "records": records, "count": len(records)}


@tool
async def fetch_ecommerce_data(
    shopify_store: Annotated[str, "Shopify store URL"],
    access_token: Annotated[str, "Shopify access token"],
) -> dict:
    """Fetch order and customer data from e-commerce platform."""
    headers = {"X-Shopify-Access-Token": access_token}
    results = {"customers": [], "orders": []}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch customers
        resp = await client.get(
            f"https://{shopify_store}/admin/api/2024-01/customers.json",
            headers=headers,
        )
        resp.raise_for_status()
        results["customers"] = resp.json().get("customers", [])

        # Fetch orders
        resp = await client.get(
            f"https://{shopify_store}/admin/api/2024-01/orders.json?status=any",
            headers=headers,
        )
        resp.raise_for_status()
        results["orders"] = resp.json().get("orders", [])

    return {"source": "ecommerce", **results}


@tool
async def fetch_analytics_data(
    ga4_property_id: Annotated[str, "Google Analytics 4 property ID"],
    credentials_path: Annotated[str, "Path to service account JSON"],
    start_date: Annotated[str, "Start date (YYYY-MM-DD)"],
    end_date: Annotated[str, "End date (YYYY-MM-DD)"],
) -> dict:
    """Fetch user behavior data from Google Analytics 4."""
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest, DateRange, Dimension, Metric,
    )

    client = BetaAnalyticsDataClient.from_service_account_json(credentials_path)
    request = RunReportRequest(
        property=f"properties/{ga4_property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[
            Dimension(name="userId"),
            Dimension(name="deviceCategory"),
            Dimension(name="sessionDefaultChannelGroup"),
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="engagementRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="conversions"),
            Metric(name="totalAdRevenue"),
        ],
    )
    response = client.run_report(request)
    return {
        "source": "ga4",
        "rows": [
            {
                "user_id": row.dimension_values[0].value,
                "device": row.dimension_values[1].value,
                "channel": row.dimension_values[2].value,
                "sessions": int(row.metric_values[0].value),
                "engagement_rate": float(row.metric_values[1].value),
                "avg_session_duration": float(row.metric_values[2].value),
                "conversions": int(row.metric_values[3].value),
                "ad_revenue": float(row.metric_values[4].value),
            }
            for row in response.rows
        ],
    }


@tool
async def fetch_support_tickets(
    zendesk_subdomain: Annotated[str, "Zendesk subdomain"],
    api_token: Annotated[str, "Zendesk API token"],
) -> dict:
    """Fetch support ticket data for sentiment and issue analysis."""
    import base64

    credentials = base64.b64encode(
        f"{{email}}/token:{api_token}".encode()
    ).decode()
    headers = {"Authorization": f"Basic {credentials}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"https://{zendesk_subdomain}.zendesk.com/api/v2/tickets.json?sort_by=updated_at",
            headers=headers,
        )
        resp.raise_for_status()
        tickets = resp.json().get("tickets", [])

    return {
        "source": "zendesk",
        "tickets": [
            {
                "id": t["id"],
                "customer_email": t.get("requester", {}).get("email"),
                "status": t["status"],
                "priority": t.get("priority", "normal"),
                "tags": t.get("tags", []),
                "created_at": t["created_at"],
                "satisfaction_rating": t.get("satisfaction_rating", {}).get("score"),
            }
            for t in tickets
        ],
    }
```

### 2.3 Agent Definition

```python
DATA_COLLECTOR_SYSTEM_PROMPT = """You are the Data Collection Agent for a customer segmentation system.

Your responsibilities:
1. Fetch customer data from all configured sources (CRM, e-commerce, analytics, support)
2. Normalize all data into the unified CustomerRecord schema
3. Enrich records with computed fields (LTV, engagement score, churn risk)
4. Deduplicate customers across sources using email as the primary key
5. Flag data quality issues (missing fields, outliers, inconsistencies)
6. Produce a clean, analysis-ready dataset

Guidelines:
- Always validate data types and ranges before storing
- Use fuzzy matching for deduplication (emails may have typos)
- Compute engagement_score as a weighted composite of: recency (30%), frequency (25%), 
  monetary (25%), support interactions (10%), and digital engagement (10%)
- Compute churn_risk using: days since last order, declining order frequency, 
  negative support sentiment, and reduced engagement
- Flag any customer with >3 data quality issues for manual review
- Never fabricate or impute missing critical fields (email, customer_id)

Output: A JSON object with 'customers' (list of CustomerRecord), 'quality_report' 
(dict with issues found), and 'collection_metadata' (sources, timestamps, counts).
"""


class DataCollectorAgent(DeepAgent):
    """Agent responsible for collecting and normalizing customer data."""

    def __init__(self, llm):
        tools = [
            Tool.from_function(fetch_crm_data),
            Tool.from_function(fetch_ecommerce_data),
            Tool.from_function(fetch_analytics_data),
            Tool.from_function(fetch_support_tickets),
            Tool.from_function(self._normalize_records),
            Tool.from_function(self._compute_derived_fields),
            Tool.from_function(self._deduplicate_customers),
            Tool.from_function(self._quality_check),
        ]
        super().__init__(
            name="DataCollector",
            llm=llm,
            tools= tools,
            system_prompt=DATA_COLLECTOR_SYSTEM_PROMPT,
        )

    @staticmethod
    async def _normalize_records(raw_records: list[dict]) -> list[dict]:
        """Normalize records from various sources into CustomerRecord schema."""
        normalized = []
        for record in raw_records:
            try:
                customer = CustomerRecord(
                    customer_id=str(record.get("id", record.get("customer_id", ""))),
                    email=record.get("email", "").lower().strip() or None,
                    age=_parse_age(record.get("age", record.get("birth_year"))),
                    gender=record.get("gender"),
                    location=_parse_location(record),
                    signup_date=record.get("created_at", record.get("signup_date")),
                    total_orders=int(record.get("orders_count", 0)),
                    total_revenue=float(record.get("total_spent", 0)),
                    avg_order_value=_safe_divide(
                        float(record.get("total_spent", 0)),
                        int(record.get("orders_count", 0)),
                    ),
                    last_order_date=record.get("last_order_at"),
                    preferred_categories=record.get("tags", []),
                )
                normalized.append(customer.model_dump())
            except (ValueError, TypeError) as e:
                # Log and skip malformed records
                continue
        return normalized

    @staticmethod
    async def _compute_derived_fields(customers: list[dict]) -> list[dict]:
        """Compute engagement_score, churn_risk, and lifetime_value."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        for c in customers:
            # Engagement score (0-100)
            recency_score = _recency_score(c.get("last_order_date"), now)
            frequency_score = min(c.get("total_orders", 0) * 5, 100)
            monetary_score = min(c.get("total_revenue", 0) / 100, 100)
            support_score = _support_score(c.get("support_tickets", []))
            digital_score = c.get("digital_engagement", 50)

            c["engagement_score"] = round(
                0.30 * recency_score
                + 0.25 * frequency_score
                + 0.25 * monetary_score
                + 0.10 * support_score
                + 0.10 * digital_score,
                2,
            )

            # Churn risk (0-1)
            c["churn_risk"] = round(_compute_churn_risk(c, now), 4)

            # Lifetime value (simple projection)
            c["lifetime_value"] = round(_compute_ltv(c), 2)

        return customers

    @staticmethod
    async def _deduplicate_customers(customers: list[dict]) -> list[dict]:
        """Deduplicate by email, merging records with complementary data."""
        seen: dict[str, dict] = {}
        for c in customers:
            email = c.get("email")
            if not email:
                # Generate synthetic ID for records without email
                c["customer_id"] = f"anon_{hash(str(c)) % 10**10}"
                seen[c["customer_id"]] = c
                continue

            if email in seen:
                # Merge: keep the record with more data, fill gaps
                existing = seen[email]
                merged = _merge_customer_records(existing, c)
                seen[email] = merged
            else:
                seen[email] = c

        return list(seen.values())

    @staticmethod
    async def _quality_check(customers: list[dict]) -> dict:
        """Run data quality checks and produce a report."""
        issues = []
        for c in customers:
            customer_issues = []
            if not c.get("email"):
                customer_issues.append("missing_email")
            if c.get("age") and (c["age"] < 13 or c["age"] > 120):
                customer_issues.append("invalid_age")
            if c.get("total_revenue", 0) < 0:
                customer_issues.append("negative_revenue")
            if c.get("total_orders", 0) > 0 and not c.get("last_order_date"):
                customer_issues.append("missing_last_order_date")
            if customer_issues:
                issues.append({
                    "customer_id": c.get("customer_id"),
                    "issues": customer_issues,
                })

        return {
            "total_records": len(customers),
            "records_with_issues": len(issues),
            "issue_rate": round(len(issues) / max(len(customers), 1), 4),
            "issues": issues,
            "recommendation": "review" if len(issues) > len(customers) * 0.05 else "proceed",
        }


# Helper functions
def _parse_age(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and value > 1900:  # birth year
        from datetime import datetime
        return datetime.now().year - value
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_location(record: dict) -> dict | None:
    parts = [
        record.get("city"),
        record.get("state", record.get("region")),
        record.get("country"),
    ]
    if any(parts):
        return {k: v for k, v in zip(["city", "region", "country"], parts) if v}
    return None


def _safe_divide(numerator: float, denominator: int) -> float:
    return round(numerator / denominator, 2) if denominator > 0 else 0.0


def _recency_score(last_order_date: str | None, now) -> float:
    if not last_order_date:
        return 0.0
    from datetime import datetime
    try:
        last = datetime.fromisoformat(last_order_date.replace("Z", "+00:00"))
        days_since = (now - last).days
        if days_since <= 30:
            return 100.0
        elif days_since <= 90:
            return 70.0
        elif days_since <= 180:
            return 40.0
        elif days_since <= 365:
            return 15.0
        return 0.0
    except (ValueError, TypeError):
        return 0.0


def _support_score(tickets: list) -> float:
    if not tickets:
        return 50.0  # Neutral
    # Higher score for positive/resolved, lower for unresolved negative
    score = 50.0
    for t in tickets:
        if t.get("status") == "solved" and t.get("satisfaction") == "good":
            score += 10
        elif t.get("status") == "open" and t.get("sentiment") == "negative":
            score -= 15
    return max(0, min(100, score))


def _compute_churn_risk(customer: dict, now) -> float:
    risk = 0.0
    # Recency factor
    last_order = customer.get("last_order_date")
    if last_order:
        from datetime import datetime
        try:
            last = datetime.fromisoformat(last_order.replace("Z", "+00:00"))
            days = (now - last).days
            if days > 365:
                risk += 0.4
            elif days > 180:
                risk += 0.2
            elif days > 90:
                risk += 0.1
        except (ValueError, TypeError):
            risk += 0.3
    else:
        risk += 0.5

    # Engagement factor
    engagement = customer.get("engagement_score", 50)
    if engagement < 20:
        risk += 0.3
    elif engagement < 40:
        risk += 0.15

    # Order frequency decline
    orders = customer.get("total_orders", 0)
    if orders > 5 and customer.get("recent_orders_90d", 0) == 0:
        risk += 0.2

    return min(1.0, risk)


def _compute_ltv(customer: dict) -> float:
    aov = customer.get("avg_order_value", 0)
    frequency = customer.get("total_orders", 0)
    # Simple LTV: AOV * expected future orders (capped)
    expected_future = max(0, 12 - frequency) if frequency < 12 else 3
    return aov * expected_future


def _merge_customer_records(a: dict, b: dict) -> dict:
    """Merge two customer records, preferring non-null values."""
    merged = {**a}
    for key, value in b.items():
        if value is not None and value != "" and value != 0:
            if key == "preferred_categories":
                merged[key] = list(set(merged.get(key, []) + value))
            elif key == "total_revenue":
                merged[key] = merged.get(key, 0) + value
            elif key == "total_orders":
                merged[key] = merged.get(key, 0) + value
            else:
                merged[key] = value
    return merged
```

---

## 3. Analysis Agent Implementation

### 3.1 Purpose

The Analysis Agent performs exploratory data analysis (EDA), statistical profiling, RFM (Recency, Frequency, Monetary) scoring, behavioral clustering, and correlation analysis to uncover patterns that will inform segmentation.

### 3.2 Tools

```python
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import pandas as pd


@tool
def compute_rfm_scores(
    customers: Annotated[list[dict], "List of customer records"],
) -> dict:
    """Compute RFM (Recency, Frequency, Monetary) scores for each customer."""
    df = pd.DataFrame(customers)

    # Recency: days since last purchase (lower is better)
    df["last_order_date"] = pd.to_datetime(df["last_order_date"], errors="coerce")
    reference_date = df["last_order_date"].max()
    df["recency_days"] = (reference_date - df["last_order_date"]).dt.days

    # Score each dimension 1-5 using quintiles
    df["R_score"] = pd.qcut(
        df["recency_days"].fillna(9999), q=5, labels=[5, 4, 3, 2, 1]
    ).astype(int)
    df["F_score"] = pd.qcut(
        df["total_orders"].fillna(0).rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    df["M_score"] = pd.qcut(
        df["total_revenue"].fillna(0).rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    # Combined RFM score
    df["RFM_score"] = (
        df["R_score"].astype(str)
        + df["F_score"].astype(str)
        + df["M_score"].astype(str)
    )

    # Segment mapping based on RFM
    def rfm_segment(row):
        r, f, m = row["R_score"], row["F_score"], row["M_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "champions"
        elif r >= 3 and f >= 3 and m >= 3:
            return "loyal_customers"
        elif r >= 4 and f <= 2:
            return "new_customers"
        elif r >= 3 and f >= 3 and m <= 2:
            return "potential_loyalists"
        elif r <= 2 and f >= 3:
            return "at_risk"
        elif r <= 2 and f <= 2 and m >= 3:
            return "cannot_lose"
        elif r <= 2 and f <= 2 and m <= 2:
            return "lost"
        else:
            return "needs_attention"

    df["rfm_segment"] = df.apply(rfm_segment, axis=1)

    return {
        "rfm_scores": df[["customer_id", "R_score", "F_score", "M_score", "RFM_score", "rfm_segment"]].to_dict("records"),
        "segment_distribution": df["rfm_segment"].value_counts().to_dict(),
        "statistics": {
            "avg_recency_days": float(df["recency_days"].mean()),
            "avg_frequency": float(df["total_orders"].mean()),
            "avg_monetary": float(df["total_revenue"].mean()),
        },
    }


@tool
def perform_behavioral_clustering(
    customers: Annotated[list[dict], "List of customer records"],
    n_clusters: Annotated[int, "Number of clusters (auto-determined if None)"] = None,
    features: Annotated[list[str], "Features to use for clustering"] = None,
) -> dict:
    """Perform K-means clustering on customer behavioral features."""
    if features is None:
        features = [
            "total_orders", "total_revenue", "avg_order_value",
            "engagement_score", "lifetime_value", "churn_risk",
        ]

    df = pd.DataFrame(customers)
    X = df[features].fillna(0).values

    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Auto-determine optimal clusters using silhouette score
    if n_clusters is None:
        best_score = -1
        best_k = 3
        for k in range(2, min(11, len(X) // 10)):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)
            score = silhouette_score(X_scaled, labels)
            if score > best_score:
                best_score = score
                best_k = k
        n_clusters = best_k

    # Final clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X_scaled)

    # PCA for visualization
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(X_scaled)
    df["pca_x"] = pca_result[:, 0]
    df["pca_y"] = pca_result[:, 1]

    # Cluster profiles
    cluster_profiles = {}
    for c in range(n_clusters):
        cluster_df = df[df["cluster"] == c]
        cluster_profiles[f"cluster_{c}"] = {
            "size": len(cluster_df),
            "percentage": round(len(cluster_df) / len(df) * 100, 2),
            "avg_revenue": round(float(cluster_df["total_revenue"].mean()), 2),
            "avg_orders": round(float(cluster_df["total_orders"].mean()), 2),
            "avg_engagement": round(float(cluster_df["engagement_score"].mean()), 2),
            "avg_churn_risk": round(float(cluster_df["churn_risk"].mean()), 4),
            "avg_ltv": round(float(cluster_df["lifetime_value"].mean()), 2),
            "top_categories": _top_categories(cluster_df),
        }

    return {
        "n_clusters": n_clusters,
        "silhouette_score": round(float(silhouette_score(X_scaled, df["cluster"])), 4),
        "cluster_profiles": cluster_profiles,
        "pca_explained_variance": pca.explained_variance_ratio_.tolist(),
        "customer_assignments": df[["customer_id", "cluster", "pca_x", "pca_y"]].to_dict("records"),
    }


@tool
def analyze_category_preferences(
    customers: Annotated[list[dict], "List of customer records"],
) -> dict:
    """Analyze product category preferences across the customer base."""
    from collections import Counter

    all_categories = Counter()
    category_revenue = {}
    category_customers = {}

    for c in customers:
        cats = c.get("preferred_categories", [])
        revenue = c.get("total_revenue", 0)
        for cat in cats:
            all_categories[cat] += 1
            category_revenue[cat] = category_revenue.get(cat, 0) + revenue
            category_customers.setdefault(cat, set()).add(c["customer_id"])

    total_customers = len(customers)
    category_analysis = {}
    for cat, count in all_categories.most_common(20):
        category_analysis[cat] = {
            "customer_count": count,
            "customer_percentage": round(count / total_customers * 100, 2),
            "total_revenue": round(category_revenue[cat], 2),
            "avg_revenue_per_customer": round(
                category_revenue[cat] / max(len(category_customers[cat]), 1), 2
            ),
        }

    # Cross-category affinity
    affinity = {}
    for c in customers:
        cats = c.get("preferred_categories", [])
        for i, cat_a in enumerate(cats):
            for cat_b in cats[i + 1:]:
                pair = tuple(sorted([cat_a, cat_b]))
                affinity[pair] = affinity.get(pair, 0) + 1

    top_affinities = sorted(affinity.items(), key=lambda x: x[1], reverse=True)[:15]

    return {
        "category_distribution": category_analysis,
        "top_category_affinities": [
            {"categories": list(pair), "co_occurrence": count}
            for pair, count in top_affinities
        ],
        "total_unique_categories": len(all_categories),
    }


@tool
def compute_correlation_matrix(
    customers: Annotated[list[dict], "List of customer records"],
) -> dict:
    """Compute correlation matrix for key customer metrics."""
    df = pd.DataFrame(customers)
    numeric_cols = [
        "age", "total_orders", "total_revenue", "avg_order_value",
        "engagement_score", "churn_risk", "lifetime_value",
    ]
    available_cols = [c for c in numeric_cols if c in df.columns]
    corr_matrix = df[available_cols].corr()

    # Find strongest correlations
    strong_correlations = []
    for i, col_a in enumerate(available_cols):
        for j, col_b in enumerate(available_cols):
            if i < j:
                corr_val = corr_matrix.loc[col_a, col_b]
                if abs(corr_val) > 0.5:
                    strong_correlations.append({
                        "feature_a": col_a,
                        "feature_b": col_b,
                        "correlation": round(float(corr_val), 4),
                        "strength": "strong" if abs(corr_val) > 0.7 else "moderate",
                    })

    return {
        "correlation_matrix": corr_matrix.to_dict(),
        "strong_correlations": sorted(
            strong_correlations, key=lambda x: abs(x["correlation"]), reverse=True
        ),
    }


@tool
def detect_anomalies(
    customers: Annotated[list[dict], "List of customer records"],
    contamination: Annotated[float, "Expected fraction of anomalies"] = 0.05,
) -> dict:
    """Detect anomalous customers using Isolation Forest."""
    from sklearn.ensemble import IsolationForest

    df = pd.DataFrame(customers)
    features = ["total_orders", "total_revenue", "avg_order_value", "engagement_score"]
    X = df[features].fillna(0).values

    iso_forest = IsolationForest(
        contamination=contamination, random_state=42
    )
    df["is_anomaly"] = iso_forest.fit_predict(X) == -1
    df["anomaly_score"] = iso_forest.score_samples(X)

    anomalies = df[df["is_anomaly"]].sort_values("anomaly_score")

    return {
        "total_anomalies": int(df["is_anomaly"].sum()),
        "anomaly_rate": round(float(df["is_anomaly"].mean()), 4),
        "anomalous_customers": anomalies[
            ["customer_id", "total_revenue", "total_orders", "engagement_score", "anomaly_score"]
        ].head(50).to_dict("records"),
    }


def _top_categories(cluster_df: pd.DataFrame, top_n: int = 5) -> list[dict]:
    """Get top categories for a cluster."""
    from collections import Counter

    cats = Counter()
    for _, row in cluster_df.iterrows():
        for cat in row.get("preferred_categories", []):
            cats[cat] += 1
    return [{"category": cat, "count": count} for cat, count in cats.most_common(top_n)]
```

### 3.3 Agent Definition

```python
ANALYST_SYSTEM_PROMPT = """You are the Analysis Agent for a customer segmentation system.

Your responsibilities:
1. Perform exploratory data analysis on the collected customer data
2. Compute RFM (Recency, Frequency, Monetary) scores for all customers
3. Run behavioral clustering to identify natural customer groupings
4. Analyze category preferences and cross-category affinities
5. Compute correlation matrices to identify key relationships
6. Detect anomalies and outliers that may need special handling
7. Produce a comprehensive analysis report with actionable insights

Guidelines:
- Always validate statistical assumptions before applying methods
- Use silhouette score to validate cluster quality; aim for > 0.3
- Consider both RFM segments AND behavioral clusters — they complement each other
- Flag any segment representing <2% of customers as "niche" (may need different treatment)
- Identify the top 3 most valuable segments by LTV
- Identify the top 3 most at-risk segments by churn probability
- Look for unexpected patterns that challenge assumptions

Output: A JSON object containing:
- rfm_analysis: RFM scores and segment distribution
- clustering_results: Cluster assignments and profiles
- category_analysis: Category preferences and affinities
- correlation_insights: Key metric relationships
- anomalies: Detected outliers
- executive_summary: 3-5 key findings in plain language
- recommendations: Suggested segment strategies
"""


class AnalysisAgent(DeepAgent):
    """Agent responsible for statistical analysis and pattern discovery."""

    def __init__(self, llm):
        tools = [
            Tool.from_function(compute_rfm_scores),
            Tool.from_function(perform_behavioral_clustering),
            Tool.from_function(analyze_category_preferences),
            Tool.from_function(compute_correlation_matrix),
            Tool.from_function(detect_anomalies),
        ]
        super().__init__(
            name="Analyst",
            llm=llm,
            tools= tools,
            system_prompt=ANALYST_SYSTEM_PROMPT,
        )
```

---

## 4. Segment Builder Agent Implementation

### 4.1 Purpose

The Segment Builder Agent translates analysis results into well-defined, actionable customer segments. It creates segment definitions with clear criteria, estimates segment sizes and value, and assigns customers to segments.

### 4.2 Tools

```python
@tool
def create_segment_definitions(
    rfm_analysis: Annotated[dict, "RFM analysis results"],
    clustering_results: Annotated[dict, "Clustering results"],
    category_analysis: Annotated[dict, "Category analysis results"],
    business_rules: Annotated[dict, "Business-specific segmentation rules"],
) -> dict:
    """Create formal segment definitions from analysis results."""
    segments = []

    # Map RFM segments to formal definitions
    rfm_mapping = {
        "champions": {
            "name": "Champions",
            "description": "Best customers: high value, frequent, recent, engaged",
            "objective": "retention",
            "priority": 1,
        },
        "loyal_customers": {
            "name": "Loyal Customers",
            "description": "Consistent purchasers with good engagement",
            "objective": "upsell",
            "priority": 2,
        },
        "potential_loyalists": {
            "name": "Potential Loyalists",
            "description": "Recent customers with moderate activity",
            "objective": "loyalty",
            "priority": 3,
        },
        "new_customers": {
            "name": "New Customers",
            "description": "First-time or very recent purchasers",
            "objective": "acquisition",
            "priority": 4,
        },
        "at_risk": {
            "name": "At Risk",
            "description": "Previously valuable customers showing decline",
            "objective": "reactivation",
            "priority": 1,
        },
        "cannot_lose": {
            "name": "Cannot Lose",
            "description": "High-value customers with declining engagement",
            "objective": "retention",
            "priority": 1,
        },
        "needs_attention": {
            "name": "Needs Attention",
            "description": "Average customers who could be nurtured",
            "objective": "loyalty",
            "priority": 5,
        },
        "lost": {
            "name": "Lost",
            "description": "Inactive customers with no recent purchases",
            "objective": "reactivation",
            "priority": 6,
        },
    }

    for rfm_segment, info in rfm_mapping.items():
        segment = SegmentDefinition(
            segment_id=f"seg_{rfm_segment}",
            name=info["name"],
            description=info["description"],
            criteria={
                "rfm_segment": rfm_segment,
                "min_r_score": _get_min_r_score(rfm_segment),
                "min_f_score": _get_min_f_score(rfm_segment),
                "min_m_score": _get_min_m_score(rfm_segment),
            },
            estimated_size=rfm_analysis.get("segment_distribution", {}).get(rfm_segment, 0),
            avg_ltv=0.0,  # Will be computed
            avg_engagement=0.0,  # Will be computed
            churn_risk_level=_get_churn_risk_level(rfm_segment),
            recommended_actions=_get_recommended_actions(info["objective"]),
        )
        segments.append(segment.model_dump())

    # Add behavioral clusters as micro-segments
    for cluster_id, profile in clustering_results.get("cluster_profiles", {}).items():
        segment = SegmentDefinition(
            segment_id=f"seg_cluster_{cluster_id}",
            name=f"Behavioral Cluster {cluster_id}",
            description=_describe_cluster(profile),
            criteria={
                "cluster_id": int(cluster_id.split("_")[1]),
                "min_revenue": profile["avg_revenue"] * 0.5,
                "max_revenue": profile["avg_revenue"] * 1.5,
            },
            estimated_size=profile["size"],
            avg_ltv=profile["avg_ltv"],
            avg_engagement=profile["avg_engagement"],
            churn_risk_level=_risk_from_score(profile["avg_churn_risk"]),
            recommended_actions=_actions_from_cluster(profile),
        )
        segments.append(segment.model_dump())

    return {"segments": segments, "total_segments": len(segments)}


@tool
def assign_customers_to_segments(
    customers: Annotated[list[dict], "List of customer records"],
    segment_definitions: Annotated[list[dict], "Segment definitions"],
) -> dict:
    """Assign each customer to one or more segments based on criteria."""
    assignments = {s["segment_id"]: [] for s in segment_definitions}
    customer_segment_map = {}

    for customer in customers:
        customer_id = customer["customer_id"]
        customer_segments = []

        for segment in segment_definitions:
            if _matches_segment(customer, segment):
                assignments[segment["segment_id"]].append(customer_id)
                customer_segments.append(segment["segment_id"])

        customer_segment_map[customer_id] = customer_segments

    # Compute segment statistics
    segment_stats = {}
    for seg_id, customer_ids in assignments.items():
        seg_customers = [c for c in customers if c["customer_id"] in customer_ids]
        if seg_customers:
            segment_stats[seg_id] = {
                "size": len(seg_customers),
                "avg_revenue": round(
                    sum(c.get("total_revenue", 0) for c in seg_customers) / len(seg_customers), 2
                ),
                "avg_engagement": round(
                    sum(c.get("engagement_score", 0) for c in seg_customers) / len(seg_customers), 2
                ),
                "avg_churn_risk": round(
                    sum(c.get("churn_risk", 0) for c in seg_customers) / len(seg_customers), 4
                ),
                "avg_ltv": round(
                    sum(c.get("lifetime_value", 0) for c in seg_customers) / len(seg_customers), 2
                ),
            }

    return {
        "assignments": assignments,
        "customer_segment_map": customer_segment_map,
        "segment_statistics": segment_stats,
        "unassigned_customers": [
            cid for cid, segs in customer_segment_map.items() if not segs
        ],
    }


@tool
def validate_segment_quality(
    segment_assignments: Annotated[dict, "Segment assignment results"],
    customers: Annotated[list[dict], "Customer records"],
) -> dict:
    """Validate segment quality using multiple metrics."""
    stats = segment_assignments.get("segment_statistics", {})
    total_customers = len(customers)

    quality_report = {}
    for seg_id, seg_stats in stats.items():
        size = seg_stats["size"]
        size_pct = size / total_customers if total_customers > 0 else 0

        # Size check: segments should be 2%-40% of total
        size_quality = "good" if 0.02 <= size_pct <= 0.40 else (
            "too_small" if size_pct < 0.02 else "too_large"
        )

        # Distinctiveness: compare segment avg to overall avg
        overall_avg_revenue = sum(c.get("total_revenue", 0) for c in customers) / max(total_customers, 1)
        revenue_lift = (
            seg_stats["avg_revenue"] / overall_avg_revenue if overall_avg_revenue > 0 else 1.0
        )

        quality_report[seg_id] = {
            "size": size,
            "size_percentage": round(size_pct * 100, 2),
            "size_quality": size_quality,
            "revenue_lift": round(revenue_lift, 2),
            "distinctiveness": "high" if revenue_lift > 1.5 or revenue_lift < 0.5 else "medium",
            "actionable": size_quality == "good" and (revenue_lift > 1.2 or revenue_lift < 0.8),
        }

    return {
        "segment_quality": quality_report,
        "overall_assessment": _assess_overall_quality(quality_report),
        "recommendations": _quality_recommendations(quality_report),
    }


# Helper functions
def _get_min_r_score(rfm_segment: str) -> int:
    mapping = {
        "champions": 4, "loyal_customers": 3, "potential_loyalists": 3,
        "new_customers": 4, "at_risk": 1, "cannot_lose": 1,
        "needs_attention": 2, "lost": 1,
    }
    return mapping.get(rfm_segment, 1)


def _get_min_f_score(rfm_segment: str) -> int:
    mapping = {
        "champions": 4, "loyal_customers": 3, "potential_loyalists": 3,
        "new_customers": 1, "at_risk": 3, "cannot_lose": 3,
        "needs_attention": 2, "lost": 1,
    }
    return mapping.get(rfm_segment, 1)


def _get_min_m_score(rfm_segment: str) -> int:
    mapping = {
        "champions": 4, "loyal_customers": 3, "potential_loyalists": 1,
        "new_customers": 1, "at_risk": 1, "cannot_lose": 3,
        "needs_attention": 2, "lost": 1,
    }
    return mapping.get(rfm_segment, 1)


def _get_churn_risk_level(rfm_segment: str) -> str:
    mapping = {
        "champions": "low", "loyal_customers": "low", "potential_loyalists": "low",
        "new_customers": "medium", "at_risk": "high", "cannot_lose": "high",
        "needs_attention": "medium", "lost": "high",
    }
    return mapping.get(rfm_segment, "medium")


def _get_recommended_actions(objective: str) -> list[str]:
    mapping = {
        "retention": ["loyalty_program", "vip_experiences", "early_access", "personalized_offers"],
        "upsell": ["product_recommendations", "bundle_offers", "premium_tier", "cross_sell"],
        "acquisition": ["welcome_series", "onboarding", "first_purchase_incentive", "education"],
        "reactivation": ["win_back_campaign", "special_discount", "feedback_request", "product_updates"],
        "loyalty": ["points_program", "tier_benefits", "referral_incentives", "community"],
    }
    return mapping.get(objective, ["personalized_email"])


def _describe_cluster(profile: dict) -> str:
    parts = [f"Cluster of {profile['size']} customers ({profile['percentage']}%)"]
    parts.append(f"avg revenue ${profile['avg_revenue']}")
    parts.append(f"avg engagement {profile['avg_engagement']}")
    if profile["avg_churn_risk"] > 0.5:
        parts.append("HIGH churn risk")
    return " — ".join(parts)


def _risk_from_score(score: float) -> str:
    if score > 0.6:
        return "high"
    elif score > 0.3:
        return "medium"
    return "low"


def _actions_from_cluster(profile: dict) -> list[str]:
    actions = []
    if profile["avg_churn_risk"] > 0.5:
        actions.extend(["retention_campaign", "feedback_survey"])
    if profile["avg_engagement"] < 40:
        actions.append("re_engagement_campaign")
    if profile["avg_revenue"] > 500:
        actions.append("vip_program")
    return actions or ["nurture_campaign"]


def _matches_segment(customer: dict, segment: dict) -> bool:
    criteria = segment.get("criteria", {})

    # RFM-based matching
    if "rfm_segment" in criteria:
        rfm = customer.get("rfm_segment", "")
        return rfm == criteria["rfm_segment"]

    # Cluster-based matching
    if "cluster_id" in criteria:
        return customer.get("cluster") == criteria["cluster_id"]

    # Revenue-based matching
    if "min_revenue" in criteria:
        if customer.get("total_revenue", 0) < criteria["min_revenue"]:
            return False
    if "max_revenue" in criteria:
        if customer.get("total_revenue", 0) > criteria["max_revenue"]:
            return False

    return True


def _assess_overall_quality(quality_report: dict) -> str:
    actionable = sum(1 for q in quality_report.values() if q.get("actionable"))
    total = len(quality_report)
    if total == 0:
        return "no_segments"
    ratio = actionable / total
    if ratio >= 0.7:
        return "excellent"
    elif ratio >= 0.5:
        return "good"
    elif ratio >= 0.3:
        return "needs_improvement"
    return "poor"


def _quality_recommendations(quality_report: dict) -> list[str]:
    recs = []
    small_segments = [s for s, q in quality_report.items() if q.get("size_quality") == "too_small"]
    if small_segments:
        recs.append(f"Consider merging {len(small_segments)} small segments")
    large_segments = [s for s, q in quality_report.items() if q.get("size_quality") == "too_large"]
    if large_segments:
        recs.append(f"Consider splitting {len(large_segments)} large segments")
    return recs
```

### 4.3 Agent Definition

```python
SEGMENT_BUILDER_SYSTEM_PROMPT = """You are the Segment Builder Agent for a customer segmentation system.

Your responsibilities:
1. Translate analysis results into formal, well-defined customer segments
2. Create segment definitions with clear, measurable criteria
3. Assign customers to segments based on the defined criteria
4. Validate segment quality (size, distinctiveness, actionability)
5. Ensure segments are mutually exclusive where possible, or define overlap rules
6. Produce segment profiles with key statistics

Guidelines:
- Every segment must have a clear business meaning and actionable objective
- Segment sizes should be between 2% and 40% of the total customer base
- Each segment should have measurable criteria that can be evaluated in SQL
- Prioritize segments by business value (LTV × size × actionability)
- Create both broad segments (for strategy) and micro-segments (for tactics)
- Document the rationale for each segment definition
- Flag any segment that cannot be effectively targeted with available channels

Output: A JSON object containing:
- segments: List of SegmentDefinition objects
- assignments: Customer-to-segment mapping
- quality_report: Segment quality validation results
- segment_profiles: Detailed profiles for each segment
- coverage_report: Percentage of customers assigned to at least one segment
"""


class SegmentBuilderAgent(DeepAgent):
    """Agent responsible for creating and validating customer segments."""

    def __init__(self, llm):
        tools = [
            Tool.from_function(create_segment_definitions),
            Tool.from_function(assign_customers_to_segments),
            Tool.from_function(validate_segment_quality),
        ]
        super().__init__(
            name="SegmentBuilder",
            llm=llm,
            tools= tools,
            system_prompt=SEGMENT_BUILDER_SYSTEM_PROMPT,
        )
```

---

## 5. Marketing Strategist Agent Implementation

### 5.1 Purpose

The Marketing Strategist Agent generates tailored marketing strategies for each segment, including channel selection, messaging, offers, budget allocation, and campaign timelines.

### 5.2 Tools

```python
@tool
def generate_segment_strategy(
    segment: Annotated[dict, "Segment definition"],
    segment_statistics: Annotated[dict, "Segment statistics"],
    business_context: Annotated[dict, "Business context (budget, goals, constraints)"],
    historical_campaigns: Annotated[list[dict], "Past campaign performance data"],
) -> dict:
    """Generate a comprehensive marketing strategy for a segment."""
    objective = segment.get("recommended_actions", ["retention"])[0]
    churn_risk = segment.get("churn_risk_level", "medium")
    avg_ltv = segment_statistics.get("avg_ltv", 0)
    avg_engagement = segment_statistics.get("avg_engagement", 50)

    # Channel selection based on segment characteristics
    channels = _select_channels(avg_engagement, churn_risk, objective)

    # Messaging strategy
    messaging = _craft_messaging(segment, objective, avg_ltv)

    # Offer design
    offer = _design_offer(segment, objective, avg_ltv, historical_campaigns)

    # Budget allocation
    budget = _allocate_budget(channels, avg_ltv, business_context)

    # Timeline
    timeline = _create_timeline(objective, channels)

    # Expected ROI
    expected_roi = _estimate_roi(segment, offer, channels, historical_campaigns)

    strategy = MarketingStrategy(
        strategy_id=f"strat_{segment['segment_id']}",
        segment_id=segment["segment_id"],
        objective=objective,
        channels=channels,
        messaging=messaging,
        offer_details=offer,
        budget_allocation=budget,
        timeline=timeline,
        expected_roi=expected_roi,
    )

    return strategy.model_dump()


@tool
def generate_campaign_sequences(
    strategy: Annotated[dict, "Marketing strategy"],
    segment_size: Annotated[int, "Number of customers in segment"],
) -> dict:
    """Generate a sequence of campaigns for the strategy."""
    objective = strategy["objective"]
    channels = strategy["channels"]

    sequences = []

    if objective == "retention":
        sequences = [
            {
                "phase": 1,
                "name": "Appreciation",
                "timing": "Week 1-2",
                "channel": "email",
                "message": "Thank you for being a valued customer",
                "cta": "Explore new arrivals",
            },
            {
                "phase": 2,
                "name": "Reward",
                "timing": "Week 3-4",
                "channel": "email" if "email" in channels else channels[0],
                "message": "Exclusive reward for you",
                "cta": "Claim your reward",
            },
            {
                "phase": 3,
                "name": "Engagement",
                "timing": "Week 5-8",
                "channel": channels[1] if len(channels) > 1 else channels[0],
                "message": "We picked these just for you",
                "cta": "Shop now",
            },
        ]
    elif objective == "reactivation":
        sequences = [
            {
                "phase": 1,
                "name": "We Miss You",
                "timing": "Week 1",
                "channel": "email",
                "message": "It's been a while! Here's what's new",
                "cta": "See what's new",
            },
            {
                "phase": 2,
                "name": "Incentive",
                "timing": "Week 2-3",
                "channel": "email",
                "message": "Come back and save 20%",
                "cta": "Shop with discount",
            },
            {
                "phase": 3,
                "name": "Last Chance",
                "timing": "Week 4",
                "channel": "sms" if "sms" in channels else "email",
                "message": "Your 20% discount expires soon",
                "cta": "Use before it expires",
            },
        ]
    elif objective == "upsell":
        sequences = [
            {
                "phase": 1,
                "name": "Recommendation",
                "timing": "Week 1-2",
                "channel": "email",
                "message": "Based on your purchases, you'll love these",
                "cta": "View recommendations",
            },
            {
                "phase": 2,
                "name": "Social Proof",
                "timing": "Week 3-4",
                "channel": "push" if "push" in channels else "email",
                "message": "Customers like you also bought...",
                "cta": "Complete your collection",
            },
            {
                "phase": 3,
                "name": "Bundle Offer",
                "timing": "Week 5-6",
                "channel": "email",
                "message": "Save 15% when you bundle",
                "cta": "Build your bundle",
            },
        ]
    elif objective == "acquisition":
        sequences = [
            {
                "phase": 1,
                "name": "Welcome",
                "timing": "Day 1",
                "channel": "email",
                "message": "Welcome! Here's 10% off your first order",
                "cta": "Start shopping",
            },
            {
                "phase": 2,
                "name": "Education",
                "timing": "Day 3-5",
                "channel": "email",
                "message": "Discover our most loved products",
                "cta": "Explore bestsellers",
            },
            {
                "phase": 3,
                "name": "Incentive",
                "timing": "Day 7-14",
                "channel": "email",
                "message": "Your 10% discount expires soon",
                "cta": "Shop now",
            },
        ]
    else:  # loyalty
        sequences = [
            {
                "phase": 1,
                "name": "Recognition",
                "timing": "Week 1",
                "channel": "email",
                "message": "You're in our loyalty program!",
                "cta": "View your benefits",
            },
            {
                "phase": 2,
                "name": "Points Boost",
                "timing": "Week 2-4",
                "channel": "push" if "push" in channels else "email",
                "message": "Earn 2x points this week",
                "cta": "Shop and earn",
            },
        ]

    return {
        "strategy_id": strategy["strategy_id"],
        "sequences": sequences,
        "total_phases": len(sequences),
        "estimated_duration_weeks": len(sequences) * 2,
    }


@tool
def optimize_budget_allocation(
    strategies: Annotated[list[dict], "All segment strategies"],
    total_budget: Annotated[float, "Total marketing budget"],
    constraints: Annotated[dict, "Budget constraints"],
) -> dict:
    """Optimize budget allocation across segments using LTV weighting."""
    # Weight by segment value (LTV × size)
    weights = {}
    total_weight = 0
    for s in strategies:
        seg_value = s.get("expected_roi", 1.0)
        weight = max(seg_value, 0.1)
        weights[s["segment_id"]] = weight
        total_weight += weight

    # Allocate proportionally
    allocation = {}
    remaining_budget = total_budget

    for seg_id, weight in weights.items():
        base_allocation = (weight / total_weight) * total_budget
        # Apply constraints
        min_budget = constraints.get("min_per_segment", 0)
        max_budget = constraints.get("max_per_segment", total_budget * 0.5)
        allocated = max(min_budget, min(base_allocation, max_budget))
        allocation[seg_id] = round(allocated, 2)
        remaining_budget -= allocated

    # Distribute remaining budget to highest-ROI segments
    if remaining_budget > 0:
        sorted_segments = sorted(
            strategies, key=lambda s: s.get("expected_roi", 0), reverse=True
        )
        for s in sorted_segments:
            if remaining_budget <= 0:
                break
            extra = min(remaining_budget, allocation[s["segment_id"]] * 0.2)
            allocation[s["segment_id"]] += extra
            remaining_budget -= extra

    return {
        "total_budget": total_budget,
        "allocation": allocation,
        "unallocated": round(remaining_budget, 2),
        "allocation_percentage": {
            k: round(v / total_budget * 100, 2) for k, v in allocation.items()
        },
    }


# Helper functions
def _select_channels(engagement: float, churn_risk: str, objective: str) -> list[str]:
    channels = ["email"]  # Always include email

    if engagement > 60:
        channels.extend(["push", "sms"])
    elif engagement > 30:
        channels.append("push")

    if churn_risk == "high":
        channels.append("direct_mail")

    if objective in ("acquisition", "upsell"):
        channels.append("social")

    return list(dict.fromkeys(channels))  # Deduplicate preserving order


def _craft_messaging(segment: dict, objective: str, avg_ltv: float) -> dict:
    name = segment.get("name", "Customer")

    messaging_templates = {
        "retention": {
            "headline": f"{name}s like you deserve the best",
            "body": "As one of our most valued customers, you get exclusive access to new products, special offers, and VIP treatment.",
            "cta": "Explore Your Benefits",
            "tone": "appreciative",
        },
        "upsell": {
            "headline": "Complete your collection",
            "body": "Based on your purchase history, we think you'll love these hand-picked recommendations.",
            "cta": "Shop Recommendations",
            "tone": "helpful",
        },
        "reactivation": {
            "headline": "We miss you! Here's 20% off",
            "body": "It's been a while since your last visit. Come back and see what's new — we've saved a special discount just for you.",
            "cta": "Claim Your Discount",
            "tone": "warm",
        },
        "acquisition": {
            "headline": "Welcome! Here's 10% off",
            "body": "Thanks for joining us! Use this discount on your first order and discover why customers love us.",
            "cta": "Start Shopping",
            "tone": "welcoming",
        },
        "loyalty": {
            "headline": "You're a VIP now",
            "body": "Welcome to our loyalty program! Earn points on every purchase and unlock exclusive rewards.",
            "cta": "View Your Rewards",
            "tone": "exciting",
        },
    }

    return messaging_templates.get(objective, messaging_templates["retention"])


def _design_offer(segment: dict, objective: str, avg_ltv: float, historical: list) -> dict:
    base_discount = 0.10  # 10% base

    if objective == "reactivation":
        base_discount = 0.20
    elif objective == "retention" and avg_ltv > 500:
        base_discount = 0.15
    elif objective == "upsell":
        base_discount = 0.05  # Smaller discount, focus on bundles

    # Check historical performance
    similar_campaigns = [
        c for c in historical
        if c.get("objective") == objective and c.get("discount", 0) > 0
    ]
    if similar_campaigns:
        best = max(similar_campaigns, key=lambda c: c.get("roi", 0))
        base_discount = best.get("discount", base_discount)

    return {
        "type": "percentage_discount",
        "value": base_discount,
        "code": f"{objective.upper()}_{int(base_discount * 100)}",
        "minimum_order": 50 if avg_ltv > 200 else 0,
        "expiry_days": 14 if objective == "reactivation" else 30,
        "stackable": False,
    }


def _allocate_budget(channels: list[str], avg_ltv: float, context: dict) -> dict:
    # Default channel weights
    weights = {
        "email": 0.30,
        "push": 0.15,
        "sms": 0.15,
        "social": 0.20,
        "direct_mail": 0.20,
    }

    # Adjust for high-value segments
    if avg_ltv > 500:
        weights["direct_mail"] = 0.30
        weights["email"] = 0.25

    # Normalize for available channels
    total_weight = sum(weights.get(c, 0.1) for c in channels)
    return {
        c: round(weights.get(c, 0.1) / total_weight, 4)
        for c in channels
    }


def _create_timeline(objective: str, channels: list[str]) -> dict:
    durations = {
        "retention": 8,
        "upsell": 6,
        "reactivation": 4,
        "acquisition": 2,
        "loyalty": 8,
    }
    weeks = durations.get(objective, 4)

    return {
        "start_date": "T+0",
        "end_date": f"T+{weeks} weeks",
        "phases": [
            {"phase": 1, "weeks": "1-2", "focus": "awareness"},
            {"phase": 2, "weeks": f"{min(3, weeks)}-{min(4, weeks)}", "focus": "engagement"},
            {"phase": 3, "weeks": f"{min(5, weeks)}-{weeks}", "focus": "conversion"},
        ],
    }


def _estimate_roi(segment: dict, offer: dict, channels: list[str], historical: list) -> float:
    # Simple ROI estimation
    base_roi = 3.0  # 3:1 baseline

    # Adjust for channel mix
    if "email" in channels:
        base_roi *= 1.2
    if "direct_mail" in channels:
        base_roi *= 0.9  # Lower ROI but higher value

    # Adjust for offer depth
    discount = offer.get("value", 0.1)
    base_roi *= (1 - discount * 2)  # Deeper discount = lower ROI

    # Check historical
    similar = [c for c in historical if c.get("segment_id") == segment.get("segment_id")]
    if similar:
        avg_hist_roi = sum(c.get("roi", 0) for c in similar) / len(similar)
        base_roi = (base_roi + avg_hist_roi) / 2

    return round(base_roi, 2)
```

### 5.3 Agent Definition

```python
STRATEGIST_SYSTEM_PROMPT = """You are the Marketing Strategist Agent for a customer segmentation system.

Your responsibilities:
1. Generate tailored marketing strategies for each customer segment
2. Select optimal channels based on segment characteristics and engagement
3. Craft compelling messaging with appropriate tone and offers
4. Design campaign sequences with multiple touchpoints
5. Allocate budget across segments to maximize overall ROI
6. Define success metrics and KPIs for each strategy

Guidelines:
- Match channel selection to segment engagement level (high engagement = more channels)
- For high churn-risk segments, prioritize reactivation over acquisition spend
- For high-LTV segments, invest in retention (cheaper than acquisition)
- Always include email as a baseline channel; add others based on data
- Messaging should be specific to the segment's needs and value proposition
- Offers should be attractive but protect margin (max 25% discount)
- Consider the customer lifecycle stage when designing sequences
- Set realistic ROI expectations based on historical performance
- Every strategy must have measurable success criteria

Output: A JSON object containing:
- strategies: List of MarketingStrategy objects (one per segment)
- campaign_sequences: Multi-touch campaign sequences
- budget_allocation: Optimized budget distribution
- kpi_framework: Success metrics for each strategy
- risk_assessment: Potential risks and mitigation plans
"""


class MarketingStrategistAgent(DeepAgent):
    """Agent responsible for generating marketing strategies per segment."""

    def __init__(self, llm):
        tools = [
            Tool.from_function(generate_segment_strategy),
            Tool.from_function(generate_campaign_sequences),
            Tool.from_function(optimize_budget_allocation),
        ]
        super().__init__(
            name="Strategist",
            llm=llm,
            tools= tools,
            system_prompt=STRATEGIST_SYSTEM_PROMPT,
        )
```

---

## 6. Reviewer Agent Implementation

### 6.1 Purpose

The Reviewer Agent acts as a quality gate, validating all outputs from previous agents for correctness, completeness, business alignment, and ethical compliance. It can request rework from any agent.

### 6.2 Tools

```python
@tool
def review_data_quality(
    quality_report: Annotated[dict, "Data quality report from Data Collector"],
    sample_records: Annotated[list[dict], "Sample of collected records"],
) -> dict:
    """Review data collection output for completeness and correctness."""
    issues = []
    warnings = []

    # Check completeness
    if quality_report.get("issue_rate", 0) > 0.10:
        issues.append(f"High issue rate: {quality_report['issue_rate']:.1%} of records have problems")
    elif quality_report.get("issue_rate", 0) > 0.05:
        warnings.append(f"Moderate issue rate: {quality_report['issue_rate']:.1%}")

    # Check for required fields
    required_fields = ["customer_id", "email", "total_revenue"]
    for field in required_fields:
        missing = sum(1 for r in sample_records if not r.get(field))
        if missing > len(sample_records) * 0.05:
            issues.append(f"Field '{field}' missing in {missing}/{len(sample_records)} records")

    # Check for PII handling
    pii_fields = ["email", "phone", "address"]
    for field in pii_fields:
        if any(field in r for r in sample_records):
            warnings.append(f"PII field '{field}' present — ensure encryption at rest")

    return {
        "approved": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "recommendation": "approve" if not issues else "rework_required",
    }


@tool
def review_analysis_validity(
    rfm_analysis: Annotated[dict, "RFM analysis results"],
    clustering_results: Annotated[dict, "Clustering results"],
    correlation_insights: Annotated[dict, "Correlation analysis"],
) -> dict:
    """Review statistical analysis for validity and reliability."""
    issues = []
    warnings = []

    # Check cluster quality
    silhouette = clustering_results.get("silhouette_score", 0)
    if silhouette < 0.2:
        issues.append(f"Poor cluster quality (silhouette={silhouette:.3f}). Consider different features or method.")
    elif silhouette < 0.3:
        warnings.append(f"Marginal cluster quality (silhouette={silhouette:.3f})")

    # Check segment sizes
    distribution = rfm_analysis.get("segment_distribution", {})
    total = sum(distribution.values())
    for segment, count in distribution.items():
        pct = count / total if total > 0 else 0
        if pct < 0.02:
            warnings.append(f"Segment '{segment}' is very small ({pct:.1%})")
        if pct > 0.50:
            warnings.append(f"Segment '{segment}' is very large ({pct:.1%}) — consider splitting")

    # Check for logical consistency
    stats = rfm_analysis.get("statistics", {})
    if stats.get("avg_recency_days", 0) > 365:
        warnings.append("Average recency > 365 days — data may be stale")

    return {
        "approved": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "recommendation": "approve" if not issues else "rework_required",
    }


@tool
def review_segment_definitions(
    segments: Annotated[list[dict], "Segment definitions"],
    assignments: Annotated[dict, "Customer assignments"],
    quality_report: Annotated[dict, "Segment quality report"],
) -> dict:
    """Review segment definitions for business validity and actionability."""
    issues = []
    warnings = []

    # Check segment count
    if len(segments) < 3:
        issues.append(f"Too few segments ({len(segments)}). Minimum 3 for meaningful differentiation.")
    if len(segments) > 15:
        warnings.append(f"Many segments ({len(segments)}). Consider consolidating for manageability.")

    # Check coverage
    unassigned = assignments.get("unassigned_customers", [])
    total = sum(len(v) for v in assignments.get("assignments", {}).values())
    unassigned_rate = len(unassigned) / max(total, 1)
    if unassigned_rate > 0.10:
        issues.append(f"High unassigned rate: {unassigned_rate:.1%} of customers not in any segment")

    # Check actionability
    for segment in segments:
        if not segment.get("recommended_actions"):
            issues.append(f"Segment '{segment['name']}' has no recommended actions")
        if not segment.get("criteria"):
            issues.append(f"Segment '{segment['name']}' has no defined criteria")

    # Check for overlap
    segment_sizes = {
        sid: len(cids) for sid, cids in assignments.get("assignments", {}).items()
    }
    total_assigned = sum(segment_sizes.values())
    if total_assigned > total * 1.5:
        warnings.append("Significant segment overlap detected — customers in multiple segments")

    return {
        "approved": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "recommendation": "approve" if not issues else "rework_required",
    }


@tool
def review_strategies(
    strategies: Annotated[list[dict], "Marketing strategies"],
    budget_allocation: Annotated[dict, "Budget allocation"],
    business_goals: Annotated[dict, "Business goals and constraints"],
) -> dict:
    """Review marketing strategies for feasibility and alignment."""
    issues = []
    warnings = []

    # Check budget
    total_allocated = sum(budget_allocation.get("allocation", {}).values())
    total_budget = budget_allocation.get("total_budget", 0)
    if total_allocated > total_budget * 1.01:  # 1% tolerance
        issues.append(f"Over budget: allocated ${total_allocated:.2f} vs budget ${total_budget:.2f}")

    # Check strategy coverage
    for strategy in strategies:
        if not strategy.get("channels"):
            issues.append(f"Strategy '{strategy['strategy_id']}' has no channels")
        if not strategy.get("messaging"):
            issues.append(f"Strategy '{strategy['strategy_id']}' has no messaging")
        if strategy.get("expected_roi", 0) < 1.0:
            warnings.append(
                f"Strategy '{strategy['strategy_id']}' has low expected ROI: {strategy['expected_roi']}"
            )

    # Check for ethical concerns
    for strategy in strategies:
        segment_id = strategy.get("segment_id", "")
        if "lost" in segment_id and strategy.get("channels", []) == ["email"]:
            warnings.append(
                f"Lost segment '{segment_id}' only uses email — consider multi-channel reactivation"
            )

    return {
        "approved": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "recommendation": "approve" if not issues else "rework_required",
    }


@tool
def review_ethical_compliance(
    segments: Annotated[list[dict], "Segment definitions"],
    strategies: Annotated[list[dict], "Marketing strategies"],
    data_sources: Annotated[list[str], "List of data sources used"],
) -> dict:
    """Review for ethical compliance and fairness."""
    issues = []
    warnings = []

    # Check for discriminatory segmenting
    sensitive_attributes = ["gender", "age", "race", "religion", "ethnicity"]
    for segment in segments:
        criteria = segment.get("criteria", {})
        for attr in sensitive_attributes:
            if attr in criteria:
                issues.append(
                    f"Segment '{segment['name']}' uses sensitive attribute '{attr}' in criteria — "
                    "may violate fairness regulations"
                )

    # Check for predatory targeting
    for strategy in strategies:
        if strategy.get("objective") == "reactivation":
            offer = strategy.get("offer_details", {})
            if offer.get("value", 0) > 0.30:
                warnings.append(
                    f"Strategy '{strategy['strategy_id']}' offers {offer['value']:.0%} discount — "
                    "ensure this doesn't create unsustainable discount expectations"
                )

    # Check data source consent
    if "third_party" in data_sources:
        warnings.append("Third-party data source used — verify consent and GDPR/CCPA compliance")

    # Check for vulnerable population targeting
    for segment in segments:
        if segment.get("churn_risk_level") == "high" and "vulnerable" in segment.get("tags", []):
            issues.append(
                f"Segment '{segment['name']}' targets vulnerable population — "
                "requires legal review"
            )

    return {
        "approved": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "recommendation": "approve" if not issues else "rework_required",
    }
```

### 6.3 Agent Definition

```python
REVIEWER_SYSTEM_PROMPT = """You are the Reviewer Agent for a customer segmentation system.

Your responsibilities:
1. Review all outputs from previous agents for quality and correctness
2. Validate data completeness, accuracy, and consistency
3. Ensure statistical methods are appropriate and correctly applied
4. Verify segments are well-defined, actionable, and non-discriminatory
5. Check marketing strategies are feasible, ethical, and aligned with business goals
6. Ensure compliance with data privacy regulations (GDPR, CCPA)
7. Request rework when outputs don't meet quality standards
8. Provide specific, actionable feedback for improvements

Review criteria:
- Data: completeness (>95% required fields), accuracy, no duplicates, PII protected
- Analysis: appropriate methods, valid assumptions, good cluster quality (silhouette > 0.3)
- Segments: clear criteria, reasonable sizes (2%-40%), actionable, non-overlapping preferred
- Strategies: feasible channels, realistic ROI, appropriate offers, ethical targeting
- Compliance: no discriminatory criteria, consent verified, vulnerable populations protected

Output: A JSON object containing:
- reviews: One review per agent output (data, analysis, segments, strategies, ethics)
- overall_approved: Boolean indicating if all reviews passed
- required_rework: List of specific items that need rework
- improvement_suggestions: Optional enhancements
- approval_chain: Sign-off trail for audit purposes
"""


class ReviewerAgent(DeepAgent):
    """Agent responsible for quality assurance and compliance review."""

    def __init__(self, llm):
        tools = [
            Tool.from_function(review_data_quality),
            Tool.from_function(review_analysis_validity),
            Tool.from_function(review_segment_definitions),
            Tool.from_function(review_strategies),
            Tool.from_function(review_ethical_compliance),
        ]
        super().__init__(
            name="Reviewer",
            llm=llm,
            tools= tools,
            system_prompt=REVIEWER_SYSTEM_PROMPT,
        )
```

---

## 7. Performance Analytics Agent Implementation

### 7.1 Purpose

The Performance Analytics Agent sets up tracking, defines KPIs, creates dashboards, and establishes a feedback loop for continuous segment performance monitoring and optimization.

### 7.2 Tools

```python
@tool
def define_kpi_framework(
    strategies: Annotated[list[dict], "Marketing strategies"],
    segments: Annotated[list[dict], "Segment definitions"],
    business_goals: Annotated[dict, "Business goals"],
) -> dict:
    """Define KPIs and success metrics for each segment and strategy."""
    kpi_framework = {}

    for strategy in strategies:
        seg_id = strategy["segment_id"]
        objective = strategy["objective"]

        base_kpis = {
            "reach": {"metric": "customers_reached", "target": "segment_size * 0.8"},
            "engagement": {"metric": "email_open_rate", "target": "0.25"},
            "conversion": {"metric": "conversion_rate", "target": _conversion_target(objective)},
            "revenue": {"metric": "attributed_revenue", "target": "segment_avg_ltv * 0.1"},
            "roi": {"metric": "roas", "target": str(strategy.get("expected_roi", 3.0))},
        }

        # Add objective-specific KPIs
        if objective == "retention":
            base_kpis["retention_rate"] = {"metric": "90_day_retention", "target": "0.85"}
            base_kpis["churn_reduction"] = {"metric": "churn_rate_change", "target": "-0.10"}
        elif objective == "reactivation":
            base_kpis["reactivation_rate"] = {"metric": "returning_customers", "target": "0.15"}
            base_kpis["time_to_convert"] = {"metric": "days_to_first_purchase", "target": "14"}
        elif objective == "upsell":
            base_kpis["upsell_rate"] = {"metric": "additional_purchase_rate", "target": "0.20"}
            base_kpis["aov_increase"] = {"metric": "avg_order_value_change", "target": "+0.15"}
        elif objective == "acquisition":
            base_kpis["activation_rate"] = {"metric": "first_purchase_rate", "target": "0.30"}
            base_kpis["cac"] = {"metric": "customer_acquisition_cost", "target": "< $50"}
        elif objective == "loyalty":
            base_kpis["program_adoption"] = {"metric": "loyalty_signup_rate", "target": "0.40"}
            base_kpis["repeat_rate"] = {"metric": "repeat_purchase_rate", "target": "0.50"}

        kpi_framework[seg_id] = {
            "strategy_id": strategy["strategy_id"],
            "objective": objective,
            "kpis": base_kpis,
            "measurement_frequency": "weekly",
            "reporting_cadence": "bi_weekly",
        }

    return {
        "kpi_framework": kpi_framework,
        "global_kpis": {
            "total_revenue_impact": {"target": "+15% QoQ"},
            "customer_satisfaction": {"target": "NPS > 50"},
            "segment_coverage": {"target": "> 90% of customer base"},
            "data_freshness": {"target": "segments updated weekly"},
        },
    }


@tool
def setup_tracking_infrastructure(
    kpi_framework: Annotated[dict, "KPI framework"],
    data_warehouse: Annotated[str, "Data warehouse connection"],
    dashboard_tool: Annotated[str, "Dashboard tool (e.g., Metabase, Looker)"],
) -> dict:
    """Set up tracking tables, ETL jobs, and dashboards."""
    tracking_setup = {
        "warehouse_tables": _generate_tracking_tables(kpi_framework),
        "etl_jobs": _generate_etl_jobs(kpi_framework),
        "dashboards": _generate_dashboard_configs(kpi_framework, dashboard_tool),
        "alerts": _generate_alert_configs(kpi_framework),
    }
    return tracking_setup


@tool
def create_feedback_loop(
    kpi_framework: Annotated[dict, "KPI framework"],
    segment_definitions: Annotated[list[dict], "Segment definitions"],
) -> dict:
    """Create a feedback loop for continuous segment optimization."""
    return {
        "feedback_schedule": {
            "weekly": "Review campaign performance vs KPIs",
            "bi_weekly": "Segment migration analysis",
            "monthly": "Segment definition review and refinement",
            "quarterly": "Full pipeline re-run with fresh data",
        },
        "optimization_triggers": [
            {
                "condition": "segment_size_change > 20%",
                "action": "Trigger segment re-evaluation",
            },
            {
                "condition": "kpi_missed_for_2_consecutive_periods",
                "action": "Trigger strategy revision",
            },
            {
                "condition": "churn_rate_increase > 5%",
                "action": "Trigger retention campaign",
            },
            {
                "condition": "new_product_launch",
                "action": "Trigger segment-specific product recommendations",
            },
        ],
        "learning_mechanisms": {
            "a_b_testing": "Test messaging variants within segments",
            "control_groups": "Maintain 5% control group per segment for attribution",
            "incrementality_measurement": "Measure true incremental impact of campaigns",
            "segment_migration_tracking": "Track customers moving between segments over time",
        },
    }


@tool
def generate_performance_report(
    campaign_results: Annotated[dict, "Campaign performance data"],
    kpi_framework: Annotated[dict, "KPI framework"],
    period: Annotated[str, "Reporting period (e.g., '2026-Q3')"],
) -> dict:
    """Generate a comprehensive performance report."""
    report = {
        "period": period,
        "executive_summary": {},
        "segment_performance": {},
        "strategy_effectiveness": {},
        "recommendations": [],
    }

    for seg_id, kpis in kpi_framework.items():
        seg_results = campaign_results.get(seg_id, {})
        performance = {}

        for kpi_name, kpi_config in kpis.get("kpis", {}).items():
            actual = seg_results.get(kpi_name, 0)
            target = kpi_config.get("target", 0)
            performance[kpi_name] = {
                "actual": actual,
                "target": target,
                "status": _kpi_status(actual, target),
                "variance": _compute_variance(actual, target),
            }

        report["segment_performance"][seg_id] = performance

    # Overall assessment
    all_kpis = [
        kpi_status
        for seg_perf in report["segment_performance"].values()
        for kpi_status in [k["status"] for k in seg_perf.values()]
    ]
    report["executive_summary"] = {
        "total_segments": len(kpi_framework),
        "kpis_on_track": all_kpis.count("on_track"),
        "kpis_at_risk": all_kpis.count("at_risk"),
        "kpis_missed": all_kpis.count("missed"),
        "overall_health": _overall_health(all_kpis),
    }

    return report


# Helper functions
def _conversion_target(objective: str) -> str:
    targets = {
        "retention": "0.80", "upsell": "0.20", "reactivation": "0.15",
        "acquisition": "0.30", "loyalty": "0.50",
    }
    return targets.get(objective, "0.20")


def _generate_tracking_tables(kpi_framework: dict) -> list[dict]:
    return [
        {
            "table_name": "segment_daily_metrics",
            "columns": [
                {"name": "date", "type": "DATE"},
                {"name": "segment_id", "type": "VARCHAR(50)"},
                {"name": "customers_reached", "type": "INT"},
                {"name": "engagements", "type": "INT"},
                {"name": "conversions", "type": "INT"},
                {"name": "revenue", "type": "DECIMAL(12,2)"},
                {"name": "campaign_cost", "type": "DECIMAL(12,2)"},
            ],
            "partition_by": "date",
        },
        {
            "table_name": "segment_migration_log",
            "columns": [
                {"name": "customer_id", "type": "VARCHAR(50)"},
                {"name": "from_segment", "type": "VARCHAR(50)"},
                {"name": "to_segment", "type": "VARCHAR(50)"},
                {"name": "migration_date", "type": "TIMESTAMP"},
                {"name": "trigger_event", "type": "VARCHAR(100)"},
            ],
        },
        {
            "table_name": "campaign_attribution",
            "columns": [
                {"name": "campaign_id", "type": "VARCHAR(50)"},
                {"name": "customer_id", "type": "VARCHAR(50)"},
                {"name": "segment_id", "type": "VARCHAR(50)"},
                {"name": "touchpoint", "type": "VARCHAR(50)"},
                {"name": "attributed_revenue", "type": "DECIMAL(12,2)"},
                {"name": "conversion_date", "type": "TIMESTAMP"},
            ],
        },
    ]


def _generate_etl_jobs(kpi_framework: dict) -> list[dict]:
    return [
        {
            "job_name": "daily_segment_metrics",
            "schedule": "0 2 * * *",  # 2 AM daily
            "source": "campaign_platform + data_warehouse",
            "destination": "segment_daily_metrics",
        },
        {
            "job_name": "weekly_segment_reassignment",
            "schedule": "0 3 * * 1",  # 3 AM every Monday
            "source": "customer_data_warehouse",
            "destination": "segment_assignments",
        },
    ]


def _generate_dashboard_configs(kpi_framework: dict, tool: str) -> list[dict]:
    return [
        {
            "dashboard_name": "Segment Performance Overview",
            "tool": tool,
            "widgets": [
                {"type": "kpi_card", "metric": "total_revenue_impact"},
                {"type": "line_chart", "metric": "weekly_revenue_by_segment"},
                {"type": "bar_chart", "metric": "segment_size_distribution"},
                {"type": "table", "metric": "kpi_scorecard_by_segment"},
            ],
        },
        {
            "dashboard_name": "Campaign Deep Dive",
            "tool": tool,
            "widgets": [
                {"type": "funnel", "metric": "campaign_conversion_funnel"},
                {"type": "heatmap", "metric": "channel_effectiveness"},
                {"type": "cohort", "metric": "cohort_retention"},
            ],
        },
    ]


def _generate_alert_configs(kpi_framework: dict) -> list[dict]:
    return [
        {
            "alert_name": "kpi_missed",
            "condition": "actual < target * 0.8 for 2 consecutive periods",
            "severity": "high",
            "notify": ["marketing_team", "segment_owner"],
        },
        {
            "alert_name": "segment_size_anomaly",
            "condition": "segment_size_change > 25% week-over-week",
            "severity": "medium",
            "notify": ["data_team"],
        },
        {
            "alert_name": "churn_spike",
            "condition": "segment_churn_rate > baseline * 1.5",
            "severity": "critical",
            "notify": ["marketing_team", "executives"],
        },
    ]


def _kpi_status(actual, target) -> str:
    try:
        actual_f = float(actual)
        target_f = float(target)
        if actual_f >= target_f * 0.95:
            return "on_track"
        elif actual_f >= target_f * 0.80:
            return "at_risk"
        return "missed"
    except (ValueError, TypeError):
        return "unknown"


def _compute_variance(actual, target) -> str:
    try:
        actual_f = float(actual)
        target_f = float(target)
        if target_f == 0:
            return "N/A"
        pct = ((actual_f - target_f) / target_f) * 100
        return f"{pct:+.1f}%"
    except (ValueError, TypeError):
        return "N/A"


def _overall_health(statuses: list[str]) -> str:
    if not statuses:
        return "unknown"
    on_track = statuses.count("on_track") / len(statuses)
    if on_track >= 0.8:
        return "healthy"
    elif on_track >= 0.6:
        return "needs_attention"
    return "at_risk"
```

### 7.3 Agent Definition

```python
ANALYTICS_SYSTEM_PROMPT = """You are the Performance Analytics Agent for a customer segmentation system.

Your responsibilities:
1. Define KPIs and success metrics for each segment and strategy
2. Set up tracking infrastructure (tables, ETL jobs, dashboards)
3. Create a feedback loop for continuous optimization
4. Generate performance reports with actionable insights
5. Establish alerting for anomalies and underperformance
6. Design A/B testing frameworks for strategy optimization
7. Track segment migration and customer lifecycle transitions

Guidelines:
- KPIs must be SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- Always include a control group for attribution (5% holdout)
- Track both leading indicators (engagement) and lagging indicators (revenue)
- Set up automated alerts for significant deviations
- Design dashboards for different audiences (executives, marketers, analysts)
- Plan for incrementality measurement, not just attribution
- Create feedback loops that trigger automatic re-evaluation
- Document all metric definitions for consistency

Output: A JSON object containing:
- kpi_framework: KPIs for each segment and strategy
- tracking_setup: Infrastructure configuration
- feedback_loop: Continuous optimization mechanisms
- alert_config: Automated alert rules
- dashboard_specs: Dashboard configurations
- reporting_schedule: Reporting cadence and audience
"""


class PerformanceAnalyticsAgent(DeepAgent):
    """Agent responsible for performance tracking and optimization."""

    def __init__(self, llm):
        tools = [
            Tool.from_function(define_kpi_framework),
            Tool.from_function(setup_tracking_infrastructure),
            Tool.from_function(create_feedback_loop),
            Tool.from_function(generate_performance_report),
        ]
        super().__init__(
            name="Analytics",
            llm=llm,
            tools= tools,
            system_prompt=ANALYTICS_SYSTEM_PROMPT,
        )
```

---

## 8. Code Examples and Snippets

### 8.1 Complete Pipeline Runner

```python
# pipeline_runner.py
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Run the complete customer segmentation pipeline."""
    from implementations.customer_segmentation_impl import SegmentationOrchestrator

    orchestrator = SegmentationOrchestrator(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379")
    )

    config = {
        "data_sources": {
            "crm": {
                "endpoint": os.getenv("CRM_ENDPOINT"),
                "api_key": os.getenv("CRM_API_KEY"),
            },
            "ecommerce": {
                "store": os.getenv("SHOPIFY_STORE"),
                "token": os.getenv("SHOPIFY_TOKEN"),
            },
            "analytics": {
                "property_id": os.getenv("GA4_PROPERTY_ID"),
                "credentials_path": os.getenv("GA4_CREDENTIALS_PATH"),
            },
        },
        "business_context": {
            "total_budget": 100000,
            "goals": ["retention", "upsell"],
            "constraints": {
                "min_per_segment": 5000,
                "max_per_segment": 40000,
            },
        },
        "date_range": {
            "start": "2026-01-01",
            "end": "2026-09-30",
        },
    }

    print("Starting customer segmentation pipeline...")
    state = await orchestrator.run_pipeline(config)

    print(f"\nPipeline completed with status: {state.status}")
    print(f"Pipeline ID: {state.pipeline_id}")
    print(f"Segments created: {len(state.segments)}")
    print(f"Strategies generated: {len(state.strategies)}")

    if state.errors:
        print(f"\nErrors encountered: {len(state.errors)}")
        for error in state.errors:
            print(f"  - {error['phase']}: {error['error']}")

    return state


if __name__ == "__main__":
    result = asyncio.run(main())
```

### 8.2 FastAPI Endpoint

```python
# api.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import asyncio

app = FastAPI(title="Customer Segmentation API", version="1.0")


class PipelineRequest(BaseModel):
    data_sources: dict
    business_context: dict
    date_range: dict
    callback_url: Optional[str] = None


class PipelineResponse(BaseModel):
    pipeline_id: str
    status: str
    message: str


class PipelineStatusResponse(BaseModel):
    pipeline_id: str
    status: str
    segments_count: int
    strategies_count: int
    errors: list[dict]


@app.post("/api/v1/segmentation/run", response_model=PipelineResponse)
async def run_segmentation(
    request: PipelineRequest,
    background_tasks: BackgroundTasks,
):
    """Start a new segmentation pipeline run."""
    from implementations.customer_segmentation_impl import SegmentationOrchestrator

    orchestrator = SegmentationOrchestrator()
    pipeline_id = str(uuid.uuid4())

    # Run in background
    background_tasks.add_task(
        _run_pipeline_async,
        orchestrator,
        pipeline_id,
        request.data_sources,
        request.business_context,
        request.date_range,
        request.callback_url,
    )

    return PipelineResponse(
        pipeline_id=pipeline_id,
        status="started",
        message="Segmentation pipeline started. Check status endpoint for progress.",
    )


@app.get("/api/v1/segmentation/{pipeline_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(pipeline_id: str):
    """Get the status of a segmentation pipeline run."""
    import redis
    import json

    r = redis.from_url("redis://localhost:6379", decode_responses=True)
    data = r.get(f"pipeline:{pipeline_id}")

    if not data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    state = json.loads(data)
    return PipelineStatusResponse(
        pipeline_id=state["pipeline_id"],
        status=state["status"],
        segments_count=len(state.get("segments", [])),
        strategies_count=len(state.get("strategies", [])),
        errors=state.get("errors", []),
    )


@app.get("/api/v1/segments")
async def list_segments(pipeline_id: str):
    """List all segments from a completed pipeline."""
    import redis
    import json

    r = redis.from_url("redis://localhost:6379", decode_responses=True)
    data = r.get(f"pipeline:{pipeline_id}")

    if not data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    state = json.loads(data)
    return {"segments": state.get("segments", [])}


@app.get("/api/v1/segments/{segment_id}/strategy")
async def get_segment_strategy(segment_id: str, pipeline_id: str):
    """Get the marketing strategy for a specific segment."""
    import redis
    import json

    r = redis.from_url("redis://localhost:6379", decode_responses=True)
    data = r.get(f"pipeline:{pipeline_id}")

    if not data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    state = json.loads(data)
    strategies = [
        s for s in state.get("strategies", [])
        if s.get("segment_id") == segment_id
    ]

    if not strategies:
        raise HTTPException(status_code=404, detail="Strategy not found for segment")

    return {"strategy": strategies[0]}


async def _run_pipeline_async(
    orchestrator, pipeline_id, data_sources, business_context, date_range, callback_url
):
    """Async wrapper for pipeline execution."""
    config = {
        "data_sources": data_sources,
        "business_context": business_context,
        "date_range": date_range,
    }
    state = await orchestrator.run_pipeline(config)

    # Send callback if configured
    if callback_url:
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(callback_url, json=state.model_dump())
```

### 8.3 Docker Compose Setup

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/segmentation
    depends_on:
      - redis
      - db
    volumes:
      - ./implementations:/app/implementations

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/segmentation
    depends_on:
      - redis
      - db
    deploy:
      replicas: 2

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=segmentation
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  scheduler:
    build:
      context: .
      dockerfile: Dockerfile.scheduler
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/segmentation
    depends_on:
      - redis
      - db

volumes:
  redis_data:
  postgres_data:
```

### 8.4 Requirements File

```txt
# requirements.txt
langchain>=0.3.0
langchain-deepagents>=0.1.0
langchain-openai>=0.2.0
langchain-core>=0.3.0
langchain-community>=0.3.0
openai>=1.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
redis>=5.0.0
httpx>=0.25.0
pydantic>=2.0.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
google-analytics-data>=0.18.0
python-dotenv>=1.0.0
asyncpg>=0.29.0
sqlalchemy>=2.0.0
alembic>=1.12.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### 8.5 Environment Configuration

```bash
# .env
OPENAI_API_KEY=sk-...
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/segmentation

# Data Source Credentials
CRM_ENDPOINT=https://api.hubspot.com
CRM_API_KEY=pat-...
SHOPIFY_STORE=your-store.myshopify.com
SHOPIFY_TOKEN=shpat_...
GA4_PROPERTY_ID=123456789
GA4_CREDENTIALS_PATH=/path/to/service-account.json

# Business Configuration
TOTAL_BUDGET=100000
MIN_SEGMENT_BUDGET=5000
MAX_SEGMENT_BUDGET=40000
```

---

## 9. Testing Strategy

### 9.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  ← Full pipeline integration tests
                    │  (10%)  │
                   ┌┴─────────┴┐
                   │ Integration│ ← Agent-to-agent communication
                   │   (20%)    │
                  ┌┴────────────┴┐
                  │    Unit       │ ← Individual tool functions
                  │    (70%)      │
                  └───────────────┘
```

### 9.2 Unit Tests

```python
# tests/test_data_collector.py
import pytest
from implementations.customer_segmentation_impl import (
    DataCollectorAgent,
    _parse_age,
    _safe_divide,
    _recency_score,
    _compute_churn_risk,
    _merge_customer_records,
)
from datetime import datetime, timezone, timedelta


class TestDataCollectorHelpers:
    """Unit tests for Data Collector helper functions."""

    def test_parse_age_from_birth_year(self):
        current_year = datetime.now().year
        assert _parse_age(current_year - 30) == 30

    def test_parse_age_direct(self):
        assert _parse_age(25) == 25

    def test_parse_age_none(self):
        assert _parse_age(None) is None

    def test_parse_age_invalid_string(self):
        assert _parse_age("not_a_number") is None

    def test_safe_divide_normal(self):
        assert _safe_divide(100.0, 4) == 25.0

    def test_safe_divide_zero_denominator(self):
        assert _safe_divide(100.0, 0) == 0.0

    def test_recency_score_recent(self):
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(days=10)).isoformat()
        assert _recency_score(recent, now) == 100.0

    def test_recency_score_old(self):
        now = datetime.now(timezone.utc)
        old = (now - timedelta(days=400)).isoformat()
        assert _recency_score(old, now) == 0.0

    def test_recency_score_none(self):
        now = datetime.now(timezone.utc)
        assert _recency_score(None, now) == 0.0

    def test_churn_risk_high(self):
        now = datetime.now(timezone.utc)
        customer = {
            "last_order_date": (now - timedelta(days=400)).isoformat(),
            "engagement_score": 10,
            "total_orders": 10,
            "recent_orders_90d": 0,
        }
        risk = _compute_churn_risk(customer, now)
        assert risk > 0.7

    def test_churn_risk_low(self):
        now = datetime.now(timezone.utc)
        customer = {
            "last_order_date": (now - timedelta(days=5)).isoformat(),
            "engagement_score": 90,
            "total_orders": 10,
            "recent_orders_90d": 3,
        }
        risk = _compute_churn_risk(customer, now)
        assert risk < 0.3

    def test_merge_customer_records(self):
        a = {
            "customer_id": "1",
            "email": "test@example.com",
            "total_revenue": 100.0,
            "total_orders": 2,
            "preferred_categories": ["electronics"],
        }
        b = {
            "customer_id": "1",
            "email": "test@example.com",
            "total_revenue": 50.0,
            "total_orders": 1,
            "preferred_categories": ["books"],
            "age": 30,
        }
        merged = _merge_customer_records(a, b)
        assert merged["total_revenue"] == 150.0
        assert merged["total_orders"] == 3
        assert set(merged["preferred_categories"]) == {"electronics", "books"}
        assert merged["age"] == 30


# tests/test_analysis_agent.py
import pytest
import numpy as np
from implementations.customer_segmentation_impl import (
    compute_rfm_scores,
    perform_behavioral_clustering,
    _top_categories,
)


class TestAnalysisTools:
    """Unit tests for Analysis Agent tools."""

    @pytest.fixture
    def sample_customers(self):
        return [
            {
                "customer_id": f"cust_{i}",
                "total_orders": np.random.randint(1, 50),
                "total_revenue": np.random.uniform(50, 5000),
                "avg_order_value": np.random.uniform(20, 500),
                "engagement_score": np.random.uniform(0, 100),
                "lifetime_value": np.random.uniform(100, 10000),
                "churn_risk": np.random.uniform(0, 1),
                "last_order_date": "2026-09-15T00:00:00Z",
                "preferred_categories": np.random.choice(
                    ["electronics", "clothing", "books", "home"], size=2
                ).tolist(),
            }
            for i in range(100)
        ]

    def test_compute_rfm_scores(self, sample_customers):
        result = compute_rfm_scores.invoke({"customers": sample_customers})
        assert "rfm_scores" in result
        assert "segment_distribution" in result
        assert "statistics" in result
        assert len(result["rfm_scores"]) == 100

    def test_rfm_segment_valid(self, sample_customers):
        result = compute_rfm_scores.invoke({"customers": sample_customers})
        valid_segments = {
            "champions", "loyal_customers", "potential_loyalists",
            "new_customers", "at_risk", "cannot_lose", "needs_attention", "lost",
        }
        for score in result["rfm_scores"]:
            assert score["rfm_segment"] in valid_segments

    def test_behavioral_clustering(self, sample_customers):
        result = perform_behavioral_clustering.invoke({
            "customers": sample_customers,
            "n_clusters": 4,
        })
        assert "n_clusters" in result
        assert "silhouette_score" in result
        assert "cluster_profiles" in result
        assert result["n_clusters"] == 4
        assert len(result["customer_assignments"]) == 100

    def test_clustering_auto_k(self, sample_customers):
        result = perform_behavioral_clustering.invoke({
            "customers": sample_customers,
            "n_clusters": None,
        })
        assert 2 <= result["n_clusters"] <= 10

    def test_top_categories(self):
        import pandas as pd
        df = pd.DataFrame({
            "preferred_categories": [
                ["electronics", "books"],
                ["electronics", "clothing"],
                ["books", "home"],
            ]
        })
        top = _top_categories(df, top_n=2)
        assert len(top) == 2
        assert top[0]["category"] == "electronics"


# tests/test_segment_builder.py
import pytest
from implementations.customer_segmentation_impl import (
    create_segment_definitions,
    assign_customers_to_segments,
    validate_segment_quality,
    _matches_segment,
)


class TestSegmentBuilder:
    """Unit tests for Segment Builder tools."""

    @pytest.fixture
    def sample_rfm_analysis(self):
        return {
            "segment_distribution": {
                "champions": 50,
                "loyal_customers": 100,
                "at_risk": 30,
                "lost": 20,
            },
            "statistics": {
                "avg_recency_days": 45,
                "avg_frequency": 5.2,
                "avg_monetary": 250.0,
            },
        }

    @pytest.fixture
    def sample_clustering_results(self):
        return {
            "n_clusters": 3,
            "silhouette_score": 0.45,
            "cluster_profiles": {
                "cluster_0": {
                    "size": 80,
                    "percentage": 40.0,
                    "avg_revenue": 500.0,
                    "avg_orders": 8.0,
                    "avg_engagement": 75.0,
                    "avg_churn_risk": 0.15,
                    "avg_ltv": 2000.0,
                    "top_categories": [{"category": "electronics", "count": 40}],
                },
                "cluster_1": {
                    "size": 60,
                    "percentage": 30.0,
                    "avg_revenue": 150.0,
                    "avg_orders": 3.0,
                    "avg_engagement": 45.0,
                    "avg_churn_risk": 0.40,
                    "avg_ltv": 500.0,
                    "top_categories": [{"category": "books", "count": 30}],
                },
            },
        }

    def test_create_segment_definitions(self, sample_rfm_analysis, sample_clustering_results):
        result = create_segment_definitions.invoke({
            "rfm_analysis": sample_rfm_analysis,
            "clustering_results": sample_clustering_results,
            "category_analysis": {},
            "business_rules": {},
        })
        assert "segments" in result
        assert result["total_segments"] >= 8  # 8 RFM + clusters

    def test_assign_customers_to_segments(self):
        customers = [
            {"customer_id": "1", "rfm_segment": "champions", "total_revenue": 1000},
            {"customer_id": "2", "rfm_segment": "lost", "total_revenue": 50},
        ]
        segments = [
            {"segment_id": "seg_champions", "criteria": {"rfm_segment": "champions"}},
            {"segment_id": "seg_lost", "criteria": {"rfm_segment": "lost"}},
        ]
        result = assign_customers_to_segments.invoke({
            "customers": customers,
            "segment_definitions": segments,
        })
        assert "1" in result["assignments"]["seg_champions"]
        assert "2" in result["assignments"]["seg_lost"]
        assert len(result["unassigned_customers"]) == 0

    def test_validate_segment_quality(self):
        assignments = {
            "assignments": {"seg_a": ["1", "2", "3"], "seg_b": ["4", "5"]},
            "segment_statistics": {
                "seg_a": {"size": 3, "avg_revenue": 500, "avg_engagement": 70, "avg_churn_risk": 0.2, "avg_ltv": 2000},
                "seg_b": {"size": 2, "avg_revenue": 100, "avg_engagement": 30, "avg_churn_risk": 0.6, "avg_ltv": 300},
            },
            "unassigned_customers": [],
        }
        customers = [{"customer_id": str(i), "total_revenue": 300} for i in range(5)]
        result = validate_segment_quality.invoke({
            "segment_assignments": assignments,
            "customers": customers,
        })
        assert "segment_quality" in result
        assert "overall_assessment" in result

    def test_matches_segment_rfm(self):
        customer = {"rfm_segment": "champions"}
        segment = {"criteria": {"rfm_segment": "champions"}}
        assert _matches_segment(customer, segment) is True

    def test_matches_segment_revenue(self):
        customer = {"total_revenue": 600}
        segment = {"criteria": {"min_revenue": 500, "max_revenue": 1000}}
        assert _matches_segment(customer, segment) is True
```

### 9.3 Integration Tests

```python
# tests/test_integration.py
import pytest
import pytest_asyncio
import redis
import json
from unittest.mock import AsyncMock, patch, MagicMock


@pytest_asyncio.fixture
async def orchestrator():
    """Create an orchestrator with mocked LLM."""
    from implementations.customer_segmentation_impl import SegmentationOrchestrator

    orch = SegmentationOrchestrator(redis_url="redis://localhost:6379")
    # Mock the LLM to avoid API calls
    for agent in orch.agents.values():
        agent.llm = MagicMock()
    yield orch


@pytest.mark.asyncio
async def test_full_pipeline_execution(orchestrator):
    """Test the complete pipeline from data collection to analytics."""
    config = {
        "data_sources": {"crm": {"endpoint": "http://test", "api_key": "test"}},
        "business_context": {"total_budget": 50000, "goals": ["retention"]},
        "date_range": {"start": "2026-01-01", "end": "2026-09-30"},
    }

    # Mock agent responses
    with patch.object(
        orchestrator.agents[AgentRole.DATA_COLLECTOR],
        "arun",
        new_callable=AsyncMock,
    ) as mock_collect:
        mock_collect.return_value = {
            "state_update": {
                "raw_data": [
                    {"customer_id": "1", "email": "test@example.com", "total_revenue": 500},
                ]
            }
        }

        with patch.object(
            orchestrator.agents[AgentRole.ANALYST],
            "arun",
            new_callable=AsyncMock,
        ) as mock_analyze:
            mock_analyze.return_value = {
                "state_update": {
                    "analysis_results": {"rfm": {"segment_distribution": {"champions": 1}}}
                }
            }

            with patch.object(
                orchestrator.agents[AgentRole.SEGMENT_BUILDER],
                "arun",
                new_callable=AsyncMock,
            ) as mock_segment:
                mock_segment.return_value = {
                    "state_update": {
                        "segments": [{"segment_id": "seg_1", "name": "Test Segment"}]
                    }
                }

                with patch.object(
                    orchestrator.agents[AgentRole.STRATEGIST],
                    "arun",
                    new_callable=AsyncMock,
                ) as mock_strategy:
                    mock_strategy.return_value = {
                        "state_update": {
                            "strategies": [{"strategy_id": "strat_1", "segment_id": "seg_1"}]
                        }
                    }

                    with patch.object(
                        orchestrator.agents[AgentRole.REVIEWER],
                        "arun",
                        new_callable=AsyncMock,
                    ) as mock_review:
                        mock_review.return_value = {
                            "state_update": {"review_feedback": [{"approved": True}]}
                        }

                        with patch.object(
                            orchestrator.agents[AgentRole.ANALYTICS],
                            "arun",
                            new_callable=AsyncMock,
                        ) as mock_analytics:
                            mock_analytics.return_value = {
                                "state_update": {"analytics": {"kpis": {}}}
                            }

                            state = await orchestrator.run_pipeline(config)

    assert state.status == "completed"
    assert len(state.raw_data) == 1
    assert len(state.segments) == 1
    assert len(state.strategies) == 1


@pytest.mark.asyncio
async def test_pipeline_error_handling(orchestrator):
    """Test that pipeline errors are captured gracefully."""
    config = {
        "data_sources": {},
        "business_context": {},
        "date_range": {},
    }

    with patch.object(
        orchestrator.agents[AgentRole.DATA_COLLECTOR],
        "arun",
        new_callable=AsyncMock,
        side_effect=Exception("API timeout"),
    ):
        state = await orchestrator.run_pipeline(config)

    assert state.status == "failed"
    assert len(state.errors) > 0
    assert "API timeout" in state.errors[0]["error"]


@pytest.mark.asyncio
async def test_agent_message_protocol(orchestrator):
    """Test that agent messages are properly formatted and routed."""
    message = AgentMessage(
        sender=AgentRole.DATA_COLLECTOR,
        recipient=AgentRole.ANALYST,
        task_id="test-123",
        status=TaskStatus.IN_PROGRESS,
        payload={"test": "data"},
    )

    assert message.message_id is not None
    assert message.sender == AgentRole.DATA_COLLECTOR
    assert message.recipient == AgentRole.ANALYST
    assert message.status == TaskStatus.IN_PROGRESS
```

### 9.4 End-to-End Tests

```python
# tests/test_e2e.py
import pytest
import pytest_asyncio
import asyncio
from testcontainers.redis import RedisContainer
from testcontainers.postgres import PostgresContainer


@pytest_asyncio.fixture(scope="module")
async def infrastructure():
    """Spin up real Redis and Postgres for E2E tests."""
    with RedisContainer("redis:7") as redis_container:
        with PostgresContainer("postgres:16") as postgres_container:
            yield {
                "redis_url": redis_container.get_connection_url(),
                "database_url": postgres_container.get_connection_url(),
            }


@pytest.mark.asyncio
async def test_end_to_end_segmentation(infrastructure):
    """Full E2E test with real infrastructure (mocked LLM)."""
    from implementations.customer_segmentation_impl import SegmentationOrchestrator

    orchestrator = SegmentationOrchestrator(redis_url=infrastructure["redis_url"])

    # Use a small, known dataset
    config = {
        "data_sources": {"test": {"dataset": "synthetic_small"}},
        "business_context": {
            "total_budget": 10000,
            "goals": ["retention", "upsell"],
            "constraints": {"min_per_segment": 1000, "max_per_segment": 5000},
        },
        "date_range": {"start": "2026-01-01", "end": "2026-09-30"},
    }

    # This test would use a mock LLM that returns predetermined responses
    # based on the input, allowing full pipeline validation
    state = await orchestrator.run_pipeline(config)

    # Assertions
    assert state.status in ["completed", "failed"]
    if state.status == "completed":
        assert len(state.segments) >= 3
        assert len(state.strategies) >= 3
        assert state.analytics != {}


@pytest.mark.asyncio
async def test_pipeline_idempotency(infrastructure):
    """Test that running the same pipeline twice produces consistent results."""
    from implementations.customer_segmentation_impl import SegmentationOrchestrator

    orchestrator = SegmentationOrchestrator(redis_url=infrastructure["redis_url"])
    config = {
        "data_sources": {"test": {"dataset": "synthetic_small"}},
        "business_context": {"total_budget": 10000},
        "date_range": {"start": "2026-01-01", "end": "2026-09-30"},
    }

    state1 = await orchestrator.run_pipeline(config)
    state2 = await orchestrator.run_pipeline(config)

    # Segments should be identical (same data, same config)
    seg_names_1 = sorted([s["name"] for s in state1.segments])
    seg_names_2 = sorted([s["name"] for s in state2.segments])
    assert seg_names_1 == seg_names_2
```

### 9.5 Performance Tests

```python
# tests/test_performance.py
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor


class TestPerformance:
    """Performance benchmarks for critical paths."""

    @pytest.mark.benchmark
    def test_rfm_computation_performance(self, benchmark):
        """Benchmark RFM score computation with 10K customers."""
        import numpy as np
        from implementations.customer_segmentation_impl import compute_rfm_scores

        customers = [
            {
                "customer_id": f"cust_{i}",
                "total_orders": np.random.randint(1, 50),
                "total_revenue": np.random.uniform(50, 5000),
                "avg_order_value": np.random.uniform(20, 500),
                "engagement_score": np.random.uniform(0, 100),
                "lifetime_value": np.random.uniform(100, 10000),
                "churn_risk": np.random.uniform(0, 1),
                "last_order_date": "2026-09-15T00:00:00Z",
            }
            for i in range(10000)
        ]

        result = benchmark(compute_rfm_scores.invoke, {"customers": customers})
        assert len(result["rfm_scores"]) == 10000

    @pytest.mark.benchmark
    def test_clustering_performance(self, benchmark):
        """Benchmark clustering with 10K customers."""
        import numpy as np
        from implementations.customer_segmentation_impl import perform_behavioral_clustering

        customers = [
            {
                "customer_id": f"cust_{i}",
                "total_orders": np.random.randint(1, 50),
                "total_revenue": np.random.uniform(50, 5000),
                "avg_order_value": np.random.uniform(20, 500),
                "engagement_score": np.random.uniform(0, 100),
                "lifetime_value": np.random.uniform(100, 10000),
                "churn_risk": np.random.uniform(0, 1),
            }
            for i in range(10000)
        ]

        result = benchmark(
            perform_behavioral_clustering.invoke,
            {"customers": customers, "n_clusters": 5},
        )
        assert result["n_clusters"] == 5

    @pytest.mark.asyncio
    async def test_pipeline_throughput(self):
        """Test that pipeline completes within acceptable time."""
        from implementations.customer_segmentation_impl import SegmentationOrchestrator

        orchestrator = SegmentationOrchestrator()
        config = {
            "data_sources": {"test": {"dataset": "synthetic_small"}},
            "business_context": {"total_budget": 10000},
            "date_range": {"start": "2026-01-01", "end": "2026-09-30"},
        }

        start = time.time()
        state = await orchestrator.run_pipeline(config)
        elapsed = time.time() - start

        # Pipeline should complete within 5 minutes (with mocked LLM)
        assert elapsed < 300, f"Pipeline took {elapsed:.1f}s, expected < 300s"
```

### 9.6 Test Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    benchmark: Performance benchmark tests
    slow: Slow integration tests
    e2e: End-to-end tests requiring infrastructure
addopts = -v --tb=short --strict-markers
```

---

## Appendix A: Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Server   │  │  API Server   │  │  API Server   │      │
│  │  (FastAPI)    │  │  (FastAPI)    │  │  (FastAPI)    │      │
│  │  Replicas: 3  │  │  Replicas: 3  │  │  Replicas: 3  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│  ┌──────┴──────────────────┴──────────────────┴───────┐      │
│  │              Redis (Task Queue + State)              │      │
│  └──────────────────────┬──────────────────────────────┘      │
│                         │                                     │
│  ┌──────────────┐  ┌────┴─────────┐  ┌──────────────┐       │
│  │  Worker       │  │  Worker       │  │  Worker       │       │
│  │  (Celery)     │  │  (Celery)     │  │  (Celery)     │       │
│  │  Replicas: 5  │  │  Replicas: 5  │  │  Replicas: 5  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                  │                  │               │
│  ┌──────┴──────────────────┴──────────────────┴───────┐      │
│  │           PostgreSQL (Persistent State)              │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │  Scheduler    │  │  Monitoring   │                         │
│  │  (CronJobs)   │  │  (Prometheus) │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Appendix B: Monitoring and Observability

```python
# monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
PIPELINE_RUNS = Counter(
    "segmentation_pipeline_runs_total",
    "Total pipeline runs",
    ["status"],
)
PIPELINE_DURATION = Histogram(
    "segmentation_pipeline_duration_seconds",
    "Pipeline execution time",
    ["phase"],
)
ACTIVE_SEGMENTS = Gauge(
    "segmentation_active_segments",
    "Number of active segments",
)
AGENT_CALLS = Counter(
    "segmentation_agent_calls_total",
    "Agent invocation count",
    ["agent_name", "status"],
)
LLM_TOKENS = Counter(
    "segmentation_llm_tokens_total",
    "LLM token usage",
    ["agent_name", "token_type"],
)


def track_phase(phase_name: str):
    """Decorator to track phase execution time."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                PIPELINE_DURATION.labels(phase=phase_name).observe(time.time() - start)
                return result
            except Exception as e:
                PIPELINE_RUNS.labels(status="failed").inc()
                raise
        return wrapper
    return decorator
```

---

*End of Implementation Plan*
