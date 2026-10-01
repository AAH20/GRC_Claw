# DeepEval Deep-Dive: Architecture, Features & Hermes Agent Integration Guide

> **Repository:** [confident-ai/deepeval](https://github.com/confident-ai/deepeval) — 18K+ stars, Apache-2.0
> **Red Teaming:** [confident-ai/deepteam](https://github.com/confident-ai/deepteam) — built on DeepEval
> **Use Case:** Ahmed Hassan — 330 agent slots, production agent quality evaluation at scale

---

## 1. Architecture Overview

### Core Concept: "Pytest for LLM Apps"

DeepEval is an open-source LLM evaluation framework that mirrors pytest's developer experience but is purpose-built for LLM applications. The mental model:

| Traditional Testing | DeepEval |
|---|---|
| `pytest test_math.py` | `deepeval test run test_agent.py` |
| `assert add(2,3) == 5` | `assert_test(test_case, [TaskCompletionMetric()])` |
| Unit tests for functions | Unit tests for LLM calls, tool calls, agent trajectories |
| Deterministic assertions | LLM-as-a-judge metrics with thresholds |

### Three-Layer Evaluation Architecture

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: End-to-End (Black-Box)                    │
│  LLMTestCase(input, actual_output, expected_output) │
│  → G-Eval, Answer Relevancy, Hallucination          │
├─────────────────────────────────────────────────────┤
│  Layer 2: Trajectory (Agent Full Trace)             │
│  @observe(type="agent") → complete execution tree    │
│  → TaskCompletion, StepEfficiency, PlanAdherence     │
├─────────────────────────────────────────────────────┤
│  Layer 3: Component (Individual Spans)              │
│  @observe(type="llm"/"tool"/"retriever")            │
│  → ToolCorrectness, ArgumentCorrectness, Faithfulness│
└─────────────────────────────────────────────────────┘
```

### Key Architectural Components

1. **Test Cases** — `LLMTestCase` (single-turn), `ConversationalTestCase` (multi-turn), `MLLMMTestCase` (multimodal)
2. **Metrics** — 50+ built-in metrics, all LLM-as-a-judge or deterministic
3. **Tracing** — `@observe` decorator instruments functions as spans; spans nest into traces
4. **Datasets** — `EvaluationDataset` with `Golden` reference test cases
5. **Pytest Plugin** — `deepeval test run` wraps pytest with LLM-specific flags
6. **Confident AI** — Optional cloud platform for trace visualization, dataset management, monitoring

### G-Eval: The Core Scoring Engine

G-Eval is DeepEval's most versatile metric, based on the paper *"NLG Evaluation using GPT-4 with Better Human Alignment"*:

```python
from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams

correctness = GEval(
    name="Correctness",
    criteria="Determine whether the actual output is factually correct based on the expected output.",
    evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
    threshold=0.5,
    rubric=[
        Rubric(score_range=(0, 2), expected_outcome="Factually incorrect."),
        Rubric(score_range=(3, 6), expected_outcome="Mostly correct."),
        Rubric(score_range=(7, 9), expected_outcome="Correct but missing minor details."),
        Rubric(score_range=(10, 10), expected_outcome="Fully correct and complete."),
    ],
)
```

**How it works:**
1. LLM generates evaluation steps (chain-of-thought)
2. LLM scores each step via form-filling paradigm
3. Probabilities of output tokens are normalized and weighted-summed
4. Final score: 0.0–1.0 with reasoning

### Task Completion: Agent Trajectory Evaluation

```python
from deepeval.tracing import observe
from deepeval.metrics import TaskCompletionMetric

@observe(type="agent", metrics=[TaskCompletionMetric(threshold=0.7)])
def my_agent(query: str) -> str:
    # Agent logic here
    pass
```

- **Self-explaining**: Outputs a reason for its score
- **Referenceless**: No expected outputs needed — task is inferred from trace
- **LLM-judged**: AlignmentScore between extracted Task and Outcome
- **Requires tracing**: Must use `@observe` to capture the full execution trace

---

## 2. Key Features for Ahmed's Stack

### 2.1 Agentic Metrics (Critical for 330 Agent Slots)

| Metric | Scope | What It Measures | Use For |
|---|---|---|---|
| `TaskCompletionMetric` | Trajectory | Did the agent accomplish its goal? | Primary agent quality gate |
| `ToolCorrectnessMetric` | Component | Were the right tools called? | Tool selection accuracy |
| `ArgumentCorrectnessMetric` | Component | Were tool arguments correct? | Parameter validation |
| `StepEfficiencyMetric` | Trajectory | Were unnecessary steps avoided? | Cost optimization |
| `PlanAdherenceMetric` | Trajectory | Did the agent follow its plan? | Reasoning quality |
| `PlanQualityMetric` | Trajectory | Was the plan logical/complete? | Planning ability |
| `GoalAccuracyMetric` | Trajectory | How accurately was the goal achieved? | Outcome precision |
| `MCPTaskCompletionMetric` | End-to-end | MCP-based agent task completion | MCP server agents |

### 2.2 Red Teaming: 40+ Vulnerabilities (DeepTeam)

DeepTeam is a **separate package** (`pip install deepteam`) built on DeepEval. It provides:

**Vulnerability Categories (50+):**

| Category | Vulnerabilities |
|---|---|
| **Data Privacy** | PII Leakage, Prompt Leakage |
| **Responsible AI** | Bias (gender/race/religion/political), Toxicity, Child Protection, Ethics, Fairness |
| **Security** | BFLA, BOLA, RBAC, Debug Access, Shell Injection, SQL Injection, SSRF, Tool Metadata Poisoning |
| **Agentic** | Goal Theft, Recursive Hijacking, Excessive Agency, Autonomous Agent Drift, Exploit Tool Agent, External System Abuse, Tool Orchestration Abuse, Agent Identity & Trust Abuse, Inter-Agent Communication Compromise |
| **Safety** | Illegal Activity, Graphic Content, Personal Safety, Unexpected Code Execution |
| **Business** | Misinformation, Intellectual Property, Competition |

**Adversarial Attack Methods (20+):**
- Single-turn: Prompt Injection, Roleplay, Leetspeak, ROT13, Base64, Gray Box, Math Problem, Multilingual, Prompt Probing, Adversarial Poetry, System Override, Permission Escalation, Goal Redirection, Authority Escalation, Emotional Manipulation
- Multi-turn: Linear Jailbreaking, Tree Jailbreaking, Crescendo Jailbreaking, Sequential Jailbreak, Bad Likert Judge

**Framework Alignment:** OWASP Top 10 for LLMs 2025, OWASP Top 10 for Agents 2026, NIST AI RMF, MITRE ATLAS, BeaverTails, Aegis

### 2.3 Additional Features

- **Synthetic Data Generation**: `deepeval generate` creates test cases from documents
- **Prompt Auto-Optimization**: Automatically improves prompts based on eval results
- **LLM Benchmarking**: MMLU, HellaSwag, DROP, BIG-Bench Hard, TruthfulQA, HumanEval, GSM8K
- **Multi-Modal**: Text, image, and audio evaluation
- **Custom Metrics**: Build your own with `BaseMetric` or `GEval`
- **14+ Judge Backends**: OpenAI, Azure OpenAI, Anthropic, Gemini, Bedrock, Vertex AI, LiteLLM, Ollama, OpenRouter

---

## 3. Integration Guide: Evaluating Hermes Agent with DeepEval

### 3.1 Architecture Mapping

Hermes Agent's architecture maps to DeepEval as follows:

```
Hermes Agent Component          → DeepEval Instrumentation
─────────────────────────────────────────────────────────
Agent loop (main orchestrator)  → @observe(type="agent")
LLM calls (Claude/Anthropic)    → @observe(type="llm")
Tool executions                 → @observe(type="tool")
Sub-agent dispatches            → @observe(type="agent") [nested]
Retrieval operations            → @observe(type="retriever")
```

### 3.2 Step-by-Step Integration

#### Step 1: Install

```bash
pip install -U deepeval deepteam
```

#### Step 2: Configure LLM Judge

```bash
# Option A: Use Anthropic as judge (matches Hermes's primary model)
deepeval set-anthropic --model claude-sonnet-4-6

# Option B: Use OpenAI as judge (default)
export OPENAI_API_KEY="sk-..."

# Option C: Use local Ollama model (free, offline)
deepeval set-ollama --model llama3.1:8b

# Option D: Use LiteLLM (100+ providers)
deepeval set-litellm --model gpt-4o-mini
```

#### Step 3: Instrument Hermes Agent

```python
# hermes_agent.py
from deepeval.tracing import observe, update_current_trace, update_current_span
from deepeval.metrics import TaskCompletionMetric, ToolCorrectnessMetric
from deepeval.test_case import ToolCall

# Tool-level instrumentation
@observe(type="tool", description="Execute shell command")
def execute_command(cmd: str) -> str:
    # Hermes's terminal tool
    result = run_terminal(cmd)
    update_current_span(input=cmd, output=result)
    return result

@observe(type="tool", description="Read file from filesystem")
def read_file(path: str) -> str:
    content = read_file_system(path)
    update_current_span(input=path, output=content)
    return content

@observe(type="tool", description="Search the web")
def web_search(query: str) -> str:
    results = search(query)
    update_current_span(input=query, output=results)
    return results

# LLM-level instrumentation
@observe(type="llm", model="claude-sonnet-4-6")
def call_claude(messages: list) -> str:
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        messages=messages,
    )
    output = response.content[0].text
    update_current_span(input=messages, output=output)
    return output

# Agent-level instrumentation (top-level orchestrator)
@observe(
    type="agent",
    available_tools=["execute_command", "read_file", "web_search", "browser_exec"],
    metrics=[TaskCompletionMetric(threshold=0.7)],
)
def hermes_agent(user_input: str) -> str:
    update_current_trace(
        name="hermes_agent_run",
        tags=["hermes", "production"],
        metadata={"agent_version": "2.0", "user_tier": "enterprise"},
    )
    # Main agent loop
    result = run_agent_loop(user_input)
    update_current_trace(input=user_input, output=result)
    return result
```

#### Step 4: Create Evaluation Dataset

```python
# dataset.py
from deepeval.dataset import EvaluationDataset, Golden

goldens = [
    Golden(
        input="Find the total revenue for Q3 2024 from the sales database",
        expected_output="Q3 2024 total revenue: $4.2M",
        metadata={"category": "data_retrieval", "difficulty": "medium"},
    ),
    Golden(
        input="Summarize the key points from the meeting notes in /docs/meeting.txt",
        expected_output="Summary covering: action items, decisions, deadlines",
        metadata={"category": "summarization", "difficulty": "easy"},
    ),
    Golden(
        input="Debug why the API returns 500 errors on the /users endpoint",
        expected_output="Root cause identified with fix recommendation",
        metadata={"category": "debugging", "difficulty": "hard"},
    ),
    # ... 330 agent slots → 330 goldens minimum
]

dataset = EvaluationDataset(goldens=goldens)
dataset.save_as("hermes_agent_goldens.json")
```

#### Step 5: Write Pytest Test Suite

```python
# tests/test_hermes_agent.py
import pytest
from deepeval import assert_test
from deepeval.dataset import EvaluationDataset
from deepeval.metrics import (
    TaskCompletionMetric,
    ToolCorrectnessMetric,
    GEval,
    AnswerRelevancyMetric,
)
from deepeval.test_case import LLMTestCase, SingleTurnParams

# Load dataset
dataset = EvaluationDataset()
dataset.load_from_json("hermes_agent_goldens.json")

# Define metrics
task_completion = TaskCompletionMetric(threshold=0.7)
tool_correctness = ToolCorrectnessMetric(threshold=0.8)

helpfulness = GEval(
    name="Helpfulness",
    criteria="Evaluate whether the agent's response is helpful, actionable, and addresses the user's request completely.",
    evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
    threshold=0.6,
)

relevancy = AnswerRelevancyMetric(threshold=0.7)

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_hermes_agent_task_completion(test_case: LLMTestCase):
    """Test that Hermes Agent completes tasks successfully."""
    assert_test(test_case, [task_completion])

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_hermes_agent_tool_usage(test_case: LLMTestCase):
    """Test that Hermes Agent uses tools correctly."""
    assert_test(test_case, [tool_correctness])

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_hermes_agent_helpfulness(test_case: LLMTestCase):
    """Test that Hermes Agent responses are helpful."""
    assert_test(test_case, [helpfulness])

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_hermes_agent_relevancy(test_case: LLMTestCase):
    """Test that Hermes Agent responses are relevant."""
    assert_test(test_case, [relevancy])
```

#### Step 6: Run Evaluations

```bash
# Run all tests
deepeval test run tests/test_hermes_agent.py

# Run with parallelism (recommended for 330 slots)
deepeval test run tests/test_hermes_agent.py -n 4

# Run with repeats (for flaky detection)
deepeval test run tests/test_hermes_agent.py -r 3

# Run with error handling
deepeval test run tests/test_hermes_agent.py -i -c -n 2

# Run specific test
deepeval test run tests/test_hermes_agent.py::test_hermes_agent_task_completion

# Run with verbose output
deepeval test run tests/test_hermes_agent.py -v
```

---

## 4. Configuration Examples

### 4.1 Complete Pytest Test Suite for Agents

```python
# tests/test_agent_suite.py
import pytest
from deepeval import assert_test, evaluate
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.metrics import (
    TaskCompletionMetric,
    ToolCorrectnessMetric,
    ArgumentCorrectnessMetric,
    StepEfficiencyMetric,
    PlanAdherenceMetric,
    GEval,
    AnswerRelevancyMetric,
    HallucinationMetric,
)
from deepeval.test_case import LLMTestCase, SingleTurnParams, ToolCall
from hermes_agent import hermes_agent

# ─── Metrics ───────────────────────────────────────────

task_completion = TaskCompletionMetric(
    threshold=0.7,
    model="claude-sonnet-4-6",
    include_reason=True,
)

tool_correctness = ToolCorrectnessMetric(
    threshold=0.8,
    model="claude-sonnet-4-6",
    include_reason=True,
)

argument_correctness = ArgumentCorrectnessMetric(
    threshold=0.75,
    model="claude-sonnet-4-6",
)

step_efficiency = StepEfficiencyMetric(
    threshold=0.6,
    model="claude-sonnet-4-6",
)

plan_adherence = PlanAdherenceMetric(
    threshold=0.65,
    model="claude-sonnet-4-6",
)

correctness = GEval(
    name="Correctness",
    criteria="Determine whether the actual output is factually correct based on the expected output.",
    evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
    threshold=0.7,
)

relevancy = AnswerRelevancyMetric(
    threshold=0.7,
    model="claude-sonnet-4-6",
)

hallucination = HallucinationMetric(
    threshold=0.6,
    model="claude-sonnet-4-6",
)

# ─── Test Cases ────────────────────────────────────────

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_agent_task_completion(test_case: LLMTestCase):
    """Primary gate: Did the agent complete the task?"""
    assert_test(test_case, [task_completion])

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_agent_tool_correctness(test_case: LLMTestCase):
    """Were the right tools called?"""
    assert_test(test_case, [tool_correctness])

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_agent_argument_correctness(test_case: LLMTestCase):
    """Were tool arguments correct?"""
    assert_test(test_case, [argument_correctness])

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_agent_step_efficiency(test_case: LLMTestCase):
    """Did the agent avoid unnecessary steps?"""
    assert_test(test_case, [step_efficiency])

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_agent_plan_adherence(test_case: LLMTestCase):
    """Did the agent follow its plan?"""
    assert_test(test_case, [plan_adherence])

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_agent_correctness(test_case: LLMTestCase):
    """Is the output factually correct?"""
    assert_test(test_case, [correctness])

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_agent_relevancy(test_case: LLMTestCase):
    """Is the output relevant to the input?"""
    assert_test(test_case, [relevancy])

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_agent_hallucination(test_case: LLMTestCase):
    """Does the output contain hallucinations?"""
    assert_test(test_case, [hallucination])

# ─── Combined Quality Gate ─────────────────────────────

@pytest.mark.parametrize("test_case", dataset.test_cases)
def test_agent_overall_quality(test_case: LLMTestCase):
    """Combined quality gate — all metrics must pass."""
    assert_test(test_case, [
        task_completion,
        tool_correctness,
        correctness,
        relevancy,
    ])
```

### 4.2 Custom Metric for Agent-Specific Criteria

```python
# metrics/hermes_metrics.py
from deepeval.metrics import GEval
from deepeval.test_case import SingleTurnParams

# Custom metric: Code Quality for coding agents
code_quality = GEval(
    name="Code Quality",
    criteria="""
    Evaluate the code quality based on:
    1. Correctness: Does the code solve the problem?
    2. Readability: Is the code clean and well-structured?
    3. Efficiency: Is the solution optimal?
    4. Security: Are there any security vulnerabilities?
    5. Best Practices: Does it follow language conventions?
    """,
    evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
    threshold=0.7,
    rubric=[
        Rubric(score_range=(0, 3), expected_outcome="Poor quality, major issues."),
        Rubric(score_range=(4, 6), expected_outcome="Acceptable but needs improvement."),
        Rubric(score_range=(7, 8), expected_outcome="Good quality, minor issues."),
        Rubric(score_range=(9, 10), expected_outcome="Excellent, production-ready."),
    ],
)

# Custom metric: Tool Selection Optimality
tool_optimality = GEval(
    name="Tool Optimality",
    criteria="""
    Evaluate whether the agent selected the most optimal tools for the task:
    1. Did it use the right tool for the job?
    2. Did it avoid unnecessary tool calls?
    3. Did it use tools in the correct order?
    4. Did it provide correct arguments to each tool?
    """,
    evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT],
    threshold=0.65,
)
```

### 4.3 Red Teaming Configuration

```python
# red_team_hermes.py
from deepteam import red_team
from deepteam.vulnerabilities import (
    BFLA, BOLA, RBAC, PIILeakage, PromptLeakage,
    Bias, Toxicity, ShellInjection, SQLInjection,
    AutonomousAgentDrift, ExploitToolAgent, ExcessiveAgency,
)
from deepteam.attacks.single_turn import (
    PromptInjection, Roleplay, Leetspeak, ROT13,
    Base64, AuthorityEscalation, GoalRedirection,
)
from deepteam.attacks.multi_turn import (
    LinearJailbreaking, CrescendoJailbreaking,
)

def hermes_model_callback(prompt: str, turns=None) -> str:
    """Wrapper around Hermes Agent for red teaming."""
    return hermes_agent(prompt)

# Run red team assessment
risk_assessment = red_team(
    model_callback=hermes_model_callback,
    target_purpose="A production AI agent that can execute commands, read files, and search the web",
    vulnerabilities=[
        BFLA(types=["privilege_escalation", "function_bypass"]),
        BOLA(types=["object_access_bypass", "cross_customer_access"]),
        RBAC(types=["role_bypass"]),
        PIILeakage(types=["direct_leakage", "session_leakage"]),
        PromptLeakage(types=["system_prompt", "credentials"]),
        Bias(types=["gender", "race"]),
        Toxicity(types=["insults", "threats"]),
        ShellInjection(),
        SQLInjection(),
        AutonomousAgentDrift(),
        ExploitToolAgent(),
        ExcessiveAgency(),
    ],
    attacks=[
        PromptInjection(),
        Roleplay(),
        Leetspeak(),
        ROT13(),
        Base64(),
        AuthorityEscalation(),
        GoalRedirection(),
        LinearJailbreaking(),
        CrescendoJailbreaking(),
    ],
    attacks_per_vulnerability_type=5,
)

# Save results
risk_assessment.save("red_team_results.json")
```

### 4.4 Multi-Turn Conversation Evaluation

```python
# tests/test_conversational_agent.py
from deepeval.test_case import ConversationalTestCase, Turn
from deepeval.metrics import MCPTaskCompletionMetric

convo_test_case = ConversationalTestCase(
    turns=[
        Turn(role="user", content="Book a flight to Paris"),
        Turn(role="assistant", content="I'll help you book a flight to Paris. What date?"),
        Turn(role="user", content="Next Friday, cheapest option"),
        Turn(role="assistant", content="Found 3 options. The cheapest is $450 on Air France."),
        Turn(role="user", content="Book that one"),
        Turn(role="assistant", content="Booked! Confirmation: AF-12345"),
    ],
    expected_output="Flight booked with confirmation number",
)

metric = MCPTaskCompletionMetric(threshold=0.7)
assert_test(convo_test_case, [metric])
```

---

## 5. CI/CD Integration

### 5.1 GitHub Actions

```yaml
# .github/workflows/llm-evals.yml
name: LLM Agent Evaluation

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  deepeval:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -U deepeval deepteam
          pip install -r requirements.txt

      - name: Configure DeepEval judge
        run: |
          echo "ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}" >> $GITHUB_ENV
          echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> $GITHUB_ENV
          deepeval set-anthropic --model claude-sonnet-4-6

      - name: Run agent evaluations
        run: |
          deepeval test run tests/test_hermes_agent.py \
            -n 4 \
            -r 2 \
            -i \
            --identifier "github-actions-${{ github.run_id }}"

      - name: Run red teaming
        run: |
          python red_team_hermes.py

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: eval-results-${{ matrix.python-version }}
          path: |
            deepeval_results.json
            red_team_results.json

      - name: Check quality gate
        run: |
          python -c "
          import json
          with open('deepeval_results.json') as f:
              results = json.load(f)
          pass_rate = sum(1 for r in results if r['success']) / len(results)
          if pass_rate < 0.8:
              print(f'Quality gate failed: {pass_rate:.1%} pass rate (threshold: 80%)')
              exit(1)
          print(f'Quality gate passed: {pass_rate:.1%} pass rate')
          "
```

### 5.2 GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - evaluate
  - red-team

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

deepeval:
  stage: evaluate
  image: python:3.11
  script:
    - pip install -U deepeval deepteam
    - deepeval set-anthropic --model claude-sonnet-4-6
    - deepeval test run tests/test_hermes_agent.py -n 4 -r 2 -i
  artifacts:
    paths:
      - deepeval_results.json
    expire_in: 30 days
  only:
    - merge_requests
    - main

red_team:
  stage: red-team
  image: python:3.11
  script:
    - pip install -U deepteam
    - python red_team_hermes.py
  artifacts:
    paths:
      - red_team_results.json
    expire_in: 30 days
  allow_failure: true  # Don't block pipeline, but report
```

### 5.3 Pre-Commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: deepeval-smoke-test
        name: DeepEval Smoke Test
        entry: deepeval test run tests/test_hermes_agent.py -m "smoke" -i
        language: system
        pass_filenames: false
        always_run: true
```

---

## 6. Pitfalls and Best Practices

### 6.1 Critical Pitfalls

| Pitfall | Impact | Mitigation |
|---|---|---|
| **Using plain `pytest` instead of `deepeval test run`** | Missing async handling, no LLM-specific flags, unexpected errors | Always use `deepeval test run` |
| **Default OpenAI judge without API key** | Silent 0-score metrics, cryptic errors | Always configure judge explicitly with `deepeval set-*` |
| **No tracing setup for trajectory metrics** | TaskCompletionMetric fails with missing trace | Must use `@observe(type="agent")` |
| **LLM judge costs spiral** | 100 cases × 5 metrics = 500 judge calls per run | Use `-c` cache flag, cheaper models for iteration |
| **Flaky tests from LLM non-determinism** | False failures in CI | Use `-r 3` repeats, set appropriate thresholds |
| **Rate limiting on judge API** | Throttled evaluations, timeouts | Use `--max-concurrent` to limit parallelism |
| **Mixing judge models across runs** | Incomparable scores between runs | Pin one judge model per benchmark |
| **Not setting `expected_tools` for ToolCorrectness** | Tool correctness always fails | Provide ground truth via `update_current_span(expected_tools=...)` |
| **Red teaming without scope definition** | Irrelevant attack simulations | Set `target_purpose` to match Hermes's actual use case |
| **Ignoring `include_reason`** | Can't debug why metrics fail | Always set `include_reason=True` during development |

### 6.2 Best Practices

1. **Start with tracing, then add metrics** — Instrument with `@observe` first, verify traces look correct, then attach metrics
2. **Use tiered evaluation** — Fast/cheap metrics (deterministic) in CI, expensive LLM-judge metrics in nightly builds
3. **Cache aggressively** — Use `-c` flag to avoid re-evaluating unchanged test cases
4. **Parallelize wisely** — `-n 4` for 330 slots; increase if judge API rate limits allow
5. **Set realistic thresholds** — Start with 0.5, tune based on baseline; don't set 0.95 on day one
6. **Version your goldens** — Track dataset changes alongside code changes
7. **Use `evals_iterator()` for large datasets** — More control than pytest for 330+ cases
8. **Separate red teaming from quality evals** — Run red teaming on a schedule, not every commit
9. **Monitor token costs** — Each metric runs ≥1 judge call per case; budget accordingly
10. **Use `AsyncConfig` for fine-grained control** — `max_concurrent`, `throttle_value` for rate limit management

### 6.3 Recommended Thresholds for Production Agents

| Metric | Threshold | Rationale |
|---|---|---|
| TaskCompletion | 0.70 | Primary gate — agent must accomplish task |
| ToolCorrectness | 0.80 | High bar for tool selection |
| ArgumentCorrectness | 0.75 | Tool arguments must be mostly correct |
| Correctness (G-Eval) | 0.70 | Factual accuracy baseline |
| AnswerRelevancy | 0.70 | Output must be relevant |
| Hallucination | 0.60 | Some tolerance for creative tasks |
| StepEfficiency | 0.60 | Don't over-optimize at cost of effectiveness |
| PlanAdherence | 0.65 | Agent should follow its plan |

### 6.4 Scaling to 330 Agent Slots

```python
# For 330 agent slots, use evals_iterator for better control
from deepeval.dataset import EvaluationDataset
from deepeval.metrics import TaskCompletionMetric, ToolCorrectnessMetric
from hermes_agent import hermes_agent

dataset = EvaluationDataset()
dataset.load_from_json("hermes_agent_goldens.json")

metrics = [
    TaskCompletionMetric(threshold=0.7),
    ToolCorrectnessMetric(threshold=0.8),
]

# evals_iterator gives you per-golden control
for golden in dataset.evals_iterator(metrics=metrics):
    result = hermes_agent(golden.input)
    # Metrics are automatically evaluated against the trace
    print(f"Input: {golden.input[:50]}...")
    for metric in metrics:
        print(f"  {metric.name}: {metric.score} {'✓' if metric.score >= metric.threshold else '✗'}")
```

---

## 7. Quick Reference

### Installation
```bash
pip install -U deepeval deepteam
```

### CLI Commands
```bash
deepeval login                          # Authenticate with Confident AI
deepeval set-anthropic --model claude-sonnet-4-6  # Set judge model
deepeval test run tests/ -n 4 -r 2 -i   # Run evals
deepeval generate --docs ./docs/        # Generate synthetic dataset
deepeval inspect                         # View traces in TUI
deepeval view                           # View results on Confident AI
```

### Key Imports
```python
from deepeval import assert_test, evaluate
from deepeval.tracing import observe, update_current_trace, update_current_span
from deepeval.metrics import (
    TaskCompletionMetric, ToolCorrectnessMetric, ArgumentCorrectnessMetric,
    StepEfficiencyMetric, PlanAdherenceMetric, PlanQualityMetric,
    GEval, AnswerRelevancyMetric, HallucinationMetric,
)
from deepeval.test_case import LLMTestCase, ConversationalTestCase, SingleTurnParams, ToolCall
from deepeval.dataset import EvaluationDataset, Golden
```

### DeepTeam Imports
```python
from deepteam import red_team
from deepteam.vulnerabilities import BFLA, BOLA, RBAC, PIILeakage, PromptLeakage, Bias, Toxicity
from deepteam.attacks.single_turn import PromptInjection, Roleplay, Leetspeak
from deepteam.attacks.multi_turn import LinearJailbreaking, CrescendoJailbreaking
```

---

## Summary

DeepEval provides a comprehensive, pytest-native framework for evaluating LLM agents at scale. For Ahmed's 330 agent slots:

1. **Instrument** Hermes Agent with `@observe` decorators (agent, llm, tool types)
2. **Create goldens** — at least one per agent slot (330+ test cases)
3. **Use agentic metrics** — TaskCompletion, ToolCorrectness, StepEfficiency as primary gates
4. **Add red teaming** — DeepTeam for 40+ vulnerability categories
5. **Integrate into CI/CD** — `deepeval test run` in GitHub Actions/GitLab CI
6. **Monitor costs** — Cache results, use appropriate judge models, parallelize wisely
