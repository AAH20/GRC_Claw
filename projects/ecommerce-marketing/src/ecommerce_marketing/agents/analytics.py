"""Analytics and reporting agent."""

from __future__ import annotations

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ecommerce_marketing.config import get_settings

logger = structlog.get_logger(__name__)


class CampaignMetrics(BaseModel):
    """Campaign performance metrics."""

    campaign_id: str = Field(..., description="Campaign identifier")
    impressions: int = Field(default=0, ge=0, description="Total impressions")
    clicks: int = Field(default=0, ge=0, description="Total clicks")
    conversions: int = Field(default=0, ge=0, description="Total conversions")
    revenue: float = Field(default=0.0, ge=0, description="Attributed revenue")
    spend: float = Field(default=0.0, ge=0, description="Campaign spend")
    ctr: float = Field(default=0.0, ge=0, description="Click-through rate")
    conversion_rate: float = Field(default=0.0, ge=0, description="Conversion rate")
    roas: float = Field(default=0.0, ge=0, description="Return on ad spend")
    cpc: float = Field(default=0.0, ge=0, description="Cost per click")


class AnalyticsReport(BaseModel):
    """Comprehensive analytics report."""

    report_id: str = Field(..., description="Report identifier")
    campaign_id: str = Field(..., description="Campaign identifier")
    metrics: CampaignMetrics = Field(..., description="Campaign metrics")
    insights: list[str] = Field(default_factory=list, description="AI-generated insights")
    recommendations: list[str] = Field(
        default_factory=list, description="Optimization recommendations"
    )
    generated_at: str = Field(..., description="Report generation timestamp")


class AnalyticsAgent:
    """AI agent for campaign analytics and performance reporting.

    Analyzes campaign performance data, generates insights, and provides
    actionable recommendations for optimization.
    """

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the analytics agent.

        Args:
            llm: Optional LangChain chat model. If not provided, uses the default
                model from settings.
        """
        self.settings = get_settings()
        self.llm = llm or self._create_default_llm()
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert e-commerce marketing analyst. "
                    "Analyze campaign performance data and provide actionable insights. "
                    "Focus on ROI, conversion optimization, and growth opportunities. "
                    "Output valid JSON with insights and recommendations arrays.",
                ),
                (
                    "human",
                    "Campaign ID: {campaign_id}\n"
                    "Metrics:\n"
                    "- Impressions: {impressions}\n"
                    "- Clicks: {clicks}\n"
                    "- Conversions: {conversions}\n"
                    "- Revenue: ${revenue}\n"
                    "- Spend: ${spend}\n"
                    "- CTR: {ctr:.2%}\n"
                    "- Conversion Rate: {conversion_rate:.2%}\n"
                    "- ROAS: {roas:.2f}\n"
                    "- CPC: ${cpc:.2f}\n\n"
                    "Provide insights and recommendations for this campaign.",
                ),
            ]
        )

    def _create_default_llm(self) -> BaseChatModel:
        """Create the default LLM from settings.

        Returns:
            Configured LangChain chat model.

        Raises:
            ValueError: If OPENAI_API_KEY is not configured.
        """
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise ImportError(
                "langchain-openai is required for default LLM. "
                "Install with: pip install langchain-openai"
            ) from exc

        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for analytics")

        return ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            temperature=0.3,
            max_tokens=1500,
        )

    def calculate_metrics(
        self,
        campaign_id: str,
        impressions: int,
        clicks: int,
        conversions: int,
        revenue: float,
        spend: float,
    ) -> CampaignMetrics:
        """Calculate derived campaign metrics.

        Args:
            campaign_id: Campaign identifier.
            impressions: Total impressions.
            clicks: Total clicks.
            conversions: Total conversions.
            revenue: Attributed revenue.
            spend: Campaign spend.

        Returns:
            Campaign metrics with derived values.
        """
        ctr = clicks / impressions if impressions > 0 else 0.0
        conversion_rate = conversions / clicks if clicks > 0 else 0.0
        roas = revenue / spend if spend > 0 else 0.0
        cpc = spend / clicks if clicks > 0 else 0.0

        return CampaignMetrics(
            campaign_id=campaign_id,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            revenue=revenue,
            spend=spend,
            ctr=ctr,
            conversion_rate=conversion_rate,
            roas=roas,
            cpc=cpc,
        )

    async def generate_report(self, metrics: CampaignMetrics) -> AnalyticsReport:
        """Generate an AI-powered analytics report for a campaign.

        Args:
            metrics: Campaign performance metrics.

        Returns:
            Analytics report with insights and recommendations.
        """
        logger.info(
            "Generating analytics report",
            campaign_id=metrics.campaign_id,
            roas=metrics.roas,
        )

        chain = self._prompt | self.llm
        response = await chain.ainvoke(
            {
                "campaign_id": metrics.campaign_id,
                "impressions": metrics.impressions,
                "clicks": metrics.clicks,
                "conversions": metrics.conversions,
                "revenue": f"{metrics.revenue:.2f}",
                "spend": f"{metrics.spend:.2f}",
                "ctr": metrics.ctr,
                "conversion_rate": metrics.conversion_rate,
                "roas": metrics.roas,
                "cpc": metrics.cpc,
            }
        )

        insights, recommendations = self._parse_report(
            response.content if hasattr(response, "content") else str(response)
        )

        report = AnalyticsReport(
            report_id="",
            campaign_id=metrics.campaign_id,
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            generated_at="",
        )

        logger.info(
            "Analytics report generated",
            report_id=report.report_id,
            campaign_id=metrics.campaign_id,
            num_insights=len(insights),
        )

        return report

    def _parse_report(self, llm_output: str) -> tuple[list[str], list[str]]:
        """Parse LLM output into insights and recommendations.

        Args:
            llm_output: Raw text output from the LLM.

        Returns:
            Tuple of (insights, recommendations) lists.
        """
        import json

        try:
            data = json.loads(llm_output)
            return data.get("insights", []), data.get("recommendations", [])
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse analytics report, using fallback")
            return (
                ["Campaign is performing within expected parameters"],
                ["Continue monitoring performance trends"],
            )
