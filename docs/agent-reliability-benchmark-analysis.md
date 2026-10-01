# Agent Reliability Benchmark (ARB) — Deep-Dive Analysis & Hermes Integration Guide

**Source:** [uujjrmi/agent-reliability-benchmark](https://github.com/uujjrmi/agent-reliability-benchmark) (MIT License)
**Date:** 2026-10-01
**Audience:** Ahmed Hassan — production agent reliability benchmarking

---

## 1. Architecture Overview

### What ARB Is

ARB is a lightweight, open-source research-engineering framework for evaluating how LLM-style agents recover from infrastructure and tool failures during multi-step tasks. It models an agent as an **asynchronous policy** operating in a controlled environment with four tools, injecting deterministic failures and measuring recovery behavior.

### Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ARB Framework                             │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Task Suite   │  │ Failure      │  │ Agent        │      │
│  │ (50 tasks,   │  │ Injector     │  │ Policies     │      │
│  │  5 categories)│  │ (7 failure   │  │ (naive,      │      │
│  │              │  │  modes)      │  │  single,     │      │
│  │              │  │              │  │  resilient,  │      │
│  │              │  │              │  │  LLM-adapter)│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └────────────┬────┘                 │               │
│                      ▼                      │               │
│              ┌──────────────┐               │               │
│              │ Environment  │◄──────────────┘               │
│              │ (4 tools:    │                               │
│              │  Calculator, │                               │
│              │  Search,     │                               │
│              │  Database,   │                               │
│              │  File Rtrv)  │                               │
│              └──────┬───────┘                               │
│                     │                                        │
│                     ▼                                        │
│              ┌──────────────┐                               │
│              │ Results      │                               │
│              │ (CSV + JSON  │                               │
│              │  per trial)  │                               │
│              └──────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

### Four Tools

| Tool | Purpose | Failure Modes Injected |
|---|---|---|
| **Calculator** | Numerical computation | Incorrect results, timeouts, corrupted output |
| **Search** | Information retrieval | Stale cached responses, partial results, rate limiting |
| **Database** | Structured queries | Unavailable, incorrect responses, schema drift |
| **File Retrieval** | Document/file access | Missing files, corrupted content, partial responses |

### Seven Failure Modes

ARB supports configurable failure probabilities for:

1. **Timeout failures** — tool calls that never return
2. **Tool unavailability** — tool is down/unreachable
3. **Incorrect responses** — semantically wrong results
4. **Stale cached responses** — outdated but well-formed data
5. **Corrupted outputs** — malformed/garbled responses
6. **Rate limiting** — 429-style throttling
7. **Partial responses** — incomplete but valid-looking data

### Agent Policies (Baselines)

| Policy | Validation | Retries | Behavior |
|---|---|---|---|
| `arb-naive` | None | 0 | Proceeds regardless of tool output quality |
| `arb-single-retry` | Yes | 1 | Validates intermediate results, retries once on failure |
| `arb-resilient` | Yes | 3 | Validates and retries up to 3 times |
| `openai:<model>` | LLM judge | Configurable | Uses OpenAI Responses API to decide retry |
| `anthropic:<model>` | LLM judge | Configurable | Uses Anthropic Messages API to decide retry |

### Task Suite

50 synthetic tasks across 5 categories (10 each):

- **Multi-hop reasoning** — chained tool calls where output of one feeds the next
- **Information retrieval** — search + database lookups
- **Numerical reasoning** — calculator-dependent computations
- **Planning** — multi-step tool orchestration
- **Tool orchestration** — complex inter-tool dependencies

Each task defines: prompt → expected intermediate tool outputs → final answer.

### Empirical Results (from README, 2026-06-18)

**Success rate by failure probability:**

| Model | p=0.00 | p=0.02 | p=0.05 | p=0.10 | p=0.20 |
|---|---|---|---|---|---|
| arb-resilient | 1.000 | 1.000 | 1.000 | 0.940 | 0.560 |
| arb-single-retry | 1.000 | 1.000 | 0.900 | 0.760 | 0.400 |
| arb-naive | 1.000 | 0.940 | 0.840 | 0.460 | 0.260 |
| claude-haiku-4-5 | 1.000 | 1.000 | 0.940 | 0.820 | 0.300 |

**Key finding:** At low failure rates (≤5%), LLM-mediated recovery matches deterministic baselines. At higher rates (≥10%), fixed-retry policies outperform LLM judges, which are more conservative about issuing retries.

---

## 2. Key Features for Ahmed's Stack

### Direct Relevance to Hermes Agent Reliability

| ARB Feature | Hermes Relevance | How It Maps |
|---|---|---|
| **Failure injection** | Tests Hermes tool-call recovery under real-world conditions | Inject failures into Hermes tool calls (terminal, browser, file ops) |
| **Recovery rate measurement** | Quantifies how often Hermes recovers from tool failures | Track retry success after injected failures |
| **Retry count** | Measures retry budget consumption | Count tool re-execution attempts |
| **Failure detection rate** | Measures whether Hermes *detects* failures vs. proceeds blindly | Track whether Hermes validates tool output before proceeding |
| **Latency under failure** | Measures performance degradation during recovery | Compare latency with/without injected failures |
| **Cost estimates** | Tracks token/call overhead of recovery | Measure additional LLM calls from retry behavior |
| **LLM-as-judge adapter** | Uses a model to evaluate recovery quality | Use a second model to judge whether Hermes recovered correctly |

### Metrics ARB Reports

| Metric | Definition | Why It Matters for Production |
|---|---|---|
| **Task success rate** | % of tasks completed correctly | Primary reliability indicator |
| **Recovery rate** | % of failures that were recovered from | Measures resilience, not just success |
| **Retry count** | Average retries per task | Cost/efficiency signal |
| **Tool call count** | Total tool invocations | Overhead measurement |
| **Latency** | End-to-end task time | SLO impact of recovery |
| **Failure detection rate** | % of failures detected by agent | Distinguishes "detected and recovered" from "got lucky" |
| **Cost estimates** | Token/call volume | Budget impact |

### What ARB Does NOT Cover (Gaps for Production)

- **No real API integration** — uses in-memory tools, not production APIs
- **No multi-turn conversation** — single-shot tasks only
- **No streaming/partial execution** — no mid-task failure recovery
- **No concurrent task interference** — no resource contention testing
- **No security/permission failures** — no auth/authorization failure modes
- **No network partition simulation** — no distributed systems failures

---

## 3. Integration Guide: Benchmarking Hermes Agent Reliability

### Approach 1: Use ARB as External Benchmark (Recommended)

Run ARB alongside Hermes to establish baseline reliability metrics, then compare Hermes against ARB baselines.

```bash
# 1. Clone and setup ARB
git clone https://github.com/uujjrmi/agent-reliability-benchmark.git
cd agent-reliability-benchmark
make setup
source .venv/bin/activate

# 2. Run deterministic baselines
python -m arb.cli \
  --models arb-resilient arb-single-retry arb-naive \
  --trials 5 \
  --failure-probability 0.05

# 3. Run failure-probability sweep
python examples/run_failure_sweep.py \
  --trials 3 \
  --probabilities 0.0 0.02 0.05 0.1 0.2

# 4. Run with LLM judge (requires API keys)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
python examples/run_frontier_experiment.py \
  --llm-models openai:gpt-5.5 anthropic:claude-sonnet-4-6 \
  --trials 1 \
  --probabilities 0.0 0.02 0.05 0.1 0.2
```

### Approach 2: Integrate ARB Failure Injection into Hermes Tool Calls

Create a Hermes-compatible wrapper that injects ARB-style failures into Hermes tool calls:

```python
# hermes_arb_bridge.py
"""
Bridge ARB failure injection into Hermes Agent tool calls.
Use this to test Hermes recovery behavior under controlled failures.
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any, Callable

@dataclass
class HermesFailureConfig:
    """Failure injection config for Hermes tool calls."""
    timeout_probability: float = 0.0
    incorrect_response_probability: float = 0.0
    stale_response_probability: float = 0.0
    corrupted_output_probability: float = 0.0
    rate_limit_probability: float = 0.0
    partial_response_probability: float = 0.0
    tool_unavailable_probability: float = 0.0

@dataclass
class HermesToolCall:
    """Record of a Hermes tool call for reliability analysis."""
    tool_name: str
    arguments: dict
    result: Any = None
    success: bool = True
    retries: int = 0
    latency_ms: float = 0.0
    failure_type: str | None = None
    recovered: bool = False

class HermesARBBenchmark:
    """
    Benchmark harness that wraps Hermes tool calls with ARB-style
    failure injection and measures recovery behavior.
    """
    
    def __init__(self, failure_config: HermesFailureConfig):
        self.config = failure_config
        self.calls: list[HermesToolCall] = []
    
    async def execute_with_failure_injection(
        self,
        tool_name: str,
        tool_fn: Callable,
        *args,
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """
        Execute a Hermes tool call with ARB-style failure injection.
        
        Args:
            tool_name: Name of the Hermes tool (e.g., "terminal", "browser")
            tool_fn: The actual tool function to call
            max_retries: Maximum retry attempts (mirrors arb-resilient=3)
            
        Returns:
            Tool result (or raises if all retries exhausted)
        """
        call_record = HermesToolCall(
            tool_name=tool_name,
            arguments={"args": args, "kwargs": kwargs}
        )
        
        for attempt in range(max_retries + 1):
            try:
                # Inject failure based on configured probabilities
                failure = self._select_failure()
                
                if failure and attempt < max_retries:
                    call_record.failure_type = failure
                    call_record.retries += 1
                    
                    if failure == "timeout":
                        await asyncio.sleep(30)  # simulate timeout
                        continue
                    elif failure == "rate_limit":
                        await asyncio.sleep(5)  # simulate backoff
                        continue
                    elif failure == "tool_unavailable":
                        raise ConnectionError(f"Tool {tool_name} unavailable")
                    elif failure == "incorrect_response":
                        # Return wrong result — does Hermes detect it?
                        result = await tool_fn(*args, **kwargs)
                        call_record.result = self._corrupt_result(result)
                        call_record.recovered = False
                        self.calls.append(call_record)
                        return call_record.result
                    elif failure == "corrupted_output":
                        result = await tool_fn(*args, **kwargs)
                        call_record.result = self._corrupt_output(result)
                        self.calls.append(call_record)
                        return call_record.result
                
                # Normal execution
                result = await tool_fn(*args, **kwargs)
                call_record.result = result
                call_record.success = True
                self.calls.append(call_record)
                return result
                
            except Exception as e:
                call_record.retries += 1
                if attempt == max_retries:
                    call_record.success = False
                    self.calls.append(call_record)
                    raise
        
        self.calls.append(call_record)
        return call_record.result
    
    def _select_failure(self) -> str | None:
        """Select a failure mode based on configured probabilities."""
        failures = {
            "timeout": self.config.timeout_probability,
            "incorrect_response": self.config.incorrect_response_probability,
            "stale_response": self.config.stale_response_probability,
            "corrupted_output": self.config.corrupted_output_probability,
            "rate_limit": self.config.rate_limit_probability,
            "partial_response": self.config.partial_response_probability,
            "tool_unavailable": self.config.tool_unavailable_probability,
        }
        
        # Normalize and select
        total = sum(failures.values())
        if total == 0:
            return None
        
        r = random.uniform(0, total)
        cumulative = 0
        for failure_type, prob in failures.items():
            cumulative += prob
            if r <= cumulative:
                return failure_type
        return None
    
    def _corrupt_result(self, result: Any) -> Any:
        """Return an incorrect but plausible result."""
        if isinstance(result, str):
            return result + " [CORRUPTED]"
        return result
    
    def _corrupt_output(self, result: Any) -> Any:
        """Return a malformed output."""
        if isinstance(result, dict):
            return {"error": "corrupted", "partial": True}
        return None
    
    def get_reliability_metrics(self) -> dict:
        """Compute ARB-style reliability metrics."""
        if not self.calls:
            return {}
        
        total = len(self.calls)
        successful = sum(1 for c in self.calls if c.success)
        recovered = sum(1 for c in self.calls if c.recovered)
        with_retries = sum(1 for c in self.calls if c.retries > 0)
        total_retries = sum(c.retries for c in self.calls)
        
        return {
            "total_calls": total,
            "success_rate": successful / total,
            "recovery_rate": recovered / total if total > 0 else 0,
            "calls_with_retries": with_retries,
            "average_retries": total_retries / total,
            "failure_detection_rate": with_retries / total if total > 0 else 0,
        }
```

### Approach 3: Custom ARB Task Suite for Hermes

Create Hermes-specific benchmark tasks that mirror real Hermes usage patterns:

```python
# hermes_arb_tasks.py
"""
Custom ARB-style task suite for Hermes Agent reliability testing.
Each task defines a prompt, expected tool sequence, and final answer.
"""

HERMES_TASK_SUITE = [
    {
        "id": "hermes-001",
        "category": "file_operations",
        "prompt": "Read the file /tmp/test.txt and count the lines",
        "expected_tools": ["read_file"],
        "expected_output_contains": ["line", "count"],
        "failure_modes": ["corrupted_output", "partial_response"],
    },
    {
        "id": "hermes-002",
        "category": "terminal_execution",
        "prompt": "Run 'ls -la /tmp' and list all files",
        "expected_tools": ["terminal"],
        "expected_output_contains": ["total", "drwx"],
        "failure_modes": ["timeout", "tool_unavailable"],
    },
    {
        "id": "hermes-003",
        "category": "web_browsing",
        "prompt": "Navigate to example.com and extract the page title",
        "expected_tools": ["browser"],
        "expected_output_contains": ["Example"],
        "failure_modes": ["timeout", "rate_limit"],
    },
    {
        "id": "hermes-004",
        "category": "multi_step",
        "prompt": "Search for 'python asyncio tutorial', extract 3 key points, and write them to /tmp/notes.txt",
        "expected_tools": ["web_search", "write_file"],
        "expected_output_contains": ["asyncio", "tutorial"],
        "failure_modes": ["stale_response", "incorrect_response"],
    },
    {
        "id": "hermes-005",
        "category": "error_recovery",
        "prompt": "Try to read /nonexistent/file.txt, then create it with content 'hello' and read it back",
        "expected_tools": ["read_file", "write_file", "read_file"],
        "expected_output_contains": ["hello"],
        "failure_modes": ["tool_unavailable"],
    },
]
```

### Running the Hermes-ARB Integration

```python
# run_hermes_arb.py
"""
Run ARB-style reliability benchmark against Hermes Agent.
"""

import asyncio
import json
from hermes_arb_bridge import HermesARBBenchmark, HermesFailureConfig
from hermes_arb_tasks import HERMES_TASK_SUITE

async def benchmark_hermes():
    # Configure failure injection
    config = HermesFailureConfig(
        timeout_probability=0.05,
        incorrect_response_probability=0.05,
        stale_response_probability=0.03,
        corrupted_output_probability=0.03,
        rate_limit_probability=0.02,
        partial_response_probability=0.02,
        tool_unavailable_probability=0.02,
    )
    
    benchmark = HermesARBBenchmark(config)
    
    # Run each task with failure injection
    for task in HERMES_TASK_SUITE:
        print(f"Running task {task['id']}: {task['prompt'][:50]}...")
        
        try:
            # Simulate Hermes tool calls with failure injection
            # In production, replace with actual Hermes tool invocations
            result = await benchmark.execute_with_failure_injection(
                tool_name=task["expected_tools"][0],
                tool_fn=lambda: asyncio.sleep(0.1),  # Replace with real tool
                max_retries=3,
            )
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Failed: {e}")
    
    # Report metrics
    metrics = benchmark.get_reliability_metrics()
    print("\n=== Hermes Reliability Metrics ===")
    print(json.dumps(metrics, indent=2))
    
    # Save results
    with open("results/hermes_arb_results.json", "w") as f:
        json.dump({
            "metrics": metrics,
            "calls": [
                {
                    "tool": c.tool_name,
                    "success": c.success,
                    "retries": c.retries,
                    "failure_type": c.failure_type,
                    "recovered": c.recovered,
                }
                for c in benchmark.calls
            ],
        }, f, indent=2)

if __name__ == "__main__":
    asyncio.run(benchmark_hermes())
```

---

## 4. Configuration Examples

### Scenario 1: Low-Failure Baseline (p=0.02)

```bash
# Simulate a well-behaved production environment
python -m arb.cli \
  --models arb-resilient arb-single-retry arb-naive \
  --trials 10 \
  --failure-probability 0.02
```

### Scenario 2: Moderate-Failure Production (p=0.05)

```bash
# Simulate typical production with occasional tool failures
python -m arb.cli \
  --models arb-resilient arb-single-retry arb-naive \
  --trials 5 \
  --failure-probability 0.05
```

### Scenario 3: High-Failure Stress Test (p=0.20)

```bash
# Simulate degraded infrastructure / peak load
python -m arb.cli \
  --models arb-resilient arb-single-retry arb-naive \
  --trials 3 \
  --failure-probability 0.20
```

### Scenario 4: Full Failure-Probability Sweep

```bash
# Run all failure levels for reliability curve
python examples/run_failure_sweep.py \
  --trials 5 \
  --probabilities 0.0 0.02 0.05 0.1 0.2 0.3 0.5
```

### Scenario 5: LLM-as-Judge with OpenAI

```bash
export OPENAI_API_KEY=sk-...
python examples/run_frontier_experiment.py \
  --llm-models openai:gpt-5.5 \
  --trials 3 \
  --probabilities 0.0 0.05 0.1 0.2 \
  --max-retries 2
```

### Scenario 6: LLM-as-Judge with Anthropic

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python examples/run_frontier_experiment.py \
  --llm-models anthropic:claude-sonnet-4-6 \
  --trials 3 \
  --probabilities 0.0 0.05 0.1 0.2 \
  --max-retries 2
```

### Scenario 7: Custom Failure Configuration (Python API)

```python
from arb.failure import FailureConfig

# Configure each failure mode independently
config = FailureConfig(
    timeout_probability=0.05,
    tool_unavailable_probability=0.03,
    incorrect_response_probability=0.05,
    stale_response_probability=0.02,
    corrupted_output_probability=0.02,
    rate_limit_probability=0.03,
    partial_response_probability=0.02,
)

# Run with custom config
# (Use programmatic API — see ARB source for exact interface)
```

### Scenario 8: Hermes-Specific Failure Profile

```python
# hermes_failure_profile.py
"""
Failure profile tailored to Hermes Agent's actual tool stack.
Based on observed failure patterns in production agent systems.
"""

HERMES_FAILURE_PROFILE = {
    # Terminal tool: occasional timeouts on long-running commands
    "timeout_probability": 0.03,
    
    # Browser tool: rate limiting on heavy pages
    "rate_limit_probability": 0.02,
    
    # File operations: corrupted output on large files
    "corrupted_output_probability": 0.01,
    
    # Web search: stale results from cached responses
    "stale_response_probability": 0.04,
    
    # API tools: occasional unavailability
    "tool_unavailable_probability": 0.02,
    
    # Database: incorrect results on complex queries
    "incorrect_response_probability": 0.03,
    
    # Partial responses on large data
    "partial_response_probability": 0.02,
}
```

---

## 5. CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/agent-reliability.yml
name: Agent Reliability Benchmark

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:
    inputs:
      failure_probability:
        description: 'Failure probability for stress test'
        required: false
        default: '0.05'
        type: choice
        options:
          - '0.0'
          - '0.02'
          - '0.05'
          - '0.1'
          - '0.2'

jobs:
  reliability-benchmark:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install ARB
        run: |
          git clone https://github.com/uujjrmi/agent-reliability-benchmark.git
          cd agent-reliability-benchmark
          make setup
      
      - name: Run deterministic baselines
        run: |
          cd agent-reliability-benchmark
          source .venv/bin/activate
          python -m arb.cli \
            --models arb-resilient arb-single-retry arb-naive \
            --trials 5 \
            --failure-probability ${{ github.event.inputs.failure_probability || '0.05' }}
      
      - name: Run failure sweep
        run: |
          cd agent-reliability-benchmark
          source .venv/bin/activate
          python examples/run_failure_sweep.py \
            --trials 3 \
            --probabilities 0.0 0.02 0.05 0.1 0.2
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: arb-results
          path: agent-reliability-benchmark/results/
      
      - name: Check reliability threshold
        run: |
          cd agent-reliability-benchmark
          source .venv/bin/activate
          python -c "
          import json
          with open('results/arb_results.json') as f:
              results = json.load(f)
          
          # Fail if success rate drops below 80% at p=0.05
          for model, data in results.items():
              if model == 'arb-resilient':
                  success_rate = data.get('success_rate', 1.0)
                  if success_rate < 0.80:
                      print(f'::error::Reliability regression: {model} success rate {success_rate:.3f} < 0.80')
                      exit(1)
                  print(f'::notice::{model} success rate: {success_rate:.3f}')
          "
      
      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('agent-reliability-benchmark/results/arb_results.json'));
            
            let body = '## Agent Reliability Benchmark Results\n\n';
            body += '| Model | Success Rate | Recovery Rate | Avg Retries |\n';
            body += '|-------|-------------|---------------|-------------|\n';
            
            for (const [model, data] of Object.entries(results)) {
              body += `| ${model} | ${(data.success_rate * 100).toFixed(1)}% | ${(data.recovery_rate * 100).toFixed(1)}% | ${data.average_retries.toFixed(2)} |\n`;
            }
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });

  llm-judge-benchmark:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    needs: reliability-benchmark
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install ARB with LLM extras
        run: |
          git clone https://github.com/uujjrmi/agent-reliability-benchmark.git
          cd agent-reliability-benchmark
          pip install -e ".[dev,llm]"
      
      - name: Run LLM-as-judge benchmark
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd agent-reliability-benchmark
          python examples/run_frontier_experiment.py \
            --llm-models openai:gpt-5.5 anthropic:claude-sonnet-4-6 \
            --trials 1 \
            --probabilities 0.0 0.05 0.1 0.2 \
            --task-limit 10
      
      - name: Upload LLM results
        uses: actions/upload-artifact@v4
        with:
          name: arb-llm-results
          path: agent-reliability-benchmark/results/
```

### Pre-Deployment Gate

```bash
#!/bin/bash
# scripts/reliability_gate.sh
# Block deployment if reliability regresses

set -euo pipefail

THRESHOLD=0.85
FAILURE_PROBABILITY=0.05

echo "Running reliability gate (threshold=$THRESHOLD, p=$FAILURE_PROBABILITY)..."

cd agent-reliability-benchmark
source .venv/bin/activate

python -m arb.cli \
  --models arb-resilient \
  --trials 5 \
  --failure-probability $FAILURE_PROBABILITY

# Check result
SUCCESS_RATE=$(python -c "
import json
with open('results/arb_results.json') as f:
    data = json.load(f)
print(data.get('arb-resilient', {}).get('success_rate', 0))
")

if (( $(echo "$SUCCESS_RATE < $THRESHOLD" | bc -l) )); then
  echo "❌ RELIABILITY GATE FAILED: success rate $SUCCESS_RATE < $THRESHOLD"
  exit 1
fi

echo "✅ Reliability gate passed: success rate $SUCCESS_RATE >= $THRESHOLD"
```

### Makefile Integration

```makefile
# Add to your Makefile

.PHONY: reliability-benchmark reliability-sweep reliability-gate

reliability-benchmark:
	@echo "Running ARB reliability benchmark..."
	cd agent-reliability-benchmark && \
		source .venv/bin/activate && \
		python -m arb.cli --models arb-resilient arb-single-retry arb-naive \
			--trials 5 --failure-probability 0.05

reliability-sweep:
	@echo "Running failure-probability sweep..."
	cd agent-reliability-benchmark && \
		source .venv/bin/activate && \
		python examples/run_failure_sweep.py \
			--trials 3 --probabilities 0.0 0.02 0.05 0.1 0.2

reliability-gate:
	@echo "Running reliability gate..."
	./scripts/reliability_gate.sh
```

---

## 6. Pitfalls and Best Practices

### Pitfalls

| Pitfall | Description | Mitigation |
|---|---|---|
| **Overfitting to synthetic tasks** | ARB's 50 synthetic tasks may not represent real Hermes usage | Supplement with Hermes-specific tasks (see Approach 3) |
| **Uniform failure assumption** | ARB's `--failure-probability` applies uniform injection; real failures are correlated | Use `FailureConfig` for per-mode probabilities; model correlated failures |
| **No statistical significance** | Small trial counts produce noisy results | Run ≥5 trials; use confidence intervals; report pass^k metrics |
| **LLM judge bias** | LLM-as-judge may share biases with the agent being tested | Use a different model family for judging; report inter-rater agreement |
| **Ignoring latency** | Recovery adds latency; a "successful" recovery that takes 10x longer may not be acceptable | Set latency SLOs; measure p50/p95/p99 latency under failure |
| **Cost blindness** | Retries cost tokens; a resilient policy may be economically unviable | Track cost per task; set cost budgets alongside reliability targets |
| **Single-failure assumption** | ARB injects one failure at a time; production has cascading failures | Run multi-failure scenarios; test correlated failure modes |
| **No partial success** | ARB is binary (success/fail); real tasks have partial completion | Define partial success criteria; measure completion percentage |
| **Context contamination** | Failed attempts remain in context, degrading subsequent retries (per arXiv:2605.08563) | Test clean-restart vs. in-context retry; measure contamination effect |
| **Tool-agnostic design** | ARB's 4 tools don't map 1:1 to Hermes's tool set | Build Hermes-specific tool adapters (see Approach 2) |

### Best Practices

1. **Start with deterministic baselines** — Run `arb-naive`, `arb-single-retry`, and `arb-resilient` first to establish the recovery policy spectrum before adding LLM judges.

2. **Use failure-probability sweeps** — Don't test at a single p-value. Run the full sweep (0.0 → 0.2) to understand the reliability curve and identify the "knee" where recovery breaks down.

3. **Measure recovery rate separately from success rate** — A 90% success rate with 0% recovery means the agent got lucky; 90% success with 60% recovery means genuine resilience.

4. **Track retry count distribution** — Average retries hide variance. Report p50/p95/p99 retry counts to catch tail behavior.

5. **Test with LLM judge from a different provider** — If Hermes uses OpenAI, judge with Anthropic (or vice versa) to avoid shared blind spots.

6. **Run repeated trials** — LLM agents are stochastic. Use `--trials 5` minimum; report pass@k and pass^k metrics.

7. **Version-pin your benchmark** — Pin ARB commit hash and model versions to ensure reproducibility. Model drift will change results.

8. **Integrate into CI early** — Add reliability gates to CI before production deployment, not after incidents.

9. **Correlate with production incidents** — Map ARB failure modes to real production failures. Weight failure probabilities by observed production frequency.

10. **Report cost alongside reliability** — A recovery policy that doubles token cost may not be viable. Always report cost-per-task and cost-per-recovery.

11. **Test context contamination** — Per the "Why Retrying Fails" paper (arXiv:2605.08563), failed attempts contaminate context. Test both in-context retry and clean-restart strategies.

12. **Use ARB as a comparative tool, not an absolute measure** — ARB's value is comparing policies/models against each other under identical conditions, not predicting absolute production reliability.

### Recommended Benchmarking Cadence

| Frequency | Scope | Purpose |
|---|---|---|
| **Every PR** | Deterministic baselines, p=0.05, 3 trials | Catch regressions early |
| **Weekly** | Full sweep (0.0–0.2), 5 trials | Track reliability trend |
| **Monthly** | LLM-as-judge + deterministic, full sweep | Model quality assessment |
| **Pre-release** | Full suite + Hermes-specific tasks, 10 trials | Release gate |
| **Post-incident** | Targeted failure mode reproduction | Validate fix effectiveness |

---

## Summary

ARB provides a solid foundation for measuring agent recovery under tool failures. For Ahmed's Hermes Agent benchmarking:

1. **Use ARB directly** for baseline reliability metrics and failure-probability sweeps
2. **Build a Hermes-ARB bridge** to inject ARB-style failures into Hermes tool calls
3. **Create Hermes-specific tasks** that mirror real usage patterns
4. **Integrate into CI/CD** with reliability gates that block deployment on regression
5. **Report recovery rate, retry count, and cost** alongside success rate
6. **Run repeated trials** and use statistical measures (pass@k, pass^k) for production decisions

The key insight from ARB's empirical results: **fixed-retry policies outperform LLM judges at high failure rates** (≥10%), suggesting that for production reliability, a well-tuned deterministic retry policy may be more robust than LLM-mediated recovery decisions.
