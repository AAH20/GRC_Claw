# Deep-Dive Analysis: 567-labs/instructor

> **For:** Ahmed Hassan — 330 agent slots, production structured output validation
> **Date:** 2026-10-01
> **Library:** instructor (v1.15.x, ~14K stars, 3M+ monthly PyPI downloads)

---

## 1. Architecture Overview

Instructor is a **thin patch layer** over LLM provider SDKs — not a runtime, not an agent framework. It wraps `chat.completions.create()` (or equivalent) with three capabilities: schema translation, Pydantic validation, and automatic retry-with-feedback.

### Core Flow

```
User Code
  │
  ▼
Instructor Patched Client  ──►  Retry Layer (Tenacity)
  │                                │
  │                                ▼
  │                         Provider SDK (OpenAI/Anthropic/Gemini/...)
  │                                │
  │                                ▼
  │                         Raw Response
  │                                │
  │                                ▼
  │                         Dispatcher (process_response)
  │                                │
  │                    ┌───────────┴───────────┐
  │                    ▼                       ▼
  │              Mode Handler           Pydantic Validation
  │           (TOOLS/JSON/STRICT)              │
  │                                            ▼
  │                                     Validated Model
  │                                            │
  └────────────────────────────────────────────┘
                       │
                       ▼
              On validation failure:
              handle_reask_kwargs() appends error
              to conversation → retry loop
```

### Key Components

| Component | File | Responsibility |
|---|---|---|
| `from_provider()` | `instructor/auto_client.py` | Universal factory — picks optimal Mode per provider |
| `patch()` | `instructor/core/patch.py` | Wraps provider `create()` with cache, templating, hooks, retry |
| `retry.py` | `instructor/core/retry.py` | Tenacity-backed retry loop with validation feedback |
| `process_response.py` | `instructor/processing/response.py` | Mode-based parsing, multimodal conversion, `_raw_response` attachment |
| `hooks.py` | `instructor/core/hooks.py` | Event bus for observability |
| `Mode` enum | `instructor/mode.py` | TOOLS, JSON, MD_JSON, TOOLS_STRICT, JSON_SCHEMA, RESPONSES_TOOLS |

### Mode System

The `Mode` enum determines how the Pydantic schema is delivered to the model:

| Mode | Mechanism | Reliability | Providers |
|---|---|---|---|
| `TOOLS` | Native function calling | Highest | OpenAI, Anthropic, Gemini, Groq |
| `TOOLS_STRICT` | OpenAI strict JSON-schema decoding | Very high | OpenAI only |
| `JSON_SCHEMA` | Provider-enforced JSON Schema | High | OpenAI, Mistral, Anthropic |
| `JSON` | JSON in message body | Medium | Most providers |
| `MD_JSON` | Extract JSON from markdown code block | Lowest | Fallback for limited providers |
| `RESPONSES_TOOLS` | OpenAI Responses API | High | OpenAI only |

**Critical insight:** Picking a weaker mode silently degrades reliability. Default to `TOOLS` whenever the provider supports it.

### Retry Mechanism

When Pydantic validation fails:
1. `ValidationError` is caught
2. `handle_reask_kwargs()` appends the error message to the conversation
3. The model is re-prompted with the error feedback
4. Loop continues up to `max_retries` (default: 3)
5. On exhaustion: `InstructorRetryException` with full context (`failed_attempts`, `last_completion`, `create_kwargs`)

---

## 2. Key Features for Ahmed's Stack

### 2.1 Structured Output (Pydantic-Native)

```python
from pydantic import BaseModel, Field
import instructor

class AgentSlot(BaseModel):
    slot_id: str
    agent_name: str
    task_type: str
    priority: int = Field(ge=1, le=5)
    input_data: dict
    expected_output_schema: dict

client = instructor.from_provider("openai/gpt-4o-mini")
slot = client.chat.completions.create(
    response_model=AgentSlot,
    messages=[{"role": "user", "content": "Extract slot config from: ..."}],
)
```

**Why it matters for 330 agent slots:** Every slot's output is a validated Pydantic instance — type-safe, IDE-autocomplete-ready, no manual JSON parsing.

### 2.2 Retry-with-Error-Feedback

The self-healing loop is the core value proposition:

```python
from pydantic import BaseModel, field_validator

class TaskResult(BaseModel):
    status: str
    confidence: float
    reasoning: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        allowed = {"pending", "running", "completed", "failed"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}, got '{v}'")
        return v

# If model returns status="in_progress", Instructor:
# 1. Catches ValidationError
# 2. Sends: "Status must be one of {'pending', 'running', 'completed', 'failed'}, got 'in_progress'"
# 3. Model corrects itself
# 4. Returns valid TaskResult
```

**Recovery rate:** >95% for schemas under 15 fields with descriptive validator messages.

### 2.3 Multi-Provider Support

One code path, 15+ providers:

```python
# OpenAI
client = instructor.from_provider("openai/gpt-4o-mini")

# Anthropic
client = instructor.from_provider("anthropic/claude-3-5-sonnet")

# Google Gemini
client = instructor.from_provider("google/gemini-2.5-flash")

# Local (Ollama)
client = instructor.from_provider("ollama/llama3.2")

# Any OpenAI-compatible endpoint
client = instructor.from_provider("openai/gpt-4o", base_url="http://localhost:8000/v1")
```

**For Ahmed's 330 slots:** Provider-agnostic slot output validation. Swap models without changing slot logic.

### 2.4 Streaming (Partial + Iterable)

```python
from instructor import Partial

# Stream partial objects as tokens arrive
stream = client.chat.completions.create_partial(
    response_model=AgentSlot,
    messages=[{"role": "user", "content": "Extract: ..."}],
)
for partial in stream:
    print(partial.slot_id)  # Updates incrementally

# Stream a list of objects
for item in client.chat.completions.create_iterable(
    response_model=AgentSlot,
    messages=[{"role": "user", "content": "Extract all slots: ..."}],
):
    process(item)  # Each item validated as it arrives
```

### 2.5 Hooks for Observability

```python
from instructor.core.hooks import HookName

client.on(HookName.COMPLETION_KWARGS, lambda **kw: log_request(kw))
client.on(HookName.COMPLETION_RESPONSE, lambda resp: log_response(resp))
client.on(HookName.PARSE_ERROR, lambda e: log_validation_error(e))
client.on(HookName.COMPLETION_LAST_ATTEMPT, lambda e, **kw: alert_on_failure(e))
client.on(HookName.COMPLETION_USAGE, lambda usage, **kw: track_tokens(usage))
```

---

## 3. Integration Guide: Instructor + Hermes Agent

### 3.1 Hermes Agent's Built-in Instructor Skill

Hermes Agent ships an official instructor skill at `optional-skills/mlops/instructor/SKILL.md`. Install it:

```bash
hermes skills install official/mlops/instructor
```

This skill provides the agent with instructions for using Instructor when it needs structured LLM outputs.

### 3.2 Architecture for Agent Tool Outputs

For Ahmed's 330 agent slots, the integration pattern is:

```
Hermes Agent (orchestrator)
  │
  ├── Tool: extract_slot_config()
  │     └── Instructor client → LLM → Validated AgentSlot
  │
  ├── Tool: validate_agent_output()
  │     └── Pydantic model → validate raw agent output
  │
  ├── Tool: batch_classify()
  │     └── Instructor iterable → stream of validated results
  │
  └── Tool: structured_reasoning()
        └── Instructor with custom Mode → typed reasoning trace
```

### 3.3 Custom Tool Definition Pattern

```python
# hermes_tools.py — custom tool for Hermes Agent
import instructor
from pydantic import BaseModel, Field
from typing import Literal

class SlotOutput(BaseModel):
    slot_id: str
    status: Literal["success", "failure", "timeout"]
    result: dict
    confidence: float = Field(ge=0.0, le=1.0)
    error_message: str | None = None

def create_slot_extractor(model: str = "openai/gpt-4o-mini"):
    """Factory: returns a tool function that uses Instructor for structured output."""
    client = instructor.from_provider(model)

    def extract_slot(raw_output: str) -> SlotOutput:
        return client.chat.completions.create(
            response_model=SlotOutput,
            messages=[{
                "role": "user",
                "content": f"Parse this agent output into structured form:\n\n{raw_output}"
            }],
            max_retries=3,
            temperature=0,  # Greedy for extraction
        )

    return extract_slot
```

### 3.4 Async Integration

```python
import asyncio
import instructor
from pydantic import BaseModel

class AgentResult(BaseModel):
    agent_id: str
    output: dict
    latency_ms: float

async def process_slot_async(slot_input: dict) -> AgentResult:
    client = instructor.from_provider("openai/gpt-4o-mini", async_client=True)
    return await client.chat.completions.create(
        response_model=AgentResult,
        messages=[{"role": "user", "content": str(slot_input)}],
        max_retries=3,
    )

# Process 330 slots concurrently
async def process_all_slots(slots: list[dict]) -> list[AgentResult]:
    semaphore = asyncio.Semaphore(50)  # Rate limit

    async def bounded(slot):
        async with semaphore:
            return await process_slot_async(slot)

    return await asyncio.gather(*(bounded(s) for s in slots))
```

### 3.5 Provider Fallback Pattern

```python
import instructor
from pydantic import BaseModel

class SlotConfig(BaseModel):
    slot_id: str
    parameters: dict
    retry_policy: dict

PRIMARY_MODEL = "openai/gpt-4o-mini"
FALLBACK_MODEL = "anthropic/claude-3-5-sonnet"

def extract_with_fallback(raw_text: str) -> SlotConfig:
    """Try primary model, fall back to secondary on repeated failure."""
    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        client = instructor.from_provider(model)
        try:
            return client.chat.completions.create(
                response_model=SlotConfig,
                messages=[{"role": "user", "content": raw_text}],
                max_retries=2,
                temperature=0,
            )
        except instructor.InstructorRetryException:
            continue  # Try next provider
    raise RuntimeError("All providers failed")
```

---

## 4. Configuration Examples

### 4.1 Basic Structured Output

```python
import instructor
from pydantic import BaseModel, Field
from typing import Optional

class AgentSlotOutput(BaseModel):
    slot_id: str = Field(description="Unique slot identifier")
    agent_name: str = Field(description="Name of the agent that ran")
    status: str = Field(description="Execution status")
    result: dict = Field(description="Agent output data")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    error: Optional[str] = Field(default=None, description="Error message if failed")

client = instructor.from_provider("openai/gpt-4o-mini")

output = client.chat.completions.create(
    response_model=AgentSlotOutput,
    messages=[{"role": "user", "content": "Extract from: slot_42 returned {...}"}],
    max_retries=3,
    temperature=0,
)
```

### 4.2 Nested Models with Validators

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal
import instructor

class RetryPolicy(BaseModel):
    max_attempts: int = Field(ge=1, le=10)
    backoff: Literal["fixed", "exponential"] = "exponential"
    base_delay_seconds: float = Field(ge=0.1, le=60.0)

class SlotConfig(BaseModel):
    slot_id: str
    model: str
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    max_tokens: int = Field(ge=1, le=8192, default=2048)
    retry_policy: RetryPolicy
    tags: list[str] = Field(default_factory=list)

    @field_validator("model")
    @classmethod
    def known_model(cls, v):
        known = {"gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "claude-3-haiku"}
        if v not in known:
            raise ValueError(f"Model must be one of {known}")
        return v

    @model_validator(mode="after")
    def temp_consistency(self):
        if self.model == "gpt-4o-mini" and self.temperature > 1.0:
            raise ValueError("gpt-4o-mini works best with temperature <= 1.0")
        return self

client = instructor.from_provider("openai/gpt-4o-mini")
config = client.chat.completions.create(
    response_model=SlotConfig,
    messages=[{"role": "user", "content": "Parse this slot config: ..."}],
    max_retries=3,
)
```

### 4.3 Streaming Partial Objects

```python
from instructor import Partial
import instructor

class DetailedSlotReport(BaseModel):
    slot_id: str
    summary: str
    findings: list[str]
    recommendations: list[str]
    risk_score: float

client = instructor.from_provider("openai/gpt-4o")

# Stream partial results for real-time UI updates
stream = client.chat.completions.create_partial(
    response_model=DetailedSlotReport,
    messages=[{"role": "user", "content": "Analyze slot 42's execution..."}],
)

for partial in stream:
    # partial is a progressively-filled DetailedSlotReport
    # Validators only run on the final complete object
    print(f"Slot: {partial.slot_id}, Findings so far: {len(partial.findings)}")
```

### 4.4 Iterable (Batch Extraction)

```python
import instructor

class SlotResult(BaseModel):
    slot_id: str
    success: bool
    output: dict

client = instructor.from_provider("openai/gpt-4o-mini")

# Stream a list of results — each validated as it arrives
results = []
for result in client.chat.completions.create_iterable(
    response_model=SlotResult,
    messages=[{"role": "user", "content": "Extract all 330 slot results: ..."}],
    max_retries=2,
):
    results.append(result)
    print(f"Processed {len(results)} slots...")

print(f"Total: {len(results)} slots, {sum(r.success for r in results)} successful")
```

### 4.5 Custom Mode Selection

```python
import instructor

client = instructor.from_provider(
    "openai/gpt-4o-mini",
    mode=instructor.Mode.TOOLS_STRICT,  # Force strict JSON-schema decoding
)

# Or for Anthropic
client = instructor.from_provider(
    "anthropic/claude-3-5-sonnet",
    mode=instructor.Mode.TOOLS,
)
```

### 4.6 Hooks for Production Monitoring

```python
import instructor
import logging
from instructor.core.hooks import HookName

logger = logging.getLogger("slot_extractor")

client = instructor.from_provider("openai/gpt-4o-mini")

# Track every retry
def on_parse_error(error):
    logger.warning(f"Validation failed: {error}")

def on_last_attempt(error, *, attempt_number, max_attempts, is_last_attempt):
    if is_last_attempt:
        logger.error(f"All {max_attempts} attempts exhausted")

def on_usage(usage, *, attempt_number):
    logger.info(f"Attempt {attempt_number}: {usage.total_tokens} tokens")

client.on(HookName.PARSE_ERROR, on_parse_error)
client.on(HookName.COMPLETION_LAST_ATTEMPT, on_last_attempt)
client.on(HookName.COMPLETION_USAGE, on_usage)
```

### 4.7 Tenacity Custom Retry Policy

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import instructor
from openai import RateLimitError, APITimeoutError

client = instructor.from_provider("openai/gpt-4o-mini")

# Pass a custom Tenacity Retrying object for full control
from tenacity import Retrying

custom_retry = Retrying(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
)

result = client.chat.completions.create(
    response_model=SlotConfig,
    messages=[{"role": "user", "content": "..."}],
    max_retries=custom_retry,  # Tenacity Retrying object
)
```

---

## 5. Comparison: Instructor vs PydanticAI vs Outlines

| Dimension | Instructor | Pydantic AI | Outlines |
|---|---|---|---|
| **Approach** | Post-generation validation + retry | Post-generation validation + retry | Pre-generation FSM constraints |
| **Schema guarantee** | High (via retry) | High (via reflection) | 100% guaranteed |
| **Provider coverage** | 15+ (OpenAI, Anthropic, Gemini, Ollama, Mistral, DeepSeek...) | 20+ hosted providers | Local models, vLLM, TGI, some hosted |
| **Requires local weights** | No | No | Usually yes |
| **Streaming** | Yes (partial + iterable) | Yes (token-level) | Yes |
| **Multi-language SDKs** | Python, TS, Go, Ruby, Rust, Elixir | Python only | Python only |
| **Agent/tool support** | No, extraction only | Yes, first-class | No |
| **Best for** | API-based extraction, migration from raw SDK | New agent projects, tool-heavy workflows | High-throughput self-hosted inference |
| **GitHub stars** | ~14K | ~14.5K | ~13.3K |
| **Maturity** | Most mature (2023) | Rapid release cadence | Maturing (Rust port in 2026) |
| **Setup time** | ~15 min | ~30 min | ~3 hours (incl. model load) |
| **p95 latency** | ~2.4s (with retries) | ~2.5s | ~1.8s (local) |
| **Valid output rate** | 96.3% | 96.8% | 100% |
| **Avg retries/call** | 0.18 | 0.16 | 0.00 |

### Decision Matrix for Ahmed's Stack

| Scenario | Recommendation | Why |
|---|---|---|
| 330 slots need structured output validation | **Instructor** | Multi-provider, proven at scale, minimal code |
| Building new agent workflows with tools | **Pydantic AI** | Agent loop, dependency injection, message history |
| High-volume batch classification (>100K/day) | **Outlines** | Zero retries, 100% compliance, lower per-call cost |
| Mixed: some extraction, some agents | **Instructor + Pydantic AI** | Use Instructor for extraction endpoints, Pydantic AI for agent runs |
| Self-hosted models with strict compliance needs | **Outlines** | Token-level constraints, no retry overhead |

### When to Choose What

```
Are you self-hosting the model?
├── YES → Outlines (100% guarantee, zero retries)
└── NO → Are you building an agent (tools, memory, multi-step)?
    ├── YES → Pydantic AI (agent framework)
    └── NO → Instructor (lightest extraction layer)
```

---

## 6. Pitfalls and Best Practices

### Pitfalls

1. **Retries multiply spend and latency.** Each retry is a full round trip with schema + prior error re-sent. A model that reliably fails one field can silently triple your token bill. Set `max_retries` deliberately (2-4 is usually enough).

2. **Schema is prompt overhead.** The model schema is injected into every request. Large, deeply-nested models add meaningful input tokens on every call, including retries. Keep schemas lean.

3. **Strict mode is not universal.** OpenAI-style strict JSON-schema decoding rejects many valid Pydantic constructs (certain unions, unbounded dicts, some default/optional patterns). A model that validates in Python may not be expressible as a strict schema.

4. **`response_model=list[Foo]` is a footgun.** Use `client.chat.completions.create_iterable(response_model=Foo)` instead — it streams one Foo at a time, while `response_model=list[Foo]` waits for the full array and is much slower.

5. **Default `max_retries` is 1 in some versions.** Many users assume "infinite retry until valid." Check your version's default and set explicitly.

6. **Validator error messages are the retry prompt.** Default Pydantic error messages are technical and model-unfriendly. Custom error messages dramatically improve retry success rates.

7. **Temperature > 0 with retries wastes API calls.** At temperature=0, retries may produce the same invalid output repeatedly. At temperature > 0, retries have a genuine chance of succeeding. Set `temperature=0` for extraction tasks.

8. **No built-in observability for retry rates.** You need external monitoring. A rising retry rate is usually a prompt or schema regression, not noise.

9. **Gemini does not support Union types** (except `Optional`). Use separate response models or `Literal` types instead.

10. **Partial objects don't run validators.** When streaming, validators only run on the final complete object. Partial objects may not satisfy every validator — this is by design.

### Best Practices

1. **Write validator messages as if instructing the model, not a human developer.**
   ```python
   # Bad
   raise ValueError("Value is not a valid integer")
   # Good
   raise ValueError(f"Field 'age' must be a whole number between 1 and 120. You provided '{v}' - please convert to an integer.")
   ```

2. **Set `temperature=0` for extraction tasks.** You want the most likely valid output, not creative variation.

3. **Use `Field(description=...)` liberally.** Descriptions become part of the schema sent to the model and directly shape output quality.

4. **Log `InstructorRetryException` with full context.** The exception contains `failed_attempts`, `last_completion`, and `create_kwargs` for reproduction.

5. **Monitor retry rates.** Alert when retry rate exceeds threshold — it signals schema/prompt regression.

6. **Use `create_iterable` for >5 items.** It's faster and more memory-efficient than waiting for a full array.

7. **Cache compiled schemas.** Instructor memoizes schema conversion with `lru_cache(maxsize=256)`, but for custom schemas, pre-compile at startup.

8. **Handle `InstructorRetryException` explicitly.** Never silently swallow it. Decide on a fallback: return None, return a default model, route to a more capable model, or queue for human review.

9. **Use hooks for production observability.** Emit metrics on `completion:usage`, `parse:error`, and `completion:last_attempt`.

10. **Keep schemas under 15 fields when possible.** Retry recovery rates drop significantly with deeply nested or wide schemas. Split large schemas into smaller, composable models.

### Production Checklist

- [ ] `max_retries` set explicitly (2-4 for most use cases)
- [ ] `temperature=0` for extraction tasks
- [ ] Custom validator error messages (model-friendly language)
- [ ] `Field(description=...)` on all fields
- [ ] Hooks registered for observability
- [ ] `InstructorRetryException` handling with fallback strategy
- [ ] Retry rate monitoring and alerting
- [ ] Schema size kept lean (avoid deep nesting)
- [ ] `create_iterable` used for batch extraction
- [ ] Provider fallback configured for critical paths

---

## Sources

- [Instructor GitHub](https://github.com/567-labs/instructor) — Official repository
- [Instructor Architecture Docs](https://python.useinstructor.com/architecture) — Official architecture documentation
- [Instructor Hooks Docs](https://python.useinstructor.com/concepts/hooks) — Official hooks documentation
- [Hermes Agent Instructor Skill](https://hermes-agent.nousresearch.com/docs/user-guide/skills/optional/mlops/mlops-instructor) — Official Hermes integration
- [Structured LLM Outputs in Python (2026)](https://pythondatabench.com/article/structured-llm-outputs-python-instructor-outlines-pydantic-ai-2026) — Comparison analysis
- [BAML vs Instructor vs Outlines vs Pydantic AI](https://aicraftguide.com/article/baml-vs-instructor-vs-outlines-pydantic-ai-structured-output-2026) — Production benchmarking
- [Instructor Production Guide](https://engineersofai.com/docs/llms/structured-generation/instructor-library) — Production patterns
