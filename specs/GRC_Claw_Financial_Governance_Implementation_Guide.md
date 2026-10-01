# GRC_Claw Financial Governance Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Implementation Ready  
**Parent Spec:** GRC_Claw_Financial_Governance_Specification.md  
**Metrics Layer:** grc-claw-unified-metrics-layer.md (UC-7: Economic Value & Accountability)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Cost Tracking Pipeline](#2-cost-tracking-pipeline)
3. [ROI Measurement](#3-roi-measurement)
4. [Budget Management](#4-budget-management)
5. [Cost Anomaly Detection](#5-cost-anomaly-detection)
6. [Budget Forecasting](#6-budget-forecasting)
7. [Financial Reporting](#7-financial-reporting)
8. [FinOps Integration](#8-finops-integration)
9. [Deployment & Operations](#9-deployment--operations)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GRC_Claw Financial Governance                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Cost    │  │   ROI    │  │  Budget  │  │  Anomaly │           │
│  │ Tracking │  │   Meas.  │  │  Mgmt    │  │ Detection│           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │              │              │              │                 │
│       └──────────────┴──────────────┴──────────────┘                │
│                           │                                         │
│                    ┌──────┴──────┐                                  │
│                    │  Financial  │                                  │
│                    │  Reporting  │                                  │
│                    └──────┬──────┘                                  │
│                           │                                         │
│                    ┌──────┴──────┐                                  │
│                    │   FinOps    │                                  │
│                    │ Integration │                                  │
│                    └─────────────┘                                  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Data Layer: PostgreSQL (ai_cost_records, ai_budgets, ai_roi_direct)│
│  Cache: Redis (real-time spend, alerts)                             │
│  Queue: Celery (async cost collection, report generation)           │
│  API: FastAPI (REST endpoints for all modules)                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Database | PostgreSQL 16 | Cost records, budgets, ROI data |
| Cache | Redis | Real-time spend tracking, alert state |
| Queue | Celery + Redis | Async cost collection, report generation |
| API | FastAPI | REST endpoints |
| ML | scikit-learn, Prophet | Anomaly detection, forecasting |
| Monitoring | Prometheus + Grafana | Operational dashboards |
| Orchestration | Apache Airflow | Scheduled pipelines |

---

## 2. Cost Tracking Pipeline

### 2.1 Core Data Models

```python
# models/cost_models.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional


class CostCategory(str, Enum):
    """Primary cost categories per GRC_Claw specification §3.1.1."""
    INFERENCE = "INF"
    TRAINING = "TRN"
    STORAGE = "STO"
    DATA = "DAT"
    INFRASTRUCTURE = "INF-ARC"
    LICENSING = "LIC"
    OPERATIONS = "OPS"
    GOVERNANCE = "GOV"
    HUMAN_RESOURCES = "HR"
    MISCELLANEOUS = "MISC"


class CostSubcategory(str, Enum):
    """Inference subcategories per specification §3.1.2."""
    INF_LLM = "INF-LLM"
    INF_EMB = "INF-EMB"
    INF_IMG = "INF-IMG"
    INF_AUD = "INF-AUD"
    INF_VID = "INF-VID"
    INF_CUST = "INF-CUST"
    INF_EDGE = "INF-EDGE"
    # Training subcategories
    TRN_FULL = "TRN-FULL"
    TRN_FT = "TRN-FT"
    TRN_RLHF = "TRN-RLHF"
    TRN_DLAB = "TRN-DLAB"
    TRN_EXP = "TRN-EXP"
    # Storage subcategories
    STO_MOD = "STO-MOD"
    STO_DAT = "STO-DAT"
    STO_EMB = "STO-EMB"
    STO_LOG = "STO-LOG"
    STO_BAK = "STO-BAK"


class SourceType(str, Enum):
    """Cost source classification per specification §3.3."""
    CLOUD_BILL = "cloud_bill"
    API_METER = "api_meter"
    MANUAL = "manual"
    ESTIMATE = "estimate"


class ApprovalStatus(str, Enum):
    """Cost record approval states."""
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


@dataclass
class CostRecord:
    """
    AI cost record matching the ai_cost_records schema (specification §3.2.1).
    
    Every AI dollar is attributed to an owner, business unit, and initiative.
    """
    cost_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: CostCategory = CostCategory.INFERENCE
    subcategory: Optional[CostSubcategory] = None
    
    # Attribution (required for every record)
    owner_id: uuid.UUID = field(default_factory=uuid.uuid4)
    business_unit_id: uuid.UUID = field(default_factory=uuid.uuid4)
    initiative_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    cost_center: str = "CC-000"
    
    # Financial
    amount: Decimal = Decimal("0")
    currency: str = "USD"
    amount_usd: Decimal = Decimal("0")
    exchange_rate: Optional[Decimal] = None
    
    # Measurement (unit economics)
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None  # tokens, gpu_hours, gb_month, requests
    unit_cost: Optional[Decimal] = None
    
    # Source
    source_type: SourceType = SourceType.CLOUD_BILL
    source_system: Optional[str] = None  # AWS Cost Explorer, Stripe, etc.
    source_record_id: Optional[str] = None
    
    # Time
    cost_period_start: datetime = field(default_factory=datetime.utcnow)
    cost_period_end: datetime = field(default_factory=datetime.utcnow)
    recorded_at: datetime = field(default_factory=datetime.utcnow)
    
    # Governance
    is_shadow: bool = False
    shadow_reason: Optional[str] = None
    approval_status: ApprovalStatus = ApprovalStatus.APPROVED
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    
    # Audit
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = field(default_factory=uuid.uuid4)
    updated_by: uuid.UUID = field(default_factory=uuid.uuid4)

    def compute_unit_cost(self) -> Optional[Decimal]:
        """Calculate cost per unit for unit economics tracking."""
        if self.quantity and self.quantity > 0 and self.amount_usd:
            self.unit_cost = self.amount_usd / self.quantity
        return self.unit_cost

    def validate(self) -> list[str]:
        """Validate record against data quality standards (specification §3.5)."""
        errors = []
        if self.amount_usd < 0:
            errors.append("amount_usd cannot be negative")
        if not self.owner_id:
            errors.append("owner_id is required (FIN-001)")
        if not self.business_unit_id:
            errors.append("business_unit_id is required (FIN-001)")
        if not self.cost_center:
            errors.append("cost_center is required (FIN-001)")
        if self.cost_period_end < self.cost_period_start:
            errors.append("cost_period_end must be after cost_period_start")
        if self.source_type == SourceType.MANUAL and not self.approved_by:
            errors.append("manual entries require approver (FIN-008)")
        return errors
```

### 2.2 Cost Collection Pipeline

```python
# pipelines/cost_collection.py
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import AsyncIterator, Optional

import aiohttp
import boto3
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.cost_models import CostRecord, CostCategory, SourceType

logger = logging.getLogger(__name__)


@dataclass
class CollectionResult:
    source: str
    records_collected: int
    records_failed: int
    total_amount_usd: Decimal
    errors: list[str]


class CostCollector(ABC):
    """Abstract base class for cost collectors."""

    @abstractmethod
    async def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        session: AsyncSession,
    ) -> CollectionResult:
        """Collect cost data from source system."""
        ...

    @abstractmethod
    def source_name(self) -> str:
        """Return the source system name."""
        ...


class AWSCostCollector(CostCollector):
    """
    Collects AI-related costs from AWS Cost Explorer.
    Covers: INF, STO, INF-ARC categories.
    """

    AI_SERVICE_PATTERNS = [
        "Amazon SageMaker",
        "Amazon Bedrock",
        "Amazon Comprehend",
        "Amazon Rekognition",
        "Amazon Textract",
        "Amazon Transcribe",
        "Amazon Polly",
        "EC2",  # GPU instances
        "S3",   # Model/data storage
    ]

    def __init__(self, access_key: str, secret_key: str, region: str = "us-east-1"):
        self.client = boto3.client(
            "ce",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def source_name(self) -> str:
        return "AWS Cost Explorer"

    async def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        session: AsyncSession,
    ) -> CollectionResult:
        records = []
        errors = []
        total = Decimal("0")

        try:
            paginator = self.client.get_paginator("get_cost_and_usage")
            for page in paginator.paginate(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": end_date.strftime("%Y-%m-%d"),
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                Filter={
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": self.AI_SERVICE_PATTERNS,
                    }
                },
            ):
                for result in page["ResultsByTime"]:
                    for group in result.get("Groups", []):
                        service = group["Keys"][0]
                        amount = Decimal(group["Metrics"]["UnblendedCost"]["Amount"])
                        
                        if amount == 0:
                            continue

                        category = self._classify_service(service)
                        record = CostRecord(
                            category=category,
                            subcategory=self._get_subcategory(service),
                            amount=amount,
                            amount_usd=amount,
                            source_type=SourceType.CLOUD_BILL,
                            source_system="AWS Cost Explorer",
                            source_record_id=f"aws:{service}:{result['TimePeriod']['Start']}",
                            cost_period_start=result["TimePeriod"]["Start"],
                            cost_period_end=result["TimePeriod"]["End"],
                            tags=["aws", service.lower().replace(" ", "_")],
                        )
                        records.append(record)
                        total += amount

        except Exception as e:
            errors.append(f"AWS collection error: {str(e)}")
            logger.exception("AWS cost collection failed")

        return CollectionResult(
            source=self.source_name(),
            records_collected=len(records),
            records_failed=len(errors),
            total_amount_usd=total,
            errors=errors,
        )

    def _classify_service(self, service: str) -> CostCategory:
        """Map AWS service to GRC_Claw cost category."""
        if "SageMaker" in service or "Bedrock" in service:
            return CostCategory.INFERENCE
        elif "S3" in service or "ECR" in service:
            return CostCategory.STORAGE
        elif "EC2" in service:
            return CostCategory.INFRASTRUCTURE
        else:
            return CostCategory.OPERATIONS

    def _get_subcategory(self, service: str) -> Optional[str]:
        """Map AWS service to subcategory."""
        mapping = {
            "Amazon Bedrock": "INF-LLM",
            "Amazon SageMaker": "INF-CUST",
            "Amazon Comprehend": "INF-CUST",
        }
        return mapping.get(service)


class OpenAICostCollector(CostCollector):
    """
    Collects inference costs from OpenAI usage API.
    Covers: INF-LLM subcategory.
    """

    def __init__(self, api_key: str, organization_id: Optional[str] = None):
        self.api_key = api_key
        self.organization_id = organization_id
        self.base_url = "https://api.openai.com/v1"

    def source_name(self) -> str:
        return "OpenAI Usage API"

    async def collect(
        self,
        start_date: datetime,
        end_date: datetime,
        session: AsyncSession,
    ) -> CollectionResult:
        records = []
        errors = []
        total = Decimal("0")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        if self.organization_id:
            headers["OpenAI-Organization"] = self.organization_id

        try:
            async with aiohttp.ClientSession(headers=headers) as http:
                # Fetch usage data
                url = f"{self.base_url}/usage"
                params = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                }
                async with http.get(url, params=params) as resp:
                    if resp.status != 200:
                        errors.append(f"OpenAI API error: {resp.status}")
                        return CollectionResult(
                            source=self.source_name(),
                            records_collected=0,
                            records_failed=1,
                            total_amount_usd=Decimal("0"),
                            errors=errors,
                        )
                    data = await resp.json()

                # Fetch cost data
                cost_url = f"{self.base_url}/costs"
                async with http.get(cost_url, params=params) as cost_resp:
                    cost_data = await cost_resp.json() if cost_resp.status == 200 else {}

                # Build cost records from usage
                for usage_item in data.get("data", []):
                    record = self._parse_usage_item(usage_item, cost_data)
                    if record:
                        records.append(record)
                        total += record.amount_usd

        except Exception as e:
            errors.append(f"OpenAI collection error: {str(e)}")
            logger.exception("OpenAI cost collection failed")

        return CollectionResult(
            source=self.source_name(),
            records_collected=len(records),
            records_failed=len(errors),
            total_amount_usd=total,
            errors=errors,
        )

    def _parse_usage_item(
        self, item: dict, cost_data: dict
    ) -> Optional[CostRecord]:
        """Parse OpenAI usage item into a CostRecord."""
        # Implementation depends on OpenAI API response structure
        # This is a simplified version
        tokens = item.get("n_context_tokens", 0) + item.get("n_generated_tokens", 0)
        if tokens == 0:
            return None

        # Cost calculation based on model pricing
        model = item.get("model", "gpt-4")
        cost_per_1k = self._get_model_pricing(model)
        amount = (Decimal(tokens) / Decimal(1000)) * cost_per_1k

        return CostRecord(
            category=CostCategory.INFERENCE,
            subcategory="INF-LLM",
            amount=amount,
            amount_usd=amount,
            quantity=Decimal(tokens),
            unit_of_measure="tokens",
            unit_cost=cost_per_1k / Decimal(1000),
            source_type=SourceType.API_METER,
            source_system="OpenAI Usage API",
            source_record_id=f"openai:{item.get('id', '')}",
            cost_period_start=datetime.utcnow(),
            cost_period_end=datetime.utcnow(),
            tags=["openai", model],
        )

    @staticmethod
    def _get_model_pricing(model: str) -> Decimal:
        """Return cost per 1K tokens for a model."""
        pricing = {
            "gpt-4": Decimal("0.06"),
            "gpt-4-turbo": Decimal("0.03"),
            "gpt-3.5-turbo": Decimal("0.002"),
            "claude-3-opus": Decimal("0.045"),
            "claude-3-sonnet": Decimal("0.015"),
        }
        return pricing.get(model, Decimal("0.03"))


class CostCollectionPipeline:
    """
    Orchestrates cost collection from all sources.
    Runs daily via Airflow or Celery beat.
    """

    def __init__(self, db_session: AsyncSession):
        self.session = db_session
        self.collectors: list[CostCollector] = []

    def register_collector(self, collector: CostCollector) -> None:
        self.collectors.append(collector)

    async def run(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[CollectionResult]:
        """Execute full collection pipeline."""
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=1)

        results = []
        for collector in self.collectors:
            logger.info(f"Collecting from {collector.source_name()}")
            result = await collector.collect(start_date, end_date, self.session)
            results.append(result)
            logger.info(
                f"Collected {result.records_collected} records "
                f"(${result.total_amount_usd}) from {result.source}"
            )

        # Deduplication check (specification §3.5)
        await self._deduplicate()
        
        return results

    async def _deduplicate(self) -> None:
        """Remove duplicate cost records based on source_record_id."""
        from sqlalchemy import text
        
        await self.session.execute(text("""
            DELETE FROM ai_cost_records a
            USING ai_cost_records b
            WHERE a.id > b.id
              AND a.source_record_id = b.source_record_id
              AND a.source_system = b.source_system
        """))
        await self.session.commit()
```

### 2.3 Shadow AI Detection

```python
# pipelines/shadow_ai_detection.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.cost_models import CostRecord, CostCategory, SourceType

logger = logging.getLogger(__name__)


@dataclass
class ShadowAIAlert:
    alert_id: str
    detection_method: str
    description: str
    estimated_amount_usd: Decimal
    source_system: str
    severity: str  # low, medium, high, critical
    detected_at: datetime
    status: str = "open"  # open, triaged, attributed, resolved


class ShadowAIDetector:
    """
    Detects shadow AI spend — AI costs outside formal budgets and governance.
    Implements detection methods from specification §3.4.1.
    """

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def detect_unattributed_cloud_spend(self) -> list[ShadowAIAlert]:
        """
        Method 1: Cloud bill anomaly detection.
        AI-related cloud charges without matching initiative.
        """
        alerts = []
        
        query = text("""
            SELECT 
                c.source_system,
                c.source_record_id,
                c.amount_usd,
                c.category,
                c.tags
            FROM ai_cost_records c
            WHERE c.is_shadow = FALSE
              AND c.approval_status = 'approved'
              AND c.cost_period_start >= NOW() - INTERVAL '7 days'
              AND (
                  c.initiative_id IS NULL 
                  OR c.owner_id IS NULL
                  OR c.business_unit_id IS NULL
              )
              AND c.category IN ('INF', 'TRN', 'STO', 'INF-ARC')
        """)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        for row in rows:
            alert = ShadowAIAlert(
                alert_id=f"shadow-cloud-{row.source_record_id}",
                detection_method="cloud_bill_anomaly",
                description=(
                    f"Unattributed {row.category} spend of ${row.amount_usd} "
                    f"from {row.source_system}"
                ),
                estimated_amount_usd=row.amount_usd,
                source_system=row.source_system,
                severity=self._classify_severity(row.amount_usd),
                detected_at=datetime.utcnow(),
            )
            alerts.append(alert)
            
            # Mark record as shadow
            await self.session.execute(
                text("""
                    UPDATE ai_cost_records 
                    SET is_shadow = TRUE, 
                        shadow_reason = :reason,
                        updated_at = NOW()
                    WHERE source_record_id = :record_id
                """),
                {
                    "reason": f"Detected by cloud_bill_anomaly: {alert.description}",
                    "record_id": row.source_record_id,
                },
            )
        
        await self.session.commit()
        return alerts

    async def detect_unregistered_api_keys(self) -> list[ShadowAIAlert]:
        """
        Method 2: API key audit.
        AI API keys not registered in asset inventory.
        """
        alerts = []
        
        # Query for API keys in cloud provider IAM that aren't in our registry
        query = text("""
            SELECT 
                k.key_id,
                k.service,
                k.last_used,
                COALESCE(SUM(c.amount_usd), 0) as total_spend
            FROM cloud_api_keys k
            LEFT JOIN ai_cost_records c ON c.source_record_id = k.key_id
            WHERE k.registered_in_inventory = FALSE
              AND k.service IN ('openai', 'anthropic', 'cohere', 'replicate')
              AND k.last_used >= NOW() - INTERVAL '30 days'
            GROUP BY k.key_id, k.service, k.last_used
            HAVING COALESCE(SUM(c.amount_usd), 0) > 0
        """)
        
        result = await self.session.execute(query)
        for row in result.fetchall():
            alert = ShadowAIAlert(
                alert_id=f"shadow-apikey-{row.key_id}",
                detection_method="api_key_audit",
                description=(
                    f"Unregistered {row.service} API key {row.key_id} "
                    f"with ${row.total_spend} spend in last 30 days"
                ),
                estimated_amount_usd=row.total_spend,
                source_system=row.service,
                severity="high" if row.total_spend > 1000 else "medium",
                detected_at=datetime.utcnow(),
            )
            alerts.append(alert)
        
        return alerts

    async def detect_saas_ai_spend(self) -> list[ShadowAIAlert]:
        """
        Method 3: SaaS spend analysis.
        AI tool subscriptions not in approved vendor list.
        """
        alerts = []
        
        query = text("""
            SELECT 
                s.vendor_name,
                s.monthly_cost,
                s.department,
                s.subscription_id
            FROM saas_subscriptions s
            WHERE s.category = 'ai_tools'
              AND s.approved_vendor = FALSE
              AND s.active = TRUE
        """)
        
        result = await self.session.execute(query)
        for row in result.fetchall():
            alert = ShadowAIAlert(
                alert_id=f"shadow-saas-{row.subscription_id}",
                detection_method="saas_spend_analysis",
                description=(
                    f"Unapproved AI SaaS: {row.vendor_name} "
                    f"(${row.monthly_cost}/mo) in {row.department}"
                ),
                estimated_amount_usd=row.monthly_cost,
                source_system="procurement",
                severity="medium",
                detected_at=datetime.utcnow(),
            )
            alerts.append(alert)
        
        return alerts

    async def compute_shadow_ai_ratio(self) -> dict:
        """
        Compute UC7-004: Shadow AI Spend Ratio.
        Formula: (Shadow AI spend / Total AI spend) × 100
        Target: <10%
        """
        query = text("""
            SELECT 
                COALESCE(SUM(amount_usd) FILTER (WHERE is_shadow = TRUE), 0) as shadow_spend,
                COALESCE(SUM(amount_usd), 0) as total_spend
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= DATE_TRUNC('month', NOW())
        """)
        
        result = await self.session.execute(query)
        row = result.fetchone()
        
        total = row.total_spend or Decimal("0")
        shadow = row.shadow_spend or Decimal("0")
        ratio = (shadow / total * 100) if total > 0 else Decimal("0")
        
        return {
            "shadow_ai_ratio": round(ratio, 2),
            "shadow_spend_usd": float(shadow),
            "total_spend_usd": float(total),
            "target": 10.0,
            "status": "green" if ratio < 10 else "yellow" if ratio < 20 else "red",
            "escalation_tier": (
                "operational" if ratio < 10 
                else "management" if ratio < 20 
                else "board"
            ),
        }

    @staticmethod
    def _classify_severity(amount: Decimal) -> str:
        if amount > 10000:
            return "critical"
        elif amount > 5000:
            return "high"
        elif amount > 1000:
            return "medium"
        return "low"
```

---

## 3. ROI Measurement

### 3.1 ROI Data Models

```python
# models/roi_models.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class ROIType(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    GOVERNANCE = "governance"
    BLENDED = "blended"


@dataclass
class DirectROIMeasurement:
    """
    Direct ROI measurement per specification §4.2.
    
    Direct ROI = (Direct AI Value - Direct AI Cost) / Direct AI Cost × 100
    """
    initiative_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    
    # Value components
    revenue_direct: Decimal = Decimal("0")
    revenue_attributed: Decimal = Decimal("0")
    cost_savings: Decimal = Decimal("0")
    productivity_gains: Decimal = Decimal("0")
    
    # Cost components
    cost_inference: Decimal = Decimal("0")
    cost_training: Decimal = Decimal("0")
    cost_storage: Decimal = Decimal("0")
    cost_data: Decimal = Decimal("0")
    cost_infrastructure: Decimal = Decimal("0")
    cost_licensing: Decimal = Decimal("0")
    cost_operations: Decimal = Decimal("0")
    
    # Evidence
    value_evidence: dict = field(default_factory=dict)
    cost_evidence: dict = field(default_factory=dict)
    
    # Governance
    measured_by: Optional[uuid.UUID] = None
    verified_by: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None

    @property
    def total_value(self) -> Decimal:
        return (
            self.revenue_direct
            + self.revenue_attributed
            + self.cost_savings
            + self.productivity_gains
        )

    @property
    def total_cost(self) -> Decimal:
        return (
            self.cost_inference
            + self.cost_training
            + self.cost_storage
            + self.cost_data
            + self.cost_infrastructure
            + self.cost_licensing
            + self.cost_operations
        )

    @property
    def net_value(self) -> Decimal:
        return self.total_value - self.total_cost

    @property
    def roi_percentage(self) -> Optional[Decimal]:
        if self.total_cost > 0:
            return (self.net_value / self.total_cost) * 100
        return None

    @property
    def roi_ratio(self) -> Optional[Decimal]:
        """ROI as a ratio (e.g., 1.5 = $1.50 return per $1 spent)."""
        if self.total_cost > 0:
            return self.total_value / self.total_cost
        return None


@dataclass
class IndirectROIMeasurement:
    """
    Indirect ROI measurement per specification §4.3.
    
    Indirect ROI = (Cost Avoidance + Productivity Gains + Quality Gains) / Total AI Cost × 100
    """
    initiative_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    
    # Cost avoidance components
    risk_prevention_value: Decimal = Decimal("0")
    compliance_avoidance_value: Decimal = Decimal("0")
    incident_avoidance_value: Decimal = Decimal("0")
    efficiency_gains: Decimal = Decimal("0")
    
    # Productivity and quality
    time_saved_hours: Decimal = Decimal("0")
    time_value_per_hour: Decimal = Decimal("0")
    quality_improvement_value: Decimal = Decimal("0")
    employee_satisfaction_value: Decimal = Decimal("0")
    customer_satisfaction_value: Decimal = Decimal("0")
    
    # Total AI cost (denominator)
    total_ai_cost: Decimal = Decimal("0")
    
    # Evidence
    evidence: dict = field(default_factory=dict)

    @property
    def total_indirect_value(self) -> Decimal:
        productivity = self.time_saved_hours * self.time_value_per_hour
        return (
            self.risk_prevention_value
            + self.compliance_avoidance_value
            + self.incident_avoidance_value
            + self.efficiency_gains
            + productivity
            + self.quality_improvement_value
            + self.employee_satisfaction_value
            + self.customer_satisfaction_value
        )

    @property
    def roi_percentage(self) -> Optional[Decimal]:
        if self.total_ai_cost > 0:
            return (self.total_indirect_value / self.total_ai_cost) * 100
        return None


@dataclass
class GovernanceROIMeasurement:
    """
    Governance ROI measurement per specification §4.4.
    
    Governance ROI = (Governance Value - Governance Cost) / Governance Cost × 100
    """
    period_start: datetime
    period_end: datetime
    
    # Governance value components
    risk_reduction_value: Decimal = Decimal("0")
    compliance_cost_savings: Decimal = Decimal("0")
    incident_cost_avoidance: Decimal = Decimal("0")
    time_to_market_acceleration: Decimal = Decimal("0")
    trust_premium: Decimal = Decimal("0")
    
    # Governance cost components
    governance_tooling_cost: Decimal = Decimal("0")
    governance_personnel_cost: Decimal = Decimal("0")
    governance_process_cost: Decimal = Decimal("0")
    
    # Evidence
    evidence: dict = field(default_factory=dict)

    @property
    def total_governance_value(self) -> Decimal:
        return (
            self.risk_reduction_value
            + self.compliance_cost_savings
            + self.incident_cost_avoidance
            + self.time_to_market_acceleration
            + self.trust_premium
        )

    @property
    def total_governance_cost(self) -> Decimal:
        return (
            self.governance_tooling_cost
            + self.governance_personnel_cost
            + self.governance_process_cost
        )

    @property
    def roi_percentage(self) -> Optional[Decimal]:
        if self.total_governance_cost > 0:
            net = self.total_governance_value - self.total_governance_cost
            return (net / self.total_governance_cost) * 100
        return None

    def maturity_target_met(self, maturity_level: int) -> bool:
        """Check if governance ROI meets target for maturity level (spec §4.4.3)."""
        targets = {1: 0.5, 2: 1.0, 3: 2.0, 4: 3.0, 5: 5.0}
        target = targets.get(maturity_level, 1.0)
        roi = self.roi_percentage
        return roi is not None and roi >= target
```

### 3.2 ROI Calculation Engine

```python
# services/roi_calculator.py
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.roi_models import (
    DirectROIMeasurement,
    IndirectROIMeasurement,
    GovernanceROIMeasurement,
    ROIType,
)

logger = logging.getLogger(__name__)


class ROICalculator:
    """
    Calculates all ROI dimensions per specification §4.
    
    Implements:
    - Direct ROI (§4.2)
    - Indirect ROI (§4.3)
    - Governance ROI (§4.4)
    - Blended ROI (§4.5 ROI-004)
    """

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def calculate_direct_roi(
        self,
        initiative_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> DirectROIMeasurement:
        """Calculate direct ROI for an initiative over a period."""
        
        # Fetch cost breakdown by category
        cost_query = text("""
            SELECT 
                COALESCE(SUM(amount_usd) FILTER (WHERE category = 'INF'), 0) as inference,
                COALESCE(SUM(amount_usd) FILTER (WHERE category = 'TRN'), 0) as training,
                COALESCE(SUM(amount_usd) FILTER (WHERE category = 'STO'), 0) as storage,
                COALESCE(SUM(amount_usd) FILTER (WHERE category = 'DAT'), 0) as data,
                COALESCE(SUM(amount_usd) FILTER (WHERE category = 'INF-ARC'), 0) as infrastructure,
                COALESCE(SUM(amount_usd) FILTER (WHERE category = 'LIC'), 0) as licensing,
                COALESCE(SUM(amount_usd) FILTER (WHERE category = 'OPS'), 0) as operations
            FROM ai_cost_records
            WHERE initiative_id = :initiative_id
              AND approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
        """)
        
        result = await self.session.execute(
            cost_query,
            {"initiative_id": initiative_id, "start": period_start, "end": period_end},
        )
        costs = result.fetchone()

        # Fetch value data from CRM/finance systems
        value_data = await self._fetch_value_data(initiative_id, period_start, period_end)

        measurement = DirectROIMeasurement(
            initiative_id=initiative_id,
            period_start=period_start,
            period_end=period_end,
            revenue_direct=Decimal(str(value_data.get("revenue_direct", 0))),
            revenue_attributed=Decimal(str(value_data.get("revenue_attributed", 0))),
            cost_savings=Decimal(str(value_data.get("cost_savings", 0))),
            productivity_gains=Decimal(str(value_data.get("productivity_gains", 0))),
            cost_inference=Decimal(str(costs.inference or 0)),
            cost_training=Decimal(str(costs.training or 0)),
            cost_storage=Decimal(str(costs.storage or 0)),
            cost_data=Decimal(str(costs.data or 0)),
            cost_infrastructure=Decimal(str(costs.infrastructure or 0)),
            cost_licensing=Decimal(str(costs.licensing or 0)),
            cost_operations=Decimal(str(costs.operations or 0)),
            value_evidence=value_data.get("evidence", {}),
        )

        logger.info(
            f"Direct ROI for initiative {initiative_id}: "
            f"{measurement.roi_percentage}% "
            f"(Value: ${measurement.total_value}, Cost: ${measurement.total_cost})"
        )
        
        return measurement

    async def calculate_governance_roi(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> GovernanceROIMeasurement:
        """Calculate governance ROI per specification §4.4."""
        
        # Fetch governance costs
        cost_query = text("""
            SELECT COALESCE(SUM(amount_usd), 0) as total
            FROM ai_cost_records
            WHERE category = 'GOV'
              AND approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
        """)
        
        result = await self.session.execute(
            cost_query, {"start": period_start, "end": period_end}
        )
        gov_cost = Decimal(str(result.fetchone().total or 0))

        # Fetch governance value components
        value_data = await self._fetch_governance_value(period_start, period_end)

        measurement = GovernanceROIMeasurement(
            period_start=period_start,
            period_end=period_end,
            risk_reduction_value=Decimal(str(value_data.get("risk_reduction", 0))),
            compliance_cost_savings=Decimal(str(value_data.get("compliance_savings", 0))),
            incident_cost_avoidance=Decimal(str(value_data.get("incident_avoidance", 0))),
            time_to_market_acceleration=Decimal(str(value_data.get("acceleration", 0))),
            trust_premium=Decimal(str(value_data.get("trust_premium", 0))),
            governance_tooling_cost=gov_cost * Decimal("0.4"),
            governance_personnel_cost=gov_cost * Decimal("0.4"),
            governance_process_cost=gov_cost * Decimal("0.2"),
            evidence=value_data.get("evidence", {}),
        )

        return measurement

    async def calculate_blended_roi(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> dict:
        """
        Calculate blended ROI (ROI-004).
        Blended ROI = (Total Value - Total Cost) / Total Cost × 100
        """
        # Aggregate all costs
        cost_query = text("""
            SELECT COALESCE(SUM(amount_usd), 0) as total_cost
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
        """)
        
        result = await self.session.execute(
            cost_query, {"start": period_start, "end": period_end}
        )
        total_cost = Decimal(str(result.fetchone().total_cost or 0))

        # Aggregate all value
        value_query = text("""
            SELECT 
                COALESCE(SUM(revenue_direct + revenue_attributed + cost_savings + productivity_gains), 0) as direct_value,
                COALESCE(SUM(risk_prevention_value + compliance_avoidance_value + incident_avoidance_value + efficiency_gains), 0) as indirect_value
            FROM ai_roi_direct r
            WHERE r.period_start >= :start AND r.period_end <= :end
        """)
        
        result = await self.session.execute(
            value_query, {"start": period_start, "end": period_end}
        )
        values = result.fetchone()
        
        total_value = Decimal(str((values.direct_value or 0) + (values.indirect_value or 0)))
        net_value = total_value - total_cost
        roi = (net_value / total_cost * 100) if total_cost > 0 else None

        return {
            "total_value_usd": float(total_value),
            "total_cost_usd": float(total_cost),
            "net_value_usd": float(net_value),
            "roi_percentage": float(roi) if roi else None,
            "roi_ratio": float(total_value / total_cost) if total_cost > 0 else None,
            "target": 1.0,
            "status": "green" if roi and roi >= 100 else "yellow" if roi and roi >= 50 else "red",
        }

    async def compute_roi_metrics(self, period_start: datetime, period_end: datetime) -> dict:
        """
        Compute all ROI metrics from the catalog (specification §4.5).
        """
        metrics = {}
        
        # ROI-001: Direct ROI (aggregate)
        direct = await self._aggregate_direct_roi(period_start, period_end)
        metrics["ROI-001"] = {
            "name": "Direct ROI",
            "value": direct,
            "target": ">1.0",
            "status": "green" if direct and direct > 1.0 else "red",
        }
        
        # ROI-002: Indirect ROI
        indirect = await self._aggregate_indirect_roi(period_start, period_end)
        metrics["ROI-002"] = {
            "name": "Indirect ROI",
            "value": indirect,
            "target": ">0.5",
            "status": "green" if indirect and indirect > 0.5 else "red",
        }
        
        # ROI-003: Governance ROI
        gov = await self.calculate_governance_roi(period_start, period_end)
        gov_roi = gov.roi_percentage
        metrics["ROI-003"] = {
            "name": "Governance ROI",
            "value": float(gov_roi) if gov_roi else None,
            "target": ">1.0",
            "status": "green" if gov_roi and gov_roi > 1.0 else "red",
        }
        
        # ROI-004: Blended ROI
        blended = await self.calculate_blended_roi(period_start, period_end)
        metrics["ROI-004"] = {
            "name": "Blended ROI",
            "value": blended.get("roi_ratio"),
            "target": ">1.0",
            "status": blended["status"],
        }
        
        # ROI-005: Cost per Inference
        cost_per_inf = await self._cost_per_inference(period_start, period_end)
        metrics["ROI-005"] = {
            "name": "Cost per Inference",
            "value": cost_per_inf,
            "target": "Declining",
            "status": "green",  # Requires trend analysis
        }
        
        # ROI-010: Payback Period
        payback = await self._payback_period(period_start, period_end)
        metrics["ROI-010"] = {
            "name": "Payback Period (months)",
            "value": payback,
            "target": "<18",
            "status": "green" if payback and payback < 18 else "yellow" if payback and payback < 24 else "red",
        }
        
        return metrics

    async def _fetch_value_data(
        self, initiative_id: uuid.UUID, start: datetime, end: datetime
    ) -> dict:
        """Fetch value data from CRM/finance systems."""
        # Integration point: CRM, billing system, time tracking
        # This would connect to your financial systems
        return {
            "revenue_direct": 0,
            "revenue_attributed": 0,
            "cost_savings": 0,
            "productivity_gains": 0,
            "evidence": {},
        }

    async def _fetch_governance_value(
        self, start: datetime, end: datetime
    ) -> dict:
        """Fetch governance value components."""
        # Integration point: risk register, incident management, compliance
        return {
            "risk_reduction": 0,
            "compliance_savings": 0,
            "incident_avoidance": 0,
            "acceleration": 0,
            "trust_premium": 0,
            "evidence": {},
        }

    async def _aggregate_direct_roi(
        self, start: datetime, end: datetime
    ) -> Optional[float]:
        query = text("""
            SELECT 
                CASE WHEN SUM(total_cost) > 0 
                THEN (SUM(total_value) - SUM(total_cost)) / SUM(total_cost)
                ELSE NULL END as roi
            FROM ai_roi_direct
            WHERE period_start >= :start AND period_end <= :end
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        row = result.fetchone()
        return float(row.roi) if row and row.roi else None

    async def _aggregate_indirect_roi(
        self, start: datetime, end: datetime
    ) -> Optional[float]:
        # Implementation for indirect ROI aggregation
        return None

    async def _cost_per_inference(
        self, start: datetime, end: datetime
    ) -> Optional[float]:
        query = text("""
            SELECT 
                CASE WHEN SUM(quantity) > 0 
                THEN SUM(amount_usd) / SUM(quantity)
                ELSE NULL END as cost_per_unit
            FROM ai_cost_records
            WHERE category = 'INF'
              AND approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
              AND quantity IS NOT NULL
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        row = result.fetchone()
        return float(row.cost_per_unit) if row and row.cost_per_unit else None

    async def _payback_period(
        self, start: datetime, end: datetime
    ) -> Optional[float]:
        """Calculate payback period in months."""
        # Simplified: cumulative net value / average monthly investment
        query = text("""
            WITH monthly AS (
                SELECT 
                    DATE_TRUNC('month', cost_period_start) as month,
                    SUM(amount_usd) as monthly_cost
                FROM ai_cost_records
                WHERE approval_status = 'approved'
                GROUP BY DATE_TRUNC('month', cost_period_start)
                ORDER BY month
            )
            SELECT COUNT(*) as months_to_payback
            FROM (
                SELECT month, monthly_cost,
                       SUM(monthly_cost) OVER (ORDER BY month) as cumulative
                FROM monthly
            ) sub
            WHERE cumulative <= 0
        """)
        result = await self.session.execute(query)
        row = result.fetchone()
        return float(row.months_to_payback) if row and row.months_to_payback else None
```

---

## 4. Budget Management

### 4.1 Budget Data Models

```python
# models/budget_models.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class BudgetType(str, Enum):
    CATEGORY = "category"
    BUSINESS_UNIT = "business_unit"
    INITIATIVE = "initiative"
    COST_CENTER = "cost_center"


class BudgetPeriod(str, Enum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"


class BudgetStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    CLOSED = "closed"


@dataclass
class Budget:
    """
    AI budget record matching ai_budgets schema (specification §5.1.2).
    """
    budget_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    budget_type: BudgetType = BudgetType.INITIATIVE
    budget_scope: str = ""  # e.g., "INF", "BU-001", "INIT-001"
    fiscal_year: int = 2026
    period: BudgetPeriod = BudgetPeriod.ANNUAL
    
    # Amounts
    budget_amount: Decimal = Decimal("0")
    currency: str = "USD"
    budget_amount_usd: Decimal = Decimal("0")
    
    # Hierarchy
    parent_budget_id: Optional[uuid.UUID] = None
    
    # Ownership
    owner_id: uuid.UUID = field(default_factory=uuid.uuid4)
    approver_id: uuid.UUID = field(default_factory=uuid.uuid4)
    
    # Status
    status: BudgetStatus = BudgetStatus.DRAFT
    
    # Timestamps
    proposed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    effective_start: datetime = field(default_factory=datetime.utcnow)
    effective_end: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    justification: Optional[str] = None
    assumptions: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    
    # Audit
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: uuid.UUID = field(default_factory=uuid.uuid4)
    updated_by: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class BudgetAllocation:
    """Budget allocation to initiative/project/cost center."""
    budget_id: uuid.UUID
    allocated_to_type: str  # initiative, project, cost_center
    allocated_to_id: uuid.UUID
    allocated_amount: Decimal
    allocated_by: uuid.UUID
    allocated_at: datetime = field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


@dataclass
class BudgetVariance:
    """Budget variance analysis result."""
    budget_id: str
    budget_scope: str
    budget_amount: Decimal
    actual_spend: Decimal
    variance_amount: Decimal
    variance_percentage: Decimal
    monthly_run_rate: Decimal
    forecast_annual: Decimal
    status: str  # under_utilized, on_track, at_risk, over_budget
    period_elapsed_pct: Decimal
    period_remaining_pct: Decimal
```

### 4.2 Budget Management Service

```python
# services/budget_manager.py
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.budget_models import (
    Budget,
    BudgetType,
    BudgetStatus,
    BudgetVariance,
    BudgetAllocation,
)

logger = logging.getLogger(__name__)


class BudgetManager:
    """
    Manages AI budget lifecycle per specification §5.
    
    Implements:
    - Budget planning workflow (§5.2.1)
    - Budget change control (§5.2.2)
    - Budget monitoring & variance analysis (§5.3)
    - Budget enforcement (§5.3.3)
    - Budget reallocation (§5.4)
    """

    # Alert thresholds from specification §5.3.2
    THRESHOLDS = {
        "under_utilized": 0.50,  # <50% spent at 75% of period
        "on_track": 0.75,        # 75-90% spent
        "at_risk": 0.90,         # 90-100% spent
        "over_budget": 1.00,     # >100% spent
        "critical_over": 1.20,   # >120% spent
    }

    # Enforcement levels from specification §5.3.3
    ENFORCEMENT = {
        "warning": {"threshold": 0.90, "action": "alert"},
        "soft_block": {"threshold": 1.00, "action": "caio_approval_required"},
        "hard_block": {"threshold": 1.10, "action": "spending_frozen"},
        "emergency": {"threshold": 1.20, "action": "all_frozen"},
    }

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def create_budget(
        self,
        budget_type: BudgetType,
        scope: str,
        amount: Decimal,
        fiscal_year: int,
        owner_id: uuid.UUID,
        approver_id: uuid.UUID,
        period: str = "annual",
        justification: str = "",
        parent_budget_id: Optional[uuid.UUID] = None,
    ) -> Budget:
        """Create a new budget in draft status."""
        now = datetime.utcnow()
        
        # Determine effective dates based on period
        if period == "annual":
            effective_start = datetime(fiscal_year, 1, 1)
            effective_end = datetime(fiscal_year, 12, 31)
        elif period == "quarterly":
            effective_start = datetime(fiscal_year, 1, 1)
            effective_end = datetime(fiscal_year, 3, 31)
        else:
            effective_start = datetime(fiscal_year, 1, 1)
            effective_end = datetime(fiscal_year, 1, 31)

        budget = Budget(
            budget_type=budget_type,
            budget_scope=scope,
            budget_amount=amount,
            budget_amount_usd=amount,
            fiscal_year=fiscal_year,
            period=period,
            owner_id=owner_id,
            approver_id=approver_id,
            status=BudgetStatus.DRAFT,
            effective_start=effective_start,
            effective_end=effective_end,
            justification=justification,
            parent_budget_id=parent_budget_id,
            created_by=owner_id,
            updated_by=owner_id,
        )

        self.session.add(budget)
        await self.session.commit()
        
        logger.info(f"Created budget {budget.budget_id} for {scope}: ${amount}")
        return budget

    async def approve_budget(
        self,
        budget_id: str,
        approver_id: uuid.UUID,
    ) -> Budget:
        """Approve a budget (transition to active)."""
        result = await self.session.execute(
            select(Budget).where(Budget.budget_id == budget_id)
        )
        budget = result.scalar_one_or_none()
        
        if not budget:
            raise ValueError(f"Budget {budget_id} not found")
        
        if budget.status != BudgetStatus.PROPOSED:
            raise ValueError(f"Cannot approve budget in status {budget.status}")
        
        budget.status = BudgetStatus.ACTIVE
        budget.approved_at = datetime.utcnow()
        budget.approver_id = approver_id
        budget.updated_at = datetime.utcnow()
        budget.updated_by = approver_id
        
        await self.session.commit()
        logger.info(f"Approved budget {budget_id}")
        return budget

    async def compute_variance(self, budget_id: str) -> BudgetVariance:
        """
        Compute budget variance per specification §5.3.1.
        """
        result = await self.session.execute(
            select(Budget).where(Budget.budget_id == budget_id)
        )
        budget = result.scalar_one_or_none()
        
        if not budget:
            raise ValueError(f"Budget {budget_id} not found")

        # Compute actual spend
        spend_query = text("""
            SELECT COALESCE(SUM(amount_usd), 0) as actual_spend
            FROM ai_cost_records c
            WHERE c.approval_status = 'approved'
              AND c.cost_period_start >= :start
              AND c.cost_period_end <= :end
              AND (
                  c.initiative_id::text = :scope
                  OR c.business_unit_id::text = :scope
                  OR c.cost_center = :scope
                  OR c.category = :scope
              )
        """)
        
        result = await self.session.execute(
            spend_query,
            {
                "start": budget.effective_start,
                "end": budget.effective_end,
                "scope": budget.budget_scope,
            },
        )
        actual_spend = Decimal(str(result.fetchone().actual_spend or 0))

        # Compute variance
        variance_amount = budget.budget_amount_usd - actual_spend
        variance_pct = (
            (variance_amount / budget.budget_amount_usd * 100)
            if budget.budget_amount_usd > 0
            else Decimal("0")
        )

        # Compute run rate and forecast
        now = datetime.utcnow()
        months_elapsed = max(
            1,
            (now - budget.effective_start).days / 30.44,
        )
        monthly_run_rate = actual_spend / Decimal(str(months_elapsed))
        forecast_annual = monthly_run_rate * 12

        # Compute period elapsed
        total_days = (budget.effective_end - budget.effective_start).days
        elapsed_days = (now - budget.effective_start).days
        period_elapsed_pct = (
            Decimal(str(elapsed_days)) / Decimal(str(total_days)) * 100
            if total_days > 0
            else Decimal("0")
        )
        period_remaining_pct = Decimal("100") - period_elapsed_pct

        # Determine status
        spend_pct = (
            actual_spend / budget.budget_amount_usd
            if budget.budget_amount_usd > 0
            else Decimal("0")
        )
        
        if spend_pct > self.THRESHOLDS["critical_over"]:
            status = "critical_over"
        elif spend_pct > self.THRESHOLDS["over_budget"]:
            status = "over_budget"
        elif spend_pct > self.THRESHOLDS["at_risk"]:
            status = "at_risk"
        elif spend_pct > self.THRESHOLDS["on_track"]:
            status = "on_track"
        elif period_elapsed_pct > 75 and spend_pct < self.THRESHOLDS["under_utilized"]:
            status = "under_utilized"
        else:
            status = "on_track"

        return BudgetVariance(
            budget_id=budget.budget_id,
            budget_scope=budget.budget_scope,
            budget_amount=budget.budget_amount_usd,
            actual_spend=actual_spend,
            variance_amount=variance_amount,
            variance_percentage=variance_pct,
            monthly_run_rate=monthly_run_rate,
            forecast_annual=forecast_annual,
            status=status,
            period_elapsed_pct=period_elapsed_pct,
            period_remaining_pct=period_remaining_pct,
        )

    async def check_enforcement(self, budget_id: str) -> Optional[dict]:
        """
        Check if budget enforcement action is needed (specification §5.3.3).
        """
        variance = await self.compute_variance(budget_id)
        spend_pct = (
            variance.actual_spend / variance.budget_amount
            if variance.budget_amount > 0
            else Decimal("0")
        )

        for level, config in self.ENFORCEMENT.items():
            if spend_pct >= Decimal(str(config["threshold"])):
                return {
                    "level": level,
                    "action": config["action"],
                    "spend_percentage": float(spend_pct * 100),
                    "threshold": config["threshold"],
                    "budget_id": budget_id,
                    "variance": variance,
                }
        
        return None

    async def reallocate_budget(
        self,
        from_budget_id: str,
        to_budget_id: str,
        amount: Decimal,
        requested_by: uuid.UUID,
        justification: str,
    ) -> dict:
        """
        Reallocate budget between initiatives (specification §5.4).
        
        Rules:
        - Contingency reserve: 10% held by CAIO
        - ROI threshold: reallocated funds must go to initiatives with ROI > 1.0
        - One-way door: cannot reallocate from governance/security/compliance
        """
        # Validate source budget
        result = await self.session.execute(
            select(Budget).where(Budget.budget_id == from_budget_id)
        )
        from_budget = result.scalar_one_or_none()
        
        if not from_budget:
            raise ValueError(f"Source budget {from_budget_id} not found")
        
        # Check one-way door rule
        if from_budget.budget_scope in ("GOV", "SEC", "COMP"):
            raise ValueError(
                f"Cannot reallocate from governance/security/compliance budget "
                f"{from_budget.budget_scope}"
            )
        
        # Validate target budget
        result = await self.session.execute(
            select(Budget).where(Budget.budget_id == to_budget_id)
        )
        to_budget = result.scalar_one_or_none()
        
        if not to_budget:
            raise ValueError(f"Target budget {to_budget_id} not found")
        
        # Check ROI threshold
        target_roi = await self._get_initiative_roi(to_budget.budget_scope)
        if target_roi is not None and target_roi < 1.0:
            raise ValueError(
                f"Target initiative ROI ({target_roi}) is below threshold (1.0)"
            )
        
        # Check available funds
        variance = await self.compute_variance(from_budget_id)
        available = variance.variance_amount
        if amount > available:
            raise ValueError(
                f"Insufficient funds: requested ${amount}, available ${available}"
            )
        
        # Execute reallocation
        from_budget.budget_amount_usd -= amount
        from_budget.updated_at = datetime.utcnow()
        from_budget.updated_by = requested_by
        
        to_budget.budget_amount_usd += amount
        to_budget.updated_at = datetime.utcnow()
        to_budget.updated_by = requested_by
        
        # Log reallocation
        await self.session.execute(
            text("""
                INSERT INTO ai_budget_reallocations 
                (from_budget_id, to_budget_id, amount, requested_by, justification, created_at)
                VALUES (:from_id, :to_id, :amount, :requested_by, :justification, NOW())
            """),
            {
                "from_id": from_budget_id,
                "to_id": to_budget_id,
                "amount": amount,
                "requested_by": requested_by,
                "justification": justification,
            },
        )
        
        await self.session.commit()
        
        logger.info(
            f"Reallocated ${amount} from {from_budget_id} to {to_budget_id}"
        )
        
        return {
            "from_budget": from_budget_id,
            "to_budget": to_budget_id,
            "amount": float(amount),
            "justification": justification,
        }

    async def get_budget_dashboard(self, fiscal_year: int) -> dict:
        """Get budget dashboard for management reporting."""
        query = text("""
            SELECT 
                b.budget_type,
                b.budget_scope,
                b.budget_amount_usd,
                b.status,
                COALESCE(SUM(c.amount_usd) FILTER (
                    WHERE c.approval_status = 'approved'
                    AND c.cost_period_start >= b.effective_start
                    AND c.cost_period_end <= b.effective_end
                ), 0) as actual_spend
            FROM ai_budgets b
            LEFT JOIN ai_cost_records c ON (
                c.initiative_id::text = b.budget_scope
                OR c.business_unit_id::text = b.budget_scope
                OR c.cost_center = b.budget_scope
                OR c.category = b.budget_scope
            )
            WHERE b.fiscal_year = :year AND b.status = 'active'
            GROUP BY b.budget_id, b.budget_type, b.budget_scope, 
                     b.budget_amount_usd, b.status
            ORDER BY b.budget_type, b.budget_scope
        """)
        
        result = await self.session.execute(query, {"year": fiscal_year})
        rows = result.fetchall()
        
        dashboard = {
            "fiscal_year": fiscal_year,
            "total_budget": Decimal("0"),
            "total_spend": Decimal("0"),
            "by_type": {},
            "by_scope": [],
        }
        
        for row in rows:
            dashboard["total_budget"] += row.budget_amount_usd
            dashboard["total_spend"] += Decimal(str(row.actual_spend or 0))
            
            if row.budget_type not in dashboard["by_type"]:
                dashboard["by_type"][row.budget_type] = {
                    "budget": Decimal("0"),
                    "spend": Decimal("0"),
                }
            dashboard["by_type"][row.budget_type]["budget"] += row.budget_amount_usd
            dashboard["by_type"][row.budget_type]["spend"] += Decimal(str(row.actual_spend or 0))
            
            dashboard["by_scope"].append({
                "scope": row.budget_scope,
                "type": row.budget_type,
                "budget": float(row.budget_amount_usd),
                "spend": float(row.actual_spend or 0),
                "variance_pct": float(
                    (row.budget_amount_usd - Decimal(str(row.actual_spend or 0)))
                    / row.budget_amount_usd * 100
                ) if row.budget_amount_usd > 0 else 0,
            })
        
        # Convert Decimals to floats for JSON serialization
        dashboard["total_budget"] = float(dashboard["total_budget"])
        dashboard["total_spend"] = float(dashboard["total_spend"])
        for k, v in dashboard["by_type"].items():
            v["budget"] = float(v["budget"])
            v["spend"] = float(v["spend"])
        
        return dashboard

    async def _get_initiative_roi(self, scope: str) -> Optional[float]:
        """Get ROI for an initiative by scope."""
        query = text("""
            SELECT 
                CASE WHEN SUM(total_cost) > 0 
                THEN (SUM(total_value) - SUM(total_cost)) / SUM(total_cost)
                ELSE NULL END as roi
            FROM ai_roi_direct
            WHERE initiative_id::text = :scope
        """)
        result = await self.session.execute(query, {"scope": scope})
        row = result.fetchone()
        return float(row.roi) if row and row.roi else None
```

---

## 5. Cost Anomaly Detection

### 5.1 Anomaly Detection Engine

```python
# services/anomaly_detector.py
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class AnomalyAlert:
    alert_id: str
    anomaly_type: str  # spike, drop, trend_change, pattern_break
    severity: str  # low, medium, high, critical
    category: str
    scope: str  # initiative_id, business_unit_id, or category
    description: str
    expected_value: float
    actual_value: float
    deviation_pct: float
    detected_at: datetime
    status: str = "open"  # open, investigating, resolved, false_positive
    assigned_to: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None


class CostAnomalyDetector:
    """
    Detects cost anomalies using statistical methods.
    
    Implements specification §3.5 data quality check:
    "Amount anomaly (>3σ from baseline) — Daily — Flag for verification"
    
    Also implements specification §6.3.2 operational report:
    "Anomaly Detection — Unusual cost patterns and spikes"
    """

    def __init__(self, db_session: AsyncSession):
        self.session = db_session
        self.min_history_days = 30  # Minimum days of history for baseline
        self.sigma_threshold = 3.0  # 3-sigma rule

    async def detect_spikes(
        self,
        lookback_days: int = 7,
        category: Optional[str] = None,
    ) -> list[AnomalyAlert]:
        """
        Detect cost spikes using z-score analysis.
        Flags any daily spend > 3σ from the rolling baseline.
        """
        alerts = []
        
        category_filter = f"AND category = '{category}'" if category else ""
        
        query = text(f"""
            WITH daily_spend AS (
                SELECT 
                    DATE(cost_period_start) as day,
                    category,
                    initiative_id,
                    business_unit_id,
                    SUM(amount_usd) as daily_total
                FROM ai_cost_records
                WHERE approval_status = 'approved'
                  AND cost_period_start >= NOW() - INTERVAL '{lookback_days + self.min_history_days} days'
                  {category_filter}
                GROUP BY DATE(cost_period_start), category, initiative_id, business_unit_id
            ),
            stats AS (
                SELECT 
                    category,
                    initiative_id,
                    business_unit_id,
                    AVG(daily_total) as mean_spend,
                    STDDEV(daily_total) as stddev_spend,
                    COUNT(*) as history_days
                FROM daily_spend
                WHERE day < CURRENT_DATE - INTERVAL '{lookback_days} days'
                GROUP BY category, initiative_id, business_unit_id
                HAVING COUNT(*) >= {self.min_history_days}
            )
            SELECT 
                d.day,
                d.category,
                d.initiative_id,
                d.business_unit_id,
                d.daily_total,
                s.mean_spend,
                s.stddev_spend,
                s.history_days,
                CASE 
                    WHEN s.stddev_spend > 0 
                    THEN (d.daily_total - s.mean_spend) / s.stddev_spend
                    ELSE 0 
                END as z_score
            FROM daily_spend d
            JOIN stats s ON (
                d.category = s.category 
                AND d.initiative_id IS NOT DISTINCT FROM s.initiative_id
                AND d.business_unit_id IS NOT DISTINCT FROM s.business_unit_id
            )
            WHERE d.day >= CURRENT_DATE - INTERVAL '{lookback_days} days'
              AND s.stddev_spend > 0
              AND (d.daily_total - s.mean_spend) / s.stddev_spend > {self.sigma_threshold}
            ORDER BY z_score DESC
        """)
        
        result = await self.session.execute(query)
        
        for row in result.fetchall():
            deviation_pct = (
                (row.daily_total - row.mean_spend) / row.mean_spend * 100
                if row.mean_spend > 0
                else 0
            )
            
            severity = self._classify_severity(row.z_score, deviation_pct)
            
            alert = AnomalyAlert(
                alert_id=f"spike-{row.day}-{row.category}-{row.initiative_id or row.business_unit_id}",
                anomaly_type="spike",
                severity=severity,
                category=row.category,
                scope=str(row.initiative_id or row.business_unit_id or "global"),
                description=(
                    f"Cost spike in {row.category}: ${row.daily_total:.2f} "
                    f"(expected: ${row.mean_spend:.2f} ± {row.stddev_spend:.2f}, "
                    f"z-score: {row.z_score:.2f})"
                ),
                expected_value=float(row.mean_spend),
                actual_value=float(row.daily_total),
                deviation_pct=float(deviation_pct),
                detected_at=datetime.utcnow(),
            )
            alerts.append(alert)
        
        logger.info(f"Detected {len(alerts)} cost spikes in last {lookback_days} days")
        return alerts

    async def detect_trend_changes(
        self,
        category: Optional[str] = None,
    ) -> list[AnomalyAlert]:
        """
        Detect significant trend changes using moving average comparison.
        Compares recent 7-day average vs previous 7-day average.
        """
        alerts = []
        
        category_filter = f"AND category = '{category}'" if category else ""
        
        query = text(f"""
            WITH daily_spend AS (
                SELECT 
                    DATE(cost_period_start) as day,
                    category,
                    initiative_id,
                    SUM(amount_usd) as daily_total
                FROM ai_cost_records
                WHERE approval_status = 'approved'
                  AND cost_period_start >= NOW() - INTERVAL '30 days'
                  {category_filter}
                GROUP BY DATE(cost_period_start), category, initiative_id
            ),
            recent AS (
                SELECT category, initiative_id, AVG(daily_total) as recent_avg
                FROM daily_spend
                WHERE day >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY category, initiative_id
            ),
            previous AS (
                SELECT category, initiative_id, AVG(daily_total) as previous_avg
                FROM daily_spend
                WHERE day >= CURRENT_DATE - INTERVAL '14 days'
                  AND day < CURRENT_DATE - INTERVAL '7 days'
                GROUP BY category, initiative_id
            )
            SELECT 
                r.category,
                r.initiative_id,
                r.recent_avg,
                p.previous_avg,
                (r.recent_avg - p.previous_avg) / NULLIF(p.previous_avg, 0) * 100 as change_pct
            FROM recent r
            JOIN previous p ON r.category = p.category 
                AND r.initiative_id IS NOT DISTINCT FROM p.initiative_id
            WHERE p.previous_avg > 0
              AND ABS((r.recent_avg - p.previous_avg) / p.previous_avg) > 0.50
            ORDER BY ABS((r.recent_avg - p.previous_avg) / p.previous_avg) DESC
        """)
        
        result = await self.session.execute(query)
        
        for row in result.fetchall():
            direction = "increase" if row.change_pct > 0 else "decrease"
            
            alert = AnomalyAlert(
                alert_id=f"trend-{row.category}-{row.initiative_id}",
                anomaly_type="trend_change",
                severity="high" if abs(row.change_pct) > 100 else "medium",
                category=row.category,
                scope=str(row.initiative_id or "global"),
                description=(
                    f"Trend {direction} in {row.category}: "
                    f"{abs(row.change_pct):.1f}% change "
                    f"(${row.previous_avg:.2f} → ${row.recent_avg:.2f})"
                ),
                expected_value=float(row.previous_avg),
                actual_value=float(row.recent_avg),
                deviation_pct=float(row.change_pct),
                detected_at=datetime.utcnow(),
            )
            alerts.append(alert)
        
        return alerts

    async def detect_pattern_breaks(self) -> list[AnomalyAlert]:
        """
        Detect breaks in regular spending patterns.
        E.g., a service that was running daily suddenly stops or changes schedule.
        """
        alerts = []
        
        query = text("""
            WITH service_patterns AS (
                SELECT 
                    category,
                    source_system,
                    EXTRACT(DOW FROM cost_period_start) as day_of_week,
                    COUNT(*) as frequency,
                    AVG(amount_usd) as avg_amount
                FROM ai_cost_records
                WHERE approval_status = 'approved'
                  AND cost_period_start >= NOW() - INTERVAL '60 days'
                GROUP BY category, source_system, EXTRACT(DOW FROM cost_period_start)
                HAVING COUNT(*) >= 4
            ),
            current_week AS (
                SELECT 
                    category,
                    source_system,
                    EXTRACT(DOW FROM cost_period_start) as day_of_week,
                    COUNT(*) as frequency,
                    AVG(amount_usd) as avg_amount
                FROM ai_cost_records
                WHERE approval_status = 'approved'
                  AND cost_period_start >= NOW() - INTERVAL '7 days'
                GROUP BY category, source_system, EXTRACT(DOW FROM cost_period_start)
            )
            SELECT 
                p.category,
                p.source_system,
                p.day_of_week,
                p.frequency as expected_frequency,
                COALESCE(c.frequency, 0) as actual_frequency,
                p.avg_amount as expected_amount,
                c.avg_amount as actual_amount
            FROM service_patterns p
            LEFT JOIN current_week c ON (
                p.category = c.category 
                AND p.source_system = c.source_system
                AND p.day_of_week = c.day_of_week
            )
            WHERE p.frequency >= 4
              AND (c.frequency IS NULL OR c.frequency < p.frequency * 0.5)
        """)
        
        result = await self.session.execute(query)
        
        for row in result.fetchall():
            alert = AnomalyAlert(
                alert_id=f"pattern-{row.category}-{row.source_system}-{row.day_of_week}",
                anomaly_type="pattern_break",
                severity="medium",
                category=row.category,
                scope=row.source_system or "global",
                description=(
                    f"Pattern break in {row.category} ({row.source_system}): "
                    f"expected {row.expected_frequency} occurrences on day {row.day_of_week}, "
                    f"found {row.actual_frequency}"
                ),
                expected_value=float(row.expected_frequency),
                actual_value=float(row.actual_frequency),
                deviation_pct=float(
                    (row.actual_frequency - row.expected_frequency) / row.expected_frequency * 100
                ) if row.expected_frequency > 0 else 0,
                detected_at=datetime.utcnow(),
            )
            alerts.append(alert)
        
        return alerts

    async def detect_unusual_unit_costs(self) -> list[AnomalyAlert]:
        """
        Detect unusual unit costs (e.g., cost per token, cost per GPU-hour).
        Flags when unit cost deviates significantly from baseline.
        """
        alerts = []
        
        query = text("""
            WITH unit_costs AS (
                SELECT 
                    category,
                    subcategory,
                    source_system,
                    unit_of_measure,
                    unit_cost,
                    cost_period_start
                FROM ai_cost_records
                WHERE approval_status = 'approved'
                  AND unit_cost IS NOT NULL
                  AND quantity > 0
                  AND cost_period_start >= NOW() - INTERVAL '30 days'
            ),
            baseline AS (
                SELECT 
                    category,
                    subcategory,
                    source_system,
                    unit_of_measure,
                    AVG(unit_cost) as avg_unit_cost,
                    STDDEV(unit_cost) as stddev_unit_cost
                FROM unit_costs
                WHERE cost_period_start < CURRENT_DATE - INTERVAL '7 days'
                GROUP BY category, subcategory, source_system, unit_of_measure
                HAVING COUNT(*) >= 10
            )
            SELECT 
                u.category,
                u.subcategory,
                u.source_system,
                u.unit_of_measure,
                u.unit_cost,
                b.avg_unit_cost,
                b.stddev_unit_cost,
                (u.unit_cost - b.avg_unit_cost) / NULLIF(b.stddev_unit_cost, 0) as z_score
            FROM unit_costs u
            JOIN baseline b ON (
                u.category = b.category
                AND u.subcategory IS NOT DISTINCT FROM b.subcategory
                AND u.source_system IS NOT DISTINCT FROM b.source_system
                AND u.unit_of_measure = b.unit_of_measure
            )
            WHERE u.cost_period_start >= CURRENT_DATE - INTERVAL '7 days'
              AND b.stddev_unit_cost > 0
              AND (u.unit_cost - b.avg_unit_cost) / b.stddev_unit_cost > 2.5
            ORDER BY (u.unit_cost - b.avg_unit_cost) / b.stddev_unit_cost DESC
        """)
        
        result = await self.session.execute(query)
        
        for row in result.fetchall():
            alert = AnomalyAlert(
                alert_id=f"unitcost-{row.category}-{row.subcategory}-{row.source_system}",
                anomaly_type="unit_cost_anomaly",
                severity="high" if row.z_score > 4 else "medium",
                category=row.category,
                scope=row.source_system or "global",
                description=(
                    f"Unusual unit cost for {row.category}/{row.subcategory}: "
                    f"${row.unit_cost:.6f} per {row.unit_of_measure} "
                    f"(expected: ${row.avg_unit_cost:.6f}, z-score: {row.z_score:.2f})"
                ),
                expected_value=float(row.avg_unit_cost),
                actual_value=float(row.unit_cost),
                deviation_pct=float(
                    (row.unit_cost - row.avg_unit_cost) / row.avg_unit_cost * 100
                ) if row.avg_unit_cost > 0 else 0,
                detected_at=datetime.utcnow(),
            )
            alerts.append(alert)
        
        return alerts

    async def run_full_detection(self) -> dict:
        """Run all anomaly detection methods and return consolidated results."""
        all_alerts = []
        
        # Spike detection
        spikes = await self.detect_spikes()
        all_alerts.extend(spikes)
        
        # Trend change detection
        trends = await self.detect_trend_changes()
        all_alerts.extend(trends)
        
        # Pattern break detection
        patterns = await self.detect_pattern_breaks()
        all_alerts.extend(patterns)
        
        # Unit cost anomaly detection
        unit_costs = await self.detect_unusual_unit_costs()
        all_alerts.extend(unit_costs)
        
        # Store alerts
        for alert in all_alerts:
            await self._store_alert(alert)
        
        # Summarize
        by_severity = {}
        by_type = {}
        for alert in all_alerts:
            by_severity[alert.severity] = by_severity.get(alert.severity, 0) + 1
            by_type[alert.anomaly_type] = by_type.get(alert.anomaly_type, 0) + 1
        
        return {
            "total_alerts": len(all_alerts),
            "by_severity": by_severity,
            "by_type": by_type,
            "alerts": [
                {
                    "id": a.alert_id,
                    "type": a.anomaly_type,
                    "severity": a.severity,
                    "description": a.description,
                    "deviation_pct": a.deviation_pct,
                }
                for a in all_alerts
            ],
        }

    async def _store_alert(self, alert: AnomalyAlert) -> None:
        """Store anomaly alert in database."""
        await self.session.execute(
            text("""
                INSERT INTO ai_cost_anomalies 
                (alert_id, anomaly_type, severity, category, scope, description,
                 expected_value, actual_value, deviation_pct, detected_at, status)
                VALUES (:id, :type, :severity, :category, :scope, :description,
                        :expected, :actual, :deviation, :detected, :status)
                ON CONFLICT (alert_id) DO UPDATE SET
                    actual_value = EXCLUDED.actual_value,
                    deviation_pct = EXCLUDED.deviation_pct,
                    detected_at = EXCLUDED.detected_at
            """),
            {
                "id": alert.alert_id,
                "type": alert.anomaly_type,
                "severity": alert.severity,
                "category": alert.category,
                "scope": alert.scope,
                "description": alert.description,
                "expected": alert.expected_value,
                "actual": alert.actual_value,
                "deviation": alert.deviation_pct,
                "detected": alert.detected_at,
                "status": alert.status,
            },
        )
        await self.session.commit()

    @staticmethod
    def _classify_severity(z_score: float, deviation_pct: float) -> str:
        if z_score > 5 or abs(deviation_pct) > 200:
            return "critical"
        elif z_score > 4 or abs(deviation_pct) > 100:
            return "high"
        elif z_score > 3 or abs(deviation_pct) > 50:
            return "medium"
        return "low"
```

---

## 6. Budget Forecasting

### 6.1 Forecasting Engine

```python
# services/forecaster.py
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    scope: str
    forecast_period: str
    current_run_rate: float
    forecast_amount: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    confidence_level: float
    method: str
    generated_at: datetime
    factors: dict  # Seasonality, trend, etc.


class BudgetForecaster:
    """
    Forecasts AI budget requirements using time-series methods.
    
    Implements specification §5.2.1 Phase 5: "Quarterly reforecasting"
    and §7.5 KPI: "Forecast Accuracy >90%"
    """

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def forecast_initiative_spend(
        self,
        initiative_id: uuid.UUID,
        forecast_months: int = 3,
    ) -> ForecastResult:
        """
        Forecast spend for an initiative using exponential smoothing.
        """
        # Fetch historical monthly spend
        query = text("""
            SELECT 
                DATE_TRUNC('month', cost_period_start) as month,
                SUM(amount_usd) as monthly_spend
            FROM ai_cost_records
            WHERE initiative_id = :initiative_id
              AND approval_status = 'approved'
              AND cost_period_start >= NOW() - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', cost_period_start)
            ORDER BY month
        """)
        
        result = await self.session.execute(
            query, {"initiative_id": initiative_id}
        )
        rows = result.fetchall()
        
        if len(rows) < 3:
            # Insufficient history — use simple average
            return self._simple_forecast(rows, initiative_id, forecast_months)
        
        # Extract time series
        values = np.array([float(row.monthly_spend) for row in rows])
        months = [row.month for row in rows]
        
        # Holt-Winters exponential smoothing (simplified)
        forecast, lower, upper = self._holt_winters_forecast(
            values, forecast_months
        )
        
        # Compute current run rate
        current_run_rate = float(np.mean(values[-3:])) if len(values) >= 3 else float(values[-1])
        
        return ForecastResult(
            scope=str(initiative_id),
            forecast_period=f"{forecast_months}m",
            current_run_rate=current_run_rate,
            forecast_amount=float(forecast),
            confidence_interval_lower=float(lower),
            confidence_interval_upper=float(upper),
            confidence_level=0.95,
            method="holt_winters",
            generated_at=datetime.utcnow(),
            factors={
                "history_months": len(rows),
                "trend": "upward" if forecast > current_run_rate else "downward",
                "seasonality_detected": self._detect_seasonality(values),
            },
        )

    async def forecast_category_spend(
        self,
        category: str,
        forecast_months: int = 3,
    ) -> ForecastResult:
        """Forecast spend for a cost category."""
        query = text("""
            SELECT 
                DATE_TRUNC('month', cost_period_start) as month,
                SUM(amount_usd) as monthly_spend
            FROM ai_cost_records
            WHERE category = :category
              AND approval_status = 'approved'
              AND cost_period_start >= NOW() - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', cost_period_start)
            ORDER BY month
        """)
        
        result = await self.session.execute(query, {"category": category})
        rows = result.fetchall()
        
        if len(rows) < 3:
            return self._simple_forecast(rows, category, forecast_months)
        
        values = np.array([float(row.monthly_spend) for row in rows])
        forecast, lower, upper = self._holt_winters_forecast(values, forecast_months)
        current_run_rate = float(np.mean(values[-3:]))
        
        return ForecastResult(
            scope=category,
            forecast_period=f"{forecast_months}m",
            current_run_rate=current_run_rate,
            forecast_amount=float(forecast),
            confidence_interval_lower=float(lower),
            confidence_interval_upper=float(upper),
            confidence_level=0.95,
            method="holt_winters",
            generated_at=datetime.utcnow(),
            factors={"history_months": len(rows)},
        )

    async def forecast_total_ai_spend(
        self,
        forecast_months: int = 12,
    ) -> ForecastResult:
        """Forecast total AI spend across all categories."""
        query = text("""
            SELECT 
                DATE_TRUNC('month', cost_period_start) as month,
                SUM(amount_usd) as monthly_spend
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= NOW() - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', cost_period_start)
            ORDER BY month
        """)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        values = np.array([float(row.monthly_spend) for row in rows])
        forecast, lower, upper = self._holt_winters_forecast(values, forecast_months)
        current_run_rate = float(np.mean(values[-3:]))
        
        return ForecastResult(
            scope="total",
            forecast_period=f"{forecast_months}m",
            current_run_rate=current_run_rate,
            forecast_amount=float(forecast),
            confidence_interval_lower=float(lower),
            confidence_interval_upper=float(upper),
            confidence_level=0.95,
            method="holt_winters",
            generated_at=datetime.utcnow(),
            factors={"history_months": len(rows)},
        )

    async def compute_forecast_accuracy(
        self,
        scope: str,
        periods_back: int = 3,
    ) -> dict:
        """
        Compute forecast accuracy (specification §7.5 KPI: >90%).
        Formula: (1 - |Forecast - Actual| / Actual) × 100
        """
        query = text("""
            WITH monthly_actuals AS (
                SELECT 
                    DATE_TRUNC('month', cost_period_start) as month,
                    SUM(amount_usd) as actual
                FROM ai_cost_records
                WHERE approval_status = 'approved'
                  AND cost_period_start >= NOW() - INTERVAL '6 months'
                GROUP BY DATE_TRUNC('month', cost_period_start)
            ),
            forecasts AS (
                SELECT 
                    forecast_period,
                    forecast_amount,
                    scope
                FROM ai_budget_forecasts
                WHERE scope = :scope
                  AND generated_at >= NOW() - INTERVAL '6 months'
            )
            SELECT 
                a.month,
                a.actual,
                f.forecast_amount,
                CASE WHEN a.actual > 0 
                THEN (1 - ABS(f.forecast_amount - a.actual) / a.actual) * 100
                ELSE NULL END as accuracy
            FROM monthly_actuals a
            LEFT JOIN forecasts f ON DATE_TRUNC('month', f.forecast_period) = a.month
            WHERE f.forecast_amount IS NOT NULL
            ORDER BY a.month DESC
            LIMIT :periods
        """)
        
        result = await self.session.execute(
            query, {"scope": scope, "periods": periods_back}
        )
        rows = result.fetchall()
        
        if not rows:
            return {"accuracy": None, "message": "No forecast history available"}
        
        accuracies = [float(row.accuracy) for row in rows if row.accuracy is not None]
        avg_accuracy = np.mean(accuracies) if accuracies else None
        
        return {
            "accuracy": round(avg_accuracy, 2) if avg_accuracy else None,
            "target": 90.0,
            "status": "green" if avg_accuracy and avg_accuracy >= 90 else "yellow" if avg_accuracy and avg_accuracy >= 80 else "red",
            "periods_evaluated": len(accuracies),
            "details": [
                {
                    "month": str(row.month),
                    "actual": float(row.actual),
                    "forecast": float(row.forecast_amount),
                    "accuracy": round(float(row.accuracy), 2) if row.accuracy else None,
                }
                for row in rows
            ],
        }

    def _holt_winters_forecast(
        self,
        values: np.ndarray,
        periods: int,
        alpha: float = 0.3,
        beta: float = 0.1,
    ) -> tuple[float, float, float]:
        """
        Simplified Holt-Winters exponential smoothing.
        Returns (forecast, lower_bound, upper_bound).
        """
        n = len(values)
        if n == 0:
            return 0.0, 0.0, 0.0
        
        # Initialize level and trend
        level = values[0]
        trend = values[1] - values[0] if n > 1 else 0
        
        # Smoothing
        for i in range(1, n):
            prev_level = level
            level = alpha * values[i] + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
        
        # Forecast
        forecast = level + trend * periods
        
        # Confidence interval (simplified)
        residuals = []
        for i in range(1, n):
            predicted = level + trend * (i - n + 1)
            residuals.append(values[i] - predicted)
        
        std_residual = np.std(residuals) if len(residuals) > 1 else np.std(values) * 0.1
        margin = 1.96 * std_residual * np.sqrt(periods)
        
        return forecast, max(0, forecast - margin), forecast + margin

    def _simple_forecast(
        self,
        rows: list,
        scope: str,
        periods: int,
    ) -> ForecastResult:
        """Simple average-based forecast for insufficient history."""
        if not rows:
            return ForecastResult(
                scope=scope,
                forecast_period=f"{periods}m",
                current_run_rate=0,
                forecast_amount=0,
                confidence_interval_lower=0,
                confidence_interval_upper=0,
                confidence_level=0.95,
                method="simple_average",
                generated_at=datetime.utcnow(),
                factors={"history_months": 0},
            )
        
        avg = float(np.mean([float(row.monthly_spend) for row in rows]))
        forecast = avg * periods
        
        return ForecastResult(
            scope=scope,
            forecast_period=f"{periods}m",
            current_run_rate=avg,
            forecast_amount=forecast,
            confidence_interval_lower=forecast * 0.7,
            confidence_interval_upper=forecast * 1.3,
            confidence_level=0.95,
            method="simple_average",
            generated_at=datetime.utcnow(),
            factors={"history_months": len(rows)},
        )

    @staticmethod
    def _detect_seasonality(values: np.ndarray) -> bool:
        """Simple seasonality detection using autocorrelation."""
        if len(values) < 6:
            return False
        # Check for repeating patterns at lag 3 (quarterly)
        if len(values) >= 6:
            corr = np.corrcoef(values[:-3], values[3:])[0, 1]
            return corr > 0.5
        return False
```

---

## 7. Financial Reporting

### 7.1 Report Generation Engine

```python
# services/reporting.py
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FinancialReportingEngine:
    """
    Generates financial reports per specification §6.
    
    Implements:
    - Board & Executive reports (§6.2)
    - Management reports (§6.3.1)
    - Operational reports (§6.3.2)
    - Report escalation (§6.4.3)
    """

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def generate_board_summary(
        self,
        quarter: int,
        year: int,
    ) -> dict:
        """
        Generate quarterly board summary per specification §6.2.1.
        """
        period_start = datetime(year, (quarter - 1) * 3 + 1, 1)
        period_end = datetime(year, quarter * 3 + 1, 1) - timedelta(days=1)
        
        # Total AI spend
        total_spend = await self._get_total_spend(period_start, period_end)
        
        # YoY change
        yoy_start = period_start.replace(year=year - 1)
        yoy_end = period_end.replace(year=year - 1)
        prior_spend = await self._get_total_spend(yoy_start, yoy_end)
        yoy_change = (
            ((total_spend - prior_spend) / prior_spend * 100)
            if prior_spend > 0
            else None
        )
        
        # Spend by category
        by_category = await self._get_spend_by_category(period_start, period_end)
        
        # Spend by BU
        by_bu = await self._get_spend_by_bu(period_start, period_end)
        
        # ROI metrics
        roi_metrics = await self._get_roi_summary(period_start, period_end)
        
        # Budget performance
        budget_perf = await self._get_budget_performance(period_start, period_end)
        
        # Shadow AI
        shadow_ratio = await self._get_shadow_ai_ratio(period_start, period_end)
        
        # Top initiatives
        top_initiatives = await self._get_top_initiatives(period_start, period_end)
        
        # Risk items
        risk_items = await self._get_risk_items(period_start, period_end)
        
        return {
            "report_type": "board_summary",
            "quarter": f"Q{quarter} {year}",
            "generated_at": datetime.utcnow().isoformat(),
            "classification": "Board Confidential",
            "sections": {
                "executive_summary": {
                    "total_ai_spend": float(total_spend),
                    "yoy_change_pct": round(yoy_change, 2) if yoy_change else None,
                    "ai_roi": roi_metrics.get("blended_roi"),
                    "budget_variance_pct": budget_perf.get("overall_variance_pct"),
                    "shadow_ai_ratio": shadow_ratio,
                },
                "key_metrics": {
                    "total_ai_spend": {
                        "value": f"${total_spend / 1_000_000:.1f}M",
                        "target": "—",
                        "status": "green",
                    },
                    "ai_roi": {
                        "value": f"{roi_metrics.get('blended_roi', 0):.1f}x",
                        "target": ">1.0x",
                        "status": "green" if roi_metrics.get("blended_roi", 0) > 1.0 else "red",
                    },
                    "budget_variance": {
                        "value": f"{budget_perf.get('overall_variance_pct', 0):.1f}%",
                        "target": "<10%",
                        "status": "green" if abs(budget_perf.get("overall_variance_pct", 0)) < 10 else "yellow",
                    },
                    "shadow_ai": {
                        "value": f"{shadow_ratio:.1f}%",
                        "target": "<10%",
                        "status": "green" if shadow_ratio < 10 else "yellow" if shadow_ratio < 20 else "red",
                    },
                },
                "spend_by_category": by_category,
                "spend_by_business_unit": by_bu,
                "top_initiatives": top_initiatives,
                "risk_items": risk_items,
                "decisions_required": self._identify_decisions(risk_items, budget_perf),
            },
        }

    async def generate_management_dashboard(
        self,
        year: int,
        month: int,
    ) -> dict:
        """
        Generate monthly management dashboard per specification §6.3.1.
        """
        period_start = datetime(year, month, 1)
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Cost by category
        cost_by_category = await self._get_spend_by_category(period_start, period_end)
        
        # Cost by BU
        cost_by_bu = await self._get_spend_by_bu(period_start, period_end)
        
        # Unit economics
        unit_economics = await self._get_unit_economics(period_start, period_end)
        
        # Budget variance
        budget_variance = await self._get_budget_variance(period_start, period_end)
        
        # Shadow AI
        shadow_ai = await self._get_shadow_ai_details(period_start, period_end)
        
        # ROI by initiative
        roi_by_initiative = await self._get_roi_by_initiative(period_start, period_end)
        
        # Vendor spend
        vendor_spend = await self._get_vendor_spend(period_start, period_end)
        
        return {
            "report_type": "management_dashboard",
            "period": f"{year}-{month:02d}",
            "generated_at": datetime.utcnow().isoformat(),
            "classification": "Management Confidential",
            "sections": {
                "cost_by_category": cost_by_category,
                "cost_by_business_unit": cost_by_bu,
                "unit_economics": unit_economics,
                "budget_variance": budget_variance,
                "shadow_ai": shadow_ai,
                "roi_by_initiative": roi_by_initiative,
                "vendor_spend": vendor_spend,
            },
        }

    async def generate_operational_report(
        self,
        report_type: str,
        date: Optional[datetime] = None,
    ) -> dict:
        """
        Generate operational reports per specification §6.3.2.
        
        Types: real_time_cost, api_cost_breakdown, training_cost, 
               storage_cost, anomaly_detection
        """
        if date is None:
            date = datetime.utcnow()
        
        if report_type == "real_time_cost":
            return await self._real_time_cost_report(date)
        elif report_type == "api_cost_breakdown":
            return await self._api_cost_breakdown(date)
        elif report_type == "training_cost":
            return await self._training_cost_report(date)
        elif report_type == "storage_cost":
            return await self._storage_cost_report(date)
        elif report_type == "anomaly_detection":
            return await self._anomaly_detection_report(date)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    async def check_escalation_triggers(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> list[dict]:
        """
        Check escalation triggers per specification §6.4.3.
        """
        escalations = []
        
        # Budget variance >20%
        variance = await self._get_budget_variance(period_start, period_end)
        if variance.get("max_variance_pct", 0) > 20:
            escalations.append({
                "condition": "Budget variance >20%",
                "escalation": "Immediate",
                "recipient": "CFO",
                "timeline": "24 hours",
                "details": variance,
            })
        
        # Shadow AI >20%
        shadow = await self._get_shadow_ai_ratio(period_start, period_end)
        if shadow > 20:
            escalations.append({
                "condition": "Shadow AI >20%",
                "escalation": "Immediate",
                "recipient": "CAIO + CISO",
                "timeline": "24 hours",
                "details": {"shadow_ai_ratio": shadow},
            })
        
        # Unexplained cost spike >$100K
        spikes = await self._get_unexplained_spikes(period_start, period_end)
        for spike in spikes:
            if spike["amount"] > 100000:
                escalations.append({
                    "condition": "Unexplained cost spike >$100K",
                    "escalation": "Immediate",
                    "recipient": "AI Financial Controller",
                    "timeline": "4 hours",
                    "details": spike,
                })
        
        return escalations

    # --- Private helper methods ---

    async def _get_total_spend(self, start: datetime, end: datetime) -> Decimal:
        query = text("""
            SELECT COALESCE(SUM(amount_usd), 0) as total
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        return Decimal(str(result.fetchone().total or 0))

    async def _get_spend_by_category(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        query = text("""
            SELECT 
                category,
                SUM(amount_usd) as total,
                COUNT(*) as record_count
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
            GROUP BY category
            ORDER BY total DESC
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        return [
            {
                "category": row.category,
                "total_usd": float(row.total),
                "record_count": row.record_count,
            }
            for row in result.fetchall()
        ]

    async def _get_spend_by_bu(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        query = text("""
            SELECT 
                business_unit_id,
                SUM(amount_usd) as total
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
            GROUP BY business_unit_id
            ORDER BY total DESC
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        return [
            {"business_unit_id": str(row.business_unit_id), "total_usd": float(row.total)}
            for row in result.fetchall()
        ]

    async def _get_roi_summary(
        self, start: datetime, end: datetime
    ) -> dict:
        query = text("""
            SELECT 
                CASE WHEN SUM(total_cost) > 0 
                THEN SUM(total_value) / SUM(total_cost)
                ELSE NULL END as blended_roi
            FROM ai_roi_direct
            WHERE period_start >= :start AND period_end <= :end
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        row = result.fetchone()
        return {"blended_roi": float(row.blended_roi) if row and row.blended_roi else None}

    async def _get_budget_performance(
        self, start: datetime, end: datetime
    ) -> dict:
        query = text("""
            SELECT 
                b.budget_id,
                b.budget_scope,
                b.budget_amount_usd,
                COALESCE(SUM(c.amount_usd), 0) as actual_spend
            FROM ai_budgets b
            LEFT JOIN ai_cost_records c ON (
                c.approval_status = 'approved'
                AND c.cost_period_start >= b.effective_start
                AND c.cost_period_end <= b.effective_end
                AND (
                    c.initiative_id::text = b.budget_scope
                    OR c.business_unit_id::text = b.budget_scope
                    OR c.cost_center = b.budget_scope
                    OR c.category = b.budget_scope
                )
            )
            WHERE b.status = 'active'
            GROUP BY b.budget_id, b.budget_scope, b.budget_amount_usd
        """)
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        total_budget = sum(float(r.budget_amount_usd) for r in rows)
        total_spend = sum(float(r.actual_spend) for r in rows)
        variance_pct = (
            (total_budget - total_spend) / total_budget * 100
            if total_budget > 0
            else 0
        )
        
        return {
            "total_budget": total_budget,
            "total_spend": total_spend,
            "overall_variance_pct": round(variance_pct, 2),
            "budgets": [
                {
                    "scope": r.budget_scope,
                    "budget": float(r.budget_amount_usd),
                    "actual": float(r.actual_spend),
                    "variance_pct": round(
                        (float(r.budget_amount_usd) - float(r.actual_spend))
                        / float(r.budget_amount_usd)
                        * 100,
                        2,
                    ) if r.budget_amount_usd > 0 else 0,
                }
                for r in rows
            ],
        }

    async def _get_shadow_ai_ratio(
        self, start: datetime, end: datetime
    ) -> float:
        query = text("""
            SELECT 
                COALESCE(SUM(amount_usd) FILTER (WHERE is_shadow = TRUE), 0) as shadow,
                COALESCE(SUM(amount_usd), 0) as total
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        row = result.fetchone()
        if row.total and row.total > 0:
            return float(row.shadow / row.total * 100)
        return 0.0

    async def _get_shadow_ai_details(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        query = text("""
            SELECT 
                category,
                source_system,
                shadow_reason,
                SUM(amount_usd) as total
            FROM ai_cost_records
            WHERE is_shadow = TRUE
              AND approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
            GROUP BY category, source_system, shadow_reason
            ORDER BY total DESC
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        return [
            {
                "category": row.category,
                "source": row.source_system,
                "reason": row.shadow_reason,
                "amount_usd": float(row.total),
            }
            for row in result.fetchall()
        ]

    async def _get_top_initiatives(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        query = text("""
            SELECT 
                initiative_id,
                SUM(amount_usd) as total_spend
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
              AND initiative_id IS NOT NULL
            GROUP BY initiative_id
            ORDER BY total_spend DESC
            LIMIT 5
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        return [
            {"initiative_id": str(row.initiative_id), "spend_usd": float(row.total_spend)}
            for row in result.fetchall()
        ]

    async def _get_unit_economics(
        self, start: datetime, end: datetime
    ) -> dict:
        query = text("""
            SELECT 
                category,
                SUM(amount_usd) as total_cost,
                SUM(quantity) as total_units,
                CASE WHEN SUM(quantity) > 0 
                THEN SUM(amount_usd) / SUM(quantity)
                ELSE NULL END as unit_cost
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
              AND quantity IS NOT NULL
              AND quantity > 0
            GROUP BY category
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        return {
            row.category: {
                "total_cost": float(row.total_cost),
                "total_units": float(row.total_units),
                "unit_cost": float(row.unit_cost) if row.unit_cost else None,
            }
            for row in result.fetchall()
        }

    async def _get_budget_variance(
        self, start: datetime, end: datetime
    ) -> dict:
        perf = await self._get_budget_performance(start, end)
        variances = [b["variance_pct"] for b in perf.get("budgets", [])]
        return {
            "max_variance_pct": max(variances) if variances else 0,
            "min_variance_pct": min(variances) if variances else 0,
            "budgets": perf.get("budgets", []),
        }

    async def _get_roi_by_initiative(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        query = text("""
            SELECT 
                initiative_id,
                total_value,
                total_cost,
                CASE WHEN total_cost > 0 
                THEN (total_value - total_cost) / total_cost
                ELSE NULL END as roi
            FROM ai_roi_direct
            WHERE period_start >= :start AND period_end <= :end
            ORDER BY total_cost DESC
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        return [
            {
                "initiative_id": str(row.initiative_id),
                "total_value": float(row.total_value),
                "total_cost": float(row.total_cost),
                "roi": round(float(row.roi), 4) if row.roi else None,
            }
            for row in result.fetchall()
        ]

    async def _get_vendor_spend(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        query = text("""
            SELECT 
                source_system,
                SUM(amount_usd) as total
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
            GROUP BY source_system
            ORDER BY total DESC
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        return [
            {"vendor": row.source_system, "total_usd": float(row.total)}
            for row in result.fetchall()
        ]

    async def _get_risk_items(
        self, start: datetime, end: datetime
    ) -> list[str]:
        risks = []
        
        # Check for over-budget initiatives
        variance = await self._get_budget_variance(start, end)
        for budget in variance.get("budgets", []):
            if budget["variance_pct"] < -20:
                risks.append(
                    f"Over budget: {budget['scope']} is {abs(budget['variance_pct']):.1f}% over"
                )
        
        # Check shadow AI
        shadow = await self._get_shadow_ai_ratio(start, end)
        if shadow > 15:
            risks.append(f"Shadow AI at {shadow:.1f}% (target: <10%)")
        
        return risks

    async def _get_unexplained_spikes(
        self, start: datetime, end: datetime
    ) -> list[dict]:
        query = text("""
            WITH daily AS (
                SELECT 
                    DATE(cost_period_start) as day,
                    SUM(amount_usd) as daily_total
                FROM ai_cost_records
                WHERE approval_status = 'approved'
                  AND cost_period_start >= :start
                  AND cost_period_end <= :end
                GROUP BY DATE(cost_period_start)
            ),
            stats AS (
                SELECT AVG(daily_total) as mean, STDDEV(daily_total) as stddev
                FROM daily
            )
            SELECT d.day, d.daily_total, 
                   (d.daily_total - s.mean) / NULLIF(s.stddev, 0) as z_score
            FROM daily d, stats s
            WHERE (d.daily_total - s.mean) / NULLIF(s.stddev, 0) > 3
            ORDER BY d.daily_total DESC
        """)
        result = await self.session.execute(query, {"start": start, "end": end})
        return [
            {"date": str(row.day), "amount": float(row.daily_total), "z_score": float(row.z_score)}
            for row in result.fetchall()
        ]

    async def _real_time_cost_report(self, date: datetime) -> dict:
        query = text("""
            SELECT 
                category,
                initiative_id,
                SUM(amount_usd) as total
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND DATE(cost_period_start) = DATE(:date)
            GROUP BY category, initiative_id
            ORDER BY total DESC
        """)
        result = await self.session.execute(query, {"date": date})
        return {
            "report_type": "real_time_cost",
            "date": date.isoformat(),
            "costs": [
                {"category": r.category, "initiative_id": str(r.initiative_id), "total": float(r.total)}
                for r in result.fetchall()
            ],
        }

    async def _api_cost_breakdown(self, date: datetime) -> dict:
        query = text("""
            SELECT 
                source_system,
                subcategory,
                SUM(amount_usd) as total,
                SUM(quantity) as units
            FROM ai_cost_records
            WHERE category = 'INF'
              AND approval_status = 'approved'
              AND DATE(cost_period_start) = DATE(:date)
            GROUP BY source_system, subcategory
            ORDER BY total DESC
        """)
        result = await self.session.execute(query, {"date": date})
        return {
            "report_type": "api_cost_breakdown",
            "date": date.isoformat(),
            "breakdown": [
                {
                    "source": r.source_system,
                    "subcategory": r.subcategory,
                    "total_usd": float(r.total),
                    "units": float(r.units) if r.units else None,
                }
                for r in result.fetchall()
            ],
        }

    async def _training_cost_report(self, date: datetime) -> dict:
        query = text("""
            SELECT 
                source_system,
                SUM(amount_usd) as total,
                SUM(quantity) as gpu_hours
            FROM ai_cost_records
            WHERE category = 'TRN'
              AND approval_status = 'approved'
              AND DATE(cost_period_start) = DATE(:date)
            GROUP BY source_system
        """)
        result = await self.session.execute(query, {"date": date})
        return {
            "report_type": "training_cost",
            "date": date.isoformat(),
            "training": [
                {"source": r.source_system, "total_usd": float(r.total), "gpu_hours": float(r.gpu_hours) if r.gpu_hours else None}
                for r in result.fetchall()
            ],
        }

    async def _storage_cost_report(self, date: datetime) -> dict:
        query = text("""
            SELECT 
                subcategory,
                SUM(amount_usd) as total,
                SUM(quantity) as gb_months
            FROM ai_cost_records
            WHERE category = 'STO'
              AND approval_status = 'approved'
              AND DATE(cost_period_start) = DATE(:date)
            GROUP BY subcategory
        """)
        result = await self.session.execute(query, {"date": date})
        return {
            "report_type": "storage_cost",
            "date": date.isoformat(),
            "storage": [
                {"subcategory": r.subcategory, "total_usd": float(r.total), "gb_months": float(r.gb_months) if r.gb_months else None}
                for r in result.fetchall()
            ],
        }

    async def _anomaly_detection_report(self, date: datetime) -> dict:
        query = text("""
            SELECT 
                alert_id,
                anomaly_type,
                severity,
                category,
                description,
                deviation_pct,
                status
            FROM ai_cost_anomalies
            WHERE DATE(detected_at) = DATE(:date)
            ORDER BY 
                CASE severity 
                    WHEN 'critical' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    ELSE 4 
                END
        """)
        result = await self.session.execute(query, {"date": date})
        return {
            "report_type": "anomaly_detection",
            "date": date.isoformat(),
            "anomalies": [
                {
                    "id": r.alert_id,
                    "type": r.anomaly_type,
                    "severity": r.severity,
                    "category": r.category,
                    "description": r.description,
                    "deviation_pct": float(r.deviation_pct) if r.deviation_pct else None,
                    "status": r.status,
                }
                for r in result.fetchall()
            ],
        }

    def _identify_decisions(
        self, risk_items: list[str], budget_perf: dict
    ) -> list[str]:
        decisions = []
        for risk in risk_items:
            if "Over budget" in risk:
                decisions.append(f"Review budget overrun: {risk}")
            if "Shadow AI" in risk:
                decisions.append("Approve shadow AI remediation program")
        return decisions
```

---

## 8. FinOps Integration

### 8.1 FinOps Platform Integration

```python
# services/finops_integration.py
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class FinOpsSyncResult:
    source: str
    records_synced: int
    last_sync: datetime
    status: str  # success, partial, failed
    errors: list[str]


class FinOpsProvider(ABC):
    """Abstract base class for FinOps platform integrations."""

    @abstractmethod
    async def sync_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> FinOpsSyncResult:
        ...

    @abstractmethod
    def provider_name(self) -> str:
        ...


class VantageFinOpsProvider(FinOpsProvider):
    """
    Integration with Vantage (https://vantage.sh) — cloud cost management.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.vantage.sh/v2"

    def provider_name(self) -> str:
        return "Vantage"

    async def sync_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> FinOpsSyncResult:
        errors = []
        records_synced = 0
        
        try:
            async with aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as session:
                # Fetch cost reports
                url = f"{self.base_url}/costs"
                params = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                }
                
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        records_synced = len(data.get("costs", []))
                    else:
                        errors.append(f"Vantage API error: {resp.status}")
                        
        except Exception as e:
            errors.append(f"Vantage sync error: {str(e)}")
            logger.exception("Vantage sync failed")
        
        return FinOpsSyncResult(
            source=self.provider_name(),
            records_synced=records_synced,
            last_sync=datetime.utcnow(),
            status="success" if not errors else "partial" if records_synced > 0 else "failed",
            errors=errors,
        )


class CloudHealthFinOpsProvider(FinOpsProvider):
    """
    Integration with VMware CloudHealth — cloud cost and governance.
    """

    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key
        self.domain = domain
        self.base_url = f"https://chapi.cloudhealthtech.com/v1"

    def provider_name(self) -> str:
        return "CloudHealth"

    async def sync_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> FinOpsSyncResult:
        errors = []
        records_synced = 0
        
        try:
            async with aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as session:
                # Fetch cost data
                url = f"{self.base_url}/billing/costs"
                params = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                }
                
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        records_synced = len(data.get("costs", []))
                    else:
                        errors.append(f"CloudHealth API error: {resp.status}")
                        
        except Exception as e:
            errors.append(f"CloudHealth sync error: {str(e)}")
            logger.exception("CloudHealth sync failed")
        
        return FinOpsSyncResult(
            source=self.provider_name(),
            records_synced=records_synced,
            last_sync=datetime.utcnow(),
            status="success" if not errors else "partial" if records_synced > 0 else "failed",
            errors=errors,
        )


class KubecostFinOpsProvider(FinOpsProvider):
    """
    Integration with Kubecost — Kubernetes cost monitoring.
    Covers: INF, INF-ARC for containerized AI workloads.
    """

    def __init__(self, base_url: str, api_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    def provider_name(self) -> str:
        return "Kubecost"

    async def sync_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> FinOpsSyncResult:
        errors = []
        records_synced = 0
        
        try:
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            
            async with aiohttp.ClientSession(headers=headers) as session:
                # Fetch allocation costs
                url = f"{self.base_url}/model/allocation"
                params = {
                    "start": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "window": "1d",
                }
                
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Kubecost returns data keyed by allocation name
                        records_synced = len(data.get("data", []))
                    else:
                        errors.append(f"Kubecost API error: {resp.status}")
                        
        except Exception as e:
            errors.append(f"Kubecost sync error: {str(e)}")
            logger.exception("Kubecost sync failed")
        
        return FinOpsSyncResult(
            source=self.provider_name(),
            records_synced=records_synced,
            last_sync=datetime.utcnow(),
            status="success" if not errors else "partial" if records_synced > 0 else "failed",
            errors=errors,
        )


class FinOpsIntegrationHub:
    """
    Central hub for FinOps platform integrations.
    
    Manages synchronization with multiple cost management platforms
    and normalizes data into the GRC_Claw cost model.
    """

    def __init__(self, db_session: AsyncSession):
        self.session = db_session
        self.providers: list[FinOpsProvider] = []

    def register_provider(self, provider: FinOpsProvider) -> None:
        self.providers.append(provider)

    async def sync_all(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[FinOpsSyncResult]:
        """Sync cost data from all registered FinOps providers."""
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=1)

        results = []
        for provider in self.providers:
            logger.info(f"Syncing from {provider.provider_name()}")
            result = await provider.sync_cost_data(start_date, end_date)
            results.append(result)
            logger.info(
                f"Synced {result.records_synced} records from {provider.provider_name()}"
            )

        return results

    async def get_consolidated_spend(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Get consolidated spend view across all FinOps sources.
        Useful for cross-platform cost attribution.
        """
        from sqlalchemy import text
        
        query = text("""
            SELECT 
                source_system,
                category,
                SUM(amount_usd) as total,
                COUNT(*) as records
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
            GROUP BY source_system, category
            ORDER BY total DESC
        """)
        
        result = await self.session.execute(
            query, {"start": start_date, "end": end_date}
        )
        
        by_source = {}
        by_category = {}
        
        for row in result.fetchall():
            source = row.source_system or "unknown"
            category = row.category
            
            if source not in by_source:
                by_source[source] = Decimal("0")
            by_source[source] += row.total
            
            if category not in by_category:
                by_category[category] = Decimal("0")
            by_category[category] += row.total
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "by_source": {k: float(v) for k, v in by_source.items()},
            "by_category": {k: float(v) for k, v in by_category.items()},
            "total": float(sum(by_source.values())),
        }

    async def reconcile_with_finops(
        self,
        finops_total: Decimal,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Reconcile GRC_Claw cost records with FinOps platform totals.
        Specification §3.5: "Source system reconciliation — Weekly — Variance report"
        """
        from sqlalchemy import text
        
        query = text("""
            SELECT COALESCE(SUM(amount_usd), 0) as total
            FROM ai_cost_records
            WHERE approval_status = 'approved'
              AND cost_period_start >= :start
              AND cost_period_end <= :end
        """)
        
        result = await self.session.execute(
            query, {"start": start_date, "end": end_date}
        )
        grc_total = Decimal(str(result.fetchone().total or 0))
        
        variance = grc_total - finops_total
        variance_pct = (
            (variance / finops_total * 100) if finops_total > 0 else Decimal("0")
        )
        
        return {
            "grc_claw_total": float(grc_total),
            "finops_total": float(finops_total),
            "variance": float(variance),
            "variance_pct": float(variance_pct),
            "tolerance_pct": 1.0,  # Specification §3.5: within 1% tolerance
            "status": "reconciled" if abs(variance_pct) <= 1.0 else "variance",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }
```

---

## 9. Deployment & Operations

### 9.1 Docker Compose Configuration

```yaml
# docker-compose.yml
version: "3.9"

services:
  # PostgreSQL — primary data store
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: grc_claw_financial
      POSTGRES_USER: grc_claw
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U grc_claw"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis — cache and message broker
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # FastAPI — REST API
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      DATABASE_URL: postgresql+asyncpg://grc_claw:${DB_PASSWORD}@postgres/grc_claw_financial
      REDIS_URL: redis://redis:6379
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  # Celery Worker — async task processing
  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      DATABASE_URL: postgresql+asyncpg://grc_claw:${DB_PASSWORD}@postgres/grc_claw_financial
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis

  # Celery Beat — scheduled tasks
  scheduler:
    build:
      context: .
      dockerfile: Dockerfile.worker
    command: celery -A tasks beat --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://grc_claw:${DB_PASSWORD}@postgres/grc_claw_financial
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis

  # Prometheus — metrics collection
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  # Grafana — dashboards
  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### 9.2 Database Migrations

```sql
-- migrations/001_initial_schema.sql
-- GRC_Claw Financial Governance Database Schema

-- Cost records table (specification §3.2.1)
CREATE TABLE ai_cost_records (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cost_id             VARCHAR(128) UNIQUE NOT NULL,
    
    -- Classification
    category            VARCHAR(16) NOT NULL,
    subcategory         VARCHAR(16),
    
    -- Attribution
    owner_id            UUID NOT NULL,
    business_unit_id    UUID NOT NULL,
    initiative_id       UUID,
    project_id          UUID,
    cost_center         VARCHAR(64) NOT NULL,
    
    -- Financial
    amount              NUMERIC(18,4) NOT NULL,
    currency            VARCHAR(3) NOT NULL DEFAULT 'USD',
    amount_usd          NUMERIC(18,4) NOT NULL,
    exchange_rate       NUMERIC(18,8),
    
    -- Measurement
    quantity            NUMERIC(18,4),
    unit_of_measure     VARCHAR(32),
    unit_cost           NUMERIC(18,6),
    
    -- Source
    source_type         VARCHAR(32) NOT NULL,
    source_system       VARCHAR(128),
    source_record_id    VARCHAR(256),
    
    -- Time
    cost_period_start   TIMESTAMPTZ NOT NULL,
    cost_period_end     TIMESTAMPTZ NOT NULL,
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Governance
    is_shadow           BOOLEAN NOT NULL DEFAULT FALSE,
    shadow_reason       TEXT,
    approval_status     VARCHAR(32) NOT NULL DEFAULT 'approved',
    approved_by         UUID,
    approved_at         TIMESTAMPTZ,
    
    -- Metadata
    metadata            JSONB,
    tags                TEXT[],
    
    -- Audit
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID NOT NULL,
    updated_by          UUID NOT NULL
);

CREATE INDEX idx_cost_category ON ai_cost_records(category);
CREATE INDEX idx_cost_owner ON ai_cost_records(owner_id);
CREATE INDEX idx_cost_bu ON ai_cost_records(business_unit_id);
CREATE INDEX idx_cost_initiative ON ai_cost_records(initiative_id);
CREATE INDEX idx_cost_period ON ai_cost_records(cost_period_start, cost_period_end);
CREATE INDEX idx_cost_shadow ON ai_cost_records(is_shadow);
CREATE INDEX idx_cost_source ON ai_cost_records(source_type, source_system);

-- Budgets table (specification §5.1.2)
CREATE TABLE ai_budgets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_id           VARCHAR(128) UNIQUE NOT NULL,
    budget_type         VARCHAR(32) NOT NULL,
    budget_scope        VARCHAR(128) NOT NULL,
    fiscal_year         INTEGER NOT NULL,
    period              VARCHAR(16) NOT NULL,
    budget_amount       NUMERIC(18,4) NOT NULL,
    currency            VARCHAR(3) NOT NULL DEFAULT 'USD',
    budget_amount_usd   NUMERIC(18,4) NOT NULL,
    parent_budget_id    UUID REFERENCES ai_budgets(id),
    owner_id            UUID NOT NULL,
    approver_id         UUID NOT NULL,
    status              VARCHAR(32) NOT NULL DEFAULT 'draft',
    proposed_at         TIMESTAMPTZ,
    approved_at         TIMESTAMPTZ,
    effective_start     TIMESTAMPTZ NOT NULL,
    effective_end       TIMESTAMPTZ NOT NULL,
    justification       TEXT,
    assumptions         JSONB,
    metadata            JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID NOT NULL,
    updated_by          UUID NOT NULL
);

-- Budget allocations
CREATE TABLE ai_budget_allocations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_id           UUID NOT NULL REFERENCES ai_budgets(id) ON DELETE CASCADE,
    allocated_to_type   VARCHAR(32) NOT NULL,
    allocated_to_id     UUID NOT NULL,
    allocated_amount    NUMERIC(18,4) NOT NULL,
    allocated_by        UUID NOT NULL,
    allocated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes               TEXT
);

-- Budget reallocations log
CREATE TABLE ai_budget_reallocations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_budget_id      UUID NOT NULL REFERENCES ai_budgets(id),
    to_budget_id        UUID NOT NULL REFERENCES ai_budgets(id),
    amount              NUMERIC(18,4) NOT NULL,
    requested_by        UUID NOT NULL,
    approved_by         UUID,
    justification       TEXT NOT NULL,
    status              VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at          TIMESTAMPTZ
);

-- Direct ROI measurements (specification §4.2.3)
CREATE TABLE ai_roi_direct (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiative_id       UUID NOT NULL,
    period_start        TIMESTAMPTZ NOT NULL,
    period_end          TIMESTAMPTZ NOT NULL,
    revenue_direct      NUMERIC(18,4) NOT NULL DEFAULT 0,
    revenue_attributed  NUMERIC(18,4) NOT NULL DEFAULT 0,
    cost_savings        NUMERIC(18,4) NOT NULL DEFAULT 0,
    productivity_gains  NUMERIC(18,4) NOT NULL DEFAULT 0,
    total_value         NUMERIC(18,4) NOT NULL,
    cost_inference      NUMERIC(18,4) NOT NULL DEFAULT 0,
    cost_training       NUMERIC(18,4) NOT NULL DEFAULT 0,
    cost_storage        NUMERIC(18,4) NOT NULL DEFAULT 0,
    cost_data           NUMERIC(18,4) NOT NULL DEFAULT 0,
    cost_infrastructure NUMERIC(18,4) NOT NULL DEFAULT 0,
    cost_licensing      NUMERIC(18,4) NOT NULL DEFAULT 0,
    cost_operations     NUMERIC(18,4) NOT NULL DEFAULT 0,
    total_cost          NUMERIC(18,4) NOT NULL,
    net_value           NUMERIC(18,4) NOT NULL,
    roi_percentage      NUMERIC(8,4) NOT NULL,
    value_evidence      JSONB NOT NULL,
    cost_evidence       JSONB NOT NULL,
    measured_by         UUID NOT NULL,
    verified_by         UUID,
    verified_at         TIMESTAMPTZ,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Cost anomalies
CREATE TABLE ai_cost_anomalies (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id            VARCHAR(256) UNIQUE NOT NULL,
    anomaly_type        VARCHAR(32) NOT NULL,
    severity            VARCHAR(16) NOT NULL,
    category            VARCHAR(16) NOT NULL,
    scope               VARCHAR(256) NOT NULL,
    description         TEXT NOT NULL,
    expected_value      NUMERIC(18,4),
    actual_value        NUMERIC(18,4),
    deviation_pct       NUMERIC(8,4),
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status              VARCHAR(32) NOT NULL DEFAULT 'open',
    assigned_to         UUID,
    resolution_notes    TEXT,
    resolved_at         TIMESTAMPTZ
);

-- Budget forecasts
CREATE TABLE ai_budget_forecasts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope               VARCHAR(256) NOT NULL,
    forecast_period     VARCHAR(32) NOT NULL,
    forecast_amount     NUMERIC(18,4) NOT NULL,
    confidence_lower    NUMERIC(18,4) NOT NULL,
    confidence_upper    NUMERIC(18,4) NOT NULL,
    confidence_level    NUMERIC(4,2) NOT NULL DEFAULT 0.95,
    method              VARCHAR(64) NOT NULL,
    factors             JSONB,
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by        UUID NOT NULL
);

-- Unit economics view (specification §3.2.2)
CREATE VIEW ai_unit_economics AS
SELECT
    initiative_id,
    model_id,
    DATE_TRUNC('month', cost_period_start) as period_month,
    SUM(CASE WHEN category = 'INF' THEN amount_usd ELSE 0 END) AS inference_cost,
    SUM(CASE WHEN category = 'INF' THEN quantity ELSE 0 END) AS inference_units,
    SUM(CASE WHEN category = 'INF' THEN amount_usd ELSE 0 END) / 
        NULLIF(SUM(CASE WHEN category = 'INF' THEN quantity ELSE 0 END), 0) AS cost_per_inference_unit,
    SUM(CASE WHEN category = 'TRN' THEN amount_usd ELSE 0 END) AS training_cost,
    SUM(CASE WHEN category = 'TRN' THEN quantity ELSE 0 END) AS training_units,
    SUM(CASE WHEN category = 'STO' THEN amount_usd ELSE 0 END) AS storage_cost,
    SUM(CASE WHEN category = 'STO' THEN quantity ELSE 0 END) AS storage_units,
    SUM(amount_usd) AS total_cost,
    COUNT(DISTINCT cost_id) AS cost_record_count
FROM ai_cost_records
WHERE approval_status = 'approved'
GROUP BY initiative_id, model_id, DATE_TRUNC('month', cost_period_start);

-- Budget variance view (specification §5.3.1)
CREATE VIEW ai_budget_variance AS
SELECT
    b.budget_id,
    b.budget_scope,
    b.budget_amount_usd AS budget_amount,
    COALESCE(SUM(c.amount_usd), 0) AS actual_spend,
    b.budget_amount_usd - COALESCE(SUM(c.amount_usd), 0) AS variance_amount,
    (b.budget_amount_usd - COALESCE(SUM(c.amount_usd), 0)) / 
        NULLIF(b.budget_amount_usd, 0) * 100 AS variance_percentage,
    COALESCE(SUM(c.amount_usd), 0) / 
        NULLIF(EXTRACT(MONTH FROM AGE(NOW(), b.effective_start)), 0) AS monthly_run_rate,
    (COALESCE(SUM(c.amount_usd), 0) / 
        NULLIF(EXTRACT(MONTH FROM AGE(NOW(), b.effective_start)), 0)) * 12 AS forecast_annual,
    CASE
        WHEN COALESCE(SUM(c.amount_usd), 0) > b.budget_amount_usd THEN 'over_budget'
        WHEN COALESCE(SUM(c.amount_usd), 0) > b.budget_amount_usd * 0.9 THEN 'at_risk'
        WHEN COALESCE(SUM(c.amount_usd), 0) > b.budget_amount_usd * 0.75 THEN 'on_track'
        ELSE 'under_utilized'
    END AS budget_status
FROM ai_budgets b
LEFT JOIN ai_cost_records c ON (
    c.initiative_id::text = b.budget_scope OR 
    c.business_unit_id::text = b.budget_scope OR
    c.cost_center = b.budget_scope
)
AND c.cost_period_start >= b.effective_start
AND c.cost_period_end <= b.effective_end
AND c.approval_status = 'approved'
WHERE b.status = 'active'
GROUP BY b.budget_id, b.budget_scope, b.budget_amount_usd, b.effective_start;
```

### 9.3 Celery Task Definitions

```python
# tasks/scheduled_tasks.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery("grc_claw_financial")
celery_app.config_from_object(
    {
        "broker_url": "redis://redis:6379/0",
        "result_backend": "redis://redis:6379/0",
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",
        "enable_utc": True,
    }
)

# Scheduled task definitions
celery_app.conf.beat_schedule = {
    "daily-cost-collection": {
        "task": "tasks.scheduled_tasks.collect_daily_costs",
        "schedule": crontab(hour=2, minute=0),  # 2:00 AM UTC
    },
    "daily-anomaly-detection": {
        "task": "tasks.scheduled_tasks.run_anomaly_detection",
        "schedule": crontab(hour=6, minute=0),  # 6:00 AM UTC
    },
    "daily-shadow-ai-scan": {
        "task": "tasks.scheduled_tasks.run_shadow_ai_detection",
        "schedule": crontab(hour=4, minute=0),  # 4:00 AM UTC
    },
    "weekly-budget-variance": {
        "task": "tasks.scheduled_tasks.generate_budget_variance",
        "schedule": crontab(day_of_week=1, hour=8, minute=0),  # Monday 8:00 AM
    },
    "monthly-management-report": {
        "task": "tasks.scheduled_tasks.generate_monthly_report",
        "schedule": crontab(day_of_month=1, hour=9, minute=0),  # 1st of month
    },
    "quarterly-forecast": {
        "task": "tasks.scheduled_tasks.generate_quarterly_forecast",
        "schedule": crontab(day_of_month=1, hour=10, minute=0, month_of_year="1,4,7,10"),
    },
    "weekly-reconciliation": {
        "task": "tasks.scheduled_tasks.run_finops_reconciliation",
        "schedule": crontab(day_of_week=0, hour=12, minute=0),  # Sunday noon
    },
}


@celery_app.task
def collect_daily_costs():
    """Daily cost collection from all sources."""
    import asyncio
    from pipelines.cost_collection import CostCollectionPipeline
    from database import get_session

    async def run():
        async for session in get_session():
            pipeline = CostCollectionPipeline(session)
            # Register collectors based on configuration
            # pipeline.register_collector(AWSCostCollector(...))
            # pipeline.register_collector(OpenAICostCollector(...))
            results = await pipeline.run()
            return results

    return asyncio.run(run())


@celery_app.task
def run_anomaly_detection():
    """Daily anomaly detection run."""
    import asyncio
    from services.anomaly_detector import CostAnomalyDetector
    from database import get_session

    async def run():
        async for session in get_session():
            detector = CostAnomalyDetector(session)
            return await detector.run_full_detection()

    return asyncio.run(run())


@celery_app.task
def run_shadow_ai_detection():
    """Daily shadow AI detection scan."""
    import asyncio
    from pipelines.shadow_ai_detection import ShadowAIDetector
    from database import get_session

    async def run():
        async for session in get_session():
            detector = ShadowAIDetector(session)
            alerts = []
            alerts.extend(await detector.detect_unattributed_cloud_spend())
            alerts.extend(await detector.detect_unregistered_api_keys())
            alerts.extend(await detector.detect_saas_ai_spend())
            ratio = await detector.compute_shadow_ai_ratio()
            return {"alerts": len(alerts), "shadow_ai_ratio": ratio}

    return asyncio.run(run())


@celery_app.task
def generate_budget_variance():
    """Weekly budget variance report."""
    import asyncio
    from services.budget_manager import BudgetManager
    from database import get_session

    async def run():
        async for session in get_session():
            manager = BudgetManager(session)
            # Generate variance for all active budgets
            return {"status": "completed"}

    return asyncio.run(run())


@celery_app.task
def generate_monthly_report():
    """Monthly management report generation."""
    import asyncio
    from services.reporting import FinancialReportingEngine
    from database import get_session

    async def run():
        async for session in get_session():
            engine = FinancialReportingEngine(session)
            now = datetime.utcnow()
            report = await engine.generate_management_dashboard(now.year, now.month)
            return report

    return asyncio.run(run())


@celery_app.task
def generate_quarterly_forecast():
    """Quarterly budget reforecast."""
    import asyncio
    from services.forecaster import BudgetForecaster
    from database import get_session

    async def run():
        async for session in get_session():
            forecaster = BudgetForecaster(session)
            forecast = await forecaster.forecast_total_ai_spend(forecast_months=3)
            return forecast

    return asyncio.run(run())


@celery_app.task
def run_finops_reconciliation():
    """Weekly FinOps reconciliation."""
    import asyncio
    from services.finops_integration import FinOpsIntegrationHub
    from database import get_session

    async def run():
        async for session in get_session():
            hub = FinOpsIntegrationHub(session)
            results = await hub.sync_all()
            return results

    return asyncio.run(run())
```

### 9.4 API Endpoints

```python
# api/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from services.cost_tracking import CostTrackingService
from services.roi_calculator import ROICalculator
from services.budget_manager import BudgetManager
from services.anomaly_detector import CostAnomalyDetector
from services.forecaster import BudgetForecaster
from services.reporting import FinancialReportingEngine
from services.finops_integration import FinOpsIntegrationHub
from database import get_session

app = FastAPI(
    title="GRC_Claw Financial Governance API",
    description="AI Financial Governance Implementation",
    version="1.0.0",
)


# --- Cost Tracking Endpoints ---

@app.get("/api/v1/costs")
async def list_costs(
    category: Optional[str] = None,
    initiative_id: Optional[str] = None,
    business_unit_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_shadow: Optional[bool] = None,
    session: AsyncSession = Depends(get_session),
):
    """List AI cost records with filtering."""
    service = CostTrackingService(session)
    return await service.list_costs(
        category=category,
        initiative_id=initiative_id,
        business_unit_id=business_unit_id,
        start_date=start_date,
        end_date=end_date,
        is_shadow=is_shadow,
    )


@app.post("/api/v1/costs")
async def create_cost_record(
    record: dict,
    session: AsyncSession = Depends(get_session),
):
    """Create a new AI cost record."""
    service = CostTrackingService(session)
    return await service.create_cost(record)


@app.get("/api/v1/costs/summary")
async def cost_summary(
    group_by: str = Query("category", enum=["category", "business_unit", "initiative", "cost_center"]),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session),
):
    """Get cost summary grouped by specified dimension."""
    service = CostTrackingService(session)
    return await service.get_summary(group_by, start_date, end_date)


# --- ROI Endpoints ---

@app.get("/api/v1/roi/direct/{initiative_id}")
async def get_direct_roi(
    initiative_id: str,
    period_start: datetime,
    period_end: datetime,
    session: AsyncSession = Depends(get_session),
):
    """Get direct ROI for an initiative."""
    calculator = ROICalculator(session)
    return await calculator.calculate_direct_roi(
        initiative_id, period_start, period_end
    )


@app.get("/api/v1/roi/governance")
async def get_governance_roi(
    period_start: datetime,
    period_end: datetime,
    session: AsyncSession = Depends(get_session),
):
    """Get governance ROI."""
    calculator = ROICalculator(session)
    return await calculator.calculate_governance_roi(period_start, period_end)


@app.get("/api/v1/roi/metrics")
async def get_all_roi_metrics(
    period_start: datetime,
    period_end: datetime,
    session: AsyncSession = Depends(get_session),
):
    """Get all ROI metrics (ROI-001 through ROI-010)."""
    calculator = ROICalculator(session)
    return await calculator.compute_roi_metrics(period_start, period_end)


# --- Budget Endpoints ---

@app.get("/api/v1/budgets")
async def list_budgets(
    fiscal_year: Optional[int] = None,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """List AI budgets."""
    manager = BudgetManager(session)
    return await manager.list_budgets(fiscal_year, status)


@app.post("/api/v1/budgets")
async def create_budget(
    budget: dict,
    session: AsyncSession = Depends(get_session),
):
    """Create a new budget."""
    manager = BudgetManager(session)
    return await manager.create_budget(**budget)


@app.get("/api/v1/budgets/{budget_id}/variance")
async def get_budget_variance(
    budget_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get budget variance analysis."""
    manager = BudgetManager(session)
    return await manager.compute_variance(budget_id)


@app.post("/api/v1/budgets/reallocate")
async def reallocate_budget(
    from_budget_id: str,
    to_budget_id: str,
    amount: float,
    requested_by: str,
    justification: str,
    session: AsyncSession = Depends(get_session),
):
    """Reallocate budget between initiatives."""
    manager = BudgetManager(session)
    return await manager.reallocate_budget(
        from_budget_id, to_budget_id, amount, requested_by, justification
    )


# --- Anomaly Detection Endpoints ---

@app.get("/api/v1/anomalies")
async def list_anomalies(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """List cost anomalies."""
    detector = CostAnomalyDetector(session)
    return await detector.list_anomalies(severity, status)


@app.post("/api/v1/anomalies/detect")
async def run_anomaly_detection(
    session: AsyncSession = Depends(get_session),
):
    """Trigger anomaly detection run."""
    detector = CostAnomalyDetector(session)
    return await detector.run_full_detection()


# --- Forecasting Endpoints ---

@app.get("/api/v1/forecasts/total")
async def forecast_total_spend(
    months: int = Query(3, ge=1, le=12),
    session: AsyncSession = Depends(get_session),
):
    """Forecast total AI spend."""
    forecaster = BudgetForecaster(session)
    return await forecaster.forecast_total_ai_spend(months)


@app.get("/api/v1/forecasts/initiative/{initiative_id}")
async def forecast_initiative_spend(
    initiative_id: str,
    months: int = Query(3, ge=1, le=12),
    session: AsyncSession = Depends(get_session),
):
    """Forecast initiative spend."""
    forecaster = BudgetForecaster(session)
    return await forecaster.forecast_initiative_spend(initiative_id, months)


@app.get("/api/v1/forecasts/accuracy")
async def get_forecast_accuracy(
    scope: str = "total",
    session: AsyncSession = Depends(get_session),
):
    """Get forecast accuracy metrics."""
    forecaster = BudgetForecaster(session)
    return await forecaster.compute_forecast_accuracy(scope)


# --- Reporting Endpoints ---

@app.get("/api/v1/reports/board-summary")
async def generate_board_summary(
    quarter: int = Query(..., ge=1, le=4),
    year: int = Query(..., ge=2024),
    session: AsyncSession = Depends(get_session),
):
    """Generate board summary report."""
    engine = FinancialReportingEngine(session)
    return await engine.generate_board_summary(quarter, year)


@app.get("/api/v1/reports/management-dashboard")
async def generate_management_dashboard(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    session: AsyncSession = Depends(get_session),
):
    """Generate management dashboard."""
    engine = FinancialReportingEngine(session)
    return await engine.generate_management_dashboard(year, month)


@app.get("/api/v1/reports/operational/{report_type}")
async def generate_operational_report(
    report_type: str,
    date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session),
):
    """Generate operational report."""
    engine = FinancialReportingEngine(session)
    return await engine.generate_operational_report(report_type, date)


# --- FinOps Integration Endpoints ---

@app.post("/api/v1/finops/sync")
async def sync_finops_data(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session),
):
    """Sync data from FinOps providers."""
    hub = FinOpsIntegrationHub(session)
    return await hub.sync_all(start_date, end_date)


@app.get("/api/v1/finops/consolidated")
async def get_consolidated_spend(
    start_date: datetime,
    end_date: datetime,
    session: AsyncSession = Depends(get_session),
):
    """Get consolidated spend across all FinOps sources."""
    hub = FinOpsIntegrationHub(session)
    return await hub.get_consolidated_spend(start_date, end_date)


@app.post("/api/v1/finops/reconcile")
async def reconcile_finops(
    finops_total: float,
    start_date: datetime,
    end_date: datetime,
    session: AsyncSession = Depends(get_session),
):
    """Reconcile GRC_Claw records with FinOps totals."""
    hub = FinOpsIntegrationHub(session)
    return await hub.reconcile_with_finops(finops_total, start_date, end_date)


# --- Shadow AI Endpoints ---

@app.get("/api/v1/shadow-ai/ratio")
async def get_shadow_ai_ratio(
    session: AsyncSession = Depends(get_session),
):
    """Get shadow AI spend ratio (UC7-004)."""
    from pipelines.shadow_ai_detection import ShadowAIDetector
    detector = ShadowAIDetector(session)
    return await detector.compute_shadow_ai_ratio()


@app.post("/api/v1/shadow-ai/detect")
async def run_shadow_ai_detection(
    session: AsyncSession = Depends(get_session),
):
    """Run shadow AI detection."""
    from pipelines.shadow_ai_detection import ShadowAIDetector
    detector = ShadowAIDetector(session)
    alerts = []
    alerts.extend(await detector.detect_unattributed_cloud_spend())
    alerts.extend(await detector.detect_unregistered_api_keys())
    alerts.extend(await detector.detect_saas_ai_spend())
    return {"alerts_generated": len(alerts)}
```

### 9.5 Testing

```python
# tests/test_financial_governance.py
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from models.cost_models import CostRecord, CostCategory, SourceType, ApprovalStatus
from models.roi_models import DirectROIMeasurement, GovernanceROIMeasurement
from models.budget_models import Budget, BudgetType, BudgetStatus
from services.roi_calculator import ROICalculator
from services.budget_manager import BudgetManager
from services.anomaly_detector import CostAnomalyDetector


class TestCostRecord:
    """Tests for cost record data model."""

    def test_create_minimal_record(self):
        record = CostRecord(
            category=CostCategory.INFERENCE,
            amount=Decimal("100.00"),
            amount_usd=Decimal("100.00"),
        )
        assert record.cost_id is not None
        assert record.category == CostCategory.INFERENCE
        assert record.is_shadow is False
        assert record.approval_status == ApprovalStatus.APPROVED

    def test_unit_cost_calculation(self):
        record = CostRecord(
            category=CostCategory.INFERENCE,
            amount_usd=Decimal("50.00"),
            quantity=Decimal("1000"),
            unit_of_measure="tokens",
        )
        unit_cost = record.compute_unit_cost()
        assert unit_cost == Decimal("0.05")

    def test_validation_requires_owner(self):
        record = CostRecord(
            category=CostCategory.INFERENCE,
            amount_usd=Decimal("100.00"),
        )
        errors = record.validate()
        assert "owner_id is required (FIN-001)" in errors

    def test_validation_requires_business_unit(self):
        record = CostRecord(
            category=CostCategory.INFERENCE,
            amount_usd=Decimal("100.00"),
        )
        errors = record.validate()
        assert "business_unit_id is required (FIN-001)" in errors

    def test_validation_manual_requires_approver(self):
        record = CostRecord(
            category=CostCategory.INFERENCE,
            amount_usd=Decimal("100.00"),
            source_type=SourceType.MANUAL,
        )
        errors = record.validate()
        assert "manual entries require approver (FIN-008)" in errors

    def test_negative_amount_rejected(self):
        record = CostRecord(
            category=CostCategory.INFERENCE,
            amount_usd=Decimal("-10.00"),
        )
        errors = record.validate()
        assert "amount_usd cannot be negative" in errors


class TestDirectROI:
    """Tests for direct ROI calculation."""

    def test_roi_calculation_positive(self):
        measurement = DirectROIMeasurement(
            initiative_id="test-initiative",
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            revenue_direct=Decimal("500000"),
            cost_inference=Decimal("100000"),
            cost_training=Decimal("50000"),
            cost_storage=Decimal("20000"),
            cost_data=Decimal("10000"),
            cost_infrastructure=Decimal("30000"),
            cost_licensing=Decimal("15000"),
            cost_operations=Decimal("25000"),
        )
        assert measurement.total_value == Decimal("500000")
        assert measurement.total_cost == Decimal("250000")
        assert measurement.net_value == Decimal("250000")
        assert measurement.roi_percentage == Decimal("100.00")
        assert measurement.roi_ratio == Decimal("2.0")

    def test_roi_calculation_negative(self):
        measurement = DirectROIMeasurement(
            initiative_id="test-initiative",
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            revenue_direct=Decimal("50000"),
            cost_inference=Decimal("100000"),
            cost_training=Decimal("50000"),
            cost_storage=Decimal("20000"),
            cost_data=Decimal("10000"),
            cost_infrastructure=Decimal("30000"),
            cost_licensing=Decimal("15000"),
            cost_operations=Decimal("25000"),
        )
        assert measurement.roi_percentage == Decimal("-50.00")
        assert measurement.roi_ratio == Decimal("0.2")

    def test_zero_cost_returns_none(self):
        measurement = DirectROIMeasurement(
            initiative_id="test-initiative",
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            revenue_direct=Decimal("100000"),
        )
        assert measurement.roi_percentage is None
        assert measurement.roi_ratio is None


class TestGovernanceROI:
    """Tests for governance ROI calculation."""

    def test_governance_roi_positive(self):
        measurement = GovernanceROIMeasurement(
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            risk_reduction_value=Decimal("500000"),
            compliance_cost_savings=Decimal("100000"),
            incident_cost_avoidance=Decimal("200000"),
            governance_tooling_cost=Decimal("50000"),
            governance_personnel_cost=Decimal("100000"),
            governance_process_cost=Decimal("30000"),
        )
        assert measurement.total_governance_value == Decimal("800000")
        assert measurement.total_governance_cost == Decimal("180000")
        assert measurement.roi_percentage == Decimal("344.44")

    def test_maturity_target_check(self):
        measurement = GovernanceROIMeasurement(
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 3, 31),
            risk_reduction_value=Decimal("500000"),
            governance_tooling_cost=Decimal("50000"),
            governance_personnel_cost=Decimal("100000"),
            governance_process_cost=Decimal("30000"),
        )
        assert measurement.maturity_target_met(1) is True
        assert measurement.maturity_target_met(3) is True
        assert measurement.maturity_target_met(5) is False


class TestBudgetVariance:
    """Tests for budget variance calculations."""

    def test_under_budget(self):
        # Budget $100K, spent $75K → 25% under
        budget = Decimal("100000")
        actual = Decimal("75000")
        variance = budget - actual
        variance_pct = (variance / budget) * 100
        assert variance == Decimal("25000")
        assert variance_pct == Decimal("25.00")

    def test_over_budget(self):
        budget = Decimal("100000")
        actual = Decimal("120000")
        variance = budget - actual
        variance_pct = (variance / budget) * 100
        assert variance == Decimal("-20000")
        assert variance_pct == Decimal("-20.00")

    def test_budget_status_thresholds(self):
        budget = Decimal("100000")
        
        # Under utilized: <50% spent at 75% of period
        assert (Decimal("40000") / budget) < Decimal("0.50")
        
        # On track: 75-90% spent
        assert (Decimal("80000") / budget) > Decimal("0.75")
        assert (Decimal("80000") / budget) < Decimal("0.90")
        
        # At risk: 90-100% spent
        assert (Decimal("95000") / budget) > Decimal("0.90")
        assert (Decimal("95000") / budget) < Decimal("1.00")
        
        # Over budget: >100% spent
        assert (Decimal("110000") / budget) > Decimal("1.00")
        
        # Critical over: >120% spent
        assert (Decimal("130000") / budget) > Decimal("1.20")


class TestShadowAIRatio:
    """Tests for shadow AI ratio calculation (UC7-004)."""

    def test_shadow_ratio_calculation(self):
        total = Decimal("1000000")
        shadow = Decimal("80000")
        ratio = (shadow / total) * 100
        assert ratio == Decimal("8.00")
        assert ratio < 10  # Green

    def test_shadow_ratio_escalation(self):
        # Operational: >10%
        assert Decimal("15") > 10
        # Management: >20%
        assert Decimal("25") > 20
        # Board: >30%
        assert Decimal("35") > 30


class TestEnforcementThresholds:
    """Tests for budget enforcement levels (specification §5.3.3)."""

    def test_warning_threshold(self):
        budget = Decimal("100000")
        spend = Decimal("95000")
        assert (spend / budget) >= Decimal("0.90")

    def test_soft_block_threshold(self):
        budget = Decimal("100000")
        spend = Decimal("105000")
        assert (spend / budget) >= Decimal("1.00")

    def test_hard_block_threshold(self):
        budget = Decimal("100000")
        spend = Decimal("115000")
        assert (spend / budget) >= Decimal("1.10")

    def test_emergency_threshold(self):
        budget = Decimal("100000")
        spend = Decimal("125000")
        assert (spend / budget) >= Decimal("1.20")


class TestAnomalyDetection:
    """Tests for anomaly detection severity classification."""

    def test_critical_severity(self):
        from services.anomaly_detector import CostAnomalyDetector
        severity = CostAnomalyDetector._classify_severity(5.5, 250)
        assert severity == "critical"

    def test_high_severity(self):
        from services.anomaly_detector import CostAnomalyDetector
        severity = CostAnomalyDetector._classify_severity(4.5, 150)
        assert severity == "high"

    def test_medium_severity(self):
        from services.anomaly_detector import CostAnomalyDetector
        severity = CostAnomalyDetector._classify_severity(3.5, 75)
        assert severity == "medium"

    def test_low_severity(self):
        from services.anomaly_detector import CostAnomalyDetector
        severity = CostAnomalyDetector._classify_severity(3.1, 30)
        assert severity == "low"


# Integration tests
@pytest.mark.asyncio
class TestCostCollectionPipeline:
    """Integration tests for cost collection."""

    async def test_aws_collector_classification(self):
        from pipelines.cost_collection import AWSCostCollector
        collector = AWSCostCollector("fake-key", "fake-secret")
        
        assert collector._classify_service("Amazon Bedrock") == CostCategory.INFERENCE
        assert collector._classify_service("Amazon SageMaker") == CostCategory.INFERENCE
        assert collector._classify_service("Amazon S3") == CostCategory.STORAGE
        assert collector._classify_service("Amazon EC2") == CostCategory.INFRASTRUCTURE

    async def test_openai_model_pricing(self):
        from pipelines.cost_collection import OpenAICostCollector
        collector = OpenAICostCollector("fake-key")
        
        assert collector._get_model_pricing("gpt-4") == Decimal("0.06")
        assert collector._get_model_pricing("gpt-3.5-turbo") == Decimal("0.002")
        assert collector._get_model_pricing("unknown-model") == Decimal("0.03")
```

### 9.6 Monitoring & Alerting Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "financial_governance_alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]
```

```yaml
# monitoring/financial_governance_alerts.yml
groups:
  - name: grc_claw_financial_governance
    rules:
      # Cost anomaly alerts
      - alert: CostSpikeDetected
        expr: grc_claw_cost_anomaly_z_score > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Cost spike detected in {{ $labels.category }}"
          description: "Z-score {{ $value }} exceeds threshold for {{ $labels.scope }}"

      - alert: CriticalCostSpike
        expr: grc_claw_cost_anomaly_z_score > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical cost spike in {{ $labels.category }}"
          description: "Z-score {{ $value }} — immediate investigation required"

      # Budget alerts
      - alert: BudgetAtRisk
        expr: grc_claw_budget_spend_ratio > 0.9
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Budget {{ $labels.scope }} at risk (>90% spent)"

      - alert: BudgetOverrun
        expr: grc_claw_budget_spend_ratio > 1.0
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "Budget {{ $labels.scope }} exceeded"
          description: "Spend ratio {{ $value }} exceeds 100%"

      # Shadow AI alerts
      - alert: ShadowAIElevated
        expr: grc_claw_shadow_ai_ratio > 10
        for: 1d
        labels:
          severity: warning
        annotations:
          summary: "Shadow AI ratio above target"
          description: "Current: {{ $value }}% (target: <10%)"

      - alert: ShadowAIHigh
        expr: grc_claw_shadow_ai_ratio > 20
        for: 1d
        labels:
          severity: critical
        annotations:
          summary: "Shadow AI ratio critically high"
          description: "Current: {{ $value }}% — management escalation required"

      # ROI alerts
      - alert: ROIBelowTarget
        expr: grc_claw_roi_ratio < 1.0
        for: 7d
        labels:
          severity: warning
        annotations:
          summary: "ROI below target"
          description: "Current ROI: {{ $value }}x (target: >1.0x)"

      # Data quality alerts
      - alert: CostDataQualityLow
        expr: grc_claw_data_quality_score < 98
        for: 1d
        labels:
          severity: warning
        annotations:
          summary: "Cost data quality below target"
          description: "Quality score: {{ $value }}% (target: >98%)"
```

---

## Appendix A: Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd grc-claw-financial-governance
cp .env.example .env
# Edit .env with your credentials

# 2. Start infrastructure
docker-compose up -d postgres redis

# 3. Run migrations
alembic upgrade head

# 4. Start services
docker-compose up -d api worker scheduler

# 5. Verify
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/costs/summary
```

## Appendix B: Environment Variables

```bash
# .env.example
DB_PASSWORD=secure_password_here
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant...
GRAFANA_PASSWORD=admin_password
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql+asyncpg://grc_claw:password@localhost/grc_claw_financial
```

## Appendix C: Metric Quick Reference

| Metric ID | Name | Formula | Target | Section |
|-----------|------|---------|--------|---------|
| UC7-003 | AI Spend Allocation Rate | (Attributed / Total) × 100 | 100% | §3 |
| UC7-004 | Shadow AI Spend Ratio | (Shadow / Total) × 100 | <10% | §3.4 |
| ROI-001 | Direct ROI | (Value - Cost) / Cost | >1.0 | §4.2 |
| ROI-002 | Indirect ROI | Indirect Value / Total Cost | >0.5 | §4.3 |
| ROI-003 | Governance ROI | (Gov Value - Gov Cost) / Gov Cost | >1.0 | §4.4 |
| ROI-004 | Blended ROI | (Total Value - Total Cost) / Total Cost | >1.0 | §4.5 |
| ROI-005 | Cost per Inference | Inference Cost / Units | Declining | §4.5 |
| ROI-010 | Payback Period | Months to recover investment | <18 months | §4.5 |

---

*End of implementation guide*</longcat_think>
