"""Transaction analysis routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from fraud_detection.agents.anomaly_detector import AnomalyDetectorAgent
from fraud_detection.agents.pattern_detector import PatternDetectorAgent
from fraud_detection.agents.risk_scorer import RiskScorerAgent
from fraud_detection.api.dependencies import verify_api_key
from fraud_detection.config.logging_config import get_logger
from fraud_detection.models.schemas import (
    AccountAnalysis,
    Anomaly,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    FraudReport,
    Pattern,
    RiskScore,
    Transaction,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["analysis"])

# Module-level agent instances (singleton pattern)
_pattern_agent: PatternDetectorAgent | None = None
_anomaly_agent: AnomalyDetectorAgent | None = None
_risk_agent: RiskScorerAgent | None = None


def get_pattern_agent() -> PatternDetectorAgent:
    """Get or create PatternDetectorAgent singleton.

    Returns:
        PatternDetectorAgent instance.
    """
    global _pattern_agent
    if _pattern_agent is None:
        _pattern_agent = PatternDetectorAgent()
    return _pattern_agent


def get_anomaly_agent() -> AnomalyDetectorAgent:
    """Get or create AnomalyDetectorAgent singleton.

    Returns:
        AnomalyDetectorAgent instance.
    """
    global _anomaly_agent
    if _anomaly_agent is None:
        _anomaly_agent = AnomalyDetectorAgent()
    return _anomaly_agent


def get_risk_agent() -> RiskScorerAgent:
    """Get or create RiskScorerAgent singleton.

    Returns:
        RiskScorerAgent instance.
    """
    global _risk_agent
    if _risk_agent is None:
        _risk_agent = RiskScorerAgent()
    return _risk_agent


@router.post("/analyze", response_model=FraudReport)
async def analyze_transaction(
    transaction: Transaction,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> FraudReport:
    """Analyze a single transaction for fraud.

    Args:
        transaction: Transaction to analyze.
        api_key: Verified API key.

    Returns:
        FraudReport with complete analysis.
    """
    pattern_agent = get_pattern_agent()
    anomaly_agent = get_anomaly_agent()
    risk_agent = get_risk_agent()

    patterns = await pattern_agent.detect(transaction)
    anomalies = await anomaly_agent.detect(transaction)
    risk_score = await risk_agent.score(transaction, patterns, anomalies)

    decision = _make_decision(risk_score.overall_score)

    return FraudReport(
        report_id=str(uuid.uuid4()),
        transaction=transaction,
        patterns=patterns,
        anomalies=anomalies,
        risk_score=risk_score,
        final_decision=decision,
        decision_reason=f"Risk score {risk_score.overall_score:.2f} -> {decision}",
    )


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(
    request: BatchAnalysisRequest,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> BatchAnalysisResponse:
    """Analyze a batch of transactions for fraud.

    Args:
        request: Batch analysis request with transactions.
        api_key: Verified API key.

    Returns:
        BatchAnalysisResponse with all reports.
    """
    reports: list[FraudReport] = []
    for transaction in request.transactions:
        pattern_agent = get_pattern_agent()
        anomaly_agent = get_anomaly_agent()
        risk_agent = get_risk_agent()

        patterns = await pattern_agent.detect(transaction)
        anomalies = await anomaly_agent.detect(transaction)
        risk_score = await risk_agent.score(transaction, patterns, anomalies)
        decision = _make_decision(risk_score.overall_score)

        reports.append(
            FraudReport(
                report_id=str(uuid.uuid4()),
                transaction=transaction,
                patterns=patterns,
                anomalies=anomalies,
                risk_score=risk_score,
                final_decision=decision,
                decision_reason=f"Risk score {risk_score.overall_score:.2f} -> {decision}",
            )
        )

    return BatchAnalysisResponse(
        batch_id=str(uuid.uuid4()),
        reports=reports,
        summary={
            "total": len(reports),
            "flagged": sum(1 for r in reports if r.final_decision != "approve"),
        },
    )


@router.post("/patterns/detect", response_model=list[Pattern])
async def detect_patterns(
    transaction: Transaction,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> list[Pattern]:
    """Detect fraud patterns in a transaction.

    Args:
        transaction: Transaction to analyze.
        api_key: Verified API key.

    Returns:
        List of detected patterns.
    """
    agent = get_pattern_agent()
    return await agent.detect(transaction)


@router.post("/anomalies/detect", response_model=list[Anomaly])
async def detect_anomalies(
    transaction: Transaction,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> list[Anomaly]:
    """Detect anomalies in a transaction.

    Args:
        transaction: Transaction to analyze.
        api_key: Verified API key.

    Returns:
        List of detected anomalies.
    """
    agent = get_anomaly_agent()
    return await agent.detect(transaction)


@router.post("/risk/score", response_model=RiskScore)
async def score_risk(
    transaction: Transaction,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> RiskScore:
    """Score risk for a transaction.

    Args:
        transaction: Transaction to score.
        api_key: Verified API key.

    Returns:
        Computed RiskScore.
    """
    agent = get_risk_agent()
    return await agent.score(transaction)


def _make_decision(score: float) -> str:
    """Make fraud decision based on risk score.

    Args:
        score: Risk score between 0 and 1.

    Returns:
        Decision string: approve, review, or block.
    """
    if score >= 0.8:
        return "block"
    if score >= 0.5:
        return "review"
    return "approve"
