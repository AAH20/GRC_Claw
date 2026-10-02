"""Pydantic models for fraud detection."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TransactionType(str, Enum):
    """Transaction type enumeration."""

    CREDIT = "credit"
    DEBIT = "debit"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"
    REFUND = "refund"


class Transaction(BaseModel):
    """Transaction data model."""

    transaction_id: str = Field(..., description="Unique transaction identifier")
    account_id: str = Field(..., description="Account identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Transaction timestamp")
    merchant_id: str | None = Field(default=None, description="Merchant identifier")
    merchant_category: str | None = Field(default=None, description="Merchant category code")
    location: str | None = Field(default=None, description="Transaction location")
    device_id: str | None = Field(default=None, description="Device identifier")
    ip_address: str | None = Field(default=None, description="IP address")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Pattern(BaseModel):
    """Detected fraud pattern model."""

    pattern_id: str = Field(..., description="Unique pattern identifier")
    pattern_type: str = Field(..., description="Type of fraud pattern")
    name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="Pattern description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    severity: RiskLevel = Field(..., description="Pattern severity level")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence")
    related_transactions: list[str] = Field(default_factory=list, description="Related transaction IDs")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")


class Anomaly(BaseModel):
    """Detected anomaly model."""

    anomaly_id: str = Field(..., description="Unique anomaly identifier")
    anomaly_type: str = Field(..., description="Type of anomaly")
    name: str = Field(..., description="Anomaly name")
    description: str = Field(..., description="Anomaly description")
    score: float = Field(..., ge=0.0, le=1.0, description="Anomaly score")
    severity: RiskLevel = Field(..., description="Anomaly severity level")
    feature_contributions: dict[str, float] = Field(
        default_factory=dict, description="Feature contribution scores"
    )
    baseline_value: float | None = Field(default=None, description="Expected baseline value")
    observed_value: float | None = Field(default=None, description="Observed value")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")


class RiskFactor(BaseModel):
    """Individual risk factor model."""

    factor_name: str = Field(..., description="Risk factor name")
    factor_type: Literal["pattern", "anomaly", "behavioral", "velocity", "geographic"] = Field(
        ..., description="Risk factor category"
    )
    weight: float = Field(..., ge=0.0, le=1.0, description="Factor weight")
    score: float = Field(..., ge=0.0, le=1.0, description="Factor score")
    description: str = Field(..., description="Factor description")
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence")


class RiskScore(BaseModel):
    """Composite risk score model."""

    score_id: str = Field(..., description="Unique score identifier")
    transaction_id: str = Field(..., description="Associated transaction ID")
    account_id: str = Field(..., description="Associated account ID")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall risk score")
    risk_level: RiskLevel = Field(..., description="Computed risk level")
    factors: list[RiskFactor] = Field(default_factory=list, description="Contributing risk factors")
    model_version: str = Field(default="1.0.0", description="Model version")
    computed_at: datetime = Field(default_factory=datetime.utcnow, description="Computation timestamp")
    explanation: str = Field(default="", description="Human-readable explanation")


class AccountProfile(BaseModel):
    """Account profile model."""

    account_id: str = Field(..., description="Account identifier")
    account_type: str = Field(default="personal", description="Account type")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation date")
    average_transaction_amount: float = Field(default=0.0, description="Average transaction amount")
    transaction_count_30d: int = Field(default=0, description="Transaction count in last 30 days")
    unique_merchants_30d: int = Field(default=0, description="Unique merchants in last 30 days")
    unique_locations_30d: int = Field(default=0, description="Unique locations in last 30 days")
    typical_transaction_types: list[TransactionType] = Field(
        default_factory=list, description="Typical transaction types"
    )
    risk_indicators: list[str] = Field(default_factory=list, description="Account risk indicators")


class AccountAnalysis(BaseModel):
    """Account analysis result model."""

    analysis_id: str = Field(..., description="Unique analysis identifier")
    account_id: str = Field(..., description="Account identifier")
    profile: AccountProfile = Field(..., description="Account profile")
    anomalies: list[Anomaly] = Field(default_factory=list, description="Detected anomalies")
    risk_score: RiskScore = Field(..., description="Account risk score")
    recommendations: list[str] = Field(default_factory=list, description="Action recommendations")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


class FraudReport(BaseModel):
    """Comprehensive fraud report model."""

    report_id: str = Field(..., description="Unique report identifier")
    transaction: Transaction = Field(..., description="Analyzed transaction")
    patterns: list[Pattern] = Field(default_factory=list, description="Detected patterns")
    anomalies: list[Anomaly] = Field(default_factory=list, description="Detected anomalies")
    risk_score: RiskScore = Field(..., description="Computed risk score")
    account_analysis: AccountAnalysis | None = Field(default=None, description="Account analysis")
    final_decision: Literal["approve", "review", "block"] = Field(
        ..., description="Final fraud decision"
    )
    decision_reason: str = Field(..., description="Decision reasoning")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Report creation time")


class BatchAnalysisRequest(BaseModel):
    """Batch analysis request model."""

    transactions: list[Transaction] = Field(
        ..., min_length=1, max_length=100, description="Transactions to analyze"
    )


class BatchAnalysisResponse(BaseModel):
    """Batch analysis response model."""

    batch_id: str = Field(..., description="Batch identifier")
    reports: list[FraudReport] = Field(default_factory=list, description="Fraud reports")
    summary: dict[str, Any] = Field(default_factory=dict, description="Batch summary")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")


class MonitoringSession(BaseModel):
    """Monitoring session model."""

    session_id: str = Field(..., description="Session identifier")
    account_id: str = Field(..., description="Monitored account ID")
    status: Literal["active", "paused", "stopped"] = Field(..., description="Session status")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    alerts_count: int = Field(default=0, description="Number of alerts generated")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(default="0.1.0", description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class AgentStatus(BaseModel):
    """Agent status model."""

    agent_name: str = Field(..., description="Agent name")
    status: Literal["idle", "running", "error"] = Field(..., description="Agent status")
    last_activity: datetime | None = Field(default=None, description="Last activity timestamp")
    tasks_processed: int = Field(default=0, description="Number of tasks processed")
    error_count: int = Field(default=0, description="Number of errors encountered")


class AgentsStatusResponse(BaseModel):
    """Agents status response model."""

    agents: list[AgentStatus] = Field(default_factory=list, description="Agent statuses")
    overall_status: str = Field(..., description="Overall system status")
