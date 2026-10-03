# Recruitment Platform API Documentation

## Table of Contents

1. [Overview](#overview)
2. [OpenAPI 3.1 Specification](#openapi-31-specification)
3. [Authentication Guide](#authentication-guide)
4. [Rate Limiting](#rate-limiting)
5. [Error Handling](#error-handling)
6. [SDK Usage Examples](#sdk-usage-examples)
7. [Webhook Documentation](#webhook-documentation)
8. [Integration Guide](#integration-guide)
9. [Endpoint Reference](#endpoint-reference)

---

## Overview

The Recruitment Platform API provides programmatic access to 42 AI-powered endpoints across 10 recruitment domains. Built with FastAPI, the platform offers resume parsing, candidate matching, interview scheduling, skills assessment, bias detection, talent pool management, recruitment analytics, onboarding automation, job description optimization, and employer branding.

### Base URLs

| Environment | URL |
|-------------|-----|
| Local Development | `http://localhost:8000/api/v1` |
| Staging | `https://staging-api.example.com/api/v1` |
| Production | `https://api.example.com/api/v1` |

### Response Envelope

All endpoints return a standard JSON envelope:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "metadata": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message",
  "details": [
    {
      "field": "text",
      "message": "Field is required",
      "code": "required"
    }
  ]
}
```

### Versioning

The API uses URL path versioning. Current version: **v1**.

```
/api/v1/resume-parser/parse
```

---

## OpenAPI 3.1 Specification

The complete OpenAPI 3.1 specification is available at [`/docs/openapi.json`](../openapi.json) or interactively at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key OpenAPI Features

- **JSON Schema 2020-12** compliance
- **Bearer token** authentication via `Authorization` header
- **Standard HTTP status codes** (200, 400, 401, 404, 422, 429, 500)
- **Pydantic v2** models with strict validation
- **OpenAPI 3.1** features: `examples`, `const`, `if/then/else` schemas

### Spec Summary

```yaml
openapi: 3.1.0
info:
  title: Recruitment Platform API
  version: 1.0.0
  description: >
    Unified AI-powered recruitment automation platform with 42 endpoints
    across 10 domains including resume parsing, candidate matching,
    interview scheduling, bias detection, and employer branding.
  contact:
    name: API Support
    email: support@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT
servers:
  - url: http://localhost:8000/api/v1
    description: Local development server
  - url: https://api.example.com/api/v1
    description: Production server
tags:
  - name: health
  - name: resume-parser
  - name: candidate-matcher
  - name: interview-scheduler
  - name: skills-assessor
  - name: bias-detector
  - name: talent-pool
  - name: analytics
  - name: onboarding
  - name: job-description
  - name: employer-branding
paths:
  # 42 endpoints total (see Endpoint Reference section)
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    AgentResponse:
      type: object
      properties:
        success: { type: boolean }
        data: { type: object }
        error: { type: string }
        metadata: { type: object }
    HealthResponse:
      type: object
      properties:
        status: { type: string, example: "healthy" }
        service: { type: string, example: "recruitment-platform" }
        version: { type: string }
        timestamp: { type: string, format: date-time }
    Error:
      type: object
      properties:
        success: { type: boolean, example: false }
        error: { type: string }
        details:
          type: array
          items: { type: object }
```

---

## Authentication Guide

### Overview

The Recruitment Platform API uses **Bearer token** authentication. All requests must include a valid API key in the `Authorization` header.

### Obtaining an API Key

1. Navigate to the Developer Portal at `https://portal.example.com`
2. Create a new application or select an existing one
3. Generate an API key from the "API Keys" section
4. Store the key securely (environment variable or secrets manager)

### Using the API Key

Include the API key in the `Authorization` header for every request:

```
Authorization: Bearer <your-api-key>
```

**Environment Variable (recommended):**
```bash
export RECRUITMENT_API_KEY="your-api-key-here"
```

**cURL:**
```bash
curl -H "Authorization: Bearer $RECRUITMENT_API_KEY" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/v1/health
```

**Python:**
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/health",
        headers={"Authorization": "Bearer your-api-key-here"}
    )
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/health', {
  headers: {
    'Authorization': 'Bearer your-api-key-here',
    'Content-Type': 'application/json'
  }
});
```

### SDK Authentication

```python
from recruitment_platform_sdk import RecruitmentPlatformClient

client = RecruitmentPlatformClient(
    base_url="http://localhost:8000",
    api_key="your-api-key-here"
)
```

### Authentication Errors

| Status Code | Error | Resolution |
|-------------|-------|------------|
| 401 | `AuthenticationError` | Invalid or expired API key |
| 403 | `Forbidden` | Insufficient permissions |

### Security Best Practices

- **Never hardcode API keys** in source code
- **Use environment variables** or a secrets manager (AWS Secrets Manager, HashiCorp Vault)
- **Rotate keys** regularly (recommended: every 90 days)
- **Scope keys** to specific environments (dev/staging/prod)
- **Monitor usage** through the Developer Portal dashboard
- **Use HTTPS** in production (enforced at the load balancer level)

---

## Rate Limiting

### Overview

The API enforces rate limiting via NGINX ingress with the following configuration:

| Zone | Rate | Burst | Scope |
|------|------|-------|-------|
| `api` | 10 req/s | 20 | All `/api/*` endpoints |
| `login` | 5 req/min | 5 | Authentication endpoints |

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1672531200
X-RateLimit-Retry-After: 5
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed per window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |
| `X-RateLimit-Retry-After` | Seconds to wait before retrying (429 only) |

### Rate Limit Tiers

| Tier | Requests/min | Requests/day | Burst |
|------|-------------|-------------|-------|
| Free | 60 | 10,000 | 10 |
| Pro | 600 | 100,000 | 50 |
| Enterprise | 6,000 | 1,000,000 | 200 |

### Handling Rate Limits

**429 Response:**
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "retry_after": 30
}
```

**Best Practices:**
1. **Exponential backoff**: Wait `2^attempt` seconds between retries
2. **Jitter**: Add random delay to avoid thundering herd
3. **Circuit breaker**: Stop requests after consecutive 429s
4. **Request batching**: Combine multiple operations into single requests
5. **Caching**: Cache responses where appropriate

**Python SDK (automatic retry):**
```python
from recruitment_platform_sdk import RecruitmentPlatformClient

# SDK automatically retries with exponential backoff
client = RecruitmentPlatformClient(
    base_url="http://localhost:8000",
    api_key="your-key",
    max_retries=3
)
```

**Manual retry logic:**
```python
import asyncio
import httpx

async def make_request_with_retry(url, headers, json_data, max_retries=3):
    async with httpx.AsyncClient() as client:
        for attempt in range(max_retries):
            response = await client.post(url, headers=headers, json=json_data)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                await asyncio.sleep(retry_after)
                continue
            return response
```

---

## Error Handling Guide

### Error Response Format

All errors follow a consistent format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "details": [
    {
      "field": "field_name",
      "message": "Specific field error",
      "code": "error_code"
    }
  ]
}
```

### HTTP Status Codes

| Code | Name | When It Occurs |
|------|------|----------------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Malformed request syntax |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 405 | Method Not Allowed | HTTP method not supported |
| 409 | Conflict | Resource state conflict |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Service temporarily down |
| 504 | Gateway Timeout | Upstream service timeout |

### Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `authentication_failed` | 401 | Invalid or expired API key |
| `permission_denied` | 403 | Insufficient permissions |
| `resource_not_found` | 404 | Requested resource not found |
| `validation_error` | 422 | Request validation failed |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_error` | 500 | Unexpected server error |
| `service_unavailable` | 503 | Service temporarily unavailable |

### SDK Error Handling

```python
from recruitment_platform_sdk import (
    RecruitmentPlatformClient,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    RecruitmentPlatformError,
)

client = RecruitmentPlatformClient(
    base_url="http://localhost:8000",
    api_key="your-key"
)

try:
    result = client.parse_resume(ResumeParseRequest(text="..."))
except AuthenticationError as e:
    print(f"Auth failed: {e.message} (status: {e.status_code})")
    # Refresh API key or notify user
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    for detail in e.response_body.get("details", []):
        print(f"  - {detail['field']}: {detail['message']}")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.response_body.get('retry_after')}s")
    # Implement backoff strategy
except ServerError as e:
    print(f"Server error: {e.message}")
    # Retry with exponential backoff
except NotFoundError as e:
    print(f"Resource not found: {e.message}")
except RecruitmentPlatformError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
```

### Common Error Scenarios

**Missing required field (422):**
```json
{
  "success": false,
  "error": "Request validation failed",
  "details": [
    {
      "field": "text",
      "message": "Field required",
      "code": "missing"
    }
  ]
}
```

**Invalid JSON (400):**
```json
{
  "success": false,
  "error": "Invalid JSON in request body"
}
```

**Rate limit exceeded (429):**
```json
{
  "success": false,
  "error": "Rate limit exceeded. Try again in 30 seconds.",
  "retry_after": 30
}
```

**Server error (500):**
```json
{
  "success": false,
  "error": "Internal server error",
  "request_id": "req-abc123"
}
```

---

## SDK Usage Examples

### Installation

```bash
pip install -e ./sdk
```

### Quick Start

```python
from recruitment_platform_sdk import RecruitmentPlatformClient

# Initialize client
client = RecruitmentPlatformClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Health check
health = client.health_check()
print(f"Status: {health.status}")  # "healthy"

# Parse a resume
from recruitment_platform_sdk import ResumeParseRequest

result = client.parse_resume(ResumeParseRequest(
    text="John Doe\njohn@example.com\nPython, AWS, Kubernetes"
))
print(result.skills)  # ["Python", "AWS", "Kubernetes"]
```

### Context Manager (Recommended)

```python
from recruitment_platform_sdk import RecruitmentPlatformClient

with RecruitmentPlatformClient(
    base_url="http://localhost:8000",
    api_key="your-key"
) as client:
    health = client.health_check()
    print(health.status)
# Client automatically closed
```

### All Domain Examples

#### Resume Parser

```python
from recruitment_platform_sdk import (
    ResumeParseRequest,
    ContactExtractionRequest,
    SkillsExtractionRequest,
)

# Parse full resume
result = client.parse_resume(ResumeParseRequest(
    text="John Doe\njohn@example.com\n(555) 123-4567\n\nSkills: Python, AWS"
))
print(result.skills)       # ["Python", "AWS"]
print(result.email)        # "john@example.com"

# Extract contact only
contact = client.extract_contact(ContactExtractionRequest(
    text="Email: test@example.com\nPhone: (555) 987-6543"
))
print(contact.email)       # "test@example.com"
print(contact.phone)       # "(555) 987-6543"

# Extract skills only
skills = client.extract_skills(SkillsExtractionRequest(
    text="Experienced in Python, JavaScript, React, Node.js"
))
print(skills.skills)       # ["python", "javascript", "react", "node"]
```

#### Candidate Matcher

```python
from recruitment_platform_sdk import (
    CandidateMatchRequest,
    MatchExplanationRequest,
    GapAnalysisRequest,
)

# Match candidates
matches = client.match_candidates(CandidateMatchRequest(
    candidates=[
        {"id": "c1", "name": "Jane", "skills": ["Python", "AWS"]},
        {"id": "c2", "name": "Bob", "skills": ["Java", "GCP"]}
    ],
    job_requirements={
        "title": "Senior Software Engineer",
        "required_skills": ["Python", "AWS", "Kubernetes"]
    }
))
print(matches.matches)  # Ranked list of candidates

# Explain a match
explanation = client.explain_match(MatchExplanationRequest(
    candidate={"id": "c1", "skills": ["Python", "AWS"]},
    job={"title": "Senior SWE", "required_skills": ["Python", "AWS", "K8s"]},
    match_result={"score": 0.85}
))
print(explanation.explanation)

# Gap analysis
gap = client.analyze_gap(GapAnalysisRequest(
    candidate_skills=["Python", "AWS"],
    required_skills=["Python", "AWS", "Kubernetes"]
))
print(gap.gaps)      # ["Kubernetes"]
print(gap.matches)   # ["Python", "AWS"]
print(gap.coverage)  # 0.667
```

#### Interview Scheduler

```python
from recruitment_platform_sdk import (
    InterviewSlotRequest,
    ConflictDetectionRequest,
    ReminderRequest,
)

# Optimize slots
slots = client.optimize_slots(InterviewSlotRequest(
    participants=[
        {
            "id": "user-1",
            "name": "Interviewer A",
            "availability": [
                {"start": "2024-01-15T09:00:00Z", "end": "2024-01-15T17:00:00Z"}
            ]
        }
    ],
    duration_minutes=60,
    preferred_days=["Monday", "Tuesday"]
))
print(slots.slots)  # Optimal time slots

# Detect conflicts
conflicts = client.detect_conflicts(ConflictDetectionRequest(
    proposed_slot={"start": "2024-01-15T14:00:00Z", "end": "2024-01-15T15:00:00Z"},
    existing_events=[
        {"title": "Standup", "start": "2024-01-15T14:30:00Z", "end": "2024-01-15T15:00:00Z"}
    ]
))
print(conflicts.conflicts)  # Detected conflicts

# Send reminder
reminder = client.send_reminder(ReminderRequest(
    interview={"id": "int-001", "candidate": "Jane", "time": "2024-01-15T14:00:00Z"},
    reminder_type="email"
))
print(reminder.delivered)  # True
```

#### Skills Assessor

```python
from recruitment_platform_sdk import (
    SkillsAssessmentRequest,
    LearningPathRequest,
    SkillValidationRequest,
)

# Assess skills
assessment = client.assess_skills(SkillsAssessmentRequest(
    skill_assessments=[
        {"skill": "Python", "level": 0.9},
        {"skill": "AWS", "level": 0.75}
    ]
))
print(assessment.assessments)

# Learning path
path = client.recommend_learning_path(LearningPathRequest(
    skill_gaps=["Kubernetes", "Terraform"],
    career_goals=["DevOps Engineer"]
))
print(path.path)

# Validate skills
validation = client.validate_skills(SkillValidationRequest(
    claimed_skills=["Python", "AWS"],
    evidence={
        "assessments": {"Python": 0.9},
        "work_history": ["Used AWS in production for 3 years"]
    }
))
print(validation.validated)
```

#### Bias Detector

```python
from recruitment_platform_sdk import (
    BiasLanguageRequest,
    FairnessScoreRequest,
    DemographicAnalysisRequest,
    BiasRecommendationRequest,
)

# Analyze language
bias = client.analyze_language(BiasLanguageRequest(
    text="We need a young and energetic candidate who can work long hours"
))
print(bias.biased_phrases)
print(bias.suggestions)

# Fairness score
fairness = client.compute_fairness(FairnessScoreRequest(
    decisions=[
        {"candidate_id": "c1", "hired": True, "gender": "F"},
        {"candidate_id": "c2", "hired": False, "gender": "M"}
    ],
    protected_attributes=["gender", "race"]
))
print(fairness.scores)

# Demographic analysis
demo = client.analyze_demographics(DemographicAnalysisRequest(
    hiring_data=[{"total_applications": 1000, "hires": 50}],
    demographics=["gender", "race"]
))
print(demo.analysis)

# Recommendations
recs = client.get_bias_recommendations(BiasRecommendationRequest(
    bias_analysis={
        "language_biases": ["gendered_terms"],
        "demographic_disparities": ["gender_gap"]
    }
))
print(recs.recommendations)
```

#### Talent Pool Manager

```python
from recruitment_platform_sdk import (
    TalentSourceRequest,
    PoolAnalysisRequest,
    TalentRecommendRequest,
    EngagementTrackRequest,
)

# Source candidates
sourced = client.source_candidates(TalentSourceRequest(
    job_requirements={"title": "Senior SWE", "required_skills": ["Python", "AWS"]},
    pool_criteria={"min_experience_years": 3, "location": "Remote"}
))
print(sourced.candidates)

# Analyze pool
pool = client.analyze_pool(PoolAnalysisRequest(
    pool_data={"total_members": 500},
    hiring_needs={"open_positions": 10, "required_skills": ["Python", "AWS"]}
))
print(pool.health_score)
print(pool.insights)

# Recommend talent
recs = client.recommend_talent(TalentRecommendRequest(
    job={"title": "Senior SWE", "required_skills": ["Python", "AWS"]},
    pool_members=[{"id": "c1", "skills": ["Python", "AWS", "Docker"]}]
))
print(recs.recommendations)

# Track engagement
engagement = client.track_engagement(EngagementTrackRequest(
    candidate_id="cand-001",
    interactions=[
        {"type": "email_open", "timestamp": "2024-01-10T09:00:00Z"},
        {"type": "profile_view", "timestamp": "2024-01-12T14:00:00Z"}
    ]
))
print(engagement.engagement_score)
print(engagement.metrics)
```

#### Recruitment Analytics

```python
from recruitment_platform_sdk import (
    CostAnalysisRequest,
    FunnelAnalysisRequest,
    DiversityMetricsRequest,
    HiringPredictionRequest,
    SourceEffectivenessRequest,
)

# Cost analysis
cost = client.analyze_cost(CostAnalysisRequest(
    hiring_data=[{"total_hires": 50, "total_applications": 1000}],
    cost_data={"total_spend": 500000, "channel_costs": {"linkedin": 200000}}
))
print(cost.total_cost)
print(cost.breakdown)

# Funnel analysis
funnel = client.analyze_funnel(FunnelAnalysisRequest(
    funnel_data={
        "stages": ["applied", "screened", "interviewed", "offered", "hired"],
        "counts": [1000, 500, 200, 50, 30]
    }
))
print(funnel.conversion_rates)
print(funnel.bottlenecks)

# Diversity metrics
diversity = client.get_diversity_metrics(DiversityMetricsRequest(
    pipeline_data=[{"stages": ["applied", "hired"], "counts": [1000, 50]}],
    demographics=["gender", "race"]
))
print(diversity.metrics)

# Hiring prediction
prediction = client.predict_hiring(HiringPredictionRequest(
    historical_data=[{"avg_time_to_hire": 30, "avg_quality_score": 0.8}],
    current_pipeline={"open_positions": 10, "active_candidates": 50}
))
print(prediction.predictions)

# Source effectiveness
sources = client.analyze_source_effectiveness(SourceEffectivenessRequest(
    source_data={"linkedin": 200, "indeed": 150, "referrals": 50},
    outcomes={"linkedin": {"hires": 20}, "indeed": {"hires": 10}}
))
print(sources.effectiveness)
```

#### Onboarding Automator

```python
from recruitment_platform_sdk import (
    ComplianceCheckRequest,
    DocumentGenerationRequest,
    ProgressTrackRequest,
    TaskScheduleRequest,
    WelcomeMessageRequest,
)

# Check compliance
compliance = client.check_compliance(ComplianceCheckRequest(
    employee_data={"name": "Jane", "start_date": "2024-02-01", "role": "SWE"},
    jurisdiction="US"
))
print(compliance.compliant)
print(compliance.violations)

# Generate documents
docs = client.generate_documents(DocumentGenerationRequest(
    employee={"name": "Jane", "role": "SWE", "department": "Engineering"},
    template_config={"include_offer_letter": True, "include_policy_ack": True}
))
print(docs.documents)

# Track progress
progress = client.track_progress(ProgressTrackRequest(
    employee_id="emp-001",
    onboarding_plan={
        "tasks": [
            {"id": "t1", "name": "Complete I-9", "completed": True},
            {"id": "t2", "name": "Setup workstation", "completed": False}
        ]
    }
))
print(progress.progress_percentage)
print(progress.completed_tasks)
print(progress.pending_tasks)

# Schedule tasks
tasks = client.schedule_tasks(TaskScheduleRequest(
    employee={"name": "Jane", "role": "SWE"},
    start_date="2024-02-01"
))
print(tasks.tasks)

# Welcome message
welcome = client.generate_welcome_message(WelcomeMessageRequest(
    employee={"name": "Jane", "role": "SWE"},
    team_info={"name": "Platform Team", "manager": "John"}
))
print(welcome.message)
```

#### Job Description Optimizer

```python
from recruitment_platform_sdk import (
    ATSCompatibilityRequest,
    BiasRemovalRequest,
    KeywordOptimizationRequest,
    SEOOptimizationRequest,
    ToneAnalysisRequest,
)

# Check ATS compatibility
ats = client.check_ats(ATSCompatibilityRequest(
    job_description="We are looking for a Senior Software Engineer with 5+ years of Python and AWS."
))
print(ats.compatible)
print(ats.issues)

# Remove bias
cleaned = client.remove_bias(BiasRemovalRequest(
    job_description="We need a young, energetic salesman who can work long hours"
))
print(cleaned.cleaned_text)
print(cleaned.bias_report)

# Optimize keywords
keywords = client.optimize_keywords(KeywordOptimizationRequest(
    job_description="Looking for a software engineer to build web applications",
    target_role="Senior Software Engineer"
))
print(keywords.optimized_text)
print(keywords.keywords)

# Optimize SEO
seo = client.optimize_seo(SEOOptimizationRequest(
    job_description="Software Engineer position at a leading tech company",
    platform="linkedin"
))
print(seo.recommendations)

# Analyze tone
tone = client.analyze_tone(ToneAnalysisRequest(
    job_description="Join our amazing team! We're looking for a rockstar developer.",
    brand_voice="professional"
))
print(tone.tone)
print(tone.alignment)
```

#### Employer Branding

```python
from recruitment_platform_sdk import (
    BrandStrategyRequest,
    ContentGenerationRequest,
    ReputationManagementRequest,
    ReviewAnalysisRequest,
    SentimentAnalysisRequest,
)

# Brand strategy
strategy = client.develop_brand_strategy(BrandStrategyRequest(
    company_data={"name": "TechCorp", "industry": "Technology", "size": 500},
    target_audience={"demographics": "Software Engineers", "experience_level": "mid-to-senior"}
))
print(strategy.strategy)

# Generate content
content = client.generate_content(ContentGenerationRequest(
    content_type="social_media_post",
    brand_guidelines={"tone": "professional", "voice": "innovative"}
))
print(content.content)

# Manage reputation
reputation = client.manage_reputation(ReputationManagementRequest(
    platform_data={
        "glassdoor": {"rating": 4.2, "reviews": 150},
        "indeed": {"rating": 4.0, "reviews": 200}
    },
    reputation_metrics={"overall": 4.1, "trend": "improving"}
))
print(reputation.status)
print(reputation.actions)

# Analyze reviews
reviews = client.analyze_reviews(ReviewAnalysisRequest(
    reviews=[
        {"rating": 5, "text": "Great place to work!"},
        {"rating": 2, "text": "Poor management"}
    ],
    platform="glassdoor"
))
print(reviews.summary)
print(reviews.themes)

# Analyze sentiment
sentiment = client.analyze_sentiment(SentimentAnalysisRequest(
    texts=[
        "Great company with amazing culture",
        "Terrible work-life balance",
        "Decent place to grow your career"
    ]
))
print(sentiment.sentiment)
print(sentiment.scores)
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Parse resume
curl -X POST http://localhost:8000/api/v1/resume-parser/parse \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RECRUITMENT_API_KEY" \
  -d '{"text": "John Doe\nPython, AWS, Kubernetes"}'

# Match candidates
curl -X POST http://localhost:8000/api/v1/candidate-matcher/match \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RECRUITMENT_API_KEY" \
  -d '{
    "candidates": [{"id": "1", "skills": ["Python"]}],
    "job_requirements": {"required_skills": ["Python"]}
  }'

# Analyze bias
curl -X POST http://localhost:8000/api/v1/bias-detector/analyze-language \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RECRUITMENT_API_KEY" \
  -d '{"text": "We need a young and energetic candidate"}'
```

### JavaScript Examples

```javascript
const baseUrl = 'http://localhost:8000/api/v1';
const headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer your-api-key'
};

// Parse resume
const parseResume = async (text) => {
  const response = await fetch(`${baseUrl}/resume-parser/parse`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ text })
  });
  const { data } = await response.json();
  return data;
};

// Match candidates
const matchCandidates = async (candidates, jobRequirements) => {
  const response = await fetch(`${baseUrl}/candidate-matcher/match`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ candidates, job_requirements: jobRequirements })
  });
  const { data } = await response.json();
  return data;
};

// Health check
const healthCheck = async () => {
  const response = await fetch(`${baseUrl}/health`);
  return response.json();
};
```

---

## Webhook Documentation

### Overview

The Recruitment Platform supports webhooks for real-time event notifications. Webhooks allow your application to receive instant updates when events occur in the platform.

### Supported Events

| Event | Description | Payload |
|-------|-------------|---------|
| `resume.parsed` | Resume parsing completed | `{ resume_id, status, data }` |
| `candidate.matched` | Candidate matching completed | `{ job_id, matches, timestamp }` |
| `interview.scheduled` | Interview scheduled | `{ interview_id, slot, participants }` |
| `interview.reminder` | Interview reminder sent | `{ interview_id, reminder_type, status }` |
| `bias.detected` | Bias detected in content | `{ content_id, bias_type, severity }` |
| `talent.sourced` | Candidates sourced from pool | `{ job_id, candidates_count, timestamp }` |
| `analytics.completed` | Analytics job completed | `{ analysis_id, type, results_url }` |
| `onboarding.progress` | Onboarding progress update | `{ employee_id, progress, completed_tasks }` |
| `onboarding.completed` | Onboarding completed | `{ employee_id, completion_date }` |
| `jd.optimized` | Job description optimized | `{ jd_id, optimizations_applied }` |
| `brand.reputation_changed` | Reputation score changed | `{ platform, old_score, new_score }` |

### Webhook Payload Format

```json
{
  "event": "resume.parsed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "resume_id": "res-123",
    "status": "completed",
    "data": {
      "contact": {"email": "john@example.com"},
      "skills": ["Python", "AWS"]
    }
  },
  "metadata": {
    "request_id": "req-abc123",
    "webhook_id": "wh-def456"
  }
}
```

### Webhook Headers

| Header | Description |
|--------|-------------|
| `X-Webhook-Event` | Event type (e.g., `resume.parsed`) |
| `X-Webhook-Signature` | HMAC-SHA256 signature for verification |
| `X-Webhook-ID` | Unique webhook delivery ID |
| `X-Webhook-Timestamp` | Unix timestamp of the event |
| `X-Request-ID` | Request ID for tracing |

### Setting Up Webhooks

1. Navigate to the Developer Portal
2. Go to **Webhooks** -> **Add Webhook**
3. Enter your endpoint URL
4. Select events to subscribe to
5. Generate a webhook secret
6. Save configuration

### Verifying Webhook Signatures

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}
```

### Webhook Delivery

- **Retry policy**: 3 attempts with exponential backoff (1s, 5s, 25s)
- **Timeout**: 10 seconds per attempt
- **Success criteria**: HTTP 2xx response
- **Failure handling**: Failed deliveries logged for 30 days

### Webhook Endpoint Example

```python
from fastapi import FastAPI, Request, Header, HTTPException
import hmac
import hashlib

app = FastAPI()
WEBHOOK_SECRET = "your-webhook-secret"

@app.post("/webhooks/recruitment")
async def handle_webhook(
    request: Request,
    x_webhook_signature: str = Header(None),
    x_webhook_event: str = Header(None)
):
    payload = await request.body()

    # Verify signature
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, x_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = await request.json()

    # Handle event
    if x_webhook_event == "resume.parsed":
        handle_resume_parsed(event["data"])
    elif x_webhook_event == "candidate.matched":
        handle_candidate_matched(event["data"])
    # ... handle other events

    return {"status": "ok"}
```

---

## Integration Guide

### Architecture Overview

```
+-------------------------------------------------------------+
|                     Load Balancer (NGINX)                    |
|                   Rate Limiting + SSL/TLS                    |
+----------------------------+--------------------------------+
                             |
+----------------------------v--------------------------------+
|                    FastAPI Application                       |
|  +-------------+  +-------------+  +---------------------+  |
|  |   Health    |  |   Resume    |  |  Candidate Matcher  |  |
|  |  Endpoints  |  |   Parser    |  |                     |  |
|  +-------------+  +-------------+  +---------------------+  |
|  +-------------+  +-------------+  +---------------------+  |
|  |  Interview  |  |   Skills    |  |   Bias Detector     |  |
|  |  Scheduler  |  |  Assessor   |  |                     |  |
|  +-------------+  +-------------+  +---------------------+  |
|  +-------------+  +-------------+  +---------------------+  |
|  |   Talent    |  |  Analytics  |  |     Onboarding      |  |
|  |    Pool     |  |             |  |                     |  |
|  +-------------+  +-------------+  +---------------------+  |
|  +-------------+  +-------------+                          |
|  |     Job     |  |  Employer   |                          |
|  | Description |  |  Branding   |                          |
|  +-------------+  +-------------+                          |
+----------------------------+--------------------------------+
                             |
+----------------------------v--------------------------------+
|              External Service Integrations                   |
|  +----------+ +----------+ +----------+ +--------------+    |
|  |  OpenAI  | |  Redis   | |  Vector  | |  File Store  |    |
|  |  Client  | |  Cache   | |  Store   | |  (S3/Local)  |    |
|  +----------+ +----------+ +----------+ +--------------+    |
|  +----------+ +----------+ +----------+ +--------------+    |
|  |  ATS     | | Calendar | | LinkedIn | |  Glassdoor   |    |
|  |  Client  | |  Sync    | |  Client  | |   Client     |    |
|  +----------+ +----------+ +----------+ +--------------+    |
+-------------------------------------------------------------+
```

### Integration Patterns

#### 1. Synchronous Request-Response

Best for: Real-time operations, simple integrations

```python
# Simple synchronous call
result = client.parse_resume(ResumeParseRequest(text="..."))
```

#### 2. Asynchronous Processing with Webhooks

Best for: Long-running operations, high-volume processing

```python
# Submit job
job = client.submit_batch_job(JobRequest(
    type="resume_parsing",
    data={"resumes": [...]}
))

# Receive webhook when complete
# POST /webhooks/recruitment
# Event: batch.completed
```

#### 3. Event-Driven Architecture

Best for: Microservices, decoupled systems

```
+----------+     +----------+     +----------+
|  Your    +---->+  Kafka   +---->+  Worker  |
|   App    |     |  Topic   |     |  Service |
+----------+     +----------+     +----------+
                                      |
                                      v
                               +----------+
                               | Recruit  |
                               | Platform |
                               +----------+
```

#### 4. Batch Processing

Best for: Bulk operations, data migration

```python
# Process multiple resumes
resumes = [{"text": "..."}, {"text": "..."}, ...]
results = []

for resume in resumes:
    result = client.parse_resume(ResumeParseRequest(text=resume["text"]))
    results.append(result)
```

### Integration Checklist

- [ ] Obtain API key from Developer Portal
- [ ] Configure environment variables
- [ ] Set up webhook endpoint (if using async)
- [ ] Implement error handling and retries
- [ ] Configure rate limit handling
- [ ] Set up monitoring and alerting
- [ ] Test in staging environment
- [ ] Review security best practices
- [ ] Document integration for your team

### Common Integration Scenarios

#### ATS Integration

```python
# Sync candidates from ATS to Recruitment Platform
def sync_candidates(ats_client):
    candidates = ats_client.get_candidates()
    for candidate in candidates:
        # Parse resume
        result = client.parse_resume(ResumeParseRequest(
            text=candidate["resume_text"]
        ))
        # Match to open positions
        matches = client.match_candidates(CandidateMatchRequest(
            candidates=[result.model_dump()],
            job_requirements={"required_skills": ["Python", "AWS"]}
        ))
        # Update ATS with match scores
        ats_client.update_candidate_score(
            candidate["id"],
            matches.matches[0]["score"]
        )
```

#### HRMS Integration

```python
# Sync onboarding status to HRMS
def sync_onboarding(employee_id):
    progress = client.track_progress(ProgressTrackRequest(
        employee_id=employee_id,
        onboarding_plan=get_onboarding_plan(employee_id)
    ))
    # Update HRMS
    hrms_client.update_onboarding_status(
        employee_id=employee_id,
        progress=progress.progress_percentage,
        completed_tasks=progress.completed_tasks
    )
```

#### Calendar Integration

```python
# Sync interviews to calendar
def schedule_interview(candidate_id, interviewer_ids):
    # Get availability
    slots = client.optimize_slots(InterviewSlotRequest(
        participants=[
            {"id": id, "availability": get_availability(id)}
            for id in interviewer_ids
        ],
        duration_minutes=60
    ))
    # Book calendar event
    calendar_client.create_event(
        title=f"Interview: {candidate_id}",
        start=slots.slots[0]["start"],
        end=slots.slots[0]["end"],
        attendees=interviewer_ids
    )
    # Send reminder
    client.send_reminder(ReminderRequest(
        interview={"candidate": candidate_id, "time": slots.slots[0]["start"]},
        reminder_type="email"
    ))
```

### Testing Your Integration

```python
import pytest
from recruitment_platform_sdk import RecruitmentPlatformClient

@pytest.fixture
def client():
    with RecruitmentPlatformClient(
        base_url="http://localhost:8000",
        api_key="test-key"
    ) as c:
        yield c

def test_health_check(client):
    health = client.health_check()
    assert health.status == "healthy"

def test_parse_resume(client):
    result = client.parse_resume(ResumeParseRequest(
        text="John Doe\nPython, AWS"
    ))
    assert "Python" in result.skills

def test_match_candidates(client):
    result = client.match_candidates(CandidateMatchRequest(
        candidates=[{"id": "1", "skills": ["Python"]}],
        job_requirements={"required_skills": ["Python"]}
    ))
    assert len(result.matches) > 0
```

---

## Endpoint Reference

### Health Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/ready` | Readiness check |

### Resume Parser (3 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/resume-parser/parse` | Parse resume into structured data |
| POST | `/api/v1/resume-parser/extract-contact` | Extract contact information |
| POST | `/api/v1/resume-parser/extract-skills` | Extract skills from text |

### Candidate Matcher (3 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/candidate-matcher/match` | Match candidates to job |
| POST | `/api/v1/candidate-matcher/explain` | Explain match decision |
| POST | `/api/v1/candidate-matcher/gap-analysis` | Analyze skills gap |

### Interview Scheduler (3 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/interview-scheduler/optimize-slots` | Find optimal interview slots |
| POST | `/api/v1/interview-scheduler/detect-conflicts` | Detect scheduling conflicts |
| POST | `/api/v1/interview-scheduler/send-reminder` | Send interview reminder |

### Skills Assessor (3 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/skills-assessor/assess` | Assess candidate skills |
| POST | `/api/v1/skills-assessor/learning-path` | Recommend learning path |
| POST | `/api/v1/skills-assessor/validate-skills` | Validate claimed skills |

### Bias Detector (4 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/bias-detector/analyze-language` | Detect biased language |
| POST | `/api/v1/bias-detector/fairness-score` | Compute fairness metrics |
| POST | `/api/v1/bias-detector/demographic-analysis` | Analyze demographics |
| POST | `/api/v1/bias-detector/recommendations` | Get mitigation recommendations |

### Talent Pool Manager (4 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/talent-pool/source` | Source candidates from pool |
| POST | `/api/v1/talent-pool/analyze-pool` | Analyze pool health |
| POST | `/api/v1/talent-pool/recommend` | Recommend talent |
| POST | `/api/v1/talent-pool/track-engagement` | Track engagement |

### Recruitment Analytics (5 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analytics/cost-analysis` | Analyze recruitment costs |
| POST | `/api/v1/analytics/funnel-analysis` | Analyze funnel conversion |
| POST | `/api/v1/analytics/diversity-metrics` | Get diversity metrics |
| POST | `/api/v1/analytics/predict` | Generate hiring predictions |
| POST | `/api/v1/analytics/source-effectiveness` | Analyze source effectiveness |

### Onboarding Automator (5 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/onboarding/check-compliance` | Check compliance |
| POST | `/api/v1/onboarding/generate-documents` | Generate documents |
| POST | `/api/v1/onboarding/track-progress` | Track progress |
| POST | `/api/v1/onboarding/schedule-tasks` | Schedule tasks |
| POST | `/api/v1/onboarding/welcome-message` | Generate welcome message |

### Job Description Optimizer (5 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/job-description/check-ats` | Check ATS compatibility |
| POST | `/api/v1/job-description/remove-bias` | Remove biased language |
| POST | `/api/v1/job-description/optimize-keywords` | Optimize keywords |
| POST | `/api/v1/job-description/optimize-seo` | Optimize for SEO |
| POST | `/api/v1/job-description/analyze-tone` | Analyze tone |

### Employer Branding (5 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/employer-branding/brand-strategy` | Develop brand strategy |
| POST | `/api/v1/employer-branding/generate-content` | Generate content |
| POST | `/api/v1/employer-branding/manage-reputation` | Manage reputation |
| POST | `/api/v1/employer-branding/analyze-reviews` | Analyze reviews |
| POST | `/api/v1/employer-branding/analyze-sentiment` | Analyze sentiment |

---

## Summary

| Category | Count |
|----------|-------|
| Total Endpoints | 42 |
| Domains | 10 |
| Health Endpoints | 2 |
| Resume Parser | 3 |
| Candidate Matcher | 3 |
| Interview Scheduler | 3 |
| Skills Assessor | 3 |
| Bias Detector | 4 |
| Talent Pool Manager | 4 |
| Recruitment Analytics | 5 |
| Onboarding Automator | 5 |
| Job Description Optimizer | 5 |
| Employer Branding | 5 |

---

## Support

- **Documentation**: https://docs.example.com
- **API Status**: https://status.example.com
- **Developer Portal**: https://portal.example.com
- **Email**: support@example.com
- **Issues**: https://github.com/example/recruitment-platform/issues

---

*Last updated: 2024-01-15*
