# AI-Powered PPC Management Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Stack:** LangChain DeepAgents, Python 3.11+, Google Ads API, OpenAI GPT-4o

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Keyword Research Agent](#2-keyword-research-agent)
3. [Bid Management Agent](#3-bid-management-agent)
4. [Ad Creative Agent](#4-ad-creative-agent)
5. [Landing Page Optimization Agent](#5-landing-page-optimization-agent)
6. [Budget Allocation Agent](#6-budget-allocation-agent)
7. [Performance Analytics Agent](#7-performance-analytics-agent)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Design

The PPC management system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. A central **PPC Orchestrator Agent** coordinates six specialized sub-agents, each responsible for a distinct aspect of PPC campaign management.

```
┌─────────────────────────────────────────────────────────────┐
│                    PPC Orchestrator Agent                     │
│  (LangChain DeepAgent — plans, delegates, synthesizes)       │
└──────────┬──────────┬──────────┬──────────┬──────────┬───────┘
           │          │          │          │          │
    ┌──────▼──┐ ┌─────▼────┐ ┌───▼─────┐ ┌──▼──────┐ ┌─▼──────────┐
    │ Keyword │ │   Bid    │ │   Ad    │ │ Landing │ │  Budget    │
    │Research │ │Management│ │Creative │ │  Page   │ │Allocation  │
    │  Agent  │ │  Agent   │ │  Agent  │ │  Agent  │ │   Agent    │
    └────┬────┘ └────┬─────┘ └────┬────┘ └────┬────┘ └─────┬──────┘
         │           │            │           │            │
    ┌────▼───────────▼────────────▼───────────▼────────────▼────┐
    │              Shared State & Memory Layer                    │
    │   (Redis + PostgreSQL + Vector Store for embeddings)       │
    └────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents | Multi-agent orchestration, tool calling, planning |
| LLM | OpenAI GPT-4o | Reasoning, content generation, decision-making |
| State Store | Redis | Real-time campaign state, session memory |
| Persistent Store | PostgreSQL | Historical performance data, audit logs |
| Vector Store | pgvector / ChromaDB | Semantic keyword clustering, ad similarity |
| APIs | Google Ads API, Bing Ads API | Campaign management, reporting |
| Monitoring | LangSmith | Tracing, evaluation, observability |
| Task Queue | Celery + Redis | Async agent task execution |

### 1.3 Shared State Schema

```python
# models/campaign_state.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class CampaignStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    PENDING_REVIEW = "pending_review"
    OPTIMIZING = "optimizing"

class CampaignState(BaseModel):
    """Shared state accessible by all agents."""
    campaign_id: str
    campaign_name: str
    status: CampaignStatus
    platform: str  # "google_ads" | "bing_ads"
    daily_budget: float
    total_budget: float
    spent_to_date: float
    start_date: datetime
    end_date: Optional[datetime] = None
    target_cpa: Optional[float] = None
    target_roas: Optional[float] = None
    keywords: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)
    ad_groups: list[dict] = Field(default_factory=list)
    performance_metrics: dict = Field(default_factory=dict)
    last_optimized: Optional[datetime] = None
    optimization_history: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
```

### 1.4 Orchestrator Agent

```python
# agents/orchestrator.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from typing import Literal

class PPCOrchestrator:
    """
    Central orchestrator that plans PPC optimization workflows,
    delegates to specialized agents, and synthesizes results.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            max_tokens=4096,
        )
        self.agent = DeepAgent(
            name="ppc_orchestrator",
            llm=self.llm,
            system_prompt=self._system_prompt(),
            tools=[
                self.keyword_research_tool,
                self.bid_management_tool,
                self.ad_creative_tool,
                self.landing_page_tool,
                self.budget_allocation_tool,
                self.performance_analytics_tool,
            ],
            sub_agents={
                "keyword_research": KeywordResearchAgent(),
                "bid_management": BidManagementAgent(),
                "ad_creative": AdCreativeAgent(),
                "landing_page": LandingPageAgent(),
                "budget_allocation": BudgetAllocationAgent(),
                "performance_analytics": PerformanceAnalyticsAgent(),
            },
        )

    def _system_prompt(self) -> str:
        return """You are the PPC Orchestrator Agent, responsible for managing
        and optimizing pay-per-click advertising campaigns across Google Ads and Bing Ads.

        Your responsibilities:
        1. Analyze campaign performance data and identify optimization opportunities
        2. Delegate tasks to specialized sub-agents based on the optimization needed
        3. Synthesize results from multiple agents into coherent action plans
        4. Ensure all changes comply with platform policies and budget constraints
        5. Maintain a feedback loop — track the impact of every optimization

        Decision framework:
        - If CPA > target_cpa by >20% → trigger Bid Management Agent
        - If CTR < industry benchmark → trigger Ad Creative Agent
        - If conversion rate < 2% → trigger Landing Page Agent
        - If budget utilization < 80% → trigger Budget Allocation Agent
        - If new campaign or quarterly review → trigger Keyword Research Agent
        - Always run Performance Analytics Agent after any optimization

        Always explain your reasoning before delegating. Log all decisions."""

    async def run_optimization_cycle(
        self,
        campaign_id: str,
        cycle_type: Literal["daily", "weekly", "monthly", "triggered"] = "daily",
    ) -> dict:
        """Execute a full optimization cycle for a campaign."""
        state = await self._load_campaign_state(campaign_id)

        # Step 1: Performance analysis
        perf_result = await self.agent.invoke(
            f"Analyze performance for campaign {campaign_id}. "
            f"Current metrics: {state.performance_metrics}. "
            f"Identify the top 3 optimization opportunities."
        )

        # Step 2: Plan and delegate
        plan = await self.agent.invoke(
            f"Based on this analysis: {perf_result}, create an optimization plan. "
            f"Specify which agents to invoke and in what order."
        )

        # Step 3: Execute plan
        results = []
        for step in plan["steps"]:
            agent_name = step["agent"]
            task = step["task"]
            result = await self.agent.invoke(
                f"Delegate to {agent_name}: {task}",
                agent_name=agent_name,
            )
            results.append({
                "agent": agent_name,
                "task": task,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            })

        # Step 4: Synthesize and log
        summary = await self.agent.invoke(
            f"Synthesize these optimization results into a summary report: {results}"
        )

        await self._save_optimization_record(campaign_id, results, summary)
        return {"plan": plan, "results": results, "summary": summary}
```

---

## 2. Keyword Research Agent

### 2.1 Purpose

Discovers, evaluates, and recommends keywords for PPC campaigns using search volume data, competition analysis, semantic clustering, and historical performance.

### 2.2 Architecture

```python
# agents/keyword_research.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_community.tools import GoogleSearchAPIWrapper
import asyncio

class KeywordResearchAgent(DeepAgent):
    """
    Specialized agent for keyword discovery, analysis, and recommendation.
    Uses search APIs, competitor analysis, and historical performance data.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        super().__init__(
            name="keyword_research",
            llm=self.llm,
            system_prompt=self._system_prompt(),
            tools=[
                self.search_keyword_ideas,
                self.analyze_keyword_metrics,
                self.cluster_keywords_semantically,
                self.analyze_competitor_keywords,
                self.estimate_keyword_performance,
                self.generate_negative_keywords,
            ],
        )

    def _system_prompt(self) -> str:
        return """You are the Keyword Research Agent, an expert in PPC keyword
        strategy and search engine marketing.

        Your capabilities:
        1. Generate keyword ideas from seed terms using search APIs and LLM knowledge
        2. Analyze keyword metrics: search volume, CPC, competition level, trend
        3. Cluster keywords semantically for ad group organization
        4. Spy on competitor keyword strategies
        5. Estimate performance potential using historical data patterns
        6. Generate negative keyword lists to reduce wasted spend

        Methodology:
        - Always start with seed keywords from the campaign context
        - Expand using long-tail variations, question keywords, and LSI terms
        - Score keywords on: relevance (1-10), volume potential (1-10),
          competition (1-10, lower is better), strategic value (1-10)
        - Group into tightly-themed ad groups (5-20 keywords per group)
        - Identify negative keywords from irrelevant search term reports

        Output format: Structured keyword recommendations with scores,
        suggested match types, and ad group assignments."""

    @tool
    async def search_keyword_ideas(
        self,
        seed_keywords: list[str],
        industry: str,
        location: str = "US",
        language: str = "en",
    ) -> list[dict]:
        """Generate keyword ideas from seed terms using LLM and search data."""
        prompt = f"""Generate 50 keyword ideas for a PPC campaign in the {industry}
        industry targeting {location} in {language}.

        Seed keywords: {seed_keywords}

        For each keyword, provide:
        - keyword: the keyword phrase
        - match_type: "exact" | "phrase" | "broad"
        - estimated_monthly_searches: integer
        - estimated_cpc: float (USD)
        - competition: "low" | "medium" | "high"
        - relevance_score: 1-10
        - intent: "informational" | "navigational" | "transactional" | "commercial"
        - suggested_ad_group: string

        Return as a JSON array."""

        response = await self.llm.ainvoke(prompt)
        return self._parse_keyword_response(response.content)

    @tool
    async def analyze_keyword_metrics(
        self,
        keywords: list[str],
        campaign_id: str,
    ) -> list[dict]:
        """Fetch and analyze performance metrics for existing keywords."""
        from google.ads.googleads.client import GoogleAdsClient

        client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                keyword_view.resource_name,
                segments.keyword.info.text,
                segments.keyword.info.match_type,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.conversions_per_interaction,
                metrics.cost_per_conversion
            FROM keyword_view
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING LAST_30_DAYS
            ORDER BY metrics.cost_micros DESC
        """

        response = service.search(customer_id=self._customer_id, query=query)
        return self._transform_keyword_metrics(response)

    @tool
    async def cluster_keywords_semantically(
        self,
        keywords: list[str],
        n_clusters: int = 10,
    ) -> dict[str, list[str]]:
        """Cluster keywords by semantic similarity for ad group organization."""
        from langchain_openai import OpenAIEmbeddings
        from sklearn.cluster import KMeans
        import numpy as np

        embeddings = OpenAIEmbeddings()
        vectors = await embeddings.aembed_documents(keywords)

        kmeans = KMeans(n_clusters=min(n_clusters, len(keywords)), random_state=42)
        labels = kmeans.fit_predict(np.array(vectors))

        clusters = {}
        for keyword, label in zip(keywords, labels):
            cluster_name = f"ad_group_{label}"
            clusters.setdefault(cluster_name, []).append(keyword)

        return clusters

    @tool
    async def analyze_competitor_keywords(
        self,
        competitor_domains: list[str],
        industry: str,
    ) -> dict:
        """Analyze competitor keyword strategies using available data."""
        prompt = f"""Analyze the PPC keyword strategy for these competitors:
        {competitor_domains} in the {industry} industry.

        Identify:
        1. Likely target keywords based on their landing pages and ad copy
        2. Keyword gaps — terms they rank for that we don't target
        3. Their estimated budget allocation across keyword themes
        4. Seasonal patterns in their strategy

        Return structured analysis."""

        response = await self.llm.ainvoke(prompt)
        return {"analysis": response.content, "competitors": competitor_domains}

    @tool
    async def estimate_keyword_performance(
        self,
        keywords: list[str],
        historical_data: dict,
    ) -> list[dict]:
        """Estimate performance potential using historical patterns."""
        prompt = f"""Based on this historical performance data:
        {historical_data}

        Estimate the 30-day performance for these keywords:
        {keywords}

        For each keyword, estimate:
        - expected_impressions
        - expected_clicks
        - expected_ctr
        - expected_cpc
        - expected_conversions
        - expected_cpa
        - confidence: "high" | "medium" | "low"

        Use patterns from similar keywords in the historical data."""

        response = await self.llm.ainvoke(prompt)
        return self._parse_performance_estimates(response.content)

    @tool
    async def generate_negative_keywords(
        self,
        search_terms: list[str],
        campaign_context: dict,
    ) -> list[str]:
        """Generate negative keywords from irrelevant search terms."""
        prompt = f"""Given these actual search terms that triggered ads:
        {search_terms}

        And this campaign context:
        {campaign_context}

        Identify which search terms are irrelevant and should be added as
        negative keywords. Return a list of negative keyword phrases with
        their match types (exact or phrase).

        Focus on:
        - Unrelated product/service searches
        - Free/cheap intent when selling premium
        - Job seekers, students, or informational queries
        - Competitor brand names (if not allowed)
        - Geographic mismatches"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_negative_keywords(response.content)
```

### 2.3 Integration with Google Ads API

```python
# services/keyword_service.py
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

class KeywordService:
    """Service layer for keyword operations via Google Ads API."""

    def __init__(self, customer_id: str, campaign_id: str):
        self.client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        self.customer_id = customer_id
        self.campaign_id = campaign_id

    async def add_keywords(
        self,
        ad_group_id: str,
        keywords: list[dict],
    ) -> list[str]:
        """Add keywords to an ad group with specified match types."""
        operations = []
        for kw in keywords:
            operation = self.client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = f"customers/{self.customer_id}/adGroups/{ad_group_id}"
            criterion.keyword.text = kw["keyword"]
            criterion.keyword.match_type = self.client.enums.KeywordMatchType[kw["match_type"].upper()]
            criterion.status = self.client.enums.AdGroupCriterionStatus.ENABLED

            if "bid" in kw:
                criterion.cpc_bid_micros = int(kw["bid"] * 1_000_000)

            operations.append(operation)

        try:
            response = self.client.get_service("AdGroupCriterionService").mutate_ad_group_criteria(
                customer_id=self.customer_id,
                operations=operations,
            )
            return [r.resource_name for r in response.results]
        except GoogleAdsException as e:
            self._handle_api_error(e)

    async def add_negative_keywords(
        self,
        campaign_id: str,
        negative_keywords: list[dict],
    ) -> list[str]:
        """Add campaign-level negative keywords."""
        operations = []
        for nk in negative_keywords:
            operation = self.client.get_type("CampaignCriterionOperation")
            criterion = operation.create
            criterion.campaign = f"customers/{self.customer_id}/campaigns/{campaign_id}"
            criterion.negative = True
            criterion.keyword.text = nk["keyword"]
            criterion.keyword.match_type = self.client.enums.KeywordMatchType[nk["match_type"].upper()]
            operations.append(operation)

        response = self.client.get_service("CampaignCriterionService").mutate_campaign_criteria(
            customer_id=self.customer_id,
            operations=operations,
        )
        return [r.resource_name for r in response.results]
```

---

## 3. Bid Management Agent

### 3.1 Purpose

Automatically adjusts keyword and ad group bids to maximize conversions while staying within target CPA/ROAS constraints. Uses portfolio bid strategies, manual CPC adjustments, and smart bidding recommendations.

### 3.2 Architecture

```python
# agents/bid_management.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from datetime import datetime, timedelta

class BidManagementAgent(DeepAgent):
    """
    Specialized agent for bid optimization across campaigns.
    Balances automation (smart bidding) with manual overrides.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        super().__init__(
            name="bid_management",
            llm=self.llm,
            system_prompt=self._system_prompt(),
            tools=[
                self.analyze_bid_performance,
                self.calculate_optimal_bids,
                self.apply_bid_adjustments,
                self.set_portfolio_bid_strategy,
                self.analyze_auction_insights,
                self.forecast_bid_impact,
            ],
        )

    def _system_prompt(self) -> str:
        return """You are the Bid Management Agent, an expert in PPC bid optimization
        and auction dynamics.

        Your responsibilities:
        1. Analyze current bid performance vs. targets (CPA, ROAS, CTR)
        2. Calculate optimal bids using historical conversion data
        3. Apply bid adjustments with proper change limits
        4. Recommend portfolio bid strategies for scale
        5. Monitor auction insights for competitive pressure
        6. Forecast the impact of bid changes before applying

        Bid management rules:
        - Never change bids by more than 30% in a single adjustment
        - Wait at least 3 days between bid changes for the same keyword
        - Consider dayparting: adjust bids by hour/day based on conversion patterns
        - Use Target CPA for campaigns with >30 conversions/month
        - Use Target ROAS for e-commerce with revenue tracking
        - Use Manual CPC for new campaigns or low-volume keywords
        - Always maintain a 15% buffer below max CPC to avoid overspending

        Change management:
        - Log every bid change with reasoning
        - Track performance before/after each change
        - Roll back changes that degrade performance by >15%
        - Escalate to human review for changes >$5/day impact"""

    @tool
    async def analyze_bid_performance(
        self,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS",
    ) -> dict:
        """Analyze current bid performance against targets."""
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.bidding_strategy_type,
                campaign.target_cpa.target_cpa_micros,
                campaign.target_roas.target_roas,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_per_conversion,
                metrics.conversions_per_interaction,
                metrics.value_per_conversion,
                metrics.search_impression_share,
                metrics.search_budget_lost_impression_share,
                metrics.search_rank_lost_impression_share
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING {date_range}
        """

        data = await self._execute_query(query)
        return self._calculate_bid_health_score(data)

    @tool
    async def calculate_optimal_bids(
        self,
        keywords: list[dict],
        target_cpa: float,
        target_roas: float,
        constraints: dict,
    ) -> list[dict]:
        """Calculate optimal CPC bids for each keyword."""
        prompt = f"""Calculate optimal CPC bids for these keywords:
        {keywords}

        Constraints:
        - Target CPA: ${target_cpa}
        - Target ROAS: {target_roas * 100}%
        - Max daily budget: ${constraints.get('max_daily_budget', 500)}
        - Min CPC: ${constraints.get('min_cpc', 0.10)}
        - Max CPC: ${constraints.get('max_cpc', 50.00)}
        - Max change: 30% from current bid

        For each keyword, calculate:
        - current_cpc
        - recommended_cpc
        - change_percent
        - expected_impressions_change
        - expected_conversions_change
        - expected_cost_change
        - confidence_score
        - reasoning

        Use the formula: optimal_cpc = (conversion_rate * conversion_value) / (1 + target_roas_margin)
        Adjust for keyword quality score and historical performance."""

        response = await self.llm.ainvoke(prompt)
        return self._parse_bid_recommendations(response.content)

    @tool
    async def apply_bid_adjustments(
        self,
        campaign_id: str,
        bid_changes: list[dict],
        dry_run: bool = True,
    ) -> dict:
        """Apply bid adjustments to keywords or ad groups."""
        if dry_run:
            return {
                "status": "dry_run",
                "changes": bid_changes,
                "total_impact": self._calculate_total_impact(bid_changes),
            }

        results = []
        for change in bid_changes:
            try:
                if change["level"] == "keyword":
                    result = await self._update_keyword_bid(
                        campaign_id=campaign_id,
                        criterion_id=change["criterion_id"],
                        new_bid=change["recommended_cpc"],
                    )
                elif change["level"] == "ad_group":
                    result = await self._update_ad_group_bid(
                        campaign_id=campaign_id,
                        ad_group_id=change["ad_group_id"],
                        new_bid=change["recommended_cpc"],
                    )
                results.append({"change": change, "result": result, "status": "success"})
            except Exception as e:
                results.append({"change": change, "error": str(e), "status": "failed"})

        # Log all changes
        await self._log_bid_changes(campaign_id, results)
        return {"status": "applied", "results": results}

    @tool
    async def set_portfolio_bid_strategy(
        self,
        campaign_ids: list[str],
        strategy_type: str,
        target_value: float,
    ) -> dict:
        """Set up a portfolio bid strategy across multiple campaigns."""
        # Create portfolio bid strategy
        portfolio_service = self.client.get_service("BiddingStrategyService")
        bidding_strategy = self.client.get_type("BiddingStrategy")

        bidding_strategy.name = f"Portfolio_{strategy_type}_{datetime.now().strftime('%Y%m%d')}"
        bidding_strategy.type_ = self.client.enums.BiddingStrategyType[strategy_type.upper()]

        if strategy_type == "target_cpa":
            bidding_strategy.target_cpa.target_cpa_micros = int(target_value * 1_000_000)
        elif strategy_type == "target_roas":
            bidding_strategy.target_roas.target_roas = target_value

        operation = self.client.get_type("BiddingStrategyOperation")
        operation.create.CopyFrom(bidding_strategy)

        response = portfolio_service.mutate_bidding_strategies(
            customer_id=self.customer_id,
            operations=[operation],
        )

        portfolio_id = response.results[0].resource_name.split("/")[-1]

        # Assign campaigns to portfolio
        campaign_service = self.client.get_service("CampaignService")
        for campaign_id in campaign_ids:
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign_operation.update.resource_name = (
                f"customers/{self.customer_id}/campaigns/{campaign_id}"
            )
            campaign_operation.update.bidding_strategy = (
                f"customers/{self.customer_id}/biddingStrategies/{portfolio_id}"
            )
            campaign_operation.update_mask.paths.append("bidding_strategy")
            campaign_service.mutate_campaigns(
                customer_id=self.customer_id,
                operations=[campaign_operation],
            )

        return {
            "portfolio_id": portfolio_id,
            "strategy_type": strategy_type,
            "target_value": target_value,
            "assigned_campaigns": campaign_ids,
        }

    @tool
    async def analyze_auction_insights(
        self,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS",
    ) -> dict:
        """Analyze auction insights to understand competitive landscape."""
        query = f"""
            SELECT
                auction_insight_domain_metrics.domain,
                auction_insight_domain_metrics.impression_share,
                auction_insight_domain_metrics.overall_top_impression_share,
                auction_insight_domain_metrics.outranking_share,
                auction_insight_domain_metrics.page_overlap_rate,
                auction_insight_domain_metrics.top_impression_percentage,
                metrics.impressions,
                metrics.average_cpc
            FROM auction_insights
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING {date_range}
            ORDER BY auction_insight_domain_metrics.impression_share DESC
            LIMIT 20
        """

        data = await self._execute_query(query)
        return {
            "top_competitors": data,
            "avg_impression_share": self._calculate_avg_share(data),
            "competitive_pressure": self._assess_competitive_pressure(data),
            "recommendations": self._generate_auction_recommendations(data),
        }

    @tool
    async def forecast_bid_impact(
        self,
        bid_changes: list[dict],
        historical_data: dict,
    ) -> dict:
        """Forecast the impact of proposed bid changes."""
        prompt = f"""Forecast the 30-day impact of these bid changes:
        {bid_changes}

        Based on this historical data:
        {historical_data}

        Estimate for each change:
        - Expected impression change (%)
        - Expected click change (%)
        - Expected cost change (%)
        - Expected conversion change (%)
        - Expected CPA change (%)
        - Risk level: "low" | "medium" | "high"
        - Confidence interval (95%)

        Also provide:
        - Total portfolio impact
        - Best case / worst case scenarios
        - Recommended monitoring checkpoints (day 1, 3, 7, 14, 30)"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_forecast(response.content)
```

### 3.3 Bid Adjustment Service

```python
# services/bid_service.py
class BidService:
    """Service layer for bid operations via Google Ads API."""

    def __init__(self, customer_id: str):
        self.client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        self.customer_id = customer_id

    async def update_keyword_bid(
        self,
        campaign_id: str,
        criterion_id: str,
        new_bid: float,
    ) -> str:
        """Update a keyword's CPC bid."""
        operation = self.client.get_type("AdGroupCriterionOperation")
        criterion = operation.update
        criterion.resource_name = (
            f"customers/{self.customer_id}/adGroupCriteria/{campaign_id}~{criterion_id}"
        )
        criterion.cpc_bid_micros = int(new_bid * 1_000_000)

        field_mask = self.client.get_type("FieldMask")
        field_mask.paths.append("cpc_bid_micros")
        operation.update_mask.CopyFrom(field_mask)

        response = self.client.get_service("AdGroupCriterionService").mutate_ad_group_criteria(
            customer_id=self.customer_id,
            operations=[operation],
        )
        return response.results[0].resource_name

    async def update_ad_group_bid(
        self,
        campaign_id: str,
        ad_group_id: str,
        new_bid: float,
    ) -> str:
        """Update an ad group's default CPC bid."""
        operation = self.client.get_type("AdGroupOperation")
        ad_group = operation.update
        ad_group.resource_name = (
            f"customers/{self.customer_id}/adGroups/{ad_group_id}"
        )
        ad_group.cpc_bid_micros = int(new_bid * 1_000_000)

        field_mask = self.client.get_type("FieldMask")
        field_mask.paths.append("cpc_bid_micros")
        operation.update_mask.CopyFrom(field_mask)

        response = self.client.get_service("AdGroupService").mutate_ad_groups(
            customer_id=self.customer_id,
            operations=[operation],
        )
        return response.results[0].resource_name

    async def set_bid_modifier(
        self,
        campaign_id: str,
        device_type: str,
        modifier: float,
    ) -> str:
        """Set device-level bid modifier (e.g., +20% for mobile)."""
        operation = self.client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = f"customers/{self.customer_id}/campaigns/{campaign_id}"
        criterion.device.type = self.client.enums.DeviceType[device_type.upper()]
        criterion.bid_modifier = modifier

        response = self.client.get_service("CampaignCriterionService").mutate_campaign_criteria(
            customer_id=self.customer_id,
            operations=[operation],
        )
        return response.results[0].resource_name
```

---

## 4. Ad Creative Agent

### 4.1 Purpose

Generates, tests, and optimizes ad copy across responsive search ads, expanded text ads, and display ads. Uses A/B testing frameworks, performance data, and LLM-powered copy generation.

### 4.2 Architecture

```python
# agents/ad_creative.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

class AdCreativeAgent(DeepAgent):
    """
    Specialized agent for ad copy generation, testing, and optimization.
    Creates headlines, descriptions, and full ad variations.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        super().__init__(
            name="ad_creative",
            llm=self.llm,
            system_prompt=self._system_prompt(),
            tools=[
                self.generate_ad_variations,
                self.analyze_ad_performance,
                self.run_ab_test,
                self.optimize_ad_copy,
                self.generate_responsive_search_ad,
                self.analyze_ad_strength,
            ],
        )

    def _system_prompt(self) -> str:
        return """You are the Ad Creative Agent, an expert in PPC advertising copy
        and conversion-focused writing.

        Your capabilities:
        1. Generate compelling ad copy (headlines, descriptions, CTAs)
        2. Analyze ad performance metrics (CTR, conversion rate, quality score)
        3. Design and manage A/B tests for ad variations
        4. Optimize existing ad copy based on performance data
        5. Create responsive search ads with multiple headline/description combinations
        6. Evaluate ad strength and provide improvement recommendations

        Ad copy principles:
        - Lead with the primary value proposition
        - Include target keywords naturally in headlines
        - Use numbers, specifics, and social proof when available
        - Create urgency without being misleading
        - Match landing page message to ad copy (message match)
        - Include a clear call-to-action
        - Comply with Google Ads character limits:
          * Headlines: 30 characters max (15 recommended)
          * Descriptions: 90 characters max (80 recommended)
          * Responsive search ads: 15 headlines, 4 descriptions minimum

        Testing methodology:
        - Test one variable at a time (headline, description, CTA, or display path)
        - Run tests for minimum 2 weeks or 1,000 impressions per variation
        - Use 95% confidence level for statistical significance
        - Document learnings for future ad creation

        Output format: Structured ad copy with headlines, descriptions,
        display paths, and extension recommendations."""

    @tool
    async def generate_ad_variations(
        self,
        product_info: dict,
        target_audience: str,
        campaign_goal: str,
        num_variations: int = 5,
    ) -> list[dict]:
        """Generate multiple ad copy variations for testing."""
        prompt = f"""Generate {num_variations} ad copy variations for a PPC campaign.

        Product/Service: {product_info}
        Target Audience: {target_audience}
        Campaign Goal: {campaign_goal}

        For each variation, provide:
        - headlines: list of 15 headlines (max 30 chars each)
        - descriptions: list of 4 descriptions (max 90 chars each)
        - display_path_1: string (max 15 chars)
        - display_path_2: string (max 15 chars)
        - call_to_action: string
        - value_proposition: string
        - emotional_appeal: "urgency" | "curiosity" | "fear" | "greed" | "trust" | "convenience"
        - expected_ctr_estimate: float

        Vary the approach across variations:
        1. Benefit-focused
        2. Feature-focused
        3. Question/curiosity-driven
        4. Social proof / authority
        5. Urgency / scarcity

        Ensure all headlines include the primary keyword naturally."""

        response = await self.llm.ainvoke(prompt)
        return self._parse_ad_variations(response.content)

    @tool
    async def analyze_ad_performance(
        self,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS",
    ) -> dict:
        """Analyze ad-level performance metrics."""
        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.final_urls,
                ad_group_ad.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_per_conversion,
                metrics.conversions_per_interaction
            FROM ad_group_ad
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING {date_range}
            AND ad_group_ad.status = 'ENABLED'
            ORDER BY metrics.impressions DESC
        """

        data = await self._execute_query(query)
        return {
            "top_performers": self._identify_top_ads(data),
            "underperformers": self._identify_weak_ads(data),
            "ctr_benchmark": self._calculate_ctr_benchmark(data),
            "quality_score_analysis": self._analyze_quality_scores(data),
            "recommendations": self._generate_ad_recommendations(data),
        }

    @tool
    async def run_ab_test(
        self,
        campaign_id: str,
        ad_group_id: str,
        variations: list[dict],
        test_duration_days: int = 14,
    ) -> dict:
        """Set up an A/B test between ad variations."""
        # Create ad variations
        created_ads = []
        for i, variation in enumerate(variations):
            ad_result = await self._create_responsive_search_ad(
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                headlines=variation["headlines"],
                descriptions=variation["descriptions"],
                final_url=variation.get("final_url", ""),
            )
            created_ads.append({
                "variation_id": i,
                "ad_id": ad_result["ad_id"],
                "copy": variation,
            })

        # Set up experiment (Google Ads Experiments API)
        experiment = await self._create_experiment(
            campaign_id=campaign_id,
            ad_group_id=ad_group_id,
            test_ads=created_ads,
            duration_days=test_duration_days,
        )

        return {
            "experiment_id": experiment["id"],
            "status": "running",
            "variations": created_ads,
            "test_duration_days": test_duration_days,
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=test_duration_days)).isoformat(),
            "success_metrics": ["ctr", "conversion_rate", "cpa"],
            "minimum_sample_size": 1000,
        }

    @tool
    async def optimize_ad_copy(
        self,
        underperforming_ads: list[dict],
        top_performing_ads: list[dict],
        campaign_context: dict,
    ) -> list[dict]:
        """Generate optimized versions of underperforming ads."""
        prompt = f"""Optimize these underperforming ads:
        {underperforming_ads}

        Using these top-performing ads as reference for what works:
        {top_performing_ads}

        Campaign context: {campaign_context}

        For each underperforming ad, generate 2 improved versions.
        Explain what you changed and why.

        Focus on:
        - Better keyword placement in headlines
        - Stronger value propositions
        - More compelling CTAs
        - Improved message match with landing pages
        - Addressing potential ad fatigue

        Return the optimized ads with explanations for each change."""

        response = await self.llm.ainvoke(prompt)
        return self._parse_optimized_ads(response.content)

    @tool
    async def generate_responsive_search_ad(
        self,
        product_info: dict,
        keywords: list[str],
        landing_page_url: str,
        num_headlines: int = 15,
        num_descriptions: int = 4,
    ) -> dict:
        """Generate a complete responsive search ad."""
        prompt = f"""Create a responsive search ad with {num_headlines} headlines
        and {num_descriptions} descriptions.

        Product: {product_info}
        Target keywords: {keywords}
        Landing page: {landing_page_url}

        Requirements:
        - Headlines: max 30 characters each, include primary keywords
        - Descriptions: max 90 characters each, include CTA
        - At least 3 headlines with the primary keyword
        - At least 2 descriptions with a clear CTA
        - Use numbers and specifics where possible
        - Create variety: benefit, feature, question, urgency, social proof

        Return as JSON with 'headlines' and 'descriptions' arrays."""

        response = await self.llm.ainvoke(prompt)
        return self._parse_rsa_response(response.content)

    @tool
    async def analyze_ad_strength(
        self,
        ad_id: str,
        campaign_id: str,
    ) -> dict:
        """Analyze ad strength and provide improvement recommendations."""
        query = f"""
            SELECT
                ad_group_ad.ad_strength,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.responsive_search_ad.pinned_headlines,
                ad_group_ad.ad.responsive_search_ad.pinned_descriptions
            FROM ad_group_ad
            WHERE ad_group_ad.ad.id = {ad_id}
            AND campaign.id = {campaign_id}
        """

        data = await self._execute_query(query)
        return {
            "ad_strength": data.get("ad_strength", "UNKNOWN"),
            "headline_count": len(data.get("headlines", [])),
            "description_count": len(data.get("descriptions", [])),
            "pinned_fields": self._get_pinned_fields(data),
            "improvement_recommendations": self._generate_strength_recommendations(data),
        }
```

### 4.3 Ad Creation Service

```python
# services/ad_service.py
class AdService:
    """Service layer for ad operations via Google Ads API."""

    def __init__(self, customer_id: str):
        self.client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        self.customer_id = customer_id

    async def create_responsive_search_ad(
        self,
        campaign_id: str,
        ad_group_id: str,
        headlines: list[str],
        descriptions: list[str],
        final_url: str,
        pinned_headlines: dict[int, str] | None = None,
        pinned_descriptions: dict[int, str] | None = None,
    ) -> dict:
        """Create a responsive search ad with headlines and descriptions."""
        operation = self.client.get_type("AdGroupAdOperation")
        ad_group_ad = operation.create
        ad_group_ad.ad_group = f"customers/{self.customer_id}/adGroups/{ad_group_id}"
        ad_group_ad.status = self.client.enums.AdGroupAdStatus.PAUSED  # Start paused for review
        ad_group_ad.ad.final_urls.append(final_url)

        # Build responsive search ad
        rsa = ad_group_ad.ad.responsive_search_ad

        for headline in headlines:
            asset = self.client.get_type("AdTextAsset")
            asset.text = headline
            rsa.headlines.append(asset)

        for description in descriptions:
            asset = self.client.get_type("AdTextAsset")
            asset.text = description
            rsa.descriptions.append(description)

        # Pin headlines/descriptions to specific positions
        if pinned_headlines:
            for position, headline in pinned_headlines.items():
                rsa.pinned_headlines[position].text = headline

        if pinned_descriptions:
            for position, description in pinned_descriptions.items():
                rsa.pinned_descriptions[position].text = description

        response = self.client.get_service("AdGroupAdService").mutate_ad_group_ads(
            customer_id=self.customer_id,
            operations=[operation],
        )

        return {
            "ad_id": response.results[0].resource_name.split("/")[-1],
            "resource_name": response.results[0].resource_name,
            "status": "created_paused",
        }

    async def create_ad_experiment(
        self,
        campaign_id: str,
        experiment_name: str,
        variations: list[dict],
        split_percentage: int = 50,
    ) -> dict:
        """Create a Google Ads experiment for A/B testing."""
        # Create experiment
        experiment_service = self.client.get_service("ExperimentService")
        experiment = self.client.get_type("Experiment")

        experiment.name = experiment_name
        experiment.type_ = self.client.enums.ExperimentType.SEARCH_CUSTOM_EXPERIMENT
        experiment.status = self.client.enums.ExperimentStatus.SETUP
        experiment.start_date = datetime.now().strftime("%Y-%m-%d")
        experiment.end_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        experiment.split_percent = split_percentage

        operation = self.client.get_type("ExperimentOperation")
        operation.create.CopyFrom(experiment)

        response = experiment_service.mutate_experiments(
            customer_id=self.customer_id,
            operations=[operation],
        )

        return {
            "experiment_id": response.results[0].resource_name.split("/")[-1],
            "status": "setup",
        }
```

---

## 5. Landing Page Optimization Agent

### 5.1 Purpose

Analyzes landing page performance, identifies conversion barriers, and recommends optimizations. Integrates with heatmaps, session recordings, and A/B testing platforms.

### 5.2 Architecture

```python
# agents/landing_page.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

class LandingPageAgent(DeepAgent):
    """
    Specialized agent for landing page analysis and optimization.
    Focuses on conversion rate optimization (CRO) principles.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        super().__init__(
            name="landing_page",
            llm=self.llm,
            system_prompt=self._system_prompt(),
            tools=[
                self.analyze_landing_page_performance,
                self.identify_conversion_barriers,
                self.recommend_page_optimizations,
                self.analyze_page_speed,
                self.check_mobile_experience,
                self.generate_landing_page_variants,
            ],
        )

    def _system_prompt(self) -> str:
        return """You are the Landing Page Optimization Agent, an expert in
        conversion rate optimization (CRO) and user experience (UX) for PPC landing pages.

        Your responsibilities:
        1. Analyze landing page performance metrics (bounce rate, time on page, conversion rate)
        2. Identify conversion barriers and friction points
        3. Recommend specific, actionable optimizations
        4. Analyze page speed and Core Web Vitals
        5. Evaluate mobile experience quality
        6. Generate A/B test variants for landing pages

        CRO Framework:
        - Relevance: Does the page match the ad's promise? (message match)
        - Clarity: Is the value proposition immediately clear?
        - Friction: What's preventing conversion? (form length, trust signals, load time)
        - Motivation: Why should the visitor convert now?
        - Trust: Are there sufficient trust signals? (reviews, guarantees, security badges)

        Key metrics to analyze:
        - Landing page experience score (Google Ads)
        - Bounce rate (target: <40% for PPC)
        - Average session duration (target: >2 minutes)
        - Conversion rate (target: >2% for lead gen, >3% for e-commerce)
        - Page load time (target: <3 seconds)
        - Core Web Vitals: LCP <2.5s, FID <100ms, CLS <0.1

        Output: Prioritized list of recommendations with expected impact,
        implementation effort, and testing priority."""

    @tool
    async def analyze_landing_page_performance(
        self,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS",
    ) -> dict:
        """Analyze landing page performance from Google Ads data."""
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.landing_page_view.search_term_less_than_300,
                campaign.landing_page_view.search_term_300_to_700,
                campaign.landing_page_view.search_term_more_than_700,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.conversions_per_interaction,
                metrics.cost_per_conversion,
                metrics.ctr
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING {date_range}
        """

        data = await self._execute_query(query)

        # Also fetch landing page experience metrics
        lp_query = f"""
            SELECT
                landing_page_view.unexpanded_final_url,
                landing_page_view.landing_page_experience_score,
                metrics.average_page_views_per_session,
                metrics.average_time_on_site,
                metrics.bounce_rate
            FROM landing_page_view
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING {date_range}
        """

        lp_data = await self._execute_query(lp_query)

        return {
            "google_ads_metrics": data,
            "landing_page_metrics": lp_data,
            "health_score": self._calculate_lp_health_score(data, lp_data),
            "priority_issues": self._identify_priority_issues(data, lp_data),
        }

    @tool
    async def identify_conversion_barriers(
        self,
        landing_page_url: str,
        page_metrics: dict,
        form_data: dict | None = None,
    ) -> list[dict]:
        """Identify specific conversion barriers on the landing page."""
        prompt = f"""Analyze this landing page for conversion barriers:

        URL: {landing_page_url}
        Performance metrics: {page_metrics}
        Form configuration: {form_data}

        Identify the top 5 conversion barriers, ranked by impact.

        For each barrier, provide:
        - barrier_type: "message_mismatch" | "page_speed" | "form_friction" |
                       "trust_deficit" | "mobile_issues" | "clarity" | "motivation"
        - severity: "critical" | "high" | "medium" | "low"
        - description: what the issue is
        - evidence: data supporting this diagnosis
        - recommendation: specific fix
        - expected_impact: estimated conversion rate improvement
        - implementation_effort: "low" | "medium" | "high"

        Consider:
        - Does the H1 match the ad copy?
        - Is the CTA above the fold?
        - How many form fields are there?
        - Are there trust signals (reviews, guarantees)?
        - Does the page load quickly on mobile?
        - Is the value proposition clear within 5 seconds?"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_conversion_barriers(response.content)

    @tool
    async def recommend_page_optimizations(
        self,
        barriers: list[dict],
        page_type: str,
        industry: str,
    ) -> list[dict]:
        """Generate specific, actionable optimization recommendations."""
        prompt = f"""Based on these conversion barriers:
        {barriers}

        For a {page_type} landing page in the {industry} industry,
        generate specific, actionable optimization recommendations.

        For each recommendation, provide:
        - priority: 1 (highest) to 5 (lowest)
        - category: "content" | "design" | "technical" | "forms" | "trust" | "mobile"
        - title: short description
        - description: detailed explanation
        - implementation_steps: list of specific steps
        - expected_impact: estimated conversion rate improvement
        - effort_hours: estimated implementation time
        - ab_test_recommended: boolean
        - ab_test_hypothesis: string (if applicable)

        Focus on high-impact, low-effort optimizations first."""

        response = await self.llm.ainvoke(prompt)
        return self._parse_optimization_recommendations(response.content)

    @tool
    async def analyze_page_speed(
        self,
        landing_page_url: str,
    ) -> dict:
        """Analyze page speed and Core Web Vitals."""
        # Use PageSpeed Insights API or similar
        import aiohttp

        api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        params = {
            "url": landing_page_url,
            "strategy": "mobile",
            "key": self._pagespeed_api_key,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as resp:
                data = await resp.json()

        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        audits = lighthouse.get("audits", {})

        return {
            "performance_score": categories.get("performance", {}).get("score", 0) * 100,
            "core_web_vitals": {
                "LCP": audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
                "FID": audits.get("max-potential-fid", {}).get("displayValue", "N/A"),
                "CLS": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
                "FCP": audits.get("first-contentful-paint", {}).get("displayValue", "N/A"),
                "TTFB": audits.get("server-response-time", {}).get("displayValue", "N/A"),
            },
            "opportunities": [
                {
                    "title": audit.get("title"),
                    "description": audit.get("description"),
                    "savings": audit.get("details", {}).get("overallSavingsMs", 0),
                }
                for key, audit in audits.items()
                if audit.get("details", {}).get("overallSavingsMs", 0) > 0
            ],
            "diagnostics": [
                {
                    "title": audit.get("title"),
                    "description": audit.get("description"),
                }
                for key, audit in audits.items()
                if audit.get("score", 1) < 0.9 and not audit.get("details", {}).get("overallSavingsMs")
            ],
        }

    @tool
    async def check_mobile_experience(
        self,
        landing_page_url: str,
    ) -> dict:
        """Evaluate mobile experience quality."""
        prompt = f"""Evaluate the mobile experience of this landing page:
        {landing_page_url}

        Assess:
        1. Mobile responsiveness and layout
        2. Touch target sizes and spacing
        3. Readability (font sizes, contrast)
        4. Form usability on mobile
        5. Navigation and menu usability
        6. Page speed on mobile
        7. Pop-ups and interstitials (Google penalty risks)
        8. Above-the-fold content quality

        Provide a score (1-10) for each dimension and specific recommendations
        for improvement. Flag any issues that could trigger Google's
        mobile usability penalties."""

        response = await self.llm.ainvoke(prompt)
        return self._parse_mobile_analysis(response.content)

    @tool
    async def generate_landing_page_variants(
        self,
        current_page_analysis: dict,
        test_hypotheses: list[str],
    ) -> list[dict]:
        """Generate A/B test variant concepts for landing pages."""
        prompt = f"""Based on this landing page analysis:
        {current_page_analysis}

        Generate landing page A/B test variants for these hypotheses:
        {test_hypotheses}

        For each variant, provide:
        - variant_name: string
        - hypothesis: string
        - changes: list of specific changes from the control
        - elements_to_test: which page elements are being tested
        - expected_outcome: what improvement is expected
        - primary_metric: main success metric
        - secondary_metrics: list of secondary metrics
        - estimated_sample_size: visitors needed for significance
        - estimated_duration: days to reach significance

        Focus on testing one major element per variant (H1, CTA, form, layout)."""

        response = await self.llm.ainvoke(prompt)
        return self._parse_lp_variants(response.content)
```

---

## 6. Budget Allocation Agent

### 6.1 Purpose

Optimizes budget distribution across campaigns, ad groups, and time periods. Uses performance data, seasonality patterns, and marginal ROI analysis to maximize return on ad spend.

### 6.2 Architecture

```python
# agents/budget_allocation.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from datetime import datetime, timedelta

class BudgetAllocationAgent(DeepAgent):
    """
    Specialized agent for budget planning, allocation, and optimization.
    Distributes budget to maximize overall portfolio performance.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        super().__init__(
            name="budget_allocation",
            llm=self.llm,
            system_prompt=self._system_prompt(),
            tools=[
                self.analyze_budget_utilization,
                self.calculate_optimal_allocation,
                self.apply_budget_changes,
                self.analyze_seasonality,
                self.forecast_budget_needs,
                self.set_budget_schedule,
            ],
        )

    def _system_prompt(self) -> str:
        return """You are the Budget Allocation Agent, an expert in PPC budget
        management and portfolio optimization.

        Your responsibilities:
        1. Analyze current budget utilization across campaigns
        2. Calculate optimal budget allocation based on marginal ROI
        3. Apply budget changes with proper safeguards
        4. Analyze seasonality patterns for budget planning
        5. Forecast future budget needs based on growth trends
        6. Set dayparting and day-of-week budget schedules

        Budget allocation principles:
        - Allocate more budget to campaigns with lower marginal CPA
        - Maintain minimum budget for new campaigns to gather data
        - Consider budget pacing: avoid spending daily budget before 2 PM
        - Account for day-of-week performance variations
        - Reserve 10-15% of budget for testing new opportunities
        - Never reduce budget by more than 30% at once
        - Increase budget gradually (20% increments) for scaling

        Marginal analysis:
        - Calculate marginal CPA for each campaign
        - Shift budget from high-marginal-CPA to low-marginal-CPA campaigns
        - Consider diminishing returns as budget increases
        - Factor in conversion lag time for accurate attribution

        Safeguards:
        - Set maximum daily spend limits
        - Implement budget alerts at 80%, 90%, 100% utilization
        - Maintain emergency budget reserve
        - Log all budget changes with reasoning"""

    @tool
    async def analyze_budget_utilization(
        self,
        account_id: str,
        date_range: str = "LAST_30_DAYS",
    ) -> dict:
        """Analyze budget utilization across all campaigns."""
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.amount_micros,
                campaign.bidding_strategy_type,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion,
                metrics.conversions_per_interaction,
                metrics.search_budget_lost_impression_share,
                metrics.search_rank_lost_impression_share
            FROM campaign
            WHERE segments.date DURING {date_range}
            ORDER BY metrics.cost_micros DESC
        """

        data = await self._execute_query(query)

        total_budget = sum(c["amount_micros"] for c in data) / 1_000_000
        total_spend = sum(c["cost_micros"] for c in data) / 1_000_000

        return {
            "total_budget": total_budget,
            "total_spend": total_spend,
            "utilization_rate": total_spend / total_budget if total_budget > 0 else 0,
            "campaigns": [
                {
                    "campaign_id": c["campaign"]["id"],
                    "name": c["campaign"]["name"],
                    "daily_budget": c["campaign"]["amount_micros"] / 1_000_000,
                    "spend": c["metrics"]["cost_micros"] / 1_000_000,
                    "conversions": c["metrics"]["conversions"],
                    "cpa": c["metrics"]["cost_per_conversion"] / 1_000_000,
                    "roas": (
                        c["metrics"]["conversions_value"] / c["metrics"]["cost_micros"]
                        if c["metrics"]["cost_micros"] > 0
                        else 0
                    ),
                    "budget_lost_impression_share": c["metrics"].get(
                        "search_budget_lost_impression_share", 0
                    ),
                }
                for c in data
            ],
            "underutilized_campaigns": [
                c for c in data
                if c["metrics"].get("search_budget_lost_impression_share", 0) < 0.1
            ],
            "overutilized_campaigns": [
                c for c in data
                if c["metrics"].get("search_budget_lost_impression_share", 0) > 0.3
            ],
        }

    @tool
    async def calculate_optimal_allocation(
        self,
        campaigns: list[dict],
        total_budget: float,
        constraints: dict,
    ) -> list[dict]:
        """Calculate optimal budget allocation across campaigns."""
        prompt = f"""Calculate the optimal budget allocation for these campaigns:
        {campaigns}

        Total available budget: ${total_budget}/day

        Constraints:
        {constraints}

        For each campaign, calculate:
        - current_daily_budget
        - recommended_daily_budget
        - change_amount
        - change_percent
        - expected_conversions_change
        - expected_cost_change
        - expected_cpa_change
        - marginal_cpa
        - reasoning

        Methodology:
        1. Calculate marginal CPA for each campaign (cost of next conversion)
        2. Rank campaigns by marginal CPA (lowest = most efficient)
        3. Allocate budget to lowest marginal CPA campaigns first
        4. Respect minimum/maximum budget constraints
        5. Maintain 10-15% testing reserve
        6. Consider diminishing returns curve

        Also provide:
        - Portfolio-level expected outcomes
        - Risk assessment
        - Recommended monitoring checkpoints"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_allocation_recommendations(response.content)

    @tool
    async def apply_budget_changes(
        self,
        campaign_id: str,
        new_daily_budget: float,
        dry_run: bool = True,
    ) -> dict:
        """Apply budget changes to a campaign."""
        if dry_run:
            return {
                "status": "dry_run",
                "campaign_id": campaign_id,
                "new_daily_budget": new_daily_budget,
                "projected_monthly_spend": new_daily_budget * 30,
            }

        operation = self.client.get_type("CampaignOperation")
        campaign = operation.update
        campaign.resource_name = f"customers/{self.customer_id}/campaigns/{campaign_id}"
        campaign.amount_micros = int(new_daily_budget * 1_000_000)

        field_mask = self.client.get_type("FieldMask")
        field_mask.paths.append("amount_micros")
        operation.update_mask.CopyFrom(field_mask)

        response = self.client.get_service("CampaignService").mutate_campaigns(
            customer_id=self.customer_id,
            operations=[operation],
        )

        return {
            "status": "applied",
            "campaign_id": campaign_id,
            "new_daily_budget": new_daily_budget,
            "resource_name": response.results[0].resource_name,
        }

    @tool
    async def analyze_seasonality(
        self,
        campaign_id: str,
        historical_months: int = 12,
    ) -> dict:
        """Analyze seasonal patterns in campaign performance."""
        query = f"""
            SELECT
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING LAST_{historical_months}_MONTHS
            ORDER BY segments.date
        """

        data = await self._execute_query(query)

        # Group by month and day of week
        monthly_patterns = self._aggregate_monthly(data)
        dow_patterns = self._aggregate_day_of_week(data)

        return {
            "monthly_patterns": monthly_patterns,
            "day_of_week_patterns": dow_patterns,
            "peak_months": self._identify_peaks(monthly_patterns),
            "trough_months": self._identify_troughs(monthly_patterns),
            "seasonality_score": self._calculate_seasonality_score(monthly_patterns),
            "recommendations": self._generate_seasonality_recommendations(
                monthly_patterns, dow_patterns
            ),
        }

    @tool
    async def forecast_budget_needs(
        self,
        campaign_id: str,
        growth_target: float,
        forecast_periods: int = 3,
    ) -> dict:
        """Forecast future budget needs based on growth targets."""
        query = f"""
            SELECT
                segments.date,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING LAST_90_DAYS
            ORDER BY segments.date
        """

        data = await self._execute_query(query)

        prompt = f"""Based on this 90-day performance data:
        {data}

        Forecast budget needs for the next {forecast_periods} months
        with a growth target of {growth_target * 100}%.

        For each month, estimate:
        - projected_spend
        - projected_conversions
        - projected_cpa
        - projected_revenue
        - projected_roas
        - confidence_interval

        Consider:
        - Historical growth trends
        - Seasonality patterns
        - Diminishing returns as budget scales
        - Market competition changes
        - Conversion rate optimization potential"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_budget_forecast(response.content)

    @tool
    async def set_budget_schedule(
        self,
        campaign_id: str,
        schedule: dict,
    ) -> dict:
        """Set dayparting budget schedule (adjust bids by time)."""
        # Note: Google Ads doesn't support direct budget scheduling,
        # but we can use ad schedules with bid modifiers
        operations = []

        for day, hours in schedule.items():
            for hour, modifier in hours.items():
                operation = self.client.get_type("CampaignCriterionOperation")
                criterion = operation.create
                criterion.campaign = f"customers/{self.customer_id}/campaigns/{campaign_id}"
                criterion.day_of_week = self.client.enums.DayOfWeek[day.upper()]
                criterion.start_hour = hour
                criterion.end_hour = (hour + 1) % 24
                criterion.bid_modifier = modifier

                operations.append(operation)

        response = self.client.get_service("CampaignCriterionService").mutate_campaign_criteria(
            customer_id=self.customer_id,
            operations=operations,
        )

        return {
            "status": "applied",
            "campaign_id": campaign_id,
            "schedule": schedule,
            "modifiers_created": len(response.results),
        }
```

---

## 7. Performance Analytics Agent

### 7.1 Purpose

Monitors, analyzes, and reports on campaign performance. Provides actionable insights, anomaly detection, and automated alerting. Serves as the feedback loop for all other agents.

### 7.2 Architecture

```python
# agents/performance_analytics.py
from langchain_deepagents import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from datetime import datetime, timedelta
import statistics

class PerformanceAnalyticsAgent(DeepAgent):
    """
    Specialized agent for performance monitoring, analysis, and reporting.
    Provides the feedback loop for all other agents.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        super().__init__(
            name="performance_analytics",
            llm=self.llm,
            system_prompt=self._system_prompt(),
            tools=[
                self.generate_performance_report,
                self.detect_anomalies,
                self.calculate_attribution,
                self.benchmark_performance,
                self.forecast_performance,
                self.generate_insights,
            ],
        )

    def _system_prompt(self) -> str:
        return """You are the Performance Analytics Agent, an expert in PPC
        performance analysis, attribution, and reporting.

        Your responsibilities:
        1. Generate comprehensive performance reports
        2. Detect anomalies and performance regressions
        3. Calculate multi-touch attribution
        4. Benchmark performance against industry standards
        5. Forecast future performance trends
        6. Generate actionable insights from data

        Analysis framework:
        - Always compare against relevant baselines (previous period, targets, benchmarks)
        - Segment analysis by device, network, location, and time
        - Identify correlation vs. causation in performance changes
        - Consider external factors (seasonality, competition, market changes)
        - Provide context for every metric (not just "CTR is 2.5%" but "CTR is 2.5%,
          which is 15% above industry average but 5% below our target")

        Reporting standards:
        - Executive summary with key metrics and trends
        - Detailed breakdowns by campaign, ad group, keyword, and ad
        - Anomaly alerts with severity classification
        - Actionable recommendations with expected impact
        - Historical trend analysis

        Anomaly detection:
        - Use statistical methods (z-score, IQR) for anomaly detection
        - Set thresholds based on historical variance
        - Classify anomalies by severity: critical, warning, info
        - Provide root cause analysis for each anomaly"""

    @tool
    async def generate_performance_report(
        self,
        campaign_ids: list[str],
        date_range: str = "LAST_30_DAYS",
        report_type: str = "comprehensive",
    ) -> dict:
        """Generate a comprehensive performance report."""
        # Fetch all relevant data
        campaign_data = await self._fetch_campaign_data(campaign_ids, date_range)
        keyword_data = await self._fetch_keyword_data(campaign_ids, date_range)
        ad_data = await self._fetch_ad_data(campaign_ids, date_range)
        conversion_data = await self._fetch_conversion_data(campaign_ids, date_range)

        # Calculate period-over-period changes
        previous_period = self._get_previous_period(date_range)
        previous_data = await self._fetch_campaign_data(campaign_ids, previous_period)

        report = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "date_range": date_range,
                "campaigns_analyzed": len(campaign_ids),
                "report_type": report_type,
            },
            "executive_summary": self._generate_executive_summary(
                campaign_data, previous_data
            ),
            "key_metrics": {
                "total_spend": sum(c["cost"] for c in campaign_data),
                "total_conversions": sum(c["conversions"] for c in campaign_data),
                "total_revenue": sum(c["revenue"] for c in campaign_data),
                "overall_ctr": self._calculate_weighted_ctr(campaign_data),
                "overall_cpa": self._calculate_weighted_cpa(campaign_data),
                "overall_roas": self._calculate_weighted_roas(campaign_data),
            },
            "period_over_period": self._calculate_period_changes(
                campaign_data, previous_data
            ),
            "campaign_breakdown": [
                self._analyze_campaign_performance(c) for c in campaign_data
            ],
            "top_performers": self._identify_top_performers(keyword_data, ad_data),
            "underperformers": self._identify_underperformers(keyword_data, ad_data),
            "trend_analysis": self._analyze_trends(campaign_data),
            "recommendations": self._generate_recommendations(
                campaign_data, keyword_data, ad_data
            ),
        }

        return report

    @tool
    async def detect_anomalies(
        self,
        campaign_id: str,
        metrics: list[str],
        sensitivity: str = "medium",
    ) -> list[dict]:
        """Detect performance anomalies using statistical methods."""
        # Fetch daily metrics for the last 90 days
        query = f"""
            SELECT
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_per_conversion
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING LAST_90_DAYS
            ORDER BY segments.date
        """

        data = await self._execute_query(query)

        anomalies = []
        sensitivity_config = {
            "low": {"z_threshold": 3.0, "iqr_multiplier": 2.0},
            "medium": {"z_threshold": 2.5, "iqr_multiplier": 1.5},
            "high": {"z_threshold": 2.0, "iqr_multiplier": 1.0},
        }
        config = sensitivity_config[sensitivity]

        for metric in metrics:
            values = [row.get(metric, 0) for row in data]
            if len(values) < 7:
                continue

            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0

            for i, row in enumerate(data):
                value = row.get(metric, 0)
                z_score = (value - mean) / stdev if stdev > 0 else 0

                if abs(z_score) > config["z_threshold"]:
                    anomalies.append({
                        "date": row["date"],
                        "metric": metric,
                        "value": value,
                        "expected_range": {
                            "lower": mean - config["z_threshold"] * stdev,
                            "upper": mean + config["z_threshold"] * stdev,
                        },
                        "z_score": z_score,
                        "severity": self._classify_anomaly_severity(z_score),
                        "direction": "spike" if z_score > 0 else "drop",
                        "possible_causes": self._suggest_anomaly_causes(
                            metric, z_score, row
                        ),
                    })

        return sorted(anomalies, key=lambda x: abs(x["z_score"]), reverse=True)

    @tool
    async def calculate_attribution(
        self,
        campaign_id: str,
        attribution_model: str = "data_driven",
    ) -> dict:
        """Calculate multi-touch attribution for conversions."""
        query = f"""
            SELECT
                segments.date,
                campaign.id,
                campaign.name,
                metrics.conversions,
                metrics.conversions_value,
                metrics.interaction_types
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING LAST_30_DAYS
        """

        data = await self._execute_query(query)

        if attribution_model == "data_driven":
            return self._calculate_data_driven_attribution(data)
        elif attribution_model == "linear":
            return self._calculate_linear_attribution(data)
        elif attribution_model == "time_decay":
            return self._calculate_time_decay_attribution(data)
        elif attribution_model == "position_based":
            return self._calculate_position_based_attribution(data)
        else:
            return self._calculate_last_click_attribution(data)

    @tool
    async def benchmark_performance(
        self,
        campaign_id: str,
        industry: str,
    ) -> dict:
        """Benchmark campaign performance against industry standards."""
        query = f"""
            SELECT
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_per_conversion,
                metrics.conversions_per_interaction,
                metrics.search_impression_share
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING LAST_30_DAYS
        """

        data = await self._execute_query(query)

        # Industry benchmarks (simplified — would come from a database)
        benchmarks = {
            "ecommerce": {"ctr": 0.025, "cpa": 45.0, "roas": 4.0, "conversion_rate": 0.025},
            "lead_gen": {"ctr": 0.035, "cpa": 75.0, "roas": 3.0, "conversion_rate": 0.035},
            "saas": {"ctr": 0.020, "cpa": 120.0, "roas": 3.5, "conversion_rate": 0.020},
            "healthcare": {"ctr": 0.030, "cpa": 90.0, "roas": 3.0, "conversion_rate": 0.030},
            "education": {"ctr": 0.040, "cpa": 60.0, "roas": 2.5, "conversion_rate": 0.040},
        }

        industry_benchmarks = benchmarks.get(industry.lower(), benchmarks["lead_gen"])

        actual = {
            "ctr": data.get("ctr", 0),
            "cpa": data.get("cost_per_conversion", 0) / 1_000_000,
            "roas": (
                data.get("conversions_value", 0) / data.get("cost_micros", 1)
                if data.get("cost_micros", 0) > 0
                else 0
            ),
            "conversion_rate": data.get("conversions_per_interaction", 0),
        }

        return {
            "industry": industry,
            "actual_performance": actual,
            "industry_benchmarks": industry_benchmarks,
            "comparison": {
                metric: {
                    "actual": actual[metric],
                    "benchmark": industry_benchmarks[metric],
                    "difference_percent": (
                        (actual[metric] - industry_benchmarks[metric])
                        / industry_benchmarks[metric]
                        * 100
                    ),
                    "status": (
                        "above_average"
                        if actual[metric] > industry_benchmarks[metric] * 1.1
                        else "below_average"
                        if actual[metric] < industry_benchmarks[metric] * 0.9
                        else "average"
                    ),
                }
                for metric in actual
            },
            "overall_percentile": self._calculate_percentile(actual, industry_benchmarks),
        }

    @tool
    async def forecast_performance(
        self,
        campaign_id: str,
        forecast_days: int = 30,
    ) -> dict:
        """Forecast future performance using historical trends."""
        query = f"""
            SELECT
                segments.date,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.cost_per_conversion
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date DURING LAST_90_DAYS
            ORDER BY segments.date
        """

        data = await self._execute_query(query)

        prompt = f"""Based on this 90-day daily performance data:
        {data}

        Forecast the next {forecast_days} days of performance.

        For each day, estimate:
        - projected_impressions
        - projected_clicks
        - projected_cost
        - projected_conversions
        - projected_revenue
        - projected_cpa
        - projected_roas

        Also provide:
        - Confidence intervals (80% and 95%)
        - Trend direction (improving, stable, declining)
        - Key assumptions
        - Risk factors

        Use time series analysis considering:
        - Day-of-week patterns
        - Recent trend direction
        - Historical variance
        - Any visible seasonality"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_forecast(response.content)

    @tool
    async def generate_insights(
        self,
        campaign_id: str,
        date_range: str = "LAST_30_DAYS",
    ) -> list[dict]:
        """Generate actionable insights from campaign data."""
        # Fetch comprehensive data
        campaign_data = await self._fetch_campaign_data([campaign_id], date_range)
        keyword_data = await self._fetch_keyword_data([campaign_id], date_range)
        ad_data = await self._fetch_ad_data([campaign_id], date_range)
        search_terms = await self._fetch_search_terms([campaign_id], date_range)

        prompt = f"""Analyze this comprehensive campaign data and generate
        actionable insights:

        Campaign data: {campaign_data}
        Keyword data: {keyword_data}
        Ad data: {ad_data}
        Search terms: {search_terms}

        Generate 5-10 actionable insights, ranked by potential impact.

        For each insight, provide:
        - insight_type: "opportunity" | "risk" | "trend" | "anomaly" | "optimization"
        - priority: "critical" | "high" | "medium" | "low"
        - title: short description
        - description: detailed explanation
        - supporting_data: specific metrics that support this insight
        - recommended_action: what to do about it
        - expected_impact: estimated improvement
        - implementation_effort: "low" | "medium" | "high"
        - confidence: "high" | "medium" | "low"

        Focus on insights that are:
        1. Actionable (not just observations)
        2. Specific (not generic advice)
        3. Data-supported (not speculation)
        4. Impactful (not trivial optimizations)"""

        response = await self.llm.ainvoke(prompt)
        return self._parse_insights(response.content)
```

---

## 8. Code Examples and Snippets

### 8.1 Project Structure

```
ppc-management/
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── keyword_research.py
│   ├── bid_management.py
│   ├── ad_creative.py
│   ├── landing_page.py
│   ├── budget_allocation.py
│   └── performance_analytics.py
├── services/
│   ├── __init__.py
│   ├── google_ads_service.py
│   ├── keyword_service.py
│   ├── bid_service.py
│   ├── ad_service.py
│   └── analytics_service.py
├── models/
│   ├── __init__.py
│   ├── campaign_state.py
│   ├── keyword.py
│   ├── bid.py
│   └── report.py
├── tools/
│   ├── __init__.py
│   ├── google_ads_tools.py
│   ├── search_tools.py
│   └── analytics_tools.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── logging_config.py
├── tests/
│   ├── __init__.py
│   ├── test_agents/
│   │   ├── test_keyword_research.py
│   │   ├── test_bid_management.py
│   │   ├── test_ad_creative.py
│   │   ├── test_landing_page.py
│   │   ├── test_budget_allocation.py
│   │   └── test_performance_analytics.py
│   ├── test_services/
│   │   ├── test_google_ads_service.py
│   │   └── test_analytics_service.py
│   ├── fixtures/
│   │   ├── campaign_data.json
│   │   ├── keyword_data.json
│   │   └── ad_performance.json
│   └── conftest.py
├── api/
│   ├── __init__.py
│   ├── routes.py
│   └── webhooks.py
├── workers/
│   ├── __init__.py
│   ├── celery_app.py
│   └── tasks.py
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml
└── README.md
```

### 8.2 Configuration

```python
# config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.1

    # Google Ads
    GOOGLE_ADS_DEVELOPER_TOKEN: str
    GOOGLE_ADS_CLIENT_ID: str
    GOOGLE_ADS_CLIENT_SECRET: str
    GOOGLE_ADS_REFRESH_TOKEN: str
    GOOGLE_ADS_LOGIN_CUSTOMER_ID: str
    GOOGLE_ADS_CUSTOMER_ID: str

    # Database
    DATABASE_URL: str = "postgresql://localhost:5432/ppc_management"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Vector Store
    VECTOR_STORE_URL: str = "postgresql://localhost:5432/ppc_vectors"

    # LangSmith
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "ppc-management"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_SECRET_KEY: str = "change-me-in-production"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Monitoring
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 8.3 FastAPI Application Entry Point

```python
# api/main.py
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from agents.orchestrator import PPCOrchestrator
from models.campaign_state import CampaignState
from config.settings import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.orchestrator = PPCOrchestrator()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="PPC Management API",
    description="AI-Powered PPC Management System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/campaigns/{campaign_id}/optimize")
async def optimize_campaign(
    campaign_id: str,
    cycle_type: str = "daily",
    background_tasks: BackgroundTasks = None,
):
    """Trigger an optimization cycle for a campaign."""
    orchestrator = app.state.orchestrator
    result = await orchestrator.run_optimization_cycle(
        campaign_id=campaign_id,
        cycle_type=cycle_type,
    )
    return {"status": "completed", "result": result}

@app.get("/campaigns/{campaign_id}/report")
async def get_performance_report(
    campaign_id: str,
    date_range: str = "LAST_30_DAYS",
):
    """Get a performance report for a campaign."""
    analytics_agent = app.state.orchestrator.agent.sub_agents["performance_analytics"]
    report = await analytics_agent.generate_performance_report(
        campaign_ids=[campaign_id],
        date_range=date_range,
    )
    return report

@app.post("/campaigns/{campaign_id}/keywords/research")
async def research_keywords(
    campaign_id: str,
    seed_keywords: list[str],
    industry: str,
):
    """Run keyword research for a campaign."""
    keyword_agent = app.state.orchestrator.agent.sub_agents["keyword_research"]
    ideas = await keyword_agent.search_keyword_ideas(
        seed_keywords=seed_keywords,
        industry=industry,
    )
    return {"keywords": ideas}

@app.post("/campaigns/{campaign_id}/bids/optimize")
async def optimize_bids(
    campaign_id: str,
    target_cpa: float | None = None,
    target_roas: float | None = None,
):
    """Run bid optimization for a campaign."""
    bid_agent = app.state.orchestrator.agent.sub_agents["bid_management"]
    analysis = await bid_agent.analyze_bid_performance(campaign_id)
    recommendations = await bid_agent.calculate_optimal_bids(
        keywords=analysis["keywords"],
        target_cpa=target_cpa or 50.0,
        target_roas=target_roas or 3.0,
        constraints={"max_daily_budget": 500},
    )
    return {"analysis": analysis, "recommendations": recommendations}

@app.post("/campaigns/{campaign_id}/ads/generate")
async def generate_ads(
    campaign_id: str,
    product_info: dict,
    num_variations: int = 5,
):
    """Generate ad creative variations."""
    ad_agent = app.state.orchestrator.agent.sub_agents["ad_creative"]
    variations = await ad_agent.generate_ad_variations(
        product_info=product_info,
        target_audience=product_info.get("target_audience", ""),
        campaign_goal=product_info.get("campaign_goal", "conversions"),
        num_variations=num_variations,
    )
    return {"variations": variations}

@app.get("/campaigns/{campaign_id}/anomalies")
async def detect_anomalies(
    campaign_id: str,
    metrics: list[str] = None,
    sensitivity: str = "medium",
):
    """Detect performance anomalies."""
    if metrics is None:
        metrics = ["ctr", "cost_per_conversion", "conversions"]
    analytics_agent = app.state.orchestrator.agent.sub_agents["performance_analytics"]
    anomalies = await analytics_agent.detect_anomalies(
        campaign_id=campaign_id,
        metrics=metrics,
        sensitivity=sensitivity,
    )
    return {"anomalies": anomalies}

@app.post("/webhooks/google-ads")
async def google_ads_webhook(payload: dict):
    """Handle Google Ads webhook notifications."""
    # Process webhook notifications for campaign changes
    event_type = payload.get("event_type")
    campaign_id = payload.get("campaign_id")

    if event_type == "CAMPAIGN_STATUS_CHANGE":
        # Trigger re-optimization
        pass
    elif event_type == "BUDGET_EXHAUSTED":
        # Alert budget allocation agent
        pass

    return {"status": "processed"}
```

### 8.4 Celery Task Workers

```python
# workers/tasks.py
from celery import Celery
from celery.schedules import crontab
from config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "ppc_management",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "daily-optimization": {
            "task": "workers.tasks.daily_optimization_cycle",
            "schedule": crontab(hour=6, minute=0),  # 6 AM UTC
        },
        "weekly-keyword-research": {
            "task": "workers.tasks.weekly_keyword_research",
            "schedule": crontab(day_of_week=1, hour=8, minute=0),  # Monday 8 AM
        },
        "hourly-bid-check": {
            "task": "workers.tasks.hourly_bid_check",
            "schedule": crontab(minute=0),  # Every hour
        },
        "daily-performance-report": {
            "task": "workers.tasks.daily_performance_report",
            "schedule": crontab(hour=18, minute=0),  # 6 PM UTC
        },
    },
)

@celery_app.task(bind=True, max_retries=3)
def daily_optimization_cycle(self):
    """Run daily optimization for all active campaigns."""
    from agents.orchestrator import PPCOrchestrator

    orchestrator = PPCOrchestrator()
    active_campaigns = get_active_campaigns()

    results = []
    for campaign_id in active_campaigns:
        try:
            result = orchestrator.run_optimization_cycle(
                campaign_id=campaign_id,
                cycle_type="daily",
            )
            results.append({"campaign_id": campaign_id, "status": "success", "result": result})
        except Exception as exc:
            self.retry(exc=exc, countdown=60)

    return results

@celery_app.task(bind=True, max_retries=3)
def weekly_keyword_research(self):
    """Run weekly keyword research for all campaigns."""
    from agents.keyword_research import KeywordResearchAgent

    agent = KeywordResearchAgent()
    campaigns = get_active_campaigns()

    for campaign_id in campaigns:
        try:
            state = load_campaign_state(campaign_id)
            ideas = agent.search_keyword_ideas(
                seed_keywords=state.keywords[:5],
                industry=state.metadata.get("industry", "general"),
            )
            # Store ideas for review
            store_keyword_ideas(campaign_id, ideas)
        except Exception as exc:
            self.retry(exc=exc, countdown=120)

@celery_app.task(bind=True)
def hourly_bid_check(self):
    """Check and adjust bids every hour."""
    from agents.bid_management import BidManagementAgent

    agent = BidManagementAgent()
    campaigns = get_active_campaigns()

    for campaign_id in campaigns:
        try:
            analysis = agent.analyze_bid_performance(campaign_id)
            if analysis["health_score"] < 0.6:
                # Trigger bid optimization
                recommendations = agent.calculate_optimal_bids(
                    keywords=analysis["keywords"],
                    target_cpa=analysis["target_cpa"],
                    target_roas=analysis["target_roas"],
                    constraints=analysis["constraints"],
                )
                agent.apply_bid_adjustments(campaign_id, recommendations, dry_run=False)
        except Exception:
            continue

@celery_app.task(bind=True)
def daily_performance_report(self):
    """Generate and send daily performance reports."""
    from agents.performance_analytics import PerformanceAnalyticsAgent

    agent = PerformanceAnalyticsAgent()
    campaigns = get_active_campaigns()

    report = agent.generate_performance_report(
        campaign_ids=campaigns,
        date_range="YESTERDAY",
        report_type="summary",
    )

    # Send report via email/Slack
    send_report_notification(report)
    return report
```

### 8.5 Docker Compose

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/ppc_management
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/ppc_management
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: celery -A workers.tasks worker --loglevel=info --concurrency=4

  scheduler:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/ppc_management
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: celery -A workers.tasks beat --loglevel=info

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=ppc_management
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 8.6 Requirements

```txt
# requirements.txt
# Core
langchain>=0.3.0
langchain-deepagents>=0.1.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
langchain-core>=0.3.0

# LLM
openai>=1.0.0

# APIs
google-ads>=25.0.0
google-api-python-client>=2.0.0

# Web Framework
fastapi>=0.115.0
uvicorn[standard]>=0.30.0

# Database
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
pgvector>=0.3.0

# Cache & Queue
redis>=5.0.0
celery>=5.4.0

# Data & Analytics
pandas>=2.0.0
numpy>=1.26.0
scikit-learn>=1.5.0
scipy>=1.13.0

# Validation & Settings
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Observability
langsmith>=0.1.0
sentry-sdk>=1.40.0
structlog>=24.0.0

# HTTP
aiohttp>=3.9.0
httpx>=0.27.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
pytest-mock>=3.12.0
factory-boy>=3.3.0
faker>=25.0.0

# Development
black>=24.0.0
ruff>=0.5.0
mypy>=1.10.0
pre-commit>=3.7.0
```

---

## 9. Testing Strategy

### 9.1 Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5%)  — Full optimization cycles
                   ─┤  Tests  ├─
                  ┌─┴─────────┴─┐
                  │  Integration │  (15%) — Agent + Service + API
                 ─┤    Tests    ├─
                ┌─┴─────────────┴─┐
                │   Agent Unit     │  (30%) — Individual agent logic
               ─┤     Tests       ├─
              ┌─┴─────────────────┴─┐
              │   Service Unit       │  (50%) — API clients, data transform
             ─┤      Tests          ├─
            ┌─┴───────────────────────┴─┐
            │        Total: 100%         │
            └───────────────────────────┘
```

### 9.2 Test Configuration

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from faker import Faker

fake = Faker()

@pytest.fixture
def mock_google_ads_client():
    """Mock Google Ads API client."""
    client = MagicMock()
    client.get_service = MagicMock()
    client.get_type = MagicMock()
    client.enums = MagicMock()
    return client

@pytest.fixture
def mock_openai_llm():
    """Mock OpenAI LLM."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="[]"))
    return llm

@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing."""
    return {
        "campaign_id": "1234567890",
        "campaign_name": "Test Campaign",
        "status": "ACTIVE",
        "platform": "google_ads",
        "daily_budget": 100.0,
        "total_budget": 3000.0,
        "spent_to_date": 1500.0,
        "target_cpa": 50.0,
        "target_roas": 3.0,
        "keywords": ["ppc software", "advertising platform", "ad management"],
        "performance_metrics": {
            "impressions": 50000,
            "clicks": 1250,
            "cost": 1500.0,
            "conversions": 45,
            "ctr": 0.025,
            "average_cpc": 1.20,
            "cost_per_conversion": 33.33,
        },
    }

@pytest.fixture
def sample_keyword_data():
    """Sample keyword data for testing."""
    return [
        {
            "keyword": "ppc software",
            "match_type": "exact",
            "estimated_monthly_searches": 12000,
            "estimated_cpc": 3.50,
            "competition": "high",
            "relevance_score": 9,
            "intent": "transactional",
        },
        {
            "keyword": "best ppc management tool",
            "match_type": "phrase",
            "estimated_monthly_searches": 3200,
            "estimated_cpc": 4.20,
            "competition": "medium",
            "relevance_score": 8,
            "intent": "commercial",
        },
    ]

@pytest.fixture
def sample_ad_data():
    """Sample ad performance data for testing."""
    return [
        {
            "ad_id": "ad_001",
            "headlines": ["PPC Software", "Automate Your Ads", "Save 50% Time"],
            "descriptions": ["AI-powered PPC management", "Start your free trial"],
            "impressions": 10000,
            "clicks": 350,
            "cost": 420.0,
            "conversions": 15,
            "ctr": 0.035,
            "cost_per_conversion": 28.0,
        },
        {
            "ad_id": "ad_002",
            "headlines": ["Ad Management", "Grow Your ROI", "Try Free"],
            "descriptions": ["Manage all your ad campaigns", "14-day free trial"],
            "impressions": 8000,
            "clicks": 200,
            "cost": 320.0,
            "conversions": 8,
            "ctr": 0.025,
            "cost_per_conversion": 40.0,
        },
    ]

@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client for API testing."""
    from httpx import AsyncClient
    from api.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

### 9.3 Agent Unit Tests

```python
# tests/test_agents/test_keyword_research.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agents.keyword_research import KeywordResearchAgent

@pytest.fixture
def keyword_agent(mock_openai_llm):
    """Create a keyword research agent with mocked LLM."""
    with patch("agents.keyword_research.ChatOpenAI", return_value=mock_openai_llm):
        agent = KeywordResearchAgent()
    return agent

@pytest.mark.asyncio
async def test_search_keyword_ideas(keyword_agent, sample_keyword_data):
    """Test keyword idea generation."""
    # Arrange
    mock_response = MagicMock()
    mock_response.content = str(sample_keyword_data)
    keyword_agent.llm.ainvoke = AsyncMock(return_value=mock_response)

    # Act
    result = await keyword_agent.search_keyword_ideas(
        seed_keywords=["ppc software"],
        industry="marketing",
    )

    # Assert
    assert isinstance(result, list)
    assert len(result) > 0
    assert keyword_agent.llm.ainvoke.called

@pytest.mark.asyncio
async def test_cluster_keywords_semantically(keyword_agent):
    """Test semantic keyword clustering."""
    # Arrange
    keywords = [
        "ppc software", "ppc management", "ppc tools",
        "facebook ads", "facebook advertising", "facebook marketing",
        "google ads", "google advertising", "google marketing",
    ]

    # Act
    result = await keyword_agent.cluster_keywords_semantically(
        keywords=keywords,
        n_clusters=3,
    )

    # Assert
    assert isinstance(result, dict)
    assert len(result) == 3
    total_keywords = sum(len(v) for v in result.values())
    assert total_keywords == len(keywords)

@pytest.mark.asyncio
async def test_generate_negative_keywords(keyword_agent):
    """Test negative keyword generation."""
    # Arrange
    search_terms = [
        "free ppc software",
        "ppc jobs",
        "ppc tutorial",
        "best ppc software",
        "ppc certification",
    ]
    campaign_context = {
        "product": "premium PPC management software",
        "target": "enterprise marketers",
        "price": "$$$",
    }

    mock_response = MagicMock()
    mock_response.content = '[{"keyword": "free", "match_type": "phrase"}, {"keyword": "jobs", "match_type": "phrase"}]'
    keyword_agent.llm.ainvoke = AsyncMock(return_value=mock_response)

    # Act
    result = await keyword_agent.generate_negative_keywords(
        search_terms=search_terms,
        campaign_context=campaign_context,
    )

    # Assert
    assert isinstance(result, list)
    assert len(result) > 0
```

```python
# tests/test_agents/test_bid_management.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agents.bid_management import BidManagementAgent

@pytest.fixture
def bid_agent(mock_openai_llm):
    with patch("agents.bid_management.ChatOpenAI", return_value=mock_openai_llm):
        agent = BidManagementAgent()
    return agent

@pytest.mark.asyncio
async def test_analyze_bid_performance(bid_agent):
    """Test bid performance analysis."""
    # Arrange
    mock_data = {
        "campaign": {"id": "123", "name": "Test"},
        "metrics": {
            "impressions": 50000,
            "clicks": 1250,
            "cost_micros": 1500000000,
            "conversions": 45,
            "ctr": 0.025,
            "cost_per_conversion": 33333333,
        },
    }
    bid_agent._execute_query = AsyncMock(return_value=mock_data)

    # Act
    result = await bid_agent.analyze_bid_performance("123")

    # Assert
    assert isinstance(result, dict)
    assert "health_score" in result

@pytest.mark.asyncio
async def test_calculate_optimal_bids(bid_agent):
    """Test optimal bid calculation."""
    # Arrange
    keywords = [
        {"keyword": "ppc software", "current_cpc": 2.50, "conversion_rate": 0.03},
        {"keyword": "ad management", "current_cpc": 3.00, "conversion_rate": 0.02},
    ]
    mock_response = MagicMock()
    mock_response.content = '[{"keyword": "ppc software", "recommended_cpc": 2.75, "change_percent": 10}]'
    bid_agent.llm.ainvoke = AsyncMock(return_value=mock_response)

    # Act
    result = await bid_agent.calculate_optimal_bids(
        keywords=keywords,
        target_cpa=50.0,
        target_roas=3.0,
        constraints={"max_daily_budget": 500},
    )

    # Assert
    assert isinstance(result, list)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_apply_bid_adjustments_dry_run(bid_agent):
    """Test bid adjustment in dry run mode."""
    # Arrange
    bid_changes = [
        {"criterion_id": "abc", "recommended_cpc": 2.75, "level": "keyword"},
    ]

    # Act
    result = await bid_agent.apply_bid_adjustments(
        campaign_id="123",
        bid_changes=bid_changes,
        dry_run=True,
    )

    # Assert
    assert result["status"] == "dry_run"
    assert "changes" in result
```

```python
# tests/test_agents/test_ad_creative.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agents.ad_creative import AdCreativeAgent

@pytest.fixture
def ad_agent(mock_openai_llm):
    with patch("agents.ad_creative.ChatOpenAI", return_value=mock_openai_llm):
        agent = AdCreativeAgent()
    return agent

@pytest.mark.asyncio
async def test_generate_ad_variations(ad_agent):
    """Test ad variation generation."""
    # Arrange
    product_info = {
        "name": "PPC Pro",
        "description": "AI-powered PPC management platform",
        "features": ["automation", "AI optimization", "reporting"],
    }
    mock_response = MagicMock()
    mock_response.content = '[{"headlines": ["PPC Software", "Automate Ads"], "descriptions": ["AI-powered management"]}]'
    ad_agent.llm.ainvoke = AsyncMock(return_value=mock_response)

    # Act
    result = await ad_agent.generate_ad_variations(
        product_info=product_info,
        target_audience="marketing managers",
        campaign_goal="conversions",
        num_variations=3,
    )

    # Assert
    assert isinstance(result, list)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_analyze_ad_performance(ad_agent, sample_ad_data):
    """Test ad performance analysis."""
    # Arrange
    ad_agent._execute_query = AsyncMock(return_value=sample_ad_data)

    # Act
    result = await ad_agent.analyze_ad_performance("123")

    # Assert
    assert isinstance(result, dict)
    assert "top_performers" in result
    assert "underperformers" in result
```

### 9.4 Service Unit Tests

```python
# tests/test_services/test_google_ads_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.google_ads_service import GoogleAdsService

@pytest.fixture
def google_ads_service(mock_google_ads_client):
    with patch("services.google_ads_service.GoogleAdsClient") as mock_client:
        mock_client.load_from_storage.return_value = mock_google_ads_client
        service = GoogleAdsService(customer_id="1234567890")
    return service

@pytest.mark.asyncio
async def test_add_keywords(google_ads_service):
    """Test adding keywords to an ad group."""
    # Arrange
    keywords = [
        {"keyword": "ppc software", "match_type": "exact", "bid": 2.50},
        {"keyword": "ad management", "match_type": "phrase", "bid": 3.00},
    ]

    mock_response = MagicMock()
    mock_response.results = [MagicMock(resource_name="customers/123/adGroupCriteria/456~789")]
    google_ads_service.client.get_service.return_value.mutate_ad_group_criteria = AsyncMock(
        return_value=mock_response
    )

    # Act
    result = await google_ads_service.add_keywords(
        ad_group_id="456",
        keywords=keywords,
    )

    # Assert
    assert isinstance(result, list)
    assert len(result) == 1

@pytest.mark.asyncio
async def test_update_keyword_bid(google_ads_service):
    """Test updating a keyword bid."""
    # Arrange
    mock_response = MagicMock()
    mock_response.results = [MagicMock(resource_name="customers/123/adGroupCriteria/456~789")]
    google_ads_service.client.get_service.return_value.mutate_ad_group_criteria = AsyncMock(
        return_value=mock_response
    )

    # Act
    result = await google_ads_service.update_keyword_bid(
        campaign_id="123",
        criterion_id="789",
        new_bid=2.75,
    )

    # Assert
    assert "adGroupCriteria" in result
```

### 9.5 Integration Tests

```python
# tests/test_integration/test_optimization_cycle.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_full_optimization_cycle(async_client, sample_campaign_data):
    """Test a complete optimization cycle end-to-end."""
    # This test uses mocked external services but real agent logic
    with patch("agents.orchestrator.PPCOrchestrator._load_campaign_state") as mock_load:
        mock_load.return_value = MagicMock(**sample_campaign_data)

        response = await async_client.post(
            "/campaigns/1234567890/optimize",
            params={"cycle_type": "daily"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "result" in data

@pytest.mark.asyncio
async def test_keyword_research_integration(async_client):
    """Test keyword research endpoint."""
    response = await async_client.post(
        "/campaigns/1234567890/keywords/research",
        params={
            "seed_keywords": ["ppc software", "ad management"],
            "industry": "marketing",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "keywords" in data

@pytest.mark.asyncio
async def test_performance_report_integration(async_client):
    """Test performance report endpoint."""
    response = await async_client.get(
        "/campaigns/1234567890/report",
        params={"date_range": "LAST_30_DAYS"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
    assert "key_metrics" in data
```

### 9.6 E2E Tests

```python
# tests/test_e2e/test_full_workflow.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_complete_ppc_workflow():
    """
    End-to-end test: Keyword research → Ad creation → Bid optimization →
    Budget allocation → Performance analysis
    """
    # This test simulates a complete PPC management workflow
    # with all external APIs mocked

    # 1. Keyword Research
    with patch("agents.keyword_research.ChatOpenAI") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(
            return_value=MagicMock(content='[{"keyword": "ppc software", "match_type": "exact"}]')
        )
        from agents.keyword_research import KeywordResearchAgent
        keyword_agent = KeywordResearchAgent()

        keywords = await keyword_agent.search_keyword_ideas(
            seed_keywords=["ppc software"],
            industry="marketing",
        )
        assert len(keywords) > 0

    # 2. Ad Creative Generation
    with patch("agents.ad_creative.ChatOpenAI") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(
            return_value=MagicMock(content='[{"headlines": ["PPC Software"], "descriptions": ["Manage ads"]}]')
        )
        from agents.ad_creative import AdCreativeAgent
        ad_agent = AdCreativeAgent()

        ads = await ad_agent.generate_ad_variations(
            product_info={"name": "PPC Pro"},
            target_audience="marketers",
            campaign_goal="conversions",
        )
        assert len(ads) > 0

    # 3. Bid Optimization
    with patch("agents.bid_management.ChatOpenAI") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(
            return_value=MagicMock(content='[{"keyword": "ppc software", "recommended_cpc": 2.50}]')
        )
        from agents.bid_management import BidManagementAgent
        bid_agent = BidManagementAgent()

        bids = await bid_agent.calculate_optimal_bids(
            keywords=keywords,
            target_cpa=50.0,
            target_roas=3.0,
            constraints={"max_daily_budget": 500},
        )
        assert len(bids) > 0

    # 4. Performance Analysis
    with patch("agents.performance_analytics.ChatOpenAI") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(
            return_value=MagicMock(content='[{"insight_type": "opportunity", "priority": "high"}]')
        )
        from agents.performance_analytics import PerformanceAnalyticsAgent
        analytics_agent = PerformanceAnalyticsAgent()

        insights = await analytics_agent.generate_insights("123")
        assert len(insights) > 0
```

### 9.7 Test Execution

```bash
# Run all tests
pytest tests/ -v --cov=agents --cov=services --cov-report=html

# Run only unit tests
pytest tests/test_agents/ tests/test_services/ -v

# Run integration tests
pytest tests/test_integration/ -v

# Run E2E tests
pytest tests/test_e2e/ -v

# Run with specific marker
pytest -m "not slow" -v

# Run with coverage threshold
pytest --cov=agents --cov-fail-under=80
```

### 9.8 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Lint
        run: |
          ruff check .
          black --check .
          mypy agents/ services/

      - name: Run unit tests
        run: |
          pytest tests/test_agents/ tests/test_services/ -v --cov=agents --cov=services

      - name: Run integration tests
        run: |
          pytest tests/test_integration/ -v

      - name: Run E2E tests
        run: |
          pytest tests/test_e2e/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

---

## Appendix A: Environment Variables

```bash
# .env.example
# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.1

# Google Ads
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_LOGIN_CUSTOMER_ID=...
GOOGLE_ADS_CUSTOMER_ID=...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ppc_management
REDIS_URL=redis://localhost:6379/0

# LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=ppc-management

# API
API_SECRET_KEY=change-me-in-production

# Monitoring
SENTRY_DSN=...
LOG_LEVEL=INFO
```

## Appendix B: Monitoring and Alerting

```python
# config/alerting.py
from dataclasses import dataclass
from typing import Callable
from enum import Enum

class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class AlertRule:
    name: str
    condition: Callable
    severity: AlertSeverity
    message_template: str
    cooldown_minutes: int = 60

ALERT_RULES = [
    AlertRule(
        name="high_cpa",
        condition=lambda m: m["cost_per_conversion"] > m["target_cpa"] * 1.5,
        severity=AlertSeverity.CRITICAL,
        message_template="CPA is {cpa}, 50% above target of {target_cpa}",
    ),
    AlertRule(
        name="low_budget_utilization",
        condition=lambda m: m["utilization_rate"] < 0.5,
        severity=AlertSeverity.WARNING,
        message_template="Budget utilization is only {utilization_rate:.0%}",
    ),
    AlertRule(
        name="high_bounce_rate",
        condition=lambda m: m["bounce_rate"] > 0.6,
        severity=AlertSeverity.WARNING,
        message_template="Bounce rate is {bounce_rate:.0%}",
    ),
    AlertRule(
        name="low_ctr",
        condition=lambda m: m["ctr"] < 0.01,
        severity=AlertSeverity.WARNING,
        message_template="CTR is {ctr:.2%}, below 1% threshold",
    ),
    AlertRule(
        name="budget_exhausted_early",
        condition=lambda m: m["utilization_rate"] > 0.9 and m["hour_of_day"] < 14,
        severity=AlertSeverity.CRITICAL,
        message_template="Budget {utilization_rate:.0%} spent by {hour_of_day}:00",
    ),
]
```

---

*Document Version: 1.0 | Last Updated: 2026-10-01*
