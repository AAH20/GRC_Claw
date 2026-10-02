"""Revenue Tracker Agent using LangChain DeepAgents."""

from typing import Any
import structlog
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import tool

from creator_analytics.agents.base import BaseCreatorAgent
from creator_analytics.models.revenue import RevenueReport, RevenueBreakdown, RevenueStream

logger = structlog.get_logger(__name__)


@tool
def calculate_revenue_per_follower(total_revenue: float, total_followers: int) -> float:
    """Calculate revenue per follower metric.

    Args:
        total_revenue: Total revenue amount.
        total_followers: Total number of followers.

    Returns:
        Revenue per follower.
    """
    if total_followers == 0:
        return 0.0
    return total_revenue / total_followers


@tool
def project_annual_revenue(monthly_revenue: float, growth_rate: float) -> float:
    """Project annual revenue based on current monthly revenue and growth rate.

    Args:
        monthly_revenue: Current monthly revenue.
        growth_rate: Monthly growth rate as a decimal.

    Returns:
        Projected annual revenue.
    """
    # Compound growth over 12 months
    projected = monthly_revenue * ((1 + growth_rate) ** 12)
    return projected


@tool
def analyze_revenue_streams(stream_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Analyze revenue streams and identify top performers.

    Args:
        stream_data: List of revenue stream data.

    Returns:
        Analyzed revenue stream data with percentages.
    """
    total = sum(s.get("amount", 0) for s in stream_data)
    analyzed = []

    for stream in stream_data:
        amount = stream.get("amount", 0)
        percentage = (amount / total * 100) if total > 0 else 0
        analyzed.append({
            **stream,
            "percentage_of_total": percentage,
        })

    return sorted(analyzed, key=lambda x: x["amount"], reverse=True)


@tool
def identify_revenue_opportunities(
    current_streams: list[str],
    audience_size: int,
    engagement_rate: float,
) -> list[str]:
    """Identify potential new revenue opportunities.

    Args:
        current_streams: Current revenue streams.
        audience_size: Total audience size.
        engagement_rate: Current engagement rate.

    Returns:
        List of recommended revenue opportunities.
    """
    opportunities = []

    if "subscriptions" not in current_streams and audience_size > 10000:
        opportunities.append("Consider launching a subscription/membership program")

    if "merchandise" not in current_streams and engagement_rate > 0.05:
        opportunities.append("Merchandise could perform well with your engaged audience")

    if "sponsorships" not in current_streams and audience_size > 50000:
        opportunities.append("Your audience size attracts brand sponsorships")

    if "affiliate" not in current_streams:
        opportunities.append("Affiliate marketing is a low-effort revenue stream")

    if "courses" not in current_streams and engagement_rate > 0.03:
        opportunities.append("Online courses could monetize your expertise")

    return opportunities


class RevenueTrackerAgent(BaseCreatorAgent):
    """Agent for tracking and analyzing creator revenue streams."""

    def __init__(self, llm: BaseLanguageModel | None = None) -> None:
        """Initialize the Revenue Tracker Agent.

        Args:
            llm: Language model for agent reasoning.
        """
        super().__init__(llm=llm, name="revenue_tracker")

    def _get_instructions(self) -> str:
        """Get system instructions for the revenue tracker agent."""
        return (
            "You are an expert revenue analyst for content creators. "
            "Track revenue streams, analyze performance, and identify "
            "new monetization opportunities. Focus on maximizing "
            "revenue while maintaining audience trust."
        )

    def _get_tools(self) -> list[Any]:
        """Get tools available to the revenue tracker agent."""
        return [
            calculate_revenue_per_follower,
            project_annual_revenue,
            analyze_revenue_streams,
            identify_revenue_opportunities,
        ]

    async def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run revenue tracking analysis.

        Args:
            input_data: Dictionary containing:
                - creator_id: Creator identifier
                - report_period_start: Start of reporting period
                - report_period_end: End of reporting period
                - stream_data: Revenue data by stream
                - total_followers: Total follower count
                - engagement_rate: Current engagement rate

        Returns:
            Revenue report with analysis.
        """
        try:
            creator_id = input_data.get("creator_id", "")
            stream_data = input_data.get("stream_data", [])
            total_followers = input_data.get("total_followers", 0)
            engagement_rate = input_data.get("engagement_rate", 0.0)

            logger.info(f"Tracking revenue for creator {creator_id}")

            # Analyze revenue streams
            analyzed_streams = analyze_revenue_streams(stream_data)

            # Build breakdown
            breakdown = []
            total_revenue = 0.0
            for stream in analyzed_streams:
                amount = stream.get("amount", 0)
                total_revenue += amount
                breakdown.append(RevenueBreakdown(
                    stream=RevenueStream(stream.get("stream", "advertising")),
                    amount=amount,
                    currency=stream.get("currency", "USD"),
                    percentage_of_total=stream.get("percentage_of_total", 0),
                    growth_rate=stream.get("growth_rate", 0),
                    transactions=stream.get("transactions", 0),
                    average_transaction_value=stream.get("average_transaction_value", 0),
                ))

            # Calculate metrics
            rev_per_follower = calculate_revenue_per_follower(total_revenue, total_followers)
            monthly_recurring = sum(
                s.amount for s in breakdown if s.stream in [RevenueStream.SUBSCRIPTIONS, RevenueStream.MEMBERSHIPS]
            )
            one_time = total_revenue - monthly_recurring

            # Project annual revenue
            avg_growth = sum(s.growth_rate for s in breakdown) / len(breakdown) if breakdown else 0
            projected_annual = project_annual_revenue(total_revenue, avg_growth)

            # Identify opportunities
            current_streams = [s.get("stream", "") for s in stream_data]
            opportunities = identify_revenue_opportunities(
                current_streams, total_followers, engagement_rate
            )

            # Use DeepAgent for deeper analysis
            if self._agent:
                agent_result = await self._agent.arun(
                    f"Analyze revenue for creator {creator_id}. "
                    f"Total revenue: {total_revenue}. "
                    f"Breakdown: {[s.model_dump() for s in breakdown]}. "
                    f"Opportunities: {opportunities}. "
                    f"Provide insights and recommendations."
                )
                insights = agent_result.get("insights", []) if isinstance(agent_result, dict) else []
                recommendations = agent_result.get("recommendations", []) if isinstance(agent_result, dict) else []
            else:
                insights = []
                recommendations = opportunities

            report = RevenueReport(
                creator_id=creator_id,
                report_period_start=input_data.get("report_period_start", ""),
                report_period_end=input_data.get("report_period_end", ""),
                total_revenue=total_revenue,
                currency="USD",
                breakdown=breakdown,
                recurring_revenue=monthly_recurring,
                one_time_revenue=one_time,
                projected_annual_revenue=projected_annual,
                revenue_per_follower=rev_per_follower,
                top_performing_content=input_data.get("top_performing_content", []),
                insights=insights,
                recommendations=recommendations,
            )

            return report.model_dump()

        except Exception as e:
            logger.error(f"Revenue tracking failed: {e}")
            raise
