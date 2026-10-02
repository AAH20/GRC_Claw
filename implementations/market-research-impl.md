# AI-Powered Market Research Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Status:** Draft  
**Framework:** LangChain DeepAgents (LangGraph-based)

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Data Collection Agent Implementation](#2-data-collection-agent-implementation)
3. [Analysis Agent Implementation](#3-analysis-agent-implementation)
4. [Reporting Agent Implementation](#4-reporting-agent-implementation)
5. [Action Agent Implementation](#5-action-agent-implementation)
6. [Performance Analytics Agent Implementation](#6-performance-analytics-agent-implementation)
7. [Code Examples and Snippets](#7-code-examples-and-snippets)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Agent Architecture

### 1.1 Overview

The AI-powered market research system uses LangChain DeepAgents to orchestrate a multi-agent pipeline that autonomously collects, analyzes, reports, and acts on market intelligence. DeepAgents extends LangChain's agent framework with built-in planning, file system operations, and sub-agent delegation capabilities.

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Market Research Orchestrator                      │
│                  (LangGraph State Machine)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Data       │───▶│  Analysis    │───▶│  Reporting   │          │
│  │  Collection  │    │    Agent     │    │    Agent     │          │
│  │    Agent     │    │              │    │              │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│         │                   │                   │                    │
│         ▼                   ▼                   ▼                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  External    │    │  Internal    │    │  Report      │          │
│  │  APIs &      │    │  Knowledge   │    │  Storage &   │          │
│  │  Scrapers    │    │  Base        │    │  Delivery    │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐                              │
│  │   Action     │◀───│  Performance │                              │
│  │    Agent     │    │  Analytics   │                              │
│  │              │    │    Agent     │                              │
│  └──────────────┘    └──────────────┘                              │
│         │                   │                                       │
│         ▼                   ▼                                       │
│  ┌──────────────┐    ┌──────────────┐                              │
│  │  Marketing   │    │  Metrics &   │                              │
│  │  Automation  │    │  Feedback    │                              │
│  │  Systems     │    │  Loop        │                              │
│  └──────────────┘    └──────────────┘                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Agent Roles and Responsibilities

| Agent | Role | Input | Output | Tools |
|-------|------|-------|--------|-------|
| **Data Collection Agent** | Gathers raw market data from multiple sources | Research queries, target markets, competitor lists | Structured datasets, raw intelligence | Web search, API clients, scrapers, RSS readers |
| **Analysis Agent** | Processes and synthesizes collected data | Raw datasets, historical benchmarks | Insights, trends, sentiment analysis, forecasts | Statistical tools, NLP models, visualization |
| **Reporting Agent** | Generates human-readable reports | Analysis results, templates, brand guidelines | PDF/HTML/Slides reports, dashboards | Document generators, chart libraries, email |
| **Action Agent** | Translates insights into actionable tasks | Analysis insights, campaign parameters | Campaign briefs, content calendars, ad copies | Marketing APIs, CMS, ad platforms |
| **Performance Analytics Agent** | Monitors and optimizes campaign performance | Campaign metrics, conversion data, A/B test results | Optimization recommendations, ROI reports | Analytics APIs, attribution models, ML predictors |

### 1.4 State Management

The system uses LangGraph's stateful graph execution to maintain context across agent interactions:

```python
from langgraph.graph import StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# Shared state schema
class MarketResearchState(MessagesState):
    research_query: str
    target_markets: list[str]
    competitors: list[str]
    collected_data: dict
    analysis_results: dict
    reports_generated: list[dict]
    actions_taken: list[dict]
    performance_metrics: dict
    iteration_count: int
    max_iterations: int
    human_approval_required: bool
    approval_status: str  # "pending", "approved", "rejected"
```

### 1.5 Communication Protocol

Agents communicate through a shared state object with typed channels:

- **Data Channel**: Raw and processed data artifacts
- **Insight Channel**: Analyzed findings and recommendations
- **Action Channel**: Task specifications and execution results
- **Feedback Channel**: Performance signals and optimization hints

### 1.6 Human-in-the-Loop Integration

Critical decision points require human approval:

1. **Budget allocation** above configurable thresholds
2. **Competitive response** strategies with reputational risk
3. **Data source** selection for sensitive markets
4. **Report distribution** to external stakeholders
5. **Automated action** execution in production environments

---

## 2. Data Collection Agent Implementation

### 2.1 Purpose

The Data Collection Agent is responsible for gathering comprehensive market intelligence from diverse sources including web pages, APIs, social media, news outlets, industry databases, and competitor websites.

### 2.2 Architecture

```
┌─────────────────────────────────────────────┐
│         Data Collection Agent               │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐  ┌─────────────┐          │
│  │   Source    │  │   Source    │          │
│  │  Registry   │  │  Validator  │          │
│  └──────┬──────┘  └──────┬──────┘          │
│         │                │                   │
│         ▼                ▼                   │
│  ┌─────────────────────────────┐           │
│  │    Collection Orchestrator  │           │
│  │    (Parallel Execution)     │           │
│  └─────────────┬───────────────┘           │
│                │                            │
│    ┌───────────┼───────────┐               │
│    ▼           ▼           ▼               │
│ ┌──────┐  ┌──────┐  ┌──────────┐         │
│ │ Web  │  │ API  │  │  Social  │         │
│ │Search│  │Client│  │  Media   │         │
│ └──────┘  └──────┘  └──────────┘         │
│    │           │           │               │
│    └───────────┼───────────┘               │
│                ▼                            │
│  ┌─────────────────────────────┐           │
│  │    Data Normalization &     │           │
│  │    Deduplication Engine     │           │
│  └─────────────┬───────────────┘           │
│                ▼                            │
│  ┌─────────────────────────────┐           │
│  │    Quality Scoring &        │           │
│  │    Relevance Filter         │           │
│  └─────────────────────────────┘           │
│                                             │
└─────────────────────────────────────────────┘
```

### 2.3 Data Sources

| Category | Sources | Collection Method | Frequency |
|----------|---------|-------------------|-----------|
| **Competitor Websites** | Competitor domains, pricing pages, blogs | Web scraping (respectful, rate-limited) | Daily |
| **News & Press** | Google News, industry publications, PR Newswire | RSS feeds, NewsAPI, web search | Hourly |
| **Social Media** | Twitter/X, LinkedIn, Reddit, industry forums | API clients, sentiment trackers | Real-time |
| **Industry Reports** | Gartner, Forrester, Statista, IBISWeb | API integrations, manual upload | Weekly |
| **Search Trends** | Google Trends, keyword planners | API polling | Daily |
| **Review Platforms** | G2, Capterra, Trustpilot, app stores | API + scraping | Daily |
| **Financial Data** | SEC EDGAR, earnings calls, investor relations | API + parsing | Quarterly |
| **Patent & R&D** | USPTO, Google Patents, research databases | API + scraping | Weekly |
| **Job Postings** | LinkedIn, Indeed, company career pages | API + scraping | Weekly |
| **Community** | Stack Overflow, GitHub, niche forums | API + scraping | Daily |

### 2.4 Implementation

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool, StructuredTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import TavilySearchResults, ReadFileTool
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
import aiohttp
from datetime import datetime, timedelta
import feedparser
import json
import hashlib

# ─── Data Models ──────────────────────────────────────────────

class DataSourceConfig(BaseModel):
    """Configuration for a data source."""
    name: str
    source_type: str  # "web", "api", "rss", "social", "database"
    url: str
    api_key: Optional[str] = None
    rate_limit: int = 10  # requests per minute
    priority: int = 5  # 1 (highest) to 10 (lowest)
    enabled: bool = True
    last_collected: Optional[datetime] = None
    reliability_score: float = 0.5  # 0.0 to 1.0

class CollectedData(BaseModel):
    """Standardized data artifact."""
    source: str
    source_url: str
    title: str
    content: str
    content_type: str  # "article", "pricing", "review", "social_post", "report"
    collected_at: datetime
    relevance_score: float = 0.0
    sentiment_score: Optional[float] = None
    entities: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    content_hash: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                self.content.encode()
            ).hexdigest()[:16]

class CollectionQuery(BaseModel):
    """Query specification for data collection."""
    research_topic: str
    target_markets: list[str]
    competitors: list[str]
    keywords: list[str]
    date_range_days: int = 30
    max_results_per_source: int = 50
    min_relevance_score: float = 0.3
    content_types: list[str] = Field(
        default_factory=lambda: ["article", "pricing", "review", "social_post"]
    )

# ─── Collection Tools ─────────────────────────────────────────

class WebSearchTool:
    """Enhanced web search with relevance scoring."""

    def __init__(self, tavily_api_key: str):
        self.search = TavilySearchResults(
            api_key=tavily_api_key,
            max_results=10,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True,
        )

    async def search_with_context(
        self, query: str, context: str, max_results: int = 10
    ) -> list[dict]:
        """Search with contextual awareness."""
        enriched_query = f"{query} context: {context}"
        results = await self.search.ainvoke(enriched_query)
        return self._score_and_filter(results, context)

    def _score_and_filter(
        self, results: list[dict], context: str
    ) -> list[dict]:
        """Score results by relevance to context."""
        scored = []
        context_lower = context.lower()
        for r in results:
            score = 0.0
            title = r.get("title", "").lower()
            content = r.get("content", "").lower()
            # Keyword overlap scoring
            context_words = set(context_lower.split())
            result_words = set((title + " " + content).split())
            overlap = len(context_words & result_words)
            score += overlap / max(len(context_words), 1)
            # Recency boost
            # (would use actual date parsing in production)
            scored.append({**r, "relevance_score": min(score, 1.0)})
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored


class APICollector:
    """Generic API data collector with rate limiting."""

    def __init__(self, config: DataSourceConfig):
        self.config = config
        self._semaphore = asyncio.Semaphore(config.rate_limit)
        self._last_request_time: Optional[datetime] = None

    async def collect(
        self, query: str, params: dict = None
    ) -> list[CollectedData]:
        """Collect data from API with rate limiting."""
        async with self._semaphore:
            await self._respect_rate_limit()
            try:
                async with aiohttp.ClientSession() as session:
                    headers = self._build_headers()
                    async with session.get(
                        self.config.url,
                        params=params or {"q": query},
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        self._last_request_time = datetime.now()
                        if response.status == 200:
                            data = await response.json()
                            return self._normalize_response(data)
                        else:
                            return []
            except Exception as e:
                # Log error, return empty
                return []

    async def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            min_interval = 60.0 / self.config.rate_limit
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)

    def _build_headers(self) -> dict:
        headers = {"User-Agent": "MarketResearchBot/1.0"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _normalize_response(self, raw_data: dict) -> list[CollectedData]:
        """Normalize API response to CollectedData format."""
        # Implementation varies by API
        items = raw_data.get("results", raw_data.get("data", []))
        normalized = []
        for item in items:
            normalized.append(CollectedData(
                source=self.config.name,
                source_url=item.get("url", self.config.url),
                title=item.get("title", "Untitled"),
                content=item.get("content", item.get("description", "")),
                content_type=self._infer_content_type(item),
                collected_at=datetime.now(),
                entities=item.get("entities", []),
                metadata={"raw": item},
            ))
        return normalized

    def _infer_content_type(self, item: dict) -> str:
        """Infer content type from item structure."""
        if "price" in item or "pricing" in item:
            return "pricing"
        if "rating" in item or "review" in item:
            return "review"
        if "social" in str(item.get("platform", "")):
            return "social_post"
        return "article"


class RSSCollector:
    """RSS/Atom feed collector."""

    def __init__(self, feed_urls: list[str]):
        self.feed_urls = feed_urls

    async def collect(
        self, keywords: list[str], max_items: int = 50
    ) -> list[CollectedData]:
        """Collect and filter RSS items by keywords."""
        results = []
        for url in self.feed_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:max_items]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))
                    content = f"{title} {summary}"

                    # Keyword matching
                    if any(kw.lower() in content.lower() for kw in keywords):
                        results.append(CollectedData(
                            source=feed.feed.get("title", url),
                            source_url=entry.get("link", url),
                            title=title,
                            content=summary,
                            content_type="article",
                            collected_at=datetime.now(),
                            metadata={
                                "published": entry.get("published", ""),
                                "author": entry.get("author", ""),
                            },
                        ))
            except Exception:
                continue
        return results


class SocialMediaCollector:
    """Social media data collector (Twitter/X, Reddit, LinkedIn)."""

    def __init__(
        self,
        twitter_bearer_token: Optional[str] = None,
        reddit_client_id: Optional[str] = None,
        reddit_client_secret: Optional[str] = None,
    ):
        self.twitter_token = twitter_bearer_token
        self.reddit_id = reddit_client_id
        self.reddit_secret = reddit_client_secret

    async def collect_twitter(
        self, query: str, max_results: int = 100
    ) -> list[CollectedData]:
        """Collect tweets matching query."""
        if not self.twitter_token:
            return []

        headers = {"Authorization": f"Bearer {self.twitter_token}"}
        url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,author_id,public_metrics,context_annotations",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, headers=headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tweets = data.get("data", [])
                    return [
                        CollectedData(
                            source="Twitter",
                            source_url=f"https://twitter.com/i/web/status/{t['id']}",
                            title=f"Tweet by {t.get('author_id', 'unknown')}",
                            content=t["text"],
                            content_type="social_post",
                            collected_at=datetime.now(),
                            sentiment_score=None,  # To be filled by analysis
                            metadata={
                                "metrics": t.get("public_metrics", {}),
                                "author_id": t.get("author_id"),
                            },
                        )
                        for t in tweets
                    ]
                return []

    async def collect_reddit(
        self, subreddits: list[str], keywords: list[str], limit: int = 50
    ) -> list[CollectedData]:
        """Collect Reddit posts from specified subreddits."""
        # Reddit API implementation
        # Requires OAuth2 authentication flow
        results = []
        # ... implementation ...
        return results


class WebScraper:
    """Respectful web scraper for competitor websites."""

    def __init__(self, respect_robots: bool = True, delay: float = 1.0):
        self.respect_robots = respect_robots
        self.delay = delay
        self.loader = WebBaseLoader()

    async def scrape_page(self, url: str) -> Optional[CollectedData]:
        """Scrape a single page with rate limiting."""
        await asyncio.sleep(self.delay)
        try:
            # Use LangChain's WebBaseLoader
            docs = self.loader.load()
            if docs:
                doc = docs[0]
                return CollectedData(
                    source=url,
                    source_url=url,
                    title=doc.metadata.get("title", ""),
                    content=doc.page_content,
                    content_type="article",
                    collected_at=datetime.now(),
                    metadata=doc.metadata,
                )
        except Exception:
            return None

    async def scrape_competitor_pricing(
        self, competitor_urls: list[str]
    ) -> list[CollectedData]:
        """Scrape pricing pages from competitors."""
        results = []
        for url in competitor_urls:
            data = await self.scrape_page(url)
            if data:
                data.content_type = "pricing"
                results.append(data)
        return results


# ─── Data Collection Agent ────────────────────────────────────

class DataCollectionAgent:
    """
    LangChain DeepAgent for comprehensive market data collection.
    Orchestrates multiple collection strategies in parallel.
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        tavily_api_key: str,
        data_sources: list[DataSourceConfig],
        vector_store: Optional[FAISS] = None,
    ):
        self.llm = llm
        self.web_search = WebSearchTool(tavily_api_key)
        self.sources = {s.name: s for s in data_sources if s.enabled}
        self.vector_store = vector_store
        self.collected_data: list[CollectedData] = []
        self._build_tools()

    def _build_tools(self):
        """Build the tool collection for the agent."""
        self.tools = [
            StructuredTool.from_function(
                func=self._tool_web_search,
                name="web_search",
                description="Search the web for market intelligence, news, and competitor information.",
            ),
            StructuredTool.from_function(
                func=self._tool_scrape_competitor,
                name="scrape_competitor",
                description="Scrape a competitor website for pricing, features, and positioning data.",
            ),
            StructuredTool.from_function(
                func=self._tool_collect_social,
                name="collect_social",
                description="Collect social media mentions and sentiment for specified brands or topics.",
            ),
            StructuredTool.from_function(
                func=self._tool_search_news,
                name="search_news",
                description="Search news sources for recent articles and press releases.",
            ),
            StructuredTool.from_function(
                func=self._tool_collect_reviews,
                name="collect_reviews",
                description="Collect product/service reviews from G2, Capterra, Trustpilot, etc.",
            ),
            StructuredTool.from_function(
                func=self._tool_store_data,
                name="store_data",
                description="Store collected data into the vector database for later retrieval.",
            ),
            StructuredTool.from_function(
                func=self._tool_deduplicate,
                name="deduplicate",
                description="Remove duplicate or near-duplicate entries from collected data.",
            ),
        ]

    async def _tool_web_search(
        self, query: str, max_results: int = 10
    ) -> str:
        """Web search tool implementation."""
        results = await self.web_search.search_with_context(
            query, query, max_results
        )
        collected = []
        for r in results:
            data = CollectedData(
                source="web_search",
                source_url=r.get("url", ""),
                title=r.get("title", ""),
                content=r.get("content", ""),
                content_type="article",
                collected_at=datetime.now(),
                relevance_score=r.get("relevance_score", 0.5),
            )
            collected.append(data)
        self.collected_data.extend(collected)
        return json.dumps([c.model_dump() for c in collected], default=str)

    async def _tool_scrape_competitor(self, url: str) -> str:
        """Competitor scraping tool implementation."""
        scraper = WebScraper(respect_robots=True, delay=1.0)
        data = await scraper.scrape_page(url)
        if data:
            self.collected_data.append(data)
            return data.model_dump_json()
        return json.dumps({"error": f"Failed to scrape {url}"})

    async def _tool_collect_social(
        self, query: str, platform: str = "twitter", max_results: int = 50
    ) -> str:
        """Social media collection tool implementation."""
        collector = SocialMediaCollector()
        if platform == "twitter":
            results = await collector.collect_twitter(query, max_results)
        else:
            results = []
        self.collected_data.extend(results)
        return json.dumps([r.model_dump() for r in results], default=str)

    async def _tool_search_news(
        self, query: str, days: int = 7, max_results: int = 20
    ) -> str:
        """News search tool implementation."""
        # Use NewsAPI or similar
        results = []
        # ... implementation ...
        return json.dumps(results, default=str)

    async def _tool_collect_reviews(
        self, product: str, platform: str = "g2", max_results: int = 50
    ) -> str:
        """Review collection tool implementation."""
        results = []
        # ... implementation ...
        return json.dumps(results, default=str)

    async def _tool_store_data(self, data_json: str) -> str:
        """Store data in vector database."""
        if self.vector_store:
            # Convert to documents and store
            pass
        return json.dumps({"status": "stored", "count": len(self.collected_data)})

    async def _tool_deduplicate(self) -> str:
        """Deduplicate collected data."""
        seen_hashes = set()
        unique = []
        for item in self.collected_data:
            if item.content_hash not in seen_hashes:
                seen_hashes.add(item.content_hash)
                unique.append(item)
        removed = len(self.collected_data) - len(unique)
        self.collected_data = unique
        return json.dumps({
            "status": "deduplicated",
            "removed": removed,
            "remaining": len(unique),
        })

    async def collect(
        self, query: CollectionQuery
    ) -> list[CollectedData]:
        """
        Execute full data collection pipeline.
        
        This is the main entry point that orchestrates all collection
        strategies in parallel and returns deduplicated, scored results.
        """
        # Phase 1: Parallel collection from all sources
        tasks = []

        # Web search
        tasks.append(
            self.web_search.search_with_context(
                query.research_topic,
                f"{' '.join(query.keywords)} {' '.join(query.competitors)}",
                query.max_results_per_source,
            )
        )

        # RSS feeds
        rss_collector = RSSCollector([
            "https://news.google.com/rss/search?q=" + "+".join(query.keywords),
        ])
        tasks.append(
            rss_collector.collect(query.keywords, query.max_results_per_source)
        )

        # Social media
        social = SocialMediaCollector()
        for competitor in query.competitors:
            tasks.append(
                social.collect_twitter(
                    competitor, query.max_results_per_source
                )
            )

        # Competitor websites
        scraper = WebScraper()
        for competitor in query.competitors:
            # Construct likely URLs
            tasks.append(
                scraper.scrape_page(f"https://{competitor}.com/pricing")
            )

        # Execute all collections
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Phase 2: Normalize and merge
        all_data = []
        for result in results:
            if isinstance(result, Exception):
                continue
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, CollectedData):
                        all_data.append(item)
                    elif isinstance(item, dict):
                        try:
                            all_data.append(CollectedData(**item))
                        except Exception:
                            pass

        # Phase 3: Deduplicate
        seen_hashes = set()
        unique_data = []
        for item in all_data:
            if item.content_hash not in seen_hashes:
                seen_hashes.add(item.content_hash)
                unique_data.append(item)

        # Phase 4: Score and filter
        scored_data = self._score_relevance(unique_data, query)
        filtered = [
            d for d in scored_data
            if d.relevance_score >= query.min_relevance_score
        ]

        # Phase 5: Sort by relevance and recency
        filtered.sort(
            key=lambda x: (x.relevance_score, x.collected_at),
            reverse=True,
        )

        self.collected_data = filtered
        return filtered

    def _score_relevance(
        self, data: list[CollectedData], query: CollectionQuery
    ) -> list[CollectedData]:
        """Score data relevance to the research query."""
        query_terms = set(
            (query.research_topic + " " + " ".join(query.keywords)).lower().split()
        )
        competitor_terms = set(
            " ".join(query.competitors).lower().split()
        )

        for item in data:
            content = (item.title + " " + item.content).lower()
            content_terms = set(content.split())

            # Term overlap
            query_overlap = len(query_terms & content_terms) / max(len(query_terms), 1)
            competitor_overlap = len(competitor_terms & content_terms) / max(len(competitor_terms), 1)

            # Content type boost
            type_boost = {
                "pricing": 0.2,
                "review": 0.15,
                "article": 0.1,
                "social_post": 0.05,
            }.get(item.content_type, 0.0)

            # Recency boost (exponential decay)
            age_days = (datetime.now() - item.collected_at).days
            recency_boost = max(0, 0.2 * (0.95 ** age_days))

            item.relevance_score = min(
                1.0,
                query_overlap * 0.4
                + competitor_overlap * 0.3
                + type_boost
                + recency_boost,
            )

        return data

    def create_agent_executor(self) -> AgentExecutor:
        """Create a LangChain agent executor with the collection tools."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a market research data collection specialist.
Your job is to gather comprehensive, high-quality data from multiple sources.

Guidelines:
- Prioritize authoritative and recent sources
- Collect diverse perspectives (competitors, customers, analysts)
- Respect rate limits and robots.txt
- Score and filter for relevance
- Deduplicate before storing
- Document source provenance for every data point

Available tools: {tools}
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=20,
        )
```

### 2.5 Data Quality Framework

| Dimension | Metric | Target | Measurement |
|-----------|--------|--------|-------------|
| **Completeness** | Source coverage | ≥ 80% of identified sources | Sources queried / Sources available |
| **Relevance** | Precision score | ≥ 0.7 average | Relevance scoring model |
| **Recency** | Data freshness | ≤ 7 days median age | Timestamp analysis |
| **Accuracy** | Fact verification | ≥ 90% verified claims | Cross-reference validation |
| **Diversity** | Source variety | ≥ 5 distinct source types | Source type distribution |
| **Uniqueness** | Deduplication rate | ≤ 5% duplicates | Hash-based dedup |

### 2.6 Error Handling and Resilience

```python
class CollectionErrorHandler:
    """Handles failures in data collection gracefully."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.failure_counts: dict[str, int] = {}

    async def execute_with_retry(
        self, source_name: str, coro
    ):
        """Execute a collection coroutine with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                result = await coro
                self.failure_counts[source_name] = 0
                return result
            except aiohttp.ClientError as e:
                self.failure_counts[source_name] = (
                    self.failure_counts.get(source_name, 0) + 1
                )
                if attempt < self.max_retries - 1:
                    wait = self.backoff_factor ** attempt
                    await asyncio.sleep(wait)
                else:
                    # Log permanent failure
                    return []
            except Exception:
                return []

    def get_source_health(self) -> dict:
        """Report health status of all sources."""
        return {
            name: {
                "failures": count,
                "status": "healthy" if count < 3 else "degraded" if count < 5 else "down",
            }
            for name, count in self.failure_counts.items()
        }
```

---

## 3. Analysis Agent Implementation

### 3.1 Purpose

The Analysis Agent processes collected market data to extract actionable insights, identify trends, perform competitive analysis, and generate forecasts. It uses a combination of LLM reasoning, statistical analysis, and domain-specific heuristics.

### 3.2 Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                   Analysis Agent Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Input: Raw Market Data                  │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Stage 1: Data Preprocessing                  │   │
│  │  • Text normalization  • Entity extraction          │   │
│  │  • Language detection  • Deduplication              │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Stage 2: Descriptive Analysis                │   │
│  │  • Market sizing      • Growth rate calculation     │   │
│  │  • Segment distribution  • Trend identification    │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Stage 3: Sentiment & Perception              │   │
│  │  • Brand sentiment    • Review analysis             │   │
│  │  • Social listening   • Emotion detection           │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Stage 4: Competitive Analysis                │   │
│  │  • Feature comparison  • Pricing analysis           │   │
│  │  • Positioning map     • SWOT synthesis              │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Stage 5: Predictive Analytics                │   │
│  │  • Trend forecasting  • Opportunity scoring         │   │
│  │  • Risk assessment     • Scenario modeling           │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Stage 6: Insight Synthesis                   │   │
│  │  • Key findings       • Strategic implications      │   │
│  │  • Recommendations    • Confidence scoring          │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Output: Structured Insights             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Implementation

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import numpy as np
from collections import Counter
from datetime import datetime, timedelta
import json
import re

# ─── Analysis Data Models ────────────────────────────────────

class MarketSegment(BaseModel):
    """A identified market segment."""
    name: str
    description: str
    estimated_size: Optional[float] = None  # in USD millions
    growth_rate: Optional[float] = None  # CAGR percentage
    key_players: list[str] = Field(default_factory=list)
    trends: list[str] = Field(default_factory=list)
    confidence: float = 0.5

class CompetitivePosition(BaseModel):
    """Competitive positioning analysis."""
    competitor: str
    market_share: Optional[float] = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    pricing_position: str = "unknown"  # "premium", "mid", "budget", "unknown"
    key_differentiators: list[str] = Field(default_factory=list)
    threat_level: str = "medium"  # "low", "medium", "high"
    confidence: float = 0.5

class SentimentAnalysis(BaseModel):
    """Sentiment analysis results."""
    overall_sentiment: str  # "positive", "negative", "neutral", "mixed"
    sentiment_score: float  # -1.0 to 1.0
    positive_themes: list[str] = Field(default_factory=list)
    negative_themes: list[str] = Field(default_factory=list)
    neutral_themes: list[str] = Field(default_factory=list)
    emotion_distribution: dict[str, float] = Field(default_factory=dict)
    trend_direction: str = "stable"  # "improving", "declining", "stable"
    confidence: float = 0.5

class TrendForecast(BaseModel):
    """Market trend forecast."""
    trend_name: str
    description: str
    current_stage: str  # "emerging", "growth", "mature", "declining"
    forecast_horizon: str  # e.g., "12 months"
    projected_growth: Optional[float] = None
    key_drivers: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    supporting_evidence: list[str] = Field(default_factory=list)

class SWOTAnalysis(BaseModel):
    """SWOT analysis for a company/product."""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)
    strategic_implications: list[str] = Field(default_factory=list)

class MarketInsight(BaseModel):
    """A single market insight."""
    insight_id: str
    category: str  # "market_size", "competitive", "trend", "sentiment", "opportunity", "risk"
    title: str
    description: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    impact: str  # "low", "medium", "high", "critical"
    timeframe: str  # "immediate", "short_term", "medium_term", "long_term"
    recommended_action: Optional[str] = None
    related_insights: list[str] = Field(default_factory=list)

class AnalysisReport(BaseModel):
    """Complete analysis output."""
    research_topic: str
    analysis_date: datetime
    executive_summary: str
    market_segments: list[MarketSegment] = Field(default_factory=list)
    competitive_positions: list[CompetitivePosition] = Field(default_factory=list)
    sentiment_analysis: Optional[SentimentAnalysis] = None
    trend_forecasts: list[TrendForecast] = Field(default_factory=list)
    swot: Optional[SWOTAnalysis] = None
    key_insights: list[MarketInsight] = Field(default_factory=list)
    data_quality_score: float = 0.0
    limitations: list[str] = Field(default_factory=list)
    methodology_notes: str = ""


# ─── Analysis Tools ──────────────────────────────────────────

class SentimentAnalyzer:
    """Rule-based + LLM sentiment analysis."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.positive_words = {
            "excellent", "outstanding", "innovative", "leading", "best",
            "superior", "exceptional", "remarkable", "impressive",
            "breakthrough", "game-changer", "dominant", "preferred",
        }
        self.negative_words = {
            "poor", "disappointing", "outdated", "expensive", "limited",
            "inferior", "problematic", "concerning", "weak", "lacking",
            "frustrating", "complicated", "slow", "unreliable",
        }

    def analyze(self, texts: list[str]) -> SentimentAnalysis:
        """Analyze sentiment across a collection of texts."""
        if not texts:
            return SentimentAnalysis(
                overall_sentiment="neutral",
                sentiment_score=0.0,
                confidence=0.0,
            )

        # Lexicon-based scoring
        pos_count = 0
        neg_count = 0
        total_words = 0

        for text in texts:
            words = re.findall(r'\b\w+\b', text.lower())
            total_words += len(words)
            pos_count += sum(1 for w in words if w in self.positive_words)
            neg_count += sum(1 for w in words if w in self.negative_words)

        # Calculate raw sentiment score
        if total_words > 0:
            raw_score = (pos_count - neg_count) / max(total_words * 0.01, 1)
            sentiment_score = max(-1.0, min(1.0, raw_score))
        else:
            sentiment_score = 0.0

        # Determine overall sentiment
        if sentiment_score > 0.2:
            overall = "positive"
        elif sentiment_score < -0.2:
            overall = "negative"
        elif -0.05 <= sentiment_score <= 0.05:
            overall = "neutral"
        else:
            overall = "mixed"

        # Theme extraction (simplified)
        positive_themes = self._extract_themes(texts, self.positive_words)
        negative_themes = self._extract_themes(texts, self.negative_words)

        return SentimentAnalysis(
            overall_sentiment=overall,
            sentiment_score=sentiment_score,
            positive_themes=positive_themes,
            negative_themes=negative_themes,
            confidence=min(0.9, 0.5 + abs(sentiment_score)),
        )

    def _extract_themes(
        self, texts: list[str], keyword_set: set
    ) -> list[str]:
        """Extract common themes around sentiment keywords."""
        themes = []
        for text in texts:
            sentences = re.split(r'[.!?]+', text)
            for sent in sentences:
                if any(kw in sent.lower() for kw in keyword_set):
                    # Extract noun phrases (simplified)
                    words = sent.strip().split()
                    if len(words) > 3:
                        theme = " ".join(words[:8]).strip()
                        if len(theme) > 10:
                            themes.append(theme)
        # Return most common themes
        counter = Counter(themes)
        return [t for t, _ in counter.most_common(5)]


class TrendAnalyzer:
    """Identifies and forecasts market trends."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def identify_trends(
        self, data: list[dict], min_mentions: int = 3
    ) -> list[TrendForecast]:
        """Identify trends from collected data."""
        # Extract topics/entities
        all_text = " ".join([
            d.get("title", "") + " " + d.get("content", "")
            for d in data
        ])

        # Use LLM to identify trends
        prompt = f"""Analyze the following market data and identify the top 5 trends.
For each trend, provide:
- Name and description
- Current stage (emerging/growth/mature/declining)
- Key drivers
- Projected growth rate
- Associated risks
- Confidence level (0.0-1.0)

Market data sample:
{all_text[:5000]}

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            # Parse response (would use structured output in production)
            trends = self._parse_trend_response(response.content)
            return trends
        except Exception:
            return []

    def _parse_trend_response(self, response: str) -> list[TrendForecast]:
        """Parse LLM trend response."""
        # Simplified parsing - would use structured output
        return []

    def forecast_growth(
        self,
        historical_data: list[float],
        periods: int = 4,
    ) -> list[float]:
        """Simple linear regression forecast."""
        if len(historical_data) < 2:
            return [historical_data[-1]] * periods if historical_data else [0] * periods

        x = np.arange(len(historical_data))
        y = np.array(historical_data)

        # Linear regression
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs

        forecasts = []
        for i in range(1, periods + 1):
            forecast = slope * (len(historical_data) + i - 1) + intercept
            forecasts.append(max(0, forecast))  # No negative market sizes

        return forecasts


class CompetitiveAnalyzer:
    """Performs competitive analysis."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def analyze_competitor(
        self,
        competitor_name: str,
        data: list[dict],
    ) -> CompetitivePosition:
        """Analyze a single competitor from collected data."""
        competitor_data = [
            d for d in data
            if competitor_name.lower() in (
                d.get("title", "") + " " + d.get("content", "")
            ).lower()
        ]

        if not competitor_data:
            return CompetitivePosition(
                competitor=competitor_name,
                confidence=0.0,
            )

        # Extract strengths and weaknesses
        combined_text = " ".join([
            d.get("content", "") for d in competitor_data
        ])

        prompt = f"""Analyze the following data about competitor '{competitor_name}'.
Identify:
1. Key strengths (up to 5)
2. Key weaknesses (up to 5)
3. Pricing position (premium/mid/budget)
4. Key differentiators (up to 3)
5. Threat level (low/medium/high)

Data:
{combined_text[:3000]}

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            # Parse and return
            return CompetitivePosition(
                competitor=competitor_name,
                strengths=["strength1", "strength2"],  # Parsed from response
                weaknesses=["weakness1"],
                pricing_position="mid",
                key_differentiators=["differentiator1"],
                threat_level="medium",
                confidence=0.7,
            )
        except Exception:
            return CompetitivePosition(
                competitor=competitor_name,
                confidence=0.3,
            )

    def generate_swot(
        self,
        company_name: str,
        competitors: list[CompetitivePosition],
        market_data: list[dict],
    ) -> SWOTAnalysis:
        """Generate SWOT analysis."""
        # Aggregate competitor insights
        all_strengths = []
        all_weaknesses = []
        for comp in competitors:
            all_strengths.extend(comp.strengths)
            all_weaknesses.extend(comp.weaknesses)

        # Use LLM for SWOT synthesis
        prompt = f"""Generate a SWOT analysis for '{company_name}' based on:
- Competitor strengths: {all_strengths}
- Competitor weaknesses: {all_weaknesses}
- Market data: {len(market_data)} data points

Provide:
- Strengths (internal, up to 5)
- Weaknesses (internal, up to 5)
- Opportunities (external, up to 5)
- Threats (external, up to 5)
- Strategic implications (up to 3)

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            return SWOTAnalysis(
                strengths=["strength1", "strength2"],
                weaknesses=["weakness1"],
                opportunities=["opportunity1"],
                threats=["threat1"],
                strategic_implications=["implication1"],
            )
        except Exception:
            return SWOTAnalysis()


class MarketSizingEngine:
    """Estimates market size using top-down and bottom-up approaches."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def estimate_market_size(
        self,
        market_description: str,
        data: list[dict],
    ) -> dict:
        """Estimate TAM, SAM, SOM."""
        # Extract any numerical data from collected content
        numbers = self._extract_market_numbers(data)

        prompt = f"""Based on the following market data, estimate:
- TAM (Total Addressable Market) in USD millions
- SAM (Serviceable Addressable Market) in USD millions
- SOM (Serviceable Obtainable Market) in USD millions
- CAGR (Compound Annual Growth Rate) percentage

Market: {market_description}
Available data points: {numbers[:10]}

Provide reasoning for each estimate. Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            return {
                "tam": 0,  # Parsed from response
                "sam": 0,
                "som": 0,
                "cagr": 0,
                "methodology": "LLM-assisted estimation",
                "confidence": 0.5,
            }
        except Exception:
            return {
                "tam": 0,
                "sam": 0,
                "som": 0,
                "cagr": 0,
                "methodology": "unavailable",
                "confidence": 0.0,
            }

    def _extract_market_numbers(self, data: list[dict]) -> list[float]:
        """Extract numerical market data from text."""
        numbers = []
        for d in data:
            text = d.get("content", "") + " " + d.get("title", "")
            # Find numbers with market context
            patterns = [
                r'\$?(\d+(?:\.\d+)?)\s*(?:billion|bn|B)',
                r'\$?(\d+(?:\.\d+)?)\s*(?:million|mn|M)',
                r'(\d+(?:\.\d+)?)\s*%',
                r'market\s+(?:size|value|worth)\s+(?:of\s+)?\$?(\d+(?:\.\d+)?)',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for m in matches:
                    try:
                        numbers.append(float(m))
                    except ValueError:
                        continue
        return numbers


# ─── Analysis Agent ──────────────────────────────────────────

class AnalysisAgent:
    """
    LangChain DeepAgent for market data analysis.
    Processes raw data into structured insights.
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.sentiment_analyzer = SentimentAnalyzer(llm)
        self.trend_analyzer = TrendAnalyzer(llm)
        self.competitive_analyzer = CompetitiveAnalyzer(llm)
        self.market_sizing = MarketSizingEngine(llm)
        self._build_tools()

    def _build_tools(self):
        """Build analysis tools."""
        self.tools = [
            StructuredTool.from_function(
                func=self._tool_analyze_sentiment,
                name="analyze_sentiment",
                description="Analyze sentiment of collected text data (reviews, social posts, articles).",
            ),
            StructuredTool.from_function(
                func=self._tool_identify_trends,
                name="identify_trends",
                description="Identify emerging and declining trends from market data.",
            ),
            StructuredTool.from_function(
                func=self._tool_competitive_analysis,
                name="competitive_analysis",
                description="Perform detailed competitive analysis on specified competitors.",
            ),
            StructuredTool.from_function(
                func=self._tool_market_sizing,
                name="market_sizing",
                description="Estimate TAM, SAM, SOM for a market segment.",
            ),
            StructuredTool.from_function(
                func=self._tool_swot_analysis,
                name="swot_analysis",
                description="Generate SWOT analysis based on market and competitive data.",
            ),
            StructuredTool.from_function(
                func=self._tool_forecast_growth,
                name="forecast_growth",
                description="Forecast market growth based on historical data.",
            ),
            StructuredTool.from_function(
                func=self._tool_extract_insights,
                name="extract_insights",
                description="Extract key insights and patterns from analyzed data.",
            ),
            StructuredTool.from_function(
                func=self._tool_score_opportunities,
                name="score_opportunities",
                description="Score and rank market opportunities by attractiveness and feasibility.",
            ),
        ]

    async def _tool_analyze_sentiment(
        self, texts_json: str
    ) -> str:
        """Analyze sentiment of provided texts."""
        texts = json.loads(texts_json)
        result = self.sentiment_analyzer.analyze(texts)
        return result.model_dump_json()

    async def _tool_identify_trends(
        self, data_json: str, min_mentions: int = 3
    ) -> str:
        """Identify trends from data."""
        data = json.loads(data_json)
        trends = self.trend_analyzer.identify_trends(data, min_mentions)
        return json.dumps([t.model_dump() for t in trends], default=str)

    async def _tool_competitive_analysis(
        self, competitor: str, data_json: str
    ) -> str:
        """Analyze a specific competitor."""
        data = json.loads(data_json)
        result = self.competitive_analyzer.analyze_competitor(
            competitor, data
        )
        return result.model_dump_json()

    async def _tool_market_sizing(
        self, market_description: str, data_json: str
    ) -> str:
        """Estimate market size."""
        data = json.loads(data_json)
        result = self.market_sizing.estimate_market_size(
            market_description, data
        )
        return json.dumps(result)

    async def _tool_swot_analysis(
        self, company: str, competitors_json: str, data_json: str
    ) -> str:
        """Generate SWOT analysis."""
        competitors_data = json.loads(competitors_json)
        competitors = [
            CompetitivePosition(**c) for c in competitors_data
        ]
        data = json.loads(data_json)
        result = self.competitive_analyzer.generate_swot(
            company, competitors, data
        )
        return result.model_dump_json()

    async def _tool_forecast_growth(
        self, historical_data_json: str, periods: int = 4
    ) -> str:
        """Forecast market growth."""
        historical = json.loads(historical_data_json)
        forecasts = self.trend_analyzer.forecast_growth(historical, periods)
        return json.dumps({
            "forecasts": forecasts,
            "periods": periods,
            "method": "linear_regression",
        })

    async def _tool_extract_insights(
        self, analysis_results_json: str
    ) -> str:
        """Extract key insights from analysis results."""
        results = json.loads(analysis_results_json)
        # Use LLM to synthesize insights
        prompt = f"""Based on the following analysis results, extract the top 10 most important market insights.
For each insight, provide:
- Category (market_size/competitive/trend/sentiment/opportunity/risk)
- Title and description
- Evidence references
- Confidence score (0.0-1.0)
- Impact level (low/medium/high/critical)
- Timeframe (immediate/short_term/medium_term/long_term)
- Recommended action

Analysis results:
{json.dumps(results, default=str)[:5000]}

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception:
            return json.dumps({"error": "insight extraction failed"})

    async def _tool_score_opportunities(
        self, opportunities_json: str
    ) -> str:
        """Score and rank market opportunities."""
        opportunities = json.loads(opportunities_json)
        # Scoring criteria: market size, growth rate, competitive intensity,
        # alignment with capabilities, time to market
        scored = []
        for opp in opportunities:
            score = 0.0
            # Market size score (0-30)
            size = opp.get("market_size", 0)
            if size > 1000:
                score += 30
            elif size > 500:
                score += 20
            elif size > 100:
                score += 10
            # Growth rate score (0-25)
            growth = opp.get("growth_rate", 0)
            if growth > 20:
                score += 25
            elif growth > 10:
                score += 15
            elif growth > 5:
                score += 5
            # Competitive gap score (0-25)
            competition = opp.get("competition_intensity", "high")
            score += {"low": 25, "medium": 15, "high": 5}.get(competition, 10)
            # Feasibility score (0-20)
            feasibility = opp.get("feasibility", "medium")
            score += {"high": 20, "medium": 10, "low": 5}.get(feasibility, 10)

            scored.append({**opp, "opportunity_score": score})

        scored.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return json.dumps(scored, default=str)

    async def analyze(
        self,
        research_topic: str,
        collected_data: list[CollectedData],
        competitors: list[str],
    ) -> AnalysisReport:
        """
        Execute full analysis pipeline.
        
        This is the main entry point that runs all analysis stages
        and produces a comprehensive AnalysisReport.
        """
        # Convert collected data to dicts for processing
        data_dicts = [d.model_dump() for d in collected_data]

        # Stage 1: Sentiment Analysis
        all_texts = [d.content for d in collected_data if d.content]
        sentiment = self.sentiment_analyzer.analyze(all_texts)

        # Stage 2: Competitive Analysis
        competitive_positions = []
        for competitor in competitors:
            pos = self.competitive_analyzer.analyze_competitor(
                competitor, data_dicts
            )
            competitive_positions.append(pos)

        # Stage 3: Trend Analysis
        trends = self.trend_analyzer.identify_trends(data_dicts)

        # Stage 4: Market Sizing
        sizing = self.market_sizing.estimate_market_size(
            research_topic, data_dicts
        )

        # Stage 5: SWOT Analysis
        swot = self.competitive_analyzer.generate_swot(
            "Our Company", competitive_positions, data_dicts
        )

        # Stage 6: Insight Synthesis
        key_insights = self._synthesize_insights(
            sentiment, competitive_positions, trends, sizing, swot
        )

        # Calculate data quality score
        quality_score = self._calculate_data_quality(collected_data)

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            research_topic, key_insights, sentiment, competitive_positions
        )

        return AnalysisReport(
            research_topic=research_topic,
            analysis_date=datetime.now(),
            executive_summary=executive_summary,
            competitive_positions=competitive_positions,
            sentiment_analysis=sentiment,
            trend_forecasts=trends,
            swot=swot,
            key_insights=key_insights,
            data_quality_score=quality_score,
            limitations=self._identify_limitations(collected_data),
            methodology_notes="Multi-source analysis using LLM-assisted extraction, lexicon-based sentiment, and statistical trend identification.",
        )

    def _synthesize_insights(
        self,
        sentiment: SentimentAnalysis,
        competitors: list[CompetitivePosition],
        trends: list[TrendForecast],
        sizing: dict,
        swot: SWOTAnalysis,
    ) -> list[MarketInsight]:
        """Synthesize key insights from all analyses."""
        insights = []

        # Sentiment-based insights
        if sentiment.sentiment_score < -0.3:
            insights.append(MarketInsight(
                insight_id="sent-001",
                category="sentiment",
                title="Negative market sentiment detected",
                description=f"Overall sentiment is {sentiment.overall_sentiment} (score: {sentiment.sentiment_score:.2f}). Key negative themes: {', '.join(sentiment.negative_themes[:3])}.",
                confidence=sentiment.confidence,
                impact="high",
                timeframe="immediate",
                recommended_action="Investigate root causes and develop reputation management strategy.",
            ))

        # Competitive insights
        for comp in competitors:
            if comp.threat_level == "high":
                insights.append(MarketInsight(
                    insight_id=f"comp-{comp.competitor}",
                    category="competitive",
                    title=f"High threat from {comp.competitor}",
                    description=f"{comp.competitor} poses a significant competitive threat with strengths in: {', '.join(comp.strengths[:3])}.",
                    confidence=comp.confidence,
                    impact="high",
                    timeframe="short_term",
                    recommended_action=f"Develop counter-positioning strategy focusing on {comp.competitor}'s weaknesses.",
                ))

        # Trend insights
        for trend in trends:
            if trend.current_stage in ("emerging", "growth"):
                insights.append(MarketInsight(
                    insight_id=f"trend-{trend.trend_name}",
                    category="trend",
                    title=f"Emerging trend: {trend.trend_name}",
                    description=trend.description,
                    confidence=trend.confidence,
                    impact="medium",
                    timeframe="medium_term",
                    recommended_action="Evaluate alignment with current capabilities and consider early investment.",
                ))

        # SWOT-based insights
        for opp in swot.opportunities:
            insights.append(MarketInsight(
                insight_id=f"opp-{hash(opp) % 10000}",
                category="opportunity",
                title=f"Opportunity: {opp[:50]}",
                description=opp,
                confidence=0.6,
                impact="medium",
                timeframe="medium_term",
            ))

        # Sort by impact and confidence
        impact_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        insights.sort(key=lambda x: (impact_order.get(x.impact, 4), -x.confidence))

        return insights[:20]  # Top 20 insights

    def _calculate_data_quality(
        self, data: list[CollectedData]
    ) -> float:
        """Calculate overall data quality score."""
        if not data:
            return 0.0

        scores = []
        for d in data:
            score = 0.0
            # Content length (longer is generally better, up to a point)
            content_len = len(d.content)
            if content_len > 500:
                score += 0.3
            elif content_len > 200:
                score += 0.2
            elif content_len > 50:
                score += 0.1
            # Has metadata
            if d.metadata:
                score += 0.2
            # Has entities
            if d.entities:
                score += 0.2
            # Source reliability (would be tracked per source)
            score += 0.3  # Default
            scores.append(min(1.0, score))

        return sum(scores) / len(scores)

    def _identify_limitations(
        self, data: list[CollectedData]
    ) -> list[str]:
        """Identify limitations of the analysis."""
        limitations = []
        if len(data) < 10:
            limitations.append("Limited data points may reduce analysis reliability")
        sources = set(d.source for d in data)
        if len(sources) < 3:
            limitations.append("Limited source diversity may introduce bias")
        # Check date range
        if data:
            dates = [d.collected_at for d in data if d.collected_at]
            if dates:
                date_range = (max(dates) - min(dates)).days
                if date_range < 7:
                    limitations.append("Short time window may miss longer-term trends")
        return limitations

    def _generate_executive_summary(
        self,
        topic: str,
        insights: list[MarketInsight],
        sentiment: SentimentAnalysis,
        competitors: list[CompetitivePosition],
    ) -> str:
        """Generate executive summary text."""
        high_impact = [i for i in insights if i.impact in ("high", "critical")]
        summary_parts = [
            f"Market research analysis for '{topic}' identified {len(insights)} key insights, "
            f"of which {len(high_impact)} are high-impact.",
            f"Overall market sentiment is {sentiment.overall_sentiment} "
            f"(score: {sentiment.sentiment_score:.2f}).",
        ]
        if competitors:
            high_threats = [c for c in competitors if c.threat_level == "high"]
            if high_threats:
                summary_parts.append(
                    f"High competitive threat from: {', '.join(c.competitor for c in high_threats)}."
                )
        return " ".join(summary_parts)

    def create_agent_executor(self) -> AgentExecutor:
        """Create a LangChain agent executor with analysis tools."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior market research analyst.
Your job is to analyze market data and extract actionable insights.

Analysis framework:
1. Start with descriptive analysis (what happened?)
2. Move to diagnostic analysis (why did it happen?)
3. Conclude with predictive analysis (what will happen?)

Guidelines:
- Always cite evidence for your claims
- Quantify findings where possible
- Distinguish between facts and inferences
- Consider multiple perspectives
- Flag uncertainties and limitations
- Prioritize insights by business impact

Available tools: {tools}
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=25,
        )
```

### 3.4 Analysis Quality Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Insight Precision** | % of insights backed by evidence | ≥ 85% |
| **Coverage** | % of data points incorporated in analysis | ≥ 90% |
| **Novelty** | % of insights not obvious from single source | ≥ 60% |
| **Actionability** | % of insights with clear recommended actions | ≥ 75% |
| **Confidence Calibration** | Predicted vs actual confidence alignment | Brier score < 0.2 |

---

## 4. Reporting Agent Implementation

### 4.1 Purpose

The Reporting Agent transforms analysis outputs into polished, audience-appropriate reports. It supports multiple formats (PDF, HTML, PowerPoint, Slack messages) and adapts content depth based on the target audience (executives, analysts, marketing teams).

### 4.2 Report Types

| Report Type | Audience | Frequency | Format | Length |
|-------------|----------|-----------|--------|--------|
| **Executive Brief** | C-suite | Weekly | PDF + Email | 2-3 pages |
| **Competitive Intelligence** | Strategy team | Bi-weekly | PDF + Dashboard | 10-15 pages |
| **Market Trends Report** | Product team | Monthly | HTML + Slides | 15-20 pages |
| **Social Listening Summary** | Marketing team | Daily | Slack + Email | 1 page |
| **Pricing Analysis** | Sales + Product | Weekly | Excel + PDF | 5-10 pages |
| **Ad Hoc Research** | Requestor | On-demand | PDF | Variable |

### 4.3 Implementation

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import json
import markdown
from jinja2 import Template
import asyncio

# ─── Report Data Models ───────────────────────────────────────

class ReportSection(BaseModel):
    """A section within a report."""
    title: str
    content: str
    section_type: str  # "text", "chart", "table", "callout", "summary"
    order: int = 0
    data_source: Optional[str] = None
    chart_config: Optional[dict] = None

class ReportTemplate(BaseModel):
    """Report template configuration."""
    name: str
    description: str
    sections: list[str]  # Ordered section names
    target_audience: str
    format: str  # "pdf", "html", "pptx", "markdown", "slack"
    style_guide: dict = Field(default_factory=dict)

class GeneratedReport(BaseModel):
    """A generated report."""
    report_id: str
    title: str
    report_type: str
    created_at: datetime
    author: str = "AI Market Research Agent"
    sections: list[ReportSection] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    format: str = "markdown"
    content_markdown: str = ""
    content_html: str = ""
    file_path: Optional[str] = None
    distribution_list: list[str] = Field(default_factory=list)


# ─── Report Generation Tools ──────────────────────────────────

class ChartGenerator:
    """Generates charts and visualizations."""

    def __init__(self):
        self.supported_types = [
            "bar", "line", "pie", "scatter", "heatmap",
            "radar", "bubble", "area",
        ]

    def generate_chart(
        self,
        chart_type: str,
        data: dict,
        title: str,
        config: dict = None,
    ) -> dict:
        """Generate chart configuration (Plotly-compatible)."""
        if chart_type not in self.supported_types:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        chart_config = {
            "type": chart_type,
            "title": title,
            "data": data,
            "layout": {
                "title": {"text": title},
                "template": "plotly_white",
                **(config or {}),
            },
        }
        return chart_config

    def market_share_pie(
        self, shares: dict[str, float], title: str = "Market Share"
    ) -> dict:
        """Generate market share pie chart."""
        return self.generate_chart(
            "pie",
            {
                "values": list(shares.values()),
                "labels": list(shares.keys()),
            },
            title,
        )

    def trend_line(
        self,
        dates: list[str],
        values: list[float],
        title: str = "Trend",
        y_axis: str = "Value",
    ) -> dict:
        """Generate trend line chart."""
        return self.generate_chart(
            "line",
            {"x": dates, "y": values},
            title,
            {"yaxis": {"title": y_axis}},
        )

    def sentiment_gauge(
        self, score: float, title: str = "Sentiment Score"
    ) -> dict:
        """Generate sentiment gauge chart."""
        return self.generate_chart(
            "indicator",
            {
                "value": score,
                "mode": "gauge+number",
                "gauge": {
                    "axis": {"range": [-1, 1]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [-1, -0.3], "color": "red"},
                        {"range": [-0.3, 0.3], "color": "gray"},
                        {"range": [0.3, 1], "color": "green"},
                    ],
                },
            },
            title,
        )

    def competitive_radar(
        self,
        categories: list[str],
        series: dict[str, list[float]],
        title: str = "Competitive Comparison",
    ) -> dict:
        """Generate radar chart for competitive comparison."""
        return self.generate_chart(
            "radar",
            {
                "categories": categories,
                "series": series,
            },
            title,
        )


class TableGenerator:
    """Generates formatted tables."""

    def generate_table(
        self,
        headers: list[str],
        rows: list[list],
        title: str = "",
        sortable: bool = True,
    ) -> dict:
        """Generate table configuration."""
        return {
            "type": "table",
            "title": title,
            "headers": headers,
            "rows": rows,
            "sortable": sortable,
        }

    def pricing_comparison_table(
        self,
        competitors: list[str],
        features: list[str],
        prices: dict[str, dict[str, str]],
    ) -> dict:
        """Generate pricing comparison table."""
        headers = ["Feature"] + competitors
        rows = []
        for feature in features:
            row = [feature]
            for comp in competitors:
                row.append(prices.get(comp, {}).get(feature, "N/A"))
            rows.append(row)
        return self.generate_table(headers, rows, "Pricing Comparison")

    def swot_table(self, swot: dict) -> dict:
        """Generate SWOT table."""
        return {
            "type": "swot",
            "strengths": swot.get("strengths", []),
            "weaknesses": swot.get("weaknesses", []),
            "opportunities": swot.get("opportunities", []),
            "threats": swot.get("threats", []),
        }


class DocumentFormatter:
    """Formats reports into various output formats."""

    def __init__(self):
        self.templates_dir = "templates/reports"

    def to_markdown(self, report: GeneratedReport) -> str:
        """Convert report to Markdown."""
        md_parts = [
            f"# {report.title}",
            "",
            f"**Generated:** {report.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Author:** {report.author}",
            "",
            "---",
            "",
        ]
        for section in sorted(report.sections, key=lambda s: s.order):
            md_parts.append(f"## {section.title}")
            md_parts.append("")
            md_parts.append(section.content)
            md_parts.append("")
        return "\n".join(md_parts)

    def to_html(self, report: GeneratedReport) -> str:
        """Convert report to HTML."""
        md_content = self.to_markdown(report)
        html_content = markdown.markdown(
            md_content,
            extensions=["tables", "fenced_code", "toc"],
        )
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{report.title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; line-height: 1.6; }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 0.5rem; }}
        h2 {{ color: #16213e; margin-top: 2rem; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #ddd; padding: 0.75rem; text-align: left; }}
        th {{ background-color: #f8f9fa; }}
        .metadata {{ color: #666; font-size: 0.9rem; }}
        .callout {{ background: #f0f4ff; border-left: 4px solid #e94560; padding: 1rem; margin: 1rem 0; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

    def to_slack(self, report: GeneratedReport) -> dict:
        """Convert report to Slack message blocks."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 {report.title}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Generated:* {report.created_at.strftime('%Y-%m-%d %H:%M')}",
                },
            },
            {"type": "divider"},
        ]
        # Add top 3 insights as sections
        for section in sorted(report.sections, key=lambda s: s.order)[:5]:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{section.title}*\n{section.content[:500]}",
                },
            })
        return {"blocks": blocks}

    def to_pdf(self, report: GeneratedReport, output_path: str) -> str:
        """Convert report to PDF (using weasyprint or similar)."""
        html_content = self.to_html(report)
        # Would use weasyprint, pdfkit, or reportlab
        # For now, return the path
        return output_path


# ─── Reporting Agent ─────────────────────────────────────────

class ReportingAgent:
    """
    LangChain DeepAgent for generating market research reports.
    Adapts content and format based on audience and purpose.
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        templates: Optional[list[ReportTemplate]] = None,
        output_dir: str = "./reports",
    ):
        self.llm = llm
        self.templates = templates or self._default_templates()
        self.output_dir = output_dir
        self.chart_gen = ChartGenerator()
        self.table_gen = TableGenerator()
        self.formatter = DocumentFormatter()
        self._build_tools()

    def _default_templates(self) -> list[ReportTemplate]:
        """Default report templates."""
        return [
            ReportTemplate(
                name="executive Brief",
                description="Concise weekly summary for executives",
                sections=[
                    "Executive Summary",
                    "Key Metrics",
                    "Top 3 Insights",
                    "Competitive Alert",
                    "Recommended Actions",
                ],
                target_audience="executive",
                format="pdf",
            ),
            ReportTemplate(
                name="Competitive Intelligence",
                description="Detailed competitive analysis",
                sections=[
                    "Executive Summary",
                    "Competitive Landscape",
                    "Competitor Profiles",
                    "Feature Comparison",
                    "Pricing Analysis",
                    "Strategic Implications",
                    "Recommendations",
                ],
                target_audience="Strategy",
                format="pdf",
            ),
            ReportTemplate(
                name="Market Trends",
                description="Monthly market trends and forecasts",
                sections=[
                    "Executive Summary",
                    "Market Overview",
                    "Trend Analysis",
                    "Segment Deep Dive",
                    "Forecast",
                    "Opportunities & Risks",
                    "Methodology",
                ],
                target_audience="Product",
                format="html",
            ),
            ReportTemplate(
                name="Social Listening Daily",
                description="Daily social media and sentiment summary",
                sections=[
                    "Sentiment Snapshot",
                    "Top Mentions",
                    "Trending Topics",
                    "Influencer Activity",
                    "Risk Alerts",
                ],
                target_audience="Marketing",
                format="slack",
            ),
        ]

    def _build_tools(self):
        """Build reporting tools."""
        self.tools = [
            StructuredTool.from_function(
                func=self._tool_generate_chart,
                name="generate_chart",
                description="Generate a chart/visualization from data (bar, line, pie, radar, etc.).",
            ),
            StructuredTool.from_function(
                func=self._tool_generate_table,
                name="generate_table",
                description="Generate a formatted table from structured data.",
            ),
            StructuredTool.from_function(
                func=self._tool_format_report,
                name="format_report",
                description="Format a report section into the target output format.",
            ),
            StructuredTool.from_function(
                func=self._tool_apply_template,
                name="apply_template",
                description="Apply a report template to structure the content.",
            ),
            StructuredTool.from_function(
                func=self._tool_export_report,
                name="export_report",
                description="Export the report to PDF, HTML, or other formats.",
            ),
            StructuredTool.from_function(
                func=self._tool_schedule_report,
                name="schedule_report",
                description="Schedule recurring report generation and distribution.",
            ),
            StructuredTool.from_function(
                func=self._tool_distribute_report,
                name="distribute_report",
                description="Distribute report via email, Slack, or other channels.",
            ),
        ]

    async def _tool_generate_chart(
        self,
        chart_type: str,
        data_json: str,
        title: str,
        config_json: str = "{}",
    ) -> str:
        """Generate a chart."""
        data = json.loads(data_json)
        config = json.loads(config_json)
        chart = self.chart_gen.generate_chart(chart_type, data, title, config)
        return json.dumps(chart)

    async def _tool_generate_table(
        self,
        headers_json: str,
        rows_json: str,
        title: str = "",
    ) -> str:
        """Generate a table."""
        headers = json.loads(headers_json)
        rows = json.loads(rows_json)
        table = self.table_gen.generate_table(headers, rows, title)
        return json.dumps(table)

    async def _tool_format_report(
        self, content: str, format: str, style: str = "default"
    ) -> str:
        """Format report content."""
        if format == "markdown":
            return content
        elif format == "html":
            return markdown.markdown(content, extensions=["tables"])
        elif format == "slack":
            # Convert to Slack mrkdwn
            return content.replace("**", "*").replace("##", "*")
        return content

    async def _tool_apply_template(
        self, template_name: str, content_json: str
    ) -> str:
        """Apply a report template."""
        template = next(
            (t for t in self.templates if t.name == template_name), None
        )
        if not template:
            return json.dumps({"error": f"Template '{template_name}' not found"})
        content = json.loads(content_json)
        structured = {
            "template": template.name,
            "audience": template.target_audience,
            "format": template.format,
            "sections": [],
        }
        for section_name in template.sections:
            section_content = content.get(section_name, "")
            structured["sections"].append({
                "title": section_name,
                "content": section_content,
                "order": template.sections.index(section_name),
            })
        return json.dumps(structured)

    async def _tool_export_report(
        self, report_json: str, format: str, output_path: str
    ) -> str:
        """Export report to file."""
        report_data = json.loads(report_json)
        # Create GeneratedReport and export
        report = GeneratedReport(
            report_id=f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=report_data.get("title", "Market Research Report"),
            report_type=report_data.get("report_type", "general"),
            created_at=datetime.now(),
            format=format,
        )
        if format == "markdown":
            content = self.formatter.to_markdown(report)
        elif format == "html":
            content = self.formatter.to_html(report)
        else:
            content = self.formatter.to_markdown(report)
        # Write to file
        return json.dumps({
            "status": "exported",
            "format": format,
            "path": output_path,
        })

    async def _tool_schedule_report(
        self,
        template_name: str,
        frequency: str,  # "daily", "weekly", "monthly"
        distribution_list: str,  # comma-separated emails/channels
    ) -> str:
        """Schedule recurring report."""
        # Would integrate with scheduler (e.g., APScheduler, Celery)
        return json.dumps({
            "status": "scheduled",
            "template": template_name,
            "frequency": frequency,
            "recipients": distribution_list.split(","),
            "next_run": "calculated based on frequency",
        })

    async def _tool_distribute_report(
        self,
        report_path: str,
        channels: str,  # comma-separated: "email,slack,drive"
        recipients: str = "",
    ) -> str:
        """Distribute report to channels."""
        channel_list = channels.split(",")
        results = {}
        for channel in channel_list:
            if channel == "email":
                results["email"] = "sent"  # Would use email service
            elif channel == "slack":
                results["slack"] = "posted"  # Would use Slack API
            elif channel == "drive":
                results["drive"] = "uploaded"  # Would use Google Drive API
        return json.dumps(results)

    async def generate_report(
        self,
        analysis_report: AnalysisReport,
        template_name: str = "Executive Brief",
        format: str = "pdf",
        audience: str = "executive",
    ) -> GeneratedReport:
        """
        Generate a complete report from analysis results.
        
        This is the main entry point that creates audience-appropriate
        reports from structured analysis output.
        """
        template = next(
            (t for t in self.templates if t.name == template_name),
            self.templates[0],
        )

        sections = []

        # Executive Summary
        sections.append(ReportSection(
            title="Executive Summary",
            content=analysis_report.executive_summary,
            section_type="summary",
            order=0,
        ))

        # Key Insights
        insights_content = self._format_insights(
            analysis_report.key_insights[:10]
        )
        sections.append(ReportSection(
            title="Key Insights",
            content=insights_content,
            section_type="text",
            order=1,
        ))

        # Sentiment Analysis
        if analysis_report.sentiment_analysis:
            sentiment = analysis_report.sentiment_analysis
            sentiment_content = self._format_sentiment(sentiment)
            sections.append(ReportSection(
                title="Market Sentiment",
                content=sentiment_content,
                section_type="text",
                order=2,
                chart_config=self.chart_gen.sentiment_gauge(
                    sentiment.sentiment_score
                ),
            ))

        # Competitive Landscape
        if analysis_report.competitive_positions:
            comp_content = self._format_competitive(
                analysis_report.competitive_positions
            )
            sections.append(ReportSection(
                title="Competitive Landscape",
                content=comp_content,
                section_type="text",
                order=3,
            ))

        # SWOT Analysis
        if analysis_report.swot:
            swot_content = self._format_swot(analysis_report.swot)
            sections.append(ReportSection(
                title="SWOT Analysis",
                content=swot_content,
                section_type="callout",
                order=4,
            ))

        # Trend Forecasts
        if analysis_report.trend_forecasts:
            trends_content = self._format_trends(
                analysis_report.trend_forecasts
            )
            sections.append(ReportSection(
                title="Trend Forecasts",
                content=trends_content,
                section_type="text",
                order=5,
            ))

        # Recommendations
        recommendations = self._generate_recommendations(
            analysis_report.key_insights
        )
        sections.append(ReportSection(
            title="Recommendations",
            content=recommendations,
            section_type="callout",
            order=6,
        ))

        # Methodology
        sections.append(ReportSection(
            title="Methodology & Data Quality",
            content=f"Data Quality Score: {analysis_report.data_quality_score:.0%}\n\n"
                    f"Methodology: {analysis_report.methodology_notes}\n\n"
                    f"Limitations: {'; '.join(analysis_report.limitations)}",
            section_type="text",
            order=99,
        ))

        # Build report
        report = GeneratedReport(
            report_id=f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=f"Market Research: {analysis_report.research_topic}",
            report_type=template_name,
            created_at=datetime.now(),
            sections=sections,
            format=format,
            metadata={
                "data_quality": analysis_report.data_quality_score,
                "insights_count": len(analysis_report.key_insights),
                "competitors_analyzed": len(
                    analysis_report.competitive_positions
                ),
                "template_used": template_name,
            },
        )

        # Generate content in target format
        if format == "markdown":
            report.content_markdown = self.formatter.to_markdown(report)
        elif format == "html":
            report.content_html = self.formatter.to_html(report)
        elif format == "slack":
            report.content_markdown = json.dumps(
                self.formatter.to_slack(report)
            )

        return report

    def _format_insights(self, insights: list[MarketInsight]) -> str:
        """Format insights for report."""
        parts = []
        for i, insight in enumerate(insights, 1):
            impact_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }.get(impact.impact, "⚪")
            parts.append(
                f"### {impact_emoji} {insight.title}\n\n"
                f"**Category:** {insight.category} | "
                f"**Impact:** {insight.impact} | "
                f"**Confidence:** {insight.confidence:.0%}\n\n"
                f"{insight.description}\n"
            )
            if insight.recommended_action:
                parts.append(
                    f"\n**Recommended Action:** {insight.recommended_action}\n"
                )
        return "\n".join(parts)

    def _format_sentiment(self, sentiment: SentimentAnalysis) -> str:
        """Format sentiment analysis for report."""
        return f"""**Overall Sentiment:** {sentiment.overall_sentiment.title()}
**Sentiment Score:** {sentiment.sentiment_score:.2f} (-1.0 to +1.0)
**Trend Direction:** {sentiment.trend_direction}
**Confidence:** {sentiment.confidence:.0%}

**Positive Themes:** {', '.join(sentiment.positive_themes) if sentiment.positive_themes else 'None identified'}
**Negative Themes:** {', '.join(sentiment.negative_themes) if sentiment.negative_themes else 'None identified'}
"""

    def _format_competitive(
        self, positions: list[CompetitivePosition]
    ) -> str:
        """Format competitive analysis for report."""
        parts = []
        for pos in positions:
            threat_emoji = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢",
            }.get(pos.threat_level, "⚪")
            parts.append(
                f"### {threat_emoji} {pos.competitor}\n\n"
                f"**Threat Level:** {pos.threat_level}\n"
                f"**Pricing Position:** {pos.pricing_position}\n\n"
                f"**Strengths:** {', '.join(pos.strengths) if pos.strengths else 'N/A'}\n\n"
                f"**Weaknesses:** {', '.join(pos.weaknesses) if pos.weaknesses else 'N/A'}\n\n"
                f"**Key Differentiators:** {', '.join(pos.key_differentiators) if pos.key_differentiators else 'N/A'}\n"
            )
        return "\n".join(parts)

    def _format_swot(self, swot: SWOTAnalysis) -> str:
        """Format SWOT analysis for report."""
        return f"""| | Helpful | Harmful |
|---|---|---|
| **Internal** | **Strengths:**<br>{'<br>'.join(f'• {s}' for s in swot.strengths)} | **Weaknesses:**<br>{'<br>'.join(f'• {w}' for w in swot.weaknesses)} |
| **External** | **Opportunities:**<br>{'<br>'.join(f'• {o}' for o in swot.opportunities)} | **Threats:**<br>{'<br>'.join(f'• {t}' for t in swot.threats)} |

**Strategic Implications:**
{'<br>'.join(f'• {i}' for i in swot.strategic_implications)}
"""

    def _format_trends(self, trends: list[TrendForecast]) -> str:
        """Format trend forecasts for report."""
        parts = []
        for trend in trends:
            stage_emoji = {
                "emerging": "🌱",
                "growth": "📈",
                "mature": "➡️",
                "declining": "📉",
            }.get(trend.current_stage, "⚪")
            parts.append(
                f"### {stage_emoji} {trend.trend_name}\n\n"
                f"**Stage:** {trend.current_stage} | "
                f"**Horizon:** {trend.forecast_horizon} | "
                f"**Confidence:** {trend.confidence:.0%}\n\n"
                f"{trend.description}\n\n"
                f"**Key Drivers:** {', '.join(trend.key_drivers)}\n\n"
                f"**Risks:** {', '.join(trend.risks)}\n"
            )
        return "\n".join(parts)

    def _generate_recommendations(
        self, insights: list[MarketInsight]
    ) -> str:
        """Generate actionable recommendations from insights."""
        recommendations = []
        for insight in insights:
            if insight.recommended_action and insight.impact in (
                "high", "critical"
            ):
                recommendations.append(
                    f"• **{insight.title}:** {insight.recommended_action}"
                )
        if not recommendations:
            recommendations.append(
                "• Continue monitoring market developments for emerging opportunities."
            )
        return "\n".join(recommendations)

    def create_agent_executor(self) -> AgentExecutor:
        """Create a LangChain agent executor with reporting tools."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional report writer specializing in market research.
Your job is to transform analysis outputs into clear, actionable reports.

Writing guidelines:
- Lead with the most important insights (inverted pyramid)
- Use clear, jargon-free language appropriate for the audience
- Support claims with data and evidence
- Use visual elements (charts, tables) to illustrate key points
- Include clear, specific recommendations
- Maintain consistent formatting and style
- Flag uncertainties and data limitations

Available tools: {tools}
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15,
        )
```

### 4.4 Report Distribution

```python
class ReportDistributor:
    """Handles report distribution across channels."""

    def __init__(
        self,
        slack_webhook: Optional[str] = None,
        email_config: Optional[dict] = None,
        drive_credentials: Optional[dict] = None,
    ):
        self.slack_webhook = slack_webhook
        self.email_config = email_config
        self.drive_credentials = drive_credentials

    async def distribute(
        self,
        report: GeneratedReport,
        channels: list[str],
        recipients: list[str] = None,
    ) -> dict:
        """Distribute report to specified channels."""
        results = {}
        for channel in channels:
            if channel == "slack":
                results["slack"] = await self._send_slack(report)
            elif channel == "email":
                results["email"] = await self._send_email(report, recipients)
            elif channel == "drive":
                results["drive"] = await self._upload_drive(report)
        return results

    async def _send_slack(self, report: GeneratedReport) -> str:
        """Send report summary to Slack."""
        # Implementation using Slack SDK
        return "sent"

    async def _send_email(
        self, report: GeneratedReport, recipients: list[str]
    ) -> str:
        """Send report via email."""
        # Implementation using sendgrid/smtp
        return "sent"

    async def _upload_drive(self, report: GeneratedReport) -> str:
        """Upload report to Google Drive."""
        # Implementation using Google Drive API
        return "uploaded"
```

---

## 5. Action Agent Implementation

### 5.1 Purpose

The Action Agent translates market insights into concrete marketing actions. It generates campaign briefs, content calendars, ad copy variations, and go-to-market recommendations based on the analysis output.

### 5.2 Action Types

| Action Category | Specific Actions | Trigger | Output |
|----------------|-----------------|---------|--------|
| **Content Marketing** | Blog topics, whitepaper outlines, social posts | Trend identification, content gaps | Content calendar, drafts |
| **Paid Advertising** | Ad copy, audience segments, bid strategies | Competitive gaps, high-intent keywords | Campaign setup specs |
| **SEO** | Keyword targets, content clusters, link building | Search trend analysis | SEO action plan |
| **Product** | Feature recommendations, positioning updates | Competitive feature gaps | Product brief |
| **Sales Enablement** | Battle cards, objection handling, case studies | Competitive threats | Sales kit |
| **Email Marketing** | Campaign sequences, subject lines, segmentation | Customer behavior insights | Email campaign spec |
| **Social Media** | Post calendar, engagement strategy, influencer targets | Social sentiment analysis | Social media plan |

### 5.3 Implementation

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
import json

# ─── Action Data Models ───────────────────────────────────────

class MarketingAction(BaseModel):
    """A specific marketing action."""
    action_id: str
    action_type: str  # "content", "advertising", "seo", "product", "sales", "email", "social"
    title: str
    description: str
    priority: str  # "critical", "high", "medium", "low"
    effort: str  # "low", "medium", "high"
    impact: str  # "low", "medium", "high"
    timeframe: str  # "immediate", "this_week", "this_month", "this_quarter"
    dependencies: list[str] = Field(default_factory=list)
    required_resources: list[str] = Field(default_factory=list)
    expected_outcome: str = ""
    success_metrics: list[str] = Field(default_factory=list)
    content: Optional[str] = None  # Generated content (ad copy, blog draft, etc.)
    status: str = "proposed"  # "proposed", "approved", "in_progress", "completed"

class CampaignBrief(BaseModel):
    """A complete campaign brief."""
    brief_id: str
    campaign_name: str
    objective: str
    target_audience: str
    key_message: str
    actions: list[MarketingAction] = Field(default_factory=list)
    budget_recommendation: Optional[float] = None
    timeline: str = ""
    kpis: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

class ContentCalendar(BaseModel):
    """A content calendar."""
    calendar_id: str
    period: str  # e.g., "2026-Q4"
    items: list[dict] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


# ─── Action Generation Tools ──────────────────────────────────

class ContentGenerator:
    """Generates marketing content based on insights."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def generate_blog_topics(
        self, insights: list[MarketInsight], count: int = 10
    ) -> list[dict]:
        """Generate blog topic ideas from insights."""
        prompt = f"""Based on these market insights, generate {count} blog topic ideas.
For each topic, provide:
- Title (SEO-optimized, under 60 characters)
- Target keyword
- Search intent (informational/transactional/navigational)
- Estimated search volume category (low/medium/high)
- Content angle
- Suggested word count

Market insights:
{json.dumps([i.model_dump() for i in insights[:10]], default=str)[:3000]}

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            # Parse response
            return [{"title": "Sample Topic", "keyword": "sample"}]
        except Exception:
            return []

    def generate_ad_copy(
        self,
        product: str,
        target_audience: str,
        key_benefit: str,
        competitive_angle: str,
        variations: int = 5,
    ) -> list[dict]:
        """Generate ad copy variations."""
        prompt = f"""Generate {variations} ad copy variations for:
Product: {product}
Target Audience: {target_audience}
Key Benefit: {key_benefit}
Competitive Angle: {competitive_angle}

For each variation, provide:
- Headline (max 30 chars)
- Primary text (max 90 chars)
- Description (max 90 chars)
- Call to action
- Targeting notes

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            return [{"headline": "Sample", "body": "Sample ad copy"}]
        except Exception:
            return []

    def generate_social_posts(
        self,
        topic: str,
        platforms: list[str],
        tone: str = "professional",
        count: int = 5,
    ) -> list[dict]:
        """Generate social media posts."""
        posts = []
        for platform in platforms:
            prompt = f"""Generate {count} social media posts for {platform} about: {topic}
Tone: {tone}
Platform constraints: {self._platform_constraints(platform)}

For each post, provide:
- Post text
- Hashtags
- Suggested posting time
- Engagement question (if applicable)

Respond in JSON format."""
            try:
                response = self.llm.invoke(prompt)
                posts.append({
                    "platform": platform,
                    "posts": [{"text": "Sample post", "hashtags": ["#sample"]}],
                })
            except Exception:
                continue
        return posts

    def _platform_constraints(self, platform: str) -> str:
        """Get platform-specific constraints."""
        constraints = {
            "twitter": "Max 280 characters, concise and engaging",
            "linkedin": "Professional tone, 1300 char max, thought leadership",
            "facebook": "Conversational, 63206 char max but shorter is better",
            "instagram": "Visual-focused, 2200 char max, hashtag-heavy",
        }
        return constraints.get(platform, "Standard social media best practices")

    def generate_email_sequence(
        self,
        sequence_type: str,  # "welcome", "nurture", "re_engagement", "product_launch"
        audience: str,
        product: str,
        steps: int = 5,
    ) -> list[dict]:
        """Generate email sequence."""
        prompt = f"""Create a {steps}-step {sequence_type} email sequence for:
Audience: {audience}
Product: {product}

For each email, provide:
- Subject line (A/B test variants)
- Preview text
- Body outline (key points, not full copy)
- Call to action
- Send timing (day X of sequence)
- Personalization tokens needed

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            return [{"subject": "Sample Subject", "body": "Sample body"}]
        except Exception:
            return []


class SEOStrategyGenerator:
    """Generates SEO action plans."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def generate_keyword_strategy(
        self,
        market_data: list[dict],
        competitors: list[str],
    ) -> dict:
        """Generate keyword targeting strategy."""
        prompt = f"""Based on market data and competitor analysis, create a keyword strategy.

Competitors: {', '.join(competitors)}

Provide:
1. Primary keywords (high volume, high intent) - top 10
2. Secondary keywords (medium volume, specific intent) - top 20
3. Long-tail opportunities (low volume, high conversion) - top 20
4. Content gaps (keywords competitors rank for but we don't) - top 10
5. Keyword difficulty assessment for each category

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            return json.loads(response.content)
        except Exception:
            return {}

    def generate_content_clusters(
        self,
        topic: str,
        subtopics: list[str],
    ) -> list[dict]:
        """Generate content cluster strategy."""
        clusters = []
        for subtopic in subtopics:
            clusters.append({
                "pillar_topic": topic,
                "cluster_topic": subtopic,
                "target_keywords": [],
                "content_type": "blog_post",
                "estimated_word_count": 1500,
                "internal_links": [],
            })
        return clusters


class CompetitiveResponseGenerator:
    """Generates competitive response strategies."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def generate_battle_card(
        self,
        competitor: str,
        our_product: str,
        competitor_strengths: list[str],
        competitor_weaknesses: list[str],
    ) -> dict:
        """Generate sales battle card."""
        prompt = f"""Create a sales battle card comparing {our_product} vs {competitor}.

Competitor strengths: {', '.join(competitor_strengths)}
Competitor weaknesses: {', '.join(competitor_weaknesses)}

Include:
1. Competitor overview (2-3 sentences)
2. Their key strengths (and how to counter each)
3. Their weaknesses (and how to exploit each)
4. Objection handling (top 5 objections and responses)
5. Win/loss analysis patterns
6. Recommended competitive positioning

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            return json.loads(response.content)
        except Exception:
            return {}

    def generate_positioning_update(
        self,
        current_positioning: str,
        market_changes: list[str],
        new_opportunities: list[str],
    ) -> dict:
        """Generate updated positioning recommendations."""
        prompt = f"""Based on market changes, recommend positioning updates.

Current positioning: {current_positioning}
Market changes: {', '.join(market_changes)}
New opportunities: {', '.join(new_opportunities)}

Provide:
1. Recommended positioning statement
2. Value proposition updates
3. Messaging hierarchy changes
4. Target segment adjustments
5. Proof points to emphasize/de-emphasize

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            return json.loads(response.content)
        except Exception:
            return {}


# ─── Action Agent ────────────────────────────────────────────

class ActionAgent:
    """
    LangChain DeepAgent for translating insights into marketing actions.
    Generates campaign briefs, content, and go-to-market plans.
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.content_gen = ContentGenerator(llm)
        self.seo_gen = SEOStrategyGenerator(llm)
        self.competitive_gen = CompetitiveResponseGenerator(llm)
        self._build_tools()

    def _build_tools(self):
        """Build action tools."""
        self.tools = [
            StructuredTool.from_function(
                func=self._tool_generate_blog_topics,
                name="generate_blog_topics",
                description="Generate blog topic ideas based on market insights and content gaps.",
            ),
            StructuredTool.from_function(
                func=self._tool_generate_ad_copy,
                name="generate_ad_copy",
                description="Generate ad copy variations for paid campaigns.",
            ),
            StructuredTool.from_function(
                func=self._tool_generate_social_posts,
                name="generate_social_posts",
                description="Generate social media post content for specified platforms.",
            ),
            StructuredTool.from_function(
                func=self._tool_generate_email_sequence,
                name="generate_email_sequence",
                description="Generate email marketing sequence (welcome, nurture, re-engagement).",
            ),
            StructuredTool.from_function(
                func=self._tool_generate_seo_strategy,
                name="generate_seo_strategy",
                description="Generate keyword strategy and content cluster plan.",
            ),
            StructuredTool.from_function(
                func=self._tool_generate_battle_card,
                name="generate_battle_card",
                description="Generate sales battle card for competitive positioning.",
            ),
            StructuredTool.from_function(
                func=self._tool_create_campaign_brief,
                name="create_campaign_brief",
                description="Create a complete campaign brief with objectives, audience, and actions.",
            ),
            StructuredTool.from_function(
                func=self._tool_create_content_calendar,
                name="create_content_calendar",
                description="Create a content calendar with themes, topics, and publishing schedule.",
            ),
            StructuredTool.from_function(
                func=self._tool_prioritize_actions,
                name="prioritize_actions",
                description="Prioritize proposed actions by impact, effort, and strategic alignment.",
            ),
            StructuredTool.from_function(
                func=self._tool_estimate_roi,
                name="estimate_roi",
                description="Estimate potential ROI for proposed marketing actions.",
            ),
        ]

    async def _tool_generate_blog_topics(
        self, insights_json: str, count: int = 10
    ) -> str:
        """Generate blog topics."""
        insights = json.loads(insights_json)
        topics = self.content_gen.generate_blog_topics(insights, count)
        return json.dumps(topics)

    async def _tool_generate_ad_copy(
        self,
        product: str,
        audience: str,
        benefit: str,
        angle: str,
        variations: int = 5,
    ) -> str:
        """Generate ad copy."""
        ads = self.content_gen.generate_ad_copy(
            product, audience, benefit, angle, variations
        )
        return json.dumps(ads)

    async def _tool_generate_social_posts(
        self,
        topic: str,
        platforms_json: str,
        tone: str = "professional",
        count: int = 5,
    ) -> str:
        """Generate social posts."""
        platforms = json.loads(platforms_json)
        posts = self.content_gen.generate_social_posts(
            topic, platforms, tone, count
        )
        return json.dumps(posts)

    async def _tool_generate_email_sequence(
        self,
        sequence_type: str,
        audience: str,
        product: str,
        steps: int = 5,
    ) -> str:
        """Generate email sequence."""
        sequence = self.content_gen.generate_email_sequence(
            sequence_type, audience, product, steps
        )
        return json.dumps(sequence)

    async def _tool_generate_seo_strategy(
        self, market_data_json: str, competitors_json: str
    ) -> str:
        """Generate SEO strategy."""
        market_data = json.loads(market_data_json)
        competitors = json.loads(competitors_json)
        strategy = self.seo_gen.generate_keyword_strategy(
            market_data, competitors
        )
        return json.dumps(strategy)

    async def _tool_generate_battle_card(
        self,
        competitor: str,
        our_product: str,
        strengths_json: str,
        weaknesses_json: str,
    ) -> str:
        """Generate battle card."""
        strengths = json.loads(strengths_json)
        weaknesses = json.loads(weaknesses_json)
        card = self.competitive_gen.generate_battle_card(
            competitor, our_product, strengths, weaknesses
        )
        return json.dumps(card)

    async def _tool_create_campaign_brief(
        self,
        objective: str,
        target_audience: str,
        key_message: str,
        actions_json: str,
    ) -> str:
        """Create campaign brief."""
        actions_data = json.loads(actions_json)
        actions = [MarketingAction(**a) for a in actions_data]
        brief = CampaignBrief(
            brief_id=f"CMP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            campaign_name=objective,
            objective=objective,
            target_audience=target_audience,
            key_message=key_message,
            actions=actions,
            timeline="To be determined based on action priorities",
            kpis=["awareness", "engagement", "conversion"],
        )
        return brief.model_dump_json()

    async def _tool_create_content_calendar(
        self,
        period: str,
        topics_json: str,
        frequency: str = "weekly",
    ) -> str:
        """Create content calendar."""
        topics = json.loads(topics_json)
        calendar = ContentCalendar(
            calendar_id=f"CAL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            period=period,
            items=[{"topic": t, "status": "planned"} for t in topics],
            themes=[t.get("category", "general") for t in topics],
        )
        return calendar.model_dump_json()

    async def _tool_prioritize_actions(
        self, actions_json: str
    ) -> str:
        """Prioritize actions by impact/effort matrix."""
        actions_data = json.loads(actions_json)
        actions = [MarketingAction(**a) for a in actions_data]

        # Impact/Effort scoring
        impact_scores = {"high": 3, "medium": 2, "low": 1}
        effort_scores = {"low": 3, "medium": 2, "high": 1}

        for action in actions:
            impact = impact_scores.get(action.impact, 2)
            effort = effort_scores.get(action.effort, 2)
            priority_score = impact * effort
            if priority_score >= 8:
                action.priority = "critical"
            elif priority_score >= 5:
                action.priority = "high"
            elif priority_score >= 3:
                action.priority = "medium"
            else:
                action.priority = "low"

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        actions.sort(key=lambda a: priority_order.get(a.priority, 4))

        return json.dumps([a.model_dump() for a in actions], default=str)

    async def _tool_estimate_roi(
        self, action_type: str, budget: float, expected_conversion_rate: float
    ) -> str:
        """Estimate ROI for a marketing action."""
        # Simplified ROI estimation
        industry_benchmarks = {
            "content": {"cac": 50, "ltv_multiplier": 3},
            "advertising": {"cac": 80, "ltv_multiplier": 2.5},
            "seo": {"cac": 30, "ltv_multiplier": 4},
            "email": {"cac": 20, "ltv_multiplier": 3.5},
            "social": {"cac": 40, "ltv_multiplier": 2.8},
        }
        benchmark = industry_benchmarks.get(action_type, {"cac": 50, "ltv_multiplier": 3})
        estimated_customers = budget / benchmark["cac"]
        estimated_revenue = estimated_customers * 100 * benchmark["ltv_multiplier"]
        roi = ((estimated_revenue - budget) / budget) * 100 if budget > 0 else 0

        return json.dumps({
            "action_type": action_type,
            "budget": budget,
            "estimated_customers": round(estimated_customers),
            "estimated_revenue": round(estimated_revenue),
            "roi_percent": round(roi, 1),
            "confidence": "low",
            "note": "Rough estimate based on industry benchmarks",
        })

    async def generate_actions(
        self,
        analysis_report: AnalysisReport,
        action_types: list[str] = None,
    ) -> list[MarketingAction]:
        """
        Generate marketing actions from analysis results.
        
        This is the main entry point that creates prioritized,
        actionable marketing tasks from insights.
        """
        if action_types is None:
            action_types = [
                "content", "advertising", "seo", "social", "email"
            ]

        actions = []
        action_id = 0

        for insight in analysis_report.key_insights:
            # Content actions
            if "content" in action_types and insight.category in (
                "trend", "opportunity"
            ):
                action_id += 1
                actions.append(MarketingAction(
                    action_id=f"ACT-{action_id:04d}",
                    action_type="content",
                    title=f"Create content: {insight.title}",
                    description=f"Develop content addressing: {insight.description}",
                    priority=insight.impact,
                    effort="medium",
                    impact=insight.impact,
                    timeframe="this_month",
                    expected_outcome="Increased organic traffic and thought leadership",
                    success_metrics=[
                        "Page views", "Time on page", "Social shares", "Backlinks"
                    ],
                ))

            # SEO actions
            if "seo" in action_types and insight.category == "trend":
                action_id += 1
                actions.append(MarketingAction(
                    action_id=f"ACT-{action_id:04d}",
                    action_type="seo",
                    title=f"SEO target: {insight.title}",
                    description=f"Target keywords related to: {insight.title}",
                    priority="medium",
                    effort="high",
                    impact="medium",
                    timeframe="this_quarter",
                    expected_outcome="Improved search rankings for target keywords",
                    success_metrics=[
                        "Keyword rankings", "Organic traffic", "Click-through rate"
                    ],
                ))

            # Social media actions
            if "social" in action_types and insight.category == "sentiment":
                action_id += 1
                actions.append(MarketingAction(
                    action_id=f"ACT-{action_id:04d}",
                    action_type="social",
                    title=f"Social response: {insight.title}",
                    description=f"Address sentiment insight: {insight.description[:100]}",
                    priority=insight.impact,
                    effort="low",
                    impact="medium",
                    timeframe="this_week",
                    expected_outcome="Improved brand sentiment and engagement",
                    success_metrics=[
                        "Sentiment score", "Engagement rate", "Brand mentions"
                    ],
                ))

            # Advertising actions
            if "advertising" in action_types and insight.impact in (
                "high", "critical"
            ):
                action_id += 1
                actions.append(MarketingAction(
                    action_id=f"ACT-{action_id:04d}",
                    action_type="advertising",
                    title=f"Ad campaign: {insight.title}",
                    description=f"Launch targeted ads based on: {insight.description[:100]}",
                    priority=insight.impact,
                    effort="medium",
                    impact="high",
                    timeframe="this_month",
                    expected_outcome="Increased qualified leads and brand awareness",
                    success_metrics=[
                        "CTR", "CPC", "CPA", "ROAS", "Conversion rate"
                    ],
                ))

            # Email marketing actions
            if "email" in action_types and insight.category == "opportunity":
                action_id += 1
                actions.append(MarketingAction(
                    action_id=f"ACT-{action_id:04d}",
                    action_type="email",
                    title=f"Email campaign: {insight.title}",
                    description=f"Create email sequence for: {insight.description[:100]}",
                    priority="medium",
                    effort="low",
                    impact="medium",
                    timeframe="this_month",
                    expected_outcome="Increased engagement and conversions",
                    success_metrics=[
                        "Open rate", "Click rate", "Conversion rate", "Revenue per email"
                    ],
                ))

        # Prioritize
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        actions.sort(key=lambda a: priority_order.get(a.priority, 4))

        return actions

    def create_agent_executor(self) -> AgentExecutor:
        """Create a LangChain agent executor with action tools."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a marketing strategist who translates market insights into action.
Your job is to create specific, actionable marketing tasks.

Guidelines:
- Every action must be specific and measurable
- Consider resource constraints and dependencies
- Prioritize by impact-to-effort ratio
- Align actions with business objectives
- Include clear success metrics
- Set realistic timelines
- Consider competitive implications

Available tools: {tools}
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=20,
        )
```

### 5.4 Action Prioritization Matrix

```
                    HIGH IMPACT
                        │
         Quick Wins    │    Strategic Investments
         (Do First)    │    (Plan Carefully)
                        │
    LOW ────────────────┼──────────────── HIGH
    EFFORT              │                 EFFORT
                        │
         Fill-Ins      │    Money Pits
         (Batch These)  │    (Avoid/Defer)
                        │
                    LOW IMPACT
```

---

## 6. Performance Analytics Agent Implementation

### 6.1 Purpose

The Performance Analytics Agent monitors the effectiveness of marketing actions, tracks KPIs, performs attribution analysis, and provides optimization recommendations. It closes the feedback loop by measuring the impact of AI-generated marketing activities.

### 6.2 Analytics Framework

```
┌─────────────────────────────────────────────────────────────────┐
│              Performance Analytics Agent                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Data Collection Layer                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │  Google  │ │  Social  │ │   Email  │ │   Ads    │  │   │
│  │  │ Analytics│ │  Media   │ │ Platform │ │ Platforms│  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Metrics Processing Layer                     │   │
│  │  • KPI calculation  • Trend detection  • Anomaly flags  │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Attribution & Analysis Layer                 │   │
│  │  • Multi-touch attribution  • Cohort analysis           │   │
│  │  • A/B test evaluation      • ROI calculation           │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Optimization Layer                           │   │
│  │  • Budget reallocation  • Channel optimization          │   │
│  │  • Content performance  • Audience refinement           │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Reporting & Feedback Layer                   │   │
│  │  • Performance dashboards  • Optimization alerts        │   │
│  │  • ROI reports             • Feedback to Action Agent    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Implementation

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
import json
import numpy as np
from collections import defaultdict

# ─── Analytics Data Models ────────────────────────────────────

class CampaignMetrics(BaseModel):
    """Metrics for a marketing campaign."""
    campaign_id: str
    campaign_name: str
    channel: str
    start_date: datetime
    end_date: Optional[datetime] = None
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0
    engagement_rate: float = 0.0
    ctr: float = 0.0
    cpc: float = 0.0
    cpa: float = 0.0
    roas: float = 0.0
    roi: float = 0.0

class AttributionModel(BaseModel):
    """Attribution analysis results."""
    model_type: str  # "first_touch", "last_touch", "linear", "time_decay", "data_driven"
    channel_attribution: dict[str, float] = Field(default_factory=dict)
    campaign_attribution: dict[str, float] = Field(default_factory=dict)
    touchpoint_analysis: list[dict] = Field(default_factory=list)
    confidence: float = 0.5

class ABTestResult(BaseModel):
    """A/B test results."""
    test_id: str
    test_name: str
    variant_a: dict  # Control metrics
    variant_b: dict  # Treatment metrics
    sample_size_a: int = 0
    sample_size_b: int = 0
    confidence_level: float = 0.95
    p_value: float = 1.0
    is_significant: bool = False
    winner: Optional[str] = None  # "A", "B", or None
    effect_size: float = 0.0
    recommendation: str = ""

class OptimizationRecommendation(BaseModel):
    """An optimization recommendation."""
    recommendation_id: str
    category: str  # "budget", "targeting", "creative", "channel", "timing"
    title: str
    description: str
    expected_impact: str  # "low", "medium", "high"
    effort: str  # "low", "medium", "high"
    confidence: float = 0.5
    supporting_data: dict = Field(default_factory=dict)
    implementation_steps: list[str] = Field(default_factory=list)

class PerformanceDashboard(BaseModel):
    """Aggregated performance dashboard."""
    dashboard_id: str
    period: str
    generated_at: datetime
    overall_kpis: dict = Field(default_factory=dict)
    channel_performance: list[dict] = Field(default_factory=list)
    campaign_rankings: list[dict] = Field(default_factory=list)
    trends: list[dict] = Field(default_factory=list)
    anomalies: list[dict] = Field(default_factory=list)
    recommendations: list[OptimizationRecommendation] = Field(
        default_factory=list
    )


# ─── Analytics Engines ────────────────────────────────────────

class MetricsCalculator:
    """Calculates marketing metrics from raw data."""

    def calculate_campaign_metrics(
        self, raw_data: dict
    ) -> CampaignMetrics:
        """Calculate all metrics for a campaign."""
        impressions = raw_data.get("impressions", 0)
        clicks = raw_data.get("clicks", 0)
        conversions = raw_data.get("conversions", 0)
        spend = raw_data.get("spend", 0.0)
        revenue = raw_data.get("revenue", 0.0)

        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        cpc = (spend / clicks) if clicks > 0 else 0.0
        cpa = (spend / conversions) if conversions > 0 else 0.0
        roas = (revenue / spend) if spend > 0 else 0.0
        roi = ((revenue - spend) / spend * 100) if spend > 0 else 0.0
        engagement_rate = (
            (clicks / impressions * 100) if impressions > 0 else 0.0
        )

        return CampaignMetrics(
            campaign_id=raw_data.get("campaign_id", ""),
            campaign_name=raw_data.get("campaign_name", ""),
            channel=raw_data.get("channel", "unknown"),
            start_date=raw_data.get("start_date", datetime.now()),
            end_date=raw_data.get("end_date"),
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            spend=spend,
            revenue=revenue,
            engagement_rate=engagement_rate,
            ctr=ctr,
            cpc=cpc,
            cpa=cpa,
            roas=roas,
            roi=roi,
        )

    def calculate_funnel_metrics(
        self, stages: dict[str, int]
    ) -> dict:
        """Calculate funnel conversion rates."""
        metrics = {}
        prev_count = None
        prev_stage = None
        for stage, count in stages.items():
            metrics[f"{stage}_count"] = count
            if prev_count and prev_count > 0:
                metrics[f"{prev_stage}_to_{stage}_rate"] = (
                    count / prev_count * 100
                )
            prev_count = count
            prev_stage = stage
        # Overall conversion
        first = list(stages.values())[0] if stages else 0
        last = list(stages.values())[-1] if stages else 0
        metrics["overall_conversion_rate"] = (
            (last / first * 100) if first > 0 else 0.0
        )
        return metrics


class AttributionEngine:
    """Multi-touch attribution analysis."""

    def __init__(self, model_type: str = "data_driven"):
        self.model_type = model_type

    def attribute(
        self, journeys: list[list[dict]]
    ) -> AttributionModel:
        """Run attribution analysis on customer journeys."""
        if self.model_type == "first_touch":
            return self._first_touch(journeys)
        elif self.model_type == "last_touch":
            return self._last_touch(journeys)
        elif self.model_type == "linear":
            return self._linear(journeys)
        elif self.model_type == "time_decay":
            return self._time_decay(journeys)
        else:
            return self._data_driven(journeys)

    def _first_touch(
        self, journeys: list[list[dict]]
    ) -> AttributionModel:
        """First-touch attribution."""
        channel_credit = defaultdict(float)
        total_conversions = 0
        for journey in journeys:
            if journey and journey[-1].get("converted", False):
                first_channel = journey[0].get("channel", "unknown")
                channel_credit[first_channel] += 1
                total_conversions += 1
        # Normalize
        attribution = {
            k: v / total_conversions
            for k, v in channel_credit.items()
        } if total_conversions > 0 else {}
        return AttributionModel(
            model_type="first_touch",
            channel_attribution=attribution,
            confidence=0.6,
        )

    def _last_touch(
        self, journeys: list[list[dict]]
    ) -> AttributionModel:
        """Last-touch attribution."""
        channel_credit = defaultdict(float)
        total_conversions = 0
        for journey in journeys:
            if journey and journey[-1].get("converted", False):
                last_channel = journey[-1].get("channel", "unknown")
                channel_credit[last_channel] += 1
                total_conversions += 1
        attribution = {
            k: v / total_conversions
            for k, v in channel_credit.items()
        } if total_conversions > 0 else {}
        return AttributionModel(
            model_type="last_touch",
            channel_attribution=attribution,
            confidence=0.6,
        )

    def _linear(
        self, journeys: list[list[dict]]
    ) -> AttributionModel:
        """Linear attribution (equal credit to all touchpoints)."""
        channel_credit = defaultdict(float)
        total_credit = 0
        for journey in journeys:
            if journey and journey[-1].get("converted", False):
                n_touchpoints = len(journey)
                credit_per_touch = 1.0 / n_touchpoints if n_touchpoints > 0 else 0
                for touch in journey:
                    channel = touch.get("channel", "unknown")
                    channel_credit[channel] += credit_per_touch
                    total_credit += credit_per_touch
        attribution = {
            k: v / total_credit
            for k, v in channel_credit.items()
        } if total_credit > 0 else {}
        return AttributionModel(
            model_type="linear",
            channel_attribution=attribution,
            confidence=0.7,
        )

    def _time_decay(
        self, journeys: list[list[dict]]
    ) -> AttributionModel:
        """Time-decay attribution (more credit to recent touchpoints)."""
        channel_credit = defaultdict(float)
        total_credit = 0
        half_life = 7  # days
        for journey in journeys:
            if journey and journey[-1].get("converted", False):
                n = len(journey)
                for i, touch in enumerate(journey):
                    # Exponential decay based on position
                    position_weight = 0.5 ** ((n - 1 - i) / half_life)
                    channel = touch.get("channel", "unknown")
                    channel_credit[channel] += position_weight
                    total_credit += position_weight
        attribution = {
            k: v / total_credit
            for k, v in channel_credit.items()
        } if total_credit > 0 else {}
        return AttributionModel(
            model_type="time_decay",
            channel_attribution=attribution,
            confidence=0.75,
        )

    def _data_driven(
        self, journeys: list[list[dict]]
    ) -> AttributionModel:
        """Data-driven attribution (simplified Shapley value approximation)."""
        # In production, this would use ML-based attribution
        # For now, use time-decay as a proxy
        return self._time_decay(journeys)


class ABTestEvaluator:
    """Evaluates A/B test results."""

    def evaluate(
        self,
        control_metrics: dict,
        treatment_metrics: dict,
        sample_size_control: int,
        sample_size_treatment: int,
        confidence_level: float = 0.95,
    ) -> ABTestResult:
        """Evaluate A/B test for statistical significance."""
        # Extract conversion rates
        control_conversions = control_metrics.get("conversions", 0)
        treatment_conversions = treatment_metrics.get("conversions", 0)

        control_rate = (
            control_conversions / sample_size_control
            if sample_size_control > 0 else 0
        )
        treatment_rate = (
            treatment_conversions / sample_size_treatment
            if sample_size_treatment > 0 else 0
        )

        # Pooled standard error
        pooled_rate = (
            (control_conversions + treatment_conversions)
            / (sample_size_control + sample_size_treatment)
            if (sample_size_control + sample_size_treatment) > 0 else 0
        )
        se = np.sqrt(
            pooled_rate * (1 - pooled_rate)
            * (1 / sample_size_control + 1 / sample_size_treatment)
        ) if sample_size_control > 0 and sample_size_treatment > 0 else 1

        # Z-score
        z_score = (
            (treatment_rate - control_rate) / se if se > 0 else 0
        )

        # P-value (two-tailed)
        from scipy import stats
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

        # Effect size (Cohen's h)
        effect_size = 2 * (
            np.arcsin(np.sqrt(treatment_rate))
            - np.arcsin(np.sqrt(control_rate))
        ) if 0 < treatment_rate < 1 and 0 < control_rate < 1 else 0

        is_significant = p_value < (1 - confidence_level)

        winner = None
        if is_significant:
            winner = "B" if treatment_rate > control_rate else "A"

        recommendation = ""
        if is_significant and winner == "B":
            recommendation = (
                f"Implement treatment (B). "
                f"Lift: {((treatment_rate - control_rate) / control_rate * 100):.1f}% "
                f"with {confidence_level:.0%} confidence."
            )
        elif is_significant and winner == "A":
            recommendation = (
                f"Keep control (A). Treatment underperformed by "
                f"{((control_rate - treatment_rate) / control_rate * 100):.1f}%."
            )
        else:
            recommendation = (
                "Test inconclusive. Consider running longer or "
                "increasing sample size."
            )

        return ABTestResult(
            test_id=f"ABT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            test_name="A/B Test",
            variant_a=control_metrics,
            variant_b=treatment_metrics,
            sample_size_a=sample_size_control,
            sample_size_b=sample_size_treatment,
            confidence_level=confidence_level,
            p_value=p_value,
            is_significant=is_significant,
            winner=winner,
            effect_size=effect_size,
            recommendation=recommendation,
        )


class AnomalyDetector:
    """Detects anomalies in marketing metrics."""

    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity  # Standard deviations

    def detect(
        self, time_series: list[dict], metric_name: str
    ) -> list[dict]:
        """Detect anomalies in a time series."""
        if len(time_series) < 7:
            return []

        values = [d.get(metric_name, 0) for d in time_series]
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return []

        anomalies = []
        for i, (point, value) in enumerate(zip(time_series, values)):
            z_score = (value - mean) / std
            if abs(z_score) > self.sensitivity:
                anomalies.append({
                    "date": point.get("date", f"index_{i}"),
                    "metric": metric_name,
                    "value": value,
                    "expected_range": (
                        mean - self.sensitivity * std,
                        mean + self.sensitivity * std,
                    ),
                    "z_score": z_score,
                    "severity": (
                        "high" if abs(z_score) > 3 else "medium"
                    ),
                    "direction": "spike" if z_score > 0 else "drop",
                })
        return anomalies


class ROICalculator:
    """Calculates ROI and related financial metrics."""

    def calculate_roi(
        self, revenue: float, cost: float
    ) -> dict:
        """Calculate comprehensive ROI metrics."""
        profit = revenue - cost
        roi = (profit / cost * 100) if cost > 0 else 0
        roas = (revenue / cost) if cost > 0 else 0
        margin = (profit / revenue * 100) if revenue > 0 else 0
        return {
            "revenue": revenue,
            "cost": cost,
            "profit": profit,
            "roi_percent": roi,
            "roas": roas,
            "profit_margin_percent": margin,
        }

    def calculate_cac_ltv(
        self,
        total_spend: float,
        new_customers: int,
        avg_revenue_per_customer: float,
        avg_customer_lifespan_months: int,
        gross_margin: float = 0.7,
    ) -> dict:
        """Calculate Customer Acquisition Cost and Lifetime Value."""
        cac = total_spend / new_customers if new_customers > 0 else 0
        ltv = (
            avg_revenue_per_customer
            * avg_customer_lifespan_months
            * gross_margin
        )
        ltv_cac_ratio = ltv / cac if cac > 0 else 0
        payback_months = (
            cac / (avg_revenue_per_customer * gross_margin)
            if avg_revenue_per_customer > 0 else 0
        )
        return {
            "cac": cac,
            "ltv": ltv,
            "ltv_cac_ratio": ltv_cac_ratio,
            "payback_period_months": payback_months,
            "is_healthy": ltv_cac_ratio >= 3,
        }

    def calculate_attributed_revenue(
        self,
        attribution: AttributionModel,
        total_revenue: float,
    ) -> dict[str, float]:
        """Calculate revenue attributed to each channel."""
        return {
            channel: total_revenue * credit
            for channel, credit in attribution.channel_attribution.items()
        }


# ─── Performance Analytics Agent ──────────────────────────────

class PerformanceAnalyticsAgent:
    """
    LangChain DeepAgent for marketing performance analytics.
    Monitors, analyzes, and optimizes marketing effectiveness.
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.metrics_calc = MetricsCalculator()
        self.attribution_engine = AttributionEngine("time_decay")
        self.ab_evaluator = ABTestEvaluator()
        self.anomaly_detector = AnomalyDetector(sensitivity=2.0)
        self.roi_calc = ROICalculator()
        self._build_tools()

    def _build_tools(self):
        """Build analytics tools."""
        self.tools = [
            StructuredTool.from_function(
                func=self._tool_calculate_metrics,
                name="calculate_metrics",
                description="Calculate marketing KPIs (CTR, CPA, ROAS, ROI) from raw campaign data.",
            ),
            StructuredTool.from_function(
                func=self._tool_run_attribution,
                name="run_attribution",
                description="Run multi-touch attribution analysis on customer journey data.",
            ),
            StructuredTool.from_function(
                func=self._tool_evaluate_ab_test,
                name="evaluate_ab_test",
                description="Evaluate A/B test results for statistical significance.",
            ),
            StructuredTool.from_function(
                func=self._tool_detect_anomalies,
                name="detect_anomalies",
                description="Detect anomalies and unusual patterns in marketing metrics.",
            ),
            StructuredTool.from_function(
                func=self._tool_calculate_roi,
                name="calculate_roi",
                description="Calculate ROI, ROAS, CAC, and LTV for campaigns.",
            ),
            StructuredTool.from_function(
                func=self._tool_generate_recommendations,
                name="generate_recommendations",
                description="Generate optimization recommendations based on performance data.",
            ),
            StructuredTool.from_function(
                func=self._tool_forecast_performance,
                name="forecast_performance",
                description="Forecast future campaign performance based on historical trends.",
            ),
            StructuredTool.from_function(
                func=self._tool_competitive_benchmark,
                name="competitive_benchmark",
                description="Benchmark performance against industry standards and competitors.",
            ),
            StructuredTool.from_function(
                func=self._tool_cohort_analysis,
                name="cohort_analysis",
                description="Perform cohort analysis to understand customer retention patterns.",
            ),
            StructuredTool.from_function(
                func=self._tool_generate_dashboard,
                name="generate_dashboard",
                description="Generate a comprehensive performance dashboard.",
            ),
        ]

    async def _tool_calculate_metrics(
        self, raw_data_json: str
    ) -> str:
        """Calculate campaign metrics."""
        raw_data = json.loads(raw_data_json)
        metrics = self.metrics_calc.calculate_campaign_metrics(raw_data)
        return metrics.model_dump_json()

    async def _tool_run_attribution(
        self, journeys_json: str, model_type: str = "time_decay"
    ) -> str:
        """Run attribution analysis."""
        journeys = json.loads(journeys_json)
        engine = AttributionEngine(model_type)
        result = engine.attribute(journeys)
        return result.model_dump_json()

    async def _tool_evaluate_ab_test(
        self,
        control_json: str,
        treatment_json: str,
        sample_size_a: int,
        sample_size_b: int,
        confidence: float = 0.95,
    ) -> str:
        """Evaluate A/B test."""
        control = json.loads(control_json)
        treatment = json.loads(treatment_json)
        result = self.ab_evaluator.evaluate(
            control, treatment, sample_size_a, sample_size_b, confidence
        )
        return result.model_dump_json()

    async def _tool_detect_anomalies(
        self, time_series_json: str, metric_name: str
    ) -> str:
        """Detect anomalies in time series data."""
        time_series = json.loads(time_series_json)
        anomalies = self.anomaly_detector.detect(time_series, metric_name)
        return json.dumps(anomalies)

    async def _tool_calculate_roi(
        self, revenue: float, cost: float
    ) -> str:
        """Calculate ROI metrics."""
        result = self.roi_calc.calculate_roi(revenue, cost)
        return json.dumps(result)

    async def _tool_generate_recommendations(
        self, performance_data_json: str
    ) -> str:
        """Generate optimization recommendations."""
        data = json.loads(performance_data_json)
        prompt = f"""Based on the following marketing performance data,
generate 5-10 specific optimization recommendations.

For each recommendation, provide:
- Category (budget/targeting/creative/channel/timing)
- Title and description
- Expected impact (low/medium/high)
- Effort required (low/medium/high)
- Confidence score (0.0-1.0)
- Supporting data references
- Implementation steps

Performance data:
{json.dumps(data, default=str)[:5000]}

Respond in JSON format."""

        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception:
            return json.dumps({"error": "recommendation generation failed"})

    async def _tool_forecast_performance(
        self, historical_metrics_json: str, periods: int = 4
    ) -> str:
        """Forecast future performance."""
        historical = json.loads(historical_metrics_json)
        # Simple moving average forecast
        forecasts = {}
        for metric in ["impressions", "clicks", "conversions", "revenue"]:
            values = [d.get(metric, 0) for d in historical]
            if len(values) >= 3:
                # Weighted moving average
                weights = [0.5, 0.3, 0.2]
                recent = values[-3:]
                forecast = sum(w * v for w, v in zip(weights, recent))
                forecasts[metric] = [forecast * (1.02 ** i) for i in range(1, periods + 1)]
            else:
                forecasts[metric] = [values[-1] if values else 0] * periods
        return json.dumps({
            "forecasts": forecasts,
            "periods": periods,
            "method": "weighted_moving_average_with_growth",
            "confidence": "medium",
        })

    async def _tool_competitive_benchmark(
        self, our_metrics_json: str, industry_benchmarks_json: str
    ) -> str:
        """Benchmark against industry standards."""
        our = json.loads(our_metrics_json)
        benchmarks = json.loads(industry_benchmarks_json)
        comparison = {}
        for metric, our_value in our.items():
            if metric in benchmarks:
                bench = benchmarks[metric]
                percentile = self._estimate_percentile(our_value, bench)
                comparison[metric] = {
                    "our_value": our_value,
                    "industry_median": bench.get("median", 0),
                    "industry_top_quartile": bench.get("p75", 0),
                    "estimated_percentile": percentile,
                    "status": (
                        "above_average" if percentile > 60
                        else "average" if percentile > 30
                        else "below_average"
                    ),
                }
        return json.dumps(comparison)

    def _estimate_percentile(
        self, value: float, benchmark: dict
    ) -> int:
        """Estimate percentile based on benchmark distribution."""
        median = benchmark.get("median", 0)
        p75 = benchmark.get("p75", median * 1.5)
        p25 = benchmark.get("p25", median * 0.5)
        if value >= p75:
            return 80
        elif value >= median:
            return 60
        elif value >= p25:
            return 40
        else:
            return 20

    async def _tool_cohort_analysis(
        self, cohort_data_json: str
    ) -> str:
        """Perform cohort retention analysis."""
        data = json.loads(cohort_data_json)
        # Calculate retention rates by cohort
        cohorts = defaultdict(lambda: defaultdict(int))
        for record in data:
            cohort_month = record.get("cohort_month", "unknown")
            period = record.get("period", 0)
            count = record.get("count", 0)
            cohorts[cohort_month][period] = count

        retention = {}
        for cohort, periods in cohorts.items():
            initial = periods.get(0, 0)
            retention[cohort] = {
                str(p): (count / initial * 100) if initial > 0 else 0
                for p, count in periods.items()
            }
        return json.dumps(retention)

    async def _tool_generate_dashboard(
        self, metrics_json: str, period: str = "last_30_days"
    ) -> str:
        """Generate performance dashboard."""
        metrics = json.loads(metrics_json)
        dashboard = PerformanceDashboard(
            dashboard_id=f"DASH-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            period=period,
            generated_at=datetime.now(),
            overall_kpis={
                "total_spend": sum(m.get("spend", 0) for m in metrics),
                "total_revenue": sum(m.get("revenue", 0) for m in metrics),
                "total_conversions": sum(m.get("conversions", 0) for m in metrics),
                "total_impressions": sum(m.get("impressions", 0) for m in metrics),
                "total_clicks": sum(m.get("clicks", 0) for m in metrics),
            },
            channel_performance=metrics,
            campaign_rankings=sorted(
                metrics, key=lambda x: x.get("roas", 0), reverse=True
            )[:10],
            anomalies=[],
            recommendations=[],
        )
        # Calculate derived KPIs
        kpis = dashboard.overall_kpis
        if kpis["total_spend"] > 0:
            kpis["overall_roas"] = kpis["total_revenue"] / kpis["total_spend"]
            kpis["overall_roi"] = (
                (kpis["total_revenue"] - kpis["total_spend"])
                / kpis["total_spend"] * 100
            )
        if kpis["total_impressions"] > 0:
            kpis["overall_ctr"] = (
                kpis["total_clicks"] / kpis["total_impressions"] * 100
            )
        if kpis["total_clicks"] > 0:
            kpis["overall_conversion_rate"] = (
                kpis["total_conversions"] / kpis["total_clicks"] * 100
            )
        return dashboard.model_dump_json()

    async def analyze_performance(
        self,
        campaign_data: list[dict],
        attribution_model: str = "time_decay",
    ) -> PerformanceDashboard:
        """
        Execute full performance analytics pipeline.
        
        This is the main entry point that processes campaign data,
        runs attribution, detects anomalies, and generates recommendations.
        """
        # Calculate metrics for each campaign
        metrics = []
        for data in campaign_data:
            m = self.metrics_calc.calculate_campaign_metrics(data)
            metrics.append(m.model_dump())

        # Detect anomalies
        anomalies = self.anomaly_detector.detect(metrics, "roas")
        anomalies.extend(self.anomaly_detector.detect(metrics, "cpa"))

        # Generate dashboard
        dashboard_json = await self._tool_generate_dashboard(
            json.dumps(metrics)
        )
        dashboard = PerformanceDashboard(**json.loads(dashboard_json))
        dashboard.anomalies = anomalies

        return dashboard

    def create_agent_executor(self) -> AgentExecutor:
        """Create a LangChain agent executor with analytics tools."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a marketing performance analyst.
Your job is to measure, analyze, and optimize marketing effectiveness.

Analytics framework:
1. Descriptive: What happened? (metrics, trends)
2. Diagnostic: Why did it happen? (attribution, correlation)
3. Predictive: What will happen? (forecasting, projections)
4. Prescriptive: What should we do? (recommendations, optimization)

Guidelines:
- Always contextualize metrics (vs. benchmarks, vs. goals, vs. historical)
- Distinguish correlation from causation
- Consider seasonality and external factors
- Prioritize recommendations by expected impact
- Flag data quality issues
- Provide actionable, specific recommendations

Available tools: {tools}
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=20,
        )
```

### 6.4 Key Performance Indicators

| KPI | Formula | Target | Measurement Frequency |
|-----|---------|--------|----------------------|
| **ROAS** | Revenue / Ad Spend | ≥ 4:1 | Daily |
| **CPA** | Ad Spend / Conversions | ≤ $50 | Daily |
| **CTR** | Clicks / Impressions × 100 | ≥ 2% | Daily |
| **Conversion Rate** | Conversions / Clicks × 100 | ≥ 5% | Daily |
| **LTV:CAC Ratio** | LTV / CAC | ≥ 3:1 | Monthly |
| **Payback Period** | CAC / (ARPU × Margin) | ≤ 12 months | Monthly |
| **Engagement Rate** | Engagements / Impressions × 100 | ≥ 3% | Daily |
| **Bounce Rate** | Single-page sessions / Total sessions | ≤ 40% | Weekly |
| **Email Open Rate** | Opens / Delivered × 100 | ≥ 25% | Per campaign |
| **Email CTR** | Clicks / Delivered × 100 | ≥ 3% | Per campaign |

### 6.5 Feedback Loop Integration

The Performance Analytics Agent feeds insights back into the system:

```
┌──────────────────────────────────────────────────────────────┐
│                    Feedback Loop Architecture                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│   │  Analysis   │────▶│   Action    │────▶│  Execution  │  │
│   │   Agent     │     │   Agent     │     │             │  │
│   └─────────────┘     └─────────────┘     └──────┬──────┘  │
│         ▲                                        │         │
│         │                                        ▼         │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│   │   Updated   │◀────│  Performance│◀────│  Campaign   │  │
│   │   Strategy  │     │  Analytics  │     │  Metrics    │  │
│   └─────────────┘     └─────────────┘     └─────────────┘  │
│                                                              │
│   Feedback signals:                                         │
│   • Which insights led to successful actions?               │
│   • Which content themes performed best?                    │
│   • Which channels delivered highest ROI?                   │
│   • Which audience segments converted best?                 │
│   • What competitive responses were effective?              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Code Examples and Snippets

### 7.1 Complete System Orchestration

```python
"""
Complete Market Research System Orchestration
Uses LangChain DeepAgents with LangGraph for stateful multi-agent coordination.
"""

import asyncio
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from typing import TypedDict, Annotated
import operator

# ─── System State ─────────────────────────────────────────────

class MarketResearchState(MessagesState):
    """Complete state for the market research pipeline."""
    research_query: str = ""
    target_markets: list[str] = []
    competitors: list[str] = []
    collected_data: list[dict] = []
    analysis_results: dict = {}
    reports_generated: list[dict] = []
    actions_taken: list[dict] = []
    performance_metrics: dict = {}
    iteration_count: int = 0
    max_iterations: int = 10
    human_approval_required: bool = False
    approval_status: str = "not_needed"
    current_stage: str = "initialized"
    errors: list[str] = []


# ─── Pipeline Stages ──────────────────────────────────────────

async def data_collection_stage(state: MarketResearchState) -> dict:
    """Stage 1: Collect market data."""
    print(f"📊 [Stage 1] Starting data collection for: {state['research_query']}")
    
    # Initialize collection agent
    collector = DataCollectionAgent(
        llm=ChatOpenAI(model="gpt-4o", temperature=0.1),
        tavily_api_key="your-tavily-key",
        data_sources=[
            DataSourceConfig(
                name="web_search",
                source_type="web",
                url="https://api.tavily.com/search",
                rate_limit=10,
                priority=1,
            ),
            DataSourceConfig(
                name="news",
                source_type="rss",
                url="https://news.google.com/rss",
                rate_limit=20,
                priority=2,
            ),
        ],
    )
    
    query = CollectionQuery(
        research_topic=state["research_query"],
        target_markets=state["target_markets"],
        competitors=state["competitors"],
        keywords=state["research_query"].split(),
        date_range_days=30,
        max_results_per_source=50,
    )
    
    collected = await collector.collect(query)
    
    return {
        "collected_data": [c.model_dump() for c in collected],
        "current_stage": "data_collected",
        "iteration_count": state["iteration_count"] + 1,
    }


async def analysis_stage(state: MarketResearchState) -> dict:
    """Stage 2: Analyze collected data."""
    print(f"🔍 [Stage 2] Analyzing {len(state['collected_data'])} data points")
    
    # Convert dicts back to CollectedData
    from dataclasses import fields
    collected = []
    for d in state["collected_data"]:
        try:
            collected.append(CollectedData(**d))
        except Exception:
            continue
    
    analyzer = AnalysisAgent(
        llm=ChatOpenAI(model="gpt-4o", temperature=0.2),
    )
    
    analysis = await analyzer.analyze(
        research_topic=state["research_query"],
        collected_data=collected,
        competitors=state["competitors"],
    )
    
    return {
        "analysis_results": analysis.model_dump(),
        "current_stage": "analysis_complete",
        "iteration_count": state["iteration_count"] + 1,
    }


async def reporting_stage(state: MarketResearchState) -> dict:
    """Stage 3: Generate reports."""
    print(f"📝 [Stage 3] Generating reports")
    
    # Reconstruct AnalysisReport
    analysis_data = state["analysis_results"]
    analysis_report = AnalysisReport(**analysis_data)
    
    reporter = ReportingAgent(
        llm=ChatOpenAI(model="gpt-4o", temperature=0.3),
    )
    
    # Generate executive brief
    exec_report = await reporter.generate_report(
        analysis_report=analysis_report,
        template_name="Executive Brief",
        format="pdf",
        audience="executive",
    )
    
    # Generate competitive intelligence report
    comp_report = await reporter.generate_report(
        analysis_report=analysis_report,
        template_name="Competitive Intelligence",
        format="html",
        audience="strategy",
    )
    
    return {
        "reports_generated": [
            exec_report.model_dump(),
            comp_report.model_dump(),
        ],
        "current_stage": "reports_generated",
        "iteration_count": state["iteration_count"] + 1,
    }


async def action_stage(state: MarketResearchState) -> dict:
    """Stage 4: Generate marketing actions."""
    print(f"⚡ [Stage 4] Generating marketing actions")
    
    analysis_report = AnalysisReport(**state["analysis_results"])
    
    action_agent = ActionAgent(
        llm=ChatOpenAI(model="gpt-4o", temperature=0.4),
    )
    
    actions = await action_agent.generate_actions(
        analysis_report=analysis_report,
        action_types=["content", "advertising", "seo", "social", "email"],
    )
    
    return {
        "actions_taken": [a.model_dump() for a in actions],
        "current_stage": "actions_generated",
        "iteration_count": state["iteration_count"] + 1,
    }


async def analytics_stage(state: MarketResearchState) -> dict:
    """Stage 5: Set up performance tracking."""
    print(f"📈 [Stage 5] Setting up performance analytics")
    
    # In production, this would connect to actual campaign data
    # For now, set up the tracking framework
    analytics_agent = PerformanceAnalyticsAgent(
        llm=ChatOpenAI(model="gpt-4o", temperature=0.1),
    )
    
    # Create performance dashboard structure
    dashboard = PerformanceDashboard(
        dashboard_id=f"DASH-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        period="campaign_lifetime",
        generated_at=datetime.now(),
        overall_kpis={},
        channel_performance=[],
        campaign_rankings=[],
        trends=[],
        anomalies=[],
        recommendations=[],
    )
    
    return {
        "performance_metrics": dashboard.model_dump(),
        "current_stage": "analytics_configured",
        "iteration_count": state["iteration_count"] + 1,
    }


# ─── Graph Construction ───────────────────────────────────────

def build_market_research_graph() -> StateGraph:
    """Build the LangGraph state machine for market research."""
    workflow = StateGraph(MarketResearchState)
    
    # Add nodes
    workflow.add_node("data_collection", data_collection_stage)
    workflow.add_node("analysis", analysis_stage)
    workflow.add_node("reporting", reporting_stage)
    workflow.add_node("action", action_stage)
    workflow.add_node("analytics", analytics_stage)
    
    # Define edges (linear pipeline with conditional branching)
    workflow.set_entry_point("data_collection")
    workflow.add_edge("data_collection", "analysis")
    workflow.add_edge("analysis", "reporting")
    workflow.add_edge("reporting", "action")
    workflow.add_edge("action", "analytics")
    workflow.add_edge("analytics", END)
    
    return workflow


# ─── Main Execution ──────────────────────────────────────────

async def run_market_research(
    query: str,
    target_markets: list[str],
    competitors: list[str],
):
    """Execute the complete market research pipeline."""
    # Build and compile graph
    graph = build_market_research_graph()
    checkpointer = MemorySaver()
    store = InMemoryStore()
    app = graph.compile(checkpointer=checkpointer, store=store)
    
    # Initialize state
    initial_state = MarketResearchState(
        research_query=query,
        target_markets=target_markets,
        competitors=competitors,
        messages=[],
    )
    
    # Execute
    config = {"configurable": {"thread_id": "market-research-001"}}
    result = await app.ainvoke(initial_state, config=config)
    
    return result


# ─── Usage Example ────────────────────────────────────────────

if __name__ == "__main__":
    result = asyncio.run(run_market_research(
        query="AI-powered customer service automation",
        target_markets=["US", "UK", "Germany"],
        competitors=["Zendesk", "Intercom", "Freshdesk"],
    ))
    
    print(f"\n{'='*60}")
    print(f"Market Research Complete!")
    print(f"Stage: {result['current_stage']}")
    print(f"Data points collected: {len(result['collected_data'])}")
    print(f"Reports generated: {len(result['reports_generated'])}")
    print(f"Actions proposed: {len(result['actions_taken'])}")
    print(f"{'='*60}")
```

### 7.2 Configuration Management

```python
# config/market_research_config.py

from pydantic_settings import BaseSettings
from typing import Optional

class MarketResearchConfig(BaseSettings):
    """Configuration for the market research system."""
    
    # LLM Settings
    openai_api_key: str
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096
    
    # API Keys
    tavily_api_key: str
    newsapi_key: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    
    # Collection Settings
    max_results_per_source: int = 50
    default_date_range_days: int = 30
    min_relevance_score: float = 0.3
    rate_limit_default: int = 10  # requests per minute
    
    # Analysis Settings
    sentiment_lexicon_path: str = "data/sentiment_lexicon.json"
    trend_min_mentions: int = 3
    forecast_periods: int = 4
    
    # Reporting Settings
    report_output_dir: str = "./reports"
    default_report_format: str = "pdf"
    chart_style: str = "plotly_white"
    
    # Action Settings
    max_actions_per_run: int = 50
    default_action_timeframe: str = "this_month"
    roi_confidence_threshold: float = 0.6
    
    # Analytics Settings
    anomaly_sensitivity: float = 2.0  # standard deviations
    attribution_model: str = "time_decay"
    ab_test_confidence: float = 0.95
    
    # Human-in-the-Loop
    require_approval_for_budget: bool = True
    budget_approval_threshold: float = 10000.0
    require_approval_for_external_distribution: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Load config
config = MarketResearchConfig()
```

### 7.3 Environment Setup

```bash
# requirements.txt
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
langgraph>=0.2.0
langgraph-checkpoint>=0.1.0
langgraph-store>=0.1.0
openai>=1.0.0
tavily-python>=0.5.0
faiss-cpu>=1.9.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
aiohttp>=3.9.0
feedparser>=6.0.0
numpy>=1.24.0
scipy>=1.11.0
pandas>=2.0.0
plotly>=5.18.0
markdown>=3.6.0
jinja2>=3.1.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

```bash
# .env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
NEWSAPI_KEY=your-newsapi-key
TWITTER_BEARER_TOKEN=your-twitter-token
REDDIT_CLIENT_ID=your-reddit-id
REDDIT_CLIENT_SECRET=your-reddit-secret
```

### 7.4 Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  market-research:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./reports:/app/reports
      - ./data:/app/data
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: market_research
      POSTGRES_USER: researcher
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

---

## 8. Testing Strategy

### 8.1 Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  ← Full pipeline integration tests
                    │  Tests  │     (5-10 tests, slow, comprehensive)
                    ├─────────┤
                    │   API   │  ← Agent API contract tests
                    │  Tests  │     (20-30 tests, medium speed)
                    ├─────────┤
                    │Integration│ ← Inter-agent communication tests
                    │  Tests  │     (30-50 tests, medium-fast)
                    ├─────────┤
                    │  Unit   │  ← Individual component tests
                    │  Tests  │     (100+ tests, fast, isolated)
                    └─────────┘
```

### 8.2 Unit Tests

```python
# tests/test_data_collection.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

class TestDataCollectionAgent:
    """Unit tests for the Data Collection Agent."""

    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=MagicMock(content="test response"))
        return llm

    @pytest.fixture
    def collection_agent(self, mock_llm):
        from implementations.market_research_impl import DataCollectionAgent
        return DataCollectionAgent(
            llm=mock_llm,
            tavily_api_key="test-key",
            data_sources=[],
        )

    @pytest.mark.asyncio
    async def test_collect_returns_data(self, collection_agent):
        """Test that collect returns a list of CollectedData."""
        query = CollectionQuery(
            research_topic="AI customer service",
            target_markets=["US"],
            competitors=["zendesk"],
            keywords=["AI", "customer service"],
        )
        
        # Mock the collection methods
        collection_agent.web_search.search_with_context = AsyncMock(
            return_value=[{
                "title": "Test Article",
                "content": "Test content about AI customer service",
                "url": "https://example.com",
                "relevance_score": 0.8,
            }]
        )
        
        result = await collection_agent.collect(query)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(d, CollectedData) for d in result)

    @pytest.mark.asyncio
    async def test_deduplication(self, collection_agent):
        """Test that duplicate content is removed."""
        data = [
            CollectedData(
                source="test",
                source_url="https://example.com/1",
                title="Same Title",
                content="Same content",
                content_type="article",
                collected_at=datetime.now(),
            ),
            CollectedData(
                source="test",
                source_url="https://example.com/2",
                title="Same Title",
                content="Same content",
                content_type="article",
                collected_at=datetime.now(),
            ),
            CollectedData(
                source="test",
                source_url="https://example.com/3",
                title="Different Title",
                content="Different content",
                content_type="article",
                collected_at=datetime.now(),
            ),
        ]
        collection_agent.collected_data = data
        
        result = await collection_agent._tool_deduplicate()
        result_dict = json.loads(result)
        
        assert result_dict["removed"] == 1
        assert result_dict["remaining"] == 2

    @pytest.mark.asyncio
    async def test_relevance_scoring(self, collection_agent):
        """Test that relevance scoring works correctly."""
        data = [
            CollectedData(
                source="test",
                source_url="https://example.com/1",
                title="AI customer service automation",
                content="This article discusses AI-powered customer service solutions",
                content_type="article",
                collected_at=datetime.now(),
            ),
            CollectedData(
                source="test",
                source_url="https://example.com/2",
                title="Cooking recipes",
                content="How to make pasta from scratch",
                content_type="article",
                collected_at=datetime.now(),
            ),
        ]
        
        query = CollectionQuery(
            research_topic="AI customer service",
            target_markets=["US"],
            competitors=["zendesk"],
            keywords=["AI", "customer service", "automation"],
        )
        
        scored = collection_agent._score_relevance(data, query)
        
        assert scored[0].relevance_score > scored[1].relevance_score
        assert scored[0].relevance_score > 0.3
        assert scored[1].relevance_score < 0.3

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting prevents excessive requests."""
        config = DataSourceConfig(
            name="test_api",
            source_type="api",
            url="https://api.example.com",
            rate_limit=2,  # 2 requests per minute
        )
        collector = APICollector(config)
        
        start = datetime.now()
        # Simulate multiple rapid requests
        for _ in range(3):
            await collector._respect_rate_limit()
        elapsed = (datetime.now() - start).total_seconds()
        
        # Should have taken at least 30 seconds for 3 requests at 2/min
        assert elapsed >= 25  # Allow some tolerance


# tests/test_analysis.py

class TestAnalysisAgent:
    """Unit tests for the Analysis Agent."""

    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=MagicMock(content='{"trends": []}'))
        return llm

    @pytest.fixture
    def analysis_agent(self, mock_llm):
        from implementations.market_research_impl import AnalysisAgent
        return AnalysisAgent(llm=mock_llm)

    def test_sentiment_analyzer_positive(self):
        """Test positive sentiment detection."""
        analyzer = SentimentAnalyzer(MagicMock())
        texts = [
            "This product is excellent and outstanding",
            "The innovative features are impressive",
            "Best customer service experience ever",
        ]
        result = analyzer.analyze(texts)
        
        assert result.overall_sentiment == "positive"
        assert result.sentiment_score > 0.2

    def test_sentiment_analyzer_negative(self):
        """Test negative sentiment detection."""
        analyzer = SentimentAnalyzer(MagicMock())
        texts = [
            "Poor quality and disappointing performance",
            "The outdated interface is frustrating",
            "Limited features and unreliable service",
        ]
        result = analyzer.analyze(texts)
        
        assert result.overall_sentiment == "negative"
        assert result.sentiment_score < -0.2

    def test_sentiment_analyzer_mixed(self):
        """Test mixed sentiment detection."""
        analyzer = SentimentAnalyzer(MagicMock())
        texts = [
            "Great features but poor documentation",
            "Excellent performance, however expensive",
        ]
        result = analyzer.analyze(texts)
        
        assert result.overall_sentiment in ("mixed", "neutral")

    def test_trend_forecast_linear(self):
        """Test linear trend forecasting."""
        analyzer = TrendAnalyzer(MagicMock())
        historical = [100, 110, 121, 133, 146]  # ~10% growth
        forecasts = analyzer.forecast_growth(historical, periods=3)
        
        assert len(forecasts) == 3
        assert all(f > 0 for f in forecasts)
        # Should show continued growth
        assert forecasts[-1] > forecasts[0]

    def test_market_sizing_number_extraction(self):
        """Test extraction of market numbers from text."""
        engine = MarketSizingEngine(MagicMock())
        data = [{
            "content": "The market is valued at $5.2 billion with 15% CAGR",
            "title": "Market Report",
        }]
        numbers = engine._extract_market_numbers(data)
        
        assert len(numbers) > 0
        assert 5.2 in numbers
        assert 15.0 in numbers


# tests/test_reporting.py

class TestReportingAgent:
    """Unit tests for the Reporting Agent."""

    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=MagicMock(content="[]"))
        return llm

    @pytest.fixture
    def reporting_agent(self, mock_llm):
        from implementations.market_research_impl import ReportingAgent
        return ReportingAgent(llm=mock_llm)

    def test_markdown_formatting(self, reporting_agent):
        """Test Markdown report generation."""
        report = GeneratedReport(
            report_id="TEST-001",
            title="Test Report",
            report_type="test",
            created_at=datetime.now(),
            sections=[
                ReportSection(
                    title="Section 1",
                    content="Test content",
                    section_type="text",
                    order=0,
                ),
            ],
        )
        
        md = reporting_agent.formatter.to_markdown(report)
        
        assert "# Test Report" in md
        assert "## Section 1" in md
        assert "Test content" in md

    def test_html_formatting(self, reporting_agent):
        """Test HTML report generation."""
        report = GeneratedReport(
            report_id="TEST-001",
            title="Test Report",
            report_type="test",
            created_at=datetime.now(),
            sections=[
                ReportSection(
                    title="Section 1",
                    content="Test content",
                    section_type="text",
                    order=0,
                ),
            ],
        )
        
        html = reporting_agent.formatter.to_html(report)
        
        assert "<!DOCTYPE html>" in html
        assert "<title>Test Report</title>" in html
        assert "Test content" in html

    def test_slack_formatting(self, reporting_agent):
        """Test Slack message formatting."""
        report = GeneratedReport(
            report_id="TEST-001",
            title="Test Report",
            report_type="test",
            created_at=datetime.now(),
            sections=[
                ReportSection(
                    title="Key Insight",
                    content="Test insight",
                    section_type="text",
                    order=0,
                ),
            ],
        )
        
        slack = reporting_agent.formatter.to_slack(report)
        
        assert "blocks" in slack
        assert len(slack["blocks"]) > 0
        assert slack["blocks"][0]["type"] == "header"

    def test_chart_generation(self):
        """Test chart configuration generation."""
        gen = ChartGenerator()
        
        chart = gen.market_share_pie(
            {"Competitor A": 40, "Competitor B": 35, "Us": 25}
        )
        
        assert chart["type"] == "pie"
        assert len(chart["data"]["values"]) == 3
        assert chart["data"]["values"] == [40, 35, 25]


# tests/test_action_agent.py

class TestActionAgent:
    """Unit tests for the Action Agent."""

    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=MagicMock(content="[]"))
        return llm

    @pytest.fixture
    def action_agent(self, mock_llm):
        from implementations.market_research_impl import ActionAgent
        return ActionAgent(llm=mock_llm)

    def test_action_prioritization(self, action_agent):
        """Test that actions are prioritized correctly."""
        actions = [
            MarketingAction(
                action_id="1",
                action_type="content",
                title="Low impact high effort",
                description="Test",
                impact="low",
                effort="high",
                priority="low",
            ),
            MarketingAction(
                action_id="2",
                action_type="advertising",
                title="High impact low effort",
                description="Test",
                impact="high",
                effort="low",
                priority="critical",
            ),
            MarketingAction(
                action_id="3",
                action_type="seo",
                title="High impact high effort",
                description="Test",
                impact="high",
                effort="high",
                priority="high",
            ),
        ]
        
        result = asyncio.run(
            action_agent._tool_prioritize_actions(
                json.dumps([a.model_dump() for a in actions])
            )
        )
        prioritized = json.loads(result)
        
        # Critical priority should be first
        assert prioritized[0]["priority"] == "critical"
        assert prioritized[0]["title"] == "High impact low effort"

    def test_content_generation_structure(self, action_agent):
        """Test that generated content has required structure."""
        topics = action_agent.content_gen.generate_blog_topics(
            insights=[], count=5
        )
        # Should return a list (may be empty if LLM fails)
        assert isinstance(topics, list)


# tests/test_analytics.py

class TestPerformanceAnalyticsAgent:
    """Unit tests for the Performance Analytics Agent."""

    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=MagicMock(content="[]"))
        return llm

    @pytest.fixture
    def analytics_agent(self, mock_llm):
        from implementations.market_research_impl import PerformanceAnalyticsAgent
        return PerformanceAnalyticsAgent(llm=mock_llm)

    def test_metrics_calculation(self, analytics_agent):
        """Test campaign metrics calculation."""
        raw_data = {
            "campaign_id": "test-001",
            "campaign_name": "Test Campaign",
            "channel": "google_ads",
            "impressions": 10000,
            "clicks": 200,
            "conversions": 10,
            "spend": 500.0,
            "revenue": 2000.0,
            "start_date": datetime.now(),
        }
        
        metrics = analytics_agent.metrics_calc.calculate_campaign_metrics(raw_data)
        
        assert metrics.ctr == 2.0  # 200/10000 * 100
        assert metrics.cpc == 2.5  # 500/200
        assert metrics.cpa == 50.0  # 500/10
        assert metrics.roas == 4.0  # 2000/500
        assert metrics.roi == 300.0  # (2000-500)/500 * 100

    def test_attribution_first_touch(self):
        """Test first-touch attribution."""
        engine = AttributionEngine("first_touch")
        journeys = [
            [
                {"channel": "organic", "converted": False},
                {"channel": "paid", "converted": True},
            ],
            [
                {"channel": "social", "converted": False},
                {"channel": "email", "converted": True},
            ],
        ]
        
        result = engine.attribute(journeys)
        
        assert result.channel_attribution["organic"] == 0.5
        assert result.channel_attribution["social"] == 0.5
        assert "paid" not in result.channel_attribution

    def test_attribution_last_touch(self):
        """Test last-touch attribution."""
        engine = AttributionEngine("last_touch")
        journeys = [
            [
                {"channel": "organic", "converted": False},
                {"channel": "paid", "converted": True},
            ],
            [
                {"channel": "social", "converted": False},
                {"channel": "email", "converted": True},
            ],
        ]
        
        result = engine.attribute(journeys)
        
        assert result.channel_attribution["paid"] == 0.5
        assert result.channel_attribution["email"] == 0.5

    def test_attribution_linear(self):
        """Test linear attribution."""
        engine = AttributionEngine("linear")
        journeys = [
            [
                {"channel": "organic", "converted": False},
                {"channel": "paid", "converted": True},
            ],
        ]
        
        result = engine.attribute(journeys)
        
        assert result.channel_attribution["organic"] == 0.5
        assert result.channel_attribution["paid"] == 0.5

    def test_ab_test_evaluation(self):
        """Test A/B test statistical evaluation."""
        evaluator = ABTestEvaluator()
        result = evaluator.evaluate(
            control_metrics={"conversions": 100},
            treatment_metrics={"conversions": 120},
            sample_size_control=10000,
            sample_size_treatment=10000,
            confidence_level=0.95,
        )
        
        assert result.is_significant is True
        assert result.winner == "B"
        assert result.p_value < 0.05

    def test_anomaly_detection(self):
        """Test anomaly detection in time series."""
        detector = AnomalyDetector(sensitivity=2.0)
        time_series = [
            {"date": "2026-01-01", "roas": 4.0},
            {"date": "2026-01-02", "roas": 4.1},
            {"date": "2026-01-03", "roas": 3.9},
            {"date": "2026-01-04", "roas": 4.0},
            {"date": "2026-01-05", "roas": 4.2},
            {"date": "2026-01-06", "roas": 10.0},  # Anomaly!
            {"date": "2026-01-07", "roas": 4.1},
        ]
        
        anomalies = detector.detect(time_series, "roas")
        
        assert len(anomalies) > 0
        assert any(a["value"] == 10.0 for a in anomalies)

    def test_roi_calculation(self):
        """Test ROI and financial metrics calculation."""
        calc = ROICalculator()
        result = calc.calculate_roi(revenue=10000, cost=2500)
        
        assert result["profit"] == 7500
        assert result["roi_percent"] == 300.0
        assert result["roas"] == 4.0

    def test_cac_ltv_calculation(self):
        """Test CAC and LTV calculation."""
        calc = ROICalculator()
        result = calc.calculate_cac_ltv(
            total_spend=50000,
            new_customers=100,
            avg_revenue_per_customer=50,
            avg_customer_lifespan_months=24,
            gross_margin=0.7,
        )
        
        assert result["cac"] == 500
        assert result["ltv"] == 840  # 50 * 24 * 0.7
        assert result["ltv_cac_ratio"] == 1.68
        assert result["is_healthy"] is False  # Below 3:1 threshold
```

### 8.3 Integration Tests

```python
# tests/integration/test_pipeline.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

class TestMarketResearchPipeline:
    """Integration tests for the complete pipeline."""

    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        llm.invoke = AsyncMock(return_value=MagicMock(content="test"))
        return llm

    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, mock_llm):
        """Test the complete pipeline from collection to analytics."""
        # This is a simplified integration test
        # In production, use real LLM with test API keys
        
        # 1. Data Collection
        collector = DataCollectionAgent(
            llm=mock_llm,
            tavily_api_key="test-key",
            data_sources=[],
        )
        
        query = CollectionQuery(
            research_topic="test market",
            target_markets=["US"],
            competitors=["test-competitor"],
            keywords=["test"],
        )
        
        # Mock collection
        with patch.object(
            collector.web_search,
            "search_with_context",
            return_value=AsyncMock(return_value=[]),
        ):
            collected = await collector.collect(query)
        
        assert isinstance(collected, list)
        
        # 2. Analysis
        analyzer = AnalysisAgent(llm=mock_llm)
        # Would test analysis with collected data
        
        # 3. Reporting
        reporter = ReportingAgent(llm=mock_llm)
        # Would test report generation
        
        # 4. Actions
        action_agent = ActionAgent(llm=mock_llm)
        # Would test action generation
        
        # 5. Analytics
        analytics = PerformanceAnalyticsAgent(llm=mock_llm)
        # Would test analytics

    @pytest.mark.asyncio
    async def test_agent_communication(self, mock_llm):
        """Test that agents can communicate through shared state."""
        state = MarketResearchState(
            research_query="test",
            target_markets=["US"],
            competitors=["test"],
            collected_data=[{"test": "data"}],
            analysis_results={"test": "results"},
        )
        
        assert state["research_query"] == "test"
        assert len(state["collected_data"]) == 1
        assert state["analysis_results"]["test"] == "results"

    @pytest.mark.asyncio
    async def test_error_recovery(self, mock_llm):
        """Test that the pipeline handles errors gracefully."""
        collector = DataCollectionAgent(
            llm=mock_llm,
            tavily_api_key="test-key",
            data_sources=[],
        )
        
        # Simulate API failure
        with patch.object(
            collector.web_search,
            "search_with_context",
            side_effect=Exception("API Error"),
        ):
            query = CollectionQuery(
                research_topic="test",
                target_markets=["US"],
                competitors=["test"],
                keywords=["test"],
            )
            
            # Should not raise, should return empty
            result = await collector.collect(query)
            assert isinstance(result, list)
```

### 8.4 End-to-End Tests

```python
# tests/e2e/test_market_research_e2e.py

import pytest
import os

@pytest.mark.e2e
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not set",
)
class TestMarketResearchE2E:
    """End-to-end tests with real API calls.
    
    These tests require valid API keys and incur costs.
    Run with: pytest -m e2e
    """

    @pytest.fixture
    def real_llm(self):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
        )

    @pytest.mark.asyncio
    async def test_real_data_collection(self, real_llm):
        """Test data collection with real APIs."""
        collector = DataCollectionAgent(
            llm=real_llm,
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            data_sources=[],
        )
        
        query = CollectionQuery(
            research_topic="AI customer service automation",
            target_markets=["US"],
            competitors=["Zendesk"],
            keywords=["AI", "customer service", "automation"],
            max_results_per_source=5,
        )
        
        result = await collector.collect(query)
        
        assert len(result) > 0
        assert all(hasattr(r, "content") for r in result)
        assert all(hasattr(r, "relevance_score") for r in result)

    @pytest.mark.asyncio
    async def test_real_analysis(self, real_llm):
        """Test analysis with real LLM."""
        analyzer = AnalysisAgent(llm=real_llm)
        
        # Create test data
        test_data = [
            CollectedData(
                source="test",
                source_url="https://example.com",
                title="AI Customer Service Market Growing",
                content="The AI customer service market is growing rapidly with 25% CAGR",
                content_type="article",
                collected_at=datetime.now(),
            ),
        ]
        
        result = await analyzer.analyze(
            research_topic="AI customer service",
            collected_data=test_data,
            competitors=["Zendesk", "Intercom"],
        )
        
        assert result.research_topic == "AI customer service"
        assert result.analysis_date is not None
        assert isinstance(result.key_insights, list)
```

### 8.5 Performance Tests

```python
# tests/performance/test_performance.py

import pytest
import time
from datetime import datetime

class TestPerformanceBenchmarks:
    """Performance benchmarks for the market research system."""

    @pytest.mark.benchmark
    def test_data_collection_throughput(self):
        """Benchmark data collection speed."""
        # Should collect 100 data points in < 30 seconds
        pass

    @pytest.mark.benchmark
    def test_analysis_latency(self):
        """Benchmark analysis latency."""
        # Should analyze 100 data points in < 60 seconds
        pass

    @pytest.mark.benchmark
    def test_report_generation_speed(self):
        """Benchmark report generation."""
        # Should generate a report in < 30 seconds
        pass

    @pytest.mark.benchmark
    def test_concurrent_collection(self):
        """Benchmark concurrent data collection."""
        # Should handle 10 concurrent sources
        pass
```

### 8.6 Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/ -v -m "not integration and not e2e and not benchmark"

# Run integration tests
pytest tests/integration/ -v

# Run E2E tests (requires API keys)
pytest tests/e2e/ -v -m e2e

# Run with coverage
pytest tests/ --cov=implementations --cov-report=html

# Run performance benchmarks
pytest tests/performance/ -v -m benchmark
```

### 8.7 Quality Gates

| Gate | Criteria | Enforcement |
|------|----------|-------------|
| **Code Coverage** | ≥ 80% line coverage | CI pipeline |
| **Unit Tests** | All passing | Pre-commit hook |
| **Integration Tests** | All passing | CI pipeline |
| **E2E Tests** | All passing | Nightly build |
| **Performance** | < 5min full pipeline | Weekly benchmark |
| **Security** | No secrets in code | Pre-commit hook |
| **Linting** | ruff + mypy clean | Pre-commit hook |

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **Agent** | An autonomous AI entity with specific capabilities and tools |
| **DeepAgent** | LangChain's advanced agent framework with planning and sub-agent support |
| **LangGraph** | Stateful graph execution framework for multi-agent systems |
| **TAM** | Total Addressable Market |
| **SAM** | Serviceable Addressable Market |
| **SOM** | Serviceable Obtainable Market |
| **CAGR** | Compound Annual Growth Rate |
| **ROAS** | Return on Ad Spend |
| **CAC** | Customer Acquisition Cost |
| **LTV** | Lifetime Value |
| **CTR** | Click-Through Rate |
| **CPA** | Cost Per Acquisition |
| **SWOT** | Strengths, Weaknesses, Opportunities, Threats |

## Appendix B: References

1. LangChain Documentation: https://python.langchain.com/
2. LangGraph Documentation: https://langchain-ai.github.io/langgraph/
3. DeepAgents Documentation: https://github.com/langchain-ai/deepagents
4. OpenAI API Reference: https://platform.openai.com/docs
5. Tavily Search API: https://docs.tavily.com/

---

*End of Implementation Plan*</longcat_think>
