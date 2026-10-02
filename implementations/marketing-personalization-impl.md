# AI-Powered Marketing Personalization Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0
**Date:** 2026-10-01
**Author:** Ahmed Hassan
**Status:** Draft for Review

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Data Collection Agent Implementation](#2-data-collection-agent-implementation)
3. [Analysis Agent Implementation](#3-analysis-agent-implementation)
4. [Personalization Agent Implementation](#4-personalization-agent-implementation)
5. [Optimization Agent Implementation](#5-optimization-agent-implementation)
6. [Governance Agent Implementation](#6-governance-agent-implementation)
7. [Performance Analytics Agent Implementation](#7-performance-analytics-agent-implementation)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The AI-powered marketing personalization system uses LangChain DeepAgents to orchestrate a multi-agent pipeline that collects customer data, analyzes behavior patterns, generates personalized content, optimizes delivery timing, enforces governance policies, and tracks performance metrics.

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent (DeepAgents)                   │
│              Coordinates workflow, manages state, routes             │
└──────────┬──────────┬──────────┬──────────┬──────────┬──────────────┘
           │          │          │          │          │
    ┌──────▼──┐ ┌─────▼────┐ ┌───▼──────┐ ┌─▼────────┐ ┌▼─────────────┐
    │  Data   │ │ Analysis │ │Personal- │ │Optimize- │ │  Governance  │
    │Collect  │ │  Agent   │ │ization   │ │  tion    │ │    Agent     │
    │  Agent  │ │          │ │  Agent   │ │  Agent   │ │              │
    └────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘
         │           │            │            │              │
    ┌────▼───────────▼────────────▼────────────▼──────────────▼────┐
    │                    Shared State & Memory Layer                  │
    │         (LangGraph State + Checkpointing + Vector Store)       │
    └───────────────────────────────────────────────────────────────┘
                                    │
    ┌───────────────────────────────▼───────────────────────────────┐
    │              Performance Analytics Agent                        │
    │         (Monitors all agents, reports to Orchestrator)          │
    └───────────────────────────────────────────────────────────────┘
```

### 1.3 Agent Roles and Responsibilities

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **Orchestrator** | Workflow coordination, task routing, state management | User requests, system events | Agent dispatch decisions, final responses |
| **Data Collection** | Gather customer data from multiple sources | Customer IDs, data source configs | Unified customer profiles |
| **Analysis** | Behavioral segmentation, pattern detection | Customer profiles | Segments, insights, predictions |
| **Personalization** | Content generation and recommendation | Segments, insights, context | Personalized content, offers, messages |
| **Optimization** | A/B testing, timing optimization, channel selection | Performance data, content variants | Optimized delivery plans |
| **Governance** | Compliance checking, bias detection, policy enforcement | All agent outputs | Approved/rejected decisions, audit logs |
| **Performance Analytics** | Metrics collection, reporting, alerting | All agent activities | Dashboards, reports, alerts |

### 1.4 Technology Stack

- **Framework:** LangChain + LangGraph + DeepAgents
- **LLM:** GPT-4 / Claude 3.5 Sonnet (configurable per agent)
- **Vector Store:** Pinecone / Weaviate for embeddings and similarity search
- **State Management:** LangGraph with SQLite/PostgreSQL checkpointing
- **Message Queue:** Redis / RabbitMQ for inter-agent communication
- **Data Sources:** CRM (Salesforce), CDP (Segment), Web Analytics (GA4), Email (SendGrid), Social (Meta API)
- **Monitoring:** LangSmith for tracing, Prometheus + Grafana for metrics
- **Deployment:** Docker + Kubernetes, AWS/GCP

### 1.5 Communication Protocol

Agents communicate via LangGraph's state-based messaging:

```python
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.postgres import PostgresSaver

# Shared state schema
class MarketingState(TypedDict):
    customer_id: str
    customer_profile: dict
    segments: list[str]
    insights: list[dict]
    personalized_content: dict
    delivery_plan: dict
    governance_decisions: list[dict]
    performance_metrics: dict
    messages: Annotated[list, add_messages]
    metadata: dict
```

### 1.6 Workflow Stages

1. **Ingestion** → Data Collection Agent gathers raw data
2. **Enrichment** → Analysis Agent processes and segments
3. **Generation** → Personalization Agent creates content
4. **Validation** → Governance Agent checks compliance
5. **Optimization** → Optimization Agent refines delivery
6. **Execution** → Content delivered via appropriate channels
7. **Measurement** → Performance Analytics Agent tracks results
8. **Feedback Loop** → Results feed back into Analysis Agent

---

## 2. Data Collection Agent Implementation

### 2.1 Purpose

The Data Collection Agent is responsible for aggregating customer data from multiple sources into a unified, normalized customer profile. It handles real-time and batch data ingestion, deduplication, and data quality validation.

### 2.2 Data Sources

| Source | Data Type | Collection Method | Frequency |
|--------|-----------|-------------------|-----------|
| CRM (Salesforce) | Demographics, purchase history, support tickets | REST API (bulk + streaming) | Real-time + Daily batch |
| CDP (Segment) | Behavioral events, traits, identities | Event streaming (webhook) | Real-time |
| Web Analytics (GA4) | Page views, sessions, conversions | Data API | Hourly |
| Email Platform (SendGrid) | Opens, clicks, bounces, unsubscribes | Event webhook | Real-time |
| Social Media (Meta, X) | Engagement, sentiment, mentions | Graph API + scraping | Every 15 min |
| Mobile App | In-app events, push interactions | SDK + API | Real-time |
| Transactional DB | Orders, refunds, subscriptions | CDC (Change Data Capture) | Real-time |
| Third-party Enrichment | Firmographic, intent data | API (Clearbit, Bombora) | Weekly |

### 2.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Optional
import httpx
import asyncio
from datetime import datetime, timedelta

# ─── Data Collection Tools ────────────────────────────────────────────

@tool
async def fetch_crm_data(customer_id: str, fields: Optional[list[str]] = None) -> dict:
    """Fetch customer data from Salesforce CRM.
    
    Args:
        customer_id: The unique customer identifier
        fields: Optional list of specific fields to retrieve
    
    Returns:
        Dictionary containing CRM record data
    """
    async with httpx.AsyncClient() as client:
        # Salesforce REST API query
        query = f"SELECT {', '.join(fields) if fields else 'Id, Name, Email, Phone, AccountId, CreatedDate, LastModifiedDate'} FROM Contact WHERE Id = '{customer_id}'"
        response = await client.get(
            f"{SALESFORCE_BASE_URL}/services/data/v59.0/query",
            params={"q": query},
            headers={"Authorization": f"Bearer {SALESFORCE_TOKEN}"}
        )
        response.raise_for_status()
        return response.json()["records"][0] if response.json()["records"] else {}


@tool
async def fetch_behavioral_events(customer_id: str, lookback_days: int = 90) -> list[dict]:
    """Fetch behavioral events from Segment CDP.
    
    Args:
        customer_id: The unique customer identifier
        lookback_days: Number of days to look back
    
    Returns:
        List of behavioral event dictionaries
    """
    start_date = (datetime.utcnow() - timedelta(days=lookback_days)).isoformat()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SEGMENT_API_URL}/events",
            json={
                "userId": customer_id,
                "startTime": start_date,
                "limit": 1000
            },
            headers={"Authorization": f"Bearer {SEGMENT_WRITE_KEY}"}
        )
        response.raise_for_status()
        return response.json().get("data", [])


@tool
async def fetch_web_analytics(customer_id: str, start_date: str, end_date: str) -> dict:
    """Fetch web analytics data from Google Analytics 4.
    
    Args:
        customer_id: The unique customer identifier
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        Dictionary containing page views, sessions, and conversion data
    """
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
    
    client = BetaAnalyticsDataClient()
    request = RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="customEvent:customer_id")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="conversions"),
            Metric(name="averageSessionDuration"),
            Metric(name="bounceRate"),
        ],
        dimension_filter={
            "filter": {
                "field_name": "customEvent:customer_id",
                "string_filter": {"value": customer_id}
            }
        }
    )
    response = client.run_report(request)
    return _parse_ga4_response(response)


@tool
async def fetch_email_engagement(customer_id: str) -> dict:
    """Fetch email engagement data from SendGrid.
    
    Args:
        customer_id: The unique customer identifier
    
    Returns:
        Dictionary containing email engagement metrics
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SENDGRID_API_URL}/v3/stats",
            params={
                "start_date": (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                "end_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "aggregated_by": "day"
            },
            headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"}
        )
        response.raise_for_status()
        # Filter for specific customer
        stats = response.json()
        return _filter_customer_email_stats(stats, customer_id)


@tool
async def fetch_purchase_history(customer_id: str) -> list[dict]:
    """Fetch purchase history from transactional database.
    
    Args:
        customer_id: The unique customer identifier
    
    Returns:
        List of purchase records
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{TRANSACTION_API_URL}/customers/{customer_id}/orders",
            params={"limit": 100, "include": "items,payments,refunds"},
            headers={"Authorization": f"Bearer {TRANSACTION_API_KEY}"}
        )
        response.raise_for_status()
        return response.json().get("orders", [])


@tool
async def fetch_social_engagement(customer_id: str) -> dict:
    """Fetch social media engagement data.
    
    Args:
        customer_id: The unique customer identifier
    
    Returns:
        Dictionary containing social engagement metrics
    """
    # Aggregate from multiple social platforms
    results = {}
    async with httpx.AsyncClient() as client:
        # Meta/Facebook
        try:
            meta_response = await client.get(
                f"{META_API_URL}/engagement",
                params={"customer_id": customer_id},
                headers={"Authorization": f"Bearer {META_ACCESS_TOKEN}"}
            )
            results["meta"] = meta_response.json() if meta_response.status_code == 200 else {}
        except Exception:
            results["meta"] = {}
        
        # X/Twitter
        try:
            x_response = await client.get(
                f"{X_API_URL}/engagement",
                params={"customer_id": customer_id},
                headers={"Authorization": f"Bearer {X_BEARER_TOKEN}"}
            )
            results["x"] = x_response.json() if x_response.status_code == 200 else {}
        except Exception:
            results["x"] = {}
    
    return results


@tool
async def enrich_customer_profile(customer_id: str) -> dict:
    """Enrich customer profile with third-party data.
    
    Args:
        customer_id: The unique customer identifier
    
    Returns:
        Dictionary containing enriched profile data
    """
    async with httpx.AsyncClient() as client:
        # Clearbit enrichment
        response = await client.get(
            f"{CLEARBIT_API_URL}/v2/combined/find",
            params={"email": customer_id},
            headers={"Authorization": f"Bearer {CLEARBIT_API_KEY}"}
        )
        if response.status_code == 200:
            return response.json()
        return {}


# ─── Data Collection Agent ───────────────────────────────────────────

DATA_COLLECTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Data Collection Agent for a marketing personalization system.
    
Your responsibility is to gather comprehensive customer data from multiple sources and compile
a unified, normalized customer profile.

Guidelines:
- Collect data from ALL available sources in parallel where possible
- Validate data quality and flag any inconsistencies
- Normalize data formats across sources
- Respect data privacy regulations (GDPR, CCPA) - only collect authorized data
- Handle missing data gracefully - note what's unavailable
- Deduplicate records across sources
- Timestamp all data collection activities

Output a structured customer profile with:
- Identity information (name, email, phone, address)
- Demographics (age, gender, location, income bracket)
- Behavioral data (web activity, email engagement, social activity)
- Transaction history (purchases, refunds, subscriptions)
- Enrichment data (firmographic, intent signals)
- Data quality score and completeness metrics
"""),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "{input}"),
])


def create_data_collection_agent(llm: Optional[ChatOpenAI] = None) -> AgentExecutor:
    """Create the Data Collection Agent.
    
    Returns:
        Configured AgentExecutor for data collection
    """
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [
        fetch_crm_data,
        fetch_behavioral_events,
        fetch_web_analytics,
        fetch_email_engagement,
        fetch_purchase_history,
        fetch_social_engagement,
        enrich_customer_profile,
    ]
    
    agent = create_openai_functions_agent(llm, tools, DATA_COLLECTION_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
    )
```

### 2.4 Data Normalization Pipeline

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import hashlib

class UnifiedCustomerProfile(BaseModel):
    """Standardized customer profile schema."""
    
    # Identity
    customer_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    
    # Demographics
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[dict] = None  # {city, state, country, postal_code}
    income_bracket: Optional[str] = None
    language: Optional[str] = "en"
    
    # Firmographic (B2B)
    company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    
    # Behavioral
    total_sessions: int = 0
    total_page_views: int = 0
    avg_session_duration: float = 0.0
    bounce_rate: float = 0.0
    last_visit: Optional[datetime] = None
    preferred_channels: list[str] = Field(default_factory=list)
    email_engagement_rate: float = 0.0
    social_engagement_score: float = 0.0
    
    # Transactional
    total_orders: int = 0
    total_revenue: float = 0.0
    avg_order_value: float = 0.0
    last_purchase: Optional[datetime] = None
    purchase_frequency: Optional[str] = None  # weekly, monthly, quarterly
    preferred_categories: list[str] = Field(default_factory=list)
    subscription_status: Optional[str] = None
    
    # Enrichment
    intent_signals: list[str] = Field(default_factory=list)
    lookalike_score: Optional[float] = None
    churn_risk: Optional[str] = None  # low, medium, high
    
    # Metadata
    data_sources: list[str] = Field(default_factory=list)
    data_quality_score: float = 0.0
    profile_completeness: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    consent_status: dict = Field(default_factory=dict)
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 120):
            raise ValueError('Invalid age')
        return v
    
    def compute_quality_score(self) -> float:
        """Compute data quality score based on completeness and consistency."""
        fields = self.dict()
        filled = sum(1 for v in fields.values() if v is not None and v != [] and v != {})
        total = len(fields)
        self.data_quality_score = filled / total if total > 0 else 0.0
        self.profile_completeness = self.data_quality_score
        return self.data_quality_score


class DataNormalizer:
    """Normalizes data from multiple sources into unified profile."""
    
    def __init__(self):
        self.source_weights = {
            "crm": 1.0,
            "segment": 0.9,
            "ga4": 0.8,
            "sendgrid": 0.85,
            "transactional": 0.95,
            "social": 0.6,
            "enrichment": 0.7,
        }
    
    def normalize(self, raw_data: dict[str, dict]) -> UnifiedCustomerProfile:
        """Merge and normalize data from all sources.
        
        Args:
            raw_data: Dictionary mapping source name to raw data
        
        Returns:
            UnifiedCustomerProfile
        """
        merged = {}
        sources_used = []
        
        for source, data in raw_data.items():
            if not data:
                continue
            sources_used.append(source)
            weight = self.source_weights.get(source, 0.5)
            normalized = self._normalize_source(source, data, weight)
            merged = self._deep_merge(merged, normalized)
        
        profile = UnifiedCustomerProfile(**merged)
        profile.data_sources = sources_used
        profile.compute_quality_score()
        return profile
    
    def _normalize_source(self, source: str, data: dict, weight: float) -> dict:
        """Normalize data from a specific source."""
        normalizers = {
            "crm": self._normalize_crm,
            "segment": self._normalize_segment,
            "ga4": self._normalize_ga4,
            "sendgrid": self._normalize_sendgrid,
            "transactional": self._normalize_transactional,
            "social": self._normalize_social,
            "enrichment": self._normalize_enrichment,
        }
        normalizer = normalizers.get(source, lambda d, w: d)
        return normalizer(data, weight)
    
    def _normalize_crm(self, data: dict, weight: float) -> dict:
        return {
            "email": data.get("Email"),
            "phone": data.get("Phone"),
            "first_name": data.get("FirstName"),
            "last_name": data.get("LastName"),
            "full_name": data.get("Name"),
            "company": data.get("Account", {}).get("Name"),
            "job_title": data.get("Title"),
        }
    
    def _normalize_segment(self, data: dict, weight: float) -> dict:
        traits = data.get("traits", {})
        return {
            "email": traits.get("email"),
            "first_name": traits.get("firstName"),
            "last_name": traits.get("lastName"),
            "total_sessions": traits.get("sessions", 0),
            "last_visit": traits.get("lastSeen"),
            "preferred_channels": traits.get("channels", []),
        }
    
    def _normalize_ga4(self, data: dict, weight: float) -> dict:
        return {
            "total_sessions": data.get("sessions", 0),
            "total_page_views": data.get("pageViews", 0),
            "avg_session_duration": data.get("avgSessionDuration", 0.0),
            "bounce_rate": data.get("bounceRate", 0.0),
        }
    
    def _normalize_sendgrid(self, data: dict, weight: float) -> dict:
        return {
            "email_engagement_rate": data.get("engagementRate", 0.0),
        }
    
    def _normalize_transactional(self, data: dict, weight: float) -> dict:
        orders = data.get("orders", [])
        total_revenue = sum(o.get("total", 0) for o in orders)
        return {
            "total_orders": len(orders),
            "total_revenue": total_revenue,
            "avg_order_value": total_revenue / len(orders) if orders else 0.0,
            "last_purchase": orders[0].get("createdAt") if orders else None,
            "preferred_categories": list(set(
                item.get("category") for o in orders for item in o.get("items", [])
            )),
        }
    
    def _normalize_social(self, data: dict, weight: float) -> dict:
        return {
            "social_engagement_score": data.get("engagementScore", 0.0),
        }
    
    def _normalize_enrichment(self, data: dict, weight: float) -> dict:
        person = data.get("person", {})
        company = data.get("company", {})
        return {
            "age": person.get("age"),
            "gender": person.get("gender"),
            "location": person.get("location"),
            "industry": company.get("industry"),
            "company_size": company.get("employeesRange"),
            "intent_signals": data.get("intent", {}).get("signals", []),
        }
    
    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()
        for key, value in override.items():
            if value is None:
                continue
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                result[key] = list(set(result[key] + value))
            else:
                result[key] = value
        return result
```

### 2.5 Data Quality Validation

```python
class DataQualityValidator:
    """Validates customer data quality and completeness."""
    
    def __init__(self):
        self.rules = {
            "email": self._validate_email,
            "phone": self._validate_phone,
            "age": self._validate_age,
            "total_revenue": self._validate_revenue,
        }
    
    def validate(self, profile: UnifiedCustomerProfile) -> dict:
        """Run all validation rules and return quality report.
        
        Returns:
            Dictionary with validation results and quality score
        """
        results = {}
        errors = []
        warnings = []
        
        for field, validator_fn in self.rules.items():
            value = getattr(profile, field, None)
            is_valid, message = validator_fn(value)
            results[field] = {"valid": is_valid, "message": message}
            if not is_valid:
                if value is None:
                    warnings.append(f"{field}: missing")
                else:
                    errors.append(f"{field}: {message}")
        
        # Completeness check
        critical_fields = ["email", "first_name", "last_name"]
        missing_critical = [f for f in critical_fields if not getattr(profile, f)]
        
        # Consistency checks
        if profile.total_orders > 0 and profile.total_revenue == 0:
            warnings.append("Has orders but zero revenue - data inconsistency")
        
        if profile.email_engagement_rate > 1.0:
            errors.append("Email engagement rate exceeds 100%")
        
        quality_score = self._compute_quality_score(profile, errors, warnings)
        
        return {
            "is_valid": len(errors) == 0,
            "quality_score": quality_score,
            "errors": errors,
            "warnings": warnings,
            "missing_critical_fields": missing_critical,
            "field_results": results,
        }
    
    def _validate_email(self, email: Optional[str]) -> tuple[bool, str]:
        if not email:
            return True, "Email not provided"
        if "@" not in email or "." not in email.split("@")[-1]:
            return False, "Invalid email format"
        return True, "Valid"
    
    def _validate_phone(self, phone: Optional[str]) -> tuple[bool, str]:
        if not phone:
            return True, "Phone not provided"
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 10:
            return False, "Phone number too short"
        return True, "Valid"
    
    def _validate_age(self, age: Optional[int]) -> tuple[bool, str]:
        if age is None:
            return True, "Age not provided"
        if age < 13:
            return False, "Age below 13 - COPPA compliance issue"
        if age > 120:
            return False, "Invalid age"
        return True, "Valid"
    
    def _validate_revenue(self, revenue: float) -> tuple[bool, str]:
        if revenue < 0:
            return False, "Negative revenue"
        return True, "Valid"
    
    def _compute_quality_score(self, profile: UnifiedCustomerProfile, 
                                errors: list, warnings: list) -> float:
        """Compute overall quality score (0-100)."""
        base_score = profile.profile_completeness * 100
        error_penalty = len(errors) * 10
        warning_penalty = len(warnings) * 3
        return max(0.0, base_score - error_penalty - warning_penalty)
```

---

## 3. Analysis Agent Implementation

### 3.1 Purpose

The Analysis Agent processes unified customer profiles to identify behavioral patterns, segment customers, predict future actions, and generate actionable insights that feed into the personalization pipeline.

### 3.2 Analysis Capabilities

| Capability | Technique | Output |
|-----------|-----------|--------|
| **Segmentation** | K-Means / DBSCAN clustering | Customer segments with labels |
| **Churn Prediction** | Gradient Boosting / Neural Network | Churn risk score (0-1) |
| **LTV Prediction** | Regression models | Predicted lifetime value |
| **Next Best Action** | Reinforcement Learning | Recommended action per customer |
| **Sentiment Analysis** | Fine-tuned LLM | Sentiment score per interaction |
| **Intent Classification** | LLM-based classification | Purchase intent signals |
| **Lookalike Modeling** | Embedding similarity | Similar customer profiles |
| **Trend Detection** | Time-series analysis | Emerging behavior patterns |

### 3.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
from typing import Literal

# ─── Analysis Tools ───────────────────────────────────────────────────

@tool
def segment_customers(profiles: list[dict], n_segments: int = 5) -> list[dict]:
    """Segment customers using K-Means clustering on behavioral features.
    
    Args:
        profiles: List of customer profile dictionaries
        n_segments: Number of segments to create
    
    Returns:
        List of segment assignments with labels and characteristics
    """
    # Extract features for clustering
    feature_matrix = []
    for profile in profiles:
        features = [
            profile.get("total_sessions", 0),
            profile.get("total_page_views", 0),
            profile.get("avg_session_duration", 0),
            profile.get("email_engagement_rate", 0),
            profile.get("total_orders", 0),
            profile.get("total_revenue", 0),
            profile.get("avg_order_value", 0),
            profile.get("social_engagement_score", 0),
        ]
        feature_matrix.append(features)
    
    X = np.array(feature_matrix)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=n_segments, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    # Generate segment descriptions
    segments = []
    for i in range(n_segments):
        segment_profiles = [p for p, l in zip(profiles, labels) if l == i]
        segment_size = len(segment_profiles)
        avg_revenue = np.mean([p.get("total_revenue", 0) for p in segment_profiles])
        avg_orders = np.mean([p.get("total_orders", 0) for p in segment_profiles])
        avg_engagement = np.mean([p.get("email_engagement_rate", 0) for p in segment_profiles])
        
        # Auto-label segment based on characteristics
        label = _auto_label_segment(avg_revenue, avg_orders, avg_engagement)
        
        segments.append({
            "segment_id": i,
            "label": label,
            "size": segment_size,
            "percentage": segment_size / len(profiles) * 100,
            "avg_revenue": float(avg_revenue),
            "avg_orders": float(avg_orders),
            "avg_engagement": float(avg_engagement),
            "characteristics": _extract_segment_characteristics(segment_profiles),
            "customer_ids": [p["customer_id"] for p in segment_profiles],
        })
    
    return segments


@tool
def predict_churn_risk(customer_profile: dict) -> dict:
    """Predict churn risk for a customer using behavioral signals.
    
    Args:
        customer_profile: Unified customer profile dictionary
    
    Returns:
        Dictionary with churn risk score and contributing factors
    """
    # Feature extraction
    features = {
        "days_since_last_purchase": _days_since(customer_profile.get("last_purchase")),
        "days_since_last_visit": _days_since(customer_profile.get("last_visit")),
        "email_engagement_trend": customer_profile.get("email_engagement_rate", 0),
        "session_frequency_change": _compute_session_trend(customer_profile),
        "support_ticket_count": customer_profile.get("support_tickets", 0),
        "refund_count": customer_profile.get("refund_count", 0),
        "subscription_status": 1 if customer_profile.get("subscription_status") == "active" else 0,
    }
    
    # Rule-based scoring (replace with ML model in production)
    risk_score = 0.0
    factors = []
    
    if features["days_since_last_purchase"] > 90:
        risk_score += 0.3
        factors.append("No purchase in 90+ days")
    elif features["days_since_last_purchase"] > 60:
        risk_score += 0.15
        factors.append("No purchase in 60+ days")
    
    if features["days_since_last_visit"] > 30:
        risk_score += 0.2
        factors.append("No website visit in 30+ days")
    
    if features["email_engagement_trend"] < 0.1:
        risk_score += 0.2
        factors.append("Low email engagement")
    
    if features["refund_count"] > 2:
        risk_score += 0.15
        factors.append("Multiple refunds")
    
    if features["subscription_status"] == 0 and customer_profile.get("total_orders", 0) > 3:
        risk_score += 0.1
        factors.append("Lapsed subscriber with purchase history")
    
    risk_level = "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low"
    
    return {
        "customer_id": customer_profile["customer_id"],
        "churn_risk_score": min(risk_score, 1.0),
        "churn_risk_level": risk_level,
        "contributing_factors": factors,
        "recommended_actions": _get_churn_prevention_actions(risk_level, factors),
    }


@tool
def predict_lifetime_value(customer_profile: dict) -> dict:
    """Predict customer lifetime value.
    
    Args:
        customer_profile: Unified customer profile dictionary
    
    Returns:
        Dictionary with LTV prediction and confidence interval
    """
    # Simplified LTV model (replace with trained model in production)
    avg_order_value = customer_profile.get("avg_order_value", 0)
    purchase_frequency = _estimate_purchase_frequency(customer_profile)
    customer_lifespan = _estimate_customer_lifespan(customer_profile)
    
    predicted_ltv = avg_order_value * purchase_frequency * customer_lifespan
    
    # Adjust based on engagement
    engagement_multiplier = 1 + (customer_profile.get("email_engagement_rate", 0) * 0.5)
    predicted_ltv *= engagement_multiplier
    
    # Confidence interval (simplified)
    confidence = 0.7  # Based on data quality
    margin = predicted_ltv * (1 - confidence)
    
    return {
        "customer_id": customer_profile["customer_id"],
        "predicted_ltv": round(predicted_ltv, 2),
        "confidence_interval": {
            "lower": round(max(0, predicted_ltv - margin), 2),
            "upper": round(predicted_ltv + margin, 2),
        },
        "confidence_score": confidence,
        "factors": {
            "avg_order_value": avg_order_value,
            "purchase_frequency": purchase_frequency,
            "estimated_lifespan_years": customer_lifespan,
            "engagement_multiplier": engagement_multiplier,
        },
    }


@tool
def analyze_behavior_patterns(customer_id: str, events: list[dict]) -> dict:
    """Analyze behavioral patterns from event stream.
    
    Args:
        customer_id: Customer identifier
        events: List of behavioral events
    
    Returns:
        Dictionary with pattern analysis results
    """
    if not events:
        return {"customer_id": customer_id, "patterns": [], "insights": []}
    
    # Time-based patterns
    hourly_distribution = _compute_hourly_distribution(events)
    daily_distribution = _compute_daily_distribution(events)
    
    # Sequence patterns
    common_sequences = _find_common_sequences(events)
    
    # Category affinity
    category_affinity = _compute_category_affinity(events)
    
    # Engagement patterns
    engagement_trend = _compute_engagement_trend(events)
    
    # Generate insights
    insights = []
    
    peak_hour = max(hourly_distribution, key=hourly_distribution.get)
    insights.append(f"Most active at {peak_hour}:00 - optimal send time")
    
    if engagement_trend == "declining":
        insights.append("Engagement declining - re-engagement campaign recommended")
    elif engagement_trend == "increasing":
        insights.append("Engaging increasing - upsell opportunity")
    
    top_category = max(category_affinity, key=category_affinity.get)
    insights.append(f"Highest affinity for {top_category} category")
    
    return {
        "customer_id": customer_id,
        "patterns": {
            "hourly_distribution": hourly_distribution,
            "daily_distribution": daily_distribution,
            "common_sequences": common_sequences,
            "category_affinity": category_affinity,
            "engagement_trend": engagement_trend,
        },
        "insights": insights,
        "optimal_contact_time": f"{peak_hour}:00",
        "preferred_categories": sorted(category_affinity, key=category_affinity.get, reverse=True)[:3],
    }


@tool
def classify_purchase_intent(customer_profile: dict, recent_events: list[dict]) -> dict:
    """Classify purchase intent using LLM-based analysis.
    
    Args:
        customer_profile: Customer profile
        recent_events: Recent behavioral events
    
    Returns:
        Dictionary with intent classification and confidence
    """
    # Prepare context for LLM
    context = _build_intent_context(customer_profile, recent_events)
    
    # Use LLM for intent classification
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    prompt = f"""Analyze the following customer data and classify their purchase intent.
    
Customer Profile:
{json.dumps(customer_profile, indent=2, default=str)}

Recent Events:
{json.dumps(recent_events[-20:], indent=2, default=str)}

Classify intent into one of:
- high_intent: Ready to purchase within 7 days
- medium_intent: Considering purchase within 30 days
- low_intent: Browsing, no immediate purchase intent
- research_phase: Comparing options, gathering information
- post_purchase: Recently purchased, potential for cross-sell

Return JSON with: intent_level, confidence, reasoning, recommended_approach
"""
    response = llm.invoke(prompt)
    return json.loads(response.content)


@tool
def find_lookalike_customers(seed_customer_id: str, candidate_profiles: list[dict], 
                              n_results: int = 50) -> list[dict]:
    """Find lookalike customers using embedding similarity.
    
    Args:
        seed_customer_id: Reference customer
        candidate_profiles: Pool of candidate customers
        n_results: Number of lookalike customers to return
    
    Returns:
        List of lookalike customers with similarity scores
    """
    from langchain_openai import OpenAIEmbeddings
    
    embeddings = OpenAIEmbeddings()
    
    # Create embedding for seed customer
    seed_profile = next((p for p in candidate_profiles if p["customer_id"] == seed_customer_id), None)
    if not seed_profile:
        return []
    
    seed_text = _profile_to_text(seed_profile)
    seed_embedding = embeddings.embed_query(seed_text)
    
    # Compute similarities
    similarities = []
    for profile in candidate_profiles:
        if profile["customer_id"] == seed_customer_id:
            continue
        profile_text = _profile_to_text(profile)
        profile_embedding = embeddings.embed_query(profile_text)
        similarity = np.dot(seed_embedding, profile_embedding) / (
            np.linalg.norm(seed_embedding) * np.linalg.norm(profile_embedding)
        )
        similarities.append({
            "customer_id": profile["customer_id"],
            "similarity_score": float(similarity),
            "profile": profile,
        })
    
    # Sort by similarity and return top N
    similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similarities[:n_results]


# ─── Analysis Agent ───────────────────────────────────────────────────

ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Analysis Agent for a marketing personalization system.

Your responsibility is to analyze customer data and generate actionable insights for
personalization and marketing optimization.

Capabilities:
- Customer segmentation using behavioral and demographic features
- Churn risk prediction and prevention recommendations
- Lifetime value prediction
- Behavioral pattern analysis
- Purchase intent classification
- Lookalike audience discovery

Guidelines:
- Use data-driven approaches, not assumptions
- Provide confidence scores for all predictions
- Explain the reasoning behind each insight
- Flag data quality issues that may affect analysis
- Consider seasonality and temporal patterns
- Respect privacy - use aggregated data where possible

Output structured analysis results with clear, actionable recommendations.
"""),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "{input}"),
])


def create_analysis_agent(llm: Optional[ChatOpenAI] = None) -> AgentExecutor:
    """Create the Analysis Agent.
    
    Returns:
        Configured AgentExecutor for analysis
    """
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [
        segment_customers,
        predict_churn_risk,
        predict_lifetime_value,
        analyze_behavior_patterns,
        classify_purchase_intent,
        find_lookalike_customers,
    ]
    
    agent = create_openai_functions_agent(llm, tools, ANALYSIS_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=15,
        handle_parsing_errors=True,
    )
```

### 3.4 Segmentation Engine

```python
from dataclasses import dataclass, field
from enum import Enum

class SegmentType(str, Enum):
    DEMOGRAPHIC = "demographic"
    BEHAVIORAL = "behavioral"
    VALUE_BASED = "value_based"
    LIFECYCLE = "lifecycle"
    INTENT_BASED = "intent_based"
    CUSTOM = "custom"

@dataclass
class CustomerSegment:
    """Represents a customer segment."""
    segment_id: str
    name: str
    segment_type: SegmentType
    size: int
    percentage: float
    avg_revenue: float
    avg_ltv: float
    churn_risk: str
    characteristics: dict = field(default_factory=dict)
    recommended_strategies: list[str] = field(default_factory=list)
    customer_ids: list[str] = field(default_factory=list)


class SegmentationEngine:
    """Multi-dimensional customer segmentation engine."""
    
    def __init__(self):
        self.segments: dict[str, CustomerSegment] = {}
        self.scaler = StandardScaler()
    
    def create_rfm_segments(self, profiles: list[dict]) -> list[CustomerSegment]:
        """Create RFM (Recency, Frequency, Monetary) segments.
        
        Args:
            profiles: List of customer profiles
        
        Returns:
            List of RFM-based customer segments
        """
        # Compute RFM scores
        rfm_data = []
        for profile in profiles:
            recency = _days_since(profile.get("last_purchase"))
            frequency = profile.get("total_orders", 0)
            monetary = profile.get("total_revenue", 0)
            rfm_data.append({
                "customer_id": profile["customer_id"],
                "recency": recency,
                "frequency": frequency,
                "monetary": monetary,
            })
        
        # Score each dimension (1-5 scale)
        df = pd.DataFrame(rfm_data)
        df["R_score"] = pd.qcut(df["recency"], 5, labels=[5,4,3,2,1])
        df["F_score"] = pd.qcut(df["frequency"].rank(method="first"), 5, labels=[1,2,3,4,5])
        df["M_score"] = pd.qcut(df["monetary"].rank(method="first"), 5, labels=[1,2,3,4,5])
        df["RFM_score"] = df["R_score"].astype(str) + df["F_score"].astype(str) + df["M_score"].astype(str)
        
        # Map RFM scores to named segments
        segment_mapping = {
            "555": ("Champions", "high_value"),
            "554": ("Champions", "high_value"),
            "544": ("Loyal Customers", "high_value"),
            "543": ("Loyal Customers", "high_value"),
            "454": ("Loyal Customers", "high_value"),
            "453": ("Loyal Customers", "high_value"),
            "444": ("Loyal Customers", "high_value"),
            "553": ("Potential Loyalists", "medium_value"),
            "552": ("Potential Loyalists", "medium_value"),
            "551": ("Potential Loyalists", "medium_value"),
            "542": ("Potential Loyalists", "medium_value"),
            "541": ("Potential Loyalists", "medium_value"),
            "452": ("Potential Loyalists", "medium_value"),
            "451": ("Potential Loyalists", "medium_value"),
            "443": ("Potential Loyalists", "medium_value"),
            "442": ("Potential Loyalists", "medium_value"),
            "512": ("New Customers", "new"),
            "511": ("New Customers", "new"),
            "422": ("New Customers", "new"),
            "421": ("New Customers", "new"),
            "412": ("New Customers", "new"),
            "411": ("New Customers", "new"),
            "355": ("At Risk", "at_risk"),
            "354": ("At Risk", "at_risk"),
            "353": ("At Risk", "at_risk"),
            "352": ("At Risk", "at_risk"),
            "351": ("At Risk", "at_risk"),
            "345": ("At Risk", "at_risk"),
            "344": ("At Risk", "at_risk"),
            "343": ("At Risk", "at_risk"),
            "342": ("At Risk", "at_risk"),
            "341": ("At Risk", "at_risk"),
            "255": ("Cannot Lose Them", "critical"),
            "254": ("Cannot Lose Them", "critical"),
            "253": ("Cannot Lose Them", "critical"),
            "252": ("Cannot Lose Them", "critical"),
            "251": ("Cannot Lose Them", "critical"),
            "245": ("Cannot Lose Them", "critical"),
            "244": ("Cannot Lose Them", "critical"),
            "243": ("Cannot Lose Them", "critical"),
            "242": ("Cannot Lose Them", "critical"),
            "241": ("Cannot Lose Them", "critical"),
            "155": ("Hibernating", "low_value"),
            "154": ("Hibernating", "low_value"),
            "153": ("Hibernating", "low_value"),
            "152": ("Hibernating", "low_value"),
            "151": ("Hibernating", "low_value"),
            "145": ("Hibernating", "low_value"),
            "144": ("Hibernating", "low_value"),
            "143": ("Hibernating", "low_value"),
            "142": ("Hibernating", "low_value"),
            "141": ("Hibernating", "low_value"),
            "135": ("Hibernating", "low_value"),
            "134": ("Hibernating", "low_value"),
            "133": ("Hibernating", "low_value"),
            "132": ("Hibernating", "low_value"),
            "131": ("Hibernating", "low_value"),
            "125": ("Hibernating", "low_value"),
            "124": ("Hibernating", "low_value"),
            "123": ("Hibernating", "low_value"),
            "122": ("Hibernating", "low_value"),
            "121": ("Hibernating", "low_value"),
            "115": ("Lost", "lost"),
            "114": ("Lost", "lost"),
            "113": ("Lost", "lost"),
            "112": ("Lost", "lost"),
            "111": ("Lost", "lost"),
        }
        
        segments = []
        for rfm_score, group in df.groupby("RFM_score"):
            name, value_tier = segment_mapping.get(rfm_score, ("Other", "unknown"))
            segment = CustomerSegment(
                segment_id=f"rfm_{rfm_score}",
                name=name,
                segment_type=SegmentType.VALUE_BASED,
                size=len(group),
                percentage=len(group) / len(df) * 100,
                avg_revenue=group["monetary"].mean(),
                avg_ltv=group["monetary"].mean() * 2.5,  # Simplified LTV estimate
                churn_risk="high" if name in ["At Risk", "Cannot Lose Them", "Hibernating"] else "low",
                characteristics={
                    "rfm_score": rfm_score,
                    "avg_recency_days": group["recency"].mean(),
                    "avg_frequency": group["frequency"].mean(),
                    "avg_monetary": group["monetary"].mean(),
                },
                recommended_strategies=_get_strategies_for_segment(name),
                customer_ids=group["customer_id"].tolist(),
            )
            segments.append(segment)
        
        return segments
    
    def create_behavioral_segments(self, profiles: list[dict]) -> list[CustomerSegment]:
        """Create behavioral segments based on engagement patterns."""
        segments = []
        
        # Define behavioral rules
        behavioral_rules = {
            "Engaged Shoppers": lambda p: (
                p.get("total_sessions", 0) > 20 and 
                p.get("email_engagement_rate", 0) > 0.3
            ),
            "Browsers": lambda p: (
                p.get("total_sessions", 0) > 10 and 
                p.get("total_orders", 0) == 0
            ),
            "One-time Buyers": lambda p: (
                p.get("total_orders", 0) == 1 and 
                _days_since(p.get("last_purchase")) > 60
            ),
            "Repeat Customers": lambda p: (
                p.get("total_orders", 0) >= 3
            ),
            "Window Shoppers": lambda p: (
                p.get("total_page_views", 0) > 50 and 
                p.get("total_sessions", 0) < 5
            ),
            "Inactive": lambda p: (
                _days_since(p.get("last_visit")) > 90
            ),
        }
        
        for name, rule in behavioral_rules.items():
            matching = [p for p in profiles if rule(p)]
            if not matching:
                continue
            
            segment = CustomerSegment(
                segment_id=f"behavioral_{name.lower().replace(' ', '_')}",
                name=name,
                segment_type=SegmentType.BEHAVIORAL,
                size=len(matching),
                percentage=len(matching) / len(profiles) * 100,
                avg_revenue=np.mean([p.get("total_revenue", 0) for p in matching]),
                avg_ltv=np.mean([p.get("total_revenue", 0) for p in matching]) * 2,
                churn_risk="high" if name in ["Inactive", "One-time Buyers"] else "low",
                characteristics={
                    "avg_sessions": np.mean([p.get("total_sessions", 0) for p in matching]),
                    "avg_page_views": np.mean([p.get("total_page_views", 0) for p in matching]),
                    "avg_orders": np.mean([p.get("total_orders", 0) for p in matching]),
                },
                recommended_strategies=_get_behavioral_strategies(name),
                customer_ids=[p["customer_id"] for p in matching],
            )
            segments.append(segment)
        
        return segments
```

---

## 4. Personalization Agent Implementation

### 4.1 Purpose

The Personalization Agent generates tailored marketing content, product recommendations, and personalized offers for individual customers or segments. It leverages the insights from the Analysis Agent to create contextually relevant messaging.

### 4.2 Personalization Dimensions

| Dimension | Description | Example |
|-----------|-------------|---------|
| **Content** | Tailored copy, images, and CTAs | "Hi Sarah, check out these running shoes" |
| **Offer** | Personalized discounts and promotions | 15% off for loyal customers |
| **Product** | Relevant product recommendations | Based on browsing history |
| **Channel** | Preferred communication channel | Email vs. push vs. SMS |
| **Timing** | Optimal send time | Based on engagement patterns |
| **Frequency** | Communication cadence | Avoid over-messaging |
| **Tone** | Communication style | Formal vs. casual |
| **Format** | Content format preference | Video vs. text vs. interactive |

### 4.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings

# ─── Personalization Tools ────────────────────────────────────────────

@tool
def generate_personalized_email(customer_profile: dict, segment: dict, 
                                  intent: dict, context: dict) -> dict:
    """Generate a personalized email for a customer.
    
    Args:
        customer_profile: Customer profile data
        segment: Customer segment information
        intent: Purchase intent analysis
        context: Additional context (campaign, season, etc.)
    
    Returns:
        Dictionary with email subject, body, and metadata
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)
    
    prompt = f"""Create a personalized marketing email for the following customer.

Customer Profile:
- Name: {customer_profile.get('first_name', 'Valued Customer')}
- Segment: {segment.get('label', 'General')}
- Purchase History: {customer_profile.get('total_orders', 0)} orders, ${customer_profile.get('total_revenue', 0):.2f} total
- Preferred Categories: {', '.join(customer_profile.get('preferred_categories', []))}
- Last Purchase: {customer_profile.get('last_purchase', 'N/A')}
- Email Engagement Rate: {customer_profile.get('email_engagement_rate', 0):.1%}

Intent Analysis:
- Intent Level: {intent.get('intent_level', 'unknown')}
- Recommended Approach: {intent.get('recommended_approach', 'general promotion')}

Campaign Context:
- Campaign Type: {context.get('campaign_type', 'general')}
- Season: {context.get('season', 'all_year')}
- Special Events: {context.get('special_events', [])}

Requirements:
- Subject line: Max 60 characters, personalized, compelling
- Body: 150-300 words, conversational tone, clear CTA
- Include personalized product recommendations if relevant
- Match tone to customer segment
- Include dynamic content blocks based on preferences
- Mobile-friendly format

Return JSON with: subject, preheader, body_html, body_text, cta_text, cta_url, personalization_score
"""
    
    response = llm.invoke(prompt)
    return json.loads(response.content)


@tool
def generate_product_recommendations(customer_profile: dict, 
                                      n_recommendations: int = 5) -> list[dict]:
    """Generate personalized product recommendations.
    
    Args:
        customer_profile: Customer profile data
        n_recommendations: Number of recommendations to generate
    
    Returns:
        List of product recommendations with scores and reasoning
    """
    # Build query from customer preferences
    query_parts = []
    if customer_profile.get("preferred_categories"):
        query_parts.extend(customer_profile["preferred_categories"])
    if customer_profile.get("intent_signals"):
        query_parts.extend(customer_profile["intent_signals"])
    
    query = " ".join(query_parts) if query_parts else "popular products"
    
    # Search vector store for similar products
    embeddings = OpenAIEmbeddings()
    vectorstore = Pinecone.from_existing_index(
        index_name=PINECONE_INDEX_NAME,
        embedding=embeddings
    )
    
    results = vectorstore.similarity_search_with_score(
        query, k=n_recommendations * 2  # Get extra for filtering
    )
    
    # Filter and rank recommendations
    recommendations = []
    seen_products = set()
    
    for doc, score in results:
        product_id = doc.metadata.get("product_id")
        if product_id in seen_products:
            continue
        seen_products.add(product_id)
        
        # Compute personalization score
        personalization_score = _compute_personalization_score(
            doc.metadata, customer_profile, score
        )
        
        recommendations.append({
            "product_id": product_id,
            "product_name": doc.metadata.get("name"),
            "category": doc.metadata.get("category"),
            "price": doc.metadata.get("price"),
            "image_url": doc.metadata.get("image_url"),
            "personalization_score": personalization_score,
            "reasoning": _generate_recommendation_reasoning(doc.metadata, customer_profile),
            "confidence": score,
        })
        
        if len(recommendations) >= n_recommendations:
            break
    
    return recommendations


@tool
def personalize_landing_page(customer_profile: dict, page_config: dict) -> dict:
    """Generate personalized landing page configuration.
    
    Args:
        customer_profile: Customer profile data
        page_config: Base page configuration
    
    Returns:
        Dictionary with personalized page elements
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0.5)
    
    prompt = f"""Personalize a landing page for the following customer.

Customer Profile:
{json.dumps(customer_profile, indent=2, default=str)}

Base Page Configuration:
{json.dumps(page_config, indent=2, default=str)}

Generate personalized:
1. Hero section (headline, subheadline, image selection)
2. Product showcase (which products to feature)
3. Social proof (testimonials relevant to customer)
4. CTA (text, color, placement)
5. Trust badges and guarantees
6. Dynamic content blocks

Consider:
- Customer's browsing history and preferences
- Segment-specific messaging
- Intent level and stage in funnel
- Past purchase behavior
- Device type (mobile vs desktop)

Return JSON with all personalized elements.
"""
    
    response = llm.invoke(prompt)
    return json.loads(response.content)


@tool
def generate_push_notification(customer_profile: dict, campaign: dict) -> dict:
    """Generate a personalized push notification.
    
    Args:
        customer_profile: Customer profile data
        campaign: Campaign configuration
    
    Returns:
        Dictionary with push notification content
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)
    
    prompt = f"""Create a personalized push notification.

Customer: {customer_profile.get('first_name', 'there')}
Segment: {customer_profile.get('segment', 'general')}
Campaign: {campaign.get('name', 'Special Offer')}
Key Message: {campaign.get('key_message', 'Check out our latest deals!')}

Requirements:
- Title: Max 40 characters
- Body: Max 100 characters
- Include personalization element
- Clear, actionable language
- Urgency without being pushy
- Deep link to relevant page

Return JSON with: title, body, deep_link, image_url, action_buttons
"""
    
    response = llm.invoke(prompt)
    return json.loads(response.content)


@tool
def generate_sms_message(customer_profile: dict, offer: dict) -> dict:
    """Generate a personalized SMS message.
    
    Args:
        customer_profile: Customer profile data
        offer: Offer details
    
    Returns:
        Dictionary with SMS content
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0.7)
    
    prompt = f"""Create a personalized SMS message.

Customer: {customer_profile.get('first_name', 'there')}
Offer: {offer.get('description', 'Special discount')}
Discount: {offer.get('discount_percentage', 10)}%
Code: {offer.get('code', 'SAVE10')}
Expiry: {offer.get('expiry_date', 'limited time')}

Requirements:
- Max 160 characters (single SMS)
- Include personalized element
- Clear CTA with link
- Include opt-out language
- Urgency without spam

Return JSON with: message, short_url, character_count
"""
    
    response = llm.invoke(prompt)
    return json.loads(response.content)


@tool
def create_dynamic_content_blocks(customer_profile: dict, 
                                   block_types: list[str]) -> list[dict]:
    """Create dynamic content blocks for web/email personalization.
    
    Args:
        customer_profile: Customer profile data
        block_types: Types of content blocks to generate
    
    Returns:
        List of content block configurations
    """
    blocks = []
    
    for block_type in block_types:
        if block_type == "hero_banner":
            blocks.append(_generate_hero_banner(customer_profile))
        elif block_type == "product_carousel":
            blocks.append(_generate_product_carousel(customer_profile))
        elif block_type == "testimonial":
            blocks.append(_generate_testimonial(customer_profile))
        elif block_type == "countdown_timer":
            blocks.append(_generate_countdown_timer(customer_profile))
        elif block_type == "social_proof":
            blocks.append(_generate_social_proof(customer_profile))
        elif block_type == "recommendation_engine":
            blocks.append(_generate_recommendation_block(customer_profile))
    
    return blocks


# ─── Personalization Agent ────────────────────────────────────────────

PERSONALIZATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Personalization Agent for a marketing personalization system.

Your responsibility is to generate personalized marketing content, recommendations, and
experiences tailored to individual customers.

Capabilities:
- Personalized email generation
- Product recommendations
- Landing page personalization
- Push notification creation
- SMS message generation
- Dynamic content blocks

Guidelines:
- Always personalize based on available customer data
- Respect customer preferences and consent
- Maintain brand voice while personalizing
- Include clear, compelling CTAs
- Optimize for the customer's preferred channel
- Consider the customer's stage in the journey
- Avoid over-personalization that feels invasive
- Ensure accessibility in all content
- Test different personalization strategies

Output structured content ready for delivery through appropriate channels.
"""),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "{input}"),
])


def create_personalization_agent(llm: Optional[ChatOpenAI] = None) -> AgentExecutor:
    """Create the Personalization Agent.
    
    Returns:
        Configured AgentExecutor for personalization
    """
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0.7)
    
    tools = [
        generate_personalized_email,
        generate_product_recommendations,
        personalize_landing_page,
        generate_push_notification,
        generate_sms_message,
        create_dynamic_content_blocks,
    ]
    
    agent = create_openai_functions_agent(llm, tools, PERSONALIZATION_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=12,
        handle_parsing_errors=True,
    )
```

### 4.4 Content Personalization Engine

```python
class ContentPersonalizationEngine:
    """Engine for generating personalized content at scale."""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)
        self.embeddings = OpenAIEmbeddings()
        self.template_cache = {}
    
    def personalize_content(self, template: str, customer_profile: dict, 
                            variables: dict) -> str:
        """Personalize a content template with customer data.
        
        Args:
            template: Content template with placeholders
            customer_profile: Customer profile data
            variables: Additional template variables
        
        Returns:
            Personalized content string
        """
        # Build variable context
        context = {
            "first_name": customer_profile.get("first_name", "there"),
            "last_name": customer_profile.get("last_name", ""),
            "full_name": customer_profile.get("full_name", "Valued Customer"),
            "email": customer_profile.get("email", ""),
            "last_purchase_date": customer_profile.get("last_purchase", ""),
            "total_orders": customer_profile.get("total_orders", 0),
            "total_revenue": customer_profile.get("total_revenue", 0),
            "preferred_categories": ", ".join(customer_profile.get("preferred_categories", [])),
            "segment": customer_profile.get("segment", "general"),
            **variables,
        }
        
        # Use LLM for advanced personalization
        prompt = f"""Personalize the following content template using the customer context.

Template:
{template}

Customer Context:
{json.dumps(context, indent=2, default=str)}

Rules:
- Replace all {{variable}} placeholders with actual values
- Adjust tone based on customer segment
- Add personalization elements where natural
- Keep the core message intact
- Ensure the content feels personal, not generic
- Max length: 500 words

Return only the personalized content, no explanations.
"""
        
        response = self.llm.invoke(prompt)
        return response.content.strip()
    
    def generate_ab_test_variants(self, base_content: dict, 
                                   n_variants: int = 3) -> list[dict]:
        """Generate A/B test variants for content.
        
        Args:
            base_content: Base content configuration
            n_variants: Number of variants to generate
        
        Returns:
            List of content variants
        """
        variants = []
        
        for i in range(n_variants):
            llm = ChatOpenAI(model="gpt-4", temperature=0.7 + (i * 0.1))
            
            prompt = f"""Create variant {i+1} of the following marketing content for A/B testing.

Base Content:
{json.dumps(base_content, indent=2, default=str)}

Variant {i+1} Strategy:
{_get_ab_test_strategy(i)}

Requirements:
- Change one key element (headline, CTA, image, offer, or tone)
- Keep other elements consistent
- Make the variant meaningfully different
- Ensure it's still on-brand

Return JSON with: variant_id, subject, body, cta_text, strategy_description
"""
            
            response = llm.invoke(prompt)
            variant = json.loads(response.content)
            variant["variant_id"] = f"variant_{i+1}"
            variants.append(variant)
        
        return variants
    
    def _get_ab_test_strategy(self, variant_index: int) -> str:
        """Get A/B test strategy for a variant."""
        strategies = [
            "Focus on emotional appeal and storytelling",
            "Focus on rational benefits and data-driven messaging",
            "Focus on urgency and scarcity",
            "Focus on social proof and community",
            "Focus on personalization and relevance",
        ]
        return strategies[variant_index % len(strategies)]
    
    def score_personalization(self, content: dict, customer_profile: dict) -> float:
        """Score how well content is personalized for a customer.
        
        Args:
            content: Content to score
            customer_profile: Customer profile
        
        Returns:
            Personalization score (0-1)
        """
        score = 0.0
        checks = 0
        
        # Check name personalization
        if customer_profile.get("first_name") and customer_profile["first_name"] in str(content):
            score += 0.2
        checks += 1
        
        # Check segment-specific content
        if customer_profile.get("segment") and customer_profile["segment"] in str(content):
            score += 0.15
        checks += 1
        
        # Check category relevance
        preferred_categories = customer_profile.get("preferred_categories", [])
        if any(cat in str(content) for cat in preferred_categories):
            score += 0.2
        checks += 1
        
        # Check purchase history reference
        if customer_profile.get("total_orders", 0) > 0 and "order" in str(content).lower():
            score += 0.15
        checks += 1
        
        # Check location personalization
        if customer_profile.get("location") and str(customer_profile["location"]) in str(content):
            score += 0.1
        checks += 1
        
        # Check behavioral reference
        if customer_profile.get("last_purchase") and "recent" in str(content).lower():
            score += 0.1
        checks += 1
        
        # Check dynamic content blocks
        if "dynamic_blocks" in content:
            score += 0.1
        checks += 1
        
        return score / checks if checks > 0 else 0.0
```

---

## 5. Optimization Agent Implementation

### 5.1 Purpose

The Optimization Agent continuously improves marketing performance by running A/B tests, optimizing send times, selecting best channels, and refining targeting strategies based on real-time performance data.

### 5.2 Optimization Capabilities

| Capability | Description | Method |
|-----------|-------------|--------|
| **A/B Testing** | Test content variants | Multi-armed bandit |
| **Send Time Optimization** | Find optimal send times | Engagement pattern analysis |
| **Channel Optimization** | Select best channel per customer | Preference + performance modeling |
| **Frequency Capping** | Prevent over-messaging | Fatigue modeling |
| **Budget Allocation** | Distribute budget across campaigns | Linear programming |
| **Audience Optimization** | Refine targeting | Lookalike expansion |
| **Creative Optimization** | Improve creative elements | Automated creative testing |
| **Funnel Optimization** | Reduce drop-off | Funnel analysis |

### 5.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from scipy import stats
import numpy as np

# ─── Optimization Tools ───────────────────────────────────────────────

@tool
def run_ab_test(campaign_id: str, variants: list[dict], 
                sample_size: int = 1000, confidence_level: float = 0.95) -> dict:
    """Run an A/B test for campaign variants.
    
    Args:
        campaign_id: Campaign identifier
        variants: List of content variants to test
        sample_size: Number of customers per variant
        confidence_level: Statistical confidence level
    
    Returns:
        Dictionary with test results and winner
    """
    results = {
        "campaign_id": campaign_id,
        "test_id": f"ab_{campaign_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "variants": [],
        "winner": None,
        "confidence_level": confidence_level,
        "sample_size_per_variant": sample_size,
        "status": "running",
    }
    
    for i, variant in enumerate(variants):
        # Simulate or fetch real test data
        variant_results = _simulate_ab_test_data(variant, sample_size)
        
        results["variants"].append({
            "variant_id": variant.get("variant_id", f"variant_{i}"),
            "content": variant,
            "metrics": variant_results,
            "confidence_interval": _compute_confidence_interval(
                variant_results, confidence_level
            ),
        })
    
    # Determine winner using statistical significance
    winner = _determine_ab_winner(results["variants"], confidence_level)
    results["winner"] = winner
    results["status"] = "completed" if winner else "inconclusive"
    
    return results


@tool
def optimize_send_time(customer_id: str, historical_engagement: list[dict]) -> dict:
    """Determine optimal send time for a customer.
    
    Args:
        customer_id: Customer identifier
        historical_engagement: Historical engagement data
    
    Returns:
        Dictionary with optimal send time and confidence
    """
    if not historical_engagement:
        return {
            "customer_id": customer_id,
            "optimal_send_time": "10:00",
            "optimal_send_day": "Tuesday",
            "confidence": 0.5,
            "reasoning": "Default - no historical data available",
        }
    
    # Analyze engagement by hour and day
    hourly_engagement = defaultdict(list)
    daily_engagement = defaultdict(list)
    
    for event in historical_engagement:
        timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        hour = timestamp.hour
        day = timestamp.strftime("%A")
        
        engagement_value = _compute_engagement_value(event)
        hourly_engagement[hour].append(engagement_value)
        daily_engagement[day].append(engagement_value)
    
    # Find optimal hour
    hourly_avg = {h: np.mean(v) for h, v in hourly_engagement.items() if v}
    optimal_hour = max(hourly_avg, key=hourly_avg.get) if hourly_avg else 10
    
    # Find optimal day
    daily_avg = {d: np.mean(v) for d, v in daily_engagement.items() if v}
    optimal_day = max(daily_avg, key=daily_avg.get) if daily_avg else "Tuesday"
    
    # Compute confidence based on data volume
    total_events = len(historical_engagement)
    confidence = min(0.95, 0.3 + (total_events / 100) * 0.65)
    
    return {
        "customer_id": customer_id,
        "optimal_send_time": f"{optimal_hour:02d}:00",
        "optimal_send_day": optimal_day,
        "confidence": confidence,
        "hourly_engagement": hourly_avg,
        "daily_engagement": daily_avg,
        "total_events_analyzed": total_events,
        "reasoning": f"Based on {total_events} engagement events, "
                     f"peak engagement at {optimal_hour}:00 on {optimal_day}",
    }


@tool
def optimize_channel_selection(customer_profile: dict, 
                                channel_performance: dict) -> dict:
    """Select optimal communication channel for a customer.
    
    Args:
        customer_profile: Customer profile data
        channel_performance: Historical channel performance data
    
    Returns:
        Dictionary with recommended channel and alternatives
    """
    # Channel scoring factors
    channel_scores = {}
    
    for channel, performance in channel_performance.items():
        score = 0.0
        
        # Factor 1: Historical engagement rate (40% weight)
        engagement_rate = performance.get("engagement_rate", 0)
        score += engagement_rate * 0.4
        
        # Factor 2: Customer preference match (25% weight)
        preferred_channels = customer_profile.get("preferred_channels", [])
        if channel in preferred_channels:
            score += 0.25
        
        # Factor 3: Channel reachability (20% weight)
        reachable = _check_channel_reachability(customer_profile, channel)
        score += (1.0 if reachable else 0.0) * 0.2
        
        # Factor 4: Cost efficiency (15% weight)
        cost = performance.get("cost_per_message", 1.0)
        max_cost = max(p.get("cost_per_message", 1.0) for p in channel_performance.values())
        cost_efficiency = 1.0 - (cost / max_cost) if max_cost > 0 else 0.5
        score += cost_efficiency * 0.15
        
        channel_scores[channel] = score
    
    # Sort channels by score
    sorted_channels = sorted(channel_scores.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "customer_id": customer_profile["customer_id"],
        "recommended_channel": sorted_channels[0][0] if sorted_channels else "email",
        "channel_scores": dict(sorted_channels),
        "alternatives": [ch for ch, _ in sorted_channels[1:3]],
        "reasoning": _generate_channel_reasoning(sorted_channels, customer_profile),
    }


@tool
def optimize_frequency_cap(customer_profile: dict, 
                           engagement_history: list[dict]) -> dict:
    """Determine optimal communication frequency for a customer.
    
    Args:
        customer_profile: Customer profile data
        engagement_history: Historical engagement data
    
    Returns:
        Dictionary with frequency cap recommendations
    """
    # Analyze engagement decay with frequency
    messages_per_week = _compute_message_frequency(engagement_history)
    engagement_rates = _compute_engagement_by_frequency(engagement_history)
    
    # Find optimal frequency (highest engagement without fatigue)
    optimal_frequency = _find_optimal_frequency(engagement_rates)
    
    # Adjust based on customer segment
    segment = customer_profile.get("segment", "general")
    segment_multiplier = {
        "Champions": 1.5,
        "Loyal Customers": 1.3,
        "Potential Loyalists": 1.0,
        "New Customers": 0.8,
        "At Risk": 0.5,
        "Cannot Lose Them": 0.3,
        "Hibernating": 0.2,
        "Lost": 0.1,
    }.get(segment, 1.0)
    
    adjusted_frequency = optimal_frequency * segment_multiplier
    
    return {
        "customer_id": customer_profile["customer_id"],
        "max_messages_per_week": round(adjusted_frequency, 1),
        "max_messages_per_month": round(adjusted_frequency * 4, 0),
        "optimal_frequency": optimal_frequency,
        "segment_adjustment": segment_multiplier,
        "fatigue_risk": "high" if messages_per_week > adjusted_frequency * 1.5 else "low",
        "recommendation": _generate_frequency_recommendation(
            adjusted_frequency, messages_per_week, segment
        ),
    }


@tool
def optimize_budget_allocation(campaigns: list[dict], total_budget: float) -> dict:
    """Optimize budget allocation across campaigns.
    
    Args:
        campaigns: List of campaign configurations
        total_budget: Total available budget
    
    Returns:
        Dictionary with optimized budget allocation
    """
    # Simple linear programming approach
    # Maximize: sum(roi_i * budget_i)
    # Subject to: sum(budget_i) <= total_budget
    #             budget_i >= min_budget_i
    
    from scipy.optimize import linprog
    
    n = len(campaigns)
    
    # Objective: minimize negative ROI (equivalent to maximizing ROI)
    c = [-c.get("expected_roi", 1.0) for c in campaigns]
    
    # Constraints
    A_ub = [[1] * n]  # Total budget constraint
    b_ub = [total_budget]
    
    # Bounds: min and max budget per campaign
    bounds = []
    for c in campaigns:
        min_budget = c.get("min_budget", 0)
        max_budget = c.get("max_budget", total_budget)
        bounds.append((min_budget, max_budget))
    
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    
    if result.success:
        allocation = {
            campaigns[i]["campaign_id"]: {
                "allocated_budget": round(result.x[i], 2),
                "expected_roi": campaigns[i].get("expected_roi", 1.0),
                "expected_return": round(result.x[i] * campaigns[i].get("expected_roi", 1.0), 2),
            }
            for i in range(n)
        }
        
        return {
            "total_budget": total_budget,
            "allocation": allocation,
            "total_expected_return": round(-result.fun, 2),
            "optimization_success": True,
        }
    else:
        # Fallback: equal allocation
        equal_budget = total_budget / n
        return {
            "total_budget": total_budget,
            "allocation": {
                c["campaign_id"]: {"allocated_budget": round(equal_budget, 2)}
                for c in campaigns
            },
            "optimization_success": False,
            "fallback_reason": result.message,
        }


@tool
def multi_armed_bandit_optimization(arm_performance: list[dict], 
                                    exploration_factor: float = 0.1) -> dict:
    """Optimize content selection using multi-armed bandit.
    
    Args:
        arm_performance: Performance data for each variant (arm)
        exploration_factor: Exploration rate (epsilon)
    
    Returns:
        Dictionary with selection probabilities and recommended arm
    """
    # Thompson Sampling approach
    selections = {}
    total_rewards = {}
    total_pulls = {}
    
    for arm in arm_performance:
        arm_id = arm["arm_id"]
        rewards = arm.get("rewards", [])
        pulls = arm.get("pulls", 0)
        
        total_pulls[arm_id] = pulls
        total_rewards[arm_id] = sum(rewards) if rewards else 0
    
    # Compute Beta distribution parameters for each arm
    beta_params = {}
    for arm in arm_performance:
        arm_id = arm["arm_id"]
        successes = total_rewards[arm_id]
        failures = total_pulls[arm_id] - successes
        beta_params[arm_id] = (successes + 1, failures + 1)  # Laplace smoothing
    
    # Sample from Beta distributions
    samples = {}
    for arm_id, (alpha, beta) in beta_params.items():
        samples[arm_id] = np.random.beta(alpha, beta)
    
    # Select best arm
    best_arm = max(samples, key=samples.get)
    
    # Compute selection probabilities
    total_samples = sum(samples.values())
    probabilities = {arm_id: s / total_samples for arm_id, s in samples.items()}
    
    return {
        "recommended_arm": best_arm,
        "selection_probabilities": probabilities,
        "expected_rewards": {
            arm_id: total_rewards[arm_id] / total_pulls[arm_id] 
            if total_pulls[arm_id] > 0 else 0
            for arm_id in total_rewards
        },
        "exploration_factor": exploration_factor,
        "confidence": samples[best_arm] / total_samples if total_samples > 0 else 0,
    }


# ─── Optimization Agent ───────────────────────────────────────────────

OPTIMIZATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Optimization Agent for a marketing personalization system.

Your responsibility is to continuously optimize marketing performance through
data-driven experimentation and refinement.

Capabilities:
- A/B testing and variant selection
- Send time optimization
- Channel selection optimization
- Frequency capping and fatigue management
- Budget allocation across campaigns
- Multi-armed bandit optimization
- Funnel optimization

Guidelines:
- Use statistical methods for decision making
- Balance exploration and exploitation
- Consider long-term customer value, not just short-term metrics
- Respect customer preferences and avoid over-messaging
- Document all experiments and results
- Automate optimization where possible
- Flag when human review is needed

Output structured optimization recommendations with clear reasoning.
"""),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "{input}"),
])


def create_optimization_agent(llm: Optional[ChatOpenAI] = None) -> AgentExecutor:
    """Create the Optimization Agent.
    
    Returns:
        Configured AgentExecutor for optimization
    """
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [
        run_ab_test,
        optimize_send_time,
        optimize_channel_selection,
        optimize_frequency_cap,
        optimize_budget_allocation,
        multi_armed_bandit_optimization,
    ]
    
    agent = create_openai_functions_agent(llm, tools, OPTIMIZATION_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=15,
        handle_parsing_errors=True,
    )
```

### 5.4 A/B Testing Framework

```python
@dataclass
class ABTestConfig:
    """Configuration for an A/B test."""
    test_id: str
    campaign_id: str
    variants: list[str]
    sample_size_per_variant: int
    confidence_level: float = 0.95
    min_detectable_effect: float = 0.05
    max_duration_days: int = 14
    primary_metric: str = "conversion_rate"
    secondary_metrics: list[str] = field(default_factory=lambda: [
        "open_rate", "click_rate", "revenue_per_customer"
    ])


class ABTestingFramework:
    """Framework for running and managing A/B tests."""
    
    def __init__(self):
        self.active_tests: dict[str, ABTestConfig] = {}
        self.test_results: dict[str, dict] = {}
    
    def create_test(self, config: ABTestConfig) -> dict:
        """Create a new A/B test.
        
        Args:
            config: Test configuration
        
        Returns:
            Test creation result
        """
        # Validate configuration
        if len(config.variants) < 2:
            return {"error": "At least 2 variants required"}
        
        if config.sample_size_per_variant < 100:
            return {"error": "Sample size too small for statistical significance"}
        
        # Compute required sample size
        required_sample = self._compute_required_sample_size(
            config.confidence_level,
            config.min_detectable_effect,
        )
        
        if config.sample_size_per_variant < required_sample:
            return {
                "warning": f"Sample size may be insufficient. Recommended: {required_sample}",
                "proceed": True,
            }
        
        self.active_tests[config.test_id] = config
        
        return {
            "test_id": config.test_id,
            "status": "created",
            "variants": config.variants,
            "sample_size_per_variant": config.sample_size_per_variant,
            "required_sample_size": required_sample,
            "estimated_duration_days": config.max_duration_days,
        }
    
    def analyze_results(self, test_id: str, data: dict) -> dict:
        """Analyze A/B test results.
        
        Args:
            test_id: Test identifier
            data: Test data with metrics per variant
        
        Returns:
            Analysis results with winner and statistical significance
        """
        if test_id not in self.active_tests:
            return {"error": "Test not found"}
        
        config = self.active_tests[test_id]
        variants = data.get("variants", {})
        
        if len(variants) < 2:
            return {"error": "Insufficient variant data"}
        
        # Compute metrics for each variant
        variant_metrics = {}
        for variant_id, metrics in variants.items():
            variant_metrics[variant_id] = {
                "sample_size": metrics.get("sample_size", 0),
                "conversions": metrics.get("conversions", 0),
                "conversion_rate": metrics.get("conversion_rate", 0),
                "revenue": metrics.get("revenue", 0),
                "revenue_per_customer": metrics.get("revenue_per_customer", 0),
                "open_rate": metrics.get("open_rate", 0),
                "click_rate": metrics.get("click_rate", 0),
            }
        
        # Statistical significance test (chi-squared for conversion rate)
        control_id = config.variants[0]
        control = variant_metrics.get(control_id, {})
        
        results = {
            "test_id": test_id,
            "control_variant": control_id,
            "variants": variant_metrics,
            "comparisons": [],
            "winner": None,
            "is_significant": False,
            "recommendation": None,
        }
        
        for variant_id in config.variants[1:]:
            treatment = variant_metrics.get(variant_id, {})
            
            # Chi-squared test for conversion rate
            chi2, p_value = self._chi_squared_test(
                control.get("conversions", 0),
                control.get("sample_size", 0),
                treatment.get("conversions", 0),
                treatment.get("sample_size", 0),
            )
            
            # Effect size
            effect_size = (
                treatment.get("conversion_rate", 0) - control.get("conversion_rate", 0)
            )
            
            comparison = {
                "variant_id": variant_id,
                "vs_control": control_id,
                "effect_size": effect_size,
                "relative_lift": (
                    effect_size / control.get("conversion_rate", 1)
                    if control.get("conversion_rate", 0) > 0 else 0
                ),
                "p_value": p_value,
                "is_significant": p_value < (1 - config.confidence_level),
                "confidence_interval": self._compute_effect_ci(
                    control, treatment, config.confidence_level
                ),
            }
            
            results["comparisons"].append(comparison)
        
        # Determine winner
        significant_winners = [
            c for c in results["comparisons"]
            if c["is_significant"] and c["effect_size"] > 0
        ]
        
        if significant_winners:
            best = max(significant_winners, key=lambda x: x["effect_size"])
            results["winner"] = best["variant_id"]
            results["is_significant"] = True
            results["recommendation"] = (
                f"Variant {best['variant_id']} is the winner with "
                f"{best['relative_lift']:.1%} lift over control "
                f"(p={best['p_value']:.4f})"
            )
        else:
            results["recommendation"] = (
                "No statistically significant winner. "
                "Consider running the test longer or increasing sample size."
            )
        
        self.test_results[test_id] = results
        return results
    
    def _chi_squared_test(self, conv_a: int, n_a: int, 
                          conv_b: int, n_b: int) -> tuple[float, float]:
        """Perform chi-squared test for two proportions."""
        if n_a == 0 or n_b == 0:
            return 0.0, 1.0
        
        # Contingency table
        table = np.array([
            [conv_a, n_a - conv_a],
            [conv_b, n_b - conv_b],
        ])
        
        chi2, p_value, _, _ = stats.chi2_contingency(table, correction=True)
        return chi2, p_value
    
    def _compute_required_sample_size(self, confidence_level: float, 
                                       mde: float, 
                                       baseline_rate: float = 0.05) -> int:
        """Compute required sample size per variant."""
        z_alpha = stats.norm.ppf(1 - (1 - confidence_level) / 2)
        z_beta = stats.norm.ppf(0.8)  # 80% power
        
        p1 = baseline_rate
        p2 = baseline_rate + mde
        
        pooled_p = (p1 + p2) / 2
        
        n = (
            (z_alpha * np.sqrt(2 * pooled_p * (1 - pooled_p)) +
             z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
        ) / (p2 - p1) ** 2
        
        return int(np.ceil(n))
    
    def _compute_effect_ci(self, control: dict, treatment: dict, 
                           confidence: float) -> dict:
        """Compute confidence interval for effect size."""
        p1 = control.get("conversion_rate", 0)
        p2 = treatment.get("conversion_rate", 0)
        n1 = control.get("sample_size", 1)
        n2 = treatment.get("sample_size", 1)
        
        se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        
        effect = p2 - p1
        return {
            "lower": effect - z * se,
            "upper": effect + z * se,
        }
```

---

## 6. Governance Agent Implementation

### 6.1 Purpose

The Governance Agent ensures all marketing activities comply with regulations (GDPR, CCPA, CAN-SPAM), company policies, and ethical standards. It audits content for bias, checks consent status, and maintains an audit trail of all decisions.

### 6.2 Governance Capabilities

| Capability | Description | Regulation |
|-----------|-------------|------------|
| **Consent Management** | Verify customer consent for marketing | GDPR, CCPA |
| **Content Compliance** | Check content against regulations | CAN-SPAM, GDPR, FTC |
| **Bias Detection** | Detect demographic bias in targeting | Ethical AI, ECOA |
| **Data Privacy** | Ensure PII handling compliance | GDPR, CCPA, HIPAA |
| **Frequency Compliance** | Enforce communication limits | CAN-SPAM, TCPA |
| **Audit Logging** | Maintain decision audit trail | SOX, GDPR Article 30 |
| **Right to Delete** | Handle data deletion requests | GDPR Article 17, CCPA |
| **Transparency** | Explain AI decisions | GDPR Article 22 |

### 6.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from datetime import datetime, timedelta
import hashlib

# ─── Governance Tools ─────────────────────────────────────────────────

@tool
def check_consent(customer_id: str, consent_type: str = "marketing") -> dict:
    """Check if customer has given consent for marketing communications.
    
    Args:
        customer_id: Customer identifier
        consent_type: Type of consent to check
    
    Returns:
        Dictionary with consent status and details
    """
    # Query consent management platform
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONSENT_API_URL}/consents/{customer_id}",
            params={"type": consent_type},
            headers={"Authorization": f"Bearer {CONSENT_API_KEY}"}
        )
        
        if response.status_code == 404:
            return {
                "customer_id": customer_id,
                "has_consent": False,
                "consent_type": consent_type,
                "status": "no_record",
                "can_market": False,
                "reason": "No consent record found",
            }
        
        response.raise_for_status()
        consent_data = response.json()
        
        return {
            "customer_id": customer_id,
            "has_consent": consent_data.get("granted", False),
            "consent_type": consent_type,
            "status": "granted" if consent_data.get("granted") else "denied",
            "granted_at": consent_data.get("granted_at"),
            "expires_at": consent_data.get("expires_at"),
            "source": consent_data.get("source"),
            "can_market": consent_data.get("granted", False) and not _is_consent_expired(consent_data),
            "reason": "Consent valid" if consent_data.get("granted") else "Consent denied or expired",
        }


@tool
def check_content_compliance(content: dict, regulations: list[str] = None) -> dict:
    """Check marketing content for regulatory compliance.
    
    Args:
        content: Content to check
        regulations: List of regulations to check against
    
    Returns:
        Dictionary with compliance check results
    """
    regulations = regulations or ["GDPR", "CAN-SPAM", "CCPA"]
    violations = []
    warnings = []
    
    content_str = json.dumps(content, default=str)
    
    # CAN-SPAM checks
    if "CAN-SPAM" in regulations:
        # Check for physical address
        if "address" not in content_str.lower() and "unsubscribe" not in content_str.lower():
            violations.append({
                "regulation": "CAN-SPAM",
                "rule": "Missing unsubscribe link",
                "severity": "critical",
                "description": "Commercial emails must include a clear unsubscribe mechanism",
            })
        
        # Check for misleading subject
        subject = content.get("subject", "")
        if subject and _is_misleading_subject(subject):
            violations.append({
                "regulation": "CAN-SPAM",
                "rule": "Misleading subject line",
                "severity": "critical",
                "description": "Subject line must not be deceptive",
            })
        
        # Check for physical postal address
        if "physical_address" not in content_str.lower():
            warnings.append({
                "regulation": "CAN-SPAM",
                "rule": "Missing physical address",
                "severity": "warning",
                "description": "Commercial emails must include valid physical postal address",
            })
    
    # GDPR checks
    if "GDPR" in regulations:
        # Check for consent reference
        if "consent" not in content_str.lower():
            warnings.append({
                "regulation": "GDPR",
                "rule": "No consent reference",
                "severity": "warning",
                "description": "Content should reference customer's consent",
            })
        
        # Check for data processing transparency
        if "data" in content_str.lower() and "process" not in content_str.lower():
            warnings.append({
                "regulation": "GDPR",
                "rule": "Data processing transparency",
                "severity": "warning",
                "description": "Content should explain how customer data is used",
            })
    
    # CCPA checks
    if "CCPA" in regulations:
        # Check for "Do Not Sell" link
        if "do not sell" not in content_str.lower():
            warnings.append({
                "regulation": "CCPA",
                "rule": "Missing Do Not Sell link",
                "severity": "warning",
                "description": "California residents must be able to opt out of data sale",
            })
    
    # FTC checks
    # Check for disclosure of material connections
    if "ad" not in content_str.lower() and "sponsored" not in content_str.lower():
        if any(word in content_str.lower() for word in ["promotion", "discount", "offer", "deal"]):
            warnings.append({
                "regulation": "FTC",
                "rule": "Ad disclosure",
                "severity": "warning",
                "description": "Promotional content should be clearly identified as advertising",
            })
    
    return {
        "content_id": content.get("content_id", "unknown"),
        "is_compliant": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "regulations_checked": regulations,
        "checked_at": datetime.utcnow().isoformat(),
    }


@tool
def detect_bias(content: dict, customer_segment: dict) -> dict:
    """Detect potential bias in marketing content and targeting.
    
    Args:
        content: Content to analyze
        customer_segment: Target customer segment
    
    Returns:
        Dictionary with bias analysis results
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    prompt = f"""Analyze the following marketing content and targeting for potential bias.

Content:
{json.dumps(content, indent=2, default=str)}

Target Segment:
{json.dumps(customer_segment, indent=2, default=str)}

Check for:
1. Demographic bias (age, gender, race, ethnicity, religion, disability)
2. Socioeconomic bias (income, education, occupation)
3. Geographic bias (location-based discrimination)
4. Language bias (exclusionary or stereotypical language)
5. Accessibility bias (content not accessible to people with disabilities)
6. Cultural bias (insensitive to cultural differences)

For each type of bias, provide:
- detected: true/false
- severity: low/medium/high
- description: explanation
- recommendation: how to fix

Return JSON with overall_bias_score (0-1, where 0 is no bias) and detailed findings.
"""
    
    response = llm.invoke(prompt)
    return json.loads(response.content)


@tool
def check_frequency_compliance(customer_id: str, message_history: list[dict], 
                                proposed_channel: str) -> dict:
    """Check if proposed communication complies with frequency limits.
    
    Args:
        customer_id: Customer identifier
        message_history: Recent message history
        proposed_channel: Channel for proposed message
    
    Returns:
        Dictionary with frequency compliance check
    """
    # Define frequency limits per channel
    limits = {
        "email": {"daily": 1, "weekly": 5, "monthly": 15},
        "sms": {"daily": 1, "weekly": 2, "monthly": 5},
        "push": {"daily": 2, "weekly": 7, "monthly": 20},
        "direct_mail": {"weekly": 1, "monthly": 2},
    }
    
    channel_limits = limits.get(proposed_channel, limits["email"])
    
    # Count recent messages
    now = datetime.utcnow()
    daily_count = 0
    weekly_count = 0
    monthly_count = 0
    
    for msg in message_history:
        msg_time = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
        days_ago = (now - msg_time).days
        
        if msg.get("channel") == proposed_channel:
            if days_ago <= 1:
                daily_count += 1
            if days_ago <= 7:
                weekly_count += 1
            if days_ago <= 30:
                monthly_count += 1
    
    # Check against limits
    violations = []
    if daily_count >= channel_limits["daily"]:
        violations.append(f"Daily limit reached ({daily_count}/{channel_limits['daily']})")
    if weekly_count >= channel_limits["weekly"]:
        violations.append(f"Weekly limit reached ({weekly_count}/{channel_limits['weekly']})")
    if monthly_count >= channel_limits["monthly"]:
        violations.append(f"Monthly limit reached ({monthly_count}/{channel_limits['monthly']})")
    
    # Check quiet hours (TCPA compliance for SMS/call)
    if proposed_channel in ["sms", "call"]:
        current_hour = now.hour
        if current_hour < 8 or current_hour > 21:
            violations.append("Outside allowed hours (8AM-9PM) for SMS/call")
    
    return {
        "customer_id": customer_id,
        "proposed_channel": proposed_channel,
        "is_compliant": len(violations) == 0,
        "violations": violations,
        "current_counts": {
            "daily": daily_count,
            "weekly": weekly_count,
            "monthly": monthly_count,
        },
        "limits": channel_limits,
        "next_available_slot": _next_available_slot(message_history, proposed_channel),
    }


@tool
def log_governance_decision(decision: dict) -> dict:
    """Log a governance decision for audit trail.
    
    Args:
        decision: Decision details to log
    
    Returns:
        Dictionary with logging confirmation
    """
    audit_entry = {
        "decision_id": hashlib.sha256(
            f"{decision.get('customer_id')}_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16],
        "timestamp": datetime.utcnow().isoformat(),
        "customer_id": decision.get("customer_id"),
        "decision_type": decision.get("decision_type"),
        "decision": decision.get("decision"),
        "reasoning": decision.get("reasoning"),
        "agent": decision.get("agent"),
        "content_id": decision.get("content_id"),
        "regulations_checked": decision.get("regulations_checked", []),
        "bias_score": decision.get("bias_score"),
        "consent_status": decision.get("consent_status"),
        "approved": decision.get("approved", False),
        "review_required": decision.get("review_required", False),
        "review_reason": decision.get("review_reason"),
    }
    
    # Store in audit log
    # In production, write to immutable audit log storage
    _store_audit_log(audit_entry)
    
    return {
        "logged": True,
        "decision_id": audit_entry["decision_id"],
        "timestamp": audit_entry["timestamp"],
    }


@tool
def handle_data_deletion_request(customer_id: str) -> dict:
    """Handle a right-to-deletion request (GDPR Article 17, CCPA).
    
    Args:
        customer_id: Customer identifier
    
    Returns:
        Dictionary with deletion request status
    """
    deletion_record = {
        "customer_id": customer_id,
        "request_type": "data_deletion",
        "requested_at": datetime.utcnow().isoformat(),
        "status": "processing",
        "steps": [
            {"step": "identify_data", "status": "pending"},
            {"step": "delete_crm", "status": "pending"},
            {"step": "delete_cdp", "status": "pending"},
            {"step": "delete_analytics", "status": "pending"},
            {"step": "delete_email_platform", "status": "pending"},
            {"step": "delete_third_party", "status": "pending"},
            {"step": "verify_deletion", "status": "pending"},
            {"step": "notify_customer", "status": "pending"},
        ],
        "completed_at": None,
    }
    
    # Execute deletion across systems
    deletion_results = {}
    
    # CRM deletion
    try:
        _delete_from_crm(customer_id)
        deletion_results["crm"] = "deleted"
    except Exception as e:
        deletion_results["crm"] = f"error: {str(e)}"
    
    # CDP deletion
    try:
        _delete_from_cdp(customer_id)
        deletion_results["cdp"] = "deleted"
    except Exception as e:
        deletion_results["cdp"] = f"error: {str(e)}"
    
    # Analytics anonymization
    try:
        _anonymize_analytics(customer_id)
        deletion_results["analytics"] = "anonymized"
    except Exception as e:
        deletion_results["analytics"] = f"error: {str(e)}"
    
    # Email platform suppression
    try:
        _suppress_email(customer_id)
        deletion_results["email_platform"] = "suppressed"
    except Exception as e:
        deletion_results["email_platform"] = f"error: {str(e)}"
    
    all_success = all(v in ["deleted", "anonymized", "suppressed"] for v in deletion_results.values())
    
    deletion_record["status"] = "completed" if all_success else "partial"
    deletion_record["deletion_results"] = deletion_results
    deletion_record["completed_at"] = datetime.utcnow().isoformat()
    
    return deletion_record


# ─── Governance Agent ─────────────────────────────────────────────────

GOVERNANCE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Governance Agent for a marketing personalization system.

Your responsibility is to ensure all marketing activities comply with regulations,
company policies, and ethical standards.

Capabilities:
- Consent verification
- Content compliance checking
- Bias detection and mitigation
- Frequency compliance enforcement
- Audit logging
- Data deletion request handling
- Transparency and explainability

Regulations to enforce:
- GDPR (General Data Protection Regulation)
- CCPA (California Consumer Privacy Act)
- CAN-SPAM (Controlling the Assault of Non-Solicited Pornography And Marketing)
- TCPA (Telephone Consumer Protection Act)
- FTC Act (Federal Trade Commission Act)

Guidelines:
- Always verify consent before marketing
- Check all content against applicable regulations
- Detect and flag potential bias
- Maintain complete audit trails
- Escalate edge cases for human review
- Prioritize customer privacy and rights
- Document all decisions and reasoning

Output structured governance decisions with clear approval/rejection and reasoning.
"""),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "{input}"),
])


def create_governance_agent(llm: Optional[ChatOpenAI] = None) -> AgentExecutor:
    """Create the Governance Agent.
    
    Returns:
        Configured AgentExecutor for governance
    """
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [
        check_consent,
        check_content_compliance,
        detect_bias,
        check_frequency_compliance,
        log_governance_decision,
        handle_data_deletion_request,
    ]
    
    agent = create_openai_functions_agent(llm, tools, GOVERNANCE_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
    )
```

### 6.4 Consent Management

```python
class ConsentManager:
    """Manages customer consent across all marketing channels."""
    
    CONSENT_TYPES = {
        "email_marketing": {
            "description": "Marketing emails",
            "regulations": ["GDPR", "CAN-SPAM", "CCPA"],
            "default_expiry_days": 365,
        },
        "sms_marketing": {
            "description": "Marketing SMS messages",
            "regulations": ["GDPR", "TCPA"],
            "default_expiry_days": 365,
        },
        "push_notifications": {
            "description": "Push notifications",
            "regulations": ["GDPR"],
            "default_expiry_days": 365,
        },
        "personalization": {
            "description": "AI-powered personalization",
            "regulations": ["GDPR"],
            "default_expiry_days": 365,
        },
        "data_processing": {
            "description": "Automated data processing",
            "regulations": ["GDPR"],
            "default_expiry_days": 365,
        },
        "third_party_sharing": {
            "description": "Sharing data with third parties",
            "regulations": ["GDPR", "CCPA"],
            "default_expiry_days": 365,
        },
    }
    
    def __init__(self):
        self.consent_store = {}  # In production: use database
    
    def record_consent(self, customer_id: str, consent_type: str, 
                       granted: bool, source: str, 
                       metadata: dict = None) -> dict:
        """Record a consent decision.
        
        Args:
            customer_id: Customer identifier
            consent_type: Type of consent
            granted: Whether consent was granted
            source: Source of consent (web_form, email, etc.)
            metadata: Additional metadata
        
        Returns:
            Consent record
        """
        if consent_type not in self.CONSENT_TYPES:
            raise ValueError(f"Unknown consent type: {consent_type}")
        
        config = self.CONSENT_TYPES[consent_type]
        
        record = {
            "customer_id": customer_id,
            "consent_type": consent_type,
            "granted": granted,
            "source": source,
            "granted_at": datetime.utcnow().isoformat() if granted else None,
            "denied_at": datetime.utcnow().isoformat() if not granted else None,
            "expires_at": (
                (datetime.utcnow() + timedelta(days=config["default_expiry_days"])).isoformat()
                if granted else None
            ),
            "regulations": config["regulations"],
            "metadata": metadata or {},
            "ip_address": metadata.get("ip_address") if metadata else None,
            "user_agent": metadata.get("user_agent") if metadata else None,
        }
        
        # Store consent record
        key = f"{customer_id}:{consent_type}"
        self.consent_store[key] = record
        
        return record
    
    def check_consent(self, customer_id: str, consent_type: str) -> dict:
        """Check if valid consent exists.
        
        Args:
            customer_id: Customer identifier
            consent_type: Type of consent to check
        
        Returns:
            Consent status
        """
        key = f"{customer_id}:{consent_type}"
        record = self.consent_store.get(key)
        
        if not record:
            return {
                "has_consent": False,
                "reason": "No consent record found",
                "can_market": False,
            }
        
        if not record.get("granted"):
            return {
                "has_consent": False,
                "reason": "Consent was denied",
                "can_market": False,
            }
        
        # Check expiry
        expires_at = record.get("expires_at")
        if expires_at:
            expiry = datetime.fromisoformat(expires_at)
            if datetime.utcnow() > expiry:
                return {
                    "has_consent": False,
                    "reason": "Consent has expired",
                    "can_market": False,
                    "expired_at": expires_at,
                }
        
        return {
            "has_consent": True,
            "reason": "Valid consent",
            "can_market": True,
            "granted_at": record.get("granted_at"),
            "expires_at": expires_at,
        }
    
    def withdraw_consent(self, customer_id: str, consent_type: str) -> dict:
        """Process a consent withdrawal request.
        
        Args:
            customer_id: Customer identifier
            consent_type: Type of consent to withdraw
        
        Returns:
            Withdrawal confirmation
        """
        key = f"{customer_id}:{consent_type}"
        record = self.consent_store.get(key)
        
        if record:
            record["granted"] = False
            record["denied_at"] = datetime.utcnow().isoformat()
            record["withdrawn_at"] = datetime.utcnow().isoformat()
        
        return {
            "customer_id": customer_id,
            "consent_type": consent_type,
            "withdrawn": True,
            "withdrawn_at": datetime.utcnow().isoformat(),
            "message": "Consent withdrawn successfully. All marketing will cease.",
        }
    
    def get_consent_summary(self, customer_id: str) -> dict:
        """Get a summary of all consent statuses for a customer.
        
        Args:
            customer_id: Customer identifier
        
        Returns:
            Consent summary
        """
        summary = {
            "customer_id": customer_id,
            "consents": {},
            "overall_status": "compliant",
        }
        
        for consent_type in self.CONSENT_TYPES:
            status = self.check_consent(customer_id, consent_type)
            summary["consents"][consent_type] = status
        
        # Check if any critical consent is missing
        critical_types = ["email_marketing", "personalization"]
        for ct in critical_types:
            if not summary["consents"][ct]["has_consent"]:
                summary["overall_status"] = "non_compliant"
                break
        
        return summary
```

---

## 7. Performance Analytics Agent Implementation

### 7.1 Purpose

The Performance Analytics Agent monitors, measures, and reports on the effectiveness of all marketing activities. It tracks key metrics, generates insights, creates dashboards, and alerts stakeholders to significant changes.

### 7.2 Analytics Capabilities

| Capability | Description | Metrics |
|-----------|-------------|---------|
| **Campaign Performance** | Track campaign ROI and effectiveness | ROAS, CPA, conversion rate |
| **Customer Analytics** | Monitor customer behavior trends | Engagement rate, retention, churn |
| **Attribution** | Multi-touch attribution modeling | First-touch, last-touch, linear, data-driven |
| **Predictive Analytics** | Forecast future performance | Revenue forecast, churn prediction |
| **Anomaly Detection** | Identify unusual patterns | Statistical anomaly detection |
| **Reporting** | Automated report generation | Daily, weekly, monthly reports |
| **Alerting** | Real-time performance alerts | Threshold-based alerts |
| **Benchmarking** | Compare against industry benchmarks | Percentile ranking |

### 7.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import pandas as pd
from scipy import stats

# ─── Analytics Tools ──────────────────────────────────────────────────

@tool
def calculate_campaign_metrics(campaign_data: dict) -> dict:
    """Calculate comprehensive campaign performance metrics.
    
    Args:
        campaign_data: Raw campaign data
    
    Returns:
        Dictionary with calculated metrics
    """
    impressions = campaign_data.get("impressions", 0)
    clicks = campaign_data.get("clicks", 0)
    conversions = campaign_data.get("conversions", 0)
    revenue = campaign_data.get("revenue", 0)
    cost = campaign_data.get("cost", 0)
    emails_sent = campaign_data.get("emails_sent", 0)
    emails_delivered = campaign_data.get("emails_delivered", 0)
    emails_opened = campaign_data.get("emails_opened", 0)
    emails_clicked = campaign_data.get("emails_clicked", 0)
    
    metrics = {
        "campaign_id": campaign_data.get("campaign_id"),
        "campaign_name": campaign_data.get("campaign_name"),
        
        # Delivery metrics
        "delivery_rate": emails_delivered / emails_sent if emails_sent > 0 else 0,
        "bounce_rate": 1 - (emails_delivered / emails_sent) if emails_sent > 0 else 0,
        
        # Engagement metrics
        "open_rate": emails_opened / emails_delivered if emails_delivered > 0 else 0,
        "click_rate": emails_clicked / emails_delivered if emails_delivered > 0 else 0,
        "click_through_rate": clicks / impressions if impressions > 0 else 0,
        "engagement_rate": (emails_opened + emails_clicked) / emails_delivered if emails_delivered > 0 else 0,
        
        # Conversion metrics
        "conversion_rate": conversions / emails_clicked if emails_clicked > 0 else 0,
        "conversion_rate_from_sent": conversions / emails_sent if emails_sent > 0 else 0,
        
        # Revenue metrics
        "revenue": revenue,
        "cost": cost,
        "profit": revenue - cost,
        "roas": revenue / cost if cost > 0 else 0,
        "roi": (revenue - cost) / cost if cost > 0 else 0,
        "cpa": cost / conversions if conversions > 0 else 0,
        "cpm": cost / (impressions / 1000) if impressions > 0 else 0,
        "revenue_per_email": revenue / emails_sent if emails_sent > 0 else 0,
        "revenue_per_customer": revenue / conversions if conversions > 0 else 0,
        
        # Time-based metrics
        "period": campaign_data.get("period", "unknown"),
        "days_active": campaign_data.get("days_active", 0),
    }
    
    return metrics


@tool
def perform_attribution_analysis(customer_journeys: list[dict], 
                                 model: str = "data_driven") -> dict:
    """Perform multi-touch attribution analysis.
    
    Args:
        customer_journeys: List of customer journey touchpoints
        model: Attribution model (first_touch, last_touch, linear, time_decay, data_driven)
    
    Returns:
        Dictionary with attribution results
    """
    if model == "first_touch":
        return _first_touch_attribution(customer_journeys)
    elif model == "last_touch":
        return _last_touch_attribution(customer_journeys)
    elif model == "linear":
        return _linear_attribution(customer_journeys)
    elif model == "time_decay":
        return _time_decay_attribution(customer_journeys)
    elif model == "data_driven":
        return _data_driven_attribution(customer_journeys)
    else:
        return {"error": f"Unknown attribution model: {model}"}


@tool
def detect_anomalies(metrics_data: list[dict], 
                     sensitivity: float = 2.0) -> list[dict]:
    """Detect anomalies in performance metrics.
    
    Args:
        metrics_data: Time-series metrics data
        sensitivity: Number of standard deviations for anomaly threshold
    
    Returns:
        List of detected anomalies
    """
    anomalies = []
    
    if not metrics_data or len(metrics_data) < 7:
        return anomalies
    
    df = pd.DataFrame(metrics_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    for column in numeric_columns:
        values = df[column].dropna()
        if len(values) < 7:
            continue
        
        mean = values.mean()
        std = values.std()
        
        if std == 0:
            continue
        
        z_scores = np.abs((values - mean) / std)
        anomaly_mask = z_scores > sensitivity
        
        for idx in values[anomaly_mask].index:
            anomalies.append({
                "timestamp": df.loc[idx, "timestamp"].isoformat(),
                "metric": column,
                "value": df.loc[idx, column],
                "expected_range": {
                    "lower": mean - sensitivity * std,
                    "upper": mean + sensitivity * std,
                },
                "z_score": z_scores[idx],
                "severity": "high" if z_scores[idx] > 3 else "medium",
                "direction": "spike" if df.loc[idx, column] > mean else "drop",
            })
    
    return anomalies


@tool
def generate_performance_report(report_type: str, 
                                 period: str,
                                 data: dict) -> dict:
    """Generate a performance report.
    
    Args:
        report_type: Type of report (executive, operational, detailed)
        period: Reporting period (daily, weekly, monthly, quarterly)
        data: Performance data
    
    Returns:
        Dictionary with report content
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0.3)
    
    prompt = f"""Generate a {report_type} performance report for the {period} period.

Performance Data:
{json.dumps(data, indent=2, default=str)}

Report Structure:
1. Executive Summary (key highlights and concerns)
2. Key Metrics Dashboard (table format)
3. Trend Analysis (week-over-week or month-over-month)
4. Segment Performance (breakdown by customer segment)
5. Channel Performance (breakdown by channel)
6. Top Performing Campaigns
7. Areas for Improvement
8. Recommendations

Tone: Professional, data-driven, actionable
Length: Appropriate for {report_type} audience

Return the report in markdown format.
"""
    
    response = llm.invoke(prompt)
    
    return {
        "report_type": report_type,
        "period": period,
        "generated_at": datetime.utcnow().isoformat(),
        "content": response.content,
        "data_summary": {
            "total_campaigns": data.get("total_campaigns", 0),
            "total_revenue": data.get("total_revenue", 0),
            "total_conversions": data.get("total_conversions", 0),
            "avg_roas": data.get("avg_roas", 0),
        },
    }


@tool
def forecast_performance(historical_data: list[dict], 
                         forecast_horizon: int = 30) -> dict:
    """Forecast future performance using time-series analysis.
    
    Args:
        historical_data: Historical performance data
        forecast_horizon: Number of days to forecast
    
    Returns:
        Dictionary with forecast results
    """
    df = pd.DataFrame(historical_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    
    # Simple moving average forecast (replace with Prophet/ARIMA in production)
    forecasts = {}
    
    for metric in ["revenue", "conversions", "engagement_rate"]:
        if metric not in df.columns:
            continue
        
        values = df[metric].dropna()
        if len(values) < 7:
            continue
        
        # Compute trend
        x = np.arange(len(values))
        slope, intercept, r_value, _, _ = stats.linregress(x, values)
        
        # Forecast
        last_idx = len(values)
        forecast_values = []
        for i in range(1, forecast_horizon + 1):
            forecast = intercept + slope * (last_idx + i)
            forecast_values.append(max(0, forecast))  # No negative values
        
        # Confidence interval
        residuals = values - (intercept + slope * x)
        mse = np.mean(residuals ** 2)
        std_error = np.sqrt(mse)
        
        forecasts[metric] = {
            "forecast_values": [round(v, 2) for v in forecast_values],
            "confidence_interval_95": {
                "lower": [round(max(0, v - 1.96 * std_error), 2) for v in forecast_values],
                "upper": [round(v + 1.96 * std_error, 2) for v in forecast_values],
            },
            "trend_slope": round(slope, 4),
            "trend_direction": "increasing" if slope > 0 else "decreasing",
            "r_squared": round(r_value ** 2, 4),
            "total_forecast": round(sum(forecast_values), 2),
        }
    
    return {
        "forecast_horizon_days": forecast_horizon,
        "forecast_start": (df["timestamp"].max() + timedelta(days=1)).isoformat(),
        "forecast_end": (df["timestamp"].max() + timedelta(days=forecast_horizon)).isoformat(),
        "metrics": forecasts,
        "model": "linear_trend",
        "confidence": "medium",
    }


@tool
def calculate_customer_analytics(customer_data: list[dict]) -> dict:
    """Calculate customer-level analytics.
    
    Args:
        customer_data: List of customer data
    
    Returns:
        Dictionary with customer analytics
    """
    df = pd.DataFrame(customer_data)
    
    analytics = {
        "total_customers": len(df),
        "active_customers": len(df[df.get("last_visit", pd.Timestamp.min) > 
                                    (datetime.utcnow() - timedelta(days=30))]),
        "new_customers_30d": len(df[df.get("created_at", pd.Timestamp.min) > 
                                     (datetime.utcnow() - timedelta(days=30))]),
        
        # Revenue metrics
        "total_revenue": df.get("total_revenue", pd.Series([0])).sum(),
        "avg_revenue_per_customer": df.get("total_revenue", pd.Series([0])).mean(),
        "median_revenue_per_customer": df.get("total_revenue", pd.Series([0])).median(),
        
        # Engagement metrics
        "avg_engagement_rate": df.get("email_engagement_rate", pd.Series([0])).mean(),
        "highly_engaged_customers": len(df[df.get("email_engagement_rate", 0) > 0.5]),
        
        # Segment distribution
        "segment_distribution": df.get("segment", pd.Series(["unknown"])).value_counts().to_dict(),
        
        # Churn metrics
        "churn_risk_distribution": df.get("churn_risk", pd.Series(["unknown"])).value_counts().to_dict(),
        
        # LTV metrics
        "avg_ltv": df.get("predicted_ltv", pd.Series([0])).mean(),
        "total_predicted_ltv": df.get("predicted_ltv", pd.Series([0])).sum(),
    }
    
    return analytics


@tool
def compare_to_benchmarks(metrics: dict, 
                          industry: str = "ecommerce") -> dict:
    """Compare performance metrics to industry benchmarks.
    
    Args:
        metrics: Current performance metrics
        industry: Industry for benchmark comparison
    
    Returns:
        Dictionary with benchmark comparison
    """
    # Industry benchmarks (simplified - use real data in production)
    benchmarks = {
        "ecommerce": {
            "email_open_rate": 0.215,
            "email_click_rate": 0.023,
            "email_conversion_rate": 0.005,
            "push_engagement_rate": 0.045,
            "sms_engagement_rate": 0.098,
            "avg_roas": 4.0,
            "avg_cpa": 45.0,
            "churn_rate": 0.05,
        },
        "saas": {
            "email_open_rate": 0.25,
            "email_click_rate": 0.035,
            "email_conversion_rate": 0.01,
            "push_engagement_rate": 0.06,
            "sms_engagement_rate": 0.12,
            "avg_roas": 3.5,
            "avg_cpa": 120.0,
            "churn_rate": 0.03,
        },
        "retail": {
            "email_open_rate": 0.18,
            "email_click_rate": 0.018,
            "email_conversion_rate": 0.004,
            "push_engagement_rate": 0.035,
            "sms_engagement_rate": 0.085,
            "avg_roas": 3.0,
            "avg_cpa": 35.0,
            "churn_rate": 0.07,
        },
    }
    
    industry_benchmarks = benchmarks.get(industry, benchmarks["ecommerce"])
    
    comparison = {}
    for metric, benchmark_value in industry_benchmarks.items():
        actual_value = metrics.get(metric, 0)
        variance = actual_value - benchmark_value
        variance_pct = (variance / benchmark_value * 100) if benchmark_value > 0 else 0
        
        comparison[metric] = {
            "actual": actual_value,
            "benchmark": benchmark_value,
            "variance": round(variance, 4),
            "variance_percentage": round(variance_pct, 1),
            "status": "above" if variance > 0 else "below" if variance < 0 else "at",
            "percentile_estimate": _estimate_percentile(actual_value, benchmark_value),
        }
    
    # Overall score
    above_count = sum(1 for c in comparison.values() if c["status"] == "above")
    overall_score = above_count / len(comparison) if comparison else 0
    
    return {
        "industry": industry,
        "metrics_comparison": comparison,
        "overall_score": round(overall_score, 2),
        "metrics_above_benchmark": above_count,
        "metrics_below_benchmark": len(comparison) - above_count,
        "summary": f"{above_count}/{len(comparison)} metrics above industry benchmark",
    }


# ─── Performance Analytics Agent ──────────────────────────────────────

ANALYTICS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Performance Analytics Agent for a marketing personalization system.

Your responsibility is to monitor, measure, and report on marketing performance
and provide actionable insights for continuous improvement.

Capabilities:
- Campaign performance measurement
- Multi-touch attribution analysis
- Anomaly detection
- Performance reporting
- Predictive forecasting
- Customer analytics
- Benchmark comparison

Guidelines:
- Use statistical methods for accurate measurement
- Provide context for all metrics (trends, comparisons)
- Highlight actionable insights, not just data
- Flag anomalies and significant changes
- Consider seasonality and external factors
- Automate reporting where possible
- Escalate critical issues immediately

Output structured analytics with clear visualizations and recommendations.
"""),
    MessagesPlaceholder(variable_name="messages"),
    ("human", "{input}"),
])


def create_analytics_agent(llm: Optional[ChatOpenAI] = None) -> AgentExecutor:
    """Create the Performance Analytics Agent.
    
    Returns:
        Configured AgentExecutor for analytics
    """
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [
        calculate_campaign_metrics,
        perform_attribution_analysis,
        detect_anomalies,
        generate_performance_report,
        forecast_performance,
        calculate_customer_analytics,
        compare_to_benchmarks,
    ]
    
    agent = create_openai_functions_agent(llm, tools, ANALYTICS_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=15,
        handle_parsing_errors=True,
    )
```

### 7.4 Attribution Models

```python
class AttributionModels:
    """Multi-touch attribution models."""
    
    @staticmethod
    def first_touch_attribution(journeys: list[dict]) -> dict:
        """First-touch attribution: 100% credit to first touchpoint."""
        channel_credit = defaultdict(float)
        total_conversions = 0
        
        for journey in journeys:
            if journey.get("converted", False):
                total_conversions += 1
                touchpoints = journey.get("touchpoints", [])
                if touchpoints:
                    first_channel = touchpoints[0].get("channel", "unknown")
                    channel_credit[first_channel] += 1
        
        return {
            "model": "first_touch",
            "total_conversions": total_conversions,
            "channel_credit": dict(channel_credit),
            "channel_percentage": {
                ch: round(credit / total_conversions * 100, 1) if total_conversions > 0 else 0
                for ch, credit in channel_credit.items()
            },
        }
    
    @staticmethod
    def last_touch_attribution(journeys: list[dict]) -> dict:
        """Last-touch attribution: 100% credit to last touchpoint."""
        channel_credit = defaultdict(float)
        total_conversions = 0
        
        for journey in journeys:
            if journey.get("converted", False):
                total_conversions += 1
                touchpoints = journey.get("touchpoints", [])
                if touchpoints:
                    last_channel = touchpoints[-1].get("channel", "unknown")
                    channel_credit[last_channel] += 1
        
        return {
            "model": "last_touch",
            "total_conversions": total_conversions,
            "channel_credit": dict(channel_credit),
            "channel_percentage": {
                ch: round(credit / total_conversions * 100, 1) if total_conversions > 0 else 0
                for ch, credit in channel_credit.items()
            },
        }
    
    @staticmethod
    def linear_attribution(journeys: list[dict]) -> dict:
        """Linear attribution: Equal credit to all touchpoints."""
        channel_credit = defaultdict(float)
        total_conversions = 0
        
        for journey in journeys:
            if journey.get("converted", False):
                total_conversions += 1
                touchpoints = journey.get("touchpoints", [])
                if touchpoints:
                    credit_per_touch = 1.0 / len(touchpoints)
                    for touch in touchpoints:
                        channel = touch.get("channel", "unknown")
                        channel_credit[channel] += credit_per_touch
        
        return {
            "model": "linear",
            "total_conversions": total_conversions,
            "channel_credit": {ch: round(c, 2) for ch, c in channel_credit.items()},
            "channel_percentage": {
                ch: round(credit / total_conversions * 100, 1) if total_conversions > 0 else 0
                for ch, credit in channel_credit.items()
            },
        }
    
    @staticmethod
    def time_decay_attribution(journeys: list[dict], 
                                half_life_days: float = 7.0) -> dict:
        """Time decay attribution: More credit to recent touchpoints."""
        channel_credit = defaultdict(float)
        total_conversions = 0
        
        for journey in journeys:
            if journey.get("converted", False):
                total_conversions += 1
                touchpoints = journey.get("touchpoints", [])
                if not touchpoints:
                    continue
                
                # Sort by timestamp
                sorted_touches = sorted(
                    touchpoints, 
                    key=lambda t: t.get("timestamp", "")
                )
                
                # Compute time decay weights
                conversion_time = datetime.fromisoformat(
                    journey.get("conversion_time", "").replace("Z", "+00:00")
                )
                
                weights = []
                for touch in sorted_touches:
                    touch_time = datetime.fromisoformat(
                        touch.get("timestamp", "").replace("Z", "+00:00")
                    )
                    days_before = (conversion_time - touch_time).total_seconds() / 86400
                    weight = 0.5 ** (days_before / half_life_days)
                    weights.append(weight)
                
                # Normalize weights
                total_weight = sum(weights)
                if total_weight > 0:
                    weights = [w / total_weight for w in weights]
                
                # Assign credit
                for touch, weight in zip(sorted_touches, weights):
                    channel = touch.get("channel", "unknown")
                    channel_credit[channel] += weight
        
        return {
            "model": "time_decay",
            "half_life_days": half_life_days,
            "total_conversions": total_conversions,
            "channel_credit": {ch: round(c, 2) for ch, c in channel_credit.items()},
            "channel_percentage": {
                ch: round(credit / total_conversions * 100, 1) if total_conversions > 0 else 0
                for ch, credit in channel_credit.items()
            },
        }
    
    @staticmethod
    def data_driven_attribution(journeys: list[dict]) -> dict:
        """Data-driven attribution: Algorithmic credit assignment."""
        # Simplified data-driven model using Shapley value concept
        # In production, use Markov chain or Shapley value computation
        
        channel_credit = defaultdict(float)
        total_conversions = 0
        
        # Count conversions with and without each channel
        channel_conversion_rates = defaultdict(lambda: {"with": 0, "without": 0})
        
        for journey in journeys:
            touchpoints = journey.get("touchpoints", [])
            channels = set(t.get("channel", "unknown") for t in touchpoints)
            converted = journey.get("converted", False)
            
            for channel in channels:
                if converted:
                    channel_conversion_rates[channel]["with"] += 1
            
            # Count journeys without this channel
            all_channels = set(t.get("channel", "unknown") for t in touchpoints)
            for channel in all_channels:
                if channel not in channels and converted:
                    channel_conversion_rates[channel]["without"] += 1
        
        # Compute marginal contribution
        for channel, counts in channel_conversion_rates.items():
            total_with = counts["with"]
            total_without = counts["without"]
            
            if total_with + total_without > 0:
                rate_with = total_with / (total_with + 1) if total_with > 0 else 0
                rate_without = total_without / (total_without + 1) if total_without > 0 else 0
                marginal_contribution = rate_with - rate_without
                channel_credit[channel] = max(0, marginal_contribution)
        
        # Normalize
        total_credit = sum(channel_credit.values())
        if total_credit > 0:
            channel_credit = {ch: c / total_credit for ch, c in channel_credit.items()}
        
        return {
            "model": "data_driven",
            "total_conversions": total_conversions,
            "channel_credit": {ch: round(c, 4) for ch, c in channel_credit.items()},
            "channel_percentage": {
                ch: round(c * 100, 1) for ch, c in channel_credit.items()
            },
        }
```

---

## 8. Code Examples and Snippets

### 8.1 Complete Pipeline Orchestration

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
import operator

# ─── State Definition ─────────────────────────────────────────────────

class MarketingPipelineState(TypedDict):
    """State shared across all agents in the pipeline."""
    customer_id: str
    customer_profile: dict
    segments: list[dict]
    insights: list[dict]
    personalized_content: dict
    delivery_plan: dict
    governance_decisions: list[dict]
    performance_metrics: dict
    messages: Annotated[list, operator.add]
    metadata: dict
    error: str


# ─── Pipeline Nodes ───────────────────────────────────────────────────

def data_collection_node(state: MarketingPipelineState) -> MarketingPipelineState:
    """Node for data collection."""
    agent = create_data_collection_agent()
    result = agent.invoke({
        "input": f"Collect comprehensive data for customer {state['customer_id']}"
    })
    
    # Parse result and update state
    profile = _parse_profile_from_result(result["output"])
    state["customer_profile"] = profile
    state["messages"].append(("data_collection", result["output"]))
    
    return state


def analysis_node(state: MarketingPipelineState) -> MarketingPipelineState:
    """Node for analysis."""
    agent = create_analysis_agent()
    result = agent.invoke({
        "input": f"Analyze customer profile and generate insights: {json.dumps(state['customer_profile'])}"
    })
    
    analysis = _parse_analysis_from_result(result["output"])
    state["segments"] = analysis.get("segments", [])
    state["insights"] = analysis.get("insights", [])
    state["messages"].append(("analysis", result["output"]))
    
    return state


def personalization_node(state: MarketingPipelineState) -> MarketingPipelineState:
    """Node for personalization."""
    agent = create_personalization_agent()
    result = agent.invoke({
        "input": f"Generate personalized content based on: {json.dumps(state['insights'])}"
    })
    
    content = _parse_content_from_result(result["output"])
    state["personalized_content"] = content
    state["messages"].append(("personalization", result["output"]))
    
    return state


def governance_node(state: MarketingPipelineState) -> MarketingPipelineState:
    """Node for governance check."""
    agent = create_governance_agent()
    result = agent.invoke({
        "input": f"Check governance compliance for: {json.dumps(state['personalized_content'])}"
    })
    
    governance = _parse_governance_from_result(result["output"])
    state["governance_decisions"] = governance.get("decisions", [])
    
    # If governance rejects, flag for review
    if not governance.get("approved", True):
        state["metadata"]["governance_flagged"] = True
        state["metadata"]["governance_reason"] = governance.get("reason", "")
    
    state["messages"].append(("governance", result["output"]))
    
    return state


def optimization_node(state: MarketingPipelineState) -> MarketingPipelineState:
    """Node for optimization."""
    agent = create_optimization_agent()
    result = agent.invoke({
        "input": f"Optimize delivery for: {json.dumps(state['personalized_content'])}"
    })
    
    plan = _parse_delivery_plan_from_result(result["output"])
    state["delivery_plan"] = plan
    state["messages"].append(("optimization", result["output"]))
    
    return state


def analytics_node(state: MarketingPipelineState) -> MarketingPipelineState:
    """Node for performance analytics."""
    agent = create_analytics_agent()
    result = agent.invoke({
        "input": f"Track performance for campaign delivery: {json.dumps(state['delivery_plan'])}"
    })
    
    metrics = _parse_metrics_from_result(result["output"])
    state["performance_metrics"] = metrics
    state["messages"].append(("analytics", result["output"]))
    
    return state


# ─── Pipeline Construction ────────────────────────────────────────────

def build_marketing_pipeline() -> StateGraph:
    """Build the complete marketing personalization pipeline.
    
    Returns:
        Compiled LangGraph state machine
    """
    workflow = StateGraph(MarketingPipelineState)
    
    # Add nodes
    workflow.add_node("data_collection", data_collection_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("personalization", personalization_node)
    workflow.add_node("governance", governance_node)
    workflow.add_node("optimization", optimization_node)
    workflow.add_node("analytics", analytics_node)
    
    # Define edges
    workflow.set_entry_point("data_collection")
    workflow.add_edge("data_collection", "analysis")
    workflow.add_edge("analysis", "personalization")
    workflow.add_edge("personalization", "governance")
    
    # Conditional edge based on governance decision
    def governance_routing(state: MarketingPipelineState) -> str:
        if state.get("metadata", {}).get("governance_flagged"):
            return "optimization"  # Skip to optimization with flag
        return "optimization"
    
    workflow.add_conditional_edges(
        "governance",
        governance_routing,
        {"optimization": "optimization"}
    )
    
    workflow.add_edge("optimization", "analytics")
    workflow.add_edge("analytics", END)
    
    # Compile with checkpointer
    checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
    app = workflow.compile(checkpointer=checkpointer)
    
    return app


# ─── Pipeline Execution ───────────────────────────────────────────────

async def run_personalization_pipeline(customer_id: str, 
                                        campaign_context: dict) -> dict:
    """Execute the full personalization pipeline for a customer.
    
    Args:
        customer_id: Customer identifier
        campaign_context: Campaign context and configuration
    
    Returns:
        Pipeline execution result
    """
    app = build_marketing_pipeline()
    
    initial_state = {
        "customer_id": customer_id,
        "customer_profile": {},
        "segments": [],
        "insights": [],
        "personalized_content": {},
        "delivery_plan": {},
        "governance_decisions": [],
        "performance_metrics": {},
        "messages": [],
        "metadata": {
            "campaign_context": campaign_context,
            "started_at": datetime.utcnow().isoformat(),
        },
        "error": "",
    }
    
    # Run pipeline
    config = {"configurable": {"thread_id": f"customer_{customer_id}"}}
    result = await app.ainvoke(initial_state, config=config)
    
    return {
        "customer_id": customer_id,
        "status": "completed",
        "profile": result.get("customer_profile"),
        "segments": result.get("segments"),
        "insights": result.get("insights"),
        "content": result.get("personalized_content"),
        "delivery_plan": result.get("delivery_plan"),
        "governance": result.get("governance_decisions"),
        "metrics": result.get("performance_metrics"),
        "metadata": result.get("metadata"),
    }
```

### 8.2 Inter-Agent Communication

```python
from redis import Redis
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    ALERT = "alert"
    GOVERNANCE_CHECK = "governance_check"
    GOVERNANCE_RESULT = "governance_result"

@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication."""
    message_id: str
    message_type: MessageType
    sender: str
    recipient: str
    payload: dict
    timestamp: str
    correlation_id: str
    priority: int = 5  # 1-10, lower is higher priority

class AgentCommunicationBus:
    """Redis-based communication bus for agent messaging."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.agent_channels = {
            "orchestrator": "agent:orchestrator",
            "data_collection": "agent:data_collection",
            "analysis": "agent:analysis",
            "personalization": "agent:personalization",
            "optimization": "agent:optimization",
            "governance": "agent:governance",
            "analytics": "agent:analytics",
        }
    
    def send_message(self, message: AgentMessage) -> bool:
        """Send a message to an agent's channel.
        
        Args:
            message: Message to send
        
        Returns:
            True if message was sent successfully
        """
        channel = self.agent_channels.get(message.recipient)
        if not channel:
            return False
        
        message_json = json.dumps(asdict(message), default=str)
        self.redis.rpush(channel, message_json)
        return True
    
    def receive_message(self, agent_name: str, timeout: int = 5) -> Optional[AgentMessage]:
        """Receive a message from an agent's channel.
        
        Args:
            agent_name: Agent to receive message for
            timeout: Timeout in seconds
        
        Returns:
            AgentMessage or None if no message available
        """
        channel = self.agent_channels.get(agent_name)
        if not channel:
            return None
        
        result = self.redis.blpop(channel, timeout=timeout)
        if result:
            _, message_json = result
            data = json.loads(message_json)
            return AgentMessage(**data)
        return None
    
    def publish_status(self, agent_name: str, status: dict) -> bool:
        """Publish a status update to all agents.
        
        Args:
            agent_name: Agent publishing the status
            status: Status data
        
        Returns:
            True if published successfully
        """
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.STATUS_UPDATE,
            sender=agent_name,
            recipient="all",
            payload=status,
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=str(uuid.uuid4()),
        )
        
        message_json = json.dumps(asdict(message), default=str)
        self.redis.publish("agent:broadcast", message_json)
        return True
    
    def request_governance_check(self, content: dict, 
                                  correlation_id: str) -> Optional[dict]:
        """Request a governance check from the Governance Agent.
        
        Args:
            content: Content to check
            correlation_id: Correlation ID for tracking
        
        Returns:
            Governance check result or None
        """
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.GOVERNANCE_CHECK,
            sender="orchestrator",
            recipient="governance",
            payload={"content": content},
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=correlation_id,
            priority=2,  # High priority
        )
        
        self.send_message(message)
        
        # Wait for response
        response = self.receive_message("orchestrator", timeout=30)
        if response and response.message_type == MessageType.GOVERNANCE_RESULT:
            return response.payload
        
        return None


# ─── Event-Driven Architecture ────────────────────────────────────────

class MarketingEventProcessor:
    """Processes marketing events and triggers appropriate agent actions."""
    
    def __init__(self, comm_bus: AgentCommunicationBus):
        self.comm_bus = comm_bus
        self.event_handlers = {
            "customer_created": self._handle_customer_created,
            "purchase_completed": self._handle_purchase_completed,
            "cart_abandoned": self._handle_cart_abandoned,
            "email_opened": self._handle_email_opened,
            "email_clicked": self._handle_email_clicked,
            "churn_risk_detected": self._handle_churn_risk,
            "campaign_ended": self._handle_campaign_ended,
        }
    
    async def process_event(self, event_type: str, event_data: dict) -> dict:
        """Process a marketing event.
        
        Args:
            event_type: Type of event
            event_data: Event data
        
        Returns:
            Processing result
        """
        handler = self.event_handlers.get(event_type)
        if not handler:
            return {"status": "ignored", "reason": f"No handler for {event_type}"}
        
        return await handler(event_data)
    
    async def _handle_customer_created(self, data: dict) -> dict:
        """Handle new customer event."""
        customer_id = data.get("customer_id")
        
        # Trigger data collection
        self.comm_bus.send_message(AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.TASK_REQUEST,
            sender="event_processor",
            recipient="data_collection",
            payload={"customer_id": customer_id, "task": "full_collection"},
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=str(uuid.uuid4()),
        ))
        
        return {"status": "triggered", "agent": "data_collection", "customer_id": customer_id}
    
    async def _handle_cart_abandoned(self, data: dict) -> dict:
        """Handle cart abandonment event."""
        customer_id = data.get("customer_id")
        cart_items = data.get("items", [])
        
        # Trigger personalization for cart recovery
        self.comm_bus.send_message(AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.TASK_REQUEST,
            sender="event_processor",
            recipient="personalization",
            payload={
                "customer_id": customer_id,
                "task": "cart_recovery",
                "cart_items": cart_items,
            },
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=str(uuid.uuid4()),
            priority=3,
        ))
        
        return {"status": "triggered", "agent": "personalization", "customer_id": customer_id}
    
    async def _handle_churn_risk(self, data: dict) -> dict:
        """Handle churn risk detection."""
        customer_id = data.get("customer_id")
        risk_score = data.get("risk_score", 0)
        
        if risk_score > 0.7:
            # High priority churn prevention
            self.comm_bus.send_message(AgentMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.TASK_REQUEST,
                sender="event_processor",
                recipient="personalization",
                payload={
                    "customer_id": customer_id,
                    "task": "churn_prevention",
                    "risk_score": risk_score,
                },
                timestamp=datetime.utcnow().isoformat(),
                correlation_id=str(uuid.uuid4()),
                priority=1,  # Highest priority
            ))
        
        return {"status": "triggered", "agent": "personalization", "customer_id": customer_id}
    
    async def _handle_purchase_completed(self, data: dict) -> dict:
        """Handle purchase completion event."""
        customer_id = data.get("customer_id")
        order_value = data.get("order_value", 0)
        
        # Trigger analysis update
        self.comm_bus.send_message(AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.TASK_REQUEST,
            sender="event_processor",
            recipient="analysis",
            payload={
                "customer_id": customer_id,
                "task": "update_profile",
                "event": "purchase",
                "order_value": order_value,
            },
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=str(uuid.uuid4()),
        ))
        
        return {"status": "triggered", "agent": "analysis", "customer_id": customer_id}
    
    async def _handle_email_opened(self, data: dict) -> dict:
        """Handle email open event."""
        # Update engagement metrics
        return {"status": "logged", "event": "email_opened"}
    
    async def _handle_email_clicked(self, data: dict) -> dict:
        """Handle email click event."""
        # Update engagement metrics and trigger follow-up
        return {"status": "logged", "event": "email_clicked"}
    
    async def _handle_campaign_ended(self, data: dict) -> dict:
        """Handle campaign end event."""
        campaign_id = data.get("campaign_id")
        
        # Trigger analytics
        self.comm_bus.send_message(AgentMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.TASK_REQUEST,
            sender="event_processor",
            recipient="analytics",
            payload={
                "campaign_id": campaign_id,
                "task": "generate_report",
            },
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=str(uuid.uuid4()),
        ))
        
        return {"status": "triggered", "agent": "analytics", "campaign_id": campaign_id}
```

### 8.3 Configuration Management

```python
from pydantic import BaseSettings, Field
from typing import Optional

class MarketingPersonalizationConfig(BaseSettings):
    """Configuration for the marketing personalization system."""
    
    # LLM Configuration
    default_llm_model: str = Field(default="gpt-4", env="DEFAULT_LLM_MODEL")
    data_collection_llm: str = Field(default="gpt-4", env="DATA_COLLECTION_LLM")
    analysis_llm: str = Field(default="gpt-4", env="ANALYSIS_LLM")
    personalization_llm: str = Field(default="gpt-4", env="PERSONALIZATION_LLM")
    governance_llm: str = Field(default="gpt-4", env="GOVERNANCE_LLM")
    analytics_llm: str = Field(default="gpt-4", env="ANALYTICS_LLM")
    
    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY")
    pinecone_environment: str = Field(default="us-east-1", env="PINECONE_ENVIRONMENT")
    
    # Data Sources
    salesforce_base_url: str = Field(..., env="SALESFORCE_BASE_URL")
    salesforce_token: str = Field(..., env="SALESFORCE_TOKEN")
    segment_write_key: str = Field(..., env="SEGMENT_WRITE_KEY")
    ga4_property_id: str = Field(..., env="GA4_PROPERTY_ID")
    sendgrid_api_key: str = Field(..., env="SENDGRID_API_KEY")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Vector Store
    pinecone_index_name: str = Field(default="marketing-content", env="PINECONE_INDEX_NAME")
    
    # Governance
    enable_governance: bool = Field(default=True, env="ENABLE_GOVERNANCE")
    enable_bias_detection: bool = Field(default=True, env="ENABLE_BIAS_DETECTION")
    enable_consent_check: bool = Field(default=True, env="ENABLE_CONSENT_CHECK")
    
    # Optimization
    ab_test_sample_size: int = Field(default=1000, env="AB_TEST_SAMPLE_SIZE")
    ab_test_confidence_level: float = Field(default=0.95, env="AB_TEST_CONFIDENCE_LEVEL")
    send_time_optimization: bool = Field(default=True, env="SEND_TIME_OPTIMIZATION")
    channel_optimization: bool = Field(default=True, env="CHANNEL_OPTIMIZATION")
    
    # Analytics
    enable_anomaly_detection: bool = Field(default=True, env="ENABLE_ANOMALY_DETECTION")
    anomaly_sensitivity: float = Field(default=2.0, env="ANOMALY_SENSITIVITY")
    forecast_horizon_days: int = Field(default=30, env="FORECAST_HORIZON_DAYS")
    
    # Rate Limiting
    max_requests_per_minute: int = Field(default=60, env="MAX_REQUESTS_PER_MINUTE")
    max_tokens_per_request: int = Field(default=4000, env="MAX_TOKENS_PER_REQUEST")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Load configuration
config = MarketingPersonalizationConfig()
```

### 8.4 Deployment Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Main application
  marketing-personalization:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/marketing
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Agent workers
  agent-worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/marketing
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  # PostgreSQL for state and data
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=marketing
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis for messaging and caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  # Grafana for dashboards
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

  # LangSmith for LLM tracing
  langsmith:
    image: langsmith/langsmith:latest
    ports:
      - "8080:8080"
    environment:
      - LANGCHAIN_TRACING_V2=true
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

---

## 9. Testing Strategy

### 9.1 Testing Overview

The testing strategy for the AI-powered marketing personalization system covers unit tests, integration tests, end-to-end tests, and performance tests. Given the AI-driven nature of the system, special attention is paid to LLM output validation, bias testing, and governance compliance testing.

### 9.2 Test Categories

| Category | Scope | Tools | Frequency |
|----------|-------|-------|-----------|
| **Unit Tests** | Individual functions and tools | pytest | Every commit |
| **Integration Tests** | Agent interactions and data flow | pytest + testcontainers | Every commit |
| **LLM Output Tests** | LLM response quality and consistency | Custom evaluators | Every commit |
| **End-to-End Tests** | Full pipeline execution | pytest + staging env | Daily |
| **Performance Tests** | Load and stress testing | Locust + k6 | Weekly |
| **Governance Tests** | Compliance and bias testing | Custom test suite | Every commit |
| **Chaos Tests** | Failure recovery | Chaos Monkey | Monthly |

### 9.3 Unit Tests

```python
# tests/test_data_collection.py
import pytest
from unittest.mock import AsyncMock, patch
from implementations.marketing-personalization-impl import (
    DataNormalizer,
    DataQualityValidator,
    UnifiedCustomerProfile,
)


class TestDataNormalizer:
    """Tests for the DataNormalizer class."""
    
    def setup_method(self):
        self.normalizer = DataNormalizer()
    
    def test_normalize_crm_data(self):
        """Test CRM data normalization."""
        raw_data = {
            "crm": {
                "Email": "john@example.com",
                "FirstName": "John",
                "LastName": "Doe",
                "Name": "John Doe",
                "Phone": "+1-555-0123",
            }
        }
        
        profile = self.normalizer.normalize(raw_data)
        
        assert profile.email == "john@example.com"
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.full_name == "John Doe"
        assert profile.phone == "+1-555-0123"
        assert "crm" in profile.data_sources
    
    def test_normalize_segment_data(self):
        """Test Segment data normalization."""
        raw_data = {
            "segment": {
                "traits": {
                    "email": "jane@example.com",
                    "firstName": "Jane",
                    "lastName": "Smith",
                    "sessions": 42,
                    "lastSeen": "2026-09-15T10:30:00Z",
                    "channels": ["email", "push"],
                }
            }
        }
        
        profile = self.normalizer.normalize(raw_data)
        
        assert profile.email == "jane@example.com"
        assert profile.total_sessions == 42
        assert "email" in profile.preferred_channels
        assert "push" in profile.preferred_channels
    
    def test_normalize_transactional_data(self):
        """Test transactional data normalization."""
        raw_data = {
            "transactional": {
                "orders": [
                    {"total": 150.00, "createdAt": "2026-09-01T10:00:00Z", "items": [{"category": "electronics"}]},
                    {"total": 75.50, "createdAt": "2026-08-15T14:30:00Z", "items": [{"category": "books"}]},
                    {"total": 200.00, "createdAt": "2026-07-20T09:00:00Z", "items": [{"category": "electronics"}]},
                ]
            }
        }
        
        profile = self.normalizer.normalize(raw_data)
        
        assert profile.total_orders == 3
        assert profile.total_revenue == 425.50
        assert profile.avg_order_value == pytest.approx(141.83, rel=0.01)
        assert "electronics" in profile.preferred_categories
        assert "books" in profile.preferred_categories
    
    def test_deep_merge(self):
        """Test deep merge functionality."""
        base = {"name": "John", "address": {"city": "NYC", "state": "NY"}}
        override = {"address": {"city": "LA", "zip": "90001"}}
        
        result = self.normalizer._deep_merge(base, override)
        
        assert result["name"] == "John"
        assert result["address"]["city"] == "LA"
        assert result["address"]["state"] == "NY"
        assert result["address"]["zip"] == "90001"
    
    def test_quality_score_computation(self):
        """Test data quality score computation."""
        profile = UnifiedCustomerProfile(
            customer_id="test_123",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            total_orders=5,
            total_revenue=500.0,
        )
        
        score = profile.compute_quality_score()
        
        assert 0 <= score <= 1
        assert profile.data_quality_score == score


class TestDataQualityValidator:
    """Tests for the DataQualityValidator class."""
    
    def setup_method(self):
        self.validator = DataQualityValidator()
    
    def test_valid_profile(self):
        """Test validation of a valid profile."""
        profile = UnifiedCustomerProfile(
            customer_id="test_123",
            email="valid@example.com",
            phone="+1-555-0123",
            age=30,
            total_revenue=1000.0,
        )
        
        result = self.validator.validate(profile)
        
        assert result["is_valid"] is True
        assert result["quality_score"] > 0.7
        assert len(result["errors"]) == 0
    
    def test_invalid_email(self):
        """Test validation catches invalid email."""
        profile = UnifiedCustomerProfile(
            customer_id="test_123",
            email="invalid-email",
        )
        
        result = self.validator.validate(profile)
        
        assert result["is_valid"] is False
        assert any("email" in e.lower() for e in result["errors"])
    
    def test_coppa_compliance(self):
        """Test COPPA compliance check for underage customers."""
        profile = UnifiedCustomerProfile(
            customer_id="test_123",
            email="child@example.com",
            age=10,
        )
        
        result = self.validator.validate(profile)
        
        assert result["is_valid"] is False
        assert any("COPPA" in e for e in result["errors"])
    
    def test_missing_critical_fields(self):
        """Test detection of missing critical fields."""
        profile = UnifiedCustomerProfile(
            customer_id="test_123",
            email="test@example.com",
        )
        
        result = self.validator.validate(profile)
        
        assert len(result["missing_critical_fields"]) > 0
        assert "first_name" in result["missing_critical_fields"]


# tests/test_analysis_agent.py
class TestSegmentationEngine:
    """Tests for the SegmentationEngine class."""
    
    def setup_method(self):
        self.engine = SegmentationEngine()
    
    def test_rfm_segmentation(self):
        """Test RFM segmentation."""
        profiles = [
            {"customer_id": "1", "last_purchase": "2026-09-28", "total_orders": 10, "total_revenue": 5000},
            {"customer_id": "2", "last_purchase": "2026-09-25", "total_orders": 5, "total_revenue": 2000},
            {"customer_id": "3", "last_purchase": "2026-01-01", "total_orders": 1, "total_revenue": 100},
            {"customer_id": "4", "last_purchase": "2026-09-20", "total_orders": 8, "total_revenue": 4000},
            {"customer_id": "5", "last_purchase": "2026-06-01", "total_orders": 2, "total_revenue": 500},
        ]
        
        segments = self.engine.create_rfm_segments(profiles)
        
        assert len(segments) > 0
        assert all(s.segment_type == SegmentType.VALUE_BASED for s in segments)
        assert sum(s.size for s in segments) == len(profiles)
    
    def test_behavioral_segmentation(self):
        """Test behavioral segmentation."""
        profiles = [
            {"customer_id": "1", "total_sessions": 50, "email_engagement_rate": 0.5, "total_orders": 5},
            {"customer_id": "2", "total_sessions": 15, "email_engagement_rate": 0.1, "total_orders": 0},
            {"customer_id": "3", "total_sessions": 5, "email_engagement_rate": 0.0, "total_orders": 1, "last_purchase": "2026-01-01"},
        ]
        
        segments = self.engine.create_behavioral_segments(profiles)
        
        assert len(segments) > 0
        segment_names = [s.name for s in segments]
        assert "Engaged Shoppers" in segment_names
        assert "Browsers" in segment_names


# tests/test_governance_agent.py
class TestConsentManager:
    """Tests for the ConsentManager class."""
    
    def setup_method(self):
        self.manager = ConsentManager()
    
    def test_record_consent(self):
        """Test recording consent."""
        record = self.manager.record_consent(
            customer_id="test_123",
            consent_type="email_marketing",
            granted=True,
            source="web_form",
            metadata={"ip_address": "192.168.1.1"},
        )
        
        assert record["granted"] is True
        assert record["consent_type"] == "email_marketing"
        assert record["source"] == "web_form"
        assert record["expires_at"] is not None
    
    def test_check_valid_consent(self):
        """Test checking valid consent."""
        self.manager.record_consent("test_123", "email_marketing", True, "web_form")
        
        status = self.manager.check_consent("test_123", "email_marketing")
        
        assert status["has_consent"] is True
        assert status["can_market"] is True
    
    def test_check_expired_consent(self):
        """Test checking expired consent."""
        # Record consent with short expiry
        record = self.manager.record_consent("test_123", "email_marketing", True, "web_form")
        
        # Manually expire the consent
        key = "test_123:email_marketing"
        self.manager.consent_store[key]["expires_at"] = (
            datetime.utcnow() - timedelta(days=1)
        ).isoformat()
        
        status = self.manager.check_consent("test_123", "email_marketing")
        
        assert status["has_consent"] is False
        assert status["can_market"] is False
        assert "expired" in status["reason"].lower()
    
    def test_withdraw_consent(self):
        """Test consent withdrawal."""
        self.manager.record_consent("test_123", "email_marketing", True, "web_form")
        
        result = self.manager.withdraw_consent("test_123", "email_marketing")
        
        assert result["withdrawn"] is True
        
        status = self.manager.check_consent("test_123", "email_marketing")
        assert status["has_consent"] is False
        assert status["can_market"] is False


class TestContentCompliance:
    """Tests for content compliance checking."""
    
    def test_can_spam_compliance_valid(self):
        """Test CAN-SPAM compliance for valid content."""
        content = {
            "subject": "Special Offer Inside",
            "body": "Check out our amazing deals! Unsubscribe here. 123 Main St, City, ST 12345",
        }
        
        result = check_content_compliance(content, regulations=["CAN-SPAM"])
        
        assert result["is_compliant"] is True
    
    def test_can_spam_compliance_missing_unsubscribe(self):
        """Test CAN-SPAM compliance catches missing unsubscribe."""
        content = {
            "subject": "Special Offer Inside",
            "body": "Check out our amazing deals!",
        }
        
        result = check_content_compliance(content, regulations=["CAN-SPAM"])
        
        assert result["is_compliant"] is False
        assert any("unsubscribe" in v["rule"].lower() for v in result["violations"])
    
    def test_can_spam_compliance_misleading_subject(self):
        """Test CAN-SPAM compliance catches misleading subject."""
        content = {
            "subject": "URGENT: You've Won $1,000,000!!!",
            "body": "Unsubscribe here. 123 Main St, City, ST 12345",
        }
        
        result = check_content_compliance(content, regulations=["CAN-SPAM"])
        
        assert result["is_compliant"] is False
        assert any("misleading" in v["rule"].lower() for v in result["violations"])
```

### 9.4 Integration Tests

```python
# tests/integration/test_pipeline.py
import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

@pytest_asyncio.fixture(scope="module")
async def postgres():
    """Start PostgreSQL test container."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres.get_connection_url()


@pytest_asyncio.fixture(scope="module")
async def redis():
    """Start Redis test container."""
    with RedisContainer("redis:7") as redis:
        yield redis.get_connection_url()


@pytest.mark.asyncio
async def test_full_pipeline_execution(postgres, redis):
    """Test full pipeline execution with real dependencies."""
    # Initialize components
    comm_bus = AgentCommunicationBus(redis_url=redis)
    event_processor = MarketingEventProcessor(comm_bus)
    
    # Create test customer
    customer_id = "test_customer_001"
    
    # Run pipeline
    result = await run_personalization_pipeline(
        customer_id=customer_id,
        campaign_context={"campaign_type": "welcome_series", "season": "fall_2026"},
    )
    
    # Verify results
    assert result["status"] == "completed"
    assert result["customer_id"] == customer_id
    assert result["profile"] is not None
    assert "segments" in result
    assert "insights" in result
    assert "content" in result
    assert "delivery_plan" in result
    assert "governance" in result
    assert "metrics" in result


@pytest.mark.asyncio
async def test_event_driven_workflow(postgres, redis):
    """Test event-driven workflow."""
    comm_bus = AgentCommunicationBus(redis_url=redis)
    event_processor = MarketingEventProcessor(comm_bus)
    
    # Test cart abandonment event
    result = await event_processor.process_event("cart_abandoned", {
        "customer_id": "test_customer_001",
        "items": [
            {"product_id": "prod_1", "name": "Running Shoes", "price": 120.00},
            {"product_id": "prod_2", "name": "Sports Socks", "price": 15.00},
        ],
        "cart_value": 135.00,
    })
    
    assert result["status"] == "triggered"
    assert result["agent"] == "personalization"


@pytest.mark.asyncio
async def test_governance_rejection_workflow(postgres, redis):
    """Test workflow when governance rejects content."""
    comm_bus = AgentCommunicationBus(redis_url=redis)
    
    # Create content that should be rejected
    non_compliant_content = {
        "subject": "You've WON! Click now!!!",
        "body": "Congratulations! You've been selected for a prize! Click here to claim!",
        "channel": "email",
    }
    
    # Run governance check
    governance_agent = create_governance_agent()
    result = governance_agent.invoke({
        "input": f"Check governance compliance: {json.dumps(non_compliant_content)}"
    })
    
    # Verify rejection
    assert "non_compliant" in result["output"].lower() or "violation" in result["output"].lower()
```

### 9.5 LLM Output Quality Tests

```python
# tests/test_llm_output_quality.py
import pytest
from langchain_openai import ChatOpenAI
from langchain.evaluation import load_evaluator

class TestLLMOutputQuality:
    """Tests for LLM output quality and consistency."""
    
    @pytest.fixture
    def llm(self):
        return ChatOpenAI(model="gpt-4", temperature=0)
    
    @pytest.fixture
    def evaluator(self):
        return load_evaluator("criteria", criteria="conciseness", llm=ChatOpenAI())
    
    def test_personalization_quality(self, llm):
        """Test that personalized content is actually personalized."""
        customer_profile = {
            "first_name": "Sarah",
            "preferred_categories": ["running", "fitness"],
            "total_orders": 5,
            "total_revenue": 500,
        }
        
        prompt = f"""Create a personalized email subject line for:
        Name: {customer_profile['first_name']}
        Interests: {', '.join(customer_profile['preferred_categories'])}
        Customer since: 5 orders
        """
        
        response = llm.invoke(prompt)
        subject = response.content
        
        # Check personalization elements
        assert "Sarah" in subject or "running" in subject.lower() or "fitness" in subject.lower()
    
    def test_content_diversity(self, llm):
        """Test that generated content is diverse (not repetitive)."""
        subjects = []
        for i in range(5):
            response = llm.invoke(
                f"Create a unique email subject line for a summer sale campaign (variant {i+1})"
            )
            subjects.append(response.content.strip())
        
        # Check uniqueness
        assert len(set(subjects)) >= 3, "Subject lines should be diverse"
    
    def test_governance_consistency(self, llm):
        """Test that governance decisions are consistent."""
        content = {
            "subject": "Special Offer",
            "body": "Great deals! Unsubscribe here. 123 Main St, City, ST 12345",
        }
        
        # Run governance check multiple times
        results = []
        for _ in range(3):
            response = llm.invoke(
                f"Is this content CAN-SPAM compliant? Content: {json.dumps(content)}"
            )
            results.append("compliant" in response.content.lower())
        
        # Should be consistent
        assert all(results) or not any(results), "Governance decisions should be consistent"
    
    def test_bias_detection(self, llm):
        """Test that bias is detected in problematic content."""
        biased_content = {
            "subject": "Perfect for young men who love sports",
            "targeting": {"age": "18-25", "gender": "male"},
        }
        
        response = llm.invoke(
            f"Analyze this marketing content for bias: {json.dumps(biased_content)}"
        )
        
        # Should detect age and gender bias
        output_lower = response.content.lower()
        assert "bias" in output_lower or "discriminat" in output_lower or "exclusionary" in output_lower
    
    def test_factual_accuracy(self, llm):
        """Test that generated content doesn't contain obvious factual errors."""
        response = llm.invoke(
            "Write a 50-word product description for a premium running shoe with "
            "carbon fiber plate, nitrogen-infused midsole, and engineered mesh upper."
        )
        
        description = response.content
        
        # Check that key features are mentioned
        assert "carbon" in description.lower()
        assert "nitrogen" in description.lower()
        assert "mesh" in description.lower()
```

### 9.6 Performance Tests

```python
# tests/performance/test_performance.py
import pytest
import time
import asyncio
from locust import HttpUser, task, between

class MarketingPipelinePerformanceTests:
    """Performance tests for the marketing personalization pipeline."""
    
    @pytest.mark.asyncio
    async def test_pipeline_latency(self):
        """Test that pipeline completes within acceptable latency."""
        from implementations.marketing-personalization-impl import run_personalization_pipeline
        
        start_time = time.time()
        
        result = await run_personalization_pipeline(
            customer_id="perf_test_001",
            campaign_context={"campaign_type": "test"},
        )
        
        elapsed = time.time() - start_time
        
        # Pipeline should complete within 30 seconds
        assert elapsed < 30, f"Pipeline took {elapsed:.1f}s, expected < 30s"
        assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_concurrent_pipeline_execution(self):
        """Test concurrent pipeline executions."""
        from implementations.marketing-personalization-impl import run_personalization_pipeline
        
        customer_ids = [f"concurrent_test_{i}" for i in range(10)]
        
        start_time = time.time()
        
        # Run 10 pipelines concurrently
        tasks = [
            run_personalization_pipeline(
                customer_id=cid,
                campaign_context={"campaign_type": "load_test"},
            )
            for cid in customer_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        # All should complete within 60 seconds
        assert elapsed < 60, f"Concurrent execution took {elapsed:.1f}s"
        
        # At least 80% should succeed
        successes = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "completed")
        assert successes >= 8, f"Only {successes}/10 pipelines succeeded"
    
    @pytest.mark.asyncio
    async def test_data_collection_throughput(self):
        """Test data collection agent throughput."""
        from implementations.marketing_personalization_impl import create_data_collection_agent
        
        agent = create_data_collection_agent()
        
        start_time = time.time()
        
        # Process 50 customers
        tasks = []
        for i in range(50):
            tasks.append(agent.ainvoke({
                "input": f"Collect data for customer throughput_test_{i}"
            }))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        # Should process 50 customers within 120 seconds
        assert elapsed < 120, f"Data collection took {elapsed:.1f}s for 50 customers"
        
        # At least 90% should succeed
        successes = sum(1 for r in results if isinstance(r, dict) and "output" in r)
        assert successes >= 45, f"Only {successes}/50 data collections succeeded"


# Locust load testing configuration
class MarketingPipelineUser(HttpUser):
    """Locust user for load testing the marketing pipeline API."""
    
    wait_time = between(1, 5)
    
    def on_start(self):
        """Setup before tests."""
        self.client.post("/api/v1/auth/login", json={
            "username": "load_test_user",
            "password": "test_password",
        })
    
    @task(3)
    def trigger_personalization(self):
        """Trigger personalization pipeline."""
        self.client.post("/api/v1/personalization/trigger", json={
            "customer_id": f"load_test_{self.user_id}",
            "campaign_context": {"campaign_type": "load_test"},
        })
    
    @task(2)
    def get_customer_profile(self):
        """Get customer profile."""
        self.client.get(f"/api/v1/customers/load_test_{self.user_id}/profile")
    
    @task(1)
    def get_campaign_metrics(self):
        """Get campaign metrics."""
        self.client.get("/api/v1/analytics/campaigns/load_test_campaign/metrics")
```

### 9.7 Governance and Compliance Tests

```python
# tests/test_governance_compliance.py
import pytest
from implementations.marketing-personalization-impl import (
    check_content_compliance,
    detect_bias,
    check_frequency_compliance,
    ConsentManager,
)

class TestGovernanceCompliance:
    """Comprehensive governance and compliance tests."""
    
    def test_gdpr_consent_requirement(self):
        """Test GDPR consent requirement enforcement."""
        content = {
            "subject": "Personalized Recommendations",
            "body": "Based on your browsing history, we recommend...",
            "uses_personal_data": True,
        }
        
        result = check_content_compliance(content, regulations=["GDPR"])
        
        # Should flag need for consent reference
        assert any("consent" in w["rule"].lower() for w in result["warnings"])
    
    def test_ccpa_do_not_sell(self):
        """Test CCPA Do Not Sell requirement."""
        content = {
            "subject": "Special Offers",
            "body": "Check out our deals! Unsubscribe here. 123 Main St, City, ST 12345",
        }
        
        result = check_content_compliance(content, regulations=["CCPA"])
        
        # Should flag missing Do Not Sell link
        assert any("do not sell" in w["rule"].lower() for w in result["warnings"])
    
    def test_tcpa_quiet_hours(self):
        """Test TCPA quiet hours compliance."""
        # Create message history with messages at various times
        message_history = [
            {"timestamp": "2026-09-30T10:00:00Z", "channel": "sms"},
            {"timestamp": "2026-09-30T14:00:00Z", "channel": "sms"},
        ]
        
        # Test during quiet hours (e.g., 10 PM)
        with patch("implementations.marketing-personalization-impl.datetime") as mock_dt:
            mock_dt.utcnow.return_value = datetime(2026, 9, 30, 22, 0, 0)
            
            result = check_frequency_compliance(
                customer_id="test_123",
                message_history=message_history,
                proposed_channel="sms",
            )
            
            assert result["is_compliant"] is False
            assert any("quiet hours" in v.lower() or "8am-9pm" in v.lower() 
                      for v in result["violations"])
    
    def test_frequency_cap_enforcement(self):
        """Test frequency cap enforcement."""
        # Create message history exceeding limits
        message_history = [
            {"timestamp": f"2026-09-{30-i}T10:00:00Z", "channel": "email"}
            for i in range(10)  # 10 emails in last 10 days
        ]
        
        result = check_frequency_compliance(
            customer_id="test_123",
            message_history=message_history,
            proposed_channel="email",
        )
        
        # Should flag frequency violation
        assert result["is_compliant"] is False
    
    def test_bias_detection_age(self):
        """Test age bias detection."""
        content = {
            "subject": "Perfect for young people!",
            "body": "This product is ideal for teenagers and college students.",
        }
        segment = {"age_range": "18-25"}
        
        result = detect_bias(content, segment)
        
        assert result["overall_bias_score"] > 0.3
        assert any(b["type"] == "age" for b in result.get("findings", []))
    
    def test_bias_detection_gender(self):
        """Test gender bias detection."""
        content = {
            "subject": "Great for men who love sports",
            "body": "This product is designed for the modern man.",
        }
        segment = {"gender": "male"}
        
        result = detect_bias(content, segment)
        
        assert result["overall_bias_score"] > 0.3
    
    def test_data_deletion_request(self):
        """Test data deletion request handling."""
        result = handle_data_deletion_request("test_customer_123")
        
        assert result["status"] in ["completed", "processing", "partial"]
        assert "deletion_results" in result
        assert result["customer_id"] == "test_customer_123"
    
    def test_audit_trail_completeness(self):
        """Test that all governance decisions are logged."""
        decision = {
            "customer_id": "test_123",
            "decision_type": "content_approval",
            "decision": "approved",
            "reasoning": "Content complies with all regulations",
            "agent": "governance",
            "regulations_checked": ["GDPR", "CAN-SPAM"],
            "bias_score": 0.1,
            "consent_status": "granted",
            "approved": True,
        }
        
        result = log_governance_decision(decision)
        
        assert result["logged"] is True
        assert "decision_id" in result
        assert "timestamp" in result
```

### 9.8 Test Execution Plan

```bash
#!/bin/bash
# run_tests.sh - Complete test execution script

set -e

echo "=== Running Unit Tests ==="
pytest tests/test_data_collection.py -v --cov=implementations --cov-report=html
pytest tests/test_analysis_agent.py -v --cov=implementations --cov-report=html
pytest tests/test_governance_agent.py -v --cov=implementations --cov-report=html

echo "=== Running Integration Tests ==="
pytest tests/integration/ -v --timeout=300

echo "=== Running LLM Output Quality Tests ==="
pytest tests/test_llm_output_quality.py -v --timeout=600

echo "=== Running Governance Compliance Tests ==="
pytest tests/test_governance_compliance.py -v

echo "=== Running Performance Tests ==="
pytest tests/performance/ -v --timeout=600

echo "=== Running Load Tests ==="
locust -f tests/performance/locustfile.py --headless -u 100 -r 10 --run-time 5m

echo "=== All Tests Complete ==="
```

### 9.9 Test Coverage Targets

| Component | Line Coverage | Branch Coverage | Notes |
|-----------|--------------|-----------------|-------|
| Data Collection Agent | 90% | 85% | All data sources tested |
| Analysis Agent | 85% | 80% | ML models validated |
| Personalization Agent | 80% | 75% | LLM outputs evaluated |
| Optimization Agent | 85% | 80% | Statistical tests validated |
| Governance Agent | 95% | 90% | Compliance critical |
| Analytics Agent | 85% | 80% | Metrics accuracy verified |
| Pipeline Orchestration | 90% | 85% | End-to-end flows tested |

### 9.10 Continuous Testing Strategy

1. **Pre-commit Hooks:** Run unit tests and linting before every commit
2. **CI Pipeline:** Run all tests on every pull request
3. **Nightly Builds:** Run full test suite including integration and performance tests
4. **Weekly Load Tests:** Run comprehensive load tests against staging environment
5. **Monthly Chaos Tests:** Run chaos engineering tests to validate resilience
6. **Quarterly Compliance Audits:** Full governance and compliance review

---

## Appendix A: Environment Variables

```bash
# .env.example

# LLM Configuration
OPENAI_API_KEY=sk-...
DEFAULT_LLM_MODEL=gpt-4

# Vector Store
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=marketing-content

# Data Sources
SALESFORCE_BASE_URL=https://your-instance.salesforce.com
SALESFORCE_TOKEN=...
SEGMENT_WRITE_KEY=...
GA4_PROPERTY_ID=...
SENDGRID_API_KEY=...
META_ACCESS_TOKEN=...
X_BEARER_TOKEN=...
CLEARBIT_API_KEY=...

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/marketing
REDIS_URL=redis://localhost:6379

# Governance
ENABLE_GOVERNANCE=true
ENABLE_BIAS_DETECTION=true
ENABLE_CONSENT_CHECK=true

# Optimization
AB_TEST_SAMPLE_SIZE=1000
AB_TEST_CONFIDENCE_LEVEL=0.95

# Analytics
ENABLE_ANOMALY_DETECTION=true
ANOMALY_SENSITIVITY=2.0

# LangSmith Tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=marketing-personalization
```

## Appendix B: API Endpoints

```yaml
# API specification (OpenAPI 3.0)
openapi: 3.0.0
info:
  title: Marketing Personalization API
  version: 1.0.0

paths:
  /api/v1/personalization/trigger:
    post:
      summary: Trigger personalization pipeline
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                customer_id:
                  type: string
                campaign_context:
                  type: object
      responses:
        200:
          description: Pipeline triggered successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PipelineResult'

  /api/v1/customers/{customer_id}/profile:
    get:
      summary: Get unified customer profile
      parameters:
        - name: customer_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Customer profile
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CustomerProfile'

  /api/v1/customers/{customer_id}/segments:
    get:
      summary: Get customer segment assignments
      parameters:
        - name: customer_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Segment assignments
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Segment'

  /api/v1/analytics/campaigns/{campaign_id}/metrics:
    get:
      summary: Get campaign performance metrics
      parameters:
        - name: campaign_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Campaign metrics
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CampaignMetrics'

  /api/v1/governance/consent/{customer_id}:
    get:
      summary: Get customer consent status
      parameters:
        - name: customer_id
          in: path
          required: true
          schema:
            type: string
      responses:
        200:
          description: Consent status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConsentStatus'

  /api/v1/governance/audit-log:
    get:
      summary: Get governance audit log
      parameters:
        - name: customer_id
          in: query
          schema:
            type: string
        - name: start_date
          in: query
          schema:
            type: string
            format: date-time
        - name: end_date
          in: query
          schema:
            type: string
            format: date-time
      responses:
        200:
          description: Audit log entries
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AuditLogEntry'

components:
  schemas:
    PipelineResult:
      type: object
      properties:
        customer_id:
          type: string
        status:
          type: string
        profile:
          $ref: '#/components/schemas/CustomerProfile'
        segments:
          type: array
          items:
            $ref: '#/components/schemas/Segment'
        content:
          type: object
        delivery_plan:
          type: object
        governance:
          type: array
          items:
            type: object
        metrics:
          type: object

    CustomerProfile:
      type: object
      properties:
        customer_id:
          type: string
        email:
          type: string
        first_name:
          type: string
        last_name:
          type: string
        total_orders:
          type: integer
        total_revenue:
          type: number
        preferred_categories:
          type: array
          items:
            type: string
        data_quality_score:
          type: number

    Segment:
      type: object
      properties:
        segment_id:
          type: string
        name:
          type: string
        segment_type:
          type: string
        characteristics:
          type: object

    CampaignMetrics:
      type: object
      properties:
        campaign_id:
          type: string
        impressions:
          type: integer
        clicks:
          type: integer
        conversions:
          type: integer
        revenue:
          type: number
        cost:
          type: number
        roas:
          type: number
        roi:
          type: number

    ConsentStatus:
      type: object
      properties:
        customer_id:
          type: string
        consents:
          type: object
        overall_status:
          type: string

    AuditLogEntry:
      type: object
      properties:
        decision_id:
          type: string
        timestamp:
          type: string
          format: date-time
        customer_id:
          type: string
        decision_type:
          type: string
        decision:
          type: string
        approved:
          type: boolean
```

---

*End of Implementation Plan*</longcat_think>
