# MLflow Deep-Dive & Integration Guide for Agent Experiment Tracking

**Target Stack:** Ahmed Hassan's multi-model evaluation pipeline (LongCat 2.5, Codex, Antigravity Pro)
**MLflow Version:** 3.x (latest stable)
**License:** Apache 2.0 (Linux Foundation)

---

## 1. Architecture Overview

MLflow is organized into five core pillars that map directly to Ahmed's experiment tracking needs:

```
┌─────────────────────────────────────────────────────────────┐
│                    MLflow Platform                          │
├─────────────┬──────────────┬──────────────┬────────────────┤
│  Tracking   │    Model     │   Prompt     │   AI Gateway   │
│  (Runs,     │   Registry   │   Registry   │  (Routing,     │
│   Params,   │  (Versions,  │  (Versions,  │   Fallbacks,   │
│   Metrics)  │   Stages)    │   Aliases)   │   Cost Ctrl)   │
├─────────────┴──────────────┴──────────────┴────────────────┤
│              Tracing (OpenTelemetry-native)                 │
│         60+ framework auto-instrumentation                  │
├─────────────────────────────────────────────────────────────┤
│              Evaluation (Scorers, Judges, Datasets)         │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 Experiment Tracking (MLflow Tracking)

The foundational layer. Every experiment run captures:

| What | How | API |
|------|-----|-----|
| Parameters | Hyperparams, model names, prompt versions | `mlflow.log_param()` / `mlflow.log_params()` |
| Metrics | Accuracy, latency, cost per token, custom scores | `mlflow.log_metric()` / `mlflow.log_metrics()` |
| Artifacts | Model weights, evaluation results, traces | `mlflow.log_artifact()` |
| Models | Logged with flavor metadata, versioned | `mlflow.<flavor>.log_model()` |
| Datasets | Training/eval data lineage | `mlflow.log_input()` |
| Code Version | Git commit hash, conda env, dependencies | Auto-captured |

**MLflow 3 introduces:**
- `mlflow.search_logged_models()` — SQL-like model search across experiments
- `models:/<model_id>` URI format (replaces `runs:/<run_id>/path`)
- `mlflow.create_external_model()` — track models stored outside MLflow (e.g., deployed agents)
- `mlflow.set_active_model()` — link traces to a specific model

### 1.2 Model Registry

Centralized model lifecycle management:

- **Registered Model** → unique name, contains versions
- **Model Version** → auto-incremented, immutable, linked to producing run
- **Model Alias** → mutable pointer (e.g., `@champion`, `@challenger`) for deployment
- **Stages** → Staging → Production (or custom stage transitions)
- **Tags** → metadata like `pre_deploy_checks: "PASSED"`

```python
# Register a model
mlflow.register_model("runs:/<run_id>/model", "agent-model")

# Promote to production
client = mlflow.MlflowClient()
client.transition_model_version_stage(
    name="agent-model", version=3, stage="Production"
)

# Load by alias
model = mlflow.pyfunc.load_model("models:/agent-model@champion")
```

### 1.3 Prompt Registry

Purpose-built for LLM/agent prompt management:

- **Version Control** — Git-inspired commit messages, immutable versions, diff comparison
- **Aliasing** — `@latest`, `@production`, `@staging` for environment-specific routing
- **Model Config** — Store `model_name`, `temperature`, `max_tokens`, `top_p` alongside prompts
- **Template Types** — Text (`{{var}}`), Chat (message list), Jinja2 (control flow)
- **Caching** — In-memory with configurable TTL per alias/version
- **Lineage** — Linked to traces and evaluation metrics

```python
import mlflow

# Register a prompt
mlflow.genai.register_prompt(
    name="agent-system-prompt",
    template="You are a {{style}} assistant. Task: {{task}}",
    model_config={"model_name": "gpt-4", "temperature": 0.3, "max_tokens": 2000},
    commit_message="Initial system prompt for agent v1"
)

# Load and use
prompt = mlflow.genai.load_prompt("prompts:/agent-system-prompt/1")
filled = prompt.format(style="helpful", task="code review")
```

### 1.4 AI Gateway

Unified OpenAI-compatible proxy for multi-provider LLM access:

| Feature | Description |
|---------|-------------|
| Unified API | Single endpoint for OpenAI, Anthropic, Bedrock, Cohere, etc. |
| Credential Management | Centralized API key storage, env var references |
| Traffic Splitting | Weighted A/B testing across models (1-100%) |
| Fallback Chains | Sequential failover on errors/rate limits |
| Usage Tracking | Token counts, costs, latency per endpoint/model |
| Tracing Integration | Every gateway request auto-captured as MLflow trace |
| Hot Reloading | Config changes without server restart |

### 1.5 Tracing (Agent Observability)

OpenTelemetry-native tracing with 60+ framework integrations:

```python
import mlflow

# One-line auto-tracing for any supported library
mlflow.openai.autolog()
mlflow.langchain.autolog()
mlflow.anthropic.autolog()

# Manual tracing for custom functions
@mlflow.trace(span_type="AGENT")
def my_agent(query: str) -> str:
    # ... agent logic
    return response

# Session grouping for multi-turn conversations
with mlflow.tracing.context(session_id="session-123", user="user-456"):
    agent.invoke("What is the capital of France?")
```

### 1.6 Evaluation

Systematic quality assessment with scorers and judges:

- **Built-in Scorers:** `Correctness`, `Safety`, `RelevanceToQuery`, `Guidelines`
- **Agent Scorers:** `ToolCallCorrectness`, `ToolCallEfficiency`
- **Custom Judges:** `make_judge()` for domain-specific LLM evaluation
- **Datasets:** Versioned evaluation datasets with expectations
- **Conversation Simulation:** Multi-turn dialogue evaluation

```python
from mlflow.genai.scorers import Correctness, ToolCallCorrectness, ToolCallEfficiency

results = mlflow.genai.evaluate(
    data=eval_dataset,
    predict_fn=agent.run,
    scorers=[Correctness(), ToolCallCorrectness(), ToolCallEfficiency()]
)
```

---

## 2. Key Features for Ahmed's Stack

### 2.1 AI Gateway with Traffic Splitting

**Use case:** Compare LongCat 2.5 vs Codex vs Antigravity Pro on identical tasks with gradual rollout.

```yaml
# gateway-config.yaml
endpoints:
  - name: longcat-chat
    endpoint_type: llm/v1/chat
    model:
      provider: openai
      name: longcat-2.5
      config:
        openai_api_key: $LONGCAT_API_KEY
        openai_api_base: https://api.longcat.ai/v1

  - name: codex-chat
    endpoint_type: llm/v1/chat
    model:
      provider: openai
      name: codex-mini
      config:
        openai_api_key: $CODEX_API_KEY
        openai_api_base: https://api.openai.com/v1

  - name: antigravity-chat
    endpoint_type: llm/v1/chat
    model:
      provider: openai
      name: antigravity-pro
      config:
        openai_api_key: $ANTIGRAVITY_API_KEY
        openai_api_base: https://api.antigravity.dev/v1

routes:
  - name: agent-route
    route_type: llm/v1/chat
    destinations:
      - name: longcat-chat
        traffic_percentage: 50
      - name: codex-chat
        traffic_percentage: 30
      - name: antigravity-chat
        traffic_percentage: 20
    routing_strategy: TRAFFIC_SPLIT
```

Start the gateway:
```bash
mlflow gateway start --config-path gateway-config.yaml --port 7000
```

Query via OpenAI SDK (gateway is OpenAI-compatible):
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7000/gateway/routes/agent-route/invocations",
    api_key="dummy"  # Gateway handles real credentials
)

response = client.chat.completions.create(
    model="agent-route",  # Route name
    messages=[{"role": "user", "content": "Review this code..."}]
)
```

### 2.2 Prompt Versioning

Track prompt changes as first-class artifacts with full lineage:

```python
import mlflow

# Version 1: Initial prompt
mlflow.genai.register_prompt(
    name="code-review-agent",
    template="Review the following code for bugs: {{code}}",
    commit_message="Initial code review prompt"
)

# Version 2: Improved with style guidance
mlflow.genai.register_prompt(
    name="code-review-agent",
    template="Review the following code for bugs and style issues. Language: {{language}}\n\n{{code}}",
    commit_message="Added language parameter and style check"
)

# A/B test: load different versions
prompt_v1 = mlflow.genai.load_prompt("prompts:/code-review-agent/1")
prompt_v2 = mlflow.genai.load_prompt("prompts:/code-review-agent/2")

# Compare in UI with diff highlighting
# Link prompt versions to experiment runs
client = mlflow.MlflowClient()
client.link_prompt_version_to_run(
    run_id=run_id,
    prompt_versions=[prompt_v2]
)
```

### 2.3 Model Comparison Across Experiments

```python
import mlflow

# Search for best-performing model across all experiments
top_models = mlflow.search_logged_models(
    experiment_ids=["1", "2", "3"],
    filter_string="metrics.accuracy > 0.85 AND params.model_type = 'agent'",
    order_by=[{"field_name": "metrics.cost_per_task", "ascending": True}],
    max_results=10
)

# Load the best model
best = top_models[0]
model = mlflow.pyfunc.load_model(f"models:/ {best.model_id}")
```

### 2.4 Cost Tracking Integration

```python
import mlflow

with mlflow.start_run(run_name="codex-eval-run-001") as run:
    # Log model configuration
    mlflow.log_params({
        "model": "codex-mini",
        "provider": "openai",
        "temperature": 0.3,
        "max_tokens": 4096,
        "prompt_version": "code-review-agent/2"
    })
    
    # Run evaluation
    results = run_agent_evaluation(model="codex-mini", dataset="code-review-100")
    
    # Log cost metrics
    mlflow.log_metrics({
        "total_cost_usd": results.total_cost,
        "cost_per_task": results.total_cost / results.num_tasks,
        "latency_p50_ms": results.latency_p50,
        "latency_p99_ms": results.latency_p99,
        "accuracy": results.accuracy,
        "error_rate": results.error_rate
    })
    
    # Log evaluation results as artifact
    mlflow.log_artifact("evaluation_results.csv")
    
    # Log traces for debugging
    mlflow.log_artifact("traces.json")
```

---

## 3. Integration Guide: Tracking Agent Experiments with MLflow

### 3.1 Setup

```bash
# Install MLflow with GenAI support
pip install 'mlflow[genai]>=3.3'

# Start tracking server (local development)
mlflow server --host 0.0.0.0 --port 5000

# For production: use database-backed store
mlflow server \
    --backend-store-uri postgresql://user:pass@localhost/mlflow \
    --default-artifact-root s3://my-bucket/mlflow-artifacts \
    --host 0.0.0.0 --port 5000
```

### 3.2 Configure Environment

```bash
# .env file
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=agent-evaluation
MLFLOW_ARTIFACT_ROOT=s3://my-bucket/mlflow-artifacts
```

### 3.3 Instrument Agent Code

```python
import mlflow
import os
from datetime import datetime

# Configure tracking
mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
mlflow.set_experiment("agent-evaluation")

# Enable auto-tracing for your LLM library
mlflow.openai.autolog()  # or mlflow.langchain.autolog(), etc.

# Define your agent with tracing
@mlflow.trace(span_type="AGENT")
def run_agent(task: str, model: str, prompt_version: str) -> dict:
    """Execute agent task and return results."""
    # Load prompt from registry
    prompt = mlflow.genai.load_prompt(f"prompts:/code-review-agent/{prompt_version}")
    filled_prompt = prompt.format(code=task, language="python")
    
    # Call LLM through gateway (auto-traced)
    from openai import OpenAI
    client = OpenAI(
        base_url="http://localhost:7000/gateway/routes/agent-route/invocations",
        api_key="dummy"
    )
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": filled_prompt}],
        temperature=0.3
    )
    
    return {
        "output": response.choices[0].message.content,
        "model": model,
        "usage": response.usage
    }
```

### 3.4 Run Experiment with Full Tracking

```python
import mlflow
import json
from datetime import datetime

def run_experiment(
    experiment_name: str,
    models: list[str],
    prompt_versions: list[str],
    dataset: list[dict]
):
    """Run a complete agent experiment with MLflow tracking."""
    
    mlflow.set_experiment(experiment_name)
    
    for model in models:
        for prompt_ver in prompt_versions:
            run_name = f"{model}-prompt-{prompt_ver}-{datetime.now():%Y%m%d-%H%M%S}"
            
            with mlflow.start_run(run_name=run_name) as run:
                run_id = run.info.run_id
                
                # Log configuration
                mlflow.log_params({
                    "model": model,
                    "prompt_version": prompt_ver,
                    "dataset_size": len(dataset),
                    "timestamp": datetime.now().isoformat(),
                    "git_commit": get_git_commit(),  # implement this
                })
                
                # Set tags for filtering
                mlflow.set_tags({
                    "experiment_type": "model_comparison",
                    "team": "ai-engineering",
                    "environment": "staging"
                })
                
                # Run evaluation
                results = []
                total_cost = 0
                latencies = []
                
                for i, task in enumerate(dataset):
                    try:
                        result = run_agent(
                            task=task["input"],
                            model=model,
                            prompt_version=prompt_ver
                        )
                        results.append({
                            "task_id": task["id"],
                            "output": result["output"],
                            "expected": task.get("expected"),
                            "success": True
                        })
                        total_cost += result.usage.total_tokens * get_token_price(model)
                        latencies.append(result.get("latency_ms", 0))
                    except Exception as e:
                        results.append({
                            "task_id": task["id"],
                            "error": str(e),
                            "success": False
                        })
                
                # Compute metrics
                success_rate = sum(1 for r in results if r["success"]) / len(results)
                avg_latency = sum(latencies) / len(latencies) if latencies else 0
                
                # Log metrics
                mlflow.log_metrics({
                    "success_rate": success_rate,
                    "total_cost_usd": total_cost,
                    "cost_per_task": total_cost / len(dataset),
                    "avg_latency_ms": avg_latency,
                    "tasks_completed": sum(1 for r in results if r["success"]),
                    "tasks_failed": sum(1 for r in results if not r["success"]),
                })
                
                # Log artifacts
                with open("results.json", "w") as f:
                    json.dump(results, f, indent=2)
                mlflow.log_artifact("results.json")
                
                # Log dataset reference
                mlflow.log_input(mlflow.data.from_pandas(
                    pd.DataFrame(dataset), name="eval-dataset"
                ))
                
                print(f"Run {run_id}: success_rate={success_rate:.2%}, cost=${total_cost:.4f}")

def get_git_commit() -> str:
    import subprocess
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()

def get_token_price(model: str) -> float:
    """Return price per token for cost tracking."""
    prices = {
        "longcat-2.5": 0.0,  # Free
        "codex-mini": 0.000002,  # $2 per 1M tokens
        "antigravity-pro": 0.000003,
    }
    return prices.get(model, 0.0)
```

### 3.5 Evaluate with MLflow Scorers

```python
from mlflow.genai.scorers import Correctness, Safety, RelevanceToQuery
from mlflow.genai import evaluate

# Define evaluation dataset
eval_data = [
    {
        "inputs": {"code": "def add(a, b): return a + b"},
        "expectations": {"expected_facts": ["function", "addition", "correct"]}
    },
    # ... more test cases
]

# Run evaluation with built-in scorers
results = mlflow.genai.evaluate(
    data=eval_data,
    predict_fn=lambda code: run_agent(code, "longcat-2.5", "1"),
    scorers=[
        Correctness(name="code_correctness"),
        Safety(name="code_safety"),
        RelevanceToQuery(name="relevance")
    ]
)

# Results are automatically logged to the active run
print(results.metrics)
```

### 3.6 Compare Experiments Programmatically

```python
import mlflow
import pandas as pd

# Search across experiments
runs = mlflow.search_runs(
    experiment_ids=["1", "2", "3"],
    filter_string="metrics.success_rate > 0.8",
    order_by=["metrics.cost_per_task ASC"],
    output_format="pandas"
)

# Compare specific runs
comparison = runs[[
    "run_id", "params.model", "params.prompt_version",
    "metrics.success_rate", "metrics.cost_per_task",
    "metrics.avg_latency_ms"
]]

print(comparison.to_string())

# Find best model by cost-efficiency
best = runs.loc[metrics.cost_per_task.idxmin()]
print(f"Best model: {best['params.model']} at ${best['metrics.cost_per_task']:.4f}/task")
```

---

## 4. Configuration Examples

### 4.1 Experiment Definition (experiment.yaml)

```yaml
# experiment.yaml
name: "agent-model-comparison-v2"
description: "Compare LongCat 2.5, Codex, and Antigravity Pro on code review tasks"

# Models to evaluate
models:
  - name: "longcat-2.5"
    provider: "longcat"
    cost_per_token: 0.0
    role: "baseline"
  - name: "codex-mini"
    provider: "openai"
    cost_per_token: 0.000002
    role: "challenger"
  - name: "antigravity-pro"
    provider: "antigravity"
    cost_per_token: 0.000003
    role: "challenger"

# Prompt versions to test
prompt_versions:
  - "code-review-agent/1"
  - "code-review-agent/2"

# Evaluation dataset
dataset:
  name: "code-review-eval"
  version: "1.0"
  size: 100
  tasks:
    - id: "task-001"
      input: "def add(a, b): return a + b"
      expected: "Correct function, no issues"
    - id: "task-002"
      input: "def divide(a, b): return a / b"
      expected: "Should check for division by zero"

# Metrics to track
metrics:
  - name: "success_rate"
    type: "percentage"
    description: "Percentage of tasks completed successfully"
  - name: "cost_per_task"
    type: "currency"
    description: "Average cost per task in USD"
  - name: "latency_p50"
    type: "milliseconds"
    description: "Median latency"
  - name: "latency_p99"
    type: "milliseconds"
    description: "99th percentile latency"

# Scorers for evaluation
scorers:
  - name: "correctness"
    type: "built_in"
  - name: "safety"
    type: "built_in"
  - name: "code_quality"
    type: "custom"
    judge: "gpt-4o-mini"
```

### 4.2 MLflow Tracking Server Configuration

```bash
# Production deployment with PostgreSQL backend
mlflow server \
    --backend-store-uri postgresql://mlflow:${DB_PASSWORD}@postgres:5432/mlflow \
    --default-artifact-root s3://my-mlflow-bucket/artifacts \
    --host 0.0.0.0 \
    --port 5000 \
    --workers 4 \
    --static-prefix /mlflow
```

### 4.3 Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  mlflow:
    image: ghcr.io/mlflow/mlflow:latest
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://mlflow:mlflow@postgres:5432/mlflow
      - MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://my-bucket/mlflow-artifacts
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    command: >
      mlflow server
      --host 0.0.0.0
      --port 5000
      --backend-store-uri ${MLFLOW_BACKEND_STORE_URI}
      --default-artifact-root ${MLFLOW_DEFAULT_ARTIFACT_ROOT}
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=mlflow
      - POSTGRES_PASSWORD=mlflow
      - POSTGRES_DB=mlflow
    volumes:
      - postgres_data:/var/lib/postgresql/data

  gateway:
    image: ghcr.io/mlflow/mlflow:latest
    ports:
      - "7000:7000"
    volumes:
      - ./gateway-config.yaml:/config.yaml
    command: mlflow gateway start --config-path /config.yaml --port 7000

volumes:
  postgres_data:
```

### 4.4 Python SDK Configuration

```python
# config.py
import mlflow
from dataclasses import dataclass

@dataclass
class ExperimentConfig:
    tracking_uri: str = "http://localhost:5000"
    experiment_name: str = "agent-evaluation"
    artifact_location: str = "s3://my-bucket/mlflow-artifacts"
    
    # Gateway settings
    gateway_uri: str = "http://localhost:7000"
    gateway_route: str = "agent-route"
    
    # Model settings
    models: list = None
    prompt_versions: list = None
    
    def __post_init__(self):
        if self.models is None:
            self.models = ["longcat-2.5", "codex-mini", "antigravity-pro"]
        if self.prompt_versions is None:
            self.prompt_versions = ["1", "2"]

def setup_mlflow(config: ExperimentConfig):
    """Initialize MLflow with configuration."""
    mlflow.set_tracking_uri(config.tracking_uri)
    mlflow.set_experiment(config.experiment_name)
    
    # Enable auto-tracing
    mlflow.openai.autolog()
    
    # Set default tags
    mlflow.set_tags({
        "project": "agent-evaluation",
        "team": "ai-engineering",
        "managed_by": "hermes-agent"
    })
    
    return config
```

---

## 5. Comparison with Other Tracking Tools

| Feature | MLflow | Weights & Biases | LangSmith | Langfuse | Neptune |
|---------|--------|-----------------|-----------|----------|---------|
| **License** | Apache 2.0 (Open Source) | Proprietary SaaS | Proprietary SaaS | Apache 2.0 (Open Source) | Proprietary SaaS |
| **Self-Hosted** | ✅ Yes | ❌ No | ❌ Enterprise only | ✅ Yes | ❌ No |
| **LLM Tracing** | ✅ OTel-native, 60+ integrations | ⚠️ Weave (added later) | ✅ Native, LangChain-first | ✅ OTel-native | ⚠️ Basic |
| **Prompt Registry** | ✅ Built-in, versioned | ⚠️ Basic versioning | ✅ Built-in | ❌ No | ❌ No |
| **AI Gateway** | ✅ Built-in with traffic splitting | ❌ No | ❌ No | ❌ No | ❌ No |
| **Model Registry** | ✅ Full lifecycle | ✅ Artifacts | ❌ No | ❌ No | ⚠️ Basic |
| **Agent Evaluation** | ✅ Built-in scorers + judges | ⚠️ Weave evals | ✅ Native | ⚠️ Basic | ❌ No |
| **Cost Tracking** | ✅ Via gateway + custom metrics | ⚠️ Manual | ✅ Built-in | ✅ Built-in | ⚠️ Manual |
| **Traffic Splitting** | ✅ Built-in | ❌ No | ❌ No | ❌ No | ❌ No |
| **Free Tier** | ✅ Unlimited (self-hosted) | ⚠️ 100GB storage | ⚠️ 5,000 traces/mo | ✅ Unlimited (self-hosted) | ⚠️ Limited |
| **Best For** | Full MLOps + LLMOps, open-source | Research visualization | LangChain apps | LLM observability | Experiment tracking |

### Recommendation for Ahmed's Stack

**MLflow is the best fit** because:
1. **Open source** — No vendor lock-in, aligns with free/open-source constraint for video production
2. **AI Gateway** — Built-in traffic splitting for A/B testing models without code changes
3. **Prompt Registry** — First-class prompt versioning with model config
4. **Cost tracking** — Custom metrics + gateway usage tracking
5. **Self-hosted** — Data stays on infrastructure (important for compliance)
6. **60+ integrations** — Works with any LLM provider or agent framework

**When to consider alternatives:**
- **LangSmith** if heavily invested in LangChain/LangGraph ecosystem
- **W&B** if prioritizing visualization and team collaboration over self-hosting
- **Langfuse** if need lightweight, open-source LLM observability only

---

## 6. Pitfalls and Best Practices

### 6.1 Common Pitfalls

| Pitfall | Impact | Solution |
|---------|--------|----------|
| **Logging every step** | 2ms per metric step, 10M step limit per run | Log every N steps or per epoch |
| **Traffic split ≠ 100%** | Fallbacks never activate | Weights must sum to exactly 100% |
| **Fallback without traffic split** | Fallbacks silently fail | Configure traffic split first |
| **No RBAC in open-source** | Unauthorized access | Add reverse proxy with auth (nginx, Traefik) |
| **Spawn method in multiprocessing** | Child processes don't inherit tracking URI | Set URI explicitly in each child process |
| **Prompt cache staleness** | Using outdated prompt versions | Set appropriate TTL or invalidate on update |
| **Missing git commit in runs** | Can't reproduce experiments | Always log git commit hash |
| **Artifact storage not configured** | Lost evaluation results | Always set `--default-artifact-root` |
| **Co-installing mlflow and mlflow-tracing** | Version conflicts | Use one or the other, not both |
| **Not setting experiment name** | Runs go to "Default" experiment | Always call `mlflow.set_experiment()` |

### 6.2 Best Practices

#### Experiment Organization
```python
# Use consistent naming conventions
mlflow.set_experiment("agent-eval/2024-10/code-review")

# Tag everything for filtering
mlflow.set_tags({
    "model_family": "longcat",
    "prompt_version": "v2",
    "dataset": "code-review-100",
    "environment": "staging"
})

# Use run names that are searchable
with mlflow.start_run(run_name="longcat-v2-prompt2-run001"):
    ...
```

#### Metric Logging Strategy
```python
# DON'T: Log every step in a long training loop
for step in range(1000000):
    mlflow.log_metric("loss", loss, step=step)  # 2ms × 1M = 2000s overhead!

# DO: Log every N steps or per epoch
for epoch in range(100):
    for step in range(1000):
        loss = train_step()
    mlflow.log_metric("loss", loss, step=epoch)  # Only 100 log calls
```

#### Cost Tracking
```python
# Always log cost alongside quality metrics
mlflow.log_metrics({
    "quality_score": 0.92,
    "cost_usd": 0.023,
    "cost_per_quality_point": 0.023 / 0.92,  # Normalized cost
})
```

#### Prompt Management
```python
# Use aliases for environment-specific prompts
mlflow.genai.set_prompt_alias("code-review-agent", "production", version=3)
mlflow.genai.set_prompt_alias("code-review-agent", "staging", version=4)

# Load by alias in production
prompt = mlflow.genai.load_prompt("prompts:/code-review-agent@production")
```

#### Gateway Configuration
```yaml
# Always use environment variables for API keys
config:
  openai_api_key: $OPENAI_API_KEY  # Never hardcode!

# Validate traffic split sums to 100%
destinations:
  - name: model-a
    traffic_percentage: 80
  - name: model-b
    traffic_percentage: 20
# Total: 100% ✓
```

#### Production Deployment
```bash
# Use database backend (not filesystem)
mlflow server --backend-store-uri postgresql://...

# Use object storage for artifacts
mlflow server --default-artifact-root s3://...

# Enable authentication via reverse proxy
# nginx config with basic auth or OAuth

# Set up monitoring
# - Prometheus metrics from MLflow server
# - Alert on failed runs, high costs, latency spikes
```

### 6.3 Security Checklist

- [ ] Never commit API keys to version control
- [ ] Use environment variables for all credentials
- [ ] Enable HTTPS in production
- [ ] Configure reverse proxy with authentication
- [ ] Restrict network access to tracking server
- [ ] Rotate API keys regularly
- [ ] Enable audit logging for gateway requests
- [ ] Use separate keys for dev/staging/production
- [ ] Redact PII from traces (`mlflow.tracing.mask()`)
- [ ] Set up backup for tracking database

### 6.4 Performance Optimization

```python
# Use async logging for high-throughput scenarios
mlflow.log_metric("loss", loss, synchronous=False)

# Configure sampling for production tracing
os.environ["MLFLOW_TRACING_SAMPLING_RATE"] = "0.1"  # 10% of traces

# Use lightweight SDK for production
# pip install mlflow-tracing  # 95% smaller than full mlflow

# Batch metric logging
mlflow.log_metrics({
    "accuracy": 0.95,
    "precision": 0.92,
    "recall": 0.89,
    "f1": 0.90
})  # Single API call
```

---

## 7. Quick Start for Ahmed's Multi-Model Evaluation

```bash
# 1. Install dependencies
pip install 'mlflow[genai]>=3.3' openai pandas

# 2. Start MLflow server
mlflow server --host 0.0.0.0 --port 5000 &

# 3. Configure environment
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_EXPERIMENT_NAME=agent-evaluation

# 4. Run experiment
python run_experiment.py

# 5. View results
open http://localhost:5000
```

```python
# run_experiment.py
import mlflow
from mlflow.genai.scorers import Correctness, Safety

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("agent-evaluation")
mlflow.openai.autolog()

# Define your evaluation
eval_data = [
    {"inputs": {"code": "def add(a,b): return a+b"}, "expectations": {"expected_facts": ["correct"]}},
    # ... more test cases
]

# Run comparison
for model in ["longcat-2.5", "codex-mini", "antigravity-pro"]:
    with mlflow.start_run(run_name=f"{model}-eval"):
        mlflow.log_param("model", model)
        
        results = mlflow.genai.evaluate(
            data=eval_data,
            predict_fn=lambda code: run_agent(code, model),
            scorers=[Correctness(), Safety()]
        )
        
        print(f"{model}: {results.metrics}")
```

---

## 8. Summary

MLflow provides a comprehensive, open-source platform for Ahmed's agent experiment tracking needs:

| Need | MLflow Solution |
|------|-----------------|
| Experiment tracking | `mlflow.start_run()` + `log_params/metrics` |
| Model comparison | `mlflow.search_logged_models()` + experiment search |
| Prompt versioning | `mlflow.genai.register_prompt()` + aliases |
| AI Gateway | Built-in with traffic splitting + fallbacks |
| Cost tracking | Custom metrics + gateway usage tracking |
| Agent observability | OpenTelemetry tracing + 60+ integrations |
| Quality evaluation | Built-in scorers + custom judges |
| Reproducibility | Git commit logging + dataset versioning |

**Key advantage:** MLflow is the only open-source platform that combines experiment tracking, model registry, prompt registry, AI gateway, and agent evaluation in a single, self-hostable package — no vendor lock-in, no per-seat pricing, full data control.
