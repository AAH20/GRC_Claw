# Agentic Customer Journey Orchestration Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build an agentic AI system using LangChain DeepAgents that autonomously maps, personalizes, orchestrates, and optimizes multi-channel customer journeys in real time.

**Architecture:** A hub-and-spoke agent architecture where a central Journey Orchestrator agent delegates to specialized sub-agents (Journey Mapper, Personalization Engine, Channel Dispatcher, Predictive Analytics, CRM/CDP Integrator). DeepAgents' built-in planning, tool use, and sub-agent delegation handle complex multi-step customer interactions. Event-driven triggers feed real-time signals into the orchestrator, which adapts journeys dynamically.

**Tech Stack:** LangChain DeepAgents, LangGraph (stateful orchestration), Python 3.11+, FastAPI (API layer), Redis (session/state store), Apache Kafka (event streaming), PostgreSQL (journey definitions), MLflow (model registry), pytest (testing).

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Journey Mapping Agent Implementation](#2-journey-mapping-agent-implementation)
3. [Personalization Engine](#3-personalization-engine)
4. [Multi-Channel Orchestration](#4-multi-channel-orchestration)
5. [Real-Time Adaptation](#5-real-time-adaptation)
6. [Predictive Journey Analytics](#6-predictive-journey-analytics)
7. [CRM and CDP Integration](#7-crm-and-cdp-integration)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### Overview

The system uses a **hub-and-spoke multi-agent architecture** built on LangChain DeepAgents. A central `JourneyOrchestratorAgent` receives customer events, maintains journey state, and delegates to specialized sub-agents via DeepAgents' `write_todos` and sub-agent invocation patterns.

### Agent Topology

```
┌─────────────────────────────────────────────────────────┐
│                  JourneyOrchestratorAgent                │
│  (Central hub: planning, state management, delegation)   │
├─────────┬──────────┬──────────┬──────────┬──────────────┤
│ Journey │Personal- │ Channel  │Predictive│  CRM/CDP    │
│ Mapper  │ization   │Dispatch  │Analytics │  Integrator  │
│ Agent   │Engine    │Agent     │Agent     │  Agent       │
└─────────┴──────────┴──────────┴──────────┴──────────────┘
         │          │          │          │              │
    ┌────▼────┐ ┌──▼───┐ ┌───▼───┐ ┌───▼────┐ ┌──────▼──────┐
    │Journey  │ │User  │ │Email  │ │Churn   │ │Salesforce   │
    │Graph DB │ │Profile│ │SMS    │ │Model   │ │Segment      │
    │         │ │Store  │ │Push   │ │LTV     │ │ CDP         │
    │         │ │       │ │Web    │ │Model   │ │             │
    └─────────┘ └──────┘ └───────┘ └────────┘ └─────────────┘
```

### Core Design Principles

- **Single Responsibility:** Each agent owns one domain (mapping, personalization, dispatch, analytics, integration)
- **Stateless Sub-Agents:** Sub-agents receive context via tool inputs, not shared memory
- **Event-Driven:** Kafka events trigger orchestrator evaluation; no polling loops
- **Human-in-the-Loop:** High-stakes journey changes (discounts >20%, churn-save offers) require approval via DeepAgents' `interrupt` mechanism
- **Observability:** Every agent decision is logged with reasoning trace for audit and debugging

### Agent Communication Protocol

All inter-agent communication uses a standardized `AgentMessage` schema:

```python
from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime

class AgentMessage(BaseModel):
    source_agent: str
    target_agent: str
    message_type: Literal["request", "response", "event", "approval_needed"]
    payload: dict[str, Any]
    correlation_id: str  # Links request-response pairs
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(ge=0.0, le=1.0)  # Agent's confidence in output
```

### State Management

Journey state is persisted in Redis with a 30-day TTL, keyed by `customer_id:journey_id`:

```python
# Redis key structure
journey:{customer_id}:{journey_id} → JSON serialized JourneyState
session:{customer_id} → JSON serialized CustomerSession
```

---

## 2. Journey Mapping Agent Implementation

### Purpose

The `JourneyMappingAgent` discovers, models, and updates customer journey graphs. It converts raw event streams into structured journey stages, identifies transition patterns, and detects journey deviations.

### Journey Graph Data Model

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class JourneyStage(str, Enum):
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    EVALUATION = "evaluation"
    PURCHASE = "purchase"
    ONBOARDING = "onboarding"
    RETENTION = "retention"
    ADVOCACY = "advocacy"
    CHURN_RISK = "churn_risk"
    CHURNED = "churned"

class JourneyTransition(BaseModel):
    from_stage: JourneyStage
    to_stage: JourneyStage
    trigger_event: str
    probability: float  # Historical transition probability
    avg_duration_hours: float
    conditions: dict[str, Any] = Field(default_factory=dict)

class CustomerJourneyState(BaseModel):
    customer_id: str
    journey_id: str
    current_stage: JourneyStage
    stage_entered_at: datetime
    stage_history: list[dict] = Field(default_factory=list)
    next_best_action: Optional[str] = None
    churn_probability: float = 0.0
    predicted_ltv: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### Agent Implementation

```python
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

# ── Tools available to JourneyMappingAgent ──

@tool
def get_customer_events(customer_id: str, lookback_hours: int = 72) -> list[dict]:
    """Retrieve recent customer events from the event store."""
    # Queries Kafka consumer / event store
    ...

@tool
def get_journey_graph(journey_id: str) -> dict:
    """Load the journey graph definition with all stages and transitions."""
    # Queries PostgreSQL journey_definitions table
    ...

@tool
def update_journey_state(customer_id: str, journey_id: str,
                         new_stage: JourneyStage, reason: str) -> dict:
    """Atomically update customer's journey stage in Redis."""
    ...

@tool
def detect_stage_anomaly(customer_id: str, current_events: list[dict]) -> dict:
    """Use statistical models to detect unusual journey patterns."""
    ...

@tool
def suggest_journey_optimization(journey_id: str) -> list[dict]:
    """Analyze aggregate journey data and suggest graph improvements."""
    ...

# ── Agent Construction ──

journey_mapping_agent = DeepAgent(
    name="journey_mapper",
    system_prompt="""You are a journey mapping specialist. Your job is to:
1. Analyze customer event sequences to determine current journey stage
2. Detect transitions between stages based on trigger events
3. Identify anomalies (stalled journeys, skipped stages, regression)
4. Suggest journey graph optimizations based on aggregate patterns

Always provide confidence scores for your stage assignments.
When confidence < 0.7, flag for human review.""",
    tools=[
        get_customer_events,
        get_journey_graph,
        update_journey_state,
        detect_stage_anomaly,
        suggest_journey_optimization,
    ],
    model="claude-sonnet-4-20250514",
)
```

### Journey State Machine (LangGraph)

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class JourneyMappingState(TypedDict):
    customer_id: str
    journey_id: str
    events: list[dict]
    current_stage: JourneyStage
    proposed_stage: JourneyStage
    confidence: float
    needs_review: bool
    messages: Annotated[list, operator.add]

def route_journey_decision(state: JourneyMappingState) -> str:
    if state["needs_review"]:
        return "human_review"
    if state["proposed_stage"] == state["current_stage"]:
        return END
    return "apply_transition"

journey_graph = StateGraph(JourneyMappingState)
journey_graph.add_node("analyze_events", analyze_events_node)
journey_graph.add_node("detect_transition", detect_transition_node)
journey_graph.add_node("apply_transition", apply_transition_node)
journey_graph.add_node("human_review", human_review_node)

journey_graph.set_entry_point("analyze_events")
journey_graph.add_edge("analyze_events", "detect_transition")
journey_graph.add_conditional_edges("detect_transition", route_journey_decision)
journey_graph.add_edge("apply_transition", END)
journey_graph.add_edge("human_review", END)

journey_mapping_workflow = journey_graph.compile()
```

### Stage Detection Logic

```python
STAGE_TRANSITION_RULES = {
    (JourneyStage.AWARENESS, JourneyStage.CONSIDERATION): {
        "triggers": ["product_page_view", "pricing_page_view", "demo_request"],
        "min_events": 2,
        "time_window_hours": 48,
    },
    (JourneyStage.CONSIDERATION, JourneyStage.EVALUATION): {
        "triggers": ["free_trial_signup", "comparison_page_view", "review_read"],
        "min_events": 1,
        "time_window_hours": 72,
    },
    (JourneyStage.EVALUATION, JourneyStage.PURCHASE): {
        "triggers": ["cart_add", "checkout_start", "payment_info_entered"],
        "min_events": 1,
        "time_window_hours": 24,
    },
    (JourneyStage.PURCHASE, JourneyStage.ONBOARDING): {
        "triggers": ["payment_success", "account_created"],
        "min_events": 1,
        "time_window_hours": 1,
    },
    (JourneyStage.ONBOARDING, JourneyStage.RETENTION): {
        "triggers": ["first_value_milestone", "onboarding_complete"],
        "min_events": 1,
        "time_window_hours": 168,  # 7 days
    },
    (JourneyStage.RETENTION, JourneyStage.ADVOCACY): {
        "triggers": ["referral_sent", "review_submitted", "nps_promoter"],
        "min_events": 1,
        "time_window_hours": 720,  # 30 days
    },
    (JourneyStage.RETENTION, JourneyStage.CHURN_RISK): {
        "triggers": ["login_decline_30d", "support_ticket_escalated",
                     "competitor_mention", "usage_drop_50pct"],
        "min_events": 2,
        "time_window_hours": 72,
    },
}
```

---

## 3. Personalization Engine

### Purpose

The `PersonalizationEngineAgent` generates personalized content, offers, timing, and channel preferences for each customer interaction. It combines collaborative filtering, contextual bandits, and LLM-based content generation.

### Architecture

```
┌──────────────────────────────────────────────┐
│         PersonalizationEngineAgent            │
├──────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────────┐   │
│  │ User Profile │  │ Real-time Context    │   │
│  │ Enrichment   │  │ Collector            │   │
│  └──────┬──────┘  └──────────┬───────────┘   │
│         │                    │               │
│         ▼                    ▼               │
│  ┌──────────────────────────────────────┐    │
│  │     Personalization Orchestrator      │    │
│  │  ┌─────────┐ ┌──────────┐ ┌───────┐ │    │
│  │  │Offer    │ │Content   │ │Timing │ │    │
│  │  │Selector │ │Generator │ │Optim. │ │    │
│  │  │(Bandit) │ │(LLM)     │ │(ML)   │ │    │
│  │  └─────────┘ └──────────┘ └───────┘ │    │
│  └──────────────────────────────────────┘    │
│         │                                    │
│         ▼                                    │
│  ┌──────────────────────────────────────┐    │
│  │     Channel Preference Model         │    │
│  └──────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

### Implementation

```python
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
import numpy as np

@tool
def get_user_profile(customer_id: str) -> dict:
    """Fetch enriched user profile from CDP."""
    # Returns: demographics, purchase history, browsing patterns,
    # engagement scores, lifetime value, preferences
    ...

@tool
def get_realtime_context(customer_id: str) -> dict:
    """Collect real-time session context."""
    # Returns: current page, session duration, cart contents,
    # device, location, time of day, referrer
    ...

@tool
def select_offer(customer_id: str, context: dict,
                 available_offers: list[dict]) -> dict:
    """Use contextual bandit to select optimal offer."""
    ...

@tool
def generate_personalized_content(customer_id: str, template_id: str,
                                   context: dict) -> dict:
    """Generate personalized copy using LLM with user profile context."""
    ...

@tool
def optimize_send_time(customer_id: str, channel: str) -> dict:
    """Predict optimal send time based on historical engagement."""
    ...

@tool
def get_channel_preferences(customer_id: str) -> dict:
    """Return channel preference scores and frequency caps."""
    ...

personalization_agent = DeepAgent(
    name="personalization_engine",
    system_prompt="""You are a personalization specialist. Your job is to:
1. Select the best offer for each customer using contextual bandits
2. Generate personalized content that resonates with the user's context
3. Determine optimal timing and channel for each interaction
4. Respect frequency caps and channel preferences
5. Balance exploration (new offers) with exploitation (known preferences)

Always provide a personalization rationale for audit purposes.""",
    tools=[
        get_user_profile,
        get_realtime_context,
        select_offer,
        generate_personalized_content,
        optimize_send_time,
        get_channel_preferences,
    ],
    model="claude-sonnet-4-20250514",
)
```

### Contextual Bandit for Offer Selection

```python
from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class Offer:
    offer_id: str
    offer_type: str  # discount, free_shipping, bundle, loyalty_points
    value: float
    cost: float
    constraints: dict  # min_tenure, max_uses, eligible_segments

class ContextualBanditOfferSelector:
    """
    LinUCB-based contextual bandit for offer selection.
    Balances exploration and exploitation using confidence bounds.
    """

    def __init__(self, n_features: int, alpha: float = 1.0):
        self.alpha = alpha
        self.n_features = n_features
        # One A matrix and b vector per offer
        self.A: dict[str, np.ndarray] = {}
        self.b: dict[str, np.ndarray] = {}

    def _init_offer(self, offer_id: str):
        if offer_id not in self.A:
            self.A[offer_id] = np.eye(self.n_features)
            self.b[offer_id] = np.zeros(self.n_features)

    def select_offer(self, context: np.ndarray,
                     available_offers: list[Offer]) -> tuple[str, float]:
        """Select offer with highest UCB score. Returns (offer_id, confidence)."""
        best_offer = None
        best_score = -np.inf

        for offer in available_offers:
            self._init_offer(offer.offer_id)
            A_inv = np.linalg.inv(self.A[offer.offer_id])
            theta = A_inv @ self.b[offer.offer_id]

            # UCB score: expected reward + exploration bonus
            expected_reward = theta @ context
            exploration = self.alpha * np.sqrt(context @ A_inv @ context)
            ucb_score = expected_reward + exploration

            if ucb_score > best_score:
                best_score = ucb_score
                best_offer = offer.offer_id

        confidence = 1.0 / (1.0 + np.exp(-best_score))  # sigmoid
        return best_offer, confidence

    def update(self, offer_id: str, context: np.ndarray, reward: float):
        """Update bandit parameters after observing reward."""
        self._init_offer(offer_id)
        self.A[offer_id] += np.outer(context, context)
        self.b[offer_id] += reward * context
```

### Content Generation with Guardrails

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

CONTENT_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a marketing copywriter. Generate personalized content
that is relevant, engaging, and respectful of the customer's context.

Rules:
- Never use high-pressure sales language
- Respect the customer's communication preferences
- Include a clear, single call-to-action
- Maximum 150 characters for SMS, 500 for email body
- Always include unsubscribe option reference

Customer Profile: {user_profile}
Context: {realtime_context}
Template Requirements: {template_requirements}
Selected Offer: {offer_details}"""),
    ("human", "Generate {content_type} content for {customer_id}"),
])

class GeneratedContent(BaseModel):
    subject_line: Optional[str] = None
    body: str
    call_to_action: str
    personalization_tokens: dict[str, str]
    content_score: float  # Predicted engagement score

content_chain = CONTENT_GENERATION_PROMPT | llm | PydanticOutputParser(pydantic_object=GeneratedContent)
```

---

## 4. Multi-Channel Orchestration

### Purpose

The `ChannelOrchestrationAgent` decides which channel(s) to use for each interaction, manages cross-channel sequencing, handles frequency capping, and ensures consistent messaging across touchpoints.

### Channel Decision Matrix

```python
from enum import Enum

class Channel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push_notification"
    IN_APP = "in_app_message"
    WEBHOOK = "webhook"
    DIRECT_MAIL = "direct_mail"
    PHONE = "phone_call"
    CHAT = "chat_widget"

class ChannelPriority:
    """Priority rules for channel selection based on urgency and context."""

    URGENCY_CHANNEL_MAP = {
        "critical": [Channel.SMS, Channel.PUSH, Channel.PHONE],
        "high": [Channel.PUSH, Channel.SMS, Channel.IN_APP],
        "normal": [Channel.EMAIL, Channel.IN_APP, Channel.PUSH],
        "low": [Channel.EMAIL, Channel.IN_APP],
    }

    JOURNEY_STAGE_CHANNELS = {
        JourneyStage.AWARENESS: [Channel.EMAIL, Channel.IN_APP],
        JourneyStage.CONSIDERATION: [Channel.EMAIL, Channel.PUSH, Channel.IN_APP],
        JourneyStage.EVALUATION: [Channel.EMAIL, Channel.CHAT, Channel.SMS],
        JourneyStage.PURCHASE: [Channel.EMAIL, Channel.SMS, Channel.PUSH],
        JourneyStage.ONBOARDING: [Channel.EMAIL, Channel.IN_APP, Channel.PUSH],
        JourneyStage.RETENTION: [Channel.EMAIL, Channel.IN_APP, Channel.PUSH],
        JourneyStage.ADVOCACY: [Channel.EMAIL, Channel.IN_APP],
        JourneyStage.CHURN_RISK: [Channel.SMS, Channel.EMAIL, Channel.PHONE],
        JourneyStage.CHURNED: [Channel.EMAIL, Channel.DIRECT_MAIL],
    }
```

### Implementation

```python
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool

@tool
def check_frequency_cap(customer_id: str, channel: Channel,
                        window_hours: int = 24) -> dict:
    """Check if customer has exceeded frequency cap for this channel."""
    ...

@tool
def get_channel_health(channel: Channel) -> dict:
    """Check delivery health metrics for a channel."""
    # Returns: delivery_rate, latency, error_rate, provider_status
    ...

@tool
def dispatch_message(customer_id: str, channel: Channel,
                     content: dict, journey_context: dict) -> dict:
    """Send message through the specified channel provider."""
    ...

@tool
def schedule_followup(customer_id: str, channel: Channel,
                      content: dict, delay_hours: float,
                      condition: str) -> dict:
    """Schedule a conditional follow-up message."""
    ...

@tool
def get_cross_channel_context(customer_id: str) -> dict:
    """Get recent cross-channel interaction history."""
    ...

channel_orchestration_agent = DeepAgent(
    name="channel_orchestrator",
    system_prompt="""You are a multi-channel orchestration specialist. Your job is to:
1. Select the optimal channel based on urgency, journey stage, and preferences
2. Sequence messages across channels for maximum impact
3. Enforce frequency caps to prevent over-communication
4. Handle channel fallback when primary channel fails
5. Ensure message consistency across all touchpoints

Always check frequency caps before dispatching.
Always have a fallback channel ready.""",
    tools=[
        check_frequency_cap,
        get_channel_health,
        dispatch_message,
        schedule_followup,
        get_cross_channel_context,
    ],
    model="claude-sonnet-4-20250514",
)
```

### Cross-Channel Sequencing Engine

```python
from datetime import datetime, timedelta
from typing import Optional

class JourneySequenceStep(BaseModel):
    step_number: int
    channel: Channel
    delay_hours: float  # Hours after previous step
    content_template_id: str
    condition: Optional[str] = None  # e.g., "not_opened_previous"
    fallback_channel: Optional[Channel] = None
    exit_condition: Optional[str] = None  # e.g., "purchased", "unsubscribed"

class JourneySequence(BaseModel):
    sequence_id: str
    name: str
    trigger_event: str
    steps: list[JourneySequenceStep]
    max_duration_days: int = 14
    exit_on_conversion: bool = True

# Example: Abandoned cart recovery sequence
abandoned_cart_sequence = JourneySequence(
    sequence_id="abandoned_cart_v2",
    name="Abandoned Cart Recovery",
    trigger_event="cart_abandoned",
    steps=[
        JourneySequenceStep(
            step_number=1,
            channel=Channel.EMAIL,
            delay_hours=1,
            content_template_id="cart_reminder_1h",
            fallback_channel=Channel.PUSH,
        ),
        JourneySequenceStep(
            step_number=2,
            channel=Channel.PUSH,
            delay_hours=23,
            content_template_id="cart_reminder_24h",
            condition="not_opened_step_1",
            fallback_channel=Channel.SMS,
        ),
        JourneySequenceStep(
            step_number=3,
            channel=Channel.EMAIL,
            delay_hours=48,
            content_template_id="cart_discount_offer",
            condition="not_purchased",
            fallback_channel=None,
        ),
    ],
    max_duration_days=5,
    exit_on_conversion=True,
)
```

### Channel Dispatch with Fallback

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class ChannelDispatcher:
    def __init__(self):
        self.providers: dict[Channel, BaseChannelProvider] = {
            Channel.EMAIL: EmailProvider(),
            Channel.SMS: SMSProvider(),
            Channel.PUSH: PushNotificationProvider(),
            Channel.IN_APP: InAppMessageProvider(),
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def dispatch_with_fallback(
        self,
        customer_id: str,
        primary_channel: Channel,
        content: dict,
        fallback_channel: Optional[Channel] = None,
    ) -> dict:
        """Dispatch message with automatic fallback on failure."""
        result = await self._try_dispatch(customer_id, primary_channel, content)

        if not result["success"] and fallback_channel:
            result = await self._try_dispatch(customer_id, fallback_channel, content)
            result["used_fallback"] = True
            result["original_channel"] = primary_channel

        return result

    async def _try_dispatch(self, customer_id: str, channel: Channel,
                            content: dict) -> dict:
        provider = self.providers[channel]
        return await provider.send(customer_id, content)
```

---

## 5. Real-Time Adaptation

### Purpose

The system continuously monitors customer behavior and adapts journey execution in real time. This includes triggering immediate actions based on live events, adjusting journey paths, and suppressing irrelevant messages.

### Event Processing Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ Event    │───▶│ Kafka    │───▶│ Event        │───▶│ Real-Time    │
│ Sources  │    │ Topics   │    │ Router       │    │ Adaptation   │
│          │    │          │    │              │    │ Engine       │
└──────────┘    └──────────┘    └──────────────┘    └──────────────┘
                     │                                     │
                ┌────▼─────┐                        ┌──────▼──────┐
                │ customer │                        │ Journey     │
                │ events   │                        │ Orchestrator│
                │ journey  │                        │ Agent       │
                │ events   │                        └─────────────┘
                └──────────┘
```

### Implementation

```python
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
from confluent_kafka import Consumer, Producer
import json

@tool
def evaluate_trigger_condition(customer_id: str, event: dict,
                                active_journeys: list[dict]) -> list[dict]:
    """Evaluate if an event triggers any journey actions."""
    ...

@tool
def suppress_irrelevant_messages(customer_id: str,
                                  current_event: dict) -> list[str]:
    """Determine which scheduled messages should be suppressed."""
    # Example: If customer already purchased, suppress cart abandonment
    ...

@tool
def accelerate_journey(customer_id: str, journey_id: str,
                        target_stage: JourneyStage) -> dict:
    """Fast-forward a customer to a later journey stage."""
    ...

@tool
def trigger_re_engagement(customer_id: str,
                          last_engagement_days: int) -> dict:
    """Trigger a re-engagement campaign for dormant customers."""
    ...

@tool
def update_realtime_personalization(customer_id: str,
                                     event: dict) -> dict:
    """Update personalization context based on real-time behavior."""
    ...

real_time_adaptation_agent = DeepAgent(
    name="real_time_adapter",
    system_prompt="""You are a real-time journey adaptation specialist. Your job is to:
1. Evaluate incoming events against active journey triggers
2. Suppress messages that are no longer relevant
3. Accelerate journeys when customers show buying signals
4. Trigger re-engagement for dormant customers
5. Update personalization context in real-time

Act quickly but carefully. When in doubt, defer to the orchestrator.""",
    tools=[
        evaluate_trigger_condition,
        suppress_irrelevant_messages,
        accelerate_journey,
        trigger_re_engagement,
        update_realtime_personalization,
    ],
    model="claude-sonnet-4-20250514",
)
```

### Kafka Event Consumer

```python
from confluent_kafka import Consumer, KafkaError
import asyncio

class JourneyEventConsumer:
    def __init__(self, orchestrator_agent, config: dict):
        self.consumer = Consumer({
            "bootstrap.servers": config["kafka_brokers"],
            "group.id": "journey-orchestrator",
            "auto.offset.reset": "latest",
            "enable.auto.commit": False,
        })
        self.orchestrator = orchestrator_agent
        self.running = False

    async def start(self, topics: list[str]):
        self.consumer.subscribe(topics)
        self.running = True

        while self.running:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise Exception(msg.error())

            event = json.loads(msg.value().decode("utf-8"))
            await self._process_event(event)
            self.consumer.commit(message=msg)

    async def _process_event(self, event: dict):
        """Process a single event through the orchestrator."""
        result = await self.orchestrator.ainvoke({
            "messages": [{
                "role": "user",
                "content": f"Process this customer event: {json.dumps(event)}"
            }],
            "customer_id": event["customer_id"],
            "event_type": event["event_type"],
            "event_data": event["data"],
        })

        # Log the decision for observability
        await self._log_decision(event, result)

    async def stop(self):
        self.running = False
        self.consumer.close()
```

### Real-Time Decision Rules

```python
REAL_TIME_RULES = [
    {
        "rule_id": "suppress_after_purchase",
        "description": "Suppress cart abandonment if purchase completed",
        "trigger_event": "payment_success",
        "action": "suppress_sequence",
        "target_sequence": "abandoned_cart_v2",
        "scope": "customer",
    },
    {
        "rule_id": "accelerate_on_pricing_view",
        "description": "Move to evaluation stage on pricing page view",
        "trigger_event": "pricing_page_view",
        "condition": "current_stage == 'consideration'",
        "action": "accelerate_journey",
        "target_stage": "evaluation",
    },
    {
        "rule_id": "churn_intervention",
        "description": "Trigger churn save flow on cancellation intent",
        "trigger_event": "cancellation_page_view",
        "condition": "tenure_days > 30",
        "action": "trigger_sequence",
        "target_sequence": "churn_save_v1",
    },
    {
        "rule_id": "re_engagement_7d",
        "description": "Re-engage customers inactive for 7+ days",
        "trigger_event": "session_start",
        "condition": "days_since_last_engagement > 7",
        "action": "trigger_sequence",
        "target_sequence": "re_engagement_v1",
    },
]
```

---

## 6. Predictive Journey Analytics

### Purpose

The `PredictiveAnalyticsAgent` forecasts customer behavior (churn probability, LTV, next best action), identifies at-risk journeys, and provides aggregate insights for journey optimization.

### Models

```python
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime, timedelta

class ChurnPredictionModel:
    """Predicts 30-day churn probability."""

    FEATURES = [
        "days_since_last_login",
        "days_since_last_purchase",
        "session_count_7d",
        "session_count_30d",
        "avg_session_duration",
        "support_ticket_count_30d",
        "nps_score",
        "email_open_rate_30d",
        "push_opt_in_status",
        "tenure_days",
        "total_orders",
        "total_revenue",
        "discount_dependency_ratio",
    ]

    def __init__(self, model_path: str):
        self.model: Pipeline = joblib.load(model_path)

    def predict(self, customer_features: dict) -> dict:
        X = np.array([[customer_features.get(f, 0) for f in self.FEATURES]])
        proba = self.model.predict_proba(X)[0][1]
        return {
            "churn_probability_30d": float(proba),
            "risk_tier": self._risk_tier(proba),
            "top_factors": self._top_factors(X),
            "predicted_at": datetime.utcnow().isoformat(),
        }

    def _risk_tier(self, proba: float) -> str:
        if proba >= 0.7: return "critical"
        if proba >= 0.4: return "high"
        if proba >= 0.2: return "medium"
        return "low"

class LTVPredictionModel:
    """Predicts 12-month customer lifetime value."""

    FEATURES = [
        "tenure_days",
        "total_orders",
        "avg_order_value",
        "purchase_frequency_90d",
        "days_since_last_purchase",
        "email_engagement_score",
        "product_category_diversity",
        "discount_usage_rate",
        "support_interaction_count",
        "referral_count",
    ]

    def __init__(self, model_path: str):
        self.model: Pipeline = joblib.load(model_path)

    def predict(self, customer_features: dict) -> dict:
        X = np.array([[customer_features.get(f, 0) for f in self.FEATURES]])
        ltv = self.model.predict(X)[0]
        return {
            "predicted_ltv_12m": float(max(0, ltv)),
            "confidence_interval": self._confidence_interval(X),
            "predicted_at": datetime.utcnow().isoformat(),
        }
```

### Next Best Action Engine

```python
from typing import Literal

class NextBestActionEngine:
    """Determines the optimal next action for each customer."""

    ACTIONS = [
        "send_educational_content",
        "offer_free_trial",
        "offer_discount_10",
        "offer_discount_20",
        "schedule_demo",
        "send_case_study",
        "invite_to_webinar",
        "trigger_churn_save",
        "request_referral",
        "send_re_engagement",
        "no_action",
    ]

    def __init__(self, churn_model: ChurnPredictionModel,
                 ltv_model: LTVPredictionModel):
        self.churn_model = churn_model
        self.ltv_model = ltv_model

    def determine_next_action(self, customer_id: str,
                              journey_state: CustomerJourneyState,
                              context: dict) -> dict:
        features = self._extract_features(customer_id, context)
        churn_pred = self.churn_model.predict(features)
        ltv_pred = self.ltv_model.predict(features)

        # Decision logic combining churn risk, LTV, and journey stage
        action = self._select_action(
            journey_stage=journey_state.current_stage,
            churn_risk=churn_pred["risk_tier"],
            churn_probability=churn_pred["churn_probability_30d"],
            predicted_ltv=ltv_pred["predicted_ltv_12m"],
            context=context,
        )

        return {
            "customer_id": customer_id,
            "recommended_action": action,
            "rationale": self._build_rationale(action, churn_pred, ltv_pred),
            "expected_outcome": self._expected_outcome(action),
            "confidence": self._action_confidence(action, churn_pred),
            "churn_prediction": churn_pred,
            "ltv_prediction": ltv_pred,
        }

    def _select_action(self, journey_stage: JourneyStage, churn_risk: str,
                       churn_probability: float, predicted_ltv: float,
                       context: dict) -> str:
        # High churn risk + high LTV → aggressive save
        if churn_risk == "critical" and predicted_ltv > 1000:
            return "trigger_churn_save"
        # High churn risk → moderate save
        if churn_risk in ("critical", "high"):
            return "offer_discount_20"
        # Evaluation stage → demo offer
        if journey_stage == JourneyStage.EVALUATION:
            return "schedule_demo"
        # Consideration stage → case study
        if journey_stage == JourneyStage.CONSIDERATION:
            return "send_case_study"
        # Retention + high LTV → referral
        if journey_stage == JourneyStage.RETENTION and predicted_ltv > 500:
            return "request_referral"
        # Default: educational content
        return "send_educational_content"
```

### Agent Implementation

```python
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool

@tool
def predict_churn(customer_id: str) -> dict:
    """Get 30-day churn prediction for a customer."""
    ...

@tool
def predict_ltv(customer_id: str) -> dict:
    """Get 12-month LTV prediction for a customer."""
    ...

@tool
def get_next_best_action(customer_id: str) -> dict:
    """Determine the optimal next action for a customer."""
    ...

@tool
def get_journey_analytics(journey_id: str) -> dict:
    """Get aggregate analytics for a journey."""
    # Returns: conversion rates by stage, drop-off points,
    # avg time in stage, bottleneck identification
    ...

@tool
def identify_at_risk_journeys() -> list[dict]:
    """Identify journeys with high stall rates or drop-offs."""
    ...

@tool
def forecast_journey_outcomes(journey_id: str,
                              horizon_days: int = 30) -> dict:
    """Forecast journey completion rates and revenue impact."""
    ...

predictive_analytics_agent = DeepAgent(
    name="predictive_analytics",
    system_prompt="""You are a predictive analytics specialist. Your job is to:
1. Forecast customer churn probability and lifetime value
2. Determine the next best action for each customer
3. Identify at-risk journeys and bottlenecks
4. Forecast journey outcomes for planning

Always provide confidence intervals with your predictions.
Flag predictions with low confidence for review.""",
    tools=[
        predict_churn,
        predict_ltv,
        get_next_best_action,
        get_journey_analytics,
        identify_at_risk_journeys,
        forecast_journey_outcomes,
    ],
    model="claude-sonnet-4-20250514",
)
```

---

## 7. CRM and CDP Integration

### Purpose

The `CRMCDPIntegratorAgent` synchronizes data between the journey orchestration system and external CRM/CDP platforms (Salesforce, Segment, HubSpot). It ensures customer data consistency and enables bidirectional data flow.

### Integration Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  CRMCDPIntegratorAgent                        │
├────────────────┬─────────────────┬───────────────────────────┤
│  Salesforce    │  Segment CDP    │  HubSpot                  │
│  Connector     │  Connector      │  Connector                │
├────────────────┼─────────────────┼───────────────────────────┤
│ • Contacts     │ • User Profiles │ • Contacts                │
│ • Opportunities│ • Events        │ • Deals                   │
│ • Campaigns    │ • Segments      │ • Tickets                 │
│ • Leads        │ • Traits        │ • Engagements             │
│ • Accounts     │ • Identities    │ • Companies               │
└────────────────┴─────────────────┴───────────────────────────┘
         │                │                  │
         ▼                ▼                  ▼
┌──────────────────────────────────────────────────────────────┐
│              Unified Customer Data Layer                      │
│         (PostgreSQL + Redis Cache + Kafka Sync)              │
└──────────────────────────────────────────────────────────────┘
```

### Implementation

```python
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
from simple_salesforce import Salesforce
import requests

@tool
def sync_customer_to_crm(customer_id: str, crm_platform: str) -> dict:
    """Sync customer data to external CRM."""
    ...

@tool
def fetch_customer_from_cdp(customer_id: str) -> dict:
    """Fetch enriched customer profile from CDP."""
    ...

@tool
def push_journey_event(customer_id: str, event: dict) -> dict:
    """Push journey event to CDP for real-time segmentation."""
    ...

@tool
def update_crm_opportunity(customer_id: str, opportunity_data: dict) -> dict:
    """Update or create CRM opportunity based on journey state."""
    ...

@tool
def get_crm_activities(customer_id: str) -> list[dict]:
    """Fetch recent CRM activities (calls, emails, meetings)."""
    ...

@tool
def sync_segment_membership(customer_id: str) -> dict:
    """Sync customer segment memberships from CDP."""
    ...

crm_cdp_integrator_agent = DeepAgent(
    name="crm_cdp_integrator",
    system_prompt="""You are a CRM/CDP integration specialist. Your job is to:
1. Keep customer data synchronized across all platforms
2. Push journey events to CDP for real-time segmentation
3. Update CRM opportunities based on journey progress
4. Fetch enriched customer data from CDP
5. Handle data conflicts with last-write-wins + timestamp strategy

Always validate data before syncing. Log all sync operations.""",
    tools=[
        sync_customer_to_crm,
        fetch_customer_from_cdp,
        push_journey_event,
        update_crm_opportunity,
        get_crm_activities,
        sync_segment_membership,
    ],
    model="claude-sonnet-4-20250514",
)
```

### Salesforce Connector

```python
from simple_salesforce import Salesforce
from tenacity import retry, stop_after_attempt, wait_exponential

class SalesforceConnector:
    def __init__(self, username: str, password: str, security_token: str):
        self.sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def upsert_contact(self, customer_data: dict) -> str:
        """Create or update a Salesforce contact."""
        contact = {
            "Email": customer_data["email"],
            "FirstName": customer_data.get("first_name", ""),
            "LastName": customer_data.get("last_name", ""),
            "LeadSource": "Journey Orchestration",
            "Journey_Stage__c": customer_data.get("journey_stage", ""),
            "Churn_Risk__c": customer_data.get("churn_risk_tier", ""),
            "Predicted_LTV__c": customer_data.get("predicted_ltv", 0),
        }

        existing = self.sf.query(
            f"SELECT Id FROM Contact WHERE Email = '{customer_data['email']}'"
        )

        if existing["totalSize"] > 0:
            contact_id = existing["records"][0]["Id"]
            self.sf.Contact.update(contact_id, contact)
        else:
            result = self.sf.Contact.create(contact)
            contact_id = result["id"]

        return contact_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def create_opportunity(self, customer_id: str, opportunity_data: dict) -> str:
        """Create a Salesforce opportunity from journey data."""
        opportunity = {
            "Name": opportunity_data["name"],
            "StageName": opportunity_data["stage"],
            "Amount": opportunity_data["amount"],
            "CloseDate": opportunity_data["close_date"],
            "Probability": opportunity_data["probability"],
            "LeadSource": "Journey Orchestration",
        }
        result = self.sf.Opportunity.create(opportunity)
        return result["id"]
```

### Segment CDP Connector

```python
import requests
import base64

class SegmentConnector:
    def __init__(self, write_key: str):
        self.write_key = write_key
        self.base_url = "https://api.segment.io/v1"
        self.auth = (write_key, "")

    def track_event(self, customer_id: str, event_name: str,
                    properties: dict) -> dict:
        """Track a customer event in Segment."""
        payload = {
            "userId": customer_id,
            "event": event_name,
            "properties": properties,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        response = requests.post(
            f"{self.base_url}/track",
            json=payload,
            auth=self.auth,
        )
        response.raise_for_status()
        return response.json()

    def identify_user(self, customer_id: str, traits: dict) -> dict:
        """Update user profile in Segment."""
        payload = {
            "userId": customer_id,
            "traits": traits,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        response = requests.post(
            f"{self.base_url}/identify",
            json=payload,
            auth=self.auth,
        )
        response.raise_for_status()
        return response.json()

    def get_user_profile(self, customer_id: str) -> dict:
        """Fetch user profile from Segment."""
        response = requests.get(
            f"{self.base_url}/profile/{customer_id}",
            auth=self.auth,
        )
        response.raise_for_status()
        return response.json()
```

### Data Sync Strategy

```python
from datetime import datetime
from typing import Literal

class DataSyncManager:
    """Manages bidirectional data sync between systems."""

    SYNC_STRATEGY = {
        "customer_profile": {
            "source_of_truth": "CDP",
            "sync_direction": "CDP → CRM",
            "conflict_resolution": "last_write_wins",
            "sync_frequency": "realtime",
        },
        "journey_state": {
            "source_of_truth": "Journey DB",
            "sync_direction": "Journey DB → CRM + CDP",
            "conflict_resolution": "journey_db_wins",
            "sync_frequency": "realtime",
        },
        "opportunity": {
            "source_of_truth": "CRM",
            "sync_direction": "CRM → Journey DB",
            "conflict_resolution": "crm_wins",
            "sync_frequency": "near_realtime",
        },
        "engagement_events": {
            "source_of_truth": "Event Store",
            "sync_direction": "Event Store → CDP",
            "conflict_resolution": "append_only",
            "sync_frequency": "realtime",
        },
    }

    async def sync_customer(self, customer_id: str,
                            direction: Literal["push", "pull", "bidirectional"]):
        """Sync customer data across all integrated systems."""
        if direction in ("pull", "bidirectional"):
            cdp_profile = await self._fetch_from_cdp(customer_id)
            await self._push_to_crm(customer_id, cdp_profile)

        if direction in ("push", "bidirectional"):
            journey_state = await self._fetch_journey_state(customer_id)
            await self._push_to_cdp(customer_id, journey_state)
            await self._push_to_crm(customer_id, journey_state)
```

---

## 8. Code Examples and Snippets

### Complete Orchestrator Setup

```python
# src/orchestrator/journey_orchestrator.py

from langchain_deepagents import DeepAgent
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Optional
import operator
import redis.asyncio as redis
import json

# ── State Definition ──

class OrchestratorState(TypedDict):
    customer_id: str
    journey_id: Optional[str]
    current_event: dict
    journey_state: Optional[dict]
    personalization: Optional[dict]
    channel_decision: Optional[dict]
    predictive_insights: Optional[dict]
    crm_sync_status: Optional[dict]
    messages: Annotated[list, operator.add]
    final_action: Optional[dict]

# ── Orchestrator Agent ──

journey_orchestrator = DeepAgent(
    name="journey_orchestrator",
    system_prompt="""You are the central journey orchestrator. Your job is to:
1. Receive customer events and determine the appropriate journey context
2. Delegate to specialized sub-agents for each domain
3. Synthesize sub-agent outputs into a cohesive action plan
4. Execute the plan and track results
5. Learn from outcomes to improve future decisions

Decision framework:
- If new customer → trigger onboarding journey
- If existing customer → evaluate current journey state
- If high churn risk → prioritize retention
- If high LTV potential → prioritize growth
- Always respect frequency caps and channel preferences""",
    tools=[
        # Sub-agent invocation tools
        invoke_journey_mapper,
        invoke_personalization_engine,
        invoke_channel_orchestrator,
        invoke_predictive_analytics,
        invoke_crm_integrator,
        # Direct tools
        get_active_journeys,
        create_journey_instance,
        update_journey_state,
        log_decision,
    ],
    model="claude-sonnet-4-20250514",
    sub_agents=[journey_mapping_agent, personalization_agent,
                channel_orchestration_agent, predictive_analytics_agent,
                crm_cdp_integrator_agent],
)

# ── LangGraph Workflow ──

def should_predict(state: OrchestratorState) -> str:
    if state.get("predictive_insights") is None:
        return "predict"
    return "personalize"

def should_remap(state: OrchestratorState) -> str:
    if state.get("journey_state") is None:
        return "remap"
    return "predict"

orchestrator_graph = StateGraph(OrchestratorState)
orchestrator_graph.add_node("remap_journey", remap_journey_node)
orchestrator_graph.add_node("predict", predict_node)
orchestrator_graph.add_node("personalize", personalize_node)
orchestrator_graph.add_node("orchestrate_channel", orchestrate_channel_node)
orchestrator_graph.add_node("sync_crm", sync_crm_node)
orchestrator_graph.add_node("execute_action", execute_action_node)

orchestrator_graph.set_entry_point("remap_journey")
orchestrator_graph.add_conditional_edges("remap_journey", should_remap)
orchestrator_graph.add_edge("remap_journey", "predict")
orchestrator_graph.add_conditional_edges("predict", should_predict)
orchestrator_graph.add_edge("predict", "personalize")
orchestrator_graph.add_edge("personalize", "orchestrate_channel")
orchestrator_graph.add_edge("orchestrate_channel", "sync_crm")
orchestrator_graph.add_edge("sync_crm", "execute_action")
orchestrator_graph.add_edge("execute_action", END)

orchestrator_workflow = orchestrator_graph.compile(
    checkpointer=RedisSaver(redis_client),
)
```

### FastAPI Endpoint

```python
# src/api/journey_api.py

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(title="Journey Orchestration API")

class CustomerEvent(BaseModel):
    customer_id: str
    event_type: str
    event_data: dict
    timestamp: Optional[str] = None

class JourneyActionResponse(BaseModel):
    correlation_id: str
    customer_id: str
    journey_id: str
    action_taken: str
    channel: str
    content: dict
    predicted_outcome: dict
    confidence: float

@app.post("/api/v1/events", response_model=JourneyActionResponse)
async def process_customer_event(
    event: CustomerEvent,
    background_tasks: BackgroundTasks,
):
    """Process a customer event and trigger journey orchestration."""
    correlation_id = str(uuid.uuid4())

    result = await orchestrator_workflow.ainvoke(
        {
            "customer_id": event.customer_id,
            "current_event": {
                "type": event.event_type,
                "data": event.event_data,
                "timestamp": event.timestamp or datetime.utcnow().isoformat(),
            },
            "messages": [],
        },
        config={"configurable": {"thread_id": correlation_id}},
    )

    # Async CRM sync
    background_tasks.add_task(
        sync_crm_async,
        customer_id=event.customer_id,
        journey_state=result.get("final_action"),
    )

    return JourneyActionResponse(
        correlation_id=correlation_id,
        customer_id=event.customer_id,
        journey_id=result["journey_id"],
        action_taken=result["final_action"]["action_type"],
        channel=result["final_action"]["channel"],
        content=result["final_action"]["content"],
        predicted_outcome=result.get("predictive_insights", {}),
        confidence=result["final_action"].get("confidence", 0.0),
    )

@app.get("/api/v1/journeys/{customer_id}")
async def get_customer_journey(customer_id: str):
    """Get current journey state for a customer."""
    state = await redis_client.get(f"journey:{customer_id}:current")
    if not state:
        raise HTTPException(status_code=404, detail="No active journey found")
    return json.loads(state)

@app.get("/api/v1/analytics/journey/{journey_id}")
async def get_journey_analytics(journey_id: str):
    """Get aggregate analytics for a journey."""
    return await predictive_analytics_agent.invoke({
        "messages": [{"role": "user", "content": f"Get analytics for journey {journey_id}"}]
    })
```

### Docker Compose Setup

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
      - KAFKA_BROKERS=kafka:9092
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/journeys
      - SALESFORCE_USERNAME=${SF_USERNAME}
      - SALESFORCE_PASSWORD=${SF_PASSWORD}
      - SALESFORCE_SECURITY_TOKEN=${SF_TOKEN}
      - SEGMENT_WRITE_KEY=${SEGMENT_KEY}
    depends_on:
      - redis
      - kafka
      - db

  worker:
    build: .
    command: python -m src.workers.journey_worker
    environment:
      - REDIS_URL=redis://redis:6379
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - redis
      - kafka

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

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: journeys
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 9. Testing Strategy

### Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5%)  - Full journey simulation
                   �┌┴─────────┴┐
                   │ Integration│  (15%) - Agent + tool + DB tests
                  ┌┴────────────┴┐
                  │    Unit       │  (80%) - Individual functions, models
                  └───────────────┘
```

### Unit Tests

```python
# tests/unit/test_journey_mapping.py

import pytest
from datetime import datetime, timedelta
from src.agents.journey_mapping import (
    detect_stage_transition,
    STAGE_TRANSITION_RULES,
    JourneyStage,
)

class TestJourneyStageDetection:
    """Unit tests for journey stage detection logic."""

    def test_awareness_to_consideration_transition(self):
        """Test transition from awareness to consideration on pricing page view."""
        events = [
            {"event_type": "product_page_view", "timestamp": datetime.utcnow() - timedelta(hours=2)},
            {"event_type": "pricing_page_view", "timestamp": datetime.utcnow() - timedelta(hours=1)},
        ]
        result = detect_stage_transition(
            customer_id="cust_123",
            current_stage=JourneyStage.AWARENESS,
            events=events,
        )
        assert result["new_stage"] == JourneyStage.CONSIDERATION
        assert result["confidence"] > 0.7

    def test_no_transition_on_single_event(self):
        """Test that single events don't trigger transitions."""
        events = [
            {"event_type": "pricing_page_view", "timestamp": datetime.utcnow()},
        ]
        result = detect_stage_transition(
            customer_id="cust_123",
            current_stage=JourneyStage.AWARENESS,
            events=events,
        )
        assert result["new_stage"] == JourneyStage.AWARENESS

    def test_churn_risk_detection(self):
        """Test churn risk stage detection."""
        events = [
            {"event_type": "login_decline_30d", "timestamp": datetime.utcnow() - timedelta(days=1)},
            {"event_type": "usage_drop_50pct", "timestamp": datetime.utcnow()},
        ]
        result = detect_stage_transition(
            customer_id="cust_123",
            current_stage=JourneyStage.RETENTION,
            events=events,
        )
        assert result["new_stage"] == JourneyStage.CHURN_RISK

    def test_stalled_journey_detection(self):
        """Test detection of stalled journeys."""
        last_activity = datetime.utcnow() - timedelta(days=30)
        result = detect_stalled_journey(
            customer_id="cust_123",
            current_stage=JourneyStage.EVALUATION,
            last_activity=last_activity,
            stall_threshold_days=14,
        )
        assert result["is_stalled"] is True
        assert result["stall_days"] == 30
```

```python
# tests/unit/test_personalization.py

import pytest
import numpy as np
from src.agents.personalization import ContextualBanditOfferSelector

class TestContextualBandit:
    """Unit tests for the contextual bandit offer selector."""

    def test_selects_best_offer(self):
        """Test that bandit selects the offer with highest expected reward."""
        selector = ContextualBanditOfferSelector(n_features=4, alpha=0.1)

        # Pre-train with known rewards
        context = np.array([1.0, 0.5, 0.3, 0.2])
        for _ in range(50):
            selector.update("offer_A", context, reward=0.9)
            selector.update("offer_B", context, reward=0.3)

        selected, confidence = selector.select_offer(
            context=context,
            available_offers=[
                Offer(offer_id="offer_A", offer_type="discount", value=10, cost=2, constraints={}),
                Offer(offer_id="offer_B", offer_type="free_shipping", value=5, cost=1, constraints={}),
            ],
        )
        assert selected == "offer_A"
        assert confidence > 0.5

    def test_exploration_with_new_offer(self):
        """Test that new offers get explored."""
        selector = ContextualBanditOfferSelector(n_features=4, alpha=1.0)
        context = np.array([1.0, 0.5, 0.3, 0.2])

        # Train only on offer_A
        for _ in range(20):
            selector.update("offer_A", context, reward=0.5)

        # offer_B is new — should sometimes be selected due to exploration
        selections = set()
        for _ in range(100):
            selected, _ = selector.select_offer(
                context=context,
                available_offers=[
                    Offer(offer_id="offer_A", offer_type="discount", value=10, cost=2, constraints={}),
                    Offer(offer_id="offer_B", offer_type="free_shipping", value=5, cost=1, constraints={}),
                ],
            )
            selections.add(selected)

        assert "offer_B" in selections  # Explored at least once
```

```python
# tests/unit/test_channel_orchestration.py

import pytest
from src.agents.channel_orchestration import (
    ChannelDispatcher,
    Channel,
    JourneySequence,
    JourneySequenceStep,
)

class TestChannelDispatch:
    """Unit tests for channel dispatch logic."""

    @pytest.mark.asyncio
    async def test_dispatch_with_fallback(self):
        """Test that fallback channel is used when primary fails."""
        dispatcher = ChannelDispatcher()

        # Mock primary channel to fail
        dispatcher.providers[Channel.EMAIL] = FailingProvider()
        dispatcher.providers[Channel.SMS] = SuccessProvider()

        result = await dispatcher.dispatch_with_fallback(
            customer_id="cust_123",
            primary_channel=Channel.EMAIL,
            content={"subject": "Test", "body": "Test body"},
            fallback_channel=Channel.SMS,
        )

        assert result["success"] is True
        assert result["used_fallback"] is True
        assert result["original_channel"] == Channel.EMAIL

    def test_frequency_cap_enforcement(self):
        """Test that frequency caps are enforced."""
        assert check_frequency_cap("cust_123", Channel.SMS, window_hours=24) == {
            "allowed": False,
            "current_count": 5,
            "cap": 3,
            "reset_at": "2024-01-01T00:00:00Z",
        }
```

### Integration Tests

```python
# tests/integration/test_orchestrator.py

import pytest
import pytest_asyncio
from testcontainers.redis import RedisContainer
from testcontainers.postgres import PostgresContainer
from src.orchestrator.journey_orchestrator import orchestrator_workflow

@pytest_asyncio.fixture
async def redis_client():
    """Spin up Redis test container."""
    with RedisContainer("redis:7") as redis:
        client = redis.get_client()
        yield client
        client.close()

@pytest_asyncio.fixture
async def db_connection():
    """Spin up PostgreSQL test container."""
    with PostgresContainer("postgres:15") as postgres:
        conn = postgres.get_connection()
        yield conn
        conn.close()

@pytest.mark.asyncio
async def test_full_journey_lifecycle(redis_client, db_connection):
    """Test complete journey from awareness to purchase."""
    # 1. Customer lands on website
    result = await orchestrator_workflow.ainvoke({
        "customer_id": "cust_test_001",
        "current_event": {
            "type": "page_view",
            "data": {"page": "homepage", "referrer": "google_ads"},
        },
        "messages": [],
    })
    assert result["journey_state"]["current_stage"] == "awareness"

    # 2. Customer views pricing page
    result = await orchestrator_workflow.ainvoke({
        "customer_id": "cust_test_001",
        "current_event": {
            "type": "pricing_page_view",
            "data": {"page": "pricing", "plan_viewed": "pro"},
        },
        "messages": [],
    })
    assert result["journey_state"]["current_stage"] == "consideration"

    # 3. Customer starts free trial
    result = await orchestrator_workflow.ainvoke({
        "customer_id": "cust_test_001",
        "current_event": {
            "type": "free_trial_signup",
            "data": {"plan": "pro", "trial_days": 14},
        },
        "messages": [],
    })
    assert result["journey_state"]["current_stage"] == "evaluation"

    # 4. Customer purchases
    result = await orchestrator_workflow.ainvoke({
        "customer_id": "cust_test_001",
        "current_event": {
            "type": "payment_success",
            "data": {"amount": 99.0, "plan": "pro_monthly"},
        },
        "messages": [],
    })
    assert result["journey_state"]["current_stage"] == "onboarding"
    assert result["final_action"]["action_type"] == "send_onboarding_email"

@pytest.mark.asyncio
async def test_churn_save_flow(redis_client, db_connection):
    """Test churn risk detection and save flow."""
    # Setup: customer in retention stage
    await redis_client.set(
        "journey:cust_churn_001:current",
        json.dumps({
            "customer_id": "cust_churn_001",
            "journey_id": "journey_123",
            "current_stage": "retention",
            "stage_entered_at": (datetime.utcnow() - timedelta(days=60)).isoformat(),
        }),
    )

    # Trigger: cancellation page view
    result = await orchestrator_workflow.ainvoke({
        "customer_id": "cust_churn_001",
        "current_event": {
            "type": "cancellation_page_view",
            "data": {"page": "cancel_subscription"},
        },
        "messages": [],
    })

    assert result["journey_state"]["current_stage"] == "churn_risk"
    assert result["final_action"]["action_type"] == "trigger_churn_save"
    assert result["predictive_insights"]["churn_probability_30d"] > 0.5
```

### E2E Tests

```python
# tests/e2e/test_journey_simulation.py

import pytest
import asyncio
from src.simulation.journey_simulator import JourneySimulator

@pytest.mark.asyncio
async def test_abandoned_cart_journey_e2e():
    """End-to-end test of abandoned cart recovery journey."""
    simulator = JourneySimulator()

    # Simulate customer adding items to cart
    await simulator.send_event(
        customer_id="cust_e2e_001",
        event_type="cart_add",
        data={"items": [{"sku": "PROD-001", "qty": 2, "price": 49.99}]},
    )

    # Simulate cart abandonment (no purchase within 1 hour)
    await simulator.advance_time(hours=1)

    # Verify first reminder email was sent
    actions = await simulator.get_actions(customer_id="cust_e2e_001")
    assert len(actions) >= 1
    assert actions[0]["channel"] == "email"
    assert actions[0]["template"] == "cart_reminder_1h"

    # Simulate customer returning and purchasing
    await simulator.send_event(
        customer_id="cust_e2e_001",
        event_type="payment_success",
        data={"amount": 99.98, "items": ["PROD-001"]},
    )

    # Verify cart abandonment sequence is suppressed
    actions_after = await simulator.get_actions(customer_id="cust_e2e_001")
    cart_reminders = [a for a in actions_after if a["template"].startswith("cart_reminder")]
    assert len(cart_reminders) == 1  # Only the first one was sent

    # Verify onboarding sequence starts
    assert any(a["template"] == "onboarding_welcome" for a in actions_after)
```

### Test Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    unit: Unit tests (fast, no external deps)
    integration: Integration tests (requires testcontainers)
    e2e: End-to-end tests (full simulation)
    slow: Tests that take > 5 seconds
addopts = -v --tb=short --strict-markers
```

```python
# conftest.py

import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")

@pytest.fixture(scope="session")
def llm_mock():
    """Mock LLM for tests that don't need real inference."""
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(
        content='{"action": "no_action", "confidence": 0.9}'
    )
    return mock
```

### Running Tests

```bash
# Unit tests only (fast feedback)
pytest -m unit -v

# Integration tests (requires Docker for testcontainers)
pytest -m integration -v

# E2E tests (full simulation)
pytest -m e2e -v

# All tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Specific test file
pytest tests/unit/test_journey_mapping.py -v

# With debugging
pytest tests/integration/test_orchestrator.py::test_full_journey_lifecycle -v --pdb
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- Set up project structure, Docker environment, CI/CD
- Implement core data models and Redis state store
- Build event ingestion pipeline (Kafka consumer)
- Create basic JourneyMappingAgent with stage detection

### Phase 2: Core Agents (Weeks 3-4)
- Implement PersonalizationEngineAgent with contextual bandit
- Build ChannelOrchestrationAgent with multi-channel dispatch
- Create PredictiveAnalyticsAgent with churn/LTV models
- Integrate all agents into JourneyOrchestratorAgent

### Phase 3: Integration (Weeks 5-6)
- Build CRM/CDP connectors (Salesforce, Segment)
- Implement bidirectional data sync
- Add real-time adaptation engine
- Create FastAPI endpoints

### Phase 4: Testing & Hardening (Weeks 7-8)
- Achieve 80%+ test coverage
- Load testing (1000+ events/second)
- Implement observability (LangSmith tracing, structured logging)
- Add human-in-the-loop approval flows

### Phase 5: Optimization (Weeks 9-10)
- A/B testing framework for journey variants
- Model retraining pipeline
- Performance optimization
- Documentation and runbooks

---

## Key Files to Create

```
src/
├── agents/
│   ├── __init__.py
│   ├── journey_mapping.py          # JourneyMappingAgent
│   ├── personalization.py          # PersonalizationEngineAgent
│   ├── channel_orchestration.py    # ChannelOrchestrationAgent
│   ├── predictive_analytics.py     # PredictiveAnalyticsAgent
│   └── crm_cdp_integration.py      # CRMCDPIntegratorAgent
├── orchestrator/
│   ├── __init__.py
│   └── journey_orchestrator.py     # Central orchestrator + LangGraph workflow
├── api/
│   ├── __init__.py
│   └── journey_api.py              # FastAPI endpoints
├── models/
│   ├── __init__.py
│   ├── journey.py                  # Journey data models
│   ├── customer.py                 # Customer profile models
│   └── events.py                   # Event schema models
├── integrations/
│   ├── __init__.py
│   ├── salesforce.py               # Salesforce connector
│   ├── segment.py                  # Segment CDP connector
│   └── hubspot.py                  # HubSpot connector
├── workers/
│   ├── __init__.py
│   └── journey_worker.py           # Kafka event consumer
├── simulation/
│   ├── __init__.py
│   └── journey_simulator.py        # E2E test simulator
└── config/
    ├── __init__.py
    └── settings.py                 # App configuration

tests/
├── unit/
│   ├── test_journey_mapping.py
│   ├── test_personalization.py
│   ├── test_channel_orchestration.py
│   └── test_predictive_analytics.py
├── integration/
│   ├── test_orchestrator.py
│   ├── test_crm_integration.py
│   └── test_cdp_integration.py
└── e2e/
    └── test_journey_simulation.py
```
