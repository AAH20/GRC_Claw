# AI-Powered Analytics & Attribution Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Stack:** LangChain DeepAgents, Python 3.11+, PostgreSQL, Redis, Apache Kafka, React/Next.js

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Data Collection Agent](#2-data-collection-agent)
3. [Attribution Engine](#3-attribution-engine)
4. [Predictive Analytics Agent](#4-predictive-analytics-agent)
5. [Reporting Agent](#5-reporting-agent)
6. [Real-Time Dashboards](#6-real-time-dashboards)
7. [Ad Platform & CRM Integration](#7-ad-platform--crm-integration)
8. [Code Examples & Snippets](#8-code-examples--snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Design

The system uses a **multi-agent orchestration pattern** with LangChain DeepAgents. A central **Analytics Orchestrator** coordinates four specialized sub-agents, each with its own toolset, memory, and LLM configuration.

```
┌─────────────────────────────────────────────────────────────┐
│                  Analytics Orchestrator                      │
│  (DeepAgent with planning, routing, and aggregation)         │
├──────────┬──────────┬───────────────┬───────────────────────┤
│          │          │               │                       │
│  Data    │  Attribution│  Predictive │  Reporting            │
│  Collector│  Engine    │  Analytics  │  Agent                │
│  Agent   │  Agent     │  Agent      │                       │
├──────────┼──────────┼───────────────┼───────────────────────┤
│ Tools:   │ Tools:    │ Tools:       │ Tools:                │
│ - API    │ - Markov  │ - Forecast   │ - Chart gen           │
│   fetch  │   model   │   model     │ - PDF export          │
│ - ETL    │ - Shapley │ - Anomaly    │ - Slack/Email         │
│ - Clean  │   value   │   detection │ - Dashboard API       │
│ - Store  │ - DL model│ - LTV pred   │ - Natural lang       │
│          │           │   (XGBoost)  │   query               │
└──────────┴──────────┴───────────────┴───────────────────────┘
         │          │               │              │
         ▼          ▼               ▼              ▼
   ┌──────────────────────────────────────────────────┐
   │              Shared Infrastructure                │
   │  PostgreSQL │ Redis │ Kafka │ S3 │ MLflow        │
   └──────────────────────────────────────────────────┘
```

### 1.2 Agent Definitions

```python
# agents/orchestrator.py
from langchain_deepagents import DeepAgent, DeepAgentConfig
from langchain_deepagents.tools import Tool
from langchain_deepagents.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

class AnalyticsOrchestrator(DeepAgent):
    """
    Central orchestrator that routes queries to specialized agents,
    aggregates results, and maintains conversation context.
    """
    
    def __init__(self):
        config = DeepAgentConfig(
            name="analytics_orchestrator",
            llm=ChatOpenAI(model="gpt-4o", temperature=0.1),
            memory=ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                max_token_limit=8000
            ),
            system_prompt=self._build_system_prompt(),
            sub_agents=[
                DataCollectorAgent(),
                AttributionEngineAgent(),
                PredictiveAnalyticsAgent(),
                ReportingAgent(),
            ],
            max_iterations=10,
            verbose=True,
        )
        super().__init__(config)
    
    def _build_system_prompt(self) -> str:
        return """You are the Analytics Orchestrator for a marketing intelligence system.
        
Your responsibilities:
1. Route user queries to the appropriate specialized agent
2. Aggregate results from multiple agents when needed
3. Maintain context across multi-turn conversations
4. Handle follow-up questions by referencing prior agent outputs

Routing rules:
- Data questions (metrics, dimensions, segments) → DataCollectorAgent
- Attribution questions (channel contribution, ROAS, credit) → AttributionEngineAgent
- Forecasting/prediction questions → PredictiveAnalyticsAgent
- Report/dashboard questions → ReportingAgent

Always confirm the user's intent before dispatching to an agent."""
```

### 1.3 Shared Memory & State Management

```python
# agents/shared_state.py
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import redis
import json

@dataclass
class AnalyticsSession:
    """Shared state across all agents in a session."""
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    data_context: dict = field(default_factory=dict)
    attribution_results: dict = field(default_factory=dict)
    predictions: dict = field(default_factory=dict)
    reports: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "data_context": self.data_context,
            "attribution_results": self.attribution_results,
            "predictions": self.predictions,
            "reports": self.reports,
        }

class SessionManager:
    """Manages agent sessions with Redis for persistence."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl = 3600 * 24  # 24 hours
    
    def get_or_create(self, session_id: str, user_id: str) -> AnalyticsSession:
        key = f"analytics_session:{session_id}"
        data = self.redis.get(key)
        if data:
            return AnalyticsSession(**json.loads(data))
        session = AnalyticsSession(session_id=session_id, user_id=user_id)
        self.save(session)
        return session
    
    def save(self, session: AnalyticsSession):
        key = f"analytics_session:{session.session_id}"
        self.redis.setex(key, self.ttl, json.dumps(session.to_dict()))
```

---

## 2. Data Collection Agent

### 2.1 Architecture

The Data Collector Agent is responsible for:
- Fetching data from multiple sources (ad platforms, CRM, web analytics)
- Cleaning, normalizing, and deduplicating data
- Storing processed data in the analytics warehouse
- Answering ad-hoc data queries

### 2.2 Implementation

```python
# agents/data_collector.py
from langchain_deepagents import DeepAgent, DeepAgentConfig
from langchain_deepagents.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import asyncpg
import aiohttp

class DataCollectorAgent(DeepAgent):
    """
    Specialized agent for marketing data collection, cleaning, and querying.
    Connects to ad platforms, CRM, and web analytics sources.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        config = DeepAgentConfig(
            name="data_collector",
            llm=ChatOpenAI(model="gpt-4o", temperature=0.0),
            tools=[
                self.fetch_ad_data,
                self.fetch_crm_data,
                self.fetch_web_analytics,
                self.query_warehouse,
                self.clean_data,
                self.get_data_summary,
            ],
            system_prompt="""You are the Data Collector Agent.
            
You collect, clean, and query marketing data from multiple sources:
- Ad platforms: Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads
- CRM: Salesforce, HubSpot
- Web analytics: Google Analytics 4, Mixpanel, Amplitude

Always:
1. Validate date ranges before querying
2. Handle API rate limits gracefully
3. Log all data fetches for audit trails
4. Return data in structured format (tables, not raw JSON)
5. Flag data quality issues (missing values, duplicates, anomalies)""",
            verbose=True,
        )
        super().__init__(config)
    
    @tool
    async def fetch_ad_data(
        self,
        platform: str,
        start_date: str,
        end_date: str,
        metrics: Optional[list[str]] = None,
        dimensions: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Fetch advertising data from specified platform.
        
        Args:
            platform: One of 'google_ads', 'meta_ads', 'linkedin_ads', 'tiktok_ads'
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            metrics: List of metrics to fetch (e.g., ['impressions', 'clicks', 'spend', 'conversions'])
            dimensions: List of dimensions to group by (e.g., ['campaign', 'ad_group', 'date'])
        
        Returns:
            DataFrame with requested ad data
        """
        fetchers = {
            "google_ads": self._fetch_google_ads,
            "meta_ads": self._fetch_meta_ads,
            "linkedin_ads": self._fetch_linkedin_ads,
            "tiktok_ads": self._fetch_tiktok_ads,
        }
        
        if platform not in fetchers:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Default metrics if not specified
        if metrics is None:
            metrics = ["impressions", "clicks", "spend", "conversions", "revenue"]
        if dimensions is None:
            dimensions = ["date", "campaign"]
        
        df = await fetchers[platform](start_date, end_date, metrics, dimensions)
        
        # Store raw data for audit
        await self._store_raw_data(platform, df, start_date, end_date)
        
        return df
    
    @tool
    async def fetch_crm_data(
        self,
        crm_source: str,
        start_date: str,
        end_date: str,
        object_type: str = "opportunities",
    ) -> pd.DataFrame:
        """
        Fetch CRM data (leads, opportunities, contacts).
        
        Args:
            crm_source: 'salesforce' or 'hubspot'
            start_date: Start date
            end_date: End date
            object_type: 'leads', 'opportunities', 'contacts', 'accounts'
        """
        if crm_source == "salesforce":
            return await self._fetch_salesforce(object_type, start_date, end_date)
        elif crm_source == "hubspot":
            return await self._fetch_hubspot(object_type, start_date, end_date)
        raise ValueError(f"Unsupported CRM: {crm_source}")
    
    @tool
    async def fetch_web_analytics(
        self,
        source: str,
        start_date: str,
        end_date: str,
        metrics: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Fetch web analytics data.
        
        Args:
            source: 'ga4', 'mixpanel', 'amplitude'
            start_date: Start date
            end_date: End date
            metrics: Metrics to fetch
        """
        fetchers = {
            "ga4": self._fetch_ga4,
            "mixpanel": self._fetch_mixpanel,
            "amplitude": self._fetch_amplitude,
        }
        if source not in fetchers:
            raise ValueError(f"Unsupported analytics source: {source}")
        return await fetchers[source](start_date, end_date, metrics)
    
    @tool
    async def query_warehouse(
        self,
        query: str,
        params: Optional[dict] = None,
    ) -> pd.DataFrame:
        """
        Execute a read-only SQL query against the analytics warehouse.
        
        Args:
            query: SQL SELECT query (read-only)
            params: Query parameters for parameterized queries
        
        Returns:
            Query results as DataFrame
        """
        # Safety: only allow SELECT queries
        normalized = query.strip().upper()
        if not normalized.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        
        async with self.db_pool.acquire() as conn:
            records = await conn.fetch(query, *(params or {}).values())
            return pd.DataFrame([dict(r) for r in records])
    
    @tool
    async def clean_data(
        self,
        df: pd.DataFrame,
        operations: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Clean and normalize a DataFrame.
        
        Args:
            df: Input DataFrame
            operations: List of cleaning operations to apply.
                       Options: 'dedupe', 'fill_na', 'normalize', 'remove_outliers',
                               'standardize_currency', 'parse_dates'
        
        Returns:
            Cleaned DataFrame
        """
        if operations is None:
            operations = ["dedupe", "fill_na", "normalize", "parse_dates"]
        
        original_len = len(df)
        cleaning_log = []
        
        if "dedupe" in operations:
            df = df.drop_duplicates()
            cleaning_log.append(f"Removed {original_len - len(df)} duplicate rows")
        
        if "fill_na" in operations:
            # Fill numeric with 0, categorical with 'unknown'
            for col in df.columns:
                if df[col].dtype in ['float64', 'int64']:
                    df[col] = df[col].fillna(0)
                else:
                    df[col] = df[col].fillna("unknown")
            cleaning_log.append("Filled NA values")
        
        if "normalize" in operations:
            # Standardize column names
            df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
            cleaning_log.append("Normalized column names")
        
        if "parse_dates" in operations:
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except (ValueError, TypeError):
                        pass
            cleaning_log.append("Parsed date columns")
        
        if "remove_outliers" in operations:
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            for col in numeric_cols:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 3 * iqr
                upper = q3 + 3 * iqr
                df = df[(df[col] >= lower) | (df[col].isna())]
                df = df[(df[col] <= upper) | (df[col].isna())]
            cleaning_log.append("Removed outliers (3*IQR rule)")
        
        if "standardize_currency" in operations:
            # Convert all monetary values to USD
            currency_cols = [c for c in df.columns if 'spend' in c or 'revenue' in c or 'cost' in c]
            for col in currency_cols:
                if 'currency' in df.columns:
                    df = self._convert_to_usd(df, col, 'currency')
            cleaning_log.append("Standardized currencies to USD")
        
        # Store cleaning metadata
        df.attrs['cleaning_log'] = cleaning_log
        return df
    
    @tool
    async def get_data_summary(self, df: pd.DataFrame) -> dict:
        """
        Generate a summary of a DataFrame for quick understanding.
        
        Returns:
            Dictionary with row count, column info, date range, and basic stats
        """
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "null_counts": df.isnull().sum().to_dict(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1e6,
        }
        
        # Date range if date columns exist
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        if date_cols:
            summary["date_range"] = {
                col: {"min": str(df[col].min()), "max": str(df[col].max())}
                for col in date_cols
            }
        
        # Numeric summaries
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            summary["numeric_summary"] = df[numeric_cols].describe().to_dict()
        
        return summary
    
    # --- Private helper methods ---
    
    async def _fetch_google_ads(
        self, start: str, end: str, metrics: list[str], dimensions: list[str]
    ) -> pd.DataFrame:
        """Fetch data from Google Ads API."""
        from google.ads.googleads.client import GoogleAdsClient
        
        client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        service = client.get_service("GoogleAdsService")
        
        # Build GAQL query
        dim_str = ", ".join(dimensions)
        met_str = ", ".join(metrics)
        query = f"""
            SELECT {dim_str}, {met_str}
            FROM campaign
            WHERE segments.date BETWEEN '{start}' AND '{end}'
        """
        
        response = service.search_stream(customer_id="1234567890", query=query)
        
        rows = []
        for batch in response:
            for row in batch.results:
                row_data = {}
                for dim in dimensions:
                    row_data[dim] = self._extract_nested_attr(row, dim)
                for met in metrics:
                    row_data[met] = self._extract_nested_attr(row, met)
                rows.append(row_data)
        
        return pd.DataFrame(rows)
    
    async def _fetch_meta_ads(
        self, start: str, end: str, metrics: list[str], dimensions: list[str]
    ) -> pd.DataFrame:
        """Fetch data from Meta Marketing API."""
        import aiohttp
        
        access_token = await self._get_meta_token()
        ad_account_id = "act_1234567890"
        
        url = f"https://graph.facebook.com/v18.0/{ad_account_id}/insights"
        params = {
            "access_token": access_token,
            "time_range": json.dumps({"since": start, "until": end}),
            "fields": ",".join(metrics),
            "level": "campaign",
            "time_increment": 1,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
        
        rows = []
        for item in data.get("data", []):
            row = {}
            for key, value in item.items():
                row[key] = value
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    async def _store_raw_data(self, source: str, df: pd.DataFrame, start: str, end: str):
        """Store raw data to S3 for audit trail."""
        import boto3
        
        s3 = boto3.client("s3")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        key = f"raw_data/{source}/{start}_{end}_{timestamp}.parquet"
        
        # Write to buffer and upload
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        buffer.seek(0)
        s3.upload_fileobj(buffer, "analytics-raw-data", key)
    
    def _extract_nested_attr(self, obj, attr_path: str):
        """Extract nested attribute from protobuf-like object."""
        parts = attr_path.split(".")
        current = obj
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        return current
    
    async def _get_meta_token(self) -> str:
        """Retrieve Meta access token from secrets manager."""
        import boto3
        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId="meta-ads-token")
        return json.loads(response["SecretString"])["access_token"]
    
    def _convert_to_usd(self, df: pd.DataFrame, amount_col: str, currency_col: str) -> pd.DataFrame:
        """Convert amounts to USD using exchange rates."""
        # Simplified: in production, use a proper FX API
        rates = {"EUR": 1.08, "GBP": 1.27, "JPY": 0.0067, "CAD": 0.74}
        df[f"{amount_col}_usd"] = df.apply(
            lambda row: row[amount_col] * rates.get(row[currency_col], 1.0), axis=1
        )
        return df
```

### 2.3 Data Pipeline (Airflow DAG)

```python
# dags/marketing_data_pipeline.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "analytics",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["analytics@company.com"],
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "marketing_data_pipeline",
    default_args=default_args,
    description="Daily marketing data collection and processing",
    schedule_interval="0 6 * * *",  # 6 AM daily
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["marketing", "analytics"],
) as dag:
    
    # Extract tasks
    extract_google_ads = PythonOperator(
        task_id="extract_google_ads",
        python_callable=extract_google_ads_task,
    )
    
    extract_meta_ads = PythonOperator(
        task_id="extract_meta_ads",
        python_callable=extract_meta_ads_task,
    )
    
    extract_crm = PythonOperator(
        task_id="extract_crm",
        python_callable=extract_crm_task,
    )
    
    extract_ga4 = PythonOperator(
        task_id="extract_ga4",
        python_callable=extract_ga4_task,
    )
    
    # Transform tasks
    clean_and_normalize = PythonOperator(
        task_id="clean_and_normalize",
        python_callable=clean_and_normalize_task,
    )
    
    # Load to warehouse
    load_to_warehouse = PostgresOperator(
        task_id="load_to_warehouse",
        sql="sql/load_marketing_data.sql",
    )
    
    # Data quality checks
    run_quality_checks = PythonOperator(
        task_id="run_quality_checks",
        python_callable=run_data_quality_checks,
    )
    
    # Dependencies
    [extract_google_ads, extract_meta_ads, extract_crm, extract_ga4] >> clean_and_normalize >> load_to_warehouse >> run_quality_checks
```

---

## 3. Attribution Engine

### 3.1 Architecture

The attribution engine implements three models, selectable based on data availability and business requirements:

| Model | Data Requirements | Complexity | Use Case |
|-------|------------------|------------|----------|
| **Markov Chains** | User-level journey data | Medium | Multi-touch, probabilistic |
| **Shapley Value** | Channel-level conversion data | Low-Medium | Fair credit distribution |
| **Deep Learning (LSTM/Transformer)** | Large-scale journey data | High | Complex, non-linear patterns |

### 3.2 Markov Chain Attribution

```python
# attribution/markov_chain.py
import numpy as np
import pandas as pd
from collections import defaultdict
from typing import Dict, List, Tuple
import networkx as nx

class MarkovChainAttribution:
    """
    Markov Chain-based multi-touch attribution model.
    
    Models the customer journey as a state transition process.
    Removal effect: measures how conversions drop if a channel is removed.
    """
    
    def __init__(self, order: int = 1):
        """
        Args:
            order: Markov order (1 = first-order, depends only on previous state)
        """
        self.order = order
        self.transition_matrix = None
        self.states = []
        self.removal_effects = {}
        self.conversion_rates = {}
    
    def fit(self, journeys: List[List[str]], conversions: List[int]):
        """
        Fit the Markov model on journey data.
        
        Args:
            journeys: List of channel sequences, e.g.,
                     [['google_ads', 'email', 'direct'],
                      ['meta_ads', 'google_ads', 'direct']]
            conversions: Binary list indicating conversion (1) or not (0)
        """
        # Define states: channels + 'Start' + 'Conversion' + 'Null'
        all_channels = set()
        for journey in journeys:
            all_channels.update(journey)
        
        self.states = ['Start'] + sorted(all_channels) + ['Conversion', 'Null']
        state_idx = {s: i for i, s in enumerate(self.states)}
        n_states = len(self.states)
        
        # Build transition count matrix
        transition_counts = np.zeros((n_states, n_states))
        
        for journey, converted in zip(journeys, conversions):
            # Add Start state
            prev_state = 'Start'
            
            for channel in journey:
                curr_state = channel
                transition_counts[state_idx[prev_state]][state_idx[curr_state]] += 1
                prev_state = curr_state
            
            # Final transition
            if converted:
                transition_counts[state_idx[prev_state]][state_idx['Conversion']] += 1
            else:
                transition_counts[state_idx[prev_state]][state_idx['Null']] += 1
        
        # Convert counts to probabilities
        self.transition_matrix = np.zeros((n_states, n_states))
        for i in range(n_states):
            row_sum = transition_counts[i].sum()
            if row_sum > 0:
                self.transition_matrix[i] = transition_counts[i] / row_sum
        
        # Calculate removal effects
        self._calculate_removal_effects(state_idx)
        
        return self
    
    def _calculate_removal_effects(self, state_idx: Dict[str, int]):
        """
        Calculate removal effect for each channel.
        Removal effect = (baseline_conversions - conversions_without_channel) / baseline_conversions
        """
        baseline_conversion = self._calculate_conversion_rate(
            self.transition_matrix, state_idx
        )
        
        for channel in state_idx:
            if channel in ['Start', 'Conversion', 'Null']:
                continue
            
            # Create modified transition matrix with channel removed
            modified_matrix = self.transition_matrix.copy()
            idx = state_idx[channel]
            
            # Remove transitions to this channel (redirect to self-loop)
            for i in range(len(self.states)):
                if i != idx:
                    modified_matrix[i][idx] = 0
                    # Redistribute probability proportionally
                    row_sum = modified_matrix[i].sum()
                    if row_sum > 0:
                        modified_matrix[i] = modified_matrix[i] / row_sum
            
            modified_conversion = self._calculate_conversion_rate(
                modified_matrix, state_idx
            )
            
            if baseline_conversion > 0:
                self.removal_effects[channel] = (
                    (baseline_conversion - modified_conversion) / baseline_conversion
                )
            else:
                self.removal_effects[channel] = 0.0
    
    def _calculate_conversion_rate(
        self, matrix: np.ndarray, state_idx: Dict[str, int]
    ) -> float:
        """
        Calculate probability of reaching 'Conversion' from 'Start'
        using absorbing Markov chain analysis.
        """
        n = len(self.states)
        start_idx = state_idx['Start']
        conv_idx = state_idx['Conversion']
        null_idx = state_idx['Null']
        
        # Transient states (all except Conversion and Null)
        transient_states = [i for i in range(n) if i not in [conv_idx, null_idx]]
        transient_idx_map = {old: new for new, old in enumerate(transient_states)}
        
        if start_idx not in transient_idx_map:
            return 0.0
        
        # Q matrix: transitions among transient states
        Q = matrix[np.ix_(transient_states, transient_states)]
        
        # R matrix: transitions from transient to absorbing
        absorbing = [conv_idx, null_idx]
        R = matrix[np.ix_(transient_states, absorbing)]
        
        # Fundamental matrix: N = (I - Q)^(-1)
        I = np.eye(len(transient_states))
        try:
            N = np.linalg.inv(I - Q)
        except np.linalg.LinAlgError:
            return 0.0
        
        # Absorption probabilities: B = N * R
        B = N @ R
        
        # Conversion probability from Start
        start_transient = transient_idx_map[start_idx]
        conv_absorbing = absorbing.index(conv_idx)
        
        return B[start_transient, conv_absorbing]
    
    def get_attribution(self) -> pd.DataFrame:
        """
        Get attribution results as a DataFrame.
        
        Returns:
            DataFrame with columns: channel, removal_effect, attribution_credit
        """
        total_removal = sum(self.removal_effects.values())
        
        results = []
        for channel, effect in self.removal_effects.items():
            credit = effect / total_removal if total_removal > 0 else 0
            results.append({
                "channel": channel,
                "removal_effect": effect,
                "attribution_credit": credit,
                "attribution_credit_pct": f"{credit * 100:.1f}%",
            })
        
        df = pd.DataFrame(results)
        df = df.sort_values("attribution_credit", ascending=False)
        return df
    
    def plot_journey_graph(self) -> nx.DiGraph:
        """Generate a directed graph of the journey for visualization."""
        G = nx.DiGraph()
        
        for i, from_state in enumerate(self.states):
            for j, to_state in enumerate(self.states):
                prob = self.transition_matrix[i][j]
                if prob > 0.01:  # Only show significant transitions
                    G.add_edge(from_state, to_state, weight=prob)
        
        return G


# --- Usage in Attribution Agent ---

# agents/attribution_engine.py
from langchain_deepagents import DeepAgent, DeepAgentConfig
from langchain_deepagents.tools import tool
from langchain_openai import ChatOpenAI
import pandas as pd
import numpy as np

class AttributionEngineAgent(DeepAgent):
    """
    Specialized agent for multi-touch attribution analysis.
    Supports Markov Chain, Shapley Value, and Deep Learning models.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        config = DeepAgentConfig(
            name="attribution_engine",
            llm=ChatOpenAI(model="gpt-4o", temperature=0.0),
            tools=[
                self.run_markov_attribution,
                self.run_shapley_attribution,
                self.run_dl_attribution,
                self.compare_models,
                self.get_channel_summary,
            ],
            system_prompt="""You are the Attribution Engine Agent.
            
You analyze marketing channel performance using multiple attribution models:
- Markov Chain: Probabilistic journey-based attribution
- Shapley Value: Game-theoretic fair credit distribution
- Deep Learning: LSTM/Transformer-based sequence attribution

Always:
1. Recommend the best model based on data characteristics
2. Explain results in business-friendly terms
3. Compare multiple models when appropriate
4. Highlight data quality issues that may affect results""",
            verbose=True,
        )
        super().__init__(config)
    
    @tool
    async def run_markov_attribution(
        self,
        start_date: str,
        end_date: str,
        customer_id_column: str = "customer_id",
        channel_column: str = "channel",
        conversion_column: str = "converted",
    ) -> dict:
        """
        Run Markov Chain attribution analysis.
        
        Returns:
            Dictionary with attribution results and model diagnostics
        """
        # Fetch journey data
        journeys_df = await self._fetch_journeys(start_date, end_date)
        
        # Build journey sequences per customer
        journeys = []
        conversions = []
        
        for customer_id, group in journeys_df.groupby(customer_id_column):
            group = group.sort_values("timestamp")
            journey = group[channel_column].tolist()
            converted = int(group[conversion_column].max())
            journeys.append(journey)
            conversions.append(converted)
        
        # Fit Markov model
        mc = MarkovChainAttribution(order=1)
        mc.fit(journeys, conversions)
        
        # Get results
        attribution_df = mc.get_attribution()
        
        return {
            "model": "markov_chain",
            "attribution": attribution_df.to_dict(orient="records"),
            "total_journeys": len(journeys),
            "conversion_rate": np.mean(conversions),
            "model_diagnostics": {
                "num_states": len(mc.states),
                "baseline_conversion_rate": mc._calculate_conversion_rate(
                    mc.transition_matrix,
                    {s: i for i, s in enumerate(mc.states)}
                ),
            },
        }
    
    @tool
    async def run_shapley_attribution(
        self,
        start_date: str,
        end_date: str,
    ) -> dict:
        """
        Run Shapley Value attribution analysis.
        
        Uses cooperative game theory to fairly distribute conversion credit.
        """
        from itertools import combinations
        
        # Fetch channel-level conversion data
        channel_data = await self._fetch_channel_conversions(start_date, end_date)
        
        channels = list(channel_data.keys())
        n = len(channels)
        
        # Characteristic function: v(S) = conversions from channels in subset S
        def characteristic_function(subset: tuple) -> float:
            """Calculate conversions attributable to a subset of channels."""
            if not subset:
                return 0.0
            
            # Fetch data for this subset
            subset_data = channel_data[list(subset)]
            # Use union of conversions from these channels
            # In practice, this requires journey-level data
            return self._calculate_subset_conversions(subset)
        
        # Calculate Shapley values
        shapley_values = {}
        factorial = np.math.factorial
        
        for i, channel in enumerate(channels):
            shapley = 0.0
            
            other_channels = [c for j, c in enumerate(channels) if j != i]
            
            for size in range(n):
                for subset in combinations(other_channels, size):
                    # Marginal contribution
                    v_with = characteristic_function(tuple(sorted(subset + (channel,))))
                    v_without = characteristic_function(tuple(sorted(subset)))
                    marginal = v_with - v_without
                    
                    # Weight
                    weight = (
                        factorial(size) * factorial(n - size - 1) / factorial(n)
                    )
                    shapley += weight * marginal
            
            shapley_values[channel] = shapley
        
        # Normalize to percentages
        total = sum(shapley_values.values())
        if total > 0:
            shapley_values = {k: v / total for k, v in shapley_values.items()}
        
        results = [
            {"channel": ch, "shapley_value": val, "attribution_pct": f"{val*100:.1f}%"}
            for ch, val in sorted(shapley_values.items(), key=lambda x: -x[1])
        ]
        
        return {
            "model": "shapley_value",
            "attribution": results,
            "total_channels": n,
        }
    
    @tool
    async def run_dl_attribution(
        self,
        start_date: str,
        end_date: str,
        model_type: str = "lstm",
    ) -> dict:
        """
        Run deep learning attribution using LSTM or Transformer.
        
        Args:
            model_type: 'lstm' or 'transformer'
        """
        import torch
        import torch.nn as nn
        
        # Fetch journey data
        journeys_df = await self._fetch_journeys(start_date, end_date)
        
        # Prepare sequences
        channel_vocab = self._build_channel_vocab(journeys_df)
        sequences, labels = self._prepare_sequences(journeys_df, channel_vocab)
        
        # Build model
        if model_type == "lstm":
            model = self._build_lstm_model(
                vocab_size=len(channel_vocab),
                embedding_dim=64,
                hidden_dim=128,
            )
        else:
            model = self._build_transformer_model(
                vocab_size=len(channel_vocab),
                d_model=64,
                nhead=4,
                num_layers=2,
            )
        
        # Train (or load pre-trained)
        model = self._train_or_load_model(model, sequences, labels, model_type)
        
        # Calculate attribution via attention weights or gradient-based methods
        attribution = self._calculate_dl_attribution(model, sequences, channel_vocab)
        
        return {
            "model": f"deep_learning_{model_type}",
            "attribution": attribution,
            "model_accuracy": self._evaluate_model(model, sequences, labels),
        }
    
    def _build_lstm_model(self, vocab_size: int, embedding_dim: int, hidden_dim: int):
        """Build LSTM-based attribution model."""
        import torch.nn as nn
        
        class LSTMAttribution(nn.Module):
            def __init__(self, vocab_size, embedding_dim, hidden_dim):
                super().__init__()
                self.embedding = nn.Embedding(vocab_size, embedding_dim)
                self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
                self.attention = nn.Linear(hidden_dim, 1)
                self.classifier = nn.Linear(hidden_dim, 2)
            
            def forward(self, x):
                embedded = self.embedding(x)
                lstm_out, _ = self.lstm(embedded)
                
                # Attention weights for interpretability
                attn_weights = torch.softmax(self.attention(lstm_out), dim=1)
                context = torch.sum(attn_weights * lstm_out, dim=1)
                
                output = self.classifier(context)
                return output, attn_weights
        
        return LSTMAttribution(vocab_size, embedding_dim, hidden_dim)
    
    def _build_transformer_model(self, vocab_size: int, d_model: int, nhead: int, num_layers: int):
        """Build Transformer-based attribution model."""
        import torch.nn as nn
        
        class TransformerAttribution(nn.Module):
            def __init__(self, vocab_size, d_model, nhead, num_layers):
                super().__init__()
                self.embedding = nn.Embedding(vocab_size, d_model)
                self.pos_encoder = PositionalEncoding(d_model)
                encoder_layer = nn.TransformerEncoderLayer(d_model, nhead, batch_first=True)
                self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
                self.classifier = nn.Linear(d_model, 2)
            
            def forward(self, x):
                embedded = self.pos_encoder(self.embedding(x))
                transformed = self.transformer(embedded)
                # Mean pooling
                pooled = transformed.mean(dim=1)
                output = self.classifier(pooled)
                return output, transformed  # Return transformed for attention analysis
        
        return TransformerAttribution(vocab_size, d_model, nhead, num_layers)
    
    @tool
    async def compare_models(
        self,
        start_date: str,
        end_date: str,
    ) -> dict:
        """
        Run all attribution models and compare results.
        """
        markov_results = await self.run_markov_attribution(start_date, end_date)
        shapley_results = await self.run_shapley_attribution(start_date, end_date)
        dl_results = await self.run_dl_attribution(start_date, end_date)
        
        # Build comparison table
        channels = set()
        for result in [markov_results, shapley_results, dl_results]:
            for item in result["attribution"]:
                channels.add(item["channel"])
        
        comparison = []
        for channel in sorted(channels):
            row = {"channel": channel}
            for model_name, result in [
                ("markov", markov_results),
                ("shapley", shapley_results),
                ("deep_learning", dl_results),
            ]:
                for item in result["attribution"]:
                    if item["channel"] == channel:
                        row[model_name] = item.get("attribution_credit", item.get("attribution_pct", "N/A"))
            comparison.append(row)
        
        return {
            "comparison": comparison,
            "recommendation": self._recommend_model(markov_results, shapley_results, dl_results),
        }
    
    def _recommend_model(self, markov: dict, shapley: dict, dl: dict) -> str:
        """Recommend the best model based on data characteristics."""
        total_journeys = markov.get("total_journeys", 0)
        
        if total_journeys < 1000:
            return "shapley_value (insufficient data for complex models)"
        elif total_journeys < 10000:
            return "markov_chain (good balance of accuracy and interpretability)"
        else:
            return "deep_learning (sufficient data for complex patterns)"
    
    async def _fetch_journeys(self, start: str, end: str) -> pd.DataFrame:
        """Fetch customer journey data from warehouse."""
        query = """
            SELECT customer_id, channel, campaign, timestamp, converted, revenue
            FROM marketing_touchpoints
            WHERE timestamp BETWEEN $1 AND $2
            ORDER BY customer_id, timestamp
        """
        async with self.db_pool.acquire() as conn:
            records = await conn.fetch(query, start, end)
            return pd.DataFrame([dict(r) for r in records])
    
    async def _fetch_channel_conversions(self, start: str, end: str) -> dict:
        """Fetch channel-level conversion data."""
        query = """
            SELECT channel, COUNT(DISTINCT customer_id) as conversions
            FROM marketing_touchpoints
            WHERE timestamp BETWEEN $1 AND $2 AND converted = 1
            GROUP BY channel
        """
        async with self.db_pool.acquire() as conn:
            records = await conn.fetch(query, start, end)
            return {r["channel"]: r["conversions"] for r in records}
    
    def _build_channel_vocab(self, df: pd.DataFrame) -> dict:
        """Build vocabulary mapping for channels."""
        channels = df["channel"].unique().tolist()
        return {ch: idx for idx, ch in enumerate(channels)}
    
    def _prepare_sequences(self, df: pd.DataFrame, vocab: dict) -> tuple:
        """Convert journey data to model-ready sequences."""
        sequences = []
        labels = []
        
        for customer_id, group in df.groupby("customer_id"):
            group = group.sort_values("timestamp")
            seq = [vocab[ch] for ch in group["channel"].tolist()]
            label = int(group["converted"].max())
            sequences.append(seq)
            labels.append(label)
        
        # Pad sequences
        from torch.nn.utils.rnn import pad_sequence
        import torch
        
        sequences = [torch.tensor(s) for s in sequences]
        sequences = pad_sequence(sequences, batch_first=True, padding_value=0)
        labels = torch.tensor(labels)
        
        return sequences, labels
    
    def _train_or_load_model(self, model, sequences, labels, model_type: str):
        """Train model or load pre-trained weights."""
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset
        
        model_path = f"models/attribution_{model_type}.pt"
        
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path))
            model.eval()
            return model
        
        # Training
        dataset = TensorDataset(sequences, labels)
        loader = DataLoader(dataset, batch_size=64, shuffle=True)
        
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        
        model.train()
        for epoch in range(20):
            total_loss = 0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                output, _ = model(batch_x)
                loss = criterion(output, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            
            if epoch % 5 == 0:
                print(f"Epoch {epoch}, Loss: {total_loss/len(loader):.4f}")
        
        # Save model
        os.makedirs("models", exist_ok=True)
        torch.save(model.state_dict(), model_path)
        
        return model
    
    def _calculate_dl_attribution(self, model, sequences, vocab) -> list:
        """Calculate attribution from deep learning model."""
        import torch
        
        model.eval()
        channel_attribution = {ch: 0.0 for ch in vocab}
        
        with torch.no_grad():
            for seq in sequences:
                output, attention = model(seq.unsqueeze(0))
                
                # Use attention weights as attribution
                if attention is not None:
                    attn_weights = attention.squeeze().cpu().numpy()
                    for idx, weight in enumerate(attn_weights):
                        if idx < len(seq):
                            channel_idx = seq[idx].item()
                            for ch, ch_idx in vocab.items():
                                if ch_idx == channel_idx:
                                    channel_attribution[ch] += weight
        
        # Normalize
        total = sum(channel_attribution.values())
        if total > 0:
            channel_attribution = {k: v / total for k, v in channel_attribution.items()}
        
        return [
            {"channel": ch, "attribution": val, "attribution_pct": f"{val*100:.1f}%"}
            for ch, val in sorted(channel_attribution.items(), key=lambda x: -x[1])
        ]
    
    def _evaluate_model(self, model, sequences, labels) -> float:
        """Evaluate model accuracy."""
        import torch
        
        model.eval()
        correct = 0
        total = 0
        
        with torch.no_grad():
            for i in range(len(sequences)):
                output, _ = model(sequences[i].unsqueeze(0))
                pred = output.argmax(dim=1).item()
                if pred == labels[i].item():
                    correct += 1
                total += 1
        
        return correct / total if total > 0 else 0.0
```

### 3.3 Shapley Value Attribution

```python
# attribution/shapley.py
import numpy as np
import pandas as pd
from itertools import combinations
from typing import Dict, List, Tuple
from math import factorial

class ShapleyAttribution:
    """
    Shapley Value-based attribution using cooperative game theory.
    
    The Shapley value fairly distributes the total conversion value among channels
    based on their marginal contributions to all possible coalitions.
    """
    
    def __init__(self):
        self.shapley_values = {}
        self.channel_contributions = {}
    
    def fit(
        self,
        channels: List[str],
        characteristic_function: callable,
    ):
        """
        Calculate Shapley values for each channel.
        
        Args:
            channels: List of channel names
            characteristic_function: Function v(S) that returns the value
                                    of coalition S (subset of channels)
        """
        n = len(channels)
        
        for i, channel in enumerate(channels):
            shapley = 0.0
            
            other_channels = [c for j, c in enumerate(channels) if j != i]
            
            for size in range(n):
                for subset in combinations(other_channels, size):
                    subset_with = tuple(sorted(subset + (channel,)))
                    subset_without = tuple(sorted(subset))
                    
                    # Marginal contribution
                    marginal = (
                        characteristic_function(subset_with)
                        - characteristic_function(subset_without)
                    )
                    
                    # Shapley weight: |S|! * (n - |S| - 1)! / n!
                    weight = (
                        factorial(size) * factorial(n - size - 1)
                    ) / factorial(n)
                    
                    shapley += weight * marginal
            
            self.shapley_values[channel] = shapley
        
        return self
    
    def get_attribution(self) -> pd.DataFrame:
        """Get normalized attribution percentages."""
        total = sum(self.shapley_values.values())
        
        results = []
        for channel, value in self.shapley_values.items():
            pct = value / total if total > 0 else 0
            results.append({
                "channel": channel,
                "shapley_value": value,
                "attribution_pct": pct,
                "attribution_pct_formatted": f"{pct * 100:.1f}%",
            })
        
        df = pd.DataFrame(results)
        df = df.sort_values("shapley_value", ascending=False)
        return df


# --- Efficient approximation for large channel sets ---

class ApproximateShapleyAttribution:
    """
    Monte Carlo approximation of Shapley values for large numbers of channels.
    Uses permutation sampling to estimate Shapley values.
    """
    
    def __init__(self, n_samples: int = 10000, random_state: int = 42):
        self.n_samples = n_samples
        self.random_state = random_state
        self.shapley_estimates = {}
    
    def fit(self, channels: List[str], characteristic_function: callable):
        """
        Estimate Shapley values using random permutations.
        """
        rng = np.random.RandomState(self.random_state)
        n = len(channels)
        
        # Initialize contributions
        contributions = {ch: [] for ch in channels}
        
        for _ in range(self.n_samples):
            # Random permutation
            perm = rng.permutation(channels)
            
            # Calculate marginal contributions along the permutation
            current_value = characteristic_function(tuple())
            
            for i, channel in enumerate(perm):
                new_coalition = tuple(sorted(perm[:i+1]))
                new_value = characteristic_function(new_coalition)
                
                marginal = new_value - current_value
                contributions[channel].append(marginal)
                
                current_value = new_value
        
        # Average contributions
        for channel in channels:
            self.shapley_estimates[channel] = np.mean(contributions[channel])
        
        return self
    
    def get_confidence_intervals(self, confidence: float = 0.95) -> pd.DataFrame:
        """Calculate confidence intervals for Shapley estimates."""
        results = []
        
        for channel, estimates in self.contributions.items():
            mean = np.mean(estimates)
            std = np.std(estimates)
            n = len(estimates)
            
            # Normal approximation
            z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
            margin = z * std / np.sqrt(n)
            
            results.append({
                "channel": channel,
                "shapley_estimate": mean,
                "ci_lower": mean - margin,
                "ci_upper": mean + margin,
                "std_error": std / np.sqrt(n),
            })
        
        return pd.DataFrame(results)
```

---

## 4. Predictive Analytics Agent

### 4.1 Architecture

The Predictive Analytics Agent handles:
- **Forecasting**: Time-series prediction of key metrics (revenue, conversions, spend)
- **Anomaly Detection**: Identifying unusual patterns in marketing data
- **Customer Lifetime Value (LTV)**: Predicting future customer value
- **Churn Prediction**: Identifying customers at risk of churning
- **Budget Optimization**: Recommending optimal budget allocation

### 4.2 Implementation

```python
# agents/predictive_analytics.py
from langchain_deepagents import DeepAgent, DeepAgentConfig
from langchain_deepagents.tools import tool
from langchain_openai import ChatOpenAI
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import asyncpg

class PredictiveAnalyticsAgent(DeepAgent):
    """
    Specialized agent for marketing predictive analytics.
    Handles forecasting, anomaly detection, LTV prediction, and budget optimization.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        config = DeepAgentConfig(
            name="predictive_analytics",
            llm=ChatOpenAI(model="gpt-4o", temperature=0.0),
            tools=[
                self.forecast_metrics,
                self.detect_anomalies,
                self.predict_ltv,
                self.predict_churn,
                self.optimize_budget,
                self.get_prediction_explanation,
            ],
            system_prompt="""You are the Predictive Analytics Agent.
            
You perform advanced predictive analytics on marketing data:
- Time-series forecasting (Prophet, ARIMA, LSTM)
- Anomaly detection (Isolation Forest, statistical methods)
- Customer Lifetime Value prediction
- Churn prediction
- Budget optimization

Always:
1. Provide confidence intervals with predictions
2. Explain model assumptions and limitations
3. Recommend actions based on predictions
4. Flag when predictions may be unreliable""",
            verbose=True,
        )
        super().__init__(config)
    
    @tool
    async def forecast_metrics(
        self,
        metric: str,
        start_date: str,
        end_date: str,
        forecast_horizon: int = 30,
        model: str = "prophet",
        include_history: bool = True,
    ) -> dict:
        """
        Forecast a marketing metric into the future.
        
        Args:
            metric: Metric to forecast ('revenue', 'conversions', 'spend', 'roas')
            start_date: Historical data start date
            end_date: Historical data end date
            forecast_horizon: Number of days to forecast
            model: Forecasting model ('prophet', 'arima', 'lstm')
            include_history: Whether to include historical data in output
        
        Returns:
            Dictionary with forecast results, confidence intervals, and model info
        """
        # Fetch historical data
        df = await self._fetch_metric_data(metric, start_date, end_date)
        
        if model == "prophet":
            forecast = self._prophet_forecast(df, metric, forecast_horizon)
        elif model == "arima":
            forecast = self._arima_forecast(df, metric, forecast_horizon)
        elif model == "lstm":
            forecast = self._lstm_forecast(df, metric, forecast_horizon)
        else:
            raise ValueError(f"Unsupported model: {model}")
        
        result = {
            "model": model,
            "metric": metric,
            "forecast_horizon_days": forecast_horizon,
            "forecast": forecast.to_dict(orient="records"),
            "model_metrics": self._calculate_forecast_metrics(df, metric),
        }
        
        if include_history:
            result["history"] = df.to_dict(orient="records")
        
        return result
    
    def _prophet_forecast(
        self, df: pd.DataFrame, metric: str, horizon: int
    ) -> pd.DataFrame:
        """Forecast using Facebook Prophet."""
        from prophet import Prophet
        
        # Prepare data for Prophet
        prophet_df = df.rename(columns={"date": "ds", metric: "y"})[["ds", "y"]]
        
        # Add regressors if available
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
        )
        
        # Add custom seasonality for marketing patterns
        model.add_seasonality(
            name="monthly",
            period=30.5,
            fourier_order=5,
        )
        
        model.fit(prophet_df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=horizon)
        forecast = model.predict(future)
        
        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(horizon)
    
    def _arima_forecast(
        self, df: pd.DataFrame, metric: str, horizon: int
    ) -> pd.DataFrame:
        """Forecast using ARIMA."""
        from statsmodels.tsa.arima.model import ARIMA
        
        series = df.set_index("date")[metric]
        
        # Auto-select ARIMA order (simplified)
        model = ARIMA(series, order=(7, 1, 7))
        fitted = model.fit()
        
        # Forecast
        forecast_result = fitted.get_forecast(steps=horizon)
        forecast_mean = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int()
        
        # Build result DataFrame
        last_date = df["date"].max()
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1), periods=horizon, freq="D"
        )
        
        forecast_df = pd.DataFrame({
            "ds": future_dates,
            "yhat": forecast_mean.values,
            "yhat_lower": conf_int.iloc[:, 0].values,
            "yhat_upper": conf_int.iloc[:, 1].values,
        })
        
        return forecast_df
    
    def _lstm_forecast(
        self, df: pd.DataFrame, metric: str, horizon: int
    ) -> pd.DataFrame:
        """Forecast using LSTM neural network."""
        import torch
        import torch.nn as nn
        from sklearn.preprocessing import MinMaxScaler
        
        # Prepare data
        scaler = MinMaxScaler()
        values = df[metric].values.reshape(-1, 1)
        scaled = scaler.fit_transform(values)
        
        # Create sequences
        seq_length = 30
        X, y = [], []
        for i in range(len(scaled) - seq_length):
            X.append(scaled[i:i + seq_length])
            y.append(scaled[i + seq_length])
        
        X = torch.FloatTensor(np.array(X))
        y = torch.FloatTensor(np.array(y))
        
        # Build LSTM model
        class LSTMForecaster(nn.Module):
            def __init__(self, input_size=1, hidden_size=64, num_layers=2):
                super().__init__()
                self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
                self.fc = nn.Linear(hidden_size, 1)
            
            def forward(self, x):
                out, _ = self.lstm(x)
                out = self.fc(out[:, -1, :])
                return out
        
        model = LSTMForecaster()
        
        # Load pre-trained or train
        model_path = f"models/lstm_forecaster_{metric}.pt"
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path))
        else:
            # Quick training
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            
            for epoch in range(50):
                model.train()
                optimizer.zero_grad()
                output = model(X)
                loss = criterion(output, y)
                loss.backward()
                optimizer.step()
            
            os.makedirs("models", exist_ok=True)
            torch.save(model.state_dict(), model_path)
        
        # Generate forecast
        model.eval()
        last_sequence = scaled[-seq_length:].reshape(1, seq_length, 1)
        forecasts = []
        
        with torch.no_grad():
            current_seq = torch.FloatTensor(last_sequence)
            for _ in range(horizon):
                pred = model(current_seq)
                forecasts.append(pred.item())
                # Update sequence
                current_seq = torch.cat([
                    current_seq[:, 1:, :],
                    pred.reshape(1, 1, 1)
                ], dim=1)
        
        # Inverse transform
        forecasts = scaler.inverse_transform(np.array(forecasts).reshape(-1, 1))
        
        # Build result
        last_date = df["date"].max()
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1), periods=horizon, freq="D"
        )
        
        # Simple confidence intervals (±10%)
        forecast_df = pd.DataFrame({
            "ds": future_dates,
            "yhat": forecasts.flatten(),
            "yhat_lower": forecasts.flatten() * 0.9,
            "yhat_upper": forecasts.flatten() * 1.1,
        })
        
        return forecast_df
    
    @tool
    async def detect_anomalies(
        self,
        metric: str,
        start_date: str,
        end_date: str,
        sensitivity: str = "medium",
    ) -> dict:
        """
        Detect anomalies in marketing metrics.
        
        Args:
            metric: Metric to analyze
            start_date: Start date
            end_date: End date
            sensitivity: 'low', 'medium', or 'high'
        
        Returns:
            Dictionary with detected anomalies and their details
        """
        df = await self._fetch_metric_data(metric, start_date, end_date)
        
        # Use Isolation Forest for anomaly detection
        from sklearn.ensemble import IsolationForest
        
        sensitivity_map = {"low": 0.05, "medium": 0.1, "high": 0.2}
        contamination = sensitivity_map.get(sensitivity, 0.1)
        
        values = df[metric].values.reshape(-1, 1)
        
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
        )
        predictions = iso_forest.fit_predict(values)
        
        # Extract anomalies
        df["is_anomaly"] = predictions == -1
        df["anomaly_score"] = iso_forest.score_samples(values)
        
        anomalies = df[df["is_anomaly"]].copy()
        
        # Classify anomaly type
        anomalies["anomaly_type"] = anomalies.apply(
            lambda row: self._classify_anomaly(row, df, metric), axis=1
        )
        
        return {
            "total_anomalies": len(anomalies),
            "anomaly_rate": len(anomalies) / len(df),
            "anomalies": anomalies.to_dict(orient="records"),
            "metric": metric,
            "sensitivity": sensitivity,
        }
    
    def _classify_anomaly(self, row, df: pd.DataFrame, metric: str) -> str:
        """Classify anomaly as spike, drop, or pattern change."""
        mean = df[metric].mean()
        std = df[metric].std()
        value = row[metric]
        
        if value > mean + 2 * std:
            return "spike"
        elif value < mean - 2 * std:
            return "drop"
        else:
            return "pattern_change"
    
    @tool
    async def predict_ltv(
        self,
        customer_segment: Optional[str] = None,
        prediction_period_months: int = 12,
    ) -> dict:
        """
        Predict Customer Lifetime Value.
        
        Uses BG/NBD model for purchase frequency and Gamma-Gamma for monetary value.
        """
        from lifetimes import BetaGeoFitter, GammaGammaFitter
        
        # Fetch customer transaction data
        transactions = await self._fetch_transaction_data(customer_segment)
        
        # Calculate RFM metrics
        from lifetimes.utils import summary_data_from_transaction_data
        
        summary = summary_data_from_transaction_data(
            transactions,
            "customer_id",
            "transaction_date",
            "amount",
            observation_period_end=transactions["transaction_date"].max(),
        )
        
        # Filter to customers with repeat purchases
        repeat_customers = summary[summary["frequency"] > 0]
        
        # Fit BG/NBD model
        bgf = BetaGeoFitter(penalizer_coef=0.01)
        bgf.fit(
            repeat_customers["frequency"],
            repeat_customers["recency"],
            repeat_customers["T"],
        )
        
        # Fit Gamma-Gamma model
        ggf = GammaGammaFitter(penalizer_coef=0.01)
        ggf.fit(
            repeat_customers["frequency"],
            repeat_customers["monetary_value"],
        )
        
        # Predict LTV
        summary["predicted_purchases"] = bgf.conditional_expected_number_of_purchases_up_to_time(
            prediction_period_months * 30,  # Convert to days
            summary["frequency"],
            summary["recency"],
            summary["T"],
        )
        
        summary["predicted_avg_value"] = ggf.conditional_expected_average_profit(
            summary["frequency"],
            summary["monetary_value"],
        )
        
        summary["predicted_ltv"] = (
            summary["predicted_purchases"] * summary["predicted_avg_value"]
        )
        
        # Segment analysis
        ltv_by_segment = summary.groupby("segment")["predicted_ltv"].agg([
            "mean", "median", "std", "count"
        ]).reset_index()
        
        return {
            "prediction_period_months": prediction_period_months,
            "total_customers": len(summary),
            "avg_predicted_ltv": summary["predicted_ltv"].mean(),
            "median_predicted_ltv": summary["predicted_ltv"].median(),
            "total_predicted_revenue": summary["predicted_ltv"].sum(),
            "ltv_by_segment": ltv_by_segment.to_dict(orient="records"),
            "top_customers": summary.nlargest(10, "predicted_ltv")[
                ["customer_id", "predicted_ltv", "predicted_purchases"]
            ].to_dict(orient="records"),
        }
    
    @tool
    async def predict_churn(
        self,
        customer_segment: Optional[str] = None,
    ) -> dict:
        """
        Predict customer churn probability.
        
        Uses XGBoost classifier with RFM features and engagement metrics.
        """
        import xgboost as xgb
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report, roc_auc_score
        
        # Fetch customer features
        features_df = await self._fetch_churn_features(customer_segment)
        
        # Prepare features
        feature_cols = [
            "recency", "frequency", "monetary_value",
            "avg_order_value", "days_since_last_login",
            "email_open_rate", "support_tickets_30d",
            "nps_score", "tenure_days",
        ]
        
        X = features_df[feature_cols]
        y = features_df["churned"]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=len(y_train[y_train == 0]) / len(y_train[y_train == 1]),
            random_state=42,
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        # Feature importance
        importance = pd.DataFrame({
            "feature": feature_cols,
            "importance": model.feature_importances_,
        }).sort_values("importance", ascending=False)
        
        # Predict churn for all customers
        features_df["churn_probability"] = model.predict_proba(X)[:, 1]
        features_df["churn_risk_segment"] = pd.cut(
            features_df["churn_probability"],
            bins=[0, 0.3, 0.7, 1.0],
            labels=["low", "medium", "high"],
        )
        
        return {
            "model_accuracy": model.score(X_test, y_test),
            "roc_auc": roc_auc_score(y_test, y_prob),
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
            "feature_importance": importance.to_dict(orient="records"),
            "churn_risk_distribution": features_df["churn_risk_segment"].value_counts().to_dict(),
            "high_risk_customers": features_df[
                features_df["churn_risk_segment"] == "high"
            ][["customer_id", "churn_probability"]].head(20).to_dict(orient="records"),
        }
    
    @tool
    async def optimize_budget(
        self,
        total_budget: float,
        channels: list[str],
        objective: str = "maximize_conversions",
        constraints: Optional[dict] = None,
    ) -> dict:
        """
        Optimize budget allocation across channels.
        
        Uses linear programming with diminishing returns curves.
        
        Args:
            total_budget: Total budget to allocate
            channels: List of channels to consider
            objective: 'maximize_conversions', 'maximize_revenue', or 'maximize_roas'
            constraints: Optional constraints like min/max per channel
        """
        from scipy.optimize import minimize
        
        # Fetch channel performance data
        channel_data = await self._fetch_channel_performance(channels)
        
        # Fit diminishing returns curves for each channel
        # Using Hill function: response = alpha * spend^beta / (gamma + spend^beta)
        curves = {}
        for channel in channels:
            data = channel_data[channel]
            curves[channel] = self._fit_hill_curve(data["spend"], data["conversions"])
        
        # Objective function (negative because we minimize)
        def objective_function(allocations):
            total = 0
            for i, channel in enumerate(channels):
                alpha, beta, gamma = curves[channel]
                total += alpha * allocations[i] ** beta / (gamma + allocations[i] ** beta)
            return -total  # Negative for minimization
        
        # Constraints
        cons = [{"type": "eq", "fun": lambda x: sum(x) - total_budget}]
        
        # Bounds
        bounds = []
        for channel in channels:
            min_spend = constraints.get(channel, {}).get("min", 0) if constraints else 0
            max_spend = constraints.get(channel, {}).get("max", total_budget) if constraints else total_budget
            bounds.append((min_spend, max_spend))
        
        # Initial guess: equal allocation
        x0 = [total_budget / len(channels)] * len(channels)
        
        # Optimize
        result = minimize(
            objective_function,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
        )
        
        # Build results
        allocation = {}
        for i, channel in enumerate(channels):
            allocation[channel] = {
                "budget": round(result.x[i], 2),
                "pct_of_total": f"{result.x[i] / total_budget * 100:.1f}%",
                "expected_conversions": round(
                    curves[channel][0] * result.x[i] ** curves[channel][1]
                    / (curves[channel][2] + result.x[i] ** curves[channel][1]),
                    0
                ),
            }
        
        return {
            "total_budget": total_budget,
            "objective": objective,
            "allocation": allocation,
            "expected_total_conversions": -result.fun,
            "optimization_success": result.success,
        }
    
    def _fit_hill_curve(self, spend: np.ndarray, conversions: np.ndarray) -> tuple:
        """Fit Hill function parameters to channel data."""
        from scipy.optimize import curve_fit
        
        def hill(x, alpha, beta, gamma):
            return alpha * x ** beta / (gamma + x ** beta)
        
        try:
            popt, _ = curve_fit(hill, spend, conversions, p0=[conversions.max(), 1, spend.mean()])
            return tuple(popt)
        except RuntimeError:
            # Fallback to simple power law
            return (conversions.max() / max(spend.mean(), 1), 0.5, 1.0)
    
    @tool
    async def get_prediction_explanation(
        self,
        prediction_type: str,
        entity_id: str,
    ) -> dict:
        """
        Explain a specific prediction using SHAP values.
        """
        import shap
        
        # This would load the appropriate model and calculate SHAP values
        # Simplified implementation
        return {
            "prediction_type": prediction_type,
            "entity_id": entity_id,
            "explanation": "SHAP-based explanation of prediction",
            "top_factors": [
                {"factor": "recency", "impact": 0.35, "direction": "increases"},
                {"factor": "frequency", "impact": 0.28, "direction": "increases"},
                {"factor": "monetary_value", "impact": 0.20, "direction": "increases"},
            ],
        }
    
    async def _fetch_metric_data(self, metric: str, start: str, end: str) -> pd.DataFrame:
        """Fetch time-series metric data."""
        query = f"""
            SELECT date, SUM({metric}) as {metric}
            FROM daily_marketing_metrics
            WHERE date BETWEEN $1 AND $2
            GROUP BY date
            ORDER BY date
        """
        async with self.db_pool.acquire() as conn:
            records = await conn.fetch(query, start, end)
            return pd.DataFrame([dict(r) for r in records])
    
    async def _fetch_transaction_data(self, segment: Optional[str] = None) -> pd.DataFrame:
        """Fetch customer transaction data."""
        query = """
            SELECT customer_id, transaction_date, amount, segment
            FROM customer_transactions
        """
        if segment:
            query += " WHERE segment = $1"
            async with self.db_pool.acquire() as conn:
                records = await conn.fetch(query, segment)
        else:
            async with self.db_pool.acquire() as conn:
                records = await conn.fetch(query)
        return pd.DataFrame([dict(r) for r in records])
    
    async def _fetch_churn_features(self, segment: Optional[str] = None) -> pd.DataFrame:
        """Fetch features for churn prediction."""
        query = """
            SELECT 
                c.customer_id,
                c.recency,
                c.frequency,
                c.monetary_value,
                c.avg_order_value,
                c.days_since_last_login,
                c.email_open_rate,
                c.support_tickets_30d,
                c.nps_score,
                c.tenure_days,
                COALESCE(c.churned, 0) as churned,
                c.segment
            FROM customer_features c
        """
        if segment:
            query += " WHERE c.segment = $1"
            async with self.db_pool.acquire() as conn:
                records = await conn.fetch(query, segment)
        else:
            async with self.db_pool.acquire() as conn:
                records = await conn.fetch(query)
        return pd.DataFrame([dict(r) for r in records])
    
    async def _fetch_channel_performance(self, channels: list[str]) -> dict:
        """Fetch historical performance data for each channel."""
        result = {}
        for channel in channels:
            query = """
                SELECT date, spend, conversions, revenue
                FROM channel_daily_performance
                WHERE channel = $1
                ORDER BY date
            """
            async with self.db_pool.acquire() as conn:
                records = await conn.fetch(query, channel)
                df = pd.DataFrame([dict(r) for r in records])
                result[channel] = {
                    "spend": df["spend"].values,
                    "conversions": df["conversions"].values,
                }
        return result
    
    def _calculate_forecast_metrics(self, df: pd.DataFrame, metric: str) -> dict:
        """Calculate model performance metrics."""
        return {
            "data_points": len(df),
            "date_range": f"{df['date'].min()} to {df['date'].max()}",
            "mean": df[metric].mean(),
            "std": df[metric].std(),
            "trend": "increasing" if df[metric].iloc[-1] > df[metric].iloc[0] else "decreasing",
        }
```

---

## 5. Reporting Agent

### 5.1 Architecture

The Reporting Agent generates:
- **Automated reports**: Daily/weekly/monthly performance summaries
- **Ad-hoc reports**: Custom reports based on user queries
- **Visual reports**: Charts, graphs, and interactive visualizations
- **Natural language summaries**: Written analysis of key findings

### 5.2 Implementation

```python
# agents/reporting.py
from langchain_deepagents import DeepAgent, DeepAgentConfig
from langchain_deepagents.tools import tool
from langchain_openai import ChatOpenAI
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import asyncpg
import json

class ReportingAgent(DeepAgent):
    """
    Specialized agent for generating marketing reports and visualizations.
    Creates automated reports, ad-hoc analyses, and natural language summaries.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        config = DeepAgentConfig(
            name="reporting",
            llm=ChatOpenAI(model="gpt-4o", temperature=0.3),
            tools=[
                self.generate_daily_report,
                self.generate_weekly_report,
                self.generate_monthly_report,
                self.create_custom_report,
                self.generate_executive_summary,
                self.create_visualization,
                self.export_report,
                self.schedule_report,
            ],
            system_prompt="""You are the Reporting Agent.
            
You generate comprehensive marketing reports:
- Automated daily/weekly/monthly reports
- Custom ad-hoc reports
- Executive summaries
- Data visualizations

Always:
1. Highlight key insights and trends
2. Compare against targets and benchmarks
3. Provide actionable recommendations
4. Use clear, business-friendly language
5. Include relevant charts and visualizations""",
            verbose=True,
        )
        super().__init__(config)
    
    @tool
    async def generate_daily_report(self, report_date: Optional[str] = None) -> dict:
        """
        Generate a daily marketing performance report.
        
        Args:
            report_date: Date for the report (default: yesterday)
        
        Returns:
            Complete daily report with metrics, insights, and recommendations
        """
        if report_date is None:
            report_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Fetch daily metrics
        metrics = await self._fetch_daily_metrics(report_date)
        
        # Fetch comparison data (previous day, same day last week)
        prev_day = await self._fetch_daily_metrics(
            (datetime.strptime(report_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        )
        prev_week = await self._fetch_daily_metrics(
            (datetime.strptime(report_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
        )
        
        # Calculate changes
        changes = self._calculate_changes(metrics, prev_day, prev_week)
        
        # Generate insights
        insights = self._generate_daily_insights(metrics, changes)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, changes)
        
        report = {
            "report_type": "daily",
            "date": report_date,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "changes": changes,
            "insights": insights,
            "recommendations": recommendations,
            "charts": await self._generate_daily_charts(report_date),
        }
        
        return report
    
    @tool
    async def generate_weekly_report(
        self,
        week_start: Optional[str] = None,
    ) -> dict:
        """Generate a weekly marketing performance report."""
        if week_start is None:
            # Default to current week's Monday
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        
        week_end = (
            datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=6)
        ).strftime("%Y-%m-%d")
        
        # Fetch weekly aggregated data
        weekly_data = await self._fetch_weekly_aggregates(week_start, week_end)
        
        # Fetch previous week for comparison
        prev_week_start = (
            datetime.strptime(week_start, "%Y-%m-%d") - timedelta(days=7)
        ).strftime("%Y-%m-%d")
        prev_week_end = (
            datetime.strptime(week_end, "%Y-%m-%d") - timedelta(days=7)
        ).strftime("%Y-%m-%d")
        prev_week_data = await self._fetch_weekly_aggregates(prev_week_start, prev_week_end)
        
        # Channel performance
        channel_performance = await self._fetch_channel_performance_weekly(week_start, week_end)
        
        # Campaign performance
        campaign_performance = await self._fetch_campaign_performance_weekly(week_start, week_end)
        
        # Attribution summary
        attribution_summary = await self._fetch_attribution_summary(week_start, week_end)
        
        report = {
            "report_type": "weekly",
            "week_start": week_start,
            "week_end": week_end,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_spend": weekly_data["total_spend"],
                "total_revenue": weekly_data["total_revenue"],
                "total_conversions": weekly_data["total_conversions"],
                "blended_roas": weekly_data["total_revenue"] / max(weekly_data["total_spend"], 1),
                "blended_cpa": weekly_data["total_spend"] / max(weekly_data["total_conversions"], 1),
            },
            "week_over_week_change": self._calculate_weekly_changes(weekly_data, prev_week_data),
            "channel_performance": channel_performance,
            "campaign_performance": campaign_performance,
            "attribution_summary": attribution_summary,
            "daily_trend": await self._fetch_daily_trend(week_start, week_end),
            "top_insights": self._generate_weekly_insights(weekly_data, channel_performance),
            "recommendations": self._generate_weekly_recommendations(weekly_data, channel_performance),
        }
        
        return report
    
    @tool
    async def generate_monthly_report(
        self,
        month: Optional[str] = None,
    ) -> dict:
        """Generate a comprehensive monthly marketing report."""
        if month is None:
            month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        
        # Fetch monthly data
        monthly_data = await self._fetch_monthly_aggregates(month)
        
        # Month-over-month comparison
        prev_month = (
            datetime.strptime(month, "%Y-%m").replace(day=1) - timedelta(days=1)
        ).strftime("%Y-%m")
        prev_month_data = await self._fetch_monthly_aggregates(prev_month)
        
        # Year-over-year comparison
        prev_year_month = f"{int(month[:4]) - 1}{month[4:]}"
        try:
            yoy_data = await self._fetch_monthly_aggregates(prev_year_month)
        except Exception:
            yoy_data = None
        
        report = {
            "report_type": "monthly",
            "month": month,
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": self._generate_executive_summary(monthly_data, prev_month_data),
            "kpi_dashboard": {
                "revenue": {
                    "value": monthly_data["total_revenue"],
                    "mom_change": self._pct_change(monthly_data["total_revenue"], prev_month_data["total_revenue"]),
                    "yoy_change": self._pct_change(monthly_data["total_revenue"], yoy_data["total_revenue"]) if yoy_data else None,
                },
                "spend": {
                    "value": monthly_data["total_spend"],
                    "mom_change": self._pct_change(monthly_data["total_spend"], prev_month_data["total_spend"]),
                },
                "conversions": {
                    "value": monthly_data["total_conversions"],
                    "mom_change": self._pct_change(monthly_data["total_conversions"], prev_month_data["total_conversions"]),
                },
                "roas": {
                    "value": monthly_data["total_revenue"] / max(monthly_data["total_spend"], 1),
                    "mom_change": self._pct_change(
                        monthly_data["total_revenue"] / max(monthly_data["total_spend"], 1),
                        prev_month_data["total_revenue"] / max(prev_month_data["total_spend"], 1),
                    ),
                },
            },
            "channel_breakdown": await self._fetch_channel_breakdown_monthly(month),
            "campaign_analysis": await self._fetch_campaign_analysis_monthly(month),
            "attribution_analysis": await self._fetch_attribution_analysis_monthly(month),
            "audience_insights": await self._fetch_audience_insights_monthly(month),
            "creative_performance": await self._fetch_creative_performance_monthly(month),
            "recommendations": self._generate_monthly_recommendations(monthly_data),
        }
        
        return report
    
    @tool
    async def create_custom_report(
        self,
        metrics: list[str],
        dimensions: list[str],
        start_date: str,
        end_date: str,
        filters: Optional[dict] = None,
        group_by: Optional[str] = None,
    ) -> dict:
        """
        Create a custom report based on user specifications.
        
        Args:
            metrics: List of metrics to include
            dimensions: List of dimensions to analyze
            start_date: Start date
            end_date: End date
            filters: Optional filters to apply
            group_by: Optional grouping dimension
        """
        # Build dynamic query
        query = self._build_custom_query(metrics, dimensions, start_date, end_date, filters, group_by)
        
        async with self.db_pool.acquire() as conn:
            records = await conn.fetch(query)
            df = pd.DataFrame([dict(r) for r in records])
        
        # Generate visualizations
        charts = []
        for metric in metrics:
            chart = self._create_chart(df, metric, dimensions[0] if dimensions else None)
            charts.append(chart)
        
        # Generate summary
        summary = self._summarize_custom_data(df, metrics, dimensions)
        
        return {
            "report_type": "custom",
            "parameters": {
                "metrics": metrics,
                "dimensions": dimensions,
                "date_range": f"{start_date} to {end_date}",
                "filters": filters,
            },
            "data": df.to_dict(orient="records"),
            "summary": summary,
            "charts": charts,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    @tool
    async def generate_executive_summary(
        self,
        start_date: str,
        end_date: str,
    ) -> dict:
        """
        Generate a natural language executive summary of marketing performance.
        """
        # Fetch key metrics
        metrics = await self._fetch_executive_metrics(start_date, end_date)
        
        # Fetch attribution results
        attribution = await self._fetch_attribution_summary(start_date, end_date)
        
        # Fetch predictive insights
        forecast = await self._fetch_forecast_summary(start_date, end_date)
        
        # Generate narrative using LLM
        summary_prompt = f"""
        Write an executive summary of marketing performance from {start_date} to {end_date}.
        
        Key metrics:
        - Total Revenue: ${metrics['total_revenue']:,.0f}
        - Total Spend: ${metrics['total_spend']:,.0f}
        - Blended ROAS: {metrics['roas']:.2f}
        - Total Conversions: {metrics['total_conversions']:,.0f}
        - Blended CPA: ${metrics['cpa']:.2f}
        
        Top performing channels (by attribution credit):
        {json.dumps(attribution[:3], indent=2)}
        
        Forecast for next 30 days:
        - Expected Revenue: ${forecast['expected_revenue']:,.0f}
        - Expected Conversions: {forecast['expected_conversions']:,.0f}
        
        Write a concise, actionable executive summary (max 300 words) highlighting:
        1. Overall performance
        2. Key wins
        3. Areas of concern
        4. Recommended actions
        """
        
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        summary = llm.predict(summary_prompt)
        
        return {
            "period": f"{start_date} to {end_date}",
            "summary": summary,
            "key_metrics": metrics,
            "top_channels": attribution[:5],
            "forecast": forecast,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    @tool
    async def create_visualization(
        self,
        chart_type: str,
        data: pd.DataFrame,
        x_axis: str,
        y_axis: str,
        title: str,
        color_by: Optional[str] = None,
    ) -> dict:
        """
        Create a chart visualization specification.
        
        Returns Plotly figure specification that can be rendered in the dashboard.
        """
        import plotly.express as px
        import plotly.graph_objects as go
        import json
        
        if chart_type == "line":
            fig = px.line(data, x=x_axis, y=y_axis, color=color_by, title=title)
        elif chart_type == "bar":
            fig = px.bar(data, x=x_axis, y=y_axis, color=color_by, title=title)
        elif chart_type == "scatter":
            fig = px.scatter(data, x=x_axis, y=y_axis, color=color_by, title=title)
        elif chart_type == "pie":
            fig = px.pie(data, names=x_axis, values=y_axis, title=title)
        elif chart_type == "funnel":
            fig = px.funnel(data, x=x_axis, y=y_axis, title=title)
        elif chart_type == "heatmap":
            fig = px.imshow(data.pivot(index=x_axis, columns=color_by, values=y_axis), title=title)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        # Enhance layout
        fig.update_layout(
            template="plotly_white",
            font=dict(size=12),
            margin=dict(l=40, r=40, t=60, b=40),
        )
        
        return {
            "chart_type": chart_type,
            "title": title,
            "spec": json.loads(fig.to_json()),
        }
    
    @tool
    async def export_report(
        self,
        report: dict,
        format: str = "pdf",
        destination: str = "download",
    ) -> dict:
        """
        Export a report to various formats.
        
        Args:
            report: Report data to export
            format: 'pdf', 'xlsx', 'pptx', 'html', or 'json'
            destination: 'download', 's3', 'email', or 'slack'
        """
        if format == "pdf":
            return await self._export_pdf(report, destination)
        elif format == "xlsx":
            return await self._export_excel(report, destination)
        elif format == "pptx":
            return await self._export_powerpoint(report, destination)
        elif format == "html":
            return await self._export_html(report, destination)
        elif format == "json":
            return await self._export_json(report, destination)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def _export_pdf(self, report: dict, destination: str) -> dict:
        """Export report as PDF using WeasyPrint."""
        from weasyprint import HTML, CSS
        
        # Generate HTML content
        html_content = self._report_to_html(report)
        
        # Convert to PDF
        pdf = HTML(string=html_content).write_pdf()
        
        if destination == "s3":
            import boto3
            s3 = boto3.client("s3")
            key = f"reports/{report['report_type']}/{report.get('date', datetime.now().strftime('%Y-%m-%d'))}.pdf"
            s3.put_object(Bucket="analytics-reports", Key=key, Body=pdf, ContentType="application/pdf")
            return {"status": "success", "location": f"s3://analytics-reports/{key}"}
        
        return {"status": "success", "content": pdf, "format": "pdf"}
    
    async def _export_excel(self, report: dict, destination: str) -> dict:
        """Export report as Excel workbook."""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Summary sheet
            summary_df = pd.DataFrame([report.get("summary", report.get("kpi_dashboard", {}))])
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            
            # Data sheets
            for key, value in report.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    pd.DataFrame(value).to_excel(writer, sheet_name=key[:31], index=False)
        
        output.seek(0)
        
        if destination == "s3":
            import boto3
            s3 = boto3.client("s3")
            key = f"reports/{report['report_type']}/{report.get('date', datetime.now().strftime('%Y-%m-%d'))}.xlsx"
            s3.put_object(Bucket="analytics-reports", Key=key, Body=output.read())
            return {"status": "success", "location": f"s3://analytics-reports/{key}"}
        
        return {"status": "success", "content": output.read(), "format": "xlsx"}
    
    def _report_to_html(self, report: dict) -> str:
        """Convert report dict to HTML for PDF generation."""
        # Simplified HTML template
        html = f"""
        <html>
        <head><title>Marketing Report - {report.get('date', 'Custom')}</title></head>
        <body>
            <h1>Marketing Performance Report</h1>
            <p>Generated: {report.get('generated_at', datetime.utcnow().isoformat())}</p>
            <hr>
            <pre>{json.dumps(report, indent=2, default=str)}</pre>
        </body>
        </html>
        """
        return html
    
    # --- Helper methods ---
    
    async def _fetch_daily_metrics(self, date: str) -> dict:
        """Fetch all metrics for a specific date."""
        query = """
            SELECT 
                SUM(spend) as total_spend,
                SUM(revenue) as total_revenue,
                SUM(conversions) as total_conversions,
                SUM(clicks) as total_clicks,
                SUM(impressions) as total_impressions,
                COUNT(DISTINCT campaign_id) as active_campaigns
            FROM daily_marketing_metrics
            WHERE date = $1
        """
        async with self.db_pool.acquire() as conn:
            record = await conn.fetchrow(query, date)
            return dict(record) if record else {}
    
    def _calculate_changes(self, current: dict, prev_day: dict, prev_week: dict) -> dict:
        """Calculate day-over-day and week-over-week changes."""
        changes = {}
        for key in current:
            if isinstance(current[key], (int, float)) and current[key] != 0:
                dod = (current[key] - prev_day.get(key, 0)) / max(abs(prev_day.get(key, 1)), 1)
                wow = (current[key] - prev_week.get(key, 0)) / max(abs(prev_week.get(key, 1)), 1)
                changes[key] = {
                    "day_over_day": f"{dod * 100:+.1f}%",
                    "week_over_week": f"{wow * 100:+.1f}%",
                }
        return changes
    
    def _generate_daily_insights(self, metrics: dict, changes: dict) -> list:
        """Generate actionable insights from daily data."""
        insights = []
        
        # ROAS insight
        if "total_revenue" in metrics and "total_spend" in metrics:
            roas = metrics["total_revenue"] / max(metrics["total_spend"], 1)
            if roas > 4:
                insights.append(f"Strong ROAS of {roas:.2f} — consider increasing budget")
            elif roas < 1.5:
                insights.append(f"Low ROAS of {roas:.2f} — review campaign targeting and creative")
        
        # Conversion rate insight
        if "total_conversions" in metrics and "total_clicks" in metrics:
            cvr = metrics["total_conversions"] / max(metrics["total_clicks"], 1)
            if cvr < 0.02:
                insights.append(f"Low conversion rate ({cvr*100:.1f}%) — check landing page experience")
        
        return insights
    
    def _generate_recommendations(self, metrics: dict, changes: dict) -> list:
        """Generate actionable recommendations."""
        recommendations = []
        
        if "total_spend" in changes:
            spend_change = changes["total_spend"].get("day_over_day", "0%")
            if "+" in spend_change and float(spend_change.strip("%+")) > 20:
                recommendations.append("Spend increased significantly — verify tracking is working correctly")
        
        return recommendations
    
    def _pct_change(self, current: float, previous: float) -> Optional[float]:
        """Calculate percentage change."""
        if previous is None or previous == 0:
            return None
        return (current - previous) / previous
    
    def _build_custom_query(
        self, metrics: list[str], dimensions: list[str],
        start: str, end: str, filters: Optional[dict], group_by: Optional[str]
    ) -> str:
        """Build a dynamic SQL query for custom reports."""
        select_cols = dimensions + [f"SUM({m}) as {m}" for m in metrics]
        query = f"SELECT {', '.join(select_cols)} FROM marketing_metrics WHERE date BETWEEN '{start}' AND '{end}'"
        
        if filters:
            for col, val in filters.items():
                query += f" AND {col} = '{val}'"
        
        group_cols = group_by if group_by else dimensions[0] if dimensions else None
        if group_cols:
            query += f" GROUP BY {group_cols}"
        
        return query
    
    def _create_chart(self, df: pd.DataFrame, metric: str, dimension: Optional[str]) -> dict:
        """Create a chart specification."""
        import plotly.express as px
        import json
        
        if dimension:
            fig = px.bar(df, x=dimension, y=metric, title=f"{metric} by {dimension}")
        else:
            fig = px.line(df, y=metric, title=metric)
        
        return json.loads(fig.to_json())
    
    def _summarize_custom_data(self, df: pd.DataFrame, metrics: list[str], dimensions: list[str]) -> dict:
        """Generate summary statistics for custom data."""
        summary = {"row_count": len(df)}
        for metric in metrics:
            if metric in df.columns:
                summary[metric] = {
                    "total": df[metric].sum(),
                    "mean": df[metric].mean(),
                    "min": df[metric].min(),
                    "max": df[metric].max(),
                }
        return summary
    
    async def _generate_daily_charts(self, date: str) -> list:
        """Generate chart specifications for daily report."""
        # Fetch hourly data for intraday chart
        query = """
            SELECT hour, spend, conversions, revenue
            FROM hourly_marketing_metrics
            WHERE date = $1
            ORDER BY hour
        """
        async with self.db_pool.acquire() as conn:
            records = await conn.fetch(query, date)
            df = pd.DataFrame([dict(r) for r in records])
        
        charts = []
        if len(df) > 0:
            # Intraday spend chart
            import plotly.express as px
            import json
            
            fig = px.line(df, x="hour", y="spend", title="Intraday Spend")
            charts.append(json.loads(fig.to_json()))
            
            # Channel breakdown pie chart
            channel_query = """
                SELECT channel, spend
                FROM daily_channel_metrics
                WHERE date = $1
            """
            async with self.db_pool.acquire() as conn:
                channel_records = await conn.fetch(channel_query, date)
                channel_df = pd.DataFrame([dict(r) for r in channel_records])
            
            if len(channel_df) > 0:
                fig2 = px.pie(channel_df, names="channel", values="spend", title="Spend by Channel")
                charts.append(json.loads(fig2.to_json()))
        
        return charts
```

---

## 6. Real-Time Dashboards

### 6.1 Architecture

Real-time dashboards use a **streaming architecture** with Kafka for data ingestion and WebSockets for live updates.

```
┌─────────────┐     ┌──────────┐     ┌──────────────┐     ┌─────────────┐
│  Ad Platforms│────▶│  Kafka   │────▶│  Stream      │────▶│  Dashboard  │
│  & CRM      │     │  Topics  │     │  Processor   │     │  (React)    │
└─────────────┘     └──────────┘     │  (Flink)     │     └─────────────┘
                                      └──────────────┘            ▲
                                                                  │
                                      ┌──────────────┐            │
                                      │  Redis       │────────────┘
                                      │  (Cache)     │   WebSocket
                                      └──────────────┘
```

### 6.2 Backend (FastAPI + WebSockets)

```python
# dashboard/server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import aioredis
from datetime import datetime

app = FastAPI(title="Marketing Analytics Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager for WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.redis = None
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await manager.connect(websocket)
    try:
        # Send initial data
        initial_data = await get_dashboard_snapshot()
        await websocket.send_json({
            "type": "snapshot",
            "data": initial_data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                # Client subscribes to specific metrics
                pass
            elif message.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def get_dashboard_snapshot() -> dict:
    """Get current dashboard data from Redis cache."""
    redis = await aioredis.create_redis_pool("redis://localhost")
    
    # Fetch cached metrics
    metrics = {}
    keys = [
        "dashboard:total_spend_today",
        "dashboard:total_revenue_today",
        "dashboard:total_conversions_today",
        "dashboard:roas_today",
        "dashboard:channel_breakdown",
        "dashboard:campaign_performance",
        "dashboard:attribution_summary",
        "dashboard:forecast_next_7d",
    ]
    
    for key in keys:
        value = await redis.get(key)
        if value:
            metrics[key.replace("dashboard:", "")] = json.loads(value)
    
    redis.close()
    await redis.wait_closed()
    
    return metrics

async def metrics_updater():
    """Background task that updates dashboard metrics periodically."""
    while True:
        try:
            # Fetch latest metrics from database
            metrics = await calculate_realtime_metrics()
            
            # Cache in Redis
            redis = await aioredis.create_redis_pool("redis://localhost")
            for key, value in metrics.items():
                await redis.setex(
                    f"dashboard:{key}",
                    300,  # 5 minute TTL
                    json.dumps(value),
                )
            redis.close()
            await redis.wait_closed()
            
            # Broadcast to connected clients
            await manager.broadcast({
                "type": "update",
                "data": metrics,
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        except Exception as e:
            print(f"Error updating metrics: {e}")
        
        await asyncio.sleep(30)  # Update every 30 seconds

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(metrics_updater())

async def calculate_realtime_metrics() -> dict:
    """Calculate real-time metrics from the database."""
    # This would query the database for latest metrics
    # Simplified implementation
    return {
        "total_spend_today": 15234.56,
        "total_revenue_today": 62341.23,
        "total_conictions_today": 342,
        "roas_today": 4.09,
        "channel_breakdown": [
            {"channel": "google_ads", "spend": 5000, "revenue": 22000, "roas": 4.4},
            {"channel": "meta_ads", "spend": 4000, "revenue": 18000, "roas": 4.5},
            {"channel": "linkedin_ads", "spend": 3000, "revenue": 12000, "roas": 4.0},
        ],
    }
```

### 6.3 Frontend (React + Recharts)

```tsx
// dashboard/src/components/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area,
} from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface DashboardData {
  total_spend_today: number;
  total_revenue_today: number;
  total_conversions_today: number;
  roas_today: number;
  channel_breakdown: ChannelData[];
  attribution_summary: AttributionData[];
  forecast_next_7d: ForecastData[];
}

interface ChannelData {
  channel: string;
  spend: number;
  revenue: number;
  roas: number;
}

interface AttributionData {
  channel: string;
  attribution_credit: number;
}

interface ForecastData {
  date: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export const MarketingDashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/dashboard');

    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'snapshot' || message.type === 'update') {
        setData(message.data);
        setLastUpdate(message.timestamp);
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => ws.close();
  }, []);

  if (!data) {
    return <div className="flex items-center justify-center h-screen">Loading dashboard...</div>;
  }

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Marketing Analytics Dashboard</h1>
        <div className="flex items-center gap-4">
          <Badge variant={wsConnected ? 'success' : 'destructive'}>
            {wsConnected ? 'Live' : 'Disconnected'}
          </Badge>
          <span className="text-sm text-gray-500">
            Last update: {new Date(lastUpdate).toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Today's Spend"
          value={`$${data.total_spend_today.toLocaleString()}`}
          trend="+12.5%"
          trendDirection="up"
        />
        <KPICard
          title="Today's Revenue"
          value={`$${data.total_revenue_today.toLocaleString()}`}
          trend="+8.3%"
          trendDirection="up"
        />
        <KPICard
          title="Conversions"
          value={data.total_conversions_today.toLocaleString()}
          trend="-2.1%"
          trendDirection="down"
        />
        <KPICard
          title="Blended ROAS"
          value={data.roas_today.toFixed(2)}
          trend="+0.3"
          trendDirection="up"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Channel Performance</h3>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.channel_breakdown}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="channel" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="spend" fill="#8884d8" name="Spend" />
                <Bar dataKey="revenue" fill="#82ca9d" name="Revenue" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Attribution Breakdown</h3>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={data.attribution_summary}
                  dataKey="attribution_credit"
                  nameKey="channel"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ channel, percent }) => `${channel}: ${(percent * 100).toFixed(0)}%`}
                >
                  {data.attribution_summary.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-6">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">7-Day Revenue Forecast</h3>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={data.forecast_next_7d}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="yhat"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.3}
                  name="Forecast"
                />
                <Area
                  type="monotone"
                  dataKey="yhat_upper"
                  stroke="#82ca9d"
                  fill="#82ca9d"
                  fillOpacity={0.1}
                  name="Upper Bound"
                />
                <Area
                  type="monotone"
                  dataKey="yhat_lower"
                  stroke="#ff7300"
                  fill="#ff7300"
                  fillOpacity={0.1}
                  name="Lower Bound"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// KPI Card Component
interface KPICardProps {
  title: string;
  value: string;
  trend: string;
  trendDirection: 'up' | 'down';
}

const KPICard: React.FC<KPICardProps> = ({ title, value, trend, trendDirection }) => (
  <Card>
    <CardContent className="pt-6">
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      <p className={`text-sm mt-2 ${trendDirection === 'up' ? 'text-green-600' : 'text-red-600'}`}>
        {trendDirection === 'up' ? '↑' : '↓'} {trend}
      </p>
    </CardContent>
  </Card>
);
```

---

## 7. Ad Platform & CRM Integration

### 7.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Integration Layer                          │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ Google Ads   │ Meta Ads     │ LinkedIn Ads │ TikTok Ads     │
│ Connector    │ Connector    │ Connector    │ Connector      │
├──────────────┴──────────────┴──────────────┴────────────────┤
│                    Unified Data Schema                        │
├──────────────────────────────────────────────────────────────┤
│  Salesforce  │  HubSpot     │  GA4          │  Mixpanel     │
│  Connector   │  Connector   │  Connector    │  Connector    │
└──────────────────────────────────────────────────────────────┘
```

### 7.2 Connector Implementation

```python
# integrations/base_connector.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import asyncio

@dataclass
class MarketingDataPoint:
    """Unified schema for all marketing data."""
    source: str                    # 'google_ads', 'meta_ads', etc.
    date: str                      # YYYY-MM-DD
    campaign_id: str
    campaign_name: str
    ad_group_id: Optional[str]
    ad_group_name: Optional[str]
    channel: str                   # Normalized channel name
    impressions: int
    clicks: int
    spend: float                   # In USD
    conversions: int
    revenue: float                 # In USD
    currency: str = "USD"
    raw_data: Optional[dict] = None

class BaseAdPlatformConnector(ABC):
    """Abstract base class for ad platform connectors."""
    
    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.rate_limiter = asyncio.Semaphore(10)  # Max 10 concurrent requests
    
    @abstractmethod
    async def authenticate(self) -> str:
        """Authenticate and return access token."""
        pass
    
    @abstractmethod
    async def fetch_campaigns(
        self, start_date: str, end_date: str
    ) -> List[MarketingDataPoint]:
        """Fetch campaign data for date range."""
        pass
    
    @abstractmethod
    async def fetch_ad_groups(
        self, campaign_id: str, start_date: str, end_date: str
    ) -> List[MarketingDataPoint]:
        """Fetch ad group data."""
        pass
    
    @abstractmethod
    async def fetch_ads(
        self, ad_group_id: str, start_date: str, end_date: str
    ) -> List[MarketingDataPoint]:
        """Fetch individual ad data."""
        pass
    
    async def fetch_all(
        self, start_date: str, end_date: str
    ) -> AsyncGenerator[MarketingDataPoint, None]:
        """Fetch all data (campaigns + ad groups + ads)."""
        campaigns = await self.fetch_campaigns(start_date, end_date)
        for campaign in campaigns:
            yield campaign
        
        # Fetch ad groups for each campaign
        for campaign in campaigns:
            ad_groups = await self.fetch_ad_groups(
                campaign.campaign_id, start_date, end_date
            )
            for ad_group in ad_groups:
                yield ad_group
            
            # Fetch ads for each ad group
            for ad_group in ad_groups:
                ads = await self.fetch_ads(
                    ad_group.ad_group_id, start_date, end_date
                )
                for ad in ads:
                    yield ad


# integrations/google_ads_connector.py
from .base_connector import BaseAdPlatformConnector, MarketingDataPoint
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import asyncio

class GoogleAdsConnector(BaseAdPlatformConnector):
    """Google Ads API connector."""
    
    def __init__(self, credentials: dict):
        super().__init__(credentials)
        self.client = None
        self.customer_id = credentials.get("customer_id")
    
    async def authenticate(self) -> str:
        """Initialize Google Ads client."""
        self.client = GoogleAdsClient.load_from_storage(
            self.credentials.get("config_path", "google-ads.yaml")
        )
        return "authenticated"
    
    async def fetch_campaigns(
        self, start_date: str, end_date: str
    ) -> List[MarketingDataPoint]:
        """Fetch campaign performance data."""
        service = self.client.get_service("GoogleAdsService")
        
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        """
        
        response = service.search_stream(
            customer_id=self.customer_id, query=query
        )
        
        results = []
        for batch in response:
            for row in batch.results:
                campaign = row.campaign
                metrics = row.metrics
                segments = row.segments
                
                results.append(MarketingDataPoint(
                    source="google_ads",
                    date=segments.date,
                    campaign_id=str(campaign.id),
                    campaign_name=campaign.name,
                    ad_group_id=None,
                    ad_group_name=None,
                    channel="google_ads",
                    impressions=metrics.impressions,
                    clicks=metrics.clicks,
                    spend=metrics.cost_micros / 1_000_000,  # Convert micros to units
                    conversions=int(metrics.conversions),
                    revenue=metrics.conversions_value,
                    raw_data={"campaign_status": campaign.status},
                ))
        
        return results
    
    async def fetch_ad_groups(
        self, campaign_id: str, start_date: str, end_date: str
    ) -> List[MarketingDataPoint]:
        """Fetch ad group performance data."""
        service = self.client.get_service("GoogleAdsService")
        
        query = f"""
            SELECT
                campaign.id,
                ad_group.id,
                ad_group.name,
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM ad_group
            WHERE campaign.id = {campaign_id}
            AND segments.date BETWEEN '{start_date}' AND '{end_date}'
        """
        
        response = service.search_stream(
            customer_id=self.customer_id, query=query
        )
        
        results = []
        for batch in response:
            for row in batch.results:
                ad_group = row.ad_group
                metrics = row.metrics
                segments = row.segments
                
                results.append(MarketingDataPoint(
                    source="google_ads",
                    date=segments.date,
                    campaign_id=str(row.campaign.id),
                    campaign_name="",
                    ad_group_id=str(ad_group.id),
                    ad_group_name=ad_group.name,
                    channel="google_ads",
                    impressions=metrics.impressions,
                    clicks=metrics.clicks,
                    spend=metrics.cost_micros / 1_000_000,
                    conversions=int(metrics.conversions),
                    revenue=metrics.conversions_value,
                ))
        
        return results


# integrations/meta_ads_connector.py
import aiohttp
from typing import List
from .base_connector import BaseAdPlatformConnector, MarketingDataPoint

class MetaAdsConnector(BaseAdPlatformConnector):
    """Meta (Facebook) Ads API connector."""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, credentials: dict):
        super().__init__(credentials)
        self.access_token = credentials.get("access_token")
        self.ad_account_id = credentials.get("ad_account_id")
    
    async def authenticate(self) -> str:
        """Verify access token."""
        url = f"{self.BASE_URL}/me"
        params = {"access_token": self.access_token}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return "authenticated"
                raise Exception(f"Authentication failed: {resp.status}")
    
    async def fetch_campaigns(
        self, start_date: str, end_date: str
    ) -> List[MarketingDataPoint]:
        """Fetch campaign data from Meta Ads."""
        url = f"{self.BASE_URL}/{self.ad_account_id}/insights"
        
        params = {
            "access_token": self.access_token,
            "time_range": f'{{"since":"{start_date}","until":"{end_date}"}}',
            "fields": "campaign_id,campaign_name,impressions,clicks,spend,actions,action_values",
            "level": "campaign",
            "time_increment": 1,
        }
        
        async with self.rate_limiter:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
        
        results = []
        for item in data.get("data", []):
            # Extract conversions from actions
            conversions = 0
            revenue = 0.0
            for action in item.get("actions", []):
                if action.get("action_type") in ["purchase", "conversion", "lead"]:
                    conversions += int(action.get("value", 0))
            for value in item.get("action_values", []):
                if value.get("action_type") in ["purchase", "conversion"]:
                    revenue += float(value.get("value", 0))
            
            results.append(MarketingDataPoint(
                source="meta_ads",
                date=item.get("date_start"),
                campaign_id=item.get("campaign_id"),
                campaign_name=item.get("campaign_name"),
                ad_group_id=None,
                ad_group_name=None,
                channel="meta_ads",
                impressions=int(item.get("impressions", 0)),
                clicks=int(item.get("clicks", 0)),
                spend=float(item.get("spend", 0)),
                conversions=conversions,
                revenue=revenue,
            ))
        
        return results


# integrations/salesforce_connector.py
from simple_salesforce import Salesforce
from typing import List
from .base_connector import BaseAdPlatformConnector, MarketingDataPoint

class SalesforceConnector(BaseAdPlatformConnector):
    """Salesforce CRM connector."""
    
    def __init__(self, credentials: dict):
        super().__init__(credentials)
        self.sf = None
    
    async def authenticate(self) -> str:
        """Authenticate with Salesforce."""
        self.sf = Salesforce(
            username=self.credentials["username"],
            password=self.credentials["password"],
            security_token=self.credentials["security_token"],
            domain=self.credentials.get("domain", "login"),
        )
        return "authenticated"
    
    async def fetch_opportunities(
        self, start_date: str, end_date: str
    ) -> List[dict]:
        """Fetch opportunity data."""
        query = f"""
            SELECT Id, Name, Amount, StageName, CloseDate, LeadSource,
                   AccountId, Account.Name, OwnerId, Owner.Name,
                   Probability, Type, NextStep
            FROM Opportunity
            WHERE CloseDate >= {start_date}
            AND CloseDate <= {end_date}
            AND IsClosed = true
            AND IsWon = true
        """
        
        results = self.sf.query_all(query)
        return results.get("records", [])
    
    async def fetch_leads(
        self, start_date: str, end_date: str
    ) -> List[dict]:
        """Fetch lead data."""
        query = f"""
            SELECT Id, FirstName, LastName, Email, Company, Status,
                   LeadSource, CreatedDate, ConvertedDate, OwnerId
            FROM Lead
            WHERE CreatedDate >= {start_date}T00:00:00Z
            AND CreatedDate <= {end_date}T23:59:59Z
        """
        
        results = self.sf.query_all(query)
        return results.get("records", [])


# integrations/integration_manager.py
from typing import Dict, List
from .google_ads_connector import GoogleAdsConnector
from .meta_ads_connector import MetaAdsConnector
from .salesforce_connector import SalesforceConnector
from .base_connector import MarketingDataPoint
import asyncio

class IntegrationManager:
    """Manages all platform integrations."""
    
    def __init__(self):
        self.connectors: Dict[str, BaseAdPlatformConnector] = {}
    
    def register_connector(self, name: str, connector: BaseAdPlatformConnector):
        """Register a platform connector."""
        self.connectors[name] = connector
    
    async def fetch_all_data(
        self, start_date: str, end_date: str
    ) -> List[MarketingDataPoint]:
        """Fetch data from all registered connectors."""
        all_data = []
        
        tasks = []
        for name, connector in self.connectors.items():
            await connector.authenticate()
            task = connector.fetch_campaigns(start_date, end_date)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, result in zip(self.connectors.keys(), results):
            if isinstance(result, Exception):
                print(f"Error fetching from {name}: {result}")
                continue
            all_data.extend(result)
        
        return all_data
    
    async def sync_to_warehouse(
        self, start_date: str, end_date: str, db_pool
    ):
        """Sync all data to the analytics warehouse."""
        data = await self.fetch_all_data(start_date, end_date)
        
        # Insert into database
        async with db_pool.acquire() as conn:
            for point in data:
                await conn.execute(
                    """
                    INSERT INTO marketing_metrics (
                        source, date, campaign_id, campaign_name,
                        channel, impressions, clicks, spend,
                        conversions, revenue, currency, raw_data
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (source, date, campaign_id) DO UPDATE SET
                        impressions = EXCLUDED.impressions,
                        clicks = EXCLUDED.clicks,
                        spend = EXCLUDED.spend,
                        conversions = EXCLUDED.conversions,
                        revenue = EXCLUDED.revenue
                    """,
                    point.source, point.date, point.campaign_id,
                    point.campaign_name, point.channel,
                    point.impressions, point.clicks, point.spend,
                    point.conversions, point.revenue, point.currency,
                    point.raw_data,
                )
        
        return len(data)
```

### 7.3 Webhook Handler for Real-Time Events

```python
# integrations/webhooks.py
from fastapi import FastAPI, Request, HTTPException
from hmac import compare_digest
import hashlib
import json

app = FastAPI()

@app.post("/webhook/meta")
async def meta_webhook(request: Request):
    """Handle Meta Ads webhook events."""
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    # Verify signature
    expected = hashlib.sha256(
        payload, 
        key=META_APP_SECRET.encode()
    ).hexdigest()
    
    if not compare_digest(f"sha256={expected}", signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = json.loads(payload)
    
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            await process_meta_change(change)
    
    return {"status": "ok"}

@app.post("/webhook/google-ads")
async def google_ads_webhook(request: Request):
    """Handle Google Ads offline conversion uploads."""
    data = await request.json()
    
    for conversion in data.get("conversions", []):
        await process_google_conversion(conversion)
    
    return {"status": "ok", "processed": len(data.get("conversions", []))}

async def process_meta_change(change: dict):
    """Process a Meta Ads change event."""
    # Update local database with new campaign/ad status
    pass

async def process_google_conversion(conversion: dict):
    """Process a Google Ads offline conversion."""
    # Store conversion data for attribution
    pass
```

---

## 8. Code Examples & Snippets

### 8.1 Complete Agent Setup

```python
# main.py - Complete system setup
import asyncio
import asyncpg
from agents.orchestrator import AnalyticsOrchestrator
from agents.data_collector import DataCollectorAgent
from agents.attribution_engine import AttributionEngineAgent
from agents.predictive_analytics import PredictiveAnalyticsAgent
from agents.reporting import ReportingAgent
from integrations.integration_manager import IntegrationManager
from integrations.google_ads_connector import GoogleAdsConnector
from integrations.meta_ads_connector import MetaAdsConnector

async def main():
    # Initialize database pool
    db_pool = await asyncpg.create_pool(
        host="localhost",
        database="marketing_analytics",
        user="analytics",
        password="secure_password",
        min_size=5,
        max_size=20,
    )
    
    # Initialize integration manager
    integration_manager = IntegrationManager()
    integration_manager.register_connector(
        "google_ads",
        GoogleAdsConnector({
            "customer_id": "1234567890",
            "config_path": "config/google-ads.yaml",
        })
    )
    integration_manager.register_connector(
        "meta_ads",
        MetaAdsConnector({
            "access_token": "your_access_token",
            "ad_account_id": "act_1234567890",
        })
    )
    
    # Initialize agents
    data_collector = DataCollectorAgent(db_pool)
    attribution_engine = AttributionEngineAgent(db_pool)
    predictive_analytics = PredictiveAnalyticsAgent(db_pool)
    reporting = ReportingAgent(db_pool)
    
    # Initialize orchestrator
    orchestrator = AnalyticsOrchestrator()
    
    # Example: Run a complete analysis workflow
    session_id = "session_001"
    user_id = "user_123"
    
    # 1. Collect data
    print("Step 1: Collecting data...")
    ad_data = await data_collector.fetch_ad_data(
        platform="google_ads",
        start_date="2026-09-01",
        end_date="2026-09-30",
    )
    print(f"Collected {len(ad_data)} records from Google Ads")
    
    # 2. Run attribution
    print("\nStep 2: Running attribution analysis...")
    attribution_results = await attribution_engine.run_markov_attribution(
        start_date="2026-09-01",
        end_date="2026-09-30",
    )
    print(f"Attribution results: {attribution_results['attribution']}")
    
    # 3. Generate forecast
    print("\nStep 3: Generating forecast...")
    forecast = await predictive_analytics.forecast_metrics(
        metric="revenue",
        start_date="2026-09-01",
        end_date="2026-09-30",
        forecast_horizon=30,
    )
    print(f"Forecast: {forecast['forecast'][:5]}")
    
    # 4. Generate report
    print("\nStep 4: Generating report...")
    report = await reporting.generate_monthly_report(month="2026-09")
    print(f"Report generated with {len(report)} sections")
    
    # Cleanup
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 8.2 Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Main application
  analytics-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://analytics:secure_password@postgres:5432/marketing_analytics
      - REDIS_URL=redis://redis:6379
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
      - kafka
    volumes:
      - ./models:/app/models
      - ./config:/app/config

  # Stream processor
  stream-processor:
    build: ./stream_processor
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - DATABASE_URL=postgresql://analytics:secure_password@postgres:5432/marketing_analytics
    depends_on:
      - kafka
      - postgres

  # PostgreSQL
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=marketing_analytics
      - POSTGRES_USER=analytics
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Kafka
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  # MLflow (model registry)
  mlflow:
    image: mlflow/mlflow:latest
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://analytics:secure_password@postgres:5432/mlflow
      - MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://mlflow-artifacts/
    depends_on:
      - postgres

  # Airflow (data pipelines)
  airflow:
    image: apache/airflow:2.7.0
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://analytics:secure_password@postgres:5432/airflow
    volumes:
      - ./dags:/opt/airflow/dags
      - ./sql:/opt/airflow/sql
    ports:
      - "8080:8080"
    depends_on:
      - postgres

  # Dashboard frontend
  dashboard:
    build: ./dashboard
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8000/ws

volumes:
  postgres_data:
  redis_data:
```

### 8.3 Database Schema

```sql
-- sql/init.sql
-- Core marketing metrics table
CREATE TABLE IF NOT EXISTS marketing_metrics (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    campaign_id VARCHAR(255) NOT NULL,
    campaign_name VARCHAR(500),
    ad_group_id VARCHAR(255),
    ad_group_name VARCHAR(500),
    channel VARCHAR(100) NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(15, 4) DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue DECIMAL(15, 4) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, date, campaign_id)
);

-- Customer journey table (for attribution)
CREATE TABLE IF NOT EXISTS customer_journeys (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    touchpoint_order INTEGER NOT NULL,
    channel VARCHAR(100) NOT NULL,
    campaign_id VARCHAR(255),
    timestamp TIMESTAMP NOT NULL,
    converted BOOLEAN DEFAULT FALSE,
    revenue DECIMAL(15, 4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attribution results
CREATE TABLE IF NOT EXISTS attribution_results (
    id SERIAL PRIMARY KEY,
    model_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    channel VARCHAR(100) NOT NULL,
    attribution_credit DECIMAL(10, 6) NOT NULL,
    removal_effect DECIMAL(10, 6),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predictions
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    model_type VARCHAR(50) NOT NULL,
    metric VARCHAR(100) NOT NULL,
    prediction_date DATE NOT NULL,
    predicted_value DECIMAL(15, 4) NOT NULL,
    lower_bound DECIMAL(15, 4),
    upper_bound DECIMAL(15, 4),
    confidence DECIMAL(5, 4),
    features JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reports
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL,
    start_date DATE,
    end_date DATE,
    content JSONB NOT NULL,
    format VARCHAR(20) DEFAULT 'json',
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_metrics_date ON marketing_metrics(date);
CREATE INDEX idx_metrics_channel ON marketing_metrics(channel);
CREATE INDEX idx_metrics_campaign ON marketing_metrics(campaign_id);
CREATE INDEX idx_journeys_customer ON customer_journeys(customer_id);
CREATE INDEX idx_journeys_timestamp ON customer_journeys(timestamp);
CREATE INDEX idx_attribution_dates ON attribution_results(start_date, end_date);
CREATE INDEX idx_predictions_date ON predictions(prediction_date);
```

### 8.4 Configuration

```yaml
# config/settings.yaml
# Application settings
app:
  name: "Marketing Analytics AI"
  version: "1.0.0"
  debug: false

# LLM Configuration
llm:
  provider: "openai"
  model: "gpt-4o"
  temperature: 0.1
  max_tokens: 4096
  api_key: ${OPENAI_API_KEY}

# Database
database:
  host: "localhost"
  port: 5432
  name: "marketing_analytics"
  user: "analytics"
  password: ${DB_PASSWORD}
  pool_size: 20

# Redis
redis:
  host: "localhost"
  port: 6379
  db: 0

# Kafka
kafka:
  bootstrap_servers: "localhost:9092"
  topics:
    - "marketing-events"
    - "attribution-results"
    - "predictions"

# Attribution
attribution:
  default_model: "markov_chain"
  models:
    markov_chain:
      order: 1
      min_journeys: 100
    shapley:
      max_channels: 15
      approximation_samples: 10000
    deep_learning:
      model_type: "lstm"
      epochs: 50
      batch_size: 64

# Predictions
predictions:
  forecast_horizon_days: 30
  models:
    prophet:
      changepoint_prior_scale: 0.05
      seasonality_prior_scale: 10.0
    arima:
      order: [7, 1, 7]
    lstm:
      hidden_size: 64
      num_layers: 2
      sequence_length: 30

# Integrations
integrations:
  google_ads:
    customer_id: "1234567890"
    config_path: "config/google-ads.yaml"
  meta_ads:
    ad_account_id: "act_1234567890"
    access_token: ${META_ACCESS_TOKEN}
  salesforce:
    username: ${SF_USERNAME}
    password: ${SF_PASSWORD}
    security_token: ${SF_SECURITY_TOKEN}

# Dashboard
dashboard:
  update_interval_seconds: 30
  cache_ttl_seconds: 300
  max_websocket_connections: 100
```

---

## 9. Testing Strategy

### 9.1 Test Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Pyramid                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                    ┌──────────┐                               │
│                    │   E2E    │  (5%)                        │
│                    │  Tests   │  Full agent workflows        │
│                   ┌┴──────────┴┐                              │
│                   │ Integration │  (15%)                     │
│                   │    Tests    │  Agent + DB + APIs         │
│                  ┌┴─────────────┴┐                            │
│                  │    Unit       │  (80%)                    │
│                  │    Tests      │  Individual functions      │
│                  └───────────────┘                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Unit Tests

```python
# tests/test_markov_attribution.py
import pytest
import numpy as np
from attribution.markov_chain import MarkovChainAttribution

class TestMarkovChainAttribution:
    """Unit tests for Markov Chain attribution model."""
    
    def test_fit_basic(self):
        """Test basic model fitting."""
        journeys = [
            ['google_ads', 'email', 'direct'],
            ['meta_ads', 'google_ads', 'direct'],
            ['google_ads', 'direct'],
            ['email', 'direct'],
        ]
        conversions = [1, 1, 0, 0]
        
        mc = MarkovChainAttribution(order=1)
        mc.fit(journeys, conversions)
        
        assert mc.transition_matrix is not None
        assert len(mc.states) > 0
        assert 'Start' in mc.states
        assert 'Conversion' in mc.states
    
    def test_transition_matrix_rows_sum_to_one(self):
        """Test that transition matrix rows sum to 1."""
        journeys = [
            ['google_ads', 'email'],
            ['meta_ads', 'direct'],
            ['google_ads', 'direct'],
        ]
        conversions = [1, 0, 1]
        
        mc = MarkovChainAttribution(order=1)
        mc.fit(journeys, conversions)
        
        for i in range(len(mc.states)):
            row_sum = mc.transition_matrix[i].sum()
            assert abs(row_sum - 1.0) < 1e-6 or row_sum == 0
    
    def test_removal_effects_calculated(self):
        """Test that removal effects are calculated for all channels."""
        journeys = [
            ['google_ads', 'email', 'direct'],
            ['meta_ads', 'google_ads', 'direct'],
            ['google_ads', 'direct'],
            ['email', 'direct'],
            ['meta_ads', 'direct'],
        ]
        conversions = [1, 1, 0, 0, 1]
        
        mc = MarkovChainAttribution(order=1)
        mc.fit(journeys, conversions)
        
        assert len(mc.removal_effects) > 0
        for channel in ['google_ads', 'meta_ads', 'email', 'direct']:
            assert channel in mc.removal_effects
    
    def test_attribution_sums_to_one(self):
        """Test that attribution credits sum to 1."""
        journeys = [
            ['google_ads', 'email', 'direct'],
            ['meta_ads', 'google_ads', 'direct'],
            ['google_ads', 'direct'],
            ['email', 'direct'],
            ['meta_ads', 'direct'],
        ]
        conversions = [1, 1, 0, 0, 1]
        
        mc = MarkovChainAttribution(order=1)
        mc.fit(journeys, conversions)
        
        df = mc.get_attribution()
        total = df['attribution_credit'].sum()
        assert abs(total - 1.0) < 1e-6
    
    def test_empty_journeys(self):
        """Test handling of empty journey list."""
        mc = MarkovChainAttribution(order=1)
        mc.fit([], [])
        
        assert mc.transition_matrix is not None
    
    def test_single_channel(self):
        """Test with single channel journeys."""
        journeys = [
            ['google_ads'],
            ['google_ads'],
            ['google_ads'],
        ]
        conversions = [1, 0, 1]
        
        mc = MarkovChainAttribution(order=1)
        mc.fit(journeys, conversions)
        
        df = mc.get_attribution()
        assert len(df) == 1
        assert df.iloc[0]['channel'] == 'google_ads'
        assert df.iloc[0]['attribution_credit'] == 1.0


# tests/test_shapley_attribution.py
import pytest
import numpy as np
from attribution.shapley import ShapleyAttribution

class TestShapleyAttribution:
    """Unit tests for Shapley Value attribution."""
    
    def test_fit_basic(self):
        """Test basic Shapley value calculation."""
        channels = ['google_ads', 'meta_ads', 'email']
        
        def characteristic_function(subset):
            """Simple characteristic function for testing."""
            values = {
                (): 0,
                ('google_ads',): 10,
                ('meta_ads',): 8,
                ('email',): 5,
                ('google_ads', 'meta_ads'): 20,
                ('google_ads', 'email'): 16,
                ('meta_ads', 'email'): 14,
                ('google_ads', 'meta_ads', 'email'): 30,
            }
            return values.get(subset, 0)
        
        shapley = ShapleyAttribution()
        shapley.fit(channels, characteristic_function)
        
        assert len(shapley.shapley_values) == 3
        for channel in channels:
            assert channel in shapley.shapley_values
    
    def test_shapley_values_sum_to_total(self):
        """Test that Shapley values sum to total value."""
        channels = ['google_ads', 'meta_ads', 'email']
        
        def characteristic_function(subset):
            values = {
                (): 0,
                ('google_ads',): 10,
                ('meta_ads',): 8,
                ('email',): 5,
                ('google_ads', 'meta_ads'): 20,
                ('google_ads', 'email'): 16,
                ('meta_ads', 'email'): 14,
                ('google_ads', 'meta_ads', 'email'): 30,
            }
            return values.get(subset, 0)
        
        shapley = ShapleyAttribution()
        shapley.fit(channels, characteristic_function)
        
        total = sum(shapley.shapley_values.values())
        assert abs(total - 30) < 1e-6
    
    def test_symmetric_channels_get_equal_credit(self):
        """Test that symmetric channels receive equal Shapley values."""
        channels = ['channel_a', 'channel_b']
        
        def characteristic_function(subset):
            values = {
                (): 0,
                ('channel_a',): 10,
                ('channel_b',): 10,
                ('channel_a', 'channel_b'): 20,
            }
            return values.get(subset, 0)
        
        shapley = ShapleyAttribution()
        shapley.fit(channels, characteristic_function)
        
        assert abs(shapley.shapley_values['channel_a'] - shapley.shapley_values['channel_b']) < 1e-6
    
    def test_null_channel_gets_zero(self):
        """Test that a channel with no marginal contribution gets zero."""
        channels = ['active_channel', 'null_channel']
        
        def characteristic_function(subset):
            values = {
                (): 0,
                ('active_channel',): 10,
                ('null_channel',): 0,
                ('active_channel', 'null_channel'): 10,
            }
            return values.get(subset, 0)
        
        shapley = ShapleyAttribution()
        shapley.fit(channels, characteristic_function)
        
        assert shapley.shapley_values['null_channel'] == 0
        assert shapley.shapley_values['active_channel'] == 10


# tests/test_data_collector.py
import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock, patch

class TestDataCollectorAgent:
    """Unit tests for Data Collector Agent."""
    
    @pytest.fixture
    def mock_db_pool(self):
        pool = AsyncMock()
        return pool
    
    @pytest.fixture
    def agent(self, mock_db_pool):
        from agents.data_collector import DataCollectorAgent
        return DataCollectorAgent(mock_db_pool)
    
    @pytest.mark.asyncio
    async def test_clean_data_dedupe(self, agent):
        """Test deduplication cleaning operation."""
        df = pd.DataFrame({
            'channel': ['google', 'google', 'meta'],
            'spend': [100, 100, 200],
        })
        
        result = await agent.clean_data(df, operations=['dedupe'])
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_clean_data_fill_na(self, agent):
        """Test NA filling cleaning operation."""
        df = pd.DataFrame({
            'channel': ['google', None, 'meta'],
            'spend': [100, 200, None],
        })
        
        result = await agent.clean_data(df, operations=['fill_na'])
        assert result['channel'].isnull().sum() == 0
        assert result['spend'].isnull().sum() == 0
    
    @pytest.mark.asyncio
    async def test_clean_data_normalize(self, agent):
        """Test column name normalization."""
        df = pd.DataFrame({
            'Channel Name': ['google'],
            'Total Spend': [100],
        })
        
        result = await agent.clean_data(df, operations=['normalize'])
        assert 'channel_name' in result.columns
        assert 'total_spend' in result.columns
    
    @pytest.mark.asyncio
    async def test_get_data_summary(self, agent):
        """Test data summary generation."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2026-01-01', '2026-01-02']),
            'channel': ['google', 'meta'],
            'spend': [100.0, 200.0],
            'revenue': [400.0, 800.0],
        })
        
        summary = await agent.get_data_summary(df)
        assert summary['row_count'] == 2
        assert summary['column_count'] == 4
        assert 'date_range' in summary
        assert 'numeric_summary' in summary


# tests/test_predictive_analytics.py
import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, patch

class TestPredictiveAnalyticsAgent:
    """Unit tests for Predictive Analytics Agent."""
    
    @pytest.fixture
    def mock_db_pool(self):
        pool = AsyncMock()
        return pool
    
    @pytest.fixture
    def agent(self, mock_db_pool):
        from agents.predictive_analytics import PredictiveAnalyticsAgent
        return PredictiveAnalyticsAgent(mock_db_pool)
    
    def test_fit_hill_curve(self, agent):
        """Test Hill curve fitting."""
        spend = np.array([0, 100, 200, 500, 1000, 2000])
        conversions = np.array([0, 15, 25, 40, 48, 50])
        
        alpha, beta, gamma = agent._fit_hill_curve(spend, conversions)
        assert alpha > 0
        assert beta > 0
        assert gamma > 0
    
    def test_classify_anomaly_spike(self, agent):
        """Test anomaly classification for spikes."""
        df = pd.DataFrame({'value': [100, 105, 98, 102, 500]})
        row = pd.Series({'value': 500})
        
        result = agent._classify_anomaly(row, df, 'value')
        assert result == 'spike'
    
    def test_classify_anomaly_drop(self, agent):
        """Test anomaly classification for drops."""
        df = pd.DataFrame({'value': [100, 105, 98, 102, 5]})
        row = pd.Series({'value': 5})
        
        result = agent._classify_anomaly(row, df, 'value')
        assert result == 'drop'


# tests/test_reporting.py
import pytest
import pandas as pd
from unittest.mock import AsyncMock

class TestReportingAgent:
    """Unit tests for Reporting Agent."""
    
    @pytest.fixture
    def mock_db_pool(self):
        pool = AsyncMock()
        return pool
    
    @pytest.fixture
    def agent(self, mock_db_pool):
        from agents.reporting import ReportingAgent
        return ReportingAgent(mock_db_pool)
    
    def test_calculate_changes(self, agent):
        """Test change calculation between periods."""
        current = {'revenue': 1100, 'spend': 500}
        prev_day = {'revenue': 1000, 'spend': 480}
        prev_week = {'revenue': 900, 'spend': 450}
        
        changes = agent._calculate_changes(current, prev_day, prev_week)
        
        assert 'revenue' in changes
        assert 'spend' in changes
    
    def test_pct_change(self, agent):
        """Test percentage change calculation."""
        assert agent._pct_change(110, 100) == 0.1
        assert agent._pct_change(90, 100) == -0.1
        assert agent._pct_change(100, 0) is None
        assert agent._pct_change(100, None) is None
    
    def test_generate_daily_insights(self, agent):
        """Test insight generation."""
        metrics = {
            'total_revenue': 5000,
            'total_spend': 1000,
            'total_conversions': 50,
            'total_clicks': 1000,
        }
        changes = {}
        
        insights = agent._generate_daily_insights(metrics, changes)
        assert len(insights) > 0
        assert any('ROAS' in i for i in insights)


# tests/test_integration_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestIntegrationManager:
    """Unit tests for Integration Manager."""
    
    def test_register_connector(self):
        """Test connector registration."""
        from integrations.integration_manager import IntegrationManager
        from integrations.base_connector import BaseAdPlatformConnector
        
        manager = IntegrationManager()
        mock_connector = MagicMock(spec=BaseAdPlatformConnector)
        
        manager.register_connector("test_platform", mock_connector)
        assert "test_platform" in manager.connectors
    
    @pytest.mark.asyncio
    async def test_fetch_all_data_handles_errors(self):
        """Test that errors in one connector don't break others."""
        from integrations.integration_manager import IntegrationManager
        from integrations.base_connector import BaseAdPlatformConnector, MarketingDataPoint
        
        manager = IntegrationManager()
        
        # Working connector
        working = AsyncMock(spec=BaseAdPlatformConnector)
        working.fetch_campaigns.return_value = [
            MarketingDataPoint(
                source="working", date="2026-01-01",
                campaign_id="1", campaign_name="Test",
                channel="test", impressions=100,
                clicks=10, spend=50, conversions=1, revenue=100,
            )
        ]
        
        # Failing connector
        failing = AsyncMock(spec=BaseAdPlatformConnector)
        failing.fetch_campaigns.side_effect = Exception("API Error")
        
        manager.register_connector("working", working)
        manager.register_connector("failing", failing)
        
        results = await manager.fetch_all_data("2026-01-01", "2026-01-31")
        assert len(results) == 1
        assert results[0].source == "working"
```

### 9.3 Integration Tests

```python
# tests/integration/test_agent_workflows.py
import pytest
import pytest_asyncio
import asyncpg
from unittest.mock import patch, AsyncMock

@pytest_asyncio.fixture
async def db_pool():
    """Create test database pool."""
    pool = await asyncpg.create_pool(
        host="localhost",
        database="marketing_analytics_test",
        user="test",
        password="test",
        min_size=1,
        max_size=5,
    )
    
    # Create test tables
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS marketing_metrics (
                id SERIAL PRIMARY KEY,
                source VARCHAR(50),
                date DATE,
                campaign_id VARCHAR(255),
                channel VARCHAR(100),
                impressions INTEGER,
                clicks INTEGER,
                spend DECIMAL(15, 4),
                conversions INTEGER,
                revenue DECIMAL(15, 4)
            )
        """)
        
        # Insert test data
        await conn.execute("""
            INSERT INTO marketing_metrics (source, date, campaign_id, channel, impressions, clicks, spend, conversions, revenue)
            VALUES 
                ('google_ads', '2026-09-01', 'camp1', 'google_ads', 10000, 500, 1000, 50, 5000),
                ('meta_ads', '2026-09-01', 'camp2', 'meta_ads', 8000, 400, 800, 40, 4000),
                ('google_ads', '2026-09-02', 'camp1', 'google_ads', 12000, 600, 1200, 60, 6000),
                ('meta_ads', '2026-09-02', 'camp2', 'meta_ads', 9000, 450, 900, 45, 4500)
        """)
    
    yield pool
    
    # Cleanup
    async with pool.acquire() as conn:
        await conn.execute("DROP TABLE IF EXISTS marketing_metrics")
    await pool.close()

@pytest.mark.asyncio
async def test_end_to_end_attribution_workflow(db_pool):
    """Test complete attribution workflow from data to results."""
    from agents.attribution_engine import AttributionEngineAgent
    
    agent = AttributionEngineAgent(db_pool)
    
    # Run attribution
    results = await agent.run_markov_attribution(
        start_date="2026-09-01",
        end_date="2026-09-30",
    )
    
    assert results["model"] == "markov_chain"
    assert "attribution" in results
    assert len(results["attribution"]) > 0

@pytest.mark.asyncio
async def test_end_to_end_forecast_workflow(db_pool):
    """Test complete forecasting workflow."""
    from agents.predictive_analytics import PredictiveAnalyticsAgent
    
    agent = PredictiveAnalyticsAgent(db_pool)
    
    forecast = await agent.forecast_metrics(
        metric="revenue",
        start_date="2026-09-01",
        end_date="2026-09-30",
        forecast_horizon=7,
        model="prophet",
    )
    
    assert forecast["model"] == "prophet"
    assert "forecast" in forecast
    assert len(forecast["forecast"]) == 7

@pytest.mark.asyncio
async def test_end_to_end_report_generation(db_pool):
    """Test complete report generation workflow."""
    from agents.reporting import ReportingAgent
    
    agent = ReportingAgent(db_pool)
    
    report = await agent.generate_daily_report(report_date="2026-09-01")
    
    assert report["report_type"] == "daily"
    assert "metrics" in report
    assert "insights" in report
    assert "recommendations" in report
```

### 9.4 E2E Tests

```python
# tests/e2e/test_full_system.py
import pytest
import pytest_asyncio
import asyncio
import asyncpg
import aiohttp

@pytest.mark.asyncio
async def test_full_analytics_workflow():
    """
    E2E test: Complete analytics workflow from data collection to report.
    
    This test exercises the full system:
    1. Data collection from mock APIs
    2. Attribution analysis
    3. Predictive analytics
    4. Report generation
    """
    # Setup
    db_pool = await asyncpg.create_pool(
        host="localhost",
        database="marketing_analytics_test",
        user="test",
        password="test",
    )
    
    try:
        # 1. Collect data
        from agents.data_collector import DataCollectorAgent
        collector = DataCollectorAgent(db_pool)
        
        # Mock the actual API calls
        with patch.object(collector, '_fetch_google_ads') as mock_fetch:
            mock_fetch.return_value = pd.DataFrame({
                'date': ['2026-09-01', '2026-09-02'],
                'campaign': ['camp1', 'camp1'],
                'impressions': [10000, 12000],
                'clicks': [500, 600],
                'spend': [1000, 1200],
                'conversions': [50, 60],
                'revenue': [5000, 6000],
            })
            
            ad_data = await collector.fetch_ad_data(
                platform="google_ads",
                start_date="2026-09-01",
                end_date="2026-09-30",
            )
            assert len(ad_data) == 2
        
        # 2. Run attribution
        from agents.attribution_engine import AttributionEngineAgent
        attribution_agent = AttributionEngineAgent(db_pool)
        
        with patch.object(attribution_agent, '_fetch_journeys') as mock_journeys:
            mock_journeys.return_value = pd.DataFrame({
                'customer_id': ['c1', 'c1', 'c2', 'c2', 'c3'],
                'channel': ['google_ads', 'email', 'meta_ads', 'google_ads', 'direct'],
                'timestamp': pd.to_datetime(['2026-09-01', '2026-09-02', '2026-09-01', '2026-09-02', '2026-09-01']),
                'converted': [1, 1, 0, 0, 0],
            })
            
            attribution = await attribution_agent.run_markov_attribution(
                start_date="2026-09-01",
                end_date="2026-09-30",
            )
            assert "attribution" in attribution
        
        # 3. Generate forecast
        from agents.predictive_analytics import PredictiveAnalyticsAgent
        predictive = PredictiveAnalyticsAgent(db_pool)
        
        with patch.object(predictive, '_fetch_metric_data') as mock_metric:
            mock_metric.return_value = pd.DataFrame({
                'date': pd.date_range('2026-09-01', periods=30),
                'revenue': [1000 + i * 50 for i in range(30)],
            })
            
            forecast = await predictive.forecast_metrics(
                metric="revenue",
                start_date="2026-09-01",
                end_date="2026-09-30",
                forecast_horizon=7,
            )
            assert "forecast" in forecast
        
        # 4. Generate report
        from agents.reporting import ReportingAgent
        reporting = ReportingAgent(db_pool)
        
        with patch.object(reporting, '_fetch_daily_metrics') as mock_daily:
            mock_daily.return_value = {
                'total_spend': 2200,
                'total_revenue': 11000,
                'total_conversions': 110,
                'total_clicks': 1100,
                'total_impressions': 22000,
            }
            
            report = await reporting.generate_daily_report("2026-09-01")
            assert report["report_type"] == "daily"
            assert "metrics" in report
    
    finally:
        await db_pool.close()
```

### 9.5 Performance Tests

```python
# tests/performance/test_attribution_performance.py
import pytest
import time
import numpy as np
from attribution.markov_chain import MarkovChainAttribution

class TestAttributionPerformance:
    """Performance tests for attribution models."""
    
    def test_markov_performance_1000_journeys(self):
        """Test Markov model with 1000 journeys."""
        np.random.seed(42)
        channels = ['google_ads', 'meta_ads', 'email', 'direct', 'linkedin_ads']
        
        journeys = []
        conversions = []
        for _ in range(1000):
            length = np.random.randint(1, 6)
            journey = list(np.random.choice(channels, size=length, replace=True))
            journeys.append(journey)
            conversions.append(np.random.choice([0, 1], p=[0.7, 0.3]))
        
        start = time.time()
        mc = MarkovChainAttribution(order=1)
        mc.fit(journeys, conversions)
        elapsed = time.time() - start
        
        assert elapsed < 5.0, f"Markov fitting took {elapsed:.2f}s (should be < 5s)"
    
    def test_markov_performance_10000_journeys(self):
        """Test Markov model with 10000 journeys."""
        np.random.seed(42)
        channels = ['google_ads', 'meta_ads', 'email', 'direct', 'linkedin_ads']
        
        journeys = []
        conversions = []
        for _ in range(10000):
            length = np.random.randint(1, 8)
            journey = list(np.random.choice(channels, size=length, replace=True))
            journeys.append(journey)
            conversions.append(np.random.choice([0, 1], p=[0.7, 0.3]))
        
        start = time.time()
        mc = MarkovChainAttribution(order=1)
        mc.fit(journeys, conversions)
        elapsed = time.time() - start
        
        assert elapsed < 30.0, f"Markov fitting took {elapsed:.2f}s (should be < 30s)"
    
    def test_shapley_performance_10_channels(self):
        """Test Shapley calculation with 10 channels."""
        from attribution.shapley import ShapleyAttribution
        
        channels = [f'channel_{i}' for i in range(10)]
        
        def characteristic_function(subset):
            return len(subset) * 10
        
        start = time.time()
        shapley = ShapleyAttribution()
        shapley.fit(channels, characteristic_function)
        elapsed = time.time() - start
        
        assert elapsed < 60.0, f"Shapley calculation took {elapsed:.2f}s (should be < 60s)"
```

### 9.6 Test Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Slow running tests
```

```yaml
# .github/workflows/test.yml
name: Analytics CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: marketing_analytics_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run unit tests
        run: pytest tests/ -m "unit" --cov=agents --cov=attribution --cov-report=xml
      
      - name: Run integration tests
        run: pytest tests/integration -m "integration"
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/marketing_analytics_test
      
      - name: Run E2E tests
        run: pytest tests/e2e -m "e2e"
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/marketing_analytics_test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Appendix: Deployment Checklist

- [ ] Set up PostgreSQL database with schema
- [ ] Configure Redis for caching
- [ ] Set up Kafka for streaming
- [ ] Deploy agent services via Docker Compose
- [ ] Configure ad platform API credentials
- [ ] Set up CRM integrations
- [ ] Deploy dashboard frontend
- [ ] Configure Airflow DAGs
- [ ] Set up MLflow for model registry
- [ ] Configure monitoring and alerting
- [ ] Set up CI/CD pipeline
- [ ] Run full test suite
- [ ] Performance benchmark
- [ ] Security audit
- [ ] Documentation review</longcat_think>
