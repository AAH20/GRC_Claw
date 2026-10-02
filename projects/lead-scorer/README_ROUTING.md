# Lead Routing & Nurture Guide

## Overview

The Lead Scorer system includes intelligent lead routing and automated nurture capabilities that work alongside the scoring and qualification agents to create a complete lead lifecycle management solution.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Lead Scorer System                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Research │  │ Evidence │  │ Scoring  │  │   Qual   │  │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │              │        │
│       └──────────────┴──────────────┴──────────────┘        │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │   Lead Routing    │                    │
│                    │      Agent        │                    │
│                    └─────────┬─────────┘                    │
│                              │                              │
│              ┌───────────────┼───────────────┐              │
│              │               │               │              │
│     ┌────────▼───────┐ ┌────▼─────┐ ┌───────▼───────┐     │
│     │     Sales      │ │ Nurture  │ │   Marketing   │     │
│     │   (Hot Leads)  │ │  Agent   │ │ (Cold Leads)  │     │
│     └────────────────┘ └────┬─────┘ └───────────────┘     │
│                              │                              │
│                    ┌─────────▼─────────┐                    │
│                    │  Scoring V2       │                    │
│                    │  (Ensemble)       │                    │
│                    └───────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Lead Routing

### How It Works

The routing agent evaluates leads against configurable rules to determine the optimal destination:

1. **Sales** — Hot, qualified leads ready for immediate engagement
2. **Sales Development** — Warm leads needing qualification
3. **Nurture** — Cold or warm leads that need continued engagement
4. **Marketing** — Disqualified or very cold leads
5. **Account Executive** — High-value enterprise leads
6. **Disqualify** — Leads that don't fit the ideal customer profile

### Routing Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `priority` | Route based on lead score and grade | Most use cases |
| `round_robin` | Distribute evenly across reps | Small teams |
| `skill_based` | Match lead industry to rep skills | Diverse portfolios |
| `territory` | Route by geographic location | Regional sales teams |
| `load_balanced` | Distribute based on current workload | Large teams |

### Routing Rules

Rules are evaluated in order (by `order` field). The first matching rule determines the destination.

```python
from lead_scorer.agents.lead_routing import LeadRoutingAgent, RoutingContext
from lead_scorer.models.routing import RoutingRule, RouteDestination, RoutingPriority

agent = LeadRoutingAgent()

# Add a rule for hot tech leads
agent.add_rule(RoutingRule(
    id="rule-hot-tech",
    name="Hot Tech Leads to AE",
    destination=RouteDestination.ACCOUNT_EXECUTIVE,
    priority=RoutingPriority.CRITICAL,
    score_threshold=85.0,
    grade_filter=["hot"],
    industry_filter=["Technology", "Software"],
    company_size_min=100,
    order=1,
))

# Route a lead
context = RoutingContext(
    lead_id="lead-123",
    score=90.0,
    grade="hot",
    industry="Technology",
    company_size=250,
)
decision = await agent.route(context)
print(decision.destination)  # RouteDestination.ACCOUNT_EXECUTIVE
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/routing/route` | Route a single lead |
| POST | `/api/v1/routing/batch` | Route multiple leads |
| GET | `/api/v1/routing/rules` | List all routing rules |
| POST | `/api/v1/routing/rules` | Create a routing rule |
| PUT | `/api/v1/routing/rules/{id}` | Update a routing rule |
| DELETE | `/api/v1/routing/rules/{id}` | Delete a routing rule |
| GET | `/api/v1/routing/stats` | Get assignment statistics |
| POST | `/api/v1/routing/reset-stats` | Reset assignment counters |

## Lead Nurture

### How It Works

The nurture agent manages automated sequences that engage cold and warm leads over time:

1. **Enrollment** — Leads are enrolled in nurture sequences based on routing decisions
2. **Step Execution** — Each sequence has ordered steps (emails, calls, LinkedIn)
3. **Engagement Tracking** — Opens, clicks, and responses are tracked
4. **Exit Evaluation** — Leads exit nurture when they become hot or qualified

### Creating a Nurture Sequence

```python
from lead_scorer.agents.lead_nurture import LeadNurtureAgent
from lead_scorer.models.routing import NurtureSequenceCreate

agent = LeadNurtureAgent()

# Create a 5-step nurture sequence
sequence = agent.create_sequence(NurtureSequenceCreate(
    name="Cold Lead Nurture",
    description="90-day nurture for cold inbound leads",
    steps=[
        {
            "channel": "email",
            "subject": "Welcome! Here's your guide",
            "content_template": "welcome_guide",
            "delay_days": 0,
        },
        {
            "channel": "email",
            "subject": "How [Company] solved [problem]",
            "content_template": "case_study_1",
            "delay_days": 3,
        },
        {
            "channel": "linkedin",
            "subject": "Let's connect",
            "content_template": "linkedin_connect",
            "delay_days": 7,
        },
        {
            "channel": "email",
            "subject": "Webinar invitation",
            "content_template": "webinar_invite",
            "delay_days": 14,
        },
        {
            "channel": "phone",
            "subject": "Check-in call",
            "content_template": "checkin_script",
            "delay_days": 21,
        },
    ],
    target_grade="cold",
))
```

### Enrolling Leads

```python
from lead_scorer.models.routing import NurtureEnrollmentRequest

enrollment = await agent.enroll(NurtureEnrollmentRequest(
    lead_id="lead-cold-123",
    sequence_id=sequence.id,
    metadata={"initial_score": 25.0, "source": "website"},
))
```

### Processing Engagement

```python
# Record email open
await agent.process_engagement(
    enrollment_id=enrollment.id,
    event_type="opened",
)

# Record link click
await agent.process_engagement(
    enrollment_id=enrollment.id,
    event_type="clicked",
    metadata={"link": "pricing_page"},
)

# Advance to next step
await agent.advance_step(enrollment.id)
```

### Exit Criteria

Leads automatically exit nurture when:

| Criteria | Description |
|----------|-------------|
| Lead becomes hot | Score reaches hot threshold (default: 80) |
| Lead becomes qualified | Qualification status changes to "qualified" |
| Score improvement | Score increases by threshold (default: 15 points) |
| Max duration | Enrollment exceeds max days (default: 90) |
| Unsubscribe | Lead unsubscribes from communications |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/nurture/sequences` | Create a nurture sequence |
| GET | `/api/v1/nurture/sequences` | List all sequences |
| GET | `/api/v1/nurture/sequences/{id}` | Get a sequence |
| DELETE | `/api/v1/nurture/sequences/{id}` | Delete a sequence |
| POST | `/api/v1/nurture/enroll` | Enroll a lead |
| GET | `/api/v1/nurture/enrollments/{id}` | Get enrollment |
| GET | `/api/v1/nurture/enrollments/lead/{id}` | Get lead enrollments |
| POST | `/api/v1/nurture/engagement` | Record engagement |
| POST | `/api/v1/nurture/advance/{id}` | Advance to next step |
| POST | `/api/v1/nurture/evaluate-exit` | Evaluate exit criteria |
| GET | `/api/v1/nurture/stats` | Get nurture statistics |

## Ensemble Scoring (V2)

### How It Works

The v2 scoring agent combines multiple models using a weighted ensemble approach:

| Model | Weight | Description |
|-------|--------|-------------|
| Firmographic | 20% | Company size, industry, revenue |
| Technographic | 10% | Tech stack, tools, hosting |
| Engagement | 25% | Email opens, clicks, website visits |
| Intent | 20% | Pricing page views, demo requests |
| Timing | 10% | Recency of engagement |
| Behavioral | 10% | Page views, downloads, social |
| Predictive | 5% | ML-based conversion prediction |

### Confidence & Explainability

The ensemble provides:

- **Confidence score** (0-1) based on model agreement and data completeness
- **Standard deviation** showing score uncertainty
- **Confidence intervals** for each component
- **Model contributions** showing each model's percentage contribution

```python
from lead_scorer.agents.lead_scoring_v2 import LeadScoringV2Agent

agent = LeadScoringV2Agent()
result = await agent.score("lead-123", research=research, evidence=evidence)

print(f"Score: {result.total_score}")
print(f"Grade: {result.grade.value}")
print(f"Confidence: {result.confidence}")
print(f"Std Dev: {result.score_std_dev}")

for component in result.components:
    print(f"  {component.name}: {component.ensemble_score:.2f} "
          f"(weight: {component.weight}, CI: {component.confidence_interval})")
```

## Configuration

### Environment Variables

```bash
# Routing
ROUTING_STRATEGY=priority
ROUTING_DEFAULT_DESTINATION=nurture
ROUTING_MAX_RULES=50

# Nurture
NURTURE_MAX_ENROLLMENT_DAYS=90
NURTURE_MIN_STEPS_BEFORE_EXIT=2
NURTURE_ENGAGEMENT_THRESHOLD=0.3
NURTURE_SCORE_IMPROVEMENT_THRESHOLD=15.0
NURTURE_AUTO_EXIT_ON_HOT=true
NURTURE_AUTO_EXIT_ON_QUALIFIED=true

# Scoring V2
SCORING_V2_TIMEOUT=45
SCORING_V2_MIN_MODELS=2
```

## Testing

Run the routing and nurture tests:

```bash
# All tests
pytest tests/test_routing.py tests/test_nurture.py tests/test_scoring_v2.py -v

# With coverage
pytest tests/test_routing.py tests/test_nurture.py tests/test_scoring_v2.py \
    --cov=lead_scorer.agents.lead_routing \
    --cov=lead_scorer.agents.lead_nurture \
    --cov=lead_scorer.agents.lead_scoring_v2 \
    --cov-report=term-missing
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "lead_scorer.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes

See `k8s/` directory for deployment manifests including:
- Deployment with HPA
- Service and Ingress
- ConfigMap for routing rules
- Prometheus monitoring

## Monitoring

### Prometheus Metrics

| Metric | Description |
|--------|-------------|
| `http_requests_total` | Total HTTP requests by method, endpoint, status |
| `http_request_duration_seconds` | Request latency histogram |
| `routing_decisions_total` | Total routing decisions by destination |
| `nurture_enrollments_active` | Current active nurture enrollments |
| `nurture_engagement_events_total` | Total engagement events processed |

### Health Check

```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "0.1.0", "service": "lead-scorer"}
```

## Best Practices

1. **Start with priority routing** — It works well for most use cases
2. **Keep rules simple** — Too many complex rules are hard to maintain
3. **Monitor assignment distribution** — Ensure even workload distribution
4. **Set realistic nurture periods** — 60-90 days is typical for B2B
5. **Track engagement thresholds** — Adjust based on your baseline metrics
6. **Use ensemble scoring** — V2 provides better accuracy than single-model scoring
7. **Review routing rules monthly** — Remove outdated rules and add new ones based on data
