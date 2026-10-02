# AI-Powered Marketing Attribution Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Status:** Draft for Review

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Data Collection Agent Implementation](#2-data-collection-agent-implementation)
3. [Attribution Engine](#3-attribution-engine)
4. [Predictive Analytics Agent Implementation](#4-predictive-analytics-agent-implementation)
5. [Reporting Agent Implementation](#5-reporting-agent-implementation)
6. [Real-time Dashboards](#6-real-time-dashboards)
7. [Integration with Ad Platforms and CRM](#7-integration-with-ad-platforms-and-crm)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The AI-powered marketing attribution system uses LangChain DeepAgents to orchestrate a multi-agent pipeline that collects touchpoint data, computes attribution across multiple models, predicts future campaign performance, and generates actionable reports. The architecture follows a hub-and-spoke pattern with a central orchestrator coordinating specialized agents.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                            │
│              (LangChain DeepAgents Planner)                      │
│         ┌──────────┬──────────┬──────────┬──────────┐           │
│         │          │          │          │          │           │
│    ┌────▼───┐ ┌───▼────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼─────┐     │
│    │  Data  │ │Attrib- │ │Predict-│ │Report- │ │Integra-│     │
│    │Collect │ │  ution │ │  ive   │ │  ing   │ │  tion  │     │
│    │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │     │
│    └────┬───┘ └───┬────┘ └──┬─────┘ └──┬─────┘ └──┬─────┘     │
│         │         │         │          │          │            │
│    ┌────▼─────────▼─────────▼──────────▼──────────▼────┐      │
│    │              SHARED STATE / MEMORY                   │      │
│    │         (Redis + PostgreSQL + Vector DB)            │      │
│    └─────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Agent Roles and Responsibilities

| Agent | Role | Input | Output | Tools |
|-------|------|-------|--------|-------|
| **Orchestrator** | Plans task decomposition, routes subtasks, aggregates results | User query, campaign context | Task plan, final response | DeepAgents planner, memory |
| **Data Collection Agent** | Fetches touchpoint data from ad platforms, CRM, web analytics | Date range, channel filters | Normalized touchpoint dataset | API clients, web scrapers |
| **Attribution Agent** | Computes multi-touch attribution using Markov, Shapley, and deep learning models | Touchpoint dataset | Attribution weights per channel/touchpoint | Markov chains, Shapley solver, PyTorch |
| **Predictive Analytics Agent** | Forecasts campaign performance, budget allocation, ROI | Historical attribution + spend data | Predictions, recommendations | Prophet, XGBoost, LLM reasoning |
| **Reporting Agent** | Generates human-readable reports, dashboards, alerts | Attribution results + predictions | Markdown/PDF reports, chart specs | Jinja2, Plotly, LLM summarization |
| **Integration Agent** | Manages API connections, OAuth tokens, data sync | Platform credentials | Synced data, connection status | REST clients, webhook handlers |

### 1.3 LangChain DeepAgents Configuration

```python
from langchain_deepagents import DeepAgent
from langchain_deepagents.planner import PlannerConfig
from langchain_deepagents.memory import SharedMemory
from langchain_deepagents.tools import ToolRegistry

# Planner configuration
planner_config = PlannerConfig(
    max_iterations=20,
    max_tool_calls_per_iteration=5,
    enable_reflection=True,
    reflection_threshold=0.7,
    parallel_tool_execution=True,
)

# Shared memory across agents
shared_memory = SharedMemory(
    backend="redis",
    redis_url="redis://localhost:6379/0",
    vector_db_url="http://localhost:6333",  # Qdrant
    session_ttl=86400,
)

# Tool registry
tool_registry = ToolRegistry()
tool_registry.register("fetch_ad_data", fetch_ad_platform_data)
tool_registry.register("compute_markov_attribution", compute_markov_chain_attribution)
tool_registry.register("compute_shapley_attribution", compute_shapley_attribution)
tool_registry.register("train_attribution_model", train_deep_attribution_model)
tool_registry.register("forecast_performance", forecast_campaign_performance)
tool_registry.register("generate_report", generate_attribution_report)
tool_registry.register("sync_crm_data", sync_crm_touchpoints)

# Orchestrator agent
orchestrator = DeepAgent(
    name="marketing-attribution-orchestrator",
    planner_config=planner_config,
    memory=shared_memory,
    tools=tool_registry,
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
)
```

### 1.4 Communication Protocol

Agents communicate via a structured message bus using JSON schemas:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AgentMessageType(str, Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    DATA_PAYLOAD = "data_payload"
    ERROR = "error"
    STATUS_UPDATE = "status_update"

class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str
    message_type: AgentMessageType
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)

class TaskRequest(BaseModel):
    task_id: str
    task_type: str  # "data_collection", "attribution", "prediction", "reporting"
    parameters: Dict[str, Any]
    dependencies: List[str] = []
    timeout_seconds: int = 300

class TaskResponse(BaseModel):
    task_id: str
    status: str  # "completed", "failed", "partial"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: int
    artifacts: List[str] = []  # File paths or URLs to outputs
```

### 1.5 State Management

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

@dataclass
class AttributionSession:
    session_id: str
    created_at: str
    status: str  # "initialized", "collecting", "attributing", "predicting", "reporting", "completed"
    raw_touchpoints: List[Dict] = field(default_factory=list)
    normalized_touchpoints: List[Dict] = field(default_factory=list)
    attribution_results: Dict[str, Dict] = field(default_factory=dict)
    predictions: Dict[str, Any] = field(default_factory=dict)
    reports: List[str] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "status": self.status,
            "touchpoint_count": len(self.normalized_touchpoints),
            "attribution_models": list(self.attribution_results.keys()),
            "report_count": len(self.reports),
            "error_count": len(self.errors),
            "metadata": self.metadata,
        }
```

---

## 2. Data Collection Agent Implementation

### 2.1 Architecture

The Data Collection Agent is responsible for gathering marketing touchpoint data from multiple sources: ad platforms (Google Ads, Meta Ads, LinkedIn Ads), CRM systems (Salesforce, HubSpot), web analytics (Google Analytics 4, Mixpanel), and email platforms (Mailchimp, SendGrid).

```
┌──────────────────────────────────────────────────────┐
│              DATA COLLECTION AGENT                    │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Source     │  │  Source      │  │  Source     │ │
│  │  Connector  │  │  Connector   │  │  Connector  │ │
│  │  Factory    │  │  Registry    │  │  Health     │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                │                  │        │
│  ┌──────▼────────────────▼──────────────────▼──────┐ │
│  │           NORMALIZATION PIPELINE                │ │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────────────┐ │ │
│  │  │ Schema  │ │ Identity │ │  Deduplication   │ │ │
│  │  │ Mapper  │ │ Resolver │ │  & Enrichment    │ │ │
│  │  └─────────┘ └──────────┘ └──────────────────┘ │ │
│  └──────────────────────┬──────────────────────────┘ │
│                         │                            │
│  ┌──────────────────────▼──────────────────────────┐ │
│  │           OUTPUT: Unified Touchpoint Schema      │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 2.2 Unified Touchpoint Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ChannelType(str, Enum):
    PAID_SEARCH = "paid_search"
    PAID_SOCIAL = "paid_social"
    DISPLAY = "display"
    VIDEO = "video"
    EMAIL = "email"
    ORGANIC_SEARCH = "organic_search"
    ORGANIC_SOCIAL = "organic_social"
    DIRECT = "direct"
    REFERRAL = "referral"
    AFFILIATE = "affiliate"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class TouchpointType(str, Enum):
    IMPRESSION = "impression"
    CLICK = "click"
    VIEW = "view"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    LEAD = "lead"
    OPPORTUNITY = "opportunity"
    SALE = "sale"

class UnifiedTouchpoint(BaseModel):
    """Canonical touchpoint schema across all channels."""
    touchpoint_id: str = Field(..., description="Unique touchpoint identifier")
    user_id: str = Field(..., description="Anonymized user identifier")
    session_id: Optional[str] = None
    timestamp: datetime
    channel: ChannelType
    touchpoint_type: TouchpointType
    
    # Source-specific metadata
    source_platform: str  # "google_ads", "meta_ads", "salesforce", etc.
    source_campaign_id: Optional[str] = None
    source_ad_group_id: Optional[str] = None
    source_ad_id: Optional[str] = None
    source_creative_id: Optional[str] = None
    
    # Attribution-relevant fields
    campaign_name: Optional[str] = None
    ad_group_name: Optional[str] = None
    ad_name: Optional[str] = None
    keyword: Optional[str] = None
    placement: Optional[str] = None
    device_type: Optional[str] = None  # "mobile", "desktop", "tablet"
    geo_country: Optional[str] = None
    geo_region: Optional[str] = None
    
    # Cost and revenue
    cost: float = 0.0
    revenue: float = 0.0
    conversion_value: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    data_quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
```

### 2.3 Source Connectors

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime, timedelta
import asyncio
import aiohttp
import logging

logger = logging.getLogger(__name__)

class BaseSourceConnector(ABC):
    """Abstract base class for all data source connectors."""
    
    def __init__(self, credentials: Dict[str, str], config: Dict[str, Any] = None):
        self.credentials = credentials
        self.config = config or {}
        self.rate_limiter = AsyncRateLimiter(
            calls_per_second=self.config.get("rate_limit", 10)
        )
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers=self._get_auth_headers(),
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        pass
    
    @abstractmethod
    async def fetch_touchpoints(
        self,
        start_date: datetime,
        end_date: datetime,
        cursor: Optional[str] = None,
    ) -> AsyncIterator[UnifiedTouchpoint]:
        """Fetch touchpoints from the source, yielding normalized records."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check connection health and credential validity."""
        pass
    
    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """Fetch available campaigns, ad groups, etc. for the account."""
        pass


class GoogleAdsConnector(BaseSourceConnector):
    """Google Ads API connector using the Google Ads API v17."""
    
    BASE_URL = "https://googleads.googleapis.com/v17/customers"
    
    def _get_auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.credentials['access_token']}",
            "developer-token": self.credentials["developer_token"],
            "Content-Type": "application/json",
        }
    
    async def fetch_touchpoints(
        self,
        start_date: datetime,
        end_date: datetime,
        cursor: Optional[str] = None,
    ) -> AsyncIterator[UnifiedTouchpoint]:
        customer_id = self.credentials["customer_id"]
        url = f"{self.BASE_URL}/{customer_id}/googleAds:searchStream"
        
        query = self._build_ga_query(start_date, end_date)
        payload = {"query": query}
        if cursor:
            payload["pageToken"] = cursor
        
        async with self.rate_limiter:
            async with self._session.post(url, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
        
        for row in data.get("results", []):
            yield self._normalize_row(row)
        
        if data.get("nextPageToken"):
            async for tp in self.fetch_touchpoints(
                start_date, end_date, data["nextPageToken"]
            ):
                yield tp
    
    def _build_ga_query(self, start: datetime, end: datetime) -> str:
        return f"""
            SELECT
                segments.date,
                campaign.id,
                campaign.name,
                ad_group.id,
                ad_group.name,
                ad_group_ad.ad.id,
                ad_group_ad.ad.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                segments.device,
                segments.keyword_info.text,
                segments.ad_destination_type
            FROM ad_group_ad
            WHERE segments.date BETWEEN '{start.strftime('%Y-%m-%d')}'
                                   AND '{end.strftime('%Y-%m-%d')}'
            ORDER BY segments.date ASC
        """
    
    def _normalize_row(self, row: Dict) -> UnifiedTouchpoint:
        segments = row.get("segments", {})
        campaign = row.get("campaign", {})
        ad_group = row.get("ad_group", {})
        ad = row.get("ad_group_ad", {}).get("ad", {})
        metrics = row.get("metrics", {})
        
        return UnifiedTouchpoint(
            touchpoint_id=f"ga_{campaign.get('id')}_{ad_group.get('id')}_{ad.get('id')}_{segments.get('date')}",
            user_id="anonymous",  # Google Ads doesn't provide user-level data without enhanced conversions
            timestamp=datetime.strptime(segments["date"], "%Y-%m-%d"),
            channel=ChannelType.PAID_SEARCH,
            touchpoint_type=TouchpointType.CLICK if int(metrics.get("clicks", 0)) > 0 else TouchpointType.IMPRESSION,
            source_platform="google_ads",
            source_campaign_id=str(campaign.get("id")),
            source_ad_group_id=str(ad_group.get("id")),
            source_ad_id=str(ad.get("id")),
            campaign_name=campaign.get("name"),
            ad_group_name=ad_group.get("name"),
            ad_name=ad.get("name"),
            keyword=segments.get("keyword_info", {}).get("text"),
            device_type=segments.get("device", "").lower(),
            cost=int(metrics.get("cost_micros", 0)) / 1_000_000,
            conversion_value=float(metrics.get("conversions_value", 0)),
            metadata={
                "impressions": int(metrics.get("impressions", 0)),
                "clicks": int(metrics.get("clicks", 0)),
                "conversions": float(metrics.get("conversions", 0)),
            },
        )
    
    async def health_check(self) -> Dict[str, Any]:
        try:
            url = f"{self.BASE_URL}/{self.credentials['customer_id']}/googleAds:search"
            payload = {"query": "SELECT campaign.id FROM campaign LIMIT 1"}
            async with self._session.post(url, json=payload) as resp:
                return {"healthy": resp.status == 200, "status": resp.status}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def get_metadata(self) -> Dict[str, Any]:
        # Fetch campaign list, ad groups, etc.
        pass


class MetaAdsConnector(BaseSourceConnector):
    """Meta (Facebook/Instagram) Ads API connector."""
    
    BASE_URL = "https://graph.facebook.com/v19.0"
    
    def _get_auth_headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}
    
    async def fetch_touchpoints(
        self,
        start_date: datetime,
        end_date: datetime,
        cursor: Optional[str] = None,
    ) -> AsyncIterator[UnifiedTouchpoint]:
        ad_account_id = self.credentials["ad_account_id"]
        url = f"{self.BASE_URL}/act_{ad_account_id}/insights"
        
        params = {
            "access_token": self.credentials["access_token"],
            "fields": "campaign_name,adset_name,ad_name,impressions,clicks,spend,actions,action_values,platform,device",
            "time_range": json.dumps({
                "since": start_date.strftime("%Y-%m-%d"),
                "until": end_date.strftime("%Y-%m-%d"),
            }),
            "time_increment": 1,  # Daily breakdown
            "limit": 500,
        }
        if cursor:
            params["after"] = cursor
        
        async with self.rate_limiter:
            async with self._session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
        
        for row in data.get("data", []):
            yield self._normalize_row(row)
        
        paging = data.get("paging", {})
        if paging.get("cursors", {}).get("after"):
            async for tp in self.fetch_touchpoints(
                start_date, end_date, paging["cursors"]["after"]
            ):
                yield tp
    
    def _normalize_row(self, row: Dict) -> UnifiedTouchpoint:
        actions = {a["action_type"]: a for a in row.get("actions", [])}
        action_values = {a["action_type"]: a for a in row.get("action_values", [])}
        
        conversions = int(actions.get("purchase", {}).get("value", 0))
        conversion_value = float(action_values.get("purchase", {}).get("value", 0))
        
        return UnifiedTouchpoint(
            touchpoint_id=f"meta_{row.get('campaign_name', '')}_{row.get('adset_name', '')}_{row.get('date_start', '')}",
            user_id="anonymous",
            timestamp=datetime.strptime(row["date_start"], "%Y-%m-%d"),
            channel=ChannelType.PAID_SOCIAL,
            touchpoint_type=TouchpointType.CONVERSION if conversions > 0 else TouchpointType.IMPRESSION,
            source_platform="meta_ads",
            campaign_name=row.get("campaign_name"),
            ad_group_name=row.get("adset_name"),
            ad_name=row.get("ad_name"),
            device_type=row.get("device", "").lower(),
            cost=float(row.get("spend", 0)),
            conversion_value=conversion_value,
            metadata={
                "impressions": int(row.get("impressions", 0)),
                "clicks": int(row.get("clicks", 0)),
                "conversions": conversions,
                "platform": row.get("platform"),
            },
        )
    
    async def health_check(self) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/me"
        params = {"access_token": self.credentials["access_token"]}
        async with self._session.get(url, params=params) as resp:
            return {"healthy": resp.status == 200, "status": resp.status}
    
    async def get_metadata(self) -> Dict[str, Any]:
        pass


class SalesforceCRMConnector(BaseSourceConnector):
    """Salesforce CRM connector for opportunity and lead data."""
    
    def _get_auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.credentials['access_token']}",
            "Content-Type": "application/json",
        }
    
    async def fetch_touchpoints(
        self,
        start_date: datetime,
        end_date: datetime,
        cursor: Optional[str] = None,
    ) -> AsyncIterator[UnifiedTouchpoint]:
        url = f"{self.credentials['instance_url']}/services/data/v59.0/query"
        
        query = f"""
            SELECT Id, ContactId, AccountId, Name, StageName, Amount,
                   CloseDate, LeadSource, CreatedDate, LastModifiedDate,
                   (SELECT Id, Subject, ActivityDate, Type FROM Tasks),
                   (SELECT Id, Subject, ActivityDate FROM Events)
            FROM Opportunity
            WHERE CloseDate >= {start_date.strftime('%Y-%m-%d')}
              AND CloseDate <= {end_date.strftime('%Y-%m-%d')}
        """
        
        params = {"q": query}
        if cursor:
            params["q"] += f" AND Id > '{cursor}'"
        
        async with self.rate_limiter:
            async with self._session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
        
        for record in data.get("records", []):
            yield self._normalize_row(record)
        
        if not data.get("done", True):
            async for tp in self.fetch_touchpoints(
                start_date, end_date, data["records"][-1]["Id"]
            ):
                yield tp
    
    def _normalize_row(self, record: Dict) -> UnifiedTouchpoint:
        return UnifiedTouchpoint(
            touchpoint_id=f"sf_opp_{record['Id']}",
            user_id=record.get("ContactId", "unknown"),
            timestamp=datetime.fromisoformat(record["CloseDate"]),
            channel=ChannelType.DIRECT,  # Will be enriched with lead source
            touchpoint_type=TouchpointType.SALE if record.get("StageName") == "Closed Won" else TouchpointType.OPPORTUNITY,
            source_platform="salesforce",
            campaign_name=record.get("LeadSource"),
            revenue=float(record.get("Amount", 0)),
            conversion_value=float(record.get("Amount", 0)),
            metadata={
                "opportunity_name": record.get("Name"),
                "stage": record.get("StageName"),
                "account_id": record.get("AccountId"),
                "lead_source": record.get("LeadSource"),
            },
        )
    
    async def health_check(self) -> Dict[str, Any]:
        url = f"{self.credentials['instance_url']}/services/data/v59.0/limits"
        async with self._session.get(url) as resp:
            return {"healthy": resp.status == 200, "status": resp.status}
    
    async def get_metadata(self) -> Dict[str, Any]:
        pass
```

### 2.4 Data Collection Agent

```python
from langchain_deepagents import DeepAgent
from langchain_deepagents.planner import PlannerConfig
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

class DataCollectionAgent:
    """Agent responsible for collecting and normalizing marketing touchpoint data."""
    
    def __init__(self, connectors: Dict[str, BaseSourceConnector], config: Dict[str, Any] = None):
        self.connectors = connectors
        self.config = config or {}
        self.normalization_pipeline = NormalizationPipeline()
        self.quality_checker = DataQualityChecker()
    
    async def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        channels: Optional[List[ChannelType]] = None,
        platforms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Collect touchpoints from all configured sources.
        
        Returns a collection result with normalized touchpoints and quality metrics.
        """
        channels = channels or list(ChannelType)
        platforms = platforms or list(self.connectors.keys())
        
        all_touchpoints: List[UnifiedTouchpoint] = []
        source_results: Dict[str, Dict] = {}
        errors: List[Dict] = []
        
        # Collect from all sources concurrently
        tasks = []
        for platform in platforms:
            if platform not in self.connectors:
                errors.append({"source": platform, "error": "Connector not configured"})
                continue
            
            connector = self.connectors[platform]
            task = self._collect_from_source(
                connector, start_date, end_date, channels
            )
            tasks.append((platform, task))
        
        for platform, task in tasks:
            try:
                touchpoints, metadata = await task
                all_touchpoints.extend(touchpoints)
                source_results[platform] = {
                    "status": "success",
                    "count": len(touchpoints),
                    "metadata": metadata,
                }
            except Exception as e:
                logger.error(f"Failed to collect from {platform}: {e}")
                errors.append({"source": platform, "error": str(e)})
                source_results[platform] = {"status": "failed", "error": str(e)}
        
        # Normalize and deduplicate
        normalized = self.normalization_pipeline.process(all_touchpoints)
        
        # Quality check
        quality_report = self.quality_checker.check(normalized)
        
        return {
            "touchpoints": [tp.dict() for tp in normalized],
            "total_raw": len(all_touchpoints),
            "total_normalized": len(normalized),
            "source_results": source_results,
            "quality_report": quality_report,
            "errors": errors,
            "collection_time": datetime.utcnow().isoformat(),
        }
    
    async def _collect_from_source(
        self,
        connector: BaseSourceConnector,
        start_date: datetime,
        end_date: datetime,
        channels: List[ChannelType],
    ) -> tuple[List[UnifiedTouchpoint], Dict[str, Any]]:
        """Collect touchpoints from a single source."""
        touchpoints = []
        metadata = {}
        
        async with connector:
            # Health check first
            health = await connector.health_check()
            if not health.get("healthy"):
                raise ConnectionError(f"Source unhealthy: {health}")
            
            # Fetch metadata
            metadata = await connector.get_metadata()
            
            # Fetch touchpoints
            async for tp in connector.fetch_touchpoints(start_date, end_date):
                if tp.channel in channels:
                    touchpoints.append(tp)
        
        return touchpoints, metadata


class NormalizationPipeline:
    """Pipeline for normalizing and deduplicating touchpoints."""
    
    def __init__(self):
        self.schema_mapper = SchemaMapper()
        self.identity_resolver = IdentityResolver()
        self.deduplicator = TouchpointDeduplicator()
    
    def process(self, touchpoints: List[UnifiedTouchpoint]) -> List[UnifiedTouchpoint]:
        # Step 1: Schema mapping (already done by connectors, but validate)
        validated = [self.schema_mapper.validate(tp) for tp in touchpoints]
        
        # Step 2: Identity resolution
        resolved = self.identity_resolver.resolve(validated)
        
        # Step 3: Deduplication
        deduplicated = self.deduplicator.deduplicate(resolved)
        
        # Step 4: Enrichment
        enriched = self._enrich(deduplicated)
        
        return enriched
    
    def _enrich(self, touchpoints: List[UnifiedTouchpoint]) -> List[UnifiedTouchpoint]:
        """Enrich touchpoints with additional context."""
        for tp in touchpoints:
            # Add channel hierarchy
            tp.metadata["channel_category"] = self._categorize_channel(tp.channel)
            # Add time-based features
            tp.metadata["hour_of_day"] = tp.timestamp.hour
            tp.metadata["day_of_week"] = tp.timestamp.weekday()
            tp.metadata["is_weekend"] = tp.timestamp.weekday() >= 5
        return touchpoints
    
    def _categorize_channel(self, channel: ChannelType) -> str:
        mapping = {
            ChannelType.PAID_SEARCH: "paid",
            ChannelType.PAID_SOCIAL: "paid",
            ChannelType.DISPLAY: "paid",
            ChannelType.VIDEO: "paid",
            ChannelType.EMAIL: "owned",
            ChannelType.ORGANIC_SEARCH: "organic",
            ChannelType.ORGANIC_SOCIAL: "organic",
            ChannelType.DIRECT: "direct",
            ChannelType.REFERRAL: "referral",
        }
        return mapping.get(channel, "other")


class DataQualityChecker:
    """Validates data quality of collected touchpoints."""
    
    def check(self, touchpoints: List[UnifiedTouchpoint]) -> Dict[str, Any]:
        total = len(touchpoints)
        if total == 0:
            return {"status": "empty", "total": 0}
        
        issues = []
        
        # Check for missing user IDs
        missing_user_id = sum(1 for tp in touchpoints if not tp.user_id or tp.user_id == "anonymous")
        if missing_user_id > 0:
            issues.append({
                "type": "missing_user_id",
                "count": missing_user_id,
                "percentage": missing_user_id / total * 100,
            })
        
        # Check for negative costs
        negative_costs = sum(1 for tp in touchpoints if tp.cost < 0)
        if negative_costs > 0:
            issues.append({
                "type": "negative_cost",
                "count": negative_costs,
                "percentage": negative_costs / total * 100,
            })
        
        # Check for future dates
        now = datetime.utcnow()
        future_dates = sum(1 for tp in touchpoints if tp.timestamp > now)
        if future_dates > 0:
            issues.append({
                "type": "future_date",
                "count": future_dates,
                "percentage": future_dates / total * 100,
            })
        
        # Check for duplicate IDs
        ids = [tp.touchpoint_id for tp in touchpoints]
        duplicate_count = len(ids) - len(set(ids))
        if duplicate_count > 0:
            issues.append({
                "type": "duplicate_id",
                "count": duplicate_count,
                "percentage": duplicate_count / total * 100,
            })
        
        # Overall quality score
        quality_score = max(0, 1.0 - sum(i["percentage"] for i in issues) / 100)
        
        return {
            "status": "pass" if quality_score >= 0.95 else "warning" if quality_score >= 0.8 else "fail",
            "total": total,
            "quality_score": quality_score,
            "issues": issues,
        }
```

### 2.5 Rate Limiting and Retry Logic

```python
import asyncio
import time
from typing import Optional
from functools import wraps

class AsyncRateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, calls_per_second: float = 10.0, burst_size: int = 5):
        self.calls_per_second = calls_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.calls_per_second
            )
            self.last_refill = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.calls_per_second
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def with_retry(max_retries: int = 3, backoff_factor: float = 2.0, 
               retryable_exceptions: tuple = (Exception,)):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait = backoff_factor ** attempt
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. Retrying in {wait}s..."
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed: {e}")
            raise last_exception
        return wrapper
    return decorator
```

---

## 3. Attribution Engine

### 3.1 Architecture Overview

The attribution engine computes multi-touch attribution using three complementary models: Markov chains, Shapley values, and deep learning. Each model provides a different perspective on channel contribution, and the engine combines them into a unified attribution score.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ATTRIBUTION ENGINE                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              TOUCHPOINT SEQUENCE BUILDER                  │   │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────────────────────┐ │   │
│  │  │ Journey │  │ Session  │  │  Path Construction      │ │   │
│  │  │ Builder │  │ Window   │  │  (ordered touchpoints)  │ │   │
│  │  └─────────┘  └──────────┘  └─────────────────────────┘ │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐               │
│         │                   │                   │               │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐        │
│  │   MARKOV    │    │  SHAPLEY    │    │    DEEP     │        │
│  │   CHAIN     │    │  VALUE      │    │  LEARNING   │        │
│  │  MODEL      │    │  MODEL      │    │   MODEL     │        │
│  │             │    │             │    │  (LSTM/     │        │
│  │ Removal     │    │ Cooperative │    │  Transformer)│        │
│  │ Effect      │    │ Game Theory │    │             │        │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘        │
│         │                   │                   │               │
│  ┌──────▼───────────────────▼───────────────────▼──────┐        │
│  │              ENSEMBLE AGGREGATOR                     │        │
│  │  Weighted combination + confidence scoring           │        │
│  └──────────────────────┬──────────────────────────────┘        │
│                         │                                        │
│  ┌──────────────────────▼──────────────────────────────┐        │
│  │           UNIFIED ATTRIBUTION RESULT                 │        │
│  │  Channel-level + Campaign-level + Touchpoint-level   │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Journey Builder

```python
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np

@dataclass
class CustomerJourney:
    """Represents a single customer's path to conversion."""
    journey_id: str
    user_id: str
    touchpoints: List[UnifiedTouchpoint] = field(default_factory=list)
    converted: bool = False
    conversion_value: float = 0.0
    conversion_timestamp: Optional[datetime] = None
    
    @property
    def path(self) -> List[str]:
        """Return the ordered list of channels in the journey."""
        return [tp.channel.value for tp in self.touchpoints]
    
    @property
    def path_string(self) -> str:
        """Return the path as a string for Markov chain analysis."""
        return " > ".join(self.path)
    
    @property
    def total_cost(self) -> float:
        return sum(tp.cost for tp in self.touchpoints)
    
    @property
    def length(self) -> int:
        return len(self.touchpoints)


class JourneyBuilder:
    """Builds customer journeys from raw touchpoints."""
    
    def __init__(
        self,
        session_window_minutes: int = 30,
        max_journey_days: int = 90,
        conversion_window_days: int = 30,
    ):
        self.session_window = timedelta(minutes=session_window_minutes)
        self.max_journey_duration = timedelta(days=max_journey_days)
        self.conversion_window = timedelta(days=conversion_window_days)
    
    def build_journeys(
        self,
        touchpoints: List[UnifiedTouchpoint],
    ) -> List[CustomerJourney]:
        """
        Build customer journeys from a flat list of touchpoints.
        
        Algorithm:
        1. Group touchpoints by user_id
        2. Sort each user's touchpoints by timestamp
        3. Split into sessions based on inactivity window
        4. Identify conversion events
        5. Build journeys ending at conversions
        """
        # Group by user
        user_touchpoints: Dict[str, List[UnifiedTouchpoint]] = defaultdict(list)
        for tp in touchpoints:
            user_touchpoints[tp.user_id].append(tp)
        
        journeys = []
        for user_id, user_tps in user_touchpoints.items():
            # Sort by timestamp
            user_tps.sort(key=lambda x: x.timestamp)
            
            # Split into sessions
            sessions = self._split_into_sessions(user_tps)
            
            # Build journeys from sessions
            for session in sessions:
                journey = self._build_journey_from_session(user_id, session)
                if journey:
                    journeys.append(journey)
        
        return journeys
    
    def _split_into_sessions(
        self,
        touchpoints: List[UnifiedTouchpoint],
    ) -> List[List[UnifiedTouchpoint]]:
        """Split touchpoints into sessions based on inactivity window."""
        if not touchpoints:
            return []
        
        sessions = []
        current_session = [touchpoints[0]]
        
        for i in range(1, len(touchpoints)):
            time_diff = touchpoints[i].timestamp - touchpoints[i-1].timestamp
            
            if time_diff > self.session_window:
                sessions.append(current_session)
                current_session = [touchpoints[i]]
            else:
                current_session.append(touchpoints[i])
        
        if current_session:
            sessions.append(current_session)
        
        return sessions
    
    def _build_journey_from_session(
        self,
        user_id: str,
        session: List[UnifiedTouchpoint],
    ) -> Optional[CustomerJourney]:
        """Build a customer journey from a session of touchpoints."""
        if not session:
            return None
        
        # Check for conversion in the session
        conversion_tp = None
        for tp in session:
            if tp.touchpoint_type in (TouchpointType.CONVERSION, TouchpointType.SALE):
                conversion_tp = tp
                break
        
        # Also check for conversions within the conversion window after the session
        if not conversion_tp:
            session_end = session[-1].timestamp
            # This would need access to future touchpoints - simplified here
            pass
        
        journey = CustomerJourney(
            journey_id=f"{user_id}_{session[0].timestamp.isoformat()}",
            user_id=user_id,
            touchpoints=session,
            converted=conversion_tp is not None,
            conversion_value=conversion_tp.conversion_value if conversion_tp else 0.0,
            conversion_timestamp=conversion_tp.timestamp if conversion_tp else None,
        )
        
        return journey
```

### 3.3 Markov Chain Attribution Model

```python
import numpy as np
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict
from scipy.linalg import expm
import logging

logger = logging.getLogger(__name__)

class MarkovChainAttribution:
    """
    Markov Chain-based multi-touch attribution model.
    
    Models the customer journey as a Markov chain where states are channels
    and transitions represent the probability of moving from one channel to another.
    The removal effect measures how much conversions decrease when a channel is removed.
    """
    
    def __init__(self, order: int = 1, smoothing: float = 0.01):
        """
        Args:
            order: Markov chain order (1 = first-order, 2 = second-order)
            smoothing: Laplace smoothing parameter for transition probabilities
        """
        self.order = order
        self.smoothing = smoothing
        self.transition_matrix: Optional[np.ndarray] = None
        self.states: List[str] = []
        self.state_to_idx: Dict[str, int] = {}
        self.removal_effects: Dict[str, float] = {}
        self.conversion_rates: Dict[str, float] = {}
    
    def fit(self, journeys: List[CustomerJourney]) -> "MarkovChainAttribution":
        """Fit the Markov chain model on customer journeys."""
        # Build state space
        self.states = self._build_state_space(journeys)
        self.state_to_idx = {s: i for i, s in enumerate(self.states)}
        n_states = len(self.states)
        
        # Build transition counts
        transition_counts = np.full((n_states, n_states), self.smoothing)
        
        for journey in journeys:
            path = self._journey_to_path(journey)
            for i in range(len(path) - 1):
                from_state = path[i]
                to_state = path[i + 1]
                if from_state in self.state_to_idx and to_state in self.state_to_idx:
                    transition_counts[
                        self.state_to_idx[from_state],
                        self.state_to_idx[to_state]
                    ] += 1
        
        # Normalize to get transition probabilities
        row_sums = transition_counts.sum(axis=1, keepdims=True)
        self.transition_matrix = transition_counts / row_sums
        
        # Calculate removal effects
        self._calculate_removal_effects(journeys)
        
        # Calculate conversion rates per state
        self._calculate_conversion_rates(journeys)
        
        return self
    
    def _build_state_space(self, journeys: List[CustomerJourney]) -> List[str]:
        """Build the state space including special states."""
        channels: Set[str] = set()
        for journey in journeys:
            for tp in journey.touchpoints:
                channels.add(tp.channel.value)
        
        # Add special states: START, CONVERSION, NULL (no conversion)
        states = ["START"] + sorted(channels) + ["CONVERSION", "NULL"]
        return states
    
    def _journey_to_path(self, journey: CustomerJourney) -> List[str]:
        """Convert a journey to a path of states."""
        path = ["START"]
        for tp in journey.touchpoints:
            path.append(tp.channel.value)
        path.append("CONVERSION" if journey.converted else "NULL")
        return path
    
    def _calculate_removal_effects(self, journeys: List[CustomerJourney]) -> None:
        """
        Calculate the removal effect for each channel.
        
        The removal effect is the decrease in conversion probability when
        a channel is removed from the Markov chain.
        """
        if self.transition_matrix is None:
            raise ValueError("Model must be fitted first")
        
        # Baseline conversion probability
        baseline_conversion_prob = self._simulate_conversion_probability(
            self.transition_matrix
        )
        
        for state in self.states:
            if state in ("START", "CONVERSION", "NULL"):
                continue
            
            # Create modified transition matrix with state removed
            modified_matrix = self._remove_state(state)
            
            # Calculate conversion probability without this state
            modified_conversion_prob = self._simulate_conversion_probability(
                modified_matrix
            )
            
            # Removal effect = (baseline - modified) / baseline
            if baseline_conversion_prob > 0:
                removal_effect = (
                    (baseline_conversion_prob - modified_conversion_prob)
                    / baseline_conversion_prob
                )
            else:
                removal_effect = 0.0
            
            self.removal_effects[state] = max(0.0, removal_effect)
    
    def _remove_state(self, state: str) -> np.ndarray:
        """Create a transition matrix with the given state removed."""
        if state not in self.state_to_idx:
            return self.transition_matrix.copy()
        
        idx = self.state_to_idx[state]
        n = len(self.states)
        
        # Create new matrix without the state
        new_states = [s for s in self.states if s != state]
        new_n = len(new_states)
        new_matrix = np.full((new_n, new_n), self.smoothing)
        
        old_to_new = {}
        new_idx = 0
        for i, s in enumerate(self.states):
            if s != state:
                old_to_new[i] = new_idx
                new_idx += 1
        
        for i in range(n):
            if i == idx:
                continue
            for j in range(n):
                if j == idx:
                    continue
                new_matrix[old_to_new[i], old_to_new[j]] += self.transition_matrix[i, j]
        
        # Normalize
        row_sums = new_matrix.sum(axis=1, keepdims=True)
        new_matrix = new_matrix / row_sums
        
        return new_matrix
    
    def _simulate_conversion_probability(
        self,
        transition_matrix: np.ndarray,
        max_steps: int = 100,
    ) -> float:
        """
        Simulate the probability of reaching the CONVERSION state
        from the START state using the transition matrix.
        """
        n = transition_matrix.shape[0]
        
        # Find START and CONVERSION indices
        start_idx = self.state_to_idx.get("START", 0)
        conversion_idx = self.state_to_idx.get("CONVERSION", n - 2)
        null_idx = self.state_to_idx.get("NULL", n - 1)
        
        # Use absorbing Markov chain analysis
        # Q = transient-to-transient transitions
        # R = transient-to-absorbing transitions
        absorbing = [conversion_idx, null_idx]
        transient = [i for i in range(n) if i not in absorbing]
        
        if not transient:
            return 0.0
        
        Q = transition_matrix[np.ix_(transient, transient)]
        R = transition_matrix[np.ix_(transient, absorbing)]
        
        # Fundamental matrix: N = (I - Q)^(-1)
        try:
            I = np.eye(len(transient))
            N = np.linalg.inv(I - Q)
        except np.linalg.LinAlgError:
            return 0.0
        
        # Absorption probabilities: B = N * R
        B = N @ R
        
        # Probability of absorption in CONVERSION state from START
        if start_idx in transient:
            start_transient_idx = transient.index(start_idx)
            conversion_absorbing_idx = absorbing.index(conversion_idx)
            return B[start_transient_idx, conversion_absorbing_idx]
        
        return 0.0
    
    def _calculate_conversion_rates(self, journeys: List[CustomerJourney]) -> None:
        """Calculate conversion rate for each channel."""
        channel_conversions: Dict[str, int] = defaultdict(int)
        channel_touchpoints: Dict[str, int] = defaultdict(int)
        
        for journey in journeys:
            for tp in journey.touchpoints:
                channel_touchpoints[tp.channel.value] += 1
                if journey.converted:
                    channel_conversions[tp.channel.value] += 1
        
        for channel in channel_touchpoints:
            if channel_touchpoints[channel] > 0:
                self.conversion_rates[channel] = (
                    channel_conversions[channel] / channel_touchpoints[channel]
                )
    
    def get_attribution(self) -> Dict[str, Dict[str, float]]:
        """
        Get attribution results for all channels.
        
        Returns a dictionary with channel names as keys and attribution
        metrics as values.
        """
        total_removal = sum(self.removal_effects.values())
        
        results = {}
        for channel, removal_effect in self.removal_effects.items():
            # Normalize removal effects to sum to 1
            normalized_attribution = (
                removal_effect / total_removal if total_removal > 0 else 0.0
            )
            
            results[channel] = {
                "removal_effect": removal_effect,
                "attribution_weight": normalized_attribution,
                "conversion_rate": self.conversion_rates.get(channel, 0.0),
            }
        
        return results
    
    def get_channel_attribution(self) -> Dict[str, float]:
        """Get simple channel attribution weights (sum to 1)."""
        total = sum(self.removal_effects.values())
        if total == 0:
            return {ch: 0.0 for ch in self.removal_effects}
        return {
            ch: effect / total
            for ch, effect in self.removal_effects.items()
        }
```

### 3.4 Shapley Value Attribution Model

```python
import numpy as np
from typing import List, Dict, Tuple, Set, Optional
from itertools import combinations
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class ShapleyAttribution:
    """
    Shapley Value-based multi-touch attribution model.
    
    Uses cooperative game theory to fairly distribute conversion credit
    across channels. Each channel is a "player" in a cooperative game,
    and the Shapley value represents the marginal contribution of each channel.
    
    For large numbers of channels, uses sampling-based approximation.
    """
    
    def __init__(self, max_exact_channels: int = 10, n_samples: int = 10000, 
                 random_seed: int = 42):
        """
        Args:
            max_exact_channels: Maximum number of channels for exact computation
            n_samples: Number of samples for approximate computation
            random_seed: Random seed for reproducibility
        """
        self.max_exact_channels = max_exact_channels
        self.n_samples = n_samples
        self.random_seed = random_seed
        self.shapley_values: Dict[str, float] = {}
        self.channel_contributions: Dict[str, List[float]] = {}
        self._rng = np.random.RandomState(random_seed)
    
    def fit(self, journeys: List[CustomerJourney]) -> "ShapleyAttribution":
        """Compute Shapley values for all channels."""
        # Extract unique channels
        channels = self._extract_channels(journeys)
        
        if len(channels) <= self.max_exact_channels:
            self._compute_exact_shapley(journeys, channels)
        else:
            self._compute_approximate_shapley(journeys, channels)
        
        return self
    
    def _extract_channels(self, journeys: List[CustomerJourney]) -> List[str]:
        """Extract unique channels from journeys."""
        channels: Set[str] = set()
        for journey in journeys:
            for tp in journey.touchpoints:
                channels.add(tp.channel.value)
        return sorted(channels)
    
    def _compute_exact_shapley(
        self,
        journeys: List[CustomerJourney],
        channels: List[str],
    ) -> None:
        """Compute exact Shapley values using all permutations."""
        n = len(channels)
        self.shapley_values = {ch: 0.0 for ch in channels}
        self.channel_contributions = {ch: [] for ch in channels}
        
        # Generate all permutations
        from itertools import permutations
        all_perms = list(permutations(channels))
        n_perms = len(all_perms)
        
        for perm in all_perms:
            # Calculate marginal contribution for each channel in this permutation
            current_value = 0.0
            current_set: Set[str] = set()
            
            for i, channel in enumerate(perm):
                # Value with this channel added
                new_set = current_set | {channel}
                new_value = self._characteristic_function(new_set, journeys)
                
                # Marginal contribution
                marginal = new_value - current_value
                self.shapley_values[channel] += marginal
                self.channel_contributions[channel].append(marginal)
                
                current_set = new_set
                current_value = new_value
        
        # Average over all permutations
        for channel in channels:
            self.shapley_values[channel] /= n_perms
    
    def _compute_approximate_shapley(
        self,
        journeys: List[CustomerJourney],
        channels: List[str],
    ) -> None:
        """Compute approximate Shapley values using random sampling."""
        n = len(channels)
        self.shapley_values = {ch: 0.0 for ch in channels}
        self.channel_contributions = {ch: [] for ch in channels}
        
        for _ in range(self.n_samples):
            # Random permutation
            perm = self._rng.permutation(channels).tolist()
            
            current_value = 0.0
            current_set: Set[str] = set()
            
            for channel in perm:
                new_set = current_set | {channel}
                new_value = self._characteristic_function(new_set, journeys)
                
                marginal = new_value - current_value
                self.shapley_values[channel] += marginal
                self.channel_contributions[channel].append(marginal)
                
                current_set = new_set
                current_value = new_value
        
        # Average over samples
        for channel in channels:
            self.shapley_values[channel] /= self.n_samples
    
    def _characteristic_function(
        self,
        channel_set: Set[str],
        journeys: List[CustomerJourney],
    ) -> float:
        """
        Characteristic function v(S) for a set of channels S.
        
        Returns the total conversion value attributed to journeys
        that only use channels in S.
        """
        total_value = 0.0
        
        for journey in journeys:
            journey_channels = {tp.channel.value for tp in journey.touchpoints}
            
            # Journey is "covered" by channel_set if all its channels are in the set
            if journey_channels.issubset(channel_set) and journey.converted:
                total_value += journey.conversion_value
        
        return total_value
    
    def get_attribution(self) -> Dict[str, Dict[str, float]]:
        """Get Shapley attribution results."""
        total_value = sum(self.shapley_values.values())
        
        results = {}
        for channel, shapley_value in self.shapley_values.items():
            contributions = self.channel_contributions.get(channel, [0.0])
            results[channel] = {
                "shapley_value": shapley_value,
                "attribution_weight": shapley_value / total_value if total_value > 0 else 0.0,
                "contribution_std": np.std(contributions) if contributions else 0.0,
                "contribution_mean": np.mean(contributions) if contributions else 0.0,
            }
        
        return results
    
    def get_channel_attribution(self) -> Dict[str, float]:
        """Get simple channel attribution weights (sum to 1)."""
        total = sum(self.shapley_values.values())
        if total == 0:
            return {ch: 0.0 for ch in self.shapley_values}
        return {
            ch: value / total
            for ch, value in self.shapley_values.items()
        }
```

### 3.5 Deep Learning Attribution Model

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Tuple, Optional
import numpy as np
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class TouchpointSequenceDataset(Dataset):
    """PyTorch Dataset for touchpoint sequences."""
    
    def __init__(
        self,
        journeys: List[CustomerJourney],
        channel_to_idx: Dict[str, int],
        max_sequence_length: int = 50,
    ):
        self.journeys = journeys
        self.channel_to_idx = channel_to_idx
        self.max_sequence_length = max_sequence_length
        self.n_channels = len(channel_to_idx)
    
    def __len__(self) -> int:
        return len(self.journeys)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, float, float]:
        journey = self.journeys[idx]
        
        # Encode channel sequence
        channel_indices = [
            self.channel_to_idx.get(tp.channel.value, 0)
            for tp in journey.touchpoints
        ]
        
        # Pad or truncate
        seq_length = len(channel_indices)
        if seq_length > self.max_sequence_length:
            channel_indices = channel_indices[:self.max_sequence_length]
            seq_length = self.max_sequence_length
        else:
            channel_indices = channel_indices + [0] * (self.max_sequence_length - seq_length)
        
        # Create channel mask (1 for real touchpoints, 0 for padding)
        mask = [1] * seq_length + [0] * (self.max_sequence_length - seq_length)
        
        # Target: conversion (1.0) or no conversion (0.0)
        target = 1.0 if journey.converted else 0.0
        
        # Conversion value
        value = journey.conversion_value
        
        return (
            torch.tensor(channel_indices, dtype=torch.long),
            torch.tensor(mask, dtype=torch.float),
            torch.tensor(target, dtype=torch.float),
            torch.tensor(value, dtype=torch.float),
        )


class DeepAttributionModel(nn.Module):
    """
    Deep learning model for multi-touch attribution.
    
    Uses a combination of:
    - Embedding layer for channel representations
    - Bidirectional LSTM for sequence modeling
    - Attention mechanism for touchpoint importance
    - Output heads for conversion prediction and attribution
    """
    
    def __init__(
        self,
        n_channels: int,
        embedding_dim: int = 64,
        hidden_dim: int = 128,
        n_lstm_layers: int = 2,
        dropout: float = 0.3,
        max_sequence_length: int = 50,
    ):
        super().__init__()
        
        self.n_channels = n_channels
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.max_sequence_length = max_sequence_length
        
        # Channel embedding
        self.channel_embedding = nn.Embedding(
            n_channels + 1, embedding_dim, padding_idx=0
        )
        
        # Positional encoding
        self.position_embedding = nn.Embedding(
            max_sequence_length, embedding_dim
        )
        
        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=n_lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if n_lstm_layers > 1 else 0,
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim * 2,  # bidirectional
            num_heads=4,
            dropout=dropout,
            batch_first=True,
        )
        
        # Conversion prediction head
        self.conversion_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )
        
        # Attribution head (produces per-touchpoint attribution scores)
        self.attribution_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )
    
    def forward(
        self,
        channel_indices: torch.Tensor,
        mask: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            channel_indices: (batch_size, seq_length) channel indices
            mask: (batch_size, seq_length) padding mask
        
        Returns:
            conversion_prob: (batch_size,) conversion probability
            attribution_scores: (batch_size, seq_length) per-touchpoint attribution
            attention_weights: (batch_size, seq_length) attention weights
        """
        batch_size, seq_length = channel_indices.shape
        
        # Embed channels
        channel_embeds = self.channel_embedding(channel_indices)  # (B, L, E)
        
        # Add positional encoding
        positions = torch.arange(seq_length, device=channel_indices.device)
        position_embeds = self.position_embedding(positions).unsqueeze(0)  # (1, L, E)
        embeds = channel_embeds + position_embeds
        
        # LSTM encoding
        lstm_out, _ = self.lstm(embeds)  # (B, L, 2*H)
        
        # Self-attention
        attn_out, attn_weights = self.attention(
            lstm_out, lstm_out, lstm_out,
            key_padding_mask=(mask == 0),
        )  # (B, L, 2*H), (B, L, L)
        
        # Conversion prediction (use attention-weighted sum)
        mask_expanded = mask.unsqueeze(-1)  # (B, L, 1)
        weighted_sum = (attn_out * mask_expanded).sum(dim=1)  # (B, 2*H)
        conversion_prob = self.conversion_head(weighted_sum).squeeze(-1)  # (B,)
        
        # Attribution scores (per touchpoint)
        attribution_scores = self.attribution_head(attn_out).squeeze(-1)  # (B, L)
        attribution_scores = attribution_scores * mask  # Zero out padding
        
        # Normalize attribution scores to sum to 1 per journey
        score_sums = attribution_scores.sum(dim=1, keepdim=True)
        attribution_scores = attribution_scores / (score_sums + 1e-8)
        
        # Average attention weights across heads
        attention_weights = attn_weights.mean(dim=1)  # (B, L, L)
        
        return conversion_prob, attribution_scores, attention_weights


class DeepAttributionTrainer:
    """Trainer for the deep attribution model."""
    
    def __init__(
        self,
        model: DeepAttributionModel,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-5,
        device: str = "auto",
    ):
        self.model = model
        self.device = self._get_device(device)
        self.model.to(self.device)
        
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
        )
        
        self.conversion_criterion = nn.BCELoss()
        self.attribution_criterion = nn.MSELoss()
        
        self.history: Dict[str, List[float]] = {
            "train_loss": [],
            "val_loss": [],
            "train_auc": [],
            "val_auc": [],
        }
    
    def _get_device(self, device: str) -> torch.device:
        if device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(device)
    
    def train(
        self,
        train_dataset: TouchpointSequenceDataset,
        val_dataset: Optional[TouchpointSequenceDataset] = None,
        epochs: int = 50,
        batch_size: int = 64,
        patience: int = 10,
    ) -> Dict[str, List[float]]:
        """Train the model with early stopping."""
        train_loader = DataLoader(
            train_dataset, batch_size=batch_size, shuffle=True
        )
        val_loader = DataLoader(
            val_dataset, batch_size=batch_size
        ) if val_dataset else None
        
        best_val_loss = float("inf")
        patience_counter = 0
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0.0
            n_batches = 0
            
            for batch in train_loader:
                channel_indices, mask, targets, values = batch
                channel_indices = channel_indices.to(self.device)
                mask = mask.to(self.device)
                targets = targets.to(self.device)
                values = values.to(self.device)
                
                self.optimizer.zero_grad()
                
                conversion_prob, attribution_scores, _ = self.model(
                    channel_indices, mask
                )
                
                # Loss: conversion prediction + attribution regularization
                conversion_loss = self.conversion_criterion(
                    conversion_prob, targets
                )
                
                # Attribution loss: encourage attribution to correlate with conversion
                # Higher attribution for touchpoints in converting journeys
                attribution_targets = mask * targets.unsqueeze(1)
                attribution_loss = self.attribution_criterion(
                    attribution_scores, attribution_targets
                )
                
                loss = conversion_loss + 0.1 * attribution_loss
                
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()
                
                train_loss += loss.item()
                n_batches += 1
            
            avg_train_loss = train_loss / n_batches
            self.history["train_loss"].append(avg_train_loss)
            
            # Validation
            if val_loader:
                val_metrics = self._validate(val_loader)
                self.history["val_loss"].append(val_metrics["loss"])
                self.history["val_auc"].append(val_metrics["auc"])
                
                # Early stopping
                if val_metrics["loss"] < best_val_loss:
                    best_val_loss = val_metrics["loss"]
                    patience_counter = 0
                    # Save best model
                    torch.save(self.model.state_dict(), "best_attribution_model.pt")
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        logger.info(f"Early stopping at epoch {epoch + 1}")
                        break
            
            logger.info(
                f"Epoch {epoch + 1}/{epochs} - "
                f"Train Loss: {avg_train_loss:.4f}"
                + (f" - Val Loss: {val_metrics['loss']:.4f}" if val_loader else "")
            )
        
        return self.history
    
    def _validate(self, val_loader: DataLoader) -> Dict[str, float]:
        """Validate the model."""
        self.model.eval()
        total_loss = 0.0
        n_batches = 0
        all_probs = []
        all_targets = []
        
        with torch.no_grad():
            for batch in val_loader:
                channel_indices, mask, targets, values = batch
                channel_indices = channel_indices.to(self.device)
                mask = mask.to(self.device)
                targets = targets.to(self.device)
                
                conversion_prob, _, _ = self.model(channel_indices, mask)
                
                loss = self.conversion_criterion(conversion_prob, targets)
                total_loss += loss.item()
                n_batches += 1
                
                all_probs.extend(conversion_prob.cpu().numpy())
                all_targets.extend(targets.cpu().numpy())
        
        # Calculate AUC
        from sklearn.metrics import roc_auc_score
        try:
            auc = roc_auc_score(all_targets, all_probs)
        except ValueError:
            auc = 0.5
        
        return {
            "loss": total_loss / n_batches,
            "auc": auc,
        }
    
    def get_channel_attribution(
        self,
        dataset: TouchpointSequenceDataset,
        batch_size: int = 64,
    ) -> Dict[str, float]:
        """
        Get channel-level attribution by aggregating per-touchpoint
        attribution scores across all journeys.
        """
        self.model.eval()
        loader = DataLoader(dataset, batch_size=batch_size)
        
        channel_scores: Dict[str, float] = defaultdict(float)
        channel_counts: Dict[str, int] = defaultdict(int)
        
        idx_to_channel = {v: k for k, v in dataset.channel_to_idx.items()}
        
        with torch.no_grad():
            for batch in loader:
                channel_indices, mask, _, _ = batch
                channel_indices = channel_indices.to(self.device)
                mask = mask.to(self.device)
                
                _, attribution_scores, _ = self.model(channel_indices, mask)
                
                # Aggregate scores by channel
                for i in range(channel_indices.shape[0]):
                    for j in range(channel_indices.shape[1]):
                        if mask[i, j] > 0:
                            channel_idx = channel_indices[i, j].item()
                            channel_name = idx_to_channel.get(channel_idx, "unknown")
                            channel_scores[channel_name] += attribution_scores[i, j].item()
                            channel_counts[channel_name] += 1
        
        # Normalize
        total = sum(channel_scores.values())
        if total == 0:
            return {ch: 0.0 for ch in channel_scores}
        
        return {
            ch: score / total
            for ch, score in channel_scores.items()
        }
```

### 3.6 Ensemble Aggregator

```python
from typing import Dict, List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class EnsembleAttributionAggregator:
    """
    Combines attribution results from multiple models into a unified score.
    
    Uses weighted averaging with confidence-based weighting.
    """
    
    def __init__(
        self,
        model_weights: Optional[Dict[str, float]] = None,
        confidence_threshold: float = 0.1,
    ):
        """
        Args:
            model_weights: Weights for each model (Markov, Shapley, Deep)
            confidence_threshold: Minimum confidence for a model's results to be included
        """
        self.model_weights = model_weights or {
            "markov": 0.3,
            "shapley": 0.3,
            "deep_learning": 0.4,
        }
        self.confidence_threshold = confidence_threshold
        self.model_confidences: Dict[str, float] = {}
    
    def aggregate(
        self,
        markov_results: Optional[Dict[str, float]] = None,
        shapley_results: Optional[Dict[str, float]] = None,
        deep_results: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate attribution results from multiple models.
        
        Returns a unified attribution dictionary with ensemble scores
        and per-model breakdowns.
        """
        all_channels: set = set()
        if markov_results:
            all_channels.update(markov_results.keys())
        if shapley_results:
            all_channels.update(shapley_results.keys())
        if deep_results:
            all_channels.update(deep_results.keys())
        
        # Calculate model confidences
        self._calculate_confidences(
            markov_results, shapley_results, deep_results
        )
        
        # Normalize weights based on confidences
        effective_weights = self._get_effective_weights()
        
        # Aggregate
        ensemble_results = {}
        for channel in all_channels:
            weighted_sum = 0.0
            model_breakdown = {}
            
            if markov_results and channel in markov_results:
                weight = effective_weights.get("markov", 0)
                contribution = markov_results[channel] * weight
                weighted_sum += contribution
                model_breakdown["markov"] = {
                    "raw": markov_results[channel],
                    "weighted": contribution,
                    "weight": weight,
                }
            
            if shapley_results and channel in shapley_results:
                weight = effective_weights.get("shapley", 0)
                contribution = shapley_results[channel] * weight
                weighted_sum += contribution
                model_breakdown["shapley"] = {
                    "raw": shapley_results[channel],
                    "weighted": contribution,
                    "weight": weight,
                }
            
            if deep_results and channel in deep_results:
                weight = effective_weights.get("deep_learning", 0)
                contribution = deep_results[channel] * weight
                weighted_sum += contribution
                model_breakdown["deep_learning"] = {
                    "raw": deep_results[channel],
                    "weighted": contribution,
                    "weight": weight,
                }
            
            ensemble_results[channel] = {
                "ensemble_attribution": weighted_sum,
                "model_breakdown": model_breakdown,
                "confidence": self._calculate_channel_confidence(model_breakdown),
            }
        
        # Normalize ensemble scores to sum to 1
        total = sum(r["ensemble_attribution"] for r in ensemble_results.values())
        if total > 0:
            for channel in ensemble_results:
                ensemble_results[channel]["ensemble_attribution"] /= total
        
        return ensemble_results
    
    def _calculate_confidences(
        self,
        markov_results: Optional[Dict[str, float]],
        shapley_results: Optional[Dict[str, float]],
        deep_results: Optional[Dict[str, float]],
    ) -> None:
        """Calculate confidence scores for each model."""
        # Markov confidence: based on data sufficiency
        if markov_results:
            self.model_confidences["markov"] = min(1.0, len(markov_results) / 5)
        else:
            self.model_confidences["markov"] = 0.0
        
        # Shapley confidence: based on sample size
        if shapley_results:
            self.model_confidences["shapley"] = min(1.0, len(shapley_results) / 5)
        else:
            self.model_confidences["shapley"] = 0.0
        
        # Deep learning confidence: based on model performance
        if deep_results:
            self.model_confidences["deep_learning"] = min(1.0, len(deep_results) / 5)
        else:
            self.model_confidences["deep_learning"] = 0.0
    
    def _get_effective_weights(self) -> Dict[str, float]:
        """Get effective weights adjusted by confidence."""
        effective = {}
        total = 0.0
        
        for model, weight in self.model_weights.items():
            confidence = self.model_confidences.get(model, 0.0)
            if confidence >= self.confidence_threshold:
                effective[model] = weight * confidence
                total += effective[model]
            else:
                effective[model] = 0.0
        
        # Normalize
        if total > 0:
            for model in effective:
                effective[model] /= total
        
        return effective
    
    def _calculate_channel_confidence(
        self,
        model_breakdown: Dict[str, Dict],
    ) -> float:
        """Calculate confidence for a specific channel's attribution."""
        if not model_breakdown:
            return 0.0
        
        # Confidence based on agreement between models
        raw_scores = [m["raw"] for m in model_breakdown.values()]
        if len(raw_scores) < 2:
            return 0.5
        
        # Lower standard deviation = higher confidence
        std = np.std(raw_scores)
        mean = np.mean(raw_scores)
        
        if mean == 0:
            return 0.5
        
        cv = std / mean  # Coefficient of variation
        confidence = max(0.0, 1.0 - cv)
        
        return confidence
```

---

## 4. Predictive Analytics Agent Implementation

### 4.1 Architecture

The Predictive Analytics Agent forecasts future campaign performance, recommends budget allocations, and predicts ROI using a combination of time-series forecasting, gradient boosting, and LLM-based reasoning.

```
┌─────────────────────────────────────────────────────────────────┐
│              PREDICTIVE ANALYTICS AGENT                           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              FEATURE ENGINEERING PIPELINE                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │   │
│  │  │ Temporal │  │ Channel  │  │  Campaign            │  │   │
│  │  │ Features │  │ Features │  │  Metadata            │  │   │
│  │  └──────────┘  └──────────┘  └──────────────────────┘  │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│         ┌───────────────────┼───────────────────┐               │
│         │                   │                   │               │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐        │
│  │  PROPHET    │    │  XGBOOST    │    │    LLM      │        │
│  │  FORECASTER │    │  REGRESSOR  │    │  REASONER   │        │
│  │             │    │             │    │             │        │
│  │ Time-series │    │ Feature-based│   │ Contextual  │        │
│  │ decomposition│  │ prediction  │    │ insights    │        │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘        │
│         │                   │                   │               │
│  ┌──────▼───────────────────▼───────────────────▼──────┐        │
│  │              PREDICTION AGGREGATOR                   │        │
│  │  Ensemble + Confidence Intervals + Scenario Analysis │        │
│  └──────────────────────┬──────────────────────────────┘        │
│                         │                                        │
│  ┌──────────────────────▼──────────────────────────────┐        │
│  │           BUDGET OPTIMIZATION ENGINE                 │        │
│  │  Linear Programming + Marginal ROI Analysis          │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Feature Engineering

```python
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

class MarketingFeatureEngineer:
    """Engineers features for predictive analytics."""
    
    def __init__(self, attribution_results: Dict[str, Any]):
        self.attribution_results = attribution_results
    
    def build_features(
        self,
        touchpoints: List[UnifiedTouchpoint],
        journeys: List[CustomerJourney],
        date_range: tuple[datetime, datetime],
    ) -> pd.DataFrame:
        """
        Build a feature matrix for predictive modeling.
        
        Returns a DataFrame with daily features per channel.
        """
        # Create daily channel-level aggregations
        daily_data = self._aggregate_daily(touchpoints, journeys, date_range)
        
        # Add temporal features
        daily_data = self._add_temporal_features(daily_data)
        
        # Add lag features
        daily_data = self._add_lag_features(daily_data)
        
        # Add rolling window features
        daily_data = self._add_rolling_features(daily_data)
        
        # Add attribution features
        daily_data = self._add_attribution_features(daily_data)
        
        # Add interaction features
        daily_data = self._add_interaction_features(daily_data)
        
        return daily_data
    
    def _aggregate_daily(
        self,
        touchpoints: List[UnifiedTouchpoint],
        journeys: List[CustomerJourney],
        date_range: tuple[datetime, datetime],
    ) -> pd.DataFrame:
        """Aggregate touchpoints and conversions by day and channel."""
        start_date, end_date = date_range
        
        # Create date range
        date_range_list = pd.date_range(start=start_date, end=end_date, freq="D")
        
        # Group touchpoints by date and channel
        daily_records = []
        for date in date_range_list:
            day_touchpoints = [
                tp for tp in touchpoints
                if tp.timestamp.date() == date.date()
            ]
            
            # Group by channel
            channel_groups: Dict[str, List[UnifiedTouchpoint]] = defaultdict(list)
            for tp in day_touchpoints:
                channel_groups[tp.channel.value].append(tp)
            
            for channel, tps in channel_groups.items():
                # Get conversions for this channel on this day
                conversions = [
                    j for j in journeys
                    if j.converted
                    and j.conversion_timestamp
                    and j.conversion_timestamp.date() == date.date()
                    and any(tp.channel.value == channel for tp in j.touchpoints)
                ]
                
                daily_records.append({
                    "date": date,
                    "channel": channel,
                    "impressions": sum(tp.metadata.get("impressions", 0) for tp in tps),
                    "clicks": sum(tp.metadata.get("clicks", 0) for tp in tps),
                    "cost": sum(tp.cost for tp in tps),
                    "conversions": len(conversions),
                    "conversion_value": sum(j.conversion_value for j in conversions),
                    "touchpoints": len(tps),
                })
        
        df = pd.DataFrame(daily_records)
        
        # Fill missing channel-date combinations with zeros
        all_channels = df["channel"].unique() if not df.empty else []
        full_index = pd.MultiIndex.from_product(
            [date_range_list, all_channels],
            names=["date", "channel"]
        )
        df = df.set_index(["date", "channel"]).reindex(full_index, fill_value=0).reset_index()
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add temporal features like day of week, month, etc."""
        df["day_of_week"] = df["date"].dt.dayofweek
        df["day_of_month"] = df["date"].dt.day
        df["month"] = df["date"].dt.month
        df["quarter"] = df["date"].dt.quarter
        df["year"] = df["date"].dt.year
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
        df["is_month_start"] = df["date"].dt.is_month_start.astype(int)
        df["is_month_end"] = df["date"].dt.is_month_end.astype(int)
        
        # Cyclical encoding
        df["day_of_week_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["day_of_week_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
        
        return df
    
    def _add_lag_features(self, df: pd.DataFrame, lags: List[int] = [1, 7, 14, 28]) -> pd.DataFrame:
        """Add lagged features for time-series modeling."""
        df = df.sort_values(["channel", "date"])
        
        for lag in lags:
            df[f"cost_lag_{lag}"] = df.groupby("channel")["cost"].shift(lag)
            df[f"conversions_lag_{lag}"] = df.groupby("channel")["conversions"].shift(lag)
            df[f"conversion_value_lag_{lag}"] = df.groupby("channel")["conversion_value"].shift(lag)
            df[f"clicks_lag_{lag}"] = df.groupby("channel")["clicks"].shift(lag)
            df[f"impressions_lag_{lag}"] = df.groupby("channel")["impressions"].shift(lag)
        
        return df
    
    def _add_rolling_features(
        self,
        df: pd.DataFrame,
        windows: List[int] = [7, 14, 28],
    ) -> pd.DataFrame:
        """Add rolling window statistics."""
        df = df.sort_values(["channel", "date"])
        
        for window in windows:
            for col in ["cost", "conversions", "conversion_value", "clicks"]:
                df[f"{col}_rolling_mean_{window}"] = (
                    df.groupby("channel")[col]
                    .transform(lambda x: x.rolling(window, min_periods=1).mean())
                )
                df[f"{col}_rolling_std_{window}"] = (
                    df.groupby("channel")[col]
                    .transform(lambda x: x.rolling(window, min_periods=1).std())
                )
                df[f"{col}_rolling_sum_{window}"] = (
                    df.groupby("channel")[col]
                    .transform(lambda x: x.rolling(window, min_periods=1).sum())
                )
        
        # Rolling ROI
        df["roi_rolling_7"] = (
            df["conversion_value_rolling_sum_7"] / (df["cost_rolling_sum_7"] + 1e-8)
        )
        df["roi_rolling_28"] = (
            df["conversion_value_rolling_sum_28"] / (df["cost_rolling_sum_28"] + 1e-8)
        )
        
        return df
    
    def _add_attribution_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add attribution-based features."""
        # Map attribution weights to channels
        for channel in df["channel"].unique():
            if channel in self.attribution_results:
                weight = self.attribution_results[channel].get("ensemble_attribution", 0)
                df.loc[df["channel"] == channel, "attribution_weight"] = weight
        
        # Fill missing attribution weights
        df["attribution_weight"] = df["attribution_weight"].fillna(0)
        
        return df
    
    def _add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add interaction features between channels."""
        # Cost per click
        df["cpc"] = df["cost"] / (df["clicks"] + 1e-8)
        
        # Cost per impression (CPM)
        df["cpm"] = df["cost"] / (df["impressions"] + 1e-8) * 1000
        
        # Click-through rate
        df["ctr"] = df["clicks"] / (df["impressions"] + 1e-8)
        
        # Conversion rate
        df["cvr"] = df["conversions"] / (df["clicks"] + 1e-8)
        
        # Return on ad spend
        df["roas"] = df["conversion_value"] / (df["cost"] + 1e-8)
        
        # Cost per acquisition
        df["cpa"] = df["cost"] / (df["conversions"] + 1e-8)
        
        return df
```

### 4.3 Prophet Forecaster

```python
from prophet import Prophet
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MarketingProphetForecaster:
    """Time-series forecaster using Facebook Prophet."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.models: Dict[str, Prophet] = {}
        self.forecasts: Dict[str, pd.DataFrame] = {}
    
    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "conversion_value",
        date_col: str = "date",
        channel_col: str = "channel",
    ) -> "MarketingProphetForecaster":
        """Fit a Prophet model for each channel."""
        channels = df[channel_col].unique()
        
        for channel in channels:
            channel_df = df[df[channel_col] == channel][[date_col, target_col]].copy()
            channel_df.columns = ["ds", "y"]
            
            # Remove outliers
            channel_df = self._remove_outliers(channel_df)
            
            model = Prophet(
                yearly_seasonality=self.config.get("yearly_seasonality", True),
                weekly_seasonality=self.config.get("weekly_seasonality", True),
                daily_seasonality=self.config.get("daily_seasonality", False),
                changepoint_prior_scale=self.config.get("changepoint_prior_scale", 0.05),
                seasonality_prior_scale=self.config.get("seasonality_prior_scale", 10.0),
                holidays_prior_scale=self.config.get("holidays_prior_scale", 10.0),
                interval_width=self.config.get("interval_width", 0.95),
            )
            
            # Add custom seasonality if needed
            if self.config.get("monthly_seasonality", True):
                model.add_seasonality(
                    name="monthly",
                    period=30.5,
                    fourier_order=5,
                )
            
            # Add country holidays
            if self.config.get("country_holidays"):
                model.add_country_holidays(
                    country_name=self.config["country_holidays"]
                )
            
            model.fit(channel_df)
            self.models[channel] = model
        
        return self
    
    def predict(
        self,
        periods: int = 30,
        freq: str = "D",
        include_history: bool = False,
    ) -> Dict[str, pd.DataFrame]:
        """Generate forecasts for all channels."""
        for channel, model in self.models.items():
            future = model.make_future_dataframe(
                periods=periods,
                freq=freq,
                include_history=include_history,
            )
            forecast = model.predict(future)
            self.forecasts[channel] = forecast
        
        return self.forecasts
    
    def get_channel_forecast(self, channel: str) -> Optional[pd.DataFrame]:
        """Get forecast for a specific channel."""
        return self.forecasts.get(channel)
    
    def get_aggregate_forecast(self) -> pd.DataFrame:
        """Get aggregated forecast across all channels."""
        if not self.forecasts:
            return pd.DataFrame()
        
        # Sum predictions across channels
        aggregate = None
        for channel, forecast in self.forecasts.items():
            if aggregate is None:
                aggregate = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
                aggregate.columns = ["date", "yhat", "yhat_lower", "yhat_upper"]
            else:
                aggregate["yhat"] += forecast["yhat"].values
                aggregate["yhat_lower"] += forecast["yhat_lower"].values
                aggregate["yhat_upper"] += forecast["yhat_upper"].values
        
        return aggregate
    
    def _remove_outliers(
        self,
        df: pd.DataFrame,
        threshold: float = 3.0,
    ) -> pd.DataFrame:
        """Remove outliers using z-score."""
        z_scores = np.abs((df["y"] - df["y"].mean()) / (df["y"].std() + 1e-8))
        return df[z_scores < threshold].copy()
```

### 4.4 XGBoost Predictor

```python
import xgboost as xgb
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging

logger = logging.getLogger(__name__)

class MarketingXGBoostPredictor:
    """XGBoost-based predictor for marketing performance."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.models: Dict[str, xgb.XGBRegressor] = {}
        self.feature_importance: Dict[str, pd.DataFrame] = {}
        self.metrics: Dict[str, Dict[str, float]] = {}
    
    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "conversion_value",
        channel_col: str = "channel",
        date_col: str = "date",
        test_size: float = 0.2,
    ) -> "MarketingXGBoostPredictor":
        """Fit XGBoost models for each channel."""
        feature_cols = self._get_feature_columns(df, [target_col, channel_col, date_col])
        
        channels = df[channel_col].unique()
        
        for channel in channels:
            channel_df = df[df[channel_col] == channel].sort_values(date_col)
            
            X = channel_df[feature_cols].fillna(0)
            y = channel_df[target_col]
            
            # Time-based split
            split_idx = int(len(X) * (1 - test_size))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            
            model = xgb.XGBRegressor(
                n_estimators=self.config.get("n_estimators", 500),
                max_depth=self.config.get("max_depth", 6),
                learning_rate=self.config.get("learning_rate", 0.05),
                subsample=self.config.get("subsample", 0.8),
                colsample_bytree=self.config.get("colsample_bytree", 0.8),
                reg_alpha=self.config.get("reg_alpha", 0.1),
                reg_lambda=self.config.get("reg_lambda", 1.0),
                early_stopping_rounds=self.config.get("early_stopping_rounds", 50),
                random_state=42,
                n_jobs=-1,
            )
            
            model.fit(
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                verbose=False,
            )
            
            self.models[channel] = model
            
            # Feature importance
            importance = pd.DataFrame({
                "feature": feature_cols,
                "importance": model.feature_importances_,
            }).sort_values("importance", ascending=False)
            self.feature_importance[channel] = importance
            
            # Metrics
            y_pred = model.predict(X_test)
            self.metrics[channel] = {
                "mae": mean_absolute_error(y_test, y_pred),
                "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                "r2": r2_score(y_test, y_pred),
                "mape": np.mean(np.abs((y_test - y_pred) / (y_test + 1e-8))) * 100,
            }
        
        return self
    
    def predict(
        self,
        df: pd.DataFrame,
        channel_col: str = "channel",
        date_col: str = "date",
    ) -> pd.DataFrame:
        """Generate predictions for all channels."""
        feature_cols = self._get_feature_columns(
            df, [channel_col, date_col, "conversion_value"]
        )
        
        predictions = []
        for channel in self.models:
            channel_df = df[df[channel_col] == channel].copy()
            if channel_df.empty:
                continue
            
            X = channel_df[feature_cols].fillna(0)
            channel_df["predicted_conversion_value"] = self.models[channel].predict(X)
            channel_df["prediction_confidence"] = self._estimate_confidence(channel, X)
            predictions.append(channel_df)
        
        return pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()
    
    def _estimate_confidence(
        self,
        channel: str,
        X: pd.DataFrame,
    ) -> np.ndarray:
        """Estimate prediction confidence using prediction intervals."""
        # Use XGBoost's built-in uncertainty estimation
        model = self.models[channel]
        
        # Get predictions from all trees
        predictions = []
        for tree in model.get_booster().get_dump():
            # Simplified: use variance across trees as confidence proxy
            pass
        
        # Return confidence scores (higher = more confident)
        # For now, use a simple heuristic based on feature similarity to training data
        return np.ones(len(X)) * 0.8  # Placeholder
    
    def _get_feature_columns(
        self,
        df: pd.DataFrame,
        exclude_cols: List[str],
    ) -> List[str]:
        """Get feature columns excluding target and metadata columns."""
        exclude_patterns = exclude_cols + [
            "conversion_value", "conversions", "revenue", "roas",
        ]
        return [
            col for col in df.columns
            if col not in exclude_patterns
            and df[col].dtype in [np.float64, np.int64, np.float32, np.int32]
        ]
```

### 4.5 Budget Optimization Engine

```python
from scipy.optimize import linprog, minimize
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class BudgetOptimizationEngine:
    """
    Optimizes budget allocation across channels using linear programming
    and marginal ROI analysis.
    """
    
    def __init__(
        self,
        attribution_results: Dict[str, Dict],
        marginal_roi_curves: Optional[Dict[str, callable]] = None,
    ):
        self.attribution_results = attribution_results
        self.marginal_roi_curves = marginal_roi_curves or {}
    
    def optimize(
        self,
        total_budget: float,
        channel_constraints: Optional[Dict[str, Tuple[float, float]]] = None,
        objective: str = "maximize_conversions",
    ) -> Dict[str, Any]:
        """
        Optimize budget allocation across channels.
        
        Args:
            total_budget: Total budget to allocate
            channel_constraints: Dict of channel -> (min_budget, max_budget)
            objective: Optimization objective
            
        Returns:
            Optimization result with recommended allocations
        """
        channels = list(self.attribution_results.keys())
        n_channels = len(channels)
        
        if n_channels == 0:
            return {"status": "error", "message": "No channels to optimize"}
        
        # Default constraints: 0 to total_budget for each channel
        if channel_constraints is None:
            channel_constraints = {
                ch: (0, total_budget) for ch in channels
            }
        
        # Build objective function coefficients
        # Use attribution weights as proxy for marginal return
        c = np.array([
            -self.attribution_results[ch].get("ensemble_attribution", 0)
            for ch in channels
        ])
        
        # Constraints
        A_eq = [np.ones(n_channels)]  # Sum of allocations = total_budget
        b_eq = [total_budget]
        
        # Bounds
        bounds = [
            channel_constraints.get(ch, (0, total_budget))
            for ch in channels
        ]
        
        # Solve
        result = linprog(
            c,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method="highs",
        )
        
        if result.success:
            allocations = {
                ch: round(result.x[i], 2)
                for i, ch in enumerate(channels)
            }
            
            # Calculate expected outcomes
            expected_conversions = self._estimate_conversions(allocations)
            expected_revenue = self._estimate_revenue(allocations)
            
            return {
                "status": "optimal",
                "allocations": allocations,
                "total_budget": total_budget,
                "expected_conversions": expected_conversions,
                "expected_revenue": expected_revenue,
                "expected_roas": expected_revenue / total_budget if total_budget > 0 else 0,
                "channel_details": self._get_channel_details(allocations),
            }
        else:
            return {
                "status": "failed",
                "message": result.message,
            }
    
    def optimize_marginal_roi(
        self,
        total_budget: float,
        channel_roi_functions: Dict[str, callable],
        granularity: float = 100.0,
    ) -> Dict[str, Any]:
        """
        Optimize budget using marginal ROI analysis.
        
        Allocates budget incrementally to the channel with the highest
        marginal ROI at each step.
        """
        channels = list(channel_roi_functions.keys())
        allocations = {ch: 0.0 for ch in channels}
        remaining_budget = total_budget
        
        while remaining_budget >= granularity:
            best_channel = None
            best_marginal_roi = -float("inf")
            
            for channel in channels:
                current = allocations[channel]
                roi_func = channel_roi_functions[channel]
                
                # Calculate marginal ROI
                current_revenue = roi_func(current)
                new_revenue = roi_func(current + granularity)
                marginal_roi = (new_revenue - current_revenue) / granularity
                
                if marginal_roi > best_marginal_roi:
                    best_marginal_roi = marginal_roi
                    best_channel = channel
            
            if best_channel is None or best_marginal_roi <= 0:
                break
            
            allocations[best_channel] += granularity
            remaining_budget -= granularity
        
        return {
            "status": "optimal",
            "allocations": allocations,
            "total_budget": total_budget,
            "remaining_budget": remaining_budget,
            "channel_details": self._get_channel_details(allocations),
        }
    
    def _estimate_conversions(self, allocations: Dict[str, float]) -> float:
        """Estimate total conversions from budget allocations."""
        total = 0.0
        for channel, budget in allocations.items():
            if channel in self.attribution_results:
                weight = self.attribution_results[channel].get("ensemble_attribution", 0)
                # Simplified: conversions proportional to budget * attribution weight
                total += budget * weight * 0.1  # Conversion rate factor
        return total
    
    def _estimate_revenue(self, allocations: Dict[str, float]) -> float:
        """Estimate total revenue from budget allocations."""
        total = 0.0
        for channel, budget in allocations.items():
            if channel in self.attribution_results:
                weight = self.attribution_results[channel].get("ensemble_attribution", 0)
                total += budget * weight * 3.0  # ROAS factor
        return total
    
    def _get_channel_details(
        self,
        allocations: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """Get detailed information for each channel."""
        details = []
        for channel, budget in allocations.items():
            attribution = self.attribution_results.get(channel, {})
            details.append({
                "channel": channel,
                "allocated_budget": budget,
                "budget_percentage": budget / sum(allocations.values()) * 100 if allocations else 0,
                "attribution_weight": attribution.get("ensemble_attribution", 0),
                "confidence": attribution.get("confidence", 0),
            })
        return sorted(details, key=lambda x: x["allocated_budget"], reverse=True)
```

### 4.6 Predictive Analytics Agent

```python
from langchain_deepagents import DeepAgent
from langchain_deepagents.planner import PlannerConfig
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PredictiveAnalyticsAgent:
    """
    Agent that orchestrates predictive analytics for marketing attribution.
    
    Combines Prophet forecasting, XGBoost prediction, and LLM-based reasoning
    to generate actionable insights and recommendations.
    """
    
    def __init__(
        self,
        forecaster: MarketingProphetForecaster,
        predictor: MarketingXGBoostPredictor,
        optimizer: BudgetOptimizationEngine,
        llm: Any,  # LangChain LLM
    ):
        self.forecaster = forecaster
        self.predictor = predictor
        self.optimizer = optimizer
        self.llm = llm
    
    async def analyze(
        self,
        historical_data: pd.DataFrame,
        forecast_horizon_days: int = 30,
        total_budget: Optional[float] = None,
        channel_constraints: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> Dict[str, Any]:
        """
        Run full predictive analytics pipeline.
        
        Returns forecasts, predictions, and budget recommendations.
        """
        results = {
            "forecasts": {},
            "predictions": {},
            "budget_recommendation": None,
            "insights": [],
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        # Step 1: Generate time-series forecasts
        logger.info("Generating Prophet forecasts...")
        self.forecaster.fit(historical_data)
        forecasts = self.forecaster.predict(periods=forecast_horizon_days)
        results["forecasts"] = {
            channel: {
                "dates": forecast["ds"].dt.strftime("%Y-%m-%d").tolist(),
                "predicted": forecast["yhat"].tolist(),
                "lower_bound": forecast["yhat_lower"].tolist(),
                "upper_bound": forecast["yhat_upper"].tolist(),
            }
            for channel, forecast in forecasts.items()
        }
        
        # Step 2: Generate XGBoost predictions
        logger.info("Generating XGBoost predictions...")
        predictions = self.predictor.predict(historical_data)
        results["predictions"] = predictions.to_dict("records")
        
        # Step 3: Budget optimization
        if total_budget:
            logger.info("Optimizing budget allocation...")
            budget_result = self.optimizer.optimize(
                total_budget=total_budget,
                channel_constraints=channel_constraints,
            )
            results["budget_recommendation"] = budget_result
        
        # Step 4: Generate LLM-based insights
        logger.info("Generating LLM insights...")
        insights = await self._generate_insights(
            historical_data, forecasts, predictions, results.get("budget_recommendation")
        )
        results["insights"] = insights
        
        return results
    
    async def _generate_insights(
        self,
        historical_data: pd.DataFrame,
        forecasts: Dict[str, pd.DataFrame],
        predictions: pd.DataFrame,
        budget_recommendation: Optional[Dict],
    ) -> List[str]:
        """Generate natural language insights using LLM."""
        # Prepare context for LLM
        context = self._prepare_llm_context(
            historical_data, forecasts, predictions, budget_recommendation
        )
        
        prompt = f"""
        You are a marketing analytics expert. Based on the following data, generate
        actionable insights and recommendations for the marketing team.
        
        ## Historical Performance Summary
        {context['historical_summary']}
        
        ## Forecast Summary
        {context['forecast_summary']}
        
        ## Budget Recommendation
        {context['budget_summary']}
        
        Please provide:
        1. Key trends observed in the data
        2. Channels that are over/under-performing
        3. Recommended actions for the next 30 days
        4. Risks and opportunities
        5. Budget reallocation suggestions
        
        Format your response as a numbered list of concise, actionable insights.
        """
        
        response = await self.llm.ainvoke(prompt)
        
        # Parse insights from response
        insights = [
            line.strip() for line in response.content.split("\n")
            if line.strip() and len(line.strip()) > 20
        ]
        
        return insights
    
    def _prepare_llm_context(
        self,
        historical_data: pd.DataFrame,
        forecasts: Dict[str, pd.DataFrame],
        predictions: pd.DataFrame,
        budget_recommendation: Optional[Dict],
    ) -> Dict[str, str]:
        """Prepare context strings for LLM prompt."""
        # Historical summary
        historical_summary = historical_data.groupby("channel").agg({
            "cost": "sum",
            "conversion_value": "sum",
            "conversions": "sum",
            "clicks": "sum",
            "impressions": "sum",
        }).to_string()
        
        # Forecast summary
        forecast_lines = []
        for channel, forecast in forecasts.items():
            total_predicted = forecast["yhat"].sum()
            forecast_lines.append(f"{channel}: {total_predicted:.2f}")
        forecast_summary = "\n".join(forecast_lines)
        
        # Budget summary
        if budget_recommendation and budget_recommendation.get("status") == "optimal":
            budget_lines = [
                f"{ch}: ${alloc:.2f}"
                for ch, alloc in budget_recommendation["allocations"].items()
            ]
            budget_summary = "\n".join(budget_lines)
        else:
            budget_summary = "No budget recommendation available"
        
        return {
            "historical_summary": historical_summary,
            "forecast_summary": forecast_summary,
            "budget_summary": budget_summary,
        }
```

---

## 5. Reporting Agent Implementation

### 5.1 Architecture

The Reporting Agent generates comprehensive, human-readable reports from attribution results, predictions, and insights. It uses Jinja2 templating, Plotly for visualizations, and LLM-based narrative generation.

```
┌─────────────────────────────────────────────────────────────────┐
│                   REPORTING AGENT                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              REPORT GENERATION PIPELINE                   │   │
│  │                                                           │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │   │
│  │  │  Data       │───▶│  Template   │───▶│  Narrative  │  │   │
│  │  │  Aggregator │    │  Engine     │    │  Generator  │  │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘  │   │
│  │         │                  │                  │           │   │
│  │  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐  │   │
│  │  │  Chart      │    │  Table      │    │  Export     │  │   │
│  │  │  Generator  │    │  Builder    │    │  Engine     │  │   │
│  │  │  (Plotly)   │    │  (Pandas)   │    │  (PDF/HTML) │  │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              OUTPUT FORMATS                               │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────────────┐ │   │
│  │  │ Markdown│  │  HTML  │  │  PDF   │  │  Slack/Email   │ │   │
│  │  └────────┘  └────────┘  └────────┘  └────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Report Generator

```python
from jinja2 import Environment, FileSystemLoader, DictLoader
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class AttributionReportGenerator:
    """Generates comprehensive attribution reports."""
    
    def __init__(self, template_dir: Optional[str] = None):
        if template_dir:
            self.env = Environment(loader=FileSystemLoader(template_dir))
        else:
            self.env = Environment(loader=DictLoader(DEFAULT_TEMPLATES))
    
    def generate(
        self,
        attribution_results: Dict[str, Dict],
        predictions: Optional[Dict] = None,
        insights: Optional[List[str]] = None,
        report_date: Optional[str] = None,
        format: str = "markdown",
    ) -> str:
        """
        Generate a full attribution report.
        
        Args:
            attribution_results: Attribution results from the ensemble
            predictions: Optional prediction results
            insights: Optional LLM-generated insights
            report_date: Report date string
            format: Output format ("markdown", "html", "json")
            
        Returns:
            Report content as a string
        """
        report_date = report_date or datetime.utcnow().strftime("%Y-%m-%d")
        
        # Generate charts
        charts = self._generate_charts(attribution_results, predictions)
        
        # Build report context
        context = {
            "report_date": report_date,
            "attribution_results": attribution_results,
            "predictions": predictions,
            "insights": insights or [],
            "charts": charts,
            "summary_stats": self._calculate_summary_stats(attribution_results),
        }
        
        # Render template
        template = self.env.get_template(f"attribution_report.{format}")
        report = template.render(**context)
        
        return report
    
    def _generate_charts(
        self,
        attribution_results: Dict[str, Dict],
        predictions: Optional[Dict] = None,
    ) -> Dict[str, str]:
        """Generate Plotly charts as HTML divs."""
        charts = {}
        
        # Attribution pie chart
        charts["attribution_pie"] = self._create_attribution_pie(attribution_results)
        
        # Attribution bar chart
        charts["attribution_bar"] = self._create_attribution_bar(attribution_results)
        
        # Model comparison chart
        charts["model_comparison"] = self._create_model_comparison(attribution_results)
        
        # Confidence chart
        charts["confidence"] = self._create_confidence_chart(attribution_results)
        
        # Forecast charts (if predictions available)
        if predictions and "forecasts" in predictions:
            charts["forecasts"] = self._create_forecast_charts(predictions["forecasts"])
        
        return charts
    
    def _create_attribution_pie(
        self,
        attribution_results: Dict[str, Dict],
    ) -> str:
        """Create a pie chart of attribution weights."""
        labels = list(attribution_results.keys())
        values = [
            attribution_results[ch].get("ensemble_attribution", 0)
            for ch in labels
        ]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo="label+percent",
            textposition="outside",
        )])
        
        fig.update_layout(
            title="Channel Attribution Distribution",
            showlegend=True,
            height=500,
        )
        
        return fig.to_html(full_html=False, include_plotlyjs="cdn")
    
    def _create_attribution_bar(
        self,
        attribution_results: Dict[str, Dict],
    ) -> str:
        """Create a bar chart of attribution weights."""
        channels = list(attribution_results.keys())
        ensemble_values = [
            attribution_results[ch].get("ensemble_attribution", 0)
            for ch in channels
        ]
        
        # Get per-model values
        model_names = ["markov", "shapley", "deep_learning"]
        model_data = {}
        for model in model_names:
            model_data[model] = [
                attribution_results[ch].get("model_breakdown", {}).get(model, {}).get("raw", 0)
                for ch in channels
            ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name="Ensemble",
            x=channels,
            y=ensemble_values,
            marker_color="#1f77b4",
        ))
        
        for model in model_names:
            fig.add_trace(go.Bar(
                name=model.replace("_", " ").title(),
                x=channels,
                y=model_data[model],
            ))
        
        fig.update_layout(
            title="Attribution Comparison Across Models",
            xaxis_title="Channel",
            yaxis_title="Attribution Weight",
            barmode="group",
            height=500,
        )
        
        return fig.to_html(full_html=False, include_plotlyjs="cdn")
    
    def _create_model_comparison(
        self,
        attribution_results: Dict[str, Dict],
    ) -> str:
        """Create a heatmap comparing model attributions."""
        channels = list(attribution_results.keys())
        models = ["markov", "shapley", "deep_learning"]
        
        z = []
        for model in models:
            row = []
            for ch in channels:
                val = attribution_results[ch].get("model_breakdown", {}).get(model, {}).get("raw", 0)
                row.append(val)
            z.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=channels,
            y=[m.replace("_", " ").title() for m in models],
            colorscale="YlOrRd",
        ))
        
        fig.update_layout(
            title="Model Attribution Heatmap",
            xaxis_title="Channel",
            yaxis_title="Model",
            height=400,
        )
        
        return fig.to_html(full_html=False, include_plotlyjs="cdn")
    
    def _create_confidence_chart(
        self,
        attribution_results: Dict[str, Dict],
    ) -> str:
        """Create a chart showing attribution confidence by channel."""
        channels = list(attribution_results.keys())
        confidences = [
            attribution_results[ch].get("confidence", 0)
            for ch in channels
        ]
        
        fig = go.Figure(data=[go.Bar(
            x=channels,
            y=confidences,
            marker_color=[
                "#2ecc71" if c >= 0.7 else "#f39c12" if c >= 0.4 else "#e74c3c"
                for c in confidences
            ],
        )])
        
        fig.update_layout(
            title="Attribution Confidence by Channel",
            xaxis_title="Channel",
            yaxis_title="Confidence Score",
            yaxis_range=[0, 1],
            height=400,
        )
        
        return fig.to_html(full_html=False, include_plotlyjs="cdn")
    
    def _create_forecast_charts(
        self,
        forecasts: Dict[str, Dict],
    ) -> str:
        """Create forecast charts for all channels."""
        n_channels = len(forecasts)
        fig = make_subplots(
            rows=n_channels,
            cols=1,
            subplot_titles=list(forecasts.keys()),
            vertical_spacing=0.1,
        )
        
        for i, (channel, forecast_data) in enumerate(forecasts.items(), 1):
            dates = forecast_data["dates"]
            predicted = forecast_data["predicted"]
            lower = forecast_data["lower_bound"]
            upper = forecast_data["upper_bound"]
            
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=predicted,
                    mode="lines",
                    name=f"{channel} Forecast",
                    line=dict(color="#1f77b4"),
                ),
                row=i, col=1,
            )
            
            fig.add_trace(
                go.Scatter(
                    x=dates + dates[::-1],
                    y=upper + lower[::-1],
                    fill="toself",
                    fillcolor="rgba(31, 119, 180, 0.2)",
                    line=dict(color="rgba(255,255,255,0)"),
                    name=f"{channel} 95% CI",
                    showlegend=False,
                ),
                row=i, col=1,
            )
        
        fig.update_layout(
            title="Channel Forecasts with 95% Confidence Intervals",
            height=300 * n_channels,
        )
        
        return fig.to_html(full_html=False, include_plotlyjs="cdn")
    
    def _calculate_summary_stats(
        self,
        attribution_results: Dict[str, Dict],
    ) -> Dict[str, Any]:
        """Calculate summary statistics for the report."""
        channels = list(attribution_results.keys())
        
        # Top channel
        top_channel = max(
            channels,
            key=lambda ch: attribution_results[ch].get("ensemble_attribution", 0),
        )
        
        # Average confidence
        avg_confidence = sum(
            attribution_results[ch].get("confidence", 0)
            for ch in channels
        ) / len(channels) if channels else 0
        
        # Model agreement (lower std = higher agreement)
        model_agreement = {}
        for ch in channels:
            breakdown = attribution_results[ch].get("model_breakdown", {})
            raw_values = [
                m.get("raw", 0) for m in breakdown.values()
            ]
            if len(raw_values) >= 2:
                model_agreement[ch] = 1.0 - min(1.0, np.std(raw_values) / (np.mean(raw_values) + 1e-8))
            else:
                model_agreement[ch] = 0.5
        
        return {
            "total_channels": len(channels),
            "top_channel": top_channel,
            "top_channel_attribution": attribution_results[top_channel].get("ensemble_attribution", 0),
            "average_confidence": avg_confidence,
            "model_agreement": model_agreement,
        }


# Default Jinja2 templates
DEFAULT_TEMPLATES = {
    "attribution_report.markdown": """# Marketing Attribution Report

**Report Date:** {{ report_date }}

---

## Executive Summary

This report provides a comprehensive analysis of marketing channel attribution
using an ensemble of Markov Chain, Shapley Value, and Deep Learning models.

### Key Findings

- **Total Channels Analyzed:** {{ summary_stats.total_channels }}
- **Top Performing Channel:** {{ summary_stats.top_channel }} ({{ "%.1f"|format(summary_stats.top_channel_attribution * 100) }}% attribution)
- **Average Confidence:** {{ "%.1f"|format(summary_stats.average_confidence * 100) }}%

---

## Attribution Results

### Channel Attribution Weights

| Channel | Attribution | Confidence |
|---------|------------|------------|
{% for channel, data in attribution_results.items() %}
| {{ channel }} | {{ "%.2f"|format(data.ensemble_attribution * 100) }}% | {{ "%.1f"|format(data.confidence * 100) }}% |
{% endfor %}

### Model Breakdown

{% for channel, data in attribution_results.items() %}
#### {{ channel }}
{% if data.model_breakdown %}
| Model | Raw Attribution | Weighted |
|-------|----------------|----------|
{% for model, model_data in data.model_breakdown.items() %}
| {{ model }} | {{ "%.4f"|format(model_data.raw) }} | {{ "%.4f"|format(model_data.weighted) }} |
{% endfor %}
{% endif %}

{% endfor %}

---

## Visualizations

### Attribution Distribution

{{ charts.attribution_pie }}

### Model Comparison

{{ charts.attribution_bar }}

### Confidence Analysis

{{ charts.confidence }}

{% if charts.forecasts %}
### Forecasts

{{ charts.forecasts }}
{% endif %}

---

## Insights & Recommendations

{% for insight in insights %}
{{ loop.index }}. {{ insight }}
{% endfor %}

---

## Technical Details

### Methodology

1. **Markov Chain Model:** First-order Markov chain with removal effect calculation
2. **Shapley Value Model:** Cooperative game theory with exact/approximate computation
3. **Deep Learning Model:** BiLSTM with attention mechanism
4. **Ensemble:** Confidence-weighted aggregation of all models

### Data Quality

- Touchpoint normalization and deduplication applied
- Identity resolution across sessions
- Outlier detection and removal

---

*Report generated by AI-Powered Marketing Attribution System*
""",
    "attribution_report.html": """<!DOCTYPE html>
<html>
<head>
    <title>Marketing Attribution Report - {{ report_date }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { color: #1a1a2e; border-bottom: 3px solid #16213e; padding-bottom: 10px; }
        h2 { color: #16213e; margin-top: 30px; }
        h3 { color: #0f3460; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #16213e; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #16213e; }
        .metric-label { font-size: 12px; color: #666; text-transform: uppercase; }
        .insight { padding: 10px 15px; margin: 5px 0; background: #e8f4f8; border-left: 4px solid #16213e; }
        .chart { margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Marketing Attribution Report</h1>
    <p><strong>Report Date:</strong> {{ report_date }}</p>
    
    <h2>Executive Summary</h2>
    <div>
        <div class="metric">
            <div class="metric-value">{{ summary_stats.total_channels }}</div>
            <div class="metric-label">Channels</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ summary_stats.top_channel }}</div>
            <div class="metric-label">Top Channel</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ "%.1f"|format(summary_stats.average_confidence * 100) }}%</div>
            <div class="metric-label">Avg Confidence</div>
        </div>
    </div>
    
    <h2>Attribution Results</h2>
    <table>
        <tr>
            <th>Channel</th>
            <th>Attribution</th>
            <th>Confidence</th>
        </tr>
        {% for channel, data in attribution_results.items() %}
        <tr>
            <td>{{ channel }}</td>
            <td>{{ "%.2f"|format(data.ensemble_attribution * 100) }}%</td>
            <td>{{ "%.1f"|format(data.confidence * 100) }}%</td>
        </tr>
        {% endfor %}
    </table>
    
    <h2>Visualizations</h2>
    <div class="chart">{{ charts.attribution_pie }}</div>
    <div class="chart">{{ charts.attribution_bar }}</div>
    <div class="chart">{{ charts.confidence }}</div>
    {% if charts.forecasts %}
    <div class="chart">{{ charts.forecasts }}</div>
    {% endif %}
    
    <h2>Insights & Recommendations</h2>
    {% for insight in insights %}
    <div class="insight">{{ insight }}</div>
    {% endfor %}
    
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
        Report generated by AI-Powered Marketing Attribution System
    </footer>
</body>
</html>
""",
}
```

### 5.3 Reporting Agent

```python
from langchain_deepagents import DeepAgent
from langchain_deepagents.planner import PlannerConfig
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ReportingAgent:
    """
    Agent that generates and distributes marketing attribution reports.
    
    Supports multiple output formats and distribution channels.
    """
    
    def __init__(
        self,
        report_generator: AttributionReportGenerator,
        llm: Any,
        config: Optional[Dict] = None,
    ):
        self.report_generator = report_generator
        self.llm = llm
        self.config = config or {}
    
    async def generate_report(
        self,
        attribution_results: Dict[str, Dict],
        predictions: Optional[Dict] = None,
        insights: Optional[List[str]] = None,
        format: str = "markdown",
        include_charts: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive attribution report.
        
        Returns a dictionary with the report content and metadata.
        """
        # Generate report
        report_content = self.report_generator.generate(
            attribution_results=attribution_results,
            predictions=predictions,
            insights=insights,
            format=format,
        )
        
        # Generate executive summary using LLM
        executive_summary = await self._generate_executive_summary(
            attribution_results, predictions, insights
        )
        
        # Generate action items
        action_items = await self._generate_action_items(
            attribution_results, predictions, insights
        )
        
        return {
            "content": report_content,
            "executive_summary": executive_summary,
            "action_items": action_items,
            "format": format,
            "generated_at": datetime.utcnow().isoformat(),
            "metadata": {
                "channels_covered": len(attribution_results),
                "has_predictions": predictions is not None,
                "has_insights": insights is not None and len(insights) > 0,
            },
        }
    
    async def _generate_executive_summary(
        self,
        attribution_results: Dict[str, Dict],
        predictions: Optional[Dict],
        insights: Optional[List[str]],
    ) -> str:
        """Generate an executive summary using LLM."""
        # Prepare data summary
        channel_lines = []
        for channel, data in sorted(
            attribution_results.items(),
            key=lambda x: x[1].get("ensemble_attribution", 0),
            reverse=True,
        ):
            channel_lines.append(
                f"- {channel}: {data.get('ensemble_attribution', 0)*100:.1f}% attribution, "
                f"{data.get('confidence', 0)*100:.1f}% confidence"
            )
        
        prompt = f"""
        Write a concise executive summary (3-5 sentences) for a marketing attribution report.
        
        Channel Attribution:
        {chr(10).join(channel_lines)}
        
        Key Insights:
        {chr(10).join(insights[:5]) if insights else "No insights available"}
        
        The summary should highlight:
        1. The most important findings
        2. Key recommendations
        3. Any risks or concerns
        
        Write in a professional, clear tone suitable for C-level executives.
        """
        
        response = await self.llm.ainvoke(prompt)
        return response.content.strip()
    
    async def _generate_action_items(
        self,
        attribution_results: Dict[str, Dict],
        predictions: Optional[Dict],
        insights: Optional[List[str]],
    ) -> List[Dict[str, str]]:
        """Generate specific action items using LLM."""
        prompt = f"""
        Based on the following attribution results and insights, generate 3-5 specific,
        actionable recommendations for the marketing team.
        
        Attribution Results:
        {json.dumps({ch: {"attribution": d.get("ensemble_attribution", 0), "confidence": d.get("confidence", 0)} for ch, d in attribution_results.items()}, indent=2)}
        
        Insights:
        {chr(10).join(insights) if insights else "None"}
        
        Format each action item as:
        - **Action**: [specific action]
        - **Channel**: [affected channel]
        - **Expected Impact**: [quantified impact if possible]
        - **Priority**: [high/medium/low]
        """
        
        response = await self.llm.ainvoke(prompt)
        
        # Parse action items from response
        action_items = []
        current_item = {}
        
        for line in response.content.split("\n"):
            line = line.strip()
            if line.startswith("- **Action:**"):
                if current_item:
                    action_items.append(current_item)
                current_item = {"action": line.replace("- **Action:**", "").strip()}
            elif line.startswith("- **Channel:**"):
                current_item["channel"] = line.replace("- **Channel:**", "").strip()
            elif line.startswith("- **Expected Impact:**"):
                current_item["expected_impact"] = line.replace("- **Expected Impact:**", "").strip()
            elif line.startswith("- **Priority:**"):
                current_item["priority"] = line.replace("- **Priority:**", "").strip()
        
        if current_item:
            action_items.append(current_item)
        
        return action_items
    
    async def distribute_report(
        self,
        report: Dict[str, Any],
        channels: List[str] = ["email"],
        recipients: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Distribute the report to specified channels.
        
        Supported channels: email, slack, webhook
        """
        distribution_results = {}
        
        for channel in channels:
            if channel == "email":
                distribution_results["email"] = await self._send_email(
                    report, recipients
                )
            elif channel == "slack":
                distribution_results["slack"] = await self._send_slack(
                    report, recipients
                )
            elif channel == "webhook":
                distribution_results["webhook"] = await self._send_webhook(
                    report
                )
        
        return distribution_results
    
    async def _send_email(
        self,
        report: Dict[str, Any],
        recipients: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Send report via email."""
        # Implementation would use email service
        logger.info(f"Sending report via email to {recipients}")
        return {"status": "sent", "recipients": recipients}
    
    async def _send_slack(
        self,
        report: Dict[str, Any],
        recipients: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Send report summary via Slack."""
        # Implementation would use Slack API
        logger.info(f"Sending report summary via Slack to {recipients}")
        return {"status": "sent", "recipients": recipients}
    
    async def _send_webhook(
        self,
        report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send report to webhook endpoint."""
        # Implementation would use HTTP POST
        logger.info("Sending report to webhook")
        return {"status": "sent"}
```

---

## 6. Real-time Dashboards

### 6.1 Architecture

Real-time dashboards provide live visibility into attribution metrics, campaign performance, and predictive insights. The system uses a streaming architecture with WebSocket connections for live updates.

```
┌─────────────────────────────────────────────────────────────────┐
│                 REAL-TIME DASHBOARD SYSTEM                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              STREAMING DATA PIPELINE                      │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │   │
│  │  │ Event    │  │ Kafka /  │  │ Stream   │  │ WebSocket│ │   │
│  │  │ Sources  │─▶│ Kinesis  │─▶│ Processor│─▶│ Server   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              DASHBOARD FRONTEND                           │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │  Real-time  │  │  Attribution│  │  Predictive │     │   │
│  │  │  Metrics    │  │  Explorer   │  │  Panel      │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  │                                                           │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │  Channel    │  │  Budget     │  │  Alert      │     │   │
│  │  │  Comparison │  │  Optimizer  │  │  Center     │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 WebSocket Server

```python
import asyncio
import json
import websockets
from typing import Dict, Set, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DashboardWebSocketServer:
    """WebSocket server for real-time dashboard updates."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.subscriptions: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
        self.latest_data: Dict[str, Any] = {}
    
    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        async with websockets.serve(self._handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever
    
    async def _handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle a client connection."""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        finally:
            self.clients.discard(websocket)
            # Remove from all subscriptions
            for clients in self.subscriptions.values():
                clients.discard(websocket)
    
    async def _handle_message(
        self,
        websocket: websockets.WebSocketServerProtocol,
        message: str,
    ):
        """Handle an incoming message from a client."""
        try:
            data = json.loads(message)
            action = data.get("action")
            
            if action == "subscribe":
                channel = data.get("channel", "all")
                if channel not in self.subscriptions:
                    self.subscriptions[channel] = set()
                self.subscriptions[channel].add(websocket)
                
                # Send latest data immediately
                if channel in self.latest_data:
                    await websocket.send(json.dumps({
                        "type": "data",
                        "channel": channel,
                        "data": self.latest_data[channel],
                        "timestamp": datetime.utcnow().isoformat(),
                    }))
            
            elif action == "unsubscribe":
                channel = data.get("channel", "all")
                if channel in self.subscriptions:
                    self.subscriptions[channel].discard(websocket)
            
            elif action == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
        
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON",
            }))
    
    async def broadcast(self, channel: str, data: Any):
        """Broadcast data to all subscribers of a channel."""
        self.latest_data[channel] = data
        
        if channel in self.subscriptions:
            message = json.dumps({
                "type": "data",
                "channel": channel,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            # Send to all subscribers
            disconnected = set()
            for client in self.subscriptions[channel]:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
            
            # Clean up disconnected clients
            self.subscriptions[channel] -= disconnected
    
    async def broadcast_to_all(self, data: Any):
        """Broadcast data to all connected clients."""
        message = json.dumps({
            "type": "broadcast",
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        self.clients -= disconnected
```

### 6.3 Dashboard Frontend (React)

```typescript
// Dashboard.tsx - Main dashboard component
import React, { useState, useEffect, useCallback } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

interface AttributionData {
  channel: string;
  attribution: number;
  confidence: number;
  model_breakdown: Record<string, { raw: number; weighted: number }>;
}

interface ForecastData {
  dates: string[];
  predicted: number[];
  lower_bound: number[];
  upper_bound: number[];
}

interface DashboardData {
  attribution: AttributionData[];
  forecasts: Record<string, ForecastData>;
  metrics: {
    total_spend: number;
    total_conversions: number;
    total_revenue: number;
    roas: number;
    cpa: number;
  };
  alerts: Array<{
    id: string;
    type: 'warning' | 'error' | 'info';
    message: string;
    timestamp: string;
  }>;
}

const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<string>('all');

  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:8765');

    websocket.onopen = () => {
      setConnected(true);
      websocket.send(JSON.stringify({ action: 'subscribe', channel: 'all' }));
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'data') {
        setData(message.data);
      }
    };

    websocket.onclose = () => {
      setConnected(false);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  const attributionChartData = {
    labels: data?.attribution.map(a => a.channel) || [],
    datasets: [
      {
        label: 'Attribution Weight',
        data: data?.attribution.map(a => a.attribution * 100) || [],
        backgroundColor: 'rgba(31, 119, 180, 0.8)',
      },
      {
        label: 'Confidence',
        data: data?.attribution.map(a => a.confidence * 100) || [],
        backgroundColor: 'rgba(46, 204, 113, 0.8)',
      },
    ],
  };

  const forecastChartData = selectedChannel !== 'all' && data?.forecasts[selectedChannel]
    ? {
        labels: data.forecasts[selectedChannel].dates,
        datasets: [
          {
            label: 'Predicted',
            data: data.forecasts[selectedChannel].predicted,
            borderColor: 'rgb(31, 119, 180)',
            backgroundColor: 'rgba(31, 119, 180, 0.1)',
            fill: true,
          },
          {
            label: 'Upper Bound',
            data: data.forecasts[selectedChannel].upper_bound,
            borderColor: 'rgba(31, 119, 180, 0.3)',
            borderDash: [5, 5],
            fill: false,
          },
          {
            label: 'Lower Bound',
            data: data.forecasts[selectedChannel].lower_bound,
            borderColor: 'rgba(31, 119, 180, 0.3)',
            borderDash: [5, 5],
            fill: '-1',
            backgroundColor: 'rgba(31, 119, 180, 0.05)',
          },
        ],
      }
    : null,
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">
          Marketing Attribution Dashboard
        </h1>
        <div className="flex items-center gap-2">
          <span
            className={`inline-block h-3 w-3 rounded-full ${
              connected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-600">
            {connected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-5">
        <Card>
          <CardHeader>Total Spend</CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              ${data?.metrics.total_spend.toLocaleString() ?? '-'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>Conversions</CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {data?.metrics.total_conversions.toLocaleString() ?? '-'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>Revenue</CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              ${data?.metrics.total_revenue.toLocaleString() ?? '-'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>ROAS</CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {data?.metrics.roas.toFixed(2) ?? '-'}x
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>CPA</CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              ${data?.metrics.cpa.toFixed(2) ?? '-'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="attribution">
        <TabsList>
          <TabsTrigger value="attribution">Attribution</TabsTrigger>
          <TabsTrigger value="forecasts">Forecasts</TabsTrigger>
          <TabsTrigger value="channels">Channels</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="attribution">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>Channel Attribution</CardHeader>
              <CardContent>
                <Bar data={attributionChartData} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>Attribution Distribution</CardHeader>
              <CardContent>
                <Pie
                  data={{
                    labels: data?.attribution.map(a => a.channel) || [],
                    datasets: [
                      {
                        data: data?.attribution.map(a => a.attribution * 100) || [],
                        backgroundColor: [
                          '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
                          '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                        ],
                      },
                    ],
                  }}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="forecasts">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <span>Channel Forecasts</span>
                <select
                  value={selectedChannel}
                  onChange={(e) => setSelectedChannel(e.target.value)}
                  className="rounded border px-2 py-1"
                >
                  <option value="all">All Channels</option>
                  {data?.attribution.map(a => (
                    <option key={a.channel} value={a.channel}>
                      {a.channel}
                    </option>
                  ))}
                </select>
              </div>
            </CardHeader>
            <CardContent>
              {forecastChartData && <Line data={forecastChartData} />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="channels">
          <Card>
            <CardHeader>Channel Details</CardHeader>
            <CardContent>
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Channel</th>
                    <th>Attribution</th>
                    <th>Confidence</th>
                    <th>Markov</th>
                    <th>Shapley</th>
                    <th>Deep Learning</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.attribution.map(a => (
                    <tr key={a.channel}>
                      <td>{a.channel}</td>
                      <td>{(a.attribution * 100).toFixed(1)}%</td>
                      <td>{(a.confidence * 100).toFixed(1)}%</td>
                      <td>
                        {(a.model_breakdown?.markov?.raw * 100 || 0).toFixed(1)}%
                      </td>
                      <td>
                        {(a.model_breakdown?.shapley?.raw * 100 || 0).toFixed(1)}%
                      </td>
                      <td>
                        {(a.model_breakdown?.deep_learning?.raw * 100 || 0).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts">
          <Card>
            <CardHeader>Active Alerts</CardHeader>
            <CardContent>
              {data?.alerts.map(alert => (
                <div
                  key={alert.id}
                  className={`mb-2 rounded p-3 ${
                    alert.type === 'error'
                      ? 'bg-red-100 text-red-800'
                      : alert.type === 'warning'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}
                >
                  <p className="font-medium">{alert.message}</p>
                  <p className="text-sm opacity-75">{alert.timestamp}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;
```

### 6.4 Real-time Data Pipeline

```python
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import aiokafka
import json
import logging

logger = logging.getLogger(__name__)

class RealTimeDataPipeline:
    """
    Streaming data pipeline for real-time attribution updates.
    
    Consumes events from Kafka, processes them through the attribution
    engine, and broadcasts updates to connected dashboard clients.
    """
    
    def __init__(
        self,
        kafka_bootstrap_servers: str = "localhost:9092",
        kafka_topic: str = "marketing-events",
        websocket_server: Optional[DashboardWebSocketServer] = None,
        attribution_engine: Optional["AttributionEngine"] = None,
    ):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.websocket_server = websocket_server
        self.attribution_engine = attribution_engine
        self.consumer: Optional[aiokafka.AIOKafkaConsumer] = None
        self._running = False
        self._event_buffer: list = []
        self._buffer_size = 100
        self._flush_interval = 5  # seconds
    
    async def start(self):
        """Start the streaming pipeline."""
        self.consumer = aiokafka.AIOKafkaConsumer(
            self.kafka_topic,
            bootstrap_servers=self.kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            group_id="attribution-pipeline",
        )
        await self.consumer.start()
        self._running = True
        
        logger.info(f"Started consuming from Kafka topic: {self.kafka_topic}")
        
        # Start processing tasks
        await asyncio.gather(
            self._consume_events(),
            self._periodic_flush(),
        )
    
    async def stop(self):
        """Stop the streaming pipeline."""
        self._running = False
        if self.consumer:
            await self.consumer.stop()
    
    async def _consume_events(self):
        """Consume events from Kafka."""
        try:
            async for msg in self.consumer:
                if not self._running:
                    break
                
                event = msg.value
                self._event_buffer.append(event)
                
                # Flush if buffer is full
                if len(self._event_buffer) >= self._buffer_size:
                    await self._flush_buffer()
        
        except Exception as e:
            logger.error(f"Error consuming events: {e}")
    
    async def _periodic_flush(self):
        """Periodically flush the event buffer."""
        while self._running:
            await asyncio.sleep(self._flush_interval)
            if self._event_buffer:
                await self._flush_buffer()
    
    async def _flush_buffer(self):
        """Process buffered events and broadcast updates."""
        if not self._event_buffer:
            return
        
        events = self._event_buffer.copy()
        self._event_buffer.clear()
        
        try:
            # Process events through attribution engine
            if self.attribution_engine:
                results = await self.attribution_engine.process_events(events)
                
                # Broadcast to dashboard clients
                if self.websocket_server:
                    await self.websocket_server.broadcast("attribution", results)
            
            # Update metrics
            metrics = self._calculate_metrics(events)
            if self.websocket_server:
                await self.websocket_server.broadcast("metrics", metrics)
        
        except Exception as e:
            logger.error(f"Error processing events: {e}")
    
    def _calculate_metrics(self, events: list) -> Dict[str, Any]:
        """Calculate real-time metrics from events."""
        total_cost = sum(e.get("cost", 0) for e in events)
        total_conversions = sum(1 for e in events if e.get("converted", False))
        total_revenue = sum(e.get("conversion_value", 0) for e in events)
        
        return {
            "total_spend": total_cost,
            "total_conversions": total_conversions,
            "total_revenue": total_revenue,
            "roas": total_revenue / total_cost if total_cost > 0 else 0,
            "cpa": total_cost / total_conversions if total_conversions > 0 else 0,
            "event_count": len(events),
            "timestamp": datetime.utcnow().isoformat(),
        }
```

---

## 7. Integration with Ad Platforms and CRM

### 7.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 INTEGRATION LAYER                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              API GATEWAY / LOAD BALANCER                  │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │              CONNECTOR FRAMEWORK                          │   │
│  │                                                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │ Google   │ │  Meta    │ │LinkedIn  │ │  Custom  │    │   │
│  │  │ Ads      │ │  Ads     │ │  Ads     │ │  APIs    │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  │                                                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │Salesforce│ │ HubSpot  │ │  GA4     │ │  Custom  │    │   │
│  │  │  CRM     │ │  CRM     │ │Analytics │ │  CRM     │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              OAUTH / AUTH MANAGER                         │   │
│  │  Token refresh, credential rotation, scope management     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              WEBHOOK HANDLER                              │   │
│  │  Real-time event ingestion from platforms                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 OAuth and Authentication Manager

```python
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import aiohttp
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OAuthToken:
    access_token: str
    refresh_token: Optional[str]
    expires_at: datetime
    token_type: str = "Bearer"
    scope: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at - timedelta(minutes=5)


class OAuthManager:
    """Manages OAuth tokens for all integrated platforms."""
    
    def __init__(self, token_store: Optional[Any] = None):
        self.token_store = token_store or {}
        self._refresh_locks: Dict[str, asyncio.Lock] = {}
    
    async def get_token(self, platform: str) -> Optional[OAuthToken]:
        """Get a valid token for a platform, refreshing if necessary."""
        token_data = self.token_store.get(platform)
        if not token_data:
            return None
        
        token = OAuthToken(**token_data)
        
        if token.is_expired:
            return await self._refresh_token(platform, token)
        
        return token
    
    async def _refresh_token(
        self,
        platform: str,
        token: OAuthToken,
    ) -> Optional[OAuthToken]:
        """Refresh an expired token."""
        if platform not in self._refresh_locks:
            self._refresh_locks[platform] = asyncio.Lock()
        
        async with self._refresh_locks[platform]:
            # Double-check after acquiring lock
            token_data = self.token_store.get(platform)
            if token_data:
                current_token = OAuthToken(**token_data)
                if not current_token.is_expired:
                    return current_token
            
            # Refresh based on platform
            refresh_handlers = {
                "google_ads": self._refresh_google_token,
                "meta_ads": self._refresh_meta_token,
                "salesforce": self._refresh_salesforce_token,
                "hubspot": self._refresh_hubspot_token,
            }
            
            handler = refresh_handlers.get(platform)
            if handler:
                new_token = await handler(token)
                if new_token:
                    self.token_store[platform] = {
                        "access_token": new_token.access_token,
                        "refresh_token": new_token.refresh_token,
                        "expires_at": new_token.expires_at.isoformat(),
                        "token_type": new_token.token_type,
                        "scope": new_token.scope,
                    }
                    return new_token
            
            return None
    
    async def _refresh_google_token(self, token: OAuthToken) -> Optional[OAuthToken]:
        """Refresh Google OAuth token."""
        # Implementation using Google OAuth2 refresh flow
        pass
    
    async def _refresh_meta_token(self, token: OAuthToken) -> Optional[OAuthToken]:
        """Refresh Meta OAuth token."""
        # Implementation using Meta's token refresh endpoint
        pass
    
    async def _refresh_salesforce_token(self, token: OAuthToken) -> Optional[OAuthToken]:
        """Refresh Salesforce OAuth token."""
        pass
    
    async def _refresh_hubspot_token(self, token: OAuthToken) -> Optional[OAuthToken]:
        """Refresh HubSpot OAuth token."""
        pass
```

### 7.3 Webhook Handler

```python
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import hmac
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

class WebhookHandler:
    """Handles incoming webhooks from ad platforms and CRMs."""
    
    def __init__(
        self,
        pipeline: RealTimeDataPipeline,
        secret_store: Optional[Dict[str, str]] = None,
    ):
        self.pipeline = pipeline
        self.secret_store = secret_store or {}
    
    async def handle_google_ads_webhook(self, request: Request):
        """Handle Google Ads webhook."""
        payload = await request.body()
        
        # Verify signature
        if not self._verify_signature("google_ads", payload, request):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        data = json.loads(payload)
        await self._process_event("google_ads", data)
        
        return {"status": "ok"}
    
    async def handle_meta_webhook(self, request: Request):
        """Handle Meta webhook."""
        payload = await request.body()
        
        if not self._verify_signature("meta_ads", payload, request):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        data = json.loads(payload)
        await self._process_event("meta_ads", data)
        
        return {"status": "ok"}
    
    async def handle_salesforce_webhook(self, request: Request):
        """Handle Salesforce Platform Events."""
        payload = await request.body()
        data = json.loads(payload)
        await self._process_event("salesforce", data)
        return {"status": "ok"}
    
    async def handle_hubspot_webhook(self, request: Request):
        """Handle HubSpot webhook."""
        payload = await request.body()
        data = json.loads(payload)
        await self._process_event("hubspot", data)
        return {"status": "ok"}
    
    def _verify_signature(
        self,
        platform: str,
        payload: bytes,
        request: Request,
    ) -> bool:
        """Verify webhook signature."""
        secret = self.secret_store.get(platform)
        if not secret:
            return True  # No secret configured, skip verification
        
        signature = request.headers.get("X-Hub-Signature-256", "")
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    async def _process_event(self, platform: str, data: Dict[str, Any]):
        """Process a webhook event and send to the pipeline."""
        event = {
            "platform": platform,
            "event_type": data.get("event_type", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        
        # Send to Kafka for processing
        await self.pipeline.send_event(event)


# FastAPI routes
@app.post("/webhooks/google-ads")
async def google_ads_webhook(request: Request):
    handler = WebhookHandler(pipeline=None)  # Inject actual pipeline
    return await handler.handle_google_ads_webhook(request)

@app.post("/webhooks/meta-ads")
async def meta_ads_webhook(request: Request):
    handler = WebhookHandler(pipeline=None)
    return await handler.handle_meta_ads_webhook(request)

@app.post("/webhooks/salesforce")
async def salesforce_webhook(request: Request):
    handler = WebhookHandler(pipeline=None)
    return await handler.handle_salesforce_webhook(request)

@app.post("/webhooks/hubspot")
async def hubspot_webhook(request: Request):
    handler = WebhookHandler(pipeline=None)
    return await handler.handle_hubspot_webhook(request)
```

### 7.4 Platform-Specific Integration Configurations

```python
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class PlatformConfig(BaseModel):
    """Configuration for a single platform integration."""
    platform: str
    enabled: bool = True
    credentials: Dict[str, str] = Field(default_factory=dict)
    sync_config: Dict[str, Any] = Field(default_factory=dict)
    webhook_secret: Optional[str] = None
    rate_limit: int = 10  # calls per second
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {
        "max_retries": 3,
        "backoff_factor": 2.0,
        "max_backoff": 60.0,
    })


class IntegrationConfig(BaseModel):
    """Master configuration for all platform integrations."""
    google_ads: PlatformConfig = Field(default_factory=lambda: PlatformConfig(
        platform="google_ads",
        sync_config={
            "customer_id": "123-456-7890",
            "developer_token": "",
            "login_customer_id": "",
            "sync_frequency_minutes": 15,
            "historical_days": 90,
            "fetch_conversions": True,
            "fetch_costs": True,
            "fetch_impressions": True,
        },
    ))
    meta_ads: PlatformConfig = Field(default_factory=lambda: PlatformConfig(
        platform="meta_ads",
        sync_config={
            "ad_account_id": "act_123456789",
            "sync_frequency_minutes": 15,
            "historical_days": 90,
            "fetch_conversions": True,
            "fetch_costs": True,
            "fetch_impressions": True,
        },
    ))
    linkedin_ads: PlatformConfig = Field(default_factory=lambda: PlatformConfig(
        platform="linkedin_ads",
        sync_config={
            "account_id": "123456",
            "sync_frequency_minutes": 30,
            "historical_days": 90,
        },
    ))
    salesforce: PlatformConfig = Field(default_factory=lambda: PlatformConfig(
        platform="salesforce",
        sync_config={
            "instance_url": "https://myinstance.salesforce.com",
            "sync_frequency_minutes": 60,
            "historical_days": 365,
            "fetch_opportunities": True,
            "fetch_leads": True,
            "fetch_activities": True,
        },
    ))
    hubspot: PlatformConfig = Field(default_factory=lambda: PlatformConfig(
        platform="hubspot",
        sync_config={
            "portal_id": "123456",
            "sync_frequency_minutes": 60,
            "historical_days": 365,
            "fetch_contacts": True,
            "fetch_deals": True,
            "fetch_engagements": True,
        },
    ))
    google_analytics: PlatformConfig = Field(default_factory=lambda: PlatformConfig(
        platform="google_analytics",
        sync_config={
            "property_id": "123456789",
            "sync_frequency_minutes": 30,
            "historical_days": 90,
            "fetch_sessions": True,
            "fetch_conversions": True,
            "fetch_events": True,
        },
    ))
```

---

## 8. Code Examples and Snippets

### 8.1 Complete Pipeline Example

```python
"""
Complete end-to-end example of the AI-powered marketing attribution system.
This example demonstrates how to orchestrate all agents together.
"""

import asyncio
from datetime import datetime, timedelta
from langchain_deepagents import DeepAgent
from langchain_deepagents.planner import PlannerConfig

async def run_attribution_pipeline():
    """Run the complete attribution pipeline."""
    
    # 1. Initialize connectors
    connectors = {
        "google_ads": GoogleAdsConnector(credentials={
            "customer_id": "123-456-7890",
            "access_token": "ya29...",
            "developer_token": "ABC123...",
        }),
        "meta_ads": MetaAdsConnector(credentials={
            "ad_account_id": "act_123456789",
            "access_token": "EAA...",
        }),
        "salesforce": SalesforceCRMConnector(credentials={
            "instance_url": "https://myinstance.salesforce.com",
            "access_token": "00D...",
        }),
    }
    
    # 2. Initialize agents
    data_agent = DataCollectionAgent(connectors=connectors)
    
    attribution_engine = AttributionEngine(
        markov_config={"order": 1, "smoothing": 0.01},
        shapley_config={"max_exact_channels": 10, "n_samples": 10000},
        deep_config={"embedding_dim": 64, "hidden_dim": 128},
    )
    
    predictive_agent = PredictiveAnalyticsAgent(
        forecaster=MarketingProphetForecaster(),
        predictor=MarketingXGBoostPredictor(),
        optimizer=BudgetOptimizationEngine(),
        llm=ChatOpenAI(model="gpt-4"),
    )
    
    reporting_agent = ReportingAgent(
        report_generator=AttributionReportGenerator(),
        llm=ChatOpenAI(model="gpt-4"),
    )
    
    # 3. Define date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=90)
    
    # 4. Collect data
    print("Step 1: Collecting data...")
    collection_result = await data_agent.collect(
        start_date=start_date,
        end_date=end_date,
    )
    print(f"  Collected {collection_result['total_normalized']} touchpoints")
    
    # 5. Build journeys
    print("Step 2: Building customer journeys...")
    journey_builder = JourneyBuilder()
    journeys = journey_builder.build_journeys(collection_result["touchpoints"])
    print(f"  Built {len(journeys)} journeys")
    
    # 6. Run attribution
    print("Step 3: Running attribution models...")
    attribution_results = await attribution_engine.compute(journeys)
    print(f"  Attribution complete for {len(attribution_results)} channels")
    
    # 7. Run predictions
    print("Step 4: Running predictive analytics...")
    feature_engineer = MarketingFeatureEngineer(attribution_results)
    features = feature_engineer.build_features(
        collection_result["touchpoints"],
        journeys,
        (start_date, end_date),
    )
    
    predictions = await predictive_agent.analyze(
        historical_data=features,
        forecast_horizon_days=30,
        total_budget=100000,
    )
    print("  Predictions complete")
    
    # 8. Generate report
    print("Step 5: Generating report...")
    report = await reporting_agent.generate_report(
        attribution_results=attribution_results,
        predictions=predictions,
        insights=predictions.get("insights"),
        format="markdown",
    )
    print("  Report generated")
    
    # 9. Save results
    output = {
        "session_id": str(uuid.uuid4()),
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "collection_summary": {
            "total_raw": collection_result["total_raw"],
            "total_normalized": collection_result["total_normalized"],
            "quality_score": collection_result["quality_report"]["quality_score"],
        },
        "attribution": attribution_results,
        "predictions": predictions,
        "report": report,
    }
    
    with open(f"attribution_results_{output['session_id']}.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\nPipeline complete! Results saved to attribution_results_{output['session_id']}.json")
    return output


if __name__ == "__main__":
    asyncio.run(run_attribution_pipeline())
```

### 8.2 LangChain DeepAgents Tool Registration

```python
from langchain_deepagents.tools import tool
from langchain_deepagents import DeepAgent

@tool
async def fetch_marketing_data(
    start_date: str,
    end_date: str,
    channels: list[str] = None,
) -> dict:
    """
    Fetch marketing touchpoint data from all connected platforms.
    
    Args:
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        channels: Optional list of channels to filter by
        
    Returns:
        Dictionary containing normalized touchpoints and metadata
    """
    # Implementation
    pass

@tool
async def compute_attribution(
    touchpoints: list[dict],
    models: list[str] = None,
) -> dict:
    """
    Compute multi-touch attribution using specified models.
    
    Args:
        touchpoints: List of normalized touchpoint dictionaries
        models: List of models to use ("markov", "shapley", "deep_learning")
        
    Returns:
        Dictionary with attribution results per channel
    """
    # Implementation
    pass

@tool
async def forecast_performance(
    historical_data: dict,
    forecast_days: int = 30,
) -> dict:
    """
    Forecast future marketing performance.
    
    Args:
        historical_data: Historical performance data
        forecast_days: Number of days to forecast
        
    Returns:
        Dictionary with forecasts and confidence intervals
    """
    # Implementation
    pass

@tool
async def optimize_budget(
    total_budget: float,
    attribution_results: dict,
    constraints: dict = None,
) -> dict:
    """
    Optimize budget allocation across channels.
    
    Args:
        total_budget: Total budget to allocate
        attribution_results: Current attribution results
        constraints: Optional budget constraints per channel
        
    Returns:
        Dictionary with recommended budget allocations
    """
    # Implementation
    pass

@tool
async def generate_report(
    attribution_results: dict,
    predictions: dict = None,
    format: str = "markdown",
) -> str:
    """
    Generate a comprehensive attribution report.
    
    Args:
        attribution_results: Attribution results
        predictions: Optional prediction results
        format: Output format ("markdown", "html", "json")
        
    Returns:
        Report content as a string
    """
    # Implementation
    pass

# Register tools with DeepAgent
tools = [
    fetch_marketing_data,
    compute_attribution,
    forecast_performance,
    optimize_budget,
    generate_report,
]

agent = DeepAgent(
    name="marketing-attribution-agent",
    tools=tools,
    planner_config=PlannerConfig(max_iterations=20),
)
```

### 8.3 Docker Compose Configuration

```yaml
version: "3.8"

services:
  # Main application
  attribution-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/attribution
      - REDIS_URL=redis://redis:6379/0
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_ADS_DEVELOPER_TOKEN=${GOOGLE_ADS_DEVELOPER_TOKEN}
      - META_ACCESS_TOKEN=${META_ACCESS_TOKEN}
      - SALESFORCE_ACCESS_TOKEN=${SALESFORCE_ACCESS_TOKEN}
    depends_on:
      - postgres
      - redis
      - kafka
    volumes:
      - ./data:/app/data
      - ./reports:/app/reports

  # WebSocket server for real-time dashboards
  websocket-server:
    build:
      context: .
      dockerfile: Dockerfile.websocket
    ports:
      - "8765:8765"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - redis
      - kafka

  # Stream processor
  stream-processor:
    build:
      context: .
      dockerfile: Dockerfile.processor
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - DATABASE_URL=postgresql://user:password@postgres:5432/attribution
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - kafka
      - postgres
      - redis

  # PostgreSQL database
  postgres:
    image: postgres:16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=attribution
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Kafka
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  # Qdrant vector database
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  # Dashboard frontend
  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8765

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

### 8.4 Environment Configuration

```bash
# .env.example

# Application
APP_ENV=production
APP_PORT=8000
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/attribution
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=marketing-events

# Vector DB
QDRANT_URL=http://localhost:6333

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Google Ads
GOOGLE_ADS_DEVELOPER_TOKEN=ABC123...
GOOGLE_ADS_CUSTOMER_ID=123-456-7890
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...

# Meta Ads
META_ACCESS_TOKEN=EAA...
META_AD_ACCOUNT_ID=act_123456789
META_APP_ID=...
META_APP_SECRET=...

# Salesforce
SALESFORCE_CLIENT_ID=...
SALESFORCE_CLIENT_SECRET=...
SALESFORCE_USERNAME=...
SALESFORCE_PASSWORD=...
SALESFORCE_SECURITY_TOKEN=...
SALESFORCE_INSTANCE_URL=https://myinstance.salesforce.com

# HubSpot
HUBSPOT_ACCESS_TOKEN=...
HUBSPOT_PORTAL_ID=123456

# Google Analytics
GA4_PROPERTY_ID=123456789
GA4_CREDENTIALS_PATH=/path/to/credentials.json

# Attribution Configuration
ATTRIBUTION_MARKOV_ORDER=1
ATTRIBUTION_MARKOV_SMOOTHING=0.01
ATTRIBUTION_SHAPLEY_MAX_EXACT=10
ATTRIBUTION_SHAPLEY_SAMPLES=10000
ATTRIBUTION_DEEP_EMBEDDING_DIM=64
ATTRIBUTION_DEEP_HIDDEN_DIM=128
ATTRIBUTION_DEEP_EPOCHS=50
ATTRIBUTION_ENSEMBLE_WEIGHTS={"markov": 0.3, "shapley": 0.3, "deep_learning": 0.4}

# Dashboard
DASHBOARD_REFRESH_INTERVAL_MS=5000
DASHBOARD_MAX_DATA_POINTS=1000
```

---

## 9. Testing Strategy

### 9.1 Testing Pyramid

```
┌─────────────────────────────────────────────────────────────────┐
│                    TESTING PYRAMID                               │
│                                                                  │
│                        ┌─────────┐                               │
│                        │   E2E   │  (5%)                         │
│                        │  Tests  │  Full pipeline validation     │
│                       ┌┴─────────┴┐                              │
│                       │ Integration│  (15%)                       │
│                       │   Tests    │  Agent interactions, APIs   │
│                      ┌┴────────────┴┐                            │
│                      │   Contract   │  (20%)                     │
│                      │    Tests     │  Schema validation          │
│                     ┌┴──────────────┴┐                           │
│                     │     Unit       │  (60%)                     │
│                     │    Tests       │  Functions, models, agents │
│                     └────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Unit Tests

```python
# tests/test_markov_attribution.py
import pytest
import numpy as np
from datetime import datetime, timedelta
from attribution.markov import MarkovChainAttribution
from models.journey import CustomerJourney, UnifiedTouchpoint, ChannelType, TouchpointType


class TestMarkovChainAttribution:
    """Unit tests for Markov Chain attribution model."""
    
    @pytest.fixture
    def sample_journeys(self):
        """Create sample journeys for testing."""
        journeys = []
        
        # Journey 1: Google -> Meta -> Conversion
        journeys.append(CustomerJourney(
            journey_id="j1",
            user_id="u1",
            touchpoints=[
                UnifiedTouchpoint(
                    touchpoint_id="t1", user_id="u1",
                    timestamp=datetime(2024, 1, 1), channel=ChannelType.PAID_SEARCH,
                    touchpoint_type=TouchpointType.CLICK, source_platform="google_ads",
                ),
                UnifiedTouchpoint(
                    touchpoint_id="t2", user_id="u1",
                    timestamp=datetime(2024, 1, 2), channel=ChannelType.PAID_SOCIAL,
                    touchpoint_type=TouchpointType.CLICK, source_platform="meta_ads",
                ),
            ],
            converted=True,
            conversion_value=100.0,
            conversion_timestamp=datetime(2024, 1, 3),
        ))
        
        # Journey 2: Google -> No conversion
        journeys.append(CustomerJourney(
            journey_id="j2",
            user_id="u2",
            touchpoints=[
                UnifiedTouchpoint(
                    touchpoint_id="t3", user_id="u2",
                    timestamp=datetime(2024, 1, 1), channel=ChannelType.PAID_SEARCH,
                    touchpoint_type=TouchpointType.CLICK, source_platform="google_ads",
                ),
            ],
            converted=False,
        ))
        
        # Journey 3: Meta -> Conversion
        journeys.append(CustomerJourney(
            journey_id="j3",
            user_id="u3",
            touchpoints=[
                UnifiedTouchpoint(
                    touchpoint_id="t4", user_id="u3",
                    timestamp=datetime(2024, 1, 1), channel=ChannelType.PAID_SOCIAL,
                    touchpoint_type=TouchpointType.CLICK, source_platform="meta_ads",
                ),
            ],
            converted=True,
            conversion_value=50.0,
            conversion_timestamp=datetime(2024, 1, 2),
        ))
        
        return journeys
    
    def test_fit_builds_transition_matrix(self, sample_journeys):
        """Test that fitting builds a valid transition matrix."""
        model = MarkovChainAttribution(order=1)
        model.fit(sample_journeys)
        
        assert model.transition_matrix is not None
        assert model.transition_matrix.shape[0] == model.transition_matrix.shape[1]
        
        # Check rows sum to 1
        row_sums = model.transition_matrix.sum(axis=1)
        np.testing.assert_array_almost_equal(row_sums, np.ones(len(row_sums)))
    
    def test_removal_effects_are_non_negative(self, sample_journeys):
        """Test that removal effects are non-negative."""
        model = MarkovChainAttribution(order=1)
        model.fit(sample_journeys)
        
        for channel, effect in model.removal_effects.items():
            assert effect >= 0, f"Removal effect for {channel} is negative: {effect}"
    
    def test_attribution_weights_sum_to_one(self, sample_journeys):
        """Test that attribution weights sum to 1."""
        model = MarkovChainAttribution(order=1)
        model.fit(sample_journeys)
        
        attribution = model.get_channel_attribution()
        total = sum(attribution.values())
        np.testing.assert_almost_equal(total, 1.0)
    
    def test_empty_journeys(self):
        """Test handling of empty journey list."""
        model = MarkovChainAttribution(order=1)
        model.fit([])
        
        assert model.transition_matrix is not None
        assert len(model.removal_effects) == 0
    
    def test_single_channel_journeys(self):
        """Test with journeys containing only one channel."""
        journeys = [
            CustomerJourney(
                journey_id="j1", user_id="u1",
                touchpoints=[
                    UnifiedTouchpoint(
                        touchpoint_id="t1", user_id="u1",
                        timestamp=datetime(2024, 1, 1),
                        channel=ChannelType.PAID_SEARCH,
                        touchpoint_type=TouchpointType.CLICK,
                        source_platform="google_ads",
                    ),
                ],
                converted=True,
                conversion_value=100.0,
            )
        ]
        
        model = MarkovChainAttribution(order=1)
        model.fit(journeys)
        
        attribution = model.get_channel_attribution()
        assert "paid_search" in attribution
        np.testing.assert_almost_equal(attribution["paid_search"], 1.0)


# tests/test_shapley_attribution.py
class TestShapleyAttribution:
    """Unit tests for Shapley Value attribution model."""
    
    @pytest.fixture
    def sample_journeys(self):
        """Create sample journeys for testing."""
        # Same fixture as above
        pass
    
    def test_shapley_values_sum_to_total_value(self, sample_journeys):
        """Test efficiency property: Shapley values sum to total value."""
        model = ShapleyAttribution(max_exact_channels=10)
        model.fit(sample_journeys)
        
        total_shapley = sum(model.shapley_values.values())
        total_value = sum(
            j.conversion_value for j in sample_journeys if j.converted
        )
        
        np.testing.assert_almost_equal(total_shapley, total_value)
    
    def test_symmetry_property(self):
        """Test that symmetric channels get equal Shapley values."""
        # Create journeys where two channels are perfectly symmetric
        pass
    
    def test_dummy_player_property(self):
        """Test that channels with no contribution get zero Shapley value."""
        pass
    
    def test_approximate_shapley_convergence(self):
        """Test that approximate Shapley converges with more samples."""
        pass


# tests/test_data_collection.py
class TestDataCollectionAgent:
    """Unit tests for data collection agent."""
    
    @pytest.fixture
    def mock_connector(self):
        """Create a mock connector."""
        pass
    
    @pytest.mark.asyncio
    async def test_collect_normalizes_touchpoints(self, mock_connector):
        """Test that collected touchpoints are properly normalized."""
        pass
    
    @pytest.mark.asyncio
    async def test_collect_handles_source_errors(self):
        """Test graceful handling of source errors."""
        pass
    
    @pytest.mark.asyncio
    async def test_collect_respects_rate_limits(self):
        """Test that rate limits are respected."""
        pass
    
    def test_quality_checker_detects_issues(self):
        """Test data quality checking."""
        pass


# tests/test_deep_attribution.py
class TestDeepAttributionModel:
    """Unit tests for deep learning attribution model."""
    
    def test_model_forward_pass(self):
        """Test model forward pass produces valid outputs."""
        model = DeepAttributionModel(
            n_channels=10,
            embedding_dim=32,
            hidden_dim=64,
        )
        
        batch_size = 4
        seq_length = 20
        
        channel_indices = torch.randint(0, 10, (batch_size, seq_length))
        mask = torch.ones(batch_size, seq_length)
        mask[:, 15:] = 0  # Padding
        
        conversion_prob, attribution_scores, attention_weights = model(
            channel_indices, mask
        )
        
        assert conversion_prob.shape == (batch_size,)
        assert attribution_scores.shape == (batch_size, seq_length)
        assert torch.all((conversion_prob >= 0) & (conversion_prob <= 1))
        assert torch.all(attribution_scores >= 0)
    
    def test_attribution_scores_sum_to_one(self):
        """Test that attribution scores sum to 1 per journey."""
        pass
    
    def test_model_training_reduces_loss(self):
        """Test that training reduces loss over epochs."""
        pass
```

### 9.3 Integration Tests

```python
# tests/integration/test_agent_pipeline.py
import pytest
import asyncio
from datetime import datetime, timedelta
from agents.data_collection import DataCollectionAgent
from agents.attribution import AttributionEngine
from agents.predictive import PredictiveAnalyticsAgent
from agents.reporting import ReportingAgent


class TestAgentPipeline:
    """Integration tests for the full agent pipeline."""
    
    @pytest.fixture
    def sample_touchpoints(self):
        """Create a comprehensive set of sample touchpoints."""
        touchpoints = []
        base_date = datetime(2024, 1, 1)
        
        for i in range(100):
            user_id = f"user_{i % 20}"
            date = base_date + timedelta(days=i % 30)
            
            touchpoints.append(UnifiedTouchpoint(
                touchpoint_id=f"tp_{i}",
                user_id=user_id,
                timestamp=date,
                channel=ChannelType.PAID_SEARCH if i % 3 == 0 else ChannelType.PAID_SOCIAL,
                touchpoint_type=TouchpointType.CLICK,
                source_platform="google_ads" if i % 3 == 0 else "meta_ads",
                cost=10.0 + i,
                conversion_value=100.0 if i % 5 == 0 else 0.0,
            ))
        
        return touchpoints
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, sample_touchpoints):
        """Test the complete pipeline from data collection to reporting."""
        # Data collection
        data_agent = DataCollectionAgent(connectors={})
        collection_result = await data_agent.collect(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )
        
        assert collection_result["total_normalized"] > 0
        
        # Attribution
        engine = AttributionEngine()
        journeys = JourneyBuilder().build_journeys(collection_result["touchpoints"])
        attribution_results = await engine.compute(journeys)
        
        assert len(attribution_results) > 0
        
        # Reporting
        report_agent = ReportingAgent(
            report_generator=AttributionReportGenerator(),
            llm=MockLLM(),
        )
        report = await report_agent.generate_report(
            attribution_results=attribution_results,
        )
        
        assert report["content"] is not None
        assert len(report["content"]) > 0
    
    @pytest.mark.asyncio
    async def test_agent_error_recovery(self):
        """Test that the pipeline recovers from agent errors."""
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_data_collection(self):
        """Test concurrent data collection from multiple sources."""
        pass


# tests/integration/test_api_endpoints.py
class TestAPIEndpoints:
    """Integration tests for API endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_trigger_attribution(self, client):
        """Test attribution trigger endpoint."""
        response = await client.post("/api/v1/attribution/run", json={
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "channels": ["paid_search", "paid_social"],
        })
        assert response.status_code == 202
    
    @pytest.mark.asyncio
    async def test_get_attribution_results(self, client):
        """Test getting attribution results."""
        response = await client.get("/api/v1/attribution/results/latest")
        assert response.status_code == 200
        data = response.json()
        assert "attribution" in data
        assert "channels" in data["attribution"]
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client):
        """Test WebSocket connection for real-time updates."""
        pass
```

### 9.4 End-to-End Tests

```python
# tests/e2e/test_full_system.py
import pytest
import asyncio
import aiohttp
from datetime import datetime, timedelta


class TestFullSystem:
    """End-to-end tests for the complete system."""
    
    @pytest.fixture
    async def system(self):
        """Start the full system for testing."""
        # Start all services
        # This would use docker-compose or similar in practice
        yield
        # Teardown
    
    @pytest.mark.asyncio
    async def test_complete_attribution_workflow(self, system):
        """Test the complete workflow from data collection to report delivery."""
        async with aiohttp.ClientSession() as session:
            # 1. Trigger data collection
            async with session.post(
                "http://localhost:8000/api/v1/attribution/run",
                json={
                    "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                },
            ) as resp:
                assert resp.status == 202
                job_id = (await resp.json())["job_id"]
            
            # 2. Poll for completion
            for _ in range(60):
                async with session.get(
                    f"http://localhost:8000/api/v1/attribution/status/{job_id}"
                ) as resp:
                    status = (await resp.json())["status"]
                    if status == "completed":
                        break
                    elif status == "failed":
                        pytest.fail("Attribution job failed")
                await asyncio.sleep(5)
            
            # 3. Get results
            async with session.get(
                f"http://localhost:8000/api/v1/attribution/results/{job_id}"
            ) as resp:
                results = await resp.json()
                assert "attribution" in results
                assert "predictions" in results
                assert "report" in results
            
            # 4. Verify dashboard is updated
            async with session.get(
                "http://localhost:8000/api/v1/dashboard/metrics"
            ) as resp:
                metrics = await resp.json()
                assert "total_spend" in metrics
                assert "total_conversions" in metrics
    
    @pytest.mark.asyncio
    async def test_real_time_updates(self, system):
        """Test real-time dashboard updates via WebSocket."""
        pass
    
    @pytest.mark.asyncio
    async def test_budget_optimization(self, system):
        """Test budget optimization endpoint."""
        pass
```

### 9.5 Performance Tests

```python
# tests/performance/test_attribution_performance.py
import pytest
import time
import asyncio
from typing import List


class TestAttributionPerformance:
    """Performance tests for attribution models."""
    
    @pytest.mark.benchmark
    def test_markov_attribution_performance(self, benchmark):
        """Benchmark Markov chain attribution."""
        journeys = generate_test_journeys(n_journeys=10000, n_channels=10)
        model = MarkovChainAttribution(order=1)
        
        result = benchmark(model.fit, journeys)
        assert result.stats.mean < 1.0  # Should complete in under 1 second
    
    @pytest.mark.benchmark
    def test_shapley_attribution_performance(self, benchmark):
        """Benchmark Shapley value computation."""
        journeys = generate_test_journeys(n_journeys=1000, n_channels=8)
        model = ShapleyAttribution(max_exact_channels=10)
        
        result = benchmark(model.fit, journeys)
        assert result.stats.mean < 10.0  # Should complete in under 10 seconds
    
    @pytest.mark.benchmark
    def test_deep_model_inference_performance(self, benchmark):
        """Benchmark deep learning model inference."""
        model = DeepAttributionModel(n_channels=20)
        dataset = generate_test_dataset(n_samples=1000)
        
        result = benchmark(model.get_channel_attribution, dataset)
        assert result.stats.mean < 5.0
    
    @pytest.mark.asyncio
    async def test_data_collection_throughput(self):
        """Test data collection throughput."""
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self):
        """Test API under concurrent load."""
        pass


def generate_test_journeys(n_journeys: int, n_channels: int) -> List[CustomerJourney]:
    """Generate test journeys for benchmarking."""
    import random
    from datetime import datetime, timedelta
    
    channels = list(ChannelType)[:n_channels]
    journeys = []
    
    for i in range(n_journeys):
        n_touchpoints = random.randint(1, 10)
        touchpoints = []
        
        for j in range(n_touchpoints):
            touchpoints.append(UnifiedTouchpoint(
                touchpoint_id=f"tp_{i}_{j}",
                user_id=f"user_{i}",
                timestamp=datetime(2024, 1, 1) + timedelta(hours=j),
                channel=random.choice(channels),
                touchpoint_type=TouchpointType.CLICK,
                source_platform="test",
                cost=random.uniform(1, 100),
            ))
        
        journeys.append(CustomerJourney(
            journey_id=f"j_{i}",
            user_id=f"user_{i}",
            touchpoints=touchpoints,
            converted=random.random() > 0.5,
            conversion_value=random.uniform(50, 500) if random.random() > 0.5 else 0,
        ))
    
    return journeys
```

### 9.6 Test Data Fixtures

```python
# tests/conftest.py
import pytest
from datetime import datetime, timedelta
from typing import List
import random


@pytest.fixture
def sample_touchpoints() -> List[UnifiedTouchpoint]:
    """Generate sample touchpoints for testing."""
    touchpoints = []
    base_date = datetime(2024, 1, 1)
    channels = [ChannelType.PAID_SEARCH, ChannelType.PAID_SOCIAL, ChannelType.EMAIL]
    
    for i in range(500):
        touchpoints.append(UnifiedTouchpoint(
            touchpoint_id=f"tp_{i}",
            user_id=f"user_{i % 50}",
            timestamp=base_date + timedelta(hours=i),
            channel=channels[i % len(channels)],
            touchpoint_type=TouchpointType.CLICK if i % 2 == 0 else TouchpointType.IMPRESSION,
            source_platform=["google_ads", "meta_ads", "mailchimp"][i % 3],
            cost=random.uniform(1, 50),
            conversion_value=random.uniform(0, 200) if i % 10 == 0 else 0,
            metadata={
                "impressions": random.randint(100, 10000),
                "clicks": random.randint(1, 100),
            },
        ))
    
    return touchpoints


@pytest.fixture
def sample_journeys(sample_touchpoints) -> List[CustomerJourney]:
    """Generate sample journeys from touchpoints."""
    builder = JourneyBuilder()
    return builder.build_journeys(sample_touchpoints)


@pytest.fixture
def sample_attribution_results() -> Dict[str, Dict]:
    """Generate sample attribution results."""
    return {
        "paid_search": {
            "ensemble_attribution": 0.35,
            "confidence": 0.85,
            "model_breakdown": {
                "markov": {"raw": 0.30, "weighted": 0.105, "weight": 0.35},
                "shapley": {"raw": 0.35, "weighted": 0.1225, "weight": 0.35},
                "deep_learning": {"raw": 0.40, "weighted": 0.14, "weight": 0.40},
            },
        },
        "paid_social": {
            "ensemble_attribution": 0.25,
            "confidence": 0.75,
            "model_breakdown": {
                "markov": {"raw": 0.20, "weighted": 0.07, "weight": 0.35},
                "shapley": {"raw": 0.25, "weighted": 0.0875, "weight": 0.35},
                "deep_learning": {"raw": 0.30, "weighted": 0.12, "weight": 0.40},
            },
        },
        "email": {
            "ensemble_attribution": 0.15,
            "confidence": 0.65,
            "model_breakdown": {
                "markov": {"raw": 0.15, "weighted": 0.0525, "weight": 0.35},
                "shapley": {"raw": 0.15, "weighted": 0.0525, "weight": 0.35},
                "deep_learning": {"raw": 0.15, "weighted": 0.06, "weight": 0.40},
            },
        },
    }


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    from unittest.mock import AsyncMock, MagicMock
    
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value=MagicMock(
        content="This is a test response from the mock LLM."
    ))
    return mock
```

### 9.7 CI/CD Pipeline Configuration

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: |
          pytest tests/unit -v --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: password
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
      kafka:
        image: confluentinc/cp-kafka:7.5.0
        ports:
          - 9092:9092
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run integration tests
        run: pytest tests/integration -v
        env:
          DATABASE_URL: postgresql://postgres:password@localhost:5432/postgres
          REDIS_URL: redis://localhost:6379/0

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v4
      - name: Run E2E tests
        run: |
          docker-compose up -d
          sleep 30
          pytest tests/e2e -v
          docker-compose down

  performance-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run performance tests
        run: pytest tests/performance -v --benchmark-only
```

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **Touchpoint** | Any interaction between a customer and a marketing channel |
| **Journey** | The sequence of touchpoints leading to a conversion |
| **Attribution** | The process of assigning credit to touchpoints for conversions |
| **Markov Chain** | A stochastic model describing sequences of events where probability depends only on the current state |
| **Shapley Value** | A solution concept in cooperative game theory that fairly distributes payoffs among players |
| **Removal Effect** | The decrease in conversions when a channel is removed from the journey |
| **Ensemble** | A combination of multiple models to improve prediction accuracy |
| **ROAS** | Return on Ad Spend - revenue generated per dollar spent on advertising |
| **CPA** | Cost Per Acquisition - cost to acquire one customer |
| **DeepAgents** | LangChain's framework for building complex multi-agent systems |

## Appendix B: References

1. Anderl, E., et al. (2016). "Mapping the Customer Journey: A Graph-Based Framework for Online Attribution Modeling."
2. Shapley, L. S. (1953). "A Value for n-Person Games."
3. Zhang, Y., et al. (2014). "Multi-Touch Attribution in Online Advertising with Survival Theory."
4. LangChain Documentation: https://python.langchain.com/
5. DeepAgents Documentation: https://github.com/langchain-ai/deepagents

---

*Document prepared by Ahmed Hassan*  
*Last updated: 2026-10-01*</longcat_think>
