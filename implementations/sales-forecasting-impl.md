# AI-Powered Sales Forecasting Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Status:** Draft  
**Framework:** LangChain DeepAgents + Python 3.11+

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Data Collection Agent Implementation](#2-data-collection-agent-implementation)
3. [Analysis Agent Implementation](#3-analysis-agent-implementation)
4. [Prediction Agent Implementation](#4-prediction-agent-implementation)
5. [Action Agent Implementation](#5-action-agent-implementation)
6. [Performance Analytics Agent Implementation](#6-performance-analytics-agent-implementation)
7. [Code Examples and Snippets](#7-code-examples-and-snippets)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The AI-powered sales forecasting system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. Five specialized agents collaborate in a pipeline architecture, each responsible for a distinct phase of the forecasting workflow:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Sales Forecasting Agent System                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Data       │───▶│  Analysis    │───▶│  Prediction  │          │
│  │  Collection  │    │    Agent     │    │    Agent     │          │
│  │    Agent     │    │              │    │              │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│         │                   │                   │                    │
│         ▼                   ▼                   ▼                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Action     │◀───│  Performance │◀───│  Prediction  │          │
│  │    Agent     │    │  Analytics   │    │    Output    │          │
│  │              │    │    Agent     │    │              │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Orchestrator / Coordinator Agent                 │  │
│  │         (LangChain DeepAgents Task Tool + Router)             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Agent Roles and Responsibilities

| Agent | Role | Input | Output | Tools |
|-------|------|-------|--------|-------|
| **Data Collection Agent** | Gathers raw sales data from multiple sources | Date range, product filters, region | Structured dataset (DataFrame/dict) | SQL queries, API calls, file readers |
| **Analysis Agent** | Performs EDA, trend detection, seasonality analysis | Cleaned dataset | Statistical summary, trend report, anomaly flags | Pandas, NumPy, SciPy, statistical tests |
| **Prediction Agent** | Generates forecasts using ML/statistical models | Analyzed data + historical patterns | Forecast values with confidence intervals | Prophet, ARIMA, scikit-learn, XGBoost |
| **Action Agent** | Translates forecasts into actionable recommendations | Forecast output + business rules | Action items, alerts, inventory suggestions | Rule engine, notification APIs |
| **Performance Analytics Agent** | Monitors forecast accuracy and system health | Predictions vs. actuals | Accuracy metrics, drift reports, model retrain triggers | MLflow, custom metrics dashboards |

### 1.3 Orchestration Pattern

The system uses **LangChain DeepAgents** with a **sequential pipeline + conditional branching** pattern:

- **Sequential flow**: Data Collection → Analysis → Prediction → Action
- **Feedback loop**: Performance Analytics feeds back into Prediction (model retraining) and Analysis (feature engineering improvements)
- **Conditional branching**: The orchestrator routes tasks based on data quality scores, forecast confidence levels, and business rules
- **Parallel execution**: Data Collection agents can run in parallel for different data sources (CRM, ERP, web analytics, external market data)

### 1.4 Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents | >= 0.1.0 |
| Language | Python | >= 3.11 |
| Data Processing | Pandas, NumPy, Polars | >= 2.0 |
| ML/Forecasting | Prophet, statsmodels, scikit-learn, XGBoost | Latest stable |
| Vector Store | FAISS / ChromaDB (for RAG on historical patterns) | >= 1.7 |
| Orchestration | LangGraph (state machine) | >= 0.2 |
| Monitoring | MLflow, LangSmith | >= 2.0 |
| API Layer | FastAPI | >= 0.100 |
| Task Queue | Celery + Redis | >= 5.0 |
| Database | PostgreSQL (structured), ClickHouse (time-series) | Latest |
| Caching | Redis | >= 7.0 |
| Deployment | Docker, Kubernetes | Latest |

### 1.5 Communication Protocol

Agents communicate via **structured message passing** using LangChain's `AgentState` and `Task` abstractions:

```python
# Message schema for inter-agent communication
class AgentMessage(BaseModel):
    agent_id: str
    message_type: Literal["task", "result", "error", "status"]
    payload: dict
    metadata: dict
    timestamp: datetime
    correlation_id: str  # For tracing across the pipeline
```

### 1.6 State Management

The system maintains a **shared state** across the pipeline using LangGraph's `StateGraph`:

```python
class SalesForecastingState(TypedDict):
    # Data collection outputs
    raw_data: dict[str, Any]
    data_quality_score: float
    collection_errors: list[str]
    
    # Analysis outputs
    eda_report: dict[str, Any]
    trend_analysis: dict[str, Any]
    seasonality: dict[str, Any]
    anomalies: list[dict]
    
    # Prediction outputs
    forecast_values: list[dict]
    confidence_intervals: dict[str, list[float]]
    model_metadata: dict[str, Any]
    
    # Action outputs
    recommendations: list[dict]
    alerts: list[dict]
    
    # Performance outputs
    accuracy_metrics: dict[str, float]
    drift_detected: bool
    retrain_recommended: bool
```

---

## 2. Data Collection Agent Implementation

### 2.1 Purpose

The Data Collection Agent is responsible for gathering, validating, and consolidating sales data from multiple internal and external sources into a unified, clean dataset ready for analysis.

### 2.2 Data Sources

| Source | Type | Frequency | Priority |
|--------|------|-----------|----------|
| CRM (Salesforce/HubSpot) | Internal | Real-time | High |
| ERP (SAP/Oracle) | Internal | Hourly | High |
| E-commerce Platform (Shopify/WooCommerce) | Internal | Real-time | High |
| Web Analytics (Google Analytics) | Internal | Daily | Medium |
| Social Media APIs | External | Daily | Medium |
| Economic Indicators (World Bank, FRED) | External | Weekly | Medium |
| Competitor Pricing (scraped) | External | Daily | Low |
| Weather Data (OpenWeatherMap) | External | Daily | Low |
| Google Trends | External | Weekly | Low |

### 2.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Any
import pandas as pd
from datetime import datetime, timedelta


# ─── Data Models ───────────────────────────────────────────────────

class DataSourceConfig(BaseModel):
    """Configuration for a single data source."""
    source_id: str
    source_type: Literal["crm", "erp", "ecommerce", "web_analytics", 
                          "social_media", "economic", "weather", "competitor"]
    connection_string: str
    credentials: dict[str, str]
    query_template: str
    refresh_interval_minutes: int = 60
    priority: int = 1  # 1 = highest


class CollectedData(BaseModel):
    """Standardized output from data collection."""
    dataset: dict[str, Any]  # Serialized DataFrame
    schema: dict[str, str]
    row_count: int
    column_count: int
    date_range: tuple[str, str]
    quality_score: float  # 0.0 to 1.0
    missing_value_pct: dict[str, float]
    source_metadata: dict[str, Any]
    collection_timestamp: str
    errors: list[str] = []


# ─── Tools ─────────────────────────────────────────────────────────

@tool
def query_crm_data(
    start_date: str,
    end_date: str,
    fields: list[str] = ["opportunity_id", "amount", "stage", "close_date", "account_id"]
) -> dict:
    """
    Query CRM system (Salesforce/HubSpot) for sales opportunities and activities.
    
    Args:
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        fields: List of CRM fields to retrieve
    
    Returns:
        Dictionary containing the query results and metadata
    """
    # Implementation would use simple-salesforce or hubspot-api-client
    from simple_salesforce import Salesforce
    
    sf = Salesforce(
        username="user@company.com",
        password="password",
        security_token="token"
    )
    
    field_str = ", ".join(fields)
    query = f"""
        SELECT {field_str}
        FROM Opportunity
        WHERE CloseDate >= {start_date}
        AND CloseDate <= {end_date}
    """
    
    results = sf.query_all(query)
    return {
        "records": results["records"],
        "total_size": results["totalSize"],
        "source": "crm"
    }


@tool
def query_erp_data(
    start_date: str,
    end_date: str,
    modules: list[str] = ["orders", "invoices", "inventory"]
) -> dict:
    """
    Query ERP system for order, invoice, and inventory data.
    
    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format
        modules: ERP modules to query
    
    Returns:
        Dictionary containing ERP data from requested modules
    """
    # Implementation would use SAP RFC or Oracle REST APIs
    results = {}
    for module in modules:
        # Placeholder for actual ERP integration
        results[module] = _query_erp_module(module, start_date, end_date)
    return {"data": results, "source": "erp"}


@tool
def query_ecommerce_data(
    start_date: str,
    end_date: str,
    metrics: list[str] = ["revenue", "orders", "aov", "conversion_rate"]
) -> dict:
    """
    Query e-commerce platform for transaction and funnel data.
    
    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format
        metrics: E-commerce metrics to retrieve
    
    Returns:
        Dictionary containing e-commerce metrics
    """
    # Implementation would use Shopify API or WooCommerce REST API
    return {
        "metrics": metrics,
        "date_range": (start_date, end_date),
        "source": "ecommerce"
    }


@tool
def query_web_analytics(
    start_date: str,
    end_date: str,
    dimensions: list[str] = ["date", "channel", "campaign"],
    metrics: list[str] = ["sessions", "users", "conversions", "revenue"]
) -> dict:
    """
    Query Google Analytics for web traffic and conversion data.
    
    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format
        dimensions: GA dimensions to break down by
        metrics: GA metrics to retrieve
    
    Returns:
        Dictionary containing analytics data
    """
    # Implementation would use Google Analytics Data API (GA4)
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    
    client = BetaAnalyticsDataClient()
    # Build and execute GA4 report request
    return {
        "dimensions": dimensions,
        "metrics": metrics,
        "source": "web_analytics"
    }


@tool
def query_external_market_data(
    indicators: list[str],
    start_date: str,
    end_date: str
) -> dict:
    """
    Query external economic and market indicators.
    
    Args:
        indicators: List of economic indicator codes (e.g., GDP, CPI, unemployment)
        start_date: Start date in ISO format
        end_date: End date in ISO format
    
    Returns:
        Dictionary containing external market data
    """
    # Implementation would use FRED API, World Bank API
    return {
        "indicators": indicators,
        "date_range": (start_date, end_date),
        "source": "external"
    }


@tool
def validate_data_quality(dataset: dict) -> dict:
    """
    Assess data quality across multiple dimensions: completeness, 
    consistency, accuracy, timeliness, and uniqueness.
    
    Args:
        dataset: The collected dataset to validate
    
    Returns:
        Quality assessment report with scores and issues
    """
    df = pd.DataFrame(dataset.get("data", []))
    
    report = {
        "completeness_score": 0.0,
        "consistency_score": 0.0,
        "accuracy_score": 0.0,
        "timeliness_score": 0.0,
        "uniqueness_score": 0.0,
        "overall_score": 0.0,
        "issues": []
    }
    
    # Completeness: check for missing values
    if not df.empty:
        missing_pct = df.isnull().mean()
        report["completeness_score"] = 1.0 - missing_pct.mean()
        
        # Flag columns with >20% missing
        high_missing = missing_pct[missing_pct > 0.2]
        for col, pct in high_missing.items():
            report["issues"].append({
                "type": "completeness",
                "column": col,
                "severity": "high" if pct > 0.5 else "medium",
                "details": f"{pct:.1%} missing values"
            })
        
        # Consistency: check data types and ranges
        # Accuracy: cross-reference with known totals
        # Timeliness: check data freshness
        # Uniqueness: check for duplicate records
        duplicate_count = df.duplicated().sum()
        report["uniqueness_score"] = 1.0 - (duplicate_count / len(df)) if len(df) > 0 else 0.0
        
        # Overall score (weighted average)
        report["overall_score"] = (
            report["completeness_score"] * 0.35 +
            report["consistency_score"] * 0.25 +
            report["accuracy_score"] * 0.20 +
            report["timeliness_score"] * 0.10 +
            report["uniqueness_score"] * 0.10
        )
    
    return report


@tool
def merge_datasets(datasets: list[dict], join_keys: list[str]) -> dict:
    """
    Merge multiple datasets into a single unified dataset.
    
    Args:
        datasets: List of dataset dictionaries to merge
        join_keys: Columns to use as join keys
    
    Returns:
        Merged dataset with conflict resolution metadata
    """
    if not datasets:
        return {"data": [], "merge_metadata": {}}
    
    merged_df = pd.DataFrame(datasets[0].get("data", []))
    merge_log = []
    
    for i, ds in enumerate(datasets[1:], start=1):
        df = pd.DataFrame(ds.get("data", []))
        try:
            merged_df = pd.merge(
                merged_df, df, 
                on=join_keys, 
                how="outer",
                suffixes=("", f"_ds{i}")
            )
            merge_log.append({
                "dataset_index": i,
                "rows_before": len(merged_df) - len(df),
                "rows_after": len(merged_df),
                "join_keys": join_keys,
                "status": "success"
            })
        except Exception as e:
            merge_log.append({
                "dataset_index": i,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "data": merged_df.to_dict(orient="records"),
        "merge_metadata": {
            "total_rows": len(merged_df),
            "total_columns": len(merged_df.columns),
            "merge_log": merge_log
        }
    }


# ─── Agent Definition ──────────────────────────────────────────────

DATA_COLLECTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Data Collection Agent for the sales forecasting system.
    
Your responsibilities:
1. Identify and query all relevant data sources for the requested time period
2. Validate data quality across completeness, consistency, accuracy, and timeliness
3. Merge data from multiple sources into a unified dataset
4. Flag any data quality issues that could impact forecasting accuracy
5. Return a structured CollectedData object

Guidelines:
- Always query the minimum necessary data to avoid over-fetching
- Prioritize high-priority sources (CRM, ERP) over low-priority (competitor, weather)
- If a source fails, continue with remaining sources and report the error
- Validate quality BEFORE returning data to the analysis phase
- Use correlation IDs to track data lineage

Time period: {time_period}
Product filters: {product_filters}
Region filters: {region_filters}
"""),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    ("human", "Collect sales data for the specified period and return a validated, merged dataset."),
])


def create_data_collection_agent(
    llm: ChatOpenAI | None = None,
    data_sources: list[DataSourceConfig] | None = None
) -> AgentExecutor:
    """
    Factory function to create the Data Collection Agent.
    
    Args:
        llm: Language model instance (defaults to GPT-4)
        data_sources: List of data source configurations
    
    Returns:
        Configured AgentExecutor for data collection
    """
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [
        query_crm_data,
        query_erp_data,
        query_ecommerce_data,
        query_web_analytics,
        query_external_market_data,
        validate_data_quality,
        merge_datasets,
    ]
    
    agent = create_openai_functions_agent(llm, tools, DATA_COLLECTION_PROMPT)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=15,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )
```

### 2.4 Data Pipeline Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Identify   │────▶│  Query Each  │────▶│   Validate   │────▶│    Merge     │
│   Sources   │     │   Source     │     │    Quality   │     │   Datasets   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                           │                    │                     │
                           ▼                    ▼                     ▼
                    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
                    │  Parallel    │     │  Score &     │     │  Unified     │
                    │  Execution   │     │  Flag Issues │     │  Dataset     │
                    └──────────────┘     └──────────────┘     └──────────────┘
```

### 2.5 Error Handling

```python
class DataCollectionError(Exception):
    """Base exception for data collection failures."""
    pass

class SourceConnectionError(DataCollectionError):
    """Raised when a data source is unreachable."""
    def __init__(self, source_id: str, original_error: Exception):
        self.source_id = source_id
        self.original_error = original_error
        super().__init__(f"Failed to connect to {source_id}: {original_error}")

class DataQualityError(DataCollectionError):
    """Raised when data quality falls below acceptable threshold."""
    def __init__(self, quality_score: float, threshold: float, issues: list):
        self.quality_score = quality_score
        self.threshold = threshold
        self.issues = issues
        super().__init__(
            f"Data quality score {quality_score:.2f} below threshold {threshold:.2f}"
        )
```

---

## 3. Analysis Agent Implementation

### 3.1 Purpose

The Analysis Agent performs comprehensive exploratory data analysis (EDA), identifies trends, detects seasonality, finds anomalies, and generates statistical summaries that inform the prediction agent.

### 3.2 Analysis Capabilities

| Analysis Type | Methods | Output |
|---------------|---------|--------|
| **Descriptive Statistics** | Mean, median, std, percentiles, skewness, kurtosis | Statistical summary table |
| **Trend Analysis** | Linear regression, Mann-Kendall test, moving averages | Trend direction, strength, significance |
| **Seasonality Detection** | FFT, autocorrelation (ACF/PACF), seasonal decomposition | Seasonal periods, strength |
| **Anomaly Detection** | Isolation Forest, Z-score, IQR method | Anomaly flags with severity |
| **Correlation Analysis** | Pearson, Spearman, mutual information | Correlation matrix, feature importance |
| **Segmentation** | K-means, RFM analysis | Customer/product segments |
| **Cohort Analysis** | Retention curves, LTV by cohort | Cohort performance metrics |

### 3.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import Any
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller, acf, pacf
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# ─── Analysis Output Models ────────────────────────────────────────

class TrendAnalysis(BaseModel):
    direction: str  # "increasing", "decreasing", "stable"
    slope: float
    r_squared: float
    p_value: float
    significance: bool
    mann_kendall_tau: float | None = None
    mann_kendall_p: float | None = None


class SeasonalityAnalysis(BaseModel):
    has_seasonality: bool
    periods: list[int]  # Detected seasonal periods (e.g., 7 for weekly, 12 for monthly)
    strength: float  # 0.0 to 1.0
    decomposition: dict[str, list[float]]  # trend, seasonal, residual components


class AnomalyReport(BaseModel):
    total_anomalies: int
    anomaly_rate: float
    anomalies: list[dict]  # Each with index, value, severity, method
    method_used: str


class AnalysisReport(BaseModel):
    descriptive_stats: dict[str, dict[str, float]]
    trend: TrendAnalysis
    seasonality: SeasonalityAnalysis
    anomalies: AnomalyReport
    correlations: dict[str, dict[str, float]]
    segments: list[dict]
    feature_importance: dict[str, float]
    summary: str
    recommendations_for_prediction: list[str]


# ─── Tools ─────────────────────────────────────────────────────────

@tool
def compute_descriptive_statistics(dataset: dict) -> dict:
    """
    Compute comprehensive descriptive statistics for all numeric columns.
    
    Args:
        dataset: The collected dataset as a dictionary
    
    Returns:
        Dictionary with statistics for each numeric column
    """
    df = pd.DataFrame(dataset.get("data", []))
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    results = {}
    for col in numeric_cols:
        series = df[col].dropna()
        results[col] = {
            "count": int(series.count()),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
            "q25": float(series.quantile(0.25)),
            "q75": float(series.quantile(0.75)),
            "skewness": float(series.skew()),
            "kurtosis": float(series.kurtosis()),
            "iqr": float(series.quantile(0.75) - series.quantile(0.25)),
            "cv": float(series.std() / series.mean()) if series.mean() != 0 else None,
        }
    
    return results


@tool
def analyze_trend(
    time_series: list[float],
    dates: list[str],
    test_type: str = "auto"
) -> dict:
    """
    Perform trend analysis on a time series using multiple methods.
    
    Args:
        time_series: Ordered list of values
        dates: Corresponding dates
        test_type: "linear", "mann_kendall", or "auto" (runs both)
    
    Returns:
        Trend analysis results with direction, strength, and significance
    """
    values = np.array(time_series)
    n = len(values)
    
    # Linear regression trend
    x = np.arange(n)
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
    
    # Mann-Kendall trend test (non-parametric)
    mk_tau = None
    mk_p = None
    if test_type in ("mann_kendall", "auto"):
        # Compute Mann-Kendall statistic
        s = 0
        for i in range(n - 1):
            for j in range(i + 1, n):
                s += np.sign(values[j] - values[i])
        
        # Variance of S
        unique_values, counts = np.unique(values, return_counts=True)
        tie_correction = sum(c * (c - 1) * (2 * c + 5) for c in counts if c > 1)
        var_s = (n * (n - 1) * (2 * n + 5) - tie_correction) / 18
        
        if var_s > 0:
            if s > 0:
                z = (s - 1) / np.sqrt(var_s)
            elif s < 0:
                z = (s + 1) / np.sqrt(var_s)
            else:
                z = 0
            mk_tau = s / (0.5 * n * (n - 1))
            mk_p = 2 * (1 - stats.norm.cdf(abs(z)))
    
    # Determine direction
    if mk_tau is not None:
        if mk_tau > 0.1:
            direction = "increasing"
        elif mk_tau < -0.1:
            direction = "decreasing"
        else:
            direction = "stable"
    else:
        direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
    
    return {
        "direction": direction,
        "slope": float(slope),
        "r_squared": float(r_value ** 2),
        "p_value": float(p_value),
        "significance": bool(p_value < 0.05),
        "mann_kendall_tau": float(mk_tau) if mk_tau is not None else None,
        "mann_kendall_p": float(mk_p) if mk_p is not None else None,
    }


@tool
def detect_seasonality(
    time_series: list[float],
    dates: list[str],
    max_period: int = 365
) -> dict:
    """
    Detect seasonality patterns using FFT and autocorrelation analysis.
    
    Args:
        time_series: Ordered list of values
        dates: Corresponding dates
        max_period: Maximum seasonal period to test
    
    Returns:
        Seasonality analysis with detected periods and strength
    """
    values = np.array(time_series)
    n = len(values)
    
    # Detrend the series
    x = np.arange(n)
    slope, intercept, _, _, _ = stats.linregress(x, values)
    detrended = values - (slope * x + intercept)
    
    # FFT analysis
    fft_vals = np.fft.rfft(detrended)
    power = np.abs(fft_vals) ** 2
    freqs = np.fft.rfftfreq(n)
    
    # Find dominant frequencies (excluding DC component)
    dominant_indices = np.argsort(power[1:])[::-1][:5] + 1
    detected_periods = []
    for idx in dominant_indices:
        if freqs[idx] > 0:
            period = int(round(1.0 / freqs[idx]))
            if 2 <= period <= min(max_period, n // 2):
                detected_periods.append({
                    "period": period,
                    "power": float(power[idx]),
                    "relative_power": float(power[idx] / power[1:].sum())
                })
    
    # Autocorrelation analysis
    acf_vals = acf(detrended, nlags=min(n // 4, max_period), fft=True)
    
    # Find peaks in ACF
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(acf_vals, height=0.1, distance=2)
    
    # Seasonal decomposition (if enough data)
    decomposition = {}
    if n >= 2 * max(detected_periods, key=lambda x: x["period"])["period"] if detected_periods else 0:
        try:
            period = detected_periods[0]["period"] if detected_periods else 7
            result = seasonal_decompose(
                pd.Series(values), 
                model="additive", 
                period=period
            )
            decomposition = {
                "trend": result.trend.dropna().tolist(),
                "seasonal": result.seasonal.dropna().tolist(),
                "residual": result.resid.dropna().tolist(),
            }
        except Exception:
            pass
    
    # Calculate seasonality strength
    if decomposition and "seasonal" in decomposition and "residual" in decomposition:
        var_seasonal = np.var(decomposition["seasonal"])
        var_residual = np.var(decomposition["residual"])
        strength = var_seasonal / (var_seasonal + var_residual) if (var_seasonal + var_residual) > 0 else 0.0
    else:
        strength = 0.0
    
    return {
        "has_seasonality": len(detected_periods) > 0 and strength > 0.1,
        "periods": [p["period"] for p in detected_periods],
        "period_details": detected_periods,
        "strength": float(strength),
        "acf_peaks": peaks.tolist(),
        "decomposition": decomposition,
    }


@tool
def detect_anomalies(
    dataset: dict,
    columns: list[str] | None = None,
    method: str = "isolation_forest",
    contamination: float = 0.05
) -> dict:
    """
    Detect anomalies in the dataset using specified method.
    
    Args:
        dataset: The dataset to analyze
        columns: Columns to check (None = all numeric)
        method: "isolation_forest", "zscore", or "iqr"
        contamination: Expected proportion of anomalies
    
    Returns:
        Anomaly report with flagged records
    """
    df = pd.DataFrame(dataset.get("data", []))
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    anomalies = []
    
    if method == "isolation_forest":
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df[columns].fillna(df[columns].median()))
        
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        predictions = iso_forest.fit_predict(scaled_data)
        scores = iso_forest.score_samples(scaled_data)
        
        for idx, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # Anomaly
                severity = "high" if score < -0.6 else "medium" if score < -0.4 else "low"
                anomalies.append({
                    "row_index": int(idx),
                    "anomaly_score": float(score),
                    "severity": severity,
                    "method": "isolation_forest",
                    "values": {col: float(df.iloc[idx][col]) for col in columns}
                })
    
    elif method == "zscore":
        for col in columns:
            series = df[col].dropna()
            z_scores = np.abs(stats.zscore(series))
            threshold = 3.0
            for idx, z in enumerate(z_scores):
                if z > threshold:
                    anomalies.append({
                        "row_index": int(idx),
                        "column": col,
                        "z_score": float(z),
                        "severity": "high" if z > 4 else "medium",
                        "method": "zscore",
                        "value": float(series.iloc[idx])
                    })
    
    elif method == "iqr":
        for col in columns:
            series = df[col].dropna()
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            for idx, val in series.items():
                if val < lower or val > upper:
                    anomalies.append({
                        "row_index": int(idx),
                        "column": col,
                        "value": float(val),
                        "bounds": [float(lower), float(upper)],
                        "severity": "high" if val < (q1 - 3 * iqr) or val > (q3 + 3 * iqr) else "medium",
                        "method": "iqr"
                    })
    
    return {
        "total_anomalies": len(anomalies),
        "anomaly_rate": len(anomalies) / len(df) if len(df) > 0 else 0.0,
        "anomalies": anomalies,
        "method_used": method,
    }


@tool
def compute_correlations(
    dataset: dict,
    target_column: str,
    method: str = "pearson"
) -> dict:
    """
    Compute correlation between all features and the target variable.
    
    Args:
        dataset: The dataset
        target_column: The target variable (e.g., "revenue", "units_sold")
        method: "pearson", "spearman", or "kendall"
    
    Returns:
    Correlation matrix and feature-target correlations
    """
    df = pd.DataFrame(dataset.get("data", []))
    numeric_df = df.select_dtypes(include=[np.number])
    
    # Full correlation matrix
    corr_matrix = numeric_df.corr(method=method)
    
    # Feature-target correlations
    if target_column in numeric_df.columns:
        target_corr = corr_matrix[target_column].drop(target_column).sort_values(key=abs, ascending=False)
        feature_target_corr = target_corr.to_dict()
    else:
        feature_target_corr = {}
    
    return {
        "correlation_matrix": corr_matrix.to_dict(),
        "feature_target_correlations": feature_target_corr,
        "method": method,
        "strongest_positive": max(feature_target_corr.items(), key=lambda x: x[1]) if feature_target_corr else None,
        "strongest_negative": min(feature_target_corr.items(), key=lambda x: x[1]) if feature_target_corr else None,
    }


@tool
def segment_customers(
    dataset: dict,
    segment_by: list[str] = ["recency", "frequency", "monetary"],
    n_segments: int = 5
) -> dict:
    """
    Perform RFM (Recency, Frequency, Monetary) customer segmentation.
    
    Args:
        dataset: Customer transaction data
        segment_by: Segmentation dimensions
        n_segments: Number of segments to create
    
    Returns:
        Segment definitions and assignments
    """
    df = pd.DataFrame(dataset.get("data", []))
    
    # Compute RFM scores
    if all(col in df.columns for col in ["customer_id", "order_date", "amount"]):
        snapshot_date = pd.to_datetime(df["order_date"]).max()
        
        rfm = df.groupby("customer_id").agg({
            "order_date": lambda x: (snapshot_date - pd.to_datetime(x).max()).days,  # Recency
            "order_id": "nunique",  # Frequency
            "amount": "sum"  # Monetary
        }).rename(columns={
            "order_date": "recency",
            "order_id": "frequency",
            "amount": "monetary"
        })
        
        # Score each dimension (1-5, 5 being best)
        for col in ["recency", "frequency", "monetary"]:
            if col == "recency":
                # Lower recency is better
                rfm[f"{col}_score"] = pd.qcut(rfm[col], q=n_segments, labels=range(n_segments, 0, -1))
            else:
                rfm[f"{col}_score"] = pd.qcut(rfm[col], q=n_segments, labels=range(1, n_segments + 1))
        
        # Combined RFM score
        rfm["rfm_score"] = (
            rfm["recency_score"].astype(str) +
            rfm["frequency_score"].astype(str) +
            rfm["monetary_score"].astype(str)
        )
        
        # Segment labels
        segment_labels = {
            "555": "Champions", "554": "Champions", "544": "Champions", "545": "Champions",
            "454": "Loyal Customers", "455": "Loyal Customers", "445": "Loyal Customers",
            "543": "Potential Loyalists", "542": "Potential Loyalists", "541": "Potential Loyalists",
            "533": "Potential Loyalists", "532": "Potential Loyalists", "531": "Potential Loyalists",
            "523": "Potential Loyalists", "522": "Potential Loyalists", "521": "Potential Loyalists",
            "441": "New Customers", "442": "New Customers", "432": "New Customers",
            "431": "New Customers", "421": "New Customers", "422": "New Customers",
            "355": "At Risk", "354": "At Risk", "345": "At Risk", "344": "At Risk",
            "353": "At Risk", "352": "At Risk", "343": "At Risk", "342": "At Risk",
            "341": "At Risk", "335": "At Risk", "334": "At Risk",
            "333": "Need Attention", "332": "Need Attention", "331": "Need Attention",
            "325": "Need Attention", "324": "Need Attention", "323": "Need Attention",
            "322": "Need Attention", "321": "Need Attention",
            "155": "Cannot Lose Them", "154": "Cannot Lose Them", "145": "Cannot Lose Them",
            "144": "Cannot Lose Them", "155": "Cannot Lose Them",
            "153": "At Risk", "152": "At Risk", "151": "At Risk",
            "143": "At Risk", "142": "At Risk", "141": "At Risk",
            "135": "Hibernating", "134": "Hibernating", "133": "Hibernating",
            "132": "Hibernating", "131": "Hibernating", "125": "Hibernating",
            "124": "Hibernating", "123": "Hibernating", "122": "Hibernating",
            "121": "Hibernating", "115": "Lost", "114": "Lost", "113": "Lost",
            "112": "Lost", "111": "Lost",
        }
        
        rfm["segment"] = rfm["rfm_score"].map(segment_labels).fillna("Others")
        
        segment_summary = rfm.groupby("segment").agg({
            "recency": "mean",
            "frequency": "mean",
            "monetary": ["mean", "count"]
        }).round(2)
        
        return {
            "segment_summary": segment_summary.to_dict(),
            "customer_segments": rfm[["recency", "frequency", "monetary", "rfm_score", "segment"]].to_dict(orient="records"),
            "n_segments": rfm["segment"].nunique(),
        }
    
    return {"error": "Required columns not found for RFM analysis"}


# ─── Agent Definition ──────────────────────────────────────────────

ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Analysis Agent for the sales forecasting system.
    
Your responsibilities:
1. Perform comprehensive exploratory data analysis (EDA)
2. Identify trends, seasonality, and patterns in the sales data
3. Detect anomalies that could indicate data quality issues or significant events
4. Analyze correlations between features and target variables
5. Segment customers/products for targeted forecasting
6. Generate actionable insights for the prediction agent

Guidelines:
- Use statistical tests to validate findings (don't rely on visual inspection alone)
- Consider both linear and non-linear patterns
- Account for external factors (holidays, promotions, economic conditions)
- Flag any data quality issues that survived the collection phase
- Prioritize findings by business impact

Dataset shape: {dataset_shape}
Date range: {date_range}
Target variable: {target_variable}
"""),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    ("human", "Analyze the sales data and produce a comprehensive analysis report."),
])


def create_analysis_agent(llm: ChatOpenAI | None = None) -> AgentExecutor:
    """Factory function to create the Analysis Agent."""
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [
        compute_descriptive_statistics,
        analyze_trend,
        detect_seasonality,
        detect_anomalies,
        compute_correlations,
        segment_customers,
    ]
    
    agent = create_openai_functions_agent(llm, tools, ANALYSIS_PROMPT)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=20,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )
```

---

## 4. Prediction Agent Implementation

### 4.1 Purpose

The Prediction Agent generates accurate sales forecasts using an ensemble of statistical and machine learning models, selecting the best model based on data characteristics and historical performance.

### 4.2 Model Selection Strategy

| Data Characteristic | Primary Model | Secondary Model | Ensemble Weight |
|---------------------|---------------|-----------------|-----------------|
| Strong trend + seasonality | Prophet | SARIMA | 0.6 / 0.4 |
| Trend only | ARIMA | Exponential Smoothing | 0.5 / 0.5 |
| Seasonal only | TBATS | Prophet | 0.5 / 0.5 |
| Non-linear patterns | XGBoost | LightGBM | 0.5 / 0.5 |
| Short history (< 30 points) | Exponential Smoothing | Simple Moving Average | 0.7 / 0.3 |
| Long history (> 2 years) | Prophet + XGBoost | DeepAR | 0.4 / 0.3 / 0.3 |
| Intermittent demand | Croston's method | TSB | 0.5 / 0.5 |

### 4.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import Any, Literal
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ─── Prediction Output Models ──────────────────────────────────────

class ForecastPoint(BaseModel):
    date: str
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence: float


class ModelPerformance(BaseModel):
    model_name: str
    mape: float
    rmse: float
    mae: float
    r_squared: float
    training_time_seconds: float


class ForecastResult(BaseModel):
    forecast_id: str
    model_used: str
    ensemble_models: list[str]
    forecast_horizon: int
    forecast_points: list[ForecastPoint]
    model_performance: ModelPerformance
    feature_importance: dict[str, float]
    metadata: dict[str, Any]


# ─── Tools ─────────────────────────────────────────────────────────

@tool
def train_prophet_model(
    time_series: list[float],
    dates: list[str],
    seasonality_mode: Literal["additive", "multiplicative"] = "multiplicative",
    changepoint_prior_scale: float = 0.05,
    yearly_seasonality: bool = True,
    weekly_seasonality: bool = True,
    daily_seasonality: bool = False,
    holidays: dict | None = None
) -> dict:
    """
    Train a Facebook Prophet model on the time series data.
    
    Args:
        time_series: Historical values
        dates: Corresponding dates
        seasonality_mode: How seasonality is modeled
        changepoint_prior_scale: Flexibility of trend changes
        yearly_seasonality: Include yearly patterns
        weekly_seasonality: Include weekly patterns
        daily_seasonality: Include daily patterns
        holidays: Custom holidays dataframe
    
    Returns:
        Trained model info and forecast
    """
    from prophet import Prophet
    
    df = pd.DataFrame({
        "ds": pd.to_datetime(dates),
        "y": time_series
    })
    
    model = Prophet(
        seasonality_mode=seasonality_mode,
        changepoint_prior_scale=changepoint_prior_scale,
        yearly_seasonality=yearly_seasonality,
        weekly_seasonality=weekly_seasonality,
        daily_seasonality=daily_seasonality,
        interval_width=0.95,
    )
    
    if holidays:
        model.holidays = pd.DataFrame(holidays)
    
    model.fit(df)
    
    return {
        "model_type": "prophet",
        "model_params": {
            "seasonality_mode": seasonality_mode,
            "changepoint_prior_scale": changepoint_prior_scale,
        },
        "training_samples": len(df),
        "model_object": model,  # Would be serialized in production
    }


@tool
def train_arima_model(
    time_series: list[float],
    order: tuple[int, int, int] = (1, 1, 1),
    seasonal_order: tuple[int, int, int, int] | None = None,
    auto_select: bool = True
) -> dict:
    """
    Train an ARIMA/SARIMA model on the time series data.
    
    Args:
        time_series: Historical values
        order: (p, d, q) order for ARIMA
        seasonal_order: (P, D, Q, s) for SARIMA
        auto_select: Use auto_arima to find best parameters
    
    Returns:
        Trained model info and diagnostics
    """
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    
    values = np.array(time_series)
    
    # Check stationarity
    adf_result = adfuller(values)
    is_stationary = adf_result[1] < 0.05
    
    if auto_select:
        # Use auto_arima for parameter selection
        try:
            from pmdarima import auto_arima
            auto_model = auto_arima(
                values,
                seasonal=seasonal_order is not None,
                m=seasonal_order[3] if seasonal_order else 1,
                suppress_warnings=True,
                stepwise=True,
                error_action="ignore"
            )
            order = auto_model.order
            seasonal_order = auto_model.seasonal_order
        except ImportError:
            pass  # Fall back to provided order
    
    # Fit model
    if seasonal_order:
        model = ARIMA(values, order=order, seasonal_order=seasonal_order)
    else:
        model = ARIMA(values, order=order)
    
    fitted = model.fit()
    
    return {
        "model_type": "sarima" if seasonal_order else "arima",
        "order": order,
        "seasonal_order": seasonal_order,
        "aic": float(fitted.aic),
        "bic": float(fitted.bic),
        "is_stationary": is_stationary,
        "adf_pvalue": float(adf_result[1]),
        "model_object": fitted,
    }


@tool
def train_xgboost_forecast(
    features: list[dict],
    target: list[float],
    forecast_features: list[dict] | None = None,
    params: dict | None = None
) -> dict:
    """
    Train an XGBoost model for sales forecasting with feature engineering.
    
    Args:
        features: List of feature dictionaries (one per time step)
        target: Target values
        forecast_features: Features for future periods (if None, uses time-based features)
        params: XGBoost hyperparameters
    
    Returns:
        Trained model and feature importance
    """
    import xgboost as xgb
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
    
    X = pd.DataFrame(features)
    y = np.array(target)
    
    # Default parameters optimized for sales forecasting
    default_params = {
        "objective": "reg:squarederror",
        "n_estimators": 500,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
        "gamma": 0.1,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": 42,
    }
    
    if params:
        default_params.update(params)
    
    # Time series cross-validation
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []
    
    for train_idx, val_idx in tscv.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        model = xgb.XGBRegressor(**default_params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        y_pred = model.predict(X_val)
        mape = mean_absolute_percentage_error(y_val, y_pred)
        cv_scores.append(mape)
    
    # Final model on all data
    final_model = xgb.XGBRegressor(**default_params)
    final_model.fit(X, y, verbose=False)
    
    # Feature importance
    importance = final_model.feature_importances_
    feature_importance = dict(zip(X.columns, importance.tolist()))
    
    return {
        "model_type": "xgboost",
        "cv_mape_mean": float(np.mean(cv_scores)),
        "cv_mape_std": float(np.std(cv_scores)),
        "feature_importance": feature_importance,
        "n_features": len(X.columns),
        "model_object": final_model,
    }


@tool
def train_exponential_smoothing(
    time_series: list[float],
    trend: Literal["add", "mul", None] = "add",
    seasonal: Literal["add", "mul", None] = "add",
    seasonal_periods: int | None = None,
    damped_trend: bool = True
) -> dict:
    """
    Train a Holt-Winters Exponential Smoothing model.
    
    Args:
        time_series: Historical values
        trend: Trend component type
        seasonal: Seasonal component type
        seasonal_periods: Number of periods in a season
        damped_trend: Whether to dampen the trend
    
    Returns:
        Trained model info
    """
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    
    values = np.array(time_series)
    
    model = ExponentialSmoothing(
        values,
        trend=trend,
        seasonal=seasonal,
        seasonal_periods=seasonal_periods,
        damped_trend=damped_trend,
    )
    
    fitted = model.fit(optimized=True)
    
    return {
        "model_type": "exponential_smoothing",
        "smoothing_level": float(fitted.params.get("smoothing_level", 0)),
        "smoothing_trend": float(fitted.params.get("smoothing_trend", 0)),
        "smoothing_seasonal": float(fitted.params.get("smoothing_seasonal", 0)),
        "aic": float(fitted.aic),
        "bic": float(fitted.bic),
        "model_object": fitted,
    }


@tool
def generate_forecast(
    model_type: str,
    model_object: Any,
    horizon: int,
    frequency: Literal["D", "W", "M", "Q"] = "D",
    confidence_level: float = 0.95,
    future_features: list[dict] | None = None
) -> dict:
    """
    Generate forecasts from a trained model.
    
    Args:
        model_type: Type of model ("prophet", "arima", "xgboost", "exponential_smoothing")
        model_object: The trained model object
        horizon: Number of periods to forecast
        frequency: Frequency of forecast periods
        confidence_level: Confidence level for prediction intervals
        future_features: Future feature values (for XGBoost)
    
    Returns:
        Forecast values with confidence intervals
    """
    from scipy import stats
    
    alpha = 1 - confidence_level
    z_score = stats.norm.ppf(1 - alpha / 2)
    
    if model_type == "prophet":
        future = model_object.make_future_dataframe(periods=horizon, freq=frequency)
        forecast = model_object.predict(future)
        forecast = forecast.tail(horizon)
        
        return {
            "dates": forecast["ds"].dt.strftime("%Y-%m-%d").tolist(),
            "predicted": forecast["yhat"].tolist(),
            "lower_bound": forecast["yhat_lower"].tolist(),
            "upper_bound": forecast["yhat_upper"].tolist(),
        }
    
    elif model_type in ("arima", "sarima"):
        forecast_result = model_object.get_forecast(steps=horizon)
        pred = forecast_result.predicted_mean
        conf_int = forecast_result.conf_int(alpha=alpha)
        
        return {
            "dates": [str(d) for d in pred.index],
            "predicted": pred.tolist(),
            "lower_bound": conf_int.iloc[:, 0].tolist(),
            "upper_bound": conf_int.iloc[:, 1].tolist(),
        }
    
    elif model_type == "xgboost":
        if future_features is None:
            raise ValueError("future_features required for XGBoost forecasting")
        
        X_future = pd.DataFrame(future_features)
        predictions = model_object.predict(X_future)
        
        # Estimate prediction intervals using residual std
        residuals = model_object.resid_ if hasattr(model_object, "resid_") else np.zeros(len(predictions))
        residual_std = np.std(residuals)
        
        return {
            "dates": [f"period_{i}" for i in range(horizon)],
            "predicted": predictions.tolist(),
            "lower_bound": (predictions - z_score * residual_std).tolist(),
            "upper_bound": (predictions + z_score * residual_std).tolist(),
        }
    
    elif model_type == "exponential_smoothing":
        forecast_values = model_object.forecast(horizon)
        
        # Approximate confidence intervals
        resid_std = np.std(model_object.resid)
        
        return {
            "dates": [f"period_{i}" for i in range(horizon)],
            "predicted": forecast_values.tolist(),
            "lower_bound": (forecast_values - z_score * resid_std).tolist(),
            "upper_bound": (forecast_values + z_score * resid_std).tolist(),
        }
    
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


@tool
def ensemble_forecasts(
    forecasts: list[dict],
    weights: list[float] | None = None,
    method: Literal["weighted_average", "median", "stacking"] = "weighted_average"
) -> dict:
    """
    Combine multiple model forecasts into an ensemble prediction.
    
    Args:
        forecasts: List of forecast dictionaries from different models
        weights: Ensemble weights (None = equal weights)
        method: Ensemble combination method
    
    Returns:
        Ensemble forecast with combined confidence intervals
    """
    if not forecasts:
        return {"error": "No forecasts provided"}
    
    n_models = len(forecasts)
    horizon = len(forecasts[0]["predicted"])
    
    if weights is None:
        weights = [1.0 / n_models] * n_models
    
    # Normalize weights
    weights = np.array(weights) / sum(weights)
    
    # Stack predictions
    all_preds = np.array([f["predicted"] for f in forecasts])  # (n_models, horizon)
    
    if method == "weighted_average":
        ensemble_pred = np.average(all_preds, axis=0, weights=weights)
    elif method == "median":
        ensemble_pred = np.median(all_preds, axis=0)
    else:
        ensemble_pred = np.average(all_preds, axis=0, weights=weights)
    
    # Combine confidence intervals (conservative: widest range)
    all_lower = np.array([f["lower_bound"] for f in forecasts])
    all_upper = np.array([f["upper_bound"] for f in forecasts])
    
    ensemble_lower = np.min(all_lower, axis=0)
    ensemble_upper = np.max(all_upper, axis=0)
    
    # Uncertainty estimation
    model_disagreement = np.std(all_preds, axis=0)
    
    return {
        "predicted": ensemble_pred.tolist(),
        "lower_bound": ensemble_lower.tolist(),
        "upper_bound": ensemble_upper.tolist(),
        "model_disagreement": model_disagreement.tolist(),
        "weights": weights.tolist(),
        "method": method,
        "n_models": n_models,
    }


@tool
def evaluate_model_performance(
    actual: list[float],
    predicted: list[float]
) -> dict:
    """
    Compute comprehensive model performance metrics.
    
    Args:
        actual: Actual values
        predicted: Predicted values
    
    Returns:
        Performance metrics including MAPE, RMSE, MAE, R-squared
    """
    from sklearn.metrics import (
        mean_absolute_percentage_error,
        mean_squared_error,
        mean_absolute_error,
        r2_score
    )
    
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    # Handle zero actuals for MAPE
    mask = actual != 0
    mape = mean_absolute_percentage_error(actual[mask], predicted[mask]) * 100 if mask.any() else float("inf")
    
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mae = mean_absolute_error(actual, predicted)
    r2 = r2_score(actual, predicted)
    
    # Additional metrics
    mpe = np.mean((actual[mask] - predicted[mask]) / actual[mask]) * 100 if mask.any() else 0.0
    smape = np.mean(2 * np.abs(actual - predicted) / (np.abs(actual) + np.abs(predicted))) * 100
    
    # Directional accuracy
    if len(actual) > 1:
        actual_direction = np.sign(np.diff(actual))
        pred_direction = np.sign(np.diff(predicted))
        directional_accuracy = np.mean(actual_direction == pred_direction) * 100
    else:
        directional_accuracy = 0.0
    
    return {
        "mape": float(mape),
        "rmse": float(rmse),
        "mae": float(mae),
        "r_squared": float(r2),
        "mpe": float(mpe),  # Mean percentage error (bias indicator)
        "smape": float(smape),
        "directional_accuracy": float(directional_accuracy),
    }


# ─── Agent Definition ──────────────────────────────────────────────

PREDICTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Prediction Agent for the sales forecasting system.
    
Your responsibilities:
1. Select appropriate forecasting models based on data characteristics
2. Train multiple models and evaluate their performance
3. Generate ensemble forecasts for robustness
4. Provide confidence intervals for all predictions
5. Select the best model or ensemble based on cross-validation performance

Guidelines:
- Always train at least 2-3 different model types for comparison
- Use time-series cross-validation (never random split for time series)
- Prefer simpler models when performance is similar (Occam's razor)
- Account for known future events (promotions, holidays, product launches)
- Provide prediction intervals, not just point estimates
- Flag if forecast confidence is low and recommend human review

Analysis findings: {analysis_summary}
Historical data points: {n_historical_points}
Forecast horizon: {horizon}
Target variable: {target_variable}
Seasonality detected: {seasonality_info}
Trend direction: {trend_direction}
"""),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    ("human", "Generate sales forecasts for the specified horizon with confidence intervals."),
])


def create_prediction_agent(llm: ChatOpenAI | None = None) -> AgentExecutor:
    """Factory function to create the Prediction Agent."""
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [
        train_prophet_model,
        train_arima_model,
        train_xgboost_forecast,
        train_exponential_smoothing,
        generate_forecast,
        ensemble_forecasts,
        evaluate_model_performance,
    ]
    
    agent = create_openai_functions_agent(llm, tools, PREDICTION_PROMPT)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=25,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )
```

### 4.4 Feature Engineering

```python
class FeatureEngineer:
    """Generate time-based and lag features for ML models."""
    
    @staticmethod
    def create_time_features(dates: list[str]) -> pd.DataFrame:
        """Create calendar-based features."""
        dt = pd.to_datetime(dates)
        return pd.DataFrame({
            "year": dt.dt.year,
            "month": dt.dt.month,
            "day": dt.dt.day,
            "dayofweek": dt.dt.dayofweek,
            "dayofyear": dt.dt.dayofyear,
            "weekofyear": dt.dt.isocalendar().week.astype(int),
            "quarter": dt.dt.quarter,
            "is_month_start": dt.dt.is_month_start.astype(int),
            "is_month_end": dt.dt.is_month_end.astype(int),
            "is_quarter_start": dt.dt.is_quarter_start.astype(int),
            "is_quarter_end": dt.dt.is_quarter_end.astype(int),
            "is_weekend": (dt.dt.dayofweek >= 5).astype(int),
        })
    
    @staticmethod
    def create_lag_features(values: list[float], lags: list[int] = [1, 7, 14, 28]) -> pd.DataFrame:
        """Create lag features for time series."""
        df = pd.DataFrame({"value": values})
        for lag in lags:
            df[f"lag_{lag}"] = df["value"].shift(lag)
        return df
    
    @staticmethod
    def create_rolling_features(
        values: list[float], 
        windows: list[int] = [7, 14, 30, 90]
    ) -> pd.DataFrame:
        """Create rolling window statistics."""
        df = pd.DataFrame({"value": values})
        for window in windows:
            df[f"rolling_mean_{window}"] = df["value"].rolling(window=window).mean()
            df[f"rolling_std_{window}"] = df["value"].rolling(window=window).std()
            df[f"rolling_min_{window}"] = df["value"].rolling(window=window).min()
            df[f"rolling_max_{window}"] = df["value"].rolling(window=window).max()
        return df
    
    @staticmethod
    def create_expanding_features(values: list[float]) -> pd.DataFrame:
        """Create expanding window statistics."""
        df = pd.DataFrame({"value": values})
        df["expanding_mean"] = df["value"].expanding().mean()
        df["expanding_std"] = df["value"].expanding().std()
        df["expanding_max"] = df["value"].expanding().max()
        df["expanding_min"] = df["value"].expanding().min()
        return df
```

---

## 5. Action Agent Implementation

### 5.1 Purpose

The Action Agent translates forecast outputs into concrete, actionable business recommendations. It applies business rules, generates alerts, and creates task assignments for sales and operations teams.

### 5.2 Action Types

| Action Category | Trigger | Output | Priority |
|----------------|---------|--------|----------|
| **Inventory** | Forecasted demand > safety stock | Purchase order suggestions | High |
| **Pricing** | Demand forecast + competitor data | Dynamic pricing recommendations | Medium |
| **Staffing** | Forecasted sales volume | Shift scheduling suggestions | Medium |
| **Marketing** | Low demand forecast | Campaign suggestions | Medium |
| **Alerts** | Anomalous patterns detected | Immediate notifications | High |
| **Budget** | Revenue forecast vs. target | Budget reallocation suggestions | High |
| **Pipeline** | Lead forecast vs. quota | Sales activity recommendations | Medium |

### 5.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime, timedelta


# ─── Action Output Models ──────────────────────────────────────────

class ActionItem(BaseModel):
    action_id: str
    category: Literal["inventory", "pricing", "staffing", "marketing", "alert", "budget", "pipeline"]
    priority: Literal["critical", "high", "medium", "low"]
    title: str
    description: str
    expected_impact: dict[str, float]  # e.g., {"revenue_change": 5000, "cost_change": -2000}
    deadline: str | None
    assigned_team: str
    status: Literal["pending", "approved", "rejected", "completed"] = "pending"
    confidence: float
    supporting_data: dict[str, Any]


class AlertConfig(BaseModel):
    alert_id: str
    alert_type: Literal["demand_spike", "demand_drop", "forecast_deviation", "data_quality", "model_drift"]
    severity: Literal["info", "warning", "critical"]
    message: str
    affected_products: list[str]
    affected_regions: list[str]
    recommended_action: str
    auto_escalate: bool


# ─── Tools ─────────────────────────────────────────────────────────

@tool
def generate_inventory_recommendations(
    forecast: dict,
    current_inventory: dict[str, int],
    lead_times: dict[str, int],  # days
    safety_stock_levels: dict[str, int],
    reorder_points: dict[str, int]
) -> list[dict]:
    """
    Generate inventory recommendations based on demand forecasts.
    
    Args:
        forecast: Forecast output with predicted demand by product
        current_inventory: Current stock levels by product
        lead_times: Supplier lead times by product
        safety_stock_levels: Minimum stock levels by product
        reorder_points: Stock levels that trigger reorder
    
    Returns:
        List of inventory action items
    """
    actions = []
    
    for product_id, forecasted_demand in forecast.get("by_product", {}).items():
        current = current_inventory.get(product_id, 0)
        safety = safety_stock_levels.get(product_id, 0)
        reorder_pt = reorder_points.get(product_id, 0)
        lead_time = lead_times.get(product_id, 7)
        
        # Calculate days of supply
        daily_demand = forecasted_demand / 30  # Assuming monthly forecast
        days_of_supply = current / daily_demand if daily_demand > 0 else float("inf")
        
        # Check if reorder needed
        if current <= reorder_pt:
            order_quantity = max(
                forecasted_demand + safety - current,
                daily_demand * lead_time * 1.5  # Safety buffer
            )
            
            actions.append({
                "category": "inventory",
                "priority": "critical" if current < safety else "high",
                "title": f"Reorder {product_id}",
                "description": f"Current stock ({current}) below reorder point ({reorder_pt}). "
                              f"Forecasted demand: {forecasted_demand:.0f} units. "
                              f"Days of supply: {days_of_supply:.1f}",
                "recommended_order_quantity": int(order_quantity),
                "expected_stockout_date": (datetime.now() + timedelta(days=int(days_of_supply))).isoformat(),
                "assigned_team": "Procurement",
                "confidence": forecast.get("confidence", 0.8),
            })
        
        # Check for overstock
        elif current > forecasted_demand * 2:
            excess = current - forecasted_demand
            actions.append({
                "category": "inventory",
                "priority": "medium",
                "title": f"Excess inventory: {product_id}",
                "description": f"Current stock ({current}) significantly exceeds forecasted demand "
                              f"({forecasted_demand:.0f}). Excess: {excess:.0f} units.",
                "recommended_action": "Consider promotion or transfer to other regions",
                "excess_units": int(excess),
                "assigned_team": "Operations",
                "confidence": forecast.get("confidence", 0.8),
            })
    
    return actions


@tool
def generate_pricing_recommendations(
    forecast: dict,
    current_prices: dict[str, float],
    competitor_prices: dict[str, float],
    price_elasticity: dict[str, float],
    margin_threshold: float = 0.15
) -> list[dict]:
    """
    Generate dynamic pricing recommendations based on demand forecasts 
    and competitive positioning.
    
    Args:
        forecast: Demand forecast by product
        current_prices: Current prices by product
        competitor_prices: Competitor prices by product
        price_elasticity: Price elasticity coefficients by product
        margin_threshold: Minimum acceptable margin
    
    Returns:
        List of pricing action items
    """
    actions = []
    
    for product_id, predicted_demand in forecast.get("by_product", {}).items():
        current_price = current_prices.get(product_id, 0)
        comp_price = competitor_prices.get(product_id, current_price)
        elasticity = price_elasticity.get(product_id, -1.5)
        
        # Demand-based pricing
        if predicted_demand > forecast.get("historical_avg", {}).get(product_id, 0) * 1.2:
            # High demand - consider price increase
            suggested_increase = min(0.10, 1 / abs(elasticity) * 0.5)
            new_price = current_price * (1 + suggested_increase)
            
            # Don't exceed competitor price by too much
            if new_price > comp_price * 1.15:
                new_price = comp_price * 1.10
            
            actions.append({
                "category": "pricing",
                "priority": "medium",
                "title": f"Price increase opportunity: {product_id}",
                "description": f"High demand forecast ({predicted_demand:.0f} vs avg "
                              f"{forecast.get('historical_avg', {}).get(product_id, 0):.0f}). "
                              f"Suggested price: ${new_price:.2f} (from ${current_price:.2f})",
                "current_price": current_price,
                "suggested_price": round(new_price, 2),
                "expected_demand_change": f"{elasticity * suggested_increase * 100:.1f}%",
                "assigned_team": "Pricing",
                "confidence": forecast.get("confidence", 0.8),
            })
        
        elif predicted_demand < forecast.get("historical_avg", {}).get(product_id, 0) * 0.8:
            # Low demand - consider price decrease to stimulate
            suggested_decrease = min(0.15, 1 / abs(elasticity) * 0.3)
            new_price = current_price * (1 - suggested_decrease)
            
            # Check margin
            # Assuming cost is 60% of current price (simplified)
            cost = current_price * 0.6
            if (new_price - cost) / new_price < margin_threshold:
                new_price = cost / (1 - margin_threshold)
            
            actions.append({
                "category": "pricing",
                "priority": "medium",
                "title": f"Price decrease opportunity: {product_id}",
                "description": f"Low demand forecast ({predicted_demand:.0f} vs avg "
                              f"{forecast.get('historical_avg', {}).get(product_id, 0):.0f}). "
                              f"Suggested price: ${new_price:.2f} (from ${current_price:.2f})",
                "current_price": current_price,
                "suggested_price": round(new_price, 2),
                "expected_demand_change": f"+{abs(elasticity) * suggested_decrease * 100:.1f}%",
                "assigned_team": "Pricing",
                "confidence": forecast.get("confidence", 0.8),
            })
    
    return actions


@tool
def generate_staffing_recommendations(
    forecast: dict,
    current_staffing: dict[str, int],
    productivity_rates: dict[str, float],  # revenue per employee per day
    labor_cost_per_hour: dict[str, float]
) -> list[dict]:
    """
    Generate staffing recommendations based on forecasted sales volume.
    
    Args:
        forecast: Revenue and volume forecast
        current_staffing: Current headcount by role
        productivity_rates: Output per employee by role
        labor_cost_per_hour: Hourly cost by role
    
    Returns:
        List of staffing action items
    """
    actions = []
    
    forecasted_revenue = forecast.get("total_revenue", 0)
    historical_avg = forecast.get("historical_avg_revenue", forecasted_revenue)
    
    for role, current_count in current_staffing.items():
        rate = productivity_rates.get(role, 1000)
        required_headcount = int(np.ceil(forecasted_revenue / rate))
        
        if required_headcount > current_count * 1.2:
            # Need more staff
            additional = required_headcount - current_count
            actions.append({
                "category": "staffing",
                "priority": "high" if additional > 2 else "medium",
                "title": f"Hire {additional} {role}(s)",
                "description": f"Forecasted revenue ${forecasted_revenue:,.0f} requires "
                              f"{required_headcount} {role}(s), currently have {current_count}",
                "additional_headcount": additional,
                "estimated_cost": additional * labor_cost_per_hour.get(role, 25) * 2080,
                "assigned_team": "HR",
                "confidence": forecast.get("confidence", 0.8),
            })
        
        elif required_headcount < current_count * 0.8:
            # Overstaffed
            excess = current_count - required_headcount
            actions.append({
                "category": "staffing",
                "priority": "low",
                "title": f"Potential overstaffing: {role}",
                "description": f"Forecasted revenue ${forecasted_revenue:,.0f} requires "
                              f"{required_headcount} {role}(s), currently have {current_count}. "
                              f"Excess: {excess}",
                "excess_headcount": excess,
                "assigned_team": "HR",
                "confidence": forecast.get("confidence", 0.8),
            })
    
    return actions


@tool
def generate_marketing_recommendations(
    forecast: dict,
    campaign_history: list[dict],
    customer_segments: dict,
    marketing_budget: float
) -> list[dict]:
    """
    Generate marketing campaign recommendations based on demand forecasts 
    and customer segment analysis.
    
    Args:
        forecast: Demand forecast
        campaign_history: Historical campaign performance
        customer_segments: Customer segment definitions
        marketing_budget: Available marketing budget
    
    Returns:
        List of marketing action items
    """
    actions = []
    
    # Identify underperforming segments
    for segment_id, segment_data in customer_segments.items():
        if segment_data.get("forecasted_growth", 0) < 0:
            # Declining segment - retention campaign
            actions.append({
                "category": "marketing",
                "priority": "high",
                "title": f"Retention campaign for {segment_id}",
                "description": f"Segment {segment_id} showing declining trend. "
                              f"Recommend targeted retention campaign.",
                "target_segment": segment_id,
                "suggested_budget": marketing_budget * 0.2,
                "expected_roi": 3.5,
                "assigned_team": "Marketing",
                "confidence": forecast.get("confidence", 0.8),
            })
    
    # Identify high-growth opportunities
    for segment_id, segment_data in customer_segments.items():
        if segment_data.get("forecasted_growth", 0) > 0.2:
            # Growing segment - acquisition campaign
            actions.append({
                "category": "marketing",
                "priority": "medium",
                "title": f"Acquisition campaign for {segment_id}",
                "description": f"Segment {segment_id} showing strong growth potential "
                              f"({segment_data['forecasted_growth']:.0%}). "
                              f"Recommend lookalike audience campaign.",
                "target_segment": segment_id,
                "suggested_budget": marketing_budget * 0.3,
                "expected_roi": 4.0,
                "assigned_team": "Marketing",
                "confidence": forecast.get("confidence", 0.8),
            })
    
    return actions


@tool
def generate_alerts(
    forecast: dict,
    actuals: dict,
    thresholds: dict[str, float]
) -> list[dict]:
    """
    Generate alerts based on forecast deviations and threshold breaches.
    
    Args:
        forecast: Forecast output
        actuals: Recent actual values
        thresholds: Alert thresholds
    
    Returns:
        List of alert configurations
    """
    alerts = []
    
    # Check forecast vs actual deviation
    for product_id, forecasted in forecast.get("by_product", {}).items():
        actual = actuals.get(product_id, 0)
        deviation = abs(forecasted - actual) / actual if actual > 0 else 0
        
        if deviation > thresholds.get("deviation_pct", 0.25):
            alerts.append({
                "alert_type": "forecast_deviation",
                "severity": "warning" if deviation < 0.4 else "critical",
                "message": f"Product {product_id}: forecast ({forecasted:.0f}) deviates "
                          f"{deviation:.1%} from actual ({actual:.0f})",
                "affected_products": [product_id],
                "recommended_action": "Review forecast model and check for external factors",
                "auto_escalate": deviation > 0.5,
            })
    
    # Check for demand spikes
    for product_id, forecasted in forecast.get("by_product", {}).items():
        historical_avg = forecast.get("historical_avg", {}).get(product_id, 0)
        if historical_avg > 0 and forecasted > historical_avg * 1.5:
            alerts.append({
                "alert_type": "demand_spike",
                "severity": "info",
                "message": f"Product {product_id}: forecasted demand spike "
                          f"({forecasted:.0f} vs avg {historical_avg:.0f})",
                "affected_products": [product_id],
                "recommended_action": "Ensure adequate inventory and staffing",
                "auto_escalate": False,
            })
    
    return alerts


@tool
def generate_budget_recommendations(
    revenue_forecast: dict,
    cost_structure: dict[str, float],
    budget_targets: dict[str, float],
    profit_margin_target: float = 0.20
) -> list[dict]:
    """
    Generate budget reallocation recommendations based on revenue forecasts.
    
    Args:
        revenue_forecast: Revenue forecast by product/region
        cost_structure: Fixed and variable costs
        budget_targets: Current budget allocations
        profit_margin_target: Target profit margin
    
    Returns:
        List of budget action items
    """
    actions = []
    
    total_forecasted_revenue = revenue_forecast.get("total", 0)
    total_costs = sum(cost_structure.values())
    projected_margin = (total_forecasted_revenue - total_costs) / total_forecasted_revenue if total_forecasted_revenue > 0 else 0
    
    if projected_margin < profit_margin_target:
        gap = profit_margin_target - projected_margin
        required_cost_reduction = gap * total_forecasted_revenue
        
        actions.append({
            "category": "budget",
            "priority": "high",
            "title": "Cost reduction needed",
            "description": f"Projected margin {projected_margin:.1%} below target "
                          f"{profit_margin_target:.1%}. Need to reduce costs by "
                          f"${required_cost_reduction:,.0f} or increase revenue.",
            "required_cost_reduction": required_cost_reduction,
            "assigned_team": "Finance",
            "confidence": revenue_forecast.get("confidence", 0.8),
        })
    
    # Reallocate budget to high-performing products
    for product_id, forecasted_revenue in revenue_forecast.get("by_product", {}).items():
        current_budget = budget_targets.get(product_id, 0)
        roi = forecasted_revenue / current_budget if current_budget > 0 else 0
        
        if roi > 5.0:  # High ROI
            actions.append({
                "category": "budget",
                "priority": "medium",
                "title": f"Increase budget for {product_id}",
                "description": f"Product {product_id} showing high ROI ({roi:.1f}x). "
                              f"Recommend budget increase of 20%.",
                "current_budget": current_budget,
                "suggested_budget": current_budget * 1.2,
                "assigned_team": "Finance",
                "confidence": revenue_forecast.get("confidence", 0.8),
            })
    
    return actions


# ─── Agent Definition ──────────────────────────────────────────────

ACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Action Agent for the sales forecasting system.
    
Your responsibilities:
1. Translate forecasts into concrete, actionable business recommendations
2. Apply business rules and constraints to generate relevant actions
3. Prioritize actions by business impact and urgency
4. Generate alerts for critical situations
5. Create task assignments for relevant teams

Guidelines:
- Every action must be tied to specific forecast data
- Consider business constraints (budget, capacity, lead times)
- Prioritize actions by expected revenue impact
- Include confidence levels for each recommendation
- Flag actions that require human approval
- Avoid conflicting recommendations

Forecast summary: {forecast_summary}
Business rules: {business_rules}
Current inventory: {inventory_summary}
Budget constraints: {budget_constraints}
"""),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    ("human", "Generate actionable business recommendations based on the sales forecast."),
])


def create_action_agent(llm: ChatOpenAI | None = None) -> AgentExecutor:
    """Factory function to create the Action Agent."""
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [
        generate_inventory_recommendations,
        generate_pricing_recommendations,
        generate_staffing_recommendations,
        generate_marketing_recommendations,
        generate_alerts,
        generate_budget_recommendations,
    ]
    
    agent = create_openai_functions_agent(llm, tools, ACTION_PROMPT)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=20,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )
```

---

## 6. Performance Analytics Agent Implementation

### 6.1 Purpose

The Performance Analytics Agent monitors forecast accuracy, detects model drift, tracks system health, and triggers retraining when performance degrades.

### 6.2 Monitored Metrics

| Metric | Description | Threshold | Action |
|--------|-------------|-----------|--------|
| **MAPE** | Mean Absolute Percentage Error | > 15% | Retrain model |
| **RMSE** | Root Mean Squared Error | > 2x historical avg | Investigate |
| **Bias (MPE)** | Mean Percentage Error | > 10% | Adjust model |
| **Coverage** | % actuals within confidence interval | < 85% | Widen intervals |
| **Drift Score** | Population Stability Index | > 0.2 | Retrain |
| **Data Freshness** | Hours since last data update | > 48h | Alert |
| **Forecast Value Added** | vs. naive baseline | < 0 | Switch model |

### 6.3 Agent Implementation

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import Any, Literal
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ─── Performance Output Models ─────────────────────────────────────

class AccuracyMetrics(BaseModel):
    mape: float
    rmse: float
    mae: float
    mpe: float  # Bias
    smape: float
    coverage: float  # % within confidence intervals
    directional_accuracy: float
    forecast_value_added: float  # vs naive baseline


class DriftReport(BaseModel):
    drift_detected: bool
    drift_score: float  # Population Stability Index
    drift_type: Literal["covariate", "concept", "prediction"]
    affected_features: list[str]
    severity: Literal["low", "medium", "high", "critical"]
    recommended_action: str


class ModelHealthReport(BaseModel):
    model_id: str
    model_type: str
    overall_health: Literal["healthy", "degraded", "critical"]
    accuracy_trend: str  # "improving", "stable", "degrading"
    last_trained: str
    last_evaluated: str
    total_predictions: int
    metrics: AccuracyMetrics
    drift: DriftReport
    retrain_recommended: bool
    retrain_urgency: Literal["none", "low", "medium", "high"]
    feature_importance_shift: dict[str, float]


# ─── Tools ─────────────────────────────────────────────────────────

@tool
def compute_forecast_accuracy(
    actuals: list[float],
    predictions: list[float],
    confidence_intervals: list[dict] | None = None
) -> dict:
    """
    Compute comprehensive forecast accuracy metrics.
    
    Args:
        actuals: Actual observed values
        predictions: Forecasted values
        confidence_intervals: Optional list of {lower, upper} bounds
    
    Returns:
        Complete accuracy metrics
    """
    from sklearn.metrics import (
        mean_absolute_percentage_error,
        mean_squared_error,
        mean_absolute_error,
    )
    
    actuals = np.array(actuals)
    predictions = np.array(predictions)
    
    # Basic metrics
    mask = actuals != 0
    mape = mean_absolute_percentage_error(actuals[mask], predictions[mask]) * 100 if mask.any() else float("inf")
    rmse = np.sqrt(mean_squared_error(actuals, predictions))
    mae = mean_absolute_error(actuals, predictions)
    mpe = np.mean((actuals[mask] - predictions[mask]) / actuals[mask]) * 100 if mask.any() else 0.0
    smape = np.mean(2 * np.abs(actuals - predictions) / (np.abs(actuals) + np.abs(predictions))) * 100
    
    # Confidence interval coverage
    coverage = 0.0
    if confidence_intervals:
        within_bounds = sum(
            1 for a, ci in zip(actuals, confidence_intervals)
            if ci["lower"] <= a <= ci["upper"]
        )
        coverage = within_bounds / len(actuals) * 100
    
    # Directional accuracy
    if len(actuals) > 1:
        actual_dir = np.sign(np.diff(actuals))
        pred_dir = np.sign(np.diff(predictions))
        directional_accuracy = np.mean(actual_dir == pred_dir) * 100
    else:
        directional_accuracy = 0.0
    
    # Forecast Value Added (vs naive baseline)
    naive_pred = np.roll(actuals, 1)
    naive_pred[0] = actuals[0]
    naive_mape = mean_absolute_percentage_error(actuals[1:], naive_pred[1:]) * 100
    fva = (naive_mape - mape) / naive_mape * 100 if naive_mape > 0 else 0.0
    
    return {
        "mape": float(mape),
        "rmse": float(rmse),
        "mae": float(mae),
        "mpe": float(mpe),
        "smape": float(smape),
        "coverage": float(coverage),
        "directional_accuracy": float(directional_accuracy),
        "forecast_value_added": float(fva),
    }


@tool
def detect_data_drift(
    reference_data: list[dict],
    current_data: list[dict],
    threshold: float = 0.2
) -> dict:
    """
    Detect data drift using Population Stability Index (PSI) 
    and feature distribution comparisons.
    
    Args:
        reference_data: Training/baseline data
        current_data: Recent production data
        threshold: PSI threshold for drift detection
    
    Returns:
        Drift report with scores and affected features
    """
    ref_df = pd.DataFrame(reference_data)
    cur_df = pd.DataFrame(current_data)
    
    numeric_cols = ref_df.select_dtypes(include=[np.number]).columns
    
    drift_results = {}
    max_psi = 0.0
    affected_features = []
    
    for col in numeric_cols:
        if col not in cur_df.columns:
            continue
        
        ref_series = ref_df[col].dropna()
        cur_series = cur_df[col].dropna()
        
        if len(ref_series) == 0 or len(cur_series) == 0:
            continue
        
        # Create bins based on reference data
        bins = np.percentile(ref_series, np.linspace(0, 100, 11))
        bins = np.unique(bins)  # Remove duplicates
        
        if len(bins) < 2:
            continue
        
        ref_counts = np.histogram(ref_series, bins=bins)[0]
        cur_counts = np.histogram(cur_series, bins=bins)[0]
        
        # Convert to proportions
        ref_pct = ref_counts / ref_counts.sum()
        cur_pct = cur_counts / cur_counts.sum()
        
        # Avoid division by zero
        ref_pct = np.clip(ref_pct, 1e-6, None)
        cur_pct = np.clip(cur_pct, 1e-6, None)
        
        # PSI calculation
        psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        
        drift_results[col] = {
            "psi": float(psi),
            "drifted": bool(psi > threshold),
            "ref_mean": float(ref_series.mean()),
            "cur_mean": float(cur_series.mean()),
            "mean_shift_pct": float((cur_series.mean() - ref_series.mean()) / ref_series.mean() * 100) if ref_series.mean() != 0 else 0.0,
        }
        
        if psi > threshold:
            affected_features.append(col)
        
        max_psi = max(max_psi, psi)
    
    # Determine drift type and severity
    if max_psi > 0.3:
        severity = "critical"
    elif max_psi > 0.2:
        severity = "high"
    elif max_psi > 0.1:
        severity = "medium"
    else:
        severity = "low"
    
    return {
        "drift_detected": bool(max_psi > threshold),
        "drift_score": float(max_psi),
        "drift_type": "covariate",
        "affected_features": affected_features,
        "severity": severity,
        "feature_drift": drift_results,
        "recommended_action": (
            "Immediate model retraining required" if severity == "critical"
            else "Schedule model retraining within 1 week" if severity == "high"
            else "Monitor closely and retrain at next scheduled interval" if severity == "medium"
            else "No action needed"
        ),
    }


@tool
def detect_concept_drift(
    historical_residuals: list[float],
    recent_residuals: list[float],
    threshold: float = 2.0
) -> dict:
    """
    Detect concept drift by analyzing changes in forecast residual patterns.
    
    Args:
        historical_residuals: Residuals from model training/validation
        recent_residuals: Residuals from recent predictions
        threshold: Z-score threshold for drift
    
    Returns:
        Concept drift analysis
    """
    hist = np.array(historical_residuals)
    rec = np.array(recent_residuals)
    
    hist_mean = np.mean(hist)
    hist_std = np.std(hist)
    
    if hist_std == 0:
        hist_std = 1e-6
    
    # Z-score of recent residuals
    z_scores = (rec - hist_mean) / hist_std
    max_z = np.max(np.abs(z_scores))
    
    # CUSUM test
    cusum_pos = np.zeros(len(rec))
    cusum_neg = np.zeros(len(rec))
    k = 0.5 * hist_std  # Reference value
    
    for i in range(1, len(rec)):
        cusum_pos[i] = max(0, cusum_pos[i-1] + (rec[i] - hist_mean) - k)
        cusum_neg[i] = max(0, cusum_neg[i-1] - (rec[i] - hist_mean) - k)
    
    cusum_alarm = np.any(cusum_pos > 5 * hist_std) or np.any(cusum_neg > 5 * hist_std)
    
    # Mean shift test
    recent_mean = np.mean(rec)
    mean_shift_z = (recent_mean - hist_mean) / (hist_std / np.sqrt(len(rec)))
    
    return {
        "concept_drift_detected": bool(max_z > threshold or cusum_alarm or abs(mean_shift_z) > threshold),
        "max_z_score": float(max_z),
        "cusum_alarm": bool(cusum_alarm),
        "mean_shift_z": float(mean_shift_z),
        "historical_residual_mean": float(hist_mean),
        "recent_residual_mean": float(recent_mean),
        "residual_variance_change": float(np.var(rec) / np.var(hist)) if np.var(hist) > 0 else 1.0,
        "recommended_action": (
            "Retrain model immediately - significant concept drift detected"
            if max_z > 3 * threshold
            else "Investigate recent changes and consider retraining"
            if max_z > threshold
            else "Continue monitoring"
        ),
    }


@tool
def track_accuracy_trend(
    accuracy_history: list[dict],
    window_size: int = 7
) -> dict:
    """
    Track accuracy metrics over time to identify trends.
    
    Args:
        accuracy_history: List of {date, mape, rmse, ...} dicts
        window_size: Rolling window size for trend detection
    
    Returns:
        Accuracy trend analysis
    """
    if len(accuracy_history) < window_size:
        return {"trend": "insufficient_data", "message": "Need more data points"}
    
    df = pd.DataFrame(accuracy_history)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    # Rolling averages
    df["mape_ma"] = df["mape"].rolling(window=window_size).mean()
    df["rmse_ma"] = df["rmse"].rolling(window=window_size).mean()
    
    # Linear trend on rolling averages
    recent = df.dropna(subset=["mape_ma"])
    if len(recent) < 3:
        return {"trend": "insufficient_data"}
    
    x = np.arange(len(recent))
    mape_slope, _, mape_r, mape_p, _ = stats.linregress(x, recent["mape_ma"])
    
    # Determine trend
    if mape_p < 0.05:
        if mape_slope > 0.5:
            trend = "degrading"
        elif mape_slope < -0.5:
            trend = "improving"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    # Volatility analysis
    mape_volatility = float(recent["mape"].std())
    
    return {
        "trend": trend,
        "mape_slope": float(mape_slope),
        "mape_p_value": float(mape_p),
        "mape_volatility": mape_volatility,
        "current_mape": float(recent["mape"].iloc[-1]),
        "best_mape": float(recent["mape"].min()),
        "worst_mape": float(recent["mape"].max()),
        "days_since_best": int((recent["date"].iloc[-1] - recent.loc[recent["mape"].idxmin(), "date"]).days),
    }


@tool
def evaluate_feature_importance_shift(
    baseline_importance: dict[str, float],
    current_importance: dict[str, float]
) -> dict:
    """
    Compare feature importance between training and current production 
    to detect feature drift.
    
    Args:
        baseline_importance: Feature importance at training time
        current_importance: Current feature importance
    
    Returns:
        Feature importance shift analysis
    """
    all_features = set(baseline_importance.keys()) | set(current_importance.keys())
    
    shifts = {}
    for feature in all_features:
        base = baseline_importance.get(feature, 0.0)
        curr = current_importance.get(feature, 0.0)
        change = curr - base
        pct_change = (change / base * 100) if base > 0 else (100.0 if curr > 0 else 0.0)
        
        shifts[feature] = {
            "baseline": base,
            "current": curr,
            "absolute_change": change,
            "pct_change": pct_change,
            "significant_shift": abs(pct_change) > 50,
        }
    
    # Identify features with significant shifts
    significant_shifts = {
        f: s for f, s in shifts.items() if s["significant_shift"]
    }
    
    return {
        "feature_shifts": shifts,
        "significant_shifts": significant_shifts,
        "n_significant_shifts": len(significant_shifts),
        "retrain_recommended": len(significant_shifts) > len(all_features) * 0.2,
    }


@tool
def generate_retrain_recommendation(
    accuracy_metrics: dict,
    drift_report: dict,
    concept_drift: dict,
    accuracy_trend: dict,
    model_age_days: int
) -> dict:
    """
    Generate a comprehensive retraining recommendation based on 
    all performance signals.
    
    Args:
        accuracy_metrics: Current accuracy metrics
        drift_report: Data drift analysis
        concept_drift: Concept drift analysis
        accuracy_trend: Accuracy trend analysis
        model_age_days: Days since last training
    
    Returns:
        Retraining recommendation with urgency and rationale
    """
    score = 0.0
    reasons = []
    
    # Accuracy-based scoring
    if accuracy_metrics.get("mape", 0) > 20:
        score += 3.0
        reasons.append(f"MAPE ({accuracy_metrics['mape']:.1f}%) exceeds 20% threshold")
    elif accuracy_metrics.get("mape", 0) > 15:
        score += 1.5
        reasons.append(f"MAPE ({accuracy_metrics['mape']:.1f}%) exceeds 15% threshold")
    
    if accuracy_metrics.get("coverage", 100) < 80:
        score += 2.0
        reasons.append(f"Confidence interval coverage ({accuracy_metrics['coverage']:.1f}%) below 80%")
    
    if accuracy_metrics.get("forecast_value_added", 0) < 0:
        score += 2.5
        reasons.append("Model underperforms naive baseline (negative FVA)")
    
    # Drift-based scoring
    if drift_report.get("drift_detected"):
        severity = drift_report.get("severity", "low")
        if severity == "critical":
            score += 3.0
        elif severity == "high":
            score += 2.0
        elif severity == "medium":
            score += 1.0
        reasons.append(f"Data drift detected (PSI: {drift_report.get('drift_score', 0):.3f})")
    
    if concept_drift.get("concept_drift_detected"):
        score += 2.5
        reasons.append("Concept drift detected in residual patterns")
    
    # Trend-based scoring
    if accuracy_trend.get("trend") == "degrading":
        score += 1.5
        reasons.append("Accuracy trend is degrading")
    
    # Age-based scoring
    if model_age_days > 90:
        score += 1.0
        reasons.append(f"Model is {model_age_days} days old (>90 days)")
    elif model_age_days > 60:
        score += 0.5
        reasons.append(f"Model is {model_age_days} days old (>60 days)")
    
    # Determine urgency
    if score >= 6.0:
        urgency = "high"
        action = "Retrain immediately"
    elif score >= 4.0:
        urgency = "medium"
        action = "Schedule retraining within 1 week"
    elif score >= 2.0:
        urgency = "low"
        action = "Include in next scheduled retraining cycle"
    else:
        urgency = "none"
        action = "No retraining needed"
    
    return {
        "retrain_recommended": score >= 2.0,
        "urgency": urgency,
        "recommended_action": action,
        "priority_score": score,
        "reasons": reasons,
        "model_age_days": model_age_days,
        "next_evaluation": (datetime.now() + timedelta(days=7 if urgency == "high" else 14)).isoformat(),
    }


# ─── Agent Definition ──────────────────────────────────────────────

PERFORMANCE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are the Performance Analytics Agent for the sales forecasting system.
    
Your responsibilities:
1. Monitor forecast accuracy against actual results
2. Detect data drift, concept drift, and model degradation
3. Track accuracy trends over time
4. Generate retraining recommendations
5. Produce performance dashboards and reports

Guidelines:
- Always compare against multiple baselines (naive, seasonal naive, previous model)
- Consider both short-term and long-term accuracy trends
- Distinguish between random variation and systematic degradation
- Provide actionable recommendations, not just metrics
- Alert stakeholders when performance drops below acceptable thresholds

Model info: {model_info}
Recent predictions: {recent_predictions}
Actual results: {actual_results}
Historical performance: {historical_performance}
"""),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
    ("human", "Evaluate forecasting performance and generate a health report with recommendations."),
])


def create_performance_analytics_agent(llm: ChatOpenAI | None = None) -> AgentExecutor:
    """Factory function to create the Performance Analytics Agent."""
    llm = llm or ChatOpenAI(model="gpt-4", temperature=0)
    
    tools = [
        compute_forecast_accuracy,
        detect_data_drift,
        detect_concept_drift,
        track_accuracy_trend,
        evaluate_feature_importance_shift,
        generate_retrain_recommendation,
    ]
    
    agent = create_openai_functions_agent(llm, tools, PERFORMANCE_PROMPT)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=20,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )
```

### 6.4 Monitoring Dashboard Schema

```python
class MonitoringDashboard:
    """Real-time monitoring dashboard data schema."""
    
    @staticmethod
    def get_dashboard_data(
        model_id: str,
        time_range: tuple[str, str]
    ) -> dict:
        """Aggregate all monitoring data for dashboard display."""
        return {
            "model_info": {
                "model_id": model_id,
                "model_type": "ensemble",
                "last_trained": "2026-09-15T10:00:00Z",
                "version": "2.3.1",
                "status": "active",
            },
            "accuracy_summary": {
                "current_mape": 12.3,
                "target_mape": 15.0,
                "trend": "stable",
                "vs_last_week": -0.5,
                "vs_last_month": -1.2,
            },
            "drift_status": {
                "data_drift": {"detected": False, "psi": 0.08},
                "concept_drift": {"detected": False, "max_z": 1.2},
                "feature_drift": {"detected": False, "n_affected": 0},
            },
            "forecast_volume": {
                "predictions_last_24h": 15420,
                "predictions_last_7d": 105840,
                "avg_confidence": 0.87,
            },
            "alerts": [
                {
                    "timestamp": "2026-10-01T08:30:00Z",
                    "severity": "warning",
                    "message": "MAPE increased by 2% in product category Electronics",
                    "acknowledged": False,
                }
            ],
            "retrain_status": {
                "retrain_recommended": False,
                "last_retrain": "2026-09-15",
                "next_scheduled": "2026-10-15",
                "urgency": "none",
            },
        }
```

---

## 7. Code Examples and Snippets

### 7.1 Complete Pipeline Orchestration

```python
"""
Complete sales forecasting pipeline using LangChain DeepAgents.
This example demonstrates the full end-to-end workflow.
"""

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
import uuid
from datetime import datetime


# ─── State Definition ──────────────────────────────────────────────

class SalesForecastingState(TypedDict):
    """Shared state across the entire forecasting pipeline."""
    
    # Configuration
    correlation_id: str
    forecast_horizon: int
    target_variable: str
    product_filters: list[str]
    region_filters: list[str]
    
    # Data Collection outputs
    raw_data: dict
    data_quality_score: float
    collection_errors: list[str]
    
    # Analysis outputs
    analysis_report: dict
    trend_direction: str
    seasonality_detected: bool
    anomalies: list[dict]
    
    # Prediction outputs
    forecast_result: dict
    model_performance: dict
    confidence_level: float
    
    # Action outputs
    action_items: list[dict]
    alerts: list[dict]
    
    # Performance outputs
    accuracy_metrics: dict
    drift_detected: bool
    retrain_recommended: bool
    
    # Pipeline metadata
    pipeline_start_time: str
    pipeline_end_time: str
    errors: Annotated[list[str], operator.add]


# ─── Pipeline Nodes ────────────────────────────────────────────────

def data_collection_node(state: SalesForecastingState) -> SalesForecastingState:
    """Node 1: Data Collection Agent execution."""
    from implementations.sales_forecasting_impl import create_data_collection_agent
    
    agent = create_data_collection_agent()
    
    result = agent.invoke({
        "input": f"Collect sales data for horizon={state['forecast_horizon']} days, "
                 f"products={state['product_filters']}, regions={state['region_filters']}",
        "time_period": f"last 2 years",
        "product_filters": state["product_filters"],
        "region_filters": state["region_filters"],
    })
    
    # Parse agent output into structured data
    collected_data = result.get("output", {})
    
    return {
        **state,
        "raw_data": collected_data.get("dataset", {}),
        "data_quality_score": collected_data.get("quality_score", 0.0),
        "collection_errors": collected_data.get("errors", []),
    }


def analysis_node(state: SalesForecastingState) -> SalesForecastingState:
    """Node 2: Analysis Agent execution."""
    from implementations.sales_forecasting_impl import create_analysis_agent
    
    if state["data_quality_score"] < 0.5:
        return {
            **state,
            "errors": [f"Data quality too low: {state['data_quality_score']:.2f}"],
        }
    
    agent = create_analysis_agent()
    
    result = agent.invoke({
        "input": "Analyze the collected sales data",
        "dataset_shape": str(state["raw_data"].get("shape", "unknown")),
        "date_range": state["raw_data"].get("date_range", "unknown"),
        "target_variable": state["target_variable"],
    })
    
    analysis_output = result.get("output", {})
    
    return {
        **state,
        "analysis_report": analysis_output,
        "trend_direction": analysis_output.get("trend", {}).get("direction", "unknown"),
        "seasonality_detected": analysis_output.get("seasonality", {}).get("has_seasonality", False),
        "anomalies": analysis_output.get("anomalies", {}).get("anomalies", []),
    }


def prediction_node(state: SalesForecastingState) -> SalesForecastingState:
    """Node 3: Prediction Agent execution."""
    from implementations.sales_forecasting_impl import create_prediction_agent
    
    agent = create_prediction_agent()
    
    result = agent.invoke({
        "input": f"Generate {state['forecast_horizon']}-day forecast",
        "analysis_summary": str(state["analysis_report"]),
        "n_historical_points": state["raw_data"].get("row_count", 0),
        "horizon": state["forecast_horizon"],
        "target_variable": state["target_variable"],
        "seasonality_info": state["seasonality_detected"],
        "trend_direction": state["trend_direction"],
    })
    
    forecast_output = result.get("output", {})
    
    return {
        **state,
        "forecast_result": forecast_output,
        "model_performance": forecast_output.get("model_performance", {}),
        "confidence_level": 0.95,
    }


def action_node(state: SalesForecastingState) -> SalesForecastingState:
    """Node 4: Action Agent execution."""
    from implementations.sales_forecasting_impl import create_action_agent
    
    agent = create_action_agent()
    
    result = agent.invoke({
        "input": "Generate actionable recommendations from the forecast",
        "forecast_summary": str(state["forecast_result"]),
        "business_rules": {"min_margin": 0.15, "max_inventory_days": 60},
        "inventory_summary": {"total_skus": 150, "low_stock_items": 12},
        "budget_constraints": {"total_budget": 500000, "remaining": 125000},
    })
    
    action_output = result.get("output", {})
    
    return {
        **state,
        "action_items": action_output.get("actions", []),
        "alerts": action_output.get("alerts", []),
    }


def performance_node(state: SalesForecastingState) -> SalesForecastingState:
    """Node 5: Performance Analytics Agent execution."""
    from implementations.sales_forecasting_impl import create_performance_analytics_agent
    
    agent = create_performance_analytics_agent()
    
    result = agent.invoke({
        "input": "Evaluate forecast performance and generate health report",
        "model_info": {"model_id": "sf_ensemble_v2", "type": "ensemble"},
        "recent_predictions": state["forecast_result"].get("forecast_points", []),
        "actual_results": state["raw_data"].get("actuals", []),
        "historical_performance": {"mape_history": [12.1, 11.8, 12.5, 13.0, 12.3]},
    })
    
    performance_output = result.get("output", {})
    
    return {
        **state,
        "accuracy_metrics": performance_output.get("accuracy_metrics", {}),
        "drift_detected": performance_output.get("drift", {}).get("drift_detected", False),
        "retrain_recommended": performance_output.get("retrain_recommended", False),
        "pipeline_end_time": datetime.now().isoformat(),
    }


# ─── Pipeline Construction ─────────────────────────────────────────

def build_forecasting_pipeline() -> StateGraph:
    """Build the complete forecasting pipeline as a LangGraph state machine."""
    
    workflow = StateGraph(SalesForecastingState)
    
    # Add nodes
    workflow.add_node("data_collection", data_collection_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("prediction", prediction_node)
    workflow.add_node("action", action_node)
    workflow.add_node("performance", performance_node)
    
    # Define edges (sequential pipeline)
    workflow.set_entry_point("data_collection")
    workflow.add_edge("data_collection", "analysis")
    workflow.add_edge("analysis", "prediction")
    workflow.add_edge("prediction", "action")
    workflow.add_edge("action", "performance")
    workflow.add_edge("performance", END)
    
    return workflow.compile()


# ─── Execution ─────────────────────────────────────────────────────

def run_forecasting_pipeline(
    horizon: int = 30,
    target: str = "revenue",
    products: list[str] | None = None,
    regions: list[str] | None = None
) -> dict:
    """
    Execute the complete sales forecasting pipeline.
    
    Args:
        horizon: Number of days to forecast
        target: Target variable name
        products: Product filter list
        regions: Region filter list
    
    Returns:
        Complete pipeline results
    """
    pipeline = build_forecasting_pipeline()
    
    initial_state = {
        "correlation_id": str(uuid.uuid4()),
        "forecast_horizon": horizon,
        "target_variable": target,
        "product_filters": products or [],
        "region_filters": regions or [],
        "pipeline_start_time": datetime.now().isoformat(),
        "errors": [],
    }
    
    result = pipeline.invoke(initial_state)
    
    return {
        "correlation_id": result["correlation_id"],
        "forecast": result.get("forecast_result", {}),
        "actions": result.get("action_items", []),
        "alerts": result.get("alerts", []),
        "performance": result.get("accuracy_metrics", {}),
        "retrain_recommended": result.get("retrain_recommended", False),
        "errors": result.get("errors", []),
        "execution_time": (
            datetime.fromisoformat(result["pipeline_end_time"]) -
            datetime.fromisoformat(result["pipeline_start_time"])
        ).total_seconds() if result.get("pipeline_end_time") else None,
    }


if __name__ == "__main__":
    # Example execution
    results = run_forecasting_pipeline(
        horizon=30,
        target="revenue",
        products=["electronics", "apparel"],
        regions=["north_america", "europe"]
    )
    
    print(f"Pipeline completed in {results['execution_time']:.1f}s")
    print(f"Forecast confidence: {results['forecast'].get('confidence_level', 'N/A')}")
    print(f"Actions generated: {len(results['actions'])}")
    print(f"Alerts: {len(results['alerts'])}")
    print(f"Retrain recommended: {results['retrain_recommended']}")
```

### 7.2 FastAPI Service Endpoint

```python
"""
FastAPI service for the sales forecasting system.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(
    title="AI Sales Forecasting API",
    description="LangChain DeepAgents-powered sales forecasting",
    version="1.0.0",
)


class ForecastRequest(BaseModel):
    horizon: int = 30
    target_variable: str = "revenue"
    product_filters: list[str] = []
    region_filters: list[str] = []
    confidence_level: float = 0.95
    include_actions: bool = True
    include_alerts: bool = True


class ForecastResponse(BaseModel):
    correlation_id: str
    status: str
    forecast: dict
    actions: list[dict]
    alerts: list[dict]
    performance: dict
    execution_time_seconds: float


@app.post("/api/v1/forecast", response_model=ForecastResponse)
async def create_forecast(request: ForecastRequest):
    """
    Generate a sales forecast with actionable recommendations.
    """
    try:
        results = run_forecasting_pipeline(
            horizon=request.horizon,
            target=request.target_variable,
            products=request.product_filters,
            regions=request.region_filters,
        )
        
        return ForecastResponse(
            correlation_id=results["correlation_id"],
            status="success",
            forecast=results["forecast"],
            actions=results["actions"],
            alerts=results["alerts"],
            performance=results["performance"],
            execution_time_seconds=results["execution_time"] or 0.0,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents": {
            "data_collection": "available",
            "analysis": "available",
            "prediction": "available",
            "action": "available",
            "performance_analytics": "available",
        },
        "version": "1.0.0",
    }


@app.get("/api/v1/models")
async def list_models():
    """List available forecasting models and their status."""
    return {
        "models": [
            {
                "id": "prophet",
                "name": "Facebook Prophet",
                "status": "active",
                "last_trained": "2026-09-15T10:00:00Z",
                "mape": 11.2,
            },
            {
                "id": "arima",
                "name": "SARIMA",
                "status": "active",
                "last_trained": "2026-09-15T10:00:00Z",
                "mape": 13.5,
            },
            {
                "id": "xgboost",
                "name": "XGBoost",
                "status": "active",
                "last_trained": "2026-09-15T10:00:00Z",
                "mape": 10.8,
            },
            {
                "id": "ensemble",
                "name": "Ensemble (Weighted)",
                "status": "active",
                "last_trained": "2026-09-15T10:00:00Z",
                "mape": 9.5,
            },
        ]
    }
```

### 7.3 Docker Deployment

```dockerfile
# Dockerfile for Sales Forecasting Service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```yaml
# docker-compose.yml
version: "3.8"

services:
  forecasting-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      - redis
      - postgres
      - mlflow
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=forecasting
      - POSTGRES_USER=forecasting
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  mlflow:
    image: mlflow/mlflow:latest
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://forecasting:${DB_PASSWORD}@postgres:5432/forecasting
      - MLFLOW_DEFAULT_ARTIFACT_ROOT=/mlflow/artifacts
    volumes:
      - mlflow_data:/mlflow

  celery-worker:
    build: .
    command: celery -A tasks worker --loglevel=info --concurrency=4
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres

volumes:
  postgres_data:
  mlflow_data:
```

### 7.4 Requirements File

```text
# requirements.txt
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.10
langgraph>=0.2.0
openai>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
scikit-learn>=1.3.0
xgboost>=2.0.0
lightgbm>=4.0.0
prophet>=1.1.0
statsmodels>=0.14.0
pmdarima>=2.0.0
fastapi>=0.100.0
uvicorn>=0.23.0
celery>=5.3.0
redis>=5.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
mlflow>=2.8.0
langsmith>=0.0.80
pydantic>=2.0.0
python-dotenv>=1.0.0
httpx>=0.25.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

---

## 8. Testing Strategy

### 8.1 Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  ← Full pipeline integration tests
                    │  Tests  │     (5-10 tests, slow)
                   �┴─────────┴┐
                   │ Integration│ ← Agent interaction tests
                   │   Tests    │    (20-30 tests, medium)
                  �┴────────────┴┐
                  │    Unit       │ ← Individual tool/function tests
                  │    Tests      │    (100+ tests, fast)
                 �┴──────────────┴┐
                 │  Property-Based │ ← Hypothesis-generated edge cases
                 │     Tests       │    (50+ tests, fast)
                ┴─────────────────┴
```

### 8.2 Unit Tests

```python
"""
Unit tests for the sales forecasting system.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


# ─── Data Collection Agent Tests ───────────────────────────────────

class TestDataCollectionAgent:
    """Tests for the Data Collection Agent."""
    
    def test_validate_data_quality_complete_data(self):
        """Test quality validation with complete, clean data."""
        dataset = {
            "data": [
                {"revenue": 1000, "units": 10, "date": "2026-01-01"},
                {"revenue": 2000, "units": 20, "date": "2026-01-02"},
                {"revenue": 1500, "units": 15, "date": "2026-01-03"},
            ]
        }
        
        result = validate_data_quality.invoke({"dataset": dataset})
        
        assert result["completeness_score"] == 1.0
        assert result["overall_score"] > 0.9
        assert len(result["issues"]) == 0
    
    def test_validate_data_quality_with_missing_values(self):
        """Test quality validation with missing values."""
        dataset = {
            "data": [
                {"revenue": 1000, "units": 10},
                {"revenue": None, "units": 20},
                {"revenue": 1500, "units": None},
            ]
        }
        
        result = validate_data_quality.invoke({"dataset": dataset})
        
        assert result["completeness_score"] < 1.0
        assert len(result["issues"]) > 0
        assert any(issue["type"] == "completeness" for issue in result["issues"])
    
    def test_validate_data_quality_with_duplicates(self):
        """Test quality validation detects duplicate records."""
        dataset = {
            "data": [
                {"revenue": 1000, "units": 10, "date": "2026-01-01"},
                {"revenue": 1000, "units": 10, "date": "2026-01-01"},
                {"revenue": 2000, "units": 20, "date": "2026-01-02"},
            ]
        }
        
        result = validate_data_quality.invoke({"dataset": dataset})
        
        assert result["uniqueness_score"] < 1.0
    
    def test_merge_datasets_success(self):
        """Test successful dataset merging."""
        ds1 = {"data": [{"id": 1, "revenue": 100}, {"id": 2, "revenue": 200}]}
        ds2 = {"data": [{"id": 1, "units": 10}, {"id": 2, "units": 20}]}
        
        result = merge_datasets.invoke({
            "datasets": [ds1, ds2],
            "join_keys": ["id"]
        })
        
        assert result["merge_metadata"]["total_rows"] == 2
        assert result["merge_metadata"]["total_columns"] == 3
    
    def test_merge_datasets_failure(self):
        """Test dataset merge with incompatible keys."""
        ds1 = {"data": [{"id": 1, "revenue": 100}]}
        ds2 = {"data": [{"different_id": 1, "units": 10}]}
        
        result = merge_datasets.invoke({
            "datasets": [ds1, ds2],
            "join_keys": ["id"]
        })
        
        assert result["merge_metadata"]["merge_log"][0]["status"] == "failed"


# ─── Analysis Agent Tests ──────────────────────────────────────────

class TestAnalysisAgent:
    """Tests for the Analysis Agent."""
    
    def test_compute_descriptive_statistics(self):
        """Test descriptive statistics computation."""
        dataset = {
            "data": [
                {"revenue": 100, "units": 10},
                {"revenue": 200, "units": 20},
                {"revenue": 300, "units": 30},
                {"revenue": 400, "units": 40},
                {"revenue": 500, "units": 50},
            ]
        }
        
        result = compute_descriptive_statistics.invoke({"dataset": dataset})
        
        assert "revenue" in result
        assert result["revenue"]["mean"] == 300.0
        assert result["revenue"]["median"] == 300.0
        assert result["revenue"]["min"] == 100.0
        assert result["revenue"]["max"] == 500.0
    
    def test_analyze_trend_increasing(self):
        """Test trend detection with clearly increasing data."""
        time_series = [100, 110, 120, 130, 140, 150, 160, 170, 180, 190]
        dates = [(datetime(2026, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") 
                 for i in range(len(time_series))]
        
        result = analyze_trend.invoke({
            "time_series": time_series,
            "dates": dates,
            "test_type": "auto"
        })
        
        assert result["direction"] == "increasing"
        assert result["significance"] is True
        assert result["r_squared"] > 0.9
    
    def test_analyze_trend_decreasing(self):
        """Test trend detection with clearly decreasing data."""
        time_series = [200, 190, 180, 170, 160, 150, 140, 130, 120, 110]
        dates = [(datetime(2026, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") 
                 for i in range(len(time_series))]
        
        result = analyze_trend.invoke({
            "time_series": time_series,
            "dates": dates,
            "test_type": "auto"
        })
        
        assert result["direction"] == "decreasing"
        assert result["significance"] is True
    
    def test_analyze_trend_stable(self):
        """Test trend detection with stable data."""
        np.random.seed(42)
        time_series = list(np.random.normal(100, 5, 20))
        dates = [(datetime(2026, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") 
                 for i in range(len(time_series))]
        
        result = analyze_trend.invoke({
            "time_series": time_series,
            "dates": dates,
            "test_type": "auto"
        })
        
        assert result["direction"] == "stable"
    
    def test_detect_seasonality_weekly(self):
        """Test seasonality detection with weekly pattern."""
        # Create data with weekly seasonality
        base = 100
        weekly_pattern = [1.2, 1.1, 1.0, 0.9, 0.8, 1.3, 1.4]  # Weekend spike
        time_series = []
        for week in range(8):
            for day in range(7):
                time_series.append(base * weekly_pattern[day] + np.random.normal(0, 2))
        
        dates = [(datetime(2026, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") 
                 for i in range(len(time_series))]
        
        result = detect_seasonality.invoke({
            "time_series": time_series,
            "dates": dates
        })
        
        assert result["has_seasonality"] is True
        assert 7 in result["periods"]
        assert result["strength"] > 0.3
    
    def test_detect_anomalies_isolation_forest(self):
        """Test anomaly detection with isolation forest."""
        np.random.seed(42)
        normal_data = list(np.random.normal(100, 10, 50))
        # Inject anomalies
        normal_data[10] = 200
        normal_data[25] = 10
        normal_data[40] = 250
        
        dataset = {"data": [{"value": v} for v in normal_data]}
        
        result = detect_anomalies.invoke({
            "dataset": dataset,
            "columns": ["value"],
            "method": "isolation_forest",
            "contamination": 0.05
        })
        
        assert result["total_anomalies"] >= 2
        assert result["method_used"] == "isolation_forest"
    
    def test_detect_anomalies_zscore(self):
        """Test anomaly detection with Z-score method."""
        np.random.seed(42)
        normal_data = list(np.random.normal(100, 10, 100))
        normal_data[50] = 200  # Clear outlier
        
        dataset = {"data": [{"value": v} for v in normal_data]}
        
        result = detect_anomalies.invoke({
            "dataset": dataset,
            "columns": ["value"],
            "method": "zscore"
        })
        
        assert result["total_anomalies"] >= 1
    
    def test_compute_correlations(self):
        """Test correlation computation."""
        dataset = {
            "data": [
                {"revenue": 100, "units": 10, "price": 10},
                {"revenue": 200, "units": 20, "price": 10},
                {"revenue": 300, "units": 30, "price": 10},
                {"revenue": 400, "units": 40, "price": 10},
            ]
        }
        
        result = compute_correlations.invoke({
            "dataset": dataset,
            "target_column": "revenue",
            "method": "pearson"
        })
        
        assert "units" in result["feature_target_correlations"]
        assert result["feature_target_correlations"]["units"] > 0.99


# ─── Prediction Agent Tests ────────────────────────────────────────

class TestPredictionAgent:
    """Tests for the Prediction Agent."""
    
    def test_train_prophet_model(self):
        """Test Prophet model training."""
        np.random.seed(42)
        dates = pd.date_range("2025-01-01", periods=365, freq="D")
        trend = np.linspace(100, 200, 365)
        seasonal = 20 * np.sin(2 * np.pi * np.arange(365) / 7)
        noise = np.random.normal(0, 5, 365)
        values = trend + seasonal + noise
        
        result = train_prophet_model.invoke({
            "time_series": values.tolist(),
            "dates": dates.strftime("%Y-%m-%d").tolist(),
            "seasonality_mode": "additive",
        })
        
        assert result["model_type"] == "prophet"
        assert result["training_samples"] == 365
    
    def test_train_arima_model(self):
        """Test ARIMA model training."""
        np.random.seed(42)
        values = list(np.cumsum(np.random.normal(0, 1, 100)) + 100)
        
        result = train_arima_model.invoke({
            "time_series": values,
            "order": (1, 1, 1),
            "auto_select": False,
        })
        
        assert result["model_type"] == "arima"
        assert "aic" in result
        assert "bic" in result
    
    def test_train_xgboost_forecast(self):
        """Test XGBoost model training."""
        np.random.seed(42)
        n_samples = 200
        
        features = []
        target = []
        for i in range(n_samples):
            feat = {
                "month": (i % 12) + 1,
                "dayofweek": i % 7,
                "lag_1": 100 + i * 0.5 + np.random.normal(0, 5),
                "rolling_mean_7": 100 + i * 0.5,
            }
            features.append(feat)
            target.append(100 + i * 0.5 + np.random.normal(0, 5))
        
        result = train_xgboost_forecast.invoke({
            "features": features,
            "target": target,
        })
        
        assert result["model_type"] == "xgboost"
        assert "cv_mape_mean" in result
        assert "feature_importance" in result
    
    def test_ensemble_forecasts(self):
        """Test ensemble forecast combination."""
        forecast1 = {
            "predicted": [100, 110, 120, 130, 140],
            "lower_bound": [90, 100, 110, 120, 130],
            "upper_bound": [110, 120, 130, 140, 150],
        }
        forecast2 = {
            "predicted": [105, 115, 125, 135, 145],
            "lower_bound": [95, 105, 115, 125, 135],
            "upper_bound": [115, 125, 135, 145, 155],
        }
        
        result = ensemble_forecasts.invoke({
            "forecasts": [forecast1, forecast2],
            "weights": [0.6, 0.4],
            "method": "weighted_average"
        })
        
        assert len(result["predicted"]) == 5
        assert result["n_models"] == 2
        # Weighted average: 0.6*100 + 0.4*105 = 102
        assert abs(result["predicted"][0] - 102.0) < 0.1
    
    def test_evaluate_model_performance(self):
        """Test model performance evaluation."""
        actual = [100, 200, 300, 400, 500]
        predicted = [105, 195, 310, 390, 510]
        
        result = evaluate_model_performance.invoke({
            "actual": actual,
            "predicted": predicted
        })
        
        assert result["mape"] < 10.0
        assert result["rmse"] > 0
        assert result["mae"] > 0
        assert result["r_squared"] > 0.9


# ─── Action Agent Tests ────────────────────────────────────────────

class TestActionAgent:
    """Tests for the Action Agent."""
    
    def test_generate_inventory_recommendations_reorder(self):
        """Test inventory recommendation for reorder scenario."""
        forecast = {
            "by_product": {"PROD-001": 500},
            "confidence": 0.85,
        }
        current_inventory = {"PROD-001": 50}
        lead_times = {"PROD-001": 14}
        safety_stock_levels = {"PROD-001": 100}
        reorder_points = {"PROD-001": 150}
        
        result = generate_inventory_recommendations.invoke({
            "forecast": forecast,
            "current_inventory": current_inventory,
            "lead_times": lead_times,
            "safety_stock_levels": safety_stock_levels,
            "reorder_points": reorder_points,
        })
        
        assert len(result) > 0
        assert result[0]["category"] == "inventory"
        assert result[0]["priority"] in ("critical", "high")
    
    def test_generate_inventory_recommendations_overstock(self):
        """Test inventory recommendation for overstock scenario."""
        forecast = {
            "by_product": {"PROD-001": 100},
            "confidence": 0.85,
        }
        current_inventory = {"PROD-001": 500}
        lead_times = {"PROD-001": 7}
        safety_stock_levels = {"PROD-001": 50}
        reorder_points = {"PROD-001": 100}
        
        result = generate_inventory_recommendations.invoke({
            "forecast": forecast,
            "current_inventory": current_inventory,
            "lead_times": lead_times,
            "safety_stock_levels": safety_stock_levels,
            "reorder_points": reorder_points,
        })
        
        assert any("Excess" in r.get("title", "") for r in result)
    
    def test_generate_pricing_recommendations(self):
        """Test pricing recommendation generation."""
        forecast = {
            "by_product": {"PROD-001": 200},
            "historical_avg": {"PROD-001": 100},
            "confidence": 0.85,
        }
        current_prices = {"PROD-001": 50.0}
        competitor_prices = {"PROD-001": 55.0}
        price_elasticity = {"PROD-001": -1.5}
        
        result = generate_pricing_recommendations.invoke({
            "forecast": forecast,
            "current_prices": current_prices,
            "competitor_prices": competitor_prices,
            "price_elasticity": price_elasticity,
        })
        
        assert len(result) > 0
        assert result[0]["category"] == "pricing"
    
    def test_generate_alerts_demand_spike(self):
        """Test alert generation for demand spike."""
        forecast = {
            "by_product": {"PROD-001": 500},
            "historical_avg": {"PROD-001": 200},
        }
        actuals = {"PROD-001": 210}
        thresholds = {"deviation_pct": 0.25}
        
        result = generate_alerts.invoke({
            "forecast": forecast,
            "actuals": actuals,
            "thresholds": thresholds,
        })
        
        assert len(result) > 0
        assert any(a["alert_type"] == "demand_spike" for a in result)


# ─── Performance Analytics Agent Tests ─────────────────────────────

class TestPerformanceAnalyticsAgent:
    """Tests for the Performance Analytics Agent."""
    
    def test_compute_forecast_accuracy(self):
        """Test forecast accuracy computation."""
        actuals = [100, 200, 300, 400, 500]
        predictions = [105, 195, 310, 390, 510]
        confidence_intervals = [
            {"lower": 90, "upper": 110},
            {"lower": 180, "upper": 210},
            {"lower": 290, "upper": 320},
            {"lower": 380, "upper": 410},
            {"lower": 490, "upper": 520},
        ]
        
        result = compute_forecast_accuracy.invoke({
            "actuals": actuals,
            "predictions": predictions,
            "confidence_intervals": confidence_intervals,
        })
        
        assert result["mape"] < 10.0
        assert result["coverage"] == 100.0
        assert result["directional_accuracy"] == 100.0
    
    def test_detect_data_drift_no_drift(self):
        """Test drift detection with stable data."""
        np.random.seed(42)
        reference = [{"value": v} for v in np.random.normal(100, 10, 1000)]
        current = [{"value": v} for v in np.random.normal(100, 10, 100)]
        
        result = detect_data_drift.invoke({
            "reference_data": reference,
            "current_data": current,
            "threshold": 0.2,
        })
        
        assert result["drift_detected"] is False
        assert result["drift_score"] < 0.2
    
    def test_detect_data_drift_with_drift(self):
        """Test drift detection with shifted data."""
        np.random.seed(42)
        reference = [{"value": v} for v in np.random.normal(100, 10, 1000)]
        current = [{"value": v} for v in np.random.normal(150, 15, 100)]
        
        result = detect_data_drift.invoke({
            "reference_data": reference,
            "current_data": current,
            "threshold": 0.2,
        })
        
        assert result["drift_detected"] is True
        assert result["drift_score"] > 0.2
    
    def test_detect_concept_drift(self):
        """Test concept drift detection."""
        np.random.seed(42)
        historical_residuals = list(np.random.normal(0, 5, 200))
        recent_residuals = list(np.random.normal(20, 10, 20))  # Shifted mean
        
        result = detect_concept_drift.invoke({
            "historical_residuals": historical_residuals,
            "recent_residuals": recent_residuals,
        })
        
        assert result["concept_drift_detected"] is True
    
    def test_track_accuracy_trend_degrading(self):
        """Test accuracy trend detection with degrading performance."""
        accuracy_history = [
            {"date": (datetime(2026, 9, 1) + timedelta(days=i)).strftime("%Y-%m-%d"),
             "mape": 10 + i * 0.5, "rmse": 100 + i * 5}
            for i in range(30)
        ]
        
        result = track_accuracy_trend.invoke({
            "accuracy_history": accuracy_history,
            "window_size": 7,
        })
        
        assert result["trend"] == "degrading"
    
    def test_generate_retrain_recommendation_urgent(self):
        """Test retrain recommendation with poor performance."""
        accuracy_metrics = {"mape": 25.0, "coverage": 70, "forecast_value_added": -5}
        drift_report = {"drift_detected": True, "drift_score": 0.35, "severity": "critical"}
        concept_drift = {"concept_drift_detected": True}
        accuracy_trend = {"trend": "degrading"}
        
        result = generate_retrain_recommendation.invoke({
            "accuracy_metrics": accuracy_metrics,
            "drift_report": drift_report,
            "concept_drift": concept_drift,
            "accuracy_trend": accuracy_trend,
            "model_age_days": 120,
        })
        
        assert result["retrain_recommended"] is True
        assert result["urgency"] == "high"
    
    def test_generate_retrain_recommendation_healthy(self):
        """Test retrain recommendation with healthy model."""
        accuracy_metrics = {"mape": 8.0, "coverage": 92, "forecast_value_added": 15}
        drift_report = {"drift_detected": False, "drift_score": 0.05, "severity": "low"}
        concept_drift = {"concept_drift_detected": False}
        accuracy_trend = {"trend": "stable"}
        
        result = generate_retrain_recommendation.invoke({
            "accuracy_metrics": accuracy_metrics,
            "drift_report": drift_report,
            "concept_drift": concept_drift,
            "accuracy_trend": accuracy_trend,
            "model_age_days": 30,
        })
        
        assert result["retrain_recommended"] is False
        assert result["urgency"] == "none"


# ─── Integration Tests ─────────────────────────────────────────────

class TestForecastingPipeline:
    """Integration tests for the complete forecasting pipeline."""
    
    @pytest.fixture
    def sample_sales_data(self):
        """Generate sample sales data for testing."""
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=730, freq="D")
        trend = np.linspace(1000, 2000, 730)
        yearly_seasonal = 200 * np.sin(2 * np.pi * np.arange(730) / 365.25)
        weekly_seasonal = 100 * np.sin(2 * np.pi * np.arange(730) / 7)
        noise = np.random.normal(0, 50, 730)
        revenue = trend + yearly_seasonal + weekly_seasonal + noise
        
        return pd.DataFrame({
            "date": dates,
            "revenue": revenue,
            "units": (revenue / 50).astype(int),
            "product_id": np.random.choice(["PROD-001", "PROD-002", "PROD-003"], 730),
            "region": np.random.choice(["NA", "EU", "APAC"], 730),
        })
    
    def test_end_to_end_forecast_generation(self, sample_sales_data):
        """Test complete forecast generation pipeline."""
        # This would test the full pipeline with mocked LLM calls
        # In practice, use VCR.py or similar to record/replay LLM responses
        pass
    
    def test_pipeline_with_low_quality_data(self):
        """Test pipeline behavior with poor quality data."""
        # Pipeline should gracefully handle and report quality issues
        pass
    
    def test_pipeline_error_recovery(self):
        """Test pipeline recovery from individual agent failures."""
        # If one agent fails, pipeline should continue with degraded functionality
        pass


# ─── Property-Based Tests ──────────────────────────────────────────

from hypothesis import given, settings, strategies as st


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @given(
        st.lists(st.floats(min_value=0, max_value=10000, allow_nan=False), min_size=30, max_size=500),
        st.sampled_from(["pearson", "spearman"]),
    )
    @settings(max_examples=50)
    def test_correlation_properties(self, values, method):
        """Correlation should always be between -1 and 1."""
        dataset = {"data": [{"x": v, "y": v * 2} for v in values]}
        
        result = compute_correlations.invoke({
            "dataset": dataset,
            "target_column": "y",
            "method": method,
        })
        
        for feature, corr in result["feature_target_correlations"].items():
            assert -1.0 <= corr <= 1.0
    
    @given(
        st.lists(st.floats(min_value=-1000, max_value=1000, allow_nan=False), min_size=10, max_size=100),
    )
    @settings(max_examples=50)
    def test_forecast_accuracy_non_negative(self, values):
        """Accuracy metrics should always be non-negative."""
        actuals = [abs(v) for v in values]
        predictions = [abs(v) + 1 for v in values]
        
        result = evaluate_model_performance.invoke({
            "actual": actuals,
            "predicted": predictions,
        })
        
        assert result["mape"] >= 0
        assert result["rmse"] >= 0
        assert result["mae"] >= 0
    
    @given(
        st.lists(st.floats(min_value=0, max_value=1000, allow_nan=False), min_size=5, max_size=50),
        st.floats(min_value=0.01, max_value=0.5),
    )
    @settings(max_examples=30)
    def test_ensemble_within_bounds(self, values, weight):
        """Ensemble prediction should be within range of input forecasts."""
        forecast1 = {
            "predicted": values,
            "lower_bound": [v * 0.9 for v in values],
            "upper_bound": [v * 1.1 for v in values],
        }
        forecast2 = {
            "predicted": [v * 1.1 for v in values],
            "lower_bound": [v for v in values],
            "upper_bound": [v * 1.2 for v in values],
        }
        
        result = ensemble_forecasts.invoke({
            "forecasts": [forecast1, forecast2],
            "weights": [weight, 1 - weight],
        })
        
        for i, pred in enumerate(result["predicted"]):
            assert pred >= min(forecast1["predicted"][i], forecast2["predicted"][i]) * 0.5
            assert pred <= max(forecast1["predicted"][i], forecast2["predicted"][i]) * 1.5


# ─── Performance Tests ─────────────────────────────────────────────

class TestPerformance:
    """Performance and load tests."""
    
    @pytest.mark.slow
    def test_large_dataset_processing(self):
        """Test processing of large datasets (100K+ rows)."""
        np.random.seed(42)
        n_rows = 100_000
        dataset = {
            "data": [
                {
                    "revenue": float(np.random.normal(1000, 200)),
                    "units": int(np.random.poisson(20)),
                    "date": (datetime(2024, 1, 1) + timedelta(days=i % 730)).isoformat(),
                }
                for i in range(n_rows)
            ]
        }
        
        import time
        start = time.time()
        result = compute_descriptive_statistics.invoke({"dataset": dataset})
        elapsed = time.time() - start
        
        assert elapsed < 5.0  # Should complete in under 5 seconds
        assert "revenue" in result
    
    @pytest.mark.slow
    def test_forecast_generation_speed(self):
        """Test that forecast generation completes within acceptable time."""
        np.random.seed(42)
        values = list(np.cumsum(np.random.normal(0, 1, 365)) + 100)
        
        import time
        start = time.time()
        result = train_exponential_smoothing.invoke({
            "time_series": values,
            "trend": "add",
            "seasonal": "add",
            "seasonal_periods": 7,
        })
        elapsed = time.time() - start
        
        assert elapsed < 10.0
        assert result["model_type"] == "exponential_smoothing"


# ─── Test Configuration ────────────────────────────────────────────

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "property: marks tests as property-based tests")
```

### 8.3 Integration Tests

```python
"""
Integration tests for agent interactions and pipeline flow.
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage


class TestAgentInteractions:
    """Test interactions between agents in the pipeline."""
    
    def test_data_collection_to_analysis_handoff(self):
        """Test that data collection output is compatible with analysis input."""
        # Simulate data collection output
        collected_data = {
            "dataset": {
                "data": [
                    {"date": "2026-01-01", "revenue": 1000, "units": 10},
                    {"date": "2026-01-02", "revenue": 1100, "units": 11},
                ],
                "shape": (2, 3),
                "date_range": ("2026-01-01", "2026-01-02"),
            },
            "quality_score": 0.95,
            "errors": [],
        }
        
        # Verify analysis agent can consume this format
        result = compute_descriptive_statistics.invoke({
            "dataset": collected_data["dataset"]
        })
        
        assert "revenue" in result
        assert result["revenue"]["count"] == 2
    
    def test_analysis_to_prediction_handoff(self):
        """Test that analysis output is compatible with prediction input."""
        analysis_output = {
            "trend": {"direction": "increasing", "slope": 10.5, "significance": True},
            "seasonality": {"has_seasonality": True, "periods": [7], "strength": 0.6},
            "anomalies": {"total_anomalies": 0, "anomalies": []},
        }
        
        # Verify prediction agent can use this information
        assert analysis_output["trend"]["direction"] in ("increasing", "decreasing", "stable")
        assert isinstance(analysis_output["seasonality"]["has_seasonality"], bool)
    
    def test_prediction_to_action_handoff(self):
        """Test that prediction output is compatible with action input."""
        forecast_output = {
            "forecast_points": [
                {"date": "2026-10-01", "predicted_value": 1500, "lower_bound": 1300, "upper_bound": 1700},
                {"date": "2026-10-02", "predicted_value": 1600, "lower_bound": 1400, "upper_bound": 1800},
            ],
            "by_product": {"PROD-001": 500, "PROD-002": 300},
            "confidence": 0.85,
            "historical_avg": {"PROD-001": 400, "PROD-002": 350},
        }
        
        # Verify action agent can consume this
        result = generate_inventory_recommendations.invoke({
            "forecast": forecast_output,
            "current_inventory": {"PROD-001": 100, "PROD-002": 200},
            "lead_times": {"PROD-001": 7, "PROD-002": 14},
            "safety_stock_levels": {"PROD-001": 50, "PROD-002": 75},
            "reorder_points": {"PROD-001": 100, "PROD-002": 150},
        })
        
        assert isinstance(result, list)
    
    def test_performance_feedback_loop(self):
        """Test that performance analytics can trigger retraining."""
        # Simulate degrading performance
        accuracy_metrics = {"mape": 22.0, "coverage": 75, "forecast_value_added": -3}
        drift_report = {"drift_detected": True, "drift_score": 0.25, "severity": "high"}
        concept_drift = {"concept_drift_detected": True}
        accuracy_trend = {"trend": "degrading"}
        
        result = generate_retrain_recommendation.invoke({
            "accuracy_metrics": accuracy_metrics,
            "drift_report": drift_report,
            "concept_drift": concept_drift,
            "accuracy_trend": accuracy_trend,
            "model_age_days": 95,
        })
        
        assert result["retrain_recommended"] is True
        assert result["urgency"] in ("high", "medium")


class TestPipelineStateManagement:
    """Test pipeline state transitions and data flow."""
    
    def test_state_initialization(self):
        """Test pipeline state is correctly initialized."""
        initial_state = {
            "correlation_id": "test-123",
            "forecast_horizon": 30,
            "target_variable": "revenue",
            "product_filters": [],
            "region_filters": [],
            "pipeline_start_time": "2026-10-01T00:00:00",
            "errors": [],
        }
        
        assert initial_state["forecast_horizon"] == 30
        assert initial_state["errors"] == []
    
    def test_error_accumulation(self):
        """Test that errors are properly accumulated across nodes."""
        errors = []
        errors.append("Data source CRM unavailable")
        errors.append("Low confidence in forecast for PROD-003")
        
        assert len(errors) == 2
        assert "CRM" in errors[0]
    
    def test_quality_gate_blocks_pipeline(self):
        """Test that low quality data blocks pipeline progression."""
        quality_score = 0.3
        threshold = 0.5
        
        should_continue = quality_score >= threshold
        
        assert should_continue is False


# ─── Mock LLM Tests ────────────────────────────────────────────────

class TestWithMockedLLM:
    """Test agent behavior with mocked LLM responses."""
    
    @patch("langchain_openai.ChatOpenAI")
    def test_data_collection_agent_with_mock(self, mock_llm):
        """Test data collection agent with mocked LLM."""
        mock_instance = MagicMock()
        mock_llm.return_value = mock_instance
        
        # Mock the agent's response
        mock_instance.invoke.return_value = {
            "output": {
                "dataset": {"data": [{"revenue": 100}]},
                "quality_score": 0.9,
                "errors": [],
            }
        }
        
        # Agent should use the mocked LLM
        agent = create_data_collection_agent(llm=mock_instance)
        assert agent is not None
    
    @patch("langchain_openai.ChatOpenAI")
    def test_prediction_agent_model_selection(self, mock_llm):
        """Test that prediction agent selects appropriate models."""
        mock_instance = MagicMock()
        mock_llm.return_value = mock_instance
        
        agent = create_prediction_agent(llm=mock_instance)
        
        # Verify agent was created with correct tools
        assert agent is not None


# ─── API Tests ─────────────────────────────────────────────────────

class TestAPIEndpoints:
    """Test FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from main import app
        
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_forecast_endpoint_validation(self, client):
        """Test forecast endpoint input validation."""
        # Missing required fields should return 422
        response = client.post("/api/v1/forecast", json={})
        assert response.status_code == 422
    
    def test_forecast_endpoint_success(self, client):
        """Test successful forecast request."""
        # This would need mocking of the pipeline
        pass
    
    def test_models_endpoint(self, client):
        """Test models listing endpoint."""
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) > 0
```

### 8.4 Test Execution Plan

```bash
#!/bin/bash
# run_tests.sh - Test execution script

echo "=== Running Sales Forecasting Test Suite ==="

# 1. Unit tests (fast, always run)
echo "Running unit tests..."
pytest tests/unit/ -v --tb=short -m "not slow" --cov=src --cov-report=term-missing

# 2. Property-based tests
echo "Running property-based tests..."
pytest tests/property/ -v --tb=short --hypothesis-seed=42

# 3. Integration tests (medium speed)
echo "Running integration tests..."
pytest tests/integration/ -v --tb=short -m "integration"

# 4. Performance tests (slow, run on schedule)
if [ "$1" == "--full" ]; then
    echo "Running performance tests..."
    pytest tests/performance/ -v --tb=short -m "slow"
fi

# 5. Generate coverage report
echo "Generating coverage report..."
coverage html -d coverage_report/
coverage xml -o coverage.xml

echo "=== Test Suite Complete ==="
```

### 8.5 Test Data Management

```python
"""
Test data fixtures and factories for the sales forecasting system.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from factory import Factory, Faker, Sequence


class SalesDataFactory(Factory):
    """Factory for generating realistic sales test data."""
    
    class Meta:
        model = dict
    
    date = Faker("date_between", start_date="-2y", end_date="today")
    revenue = Faker("pyfloat", min_value=100, max_value=10000)
    units = Faker("pyint", min_value=1, max_value=100)
    product_id = Faker("random_element", elements=["PROD-001", "PROD-002", "PROD-003"])
    region = Faker("random_element", elements=["NA", "EU", "APAC"])
    channel = Faker("random_element", elements=["online", "retail", "wholesale"])


@pytest.fixture
def generate_sales_data():
    """Generate a configurable amount of sales test data."""
    def _generate(n_records=1000, start_date="2024-01-01", freq="D"):
        np.random.seed(42)
        dates = pd.date_range(start_date, periods=n_records, freq=freq)
        
        # Create realistic patterns
        trend = np.linspace(1000, 2000, n_records)
        yearly = 200 * np.sin(2 * np.pi * np.arange(n_records) / 365.25)
        weekly = 100 * np.sin(2 * np.pi * np.arange(n_records) / 7)
        noise = np.random.normal(0, 50, n_records)
        
        revenue = trend + yearly + weekly + noise
        
        return pd.DataFrame({
            "date": dates,
            "revenue": np.maximum(revenue, 0),
            "units": (revenue / 50).astype(int),
            "product_id": np.random.choice(["PROD-001", "PROD-002", "PROD-003"], n_records),
            "region": np.random.choice(["NA", "EU", "APAC"], n_records),
            "channel": np.random.choice(["online", "retail", "wholesale"], n_records),
        })
    
    return _generate


@pytest.fixture
def sample_time_series():
    """Generate a simple time series for model testing."""
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=365, freq="D")
    values = 100 + np.linspace(0, 100, 365) + 20 * np.sin(2 * np.pi * np.arange(365) / 7)
    values += np.random.normal(0, 5, 365)
    return values.tolist(), dates.strftime("%Y-%m-%d").tolist()


@pytest.fixture
def mock_forecast_result():
    """Generate a mock forecast result for testing."""
    return {
        "forecast_id": "test-forecast-001",
        "model_used": "ensemble",
        "ensemble_models": ["prophet", "xgboost"],
        "forecast_horizon": 30,
        "forecast_points": [
            {
                "date": (datetime(2026, 10, 1) + timedelta(days=i)).strftime("%Y-%m-%d"),
                "predicted_value": 1500 + i * 10,
                "lower_bound": 1300 + i * 10,
                "upper_bound": 1700 + i * 10,
                "confidence": 0.95 - i * 0.001,
            }
            for i in range(30)
        ],
        "model_performance": {
            "model_name": "ensemble",
            "mape": 9.5,
            "rmse": 150.0,
            "mae": 120.0,
            "r_squared": 0.92,
            "training_time_seconds": 45.2,
        },
        "confidence_level": 0.95,
    }
```

### 8.6 CI/CD Test Pipeline

```yaml
# .github/workflows/test.yml
name: Sales Forecasting Tests

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
          pip install -r requirements-test.txt
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=src --cov-report=xml -m "not slow"
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v --tb=short
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379

  property-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run property-based tests
        run: pytest tests/property/ -v --hypothesis-profile=ci

  performance-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run performance tests
        run: pytest tests/performance/ -v -m "slow" --timeout=300
```

---

## Appendix A: Configuration Reference

```yaml
# config.yaml - System configuration
forecasting:
  default_horizon: 30
  max_horizon: 365
  confidence_level: 0.95
  min_data_points: 30
  quality_threshold: 0.5
  
  models:
    prophet:
      enabled: true
      seasonality_mode: multiplicative
      changepoint_prior_scale: 0.05
    arima:
      enabled: true
      auto_select: true
      max_p: 5
      max_d: 2
      max_q: 5
    xgboost:
      enabled: true
      n_estimators: 500
      max_depth: 6
      learning_rate: 0.05
    exponential_smoothing:
      enabled: true
      damped_trend: true
  
  ensemble:
    method: weighted_average
    weights:
      prophet: 0.35
      xgboost: 0.35
      arima: 0.30

data_sources:
  crm:
    type: salesforce
    refresh_interval: 3600
    priority: 1
  erp:
    type: sap
    refresh_interval: 1800
    priority: 1
  ecommerce:
    type: shopify
    refresh_interval: 600
    priority: 1
  web_analytics:
    type: google_analytics
    refresh_interval: 86400
    priority: 2

monitoring:
  metrics_retention_days: 365
  alert_thresholds:
    mape: 15.0
    coverage: 85.0
    drift_psi: 0.2
  retrain:
    auto_retrain: false
    schedule: "0 2 * * 0"  # Weekly on Sunday at 2 AM
    min_model_age_days: 7

agents:
  llm_model: gpt-4
  temperature: 0
  max_iterations: 25
  timeout_seconds: 300
  retry_attempts: 3
  retry_delay_seconds: 5
```

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| **MAPE** | Mean Absolute Percentage Error — average percentage deviation of forecasts from actuals |
| **RMSE** | Root Mean Squared Error — square root of average squared forecast errors |
| **PSI** | Population Stability Index — measures distribution shift between two datasets |
| **FVA** | Forecast Value Added — improvement over a naive baseline forecast |
| **CUSUM** | Cumulative Sum control chart — detects small shifts in process mean |
| **RFM** | Recency, Frequency, Monetary — customer segmentation framework |
| **SARIMA** | Seasonal AutoRegressive Integrated Moving Average |
| **TBATS** | Trigonometric seasonality, Box-Cox transformation, ARMA errors, Trend, Seasonal components |
| **Croston's method** | Forecasting method for intermittent demand patterns |
| **Prophet** | Facebook's open-source forecasting tool for time series with strong seasonal effects |

---

*End of Implementation Plan*</longcat_think>
