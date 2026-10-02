# AI-Powered Feedback & Review Management — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a multi-agent system using LangChain DeepAgents that autonomously collects, analyzes, responds to, and acts on customer feedback and reviews across all channels, with continuous performance monitoring.

**Architecture:** Five specialized DeepAgents orchestrated by a central coordinator. Each agent has a single responsibility, custom tools, and a system prompt defining its role. Agents communicate via a shared state store (Redis) and structured message passing. The coordinator routes tasks, resolves conflicts, and maintains conversation context.

**Tech Stack:** LangChain DeepAgents, Python 3.11+, Redis, FastAPI, PostgreSQL, OpenAI GPT-4o, pytest, Docker

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Collection Agent](#2-collection-agent)
3. [Analysis Agent](#3-analysis-agent)
4. [Response Agent](#4-response-agent)
5. [Action Agent](#5-action-agent)
6. [Performance Analytics Agent](#6-performance-analytics-agent)
7. [Code Examples & Snippets](#7-code-examples--snippets)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordinator Agent                         │
│  (Routes tasks, resolves conflicts, maintains context)      │
└────────┬──────────┬──────────┬──────────┬──────────┬────────┘
         │          │          │          │          │
    ┌────▼────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼─────┐
    │Collect  │ │Analyze │ │Respond │ │ Action  │ │Analytics│
    │ Agent   │ │ Agent  │ │ Agent  │ │ Agent  │ │ Agent   │
    └────┬────┘ └──┬─────┘ └──┬─────┘ └──┬─────┘ └──┬─────┘
         │          │          │          │          │
    ┌────▼──────────▼──────────▼──────────▼──────────▼────┐
    │              Shared State (Redis + PostgreSQL)        │
    └──────────────────────────────────────────────────────┘
```

### 1.2 Agent Definitions

```python
# src/agents/base.py
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from enum import Enum
from typing import Any
import redis
import json
import uuid
from datetime import datetime


class AgentRole(str, Enum):
    COORDINATOR = "coordinator"
    COLLECTOR = "collector"
    ANALYZER = "analyzer"
    RESPONDER = "responder"
    ACTOR = "actor"
    ANALYST = "analyst"


class FeedbackItem(BaseModel):
    """Unified feedback data model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str  # email, chat, social, survey, review_site, support_ticket
    channel: str  # g2, trustpilot, google, email, zendesk, intercom
    customer_id: str
    customer_name: str
    customer_email: str | None = None
    content: str
    rating: int | None = None  # 1-5 scale
    metadata: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "new"  # new, analyzed, responded, actioned, closed
    priority: str = "medium"  # low, medium, high, critical
    sentiment: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    analysis: dict[str, Any] = Field(default_factory=dict)
    response: str | None = None
    actions: list[dict[str, Any]] = Field(default_factory=list)


class AgentMessage(BaseModel):
    """Inter-agent communication protocol."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: AgentRole
    recipient: AgentRole
    message_type: str  # task, result, alert, escalation
    payload: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str | None = None  # links related messages


class SharedState:
    """Redis-backed shared state store for inter-agent communication."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.feedback_prefix = "feedback:"
        self.message_queue = "agent:messages:"
        self.metrics_prefix = "metrics:"

    def store_feedback(self, item: FeedbackItem) -> str:
        key = f"{self.feedback_prefix}{item.id}"
        self.client.setex(key, 86400 * 30, item.model_dump_json())  # 30-day TTL
        return item.id

    def get_feedback(self, feedback_id: str) -> FeedbackItem | None:
        key = f"{self.feedback_prefix}{feedback_id}"
        data = self.client.get(key)
        return FeedbackItem.model_validate_json(data) if data else None

    def update_feedback(self, feedback_id: str, updates: dict[str, Any]) -> FeedbackItem | None:
        item = self.get_feedback(feedback_id)
        if not item:
            return None
        for k, v in updates.items():
            setattr(item, k, v)
        self.store_feedback(item)
        return item

    def publish_message(self, msg: AgentMessage) -> None:
        queue = f"{self.message_queue}{msg.recipient.value}"
        self.client.lpush(queue, msg.model_dump_json())

    def consume_messages(self, role: AgentRole, count: int = 10) -> list[AgentMessage]:
        queue = f"{self.message_queue}{role.value}"
        messages = []
        for _ in range(count):
            data = self.client.rpop(queue)
            if not data:
                break
            messages.append(AgentMessage.model_validate_json(data))
        return messages

    def query_feedback(self, status: str | None = None,
                       priority: str | None = None,
                       category: str | None = None,
                       limit: int = 100) -> list[FeedbackItem]:
        """Scan and filter feedback items."""
        results = []
        for key in self.client.scan_iter(match=f"{self.feedback_prefix}*", count=100):
            data = self.client.get(key)
            if not data:
                continue
            item = FeedbackItem.model_validate_json(data)
            if status and item.status != status:
                continue
            if priority and item.priority != priority:
                continue
            if category and item.category != category:
                continue
            results.append(item)
            if len(results) >= limit:
                break
        return results
```

### 1.3 Coordinator Agent

```python
# src/agents/coordinator.py
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from .base import AgentRole, AgentMessage, SharedState, FeedbackItem


def create_coordinator_agent(state: SharedState) -> DeepAgent:
    """Creates the central coordinator that routes tasks between agents."""

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    @tool
    def route_to_collector(source_config: dict) -> dict:
        """Route a collection task to the Collector agent.
        Args:
            source_config: Dict with 'channel', 'time_range', 'filters'
        Returns:
            Confirmation with task ID
        """
        msg = AgentMessage(
            sender=AgentRole.COORDINATOR,
            recipient=AgentRole.COLLECTOR,
            message_type="task",
            payload={"action": "collect", "config": source_config},
        )
        state.publish_message(msg)
        return {"status": "queued", "agent": "collector", "task": "collect"}

    @tool
    def route_to_analyzer(feedback_id: str) -> dict:
        """Route a feedback item to the Analysis agent."""
        msg = AgentMessage(
            sender=AgentRole.COORDINATOR,
            recipient=AgentRole.ANALYZER,
            message_type="task",
            payload={"action": "analyze", "feedback_id": feedback_id},
        )
        state.publish_message(msg)
        return {"status": "queued", "agent": "analyzer", "task": "analyze"}

    @tool
    def route_to_responder(feedback_id: str) -> dict:
        """Route a feedback item to the Response agent."""
        msg = AgentMessage(
            sender=AgentRole.COORDINATOR,
            recipient=AgentRole.RESPONDER,
            message_type="task",
            payload={"action": "respond", "feedback_id": feedback_id},
        )
        state.publish_message(msg)
        return {"status": "queued", "agent": "responder", "task": "respond"}

    @tool
    def route_to_actor(feedback_id: str, action_type: str) -> dict:
        """Route an action request to the Action agent."""
        msg = AgentMessage(
            sender=AgentRole.COORDINATOR,
            recipient=AgentRole.ACTOR,
            message_type="task",
            payload={"action": "execute", "feedback_id": feedback_id, "action_type": action_type},
        )
        state.publish_message(msg)
        return {"status": "queued", "agent": "actor", "task": "execute"}

    @tool
    def escalate_feedback(feedback_id: str, reason: str) -> dict:
        """Escalate a feedback item to human review."""
        state.update_feedback(feedback_id, {"priority": "critical", "status": "escalated"})
        msg = AgentMessage(
            sender=AgentRole.COORDINATOR,
            recipient=AgentRole.ANALYST,
            message_type="alert",
            payload={"alert": "escalation", "feedback_id": feedback_id, "reason": reason},
        )
        state.publish_message(msg)
        return {"status": "escalated", "feedback_id": feedback_id}

    system_prompt = """You are the Coordinator agent for a feedback management system.
    Your responsibilities:
    1. Ingest incoming feedback from any source
    2. Route tasks to the appropriate specialized agent
    3. Resolve conflicts between agent outputs
    4. Escalate critical items to human reviewers
    5. Maintain overall system health

    Decision rules:
    - Rating <= 2 OR contains urgent keywords -> priority=critical, escalate immediately
    - Rating == 3 -> priority=high
    - Rating >= 4 -> priority=medium
    - VIP customer (metadata.is_vip=true) -> bump priority one level

    Always confirm task routing with a structured response."""

    return DeepAgent(
        llm=llm,
        tools=[route_to_collector, route_to_analyzer, route_to_responder,
               route_to_actor, escalate_feedback],
        system_prompt=system_prompt,
        name="coordinator",
    )
```

---

## 2. Collection Agent

### 2.1 Responsibilities

- Poll multiple feedback sources on a schedule
- Normalize data into the unified `FeedbackItem` model
- Deduplicate submissions
- Enrich with customer metadata
- Store in shared state and forward to Analysis

### 2.2 Implementation

```python
# src/agents/collector.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_community.tools import GoogleSearchRun
from .base import AgentRole, AgentMessage, SharedState, FeedbackItem
from .connectors import (
    G2Connector, TrustpilotConnector, GoogleReviewsConnector,
    ZendeskConnector, IntercomConnector, EmailConnector, SurveyConnector
)
import hashlib
from datetime import datetime, timedelta


def create_collector_agent(state: SharedState) -> DeepAgent:
    """Creates the Collection agent that gathers feedback from all channels."""

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Initialize connectors
    connectors = {
        "g2": G2Connector(),
        "trustpilot": TrustpilotConnector(),
        "google_reviews": GoogleReviewsConnector(),
        "zendesk": ZendeskConnector(),
        "intercom": IntercomConnector(),
        "email": EmailConnector(),
        "survey": SurveyConnector(),
    }

    @tool
    def collect_from_channel(channel: str, since_minutes: int = 60) -> dict:
        """Collect feedback from a specific channel.
        Args:
            channel: One of g2, trustpilot, google_reviews, zendesk, intercom, email, survey
            since_minutes: How far back to collect
        Returns:
            Collection summary with count and IDs
        """
        if channel not in connectors:
            return {"error": f"Unknown channel: {channel}"}

        connector = connectors[channel]
        since = datetime.utcnow() - timedelta(minutes=since_minutes)
        raw_items = connector.fetch(since=since)

        collected = []
        duplicates = 0
        for raw in raw_items:
            # Deduplication via content hash
            content_hash = hashlib.sha256(
                f"{raw['customer_id']}:{raw['content'][:200]}".encode()
            ).hexdigest()

            # Check for existing
            existing = state.client.get(f"feedback:hash:{content_hash}")
            if existing:
                duplicates += 1
                continue

            # Normalize to FeedbackItem
            item = FeedbackItem(
                source=channel,
                channel=channel,
                customer_id=raw["customer_id"],
                customer_name=raw.get("customer_name", "Anonymous"),
                customer_email=raw.get("customer_email"),
                content=raw["content"],
                rating=raw.get("rating"),
                metadata={
                    "content_hash": content_hash,
                    "is_vip": raw.get("is_vip", False),
                    "raw_id": raw.get("id"),
                    "product_area": raw.get("product_area"),
                },
            )

            feedback_id = state.store_feedback(item)
            state.client.setex(f"feedback:hash:{content_hash}", 86400 * 7, feedback_id)

            # Auto-forward to analyzer
            msg = AgentMessage(
                sender=AgentRole.COLLECTOR,
                recipient=AgentRole.COORDINATOR,
                message_type="result",
                payload={"action": "collected", "feedback_id": feedback_id},
            )
            state.publish_message(msg)
            collected.append(feedback_id)

        return {
            "channel": channel,
            "collected": len(collected),
            "duplicates": duplicates,
            "feedback_ids": collected,
        }

    @tool
    def collect_all_channels(since_minutes: int = 60) -> dict:
        """Collect feedback from all configured channels."""
        results = {}
        for channel in connectors:
            results[channel] = collect_from_channel.invoke(
                {"channel": channel, "since_minutes": since_minutes}
            )
        return results

    @tool
    def enrich_customer_data(feedback_id: str) -> dict:
        """Enrich feedback item with customer metadata from CRM."""
        item = state.get_feedback(feedback_id)
        if not item:
            return {"error": "Feedback not found"}

        # Lookup customer in CRM (Salesforce/HubSpot)
        crm_data = connectors["zendesk"].get_customer_profile(item.customer_id)

        updates = {
            "metadata": {
                **item.metadata,
                "is_vip": crm_data.get("tier") in ["enterprise", "vip"],
                "customer_tenure_days": crm_data.get("tenure_days"),
                "previous_tickets": crm_data.get("open_ticket_count", 0),
                "ltv": crm_data.get("lifetime_value", 0),
            }
        }
        state.update_feedback(feedback_id, updates)
        return {"feedback_id": feedback_id, "enriched": True}

    system_prompt = """You are the Collection agent for a feedback management system.
    Your responsibilities:
    1. Fetch feedback from all connected channels
    2. Normalize data into the unified FeedbackItem format
    3. Deduplicate using content hashing
    4. Enrich with customer metadata
    5. Forward new items to the Coordinator for analysis routing

    Channels: G2, Trustpilot, Google Reviews, Zendesk, Intercom, Email, Surveys
    Collection frequency: Every 5 minutes for real-time channels, hourly for others

    Always validate data quality before storing. Flag items with missing customer IDs."""

    return DeepAgent(
        llm=llm,
        tools=[collect_from_channel, collect_all_channels, enrich_customer_data],
        system_prompt=system_prompt,
        name="collector",
    )
```

### 2.3 Connector Interface

```python
# src/agents/connectors/base.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseConnector(ABC):
    """Abstract base for all feedback source connectors."""

    @abstractmethod
    def fetch(self, since: datetime, **kwargs) -> list[dict[str, Any]]:
        """Fetch raw feedback items since the given timestamp."""
        pass

    @abstractmethod
    def get_customer_profile(self, customer_id: str) -> dict[str, Any]:
        """Fetch customer metadata from the source system."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify the connector is operational."""
        pass


# src/agents/connectors/g2.py
import requests
from .base import BaseConnector


class G2Connector(BaseConnector):
    def __init__(self):
        self.api_key = "<G2_API_KEY>"
        self.base_url = "https://api.g2.com/v2"

    def fetch(self, since: datetime, **kwargs) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/reviews",
            headers={"Authorization": f"Token {self.api_key}"},
            params={"updated_after": since.isoformat(), "per_page": 100},
            timeout=30,
        )
        resp.raise_for_status()
        return [
            {
                "id": r["id"],
                "customer_id": r["reviewer"]["id"],
                "customer_name": r["reviewer"]["name"],
                "customer_email": r["reviewer"].get("email"),
                "content": r["content"],
                "rating": r.get("rating"),
                "product_area": r.get("product_area"),
            }
            for r in resp.json().get("data", [])
        ]

    def get_customer_profile(self, customer_id: str) -> dict:
        # G2 doesn't have CRM data; return minimal
        return {"tier": "standard", "tenure_days": 0}

    def health_check(self) -> bool:
        try:
            resp = requests.get(
                f"{self.base_url}/ping",
                headers={"Authorization": f"Token {self.api_key}"},
                timeout=5,
            )
            return resp.status_code == 200
        except Exception:
            return False
```

---

## 3. Analysis Agent

### 3.1 Responsibilities

- Sentiment analysis (positive/negative/neutral + intensity)
- Topic categorization and tagging
- Priority scoring
- Trend detection and clustering
- Root cause analysis for negative feedback
- Competitive intelligence extraction

### 3.2 Implementation

```python
# src/agents/analyzer.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from .base import AgentRole, AgentMessage, SharedState, FeedbackItem
from typing import Literal


class AnalysisResult(BaseModel):
    sentiment: Literal["positive", "negative", "neutral", "mixed"]
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    category: str
    subcategory: str | None = None
    priority: Literal["low", "medium", "high", "critical"]
    tags: list[str]
    summary: str
    key_phrases: list[str]
    emotion: Literal["angry", "frustrated", "satisfied", "happy", "confused", "neutral"]
    urgency_indicators: list[str]
    suggested_actions: list[str]
    related_products: list[str]
    competitive_mentions: list[str]


def create_analyzer_agent(state: SharedState) -> DeepAgent:
    """Creates the Analysis agent that processes and categorizes feedback."""

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    CATEGORIES = [
        "product_quality", "pricing", "customer_support", "onboarding",
        "feature_request", "bug_report", "usability", "performance",
        "billing", "integration", "documentation", "security",
    ]

    @tool
    def analyze_feedback(feedback_id: str) -> dict:
        """Perform deep analysis on a feedback item.
        Args:
            feedback_id: The feedback item ID to analyze
        Returns:
            Structured analysis result
        """
        item = state.get_feedback(feedback_id)
        if not item:
            return {"error": "Feedback not found"}

        # Build analysis prompt
        prompt = f"""Analyze the following customer feedback:

Content: {item.content}
Rating: {item.rating or 'N/A'}
Channel: {item.channel}
Customer: {item.customer_name}
Metadata: {item.metadata}

Perform:
1. Sentiment analysis (positive/negative/neutral/mixed, score -1 to 1)
2. Category classification (one of: {', '.join(CATEGORIES)})
3. Priority assessment based on sentiment, customer tier, and content urgency
4. Extract key phrases and emotional tone
5. Identify suggested actions
6. Detect competitive mentions
7. Flag urgency indicators (churn risk, legal threat, executive mention)

Return structured analysis."""

        response = llm.invoke(prompt)
        # Parse structured output
        parser = PydanticOutputParser(pydantic_object=AnalysisResult)
        analysis = parser.parse(response.content)

        # Update feedback item
        state.update_feedback(feedback_id, {
            "status": "analyzed",
            "sentiment": analysis.sentiment,
            "category": analysis.category,
            "priority": analysis.priority,
            "tags": analysis.tags,
            "analysis": analysis.model_dump(),
        })

        # Forward to responder if negative/neutral, or action if critical
        if analysis.priority == "critical":
            msg = AgentMessage(
                sender=AgentRole.ANALYZER,
                recipient=AgentRole.COORDINATOR,
                message_type="alert",
                payload={
                    "alert": "critical_feedback",
                    "feedback_id": feedback_id,
                    "analysis": analysis.model_dump(),
                },
            )
        else:
            msg = AgentMessage(
                sender=AgentRole.ANALYZER,
                recipient=AgentRole.COORDINATOR,
                message_type="result",
                payload={
                    "action": "analyzed",
                    "feedback_id": feedback_id,
                    "next_step": "respond",
                },
            )
        state.publish_message(msg)

        return {"feedback_id": feedback_id, "analysis": analysis.model_dump()}

    @tool
    def batch_analyze(hours: int = 24) -> dict:
        """Analyze all unanalyzed feedback from the last N hours."""
        items = state.query_feedback(status="new", limit=500)
        results = {"analyzed": 0, "errors": 0, "details": []}

        for item in items:
            try:
                result = analyze_feedback.invoke({"feedback_id": item.id})
                results["analyzed"] += 1
                results["details"].append(result)
            except Exception as e:
                results["errors"] += 1
                results["details"].append({"feedback_id": item.id, "error": str(e)})

        return results

    @tool
    def detect_trends(hours: int = 168) -> dict:
        """Detect emerging trends across all analyzed feedback."""
        items = state.query_feedback(status="analyzed", limit=1000)

        # Aggregate by category and sentiment
        category_counts = {}
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        tag_counts = {}

        for item in items:
            cat = item.category or "uncategorized"
            category_counts[cat] = category_counts.get(cat, 0) + 1
            sentiment_counts[item.sentiment or "neutral"] += 1
            for tag in item.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Find trending tags (appearing 3+ times)
        trending = {tag: count for tag, count in tag_counts.items() if count >= 3}

        return {
            "period_hours": hours,
            "total_items": len(items),
            "category_distribution": category_counts,
            "sentiment_distribution": sentiment_counts,
            "trending_tags": trending,
            "top_categories": sorted(category_counts.items(), key=lambda x: -x[1])[:5],
        }

    @tool
    def cluster_similar_feedback(hours: int = 72) -> dict:
        """Cluster similar feedback items to identify common issues."""
        items = state.query_feedback(status="analyzed", limit=200)

        # Simple keyword-based clustering (production: use embeddings)
        clusters = {}
        for item in items:
            key_phrases = item.analysis.get("key_phrases", [])
            for phrase in key_phrases:
                if phrase not in clusters:
                    clusters[phrase] = {"count": 0, "items": [], "avg_sentiment": 0}
                clusters[phrase]["count"] += 1
                clusters[phrase]["items"].append(item.id)
                clusters[phrase]["avg_sentiment"] += item.analysis.get("sentiment_score", 0)

        # Sort by count descending
        sorted_clusters = sorted(clusters.items(), key=lambda x: -x[1]["count"])
        return {
            "clusters": [
                {"topic": k, "count": v["count"], "sample_items": v["items"][:5]}
                for k, v in sorted_clusters[:10]
            ]
        }

    system_prompt = """You are the Analysis agent for a feedback management system.
    Your responsibilities:
    1. Perform sentiment analysis on all incoming feedback
    2. Categorize feedback into predefined categories
    3. Assess priority based on content, customer tier, and urgency
    4. Extract key phrases, emotions, and competitive intelligence
    5. Detect trends and cluster similar feedback
    6. Recommend actions for each feedback item

    Priority rules:
    - Critical: Churn threats, legal mentions, executive complaints, security issues
    - High: Very negative sentiment + VIP customer, product bugs affecting workflow
    - Medium: Standard complaints, feature requests
    - Low: General questions, positive feedback with minor suggestions

    Always provide structured, actionable analysis. Flag anything requiring immediate attention."""

    return DeepAgent(
        llm=llm,
        tools=[analyze_feedback, batch_analyze, detect_trends, cluster_similar_feedback],
        system_prompt=system_prompt,
        name="analyzer",
    )
```

---

## 4. Response Agent

### 4.1 Responsibilities

- Draft personalized responses to feedback
- Match tone to sentiment and customer tier
- Ensure brand voice consistency
- Generate response templates for common scenarios
- Handle multi-language responses
- Escalate sensitive responses for human approval

### 4.3 Implementation

```python
# src/agents/responder.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from .base import AgentRole, AgentMessage, SharedState, FeedbackItem
from typing import Literal


class ResponseDraft(BaseModel):
    subject: str
    body: str
    tone: Literal["empathetic", "professional", "apologetic", "enthusiastic", "neutral"]
    language: str = "en"
    requires_approval: bool = False
    approval_reason: str | None = None
    suggested_offer: str | None = None  # discount, refund, upgrade, etc.
    internal_notes: str | None = None


def create_responder_agent(state: SharedState) -> DeepAgent:
    """Creates the Response agent that drafts customer-facing replies."""

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

    @tool
    def draft_response(feedback_id: str, tone_override: str | None = None) -> dict:
        """Draft a response to a feedback item.
        Args:
            feedback_id: The feedback item to respond to
            tone_override: Optional tone override (empathetic, professional, apologetic, enthusiastic)
        Returns:
            Drafted response with metadata
        """
        item = state.get_feedback(feedback_id)
        if not item:
            return {"error": "Feedback not found"}

        analysis = item.analysis
        sentiment = analysis.get("sentiment", "neutral")
        category = analysis.get("category", "general")
        is_vip = item.metadata.get("is_vip", False)

        # Determine tone
        tone = tone_override or _select_tone(sentiment, category, is_vip)

        # Build response prompt
        prompt = f"""Draft a customer response to the following feedback:

Customer: {item.customer_name}
Channel: {item.channel}
Original feedback: {item.content}
Rating: {item.rating or 'N/A'}
Sentiment: {sentiment} (score: {analysis.get('sentiment_score', 0)})
Category: {category}
Priority: {item.priority}
Customer tier: {'VIP/Enterprise' if is_vip else 'Standard'}
Customer tenure: {item.metadata.get('customer_tenure_days', 0)} days

Tone: {tone}
Language: {item.metadata.get('preferred_language', 'en')}

Guidelines:
1. Address the customer by name
2. Acknowledge their specific concern — never use generic templates
3. If negative: apologize sincerely, explain what we're doing, offer concrete next step
4. If positive: thank them specifically, reinforce their decision
5. If feature request: confirm it's logged, share timeline if available
6. Keep it under 200 words unless the issue requires detail
7. Include a clear call-to-action
8. For VIP customers: offer direct line to support lead

Return the response draft."""

        response = llm.invoke(prompt)
        parser = PydanticOutputParser(pydantic_object=ResponseDraft)
        draft = parser.parse(response.content)

        # Determine if human approval needed
        requires_approval = _needs_approval(item, draft)
        draft.requires_approval = requires_approval

        # Store response
        state.update_feedback(feedback_id, {
            "response": draft.body,
            "status": "responded" if not requires_approval else "pending_approval",
        })

        # Notify coordinator
        msg = AgentMessage(
            sender=AgentRole.RESPONDER,
            recipient=AgentRole.COORDINATOR,
            message_type="result",
            payload={
                "action": "drafted_response",
                "feedback_id": feedback_id,
                "requires_approval": requires_approval,
            },
        )
        state.publish_message(msg)

        return {
            "feedback_id": feedback_id,
            "draft": draft.model_dump(),
            "requires_approval": requires_approval,
        }

    @tool
    def generate_template(category: str, sentiment: str) -> dict:
        """Generate a reusable response template for a category/sentiment combo."""
        prompt = f"""Create a response template for:
Category: {category}
Sentiment: {sentiment}

The template should:
1. Have placeholders for: {{customer_name}}, {{specific_issue}}, {{resolution}}, {{next_step}}
2. Be adaptable to specific situations
3. Follow brand voice: professional but warm, concise, action-oriented
4. Include a fallback for when more info is needed

Return the template with usage guidelines."""

        response = llm.invoke(prompt)
        return {"category": category, "sentiment": sentiment, "template": response.content}

    @tool
    def translate_response(feedback_id: str, target_language: str) -> dict:
        """Translate a drafted response to the customer's preferred language."""
        item = state.get_feedback(feedback_id)
        if not item or not item.response:
            return {"error": "No response to translate"}

        prompt = f"""Translate the following customer response to {target_language}.
Maintain the tone, formatting, and placeholders. Adapt cultural references as needed.

Response:
{item.response}

Return only the translated text."""

        translated = llm.invoke(prompt).content
        return {
            "feedback_id": feedback_id,
            "language": target_language,
            "translated": translated,
        }

    def _select_tone(sentiment: str, category: str, is_vip: bool) -> str:
        if sentiment == "negative":
            return "apologetic" if category in ["bug_report", "customer_support"] else "empathetic"
        if sentiment == "positive":
            return "enthusiastic"
        if category == "feature_request":
            return "professional"
        return "professional"

    def _needs_approval(item: FeedbackItem, draft: ResponseDraft) -> bool:
        """Determine if a response needs human approval before sending."""
        if item.priority == "critical":
            return True
        if item.metadata.get("is_vip", False) and item.sentiment == "negative":
            return True
        if draft.suggested_offer in ["refund", "credit", "discount"]:
            return True
        if "legal" in item.tags or "lawsuit" in item.content.lower():
            return True
        return False

    system_prompt = """You are the Response agent for a feedback management system.
    Your responsibilities:
    1. Draft personalized, on-brand responses to customer feedback
    2. Match tone to sentiment, category, and customer tier
    3. Generate reusable templates for common scenarios
    4. Translate responses for international customers
    5. Flag responses requiring human approval

    Brand voice: Professional but warm. We apologize when we're wrong, celebrate when
    customers are happy, and always provide a clear next step. Never blame the customer.
    Never make promises we can't keep. Always acknowledge the specific issue raised.

    Approval required for: Critical priority, VIP + negative, refund/credit offers,
    legal mentions, anything that could escalate publicly."""

    return DeepAgent(
        llm=llm,
        tools=[draft_response, generate_template, translate_response],
        system_prompt=system_prompt,
        name="responder",
    )
```

---

## 5. Action Agent

### 5.1 Responsibilities

- Create tickets in project management tools (Jira, Linear, Asana)
- Trigger workflows in CRM (HubSpot, Salesforce)
- Schedule follow-up tasks
- Initiate refund/credit processes
- Notify relevant teams via Slack/Email
- Update knowledge base with new solutions
- Close the loop with customers

### 5.2 Implementation

```python
# src/agents/actor.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from .base import AgentRole, AgentMessage, SharedState, FeedbackItem
from .integrations import (
    JiraIntegration, SlackIntegration, HubSpotIntegration,
    ZendeskIntegration, CalendarIntegration, BillingIntegration
)


def create_actor_agent(state: SharedState) -> DeepAgent:
    """Creates the Action agent that executes follow-up actions."""

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Initialize integrations
    jira = JiraIntegration()
    slack = SlackIntegration()
    hubspot = HubSpotIntegration()
    zendesk = ZendeskIntegration()
    calendar = CalendarIntegration()
    billing = BillingIntegration()

    @tool
    def create_ticket(feedback_id: str, ticket_type: str = "task") -> dict:
        """Create a ticket in Jira/Linear for follow-up.
        Args:
            feedback_id: The feedback item to create a ticket for
            ticket_type: One of task, bug, story, epic
        Returns:
            Ticket details with URL
        """
        item = state.get_feedback(feedback_id)
        if not item:
            return {"error": "Feedback not found"}

        analysis = item.analysis
        title = f"[{item.priority.upper()}] {item.category}: {item.content[:80]}..."
        description = f"""Customer: {item.customer_name} ({item.customer_id})
Channel: {item.channel}
Priority: {item.priority}
Sentiment: {item.sentiment}
Category: {item.category}

Original Feedback:
{item.content}

Analysis Summary:
{analysis.get('summary', 'N/A')}

Suggested Actions:
{chr(10).join(f'- {a}' for a in analysis.get('suggested_actions', []))}

Feedback ID: {feedback_id}
"""

        labels = [item.category, item.sentiment or "unknown", f"priority-{item.priority}"]
        if item.metadata.get("is_vip"):
            labels.append("vip")

        ticket = jira.create_issue(
            title=title,
            description=description,
            issue_type=ticket_type,
            priority=_map_priority(item.priority),
            labels=labels,
            assignee=_route_to_team(item.category),
        )

        # Record action
        _record_action(state, feedback_id, "ticket_created", {
            "ticket_id": ticket["id"],
            "ticket_url": ticket["url"],
            "system": "jira",
        })

        return {"ticket_id": ticket["id"], "url": ticket["url"]}

    @tool
    def notify_team(feedback_id: str, team: str, message: str | None = None) -> dict:
        """Send a notification to a team channel.
        Args:
            feedback_id: Related feedback item
            team: Team identifier (support, product, engineering, billing, leadership)
            message: Custom message (auto-generated if not provided)
        Returns:
            Notification confirmation
        """
        item = state.get_feedback(feedback_id)
        if not item:
            return {"error": "Feedback not found"}

        if not message:
            message = _generate_notification_message(item)

        channel_map = {
            "support": "#support-alerts",
            "product": "#product-feedback",
            "engineering": "#eng-bugs",
            "billing": "#billing-issues",
            "leadership": "#leadership-escalations",
        }

        slack.send_message(
            channel=channel_map.get(team, "#general"),
            text=message,
            attachments=[{
                "title": f"Feedback: {item.content[:100]}...",
                "title_link": f"https://app.example.com/feedback/{feedback_id}",
                "color": _priority_color(item.priority),
                "fields": [
                    {"title": "Priority", "value": item.priority, "short": True},
                    {"title": "Category", "value": item.category, "short": True},
                    {"title": "Customer", "value": item.customer_name, "short": True},
                    {"title": "Sentiment", "value": item.sentiment or "unknown", "short": True},
                ],
            }],
        )

        _record_action(state, feedback_id, "team_notified", {
            "team": team,
            "channel": channel_map.get(team, "#general"),
        })

        return {"notified": team, "feedback_id": feedback_id}

    @tool
    def schedule_followup(feedback_id: str, days: int = 7) -> dict:
        """Schedule a follow-up task for a customer.
        Args:
            feedback_id: The feedback item
            days: Days until follow-up
        Returns:
            Scheduled task details
        """
        item = state.get_feedback(feedback_id)
        if not item:
            return {"error": "Feedback not found"}

        followup_date = datetime.utcnow() + timedelta(days=days)
        task = calendar.create_event(
            title=f"Follow-up: {item.customer_name} - {item.category}",
            description=f"Follow up on feedback: {item.content[:200]}",
            start_time=followup_date,
            duration_minutes=30,
            attendees=[item.customer_email] if item.customer_email else [],
            metadata={"feedback_id": feedback_id},
        )

        _record_action(state, feedback_id, "followup_scheduled", {
            "date": followup_date.isoformat(),
            "event_id": task["id"],
        })

        return {"scheduled": followup_date.isoformat(), "event_id": task["id"]}

    @tool
    def update_crm(feedback_id: str) -> dict:
        """Update CRM records with feedback data."""
        item = state.get_feedback(feedback_id)
        if not item:
            return {"error": "Feedback not found"}

        # Create or update contact
        contact = hubspot.upsert_contact(
            email=item.customer_email or f"{item.customer_id}@placeholder.com",
            name=item.customer_name,
            metadata={
                "last_feedback_date": item.collected_at.isoformat(),
                "last_feedback_sentiment": item.sentiment,
                "feedback_count": item.metadata.get("previous_tickets", 0) + 1,
                "ltv": item.metadata.get("ltv", 0),
            },
        )

        # Create engagement
        hubspot.create_engagement(
            contact_id=contact["id"],
            type="NOTE",
            title=f"Feedback received via {item.channel}",
            body=item.content,
            metadata={"feedback_id": feedback_id},
        )

        _record_action(state, feedback_id, "crm_updated", {
            "contact_id": contact["id"],
        })

        return {"contact_id": contact["id"], "updated": True}

    @tool
    def process_refund(feedback_id: str, amount: float, reason: str) -> dict:
        """Process a refund or credit for a customer.
        Args:
            feedback_id: The feedback item
            refund_amount: Amount to refund
            reason: Business reason for the refund
        Returns:
            Refund confirmation
        """
        item = state.get_feedback(feedback_id)
        if not item:
            return {"error": "Feedback not found"}

        # Verify approval
        if item.priority != "critical" and not item.metadata.get("is_vip"):
            return {"error": "Refund requires critical priority or VIP status"}

        refund = billing.issue_refund(
            customer_id=item.customer_id,
            amount=amount,
            reason=reason,
            feedback_id=feedback_id,
        )

        _record_action(state, feedback_id, "refund_processed", {
            "amount": amount,
            "refund_id": refund["id"],
        })

        return {"refund_id": refund["id"], "amount": amount, "status": "processed"}

    @tool
    def close_feedback(feedback_id: str, resolution: str) -> dict:
        """Mark a feedback item as resolved and closed."""
        state.update_feedback(feedback_id, {
            "status": "closed",
            "analysis": {**state.get_feedback(feedback_id).analysis, "resolution": resolution},
        })

        _record_action(state, feedback_id, "closed", {"resolution": resolution})

        return {"feedback_id": feedback_id, "status": "closed"}

    def _record_action(state: SharedState, feedback_id: str, action_type: str, details: dict):
        item = state.get_feedback(feedback_id)
        if item:
            actions = item.actions + [{"type": action_type, "details": details, "timestamp": datetime.utcnow().isoformat()}]
            state.update_feedback(feedback_id, {"actions": actions})

    def _map_priority(priority: str) -> str:
        return {"critical": "highest", "high": "high", "medium": "medium", "low": "low"}.get(priority, "medium")

    def _route_to_team(category: str) -> str:
        routing = {
            "bug_report": "engineering",
            "feature_request": "product",
            "billing": "billing",
            "customer_support": "support",
            "integration": "engineering",
            "security": "security",
        }
        return routing.get(category, "support")

    def _priority_color(priority: str) -> str:
        return {"critical": "#FF0000", "high": "#FF8C00", "medium": "#FFD700", "low": "#00FF00"}.get(priority, "#808080")

    def _generate_notification_message(item: FeedbackItem) -> str:
        return (
            f"New {item.priority} priority feedback from {item.customer_name} "
            f"via {item.channel}. Category: {item.category}. "
            f"Sentiment: {item.sentiment}. "
            f"Content: {item.content[:150]}..."
        )

    system_prompt = """You are the Action agent for a feedback management system.
    Your responsibilities:
    1. Create tickets in project management tools for follow-up
    2. Notify relevant teams via Slack
    3. Schedule follow-up tasks and meetings
    4. Update CRM records with feedback data
    5. Process refunds/credits when authorized
    6. Close feedback items when resolved

    Routing rules:
    - bug_report -> Engineering team
    - feature_request -> Product team
    - billing -> Billing team
    - customer_support -> Support team
    - security -> Security team
    - critical items -> Leadership notification

    Always confirm actions before executing. Log all actions for audit trail."""

    return DeepAgent(
        llm=llm,
        tools=[create_ticket, notify_team, schedule_followup, update_crm,
               process_refund, close_feedback],
        system_prompt=system_prompt,
        name="actor",
    )
```

---

## 6. Performance Analytics Agent

### 6.1 Responsibilities

- Track KPIs (response time, resolution time, CSAT, NPS)
- Generate daily/weekly/monthly reports
- Identify performance anomalies
- Benchmark against historical data
- Provide actionable recommendations
- Forecast trends

### 6.2 Implementation

```python
# src/agents/analyst.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from .base import AgentRole, AgentMessage, SharedState, FeedbackItem
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


def create_analyst_agent(state: SharedState) -> DeepAgent:
    """Creates the Performance Analytics agent."""

    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    @tool
    def compute_kpis(hours: int = 24) -> dict:
        """Compute key performance indicators for a time period."""
        items = state.query_feedback(limit=5000)
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [i for i in items if i.collected_at >= cutoff]

        if not recent:
            return {"error": "No feedback in the specified period"}

        # Response metrics
        responded = [i for i in recent if i.status in ("responded", "actioned", "closed")]
        closed = [i for i in recent if i.status == "closed"]

        # Sentiment distribution
        sentiment_dist = defaultdict(int)
        for item in recent:
            sentiment_dist[item.sentiment or "unknown"] += 1

        # Category distribution
        category_dist = defaultdict(int)
        for item in recent:
            category_dist[item.category or "uncategorized"] += 1

        # Average rating
        rated = [i for i in recent if i.rating is not None]
        avg_rating = statistics.mean([i.rating for i in rated]) if rated else None

        # Priority distribution
        priority_dist = defaultdict(int)
        for item in recent:
            priority_dist[item.priority] += 1

        # VIP metrics
        vip_items = [i for i in recent if i.metadata.get("is_vip")]
        vip_responded = [i for i in vip_items if i.status in ("responded", "actioned", "closed")]

        return {
            "period_hours": hours,
            "total_feedback": len(recent),
            "response_rate": len(responded) / len(recent) if recent else 0,
            "closure_rate": len(closed) / len(recent) if recent else 0,
            "average_rating": round(avg_rating, 2) if avg_rating else None,
            "sentiment_distribution": dict(sentiment_dist),
            "category_distribution": dict(category_dist),
            "priority_distribution": dict(priority_dist),
            "vip_feedback_count": len(vip_items),
            "vip_response_rate": len(vip_responded) / len(vip_items) if vip_items else 0,
            "critical_count": priority_dist.get("critical", 0),
        }

    @tool
    def generate_report(period: str = "daily") -> dict:
        """Generate a performance report.
        Args:
            period: One of daily, weekly, monthly
        Returns:
            Structured report with insights
        """
        hours = {"daily": 24, "weekly": 168, "monthly": 720}[period]
        kpis = compute_kpis.invoke({"hours": hours})

        # Get trends
        items = state.query_feedback(status="analyzed", limit=1000)
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [i for i in items if i.collected_at >= cutoff]

        # Compute trend (compare first half vs second half)
        mid = cutoff + (datetime.utcnow() - cutoff) / 2
        first_half = [i for i in recent if i.collected_at < mid]
        second_half = [i for i in recent if i.collected_at >= mid]

        first_neg = sum(1 for i in first_half if i.sentiment == "negative") / max(len(first_half), 1)
        second_neg = sum(1 for i in second_half if i.sentiment == "negative") / max(len(second_half), 1)

        trend = "improving" if second_neg < first_neg else "declining" if second_neg > first_neg else "stable"

        # Generate insights with LLM
        prompt = f"""Analyze these KPIs and provide actionable insights:

KPIs: {kpis}
Trend: {trend}
Period: {period}

Provide:
1. Top 3 highlights (what's going well)
2. Top 3 concerns (what needs attention)
3. 3 specific, actionable recommendations
4. Any anomalies detected

Be concise and data-driven."""

        insights = llm.invoke(prompt).content

        report = {
            "period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "kpis": kpis,
            "trend": trend,
            "insights": insights,
        }

        # Store report
        state.client.setex(
            f"metrics:report:{period}:{datetime.utcnow().strftime('%Y%m%d')}",
            86400 * 90,
            json.dumps(report),
        )

        return report

    @tool
    def detect_anomalies(hours: int = 24) -> dict:
        """Detect anomalies in feedback patterns."""
        items = state.query_feedback(limit=5000)
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [i for i in items if i.collected_at >= cutoff]

        anomalies = []

        # Check for volume spike
        hourly_counts = defaultdict(int)
        for item in recent:
            hour_key = item.collected_at.strftime("%Y-%m-%d-%H")
            hourly_counts[hour_key] += 1

        if hourly_counts:
            avg_volume = statistics.mean(hourly_counts.values())
            std_volume = statistics.stdev(hourly_counts.values()) if len(hourly_counts) > 1 else 0
            for hour, count in hourly_counts.items():
                if count > avg_volume + 2 * std_volume:
                    anomalies.append({
                        "type": "volume_spike",
                        "hour": hour,
                        "count": count,
                        "expected": round(avg_volume, 1),
                    })

        # Check for sentiment shift
        neg_count = sum(1 for i in recent if i.sentiment == "negative")
        neg_ratio = neg_count / max(len(recent), 1)
        if neg_ratio > 0.4:
            anomalies.append({
                "type": "negative_sentiment_spike",
                "ratio": round(neg_ratio, 2),
                "threshold": 0.4,
            })

        # Check for category concentration
        cat_counts = defaultdict(int)
        for item in recent:
            cat_counts[item.category or "unknown"] += 1
        if cat_counts:
            top_cat, top_count = max(cat_counts.items(), key=lambda x: x[1])
            if top_count / max(len(recent), 1) > 0.5:
                anomalies.append({
                    "type": "category_concentration",
                    "category": top_cat,
                    "ratio": round(top_count / max(len(recent), 1), 2),
                })

        return {"anomalies": anomalies, "checked_at": datetime.utcnow().isoformat()}

    @tool
    def forecast_trends(days: int = 7) -> dict:
        """Forecast feedback volume and sentiment for the next N days."""
        # Simple moving average forecast (production: use Prophet or similar)
        items = state.query_feedback(limit=5000)
        daily_counts = defaultdict(lambda: {"total": 0, "negative": 0, "positive": 0})

        for item in items:
            day = item.collected_at.strftime("%Y-%m-%d")
            daily_counts[day]["total"] += 1
            if item.sentiment == "negative":
                daily_counts[day]["negative"] += 1
            elif item.sentiment == "positive":
                daily_counts[day]["positive"] += 1

        if not daily_counts:
            return {"error": "Insufficient data for forecasting"}

        counts = [v["total"] for v in daily_counts.values()]
        neg_ratios = [v["negative"] / v["total"] for v in daily_counts.values() if v["total"] > 0]

        avg_daily = statistics.mean(counts)
        avg_neg_ratio = statistics.mean(neg_ratios) if neg_ratios else 0

        forecast = []
        for i in range(1, days + 1):
            date = (datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d")
            forecast.append({
                "date": date,
                "predicted_volume": round(avg_daily),
                "predicted_negative_ratio": round(avg_neg_ratio, 2),
            })

        return {
            "forecast_period_days": days,
            "historical_avg_daily_volume": round(avg_daily, 1),
            "historical_avg_negative_ratio": round(avg_neg_ratio, 2),
            "forecast": forecast,
        }

    system_prompt = """You are the Performance Analytics agent for a feedback management system.
    Your responsibilities:
    1. Compute KPIs: response rate, closure rate, average rating, sentiment distribution
    2. Generate daily, weekly, and monthly reports
    3. Detect anomalies in volume, sentiment, and category distribution
    4. Forecast trends using historical data
    5. Provide actionable, data-driven recommendations

    Always contextualize metrics against historical baselines. Flag anything that deviates
    more than 2 standard deviations from the mean. Be concise — executives read these reports."""

    return DeepAgent(
        llm=llm,
        tools=[compute_kpis, generate_report, detect_anomalies, forecast_trends],
        system_prompt=system_prompt,
        name="analyst",
    )
```

---

## 7. Code Examples & Snippets

### 7.1 Project Structure

```
feedback-management/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py              # Shared models, state, message protocol
│   │   ├── coordinator.py       # Central coordinator agent
│   │   ├── collector.py         # Collection agent
│   │   ├── analyzer.py          # Analysis agent
│   │   ├── responder.py         # Response agent
│   │   ├── actor.py             # Action agent
│   │   ├── analyst.py           # Performance analytics agent
│   │   ├── connectors/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Abstract connector
│   │   │   ├── g2.py
│   │   │   ├── trustpilot.py
│   │   │   ├── google_reviews.py
│   │   │   ├── zendesk.py
│   │   │   ├── intercom.py
│   │   │   ├── email.py
│   │   │   └── survey.py
│   │   └── integrations/
│   │       ├── __init__.py
│   │       ├── jira.py
│   │       ├── slack.py
│   │       ├── hubspot.py
│   │       ├── zendesk.py
│   │       ├── calendar.py
│   │       └── billing.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── routes/
│   │   │   ├── feedback.py
│   │   │   ├── webhooks.py
│   │   │   └── analytics.py
│   │   └── middleware/
│   │       ├── auth.py
│   │       └── rate_limit.py
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── scheduler.py         # Celery/APScheduler tasks
│   │   └── event_processor.py   # Kafka/SQS consumer
│   ├── config/
│   │   ├── settings.py          # Pydantic settings
│   │   └── logging.py
│   └── tests/
│       ├── conftest.py
│       ├── test_base.py
│       ├── test_coordinator.py
│       ├── test_collector.py
│       ├── test_analyzer.py
│       ├── test_responder.py
│       ├── test_actor.py
│       ├── test_analyst.py
│       ├── test_connectors.py
│       ├── test_integrations.py
│       └── test_e2e.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── README.md
```

### 7.2 FastAPI Application Entry Point

```python
# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.agents.base import SharedState, FeedbackItem, AgentRole, AgentMessage
from src.agents.coordinator import create_coordinator_agent
from src.agents.collector import create_collector_agent
from src.agents.analyzer import create_analyzer_agent
from src.agents.responder import create_responder_agent
from src.agents.actor import create_actor_agent
from src.agents.analyst import create_analyst_agent
from src.config.settings import get_settings
import asyncio

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    state = SharedState(redis_url=settings.redis_url)
    app.state.shared = state
    app.state.coordinator = create_coordinator_agent(state)
    app.state.collector = create_collector_agent(state)
    app.state.analyzer = create_analyzer_agent(state)
    app.state.responder = create_responder_agent(state)
    app.state.actor = create_actor_agent(state)
    app.state.analyst = create_analyst_agent(state)

    # Start background workers
    app.state.collection_task = asyncio.create_task(collection_worker(state))
    app.state.analysis_task = asyncio.create_task(analysis_worker(state))

    yield

    # Shutdown
    app.state.collection_task.cancel()
    app.state.analysis_task.cancel()


app = FastAPI(
    title="AI Feedback Management System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def collection_worker(state: SharedState):
    """Background worker that periodically collects feedback."""
    while True:
        try:
            # Collect from all channels every 5 minutes
            for channel in ["g2", "trustpilot", "google_reviews", "zendesk", "intercom"]:
                msg = AgentMessage(
                    sender=AgentRole.COORDINATOR,
                    recipient=AgentRole.COLLECTOR,
                    message_type="task",
                    payload={"action": "collect", "config": {"channel": channel, "since_minutes": 5}},
                )
                state.publish_message(msg)
            await asyncio.sleep(300)  # 5 minutes
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Collection worker error: {e}")
            await asyncio.sleep(60)


async def analysis_worker(state: SharedState):
    """Background worker that processes unanalyzed feedback."""
    while True:
        try:
            items = state.query_feedback(status="new", limit=50)
            for item in items:
                msg = AgentMessage(
                    sender=AgentRole.COORDINATOR,
                    recipient=AgentRole.ANALYZER,
                    message_type="task",
                    payload={"action": "analyze", "feedback_id": item.id},
                )
                state.publish_message(msg)
            await asyncio.sleep(30)  # Check every 30 seconds
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Analysis worker error: {e}")
            await asyncio.sleep(60)


@app.post("/feedback/submit", response_model=dict)
async def submit_feedback(item: FeedbackItem, background: BackgroundTasks):
    """Submit a new feedback item into the system."""
    state: SharedState = app.state.shared
    feedback_id = state.store_feedback(item)

    # Auto-route to analyzer
    msg = AgentMessage(
        sender=AgentRole.COORDINATOR,
        recipient=AgentRole.ANALYZER,
        message_type="task",
        payload={"action": "analyze", "feedback_id": feedback_id},
    )
    state.publish_message(msg)

    return {"feedback_id": feedback_id, "status": "received"}


@app.get("/feedback/{feedback_id}", response_model=FeedbackItem)
async def get_feedback(feedback_id: str):
    """Retrieve a feedback item by ID."""
    state: SharedState = app.state.shared
    item = state.get_feedback(feedback_id)
    if not item:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return item


@app.get("/feedback", response_model=list[FeedbackItem])
async def list_feedback(
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    limit: int = 100,
):
    """List feedback items with optional filters."""
    state: SharedState = app.state.shared
    return state.query_feedback(status=status, priority=priority, category=category, limit=limit)


@app.post("/feedback/{feedback_id}/respond", response_model=dict)
async def trigger_response(feedback_id: str, tone: str | None = None):
    """Trigger the Response agent for a feedback item."""
    state: SharedState = app.state.shared
    msg = AgentMessage(
        sender=AgentRole.COORDINATOR,
        recipient=AgentRole.RESPONDER,
        message_type="task",
        payload={"action": "respond", "feedback_id": feedback_id, "tone": tone},
    )
    state.publish_message(msg)
    return {"status": "queued", "agent": "responder"}


@app.post("/feedback/{feedback_id}/action", response_model=dict)
async def trigger_action(feedback_id: str, action_type: str):
    """Trigger the Action agent for a feedback item."""
    state: SharedState = app.state.shared
    msg = AgentMessage(
        sender=AgentRole.COORDINATOR,
        recipient=AgentRole.ACTOR,
        message_type="task",
        payload={"action": "execute", "feedback_id": feedback_id, "action_type": action_type},
    )
    state.publish_message(msg)
    return {"status": "queued", "agent": "actor"}


@app.get("/analytics/kpis", response_model=dict)
async def get_kpis(hours: int = 24):
    """Get KPIs for a time period."""
    state: SharedState = app.state.shared
    # Delegate to analyst agent
    result = app.state.analyst.compute_kpis(hours=hours)
    return result


@app.get("/analytics/report/{period}", response_model=dict)
async def get_report(period: str):
    """Get a performance report (daily, weekly, monthly)."""
    if period not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Period must be daily, weekly, or monthly")
    return app.state.analyst.generate_report(period=period)


@app.post("/webhooks/{channel}", response_model=dict)
async def receive_webhook(channel: str, payload: dict):
    """Receive webhooks from external platforms."""
    state: SharedState = app.state.shared
    # Normalize webhook payload to FeedbackItem
    item = FeedbackItem(
        source=f"webhook_{channel}",
        channel=channel,
        customer_id=payload.get("customer_id", "unknown"),
        customer_name=payload.get("customer_name", "Anonymous"),
        content=payload.get("content", ""),
        rating=payload.get("rating"),
        metadata={"webhook_payload": payload},
    )
    feedback_id = state.store_feedback(item)
    return {"feedback_id": feedback_id, "status": "received"}
```

### 7.3 Docker Compose

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/feedback
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis
      - db
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/feedback
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis
      - db
    command: python -m src.workers.scheduler

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
      - POSTGRES_DB=feedback
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

### 7.4 Configuration

```python
# src/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allowed_origins: list[str] = ["*"]

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/feedback"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"

    # Connectors
    g2_api_key: str = ""
    trustpilot_api_key: str = ""
    google_reviews_api_key: str = ""
    zendesk_api_token: str = ""
    intercom_api_token: str = ""

    # Integrations
    jira_url: str = ""
    jira_api_token: str = ""
    slack_bot_token: str = ""
    hubspot_api_key: str = ""

    # Collection
    collection_interval_seconds: int = 300
    analysis_interval_seconds: int = 30

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 8. Testing Strategy

### 8.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5 tests, ~2 min)
                   ┌┴─────────┴┐
                   │ Integration│  (20 tests, ~30s)
                  ┌┴────────────┴┐
                  │    Unit       │  (100+ tests, ~10s)
                 ┌┴───────────────┴┐
                 │  Contract       │  (15 tests, ~5s)
                 └─────────────────┘
```

### 8.2 Unit Tests

```python
# src/tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch
from src.agents.base import SharedState, FeedbackItem, AgentMessage, AgentRole
from datetime import datetime


@pytest.fixture
def mock_redis():
    with patch("src.agents.base.redis") as mock:
        client = MagicMock()
        mock.from_url.return_value = client
        yield client


@pytest.fixture
def shared_state(mock_redis):
    state = SharedState(redis_url="redis://mock")
    state.client = mock_redis
    return state


@pytest.fixture
def sample_feedback():
    return FeedbackItem(
        id="fb-001",
        source="zendesk",
        channel="zendesk",
        customer_id="cust-123",
        customer_name="Jane Doe",
        customer_email="jane@example.com",
        content="The new dashboard is confusing and slow. Please fix the navigation.",
        rating=2,
        metadata={"is_vip": True, "customer_tenure_days": 365},
    )


@pytest.fixture
def sample_analysis():
    return {
        "sentiment": "negative",
        "sentiment_score": -0.7,
        "category": "usability",
        "priority": "high",
        "tags": ["dashboard", "navigation", "performance"],
        "summary": "Customer frustrated with new dashboard navigation and performance",
        "key_phrases": ["confusing", "slow", "navigation"],
        "emotion": "frustrated",
        "urgency_indicators": [],
        "suggested_actions": ["Create UX improvement ticket", "Schedule follow-up call"],
        "related_products": ["dashboard"],
        "competitive_mentions": [],
    }
```

```python
# src/tests/test_base.py
import pytest
from src.agents.base import SharedState, FeedbackItem, AgentMessage, AgentRole
from datetime import datetime


class TestFeedbackItem:
    def test_create_feedback_item(self, sample_feedback):
        assert sample_feedback.id == "fb-001"
        assert sample_feedback.status == "new"
        assert sample_feedback.priority == "medium"
        assert sample_feedback.sentiment is None

    def test_feedback_serialization(self, sample_feedback):
        json_str = sample_feedback.model_dump_json()
        restored = FeedbackItem.model_validate_json(json_str)
        assert restored.id == sample_feedback.id
        assert restored.content == sample_feedback.content


class TestSharedState:
    def test_store_and_retrieve(self, shared_state, sample_feedback, mock_redis):
        mock_redis.get.return_value = sample_feedback.model_dump_json()

        feedback_id = shared_state.store_feedback(sample_feedback)
        assert feedback_id == "fb-001"

        retrieved = shared_state.get_feedback(feedback_id)
        assert retrieved is not None
        assert retrieved.customer_name == "Jane Doe"

    def test_update_feedback(self, shared_state, sample_feedback, mock_redis):
        mock_redis.get.return_value = sample_feedback.model_dump_json()

        shared_state.store_feedback(sample_feedback)
        updated = shared_state.update_feedback("fb-001", {"status": "analyzed", "sentiment": "negative"})
        assert updated.status == "analyzed"
        assert updated.sentiment == "negative"

    def test_publish_and_consume_messages(self, shared_state, mock_redis):
        msg = AgentMessage(
            sender=AgentRole.COORDINATOR,
            recipient=AgentRole.ANALYZER,
            message_type="task",
            payload={"action": "analyze", "feedback_id": "fb-001"},
        )
        mock_redis.rpop.return_value = msg.model_dump_json()

        shared_state.publish_message(msg)
        messages = shared_state.consume_messages(AgentRole.ANALYZER)
        assert len(messages) == 1
        assert messages[0].sender == AgentRole.COORDINATOR

    def test_query_feedback_empty(self, shared_state, mock_redis):
        mock_redis.scan_iter.return_value = iter([])
        results = shared_state.query_feedback(status="new")
        assert len(results) == 0
```

```python
# src/tests/test_collector.py
import pytest
from unittest.mock import MagicMock, patch
from src.agents.collector import create_collector_agent
from src.agents.base import FeedbackItem, AgentRole


class TestCollectorAgent:
    def test_collect_from_channel(self, shared_state, mock_redis):
        # Mock connector
        mock_connector = MagicMock()
        mock_connector.fetch.return_value = [
            {
                "id": "g2-001",
                "customer_id": "cust-456",
                "customer_name": "John Smith",
                "content": "Great product, but pricing is too high",
                "rating": 4,
            }
        ]

        with patch("src.agents.collector.G2Connector", return_value=mock_connector):
            agent = create_collector_agent(shared_state)
            result = agent.tools[0].invoke({
                "channel": "g2",
                "since_minutes": 60,
            })

        assert result["collected"] == 1
        assert result["duplicates"] == 0
        assert len(result["feedback_ids"]) == 1

    def test_deduplication(self, shared_state, mock_redis, sample_feedback):
        # Pre-populate hash
        mock_redis.get.return_value = "fb-existing"

        mock_connector = MagicMock()
        mock_connector.fetch.return_value = [
            {
                "id": "g2-001",
                "customer_id": sample_feedback.customer_id,
                "customer_name": sample_feedback.customer_name,
                "content": sample_feedback.content,
                "rating": 4,
            }
        ]

        with patch("src.agents.collector.G2Connector", return_value=mock_connector):
            agent = create_collector_agent(shared_state)
            result = agent.tools[0].invoke({
                "channel": "g2",
                "since_minutes": 60,
            })

        assert result["collected"] == 0
        assert result["duplicates"] == 1

    def test_enrich_customer_data(self, shared_state, mock_redis, sample_feedback):
        mock_redis.get.return_value = sample_feedback.model_dump_json()

        mock_connector = MagicMock()
        mock_connector.get_customer_profile.return_value = {
            "tier": "enterprise",
            "tenure_days": 730,
            "open_ticket_count": 2,
            "lifetime_value": 50000,
        }

        with patch("src.agents.collector.ZendeskConnector", return_value=mock_connector):
            agent = create_collector_agent(shared_state)
            result = agent.tools[2].invoke({"feedback_id": "fb-001"})

        assert result["enriched"] is True
```

```python
# src/tests/test_analyzer.py
import pytest
from unittest.mock import MagicMock, patch
from src.agents.analyzer import create_analyzer_agent
from src.agents.base import FeedbackItem


class TestAnalyzerAgent:
    def test_analyze_feedback(self, shared_state, mock_redis, sample_feedback):
        mock_redis.get.return_value = sample_feedback.model_dump_json()

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="""{
                "sentiment": "negative",
                "sentiment_score": -0.7,
                "category": "usability",
                "priority": "high",
                "tags": ["dashboard", "navigation"],
                "summary": "Customer frustrated with dashboard",
                "key_phrases": ["confusing", "slow"],
                "emotion": "frustrated",
                "urgency_indicators": [],
                "suggested_actions": ["Create UX ticket"],
                "related_products": ["dashboard"],
                "competitive_mentions": []
            }"""
        )

        with patch("src.agents.analyzer.ChatOpenAI", return_value=mock_llm):
            agent = create_analyzer_agent(shared_state)
            result = agent.tools[0].invoke({"feedback_id": "fb-001"})

        assert result["feedback_id"] == "fb-001"
        assert result["analysis"]["sentiment"] == "negative"
        assert result["analysis"]["category"] == "usability"

    def test_detect_trends(self, shared_state, mock_redis):
        # Create multiple feedback items
        items = []
        for i in range(5):
            item = FeedbackItem(
                id=f"fb-{i}",
                source="zendesk",
                channel="zendesk",
                customer_id=f"cust-{i}",
                customer_name=f"Customer {i}",
                content=f"Feedback {i} about pricing",
                rating=2,
                status="analyzed",
                sentiment="negative",
                category="pricing",
                tags=["pricing", "expensive"],
                analysis={"sentiment_score": -0.6, "key_phrases": ["pricing", "expensive"]},
            )
            items.append(item.model_dump_json())

        mock_redis.scan_iter.return_value = iter([f"feedback:fb-{i}" for i in range(5)])
        mock_redis.get.side_effect = items

        agent = create_analyzer_agent(shared_state)
        result = agent.tools[2].invoke({"hours": 168})

        assert result["total_items"] == 5
        assert result["sentiment_distribution"]["negative"] == 5
        assert "pricing" in result["trending_tags"]
```

```python
# src/tests/test_responder.py
import pytest
from unittest.mock import MagicMock, patch
from src.agents.responder import create_responder_agent
from src.agents.base import FeedbackItem


class TestResponderAgent:
    def test_draft_response_negative(self, shared_state, mock_redis, sample_feedback):
        sample_feedback.status = "analyzed"
        sample_feedback.sentiment = "negative"
        sample_feedback.analysis = {
            "sentiment": "negative",
            "sentiment_score": -0.7,
            "category": "usability",
            "summary": "Customer frustrated with dashboard",
            "suggested_actions": ["Create UX ticket"],
        }
        mock_redis.get.return_value = sample_feedback.model_dump_json()

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="""{
                "subject": "Re: Your feedback about our dashboard",
                "body": "Hi Jane, thank you for your feedback. I understand the new dashboard navigation has been frustrating. We're actively working on improvements...",
                "tone": "apologetic",
                "language": "en",
                "requires_approval": true,
                "approval_reason": "VIP customer with negative sentiment",
                "suggested_offer": null,
                "internal_notes": "VIP customer - consider personal outreach"
            }"""
        )

        with patch("src.agents.responder.ChatOpenAI", return_value=mock_llm):
            agent = create_responder_agent(shared_state)
            result = agent.tools[0].invoke({"feedback_id": "fb-001"})

        assert result["feedback_id"] == "fb-001"
        assert result["draft"]["tone"] == "apologetic"
        assert result["requires_approval"] is True

    def test_draft_response_positive(self, shared_state, mock_redis):
        feedback = FeedbackItem(
            id="fb-002",
            source="g2",
            channel="g2",
            customer_id="cust-789",
            customer_name="Happy Customer",
            content="Love the new features! Great job team.",
            rating=5,
            status="analyzed",
            sentiment="positive",
            category="product_quality",
            analysis={"sentiment": "positive", "sentiment_score": 0.9},
        )
        mock_redis.get.return_value = feedback.model_dump_json()

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="""{
                "subject": "Re: Your review",
                "body": "Hi Happy Customer, thank you so much for the kind words! We're thrilled you're enjoying the new features...",
                "tone": "enthusiastic",
                "language": "en",
                "requires_approval": false,
                "approval_reason": null,
                "suggested_offer": null,
                "internal_notes": null
            }"""
        )

        with patch("src.agents.responder.ChatOpenAI", return_value=mock_llm):
            agent = create_responder_agent(shared_state)
            result = agent.tools[0].invoke({"feedback_id": "fb-002"})

        assert result["draft"]["tone"] == "enthusiastic"
        assert result["requires_approval"] is False
```

```python
# src/tests/test_actor.py
import pytest
from unittest.mock import MagicMock, patch
from src.agents.actor import create_actor_agent
from src.agents.base import FeedbackItem


class TestActorAgent:
    def test_create_ticket(self, shared_state, mock_redis, sample_feedback):
        sample_feedback.status = "analyzed"
        sample_feedback.priority = "high"
        sample_feedback.category = "bug_report"
        sample_feedback.analysis = {"summary": "Bug in dashboard"}
        mock_redis.get.return_value = sample_feedback.model_dump_json()

        mock_jira = MagicMock()
        mock_jira.create_issue.return_value = {
            "id": "PROJ-123",
            "url": "https://jira.example.com/PROJ-123",
        }

        with patch("src.agents.actor.JiraIntegration", return_value=mock_jira):
            agent = create_actor_agent(shared_state)
            result = agent.tools[0].invoke({
                "feedback_id": "fb-001",
                "ticket_type": "bug",
            })

        assert result["ticket_id"] == "PROJ-123"
        assert "url" in result

    def test_notify_team(self, shared_state, mock_redis, sample_feedback):
        mock_redis.get.return_value = sample_feedback.model_dump_json()

        mock_slack = MagicMock()

        with patch("src.agents.actor.SlackIntegration", return_value=mock_slack):
            agent = create_actor_agent(shared_state)
            result = agent.tools[1].invoke({
                "feedback_id": "fb-001",
                "team": "engineering",
            })

        assert result["notified"] == "engineering"
        mock_slack.send_message.assert_called_once()

    def test_process_refund_requires_approval(self, shared_state, mock_redis, sample_feedback):
        # Non-critical, non-VIP should fail
        sample_feedback.priority = "medium"
        sample_feedback.metadata = {"is_vip": False}
        mock_redis.get.return_value = sample_feedback.model_dump_json()

        agent = create_actor_agent(shared_state)
        result = agent.tools[4].invoke({
            "feedback_id": "fb-001",
            "amount": 100.0,
            "reason": "Customer complaint",
        })

        assert "error" in result
```

```python
# src/tests/test_analyst.py
import pytest
from unittest.mock import MagicMock, patch
from src.agents.analyst import create_analyst_agent
from src.agents.base import FeedbackItem
from datetime import datetime, timedelta


class TestAnalystAgent:
    def test_compute_kpis(self, shared_state, mock_redis):
        # Create test data
        items = []
        now = datetime.utcnow()
        for i in range(10):
            item = FeedbackItem(
                id=f"fb-{i}",
                source="zendesk",
                channel="zendesk",
                customer_id=f"cust-{i}",
                customer_name=f"Customer {i}",
                content=f"Feedback {i}",
                rating=3,
                status="closed" if i < 7 else "new",
                sentiment="negative" if i < 4 else "positive",
                category="pricing" if i < 5 else "usability",
                priority="high" if i < 2 else "medium",
                collected_at=now - timedelta(hours=i),
            )
            items.append(item.model_dump_json())

        mock_redis.scan_iter.return_value = iter([f"feedback:fb-{i}" for i in range(10)])
        mock_redis.get.side_effect = items

        agent = create_analyst_agent(shared_state)
        result = agent.tools[0].invoke({"hours": 24})

        assert result["total_feedback"] == 10
        assert result["closure_rate"] == 0.7
        assert result["sentiment_distribution"]["negative"] == 4
        assert result["sentiment_distribution"]["positive"] == 6

    def test_detect_anomalies_volume_spike(self, shared_state, mock_redis):
        # Create items with a volume spike in one hour
        items = []
        now = datetime.utcnow()
        for i in range(20):
            item = FeedbackItem(
                id=f"fb-{i}",
                source="zendesk",
                channel="zendesk",
                customer_id=f"cust-{i}",
                customer_name=f"Customer {i}",
                content=f"Feedback {i}",
                collected_at=now - timedelta(hours=1),  # All in same hour
            )
            items.append(item.model_dump_json())

        mock_redis.scan_iter.return_value = iter([f"feedback:fb-{i}" for i in range(20)])
        mock_redis.get.side_effect = items

        agent = create_analyst_agent(shared_state)
        result = agent.tools[2].invoke({"hours": 24})

        assert len(result["anomalies"]) > 0
        assert any(a["type"] == "volume_spike" for a in result["anomalies"])
```

### 8.3 Integration Tests

```python
# src/tests/test_e2e.py
import pytest
from unittest.mock import MagicMock, patch
from src.agents.base import SharedState, FeedbackItem, AgentRole, AgentMessage
from src.agents.coordinator import create_coordinator_agent
from src.agents.collector import create_collector_agent
from src.agents.analyzer import create_analyzer_agent
from src.agents.responder import create_responder_agent
from src.agents.actor import create_actor_agent


class TestEndToEnd:
    """End-to-end tests that verify the full feedback processing pipeline."""

    def test_full_pipeline_positive_feedback(self, shared_state, mock_redis):
        """Test: Collect -> Analyze -> Respond -> Action for positive feedback."""
        # 1. Collector receives feedback
        feedback = FeedbackItem(
            id="fb-e2e-001",
            source="g2",
            channel="g2",
            customer_id="cust-e2e",
            customer_name="Happy Customer",
            customer_email="happy@example.com",
            content="Amazing product! The new features are exactly what we needed.",
            rating=5,
            metadata={"is_vip": False},
        )
        mock_redis.get.return_value = feedback.model_dump_json()

        # 2. Analyzer processes it
        mock_llm_analyze = MagicMock()
        mock_llm_analyze.invoke.return_value = MagicMock(
            content="""{
                "sentiment": "positive",
                "sentiment_score": 0.9,
                "category": "product_quality",
                "priority": "low",
                "tags": ["features", "satisfaction"],
                "summary": "Very positive feedback about new features",
                "key_phrases": ["amazing", "exactly what we needed"],
                "emotion": "happy",
                "urgency_indicators": [],
                "suggested_actions": ["Send thank you response"],
                "related_products": [],
                "competitive_mentions": []
            }"""
        )

        # 3. Responder drafts response
        mock_llm_respond = MagicMock()
        mock_llm_respond.invoke.return_value = MagicMock(
            content="""{
                "subject": "Re: Your review",
                "body": "Hi Happy Customer, thank you so much! We're thrilled you're enjoying the new features...",
                "tone": "enthusiastic",
                "language": "en",
                "requires_approval": false,
                "approval_reason": null,
                "suggested_offer": null,
                "internal_notes": null
            }"""
        )

        with patch("src.agents.analyzer.ChatOpenAI", return_value=mock_llm_analyze):
            analyzer = create_analyzer_agent(shared_state)
            analysis_result = analyzer.tools[0].invoke({"feedback_id": "fb-e2e-001"})

        assert analysis_result["analysis"]["sentiment"] == "positive"

        # Verify feedback was updated
        updated_item = shared_state.get_feedback("fb-e2e-001")
        assert updated_item.status == "analyzed"
        assert updated_item.sentiment == "positive"

    def test_full_pipeline_critical_escalation(self, shared_state, mock_redis):
        """Test: Critical feedback triggers escalation path."""
        feedback = FeedbackItem(
            id="fb-e2e-002",
            source="zendesk",
            channel="zendesk",
            customer_id="cust-vip",
            customer_name="VIP Customer",
            customer_email="vip@example.com",
            content="This is unacceptable. Our entire team is blocked. We're considering legal action.",
            rating=1,
            metadata={"is_vip": True, "ltv": 100000},
        )
        mock_redis.get.return_value = feedback.model_dump_json()

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="""{
                "sentiment": "negative",
                "sentiment_score": -0.95,
                "category": "bug_report",
                "priority": "critical",
                "tags": ["blocking", "legal", "vip"],
                "summary": "VIP customer blocked, threatening legal action",
                "key_phrases": ["unacceptable", "blocked", "legal action"],
                "emotion": "angry",
                "urgency_indicators": ["legal threat", "blocking issue", "VIP"],
                "suggested_actions": ["Immediate engineering escalation", "Executive outreach", "Legal team notification"],
                "related_products": [],
                "competitive_mentions": []
            }"""
        )

        with patch("src.agents.analyzer.ChatOpenAI", return_value=mock_llm):
            analyzer = create_analyzer_agent(shared_state)
            result = analyzer.tools[0].invoke({"feedback_id": "fb-e2e-002"})

        assert result["analysis"]["priority"] == "critical"
        assert result["analysis"]["sentiment"] == "negative"

        # Verify escalation message was published
        # (In real test, check mock_redis.lpush calls)

    def test_deduplication_pipeline(self, shared_state, mock_redis):
        """Test: Duplicate feedback is not processed twice."""
        feedback = FeedbackItem(
            id="fb-e2e-003",
            source="zendesk",
            channel="zendesk",
            customer_id="cust-dup",
            customer_name="Duplicate Customer",
            content="Same feedback submitted twice",
            rating=3,
        )

        # First submission
        mock_redis.get.return_value = None  # No existing hash
        shared_state.store_feedback(feedback)

        # Second submission - hash exists
        mock_redis.get.return_value = "fb-e2e-003"

        # Should be detected as duplicate
        # (In real test, verify collector skips it)
```

### 8.4 Contract Tests

```python
# src/tests/test_connectors.py
import pytest
from unittest.mock import MagicMock, patch
from src.agents.connectors.g2 import G2Connector
from src.agents.connectors.base import BaseConnector


class TestConnectorContract:
    """Verify all connectors implement the required interface."""

    @pytest.mark.parametrize("connector_class", [
        G2Connector,
        # TrustpilotConnector,
        # GoogleReviewsConnector,
        # ZendeskConnector,
        # IntercomConnector,
        # EmailConnector,
        # SurveyConnector,
    ])
    def test_connector_implements_interface(self, connector_class):
        connector = connector_class()
        assert isinstance(connector, BaseConnector)
        assert hasattr(connector, "fetch")
        assert hasattr(connector, "get_customer_profile")
        assert hasattr(connector, "health_check")

    def test_g2_connector_health_check_failure(self):
        connector = G2Connector()
        with patch("src.agents.connectors.g2.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            assert connector.health_check() is False

    def test_g2_connector_fetch_parsing(self):
        connector = G2Connector()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "rev-001",
                    "reviewer": {"id": "user-001", "name": "Test User"},
                    "content": "Great product",
                    "rating": 5,
                }
            ]
        }

        with patch("src.agents.connectors.g2.requests.get", return_value=mock_response):
            from datetime import datetime
            results = connector.fetch(since=datetime.utcnow())

        assert len(results) == 1
        assert results[0]["id"] == "rev-001"
        assert results[0]["customer_id"] == "user-001"
```

### 8.5 Running Tests

```bash
# Run all tests
pytest src/tests/ -v

# Run with coverage
pytest src/tests/ -v --cov=src --cov-report=html

# Run specific test file
pytest src/tests/test_analyzer.py -v

# Run with markers
pytest src/tests/ -v -m "not slow"

# Run E2E tests only
pytest src/tests/test_e2e.py -v

# Run with parallel execution
pytest src/tests/ -v -n auto
```

### 8.6 Test Coverage Goals

| Component | Target Coverage | Critical Paths |
|-----------|----------------|----------------|
| Base models | 95% | Serialization, validation |
| Coordinator | 85% | Routing, escalation |
| Collector | 80% | Deduplication, normalization |
| Analyzer | 85% | Sentiment, categorization |
| Responder | 80% | Tone selection, approval rules |
| Actor | 75% | Ticket creation, notifications |
| Analyst | 80% | KPI computation, anomaly detection |
| Connectors | 70% | Data fetching, parsing |
| API routes | 85% | All endpoints |

---

## Appendix: Deployment Checklist

- [ ] Set up Redis cluster with persistence
- [ ] Configure PostgreSQL with automated backups
- [ ] Set up OpenAI API key with rate limiting
- [ ] Configure all connector API keys
- [ ] Set up integration credentials (Jira, Slack, HubSpot)
- [ ] Deploy with Docker Compose or Kubernetes
- [ ] Configure monitoring (Prometheus + Grafana)
- [ ] Set up alerting (PagerDuty/Opsgenie)
- [ ] Run full test suite in CI/CD
- [ ] Load test with realistic feedback volume
- [ ] Document runbooks for common failures
- [ ] Set up log aggregation (ELK/Loki)
- [ ] Configure backup and disaster recovery
