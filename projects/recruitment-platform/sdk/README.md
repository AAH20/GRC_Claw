# Recruitment Platform Python SDK

A production-grade Python client for the [Recruitment Platform](../README.md) REST API. Provides typed access to all 42 endpoints across 10 recruitment domains with automatic retries, authentication, and comprehensive error handling.

## Installation

```bash
pip install -e ./sdk
```

## Quick Start

```python
from recruitment_platform_sdk import RecruitmentPlatformClient

# Initialize the client
client = RecruitmentPlatformClient(
    base_url="http://localhost:8000",
    api_key="your-api-key",  # optional
)

# Check API health
health = client.health_check()
print(f"Status: {health.status}")  # "healthy"

# Parse a resume
from recruitment_platform_sdk import ResumeParseRequest

result = client.parse_resume(ResumeParseRequest(text="John Doe\nSoftware Engineer\nPython, AWS, Kubernetes"))
print(result.skills)  # ["Python", "AWS", "Kubernetes"]
```

## Features

- **Type-safe**: Full Pydantic models for all requests and responses
- **Authentication**: Bearer token support via `api_key` parameter
- **Retries**: Automatic exponential backoff for rate limits and server errors
- **Error handling**: Custom exceptions for each HTTP error category
- **Context manager**: Use with `with` statement for automatic cleanup
- **Async-ready**: Built on `httpx` for future async support

## API Domains

### Health
- `health_check()` — Check API health
- `readiness_check()` — Check API readiness

### Resume Parser
- `parse_resume(request)` — Parse resume into structured data
- `extract_contact(request)` — Extract contact information
- `extract_skills(request)` — Extract skills

### Candidate Matcher
- `match_candidates(request)` — Match candidates to job
- `explain_match(request)` — Explain a match decision
- `analyze_gap(request)` — Analyze skills gap

### Interview Scheduler
- `optimize_slots(request)` — Find optimal interview slots
- `detect_conflicts(request)` — Detect scheduling conflicts
- `send_reminder(request)` — Send interview reminder

### Skills Assessor
- `assess_skills(request)` — Assess candidate skills
- `recommend_learning_path(request)` — Recommend learning path
- `validate_skills(request)` — Validate claimed skills

### Bias Detector
- `analyze_language(request)` — Detect biased language
- `compute_fairness(request)` — Compute fairness metrics
- `analyze_demographics(request)` — Analyze demographics
- `get_bias_recommendations(request)` — Get mitigation recommendations

### Talent Pool Manager
- `source_candidates(request)` — Source candidates
- `analyze_pool(request)` — Analyze pool health
- `recommend_talent(request)` — Recommend talent
- `track_engagement(request)` — Track engagement

### Recruitment Analytics
- `analyze_cost(request)` — Analyze recruitment costs
- `analyze_funnel(request)` — Analyze funnel
- `get_diversity_metrics(request)` — Get diversity metrics
- `predict_hiring(request)` — Generate hiring predictions
- `analyze_source_effectiveness(request)` — Analyze source effectiveness

### Onboarding Automator
- `check_compliance(request)` — Check compliance
- `generate_documents(request)` — Generate documents
- `track_progress(request)` — Track progress
- `schedule_tasks(request)` — Schedule tasks
- `generate_welcome_message(request)` — Generate welcome message

### Job Description Optimizer
- `check_ats(request)` — Check ATS compatibility
- `remove_bias(request)` — Remove biased language
- `optimize_keywords(request)` — Optimize keywords
- `optimize_seo(request)` — Optimize for SEO
- `analyze_tone(request)` — Analyze tone

### Employer Branding
- `develop_brand_strategy(request)` — Develop brand strategy
- `generate_content(request)` — Generate content
- `manage_reputation(request)` — Manage reputation
- `analyze_reviews(request)` — Analyze reviews
- `analyze_sentiment(request)` — Analyze sentiment

## Error Handling

```python
from recruitment_platform_sdk import (
    RecruitmentPlatformClient,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

client = RecruitmentPlatformClient(base_url="http://localhost:8000")

try:
    result = client.parse_resume(ResumeParseRequest(text="..."))
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Invalid request: {e.message}")
except RateLimitError:
    print("Rate limit exceeded, try again later")
except ServerError:
    print("Server error, try again later")
except NotFoundError:
    print("Resource not found")
```

## Context Manager

```python
with RecruitmentPlatformClient(base_url="http://localhost:8000") as client:
    health = client.health_check()
    print(health.status)
# Client automatically closed
```

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | required | API base URL |
| `api_key` | `str \| None` | `None` | Bearer token for authentication |
| `timeout` | `float` | `30.0` | Request timeout in seconds |
| `max_retries` | `int` | `3` | Maximum retry attempts |

## Requirements

- Python 3.12+
- `httpx>=0.27.0`
- `pydantic>=2.7.0`
- `tenacity>=8.3.0`

## License

MIT
