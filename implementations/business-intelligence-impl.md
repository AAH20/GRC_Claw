# AI-Powered Business Intelligence Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Author:** Ahmed Hassan  
**Date:** 2026-10-01  
**Status:** Draft

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Data Collection Agent Implementation](#2-data-collection-agent-implementation)
3. [Analysis Agent Implementation](#3-analysis-agent-implementation)
4. [Visualization Agent Implementation](#4-visualization-agent-implementation)
5. [Reporting Agent Implementation](#5-reporting-agent-implementation)
6. [Predictive Analytics Agent Implementation](#6-predictive-analytics-agent-implementation)
7. [Code Examples and Snippets](#7-code-examples-and-snippets)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Design

The AI-powered business intelligence system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. The architecture consists of five specialized agents coordinated by a central orchestrator that routes tasks, manages state, and synthesizes outputs.

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│  (Task routing, state management, result synthesis)         │
└──────────┬──────────┬──────────┬──────────┬─────────────────┘
           │          │          │          │
    ┌──────▼──┐ ┌─────▼────┐ ┌──▼──────┐ ┌─▼──────────┐
    │  Data   │ │ Analysis │ │  Viz    │ │  Reporting │
    │Collection│ │  Agent   │ │  Agent  │ │   Agent    │
    └────┬────┘ └────┬─────┘ └────┬────┘ └─────┬──────┘
         │           │            │             │
    ┌────▼───────────▼────────────▼─────────────▼────┐
    │              Predictive Analytics Agent          │
    └──────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents | Multi-agent orchestration |
| LLM Backend | OpenAI GPT-4o / Claude 3.5 Sonnet | Reasoning and generation |
| Data Connectors | LangChain Tools + Custom APIs | External data ingestion |
| Vector Store | ChromaDB / Pinecone | Semantic search over reports |
| Cache | Redis | Intermediate result caching |
| Message Queue | Celery + Redis | Async task distribution |
| Storage | PostgreSQL + S3 | Structured data + artifacts |
| Monitoring | LangSmith | Tracing and observability |

### 1.3 Agent Communication Protocol

Agents communicate via a **shared blackboard pattern** with typed messages:

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime
import uuid


class MessageType(Enum):
    TASK_REQUEST = "task_request"
    TASK_RESULT = "task_result"
    DATA_PAYLOAD = "data_payload"
    ANALYSIS_RESULT = "analysis_result"
    VISUALIZATION_SPEC = "visualization_spec"
    REPORT_DRAFT = "report_draft"
    PREDICTION_RESULT = "prediction_result"
    ERROR = "error"
    STATUS_UPDATE = "status_update"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = ""
    message_type: MessageType = MessageType.TASK_REQUEST
    payload: Any = None
    priority: Priority = Priority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }
```

### 1.4 Orchestrator Design

```python
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from typing import Callable
import json


class BusinessIntelligenceOrchestrator:
    """Central orchestrator that routes tasks to specialized agents."""

    AGENT_REGISTRY = {
        "data_collection": "DataCollectionAgent",
        "analysis": "AnalysisAgent",
        "visualization": "VisualizationAgent",
        "reporting": "ReportingAgent",
        "predictive": "PredictiveAnalyticsAgent",
    }

    def __init__(self, llm, tool_registry, state_store):
        self.llm = llm
        self.tool_registry = tool_registry
        self.state_store = state_store
        self.agents: dict[str, BaseAgent] = {}
        self._initialize_agents()

    def _initialize_agents(self):
        for agent_name, agent_class_name in self.AGENT_REGISTRY.items():
            self.agents[agent_name] = self._create_agent(agent_name)

    def _create_agent(self, agent_name: str) -> "BaseAgent":
        agent_classes = {
            "data_collection": DataCollectionAgent,
            "analysis": AnalysisAgent,
            "visualization": VisualizationAgent,
            "reporting": ReportingAgent,
            "predictive": PredictiveAnalyticsAgent,
        }
        return agent_classes[agent_name](
            llm=self.llm,
            tools=self.tool_registry.get_tools_for_agent(agent_name),
            state_store=self.state_store,
        )

    async def process_query(self, user_query: str, context: dict) -> dict:
        """Main entry point: parse query, route to agents, synthesize results."""
        # Step 1: Decompose the query into sub-tasks
        task_plan = await self._decompose_query(user_query, context)

        # Step 2: Execute tasks in dependency order
        results = {}
        for task in task_plan:
            agent_name = task["agent"]
            agent = self.agents[agent_name]
            result = await agent.execute(
                task=task,
                context=context,
                prior_results=results,
            )
            results[task["task_id"]] = result

        # Step 3: Synthesize final output
        final_output = await self._synthesize_results(user_query, results, context)
        return final_output

    async def _decompose_query(self, query: str, context: dict) -> list[dict]:
        """Use LLM to break complex queries into agent-specific tasks."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a task decomposition planner for a business intelligence system.
Break the user query into ordered sub-tasks for specialized agents.
Available agents: data_collection, analysis, visualization, reporting, predictive.
Return a JSON array of tasks with fields: task_id, agent, description, depends_on."""),
            ("human", "Query: {query}\nContext: {context}"),
        ])
        chain = prompt | self.llm | JsonOutputParser()
        response = await chain.ainvoke({"query": query, "context": json.dumps(context)})
        return response

    async def _synthesize_results(self, query: str, results: dict, context: dict) -> dict:
        """Combine agent outputs into a coherent final response."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a business intelligence synthesizer.
Combine the outputs from multiple specialized agents into a single, coherent response.
Highlight key insights, note any data limitations, and suggest next steps."""),
            ("human", "Original Query: {query}\nAgent Results: {results}"),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "query": query,
            "results": json.dumps(results, default=str),
        })
        return {
            "query": query,
            "response": response.content,
            "agent_results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }
```

### 1.5 State Management

```python
from typing import Protocol
import redis.asyncio as redis
import json


class StateStore(Protocol):
    async def get(self, key: str) -> Optional[dict]: ...
    async def set(self, key: str, value: dict, ttl: int = 3600) -> None: ...
    async def delete(self, key: str) -> None: ...


class RedisStateStore:
    """Redis-backed state store for inter-agent communication."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[dict]:
        data = await self.client.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        await self.client.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def publish(self, channel: str, message: AgentMessage) -> None:
        await self.client.publish(channel, json.dumps(message.to_dict(), default=str))
```

---

## 2. Data Collection Agent Implementation

### 2.1 Agent Overview

The Data Collection Agent is responsible for gathering business data from multiple sources: databases, APIs, web scraping, file uploads, and streaming sources. It normalizes, validates, and stores collected data for downstream agents.

### 2.2 Architecture

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool, BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import Any
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta


class DataSourceConfig(BaseModel):
    source_type: str  # "database", "api", "web", "file", "stream"
    connection_string: str
    credentials: dict = Field(default_factory=dict)
    query: Optional[str] = None
    schedule: Optional[str] = None  # cron expression
    schema: Optional[dict] = None


class DataCollectionAgent(BaseAgent):
    """Agent responsible for collecting data from diverse sources."""

    def __init__(self, llm, tools, state_store):
        super().__init__(llm, tools, state_store)
        self.collectors = {
            "database": DatabaseCollector(),
            "api": APICollector(),
            "web": WebCollector(),
            "file": FileCollector(),
            "stream": StreamCollector(),
        }
        self.validator = DataValidator()
        self.normalizer = DataNormalizer()

    async def execute(self, task: dict, context: dict, prior_results: dict) -> dict:
        """Execute data collection task."""
        source_configs = task.get("sources", [])
        collection_results = []

        for config_dict in source_configs:
            config = DataSourceConfig(**config_dict)
            collector = self.collectors.get(config.source_type)

            if not collector:
                collection_results.append({
                    "source": config.connection_string,
                    "status": "error",
                    "error": f"Unsupported source type: {config.source_type}",
                })
                continue

            try:
                # Collect raw data
                raw_data = await collector.collect(config)

                # Validate
                validation_result = self.validator.validate(raw_data, config.schema)
                if not validation_result.is_valid:
                    collection_results.append({
                        "source": config.connection_string,
                        "status": "validation_failed",
                        "errors": validation_result.errors,
                    })
                    continue

                # Normalize
                normalized_data = self.normalizer.normalize(raw_data, config.schema)

                # Store
                storage_key = await self._store_data(normalized_data, config)

                collection_results.append({
                    "source": config.connection_string,
                    "status": "success",
                    "records_collected": len(normalized_data),
                    "storage_key": storage_key,
                    "schema": normalized_data.columns.tolist() if hasattr(normalized_data, 'columns') else None,
                })

            except Exception as e:
                collection_results.append({
                    "source": config.connection_string,
                    "status": "error",
                    "error": str(e),
                })

        return {
            "agent": "data_collection",
            "task_id": task["task_id"],
            "results": collection_results,
            "total_records": sum(r.get("records_collected", 0) for r in collection_results),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _store_data(self, data, config: DataSourceConfig) -> str:
        """Store collected data and return a reference key."""
        storage_key = f"data/{config.source_type}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        await self.state_store.set(storage_key, {
            "data": data.to_dict(orient="records") if hasattr(data, 'to_dict') else data,
            "config": config.dict(),
            "collected_at": datetime.utcnow().isoformat(),
        }, ttl=86400 * 7)  # 7-day TTL
        return storage_key
```

### 2.3 Data Collectors

```python
class DatabaseCollector:
    """Collect data from SQL and NoSQL databases."""

    async def collect(self, config: DataSourceConfig) -> pd.DataFrame:
        if config.connection_string.startswith("postgresql"):
            return await self._collect_postgres(config)
        elif config.connection_string.startswith("mysql"):
            return await self._collect_mysql(config)
        elif config.connection_string.startswith("mongodb"):
            return await self._collect_mongodb(config)
        else:
            raise ValueError(f"Unsupported database: {config.connection_string}")

    async def _collect_postgres(self, config: DataSourceConfig) -> pd.DataFrame:
        import asyncpg
        conn = await asyncpg.connect(config.connection_string)
        try:
            query = config.query or "SELECT * FROM information_schema.tables"
            records = await conn.fetch(query)
            return pd.DataFrame([dict(r) for r in records])
        finally:
            await conn.close()

    async def _collect_mysql(self, config: DataSourceConfig) -> pd.DataFrame:
        import aiomysql
        conn = await aiomysql.connect(**config.credentials)
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(config.query)
                records = await cur.fetchall()
                return pd.DataFrame(records)
        finally:
            conn.close()

    async def _collect_mongodb(self, config: DataSourceConfig) -> pd.DataFrame:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(config.connection_string)
        db = client.get_default_database()
        collection = db[config.credentials.get("collection", "data")]
        cursor = collection.find(config.query or {})
        records = await cursor.to_list(length=10000)
        return pd.DataFrame(records)


class APICollector:
    """Collect data from REST and GraphQL APIs."""

    async def collect(self, config: DataSourceConfig) -> pd.DataFrame:
        async with aiohttp.ClientSession() as session:
            headers = config.credentials.get("headers", {})
            async with session.get(
                config.connection_string,
                headers=headers,
                params=config.credentials.get("params"),
            ) as response:
                response.raise_for_status()
                data = await response.json()

                # Handle paginated responses
                if isinstance(data, dict) and "results" in data:
                    all_records = data["results"]
                    while data.get("next"):
                        async with session.get(data["next"], headers=headers) as r:
                            r.raise_for_status()
                            data = await r.json()
                            all_records.extend(data["results"])
                    return pd.DataFrame(all_records)

                return pd.DataFrame(data if isinstance(data, list) else [data])


class WebCollector:
    """Collect data from web pages using LangChain tools."""

    async def collect(self, config: DataSourceConfig) -> pd.DataFrame:
        from langchain_community.tools import RunRequestURL
        scraper = RunRequestURL()
        result = scrapar.run(config.connection_string)
        # Parse HTML tables into DataFrame
        tables = pd.read_html(result)
        return tables[0] if tables else pd.DataFrame()


class FileCollector:
    """Collect data from uploaded files (CSV, Excel, JSON, Parquet)."""

    async def collect(self, config: DataSourceConfig) -> pd.DataFrame:
        file_path = config.connection_string
        if file_path.endswith(".csv"):
            return pd.read_csv(file_path)
        elif file_path.endswith((".xlsx", ".xls")):
            return pd.read_excel(file_path)
        elif file_path.endswith(".json"):
            return pd.read_json(file_path)
        elif file_path.endswith(".parquet"):
            return pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")


class StreamCollector:
    """Collect data from streaming sources (Kafka, WebSockets)."""

    async def collect(self, config: DataSourceConfig) -> pd.DataFrame:
        # Implementation for Kafka consumer
        from aiokafka import AIOKafkaConsumer
        import json

        consumer = AIOKafkaConsumer(
            config.credentials.get("topic", "default"),
            bootstrap_servers=config.connection_string,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await consumer.start()
        records = []
        try:
            async for msg in consumer:
                records.append(msg.value)
                if len(records) >= config.credentials.get("max_records", 1000):
                    break
        finally:
            await consumer.stop()
        return pd.DataFrame(records)
```

### 2.4 Data Validation and Normalization

```python
from pydantic import BaseModel, ValidationError
from typing import Optional
import great_expectations as gx


class ValidationResult:
    def __init__(self, is_valid: bool, errors: list, warnings: list):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings


class DataValidator:
    """Validate collected data against expected schemas."""

    def validate(self, data: pd.DataFrame, schema: Optional[dict]) -> ValidationResult:
        errors = []
        warnings = []

        if schema:
            # Check required columns
            required_cols = schema.get("required_columns", [])
            missing_cols = set(required_cols) - set(data.columns)
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")

            # Check data types
            type_mapping = schema.get("column_types", {})
            for col, expected_type in type_mapping.items():
                if col in data.columns:
                    actual_type = str(data[col].dtype)
                    if not self._type_matches(actual_type, expected_type):
                        warnings.append(
                            f"Column '{col}' expected {expected_type}, got {actual_type}"
                        )

            # Check for nulls in critical columns
            critical_cols = schema.get("critical_columns", [])
            for col in critical_cols:
                if col in data.columns and data[col].isnull().any():
                    errors.append(f"Critical column '{col}' contains null values")

            # Check row count
            min_rows = schema.get("min_rows", 1)
            if len(data) < min_rows:
                errors.append(f"Expected at least {min_rows} rows, got {len(data)}")

        # Generic quality checks
        if data.empty:
            errors.append("Data is empty")

        duplicate_ratio = data.duplicated().sum() / max(len(data), 1)
        if duplicate_ratio > 0.1:
            warnings.append(f"High duplicate ratio: {duplicate_ratio:.1%}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _type_matches(self, actual: str, expected: str) -> bool:
        type_map = {
            "int": ["int64", "int32", "Int64"],
            "float": ["float64", "float32"],
            "string": ["object", "string"],
            "datetime": ["datetime64[ns]", "datetime64"],
            "bool": ["bool"],
        }
        return actual in type_map.get(expected, [expected])


class DataNormalizer:
    """Normalize data into a consistent format."""

    def normalize(self, data: pd.DataFrame, schema: Optional[dict]) -> pd.DataFrame:
        df = data.copy()

        # Standardize column names
        df.columns = df.columns.str.lower().str.replace(r"\s+", "_", regex=True)

        # Apply schema-based transformations
        if schema:
            # Type conversions
            for col, target_type in schema.get("column_types", {}).items():
                if col in df.columns:
                    df[col] = self._convert_type(df[col], target_type)

            # Rename columns
            column_mapping = schema.get("column_mapping", {})
            df = df.rename(columns=column_mapping)

            # Sort columns
            preferred_order = schema.get("column_order", [])
            if preferred_order:
                ordered_cols = [c for c in preferred_order if c in df.columns]
                remaining_cols = [c for c in df.columns if c not in preferred_order]
                df = df[ordered_cols + remaining_cols]

        # Remove completely empty rows/columns
        df = df.dropna(how="all").dropna(axis=1, how="all")

        # Add metadata
        df.attrs["normalized_at"] = datetime.utcnow().isoformat()
        df.attrs["row_count"] = len(df)

        return df

    def _convert_type(self, series: pd.Series, target_type: str) -> pd.Series:
        converters = {
            "int": lambda s: pd.to_numeric(s, errors="coerce").astype("Int64"),
            "float": lambda s: pd.to_numeric(s, errors="coerce"),
            "string": lambda s: s.astype(str),
            "datetime": lambda s: pd.to_datetime(s, errors="coerce"),
            "bool": lambda s: s.map({"true": True, "false": False, "1": True, "0": False}),
        }
        converter = converters.get(target_type)
        return converter(series) if converter else series
```

---

## 3. Analysis Agent Implementation

### 3.1 Agent Overview

The Analysis Agent performs statistical analysis, trend detection, anomaly detection, and correlation analysis on collected data. It uses a combination of traditional statistical methods and LLM-powered reasoning.

### 3.2 Implementation

```python
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Literal


class AnalysisAgent(BaseAgent):
    """Agent responsible for statistical and exploratory data analysis."""

    def __init__(self, llm, tools, state_store):
        super().__init__(llm, tools, state_store)
        self.analyzers = {
            "descriptive": DescriptiveAnalyzer(),
            "trend": TrendAnalyzer(),
            "anomaly": AnomalyAnalyzer(),
            "correlation": CorrelationAnalyzer(),
            "segmentation": SegmentationAnalyzer(),
            "forecast": ForecastAnalyzer(),
        }

    async def execute(self, task: dict, context: dict, prior_results: dict) -> dict:
        """Execute analysis task on collected data."""
        # Retrieve data from prior collection results
        data = await self._resolve_data(task, prior_results)
        if data is None or data.empty:
            return {
                "agent": "analysis",
                "task_id": task["task_id"],
                "status": "error",
                "error": "No data available for analysis",
            }

        analysis_type = task.get("analysis_type", "descriptive")
        parameters = task.get("parameters", {})

        analyzer = self.analyzers.get(analysis_type)
        if not analyzer:
            return {
                "agent": "analysis",
                "task_id": task["task_id"],
                "status": "error",
                "error": f"Unknown analysis type: {analysis_type}",
            }

        try:
            result = await analyzer.analyze(data, parameters)

            # Use LLM to generate narrative insights
            narrative = await self._generate_narrative(data, result, analysis_type)

            return {
                "agent": "analysis",
                "task_id": task["task_id"],
                "status": "success",
                "analysis_type": analysis_type,
                "results": result,
                "narrative": narrative,
                "data_summary": {
                    "rows": len(data),
                    "columns": len(data.columns),
                    "column_names": data.columns.tolist(),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "agent": "analysis",
                "task_id": task["task_id"],
                "status": "error",
                "error": str(e),
            }

    async def _resolve_data(self, task: dict, prior_results: dict) -> Optional[pd.DataFrame]:
        """Resolve data references from prior agent results."""
        data_ref = task.get("data_reference")
        if not data_ref:
            # Try to find data in prior results
            for result in prior_results.values():
                if isinstance(result, dict) and result.get("agent") == "data_collection":
                    for r in result.get("results", []):
                        if r.get("status") == "success":
                            data_ref = r.get("storage_key")
                            break

        if data_ref:
            stored = await self.state_store.get(data_ref)
            if stored and "data" in stored:
                return pd.DataFrame(stored["data"])

        return None

    async def _generate_narrative(self, data: pd.DataFrame, result: dict, analysis_type: str) -> str:
        """Use LLM to generate human-readable insights from analysis results."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a business intelligence analyst.
Generate clear, actionable insights from the analysis results.
Focus on business implications, not technical details.
Highlight anomalies, trends, and recommendations."""),
            ("human", """Analysis Type: {analysis_type}
Data Shape: {shape}
Analysis Results: {results}

Provide a concise narrative summary of the key findings."""),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "analysis_type": analysis_type,
            "shape": f"{data.shape[0]} rows x {data.shape[1]} columns",
            "results": json.dumps(result, default=str),
        })
        return response.content
```

### 3.3 Analyzers

```python
class DescriptiveAnalyzer:
    """Compute descriptive statistics."""

    async def analyze(self, data: pd.DataFrame, params: dict) -> dict:
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        categorical_cols = data.select_dtypes(include=["object", "category"]).columns

        result = {
            "numeric_summary": {},
            "categorical_summary": {},
            "missing_values": data.isnull().sum().to_dict(),
            "memory_usage_mb": data.memory_usage(deep=True).sum() / 1e6,
        }

        if len(numeric_cols) > 0:
            desc = data[numeric_cols].describe()
            result["numeric_summary"] = desc.to_dict()

            # Additional statistics
            for col in numeric_cols:
                result["numeric_summary"][col]["skewness"] = float(data[col].skew())
                result["numeric_summary"][col]["kurtosis"] = float(data[col].kurtosis())

        if len(categorical_cols) > 0:
            for col in categorical_cols:
                result["categorical_summary"][col] = {
                    "unique_count": int(data[col].nunique()),
                    "top_values": data[col].value_counts().head(10).to_dict(),
                    "mode": data[col].mode().iloc[0] if not data[col].mode().empty else None,
                }

        return result


class TrendAnalyzer:
    """Detect trends in time-series data."""

    async def analyze(self, data: pd.DataFrame, params: dict) -> dict:
        date_col = params.get("date_column")
        value_col = params.get("value_column")

        if not date_col or not value_col:
            # Auto-detect date column
            date_candidates = data.select_dtypes(include=["datetime64"]).columns
            if len(date_candidates) > 0:
                date_col = date_candidates[0]
            numeric_candidates = data.select_dtypes(include=[np.number]).columns
            if len(numeric_candidates) > 0:
                value_col = numeric_candidates[0]

        if not date_col or not value_col:
            return {"error": "Could not detect date/value columns for trend analysis"}

        df = data.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)

        # Linear trend
        x = np.arange(len(df))
        y = df[value_col].values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # Moving averages
        df["ma_7"] = df[value_col].rolling(window=min(7, len(df))).mean()
        df["ma_30"] = df[value_col].rolling(window=min(30, len(df))).mean()

        # Trend direction
        recent = df[value_col].tail(min(30, len(df) // 3))
        early = df[value_col].head(min(30, len(df) // 3))
        trend_direction = "increasing" if recent.mean() > early.mean() else "decreasing"

        # Seasonality detection (simple)
        if len(df) >= 14:
            autocorr = df[value_col].autocorr(lag=min(7, len(df) // 4))
        else:
            autocorr = None

        return {
            "date_column": date_col,
            "value_column": value_col,
            "trend_slope": float(slope),
            "trend_r_squared": float(r_value ** 2),
            "trend_p_value": float(p_value),
            "trend_direction": trend_direction,
            "recent_mean": float(recent.mean()),
            "early_mean": float(early.mean()),
            "percent_change": float((recent.mean() - early.mean()) / early.mean() * 100) if early.mean() != 0 else None,
            "seasonality_autocorr": float(autocorr) if autocorr else None,
            "moving_average_7": df["ma_7"].dropna().tolist(),
            "moving_average_30": df["ma_30"].dropna().tolist(),
        }


class AnomalyAnalyzer:
    """Detect anomalies using Isolation Forest and statistical methods."""

    async def analyze(self, data: pd.DataFrame, params: dict) -> dict:
        contamination = params.get("contamination", 0.05)
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_cols:
            return {"error": "No numeric columns for anomaly detection"}

        df = data[numeric_cols].dropna()
        scaler = StandardScaler()
        scaled = scaler.fit_transform(df)

        # Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        predictions = iso_forest.fit_predict(scaled)
        anomaly_scores = iso_forest.score_samples(scaled)

        # Statistical outliers (Z-score)
        z_scores = np.abs(stats.zscore(df))
        statistical_outliers = (z_scores > 3).any(axis=1)

        anomaly_indices = np.where(predictions == -1)[0]
        outlier_rows = df.iloc[anomaly_indices]

        return {
            "total_records": len(df),
            "anomalies_detected": int(len(anomaly_indices)),
            "anomaly_rate": float(len(anomaly_indices) / len(df)),
            "anomaly_indices": anomaly_indices.tolist(),
            "anomaly_scores": anomaly_scores[anomaly_indices].tolist(),
            "statistical_outliers_count": int(statistical_outliers.sum()),
            "anomaly_summary": outlier_rows.describe().to_dict() if len(outlier_rows) > 0 else {},
            "columns_analyzed": numeric_cols,
        }


class CorrelationAnalyzer:
    """Analyze correlations between variables."""

    async def analyze(self, data: pd.DataFrame, params: dict) -> dict:
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        method = params.get("method", "pearson")

        if len(numeric_cols) < 2:
            return {"error": "Need at least 2 numeric columns for correlation analysis"}

        corr_matrix = data[numeric_cols].corr(method=method)

        # Find strongest correlations
        pairs = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                pairs.append({
                    "var1": numeric_cols[i],
                    "var2": numeric_cols[j],
                    "correlation": float(corr_matrix.iloc[i, j]),
                })

        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "method": method,
            "correlation_matrix": corr_matrix.to_dict(),
            "strongest_correlations": pairs[:10],
            "highly_correlated_pairs": [p for p in pairs if abs(p["correlation"]) > 0.8],
        }


class SegmentationAnalyzer:
        """Customer/record segmentation using clustering."""

    async def analyze(self, data: pd.DataFrame, params: dict) -> dict:
        from sklearn.cluster import KMeans

        n_clusters = params.get("n_clusters", 4)
        feature_cols = params.get("feature_columns", data.select_dtypes(include=[np.number]).columns.tolist())

        df = data[feature_cols].dropna()
        scaler = StandardScaler()
        scaled = scaler.fit_transform(df)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(scaled)

        df["cluster"] = labels
        cluster_summary = df.groupby("cluster").agg(["mean", "std", "count"]).to_dict()

        return {
            "n_clusters": n_clusters,
            "cluster_sizes": pd.Series(labels).value_counts().to_dict(),
            "cluster_centers": kmeans.cluster_centers_.tolist(),
            "inertia": float(kmeans.inertia_),
            "cluster_summary": cluster_summary,
            "feature_columns": feature_cols,
        }


class ForecastAnalyzer:
    """Simple forecasting using exponential smoothing."""

    async def analyze(self, data: pd.DataFrame, params: dict) -> dict:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        value_col = params.get("value_column")
        date_col = params.get("date_column")
        periods = params.get("forecast_periods", 30)

        if not value_col:
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            value_col = numeric_cols[0] if len(numeric_cols) > 0 else None

        if not value_col:
            return {"error": "No value column for forecasting"}

        series = data[value_col].dropna()

        if len(series) < 10:
            return {"error": "Need at least 10 data points for forecasting"}

        try:
            model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal="add" if len(series) >= 20 else None,
                seasonal_periods=min(12, len(series) // 2) if len(series) >= 20 else None,
            )
            fitted = model.fit()
            forecast = fitted.forecast(periods)

            return {
                "value_column": value_col,
                "forecast_periods": periods,
                "forecast_values": forecast.tolist(),
                "forecast_mean": float(forecast.mean()),
                "aic": float(fitted.aic),
                "bic": float(fitted.bic),
                "model_params": {
                    "smoothing_level": float(fitted.params.get("smoothing_level", 0)),
                    "smoothing_trend": float(fitted.params.get("smoothing_trend", 0)),
                },
            }
        except Exception as e:
            return {"error": f"Forecasting failed: {str(e)}"}
```

---

## 4. Visualization Agent Implementation

### 4.1 Agent Overview

The Visualization Agent transforms analysis results into interactive charts, dashboards, and visual specifications. It uses a combination of programmatic charting libraries and LLM-guided design decisions.

### 4.2 Implementation

```python
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json


class VisualizationAgent(BaseAgent):
    """Agent responsible for creating visualizations from analysis results."""

    def __init__(self, llm, tools, state_store):
        super().__init__(llm, tools, state_store)
        self.chart_factory = ChartFactory()
        self.dashboard_builder = DashboardBuilder()

    async def execute(self, task: dict, context: dict, prior_results: dict) -> dict:
        """Execute visualization task."""
        viz_type = task.get("visualization_type", "auto")
        data = await self._resolve_data(task, prior_results)
        analysis_results = self._find_analysis_results(prior_results)

        if viz_type == "auto":
            viz_type = await self._recommend_visualization(data, analysis_results, task)

        try:
            if viz_type == "dashboard":
                result = await self._build_dashboard(data, analysis_results, task)
            elif viz_type == "chart":
                result = await self._create_chart(data, analysis_results, task)
            elif viz_type == "table":
                result = await self._create_table(data, task)
            else:
                result = await self._create_chart(data, analysis_results, task)

            return {
                "agent": "visualization",
                "task_id": task["task_id"],
                "status": "success",
                "visualization_type": viz_type,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "agent": "visualization",
                "task_id": task["task_id"],
                "status": "error",
                "error": str(e),
            }

    async def _recommend_visualization(
        self, data: Optional[pd.DataFrame], analysis_results: dict, task: dict
    ) -> str:
        """Use LLM to recommend the best visualization type."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data visualization expert.
Recommend the best visualization type based on the data and analysis context.
Options: line_chart, bar_chart, scatter_plot, heatmap, pie_chart, histogram, box_plot, dashboard, table.
Return only the visualization type name."""),
            ("human", """Data shape: {shape}
Columns: {columns}
Analysis type: {analysis_type}
User request: {request}

What visualization type is most appropriate?"""),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "shape": f"{data.shape}" if data is not None else "No data",
            "columns": data.columns.tolist() if data is not None else [],
            "analysis_type": analysis_results.get("analysis_type", "unknown") if analysis_results else "unknown",
            "request": task.get("description", ""),
        })
        return response.content.strip().lower().replace(" ", "_")

    async def _create_chart(
        self, data: pd.DataFrame, analysis_results: dict, task: dict
    ) -> dict:
        """Create a single chart based on task specifications."""
        chart_type = task.get("chart_type", "line")
        x_col = task.get("x_column")
        y_col = task.get("y_column")
        color_col = task.get("color_column")
        title = task.get("title", "Business Intelligence Chart")

        # Auto-detect columns if not specified
        if not x_col:
            date_cols = data.select_dtypes(include=["datetime64"]).columns
            x_col = date_cols[0] if len(date_cols) > 0 else data.columns[0]
        if not y_col:
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            y_col = numeric_cols[0] if len(numeric_cols) > 0 else data.columns[1]

        chart = self.chart_factory.create(
            chart_type=chart_type,
            data=data,
            x=x_col,
            y=y_col,
            color=color_col,
            title=title,
        )

        return {
            "chart_type": chart_type,
            "spec": chart.to_json(),
            "html": chart.to_html(full_html=False, include_plotlyjs="cdn"),
            "interactive": True,
        }

    async def _build_dashboard(
        self, data: pd.DataFrame, analysis_results: dict, task: dict
    ) -> dict:
        """Build a multi-chart dashboard."""
        charts = []

        # KPI cards
        kpis = self._extract_kpis(data, analysis_results)
        charts.append({"type": "kpi_cards", "data": kpis})

        # Main trend chart
        if data is not None and len(data) > 0:
            date_cols = data.select_dtypes(include=["datetime64"]).columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns

            if len(date_cols) > 0 and len(numeric_cols) > 0:
                trend_chart = px.line(
                    data, x=date_cols[0], y=numeric_cols[0],
                    title=f"{numeric_cols[0]} Over Time",
                )
                charts.append({"type": "chart", "spec": trend_chart.to_json()})

            # Distribution chart
            if len(numeric_cols) > 0:
                dist_chart = px.histogram(
                    data, x=numeric_cols[0],
                    title=f"Distribution of {numeric_cols[0]}",
                )
                charts.append({"type": "chart", "spec": dist_chart.to_json()})

            # Correlation heatmap
            if len(numeric_cols) > 1:
                corr = data[numeric_cols].corr()
                heatmap = px.imshow(
                    corr, text_auto=True,
                    title="Correlation Matrix",
                    color_continuous_scale="RdBu",
                )
                charts.append({"type": "chart", "spec": heatmap.to_json()})

        # Analysis result visualizations
        if analysis_results:
            if "anomalies_detected" in str(analysis_results):
                anomaly_chart = self._create_anomaly_chart(data, analysis_results)
                if anomaly_chart:
                    charts.append({"type": "chart", "spec": anomaly_chart.to_json()})

        return {
            "type": "dashboard",
            "charts": charts,
            "layout": "grid",
            "title": task.get("title", "Business Intelligence Dashboard"),
        }

    def _extract_kpis(self, data: Optional[pd.DataFrame], analysis_results: dict) -> list:
        """Extract key performance indicators."""
        kpis = []
        if data is None:
            return kpis

        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols[:5]:
            kpis.append({
                "label": col.replace("_", " ").title(),
                "value": f"{data[col].sum():,.2f}" if data[col].sum() > 1000 else f"{data[col].mean():.2f}",
                "trend": "up" if data[col].iloc[-1] > data[col].iloc[0] else "down" if len(data) > 1 else "flat",
            })

        return kpis

    def _create_anomaly_chart(self, data: pd.DataFrame, analysis_results: dict) -> Optional[go.Figure]:
        """Create a chart highlighting anomalies."""
        if not analysis_results or "anomaly_indices" not in analysis_results:
            return None

        anomaly_indices = analysis_results["anomaly_indices"]
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return None

        value_col = numeric_cols[0]
        fig = go.Figure()

        # Normal points
        normal_mask = ~data.index.isin(anomaly_indices)
        fig.add_trace(go.Scatter(
            x=data.index[normal_mask],
            y=data[value_col][normal_mask],
            mode="markers",
            name="Normal",
            marker=dict(color="blue", size=6),
        ))

        # Anomaly points
        if len(anomaly_indices) > 0:
            fig.add_trace(go.Scatter(
                x=data.index[anomaly_indices],
                y=data[value_col].iloc[anomaly_indices],
                mode="markers",
                name="Anomaly",
                marker=dict(color="red", size=10, symbol="x"),
            ))

        fig.update_layout(title=f"Anomaly Detection: {value_col}")
        return fig

    async def _create_table(self, data: pd.DataFrame, task: dict) -> dict:
        """Create an interactive data table."""
        page_size = task.get("page_size", 25)
        columns = task.get("columns", data.columns.tolist())

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=columns,
                fill_color="paleturquoise",
                align="left",
            ),
            cells=dict(
                values=[data[col].tolist() for col in columns],
                fill_color="lavender",
                align="left",
            ),
        )])

        fig.update_layout(title=task.get("title", "Data Table"))

        return {
            "type": "table",
            "spec": fig.to_json(),
            "row_count": len(data),
            "columns": columns,
        }
```

### 4.3 Chart Factory

```python
class ChartFactory:
    """Factory for creating various chart types."""

    def create(
        self,
        chart_type: str,
        data: pd.DataFrame,
        x: str,
        y: str,
        color: Optional[str] = None,
        title: str = "",
        **kwargs,
    ) -> go.Figure:
        creators = {
            "line": self._create_line_chart,
            "bar": self._create_bar_chart,
            "scatter": self._create_scatter_plot,
            "pie": self._create_pie_chart,
            "histogram": self._create_histogram,
            "box": self._create_box_plot,
            "heatmap": self._create_heatmap,
            "area": self._create_area_chart,
        }

        creator = creators.get(chart_type, self._create_line_chart)
        return creator(data, x, y, color, title, **kwargs)

    def _create_line_chart(self, data, x, y, color, title, **kwargs):
        if color:
            fig = px.line(data, x=x, y=y, color=color, title=title, markers=True)
        else:
            fig = px.line(data, x=x, y=y, title=title, markers=True)
        fig.update_layout(hovermode="x unified")
        return fig

    def _create_bar_chart(self, data, x, y, color, title, **kwargs):
        orientation = kwargs.get("orientation", "v")
        if orientation == "h":
            fig = px.bar(data, x=y, y=x, color=color, title=title, orientation="h")
        else:
            fig = px.bar(data, x=x, y=y, color=color, title=title)
        return fig

    def _create_scatter_plot(self, data, x, y, color, title, **kwargs):
        size_col = kwargs.get("size")
        fig = px.scatter(data, x=x, y=y, color=color, size=size_col, title=title, trendline="ols")
        return fig

    def _create_pie_chart(self, data, x, y, color, title, **kwargs):
        fig = px.pie(data, names=x, values=y, title=title)
        return fig

    def _create_histogram(self, data, x, y, color, title, **kwargs):
        nbins = kwargs.get("nbins", 30)
        fig = px.histogram(data, x=x, color=color, nbins=nbins, title=title, marginal="box")
        return fig

    def _create_box_plot(self, data, x, y, color, title, **kwargs):
        fig = px.box(data, x=x, y=y, color=color, title=title)
        return fig

    def _create_heatmap(self, data, x, y, color, title, **kwargs):
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        corr = data[numeric_cols].corr()
        fig = px.imshow(corr, text_auto=True, title=title, color_continuous_scale="RdBu", aspect="auto")
        return fig

    def _create_area_chart(self, data, x, y, color, title, **kwargs):
        fig = px.area(data, x=x, y=y, color=color, title=title)
        return fig
```

---

## 5. Reporting Agent Implementation

### 5.1 Agent Overview

The Reporting Agent generates comprehensive business intelligence reports by synthesizing outputs from all other agents. It produces structured documents in multiple formats (Markdown, PDF, HTML) with executive summaries, detailed findings, and recommendations.

### 5.2 Implementation

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS
import markdown
from pathlib import Path


class ReportingAgent(BaseAgent):
    """Agent responsible for generating comprehensive BI reports."""

    def __init__(self, llm, tools, state_store):
        super().__init__(llm, tools, state_store)
        self.template_env = Environment(
            loader=FileSystemLoader("templates/reports"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.report_types = {
            "executive_summary": self._generate_executive_summary,
            "detailed_analysis": self._generate_detailed_report,
            "operational_dashboard": self._generate_operational_report,
            "strategic_insights": self._generate_strategic_report,
        }

    async def execute(self, task: dict, context: dict, prior_results: dict) -> dict:
        """Execute reporting task."""
        report_type = task.get("report_type", "executive_summary")
        output_format = task.get("output_format", "markdown")
        title = task.get("title", "Business Intelligence Report")

        generator = self.report_types.get(report_type, self._generate_executive_summary)

        try:
            report_content = await generator(
                task=task,
                context=context,
                prior_results=prior_results,
                title=title,
            )

            # Format output
            if output_format == "html":
                formatted = self._to_html(report_content)
            elif output_format == "pdf":
                formatted = await self._to_pdf(report_content)
            else:
                formatted = report_content  # Markdown

            # Store report
            report_key = f"report/{report_type}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            await self.state_store.set(report_key, {
                "content": report_content,
                "formatted": formatted if isinstance(formatted, str) else "PDF_BINARY",
                "type": report_type,
                "format": output_format,
                "title": title,
            }, ttl=86400 * 30)  # 30-day TTL

            return {
                "agent": "reporting",
                "task_id": task["task_id"],
                "status": "success",
                "report_type": report_type,
                "output_format": output_format,
                "title": title,
                "content": report_content,
                "report_key": report_key,
                "word_count": len(report_content.split()),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "agent": "reporting",
                "task_id": task["task_id"],
                "status": "error",
                "error": str(e),
            }

    async def _generate_executive_summary(
        self, task: dict, context: dict, prior_results: dict, title: str
    ) -> str:
        """Generate an executive summary report."""
        # Gather all agent outputs
        data_summary = self._summarize_data_collection(prior_results)
        analysis_summary = self._summarize_analysis(prior_results)
        viz_summary = self._summarize_visualizations(prior_results)
        prediction_summary = self._summarize_predictions(prior_results)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior business intelligence consultant writing an executive summary.
Create a concise, actionable report for C-level executives.
Structure: Executive Summary, Key Findings, Recommendations, Next Steps.
Use clear, non-technical language. Focus on business impact."""),
            ("human", """Report Title: {title}
Original Query: {query}

Data Collection Summary:
{data_summary}

Analysis Summary:
{analysis_summary}

Visualization Summary:
{viz_summary}

Prediction Summary:
{prediction_summary}

Generate the executive summary report in Markdown."""),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "title": title,
            "query": context.get("original_query", ""),
            "data_summary": data_summary,
            "analysis_summary": analysis_summary,
            "viz_summary": viz_summary,
            "prediction_summary": prediction_summary,
        })
        return response.content

    async def _generate_detailed_report(
        self, task: dict, context: dict, prior_results: dict, title: str
    ) -> str:
        """Generate a detailed analytical report."""
        sections = []

        # Title and metadata
        sections.append(f"# {title}\n")
        sections.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
        sections.append(f"**Query:** {context.get('original_query', 'N/A')}\n")
        sections.append("---\n")

        # Data Collection Section
        data_result = self._find_agent_result(prior_results, "data_collection")
        if data_result:
            sections.append("## Data Collection\n")
            sections.append(f"- **Total Records:** {data_result.get('total_records', 'N/A')}\n")
            for r in data_result.get("results", []):
                status_icon = "✅" if r.get("status") == "success" else "❌"
                sections.append(f"- {status_icon} {r.get('source', 'Unknown')}: {r.get('records_collected', 0)} records\n")
            sections.append("\n")

        # Analysis Section
        analysis_result = self._find_agent_result(prior_results, "analysis")
        if analysis_result:
            sections.append("## Analysis Results\n")
            sections.append(f"**Analysis Type:** {analysis_result.get('analysis_type', 'N/A')}\n")
            if analysis_result.get("narrative"):
                sections.append(f"\n{analysis_result['narrative']}\n")
            sections.append("\n")

        # Visualization Section
        viz_result = self._find_agent_result(prior_results, "visualization")
        if viz_result:
            sections.append("## Visualizations\n")
            sections.append(f"**Type:** {viz_result.get('visualization_type', 'N/A')}\n")
            sections.append(f"See attached dashboard/chart artifacts.\n\n")

        # Prediction Section
        pred_result = self._find_agent_result(prior_results, "predictive")
        if pred_result:
            sections.append("## Predictions\n")
            if pred_result.get("narrative"):
                sections.append(f"\n{pred_result['narrative']}\n")
            sections.append("\n")

        # Recommendations
        sections.append("## Recommendations\n")
        recs = await self._generate_recommendations(prior_results)
        for i, rec in enumerate(recs, 1):
            sections.append(f"{i}. {rec}\n")

        return "\n".join(sections)

    async def _generate_operational_report(
        self, task: dict, context: dict, prior_results: dict, title: str
    ) -> str:
        """Generate an operational dashboard-style report."""
        # Similar to detailed but focused on operational metrics
        return await self._generate_detailed_report(task, context, prior_results, title)

    async def _generate_strategic_report(
        self, task: dict, context: dict, prior_results: dict, title: str
    ) -> str:
        """Generate a strategic insights report."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a strategic business analyst.
Generate a strategic insights report focusing on long-term trends, competitive implications,
and strategic recommendations. Use frameworks like SWOT, Porter's Five Forces where relevant."""),
            ("human", "Title: {title}\nContext: {context}\nResults: {results}"),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "title": title,
            "context": context.get("original_query", ""),
            "results": json.dumps(prior_results, default=str),
        })
        return response.content

    def _summarize_data_collection(self, prior_results: dict) -> str:
        result = self._find_agent_result(prior_results, "data_collection")
        if not result:
            return "No data collection performed."
        return f"Collected {result.get('total_records', 0)} records from {len(result.get('results', []))} sources."

    def _summarize_analysis(self, prior_results: dict) -> str:
        result = self._find_agent_result(prior_results, "analysis")
        if not result:
            return "No analysis performed."
        return result.get("narrative", "Analysis completed.")

    def _summarize_visualizations(self, prior_results: dict) -> str:
        result = self._find_agent_result(prior_results, "visualization")
        if not result:
            return "No visualizations created."
        return f"Created {result.get('visualization_type', 'unknown')} visualization."

    def _summarize_predictions(self, prior_results: dict) -> str:
        result = self._find_agent_result(prior_results, "predictive")
        if not result:
            return "No predictions generated."
        return result.get("narrative", "Prediction completed.")

    def _find_agent_result(self, prior_results: dict, agent_name: str) -> Optional[dict]:
        for result in prior_results.values():
            if isinstance(result, dict) and result.get("agent") == agent_name:
                return result
        return None

    async def _generate_recommendations(self, prior_results: dict) -> list[str]:
        """Generate actionable recommendations based on all results."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Generate 3-5 actionable business recommendations based on the analysis results. Return as a numbered list."),
            ("human", "Results: {results}"),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({"results": json.dumps(prior_results, default=str)})
        # Parse numbered list
        lines = response.content.strip().split("\n")
        return [l.lstrip("0123456789. ").strip() for l in lines if l.strip()]

    def _to_html(self, markdown_content: str) -> str:
        """Convert Markdown to styled HTML."""
        html_body = markdown.markdown(markdown_content, extensions=["tables", "fenced_code"])
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>BI Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; line-height: 1.6; }}
h1 {{ color: #1a1a2e; border-bottom: 2px solid #16213e; padding-bottom: 0.5rem; }}
h2 {{ color: #16213e; margin-top: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background-color: #16213e; color: white; }}
</style></head><body>{html_body}</body></html>"""

    async def _to_pdf(self, markdown_content: str) -> bytes:
        """Convert Markdown to PDF."""
        html_content = self._to_html(markdown_content)
        pdf = HTML(string=html_content).write_pdf()
        return pdf
```

---

## 6. Predictive Analytics Agent Implementation

### 6.1 Agent Overview

The Predictive Analytics Agent builds and applies machine learning models for forecasting, classification, and recommendation tasks. It automates model selection, training, evaluation, and interpretation.

### 6.2 Implementation

```python
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix,
)
import joblib
import io
import base64


class PredictiveAnalyticsAgent(BaseAgent):
    """Agent responsible for building and applying predictive models."""

    def __init__(self, llm, tools, state_store):
        super().__init__(llm, tools, state_store)
        self.model_registry = ModelRegistry()
        self.feature_engineer = FeatureEngineer()

    async def execute(self, task: dict, context: dict, prior_results: dict) -> dict:
        """Execute predictive analytics task."""
        prediction_type = task.get("prediction_type", "forecast")
        data = await self._resolve_data(task, prior_results)

        if data is None or data.empty:
            return {
                "agent": "predictive",
                "task_id": task["task_id"],
                "status": "error",
                "error": "No data available for prediction",
            }

        target_col = task.get("target_column")
        feature_cols = task.get("feature_columns")
        test_size = task.get("test_size", 0.2)

        try:
            # Feature engineering
            X, y, feature_names = self.feature_engineer.prepare_features(
                data, target_col, feature_cols
            )

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            # Model selection and training
            if prediction_type in ["forecast", "regression"]:
                model, metrics = await self._train_regressor(X_train, X_test, y_train, y_test)
            elif prediction_type == "classification":
                model, metrics = await self._train_classifier(X_train, X_test, y_train, y_test)
            else:
                model, metrics = await self._train_regressor(X_train, X_test, y_train, y_test)

            # Feature importance
            importance = self._get_feature_importance(model, feature_names)

            # Generate predictions
            predictions = model.predict(X_test)

            # LLM interpretation
            narrative = await self._interpret_results(
                prediction_type, metrics, importance, feature_names
            )

            # Store model
            model_key = await self._store_model(model, metrics, feature_names)

            return {
                "agent": "predictive",
                "task_id": task["task_id"],
                "status": "success",
                "prediction_type": prediction_type,
                "model_type": type(model).__name__,
                "metrics": metrics,
                "feature_importance": importance,
                "predictions_sample": predictions[:20].tolist(),
                "narrative": narrative,
                "model_key": model_key,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "agent": "predictive",
                "task_id": task["task_id"],
                "status": "error",
                "error": str(e),
            }

    async def _train_regressor(
        self, X_train, X_test, y_train, y_test
    ) -> tuple:
        """Train and evaluate regression models, return best."""
        models = {
            "linear": LinearRegression(),
            "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
            "gradient_boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
        }

        best_model = None
        best_score = float("-inf")
        best_metrics = {}

        for name, model in models.items():
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)

            metrics = {
                "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
                "mae": float(mean_absolute_error(y_test, predictions)),
                "r2": float(r2_score(y_test, predictions)),
            }

            if metrics["r2"] > best_score:
                best_score = metrics["r2"]
                best_model = model
                best_metrics = metrics
                best_metrics["model_name"] = name

        return best_model, best_metrics

    async def _train_classifier(
        self, X_train, X_test, y_train, y_test
    ) -> tuple:
        """Train and evaluate classification models."""
        models = {
            "logistic": LogisticRegression(max_iter=1000, random_state=42),
            "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
        }

        best_model = None
        best_score = float("-inf")
        best_metrics = {}

        for name, model in models.items():
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)

            metrics = {
                "accuracy": float(accuracy_score(y_test, predictions)),
                "precision": float(precision_score(y_test, predictions, average="weighted")),
                "recall": float(recall_score(y_test, predictions, average="weighted")),
                "f1": float(f1_score(y_test, predictions, average="weighted")),
            }

            if metrics["f1"] > best_score:
                best_score = metrics["f1"]
                best_model = model
                best_metrics = metrics
                best_metrics["model_name"] = name

        return best_model, best_metrics

    def _get_feature_importance(self, model, feature_names: list) -> dict:
        """Extract feature importance from model."""
        if hasattr(model, "feature_importances_"):
            importance = model.feature_importances_
        elif hasattr(model, "coef_"):
            importance = np.abs(model.coef_)
            if importance.ndim > 1:
                importance = importance.mean(axis=0)
        else:
            return {}

        return dict(sorted(
            zip(feature_names, importance.tolist()),
            key=lambda x: x[1],
            reverse=True,
        ))

    async def _interpret_results(
        self, prediction_type: str, metrics: dict, importance: dict, feature_names: list
    ) -> str:
        """Use LLM to interpret model results."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data science interpreter.
Explain the predictive model results in business terms.
Focus on: model performance, key drivers, limitations, and actionable insights."""),
            ("human", """Prediction Type: {prediction_type}
Model: {model_name}
Metrics: {metrics}
Top Features: {importance}

Provide a business-friendly interpretation."""),
        ])
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "prediction_type": prediction_type,
            "model_name": metrics.get("model_name", "unknown"),
            "metrics": json.dumps(metrics),
            "importance": json.dumps(dict(list(importance.items())[:5])),
        })
        return response.content

    async def _store_model(self, model, metrics: dict, feature_names: list) -> str:
        """Serialize and store the trained model."""
        model_buffer = io.BytesIO()
        joblib.dump(model, model_buffer)
        model_b64 = base64.b64encode(model_buffer.getvalue()).decode()

        model_key = f"model/{type(model).__name__}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        await self.state_store.set(model_key, {
            "model_b64": model_b64,
            "metrics": metrics,
            "feature_names": feature_names,
            "created_at": datetime.utcnow().isoformat(),
        }, ttl=86400 * 90)  # 90-day TTL
        return model_key
```

### 6.3 Feature Engineering

```python
class FeatureEngineer:
    """Automated feature engineering for predictive models."""

    def prepare_features(
        self,
        data: pd.DataFrame,
        target_col: Optional[str],
        feature_cols: Optional[list],
    ) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Prepare feature matrix and target vector."""
        df = data.copy()

        # Auto-detect target if not specified
        if not target_col:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            target_col = numeric_cols[-1] if len(numeric_cols) > 0 else None

        if not target_col:
            raise ValueError("No target column specified or detected")

        # Select features
        if feature_cols:
            X = df[feature_cols].copy()
        else:
            X = df.drop(columns=[target_col]).copy()

        # Handle categorical features
        categorical_cols = X.select_dtypes(include=["object", "category"]).columns
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)

        # Handle datetime features
        datetime_cols = X.select_dtypes(include=["datetime64"]).columns
        for col in datetime_cols:
            X[f"{col}_year"] = X[col].dt.year
            X[f"{col}_month"] = X[col].dt.month
            X[f"{col}_day"] = X[col].dt.day
            X[f"{col}_dayofweek"] = X[col].dt.dayofweek
            X = X.drop(columns=[col])

        # Handle missing values
        X = X.fillna(X.median())

        y = df[target_col].values
        feature_names = X.columns.tolist()

        return X.values, y, feature_names


class ModelRegistry:
    """Registry for tracking trained models."""

    def __init__(self):
        self.models: dict[str, dict] = {}

    def register(self, model_id: str, model_info: dict):
        self.models[model_id] = {
            **model_info,
            "registered_at": datetime.utcnow().isoformat(),
        }

    def get_best_model(self, metric: str = "r2") -> Optional[str]:
        if not self.models:
            return None
        return max(self.models.items(), key=lambda x: x[1].get("metrics", {}).get(metric, 0))[0]
```

---

## 7. Code Examples and Snippets

### 7.1 Complete Pipeline Example

```python
import asyncio
from langchain_openai import ChatOpenAI


async def run_bi_pipeline():
    """Complete example of running the BI pipeline."""
    # Initialize
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    state_store = RedisStateStore()
    tool_registry = ToolRegistry()

    orchestrator = BusinessIntelligenceOrchestrator(
        llm=llm,
        tool_registry=tool_registry,
        state_store=state_store,
    )

    # Example query
    user_query = """
    Analyze our sales data from the last quarter. 
    Identify trends, detect anomalies, and create a forecast for next month.
    Generate an executive summary report with visualizations.
    """

    context = {
        "user_id": "user_123",
        "department": "sales",
        "data_sources": [
            {
                "source_type": "database",
                "connection_string": "postgresql://user:pass@localhost:5432/sales_db",
                "query": "SELECT * FROM sales WHERE sale_date >= NOW() - INTERVAL '3 months'",
                "schema": {
                    "required_columns": ["sale_date", "amount", "product_id", "region"],
                    "column_types": {"sale_date": "datetime", "amount": "float"},
                    "critical_columns": ["sale_date", "amount"],
                },
            }
        ],
    }

    # Execute pipeline
    result = await orchestrator.process_query(user_query, context)
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    asyncio.run(run_bi_pipeline())
```

### 7.2 Tool Registration

```python
from langchain_core.tools import tool


class ToolRegistry:
    """Central registry for agent tools."""

    def __init__(self):
        self._tools: dict[str, list] = {
            "data_collection": [],
            "analysis": [],
            "visualization": [],
            "reporting": [],
            "predictive": [],
        }
        self._register_default_tools()

    def _register_default_tools(self):
        @tool
        def query_database(connection_string: str, query: str) -> str:
            """Execute a SQL query and return results as JSON."""
            import pandas as pd
            from sqlalchemy import create_engine
            engine = create_engine(connection_string)
            df = pd.read_sql(query, engine)
            return df.to_json(orient="records")

        @tool
        def fetch_api_data(url: str, headers: dict = None) -> str:
            """Fetch data from a REST API endpoint."""
            import requests
            response = requests.get(url, headers=headers or {})
            return response.text

        @tool
        def read_file(file_path: str) -> str:
            """Read and parse a data file (CSV, Excel, JSON)."""
            import pandas as pd
            if file_path.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file_path.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_json(file_path)
            return df.to_json(orient="records")

        @tool
        def compute_statistics(data_json: str, columns: list = None) -> str:
            """Compute descriptive statistics on data."""
            import pandas as pd
            df = pd.read_json(data_json)
            if columns:
                df = df[columns]
            return df.describe().to_json()

        @tool
        def detect_anomalies(data_json: str, column: str, threshold: float = 3.0) -> str:
            """Detect anomalies using Z-score method."""
            import pandas as pd
            import numpy as np
            df = pd.read_json(data_json)
            z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
            anomalies = df[z_scores > threshold]
            return anomalies.to_json(orient="records")

        self._tools["data_collection"] = [query_database, fetch_api_data, read_file]
        self._tools["analysis"] = [compute_statistics, detect_anomalies]

    def get_tools_for_agent(self, agent_name: str) -> list:
        return self._tools.get(agent_name, [])
```

### 7.3 FastAPI Service Wrapper

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid


app = FastAPI(title="BI Agent API", version="1.0.0")


class BIQueryRequest(BaseModel):
    query: str
    context: dict = {}
    data_sources: list[dict] = []
    output_format: str = "markdown"


class BIQueryResponse(BaseModel):
    request_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


# Global orchestrator instance
orchestrator: Optional[BusinessIntelligenceOrchestrator] = None


@app.on_event("startup")
async def startup():
    global orchestrator
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    state_store = RedisStateStore()
    tool_registry = ToolRegistry()
    orchestrator = BusinessIntelligenceOrchestrator(llm, tool_registry, state_store)


@app.post("/api/v1/query", response_model=BIQueryResponse)
async def submit_query(request: BIQueryRequest, background_tasks: BackgroundTasks):
    request_id = str(uuid.uuid4())
    try:
        context = {**request.context, "data_sources": request.data_sources}
        result = await orchestrator.process_query(request.query, context)
        return BIQueryResponse(request_id=request_id, status="success", result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "agents": list(orchestrator.AGENT_REGISTRY.keys()) if orchestrator else []}
```

### 7.4 Configuration File

```yaml
# config/bi_config.yaml
agents:
  orchestrator:
    model: gpt-4o
    temperature: 0
    max_tokens: 4096
    timeout: 300

  data_collection:
    max_records_per_source: 100000
    retry_attempts: 3
    retry_delay: 5
    supported_sources:
      - postgresql
      - mysql
      - mongodb
      - rest_api
      - graphql
      - csv
      - excel
      - parquet
      - kafka

  analysis:
    default_analysis_type: descriptive
    anomaly_contamination: 0.05
    correlation_threshold: 0.8
    max_categories: 50

  visualization:
    default_chart_type: line
    color_palette: "plotly"
    interactive: true
    export_formats:
      - html
      - png
      - svg
      - pdf

  reporting:
    default_format: markdown
    template_dir: "templates/reports"
    max_report_length: 50000
    supported_formats:
      - markdown
      - html
      - pdf

  predictive:
    default_model: auto
    test_size: 0.2
    cv_folds: 5
    hyperparameter_tuning: true
    max_training_time: 300

infrastructure:
  redis:
    host: localhost
    port: 6379
    db: 0

  postgresql:
    host: localhost
    port: 5432
    database: bi_platform

  monitoring:
    langsmith:
      enabled: true
      project: bi-agents
    prometheus:
      enabled: true
      port: 9090
```

---

## 8. Testing Strategy

### 8.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5 tests)
                   ─┤ Tests   ├─
                  ┌─┴─────────┴─┐
                  │  Integration │  (20 tests)
                 ─┤    Tests     ├─
                ┌─┴──────────────┴─┐
                │    Unit Tests     │  (100+ tests)
               ─┤  (per agent)      ├─
              ┌─┴──────────────────┴─┐
              │   Component Tests     │  (50 tests)
              └───────────────────────┘
```

### 8.2 Unit Tests

```python
# tests/test_data_collection_agent.py
import pytest
import pandas as pd
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=100),
        "sales": [100 + i * 2 + (i % 7) * 10 for i in range(100)],
        "region": ["North", "South", "East", "West"] * 25,
        "product": ["A", "B", "C"] * 33 + ["A"],
    })


@pytest.fixture
def mock_state_store():
    store = AsyncMock()
    store.get.return_value = None
    return store


@pytest.mark.asyncio
async def test_data_collection_agent_success(sample_data, mock_state_store):
    from implementations.business_intelligence_impl import DataCollectionAgent

    llm = MagicMock()
    agent = DataCollectionAgent(llm, [], mock_state_store)

    task = {
        "task_id": "test_001",
        "sources": [
            {
                "source_type": "file",
                "connection_string": "/tmp/test_data.csv",
            }
        ],
    }

    # Mock the file collector
    agent.collectors["file"] = AsyncMock()
    agent.collectors["file"].collect.return_value = sample_data

    result = await agent.execute(task, {}, {})

    assert result["status"] == "success"
    assert result["total_records"] == 100
    assert len(result["results"]) == 1


@pytest.mark.asyncio
async def test_data_collection_agent_validation_failure(mock_state_store):
    from implementations.business_intelligence_impl import DataCollectionAgent

    llm = MagicMock()
    agent = DataCollectionAgent(llm, [], mock_state_store)

    task = {
        "task_id": "test_002",
        "sources": [
            {
                "source_type": "file",
                "connection_string": "/tmp/bad_data.csv",
                "schema": {
                    "required_columns": ["nonexistent_column"],
                },
            }
        ],
    }

    bad_data = pd.DataFrame({"a": [1, 2, 3]})
    agent.collectors["file"] = AsyncMock()
    agent.collectors["file"].collect.return_value = bad_data

    result = await agent.execute(task, {}, {})

    assert result["results"][0]["status"] == "validation_failed"


@pytest.mark.asyncio
async def test_trend_analyzer_detects_upward_trend():
    from implementations.business_intelligence_impl import TrendAnalyzer

    data = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=60),
        "value": list(range(60, 120)),  # Clear upward trend
    })

    analyzer = TrendAnalyzer()
    result = await analyzer.analyze(data, {"date_column": "date", "value_column": "value"})

    assert result["trend_direction"] == "increasing"
    assert result["trend_slope"] > 0
    assert result["trend_r_squared"] > 0.9


@pytest.mark.asyncio
async def test_anomaly_detector_finds_outliers():
    from implementations.business_intelligence_impl import AnomalyAnalyzer

    # Normal data with a few outliers
    values = list(range(100))
    values[50] = 1000  # Clear outlier
    values[75] = -500  # Clear outlier

    data = pd.DataFrame({"value": values})
    analyzer = AnomalyAnalyzer()
    result = await analyzer.analyze(data, {"contamination": 0.05})

    assert result["anomalies_detected"] >= 2
    assert 50 in result["anomaly_indices"]
    assert 75 in result["anomaly_indices"]


@pytest.mark.asyncio
async def test_correlation_analyzer():
    from implementations.business_intelligence_impl import CorrelationAnalyzer

    data = pd.DataFrame({
        "a": [1, 2, 3, 4, 5],
        "b": [2, 4, 6, 8, 10],  # Perfect correlation with a
        "c": [5, 3, 1, 4, 2],   # No correlation
    })

    analyzer = CorrelationAnalyzer()
    result = await analyzer.analyze(data, {"method": "pearson"})

    # Find the a-b pair
    ab_pair = next(p for p in result["strongest_correlations"] if {p["var1"], p["var2"]} == {"a", "b"})
    assert abs(ab_pair["correlation"]) > 0.99
```

### 8.3 Integration Tests

```python
# tests/integration/test_pipeline.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_full_pipeline_execution():
    """Test the complete BI pipeline from query to report."""
    from implementations.business_intelligence_impl import BusinessIntelligenceOrchestrator

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="Test response")

    state_store = AsyncMock()
    tool_registry = MagicMock()
    tool_registry.get_tools_for_agent.return_value = []

    orchestrator = BusinessIntelligenceOrchestrator(llm, tool_registry, state_store)

    # Mock agent executions
    async def mock_execute(task, context, prior_results):
        return {
            "agent": task["agent"],
            "task_id": task["task_id"],
            "status": "success",
            "results": [{"source": "test", "records_collected": 100}],
        }

    for agent in orchestrator.agents.values():
        agent.execute = mock_execute

    result = await orchestrator.process_query(
        "Analyze sales data",
        {"user_id": "test"},
    )

    assert "response" in result
    assert "agent_results" in result


@pytest.mark.asyncio
async def test_agent_communication_via_state_store():
    """Test that agents can share data through the state store."""
    from implementations.business_intelligence_impl import RedisStateStore, AgentMessage, MessageType

    store = AsyncMock(spec=RedisStateStore)

    # Simulate data collection storing results
    await store.set("data/sales/20240101", {
        "data": [{"date": "2024-01-01", "sales": 1000}],
    })

    # Simulate analysis agent retrieving data
    stored = await store.get("data/sales/20240101")
    assert stored is not None
    assert stored["data"][0]["sales"] == 1000
```

### 8.4 End-to-End Tests

```python
# tests/e2e/test_bi_e2e.py
import pytest
import asyncio
import aiohttp


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_end_to_end_sales_analysis():
    """Full E2E test: query → data collection → analysis → visualization → report."""
    async with aiohttp.ClientSession() as session:
        # Submit query
        async with session.post("http://localhost:8000/api/v1/query", json={
            "query": "What were our top-selling products last month?",
            "context": {"department": "sales"},
            "data_sources": [{
                "source_type": "database",
                "connection_string": "postgresql://test:test@localhost:5432/test_db",
                "query": "SELECT * FROM sales WHERE sale_date >= DATE_TRUNC('month', NOW() - INTERVAL '1 month')",
            }],
        }) as resp:
            assert resp.status == 200
            result = await resp.json()
            assert result["status"] == "success"
            assert "agent_results" in result


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_health_endpoint():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/api/v1/health") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "healthy"
            assert len(data["agents"]) == 5
```

### 8.5 Performance Tests

```python
# tests/performance/test_performance.py
import pytest
import time
import asyncio


@pytest.mark.performance
@pytest.mark.asyncio
async def test_data_collection_performance():
    """Ensure data collection completes within SLA."""
    from implementations.business_intelligence_impl import DataCollectionAgent

    llm = MagicMock()
    agent = DataCollectionAgent(llm, [], AsyncMock())

    task = {
        "task_id": "perf_001",
        "sources": [{"source_type": "file", "connection_string": "/tmp/large_data.csv"}],
    }

    start = time.time()
    result = await agent.execute(task, {}, {})
    elapsed = time.time() - start

    assert elapsed < 30, f"Data collection took {elapsed:.1f}s, exceeding 30s SLA"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_agent_execution():
    """Test that multiple agents can run concurrently."""
    from implementations.business_intelligence_impl import BusinessIntelligenceOrchestrator

    llm = MagicMock()
    orchestrator = BusinessIntelligenceOrchestrator(llm, MagicMock(), AsyncMock())

    async def slow_execute(task, context, prior_results):
        await asyncio.sleep(0.5)
        return {"agent": task["agent"], "status": "success"}

    for agent in orchestrator.agents.values():
        agent.execute = slow_execute

    start = time.time()
    result = await orchestrator.process_query("test", {})
    elapsed = time.time() - start

    # Should complete in ~1s (orchestrator + slowest agent), not 2.5s (sequential)
    assert elapsed < 2.0, f"Concurrent execution took {elapsed:.1f}s"
```

### 8.6 Test Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    e2e: End-to-end tests (deselect with '-m "not e2e"')
    performance: Performance tests (deselect with '-m "not performance"')
    integration: Integration tests
    unit: Unit tests
addopts = -v --tb=short --strict-markers
```

```yaml
# .github/workflows/test.yml
name: BI Agent Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports: ["6379:6379"]
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run unit tests
        run: pytest -m "unit" --cov=implementations --cov-report=xml

      - name: Run integration tests
        run: pytest -m "integration" --cov-append

      - name: Run performance tests
        run: pytest -m "performance" --cov-append

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Appendix A: Deployment Architecture

```
                    ┌──────────────┐
                    │   Load       │
                    │  Balancer    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
        │  FastAPI  │ │ FastAPI│ │ FastAPI  │
        │  Worker 1 │ │Worker 2│ │ Worker 3 │
        └─────┬─────┘ └───┬────┘ └────┬─────┘
              │            │            │
        ┌─────▼────────────▼────────────▼─────┐
        │           Redis Cluster              │
        │   (State Store + Message Queue)     │
        └─────────────────┬──────────────────┘
                          │
        ┌─────────────────▼──────────────────┐
        │         PostgreSQL Cluster          │
        │   (Structured Data + Metadata)     │
        └────────────────────────────────────┘
```

## Appendix B: Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=bi-agents

REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost:5432/bi_platform

LOG_LEVEL=INFO
MAX_AGENT_ITERATIONS=20
DEFAULT_TIMEOUT=300
```

---

*End of Implementation Plan*
