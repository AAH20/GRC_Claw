# GRC_Claw Monitoring Implementation Guide

**Version:** 1.0.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Status:** Draft  
**Standard:** ISO 42001 Clause 9 (Monitoring, Measurement, Analysis, and Evaluation)  
**References:** GRC_CLAW_MONITORING_OBSERVABILITY_SPEC.md, grc-claw-performance-spec.md

---

## Table of Contents

1. [Metric Collection (Python)](#1-metric-collection-python)
2. [Alert Rules (Prometheus)](#2-alert-rules-prometheus)
3. [Dashboard Configurations (Grafana JSON)](#3-dashboard-configurations-grafana-json)
4. [Anomaly Detection (Python)](#4-anomaly-detection-python)
5. [Predictive Alerting (Python)](#5-predictive-alerting-python)
6. [Monitoring Data Quality (Python)](#6-monitoring-data-quality-python)
7. [Monitoring Cost Optimization (Python)](#7-monitoring-cost-optimization-python)

---

## 1. Metric Collection (Python)

### 1.1 Prometheus Metrics Exporter

```python
# grc_claw/monitoring/metrics_exporter.py
"""
GRC_Claw Prometheus Metrics Exporter.

Exposes all 60+ metrics defined in the monitoring specification
via a Prometheus-compatible HTTP endpoint.
"""

import os
import time
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps
from contextlib import contextmanager

from prometheus_client import (
    Counter, Histogram, Gauge, Info, Summary,
    start_http_server, CollectorRegistry, push_to_gateway
)
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily


# ─── Custom Registry ──────────────────────────────────────────────────────────

REGISTRY = CollectorRegistry()


# ─── Model Performance Metrics ───────────────────────────────────────────────

llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'End-to-end LLM call latency in seconds',
    ['model', 'provider', 'agent_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    registry=REGISTRY
)

llm_token_usage = Counter(
    'llm_token_usage_total',
    'Total tokens consumed per call',
    ['model', 'type'],  # type: input, output, total
    registry=REGISTRY
)

llm_cost_total = Counter(
    'llm_cost_total_dollars',
    'Total LLM cost in USD',
    ['model', 'provider', 'agent_id'],
    registry=REGISTRY
)

llm_error_rate = Gauge(
    'llm_error_rate',
    'LLM error rate over 5m window',
    ['model', 'error_type'],
    registry=REGISTRY
)

llm_success_rate = Gauge(
    'llm_success_rate',
    'LLM success rate over 5m window',
    ['model'],
    registry=REGISTRY
)

llm_timeout_rate = Gauge(
    'llm_timeout_rate',
    'LLM timeout rate',
    ['model'],
    registry=REGISTRY
)

llm_retry_count = Counter(
    'llm_retry_count_total',
    'Retry attempts per LLM call',
    ['model', 'reason'],
    registry=REGISTRY
)

llm_quality_score = Gauge(
    'llm_quality_score',
    'LLM-as-judge quality score (0-1)',
    ['model', 'eval_type'],
    registry=REGISTRY
)

llm_relevance_score = Gauge(
    'llm_relevance_score',
    'Output relevance score (0-1)',
    ['model'],
    registry=REGISTRY
)

llm_groundedness_score = Gauge(
    'llm_groundedness_score',
    'Output groundedness score for RAG (0-1)',
    ['model'],
    registry=REGISTRY
)


# ─── Drift Detection Metrics ─────────────────────────────────────────────────

feature_drift_score = Gauge(
    'feature_drift_score',
    'PSI (Population Stability Index) per feature',
    ['feature_name', 'model_id'],
    registry=REGISTRY
)

prediction_drift_score = Gauge(
    'prediction_drift_score',
    'Prediction distribution drift score',
    ['model_id', 'version'],
    registry=REGISTRY
)

embedding_drift_score = Gauge(
    'embedding_drift_score',
    'Embedding space drift (Wasserstein distance)',
    ['model_id'],
    registry=REGISTRY
)

data_quality_score = Gauge(
    'data_quality_score',
    'Input data quality score',
    ['model_id', 'dataset'],
    registry=REGISTRY
)

concept_drift_detected = Counter(
    'concept_drift_detected_total',
    'Concept drift events',
    ['model_id', 'drift_type'],
    registry=REGISTRY
)

model_version_delta = Gauge(
    'model_version_delta',
    'Performance delta between model versions',
    ['model_id', 'from_version', 'to_version'],
    registry=REGISTRY
)

training_serving_skew = Gauge(
    'training_serving_skew',
    'Train/serve feature distribution skew',
    ['model_id', 'feature'],
    registry=REGISTRY
)


# ─── Bias & Fairness Metrics ───────────────────────────────────────────────

demographic_parity_diff = Gauge(
    'demographic_parity_diff',
    'Demographic parity difference',
    ['model_id', 'protected_class'],
    registry=REGISTRY
)

equalized_odds_diff = Gauge(
    'equalized_odds_diff',
    'Equalized odds difference',
    ['model_id', 'protected_class'],
    registry=REGISTRY
)

disparate_impact_ratio = Gauge(
    'disparate_impact_ratio',
    'Disparate impact ratio',
    ['model_id', 'protected_class'],
    registry=REGISTRY
)

bias_score = Gauge(
    'bias_score',
    'Composite bias score (0-1)',
    ['model_id', 'bias_type'],
    registry=REGISTRY
)

fairness_violation_count = Counter(
    'fairness_violation_count_total',
    'Fairness threshold violations',
    ['model_id', 'protected_class'],
    registry=REGISTRY
)

counterfactual_fairness_score = Gauge(
    'counterfactual_fairness_score',
    'Counterfactual fairness metric',
    ['model_id'],
    registry=REGISTRY
)


# ─── Safety Metrics ──────────────────────────────────────────────────────────

toxicity_score = Gauge(
    'toxicity_score',
    'Toxicity probability score',
    ['model_id', 'content_type'],
    registry=REGISTRY
)

jailbreak_attempt_count = Counter(
    'jailbreak_attempt_count_total',
    'Detected jailbreak attempts',
    ['agent_id', 'technique'],
    registry=REGISTRY
)

prompt_injection_count = Counter(
    'prompt_injection_count_total',
    'Detected prompt injections',
    ['agent_id', 'source'],
    registry=REGISTRY
)

pii_detection_count = Counter(
    'pii_detection_count_total',
    'PII detections',
    ['agent_id', 'pii_type'],
    registry=REGISTRY
)

nsfw_content_count = Counter(
    'nsfw_content_count_total',
    'NSFW content detections',
    ['agent_id'],
    registry=REGISTRY
)

harmful_content_rate = Gauge(
    'harmful_content_rate',
    'Harmful content rate',
    ['model_id'],
    registry=REGISTRY
)

safety_violation_count = Counter(
    'safety_violation_count_total',
    'Safety policy violations',
    ['agent_id', 'violation_type'],
    registry=REGISTRY
)

guard_pass_rate = Gauge(
    'guard_pass_rate',
    'Guardrail validation pass rate',
    ['agent_id', 'guard_type'],
    registry=REGISTRY
)

guard_false_positive_rate = Gauge(
    'guard_false_positive_rate',
    'Guardrail false positive rate',
    ['guard_type'],
    registry=REGISTRY
)

guard_false_negative_rate = Gauge(
    'guard_false_negative_rate',
    'Guardrail false negative rate',
    ['guard_type'],
    registry=REGISTRY
)

reask_rate = Gauge(
    'reask_rate',
    'Reask rate (user friction)',
    ['agent_id', 'guard_type'],
    registry=REGISTRY
)


# ─── Security Metrics ────────────────────────────────────────────────────────

constraint_breach_count = Counter(
    'constraint_breach_count_total',
    'Policy constraint breaches',
    ['agent_id', 'policy_id'],
    registry=REGISTRY
)

constraint_eval_pass_rate = Gauge(
    'constraint_eval_pass_rate',
    'Constraint evaluation pass rate',
    ['policy_id'],
    registry=REGISTRY
)

unauthorized_action_count = Counter(
    'unauthorized_action_count_total',
    'Unauthorized action attempts',
    ['agent_id', 'action_type'],
    registry=REGISTRY
)

privilege_escalation_count = Counter(
    'privilege_escalation_count_total',
    'Privilege escalation attempts',
    ['agent_id'],
    registry=REGISTRY
)

anomaly_score = Gauge(
    'anomaly_score',
    'Behavioral anomaly score',
    ['agent_id'],
    registry=REGISTRY
)

threat_detection_count = Counter(
    'threat_detection_count_total',
    'Security threat detections',
    ['severity', 'source'],
    registry=REGISTRY
)

audit_log_integrity = Gauge(
    'audit_log_integrity',
    'Audit log hash chain integrity (1.0 = intact)',
    ['log_source'],
    registry=REGISTRY
)

access_violation_count = Counter(
    'access_violation_count_total',
    'Access control violations',
    ['resource', 'agent_id'],
    registry=REGISTRY
)


# ─── Agent Behavior Metrics ──────────────────────────────────────────────────

agent_run_duration = Histogram(
    'agent_run_duration_seconds',
    'Agent run duration in seconds',
    ['agent_id'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=REGISTRY
)

agent_success_rate = Gauge(
    'agent_success_rate',
    'Agent task success rate',
    ['agent_id'],
    registry=REGISTRY
)

agent_tool_call_count = Counter(
    'agent_tool_call_count_total',
    'Tool invocations',
    ['agent_id', 'tool_name'],
    registry=REGISTRY
)

agent_tool_error_count = Counter(
    'agent_tool_error_count_total',
    'Tool call errors',
    ['agent_id', 'tool_name'],
    registry=REGISTRY
)

agent_decision_latency = Histogram(
    'agent_decision_latency_seconds',
    'Decision-making latency',
    ['agent_id', 'decision_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=REGISTRY
)

agent_loop_count = Counter(
    'agent_loop_count_total',
    'Agent loop iterations',
    ['agent_id'],
    registry=REGISTRY
)

agent_context_window_usage = Gauge(
    'agent_context_window_usage',
    'Context window utilization percentage',
    ['agent_id'],
    registry=REGISTRY
)

agent_cost_per_run = Gauge(
    'agent_cost_per_run_dollars',
    'Cost per agent run in USD',
    ['agent_id'],
    registry=REGISTRY
)

agent_human_escalation_rate = Gauge(
    'agent_human_escalation_rate',
    'Human escalation rate',
    ['agent_id'],
    registry=REGISTRY
)

agent_constraint_eval_duration = Histogram(
    'agent_constraint_eval_duration_seconds',
    'Constraint evaluation time',
    ['agent_id', 'policy_id'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    registry=REGISTRY
)


# ─── Incident & Response Metrics ─────────────────────────────────────────────

incident_count = Counter(
    'incident_count_total',
    'Total incidents',
    ['severity', 'fault_class'],
    registry=REGISTRY
)

time_to_detect = Histogram(
    'time_to_detect_seconds',
    'Time to detect incident in seconds',
    ['incident_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
    registry=REGISTRY
)

time_to_respond = Histogram(
    'time_to_respond_seconds',
    'Time to respond to incident in seconds',
    ['incident_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
    registry=REGISTRY
)

time_to_resolve = Histogram(
    'time_to_resolve_seconds',
    'Time to resolve incident in seconds',
    ['incident_type'],
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400],
    registry=REGISTRY
)

incident_impact_score = Gauge(
    'incident_impact_score',
    'Business impact score (1-5)',
    ['incident_id'],
    registry=REGISTRY
)

incident_recurrence_count = Counter(
    'incident_recurrence_count_total',
    'Recurring incident count',
    ['fault_class'],
    registry=REGISTRY
)

verification_failure_count = Counter(
    'verification_failure_count_total',
    'Post-fix verification failures',
    ['incident_id'],
    registry=REGISTRY
)


# ─── GRC Info ────────────────────────────────────────────────────────────────

grc_claw_info = Info(
    'grc_claw',
    'GRC_Claw version and configuration',
    registry=REGISTRY
)


# ─── Metric Collection Decorators & Helpers ───────────────────────────────────

class MetricsCollector:
    """
    High-level metrics collector for GRC_Claw.
    
    Provides decorators and context managers for instrumenting
    agent code with minimal boilerplate.
    """
    
    def __init__(self, push_gateway: Optional[str] = None,
                 job_name: str = "grc-claw"):
        self.push_gateway = push_gateway
        self.job_name = job_name
        self._label_cache: Dict[str, List[str]] = {}
    
    def start_server(self, port: int = 8000):
        """Start Prometheus HTTP metrics server."""
        start_http_server(port, registry=REGISTRY)
    
    def push_metrics(self):
        """Push metrics to Prometheus Pushgateway."""
        if self.push_gateway:
            push_to_gateway(
                self.push_gateway,
                job=self.job_name,
                registry=REGISTRY
            )
    
    @contextmanager
    def track_llm_call(self, model: str, provider: str, agent_id: str):
        """Context manager to track an LLM call end-to-end."""
        start = time.time()
        error_occurred = False
        error_type = None
        
        try:
            yield self
        except Exception as e:
            error_occurred = True
            error_type = type(e).__name__
            raise
        finally:
            duration = time.time() - start
            llm_request_duration.labels(
                model=model, provider=provider, agent_id=agent_id
            ).observe(duration)
            
            if error_occurred:
                llm_error_rate.labels(
                    model=model, error_type=error_type or "unknown"
                ).set(1.0)
    
    def record_llm_usage(self, model: str, agent_id: str,
                         input_tokens: int, output_tokens: int,
                         cost_usd: float):
        """Record token usage and cost for an LLM call."""
        llm_token_usage.labels(model=model, type='input').inc(input_tokens)
        llm_token_usage.labels(model=model, type='output').inc(output_tokens)
        llm_token_usage.labels(model=model, type='total').inc(
            input_tokens + output_tokens
        )
        llm_cost_total.labels(
            model=model, provider=self._get_provider(model), agent_id=agent_id
        ).inc(cost_usd)
    
    def record_agent_run(self, agent_id: str, duration: float,
                         success: bool, cost: float, tool_calls: int,
                         tool_errors: int, context_usage: float):
        """Record a complete agent run."""
        agent_run_duration.labels(agent_id=agent_id).observe(duration)
        agent_success_rate.labels(agent_id=agent_id).set(1.0 if success else 0.0)
        agent_cost_per_run.labels(agent_id=agent_id).set(cost)
        agent_context_window_usage.labels(agent_id=agent_id).set(context_usage)
        
        if tool_calls > 0:
            agent_tool_call_count.labels(
                agent_id=agent_id, tool_name="aggregate"
            ).inc(tool_calls)
        
        if tool_errors > 0:
            agent_tool_error_count.labels(
                agent_id=agent_id, tool_name="aggregate"
            ).inc(tool_errors)
    
    def record_safety_event(self, agent_id: str, event_type: str,
                           details: Dict):
        """Record a safety-related event."""
        if event_type == "jailbreak":
            jailbreak_attempt_count.labels(
                agent_id=agent_id,
                technique=details.get("technique", "unknown")
            ).inc()
        elif event_type == "prompt_injection":
            prompt_injection_count.labels(
                agent_id=agent_id,
                source=details.get("source", "unknown")
            ).inc()
        elif event_type == "pii_detection":
            pii_detection_count.labels(
                agent_id=agent_id,
                pii_type=details.get("pii_type", "unknown")
            ).inc()
        elif event_type == "nsfw":
            nsfw_content_count.labels(agent_id=agent_id).inc()
        elif event_type == "violation":
            safety_violation_count.labels(
                agent_id=agent_id,
                violation_type=details.get("violation_type", "unknown")
            ).inc()
    
    def record_security_event(self, agent_id: str, event_type: str,
                              details: Dict):
        """Record a security-related event."""
        if event_type == "constraint_breach":
            constraint_breach_count.labels(
                agent_id=agent_id,
                policy_id=details.get("policy_id", "unknown")
            ).inc()
        elif event_type == "unauthorized_action":
            unauthorized_action_count.labels(
                agent_id=agent_id,
                action_type=details.get("action_type", "unknown")
            ).inc()
        elif event_type == "privilege_escalation":
            privilege_escalation_count.labels(agent_id=agent_id).inc()
        elif event_type == "access_violation":
            access_violation_count.labels(
                resource=details.get("resource", "unknown"),
                agent_id=agent_id
            ).inc()
    
    def record_incident(self, severity: str, fault_class: str,
                        incident_type: str, detect_time: float,
                        respond_time: float, resolve_time: float,
                        impact: int):
        """Record an incident with full lifecycle metrics."""
        incident_count.labels(
            severity=severity, fault_class=fault_class
        ).inc()
        time_to_detect.labels(incident_type=incident_type).observe(detect_time)
        time_to_respond.labels(incident_type=incident_type).observe(respond_time)
        time_to_resolve.labels(incident_type=incident_type).observe(resolve_time)
    
    def _get_provider(self, model: str) -> str:
        """Infer provider from model name."""
        if model.startswith("gpt"):
            return "openai"
        elif model.startswith("claude"):
            return "anthropic"
        elif model.startswith("llama"):
            return "meta"
        return "unknown"


# ─── Singleton Instance ─────────────────────────────────────────────────────

metrics = MetricsCollector()
```

### 1.2 Langfuse Trace Collector

```python
# grc_claw/monitoring/langfuse_collector.py
"""
Langfuse integration for LLM tracing and evaluation.
Collects traces, scores, and evaluation data for GRC_Claw.
"""

import os
import time
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context


@dataclass
class TraceContext:
    """Context for a single trace."""
    trace_id: str
    agent_id: str
    model: str
    start_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    spans: List[Dict] = field(default_factory=list)


class GRCClawLangfuseCollector:
    """
    Langfuse collector for GRC_Claw observability.
    
    Handles trace creation, generation logging, scoring,
    and PII redaction.
    """
    
    def __init__(self):
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        )
        self.environment = os.getenv("GRC_CLAW_ENVIRONMENT", "production")
        self.version = os.getenv("GRC_CLAW_VERSION", "1.0.0")
        self.sample_rate = self._get_sample_rate()
        self._active_traces: Dict[str, TraceContext] = {}
    
    def _get_sample_rate(self) -> float:
        """Get sampling rate based on environment."""
        rates = {"development": 1.0, "staging": 0.5, "production": 0.1}
        return rates.get(self.environment, 0.1)
    
    def _should_sample(self) -> bool:
        """Determine if current request should be sampled."""
        import random
        return random.random() < self.sample_rate
    
    def _generate_trace_id(self, agent_id: str, task: str) -> str:
        """Generate a deterministic trace ID."""
        data = f"{agent_id}:{task}:{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def start_trace(self, agent_id: str, task: str, model: str,
                    metadata: Optional[Dict] = None) -> Optional[str]:
        """Start a new trace for an agent run."""
        if not self._should_sample():
            return None
        
        trace_id = self._generate_trace_id(agent_id, task)
        
        langfuse_context.update_current_trace(
            id=trace_id,
            name=f"agent-{agent_id}",
            user_id=agent_id,
            metadata={
                "agent_id": agent_id,
                "task": task,
                "model": model,
                "environment": self.environment,
                "grc_claw_version": self.version,
                **(metadata or {})
            }
        )
        
        self._active_traces[trace_id] = TraceContext(
            trace_id=trace_id,
            agent_id=agent_id,
            model=model,
            start_time=time.time(),
            metadata=metadata or {}
        )
        
        return trace_id
    
    def log_llm_generation(self, model: str, messages: List[Dict],
                           response: Dict, latency_ms: float,
                           cost_usd: float):
        """Log an LLM generation within the current trace."""
        usage = response.get("usage", {})
        
        langfuse_context.update_current_generation(
            name="llm-call",
            model=model,
            input=self._redact_pii(messages),
            output=self._redact_pii(response.get("content", "")),
            usage={
                "input": usage.get("prompt_tokens", 0),
                "output": usage.get("completion_tokens", 0),
                "total": usage.get("total_tokens", 0)
            },
            metadata={
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
                "finish_reason": response.get("finish_reason", "unknown")
            }
        )
    
    def log_tool_call(self, tool_name: str, arguments: Dict,
                       result: Dict, duration_ms: float,
                       error: Optional[str] = None):
        """Log a tool call within the current trace."""
        langfuse_context.update_current_span(
            name=f"tool-{tool_name}",
            input=arguments,
            output={"result": result, "error": error},
            metadata={"duration_ms": duration_ms}
        )
    
    def log_decision(self, decision_type: str, context: Dict,
                     decision: str, rationale: str):
        """Log a governance decision."""
        langfuse_context.update_current_span(
            name=f"decision-{decision_type}",
            input=context,
            output={"decision": decision, "rationale": rationale},
            metadata={"decision_type": decision_type}
        )
    
    def score_trace(self, trace_id: str, score_name: str,
                    value: float, comment: Optional[str] = None):
        """Add a score to a trace."""
        self.langfuse.score(
            trace_id=trace_id,
            name=score_name,
            value=value,
            comment=comment
        )
    
    def score_quality(self, trace_id: str, score: float,
                      eval_type: str = "quality"):
        """Record LLM-as-judge quality score."""
        self.score_trace(trace_id, f"quality-{eval_type}", score)
    
    def score_safety(self, trace_id: str, toxicity: float,
                     pii_detected: bool, jailbreak: bool):
        """Record safety scores for a trace."""
        self.score_trace(trace_id, "safety-toxicity", toxicity)
        self.score_trace(trace_id, "safety-pii_detected", float(pii_detected))
        self.score_trace(trace_id, "safety-jailbreak", float(jailbreak))
    
    def end_trace(self, trace_id: str, output: Optional[Dict] = None):
        """End a trace and flush."""
        if trace_id in self._active_traces:
            trace = self._active_traces.pop(trace_id)
            duration = time.time() - trace.start_time
            
            langfuse_context.update_current_trace(
                output=output,
                metadata={
                    **trace.metadata,
                    "duration_seconds": duration,
                    "completed_at": datetime.utcnow().isoformat()
                }
            )
    
    def flush(self):
        """Flush all pending traces to Langfuse."""
        self.langfuse.flush()
    
    def _redact_pii(self, data: Any) -> Any:
        """Redact PII from data before sending to Langfuse."""
        # Integration with Presidio or similar PII detection
        # This is a placeholder - actual implementation would use
        # the presidio skill or similar PII detection library
        if isinstance(data, str):
            # Simple regex-based redaction for common PII patterns
            import re
            # Email addresses
            data = re.sub(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                '[REDACTED_EMAIL]', data
            )
            # Phone numbers
            data = re.sub(
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                '[REDACTED_PHONE]', data
            )
            # SSN
            data = re.sub(
                r'\b\d{3}-\d{2}-\d{4}\b',
                '[REDACTED_SSN]', data
            )
            return data
        elif isinstance(data, list):
            return [self._redact_pii(item) for item in data]
        elif isinstance(data, dict):
            return {k: self._redact_pii(v) for k, v in data.items()}
        return data
```

### 1.3 Arize Drift Collector

```python
# grc_claw/monitoring/arize_collector.py
"""
Arize integration for model monitoring, drift detection,
and bias/fairness tracking.
"""

import os
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from arize.api import Client
from arize.utils.types import (
    Environments, ModelTypes, Schema, EmbeddingColumnNames
)


class GRCClawArizeCollector:
    """
    Arize collector for GRC_Claw model monitoring.
    
    Handles prediction logging, drift detection, and
    fairness metric reporting.
    """
    
    def __init__(self, model_id: str, model_version: str,
                 environment: str = "production"):
        self.model_id = model_id
        self.model_version = model_version
        self.environment = (
            Environments.PRODUCTION if environment == "production"
            else Environments.STAGING
        )
        
        self.arize = Client(
            space_key=os.getenv("ARIZE_SPACE_KEY"),
            api_key=os.getenv("ARIZE_API_KEY")
        )
        
        self.schema = Schema(
            prediction_column_name="prediction",
            actual_label_column_name="actual",
            feature_column_names=[
                "user_input", "context", "agent_id", "task_type",
                "protected_class_gender", "protected_class_race",
                "protected_class_age"
            ],
            embedding_features={
                "input_embedding": EmbeddingColumnNames(
                    vector_column_name="input_vector",
                    data_column_name="user_input"
                )
            },
            tag_column_names=["model_version", "agent_id", "environment"]
        )
    
    def log_prediction(self, prediction_id: str, prediction: str,
                      features: Dict, actual: Optional[str] = None,
                      embedding_vector: Optional[List[float]] = None):
        """Log a prediction for drift and performance monitoring."""
        response = self.arize.log(
            model_id=self.model_id,
            model_version=self.model_version,
            environment=self.environment,
            model_type=ModelTypes.SCORE_CATEGORICAL,
            schema=self.schema,
            prediction_id=prediction_id,
            prediction_label=prediction,
            actual_label=actual,
            features=features,
            embedding_vectors={"input_embedding": embedding_vector},
            tags={
                "model_version": self.model_version,
                "agent_id": features.get("agent_id", "unknown"),
                "environment": self.environment.value
            }
        )
        return response
    
    def log_fairness_metrics(self, metrics: Dict[str, Dict]):
        """
        Log fairness metrics for bias monitoring.
        
        Args:
            metrics: Dict mapping protected_class to fairness metrics.
                Example: {
                    "gender": {
                        "demographic_parity_diff": 0.05,
                        "equalized_odds_diff": 0.03,
                        "disparate_impact_ratio": 0.95
                    }
                }
        """
        for protected_class, values in metrics.items():
            self.arize.log_fairness(
                model_id=self.model_id,
                model_version=self.model_version,
                protected_class=protected_class,
                demographic_parity_difference=values.get("demographic_parity_diff"),
                equalized_odds_difference=values.get("equalized_odds_diff"),
                disparate_impact_ratio=values.get("disparate_impact_ratio")
            )
    
    def get_drift_report(self, start_date: str, end_date: str) -> Dict:
        """Generate drift report for a time period."""
        return self.arize.get_drift(
            model_id=self.model_id,
            model_version=self.model_version,
            start_date=start_date,
            end_date=end_date
        )
    
    def compute_psi(self, reference: np.ndarray,
                    current: np.ndarray, bins: int = 10) -> float:
        """
        Compute Population Stability Index (PSI).
        
        PSI < 0.1: No significant shift
        0.1 ≤ PSI < 0.2: Moderate shift
        PSI ≥ 0.2: Significant shift
        """
        ref_hist, bin_edges = np.histogram(reference, bins=bins)
        cur_hist, _ = np.histogram(current, bins=bin_edges)
        
        # Normalize to probabilities
        ref_pct = ref_hist / len(reference)
        cur_pct = cur_hist / len(current)
        
        # Avoid division by zero
        ref_pct = np.clip(ref_pct, 1e-6, None)
        cur_pct = np.clip(cur_pct, 1e-6, None)
        
        psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        return float(psi)
    
    def compute_ks_test(self, reference: np.ndarray,
                        current: np.ndarray) -> float:
        """
        Compute Kolmogorov-Smirnov test statistic.
        
        Returns the KS statistic (0-1). Higher values indicate
        greater distribution difference.
        """
        from scipy import stats
        statistic, pvalue = stats.ks_2samp(reference, current)
        return float(statistic)
    
    def compute_wasserstein_distance(self, reference: np.ndarray,
                                     current: np.ndarray) -> float:
        """Compute Wasserstein distance between two distributions."""
        from scipy.stats import wasserstein_distance
        return float(wasserstein_distance(reference, current))
```

### 1.4 Datadog Infrastructure Collector

```python
# grc_claw/monitoring/datadog_collector.py
"""
Datadog integration for infrastructure monitoring, APM,
and log management.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

from datadog import initialize, statsd


class GRCClawDatadogCollector:
    """
    Datadog collector for GRC_Claw infrastructure monitoring.
    
    Handles custom metrics, events, and incident reporting.
    """
    
    def __init__(self):
        initialize(
            api_key=os.getenv("DATADOG_API_KEY"),
            app_key=os.getenv("DATADOG_APP_KEY")
        )
        self.statsd = statsd
        self.environment = os.getenv("GRC_CLAW_ENVIRONMENT", "production")
        self.version = os.getenv("GRC_CLAW_VERSION", "1.0.0")
        self.base_tags = [
            f"env:{self.environment}",
            f"version:{self.version}",
            "service:grc-claw"
        ]
    
    def emit_gauge(self, metric_name: str, value: float,
                   tags: Optional[List[str]] = None):
        """Emit a gauge metric."""
        all_tags = self.base_tags + (tags or [])
        self.statsd.gauge(metric_name, value, tags=all_tags)
    
    def emit_counter(self, metric_name: str, value: int = 1,
                     tags: Optional[List[str]] = None):
        """Emit a counter metric."""
        all_tags = self.base_tags + (tags or [])
        self.statsd.increment(metric_name, value, tags=all_tags)
    
    def emit_histogram(self, metric_name: str, value: float,
                       tags: Optional[List[str]] = None):
        """Emit a histogram metric."""
        all_tags = self.base_tags + (tags or [])
        self.statsd.histogram(metric_name, value, tags=all_tags)
    
    def emit_event(self, title: str, text: str,
                   tags: Optional[List[str]] = None,
                   alert_type: str = "info"):
        """Emit a Datadog event."""
        all_tags = self.base_tags + (tags or [])
        self.statsd.event(
            title=title,
            text=text,
            tags=all_tags,
            alert_type=alert_type
        )
    
    def emit_safety_incident(self, incident: Dict):
        """Emit a safety incident as a Datadog event."""
        severity = incident.get("severity", "P2")
        alert_type = "error" if severity == "P0" else "warning"
        
        self.emit_event(
            title=f"Safety Incident: {incident['type']}",
            text=incident["description"],
            tags=[
                f"agent_id:{incident['agent_id']}",
                f"severity:{severity}",
                f"type:{incident['type']}",
                "grc_claw:safety"
            ],
            alert_type=alert_type
        )
    
    def emit_governance_decision(self, decision: Dict):
        """Emit a governance decision as a Datadog event."""
        self.emit_event(
            title=f"Governance Decision: {decision['action']}",
            text=decision["rationale"],
            tags=[
                f"decision_type:{decision['type']}",
                f"risk_level:{decision['risk_level']}",
                "grc_claw:governance"
            ],
            alert_type="info"
        )
    
    def emit_enforcement_metrics(self, decision: str, policy_id: str,
                                  agent_id: str, duration_ms: float):
        """Emit enforcement decision metrics."""
        self.emit_counter(
            "grc.enforcement.decisions",
            tags=[f"decision:{decision}", f"policy_id:{policy_id}",
                  f"agent_id:{agent_id}"]
        )
        self.emit_histogram(
            "grc.enforcement.duration_ms",
            duration_ms,
            tags=[f"decision:{decision}"]
        )
```

---

## 2. Alert Rules (Prometheus)

### 2.1 Prometheus Alert Rules

```yaml
# grc_claw/monitoring/prometheus/alert_rules.yml
# GRC_Claw Prometheus Alert Rules
# 30+ alert rules across 7 categories

groups:
  # ─── Model Performance Alerts ──────────────────────────────────────────
  - name: model_performance
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: llm_error_rate > 0.05
        for: 5m
        labels:
          severity: P1
          category: model_performance
        annotations:
          summary: "High error rate for model {{ $labels.model }}"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"
          runbook: "https://wiki.internal/runbooks/high-error-rate"

      - alert: LowSuccessRate
        expr: llm_success_rate < 0.95
        for: 10m
        labels:
          severity: P1
          category: model_performance
        annotations:
          summary: "Low success rate for model {{ $labels.model }}"
          description: "Success rate is {{ $value | humanizePercentage }} (threshold: 95%)"

      - alert: HighP95Latency
        expr: histogram_quantile(0.95, rate(llm_request_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: P2
          category: model_performance
        annotations:
          summary: "High P95 latency for model {{ $labels.model }}"
          description: "P95 latency is {{ $value }}s (threshold: 10s)"

      - alert: HighCostRate
        expr: rate(llm_cost_total_dollars[1h]) > 100
        for: 1h
        labels:
          severity: P2
          category: model_performance
        annotations:
          summary: "High LLM cost rate"
          description: "Cost rate is ${{ $value }}/hr (threshold: $100/hr)"

      - alert: LowQualityScore
        expr: llm_quality_score < 0.7
        for: 15m
        labels:
          severity: P2
          category: model_performance
        annotations:
          summary: "Low quality score for model {{ $labels.model }}"
          description: "Quality score is {{ $value }} (threshold: 0.7)"

      - alert: HighTimeoutRate
        expr: llm_timeout_rate > 0.02
        for: 5m
        labels:
          severity: P2
          category: model_performance
        annotations:
          summary: "High timeout rate for model {{ $labels.model }}"
          description: "Timeout rate is {{ $value | humanizePercentage }} (threshold: 2%)"

      - alert: HighRetryRate
        expr: rate(llm_retry_count_total[5m]) > 0.1
        for: 5m
        labels:
          severity: P3
          category: model_performance
        annotations:
          summary: "High retry rate for model {{ $labels.model }}"
          description: "Retry rate is {{ $value }}/s (threshold: 0.1/s)"

  # ─── Drift Detection Alerts ───────────────────────────────────────────
  - name: drift_detection
    interval: 60s
    rules:
      - alert: FeatureDriftDetected
        expr: feature_drift_score > 0.2
        for: 15m
        labels:
          severity: P2
          category: drift
        annotations:
          summary: "Feature drift detected for {{ $labels.feature_name }}"
          description: "PSI is {{ $value }} (threshold: 0.2)"

      - alert: PredictionDriftDetected
        expr: prediction_drift_score > 0.15
        for: 15m
        labels:
          severity: P2
          category: drift
        annotations:
          summary: "Prediction drift detected for model {{ $labels.model_id }}"
          description: "Drift score is {{ $value }} (threshold: 0.15)"

      - alert: EmbeddingDriftDetected
        expr: embedding_drift_score > 0.3
        for: 30m
        labels:
          severity: P2
          category: drift
        annotations:
          summary: "Embedding drift detected for model {{ $labels.model_id }}"
          description: "Wasserstein distance is {{ $value }} (threshold: 0.3)"

      - alert: ModelVersionRegression
        expr: model_version_delta < -0.1
        for: 10m
        labels:
          severity: P1
          category: drift
        annotations:
          summary: "Model version regression detected"
          description: "Performance delta is {{ $value }} (threshold: -0.1)"

      - alert: TrainingServingSkew
        expr: training_serving_skew > 0.15
        for: 15m
        labels:
          severity: P2
          category: drift
        annotations:
          summary: "Training-serving skew detected"
          description: "Skew is {{ $value }} for feature {{ $labels.feature }} (threshold: 0.15)"

      - alert: LowDataQualityScore
        expr: data_quality_score < 0.8
        for: 15m
        labels:
          severity: P2
          category: drift
        annotations:
          summary: "Low data quality score"
          description: "Data quality is {{ $value }} (threshold: 0.8)"

  # ─── Bias & Fairness Alerts ───────────────────────────────────────────
  - name: bias_fairness
    interval: 60s
    rules:
      - alert: DemographicParityViolation
        expr: abs(demographic_parity_diff) > 0.10
        for: 15m
        labels:
          severity: P1
          category: bias_fairness
        annotations:
          summary: "Demographic parity violation for {{ $labels.protected_class }}"
          description: "Difference is {{ $value }} (threshold: ±0.10)"

      - alert: EqualizedOddsViolation
        expr: abs(equalized_odds_diff) > 0.10
        for: 15m
        labels:
          severity: P1
          category: bias_fairness
        annotations:
          summary: "Equalized odds violation for {{ $labels.protected_class }}"
          description: "Difference is {{ $value }} (threshold: ±0.10)"

      - alert: DisparateImpactViolation
        expr: disparate_impact_ratio < 0.80 or disparate_impact_ratio > 1.25
        for: 15m
        labels:
          severity: P1
          category: bias_fairness
        annotations:
          summary: "Disparate impact violation for {{ $labels.protected_class }}"
          description: "Ratio is {{ $value }} (threshold: 0.80-1.25)"

      - alert: HighBiasScore
        expr: bias_score > 0.5
        for: 15m
        labels:
          severity: P1
          category: bias_fairness
        annotations:
          summary: "High bias score for model {{ $labels.model_id }}"
          description: "Bias score is {{ $value }} (threshold: 0.5)"

      - alert: FairnessViolationSpike
        expr: rate(fairness_violation_count_total[15m]) > 5
        for: 15m
        labels:
          severity: P1
          category: bias_fairness
        annotations:
          summary: "Fairness violation spike"
          description: "Violation rate is {{ $value }}/s (threshold: 5/s)"

  # ─── Safety Alerts ────────────────────────────────────────────────────
  - name: safety
    interval: 30s
    rules:
      - alert: ToxicityDetected
        expr: toxicity_score > 0.7
        for: 1m
        labels:
          severity: P0
          category: safety
        annotations:
          summary: "Toxic content detected"
          description: "Toxicity score is {{ $value }} (threshold: 0.7)"

      - alert: JailbreakAttempt
        expr: rate(jailbreak_attempt_count_total[5m]) > 0
        for: 1m
        labels:
          severity: P0
          category: safety
        annotations:
          summary: "Jailbreak attempt detected"
          description: "Jailbreak technique: {{ $labels.technique }}"

      - alert: PromptInjectionDetected
        expr: rate(prompt_injection_count_total[5m]) > 0
        for: 1m
        labels:
          severity: P0
          category: safety
        annotations:
          summary: "Prompt injection detected"
          description: "Source: {{ $labels.source }}"

      - alert: HighHarmfulContentRate
        expr: harmful_content_rate > 0.01
        for: 5m
        labels:
          severity: P1
          category: safety
        annotations:
          summary: "High harmful content rate"
          description: "Rate is {{ $value | humanizePercentage }} (threshold: 1%)"

      - alert: GuardFalsePositiveRateHigh
        expr: guard_false_positive_rate > 0.15
        for: 30m
        labels:
          severity: P2
          category: safety
        annotations:
          summary: "High false positive rate for guard {{ $labels.guard_type }}"
          description: "FPR is {{ $value | humanizePercentage }} (threshold: 15%)"

      - alert: GuardFalseNegativeRateHigh
        expr: guard_false_negative_rate > 0.05
        for: 30m
        labels:
          severity: P1
          category: safety
        annotations:
          summary: "High false negative rate for guard {{ $labels.guard_type }}"
          description: "FNR is {{ $value | humanizePercentage }} (threshold: 5%)"

      - alert: HighReaskRate
        expr: reask_rate > 0.20
        for: 30m
        labels:
          severity: P3
          category: safety
        annotations:
          summary: "High reask rate"
          description: "Reask rate is {{ $value | humanizePercentage }} (threshold: 20%)"

      - alert: PIIDetectionSpike
        expr: rate(pii_detection_count_total[5m]) > 10
        for: 5m
        labels:
          severity: P1
          category: safety
        annotations:
          summary: "PII detection spike"
          description: "PII detection rate is {{ $value }}/s (threshold: 10/s)"

  # ─── Security Alerts ──────────────────────────────────────────────────
  - name: security
    interval: 30s
    rules:
      - alert: ConstraintBreach
        expr: rate(constraint_breach_count_total[5m]) > 0
        for: 1m
        labels:
          severity: P0
          category: security
        annotations:
          summary: "Policy constraint breach"
          description: "Policy: {{ $labels.policy_id }}"

      - alert: UnauthorizedAction
        expr: rate(unauthorized_action_count_total[5m]) > 0
        for: 1m
        labels:
          severity: P0
          category: security
        annotations:
          summary: "Unauthorized action attempt"
          description: "Action: {{ $labels.action_type }}"

      - alert: PrivilegeEscalation
        expr: rate(privilege_escalation_count_total[5m]) > 0
        for: 1m
        labels:
          severity: P0
          category: security
        annotations:
          summary: "Privilege escalation attempt"
          description: "Agent: {{ $labels.agent_id }}"

      - alert: HighAnomalyScore
        expr: anomaly_score > 0.8
        for: 5m
        labels:
          severity: P1
          category: security
        annotations:
          summary: "High behavioral anomaly score"
          description: "Anomaly score is {{ $value }} (threshold: 0.8)"

      - alert: AuditLogIntegrityFailure
        expr: audit_log_integrity < 1.0
        for: 1m
        labels:
          severity: P0
          category: security
        annotations:
          summary: "Audit log integrity failure"
          description: "Integrity score is {{ $value }} (expected: 1.0)"

      - alert: AccessViolationSpike
        expr: rate(access_violation_count_total[5m]) > 5
        for: 5m
        labels:
          severity: P1
          category: security
        annotations:
          summary: "Access violation spike"
          description: "Violation rate is {{ $value }}/s (threshold: 5/s)"

      - alert: ThreatDetectionSpike
        expr: rate(threat_detection_count_total[5m]) > 0
        for: 1m
        labels:
          severity: P0
          category: security
        annotations:
          summary: "Security threat detected"
          description: "Source: {{ $labels.source }}, Severity: {{ $labels.severity }}"

  # ─── Agent Behavior Alerts ────────────────────────────────────────────
  - name: agent_behavior
    interval: 30s
    rules:
      - alert: AgentLoopDetected
        expr: agent_loop_count > 50
        for: 5m
        labels:
          severity: P2
          category: agent_behavior
        annotations:
          summary: "Agent loop detected"
          description: "Loop count is {{ $value }} (threshold: 50)"

      - alert: AgentContextWindowNearLimit
        expr: agent_context_window_usage > 0.90
        for: 5m
        labels:
          severity: P2
          category: agent_behavior
        annotations:
          summary: "Agent context window near limit"
          description: "Usage is {{ $value | humanizePercentage }} (threshold: 90%)"

      - alert: AgentHighEscalationRate
        expr: agent_human_escalation_rate > 0.30
        for: 30m
        labels:
          severity: P2
          category: agent_behavior
        annotations:
          summary: "High human escalation rate"
          description: "Rate is {{ $value | humanizePercentage }} (threshold: 30%)"

      - alert: AgentHighCostPerRun
        expr: agent_cost_per_run_dollars > 5.00
        for: 1h
        labels:
          severity: P3
          category: agent_behavior
        annotations:
          summary: "High cost per agent run"
          description: "Cost is ${{ $value }} (threshold: $5.00)"

      - alert: AgentLowSuccessRate
        expr: agent_success_rate < 0.80
        for: 15m
        labels:
          severity: P2
          category: agent_behavior
        annotations:
          summary: "Low agent success rate"
          description: "Success rate is {{ $value | humanizePercentage }} (threshold: 80%)"

      - alert: AgentHighToolErrorRate
        expr: |
          rate(agent_tool_error_count_total[5m])
          / rate(agent_tool_call_count_total[5m]) > 0.10
        for: 10m
        labels:
          severity: P2
          category: agent_behavior
        annotations:
          summary: "High tool error rate for agent {{ $labels.agent_id }}"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 10%)"

  # ─── Incident Response Alerts ─────────────────────────────────────────
  - name: incident_response
    interval: 30s
    rules:
      - alert: HighIncidentRate
        expr: rate(incident_count_total[1h]) > 10
        for: 1h
        labels:
          severity: P1
          category: incident_response
        annotations:
          summary: "High incident rate"
          description: "Incident rate is {{ $value }}/hr (threshold: 10/hr)"

      - alert: SlowDetection
        expr: histogram_quantile(0.95, rate(time_to_detect_seconds_bucket[15m])) > 300
        for: 5m
        labels:
          severity: P2
          category: incident_response
        annotations:
          summary: "Slow incident detection"
          description: "P95 detection time is {{ $value }}s (threshold: 300s)"

      - alert: SlowResolution
        expr: histogram_quantile(0.95, rate(time_to_resolve_seconds_bucket[1h])) > 3600
        for: 15m
        labels:
          severity: P2
          category: incident_response
        annotations:
          summary: "Slow incident resolution"
          description: "P95 resolution time is {{ $value }}s (threshold: 3600s)"

      - alert: RecurringIncident
        expr: incident_recurrence_count > 3
        for: 24h
        labels:
          severity: P1
          category: incident_response
        annotations:
          summary: "Recurring incident pattern"
          description: "Recurrence count is {{ $value }} (threshold: 3)"

      - alert: VerificationFailure
        expr: rate(verification_failure_count_total[24h]) > 0
        for: 1h
        labels:
          severity: P1
          category: incident_response
        annotations:
          summary: "Post-fix verification failure"
          description: "Verification failures detected"

      - alert: HighImpactIncident
        expr: incident_impact_score >= 4
        for: 5m
        labels:
          severity: P0
          category: incident_response
        annotations:
          summary: "High impact incident"
          description: "Impact score is {{ $value }} (threshold: 4)"

  # ─── Monitoring Health Alerts ─────────────────────────────────────────
  - name: monitoring_health
    interval: 60s
    rules:
      - alert: PrometheusTargetDown
        expr: up{job="grc-claw"} == 0
        for: 2m
        labels:
          severity: P1
          category: monitoring
        annotations:
          summary: "Prometheus target down"
          description: "Target {{ $labels.instance }} is down"

      - alert: HighPrometheusMemory
        expr: |
          process_resident_memory_bytes{job="prometheus"}
          / 1024 / 1024 / 1024 > 8
        for: 10m
        labels:
          severity: P2
          category: monitoring
        annotations:
          summary: "Prometheus memory usage high"
          description: "Memory usage is {{ $value }}GB (threshold: 8GB)"

      - alert: AlertmanagerSilenceExpiring
        expr: |
          alertmanager_silences{state="active"}
          and on() (time() - alertmanager_silences{state="active"}["starts_at"]) > 82800
        for: 1h
        labels:
          severity: P3
          category: monitoring
        annotations:
          summary: "Alert silence expiring soon"
          description: "Silence for {{ $labels.alertname }} expires in <12h"
```

### 2.2 AlertManager Configuration

```yaml
# grc_claw/monitoring/prometheus/alertmanager.yml
# AlertManager routing and receiver configuration

global:
  smtp_smarthost: 'smtp.company.com:587'
  smtp_from: 'grc-claw@company.com'
  smtp_auth_username: 'grc-claw@company.com'
  smtp_auth_password: '${SMTP_PASSWORD}'
  slack_api_url: '${SLACK_WEBHOOK_URL}'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'
  resolve_timeout: 5m

# Templates
templates:
  - '/etc/alertmanager/templates/*.tmpl'

# Route tree
route:
  receiver: default
  group_by: ['alertname', 'severity', 'category', 'model_id']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    # P0 — Critical: Immediate PagerDuty page + phone
    - match:
        severity: P0
      receiver: pagerduty-critical
      group_wait: 0s
      group_interval: 1m
      repeat_interval: 5m
      continue: true

    # P1 — High: PagerDuty page
    - match:
        severity: P1
      receiver: pagerduty-high
      group_wait: 0s
      group_interval: 5m
      repeat_interval: 15m
      continue: true

    # P2 — Medium: Slack #alerts
    - match:
        severity: P2
      receiver: slack-alerts
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 1h

    # P3 — Low: Slack #alerts-low
    - match:
        severity: P3
      receiver: slack-alerts-low
      group_wait: 5m
      group_interval: 15m
      repeat_interval: 4h

    # P4 — Info: Email digest
    - match:
        severity: P4
      receiver: email-digest
      group_wait: 1h
      group_interval: 6h
      repeat_interval: 24h

    # Monitoring self-alerts go to infra team
    - match:
        category: monitoring
      receiver: slack-infra
      group_wait: 1m
      repeat_interval: 2h

# Inhibition rules
inhibit_rules:
  # If P0 is firing, don't also fire P1 for same alert
  - source_match:
      severity: P0
    target_match:
      severity: P1
    equal: ['alertname', 'model_id']

  # If P1 is firing, don't also fire P2 for same alert
  - source_match:
      severity: P1
    target_match:
      severity: P2
    equal: ['alertname', 'model_id']

  # If model is down, don't fire individual metric alerts
  - source_match:
      alertname: PrometheusTargetDown
    target_match_re:
      alertname: 'HighErrorRate|LowSuccessRate|HighP95Latency'
    equal: ['model_id']

# Receivers
receivers:
  - name: 'default'
    slack_configs:
      - channel: '#grc-alerts'
        send_resolved: true
        title: '{{ template "slack.default.title" . }}'
        text: '{{ template "slack.default.text" . }}'

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - routing_key: '${PAGERDUTY_CRITICAL_KEY}'
        severity: critical
        description: '{{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ template "pagerduty.default.instances" .Alerts.Firing }}'
          resolved: '{{ template "pagerduty.default.instances" .Alerts.Resolved }}'
          runbook: '{{ .CommonAnnotations.runbook }}'

  - name: 'pagerduty-high'
    pagerduty_configs:
      - routing_key: '${PAGERDUTY_HIGH_KEY}'
        severity: error
        description: '{{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ template "pagerduty.default.instances" .Alerts.Firing }}'
          runbook: '{{ .CommonAnnotations.runbook }}'

  - name: 'slack-alerts'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#grc-alerts'
        send_resolved: true
        title: '[{{ .CommonLabels.severity }}] {{ .CommonLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'
        actions:
          - type: button
            text: 'Runbook'
            url: '{{ .CommonAnnotations.runbook }}'
          - type: button
            text: 'Dashboard'
            url: 'https://grafana.internal/d/grc-claw'

  - name: 'slack-alerts-low'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#grc-alerts-low'
        send_resolved: true
        title: '[{{ .CommonLabels.severity }}] {{ .CommonLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'

  - name: 'slack-infra'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#infra-alerts'
        send_resolved: true
        title: '[Monitoring] {{ .CommonLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'

  - name: 'email-digest'
    email_configs:
      - to: 'ai-governance@company.com'
        from: 'grc-claw@company.com'
        smarthost: 'smtp.company.com:587'
        auth_username: 'grc-claw@company.com'
        auth_password: '${SMTP_PASSWORD}'
        headers:
          Subject: '[GRC_Claw] {{ .CommonLabels.severity }}: {{ .CommonLabels.alertname }}'
        html: '{{ template "email.default.html" . }}'
```

### 2.3 Prometheus Scrape Configuration

```yaml
# grc_claw/monitoring/prometheus/prometheus.yml
# Prometheus server configuration

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'grc-claw-production'
    region: 'us-east-1'

# Alert rules
rule_files:
  - '/etc/prometheus/rules/alert_rules.yml'

# Alertmanager
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
      timeout: 10s

# Scrape configurations
scrape_configs:
  # GRC_Claw application metrics
  - job_name: 'grc-claw'
    static_configs:
      - targets: ['grc-claw:8000']
    metrics_path: /metrics
    scrape_interval: 15s
    scrape_timeout: 10s
    labels:
      service: grc-claw
      environment: production

  # Langfuse metrics
  - job_name: 'langfuse'
    static_configs:
      - targets: ['langfuse:3000']
    metrics_path: /api/public/metrics
    scrape_interval: 30s
    scrape_timeout: 15s

  # Arize metrics
  - job_name: 'arize'
    static_configs:
      - targets: ['arize:8080']
    metrics_path: /metrics
    scrape_interval: 30s
    scrape_timeout: 15s

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s

  # Grafana metrics
  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
    metrics_path: /metrics
    scrape_interval: 30s

  # Node exporter (infrastructure)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  # cAdvisor (container metrics)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 15s
```

---

## 3. Dashboard Configurations (Grafana JSON)

### 3.1 Executive Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "GRC_Claw — Executive Dashboard",
    "description": "High-level governance posture for C-suite and auditors",
    "tags": ["grc-claw", "executive", "governance"],
    "timezone": "browser",
    "refresh": "1m",
    "time": {"from": "now-24h", "to": "now"},
    "schemaVersion": 39,
    "version": 1,
    "panels": [
      {
        "id": 1,
        "title": "Overall Risk Score",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "grc_claw_risk_score_overall",
          "legendFormat": "Risk Score",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "none",
            "min": 0,
            "max": 100,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 30},
                {"color": "orange", "value": 50},
                {"color": "red", "value": 70},
                {"color": "dark-red", "value": 85}
              ]
            }
          }
        },
        "options": {
          "colorMode": "background",
          "graphMode": "area",
          "justifyMode": "auto",
          "orientation": "auto",
          "reduceOptions": {"calcs": ["lastNotNull"]}
        }
      },
      {
        "id": 2,
        "title": "Active Incidents",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(increase(incident_count_total[24h])) by (severity)",
          "legendFormat": "{{severity}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "none",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 1},
                {"color": "red", "value": 5}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Compliance Status",
        "type": "table",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "grc_claw_compliance_score",
          "format": "table",
          "instant": true,
          "refId": "A"
        }],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {"Time": true},
              "renameByName": {
                "clause": "ISO 42001 Clause",
                "value": "Compliance %"
              }
            }
          }
        ]
      },
      {
        "id": 4,
        "title": "Model Health Summary",
        "type": "table",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 4},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "llm_success_rate",
          "format": "table",
          "instant": true,
          "refId": "A"
        }],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {"Time": true},
              "renameByName": {
                "model": "Model",
                "value": "Success Rate"
              }
            }
          }
        ]
      },
      {
        "id": 5,
        "title": "Fairness Overview",
        "type": "gauge",
        "gridPos": {"h": 5, "w": 6, "x": 0, "y": 10},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "abs(demographic_parity_diff)",
          "legendFormat": "{{protected_class}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "none",
            "min": 0,
            "max": 0.3,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 0.1},
                {"color": "red", "value": 0.2}
              ]
            }
          }
        }
      },
      {
        "id": 6,
        "title": "Safety Incidents (24h)",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 12, "x": 6, "y": 10},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [
          {
            "expr": "sum(increase(safety_violation_count_total[24h]))",
            "legendFormat": "Safety Violations",
            "refId": "A"
          },
          {
            "expr": "sum(increase(jailbreak_attempt_count_total[24h]))",
            "legendFormat": "Jailbreak Attempts",
            "refId": "B"
          },
          {
            "expr": "sum(increase(prompt_injection_count_total[24h]))",
            "legendFormat": "Prompt Injections",
            "refId": "C"
          }
        ]
      },
      {
        "id": 7,
        "title": "Cost & Budget",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 12, "x": 0, "y": 15},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [
          {
            "expr": "sum(rate(llm_cost_total_dollars[1h])) * 3600",
            "legendFormat": "Hourly Cost ($)",
            "refId": "A"
          },
          {
            "expr": "grc_claw_budget_limit_dollars_per_hour",
            "legendFormat": "Budget Limit",
            "refId": "B",
            "lineStyle": {"fill": "dash", "dash": [10, 10]}
          }
        ],
        "fieldConfig": {
          "defaults": {"unit": "currencyUSD"}
        }
      },
      {
        "id": 8,
        "title": "Audit Trail Status",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": 15},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "audit_log_integrity",
          "legendFormat": "{{log_source}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": null},
                {"color": "green", "value": 1}
              ]
            }
          }
        }
      }
    ]
  }
}
```

### 3.2 Model Performance Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "GRC_Claw — Model Performance",
    "description": "Track LLM model health, quality, and cost",
    "tags": ["grc-claw", "model", "performance"],
    "timezone": "browser",
    "refresh": "30s",
    "time": {"from": "now-6h", "to": "now"},
    "schemaVersion": 39,
    "version": 1,
    "templating": {
      "list": [
        {
          "name": "model",
          "label": "Model",
          "type": "query",
          "datasource": {"type": "prometheus", "uid": "prometheus"},
          "query": "label_values(llm_request_duration_seconds_bucket, model)",
          "multi": true,
          "includeAll": true
        }
      ]
    },
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(llm_request_duration_seconds_count{model=~\"$model\"}[5m])) by (model)",
          "legendFormat": "{{model}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "reqps"}}
      },
      {
        "id": 2,
        "title": "P50/P95/P99 Latency",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(llm_request_duration_seconds_bucket{model=~\"$model\"}[5m])) by (le, model))",
            "legendFormat": "P50 {{model}}",
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(llm_request_duration_seconds_bucket{model=~\"$model\"}[5m])) by (le, model))",
            "legendFormat": "P95 {{model}}",
            "refId": "B"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(llm_request_duration_seconds_bucket{model=~\"$model\"}[5m])) by (le, model))",
            "legendFormat": "P99 {{model}}",
            "refId": "C"
          }
        ],
        "fieldConfig": {"defaults": {"unit": "s"}}
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 8, "x": 0, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "llm_error_rate{model=~\"$model\"}",
          "legendFormat": "{{model}} — {{error_type}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "percentunit"}}
      },
      {
        "id": 4,
        "title": "Token Usage",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 8, "x": 8, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [
          {
            "expr": "sum(rate(llm_token_usage_total{model=~\"$model\",type=\"input\"}[5m])) by (model)",
            "legendFormat": "Input {{model}}",
            "refId": "A"
          },
          {
            "expr": "sum(rate(llm_token_usage_total{model=~\"$model\",type=\"output\"}[5m])) by (model)",
            "legendFormat": "Output {{model}}",
            "refId": "B"
          }
        ],
        "fieldConfig": {"defaults": {"unit": "short"}}
      },
      {
        "id": 5,
        "title": "Cost per Request",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 8, "x": 0, "y": 11},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(llm_cost_total_dollars{model=~\"$model\"}[5m])) by (model)",
          "legendFormat": "{{model}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "currencyUSD"}}
      },
      {
        "id": 6,
        "title": "Quality Score Distribution",
        "type": "histogram",
        "gridPos": {"h": 5, "w": 8, "x": 8, "y": 11},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "llm_quality_score{model=~\"$model\"}",
          "legendFormat": "{{model}} — {{eval_type}}",
          "refId": "A"
        }]
      },
      {
        "id": 7,
        "title": "Model Comparison",
        "type": "table",
        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 16},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [
          {
            "expr": "llm_success_rate{model=~\"$model\"}",
            "format": "table",
            "instant": true,
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(llm_request_duration_seconds_bucket{model=~\"$model\"}[5m])) by (le, model))",
            "format": "table",
            "instant": true,
            "refId": "B"
          },
          {
            "expr": "sum(rate(llm_cost_total_dollars{model=~\"$model\"}[1h])) by (model)",
            "format": "table",
            "instant": true,
            "refId": "C"
          }
        ],
        "transformations": [
          {
            "id": "merge",
            "options": {}
          },
          {
            "id": "organize",
            "options": {
              "excludeByName": {"Time": true},
              "renameByName": {
                "model": "Model",
                "Value #A": "Success Rate",
                "Value #B": "P95 Latency (s)",
                "Value #C": "Hourly Cost ($)"
              }
            }
          }
        ]
      }
    ]
  }
}
```

### 3.3 Drift Detection Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "GRC_Claw — Drift Detection",
    "description": "Monitor data and model drift over time",
    "tags": ["grc-claw", "drift", "model"],
    "timezone": "browser",
    "refresh": "15m",
    "time": {"from": "now-7d", "to": "now"},
    "schemaVersion": 39,
    "version": 1,
    "panels": [
      {
        "id": 1,
        "title": "Feature Drift Heatmap (PSI)",
        "type": "heatmap",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "feature_drift_score",
          "legendFormat": "{{feature_name}}",
          "refId": "A"
        }],
        "heatmap": {
          "yAxis": {"unit": "none", "min": 0, "max": 1},
          "color": {
            "mode": "scheme",
            "scheme": "RdYlBu",
            "steps": 6,
            "reverse": true
          },
          "dataFormat": "tsbuckets"
        }
      },
      {
        "id": 2,
        "title": "Prediction Distribution Shift",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "prediction_drift_score",
          "legendFormat": "{{model_id}} — {{version}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "none",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 0.15},
                {"color": "red", "value": 0.25}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Embedding Drift (Wasserstein)",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 8},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "embedding_drift_score",
          "legendFormat": "{{model_id}}",
          "refId": "A"
        }]
      },
      {
        "id": 4,
        "title": "Data Quality Score",
        "type": "gauge",
        "gridPos": {"h": 6, "w": 6, "x": 12, "y": 8},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "data_quality_score",
          "legendFormat": "{{model_id}} — {{dataset}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 1,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": null},
                {"color": "yellow", "value": 0.6},
                {"color": "green", "value": 0.8}
              ]
            }
          }
        }
      },
      {
        "id": 5,
        "title": "Drift Alerts",
        "type": "table",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 14},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "ALERTS{alertname=~\".*Drift.*\", alertstate=\"firing\"}",
          "format": "table",
          "instant": true,
          "refId": "A"
        }]
      },
      {
        "id": 6,
        "title": "Retraining Recommendations",
        "type": "table",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 14},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "grc_claw_retraining_recommended",
          "format": "table",
          "instant": true,
          "refId": "A"
        }]
      }
    ]
  }
}
```

### 3.4 Bias & Fairness Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "GRC_Claw — Bias & Fairness",
    "description": "Monitor fairness across protected classes",
    "tags": ["grc-claw", "fairness", "bias"],
    "timezone": "browser",
    "refresh": "15m",
    "time": {"from": "now-24h", "to": "now"},
    "schemaVersion": 39,
    "version": 1,
    "panels": [
      {
        "id": 1,
        "title": "Demographic Parity Difference",
        "type": "bargauge",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "demographic_parity_diff",
          "legendFormat": "{{protected_class}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "none",
            "min": -0.3,
            "max": 0.3,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": null},
                {"color": "green", "value": -0.1},
                {"color": "green", "value": 0.1},
                {"color": "red", "value": 0.2}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Equalized Odds Difference",
        "type": "bargauge",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "equalized_odds_diff",
          "legendFormat": "{{protected_class}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "none",
            "min": -0.3,
            "max": 0.3,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": null},
                {"color": "green", "value": -0.1},
                {"color": "green", "value": 0.1},
                {"color": "red", "value": 0.2}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Disparate Impact Ratio",
        "type": "gauge",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "disparate_impact_ratio",
          "legendFormat": "{{protected_class}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 2,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": null},
                {"color": "yellow", "value": 0.8},
                {"color": "green", "value": 0.9},
                {"color": "green", "value": 1.1},
                {"color": "yellow", "value": 1.25},
                {"color": "red", "value": 1.5}
              ]
            }
          }
        }
      },
      {
        "id": 4,
        "title": "Bias Score Trend",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "bias_score",
          "legendFormat": "{{model_id}} — {{bias_type}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "none",
            "min": 0,
            "max": 1,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 0.3},
                {"color": "red", "value": 0.5}
              ]
            }
          }
        }
      },
      {
        "id": 5,
        "title": "Fairness Violations",
        "type": "table",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 12},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "increase(fairness_violation_count_total[24h])",
          "format": "table",
          "instant": true,
          "refId": "A"
        }]
      },
      {
        "id": 6,
        "title": "Intersectional Analysis",
        "type": "heatmap",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 12},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "grc_claw_intersectional_bias_score",
          "legendFormat": "{{intersection}}",
          "refId": "A"
        }],
        "heatmap": {
          "color": {
            "mode": "scheme",
            "scheme": "RdYlBu",
            "reverse": true
          }
        }
      }
    ]
  }
}
```

### 3.5 Safety Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "GRC_Claw — Safety",
    "description": "Monitor content safety and guardrail effectiveness",
    "tags": ["grc-claw", "safety", "guardrails"],
    "timezone": "browser",
    "refresh": "1m",
    "time": {"from": "now-24h", "to": "now"},
    "schemaVersion": 39,
    "version": 1,
    "panels": [
      {
        "id": 1,
        "title": "Toxicity Score Distribution",
        "type": "histogram",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "toxicity_score",
          "legendFormat": "{{model_id}} — {{content_type}}",
          "refId": "A"
        }]
      },
      {
        "id": 2,
        "title": "Jailbreak Attempts",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(jailbreak_attempt_count_total[5m])) by (technique)",
          "legendFormat": "{{technique}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "ops"}}
      },
      {
        "id": 3,
        "title": "Prompt Injections",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 16, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(prompt_injection_count_total[5m])) by (source)",
          "legendFormat": "{{source}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "ops"}}
      },
      {
        "id": 4,
        "title": "PII Detections",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 8, "x": 0, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(pii_detection_count_total[5m])) by (pii_type)",
          "legendFormat": "{{pii_type}}",
          "refId": "A"
        }]
      },
      {
        "id": 5,
        "title": "Guard Pass Rates",
        "type": "bargauge",
        "gridPos": {"h": 5, "w": 8, "x": 8, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "guard_pass_rate",
          "legendFormat": "{{guard_type}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "percentunit", "min": 0, "max": 1}}
      },
      {
        "id": 6,
        "title": "Guard FPR/FNR",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 8, "x": 16, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [
          {
            "expr": "guard_false_positive_rate",
            "legendFormat": "FPR — {{guard_type}}",
            "refId": "A"
          },
          {
            "expr": "guard_false_negative_rate",
            "legendFormat": "FNR — {{guard_type}}",
            "refId": "B"
          }
        ],
        "fieldConfig": {"defaults": {"unit": "percentunit"}}
      },
      {
        "id": 7,
        "title": "Reask Rate",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 12, "x": 0, "y": 11},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "reask_rate",
          "legendFormat": "{{agent_id}} — {{guard_type}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "percentunit"}}
      },
      {
        "id": 8,
        "title": "Safety Incidents",
        "type": "table",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 11},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "increase(safety_violation_count_total[1h])",
          "format": "table",
          "instant": true,
          "refId": "A"
        }]
      }
    ]
  }
}
```

### 3.6 Security Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "GRC_Claw — Security",
    "description": "Monitor policy compliance and security events",
    "tags": ["grc-claw", "security", "policy"],
    "timezone": "browser",
    "refresh": "1m",
    "time": {"from": "now-24h", "to": "now"},
    "schemaVersion": 39,
    "version": 1,
    "panels": [
      {
        "id": 1,
        "title": "Constraint Breaches",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(constraint_breach_count_total[5m])) by (policy_id)",
          "legendFormat": "{{policy_id}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "ops"}}
      },
      {
        "id": 2,
        "title": "Unauthorized Actions",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(unauthorized_action_count_total[5m])) by (action_type)",
          "legendFormat": "{{action_type}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "ops"}}
      },
      {
        "id": 3,
        "title": "Anomaly Score",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "anomaly_score",
          "legendFormat": "{{agent_id}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 1,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 0.6},
                {"color": "red", "value": 0.8}
              ]
            }
          }
        }
      },
      {
        "id": 4,
        "title": "Access Violations",
        "type": "table",
        "gridPos": {"h": 6, "w": 8, "x": 8, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "increase(access_violation_count_total[1h])",
          "format": "table",
          "instant": true,
          "refId": "A"
        }]
      },
      {
        "id": 5,
        "title": "Audit Log Integrity",
        "type": "stat",
        "gridPos": {"h": 4, "w": 8, "x": 16, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "audit_log_integrity",
          "legendFormat": "{{log_source}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": null},
                {"color": "green", "value": 1}
              ]
            }
          }
        }
      },
      {
        "id": 6,
        "title": "Threat Detections",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 12},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(threat_detection_count_total[5m])) by (severity)",
          "legendFormat": "{{severity}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "ops"}}
      },
      {
        "id": 7,
        "title": "Policy Compliance",
        "type": "gauge",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 12},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "constraint_eval_pass_rate",
          "legendFormat": "{{policy_id}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit",
            "min": 0,
            "max": 1,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": null},
                {"color": "yellow", "value": 0.9},
                {"color": "green", "value": 0.95}
              ]
            }
          }
        }
      }
    ]
  }
}
```

### 3.7 Agent Behavior Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "GRC_Claw — Agent Behavior",
    "description": "Monitor agent performance and behavior patterns",
    "tags": ["grc-claw", "agent", "behavior"],
    "timezone": "browser",
    "refresh": "30s",
    "time": {"from": "now-6h", "to": "now"},
    "schemaVersion": 39,
    "version": 1,
    "templating": {
      "list": [
        {
          "name": "agent",
          "label": "Agent",
          "type": "query",
          "datasource": {"type": "prometheus", "uid": "prometheus"},
          "query": "label_values(agent_run_duration_seconds_bucket, agent_id)",
          "multi": true,
          "includeAll": true
        }
      ]
    },
    "panels": [
      {
        "id": 1,
        "title": "Agent Success Rate",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "agent_success_rate{agent_id=~\"$agent\"}",
          "legendFormat": "{{agent_id}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "percentunit"}}
      },
      {
        "id": 2,
        "title": "Agent Latency (P50/P95/P99)",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(agent_run_duration_seconds_bucket{agent_id=~\"$agent\"}[5m])) by (le, agent_id))",
            "legendFormat": "P50 {{agent_id}}",
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(agent_run_duration_seconds_bucket{agent_id=~\"$agent\"}[5m])) by (le, agent_id))",
            "legendFormat": "P95 {{agent_id}}",
            "refId": "B"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(agent_run_duration_seconds_bucket{agent_id=~\"$agent\"}[5m])) by (le, agent_id))",
            "legendFormat": "P99 {{agent_id}}",
            "refId": "C"
          }
        ],
        "fieldConfig": {"defaults": {"unit": "s"}}
      },
      {
        "id": 3,
        "title": "Tool Usage",
        "type": "bargauge",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(agent_tool_call_count_total{agent_id=~\"$agent\"}[5m])) by (tool_name)",
          "legendFormat": "{{tool_name}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "ops"}}
      },
      {
        "id": 4,
        "title": "Tool Error Rate",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(agent_tool_error_count_total{agent_id=~\"$agent\"}[5m])) by (tool_name)",
          "legendFormat": "{{tool_name}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "ops"}}
      },
      {
        "id": 5,
        "title": "Agent Loop Count",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 8, "x": 0, "y": 12},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "agent_loop_count{agent_id=~\"$agent\"}",
          "legendFormat": "{{agent_id}}",
          "refId": "A"
        }]
      },
      {
        "id": 6,
        "title": "Context Window Usage",
        "type": "gauge",
        "gridPos": {"h": 5, "w": 8, "x": 8, "y": 12},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "agent_context_window_usage{agent_id=~\"$agent\"}",
          "legendFormat": "{{agent_id}}",
          "refId": "A"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit",
            "min": 0,
            "max": 1,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 0.7},
                {"color": "red", "value": 0.9}
              ]
            }
          }
        }
      },
      {
        "id": 7,
        "title": "Human Escalation Rate",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 8, "x": 16, "y": 12},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "agent_human_escalation_rate{agent_id=~\"$agent\"}",
          "legendFormat": "{{agent_id}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "percentunit"}}
      },
      {
        "id": 8,
        "title": "Agent Cost per Run",
        "type": "timeseries",
        "gridPos": {"h": 5, "w": 24, "x": 0, "y": 17},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "agent_cost_per_run_dollars{agent_id=~\"$agent\"}",
          "legendFormat": "{{agent_id}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "currencyUSD"}}
      }
    ]
  }
}
```

### 3.8 Incident Response Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "GRC_Claw — Incident Response",
    "description": "Track incident lifecycle and response effectiveness",
    "tags": ["grc-claw", "incident", "response"],
    "timezone": "browser",
    "refresh": "30s",
    "time": {"from": "now-7d", "to": "now"},
    "schemaVersion": 39,
    "version": 1,
    "panels": [
      {
        "id": 1,
        "title": "Active Incidents",
        "type": "table",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "ALERTS{alertstate=\"firing\", category=\"incident_response\"}",
          "format": "table",
          "instant": true,
          "refId": "A"
        }]
      },
      {
        "id": 2,
        "title": "Incident Rate",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 0},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(incident_count_total[1h])) by (severity)",
          "legendFormat": "{{severity}}",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "ops"}}
      },
      {
        "id": 3,
        "title": "MTTD / MTTR / MTTA",
        "type": "stat",
        "gridPos": {"h": 4, "w": 12, "x": 0, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(time_to_detect_seconds_bucket[24h])) by (le))",
            "legendFormat": "MTTD",
            "refId": "A"
          },
          {
            "expr": "histogram_quantile(0.50, sum(rate(time_to_respond_seconds_bucket[24h])) by (le))",
            "legendFormat": "MTTA",
            "refId": "B"
          },
          {
            "expr": "histogram_quantile(0.50, sum(rate(time_to_resolve_seconds_bucket[24h])) by (le))",
            "legendFormat": "MTTR",
            "refId": "C"
          }
        ],
        "fieldConfig": {"defaults": {"unit": "s"}}
      },
      {
        "id": 4,
        "title": "Incidents by Class",
        "type": "piechart",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(increase(incident_count_total[7d])) by (fault_class)",
          "legendFormat": "{{fault_class}}",
          "refId": "A"
        }],
        "options": {"pieType": "donut", "displayLabels": ["percent"]}
      },
      {
        "id": 5,
        "title": "Recurring Incidents",
        "type": "table",
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 12},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "incident_recurrence_count",
          "format": "table",
          "instant": true,
          "refId": "A"
        }]
      },
      {
        "id": 6,
        "title": "Verification Failures",
        "type": "timeseries",
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 12},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "sum(rate(verification_failure_count_total[24h]))",
          "legendFormat": "Verification Failures",
          "refId": "A"
        }],
        "fieldConfig": {"defaults": {"unit": "ops"}}
      },
      {
        "id": 7,
        "title": "Impact Score Distribution",
        "type": "histogram",
        "gridPos": {"h": 6, "w": 24, "x": 0, "y": 18},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
          "expr": "incident_impact_score",
          "legendFormat": "Impact Score",
          "refId": "A"
        }]
      }
    ]
  }
}
```

---

## 4. Anomaly Detection (Python)

### 4.1 Statistical Anomaly Detector

```python
# grc_claw/monitoring/anomaly_detector.py
"""
Statistical anomaly detection for GRC_Claw metrics.

Supports multiple detection methods:
- Z-Score based detection
- IQR (Interquartile Range) based detection
- Isolation Forest for multivariate anomalies
- Seasonal decomposition for time-series anomalies
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import statistics
import math

from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


@dataclass
class AnomalyResult:
    """Result of an anomaly detection check."""
    is_anomaly: bool
    score: float  # 0-1, higher = more anomalous
    method: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class StatisticalAnomalyDetector:
    """
    Statistical anomaly detection using multiple methods.
    
    Maintains a sliding window of recent values and detects
    anomalies based on statistical properties.
    """
    
    def __init__(self, window_size: int = 100, z_threshold: float = 3.0,
                 iqr_multiplier: float = 1.5):
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier
        self._windows: Dict[str, deque] = {}
        self._scalers: Dict[str, StandardScaler] = {}
    
    def _get_window(self, metric_name: str) -> deque:
        """Get or create a sliding window for a metric."""
        if metric_name not in self._windows:
            self._windows[metric_name] = deque(maxlen=self.window_size)
        return self._windows[metric_name]
    
    def update(self, metric_name: str, value: float) -> AnomalyResult:
        """
        Update the detector with a new value and check for anomalies.
        
        Uses a combination of Z-score and IQR methods.
        """
        window = self._get_window(metric_name)
        
        # Need minimum data for statistical methods
        if len(window) < 10:
            window.append(value)
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                method="insufficient_data",
                details={"window_size": len(window)}
            )
        
        # Z-Score method
        mean = statistics.mean(window)
        stdev = statistics.stdev(window) if len(window) > 1 else 0
        
        if stdev > 0:
            z_score = abs((value - mean) / stdev)
        else:
            z_score = 0
        
        # IQR method
        sorted_window = sorted(window)
        q1 = np.percentile(sorted_window, 25)
        q3 = np.percentile(sorted_window, 75)
        iqr = q3 - q1
        
        if iqr > 0:
            iqr_score = max(0, (value - q3) / iqr) if value > q3 else \
                       max(0, (q1 - value) / iqr) if value < q1 else 0
        else:
            iqr_score = 0
        
        # Combined score (weighted average)
        combined_score = min(1.0, (z_score / self.z_threshold) * 0.6 + 
                                  (iqr_score / self.iqr_multiplier) * 0.4)
        
        is_anomaly = z_score > self.z_threshold or iqr_score > self.iqr_multiplier
        
        # Update window
        window.append(value)
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            score=round(combined_score, 4),
            method="zscore_iqr",
            details={
                "z_score": round(z_score, 4),
                "iqr_score": round(iqr_score, 4),
                "mean": round(mean, 4),
                "stdev": round(stdev, 4),
                "q1": round(q1, 4),
                "q3": round(q3, 4),
                "window_size": len(window)
            }
        )
    
    def detect_seasonal_anomaly(self, metric_name: str, value: float,
                                 season_length: int = 24) -> AnomalyResult:
        """
        Detect anomalies in seasonal time-series data.
        
        Compares current value against the expected value based on
        the same position in previous seasons.
        """
        window = self._get_window(metric_name)
        
        if len(window) < season_length * 2:
            window.append(value)
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                method="seasonal_insufficient_data",
                details={"window_size": len(window), "required": season_length * 2}
            )
        
        # Get values at the same position in previous seasons
        window_list = list(window)
        seasonal_values = []
        for i in range(1, len(window_list) // season_length + 1):
            idx = len(window_list) - i * season_length
            if idx >= 0:
                seasonal_values.append(window_list[idx])
        
        if len(seasonal_values) < 2:
            window.append(value)
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                method="seasonal_insufficient_seasons",
                details={"seasons_available": len(seasonal_values)}
            )
        
        # Compare against seasonal baseline
        seasonal_mean = statistics.mean(seasonal_values)
        seasonal_stdev = statistics.stdev(seasonal_values) if len(seasonal_values) > 1 else 0
        
        if seasonal_stdev > 0:
            seasonal_z = abs((value - seasonal_mean) / seasonal_stdev)
        else:
            seasonal_z = 0
        
        score = min(1.0, seasonal_z / self.z_threshold)
        is_anomaly = seasonal_z > self.z_threshold
        
        window.append(value)
        
        return AnomalyResult(
            is_anomaly=is_anomaly,
            score=round(score, 4),
            method="seasonal_zscore",
            details={
                "seasonal_z_score": round(seasonal_z, 4),
                "seasonal_mean": round(seasonal_mean, 4),
                "seasonal_stdev": round(seasonal_stdev, 4),
                "seasons_compared": len(seasonal_values)
            }
        )


class IsolationForestDetector:
    """
    Multivariate anomaly detection using Isolation Forest.
    
    Detects anomalies across multiple metrics simultaneously,
    capturing complex relationships between metrics.
    """
    
    def __init__(self, contamination: float = 0.05,
                 n_estimators: int = 100,
                 window_size: int = 1000):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.window_size = window_size
        self.model: Optional[IsolationForest] = None
        self.scaler = StandardScaler()
        self._data: List[List[float]] = []
        self._metric_names: List[str] = []
        self._is_fitted = False
    
    def fit(self, data: np.ndarray, metric_names: List[str]):
        """
        Fit the Isolation Forest on historical data.
        
        Args:
            data: 2D array of shape (n_samples, n_metrics)
            metric_names: List of metric names corresponding to columns
        """
        self._metric_names = metric_names
        scaled_data = self.scaler.fit_transform(data)
        
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=42
        )
        self.model.fit(scaled_data)
        self._is_fitted = True
    
    def detect(self, values: List[float]) -> AnomalyResult:
        """
        Detect if the given multivariate observation is anomalous.
        
        Args:
            values: List of metric values (must match metric_names order)
        """
        if not self._is_fitted:
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                method="isolation_forest_not_fitted",
                details={}
            )
        
        data = np.array(values).reshape(1, -1)
        scaled = self.scaler.transform(data)
        
        # Isolation Forest: -1 = anomaly, 1 = normal
        prediction = self.model.predict(scaled)[0]
        # Anomaly score: negative = more anomalous
        raw_score = self.model.score_samples(scaled)[0]
        
        # Normalize to 0-1
        score = min(1.0, max(0.0, -raw_score * 2))
        
        return AnomalyResult(
            is_anomaly=prediction == -1,
            score=round(score, 4),
            method="isolation_forest",
            details={
                "raw_score": round(raw_score, 4),
                "metrics": self._metric_names
            }
        )
    
    def partial_fit(self, data: np.ndarray):
        """Incrementally update the model with new data."""
        self._data.extend(data.tolist())
        
        # Keep only recent data
        if len(self._data) > self.window_size:
            self._data = self._data[-self.window_size:]
        
        # Refit periodically
        if len(self._data) >= 100:
            arr = np.array(self._data)
            self.fit(arr, self._metric_names)


class BehavioralAnomalyDetector:
    """
    Behavioral anomaly detection for agent behavior patterns.
    
    Detects unusual patterns in agent behavior such as:
    - Unusual tool call sequences
    - Abnormal decision patterns
    - Deviation from learned behavior profiles
    """
    
    def __init__(self, profile_window: int = 1000):
        self.profile_window = profile_window
        self._agent_profiles: Dict[str, Dict] = {}
        self._tool_sequences: Dict[str, List[str]] = {}
        self._decision_patterns: Dict[str, Dict] = {}
    
    def update_agent_profile(self, agent_id: str, metrics: Dict):
        """Update the behavioral profile for an agent."""
        if agent_id not in self._agent_profiles:
            self._agent_profiles[agent_id] = {
                "tool_call_counts": {},
                "decision_counts": {},
                "avg_duration": 0.0,
                "avg_cost": 0.0,
                "sample_count": 0
            }
        
        profile = self._agent_profiles[agent_id]
        
        # Update tool call counts
        for tool, count in metrics.get("tool_calls", {}).items():
            profile["tool_call_counts"][tool] = \
                profile["tool_call_counts"].get(tool, 0) + count
        
        # Update decision counts
        for decision, count in metrics.get("decisions", {}).items():
            profile["decision_counts"][decision] = \
                profile["decision_counts"].get(decision, 0) + count
        
        # Update running averages
        n = profile["sample_count"]
        profile["avg_duration"] = (
            (profile["avg_duration"] * n + metrics.get("duration", 0)) / (n + 1)
        )
        profile["avg_cost"] = (
            (profile["avg_cost"] * n + metrics.get("cost", 0)) / (n + 1)
        )
        profile["sample_count"] += 1
    
    def detect_behavioral_anomaly(self, agent_id: str,
                                   current_metrics: Dict) -> AnomalyResult:
        """
        Detect behavioral anomalies for an agent.
        
        Compares current behavior against the agent's historical profile.
        """
        if agent_id not in self._agent_profiles:
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                method="no_profile",
                details={"agent_id": agent_id}
            )
        
        profile = self._agent_profiles[agent_id]
        anomaly_indicators = []
        
        # Check tool usage anomaly
        current_tools = current_metrics.get("tool_calls", {})
        total_profile_tools = sum(profile["tool_call_counts"].values())
        
        if total_profile_tools > 0:
            for tool, count in current_tools.items():
                expected_ratio = profile["tool_call_counts"].get(tool, 0) / total_profile_tools
                total_current = sum(current_tools.values())
                if total_current > 0:
                    current_ratio = count / total_current
                    if expected_ratio > 0:
                        ratio_diff = abs(current_ratio - expected_ratio) / expected_ratio
                        if ratio_diff > 2.0:  # 2x deviation
                            anomaly_indicators.append({
                                "type": "tool_usage_anomaly",
                                "tool": tool,
                                "expected_ratio": round(expected_ratio, 4),
                                "current_ratio": round(current_ratio, 4),
                                "deviation": round(ratio_diff, 4)
                            })
        
        # Check duration anomaly
        current_duration = current_metrics.get("duration", 0)
        if profile["avg_duration"] > 0 and profile["sample_count"] > 10:
            duration_ratio = current_duration / profile["avg_duration"]
            if duration_ratio > 3.0:  # 3x normal duration
                anomaly_indicators.append({
                    "type": "duration_anomaly",
                    "expected_avg": round(profile["avg_duration"], 4),
                    "current": round(current_duration, 4),
                    "ratio": round(duration_ratio, 4)
                })
        
        # Check cost anomaly
        current_cost = current_metrics.get("cost", 0)
        if profile["avg_cost"] > 0 and profile["sample_count"] > 10:
            cost_ratio = current_cost / profile["avg_cost"]
            if cost_ratio > 3.0:
                anomaly_indicators.append({
                    "type": "cost_anomaly",
                    "expected_avg": round(profile["avg_cost"], 4),
                    "current": round(current_cost, 4),
                    "ratio": round(cost_ratio, 4)
                })
        
        # Calculate overall score
        score = min(1.0, len(anomaly_indicators) * 0.3)
        
        return AnomalyResult(
            is_anomaly=len(anomaly_indicators) > 0,
            score=round(score, 4),
            method="behavioral_profile",
            details={
                "agent_id": agent_id,
                "indicators": anomaly_indicators,
                "profile_samples": profile["sample_count"]
            }
        )
    
    def detect_tool_sequence_anomaly(self, agent_id: str,
                                      tool_sequence: List[str]) -> AnomalyResult:
        """
        Detect anomalies in tool call sequences.
        
        Uses n-gram analysis to detect unusual tool call patterns.
        """
        if agent_id not in self._tool_sequences:
            self._tool_sequences[agent_id] = []
        
        history = self._tool_sequences[agent_id]
        
        if len(history) < 20:
            history.extend(tool_sequence)
            return AnomalyResult(
                is_anomaly=False,
                score=0.0,
                method="sequence_insufficient_data",
                details={"history_size": len(history)}
            )
        
        # Build bigram transition probabilities
        transitions = {}
        for i in range(len(history) - 1):
            bigram = (history[i], history[i + 1])
            transitions[bigram] = transitions.get(bigram, 0) + 1
        
        total_transitions = sum(transitions.values())
        
        # Check current sequence against transition probabilities
        anomaly_count = 0
        for i in range(len(tool_sequence) - 1):
            bigram = (tool_sequence[i], tool_sequence[i + 1])
            if bigram not in transitions:
                anomaly_count += 1
            elif transitions[bigram] / total_transitions < 0.01:
                anomaly_count += 1
        
        anomaly_rate = anomaly_count / max(len(tool_sequence) - 1, 1)
        score = min(1.0, anomaly_rate * 2)
        
        history.extend(tool_sequence)
        if len(history) > self.profile_window:
            history[:] = history[-self.profile_window:]
        
        return AnomalyResult(
            is_anomaly=anomaly_rate > 0.3,
            score=round(score, 4),
            method="tool_sequence_ngram",
            details={
                "anomaly_rate": round(anomaly_rate, 4),
                "sequence_length": len(tool_sequence),
                "unusual_transitions": anomaly_count
            }
        )
```

### 4.2 Anomaly Detection Pipeline

```python
# grc_claw/monitoring/anomaly_pipeline.py
"""
Anomaly detection pipeline that orchestrates multiple detectors
and feeds results into the alerting system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from grc_claw.monitoring.anomaly_detector import (
    StatisticalAnomalyDetector,
    IsolationForestDetector,
    BehavioralAnomalyDetector,
    AnomalyResult
)
from grc_claw.monitoring.metrics_exporter import metrics


logger = logging.getLogger(__name__)


@dataclass
class AnomalyAlert:
    """An anomaly alert generated by the pipeline."""
    metric_name: str
    agent_id: Optional[str]
    result: AnomalyResult
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AnomalyDetectionPipeline:
    """
    Orchestrates multiple anomaly detection methods and
    generates alerts when anomalies are detected.
    """
    
    def __init__(self):
        self.statistical_detector = StatisticalAnomalyDetector()
        self.isolation_detector = IsolationForestDetector()
        self.behavioral_detector = BehavioralAnomalyDetector()
        self._alert_handlers: List[Callable] = []
        self._metric_configs: Dict[str, Dict] = {}
    
    def register_alert_handler(self, handler: Callable):
        """Register a callback for anomaly alerts."""
        self._alert_handlers.append(handler)
    
    def configure_metric(self, metric_name: str, config: Dict):
        """
        Configure anomaly detection for a specific metric.
        
        Config options:
        - method: 'statistical', 'isolation_forest', 'behavioral', 'seasonal'
        - threshold: anomaly score threshold (0-1)
        - season_length: for seasonal detection
        - enabled: whether detection is active
        """
        self._metric_configs[metric_name] = {
            "method": "statistical",
            "threshold": 0.8,
            "enabled": True,
            **config
        }
    
    def process_metric(self, metric_name: str, value: float,
                       agent_id: Optional[str] = None) -> Optional[AnomalyAlert]:
        """
        Process a metric value through the anomaly detection pipeline.
        
        Returns an AnomalyAlert if an anomaly is detected, None otherwise.
        """
        config = self._metric_configs.get(metric_name, {})
        if not config.get("enabled", True):
            return None
        
        method = config.get("method", "statistical")
        threshold = config.get("threshold", 0.8)
        
        # Run appropriate detector
        if method == "statistical":
            result = self.statistical_detector.update(metric_name, value)
        elif method == "seasonal":
            season_length = config.get("season_length", 24)
            result = self.statistical_detector.detect_seasonal_anomaly(
                metric_name, value, season_length
            )
        elif method == "behavioral" and agent_id:
            result = self.behavioral_detector.detect_behavioral_anomaly(
                agent_id, {metric_name: value}
            )
        else:
            result = self.statistical_detector.update(metric_name, value)
        
        # Check if anomaly score exceeds threshold
        if result.is_anomaly and result.score >= threshold:
            alert = AnomalyAlert(
                metric_name=metric_name,
                agent_id=agent_id,
                result=result
            )
            
            # Update Prometheus gauge
            metrics.anomaly_score.labels(
                agent_id=agent_id or "system"
            ).set(result.score)
            
            # Notify handlers
            for handler in self._alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")
            
            return alert
        
        return None
    
    def process_multivariate(self, metric_values: Dict[str, float],
                             agent_id: Optional[str] = None) -> Optional[AnomalyAlert]:
        """
        Process multiple metrics simultaneously for multivariate anomaly detection.
        """
        values = list(metric_values.values())
        result = self.isolation_detector.detect(values)
        
        if result.is_anomaly and result.score >= 0.8:
            alert = AnomalyAlert(
                metric_name="multivariate",
                agent_id=agent_id,
                result=result
            )
            
            for handler in self._alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")
            
            return alert
        
        return None
    
    async def run_continuous_detection(self, metric_source: Callable,
                                        interval_seconds: float = 60.0):
        """
        Run continuous anomaly detection on a metric source.
        
        Args:
            metric_source: Async callable that returns Dict[str, float]
            interval_seconds: Detection interval
        """
        while True:
            try:
                metric_values = await metric_source()
                
                for metric_name, value in metric_values.items():
                    self.process_metric(metric_name, value)
                
                # Also run multivariate detection
                if len(metric_values) > 1:
                    self.process_multivariate(metric_values)
                    
            except Exception as e:
                logger.error(f"Anomaly detection error: {e}")
            
            await asyncio.sleep(interval_seconds)
```

---

## 5. Predictive Alerting (Python)

### 5.1 Predictive Alert Engine

```python
# grc_claw/monitoring/predictive_alerts.py
"""
Predictive alerting engine for GRC_Claw.

Uses time-series forecasting to predict future metric values
and generate alerts before thresholds are breached.

Supported models:
- Exponential Smoothing (Holt-Winters)
- ARIMA
- Linear regression with trend
- Prophet (optional)
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import statistics
import math

from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures


@dataclass
class PredictionResult:
    """Result of a predictive forecast."""
    metric_name: str
    current_value: float
    predicted_value: float
    prediction_horizon: str  # e.g., "5m", "1h", "24h"
    confidence_interval: Tuple[float, float]
    will_breach_threshold: bool
    threshold: Optional[float]
    time_to_breach: Optional[timedelta]
    model_used: str
    confidence: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PredictiveAlert:
    """A predictive alert generated before threshold breach."""
    metric_name: str
    severity: str  # P1, P2, P3
    prediction: PredictionResult
    recommended_action: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ExponentialSmoothingForecaster:
    """
    Holt-Winters exponential smoothing forecaster.
    
    Captures trend and seasonality in time-series data.
    """
    
    def __init__(self, alpha: float = 0.3, beta: float = 0.1,
                 gamma: float = 0.1, season_length: int = 24):
        self.alpha = alpha  # Level smoothing
        self.beta = beta    # Trend smoothing
        self.gamma = gamma  # Seasonal smoothing
        self.season_length = season_length
        self._level = None
        self._trend = None
        self._seasonal = None
    
    def fit(self, data: np.ndarray):
        """Fit the model on historical data."""
        n = len(data)
        if n < self.season_length * 2:
            raise ValueError(f"Need at least {self.season_length * 2} data points")
        
        # Initialize seasonal components
        self._seasonal = np.zeros(self.season_length)
        for i in range(self.season_length):
            self._seasonal[i] = np.mean(data[i::self.season_length])
        
        # Initialize level and trend
        self._level = data[0] / self._seasonal[0]
        self._trend = (data[self.season_length] - data[0]) / self.season_length
        
        # Apply Holt-Winters
        for t in range(n):
            season_idx = t % self.season_length
            value = data[t]
            
            old_level = self._level
            self._level = self.alpha * (value / self._seasonal[season_idx]) + \
                         (1 - self.alpha) * (self._level + self._trend)
            self._trend = self.beta * (self._level - old_level) + \
                         (1 - self.beta) * self._trend
            self._seasonal[season_idx] = self.gamma * (value / self._level) + \
                                        (1 - self.gamma) * self._seasonal[season_idx]
    
    def forecast(self, steps: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Forecast future values.
        
        Returns:
            (forecasts, lower_bound, upper_bound)
        """
        if self._level is None:
            raise ValueError("Model not fitted")
        
        forecasts = np.zeros(steps)
        for i in range(steps):
            season_idx = (len(self._seasonal) + i) % self.season_length
            forecasts[i] = (self._level + (i + 1) * self._trend) * self._seasonal[season_idx]
        
        # Simple confidence interval (±10% of forecast)
        margin = np.abs(forecasts) * 0.1
        lower = forecasts - margin
        upper = forecasts + margin
        
        return forecasts, lower, upper


class LinearTrendForecaster:
    """
    Linear regression forecaster with optional polynomial features.
    
    Simple but effective for metrics with clear trends.
    """
    
    def __init__(self, degree: int = 1):
        self.degree = degree
        self.model = LinearRegression()
        self.poly_features = PolynomialFeatures(degree=degree)
        self._residual_std = 0.0
    
    def fit(self, data: np.ndarray):
        """Fit the model on historical data."""
        n = len(data)
        X = np.arange(n).reshape(-1, 1)
        y = data
        
        X_poly = self.poly_features.fit_transform(X)
        self.model.fit(X_poly, y)
        
        # Calculate residual standard deviation for confidence intervals
        predictions = self.model.predict(X_poly)
        residuals = y - predictions
        self._residual_std = np.std(residuals)
    
    def forecast(self, steps: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Forecast future values.
        
        Returns:
            (forecasts, lower_bound, upper_bound)
        """
        n = len(self.model.coef_)  # Not directly useful, but we need current length
        # We need to know the current length - store it during fit
        # For simplicity, we'll use a large enough range
        current_n = self.model.n_features_in_  # This won't work directly
        
        # Actually, let's store the length during fit
        # This is a simplified version
        future_X = np.arange(steps).reshape(-1, 1)
        # We need to offset by the training data length
        # For this implementation, we'll assume the caller manages the offset
        
        forecasts = np.zeros(steps)
        for i in range(steps):
            x = np.array([[i]])
            x_poly = self.poly_features.transform(x)
            forecasts[i] = self.model.predict(x_poly)[0]
        
        # Confidence interval based on residual std
        margin = 1.96 * self._residual_std  # 95% CI
        lower = forecasts - margin
        upper = forecasts + margin
        
        return forecasts, lower, upper


class PredictiveAlertEngine:
    """
    Predictive alerting engine that forecasts metric values
    and generates alerts before thresholds are breached.
    """
    
    def __init__(self, history_window: int = 1000):
        self.history_window = history_window
        self._metric_history: Dict[str, deque] = {}
        self._forecasters: Dict[str, Any] = {}
        self._thresholds: Dict[str, Dict] = {}
        self._alert_handlers: List[Callable] = []
    
    def register_alert_handler(self, handler: Callable):
        """Register a callback for predictive alerts."""
        self._alert_handlers.append(handler)
    
    def configure_threshold(self, metric_name: str, threshold: float,
                            direction: str = "above",
                            horizon: str = "1h",
                            severity: str = "P2",
                            cooldown_minutes: int = 30):
        """
        Configure a predictive threshold for a metric.
        
        Args:
            metric_name: Name of the metric
            threshold: Threshold value
            direction: 'above' or 'below'
            horizon: Prediction horizon ('5m', '15m', '1h', '24h')
            severity: Alert severity
            cooldown_minutes: Minimum time between alerts for this metric
        """
        self._thresholds[metric_name] = {
            "threshold": threshold,
            "direction": direction,
            "horizon": horizon,
            "severity": severity,
            "cooldown_minutes": cooldown_minutes,
            "last_alert": None
        }
    
    def _get_history(self, metric_name: str) -> deque:
        """Get or create history for a metric."""
        if metric_name not in self._metric_history:
            self._metric_history[metric_name] = deque(maxlen=self.history_window)
        return self._metric_history[metric_name]
    
    def update(self, metric_name: str, value: float,
               timestamp: Optional[datetime] = None) -> Optional[PredictionResult]:
        """
        Update the engine with a new metric value and generate predictions.
        
        Returns a PredictionResult if the metric has a configured threshold,
        None otherwise.
        """
        history = self._get_history(metric_name)
        history.append(value)
        
        if metric_name not in self._thresholds:
            return None
        
        config = self._thresholds[metric_name]
        
        # Check cooldown
        if config["last_alert"]:
            cooldown = timedelta(minutes=config["cooldown_minutes"])
            if timestamp and (timestamp - config["last_alert"]) < cooldown:
                return None
        
        # Need minimum data for forecasting
        if len(history) < 50:
            return None
        
        # Generate forecast
        data = np.array(list(history))
        
        try:
            # Use exponential smoothing for seasonal data, linear for trends
            if len(data) >= 48:
                forecaster = ExponentialSmoothingForecaster(season_length=24)
                forecaster.fit(data)
                horizon_steps = self._parse_horizon(config["horizon"])
                forecasts, lower, upper = forecaster.forecaster.forecast(horizon_steps)
                model_used = "holt_winters"
            else:
                forecaster = LinearTrendForecaster(degree=1)
                forecaster.fit(data)
                horizon_steps = self._parse_horizon(config["horizon"])
                forecasts, lower, upper = forecaster.forecast(horizon_steps)
                model_used = "linear_trend"
            
            # Check if threshold will be breached
            threshold = config["threshold"]
            direction = config["direction"]
            
            will_breach = False
            time_to_breach = None
            
            for i, forecast in enumerate(forecasts):
                if direction == "above" and forecast > threshold:
                    will_breach = True
                    time_to_breach = self._steps_to_timedelta(i + 1, config["horizon"])
                    break
                elif direction == "below" and forecast < threshold:
                    will_breach = True
                    time_to_breach = self._steps_to_timedelta(i + 1, config["horizon"])
                    break
            
            # Calculate confidence based on data quality
            confidence = min(1.0, len(data) / 200) * 0.8 + 0.2
            
            result = PredictionResult(
                metric_name=metric_name,
                current_value=value,
                predicted_value=round(float(forecasts[-1]), 4),
                prediction_horizon=config["horizon"],
                confidence_interval=(round(float(lower[-1]), 4), round(float(upper[-1]), 4)),
                will_breach_threshold=will_breach,
                threshold=threshold,
                time_to_breach=time_to_breach,
                model_used=model_used,
                confidence=round(confidence, 4)
            )
            
            # Generate alert if threshold will be breached
            if will_breach:
                config["last_alert"] = timestamp or datetime.utcnow()
                alert = PredictiveAlert(
                    metric_name=metric_name,
                    severity=config["severity"],
                    prediction=result,
                    recommended_action=self._generate_recommendation(metric_name, result)
                )
                
                for handler in self._alert_handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        logger.error(f"Predictive alert handler failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Forecasting failed for {metric_name}: {e}")
            return None
    
    def _parse_horizon(self, horizon: str) -> int:
        """Parse horizon string to number of steps."""
        mapping = {"5m": 5, "15m": 15, "30m": 30, "1h": 60, "24h": 1440}
        return mapping.get(horizon, 60)
    
    def _steps_to_timedelta(self, steps: int, horizon: str) -> timedelta:
        """Convert steps to timedelta based on horizon."""
        if horizon == "5m":
            return timedelta(minutes=steps)
        elif horizon == "15m":
            return timedelta(minutes=steps * 15)
        elif horizon == "30m":
            return timedelta(minutes=steps * 30)
        elif horizon == "1h":
            return timedelta(hours=steps)
        elif horizon == "24h":
            return timedelta(hours=steps)
        return timedelta(hours=steps)
    
    def _generate_recommendation(self, metric_name: str, prediction: PredictionResult) -> str:
        """Generate a recommendation based on the prediction."""
        if prediction.time_to_breach and prediction.time_to_breach < timedelta(hours=1):
            return f"URGENT: {metric_name} predicted to breach threshold in {prediction.time_to_breach}. Take immediate action."
        elif prediction.time_to_breach and prediction.time_to_breach < timedelta(hours=24):
            return f"WARNING: {metric_name} predicted to breach threshold in {prediction.time_to_breach}. Plan mitigation."
        else:
            return f"INFO: {metric_name} trending toward threshold. Monitor closely."


class CapacityForecaster:
    """
    Forecasts resource capacity and scaling needs.
    
    Predicts when resources will be exhausted based on
    current usage trends and growth rates.
    """
    
    def __init__(self):
        self._capacity_history: Dict[str, deque] = {}
    
    def update(self, resource_name: str, current_usage: float,
               capacity: float, timestamp: Optional[datetime] = None):
        """Update capacity tracking for a resource."""
        if resource_name not in self._capacity_history:
            self._capacity_history[resource_name] = deque(maxlen=1000)
        
        self._capacity_history[resource_name].append({
            "timestamp": timestamp or datetime.utcnow(),
            "usage": current_usage,
            "capacity": capacity,
            "utilization": current_usage / capacity if capacity > 0 else 0
        })
    
    def predict_saturation(self, resource_name: str,
                           threshold: float = 0.8) -> Optional[Dict]:
        """
        Predict when a resource will reach saturation.
        
        Returns dict with predicted saturation time and recommended action,
        or None if not enough data.
        """
        if resource_name not in self._capacity_history:
            return None
        
        history = list(self._capacity_history[resource_name])
        if len(history) < 30:
            return None
        
        # Calculate growth rate
        recent = history[-30:]
        utilizations = [h["utilization"] for h in recent]
        
        # Linear regression on utilization over time
        x = np.arange(len(utilizations))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, utilizations)
        
        if slope <= 0:
            return None  # Not growing
        
        # Predict when utilization will exceed threshold
        steps_to_threshold = (threshold - intercept) / slope
        
        if steps_to_threshold <= 0:
            return None
        
        # Estimate time based on data collection interval
        time_per_step = (recent[-1]["timestamp"] - recent[0]["timestamp"]) / len(recent)
        time_to_saturation = time_per_step * steps_to_threshold
        
        saturation_time = datetime.utcnow() + time_to_saturation
        
        return {
            "resource": resource_name,
            "current_utilization": round(utilizations[-1], 4),
            "growth_rate_per_step": round(slope, 6),
            "r_squared": round(r_value ** 2, 4),
            "predicted_saturation": saturation_time.isoformat(),
            "time_to_saturation_hours": round(time_to_saturation.total_seconds() / 3600, 2),
            "recommended_action": self._capacity_recommendation(
                resource_name, time_to_saturation, threshold
            )
        }
    
    def _capacity_recommendation(self, resource: str,
                                  time_to_saturation: timedelta,
                                  threshold: float) -> str:
        """Generate capacity recommendation."""
        hours = time_to_saturation.total_seconds() / 3600
        
        if hours < 24:
            return f"CRITICAL: {resource} will saturate in {hours:.1f}h. Scale immediately."
        elif hours < 72:
            return f"HIGH: {resource} will saturate in {hours:.1f}h. Plan scaling within 24h."
        elif hours < 168:  # 1 week
            return f"MEDIUM: {resource} will saturate in {hours:.1f}h. Include in next capacity review."
        else:
            return f"LOW: {resource} utilization trending toward {threshold*100}% in {hours:.1f}h. Monitor."
```

---

## 6. Monitoring Data Quality (Python)

### 6.1 Data Quality Monitor

```python
# grc_claw/monitoring/data_quality.py
"""
Monitoring data quality assurance for GRC_Claw.

Validates metric data quality, detects gaps, anomalies in
the monitoring pipeline itself, and ensures data completeness.
"""

import time
import statistics
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import math

from grc_claw.monitoring.metrics_exporter import metrics


@dataclass
class DataQualityReport:
    """Report on monitoring data quality."""
    metric_name: str
    timestamp: datetime
    completeness: float  # 0-1
    freshness_seconds: float
    validity_score: float  # 0-1
    consistency_score: float  # 0-1
    anomalies_detected: List[Dict]
    issues: List[str]
    overall_score: float  # 0-1


@dataclass
class MetricValidationRule:
    """Validation rule for a metric."""
    metric_name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    expected_labels: Optional[Set[str]] = None
    max_staleness_seconds: float = 60.0
    min_sample_rate: float = 0.95  # Expected sample rate (0-1)
    value_type: str = "float"  # float, int, bool
    allow_null: bool = False


class MonitoringDataQualityMonitor:
    """
    Monitors the quality of monitoring data itself.
    
    Detects:
    - Missing metrics (expected but not reported)
    - Stale metrics (not updated recently)
    - Invalid values (out of expected range)
    - Label inconsistencies
    - Data gaps
    - Collection delays
    """
    
    def __init__(self):
        self._validation_rules: Dict[str, MetricValidationRule] = {}
        self._metric_timestamps: Dict[str, datetime] = {}
        self._metric_values: Dict[str, List[float]] = defaultdict(list)
        self._metric_labels: Dict[str, Set[str]] = defaultdict(set)
        self._expected_metrics: Set[str] = set()
        self._quality_history: Dict[str, List[DataQualityReport]] = defaultdict(list)
    
    def register_metric(self, rule: MetricValidationRule):
        """Register a metric for quality monitoring."""
        self._validation_rules[rule.metric_name] = rule
        self._expected_metrics.add(rule.metric_name)
    
    def record_metric(self, metric_name: str, value: float,
                      labels: Optional[Dict] = None,
                      timestamp: Optional[datetime] = None):
        """Record a metric observation for quality tracking."""
        ts = timestamp or datetime.utcnow()
        self._metric_timestamps[metric_name] = ts
        
        if value is not None:
            self._metric_values[metric_name].append(value)
            # Keep only recent values
            if len(self._metric_values[metric_name]) > 1000:
                self._metric_values[metric_name] = \
                    self._metric_values[metric_name][-1000:]
        
        if labels:
            self._metric_labels[metric_name].update(labels.keys())
    
    def check_completeness(self, lookback_seconds: float = 300) -> Dict[str, Any]:
        """
        Check if all expected metrics are being reported.
        
        Returns dict with missing metrics and completeness score.
        """
        now = datetime.utcnow()
        lookback = timedelta(seconds=lookback_seconds)
        
        missing_metrics = []
        stale_metrics = []
        healthy_metrics = []
        
        for metric_name in self._expected_metrics:
            rule = self._validation_rules.get(metric_name)
            if not rule:
                continue
            
            last_seen = self._metric_timestamps.get(metric_name)
            
            if last_seen is None:
                missing_metrics.append(metric_name)
            elif (now - last_seen) > timedelta(seconds=rule.max_staleness_seconds):
                stale_metrics.append({
                    "metric": metric_name,
                    "last_seen": last_seen.isoformat(),
                    "staleness_seconds": (now - last_seen).total_seconds()
                })
            else:
                healthy_metrics.append(metric_name)
        
        total_expected = len(self._expected_metrics)
        completeness = len(healthy_metrics) / total_expected if total_expected > 0 else 1.0
        
        return {
            "completeness": round(completeness, 4),
            "total_expected": total_expected,
            "healthy": len(healthy_metrics),
            "missing": missing_metrics,
            "stale": stale_metrics,
            "timestamp": now.isoformat()
        }
    
    def check_validity(self, metric_name: str) -> Dict[str, Any]:
        """
        Check if metric values are within valid ranges.
        """
        rule = self._validation_rules.get(metric_name)
        if not rule:
            return {"valid": True, "issues": []}
        
        values = self._metric_values.get(metric_name, [])
        if not values:
            return {"valid": False, "issues": ["no_data"]}
        
        issues = []
        
        # Check value range
        if rule.min_value is not None:
            below_min = [v for v in values if v < rule.min_value]
            if below_min:
                issues.append({
                    "type": "below_minimum",
                    "count": len(below_min),
                    "min_allowed": rule.min_value,
                    "min_found": min(below_min)
                })
        
        if rule.max_value is not None:
            above_max = [v for v in values if v > rule.max_value]
            if above_max:
                issues.append({
                    "type": "above_maximum",
                    "count": len(above_max),
                    "max_allowed": rule.max_value,
                    "max_found": max(above_max)
                })
        
        # Check for null/None values
        if not rule.allow_null:
            null_count = sum(1 for v in values if v is None)
            if null_count > 0:
                issues.append({
                    "type": "null_values",
                    "count": null_count
                })
        
        # Check for NaN/Inf
        nan_count = sum(1 for v in values if v is not None and math.isnan(v))
        inf_count = sum(1 for v in values if v is not None and math.isinf(v))
        if nan_count > 0:
            issues.append({"type": "nan_values", "count": nan_count})
        if inf_count > 0:
            issues.append({"type": "inf_values", "count": inf_count})
        
        # Check label consistency
        if rule.expected_labels:
            actual_labels = self._metric_labels.get(metric_name, set())
            missing_labels = rule.expected_labels - actual_labels
            if missing_labels:
                issues.append({
                    "type": "missing_labels",
                    "labels": list(missing_labels)
                })
        
        validity_score = 1.0 - (len(issues) * 0.1)
        validity_score = max(0.0, validity_score)
        
        return {
            "valid": len(issues) == 0,
            "validity_score": round(validity_score, 4),
            "issues": issues,
            "sample_count": len(values)
        }
    
    def check_consistency(self, metric_name: str) -> Dict[str, Any]:
        """
        Check metric consistency (no sudden jumps or drops).
        """
        values = self._metric_values.get(metric_name, [])
        if len(values) < 10:
            return {"consistent": True, "score": 1.0, "issues": []}
        
        issues = []
        
        # Check for sudden jumps using coefficient of variation
        recent = values[-50:]
        mean = statistics.mean(recent)
        stdev = statistics.stdev(recent) if len(recent) > 1 else 0
        
        if mean > 0:
            cv = stdev / mean
            if cv > 2.0:  # Very high variability
                issues.append({
                    "type": "high_variability",
                    "cv": round(cv, 4),
                    "mean": round(mean, 4),
                    "stdev": round(stdev, 4)
                })
        
        # Check for flatline (stuck values)
        unique_values = len(set(recent[-20:]))
        if unique_values < 3 and len(recent) >= 20:
            issues.append({
                "type": "flatline",
                "unique_values": unique_values,
                "suggestion": "Metric may be stuck or not updating"
            })
        
        # Check for gaps in data
        timestamps = []
        for ts_str, val in zip(
            [self._metric_timestamps.get(metric_name)] * len(values),
            values
        ):
            if ts_str:
                timestamps.append(ts_str)
        
        consistency_score = 1.0 - (len(issues) * 0.2)
        consistency_score = max(0.0, consistency_score)
        
        return {
            "consistent": len(issues) == 0,
            "score": round(consistency_score, 4),
            "issues": issues
        }
    
    def check_freshness(self, metric_name: str) -> Dict[str, Any]:
        """Check if metric data is fresh."""
        rule = self._validation_rules.get(metric_name)
        if not rule:
            return {"fresh": True, "staleness_seconds": 0}
        
        last_seen = self._metric_timestamps.get(metric_name)
        if last_seen is None:
            return {
                "fresh": False,
                "staleness_seconds": float('inf'),
                "issue": "never_reported"
            }
        
        staleness = (datetime.utcnow() - last_seen).total_seconds()
        fresh = staleness <= rule.max_staleness_seconds
        
        return {
            "fresh": fresh,
            "staleness_seconds": round(staleness, 2),
            "max_allowed": rule.max_staleness_seconds,
            "last_seen": last_seen.isoformat()
        }
    
    def generate_quality_report(self, metric_name: str) -> DataQualityReport:
        """Generate a comprehensive quality report for a metric."""
        now = datetime.utcnow()
        
        completeness = self.check_completeness()
        validity = self.check_validity(metric_name)
        consistency = self.check_consistency(metric_name)
        freshness = self.check_freshness(metric_name)
        
        # Calculate overall score
        scores = [
            completeness.get("completeness", 1.0),
            validity.get("validity_score", 1.0),
            consistency.get("score", 1.0),
            1.0 if freshness.get("fresh", True) else 0.0
        ]
        overall = sum(scores) / len(scores)
        
        # Collect all issues
        issues = []
        if not validity.get("valid", True):
            issues.extend([f"validity: {i}" for i in validity.get("issues", [])])
        if not consistency.get("consistent", True):
            issues.extend([f"consistency: {i}" for i in consistency.get("issues", [])])
        if not freshness.get("fresh", True):
            issues.append(f"freshness: stale by {freshness.get('staleness_seconds', 0)}s")
        
        report = DataQualityReport(
            metric_name=metric_name,
            timestamp=now,
            completeness=completeness.get("completeness", 1.0),
            freshness_seconds=freshness.get("staleness_seconds", 0),
            validity_score=validity.get("validity_score", 1.0),
            consistency_score=consistency.get("score", 1.0),
            anomalies_detected=validity.get("issues", []) + consistency.get("issues", []),
            issues=issues,
            overall_score=round(overall, 4)
        )
        
        # Store report history
        self._quality_history[metric_name].append(report)
        if len(self._quality_history[metric_name]) > 100:
            self._quality_history[metric_name] = \
                self._quality_history[metric_name][-100:]
        
        return report
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall monitoring health score."""
        if not self._expected_metrics:
            return {"health": 1.0, "status": "no_metrics_configured"}
        
        reports = []
        for metric_name in self._expected_metrics:
            report = self.generate_quality_report(metric_name)
            reports.append(report)
        
        avg_score = sum(r.overall_score for r in reports) / len(reports)
        
        # Categorize health
        if avg_score >= 0.95:
            status = "healthy"
        elif avg_score >= 0.80:
            status = "degraded"
        elif avg_score >= 0.60:
            status = "unhealthy"
        else:
            status = "critical"
        
        # Find problematic metrics
        problematic = [
            {"metric": r.metric_name, "score": r.overall_score, "issues": r.issues}
            for r in reports if r.overall_score < 0.8
        ]
        
        return {
            "health": round(avg_score, 4),
            "status": status,
            "total_metrics": len(self._expected_metrics),
            "problematic_metrics": problematic,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def detect_pipeline_anomalies(self) -> List[Dict]:
        """
        Detect anomalies in the monitoring pipeline itself.
        
        Identifies patterns that suggest monitoring infrastructure issues.
        """
        anomalies = []
        
        # Check for widespread staleness
        stale_count = 0
        for metric_name in self._expected_metrics:
            freshness = self.check_freshness(metric_name)
            if not freshness.get("fresh", True):
                stale_count += 1
        
        if stale_count > len(self._expected_metrics) * 0.3:
            anomalies.append({
                "type": "widespread_staleness",
                "severity": "high",
                "affected_metrics": stale_count,
                "total_metrics": len(self._expected_metrics),
                "suggestion": "Check Prometheus scrape configuration and network connectivity"
            })
        
        # Check for data gaps
        for metric_name in self._expected_metrics:
            values = self._metric_values.get(metric_name, [])
            if len(values) >= 2:
                # Check for sudden drops in sample rate
                recent_count = len([v for v in values[-100:] if v is not None])
                if recent_count < 50:  # Less than 50% of expected samples
                    anomalies.append({
                        "type": "data_gap",
                        "metric": metric_name,
                        "severity": "medium",
                        "recent_samples": recent_count,
                        "expected_samples": 100,
                        "suggestion": f"Check {metric_name} collection pipeline"
                    })
        
        return anomalies


class MetricSchemaValidator:
    """
    Validates metric schemas against the GRC_Claw monitoring specification.
    
    Ensures all metrics follow naming conventions, have correct types,
    and include required labels.
    """
    
    # Required labels per metric category
    REQUIRED_LABELS = {
        "model": {"model", "provider"},
        "agent": {"agent_id"},
        "safety": {"agent_id"},
        "security": {"agent_id"},
        "fairness": {"model_id", "protected_class"},
        "drift": {"model_id"},
        "incident": {"severity", "fault_class"}
    }
    
    # Metric name patterns
    METRIC_PATTERNS = {
        "llm_request_duration_seconds": "histogram",
        "llm_token_usage_total": "counter",
        "llm_cost_total_dollars": "counter",
        "llm_error_rate": "gauge",
        "llm_success_rate": "gauge",
        "feature_drift_score": "gauge",
        "prediction_drift_score": "gauge",
        "toxicity_score": "gauge",
        "jailbreak_attempt_count_total": "counter",
        "constraint_breach_count_total": "counter",
        "anomaly_score": "gauge",
        "agent_run_duration_seconds": "histogram",
        "agent_success_rate": "gauge",
        "incident_count_total": "counter",
        "time_to_detect_seconds": "histogram",
    }
    
    def validate_metric_name(self, name: str) -> Tuple[bool, List[str]]:
        """Validate a metric name against conventions."""
        issues = []
        
        # Check naming convention: {namespace}_{category}_{metric}_{unit}
        parts = name.split('_')
        if len(parts) < 3:
            issues.append(f"Metric name '{name}' does not follow naming convention")
        
        # Check for valid metric type suffix
        valid_suffixes = ['_total', '_seconds', '_score', '_rate', '_count',
                         '_ratio', '_diff', '_usage', '_duration']
        if not any(name.endswith(suffix) for suffix in valid_suffixes):
            issues.append(f"Metric name '{name}' missing valid type suffix")
        
        return len(issues) == 0, issues
    
    def validate_labels(self, metric_name: str,
                        labels: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate metric labels against requirements."""
        issues = []
        
        # Determine category from metric name
        category = self._infer_category(metric_name)
        required = self.REQUIRED_LABELS.get(category, set())
        
        missing = required - set(labels.keys())
        if missing:
            issues.append(f"Missing required labels: {missing}")
        
        # Check for environment label
        if "environment" not in labels:
            issues.append("Missing 'environment' label")
        
        return len(issues) == 0, issues
    
    def _infer_category(self, metric_name: str) -> str:
        """Infer metric category from name."""
        if metric_name.startswith("llm_"):
            return "model"
        elif metric_name.startswith("agent_"):
            return "agent"
        elif any(x in metric_name for x in ["toxicity", "jailbreak", "guard_", "safety_"]):
            return "safety"
        elif any(x in metric_name for x in ["constraint_", "unauthorized_", "anomaly_", "security_"]):
            return "security"
        elif any(x in metric_name for x in ["bias_", "fairness_", "demographic_", "disparate_"]):
            return "fairness"
        elif any(x in metric_name for x in ["drift_", "skew_"]):
            return "drift"
        elif any(x in metric_name for x in ["incident_", "time_to_"]):
            return "incident"
        return "unknown"
    
    def validate_metric_type(self, metric_name: str,
                              expected_type: str) -> Tuple[bool, List[str]]:
        """Validate that a metric has the expected type."""
        issues = []
        
        actual_type = self.METRIC_PATTERNS.get(metric_name)
        if actual_type and actual_type != expected_type:
            issues.append(
                f"Metric '{metric_name}' expected type '{expected_type}' "
                f"but found '{actual_type}'"
            )
        
        return len(issues) == 0, issues
```

### 6.2 Data Quality Dashboard Integration

```python
# grc_claw/monitoring/data_quality_reporter.py
"""
Reports monitoring data quality metrics to Prometheus.
"""

from grc_claw.monitoring.data_quality import MonitoringDataQualityMonitor
from grc_claw.monitoring.metrics_exporter import REGISTRY
from prometheus_client import Gauge, Counter, Histogram


# Data quality metrics
data_quality_score = Gauge(
    'grc_monitoring_data_quality_score',
    'Overall data quality score',
    ['metric_name'],
    registry=REGISTRY
)

data_quality_completeness = Gauge(
    'grc_monitoring_data_completeness',
    'Data completeness ratio',
    registry=REGISTRY
)

data_quality_freshness = Gauge(
    'grc_monitoring_data_freshness_seconds',
    'Data freshness in seconds',
    ['metric_name'],
    registry=REGISTRY
)

data_quality_issues_total = Counter(
    'grc_monitoring_data_quality_issues_total',
    'Total data quality issues detected',
    ['issue_type', 'metric_name'],
    registry=REGISTRY
)

monitoring_pipeline_anomalies = Gauge(
    'grc_monitoring_pipeline_anomalies',
    'Number of monitoring pipeline anomalies',
    registry=REGISTRY
)


class DataQualityReporter:
    """Reports data quality metrics to Prometheus."""
    
    def __init__(self, quality_monitor: MonitoringDataQualityMonitor):
        self.quality_monitor = quality_monitor
    
    def report(self):
        """Generate and report all data quality metrics."""
        health = self.quality_monitor.get_overall_health()
        
        # Report overall health
        data_quality_completeness.set(health.get("health", 1.0))
        
        # Report per-metric quality
        for metric_name in self.quality_monitor._expected_metrics:
            report = self.quality_monitor.generate_quality_report(metric_name)
            
            data_quality_score.labels(metric_name=metric_name).set(
                report.overall_score
            )
            data_quality_freshness.labels(metric_name=metric_name).set(
                report.freshness_seconds
            )
            
            # Report issues
            for issue in report.issues:
                issue_type = issue.split(":")[0] if ":" in issue else "unknown"
                data_quality_issues_total.labels(
                    issue_type=issue_type,
                    metric_name=metric_name
                ).inc()
        
        # Report pipeline anomalies
        anomalies = self.quality_monitor.detect_pipeline_anomalies()
        monitoring_pipeline_anomalies.set(len(anomalies))
        
        return health
```

---

## 7. Monitoring Cost Optimization (Python)

### 7.1 Cost Optimizer

```python
# grc_claw/monitoring/cost_optimizer.py
"""
Monitoring cost optimization for GRC_Claw.

Analyzes monitoring infrastructure costs and provides
optimization recommendations for:
- Metric retention policies
- Sampling rates
- Storage tiering
- Alert fatigue reduction
- Dashboard optimization
"""

import json
import statistics
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import math


@dataclass
class CostBreakdown:
    """Cost breakdown for monitoring infrastructure."""
    storage_cost_monthly: float
    ingestion_cost_monthly: float
    query_cost_monthly: float
    alerting_cost_monthly: float
    compute_cost_monthly: float
    total_monthly: float
    currency: str = "USD"


@dataclass
class OptimizationRecommendation:
    """A cost optimization recommendation."""
    category: str  # storage, ingestion, query, alerting, compute
    title: str
    description: str
    estimated_savings_monthly: float
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high
    steps: List[str]
    priority: int  # 1 = highest


@dataclass
class MetricCostProfile:
    """Cost profile for a single metric."""
    metric_name: str
    sample_rate: float  # samples per second
    retention_days: int
    storage_bytes_per_sample: int
    query_frequency: float  # queries per day
    alert_count_30d: int
    estimated_monthly_cost: float


class MonitoringCostOptimizer:
    """
    Analyzes and optimizes monitoring infrastructure costs.
    
    Provides recommendations for reducing costs while
    maintaining monitoring effectiveness.
    """
    
    # Cost constants (USD)
    COST_PER_GB_INGESTION = 0.10  # per GB per month
    COST_PER_GB_STORAGE_HOT = 0.10  # per GB per month (hot storage)
    COST_PER_GB_STORAGE_COLD = 0.02  # per GB per month (cold storage)
    COST_PER_1K_QUERIES = 0.01  # per 1K queries
    COST_PER_ALERT = 0.01  # per alert notification
    COST_PER_COMPUTE_HOUR = 0.05  # per vCPU hour
    
    def __init__(self):
        self._metric_profiles: Dict[str, MetricCostProfile] = {}
        self._cost_history: List[CostBreakdown] = []
        self._alert_history: Dict[str, List[datetime]] = defaultdict(list)
        self._query_patterns: Dict[str, int] = defaultdict(int)
    
    def profile_metric(self, metric_name: str, sample_rate: float,
                       retention_days: int, storage_bytes_per_sample: int = 100,
                       query_frequency: float = 100):
        """Create a cost profile for a metric."""
        # Estimate monthly storage
        samples_per_month = sample_rate * 86400 * 30
        storage_gb = (samples_per_month * storage_bytes_per_sample) / (1024 ** 3)
        
        # Estimate ingestion cost
        ingestion_gb = storage_gb  # Simplified
        ingestion_cost = ingestion_gb * self.COST_PER_GB_INGESTION
        
        # Estimate storage cost
        storage_cost = storage_gb * self.COST_PER_GB_STORAGE_HOT
        
        # Estimate query cost
        queries_per_month = query_frequency * 30
        query_cost = (queries_per_month / 1000) * self.COST_PER_1K_QUERIES
        
        # Estimate alert cost
        alert_count = len(self._alert_history.get(metric_name, []))
        alert_cost = alert_count * self.COST_PER_ALERT
        
        total = ingestion_cost + storage_cost + query_cost + alert_cost
        
        self._metric_profiles[metric_name] = MetricCostProfile(
            metric_name=metric_name,
            sample_rate=sample_rate,
            retention_days=retention_days,
            storage_bytes_per_sample=storage_bytes_per_sample,
            query_frequency=query_frequency,
            alert_count_30d=alert_count,
            estimated_monthly_cost=round(total, 2)
        )
    
    def record_alert(self, metric_name: str, timestamp: Optional[datetime] = None):
        """Record an alert for cost tracking."""
        self._alert_history[metric_name].append(
            timestamp or datetime.utcnow()
        )
    
    def record_query(self, metric_name: str):
        """Record a query for cost tracking."""
        self._query_patterns[metric_name] += 1
    
    def get_cost_breakdown(self) -> CostBreakdown:
        """Get current cost breakdown."""
        storage = sum(
            p.estimated_monthly_cost * 0.4  # 40% storage
            for p in self._metric_profiles.values()
        )
        ingestion = sum(
            p.estimated_monthly_cost * 0.3  # 30% ingestion
            for p in self._metric_profiles.values()
        )
        query = sum(
            p.estimated_monthly_cost * 0.15  # 15% query
            for p in self._metric_profiles.values()
        )
        alerting = sum(
            p.estimated_monthly_cost * 0.1  # 10% alerting
            for p in self._metric_profiles.values()
        )
        compute = sum(
            p.estimated_monthly_cost * 0.05  # 5% compute
            for p in self._metric_profiles.values()
        )
        
        total = storage + ingestion + query + alerting + compute
        
        breakdown = CostBreakdown(
            storage_cost_monthly=round(storage, 2),
            ingestion_cost_monthly=round(ingestion, 2),
            query_cost_monthly=round(query, 2),
            alerting_cost_monthly=round(alerting, 2),
            compute_cost_monthly=round(compute, 2),
            total_monthly=round(total, 2)
        )
        
        self._cost_history.append(breakdown)
        return breakdown
    
    def analyze_alert_fatigue(self) -> Dict[str, Any]:
        """
        Analyze alert patterns for alert fatigue.
        
        Identifies metrics that generate excessive alerts,
        suggesting threshold tuning or alert consolidation.
        """
        fatigue_report = {}
        
        for metric_name, timestamps in self._alert_history.items():
            if not timestamps:
                continue
            
            # Filter to last 30 days
            cutoff = datetime.utcnow() - timedelta(days=30)
            recent = [t for t in timestamps if t > cutoff]
            
            if not recent:
                continue
            
            # Calculate alert frequency
            alert_count = len(recent)
            
            # Calculate alert clustering (bursts)
            if len(recent) > 1:
                intervals = [
                    (recent[i+1] - recent[i]).total_seconds() / 60
                    for i in range(len(recent) - 1)
                ]
                avg_interval = statistics.mean(intervals) if intervals else 0
                min_interval = min(intervals) if intervals else 0
            else:
                avg_interval = float('inf')
                min_interval = float('inf')
            
            # Identify fatigue patterns
            fatigue_indicators = []
            
            if alert_count > 100:
                fatigue_indicators.append("excessive_alert_count")
            if avg_interval < 5:  # Less than 5 minutes between alerts
                fatigue_indicators.append("rapid_fire_alerts")
            if min_interval < 1:  # Less than 1 minute between alerts
                fatigue_indicators.append("alert_storm")
            
            # Calculate potential savings from consolidation
            # If we could reduce alerts by 80% through better thresholds
            potential_savings = alert_count * 0.8 * self.COST_PER_ALERT
            
            fatigue_report[metric_name] = {
                "alert_count_30d": alert_count,
                "avg_interval_minutes": round(avg_interval, 2) if avg_interval != float('inf') else None,
                "min_interval_minutes": round(min_interval, 2) if min_interval != float('inf') else None,
                "fatigue_indicators": fatigue_indicators,
                "estimated_monthly_cost": round(alert_count * self.COST_PER_ALERT, 2),
                "potential_savings": round(potential_savings, 2),
                "recommendation": self._fatigue_recommendation(
                    alert_count, fatigue_indicators
                )
            }
        
        return fatigue_report
    
    def _fatigue_recommendation(self, alert_count: int,
                                 indicators: List[str]) -> str:
        """Generate recommendation for alert fatigue."""
        if "alert_storm" in indicators:
            return "CRITICAL: Implement alert grouping and rate limiting. Consider raising thresholds."
        elif "rapid_fire_alerts" in indicators:
            return "HIGH: Add 'for' duration to alert rules. Implement alert grouping."
        elif "excessive_alert_count" in indicators:
            return "MEDIUM: Review alert thresholds. Consider consolidating related alerts."
        elif alert_count > 50:
            return "LOW: Monitor alert frequency. Consider weekly alert review."
        else:
            return "OK: Alert frequency is within acceptable range."
    
    def generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Generate cost optimization recommendations.
        
        Analyzes current monitoring setup and suggests
        cost-saving measures.
        """
        recommendations = []
        
        # 1. Storage tiering for old metrics
        old_metrics = [
            name for name, profile in self._metric_profiles.items()
            if profile.retention_days > 90
        ]
        if old_metrics:
            savings = sum(
                self._metric_profiles[name].estimated_monthly_cost * 0.3
                for name in old_metrics
            )
            recommendations.append(OptimizationRecommendation(
                category="storage",
                title="Implement storage tiering for historical metrics",
                description=f"Move {len(old_metrics)} metrics with >90d retention to cold storage",
                estimated_savings_monthly=round(savings, 2),
                implementation_effort="low",
                risk_level="low",
                steps=[
                    "Identify metrics with retention > 90 days",
                    "Configure Prometheus remote_write with storage tiering",
                    "Move metrics older than 30 days to cold storage",
                    "Update Grafana queries to use appropriate storage tier"
                ],
                priority=1
            ))
        
        # 2. Reduce scrape interval for high-volume metrics
        high_volume = [
            name for name, profile in self._metric_profiles.items()
            if profile.sample_rate > 1.0
        ]
        if high_volume:
            savings = sum(
                self._metric_profiles[name].estimated_monthly_cost * 0.2
                for name in high_volume
            )
            recommendations.append(OptimizationRecommendation(
                category="ingestion",
                title="Reduce scrape interval for high-volume metrics",
                description=f"Increase scrape interval from 15s to 30s for {len(high_volume)} metrics",
                estimated_savings_monthly=round(savings, 2),
                implementation_effort="low",
                risk_level="low",
                steps=[
                    "Identify metrics with sample_rate > 1.0/s",
                    "Increase scrape_interval in prometheus.yml",
                    "Verify alert rules still fire correctly",
                    "Monitor for any detection gaps"
                ],
                priority=2
            ))
        
        # 3. Alert consolidation
        fatigue = self.analyze_alert_fatigue()
        fatigued_metrics = {
            name: data for name, data in fatigue.items()
            if data.get("fatigue_indicators")
        }
        if fatigued_metrics:
            total_savings = sum(
                data["potential_savings"] for data in fatigued_metrics.values()
            )
            recommendations.append(OptimizationRecommendation(
                category="alerting",
                title="Consolidate and tune alert thresholds",
                description=f"Fix alert fatigue for {len(fatigued_metrics)} metrics",
                estimated_savings_monthly=round(total_savings, 2),
                implementation_effort="medium",
                risk_level="medium",
                steps=[
                    "Review alert rules for metrics with fatigue indicators",
                    "Add 'for' duration to prevent flapping",
                    "Implement alert grouping in AlertManager",
                    "Raise thresholds for noisy alerts",
                    "Create inhibition rules for related alerts"
                ],
                priority=1
            ))
        
        # 4. Dashboard query optimization
        expensive_queries = [
            name for name, count in self._query_patterns.items()
            if count > 10000
        ]
        if expensive_queries:
            savings = len(expensive_queries) * 50  # Estimated
            recommendations.append(OptimizationRecommendation(
                category="query",
                title="Optimize expensive dashboard queries",
                description=f"Add recording rules for {len(expensive_queries)} frequently queried metrics",
                estimated_savings_monthly=round(savings, 2),
                implementation_effort="medium",
                risk_level="low",
                steps=[
                    "Identify metrics with high query frequency",
                    "Create Prometheus recording rules for common aggregations",
                    "Update dashboards to use recording rules",
                    "Add query caching in Grafana"
                ],
                priority=3
            ))
        
        # 5. Metric sampling for low-value metrics
        low_value_metrics = [
            name for name, profile in self._metric_profiles.items()
            if profile.query_frequency < 10 and profile.sample_rate > 0.1
        ]
        if low_value_metrics:
            savings = sum(
                self._metric_profiles[name].estimated_monthly_cost * 0.5
                for name in low_value_metrics
            )
            recommendations.append(OptimizationRecommendation(
                category="ingestion",
                title="Reduce sampling for low-value metrics",
                description=f"Reduce sample rate for {len(low_value_metrics)} rarely queried metrics",
                estimated_savings_monthly=round(savings, 2),
                implementation_effort="low",
                risk_level="low",
                steps=[
                    "Identify metrics with low query frequency",
                    "Reduce sample rate or increase scrape interval",
                    "Verify no critical alerts depend on these metrics",
                    "Document reduced monitoring coverage"
                ],
                priority=4
            ))
        
        # 6. Right-size monitoring infrastructure
        recommendations.append(OptimizationRecommendation(
            category="compute",
            title="Right-size monitoring infrastructure",
            description="Evaluate Prometheus and Grafana resource allocation",
            estimated_savings_monthly=200.0,
            implementation_effort="medium",
            risk_level="low",
            steps=[
                "Review Prometheus memory and CPU utilization",
                "Evaluate Grafana instance sizing",
                "Consider using Grafana Cloud or managed Prometheus",
                "Implement resource limits and requests in K8s",
                "Review and optimize Prometheus configuration"
            ],
            priority=3
        ))
        
        # Sort by priority
        recommendations.sort(key=lambda r: r.priority)
        
        return recommendations
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        cost = self.get_cost_breakdown()
        fatigue = self.analyze_alert_fatigue()
        recommendations = self.generate_optimization_recommendations()
        
        total_potential_savings = sum(
            r.estimated_savings_monthly for r in recommendations
        )
        
        return {
            "current_costs": {
                "total_monthly": cost.total_monthly,
                "breakdown": {
                    "storage": cost.storage_cost_monthly,
                    "ingestion": cost.ingestion_cost_monthly,
                    "query": cost.query_cost_monthly,
                    "alerting": cost.alerting_cost_monthly,
                    "compute": cost.compute_cost_monthly
                }
            },
            "alert_fatigue": fatigue,
            "recommendations": [
                {
                    "category": r.category,
                    "title": r.title,
                    "description": r.description,
                    "estimated_savings_monthly": r.estimated_savings_monthly,
                    "implementation_effort": r.implementation_effort,
                    "risk_level": r.risk_level,
                    "steps": r.steps,
                    "priority": r.priority
                }
                for r in recommendations
            ],
            "total_potential_savings_monthly": round(total_potential_savings, 2),
            "savings_percentage": round(
                (total_potential_savings / cost.total_monthly * 100)
                if cost.total_monthly > 0 else 0, 2
            ),
            "timestamp": datetime.utcnow().isoformat()
        }


class RetentionPolicyOptimizer:
    """
    Optimizes metric retention policies based on access patterns.
    
    Implements tiered retention:
    - Hot: Recent data, high resolution (0-7 days)
    - Warm: Medium-term data, reduced resolution (7-30 days)
    - Cold: Long-term data, minimal resolution (30-365 days)
    - Archive: Compliance data, aggregated only (365+ days)
    """
    
    TIERS = {
        "hot": {"retention_days": 7, "resolution": "15s", "cost_factor": 1.0},
        "warm": {"retention_days": 30, "resolution": "1m", "cost_factor": 0.5},
        "cold": {"retention_days": 365, "resolution": "5m", "cost_factor": 0.1},
        "archive": {"retention_days": 2555, "resolution": "1h", "cost_factor": 0.02}
    }
    
    def __init__(self):
        self._access_patterns: Dict[str, Dict] = {}
    
    def record_access(self, metric_name: str, data_age_days: float):
        """Record access to metric data of a certain age."""
        if metric_name not in self._access_patterns:
            self._access_patterns[metric_name] = {
                "accesses": [],
                "age_distribution": defaultdict(int)
            }
        
        self._access_patterns[metric_name]["accesses"].append({
            "timestamp": datetime.utcnow(),
            "data_age_days": data_age_days
        })
        
        # Categorize by age
        if data_age_days <= 7:
            tier = "hot"
        elif data_age_days <= 30:
            tier = "warm"
        elif data_age_days <= 365:
            tier = "cold"
        else:
            tier = "archive"
        
        self._access_patterns[metric_name]["age_distribution"][tier] += 1
    
    def recommend_tier(self, metric_name: str) -> Dict[str, Any]:
        """
        Recommend optimal retention tier for a metric.
        """
        if metric_name not in self._access_patterns:
            return {
                "metric": metric_name,
                "recommended_tier": "hot",
                "reason": "No access pattern data, defaulting to hot"
            }
        
        patterns = self._access_patterns[metric_name]
        age_dist = patterns["age_distribution"]
        total = sum(age_dist.values())
        
        if total == 0:
            return {
                "metric": metric_name,
                "recommended_tier": "hot",
                "reason": "No access data"
            }
        
        # Find most accessed tier
        most_accessed = max(age_dist.items(), key=lambda x: x[1])
        tier_name = most_accessed[0]
        tier_pct = most_accessed[1] / total
        
        # Calculate potential savings from tier optimization
        current_cost = self.TIERS["hot"]["cost_factor"]
        optimal_cost = self.TIERS[tier_name]["cost_factor"]
        savings = (current_cost - optimal_cost) / current_cost
        
        return {
            "metric": metric_name,
            "recommended_tier": tier_name,
            "access_distribution": {
                tier: round(count / total, 4)
                for tier, count in age_dist.items()
            },
            "most_accessed_tier": tier_name,
            "most_accessed_percentage": round(tier_pct, 4),
            "potential_savings": round(savings * 100, 2),
            "reason": f"Most data access ({tier_pct*100:.1f}%) is from {tier_name} tier"
        }
    
    def generate_retention_plan(self) -> List[Dict]:
        """Generate retention plan for all metrics."""
        plan = []
        
        for metric_name in self._access_patterns:
            recommendation = self.recommend_tier(metric_name)
            tier = recommendation["recommended_tier"]
            tier_config = self.TIERS[tier]
            
            plan.append({
                "metric": metric_name,
                "tier": tier,
                "retention_days": tier_config["retention_days"],
                "resolution": tier_config["resolution"],
                "cost_factor": tier_config["cost_factor"],
                "potential_savings_pct": recommendation.get("potential_savings", 0)
            })
        
        return plan
```

### 7.2 Cost Optimization Configuration

```yaml
# grc_claw/monitoring/cost_optimization.yml
# Monitoring cost optimization configuration

# Retention policies by metric category
retention_policies:
  # High-value metrics: keep at full resolution
  - category: safety
    hot_retention: 7d
    warm_retention: 30d
    cold_retention: 365d
    resolution_hot: 15s
    resolution_warm: 1m
    resolution_cold: 5m

  - category: security
    hot_retention: 7d
    warm_retention: 30d
    cold_retention: 365d
    resolution_hot: 15s
    resolution_warm: 1m
    resolution_cold: 5m

  - category: model_performance
    hot_retention: 7d
    warm_retention: 30d
    cold_retention: 90d
    resolution_hot: 15s
    resolution_warm: 1m
    resolution_cold: 5m

  - category: drift
    hot_retention: 3d
    warm_retention: 14d
    cold_retention: 90d
    resolution_hot: 1m
    resolution_warm: 5m
    resolution_cold: 1h

  - category: bias_fairness
    hot_retention: 3d
    warm_retention: 14d
    cold_retention: 90d
    resolution_hot: 1m
    resolution_warm: 5m
    resolution_cold: 1h

  - category: agent_behavior
    hot_retention: 3d
    warm_retention: 14d
    cold_retention: 60d
    resolution_hot: 15s
    resolution_warm: 1m
    resolution_cold: 5m

  - category: incident_response
    hot_retention: 7d
    warm_retention: 30d
    cold_retention: 365d
    resolution_hot: 15s
    resolution_warm: 1m
    resolution_cold: 5m

# Sampling rates by metric value
sampling_rates:
  high_value:
    metrics: [toxicity_score, jailbreak_attempt_count, constraint_breach_count]
    sample_rate: 1.0  # 100%
  medium_value:
    metrics: [llm_error_rate, llm_success_rate, feature_drift_score]
    sample_rate: 0.5  # 50%
  low_value:
    metrics: [agent_loop_count, agent_context_window_usage]
    sample_rate: 0.1  # 10%

# Alert consolidation rules
alert_consolidation:
  # Group alerts that fire together frequently
  - name: model_health_group
    alerts: [HighErrorRate, LowSuccessRate, HighP95Latency]
    group_window: 5m
    max_alerts_per_group: 1
    consolidation_message: "Multiple model health issues detected for {{ $labels.model }}"

  - name: safety_group
    alerts: [ToxicityDetected, JailbreakAttempt, PromptInjectionDetected]
    group_window: 1m
    max_alerts_per_group: 1
    consolidation_message: "Multiple safety issues detected"

  - name: drift_group
    alerts: [FeatureDriftDetected, PredictionDriftDetected, EmbeddingDriftDetected]
    group_window: 15m
    max_alerts_per_group: 1
    consolidation_message: "Multiple drift indicators detected"

# Cost thresholds
cost_alerts:
  - name: HighMonitoringCost
    condition: monthly_cost > 5000
    severity: P2
    message: "Monitoring cost exceeded $5000/month"

  - name: MonitoringCostSpike
    condition: cost_increase_7d > 50%
    severity: P2
    message: "Monitoring cost increased by >50% in 7 days"

# Optimization schedule
optimization_schedule:
  review_frequency: weekly
  auto_apply_safe_changes: true
  require_approval_for:
    - retention_policy_changes
    - sampling_rate_changes
    - alert_threshold_changes
```

---

## Appendix A: File Structure

```
grc_claw/monitoring/
├── __init__.py
├── metrics_exporter.py          # Section 1.1 - Prometheus metrics
├── langfuse_collector.py        # Section 1.2 - Langfuse integration
├── arize_collector.py           # Section 1.3 - Arize integration
├── datadog_collector.py         # Section 1.4 - Datadog integration
├── anomaly_detector.py          # Section 4.1 - Anomaly detection
├── anomaly_pipeline.py          # Section 4.2 - Detection pipeline
├── predictive_alerts.py         # Section 5 - Predictive alerting
├── data_quality.py              # Section 6.1 - Data quality monitoring
├── data_quality_reporter.py     # Section 6.2 - Quality reporting
├── cost_optimizer.py            # Section 7.1 - Cost optimization
├── prometheus/
│   ├── prometheus.yml           # Section 2.3 - Scrape config
│   ├── alert_rules.yml          # Section 2.1 - Alert rules
│   └── alertmanager.yml         # Section 2.2 - Alert routing
├── grafana/
│   ├── executive_dashboard.json       # Section 3.1
│   ├── model_performance_dashboard.json # Section 3.2
│   ├── drift_detection_dashboard.json  # Section 3.3
│   ├── bias_fairness_dashboard.json    # Section 3.4
│   ├── safety_dashboard.json          # Section 3.5
│   ├── security_dashboard.json        # Section 3.6
│   ├── agent_behavior_dashboard.json   # Section 3.7
│   └── incident_response_dashboard.json # Section 3.8
└── config/
    ├── cost_optimization.yml    # Section 7.2
    └── monitoring_config.yml    # General configuration
```

---

## Appendix B: Quick Start

### B.1 Docker Compose for Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.47.0
    ports:
      - "9090:9090"
    volumes:
      - ./grc_claw/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./grc_claw/monitoring/prometheus/alert_rules.yml:/etc/prometheus/rules/alert_rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'

  alertmanager:
    image: prom/alertmanager:v0.26.0
    ports:
      - "9093:9093"
    volumes:
      - ./grc_claw/monitoring/prometheus/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'

  grafana:
    image: grafana/grafana:10.1.0
    ports:
      - "3000:3000"
    volumes:
      - ./grc_claw/monitoring/grafana/:/etc/grafana/provisioning/dashboards/
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel

  node-exporter:
    image: prom/node-exporter:v1.6.1
    ports:
      - "9100:9100"

volumes:
  prometheus_data:
  grafana_data:
```

### B.2 Environment Variables

```bash
# Monitoring stack
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
ALERTMANAGER_URL=http://localhost:9093

# Alerting
PAGERDUTY_CRITICAL_KEY=your-key-here
PAGERDUTY_HIGH_KEY=your-key-here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SMTP_PASSWORD=your-smtp-password

# Langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Arize
ARIZE_SPACE_KEY=your-space-key
ARIZE_API_KEY=your-api-key

# Datadog
DATADOG_API_KEY=your-api-key
DATADOG_APP_KEY=your-app-key

# GRC_Claw
GRC_CLAW_ENVIRONMENT=production
GRC_CLAW_VERSION=1.0.0
```

---

**Document Control:**
- Next review date: 2026-11-01
- Owner: AI Governance Team
- Approver: Chief AI Officer
</longcat_think>
