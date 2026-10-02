# AI-Powered Social Media Management Implementation Plan

## LangChain DeepAgents Architecture

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Stack:** LangChain DeepAgents, Python 3.11+, LangGraph, FastAPI

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Content Creation Agent](#2-content-creation-agent)
3. [Scheduling Agent](#3-scheduling-agent)
4. [Engagement Agent](#4-engagement-agent)
5. [Social Listening Agent](#5-social-listening-agent)
6. [Influencer Identification Agent](#6-influencer-identification-agent)
7. [Performance Analytics Agent](#7-performance-analytics-agent)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 High-Level Design

The system uses a **multi-agent orchestration pattern** built on LangChain DeepAgents and LangGraph. A central Orchestrator agent coordinates six specialized sub-agents, each responsible for a distinct social media management function.

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│              (LangGraph State Machine)                       │
├─────────┬─────────┬─────────┬─────────┬─────────┬──────────┤
│ Content │Scheduling│Engagement│Listening│Influencer│Analytics │
│ Creation│  Agent   │  Agent   │  Agent  │   Agent  │  Agent   │
│  Agent  │          │          │         │          │          │
├─────────┴─────────┴─────────┴─────────┴─────────┴──────────┤
│              Shared Memory & State Store                     │
│         (Redis + PostgreSQL + Vector DB)                    │
├─────────────────────────────────────────────────────────────┤
│              Platform API Adapters                           │
│    (Twitter/X, Instagram, LinkedIn, TikTok, Facebook)      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LangChain DeepAgents | Tool-calling agents with planning |
| Orchestration | LangGraph | Stateful multi-agent workflows |
| LLM | GPT-4o / Claude 3.5 Sonnet | Reasoning and generation |
| Vector Store | ChromaDB / Pinecone | Content embedding & similarity |
| Cache | Redis | Session state, rate limiting |
| Database | PostgreSQL | Persistent analytics, schedules |
| Task Queue | Celery + Redis | Async job processing |
| API Layer | FastAPI | REST endpoints for frontend |
| Monitoring | LangSmith | Tracing and observability |

### 1.3 Agent Communication Protocol

Agents communicate via a **shared blackboard pattern** using LangGraph's state management:

```python
from langgraph.graph import StateGraph, MessagesState
from typing import TypedDict, Annotated, Literal
from operator import add

class SocialMediaState(TypedDict):
    messages: Annotated[list, add]
    current_agent: Literal[
        "orchestrator", "content_creation", "scheduling",
        "engagement", "listening", "influencer", "analytics"
    ]
    content_queue: list[dict]
    schedule: list[dict]
    engagement_tasks: list[dict]
    listening_results: list[dict]
    influencer_candidates: list[dict]
    analytics_data: dict
    brand_voice: dict
    campaign_context: dict
```

### 1.4 Orchestrator Logic

The Orchestrator uses a **plan-and-execute** pattern:

1. **Receives** high-level goals (e.g., "Launch product campaign for Q4")
2. **Decomposes** into sub-tasks for each agent
3. **Dispatches** tasks with context
4. **Monitors** progress and handles failures
5. **Aggregates** results for reporting

### 1.5 Shared Memory Architecture

- **Short-term**: LangGraph checkpoint state (per-session)
- **Medium-term**: Redis (24-hour TTL for active campaigns)
- **Long-term**: PostgreSQL (historical data, brand voice profiles)
- **Semantic**: Vector DB (content embeddings, past performance)

---

## 2. Content Creation Agent

### 2.1 Responsibilities

- Generate platform-native content (posts, threads, stories, reels scripts)
- Maintain brand voice consistency
- A/B test variations
- Repurpose content across platforms
- Generate visual descriptions for design team

### 2.2 Implementation

```python
from langchain_deepagents import DeepAgent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

class ContentCreationAgent(DeepAgent):
    """Agent responsible for generating social media content."""

    def __init__(self, brand_voice: dict, vector_store):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.brand_voice = brand_voice
        self.vector_store = vector_store
        self.tools = [
            self.search_past_performing_content,
            self.generate_post,
            self.generate_thread,
            self.generate_caption,
            self.generate_hashtags,
            self.repurpose_content,
            self.score_content,
        ]
        super().__init__(
            name="content_creation",
            llm=self.llm,
            tools=self.tools,
            system_prompt=self._build_system_prompt(),
        )

    def _build_system_prompt(self) -> str:
        return f"""You are an expert social media content creator.

Brand Voice Profile:
- Tone: {self.brand_voice.get('tone', 'professional')}
- Style: {self.brand_voice.get('style', 'conversational')}
- Values: {self.brand_voice.get('values', [])}
- Avoid: {self.brand_voice.get('avoid', [])}
- Emoji usage: {self.brand_voice.get('emoji_usage', 'minimal')}

Your tasks:
1. Create platform-optimized content that matches brand voice
2. Search past content for inspiration and avoid duplication
3. Generate multiple variations for A/B testing
4. Adapt content for each platform's format and audience
5. Include relevant hashtags and CTAs

Always consider:
- Platform character limits and best practices
- Current trends and cultural moments
- Accessibility (alt text, camelCase hashtags)
- Engagement hooks in the first 1-2 lines
"""

    @tool
    def search_past_performing_content(
        self, topic: str, platform: str, top_k: int = 5
    ) -> list[dict]:
        """Search vector store for past high-performing content on a topic."""
        results = self.vector_store.similarity_search(
            query=topic,
            k=top_k,
            filter={"platform": platform, "engagement_rate": {"$gt": 0.05}},
        )
        return [
            {
                "content": r.page_content,
                "metadata": r.metadata,
                "engagement_rate": r.metadata.get("engagement_rate"),
            }
            for r in results
        ]

    @tool
    def generate_post(
        self,
        topic: str,
        platform: str,
        tone: str = "professional",
        include_cta: bool = True,
        max_length: int | None = None,
    ) -> dict:
        """Generate a single social media post."""
        platform_limits = {
            "twitter": 280,
            "instagram": 2200,
            "linkedin": 3000,
            "tiktok": 2200,
            "facebook": 63206,
        }
        limit = max_length or platform_limits.get(platform, 280)

        prompt = f"""Create a {tone} {platform} post about: {topic}
        Character limit: {limit}
        Include CTA: {include_cta}
        Brand voice: {self.brand_voice}
        
        Return JSON: {{"text": "...", "hashtags": [...], "alt_text": "...", "cta": "..."}}
        """
        response = self.llm.invoke(prompt)
        return response

    @tool
    def generate_thread(
        self, topic: str, num_posts: int = 5, platform: str = "twitter"
    ) -> list[dict]:
        """Generate a threaded post series."""
        prompt = f"""Create a {num_posts}-post thread about: {topic}
        Platform: {platform}
        Each post should build on the previous one.
        First post must be a strong hook.
        Last post should include a CTA.
        
        Return JSON array of posts.
        """
        response = self.llm.invoke(prompt)
        return response

    @tool
    def generate_hashtags(self, topic: str, platform: str, count: int = 10) -> list[str]:
        """Generate relevant hashtags for a topic and platform."""
        prompt = f"""Generate {count} relevant hashtags for {topic} on {platform}.
        Mix of popular, niche, and branded hashtags.
        Use camelCase for multi-word hashtags.
        Return as JSON array.
        """
        response = self.llm.invoke(prompt)
        return response

    @tool
    def repurpose_content(
        self, original_content: str, target_platform: str
    ) -> dict:
        """Adapt content from one platform to another."""
        prompt = f"""Repurpose this content for {target_platform}:
        
        Original: {original_content}
        
        Adapt for {target_platform}'s format, audience, and best practices.
        Maintain the core message but optimize for the new platform.
        """
        response = self.llm.invoke(prompt)
        return response

    @tool
    def score_content(self, content: str, platform: str) -> dict:
        """Score content quality before publishing."""
        prompt = f"""Score this {platform} content on:
        - Engagement potential (1-10)
        - Brand alignment (1-10)
        - Clarity (1-10)
        - Shareability (1-10)
        
        Content: {content}
        
        Return JSON with scores and improvement suggestions.
        """
        response = self.llm.invoke(prompt)
        return response
```

### 2.3 Content Pipeline

```
Idea → Research → Draft → Score → Revise → Approve → Queue
                ↑                              │
                └──── Feedback Loop ───────────┘
```

---

## 3. Scheduling Agent

### 3.1 Responsibilities

- Optimal posting time calculation
- Content calendar management
- Frequency optimization per platform
- Avoid content clustering
- Timezone-aware scheduling

### 3.2 Implementation

```python
from datetime import datetime, timedelta
from typing import Optional
import pytz

class SchedulingAgent(DeepAgent):
    """Agent responsible for scheduling content across platforms."""

    def __init__(self, analytics_db, platform_configs: dict):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.analytics_db = analytics_db
        self.platform_configs = platform_configs
        self.tools = [
            self.get_optimal_posting_times,
            self.schedule_post,
            self.get_content_calendar,
            self.check_schedule_conflicts,
            self.optimize_frequency,
            self.bulk_schedule,
        ]
        super().__init__(
            name="scheduling",
            llm=self.llm,
            tools=self.tools,
            system_prompt=self._build_system_prompt(),
        )

    def _build_system_prompt(self) -> str:
        return """You are a social media scheduling optimizer.

Your responsibilities:
1. Determine optimal posting times based on audience analytics
2. Maintain consistent posting frequency per platform
3. Avoid scheduling conflicts (too many posts in short window)
4. Respect timezone differences for global audiences
5. Balance content types across the calendar
6. Account for platform-specific best practices

Platform best times (general):
- Twitter/X: Weekdays 9-11am, 12-1pm, 5-6pm
- Instagram: Weekdays 11am-1pm, 7-9pm
- LinkedIn: Tue-Thu 8-10am, 12pm
- TikTok: Tue-Thu 2-6pm, 7-11pm
- Facebook: Weekdays 9am-3pm

Always prioritize data-driven times over general guidelines.
"""

    @tool
    def get_optimal_posting_times(
        self,
        platform: str,
        content_type: str,
        target_audience_tz: str = "America/New_York",
        days_ahead: int = 7,
    ) -> list[dict]:
        """Calculate optimal posting times based on historical engagement data."""
        # Query analytics for best performing time slots
        query = """
        SELECT 
            EXTRACT(HOUR FROM posted_at) as hour,
            EXTRACT(DOW FROM posted_at) as day_of_week,
            AVG(engagement_rate) as avg_engagement,
            COUNT(*) as post_count
        FROM social_media_posts
        WHERE platform = %s 
          AND content_type = %s
          AND posted_at > NOW() - INTERVAL '90 days'
        GROUP BY hour, day_of_week
        HAVING COUNT(*) >= 3
        ORDER BY avg_engagement DESC
        LIMIT 10;
        """
        results = self.analytics_db.execute(query, (platform, content_type))
        
        # Convert to target timezone
        tz = pytz.timezone(target_audience_tz)
        optimal_times = []
        for row in results:
            optimal_times.append({
                "day_of_week": row["day_of_week"],
                "hour_local": row["hour"],
                "hour_target_tz": self._convert_timezone(row["hour"], tz),
                "expected_engagement": row["avg_engagement"],
                "confidence": min(row["post_count"] / 10, 1.0),
            })
        
        return optimal_times

    @tool
    def schedule_post(
        self,
        content: dict,
        platform: str,
        scheduled_time: datetime,
        campaign_id: Optional[str] = None,
    ) -> dict:
        """Schedule a post for publishing."""
        # Validate no conflicts
        conflicts = self.check_schedule_conflicts(
            platform=platform,
            proposed_time=scheduled_time,
            window_minutes=30,
        )
        
        if conflicts:
            # Suggest alternative times
            alternatives = self._find_alternative_times(
                platform, scheduled_time, conflicts
            )
            return {
                "status": "conflict",
                "conflicts": conflicts,
                "suggested_alternatives": alternatives,
            }
        
        # Create schedule entry
        schedule_entry = {
            "id": generate_uuid(),
            "content": content,
            "platform": platform,
            "scheduled_time": scheduled_time.isoformat(),
            "campaign_id": campaign_id,
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Store in database
        self.analytics_db.insert("content_schedule", schedule_entry)
        
        # Add to Celery queue for publishing
        publish_task.apply_async(
            args=[schedule_entry["id"]],
            eta=scheduled_time,
        )
        
        return {"status": "scheduled", "schedule_id": schedule_entry["id"]}

    @tool
    def get_content_calendar(
        self,
        start_date: datetime,
        end_date: datetime,
        platforms: list[str] | None = None,
    ) -> list[dict]:
        """Retrieve content calendar for a date range."""
        query = """
        SELECT * FROM content_schedule
        WHERE scheduled_time BETWEEN %s AND %s
        {platform_filter}
        ORDER BY scheduled_time ASC;
        """
        params = [start_date, end_date]
        
        if platforms:
            platform_filter = "AND platform = ANY(%s)"
            params.append(platforms)
        else:
            platform_filter = ""
        
        query = query.format(platform_filter=platform_filter)
        return self.analytics_db.execute(query, params)

    @tool
    def check_schedule_conflicts(
        self,
        platform: str,
        proposed_time: datetime,
        window_minutes: int = 30,
    ) -> list[dict]:
        """Check for scheduling conflicts on a platform."""
        window_start = proposed_time - timedelta(minutes=window_minutes)
        window_end = proposed_time + timedelta(minutes=window_minutes)
        
        query = """
        SELECT id, content, scheduled_time, status
        FROM content_schedule
        WHERE platform = %s
          AND scheduled_time BETWEEN %s AND %s
          AND status IN ('scheduled', 'approved');
        """
        return self.analytics_db.execute(
            query, (platform, window_start, window_end)
        )

    @tool
    def optimize_frequency(
        self, platform: str, campaign_goals: dict
    ) -> dict:
        """Recommend optimal posting frequency."""
        # Analyze current frequency vs engagement
        query = """
        SELECT 
            DATE_TRUNC('week', posted_at) as week,
            COUNT(*) as post_count,
            AVG(engagement_rate) as avg_engagement
        FROM social_media_posts
        WHERE platform = %s
          AND posted_at > NOW() - INTERVAL '12 weeks'
        GROUP BY week
        ORDER BY week DESC;
        """
        weekly_stats = self.analytics_db.execute(query, (platform,))
        
        # Use LLM to analyze and recommend
        prompt = f"""Based on this posting frequency data, recommend optimal frequency:
        
        Weekly stats: {weekly_stats}
        Campaign goals: {campaign_goals}
        
        Consider:
        - Diminishing returns from over-posting
        - Audience fatigue signals
        - Platform algorithm preferences
        - Content quality vs quantity trade-off
        
        Return JSON with recommended posts_per_week and reasoning.
        """
        return self.llm.invoke(prompt)

    @tool
    def bulk_schedule(
        self, content_items: list[dict], platform: str, start_date: datetime
    ) -> list[dict]:
        """Schedule multiple content items with optimal spacing."""
        scheduled = []
        current_time = start_date
        
        for item in content_items:
            # Find next optimal slot
            optimal = self.get_optimal_posting_times(
                platform=platform,
                content_type=item.get("content_type", "standard"),
            )
            
            if optimal:
                best_slot = optimal[0]
                current_time = self._next_occurrence(
                    best_slot["day_of_week"], best_slot["hour_local"], current_time
                )
            
            result = self.schedule_post(
                content=item,
                platform=platform,
                scheduled_time=current_time,
            )
            scheduled.append(result)
            
            # Space posts appropriately
            current_time += timedelta(hours=self._get_spacing(platform))
        
        return scheduled
```

### 3.3 Scheduling Algorithm

The scheduling agent uses a **constraint satisfaction** approach:

1. **Hard constraints**: Platform limits, blackout dates, approval status
2. **Soft constraints**: Optimal times, content type diversity, frequency targets
3. **Optimization**: Maximize expected engagement while maintaining consistency

---

## 4. Engagement Agent

### 4.1 Responsibilities

- Monitor mentions, comments, and DMs
- Generate contextual response suggestions
- Escalate sensitive issues to human team
- Identify brand advocates and trolls
- Track response time SLAs

### 4.2 Implementation

```python
from enum import Enum

class Sentiment(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    CRISIS = "crisis"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class EngagementAgent(DeepAgent):
    """Agent responsible for social media engagement and community management."""

    def __init__(self, brand_voice: dict, escalation_rules: dict):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
        self.brand_voice = brand_voice
        self.escalation_rules = escalation_rules
        self.tools = [
            self.monitor_mentions,
            self.analyze_sentiment,
            self.generate_response,
            self.categorize_engagement,
            self.detect_crisis,
            self.identify_advocates,
            self.escalate_issue,
            self.track_response_sla,
        ]
        super().__init__(
            name="engagement",
            llm=self.llm,
            tools=self.tools,
            system_prompt=self._build_system_prompt(),
        )

    def _build_system_prompt(self) -> str:
        return f"""You are a social media community manager.

Brand Voice: {self.brand_voice}

Your responsibilities:
1. Monitor and categorize all brand mentions and comments
2. Generate empathetic, on-brand responses
3. Detect and escalate potential crises
4. Identify brand advocates and engage them
5. Maintain response time SLAs (target: < 1 hour for complaints)

Response guidelines:
- Always acknowledge the person's feelings
- Never argue or be defensive
- Take detailed complaints offline (DM)
- Use the person's name when available
- Keep responses concise and actionable
- Match the platform's communication style

Escalation triggers:
- Legal threats or mentions
- Media inquiries
- Viral negative content (>1000 shares)
- Safety concerns
- Executive mentions with complaints
"""

    @tool
    def monitor_mentions(
        self, platform: str, since: datetime, brand_handles: list[str]
    ) -> list[dict]:
        """Fetch recent mentions from platform API."""
        adapter = PlatformAdapterFactory.get_adapter(platform)
        mentions = adapter.get_mentions(
            handles=brand_handles,
            since=since,
            include_replies=True,
            include_retweets=True,
        )
        
        # Enrich with author info
        for mention in mentions:
            mention["author_followers"] = adapter.get_user_followers(
                mention["author_id"]
            )
            mention["author_verified"] = adapter.get_user_verified(
                mention["author_id"]
            )
        
        return mentions

    @tool
    def analyze_sentiment(self, text: str, context: dict | None = None) -> dict:
        """Analyze sentiment with nuance detection."""
        prompt = f"""Analyze the sentiment of this social media post:
        
        Text: {text}
        Context: {context or 'None'}
        
        Consider:
        - Primary sentiment (positive/neutral/negative)
        - Sarcasm detection
        - Emotion intensity (1-10)
        - Urgency level
        - Potential for virality
        - Brand risk level
        
        Return JSON with detailed sentiment analysis.
        """
        return self.llm.invoke(prompt)

    @tool
    def generate_response(
        self,
        original_post: dict,
        sentiment: dict,
        response_type: str = "standard",
    ) -> dict:
        """Generate an appropriate response."""
        prompt = f"""Generate a response to this social media post:
        
        Original post: {original_post['text']}
        Author: @{original_post['author_handle']}
        Platform: {original_post['platform']}
        Sentiment: {sentiment}
        Response type: {response_type}
        
        Brand voice: {self.brand_voice}
        
        Guidelines:
        - Be genuine and empathetic
        - Address the specific concern/question
        - Include next steps or call to action
        - Keep within platform character limits
        - Use appropriate emoji (brand allows: {self.brand_voice.get('emoji_usage', 'minimal')})
        
        Return JSON: {{"response": "...", "tone": "...", "requires_approval": bool}}
        """
        return self.llm.invoke(prompt)

    @tool
    def categorize_engagement(self, post: dict) -> dict:
        """Categorize engagement type and priority."""
        prompt = f"""Categorize this social media engagement:
        
        Post: {post['text']}
        Author followers: {post.get('author_followers', 0)}
        Author verified: {post.get('author_verified', False)}
        
        Categories:
        - question (product, support, general)
        - complaint (product, service, billing)
        - compliment
        - mention (neutral reference)
        - spam
        - crisis (legal, safety, viral negative)
        - influencer_opportunity
        
        Also assign priority (1-4) based on:
        - Author influence (followers, verification)
        - Sentiment severity
        - Virality potential
        - Brand risk
        
        Return JSON with category, priority, and reasoning.
        """
        return self.llm.invoke(prompt)

    @tool
    def detect_crisis(self, mentions: list[dict]) -> dict:
        """Detect potential PR crises from mention patterns."""
        # Aggregate signals
        negative_count = sum(
            1 for m in mentions if m.get("sentiment") == "negative"
        )
        high_reach = sum(
            1 for m in mentions if m.get("author_followers", 0) > 10000
        )
        viral_signals = sum(
            1 for m in mentions if m.get("share_count", 0) > 100
        )
        
        crisis_score = (
            negative_count * 1
            + high_reach * 3
            + viral_signals * 5
        )
        
        if crisis_score >= 20:
            return {
                "crisis_detected": True,
                "severity": "high",
                "crisis_score": crisis_score,
                "recommended_action": "immediate_escalation",
                "summary": f"Potential crisis: {negative_count} negative mentions, "
                f"{high_reach} from high-reach accounts, {viral_signals} going viral",
            }
        elif crisis_score >= 10:
            return {
                "crisis_detected": True,
                "severity": "medium",
                "crisis_score": crisis_score,
                "recommended_action": "monitor_closely",
            }
        
        return {"crisis_detected": False, "crisis_score": crisis_score}

    @tool
    def identify_advocates(self, mentions: list[dict], min_engagement: int = 5) -> list[dict]:
        """Identify potential brand advocates."""
        # Group by author
        author_stats = {}
        for mention in mentions:
            author = mention["author_handle"]
            if author not in author_stats:
                author_stats[author] = {
                    "handle": author,
                    "mention_count": 0,
                    "positive_count": 0,
                    "total_reach": 0,
                }
            author_stats[author]["mention_count"] += 1
            if mention.get("sentiment") == "positive":
                author_stats[author]["positive_count"] += 1
            author_stats[author]["total_reach"] += mention.get("author_followers", 0)
        
        # Filter for advocates
        advocates = []
        for author, stats in author_stats.items():
            if (
                stats["mention_count"] >= min_engagement
                and stats["positive_count"] / stats["mention_count"] > 0.6
            ):
                advocates.append({
                    **stats,
                    "advocate_score": (
                        stats["mention_count"] * 0.3
                        + stats["positive_count"] * 0.5
                        + min(stats["total_reach"] / 10000, 5) * 0.2
                    ),
                })
        
        return sorted(advocates, key=lambda x: x["advocate_score"], reverse=True)

    @tool
    def escalate_issue(self, issue: dict, reason: str) -> dict:
        """Escalate an issue to the human team."""
        escalation = {
            "issue_id": generate_uuid(),
            "original_post": issue,
            "reason": reason,
            "escalated_at": datetime.utcnow().isoformat(),
            "status": "pending_review",
            "assigned_team": self._route_escalation(issue),
        }
        
        # Send notification
        self._send_escalation_notification(escalation)
        
        return escalation

    @tool
    def track_response_sla(self, platform: str) -> dict:
        """Track response time SLA compliance."""
        query = """
        SELECT 
            platform,
            AVG(EXTRACT(EPOCH FROM (first_response_at - created_at))/60) as avg_response_minutes,
            PERCENTILE_CONT(0.95) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (first_response_at - created_at))/60
            ) as p95_response_minutes,
            COUNT(*) FILTER (WHERE first_response_at IS NULL) as unanswered_count,
            COUNT(*) as total_mentions
        FROM social_media_mentions
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY platform;
        """
        return self.analytics_db.execute(query, (platform,))
```

### 4.3 Engagement Workflow

```
Mention Received → Categorize → Sentiment Analysis → Route
                                                    ├─ Positive → Thank & Engage
                                                    ├─ Question → Answer/Route to FAQ
                                                    ├─ Complaint → Empathize + Resolve
                                                    ├─ Crisis → Escalate Immediately
                                                    └─ Spam → Filter/Block
```

---

## 5. Social Listening Agent

### 5.1 Responsibilities

- Monitor brand mentions across platforms
- Track competitor activity
- Identify trending topics and hashtags
- Detect emerging issues before they escalate
- Generate daily/weekly listening reports

### 5.2 Implementation

```python
class SocialListeningAgent(DeepAgent):
    """Agent responsible for social listening and trend detection."""

    def __init__(self, brand_keywords: list[str], competitor_handles: list[str]):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.4)
        self.brand_keywords = brand_keywords
        self.competitor_handles = competitor_handles
        self.tools = [
            self.monitor_brand_mentions,
            self.track_competitors,
            self.detect_trends,
            self.analyze_share_of_voice,
            self.generate_listening_report,
            self.identify_emerging_issues,
            self.track_hashtag_performance,
        ]
        super().__init__(
            name="listening",
            llm=self.llm,
            tools=self.tools,
            system_prompt=self._build_system_prompt(),
        )

    def _build_system_prompt(self) -> str:
        return f"""You are a social media listening analyst.

Brand keywords to monitor: {self.brand_keywords}
Competitors to track: {self.competitor_handles}

Your responsibilities:
1. Monitor all brand mentions across platforms
2. Track competitor strategies and performance
3. Identify emerging trends and conversations
4. Calculate share of voice vs competitors
5. Detect potential issues before they escalate
6. Generate actionable listening reports

Analysis framework:
- Volume: Mention counts and trajectory
- Sentiment: Positive/negative/neutral ratio
- Reach: Total potential impressions
- Engagement: Likes, shares, comments
- Share of voice: Brand vs competitor mention ratio
- Trend velocity: Rate of change in mentions
"""

    @tool
    def monitor_brand_mentions(
        self,
        platforms: list[str],
        time_window: str = "24h",
        include_sentiment: bool = True,
    ) -> dict:
        """Comprehensive brand mention monitoring."""
        results = {}
        
        for platform in platforms:
            adapter = PlatformAdapterFactory.get_adapter(platform)
            
            # Search for brand keywords
            mentions = []
            for keyword in self.brand_keywords:
                mentions.extend(
                    adapter.search_posts(
                        query=keyword,
                        time_window=time_window,
                        max_results=100,
                    )
                )
            
            # Deduplicate
            seen = set()
            unique_mentions = []
            for m in mentions:
                if m["id"] not in seen:
                    seen.add(m["id"])
                    unique_mentions.append(m)
            
            # Analyze sentiment if requested
            if include_sentiment:
                for mention in unique_mentions:
                    mention["sentiment"] = self.analyze_sentiment(
                        mention["text"]
                    )
            
            results[platform] = {
                "total_mentions": len(unique_mentions),
                "unique_authors": len(set(m["author_id"] for m in unique_mentions)),
                "total_reach": sum(m.get("author_followers", 0) for m in unique_mentions),
                "sentiment_breakdown": self._aggregate_sentiment(unique_mentions),
                "top_mentions": sorted(
                    unique_mentions,
                    key=lambda x: x.get("engagement_count", 0),
                    reverse=True,
                )[:10],
                "mentions": unique_mentions,
            }
        
        return results

    @tool
    def track_competitors(
        self, platforms: list[str], time_window: str = "7d"
    ) -> dict:
        """Track competitor activity and performance."""
        results = {}
        
        for competitor in self.competitor_handles:
            competitor_data = {
                "handle": competitor,
                "platforms": {},
            }
            
            for platform in platforms:
                adapter = PlatformAdapterFactory.get_adapter(platform)
                
                # Get competitor's recent posts
                posts = adapter.get_user_posts(
                    handle=competitor,
                    time_window=time_window,
                    max_results=50,
                )
                
                # Calculate metrics
                total_engagement = sum(
                    p.get("like_count", 0)
                    + p.get("share_count", 0)
                    + p.get("comment_count", 0)
                    for p in posts
                )
                
                competitor_data["platforms"][platform] = {
                    "post_count": len(posts),
                    "total_engagement": total_engagement,
                    "avg_engagement": total_engagement / max(len(posts), 1),
                    "top_posts": sorted(
                        posts,
                        key=lambda x: x.get("like_count", 0)
                        + x.get("share_count", 0),
                        reverse=True,
                    )[:5],
                    "posting_frequency": self._calculate_frequency(posts),
                }
            
            results[competitor] = competitor_data
        
        return results

    @tool
    def detect_trends(
        self,
        platforms: list[str],
        category: str | None = None,
        min_velocity: float = 1.5,
    ) -> list[dict]:
        """Detect trending topics and hashtags."""
        trends = []
        
        for platform in platforms:
            adapter = PlatformAdapterFactory.get_adapter(platform)
            
            # Get trending topics
            platform_trends = adapter.get_trending_topics(
                category=category,
                limit=50,
            )
            
            for trend in platform_trends:
                # Calculate velocity (rate of growth)
                velocity = self._calculate_trend_velocity(trend, platform)
                
                if velocity >= min_velocity:
                    # Check brand relevance
                    relevance = self._assess_brand_relevance(trend)
                    
                    if relevance > 0.5:
                        trends.append({
                            "topic": trend["name"],
                            "platform": platform,
                            "volume": trend["volume"],
                            "velocity": velocity,
                            "brand_relevance": relevance,
                            "suggested_action": self._suggest_trend_action(
                                trend, relevance
                            ),
                        })
        
        return sorted(trends, key=lambda x: x["velocity"] * x["brand_relevance"], reverse=True)

    @tool
    def analyze_share_of_voice(
        self, platforms: list[str], time_window: str = "30d"
    ) -> dict:
        """Calculate brand share of voice vs competitors."""
        brand_mentions = self.monitor_brand_mentions(platforms, time_window)
        competitor_data = self.track_competitors(platforms, time_window)
        
        brand_total = sum(
            data["total_mentions"] for data in brand_mentions.values()
        )
        
        competitor_totals = {}
        for competitor, data in competitor_data.items():
            competitor_totals[competitor] = sum(
                p["post_count"] for p in data["platforms"].values()
            )
        
        total_voice = brand_total + sum(competitor_totals.values())
        
        return {
            "brand_mentions": brand_total,
            "brand_share": brand_total / max(total_voice, 1),
            "competitor_shares": {
                c: count / max(total_voice, 1)
                for c, count in competitor_totals.items()
            },
            "total_voice": total_voice,
            "trend": self._calculate_voice_trend(platforms, time_window),
        }

    @tool
    def generate_listening_report(
        self,
        report_type: str = "daily",
        platforms: list[str] | None = None,
    ) -> dict:
        """Generate a comprehensive listening report."""
        platforms = platforms or ["twitter", "instagram", "linkedin"]
        
        time_window = "24h" if report_type == "daily" else "7d"
        
        # Gather data
        brand_mentions = self.monitor_brand_mentions(platforms, time_window)
        competitors = self.track_competitors(platforms, time_window)
        trends = self.detect_trends(platforms)
        sov = self.analyze_share_of_voice(platforms, time_window)
        
        # Generate insights with LLM
        prompt = f"""Generate a {report_type} social listening report:
        
        Brand mentions: {brand_mentions}
        Competitor activity: {competitors}
        Emerging trends: {trends}
        Share of voice: {sov}
        
        Include:
        1. Executive summary (3-4 bullet points)
        2. Key metrics and changes from previous period
        3. Notable mentions and conversations
        4. Competitor highlights
        5. Trending topics to consider
        6. Recommended actions
        7. Potential risks or opportunities
        
        Format as structured JSON.
        """
        
        report = self.llm.invoke(prompt)
        return report

    @tool
    def identify_emerging_issues(
        self, platforms: list[str], sensitivity: str = "medium"
    ) -> list[dict]:
        """Detect emerging issues before they become crises."""
        # Get recent mentions with negative sentiment
        mentions = self.monitor_brand_mentions(platforms, "24h")
        
        issues = []
        for platform, data in mentions.items():
            negative = [
                m for m in data.get("mentions", [])
                if m.get("sentiment", {}).get("primary") == "negative"
            ]
            
            # Group by topic/theme
            themes = self._cluster_by_theme(negative)
            
            for theme, theme_mentions in themes.items():
                # Calculate issue velocity
                velocity = len(theme_mentions) / 24  # mentions per hour
                
                # Check for acceleration
                acceleration = self._calculate_acceleration(theme_mentions)
                
                if velocity > 2 or acceleration > 2:
                    issues.append({
                        "theme": theme,
                        "mention_count": len(theme_mentions),
                        "velocity": velocity,
                        "acceleration": acceleration,
                        "sample_mentions": theme_mentions[:3],
                        "severity": self._assess_issue_severity(theme_mentions),
                        "recommended_response": self._suggest_issue_response(theme),
                    })
        
        return sorted(issues, key=lambda x: x["severity"], reverse=True)

    @tool
    def track_hashtag_performance(
        self, hashtags: list[str], platforms: list[str], time_window: str = "30d"
    ) -> dict:
        """Track performance of branded and campaign hashtags."""
        results = {}
        
        for hashtag in hashtags:
            tag_data = {"hashtag": hashtag, "platforms": {}}
            
            for platform in platforms:
                adapter = PlatformAdapterFactory.get_adapter(platform)
                
                posts = adapter.search_posts(
                    query=f"#{hashtag}",
                    time_window=time_window,
                    max_results=1000,
                )
                
                total_engagement = sum(
                    p.get("like_count", 0)
                    + p.get("share_count", 0)
                    + p.get("comment_count", 0)
                    for p in posts
                )
                
                tag_data["platforms"][platform] = {
                    "post_count": len(posts),
                    "total_engagement": total_engagement,
                    "avg_engagement": total_engagement / max(len(posts), 1),
                    "reach": sum(p.get("author_followers", 0) for p in posts),
                    "top_posts": sorted(
                        posts,
                        key=lambda x: x.get("like_count", 0),
                        reverse=True,
                    )[:5],
                }
            
            results[hashtag] = tag_data
        
        return results
```

### 5.3 Listening Dashboard Data Flow

```
Platform APIs → Stream Processor → Sentiment Analysis → Trend Detection → Alert System
                                                                    ↓
                                                              Dashboard API
                                                                    ↓
                                                              React Frontend
```

---

## 6. Influencer Identification Agent

### 6.1 Responsibilities

- Identify relevant influencers in brand's niche
- Score influencer quality and brand fit
- Track influencer engagement history
- Manage outreach campaigns
- Monitor influencer content performance

### 6.2 Implementation

```python
class InfluencerIdentificationAgent(DeepAgent):
    """Agent responsible for identifying and evaluating influencers."""

    def __init__(self, brand_profile: dict, campaign_criteria: dict):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.4)
        self.brand_profile = brand_profile
        self.campaign_criteria = campaign_criteria
        self.tools = [
            self.discover_influencers,
            self.score_influencer,
            self.analyze_audience_quality,
            self.check_brand_alignment,
            self.track_influencer_content,
            self.generate_outreach_message,
            self.monitor_influencer_campaigns,
            self.calculate_influencer_roi,
        ]
        super().__init__(
            name="influencer",
            llm=self.llm,
            tools=self.tools,
            system_prompt=self._build_system_prompt(),
        )

    def _build_system_prompt(self) -> str:
        return f"""You are an influencer marketing specialist.

Brand profile: {self.brand_profile}
Campaign criteria: {self.campaign_criteria}

Your responsibilities:
1. Discover relevant influencers in the brand's niche
2. Evaluate influencer quality, authenticity, and brand fit
3. Analyze audience demographics and quality
4. Generate personalized outreach messages
5. Track influencer campaign performance
6. Calculate influencer ROI

Evaluation criteria:
- Engagement rate (minimum 2% for micro, 1% for macro)
- Audience authenticity (low bot percentage)
- Content quality and brand alignment
- Posting consistency
- Audience demographics match
- Past brand partnership quality
- Growth trajectory

Red flags:
- Sudden follower spikes
- Low engagement relative to follower count
- Excessive sponsored content
- Controversial history
- Fake engagement patterns
"""

    @tool
    def discover_influencers(
        self,
        platforms: list[str],
        niche: str,
        min_followers: int = 10000,
        max_followers: int = 1000000,
        location: str | None = None,
    ) -> list[dict]:
        """Discover influencers in a specific niche."""
        influencers = []
        
        for platform in platforms:
            adapter = PlatformAdapterFactory.get_adapter(platform)
            
            # Search by niche keywords
            keywords = self._generate_niche_keywords(niche)
            
            for keyword in keywords:
                users = adapter.search_users(
                    query=keyword,
                    min_followers=min_followers,
                    max_followers=max_followers,
                    location=location,
                    limit=50,
                )
                
                for user in users:
                    # Get detailed metrics
                    metrics = adapter.get_user_metrics(user["id"])
                    
                    influencers.append({
                        "platform": platform,
                        "user_id": user["id"],
                        "handle": user["handle"],
                        "name": user.get("name", ""),
                        "bio": user.get("bio", ""),
                        "followers": metrics["followers"],
                        "following": metrics["following"],
                        "post_count": metrics["post_count"],
                        "avg_likes": metrics["avg_likes"],
                        "avg_comments": metrics["avg_comments"],
                        "engagement_rate": metrics["engagement_rate"],
                        "profile_url": user.get("profile_url", ""),
                        "email": user.get("email"),  # If available
                        "category": niche,
                    })
        
        # Deduplicate across platforms
        seen = set()
        unique = []
        for inf in influencers:
            key = inf["handle"].lower()
            if key not in seen:
                seen.add(key)
                unique.append(inf)
        
        return unique

    @tool
    def score_influencer(self, influencer: dict) -> dict:
        """Score an influencer across multiple dimensions."""
        scores = {
            "reach_score": self._score_reach(influencer),
            "engagement_score": self._score_engagement(influencer),
            "authenticity_score": self._score_authenticity(influencer),
            "alignment_score": self._score_alignment(influencer),
            "consistency_score": self._score_consistency(influencer),
        }
        
        # Weighted total
        weights = {
            "reach_score": 0.15,
            "engagement_score": 0.30,
            "authenticity_score": 0.25,
            "alignment_score": 0.20,
            "consistency_score": 0.10,
        }
        
        total_score = sum(
            scores[k] * weights[k] for k in scores
        )
        
        return {
            "influencer": influencer["handle"],
            "platform": influencer["platform"],
            "scores": scores,
            "total_score": round(total_score, 2),
            "tier": self._classify_tier(total_score),
            "recommendation": self._generate_recommendation(total_score, scores),
        }

    @tool
    def analyze_audience_quality(self, influencer_handle: str, platform: str) -> dict:
        """Analyze the quality and authenticity of an influencer's audience."""
        adapter = PlatformAdapterFactory.get_adapter(platform)
        
        # Get audience demographics
        demographics = adapter.get_audience_demographics(influencer_handle)
        
        # Analyze engagement patterns
        posts = adapter.get_user_posts(influencer_handle, limit=50)
        
        engagement_pattern = self._analyze_engagement_pattern(posts)
        
        # Detect fake followers
        authenticity = self._detect_fake_followers(
            influencer_handle, demographics, engagement_pattern
        )
        
        return {
            "demographics": demographics,
            "engagement_pattern": engagement_pattern,
            "authenticity_score": authenticity["score"],
            "fake_follower_estimate": authenticity["fake_percentage"],
            "quality_tier": authenticity["tier"],
            "red_flags": authenticity["red_flags"],
        }

    @tool
    def check_brand_alignment(self, influencer: dict) -> dict:
        """Check how well an influencer aligns with brand values."""
        # Get influencer's recent content
        adapter = PlatformAdapterFactory.get_adapter(influencer["platform"])
        posts = adapter.get_user_posts(influencer["user_id"], limit=30)
        
        # Analyze content themes
        prompt = f"""Analyze this influencer's content for brand alignment:
        
        Brand values: {self.brand_profile.get('values', [])}
        Brand voice: {self.brand_profile.get('voice', '')}
        Target audience: {self.brand_profile.get('target_audience', '')}
        
        Influencer bio: {influencer.get('bio', '')}
        Recent posts: {[p['text'][:200] for p in posts]}
        
        Evaluate:
        1. Content theme alignment (0-10)
        2. Values alignment (0-10)
        3. Audience overlap (0-10)
        4. Brand safety risk (0-10, 10 = no risk)
        5. Past partnership quality (0-10)
        
        Return JSON with scores and detailed reasoning.
        """
        
        return self.llm.invoke(prompt)

    @tool
    def generate_outreach_message(
        self, influencer: dict, campaign: dict, personalization: dict
    ) -> dict:
        """Generate a personalized outreach message."""
        prompt = f"""Write a personalized outreach message to this influencer:
        
        Influencer: {influencer['handle']} ({influencer['platform']})
        Followers: {influencer['followers']}
        Niche: {influencer.get('category', 'N/A')}
        Recent content: {personalization.get('recent_posts', [])}
        
        Campaign details: {campaign}
        Brand: {self.brand_profile.get('name', '')}
        
        Guidelines:
        - Keep it concise and genuine
        - Reference their specific content
        - Clearly state the value proposition
        - Include compensation range if appropriate
        - Professional but not corporate
        - Include clear CTA
        
        Return JSON: {{"subject": "...", "message": "...", "platform": "..."}}
        """
        
        return self.llm.invoke(prompt)

    @tool
    def track_influencer_content(
        self, influencer_handle: str, platform: str, campaign_id: str
    ) -> dict:
        """Track content created by influencer for a campaign."""
        adapter = PlatformAdapterFactory.get_adapter(platform)
        
        # Get posts mentioning the brand
        posts = adapter.search_posts(
            query=f"@{influencer_handle} #{campaign_id}",
            time_window="30d",
        )
        
        # Calculate performance
        total_engagement = sum(
            p.get("like_count", 0)
            + p.get("share_count", 0)
            + p.get("comment_count", 0)
            for p in posts
        )
        
        return {
            "influencer": influencer_handle,
            "campaign_id": campaign_id,
            "posts_found": len(posts),
            "total_engagement": total_engagement,
            "avg_engagement": total_engagement / max(len(posts), 1),
            "reach": sum(p.get("author_followers", 0) for p in posts),
            "posts": posts,
            "content_quality": self._assess_content_quality(posts),
        }

    @tool
    def monitor_influencer_campaigns(self, active_campaigns: list[dict]) -> dict:
        """Monitor all active influencer campaigns."""
        results = {}
        
        for campaign in active_campaigns:
            campaign_id = campaign["id"]
            
            # Track each influencer in the campaign
            influencer_results = []
            for influencer in campaign["influencers"]:
                tracking = self.track_influencer_content(
                    influencer_handle=influencer["handle"],
                    platform=influencer["platform"],
                    campaign_id=campaign_id,
                )
                influencer_results.append(tracking)
            
            # Aggregate campaign performance
            total_engagement = sum(
                r["total_engagement"] for r in influencer_results
            )
            total_reach = sum(r["reach"] for r in influencer_results)
            
            results[campaign_id] = {
                "campaign_name": campaign["name"],
                "influencer_count": len(campaign["influencers"]),
                "total_posts": sum(r["posts_found"] for r in influencer_results),
                "total_engagement": total_engagement,
                "total_reach": total_reach,
                "cost": campaign.get("budget", 0),
                "roi": self._calculate_campaign_roi(
                    total_engagement, total_reach, campaign.get("budget", 0)
                ),
                "influencer_breakdown": influencer_results,
            }
        
        return results

    @tool
    def calculate_influencer_roi(
        self, campaign_results: dict, campaign_cost: float
    ) -> dict:
        """Calculate ROI for an influencer campaign."""
        # Calculate value metrics
        total_engagement = campaign_results["total_engagement"]
        total_reach = campaign_results["total_reach"]
        
        # Industry benchmarks
        cpm = 10.0  # Cost per 1000 impressions
        cpe = 0.10  # Cost per engagement
        
        # Calculate value
        reach_value = (total_reach / 1000) * cpm
        engagement_value = total_engagement * cpe
        total_value = reach_value + engagement_value
        
        # Calculate ROI
        roi = (total_value - campaign_cost) / max(campaign_cost, 1)
        
        return {
            "campaign_cost": campaign_cost,
            "reach_value": round(reach_value, 2),
            "engagement_value": round(engagement_value, 2),
            "total_value": round(total_value, 2),
            "roi_percentage": round(roi * 100, 2),
            "roi_multiple": round(total_value / max(campaign_cost, 1), 2),
            "cost_per_engagement": round(campaign_cost / max(total_engagement, 1), 2),
            "cost_per_reach": round(campaign_cost / max(total_reach, 1), 4),
        }
```

### 6.3 Influencer Scoring Algorithm

```
Total Score = 
    Reach Score × 0.15 +
    Engagement Score × 0.30 +
    Authenticity Score × 0.25 +
    Brand Alignment × 0.20 +
    Consistency Score × 0.10

Tiers:
- 90+: Tier 1 (Premium) - Priority outreach
- 75-89: Tier 2 (High Quality) - Strong candidates
- 60-74: Tier 3 (Good) - Consider for smaller campaigns
- <60: Tier 4 (Low) - Not recommended
```

---

## 7. Performance Analytics Agent

### 7.1 Responsibilities

- Aggregate performance metrics across platforms
- Generate automated reports and insights
- Identify top-performing content patterns
- Forecast future performance
- Provide optimization recommendations

### 7.2 Implementation

```python
class PerformanceAnalyticsAgent(DeepAgent):
    """Agent responsible for social media analytics and reporting."""

    def __init__(self, analytics_db, benchmark_data: dict):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.analytics_db = analytics_db
        self.benchmark_data = benchmark_data
        self.tools = [
            self.get_platform_metrics,
            self.get_content_performance,
            self.generate_analytics_report,
            self.identify_top_performers,
            self.analyze_posting_patterns,
            self.forecast_performance,
            self.compare_to_benchmarks,
            self.generate_recommendations,
            self.calculate_funnel_metrics,
        ]
        super().__init__(
            name="analytics",
            llm=self.llm,
            tools=self.tools,
            system_prompt=self._build_system_prompt(),
        )

    def _build_system_prompt(self) -> str:
        return """You are a social media analytics expert.

Your responsibilities:
1. Aggregate and analyze performance metrics across all platforms
2. Identify patterns in top-performing content
3. Generate actionable insights and recommendations
4. Forecast future performance trends
5. Compare performance to industry benchmarks
6. Calculate funnel metrics and conversion attribution

Key metrics to track:
- Engagement rate (by platform and content type)
- Reach and impressions
- Follower growth rate
- Click-through rate
- Conversion rate
- Share of voice
- Response time and rate
- Sentiment distribution
- Video view rate
- Story completion rate

Always provide:
- Context for metrics (vs previous period, vs benchmark)
- Actionable recommendations
- Statistical significance where applicable
- Clear visualizations suggestions
"""

    @tool
    def get_platform_metrics(
        self,
        platforms: list[str],
        start_date: datetime,
        end_date: datetime,
        metrics: list[str] | None = None,
    ) -> dict:
        """Get aggregated metrics for specified platforms."""
        metrics = metrics or [
            "followers", "posts", "impressions", "reach",
            "engagements", "likes", "comments", "shares",
            "clicks", "video_views",
        ]
        
        results = {}
        
        for platform in platforms:
            query = f"""
            SELECT 
                COUNT(*) as post_count,
                SUM(impressions) as total_impressions,
                SUM(reach) as total_reach,
                SUM(engagements) as total_engagements,
                SUM(likes) as total_likes,
                SUM(comments) as total_comments,
                SUM(shares) as total_shares,
                SUM(clicks) as total_clicks,
                SUM(video_views) as total_video_views,
                AVG(engagement_rate::float) as avg_engagement_rate,
                MAX(follower_count) as current_followers,
                MIN(follower_count) as start_followers
            FROM social_media_posts
            WHERE platform = %s
              AND posted_at BETWEEN %s AND %s;
            """
            
            result = self.analytics_db.execute(query, (platform, start_date, end_date))
            
            if result:
                row = result[0]
                results[platform] = {
                    "post_count": row["post_count"],
                    "total_impressions": row["total_impressions"],
                    "total_reach": row["total_reach"],
                    "total_engagements": row["total_engagements"],
                    "engagement_rate": (
                        row["total_engagements"] / max(row["total_impressions"], 1)
                    ),
                    "follower_growth": (
                        row["current_followers"] - row["start_followers"]
                    ),
                    "follower_growth_rate": (
                        (row["current_followers"] - row["start_followers"])
                        / max(row["start_followers"], 1)
                    ),
                    "avg_engagement_rate": row["avg_engagement_rate"],
                    "total_clicks": row["total_clicks"],
                    "total_video_views": row["total_video_views"],
                }
        
        return results

    @tool
    def get_content_performance(
        self,
        platform: str,
        content_type: str | None = None,
        limit: int = 20,
        sort_by: str = "engagement_rate",
    ) -> list[dict]:
        """Get top performing content."""
        query = """
        SELECT 
            id,
            content_text,
            content_type,
            posted_at,
            impressions,
            reach,
            engagements,
            likes,
            comments,
            shares,
            clicks,
            engagement_rate,
            sentiment_score
        FROM social_media_posts
        WHERE platform = %s
        {content_type_filter}
        ORDER BY {sort_by} DESC
        LIMIT %s;
        """
        
        params = [platform, limit]
        content_type_filter = ""
        
        if content_type:
            content_type_filter = "AND content_type = %s"
            params.insert(1, content_type)
        
        query = query.format(
            content_type_filter=content_type_filter,
            sort_by=sort_by,
        )
        
        return self.analytics_db.execute(query, params)

    @tool
    def generate_analytics_report(
        self,
        report_type: str = "weekly",
        platforms: list[str] | None = None,
        campaign_id: str | None = None,
    ) -> dict:
        """Generate a comprehensive analytics report."""
        platforms = platforms or ["twitter", "instagram", "linkedin"]
        
        # Determine date range
        if report_type == "daily":
            start_date = datetime.utcnow() - timedelta(days=1)
            end_date = datetime.utcnow()
        elif report_type == "weekly":
            start_date = datetime.utcnow() - timedelta(days=7)
            end_date = datetime.utcnow()
        elif report_type == "monthly":
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
        else:
            start_date = datetime.utcnow() - timedelta(days=90)
            end_date = datetime.utcnow()
        
        # Gather data
        platform_metrics = self.get_platform_metrics(
            platforms, start_date, end_date
        )
        
        top_content = {}
        for platform in platforms:
            top_content[platform] = self.get_content_performance(
                platform, limit=10
            )
        
        # Get previous period for comparison
        period_length = end_date - start_date
        prev_start = start_date - period_length
        prev_end = start_date
        
        prev_metrics = self.get_platform_metrics(
            platforms, prev_start, prev_end
        )
        
        # Generate insights
        prompt = f"""Generate a {report_type} social media analytics report:
        
        Current period metrics: {platform_metrics}
        Previous period metrics: {prev_metrics}
        Top performing content: {top_content}
        Report type: {report_type}
        Campaign ID: {campaign_id}
        
        Include:
        1. Executive summary with key highlights
        2. Platform-by-platform breakdown
        3. Period-over-period changes (with % change)
        4. Top performing content analysis
        5. Audience growth analysis
        6. Engagement quality assessment
        7. Benchmark comparison
        8. Key insights and patterns
        9. Recommendations for next period
        
        Format as structured JSON suitable for dashboard display.
        """
        
        report = self.llm.invoke(prompt)
        return report

    @tool
    def identify_top_performers(
        self,
        platform: str,
        criteria: str = "engagement_rate",
        content_type: str | None = None,
        time_window: str = "30d",
    ) -> dict:
        """Identify patterns in top-performing content."""
        # Get top 10% of content
        query = """
        WITH ranked_content AS (
            SELECT *,
                NTILE(10) OVER (ORDER BY engagement_rate DESC) as percentile
            FROM social_media_posts
            WHERE platform = %s
              AND posted_at > NOW() - INTERVAL %s
            {content_type_filter}
        )
        SELECT 
            content_type,
            AVG(engagement_rate) as avg_engagement,
            AVG(LENGTH(content_text)) as avg_length,
            MODE() WITHIN GROUP (ORDER BY EXTRACT(HOUR FROM posted_at)) as common_posting_hour,
            MODE() WITHIN GROUP (ORDER BY EXTRACT(DOW FROM posted_at)) as common_posting_day,
            COUNT(*) as post_count
        FROM ranked_content
        WHERE percentile = 1
        GROUP BY content_type;
        """
        
        # Also get common themes
        top_posts = self.get_content_performance(
            platform, content_type, limit=50, sort_by=criteria
        )
        
        # Analyze themes with LLM
        prompt = f"""Analyze these top-performing posts and identify common patterns:
        
        Posts: {[p['content_text'][:200] for p in top_posts]}
        
        Identify:
        1. Common themes and topics
        2. Content structure patterns
        3. Hashtag usage patterns
        4. CTA patterns
        5. Emotional triggers
        6. Format preferences
        
        Return JSON with pattern analysis.
        """
        
        patterns = self.llm.invoke(prompt)
        
        return {
            "top_performer_patterns": patterns,
            "content_type_breakdown": self.analytics_db.execute(query, (platform, time_window)),
            "sample_top_posts": top_posts[:10],
        }

    @tool
    def analyze_posting_patterns(self, platform: str, days: int = 90) -> dict:
        """Analyze optimal posting patterns from historical data."""
        query = """
        SELECT 
            EXTRACT(HOUR FROM posted_at) as hour,
            EXTRACT(DOW FROM posted_at) as day_of_week,
            content_type,
            AVG(engagement_rate) as avg_engagement,
            AVG(reach) as avg_reach,
            COUNT(*) as post_count
        FROM social_media_posts
        WHERE platform = %s
          AND posted_at > NOW() - INTERVAL '%s days'
        GROUP BY hour, day_of_week, content_type
        HAVING COUNT(*) >= 3
        ORDER BY avg_engagement DESC;
        """
        
        patterns = self.analytics_db.execute(query, (platform, days))
        
        # Find best times
        best_times = {}
        for row in patterns:
            day = row["day_of_week"]
            if day not in best_times:
                best_times[day] = []
            best_times[day].append({
                "hour": row["hour"],
                "engagement": row["avg_engagement"],
                "content_type": row["content_type"],
                "confidence": min(row["post_count"] / 10, 1.0),
            })
        
        return {
            "optimal_posting_times": best_times,
            "best_content_types": self._rank_content_types(patterns),
            "posting_frequency_analysis": self._analyze_frequency(patterns),
            "recommendations": self._generate_timing_recommendations(patterns),
        }

    @tool
    def forecast_performance(
        self,
        platform: str,
        forecast_days: int = 30,
        confidence_interval: float = 0.95,
    ) -> dict:
        """Forecast future performance using historical trends."""
        # Get historical data
        query = """
        SELECT 
            DATE(posted_at) as date,
            COUNT(*) as posts,
            SUM(impressions) as impressions,
            SUM(engagements) as engagements,
            AVG(engagement_rate) as engagement_rate,
            MAX(follower_count) as followers
        FROM social_media_posts
        WHERE platform = %s
          AND posted_at > NOW() - INTERVAL '90 days'
        GROUP BY DATE(posted_at)
        ORDER BY date;
        """
        
        historical = self.analytics_db.execute(query, (platform,))
        
        # Simple trend analysis (in production, use Prophet or similar)
        # This is a simplified version
        import numpy as np
        
        followers = [h["followers"] for h in historical]
        engagement_rates = [h["engagement_rate"] for h in historical]
        
        # Calculate trends
        follower_trend = np.polyfit(range(len(followers)), followers, 1)
        engagement_trend = np.polyfit(range(len(engagement_rates)), engagement_rates, 1)
        
        # Forecast
        forecast = []
        last_date = historical[-1]["date"] if historical else datetime.utcnow()
        
        for i in range(1, forecast_days + 1):
            forecast_date = last_date + timedelta(days=i)
            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted_followers": int(
                    follower_trend[0] * (len(followers) + i) + follower_trend[1]
                ),
                "predicted_engagement_rate": max(
                    0,
                    engagement_trend[0] * (len(engagement_rates) + i) + engagement_trend[1]
                ),
            })
        
        return {
            "platform": platform,
            "forecast_period_days": forecast_days,
            "forecast": forecast,
            "trend_direction": "up" if follower_trend[0] > 0 else "down",
            "confidence": confidence_interval,
            "model": "linear_trend",
        }

    @tool
    def compare_to_benchmarks(
        self, platform: str, metrics: dict
    ) -> dict:
        """Compare performance to industry benchmarks."""
        benchmarks = self.benchmark_data.get(platform, {})
        
        comparison = {}
        for metric, value in metrics.items():
            benchmark = benchmarks.get(metric)
            if benchmark:
                comparison[metric] = {
                    "actual": value,
                    "benchmark": benchmark,
                    "difference": value - benchmark,
                    "difference_percent": (
                        (value - benchmark) / max(benchmark, 0.001) * 100
                    ),
                    "status": "above" if value > benchmark else "below",
                    "percentile": self._estimate_percentile(value, benchmark),
                }
        
        return comparison

    @tool
    def generate_recommendations(
        self,
        analytics_data: dict,
        goals: dict,
    ) -> list[dict]:
        """Generate actionable recommendations based on analytics."""
        prompt = f"""Based on this analytics data, generate specific recommendations:
        
        Analytics: {analytics_data}
        Goals: {goals}
        
        For each recommendation, provide:
        1. Clear, actionable recommendation
        2. Expected impact (high/medium/low)
        3. Implementation effort (high/medium/low)
        4. Priority score (1-10)
        5. Specific steps to implement
        6. Success metrics to track
        
        Focus on:
        - Content strategy improvements
        - Posting time optimization
        - Audience growth tactics
        - Engagement improvement
        - Platform-specific opportunities
        
        Return JSON array of recommendations.
        """
        
        return self.llm.invoke(prompt)

    @tool
    def calculate_funnel_metrics(
        self,
        platform: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Calculate social media funnel metrics."""
        query = """
        SELECT 
            SUM(impressions) as total_impressions,
            SUM(reach) as total_reach,
            SUM(clicks) as total_clicks,
            SUM(conversions) as total_conversions,
            SUM(engagements) as total_engagements,
            AVG(ctr) as avg_ctr,
            AVG(conversion_rate) as avg_conversion_rate
        FROM social_media_posts
        WHERE platform = %s
          AND posted_at BETWEEN %s AND %s;
        """
        
        result = self.analytics_db.execute(query, (platform, start_date, end_date))
        
        if result:
            row = result[0]
            impressions = row["total_impressions"] or 0
            clicks = row["total_clicks"] or 0
            conversions = row["total_conversions"] or 0
            
            return {
                "impressions": impressions,
                "reach": row["total_reach"],
                "engagements": row["total_engagements"],
                "clicks": clicks,
                "conversions": conversions,
                "ctr": clicks / max(impressions, 1),
                "click_to_conversion": conversions / max(clicks, 1),
                "overall_conversion": conversions / max(impressions, 1),
                "funnel_stages": {
                    "awareness": impressions,
                    "interest": row["total_engagements"],
                    "consideration": clicks,
                    "conversion": conversions,
                },
            }
        
        return {}
```

### 7.3 Analytics Pipeline

```
Raw Data → ETL → Data Warehouse → Aggregation → ML Models → Insights → Dashboard
                                                                    ↓
                                                              Automated Reports
                                                                    ↓
                                                              Slack/Email Alerts
```

---

## 8. Code Examples and Snippets

### 8.1 Complete Orchestrator Setup

```python
from langgraph.graph import StateGraph, END
from langchain_deepagents import DeepAgent

def create_social_media_orchestrator():
    """Create the complete multi-agent orchestrator."""
    
    # Initialize all agents
    content_agent = ContentCreationAgent(
        brand_voice=load_brand_voice(),
        vector_store=load_vector_store(),
    )
    
    scheduling_agent = SchedulingAgent(
        analytics_db=load_analytics_db(),
        platform_configs=load_platform_configs(),
    )
    
    engagement_agent = EngagementAgent(
        brand_voice=load_brand_voice(),
        escalation_rules=load_escalation_rules(),
    )
    
    listening_agent = SocialListeningAgent(
        brand_keywords=load_brand_keywords(),
        competitor_handles=load_competitor_handles(),
    )
    
    influencer_agent = InfluencerIdentificationAgent(
        brand_profile=load_brand_profile(),
        campaign_criteria=load_campaign_criteria(),
    )
    
    analytics_agent = PerformanceAnalyticsAgent(
        analytics_db=load_analytics_db(),
        benchmark_data=load_benchmark_data(),
    )
    
    # Build the graph
    workflow = StateGraph(SocialMediaState)
    
    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("content_creation", content_agent)
    workflow.add_node("scheduling", scheduling_agent)
    workflow.add_node("engagement", engagement_agent)
    workflow.add_node("listening", listening_agent)
    workflow.add_node("influencer", influencer_agent)
    workflow.add_node("analytics", analytics_agent)
    
    # Define edges
    workflow.set_entry_point("orchestrator")
    
    workflow.add_conditional_edges(
        "orchestrator",
        route_to_agent,
        {
            "content_creation": "content_creation",
            "scheduling": "scheduling",
            "engagement": "engagement",
            "listening": "listening",
            "influencer": "influencer",
            "analytics": "analytics",
            "end": END,
        },
    )
    
    # All agents return to orchestrator
    for agent in [
        "content_creation", "scheduling", "engagement",
        "listening", "influencer", "analytics",
    ]:
        workflow.add_edge(agent, "orchestrator")
    
    return workflow.compile(checkpointer=MemorySaver())
```

### 8.2 Platform API Adapter Pattern

```python
from abc import ABC, abstractmethod

class PlatformAdapter(ABC):
    """Abstract base class for social media platform adapters."""
    
    @abstractmethod
    def get_mentions(self, handles: list[str], since: datetime) -> list[dict]:
        pass
    
    @abstractmethod
    def post_content(self, content: dict) -> dict:
        pass
    
    @abstractmethod
    def get_user_metrics(self, user_id: str) -> dict:
        pass
    
    @abstractmethod
    def search_posts(self, query: str, **kwargs) -> list[dict]:
        pass

class TwitterAdapter(PlatformAdapter):
    """Twitter/X API adapter."""
    
    def __init__(self, bearer_token: str):
        self.client = tweepy.Client(bearer_token=bearer_token)
    
    def get_mentions(self, handles: list[str], since: datetime) -> list[dict]:
        query = " OR ".join([f"@{h}" for h in handles])
        tweets = self.client.search_recent_tweets(
            query=query,
            start_time=since,
            tweet_fields=["created_at", "author_id", "public_metrics"],
        )
        return [self._normalize_tweet(t) for t in (tweets.data or [])]
    
    def post_content(self, content: dict) -> dict:
        if content.get("media"):
            # Upload media first
            media_ids = [self.client.upload_media(m) for m in content["media"]]
            response = self.client.create_tweet(
                text=content["text"],
                media_ids=media_ids,
            )
        else:
            response = self.client.create_tweet(text=content["text"])
        return {"id": response.data["id"], "url": f"https://twitter.com/i/status/{response.data['id']}"}
    
    def _normalize_tweet(self, tweet) -> dict:
        return {
            "id": str(tweet.id),
            "text": tweet.text,
            "author_id": str(tweet.author_id),
            "created_at": tweet.created_at.isoformat(),
            "platform": "twitter",
            "metrics": tweet.public_metrics,
        }

class PlatformAdapterFactory:
    """Factory for creating platform adapters."""
    
    _adapters = {}
    
    @classmethod
    def get_adapter(cls, platform: str) -> PlatformAdapter:
        if platform not in cls._adapters:
            config = load_platform_config(platform)
            
            if platform == "twitter":
                cls._adapters[platform] = TwitterAdapter(config["bearer_token"])
            elif platform == "instagram":
                cls._adapters[platform] = InstagramAdapter(config["access_token"])
            elif platform == "linkedin":
                cls._adapters[platform] = LinkedInAdapter(config["access_token"])
            # Add more platforms...
        
        return cls._adapters[platform]
```

### 8.3 FastAPI Integration

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="Social Media AI Agent API")

# Initialize orchestrator
orchestrator = create_social_media_orchestrator()

class CampaignRequest(BaseModel):
    name: str
    goals: dict
    platforms: list[str]
    start_date: datetime
    end_date: datetime
    budget: float | None = None

class ContentRequest(BaseModel):
    topic: str
    platforms: list[str]
    content_type: str = "standard"
    count: int = 3

@app.post("/campaigns")
async def create_campaign(request: CampaignRequest):
    """Create and launch a new social media campaign."""
    result = await orchestrator.ainvoke({
        "messages": [{"role": "user", "content": f"Launch campaign: {request.dict()}"}],
        "current_agent": "orchestrator",
        "campaign_context": request.dict(),
    })
    return {"campaign_id": result.get("campaign_id"), "status": "launched"}

@app.post("/content/generate")
async def generate_content(request: ContentRequest):
    """Generate social media content."""
    result = await orchestrator.ainvoke({
        "messages": [{"role": "user", "content": request.dict()}],
        "current_agent": "content_creation",
    })
    return {"content": result.get("content_queue", [])}

@app.get("/analytics/{platform}")
async def get_analytics(
    platform: str,
    start_date: datetime,
    end_date: datetime,
):
    """Get analytics for a platform."""
    result = await orchestrator.ainvoke({
        "messages": [{"role": "user", "content": f"Get analytics for {platform} from {start_date} to {end_date}"}],
        "current_agent": "analytics",
    })
    return result.get("analytics_data", {})

@app.get("/listening/report")
async def get_listening_report(
    report_type: str = "daily",
    platforms: list[str] = Query(["twitter", "instagram"]),
):
    """Get social listening report."""
    result = await orchestrator.ainvoke({
        "messages": [{"role": "user", "content": f"Generate {report_type} listening report for {platforms}"}],
        "current_agent": "listening",
    })
    return result.get("listening_results", {})

@app.post("/influencers/discover")
async def discover_influencers(
    niche: str,
    platforms: list[str],
    min_followers: int = 10000,
    max_followers: int = 1000000,
):
    """Discover influencers in a niche."""
    result = await orchestrator.ainvoke({
        "messages": [{"role": "user", "content": f"Find influencers in {niche} on {platforms}"}],
        "current_agent": "influencer",
    })
    return {"influencers": result.get("influencer_candidates", [])}
```

### 8.4 Celery Task Queue Integration

```python
from celery import Celery

celery_app = Celery("social_media", broker="redis://localhost:6379/0")

@celery_app.task
def publish_scheduled_post(schedule_id: str):
    """Publish a scheduled post."""
    # Get schedule entry
    schedule = db.get_schedule_entry(schedule_id)
    
    # Get platform adapter
    adapter = PlatformAdapterFactory.get_adapter(schedule["platform"])
    
    # Publish
    result = adapter.post_content(schedule["content"])
    
    # Update status
    db.update_schedule_status(schedule_id, "published", result)
    
    return result

@celery_app.task
def run_engagement_monitor():
    """Periodic task to monitor engagement."""
    orchestrator = create_social_media_orchestrator()
    
    result = orchestrator.invoke({
        "messages": [{"role": "user", "content": "Run engagement monitoring cycle"}],
        "current_agent": "engagement",
    })
    
    return result

@celery_app.task
def run_listening_report():
    """Generate daily listening report."""
    orchestrator = create_social_media_orchestrator()
    
    result = orchestrator.invoke({
        "messages": [{"role": "user", "content": "Generate daily listening report"}],
        "current_agent": "listening",
    })
    
    # Send report via email/Slack
    send_report_notification(result)
    
    return result

# Schedule periodic tasks
celery_app.conf.beat_schedule = {
    "engagement-monitor": {
        "task": "run_engagement_monitor",
        "schedule": 300.0,  # Every 5 minutes
    },
    "listening-report": {
        "task": "run_listening_report",
        "schedule": 86400.0,  # Daily
    },
}
```

### 8.5 Database Schema

```sql
-- Core tables for the social media management system

CREATE TABLE social_media_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    external_id VARCHAR(255),
    content_text TEXT NOT NULL,
    content_type VARCHAR(50),
    media_urls JSONB,
    posted_at TIMESTAMP WITH TIME ZONE,
    campaign_id UUID,
    schedule_id UUID,
    
    -- Metrics
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    engagements INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    video_views INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,4),
    sentiment_score DECIMAL(3,2),
    
    -- Metadata
    author_id VARCHAR(255),
    author_handle VARCHAR(255),
    follower_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE content_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content JSONB NOT NULL,
    platform VARCHAR(50) NOT NULL,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    campaign_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    external_id VARCHAR(255)
);

CREATE TABLE social_media_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    external_id VARCHAR(255),
    text TEXT NOT NULL,
    author_id VARCHAR(255),
    author_handle VARCHAR(255),
    author_followers INTEGER,
    author_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE,
    first_response_at TIMESTAMP WITH TIME ZONE,
    sentiment VARCHAR(50),
    category VARCHAR(50),
    priority INTEGER,
    status VARCHAR(50) DEFAULT 'new'
);

CREATE TABLE influencers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handle VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    name VARCHAR(255),
    bio TEXT,
    followers INTEGER,
    following INTEGER,
    engagement_rate DECIMAL(5,4),
    category VARCHAR(100),
    email VARCHAR(255),
    score DECIMAL(5,2),
    tier VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    goals JSONB,
    platforms JSONB,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    budget DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE analytics_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    followers INTEGER,
    posts INTEGER,
    impressions INTEGER,
    reach INTEGER,
    engagements INTEGER,
    engagement_rate DECIMAL(5,4),
    clicks INTEGER,
    conversions INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(platform, date)
);

-- Indexes for common queries
CREATE INDEX idx_posts_platform_posted ON social_media_posts(platform, posted_at DESC);
CREATE INDEX idx_posts_campaign ON social_media_posts(campaign_id);
CREATE INDEX idx_schedule_status_time ON content_schedule(status, scheduled_time);
CREATE INDEX idx_mentions_platform_created ON social_media_mentions(platform, created_at DESC);
CREATE INDEX idx_mentions_status ON social_media_mentions(status);
CREATE INDEX idx_analytics_platform_date ON analytics_daily(platform, date DESC);
```

---

## 9. Testing Strategy

### 9.1 Testing Pyramid

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

### 9.2 Unit Tests

```python
# tests/test_content_agent.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

class TestContentCreationAgent:
    
    @pytest.fixture
    def agent(self):
        brand_voice = {
            "tone": "professional",
            "style": "conversational",
            "values": ["innovation", "trust"],
            "avoid": ["slang", "jargon"],
            "emoji_usage": "minimal",
        }
        vector_store = Mock()
        return ContentCreationAgent(brand_voice, vector_store)
    
    def test_generate_post_returns_valid_structure(self, agent):
        """Test that generate_post returns properly structured content."""
        with patch.object(agent.llm, 'invoke') as mock_invoke:
            mock_invoke.return_value = {
                "text": "Test post content",
                "hashtags": ["#test", "#ai"],
                "alt_text": "Test alt text",
                "cta": "Learn more",
            }
            
            result = agent.generate_post(
                topic="AI in marketing",
                platform="twitter",
                tone="professional",
            )
            
            assert "text" in result
            assert "hashtags" in result
            assert isinstance(result["hashtags"], list)
    
    def test_generate_post_respects_character_limit(self, agent):
        """Test that generated posts respect platform character limits."""
        with patch.object(agent.llm, 'invoke') as mock_invoke:
            mock_invoke.return_value = {
                "text": "x" * 300,  # Over Twitter limit
                "hashtags": ["#test"],
            }
            
            result = agent.generate_post(
                topic="Test",
                platform="twitter",
                max_length=280,
            )
            
            # Agent should truncate or regenerate
            assert len(result["text"]) <= 280
    
    def test_search_past_performing_content_filters_correctly(self, agent):
        """Test that vector store search applies correct filters."""
        agent.vector_store.similarity_search.return_value = []
        
        agent.search_past_performing_content(
            topic="AI marketing",
            platform="twitter",
        )
        
        agent.vector_store.similarity_search.assert_called_once_with(
            query="AI marketing",
            k=5,
            filter={"platform": "twitter", "engagement_rate": {"$gt": 0.05}},
        )
    
    def test_score_content_returns_numeric_scores(self, agent):
        """Test that content scoring returns valid numeric scores."""
        with patch.object(agent.llm, 'invoke') as mock_invoke:
            mock_invoke.return_value = {
                "engagement_potential": 8,
                "brand_alignment": 9,
                "clarity": 7,
                "shareability": 6,
            }
            
            result = agent.score_content("Test content", "twitter")
            
            assert all(
                isinstance(result[k], (int, float))
                for k in ["engagement_potential", "brand_alignment", "clarity", "shareability"]
            )


class TestSchedulingAgent:
    
    @pytest.fixture
    def agent(self):
        analytics_db = Mock()
        platform_configs = {"twitter": {"max_posts_per_day": 5}}
        return SchedulingAgent(analytics_db, platform_configs)
    
    def test_check_schedule_conflicts_detects_overlap(self, agent):
        """Test that scheduling conflicts are properly detected."""
        agent.analytics_db.execute.return_value = [
            {"id": "existing-1", "scheduled_time": "2026-10-01T10:00:00Z"}
        ]
        
        conflicts = agent.check_schedule_conflicts(
            platform="twitter",
            proposed_time=datetime(2026, 10, 1, 10, 15),
            window_minutes=30,
        )
        
        assert len(conflicts) == 1
    
    def test_schedule_post_creates_celery_task(self, agent):
        """Test that scheduling creates a Celery task."""
        agent.analytics_db.execute.return_value = []  # No conflicts
        
        with patch('social_media_impl.publish_task') as mock_task:
            result = agent.schedule_post(
                content={"text": "Test post"},
                platform="twitter",
                scheduled_time=datetime(2026, 10, 1, 10, 0),
            )
            
            mock_task.apply_async.assert_called_once()
            assert result["status"] == "scheduled"


class TestEngagementAgent:
    
    @pytest.fixture
    def agent(self):
        brand_voice = {"tone": "friendly", "emoji_usage": "moderate"}
        escalation_rules = {"crisis_threshold": 20}
        return EngagementAgent(brand_voice, escalation_rules)
    
    def test_detect_crisis_triggers_on_viral_negative(self, agent):
        """Test crisis detection with viral negative content."""
        mentions = [
            {"sentiment": "negative", "share_count": 1500, "author_followers": 50000}
            for _ in range(5)
        ]
        
        result = agent.detect_crisis(mentions)
        
        assert result["crisis_detected"] is True
        assert result["severity"] == "high"
    
    def test_identify_advocates_filters_correctly(self, agent):
        """Test advocate identification logic."""
        mentions = [
            {"author_handle": "advocate1", "sentiment": "positive", "author_followers": 5000},
            {"author_handle": "advocate1", "sentiment": "positive", "author_followers": 5000},
            {"author_handle": "advocate1", "sentiment": "positive", "author_followers": 5000},
            {"author_handle": "troll1", "sentiment": "negative", "author_followers": 100},
        ]
        
        advocates = agent.identify_advocates(mentions, min_engagement=2)
        
        assert len(advocates) == 1
        assert advocates[0]["handle"] == "advocate1"
    
    def test_generate_response_matches_brand_voice(self, agent):
        """Test that generated responses align with brand voice."""
        with patch.object(agent.llm, 'invoke') as mock_invoke:
            mock_invoke.return_value = {
                "response": "Thanks for reaching out! We'd love to help.",
                "tone": "friendly",
                "requires_approval": False,
            }
            
            result = agent.generate_response(
                original_post={
                    "text": "I love your product!",
                    "author_handle": "user123",
                    "platform": "twitter",
                },
                sentiment={"primary": "positive"},
            )
            
            assert "response" in result
            assert result["tone"] == "friendly"
```

### 9.3 Integration Tests

```python
# tests/integration/test_agent_pipeline.py
import pytest
import asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

class TestAgentPipeline:
    """Integration tests for the complete agent pipeline."""
    
    @pytest.fixture(scope="module")
    def postgres(self):
        with PostgresContainer("postgres:15") as pg:
            yield pg
    
    @pytest.fixture(scope="module")
    def redis(self):
        with RedisContainer("redis:7") as redis:
            yield redis
    
    @pytest.fixture
    def orchestrator(self, postgres, redis):
        """Create orchestrator with test containers."""
        # Configure with test containers
        config = {
            "database_url": postgres.get_connection_url(),
            "redis_url": redis.get_connection_url(),
        }
        return create_social_media_orchestrator(config)
    
    @pytest.mark.asyncio
    async def test_content_creation_to_scheduling_pipeline(self, orchestrator):
        """Test complete content creation and scheduling flow."""
        result = await orchestrator.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Create and schedule a post about our new AI feature for Twitter"
            }],
            "current_agent": "orchestrator",
        })
        
        assert "content_queue" in result
        assert len(result["content_queue"]) > 0
        assert result["current_agent"] in ["scheduling", "orchestrator"]
    
    @pytest.mark.asyncio
    async def test_engagement_monitoring_flow(self, orchestrator):
        """Test engagement monitoring with mock data."""
        result = await orchestrator.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Check for new mentions and respond to any questions"
            }],
            "current_agent": "engagement",
        })
        
        assert "engagement_tasks" in result
    
    @pytest.mark.asyncio
    async def test_analytics_report_generation(self, orchestrator):
        """Test analytics report generation."""
        result = await orchestrator.ainvoke({
            "messages": [{
                "role": "user",
                "content": "Generate weekly analytics report for all platforms"
            }],
            "current_agent": "analytics",
        })
        
        assert "analytics_data" in result
```

### 9.4 End-to-End Tests

```python
# tests/e2e/test_social_media_workflow.py
import pytest
from datetime import datetime, timedelta

class TestSocialMediaWorkflow:
    """End-to-end tests for complete social media workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_campaign_lifecycle(self, e2e_env):
        """Test complete campaign from creation to analytics."""
        api_client = e2e_env.api_client
        
        # 1. Create campaign
        campaign = await api_client.post("/campaigns", json={
            "name": "Q4 Product Launch",
            "goals": {"awareness": 100000, "engagement": 5000},
            "platforms": ["twitter", "instagram", "linkedin"],
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        })
        campaign_id = campaign["campaign_id"]
        
        # 2. Generate content
        content = await api_client.post("/content/generate", json={
            "topic": "New AI product launch",
            "platforms": ["twitter", "instagram"],
            "content_type": "announcement",
            "count": 5,
        })
        assert len(content["content"]) >= 5
        
        # 3. Schedule content
        for item in content["content"]:
            schedule = await api_client.post("/schedule", json={
                "content": item,
                "platform": item["platform"],
                "scheduled_time": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                "campaign_id": campaign_id,
            })
            assert schedule["status"] == "scheduled"
        
        # 4. Check listening
        listening = await api_client.get("/listening/report", params={
            "report_type": "daily",
            "platforms": ["twitter", "instagram"],
        })
        assert "brand_mentions" in listening
        
        # 5. Get analytics
        analytics = await api_client.get(f"/analytics/{campaign_id}")
        assert "metrics" in analytics
    
    @pytest.mark.asyncio
    async def test_crisis_detection_and_escalation(self, e2e_env):
        """Test crisis detection workflow."""
        # Simulate viral negative mentions
        mock_mentions = [
            {
                "text": "This product is terrible! @yourbrand",
                "author_handle": "influencer1",
                "author_followers": 100000,
                "share_count": 5000,
                "sentiment": "negative",
            }
            for _ in range(10)
        ]
        
        # Inject mock mentions
        e2e_env.inject_mentions(mock_mentions)
        
        # Run engagement monitoring
        result = await e2e_env.orchestrator.ainvoke({
            "messages": [{"role": "user", "content": "Run engagement monitoring"}],
            "current_agent": "engagement",
        })
        
        # Verify crisis was detected
        assert result.get("crisis_detected") is True
        assert result.get("escalation_status") == "escalated"
```

### 9.5 Performance Tests

```python
# tests/performance/test_agent_performance.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

class TestAgentPerformance:
    """Performance tests for agent operations."""
    
    @pytest.mark.benchmark
    def test_content_generation_speed(self, benchmark):
        """Benchmark content generation speed."""
        agent = create_content_agent()
        
        result = benchmark(
            agent.generate_post,
            topic="AI marketing",
            platform="twitter",
        )
        
        assert result is not None
    
    @pytest.mark.benchmark
    def test_engagement_monitoring_speed(self, benchmark):
        """Benchmark engagement monitoring with 1000 mentions."""
        agent = create_engagement_agent()
        mock_mentions = generate_mock_mentions(1000)
        
        result = benchmark(
            agent.categorize_engagement,
            mock_mentions,
        )
        
        assert result is not None
    
    def test_concurrent_scheduling(self):
        """Test concurrent scheduling operations."""
        agent = create_scheduling_agent()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    agent.schedule_post,
                    content={"text": f"Post {i}"},
                    platform="twitter",
                    scheduled_time=datetime.utcnow() + timedelta(hours=i),
                )
                for i in range(100)
            ]
            
            results = [f.result() for f in futures]
        
        # All should succeed without conflicts
        assert all(r["status"] in ["scheduled", "conflict"] for r in results)
    
    def test_analytics_query_performance(self):
        """Test analytics query performance with large dataset."""
        agent = create_analytics_agent()
        
        start = time.time()
        result = agent.get_platform_metrics(
            platforms=["twitter", "instagram", "linkedin"],
            start_date=datetime.utcnow() - timedelta(days=90),
            end_date=datetime.utcnow(),
        )
        duration = time.time() - start
        
        # Should complete within 2 seconds
        assert duration < 2.0
```

### 9.6 Mock Data Generators

```python
# tests/fixtures/mock_data.py
import random
from datetime import datetime, timedelta

def generate_mock_mentions(count: int = 100) -> list[dict]:
    """Generate mock social media mentions for testing."""
    sentiments = ["positive", "neutral", "negative"]
    weights = [0.4, 0.4, 0.2]
    
    mentions = []
    for i in range(count):
        sentiment = random.choices(sentiments, weights=weights)[0]
        mentions.append({
            "id": f"mention-{i}",
            "text": f"Test mention {i} with #{random.choice(['AI', 'tech', 'marketing'])}",
            "author_handle": f"user{random.randint(1, 1000)}",
            "author_id": f"user-id-{random.randint(1, 1000)}",
            "author_followers": random.randint(100, 100000),
            "author_verified": random.random() < 0.1,
            "platform": random.choice(["twitter", "instagram", "linkedin"]),
            "created_at": (datetime.utcnow() - timedelta(hours=random.randint(0, 24))).isoformat(),
            "sentiment": sentiment,
            "like_count": random.randint(0, 100),
            "share_count": random.randint(0, 50),
            "comment_count": random.randint(0, 30),
        })
    
    return mentions

def generate_mock_posts(count: int = 50) -> list[dict]:
    """Generate mock social media posts for testing."""
    posts = []
    for i in range(count):
        posted_at = datetime.utcnow() - timedelta(days=random.randint(0, 90))
        impressions = random.randint(1000, 100000)
        engagements = random.randint(10, int(impressions * 0.1))
        
        posts.append({
            "id": f"post-{i}",
            "platform": random.choice(["twitter", "instagram", "linkedin"]),
            "content_text": f"Test post content {i}",
            "content_type": random.choice(["text", "image", "video", "link"]),
            "posted_at": posted_at.isoformat(),
            "impressions": impressions,
            "reach": int(impressions * 0.8),
            "engagements": engagements,
            "likes": int(engagements * 0.6),
            "comments": int(engagements * 0.2),
            "shares": int(engagements * 0.2),
            "clicks": random.randint(0, int(engagements * 0.3)),
            "engagement_rate": engagements / max(impressions, 1),
        })
    
    return posts
```

### 9.7 Test Configuration

```yaml
# tests/pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    benchmark: Performance benchmark tests
    integration: Integration tests requiring external services
    e2e: End-to-end tests
    slow: Tests that take longer than 10 seconds

# tests/conftest.py
import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests",
    )

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: mark test as slow to run"
    )

def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
```

### 9.8 CI/CD Test Pipeline

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
      - run: pip install -e ".[test]"
      - run: pytest tests/unit -v --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[test]"
      - run: pytest tests/integration -v
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[test]"
      - run: pytest tests/e2e -v --run-slow
```

---

## Appendix A: Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install langchain-deepagents langgraph langchain-openai
pip install fastapi uvicorn celery redis
pip install psycopg2-binary chromadb
pip install tweepy instagrapi
pip install pytest pytest-asyncio pytest-benchmark

# Set up environment variables
export OPENAI_API_KEY="sk-..."
export DATABASE_URL="postgresql://user:pass@localhost:5432/social_media"
export REDIS_URL="redis://localhost:6379/0"
export TWITTER_BEARER_TOKEN="..."
export INSTAGRAM_ACCESS_TOKEN="..."
export LINKEDIN_ACCESS_TOKEN="..."

# Run migrations
alembic upgrade head

# Start services
redis-server
celery -A social_media worker --loglevel=info
celery -A social_media beat --loglevel=info
uvicorn social_media.api:app --reload
```

## Appendix B: Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  API Server │  │  API Server │  │  API Server │         │
│  │   (FastAPI) │  │   (FastAPI) │  │   (FastAPI) │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         └─────────────────┼─────────────────┘                │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────┐        │
│  │              Celery Worker Pool                  │        │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │        │
│  │  │Worker 1│ │Worker 2│ │Worker 3│ │Worker N│   │        │
│  │  └────────┘ └────────┘ └────────┘ └────────┘   │        │
│  └────────────────────────┬────────────────────────┘        │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────┐        │
│  │              Data Layer                           │        │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │        │
│  │  │PostgreSQL│ │ Redis  │ │ChromaDB│ │S3 Bucket│   │        │
│  │  └────────┘ └────────┘ └────────┘ └────────┘   │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

*End of Implementation Plan*
