# AI-Powered Email Marketing Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Stack:** LangChain DeepAgents, Python 3.11+, PostgreSQL, Redis, Celery

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Segmentation Agent](#2-segmentation-agent-implementation)
3. [Content Personalization Agent](#3-content-personalization-agent-implementation)
4. [Send Time Optimization Agent](#4-send-time-optimization-agent-implementation)
5. [Subject Line Optimization Agent](#5-subject-line-optimization-agent-implementation)
6. [List Hygiene Agent](#6-list-hygiene-agent-implementation)
7. [Performance Analytics Agent](#7-performance-analytics-agent-implementation)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Design

The system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. A central **Email Marketing Orchestrator** coordinates six specialized agents, each responsible for a distinct aspect of the email marketing lifecycle.

```
┌─────────────────────────────────────────────────────────────┐
│                  Email Marketing Orchestrator                 │
│  (LangChain DeepAgent — plans, delegates, synthesizes)      │
└──────────┬──────────┬──────────┬──────────┬──────────┬───────┘
           │          │          │          │          │
    ┌──────▼──┐ ┌─────▼────┐ ┌───▼──────┐ ┌─▼────────┐ ┌─▼──────────┐
    │Segment- │ │Content   │ │Send Time │ │Subject   │ │List        │
    │ation    │ │Personal- │ │Optimize  │ │Line      │ │Hygiene     │
    │Agent    │ │ization   │ │Agent     │ │Optimize  │ │Agent       │
    └────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘
         │           │            │            │             │
    ┌────▼───────────▼────────────▼────────────▼─────────────▼────┐
    │              Shared Infrastructure Layer                     │
    │  PostgreSQL │ Redis │ Celery │ SendGrid/Mailgun │ LangSmith  │
    └──────────────────────────────────────────────────────────────┘
           │
    ┌──────▼──────────┐
    │  Performance    │
    │  Analytics      │
    │  Agent          │
    └─────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents | Multi-agent orchestration, tool use, planning |
| LLM | OpenAI GPT-4o / Anthropic Claude 3.5 Sonnet | Reasoning, content generation |
| Vector Store | pgvector (PostgreSQL) | Subscriber embeddings, semantic search |
| Cache | Redis | Rate limiting, session state, dedup |
| Task Queue | Celery + Redis | Async agent execution, scheduled sends |
| Email Provider | SendGrid / Mailgun | Email delivery, webhooks |
| Observability | LangSmith | Tracing, evaluation, monitoring |
| Data Store | PostgreSQL 16 | Subscriber data, campaign history, analytics |
| API | FastAPI | REST endpoints for agent invocation |

### 1.3 Orchestrator Agent

The orchestrator is the entry point. It receives a high-level marketing goal (e.g., "Launch a re-engagement campaign for lapsed subscribers") and decomposes it into sub-tasks for the specialized agents.

```python
# orchestrator.py
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool

orchestrator = DeepAgent(
    name="email_marketing_orchestrator",
    system_prompt="""You are the Email Marketing Orchestrator. Your role is to:
1. Analyze the marketing goal and audience
2. Delegate to specialized agents in the correct order
3. Synthesize agent outputs into a cohesive campaign plan
4. Ensure compliance with CAN-SPAM, GDPR, and internal policies

Available agents:
- segmentation_agent: Identifies and scores subscriber segments
- content_agent: Generates personalized email content
- send_time_agent: Determines optimal send times per subscriber
- subject_line_agent: Creates and A/B tests subject lines
- list_hygiene_agent: Cleans and validates subscriber lists
- analytics_agent: Tracks performance and provides insights

Always run list_hygiene_agent before any campaign send.
Always run analytics_agent after campaign completion.""",
    tools=[
        segmentation_agent.as_tool(),
        content_agent.as_tool(),
        send_time_agent.as_tool(),
        subject_line_agent.as_tool(),
        list_hygiene_agent.as_tool(),
        analytics_agent.as_tool(),
    ],
    model="gpt-4o",
)
```

### 1.4 Agent Communication Protocol

Agents communicate via a **structured message bus** using Pydantic models:

```python
# schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentMessage(BaseModel):
    agent_name: str
    status: AgentStatus
    payload: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str
    error: Optional[str] = None

class SegmentResult(BaseModel):
    segment_id: str
    segment_name: str
    subscriber_count: int
    criteria: dict
    estimated_engagement_rate: float

class ContentResult(BaseModel):
    campaign_id: str
    variants: list[dict]  # [{variant_id, subject, preheader, body_html, body_text}]
    personalization_tokens: list[str]

class SendTimeResult(BaseModel):
    campaign_id: str
    send_schedule: list[dict]  # [{subscriber_id, optimal_send_time, timezone}]

class SubjectLineResult(BaseModel):
    campaign_id: str
    variants: list[dict]  # [{variant_id, subject_line, predicted_open_rate}]
    ab_test_config: dict

class ListHygieneResult(BaseModel):
    total_subscribers: int
    valid_count: int
    removed_count: int
    removal_reasons: dict  # {"bounced": 45, "unsubscribed": 12, ...}
    risk_score: float

class AnalyticsResult(BaseModel):
    campaign_id: str
    sent: int
    delivered: int
    opened: int
    clicked: int
    bounced: int
    unsubscribed: int
    complaints: int
    revenue_attributed: float
```

### 1.5 Workflow Execution

```python
# workflow.py
import asyncio
from celery import Celery
from langchain_deepagents import DeepAgent

celery_app = Celery("email_marketing", broker="redis://localhost:6379/0")

@celery_app.task(bind=True, max_retries=3)
def execute_campaign_workflow(self, campaign_config: dict):
    """Execute the full email marketing campaign workflow."""
    correlation_id = generate_correlation_id()

    try:
        # Step 1: List Hygiene (always first)
        hygiene_result = run_agent("list_hygiene_agent", {
            "campaign_id": campaign_config["campaign_id"],
            "subscriber_list": campaign_config["subscriber_list"],
        }, correlation_id)

        # Step 2: Segmentation
        segment_result = run_agent("segmentation_agent", {
            "campaign_id": campaign_config["campaign_id"],
            "subscribers": hygiene_result["valid_subscribers"],
            "campaign_goal": campaign_config["goal"],
        }, correlation_id)

        # Step 3: Content Personalization
        content_result = run_agent("content_agent", {
            "campaign_id": campaign_config["campaign_id"],
            "segments": segment_result["segments"],
            "campaign_brief": campaign_config["brief"],
        }, correlation_id)

        # Step 4: Subject Line Optimization
        subject_result = run_agent("subject_line_agent", {
            "campaign_id": campaign_config["campaign_id"],
            "content_variants": content_result["variants"],
            "audience": segment_result["segments"],
        }, correlation_id)

        # Step 5: Send Time Optimization
        send_time_result = run_agent("send_time_agent", {
            "campaign_id": campaign_config["campaign_id"],
            "subscribers": hygiene_result["valid_subscribers"],
            "segments": segment_result["segments"],
        }, correlation_id)

        # Step 6: Dispatch
        dispatch_campaign(
            content=content_result,
            subject_lines=subject_result,
            send_schedule=send_time_result,
        )

        return {"status": "completed", "correlation_id": correlation_id}

    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

---

## 2. Segmentation Agent Implementation

### 2.1 Purpose

Dynamically segments subscribers based on behavioral, demographic, and engagement data using a combination of rule-based filtering and LLM-powered semantic segmentation.

### 2.2 Architecture

```python
# agents/segmentation_agent.py
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from pgvector.psycopg import register_vector
import psycopg2

class SegmentationAgent:
    """Agent that identifies and scores subscriber segments."""

    def __init__(self, db_url: str, llm_model: str = "gpt-4o"):
        self.db_url = db_url
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.agent = DeepAgent(
            name="segmentation_agent",
            system_prompt="""You are the Segmentation Agent. Your responsibilities:
1. Analyze subscriber data to identify meaningful segments
2. Use both rule-based criteria and behavioral embeddings
3. Score segments by predicted engagement likelihood
4. Ensure segments are mutually exclusive where possible
5. Respect minimum segment sizes (n >= 100) for statistical significance

Output structured segment definitions with:
- Segment name and description
- Inclusion/exclusion criteria
- Predicted engagement rate
- Recommended content strategy per segment""",
            tools=[
                self.get_subscriber_data,
                self.create_behavioral_embedding,
                self.score_segment_engagement,
                self.validate_segment_size,
            ],
            model=llm_model,
        )

    @tool
    def get_subscriber_data(self, filters: dict) -> list[dict]:
        """Retrieve subscriber data from PostgreSQL with optional filters."""
        query = """
            SELECT s.subscriber_id, s.email, s.signup_date, s.country,
                   s.preferences, s.demographics,
                   COALESCE(e.total_opens, 0) as total_opens,
                   COALESCE(e.total_clicks, 0) as total_clicks,
                   COALESCE(e.last_open_date, NULL) as last_open_date,
                   COALESCE(e.last_click_date, NULL) as last_click_date,
                   COALESCE(e.emails_received, 0) as emails_received,
                   COALESCE(e.emails_opened, 0) as emails_opened
            FROM subscribers s
            LEFT JOIN engagement_summary e ON s.subscriber_id = e.subscriber_id
            WHERE s.status = 'active'
        """
        params = []
        if filters.get("country"):
            query += " AND s.country = %s"
            params.append(filters["country"])
        if filters.get("min_engagement"):
            query += " AND (COALESCE(e.emails_opened, 0)::float / NULLIF(e.emails_received, 0)) >= %s"
            params.append(filters["min_engagement"])

        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    @tool
    def create_behavioral_embedding(self, subscriber_data: dict) -> list[float]:
        """Create a behavioral embedding vector for a subscriber."""
        behavior_text = f"""
        Engagement pattern: {subscriber_data.get('total_opens', 0)} opens out of
        {subscriber_data.get('emails_received', 0)} emails received.
        Last engagement: {subscriber_data.get('last_open_date', 'never')}.
        Preferences: {subscriber_data.get('preferences', {})}.
        Demographics: {subscriber_data.get('demographics', {})}.
        """
        return self.embeddings.embed_query(behavior_text)

    @tool
    def score_segment_engagement(self, segment_criteria: dict) -> float:
        """Predict engagement rate for a segment using historical data."""
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN opened THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0) as open_rate,
                SUM(CASE WHEN clicked THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0) as click_rate
            FROM campaign_events ce
            JOIN subscribers s ON ce.subscriber_id = s.subscriber_id
            WHERE ce.campaign_id IN (
                SELECT campaign_id FROM campaigns
                WHERE created_at > NOW() - INTERVAL '90 days'
            )
        """
        # Add segment-specific filters
        if segment_criteria.get("min_days_since_signup"):
            query += f" AND s.signup_date < NOW() - INTERVAL '{segment_criteria['min_days_since_signup']} days'"
        if segment_criteria.get("engagement_level"):
            query += f" AND (ce.opened::int + ce.clicked::int) >= {segment_criteria['engagement_level']}"

        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
                if row and row[0] > 0:
                    return round(row[1] * 0.6 + row[2] * 0.4, 4)  # Weighted score
                return 0.0

    @tool
    def validate_segment_size(self, subscriber_ids: list[str]) -> dict:
        """Validate that a segment meets minimum size requirements."""
        count = len(subscriber_ids)
        return {
            "count": count,
            "is_valid": count >= 100,
            "recommendation": "proceed" if count >= 100 else "merge_with_similar_segment",
        }

    def run(self, campaign_id: str, subscribers: list[dict], campaign_goal: str) -> dict:
        """Execute segmentation for a campaign."""
        result = self.agent.invoke({
            "input": f"""Segment the following {len(subscribers)} subscribers for campaign '{campaign_id}'.
            Campaign goal: {campaign_goal}
            Create 3-5 meaningful segments based on engagement level, demographics, and behavior.
            For each segment, provide: name, description, criteria, subscriber_count, predicted_engagement_rate.""",
        })
        return result
```

### 2.3 Segmentation Strategies

| Strategy | Method | Use Case |
|----------|--------|----------|
| **RFM Analysis** | Recency, Frequency, Monetary scoring | E-commerce, subscription |
| **Engagement Tiers** | Open/click rate percentiles | General newsletters |
| **Behavioral Embeddings** | pgvector similarity search | Content preference matching |
| **Lifecycle Stage** | Signup date + engagement trend | Onboarding, re-engagement |
| **Predictive Churn** | LLM-classified risk score | Win-back campaigns |
| **Demographic** | Country, language, age group | Localized campaigns |

### 2.4 Database Schema

```sql
-- segmentation tables
CREATE TABLE segments (
    segment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(campaign_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    criteria JSONB NOT NULL,
    subscriber_count INTEGER DEFAULT 0,
    predicted_engagement_rate FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE segment_subscribers (
    segment_id UUID REFERENCES segments(segment_id),
    subscriber_id UUID REFERENCES subscribers(subscriber_id),
    score FLOAT,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (segment_id, subscriber_id)
);

-- Enable vector similarity search
CREATE EXTENSION vector;
CREATE TABLE subscriber_embeddings (
    subscriber_id UUID PRIMARY KEY REFERENCES subscribers(subscriber_id),
    embedding vector(1536),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON subscriber_embeddings USING hnsw (embedding vector_cosine_ops);
```

---

## 3. Content Personalization Agent Implementation

### 3.1 Purpose

Generates personalized email content (subject, preheader, body HTML/text) tailored to each segment and individual subscriber using LLM-powered generation with brand voice consistency.

### 3.2 Architecture

```python
# agents/content_agent.py
from langchain_deepagents import DeepAgent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class EmailVariant(BaseModel):
    variant_id: str
    subject_line: str = Field(max_length=100)
    preheader: str = Field(max_length=150)
    body_html: str
    body_text: str
    personalization_tokens: list[str]
    tone: str
    call_to_action: str

class ContentAgent:
    """Agent that generates personalized email content."""

    def __init__(self, brand_voice_guide: str, llm_model: str = "gpt-4o"):
        self.brand_voice_guide = brand_voice_guide
        self.llm = ChatOpenAI(model=llm_model, temperature=0.7)
        self.agent = DeepAgent(
            name="content_agent",
            system_prompt=f"""You are the Content Personalization Agent.

Brand Voice Guide:
{brand_voice_guide}

Your responsibilities:
1. Generate email content variants for each subscriber segment
2. Personalize content using subscriber data (name, preferences, past behavior)
3. Maintain brand voice consistency across all variants
4. Create both HTML and plain text versions
5. Include clear, compelling calls-to-action
6. Optimize for accessibility (alt text, semantic HTML)
7. Ensure CAN-SPAM compliance (physical address, unsubscribe link)

Personalization techniques:
- Dynamic content blocks based on segment
- Product recommendations from purchase history
- Location-specific offers and events
- Engagement-based tone adjustment
- Name personalization (first name only, never full name in subject)""",
            tools=[
                self.get_subscriber_profile,
                self.get_recommendations,
                self.render_template,
                self.validate_compliance,
            ],
            model=llm_model,
        )

    @tool
    def get_subscriber_profile(self, subscriber_id: str) -> dict:
        """Retrieve full subscriber profile for personalization."""
        query = """
            SELECT s.*, e.total_opens, e.total_clicks, e.last_open_date,
                   p.preferred_categories, p.preferred_send_frequency,
                   p.last_purchase_date, p.total_spend
            FROM subscribers s
            LEFT JOIN engagement_summary e ON s.subscriber_id = e.subscriber_id
            LEFT JOIN subscriber_preferences p ON s.subscriber_id = p.subscriber_id
            WHERE s.subscriber_id = %s
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (subscriber_id,))
                columns = [desc[0] for desc in cur.description]
                row = cur.fetchone()
                return dict(zip(columns, row)) if row else {}

    @tool
    def get_recommendations(self, subscriber_id: str, category: str, count: int = 3) -> list[dict]:
        """Get product/content recommendations based on subscriber history."""
        query = """
            WITH subscriber_vector AS (
                SELECT embedding FROM subscriber_embeddings WHERE subscriber_id = %s
            )
            SELECT c.content_id, c.title, c.category, c.url,
                   1 - (se.embedding <=> (SELECT embedding FROM subscriber_vector)) as similarity
            FROM content_items se
            JOIN content c ON se.content_id = c.content_id
            WHERE c.category = %s
            ORDER BY se.embedding <=> (SELECT embedding FROM subscriber_vector)
            LIMIT %s
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (subscriber_id, category, count))
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    @tool
    def render_template(self, template_id: str, personalization_data: dict) -> dict:
        """Render an email template with personalization data."""
        template = self.load_template(template_id)
        # Use Jinja2 for template rendering
        from jinja2 import Template
        tmpl = Template(template["body_html"])
        rendered_html = tmpl.render(**personalization_data)
        tmpl_txt = Template(template["body_text"])
        rendered_text = tmpl_txt.render(**personalization_data)
        return {
            "body_html": rendered_html,
            "body_text": rendered_text,
            "subject_line": Template(template["subject"]).render(**personalization_data),
        }

    @tool
    def validate_compliance(self, content: dict) -> dict:
        """Validate email content for CAN-SPAM and GDPR compliance."""
        issues = []
        if "unsubscribe" not in content.get("body_html", "").lower():
            issues.append("Missing unsubscribe link")
        if "physical" not in content.get("body_html", "").lower() and "{organization_address}" not in content.get("body_html", ""):
            issues.append("Missing physical address")
        if len(content.get("subject_line", "")) > 100:
            issues.append("Subject line exceeds 100 characters")
        return {"is_compliant": len(issues) == 0, "issues": issues}

    def generate_campaign_content(self, campaign_id: str, segments: list[dict], brief: dict) -> dict:
        """Generate content variants for all segments."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.agent.system_prompt),
            ("human", """Generate email content for campaign '{campaign_id}'.

Campaign Brief:
{brief}

Segments:
{segments}

For each segment, create 2 content variants (A/B test).
Each variant should include: subject_line, preheader, body_html, body_text, personalization_tokens.

Ensure:
- Subject lines are under 60 characters
- Preheader complements (doesn't repeat) subject
- HTML is responsive and accessible
- Plain text version is included
- Unsubscribe link and physical address are present
- Brand voice is consistent"""),
        ])

        chain = prompt | self.llm | PydanticOutputParser(pydantic_object=EmailVariant)
        result = chain.invoke({
            "campaign_id": campaign_id,
            "brief": json.dumps(brief),
            "segments": json.dumps(segments),
        })
        return result
```

### 3.3 Personalization Levels

| Level | Technique | Example |
|-------|-----------|---------|
| **Segment-level** | Different content per segment | "Welcome back, lapsed reader!" vs "Welcome, new subscriber!" |
| **Individual-level** | Subscriber-specific data | Name, past purchases, browsing history |
| **Behavioral** | Trigger-based content | Abandoned cart, browse abandonment |
| **Contextual** | Time/weather/location | "Rainy day in Seattle? Here's what to read..." |
| **Predictive** | ML-predicted preferences | Recommended articles based on embedding similarity |

### 3.4 Email Template Structure

```html
<!-- templates/base_email.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject_line }}</title>
    <!--[if mso]>
    <style>table { border-collapse: collapse; }</style>
    <![endif]-->
</head>
<body style="margin:0; padding:0; background-color:#f4f4f4;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;">
        <tr>
            <td align="center" style="padding:20px 0;">
                <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:8px;">
                    <!-- Header -->
                    <tr>
                        <td style="padding:30px 40px; text-align:center; background-color:{{ brand_color }};">
                            <img src="{{ logo_url }}" alt="{{ organization_name }}" width="150" style="max-width:150px;">
                        </td>
                    </tr>
                    <!-- Personalized Greeting -->
                    <tr>
                        <td style="padding:30px 40px 10px;">
                            <h1 style="margin:0; font-size:24px; color:#333;">{% if first_name %}Hi {{ first_name }},{% else %}Hi there,{% endif %}</h1>
                        </td>
                    </tr>
                    <!-- Dynamic Content Block -->
                    <tr>
                        <td style="padding:10px 40px;">
                            {{ dynamic_content | safe }}
                        </td>
                    </tr>
                    <!-- Product Recommendations (if applicable) -->
                    {% if recommendations %}
                    <tr>
                        <td style="padding:20px 40px;">
                            <h2 style="font-size:18px; color:#333;">Recommended for you</h2>
                            {% for item in recommendations %}
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:15px;">
                                <tr>
                                    <td width="80">
                                        <img src="{{ item.image_url }}" alt="{{ item.title }}" width="80" style="border-radius:4px;">
                                    </td>
                                    <td style="padding-left:15px;">
                                        <a href="{{ item.url }}?utm_source=email&utm_medium=email&utm_campaign={{ campaign_id }}&subscriber={{ subscriber_id }}" style="color:{{ brand_color }}; text-decoration:none; font-weight:bold;">{{ item.title }}</a>
                                        <p style="margin:5px 0 0; color:#666; font-size:14px;">{{ item.description }}</p>
                                    </td>
                                </tr>
                            </table>
                            {% endfor %}
                        </td>
                    </tr>
                    {% endif %}
                    <!-- CTA -->
                    <tr>
                        <td style="padding:20px 40px; text-align:center;">
                            <a href="{{ cta_url }}?utm_source=email&utm_medium=email&utm_campaign={{ campaign_id }}&subscriber={{ subscriber_id }}" style="display:inline-block; padding:14px 32px; background-color:{{ brand_color }}; color:#ffffff; text-decoration:none; border-radius:6px; font-weight:bold;">{{ cta_text }}</a>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding:30px 40px; background-color:#f9f9f9; text-align:center; font-size:12px; color:#999;">
                            <p>{{ organization_name }}<br>{{ organization_address }}</p>
                            <p>
                                <a href="{{ unsubscribe_url }}" style="color:#999; text-decoration:underline;">Unsubscribe</a> |
                                <a href="{{ preferences_url }}" style="color:#999; text-decoration:underline;">Email Preferences</a> |
                                <a href="{{ view_in_browser_url }}" style="color:#999; text-decoration:underline;">View in Browser</a>
                            </p>
                            <p>You received this email because you subscribed to {{ organization_name }}.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
```

---

## 4. Send Time Optimization Agent Implementation

### 4.1 Purpose

Determines the optimal send time for each subscriber based on their historical engagement patterns, timezone, and behavioral data to maximize open rates.

### 4.2 Architecture

```python
# agents/send_time_agent.py
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
from datetime import datetime, timedelta
import pytz
import numpy as np
from collections import Counter

class SendTimeAgent:
    """Agent that determines optimal send times per subscriber."""

    def __init__(self, db_url: str, llm_model: str = "gpt-4o"):
        self.db_url = db_url
        self.agent = DeepAgent(
            name="send_time_agent",
            system_prompt="""You are the Send Time Optimization Agent.

Your responsibilities:
1. Analyze each subscriber's historical open/click times
2. Determine the optimal send time window for each subscriber
3. Respect subscriber timezone and local business hours
4. Avoid sending during typical sleep hours (10 PM - 6 AM local)
5. Consider day-of-week patterns
6. Stagger sends to avoid thundering herd (max 1000 emails/minute)
7. Prioritize higher-engagement subscribers for prime time slots

Send time factors (weighted):
- Historical open time: 40%
- Day-of-week pattern: 25%
- Timezone/business hours: 20%
- Engagement recency: 15%

Output: For each subscriber, provide optimal_send_time (UTC), timezone, and confidence_score.""",
            tools=[
                self.get_engagement_history,
                self.analyze_time_patterns,
                self.get_subscriber_timezone,
                self.calculate_optimal_window,
                self.stagger_schedule,
            ],
            model=llm_model,
        )

    @tool
    def get_engagement_history(self, subscriber_id: str, days: int = 90) -> list[dict]:
        """Get historical engagement timestamps for a subscriber."""
        query = """
            SELECT event_type, event_timestamp, timezone
            FROM campaign_events
            WHERE subscriber_id = %s
              AND event_type IN ('open', 'click')
              AND event_timestamp > NOW() - INTERVAL '%s days'
            ORDER BY event_timestamp DESC
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (subscriber_id, days))
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    @tool
    def analyze_time_patterns(self, engagement_history: list[dict]) -> dict:
        """Analyze engagement history to find optimal send time patterns."""
        if not engagement_history:
            return {"optimal_hour": 10, "optimal_day": "Tuesday", "confidence": 0.3}

        hours = []
        days = []
        for event in engagement_history:
            ts = event["event_timestamp"]
            if event.get("timezone"):
                tz = pytz.timezone(event["timezone"])
                ts = ts.replace(tzinfo=pytz.UTC).astimezone(tz)
            hours.append(ts.hour)
            days.append(ts.strftime("%A"))

        # Find peak hour (mode of hours)
        hour_counts = Counter(hours)
        optimal_hour = hour_counts.most_common(1)[0][0]

        # Find peak day
        day_counts = Counter(days)
        optimal_day = day_counts.most_common(1)[0][0]

        # Calculate confidence based on data volume and consistency
        total_events = len(engagement_history)
        top_hour_ratio = hour_counts.most_common(1)[0][1] / total_events
        confidence = min(0.95, (total_events / 50) * 0.5 + top_hour_ratio * 0.5)

        return {
            "optimal_hour": optimal_hour,
            "optimal_day": optimal_day,
            "hour_distribution": dict(hour_counts),
            "day_distribution": dict(day_counts),
            "confidence": round(confidence, 2),
        }

    @tool
    def get_subscriber_timezone(self, subscriber_id: str) -> str:
        """Get subscriber's timezone from profile or infer from IP/country."""
        query = """
            SELECT timezone, country, last_ip_country
            FROM subscribers WHERE subscriber_id = %s
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (subscriber_id,))
                row = cur.fetchone()
                if row and row[0]:
                    return row[0]
                # Infer from country
                country_tz_map = {
                    "US": "America/New_York",
                    "GB": "Europe/London",
                    "DE": "Europe/Berlin",
                    "IN": "Asia/Kolkata",
                    "AE": "Asia/Dubai",
                    "AU": "Australia/Sydney",
                }
                return country_tz_map.get(row[1] if row else None, "UTC")

    @tool
    def calculate_optimal_window(self, patterns: dict, timezone: str, engagement_recency: str) -> dict:
        """Calculate the optimal send time window."""
        tz = pytz.timezone(timezone)
        optimal_hour = patterns["optimal_hour"]

        # Adjust for sleep hours (10 PM - 6 AM)
        if optimal_hour >= 22 or optimal_hour < 6:
            optimal_hour = 8  # Move to 8 AM

        # Adjust for weekends (engagement typically lower on weekends)
        optimal_day = patterns["optimal_day"]
        if optimal_day in ("Saturday", "Sunday"):
            optimal_day = "Tuesday"

        # Calculate next occurrence
        now = datetime.now(tz)
        target = now.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)

        days_ahead = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        current_day_idx = days_ahead.index(now.strftime("%A"))
        target_day_idx = days_ahead.index(optimal_day)
        delta = (target_day_idx - current_day_idx) % 7
        if delta == 0 and target <= now:
            delta = 7
        target += timedelta(days=delta)

        # Convert to UTC for storage
        target_utc = target.astimezone(pytz.UTC)

        return {
            "optimal_send_time_utc": target_utc.isoformat(),
            "optimal_send_time_local": target.isoformat(),
            "timezone": timezone,
            "confidence_score": patterns["confidence"],
            "rationale": f"Based on {patterns.get('hour_distribution', {})} engagement pattern",
        }

    @tool
    def stagger_schedule(self, send_times: list[dict], max_per_minute: int = 1000) -> list[dict]:
        """Stagger send times to avoid overwhelming the email provider."""
        # Sort by optimal send time
        sorted_times = sorted(send_times, key=lambda x: x["optimal_send_time_utc"])

        staggered = []
        current_minute = None
        count_in_minute = 0

        for entry in sorted_times:
            send_time = datetime.fromisoformat(entry["optimal_send_time_utc"])
            minute_key = send_time.replace(second=0, microsecond=0)

            if minute_key != current_minute:
                current_minute = minute_key
                count_in_minute = 0

            if count_in_minute >= max_per_minute:
                # Push to next minute
                current_minute += timedelta(minutes=1)
                count_in_minute = 0
                entry["optimal_send_time_utc"] = current_minute.isoformat()
                entry["staggered"] = True

            staggered.append(entry)
            count_in_minute += 1

        return staggered

    def optimize_send_times(self, campaign_id: str, subscribers: list[dict], segments: list[dict]) -> dict:
        """Calculate optimal send times for all subscribers."""
        results = []
        for sub in subscribers:
            history = self.get_engagement_history(sub["subscriber_id"])
            patterns = self.analyze_time_patterns(history)
            tz = self.get_subscriber_timezone(sub["subscriber_id"])
            window = self.calculate_optimal_window(patterns, tz, sub.get("last_open_date"))
            results.append({
                "subscriber_id": sub["subscriber_id"],
                **window,
            })

        staggered = self.stagger_schedule(results)
        return {"campaign_id": campaign_id, "send_schedule": staggered}
```

### 4.3 Send Time Optimization Algorithm

```
Input: Subscriber engagement history
Output: Optimal send time per subscriber

1. Collect all open/click timestamps (last 90 days)
2. Convert to subscriber's local timezone
3. Build hour-of-day histogram → find peak hour
4. Build day-of-week histogram → find peak day
5. Apply constraints:
   - No sends 10 PM - 6 AM local
   - No sends on holidays (check holiday calendar)
   - Weekend sends only for high-engagement subscribers
6. Calculate next valid occurrence
7. Stagger across minutes to respect rate limits
8. Assign confidence score based on data quality
```

---

## 5. Subject Line Optimization Agent Implementation

### 5.1 Purpose

Generates, tests, and optimizes subject lines using LLM generation, A/B testing, and predictive open-rate scoring.

### 5.2 Architecture

```python
# agents/subject_line_agent.py
from langchain_deepagents import DeepAgent
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
import random

class SubjectLineAgent:
    """Agent that creates and optimizes subject lines."""

    def __init__(self, db_url: str, llm_model: str = "gpt-4o"):
        self.db_url = db_url
        self.llm = ChatOpenAI(model=llm_model, temperature=0.8)
        self.agent = DeepAgent(
            name="subject_line_agent",
            system_prompt="""You are the Subject Line Optimization Agent.

Your responsibilities:
1. Generate multiple subject line variants for A/B testing
2. Predict open rates for each variant
3. Optimize for different segments and contexts
4. Avoid spam trigger words and excessive punctuation
5. Ensure subject lines are mobile-friendly (under 40 characters ideal)
6. Balance curiosity, urgency, and clarity

Subject line best practices:
- Front-load important words (first 30 characters visible on mobile)
- Use numbers and specific data when possible
- Create curiosity gaps without being clickbait
- Personalize when relevant (name, location, behavior)
- Avoid: ALL CAPS, excessive !!!, spam triggers (FREE, ACT NOW, etc.)
- Test emoji usage (can increase opens but brand-dependent)

A/B test configuration:
- Minimum 2 variants, maximum 5
- Test sample size: 10% of segment per variant
- Test duration: 4 hours or 1000 opens per variant
- Winner selection: highest open rate with statistical significance (p < 0.05)""",
            tools=[
                self.generate_variants,
                self.predict_open_rate,
                self.check_spam_triggers,
                self.get_historical_performance,
                self.configure_ab_test,
            ],
            model=llm_model,
        )

    @tool
    def generate_variants(self, content_brief: dict, segment: dict, count: int = 3) -> list[dict]:
        """Generate subject line variants for a segment."""
        prompt = f"""Generate {count} subject line variants for the following email campaign.

Campaign brief: {content_brief}
Target segment: {segment['name']} - {segment['description']}
Segment characteristics: {segment.get('criteria', {})}

Requirements:
- Each variant should be under 60 characters (ideal: 30-40)
- Include at least one with a number/statistic
- Include at least one with personalization
- Include at least one with curiosity/urgency
- Avoid spam trigger words
- Mobile-optimized (important words in first 30 chars)

Return JSON array of variants with: subject_line, approach, predicted_open_rate"""

        response = self.llm.invoke(prompt)
        return json.loads(response.content)

    @tool
    def predict_open_rate(self, subject_line: str, segment: dict) -> float:
        """Predict open rate for a subject line based on historical data."""
        # Query similar subject lines from historical campaigns
        query = """
            SELECT AVG(open_rate) as avg_open_rate, COUNT(*) as sample_size
            FROM (
                SELECT campaign_id,
                       SUM(CASE WHEN event_type = 'open' THEN 1 ELSE 0 END)::float /
                       NULLIF(SUM(CASE WHEN event_type = 'delivered' THEN 1 ELSE 0 END), 0) as open_rate
                FROM campaign_events
                WHERE campaign_id IN (
                    SELECT campaign_id FROM campaigns
                    WHERE subject_line %s
                    AND created_at > NOW() - INTERVAL '180 days'
                )
                GROUP BY campaign_id
            ) subq
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (subject_line,))
                row = cur.fetchone()
                if row and row[1] and row[1] >= 10:
                    return round(row[0], 4)

        # Fallback: use LLM to estimate
        prompt = f"""Estimate the open rate for this subject line targeting {segment['name']}:
"{subject_line}"

Consider: length, personalization, urgency, curiosity, spam score.
Return a float between 0.05 and 0.45."""
        response = self.llm.invoke(prompt)
        return float(response.content.strip())

    @tool
    def check_spam_triggers(self, subject_line: str) -> dict:
        """Check subject line for spam trigger words and patterns."""
        spam_words = [
            "free", "act now", "urgent", "limited time", "click here",
            "buy now", "order now", "call now", "100%", "guarantee",
            "no obligation", "risk-free", "winner", "congratulations",
            "cash", "credit", "loan", "mortgage", "viagra", "weight loss",
        ]
        triggers_found = [w for w in spam_words if w in subject_line.lower()]

        issues = []
        if triggers_found:
            issues.append(f"Spam triggers: {', '.join(triggers_found)}")
        if subject_line.isupper():
            issues.append("ALL CAPS subject line")
        if subject_line.count("!") > 1:
            issues.append("Multiple exclamation marks")
        if "???" in subject_line:
            issues.append("Multiple question marks")
        if len(subject_line) > 100:
            issues.append("Exceeds 100 characters")

        spam_score = len(triggers_found) * 0.2 + len(issues) * 0.1
        return {
            "spam_score": min(1.0, spam_score),
            "triggers": triggers_found,
            "issues": issues,
            "is_clean": spam_score < 0.3,
        }

    @tool
    def get_historical_performance(self, segment_id: str) -> dict:
        """Get historical subject line performance for a segment."""
        query = """
            SELECT subject_line,
                   AVG(open_rate) as avg_open_rate,
                   AVG(click_rate) as avg_click_rate,
                   COUNT(*) as times_used
            FROM campaign_performance
            WHERE segment_id = %s
              AND created_at > NOW() - INTERVAL '180 days'
            GROUP BY subject_line
            ORDER BY avg_open_rate DESC
            LIMIT 10
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (segment_id,))
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    @tool
    def configure_ab_test(self, variants: list[dict], segment_size: int) -> dict:
        """Configure A/B test parameters."""
        num_variants = len(variants)
        test_sample_size = max(100, int(segment_size * 0.1))  # 10% for testing
        per_variant = test_sample_size // num_variants

        return {
            "test_type": "subject_line_ab",
            "variants": [{"variant_id": i, **v} for i, v in enumerate(variants)],
            "test_sample_size": test_sample_size,
            "per_variant_sample": per_variant,
            "test_duration_hours": 4,
            "min_opens_for_significance": 100,
            "confidence_level": 0.95,
            "selection_criteria": "highest_open_rate",
        }

    def optimize(self, campaign_id: str, content_variants: list[dict], audience: list[dict]) -> dict:
        """Generate and configure subject line A/B tests."""
        all_variants = []
        for segment in audience:
            variants = self.generate_variants(
                content_brief=content_variants[0],
                segment=segment,
                count=3,
            )
            # Filter out spammy variants
            clean_variants = []
            for v in variants:
                spam_check = self.check_spam_triggers(v["subject_line"])
                if spam_check["is_clean"]:
                    v["spam_score"] = spam_check["spam_score"]
                    v["predicted_open_rate"] = self.predict_open_rate(v["subject_line"], segment)
                    clean_variants.append(v)

            ab_config = self.configure_ab_test(clean_variants, segment["subscriber_count"])
            all_variants.append({
                "segment_id": segment["segment_id"],
                "segment_name": segment["name"],
                "variants": clean_variants,
                "ab_test_config": ab_config,
            })

        return {"campaign_id": campaign_id, "subject_line_tests": all_variants}
```

### 5.3 Subject Line Strategies

| Strategy | Template | Best For |
|----------|----------|----------|
| **Curiosity Gap** | "The [metric] that changed how we [outcome]" | Content, newsletters |
| **Urgency** | "Last chance: [offer] ends [deadline]" | Promotions, sales |
| **Social Proof** | "Join [number] [audience] who [benefit]" | Product launches |
| **Personalization** | "[First name], your [item] is waiting" | Re-engagement |
| **Question** | "Are you making this [common mistake]?" | Educational |
| **Number/List** | "7 ways to [achieve outcome]" | How-to content |
| **How-To** | "How to [achieve result] in [timeframe]" | Tutorials |
| **Behind the Scenes** | "Inside: How we [process/result]" | Brand storytelling |

---

## 6. List Hygiene Agent Implementation

### 6.1 Purpose

Maintains list health by identifying and removing invalid, risky, or unengaged subscribers, managing bounce/complaint handling, and ensuring deliverability.

### 6.2 Architecture

```python
# agents/list_hygiene_agent.py
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
import dns.resolver
import smtplib
import re

class ListHygieneAgent:
    """Agent that cleans and validates subscriber lists."""

    def __init__(self, db_url: str, llm_model: str = "gpt-4o"):
        self.db_url = db_url
        self.agent = DeepAgent(
            name="list_hygiene_agent",
            system_prompt="""You are the List Hygiene Agent.

Your responsibilities:
1. Validate email addresses (syntax, domain, MX records)
2. Identify and remove hard bounces
3. Process unsubscribe requests and suppressions
4. Flag spam complaints and abuse reports
5. Identify inactive/dormant subscribers
6. Detect duplicate and role-based accounts
7. Monitor sender reputation and deliverability
8. Ensure GDPR/CCPA compliance (right to be forgotten)

Hygiene rules:
- Remove hard bounces immediately
- Suppress after 1 spam complaint
- Flag subscribers with 0 opens in 90 days as "at-risk"
- Remove role-based emails (info@, admin@, support@) for B2C
- Validate MX records before sending
- Check against known disposable email providers
- Honor unsubscribe within 24 hours (CAN-SPAM: 10 business days max)

Output: Clean subscriber list with removal reasons and risk scores.""",
            tools=[
                self.validate_email_syntax,
                self.check_mx_records,
                self.check_disposable_domain,
                self.process_bounces,
                self.process_unsubscribes,
                self.identify_inactive,
                self.detect_duplicates,
                self.calculate_list_health_score,
            ],
            model=llm_model,
        )

    @tool
    def validate_email_syntax(self, email: str) -> dict:
        """Validate email address syntax."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, email))
        issues = []
        if not is_valid:
            issues.append("Invalid syntax")
        if ".." in email:
            issues.append("Double dots in email")
        if email.count("@") != 1:
            issues.append("Multiple @ symbols")
        return {"email": email, "is_valid": is_valid, "issues": issues}

    @tool
    def check_mx_records(self, domain: str) -> dict:
        """Check if domain has valid MX records."""
        try:
            answers = dns.resolver.resolve(domain, "MX")
            mx_records = [str(rdata.exchange) for rdata in answers]
            return {
                "domain": domain,
                "has_mx": True,
                "mx_records": mx_records,
                "is_valid": len(mx_records) > 0,
            }
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return {"domain": domain, "has_mx": False, "mx_records": [], "is_valid": False}

    @tool
    def check_disposable_domain(self, domain: str) -> dict:
        """Check if domain is a known disposable email provider."""
        disposable_domains = {
            "mailinator.com", "guerrillamail.com", "tempmail.com",
            "10minutemail.com", "yopmail.com", "throwaway.email",
            "fakeinbox.com", "sharklasers.com", "guerrillamailblock.com",
        }
        return {
            "domain": domain,
            "is_disposable": domain.lower() in disposable_domains,
        }

    @tool
    def process_bounces(self, campaign_id: str) -> dict:
        """Process bounce events from email provider webhooks."""
        query = """
            SELECT subscriber_id, bounce_type, bounce_reason, bounced_at
            FROM bounce_events
            WHERE campaign_id = %s
              AND processed = FALSE
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (campaign_id,))
                bounces = cur.fetchall()

        hard_bounces = []
        soft_bounces = []
        for sub_id, btype, reason, _ in bounces:
            if btype == "hard":
                hard_bounces.append(sub_id)
            else:
                soft_bounces.append(sub_id)

        # Remove hard bounces immediately
        if hard_bounces:
            cur.execute("""
                UPDATE subscribers SET status = 'bounced', updated_at = NOW()
                WHERE subscriber_id = ANY(%s)
            """, (hard_bounces,))

        # Track soft bounces (3+ = hard)
        if soft_bounces:
            cur.execute("""
                INSERT INTO soft_bounce_log (subscriber_id, bounce_count, last_bounce)
                VALUES (%s, 1, NOW())
                ON CONFLICT (subscriber_id) DO UPDATE
                SET bounce_count = soft_bounce_log.bounce_count + 1,
                    last_bounce = NOW()
            """, [(sid,) for sid in soft_bounces])

            # Convert to hard after 3 soft bounces
            cur.execute("""
                UPDATE subscribers SET status = 'bounced'
                WHERE subscriber_id IN (
                    SELECT subscriber_id FROM soft_bounce_log
                    WHERE bounce_count >= 3
                )
            """)

        conn.commit()
        return {
            "hard_bounces_removed": len(hard_bounces),
            "soft_bounces_tracked": len(soft_bounces),
        }

    @tool
    def process_unsubscribes(self, campaign_id: str) -> dict:
        """Process unsubscribe requests."""
        query = """
            SELECT subscriber_id, unsubscribed_at, reason
            FROM unsubscribe_events
            WHERE campaign_id = %s
              AND processed = FALSE
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (campaign_id,))
                unsubs = cur.fetchall()

        for sub_id, _, _ in unsubs:
            cur.execute("""
                UPDATE subscribers SET status = 'unsubscribed', updated_at = NOW()
                WHERE subscriber_id = %s
            """, (sub_id,))
            # Add to suppression list
            cur.execute("""
                INSERT INTO suppression_list (subscriber_id, reason, created_at)
                VALUES (%s, 'unsubscribe', NOW())
                ON CONFLICT DO NOTHING
            """, (sub_id,))

        conn.commit()
        return {"unsubscribes_processed": len(unsubs)}

    @tool
    def identify_inactive(self, days_threshold: int = 90) -> list[str]:
        """Identify subscribers with no engagement in the threshold period."""
        query = """
            SELECT s.subscriber_id
            FROM subscribers s
            LEFT JOIN engagement_summary e ON s.subscriber_id = e.subscriber_id
            WHERE s.status = 'active'
              AND (e.last_open_date IS NULL OR e.last_open_date < NOW() - INTERVAL '%s days')
              AND s.signup_date < NOW() - INTERVAL '%s days'
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (days_threshold, days_threshold))
                return [row[0] for row in cur.fetchall()]

    @tool
    def detect_duplicates(self) -> list[dict]:
        """Detect duplicate subscribers by email or similar profile."""
        query = """
            SELECT email, COUNT(*) as count, array_agg(subscriber_id) as ids
            FROM subscribers
            WHERE status = 'active'
            GROUP BY email
            HAVING COUNT(*) > 1
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return [{"email": row[0], "count": row[1], "ids": row[2]} for row in cur.fetchall()]

    @tool
    def calculate_list_health_score(self) -> dict:
        """Calculate overall list health score."""
        query = """
            SELECT
                COUNT(*) FILTER (WHERE status = 'active') as active_count,
                COUNT(*) FILTER (WHERE status = 'bounced') as bounced_count,
                COUNT(*) FILTER (WHERE status = 'unsubscribed') as unsubscribed_count,
                COUNT(*) FILTER (WHERE status = 'complained') as complained_count,
                COUNT(*) as total_count
            FROM subscribers
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
                active, bounced, unsubscribed, complained, total = row

                if total == 0:
                    return {"health_score": 0, "grade": "F"}

                # Health score: weighted penalty for bad addresses
                penalty = (bounced * 1.0 + complained * 2.0 + unsubscribed * 0.5) / total
                health_score = max(0, 1.0 - penalty)

                grade = "A" if health_score >= 0.95 else \
                        "B" if health_score >= 0.85 else \
                        "C" if health_score >= 0.70 else \
                        "D" if health_score >= 0.50 else "F"

                return {
                    "health_score": round(health_score, 4),
                    "grade": grade,
                    "active": active,
                    "bounced": bounced,
                    "unsubscribed": unsubscribed,
                    "complained": complained,
                    "total": total,
                    "recommendations": self._get_recommendations(health_score, bounced, complained),
                }

    def _get_recommendations(self, score: float, bounced: int, complained: int) -> list[str]:
        recs = []
        if score < 0.85:
            recs.append("Run full list validation (MX, syntax, disposable check)")
        if bounced > 100:
            recs.append("Review bounce handling — consider double opt-in")
        if complained > 10:
            recs.append("Investigate spam complaints — review content and targeting")
        if score < 0.70:
            recs.append("Consider list re-permission campaign")
        return recs

    def clean_list(self, campaign_id: str, subscriber_list: list[dict]) -> dict:
        """Execute full list hygiene pipeline."""
        results = {
            "campaign_id": campaign_id,
            "total_input": len(subscriber_list),
            "valid": [],
            "removed": [],
        }

        for sub in subscriber_list:
            email = sub["email"]
            # Step 1: Syntax validation
            syntax = self.validate_email_syntax(email)
            if not syntax["is_valid"]:
                results["removed"].append({"subscriber_id": sub["subscriber_id"], "reason": "invalid_syntax"})
                continue

            # Step 2: Disposable domain check
            domain = email.split("@")[1]
            if self.check_disposable_domain(domain)["is_disposable"]:
                results["removed"].append({"subscriber_id": sub["subscriber_id"], "reason": "disposable_domain"})
                continue

            # Step 3: MX record check
            mx = self.check_mx_records(domain)
            if not mx["is_valid"]:
                results["removed"].append({"subscriber_id": sub["subscriber_id"], "reason": "no_mx_record"})
                continue

            # Step 4: Suppression list check
            if self._is_suppressed(sub["subscriber_id"]):
                results["removed"].append({"subscriber_id": sub["subscriber_id"], "reason": "suppressed"})
                continue

            results["valid"].append(sub)

        # Process bounces and unsubscribes
        bounce_results = self.process_bounces(campaign_id)
        unsub_results = self.process_unsubscribes(campaign_id)

        # Calculate health score
        health = self.calculate_list_health_score()

        results.update({
            "valid_count": len(results["valid"]),
            "removed_count": len(results["removed"]),
            "bounce_processing": bounce_results,
            "unsubscribe_processing": unsub_results,
            "list_health": health,
        })

        return results

    def _is_suppressed(self, subscriber_id: str) -> bool:
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM suppression_list WHERE subscriber_id = %s", (subscriber_id,))
                return cur.fetchone() is not None
```

### 6.3 Hygiene Schedule

| Task | Frequency | Action |
|------|-----------|--------|
| Syntax validation | Per campaign | Validate all emails before send |
| MX record check | Per campaign | Verify domain deliverability |
| Bounce processing | Real-time (webhook) | Remove hard bounces immediately |
| Unsubscribe processing | Real-time (webhook) | Suppress within 24 hours |
| Inactive identification | Weekly | Flag 90-day inactive subscribers |
| Duplicate detection | Monthly | Merge or remove duplicates |
| List health score | Daily | Monitor overall list quality |
| Re-permission campaign | Quarterly | Re-engage inactive subscribers |
| Full list audit | Semi-annually | Comprehensive validation |

---

## 7. Performance Analytics Agent Implementation

### 7.1 Purpose

Tracks, analyzes, and reports on campaign performance metrics, provides actionable insights, and feeds learnings back into the optimization loop.

### 7.2 Architecture

```python
# agents/analytics_agent.py
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
from datetime import datetime, timedelta

class AnalyticsAgent:
    """Agent that tracks and analyzes campaign performance."""

    def __init__(self, db_url: str, llm_model: str = "gpt-4o"):
        self.db_url = db_url
        self.agent = DeepAgent(
            name="analytics_agent",
            system_prompt="""You are the Performance Analytics Agent.

Your responsibilities:
1. Track campaign performance metrics in real-time
2. Calculate key email marketing KPIs
3. Identify trends and anomalies
4. Compare performance against benchmarks and past campaigns
5. Generate actionable insights and recommendations
6. Create performance reports for stakeholders
7. Feed learnings back into the optimization loop

Key metrics to track:
- Delivery rate: delivered / sent
- Open rate: unique opens / delivered
- Click-through rate (CTR): unique clicks / delivered
- Click-to-open rate (CTOR): unique clicks / unique opens
- Bounce rate: bounces / sent
- Unsubscribe rate: unsubscribes / delivered
- Complaint rate: complaints / delivered
- Conversion rate: conversions / delivered
- Revenue per email: total revenue / delivered
- List growth rate: (new - unsubscribed) / total * 100

Benchmarks (industry average):
- Open rate: 20-25%
- CTR: 2-5%
- Bounce rate: < 2%
- Unsubscribe rate: < 0.5%
- Complaint rate: < 0.1%

Always provide context: compare to past campaigns, industry benchmarks, and segment performance.""",
            tools=[
                self.get_campaign_metrics,
                self.get_segment_breakdown,
                self.get_time_series,
                self.compare_to_benchmarks,
                self.detect_anomalies,
                self.generate_insights,
                self.create_report,
            ],
            model=llm_model,
        )

    @tool
    def get_campaign_metrics(self, campaign_id: str) -> dict:
        """Get comprehensive metrics for a campaign."""
        query = """
            SELECT
                COUNT(*) FILTER (WHERE event_type = 'sent') as sent,
                COUNT(*) FILTER (WHERE event_type = 'delivered') as delivered,
                COUNT(*) FILTER (WHERE event_type = 'open' AND is_unique) as unique_opens,
                COUNT(*) FILTER (WHERE event_type = 'click' AND is_unique) as unique_clicks,
                COUNT(*) FILTER (WHERE event_type = 'bounce') as bounces,
                COUNT(*) FILTER (WHERE event_type = 'unsubscribe') as unsubscribes,
                COUNT(*) FILTER (WHERE event_type = 'complaint') as complaints,
                COUNT(*) FILTER (WHERE event_type = 'conversion') as conversions,
                SUM(revenue) FILTER (WHERE event_type = 'conversion') as total_revenue
            FROM campaign_events
            WHERE campaign_id = %s
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (campaign_id,))
                row = cur.fetchone()
                sent, delivered, opens, clicks, bounces, unsubs, complaints, conversions, revenue = row

                return {
                    "campaign_id": campaign_id,
                    "sent": sent or 0,
                    "delivered": delivered or 0,
                    "unique_opens": opens or 0,
                    "unique_clicks": clicks or 0,
                    "bounces": bounces or 0,
                    "unsubscribes": unsubs or 0,
                    "complaints": complaints or 0,
                    "conversions": conversions or 0,
                    "total_revenue": float(revenue) if revenue else 0.0,
                    "delivery_rate": (delivered / sent) if sent else 0,
                    "open_rate": (opens / delivered) if delivered else 0,
                    "ctr": (clicks / delivered) if delivered else 0,
                    "ctor": (clicks / opens) if opens else 0,
                    "bounce_rate": (bounces / sent) if sent else 0,
                    "unsubscribe_rate": (unsubs / delivered) if delivered else 0,
                    "complaint_rate": (complaints / delivered) if delivered else 0,
                    "conversion_rate": (conversions / delivered) if delivered else 0,
                    "revenue_per_email": (float(revenue) / delivered) if delivered and revenue else 0,
                }

    @tool
    def get_segment_breakdown(self, campaign_id: str) -> list[dict]:
        """Get performance breakdown by segment."""
        query = """
            SELECT
                s.segment_id,
                s.name as segment_name,
                COUNT(*) FILTER (WHERE ce.event_type = 'delivered') as delivered,
                COUNT(*) FILTER (WHERE ce.event_type = 'open' AND ce.is_unique) as opens,
                COUNT(*) FILTER (WHERE ce.event_type = 'click' AND ce.is_unique) as clicks,
                COUNT(*) FILTER (WHERE ce.event_type = 'conversion') as conversions,
                SUM(ce.revenue) FILTER (WHERE ce.event_type = 'conversion') as revenue
            FROM campaign_events ce
            JOIN segment_subscribers s ON ce.subscriber_id = s.subscriber_id
            WHERE ce.campaign_id = %s
            GROUP BY s.segment_id, s.name
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (campaign_id,))
                columns = [desc[0] for desc in cur.description]
                results = []
                for row in cur.fetchall():
                    d = dict(zip(columns, row))
                    d["open_rate"] = (d["opens"] / d["delivered"]) if d["delivered"] else 0
                    d["ctr"] = (d["clicks"] / d["delivered"]) if d["delivered"] else 0
                    results.append(d)
                return results

    @tool
    def get_time_series(self, campaign_id: str, granularity: str = "hour") -> list[dict]:
        """Get time-series data for campaign events."""
        query = f"""
            SELECT
                date_trunc('{granularity}', event_timestamp) as time_bucket,
                event_type,
                COUNT(*) as count
            FROM campaign_events
            WHERE campaign_id = %s
            GROUP BY time_bucket, event_type
            ORDER BY time_bucket
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (campaign_id,))
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    @tool
    def compare_to_benchmarks(self, metrics: dict) -> dict:
        """Compare campaign metrics to industry benchmarks."""
        benchmarks = {
            "open_rate": {"min": 0.20, "target": 0.25, "max": 0.35},
            "ctr": {"min": 0.02, "target": 0.035, "max": 0.06},
            "bounce_rate": {"min": 0.0, "target": 0.01, "max": 0.02},
            "unsubscribe_rate": {"min": 0.0, "target": 0.002, "max": 0.005},
            "complaint_rate": {"min": 0.0, "target": 0.0005, "max": 0.001},
        }

        comparison = {}
        for metric, bench in benchmarks.items():
            value = metrics.get(metric, 0)
            if value < bench["min"]:
                status = "below_benchmark"
            elif value > bench["max"]:
                status = "above_benchmark" if metric in ("open_rate", "ctr") else "critical"
            elif value >= bench["target"]:
                status = "meeting_target"
            else:
                status = "approaching_target"

            comparison[metric] = {
                "value": round(value, 4),
                "benchmark_min": bench["min"],
                "benchmark_target": bench["target"],
                "benchmark_max": bench["max"],
                "status": status,
                "delta_from_target": round(value - bench["target"], 4),
            }

        return comparison

    @tool
    def detect_anomalies(self, campaign_id: str) -> list[dict]:
        """Detect anomalies in campaign performance."""
        anomalies = []

        # Check for sudden spike in unsubscribes
        query = """
            SELECT DATE_TRUNC('hour', event_timestamp) as hour,
                   COUNT(*) as unsub_count
            FROM campaign_events
            WHERE campaign_id = %s AND event_type = 'unsubscribe'
            GROUP BY hour
            HAVING COUNT(*) > (
                SELECT AVG(unsub_count) + 3 * STDDEV(unsub_count)
                FROM (
                    SELECT COUNT(*) as unsub_count
                    FROM campaign_events
                    WHERE event_type = 'unsubscribe'
                    GROUP BY DATE_TRUNC('hour', event_timestamp)
                ) subq
            )
        """
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (campaign_id,))
                for row in cur.fetchall():
                    anomalies.append({
                        "type": "unsubscribe_spike",
                        "hour": row[0],
                        "count": row[1],
                        "severity": "high",
                    })

        # Check for delivery rate drop
        metrics = self.get_campaign_metrics(campaign_id)
        if metrics["delivery_rate"] < 0.95:
            anomalies.append({
                "type": "delivery_rate_drop",
                "value": metrics["delivery_rate"],
                "severity": "critical" if metrics["delivery_rate"] < 0.90 else "medium",
            })

        return anomalies

    @tool
    def generate_insights(self, metrics: dict, segment_breakdown: list[dict], anomalies: list[dict]) -> list[str]:
        """Generate actionable insights from campaign data."""
        insights = []

        # Open rate insights
        if metrics["open_rate"] < 0.15:
            insights.append("Open rate is below 15%. Consider improving subject lines and sender name recognition.")
        elif metrics["open_rate"] > 0.30:
            insights.append(f"Excellent open rate ({metrics['open_rate']:.1%}). Analyze what worked and replicate.")

        # CTR insights
        if metrics["ctr"] < 0.01:
            insights.append("CTR is below 1%. Review email content, CTA placement, and relevance to audience.")

        # Segment insights
        if segment_breakdown:
            best = max(segment_breakdown, key=lambda x: x["open_rate"])
            worst = min(segment_breakdown, key=lambda x: x["open_rate"])
            if best["open_rate"] > worst["open_rate"] * 2:
                insights.append(f"Large segment performance gap: '{best['segment_name']}' ({best['open_rate']:.1%}) vs '{worst['segment_name']}' ({worst['open_rate']:.1%}). Consider separate content strategies.")

        # Anomaly insights
        for anomaly in anomalies:
            if anomaly["type"] == "unsubscribe_spike":
                insights.append(f"Unsubscribe spike detected at {anomaly['hour']}. Review content sent in that hour.")
            elif anomaly["type"] == "delivery_rate_drop":
                insights.append(f"Delivery rate dropped to {anomaly['value']:.1%}. Check sender reputation and list quality.")

        # Revenue insights
        if metrics["revenue_per_email"] > 0:
            insights.append(f"Revenue per email: ${metrics['revenue_per_email']:.2f}. Total attributed revenue: ${metrics['total_revenue']:.2f}.")

        return insights

    @tool
    def create_report(self, campaign_id: str, format: str = "markdown") -> str:
        """Create a comprehensive campaign performance report."""
        metrics = self.get_campaign_metrics(campaign_id)
        segments = self.get_segment_breakdown(campaign_id)
        benchmarks = self.compare_to_benchmarks(metrics)
        anomalies = self.detect_anomalies(campaign_id)
        insights = self.generate_insights(metrics, segments, anomalies)

        report = f"""# Campaign Performance Report: {campaign_id}

Generated: {datetime.utcnow().isoformat()}

## Executive Summary

| Metric | Value | Benchmark | Status |
|--------|-------|-----------|--------|
| Delivery Rate | {metrics['delivery_rate']:.1%} | >95% | {'✅' if metrics['delivery_rate'] > 0.95 else '⚠️'} |
| Open Rate | {metrics['open_rate']:.1%} | 20-25% | {'✅' if metrics['open_rate'] > 0.20 else '⚠️'} |
| CTR | {metrics['ctr']:.1%} | 2-5% | {'✅' if metrics['ctr'] > 0.02 else '⚠️'} |
| Bounce Rate | {metrics['bounce_rate']:.1%} | <2% | {'✅' if metrics['bounce_rate'] < 0.02 else '⚠️'} |
| Unsubscribe Rate | {metrics['unsubscribe_rate']:.1%} | <0.5% | {'✅' if metrics['unsubscribe_rate'] < 0.005 else '⚠️'} |
| Complaint Rate | {metrics['complaint_rate']:.1%} | <0.1% | {'✅' if metrics['complaint_rate'] < 0.001 else '⚠️'} |

## Key Metrics

- **Total Sent:** {metrics['sent']:,}
- **Delivered:** {metrics['delivered']:,}
- **Unique Opens:** {metrics['unique_opens']:,}
- **Unique Clicks:** {metrics['unique_clicks']:,}
- **Conversions:** {metrics['conversions']:,}
- **Total Revenue:** ${metrics['total_revenue']:,.2f}
- **Revenue per Email:** ${metrics['revenue_per_email']:.2f}

## Segment Performance

| Segment | Delivered | Opens | Clicks | Open Rate | CTR |
|---------|-----------|-------|--------|-----------|-----|
"""
        for seg in segments:
            report += f"| {seg['segment_name']} | {seg['delivered']:,} | {seg['opens']:,} | {seg['clicks']:,} | {seg['open_rate']:.1%} | {seg['ctr']:.1%} |\n"

        report += f"""
## Anomalies Detected

"""
        if anomalies:
            for a in anomalies:
                report += f"- **{a['type']}** (severity: {a['severity']})\n"
        else:
            report += "No anomalies detected.\n"

        report += f"""
## Insights & Recommendations

"""
        for i, insight in enumerate(insights, 1):
            report += f"{i}. {insight}\n"

        return report

    def analyze(self, campaign_id: str) -> dict:
        """Run full analytics pipeline for a campaign."""
        metrics = self.get_campaign_metrics(campaign_id)
        segments = self.get_segment_breakdown(campaign_id)
        benchmarks = self.compare_to_benchmarks(metrics)
        anomalies = self.detect_anomalies(campaign_id)
        insights = self.generate_insights(metrics, segments, anomalies)
        report = self.create_report(campaign_id)

        return {
            "campaign_id": campaign_id,
            "metrics": metrics,
            "segment_breakdown": segments,
            "benchmark_comparison": benchmarks,
            "anomalies": anomalies,
            "insights": insights,
            "report": report,
        }
```

### 7.3 Analytics Dashboard Schema

```sql
-- analytics tables
CREATE TABLE campaign_events (
    event_id BIGSERIAL PRIMARY KEY,
    campaign_id UUID REFERENCES campaigns(campaign_id),
    subscriber_id UUID REFERENCES subscribers(subscriber_id),
    event_type VARCHAR(50) NOT NULL,  -- sent, delivered, open, click, bounce, unsubscribe, complaint, conversion
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    is_unique BOOLEAN DEFAULT FALSE,
    url_clicked TEXT,
    revenue DECIMAL(10,2),
    metadata JSONB,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_campaign_events_campaign ON campaign_events(campaign_id);
CREATE INDEX idx_campaign_events_subscriber ON campaign_events(subscriber_id);
CREATE INDEX idx_campaign_events_type ON campaign_events(event_type);
CREATE INDEX idx_campaign_events_timestamp ON campaign_events(event_timestamp);

CREATE TABLE campaign_daily_stats (
    campaign_id UUID REFERENCES campaigns(campaign_id),
    date DATE NOT NULL,
    sent INTEGER DEFAULT 0,
    delivered INTEGER DEFAULT 0,
    opens INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    bounces INTEGER DEFAULT 0,
    unsubscribes INTEGER DEFAULT 0,
    complaints INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0,
    PRIMARY KEY (campaign_id, date)
);
```

---

## 8. Code Examples and Snippets

### 8.1 Project Structure

```
email-marketing-agents/
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── segmentation_agent.py
│   ├── content_agent.py
│   ├── send_time_agent.py
│   ├── subject_line_agent.py
│   ├── list_hygiene_agent.py
│   └── analytics_agent.py
├── tools/
│   ├── __init__.py
│   ├── database.py
│   ├── email_provider.py
│   ├── template_engine.py
│   └── validation.py
├── schemas/
│   ├── __init__.py
│   ├── agents.py
│   ├── campaigns.py
│   └── events.py
├── templates/
│   ├── base_email.html
│   ├── welcome_series.html
│   ├── re_engagement.html
│   └── promotional.html
├── workflows/
│   ├── __init__.py
│   ├── campaign_workflow.py
│   └── automation_workflow.py
├── tests/
│   ├── test_segmentation.py
│   ├── test_content.py
│   ├── test_send_time.py
│   ├── test_subject_line.py
│   ├── test_list_hygiene.py
│   └── test_analytics.py
├── config.py
├── main.py
├── requirements.txt
└── docker-compose.yml
```

### 8.2 Configuration

```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/email_marketing"
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM
    OPENAI_API_KEY: str
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.7

    # Email Provider
    SENDGRID_API_KEY: str
    FROM_EMAIL: str = "noreply@example.com"
    FROM_NAME: str = "Example Company"

    # Rate Limiting
    MAX_EMAILS_PER_MINUTE: int = 1000
    MAX_EMAILS_PER_DAY: int = 50000

    # LangSmith
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "email-marketing-agents"

    # Brand
    BRAND_VOICE_GUIDE: str = """
    - Tone: Professional but approachable
    - Language: Clear, concise, jargon-free
    - Values: Transparency, customer-first, data-driven
    - Avoid: Hype, false urgency, clickbait
    """

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

### 8.3 FastAPI Application

```python
# main.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from workflows.campaign_workflow import execute_campaign_workflow
from agents.analytics_agent import AnalyticsAgent
from config import get_settings

app = FastAPI(title="AI Email Marketing Agents", version="1.0.0")
settings = get_settings()

class CampaignRequest(BaseModel):
    campaign_id: str
    goal: str
    subscriber_list: list[dict]
    brief: dict
    scheduled_send_time: Optional[str] = None

class AnalyticsRequest(BaseModel):
    campaign_id: str

@app.post("/campaigns")
async def create_campaign(request: CampaignRequest, background_tasks: BackgroundTasks):
    """Create and execute a new email marketing campaign."""
    # Validate and queue the campaign workflow
    task = execute_campaign_workflow.delay(request.dict())
    return {
        "status": "queued",
        "task_id": task.id,
        "campaign_id": request.campaign_id,
    }

@app.get("/campaigns/{campaign_id}/status")
async def get_campaign_status(campaign_id: str):
    """Get the status of a campaign execution."""
    # Check Celery task status
    from celery.result import AsyncResult
    # ... implementation
    return {"campaign_id": campaign_id, "status": "running"}

@app.post("/analytics/{campaign_id}")
async def get_campaign_analytics(campaign_id: str):
    """Get analytics for a completed campaign."""
    analytics_agent = AnalyticsAgent(db_url=settings.DATABASE_URL)
    result = analytics_agent.analyze(campaign_id)
    return result

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

### 8.4 Docker Compose

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/email_marketing
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: celery -A workflows.campaign_workflow worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/email_marketing
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
    depends_on:
      - db
      - redis

  scheduler:
    build: .
    command: celery -A workflows.campaign_workflow beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=email_marketing
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 8.5 Requirements

```txt
# requirements.txt
langchain>=0.3.0
langchain-deepagents>=0.1.0
langchain-openai>=0.2.0
langchain-core>=0.3.0
langsmith>=0.1.0
openai>=1.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
celery>=5.3.0
redis>=5.0.0
psycopg2-binary>=2.9.0
pgvector>=0.2.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
jinja2>=3.1.0
pytz>=2023.3
dnspython>=2.4.0
numpy>=1.24.0
python-dotenv>=1.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
```

### 8.6 Webhook Handler

```python
# webhooks/sendgrid.py
from fastapi import APIRouter, Request
from typing import List
import hmac
import hashlib
import base64

router = APIRouter()

@router.post("/webhooks/sendgrid")
async def handle_sendgrid_webhook(request: Request):
    """Handle SendGrid event webhooks."""
    events = await request.json()
    signature = request.headers.get("X-Twilio-Email-Event-Webhook-Signature", "")
    timestamp = request.headers.get("X-Twilio-Email-Event-Webhook-Timestamp", "")

    # Verify webhook signature
    if not verify_sendgrid_signature(await request.body(), signature, timestamp):
        return {"error": "Invalid signature"}, 401

    for event in events:
        await process_sendgrid_event(event)

    return {"processed": len(events)}

async def process_sendgrid_event(event: dict):
    """Process a single SendGrid event."""
    event_type = event.get("event")
    campaign_id = event.get("campaign_id")
    subscriber_id = event.get("subscriber_id")

    event_mapping = {
        "delivered": "delivered",
        "open": "open",
        "click": "click",
        "bounce": "bounce",
        "unsubscribe": "unsubscribe",
        "spamreport": "complaint",
        "dropped": "bounce",
    }

    mapped_type = event_mapping.get(event_type)
    if mapped_type:
        await store_event(campaign_id, subscriber_id, mapped_type, event)

async def store_event(campaign_id: str, subscriber_id: str, event_type: str, raw_event: dict):
    """Store event in database."""
    query = """
        INSERT INTO campaign_events (campaign_id, subscriber_id, event_type, metadata, event_timestamp)
        VALUES (%s, %s, %s, %s, NOW())
    """
    with psycopg2.connect(settings.DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (campaign_id, subscriber_id, event_type, json.dumps(raw_event)))
        conn.commit()
```

---

## 9. Testing Strategy

### 9.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5 tests)
                    │  Tests  │  Full campaign lifecycle
                   �┴─────────┴┐
                   │ Integration│  (20 tests)
                   │   Tests    │  Agent + DB + Provider
                  �┴────────────┴┐
                  │    Unit       │  (100+ tests)
                  │    Tests      │  Individual functions
                 ┴───────────────┴
```

### 9.2 Unit Tests

```python
# tests/test_segmentation.py
import pytest
from agents.segmentation_agent import SegmentationAgent
from unittest.mock import MagicMock, patch

@pytest.fixture
def segmentation_agent():
    return SegmentationAgent(db_url="postgresql://test:test@localhost:5432/test")

class TestSegmentationAgent:
    def test_get_subscriber_data_returns_active_subscribers(self, segmentation_agent):
        """Test that only active subscribers are returned."""
        with patch.object(segmentation_agent, 'get_subscriber_data') as mock_get:
            mock_get.return_value = [
                {"subscriber_id": "1", "email": "test@example.com", "status": "active"},
            ]
            result = segmentation_agent.get_subscriber_data({"country": "US"})
            assert len(result) == 1
            assert result[0]["email"] == "test@example.com"

    def test_score_segment_engagement_calculation(self, segmentation_agent):
        """Test engagement score calculation."""
        with patch('psycopg2.connect') as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = (1000, 0.25, 0.05)
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

            score = segmentation_agent.score_segment_engagement({"engagement_level": 1})
            assert score == 0.17  # 0.25 * 0.6 + 0.05 * 0.4

    def test_validate_segment_size_minimum(self, segmentation_agent):
        """Test segment size validation."""
        result = segmentation_agent.validate_segment_size(["id"] * 50)
        assert result["is_valid"] is False
        assert result["recommendation"] == "merge_with_similar_segment"

        result = segmentation_agent.validate_segment_size(["id"] * 150)
        assert result["is_valid"] is True

    def test_create_behavioral_embedding(self, segmentation_agent):
        """Test behavioral embedding creation."""
        subscriber_data = {
            "total_opens": 50,
            "emails_received": 100,
            "last_open_date": "2026-09-01",
            "preferences": {"category": "technology"},
            "demographics": {"country": "US"},
        }
        embedding = segmentation_agent.create_behavioral_embedding(subscriber_data)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
```

```python
# tests/test_content.py
import pytest
from agents.content_agent import ContentAgent

@pytest.fixture
def content_agent():
    return ContentAgent(brand_voice_guide="Professional but approachable")

class TestContentAgent:
    def test_validate_compliance_detects_missing_unsubscribe(self, content_agent):
        """Test that missing unsubscribe link is detected."""
        content = {
            "body_html": "<html><body>Hello</body></html>",
            "subject_line": "Test",
        }
        result = content_agent.validate_compliance(content)
        assert result["is_compliant"] is False
        assert "Missing unsubscribe link" in result["issues"]

    def test_validate_compliance_passes_valid_content(self, content_agent):
        """Test that compliant content passes validation."""
        content = {
            "body_html": """
                <html><body>
                <p>Hello</p>
                <a href="https://example.com/unsubscribe">Unsubscribe</a>
                <p>123 Main St, City, ST 12345</p>
                </body></html>
            """,
            "subject_line": "Test Subject",
        }
        result = content_agent.validate_compliance(content)
        assert result["is_compliant"] is True

    def test_render_template_with_personalization(self, content_agent):
        """Test template rendering with personalization data."""
        with patch.object(content_agent, 'load_template') as mock_load:
            mock_load.return_value = {
                "body_html": "Hello {{ first_name }}, check out {{ product_name }}",
                "body_text": "Hello {{ first_name }}, check out {{ product_name }}",
                "subject": "Special offer for {{ first_name }}",
            }
            result = content_agent.render_template("test_template", {
                "first_name": "Ahmed",
                "product_name": "AI Course",
            })
            assert "Ahmed" in result["body_html"]
            assert "AI Course" in result["body_html"]
```

```python
# tests/test_send_time.py
import pytest
from datetime import datetime
from agents.send_time_agent import SendTimeAgent

@pytest.fixture
def send_time_agent():
    return SendTimeAgent(db_url="postgresql://test:test@localhost:5432/test")

class TestSendTimeAgent:
    def test_analyze_time_patterns_with_no_history(self, send_time_agent):
        """Test default patterns when no engagement history exists."""
        result = send_time_agent.analyze_time_patterns([])
        assert result["optimal_hour"] == 10
        assert result["confidence"] == 0.3

    def test_analyze_time_patterns_finds_peak_hour(self, send_time_agent):
        """Test that peak hour is correctly identified."""
        history = [
            {"event_timestamp": datetime(2026, 9, 1, 9, 0), "timezone": "US/Eastern"},
            {"event_timestamp": datetime(2026, 9, 2, 9, 0), "timezone": "US/Eastern"},
            {"event_timestamp": datetime(2026, 9, 3, 10, 0), "timezone": "US/Eastern"},
            {"event_timestamp": datetime(2026, 9, 4, 9, 0), "timezone": "US/Eastern"},
        ]
        result = send_time_agent.analyze_time_patterns(history)
        assert result["optimal_hour"] == 9
        assert result["confidence"] > 0.3

    def test_calculate_optimal_window_avoids_sleep_hours(self, send_time_agent):
        """Test that send times during sleep hours are adjusted."""
        patterns = {"optimal_hour": 23, "confidence": 0.8}
        result = send_time_agent.calculate_optimal_window(patterns, "US/Eastern", "2026-09-01")
        # Should be moved to 8 AM
        send_time = datetime.fromisoformat(result["optimal_send_time_local"])
        assert send_time.hour == 8

    def test_stagger_schedule_respects_rate_limit(self, send_time_agent):
        """Test that schedule is staggered to respect rate limits."""
        send_times = [
            {"subscriber_id": f"sub_{i}", "optimal_send_time_utc": "2026-10-01T10:00:00+00:00"}
            for i in range(1500)
        ]
        result = send_time_agent.stagger_schedule(send_times, max_per_minute=1000)
        # First 1000 should be at 10:00, next 500 at 10:01
        assert result[0]["optimal_send_time_utc"] == "2026-10-01T10:00:00+00:00"
        assert result[999]["optimal_send_time_utc"] == "2026-10-01T10:00:00+00:00"
        assert result[1000]["optimal_send_time_utc"] == "2026-10-01T10:01:00+00:00"
        assert result[1000]["staggered"] is True
```

```python
# tests/test_subject_line.py
import pytest
from agents.subject_line_agent import SubjectLineAgent

@pytest.fixture
def subject_line_agent():
    return SubjectLineAgent(db_url="postgresql://test:test@localhost:5432/test")

class TestSubjectLineAgent:
    def test_check_spam_triggers_detects_spam_words(self, subject_line_agent):
        """Test spam trigger detection."""
        result = subject_line_agent.check_spam_triggers("FREE ACT NOW!!! Click here to win!")
        assert result["is_clean"] is False
        assert "free" in result["triggers"]
        assert "act now" in result["triggers"]

    def test_check_spam_triggers_passes_clean_subject(self, subject_line_agent):
        """Test that clean subject lines pass."""
        result = subject_line_agent.check_spam_triggers("Your weekly digest: 5 stories worth reading")
        assert result["is_clean"] is True
        assert result["spam_score"] == 0.0

    def test_configure_ab_test_splits_evenly(self, subject_line_agent):
        """Test A/B test configuration."""
        variants = [
            {"subject_line": "Variant A"},
            {"subject_line": "Variant B"},
            {"subject_line": "Variant C"},
        ]
        result = subject_line_agent.configure_ab_test(variants, segment_size=10000)
        assert result["test_sample_size"] == 1000  # 10% of 10000
        assert result["per_variant_sample"] == 333  # 1000 / 3
        assert result["confidence_level"] == 0.95
```

```python
# tests/test_list_hygiene.py
import pytest
from agents.list_hygiene_agent import ListHygieneAgent

@pytest.fixture
def list_hygiene_agent():
    return ListHygieneAgent(db_url="postgresql://test:test@localhost:5432/test")

class TestListHygieneAgent:
    def test_validate_email_syntax_valid(self, list_hygiene_agent):
        """Test valid email syntax."""
        result = list_hygiene_agent.validate_email_syntax("test@example.com")
        assert result["is_valid"] is True

    def test_validate_email_syntax_invalid(self, list_hygiene_agent):
        """Test invalid email syntax."""
        result = list_hygiene_agent.validate_email_syntax("invalid..email@@example.com")
        assert result["is_valid"] is False
        assert len(result["issues"]) > 0

    def test_check_disposable_domain(self, list_hygiene_agent):
        """Test disposable domain detection."""
        result = list_hygiene_agent.check_disposable_domain("mailinator.com")
        assert result["is_disposable"] is True

        result = list_hygiene_agent.check_disposable_domain("gmail.com")
        assert result["is_disposable"] is False

    def test_identify_inactive_subscribers(self, list_hygiene_agent):
        """Test inactive subscriber identification."""
        with patch('psycopg2.connect') as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = [("sub_1",), ("sub_2",)]
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

            result = list_hygiene_agent.identify_inactive(days_threshold=90)
            assert len(result) == 2

    def test_calculate_list_health_score(self, list_hygiene_agent):
        """Test list health score calculation."""
        with patch('psycopg2.connect') as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = (950, 30, 10, 5, 1000)  # active, bounced, unsub, complained, total
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

            result = list_hygiene_agent.calculate_list_health_score()
            assert result["grade"] in ("A", "B", "C", "D", "F")
            assert 0 <= result["health_score"] <= 1.0
```

```python
# tests/test_analytics.py
import pytest
from agents.analytics_agent import AnalyticsAgent

@pytest.fixture
def analytics_agent():
    return AnalyticsAgent(db_url="postgresql://test:test@localhost:5432/test")

class TestAnalyticsAgent:
    def test_get_campaign_metrics_calculates_rates(self, analytics_agent):
        """Test that metrics are correctly calculated."""
        with patch('psycopg2.connect') as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = (1000, 950, 200, 50, 30, 10, 2, 25, 500.0)
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

            result = analytics_agent.get_campaign_metrics("campaign_1")
            assert result["delivery_rate"] == 0.95
            assert result["open_rate"] == pytest.approx(0.2105, rel=0.01)
            assert result["ctr"] == pytest.approx(0.0526, rel=0.01)
            assert result["bounce_rate"] == 0.03

    def test_compare_to_benchmarks(self, analytics_agent):
        """Test benchmark comparison."""
        metrics = {
            "open_rate": 0.22,
            "ctr": 0.03,
            "bounce_rate": 0.01,
            "unsubscribe_rate": 0.003,
            "complaint_rate": 0.0005,
        }
        result = analytics_agent.compare_to_benchmarks(metrics)
        assert result["open_rate"]["status"] == "approaching_target"
        assert result["ctr"]["status"] == "approaching_target"

    def test_detect_anomalies_finds_unsubscribe_spike(self, analytics_agent):
        """Test anomaly detection for unsubscribe spikes."""
        with patch('psycopg2.connect') as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = [("2026-10-01 10:00:00", 50)]
            mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cur

            result = analytics_agent.detect_anomalies("campaign_1")
            assert len(result) > 0
            assert result[0]["type"] == "unsubscribe_spike"

    def test_generate_insights_low_open_rate(self, analytics_agent):
        """Test insight generation for low open rate."""
        metrics = {"open_rate": 0.10, "ctr": 0.005, "revenue_per_email": 0.5}
        segments = []
        anomalies = []
        insights = analytics_agent.generate_insights(metrics, segments, anomalies)
        assert any("Open rate is below 15%" in i for i in insights)
```

### 9.3 Integration Tests

```python
# tests/integration/test_campaign_workflow.py
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from workflows.campaign_workflow import execute_campaign_workflow

@pytest.fixture(scope="module")
def postgres():
    with PostgresContainer("pgvector/pgvector:pg16") as pg:
        yield pg.get_connection_url()

@pytest.fixture(scope="module")
def redis():
    with RedisContainer("redis:7-alpine") as redis:
        yield redis.get_connection_url()

@pytest.mark.integration
class TestCampaignWorkflow:
    def test_full_campaign_lifecycle(self, postgres, redis):
        """Test the complete campaign workflow from creation to analytics."""
        campaign_config = {
            "campaign_id": "test-campaign-001",
            "goal": "Re-engage lapsed subscribers",
            "subscriber_list": [
                {"subscriber_id": f"sub_{i}", "email": f"user{i}@example.com"}
                for i in range(200)
            ],
            "brief": {
                "subject": "We miss you!",
                "content_type": "re_engagement",
                "offer": "20% off your next purchase",
            },
        }

        # Execute workflow
        result = execute_campaign_workflow(campaign_config)

        assert result["status"] == "completed"
        assert result["correlation_id"] is not None

    def test_list_hygiene_removes_invalid_emails(self, postgres, redis):
        """Test that list hygiene removes invalid emails before sending."""
        campaign_config = {
            "campaign_id": "test-campaign-002",
            "goal": "Test hygiene",
            "subscriber_list": [
                {"subscriber_id": "sub_1", "email": "valid@example.com"},
                {"subscriber_id": "sub_2", "email": "invalid..email@example.com"},
                {"subscriber_id": "sub_3", "email": "test@mailinator.com"},
            ],
            "brief": {"subject": "Test", "content_type": "test"},
        }

        result = execute_campaign_workflow(campaign_config)
        assert result["status"] == "completed"
        # Invalid emails should be removed
        assert result["hygiene_result"]["removed_count"] == 2
```

### 9.4 End-to-End Tests

```python
# tests/e2e/test_email_delivery.py
import pytest
import time
from main import app
from httpx import AsyncClient

@pytest.mark.e2e
@pytest.mark.asyncio
class TestEmailDelivery:
    async def test_campaign_creation_and_tracking(self):
        """Test full campaign creation, sending, and tracking flow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create campaign
            response = await client.post("/campaigns", json={
                "campaign_id": "e2e-test-001",
                "goal": "Test campaign",
                "subscriber_list": [
                    {"subscriber_id": f"sub_{i}", "email": f"user{i}@example.com"}
                    for i in range(10)
                ],
                "brief": {"subject": "Test", "content_type": "test"},
            })
            assert response.status_code == 200
            task_id = response.json()["task_id"]

            # Poll for completion
            for _ in range(30):
                status_resp = await client.get(f"/campaigns/e2e-test-001/status")
                if status_resp.json()["status"] == "completed":
                    break
                time.sleep(2)

            # Get analytics
            analytics_resp = await client.post("/analytics/e2e-test-001")
            assert analytics_resp.status_code == 200
            data = analytics_resp.json()
            assert "metrics" in data
            assert "insights" in data
```

### 9.5 Test Execution

```bash
# Run all unit tests
pytest tests/ -v --tb=short

# Run with coverage
pytest tests/ --cov=agents --cov=workflows --cov-report=html

# Run integration tests (requires Docker)
pytest tests/integration/ -v --integration

# Run E2E tests (requires full stack)
pytest tests/e2e/ -v --e2e

# Run specific agent tests
pytest tests/test_segmentation.py -v

# Run with LangSmith tracing
LANGCHAIN_TRACING_V2=true pytest tests/ -v
```

### 9.6 Quality Gates

| Gate | Threshold | Tool |
|------|-----------|------|
| Unit test coverage | ≥ 80% | pytest-cov |
| Integration test pass rate | 100% | pytest |
| LLM output validity | ≥ 95% | Custom validator |
| API response time | < 500ms p95 | Locust |
| Email delivery rate | > 95% | SendGrid stats |
| Agent error rate | < 1% | LangSmith |

---

## Appendix A: Environment Variables

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/email_marketing
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
SENDGRID_API_KEY=SG.xxx
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=email-marketing-agents
FROM_EMAIL=noreply@example.com
FROM_NAME="Example Company"
MAX_EMAILS_PER_MINUTE=1000
MAX_EMAILS_PER_DAY=50000
```

## Appendix B: Deployment Checklist

- [ ] Set up PostgreSQL with pgvector extension
- [ ] Configure Redis for Celery broker and caching
- [ ] Set up SendGrid/Mailgun account with verified domain
- [ ] Configure SPF, DKIM, DMARC records
- [ ] Set up LangSmith for observability
- [ ] Deploy API service (FastAPI + Uvicorn)
- [ ] Deploy Celery workers
- [ ] Deploy Celery beat scheduler
- [ ] Configure webhook endpoints for email events
- [ ] Set up monitoring and alerting (Prometheus + Grafana)
- [ ] Configure log aggregation (ELK or similar)
- [ ] Set up CI/CD pipeline
- [ ] Run full test suite
- [ ] Load test with production-like volume
- [ ] Document runbooks for common failures

---

*End of Implementation Plan*
