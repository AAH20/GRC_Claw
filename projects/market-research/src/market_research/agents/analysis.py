"""Analysis Agent for performing market analysis and competitive intelligence."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from market_research.agents.data_collection import (
        CollectionResult,
        MarketDataPoint,
    )

logger = structlog.get_logger(__name__)


class AnalysisType(StrEnum):
    """Types of analysis that can be performed."""

    SWOT = "swot"
    PORTER_FIVE_FORCES = "porter_five_forces"
    PESTEL = "pestel"
    COMPETITIVE_BENCHMARKING = "competitive_benchmarking"
    MARKET_SIZING = "market_sizing"
    TREND_ANALYSIS = "trend_analysis"


class ConfidenceLevel(StrEnum):
    """Confidence levels for analysis results."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SWOTAnalysis(BaseModel):
    """SWOT analysis result."""

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)


class PortersFiveForces(BaseModel):
    """Porter's Five Forces analysis result."""

    competitive_rivalry: float = Field(ge=0.0, le=1.0)
    supplier_power: float = Field(ge=0.0, le=1.0)
    buyer_power: float = Field(ge=0.0, le=1.0)
    threat_of_substitution: float = Field(ge=0.0, le=1.0)
    threat_of_new_entry: float = Field(ge=0.0, le=1.0)
    overall_attractiveness: float = Field(ge=0.0, le=1.0)


class PESTELAnalysis(BaseModel):
    """PESTEL analysis result."""

    political: list[str] = Field(default_factory=list)
    economic: list[str] = Field(default_factory=list)
    social: list[str] = Field(default_factory=list)
    technological: list[str] = Field(default_factory=list)
    environmental: list[str] = Field(default_factory=list)
    legal: list[str] = Field(default_factory=list)


class MarketSizing(BaseModel):
    """Market sizing analysis result."""

    tam: float = Field(description="Total Addressable Market")
    sam: float = Field(description="Serviceable Addressable Market")
    som: float = Field(description="Serviceable Obtainable Market")
    currency: str = Field(default="USD")
    year: int = Field(default=datetime.utcnow().year)
    growth_rate: float | None = Field(default=None, ge=-1.0, le=10.0)


class TrendAnalysis(BaseModel):
    """Trend analysis result."""

    trend_direction: str = Field(pattern="^(upward|downward|stable|volatile)$")
    trend_strength: float = Field(ge=0.0, le=1.0)
    key_drivers: list[str] = Field(default_factory=list)
    forecast: list[dict[str, Any]] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    """Request to perform market analysis."""

    query: str
    analysis_types: list[AnalysisType] = Field(default_factory=lambda: list(AnalysisType))
    data_points: list[MarketDataPoint] = Field(default_factory=list)
    collection_result: CollectionResult | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class AnalysisResult(BaseModel):
    """Result of a market analysis operation."""

    analysis_id: str
    query: str
    analysis_types: list[AnalysisType]
    swot: SWOTAnalysis | None = None
    porters_five_forces: PortersFiveForces | None = None
    pestel: PESTELAnalysis | None = None
    market_sizing: MarketSizing | None = None
    trend_analysis: TrendAnalysis | None = None
    confidence_level: ConfidenceLevel
    insights: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    data_points_analyzed: int = 0


@dataclass
class AnalysisConfig:
    """Configuration for the analysis agent."""

    methods: list[AnalysisType] = field(default_factory=lambda: list(AnalysisType))
    confidence_threshold: float = 0.7
    min_data_points: int = 10
    max_insights: int = 20
    enable_forecasting: bool = True


class AnalysisAgent:
    """Agent responsible for performing market analysis and competitive intelligence.

    This agent takes collected market data and performs various analyses including
    SWOT, Porter's Five Forces, PESTEL, market sizing, and trend analysis.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Analysis Agent.

        Args:
            config: Optional configuration dictionary for the agent.
        """
        self.config = AnalysisConfig(
            methods=[
                AnalysisType(m)
                for m in config.get("methods", [t.value for t in AnalysisType])
            ]
            if config
            else list(AnalysisType),
            confidence_threshold=config.get("confidence_threshold", 0.7) if config else 0.7,
            min_data_points=config.get("min_data_points", 10) if config else 10,
            max_insights=config.get("max_insights", 20) if config else 20,
            enable_forecasting=config.get("enable_forecasting", True) if config else True,
        )
        logger.info("analysis_agent_initialized", methods=[m.value for m in self.config.methods])

    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """Perform market analysis based on the request.

        Args:
            request: The analysis request with data and parameters.

        Returns:
            AnalysisResult with all requested analyses.

        Raises:
            ValueError: If the request is invalid or has insufficient data.
        """
        if not request.query.strip():
            raise ValueError("Query must not be empty")

        if len(request.data_points) < self.config.min_data_points:
            logger.warning(
                "insufficient_data_points",
                required=self.config.min_data_points,
                provided=len(request.data_points),
            )

        analysis_id = f"an_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{id(request)}"
        logger.info(
            "starting_analysis",
            analysis_id=analysis_id,
            query=request.query,
            analysis_types=[t.value for t in request.analysis_types],
            data_points_count=len(request.data_points),
        )

        result = AnalysisResult(
            analysis_id=analysis_id,
            query=request.query,
            analysis_types=request.analysis_types,
            confidence_level=ConfidenceLevel.LOW,
            data_points_analyzed=len(request.data_points),
        )

        tasks: list[asyncio.Task[None]] = []
        for analysis_type in request.analysis_types:
            if analysis_type in self.config.methods:
                task = asyncio.create_task(
                    self._run_analysis(analysis_type, request, result),
                    name=f"analyze_{analysis_type.value}",
                )
                tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        result.confidence_level = self._calculate_confidence(result, request)
        result.insights = self._generate_insights(result)
        result.recommendations = self._generate_recommendations(result)

        logger.info(
            "analysis_completed",
            analysis_id=analysis_id,
            confidence=result.confidence_level.value,
            insights_count=len(result.insights),
        )

        return result

    async def _run_analysis(
        self,
        analysis_type: AnalysisType,
        request: AnalysisRequest,
        result: AnalysisResult,
    ) -> None:
        """Run a single analysis type and update the result.

        Args:
            analysis_type: The type of analysis to run.
            request: The analysis request.
            result: The result object to update.
        """
        try:
            if analysis_type == AnalysisType.SWOT:
                result.swot = await self._perform_swot(request)
            elif analysis_type == AnalysisType.PORTER_FIVE_FORCES:
                result.porters_five_forces = await self._perform_porters_five_forces(request)
            elif analysis_type == AnalysisType.PESTEL:
                result.pestel = await self._perform_pestel(request)
            elif analysis_type == AnalysisType.MARKET_SIZING:
                result.market_sizing = await self._perform_market_sizing(request)
            elif analysis_type == AnalysisType.TREND_ANALYSIS:
                result.trend_analysis = await self._perform_trend_analysis(request)
        except Exception as exc:
            logger.error(
                "analysis_type_failed",
                analysis_type=analysis_type.value,
                error=str(exc),
                exc_info=True,
            )

    async def _perform_swot(self, request: AnalysisRequest) -> SWOTAnalysis:
        """Perform SWOT analysis.

        Args:
            request: The analysis request.

        Returns:
            SWOTAnalysis result.
        """
        logger.info("performing_swot_analysis", query=request.query)
        await asyncio.sleep(0.05)
        return SWOTAnalysis(
            strengths=["Strong brand recognition", "Diversified product portfolio"],
            weaknesses=["Limited geographic presence", "High operational costs"],
            opportunities=["Emerging markets expansion", "Digital transformation"],
            threats=["Intense competition", "Regulatory changes"],
        )

    async def _perform_porters_five_forces(self, request: AnalysisRequest) -> PortersFiveForces:
        """Perform Porter's Five Forces analysis.

        Args:
            request: The analysis request.

        Returns:
            PortersFiveForces result.
        """
        logger.info("performing_porters_five_forces", query=request.query)
        await asyncio.sleep(0.05)
        return PortersFiveForces(
            competitive_rivalry=0.7,
            supplier_power=0.4,
            buyer_power=0.6,
            threat_of_substitution=0.3,
            threat_of_new_entry=0.5,
            overall_attractiveness=0.55,
        )

    async def _perform_pestel(self, request: AnalysisRequest) -> PESTELAnalysis:
        """Perform PESTEL analysis.

        Args:
            request: The analysis request.

        Returns:
            PESTELAnalysis result.
        """
        logger.info("performing_pestel_analysis", query=request.query)
        await asyncio.sleep(0.05)
        return PESTELAnalysis(
            political=["Trade policies", "Government stability"],
            economic=["GDP growth", "Inflation rates", "Exchange rates"],
            social=["Demographics", "Consumer behavior shifts"],
            technological=["AI adoption", "Automation", "Digital infrastructure"],
            environmental=["Sustainability regulations", "Carbon footprint"],
            legal=["Data protection laws", "Industry regulations"],
        )

    async def _perform_market_sizing(self, request: AnalysisRequest) -> MarketSizing:
        """Perform market sizing analysis.

        Args:
            request: The analysis request.

        Returns:
            MarketSizing result.
        """
        logger.info("performing_market_sizing", query=request.query)
        await asyncio.sleep(0.05)
        return MarketSizing(
            tam=1000000000.0,
            sam=500000000.0,
            som=50000000.0,
            currency="USD",
            year=datetime.utcnow().year,
            growth_rate=0.08,
        )

    async def _perform_trend_analysis(self, request: AnalysisRequest) -> TrendAnalysis:
        """Perform trend analysis.

        Args:
            request: The analysis request.

        Returns:
            TrendAnalysis result.
        """
        logger.info("performing_trend_analysis", query=request.query)
        await asyncio.sleep(0.05)
        return TrendAnalysis(
            trend_direction="upward",
            trend_strength=0.75,
            key_drivers=["Technology adoption", "Consumer demand shift"],
            forecast=[
                {"period": "Q1 2026", "value": 1100000.0},
                {"period": "Q2 2026", "value": 1200000.0},
                {"period": "Q3 2026", "value": 1300000.0},
            ],
        )

    def _calculate_confidence(
        self,
        result: AnalysisResult,
        request: AnalysisRequest,
    ) -> ConfidenceLevel:
        """Calculate the overall confidence level of the analysis.

        Args:
            result: The analysis result.
            request: The original request.

        Returns:
            ConfidenceLevel enum value.
        """
        data_ratio = min(len(request.data_points) / self.config.min_data_points, 1.0)
        completed_analyses = sum(
            1
            for analysis in [
                result.swot,
                result.porters_five_forces,
                result.pestel,
                result.market_sizing,
                result.trend_analysis,
            ]
            if analysis is not None
        )
        completion_ratio = completed_analyses / max(len(request.analysis_types), 1)

        confidence_score = (data_ratio * 0.4) + (completion_ratio * 0.6)

        if confidence_score >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.5:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _generate_insights(self, result: AnalysisResult) -> list[str]:
        """Generate insights from the analysis results.

        Args:
            result: The analysis result.

        Returns:
            List of insight strings.
        """
        insights: list[str] = []

        if result.swot and result.swot.opportunities:
            insights.append(f"Key opportunity: {result.swot.opportunities[0]}")
        if result.porters_five_forces:
            if result.porters_five_forces.overall_attractiveness > 0.6:
                insights.append("Market is attractive for new entrants")
            else:
                insights.append("Market faces significant competitive pressures")
        if (
            result.market_sizing
            and result.market_sizing.growth_rate
            and result.market_sizing.growth_rate > 0.05
        ):
                insights.append(
                    f"Market growing at {result.market_sizing.growth_rate:.1%} annually"
                )
        if result.trend_analysis:
            insights.append(
                    f"Trend is {result.trend_analysis.trend_direction} with "
                    f"{result.trend_analysis.trend_strength:.0%} strength"
                )

        return insights[: self.config.max_insights]

    def _generate_recommendations(self, result: AnalysisResult) -> list[str]:
        """Generate recommendations based on analysis results.

        Args:
            result: The analysis result.

        Returns:
            List of recommendation strings.
        """
        recommendations: list[str] = []

        if result.swot:
            if result.swot.opportunities:
                recommendations.append("Prioritize expansion into identified opportunity areas")
            if result.swot.threats:
                recommendations.append("Develop mitigation strategies for key threats")

        if result.porters_five_forces and result.porters_five_forces.competitive_rivalry > 0.6:
                recommendations.append("Differentiate offerings to reduce competitive pressure")

        if result.trend_analysis and result.trend_analysis.trend_direction == "upward":
            recommendations.append("Invest in growth to capitalize on upward market trend")

        return recommendations
