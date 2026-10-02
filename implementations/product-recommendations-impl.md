# AI-Powered Product Recommendations Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Stack:** LangChain DeepAgents, Python 3.11+, OpenAI GPT-4o, Pinecone, Redis, FastAPI

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Data Collection Agent](#2-data-collection-agent)
3. [Analysis Agent](#3-analysis-agent)
4. [Recommendation Agent](#4-recommendation-agent)
5. [Cross-Sell Agent](#5-cross-sell-agent)
6. [Optimization Agent](#6-optimization-agent)
7. [Performance Analytics Agent](#7-performance-analytics-agent)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The AI-powered product recommendation system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. Six specialized agents collaborate through a central coordinator to deliver personalized, real-time product recommendations.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (Coordinator)                    │
│              LangChain DeepAgents + Router Chain                │
└────────┬──────────┬──────────┬──────────┬──────────┬───────────┘
         │          │          │          │          │
    ┌────▼────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼──────────┐
    │  Data   │ │Analysis│ │  Rec   │ │Cross-  │ │Optimization │
    │Collection│ │ Agent  │ │ Agent  │ │Sell    │ │   Agent     │
    │  Agent  │ │        │ │        │ │ Agent  │ │             │
    └────┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └──────┬──────┘
         │          │          │          │              │
    ┌────▼──────────▼──────────▼──────────▼──────────────▼────┐
    │              Performance Analytics Agent                  │
    │         (Monitors all agents, collects metrics)           │
    └──────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents | Multi-agent orchestration |
| LLM | OpenAI GPT-4o | Reasoning and generation |
| Vector DB | Pinecone | Product embeddings, similarity search |
| Cache | Redis | Session state, real-time features |
| Feature Store | Feast | Online/offline feature serving |
| API | FastAPI | REST endpoints for recommendations |
| Message Queue | Apache Kafka | Event streaming between agents |
| Monitoring | Langfuse + Prometheus | Tracing and metrics |
| Orchestration | LangGraph | Agent workflow state machines |

### 1.3 Agent Communication Protocol

Agents communicate via **structured messages** through Kafka topics:

```python
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from enum import Enum

class AgentType(Enum):
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    CROSS_SELL = "cross_sell"
    OPTIMIZATION = "optimization"
    ANALYTICS = "analytics"

class MessagePriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AgentMessage:
    """Standard inter-agent communication message."""
    message_id: str
    source_agent: AgentType
    target_agent: AgentType
    message_type: str  # "request", "response", "event", "alert"
    payload: dict[str, Any]
    priority: MessagePriority = MessagePriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None  # For tracing request-response pairs
    ttl_seconds: int = 300  # Message time-to-live

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "source_agent": self.source_agent.value,
            "target_agent": self.target_agent.value,
            "message_type": self.message_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "ttl_seconds": self.ttl_seconds,
        }
```

### 1.4 Orchestrator Design

```python
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class OrchestratorState(TypedDict):
    """State passed between agents in the orchestration graph."""
    user_id: str
    session_id: str
    context: dict  # User context: browsing history, cart, preferences
    task: str  # Current task description
    agent_outputs: Annotated[list, operator.add]  # Accumulated agent results
    final_recommendations: list
    metadata: dict  # Timing, confidence scores, explanations

class RecommendationOrchestrator:
    """
    Central coordinator that routes tasks to specialized agents
    and aggregates their outputs using LangGraph state machines.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.agents = {}
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(OrchestratorState)

        # Add agent nodes
        workflow.add_node("data_collection", self._run_data_collection)
        workflow.add_node("analysis", self._run_analysis)
        workflow.add_node("recommendation", self._run_recommendation)
        workflow.add_node("cross_sell", self._run_cross_sell)
        workflow.add_node("optimization", self._run_optimization)
        workflow.add_node("analytics", self._run_analytics)

        # Define edges (execution flow)
        workflow.set_entry_point("data_collection")
        workflow.add_edge("data_collection", "analysis")
        workflow.add_edge("analysis", "recommendation")
        workflow.add_edge("recommendation", "cross_sell")
        workflow.add_edge("cross_sell", "optimization")
        workflow.add_edge("optimization", "analytics")
        workflow.add_edge("analytics", END)

        return workflow.compile()

    async def recommend(self, user_id: str, session_id: str, context: dict) -> dict:
        """Main entry point for getting recommendations."""
        initial_state = OrchestratorState(
            user_id=user_id,
            session_id=session_id,
            context=context,
            task="Generate personalized product recommendations",
            agent_outputs=[],
            final_recommendations=[],
            metadata={"start_time": datetime.utcnow().isoformat()},
        )
        result = await self.graph.ainvoke(initial_state)
        return {
            "recommendations": result["final_recommendations"],
            "metadata": result["metadata"],
        }
```

### 1.5 Agent Responsibilities Matrix

| Agent | Input | Output | Tools | Latency SLA |
|-------|-------|--------|-------|-------------|
| Data Collection | User ID, session context | Enriched user profile | DB queries, API calls, event streams | < 200ms |
| Analysis | User profile | Behavioral segments, intent | Statistical models, clustering | < 300ms |
| Recommendation | Analysis results | Ranked product list | Vector search, ranking models | < 150ms |
| Cross-Sell | Recommendations + cart | Complementary products | Association rules, graph traversal | < 100ms |
| Optimization | All prior outputs | Final ranked list with explanations | A/B testing, diversification | < 100ms |
| Analytics | All agent outputs | Metrics, logs, alerts | Monitoring dashboards | Async |

---

## 2. Data Collection Agent

### 2.1 Purpose

The Data Collection Agent gathers all relevant user data from multiple sources to build a comprehensive, real-time user profile for downstream agents.

### 2.2 Data Sources

```python
from abc import ABC, abstractmethod
from typing import Any
import asyncio

class DataSource(ABC):
    """Abstract base class for all data sources."""

    @abstractmethod
    async def fetch(self, user_id: str, **kwargs) -> dict[str, Any]:
        pass

class UserProfileSource(DataSource):
    """Fetches user demographic and preference data from the main database."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def fetch(self, user_id: str, **kwargs) -> dict:
        query = """
            SELECT user_id, age_group, gender, location, 
                   preferred_categories, price_sensitivity,
                   loyalty_tier, account_created_at,
                   email_subscribed, notification_prefs
            FROM user_profiles 
            WHERE user_id = $1
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else {}

class BrowsingHistorySource(DataSource):
    """Fetches real-time browsing history from Redis/clickstream."""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def fetch(self, user_id: str, **kwargs) -> dict:
        # Get last 50 page views from the last 24 hours
        key = f"user:{user_id}:page_views"
        views = await self.redis.lrange(key, 0, 49)

        # Get search queries
        search_key = f"user:{user_id}:searches"
        searches = await self.redis.lrange(search_key, 0, 19)

        # Get product interactions
        interaction_key = f"user:{user_id}:interactions"
        interactions = await self.redis.lrange(interaction_key, 0, 99)

        return {
            "recent_page_views": [json.loads(v) for v in views],
            "recent_searches": [json.loads(s) for s in searches],
            "product_interactions": [json.loads(i) for i in interactions],
        }

class PurchaseHistorySource(DataSource):
    """Fetches historical purchase data."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def fetch(self, user_id: str, **kwargs) -> dict:
        query = """
            SELECT order_id, product_id, quantity, unit_price, 
                   discount_applied, order_date, category,
                   payment_method, returned
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.user_id = $1
            ORDER BY o.order_date DESC
            LIMIT 100
        """
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return {"purchase_history": [dict(r) for r in rows]}

class CartStateSource(DataSource):
    """Fetches current cart contents in real-time."""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def fetch(self, user_id: str, **kwargs) -> dict:
        cart_key = f"user:{user_id}:cart"
        cart_items = await self.redis.hgetall(cart_key)
        return {
            "cart_items": [
                json.loads(v) for v in cart_items.values()
            ],
            "cart_total": sum(
                json.loads(v).get("price", 0) * json.loads(v).get("quantity", 1)
                for v in cart_items.values()
            ),
        }

class RealTimeEventSource(DataSource):
    """Consumes real-time events from Kafka (clicks, wishlist adds, etc.)."""

    def __init__(self, kafka_consumer):
        self.kafka = kafka_consumer

    async def fetch(self, user_id: str, **kwargs) -> dict:
        # Poll recent events for this user (last 5 minutes)
        events = []
        async for msg in self.kafka.poll(timeout_ms=100):
            event = json.loads(msg.value)
            if event.get("user_id") == user_id:
                events.append(event)
            if len(events) >= 200:
                break
        return {"real_time_events": events}
```

### 2.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
import uuid

class DataCollectionAgent:
    """
    Collects and enriches user data from multiple sources.
    Runs data quality checks and produces a unified user profile.
    """

    def __init__(self, config: dict):
        self.llm = ChatOpenAI(
            model=config.get("model", "gpt-4o"),
            temperature=0,  # Deterministic for data collection
        )
        self.sources: list[DataSource] = []
        self.prompt = self._build_prompt()
        self.agent = self._build_agent()

    def _build_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            ("system", """You are the Data Collection Agent. Your job is to gather 
            all relevant user data from available sources and produce a comprehensive, 
            structured user profile. 
            
            Rules:
            1. Fetch data from ALL available sources in parallel
            2. Validate data quality (check for missing fields, stale data)
            3. Flag any anomalies or data quality issues
            4. Produce a unified JSON profile with confidence scores
            5. Never fabricate data - if a source is unavailable, mark it as such
            
            Output format:
            {
                "user_id": "...",
                "profile": { ... },
                "data_quality": { "completeness": 0.0-1.0, "issues": [...] },
                "collection_metadata": { "sources_used": [...], "latency_ms": ... }
            }"""),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])

    def _build_agent(self):
        tools = [
            self._create_fetch_profile_tool(),
            self._create_fetch_browsing_tool(),
            self._create_fetch_purchases_tool(),
            self._create_fetch_cart_tool(),
            self._create_fetch_events_tool(),
            self._create_validate_data_tool(),
        ]
        agent = create_openai_functions_agent(self.llm, tools, self.prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )

    def _create_fetch_profile_tool(self):
        @tool
        async def fetch_user_profile(user_id: str) -> str:
            """Fetch the user's demographic profile and preferences from the main database."""
            source = UserProfileSource(self.db_pool)
            data = await source.fetch(user_id)
            return json.dumps(data)
        return fetch_user_profile

    def _create_fetch_browsing_tool(self):
        @tool
        async def fetch_browsing_history(user_id: str, limit: int = 50) -> str:
            """Fetch the user's recent browsing history including page views, searches, and interactions."""
            source = BrowsingHistorySource(self.redis_client)
            data = await source.fetch(user_id, limit=limit)
            return json.dumps(data)
        return fetch_browsing_history

    def _create_fetch_purchases_tool(self):
        @tool
        async def fetch_purchase_history(user_id: str, limit: int = 100) -> str:
            """Fetch the user's historical purchases and order details."""
            source = PurchaseHistorySource(self.db_pool)
            data = await source.fetch(user_id, limit=limit)
            return json.dumps(data)
        return fetch_purchase_history

    def _create_fetch_cart_tool(self):
        @tool
        async def fetch_cart_state(user_id: str) -> str:
            """Fetch the user's current shopping cart contents in real-time."""
            source = CartStateSource(self.redis_client)
            data = await source.fetch(user_id)
            return json.dumps(data)
        return fetch_cart_state

    def _create_fetch_events_tool(self):
        @tool
        async def fetch_real_time_events(user_id: str, window_minutes: int = 5) -> str:
            """Fetch real-time user events from the event stream (clicks, wishlist adds, etc.)."""
            source = RealTimeEventSource(self.kafka_consumer)
            data = await source.fetch(user_id, window_minutes=window_minutes)
            return json.dumps(data)
        return fetch_real_time_events

    def _create_validate_data_tool(self):
        @tool
        def validate_data_quality(profile_json: str) -> str:
            """Validate the collected user data for completeness, consistency, and freshness."""
            profile = json.loads(profile_json)
            issues = []
            completeness_scores = {}

            # Check required fields
            required_fields = ["user_id", "age_group", "location"]
            for field in required_fields:
                if not profile.get(field):
                    issues.append(f"Missing required field: {field}")
                    completeness_scores[field] = 0.0
                else:
                    completeness_scores[field] = 1.0

            # Check data freshness
            if "last_active" in profile:
                last_active = datetime.fromisoformat(profile["last_active"])
                days_inactive = (datetime.utcnow() - last_active).days
                if days_inactive > 30:
                    issues.append(f"User inactive for {days_inactive} days")

            # Check for anomalies
            if profile.get("purchase_history"):
                total_spend = sum(p["unit_price"] * p["quantity"] for p in profile["purchase_history"])
                if total_spend > 100000:  # Unusually high spend
                    issues.append(f"Unusually high lifetime spend: ${total_spend:,.2f}")

            completeness = sum(completeness_scores.values()) / max(len(completeness_scores), 1)

            return json.dumps({
                "completeness_score": completeness,
                "issues": issues,
                "is_valid": completeness >= 0.6 and len(issues) < 3,
            })
        return validate_data_quality

    async def run(self, user_id: str, session_id: str) -> dict:
        """Execute data collection for a user."""
        start_time = time.monotonic()

        result = await self.agent.ainvoke({
            "input": f"Collect all data for user {user_id}, session {session_id}",
            "chat_history": [],
        })

        latency_ms = (time.monotonic() - start_time) * 1000

        return {
            "agent": AgentType.DATA_COLLECTION.value,
            "user_id": user_id,
            "session_id": session_id,
            "output": result["output"],
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
```

### 2.4 Data Schema

```python
from pydantic import BaseModel, Field
from typing import Optional

class UnifiedUserProfile(BaseModel):
    """Standardized user profile produced by the Data Collection Agent."""

    user_id: str
    demographics: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    behavioral_summary: dict = Field(default_factory=dict)
    purchase_summary: dict = Field(default_factory=dict)
    current_session: dict = Field(default_factory=dict)
    data_quality: dict = Field(default_factory=dict)
    collected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr_12345",
                "demographics": {
                    "age_group": "25-34",
                    "location": "US-NY",
                    "loyalty_tier": "gold",
                },
                "preferences": {
                    "preferred_categories": ["electronics", "home"],
                    "price_sensitivity": "medium",
                    "brand_affinity": ["apple", "sony"],
                },
                "behavioral_summary": {
                    "total_sessions_30d": 45,
                    "avg_session_duration_sec": 320,
                    "favorite_category": "electronics",
                    "cart_abandonment_rate": 0.35,
                },
                "purchase_summary": {
                    "lifetime_orders": 23,
                    "lifetime_spend": 4520.00,
                    "avg_order_value": 196.52,
                    "return_rate": 0.08,
                    "last_purchase_days_ago": 12,
                },
                "current_session": {
                    "cart_items_count": 2,
                    "cart_value": 299.99,
                    "active_category": "electronics",
                    "session_duration_sec": 180,
                },
                "data_quality": {
                    "completeness": 0.92,
                    "issues": [],
                },
            }
        }
```

---

## 3. Analysis Agent

### 3.1 Purpose

The Analysis Agent processes the unified user profile to extract behavioral patterns, segment the user, detect intent, and compute affinity scores that downstream agents use for recommendations.

### 3.2 Analysis Pipeline

```python
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd

class AnalysisAgent:
    """
    Analyzes user data to produce behavioral insights, segmentation,
    intent detection, and affinity scoring.
    """

    def __init__(self, config: dict):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        self.scaler = StandardScaler()
        self.segmentation_model = None  # Loaded from trained model
        self.intent_classifier = None   # Loaded from trained model

    async def run(self, user_profile: dict, context: dict) -> dict:
        """Execute the full analysis pipeline."""
        start_time = time.monotonic()

        # Step 1: Behavioral segmentation
        segment = await self._compute_segment(user_profile)

        # Step 2: Intent detection
        intent = await self._detect_intent(user_profile, context)

        # Step 3: Category affinity scoring
        category_affinity = self._compute_category_affinity(user_profile)

        # Step 4: Price sensitivity analysis
        price_sensitivity = self._analyze_price_sensitivity(user_profile)

        # Step 5: Purchase propensity scoring
        purchase_propensity = self._score_purchase_propensity(user_profile)

        # Step 6: Churn risk assessment
        churn_risk = self._assess_churn_risk(user_profile)

        # Step 7: Generate natural language insights
        insights = await self._generate_insights(
            user_profile, segment, intent, category_affinity
        )

        latency_ms = (time.monotonic() - start_time) * 1000

        return {
            "agent": AgentType.ANALYSIS.value,
            "user_id": user_profile["user_id"],
            "segment": segment,
            "intent": intent,
            "category_affinity": category_affinity,
            "price_sensitivity": price_sensitivity,
            "purchase_propensity": purchase_propensity,
            "churn_risk": churn_risk,
            "insights": insights,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _compute_segment(self, profile: dict) -> dict:
        """Assign user to a behavioral segment using clustering."""
        features = self._extract_segmentation_features(profile)

        if self.segmentation_model:
            segment_id = self.segmentation_model.predict([features])[0]
            segment_name = self._segment_id_to_name(segment_id)
        else:
            # Fallback rule-based segmentation
            segment_name = self._rule_based_segment(profile)

        return {
            "segment_id": segment_id if self.segmentation_model else None,
            "segment_name": segment_name,
            "confidence": 0.85,
        }

    def _extract_segmentation_features(self, profile: dict) -> list[float]:
        """Extract numerical features for segmentation."""
        behavioral = profile.get("behavioral_summary", {})
        purchase = profile.get("purchase_summary", {})

        return [
            behavioral.get("total_sessions_30d", 0),
            behavioral.get("avg_session_duration_sec", 0),
            behavioral.get("cart_abandonment_rate", 0),
            purchase.get("lifetime_orders", 0),
            purchase.get("lifetime_spend", 0),
            purchase.get("avg_order_value", 0),
            purchase.get("return_rate", 0),
            purchase.get("last_purchase_days_ago", 365),
        ]

    def _rule_based_segment(self, profile: dict) -> str:
        """Fallback rule-based segmentation when ML model is unavailable."""
        purchase = profile.get("purchase_summary", {})
        behavioral = profile.get("behavioral_summary", {})

        ltv = purchase.get("lifetime_spend", 0)
        orders = purchase.get("lifetime_orders", 0)
        abandonment = behavioral.get("cart_abandonment_rate", 0)
        days_since = purchase.get("last_purchase_days_ago", 365)

        if ltv > 5000 and orders > 10:
            return "vip_loyal"
        elif ltv > 1000 and orders > 3:
            return "repeat_buyer"
        elif orders == 0 and behavioral.get("total_sessions_30d", 0) > 10:
            return "browser"
        elif abandonment > 0.5:
            return "cart_abandoner"
        elif days_since > 90:
            return "at_risk"
        else:
            return "new_prospect"

    async def _detect_intent(self, profile: dict, context: dict) -> dict:
        """Detect user's current shopping intent using LLM + heuristics."""
        # Build intent detection prompt
        recent_views = profile.get("current_session", {}).get("recent_views", [])
        searches = profile.get("current_session", {}).get("searches", [])
        cart = profile.get("current_session", {}).get("cart_items", [])

        intent_prompt = f"""Analyze the following user session data and classify 
        the primary shopping intent. Choose from: 
        - "browsing" (just looking, no clear goal)
        - "comparison" (comparing products)
        - "purchase_ready" (ready to buy, has items in cart)
        - "research" (gathering information)
        - "deal_seeking" (looking for discounts)
        - "reorder" (repeating a previous purchase)

        Recent product views: {[v.get('category') for v in recent_views[:10]]}
        Recent searches: {[s.get('query') for s in searches[:5]]}
        Cart items: {[c.get('category') for c in cart]}
        Session duration: {context.get('session_duration_sec', 0)} seconds

        Respond with JSON: {{"intent": "...", "confidence": 0.0-1.0, "explanation": "..."}}"""

        response = await self.llm.ainvoke(intent_prompt)
        intent_result = json.loads(response.content)

        return intent_result

    def _compute_category_affinity(self, profile: dict) -> dict[str, float]:
        """Compute affinity scores for each product category."""
        affinity = defaultdict(float)

        # Weight different signals
        weights = {
            "purchases": 1.0,
            "views": 0.3,
            "searches": 0.5,
            "cart_adds": 0.8,
        }

        # Purchase-based affinity
        for order in profile.get("purchase_summary", {}).get("orders", []):
            cat = order.get("category", "unknown")
            affinity[cat] += weights["purchases"] * order.get("quantity", 1)

        # View-based affinity
        for view in profile.get("current_session", {}).get("recent_views", []):
            cat = view.get("category", "unknown")
            affinity[cat] += weights["views"]

        # Search-based affinity
        for search in profile.get("current_session", {}).get("searches", []):
            for cat in search.get("categories_matched", []):
                affinity[cat] += weights["searches"]

        # Normalize to 0-1
        if affinity:
            max_score = max(affinity.values())
            affinity = {k: v / max_score for k, v in affinity.items()}

        return dict(affinity)

    def _analyze_price_sensitivity(self, profile: dict) -> dict:
        """Analyze user's price sensitivity from purchase behavior."""
        orders = profile.get("purchase_summary", {}).get("orders", [])

        if not orders:
            return {"level": "unknown", "score": 0.5}

        discounts = [o.get("discount_applied", 0) for o in orders]
        avg_discount = np.mean(discounts) if discounts else 0

        # Categorize sensitivity
        if avg_discount > 0.3:
            level = "high"
        elif avg_discount > 0.1:
            level = "medium"
        else:
            level = "low"

        return {
            "level": level,
            "score": min(avg_discount * 2, 1.0),  # Normalize to 0-1
            "avg_discount_used": avg_discount,
        }

    def _score_purchase_propensity(self, profile: dict) -> dict:
        """Score the likelihood of the user making a purchase."""
        behavioral = profile.get("behavioral_summary", {})
        purchase = profile.get("purchase_summary", {})
        session = profile.get("current_session", {})

        # Feature engineering
        features = {
            "has_cart_items": 1 if session.get("cart_items_count", 0) > 0 else 0,
            "cart_value": session.get("cart_value", 0),
            "session_duration": session.get("session_duration_sec", 0),
            "pages_viewed": len(session.get("recent_views", [])),
            "returning_customer": 1 if purchase.get("lifetime_orders", 0) > 0 else 0,
            "days_since_last_purchase": purchase.get("last_purchase_days_ago", 365),
            "abandonment_rate": behavioral.get("cart_abandonment_rate", 0),
        }

        # Simple logistic-style scoring
        score = 0.0
        score += features["has_cart_items"] * 0.3
        score += min(features["cart_value"] / 500, 1.0) * 0.2
        score += min(features["session_duration"] / 600, 1.0) * 0.15
        score += min(features["pages_viewed"] / 20, 1.0) * 0.1
        score += features["returning_customer"] * 0.15
        score -= features["abandonment_rate"] * 0.1

        return {
            "score": min(max(score, 0.0), 1.0),
            "likelihood": "high" if score > 0.6 else "medium" if score > 0.3 else "low",
            "factors": features,
        }

    def _assess_churn_risk(self, profile: dict) -> dict:
        """Assess the risk of the user churning."""
        purchase = profile.get("purchase_summary", {})
        behavioral = profile.get("behavioral_summary", {})

        days_since = purchase.get("last_purchase_days_ago", 365)
        orders = purchase.get("lifetime_orders", 0)
        sessions = behavioral.get("total_sessions_30d", 0)

        # Churn risk factors
        risk_score = 0.0
        if days_since > 90:
            risk_score += 0.4
        if days_since > 180:
            risk_score += 0.3
        if sessions < 2:
            risk_score += 0.2
        if orders > 5 and days_since > 60:
            risk_score += 0.1

        return {
            "risk_level": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low",
            "risk_score": min(risk_score, 1.0),
            "days_since_last_purchase": days_since,
        }

    async def _generate_insights(
        self, profile: dict, segment: dict, intent: dict, affinity: dict
    ) -> list[str]:
        """Generate natural language insights about the user."""
        prompt = f"""Based on the following user analysis, generate 3-5 concise, 
        actionable insights for a recommendation engine:
        
        Segment: {segment['segment_name']}
        Intent: {intent['intent']} (confidence: {intent['confidence']})
        Top categories: {dict(sorted(affinity.items(), key=lambda x: -x[1])[:3])}
        Behavioral summary: {profile.get('behavioral_summary', {})}
        Purchase summary: {profile.get('purchase_summary', {})}
        
        Each insight should be one sentence, focused on recommendation strategy."""

        response = await self.llm.ainvoke(prompt)
        insights = [s.strip() for s in response.content.split("\n") if s.strip()]
        return insights[:5]
```

---

## 4. Recommendation Agent

### 4.1 Purpose

The Recommendation Agent generates personalized product recommendations using a hybrid approach combining collaborative filtering, content-based filtering, and LLM-powered ranking.

### 4.2 Recommendation Strategy

```python
class RecommendationAgent:
    """
    Generates personalized product recommendations using hybrid filtering:
    1. Candidate generation (multiple strategies)
    2. LLM-based ranking and filtering
    3. Diversity injection
    4. Business rule application
    """

    def __init__(self, config: dict):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.vector_store = PineconeVectorStore(
            api_key=config["pinecone_api_key"],
            index_name=config["pinecone_index"],
        )
        self.product_catalog = ProductCatalogService(config)
        self.cache = RedisCache(config["redis_url"])

    async def run(self, user_profile: dict, analysis: dict, context: dict) -> dict:
        """Generate recommendations for a user."""
        start_time = time.monotonic()

        # Step 1: Generate candidates from multiple sources
        candidates = await self._generate_candidates(user_profile, analysis, context)

        # Step 2: Score and rank candidates
        ranked = await self._rank_candidates(candidates, user_profile, analysis)

        # Step 3: Apply diversity and business rules
        diversified = self._apply_diversity(ranked, max_results=20)

        # Step 4: Generate explanations
        recommendations = await self._generate_explanations(
            diversified, user_profile, analysis
        )

        latency_ms = (time.monotonic() - start_time) * 1000

        return {
            "agent": AgentType.RECOMMENDATION.value,
            "user_id": user_profile["user_id"],
            "recommendations": recommendations,
            "candidate_count": len(candidates),
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _generate_candidates(
        self, profile: dict, analysis: dict, context: dict
    ) -> list[dict]:
        """Generate candidate products from multiple strategies."""
        candidates = []

        # Strategy 1: Vector similarity (content-based)
        vector_candidates = await self._vector_similarity_search(profile, analysis)
        candidates.extend(vector_candidates)

        # Strategy 2: Collaborative filtering (users like you)
        cf_candidates = await self._collaborative_filtering(profile)
        candidates.extend(cf_candidates)

        # Strategy 3: Trending in preferred categories
        trending = await self._get_trending(profile, analysis)
        candidates.extend(trending)

        # Strategy 4: Personalized search results
        search_based = await self._search_based_candidates(profile, context)
        candidates.extend(search_based)

        # Strategy 5: LLM-generated suggestions
        llm_candidates = await self._llm_candidate_generation(profile, analysis)
        candidates.extend(llm_candidates)

        # Deduplicate
        seen_ids = set()
        unique_candidates = []
        for c in candidates:
            pid = c["product_id"]
            if pid not in seen_ids:
                seen_ids.add(pid)
                unique_candidates.append(c)

        return unique_candidates

    async def _vector_similarity_search(
        self, profile: dict, analysis: dict, top_k: int = 50
    ) -> list[dict]:
        """Find similar products using vector embeddings."""
        # Build query embedding from user preferences
        query_text = self._build_preference_query(profile, analysis)
        query_embedding = await self._get_embedding(query_text)

        # Search vector store
        results = self.vector_store.similarity_search(
            vector=query_embedding,
            top_k=top_k,
            filter={"in_stock": True, "is_active": True},
        )

        return [
            {
                "product_id": r.metadata["product_id"],
                "name": r.metadata["name"],
                "category": r.metadata["category"],
                "price": r.metadata["price"],
                "score": r.score,
                "source": "vector_similarity",
                "metadata": r.metadata,
            }
            for r in results
        ]

    async def _collaborative_filtering(self, profile: dict, top_k: int = 30) -> list[dict]:
        """Get recommendations from similar users (collaborative filtering)."""
        segment = profile.get("segment", {}).get("segment_name", "new_prospect")

        # Query pre-computed CF recommendations from feature store
        cf_key = f"cf_recs:{segment}:{profile['user_id']}"
        cached = await self.cache.get(cf_key)

        if cached:
            return json.loads(cached)

        # Fallback: query from feature store
        cf_recs = await self.feature_store.get_online_features(
            features=["cf:recommended_products"],
            entity_rows=[{"user_id": profile["user_id"]}],
        )

        return [
            {
                "product_id": pid,
                "source": "collaborative_filtering",
                "score": score,
            }
            for pid, score in zip(
                cf_recs["product_ids"], cf_recs["scores"]
            )
        ][:top_k]

    async def _rank_candidates(
        self, candidates: list[dict], profile: dict, analysis: dict
    ) -> list[dict]:
        """Rank candidates using LLM with structured output."""
        # Prepare candidate summary for LLM
        candidate_summary = [
            {
                "product_id": c["product_id"],
                "name": c.get("name", ""),
                "category": c.get("category", ""),
                "price": c.get("price", 0),
                "source": c.get("source", ""),
                "base_score": c.get("score", 0.5),
            }
            for c in candidates[:100]  # Limit for LLM context
        ]

        ranking_prompt = f"""You are a product recommendation ranking engine.
        Rank the following candidate products for this user.

        User profile:
        - Segment: {analysis['segment']['segment_name']}
        - Intent: {analysis['intent']['intent']}
        - Top categories: {dict(sorted(analysis['category_affinity'].items(), key=lambda x: -x[1])[:3])}
        - Price sensitivity: {analysis['price_sensitivity']['level']}
        - Purchase propensity: {analysis['purchase_propensity']['likelihood']}

        Candidates (JSON):
        {json.dumps(candidate_summary, indent=2)}

        Rank these products from 1 (best) to {len(candidate_summary)} (worst).
        Consider: relevance to user preferences, intent match, price appropriateness,
        diversity of categories, and predicted conversion likelihood.

        Return JSON array of ranked product IDs with scores (0-1) and brief reasons:
        [{{"product_id": "...", "rank": 1, "score": 0.95, "reason": "..."}}]"""

        response = await self.llm.ainvoke(ranking_prompt)
        ranked = json.loads(response.content)

        # Merge with full candidate data
        candidate_map = {c["product_id"]: c for c in candidates}
        enriched = []
        for r in ranked:
            full = candidate_map.get(r["product_id"], {})
            enriched.append({**full, **r})

        return sorted(enriched, key=lambda x: x["rank"])

    def _apply_diversity(
        self, ranked: list[dict], max_results: int = 20
    ) -> list[dict]:
        """Apply MMR (Maximal Marginal Relevance) for diversity."""
        selected = []
        category_counts = defaultdict(int)

        for item in ranked:
            if len(selected) >= max_results:
                break

            cat = item.get("category", "unknown")

            # Diversity penalty: limit same-category items
            if category_counts[cat] >= 3:
                continue

            # Calculate MMR score
            relevance = item.get("score", 0.5)
            diversity_penalty = category_counts[cat] * 0.1
            mmr_score = relevance - diversity_penalty

            selected.append({**item, "mmr_score": mmr_score})
            category_counts[cat] += 1

        return selected

    async def _generate_explanations(
        self, recommendations: list[dict], profile: dict, analysis: dict
    ) -> list[dict]:
        """Generate human-readable explanations for each recommendation."""
        explanations = []
        for rec in recommendations:
            prompt = f"""Generate a brief, personalized explanation (max 15 words) 
            for why this product is recommended:
            
            Product: {rec.get('name', 'Unknown')} (${rec.get('price', 0)})
            Category: {rec.get('category', 'Unknown')}
            User segment: {analysis['segment']['segment_name']}
            User intent: {analysis['intent']['intent']}
            Reason from ranking: {rec.get('reason', '')}
            
            Make it sound natural and helpful. No marketing fluff."""

            response = await self.llm.ainvoke(prompt)
            explanations.append({
                **rec,
                "explanation": response.content.strip(),
            })

        return explanations

    def _build_preference_query(self, profile: dict, analysis: dict) -> str:
        """Build a text query representing user preferences for vector search."""
        parts = []

        # Add top categories
        top_cats = sorted(
            analysis["category_affinity"].items(), key=lambda x: -x[1]
        )[:3]
        parts.append(f"Categories: {', '.join(c for c, _ in top_cats)}")

        # Add intent
        parts.append(f"Shopping intent: {analysis['intent']['intent']}")

        # Add price range preference
        sensitivity = analysis["price_sensitivity"]["level"]
        parts.append(f"Price preference: {sensitivity}")

        # Add recent search terms
        searches = profile.get("current_session", {}).get("searches", [])
        if searches:
            parts.append(f"Recent searches: {', '.join(s.get('query', '') for s in searches[:3])}")

        return ". ".join(parts)
```

---

## 5. Cross-Sell Agent

### 5.1 Purpose

The Cross-Sell Agent identifies complementary products, bundles, and upsell opportunities based on the user's current recommendations and cart contents.

### 5.2 Cross-Sell Strategies

```python
class CrossSellAgent:
    """
    Identifies cross-sell, upsell, and bundle opportunities.
    Uses association rules, product graphs, and LLM reasoning.
    """

    def __init__(self, config: dict):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.association_rules = self._load_association_rules()
        self.product_graph = ProductGraphService(config)
        self.bundle_service = BundleService(config)

    async def run(
        self,
        user_profile: dict,
        analysis: dict,
        recommendations: list[dict],
        context: dict,
    ) -> dict:
        """Generate cross-sell opportunities."""
        start_time = time.monotonic()

        cart_items = context.get("cart_items", [])
        recommended_ids = [r["product_id"] for r in recommendations]

        # Strategy 1: Association rule-based cross-sell
        association_recs = self._association_cross_sell(
            recommended_ids, cart_items
        )

        # Strategy 2: Product graph traversal
        graph_recs = await self._graph_cross_sell(recommended_ids)

        # Strategy 3: Bundle recommendations
        bundle_recs = await self._bundle_recommendations(
            recommended_ids, cart_items
        )

        # Strategy 4: LLM-powered complementary product suggestions
        llm_recs = await self._llm_cross_sell(
            user_profile, analysis, recommendations, cart_items
        )

        # Strategy 5: Upsell opportunities
        upsell_recs = self._upsell_opportunities(recommendations, cart_items)

        # Merge and rank all cross-sell opportunities
        all_opportunities = (
            association_recs + graph_recs + bundle_recs + llm_recs + upsell_recs
        )
        ranked = self._rank_cross_sell(all_opportunities, analysis)

        latency_ms = (time.monotonic() - start_time) * 1000

        return {
            "agent": AgentType.CROSS_SELL.value,
            "user_id": user_profile["user_id"],
            "cross_sell_opportunities": ranked,
            "total_opportunities": len(ranked),
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _association_cross_sell(
        self, product_ids: list[str], cart_items: list[dict]
    ) -> list[dict]:
        """Find cross-sell items using pre-computed association rules."""
        opportunities = []
        all_items = set(product_ids + [c["product_id"] for c in cart_items])

        for item_id in all_items:
            # Look up association rules for this product
            rules = self.association_rules.get(item_id, [])
            for rule in rules:
                if rule["consequent"] not in all_items:
                    opportunities.append({
                        "product_id": rule["consequent"],
                        "source_product": item_id,
                        "type": "cross_sell",
                        "confidence": rule["confidence"],
                        "lift": rule["lift"],
                        "source": "association_rules",
                    })

        return opportunities

    async def _graph_cross_sell(self, product_ids: list[str]) -> list[dict]:
        """Traverse product relationship graph for cross-sell opportunities."""
        opportunities = []

        for pid in product_ids:
            # Get related products from graph
            related = await self.product_graph.get_related(
                pid,
                relation_types=["complementary", "accessory", "compatible"],
                max_depth=2,
            )
            for rel in related:
                opportunities.append({
                    "product_id": rel["target_id"],
                    "source_product": pid,
                    "type": "cross_sell",
                    "relationship": rel["relationship_type"],
                    "weight": rel["weight"],
                    "source": "product_graph",
                })

        return opportunities

    async def _bundle_recommendations(
        self, product_ids: list[str], cart_items: list[dict]
    ) -> list[dict]:
        """Find product bundles that include recommended items."""
        all_items = set(product_ids + [c["product_id"] for c in cart_items])
        bundles = await self.bundle_service.find_bundles_containing(all_items)

        opportunities = []
        for bundle in bundles:
            # Find items in bundle not already in recommendations/cart
            missing_items = [
                item for item in bundle["items"]
                if item["product_id"] not in all_items
            ]
            if missing_items:
                opportunities.append({
                    "product_id": bundle["bundle_id"],
                    "type": "bundle",
                    "bundle_name": bundle["name"],
                    "missing_items": missing_items,
                    "bundle_price": bundle["price"],
                    "savings": bundle.get("savings", 0),
                    "source": "bundle_service",
                })

        return opportunities

    async def _llm_cross_sell(
        self,
        profile: dict,
        analysis: dict,
        recommendations: list[dict],
        cart_items: list[dict],
    ) -> list[dict]:
        """Use LLM to suggest complementary products."""
        rec_summary = [
            {"id": r["product_id"], "name": r.get("name", ""), "category": r.get("category", "")}
            for r in recommendations[:10]
        ]
        cart_summary = [
            {"id": c["product_id"], "name": c.get("name", ""), "category": c.get("category", "")}
            for c in cart_items
        ]

        prompt = f"""Based on the user's recommended products and cart items,
        suggest complementary products that would enhance their purchase.

        User intent: {analysis['intent']['intent']}
        User segment: {analysis['segment']['segment_name']}

        Recommended products: {json.dumps(rec_summary)}
        Cart items: {json.dumps(cart_summary)}

        Suggest up to 5 complementary products. For each, provide:
        - product_id (use realistic IDs like "prod_xxxxx")
        - name
        - category
        - why_it_complements (brief explanation)
        - cross_sell_type (complementary|accessory|upgrade|consumable)

        Return JSON array."""

        response = await self.llm.ainvoke(prompt)
        suggestions = json.loads(response.content)

        return [
            {
                "product_id": s["product_id"],
                "name": s["name"],
                "category": s["category"],
                "type": s["cross_sell_type"],
                "reason": s["why_it_complements"],
                "source": "llm_suggestion",
            }
            for s in suggestions
        ]

    def _upsell_opportunities(
        self, recommendations: list[dict], cart_items: list[dict]
    ) -> list[dict]:
        """Identify upsell opportunities (premium versions of considered products)."""
        opportunities = []

        for rec in recommendations:
            # Check if there's a premium version
            premium = self._find_premium_version(rec["product_id"])
            if premium:
                price_diff = premium["price"] - rec.get("price", 0)
                if price_diff > 0 and price_diff / max(rec.get("price", 1), 1) < 0.5:
                    opportunities.append({
                        "product_id": premium["product_id"],
                        "source_product": rec["product_id"],
                        "type": "upsell",
                        "price_difference": price_diff,
                        "source": "upsell_detection",
                    })

        return opportunities

    def _rank_cross_sell(
        self, opportunities: list[dict], analysis: dict
    ) -> list[dict]:
        """Rank cross-sell opportunities by expected value."""
        scored = []
        for opp in opportunities:
            score = 0.0

            # Base score from source confidence
            if "confidence" in opp:
                score += opp["confidence"] * 0.3
            if "weight" in opp:
                score += opp["weight"] * 0.2

            # Boost for intent alignment
            if analysis["intent"]["intent"] == "purchase_ready":
                score += 0.2

            # Boost for bundles (higher AOV)
            if opp["type"] == "bundle":
                score += 0.15

            # Boost for high purchase propensity
            if analysis["purchase_propensity"]["likelihood"] == "high":
                score += 0.1

            scored.append({**opp, "cross_sell_score": min(score, 1.0)})

        return sorted(scored, key=lambda x: -x["cross_sell_score"])[:10]
```

---

## 6. Optimization Agent

### 6.1 Purpose

The Optimization Agent fine-tunes the final recommendation list by applying business rules, A/B testing variants, diversity constraints, and real-time feedback signals.

### 6.2 Optimization Logic

```python
class OptimizationAgent:
    """
    Optimizes the final recommendation list by applying:
    - Business rules and constraints
    - A/B test variant selection
    - Diversity and serendipity injection
    - Real-time feedback integration
    - Exploration vs exploitation balance
    """

    def __init__(self, config: dict):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.ab_test_service = ABTestService(config)
        self.business_rules = BusinessRuleEngine(config)
        self.feedback_service = RealTimeFeedbackService(config)

    async def run(
        self,
        user_profile: dict,
        analysis: dict,
        recommendations: list[dict],
        cross_sell: list[dict],
        context: dict,
    ) -> dict:
        """Optimize and finalize recommendations."""
        start_time = time.monotonic()

        # Step 1: Apply business rules
        filtered = self._apply_business_rules(recommendations, context)

        # Step 2: Select A/B test variant
        variant = await self._select_ab_variant(user_profile["user_id"])

        # Step 3: Apply variant-specific ranking adjustments
        adjusted = self._apply_variant_adjustments(filtered, variant)

        # Step 4: Inject diversity and serendipity
        diversified = self._inject_diversity(adjusted, analysis)

        # Step 5: Integrate real-time feedback
        final = await self._integrate_feedback(diversified, user_profile["user_id"])

        # Step 6: Merge cross-sell opportunities
        merged = self._merge_cross_sell(final, cross_sell)

        # Step 7: Final ranking with exploration
        optimized = self._exploration_exploitation_balance(merged, analysis)

        latency_ms = (time.monotonic() - start_time) * 1000

        return {
            "agent": AgentType.OPTIMIZATION.value,
            "user_id": user_profile["user_id"],
            "final_recommendations": optimized,
            "ab_variant": variant,
            "optimization_metadata": {
                "rules_applied": len(self.business_rules.active_rules),
                "diversity_score": self._compute_diversity_score(optimized),
                "exploration_ratio": 0.15,
            },
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _apply_business_rules(
        self, recommendations: list[dict], context: dict
    ) -> list[dict]:
        """Apply business constraints and rules."""
        filtered = []

        for rec in recommendations:
            # Rule 1: Exclude out-of-stock items
            if rec.get("stock_quantity", 1) <= 0:
                continue

            # Rule 2: Exclude items already purchased recently
            if self._recently_purchased(rec["product_id"], context):
                continue

            # Rule 3: Price range constraints
            if not self._price_in_range(rec.get("price", 0), context):
                continue

            # Rule 4: Category exclusions (e.g., no alcohol for underage users)
            if self._category_excluded(rec.get("category"), context):
                continue

            # Rule 5: Margin-based boosting
            margin = rec.get("margin", 0)
            rec["business_score"] = self._compute_business_score(rec, margin)

            filtered.append(rec)

        return filtered

    async def _select_ab_variant(self, user_id: str) -> dict:
        """Select A/B test variant for this user."""
        # Check active experiments
        experiments = await self.ab_test_service.get_active_experiments(
            user_id=user_id
        )

        variant = {"experiment_id": None, "variant": "control"}

        for exp in experiments:
            # Deterministic assignment based on user_id hash
            bucket = hash(f"{user_id}:{exp['id']}") % 100
            if bucket < exp["traffic_allocation"]:
                variant = {
                    "experiment_id": exp["id"],
                    "variant": exp["variant_name"],
                    "parameters": exp.get("parameters", {}),
                }
                break

        return variant

    def _apply_variant_adjustments(
        self, recommendations: list[dict], variant: dict
    ) -> list[dict]:
        """Apply A/B test variant-specific adjustments."""
        params = variant.get("parameters", {})

        # Example: Variant boosts certain categories
        if "category_boost" in params:
            boost_cats = params["category_boost"]
            for rec in recommendations:
                if rec.get("category") in boost_cats:
                    rec["score"] = rec.get("score", 0.5) * (1 + boost_cats[rec["category"]])

        # Example: Variant changes ranking strategy
        if params.get("ranking_strategy") == "margin_optimized":
            recommendations = sorted(
                recommendations,
                key=lambda x: x.get("margin", 0) * x.get("score", 0.5),
                reverse=True,
            )

        return recommendations

    def _inject_diversity(
        self, recommendations: list[dict], analysis: dict
    ) -> list[dict]:
        """Inject diversity using MMR and serendipity."""
        # MMR-based re-ranking
        selected = []
        lambda_param = 0.7  # Balance between relevance and diversity

        candidates = list(recommendations)
        while candidates and len(selected) < 20:
            best_mmr_score = -1
            best_idx = 0

            for i, item in enumerate(candidates):
                relevance = item.get("score", 0.5)

                # Compute max similarity to already selected items
                max_sim = 0
                for sel in selected:
                    sim = self._item_similarity(item, sel)
                    max_sim = max(max_sim, sim)

                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim

                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_idx = i

            selected.append(candidates.pop(best_idx))

        # Inject serendipity: add 2 unexpected items
        serendipity_items = self._get_serendipity_picks(analysis, selected)
        selected.extend(serendipity_items)

        return selected

    async def _integrate_feedback(
        self, recommendations: list[dict], user_id: str
    ) -> list[dict]:
        """Integrate real-time feedback signals."""
        # Get recent feedback for this user
        feedback = await self.feedback_service.get_recent_feedback(user_id)

        for rec in recommendations:
            pid = rec["product_id"]

            # Downrank items the user has dismissed
            if pid in feedback.get("dismissed", []):
                rec["score"] *= 0.3

            # Boost items similar to recently liked items
            if pid in feedback.get("liked_similar", []):
                rec["score"] *= 1.3

            # Downrank items from categories the user has ignored
            if rec.get("category") in feedback.get("ignored_categories", []):
                rec["score"] *= 0.5

        return sorted(recommendations, key=lambda x: -x.get("score", 0))

    def _merge_cross_sell(
        self, recommendations: list[dict], cross_sell: list[dict]
    ) -> list[dict]:
        """Merge cross-sell opportunities into the recommendation list."""
        merged = list(recommendations)

        for cs in cross_sell[:5]:  # Top 5 cross-sell items
            # Insert cross-sell items at strategic positions
            insert_pos = min(len(merged), 5)  # Insert near top
            merged.insert(insert_pos, {
                **cs,
                "is_cross_sell": True,
                "display_position": "inline",
            })

        return merged

    def _exploration_exploitation_balance(
        self, recommendations: list[dict], analysis: dict
    ) -> list[dict]:
        """Balance exploration (new items) with exploitation (known good items)."""
        exploration_ratio = 0.15  # 15% exploration

        n_explore = int(len(recommendations) * exploration_ratio)
        n_exploit = len(recommendations) - n_explore

        # Exploitation: top-ranked items
        exploit_items = recommendations[:n_exploit]

        # Exploration: items from less-represented categories
        explore_items = self._get_exploration_items(
            analysis, n_explore, exploit_items
        )

        # Interleave exploration items
        final = []
        for i, item in enumerate(exploit_items):
            final.append(item)
            if i % 4 == 3 and explore_items:  # Every 4th position
                final.append(explore_items.pop(0))

        return final

    def _compute_diversity_score(self, recommendations: list[dict]) -> float:
        """Compute intra-list diversity score."""
        categories = [r.get("category") for r in recommendations]
        unique_cats = len(set(categories))
        return unique_cats / max(len(categories), 1)

    def _item_similarity(self, item1: dict, item2: dict) -> float:
        """Compute similarity between two items."""
        # Simple category-based similarity
        if item1.get("category") == item2.get("category"):
            return 0.8
        # Price similarity
        p1 = item1.get("price", 0)
        p2 = item2.get("price", 0)
        if max(p1, p2) > 0:
            price_sim = 1 - abs(p1 - p2) / max(p1, p2)
            return price_sim * 0.2
        return 0.0
```

---

## 7. Performance Analytics Agent

### 7.1 Purpose

The Performance Analytics Agent monitors all agents, collects metrics, detects anomalies, and provides feedback for continuous improvement.

### 7.2 Analytics Implementation

```python
from prometheus_client import Counter, Histogram, Gauge
import structlog

logger = structlog.get_logger()

class PerformanceAnalyticsAgent:
    """
    Monitors agent performance, collects metrics, detects anomalies,
    and provides actionable insights for system optimization.
    """

    def __init__(self, config: dict):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.metrics_store = MetricsStore(config)
        self.alert_manager = AlertManager(config)

        # Prometheus metrics
        self.recommendation_counter = Counter(
            "recommendations_generated_total",
            "Total recommendations generated",
            ["agent", "status"],
        )
        self.latency_histogram = Histogram(
            "agent_latency_seconds",
            "Agent processing latency",
            ["agent"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
        )
        self.quality_gauge = Gauge(
            "recommendation_quality_score",
            "Quality score of recommendations",
            ["agent"],
        )

    async def run(
        self,
        agent_outputs: dict[str, dict],
        user_id: str,
        session_id: str,
    ) -> dict:
        """Collect and analyze performance metrics from all agents."""
        start_time = time.monotonic()

        # Step 1: Collect metrics from all agents
        metrics = self._collect_agent_metrics(agent_outputs)

        # Step 2: Compute aggregate KPIs
        kpis = self._compute_kpis(metrics)

        # Step 3: Detect anomalies
        anomalies = self._detect_anomalies(metrics)

        # Step 4: Generate performance report
        report = await self._generate_report(metrics, kpis, anomalies)

        # Step 5: Send alerts if needed
        if anomalies:
            await self._send_alerts(anomalies)

        # Step 6: Store metrics for historical analysis
        await self._store_metrics(user_id, session_id, metrics, kpis)

        latency_ms = (time.monotonic() - start_time) * 1000

        return {
            "agent": AgentType.ANALYTICS.value,
            "user_id": user_id,
            "session_id": session_id,
            "metrics": metrics,
            "kpis": kpis,
            "anomalies": anomalies,
            "report": report,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _collect_agent_metrics(self, outputs: dict[str, dict]) -> dict:
        """Collect metrics from each agent's output."""
        metrics = {}

        for agent_name, output in outputs.items():
            metrics[agent_name] = {
                "latency_ms": output.get("latency_ms", 0),
                "success": "error" not in output,
                "output_size": len(json.dumps(output)),
                "timestamp": output.get("timestamp"),
            }

            # Agent-specific metrics
            if agent_name == "recommendation":
                metrics[agent_name]["candidate_count"] = output.get("candidate_count", 0)
                metrics[agent_name]["recommendation_count"] = len(
                    output.get("recommendations", [])
                )
            elif agent_name == "cross_sell":
                metrics[agent_name]["opportunity_count"] = output.get(
                    "total_opportunities", 0
                )

        return metrics

    def _compute_kpis(self, metrics: dict) -> dict:
        """Compute key performance indicators."""
        total_latency = sum(m["latency_ms"] for m in metrics.values())
        agent_count = len(metrics)
        success_rate = sum(1 for m in metrics.values() if m["success"]) / max(agent_count, 1)

        # Recommendation-specific KPIs
        rec_metrics = metrics.get("recommendation", {})
        cross_sell_metrics = metrics.get("cross_sell", {})

        kpis = {
            "total_latency_ms": total_latency,
            "agent_count": agent_count,
            "success_rate": success_rate,
            "avg_agent_latency_ms": total_latency / max(agent_count, 1),
            "p95_latency_ms": self._compute_p95_latency(metrics),
            "recommendation_count": rec_metrics.get("recommendation_count", 0),
            "candidate_count": rec_metrics.get("candidate_count", 0),
            "cross_sell_opportunities": cross_sell_metrics.get("opportunity_count", 0),
            "end_to_end_latency_ms": total_latency,
        }

        # Update Prometheus metrics
        self.latency_histogram.labels(agent="total").observe(total_latency / 1000)
        self.recommendation_counter.labels(
            agent="recommendation", status="success" if success_rate == 1.0 else "partial"
        ).inc()

        return kpis

    def _detect_anomalies(self, metrics: dict) -> list[dict]:
        """Detect performance anomalies."""
        anomalies = []

        for agent_name, agent_metrics in metrics.items():
            latency = agent_metrics.get("latency_ms", 0)

            # Latency anomaly
            if latency > 1000:  # > 1 second
                anomalies.append({
                    "type": "high_latency",
                    "agent": agent_name,
                    "value": latency,
                    "threshold": 1000,
                    "severity": "warning" if latency < 2000 else "critical",
                })

            # Failure anomaly
            if not agent_metrics.get("success", True):
                anomalies.append({
                    "type": "agent_failure",
                    "agent": agent_name,
                    "severity": "critical",
                })

        return anomalies

    async def _generate_report(
        self, metrics: dict, kpis: dict, anomalies: list[dict]
    ) -> dict:
        """Generate a natural language performance report."""
        prompt = f"""Generate a concise performance report for the recommendation system.

        Metrics: {json.dumps(metrics, indent=2)}
        KPIs: {json.dumps(kpis, indent=2)}
        Anomalies: {json.dumps(anomalies, indent=2)}

        Provide:
        1. Executive summary (2-3 sentences)
        2. Key findings (bullet points)
        3. Recommendations for improvement (if any)

        Keep it concise and actionable."""

        response = await self.llm.ainvoke(prompt)

        return {
            "summary": response.content,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _send_alerts(self, anomalies: list[dict]):
        """Send alerts for critical anomalies."""
        for anomaly in anomalies:
            if anomaly["severity"] == "critical":
                await self.alert_manager.send_alert(
                    channel="pagerduty",
                    title=f"Recommendation System Anomaly: {anomaly['type']}",
                    description=json.dumps(anomaly),
                    severity="critical",
                )

    async def _store_metrics(
        self, user_id: str, session_id: str, metrics: dict, kpis: dict
    ):
        """Store metrics for historical analysis and model training."""
        await self.metrics_store.store({
            "user_id": user_id,
            "session_id": session_id,
            "metrics": metrics,
            "kpis": kpis,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def _compute_p95_latency(self, metrics: dict) -> float:
        """Compute P95 latency across all agents."""
        latencies = sorted(m["latency_ms"] for m in metrics.values())
        if not latencies:
            return 0
        idx = int(len(latencies) * 0.95)
        return latencies[min(idx, len(latencies) - 1)]
```

### 7.3 Dashboard Metrics

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| End-to-end latency | Total time for all agents | < 2s | > 5s |
| Recommendation relevance | CTR on recommendations | > 8% | < 3% |
| Conversion rate | Purchase from recommendations | > 5% | < 2% |
| Diversity score | Category diversity in results | > 0.6 | < 0.3 |
| Agent success rate | % of successful agent runs | > 99% | < 95% |
| Cache hit rate | % of cached recommendations | > 40% | < 20% |

---

## 8. Code Examples and Snippets

### 8.1 Complete Pipeline Integration

```python
# main.py - Complete recommendation pipeline
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

app = FastAPI(title="AI Product Recommendations")

# Global agent instances
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    # Initialize all agents
    config = load_config()
    orchestrator = RecommendationOrchestrator(config)
    yield
    # Cleanup
    await orchestrator.shutdown()

app = FastAPI(lifespan=lifespan)

@app.post("/api/v1/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """
    Main endpoint for getting personalized product recommendations.
    """
    context = {
        "cart_items": request.cart_items,
        "current_page": request.current_page,
        "session_duration_sec": request.session_duration_sec,
        "device_type": request.device_type,
    }

    result = await orchestrator.recommend(
        user_id=request.user_id,
        session_id=request.session_id,
        context=context,
    )

    return {
        "recommendations": result["recommendations"],
        "metadata": result["metadata"],
    }

@app.get("/api/v1/recommendations/{user_id}/feedback")
async def submit_feedback(
    user_id: str,
    product_id: str,
    feedback_type: str,  # "click", "dismiss", "purchase", "wishlist"
):
    """Collect user feedback for real-time optimization."""
    await orchestrator.feedback_service.record_feedback(
        user_id=user_id,
        product_id=product_id,
        feedback_type=feedback_type,
    )
    return {"status": "recorded"}
```

### 8.2 Docker Compose Setup

```yaml
# docker-compose.yml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - REDIS_URL=redis://redis:6379
      - KAFKA_BROKER=kafka:9092
    depends_on:
      - redis
      - kafka
      - pinecone

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  kafka:
    image: confluentinc/cp-kafka:latest
    ports:
      - "9092:9092"
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
```

### 8.3 Configuration Management

```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str
    pinecone_api_key: str
    pinecone_environment: str = "us-east-1"
    pinecone_index: str = "product-recommendations"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Kafka
    kafka_broker: str = "localhost:9092"
    kafka_topic_events: str = "user-events"
    kafka_topic_recommendations: str = "recommendations"

    # Model Settings
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.2
    embedding_model: str = "text-embedding-3-small"

    # Recommendation Settings
    max_recommendations: int = 20
    candidate_pool_size: int = 100
    diversity_lambda: float = 0.7
    exploration_ratio: float = 0.15
    cache_ttl_seconds: int = 300

    # Feature Store
    feast_repo_path: str = "./feature_repo"

    # Monitoring
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    prometheus_port: int = 9090

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 8.4 Event-Driven Architecture

```python
# events.py - Kafka event producers and consumers
from confluent_kafka import Producer, Consumer, KafkaError
import json

class EventProducer:
    """Produces events to Kafka for inter-agent communication."""

    def __init__(self, bootstrap_servers: str):
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "client.id": "recommendation-system",
        })

    def send_event(self, topic: str, event: dict):
        self.producer.produce(
            topic,
            key=event.get("user_id", ""),
            value=json.dumps(event),
            callback=self._delivery_callback,
        )
        self.producer.poll(0)

    def _delivery_callback(self, err, msg):
        if err:
            logger.error(f"Message delivery failed: {err}")

class EventConsumer:
    """Consumes events from Kafka."""

    def __init__(self, bootstrap_servers: str, group_id: str, topics: list[str]):
        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "latest",
        })
        self.consumer.subscribe(topics)

    async def consume(self, handler):
        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise Exception(msg.error())

            event = json.loads(msg.value())
            await handler(event)
```

### 8.5 Caching Strategy

```python
# cache.py - Multi-layer caching
import hashlib
import json
from typing import Optional

class RecommendationCache:
    """
    Multi-layer caching:
    1. L1: In-memory LRU cache (fastest, smallest)
    2. L2: Redis cache (fast, shared across instances)
    3. L3: Pre-computed recommendations (fallback)
    """

    def __init__(self, redis_client, l1_size: int = 1000):
        self.l1_cache = {}  # Simple dict with LRU eviction
        self.l1_size = l1_size
        self.redis = redis_client
        self.l1_access_order = []

    def _make_key(self, user_id: str, context_hash: str) -> str:
        return f"recs:{user_id}:{context_hash}"

    def _hash_context(self, context: dict) -> str:
        """Create a hash of relevant context for cache key."""
        relevant = {
            "cart_count": len(context.get("cart_items", [])),
            "cart_value": context.get("cart_value", 0),
            "current_page": context.get("current_page", ""),
            "device_type": context.get("device_type", ""),
        }
        return hashlib.md5(
            json.dumps(relevant, sort_keys=True).encode()
        ).hexdigest()[:12]

    async def get(self, user_id: str, context: dict) -> Optional[list]:
        context_hash = self._hash_context(context)
        key = self._make_key(user_id, context_hash)

        # L1 check
        if key in self.l1_cache:
            self._update_l1_access(key)
            return self.l1_cache[key]

        # L2 check
        cached = await self.redis.get(key)
        if cached:
            result = json.loads(cached)
            self._set_l1(key, result)
            return result

        return None

    async def set(
        self, user_id: str, context: dict, recommendations: list, ttl: int = 300
    ):
        context_hash = self._hash_context(context)
        key = self._make_key(user_id, context_hash)

        # Set L1
        self._set_l1(key, recommendations)

        # Set L2
        await self.redis.setex(key, ttl, json.dumps(recommendations))

    def _set_l1(self, key: str, value: list):
        if len(self.l1_cache) >= self.l1_size:
            # Evict least recently used
            evict_key = self.l1_access_order.pop(0)
            self.l1_cache.pop(evict_key, None)

        self.l1_cache[key] = value
        self._update_l1_access(key)

    def _update_l1_access(self, key: str):
        if key in self.l1_access_order:
            self.l1_access_order.remove(key)
        self.l1_access_order.append(key)
```

---

## 9. Testing Strategy

### 9.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5 tests)
                    │  Tests  │
                   ┌┴─────────┴┐
                   │ Integration│  (20 tests)
                   │   Tests    │
                  ┌┴────────────┴┐
                  │    Unit       │  (100+ tests)
                  │    Tests      │
                 ┌┴───────────────┴┐
                 │  Contract Tests  │  (15 tests)
                 │  (Pact/Schema)   │
                 └──────────────────┘
```

### 9.2 Unit Tests

```python
# tests/test_data_collection_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_db_pool():
    pool = AsyncMock()
    conn = AsyncMock()
    conn.fetchrow.return_value = {
        "user_id": "usr_123",
        "age_group": "25-34",
        "location": "US-NY",
    }
    pool.acquire.return_value.__aenter__.return_value = conn
    return pool

@pytest.mark.asyncio
async def test_data_collection_agent_fetches_profile(mock_db_pool):
    agent = DataCollectionAgent({"db_pool": mock_db_pool})
    result = await agent.run("usr_123", "sess_456")

    assert result["agent"] == "data_collection"
    assert result["user_id"] == "usr_123"
    assert result["latency_ms"] > 0
    assert "output" in result

@pytest.mark.asyncio
async def test_data_collection_handles_missing_user():
    pool = AsyncMock()
    conn = AsyncMock()
    conn.fetchrow.return_value = None
    pool.acquire.return_value.__aenter__.return_value = conn

    agent = DataCollectionAgent({"db_pool": pool})
    result = await agent.run("nonexistent", "sess_456")

    assert result["data_quality"]["completeness"] < 0.5

# tests/test_recommendation_agent.py
@pytest.mark.asyncio
async def test_recommendation_agent_returns_ranked_list():
    agent = RecommendationAgent(mock_config)
    profile = create_test_profile()
    analysis = create_test_analysis()

    result = await agent.run(profile, analysis, {})

    assert len(result["recommendations"]) > 0
    assert all("explanation" in r for r in result["recommendations"])
    assert result["candidate_count"] >= len(result["recommendations"])

@pytest.mark.asyncio
async def test_recommendation_diversity():
    agent = RecommendationAgent(mock_config)
    profile = create_test_profile()
    analysis = create_test_analysis()

    result = await agent.run(profile, analysis, {})
    categories = [r["category"] for r in result["recommendations"]]
    unique_ratio = len(set(categories)) / len(categories)

    assert unique_ratio > 0.3  # At least 30% category diversity
```

### 9.3 Integration Tests

```python
# tests/integration/test_full_pipeline.py
import pytest
import asyncio

@pytest.mark.asyncio
async def test_end_to_end_recommendation_pipeline():
    """Test the complete multi-agent pipeline."""
    # Setup
    config = load_test_config()
    orchestrator = RecommendationOrchestrator(config)

    # Execute
    result = await orchestrator.recommend(
        user_id="test_user_001",
        session_id="test_session_001",
        context={
            "cart_items": [{"product_id": "prod_123", "price": 99.99}],
            "current_page": "electronics",
            "session_duration_sec": 300,
        },
    )

    # Assert
    assert "recommendations" in result
    assert len(result["recommendations"]) > 0
    assert len(result["recommendations"]) <= 20

    # Verify all agents ran
    agent_types = {r.get("agent") for r in result.get("agent_outputs", [])}
    expected_agents = {
        "data_collection", "analysis", "recommendation",
        "cross_sell", "optimization", "analytics"
    }
    assert expected_agents.issubset(agent_types)

    # Verify latency SLA
    assert result["metadata"]["total_latency_ms"] < 5000  # 5 second SLA

@pytest.mark.asyncio
async def test_recommendation_with_empty_cart():
    """Test recommendations when user has no cart items."""
    orchestrator = RecommendationOrchestrator(load_test_config())

    result = await orchestrator.recommend(
        user_id="test_user_002",
        session_id="test_session_002",
        context={"cart_items": [], "current_page": "home"},
    )

    assert len(result["recommendations"]) > 0
    # Should still return recommendations based on browsing history

@pytest.mark.asyncio
async def test_cold_start_user():
    """Test recommendations for a new user with no history."""
    orchestrator = RecommendationOrchestrator(load_test_config())

    result = await orchestrator.recommend(
        user_id="brand_new_user",
        session_id="test_session_003",
        context={"cart_items": [], "current_page": "home"},
    )

    # Should return popular/trending items
    assert len(result["recommendations"]) > 0
```

### 9.4 Contract Tests

```python
# tests/contract/test_api_contracts.py
import pytest
from pact import Consumer, Provider

@pytest.fixture
def pact():
    return Consumer("recommendation-client").has_pact_with(
        Provider("recommendation-service"),
        pact_dir="./pacts",
    )

def test_get_recommendations_contract(pact):
    """Verify the recommendations API contract."""
    expected = {
        "recommendations": [
            {
                "product_id": "prod_123",
                "name": "Test Product",
                "price": 99.99,
                "category": "electronics",
                "explanation": "Recommended because...",
                "score": 0.95,
            }
        ],
        "metadata": {
            "total_latency_ms": 1500,
            "ab_variant": "control",
        },
    }

    (pact
     .given("user exists with profile")
     .upon_receiving("a request for recommendations")
     .with_request("POST", "/api/v1/recommendations", body={
         "user_id": "usr_123",
         "session_id": "sess_456",
         "context": {},
     })
     .will_respond_with(200, body=expected))

    with pact:
        result = requests.post(
            f"{pact.uri}/api/v1/recommendations",
            json={"user_id": "usr_123", "session_id": "sess_456", "context": {}},
        )
        assert result.status_code == 200
        assert "recommendations" in result.json()
```

### 9.5 Load Testing

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between
import random
import json

class RecommendationUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.user_ids = [f"load_test_user_{i}" for i in range(1000)]

    @task(10)
    def get_recommendations(self):
        user_id = random.choice(self.user_ids)
        self.client.post(
            "/api/v1/recommendations",
            json={
                "user_id": user_id,
                "session_id": f"load_session_{random.randint(1, 10000)}",
                "context": {
                    "cart_items": [],
                    "current_page": random.choice(["home", "electronics", "clothing"]),
                    "session_duration_sec": random.randint(30, 600),
                },
            },
            timeout=10,
        )

    @task(3)
    def get_recommendations_with_cart(self):
        user_id = random.choice(self.user_ids)
        self.client.post(
            "/api/v1/recommendations",
            json={
                "user_id": user_id,
                "session_id": f"load_session_{random.randint(1, 10000)}",
                "context": {
                    "cart_items": [
                        {"product_id": f"prod_{random.randint(1, 1000)}", "price": 49.99}
                    ],
                    "current_page": "cart",
                    "session_duration_sec": 300,
                },
            },
            timeout=10,
        )

    @task(1)
    def submit_feedback(self):
        self.client.post(
            f"/api/v1/recommendations/{random.choice(self.user_ids)}/feedback",
            params={
                "product_id": f"prod_{random.randint(1, 1000)}",
                "feedback_type": random.choice(["click", "dismiss", "purchase"]),
            },
        )
```

### 9.6 Evaluation Framework

```python
# tests/evaluation/test_recommendation_quality.py
import numpy as np
from sklearn.metrics import ndcg_score, precision_score, recall_score

class RecommendationEvaluator:
    """
    Evaluates recommendation quality using offline metrics.
    """

    def __init__(self, test_data_path: str):
        self.test_data = self._load_test_data(test_data_path)

    def evaluate(self, recommendations: list[dict], ground_truth: list[str]) -> dict:
        """Compute recommendation quality metrics."""
        rec_ids = [r["product_id"] for r in recommendations]

        return {
            "precision@5": self._precision_at_k(rec_ids, ground_truth, 5),
            "precision@10": self._precision_at_k(rec_ids, ground_truth, 10),
            "recall@10": self._recall_at_k(rec_ids, ground_truth, 10),
            "ndcg@10": self._ndcg_at_k(rec_ids, ground_truth, 10),
            "mrr": self._mean_reciprocal_rank(rec_ids, ground_truth),
            "coverage": self._catalog_coverage(rec_ids),
            "diversity": self._intra_list_diversity(recommendations),
        }

    def _precision_at_k(self, recs: list[str], truth: list[str], k: int) -> float:
        if not recs[:k]:
            return 0.0
        return len(set(recs[:k]) & set(truth)) / k

    def _recall_at_k(self, recs: list[str], truth: list[str], k: int) -> float:
        if not truth:
            return 0.0
        return len(set(recs[:k]) & set(truth)) / len(truth)

    def _ndcg_at_k(self, recs: list[str], truth: list[str], k: int) -> float:
        y_true = [[1 if r in truth else 0 for r in recs[:k]]]
        y_score = [[1.0 / (i + 1) for i in range(len(recs[:k]))]]
        return ndcg_score(y_true, y_score)

    def _mean_reciprocal_rank(self, recs: list[str], truth: list[str]) -> float:
        for i, r in enumerate(recs):
            if r in truth:
                return 1.0 / (i + 1)
        return 0.0

    def _catalog_coverage(self, recs: list[str]) -> float:
        """Percentage of catalog items that appear in recommendations."""
        all_items = set(self.test_data["all_product_ids"])
        return len(set(recs) & all_items) / len(all_items)

    def _intra_list_diversity(self, recommendations: list[dict]) -> float:
        """Compute diversity based on category distribution."""
        categories = [r.get("category") for r in recommendations]
        unique = len(set(categories))
        return unique / max(len(categories), 1)
```

### 9.7 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Recommendation System Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pip install -r requirements-test.txt
      - run: pytest tests/unit -v --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports: ["6379:6379"]
      kafka:
        image: confluentinc/cp-kafka:latest
        ports: ["9092:9092"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/integration -v

  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pact-python
      - run: pytest tests/contract -v

  load-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: pip install locust
      - run: locust -f tests/load/locustfile.py --headless -u 100 -r 10 --run-time 5m
```

---

## Appendix A: Deployment Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        CDN (CloudFront)                       │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    API Gateway (Kong/AWS)                     │
│              Rate Limiting, Auth, Request Routing             │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│              Kubernetes Cluster (EKS/GKE)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  API Pods   │  │  API Pods   │  │  API Pods   │  (HPA)   │
│  │  (FastAPI)  │  │  (FastAPI)  │  │  (FastAPI)  │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                   │
│  ┌──────▼────────────────▼────────────────▼──────┐          │
│  │           Redis Cluster (Cache)               │          │
│  └───────────────────────────────────────────────┘          │
│  ┌───────────────────────────────────────────────┐          │
│  │        Kafka Cluster (Event Streaming)         │          │
│  └───────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│              Data Layer                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │PostgreSQL│  │ Pinecone │  │  Feast   │  │ClickHouse│    │
│  │ (Users,  │  │(Vectors) │  │(Features)│  │ (Events) │    │
│  │ Orders)  │  │          │  │          │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└──────────────────────────────────────────────────────────────┘
```

## Appendix B: Environment Variables

```bash
# .env.example
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pc-...
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX=product-recommendations
REDIS_URL=redis://localhost:6379
KAFKA_BROKER=localhost:9092
DATABASE_URL=postgresql://user:pass@localhost:5432/recommendations
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
PROMETHEUS_PORT=9092
LOG_LEVEL=INFO
ENVIRONMENT=development
```

---

*End of Implementation Plan*
