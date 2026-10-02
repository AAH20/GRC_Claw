# AI-Powered SEO & Content Optimization Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build a multi-agent SEO system using LangChain DeepAgents that automates keyword research, content optimization, technical SEO audits, link building, monitoring, and performance analytics.

**Architecture:** Six specialized DeepAgents orchestrated by a central coordinator agent. Each agent has domain-specific tools, prompts, and output schemas. The coordinator routes tasks, aggregates results, and manages the end-to-end SEO workflow.

**Tech Stack:** LangChain, LangGraph, DeepAgents, Python 3.11+, Pydantic, OpenAI GPT-4o, Google Search Console API, Screaming Frog API, Ahrefs API, PostgreSQL, Redis, FastAPI

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Keyword Research Agent](#2-keyword-research-agent)
3. [Content Optimization Agent](#3-content-optimization-agent)
4. [Technical SEO Agent](#4-technical-seo-agent)
5. [Link Building Agent](#5-link-building-agent)
6. [SEO Monitoring Agent](#6-seo-monitoring-agent)
7. [Performance Analytics Agent](#7-performance-analytics-agent)
8. [Code Examples & Snippets](#8-code-examples--snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The SEO system uses a hub-and-spoke architecture with a central coordinator and six specialized agents:

```
                    ┌─────────────────────┐
                    │   Coordinator Agent  │
                    │   (Orchestrator)     │
                    └──────────┬──────────┘
                               │
        ┌──────────┬───────────┼───────────┬──────────┐
        │          │           │           │          │
   ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
   │Keyword │ │Content │ │Technical│ │  Link  │ │Monitor │
   │Research│ │Optimize│ │  SEO   │ │ Build  │ │  &     │
   │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │Analytics│
   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### 1.2 Coordinator Agent

The coordinator receives high-level SEO objectives, decomposes them into sub-tasks, dispatches to specialized agents, and synthesizes results.

```python
# src/agents/coordinator.py
from langchain.agents import AgentExecutor
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from pydantic import BaseModel

class SEOWorkflowState(TypedDict):
    objective: str
    domain: str
    current_phase: Literal[
        "keyword_research",
        "content_optimization",
        "technical_seo",
        "link_building",
        "monitoring",
        "analytics",
        "complete"
    ]
    results: dict
    errors: list

class CoordinatorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(SEOWorkflowState)

        graph.add_node("keyword_research", self._run_keyword_research)
        graph.add_node("content_optimization", self._run_content_optimization)
        graph.add_node("technical_seo", self._run_technical_seo)
        graph.add_node("link_building", self._run_link_building)
        graph.add_node("monitoring", self._run_monitoring)
        graph.add_node("analytics", self._run_analytics)

        graph.set_entry_point("keyword_research")
        graph.add_edge("keyword_research", "content_optimization")
        graph.add_edge("content_optimization", "technical_seo")
        graph.add_edge("technical_seo", "link_building")
        graph.add_edge("link_building", "monitoring")
        graph.add_edge("monitoring", "analytics")
        graph.add_edge("analytics", END)

        return graph.compile()

    async def execute(self, objective: str, domain: str) -> dict:
        initial_state = SEOWorkflowState(
            objective=objective,
            domain=domain,
            current_phase="keyword_research",
            results={},
            errors=[]
        )
        return await self.graph.ainvoke(initial_state)
```

### 1.3 Shared Infrastructure

```python
# src/agents/base.py
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel
from langchain.tools import BaseTool
from langchain_openai import ChatOpenIO
import structlog

logger = structlog.get_logger(__name__)

class AgentResult(BaseModel):
    agent_name: str
    status: str  # "success", "partial", "failed"
    data: dict[str, Any]
    recommendations: list[str]
    confidence_score: float  # 0.0 - 1.0
    execution_time_ms: int

class BaseSEOAgent(ABC):
    """Base class for all SEO agents."""

    def __init__(self, name: str, tools: list[BaseTool]):
        self.name = name
        self.tools = tools
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        self.logger = logger.bind(agent=name)

    @abstractmethod
    async def run(self, context: dict) -> AgentResult:
        """Execute the agent's primary task."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the agent's system prompt."""
        pass

    def _create_executor(self) -> AgentExecutor:
        from langchain.agents import create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )
```

### 1.4 Data Models

```python
# src/models/seo.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional

class KeywordIntent(str, Enum):
    INFORMATIONAL = "informational"
    NAVIGATIONAL = "navigational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"

class KeywordData(BaseModel):
    keyword: str
    search_volume: int
    difficulty: float = Field(ge=0, le=100)
    cpc: float
    intent: KeywordIntent
    serp_features: list[str]
    trend: list[float]  # 12-month trend
    related_keywords: list[str]
    content_gap_score: float = Field(ge=0, le=1)

class ContentAudit(BaseModel):
    url: str
    title: str
    meta_description: str
    word_count: int
    readability_score: float
    keyword_density: dict[str, float]
    internal_links: list[str]
    external_links: list[str]
    heading_structure: list[dict]
    issues: list[dict]
    opportunities: list[dict]

class TechnicalIssue(BaseModel):
    severity: Literal["critical", "high", "medium", "low"]
    category: str
    description: str
    affected_urls: list[str]
    fix_recommendation: str
    estimated_impact: str

class BacklinkData(BaseModel):
    source_url: str
    target_url: str
    anchor_text: str
    domain_authority: float
    page_authority: float
    link_type: Literal["dofollow", "nofollow"]
    first_seen: datetime
    status: Literal["active", "lost", "broken"]

class SEOMetrics(BaseModel):
    domain: str
    date: datetime
    organic_traffic: int
    keyword_rankings: dict[str, int]
    impressions: int
    clicks: int
    average_position: float
    ctr: float
    core_web_vitals: dict[str, float]
    indexed_pages: int
    total_backlinks: int
    referring_domains: int
```

---

## 2. Keyword Research Agent

### 2.1 Purpose

Discovers, analyzes, and prioritizes keywords using search volume data, competitor analysis, SERP feature detection, and trend analysis.

### 2.2 Tools

```python
# src/agents/tools/keyword_tools.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
import httpx
import json

class SearchVolumeInput(BaseModel):
    keywords: list[str] = Field(description="List of keywords to analyze")
    location: str = Field(default="US", description="Target location")
    language: str = Field(default="en", description="Target language")

class SearchVolumeTool(BaseTool):
    name = "search_volume_lookup"
    description = "Get search volume, CPC, and competition data for keywords"
    args_schema = SearchVolumeInput

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.semrush.com/"

    async def _arun(self, keywords: list[str], location: str = "US",
                    language: str = "en") -> dict:
        params = {
            "type": "phrase_this",
            "key": self.api_key,
            "phrase": ",".join(keywords),
            "database": location.lower(),
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.base_url, params=params, timeout=30)
            return self._parse_semrush_response(resp.text)

    def _parse_semrush_response(self, csv_text: str) -> dict:
        lines = csv_text.strip().split("\n")
        headers = lines[0].split(";")
        results = {}
        for line in lines[1:]:
            values = line.split(";")
            row = dict(zip(headers, values))
            results[row["Ph"]] = {
                "search_volume": int(row.get("Nq", 0)),
                "cpc": float(row.get("Cp", 0)),
                "competition": float(row.get("Co", 0)),
                "number_of_results": int(row.get("Nr", 0)),
                "trend": row.get("Td", ""),
            }
        return results

class SERPAnalysisInput(BaseModel):
    keyword: str = Field(description="Keyword to analyze SERP for")
    location: str = Field(default="US")

class SERPAnalysisTool(BaseTool):
    name = "serp_analysis"
    description = "Analyze SERP features, competitors, and ranking factors"
    args_schema = SERPAnalysisInput

    def __init__(self, serpapi_key: str):
        self.api_key = serpapi_key

    async def _arun(self, keyword: str, location: str = "US") -> dict:
        params = {
            "q": keyword,
            "api_key": self.api_key,
            "gl": location,
            "num": 10,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://serpapi.com/search", params=params, timeout=30
            )
            data = resp.json()

        return {
            "serp_features": self._extract_serp_features(data),
            "top_results": [
                {
                    "position": r.get("position"),
                    "title": r.get("title"),
                    "url": r.get("link"),
                    "snippet": r.get("snippet"),
                }
                for r in data.get("organic_results", [])
            ],
            "people_also_ask": [
                q.get("question")
                for q in data.get("people_also_ask", [])
            ],
            "related_searches": [
                s.get("query")
                for s in data.get("related_searches", [])
            ],
        }

    def _extract_serp_features(self, data: dict) -> list[str]:
        features = []
        if data.get("answer_box"):
            features.append("featured_snippet")
        if data.get("knowledge_graph"):
            features.append("knowledge_graph")
        if data.get("local_pack"):
            features.append("local_pack")
        if data.get("image_pack"):
            features.append("image_pack")
        if data.get("video_carousel"):
            features.append("video_carousel")
        if data.get("people_also_ask"):
            features.append("people_also_ask")
        if data.get("shopping_results"):
            features.append("shopping_results")
        return features

class KeywordGapInput(BaseModel):
    domain: str = Field(description="Your domain")
    competitor_domains: list[str] = Field(description="Competitor domains")

class KeywordGapTool(BaseTool):
    name = "keyword_gap_analysis"
    description = "Find keywords competitors rank for but you don't"
    args_schema = KeywordGapInput

    async def _arun(self, domain: str, competitor_domains: list[str]) -> dict:
        # Uses Ahrefs API to find keyword gaps
        gaps = []
        for competitor in competitor_domains:
            competitor_keywords = await self._get_competitor_keywords(competitor)
            our_keywords = await self._get_domain_keywords(domain)
            gap = set(competitor_keywords) - set(our_keywords)
            gaps.extend(list(gap)[:50])
        return {"keyword_gaps": list(set(gaps))}

    async def _get_competitor_keywords(self, domain: str) -> list[str]:
        # Ahrefs API integration
        pass

    async def _get_domain_keywords(self, domain: str) -> list[str]:
        # Ahrefs API integration
        pass
```

### 2.3 Agent Implementation

```python
# src/agents/keyword_research_agent.py
from src.agents.base import BaseSEOAgent, AgentResult
from src.agents.tools.keyword_tools import (
    SearchVolumeTool, SERPAnalysisTool, KeywordGapTool,
)
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
import time

class KeywordResearchAgent(BaseSEOAgent):
    def __init__(self, semrush_key: str, serpapi_key: str, ahrefs_key: str):
        tools = [
            SearchVolumeTool(semrush_key),
            SERPAnalysisTool(serpapi_key),
            KeywordGapTool(ahrefs_key),
        ]
        super().__init__("keyword_research", tools)

    def get_system_prompt(self) -> str:
        return """You are an expert SEO keyword researcher. Your task is to:
1. Discover high-value keywords using search volume data and competitor analysis
2. Analyze SERP features and ranking difficulty for each keyword
3. Identify content gaps and opportunities
4. Classify keywords by search intent (informational, navigational, commercial, transactional)
5. Prioritize keywords based on a weighted score of volume, difficulty, and business value

For each keyword cluster, provide:
- Primary keyword with full metrics
- Related long-tail variations
- Content recommendations
- Estimated traffic potential
- Priority score (1-10)

Always validate data across multiple sources and flag inconsistencies."""

    async def run(self, context: dict) -> AgentResult:
        start_time = time.time()
        domain = context.get("domain", "")
        competitors = context.get("competitors", [])
        seed_keywords = context.get("seed_keywords", [])

        executor = self._create_executor()

        try:
            # Phase 1: Expand seed keywords
            expansion_result = await executor.ainvoke({
                "input": f"""Research keywords for {domain}.
                Seed keywords: {seed_keywords}
                Competitors: {competitors}
                Find 50+ keyword opportunities with full metrics."""
            })

            # Phase 2: Gap analysis
            gap_result = await executor.ainvoke({
                "input": f"""Perform keyword gap analysis for {domain}
                against competitors: {competitors}.
                Identify keywords they rank for that we don't."""
            })

            # Phase 3: Prioritization
            prioritization = await executor.ainvoke({
                "input": """Based on the research data, prioritize keywords
                into tiers: high-priority (quick wins), medium-priority
                (strategic), and low-priority (long-term). Consider search
                volume, difficulty, intent, and business relevance."""
            })

            execution_time = int((time.time() - start_time) * 1000)

            return AgentResult(
                agent_name=self.name,
                status="success",
                data={
                    "keyword_opportunities": expansion_result.get("output"),
                    "keyword_gaps": gap_result.get("output"),
                    "prioritized_keywords": prioritization.get("output"),
                },
                recommendations=[
                    "Focus on high-priority keywords first",
                    "Create content clusters around primary keywords",
                    "Monitor keyword gaps monthly",
                ],
                confidence_score=0.85,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            self.logger.error("keyword_research_failed", error=str(e))
            return AgentResult(
                agent_name=self.name,
                status="failed",
                data={},
                recommendations=["Retry with fewer keywords", "Check API quotas"],
                confidence_score=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

---

## 3. Content Optimization Agent

### 3.1 Purpose

Analyzes existing content, identifies optimization opportunities, generates content briefs, and provides actionable recommendations for improving on-page SEO.

### 3.2 Tools

```python
# src/agents/tools/content_tools.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
import httpx
from bs4 import BeautifulSoup

class ContentFetchInput(BaseModel):
    url: str = Field(description="URL of content to analyze")

class ContentFetchTool(BaseTool):
    name = "fetch_content"
    description = "Fetch and extract content from a URL"
    args_schema = ContentFetchInput

    async def _arun(self, url: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30, follow_redirects=True)
            soup = BeautifulSoup(resp.text, "html.parser")

        return {
            "title": soup.title.string if soup.title else "",
            "meta_description": soup.find("meta", attrs={"name": "description"})
                .get("content", "") if soup.find("meta", attrs={"name": "description"}) else "",
            "headings": [
                {"level": h.name, "text": h.get_text(strip=True)}
                for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
            ],
            "body_text": soup.get_text(separator=" ", strip=True),
            "word_count": len(soup.get_text(separator=" ", strip=True).split()),
            "internal_links": [a["href"] for a in soup.find_all("a", href=True)
                              if a["href"].startswith("/")],
            "external_links": [a["href"] for a in soup.find_all("a", href=True)
                               if a["href"].startswith("http")],
            "images": [{"src": img.get("src", ""), "alt": img.get("alt", "")}
                       for img in soup.find_all("img")],
            "schema_markup": self._extract_schema(soup),
        }

    def _extract_schema(self, soup) -> list[dict]:
        schemas = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                schemas.append(json.loads(script.string))
            except (json.JSONDecodeError, TypeError):
                continue
        return schemas

class ReadabilityInput(BaseModel):
    text: str = Field(description="Text to analyze for readability")

class ReadabilityTool(BaseTool):
    name = "readability_analysis"
    description = "Analyze text readability using Flesch-Kincaid and other metrics"
    args_schema = ReadabilityInput

    async def _arun(self, text: str) -> dict:
        import textstat

        return {
            "flesch_reading_ease": textstat.flesch_reading_ease(text),
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
            "smog_index": textstat.smog_index(text),
            "coleman_liau_index": textstat.coleman_liau_index(text),
            "automated_readability_index": textstat.automated_readability_index(text),
            "dale_chall_readability_score": textstat.dale_chall_readability_score(text),
            "difficult_words_count": textstat.difficult_words(text),
            "syllable_count": textstat.syllable_count(text),
            "lexicon_count": textstat.lexicon_count(text),
            "sentence_count": textstat.sentence_count(text),
        }

class ContentScoreInput(BaseModel):
    url: str = Field(description="URL to score")
    target_keywords: list[str] = Field(description="Target keywords for this content")

class ContentScoreTool(BaseTool):
    name = "content_quality_score"
    description = "Score content quality against SEO best practices"
    args_schema = ContentScoreInput

    async def _arun(self, url: str, target_keywords: list[str]) -> dict:
        fetch_tool = ContentFetchTool()
        content = await fetch_tool._arun(url)
        readability = await ReadabilityTool()._arun(content["body_text"])

        scores = {
            "title_optimization": self._score_title(content["title"], target_keywords),
            "meta_description": self._score_meta(content["meta_description"], target_keywords),
            "content_depth": self._score_depth(content["word_count"]),
            "readability": self._score_readability(readability),
            "heading_structure": self._score_headings(content["headings"]),
            "internal_linking": self._score_internal_links(content["internal_links"]),
            "image_optimization": self._score_images(content["images"]),
            "schema_markup": self._score_schema(content["schema_markup"]),
        }

        scores["overall"] = sum(scores.values()) / len(scores)
        return scores

    def _score_title(self, title: str, keywords: list[str]) -> float:
        score = 0.0
        if any(kw.lower() in title.lower() for kw in keywords):
            score += 0.4
        if 30 <= len(title) <= 60:
            score += 0.3
        if title[0].isupper():
            score += 0.1
        if any(c.isdigit() for c in title):
            score += 0.2
        return min(score, 1.0)

    def _score_meta(self, meta: str, keywords: list[str]) -> float:
        score = 0.0
        if meta:
            score += 0.3
            if any(kw.lower() in meta.lower() for kw in keywords):
                score += 0.4
            if 120 <= len(meta) <= 160:
                score += 0.3
        return min(score, 1.0)

    def _score_depth(self, word_count: int) -> float:
        if word_count >= 2000:
            return 1.0
        elif word_count >= 1500:
            return 0.8
        elif word_count >= 1000:
            return 0.6
        elif word_count >= 500:
            return 0.4
        return 0.2

    def _score_readability(self, readability: dict) -> float:
        fre = readability.get("flesch_reading_ease", 0)
        if 60 <= fre <= 70:
            return 1.0
        elif 50 <= fre <= 80:
            return 0.7
        return 0.4

    def _score_headings(self, headings: list[dict]) -> float:
        score = 0.0
        levels = [h["level"] for h in headings]
        if "h1" in levels:
            score += 0.4
        if levels.count("h1") == 1:
            score += 0.3
        if "h2" in levels:
            score += 0.3
        return min(score, 1.0)

    def _score_internal_links(self, links: list[str]) -> float:
        if len(links) >= 5:
            return 1.0
        elif len(links) >= 3:
            return 0.7
        elif len(links) >= 1:
            return 0.4
        return 0.0

    def _score_images(self, images: list[dict]) -> float:
        if not images:
            return 0.5
        with_alt = sum(1 for img in images if img.get("alt"))
        return with_alt / len(images)

    def _score_schema(self, schemas: list[dict]) -> float:
        return 1.0 if schemas else 0.0
```

### 3.3 Agent Implementation

```python
# src/agents/content_optimization_agent.py
from src.agents.base import BaseSEOAgent, AgentResult
from src.agents.tools.content_tools import (
    ContentFetchTool, ReadabilityTool, ContentScoreTool,
)
import time

class ContentOptimizationAgent(BaseSEOAgent):
    def __init__(self):
        tools = [ContentFetchTool(), ReadabilityTool(), ContentScoreTool()]
        super().__init__("content_optimization", tools)

    def get_system_prompt(self) -> str:
        return """You are an expert content optimizer specializing in SEO.
Your responsibilities:
1. Analyze content quality, structure, and on-page SEO factors
2. Identify content gaps, thin content, and optimization opportunities
3. Generate detailed content briefs for new content creation
4. Recommend internal linking strategies
5. Optimize content for target keywords while maintaining readability
6. Ensure content aligns with search intent

For each piece of content, evaluate:
- Keyword usage and placement (title, headings, body, meta)
- Content depth and comprehensiveness
- Readability and user engagement factors
- Internal and external linking
- Schema markup and structured data
- Image optimization
- Content freshness signals

Provide specific, actionable recommendations with priority levels."""

    async def run(self, context: dict) -> AgentResult:
        start_time = time.time()
        urls = context.get("content_urls", [])
        target_keywords = context.get("target_keywords", [])

        executor = self._create_executor()

        try:
            audits = []
            for url in urls:
                audit_result = await executor.ainvoke({
                    "input": f"""Perform a comprehensive content audit for {url}.
                    Target keywords: {target_keywords}.
                    Analyze all on-page SEO factors, content quality,
                    readability, and optimization opportunities."""
                })
                audits.append({
                    "url": url,
                    "audit": audit_result.get("output"),
                })

            # Generate content briefs for gaps
            briefs_result = await executor.ainvoke({
                "input": f"""Based on the audits, generate content briefs
                for any content gaps identified. Target keywords: {target_keywords}.
                Include: target keyword, search intent, suggested title,
                outline, word count target, and internal linking plan."""
            })

            execution_time = int((time.time() - start_time) * 1000)

            return AgentResult(
                agent_name=self.name,
                status="success",
                data={
                    "content_audits": audits,
                    "content_briefs": briefs_result.get("output"),
                },
                recommendations=[
                    "Prioritize fixing critical on-page issues first",
                    "Update thin content with more comprehensive coverage",
                    "Add internal links from high-authority pages",
                    "Implement schema markup where missing",
                ],
                confidence_score=0.82,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            self.logger.error("content_optimization_failed", error=str(e))
            return AgentResult(
                agent_name=self.name,
                status="failed",
                data={},
                recommendations=["Check URL accessibility", "Verify content is crawlable"],
                confidence_score=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
```

---

## 4. Technical SEO Agent

### 4.1 Purpose

Audits website technical health including crawlability, indexation, site speed, mobile usability, structured data, and Core Web Vitals.

### 4.2 Tools

```python
# src/agents/tools/technical_tools.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import httpx
import json

class CrawlAuditInput(BaseModel):
    domain: str = Field(description="Domain to audit")
    max_pages: int = Field(default=1000, description="Maximum pages to crawl")

class CrawlAuditTool(BaseTool):
    name = "crawl_audit"
    description = "Crawl website and identify technical SEO issues"
    args_schema = CrawlAuditInput

    def __init__(self, screamingfrog_path: str):
        self.screamingfrog_path = screamingfrog_path

    async def _arun(self, domain: str, max_pages: int = 1000) -> dict:
        import subprocess
        import csv
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output_path = f.name

        cmd = [
            self.screamingfrog_path,
            "--crawl", f"https://{domain}",
            "--headless",
            "--output-folder", "/tmp",
            "--export-csv", output_path,
            "--max-crawl-pages", str(max_pages),
        ]
        subprocess.run(cmd, capture_output=True, timeout=300)

        issues = {
            "broken_links": [],
            "redirect_chains": [],
            "missing_meta": [],
            "duplicate_content": [],
            "orphan_pages": [],
            "slow_pages": [],
            "mobile_issues": [],
        }

        with open(output_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                status = row.get("Status Code", "")
                if status and status.startswith("4"):
                    issues["broken_links"].append({
                        "url": row.get("Address", ""),
                        "status": status,
                    })
                elif status and status.startswith("3"):
                    issues["redirect_chains"].append({
                        "url": row.get("Address", ""),
                        "status": status,
                    })

                if row.get("Meta Description 1") == "":
                    issues["missing_meta"].append(row.get("Address", ""))

                load_time = float(row.get("Crawl Depth", 0) or 0)
                if load_time > 3.0:
                    issues["slow_pages"].append({
                        "url": row.get("Address", ""),
                        "load_time": load_time,
                    })

        return issues

class CoreWebVitalsInput(BaseModel):
    url: str = Field(description="URL to check Core Web Vitals for")

class CoreWebVitalsTool(BaseTool):
    name = "core_web_vitals"
    description = "Check Core Web Vitals metrics using PageSpeed Insights API"
    args_schema = CoreWebVitalsInput

    def __init__(self, psi_api_key: str):
        self.api_key = psi_api_key

    async def _arun(self, url: str) -> dict:
        params = {
            "url": url,
            "key": self.api_key,
            "strategy": "mobile",
            "category": "performance",
            "category": "seo",
            "category": "accessibility",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params=params, timeout=60,
            )
            data = resp.json()

        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        audits = lighthouse.get("audits", {})

        return {
            "performance_score": categories.get("performance", {}).get("score", 0) * 100,
            "seo_score": categories.get("seo", {}).get("score", 0) * 100,
            "accessibility_score": categories.get("accessibility", {}).get("score", 0) * 100,
            "core_web_vitals": {
                "LCP": audits.get("largest-contentful-paint", {}).get("displayValue", ""),
                "FID": audits.get("max-potential-fid", {}).get("displayValue", ""),
                "CLS": audits.get("cumulative-layout-shift", {}).get("displayValue", ""),
                "FCP": audits.get("first-contentful-paint", {}).get("displayValue", ""),
                "TTFB": audits.get("server-response-time", {}).get("displayValue", ""),
                "TBT": audits.get("total-blocking-time", {}).get("displayValue", ""),
            },
            "opportunities": [
                {"title": a.get("title"), "savings": a.get("details", {}).get("overallSavingsMs", 0)}
                for a in audits.values()
                if a.get("details", {}).get("overallSavingsMs", 0) > 0
            ],
        }

class IndexationInput(BaseModel):
    domain: str = Field(description="Domain to check indexation status")

class IndexationTool(BaseTool):
    name = "indexation_check"
    description = "Check indexation status via Google Search Console API"
    args_schema = IndexationInput

    def __init__(self, gsc_credentials: dict):
        self.credentials = gsc_credentials

    async def _arun(self, domain: str) -> dict:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_info(
            self.credentials,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        service = build("searchconsole", "v1", credentials=credentials)

        request = {
            "siteUrl": f"sc-domain:{domain}",
            "rowLimit": 25000,
        }
        response = service.urlInspection().index().inspect(
            body={"inspectionUrl": f"https://{domain}", "siteUrl": f"sc-domain:{domain}"}
        ).execute()

        sitemaps = service.sitemaps().list(siteUrl=f"sc-domain:{domain}").execute()

        return {
            "index_status": response.get("inspectionResult", {}).get("indexStatusResult", {}),
            "sitemaps": sitemaps.get("sitemap", []),
            "coverage_issues": self._parse_coverage_issues(response),
        }

    def _parse_coverage_issues(self, response: dict) -> list[dict]:
        result = response.get("inspectionResult", {}).get("indexStatusResult", {})
        issues = []
        if result.get("coverageState") != "Indexed":
            issues.append({
                "type": "indexation",
                "state": result.get("coverageState", "Unknown"),
                "details": result.get("lastCrawlTime", ""),
            })
        return issues
```

### 4.3 Agent Implementation

```python
# src/agents/technical_seo_agent.py
from src.agents.base import BaseSEOAgent, AgentResult
from src.agents.tools.technical_tools import (
    CrawlAuditTool, CoreWebVitalsTool, IndexationTool,
)
import time

class TechnicalSEOAgent(BaseSEOAgent):
    def __init__(self, sf_path: str, psi_key: str, gsc_creds: dict):
        tools = [
            CrawlAuditTool(sf_path),
            CoreWebVitalsTool(psi_key),
            IndexationTool(gsc_creds),
        ]
        super().__init__("technical_seo", tools)

    def get_system_prompt(self) -> str:
        return """You are an expert technical SEO auditor. Your responsibilities:
1. Crawl websites to identify technical issues affecting search performance
2. Analyze Core Web Vitals and page speed metrics
3. Check indexation status and crawl budget optimization
4. Identify structured data and schema markup opportunities
5. Audit mobile usability and responsive design
6. Check HTTPS implementation and security headers
7. Analyze XML sitemap and robots.txt configuration

Categorize issues by severity:
- Critical: Broken links, crawl errors, indexation blocks
- High: Slow pages, missing meta tags, redirect chains
- Medium: Missing schema, image optimization, internal linking
- Low: Minor markup issues, cosmetic improvements

For each issue, provide:
- Clear description of the problem
- Affected URLs or scope
- Step-by-step fix recommendation
- Estimated impact on SEO performance
- Priority level"""

    async def run(self, context: dict) -> AgentResult:
        start_time = time.time()
        domain = context.get("domain", "")

        executor = self._create_executor()

        try:
            crawl_result = await executor.ainvoke({
                "input": f"""Perform a comprehensive technical SEO audit for {domain}.
                Crawl the site, check Core Web Vitals, verify indexation status,
                and identify all technical issues."""
            })

            vitals_result = await executor.ainvoke({
                "input": f"""Analyze Core Web Vitals for {domain}.
                Check LCP, FID, CLS, FCP, TTFB, and TBT.
                Identify optimization opportunities."""
            })

            execution_time = int((time.time() - start_time) * 1000)

            return AgentResult(
                agent_name=self.name,
                status="success",
                data={
                    "crawl_audit": crawl_result.get("output"),
                    "core_web_vitals": vitals_result.get("output"),
                },
                recommendations=[
                    "Fix critical crawl errors immediately",
                    "Optimize images and enable compression",
                    "Implement lazy loading for below-fold content",
                    "Add missing structured data markup",
                    "Improve server response time",
                ],
                confidence_score=0.88,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            self.logger.error("technical_seo_failed", error=str(e))
            return AgentResult(
                agent_name=self.name,
                status="failed",
                data={},
                recommendations=["Verify API credentials", "Check domain accessibility"],
                confidence_score=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
```

---

## 5. Link Building Agent

### 5.1 Purpose

Identifies link building opportunities, analyzes competitor backlinks, finds broken link opportunities, and recommends outreach strategies.

### 5.2 Tools

```python
# src/agents/tools/link_tools.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import httpx

class BacklinkAnalysisInput(BaseModel):
    domain: str = Field(description="Domain to analyze backlinks for")

class BacklinkAnalysisTool(BaseTool):
    name = "backlink_analysis"
    description = "Analyze backlink profile using Ahrefs API"
    args_schema = BacklinkAnalysisInput

    def __init__(self, ahrefs_key: str):
        self.api_key = ahrefs_key
        self.base_url = "https://apiv2.ahrefs.com"

    async def _arun(self, domain: str) -> dict:
        params = {
            "target": domain,
            "mode": "domain",
            "limit": 1000,
            "order_by": "domain_rating:desc",
            "output": "json",
            "token": self.api_key,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/v3/site-explorer/backlinks",
                params=params, timeout=60,
            )
            data = resp.json()

        backlinks = data.get("backlinks", [])
        return {
            "total_backlinks": len(backlinks),
            "referring_domains": len(set(b.get("domain", "") for b in backlinks)),
            "domain_rating": data.get("domain_rating", 0),
            "top_backlinks": [
                {
                    "source": b.get("url_from", ""),
                    "target": b.get("url_to", ""),
                    "anchor": b.get("anchor", ""),
                    "domain_rating": b.get("domain_rating", 0),
                    "traffic": b.get("traffic", 0),
                }
                for b in backlinks[:50]
            ],
            "anchor_distribution": self._analyze_anchors(backlinks),
            "link_velocity": self._calculate_velocity(backlinks),
        }

    def _analyze_anchors(self, backlinks: list[dict]) -> dict:
        anchors = {}
        for link in backlinks:
            anchor = link.get("anchor", "N/A")
            anchors[anchor] = anchors.get(anchor, 0) + 1
        return dict(sorted(anchors.items(), key=lambda x: x[1], reverse=True)[:20])

    def _calculate_velocity(self, backlinks: list[dict]) -> dict:
        from datetime import datetime, timedelta
        now = datetime.now()
        last_30 = sum(1 for b in backlinks
                      if b.get("first_seen", "") and
                      datetime.fromisoformat(b["first_seen"]) > now - timedelta(days=30))
        last_90 = sum(1 for b in backlinks
                      if b.get("first_seen", "") and
                      datetime.fromisoformat(b["first_seen"]) > now - timedelta(days=90))
        return {"last_30_days": last_30, "last_90_days": last_90}

class LinkOpportunityInput(BaseModel):
    domain: str = Field(description="Your domain")
    competitor_domains: list[str] = Field(description="Competitor domains to analyze")

class LinkOpportunityTool(BaseTool):
    name = "link_opportunities"
    description = "Find link building opportunities from competitors and broken links"
    args_schema = LinkOpportunityInput

    async def _arun(self, domain: str, competitor_domains: list[str]) -> dict:
        opportunities = []

        for competitor in competitor_domains:
            comp_links = await self._get_competitor_links(competitor)
            our_links = await self._get_domain_links(domain)
            new_opportunities = [
                link for link in comp_links
                if link["source"] not in [o["source"] for o in our_links]
            ]
            opportunities.extend(new_opportunities[:20])

        broken_links = await self._find_broken_links(domain)

        return {
            "competitor_opportunities": opportunities,
            "broken_link_opportunities": broken_links,
            "resource_page_opportunities": await self._find_resource_pages(domain),
            "guest_post_opportunities": await self._find_guest_post_opps(domain),
        }

    async def _get_competitor_links(self, domain: str) -> list[dict]:
        pass  # Ahrefs API call

    async def _get_domain_links(self, domain: str) -> list[dict]:
        pass  # Ahrefs API call

    async def _find_broken_links(self, domain: str) -> list[dict]:
        pass  # Find broken external links on competitor sites

    async def _find_resource_pages(self, domain: str) -> list[dict]:
        pass  # Find resource pages that link to competitors

    async def _find_guest_post_opps(self, domain: str) -> list[dict]:
        pass  # Find guest post opportunities via search
```

### 5.3 Agent Implementation

```python
# src/agents/link_building_agent.py
from src.agents.base import BaseSEOAgent, AgentResult
from src.agents.tools.link_tools import (
    BacklinkAnalysisTool, LinkOpportunityTool,
)
import time

class LinkBuildingAgent(BaseSEOAgent):
    def __init__(self, ahrefs_key: str):
        tools = [
            BacklinkAnalysisTool(ahrefs_key),
            LinkOpportunityTool(),
        ]
        super().__init__("link_building", tools)

    def get_system_prompt(self) -> str:
        return """You are an expert link building strategist. Your responsibilities:
1. Analyze backlink profiles and identify quality issues
2. Find link building opportunities from competitor analysis
3. Identify broken link building opportunities
4. Recommend guest posting and digital PR strategies
5. Evaluate link quality and identify toxic links
6. Create outreach templates and strategies

For each opportunity, provide:
- Source domain and URL
- Domain authority and relevance score
- Link type (guest post, resource page, broken link, etc.)
- Outreach difficulty estimate
- Recommended approach and template
- Priority score based on value and effort

Focus on:
- High-authority, relevant domains
- Natural link acquisition methods
- Content-driven link building
- Relationship-based outreach"""

    async def run(self, context: dict) -> AgentResult:
        start_time = time.time()
        domain = context.get("domain", "")
        competitors = context.get("competitors", [])

        executor = self._create_executor()

        try:
            analysis_result = await executor.ainvoke({
                "input": f"""Analyze the backlink profile for {domain}.
                Identify toxic links, link velocity trends, and quality issues."""
            })

            opportunities_result = await executor.ainvoke({
                "input": f"""Find link building opportunities for {domain}
                based on competitor analysis: {competitors}.
                Include broken link opportunities, guest post prospects,
                and resource page opportunities."""
            })

            execution_time = int((time.time() - start_time) * 1000)

            return AgentResult(
                agent_name=self.name,
                status="success",
                data={
                    "backlink_analysis": analysis_result.get("output"),
                    "link_opportunities": opportunities_result.get("output"),
                },
                recommendations=[
                    "Disavow toxic backlinks immediately",
                    "Focus on high-DA relevant domains first",
                    "Create linkable assets (infographics, studies, tools)",
                    "Build relationships with industry bloggers",
                    "Monitor link velocity weekly",
                ],
                confidence_score=0.78,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            self.logger.error("link_building_failed", error=str(e))
            return AgentResult(
                agent_name=self.name,
                status="failed",
                data={},
                recommendations=["Verify Ahrefs API key", "Check competitor domains"],
                confidence_score=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
```

---

## 6. SEO Monitoring Agent

### 6.1 Purpose

Continuously tracks keyword rankings, SERP changes, competitor movements, and alert-worthy SEO events. Provides daily/weekly monitoring reports.

### 6.2 Tools

```python
# src/agents/tools/monitoring_tools.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import httpx
from datetime import datetime, timedelta

class RankingTrackInput(BaseModel):
    domain: str = Field(description="Domain to track")
    keywords: list[str] = Field(description="Keywords to monitor")
    location: str = Field(default="US")

class RankingTrackTool(BaseTool):
    name = "track_rankings"
    description = "Track keyword rankings over time"
    args_schema = RankingTrackInput

    def __init__(self, gsc_credentials: dict):
        self.credentials = gsc_credentials

    async def _arun(self, domain: str, keywords: list[str], location: str = "US") -> dict:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_info(
            self.credentials,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        service = build("searchconsole", "v1", credentials=credentials)

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        request = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["query", "date"],
            "rowLimit": 25000,
            "startRow": 0,
        }

        response = service.searchanalytics().query(
            siteUrl=f"sc-domain:{domain}", body=request
        ).execute()

        rankings = {}
        for row in response.get("rows", []):
            query = row["keys"][0]
            if query in keywords:
                if query not in rankings:
                    rankings[query] = []
                rankings[query].append({
                    "date": row["keys"][1],
                    "position": row["position"],
                    "clicks": row["clicks"],
                    "impressions": row["impressions"],
                    "ctr": row["ctr"],
                })

        return {
            "rankings": rankings,
            "average_positions": {
                kw: sum(r["position"] for r in data) / len(data)
                for kw, data in rankings.items() if data
            },
            "position_changes": self._calculate_changes(rankings),
        }

    def _calculate_changes(self, rankings: dict) -> dict:
        changes = {}
        for kw, data in rankings.items():
            if len(data) >= 2:
                recent = data[-1]["position"]
                previous = data[0]["position"]
                changes[kw] = {
                    "change": previous - recent,
                    "trend": "improving" if recent < previous else "declining",
                }
        return changes

class SERPMonitorInput(BaseModel):
    keywords: list[str] = Field(description="Keywords to monitor SERP for")

class SERPMonitorTool(BaseTool):
    name = "monitor_serp"
    description = "Monitor SERP changes and featured snippet opportunities"
    args_schema = SERPMonitorInput

    def __init__(self, serpapi_key: str):
        self.api_key = serpapi_key

    async def _arun(self, keywords: list[str]) -> dict:
        changes = {}
        for keyword in keywords:
            params = {
                "q": keyword,
                "api_key": self.api_key,
                "num": 10,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://serpapi.com/search", params=params, timeout=30
                )
                data = resp.json()

            changes[keyword] = {
                "top_results": [
                    {"position": r.get("position"), "url": r.get("link"), "title": r.get("title")}
                    for r in data.get("organic_results", [])[:5]
                ],
                "serp_features": self._detect_features(data),
                "featured_snippet": data.get("answer_box") is not None,
            }
        return changes

    def _detect_features(self, data: dict) -> list[str]:
        features = []
        if data.get("answer_box"):
            features.append("featured_snippet")
        if data.get("knowledge_graph"):
            features.append("knowledge_graph")
        if data.get("local_pack"):
            features.append("local_pack")
        if data.get("image_pack"):
            features.append("image_pack")
        if data.get("video_carousel"):
            features.append("video_carousel")
        return features

class CompetitorMonitorInput(BaseModel):
    domain: str = Field(description="Your domain")
    competitors: list[str] = Field(description="Competitor domains to monitor")

class CompetitorMonitorTool(BaseTool):
    name = "monitor_competitors"
    description = "Monitor competitor SEO movements and changes"
    args_schema = CompetitorMonitorInput

    async def _arun(self, domain: str, competitors: list[str]) -> dict:
        results = {}
        for competitor in competitors:
            results[competitor] = {
                "new_rankings": await self._check_new_rankings(competitor),
                "content_changes": await self._check_content_changes(competitor),
                "backlink_changes": await self._check_backlink_changes(competitor),
            }
        return results

    async def _check_new_rankings(self, domain: str) -> list[dict]:
        pass  # Check for new keyword rankings

    async def _check_content_changes(self, domain: str) -> list[dict]:
        pass  # Monitor content updates

    async def _check_backlink_changes(self, domain: str) -> list[dict]:
        pass  # Monitor new backlinks
```

### 6.3 Agent Implementation

```python
# src/agents/seo_monitoring_agent.py
from src.agents.base import BaseSEOAgent, AgentResult
from src.agents.tools.monitoring_tools import (
    RankingTrackTool, SERPMonitorTool, CompetitorMonitorTool,
)
import time

class SEOMonitoringAgent(BaseSEOAgent):
    def __init__(self, gsc_creds: dict, serpapi_key: str):
        tools = [
            RankingTrackTool(gsc_creds),
            SERPMonitorTool(serpapi_key),
            CompetitorMonitorTool(),
        ]
        super().__init__("seo_monitoring", tools)

    def get_system_prompt(self) -> str:
        return """You are an expert SEO monitor. Your responsibilities:
1. Track keyword rankings and identify significant position changes
2. Monitor SERP changes and new feature opportunities
3. Track competitor movements and new content
4. Identify alert-worthy events (ranking drops, SERP feature losses)
5. Generate daily/weekly monitoring reports
6. Recommend actions based on monitoring data

Alert thresholds:
- Ranking drop > 5 positions: Warning
- Ranking drop > 10 positions: Critical
- Loss of featured snippet: High priority
- Competitor outranking for target keywords: Monitor closely
- Traffic drop > 20%: Investigate immediately

Provide actionable insights, not just data."""

    async def run(self, context: dict) -> AgentResult:
        start_time = time.time()
        domain = context.get("domain", "")
        keywords = context.get("target_keywords", [])
        competitors = context.get("competitors", [])

        executor = self._create_executor()

        try:
            ranking_result = await executor.ainvoke({
                "input": f"""Track rankings for {domain} across these keywords: {keywords}.
                Identify significant changes, trends, and alert-worthy events."""
            })

            serp_result = await executor.ainvoke({
                "input": f"""Monitor SERP changes for keywords: {keywords}.
                Identify new opportunities and threats."""
            })

            competitor_result = await executor.ainvoke({
                "input": f"""Monitor competitor movements for: {competitors}.
                Identify new content, ranking changes, and backlink activity."""
            })

            execution_time = int((time.time() - start_time) * 1000)

            return AgentResult(
                agent_name=self.name,
                status="success",
                data={
                    "ranking_tracking": ranking_result.get("output"),
                    "serp_monitoring": serp_result.get("output"),
                    "competitor_monitoring": competitor_result.get("output"),
                },
                recommendations=[
                    "Set up automated alerts for critical ranking drops",
                    "Investigate pages losing featured snippets",
                    "Create content to counter competitor movements",
                    "Weekly monitoring review recommended",
                ],
                confidence_score=0.90,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            self.logger.error("seo_monitoring_failed", error=str(e))
            return AgentResult(
                agent_name=self.name,
                status="failed",
                data={},
                recommendations=["Verify API credentials", "Check keyword list"],
                confidence_score=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
```

---

## 7. Performance Analytics Agent

### 7.1 Purpose

Aggregates SEO performance data, calculates ROI, generates comprehensive reports, and provides strategic recommendations based on data analysis.

### 7.2 Tools

```python
# src/agents/tools/analytics_tools.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import httpx
from datetime import datetime, timedelta

class TrafficAnalysisInput(BaseModel):
    domain: str = Field(description="Domain to analyze")
    date_range: str = Field(default="30d", description="Date range (7d, 30d, 90d)")

class TrafficAnalysisTool(BaseTool):
    name = "analyze_traffic"
    description = "Analyze organic traffic patterns and trends"
    args_schema = TrafficAnalysisInput

    def __init__(self, gsc_credentials: dict):
        self.credentials = gsc_credentials

    async def _arun(self, domain: str, date_range: str = "30d") -> dict:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_info(
            self.credentials,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        service = build("searchconsole", "v1", credentials=credentials)

        days = int(date_range.replace("d", ""))
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        request = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["date"],
            "rowLimit": 25000,
        }

        response = service.searchanalytics().query(
            siteUrl=f"sc-domain:{domain}", body=request
        ).execute()

        rows = response.get("rows", [])
        total_clicks = sum(r["clicks"] for r in rows)
        total_impressions = sum(r["impressions"] for r in rows)

        return {
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "average_ctr": total_clicks / total_impressions if total_impressions > 0 else 0,
            "average_position": sum(r["position"] for r in rows) / len(rows) if rows else 0,
            "daily_data": [
                {"date": r["keys"][0], "clicks": r["clicks"], "impressions": r["impressions"]}
                for r in rows
            ],
            "trend": self._calculate_trend(rows),
        }

    def _calculate_trend(self, rows: list[dict]) -> str:
        if len(rows) < 2:
            return "insufficient_data"
        first_half = rows[:len(rows)//2]
        second_half = rows[len(rows)//2:]
        first_clicks = sum(r["clicks"] for r in first_half)
        second_clicks = sum(r["clicks"] for r in second_half)
        if second_clicks > first_clicks * 1.1:
            return "growing"
        elif second_clicks < first_clicks * 0.9:
            return "declining"
        return "stable"

class ROIAnalysisInput(BaseModel):
    domain: str = Field(description="Domain to analyze")
    conversion_value: float = Field(description="Average conversion value in USD")

class ROIAnalysisTool(BaseTool):
    name = "analyze_roi"
    description = "Calculate SEO ROI and conversion metrics"
    args_schema = ROIAnalysisInput

    async def _arun(self, domain: str, conversion_value: float) -> dict:
        # This would integrate with Google Analytics or other analytics
        # For now, using GSC data as proxy
        traffic_data = await TrafficAnalysisTool(self.credentials)._arun(domain, "30d")

        estimated_conversions = traffic_data["total_clicks"] * 0.03  # 3% conversion rate
        estimated_revenue = estimated_conversions * conversion_value

        return {
            "estimated_monthly_traffic": traffic_data["total_clicks"],
            "estimated_conversions": estimated_conversions,
            "estimated_revenue": estimated_revenue,
            "cost_per_acquisition": 0,  # Would need cost data
            "roi_percentage": 0,  # Would need investment data
            "projections": {
                "3_months": estimated_revenue * 3,
                "6_months": estimated_revenue * 6,
                "12_months": estimated_revenue * 12,
            },
        }

class ReportInput(BaseModel):
    domain: str = Field(description="Domain to generate report for")
    report_type: str = Field(default="comprehensive", description="Report type")

class ReportGeneratorTool(BaseTool):
    name = "generate_report"
    description = "Generate comprehensive SEO performance reports"
    args_schema = ReportInput

    async def _arun(self, domain: str, report_type: str = "comprehensive") -> dict:
        # Aggregate data from all sources
        traffic = await TrafficAnalysisTool(self.credentials)._arun(domain, "30d")

        report = {
            "domain": domain,
            "generated_at": datetime.now().isoformat(),
            "report_type": report_type,
            "executive_summary": {
                "total_organic_traffic": traffic["total_clicks"],
                "total_impressions": traffic["total_impressions"],
                "average_ctr": traffic["average_ctr"],
                "average_position": traffic["average_position"],
                "traffic_trend": traffic["trend"],
            },
            "key_metrics": {
                "traffic_growth": "calculated_vs_previous_period",
                "keyword_rankings": "from_monitoring_agent",
                "backlink_growth": "from_link_building_agent",
                "technical_health": "from_technical_seo_agent",
            },
            "recommendations": [],
            "next_steps": [],
        }

        return report
```

### 7.3 Agent Implementation

```python
# src/agents/performance_analytics_agent.py
from src.agents.base import BaseSEOAgent, AgentResult
from src.agents.tools.analytics_tools import (
    TrafficAnalysisTool, ROIAnalysisTool, ReportGeneratorTool,
)
import time

class PerformanceAnalyticsAgent(BaseSEOAgent):
    def __init__(self, gsc_creds: dict):
        tools = [
            TrafficAnalysisTool(gsc_creds),
            ROIAnalysisTool(gsc_creds),
            ReportGeneratorTool(gsc_creds),
        ]
        super().__init__("performance_analytics", tools)

    def get_system_prompt(self) -> str:
        return """You are an expert SEO performance analyst. Your responsibilities:
1. Aggregate and analyze SEO performance data from multiple sources
2. Calculate ROI and demonstrate SEO business value
3. Generate comprehensive reports for stakeholders
4. Identify trends, patterns, and anomalies in performance data
5. Provide strategic recommendations based on data analysis
6. Forecast future performance and set realistic targets

For each analysis, provide:
- Clear data visualizations and summaries
- Trend analysis with statistical significance
- Actionable recommendations with expected impact
- Benchmark comparisons where applicable
- Executive summary for non-technical stakeholders"""

    async def run(self, context: dict) -> AgentResult:
        start_time = time.time()
        domain = context.get("domain", "")
        conversion_value = context.get("conversion_value", 100.0)

        executor = self._create_executor()

        try:
            traffic_result = await executor.ainvoke({
                "input": f"""Analyze organic traffic for {domain} over the last 30 days.
                Identify trends, patterns, and anomalies."""
            })

            roi_result = await executor.ainvoke({
                "input": f"""Calculate SEO ROI for {domain} with average conversion
                value of ${conversion_value}. Include projections and recommendations."""
            })

            report_result = await executor.ainvoke({
                "input": f"""Generate a comprehensive SEO performance report for {domain}.
                Include all key metrics, trends, and strategic recommendations."""
            })

            execution_time = int((time.time() - start_time) * 1000)

            return AgentResult(
                agent_name=self.name,
                status="success",
                data={
                    "traffic_analysis": traffic_result.get("output"),
                    "roi_analysis": roi_result.get("output"),
                    "performance_report": report_result.get("output"),
                },
                recommendations=[
                    "Focus on high-traffic, low-conversion pages for quick wins",
                    "Increase content production for growing keyword clusters",
                    "Address technical issues impacting crawl efficiency",
                    "Set up automated monthly reporting",
                ],
                confidence_score=0.85,
                execution_time_ms=execution_time,
            )
        except Exception as e:
            self.logger.error("performance_analytics_failed", error=str(e))
            return AgentResult(
                agent_name=self.name,
                status="failed",
                data={},
                recommendations=["Verify analytics access", "Check data availability"],
                confidence_score=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
```

---

## 8. Code Examples & Snippets

### 8.1 Project Structure

```
seo-agents/
├── src/
│   ├── agents/
│   │   ├── base.py
│   │   ├── coordinator.py
│   │   ├── keyword_research_agent.py
│   │   ├── content_optimization_agent.py
│   │   ├── technical_seo_agent.py
│   │   ├── link_building_agent.py
│   │   ├── seo_monitoring_agent.py
│   │   └── performance_analytics_agent.py
│   ├── agents/tools/
│   │   ├── keyword_tools.py
│   │   ├── content_tools.py
│   │   ├── technical_tools.py
│   │   ├── link_tools.py
│   │   ├── monitoring_tools.py
│   │   └── analytics_tools.py
│   ├── models/
│   │   └── seo.py
│   ├── api/
│   │   └── main.py
│   ├── config/
│   │   └── settings.py
│   └── utils/
│       ├── cache.py
│       └── rate_limiter.py
├── tests/
│   ├── test_agents/
│   │   ├── test_keyword_research.py
│   │   ├── test_content_optimization.py
│   │   ├── test_technical_seo.py
│   │   ├── test_link_building.py
│   │   ├── test_monitoring.py
│   │   └── test_analytics.py
│   ├── test_tools/
│   │   └── test_all_tools.py
│   └── conftest.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example
```

### 8.2 Configuration

```python
# src/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    SEMRUSH_API_KEY: str
    SERPAPI_KEY: str
    AHREFS_API_KEY: str
    PSI_API_KEY: str

    # Google Search Console
    GSC_CREDENTIALS_PATH: str = "credentials/gsc-service-account.json"

    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/seo_agents"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Agent Settings
    MAX_ITERATIONS: int = 10
    TEMPERATURE: float = 0.2
    REQUEST_TIMEOUT: int = 30
    RATE_LIMIT_PER_MINUTE: int = 60

    # Monitoring
    ALERT_THRESHOLD_RANKING_DROP: int = 5
    ALERT_THRESHOLD_TRAFFIC_DROP: float = 0.20

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 8.3 FastAPI Application

```python
# src/api/main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.agents.coordinator import CoordinatorAgent
from src.config.settings import get_settings

app = FastAPI(title="SEO Agents API", version="1.0.0")

class SEORequest(BaseModel):
    domain: str
    objective: str
    competitors: list[str] = []
    seed_keywords: list[str] = []
    target_keywords: list[str] = []
    content_urls: list[str] = []
    conversion_value: float = 100.0

class SEOResponse(BaseModel):
    job_id: str
    status: str
    results: Optional[dict] = None
    errors: list[str] = []

@app.post("/api/v1/seo/analyze", response_model=SEOResponse)
async def analyze_seo(request: SEORequest, background_tasks: BackgroundTasks):
    """Start a comprehensive SEO analysis."""
    import uuid
    job_id = str(uuid.uuid4())

    coordinator = CoordinatorAgent()

    context = {
        "domain": request.domain,
        "competitors": request.competitors,
        "seed_keywords": request.seed_keywords,
        "target_keywords": request.target_keywords,
        "content_urls": request.content_urls,
        "conversion_value": request.conversion_value,
    }

    try:
        results = await coordinator.execute(request.objective, request.domain)
        return SEOResponse(
            job_id=job_id,
            status="completed",
            results=results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/seo/monitor")
async def start_monitoring(request: SEORequest):
    """Start continuous SEO monitoring."""
    from src.agents.seo_monitoring_agent import SEOMonitoringAgent

    agent = SEOMonitoringAgent(
        gsc_creds={},
        serpapi_key=get_settings().SERPAPI_KEY,
    )

    context = {
        "domain": request.domain,
        "target_keywords": request.target_keywords,
        "competitors": request.competitors,
    }

    result = await agent.run(context)
    return result.model_dump()

@app.get("/api/v1/seo/report/{domain}")
async def get_report(domain: str):
    """Get latest SEO performance report."""
    from src.agents.performance_analytics_agent import PerformanceAnalyticsAgent

    agent = PerformanceAnalyticsAgent(gsc_creds={})
    result = await agent.run({"domain": domain})
    return result.model_dump()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

### 8.4 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY src/ src/

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - redis
      - postgres
    volumes:
      - ./credentials:/app/credentials

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: seo_agents
      POSTGRES_USER: seo_user
      POSTGRES_PASSWORD: seo_pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  worker:
    build: .
    command: celery -A src.tasks worker --loglevel=info
    env_file:
      - .env
    depends_on:
      - redis
      - postgres

volumes:
  pgdata:
```

### 8.5 Caching & Rate Limiting

```python
# src/utils/cache.py
import json
import hashlib
from functools import wraps
from typing import Callable, Any
import redis.asyncio as redis
from src.config.settings import get_settings

redis_client = redis.from_url(get_settings().REDIS_URL)

def cached(ttl: int = 3600):
    """Cache decorator for async functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{hashlib.md5(json.dumps([str(a) for a in args] + [str(v) for v in kwargs.values()]).encode()).hexdigest()}"
            cached_value = await redis_client.get(key)
            if cached_value:
                return json.loads(cached_value)
            result = await func(*args, **kwargs)
            await redis_client.setex(key, ttl, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

# src/utils/rate_limiter.py
import time
from collections import deque
from functools import wraps

class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()

    async def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            while self.calls and self.calls[0] < now - self.period:
                self.calls.popleft()
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            self.calls.append(time.time())
            return await func(*args, **kwargs)
        return wrapper
```

### 8.6 Database Models

```python
# src/models/database.py
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from src.config.settings import get_settings

Base = declarative_base()
engine = create_engine(get_settings().DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class KeywordRanking(Base):
    __tablename__ = "keyword_rankings"

    id = Column(Integer, primary_key=True)
    domain = Column(String, index=True)
    keyword = Column(String, index=True)
    position = Column(Float)
    previous_position = Column(Float)
    clicks = Column(Integer)
    impressions = Column(Integer)
    ctr = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)

class ContentAuditRecord(Base):
    __tablename__ = "content_audits"

    id = Column(Integer, primary_key=True)
    url = Column(String, index=True)
    domain = Column(String, index=True)
    overall_score = Column(Float)
    issues = Column(JSON)
    recommendations = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class BacklinkRecord(Base):
    __tablename__ = "backlinks"

    id = Column(Integer, primary_key=True)
    source_url = Column(String)
    target_url = Column(String)
    anchor_text = Column(String)
    domain_authority = Column(Float)
    status = Column(String)
    first_seen = Column(DateTime)
    last_checked = Column(DateTime)
```

---

## 9. Testing Strategy

### 9.1 Test Architecture

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_base_agent.py
│   ├── test_models.py
│   └── test_utils.py
├── integration/
│   ├── test_keyword_agent.py
│   ├── test_content_agent.py
│   ├── test_technical_agent.py
│   ├── test_link_agent.py
│   ├── test_monitoring_agent.py
│   └── test_analytics_agent.py
├── e2e/
│   └── test_full_workflow.py
└── fixtures/
    ├── sample_keywords.json
    ├── sample_content.json
    └── sample_backlinks.json
```

### 9.2 Unit Tests

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from src.agents.base import BaseSEOAgent, AgentResult

@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.invoke = AsyncMock(return_value={"output": "test response"})
    return llm

@pytest.fixture
def sample_keyword_data():
    return {
        "keyword": "seo optimization",
        "search_volume": 12000,
        "difficulty": 45.5,
        "cpc": 3.20,
        "intent": "informational",
        "serp_features": ["featured_snippet", "people_also_ask"],
        "trend": [100, 105, 110, 108, 115, 120, 118, 125, 130, 128, 135, 140],
    }

@pytest.fixture
def sample_agent_result():
    return AgentResult(
        agent_name="test_agent",
        status="success",
        data={"test": "data"},
        recommendations=["test recommendation"],
        confidence_score=0.9,
        execution_time_ms=1000,
    )

# tests/unit/test_base_agent.py
import pytest
from src.agents.base import BaseSEOAgent, AgentResult

class TestBaseSEOAgent:
    def test_agent_result_creation(self, sample_agent_result):
        assert sample_agent_result.agent_name == "test_agent"
        assert sample_agent_result.status == "success"
        assert sample_agent_result.confidence_score == 0.9

    def test_agent_result_validation(self):
        with pytest.raises(ValueError):
            AgentResult(
                agent_name="test",
                status="success",
                data={},
                recommendations=[],
                confidence_score=1.5,  # Should be 0-1
                execution_time_ms=1000,
            )

# tests/unit/test_models.py
import pytest
from src.models.seo import KeywordData, KeywordIntent, TechnicalIssue

class TestKeywordData:
    def test_valid_keyword(self, sample_keyword_data):
        kw = KeywordData(**sample_keyword_data)
        assert kw.keyword == "seo optimization"
        assert kw.search_volume == 12000

    def test_invalid_difficulty(self, sample_keyword_data):
        sample_keyword_data["difficulty"] = 150
        with pytest.raises(ValueError):
            KeywordData(**sample_keyword_data)

    def test_intent_enum(self):
        assert KeywordIntent.INFORMATIONAL == "informational"
        assert KeywordIntent.COMMERCIAL == "commercial"

class TestTechnicalIssue:
    def test_valid_issue(self):
        issue = TechnicalIssue(
            severity="critical",
            category="crawl",
            description="Broken internal links",
            affected_urls=["https://example.com/page1"],
            fix_recommendation="Fix or remove broken links",
            estimated_impact="High",
        )
        assert issue.severity == "critical"
```

### 9.3 Integration Tests

```python
# tests/integration/test_keyword_agent.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from src.agents.keyword_research_agent import KeywordResearchAgent

@pytest_asyncio.fixture
async def keyword_agent():
    agent = KeywordResearchAgent(
        semrush_key="test_key",
        serpapi_key="test_key",
        ahrefs_key="test_key",
    )
    return agent

@pytest.mark.asyncio
class TestKeywordResearchAgent:
    async def test_successful_research(self, keyword_agent, mock_llm):
        keyword_agent.llm = mock_llm

        context = {
            "domain": "example.com",
            "competitors": ["competitor1.com"],
            "seed_keywords": ["seo tools"],
        }

        with patch.object(keyword_agent, '_create_executor') as mock_exec:
            mock_executor = AsyncMock()
            mock_executor.ainvoke = AsyncMock(return_value={
                "output": "Keyword research results"
            })
            mock_exec.return_value = mock_executor

            result = await keyword_agent.run(context)

        assert result.status == "success"
        assert result.agent_name == "keyword_research"
        assert "keyword_opportunities" in result.data

    async def test_failed_research(self, keyword_agent):
        context = {"domain": "example.com"}

        with patch.object(keyword_agent, '_create_executor') as mock_exec:
            mock_executor = AsyncMock()
            mock_executor.ainvoke = AsyncMock(side_effect=Exception("API Error"))
            mock_exec.return_value = mock_executor

            result = await keyword_agent.run(context)

        assert result.status == "failed"
        assert result.confidence_score == 0.0

# tests/integration/test_content_agent.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from src.agents.content_optimization_agent import ContentOptimizationAgent

@pytest.mark.asyncio
class TestContentOptimizationAgent:
    async def test_content_audit(self):
        agent = ContentOptimizationAgent()

        context = {
            "content_urls": ["https://example.com/blog/post1"],
            "target_keywords": ["seo optimization"],
        }

        with patch.object(agent, '_create_executor') as mock_exec:
            mock_executor = AsyncMock()
            mock_executor.ainvoke = AsyncMock(return_value={
                "output": "Content audit results"
            })
            mock_exec.return_value = mock_executor

            result = await agent.run(context)

        assert result.status == "success"
        assert "content_audits" in result.data
```

### 9.4 E2E Tests

```python
# tests/e2e/test_full_workflow.py
import pytest
import pytest_asyncio
from src.agents.coordinator import CoordinatorAgent

@pytest.mark.asyncio
class TestFullSEOWorkflow:
    async def test_complete_seo_analysis(self):
        """Test the full SEO workflow from keyword research to analytics."""
        coordinator = CoordinatorAgent()

        # Mock all agent executors
        with patch('src.agents.keyword_research_agent.KeywordResearchAgent._create_executor') as kw_mock, \
             patch('src.agents.content_optimization_agent.ContentOptimizationAgent._create_executor') as co_mock, \
             patch('src.agents.technical_seo_agent.TechnicalSEOAgent._create_executor') as ts_mock, \
             patch('src.agents.link_building_agent.LinkBuildingAgent._create_executor') as lb_mock, \
             patch('src.agents.seo_monitoring_agent.SEOMonitoringAgent._create_executor') as mo_mock, \
             patch('src.agents.performance_analytics_agent.PerformanceAnalyticsAgent._create_executor') as pa_mock:

            for mock in [kw_mock, co_mock, ts_mock, lb_mock, mo_mock, pa_mock]:
                mock_executor = AsyncMock()
                mock_executor.ainvoke = AsyncMock(return_value={
                    "output": "Agent results"
                })
                mock.return_value = mock_executor

            result = await coordinator.execute(
                objective="Comprehensive SEO analysis and optimization",
                domain="example.com",
            )

        assert result is not None
        assert "results" in result or len(result) > 0
```

### 9.5 Test Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Run specific test categories
pytest tests/unit/ -v -m "unit"
pytest tests/integration/ -v -m "integration"
pytest tests/e2e/ -v -m "e2e"

# Run with async support
pytest tests/ -v --asyncio-mode=auto

# Run with debugging
pytest tests/ -v --pdb

# Generate coverage report
pytest tests/ --cov=src --cov-report=xml:coverage.xml
```

### 9.6 CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: SEO Agents CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run linting
        run: |
          ruff check src/ tests/
          mypy src/

      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Run integration tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          SEMRUSH_API_KEY: ${{ secrets.SEMRUSH_API_KEY }}
        run: |
          pytest tests/integration/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### 9.7 Performance Testing

```python
# tests/performance/test_agent_performance.py
import pytest
import time
from src.agents.keyword_research_agent import KeywordResearchAgent

@pytest.mark.asyncio
class TestAgentPerformance:
    async def test_keyword_research_performance(self):
        """Ensure keyword research completes within acceptable time."""
        agent = KeywordResearchAgent("key1", "key2", "key3")

        context = {
            "domain": "example.com",
            "competitors": ["c1.com", "c2.com"],
            "seed_keywords": ["seo", "marketing"],
        }

        start = time.time()
        with patch.object(agent, '_create_executor') as mock_exec:
            mock_executor = AsyncMock()
            mock_executor.ainvoke = AsyncMock(return_value={"output": "results"})
            mock_exec.return_value = mock_executor
            result = await agent.run(context)
        elapsed = time.time() - start

        assert elapsed < 30, f"Agent took {elapsed}s, expected < 30s"
        assert result.execution_time_ms < 30000

    @pytest.mark.parametrize("num_keywords", [10, 50, 100])
    async def test_scalability(self, num_keywords):
        """Test agent performance with varying keyword counts."""
        keywords = [f"keyword_{i}" for i in range(num_keywords)]
        # Performance assertions here
```

---

## Summary

This implementation plan provides a complete blueprint for building an AI-powered SEO system using LangChain DeepAgents. The architecture consists of:

1. **Coordinator Agent** - Orchestrates the workflow and manages task distribution
2. **Keyword Research Agent** - Discovers and prioritizes keywords using multiple data sources
3. **Content Optimization Agent** - Audits and optimizes content for SEO performance
4. **Technical SEO Agent** - Identifies and prioritizes technical issues
5. **Link Building Agent** - Finds and evaluates link building opportunities
6. **SEO Monitoring Agent** - Tracks rankings, SERP changes, and competitor movements
7. **Performance Analytics Agent** - Aggregates data and generates reports

Each agent is built on a shared base class with consistent interfaces, error handling, and result formatting. The system uses LangGraph for workflow orchestration, Pydantic for data validation, and integrates with major SEO APIs (SEMrush, Ahrefs, SerpAPI, Google Search Console, PageSpeed Insights).

The testing strategy covers unit tests, integration tests, and end-to-end tests with mocking for external API dependencies.

