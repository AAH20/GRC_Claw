# AI-Powered Brand Monitoring Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0.0  
**Author:** Ahmed Hassan  
**Date:** 2026-10-01  
**Status:** Draft  
**Stack:** LangChain DeepAgents, Python 3.11+, OpenAI GPT-4, Pinecone, Redis, FastAPI

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Listening Agent Implementation](#2-listening-agent-implementation)
3. [Analysis Agent Implementation](#3-analysis-agent-implementation)
4. [Response Agent Implementation](#4-response-agent-implementation)
5. [Reporting Agent Implementation](#5-reporting-agent-implementation)
6. [Performance Analytics Agent Implementation](#6-performance-analytics-agent-implementation)
7. [Code Examples and Snippets](#7-code-examples-and-snippets)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The AI-powered brand monitoring system uses LangChain DeepAgents to create a multi-agent pipeline that continuously listens to brand mentions across channels, analyzes sentiment and intent, generates response recommendations, produces reports, and tracks performance metrics.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Brand Monitoring System                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │Listening │───▶│ Analysis │───▶│ Response │───▶│ Reporting│     │
│  │  Agent   │    │  Agent   │    │  Agent   │    │  Agent   │     │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│       │               │               │               │             │
│       ▼               ▼               ▼               ▼             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Performance Analytics Agent                     │  │
│  │         (Cross-cutting: monitors all agents)                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Shared Infrastructure Layer                     │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │  │
│  │  │Pinecone │ │  Redis  │ │PostgreSQL│ │  S3     │ │OpenAI  │ │  │
│  │  │(Vector) │ │ (Cache) │ │ (Store)  │ │(Assets) │ │(LLM)   │ │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Agent Topology

| Agent | Role | Input | Output | Model |
|-------|------|-------|--------|-------|
| Listening Agent | Data ingestion & normalization | Social APIs, RSS, webhooks | Standardized mention objects | GPT-4o-mini |
| Analysis Agent | Sentiment, intent, entity extraction | Standardized mentions | Enriched analysis objects | GPT-4o |
| Response Agent | Response generation & routing | Analysis objects | Response drafts + routing decisions | GPT-4o |
| Reporting Agent | Report generation & distribution | Aggregated analysis data | PDF/HTML reports + alerts | GPT-4o-mini |
| Performance Analytics Agent | Metrics, dashboards, optimization | All agent outputs | KPIs, recommendations, alerts | GPT-4o-mini |

### 1.3 Communication Patterns

- **Event-Driven:** Agents communicate via Redis Streams for real-time processing
- **Orchestration:** LangChain DeepAgents `AgentExecutor` coordinates the pipeline
- **State Management:** Shared state via Redis with PostgreSQL persistence
- **Error Handling:** Dead-letter queue with exponential backoff retry

### 1.4 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| LLM | OpenAI GPT-4o / GPT-4o-mini | Reasoning, generation, analysis |
| Framework | LangChain DeepAgents 0.3+ | Agent orchestration |
| Vector DB | Pinecone | Semantic search, deduplication |
| Cache | Redis 7+ | Real-time state, streams |
| Database | PostgreSQL 16+ | Persistent storage |
| Task Queue | Celery + Redis | Background processing |
| API | FastAPI | REST endpoints |
| Monitoring | Prometheus + Grafana | Observability |
| Deployment | Docker + Kubernetes | Container orchestration |

---

## 2. Listening Agent Implementation

### 2.1 Responsibilities

- Connect to data sources (Twitter/X API, Reddit API, News APIs, Google Alerts, RSS feeds)
- Normalize incoming data into a standard `Mention` schema
- Deduplicate mentions using vector similarity
- Enrich with metadata (author influence, reach, engagement)
- Publish to the processing stream

### 2.2 Data Source Connectors

```python
# connectors/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Optional
import uuid

@dataclass
class Mention:
    """Standardized mention schema across all sources."""
    id: str
    source: str                    # twitter, reddit, news, rss
    source_id: str                 # Original ID from source
    content: str                   # Raw text content
    author: str                    # Display name
    author_id: str                 # Platform-specific ID
    author_followers: int          # Influence metric
    url: Optional[str]             # Permalink
    published_at: datetime         # Original timestamp
    collected_at: datetime         # Ingestion timestamp
    language: str                  # ISO 639-1 code
    engagement: dict               # {likes, shares, comments, views}
    media_urls: list[str]          # Attached media
    parent_id: Optional[str]       # For threaded conversations
    metadata: dict                 # Source-specific extras
    brand_keywords_matched: list[str]  # Which keywords triggered

class BaseConnector(ABC):
    """Abstract base for all data source connectors."""

    def __init__(self, config: dict):
        self.config = config
        self.rate_limiter = RateLimiter(
            requests_per_window=config.get("rate_limit", 100),
            window_seconds=config.get("window", 60)
        )

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the data source."""
        pass

    @abstractmethod
    async def listen(self) -> AsyncIterator[Mention]:
        """Yield normalized mentions in real-time."""
        pass

    @abstractmethod
    async def backfill(self, since: datetime) -> AsyncIterator[Mention]:
        """Historical data ingestion."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up resources."""
        pass

    def normalize(self, raw_data: dict) -> Mention:
        """Override in subclass to map source-specific format to Mention."""
        raise NotImplementedError
```

### 2.3 Twitter/X Connector

```python
# connectors/twitter_connector.py
import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator

import tweepy
from .base import BaseConnector, Mention

class TwitterConnector(BaseConnector):
    """Twitter/X API v2 connector with filtered stream support."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.bearer_token = config["bearer_token"]
        self.keywords = config.get("keywords", [])
        self.client = None
        self.streaming_client = None

    async def connect(self) -> None:
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            wait_on_rate_limit=True
        )
        self.streaming_client = BrandStreamListener(
            bearer_token=self.bearer_token,
            keywords=self.keywords
        )

    async def listen(self) -> AsyncIterator[Mention]:
        """Stream mentions matching brand keywords."""
        for tweet in self.streaming_client.stream():
            mention = self._normalize_tweet(tweet)
            if mention:
                yield mention

    async def backfill(self, since: datetime) -> AsyncIterator[Mention]:
        """Search recent tweets (last 7 days for standard API)."""
        query = " OR ".join(self.keywords)
        paginator = tweepy.Paginator(
            self.client.search_recent_tweets,
            query=query,
            tweet_fields=["created_at", "public_metrics", "author_id", "lang"],
            user_fields=["public_metrics", "username"],
            expansions=["author_id"],
            start_time=since.isoformat(),
            max_results=100
        )
        for response in paginator:
            users = {u.id: u for u in response.includes.get("users", [])}
            for tweet in response.data or []:
                author = users.get(tweet.author_id)
                mention = self._normalize_tweet(tweet, author)
                if mention:
                    yield mention

    def _normalize_tweet(self, tweet, author=None) -> Mention:
        metrics = tweet.public_metrics or {}
        author_metrics = author.public_metrics if author else {}
        return Mention(
            id=str(uuid.uuid4()),
            source="twitter",
            source_id=str(tweet.id),
            content=tweet.text,
            author=author.username if author else "unknown",
            author_id=str(tweet.author_id) if tweet.author_id else "unknown",
            author_followers=author_metrics.get("followers_count", 0),
            url=f"https://twitter.com/i/web/status/{tweet.id}",
            published_at=tweet.created_at,
            collected_at=datetime.now(timezone.utc),
            language=tweet.lang or "en",
            engagement={
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "quotes": metrics.get("quote_count", 0),
                "impressions": metrics.get("impression_count", 0),
            },
            media_urls=self._extract_media(tweet),
            parent_id=str(tweet.referenced_tweets[0].id) if hasattr(tweet, "referenced_tweets") and tweet.referenced_tweets else None,
            metadata={"verified": author.verified if author else False},
            brand_keywords_matched=self._match_keywords(tweet.text),
        )

    def _extract_media(self, tweet) -> list[str]:
        if not hasattr(tweet, "attachments"):
            return []
        # Extract media URLs from attachments
        return []

    def _match_keywords(self, text: str) -> list[str]:
        text_lower = text.lower()
        return [kw for kw in self.keywords if kw.lower() in text_lower]
```

### 2.4 Reddit Connector

```python
# connectors/reddit_connector.py
import asyncpraw
from datetime import datetime, timezone
from typing import AsyncIterator

from .base import BaseConnector, Mention

class RedditConnector(BaseConnector):
    """Reddit connector using asyncpraw for subreddit monitoring."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.subreddits = config.get("subreddits", [])
        self.keywords = config.get("keywords", [])
        self.reddit = None

    async def connect(self) -> None:
        self.reddit = asyncpraw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent="BrandMonitor/1.0",
        )

    async def listen(self) -> AsyncIterator[Mention]:
        """Stream comments and submissions from monitored subreddits."""
        for subreddit_name in self.subreddits:
            subreddit = await self.reddit.subreddit(subreddit_name)
            # Stream comments
            async for comment in subreddit.stream.comments(skip_existing=True):
                if self._matches_keywords(comment.body):
                    yield self._normalize_comment(comment, subreddit_name)
            # Stream submissions
            async for submission in subreddit.stream.submissions(skip_existing=True):
                if self._matches_keywords(submission.title + " " + submission.selftext):
                    yield self._normalize_submission(submission, subreddit_name)

    async def backfill(self, since: datetime) -> AsyncIterator[Mention]:
        """Fetch recent posts from subreddits."""
        for subreddit_name in self.subreddits:
            subreddit = await self.reddit.subreddit(subreddit_name)
            async for submission in subreddit.new(limit=500):
                created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                if created < since:
                    break
                if self._matches_keywords(submission.title + " " + submission.selftext):
                    yield self._normalize_submission(submission, subreddit_name)

    def _normalize_comment(self, comment, subreddit) -> Mention:
        return Mention(
            id=str(uuid.uuid4()),
            source="reddit",
            source_id=str(comment.id),
            content=comment.body,
            author=str(comment.author) if comment.author else "[deleted]",
            author_id=str(comment.author_fullname) if hasattr(comment, "author_fullname") else "unknown",
            author_followers=0,  # Reddit doesn't expose this easily
            url=f"https://reddit.com{comment.permalink}",
            published_at=datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
            collected_at=datetime.now(timezone.utc),
            language="en",
            engagement={
                "upvotes": comment.score,
                "replies": comment.num_comments if hasattr(comment, "num_comments") else 0,
            },
            media_urls=[],
            parent_id=str(comment.parent_id) if comment.parent_id else None,
            metadata={"subreddit": subreddit, "is_submission": False},
            brand_keywords_matched=self._match_keywords(comment.body),
        )

    def _normalize_submission(self, submission, subreddit) -> Mention:
        return Mention(
            id=str(uuid.uuid4()),
            source="reddit",
            source_id=str(submission.id),
            content=f"{submission.title}\n\n{submission.selftext}",
            author=str(submission.author) if submission.author else "[deleted]",
            author_id=str(submission.author_fullname) if hasattr(submission, "author_fullname") else "unknown",
            author_followers=0,
            url=f"https://reddit.com{submission.permalink}",
            published_at=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
            collected_at=datetime.now(timezone.utc),
            language="en",
            engagement={
                "upvotes": submission.score,
                "comments": submission.num_comments,
            },
            media_urls=[submission.url] if submission.url else [],
            parent_id=None,
            metadata={"subreddit": subreddit, "is_submission": True},
            brand_keywords_matched=self._match_keywords(submission.title + " " + submission.selftext),
        )

    def _matches_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.keywords)

    def _match_keywords(self, text: str) -> list[str]:
        text_lower = text.lower()
        return [kw for kw in self.keywords if kw.lower() in text_lower]
```

### 2.5 News & RSS Connector

```python
# connectors/news_connector.py
import feedparser
import httpx
from datetime import datetime, timezone
from typing import AsyncIterator

from .base import BaseConnector, Mention

class NewsConnector(BaseConnector):
    """RSS feed and news API connector."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.feeds = config.get("feeds", [])
        self.news_api_key = config.get("news_api_key")
        self.keywords = config.get("keywords", [])

    async def connect(self) -> None:
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def listen(self) -> AsyncIterator[Mention]:
        """Poll RSS feeds periodically."""
        while True:
            for feed_url in self.feeds:
                async for mention in self._poll_feed(feed_url):
                    yield mention
            await asyncio.sleep(self.config.get("poll_interval", 300))

    async def backfill(self, since: datetime) -> AsyncIterator[Mention]:
        """Fetch historical articles from NewsAPI."""
        if not self.news_api_key:
            return
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": " OR ".join(self.keywords),
            "from": since.strftime("%Y-%m-%d"),
            "sortBy": "publishedAt",
            "apiKey": self.news_api_key,
            "pageSize": 100,
        }
        response = await self.http_client.get(url, params=params)
        data = response.json()
        for article in data.get("articles", []):
            yield self._normalize_article(article)

    async def _poll_feed(self, feed_url: str) -> AsyncIterator[Mention]:
        response = await self.http_client.get(feed_url)
        feed = feedparser.parse(response.content)
        for entry in feed.entries:
            published = self._parse_date(entry)
            if self._matches_keywords(entry.title + " " + entry.get("summary", "")):
                yield Mention(
                    id=str(uuid.uuid4()),
                    source="news",
                    source_id=entry.get("id", entry.link),
                    content=f"{entry.title}\n\n{entry.get('summary', '')}",
                    author=entry.get("author", feed.feed.get("title", "Unknown")),
                    author_id=entry.get("author", "unknown"),
                    author_followers=0,
                    url=entry.link,
                    published_at=published,
                    collected_at=datetime.now(timezone.utc),
                    language=entry.get("language", "en"),
                    engagement={},
                    media_urls=[],
                    parent_id=None,
                    metadata={"feed_title": feed.feed.get("title", "")},
                    brand_keywords_matched=self._match_keywords(entry.title),
                )

    def _normalize_article(self, article: dict) -> Mention:
        published = datetime.fromisoformat(
            article["publishedAt"].replace("Z", "+00:00")
        )
        return Mention(
            id=str(uuid.uuid4()),
            source="news",
            source_id=article.get("url", ""),
            content=f"{article['title']}\n\n{article.get('description', '')}",
            author=article.get("author", article.get("source", {}).get("name", "Unknown")),
            author_id=article.get("source", {}).get("id", "unknown"),
            author_followers=0,
            url=article.get("url", ""),
            published_at=published,
            collected_at=datetime.now(timezone.utc),
            language="en",
            engagement={},
            media_urls=[article["urlToImage"]] if article.get("urlToImage") else [],
            parent_id=None,
            metadata={"source_name": article.get("source", {}).get("name", "")},
            brand_keywords_matched=self._match_keywords(article["title"]),
        )

    def _parse_date(self, entry) -> datetime:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        return datetime.now(timezone.utc)

    def _matches_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in self.keywords)

    def _match_keywords(self, text: str) -> list[str]:
        text_lower = text.lower()
        return [kw for kw in self.keywords if kw.lower() in text_lower]
```

### 2.6 Deduplication Service

```python
# services/deduplication.py
import hashlib
from typing import Optional

from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec

class DeduplicationService:
    """Vector-based deduplication using Pinecone."""

    def __init__(self, api_key: str, environment: str, index_name: str = "brand-mentions"):
        self.pc = Pinecone(api_key=api_key)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.index_name = index_name
        self._ensure_index()

    def _ensure_index(self):
        if self.index_name not in [idx.name for idx in self.pc.list_indexes()]:
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        self.index = self.pc.Index(self.index_name)

    async def is_duplicate(self, mention, threshold: float = 0.92) -> Optional[str]:
        """Check if a mention is a duplicate. Returns original ID if duplicate."""
        embedding = await self.embeddings.aembed_query(mention.content)
        results = self.index.query(
            vector=embedding,
            top_k=1,
            include_metadata=True,
            filter={"source": mention.source},
        )
        if results.matches and results.matches[0].score >= threshold:
            return results.matches[0].id
        return None

    async def store(self, mention) -> None:
        """Store mention embedding for future deduplication."""
        embedding = await self.embeddings.aembed_query(mention.content)
        self.index.upsert(
            vectors=[{
                "id": mention.id,
                "values": embedding,
                "metadata": {
                    "source": mention.source,
                    "author": mention.author,
                    "published_at": mention.published_at.isoformat(),
                    "brand_keywords": mention.brand_keywords_matched,
                },
            }]
        )

    def content_hash(self, content: str) -> str:
        """Fast exact-match hash for obvious duplicates."""
        normalized = " ".join(content.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()
```

### 2.7 Listening Agent (LangChain DeepAgents)

```python
# agents/listening_agent.py
import json
import logging
from datetime import datetime, timezone
from typing import AsyncIterator

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

from connectors.twitter_connector import TwitterConnector
from connectors.reddit_connector import RedditConnector
from connectors.news_connector import NewsConnector
from services.deduplication import DeduplicationService

logger = logging.getLogger(__name__)

LISTENING_SYSTEM_PROMPT = """You are the Listening Agent for a brand monitoring system.

Your role is to:
1. Monitor configured data sources for brand mentions
2. Normalize all incoming data into the standard Mention schema
3. Filter out irrelevant content and duplicates
4. Enrich mentions with available metadata
5. Publish validated mentions to the processing stream

Rules:
- Always validate data quality before publishing
- Flag potential bot accounts and spam
- Preserve original timestamps and source attribution
- Handle rate limits gracefully with exponential backoff
- Log all ingestion metrics for the Performance Analytics Agent

Output format: JSON array of Mention objects
"""

class ListeningAgent:
    """LangChain DeepAgents-based listening agent."""

    def __init__(self, config: dict):
        self.config = config
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=4096,
        )
        self.dedup = DeduplicationService(
            api_key=config["pinecone_api_key"],
            environment=config.get("pinecone_environment", "us-east-1"),
        )
        self.connectors: list[BaseConnector] = []
        self.redis_client = None
        self._setup_connectors()
        self._setup_agent()

    def _setup_connectors(self):
        """Initialize all configured connectors."""
        connector_configs = self.config.get("connectors", {})
        if "twitter" in connector_configs:
            self.connectors.append(TwitterConnector(connector_configs["twitter"]))
        if "reddit" in connector_configs:
            self.connectors.append(RedditConnector(connector_configs["reddit"]))
        if "news" in connector_configs:
            self.connectors.append(NewsConnector(connector_configs["news"]))

    def _setup_agent(self):
        """Create the LangChain agent with tools."""
        tools = [
            Tool(
                name="validate_mention",
                func=self._validate_mention,
                description="Validate a mention object for data quality and completeness.",
            ),
            Tool(
                name="check_duplicate",
                func=self._check_duplicate,
                description="Check if a mention is a duplicate using vector similarity.",
            ),
            Tool(
                name="enrich_metadata",
                func=self._enrich_metadata,
                description="Enrich mention with additional metadata (author influence, reach).",
            ),
            Tool(
                name="publish_mention",
                func=self._publish_mention,
                description="Publish a validated mention to the Redis processing stream.",
            ),
            Tool(
                name="flag_spam",
                func=self._flag_spam,
                description="Flag a mention as potential spam or bot content.",
            ),
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", LISTENING_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        langchain_agent = create_openai_functions_agent(self.llm, tools, prompt)
        self.executor = AgentExecutor(
            agent=langchain_agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )

    async def start(self):
        """Start all connectors and begin listening."""
        for connector in self.connectors:
            await connector.connect()
            logger.info(f"Connected: {connector.__class__.__name__}")

        # Start listening tasks
        tasks = []
        for connector in self.connectors:
            task = asyncio.create_task(self._process_connector(connector))
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def _process_connector(self, connector: BaseConnector):
        """Process mentions from a single connector."""
        async for mention in connector.listen():
            try:
                # Quick exact-match dedup
                content_hash = self.dedup.content_hash(mention.content)
                if await self._is_exact_duplicate(content_hash):
                    logger.debug(f"Exact duplicate skipped: {mention.source_id}")
                    continue

                # Vector similarity dedup
                duplicate_id = await self.dedup.is_duplicate(mention)
                if duplicate_id:
                    logger.info(f"Vector duplicate found: {mention.source_id} -> {duplicate_id}")
                    continue

                # Use LLM agent for validation and enrichment
                result = await self.executor.ainvoke({
                    "input": f"Validate and process this mention: {mention.__dict__}"
                })

                # Store embedding for future dedup
                await self.dedup.store(mention)

                # Publish to stream
                await self._publish_to_stream(mention)

            except Exception as e:
                logger.error(f"Error processing mention from {connector.__class__.__name__}: {e}")
                await self._send_to_dead_letter(mention, str(e))

    async def _validate_mention(self, mention_data: str) -> str:
        """Tool: Validate mention quality."""
        data = json.loads(mention_data)
        issues = []
        if not data.get("content") or len(data["content"]) < 10:
            issues.append("Content too short")
        if not data.get("author"):
            issues.append("Missing author")
        if not data.get("published_at"):
            issues.append("Missing timestamp")
        return json.dumps({"valid": len(issues) == 0, "issues": issues})

    async def _check_duplicate(self, mention_id: str) -> str:
        """Tool: Check for duplicates."""
        # Implementation delegates to dedup service
        return json.dumps({"is_duplicate": False})

    async def _enrich_metadata(self, mention_data: str) -> str:
        """Tool: Enrich with additional metadata."""
        data = json.loads(mention_data)
        # Add influence score, reach estimation, etc.
        data["metadata"]["influence_score"] = self._calculate_influence(data)
        return json.dumps(data)

    async def _publish_mention(self, mention_data: str) -> str:
        """Tool: Publish to Redis stream."""
        return await self._publish_to_stream(json.loads(mention_data))

    async def _flag_spam(self, mention_id: str) -> str:
        """Tool: Flag as spam."""
        logger.warning(f"Spam flagged: {mention_id}")
        return json.dumps({"flagged": True})

    async def _publish_to_stream(self, mention) -> str:
        """Publish mention to Redis Stream for downstream processing."""
        if not self.redis_client:
            import redis.asyncio as aioredis
            self.redis_client = aioredis.from_url(
                self.config.get("redis_url", "redis://localhost:6379")
            )

        await self.redis_client.xadd(
            "brand:mentions:stream",
            {"data": json.dumps(mention.__dict__, default=str)},
            maxlen=100000,
        )
        logger.info(f"Published mention: {mention.id} from {mention.source}")
        return mention.id

    async def _is_exact_duplicate(self, content_hash: str) -> bool:
        """Check Redis for exact content hash match."""
        if not self.redis_client:
            return False
        exists = await self.redis_client.get(f"hash:{content_hash}")
        if not exists:
            await self.redis_client.setex(f"hash:{content_hash}", 86400, "1")
        return exists is not None

    async def _send_to_dead_letter(self, mention, error: str):
        """Send failed mentions to dead-letter queue."""
        await self.redis_client.xadd(
            "brand:mentions:dead_letter",
            {"data": json.dumps(mention.__dict__, default=str), "error": error},
        )

    def _calculate_influence(self, data: dict) -> float:
        """Calculate author influence score (0-100)."""
        followers = data.get("author_followers", 0)
        if followers > 1_000_000:
            return 100.0
        elif followers > 100_000:
            return 80.0
        elif followers > 10_000:
            return 60.0
        elif followers > 1_000:
            return 40.0
        return 20.0
```

---

## 3. Analysis Agent Implementation

### 3.1 Responsibilities

- Sentiment analysis (positive, negative, neutral, mixed)
- Emotion detection (joy, anger, fear, sadness, surprise)
- Intent classification (complaint, praise, question, suggestion, inquiry)
- Entity extraction (products, features, competitors, people)
- Topic clustering and trend detection
- Urgency scoring and priority assignment
- Brand health scoring

### 3.2 Analysis Schema

```python
# models/analysis.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class EmotionLabel(str, Enum):
    JOY = "joy"
    ANGER = "anger"
    FEAR = "fear"
    SADNESS = "sadness"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"

class IntentLabel(str, Enum):
    COMPLAINT = "complaint"
    PRAISE = "praise"
    QUESTION = "question"
    SUGGESTION = "suggestion"
    INQUIRY = "inquiry"
    COMPARISON = "comparison"
    PURCHASE_INTENT = "purchase_intent"
    CHURN_RISK = "churn_risk"
    SUPPORT_REQUEST = "support_request"

class UrgencyLevel(str, Enum):
    CRITICAL = "critical"      # Immediate response required (< 1 hour)
    HIGH = "high"              # Response within 4 hours
    MEDIUM = "medium"          # Response within 24 hours
    LOW = "low"                # Response within 72 hours
    NONE = "none"              # No response needed

@dataclass
class AnalysisResult:
    """Complete analysis result for a single mention."""
    mention_id: str
    analyzed_at: datetime

    # Sentiment
    sentiment: SentimentLabel
    sentiment_score: float          # -1.0 to 1.0
    sentiment_confidence: float     # 0.0 to 1.0

    # Emotions (multi-label)
    emotions: dict[EmotionLabel, float]  # emotion -> confidence

    # Intent
    primary_intent: IntentLabel
    secondary_intents: list[IntentLabel]
    intent_confidence: float

    # Entities
    products_mentioned: list[str]
    features_mentioned: list[str]
    competitors_mentioned: list[str]
    people_mentioned: list[str]

    # Topics
    topics: list[str]
    topic_confidence: dict[str, float]

    # Urgency & Priority
    urgency: UrgencyLevel
    urgency_score: float            # 0.0 to 1.0
    priority_score: float           # Composite 0.0 to 1.0

    # Brand Health Impact
    brand_health_impact: float      # -10.0 to +10.0
    reach_weight: float             # Based on author influence

    # Risk Assessment
    risk_flags: list[str]           # e.g., "viral_negative", "influencer_complaint"
    escalation_recommended: bool

    # Metadata
    model_version: str
    processing_time_ms: int
    raw_llm_response: Optional[str] = None
```

### 3.3 Analysis Agent

```python
# agents/analysis_agent.py
import json
import logging
import time
from datetime import datetime, timezone

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

from models.analysis import (
    AnalysisResult, SentimentLabel, EmotionLabel,
    IntentLabel, UrgencyLevel,
)

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """You are the Analysis Agent for a brand monitoring system.

Your role is to deeply analyze brand mentions and extract actionable insights.

Analysis dimensions:
1. SENTIMENT: Classify as positive, negative, neutral, or mixed. Provide a score from -1.0 (very negative) to +1.0 (very positive).
2. EMOTIONS: Detect all applicable emotions with confidence scores.
3. INTENT: Classify the primary intent (complaint, praise, question, suggestion, etc.).
4. ENTITIES: Extract mentioned products, features, competitors, and people.
5. TOPICS: Identify discussion topics and themes.
6. URGENCY: Assess how urgently this mention requires a response.
7. BRAND IMPACT: Estimate the potential impact on brand health (-10 to +10).
8. RISK FLAGS: Identify any risk patterns (viral negative, influencer complaint, etc.).

Rules:
- Consider context and sarcasm
- Weight by author influence and reach
- Flag crisis-level content immediately
- Be conservative with urgency assessments
- Always provide confidence scores

Output: Structured JSON matching the AnalysisResult schema.
"""

class AnalysisAgent:
    """LangChain DeepAgents-based analysis agent."""

    def __init__(self, config: dict):
        self.config = config
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        self._setup_agent()
        self._load_few_shot_examples()

    def _setup_agent(self):
        """Create the LangChain analysis agent."""
        tools = [
            Tool(
                name="analyze_sentiment",
                func=self._analyze_sentiment,
                description="Perform deep sentiment analysis on text content.",
            ),
            Tool(
                name="detect_emotions",
                func=self._detect_emotions,
                description="Detect emotional tone and intensity.",
            ),
            Tool(
                name="classify_intent",
                func=self._classify_intent,
                description="Classify the primary intent behind the mention.",
            ),
            Tool(
                name="extract_entities",
                func=self._extract_entities,
                description="Extract products, features, competitors, and people.",
            ),
            Tool(
                name="assess_urgency",
                func=self._assess_urgency,
                description="Assess urgency level and priority.",
            ),
            Tool(
                name="calculate_brand_impact",
                func=self._calculate_brand_impact,
                description="Calculate potential brand health impact.",
            ),
            Tool(
                name="check_risk_patterns",
                func=self._check_risk_patterns,
                description="Check for known risk patterns and escalation triggers.",
            ),
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", ANALYSIS_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="few_shot", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        langchain_agent = create_openai_functions_agent(self.llm, tools, prompt)
        self.executor = AgentExecutor(
            agent=langchain_agent,
            tools=tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=True,
        )

    def _load_few_shot_examples(self):
        """Load few-shot examples for better classification."""
        self.few_shot_examples = [
            {
                "input": "This product is absolutely terrible. Worst purchase ever. @YourBrand should be ashamed.",
                "output": {
                    "sentiment": "negative",
                    "sentiment_score": -0.95,
                    "emotions": {"anger": 0.9, "disgust": 0.7},
                    "primary_intent": "complaint",
                    "urgency": "high",
                    "risk_flags": ["strong_negative_language"],
                }
            },
            {
                "input": "Just tried @YourBrand's new feature and it's a game changer! Love the team's work.",
                "output": {
                    "sentiment": "positive",
                    "sentiment_score": 0.9,
                    "emotions": {"joy": 0.85, "trust": 0.7},
                    "primary_intent": "praise",
                    "urgency": "none",
                    "risk_flags": [],
                }
            },
            {
                "input": "How do I reset my password? Can't find the option anywhere.",
                "output": {
                    "sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "emotions": {"anticipation": 0.3},
                    "primary_intent": "support_request",
                    "urgency": "medium",
                    "risk_flags": [],
                }
            },
        ]

    async def analyze(self, mention) -> AnalysisResult:
        """Analyze a single mention and return structured results."""
        start_time = time.time()

        # Build analysis context
        context = self._build_analysis_context(mention)

        # Run the agent
        result = await self.executor.ainvoke({
            "input": context,
            "few_shot": self._format_few_shot(),
        })

        # Parse and validate result
        analysis = self._parse_result(result, mention, start_time)

        # Post-process: apply business rules
        analysis = self._apply_business_rules(analysis, mention)

        return analysis

    def _build_analysis_context(self, mention) -> str:
        """Build rich context for the analysis agent."""
        return json.dumps({
            "content": mention.content,
            "source": mention.source,
            "author": mention.author,
            "author_followers": mention.author_followers,
            "engagement": mention.engagement,
            "language": mention.language,
            "brand_keywords_matched": mention.brand_keywords_matched,
            "metadata": mention.metadata,
        }, default=str)

    def _format_few_shot(self) -> str:
        """Format few-shot examples for the prompt."""
        examples = []
        for ex in self.few_shot_examples:
            examples.append(f"Input: {ex['input']}\nOutput: {json.dumps(ex['output'])}")
        return "\n\n".join(examples)

    def _parse_result(self, result: dict, mention, start_time: float) -> AnalysisResult:
        """Parse agent output into AnalysisResult."""
        output = result.get("output", result)
        if isinstance(output, str):
            output = json.loads(output)

        processing_time = int((time.time() - start_time) * 1000)

        return AnalysisResult(
            mention_id=mention.id,
            analyzed_at=datetime.now(timezone.utc),
            sentiment=SentimentLabel(output.get("sentiment", "neutral")),
            sentiment_score=float(output.get("sentiment_score", 0.0)),
            sentiment_confidence=float(output.get("sentiment_confidence", 0.8)),
            emotions={
                EmotionLabel(k): float(v)
                for k, v in output.get("emotions", {}).items()
            },
            primary_intent=IntentLabel(output.get("primary_intent", "inquiry")),
            secondary_intents=[
                IntentLabel(i) for i in output.get("secondary_intents", [])
            ],
            intent_confidence=float(output.get("intent_confidence", 0.7)),
            products_mentioned=output.get("products_mentioned", []),
            features_mentioned=output.get("features_mentioned", []),
            competitors_mentioned=output.get("competitors_mentioned", []),
            people_mentioned=output.get("people_mentioned", []),
            topics=output.get("topics", []),
            topic_confidence=output.get("topic_confidence", {}),
            urgency=UrgencyLevel(output.get("urgency", "low")),
            urgency_score=float(output.get("urgency_score", 0.3)),
            priority_score=float(output.get("priority_score", 0.3)),
            brand_health_impact=float(output.get("brand_health_impact", 0.0)),
            reach_weight=self._calculate_reach_weight(mention),
            risk_flags=output.get("risk_flags", []),
            escalation_recommended=bool(output.get("escalation_recommended", False)),
            model_version="gpt-4o-2024-08-06",
            processing_time_ms=processing_time,
            raw_llm_response=json.dumps(output),
        )

    def _apply_business_rules(self, analysis: AnalysisResult, mention) -> AnalysisResult:
        """Apply business-specific rules on top of LLM analysis."""
        # Rule 1: High-follower negative mentions are automatically high urgency
        if (mention.author_followers > 100_000 and
            analysis.sentiment == SentimentLabel.NEGATIVE and
            analysis.urgency not in (UrgencyLevel.CRITICAL, UrgencyLevel.HIGH)):
            analysis.urgency = UrgencyLevel.HIGH
            analysis.urgency_score = max(analysis.urgency_score, 0.7)
            analysis.risk_flags.append("influencer_negative")

        # Rule 2: Viral content detection
        total_engagement = sum(mention.engagement.values())
        if total_engagement > 10_000 and analysis.sentiment == SentimentLabel.NEGATIVE:
            analysis.urgency = UrgencyLevel.CRITICAL
            analysis.risk_flags.append("viral_negative")
            analysis.escalation_recommended = True

        # Rule 3: Purchase intent with negative sentiment = churn risk
        if (analysis.primary_intent == IntentLabel.PURCHASE_INTENT and
            analysis.sentiment == SentimentLabel.NEGATIVE):
            analysis.primary_intent = IntentLabel.CHURN_RISK
            analysis.risk_flags.append("churn_risk")

        # Rule 4: Recalculate priority score
        analysis.priority_score = self._calculate_priority_score(analysis, mention)

        return analysis

    def _calculate_priority_score(self, analysis: AnalysisResult, mention) -> float:
        """Calculate composite priority score (0-1)."""
        weights = {
            "urgency": 0.35,
            "sentiment_severity": 0.25,
            "reach": 0.20,
            "engagement": 0.10,
            "risk": 0.10,
        }

        urgency_map = {
            UrgencyLevel.CRITICAL: 1.0,
            UrgencyLevel.HIGH: 0.75,
            UrgencyLevel.MEDIUM: 0.5,
            UrgencyLevel.LOW: 0.25,
            UrgencyLevel.NONE: 0.0,
        }

        sentiment_severity = abs(analysis.sentiment_score)
        reach_score = min(mention.author_followers / 1_000_000, 1.0)
        engagement_score = min(sum(mention.engagement.values()) / 50_000, 1.0)
        risk_score = min(len(analysis.risk_flags) * 0.3, 1.0)

        score = (
            weights["urgency"] * urgency_map[analysis.urgency] +
            weights["sentiment_severity"] * sentiment_severity +
            weights["reach"] * reach_score +
            weights["engagement"] * engagement_score +
            weights["risk"] * risk_score
        )

        return min(score, 1.0)

    def _calculate_reach_weight(self, mention) -> float:
        """Calculate reach weight based on author influence and engagement."""
        follower_weight = min(mention.author_followers / 1_000_000, 1.0)
        engagement_total = sum(mention.engagement.values())
        engagement_weight = min(engagement_total / 100_000, 1.0)
        return (follower_weight * 0.6) + (engagement_weight * 0.4)

    # Tool implementations
    async def _analyze_sentiment(self, text: str) -> str:
        """Tool: Deep sentiment analysis."""
        # Delegates to LLM via the agent
        return json.dumps({"sentiment": "neutral", "score": 0.0})

    async def _detect_emotions(self, text: str) -> str:
        """Tool: Emotion detection."""
        return json.dumps({"emotions": {}})

    async def _classify_intent(self, text: str) -> str:
        """Tool: Intent classification."""
        return json.dumps({"primary_intent": "inquiry"})

    async def _extract_entities(self, text: str) -> str:
        """Tool: Entity extraction."""
        return json.dumps({
            "products": [], "features": [],
            "competitors": [], "people": [],
        })

    async def _assess_urgency(self, text: str) -> str:
        """Tool: Urgency assessment."""
        return json.dumps({"urgency": "low", "score": 0.3})

    async def _calculate_brand_impact(self, text: str) -> str:
        """Tool: Brand impact calculation."""
        return json.dumps({"impact": 0.0})

    async def _check_risk_patterns(self, text: str) -> str:
        """Tool: Risk pattern detection."""
        return json.dumps({"risk_flags": [], "escalation": False})
```

### 3.4 Batch Analysis Pipeline

```python
# pipelines/analysis_pipeline.py
import asyncio
import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from agents.analysis_agent import AnalysisAgent
from models.analysis import AnalysisResult

logger = logging.getLogger(__name__)

class AnalysisPipeline:
    """Consumes mentions from Redis stream and produces analysis results."""

    def __init__(self, config: dict):
        self.config = config
        self.agent = AnalysisAgent(config)
        self.redis = aioredis.from_url(config.get("redis_url", "redis://localhost:6379"))
        self.batch_size = config.get("analysis_batch_size", 10)
        self.processing_group = "analysis_consumers"

    async def start(self):
        """Start consuming from the mentions stream."""
        await self._ensure_consumer_group()

        while True:
            try:
                messages = await self.redis.xreadgroup(
                    groupname=self.processing_group,
                    consumername="analysis-worker-1",
                    streams={"brand:mentions:stream": ">"},
                    count=self.batch_size,
                    block=5000,
                )

                if messages:
                    tasks = []
                    for stream_name, stream_messages in messages:
                        for msg_id, msg_data in stream_messages:
                            task = self._process_message(msg_id, msg_data)
                            tasks.append(task)

                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Acknowledge processed messages
                    for (stream_name, stream_messages), result in zip(messages, results):
                        if not isinstance(result, Exception):
                            for msg_id, _ in stream_messages:
                                await self.redis.xack(
                                    "brand:mentions:stream",
                                    self.processing_group,
                                    msg_id,
                                )

            except Exception as e:
                logger.error(f"Analysis pipeline error: {e}")
                await asyncio.sleep(5)

    async def _process_message(self, msg_id: str, msg_data: dict):
        """Process a single mention from the stream."""
        mention_data = json.loads(msg_data[b"data"].decode())
        mention = Mention(**mention_data)

        # Run analysis
        analysis = await self.agent.analyze(mention)

        # Store result
        await self._store_analysis(analysis)

        # Publish to next stream
        await self.redis.xadd(
            "brand:analysis:stream",
            {"data": json.dumps(analysis.__dict__, default=str)},
            maxlen=100000,
        )

        logger.info(f"Analyzed mention {mention.id}: {analysis.sentiment.value} "
                    f"(urgency: {analysis.urgency.value})")

    async def _store_analysis(self, analysis: AnalysisResult):
        """Persist analysis to PostgreSQL."""
        # Implementation using asyncpg or SQLAlchemy
        pass

    async def _ensure_consumer_group(self):
        """Create consumer group if it doesn't exist."""
        try:
            await self.redis.xgroup_create(
                "brand:mentions:stream",
                self.processing_group,
                id="0",
                mkstream=True,
            )
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise
```

---

## 4. Response Agent Implementation

### 4.1 Responsibilities

- Generate response drafts based on analysis results
- Route mentions to appropriate teams (support, PR, legal, executive)
- Determine response channel and tone
- Escalate critical issues
- Track response status and outcomes

### 4.2 Response Schema

```python
# models/response.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class ResponseChannel(str, Enum):
    TWITTER_REPLY = "twitter_reply"
    TWITTER_DM = "twitter_dm"
    REDDIT_REPLY = "reddit_reply"
    EMAIL = "email"
    PHONE = "phone"
    NO_RESPONSE = "no_response"

class ResponseTone(str, Enum):
    EMPATHETIC = "empathetic"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    APOLOGETIC = "apologetic"
    GRATEFUL = "grateful"
    INFORMATIVE = "informative"

class ResponseStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    REJECTED = "rejected"
    ESCALATED = "escalated"

class RoutingTeam(str, Enum):
    SUPPORT = "support"
    PR = "pr"
    LEGAL = "legal"
    EXECUTIVE = "executive"
    PRODUCT = "product"
    MARKETING = "marketing"
    COMMUNITY = "community"

@dataclass
class ResponseDecision:
    """Response decision and draft for a mention."""
    mention_id: str
    analysis_id: str
    decided_at: datetime

    # Decision
    should_respond: bool
    response_channel: ResponseChannel
    response_tone: ResponseTone
    routing_team: RoutingTeam
    routing_reason: str

    # Draft
    response_draft: Optional[str]
    response_template_used: Optional[str]

    # Status
    status: ResponseStatus
    approved_by: Optional[str]
    sent_at: Optional[datetime]

    # Escalation
    is_escalated: bool
    escalation_reason: Optional[str]
    escalation_target: Optional[str]

    # Metadata
    model_version: str
    processing_time_ms: int
```

### 4.3 Response Agent

```python
# agents/response_agent.py
import json
import logging
import time
from datetime import datetime, timezone

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

from models.analysis import AnalysisResult, SentimentLabel, IntentLabel, UrgencyLevel
from models.response import (
    ResponseDecision, ResponseChannel, ResponseTone,
    ResponseStatus, RoutingTeam,
)

logger = logging.getLogger(__name__)

RESPONSE_SYSTEM_PROMPT = """You are the Response Agent for a brand monitoring system.

Your role is to:
1. Decide whether a response is needed for each mention
2. Determine the appropriate response channel and tone
3. Route the mention to the correct team
4. Generate a response draft when appropriate
5. Escalate critical issues to the right stakeholders

Decision framework:
- COMPLAINT + negative sentiment → Respond with empathy, route to Support
- PRAISE + positive sentiment → Respond with gratitude, route to Community
- QUESTION → Respond informatively, route to Support
- SUGGESTION → Acknowledge and route to Product
- INQUIRY → Respond with information, route to Marketing
- CHURN_RISK → Escalate to Customer Success
- VIRAL_NEGATIVE → Escalate to PR + Executive
- INFLUENCER_COMPLAINT → Escalate to PR + Executive

Response guidelines:
- Match the tone of the original mention
- Be authentic and human, never robotic
- Acknowledge specific points from the original mention
- Include clear next steps or calls to action
- Never make promises the company can't keep
- Keep responses under 280 characters for Twitter
- For sensitive issues, draft but require human approval

Output: Structured JSON matching the ResponseDecision schema.
"""

class ResponseAgent:
    """LangChain DeepAgents-based response agent."""

    def __init__(self, config: dict):
        self.config = config
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        self._setup_agent()
        self._load_response_templates()

    def _setup_agent(self):
        """Create the LangChain response agent."""
        tools = [
            Tool(
                name="decide_response",
                func=self._decide_response,
                description="Decide whether and how to respond to a mention.",
            ),
            Tool(
                name="generate_draft",
                func=self._generate_draft,
                description="Generate a response draft based on the analysis.",
            ),
            Tool(
                name="route_to_team",
                func=self._route_to_team,
                description="Route the mention to the appropriate team.",
            ),
            Tool(
                name="escalate",
                func=self._escalate,
                description="Escalate critical issues to stakeholders.",
            ),
            Tool(
                name="check_sensitivity",
                func=self._check_sensitivity,
                description="Check if content requires legal/executive review.",
            ),
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", RESPONSE_SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        langchain_agent = create_openai_functions_agent(self.llm, tools, prompt)
        self.executor = AgentExecutor(
            agent=langchain_agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )

    def _load_response_templates(self):
        """Load response templates for common scenarios."""
        self.templates = {
            "complaint_acknowledgment": {
                "tone": ResponseTone.EMPATHETIC,
                "template": "Hi {author}, we're really sorry to hear about your experience. "
                           "We'd like to make this right. Could you share more details via DM?",
                "channel": ResponseChannel.TWITTER_REPLY,
                "team": RoutingTeam.SUPPORT,
            },
            "praise_thanks": {
                "tone": ResponseTone.GRATEFUL,
                "template": "Thank you so much, {author}! 🎉 We're thrilled you're enjoying it. "
                           "Your support means the world to our team!",
                "channel": ResponseChannel.TWITTER_REPLY,
                "team": RoutingTeam.COMMUNITY,
            },
            "question_answer": {
                "tone": ResponseTone.INFORMATIVE,
                "template": "Hi {author}! Great question. {answer} "
                           "Let us know if you need anything else!",
                "channel": ResponseChannel.TWITTER_REPLY,
                "team": RoutingTeam.SUPPORT,
            },
            "suggestion_acknowledgment": {
                "tone": ResponseTone.PROFESSIONAL,
                "template": "Hi {author}, thank you for the suggestion! We've shared it with our "
                           "product team. We're always looking to improve.",
                "channel": ResponseChannel.TWITTER_REPLY,
                "team": RoutingTeam.PRODUCT,
            },
            "churn_risk": {
                "tone": ResponseTone.EMPATHETIC,
                "template": "Hi {author}, we're sorry to hear you're considering leaving. "
                           "A team member will reach out to see how we can help.",
                "channel": ResponseChannel.EMAIL,
                "team": RoutingTeam.SUPPORT,
            },
            "viral_negative": {
                "tone": ResponseTone.PROFESSIONAL,
                "template": "We're aware of the concerns raised and take them seriously. "
                           "We're investigating and will share an update shortly.",
                "channel": ResponseChannel.TWITTER_REPLY,
                "team": RoutingTeam.PR,
            },
        }

    async def decide(self, mention, analysis: AnalysisResult) -> ResponseDecision:
        """Make response decision for a mention."""
        start_time = time.time()

        context = self._build_decision_context(mention, analysis)

        result = await self.executor.ainvoke({"input": context})

        decision = self._parse_decision(result, mention, analysis, start_time)
        decision = self._apply_routing_rules(decision, mention, analysis)

        return decision

    def _build_decision_context(self, mention, analysis: AnalysisResult) -> str:
        """Build context for response decision."""
        return json.dumps({
            "mention": {
                "content": mention.content,
                "source": mention.source,
                "author": mention.author,
                "author_followers": mention.author_followers,
                "engagement": mention.engagement,
            },
            "analysis": {
                "sentiment": analysis.sentiment.value,
                "sentiment_score": analysis.sentiment_score,
                "primary_intent": analysis.primary_intent.value,
                "urgency": analysis.urgency.value,
                "urgency_score": analysis.urgency_score,
                "risk_flags": analysis.risk_flags,
                "escalation_recommended": analysis.escalation_recommended,
                "brand_health_impact": analysis.brand_health_impact,
            },
            "available_templates": list(self.templates.keys()),
        }, default=str)

    def _parse_decision(self, result: dict, mention, analysis: AnalysisResult,
                        start_time: float) -> ResponseDecision:
        """Parse agent output into ResponseDecision."""
        output = result.get("output", result)
        if isinstance(output, str):
            output = json.loads(output)

        processing_time = int((time.time() - start_time) * 1000)

        return ResponseDecision(
            mention_id=mention.id,
            analysis_id=analysis.mention_id,
            decided_at=datetime.now(timezone.utc),
            should_respond=bool(output.get("should_respond", True)),
            response_channel=ResponseChannel(output.get("response_channel", "twitter_reply")),
            response_tone=ResponseTone(output.get("response_tone", "professional")),
            routing_team=RoutingTeam(output.get("routing_team", "support")),
            routing_reason=output.get("routing_reason", ""),
            response_draft=output.get("response_draft"),
            response_template_used=output.get("template_used"),
            status=ResponseStatus(output.get("status", "draft")),
            approved_by=None,
            sent_at=None,
            is_escalated=bool(output.get("is_escalated", False)),
            escalation_reason=output.get("escalation_reason"),
            escalation_target=output.get("escalation_target"),
            model_version="gpt-4o-2024-08-06",
            processing_time_ms=processing_time,
        )

    def _apply_routing_rules(self, decision: ResponseDecision, mention,
                             analysis: AnalysisResult) -> ResponseDecision:
        """Apply business routing rules on top of agent decision."""
        # Rule 1: Critical urgency always escalates
        if analysis.urgency == UrgencyLevel.CRITICAL:
            decision.is_escalated = True
            decision.escalation_reason = "Critical urgency level"
            decision.escalation_target = "executive-team"
            decision.status = ResponseStatus.ESCALATED

        # Rule 2: Viral negative content goes to PR
        if "viral_negative" in analysis.risk_flags:
            decision.routing_team = RoutingTeam.PR
            decision.is_escalated = True
            decision.escalation_target = "pr-director"

        # Rule 3: Influencer complaints go to PR
        if "influencer_complaint" in analysis.risk_flags:
            decision.routing_team = RoutingTeam.PR
            decision.is_escalated = True
            decision.escalation_target = "pr-director"

        # Rule 4: Legal risk detection
        legal_keywords = ["lawsuit", "lawyer", "legal action", "sue", "attorney"]
        if any(kw in mention.content.lower() for kw in legal_keywords):
            decision.routing_team = RoutingTeam.LEGAL
            decision.is_escalated = True
            decision.escalation_target = "legal-team"

        # Rule 5: No response for neutral/positive with low engagement
        if (analysis.sentiment in (SentimentLabel.POSITIVE, SentimentLabel.NEUTRAL) and
            analysis.urgency == UrgencyLevel.NONE and
            sum(mention.engagement.values()) < 10):
            decision.should_respond = False
            decision.response_channel = ResponseChannel.NO_RESPONSE

        # Rule 6: High-value customers get personal outreach
        if mention.author_followers > 500_000 and analysis.sentiment == SentimentLabel.NEGATIVE:
            decision.response_channel = ResponseChannel.EMAIL
            decision.routing_team = RoutingTeam.EXECUTIVE

        return decision

    # Tool implementations
    async def _decide_response(self, context: str) -> str:
        """Tool: Decide response strategy."""
        return json.dumps({"should_respond": True})

    async def _generate_draft(self, context: str) -> str:
        """Tool: Generate response draft."""
        return json.dumps({"response_draft": ""})

    async def _route_to_team(self, context: str) -> str:
        """Tool: Route to team."""
        return json.dumps({"routing_team": "support"})

    async def _escalate(self, context: str) -> str:
        """Tool: Escalate issue."""
        return json.dumps({"escalated": False})

    async def _check_sensitivity(self, context: str) -> str:
        """Tool: Check content sensitivity."""
        return json.dumps({"sensitive": False})
```

---

## 5. Reporting Agent Implementation

### 5.1 Responsibilities

- Generate daily/weekly/monthly brand health reports
- Create executive summaries with key metrics
- Produce trend analysis and anomaly detection
- Distribute reports via email, Slack, and dashboard
- Generate ad-hoc reports on demand

### 5.2 Report Types

```python
# models/report.py
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
from typing import Optional

class ReportType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    AD_HOC = "ad_hoc"
    CRISIS = "crisis"
    COMPETITIVE = "competitive"

class ReportFormat(str, Enum):
    PDF = "pdf"
    HTML = "html"
    SLACK = "slack"
    EMAIL = "email"
    DASHBOARD = "dashboard"

@dataclass
class BrandHealthMetrics:
    """Aggregated brand health metrics for a reporting period."""
    period_start: date
    period_end: date

    # Volume metrics
    total_mentions: int
    mentions_by_source: dict[str, int]
    mentions_change_pct: float       # vs previous period

    # Sentiment metrics
    sentiment_distribution: dict[str, float]  # {positive: 0.45, negative: 0.25, ...}
    net_sentiment_score: float       # -1.0 to 1.0
    sentiment_change_pct: float

    # Engagement metrics
    total_engagement: int
    avg_engagement_per_mention: float
    reach_estimate: int

    # Share of voice
    brand_mentions: int
    competitor_mentions: dict[str, int]
    share_of_voice: float            # 0.0 to 1.0

    # Topic analysis
    top_topics: list[dict]           # [{topic, count, sentiment}]
    emerging_topics: list[dict]
    declining_topics: list[dict]

    # Response metrics
    response_rate: float
    avg_response_time_minutes: float
    resolution_rate: float

    # Risk metrics
    crisis_mentions: int
    escalated_mentions: int
    resolved_crises: int

    # Brand health score (composite)
    brand_health_score: float        # 0-100
    health_score_change: float       # vs previous period

@dataclass
class Report:
    """Generated report."""
    id: str
    report_type: ReportType
    format: ReportFormat
    generated_at: datetime
    metrics: BrandHealthMetrics
    summary: str
    key_findings: list[str]
    recommendations: list[str]
    charts_data: dict                # Data for visualization
    raw_data: dict                   # Full underlying data
```

### 5.3 Reporting Agent

```python
# agents/reporting_agent.py
import json
import logging
import uuid
from datetime import datetime, timezone, timedelta

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

from models.report import Report, ReportType, ReportFormat, BrandHealthMetrics

logger = logging.getLogger(__name__)

REPORTING_SYSTEM_PROMPT = """You are the Reporting Agent for a brand monitoring system.

Your role is to:
1. Aggregate brand monitoring data into meaningful reports
2. Identify trends, patterns, and anomalies
3. Generate executive summaries with actionable insights
4. Create data visualizations and charts
5. Distribute reports to stakeholders

Report types:
- DAILY: Brief overview of last 24 hours, key metrics, urgent items
- WEEKLY: Comprehensive analysis with trends, comparisons, recommendations
- MONTHLY: Strategic overview with deep analysis and forecasting
- AD_HOC: On-demand reports for specific queries or time periods
- CRISIS: Real-time crisis monitoring and stakeholder updates
- COMPETITIVE: Brand vs competitor analysis

Guidelines:
- Lead with the most important insights
- Use clear, non-technical language for executive summaries
- Include specific numbers and percentages
- Highlight significant changes from previous periods
- Provide actionable recommendations
- Flag potential risks and opportunities

Output: Structured report with metrics, summary, findings, and recommendations.
"""

class ReportingAgent:
    """LangChain DeepAgents-based reporting agent."""

    def __init__(self, config: dict):
        self.config = config
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )
        self._setup_agent()

    def _setup_agent(self):
        """Create the LangChain reporting agent."""
        tools = [
            Tool(
                name="aggregate_metrics",
                func=self._aggregate_metrics,
                description="Aggregate raw metrics for the reporting period.",
            ),
            Tool(
                name="detect_trends",
                func=self._detect_trends,
                description="Detect trends and patterns in the data.",
            ),
            Tool(
                name="generate_summary",
                func=self._generate_summary,
                description="Generate an executive summary from metrics.",
            ),
            Tool(
                name="create_recommendations",
                func=self._create_recommendations,
                description="Create actionable recommendations based on findings.",
            ),
            Tool(
                name="detect_anomalies",
                func=self._detect_anomalies,
                description="Detect anomalies and unusual patterns.",
            ),
            Tool(
                name="compare_periods",
                func=self._compare_periods,
                description="Compare current period with previous periods.",
            ),
            Tool(
                name="generate_chart_data",
                func=self._generate_chart_data,
                description="Generate data structures for charts and visualizations.",
            ),
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", REPORTING_SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        langchain_agent = create_openai_functions_agent(self.llm, tools, prompt)
        self.executor = AgentExecutor(
            agent=langchain_agent,
            tools=tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=True,
        )

    async def generate_report(self, report_type: ReportType,
                             period_start: date, period_end: date,
                             format: ReportFormat = ReportFormat.PDF) -> Report:
        """Generate a complete report for the specified period."""
        context = json.dumps({
            "report_type": report_type.value,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "format": format.value,
            "brand_keywords": self.config.get("brand_keywords", []),
            "competitors": self.config.get("competitors", []),
        })

        result = await self.executor.ainvoke({"input": context})

        report = self._parse_report(result, report_type, format, period_start, period_end)
        return report

    async def generate_daily_report(self) -> Report:
        """Generate a daily report for the last 24 hours."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        return await self.generate_report(ReportType.DAILY, yesterday, today)

    async def generate_weekly_report(self) -> Report:
        """Generate a weekly report for the last 7 days."""
        today = date.today()
        week_ago = today - timedelta(days=7)
        return await self.generate_report(ReportType.WEEKLY, week_ago, today)

    async def generate_monthly_report(self) -> Report:
        """Generate a monthly report for the last 30 days."""
        today = date.today()
        month_ago = today - timedelta(days=30)
        return await self.generate_report(ReportType.MONTHLY, month_ago, today)

    async def generate_crisis_report(self, crisis_id: str) -> Report:
        """Generate a crisis-specific report."""
        return await self.generate_report(ReportType.CRISIS, date.today(), date.today())

    def _parse_report(self, result: dict, report_type: ReportType,
                     format: ReportFormat, period_start: date,
                     period_end: date) -> Report:
        """Parse agent output into Report."""
        output = result.get("output", result)
        if isinstance(output, str):
            output = json.loads(output)

        return Report(
            id=str(uuid.uuid4()),
            report_type=report_type,
            format=format,
            generated_at=datetime.now(timezone.utc),
            metrics=BrandHealthMetrics(
                period_start=period_start,
                period_end=period_end,
                total_mentions=output.get("total_mentions", 0),
                mentions_by_source=output.get("mentions_by_source", {}),
                mentions_change_pct=output.get("mentions_change_pct", 0.0),
                sentiment_distribution=output.get("sentiment_distribution", {}),
                net_sentiment_score=output.get("net_sentiment_score", 0.0),
                sentiment_change_pct=output.get("sentiment_change_pct", 0.0),
                total_engagement=output.get("total_engagement", 0),
                avg_engagement_per_mention=output.get("avg_engagement_per_mention", 0.0),
                reach_estimate=output.get("reach_estimate", 0),
                brand_mentions=output.get("brand_mentions", 0),
                competitor_mentions=output.get("competitor_mentions", {}),
                share_of_voice=output.get("share_of_voice", 0.0),
                top_topics=output.get("top_topics", []),
                emerging_topics=output.get("emerging_topics", []),
                declining_topics=output.get("declining_topics", []),
                response_rate=output.get("response_rate", 0.0),
                avg_response_time_minutes=output.get("avg_response_time_minutes", 0.0),
                resolution_rate=output.get("resolution_rate", 0.0),
                crisis_mentions=output.get("crisis_mentions", 0),
                escalated_mentions=output.get("escalated_mentions", 0),
                resolved_crises=output.get("resolved_crises", 0),
                brand_health_score=output.get("brand_health_score", 50.0),
                health_score_change=output.get("health_score_change", 0.0),
            ),
            summary=output.get("summary", ""),
            key_findings=output.get("key_findings", []),
            recommendations=output.get("recommendations", []),
            charts_data=output.get("charts_data", {}),
            raw_data=output.get("raw_data", {}),
        )

    # Tool implementations
    async def _aggregate_metrics(self, period: str) -> str:
        """Tool: Aggregate metrics from database."""
        return json.dumps({})

    async def _detect_trends(self, data: str) -> str:
        """Tool: Detect trends in data."""
        return json.dumps({"trends": []})

    async def _generate_summary(self, metrics: str) -> str:
        """Tool: Generate executive summary."""
        return json.dumps({"summary": ""})

    async def _create_recommendations(self, findings: str) -> str:
        """Tool: Create recommendations."""
        return json.dumps({"recommendations": []})

    async def _detect_anomalies(self, data: str) -> str:
        """Tool: Detect anomalies."""
        return json.dumps({"anomalies": []})

    async def _compare_periods(self, current: str, previous: str) -> str:
        """Tool: Compare periods."""
        return json.dumps({})

    async def _generate_chart_data(self, metrics: str) -> str:
        """Tool: Generate chart data."""
        return json.dumps({})
```

### 5.4 Report Distribution

```python
# services/report_distribution.py
import logging
from datetime import datetime

import aiohttp
from jinja2 import Environment, FileSystemLoader

from models.report import Report, ReportFormat

logger = logging.getLogger(__name__)

class ReportDistributionService:
    """Distributes reports to various channels."""

    def __init__(self, config: dict):
        self.config = config
        self.jinja_env = Environment(
            loader=FileSystemLoader("templates/reports/")
        )

    async def distribute(self, report: Report, channels: list[str]):
        """Distribute report to specified channels."""
        for channel in channels:
            try:
                if channel == "email":
                    await self._send_email(report)
                elif channel == "slack":
                    await self._send_slack(report)
                elif channel == "dashboard":
                    await self._update_dashboard(report)
                elif channel == "pdf":
                    await self._generate_pdf(report)
            except Exception as e:
                logger.error(f"Failed to distribute to {channel}: {e}")

    async def _send_email(self, report: Report):
        """Send report via email."""
        template = self.jinja_env.get_template("email_report.html")
        html_content = template.render(report=report)
        # Send via email service (SendGrid, SES, etc.)
        logger.info(f"Email report sent: {report.id}")

    async def _send_slack(self, report: Report):
        """Send report summary to Slack."""
        webhook_url = self.config.get("slack_webhook_url")
        if not webhook_url:
            return

        payload = {
            "text": f"Brand Monitoring Report - {report.report_type.value}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Brand Health Score: {report.metrics.brand_health_score:.1f}/100*",
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": report.summary[:3000],  # Slack limit
                    }
                },
            ]
        }

        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json=payload)

    async def _update_dashboard(self, report: Report):
        """Update real-time dashboard."""
        # Push to WebSocket or update dashboard API
        pass

    async def _generate_pdf(self, report: Report):
        """Generate PDF report."""
        template = self.jinja_env.get_template("pdf_report.html")
        html_content = template.render(report=report)
        # Use WeasyPrint or similar to generate PDF
        logger.info(f"PDF report generated: {report.id}")
```

---

## 6. Performance Analytics Agent Implementation

### 6.1 Responsibilities

- Monitor all agent performance metrics
- Track system health and latency
- Calculate cost per mention processed
- Detect model drift and quality degradation
- Generate optimization recommendations
- Provide real-time dashboards

### 6.2 Metrics Schema

```python
# models/performance.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class MetricType(str, Enum):
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ACCURACY = "accuracy"
    COST = "cost"
    AVAILABILITY = "availability"
    ERROR_RATE = "error_rate"

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class AgentMetrics:
    """Performance metrics for a single agent."""
    agent_name: str
    timestamp: datetime

    # Latency
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

    # Throughput
    mentions_per_minute: float
    mentions_per_hour: float

    # Quality
    accuracy_score: float           # 0.0 to 1.0
    confidence_avg: float
    error_rate: float               # 0.0 to 1.0

    # Cost
    total_cost_usd: float
    cost_per_mention_usd: float
    tokens_consumed: int

    # Availability
    uptime_pct: float
    failed_requests: int
    total_requests: int

@dataclass
class SystemHealth:
    """Overall system health snapshot."""
    timestamp: datetime
    overall_status: str             # healthy, degraded, down
    agent_metrics: dict[str, AgentMetrics]
    active_alerts: list[dict]
    recommendations: list[str]
```

### 6.3 Performance Analytics Agent

```python
# agents/performance_analytics_agent.py
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

from models.performance import AgentMetrics, SystemHealth, MetricType, AlertSeverity

logger = logging.getLogger(__name__)

PERFORMANCE_SYSTEM_PROMPT = """You are the Performance Analytics Agent for a brand monitoring system.

Your role is to:
1. Monitor the performance of all agents in the system
2. Track latency, throughput, accuracy, cost, and availability metrics
3. Detect anomalies and performance degradation
4. Generate optimization recommendations
5. Create alerts for critical issues
6. Provide real-time system health dashboards

Key metrics to track:
- LATENCY: Response times for each agent (p50, p95, p99)
- THROUGHPUT: Mentions processed per minute/hour
- ACCURACY: Classification accuracy, sentiment accuracy
- COST: API costs per mention, total system cost
- AVAILABILITY: Uptime, error rates, failed requests

Alert thresholds:
- p95 latency > 10s → WARNING
- p95 latency > 30s → CRITICAL
- Error rate > 5% → WARNING
- Error rate > 10% → CRITICAL
- Cost per mention > $0.05 → WARNING
- Cost per mention > $0.10 → CRITICAL

Output: Structured metrics, alerts, and recommendations.
"""

class PerformanceAnalyticsAgent:
    """LangChain DeepAgents-based performance analytics agent."""

    def __init__(self, config: dict):
        self.config = config
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        self._setup_agent()
        self.metrics_store = defaultdict(list)  # In-memory; use Prometheus in production

    def _setup_agent(self):
        """Create the LangChain performance analytics agent."""
        tools = [
            Tool(
                name="collect_metrics",
                func=self._collect_metrics,
                description="Collect performance metrics from all agents.",
            ),
            Tool(
                name="detect_anomalies",
                func=self._detect_anomalies,
                description="Detect performance anomalies and degradation.",
            ),
            Tool(
                name="generate_alerts",
                func=self._generate_alerts,
                description="Generate alerts for threshold violations.",
            ),
            Tool(
                name="optimize_costs",
                func=self._optimize_costs,
                description="Recommend cost optimization strategies.",
            ),
            Tool(
                name="forecast_load",
                func=self._forecast_load,
                description="Forecast future system load and capacity needs.",
            ),
            Tool(
                name="benchmark_accuracy",
                func=self._benchmark_accuracy,
                description="Benchmark model accuracy against ground truth.",
            ),
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", PERFORMANCE_SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        langchain_agent = create_openai_functions_agent(self.llm, tools, prompt)
        self.executor = AgentExecutor(
            agent=langchain_agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )

    async def collect_system_health(self) -> SystemHealth:
        """Collect comprehensive system health snapshot."""
        context = json.dumps({
            "agents": ["listening", "analysis", "response", "reporting"],
            "time_window_minutes": 60,
            "alert_thresholds": {
                "p95_latency_warning_ms": 10000,
                "p95_latency_critical_ms": 30000,
                "error_rate_warning": 0.05,
                "error_rate_critical": 0.10,
                "cost_per_mention_warning_usd": 0.05,
                "cost_per_mention_critical_usd": 0.10,
            },
        })

        result = await self.executor.ainvoke({"input": context})
        return self._parse_health_snapshot(result)

    async def track_agent_metric(self, agent_name: str, metric_type: MetricType,
                                  value: float, metadata: dict = None):
        """Track a single metric for an agent."""
        metric = {
            "agent_name": agent_name,
            "metric_type": metric_type.value,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self.metrics_store[agent_name].append(metric)

        # Check thresholds
        await self._check_thresholds(agent_name, metric_type, value)

    async def generate_optimization_recommendations(self) -> list[str]:
        """Generate system optimization recommendations."""
        context = json.dumps({
            "metrics": dict(self.metrics_store),
            "bottlenecks": self._identify_bottlenecks(),
            "cost_analysis": self._analyze_costs(),
        })

        result = await self.executor.ainvoke({
            "input": f"Analyze these metrics and provide optimization recommendations: {context}"
        })

        output = result.get("output", result)
        if isinstance(output, str):
            output = json.loads(output)

        return output.get("recommendations", [])

    def _parse_health_snapshot(self, result: dict) -> SystemHealth:
        """Parse agent output into SystemHealth."""
        output = result.get("output", result)
        if isinstance(output, str):
            output = json.loads(output)

        agent_metrics = {}
        for agent_name, metrics_data in output.get("agent_metrics", {}).items():
            agent_metrics[agent_name] = AgentMetrics(
                agent_name=agent_name,
                timestamp=datetime.now(timezone.utc),
                avg_latency_ms=metrics_data.get("avg_latency_ms", 0),
                p50_latency_ms=metrics_data.get("p50_latency_ms", 0),
                p95_latency_ms=metrics_data.get("p95_latency_ms", 0),
                p99_latency_ms=metrics_data.get("p99_latency_ms", 0),
                mentions_per_minute=metrics_data.get("mentions_per_minute", 0),
                mentions_per_hour=metrics_data.get("mentions_per_hour", 0),
                accuracy_score=metrics_data.get("accuracy_score", 0),
                confidence_avg=metrics_data.get("confidence_avg", 0),
                error_rate=metrics_data.get("error_rate", 0),
                total_cost_usd=metrics_data.get("total_cost_usd", 0),
                cost_per_mention_usd=metrics_data.get("cost_per_mention_usd", 0),
                tokens_consumed=metrics_data.get("tokens_consumed", 0),
                uptime_pct=metrics_data.get("uptime_pct", 100),
                failed_requests=metrics_data.get("failed_requests", 0),
                total_requests=metrics_data.get("total_requests", 0),
            )

        return SystemHealth(
            timestamp=datetime.now(timezone.utc),
            overall_status=output.get("overall_status", "healthy"),
            agent_metrics=agent_metrics,
            active_alerts=output.get("active_alerts", []),
            recommendations=output.get("recommendations", []),
        )

    def _identify_bottlenecks(self) -> list[dict]:
        """Identify system bottlenecks from metrics."""
        bottlenecks = []
        for agent_name, metrics in self.metrics_store.items():
            if not metrics:
                continue
            recent = metrics[-100:]  # Last 100 data points
            avg_latency = sum(m["value"] for m in recent if m["metric_type"] == "latency") / max(len(recent), 1)
            if avg_latency > 5000:  # 5 seconds
                bottlenecks.append({
                    "agent": agent_name,
                    "issue": "high_latency",
                    "avg_latency_ms": avg_latency,
                })
        return bottlenecks

    def _analyze_costs(self) -> dict:
        """Analyze cost patterns."""
        total_cost = 0
        cost_by_agent = defaultdict(float)
        for agent_name, metrics in self.metrics_store.items():
            for m in metrics:
                if m["metric_type"] == "cost":
                    cost_by_agent[agent_name] += m["value"]
                    total_cost += m["value"]
        return {
            "total_cost_usd": total_cost,
            "cost_by_agent": dict(cost_by_agent),
        }

    async def _check_thresholds(self, agent_name: str, metric_type: MetricType, value: float):
        """Check if a metric violates thresholds."""
        thresholds = {
            MetricType.LATENCY: {"warning": 10000, "critical": 30000},
            MetricType.ERROR_RATE: {"warning": 0.05, "critical": 0.10},
            MetricType.COST: {"warning": 0.05, "critical": 0.10},
        }

        if metric_type not in thresholds:
            return

        threshold = thresholds[metric_type]
        if value > threshold["critical"]:
            logger.critical(f"CRITICAL: {agent_name} {metric_type.value} = {value}")
        elif value > threshold["warning"]:
            logger.warning(f"WARNING: {agent_name} {metric_type.value} = {value}")

    # Tool implementations
    async def _collect_metrics(self, agent_name: str) -> str:
        """Tool: Collect metrics for an agent."""
        metrics = self.metrics_store.get(agent_name, [])
        return json.dumps({"metrics": metrics[-100:]})

    async def _detect_anomalies(self, metrics_data: str) -> str:
        """Tool: Detect anomalies."""
        return json.dumps({"anomalies": []})

    async def _generate_alerts(self, metrics_data: str) -> str:
        """Tool: Generate alerts."""
        return json.dumps({"alerts": []})

    async def _optimize_costs(self, cost_data: str) -> str:
        """Tool: Optimize costs."""
        return json.dumps({"recommendations": []})

    async def _forecast_load(self, historical_data: str) -> str:
        """Tool: Forecast load."""
        return json.dumps({"forecast": {}})

    async def _benchmark_accuracy(self, evaluation_data: str) -> str:
        """Tool: Benchmark accuracy."""
        return json.dumps({"accuracy": 0.0})
```

---

## 7. Code Examples and Snippets

### 7.1 Project Structure

```
brand-monitoring/
├── agents/
│   ├── __init__.py
│   ├── listening_agent.py
│   ├── analysis_agent.py
│   ├── response_agent.py
│   ├── reporting_agent.py
│   └── performance_analytics_agent.py
├── connectors/
│   ├── __init__.py
│   ├── base.py
│   ├── twitter_connector.py
│   ├── reddit_connector.py
│   └── news_connector.py
├── models/
│   ├── __init__.py
│   ├── analysis.py
│   ├── response.py
│   ├── report.py
│   └── performance.py
├── pipelines/
│   ├── __init__.py
│   ├── analysis_pipeline.py
│   └── response_pipeline.py
├── services/
│   ├── __init__.py
│   ├── deduplication.py
│   ├── report_distribution.py
│   └── notification.py
├── templates/
│   └── reports/
│       ├── email_report.html
│       └── pdf_report.html
├── tests/
│   ├── __init__.py
│   ├── test_listening_agent.py
│   ├── test_analysis_agent.py
│   ├── test_response_agent.py
│   ├── test_reporting_agent.py
│   └── test_performance_agent.py
├── config/
│   ├── default.yaml
│   └── production.yaml
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── main.py
```

### 7.2 Configuration

```yaml
# config/default.yaml
brand:
  name: "YourBrand"
  keywords:
    - "YourBrand"
    - "@YourBrand"
    - "#YourBrand"
    - "Your Brand Name"
  competitors:
    - "CompetitorA"
    - "CompetitorB"

connectors:
  twitter:
    bearer_token: "${TWITTER_BEARER_TOKEN}"
    keywords: ["YourBrand", "@YourBrand"]
    rate_limit: 100
    window: 60
  reddit:
    client_id: "${REDDIT_CLIENT_ID}"
    client_secret: "${REDDIT_CLIENT_SECRET}"
    subreddits: ["yourbrand", "technology"]
    keywords: ["YourBrand"]
  news:
    feeds:
      - "https://feeds.bbci.co.uk/news/technology/rss.xml"
      - "https://techcrunch.com/feed/"
    news_api_key: "${NEWS_API_KEY}"
    keywords: ["YourBrand"]
    poll_interval: 300

agents:
  listening:
    model: "gpt-4o-mini"
    temperature: 0
    max_tokens: 4096
  analysis:
    model: "gpt-4o"
    temperature: 0.1
    max_tokens: 4096
  response:
    model: "gpt-4o"
    temperature: 0.3
    max_tokens: 4096
  reporting:
    model: "gpt-4o"
    temperature: 0.2
    max_tokens: 8192
  performance:
    model: "gpt-4o-mini"
    temperature: 0.1
    max_tokens: 4096

infrastructure:
  redis:
    url: "${REDIS_URL}"
  pinecone:
    api_key: "${PINECONE_API_KEY}"
    environment: "us-east-1"
    index_name: "brand-mentions"
  postgresql:
    url: "${DATABASE_URL}"
  openai:
    api_key: "${OPENAI_API_KEY}"

monitoring:
  prometheus_port: 9090
  grafana_port: 3000
  alert_webhook: "${SLACK_WEBHOOK_URL}"
```

### 7.3 Main Application Entry Point

```python
# main.py
import asyncio
import logging
import os

import yaml
from dotenv import load_dotenv

from agents.listening_agent import ListeningAgent
from agents.analysis_agent import AnalysisAgent
from agents.response_agent import ResponseAgent
from agents.reporting_agent import ReportingAgent
from agents.performance_analytics_agent import PerformanceAnalyticsAgent
from pipelines.analysis_pipeline import AnalysisPipeline

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(path: str = "config/default.yaml") -> dict:
    with open(path) as f:
        config = yaml.safe_load(f)
    # Resolve environment variables
    return resolve_env_vars(config)


def resolve_env_vars(obj):
    if isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        return os.getenv(obj[2:-1], "")
    return obj


async def main():
    config = load_config()

    # Initialize agents
    listening_agent = ListeningAgent(config)
    analysis_agent = AnalysisAgent(config)
    response_agent = ResponseAgent(config)
    reporting_agent = ReportingAgent(config)
    performance_agent = PerformanceAnalyticsAgent(config)

    # Initialize pipelines
    analysis_pipeline = AnalysisPipeline(config)

    # Start all components
    tasks = [
        asyncio.create_task(listening_agent.start()),
        asyncio.create_task(analysis_pipeline.start()),
        asyncio.create_task(scheduled_reports(reporting_agent)),
        asyncio.create_task(monitor_performance(performance_agent)),
    ]

    await asyncio.gather(*tasks)


async def scheduled_reports(reporting_agent: ReportingAgent):
    """Generate reports on a schedule."""
    while True:
        now = datetime.now()
        # Daily report at 8 AM
        if now.hour == 8 and now.minute == 0:
            report = await reporting_agent.generate_daily_report()
            logger.info(f"Daily report generated: {report.id}")
        # Weekly report on Monday at 9 AM
        if now.weekday() == 0 and now.hour == 9 and now.minute == 0:
            report = await reporting_agent.generate_weekly_report()
            logger.info(f"Weekly report generated: {report.id}")
        # Monthly report on 1st of month at 10 AM
        if now.day == 1 and now.hour == 10 and now.minute == 0:
            report = await reporting_agent.generate_monthly_report()
            logger.info(f"Monthly report generated: {report.id}")
        await asyncio.sleep(60)


async def monitor_performance(performance_agent: PerformanceAnalyticsAgent):
    """Continuously monitor system performance."""
    while True:
        health = await performance_agent.collect_system_health()
        logger.info(f"System health: {health.overall_status}")
        for alert in health.active_alerts:
            logger.warning(f"Active alert: {alert}")
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
```

### 7.4 Docker Compose

```yaml
# docker-compose.yml
version: "3.9"

services:
  brand-monitoring:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - redis
      - postgres
    volumes:
      - ./config:/app/config
      - ./templates:/app/templates

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: brand_monitoring
      POSTGRES_USER: brand_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  redis_data:
  postgres_data:
  grafana_data:
```

### 7.5 Requirements

```txt
# requirements.txt
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
openai>=1.0.0
tweepy>=4.14.0
asyncpraw>=7.7.0
feedparser>=6.0.0
httpx>=0.25.0
redis>=5.0.0
pinecone-client>=3.0.0
asyncpg>=0.29.0
sqlalchemy>=2.0.0
celery>=5.3.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0
pyyaml>=6.0.0
python-dotenv>=1.0.0
jinja2>=3.1.0
aiohttp>=3.9.0
prometheus-client>=0.19.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
```

---

## 8. Testing Strategy

### 8.1 Test Pyramid

```
                    ┌──────────┐
                    │   E2E    │  ← Full pipeline integration tests
                    │  (10%)   │
                   ┌┴──────────┴┐
                   │ Integration │  ← Agent + service integration
                   │   (20%)     │
                  ┌┴─────────────┴┐
                  │    Unit Tests   │  ← Individual agent/tool tests
                  │     (70%)       │
                  └─────────────────┘
```

### 8.2 Unit Tests

```python
# tests/test_listening_agent.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from agents.listening_agent import ListeningAgent
from connectors.base import Mention


@pytest_asyncio.fixture
async def listening_agent():
    config = {
        "pinecone_api_key": "test-key",
        "redis_url": "redis://localhost:6379",
        "connectors": {
            "twitter": {
                "bearer_token": "test-token",
                "keywords": ["TestBrand"],
            }
        },
    }
    agent = ListeningAgent(config)
    yield agent


@pytest.fixture
def sample_mention():
    return Mention(
        id="test-uuid-1",
        source="twitter",
        source_id="12345678",
        content="I love TestBrand's new product! Amazing quality.",
        author="testuser",
        author_id="user123",
        author_followers=5000,
        url="https://twitter.com/testuser/status/12345678",
        published_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc),
        language="en",
        engagement={"likes": 10, "retweets": 2, "replies": 1},
        media_urls=[],
        parent_id=None,
        metadata={},
        brand_keywords_matched=["TestBrand"],
    )


class TestListeningAgent:
    @pytest.mark.asyncio
    async def test_validate_mention_valid(self, listening_agent, sample_mention):
        """Test that a valid mention passes validation."""
        result = await listening_agent._validate_mention(
            str(sample_mention.__dict__)
        )
        data = json.loads(result)
        assert data["valid"] is True
        assert len(data["issues"]) == 0

    @pytest.mark.asyncio
    async def test_validate_mention_short_content(self, listening_agent):
        """Test that short content is flagged."""
        result = await listening_agent._validate_mention(
            json.dumps({"content": "Hi", "author": "user", "published_at": "2024-01-01"})
        )
        data = json.loads(result)
        assert data["valid"] is False
        assert "Content too short" in data["issues"]

    @pytest.mark.asyncio
    async def test_exact_duplicate_detection(self, listening_agent, sample_mention):
        """Test exact duplicate detection via content hash."""
        hash1 = listening_agent.dedup.content_hash(sample_mention.content)
        hash2 = listening_agent.dedup.content_hash(sample_mention.content)
        assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_influence_score_calculation(self, listening_agent):
        """Test influence score calculation for different follower counts."""
        assert listening_agent._calculate_influence({"author_followers": 2_000_000}) == 100.0
        assert listening_agent._calculate_influence({"author_followers": 500_000}) == 80.0
        assert listening_agent._calculate_influence({"author_followers": 50_000}) == 60.0
        assert listening_agent._calculate_influence({"author_followers": 5_000}) == 40.0
        assert listening_agent._calculate_influence({"author_followers": 100}) == 20.0

    @pytest.mark.asyncio
    async def test_publish_to_stream(self, listening_agent, sample_mention):
        """Test publishing mention to Redis stream."""
        listening_agent.redis_client = AsyncMock()
        result = await listening_agent._publish_to_stream(sample_mention)
        assert result == sample_mention.id
        listening_agent.redis_client.xadd.assert_called_once()
```

```python
# tests/test_analysis_agent.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from agents.analysis_agent import AnalysisAgent
from models.analysis import SentimentLabel, IntentLabel, UrgencyLevel
from connectors.base import Mention


@pytest_asyncio.fixture
async def analysis_agent():
    config = {"openai_api_key": "test-key"}
    agent = AnalysisAgent(config)
    yield agent


@pytest.fixture
def sample_mention():
    return Mention(
        id="test-uuid-1",
        source="twitter",
        source_id="12345678",
        content="This product is absolutely terrible. Worst purchase ever.",
        author="angry_user",
        author_id="user123",
        author_followers=150000,
        url="https://twitter.com/angry_user/status/12345678",
        published_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc),
        language="en",
        engagement={"likes": 5, "retweets": 10, "replies": 3},
        media_urls=[],
        parent_id=None,
        metadata={},
        brand_keywords_matched=["TestBrand"],
    )


class TestAnalysisAgent:
    @pytest.mark.asyncio
    async def test_negative_sentiment_detection(self, analysis_agent, sample_mention):
        """Test that negative sentiment is correctly detected."""
        with patch.object(analysis_agent.executor, "ainvoke", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "output": {
                    "sentiment": "negative",
                    "sentiment_score": -0.9,
                    "sentiment_confidence": 0.95,
                    "emotions": {"anger": 0.85, "disgust": 0.6},
                    "primary_intent": "complaint",
                    "secondary_intents": [],
                    "intent_confidence": 0.9,
                    "products_mentioned": ["TestProduct"],
                    "features_mentioned": [],
                    "competitors_mentioned": [],
                    "people_mentioned": [],
                    "topics": ["quality", "customer service"],
                    "topic_confidence": {"quality": 0.8, "customer service": 0.7},
                    "urgency": "high",
                    "urgency_score": 0.7,
                    "priority_score": 0.65,
                    "brand_health_impact": -5.0,
                    "risk_flags": ["influencer_negative"],
                    "escalation_recommended": True,
                }
            }

            result = await analysis_agent.analyze(sample_mention)

            assert result.sentiment == SentimentLabel.NEGATIVE
            assert result.sentiment_score == pytest.approx(-0.9, abs=0.1)
            assert result.primary_intent == IntentLabel.COMPLAINT
            assert result.urgency == UrgencyLevel.HIGH
            assert result.escalation_recommended is True

    @pytest.mark.asyncio
    async def test_business_rule_influencer_negative(self, analysis_agent, sample_mention):
        """Test that high-follower negative mentions are auto-escalated."""
        with patch.object(analysis_agent.executor, "ainvoke", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "output": {
                    "sentiment": "negative",
                    "sentiment_score": -0.6,
                    "sentiment_confidence": 0.85,
                    "emotions": {"anger": 0.5},
                    "primary_intent": "complaint",
                    "secondary_intents": [],
                    "intent_confidence": 0.8,
                    "products_mentioned": [],
                    "features_mentioned": [],
                    "competitors_mentioned": [],
                    "people_mentioned": [],
                    "topics": [],
                    "topic_confidence": {},
                    "urgency": "medium",
                    "urgency_score": 0.5,
                    "priority_score": 0.4,
                    "brand_health_impact": -3.0,
                    "risk_flags": [],
                    "escalation_recommended": False,
                }
            }

            result = await analysis_agent.analyze(sample_mention)

            # Business rule: 150K followers + negative → HIGH urgency
            assert result.urgency == UrgencyLevel.HIGH
            assert "influencer_negative" in result.risk_flags

    @pytest.mark.asyncio
    async def test_viral_content_detection(self, analysis_agent, sample_mention):
        """Test viral content detection with high engagement."""
        sample_mention.engagement = {"likes": 5000, "retweets": 3000, "replies": 2000}

        with patch.object(analysis_agent.executor, "ainvoke", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "output": {
                    "sentiment": "negative",
                    "sentiment_score": -0.7,
                    "sentiment_confidence": 0.9,
                    "emotions": {"anger": 0.7},
                    "primary_intent": "complaint",
                    "secondary_intents": [],
                    "intent_confidence": 0.85,
                    "products_mentioned": [],
                    "features_mentioned": [],
                    "competitors_mentioned": [],
                    "people_mentioned": [],
                    "topics": [],
                    "topic_confidence": {},
                    "urgency": "high",
                    "urgency_score": 0.7,
                    "priority_score": 0.6,
                    "brand_health_impact": -4.0,
                    "risk_flags": [],
                    "escalation_recommended": False,
                }
            }

            result = await analysis_agent.analyze(sample_mention)

            # Business rule: 10K+ engagement + negative → CRITICAL
            assert result.urgency == UrgencyLevel.CRITICAL
            assert "viral_negative" in result.risk_flags
            assert result.escalation_recommended is True

    def test_priority_score_calculation(self, analysis_agent, sample_mention):
        """Test composite priority score calculation."""
        from models.analysis import AnalysisResult, EmotionLabel

        analysis = AnalysisResult(
            mention_id="test",
            analyzed_at=datetime.now(timezone.utc),
            sentiment=SentimentLabel.NEGATIVE,
            sentiment_score=-0.8,
            sentiment_confidence=0.9,
            emotions={EmotionLabel.ANGER: 0.8},
            primary_intent=IntentLabel.COMPLAINT,
            secondary_intents=[],
            intent_confidence=0.85,
            products_mentioned=[],
            features_mentioned=[],
            competitors_mentioned=[],
            people_mentioned=[],
            topics=[],
            topic_confidence={},
            urgency=UrgencyLevel.HIGH,
            urgency_score=0.75,
            priority_score=0.0,  # Will be recalculated
            brand_health_impact=-5.0,
            reach_weight=0.5,
            risk_flags=["influencer_negative"],
            escalation_recommended=True,
            model_version="test",
            processing_time_ms=1000,
        )

        score = analysis_agent._calculate_priority_score(analysis, sample_mention)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high given the inputs
```

```python
# tests/test_response_agent.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from agents.response_agent import ResponseAgent
from models.analysis import (
    AnalysisResult, SentimentLabel, EmotionLabel,
    IntentLabel, UrgencyLevel,
)
from models.response import ResponseChannel, ResponseTone, ResponseStatus, RoutingTeam
from connectors.base import Mention


@pytest_asyncio.fixture
async def response_agent():
    config = {"openai_api_key": "test-key"}
    agent = ResponseAgent(config)
    yield agent


@pytest.fixture
def sample_mention():
    return Mention(
        id="test-uuid-1",
        source="twitter",
        source_id="12345678",
        content="I love TestBrand's new product! Amazing quality.",
        author="happy_user",
        author_id="user123",
        author_followers=500,
        url="https://twitter.com/happy_user/status/12345678",
        published_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc),
        language="en",
        engagement={"likes": 5, "retweets": 1, "replies": 0},
        media_urls=[],
        parent_id=None,
        metadata={},
        brand_keywords_matched=["TestBrand"],
    )


@pytest.fixture
def sample_analysis():
    return AnalysisResult(
        mention_id="test-uuid-1",
        analyzed_at=datetime.now(timezone.utc),
        sentiment=SentimentLabel.POSITIVE,
        sentiment_score=0.85,
        sentiment_confidence=0.9,
        emotions={EmotionLabel.JOY: 0.8},
        primary_intent=IntentLabel.PRAISE,
        secondary_intents=[],
        intent_confidence=0.9,
        products_mentioned=["TestProduct"],
        features_mentioned=[],
        competitors_mentioned=[],
        people_mentioned=[],
        topics=["quality"],
        topic_confidence={"quality": 0.8},
        urgency=UrgencyLevel.NONE,
        urgency_score=0.1,
        priority_score=0.15,
        brand_health_impact=3.0,
        reach_weight=0.1,
        risk_flags=[],
        escalation_recommended=False,
        model_version="test",
        processing_time_ms=500,
    )


class TestResponseAgent:
    @pytest.mark.asyncio
    async def test_praise_response_decision(self, response_agent, sample_mention, sample_analysis):
        """Test response decision for positive praise mention."""
        with patch.object(response_agent.executor, "ainvoke", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "output": {
                    "should_respond": True,
                    "response_channel": "twitter_reply",
                    "response_tone": "grateful",
                    "routing_team": "community",
                    "routing_reason": "Positive praise from community member",
                    "response_draft": "Thank you so much! We're thrilled you're enjoying it!",
                    "template_used": "praise_thanks",
                    "status": "draft",
                    "is_escalated": False,
                }
            }

            result = await response_agent.decide(sample_mention, sample_analysis)

            assert result.should_respond is True
            assert result.response_channel == ResponseChannel.TWITTER_REPLY
            assert result.response_tone == ResponseTone.GRATEFUL
            assert result.routing_team == RoutingTeam.COMMUNITY

    @pytest.mark.asyncio
    async def test_no_response_for_low_engagement_positive(self, response_agent, sample_mention, sample_analysis):
        """Test that low-engagement positive mentions don't get responses."""
        sample_mention.engagement = {"likes": 1, "retweets": 0, "replies": 0}

        with patch.object(response_agent.executor, "ainvoke", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "output": {
                    "should_respond": True,
                    "response_channel": "twitter_reply",
                    "response_tone": "grateful",
                    "routing_team": "community",
                    "routing_reason": "Positive mention",
                    "response_draft": "Thanks!",
                    "template_used": "praise_thanks",
                    "status": "draft",
                    "is_escalated": False,
                }
            }

            result = await response_agent.decide(sample_mention, sample_analysis)

            # Business rule: Low engagement + positive + no urgency → no response
            assert result.should_respond is False
            assert result.response_channel == ResponseChannel.NO_RESPONSE

    @pytest.mark.asyncio
    async def test_critical_urgency_escalation(self, response_agent, sample_mention, sample_analysis):
        """Test that critical urgency always escalates."""
        sample_analysis.urgency = UrgencyLevel.CRITICAL
        sample_analysis.risk_flags = ["viral_negative"]

        with patch.object(response_agent.executor, "ainvoke", new_callable=AsyncMock) as mock:
            mock.return_value = {
                "output": {
                    "should_respond": True,
                    "response_channel": "twitter_reply",
                    "response_tone": "professional",
                    "routing_team": "support",
                    "routing_reason": "Negative mention",
                    "response_draft": "We're looking into this.",
                    "template_used": None,
                    "status": "draft",
                    "is_escalated": False,
                }
            }

            result = await response_agent.decide(sample_mention, sample_analysis)

            # Business rule: Critical urgency → always escalate
            assert result.is_escalated is True
            assert result.status == ResponseStatus.ESCALATED
            assert result.routing_team == RoutingTeam.PR
```

### 8.3 Integration Tests

```python
# tests/test_integration_pipeline.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from agents.listening_agent import ListeningAgent
from agents.analysis_agent import AnalysisAgent
from agents.response_agent import ResponseAgent
from connectors.base import Mention


@pytest.mark.asyncio
async def test_full_pipeline_flow():
    """Test the complete pipeline from listening to response."""
    # This test uses mocked LLM responses to verify the pipeline flow
    config = {
        "pinecone_api_key": "test-key",
        "redis_url": "redis://localhost:6379",
        "openai_api_key": "test-key",
    }

    # Create test mention
    mention = Mention(
        id="integration-test-1",
        source="twitter",
        source_id="99999",
        content="TestBrand's customer service has been amazing! Shoutout to @support_team",
        author="satisfied_customer",
        author_id="cust123",
        author_followers=250,
        url="https://twitter.com/satisfied_customer/status/99999",
        published_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc),
        language="en",
        engagement={"likes": 15, "retweets": 3, "replies": 2},
        media_urls=[],
        parent_id=None,
        metadata={},
        brand_keywords_matched=["TestBrand"],
    )

    # Step 1: Listening agent validates
    listening_agent = ListeningAgent(config)
    validation = await listening_agent._validate_mention(str(mention.__dict__))
    assert json.loads(validation)["valid"] is True

    # Step 2: Analysis agent analyzes
    analysis_agent = AnalysisAgent(config)
    with patch.object(analysis_agent.executor, "ainvoke", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "output": {
                "sentiment": "positive",
                "sentiment_score": 0.85,
                "sentiment_confidence": 0.92,
                "emotions": {"joy": 0.8, "trust": 0.7},
                "primary_intent": "praise",
                "secondary_intents": [],
                "intent_confidence": 0.9,
                "products_mentioned": [],
                "features_mentioned": ["customer service"],
                "competitors_mentioned": [],
                "people_mentioned": ["support_team"],
                "topics": ["customer service", "support"],
                "topic_confidence": {"customer service": 0.9, "support": 0.8},
                "urgency": "none",
                "urgency_score": 0.05,
                "priority_score": 0.1,
                "brand_health_impact": 4.0,
                "risk_flags": [],
                "escalation_recommended": False,
            }
        }
        analysis = await analysis_agent.analyze(mention)

    assert analysis.sentiment == SentimentLabel.POSITIVE
    assert analysis.primary_intent == IntentLabel.PRAISE

    # Step 3: Response agent decides
    response_agent = ResponseAgent(config)
    with patch.object(response_agent.executor, "ainvoke", new_callable=AsyncMock) as mock:
        mock.return_value = {
            "output": {
                "should_respond": True,
                "response_channel": "twitter_reply",
                "response_tone": "grateful",
                "routing_team": "community",
                "routing_reason": "Positive praise for support team",
                "response_draft": "Thank you for the kind words! Our support team will be happy to hear this.",
                "template_used": "praise_thanks",
                "status": "draft",
                "is_escalated": False,
            }
        }
        decision = await response_agent.decide(mention, analysis)

    assert decision.should_respond is True
    assert decision.routing_team == RoutingTeam.COMMUNITY
    assert decision.response_tone == ResponseTone.GRATEFUL
```

### 8.4 E2E Tests

```python
# tests/test_e2e_brand_monitoring.py
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone

from main import load_config
from agents.listening_agent import ListeningAgent
from agents.analysis_agent import AnalysisAgent
from agents.response_agent import ResponseAgent
from agents.reporting_agent import ReportingAgent


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_end_to_end_brand_monitoring():
    """End-to-end test with real LLM calls (requires API keys)."""
    config = load_config("config/test.yaml")

    # Initialize all agents
    listening = ListeningAgent(config)
    analysis = AnalysisAgent(config)
    response = ResponseAgent(config)
    reporting = ReportingAgent(config)

    # Create a realistic test mention
    from connectors.base import Mention
    mention = Mention(
        id="e2e-test-001",
        source="twitter",
        source_id="e2e-001",
        content="Just had an incredible experience with @YourBrand support! "
                "They resolved my issue in minutes. Highly recommend!",
        author="tech_enthusiast",
        author_id="tech123",
        author_followers=15000,
        url="https://twitter.com/tech_enthusiast/status/e2e-001",
        published_at=datetime.now(timezone.utc),
        collected_at=datetime.now(timezone.utc),
        language="en",
        engagement={"likes": 25, "retweets": 5, "replies": 3},
        media_urls=[],
        parent_id=None,
        metadata={"verified": False},
        brand_keywords_matched=["@YourBrand"],
    )

    # Step 1: Validate
    validation = await listening._validate_mention(str(mention.__dict__))
    assert json.loads(validation)["valid"] is True

    # Step 2: Analyze (real LLM call)
    analysis_result = await analysis.analyze(mention)
    assert analysis_result.sentiment in [SentimentLabel.POSITIVE, SentimentLabel.NEUTRAL]
    assert analysis_result.primary_intent in [IntentLabel.PRAISE, IntentLabel.INQUIRY]

    # Step 3: Decide response (real LLM call)
    response_decision = await response.decide(mention, analysis_result)
    assert isinstance(response_decision.should_respond, bool)
    assert response_decision.routing_team in list(RoutingTeam)

    # Step 4: Generate mini report (real LLM call)
    report = await reporting.generate_report(
        ReportType.AD_HOC,
        date.today() - timedelta(days=1),
        date.today(),
    )
    assert report.metrics.total_mentions >= 0
    assert len(report.summary) > 0

    print(f"\nE2E Test Results:")
    print(f"  Sentiment: {analysis_result.sentiment.value} ({analysis_result.sentiment_score:.2f})")
    print(f"  Intent: {analysis_result.primary_intent.value}")
    print(f"  Response: {response_decision.should_respond} via {response_decision.response_channel.value}")
    print(f"  Routed to: {response_decision.routing_team.value}")
    print(f"  Report health score: {report.metrics.brand_health_score:.1f}")
```

### 8.5 Test Configuration

```yaml
# config/test.yaml
brand:
  name: "TestBrand"
  keywords: ["TestBrand", "@TestBrand"]
  competitors: ["CompetitorA"]

connectors:
  twitter:
    bearer_token: "test-token"
    keywords: ["TestBrand"]
  reddit:
    client_id: "test-id"
    client_secret: "test-secret"
    subreddits: ["test"]
    keywords: ["TestBrand"]

agents:
  listening:
    model: "gpt-4o-mini"
    temperature: 0
  analysis:
    model: "gpt-4o"
    temperature: 0.1
  response:
    model: "gpt-4o"
    temperature: 0.3
  reporting:
    model: "gpt-4o"
    temperature: 0.2
  performance:
    model: "gpt-4o-mini"
    temperature: 0.1

infrastructure:
  redis:
    url: "redis://localhost:6379"
  pinecone:
    api_key: "test-key"
    environment: "us-east-1"
    index_name: "test-brand-mentions"
  openai:
    api_key: "test-key"
```

### 8.6 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=agents --cov=connectors --cov=models --cov-report=html

# Run only unit tests
pytest tests/ -v -m "not integration and not e2e"

# Run integration tests
pytest tests/ -v -m integration

# Run E2E tests (requires real API keys)
pytest tests/ -v -m e2e

# Run specific test file
pytest tests/test_analysis_agent.py -v

# Run with async support
pytest tests/ -v --asyncio-mode=auto
```

### 8.7 Performance Benchmarks

```python
# tests/benchmarks/test_performance.py
import pytest
import time
import statistics
from datetime import datetime, timezone

from agents.analysis_agent import AnalysisAgent
from connectors.base import Mention


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks for all agents."""

    @pytest.fixture
    def sample_mentions(self):
        """Generate sample mentions for benchmarking."""
        mentions = []
        for i in range(100):
            mentions.append(Mention(
                id=f"bench-{i}",
                source="twitter",
                source_id=f"bench-{i}",
                content=f"Sample mention content for benchmarking #{i}. "
                        f"This is a test of the brand monitoring system.",
                author=f"user_{i}",
                author_id=f"user_{i}",
                author_followers=1000 * i,
                url=f"https://twitter.com/user_{i}/status/{i}",
                published_at=datetime.now(timezone.utc),
                collected_at=datetime.now(timezone.utc),
                language="en",
                engagement={"likes": i * 10, "retweets": i * 2},
                media_urls=[],
                parent_id=None,
                metadata={},
                brand_keywords_matched=["TestBrand"],
            ))
        return mentions

    @pytest.mark.asyncio
    async def test_analysis_agent_latency(self, sample_mentions):
        """Benchmark analysis agent latency."""
        config = {"openai_api_key": "test-key"}
        agent = AnalysisAgent(config)

        latencies = []
        for mention in sample_mentions[:10]:  # Sample 10
            start = time.time()
            with patch.object(agent.executor, "ainvoke", new_callable=AsyncMock) as mock:
                mock.return_value = {"output": {"sentiment": "neutral"}}
                await agent.analyze(mention)
            latencies.append((time.time() - start) * 1000)

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\nAnalysis Agent Latency:")
        print(f"  Average: {avg_latency:.1f}ms")
        print(f"  P95: {p95_latency:.1f}ms")

        assert avg_latency < 5000  # 5 second SLA
        assert p95_latency < 10000  # 10 second P95 SLA

    @pytest.mark.asyncio
    async def test_throughput(self, sample_mentions):
        """Benchmark system throughput."""
        config = {"openai_api_key": "test-key"}
        agent = AnalysisAgent(config)

        start = time.time()
        for mention in sample_mentions:
            with patch.object(agent.executor, "ainvoke", new_callable=AsyncMock) as mock:
                mock.return_value = {"output": {"sentiment": "neutral"}}
                await agent.analyze(mention)
        elapsed = time.time() - start

        throughput = len(sample_mentions) / elapsed
        print(f"\nThroughput: {throughput:.1f} mentions/second")
        assert throughput > 1.0  # At least 1 mention/second
```

---

## Appendix A: Deployment Checklist

- [ ] Set up Redis cluster with persistence
- [ ] Configure Pinecone index with proper dimensions
- [ ] Set up PostgreSQL with automated backups
- [ ] Configure OpenAI API keys with rate limiting
- [ ] Set up Twitter/X API credentials
- [ ] Configure Reddit API credentials
- [ ] Set up NewsAPI key
- [ ] Configure Slack webhook for alerts
- [ ] Set up Prometheus + Grafana monitoring
- [ ] Configure Docker Compose for local development
- [ ] Set up Kubernetes manifests for production
- [ ] Configure CI/CD pipeline with GitHub Actions
- [ ] Set up staging environment
- [ ] Configure log aggregation (ELK or Datadog)
- [ ] Set up alerting (PagerDuty or Opsgenie)
- [ ] Configure backup and disaster recovery
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall and security groups
- [ ] Set up VPN for database access
- [ ] Configure secrets management (Vault or AWS Secrets Manager)
- [ ] Set up model versioning and A/B testing
- [ ] Configure feature flags for gradual rollout

## Appendix B: Cost Estimation

| Component | Monthly Cost (Est.) | Notes |
|-----------|---------------------|-------|
| OpenAI API | $500 - $2,000 | Depends on mention volume |
| Pinecone | $70 - $200 | Serverless tier |
| Redis | $50 - $150 | Managed Redis |
| PostgreSQL | $50 - $200 | Managed PostgreSQL |
| Compute | $200 - $500 | Kubernetes nodes |
| Monitoring | $50 - $100 | Prometheus + Grafana |
| **Total** | **$920 - $3,150** | |

## Appendix C: Security Considerations

1. **API Key Management:** Use environment variables or secrets manager, never hardcode
2. **Data Privacy:** Anonymize PII in mentions before LLM processing
3. **Rate Limiting:** Implement per-source rate limiting to avoid API bans
4. **Input Validation:** Sanitize all incoming data to prevent prompt injection
5. **Access Control:** Role-based access to reports and dashboards
6. **Audit Logging:** Log all agent decisions and actions for compliance
7. **Encryption:** Encrypt data at rest and in transit
8. **Model Security:** Monitor for prompt injection attacks via mentions

---

*End of Implementation Plan*
