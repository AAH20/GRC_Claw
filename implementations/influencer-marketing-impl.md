# AI-Powered Influencer Marketing Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Stack:** LangChain + DeepAgents + Python 3.11+

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Discovery Agent](#2-discovery-agent)
3. [Vetting Agent](#3-vetting-agent)
4. [Outreach Agent](#4-outreach-agent)
5. [Negotiation Agent](#5-negotiation-agent)
6. [Content Agent](#6-content-agent)
7. [Performance Agent](#7-performance-agent)
8. [Optimization Agent](#8-optimization-agent)
9. [Relationship Management Agent](#9-relationship-management-agent)
10. [Code Examples & Snippets](#10-code-examples--snippets)
11. [Testing Strategy](#11-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The AI-powered influencer marketing system uses LangChain DeepAgents to orchestrate a multi-agent pipeline that automates the entire influencer marketing lifecycle — from discovery to relationship management.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT (DeepAgents)                   │
│         Coordinates workflow, manages state, routes tasks            │
└──────────────┬──────────────────────────────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┬──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Discov- │ │Vetting │ │Outreach│ │Negotia-│ │Content │ │Perform-│ │Optimiz-│
│ery     │ │Agent   │ │Agent   │ │tion    │ │Agent   │ │ance    │ │ation   │
│Agent   │ │        │ │        │ │Agent   │ │        │ │Agent   │ │Agent   │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
    │          │          │          │          │          │          │
    └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
                                    │
                         ┌──────────┴──────────┐
                         │  Relationship Mgmt  │
                         │      Agent          │
                         └─────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents | Multi-agent orchestration |
| LLM | GPT-4o / Claude 3.5 Sonnet | Reasoning & generation |
| Vector Store | Pinecone / ChromaDB | Influencer profile embeddings |
| Graph DB | Neo4j | Relationship mapping |
| Task Queue | Celery + Redis | Async task execution |
| Workflow | LangGraph | Stateful agent workflows |
| Monitoring | LangSmith | Tracing & observability |
| Storage | PostgreSQL + S3 | Structured data & media |
| API | FastAPI | REST endpoints |
| Scheduling | APScheduler | Cron-based triggers |

### 1.3 Agent Communication Protocol

```python
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
import operator

class AgentState(TypedDict):
    """Shared state across all agents in the pipeline."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    influencer_id: str | None
    campaign_id: str | None
    current_agent: str
    task_context: dict
    results: dict
    errors: list[str]
    metadata: dict
```

### 1.4 Orchestrator Design

```python
from langgraph.graph import StateGraph, END
from langchain_deepagents import DeepAgent

class InfluencerMarketingOrchestrator:
    """
    Top-level orchestrator that routes tasks to specialized agents
    and manages the overall campaign lifecycle.
    """
    
    def __init__(self, llm, tools, vector_store, graph_db):
        self.llm = llm
        self.tools = tools
        self.vector_store = vector_store
        self.graph_db = graph_db
        self.agents = self._initialize_agents()
        self.workflow = self._build_workflow()
    
    def _initialize_agents(self) -> dict:
        return {
            "discovery": DiscoveryAgent(self.llm, self.tools, self.vector_store),
            "vetting": VettingAgent(self.llm, self.tools, self.vector_store),
            "outreach": OutreachAgent(self.llm, self.tools),
            "negotiation": NegotiationAgent(self.llm, self.tools),
            "content": ContentAgent(self.llm, self.tools),
            "performance": PerformanceAgent(self.llm, self.tools),
            "optimization": OptimizationAgent(self.llm, self.tools),
            "relationship": RelationshipAgent(self.llm, self.tools, self.graph_db),
        }
    
    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        # Add nodes
        for name, agent in self.agents.items():
            workflow.add_node(name, agent.run)
        
        # Define edges
        workflow.add_edge("discovery", "vetting")
        workflow.add_edge("vetting", "outreach")
        workflow.add_edge("outreach", "negotiation")
        workflow.add_edge("negotiation", "content")
        workflow.add_edge("content", "performance")
        workflow.add_edge("performance", "optimization")
        workflow.add_edge("optimization", "relationship")
        workflow.add_edge("relationship", END)
        
        # Conditional routing for re-vetting or re-negotiation
        workflow.add_conditional_edges(
            "vetting",
            self._should_proceed,
            {"proceed": "outreach", "reject": END, "re-vet": "vetting"}
        )
        
        workflow.add_conditional_edges(
            "negotiation",
            self._negotiation_result,
            {"accepted": "content", "counter": "negotiation", "rejected": "relationship"}
        )
        
        workflow.set_entry_point("discovery")
        return workflow.compile()
    
    def _should_proceed(self, state: AgentState) -> str:
        vetting_result = state["results"].get("vetting", {})
        if vetting_result.get("score", 0) >= 0.7:
            return "proceed"
        elif vetting_result.get("score", 0) >= 0.4:
            return "re-vet"
        return "reject"
    
    def _negotiation_result(self, state: AgentState) -> str:
        negotiation = state["results"].get("negotiation", {})
        status = negotiation.get("status", "")
        if status == "accepted":
            return "accepted"
        elif status == "counter_offer":
            return "counter"
        return "rejected"
```

---

## 2. Discovery Agent

### 2.1 Purpose

The Discovery Agent identifies potential influencers across social platforms that match campaign criteria including niche, audience demographics, engagement patterns, and brand alignment.

### 2.2 Implementation

```python
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepagents import DeepAgent
from pydantic import BaseModel, Field
from typing import Optional
import httpx
import asyncio

class InfluencerProfile(BaseModel):
    """Structured influencer profile extracted from discovery."""
    platform: str = Field(description="Social media platform (instagram, tiktok, youtube)")
    handle: str = Field(description="Influencer handle/username")
    display_name: str = Field(description="Display name")
    bio: str = Field(description="Profile bio/description")
    follower_count: int = Field(description="Number of followers")
    following_count: int = Field(description="Number of accounts following")
    post_count: int = Field(description="Total posts")
    engagement_rate: float = Field(description="Average engagement rate (0-1)")
    avg_likes: int = Field(description="Average likes per post")
    avg_comments: int = Field(description="Average comments per post")
    niche_tags: list[str] = Field(description="Content niche categories")
    audience_demographics: dict = Field(description="Audience age/gender/location breakdown")
    recent_posts: list[dict] = Field(description="Recent post metadata")
    contact_info: Optional[dict] = Field(description="Public contact information")
    brand_mentions: list[str] = Field(description="Recent brand collaborations")
    profile_url: str = Field(description="Direct profile URL")

class DiscoveryAgent(DeepAgent):
    """
    Discovers influencers across platforms using search APIs,
    hashtag analysis, and graph-based expansion.
    """
    
    SYSTEM_PROMPT = """You are an expert influencer discovery specialist.
    
    Your task is to find influencers who are strong candidates for brand partnerships.
    You have access to platform APIs, hashtag search, and audience analysis tools.
    
    Discovery criteria:
    - Match campaign niche and target demographics
    - Minimum engagement rate thresholds
    - Audience authenticity indicators
    - Content quality and brand safety
    - Geographic relevance
    
    Always verify data from multiple sources before including an influencer.
    """
    
    def __init__(self, llm, tools, vector_store):
        super().__init__(
            llm=llm,
            tools=tools,
            system_prompt=self.SYSTEM_PROMPT,
        )
        self.vector_store = vector_store
    
    @tool
    async def search_instagram_hashtags(
        self, 
        hashtag: str, 
        min_followers: int = 10000,
        max_followers: int = 500000,
        limit: int = 50
    ) -> list[InfluencerProfile]:
        """Search Instagram for influencers by hashtag with follower filters."""
        # Implementation using Instagram Graph API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.instagram.com/v18.0/ig_hashtag_search",
                params={
                    "q": hashtag,
                    "fields": "id,name",
                    "access_token": self._get_platform_token("instagram")
                }
            )
            hashtag_data = response.json()
            
            profiles = []
            for tag in hashtag_data.get("data", [])[:limit]:
                # Fetch top media for each hashtag
                media = await self._fetch_hashtag_media(tag["id"])
                for post in media:
                    profile = await self._extract_profile_from_post(post)
                    if profile and min_followers <= profile.follower_count <= max_followers:
                        profiles.append(profile)
            
            return profiles
    
    @tool
    async def search_tiktok_creators(
        self,
        keywords: list[str],
        min_followers: int = 10000,
        max_followers: int = 1000000,
        categories: list[str] = None
    ) -> list[InfluencerProfile]:
        """Search TikTok Creator Marketplace for matching creators."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://open-api.tiktok.com/creator_marketplace/search/",
                json={
                    "keywords": keywords,
                    "filters": {
                        "follower_count_min": min_followers,
                        "follower_count_max": max_followers,
                        "categories": categories or [],
                    }
                },
                headers={"Authorization": f"Bearer {self._get_platform_token('tiktok')}"}
            )
            return [InfluencerProfile(**item) for item in response.json().get("creators", [])]
    
    @tool
    async def search_youtube_channels(
        self,
        query: str,
        min_subscribers: int = 5000,
        max_subscribers: int = 500000,
        category: str = None
    ) -> list[InfluencerProfile]:
        """Search YouTube for channels matching criteria."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "q": query,
                    "type": "channel",
                    "part": "snippet",
                    "maxResults": 50,
                    "key": self._get_platform_token("youtube")
                }
            )
            channels = response.json().get("items", [])
            
            profiles = []
            for channel in channels:
                channel_id = channel["id"]["channelId"]
                stats = await self._fetch_youtube_stats(channel_id)
                if min_subscribers <= stats["subscriberCount"] <= max_subscribers:
                    profiles.append(InfluencerProfile(
                        platform="youtube",
                        handle=channel["snippet"]["title"],
                        display_name=channel["snippet"]["title"],
                        bio=channel["snippet"]["description"],
                        follower_count=stats["subscriberCount"],
                        # ... additional fields
                    ))
            return profiles
    
    @tool
    async def expand_network(
        self,
        seed_influencer: str,
        platform: str,
        depth: int = 2,
        expansion_strategy: str = "collaborators"
    ) -> list[InfluencerProfile]:
        """
        Expand discovery through network analysis.
        Strategies: collaborators, similar_accounts, audience_overlap
        """
        if expansion_strategy == "collaborators":
            return await self._find_collaborators(seed_influencer, platform, depth)
        elif expansion_strategy == "similar_accounts":
            return await self._find_similar_accounts(seed_influencer, platform)
        elif expansion_strategy == "audience_overlap":
            return await self._find_audience_overlap(seed_influencer, platform)
        return []
    
    @tool
    async def analyze_engagement_authenticity(
        self,
        profile: InfluencerProfile
    ) -> dict:
        """
        Analyze engagement patterns for authenticity.
        Detects fake followers, engagement pods, and bot activity.
        """
        analysis = {
            "authenticity_score": 0.0,
            "follower_quality": "unknown",
            "engagement_consistency": 0.0,
            "red_flags": [],
            "green_flags": [],
        }
        
        # Follower-to-engagement ratio analysis
        expected_engagement = profile.follower_count * 0.03  # 3% baseline
        actual_engagement = profile.avg_likes + profile.avg_comments
        ratio = actual_engagement / expected_engagement if expected_engagement > 0 else 0
        
        if ratio < 0.1:
            analysis["red_flags"].append("Very low engagement ratio - possible fake followers")
        elif ratio > 2.0:
            analysis["red_flags"].append("Unusually high engagement - possible engagement pods")
        else:
            analysis["green_flags"].append("Engagement ratio within normal range")
        
        # Follower growth pattern analysis
        growth_data = await self._fetch_growth_history(profile)
        if self._detect_spike_pattern(growth_data):
            analysis["red_flags"].append("Suspicious follower growth spikes detected")
        
        # Comment quality analysis
        comment_analysis = await self._analyze_comment_quality(profile)
        if comment_analysis["generic_comment_ratio"] > 0.7:
            analysis["red_flags"].append("High ratio of generic/spam comments")
        
        # Calculate overall authenticity score
        analysis["authenticity_score"] = self._calculate_authenticity_score(analysis)
        return analysis
    
    async def run(self, state: AgentState) -> AgentState:
        """Execute discovery based on campaign requirements."""
        campaign = state["task_context"]["campaign"]
        
        # Parallel discovery across platforms
        discovery_tasks = []
        for platform in campaign["target_platforms"]:
            if platform == "instagram":
                discovery_tasks.append(
                    self.search_instagram_hashtags(
                        hashtag=campaign["primary_hashtag"],
                        min_followers=campaign["min_followers"],
                        max_followers=campaign["max_followers"]
                    )
                )
            elif platform == "tiktok":
                discovery_tasks.append(
                    self.search_tiktok_creators(
                        keywords=campaign["keywords"],
                        min_followers=campaign["min_followers"],
                        max_followers=campaign["max_followers"]
                    )
                )
            elif platform == "youtube":
                discovery_tasks.append(
                    self.search_youtube_channels(
                        query=campaign["search_query"],
                        min_subscribers=campaign["min_followers"],
                        max_subscribers=campaign["max_followers"]
                    )
                )
        
        results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        # Deduplicate and rank
        all_profiles = []
        for result in results:
            if isinstance(result, list):
                all_profiles.extend(result)
        
        # Rank by relevance score
        ranked = self._rank_by_relevance(all_profiles, campaign)
        
        # Store in vector store for similarity search
        await self._index_profiles(ranked[:100])  # Top 100 candidates
        
        state["results"]["discovery"] = {
            "candidates": ranked[:50],
            "total_found": len(all_profiles),
            "platforms_searched": campaign["target_platforms"],
        }
        return state
```

### 2.3 Discovery Tools

| Tool | Platform | Purpose |
|------|----------|---------|
| `search_instagram_hashtags` | Instagram | Hashtag-based discovery |
| `search_tiktok_creators` | TikTok | Creator Marketplace search |
| `search_youtube_channels` | YouTube | Channel search via Data API |
| `expand_network` | All | Graph-based expansion |
| `analyze_engagement_authenticity` | All | Fake follower detection |
| `fetch_growth_history` | All | Growth pattern analysis |
| `analyze_comment_quality` | All | Comment authenticity |

---

## 3. Vetting Agent

### 3.1 Purpose

The Vetting Agent performs deep due diligence on discovered influencers, evaluating brand safety, audience quality, content alignment, and partnership history.

### 3.2 Implementation

```python
class VettingAgent(DeepAgent):
    """
    Evaluates influencer candidates across multiple dimensions:
    - Brand safety and content audit
    - Audience quality and demographics match
    - Content alignment with brand values
    - Partnership history and professionalism
    - Legal/compliance check
    """
    
    SYSTEM_PROMPT = """You are a thorough influencer vetting specialist.
    
    You evaluate influencer candidates for brand partnerships. Your analysis
    must be comprehensive, data-driven, and flag any potential risks.
    
    Evaluation dimensions:
    1. Brand Safety: Content audit for controversial topics, competitor mentions
    2. Audience Quality: Demographic match, authenticity, engagement depth
    3. Content Alignment: Values alignment, aesthetic fit, messaging compatibility
    4. Professionalism: Past brand deal behavior, communication quality
    5. Compliance: FTC disclosure adherence, platform policy compliance
    
    Score each dimension 0-1 and provide detailed reasoning.
    """
    
    def __init__(self, llm, tools, vector_store):
        super().__init__(llm=llm, tools=tools, system_prompt=self.SYSTEM_PROMPT)
        self.vector_store = vector_store
    
    @tool
    async def audit_content_safety(
        self,
        profile: InfluencerProfile,
        brand_guidelines: dict
    ) -> dict:
        """
        Comprehensive content safety audit using LLM analysis
        of recent posts, captions, and comments.
        """
        # Fetch recent content
        recent_content = await self._fetch_recent_content(profile, days=90)
        
        audit_prompt = f"""
        Analyze the following influencer content for brand safety.
        
        Brand Guidelines:
        - Prohibited topics: {brand_guidelines.get('prohibited_topics', [])}
        - Competitor brands to avoid: {brand_guidelines.get('competitors', [])}
        - Required values: {brand_guidelines.get('brand_values', [])}
        - Tone guidelines: {brand_guidelines.get('tone', 'professional')}
        
        Content to analyze:
        {self._format_content_for_analysis(recent_content)}
        
        Provide:
        1. Safety score (0-1)
        2. List of any concerning content
        3. Competitor mentions found
        4. Values alignment assessment
        5. Risk level (low/medium/high)
        """
        
        audit_result = await self.llm.ainvoke(audit_prompt)
        return self._parse_audit_result(audit_result)
    
    @tool
    async def analyze_audience_quality(
        self,
        profile: InfluencerProfile,
        target_demographics: dict
    ) -> dict:
        """
        Deep analysis of audience quality including:
        - Demographic match with target audience
        - Follower authenticity
        - Engagement quality and depth
        - Audience interests and affinities
        """
        # Fetch audience insights
        audience_data = await self._fetch_audience_insights(profile)
        
        # Demographic match score
        demo_match = self._calculate_demographic_match(
            audience_data["demographics"],
            target_demographics
        )
        
        # Follower authenticity (using third-party data if available)
        authenticity = await self._check_follower_authenticity(profile)
        
        # Engagement depth analysis
        engagement_quality = await self._analyze_engagement_depth(profile)
        
        # Audience interests alignment
        interest_alignment = self._calculate_interest_alignment(
            audience_data["interests"],
            target_demographics.get("interests", [])
        )
        
        return {
            "overall_score": (
                demo_match * 0.3 +
                authenticity["score"] * 0.3 +
                engagement_quality["score"] * 0.2 +
                interest_alignment * 0.2
            ),
            "demographic_match": demo_match,
            "authenticity": authenticity,
            "engagement_quality": engagement_quality,
            "interest_alignment": interest_alignment,
            "audience_size_estimate": audience_data["estimated_reach"],
        }
    
    @tool
    async def check_partnership_history(
        self,
        profile: InfluencerProfile
    ) -> dict:
        """
        Analyze past brand partnerships for:
        - Frequency and recency of sponsored content
        - Types of brands worked with
        - Disclosure compliance (FTC, platform policies)
        - Reported partnership quality
        """
        # Extract sponsored posts
        sponsored_posts = await self._identify_sponsored_content(profile)
        
        # Analyze disclosure compliance
        disclosure_score = self._check_ftc_compliance(sponsored_posts)
        
        # Categorize past partners
        partner_categories = self._categorize_partners(sponsored_posts)
        
        # Check for competitor partnerships
        competitor_conflicts = self._find_competitor_conflicts(
            sponsored_posts, 
            profile.brand_mentions
        )
        
        # Partnership frequency analysis
        frequency = len(sponsored_posts) / max(len(profile.recent_posts), 1)
        
        return {
            "total_partnerships": len(sponsored_posts),
            "disclosure_compliance_score": disclosure_score,
            "partner_categories": partner_categories,
            "competitor_conflicts": competitor_conflicts,
            "partnership_frequency": frequency,
            "avg_partnership_engagement": self._avg_partnership_engagement(sponsored_posts),
            "risk_flags": self._identify_partnership_risks(sponsored_posts),
        }
    
    @tool
    async def check_legal_compliance(
        self,
        profile: InfluencerProfile,
        campaign_requirements: dict
    ) -> dict:
        """
        Verify legal and compliance requirements:
        - FTC disclosure history
        - Platform policy violations
        - Copyright/trademark issues
        - Exclusivity conflicts
        - Age/identity verification
        """
        compliance = {
            "ftc_compliant": True,
            "platform_violations": [],
            "exclusivity_conflicts": [],
            "identity_verified": False,
            "age_verified": False,
            "overall_compliant": True,
        }
        
        # Check platform violation history
        violations = await self._fetch_platform_violations(profile)
        compliance["platform_violations"] = violations
        
        # Check for exclusivity agreements
        exclusivity = await self._check_exclusivity_agreements(profile)
        compliance["exclusivity_conflicts"] = exclusivity
        
        # Identity verification
        compliance["identity_verified"] = await self._verify_identity(profile)
        
        # Age verification (must be 18+ for most partnerships)
        compliance["age_verified"] = profile.follower_count > 0  # Proxy check
        
        compliance["overall_compliant"] = (
            compliance["ftc_compliant"] and
            len(compliance["platform_violations"]) == 0 and
            len(compliance["exclusivity_conflicts"]) == 0 and
            compliance["identity_verified"]
        )
        
        return compliance
    
    async def run(self, state: AgentState) -> AgentState:
        """Execute vetting pipeline for discovered candidates."""
        candidates = state["results"]["discovery"]["candidates"]
        campaign = state["task_context"]["campaign"]
        
        vetted_candidates = []
        for candidate in candidates[:20]:  # Vet top 20
            # Parallel vetting tasks
            safety, audience, history, compliance = await asyncio.gather(
                self.audit_content_safety(candidate, campaign["brand_guidelines"]),
                self.analyze_audience_quality(candidate, campaign["target_demographics"]),
                self.check_partnership_history(candidate),
                self.check_legal_compliance(candidate, campaign["requirements"]),
            )
            
            # Calculate composite vetting score
            composite_score = self._calculate_vetting_score(
                safety, audience, history, compliance
            )
            
            vetted_candidates.append({
                "profile": candidate,
                "scores": {
                    "brand_safety": safety["safety_score"],
                    "audience_quality": audience["overall_score"],
                    "partnership_history": history["disclosure_compliance_score"],
                    "legal_compliance": 1.0 if compliance["overall_compliant"] else 0.0,
                    "composite": composite_score,
                },
                "details": {
                    "safety_audit": safety,
                    "audience_analysis": audience,
                    "partnership_history": history,
                    "compliance_check": compliance,
                },
                "recommendation": self._make_recommendation(composite_score, safety, compliance),
            })
        
        # Sort by composite score
        vetted_candidates.sort(key=lambda x: x["scores"]["composite"], reverse=True)
        
        state["results"]["vetting"] = {
            "vetted_candidates": vetted_candidates,
            "approved": [c for c in vetted_candidates if c["recommendation"] == "approve"],
            "rejected": [c for c in vetted_candidates if c["recommendation"] == "reject"],
            "needs_review": [c for c in vetted_candidates if c["recommendation"] == "review"],
        }
        return state
    
    def _calculate_vetting_score(self, safety, audience, history, compliance) -> float:
        """Weighted composite score across all vetting dimensions."""
        if not compliance["overall_compliant"]:
            return 0.0  # Hard fail on compliance
        
        weights = {
            "safety": 0.30,
            "audience": 0.30,
            "history": 0.20,
            "compliance": 0.20,
        }
        
        return (
            safety["safety_score"] * weights["safety"] +
            audience["overall_score"] * weights["audience"] +
            history["disclosure_compliance_score"] * weights["history"] +
            (1.0 if compliance["overall_compliant"] else 0.0) * weights["compliance"]
        )
    
    def _make_recommendation(self, score, safety, compliance) -> str:
        if not compliance["overall_compliant"]:
            return "reject"
        if safety["risk_level"] == "high":
            return "reject"
        if score >= 0.75:
            return "approve"
        if score >= 0.50:
            return "review"
        return "reject"
```

---

## 4. Outreach Agent

### 4.1 Purpose

The Outreach Agent manages initial contact with vetted influencers, crafting personalized outreach messages and managing communication channels.

### 4.2 Implementation

```python
class OutreachAgent(DeepAgent):
    """
    Manages influencer outreach through personalized messaging
    across email, DM, and platform-specific contact methods.
    """
    
    SYSTEM_PROMPT = """You are an influencer outreach specialist.
    
    Your goal is to initiate contact with influencers in a personalized,
    authentic way that maximizes response rates.
    
    Principles:
    - Personalize every message with specific references to their content
    - Lead with value proposition, not just the ask
    - Be transparent about brand partnership nature
    - Respect their time and communication preferences
    - Follow up appropriately without being pushy
    
    You have access to:
    - Influencer content history for personalization
    - Brand campaign details
    - Past outreach templates (adapt, don't copy)
    - Communication channel preferences
    """
    
    def __init__(self, llm, tools):
        super().__init__(llm=llm, tools=tools, system_prompt=self.SYSTEM_PROMPT)
    
    @tool
    async def craft_personalized_outreach(
        self,
        influencer: InfluencerProfile,
        campaign: dict,
        tone: str = "professional_friendly"
    ) -> dict:
        """
        Generate a personalized outreach message based on
        influencer's content, style, and campaign details.
        """
        # Analyze influencer's content style
        content_analysis = await self._analyze_content_style(influencer)
        
        # Find specific content to reference
        reference_content = self._select_reference_content(
            influencer.recent_posts, 
            campaign["themes"]
        )
        
        outreach_prompt = f"""
        Write a personalized outreach message for an influencer partnership.
        
        Influencer Profile:
        - Name: {influencer.display_name}
        - Niche: {', '.join(influencer.niche_tags)}
        - Content style: {content_analysis['style_description']}
        - Recent notable post: {reference_content['title']}
        - Audience size: {influencer.follower_count:,} followers
        
        Campaign Details:
        - Brand: {campaign['brand_name']}
        - Product: {campaign['product_name']}
        - Key message: {campaign['key_message']}
        - Deliverables: {campaign['deliverables']}
        - Budget range: {campaign['budget_range']}
        - Timeline: {campaign['timeline']}
        
        Tone: {tone}
        
        Requirements:
        - Reference specific content they created
        - Explain why they're a good fit
        - Clearly state it's a paid partnership
        - Include key campaign details
        - Keep it concise (under 200 words for DM, under 300 for email)
        - Include a clear call-to-action
        
        Generate both an email version and a DM version.
        """
        
        result = await self.llm.ainvoke(outreach_prompt)
        return self._parse_outreach_message(result)
    
    @tool
    async def send_outreach(
        self,
        influencer: InfluencerProfile,
        message: dict,
        channel: str = "email"
    ) -> dict:
        """
        Send outreach message through specified channel.
        Tracks delivery and response status.
        """
        if channel == "email":
            result = await self._send_email(
                to=influencer.contact_info["email"],
                subject=message["email_subject"],
                body=message["email_body"],
                track_opens=True,
                track_clicks=True
            )
        elif channel == "instagram_dm":
            result = await self._send_instagram_dm(
                username=influencer.handle,
                message=message["dm_body"]
            )
        elif channel == "tiktok_message":
            result = await self._send_tiktok_message(
                username=influencer.handle,
                message=message["dm_body"]
            )
        else:
            raise ValueError(f"Unsupported channel: {channel}")
        
        return {
            "channel": channel,
            "sent_at": datetime.utcnow().isoformat(),
            "status": result["status"],
            "message_id": result.get("message_id"),
            "tracking_id": result.get("tracking_id"),
        }
    
    @tool
    async def schedule_follow_up(
        self,
        influencer: InfluencerProfile,
        original_message: dict,
        follow_up_sequence: list[dict] = None
    ) -> list[dict]:
        """
        Schedule a sequence of follow-up messages if no response.
        Default sequence: Day 3, Day 7, Day 14
        """
        if follow_up_sequence is None:
            follow_up_sequence = [
                {"day": 3, "tone": "gentle_reminder", "value_add": True},
                {"day": 7, "tone": "additional_value", "value_add": True},
                {"day": 14, "tone": "breakup_email", "value_add": False},
            ]
        
        scheduled = []
        for step in follow_up_sequence:
            follow_up = await self._craft_follow_up(
                influencer, original_message, step
            )
            scheduled.append({
                "scheduled_for": (datetime.utcnow() + timedelta(days=step["day"])).isoformat(),
                "message": follow_up,
                "trigger_condition": "no_response",
            })
        
        return scheduled
    
    async def run(self, state: AgentState) -> AgentState:
        """Execute outreach for approved influencer candidates."""
        approved = state["results"]["vetting"]["approved"]
        campaign = state["task_context"]["campaign"]
        
        outreach_results = []
        for candidate in approved:
            profile = candidate["profile"]
            
            # Determine best contact channel
            channel = self._select_contact_channel(profile, campaign)
            
            # Craft personalized message
            message = await self.craft_personalized_outreach(
                profile, campaign, tone=campaign.get("outreach_tone", "professional_friendly")
            )
            
            # Send outreach
            send_result = await self.send_outreach(profile, message, channel)
            
            # Schedule follow-ups
            follow_ups = await self.schedule_follow_up(profile, message)
            
            outreach_results.append({
                "influencer_id": profile.handle,
                "channel": channel,
                "message": message,
                "send_result": send_result,
                "follow_ups": follow_ups,
                "status": "sent",
            })
        
        state["results"]["outreach"] = {
            "outreach_attempts": outreach_results,
            "total_sent": len(outreach_results),
            "by_channel": self._summarize_by_channel(outreach_results),
        }
        return state
```

---

## 5. Negotiation Agent

### 5.1 Purpose

The Negotiation Agent handles rate discussions, contract terms, and deliverable agreements with influencers, aiming to reach mutually beneficial partnerships within budget constraints.

### 5.2 Implementation

```python
class NegotiationAgent(DeepAgent):
    """
    Manages rate negotiation, contract terms, and deliverable
    agreements with influencers using principled negotiation.
    """
    
    SYSTEM_PROMPT = """You are a skilled partnership negotiator.
    
    You negotiate influencer partnership terms including:
    - Compensation (flat fee, performance bonus, affiliate, product gifting)
    - Deliverables (posts, stories, videos, usage rights)
    - Timeline and exclusivity
    - Contract terms and conditions
    
    Negotiation principles:
    - Aim for win-win outcomes
    - Understand the influencer's perspective and constraints
    - Be transparent about budget parameters
    - Know your walk-away points
    - Document all agreed terms clearly
    
    You have access to:
    - Market rate data for similar influencers
    - Campaign budget constraints
    - Past negotiation outcomes
    - Contract templates
    """
    
    def __init__(self, llm, tools):
        super().__init__(llm=llm, tools=tools, system_prompt=self.SYSTEM_PROMPT)
    
    @tool
    async def research_market_rate(
        self,
        influencer: InfluencerProfile,
        deliverables: list[str]
    ) -> dict:
        """
        Research market rates for influencers with similar
        metrics and deliverable types.
        """
        # Query rate database
        rate_data = await self._query_rate_database(
            platform=influencer.platform,
            follower_range=self._get_follower_range(influencer.follower_count),
            engagement_range=self._get_engagement_range(influencer.engagement_rate),
            deliverables=deliverables
        )
        
        # Calculate suggested rate range
        base_rate = rate_data["median_rate"]
        engagement_multiplier = self._engagement_multiplier(influencer.engagement_rate)
        deliverable_multiplier = self._deliverable_multiplier(deliverables)
        
        suggested_low = base_rate * engagement_multiplier * 0.8
        suggested_high = base_rate * engagement_multiplier * deliverable_multiplier * 1.2
        
        return {
            "market_median": base_rate,
            "market_range": (rate_data["p25"], rate_data["p75"]),
            "suggested_range": (suggested_low, suggested_high),
            "engagement_multiplier": engagement_multiplier,
            "deliverable_multiplier": deliverable_multiplier,
            "rate_factors": rate_data["factors"],
        }
    
    @tool
    async def generate_proposal(
        self,
        influencer: InfluencerProfile,
        campaign: dict,
        market_rate: dict
    ) -> dict:
        """
        Generate a partnership proposal with rate, deliverables,
        and terms based on market research and campaign budget.
        """
        budget = campaign["budget"]
        deliverables = campaign["deliverables"]
        
        # Determine optimal compensation structure
        comp_structure = self._design_compensation_structure(
            budget, market_rate, deliverables
        )
        
        proposal_prompt = f"""
        Create a partnership proposal for an influencer collaboration.
        
        Influencer: {influencer.display_name} (@{influencer.handle})
        Platform: {influencer.platform}
        Followers: {influencer.follower_count:,}
        Engagement Rate: {influencer.engagement_rate:.1%}
        
        Campaign: {campaign['name']}
        Brand: {campaign['brand_name']}
        Product: {campaign['product_name']}
        Key Message: {campaign['key_message']}
        
        Deliverables Required: {', '.join(deliverables)}
        Budget Range: ${budget['min']:,} - ${budget['max']:,}
        Timeline: {campaign['timeline']}
        
        Market Rate Data:
        - Median rate: ${market_rate['market_median']:,.0f}
        - Suggested range: ${market_rate['suggested_range'][0]:,.0f} - ${market_rate['suggested_range'][1]:,.0f}
        
        Compensation Structure: {comp_structure}
        
        Generate a professional proposal including:
        1. Personalized opening referencing their work
        2. Campaign overview and brand alignment
        3. Specific deliverables with timeline
        4. Compensation breakdown
        5. Usage rights and exclusivity terms
        6. Next steps
        
        Keep it professional, concise, and focused on mutual value.
        """
        
        result = await self.llm.ainvoke(proposal_prompt)
        return self._parse_proposal(result)
    
    @tool
    async def handle_counter_offer(
        self,
        original_proposal: dict,
        counter_offer: dict,
        budget_constraints: dict,
        negotiation_history: list[dict]
    ) -> dict:
        """
        Process and respond to influencer counter-offers.
        Determines acceptance, rejection, or counter-counter.
        """
        analysis_prompt = f"""
        Analyze this negotiation exchange and recommend a response.
        
        Original Proposal:
        - Rate: ${original_proposal['rate']:,.0f}
        - Deliverables: {original_proposal['deliverables']}
        - Terms: {original_proposal['terms']}
        
        Influencer Counter-Offer:
        - Rate: ${counter_offer.get('rate', 'N/A')}
        - Deliverables: {counter_offer.get('deliverables', 'N/A')}
        - Terms: {counter_offer.get('terms', 'N/A')}
        - Justification: {counter_offer.get('justification', 'N/A')}
        
        Budget Constraints:
        - Maximum: ${budget_constraints['max']:,}
        - Target: ${budget_constraints['target']:,}
        - Walk-away: ${budget_constraints['walk_away']:,}
        
        Negotiation History:
        {self._format_negotiation_history(negotiation_history)}
        
        Analyze:
        1. Is the counter-offer within budget?
        2. Is it fair relative to market rates?
        3. What is the influencer's likely BATNA?
        4. What is our BATNA?
        5. Recommended response strategy
        
        Provide a specific counter-proposal or acceptance recommendation.
        """
        
        result = await self.llm.ainvoke(analysis_prompt)
        return self._parse_negotiation_response(result)
    
    @tool
    async def generate_contract(
        self,
        agreed_terms: dict,
        influencer: InfluencerProfile,
        campaign: dict
    ) -> dict:
        """
        Generate a partnership agreement based on negotiated terms.
        """
        contract_prompt = f"""
        Generate a influencer partnership agreement based on these agreed terms:
        
        Parties:
        - Brand: {campaign['brand_name']}
        - Influencer: {influencer.display_name} (@{influencer.handle})
        
        Agreed Terms:
        {json.dumps(agreed_terms, indent=2)}
        
        Include:
        1. Scope of work and deliverables
        2. Compensation and payment terms
        3. Timeline and deadlines
        4. Usage rights and licensing
        5. Exclusivity clauses
        6. FTC disclosure requirements
        7. Termination conditions
        8. Liability and indemnification
        9. Governing law
        
        Use clear, plain language while being legally comprehensive.
        """
        
        result = await self.llm.ainvoke(contract_prompt)
        return self._parse_contract(result)
    
    async def run(self, state: AgentState) -> AgentState:
        """Execute negotiation for influencers who responded to outreach."""
        responded = [
            r for r in state["results"]["outreach"]["outreach_attempts"]
            if r.get("response") and r["response"].get("interested")
        ]
        campaign = state["task_context"]["campaign"]
        
        negotiation_results = []
        for response in responded:
            profile = response["profile"]
            
            # Research market rate
            market_rate = await self.research_market_rate(
                profile, campaign["deliverables"]
            )
            
            # Generate initial proposal
            proposal = await self.generate_proposal(
                profile, campaign, market_rate
            )
            
            # Simulate or process actual negotiation
            negotiation_history = []
            current_offer = proposal
            max_rounds = 5
            
            for round_num in range(max_rounds):
                # In production, this would wait for actual influencer response
                counter = await self._get_influencer_response(profile, current_offer)
                
                if counter.get("accepted"):
                    negotiation_results.append({
                        "influencer_id": profile.handle,
                        "status": "accepted",
                        "final_terms": current_offer,
                        "rounds": round_num + 1,
                        "history": negotiation_history,
                    })
                    break
                
                # Handle counter-offer
                decision = await self.handle_counter_offer(
                    current_offer, counter, 
                    {"max": campaign["budget"]["max"], 
                     "target": campaign["budget"]["target"],
                     "walk_away": campaign["budget"]["max"] * 1.1},
                    negotiation_history
                )
                
                negotiation_history.append({
                    "round": round_num + 1,
                    "offer": current_offer,
                    "counter": counter,
                    "decision": decision,
                })
                
                if decision["action"] == "accept":
                    negotiation_results.append({
                        "influencer_id": profile.handle,
                        "status": "accepted",
                        "final_terms": counter,
                        "rounds": round_num + 1,
                        "history": negotiation_history,
                    })
                    break
                elif decision["action"] == "reject":
                    negotiation_results.append({
                        "influencer_id": profile.handle,
                        "status": "rejected",
                        "reason": decision["reason"],
                        "rounds": round_num + 1,
                        "history": negotiation_history,
                    })
                    break
                
                current_offer = decision["counter_proposal"]
            
            # Generate contract for accepted deals
            if negotiation_results[-1]["status"] == "accepted":
                contract = await self.generate_contract(
                    negotiation_results[-1]["final_terms"],
                    profile, campaign
                )
                negotiation_results[-1]["contract"] = contract
        
        state["results"]["negotiation"] = {
            "negotiations": negotiation_results,
            "accepted": [n for n in negotiation_results if n["status"] == "accepted"],
            "rejected": [n for n in negotiation_results if n["status"] == "rejected"],
            "pending": [n for n in negotiation_results if n["status"] == "pending"],
        }
        return state
```

---

## 6. Content Agent

### 6.1 Purpose

The Content Agent manages content creation workflows including brief generation, content review, approval workflows, and FTC compliance checking.

### 6.2 Implementation

```python
class ContentAgent(DeepAgent):
    """
    Manages the content creation process from brief to published post,
    including compliance checking and approval workflows.
    """
    
    SYSTEM_PROMPT = """You are a content creation manager for influencer partnerships.
    
    You oversee:
    - Content brief creation and distribution
    - Content review and feedback
    - FTC compliance verification
    - Approval workflow management
    - Content scheduling and publishing
    
    Ensure all content:
    - Aligns with brand guidelines and campaign objectives
    - Meets FTC disclosure requirements
    - Respects the influencer's authentic voice
    - Meets platform-specific requirements
    - Is delivered on schedule
    """
    
    def __init__(self, llm, tools):
        super().__init__(llm=llm, tools=tools, system_prompt=self.SYSTEM_PROMPT)
    
    @tool
    async def generate_content_brief(
        self,
        influencer: InfluencerProfile,
        campaign: dict,
        agreed_terms: dict
    ) -> dict:
        """
        Generate a detailed content brief for the influencer
        that balances brand requirements with creative freedom.
        """
        brief_prompt = f"""
        Create a content brief for an influencer partnership.
        
        Influencer: {influencer.display_name} (@{influencer.handle})
        Platform: {influencer.platform}
        Content Style: {influencer.niche_tags}
        Audience: {influencer.audience_demographics}
        
        Campaign: {campaign['name']}
        Brand: {campaign['brand_name']}
        Product: {campaign['product_name']}
        Key Message: {campaign['key_message']}
        Campaign Hashtags: {campaign.get('hashtags', [])}
        Brand Guidelines: {campaign['brand_guidelines']}
        
        Agreed Deliverables: {agreed_terms['deliverables']}
        Usage Rights: {agreed_terms.get('usage_rights', 'N/A')}
        
        Create a brief that includes:
        1. Campaign overview (concise)
        2. Product key points and talking points
        3. Mandatory elements (hashtags, mentions, disclosures)
        4. Creative direction and tone guidance
        5. Do's and Don'ts
        6. Deliverable specifications per platform
        7. Timeline and milestones
        8. Approval process
        
        Balance brand requirements with creative freedom.
        The brief should guide, not restrict.
        """
        
        result = await self.llm.ainvoke(brief_prompt)
        return self._parse_content_brief(result)
    
    @tool
    async def review_content_draft(
        self,
        draft: dict,
        brief: dict,
        brand_guidelines: dict
    ) -> dict:
        """
        Review influencer content draft against brief and brand guidelines.
        Provides specific, actionable feedback.
        """
        review_prompt = f"""
        Review this content draft against the campaign brief and brand guidelines.
        
        Content Draft:
        - Platform: {draft['platform']}
        - Caption: {draft.get('caption', 'N/A')}
        - Media description: {draft.get('media_description', 'N/A')}
        - Hashtags: {draft.get('hashtags', [])}
        - Mentions: {draft.get('mentions', [])}
        
        Campaign Brief:
        {json.dumps(brief, indent=2)}
        
        Brand Guidelines:
        {json.dumps(brand_guidelines, indent=2)}
        
        Review for:
        1. Brief compliance (all required elements present)
        2. Brand safety (no prohibited content)
        3. FTC disclosure compliance
        4. Platform policy compliance
        5. Tone and voice alignment
        6. Hashtag and mention accuracy
        7. Overall quality and authenticity
        
        Provide:
        - Approval status: approved / approved_with_changes / rejected
        - Specific feedback points
        - Required changes (if any)
        - Suggestions for improvement (optional)
        """
        
        result = await self.llm.ainvoke(review_prompt)
        return self._parse_content_review(result)
    
    @tool
    async def check_ftc_compliance(
        self,
        content: dict,
        platform: str
    ) -> dict:
        """
        Verify FTC disclosure compliance for sponsored content.
        Checks for proper #ad, #sponsored, or platform-native disclosure.
        """
        compliance = {
            "compliant": True,
            "disclosure_present": False,
            "disclosure_type": None,
            "disclosure_placement": None,
            "issues": [],
            "recommendations": [],
        }
        
        caption = content.get("caption", "").lower()
        hashtags = [h.lower() for h in content.get("hashtags", [])]
        
        # Check for disclosure hashtags
        disclosure_tags = ["#ad", "#sponsored", "#paid", "#partner", "#ambassador"]
        found_disclosure = [tag for tag in disclosure_tags if tag in hashtags]
        
        if found_disclosure:
            compliance["disclosure_present"] = True
            compliance["disclosure_type"] = "hashtag"
            compliance["disclosure_placement"] = "hashtags"
        elif "ad" in caption or "sponsored" in caption or "paid partnership" in caption:
            compliance["disclosure_present"] = True
            compliance["disclosure_type"] = "text"
            compliance["disclosure_placement"] = "caption"
        
        # Platform-specific checks
        if platform == "instagram":
            # Check if using Instagram's paid partnership tag
            if content.get("paid_partnership_tag"):
                compliance["disclosure_present"] = True
                compliance["disclosure_type"] = "platform_native"
        
        if not compliance["disclosure_present"]:
            compliance["compliant"] = False
            compliance["issues"].append("No FTC disclosure found")
            compliance["recommendations"].append(
                "Add #ad or #sponsored hashtag, or use platform's paid partnership tool"
            )
        
        # Check disclosure placement (should be early in caption)
        if compliance["disclosure_present"] and compliance["disclosure_placement"] == "caption":
            # Simple check - disclosure should be in first 3 lines
            lines = content.get("caption", "").split("\n")
            first_three = " ".join(lines[:3]).lower()
            if not any(tag in first_three for tag in disclosure_tags):
                compliance["recommendations"].append(
                    "Move disclosure to the beginning of the caption for visibility"
                )
        
        return compliance
    
    @tool
    async def manage_approval_workflow(
        self,
        content: dict,
        brief: dict,
        stakeholders: list[str]
    ) -> dict:
        """
        Manage the content approval workflow including
        routing to stakeholders and tracking approvals.
        """
        workflow = {
            "content_id": content["id"],
            "status": "pending_review",
            "stakeholder_reviews": {},
            "current_reviewer": None,
            "approval_history": [],
        }
        
        # Initial review by campaign manager
        review = await self.review_content_draft(content, brief, {})
        workflow["stakeholder_reviews"]["campaign_manager"] = review
        
        if review["status"] == "approved":
            workflow["status"] = "approved"
        elif review["status"] == "approved_with_changes":
            workflow["status"] = "revision_requested"
            workflow["required_changes"] = review["required_changes"]
        else:
            workflow["status"] = "rejected"
            workflow["rejection_reason"] = review["feedback"]
        
        # Route to legal if needed
        if content.get("requires_legal_review"):
            workflow["current_reviewer"] = "legal"
            # In production, this would notify legal team
        
        return workflow
    
    async def run(self, state: AgentState) -> AgentState:
        """Execute content creation workflow for accepted negotiations."""
        accepted = state["results"]["negotiation"]["accepted"]
        campaign = state["task_context"]["campaign"]
        
        content_results = []
        for deal in accepted:
            profile = deal["profile"]
            terms = deal["final_terms"]
            
            # Generate content brief
            brief = await self.generate_content_brief(profile, campaign, terms)
            
            # Send brief to influencer (in production, via email/portal)
            brief_sent = await self._send_brief_to_influencer(profile, brief)
            
            # Wait for draft (in production, this would be async with webhook)
            draft = await self._wait_for_content_draft(profile, brief)
            
            # Review draft
            review = await self.review_content_draft(
                draft, brief, campaign["brand_guidelines"]
            )
            
            # FTC compliance check
            ftc_check = await self.check_ftc_compliance(draft, profile.platform)
            
            # Manage approval workflow
            workflow = await self.manage_approval_workflow(
                draft, brief, campaign.get("stakeholders", [])
            )
            
            content_results.append({
                "influencer_id": profile.handle,
                "brief": brief,
                "draft": draft,
                "review": review,
                "ftc_compliance": ftc_check,
                "workflow": workflow,
                "status": workflow["status"],
            })
        
        state["results"]["content"] = {
            "content_items": content_results,
            "approved": [c for c in content_results if c["status"] == "approved"],
            "pending_revision": [c for c in content_results if c["status"] == "revision_requested"],
            "rejected": [c for c in content_results if c["status"] == "rejected"],
        }
        return state
```

---

## 7. Performance Agent

### 7.1 Purpose

The Performance Agent tracks, measures, and reports on campaign performance across all influencer partnerships, calculating ROI and generating insights.

### 7.2 Implementation

```python
class PerformanceAgent(DeepAgent):
    """
    Tracks and analyzes campaign performance metrics across
    all influencer partnerships and content pieces.
    """
    
    SYSTEM_PROMPT = """You are a performance marketing analyst.
    
    You track, measure, and report on influencer marketing performance.
    
    Key metrics you monitor:
    - Reach and impressions
    - Engagement (likes, comments, shares, saves)
    - Click-through rate
    - Conversion rate and attributed revenue
    - Cost per engagement (CPE)
    - Cost per acquisition (CPA)
    - Return on ad spend (ROAS)
    - Earned media value (EMV)
    - Brand lift and sentiment
    
    You provide actionable insights and recommendations
    based on performance data.
    """
    
    def __init__(self, llm, tools):
        super().__init__(llm=llm, tools=tools, system_prompt=self.SYSTEM_PROMPT)
    
    @tool
    async def collect_performance_data(
        self,
        content_items: list[dict],
        campaign: dict,
        tracking_config: dict
    ) -> list[dict]:
        """
        Collect performance data from all platforms
        for published content.
        """
        performance_data = []
        
        for item in content_items:
            profile = item["profile"]
            content = item["content"]
            
            # Collect platform metrics
            if profile.platform == "instagram":
                metrics = await self._fetch_instagram_metrics(content["id"])
            elif profile.platform == "tiktok":
                metrics = await self._fetch_tiktok_metrics(content["id"])
            elif profile.platform == "youtube":
                metrics = await self._fetch_youtube_metrics(content["id"])
            
            # Collect tracking data (UTM, promo codes)
            tracking = await self._collect_tracking_data(
                content["id"], tracking_config
            )
            
            # Calculate derived metrics
            derived = self._calculate_derived_metrics(metrics, tracking, item)
            
            performance_data.append({
                "influencer_id": profile.handle,
                "content_id": content["id"],
                "platform": profile.platform,
                "metrics": metrics,
                "tracking": tracking,
                "derived": derived,
                "collected_at": datetime.utcnow().isoformat(),
            })
        
        return performance_data
    
    @tool
    async def calculate_campaign_roi(
        self,
        performance_data: list[dict],
        campaign_costs: dict
    ) -> dict:
        """
        Calculate overall campaign ROI including:
        - Total investment (influencer fees + product + management)
        - Total attributed revenue
        - ROAS
        - Cost per acquisition
        - Earned media value
        """
        total_cost = (
            campaign_costs.get("influencer_fees", 0) +
            campaign_costs.get("product_costs", 0) +
            campaign_costs.get("management_fees", 0)
        )
        
        total_revenue = sum(
            d["tracking"].get("attributed_revenue", 0) 
            for d in performance_data
        )
        
        total_engagements = sum(
            d["metrics"].get("engagements", 0) 
            for d in performance_data
        )
        
        total_impressions = sum(
            d["metrics"].get("impressions", 0) 
            for d in performance_data
        )
        
        total_clicks = sum(
            d["tracking"].get("clicks", 0) 
            for d in performance_data
        )
        
        total_conversions = sum(
            d["tracking"].get("conversions", 0) 
            for d in performance_data
        )
        
        roas = total_revenue / total_cost if total_cost > 0 else 0
        cpe = total_cost / total_engagements if total_engagements > 0 else 0
        cpa = total_cost / total_conversions if total_conversions > 0 else 0
        ctr = total_clicks / total_impressions if total_impressions > 0 else 0
        conversion_rate = total_conversions / total_clicks if total_clicks > 0 else 0
        
        # Calculate Earned Media Value
        emv = self._calculate_emv(performance_data)
        
        return {
            "total_cost": total_cost,
            "total_revenue": total_revenue,
            "roas": roas,
            "cost_per_engagement": cpe,
            "cost_per_acquisition": cpa,
            "click_through_rate": ctr,
            "conversion_rate": conversion_rate,
            "earned_media_value": emv,
            "total_impressions": total_impressions,
            "total_engagements": total_engagements,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
        }
    
    @tool
    async def generate_performance_report(
        self,
        performance_data: list[dict],
        roi_metrics: dict,
        campaign: dict
    ) -> dict:
        """
        Generate a comprehensive performance report with
        insights and recommendations.
        """
        report_prompt = f"""
        Generate a comprehensive influencer marketing performance report.
        
        Campaign: {campaign['name']}
        Brand: {campaign['brand_name']}
        Period: {campaign['start_date']} to {campaign['end_date']}
        
        ROI Metrics:
        {json.dumps(roi_metrics, indent=2)}
        
        Individual Performance Data:
        {json.dumps(performance_data, indent=2)}
        
        Generate a report including:
        1. Executive summary
        2. Campaign overview
        3. Key metrics dashboard
        4. Top performing influencers
        5. Top performing content
        6. Platform breakdown
        7. Audience insights
        8. ROI analysis
        9. Key learnings
        10. Recommendations for future campaigns
        
        Be specific with numbers and provide actionable insights.
        """
        
        result = await self.llm.ainvoke(report_prompt)
        return self._parse_performance_report(result)
    
    @tool
    async def identify_top_performers(
        self,
        performance_data: list[dict],
        metric: str = "roas"
    ) -> list[dict]:
        """
        Identify top performing influencers and content
        based on specified metric.
        """
        # Calculate individual ROAS for each influencer
        performer_scores = []
        for data in performance_data:
            revenue = data["tracking"].get("attributed_revenue", 0)
            cost = data.get("cost", 0)
            roas = revenue / cost if cost > 0 else 0
            
            performer_scores.append({
                "influencer_id": data["influencer_id"],
                "content_id": data["content_id"],
                "platform": data["platform"],
                "roas": roas,
                "engagement_rate": data["derived"].get("engagement_rate", 0),
                "conversion_rate": data["derived"].get("conversion_rate", 0),
                "total_engagements": data["metrics"].get("engagements", 0),
                "total_revenue": revenue,
            })
        
        # Sort by specified metric
        performer_scores.sort(key=lambda x: x.get(metric, 0), reverse=True)
        return performer_scores
    
    async def run(self, state: AgentState) -> AgentState:
        """Execute performance tracking and reporting."""
        approved_content = state["results"]["content"]["approved"]
        campaign = state["task_context"]["campaign"]
        
        # Collect performance data
        performance_data = await self.collect_performance_data(
            approved_content, campaign, campaign.get("tracking", {})
        )
        
        # Calculate ROI
        roi_metrics = await self.calculate_campaign_roi(
            performance_data, campaign.get("costs", {})
        )
        
        # Generate report
        report = await self.generate_performance_report(
            performance_data, roi_metrics, campaign
        )
        
        # Identify top performers
        top_performers = await self.identify_top_performers(performance_data)
        
        state["results"]["performance"] = {
            "performance_data": performance_data,
            "roi_metrics": roi_metrics,
            "report": report,
            "top_performers": top_performers,
        }
        return state
```

---

## 8. Optimization Agent

### 8.1 Purpose

The Optimization Agent analyzes performance data to identify optimization opportunities and automatically adjusts campaign parameters for better results.

### 8.2 Implementation

```python
class OptimizationAgent(DeepAgent):
    """
    Analyzes campaign performance and identifies optimization
    opportunities across targeting, content, and budget allocation.
    """
    
    SYSTEM_PROMPT = """You are a campaign optimization specialist.
    
    You analyze performance data to identify opportunities
    for improving campaign results.
    
    Optimization areas:
    - Audience targeting refinement
    - Content strategy adjustments
    - Budget reallocation
    - Influencer selection criteria
    - Timing and frequency optimization
    - Creative direction improvements
    
    You use data-driven insights to make specific,
    actionable recommendations.
    """
    
    def __init__(self, llm, tools):
        super().__init__(llm=llm, tools=tools, system_prompt=self.SYSTEM_PROMPT)
    
    @tool
    async def analyze_audience_performance(
        self,
        performance_data: list[dict],
        demographic_data: dict
    ) -> dict:
        """
        Analyze which audience segments are performing best
        and recommend targeting adjustments.
        """
        segment_performance = {}
        
        for data in performance_data:
            demographics = data.get("audience_demographics", {})
            for segment, metrics in demographics.items():
                if segment not in segment_performance:
                    segment_performance[segment] = {
                        "impressions": 0,
                        "engagements": 0,
                        "conversions": 0,
                        "revenue": 0,
                    }
                segment_performance[segment]["impressions"] += metrics.get("impressions", 0)
                segment_performance[segment]["engagements"] += metrics.get("engagements", 0)
                segment_performance[segment]["conversions"] += metrics.get("conversions", 0)
                segment_performance[segment]["revenue"] += metrics.get("revenue", 0)
        
        # Calculate segment-level metrics
        for segment, metrics in segment_performance.items():
            metrics["engagement_rate"] = (
                metrics["engagements"] / metrics["impressions"] 
                if metrics["impressions"] > 0 else 0
            )
            metrics["conversion_rate"] = (
                metrics["conversions"] / metrics["engagements"]
                if metrics["engagements"] > 0 else 0
            )
            metrics["revenue_per_impression"] = (
                metrics["revenue"] / metrics["impressions"]
                if metrics["impressions"] > 0 else 0
            )
        
        # Identify top and bottom segments
        sorted_segments = sorted(
            segment_performance.items(),
            key=lambda x: x[1]["revenue_per_impression"],
            reverse=True
        )
        
        return {
            "segment_performance": segment_performance,
            "top_segments": [s[0] for s in sorted_segments[:3]],
            "bottom_segments": [s[0] for s in sorted_segments[-3:]],
            "recommendations": self._generate_targeting_recommendations(
                sorted_segments
            ),
        }
    
    @tool
    async def optimize_budget_allocation(
        self,
        performance_data: list[dict],
        total_budget: float,
        campaign: dict
    ) -> dict:
        """
        Recommend optimal budget allocation across influencers
        based on performance data.
        """
        # Calculate efficiency score for each influencer
        influencer_efficiency = []
        for data in performance_data:
            revenue = data["tracking"].get("attributed_revenue", 0)
            cost = data.get("cost", 0)
            roas = revenue / cost if cost > 0 else 0
            
            influencer_efficiency.append({
                "influencer_id": data["influencer_id"],
                "roas": roas,
                "cost": cost,
                "revenue": revenue,
                "efficiency_score": roas,  # Can be enhanced with more factors
            })
        
        # Sort by efficiency
        influencer_efficiency.sort(
            key=lambda x: x["efficiency_score"], 
            reverse=True
        )
        
        # Allocate budget proportionally to efficiency
        total_efficiency = sum(i["efficiency_score"] for i in influencer_efficiency)
        
        allocation = []
        for influencer in influencer_efficiency:
            if total_efficiency > 0:
                share = influencer["efficiency_score"] / total_efficiency
            else:
                share = 1.0 / len(influencer_efficiency)
            
            recommended_budget = total_budget * share
            
            allocation.append({
                "influencer_id": influencer["influencer_id"],
                "current_spend": influencer["cost"],
                "recommended_budget": recommended_budget,
                "change": recommended_budget - influencer["cost"],
                "roas": influencer["roas"],
                "rationale": f"ROAS of {influencer['roas']:.2f} indicates "
                           f"{'strong' if influencer['roas'] > 3 else 'moderate' if influencer['roas'] > 1 else 'weak'} performance",
            })
        
        return {
            "total_budget": total_budget,
            "allocation": allocation,
            "expected_improvement": self._estimate_improvement(
                allocation, influencer_efficiency
            ),
        }
    
    @tool
    async def generate_optimization_recommendations(
        self,
        performance_data: list[dict],
        roi_metrics: dict,
        campaign: dict
    ) -> list[dict]:
        """
        Generate specific, actionable optimization recommendations
        based on comprehensive performance analysis.
        """
        recommendations_prompt = f"""
        Analyze this campaign performance data and generate
        specific, actionable optimization recommendations.
        
        Campaign: {campaign['name']}
        ROI Metrics: {json.dumps(roi_metrics, indent=2)}
        Performance Data: {json.dumps(performance_data, indent=2)}
        
        Generate recommendations across these categories:
        1. Audience targeting adjustments
        2. Content strategy improvements
        3. Influencer selection criteria updates
        4. Budget reallocation suggestions
        5. Timing and frequency optimizations
        6. Creative direction adjustments
        
        For each recommendation, provide:
        - Category
        - Specific action
        - Expected impact
        - Implementation effort (low/medium/high)
        - Priority (high/medium/low)
        - Supporting data/rationale
        
        Focus on high-impact, actionable recommendations.
        """
        
        result = await self.llm.ainvoke(recommendations_prompt)
        return self._parse_recommendations(result)
    
    async def run(self, state: AgentState) -> AgentState:
        """Execute optimization analysis and generate recommendations."""
        performance_data = state["results"]["performance"]["performance_data"]
        roi_metrics = state["results"]["performance"]["roi_metrics"]
        campaign = state["task_context"]["campaign"]
        
        # Analyze audience performance
        audience_analysis = await self.analyze_audience_performance(
            performance_data, campaign.get("target_demographics", {})
        )
        
        # Optimize budget allocation
        budget_optimization = await self.optimize_budget_allocation(
            performance_data, campaign["budget"]["total"], campaign
        )
        
        # Generate comprehensive recommendations
        recommendations = await self.generate_optimization_recommendations(
            performance_data, roi_metrics, campaign
        )
        
        state["results"]["optimization"] = {
            "audience_analysis": audience_analysis,
            "budget_optimization": budget_optimization,
            "recommendations": recommendations,
        }
        return state
```

---

## 9. Relationship Management Agent

### 9.1 Purpose

The Relationship Management Agent maintains long-term relationships with influencers, managing communication, tracking interaction history, and identifying upsell/cross-sell opportunities.

### 9.2 Implementation

```python
class RelationshipAgent(DeepAgent):
    """
    Manages long-term influencer relationships including:
    - Communication tracking
    - Relationship health scoring
    - Upsell/cross-sell identification
    - Retention and loyalty programs
    - Conflict resolution
    """
    
    SYSTEM_PROMPT = """You are an influencer relationship manager.
    
    You build and maintain long-term relationships with influencers
    to maximize lifetime value and create brand advocates.
    
    Responsibilities:
    - Track all interactions and communications
    - Monitor relationship health and satisfaction
    - Identify upsell and cross-sell opportunities
    - Manage retention and loyalty programs
    - Handle issues and conflicts proactively
    - Coordinate with other agents on relationship context
    
    You have access to:
    - Full interaction history
    - Performance data across campaigns
    - Communication preferences
    - Personal notes and context
    """
    
    def __init__(self, llm, tools, graph_db):
        super().__init__(llm=llm, tools=tools, system_prompt=self.SYSTEM_PROMPT)
        self.graph_db = graph_db
    
    @tool
    async def calculate_relationship_health(
        self,
        influencer_id: str,
        interaction_history: list[dict],
        performance_data: list[dict]
    ) -> dict:
        """
        Calculate a relationship health score based on:
        - Communication frequency and quality
        - Performance consistency
        - Responsiveness and professionalism
        - Growth trajectory
        - Brand advocacy indicators
        """
        health_factors = {
            "communication_score": 0.0,
            "performance_score": 0.0,
            "professionalism_score": 0.0,
            "growth_score": 0.0,
            "advocacy_score": 0.0,
        }
        
        # Communication analysis
        if interaction_history:
            response_times = [
                i.get("response_time_hours", 48) 
                for i in interaction_history
            ]
            avg_response_time = sum(response_times) / len(response_times)
            health_factors["communication_score"] = max(
                0, 1 - (avg_response_time / 168)  # Normalize to 1 week
            )
        
        # Performance analysis
        if performance_data:
            roas_values = [p.get("roas", 0) for p in performance_data]
            avg_roas = sum(roas_values) / len(roas_values)
            health_factors["performance_score"] = min(avg_roas / 5, 1.0)
        
        # Professionalism (from interaction notes)
        professional_indicators = sum(
            1 for i in interaction_history 
            if i.get("professional", True)
        )
        health_factors["professionalism_score"] = (
            professional_indicators / len(interaction_history)
            if interaction_history else 0.5
        )
        
        # Growth trajectory
        if len(performance_data) >= 2:
            recent = performance_data[-1].get("follower_count", 0)
            previous = performance_data[-2].get("follower_count", 0)
            growth = (recent - previous) / previous if previous > 0 else 0
            health_factors["growth_score"] = min(max(growth * 10, 0), 1)
        
        # Advocacy (unsolicited positive mentions, repeat partnerships)
        advocacy_indicators = sum(
            1 for i in interaction_history
            if i.get("unsolicited_mention", False) or i.get("repeat_partnership", False)
        )
        health_factors["advocacy_score"] = min(
            advocacy_indicators / 5, 1.0
        )
        
        # Weighted composite
        weights = {
            "communication_score": 0.20,
            "performance_score": 0.30,
            "professionalism_score": 0.20,
            "growth_score": 0.15,
            "advocacy_score": 0.15,
        }
        
        overall_health = sum(
            health_factors[k] * weights[k] for k in weights
        )
        
        return {
            "overall_score": overall_health,
            "factors": health_factors,
            "status": (
                "strong" if overall_health >= 0.7
                else "healthy" if overall_health >= 0.5
                else "at_risk" if overall_health >= 0.3
                else "critical"
            ),
            "last_assessed": datetime.utcnow().isoformat(),
        }
    
    @tool
    async def identify_upsell_opportunities(
        self,
        influencer_id: str,
        current_campaigns: list[dict],
        performance_data: list[dict],
        available_products: list[dict]
    ) -> list[dict]:
        """
        Identify opportunities to expand the partnership
        with existing influencers.
        """
        opportunities = []
        
        # Analyze content performance for expansion opportunities
        top_content = sorted(
            performance_data,
            key=lambda x: x.get("roas", 0),
            reverse=True
        )[:3]
        
        for content in top_content:
            if content.get("roas", 0) > 3:
                opportunities.append({
                    "type": "content_expansion",
                    "influencer_id": influencer_id,
                    "rationale": f"High-performing content (ROAS: {content['roas']:.2f}) "
                               f"suggests potential for expanded partnership",
                    "suggested_action": "Propose additional content series or longer-term partnership",
                    "expected_value": content.get("revenue", 0) * 0.5,
                    "priority": "high",
                })
        
        # Check for product cross-sell
        current_products = set(
            c.get("product") for c in current_campaigns
        )
        for product in available_products:
            if product["name"] not in current_products:
                # Check if influencer's audience aligns with product
                alignment = self._check_audience_product_alignment(
                    influencer_id, product
                )
                if alignment > 0.6:
                    opportunities.append({
                        "type": "product_cross_sell",
                        "influencer_id": influencer_id,
                        "product": product["name"],
                        "rationale": f"Audience alignment score: {alignment:.2f}",
                        "suggested_action": f"Introduce {product['name']} to partnership",
                        "expected_value": product.get("avg_partnership_value", 0),
                        "priority": "medium" if alignment > 0.8 else "low",
                    })
        
        return opportunities
    
    @tool
    async def generate_communication_schedule(
        self,
        influencer_id: str,
        relationship_health: dict,
        campaign_calendar: list[dict]
    ) -> list[dict]:
        """
        Generate a personalized communication schedule
        based on relationship health and campaign needs.
        """
        schedule = []
        health_status = relationship_health["status"]
        
        # Base communication frequency by health status
        frequency_map = {
            "strong": {"check_in_days": 14, "value_add_days": 7},
            "healthy": {"check_in_days": 7, "value_add_days": 14},
            "at_risk": {"check_in_days": 3, "value_add_days": 7},
            "critical": {"check_in_days": 1, "value_add_days": 3},
        }
        
        freq = frequency_map.get(health_status, frequency_map["healthy"])
        
        # Generate check-in schedule
        for day in range(0, 90, freq["check_in_days"]):
            schedule.append({
                "type": "check_in",
                "scheduled_for": (datetime.utcnow() + timedelta(days=day)).isoformat(),
                "purpose": "Relationship maintenance and satisfaction check",
                "channel": "email",  # Could be personalized
                "auto_generate": True,
            })
        
        # Generate value-add schedule
        for day in range(0, 90, freq["value_add_days"]):
            schedule.append({
                "type": "value_add",
                "scheduled_for": (datetime.utcnow() + timedelta(days=day)).isoformat(),
                "purpose": "Share relevant content, industry insights, or opportunities",
                "channel": "email",
                "auto_generate": True,
            })
        
        # Add campaign-specific touchpoints
        for campaign in campaign_calendar:
            schedule.append({
                "type": "campaign_touchpoint",
                "scheduled_for": campaign["start_date"],
                "purpose": f"Campaign kickoff: {campaign['name']}",
                "channel": "email",
                "auto_generate": False,
            })
        
        return sorted(schedule, key=lambda x: x["scheduled_for"])
    
    @tool
    async def update_relationship_graph(
        self,
        influencer_id: str,
        interaction: dict,
        relationship_data: dict
    ) -> None:
        """
        Update the relationship graph database with
        new interaction data and relationship context.
        """
        # Create or update influencer node
        await self.graph_db.run("""
            MERGE (i:Influencer {id: $influencer_id})
            SET i.last_interaction = $timestamp,
                i.health_score = $health_score,
                i.total_campaigns = $total_campaigns,
                i.total_revenue = $total_revenue
        """, {
            "influencer_id": influencer_id,
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": relationship_data["overall_score"],
            "total_campaigns": relationship_data.get("total_campaigns", 0),
            "total_revenue": relationship_data.get("total_revenue", 0),
        })
        
        # Create interaction node and relationship
        await self.graph_db.run("""
            MATCH (i:Influencer {id: $influencer_id})
            CREATE (int:Interaction {
                id: $interaction_id,
                type: $type,
                timestamp: $timestamp,
                sentiment: $sentiment,
                notes: $notes
            })
            CREATE (i)-[:HAS_INTERACTION]->(int)
        """, {
            "influencer_id": influencer_id,
            "interaction_id": str(uuid.uuid4()),
            "type": interaction["type"],
            "timestamp": datetime.utcnow().isoformat(),
            "sentiment": interaction.get("sentiment", "neutral"),
            "notes": interaction.get("notes", ""),
        })
    
    async def run(self, state: AgentState) -> AgentState:
        """Execute relationship management for all partnered influencers."""
        accepted = state["results"]["negotiation"]["accepted"]
        performance_data = state["results"]["performance"]["performance_data"]
        
        relationship_results = []
        for deal in accepted:
            profile = deal["profile"]
            influencer_id = profile.handle
            
            # Get interaction history
            history = await self._get_interaction_history(influencer_id)
            
            # Get performance history
            perf_history = [
                p for p in performance_data 
                if p["influencer_id"] == influencer_id
            ]
            
            # Calculate relationship health
            health = await self.calculate_relationship_health(
                influencer_id, history, perf_history
            )
            
            # Identify upsell opportunities
            opportunities = await self.identify_upsell_opportunities(
                influencer_id,
                state["task_context"]["campaign"],
                perf_history,
                state["task_context"].get("available_products", [])
            )
            
            # Generate communication schedule
            schedule = await self.generate_communication_schedule(
                influencer_id, health, 
                state["task_context"].get("campaign_calendar", [])
            )
            
            # Update relationship graph
            await self.update_relationship_graph(
                influencer_id,
                {"type": "campaign_completion", "notes": "Campaign wrapped"},
                health
            )
            
            relationship_results.append({
                "influencer_id": influencer_id,
                "health": health,
                "opportunities": opportunities,
                "communication_schedule": schedule,
            })
        
        state["results"]["relationship"] = {
            "relationships": relationship_results,
            "summary": {
                "strong": sum(1 for r in relationship_results if r["health"]["status"] == "strong"),
                "healthy": sum(1 for r in relationship_results if r["health"]["status"] == "healthy"),
                "at_risk": sum(1 for r in relationship_results if r["health"]["status"] == "at_risk"),
                "critical": sum(1 for r in relationship_results if r["health"]["status"] == "critical"),
            },
            "upsell_opportunities": [
                opp for r in relationship_results 
                for opp in r["opportunities"]
            ],
        }
        return state
```

---

## 10. Code Examples & Snippets

### 10.1 Complete Pipeline Execution

```python
import asyncio
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

async def run_influencer_marketing_pipeline(campaign_config: dict):
    """
    Execute the complete influencer marketing pipeline.
    """
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    
    # Initialize tools and stores
    tools = initialize_all_tools()
    vector_store = initialize_vector_store()
    graph_db = initialize_graph_db()
    
    # Create orchestrator
    orchestrator = InfluencerMarketingOrchestrator(
        llm=llm,
        tools=tools,
        vector_store=vector_store,
        graph_db=graph_db
    )
    
    # Initialize state
    initial_state = AgentState(
        messages=[],
        influencer_id=None,
        campaign_id=campaign_config["id"],
        current_agent="discovery",
        task_context={"campaign": campaign_config},
        results={},
        errors=[],
        metadata={"started_at": datetime.utcnow().isoformat()},
    )
    
    # Execute pipeline
    final_state = await orchestrator.workflow.ainvoke(initial_state)
    
    return final_state

# Run the pipeline
campaign_config = {
    "id": "camp_2026_q4_001",
    "name": "Fall Product Launch 2026",
    "brand_name": "Acme Beauty",
    "product_name": "Vitamin C Serum",
    "key_message": "Radiant skin in 7 days",
    "target_platforms": ["instagram", "tiktok"],
    "min_followers": 10000,
    "max_followers": 500000,
    "primary_hashtag": "#skincareroutine",
    "keywords": ["skincare", "beauty", "glow", "vitaminc"],
    "target_demographics": {
        "age_range": "18-34",
        "gender": "female",
        "locations": ["US", "UK", "CA"],
        "interests": ["skincare", "beauty", "wellness"],
    },
    "brand_guidelines": {
        "prohibited_topics": ["politics", "religion", "controversial"],
        "competitors": ["BrandX", "BrandY"],
        "brand_values": ["authenticity", "inclusivity", "sustainability"],
        "tone": "professional_friendly",
    },
    "deliverables": ["feed_post", "stories", "reel"],
    "budget": {"min": 50000, "max": 150000, "total": 100000},
    "timeline": "2026-10-15 to 2026-11-15",
    "requirements": {"ftc_compliant": True, "exclusivity": "category_30_days"},
}

result = asyncio.run(run_influencer_marketing_pipeline(campaign_config))
```

### 10.2 FastAPI Endpoint

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="Influencer Marketing API")

class CampaignRequest(BaseModel):
    name: str
    brand_name: str
    product_name: str
    target_platforms: list[str]
    min_followers: int
    max_followers: int
    budget: dict
    deliverables: list[str]

@app.post("/campaigns")
async def create_campaign(
    request: CampaignRequest,
    background_tasks: BackgroundTasks
):
    """Create and launch a new influencer marketing campaign."""
    campaign_id = f"camp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    campaign_config = {
        "id": campaign_id,
        **request.dict(),
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
    }
    
    # Launch pipeline in background
    background_tasks.add_task(
        run_influencer_marketing_pipeline,
        campaign_config
    )
    
    return {
        "campaign_id": campaign_id,
        "status": "initiated",
        "message": "Campaign pipeline started successfully",
    }

@app.get("/campaigns/{campaign_id}")
async def get_campaign_status(campaign_id: str):
    """Get current status and results of a campaign."""
    # Fetch from database
    campaign = await fetch_campaign(campaign_id)
    return campaign

@app.get("/campaigns/{campaign_id}/performance")
async def get_campaign_performance(campaign_id: str):
    """Get performance metrics for a campaign."""
    performance = await fetch_performance_data(campaign_id)
    return performance

@app.get("/influencers/{influencer_id}/health")
async def get_influencer_health(influencer_id: str):
    """Get relationship health score for an influencer."""
    health = await calculate_influencer_health(influencer_id)
    return health
```

### 10.3 Celery Task Queue Integration

```python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery("influencer_marketing")
celery_app.config_from_object({
    "broker_url": "redis://localhost:6379/0",
    "result_backend": "redis://localhost:6379/0",
    "task_serializer": "json",
    "result_serializer": "json",
    "timezone": "UTC",
})

@celery_app.task(bind=True, max_retries=3)
def execute_agent_task(self, agent_name: str, state_dict: dict):
    """Execute a single agent task asynchronously."""
    try:
        state = AgentState(**state_dict)
        agent = get_agent(agent_name)
        result = asyncio.run(agent.run(state))
        return dict(result)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@celery_app.task
def schedule_performance_collection(campaign_id: str):
    """Schedule periodic performance data collection."""
    # Collect metrics every 6 hours during active campaign
    performance_data = collect_all_metrics(campaign_id)
    store_performance_data(campaign_id, performance_data)

@celery_app.task
def schedule_relationship_check_ins():
    """Daily relationship health check for all active influencers."""
    active_influencers = get_active_influencers()
    for influencer in active_influencers:
        health = calculate_relationship_health(influencer["id"])
        if health["status"] in ["at_risk", "critical"]:
            notify_account_manager(influencer["id"], health)

# Celery beat schedule
celery_app.conf.beat_schedule = {
    "collect-performance": {
        "task": "schedule_performance_collection",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "relationship-check": {
        "task": "schedule_relationship_check_ins",
        "schedule": crontab(minute=0, hour=9),  # Daily at 9 AM
    },
}
```

### 10.4 LangSmith Tracing Configuration

```python
from langsmith import Client
from langchain.callbacks.tracers.langchain import LangChainTracer

# Configure LangSmith for observability
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-api-key"
os.environ["LANGCHAIN_PROJECT"] = "influencer-marketing"

tracer = LangChainTracer(
    project_name="influencer-marketing",
    example_id=None,
)

# Use in agent execution
async def run_with_tracing(agent, state):
    with tracer.as_runnable():
        result = await agent.run(state)
    return result
```

### 10.5 Vector Store Setup

```python
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings
import pinecone

def initialize_vector_store():
    """Initialize Pinecone vector store for influencer profiles."""
    pinecone.init(
        api_key=os.environ["PINECONE_API_KEY"],
        environment=os.environ["PINECONE_ENVIRONMENT"],
    )
    
    index_name = "influencer-profiles"
    
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(
            name=index_name,
            dimension=1536,  # OpenAI embeddings dimension
            metric="cosine",
        )
    
    index = pinecone.Index(index_name)
    embeddings = OpenAIEmbeddings()
    
    vector_store = Pinecone(index, embeddings, "text")
    return vector_store

async def index_influencer_profiles(profiles: list[InfluencerProfile]):
    """Index influencer profiles for similarity search."""
    texts = []
    metadatas = []
    
    for profile in profiles:
        text = f"""
        {profile.display_name} (@{profile.handle})
        Platform: {profile.platform}
        Niche: {', '.join(profile.niche_tags)}
        Followers: {profile.follower_count:,}
        Engagement: {profile.engagement_rate:.1%}
        Bio: {profile.bio}
        """
        texts.append(text)
        metadatas.append({
            "platform": profile.platform,
            "handle": profile.handle,
            "follower_count": profile.follower_count,
            "engagement_rate": profile.engagement_rate,
        })
    
    await vector_store.aadd_texts(texts, metadatas)
```

### 10.6 Neo4j Graph Database Setup

```python
from neo4j import AsyncGraphDatabase

class InfluencerGraphDB:
    """Neo4j graph database for relationship mapping."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    async def initialize_schema(self):
        """Create constraints and indexes."""
        async with self.driver.session() as session:
            # Constraints
            await session.run("""
                CREATE CONSTRAINT influencer_id IF NOT EXISTS
                FOR (i:Influencer) REQUIRE i.id IS UNIQUE
            """)
            await session.run("""
                CREATE CONSTRAINT campaign_id IF NOT EXISTS
                FOR (c:Campaign) REQUIRE c.id IS UNIQUE
            """)
            
            # Indexes
            await session.run("""
                CREATE INDEX influencer_platform IF NOT EXISTS
                FOR (i:Influencer) ON (i.platform)
            """)
            await session.run("""
                CREATE INDEX influencer_health IF NOT EXISTS
                FOR (i:Influencer) ON (i.health_score)
            """)
    
    async def find_similar_influencers(
        self, 
        influencer_id: str, 
        limit: int = 10
    ) -> list[dict]:
        """Find similar influencers based on shared connections and attributes."""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (i:Influencer {id: $influencer_id})-[:COLLABORATED_WITH]-(c:Campaign)
                      <-[:PARTICIPATED_IN]-(other:Influencer)
                WHERE other.id <> $influencer_id
                WITH other, count(c) as shared_campaigns
                ORDER BY shared_campaigns DESC
                LIMIT $limit
                RETURN other.id as influencer_id, 
                       other.handle as handle,
                       other.platform as platform,
                       shared_campaigns
            """, {"influencer_id": influencer_id, "limit": limit})
            
            return [record.data() async for record in result]
    
    async def get_influencer_network(
        self, 
        influencer_id: str, 
        depth: int = 2
    ) -> dict:
        """Get the full network around an influencer."""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH path = (i:Influencer {id: $influencer_id})
                      -[:COLLABORATED_WITH|SIMILAR_TO*1..%d]-(connected)
                RETURN [node in nodes(path) | node.id] as path,
                       [node in nodes(path) | node.handle] as handles,
                       length(path) as depth
            """ % depth, {"influencer_id": influencer_id})
            
            paths = [record.data() async for record in result]
            return {
                "influencer_id": influencer_id,
                "network_paths": paths,
                "network_size": len(paths),
            }
```

---

## 11. Testing Strategy

### 11.1 Test Pyramid

```
                    ┌─────────┐
                    │   E2E   │  (5%)
                    │  Tests  │
                   ┌┴─────────┴┐
                   │ Integration│  (15%)
                   │   Tests    │
                  ┌┴────────────┴┐
                  │    Unit       │  (80%)
                  │    Tests      │
                  └───────────────┘
```

### 11.2 Unit Tests

```python
# tests/test_discovery_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.discovery import DiscoveryAgent, InfluencerProfile

@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content="test"))
    return llm

@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    store.aadd_texts = AsyncMock()
    return store

@pytest.fixture
def discovery_agent(mock_llm, mock_vector_store):
    tools = []
    return DiscoveryAgent(mock_llm, tools, mock_vector_store)

@pytest.mark.asyncio
async def test_search_instagram_hashtags(discovery_agent):
    """Test hashtag-based influencer discovery."""
    # Mock API response
    mock_response = {
        "data": [
            {"id": "123", "name": "skincare"},
            {"id": "456", "name": "beauty"},
        ]
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=MagicMock(json=AsyncMock(return_value=mock_response))
        )
        
        results = await discovery_agent.search_instagram_hashtags(
            hashtag="skincare",
            min_followers=10000,
            max_followers=100000
        )
        
        assert isinstance(results, list)
        assert len(results) > 0

@pytest.mark.asyncio
async def test_engagement_authenticity_analysis(discovery_agent):
    """Test engagement authenticity scoring."""
    profile = InfluencerProfile(
        platform="instagram",
        handle="test_influencer",
        display_name="Test Influencer",
        bio="Test bio",
        follower_count=50000,
        following_count=500,
        post_count=200,
        engagement_rate=0.05,
        avg_likes=2500,
        avg_comments=100,
        niche_tags=["skincare", "beauty"],
        audience_demographics={"age": "18-34", "gender": "female"},
        recent_posts=[],
        brand_mentions=[],
        profile_url="https://instagram.com/test_influencer",
    )
    
    result = await discovery_agent.analyze_engagement_authenticity(profile)
    
    assert "authenticity_score" in result
    assert 0 <= result["authenticity_score"] <= 1
    assert "red_flags" in result
    assert "green_flags" in result

@pytest.mark.asyncio
async def test_discovery_agent_run(discovery_agent, mock_llm):
    """Test full discovery agent execution."""
    state = AgentState(
        messages=[],
        influencer_id=None,
        campaign_id="test_campaign",
        current_agent="discovery",
        task_context={
            "campaign": {
                "target_platforms": ["instagram"],
                "min_followers": 10000,
                "max_followers": 100000,
                "primary_hashtag": "skincare",
                "keywords": ["skincare", "beauty"],
            }
        },
        results={},
        errors=[],
        metadata={},
    )
    
    # Mock the search to return test data
    with patch.object(
        discovery_agent, 
        "search_instagram_hashtags", 
        new=AsyncMock(return_value=[])
    ):
        result = await discovery_agent.run(state)
    
    assert "discovery" in result["results"]
    assert "candidates" in result["results"]["discovery"]
```

### 11.3 Integration Tests

```python
# tests/test_pipeline_integration.py
import pytest
from langchain_openai import ChatOpenAI
from orchestrator import InfluencerMarketingOrchestrator

@pytest.fixture
def test_orchestrator():
    """Create orchestrator with test configuration."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = initialize_test_tools()
    vector_store = initialize_test_vector_store()
    graph_db = initialize_test_graph_db()
    
    return InfluencerMarketingOrchestrator(llm, tools, vector_store, graph_db)

@pytest.mark.asyncio
async def test_full_pipeline_execution(test_orchestrator):
    """Test complete pipeline from discovery to relationship management."""
    campaign_config = {
        "id": "test_camp_001",
        "name": "Test Campaign",
        "brand_name": "Test Brand",
        "product_name": "Test Product",
        "key_message": "Test message",
        "target_platforms": ["instagram"],
        "min_followers": 10000,
        "max_followers": 100000,
        "primary_hashtag": "test",
        "keywords": ["test"],
        "target_demographics": {
            "age_range": "18-34",
            "gender": "female",
            "locations": ["US"],
            "interests": ["beauty"],
        },
        "brand_guidelines": {
            "prohibited_topics": [],
            "competitors": [],
            "brand_values": ["authenticity"],
            "tone": "professional",
        },
        "deliverables": ["feed_post"],
        "budget": {"min": 1000, "max": 5000, "total": 3000},
        "timeline": "2026-10-01 to 2026-10-31",
        "requirements": {"ftc_compliant": True},
    }
    
    initial_state = AgentState(
        messages=[],
        influencer_id=None,
        campaign_id=campaign_config["id"],
        current_agent="discovery",
        task_context={"campaign": campaign_config},
        results={},
        errors=[],
        metadata={},
    )
    
    # Execute pipeline
    final_state = await test_orchestrator.workflow.ainvoke(initial_state)
    
    # Verify all agents executed
    assert "discovery" in final_state["results"]
    assert "vetting" in final_state["results"]
    assert "outreach" in final_state["results"]
    assert "negotiation" in final_state["results"]
    assert "content" in final_state["results"]
    assert "performance" in final_state["results"]
    assert "optimization" in final_state["results"]
    assert "relationship" in final_state["results"]
    
    # Verify no errors
    assert len(final_state["errors"]) == 0

@pytest.mark.asyncio
async def test_agent_communication(test_orchestrator):
    """Test that agents properly communicate through shared state."""
    # Test that discovery results flow to vetting
    # Test that vetting results flow to outreach
    # etc.
    pass

@pytest.mark.asyncio
async def test_error_handling_and_recovery(test_orchestrator):
    """Test pipeline behavior when individual agents fail."""
    # Simulate agent failure
    # Verify error is captured in state
    # Verify pipeline can recover or gracefully terminate
    pass
```

### 11.4 E2E Tests

```python
# tests/test_e2e_api.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_campaign_e2e():
    """Test full campaign creation and execution via API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create campaign
        response = await client.post("/campaigns", json={
            "name": "E2E Test Campaign",
            "brand_name": "Test Brand",
            "product_name": "Test Product",
            "target_platforms": ["instagram"],
            "min_followers": 10000,
            "max_followers": 100000,
            "budget": {"min": 1000, "max": 5000, "total": 3000},
            "deliverables": ["feed_post"],
        })
        
        assert response.status_code == 200
        campaign_id = response.json()["campaign_id"]
        
        # Poll for completion
        max_wait = 300  # 5 minutes
        waited = 0
        while waited < max_wait:
            status_response = await client.get(f"/campaigns/{campaign_id}")
            status = status_response.json()
            
            if status["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(5)
            waited += 5
        
        # Verify results
        assert status["status"] == "completed"
        assert "results" in status
```

### 11.5 Performance Tests

```python
# tests/test_performance.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.asyncio
async def test_discovery_throughput():
    """Test discovery agent can handle large candidate volumes."""
    agent = create_test_agent()
    
    start = time.time()
    results = await agent.search_instagram_hashtags(
        hashtag="beauty", limit=1000
    )
    elapsed = time.time() - start
    
    assert len(results) > 0
    assert elapsed < 30  # Should complete within 30 seconds

@pytest.mark.asyncio
async def test_parallel_agent_execution():
    """Test that independent agents can run in parallel."""
    # Discovery for multiple campaigns simultaneously
    campaigns = [create_test_campaign(i) for i in range(5)]
    
    start = time.time()
    results = await asyncio.gather(*[
        run_discovery_for_campaign(c) for c in campaigns
    ])
    elapsed = time.time() - start
    
    assert len(results) == 5
    assert elapsed < 60  # All 5 should complete within 60 seconds

@pytest.mark.asyncio
async def test_vector_store_query_performance():
    """Test vector store similarity search performance."""
    vector_store = initialize_test_vector_store()
    
    # Index 10,000 profiles
    profiles = generate_test_profiles(10000)
    await vector_store.aadd_texts(
        [p.text for p in profiles],
        [p.metadata for p in profiles]
    )
    
    # Query performance
    start = time.time()
    results = await vector_store.asimilarity_search(
        "beauty skincare influencer", k=10
    )
    elapsed = time.time() - start
    
    assert len(results) == 10
    assert elapsed < 1  # Should be under 1 second
```

### 11.6 Mock Data Fixtures

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_influencer_profile():
    return InfluencerProfile(
        platform="instagram",
        handle="beauty_jane",
        display_name="Jane's Beauty Blog",
        bio="Sharing authentic skincare tips and product reviews",
        follower_count=125000,
        following_count=800,
        post_count=450,
        engagement_rate=0.045,
        avg_likes=5625,
        avg_comments=180,
        niche_tags=["skincare", "beauty", "wellness"],
        audience_demographics={
            "age": {"18-24": 0.35, "25-34": 0.45, "35-44": 0.15, "45+": 0.05},
            "gender": {"female": 0.85, "male": 0.15},
            "locations": {"US": 0.60, "UK": 0.20, "CA": 0.10, "other": 0.10},
        },
        recent_posts=[
            {"id": "1", "likes": 5200, "comments": 150, "date": "2026-09-15"},
            {"id": "2", "likes": 6100, "comments": 200, "date": "2026-09-10"},
        ],
        brand_mentions=["BrandA", "BrandB"],
        profile_url="https://instagram.com/beauty_jane",
        contact_info={"email": "jane@beautyblog.com"},
    )

@pytest.fixture
def sample_campaign_config():
    return {
        "id": "test_camp_001",
        "name": "Test Skincare Campaign",
        "brand_name": "TestBrand",
        "product_name": "Hydrating Serum",
        "key_message": "Deep hydration for all skin types",
        "target_platforms": ["instagram", "tiktok"],
        "min_followers": 10000,
        "max_followers": 500000,
        "primary_hashtag": "#skincareroutine",
        "keywords": ["skincare", "hydration", "serum", "beauty"],
        "target_demographics": {
            "age_range": "18-34",
            "gender": "female",
            "locations": ["US", "UK", "CA"],
            "interests": ["skincare", "beauty", "wellness"],
        },
        "brand_guidelines": {
            "prohibited_topics": ["politics", "religion"],
            "competitors": ["CompetitorX"],
            "brand_values": ["authenticity", "science-backed"],
            "tone": "professional_friendly",
        },
        "deliverables": ["feed_post", "stories", "reel"],
        "budget": {"min": 50000, "max": 150000, "total": 100000},
        "timeline": "2026-10-01 to 2026-10-31",
        "requirements": {"ftc_compliant": True, "exclusivity": "category_30_days"},
    }
```

### 11.7 Test Coverage Requirements

| Component | Unit Tests | Integration Tests | E2E Tests |
|-----------|-----------|-------------------|-----------|
| Discovery Agent | ✅ | ✅ | ✅ |
| Vetting Agent | ✅ | ✅ | ✅ |
| Outreach Agent | ✅ | ✅ | ✅ |
| Negotiation Agent | ✅ | ✅ | ✅ |
| Content Agent | ✅ | ✅ | ✅ |
| Performance Agent | ✅ | ✅ | ✅ |
| Optimization Agent | ✅ | ✅ | ✅ |
| Relationship Agent | ✅ | ✅ | ✅ |
| Orchestrator | ✅ | ✅ | ✅ |
| API Endpoints | N/A | ✅ | ✅ |
| Database Layer | ✅ | ✅ | N/A |

### 11.8 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements-test.txt
      - run: pytest tests/unit -v --cov=agents --cov-report=xml
      - uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports: ["6379:6379"]
      neo4j:
        image: neo4j:5
        ports: ["7687:7687"]
        env:
          NEO4J_AUTH: neo4j/testpassword
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements-test.txt
      - run: pytest tests/integration -v

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements-test.txt
      - run: pytest tests/e2e -v
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

---

## Appendix A: Environment Variables

```bash
# .env
# LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Platform APIs
INSTAGRAM_ACCESS_TOKEN=...
TIKTOK_ACCESS_TOKEN=...
YOUTUBE_API_KEY=...

# Infrastructure
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost:5432/influencer_marketing

# Observability
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=influencer_marketing

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Appendix B: Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  API Server │  │  API Server │  │  API Server │          │
│  │   (FastAPI) │  │   (FastAPI) │  │   (FastAPI) │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         └─────────────────┼─────────────────┘                │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────┐        │
│  │              Celery Worker Pool                  │        │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐    │        │
│  │  │Worker 1│ │Worker 2│ │Worker 3│ │Worker N│    │        │
│  │  └────────┘ └────────┘ └────────┘ └────────┘    │        │
│  └────────────────────────┬────────────────────────┘        │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────┐        │
│  │              Redis (Task Queue)                  │        │
│  └────────────────────────┬────────────────────────┘        │
│                           │                                  │
│  ┌──────────────┐  ┌──────┴──────┐  ┌──────────────┐       │
│  │  PostgreSQL  │  │   Neo4j     │  │   Pinecone   │       │
│  │  (Primary)   │  │  (Graph DB) │  │  (Vector)    │       │
│  └──────────────┘  └─────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

*End of Implementation Plan*
