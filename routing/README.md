# Model Routing System

Production-grade model routing and cost optimization system for agentic AI marketing projects.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Request                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ModelRouter (router.py)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Complexity  │  │    Model     │  │   Capability Filter   │  │
│  │  Analyzer    │  │  Registry    │  │                       │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Routing Decision                              │
│         (model, tier, estimated cost, confidence)                │
└─────────────────────────────┬───────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  TokenBudget    │ │  SemanticCache  │ │  LatencyOptimizer│
│  (budget.py)    │ │  (cache.py)     │ │  (latency.py)   │
│                 │ │                 │ │                 │
│ • Hourly limits │ │ • Similarity    │ │ • P95 tracking  │
│ • Daily limits  │ │   matching      │ │ • Optimization  │
│ • Cost limits   │ │ • TTL eviction  │ │ • Recommendations│
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────┬───┴───────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LayaClient (laya.py)                        │
│              Multi-provider model gateway                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  FallbackChain  │ │  QualityScorer  │ │  CostMonitor    │
│  (fallback.py)  │ │  (quality.py)   │ │  (cost.py)      │
│                 │ │                 │ │                 │
│ • Circuit       │ │ • 7 dimensions   │ │ • Real-time     │
│   breaker       │ │ • Safety check  │ │   tracking      │
│ • Retry logic   │ │ • Custom rules  │ │ • Alerts        │
│ • Multi-model   │ │ • Feedback      │ │ • Reporting     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Components

### 1. Router (`router.py`)
Tiered model routing with complexity analysis and capability filtering.

- **5 tiers**: `ultra_fast`, `fast`, `balanced`, `quality`, `ultra_quality`
- **Heuristic complexity analyzer** (no external dependencies)
- **Weighted scoring** for model selection
- **Pre/post routing hooks** for extensibility

### 2. Laya Integration (`laya.py`)
Multi-provider model gateway client.

- **Unified API** for multiple model providers
- **Retry logic** with exponential backoff
- **Response caching** with TTL
- **Session statistics** tracking

### 3. Token Budget (`budget.py`)
Configurable token and cost budget enforcement.

- **Multiple periods**: hourly, daily, weekly, monthly, total
- **Hard limits** with `BudgetExceededError`
- **Alert thresholds** at configurable percentages
- **Thread-safe** consumption tracking
- **BudgetManager** for multi-project budgets

### 4. Cost Monitoring (`cost.py`)
Real-time cost tracking and reporting.

- **Per-model cost** breakdown
- **Per-project cost** attribution
- **Configurable alerts** with callbacks
- **JSON/CSV export** capabilities
- **Retention management** (configurable hours)

### 5. Semantic Cache (`cache.py`)
Intelligent response caching with semantic similarity.

- **Cosine similarity** matching
- **Configurable threshold** (default 0.85)
- **TTL-based expiration**
- **LRU eviction** when at capacity
- **Pluggable embedding** provider

### 6. Fallback Strategies (`fallback.py`)
Resilient fallback chains with circuit breakers.

- **Circuit breaker** pattern (configurable threshold/timeout)
- **Exponential backoff** retries
- **Multiple strategies**: default, random, weighted
- **Event history** for debugging

### 7. Quality Scoring (`quality.py`)
Multi-dimensional response quality assessment.

- **7 dimensions**: correctness, relevance, coherence, completeness, safety, helpfulness, conciseness
- **Configurable weights** per dimension
- **Safety checks** for prompt injection and PII
- **Custom scoring rules** support
- **Score trending** and feedback

### 8. Latency Optimization (`latency.py`)
Real-time latency profiling and optimization.

- **P50/P95/P99** percentile tracking
- **Latency tier** classification
- **Optimization suggestions**
- **Model comparison** tools

## Quick Start

### Installation

```bash
cd ~/GRC_Claw/routing
chmod +x scripts/setup-routing.sh
./scripts/setup-routing.sh
source .venv/bin/activate
```

### Basic Usage

```python
from routing import ModelRouter, ModelSpec, RouteTier

# Create router
router = ModelRouter()

# Register models
router.register_model(ModelSpec(
    name="gpt-4o-mini",
    tier=RouteTier.FAST,
    max_tokens=128000,
    cost_per_1k_tokens=0.00015,
    avg_latency_ms=150,
    quality_score=0.75,
    capabilities=frozenset(["text", "function_calling"]),
))

# Route a request
decision = router.route("What is machine learning?")
print(f"Selected: {decision.model.name}")
print(f"Estimated cost: ${decision.estimated_cost:.6f}")
print(f"Confidence: {decision.confidence:.2f}")
```

### With Budget Enforcement

```python
from routing import TokenBudget, BudgetConfig, BudgetPeriod

config = BudgetConfig(
    period=BudgetPeriod.DAILY,
    max_tokens=1_000_000,
    max_cost_usd=50.0,
    hard_limit=True,
)
budget = TokenBudget(config)

# This will raise BudgetExceededError if over limit
budget.consume(tokens=1000, cost_usd=0.01, model="gpt-4o")
```

### With Fallback Chain

```python
from routing import FallbackChain, FallbackStrategy

chain = FallbackChain(FallbackStrategy(
    name="production",
    max_retries=2,
    fallback_models=["gpt-4o", "gpt-4o-mini", "claude-3-haiku"],
))

# Add executors for each model
chain.add_model("gpt-4o", gpt4o_executor)
chain.add_model("gpt-4o-mini", mini_executor)

# Execute with automatic fallback
model_used, response = chain.execute("Hello!")
```

## Configuration

Default configuration is created at `config/routing.yaml` by the setup script.

Key settings:
- `routing.default_tier`: Default routing tier
- `budget.daily.max_tokens`: Daily token limit
- `cache.similarity_threshold`: Semantic cache matching threshold
- `fallback.max_retries`: Retry attempts before fallback
- `latency.target_p95_ms`: Target P95 latency

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `INSTALL_DEV` | Install dev dependencies | `0` |
| `LAYA_API_KEY` | Laya API key | - |
| `ROUTING_LOG_LEVEL` | Logging level | `INFO` |

## Testing

```bash
# Run with development dependencies
INSTALL_DEV=1 ./scripts/setup-routing.sh

# Run tests
pytest tests/

# Type checking
mypy routing/

# Linting
ruff check routing/
```

## License

MIT
