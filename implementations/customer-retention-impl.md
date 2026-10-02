# AI-Powered Customer Retention Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Stack:** LangChain DeepAgents, Python 3.11+, PostgreSQL, Redis, FastAPI

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Prediction Agent Implementation](#2-prediction-agent-implementation)
3. [Intervention Agent Implementation](#3-intervention-agent-implementation)
4. [Optimization Agent Implementation](#4-optimization-agent-implementation)
5. [Performance Analytics Agent Implementation](#5-performance-analytics-agent-implementation)
6. [Code Examples and Snippets](#6-code-examples-and-snippets)
7. [Testing Strategy](#7-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The AI-powered customer retention system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. Four specialized agents collaborate to predict churn, design interventions, optimize strategies, and measure performance in a continuous feedback loop.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                            │
│              (LangChain DeepAgents Coordinator)                  │
└──────────┬──────────────┬──────────────┬───────────────┬────────┘
           │              │              │               │
    ┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐ ┌──────▼───────┐
    │  Prediction │ │Interven- │ │Optimization│ │  Analytics   │
    │    Agent    │ │tion Agent│ │   Agent    │ │    Agent     │
    └──────┬──────┘ └────┬─────┘ └─────┬──────┘ └──────┬───────┘
           │              │              │               │
    ┌──────▼──────────────▼──────────────▼───────────────▼───────┐
    │              Shared State & Message Bus                     │
    │         (Redis + PostgreSQL + Event Store)                  │
    └─────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents | Multi-agent orchestration, tool calling, planning |
| LLM Backend | GPT-4o / Claude 3.5 Sonnet | Reasoning, content generation, classification |
| Vector Store | pgvector (PostgreSQL) | Customer embeddings, similarity search |
| Cache / Bus | Redis | Inter-agent messaging, session state, rate limiting |
| Database | PostgreSQL 16 | Customer profiles, events, predictions, interventions |
| API Layer | FastAPI | REST endpoints for external integrations |
| Task Queue | Celery + Redis | Async intervention delivery, batch scoring |
| Monitoring | LangSmith + Custom Metrics | Tracing, evaluation, observability |
| Feature Store | Feast (optional) | Real-time feature computation |

### 1.3 Agent Communication Protocol

Agents communicate via a **typed message bus** using Pydantic schemas:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    PREDICTION = "prediction"
    INTERVENTION = "intervention"
    OPTIMIZATION = "optimization"
    ANALYTICS = "analytics"

class MessagePriority(str, Enum):
    CRITICAL = "critical"      # Immediate action required
    HIGH = "high"              # Process within 1 minute
    NORMAL = "normal"          # Process within 5 minutes
    LOW = "low"                # Process when capacity available

class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: AgentRole
    recipient: AgentRole
    message_type: str  # e.g., "churn_prediction", "intervention_recommendation"
    priority: MessagePriority = MessagePriority.NORMAL
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str  # Groups related messages across agents
    ttl_seconds: int = 3600  # Message expiry

class AgentResponse(BaseModel):
    message_id: str
    correlation_id: str
    sender: AgentRole
    status: str  # "success", "partial", "failed", "deferred"
    payload: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_trace: Optional[str] = None
    suggested_actions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### 1.4 Shared State Management

```python
from typing import Dict, Any, Optional
import json
import redis.asyncio as redis

class SharedStateManager:
    """Manages shared state across all agents using Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.state_prefix = "retention:state:"
        self.lock_prefix = "retention:lock:"

    async def get_customer_state(self, customer_id: str) -> Dict[str, Any]:
        key = f"{self.state_prefix}customer:{customer_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else {}

    async def update_customer_state(
        self, customer_id: str, updates: Dict[str, Any], ttl: int = 86400
    ):
        key = f"{self.state_prefix}customer:{customer_id}"
        current = await self.get_customer_state(customer_id)
        current.update(updates)
        current["last_updated"] = datetime.utcnow().isoformat()
        await self.redis.setex(key, ttl, json.dumps(current))

    async def publish_message(self, channel: str, message: AgentMessage):
        await self.redis.publish(
            f"retention:channel:{channel}",
            message.model_dump_json(),
        )

    async def acquire_lock(self, lock_name: str, ttl: int = 30) -> bool:
        key = f"{self.lock_prefix}{lock_name}"
        acquired = await self.redis.set(key, "1", nx=True, ex=ttl)
        return bool(acquired)
```

### 1.5 Orchestrator Agent

The Orchestrator is the top-level coordinator that routes tasks, manages the agent lifecycle, and ensures system-wide consistency.

```python
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_deepagents import DeepAgent

ORCHESTRATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Orchestrator Agent for the Customer Retention System.

Your responsibilities:
1. Ingest customer signals and route to the appropriate specialized agent
2. Coordinate multi-agent workflows (e.g., predict → intervene → measure)
3. Resolve conflicts between agent recommendations
4. Maintain system-wide policies and guardrails
5. Escalate edge cases to human operators

Available agents:
- @prediction: Churn prediction, customer scoring, risk segmentation
- @intervention: Campaign design, message personalization, channel selection
- @optimization: A/B testing, strategy tuning, budget allocation
- @analytics: Performance measurement, reporting, insight generation

Always include a correlation_id when initiating multi-agent workflows.
Never make retention decisions without prediction agent input.
Log all decisions with full reasoning traces."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

class OrchestratorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.agent = DeepAgent(
            name="orchestrator",
            llm=self.llm,
            prompt=ORCHESTRATOR_PROMPT,
            tools=[
                RouteToPredictionTool(),
                RouteToInterventionTool(),
                RouteToOptimizationTool(),
                RouteToAnalyticsTool(),
                EscalateToHumanTool(),
            ],
        )
        self.state_manager = SharedStateManager()

    async def process_customer_signal(
        self, customer_id: str, signal: Dict[str, Any]
    ) -> AgentResponse:
        """Process an incoming customer signal and route appropriately."""
        correlation_id = str(uuid.uuid4())

        # Enrich signal with customer context
        customer_state = await self.state_manager.get_customer_state(customer_id)
        enriched_signal = {**signal, "customer_context": customer_state}

        # Determine routing
        signal_type = signal.get("type", "unknown")
        if signal_type in ("churn_risk_alert", "engagement_drop", "payment_failure"):
            return await self._initiate_retention_workflow(
                customer_id, enriched_signal, correlation_id
            )
        elif signal_type == "campaign_performance":
            return await self._route_to_analytics(enriched_signal, correlation_id)
        else:
            return await self._route_to_prediction(enriched_signal, correlation_id)

    async def _initiate_retention_workflow(
        self, customer_id: str, signal: Dict, correlation_id: str
    ) -> AgentResponse:
        """Full retention workflow: predict → intervene → schedule measurement."""
        # Step 1: Get churn prediction
        prediction = await self._call_agent(
            AgentRole.PREDICTION,
            "predict_churn",
            {"customer_id": customer_id, "signal": signal},
            correlation_id,
        )

        if prediction.confidence < 0.6:
            return AgentResponse(
                message_id=str(uuid.uuid4()),
                correlation_id=correlation_id,
                sender=AgentRole.ORCHESTRATOR,
                status="deferred",
                payload={"reason": "Low prediction confidence", "prediction": prediction.payload},
                suggested_actions=["Collect more data", "Schedule re-evaluation"],
            )

        # Step 2: Design intervention
        intervention = await self._call_agent(
            AgentRole.INTERVENTION,
            "design_intervention",
            {
                "customer_id": customer_id,
                "prediction": prediction.payload,
                "signal": signal,
            },
            correlation_id,
        )

        # Step 3: Schedule performance measurement
        await self._call_agent(
            AgentRole.ANALYTICS,
            "schedule_measurement",
            {
                "customer_id": customer_id,
                "intervention_id": intervention.payload.get("intervention_id"),
                "correlation_id": correlation_id,
            },
            correlation_id,
        )

        return AgentResponse(
            message_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            sender=AgentRole.ORCHESTRATOR,
            status="success",
            payload={
                "workflow": "retention",
                "prediction": prediction.payload,
                "intervention": intervention.payload,
            },
            confidence=min(prediction.confidence, intervention.confidence),
        )
```

---

## 2. Prediction Agent Implementation

### 2.1 Purpose

The Prediction Agent is responsible for:
- **Churn probability scoring** (binary classification)
- **Customer lifetime value (CLV) estimation** (regression)
- **Risk segmentation** (clustering-based tiering)
- **Next-best-action recommendation** (reinforcement learning)
- **Anomaly detection** on customer behavior patterns

### 2.2 Architecture

```python
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta

PREDICTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Prediction Agent for the Customer Retention System.

Your capabilities:
1. Churn Prediction: Estimate probability of customer churn within configurable windows
2. CLV Estimation: Predict customer lifetime value using historical + behavioral data
3. Risk Segmentation: Classify customers into risk tiers (low/medium/high/critical)
4. Behavioral Anomaly Detection: Identify unusual patterns that precede churn
5. Feature Importance: Explain which factors drive each prediction

Guidelines:
- Always provide confidence intervals, not just point estimates
- Flag data quality issues that may affect prediction accuracy
- Consider seasonality and recent trend changes
- Use the customer's full interaction history, not just recent events
- When confidence is low, recommend data collection actions

Output format: Structured prediction with probability, confidence, top features, and recommended monitoring actions."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

class ChurnPrediction(BaseModel):
    customer_id: str
    churn_probability: float = Field(ge=0.0, le=1.0)
    confidence_interval: Tuple[float, float]
    prediction_window_days: int
    risk_tier: str  # "low", "medium", "high", "critical"
    top_features: List[Dict[str, Any]]  # [{"feature": "recency_days", "importance": 0.35, "direction": "increases_risk"}]
    clv_estimate: Optional[float] = None
    clv_confidence_interval: Optional[Tuple[float, float]] = None
    anomaly_flags: List[str] = Field(default_factory=list)
    recommended_monitoring: List[str] = Field(default_factory=list)
    model_version: str
    prediction_timestamp: datetime = Field(default_factory=datetime.utcnow)

class PredictionAgent:
    def __init__(self, model_registry, feature_store, db_session):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
        self.agent = DeepAgent(
            name="prediction",
            llm=self.llm,
            prompt=PREDICTION_PROMPT,
            tools=[
                ComputeChurnFeaturesTool(feature_store),
                ScoreChurnModelTool(model_registry),
                EstimateCLVTool(model_registry),
                DetectAnomaliesTool(feature_store),
                GetCustomerHistoryTool(db_store),
                ExplainPredictionTool(),
            ],
        )
        self.model_registry = model_registry
        self.feature_store = feature_store
        self.db = db_session

    async def predict_churn(
        self,
        customer_id: str,
        window_days: int = 30,
        include_explanation: bool = True,
    ) -> ChurnPrediction:
        """Generate a churn prediction for a customer."""
        # Step 1: Compute features
        features = await self._compute_features(customer_id)

        # Step 2: Score with ensemble model
        raw_prediction = await self._score_model(features, window_days)

        # Step 3: Detect anomalies
        anomalies = await self._detect_anomalies(customer_id, features)

        # Step 4: Estimate CLV
        clv = await self._estimate_clv(customer_id, features)

        # Step 5: Build explanation
        explanation = await self._explain_prediction(features, raw_prediction) if include_explanation else None

        # Step 6: Determine risk tier
        risk_tier = self._classify_risk_tier(raw_prediction["probability"], anomalies)

        prediction = ChurnPrediction(
            customer_id=customer_id,
            churn_probability=raw_prediction["probability"],
            confidence_interval=raw_prediction["confidence_interval"],
            prediction_window_days=window_days,
            risk_tier=risk_tier,
            top_features=explanation["top_features"] if explanation else [],
            clv_estimate=clv["estimate"],
            clv_confidence_interval=clv.get("confidence_interval"),
            anomaly_flags=anomalies,
            recommended_monitoring=self._recommend_monitoring(risk_tier, anomalies),
            model_version=raw_prediction["model_version"],
        )

        # Persist prediction
        await self._persist_prediction(prediction)

        return prediction

    async def batch_predict(
        self, customer_ids: List[str], window_days: int = 30
    ) -> List[ChurnPrediction]:
        """Batch prediction for efficiency."""
        # Use Celery for parallel processing
        from celery import group
        job = group(
            predict_single_customer.s(cid, window_days) for cid in customer_ids
        )
        result = job.apply_async()
        return result.get(timeout=300)

    async def _compute_features(self, customer_id: str) -> Dict[str, Any]:
        """Compute real-time and batch features."""
        # Real-time features from feature store
        rt_features = await self.feature_store.get_online_features(
            entity_rows=[{"customer_id": customer_id}],
            feature_refs=[
                "customer:recency_days",
                "customer:frequency_30d",
                "customer:monetary_90d",
                "customer:engagement_score_7d",
                "customer:support_tickets_30d",
                "customer:nps_score_latest",
                "customer:tenure_days",
                "customer:payment_failures_90d",
                "customer:feature_usage_breadth",
                "customer:days_since_last_login",
                "customer:contract_value",
                "customer:discount_dependency",
            ],
        )

        # Computed features
        computed = {
            "rfm_score": self._compute_rfm_score(rt_features),
            "engagement_trend": self._compute_engagement_trend(customer_id),
            "churn_risk_signals": self._count_risk_signals(rt_features),
            "lifecycle_stage": self._classify_lifecycle_stage(rt_features),
        }

        return {**rt_features, **computed}

    def _classify_risk_tier(
        self, probability: float, anomalies: List[str]
    ) -> str:
        """Classify customer into risk tier."""
        if probability >= 0.8 or len(anomalies) >= 3:
            return "critical"
        elif probability >= 0.6 or len(anomalies) >= 2:
            return "high"
        elif probability >= 0.35 or len(anomalies) >= 1:
            return "medium"
        return "low"

    def _recommend_monitoring(
        self, risk_tier: str, anomalies: List[str]
    ) -> List[str]:
        """Recommend monitoring actions based on risk."""
        recommendations = []
        if risk_tier == "critical":
            recommendations.extend([
                "Daily engagement monitoring",
                "Real-time alert on any negative signal",
                "Assign dedicated retention specialist",
                "Prepare executive escalation path",
            ])
        elif risk_tier == "high":
            recommendations.extend([
                "Weekly engagement monitoring",
                "Alert on engagement drop > 20%",
                "Trigger proactive outreach within 48h",
            ])
        elif risk_tier == "medium":
            recommendations.extend([
                "Bi-weekly monitoring",
                "Include in next campaign wave",
            ])
        else:
            recommendations.append("Monthly health check")

        if "payment_failure" in anomalies:
            recommendations.append("Monitor payment retry success")
        if "engagement_drop" in anomalies:
            recommendations.append("Track re-engagement after intervention")

        return recommendations
```

### 2.3 Feature Engineering Pipeline

```python
from feast import Entity, Feature, FeatureView, ValueType
from feast.types import Float32, Int64, String, Bool
from datetime import timedelta

# Feast feature store definitions
customer = Entity(
    name="customer_id",
    value_type=ValueType.STRING,
    description="Customer identifier",
)

customer_stats_fv = FeatureView(
    name="customer_stats",
    entities=["customer_id"],
    ttl=timedelta(hours=1),
    features=[
        Feature(name="recency_days", dtype=Int64),
        Feature(name="frequency_30d", dtype=Int64),
        Feature(name="monetary_90d", dtype=Float32),
        Feature(name="engagement_score_7d", dtype=Float32),
        Feature(name="support_tickets_30d", dtype=Int64),
        Feature(name="nps_score_latest", dtype=Int64),
        Feature(name="tenure_days", dtype=Int64),
        Feature(name="payment_failures_90d", dtype=Int64),
        Feature(name="feature_usage_breadth", dtype=Float32),
        Feature(name="days_since_last_login", dtype=Int64),
        Feature(name="contract_value", dtype=Float32),
        Feature(name="discount_dependency", dtype=Float32),
        Feature(name="email_open_rate_30d", dtype=Float32),
        Feature(name="session_count_7d", dtype=Int64),
        Feature(name="avg_session_duration_7d", dtype=Float32),
        Feature(name="churn_label_90d", dtype=Bool),  # Training label
    ],
    online=True,
    source=PostgresSource(
        table_ref="customer_feature_stats",
        event_timestamp_column="computed_at",
    ),
)
```

### 2.4 Model Training Pipeline

```python
import mlflow
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, average_precision_score,
    brier_score_loss, log_loss,
)
import lightgbm as lgb
import xgboost as xgb
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

class ChurnModelTrainer:
    """Trains and calibrates churn prediction models."""

    def __init__(self, feature_store, experiment_name="churn_prediction"):
        self.feature_store = feature_store
        self.experiment_name = experiment_name
        mlflow.set_experiment(experiment_name)

    def train(
        self,
        training_data: pd.DataFrame,
        model_type: str = "lightgbm",
        calibration_method: str = "isotonic",
    ) -> Dict[str, Any]:
        """Train a churn model with calibration and evaluation."""

        feature_cols = [c for c in training_data.columns if c.startswith("feature_")]
        target_col = "churned_90d"

        X = training_data[feature_cols]
        y = training_data[target_col]

        # Time-series split for temporal data
        tscv = TimeSeriesSplit(n_splits=5)

        # Handle class imbalance
        smote = SMOTE(sampling_strategy=0.3, random_state=42)

        if model_type == "lightgbm":
            base_model = lgb.LGBMClassifier(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=6,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                class_weight="balanced",
                random_state=42,
            )
        elif model_type == "xgboost":
            base_model = xgb.XGBClassifier(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=len(y[y==0]) / len(y[y==1]),
                random_state=42,
            )
        else:
            base_model = GradientBoostingClassifier(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=5,
                random_state=42,
            )

        # Calibrated pipeline
        calibrated = CalibratedClassifierCV(
            base_model, method=calibration_method, cv=3
        )
        pipeline = ImbPipeline([
            ("smote", smote),
            ("classifier", calibrated),
        ])

        # Cross-validation
        cv_results = []
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            pipeline.fit(X_train, y_train)
            y_pred_proba = pipeline.predict_proba(X_val)[:, 1]

            metrics = {
                "fold": fold,
                "roc_auc": roc_auc_score(y_val, y_pred_proba),
                "avg_precision": average_precision_score(y_val, y_pred_proba),
                "brier_score": brier_score_loss(y_val, y_pred_proba),
                "log_loss": log_loss(y_val, y_pred_proba),
            }
            cv_results.append(metrics)

        # Final training on all data
        pipeline.fit(X, y)

        # Log to MLflow
        with mlflow.start_run():
            mlflow.log_params({
                "model_type": model_type,
                "calibration": calibration_method,
                "n_features": len(feature_cols),
                "n_samples": len(X),
                "positive_rate": y.mean(),
            })
            for fold_metrics in cv_results:
                for k, v in fold_metrics.items():
                    mlflow.log_metric(f"cv_{k}", v, step=fold_metrics.get("fold", 0))

            mlflow.sklearn.log_model(pipeline, "model")

        return {
            "pipeline": pipeline,
            "cv_results": cv_results,
            "feature_names": feature_cols,
            "model_type": model_type,
        }
```

---

## 3. Intervention Agent Implementation

### 3.1 Purpose

The Intervention Agent designs, personalizes, and delivers retention interventions:
- **Intervention strategy selection** (discount, outreach, feature education, etc.)
- **Message personalization** using LLM-generated content
- **Channel optimization** (email, in-app, SMS, phone)
- **Timing optimization** (when to send for maximum impact)
- **Budget-aware intervention allocation**

### 3.2 Architecture

```python
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta

INTERVENTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Intervention Agent for the Customer Retention System.

Your capabilities:
1. Strategy Selection: Choose the optimal intervention type based on customer profile
2. Content Personalization: Generate personalized messaging using customer data
3. Channel Optimization: Select the best delivery channel and timing
4. Offer Calibration: Determine appropriate incentive levels
5. Multi-step Journey Design: Create sequenced intervention campaigns

Intervention types:
- proactive_outreach: Personal call/email from account manager
- targeted_discount: Personalized discount or credit
- feature_education: Tutorial or training on underused features
- loyalty_reward: Points, badges, or status upgrades
- product_enhancement: Free add-on or premium trial
- feedback_request: Survey or conversation to address concerns
- win_back_campaign: Re-engagement for already churned customers

Guidelines:
- Match intervention intensity to churn risk level and CLV
- Respect communication frequency caps and opt-out preferences
- Consider customer's preferred language and communication style
- Always include a clear value proposition
- Design for measurable outcomes (define success metrics)
- A/B test intervention variants when possible
- Stay within allocated budget per customer segment

Output: Structured intervention plan with content, channel, timing, and success metrics."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

class InterventionType(str, Enum):
    PROACTIVE_OUTREACH = "proactive_outreach"
    TARGETED_DISCOUNT = "targeted_discount"
    FEATURE_EDUCATION = "feature_education"
    LOYALTY_REWARD = "loyalty_reward"
    PRODUCT_ENHANCEMENT = "product_enhancement"
    FEEDBACK_REQUEST = "feedback_request"
    WIN_BACK_CAMPAIGN = "win_back_campaign"

class ChannelType(str, Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"
    PHONE = "phone"
    PUSH = "push"
    DIRECT_MAIL = "direct_mail"

class InterventionPlan(BaseModel):
    intervention_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    intervention_type: InterventionType
    risk_tier: str
    priority: int = Field(ge=1, le=10)
    channels: List[ChannelType]
    content: Dict[str, Any]  # Personalized message content per channel
    offer_details: Optional[Dict[str, Any]] = None  # Discount amount, features, etc.
    timing: Dict[str, Any]  # {"send_at": datetime, "timezone": str, "expiration": datetime}
    success_metrics: List[str]  # e.g., ["email_open", "feature_used_within_7d", "no_churn_30d"]
    expected_outcome: Dict[str, float]  # {"churn_reduction": 0.15, "engagement_lift": 0.25}
    budget_cost: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str

class InterventionAgent:
    def __init__(self, llm, template_store, channel_optimizer, budget_tracker):
        self.llm = llm
        self.agent = DeepAgent(
            name="intervention",
            llm=self.llm,
            prompt=INTERVENTION_PROMPT,
            tools=[
                SelectInterventionStrategyTool(),
                GeneratePersonalizedContentTool(template_store),
                OptimizeChannelTool(channel_optimizer),
                CalibrateOfferTool(budget_tracker),
                CheckCommunicationCapsTool(),
                ScheduleInterventionTool(),
                CreateABTestVariantTool(),
            ],
        )
        self.template_store = template_store
        self.channel_optimizer = channel_optimizer
        self.budget_tracker = budget_tracker

    async def design_intervention(
        self,
        customer_id: str,
        prediction: ChurnPrediction,
        customer_context: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> InterventionPlan:
        """Design a personalized intervention plan."""

        # Step 1: Select intervention strategy
        strategy = await self._select_strategy(prediction, customer_context)

        # Step 2: Generate personalized content
        content = await self._generate_content(
            customer_id, strategy, prediction, customer_context
        )

        # Step 3: Optimize channel selection
        channels = await self._optimize_channels(customer_id, strategy, customer_context)

        # Step 4: Calibrate offer if applicable
        offer = None
        if strategy in (InterventionType.TARGETED_DISCOUNT, InterventionType.LOYALTY_REWARD):
            offer = await self._calibrate_offer(prediction, customer_context, constraints)

        # Step 5: Determine optimal timing
        timing = await self._optimize_timing(customer_id, channels, customer_context)

        # Step 6: Define success metrics
        success_metrics = self._define_success_metrics(strategy, prediction)

        # Step 7: Calculate expected outcome and cost
        expected = self._estimate_impact(strategy, prediction, offer)
        cost = self._calculate_cost(strategy, offer, channels)

        plan = InterventionPlan(
            customer_id=customer_id,
            intervention_type=strategy,
            risk_tier=prediction.risk_tier,
            priority=self._calculate_priority(prediction),
            channels=channels,
            content=content,
            offer_details=offer,
            timing=timing,
            success_metrics=success_metrics,
            expected_outcome=expected,
            budget_cost=cost,
        )

        await self._persist_plan(plan)
        return plan

    async def _select_strategy(
        self, prediction: ChurnPrediction, context: Dict[str, Any]
    ) -> InterventionType:
        """Select the best intervention strategy based on prediction and context."""

        # Rule-based pre-filtering
        if prediction.risk_tier == "critical":
            if context.get("is_enterprise", False):
                return InterventionType.PROACTIVE_OUTREACH
            return InterventionType.TARGETED_DISCOUNT

        if prediction.risk_tier == "high":
            if "feature_underuse" in prediction.anomaly_flags:
                return InterventionType.FEATURE_EDUCATION
            if "engagement_drop" in prediction.anomaly_flags:
                return InterventionType.PROACTIVE_OUTREACH
            return InterventionType.TARGETED_DISCOUNT

        if prediction.risk_tier == "medium":
            if context.get("nps_score", 10) < 6:
                return InterventionType.FEEDBACK_REQUEST
            return InterventionType.LOYALTY_REWARD

        # Low risk: preventive engagement
        return InterventionType.FEATURE_EDUCATION

    async def _generate_content(
        self,
        customer_id: str,
        strategy: InterventionType,
        prediction: ChurnPrediction,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate personalized content using LLM."""

        # Build content generation prompt
        content_prompt = f"""
        Generate personalized retention intervention content.

        Customer Profile:
        - Name: {context.get('first_name', 'Valued Customer')}
        - Company: {context.get('company_name', 'N/A')}
        - Plan: {context.get('plan_type', 'Unknown')}
        - Tenure: {context.get('tenure_days', 0)} days
        - Key features used: {context.get('top_features', [])}
        - Recent activity: {context.get('recent_activity_summary', 'N/A')}

        Intervention Type: {strategy.value}
        Churn Risk: {prediction.risk_tier} (probability: {prediction.churn_probability:.2f})
        Top Risk Factors: {[f['feature'] for f in prediction.top_features[:3]]}

        Generate:
        1. Email subject line (max 60 chars)
        2. Email body (max 500 words, warm and personal tone)
        3. In-app message (max 200 chars)
        4. SMS message (max 160 chars)

        Tone: Professional but warm, empathetic, value-focused.
        Language: {context.get('preferred_language', 'en')}
        """

        response = await self.llm.ainvoke(content_prompt)
        return self._parse_content_response(response.content)

    async def _optimize_channels(
        self, customer_id: str, strategy: InterventionType, context: Dict[str, Any]
    ) -> List[ChannelType]:
        """Select optimal delivery channels."""

        # Get channel preferences and history
        channel_history = await self.channel_optimizer.get_channel_performance(customer_id)

        # Score each channel
        channel_scores = {}
        for channel in ChannelType:
            score = self._score_channel(channel, strategy, context, channel_history)
            channel_scores[channel] = score

        # Select top channels (max 2 for non-critical, 3 for critical)
        max_channels = 3 if strategy == InterventionType.PROACTIVE_OUTREACH else 2
        sorted_channels = sorted(channel_scores.items(), key=lambda x: x[1], reverse=True)

        selected = [ch for ch, score in sorted_channels[:max_channels] if score > 0.3]

        # Always include at least one channel
        if not selected:
            selected = [ChannelType.EMAIL]

        return selected

    def _score_channel(
        self,
        channel: ChannelType,
        strategy: InterventionType,
        context: Dict[str, Any],
        history: Dict[str, Any],
    ) -> float:
        """Score a channel's effectiveness for this intervention."""
        score = 0.5  # Base score

        # Preference boost
        if context.get("preferred_channel") == channel:
            score += 0.2

        # Historical performance
        hist = history.get(channel.value, {})
        score += hist.get("open_rate", 0) * 0.15
        score += hist.get("response_rate", 0) * 0.15

        # Strategy-channel fit
        fit_scores = {
            InterventionType.PROACTIVE_OUTREACH: {
                ChannelType.PHONE: 0.3, ChannelType.EMAIL: 0.2,
            },
            InterventionType.TARGETED_DISCOUNT: {
                ChannelType.EMAIL: 0.2, ChannelType.IN_APP: 0.15, ChannelType.PUSH: 0.1,
            },
            InterventionType.FEATURE_EDUCATION: {
                ChannelType.IN_APP: 0.3, ChannelType.EMAIL: 0.15,
            },
            InterventionType.LOYALTY_REWARD: {
                ChannelType.PUSH: 0.2, ChannelType.IN_APP: 0.15, ChannelType.EMAIL: 0.1,
            },
        }
        score += fit_scores.get(strategy, {}).get(channel, 0)

        # Recency penalty (don't overuse same channel)
        last_used = hist.get("last_used_days_ago", 30)
        if last_used < 3:
            score -= 0.3
        elif last_used < 7:
            score -= 0.1

        return max(0.0, min(1.0, score))

    async def _calibrate_offer(
        self,
        prediction: ChurnPrediction,
        context: Dict[str, Any],
        constraints: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calibrate the offer amount based on CLV and risk."""

        clv = prediction.clv_estimate or context.get("estimated_clv", 0)
        risk = prediction.churn_probability

        # Base offer as percentage of CLV
        if risk >= 0.8:
            offer_pct = 0.15  # 15% of CLV
        elif risk >= 0.6:
            offer_pct = 0.10
        elif risk >= 0.35:
            offer_pct = 0.05
        else:
            offer_pct = 0.02

        offer_value = clv * offer_pct

        # Apply budget constraints
        max_budget = constraints.get("max_offer_per_customer", float("inf"))
        offer_value = min(offer_value, max_budget)

        # Determine offer type
        plan_type = context.get("plan_type", "monthly")
        if plan_type == "annual":
            offer = {
                "type": "percentage_discount",
                "value": min(offer_pct * 100, 25),  # Cap at 25%
                "duration_months": 3,
                "description": f"{offer_pct*100:.0f}% discount for 3 months",
            }
        else:
            offer = {
                "type": "account_credit",
                "value": round(offer_value, 2),
                "duration_months": 1,
                "description": f"${offer_value:.2f} account credit",
            }

        return offer

    def _define_success_metrics(
        self, strategy: InterventionType, prediction: ChurnPrediction
    ) -> List[str]:
        """Define measurable success metrics for the intervention."""
        base_metrics = ["intervention_delivered", "intervention_acknowledged"]

        strategy_metrics = {
            InterventionType.PROACTIVE_OUTREACH: [
                "call_completed", "meeting_scheduled", "concern_addressed",
                "no_churn_30d",
            ],
            InterventionType.TARGETED_DISCOUNT: [
                "offer_accepted", "payment_succeeds_30d", "no_churn_30d",
            ],
            InterventionType.FEATURE_EDUCATION: [
                "tutorial_completed", "feature_used_within_7d",
                "engagement_score_improved", "no_churn_30d",
            ],
            InterventionType.LOYALTY_REWARD: [
                "reward_claimed", "engagement_increase_14d", "no_churn_30d",
            ],
            InterventionType.FEEDBACK_REQUEST: [
                "survey_completed", "feedback_addressed", "nps_improved",
            ],
            InterventionType.WIN_BACK_CAMPAIGN: [
                "re_engaged", "login_within_7d", "conversion_30d",
            ],
        }

        return base_metrics + strategy_metrics.get(strategy, ["no_churn_30d"])
```

### 3.3 Intervention Delivery Pipeline

```python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery("interventions", broker="redis://localhost:6379/1")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def deliver_intervention(self, intervention_id: str):
    """Deliver an intervention through the specified channels."""
    try:
        plan = get_intervention_plan(intervention_id)
        customer = get_customer(plan.customer_id)

        results = {}
        for channel in plan.channels:
            if channel == ChannelType.EMAIL:
                results["email"] = send_email(
                    to=customer.email,
                    subject=plan.content["email_subject"],
                    body=plan.content["email_body"],
                    tracking_id=intervention_id,
                )
            elif channel == ChannelType.IN_APP:
                results["in_app"] = send_in_app_message(
                    user_id=customer.id,
                    message=plan.content["in_app_message"],
                    campaign_id=intervention_id,
                )
            elif channel == ChannelType.SMS:
                results["sms"] = send_sms(
                    phone=customer.phone,
                    message=plan.content["sms_message"],
                    tracking_id=intervention_id,
                )
            elif channel == ChannelType.PUSH:
                results["push"] = send_push_notification(
                    user_id=customer.id,
                    title=plan.content.get("push_title", "Special Offer"),
                    body=plan.content["in_app_message"],
                    campaign_id=intervention_id,
                )

        # Record delivery
        record_intervention_delivery(intervention_id, results)

        # Schedule follow-up measurement
        schedule_measurement.delay(
            intervention_id=intervention_id,
            customer_id=plan.customer_id,
            metrics=plan.success_metrics,
            measure_after_days=30,
        )

        return results

    except Exception as exc:
        raise self.retry(exc=exc)

@celery_app.task
def process_intervention_queue():
    """Process pending interventions that are ready for delivery."""
    now = datetime.utcnow()
    pending = get_pending_interventions(before=now, limit=100)

    for plan in pending:
        # Check communication caps
        if not check_communication_cap(plan.customer_id, plan.channels):
            reschedule_intervention(plan.intervention_id, delay_hours=24)
            continue

        # Check if customer state has changed
        current_prediction = get_latest_prediction(plan.customer_id)
        if current_prediction and current_prediction.risk_tier == "low":
            cancel_intervention(plan.intervention_id, reason="risk_resolved")
            continue

        deliver_intervention.delay(plan.intervention_id)

# Schedule queue processing every 5 minutes
celery_app.conf.beat_schedule = {
    "process-intervention-queue": {
        "task": "interventions.process_intervention_queue",
        "schedule": 300.0,  # 5 minutes
    },
}
```

---

## 4. Optimization Agent Implementation

### 4.1 Purpose

The Optimization Agent continuously improves the retention system:
- **A/B test design and analysis** for interventions
- **Strategy parameter tuning** (thresholds, offer levels, timing)
- **Budget allocation optimization** across segments
- **Model performance monitoring** and retraining triggers
- **Causal impact estimation** using quasi-experimental methods

### 4.2 Architecture

```python
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from scipy import stats

OPTIMIZATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Optimization Agent for the Customer Retention System.

Your capabilities:
1. A/B Test Analysis: Evaluate experiment results and recommend winners
2. Strategy Tuning: Optimize thresholds, offer levels, and timing parameters
3. Budget Allocation: Distribute retention budget across segments for maximum ROI
4. Causal Inference: Estimate true intervention impact using causal methods
5. Model Monitoring: Track prediction model performance and trigger retraining
6. Multi-armed Bandit: Balance exploration vs exploitation in intervention selection

Guidelines:
- Always use statistical significance (p < 0.05) before recommending changes
- Consider practical significance, not just statistical significance
- Account for multiple comparisons when analyzing many variants
- Respect minimum sample sizes before drawing conclusions
- Consider long-term effects, not just immediate metrics
- Document all experiments with hypotheses and learnings

Output: Structured optimization recommendations with confidence levels and expected impact."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

class ABTestResult(BaseModel):
    experiment_id: str
    hypothesis: str
    variants: List[Dict[str, Any]]  # [{"name": "control", "n": 1000, "churn_rate": 0.12}, ...]
    primary_metric: str
    results: Dict[str, Any]  # Statistical test results
    winner: Optional[str] = None
    confidence: float
    recommendation: str
    sample_size_adequate: bool
    duration_days: int

class OptimizationRecommendation(BaseModel):
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # "strategy", "budget", "model", "timing", "channel"
    priority: int = Field(ge=1, le=10)
    current_state: Dict[str, Any]
    proposed_change: Dict[str, Any]
    expected_impact: Dict[str, float]  # {"churn_reduction": 0.05, "roi_lift": 0.15}
    confidence: float
    supporting_evidence: Dict[str, Any]
    risks: List[str]
    rollback_plan: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OptimizationAgent:
    def __init__(self, experiment_store, metrics_store, budget_tracker):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.agent = DeepAgent(
            name="optimization",
            llm=self.llm,
            prompt=OPTIMIZATION_PROMPT,
            tools=[
                AnalyzeABTestTool(experiment_store),
                TuneStrategyParametersTool(),
                OptimizeBudgetAllocationTool(budget_tracker),
                EstimateCausalImpactTool(),
                MonitorModelPerformanceTool(),
                RunMultiArmedBanditTool(),
            ],
        )
        self.experiment_store = experiment_store
        self.metrics_store = metrics_store
        self.budget_tracker = budget_tracker

    async def analyze_experiment(self, experiment_id: str) -> ABTestResult:
        """Analyze an A/B test and recommend a winner."""

        experiment = await self.experiment_store.get_experiment(experiment_id)
        variants_data = await self.experiment_store.get_variant_metrics(experiment_id)

        # Check sample size adequacy
        adequate = self._check_sample_size(experiment, variants_data)

        # Perform statistical test
        if experiment["type"] == "binary":
            results = self._proportion_test(variants_data)
        elif experiment["type"] == "continuous":
            results = self._t_test(variants_data)
        else:
            results = self._mann_whitney_test(variants_data)

        # Determine winner
        winner = None
        if results["p_value"] < 0.05 and adequate:
            winner = self._select_winner(variants_data, experiment["primary_metric"])

        # Build recommendation
        recommendation = self._build_recommendation(
            experiment, variants_data, results, winner, adequate
        )

        return ABTestResult(
            experiment_id=experiment_id,
            hypothesis=experiment["hypothesis"],
            variants=variants_data,
            primary_metric=experiment["primary_metric"],
            results=results,
            winner=winner,
            confidence=1.0 - results["p_value"],
            recommendation=recommendation,
            sample_size_adequate=adequate,
            duration_days=(datetime.utcnow() - experiment["started_at"]).days,
        )

    def _proportion_test(self, variants: List[Dict]) -> Dict[str, Any]:
        """Chi-squared test for binary outcomes (e.g., churn rates)."""
        control = variants[0]
        treatment = variants[1]

        # Contingency table
        n1, x1 = control["n"], control["conversions"]
        n2, x2 = treatment["n"], treatment["conversions"]

        p1 = x1 / n1
        p2 = x2 / n2
        p_pool = (x1 + x2) / (n1 + n2)

        se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        z_stat = (p2 - p1) / se if se > 0 else 0
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

        # Effect size (relative lift)
        relative_lift = (p2 - p1) / p1 if p1 > 0 else 0

        # Confidence interval for difference
        se_diff = np.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2)
        ci_lower = (p2 - p1) - 1.96 * se_diff
        ci_upper = (p2 - p1) + 1.96 * se_diff

        return {
            "test_type": "chi_squared",
            "control_rate": p1,
            "treatment_rate": p2,
            "absolute_difference": p2 - p1,
            "relative_lift": relative_lift,
            "ci_95": (ci_lower, ci_upper),
            "z_statistic": z_stat,
            "p_value": p_value,
            "significant": p_value < 0.05,
        }

    async def optimize_budget_allocation(
        self,
        total_budget: float,
        segments: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Optimize budget allocation across customer segments."""

        # Build optimization problem
        # Maximize: sum(churn_reduction_i * customers_i)
        # Subject to: sum(cost_i) <= total_budget
        #            cost_i >= min_spend_i for each segment

        from scipy.optimize import minimize

        n_segments = len(segments)

        def objective(allocations):
            """Negative total churn reduction (for minimization)."""
            total = 0
            for i, seg in enumerate(segments):
                # Diminishing returns model
                effectiveness = seg["intervention_effectiveness"]
                customers = seg["customer_count"]
                # Logarithmic diminishing returns
                churn_reduction = effectiveness * customers * np.log1p(allocations[i] / seg["cost_per_customer"])
                total += churn_reduction
            return -total

        def budget_constraint(allocations):
            return total_budget - sum(allocations)

        # Initial allocation: proportional to segment value
        x0 = np.array([total_budget * seg["customer_count"] / sum(s["customer_count"] for s in segments)
                       for seg in segments])

        # Bounds: min and max per segment
        bounds = []
        for seg in segments:
            min_spend = constraints.get("min_spend_per_segment", 0) if constraints else 0
            max_spend = constraints.get("max_spend_per_segment", total_budget) if constraints else total_budget
            bounds.append((min_spend, max_spend))

        constraints_list = [
            {"type": "ineq", "fun": budget_constraint},
        ]

        result = minimize(
            objective, x0, method="SLSQP", bounds=bounds, constraints=constraints_list
        )

        allocation = {
            seg["segment_id": result[i]
            for i, seg in enumerate(segments)
        }

        return {
            "total_budget": total_budget,
            "allocation": allocation,
            "expected_churn_reduction": -result.fun,
            "optimization_success": result.success,
            "segments_optimized": n_segments,
        }

    async def estimate_causal_impact(
        self,
        intervention_id: str,
        method: str = "propensity_matching",
    ) -> Dict[str, Any]:
        """Estimate the causal impact of an intervention using quasi-experimental methods."""

        if method == "propensity_matching":
            return await self._propensity_score_matching(intervention_id)
        elif method == "difference_in_differences":
            return await self._difference_in_differences(intervention_id)
        elif method == "synthetic_control":
            return await self._synthetic_control(intervention_id)
        else:
            raise ValueError(f"Unknown causal inference method: {method}")

    async def _propensity_score_matching(
        self, intervention_id: str
    ) -> Dict[str, Any]:
        """Estimate causal impact using propensity score matching."""

        from sklearn.linear_model import LogisticRegression
        from sklearn.neighbors import NearestNeighbors

        # Get treatment and control groups
        data = await self.metrics_store.get_intervention_outcomes(intervention_id)

        treatment = data[data["received_intervention"] == 1]
        control = data[data["received_intervention"] == 0]

        # Features for matching
        feature_cols = [
            "tenure_days", "contract_value", "engagement_score_7d",
            "recency_days", "frequency_30d", "monetary_90d",
            "support_tickets_30d", "nps_score_latest",
        ]

        # Fit propensity score model
        X = data[feature_cols]
        y = data["received_intervention"]

        ps_model = LogisticRegression(max_iter=1000, random_state=42)
        ps_model.fit(X, y)
        data["propensity_score"] = ps_model.predict_proba(X)[:, 1]

        # Match treatment to control
        treatment_ps = data[data["received_intervention"] == 1]["propensity_score"].values.reshape(-1, 1)
        control_ps = data[data["received_intervention"] == 0]["propensity_score"].values.reshape(-1, 1)

        nbrs = NearestNeighbors(n_neighbors=1).fit(control_ps)
        distances, indices = nbrs.kneighbors(treatment_ps)

        # Calculate ATT (Average Treatment Effect on Treated)
        treatment_outcomes = data[data["received_intervention"] == 1]["churned_30d"].values
        matched_control_outcomes = data[data["received_intervention"] == 0]["churned_30d"].values[indices.flatten()]

        att = np.mean(treatment_outcomes - matched_control_outcomes)

        # Bootstrap confidence interval
        n_bootstrap = 1000
        bootstrap_atts = []
        for _ in range(n_bootstrap):
            sample_idx = np.random.choice(len(treatment_outcomes), size=len(treatment_outcomes), replace=True)
            bootstrap_atts.append(np.mean(treatment_outcomes[sample_idx] - matched_control_outcomes[sample_idx]))

        ci_lower = np.percentile(bootstrap_atts, 2.5)
        ci_upper = np.percentile(bootstrap_atts, 97.5)

        return {
            "method": "propensity_score_matching",
            "att": att,
            "ci_95": (ci_lower, ci_upper),
            "n_treated": len(treatment),
            "n_control": len(control),
            "n_matched": len(treatment_outcomes),
            "balance_check": self._check_covariate_balance(data, feature_cols),
        }

    async def monitor_model_performance(self) -> Dict[str, Any]:
        """Monitor prediction model performance and trigger retraining if needed."""

        # Get recent predictions and actual outcomes
        recent = await self.metrics_store.get_recent_predictions_with_outcomes(days=30)

        # Calculate performance metrics
        from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss

        y_true = recent["churned"].values
        y_pred_proba = recent["predicted_probability"].values

        current_metrics = {
            "roc_auc": roc_auc_score(y_true, y_pred_proba),
            "log_loss": log_loss(y_true, y_pred_proba),
            "brier_score": brier_score_loss(y_true, y_pred_proba),
            "calibration_error": self._expected_calibration_error(y_true, y_pred_proba),
        }

        # Compare to baseline
        baseline = await self.metrics_store.get_baseline_metrics()
        drift_detected = self._detect_performance_degradation(current_metrics, baseline)

        # Check for data drift
        feature_drift = await self._check_feature_drift(days=30)

        retraining_needed = drift_detected or feature_drift["significant_drift"]

        return {
            "current_metrics": current_metrics,
            "baseline_metrics": baseline,
            "drift_detected": drift_detected,
            "feature_drift": feature_drift,
            "retraining_needed": retraining_needed,
            "recommended_action": "retrain" if retraining_needed else "monitor",
        }

    def _expected_calibration_error(
        self, y_true: np.ndarray, y_pred_proba: np.ndarray, n_bins: int = 10
    ) -> float:
        """Calculate Expected Calibration Error (ECE)."""
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        for i in range(n_bins):
            mask = (y_pred_proba >= bin_boundaries[i]) & (y_pred_proba < bin_boundaries[i+1])
            if mask.sum() > 0:
                avg_confidence = y_pred_proba[mask].mean()
                avg_accuracy = y_true[mask].mean()
                ece += (mask.sum() / len(y_true)) * abs(avg_confidence - avg_accuracy)
        return ece
```

### 4.3 Multi-Armed Bandit for Intervention Selection

```python
import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass, field

@dataclass
class BanditArm:
    """Represents one intervention option."""
    arm_id: str
    intervention_type: str
    alpha: int = 1  # Successes + 1 (Beta prior)
    beta: int = 1   # Failures + 1 (Beta prior)
    total_pulls: int = 0
    total_reward: float = 0.0

    @property
    def mean_reward(self) -> float:
        return self.total_reward / self.total_pulls if self.total_pulls > 0 else 0.5

    @property
    def uncertainty(self) -> float:
        """Standard deviation of Beta distribution."""
        return np.sqrt(
            (self.alpha * self.beta) /
            ((self.alpha + self.beta)**2 * (self.alpha + self.beta + 1))
        )

class ThompsonSamplingBandit:
    """Thompson Sampling bandit for intervention selection."""

    def __init__(self, arms: List[BanditArm], exploration_factor: float = 1.0):
        self.arms = {arm.arm_id: arm for arm in arms}
        self.exploration_factor = exploration_factor

    def select_arm(self, context: Dict[str, Any] = None) -> str:
        """Select an arm using Thompson Sampling."""
        samples = {}
        for arm_id, arm in self.arms.items]:
            # Sample from Beta posterior
            sample = np.random.beta(arm.alpha, arm.beta)
            samples[arm_id] = sample

        # Select arm with highest sample
        return max(samples, key=samples.get)

    def update(self, arm_id: str, reward: float):
        """Update arm statistics after observing reward."""
        arm = self.arms[arm_id]
        arm.total_pulls += 1
        arm.total_reward += reward

        # Update Beta parameters
        if reward > 0:
            arm.alpha += reward
        else:
            arm.beta += (1 - reward)

    def get_arm_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all arms."""
        return {
            arm_id: {
                "mean_reward": arm.mean_reward,
                "uncertainty": arm.uncertainty,
                "total_pulls": arm.total_pulls,
                "alpha": arm.alpha,
                "beta": arm.beta,
            }
            for arm_id, arm in self.arms.items()
        }

class ContextualBandit:
    """Contextual bandit using LinUCB for intervention selection."""

    def __init__(self, n_arms: int, n_features: int, alpha: float = 1.0):
        self.n_arms = n_arms
        self.n_features = n_features
        self.alpha = alpha

        # Initialize A and b for each arm (LinUCB)
        self.A = {i: np.eye(n_features) for i in range(n_arms)}
        self.b = {i: np.zeros(n_features) for i in range(n_arms)}

    def select_arm(self, context_vector: np.ndarray) -> int:
        """Select arm using LinUCB policy."""
        ucb_values = {}

        for arm in range(self.n_arms):
            A_inv = np.linalg.inv(self.A[arm])
            theta = A_inv @ self.b[arm]

            # UCB = expected reward + alpha * uncertainty
            expected_reward = context_vector @ theta
            uncertainty = np.sqrt(context_vector @ A_inv @ context_vector)
            ucb_values[arm] = expected_reward + self.alpha * uncertainty

        return max(ucb_values, key=ucb_values.get)

    def update(self, arm: int, context_vector: np.ndarray, reward: float):
        """Update arm parameters after observing reward."""
        self.A[arm] += np.outer(context_vector, context_vector)
        self.b[arm] += reward * context_vector
```

---

## 5. Performance Analytics Agent Implementation

### 5.1 Purpose

The Performance Analytics Agent measures, reports, and derives insights:
- **Real-time dashboard metrics** (churn rate, retention rate, intervention ROI)
- **Cohort analysis** and customer lifecycle reporting
- **Attribution modeling** for intervention effectiveness
- **Anomaly detection** on key business metrics
- **Automated insight generation** and alerting

### 5.2 Architecture

```python
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

ANALYTICS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Performance Analytics Agent for the Customer Retention System.

Your capabilities:
1. KPI Tracking: Monitor churn rate, retention rate, CLV, NPS, and intervention ROI
2. Cohort Analysis: Track customer cohorts over time to identify trends
3. Attribution Modeling: Determine which interventions drive retention
4. Anomaly Detection: Identify unusual patterns in key metrics
5. Insight Generation: Automatically surface actionable insights
6. Reporting: Generate executive summaries and detailed reports

Key Metrics:
- Churn Rate: % of customers who cancel within a period
- Retention Rate: % of customers who remain active
- Net Revenue Retention (NRR): Revenue expansion minus contraction minus churn
- Gross Revenue Retention (GRR): Revenue retained excluding expansion
- Customer Lifetime Value (CLV): Predicted total revenue per customer
- Intervention ROI: (Revenue saved - Intervention cost) / Intervention cost
- Time to Rescue: Average time from risk detection to successful intervention

Guidelines:
- Always segment metrics by customer tier, plan type, and cohort
- Compare against historical baselines and targets
- Distinguish correlation from causation
- Highlight both positive and negative trends
- Provide actionable recommendations, not just data

Output: Structured analytics report with metrics, trends, insights, and recommendations."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

class RetentionMetrics(BaseModel):
    period_start: datetime
    period_end: datetime
    segment: str
    total_customers: int
    churned_customers: int
    churn_rate: float
    retention_rate: float
    gross_revenue_retention: float
    net_revenue_retention: float
    avg_clv: float
    total_interventions: int
    successful_interventions: int
    intervention_success_rate: float
    intervention_roi: float
    avg_time_to_rescue_hours: float
    nps_avg: float
    period_over_period_change: Dict[str, float]

class AnalyticsInsight(BaseModel):
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # "positive", "negative", "neutral", "anomaly"
    severity: str  # "info", "warning", "critical"
    title: str
    description: str
    affected_segment: str
    metric_impacted: str
    trend_direction: str  # "improving", "declining", "stable"
    recommended_actions: List[str]
    confidence: float
    detected_at: datetime = Field(default_factory=datetime.utcnow)

class PerformanceAnalyticsAgent:
    def __init__(self, metrics_store, report_store, alert_manager):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.agent = DeepAgent(
            name="analytics",
            llm=self.llm,
            prompt=ANALYTICS_PROMPT,
            tools=[
                ComputeRetentionMetricsTool(metrics_store),
                RunCohortAnalysisTool(metrics_store),
                AttributeInterventionImpactTool(metrics_store),
                DetectMetricAnomaliesTool(metrics_store),
                GenerateInsightReportTool(),
                CreateDashboardWidgetTool(),
                ScheduleReportTool(),
            ],
        )
        self.metrics_store = metrics_store
        self.report_store = report_store
        self.alert_manager = alert_manager

    async def compute_retention_metrics(
        self,
        period_start: datetime,
        period_end: datetime,
        segment: Optional[str] = None,
    ) -> RetentionMetrics:
        """Compute comprehensive retention metrics for a period."""

        # Base query
        query = """
        WITH customer_status AS (
            SELECT
                c.customer_id,
                c.segment,
                c.plan_type,
                c.clv_estimate,
                c.nps_score,
                CASE WHEN c.churn_date BETWEEN :start AND :end THEN 1 ELSE 0 END as churned,
                COALESCE(SUM(i.cost), 0) as intervention_cost,
                COALESCE(SUM(CASE WHEN i.success = true THEN 1 ELSE 0 END), 0) as successful_interventions,
                COUNT(i.intervention_id) as total_interventions
            FROM customers c
            LEFT JOIN interventions i ON c.customer_id = i.customer_id
                AND i.created_at BETWEEN :start AND :end
            WHERE c.created_at <= :end
            {segment_filter}
            GROUP BY c.customer_id, c.segment, c.plan_type, c.clv_estimate, c.nps_score, c.churn_date
        ),
        revenue AS (
            SELECT
                segment,
                SUM(CASE WHEN churned = 0 THEN clv_estimate ELSE 0 END) as retained_revenue,
                SUM(clv_estimate) as total_revenue,
                SUM(CASE WHEN churned = 1 THEN clv_estimate ELSE 0 END) as churned_revenue
            FROM customer_status
            GROUP BY segment
        )
        SELECT
            cs.segment,
            COUNT(*) as total_customers,
            SUM(cs.churned) as churned_customers,
            AVG(cs.churned) as churn_rate,
            1 - AVG(cs.churned) as retention_rate,
            r.retained_revenue / r.total_revenue as grr,
            r.retained_revenue / r.total_revenue as nrr,  -- Simplified; expansion revenue would be added
            AVG(cs.clv_estimate) as avg_clv,
            SUM(cs.total_interventions) as total_interventions,
            SUM(cs.successful_interventions) as successful_interventions,
            AVG(cs.nps_avg) as nps_avg
        FROM customer_status cs
        JOIN revenue r ON cs.segment = r.segment
        GROUP BY cs.segment, r.retained_revenue, r.total_revenue
        """

        segment_filter = "AND c.segment = :segment" if segment else ""
        query = query.format(segment_filter=segment_filter)

        params = {"start": period_start, "end": period_end}
        if segment:
            params["segment"] = segment

        result = await self.metrics_store.execute(query, params)
        row = result.fetchone()

        # Compute intervention ROI
        total_intervention_cost = await self.metrics_store.get_total_intervention_cost(
            period_start, period_end, segment
        )
        revenue_saved = await self.metrics_store.get_revenue_saved(
            period_start, period_end, segment
        )
        roi = (revenue_saved - total_intervention_cost) / total_intervention_cost if total_intervention_cost > 0 else 0

        # Period-over-period change
        prev_period = await self._get_previous_period_metrics(period_start, period_end, segment)
        pod_change = self._compute_period_change(row, prev_period)

        return RetentionMetrics(
            period_start=period_start,
            period_end=period_end,
            segment=segment or "all",
            total_customers=row.total_customers,
            churned_customers=row.churned_customers,
            churn_rate=row.churn_rate,
            retention_rate=row.retention_rate,
            gross_revenue_retention=row.grr,
            net_revenue_retention=row.nrr,
            avg_clv=row.avg_clv,
            total_interventions=row.total_interventions,
            successful_interventions=row.successful_interventions,
            intervention_success_rate=(
                row.successful_interventions / row.total_interventions
                if row.total_interventions > 0 else 0
            ),
            intervention_roi=roi,
            avg_time_to_rescue_hours=await self._compute_avg_time_to_rescue(
                period_start, period_end, segment
            ),
            nps_avg=row.nps_avg,
            period_over_period_change=pod_change,
        )

    async def run_cohort_analysis(
        self,
        cohort_definition: str = "signup_month",
        metric: str = "retention_rate",
        periods: int = 12,
    ) -> Dict[str, Any]:
        """Run cohort analysis to track customer groups over time."""

        query = """
        WITH cohorts AS (
            SELECT
                customer_id,
                DATE_TRUNC('month', created_at) as cohort_month,
                segment,
                plan_type
            FROM customers
            WHERE created_at >= :start_date
        ),
        activity AS (
            SELECT
                c.customer_id,
                c.cohort_month,
                c.segment,
                DATE_TRUNC('month', e.event_date) as activity_month,
                COUNT(e.event_id) as event_count
            FROM cohorts c
            LEFT JOIN customer_events e ON c.customer_id = e.customer_id
            GROUP BY c.customer_id, c.cohort_month, c.segment, DATE_TRUNC('month', e.event_date)
        )
        SELECT
            cohort_month,
            activity_month,
            segment,
            COUNT(DISTINCT customer_id) as active_customers,
            COUNT(DISTINCT customer_id) * 1.0 /
                FIRST_VALUE(COUNT(DISTINCT customer_id)) OVER (
                    PARTITION BY cohort_month, segment ORDER BY activity_month
                ) as retention_rate
        FROM activity
        GROUP BY cohort_month, activity_month, segment
        ORDER BY cohort_month, activity_month
        """

        start_date = datetime.utcnow() - timedelta(days=30 * periods)
        results = await self.metrics_store.execute(query, {"start_date": start_date})

        # Pivot into cohort table
        cohort_data = []
        for row in results:
            cohort_data.append({
                "cohort_month": row.cohort_month,
                "activity_month": row.activity_month,
                "segment": row.segment,
                "active_customers": row.active_customers,
                "retention_rate": row.retention_rate,
                "period_number": (row.activity_month - row.cohort_month).days // 30,
            })

        df = pd.DataFrame(cohort_data)

        # Compute cohort insights
        insights = self._analyze_cohort_trends(df)

        return {
            "cohort_definition": cohort_definition,
            "metric": metric,
            "data": cohort_data,
            "insights": insights,
            "summary_statistics": {
                "avg_retention_3m": df[df["period_number"] == 3]["retention_rate"].mean(),
                "avg_retention_6m": df[df["period_number"] == 6]["retention_rate"].mean(),
                "avg_retention_12m": df[df["period_number"] == 12]["retention_rate"].mean(),
                "best_cohort": df.groupby("cohort_month")["retention_rate"].mean().idxmax(),
                "worst_cohort": df.groupby("cohort_month")["retention_rate"].mean().idxmin(),
            },
        }

    async def detect_anomalies(self) -> List[AnalyticsInsight]:
        """Detect anomalies in key metrics and generate insights."""

        insights = []

        # Check churn rate anomaly
        churn_anomaly = await self._check_churn_rate_anomaly()
        if churn_anomaly:
            insights.append(churn_anomaly)

        # Check intervention ROI anomaly
        roi_anomaly = await self._check_intervention_roi_anomaly()
        if roi_anomaly:
            insights.append(roi_anomaly)

        # Check engagement drop
        engagement_anomaly = await self._check_engagement_anomaly()
        if engagement_anomaly:
            insights.append(engagement_anomaly)

        # Check NPS drop
        nps_anomaly = await self._check_nps_anomaly()
        if nps_anomaly:
            insights.append(nps_anomaly)

        # Send alerts for critical insights
        for insight in insights:
            if insight.severity == "critical":
                await self.alert_manager.send_alert(
                    channel="slack",
                    message=f"🚨 CRITICAL: {insight.title} - {insight.description}",
                    priority="P1",
                )

        return insights

    async def _check_churn_rate_anomaly(self) -> Optional[AnalyticsInsight]:
        """Detect unusual churn rate changes."""
        # Get daily churn rates for last 30 days
        daily_rates = await self.metrics_store.get_daily_churn_rates(days=30)

        if len(daily_rates) < 7:
            return None

        rates = np.array([r["churn_rate"] for r in daily_rates])
        mean_rate = np.mean(rates[:-7])  # Baseline from earlier days
        std_rate = np.std(rates[:-7])
        recent_mean = np.mean(rates[-7:])  # Last 7 days

        # Z-score for recent period
        z_score = (recent_mean - mean_rate) / std_rate if std_rate > 0 else 0

        if abs(z_score) > 2.5:  # Anomaly threshold
            direction = "increased" if z_score > 0 else "decreased"
            severity = "critical" if abs(z_score) > 3.5 else "warning"

            return AnalyticsInsight(
                category="anomaly",
                severity=severity,
                title=f"Churn Rate Anomaly: {direction} {abs(z_score):.1f}σ",
                description=(
                    f"7-day average churn rate ({recent_mean:.1%}) is {abs(z_score):.1f} standard "
                    f"deviations {direction} from the 30-day baseline ({mean_rate:.1%})."
                ),
                affected_segment="all",
                metric_impacted="churn_rate",
                trend_direction="declining" if z_score > 0 else "improving",
                recommended_actions=[
                    "Review recent product changes or incidents",
                    "Check for competitive actions or market shifts",
                    "Analyze churned customer feedback for common themes",
                    "Verify data pipeline integrity",
                ],
                confidence=min(abs(z_score) / 4.0, 0.99),
            )

        return None

    async def generate_executive_summary(
        self, period: str = "monthly"
    ) -> Dict[str, Any]:
        """Generate an executive summary report."""

        if period == "monthly":
            start = datetime.utcnow() - timedelta(days=30)
        elif period == "quarterly":
            start = datetime.utcnow() - timedelta(days=90)
        else:
            start = datetime.utcnow() - timedelta(days=7)

        end = datetime.utcnow()

        metrics = await self.compute_retention_metrics(start, end)
        insights = await self.detect_anomalies()
        top_interventions = await self._get_top_interventions(start, end)
        segment_breakdown = await self._get_segment_breakdown(start, end)

        # Use LLM to generate narrative summary
        summary_prompt = f"""
        Generate an executive summary for the customer retention program.

        Key Metrics (Last {period}):
        - Churn Rate: {metrics.churn_rate:.1%} (change: {metrics.period_over_period_change.get('churn_rate', 0):+.1%})
        - Retention Rate: {metrics.retention_rate:.1%}
        - Net Revenue Retention: {metrics.net_revenue_retention:.1%}
        - Avg CLV: ${metrics.avg_clv:,.0f}
        - Intervention ROI: {metrics.intervention_roi:.1%}
        - Successful Interventions: {metrics.successful_interventions}/{metrics.total_interventions}

        Key Insights:
        {self._format_insights_for_prompt(insights)}

        Top Performing Interventions:
        {self._format_interventions_for_prompt(top_interventions)}

        Write a concise executive summary (max 300 words) highlighting:
        1. Overall retention health
        2. Key wins and concerns
        3. Recommended focus areas for next period
        """

        narrative = await self.llm.ainvoke(summary_prompt)

        return {
            "period": period,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "metrics": metrics.model_dump(),
            "insights": [i.model_dump() for i in insights],
            "top_interventions": top_interventions,
            "segment_breakdown": segment_breakdown,
            "executive_summary": narrative.content,
            "generated_at": datetime.utcnow().isoformat(),
        }
```

### 5.3 Dashboard and Reporting

```python
from fastapi import FastAPI, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional

app = FastAPI(title="Customer Retention Analytics API")

@app.get("/api/v1/metrics/retention")
async def get_retention_metrics(
    start: datetime = Query(default=None),
    end: datetime = Query(default=None),
    segment: Optional[str] = None,
    analytics_agent: PerformanceAnalyticsAgent = Depends(get_analytics_agent),
):
    """Get retention metrics for a period."""
    if not start:
        start = datetime.utcnow() - timedelta(days=30)
    if not end:
        end = datetime.utcnow()

    metrics = await analytics_agent.compute_retention_metrics(start, end, segment)
    return metrics

@app.get("/api/v1/analytics/cohorts")
async def get_cohort_analysis(
    cohort_by: str = Query(default="signup_month"),
    metric: str = Query(default="retention_rate"),
    periods: int = Query(default=12, ge=3, le=24),
    analytics_agent: PerformanceAnalyticsAgent = Depends(get_analytics_agent),
):
    """Get cohort analysis."""
    return await analytics_agent.run_cohort_analysis(cohort_by, metric, periods)

@app.get("/api/v1/analytics/insights")
async def get_insights(
    severity: Optional[str] = Query(default=None),
    analytics_agent: PerformanceAnalyticsAgent = Depends(get_analytics_agent),
):
    """Get current analytics insights."""
    insights = await analytics_agent.detect_anomalies()
    if severity:
        insights = [i for i in insights if i.severity == severity]
    return {"insights": [i.model_dump() for i in insights]}

@app.get("/api/v1/reports/executive-summary")
async def get_executive_summary(
    period: str = Query(default="monthly", regex="^(weekly|monthly|quarterly)$"),
    analytics_agent: PerformanceAnalyticsAgent = Depends(get_analytics_agent),
):
    """Generate executive summary report."""
    return await analytics_agent.generate_executive_summary(period)

@app.get("/api/v1/analytics/realtime")
async def get_realtime_metrics(
    analytics_agent: PerformanceAnalyticsAgent = Depends(get_analytics_agent),
):
    """Get real-time metrics for live dashboard."""
    # Cached in Redis with 60s TTL
    cache_key = "retention:realtime_metrics"
    cached = await analytics_agent.metrics_store.get_cache(cache_key)

    if cached:
        return json.loads(cached)

    # Compute real-time metrics
    metrics = {
        "active_customers_24h": await analytics_agent.metrics_store.get_active_count(hours=24),
        "interventions_delivered_24h": await analytics_agent.metrics_store.get_intervention_count(hours=24),
        "churn_risk_alerts_24h": await analytics_agent.metrics_store.get_alert_count(hours=24),
        "avg_churn_probability_24h": await analytics_agent.metrics_store.get_avg_churn_probability(hours=24),
        "intervention_success_rate_7d": await analytics_agent.metrics_store.get_success_rate(days=7),
        "current_runway_months": await analytics_agent.metrics_store.get_runway(),
    }

    # Cache for 60 seconds
    await analytics_agent.metrics_store.set_cache(
        cache_key, json.dumps(metrics), ttl=60
    )

    return metrics
```

---

## 6. Code Examples and Snippets

### 6.1 Complete Agent Initialization

```python
# main.py - Application entry point
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from agents.orchestrator import OrchestratorAgent
from agents.prediction import PredictionAgent
from agents.intervention import InterventionAgent
from agents.optimization import OptimizationAgent
from agents.analytics import PerformanceAnalyticsAgent
from infrastructure.state import SharedStateManager
from infrastructure.database import get_db_session
from infrastructure.model_registry import ModelRegistry

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    # Initialize shared components
    state_manager = SharedStateManager()
    db_session = await get_db_session()
    model_registry = ModelRegistry()
    await model_registry.load_models()

    # Initialize agents
    app.state.orchestrator = OrchestratorAgent()
    app.state.prediction = PredictionAgent(
        model_registry=model_registry,
        feature_store=app.state.feature_store,
        db_session=db_session,
    )
    app.state.intervention = InterventionAgent(
        llm=ChatOpenAI(model="gpt-4o"),
        template_store=app.state.template_store,
        channel_optimizer=app.state.channel_optimizer,
        budget_tracker=app.state.budget_tracker,
    )
    app.state.optimization = OptimizationAgent(
        experiment_store=app.state.experiment_store,
        metrics_store=app.state.metrics_store,
        budget_tracker=app.state.budget_tracker,
    )
    app.state.analytics = PerformanceAnalyticsAgent(
        metrics_store=app.state.metrics_store,
        report_store=app.state.report_store,
        alert_manager=app.state.alert_manager,
    )

    # Start background tasks
    asyncio.create_task(app.state.prediction.start_batch_scoring())
    asyncio.create_task(app.state.analytics.start_continuous_monitoring())

    yield

    # Cleanup
    await db_session.close()
    await state_manager.close()

app = FastAPI(lifespan=lifespan)
```

### 6.2 Database Schema

```sql
-- Core schema for customer retention system

CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(200),
    plan_type VARCHAR(50) NOT NULL,
    segment VARCHAR(50) NOT NULL DEFAULT 'standard',
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, at_risk, churned, won_back
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    churn_date TIMESTAMPTZ,
    clv_estimate DECIMAL(12, 2),
    nps_score INTEGER,
    preferred_language VARCHAR(10) DEFAULT 'en',
    preferred_channel VARCHAR(20),
    timezone VARCHAR(50) DEFAULT 'UTC',
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE customer_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    event_type VARCHAR(50) NOT NULL, -- login, purchase, support_ticket, feature_use, etc.
    event_data JSONB DEFAULT '{}',
    event_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customer_events_customer_date ON customer_events(customer_id, event_date DESC);
CREATE INDEX idx_customer_events_type_date ON customer_events(event_type, event_date DESC);

CREATE TABLE predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    churn_probability DECIMAL(5, 4) NOT NULL,
    confidence_interval_lower DECIMAL(5, 4) NOT NULL,
    confidence_interval_upper DECIMAL(5, 4) NOT NULL,
    risk_tier VARCHAR(20) NOT NULL,
    prediction_window_days INTEGER NOT NULL DEFAULT 30,
    model_version VARCHAR(50) NOT NULL,
    top_features JSONB DEFAULT '[]',
    clv_estimate DECIMAL(12, 2),
    anomaly_flags JSONB DEFAULT '[]',
    prediction_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actual_outcome BOOLEAN, -- Filled in later for model evaluation
    outcome_timestamp TIMESTAMPTZ
);

CREATE INDEX idx_predictions_customer ON predictions(customer_id, prediction_timestamp DESC);
CREATE INDEX idx_predictions_risk ON predictions(risk_tier, prediction_timestamp DESC);

CREATE TABLE interventions (
    intervention_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    prediction_id UUID REFERENCES predictions(prediction_id),
    intervention_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'planned', -- planned, scheduled, delivered, acknowledged, completed, cancelled
    priority INTEGER NOT NULL DEFAULT 5,
    channels JSONB NOT NULL DEFAULT '[]',
    content JSONB NOT NULL DEFAULT '{}',
    offer_details JSONB,
    scheduled_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    success_metrics JSONB DEFAULT '[]',
    actual_outcome JSONB,
    cost DECIMAL(10, 2) DEFAULT 0,
    correlation_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_interventions_customer ON interventions(customer_id, created_at DESC);
CREATE INDEX idx_interventions_status ON interventions(status, scheduled_at);
CREATE INDEX idx_interventions_correlation ON interventions(correlation_id);

CREATE TABLE experiments (
    experiment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    hypothesis TEXT NOT NULL,
    experiment_type VARCHAR(20) NOT NULL, -- ab_test, bandit, switchback
    status VARCHAR(20) NOT NULL DEFAULT 'draft', -- draft, running, paused, completed, archived
    primary_metric VARCHAR(100) NOT NULL,
    secondary_metrics JSONB DEFAULT '[]',
    variants JSONB NOT NULL DEFAULT '[]',
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTz,
    min_sample_size INTEGER DEFAULT 1000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE agent_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id UUID NOT NULL,
    sender VARCHAR(50) NOT NULL,
    recipient VARCHAR(50) NOT NULL,
    message_type VARCHAR(100) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    payload JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_agent_messages_correlation ON agent_messages(correlation_id);
CREATE INDEX idx_agent_messages_status ON agent_messages(status, created_at);
```

### 6.3 Docker Compose Configuration

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
      - DATABASE_URL=postgresql://retention:retention@postgres:5432/retention
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - LANGCHAIN_TRACING_V2=true
      - LANGCHAIN_PROJECT=customer-retention
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://retention:retention@postgres:5432/retention
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis
      - postgres
    deploy:
      replicas: 4

  scheduler:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A tasks beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://retention:retention@postgres:5432/retention
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=retention
      - POSTGRES_PASSWORD=retention
      - POSTGRES_DB=retention
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U retention"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  langsmith:
    image: langchain/langsmith:latest
    ports:
      - "8080:8080"
    environment:
      - LANGCHAIN_TRACING_V2=true

volumes:
  postgres_data:
  redis_data:
```

### 6.4 Environment Configuration

```bash
# .env
# Database
DATABASE_URL=postgresql://retention:retention@localhost:5432/retention
REDIS_URL=redis://localhost:6379

# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.1

# LangChain / LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=customer-retention
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Feature Store
FEAST_REPOSITORY_PATH=./feature_repo
FEAST_ONLINE_STORE_HOST=postgres
FEAST_ONLINE_STORE_PORT=5432

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=churn_prediction

# Agent Configuration
ORCHESTRATOR_MAX_CONCURRENT_WORKFLOWS=50
PREDICTION_BATCH_SIZE=1000
PREDICTION_REFRESH_INTERVAL_HOURS=24
INTERVENTION_MAX_DAILY_PER_CUSTOMER=3
INTERVENTION_COOLDOWN_HOURS=24
OPTIMIZATION_MIN_SAMPLE_SIZE=1000
ANOMALY_DETECTION_SENSITIVITY=2.5

# Monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
PAGERDUTY_KEY=...
METRICS_EXPORT_INTERVAL_SECONDS=60
```

---

## 7. Testing Strategy

### 7.1 Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5%)  - Full workflow integration tests
                   ─┤─────────┤
                  │   API    │  (15%) - Endpoint contract tests
                 ─┤──────────┤
                │  Agent    │  (20%) - Agent behavior & tool tests
               ─┤────────────┤
              │  Service   │  (30%) - Business logic unit tests
             ─┤──────────────┤
            │  Repository  │  (30%) - Data access layer tests
            └───────────────┘
```

### 7.2 Unit Tests

```python
# tests/test_prediction_agent.py
import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from agents.prediction import PredictionAgent, ChurnPrediction
from models.schemas import AgentRole

@pytest.fixture
def mock_feature_store():
    store = AsyncMock()
    store.get_online_features.return_value = {
        "recency_days": 15,
        "frequency_30d": 3,
        "monetary_90d": 299.99,
        "engagement_score_7d": 0.45,
        "support_tickets_30d": 2,
        "nps_score_latest": 7,
        "tenure_days": 365,
        "payment_failures_90d": 0,
        "feature_usage_breadth": 0.3,
        "days_since_last_login": 5,
        "contract_value": 3600.0,
        "discount_dependency": 0.1,
    }
    return store

@pytest.fixture
def mock_model_registry():
    registry = MagicMock()
    registry.get_model.return_value = MagicMock(
        predict_proba=MagicMock(return_value=np.array([[0.7, 0.3]]))
    )
    return registry

@pytest.fixture
def prediction_agent(mock_feature_store, mock_model_registry):
    return PredictionAgent(
        model_registry=mock_model_registry,
        feature_store=mock_feature_store,
        db_session=AsyncMock(),
    )

@pytest.mark.asyncio
async def test_predict_churn_returns_valid_prediction(prediction_agent):
    """Test that predict_churn returns a valid ChurnPrediction."""
    result = await prediction_agent.predict_churn(
        customer_id="cust_123",
        window_days=30,
    )

    assert isinstance(result, ChurnPrediction)
    assert result.customer_id == "cust_123"
    assert 0.0 <= result.churn_probability <= 1.0
    assert result.confidence_interval[0] <= result.churn_probability <= result.confidence_interval[1]
    assert result.risk_tier in ("low", "medium", "high", "critical")
    assert result.prediction_window_days == 30
    assert result.model_version is not None

@pytest.mark.asyncio
async def test_risk_tier_classification(prediction_agent):
    """Test risk tier classification logic."""
    test_cases = [
        (0.95, ["anomaly1", "anomaly2", "anomaly3"], "critical"),
        (0.85, [], "critical"),
        (0.70, ["anomaly1"], "high"),
        (0.50, [], "high"),
        (0.40, ["anomaly1"], "medium"),
        (0.20, [], "low"),
    ]

    for prob, anomalies, expected_tier in test_cases:
        tier = prediction_agent._classify_risk_tier(prob, anomalies)
        assert tier == expected_tier, f"Failed for prob={prob}, anomalies={len(anomalies)}"

@pytest.mark.asyncio
async def test_batch_predict_handles_empty_list(prediction_agent):
    """Test batch prediction with empty customer list."""
    result = await prediction_agent.batch_predict([])
    assert result == []

@pytest.mark.asyncio
async def test_feature_computation_handles_missing_data(mock_feature_store):
    """Test feature computation with missing data."""
    mock_feature_store.get_online_features.return_value = {
        "recency_days": None,
        "frequency_30d": 0,
    }

    agent = PredictionAgent(
        model_registry=MagicMock(),
        feature_store=mock_feature_store,
        db_session=AsyncMock(),
    )

    # Should not raise, should handle gracefully
    features = await agent._compute_features("cust_123")
    assert "rfm_score" in features
    assert "engagement_trend" in features
```

### 7.3 Agent Behavior Tests

```python
# tests/test_agent_behavior.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.orchestrator import OrchestratorAgent
from agents.intervention import InterventionAgent, InterventionType, ChannelType
from models.schemas import AgentRole, AgentMessage, MessagePriority

@pytest.mark.asyncio
async def test_orchestrator_routes_churn_signal_to_prediction():
    """Test that orchestrator correctly routes churn risk signals."""
    orchestrator = OrchestratorAgent()
    orchestrator._call_agent = AsyncMock()

    # Mock prediction response
    orchestrator._call_agent.return_value = MagicMock(
        confidence=0.85,
        payload={"churn_probability": 0.75, "risk_tier": "high"},
    )

    result = await orchestrator.process_customer_signal(
        customer_id="cust_123",
        signal={"type": "churn_risk_alert", "source": "engagement_drop"},
    )

    # Verify prediction agent was called
    call_args = orchestrator._call_agent.call_args_list
    assert any(
        call[0][0] == AgentRole.PREDICTION for call in call_args
    ), "Prediction agent should be called for churn risk signals"

@pytest.mark.asyncio
async def test_orchestrator_defers_on_low_confidence():
    """Test that orchestrator defers workflow when prediction confidence is low."""
    orchestrator = OrchestratorAgent()
    orchestrator._call_agent = AsyncMock()
    orchestrator._call_agent.return_value = MagicMock(
        confidence=0.45,
        payload={"churn_probability": 0.55},
    )

    result = await orchestrator.process_customer_signal(
        customer_id="cust_123",
        signal={"type": "churn_risk_alert"},
    )

    assert result.status == "deferred"
    assert "Low prediction confidence" in result.payload["reason"]

@pytest.mark.asyncio
async def test_intervention_agent_selects_correct_strategy():
    """Test intervention strategy selection based on risk tier."""
    agent = InterventionAgent(
        llm=AsyncMock(),
        template_store=AsyncMock(),
        channel_optimizer=AsyncMock(),
        budget_tracker=AsyncMock(),
    )

    # Critical risk enterprise → proactive outreach
    strategy = await agent._select_strategy(
        prediction=MagicMock(risk_tier="critical", anomaly_flags=[]),
        context={"is_enterprise": True},
    )
    assert strategy == InterventionType.PROACTIVE_OUTREACH

    # Critical risk non-enterprise → targeted discount
    strategy = await agent._select_strategy(
        prediction=MagicMock(risk_tier="critical", anomaly_flags=[]),
        context={"is_enterprise": False},
    )
    assert strategy == InterventionType.TARGETED_DISCOUNT

    # High risk with feature underuse → feature education
    strategy = await agent._select_strategy(
        prediction=MagicMock(risk_tier="high", anomaly_flags=["feature_underuse"]),
        context={},
    )
    assert strategy == InterventionType.FEATURE_EDUCATION

    # Medium risk with low NPS → feedback request
    strategy = await agent._select_strategy(
        prediction=MagicMock(risk_tier="medium", anomaly_flags=[]),
        context={"nps_score": 4},
    )
    assert strategy == InterventionType.FEEDBACK_REQUEST

@pytest.mark.asyncio
async def test_intervention_agent_respects_communication_caps():
    """Test that intervention agent checks communication caps."""
    agent = InterventionAgent(
        llm=AsyncMock(),
        template_store=AsyncMock(),
        channel_optimizer=AsyncMock(),
        budget_tracker=AsyncMock(),
    )

    # Mock cap check
    agent.agent = MagicMock()
    agent.agent.tools = []

    # Should not exceed daily cap
    with patch("agents.intervention.check_communication_caps") as mock_caps:
        mock_caps.return_value = False
        # Intervention should be rescheduled, not delivered
        # This would be tested at the delivery pipeline level
```

### 7.4 Integration Tests

```python
# tests/test_integration.py
import pytest
import asyncio
from datetime import datetime, timedelta
from testclient import TestClient

from main import app
from infrastructure.database import get_db_session
from infrastructure.state import SharedStateManager

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_full_retention_workflow(test_client):
    """End-to-end test: signal → prediction → intervention → measurement."""
    customer_id = "test-cust-001"

    # Step 1: Ingest customer signal
    response = test_client.post("/api/v1/signals", json={
        "customer_id": customer_id,
        "type": "churn_risk_alert",
        "source": "engagement_drop",
        "data": {"engagement_drop_percent": 40},
    })
    assert response.status_code == 202
    correlation_id = response.json()["correlation_id"]

    # Step 2: Wait for workflow to complete (with timeout)
    for _ in range(30):
        await asyncio.sleep(1)
        status = test_client.get(f"/api/v1/workflows/{correlation_id}")
        if status.json()["status"] in ("completed", "failed"):
            break

    workflow_result = status.json()
    assert workflow_result["status"] == "completed"
    assert "prediction" in workflow_result["result"]
    assert "intervention" in workflow_result["result"]

    # Step 3: Verify prediction was stored
    predictions = test_client.get(f"/api/v1/customers/{customer_id}/predictions")
    assert predictions.status_code == 200
    assert len(predictions.json()) > 0

    # Step 4: Verify intervention was created
    interventions = test_client.get(f"/api/v1/customers/{customer_id}/interventions")
    assert interventions.status_code == 200
    assert len(interventions.json()) > 0

@pytest.mark.asyncio
async def test_batch_prediction_endpoint(test_client):
    """Test batch prediction endpoint."""
    customer_ids = [f"batch-cust-{i:03d}" for i in range(50)]

    response = test_client.post("/api/v1/predictions/batch", json={
        "customer_ids": customer_ids,
        "window_days": 30,
    })

    assert response.status_code == 202
    result = response.json()
    assert result["total_requested"] == 50
    assert result["status"] == "processing"

    # Poll for completion
    job_id = result["job_id"]
    for _ in range(60):
        await asyncio.sleep(2)
        status = test_client.get(f"/api/v1/jobs/{job_id}")
        if status.json()["status"] in ("completed", "failed"):
            break

    final = status.json()
    assert final["status"] == "completed"
    assert final["successful"] >= 45  # Allow some failures

@pytest.mark.asyncio
async def test_analytics_metrics_endpoint(test_client):
    """Test analytics metrics computation."""
    response = test_client.get("/api/v1/metrics/retention", params={
        "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
        "end": datetime.utcnow().isoformat(),
    })

    assert response.status_code == 200
    metrics = response.json()
    assert "churn_rate" in metrics
    assert "retention_rate" in metrics
    assert "intervention_roi" in metrics
    assert 0 <= metrics["churn_rate"] <= 1
    assert 0 <= metrics["retention_rate"] <= 1
```

### 7.5 Load and Performance Tests

```python
# tests/test_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from locust import HttpUser, task, between

class RetentionAPIUser(HttpUser):
    """Locust load test for retention API."""

    wait_time = between(1, 5)

    @task(3)
    def get_metrics(self):
        self.client.get("/api/v1/metrics/retention")

    @task(2)
    def get_realtime_metrics(self):
        self.client.get("/api/v1/analytics/realtime")

    @task(1)
    def submit_signal(self):
        self.client.post("/api/v1/signals", json={
            "customer_id": f"load-test-{self.user_id}",
            "type": "engagement_drop",
            "data": {"drop_percent": 25},
        })

    @task(1)
    def get_executive_summary(self):
        self.client.get("/api/v1/reports/executive-summary?period=weekly")

@pytest.mark.asyncio
async def test_prediction_latency_sla():
    """Test that predictions complete within SLA (p99 < 500ms)."""
    latencies = []

    for i in range(100):
        start = time.monotonic()
        # Make prediction request
        response = await make_prediction_request(f"perf-test-{i}")
        latency = (time.monotonic() - start) * 1000  # ms
        latencies.append(latency)

    p50 = np.percentile(latencies, 50)
    p99 = np.percentile(latencies, 99)

    assert p50 < 100, f"p50 latency {p50:.1f}ms exceeds 100ms SLA"
    assert p99 < 500, f"p99 latency {p99:.1f}ms exceeds 500ms SLA"

@pytest.mark.asyncio
async def test_concurrent_agent_workflows():
    """Test system handles concurrent agent workflows."""
    async def run_workflow(customer_id: str):
        return await submit_signal_and_wait(customer_id, timeout=60)

    # Run 20 concurrent workflows
    tasks = [run_workflow(f"concurrent-{i}") for i in range(20)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) >= 18, f"Only {len(successes)}/20 concurrent workflows succeeded"
```

### 7.6 Model Evaluation Tests

```python
# tests/test_model_evaluation.py
import pytest
import numpy as np
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, average_precision_score,
    brier_score_loss, log_loss, confusion_matrix, classification_report,
)
from calibration import calibration_curve

class TestChurnModelEvaluation:
    """Comprehensive model evaluation tests."""

    @pytest.fixture
    def model_predictions(self):
        """Load model predictions and actual outcomes."""
        # In practice, load from database
        np.random.seed(42)
        n = 10000
        y_true = np.random.binomial(1, 0.15, n)  # 15% churn rate
        y_pred_proba = np.random.beta(2, 8, n)  # Skewed toward low probabilities
        # Add some signal
        y_pred_proba[y_true == 1] = np.random.beta(5, 5, y_true.sum())
        return y_true, y_pred_proba

    def test_roc_auc_above_threshold(self, model_predictions):
        """Model ROC-AUC must be above 0.75."""
        y_true, y_pred_proba = model_predictions
        auc = roc_auc_score(y_true, y_pred_proba)
        assert auc > 0.75, f"ROC-AUC {auc:.3f} below threshold 0.75"

    def test_average_precision_above_threshold(self, model_predictions):
        """Model average precision must be above 0.40."""
        y_true, y_pred_proba = model_predictions
        ap = average_precision_score(y_true, y_pred_proba)
        assert ap > 0.40, f"Average precision {ap:.3f} below threshold 0.40"

    def test_calibration_error_below_threshold(self, model_predictions):
        """Expected Calibration Error must be below 0.05."""
        y_true, y_pred_proba = model_predictions
        ece = compute_ece(y_true, y_pred_proba, n_bins=10)
        assert ece < 0.05, f"ECE {ece:.3f} exceeds threshold 0.05"

    def test_brier_score_below_threshold(self, model_predictions):
        """Brier score must be below 0.10."""
        y_true, y_pred_proba = model_predictions
        brier = brier_score_loss(y_true, y_pred_proba)
        assert brier < 0.10, f"Brier score {brier:.3f} exceeds threshold 0.10"

    def test_precision_at_10_percent(self, model_predictions):
        """Precision at 10% recall must be above 0.50."""
        y_true, y_pred_proba = model_predictions
        precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)

        # Find precision at 10% recall
        idx = np.argmin(np.abs(recall - 0.10))
        precision_at_10 = precision[idx]

        assert precision_at_10 > 0.50, (
            f"Precision@10% recall {precision_at_10:.3f} below threshold 0.50"
        )

    def test_no_prediction_drift(self):
        """Test that model predictions haven't drifted significantly."""
        recent_predictions = get_recent_predictions(days=7)
        baseline_predictions = get_baseline_predictions()

        # KS test for distribution difference
        from scipy.stats import ks_2samp
        ks_stat, p_value = ks_2samp(
            recent_predictions["predicted_probability"],
            baseline_predictions["predicted_probability"],
        )

        assert p_value > 0.01, (
            f"Prediction distribution drift detected (KS stat: {ks_stat:.3f}, p: {p_value:.4f})"
        )

    def test_fairness_across_segments(self, model_predictions):
        """Test model fairness across customer segments."""
        y_true, y_pred_proba = model_predictions
        segments = get_customer_segments(len(y_true))

        segment_metrics = {}
        for segment in np.unique(segments):
            mask = segments == segment
            segment_metrics[segment] = {
                "roc_auc": roc_auc_score(y_true[mask], y_pred_proba[mask]),
                "avg_predicted": np.mean(y_pred_proba[mask]),
                "avg_actual": np.mean(y_true[mask]),
            }

        # Check calibration across segments
        for segment, metrics in segment_metrics.items():
            calibration_gap = abs(metrics["avg_predicted"] - metrics["avg_actual"])
            assert calibration_gap < 0.10, (
                f"Segment {segment} calibration gap {calibration_gap:.3f} exceeds 0.10"
            )
```

### 7.7 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy agents/ infrastructure/

  unit-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[test]"
      - run: pytest tests/unit -v --cov=agents --cov-report=xml
      - uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[test]"
      - run: pytest tests/test_integration.py -v

  model-evaluation:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[test]"
      - run: pytest tests/test_model_evaluation.py -v
      - name: Check model metrics thresholds
        run: |
          python scripts/check_model_thresholds.py \
            --min-auc 0.75 \
            --min-ap 0.40 \
            --max-ece 0.05

  load-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install locust
      - name: Start services
        run: docker-compose up -d
      - name: Run load tests
        run: locust -f tests/test_performance.py --headless -u 100 -r 10 --run-time 5m
      - name: Stop services
        run: docker-compose down
```

---

## Appendix A: Deployment Checklist

- [ ] Infrastructure provisioned (Kubernetes / ECS / Cloud Run)
- [ ] PostgreSQL with pgvector extension configured
- [ ] Redis cluster configured with persistence
- [ ] Feature store (Feast) deployed and populated
- [ ] MLflow tracking server configured
- [ ] LangSmith project created and API keys configured
- [ ] Model artifacts uploaded to model registry
- [ ] Celery workers scaled appropriately
- [ ] Monitoring dashboards created (Grafana / Datadog)
- [ ] Alert rules configured (PagerDuty / Opsgenie)
- [ ] CI/CD pipeline active
- [ ] Runbooks documented for common incidents
- [ ] Disaster recovery plan tested
- [ ] Security review completed (secrets, RBAC, encryption)
- [ ] GDPR / CCPA compliance verified
- [ ] Load tests passed at 2x expected traffic
- [ ] Rollback procedure tested

## Appendix B: Key Metrics Reference

| Metric | Definition | Target | Alert Threshold |
|--------|-----------|--------|-----------------|
| Churn Rate | % customers lost per period | < 5% monthly | > 8% monthly |
| Retention Rate | % customers retained | > 95% monthly | < 92% monthly |
| NRR | Net Revenue Retention | > 110% | < 100% |
| GRR | Gross Revenue Retention | > 90% | < 85% |
| Intervention ROI | (Revenue saved - Cost) / Cost | > 3.0 | < 1.5 |
| Prediction AUC | Model discrimination | > 0.80 | < 0.75 |
| Calibration ECE | Expected Calibration Error | < 0.03 | > 0.05 |
| Time to Rescue | Hours from alert to intervention | < 24h | > 72h |
| Customer Satisfaction | NPS score | > 40 | < 20 |

---

*End of Implementation Plan*
