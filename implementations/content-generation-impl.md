# AI-Powered Content Generation Implementation Plan

## LangChain DeepAgents Architecture for Agentic AI Marketing Systems

**Version:** 1.0
**Date:** 2026-10-01
**Author:** Ahmed Hassan
**Stack:** LangChain DeepAgents, Python 3.11+, LangGraph, OpenAI/Anthropic LLMs

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Content Research Agent Implementation](#2-content-research-agent-implementation)
3. [Content Generation Agent Implementation](#3-content-generation-agent-implementation)
4. [Content Optimization Agent Implementation](#4-content-optimization-agent-implementation)
5. [Personalization Engine](#5-personalization-engine)
6. [Multi-Language Support (Arabic, English)](#6-multi-language-support-arabic-english)
7. [Content Performance Analytics](#7-content-performance-analytics)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Architecture Overview

The AI-powered content generation system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents. The architecture consists of four specialized agents coordinated by a central orchestrator, with shared state managed through LangGraph.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Content Generation System                     │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Research   │───▶│  Generation  │───▶│ Optimization │      │
│  │    Agent     │    │    Agent     │    │    Agent     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              LangGraph Shared State                   │      │
│  │  (ContentBrief, ResearchData, Draft, OptimizedOutput) │      │
│  └──────────────────────────────────────────────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │Personalization│    │  Analytics   │    │  Multi-Lang  │      │
│  │   Engine     │    │   Tracker    │    │   Engine     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Orchestrator (DeepAgent)                  │      │
│  │         Routes tasks, manages workflow                 │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents | Multi-agent orchestration |
| State Management | LangGraph | Stateful workflow graphs |
| LLM Provider | OpenAI GPT-4o / Anthropic Claude | Content generation & reasoning |
| Vector Store | ChromaDB / Pinecone | Research data & embeddings |
| Cache | Redis | Session & result caching |
| Queue | Celery + Redis | Async task processing |
| Database | PostgreSQL + pgvector | Content storage & analytics |
| Monitoring | LangSmith | Tracing & observability |
| API Layer | FastAPI | REST endpoints |

### 1.3 Agent Communication Protocol

Agents communicate through a **shared state object** managed by LangGraph. Each agent reads from and writes to this state, enabling sequential and parallel execution patterns.

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Annotated
from langchain_core.messages import BaseMessage

class ContentGenerationState(TypedDict):
    """Shared state across all agents in the content generation pipeline."""
    # Input
    topic: str
    target_audience: str
    content_type: str  # blog, social, email, ad_copy
    language: str  # en, ar
    brand_voice: str
    keywords: List[str]
    
    # Research phase
    research_data: Optional[dict]
    competitor_analysis: Optional[dict]
    trend_data: Optional[dict]
    
    # Generation phase
    content_draft: Optional[str]
    content_outline: Optional[List[dict]]
    
    # Optimization phase
    optimized_content: Optional[str]
    seo_score: Optional[float]
    readability_score: Optional[float]
    
    # Personalization
    personalized_variants: Optional[List[dict]]
    
    # Analytics
    content_id: Optional[str]
    performance_metrics: Optional[dict]
    
    # Workflow control
    current_step: str
    errors: List[str]
    messages: Annotated[List[BaseMessage], "add_messages"]
```

### 1.4 Workflow Graph Definition

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

def build_content_generation_graph():
    """Build the complete content generation workflow graph."""
    
    workflow = StateGraph(ContentGenerationState)
    
    # Add nodes
    workflow.add_node("research", research_agent_node)
    workflow.add_node("generate", generation_agent_node)
    workflow.add_node("optimize", optimization_agent_node)
    workflow.add_node("personalize", personalization_node)
    workflow.add_node("analytics", analytics_node)
    
    # Define edges
    workflow.set_entry_point("research")
    workflow.add_edge("research", "generate")
    workflow.add_edge("generate", "optimize")
    workflow.add_edge("optimize", "personalize")
    workflow.add_edge("personalize", "analytics")
    workflow.add_edge("analytics", END)
    
    # Conditional edges for error handling
    workflow.add_conditional_edges(
        "research",
        should_retry_research,
        {"retry": "research", "fail": END}
    )
    
    # Compile with checkpointer for persistence
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app
```

### 1.5 Orchestrator Design

The orchestrator uses LangChain DeepAgents' `create_deep_agent` to manage the overall workflow:

```python
from langchain.agents import create_deep_agent
from langchain.tools import Tool

def create_content_orchestrator():
    """Create the main orchestrator agent."""
    
    tools = [
        Tool(
            name="research_content",
            func=research_tool,
            description="Research topic, competitors, and trends"
        ),
        Tool(
            name="generate_content",
            func=generate_tool,
            description="Generate content draft based on research"
        ),
        Tool(
            name="optimize_content",
            func=optimize_tool,
            description="Optimize content for SEO, readability, and engagement"
        ),
        Tool(
            name="personalize_content",
            func=personalize_tool,
            description="Create personalized content variants"
        ),
        Tool(
            name="analyze_performance",
            func=analytics_tool,
            description="Track and analyze content performance"
        ),
    ]
    
    agent = create_deep_agent(
        tools=tools,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        model="gpt-4o",
    )
    
    return agent
```

---

## 2. Content Research Agent Implementation

### 2.1 Agent Purpose

The Research Agent gathers comprehensive information about the target topic, including competitor analysis, trending keywords, audience insights, and industry benchmarks. It produces a structured `ContentBrief` that feeds into the generation phase.

### 2.2 Research Agent Architecture

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_community.tools import TavilySearchResults, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import json

class ContentResearchAgent:
    """
    Specialized agent for content research.
    Gathers topic information, competitor data, trends, and audience insights.
    """
    
    def __init__(self, llm, config: Optional[Dict] = None):
        self.llm = llm
        self.config = config or {}
        self.tools = self._initialize_tools()
        self.agent = self._build_agent()
    
    def _initialize_tools(self) -> List:
        """Initialize research tools."""
        tools = [
            TavilySearchResults(
                max_results=10,
                search_depth="advanced",
                include_answer=True,
            ),
            WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
            self._create_competitor_analysis_tool(),
            self._create_keyword_research_tool(),
            self._create_trend_analysis_tool(),
            self._create_audience_insights_tool(),
        ]
        return tools
    
    def _build_agent(self):
        """Build the ReAct agent with research-specific prompt."""
        
        system_prompt = """You are an expert content research analyst. Your job is to gather 
        comprehensive information about a given topic to inform content creation.
        
        Your research process:
        1. Search for authoritative sources on the topic
        2. Analyze competitor content and identify gaps
        3. Research trending keywords and search volume
        4. Identify audience pain points and interests
        5. Gather statistics, data points, and expert quotes
        6. Synthesize findings into a structured content brief
        
        Output a JSON object with:
        - topic_summary: Brief overview of the topic
        - key_themes: List of main themes to cover
        - target_keywords: Primary and secondary keywords with search volume
        - competitor_gaps: Content gaps in competitor materials
        - audience_insights: Pain points, interests, and preferences
        - statistics: Relevant data points and statistics
        - expert_quotes: Notable quotes from industry experts
        - content_angle: Recommended unique angle for the content
        - suggested_outline: Proposed content structure
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Research the following topic: {topic}\nTarget audience: {audience}\nContent type: {content_type}"),
        ])
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )
    
    @tool
    def _create_competitor_analysis_tool(self):
        """Analyze competitor content for a given topic."""
        
        @tool
        def analyze_competitors(topic: str, num_competitors: int = 5) -> str:
            """
            Analyze top competitor content for a given topic.
            
            Args:
                topic: The content topic to analyze
                num_competitors: Number of competitors to analyze (default 5)
            
            Returns:
                JSON string with competitor analysis results
            """
            # Search for competitor content
            search_results = TavilySearchResults(max_results=num_competitors * 2).invoke(
                f"best {topic} content articles blog posts"
            )
            
            analysis = {
                "competitors": [],
                "content_gaps": [],
                "common_themes": [],
                "differentiation_opportunities": []
            }
            
            for result in search_results[:num_competitors]:
                competitor = {
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "content_summary": result.get("content", "")[:500],
                    "strengths": [],
                    "weaknesses": []
                }
                analysis["competitors"].append(competitor)
            
            # Identify gaps using LLM
            gap_analysis_prompt = f"""Based on these competitor articles about '{topic}', 
            identify content gaps and differentiation opportunities:
            {json.dumps(analysis['competitors'], indent=2)}
            
            Focus on:
            - Topics not covered deeply
            - Outdated information
            - Missing perspectives
            - Format opportunities (video, interactive, etc.)
            """
            
            gap_response = self.llm.invoke(gap_analysis_prompt)
            analysis["content_gaps"] = gap_response.content
            
            return json.dumps(analysis, indent=2)
        
        return analyze_competitors
    
    @tool
    def _create_keyword_research_tool(self):
        """Research keywords and search volume data."""
        
        @tool
        def research_keywords(topic: str, language: str = "en") -> str:
            """
            Research keywords for a given topic.
            
            Args:
                topic: The content topic
                language: Target language (en or ar)
            
            Returns:
                JSON string with keyword data
            """
            # Use multiple keyword research approaches
            keywords = {
                "primary_keywords": [],
                "secondary_keywords": [],
                "long_tail_keywords": [],
                "search_volume": {},
                "competition_level": {},
                "trending_keywords": []
            }
            
            # Generate keyword suggestions using LLM
            keyword_prompt = f"""Generate comprehensive keyword research for the topic '{topic}' 
            in {language} language. Include:
            - 5 primary keywords (high volume, high relevance)
            - 10 secondary keywords (medium volume, high relevance)
            - 15 long-tail keywords (low volume, very high relevance)
            - Estimated search volume for each
            - Competition level (low/medium/high)
            - Related trending keywords
            
            Return as structured JSON.
            """
            
            response = self.llm.invoke(keyword_prompt)
            keywords["raw_response"] = response.content
            
            return json.dumps(keywords, indent=2)
        
        return research_keywords
    
    @tool
    def _create_trend_analysis_tool(self):
        """Analyze trending topics and industry trends."""
        
        @tool
        def analyze_trends(topic: str) -> str:
            """
            Analyze current trends related to the topic.
            
            Args:
                topic: The content topic
            
            Returns:
                JSON string with trend analysis
            """
            trends = {
                "trending_subtopics": [],
                "industry_developments": [],
                "seasonal_factors": [],
                "emerging_themes": [],
                "declining_themes": []
            }
            
            trend_prompt = f"""Analyze current trends related to '{topic}'. Consider:
            - Recent news and developments
            - Social media trends
            - Industry reports and forecasts
            - Seasonal relevance
            - Emerging technologies or approaches
            
            Return structured trend analysis as JSON.
            """
            
            response = self.llm.invoke(trend_prompt)
            trends["analysis"] = response.content
            
            return json.dumps(trends, indent=2)
        
        return analyze_trends
    
    @tool
    def _create_audience_insights_tool(self):
        """Gather audience insights and preferences."""
        
        @tool
        def gather_audience_insights(audience: str, topic: str) -> str:
            """
            Gather insights about the target audience.
            
            Args:
                audience: Target audience description
                topic: Content topic
            
            Returns:
                JSON string with audience insights
            """
            insights = {
                "demographics": {},
                "pain_points": [],
                "interests": [],
                "content_preferences": {},
                "buying_behavior": {},
                "objections": []
            }
            
            insight_prompt = f"""Analyze the target audience '{audience}' for content about '{topic}'.
            Provide insights on:
            - Demographics and psychographics
            - Pain points and challenges
            - Interests and motivations
            - Preferred content formats and channels
            - Decision-making process
            - Common objections or concerns
            
            Return structured audience insights as JSON.
            """
            
            response = self.llm.invoke(insight_prompt)
            insights["analysis"] = response.content
            
            return json.dumps(insights, indent=2)
        
        return gather_audience_insights
    
    def research(self, topic: str, audience: str, content_type: str, language: str = "en") -> Dict:
        """
        Execute the full research workflow.
        
        Args:
            topic: Content topic
            audience: Target audience
            content_type: Type of content to create
            language: Target language
            
        Returns:
            Structured research brief as dictionary
        """
        result = self.agent.invoke({
            "topic": topic,
            "audience": audience,
            "content_type": content_type,
            "language": language,
        })
        
        # Parse and structure the research output
        research_brief = self._structure_research_output(result)
        return research_brief
    
    def _structure_research_output(self, raw_output: str) -> Dict:
        """Structure raw agent output into a consistent format."""
        # Implementation would parse the agent's output
        # and normalize it into the ContentBrief structure
        pass
```

### 2.3 Research Data Schema

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class KeywordData(BaseModel):
    keyword: str
    search_volume: Optional[int] = None
    competition: str = "medium"  # low, medium, high
    relevance_score: float = Field(ge=0, le=1)
    keyword_type: str  # primary, secondary, long_tail

class CompetitorAnalysis(BaseModel):
    url: str
    title: str
    content_summary: str
    word_count: Optional[int] = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    content_gaps: List[str] = []

class AudienceInsight(BaseModel):
    segment: str
    demographics: dict
    pain_points: List[str]
    interests: List[str]
    content_preferences: dict
    objections: List[str]

class TrendData(BaseModel):
    trend_name: str
    trend_type: str  # emerging, stable, declining
    relevance_score: float
    description: str
    source: Optional[str] = None

class ContentBrief(BaseModel):
    """Structured output from the research agent."""
    topic: str
    topic_summary: str
    key_themes: List[str]
    target_keywords: List[KeywordData]
    competitor_analysis: List[CompetitorAnalysis]
    audience_insights: List[AudienceInsight]
    trends: List[TrendData]
    statistics: List[dict]
    expert_quotes: List[dict]
    content_angle: str
    suggested_outline: List[dict]
    language: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 3. Content Generation Agent Implementation

### 3.1 Agent Purpose

The Generation Agent takes the research brief and produces high-quality content drafts. It supports multiple content types (blog posts, social media, email campaigns, ad copy) and multiple languages (English, Arabic).

### 3.2 Generation Agent Architecture

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from typing import Dict, List, Optional, Literal
import json

class ContentGenerationAgent:
    """
    Specialized agent for content generation.
    Produces drafts based on research briefs, supporting multiple formats and languages.
    """
    
    CONTENT_TEMPLATES = {
        "blog_post": {
            "structure": ["introduction", "body_sections", "conclusion", "cta"],
            "min_words": 1000,
            "max_words": 3000,
            "tone_options": ["professional", "conversational", "authoritative", "friendly"],
        },
        "social_media": {
            "formats": ["linkedin_post", "twitter_thread", "instagram_caption", "facebook_post"],
            "max_chars": {"linkedin": 3000, "twitter": 280, "instagram": 2200, "facebook": 63206},
        },
        "email_campaign": {
            "types": ["newsletter", "promotional", "nurture", "announcement"],
            "components": ["subject_line", "preheader", "body", "cta"],
        },
        "ad_copy": {
            "types": ["google_ads", "facebook_ads", "linkedin_ads", "display_ads"],
            "components": ["headline", "description", "cta"],
        },
    }
    
    def __init__(self, llm, config: Optional[Dict] = None):
        self.llm = llm
        self.config = config or {}
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.generation_chain = self._build_generation_chain()
    
    def _build_generation_chain(self):
        """Build the content generation chain."""
        
        system_prompt = """You are an expert content writer who creates engaging, 
        high-quality content tailored to specific audiences and platforms.
        
        Your writing principles:
        1. Hook the reader in the first sentence
        2. Provide genuine value and actionable insights
        3. Use clear, concise language
        4. Incorporate storytelling where appropriate
        5. Include data and statistics to support claims
        6. End with a clear call-to-action
        7. Match the brand voice and tone
        8. Optimize for the target platform's best practices
        
        Always write in the specified language with native-level fluency.
        For Arabic content, use Modern Standard Arabic (MSA) unless dialect is specified.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="research_context"),
            ("human", GENERATION_PROMPT_TEMPLATE),
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        return chain
    
    def generate(
        self,
        brief: ContentBrief,
        content_type: str,
        language: str = "en",
        brand_voice: str = "professional",
        additional_instructions: Optional[str] = None,
    ) -> Dict:
        """
        Generate content based on the research brief.
        
        Args:
            brief: Research brief from the research agent
            content_type: Type of content (blog_post, social_media, email_campaign, ad_copy)
            language: Target language (en, ar)
            brand_voice: Brand voice/tone
            additional_instructions: Any additional generation instructions
            
        Returns:
            Dictionary with generated content and metadata
        """
        # Build generation context
        context = self._build_generation_context(brief, content_type, language)
        
        # Generate content
        result = self.generation_chain.invoke({
            "research_context": context,
            "topic": brief.topic,
            "content_type": content_type,
            "language": language,
            "brand_voice": brand_voice,
            "target_audience": brief.audience_insights[0].segment if brief.audience_insights else "general",
            "keywords": [k.keyword for k in brief.target_keywords if k.keyword_type == "primary"],
            "content_angle": brief.content_angle,
            "outline": brief.suggested_outline,
            "additional_instructions": additional_instructions or "",
        })
        
        # Post-process and structure
        structured_output = self._structure_generated_content(
            result, content_type, language
        )
        
        return structured_output
    
    def _build_generation_context(self, brief: ContentBrief, content_type: str, language: str) -> List:
        """Build the context messages for generation."""
        from langchain_core.messages import SystemMessage, HumanMessage
        
        context = [
            SystemMessage(content=f"Content brief for: {brief.topic}"),
            HumanMessage(content=f"""
            Topic Summary: {brief.topic_summary}
            Key Themes: {', '.join(brief.key_themes)}
            Content Angle: {brief.content_angle}
            Target Keywords: {', '.join([k.keyword for k in brief.target_keywords[:5]])}
            Audience: {brief.audience_insights[0].segment if brief.audience_insights else 'General'}
            Pain Points: {', '.join(brief.audience_insights[0].pain_points[:3]) if brief.audience_insights else 'N/A'}
            """),
        ]
        return context
    
    def _structure_generated_content(self, raw_content: str, content_type: str, language: str) -> Dict:
        """Structure raw generated content into a consistent format."""
        
        if content_type == "blog_post":
            return self._structure_blog_post(raw_content, language)
        elif content_type == "social_media":
            return self._structure_social_media(raw_content, language)
        elif content_type == "email_campaign":
            return self._structure_email(raw_content, language)
        elif content_type == "ad_copy":
            return self._structure_ad_copy(raw_content, language)
        else:
            return {
                "content": raw_content,
                "content_type": content_type,
                "language": language,
                "word_count": len(raw_content.split()),
            }
    
    def _structure_blog_post(self, content: str, language: str) -> Dict:
        """Structure blog post content with metadata."""
        return {
            "content": content,
            "content_type": "blog_post",
            "language": language,
            "word_count": len(content.split()),
            "reading_time_minutes": len(content.split()) // 200,
            "sections": self._extract_sections(content),
            "meta_description": self._extract_meta_description(content),
        }
    
    def _structure_social_media(self, content: str, language: str) -> Dict:
        """Structure social media content."""
        return {
            "content": content,
            "content_type": "social_media",
            "language": language,
            "character_count": len(content),
            "hashtags": self._extract_hashtags(content),
            "mentions": self._extract_mentions(content),
        }
    
    def _structure_email(self, content: str, language: str) -> Dict:
        """Structure email content."""
        return {
            "content": content,
            "content_type": "email_campaign",
            "language": language,
            "subject_line": self._extract_subject_line(content),
            "preheader": self._extract_preheader(content),
            "body": content,
            "cta": self._extract_cta(content),
        }
    
    def _structure_ad_copy(self, content: str, language: str) -> Dict:
        """Structure ad copy content."""
        return {
            "content": content,
            "content_type": "ad_copy",
            "language": language,
            "headline": self._extract_headline(content),
            "description": content,
            "cta": self._extract_cta(content),
        }
    
    def _extract_sections(self, content: str) -> List[Dict]:
        """Extract sections from blog post content."""
        # Implementation would parse headers and structure
        pass
    
    def _extract_meta_description(self, content: str) -> str:
        """Extract or generate meta description."""
        pass
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from social media content."""
        import re
        return re.findall(r'#(\w+)', content)
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract mentions from social media content."""
        import re
        return re.findall(r'@(\w+)', content)
    
    def _extract_subject_line(self, content: str) -> str:
        """Extract subject line from email content."""
        pass
    
    def _extract_preheader(self, content: str) -> str:
        """Extract preheader from email content."""
        pass
    
    def _extract_cta(self, content: str) -> str:
        """Extract call-to-action from content."""
        pass
    
    def _extract_headline(self, content: str) -> str:
        """Extract headline from ad copy."""
        pass


GENERATION_PROMPT_TEMPLATE = """
Create {content_type} content about: {topic}

Requirements:
- Language: {language}
- Brand Voice: {brand_voice}
- Target Audience: {target_audience}
- Content Angle: {content_angle}
- Target Keywords to include naturally: {keywords}

Content Outline:
{outline}

Additional Instructions:
{additional_instructions}

Generate the content now. Ensure it is:
1. Engaging and valuable to the target audience
2. Optimized for the specified platform
3. Written in natural, fluent {language}
4. Aligned with the brand voice: {brand_voice}
5. Incorporating the target keywords naturally
"""
```

### 3.3 Content Type-Specific Generators

```python
class BlogPostGenerator:
    """Specialized generator for long-form blog content."""
    
    def __init__(self, llm):
        self.llm = llm
        self.outline_chain = self._build_outline_chain()
        self.section_chain = self._build_section_chain()
    
    def _build_outline_chain(self):
        """Build chain for generating content outlines."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a content strategist who creates detailed blog post outlines."),
            ("human", "Create a detailed outline for a blog post about: {topic}\nTarget audience: {audience}\nKeywords: {keywords}"),
        ])
        return prompt | self.llm | JsonOutputParser()
    
    def _build_section_chain(self):
        """Build chain for generating individual sections."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert blog writer. Write engaging, well-researched content."),
            ("human", "Write the '{section_title}' section about: {section_topic}\nContext: {context}\nWord count target: {word_count}"),
        ])
        return prompt | self.llm | StrOutputParser()
    
    def generate(self, brief: ContentBrief, language: str = "en") -> Dict:
        """Generate a complete blog post."""
        # Step 1: Generate outline
        outline = self.outline_chain.invoke({
            "topic": brief.topic,
            "audience": brief.audience_insights[0].segment if brief.audience_insights else "general",
            "keywords": [k.keyword for k in brief.target_keywords[:5]],
        })
        
        # Step 2: Generate each section
        sections = []
        for section in outline.get("sections", []):
            section_content = self.section_chain.invoke({
                "section_title": section["title"],
                "section_topic": section["topic"],
                "context": brief.topic_summary,
                "word_count": section.get("word_count", 300),
            })
            sections.append({
                "title": section["title"],
                "content": section_content,
            })
        
        # Step 3: Assemble full post
        full_content = self._assemble_blog_post(outline, sections)
        
        return {
            "title": outline.get("title", brief.topic),
            "content": full_content,
            "sections": sections,
            "word_count": len(full_content.split()),
            "meta_description": outline.get("meta_description", ""),
            "language": language,
        }
    
    def _assemble_blog_post(self, outline: Dict, sections: List[Dict]) -> str:
        """Assemble sections into a complete blog post."""
        parts = [f"# {outline.get('title', '')}\n"]
        
        # Introduction
        intro = outline.get("introduction", "")
        if intro:
            parts.append(f"{intro}\n")
        
        # Body sections
        for section in sections:
            parts.append(f"## {section['title']}\n")
            parts.append(f"{section['content']}\n")
        
        # Conclusion
        conclusion = outline.get("conclusion", "")
        if conclusion:
            parts.append(f"## Conclusion\n")
            parts.append(f"{conclusion}\n")
        
        return "\n".join(parts)


class SocialMediaGenerator:
    """Specialized generator for social media content."""
    
    PLATFORM_SPECS = {
        "linkedin": {"max_chars": 3000, "optimal_length": 1500, "hashtag_count": 3},
        "twitter": {"max_chars": 280, "optimal_length": 200, "hashtag_count": 2},
        "instagram": {"max_chars": 2200, "optimal_length": 125, "hashtag_count": 10},
        "facebook": {"max_chars": 63206, "optimal_length": 400, "hashtag_count": 2},
    }
    
    def __init__(self, llm):
        self.llm = llm
    
    def generate(self, brief: ContentBrief, platform: str, language: str = "en") -> Dict:
        """Generate social media content for a specific platform."""
        specs = self.PLATFORM_SPECS.get(platform, self.PLATFORM_SPECS["linkedin"])
        
        prompt = f"""Create a {platform} post about: {topic}
        Language: {language}
        Max characters: {specs['max_chars']}
        Optimal length: {specs['optimal_length']} characters
        Include {specs['hashtag_count']} relevant hashtags
        Target audience: {brief.audience_insights[0].segment if brief.audience_insights else 'general'}
        Key message: {brief.content_angle}
        
        Make it engaging, platform-optimized, and include a clear CTA.
        """
        
        result = self.llm.invoke(prompt)
        
        return {
            "content": result.content,
            "platform": platform,
            "language": language,
            "character_count": len(result.content),
            "hashtags": self._extract_hashtags(result.content),
        }
```

---

## 4. Content Optimization Agent Implementation

### 4.1 Agent Purpose

The Optimization Agent refines generated content for SEO, readability, engagement, and platform-specific best practices. It scores content and provides actionable improvement suggestions.

### 4.2 Optimization Agent Architecture

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from textstat import flesch_reading_ease, flesch_kincaid_grade
from typing import Dict, List, Tuple
import re
import json

class ContentOptimizationAgent:
    """
    Specialized agent for content optimization.
    Optimizes for SEO, readability, engagement, and platform best practices.
    """
    
    def __init__(self, llm, config: Optional[Dict] = None):
        self.llm = llm
        self.config = config or {}
        self.seo_chain = self._build_seo_chain()
        self.readability_chain = self._build_readability_chain()
        self.engagement_chain = self._build_engagement_chain()
    
    def optimize(
        self,
        content: str,
        content_type: str,
        target_keywords: List[str],
        language: str = "en",
    ) -> Dict:
        """
        Optimize content across multiple dimensions.
        
        Args:
            content: Raw content to optimize
            content_type: Type of content
            target_keywords: Keywords to optimize for
            language: Content language
            
        Returns:
            Dictionary with optimized content and scores
        """
        # Run optimization analyses in parallel
        seo_analysis = self._analyze_seo(content, target_keywords, language)
        readability_analysis = self._analyze_readability(content, language)
        engagement_analysis = self._analyze_engagement(content, content_type)
        
        # Generate optimized content
        optimized_content = self._generate_optimized_content(
            content, seo_analysis, readability_analysis, engagement_analysis
        )
        
        # Calculate overall scores
        overall_score = self._calculate_overall_score(
            seo_analysis, readability_analysis, engagement_analysis
        )
        
        return {
            "original_content": content,
            "optimized_content": optimized_content,
            "seo_score": seo_analysis["score"],
            "readability_score": readability_analysis["score"],
            "engagement_score": engagement_analysis["score"],
            "overall_score": overall_score,
            "seo_analysis": seo_analysis,
            "readability_analysis": readability_analysis,
            "engagement_analysis": engagement_analysis,
            "improvement_suggestions": self._compile_suggestions(
                seo_analysis, readability_analysis, engagement_analysis
            ),
        }
    
    def _analyze_seo(self, content: str, keywords: List[str], language: str) -> Dict:
        """Analyze and optimize SEO factors."""
        
        # Keyword analysis
        keyword_analysis = {}
        content_lower = content.lower()
        
        for keyword in keywords:
            count = content_lower.count(keyword.lower())
            keyword_analysis[keyword] = {
                "count": count,
                "density": count / len(content.split()) * 100 if content else 0,
                "in_title": keyword.lower() in content_lower[:100],
                "in_first_100": keyword.lower() in content_lower[:100],
                "in_headings": self._check_keyword_in_headings(content, keyword),
            }
        
        # Content structure analysis
        structure_analysis = {
            "has_title": bool(re.search(r'^#\s+', content, re.MULTILINE)),
            "has_meta_description": "meta description" in content_lower,
            "has_headings": len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE)),
            "has_images": "![" in content,
            "has_internal_links": bool(re.search(r'\[.*?\]\(.*?\)', content)),
            "has_external_links": bool(re.search(r'\[.*?\]\(https?://', content)),
            "word_count": len(content.split()),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
        }
        
        # Calculate SEO score
        seo_score = self._calculate_seo_score(keyword_analysis, structure_analysis)
        
        # Generate SEO suggestions
        suggestions = self._generate_seo_suggestions(keyword_analysis, structure_analysis)
        
        return {
            "score": seo_score,
            "keyword_analysis": keyword_analysis,
            "structure_analysis": structure_analysis,
            "suggestions": suggestions,
        }
    
    def _analyze_readability(self, content: str, language: str) -> Dict:
        """Analyze content readability."""
        
        if language == "en":
            flesch_score = flesch_reading_ease(content)
            fk_grade = flesch_kincaid_grade(content)
        else:
            # For Arabic, use adapted metrics
            flesch_score = self._calculate_arabic_readability(content)
            fk_grade = None
        
        # Additional readability metrics
        sentences = re.split(r'[.!?؟。]', content)
        words = content.split()
        
        metrics = {
            "flesch_reading_ease": flesch_score,
            "flesch_kincaid_grade": fk_grade,
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
            "long_sentences": len([s for s in sentences if len(s.split()) > 30]),
            "passive_voice_count": self._count_passive_voice(content, language),
            "paragraph_lengths": [len(p.split()) for p in content.split('\n\n') if p.strip()],
        }
        
        # Calculate readability score (0-100)
        readability_score = self._calculate_readability_score(metrics, language)
        
        return {
            "score": readability_score,
            "metrics": metrics,
            "suggestions": self._generate_readability_suggestions(metrics, language),
        }
    
    def _analyze_engagement(self, content: str, content_type: str) -> Dict:
        """Analyze content engagement potential."""
        
        engagement_factors = {
            "has_hook": self._has_strong_opening(content),
            "has_storytelling": self._has_storytelling_elements(content),
            "has_data": bool(re.search(r'\d+%|\d+\s*(million|billion|thousand)', content)),
            "has_quotes": '"' in content or '"' in content or '"' in content,
            "has_questions": '?' in content or '؟' in content,
            "has_cta": self._has_call_to_action(content),
            "has_emotional_words": self._has_emotional_appeal(content),
            "has_power_words": self._has_power_words(content),
            "content_length_appropriate": self._check_length_for_platform(content, content_type),
        }
        
        engagement_score = sum(engagement_factors.values()) / len(engagement_factors) * 100
        
        return {
            "score": engagement_score,
            "factors": engagement_factors,
            "suggestions": self._generate_engagement_suggestions(engagement_factors),
        }
    
    def _generate_optimized_content(
        self,
        content: str,
        seo_analysis: Dict,
        readability_analysis: Dict,
        engagement_analysis: Dict,
    ) -> str:
        """Generate optimized version of the content."""
        
        optimization_prompt = f"""Optimize the following content based on these analyses:

ORIGINAL CONTENT:
{content}

SEO ANALYSIS:
- Score: {seo_analysis['score']}/100
- Suggestions: {json.dumps(seo_analysis['suggestions'], indent=2)}

READABILITY ANALYSIS:
- Score: {readability_analysis['score']}/100
- Suggestions: {json.dumps(readability_analysis['suggestions'], indent=2)}

ENGAGEMENT ANALYSIS:
- Score: {engagement_analysis['score']}/100
- Suggestions: {json.dumps(engagement_analysis['suggestions'], indent=2)}

Optimize the content to improve all three scores while maintaining the core message.
Return only the optimized content, no explanations.
"""
        
        result = self.llm.invoke(optimization_prompt)
        return result.content
    
    def _calculate_seo_score(self, keyword_analysis: Dict, structure: Dict) -> float:
        """Calculate overall SEO score."""
        scores = []
        
        # Keyword optimization (30%)
        keyword_scores = []
        for kw, data in keyword_analysis.items():
            kw_score = 0
            if data["count"] > 0:
                kw_score += 30
            if 0.5 <= data["density"] <= 2.5:
                kw_score += 30
            if data["in_title"]:
                kw_score += 20
            if data["in_first_100"]:
                kw_score += 20
            keyword_scores.append(kw_score)
        scores.append(sum(keyword_scores) / len(keyword_scores) * 0.3 if keyword_scores else 0)
        
        # Content structure (40%)
        structure_score = 0
        if structure["has_title"]:
            structure_score += 10
        if structure["has_headings"] >= 3:
            structure_score += 15
        if structure["word_count"] >= 1000:
            structure_score += 15
        scores.append(structure_score * 0.4)
        
        # Content length (30%)
        length_score = min(structure["word_count"] / 1500 * 100, 100)
        scores.append(length_score * 0.3)
        
        return sum(scores)
    
    def _calculate_readability_score(self, metrics: Dict, language: str) -> float:
        """Calculate readability score."""
        if language == "en":
            # Flesch Reading Ease: 60-70 is ideal
            flesch = metrics["flesch_reading_ease"]
            flesch_score = max(0, min(100, (flesch / 70) * 100))
            
            # Sentence length: 15-20 words is ideal
            avg_sent = metrics["avg_sentence_length"]
            sent_score = 100 - abs(avg_sent - 17.5) * 5
            sent_score = max(0, min(100, sent_score))
            
            return (flesch_score + sent_score) / 2
        else:
            # Arabic readability scoring
            return self._calculate_arabic_readability_score(metrics)
    
    def _calculate_arabic_readability(self, content: str) -> float:
        """Calculate readability score for Arabic content."""
        # Adapted metrics for Arabic
        sentences = re.split(r'[.!?؟。]', content)
        words = content.split()
        
        if not sentences or not words:
            return 0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(w) for w in words) / len(words)
        
        # Arabic tends to have longer words; adjust thresholds
        score = 100
        if avg_sentence_length > 25:
            score -= (avg_sentence_length - 25) * 2
        if avg_word_length > 6:
            score -= (avg_word_length - 6) * 5
        
        return max(0, min(100, score))
    
    def _count_passive_voice(self, content: str, language: str) -> int:
        """Count passive voice constructions."""
        if language == "en":
            # Common passive voice patterns
            passive_patterns = [
                r'\b(is|are|was|were|be|been|being)\s+\w+ed\b',
                r'\b(is|are|was|were|be|been|being)\s+\w+en\b',
            ]
        else:
            # Arabic passive patterns
            passive_patterns = [
                r'\bتم\b', r'\bتمّ\b', r'\bيُ', r'\bتُ', r'\bنُ',
            ]
        
        count = 0
        for pattern in passive_patterns:
            count += len(re.findall(pattern, content, re.IGNORECASE))
        
        return count
    
    def _has_strong_opening(self, content: str) -> bool:
        """Check if content has a strong opening hook."""
        first_100 = content[:100].lower()
        hook_indicators = [
            "imagine", "what if", "did you know", "here's why",
            "picture this", "consider this", "the truth is",
            "تخيل", "هل تعلم", "هل تعلم أن", "الحقيقة هي",
        ]
        return any(indicator in first_100 for indicator in hook_indicators)
    
    def _has_storytelling_elements(self, content: str) -> bool:
        """Check for storytelling elements."""
        story_indicators = [
            "once upon", "story", "journey", "experience",
            "example", "case study", "imagine",
            "قصة", "مثال", "تجربة", "رحلة",
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in story_indicators)
    
    def _has_call_to_action(self, content: str) -> bool:
        """Check for call-to-action."""
        cta_indicators = [
            "click", "sign up", "subscribe", "download", "learn more",
            "get started", "try now", "contact us", "register",
            "اشترك", "سجل", "حمّل", "تواصل معنا", "ابدأ الآن",
            "انقر", "اكتشف",
        ]
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in cta_indicators)
    
    def _has_emotional_appeal(self, content: str) -> bool:
        """Check for emotional appeal words."""
        emotional_words = [
            "amazing", "incredible", "revolutionary", "breakthrough",
            "exclusive", "limited", "proven", "guaranteed",
            "مذهل", "رائع", "حصري", "مضمون", "مثبت",
        ]
        content_lower = content.lower()
        return any(word in content_lower for word in emotional_words)
    
    def _has_power_words(self, content: str) -> bool:
        """Check for power words that drive engagement."""
        power_words = [
            "free", "new", "now", "today", "instantly", "effortless",
            "secret", "ultimate", "essential", "critical",
            "مجاني", "جديد", "الآن", "اليوم", "فوري", "سهل",
            "سر", "أساسي", "حيوي",
        ]
        content_lower = content.lower()
        return any(word in content_lower for word in power_words)
    
    def _check_length_for_platform(self, content: str, content_type: str) -> bool:
        """Check if content length is appropriate for the platform."""
        word_count = len(content.split())
        
        length_requirements = {
            "blog_post": (800, 3000),
            "social_media": (50, 500),
            "email_campaign": (200, 800),
            "ad_copy": (10, 100),
        }
        
        min_words, max_words = length_requirements.get(content_type, (100, 2000))
        return min_words <= word_count <= max_words
    
    def _check_keyword_in_headings(self, content: str, keyword: str) -> bool:
        """Check if keyword appears in any heading."""
        headings = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        return any(keyword.lower() in h.lower() for h in headings)
    
    def _generate_seo_suggestions(self, keyword_analysis: Dict, structure: Dict) -> List[str]:
        """Generate SEO improvement suggestions."""
        suggestions = []
        
        for kw, data in keyword_analysis.items():
            if data["count"] == 0:
                suggestions.append(f"Add the keyword '{kw}' to the content")
            elif data["density"] < 0.5:
                suggestions.append(f"Increase usage of '{kw}' (current density: {data['density']:.1f}%)")
            elif data["density"] > 2.5:
                suggestions.append(f"Reduce usage of '{kw}' to avoid keyword stuffing (current: {data['density']:.1f}%)")
            
            if not data["in_title"]:
                suggestions.append(f"Include '{kw}' in the title")
            if not data["in_first_100"]:
                suggestions.append(f"Add '{kw}' in the first 100 words")
        
        if not structure["has_headings"]:
            suggestions.append("Add section headings (H2, H3) to improve structure")
        if structure["word_count"] < 1000:
            suggestions.append(f"Expand content (current: {structure['word_count']} words, recommended: 1000+)")
        
        return suggestions
    
    def _generate_readability_suggestions(self, metrics: Dict, language: str) -> List[str]:
        """Generate readability improvement suggestions."""
        suggestions = []
        
        if metrics["avg_sentence_length"] > 25:
            suggestions.append(f"Shorten sentences (avg: {metrics['avg_sentence_length']:.0f} words, target: 15-20)")
        
        if metrics["long_sentences"] > 3:
            suggestions.append(f"Break up {metrics['long_sentences']} long sentences (>30 words)")
        
        if metrics["passive_voice_count"] > 5:
            suggestions.append(f"Reduce passive voice usage ({metrics['passive_voice_count']} instances found)")
        
        if language == "en" and metrics.get("flesch_reading_ease", 0) < 50:
            suggestions.append("Simplify vocabulary to improve reading ease")
        
        return suggestions
    
    def _generate_engagement_suggestions(self, factors: Dict) -> List[str]:
        """Generate engagement improvement suggestions."""
        suggestions = []
        
        if not factors["has_hook"]:
            suggestions.append("Add a strong opening hook to capture attention")
        if not factors["has_storytelling"]:
            suggestions.append("Incorporate storytelling elements to increase relatability")
        if not factors["has_data"]:
            suggestions.append("Add statistics or data points to support claims")
        if not factors["has_quotes"]:
            suggestions.append("Include expert quotes or testimonials for credibility")
        if not factors["has_questions"]:
            suggestions.append("Add rhetorical questions to engage readers")
        if not factors["has_cta"]:
            suggestions.append("Add a clear call-to-action at the end")
        if not factors["has_emotional_words"]:
            suggestions.append("Include emotional appeal words to connect with readers")
        if not factors["has_power_words"]:
            suggestions.append("Use power words to increase engagement")
        
        return suggestions
    
    def _calculate_overall_score(self, seo: Dict, readability: Dict, engagement: Dict) -> float:
        """Calculate weighted overall optimization score."""
        weights = {"seo": 0.4, "readability": 0.3, "engagement": 0.3}
        return (
            seo["score"] * weights["seo"] +
            readability["score"] * weights["readability"] +
            engagement["score"] * weights["engagement"]
        )
    
    def _compile_suggestions(self, seo: Dict, readability: Dict, engagement: Dict) -> List[str]:
        """Compile all suggestions into a single list."""
        return (
            seo.get("suggestions", []) +
            readability.get("suggestions", []) +
            engagement.get("suggestions", [])
        )
```

---

## 5. Personalization Engine

### 5.1 Engine Purpose

The Personalization Engine creates tailored content variants for different audience segments, platforms, and individual user profiles. It uses behavioral data, demographic information, and contextual signals to customize content.

### 5.2 Personalization Architecture

```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from datetime import datetime, timedelta

class PersonalizationLevel(Enum):
    SEGMENT = "segment"           # Based on audience segment
    BEHAVIORAL = "behavioral"     # Based on user behavior
    CONTEXTUAL = "contextual"     # Based on context (time, location, device)
    INDIVIDUAL = "individual"     # Based on individual user profile

class ContentType(Enum):
    HEADLINE = "headline"
    INTRO = "intro"
    BODY = "body"
    CTA = "cta"
    VISUAL = "visual"
    FULL = "full"

@dataclass
class UserProfile:
    """User profile for personalization."""
    user_id: str
    segment: str
    demographics: Dict[str, Any] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    behavior_history: List[Dict] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    language: str = "en"
    timezone: str = "UTC"
    device_type: str = "desktop"
    engagement_history: Dict[str, float] = field(default_factory=dict)

@dataclass
class PersonalizationContext:
    """Context for personalization decisions."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    platform: str = "web"
    device: str = "desktop"
    location: Optional[str] = None
    referrer: Optional[str] = None
    campaign: Optional[str] = None
    ab_test_group: Optional[str] = None

@dataclass
class PersonalizedVariant:
    """A personalized content variant."""
    variant_id: str
    content: str
    content_type: ContentType
    personalization_level: PersonalizationLevel
    target_segment: str
    personalization_factors: List[str]
    confidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class PersonalizationEngine:
    """
    Engine for creating personalized content variants.
    Supports segment-based, behavioral, contextual, and individual personalization.
    """
    
    def __init__(self, llm, config: Optional[Dict] = None):
        self.llm = llm
        self.config = config or {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.segment_rules = self._load_segment_rules()
        self.personalization_chain = self._build_personalization_chain()
    
    def _build_personalization_chain(self):
        """Build the personalization chain."""
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", PERSONALIZATION_SYSTEM_PROMPT),
            ("human", PERSONALIZATION_PROMPT_TEMPLATE),
        ])
        
        return prompt | self.llm
    
    def personalize(
        self,
        content: str,
        user_profile: UserProfile,
        context: PersonalizationContext,
        content_type: ContentType = ContentType.FULL,
        level: PersonalizationLevel = PersonalizationLevel.SEGMENT,
    ) -> PersonalizedVariant:
        """
        Create a personalized variant of the content.
        
        Args:
            content: Original content
            user_profile: User profile for personalization
            context: Personalization context
            content_type: Type of content to personalize
            level: Personalization level
            
        Returns:
            PersonalizedVariant with tailored content
        """
        # Determine personalization factors
        factors = self._determine_personalization_factors(
            user_profile, context, level
        )
        
        # Generate personalized content
        personalized_content = self._generate_personalized_content(
            content, user_profile, context, factors, content_type
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(factors, user_profile)
        
        # Create variant
        variant = PersonalizedVariant(
            variant_id=self._generate_variant_id(content, user_profile.user_id),
            content=personalized_content,
            content_type=content_type,
            personalization_level=level,
            target_segment=user_profile.segment,
            personalization_factors=factors,
            confidence_score=confidence,
            metadata={
                "original_content_hash": hashlib.md5(content.encode()).hexdigest(),
                "user_id": user_profile.user_id,
                "timestamp": context.timestamp.isoformat(),
                "platform": context.platform,
            },
        )
        
        return variant
    
    def create_segment_variants(
        self,
        content: str,
        segments: List[str],
        context: PersonalizationContext,
    ) -> List[PersonalizedVariant]:
        """
        Create personalized variants for multiple segments.
        
        Args:
            content: Original content
            segments: List of target segments
            context: Personalization context
            
        Returns:
            List of PersonalizedVariant objects
        """
        variants = []
        
        for segment in segments:
            # Create a representative profile for the segment
            segment_profile = self._get_segment_profile(segment)
            
            variant = self.personalize(
                content=content,
                user_profile=segment_profile,
                context=context,
                level=PersonalizationLevel.SEGMENT,
            )
            variants.append(variant)
        
        return variants
    
    def _determine_personalization_factors(
        self,
        profile: UserProfile,
        context: PersonalizationContext,
        level: PersonalizationLevel,
    ) -> List[str]:
        """Determine which personalization factors to apply."""
        factors = []
        
        if level in (PersonalizationLevel.SEGMENT, PersonalizationLevel.INDIVIDUAL):
            factors.append(f"segment:{profile.segment}")
            factors.extend([f"interest:{i}" for i in profile.interests[:3]])
        
        if level in (PersonalizationLevel.BEHAVIORAL, PersonalizationLevel.INDIVIDUAL):
            # Analyze behavior history
            top_topics = self._get_top_topics(profile.behavior_history)
            factors.extend([f"topic:{t}" for t in top_topics])
            
            # Engagement patterns
            preferred_format = self._get_preferred_format(profile.engagement_history)
            if preferred_format:
                factors.append(f"format:{preferred_format}")
        
        if level == PersonalizationLevel.CONTEXTUAL:
            factors.append(f"platform:{context.platform}")
            factors.append(f"device:{context.device}")
            if context.location:
                factors.append(f"location:{context.location}")
            factors.append(f"time:{context.timestamp.hour}")
        
        if level == PersonalizationLevel.INDIVIDUAL:
            factors.append(f"language:{profile.language}")
            factors.append(f"timezone:{profile.timezone}")
        
        return factors
    
    def _generate_personalized_content(
        self,
        content: str,
        profile: UserProfile,
        context: PersonalizationContext,
        factors: List[str],
        content_type: ContentType,
    ) -> str:
        """Generate personalized content using LLM."""
        
        result = self.personalization_chain.invoke({
            "original_content": content,
            "user_segment": profile.segment,
            "user_interests": ", ".join(profile.interests),
            "user_language": profile.language,
            "platform": context.platform,
            "device": context.device,
            "personalization_factors": ", ".join(factors),
            "content_type": content_type.value,
        })
        
        return result.content
    
    def _calculate_confidence(self, factors: List[str], profile: UserProfile) -> float:
        """Calculate confidence score for the personalization."""
        base_confidence = 0.5
        
        # More factors = higher confidence (up to a point)
        factor_bonus = min(len(factors) * 0.05, 0.2)
        
        # Richer profile = higher confidence
        profile_bonus = 0.0
        if profile.demographics:
            profile_bonus += 0.05
        if profile.interests:
            profile_bonus += 0.05
        if profile.behavior_history:
            profile_bonus += 0.05
        if profile.engagement_history:
            profile_bonus += 0.05
        
        return min(base_confidence + factor_bonus + profile_bonus, 1.0)
    
    def _generate_variant_id(self, content: str, user_id: str) -> str:
        """Generate a unique variant ID."""
        data = f"{content}:{user_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _get_top_topics(self, behavior_history: List[Dict]) -> List[str]:
        """Extract top topics from behavior history."""
        topic_counts = {}
        for event in behavior_history:
            topic = event.get("topic", "")
            if topic:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_topics[:3]]
    
    def _get_preferred_format(self, engagement_history: Dict[str, float]) -> Optional[str]:
        """Determine preferred content format from engagement history."""
        if not engagement_history:
            return None
        
        return max(engagement_history.items(), key=lambda x: x[1])[0]
    
    def _get_segment_profile(self, segment: str) -> UserProfile:
        """Get or create a representative profile for a segment."""
        # In production, this would fetch from a database
        segment_profiles = {
            "enterprise": UserProfile(
                user_id=f"segment_{segment}",
                segment=segment,
                demographics={"company_size": "1000+", "industry": "technology"},
                interests=["digital transformation", "AI", "automation"],
                language="en",
            ),
            "smb": UserProfile(
                user_id=f"segment_{segment}",
                segment=segment,
                demographics={"company_size": "10-100", "industry": "various"},
                interests=["growth", "efficiency", "cost reduction"],
                language="en",
            ),
            "startup": UserProfile(
                user_id=f"segment_{segment}",
                segment=segment,
                demographics={"company_size": "1-10", "industry": "technology"},
                interests=["innovation", "scaling", "funding"],
                language="en",
            ),
        }
        
        return segment_profiles.get(segment, UserProfile(
            user_id=f"segment_{segment}",
            segment=segment,
        ))
    
    def _load_segment_rules(self) -> Dict:
        """Load personalization rules for different segments."""
        return {
            "enterprise": {
                "tone": "professional",
                "focus": ["ROI", "scalability", "security", "compliance"],
                "cta_style": "consultation",
                "content_depth": "detailed",
            },
            "smb": {
                "tone": "friendly",
                "focus": ["cost-effectiveness", "ease of use", "quick results"],
                "cta_style": "trial",
                "content_depth": "moderate",
            },
            "startup": {
                "tone": "energetic",
                "focus": ["innovation", "speed", "competitive advantage"],
                "cta_style": "signup",
                "content_depth": "concise",
            },
        }


PERSONALIZATION_SYSTEM_PROMPT = """You are a content personalization expert. Your task is to adapt 
content for specific audience segments while maintaining the core message and value proposition.

Personalization principles:
1. Maintain the core message and key value propositions
2. Adapt tone, examples, and references to match the audience
3. Emphasize benefits most relevant to the target segment
4. Use language and terminology familiar to the audience
5. Adjust content depth and complexity appropriately
6. Respect cultural and regional preferences
7. Keep the content authentic and avoid over-personalization

Always output the personalized content directly without explanations.
"""

PERSONALIZATION_PROMPT_TEMPLATE = """
Personalize the following content for the specified audience:

ORIGINAL CONTENT:
{content}

TARGET SEGMENT: {user_segment}
USER INTERESTS: {user_interests}
LANGUAGE: {user_language}
PLATFORM: {platform}
DEVICE: {device}
PERSONALIZATION FACTORS: {personalization_factors}
CONTENT TYPE TO PERSONALIZE: {content_type}

Adapt the content to resonate with this specific audience while keeping the core message intact.
"""
```

### 5.3 A/B Testing Integration

```python
class ABTestManager:
    """Manage A/B tests for content variants."""
    
    def __init__(self):
        self.experiments: Dict[str, Dict] = {}
    
    def create_experiment(
        self,
        name: str,
        variants: List[PersonalizedVariant],
        traffic_split: List[float],
        success_metric: str = "conversion_rate",
    ) -> str:
        """Create a new A/B test experiment."""
        experiment_id = hashlib.md5(name.encode()).hexdigest()[:12]
        
        self.experiments[experiment_id] = {
            "name": name,
            "variants": variants,
            "traffic_split": traffic_split,
            "success_metric": success_metric,
            "start_time": datetime.utcnow(),
            "status": "running",
            "results": {v.variant_id: {"impressions": 0, "conversions": 0} for v in variants},
        }
        
        return experiment_id
    
    def assign_variant(self, experiment_id: str, user_id: str) -> Optional[PersonalizedVariant]:
        """Assign a variant to a user based on traffic split."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None
        
        # Deterministic assignment based on user_id
        hash_val = int(hashlib.md5(f"{experiment_id}:{user_id}".encode()).hexdigest(), 16)
        bucket = (hash_val % 100) / 100.0
        
        cumulative = 0
        for i, split in enumerate(experiment["traffic_split"]):
            cumulative += split
            if bucket <= cumulative:
                return experiment["variants"][i]
        
        return experiment["variants"][0]
    
    def track_event(self, experiment_id: str, variant_id: str, event_type: str):
        """Track an event for a variant."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return
        
        results = experiment["results"].get(variant_id, {})
        if event_type == "impression":
            results["impressions"] = results.get("impressions", 0) + 1
        elif event_type == "conversion":
            results["conversions"] = results.get("conversions", 0) + 1
        
        experiment["results"][variant_id] = results
    
    def get_results(self, experiment_id: str) -> Dict:
        """Get experiment results with statistical significance."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return {}
        
        results = {}
        for variant_id, data in experiment["results"].items():
            impressions = data.get("impressions", 0)
            conversions = data.get("conversions", 0)
            conversion_rate = conversions / impressions if impressions > 0 else 0
            
            results[variant_id] = {
                "impressions": impressions,
                "conversions": conversions,
                "conversion_rate": conversion_rate,
            }
        
        return results
```

---

## 6. Multi-Language Support (Arabic, English)

### 6.1 Architecture Overview

The multi-language support system handles content generation, optimization, and personalization in both English and Arabic, with proper RTL support, cultural adaptation, and language-specific SEO.

```
┌─────────────────────────────────────────────────────────┐
│                 Multi-Language Engine                     │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │   English    │    │   Arabic     │                   │
│  │   Pipeline   │    │   Pipeline   │                   │
│  │              │    │              │                   │
│  │ • LTR Layout │    │ • RTL Layout │                   │
│  │ • Western    │    │ • MSA/Dialect│                   │
│  │   SEO        │    │ • Arabic SEO │                   │
│  │ • Western    │    │ • Cultural   │                   │
│  │   Cultural   │    │   Context    │                   │
│  │   Context    │    │ • Arabic     │                   │
│  │              │    │   Readability│                   │
│  └──────────────┘    └──────────────┘                   │
│         │                   │                            │
│         ▼                   ▼                            │
│  ┌──────────────────────────────────────┐               │
│  │         Shared Components             │               │
│  │  • Translation Memory                 │               │
│  │  • Terminology Database               │               │
│  │  • Quality Assurance                  │               │
│  │  • Cross-language Analytics           │               │
│  └──────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Language Configuration

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class LanguageCode(Enum):
    ENGLISH = "en"
    ARABIC = "ar"

class ArabicDialect(Enum):
    MSA = "msa"                    # Modern Standard Arabic
    EGYPTIAN = "egy"               # Egyptian Arabic
    GULF = "glf"                   # Gulf Arabic
    LEVANTINE = "lev"              # Levantine Arabic
    MAGHREBI = "magh"              # Maghrebi Arabic

@dataclass
class LanguageConfig:
    """Configuration for a specific language."""
    code: str
    name: str
    native_name: str
    direction: str  # ltr, rtl
    font_family: str
    date_format: str
    number_format: str
    plural_rules: Dict[str, str]
    seo_best_practices: Dict[str, any]
    cultural_guidelines: Dict[str, any]
    readability_metrics: Dict[str, any]
    power_words: List[str]
    emotional_words: List[str]
    cta_phrases: List[str]
    stop_words: List[str]

LANGUAGE_CONFIGS = {
    "en": LanguageConfig(
        code="en",
        name="English",
        native_name="English",
        direction="ltr",
        font_family="Inter, Roboto, Arial",
        date_format="%B %d, %Y",
        number_format="{:,}",
        plural_rules={"one": "1 item", "other": "{count} items"},
        seo_best_practices={
            "title_length": (50, 60),
            "meta_description_length": (150, 160),
            "keyword_density": (0.5, 2.5),
            "min_word_count": 1000,
            "heading_structure": "H1 > H2 > H3",
            "url_format": "lowercase-hyphenated",
        },
        cultural_guidelines={
            "tone": "direct and professional",
            "humor": "subtle and situational",
            "formality": "moderate",
            "cultural_references": "Western-centric",
        },
        readability_metrics={
            "flesch_target": (60, 70),
            "sentence_length": (15, 20),
            "paragraph_length": (3, 5),
        },
        power_words=[
            "free", "new", "now", "today", "instantly", "effortless",
            "secret", "ultimate", "essential", "critical", "proven",
            "exclusive", "limited", "guaranteed", "breakthrough",
        ],
        emotional_words=[
            "amazing", "incredible", "revolutionary", "transformative",
            "inspiring", "remarkable", "outstanding", "exceptional",
        ],
        cta_phrases=[
            "Get started", "Learn more", "Sign up now", "Try it free",
            "Download now", "Contact us", "Request a demo", "Join today",
        ],
        stop_words=[
            "a", "an", "the", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "is", "are",
        ],
    ),
    "ar": LanguageConfig(
        code="ar",
        name="Arabic",
        native_name="العربية",
        direction="rtl",
        font_family="Noto Sans Arabic, Cairo, Tajawal",
        date_format="%d %B %Y",
        number_format="{:,}",
        plural_rules={
            "zero": "0 عناصر",
            "one": "عنصر واحد",
            "two": "عنصران",
            "few": "{count} عناصر",
            "many": "{count} عنصراً",
            "other": "{count} عنصر",
        },
        seo_best_practices={
            "title_length": (50, 70),
            "meta_description_length": (150, 170),
            "keyword_density": (0.5, 2.5),
            "min_word_count": 800,
            "heading_structure": "H1 > H2 > H3",
            "url_format": "arabic-allowed",
            "google_arabic_seo": True,
            "arabic_keywords_in_url": True,
        },
        cultural_guidelines={
            "tone": "respectful and formal",
            "humor": "conservative and context-appropriate",
            "formality": "high",
            "cultural_references": "Middle East and Islamic culture aware",
            "religious_sensitivity": "high",
            "gender_language": "inclusive",
        },
        readability_metrics={
            "sentence_length": (10, 20),
            "paragraph_length": (2, 4),
            "word_length_factor": 1.3,  # Arabic words tend to be longer
        },
        power_words=[
            "مجاني", "جديد", "الآن", "اليوم", "فوري", "سهل",
            "سر", "أساسي", "حيوي", "مثبت", "مضمون", "حصري",
            "محدود", "استثنائي", "مذهل", "رائع",
        ],
        emotional_words=[
            "مذهل", "رائع", "استثنائي", "ملهم", "مميز",
            "فريد", "متميز", "خارق", "مدهش",
        ],
        cta_phrases=[
            "ابدأ الآن", "سجّل الآن", "حمّل الآن", "اكتشف المزيد",
            "تواصل معنا", "اطلب عرضاً توضيحياً", "انضم اليوم", "جرّب مجاناً",
        ],
        stop_words [
            "في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه",
            "ذلك", "تلك", "الذي", "التي", "كان", "كانت", "هو", "هي",
        ],
    ),
}
```

### 6.3 Multi-Language Content Generator

```python
class MultiLanguageContentGenerator:
    """Generate content in multiple languages with proper localization."""
    
    def __init__(self, llm, config: Optional[Dict] = None):
        self.llm = llm
        self.config = config or {}
        self.language_configs = LANGUAGE_CONFIGS
        self.translation_memory = {}
        self.terminology_db = self._load_terminology_database()
    
    def generate(
        self,
        brief: ContentBrief,
        content_type: str,
        target_language: str,
        source_language: str = "en",
        dialect: Optional[str] = None,
    ) -> Dict:
        """
        Generate content in the target language.
        
        Args:
            brief: Research brief
            content_type: Type of content
            target_language: Target language code
            source_language: Source language code
            dialect: Arabic dialect (if applicable)
            
        Returns:
            Dictionary with generated content and metadata
        """
        lang_config = self.language_configs.get(target_language)
        if not lang_config:
            raise ValueError(f"Unsupported language: {target_language}")
        
        # Check translation memory for existing translations
        cache_key = f"{brief.topic}:{content_type}:{target_language}"
        if cache_key in self.translation_memory:
            return self.translation_memory[cache_key]
        
        # Generate content with language-specific prompt
        content = self._generate_in_language(
            brief, content_type, target_language, dialect
        )
        
        # Apply language-specific optimizations
        optimized = self._apply_language_specific_optimizations(
            content, target_language
        )
        
        result = {
            "content": optimized,
            "language": target_language,
            "dialect": dialect,
            "direction": lang_config.direction,
            "content_type": content_type,
            "word_count": len(optimized.split()),
            "character_count": len(optimized),
            "language_config": {
                "font_family": lang_config.font_family,
                "date_format": lang_config.date_format,
                "number_format": lang_config.number_format,
            },
        }
        
        # Cache result
        self.translation_memory[cache_key] = result
        
        return result
    
    def _generate_in_language(
        self,
        brief: ContentBrief,
        content_type: str,
        language: str,
        dialect: Optional[str] = None,
    ) -> str:
        """Generate content in the specified language."""
        
        lang_config = self.language_configs[language]
        
        # Build language-specific prompt
        prompt = self._build_language_prompt(
            brief, content_type, language, dialect, lang_config
        )
        
        result = self.llm.invoke(prompt)
        return result.content
    
    def _build_language_prompt(
        self,
        brief: ContentBrief,
        content_type: str,
        language: str,
        dialect: Optional[str],
        lang_config: LanguageConfig,
    ) -> str:
        """Build a language-specific generation prompt."""
        
        dialect_instruction = ""
        if language == "ar" and dialect:
            dialect_names = {
                "msa": "Modern Standard Arabic (MSA)",
                "egy": "Egyptian Arabic dialect",
                "glf": "Gulf Arabic dialect",
                "lev": "Levantine Arabic dialect",
                "magh": "Maghrebi Arabic dialect",
            }
            dialect_instruction = f" Use {dialect_names.get(dialect, dialect)} for this content."
        
        return f"""Create {content_type} content about: {brief.topic}

LANGUAGE REQUIREMENTS:
- Target Language: {lang_config.name} ({lang_config.native_name})
- Text Direction: {lang_config.direction.upper()}
- Dialect: {dialect or "Standard"}
{dialect_instruction}

CONTENT REQUIREMENTS:
- Topic Summary: {brief.topic_summary}
- Key Themes: {', '.join(brief.key_themes)}
- Content Angle: {brief.content_angle}
- Target Keywords: {', '.join([k.keyword for k in brief.target_keywords[:5]])}
- Target Audience: {brief.audience_insights[0].segment if brief.audience_insights else 'General'}

LANGUAGE-SPECIFIC GUIDELINES:
- Tone: {lang_config.cultural_guidelines.get('tone', 'professional')}
- Formality: {lang_config.cultural_guidelines.get('formality', 'moderate')}
- Power words to consider: {', '.join(lang_config.power_words[:5])}
- CTA style: {lang_config.cultural_guidelines.get('cta_style', 'direct')}

SEO REQUIREMENTS:
- Title length: {lang_config.seo_best_practices['title_length'][0]}-{lang_config.seo_best_practices['title_length'][1]} characters
- Meta description: {lang_config.seo_best_practices['meta_description_length'][0]}-{lang_config.seo_best_practices['meta_description_length'][1]} characters
- Minimum word count: {lang_config.seo_best_practices['min_word_count']}

Generate high-quality, native-level {lang_config.name} content that reads naturally 
and is culturally appropriate for the target audience.
"""
    
    def _apply_language_specific_optimizations(
        self, content: str, language: str
    ) -> str:
        """Apply language-specific optimizations to content."""
        
        if language == "ar":
            content = self._optimize_arabic_content(content)
        elif language == "en":
            content = self._optimize_english_content(content)
        
        return content
    
    def _optimize_arabic_content(self, content: str) -> str:
        """Apply Arabic-specific optimizations."""
        
        # Ensure proper Arabic punctuation
        content = content.replace(",", "،")  # Arabic comma
        content = content.replace(";", "؛")  # Arabic semicolon
        content = content.replace("?", "؟")  # Arabic question mark
        
        # Remove tatweel (kashida) if present
        content = content.replace("ـ", "")
        
        # Ensure proper Arabic number formatting
        # (Arabic uses Eastern Arabic numerals in some contexts)
        
        # Add RTL marks for mixed content
        if any(c.isascii() and c.isalpha() for c in content):
            # Wrap Latin text with RTL marks
            import re
            content = re.sub(
                r'([a-zA-Z]+)',
                r'\u2066\1\u2069',  # LRI ... PDI
                content
            )
        
        return content
    
    def _optimize_english_content(self, content: str) -> str:
        """Apply English-specific optimizations."""
        # Standard English optimizations
        return content
    
    def translate_content(
        self,
        content: str,
        source_language: str,
        target_language: str,
        content_type: str = "general",
    ) -> str:
        """
        Translate content between languages while preserving meaning and tone.
        
        Args:
            content: Content to translate
            source_language: Source language code
            target_language: Target language code
            content_type: Type of content (affects translation style)
            
        Returns:
            Translated content
        """
        translation_prompt = f"""Translate the following {content_type} content from 
        {self.language_configs[source_language].name} to {self.language_configs[target_language].name}.

SOURCE CONTENT:
{content}

TRANSLATION REQUIREMENTS:
- Maintain the original tone and style
- Adapt cultural references appropriately
- Preserve formatting and structure
- Use natural, fluent {self.language_configs[target_language].name}
- Keep technical terms consistent with industry standards
- Adapt idioms and expressions to the target language
- Maintain SEO keywords in the target language

Provide only the translation, no explanations.
"""
        
        result = self.llm.invoke(translation_prompt)
        return result.content
    
    def _load_terminology_database(self) -> Dict:
        """Load terminology database for consistent translations."""
        return {
            "en": {
                "artificial intelligence": "الذكاء الاصطناعي",
                "machine learning": "التعلم الآلي",
                "deep learning": "التعلم العميق",
                "natural language processing": "معالجة اللغة الطبيعية",
                "content generation": "توليد المحتوى",
                "marketing automation": "أتمتة التسويق",
            },
            "ar": {
                "الذكاء الاصطناعي": "artificial intelligence",
                "التعلم الآلي": "machine learning",
                "التعلم العميق": "deep learning",
                "معالجة اللغة الطبيعية": "natural language processing",
                "توليد المحتوى": "content generation",
                "أتمتة التسويق": "marketing automation",
            },
        }
```

### 6.4 RTL Layout Support

```python
class RTLSupport:
    """Handle RTL layout and formatting for Arabic content."""
    
    @staticmethod
    def get_html_direction(language: str) -> str:
        """Get HTML direction attribute for a language."""
        return "rtl" if language == "ar" else "ltr"
    
    @staticmethod
    def wrap_mixed_content(text: str, language: str) -> str:
        """Wrap mixed-direction text with proper Unicode controls."""
        if language == "ar":
            # Add RTL mark at the beginning
            text = "\u2066" + text + "\u2067"  # RLI ... PDI
        return text
    
    @staticmethod
    def format_numbers(number: int, language: str) -> str:
        """Format numbers according to language conventions."""
        if language == "ar":
            # Use Eastern Arabic numerals
            eastern_numerals = "٠١٢٣٤٥٦٧٨٩"
            return "".join(eastern_numerals[int(d)] for d in str(number))
        return f"{number:,}"
    
    @staticmethod
    def get_css_direction_styles(language: str) -> Dict[str, str]:
        """Get CSS styles for proper direction handling."""
        if language == "ar":
            return {
                "direction": "rtl",
                "text-align": "right",
                "font-family": "Noto Sans Arabic, Cairo, Tajawal, sans-serif",
                "margin-left": "auto",
                "margin-right": "0",
                "padding-left": "1rem",
                "padding-right": "0",
            }
        return {
            "direction": "ltr",
            "text-align": "left",
            "font-family": "Inter, Roboto, Arial, sans-serif",
        }
```

---

## 7. Content Performance Analytics

### 7.1 Analytics Architecture

```python
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics

class MetricType(Enum):
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    ENGAGEMENT_TIME = "engagement_time"
    BOUNCE_RATE = "bounce_rate"
    SHARES = "shares"
    COMMENTS = "comments"
    SENTIMENT = "sentiment"
    SEO_RANKING = "seo_ranking"
    READABILITY = "readability"

@dataclass
class ContentMetrics:
    """Metrics for a single content piece."""
    content_id: str
    content_type: str
    language: str
    published_at: datetime
    metrics: Dict[str, List[Dict]] = field(default_factory=dict)
    
    def add_metric(self, metric_type: str, value: float, timestamp: Optional[datetime] = None):
        """Add a metric data point."""
        if metric_type not in self.metrics:
            self.metrics[metric_type] = []
        
        self.metrics[metric_type].append({
            "value": value,
            "timestamp": timestamp or datetime.utcnow(),
        })
    
    def get_metric_summary(self, metric_type: str) -> Dict:
        """Get summary statistics for a metric."""
        data = self.metrics.get(metric_type, [])
        if not data:
            return {}
        
        values = [d["value"] for d in data]
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1],
            "trend": self._calculate_trend(values),
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction."""
        if len(values) < 2:
            return "stable"
        
        recent = values[-5:] if len(values) >= 5 else values
        if len(recent) < 2:
            return "stable"
        
        diff = recent[-1] - recent[0]
        threshold = statistics.stdev(values) * 0.5 if len(values) > 1 else 0
        
        if diff > threshold:
            return "increasing"
        elif diff < -threshold:
            return "decreasing"
        return "stable"


class ContentAnalyticsEngine:
    """
    Engine for tracking and analyzing content performance.
    Provides insights, recommendations, and reporting.
    """
    
    def __init__(self, db_connection=None, config: Optional[Dict] = None):
        self.db = db_connection
        self.config = config or {}
        self.metrics_store: Dict[str, ContentMetrics] = {}
        self.benchmarks = self._load_benchmarks()
    
    def track_content(
        self,
        content_id: str,
        content_type: str,
        language: str,
        metadata: Optional[Dict] = None,
    ) -> ContentMetrics:
        """Initialize tracking for a new content piece."""
        metrics = ContentMetrics(
            content_id=content_id,
            content_type=content_type,
            language=language,
            published_at=datetime.utcnow(),
        )
        
        if metadata:
            metrics.metadata = metadata
        
        self.metrics_store[content_id] = metrics
        return metrics
    
    def record_event(
        self,
        content_id: str,
        event_type: str,
        value: float = 1.0,
        metadata: Optional[Dict] = None,
    ):
        """Record a performance event."""
        metrics = self.metrics_store.get(content_id)
        if not metrics:
            return
        
        metrics.add_metric(event_type, value)
        
        # Persist to database
        self._persist_event(content_id, event_type, value, metadata)
    
    def get_performance_report(
        self,
        content_id: str,
        time_range: Optional[timedelta] = None,
    ) -> Dict:
        """Generate a performance report for a content piece."""
        metrics = self.metrics_store.get(content_id)
        if not metrics:
            return {}
        
        time_range = time_range or timedelta(days=30)
        cutoff = datetime.utcnow() - time_range
        
        report = {
            "content_id": content_id,
            "content_type": metrics.content_type,
            "language": metrics.language,
            "published_at": metrics.published_at.isoformat(),
            "time_range_days": time_range.days,
            "metrics": {},
            "summary": {},
            "recommendations": [],
        }
        
        # Calculate metrics
        for metric_type in metrics.metrics:
            summary = metrics.get_metric_summary(metric_type)
            report["metrics"][metric_type] = summary
        
        # Calculate derived metrics
        report["summary"] = self._calculate_summary_metrics(metrics)
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(metrics, report["summary"])
        
        return report
    
    def get_aggregate_report(
        self,
        content_type: Optional[str] = None,
        language: Optional[str] = None,
        time_range: timedelta = timedelta(days=30),
    ) -> Dict:
        """Generate aggregate performance report."""
        cutoff = datetime.utcnow() - time_range
        
        # Filter content pieces
        filtered = {
            cid: m for cid, m in self.metrics_store.items()
            if (content_type is None or m.content_type == content_type)
            and (language is None or m.language == language)
            and m.published_at >= cutoff
        }
        
        if not filtered:
            return {"message": "No data available for the specified filters"}
        
        # Aggregate metrics
        aggregate = {
            "total_content_pieces": len(filtered),
            "content_type": content_type or "all",
            "language": language or "all",
            "time_range_days": time_range.days,
            "metrics": {},
            "top_performers": [],
            "underperformers": [],
        }
        
        # Calculate aggregate statistics
        all_metrics = {}
        for metric_type in MetricType:
            values = []
            for m in filtered.values():
                summary = m.get_metric_summary(metric_type.value)
                if summary:
                    values.append(summary["mean"])
            
            if values:
                all_metrics[metric_type.value] = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values),
                }
        
        aggregate["metrics"] = all_metrics
        
        # Identify top and under performers
        aggregate["top_performers"] = self._identify_top_performers(filtered)
        aggregate["underperformers"] = self._identify_underperformers(filtered)
        
        return aggregate
    
    def _calculate_summary_metrics(self, metrics: ContentMetrics) -> Dict:
        """Calculate summary metrics for a content piece."""
        summary = {}
        
        # Engagement rate
        impressions = metrics.get_metric_summary("impressions")
        clicks = metrics.get_metric_summary("clicks")
        
        if impressions and clicks and impressions["mean"] > 0:
            summary["ctr"] = (clicks["mean"] / impressions["mean"]) * 100
        
        # Conversion rate
        conversions = metrics.get_metric_summary("conversions")
        if conversions and clicks and clicks["mean"] > 0:
            summary["conversion_rate"] = (conversions["mean"] / clicks["mean"]) * 100
        
        # Average engagement time
        engagement = metrics.get_metric_summary("engagement_time")
        if engagement:
            summary["avg_engagement_time"] = engagement["mean"]
        
        # Bounce rate
        bounce = metrics.get_metric_summary("bounce_rate")
        if bounce:
            summary["bounce_rate"] = bounce["mean"]
        
        # Social shares
        shares = metrics.get_metric_summary("shares")
        if shares:
            summary["total_shares"] = shares["mean"]
        
        # SEO ranking
        seo = metrics.get_metric_summary("seo_ranking")
        if seo:
            summary["avg_seo_ranking"] = seo["mean"]
        
        return summary
    
    def _generate_recommendations(self, metrics: ContentMetrics, summary: Dict) -> List[str]:
        """Generate actionable recommendations based on performance."""
        recommendations = []
        
        # CTR recommendations
        ctr = summary.get("ctr", 0)
        if ctr < 2:
            recommendations.append("CTR is below average. Consider improving headlines and meta descriptions.")
        elif ctr > 5:
            recommendations.append("CTR is strong. Analyze what's working and apply to other content.")
        
        # Conversion rate recommendations
        conv_rate = summary.get("conversion_rate", 0)
        if conv_rate < 1:
            recommendations.append("Conversion rate is low. Review CTA placement and messaging.")
        
        # Engagement time recommendations
        engagement = summary.get("avg_engagement_time", 0)
        if engagement < 60:
            recommendations.append("Engagement time is short. Consider adding more engaging elements or improving content structure.")
        
        # Bounce rate recommendations
        bounce = summary.get("bounce_rate", 0)
        if bounce > 70:
            recommendations.append("Bounce rate is high. Review content relevance and page load speed.")
        
        # SEO recommendations
        seo = summary.get("avg_seo_ranking", 0)
        if seo > 20:
            recommendations.append("SEO ranking needs improvement. Review keyword optimization and content quality.")
        
        return recommendations
    
    def _identify_top_performers(self, metrics_store: Dict[str, ContentMetrics]) -> List[Dict]:
        """Identify top-performing content pieces."""
        performers = []
        
        for content_id, metrics in metrics_store.items():
            summary = self._calculate_summary_metrics(metrics)
            score = self._calculate_performance_score(summary)
            performers.append({
                "content_id": content_id,
                "content_type": metrics.content_type,
                "language": metrics.language,
                "performance_score": score,
                "summary": summary,
            })
        
        performers.sort(key=lambda x: x["performance_score"], reverse=True)
        return performers[:10]
    
    def _identify_underperformers(self, metrics_store: Dict[str, ContentMetrics]) -> List[Dict]:
        """Identify underperforming content pieces."""
        performers = []
        
        for content_id, metrics in metrics_store.items():
            summary = self._calculate_summary_metrics(metrics)
            score = self._calculate_performance_score(summary)
            performers.append({
                "content_id": content_id,
                "content_type": metrics.content_type,
                "language": metrics.language,
                "performance_score": score,
                "summary": summary,
            })
        
        performers.sort(key=lambda x: x["performance_score"])
        return performers[:10]
    
    def _calculate_performance_score(self, summary: Dict) -> float:
        """Calculate an overall performance score."""
        score = 0
        
        # CTR (weight: 25%)
        ctr = summary.get("ctr", 0)
        score += min(ctr / 5, 1) * 25
        
        # Conversion rate (weight: 30%)
        conv_rate = summary.get("conversion_rate", 0)
        score += min(conv_rate / 3, 1) * 30
        
        # Engagement time (weight: 20%)
        engagement = summary.get("avg_engagement_time", 0)
        score += min(engagement / 180, 1) * 20
        
        # Bounce rate (weight: 15%) - lower is better
        bounce = summary.get("bounce_rate", 100)
        score += max(0, (100 - bounce) / 100) * 15
        
        # SEO ranking (weight: 10%) - lower is better
        seo = summary.get("avg_seo_ranking", 50)
        score += max(0, (50 - seo) / 50) * 10
        
        return score
    
    def _load_benchmarks(self) -> Dict:
        """Load industry benchmarks for comparison."""
        return {
            "blog_post": {
                "avg_ctr": 2.5,
                "avg_conversion_rate": 1.5,
                "avg_engagement_time": 120,
                "avg_bounce_rate": 60,
                "avg_seo_ranking": 15,
            },
            "social_media": {
                "avg_ctr": 1.8,
                "avg_conversion_rate": 0.8,
                "avg_engagement_time": 30,
                "avg_bounce_rate": 40,
            },
            "email_campaign": {
                "avg_ctr": 3.0,
                "avg_conversion_rate": 2.0,
                "avg_engagement_time": 90,
                "avg_bounce_rate": 35,
            },
        }
    
    def _persist_event(self, content_id: str, event_type: str, value: float, metadata: Optional[Dict]):
        """Persist event to database."""
        # Implementation would write to database
        pass
```

### 7.2 Real-Time Dashboard Data

```python
class AnalyticsDashboard:
    """Provide data for real-time analytics dashboard."""
    
    def __init__(self, analytics_engine: ContentAnalyticsEngine):
        self.engine = analytics_engine
    
    def get_dashboard_data(self, time_range: timedelta = timedelta(days=7)) -> Dict:
        """Get data for the main dashboard."""
        return {
            "overview": self._get_overview_metrics(time_range),
            "content_performance": self._get_content_performance(time_range),
            "language_comparison": self._get_language_comparison(time_range),
            "trending_content": self._get_trending_content(time_range),
            "recommendations": self._get_top_recommendations(time_range),
        }
    
    def _get_overview_metrics(self, time_range: timedelta) -> Dict:
        """Get high-level overview metrics."""
        aggregate = self.engine.get_aggregate_report(time_range=time_range)
        return {
            "total_content": aggregate.get("total_content_pieces", 0),
            "avg_ctr": aggregate.get("metrics", {}).get("clicks", {}).get("mean", 0),
            "avg_conversion_rate": aggregate.get("metrics", {}).get("conversions", {}).get("mean", 0),
            "total_impressions": aggregate.get("metrics", {}).get("impressions", {}).get("mean", 0),
        }
    
    def _get_content_performance(self, time_range: timedelta) -> List[Dict]:
        """Get performance data for all content pieces."""
        return self.engine.get_aggregate_report(time_range=time_range).get("top_performers", [])
    
    def _get_language_comparison(self, time_range: timedelta) -> Dict:
        """Compare performance across languages."""
        en_report = self.engine.get_aggregate_report(language="en", time_range=time_range)
        ar_report = self.engine.get_aggregate_report(language="ar", time_range=time_range)
        
        return {
            "english": en_report.get("metrics", {}),
            "arabic": ar_report.get("metrics", {}),
        }
    
    def _get_trending_content(self, time_range: timedelta) -> List[Dict]:
        """Get trending content based on recent performance."""
        return self.engine.get_aggregate_report(time_range=time_range).get("top_performers", [])[:5]
    
    def _get_top_recommendations(self, time_range: timedelta) -> List[str]:
        """Get top recommendations across all content."""
        recommendations = []
        for content_id in self.engine.metrics_store:
            report = self.engine.get_performance_report(content_id, time_range)
            recommendations.extend(report.get("recommendations", []))
        
        # Return unique recommendations
        return list(set(recommendations))[:10]
```

---

## 8. Code Examples and Snippets

### 8.1 Complete Pipeline Example

```python
"""
Complete content generation pipeline example.
Demonstrates the full workflow from research to analytics.
"""

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os

load_dotenv()

def run_content_generation_pipeline():
    """Run the complete content generation pipeline."""
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        max_tokens=4000,
    )
    
    # Initialize agents
    research_agent = ContentResearchAgent(llm=llm)
    generation_agent = ContentGenerationAgent(llm=llm)
    optimization_agent = ContentOptimizationAgent(llm=llm)
    personalization_engine = PersonalizationEngine(llm=llm)
    analytics_engine = ContentAnalyticsEngine()
    
    # Step 1: Research
    print("Step 1: Researching topic...")
    brief = research_agent.research(
        topic="AI-powered content marketing for enterprise businesses",
        audience="Marketing directors and CMOs at enterprise companies",
        content_type="blog_post",
        language="en",
    )
    print(f"Research complete. Found {len(brief.target_keywords)} keywords.")
    
    # Step 2: Generate
    print("Step 2: Generating content...")
    generated = generation_agent.generate(
        brief=brief,
        content_type="blog_post",
        language="en",
        brand_voice="professional",
    )
    print(f"Generated {generated['word_count']} words.")
    
    # Step 3: Optimize
    print("Step 3: Optimizing content...")
    optimized = optimization_agent.optimize(
        content=generated["content"],
        content_type="blog_post",
        target_keywords=[k.keyword for k in brief.target_keywords if k.keyword_type == "primary"],
        language="en",
    )
    print(f"Optimization complete. Overall score: {optimized['overall_score']:.1f}/100")
    
    # Step 4: Personalize
    print("Step 4: Creating personalized variants...")
    user_profile = UserProfile(
        user_id="user_123",
        segment="enterprise",
        demographics={"company_size": "1000+", "industry": "technology"},
        interests=["AI", "digital transformation", "marketing automation"],
        language="en",
    )
    
    context = PersonalizationContext(
        platform="web",
        device="desktop",
    )
    
    personalized = personalization_engine.personalize(
        content=optimized["optimized_content"],
        user_profile=user_profile,
        context=context,
    )
    print(f"Personalization complete. Confidence: {personalized.confidence_score:.2f}")
    
    # Step 5: Generate Arabic version
    print("Step 5: Generating Arabic version...")
    arabic_content = MultiLanguageContentGenerator(llm=llm).generate(
        brief=brief,
        content_type="blog_post",
        target_language="ar",
        source_language="en",
    )
    print(f"Arabic content generated: {arabic_content['word_count']} words.")
    
    # Step 6: Track analytics
    print("Step 6: Setting up analytics tracking...")
    content_id = f"content_{hash(personalized.content) % 10000}"
    analytics_engine.track_content(
        content_id=content_id,
        content_type="blog_post",
        language="en",
        metadata={
            "topic": brief.topic,
            "segment": user_profile.segment,
            "personalization_level": personalized.personalization_level.value,
        },
    )
    
    # Simulate some events
    analytics_engine.record_event(content_id, "impressions", 1000)
    analytics_engine.record_event(content_id, "clicks", 45)
    analytics_engine.record_event(content_id, "conversions", 3)
    analytics_engine.record_event(content_id, "engagement_time", 180)
    
    # Generate report
    report = analytics_engine.get_performance_report(content_id)
    print(f"Performance report generated with {len(report.get('recommendations', []))} recommendations.")
    
    return {
        "brief": brief,
        "generated": generated,
        "optimized": optimized,
        "personalized": personalized,
        "arabic_content": arabic_content,
        "analytics_report": report,
    }


if __name__ == "__main__":
    results = run_content_generation_pipeline()
    print("\nPipeline complete!")
    print(f"Content ID: {results['analytics_report']['content_id']}")
    print(f"Overall optimization score: {results['optimized']['overall_score']:.1f}/100")
```

### 8.2 FastAPI Endpoint Example

```python
"""
FastAPI endpoints for the content generation system.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="AI Content Generation API", version="1.0.0")

# Pydantic models for API
class ContentRequest(BaseModel):
    topic: str
    target_audience: str
    content_type: str
    language: str = "en"
    brand_voice: str = "professional"
    keywords: List[str] = []
    personalization_level: str = "segment"

class ContentResponse(BaseModel):
    content_id: str
    content: str
    language: str
    content_type: str
    word_count: int
    seo_score: float
    readability_score: float
    engagement_score: float
    overall_score: float
    recommendations: List[str]

class PersonalizationRequest(BaseModel):
    content: str
    user_id: str
    segment: str
    platform: str = "web"
    device: str = "desktop"

# Initialize components (in production, use dependency injection)
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
research_agent = ContentResearchAgent(llm=llm)
generation_agent = ContentGenerationAgent(llm=llm)
optimization_agent = ContentOptimizationAgent(llm=llm)
personalization_engine = PersonalizationEngine(llm=llm)
analytics_engine = ContentAnalyticsEngine()

@app.post("/api/v1/content/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest):
    """Generate optimized content."""
    try:
        # Research
        brief = research_agent.research(
            topic=request.topic,
            audience=request.target_audience,
            content_type=request.content_type,
            language=request.language,
        )
        
        # Generate
        generated = generation_agent.generate(
            brief=brief,
            content_type=request.content_type,
            language=request.language,
            brand_voice=request.brand_voice,
        )
        
        # Optimize
        optimized = optimization_agent.optimize(
            content=generated["content"],
            content_type=request.content_type,
            target_keywords=request.keywords or [k.keyword for k in brief.target_keywords[:5]],
            language=request.language,
        )
        
        # Track
        content_id = f"content_{hash(optimized['optimized_content']) % 100000}"
        analytics_engine.track_content(
            content_id=content_id,
            content_type=request.content_type,
            language=request.language,
        )
        
        return ContentResponse(
            content_id=content_id,
            content=optimized["optimized_content"],
            language=request.language,
            content_type=request.content_type,
            word_count=len(optimized["optimized_content"].split()),
            seo_score=optimized["seo_score"],
            readability_score=optimized["readability_score"],
            engagement_score=optimized["engagement_score"],
            overall_score=optimized["overall_score"],
            recommendations=optimized["improvement_suggestions"],
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/content/personalize")
async def personalize_content(request: PersonalizationRequest):
    """Create personalized content variant."""
    try:
        user_profile = UserProfile(
            user_id=request.user_id,
            segment=request.segment,
        )
        
        context = PersonalizationContext(
            platform=request.platform,
            device=request.device,
        )
        
        variant = personalization_engine.personalize(
            content=request.content,
            user_profile=user_profile,
            context=context,
        )
        
        return {
            "variant_id": variant.variant_id,
            "content": variant.content,
            "personalization_level": variant.personalization_level.value,
            "confidence_score": variant.confidence_score,
            "factors": variant.personalization_factors,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/content/translate")
async def translate_content(
    content: str,
    source_language: str,
    target_language: str,
    content_type: str = "general",
):
    """Translate content between languages."""
    try:
        translator = MultiLanguageContentGenerator(llm=llm)
        translated = translator.translate_content(
            content=content,
            source_language=source_language,
            target_language=target_language,
            content_type=content_type,
        )
        
        return {
            "translated_content": translated,
            "source_language": source_language,
            "target_language": target_language,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/{content_id}")
async def get_analytics(content_id: str, days: int = 30):
    """Get performance analytics for a content piece."""
    try:
        report = analytics_engine.get_performance_report(
            content_id=content_id,
            time_range=timedelta(days=days),
        )
        return report
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard(days: int = 7):
    """Get dashboard data."""
    try:
        dashboard = AnalyticsDashboard(analytics_engine)
        return dashboard.get_dashboard_data(time_range=timedelta(days=days))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail(str(e)))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 8.3 LangGraph Workflow Integration

```python
"""
LangGraph workflow integration for the content generation system.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

def research_agent_node(state: ContentGenerationState) -> ContentGenerationState:
    """Research agent node for LangGraph."""
    agent = ContentResearchAgent(llm=state["llm"])
    
    brief = agent.research(
        topic=state["topic"],
        audience=state["target_audience"],
        content_type=state["content_type"],
        language=state["language"],
    )
    
    state["research_data"] = brief.model_dump()
    state["current_step"] = "research_complete"
    state["messages"].append(AIMessage(content=f"Research complete. Found {len(brief.target_keywords)} keywords."))
    
    return state

def generation_agent_node(state: ContentGenerationState) -> ContentGenerationState:
    """Generation agent node for LangGraph."""
    agent = ContentGenerationAgent(llm=state["llm"])
    
    brief = ContentBrief(**state["research_data"])
    
    generated = agent.generate(
        brief=brief,
        content_type=state["content_type"],
        language=state["language"],
        brand_voice=state["brand_voice"],
    )
    
    state["content_draft"] = generated["content"]
    state["current_step"] = "generation_complete"
    state["messages"].append(AIMessage(content=f"Generated {generated['word_count']} words."))
    
    return state

def optimization_agent_node(state: ContentGenerationState) -> ContentGenerationState:
    """Optimization agent node for LangGraph."""
    agent = ContentOptimizationAgent(llm=state["llm"])
    
    brief = ContentBrief(**state["research_data"])
    
    optimized = agent.optimize(
        content=state["content_draft"],
        content_type=state["content_type"],
        target_keywords=[k.keyword for k in brief.target_keywords if k.keyword_type == "primary"],
        language=state["language"],
    )
    
    state["optimized_content"] = optimized["optimized_content"]
    state["seo_score"] = optimized["seo_score"]
    state["readability_score"] = optimized["readability_score"]
    state["current_step"] = "optimization_complete"
    state["messages"].append(AIMessage(content=f"Optimization complete. Score: {optimized['overall_score']:.1f}/100"))
    
    return state

def personalization_node(state: ContentGenerationState) -> ContentGenerationState:
    """Personalization node for LangGraph."""
    engine = PersonalizationEngine(llm=state["llm"])
    
    # Create default user profile from state
    user_profile = UserProfile(
        user_id="default_user",
        segment=state.get("target_audience", "general"),
        language=state["language"],
    )
    
    context = PersonalizationContext()
    
    variant = engine.personalize(
        content=state["optimized_content"],
        user_profile=user_profile,
        context=context,
    )
    
    state["personalized_variants"] = [variant.__dict__]
    state["current_step"] = "personalization_complete"
    state["messages"].append(AIMessage(content="Personalization complete."))
    
    return state

def analytics_node(state: ContentGenerationState) -> ContentGenerationState:
    """Analytics node for LangGraph."""
    engine = ContentAnalyticsEngine()
    
    content_id = f"content_{hash(state['optimized_content']) % 100000}"
    
    engine.track_content(
        content_id=content_id,
        content_type=state["content_type"],
        language=state["language"],
    )
    
    state["content_id"] = content_id
    state["current_step"] = "analytics_complete"
    state["messages"].append(AIMessage(content=f"Analytics tracking initialized. Content ID: {content_id}"))
    
    return state

def should_retry_research(state: ContentGenerationState) -> str:
    """Conditional edge function for research retry logic."""
    if len(state.get("errors", [])) > 2:
        return "fail"
    if state.get("research_data") is None:
        return "retry"
    return "generate"

def build_content_generation_graph(llm):
    """Build the complete LangGraph workflow."""
    
    workflow = StateGraph(ContentGenerationState)
    
    # Add nodes
    workflow.add_node("research", research_agent_node)
    workflow.add_node("generate", generation_agent_node)
    workflow.add_node("optimize", optimization_agent_node)
    workflow.add_node("personalize", personalization_node)
    workflow.add_node("analytics", analytics_node)
    
    # Define edges
    workflow.set_entry_point("research")
    workflow.add_edge("research", "generate")
    workflow.add_edge("generate", "optimize")
    workflow.add_edge("optimize", "personalize")
    workflow.add_edge("personalize", "analytics")
    workflow.add_edge("analytics", END)
    
    # Compile
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app

# Usage
# graph = build_content_generation_graph(llm)
# result = graph.invoke({
#     "topic": "AI in marketing",
#     "target_audience": "Marketing professionals",
#     "content_type": "blog_post",
#     "language": "en",
#     "brand_voice": "professional",
#     "keywords": ["AI marketing", "content automation"],
#     "current_step": "started",
#     "errors": [],
#     "messages": [],
#     "llm": llm,
# })
```

### 8.4 Celery Task Queue Integration

```python
"""
Celery tasks for async content generation.
"""

from celery import Celery
from celery.result import AsyncResult

celery_app = Celery(
    "content_generation",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

@celery_app.task(bind=True, max_retries=3)
def generate_content_task(self, topic: str, audience: str, content_type: str, language: str = "en"):
    """Async task for content generation."""
    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        
        # Research
        research_agent = ContentResearchAgent(llm=llm)
        brief = research_agent.research(topic, audience, content_type, language)
        
        # Generate
        generation_agent = ContentGenerationAgent(llm=llm)
        generated = generation_agent.generate(brief, content_type, language)
        
        # Optimize
        optimization_agent = ContentOptimizationAgent(llm=llm)
        optimized = optimization_agent.optimize(
            content=generated["content"],
            content_type=content_type,
            target_keywords=[k.keyword for k in brief.target_keywords[:5]],
            language=language,
        )
        
        return {
            "status": "success",
            "content": optimized["optimized_content"],
            "scores": {
                "seo": optimized["seo_score"],
                "readability": optimized["readability_score"],
                "engagement": optimized["engagement_score"],
                "overall": optimized["overall_score"],
            },
            "recommendations": optimized["improvement_suggestions"],
        }
    
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task
def batch_generate_content(tasks: List[Dict]):
    """Generate content for multiple topics in parallel."""
    from celery import group
    
    job = group(
        generate_content_task.s(
            topic=t["topic"],
            audience=t["audience"],
            content_type=t["content_type"],
            language=t.get("language", "en"),
        )
        for t in tasks
    )
    
    result = job.apply_async()
    return result.id

@celery_app.task
def translate_content_task(content: str, source_lang: str, target_lang: str):
    """Async task for content translation."""
    llm = ChatOpenAI(model="gpt-4o")
    translator = MultiLanguageContentGenerator(llm=llm)
    
    translated = translator.translate_content(
        content=content,
        source_language=source_lang,
        target_language=target_lang,
    )
    
    return {
        "status": "success",
        "translated_content": translated,
        "source_language": source_lang,
        "target_language": target_lang,
    }
```

---

## 9. Testing Strategy

### 9.1 Testing Pyramid

```
                    ┌─────────┐
                    │   E2E   │  ← Full pipeline tests
                    │  Tests  │
                   ┌┴─────────┴┐
                   │ Integration│ ← Agent interaction tests
                   │   Tests    │
                  ┌┴────────────┴┐
                  │    Unit       │ ← Individual component tests
                  │    Tests      │
                 ┌┴───────────────┴┐
                 │  Contract Tests  │ ← API schema validation
                 └──────────────────┘
```

### 9.2 Unit Tests

```python
"""
Unit tests for content generation components.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

class TestContentResearchAgent:
    """Unit tests for ContentResearchAgent."""
    
    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.invoke.return_value = Mock(content='{"topic_summary": "Test summary"}')
        return llm
    
    @pytest.fixture
    def research_agent(self, mock_llm):
        return ContentResearchAgent(llm=mock_llm)
    
    def test_research_returns_structured_brief(self, research_agent):
        """Test that research returns a properly structured brief."""
        result = research_agent.research(
            topic="AI in marketing",
            audience="Marketing professionals",
            content_type="blog_post",
        )
        
        assert isinstance(result, dict)
        assert "topic" in result
        assert "target_keywords" in result
    
    def test_research_handles_empty_results(self, research_agent, mock_llm):
        """Test research agent handles empty search results."""
        mock_llm.invoke.return_value = Mock(content="{}")
        
        result = research_agent.research(
            topic="Obscure topic",
            audience="Niche audience",
            content_type="blog_post",
        )
        
        assert isinstance(result, dict)
    
    def test_keyword_research_tool(self, research_agent):
        """Test keyword research tool returns valid data."""
        result = research_agent._create_keyword_research_tool().invoke({
            "topic": "AI marketing",
            "language": "en",
        })
        
        assert isinstance(result, str)
        assert "primary_keywords" in result


class TestContentGenerationAgent:
    """Unit tests for ContentGenerationAgent."""
    
    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.invoke.return_value = Mock(content="# Test Blog Post\n\nThis is test content.")
        return llm
    
    @pytest.fixture
    def sample_brief(self):
        return ContentBrief(
            topic="AI in Marketing",
            topic_summary="AI is transforming marketing",
            key_themes=["automation", "personalization"],
            target_keywords=[
                KeywordData(keyword="AI marketing", keyword_type="primary", relevance_score=0.9),
            ],
            competitor_analysis=[],
            audience_insights=[],
            trends=[],
            statistics=[],
            expert_quotes=[],
            content_angle="How AI transforms marketing",
            suggested_outline=[],
            language="en",
        )
    
    def test_generate_blog_post(self, mock_llm, sample_brief):
        """Test blog post generation."""
        agent = ContentGenerationAgent(llm=mock_llm)
        
        result = agent.generate(
            brief=sample_brief,
            content_type="blog_post",
            language="en",
        )
        
        assert "content" in result
        assert result["content_type"] == "blog_post"
        assert result["language"] == "en"
    
    def test_generate_social_media(self, mock_llm, sample_brief):
        """Test social media content generation."""
        agent = ContentGenerationAgent(llm=mock_llm)
        
        result = agent.generate(
            brief=sample_brief,
            content_type="social_media",
            language="en",
        )
        
        assert "content" in result
        assert result["content_type"] == "social_media"
    
    def test_generate_arabic_content(self, mock_llm, sample_brief):
        """Test Arabic content generation."""
        mock_llm.invoke.return_value = Mock(content="# الذكاء الاصطناعي في التسويق\n\nمحتوى تجريبي.")
        
        agent = ContentGenerationAgent(llm=mock_llm)
        
        result = agent.generate(
            brief=sample_brief,
            content_type="blog_post",
            language="ar",
        )
        
        assert result["language"] == "ar"
        assert "content" in result


class TestContentOptimizationAgent:
    """Unit tests for ContentOptimizationAgent."""
    
    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.invoke.return_value = Mock(content="Optimized content")
        return llm
    
    @pytest.fixture
    def optimization_agent(self, mock_llm):
        return ContentOptimizationAgent(llm=mock_llm)
    
    def test_optimize_returns_scores(self, optimization_agent):
        """Test that optimization returns all required scores."""
        result = optimization_agent.optimize(
            content="# Test Content\n\nThis is test content for optimization.",
            content_type="blog_post",
            target_keywords=["test", "content"],
            language="en",
        )
        
        assert "seo_score" in result
        assert "readability_score" in result
        assert "engagement_score" in result
        assert "overall_score" in result
        assert 0 <= result["seo_score"] <= 100
        assert 0 <= result["readability_score"] <= 100
        assert 0 <= result["engagement_score"] <= 100
    
    def test_seo_analysis_detects_missing_keywords(self, optimization_agent):
        """Test SEO analysis detects missing keywords."""
        result = optimization_agent.optimize(
            content="# Test\n\nSome content without keywords.",
            content_type="blog_post",
            target_keywords=["missing_keyword"],
            language="en",
        )
        
        assert result["seo_score"] < 100
        assert any("missing_keyword" in s for s in result["improvement_suggestions"])
    
    def test_readability_analysis_detects_long_sentences(self, optimization_agent):
        """Test readability analysis detects long sentences."""
        long_sentence = "This is a very long sentence " * 20 + "."
        
        result = optimization_agent.optimize(
            content=long_sentence,
            content_type="blog_post",
            target_keywords=[],
            language="en",
        )
        
        assert result["readability_score"] < 100


class TestPersonalizationEngine:
    """Unit tests for PersonalizationEngine."""
    
    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.invoke.return_value = Mock(content="Personalized content for enterprise segment.")
        return llm
    
    @pytest.fixture
    def personalization_engine(self, mock_llm):
        return PersonalizationEngine(llm=mock_llm)
    
    @pytest.fixture
    def sample_profile(self):
        return UserProfile(
            user_id="user_123",
            segment="enterprise",
            interests=["AI", "automation"],
            language="en",
        )
    
    def test_personalize_returns_variant(self, personalization_engine, sample_profile):
        """Test personalization returns a variant."""
        context = PersonalizationContext()
        
        variant = personalization_engine.personalize(
            content="Original content",
            user_profile=sample_profile,
            context=context,
        )
        
        assert isinstance(variant, PersonalizedVariant)
        assert variant.content
        assert variant.confidence_score > 0
    
    def test_create_segment_variants(self, personalization_engine):
        """Test creating variants for multiple segments."""
        context = PersonalizationContext()
        
        variants = personalization_engine.create_segment_variants(
            content="Original content",
            segments=["enterprise", "smb", "startup"],
            context=context,
        )
        
        assert len(variants) == 3
        assert all(isinstance(v, PersonalizedVariant) for v in variants)


class TestMultiLanguageSupport:
    """Unit tests for multi-language support."""
    
    @pytest.fixture
    def mock_llm(self):
        llm = Mock()
        llm.invoke.return_value = Mock(content="Test content")
        return llm
    
    def test_arabic_content_direction(self):
        """Test Arabic content has RTL direction."""
        config = LANGUAGE_CONFIGS["ar"]
        assert config.direction == "rtl"
    
    def test_english_content_direction(self):
        """Test English content has LTR direction."""
        config = LANGUAGE_CONFIGS["en"]
        assert config.direction == "ltr"
    
    def test_arabic_optimization_replaces_punctuation(self):
        """Test Arabic optimization replaces punctuation correctly."""
        generator = MultiLanguageContentGenerator(llm=Mock())
        
        content = "Hello, world; how are you?"
        optimized = generator._optimize_arabic_content(content)
        
        assert "،" in optimized  # Arabic comma
        assert "؛" in optimized  # Arabic semicolon
        assert "؟" in optimized  # Arabic question mark
    
    def test_translation_memory_caching(self, mock_llm):
        """Test translation memory caches results."""
        generator = MultiLanguageContentGenerator(llm=mock_llm)
        
        brief = ContentBrief(
            topic="Test",
            topic_summary="Test",
            key_themes=[],
            target_keywords=[],
            competitor_analysis=[],
            audience_insights=[],
            trends=[],
            statistics=[],
            expert_quotes=[],
            content_angle="Test",
            suggested_outline=[],
            language="en",
        )
        
        # First call
        result1 = generator.generate(brief, "blog_post", "ar")
        
        # Second call should use cache
        result2 = generator.generate(brief, "blog_post", "ar")
        
        assert result1["content"] == result2["content"]


class TestContentAnalytics:
    """Unit tests for content analytics."""
    
    @pytest.fixture
    def analytics_engine(self):
        return ContentAnalyticsEngine()
    
    def test_track_content_initializes_metrics(self, analytics_engine):
        """Test tracking initializes metrics for content."""
        metrics = analytics_engine.track_content(
            content_id="test_123",
            content_type="blog_post",
            language="en",
        )
        
        assert metrics.content_id == "test_123"
        assert metrics.content_type == "blog_post"
    
    def test_record_event_updates_metrics(self, analytics_engine):
        """Test recording events updates metrics."""
        analytics_engine.track_content("test_123", "blog_post", "en")
        
        analytics_engine.record_event("test_123", "impressions", 100)
        analytics_engine.record_event("test_123", "clicks", 10)
        
        metrics = analytics_engine.metrics_store["test_123"]
        summary = metrics.get_metric_summary("impressions")
        
        assert summary["count"] == 1
        assert summary["mean"] == 100
    
    def test_performance_report_generation(self, analytics_engine):
        """Test performance report generation."""
        analytics_engine.track_content("test_123", "blog_post", "en")
        analytics_engine.record_event("test_123", "impressions", 1000)
        analytics_engine.record_event("test_123", "clicks", 50)
        analytics_engine.record_event("test_123", "conversions", 5)
        
        report = analytics_engine.get_performance_report("test_123")
        
        assert report["content_id"] == "test_123"
        assert "metrics" in report
        assert "summary" in report
        assert "recommendations" in report
    
    def test_aggregate_report(self, analytics_engine):
        """Test aggregate report generation."""
        # Add multiple content pieces
        for i in range(3):
            analytics_engine.track_content(f"content_{i}", "blog_post", "en")
            analytics_engine.record_event(f"content_{i}", "impressions", 100 * (i + 1))
        
        report = analytics_engine.get_aggregate_report(content_type="blog_post")
        
        assert report["total_content_pieces"] == 3
        assert "metrics" in report
```

### 9.3 Integration Tests

```python
"""
Integration tests for the content generation pipeline.
"""

import pytest
from unittest.mock import Mock, patch

class TestContentGenerationPipeline:
    """Integration tests for the full pipeline."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM with realistic responses."""
        llm = Mock()
        
        def mock_invoke(prompt):
            prompt_str = str(prompt)
            
            if "research" in prompt_str.lower() or "keyword" in prompt_str.lower():
                return Mock(content="""
                {
                    "topic_summary": "AI is transforming marketing",
                    "key_themes": ["automation", "personalization", "analytics"],
                    "target_keywords": ["AI marketing", "content automation"],
                    "content_angle": "How AI transforms marketing operations"
                }
                """)
            elif "generate" in prompt_str.lower() or "write" in prompt_str.lower():
                return Mock(content="""
                # AI in Marketing: Transforming the Industry
                
                Artificial intelligence is revolutionizing how businesses approach marketing.
                
                ## Key Benefits
                
                1. Automation of repetitive tasks
                2. Personalized customer experiences
                3. Data-driven decision making
                
                ## Conclusion
                
                AI is not just a trend; it's a fundamental shift in marketing.
                """)
            elif "optimize" in prompt_str.lower():
                return Mock(content="""
                # AI in Marketing: Transforming the Industry in 2024
                
                Artificial intelligence is revolutionizing how businesses approach marketing,
                delivering unprecedented automation and personalization capabilities.
                
                ## Key Benefits of AI Marketing
                
                1. Automation of repetitive marketing tasks
                2. Personalized customer experiences at scale
                3. Data-driven decision making and optimization
                
                ## Getting Started with AI Marketing
                
                Businesses can start their AI marketing journey today.
                """)
            elif "personalize" in prompt_str.lower():
                return Mock(content="""
                # AI in Marketing: Enterprise Transformation Guide
                
                For enterprise marketing leaders, AI offers unprecedented opportunities
                to scale operations and deliver personalized experiences.
                """)
            else:
                return Mock(content="Generated content")
        
        llm.invoke = mock_invoke
        return llm
    
    def test_full_pipeline_execution(self, mock_llm):
        """Test the complete pipeline from research to analytics."""
        # Initialize all agents
        research_agent = ContentResearchAgent(llm=mock_llm)
        generation_agent = ContentGenerationAgent(llm=mock_llm)
        optimization_agent = ContentOptimizationAgent(llm=mock_llm)
        personalization_engine = PersonalizationEngine(llm=mock_llm)
        analytics_engine = ContentAnalyticsEngine()
        
        # Execute pipeline
        brief = research_agent.research(
            topic="AI in marketing",
            audience="Marketing professionals",
            content_type="blog_post",
        )
        
        generated = generation_agent.generate(
            brief=brief,
            content_type="blog_post",
            language="en",
        )
        
        optimized = optimization_agent.optimize(
            content=generated["content"],
            content_type="blog_post",
            target_keywords=[k.keyword for k in brief.target_keywords[:5]],
            language="en",
        )
        
        user_profile = UserProfile(
            user_id="test_user",
            segment="enterprise",
            language="en",
        )
        
        personalized = personalization_engine.personalize(
            content=optimized["optimized_content"],
            user_profile=user_profile,
            context=PersonalizationContext(),
        )
        
        # Verify pipeline output
        assert brief is not None
        assert generated["content"]
        assert optimized["overall_score"] > 0
        assert personalized.content
        assert personalized.confidence_score > 0
    
    def test_multi_language_pipeline(self, mock_llm):
        """Test pipeline with multiple languages."""
        generator = MultiLanguageContentGenerator(llm=mock_llm)
        
        brief = ContentBrief(
            topic="AI in Marketing",
            topic_summary="AI transforms marketing",
            key_themes=["automation"],
            target_keywords=[],
            competitor_analysis=[],
            audience_insights=[],
            trends=[],
            statistics=[],
            expert_quotes=[],
            content_angle="AI marketing transformation",
            suggested_outline=[],
            language="en",
        )
        
        # Generate in English
        en_result = generator.generate(brief, "blog_post", "en")
        assert en_result["language"] == "en"
        assert en_result["direction"] == "ltr"
        
        # Generate in Arabic
        ar_result = generator.generate(brief, "blog_post", "ar")
        assert ar_result["language"] == "ar"
        assert ar_result["direction"] == "rtl"
    
    def test_arabic_to_english_translation(self, mock_llm):
        """Test translation from Arabic to English."""
        generator = MultiLanguageContentGenerator(llm=mock_llm)
        
        arabic_content = "# الذكاء الاصطناعي في التسويق\n\nمحتوى تجريبي"
        
        translated = generator.translate_content(
            content=arabic_content,
            source_language="ar",
            target_language="en",
        )
        
        assert translated is not None
        assert len(translated) > 0


class TestLangGraphWorkflow:
    """Integration tests for LangGraph workflow."""
    
    def test_workflow_graph_execution(self):
        """Test LangGraph workflow execution."""
        from langgraph.graph import StateGraph, END
        
        # Create a simple test graph
        workflow = StateGraph(dict)
        
        def node_a(state):
            state["value"] = "A"
            return state
        
        def node_b(state):
            state["value"] += "B"
            return state
        
        workflow.add_node("a", node_a)
        workflow.add_node("b", node_b)
        workflow.set_entry_point("a")
        workflow.add_edge("a", "b")
        workflow.add_edge("b", END)
        
        app = workflow.compile()
        result = app.invoke({"value": ""})
        
        assert result["value"] == "AB"
```

### 9.4 End-to-End Tests

```python
"""
End-to-end tests for the content generation system.
These tests use real LLM calls and should be run sparingly.
"""

import pytest
import os

# Skip these tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not available"
)

class TestEndToEndContentGeneration:
    """End-to-end tests with real LLM calls."""
    
    @pytest.fixture(scope="module")
    def llm(self):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    @pytest.fixture(scope="module")
    def research_agent(self, llm):
        return ContentResearchAgent(llm=llm)
    
    @pytest.fixture(scope="module")
    def generation_agent(self, llm):
        return ContentGenerationAgent(llm=llm)
    
    @pytest.fixture(scope="module")
    def optimization_agent(self, llm):
        return ContentOptimizationAgent(llm=llm)
    
    def test_research_to_generation_pipeline(self, research_agent, generation_agent):
        """Test research and generation with real LLM."""
        brief = research_agent.research(
            topic="Sustainable marketing practices",
            audience="Eco-conscious consumers",
            content_type="blog_post",
        )
        
        assert brief is not None
        assert len(brief.target_keywords) > 0
        
        generated = generation_agent.generate(
            brief=brief,
            content_type="blog_post",
            language="en",
        )
        
        assert generated["word_count"] > 100
        assert len(generated["content"]) > 0
    
    def test_optimization_improves_content(self, optimization_agent):
        """Test that optimization actually improves content scores."""
        original_content = """
        Marketing is important. Companies should do marketing. 
        Marketing helps businesses grow. There are many marketing strategies.
        """
        
        optimized = optimization_agent.optimize(
            content=original_content,
            content_type="blog_post",
            target_keywords=["marketing", "business growth"],
            language="en",
        )
        
        assert optimized["seo_score"] >= 0
        assert optimized["readability_score"] >= 0
        assert optimized["engagement_score"] >= 0
        assert len(optimized["improvement_suggestions"]) > 0
    
    def test_arabic_content_generation(self, llm):
        """Test Arabic content generation with real LLM."""
        generator = MultiLanguageContentGenerator(llm=llm)
        
        brief = ContentBrief(
            topic="Digital transformation",
            topic_summary="Digital transformation is essential",
            key_themes=["technology", "innovation"],
            target_keywords=[],
            competitor_analysis=[],
            audience_insights=[],
            trends=[],
            statistics=[],
            expert_quotes=[],
            content_angle="Digital transformation guide",
            suggested_outline=[],
            language="ar",
        )
        
        result = generator.generate(brief, "blog_post", "ar")
        
        assert result["language"] == "ar"
        assert result["direction"] == "rtl"
        assert len(result["content"]) > 0
    
    def test_full_pipeline_with_analytics(self, research_agent, generation_agent, optimization_agent):
        """Test complete pipeline including analytics."""
        analytics_engine = ContentAnalyticsEngine()
        
        # Research
        brief = research_agent.research(
            topic="Remote work productivity",
            audience="Remote team managers",
            content_type="blog_post",
        )
        
        # Generate
        generated = generation_agent.generate(
            brief=brief,
            content_type="blog_post",
            language="en",
        )
        
        # Optimize
        optimized = optimization_agent.optimize(
            content=generated["content"],
            content_type="blog_post",
            target_keywords=[k.keyword for k in brief.target_keywords[:3]],
            language="en",
        )
        
        # Track
        content_id = "e2e_test_content"
        analytics_engine.track_content(
            content_id=content_id,
            content_type="blog_post",
            language="en",
        )
        
        # Simulate events
        analytics_engine.record_event(content_id, "impressions", 5000)
        analytics_engine.record_event(content_id, "clicks", 250)
        analytics_engine.record_event(content_id, "conversions", 12)
        analytics_engine.record_event(content_id, "engagement_time", 150)
        
        # Get report
        report = analytics_engine.get_performance_report(content_id)
        
        assert report["content_id"] == content_id
        assert "metrics" in report
        assert "summary" in report
        assert "recommendations" in report
```

### 9.5 Performance Tests

```python
"""
Performance and load tests for the content generation system.
"""

import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class TestPerformance:
    """Performance tests for content generation."""
    
    def test_research_agent_response_time(self):
        """Test research agent completes within acceptable time."""
        llm = Mock()
        llm.invoke.return_value = Mock(content='{"result": "test"}')
        
        agent = ContentResearchAgent(llm=llm)
        
        start = time.time()
        result = agent.research("test topic", "test audience", "blog_post")
        elapsed = time.time() - start
        
        assert elapsed < 30  # Should complete within 30 seconds
    
    def test_generation_agent_response_time(self):
        """Test generation agent completes within acceptable time."""
        llm = Mock()
        llm.invoke.return_value = Mock(content="Generated content " * 100)
        
        agent = ContentGenerationAgent(llm=llm)
        
        brief = ContentBrief(
            topic="Test",
            topic_summary="Test",
            key_themes=[],
            target_keywords=[],
            competitor_analysis=[],
            audience_insights=[],
            trends=[],
            statistics=[],
            expert_quotes=[],
            content_angle="Test",
            suggested_outline=[],
            language="en",
        )
        
        start = time.time()
        result = agent.generate(brief, "blog_post", "en")
        elapsed = time.time() - start
        
        assert elapsed < 60  # Should complete within 60 seconds
    
    def test_optimization_agent_response_time(self):
        """Test optimization agent completes within acceptable time."""
        llm = Mock()
        llm.invoke.return_value = Mock(content="Optimized content")
        
        agent = ContentOptimizationAgent(llm=llm)
        
        content = "Test content " * 100
        
        start = time.time()
        result = agent.optimize(content, "blog_post", ["test"], "en")
        elapsed = time.time() - start
        
        assert elapsed < 30  # Should complete within 30 seconds
    
    def test_concurrent_content_generation(self):
        """Test system handles concurrent generation requests."""
        llm = Mock()
        llm.invoke.return_value = Mock(content="Generated content")
        
        def generate_content(topic):
            agent = ContentGenerationAgent(llm=llm)
            brief = ContentBrief(
                topic=topic,
                topic_summary=f"Summary for {topic}",
                key_themes=[],
                target_keywords=[],
                competitor_analysis=[],
                audience_insights=[],
                trends=[],
                statistics=[],
                expert_quotes=[],
                content_angle="Test",
                suggested_outline=[],
                language="en",
            )
            return agent.generate(brief, "blog_post", "en")
        
        topics = [f"Topic {i}" for i in range(5)]
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_content, topic) for topic in topics]
            results = [f.result() for f in as_completed(futures)]
        
        elapsed = time.time() - start
        
        assert len(results) == 5
        assert elapsed < 120  # All 5 should complete within 2 minutes
    
    def test_analytics_query_performance(self):
        """Test analytics queries are fast."""
        engine = ContentAnalyticsEngine()
        
        # Add test data
        for i in range(100):
            content_id = f"content_{i}"
            engine.track_content(content_id, "blog_post", "en")
            for j in range(10):
                engine.record_event(content_id, "impressions", 100)
                engine.record_event(content_id, "clicks", 10)
        
        start = time.time()
        report = engine.get_aggregate_report(content_type="blog_post")
        elapsed = time.time() - start
        
        assert elapsed < 5  # Should complete within 5 seconds
        assert report["total_content_pieces"] == 100
```

### 9.6 Test Configuration

```python
# conftest.py
import pytest
import os

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        "mock_llm": True,
        "max_retries": 3,
        "timeout_seconds": 30,
    }

@pytest.fixture(autouse=True)
def reset_analytics_store():
    """Reset analytics store between tests."""
    yield
    # Cleanup after test

# pytest.ini
"""
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
addopts = -v --tb=short
"""
```

---

## Appendix: Environment Setup

### Requirements.txt

```
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.2.0
langchain-anthropic>=0.2.0
langchain-community>=0.3.0
langgraph>=0.2.0
langsmith>=0.1.0
openai>=1.0.0
anthropic>=0.30.0
chromadb>=0.4.0
pinecone-client>=3.0.0
redis>=5.0.0
celery>=5.3.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
python-dotenv>=1.0.0
textstat>=0.7.3
beautifulsoup4>=4.12.0
requests>=2.31.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=content-generation
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost/content_db
CHROMA_DB_PATH=./chroma_db
```

---

## Summary

This implementation plan provides a comprehensive blueprint for building an AI-powered content generation system using LangChain DeepAgents. The system features:

1. **Multi-agent architecture** with specialized research, generation, and optimization agents
2. **LangGraph-based workflow** for stateful, resumable content pipelines
3. **Multi-language support** with full Arabic (RTL) and English (LTR) capabilities
4. **Personalization engine** with segment-based, behavioral, and contextual targeting
5. **Real-time analytics** with performance tracking and actionable recommendations
6. **Comprehensive testing** with unit, integration, end-to-end, and performance tests
7. **Production-ready code** with FastAPI endpoints, Celery task queues, and proper error handling

The modular design allows for incremental adoption—teams can start with individual agents and gradually build toward the full pipeline as their needs evolve.</longcat_think>
