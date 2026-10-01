# RouteLLM Deep-Dive: Architecture, Integration & Production Guide

> **For:** Ahmed Hassan — 330 agent slots, FinOps optimization  
> **Repo:** [lm-sys/RouteLLM](https://github.com/lm-sys/RouteLLM) (5.5K stars, Apache-2.0)  
> **Paper:** [arXiv:2406.18665](https://arxiv.org/abs/2406.18665) (ICLR 2025)  
> **Status:** Research-grade; last commit Aug 2024. Still the canonical open-source routing framework.

---

## 1. Architecture Overview

### Core Concept

RouteLLM is a **binary LLM router** that sits between your application and two models — a **strong** (expensive, high-quality) model and a **weak** (cheaper, lower-quality) model. For each incoming query, the router predicts whether the strong model is *needed* to produce an acceptable answer. If not, the query is routed to the weak model.

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Client     │────▶│  RouteLLM        │────▶│  Strong Model   │
│  Request    │     │  Controller      │     │  (GPT-4, etc.)  │
│             │     │                  │     └─────────────────┘
│             │     │  Router decides: │
│             │     │  strong_win_rate │     ┌─────────────────┐
│             │     │  vs. threshold   │────▶│  Weak Model     │
│             │     │                  │     │  (Mixtral, etc.)│
└─────────────┘     └──────────────────┘     └─────────────────┘
```

### The Routing Decision

The core formula:

```
R^α(q) = M_strong  if  P_θ(win_strong | q) ≥ α
          M_weak    otherwise
```

Where:
- `P_θ(win_strong | q)` = probability that the strong model outperforms the weak model on query `q`
- `α` (alpha) = cost threshold — the single knob controlling the cost-quality tradeoff

**Higher threshold → fewer strong-model calls → lower cost, potentially lower quality.**

### Four Router Architectures

| Router | Method | Training Data | Inference Latency | External Dependencies | Best For |
|--------|--------|---------------|-------------------|----------------------|----------|
| **mf** (Matrix Factorization) | Learns query-model embeddings; bilinear scoring | Pairwise preference pairs | ~50ms (includes embedding API call) | OpenAI Embedding API | General online routing (recommended) |
| **bert** | DeBERTa-v3 fine-tuned classifier | 3-class classification labels | ~15ms (CPU) | None | Low-latency / offline |
| **sw_ranking** | Similarity-weighted Elo (Bradley-Terry) | No training needed | ~200-500ms | OpenAI Embedding API | Offline evaluation |
| **causal_llm** | Llama-3-8B fine-tuned classifier | Pairwise preference pairs | ~50-100ms | GPU | Weak model is a small LM |
| **random** | Random baseline | N/A | ~0ms | None | Baseline comparison |

### Training Data Pipeline

RouteLLM's routers are trained on **Chatbot Arena preference data** (~80K human-judged battles):

1. **Raw Arena data** (`D_arena`): 80K battles with human votes (model_a vs model_b → winner)
2. **Data augmentation** — critical for performance:
   - `D_gold`: Golden-labeled data from MMLU validation split (~1,500 samples)
   - `D_judge`: GPT-4-as-judge labeled data (~25K preference pairs from Nectar dataset)
3. **Filtering**: Remove ties, same-model matchups, and ambiguous labels

**Key insight from the paper**: Routers trained *only* on Arena data perform poorly (near-random on MMLU). Augmentation with just 2% golden-labeled data dramatically improves performance.

### MF Router Architecture (Recommended)

```
Input Query ──▶ text-embedding-3-small (1536-dim)
                         │
                    text_proj (Linear: 1536 → 128)
                         │
                         ▼
              ┌─────────────────────┐
              │  Element-wise       │
              │  product with       │──▶ classifier (Linear: 128 → 1) ──▶ logit
              │  (P[winner] -       │
              │   P[loser])         │
              └─────────────────────┘
```

- **Model embeddings**: 64 models × 128-dim (trainable)
- **Prompt embeddings**: 1536-dim (frozen, from OpenAI API)
- **Loss**: BCEWithLogitsLoss (label always 1.0 — data pre-arranged so winner is always first)
- **Hyperparameters**: dim=128, lr=3e-4, weight_decay=1e-5, batch_size=64, epochs=100

---

## 2. Key Features for Ahmed's Stack

### Cost Reduction: 85% on MT Bench

| Benchmark | Cost Reduction | Quality Retained | GPT-4 Calls Needed |
|-----------|---------------|------------------|-------------------|
| MT Bench | **85%** | 95% of GPT-4 | ~26% |
| MMLU | 45% | 95% of GPT-4 | ~54% |
| GSM8K | 35% | 95% of GPT-4 | ~65% |

**For 330 agent slots**: If each slot currently uses GPT-4 ($24.7/M tokens), routing 74% to a model like Mixtral ($0.24/M tokens) yields:

```
Current cost:  330 × $24.7 = $8,151 per M tokens
Routed cost:   330 × (0.26 × $24.7 + 0.74 × $0.24) = 330 × $6.60 = $2,178 per M tokens
Savings:       ~73% reduction in token costs
```

### Feature Checklist for Production

| Feature | RouteLLM Support | Notes |
|---------|-----------------|-------|
| Drop-in OpenAI client replacement | ✅ | `from routellm.controller import Controller` |
| OpenAI-compatible server | ✅ | `python -m routellm.openai_server` |
| Pre-trained routers out of the box | ✅ | 4 routers, no training needed |
| Cost threshold calibration | ✅ | `python -m routellm.calibrate_threshold` |
| Multi-provider support | ✅ | Via LiteLLM (100+ providers) |
| Local model routing (Ollama) | ✅ | Via LiteLLM + Ollama |
| Custom router training | ✅ | Implement `Router` abstract class |
| Streaming support | ✅ | SSE-compatible |
| Router benchmarking | ✅ | Built-in eval framework |
| Circuit breaker / retry | ❌ | Not built-in — add at LiteLLM layer |
| Semantic caching | ❌ | Not built-in — add at LiteLLM layer |
| Cost tracking / observability | ❌ | Not built-in — use LiteLLM callbacks |
| Multi-model routing (N-way) | ❌ | Binary only (strong/weak) |

### What's Missing for Production FinOps

RouteLLM is a **router**, not a full FinOps layer. For Ahmed's 330-slot deployment, you'll need to wrap it with:

1. **Cost tracking**: LiteLLM's `success_callback` → Langfuse/Prometheus
2. **Rate limiting**: LiteLLM's built-in RPM/TPM controls
3. **Fallback chains**: LiteLLM's `Router` with fallback lists
4. **Caching**: LiteLLM's semantic caching (or Redis)
5. **Monitoring**: Prometheus + Grafana dashboards
6. **Budget guards**: Custom middleware or LiteLLM pre-call hooks

---

## 3. Integration Guide: RouteLLM + LiteLLM

### Architecture for Ahmed's Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Applications                        │
│                    (330 agent slots)                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LiteLLM Proxy (Port 4000)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Cost Tracking│  │ Rate Limiting│  │ Fallback Chains       │  │
│  │ (Langfuse)   │  │ (RPM/TPM)    │  │ (provider failover)   │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Caching      │  │ Budget Guards│  │ Observability         │  │
│  │ (Redis)      │  │ (per-slot)   │  │ (Prometheus)          │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  RouteLLM Server (Port 6060)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Controller                                               │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │   │
│  │  │ MF Router   │  │ BERT Router  │  │ SW-Ranking     │  │   │
│  │  │ (primary)   │  │ (low-latency)│  │ (fallback)     │  │   │
│  │  └─────────────┘  └──────────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
┌─────────────────────┐    ┌─────────────────────────┐
│  Strong Model       │    │  Weak Model             │
│  (GPT-4 / Claude)   │    │  (Mixtral / Llama /     │
│                     │    │   GPT-4o-mini)          │
└─────────────────────┘    └─────────────────────────┘
```

### Step-by-Step Integration

#### Step 1: Install RouteLLM

```bash
pip install "routellm[serve,eval]"
```

#### Step 2: Configure LiteLLM as the Outer Proxy

```yaml
# litellm_config.yaml
model_list:
  # RouteLLM as a "provider" — all model names get prefixed
  - model_name: "router-mf-*"  # Catch-all for RouteLLM models
    litellm_params:
      model: "openai/router-mf-0.5"  # OpenAI-compatible format
      api_base: "http://localhost:6060/v1"
      api_key: "not-needed"

  # Direct model access (bypass router for specific use cases)
  - model_name: "gpt-4"
    litellm_params:
      model: "gpt-4"
      api_key: os.environ/OPENAI_API_KEY

  - model_name: "gpt-4o-mini"
    litellm_params:
      model: "gpt-4o-mini"
      api_key: os.environ/OPENAI_API_KEY

  # Fallback chain: try router first, fall back to direct
  - model_name: "smart-router"
    litellm_params:
      model: "openai/router-mf-0.5"
      api_base: "http://localhost:6060/v1"
      api_key: "not-needed"
      fallbacks: [{"gpt-4": ["OPENAI_API_KEY"]}]

litellm_settings:
  success_callback: ["langfuse"]  # Cost tracking
  failure_callback: ["langfuse"]
  cache:
    type: "redis"
    host: "localhost"
    port: 6379
    ttl: 3600

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

#### Step 3: Start RouteLLM Server

```bash
python -m routellm.openai_server \
  --routers mf bert \
  --strong-model gpt-4-1106-preview \
  --weak-model anyscale/mistralai/Mixtral-8x7B-Instruct-v0.1 \
  --port 6060
```

#### Step 4: Start LiteLLM Proxy

```bash
litellm --config litellm_config.yaml --port 4000
```

#### Step 5: Client Integration

```python
from openai import OpenAI

# Point to LiteLLM (which sits in front of RouteLLM)
client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="sk-litellm-master-key"
)

# Route via RouteLLM through LiteLLM
response = client.chat.completions.create(
    model="router-mf-0.5",  # router-{type}-{threshold}
    messages=[{"role": "user", "content": "Hello!"}]
)

# Or use a different threshold for different use cases
# Lower threshold = more strong model calls = higher quality
# Higher threshold = fewer strong model calls = lower cost
response = client.chat.completions.create(
    model="router-mf-0.8",  # Cost-first: 80% weak model
    messages=[{"role": "user", "content": "Simple query"}]
)
```

### Alternative: Direct RouteLLM (No LiteLLM)

For simpler deployments, RouteLLM can be used directly:

```python
from routellm.controller import Controller

client = Controller(
    routers=["mf"],
    strong_model="gpt-4-1106-preview",
    weak_model="anyscale/mistralai/Mixtral-8x7B-Instruct-v0.1",
)

response = client.chat.completions.create(
    model="router-mf-0.5",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## 4. Configuration Examples

### Router Configuration (config.example.yaml)

```yaml
# Default config — points to HuggingFace checkpoints
mf:
  checkpoint_path: routellm/mf_gpt4_augmented

bert:
  checkpoint_path: routellm/bert_gpt4_augmented

causal_llm:
  checkpoint_path: routellm/causal_llm_gpt4_augmented

sw_ranking:
  arena_battle_datasets:
    - lmsys/lmsys-arena-human-preference-55k
    - routellm/gpt4_judge_battles
  arena_embedding_datasets:
    - routellm/arena_battles_embeddings
    - routellm/gpt4_judge_battles_embeddings
```

### Threshold Calibration

```bash
# Calibrate for 50% strong model calls (quality-first)
python -m routellm.calibrate_threshold \
  --routers mf \
  --strong-model-pct 0.5 \
  --config config.example.yaml
# Output: threshold = 0.11593

# Calibrate for 20% strong model calls (cost-first)
python -m routellm.calibrate_threshold \
  --routers mf \
  --strong-model-pct 0.2 \
  --config config.example.yaml
# Output: threshold ≈ 0.35 (approximate)

# Calibrate for 80% strong model calls (maximum quality)
python -m routellm.calibrate_threshold \
  --routers mf \
  --strong-model-pct 0.8 \
  --config config.example.yaml
# Output: threshold ≈ 0.02 (approximate)
```

### Custom Router Training (MF Router)

```python
# train_matrix_factorization.py — simplified
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# 1. Prepare preference data
# Format: [{"prompt": "...", "model_a": "...", "model_b": "...", "winner": "model_a"}]
data = load_preference_data("my_battles.jsonl")

# 2. Pre-compute embeddings (one-time cost)
# Use OpenAI text-embedding-3-small (1536-dim)
embeddings = compute_embeddings([d["prompt"] for d in data])
np.save("prompt_embeddings.npy", embeddings)

# 3. Define model
class MFModel_Train(nn.Module):
    def __init__(self, num_models=64, dim=128, text_dim=1536):
        super().__init__()
        self.P = nn.Embedding(num_models, dim)          # Model embeddings
        self.Q = nn.Embedding(num_prompts, text_dim)      # Prompt embeddings (frozen)
        self.text_proj = nn.Linear(text_dim, dim, bias=False)
        self.classifier = nn.Linear(dim, 1, bias=False)

    def forward(self, model_win, model_loss, prompt_idx):
        # Bradley-Terry preference model
        diff = normalize(self.P(model_win)) - normalize(self.P(model_loss))
        prompt_proj = self.text_proj(self.Q(prompt_idx))
        logit = self.classifier(diff * prompt_proj)
        return logit

# 4. Training loop
model = MFModel_Train()
optimizer = torch.optim.Adam(model.parameters(), lr=3e-4, weight_decay=1e-5)
criterion = nn.BCEWithLogitsLoss()

for epoch in range(100):
    for batch in DataLoader(dataset, batch_size=64):
        logit = model(batch.model_win, batch.model_loss, batch.prompt_idx)
        loss = criterion(logit, torch.ones_like(logit))  # Label always 1
        loss.backward()
        optimizer.step()

# 5. Push to HuggingFace Hub
model.push_to_hub("myorg/my_mf_router")
```

### Custom Router Implementation

```python
# my_router.py
from routellm.routers import Router

class MyCustomRouter(Router):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load your model here

    def calculate_strong_win_rate(self, prompt: str) -> float:
        """
        Returns: float in [0, 1]
        Probability that the strong model will outperform the weak model
        on this specific prompt.
        """
        # Your routing logic here
        return self.my_model.predict(prompt)

# Register in ROUTER_CLS dictionary
from routellm.routers import ROUTER_CLS
ROUTER_CLS["my_router"] = MyCustomRouter
```

### LiteLLM Router Config for Multi-Provider Fallback

```yaml
# litellm_routing.yaml
model_list:
  - model_name: "smart-agent"
    litellm_params:
      model: "openai/router-mf-0.5"
      api_base: "http://localhost:6060/v1"
      api_key: "not-needed"
      # Fallback chain if RouteLLM server is down
      fallbacks:
        - model: "gpt-4o-mini"
          api_key: os.environ/OPENAI_API_KEY
        - model: "claude-3-haiku-20240307"
          api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: "budget-agent"
    litellm_params:
      model: "openai/router-mf-0.8"  # More aggressive cost savings
      api_base: "http://localhost:6060/v1"
      api_key: "not-needed"

  - model_name: "quality-agent"
    litellm_params:
      model: "openai/router-mf-0.2"  # Quality-first
      api_base: "http://localhost:6060/v1"
      api_key: "not-needed"

litellm_settings:
  routing_strategy: "least-busy"  # or "latency-based-routing"
  request_timeout: 60
  num_retries: 3
  retry_after: 5
```

---

## 5. Comparison with Other Routing Strategies

### RouteLLM vs Commercial Systems

| System | Type | MT-Bench Score | GPT-4 Usage | Relative Cost | Status |
|--------|------|---------------|-------------|---------------|--------|
| **RouteLLM (mf)** | Open-source | 8.76 | 25.4% | 1.00x | Dormant since Aug 2024 |
| **Unify AI** | Commercial | 8.76 | 45.6% | 1.80x | Pivoted to agent runtime |
| **Martian** | Commercial | 8.31 | ~50% | 1.68x | Pivoted to interpretability |
| **Not Diamond** | Commercial | — | — | — | Active (supplier to OpenRouter) |

**Key finding**: RouteLLM matches commercial quality while using 40-44% fewer GPT-4 calls.

### RouteLLM vs Other Open-Source Approaches

| Approach | Mechanism | Cost Savings | Latency Overhead | Training Required | Best For |
|----------|-----------|-------------|-----------------|-------------------|----------|
| **RouteLLM** | Pre-call classification | 35-85% | 15-500ms | Pre-trained available | General-purpose routing |
| **LiteLLM Router** | Load balancing / failover | 30-50% | ~0ms | None | Provider failover, not quality routing |
| **FrugalGPT** | Cascading (cheap → expensive) | Up to 98% | High (sequential calls) | Scorer model | Classification tasks |
| **Semantic Router** | Intent-based routing | Varies | ~10ms | Intent classifier | Known intent categories |
| **vLLM Semantic Router** | Intent + reasoning toggle | ~48% token reduction | Low | None | vLLM-served models |
| **OpenRouter Auto** | Cheapest provider for same model | Varies | ~0ms | None | Multi-provider aggregation |

### When to Use What

```
┌─────────────────────────────────────────────────────────────┐
│  Do you know which model you want?                          │
│  ├── YES → OpenRouter Auto / LiteLLM Router (aggregation)   │
│  └── NO  → Do you want the cheapest acceptable model?       │
│           ├── YES → RouteLLM (semantic routing)              │
│           └── NO  → Do you need multi-step reasoning?       │
│                     ├── YES → FrugalGPT cascade             │
│                     └── NO  → RouteLLM with low threshold   │
└─────────────────────────────────────────────────────────────┘
```

### RouteLLM vs LiteLLM: Complementary, Not Competing

| Dimension | RouteLLM | LiteLLM |
|-----------|----------|---------|
| **Primary function** | Model selection (which LLM?) | Provider management (which API?) |
| **Routing logic** | Learned from preference data | Load balancing, failover, least-busy |
| **Cost optimization** | Avoid over-provisioning | Avoid provider markup |
| **Quality optimization** | Yes (predicts quality needs) | No (assumes same model = same quality) |
| **Best used** | Inside LiteLLM as a provider | As the outer proxy/gateway |

**Recommendation**: Use both. LiteLLM as the gateway (cost tracking, rate limiting, failover), RouteLLM as a provider inside LiteLLM (intelligent model selection).

---

## 6. Pitfalls and Best Practices

### Pitfalls

#### 1. Domain Mismatch (Critical)

> RouteLLM's routers are trained on Chatbot Arena data, which skews toward open-ended, conversational queries. If your production traffic is highly domain-specific — medical coding, legal clause analysis, semiconductor design — the router's complexity predictions may be poorly calibrated.

**Mitigation**: Collect domain-specific preference data and fine-tune the router before deploying. Even 1,500 labeled samples (2% of training data) can dramatically improve performance.

#### 2. Binary Routing Limitation

RouteLLM only supports **two-model routing**. If you have 5+ models in your stack (e.g., GPT-4, Claude, Mixtral, Llama, GPT-4o-mini), you need to either:
- Create multiple RouteLLM instances with different model pairs
- Use a cascade: RouteLLM first, then LiteLLM Router for provider selection
- Train a custom N-way router

#### 3. Stale Repository

The repository has had **no commits since August 2024**. This means:
- No bug fixes for newer model APIs
- No support for newer embedding models
- Potential compatibility issues with newer LiteLLM versions
- No community support for new issues

**Mitigation**: Fork and maintain internally, or use as-is with thorough testing.

#### 4. Embedding API Dependency

The `mf` and `sw_ranking` routers require an OpenAI Embedding API call at inference time (~50ms). This adds:
- Latency overhead
- API cost (~$0.02/1M tokens for text-embedding-3-small)
- A dependency on OpenAI's embedding service

**Mitigation**: Use the `bert` router for fully local inference, or cache embeddings for repeated queries.

#### 5. Threshold Calibration Drift

The optimal threshold depends on your query distribution. If your traffic mix changes (e.g., more complex queries during certain seasons), the threshold may need recalibration.

**Mitigation**: Set up a recurring calibration pipeline. Monitor the strong-model call rate and recalibrate weekly.

#### 6. No Built-in Observability

RouteLLM does not expose:
- Per-request routing decisions
- Cost attribution by router
- Quality metrics
- A/B testing between routers

**Mitigation**: Add logging middleware at the LiteLLM layer. Use LiteLLM's `success_callback` to forward all requests to Langfuse/Prometheus.

#### 7. Router Overhead Cost

The paper reports router overhead costs:
- GPU-based routers (MF, BERT): ~$0.001-0.01 per 1,000 requests on a g2-standard-4 VM
- CPU-based routers (SW-Ranking): ~$0.01-0.10 per 1,000 requests on n2-standard-8

For 330 agent slots at ~100 requests/day each = 33K requests/day, router overhead is negligible (<$1/day).

### Best Practices

#### 1. Start with the MF Router

The matrix factorization router is:
- Best-performing on benchmarks
- Lightweight (~1ms inference after embedding)
- Pre-trained and available on HuggingFace
- Generalizes well to unseen model pairs

#### 2. Calibrate Thresholds Per Use Case

Don't use a single threshold for all traffic. Instead:

| Use Case | Threshold | Strong Model % | Rationale |
|----------|-----------|---------------|-----------|
| Customer-facing chat | 0.3 | ~30% | Quality matters, but most queries are simple |
| Internal agent tasks | 0.7 | ~70% | Cost-first, agents can retry |
| Code generation | 0.2 | ~20% | Quality critical for code |
| Batch processing | 0.9 | ~90% | Maximum cost savings |
| Complex reasoning | 0.1 | ~10% | Near-GPT-4 quality |

#### 3. Implement a Shadow Mode

Before fully deploying, run RouteLLM in **shadow mode**:
- Route all requests to both models
- Log the routing decision without acting on it
- Compare quality metrics between routed and non-routed
- Gradually shift traffic to routed responses

#### 4. Use Data Augmentation for Custom Routers

If training a custom router:
1. Start with Chatbot Arena data (80K battles)
2. Add GPT-4-as-judge labels for your domain (~25K samples)
3. Add golden-labeled data from your evaluation set (~1,500 samples)
4. This 2% augmentation can improve APGR by 60%+

#### 5. Monitor the Strong-Model Call Rate

Set up alerts for:
- Strong-model call rate exceeding target by >10%
- Router latency exceeding 100ms p99
- Quality metrics (user feedback, task success rate) dropping below baseline

#### 6. Implement a Fallback Chain

```
Request → RouteLLM (mf router)
  ├── Success → Route to strong/weak model
  ├── Router timeout → Route to strong model (safe default)
  ├── Router error → Route to strong model (safe default)
  └── Strong model fails → LiteLLM fallback to next provider
```

#### 7. Version Your Router Configurations

```yaml
# router_configs/
# v1.yaml — initial deployment
mf:
  checkpoint_path: routellm/mf_gpt4_augmented
  threshold: 0.5

# v2.yaml — after domain fine-tuning
mf:
  checkpoint_path: myorg/mf_gpt4_augmented_v2
  threshold: 0.4
```

#### 8. Cost Monitoring Dashboard

Track these metrics per agent slot:
- **Cost per request** (split by strong/weak)
- **Strong-model call rate** (should match calibrated target)
- **Quality score** (user feedback, task completion rate)
- **Router overhead** (latency, API costs)
- **Savings vs. baseline** (all-strong-model cost)

---

## Summary: Recommendation for Ahmed's 330-Slot Deployment

### Recommended Stack

```
LiteLLM (gateway) → RouteLLM (router) → Strong/Weak models
     ↓                    ↓
Cost tracking      Routing decisions
Rate limiting      Threshold per use case
Fallback chains    Shadow mode → full deploy
```

### Expected Outcomes

| Metric | Current (All GPT-4) | With RouteLLM | Savings |
|--------|---------------------|---------------|---------|
| Cost per M tokens | $24.70 | ~$6.60 | **73%** |
| Quality (MT-Bench) | 9.3 | 8.8 (95%) | -5% |
| Strong model calls | 100% | ~26% | -74% |
| Router overhead | — | ~$0.50/day | Negligible |

### Implementation Timeline

| Phase | Duration | Activities |
|-------|----------|-----------|
| **1. Setup** | Week 1 | Install RouteLLM + LiteLLM, configure model pair |
| **2. Calibration** | Week 2 | Calibrate thresholds per use case, set up shadow mode |
| **3. Pilot** | Week 3-4 | Deploy to 10% of slots (33 agents), monitor quality |
| **4. Scale** | Week 5-6 | Roll out to all 330 slots, set up dashboards |
| **5. Optimize** | Ongoing | Fine-tune router on production data, recalibrate monthly |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Domain mismatch | Medium | High | Fine-tune on production data |
| Repo abandonment | High | Low | Fork internally, it's stable code |
| Quality regression | Low | Medium | Shadow mode, gradual rollout |
| Embedding API outage | Low | Medium | Use BERT router as fallback |
| Threshold drift | Medium | Low | Automated recalibration pipeline |

---

*Sources: [GitHub](https://github.com/lm-sys/RouteLLM), [Paper](https://arxiv.org/abs/2406.18665), [Blog](https://lmsys.org/blog/2024-07-01-routellm/), [Anyscale](https://www.anyscale.com/blog/building-an-llm-router-for-high-quality-and-cost-effective-responses)*
