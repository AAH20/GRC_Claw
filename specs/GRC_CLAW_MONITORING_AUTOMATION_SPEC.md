# GRC_Claw Monitoring Automation & Predictive Analytics Specification

**Version:** 1.0.0  
**Date:** 2026-10-01  
**Author:** Ahmed Hassan  
**Status:** Draft  
**Standard:** ISO 42001 Clause 9 (Monitoring, Measurement, Analysis, and Evaluation)  
**Parent Documents:** GRC_CLAW_MONITORING_OBSERVABILITY_SPEC.md, grc-claw-performance-spec.md

---

## 1. Purpose & Scope

This specification extends the GRC_Claw Monitoring & Observability Specification with detailed monitoring automation, anomaly detection, predictive analytics, data quality assurance, self-health monitoring, and cost optimization. It transforms monitoring from a reactive, threshold-based system into a proactive, self-managing observability platform.

**In scope:**
- Automated metric collection pipelines with self-healing ingestion
- Statistical and ML-based anomaly detection automation
- Predictive alerting with forecasting and early warning
- Monitoring data quality validation and assurance
- Monitoring system self-health and meta-monitoring
- Monitoring cost optimization and resource efficiency

**Out of scope:**
- Application-level business logic monitoring
- End-user experience monitoring (covered by RUM spec)
- Third-party SaaS monitoring

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                GRC_Claw Monitoring Automation Pipeline                        │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Auto       │  │   Anomaly    │  │  Predictive  │  │   Data       │   │
│  │   Collection │→ │   Detection  │→ │   Alerting   │→ │   Quality    │   │
│  │   Engine     │  │   Engine     │  │   Engine     │  │   Validator  │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │            │
│         └────────────┬────┴────────┬────────┴────────┬────────┘            │
│                      │             │             │                          │
│              ┌───────▼──────┐ ┌────▼─────┐ ┌────▼──────┐                  │
│              │  Self-Health │ │  Cost    │ │  Alert    │                  │
│              │  Monitor     │ │Optimizer │ │  Router   │                  │
│              └──────────────┘ └──────────┘ └───────────┘                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Governance Feedback Loop                          │    │
│  │  Monitoring Health → Risk Engine → Control Updates → Cost Actions   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Data Flow

1. **Auto-Collection** — Agents, models, and infrastructure emit telemetry via auto-instrumented collectors with adaptive sampling
2. **Anomaly Detection** — Real-time and batch anomaly detection engines score every metric stream
3. **Predictive Alerting** — Forecasting models predict threshold breaches before they occur
4. **Data Quality** — Every metric is validated for completeness, accuracy, timeliness, and consistency
5. **Self-Health** — The monitoring system monitors itself; meta-metrics track pipeline health
6. **Cost Optimization** — Continuous analysis of monitoring spend vs. value drives sampling and retention tuning

---

## 3. Automated Metric Collection

### 3.1 Collection Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Metric Collection Pipeline                        │
│                                                                      │
│  Sources        Collectors         Processors         Storage        │
│  ───────        ──────────         ──────────         ───────        │
│  ┌────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       │
│  │ Langfuse│───→│ Trace    │───→│ Enrich   │───→│ Prometheus│       │
│  │ Traces  │    │ Collector│    │ & Label  │    │ (TSDB)   │       │
│  └────────┘    └──────────┘    └──────────┘    └──────────┘       │
│  ┌────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       │
│  │ Arize  │───→│ Drift    │───→│ Normalize│───→│ Arize    │       │
│  │ Events │    │ Collector│    │ & Score  │    │ Store    │       │
│  └────────┘    └──────────┘    └──────────┘    └──────────┘       │
│  ┌────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       │
│  │ Custom │───→│ GRC      │───→│ Validate │───→│ Kafka    │       │
│  │ Agents │    │ Collector│    │ & Route  │    │ (Bus)    │       │
│  └────────┘    └──────────┘    └──────────┘    └──────────┘       │
│  ┌────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       │
│  │Infra   │───→│ Datadog  │───→│ Correlate│───→│ Datadog  │       │
│  │ Metrics│    │ Collector│    │ & Tag    │    │ (APM)    │       │
│  └────────┘    └──────────┘    └──────────┘    └──────────┘       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Adaptive Sampling Controller                     │   │
│  │  • Volume-based sampling  • Priority-based sampling          │   │
│  │  • Anomaly-triggered full capture  • Cost-aware sampling     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Auto-Instrumentation

All GRC_Claw components are auto-instrumented via a shared library that requires zero code changes for basic metrics:

```python
# grc_claw/auto_instrumentation.py
import time
import functools
from typing import Optional, Callable
from contextlib import contextmanager

class AutoInstrumenter:
    """Zero-code-change metric collection for GRC_Claw components."""
    
    def __init__(self, component_name: str, metrics_client):
        self.component = component_name
        self.metrics = metrics_client
        self._active_spans = {}
    
    def instrument_method(self, func: Callable) -> Callable:
        """Decorator that auto-collects latency, error, and throughput metrics."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.monotonic()
            labels = {
                "component": self.component,
                "method": func.__name__,
            }
            
            try:
                result = func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                labels["error_type"] = type(e).__name__
                raise
            finally:
                duration = time.monotonic() - start
                self.metrics.histogram(
                    "grc_method_duration_seconds",
                    duration,
                    labels=labels
                )
                self.metrics.increment(
                    "grc_method_calls_total",
                    labels={**labels, "status": status}
                )
        
        return wrapper
    
    @contextmanager
    def span(self, operation: str, labels: Optional[dict] = None):
        """Context manager for tracing arbitrary code blocks."""
        span_id = f"{self.component}:{operation}:{time.time()}"
        merged_labels = {"component": self.component, "operation": operation}
        if labels:
            merged_labels.update(labels)
        
        self._active_spans[span_id] = {
            "start": time.monotonic(),
            "labels": merged_labels
        }
        
        try:
            yield span_id
        except Exception as e:
            self._active_spans[span_id]["error"] = str(e)
            self._active_spans[span_id]["error_type"] = type(e).__name__
            raise
        finally:
            span_data = self._active_spans.pop(span_id)
            duration = time.monotonic() - span_data["start"]
            
            self.metrics.histogram(
                "grc_operation_duration_seconds",
                duration,
                labels=span_data["labels"]
            )
            
            if "error_type" in span_data:
                self.metrics.increment(
                    "grc_operation_errors_total",
                    labels={
                        "component": self.component,
                        "operation": operation,
                        "error_type": span_data["error_type"]
                    }
                )
    
    def auto_collect_llm_metrics(self, model: str, usage: dict, latency_ms: float, 
                                  cost: float, metadata: Optional[dict] = None):
        """Auto-collect LLM-specific metrics from any provider response."""
        base_labels = {"model": model}
        if metadata:
            base_labels.update(metadata)
        
        self.metrics.histogram("llm_request_duration_seconds", latency_ms / 1000, 
                              labels=base_labels)
        self.metrics.increment("llm_token_usage_total", 
                              labels={**base_labels, "type": "input"},
                              value=usage.get("prompt_tokens", 0))
        self.metrics.increment("llm_token_usage_total",
                              labels={**base_labels, "type": "output"},
                              value=usage.get("completion_tokens", 0))
        self.metrics.increment("llm_cost_total", value=cost, labels=base_labels)
    
    def auto_collect_agent_metrics(self, agent_id: str, run_data: dict):
        """Auto-collect agent behavior metrics."""
        labels = {"agent_id": agent_id}
        
        self.metrics.histogram("agent_run_duration_seconds", 
                              run_data.get("duration_seconds", 0), labels=labels)
        self.metrics.gauge("agent_success_rate",
                          1.0 if run_data.get("success") else 0.0, labels=labels)
        self.metrics.gauge("agent_context_window_usage",
                          run_data.get("context_usage_pct", 0), labels=labels)
        self.metrics.gauge("agent_cost_per_run",
                          run_data.get("cost_usd", 0), labels=labels)
        
        for tool_call in run_data.get("tool_calls", []):
            self.metrics.increment("agent_tool_call_count",
                                  labels={**labels, "tool_name": tool_call["name"]})
            if tool_call.get("error"):
                self.metrics.increment("agent_tool_error_count",
                                      labels={**labels, "tool_name": tool_call["name"]})
```

### 3.3 Adaptive Sampling Controller

Sampling rates adjust dynamically based on system state, anomaly signals, and cost constraints:

```python
# grc_claw/adaptive_sampling.py
from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum
import time

class SamplingPriority(Enum):
    CRITICAL = "critical"    # Always 100% — safety/security events
    HIGH = "high"            # 100% during anomalies, 50% normal
    MEDIUM = "medium"        # 50% during anomalies, 10% normal
    LOW = "low"              # 10% during anomalies, 1% normal
    BACKGROUND = "background"  # 1% always — informational metrics

@dataclass
class SamplingConfig:
    normal_rate: float
    anomaly_rate: float
    max_samples_per_second: float
    min_samples_per_second: float = 1.0
    cooldown_seconds: int = 300  # Time to return to normal after anomaly

class AdaptiveSamplingController:
    """Dynamically adjusts metric sampling rates based on system state."""
    
    DEFAULT_CONFIGS = {
        SamplingPriority.CRITICAL: SamplingConfig(1.0, 1.0, 10000),
        SamplingPriority.HIGH: SamplingConfig(0.5, 1.0, 5000),
        SamplingPriority.MEDIUM: SamplingConfig(0.1, 0.5, 1000),
        SamplingPriority.LOW: SamplingConfig(0.01, 0.1, 100),
        SamplingPriority.BACKGROUND: SamplingConfig(0.01, 0.01, 10),
    }
    
    def __init__(self, cost_budget_daily: float = 100.0):
        self.cost_budget = cost_budget_daily
        self.current_rates: Dict[str, float] = {}
        self.anomaly_state: Dict[str, float] = {}  # metric -> anomaly expiry time
        self.sample_counters: Dict[str, int] = {}
        self.last_cost_check = time.time()
        self.daily_cost = 0.0
    
    def get_sampling_rate(self, metric_name: str, priority: SamplingPriority) -> float:
        """Get current sampling rate for a metric."""
        config = self.DEFAULT_CONFIGS[priority]
        
        # Check if metric is in anomaly state
        if metric_name in self.anomaly_state:
            if time.time() < self.anomaly_state[metric_name]:
                return config.anomaly_rate
            else:
                del self.anomaly_state[metric_name]
        
        # Cost-based throttling
        if self.daily_cost > self.cost_budget * 0.9:
            return max(config.normal_rate * 0.1, config.min_samples_per_second)
        elif self.daily_cost > self.cost_budget * 0.75:
            return config.normal_rate * 0.5
        
        return config.normal_rate
    
    def mark_anomaly(self, metric_name: str, duration_seconds: int = 300):
        """Temporarily boost sampling for a metric that is anomalous."""
        self.anomaly_state[metric_name] = time.time() + duration_seconds
    
    def should_sample(self, metric_name: str, priority: SamplingPriority) -> bool:
        """Determine if a specific data point should be sampled."""
        rate = self.get_sampling_rate(metric_name, priority)
        if rate >= 1.0:
            return True
        
        # Deterministic sampling for consistency
        bucket = int(time.time() * 10)  # 100ms buckets
        return (hash(f"{metric_name}:{bucket}") % 10000) < (rate * 10000)
    
    def record_sample(self, metric_name: str, estimated_cost: float):
        """Record a sample for cost tracking."""
        self.sample_counters[metric_name] = self.sample_counters.get(metric_name, 0) + 1
        self.daily_cost += estimated_cost
    
    def get_sampling_report(self) -> dict:
        """Generate sampling effectiveness report."""
        return {
            "current_rates": self.current_rates,
            "anomalous_metrics": list(self.anomaly_state.keys()),
            "daily_cost_usd": round(self.daily_cost, 2),
            "budget_utilization": round(self.daily_cost / self.cost_budget, 4),
            "total_samples": sum(self.sample_counters.values()),
            "samples_by_metric": dict(sorted(
                self.sample_counters.items(), key=lambda x: -x[1]
            )[:20])
        }
```

### 3.4 Collection Schedules

| Metric Category | Collection Interval | Batch Size | Timeout | Retry Policy |
|----------------|-------------------|------------|---------|--------------|
| Model performance (latency, errors) | 15s | 100 | 5s | 3 retries, exponential backoff |
| Token usage & cost | 30s | 500 | 10s | 2 retries |
| Drift scores | 15m | 1 | 60s | 1 retry |
| Bias/fairness | 15m | 1 | 60s | 1 retry |
| Safety events | Real-time (push) | 1 | 5s | 5 retries, immediate |
| Security events | Real-time (push) | 1 | 5s | 5 retries, immediate |
| Agent behavior | 30s | 200 | 10s | 2 retries |
| Incident metrics | Real-time (push) | 1 | 5s | 3 retries |
| Infrastructure | 15s | 500 | 5s | 2 retries |
| Self-health | 10s | 1 | 3s | No retry (self-healing) |

### 3.5 Collection Self-Healing

```python
# grc_claw/collection_self_healing.py
from typing import List, Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)

class CollectionSelfHealing:
    """Automatically detects and recovers from collection pipeline failures."""
    
    def __init__(self, metrics_client, alert_manager):
        self.metrics = metrics_client
        self.alerts = alert_manager
        self.failure_counts: Dict[str, int] = {}
        self.last_success: Dict[str, float] = {}
        self.circuit_breakers: Dict[str, bool] = {}
        self.FAILURE_THRESHOLD = 5
        self.CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes
    
    def record_success(self, source: str):
        """Record successful collection from a source."""
        self.last_success[source] = time.time()
        self.failure_counts[source] = 0
        if source in self.circuit_breakers:
            del self.circuit_breakers[source]
            logger.info(f"Circuit breaker reset for {source}")
    
    def record_failure(self, source: str, error: Exception):
        """Record collection failure and trigger healing if needed."""
        self.failure_counts[source] = self.failure_counts.get(source, 0) + 1
        
        if self.failure_counts[source] >= self.FAILURE_THRESHOLD:
            self._open_circuit_breaker(source, error)
    
    def _open_circuit_breaker(self, source: str, error: Exception):
        """Open circuit breaker for a failing source."""
        self.circuit_breakers[source] = True
        logger.error(f"Circuit breaker opened for {source}: {error}")
        
        self.alerts.send_alert(
            title=f"Collection circuit breaker: {source}",
            description=f"Source {source} failed {self.FAILURE_THRESHOLD} times. "
                       f"Last error: {error}",
            severity="P2",
            labels={"source": source, "error_type": type(error).__name__}
        )
        
        # Attempt self-healing
        self._attempt_healing(source, error)
    
    def _attempt_healing(self, source: str, error: Exception):
        """Attempt to heal a failing collection source."""
        healing_actions = {
            "langfuse": self._heal_langfuse,
            "arize": self._heal_arize,
            "prometheus": self._heal_prometheus,
            "datadog": self._heal_datadog,
            "kafka": self._heal_kafka,
        }
        
        healer = healing_actions.get(source)
        if healer:
            try:
                healer()
                logger.info(f"Self-healing succeeded for {source}")
            except Exception as heal_error:
                logger.error(f"Self-healing failed for {source}: {heal_error}")
    
    def _heal_langfuse(self):
        """Heal Langfuse connection: flush buffer, reconnect, reduce batch size."""
        # Implementation: reconnect Langfuse client, reduce batch size
        pass
    
    def _heal_arize(self):
        """Heal Arize connection: reset client, verify API key."""
        pass
    
    def _heal_prometheus(self):
        """Heal Prometheus: restart scrape, verify target health."""
        pass
    
    def _heal_datadog(self):
        """Heal Datadog: reset statsd connection, verify API."""
        pass
    
    def _heal_kafka(self):
        """Heal Kafka: reconnect consumer, reset offset if needed."""
        pass
    
    def is_healthy(self, source: str) -> bool:
        """Check if a collection source is healthy."""
        if source in self.circuit_breakers:
            # Check if circuit breaker timeout has elapsed
            if time.time() - self.last_success.get(source, 0) > self.CIRCUIT_BREAKER_TIMEOUT:
                del self.circuit_breakers[source]
                return True
            return False
        
        last = self.last_success.get(source, 0)
        return (time.time() - last) < 60  # Healthy if success in last 60s
    
    def get_health_report(self) -> dict:
        """Generate collection health report."""
        return {
            "sources": {
                source: {
                    "healthy": self.is_healthy(source),
                    "failure_count": self.failure_counts.get(source, 0),
                    "last_success_seconds_ago": round(
                        time.time() - self.last_success.get(source, 0), 1
                    ),
                    "circuit_breaker_open": source in self.circuit_breakers
                }
                for source in set(list(self.failure_counts.keys()) + 
                                 list(self.last_success.keys()))
            }
        }
```

---

## 4. Anomaly Detection Automation

### 4.1 Detection Engine Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Anomaly Detection Engine                            │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Real-Time   │  │   Batch      │  │  Ensemble    │             │
│  │  Detectors   │  │  Detectors   │  │  Aggregator  │             │
│  │              │  │              │  │              │             │
│  │ • Z-Score    │  │ • Isolation  │  │ • Voting     │             │
│  │ • EWMA       │  │   Forest     │  │ • Confidence │             │
│  │ • Seasonal   │  │ • LOF        │  │   Scoring    │             │
│  │   Decompose  │  │ • DBSCAN     │  │ • Severity   │             │
│  │ • CUSUM      │  │ • Prophet    │  │   Assignment │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                 │                      │
│         └────────────┬────┘                 │                      │
│                      │                      │                      │
│              ┌───────▼──────┐    ┌──────────▼──────────┐          │
│              │  Feature     │    │  Anomaly Event      │          │
│              │  Extractor   │───→│  Router             │          │
│              │              │    │                     │          │
│              │ • Statistical│    │ • Dedup              │          │
│              │ • Temporal   │    │ • Correlate          │          │
│              │ • Contextual │    │ • Route to Alert     │          │
│              └──────────────┘    └─────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Real-Time Anomaly Detectors

```python
# grc_claw/anomaly_detection.py
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque
import time
import statistics

class AnomalySeverity(Enum):
    LOW = "low"           # 1-2 sigma
    MEDIUM = "medium"     # 2-3 sigma
    HIGH = "high"         # 3-4 sigma
    CRITICAL = "critical" # >4 sigma

@dataclass
class AnomalyEvent:
    metric_name: str
    timestamp: float
    value: float
    expected_value: float
    deviation: float  # in standard deviations
    severity: AnomalySeverity
    detector: str
    context: dict
    confidence: float  # 0-1

class ZScoreDetector:
    """Streaming Z-Score anomaly detector with adaptive window."""
    
    def __init__(self, window_size: int = 100, min_samples: int = 30):
        self.window = deque(maxlen=window_size)
        self.min_samples = min_samples
        self.mean = 0.0
        self.std = 0.0
    
    def update(self, value: float) -> Optional[AnomalyEvent]:
        """Update detector with new value and return anomaly if detected."""
        self.window.append(value)
        
        if len(self.window) < self.min_samples:
            return None
        
        self.mean = statistics.mean(self.window)
        self.std = statistics.stdev(self.window) if len(self.window) > 1 else 0
        
        if self.std == 0:
            return None
        
        z_score = abs(value - self.mean) / self.std
        
        if z_score > 2.0:
            severity = self._zscore_to_severity(z_score)
            return AnomalyEvent(
                metric_name="",
                timestamp=time.time(),
                value=value,
                expected_value=self.mean,
                deviation=z_score,
                severity=severity,
                detector="zscore",
                context={"window_mean": self.mean, "window_std": self.std},
                confidence=min(z_score / 5.0, 1.0)
            )
        return None
    
    def _zscore_to_severity(self, z: float) -> AnomalySeverity:
        if z > 4.0:
            return AnomalySeverity.CRITICAL
        elif z > 3.0:
            return AnomalySeverity.HIGH
        elif z > 2.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

class EWMADetector:
    """Exponentially Weighted Moving Average detector for trend anomalies."""
    
    def __init__(self, alpha: float = 0.3, threshold: float = 3.0):
        self.alpha = alpha
        self.threshold = threshold
        self.ewma = None
        self.ewmvar = None
        self.initialized = False
    
    def update(self, value: float) -> Optional[AnomalyEvent]:
        """Update EWMA and detect anomalies."""
        if not self.initialized:
            self.ewma = value
            self.ewmvar = 0
            self.initialized = True
            return None
        
        # Update EWMA
        diff = value - self.ewma
        self.ewma = self.alpha * value + (1 - self.alpha) * self.ewma
        self.ewmvar = (1 - self.alpha) * (self.ewmvar + self.alpha * diff * diff)
        
        ewmstd = np.sqrt(self.ewmvar) if self.ewmvar > 0 else 0
        
        if ewmstd == 0:
            return None
        
        z_score = abs(diff) / ewmstd
        
        if z_score > self.threshold:
            return AnomalyEvent(
                metric_name="",
                timestamp=time.time(),
                value=value,
                expected_value=self.ewma,
                deviation=z_score,
                severity=self._zscore_to_severity(z_score),
                detector="ewma",
                context={"ewma": self.ewma, "ewmstd": ewmstd},
                confidence=min(z_score / 5.0, 1.0)
            )
        return None
    
    def _zscore_to_severity(self, z: float) -> AnomalySeverity:
        if z > 4.0:
            return AnomalySeverity.CRITICAL
        elif z > 3.0:
            return AnomalySeverity.HIGH
        elif z > 2.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

class CUSUMDetector:
    """Cumulative Sum detector for detecting small persistent shifts."""
    
    def __init__(self, target: float = 0, slack: float = 1.0, 
                 threshold: float = 4.0):
        self.target = target
        self.slack = slack
        self.threshold = threshold
        self.cusum_high = 0.0
        self.cusum_low = 0.0
        self.baseline = None
        self.baseline_window = deque(maxlen=50)
    
    def update(self, value: float) -> Optional[AnomalyEvent]:
        """Update CUSUM and detect persistent shifts."""
        self.baseline_window.append(value)
        
        if len(self.baseline_window) < 20:
            return None
        
        self.baseline = statistics.median(self.baseline_window)
        normalized = value - self.baseline
        
        self.cusum_high = max(0, self.cusum_high + normalized - self.slack)
        self.cusum_low = min(0, self.cusum_low + normalized + self.slack)
        
        if self.cusum_high > self.threshold:
            self.cusum_high = 0  # Reset after detection
            return AnomalyEvent(
                metric_name="",
                timestamp=time.time(),
                value=value,
                expected_value=self.baseline,
                deviation=self.cusum_high,
                severity=AnomalySeverity.HIGH,
                detector="cusum",
                context={"direction": "upward_shift", "baseline": self.baseline},
                confidence=0.8
            )
        
        if abs(self.cusum_low) > self.threshold:
            self.cusum_low = 0
            return AnomalyEvent(
                metric_name="",
                timestamp=time.time(),
                value=value,
                expected_value=self.baseline,
                deviation=abs(self.cusum_low),
                severity=AnomalySeverity.HIGH,
                detector="cusum",
                context={"direction": "downward_shift", "baseline": self.baseline},
                confidence=0.8
            )
        
        return None

class SeasonalDecompositionDetector:
    """Detects anomalies by decomposing seasonal patterns."""
    
    def __init__(self, season_length: int = 96):  # 15-min intervals, 24h
        self.season_length = season_length
        self.seasonal_pattern = [[] for _ in range(season_length)]
        self.trend_window = deque(maxlen=season_length * 2)
        self.residual_threshold = 3.0
    
    def update(self, value: float, timestamp: Optional[float] = None) -> Optional[AnomalyEvent]:
        """Update seasonal decomposition and detect anomalies."""
        if timestamp is None:
            timestamp = time.time()
        
        # Determine position in seasonal cycle
        position = int(timestamp / 900) % self.season_length  # 15-min buckets
        
        self.seasonal_pattern[position].append(value)
        self.trend_window.append(value)
        
        if len(self.seasonal_pattern[position]) < 3:
            return None
        
        # Calculate seasonal baseline
        seasonal_baseline = statistics.median(self.seasonal_pattern[position])
        
        # Calculate trend
        if len(self.trend_window) < self.season_length:
            return None
        trend = statistics.median(self.trend_window)
        
        # Expected value = trend + seasonal component
        expected = seasonal_baseline
        residual = value - expected
        
        # Calculate residual std
        residuals = []
        for p in range(self.season_length):
            if len(self.seasonal_pattern[p]) > 1:
                for v in self.seasonal_pattern[p]:
                    residuals.append(v - statistics.median(self.seasonal_pattern[p]))
        
        if len(residuals) < 10:
            return None
        
        residual_std = statistics.stdev(residuals)
        if residual_std == 0:
            return None
        
        z_score = abs(residual) / residual_std
        
        if z_score > self.residual_threshold:
            return AnomalyEvent(
                metric_name="",
                timestamp=timestamp,
                value=value,
                expected_value=expected,
                deviation=z_score,
                severity=self._zscore_to_severity(z_score),
                detector="seasonal",
                context={
                    "seasonal_baseline": seasonal_baseline,
                    "trend": trend,
                    "residual": residual
                },
                confidence=min(z_score / 5.0, 1.0)
            )
        return None
    
    def _zscore_to_severity(self, z: float) -> AnomalySeverity:
        if z > 4.0:
            return AnomalySeverity.CRITICAL
        elif z > 3.0:
            return AnomalySeverity.HIGH
        elif z > 2.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
```

### 4.3 Ensemble Anomaly Aggregator

```python
class EnsembleAnomalyAggregator:
    """Combines multiple detectors and produces unified anomaly events."""
    
    def __init__(self):
        self.detectors: Dict[str, list] = {}
        self.recent_anomalies: deque = deque(maxlen=1000)
        self.correlation_window = 300  # 5 minutes
    
    def register_detector(self, metric_pattern: str, detector):
        """Register a detector for a metric pattern."""
        if metric_pattern not in self.detectors:
            self.detectors[metric_pattern] = []
        self.detectors[metric_pattern].append(detector)
    
    def process(self, metric_name: str, value: float, 
                timestamp: Optional[float] = None) -> Optional[AnomalyEvent]:
        """Process a metric value through all applicable detectors."""
        if timestamp is None:
            timestamp = time.time()
        
        applicable = []
        for pattern, detectors in self.detectors.items():
            if self._matches(metric_name, pattern):
                applicable.extend(detectors)
        
        if not applicable:
            return None
        
        events = []
        for detector in applicable:
            event = detector.update(value)
            if event:
                event.metric_name = metric_name
                events.append(event)
        
        if not events:
            return None
        
        # Ensemble voting: weight by confidence
        return self._aggregate(events)
    
    def _aggregate(self, events: List[AnomalyEvent]) -> AnomalyEvent:
        """Aggregate multiple detector outputs into single event."""
        # Weight by confidence
        total_weight = sum(e.confidence for e in events)
        
        # Majority vote on severity
        severity_votes = {}
        for e in events:
            severity_votes[e.severity] = severity_votes.get(e.severity, 0) + e.confidence
        
        final_severity = max(severity_votes, key=severity_votes.get)
        
        # Weighted average of deviation
        avg_deviation = sum(e.deviation * e.confidence for e in events) / total_weight
        
        # Combined confidence
        combined_confidence = min(total_weight / len(events), 1.0)
        
        # Merge context
        merged_context = {}
        for e in events:
            merged_context.update(e.context)
        merged_context["detectors_triggered"] = [e.detector for e in events]
        
        return AnomalyEvent(
            metric_name=events[0].metric_name,
            timestamp=events[0].timestamp,
            value=events[0].value,
            expected_value=events[0].expected_value,
            deviation=avg_deviation,
            severity=final_severity,
            detector="ensemble",
            context=merged_context,
            confidence=combined_confidence
        )
    
    def _matches(self, metric_name: str, pattern: str) -> bool:
        """Check if metric name matches a pattern."""
        import fnmatch
        return fnmatch.fnmatch(metric_name, pattern)
    
    def find_correlated_anomalies(self, event: AnomalyEvent, 
                                    window_seconds: int = 300) -> List[AnomalyEvent]:
        """Find anomalies that occurred within a time window of the given event."""
        correlated = []
        for recent in self.recent_anomalies:
            if (abs(recent.timestamp - event.timestamp) < window_seconds and
                recent.metric_name != event.metric_name):
                correlated.append(recent)
        return correlated
```

### 4.4 Anomaly Detection Configuration

```yaml
# anomaly_detection.config.yaml
anomaly_detection:
  enabled: true
  
  detectors:
    zscore:
      enabled: true
      window_size: 100
      min_samples: 30
      threshold_sigma: 2.0
      applies_to:
        - "llm_*"
        - "agent_*"
        - "grc_*"
    
    ewma:
      enabled: true
      alpha: 0.3
      threshold: 3.0
      applies_to:
        - "llm_request_duration_seconds"
        - "llm_error_rate"
        - "agent_run_duration_seconds"
    
    cusum:
      enabled: true
      slack: 1.0
      threshold: 4.0
      applies_to:
        - "llm_error_rate"
        - "llm_cost_total"
        - "constraint_breach_count"
    
    seasonal:
      enabled: true
      season_length: 96  # 24h at 15-min intervals
      threshold: 3.0
      applies_to:
        - "llm_request_duration_seconds"
        - "agent_run_duration_seconds"
        - "agent_tool_call_count"
  
  ensemble:
    enabled: true
    min_detectors: 2  # Minimum detectors that must agree
    confidence_threshold: 0.6
    severity_upgrade: true  # Upgrade severity if multiple detectors agree
  
  correlation:
    enabled: true
    window_seconds: 300
    max_correlated: 10
    group_by: ["model_id", "agent_id", "environment"]
  
  suppression:
    enabled: true
    rules:
      - name: "maintenance_window"
        condition: "time in maintenance_window"
        action: "suppress_all"
      - name: "known_deploy"
        condition: "deploy_in_progress == true"
        action: "suppress_severity_below"
        params:
          severity: "HIGH"
      - name: "flapping_metric"
        condition: "alert_count_1h > 10"
        action: "cooldown"
        params:
          cooldown_minutes: 30
```

---

## 5. Predictive Alerting

### 5.1 Predictive Alerting Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Predictive Alerting Engine                         │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Forecasting │  │  Threshold   │  │  Impact      │             │
│  │  Models      │  │  Projector   │  │  Predictor   │             │
│  │              │  │              │  │              │             │
│  │ • Holt-Winters│  │ • Linear     │  │ • Severity   │             │
│  │ • ARIMA      │  │   Extrapolate│  │   Forecast   │             │
│  │ • Prophet    │  │ • Monte Carlo│  │ • Cost       │             │
│  │ • LSTM       │  │ • Slope      │  │   Forecast   │             │
│  │ • Linear     │  │   Analysis   │  │ • Risk       │             │
│  │   Regression │  │              │  │   Forecast   │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                 │                      │
│         └────────────┬────┘                 │                      │
│                      │                      │                      │
│              ┌───────▼──────┐    ┌──────────▼──────────┐          │
│              │  Prediction  │    │  Early Warning      │          │
│              │  Aggregator  │───→│  Generator          │          │
│              │              │    │                     │          │
│              │ • Confidence │    │ • Pre-threshold     │          │
│              │   Intervals  │    │   Alerts            │          │
│              │ • Model      │    │ • Cost Overrun      │          │
│              │   Selection  │    │   Warnings          │          │
│              │ • Ensemble   │    │ • Capacity          │          │
│              │   Forecast   │    │   Warnings          │          │
│              └──────────────┘    └─────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Forecasting Models

```python
# grc_claw/predictive_alerting.py
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque
import time
from abc import ABC, abstractmethod

@dataclass
class ForecastResult:
    metric_name: str
    timestamps: List[float]
    predicted_values: List[float]
    lower_bound: List[float]
    upper_bound: List[float]
    confidence: float
    model_used: str
    horizon_minutes: int

@dataclass
class PredictiveAlert:
    metric_name: str
    alert_type: str  # "threshold_breach", "cost_overrun", "capacity"
    predicted_time: float  # Unix timestamp when breach is predicted
    current_value: float
    predicted_value: float
    threshold: float
    confidence: float
    time_to_breach_minutes: float
    severity: str
    recommended_action: str

class ForecastingModel(ABC):
    """Base class for forecasting models."""
    
    @abstractmethod
    def fit(self, timestamps: List[float], values: List[float]):
        pass
    
    @abstractmethod
    def predict(self, horizon: int, interval: int = 1) -> ForecastResult:
        pass

class HoltWintersForecaster(ForecastingModel):
    """Holt-Winters exponential smoothing for seasonal data."""
    
    def __init__(self, season_length: int = 96, alpha: float = 0.3, 
                 beta: float = 0.1, gamma: float = 0.1):
        self.season_length = season_length
        self.alpha = alpha  # Level smoothing
        self.beta = beta    # Trend smoothing
        self.gamma = gamma  # Seasonal smoothing
        self.level = None
        self.trend = None
        self.seasonal = None
        self.timestamps = None
        self.values = None
    
    def fit(self, timestamps: List[float], values: List[float]):
        """Fit Holt-Winters model."""
        self.timestamps = timestamps
        self.values = values
        n = len(values)
        
        if n < self.season_length * 2:
            raise ValueError(f"Need at least {self.season_length * 2} data points")
        
        # Initialize seasonal components
        self.seasonal = [0.0] * self.season_length
        season_averages = []
        for i in range(self.season_length):
            season_vals = values[i::self.season_length]
            season_averages.append(np.mean(season_vals))
        
        overall_avg = np.mean(season_averages)
        for i in range(self.season_length):
            self.seasonal[i] = season_averages[i] - overall_avg
        
        # Initialize level and trend
        self.level = values[0] - self.seasonal[0]
        self.trend = (values[self.season_length] - values[0]) / self.season_length
        
        # Smooth
        for t in range(n):
            season_idx = t % self.season_length
            value = values[t]
            
            old_level = self.level
            self.level = self.alpha * (value - self.seasonal[season_idx]) + \
                        (1 - self.alpha) * (self.level + self.trend)
            self.trend = self.beta * (self.level - old_level) + \
                        (1 - self.beta) * self.trend
            self.seasonal[season_idx] = self.gamma * (value - self.level) + \
                                       (1 - self.gamma) * self.seasonal[season_idx]
    
    def predict(self, horizon: int, interval: int = 1) -> ForecastResult:
        """Generate forecast for given horizon."""
        if self.level is None:
            raise RuntimeError("Model not fitted")
        
        last_ts = self.timestamps[-1]
        interval_seconds = (self.timestamps[1] - self.timestamps[0]) if len(self.timestamps) > 1 else 900
        
        timestamps = []
        predictions = []
        lower_bounds = []
        upper_bounds = []
        
        # Calculate residual std for confidence intervals
        fitted = []
        for t in range(len(self.values)):
            season_idx = t % self.season_length
            fitted.append(self.level + self.trend * t + self.seasonal[season_idx])
        residuals = np.array(self.values) - np.array(fitted)
        residual_std = np.std(residuals)
        
        for h in range(1, horizon + 1):
            season_idx = (len(self.values) + h - 1) % self.season_length
            forecast = self.level + self.trend * h + self.seasonal[season_idx]
            
            # Confidence interval widens with horizon
            margin = 1.96 * residual_std * np.sqrt(h)
            
            timestamps.append(last_ts + h * interval_seconds)
            predictions.append(forecast)
            lower_bounds.append(forecast - margin)
            upper_bounds.append(forecast + margin)
        
        return ForecastResult(
            metric_name="",
            timestamps=timestamps,
            predicted_values=predictions,
            lower_bound=lower_bounds,
            upper_bound=upper_bounds,
            confidence=max(0.5, 1.0 - 0.02 * horizon),  # Confidence decays with horizon
            model_used="holt_winters",
            horizon_minutes=horizon * int(interval_seconds / 60)
        )

class LinearRegressionForecaster(ForecastingModel):
    """Simple linear regression forecaster for trend-based prediction."""
    
    def __init__(self):
        self.slope = 0.0
        self.intercept = 0.0
        self.r_squared = 0.0
        self.timestamps = None
        self.values = None
        self.residual_std = 0.0
    
    def fit(self, timestamps: List[float], values: List[float]):
        """Fit linear regression."""
        self.timestamps = timestamps
        self.values = values
        
        x = np.array(timestamps)
        y = np.array(values)
        
        n = len(x)
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator == 0:
            self.slope = 0
        else:
            self.slope = numerator / denominator
        
        self.intercept = y_mean - self.slope * x_mean
        
        # R-squared
        ss_res = np.sum((y - (self.slope * x + self.intercept)) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        self.r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Residual std
        self.residual_std = np.sqrt(ss_res / max(n - 2, 1))
    
    def predict(self, horizon: int, interval: int = 1) -> ForecastResult:
        """Generate forecast."""
        last_ts = self.timestamps[-1]
        interval_seconds = (self.timestamps[1] - self.timestamps[0]) if len(self.timestamps) > 1 else 900
        
        timestamps = []
        predictions = []
        lower_bounds = []
        upper_bounds = []
        
        for h in range(1, horizon + 1):
            ts = last_ts + h * interval_seconds
            pred = self.slope * ts + self.intercept
            margin = 1.96 * self.residual_std * np.sqrt(h)
            
            timestamps.append(ts)
            predictions.append(pred)
            lower_bounds.append(pred - margin)
            upper_bounds.append(pred + margin)
        
        return ForecastResult(
            metric_name="",
            timestamps=timestamps,
            predicted_values=predictions,
            lower_bound=lower_bounds,
            upper_bound=upper_bounds,
            confidence=self.r_squared,
            model_used="linear_regression",
            horizon_minutes=horizon * int(interval_seconds / 60)
        )

class MonteCarloProjector:
    """Projects threshold breach probability using Monte Carlo simulation."""
    
    def __init__(self, n_simulations: int = 1000):
        self.n_simulations = n_simulations
    
    def project_breach(self, values: List[float], threshold: float, 
                       horizon: int, interval_seconds: int = 900) -> dict:
        """Project probability of breaching threshold within horizon."""
        if len(values) < 10:
            return {"breach_probability": 0, "expected_time_to_breach": None}
        
        # Estimate drift and volatility from historical data
        returns = np.diff(values) / np.array(values[:-1])
        drift = np.mean(returns)
        volatility = np.std(returns)
        
        if volatility == 0:
            volatility = 0.001  # Minimum volatility
        
        current_value = values[-1]
        breach_times = []
        
        for _ in range(self.n_simulations):
            value = current_value
            for step in range(horizon):
                # Geometric Brownian Motion
                dt = interval_seconds / 86400  # Daily scale
                shock = np.random.normal(0, 1)
                value = value * np.exp((drift - 0.5 * volatility**2) * dt + 
                                       volatility * np.sqrt(dt) * shock)
                
                if value >= threshold:
                    breach_times.append(step * interval_seconds / 60)  # minutes
                    break
        
        breach_prob = len(breach_times) / self.n_simulations
        
        return {
            "breach_probability": round(breach_prob, 4),
            "expected_time_to_breach_minutes": round(np.mean(breach_times), 1) if breach_times else None,
            "breach_time_p10_minutes": round(np.percentile(breach_times, 10), 1) if breach_times else None,
            "breach_time_p90_minutes": round(np.percentile(breach_times, 90), 1) if breach_times else None,
            "current_value": current_value,
            "threshold": threshold,
            "drift_per_day": round(drift, 6),
            "volatility": round(volatility, 6)
        }
```

### 5.3 Predictive Alert Generator

```python
class PredictiveAlertGenerator:
    """Generates early-warning alerts before thresholds are breached."""
    
    def __init__(self, metrics_client, alert_manager):
        self.metrics = metrics_client
        self.alerts = alert_manager
        self.forecasters = {
            "holt_winters": HoltWintersForecaster(),
            "linear": LinearRegressionForecaster(),
        }
        self.mc_projector = MonteCarloProjector()
        self.prediction_history: Dict[str, List[dict]] = {}
        self.prediction_accuracy: Dict[str, List[bool]] = {}
    
    def evaluate_metric(self, metric_name: str, current_value: float,
                        historical_values: List[float], thresholds: dict) -> Optional[PredictiveAlert]:
        """Evaluate a metric for predictive alerting."""
        
        # Select best forecaster based on data characteristics
        forecaster = self._select_forecaster(historical_values)
        
        if forecaster is None:
            return None
        
        # Generate forecast
        timestamps = [time.time() - (len(historical_values) - i) * 900 
                     for i in range(len(historical_values))]
        
        try:
            forecaster.fit(timestamps, historical_values)
            forecast = forecaster.predict(horizon=12)  # 3 hours ahead at 15-min intervals
        except Exception:
            return None
        
        # Check each threshold
        for threshold_name, threshold_value in thresholds.items():
            # Check if any predicted value crosses threshold
            for i, (pred, lower, upper) in enumerate(zip(
                forecast.predicted_values, forecast.lower_bound, forecast.upper_bound
            )):
                if pred >= threshold_value:
                    minutes_to_breach = (i + 1) * 15
                    
                    # Calculate confidence
                    confidence = forecast.confidence * (1 - 0.05 * i)
                    
                    if confidence < 0.3:
                        continue
                    
                    # Determine severity based on time to breach
                    if minutes_to_breach <= 30:
                        severity = "P1"
                    elif minutes_to_breach <= 60:
                        severity = "P2"
                    else:
                        severity = "P3"
                    
                    alert = PredictiveAlert(
                        metric_name=metric_name,
                        alert_type="threshold_breach",
                        predicted_time=forecast.timestamps[i],
                        current_value=current_value,
                        predicted_value=pred,
                        threshold=threshold_value,
                        confidence=confidence,
                        time_to_breach_minutes=minutes_to_breach,
                        severity=severity,
                        recommended_action=self._recommend_action(
                            metric_name, threshold_name, minutes_to_breach
                        )
                    )
                    
                    self._record_prediction(alert)
                    return alert
        
        return None
    
    def evaluate_cost_overrun(self, metric_name: str, current_spend: float,
                               budget: float, historical_spend: List[float]) -> Optional[PredictiveAlert]:
        """Predict cost overrun before it happens."""
        
        projection = self.mc_projector.project_breach(
            historical_spend, budget, horizon=72  # 72 intervals = 18 hours at 15-min
        )
        
        if projection["breach_probability"] > 0.5:
            return PredictiveAlert(
                metric_name=metric_name,
                alert_type="cost_overrun",
                predicted_time=time.time() + projection["expected_time_to_breach_minutes"] * 60,
                current_value=current_spend,
                predicted_value=budget,
                threshold=budget,
                confidence=projection["breach_probability"],
                time_to_breach_minutes=projection["expected_time_to_breach_minutes"],
                severity="P2" if projection["breach_probability"] > 0.8 else "P3",
                recommended_action="Review cost optimization: enable caching, reduce sampling, or request budget increase"
            )
        
        return None
    
    def _select_forecaster(self, values: List[float]) -> Optional[ForecastingModel]:
        """Select best forecasting model based on data characteristics."""
        if len(values) < 20:
            return None
        
        # Check for seasonality
        if len(values) >= 192:  # 2 days of 15-min data
            return self.forecasters["holt_winters"]
        
        # Default to linear for shorter series
        return self.forecasters["linear"]
    
    def _recommend_action(self, metric_name: str, threshold_name: str, 
                          minutes_to_breach: float) -> str:
        """Generate recommended action based on metric and time to breach."""
        if minutes_to_breach <= 15:
            return f"URGENT: {metric_name} will breach {threshold_name} in {minutes_to_breach:.0f} min. Take immediate action."
        elif minutes_to_breach <= 60:
            return f"HIGH: {metric_name} trending toward {threshold_name}. Review within the hour."
        else:
            return f"MEDIUM: {metric_name} may breach {threshold_name} in {minutes_to_breach/60:.1f} hours. Plan mitigation."
    
    def _record_prediction(self, alert: PredictiveAlert):
        """Record prediction for accuracy tracking."""
        key = f"{alert.metric_name}:{alert.alert_type}"
        if key not in self.prediction_history:
            self.prediction_history[key] = []
        self.prediction_history[key].append({
            "timestamp": time.time(),
            "predicted_breach_time": alert.predicted_time,
            "confidence": alert.confidence
        })
    
    def get_prediction_accuracy(self) -> dict:
        """Calculate prediction accuracy metrics."""
        accuracy = {}
        for key, predictions in self.prediction_history.items():
            if not predictions:
                continue
            
            # Check if predicted breaches actually occurred
            correct = sum(1 for p in predictions if p.get("occurred", False))
            total = len(predictions)
            
            accuracy[key] = {
                "total_predictions": total,
                "correct_predictions": correct,
                "accuracy": round(correct / total, 4) if total > 0 else 0,
                "average_confidence": round(
                    np.mean([p["confidence"] for p in predictions]), 4
                )
            }
        
        return accuracy
```

### 5.4 Predictive Alert Configuration

```yaml
# predictive_alerting.config.yaml
predictive_alerting:
  enabled: true
  
  forecasting:
    models:
      holt_winters:
        enabled: true
        min_data_points: 192  # 2 days at 15-min intervals
        season_length: 96
        max_horizon: 48  # 12 hours ahead
      
      linear_regression:
        enabled: true
        min_data_points: 20
        max_horizon: 24  # 6 hours ahead
      
      monte_carlo:
        enabled: true
        simulations: 1000
        confidence_level: 0.95
  
  early_warning:
    enabled: true
    lookahead_minutes: [15, 30, 60, 120, 240]
    min_confidence: 0.5
    severity_mapping:
      - max_minutes: 15
        severity: P1
      - max_minutes: 60
        severity: P2
      - max_minutes: 240
        severity: P3
  
  cost_prediction:
    enabled: true
    budget_check_interval: 900  # 15 minutes
    forecast_horizon_hours: 24
    breach_probability_threshold: 0.5
    actions:
      - "Enable aggressive caching"
      - "Reduce sampling rates"
      - "Route to cheaper model"
      - "Request budget increase"
  
  capacity_prediction:
    enabled: true
    metrics:
      - agent_context_window_usage
      - llm_token_usage_total
      - evidence_queue_depth
    forecast_horizon_hours: 48
    threshold: 0.85  # 85% capacity
  
  model_selection:
    auto_select: true
    evaluation_window: 100  # Last N predictions to evaluate
    accuracy_threshold: 0.6  # Minimum accuracy to keep model active
```

---

## 6. Monitoring Data Quality

### 6.1 Data Quality Framework

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Data Quality Validation Pipeline                    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Completeness│  │  Accuracy    │  │  Timeliness  │             │
│  │  Validator   │  │  Validator   │  │  Validator   │             │
│  │              │  │              │  │              │             │
│  │ • Missing    │  │ • Range      │  │ • Staleness  │             │
│  │   data check │  │   validation │  │   detection  │             │
│  │ • Gap        │  │ • Outlier    │  │ • Delay      │             │
│  │   detection  │  │   detection  │  │   measurement│             │
│  │ • Coverage   │  │ • Cross-     │  │ • Clock skew │             │
│  │   analysis   │  │   source     │  │   detection  │             │
│  │              │  │   verify     │  │              │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                 │                      │
│         └────────────┬────┘                 │                      │
│                      │                      │                      │
│              ┌───────▼──────┐    ┌──────────▼──────────┐          │
│              │  Consistency │    │  Quality Score      │          │
│              │  Validator   │───→│  Aggregator         │          │
│              │              │    │                     │          │
│              │ • Cross-     │    │ • Overall DQ Score  │          │
│              │   metric     │    │ • DQ Grade (A-F)    │          │
│              │   checks     │    │ • DQ Trend          │          │
│              │ • Schema     │    │ • DQ Alerts         │          │
│              │   validation │    │                     │          │
│              └──────────────┘    └─────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Data Quality Validators

```python
# grc_claw/data_quality.py
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque
import time
import statistics

class DQGrade(Enum):
    A = "a"  # 95-100: Excellent
    B = "b"  # 85-94:  Good
    C = "c"  # 70-84:  Fair
    D = "d"  # 50-69:  Poor
    F = "f"  # 0-49:   Critical

@dataclass
class DQScore:
    metric_name: str
    completeness: float  # 0-1
    accuracy: float      # 0-1
    timeliness: float    # 0-1
    consistency: float   # 0-1
    overall: float       # 0-1
    grade: DQGrade
    issues: List[str]
    timestamp: float

class CompletenessValidator:
    """Validates that expected data is present."""
    
    def __init__(self, expected_interval: float = 15.0, 
                 max_missing_ratio: float = 0.05):
        self.expected_interval = expected_interval
        self.max_missing_ratio = max_missing_ratio
        self.timestamps: deque = deque(maxlen=10000)
    
    def record_timestamp(self, ts: float):
        """Record a data point timestamp."""
        self.timestamps.append(ts)
    
    def validate(self) -> Tuple[float, List[str]]:
        """Validate completeness and return score and issues."""
        issues = []
        
        if len(self.timestamps) < 2:
            return 0.0, ["insufficient_data"]
        
        # Check for gaps
        sorted_ts = sorted(self.timestamps)
        gaps = []
        for i in range(1, len(sorted_ts)):
            gap = sorted_ts[i] - sorted_ts[i-1]
            if gap > self.expected_interval * 2:
                gaps.append(gap)
        
        if gaps:
            total_gap = sum(gaps)
            expected_total = (len(sorted_ts) - 1) * self.expected_interval
            missing_ratio = total_gap / expected_total if expected_total > 0 else 0
            
            if missing_ratio > self.max_missing_ratio:
                issues.append(f"missing_data_ratio:{missing_ratio:.4f}")
        
        # Check recent data
        now = time.time()
        last_ts = sorted_ts[-1]
        staleness = now - last_ts
        
        if staleness > self.expected_interval * 4:
            issues.append(f"stale_data:{staleness:.0f}s")
        
        # Calculate completeness score
        if not issues:
            return 1.0, []
        
        # Score based on severity of issues
        score = 1.0
        for issue in issues:
            if issue.startswith("missing_data_ratio"):
                ratio = float(issue.split(":")[1])
                score -= ratio * 2
            elif issue.startswith("stale_data"):
                staleness = float(issue.split(":")[1])
                score -= min(staleness / 300, 0.5)
        
        return max(score, 0.0), issues

class AccuracyValidator:
    """Validates data accuracy through range checks and outlier detection."""
    
    def __init__(self, zscore_threshold: float = 4.0):
        self.zscore_threshold = zscore_threshold
        self.values: deque = deque(maxlen=1000)
        self.known_ranges: Dict[str, Tuple[float, float]] = {}
    
    def set_range(self, metric_name: str, min_val: float, max_val: float):
        """Set expected range for a metric."""
        self.known_ranges[metric_name] = (min_val, max_val)
    
    def validate(self, metric_name: str, value: float) -> Tuple[float, List[str]]:
        """Validate accuracy of a single value."""
        issues = []
        
        # Range check
        if metric_name in self.known_ranges:
            min_val, max_val = self.known_ranges[metric_name]
            if value < min_val or value > max_val:
                issues.append(f"out_of_range:[{min_val},{max_val}],value={value}")
        
        # Statistical outlier check
        self.values.append(value)
        if len(self.values) >= 30:
            mean = statistics.mean(self.values)
            std = statistics.stdev(self.values)
            if std > 0:
                zscore = abs(value - mean) / std
                if zscore > self.zscore_threshold:
                    issues.append(f"statistical_outlier:zscore={zscore:.2f}")
        
        # Negative value check for counters
        if metric_name.endswith("_total") and value < 0:
            issues.append("negative_counter")
        
        if not issues:
            return 1.0, []
        
        score = max(1.0 - len(issues) * 0.2, 0.0)
        return score, issues

class TimelinessValidator:
    """Validates that data arrives on time."""
    
    def __init__(self, max_delay_seconds: float = 60.0):
        self.max_delay = max_delay_seconds
        self.arrival_times: deque = deque(maxlen=1000)
        self.event_times: deque = deque(maxlen=1000)
    
    def record(self, event_time: float, arrival_time: Optional[float] = None):
        """Record event time and arrival time."""
        if arrival_time is None:
            arrival_time = time.time()
        self.event_times.append(event_time)
        self.arrival_times.append(arrival_time)
    
    def validate(self) -> Tuple[float, List[str]]:
        """Validate timeliness."""
        issues = []
        
        if len(self.arrival_times) < 2:
            return 1.0, []
        
        # Calculate delays
        delays = [arr - evt for arr, evt in zip(self.arrival_times, self.event_times)]
        avg_delay = statistics.mean(delays)
        p95_delay = sorted(delays)[int(len(delays) * 0.95)]
        
        if p95_delay > self.max_delay:
            issues.append(f"high_latency:p95={p95_delay:.1f}s")
        
        # Check for clock skew (negative delays)
        negative_delays = [d for d in delays if d < -1]
        if negative_delays:
            issues.append(f"clock_skew:{len(negative_delays)}_events")
        
        # Score
        if not issues:
            return 1.0, []
        
        score = max(1.0 - (p95_delay / self.max_delay) * 0.5, 0.0)
        return score, issues

class ConsistencyValidator:
    """Validates cross-metric consistency."""
    
    def __init__(self):
        self.cross_checks: List[dict] = []
        self.metric_values: Dict[str, deque] = {}
    
    def register_cross_check(self, name: str, metrics: List[str], 
                              check_type: str, params: dict):
        """Register a cross-metric consistency check."""
        self.cross_checks.append({
            "name": name,
            "metrics": metrics,
            "type": check_type,
            "params": params
        })
    
    def record_value(self, metric_name: str, value: float):
        """Record a metric value for consistency checking."""
        if metric_name not in self.metric_values:
            self.metric_values[metric_name] = deque(maxlen=1000)
        self.metric_values[metric_name].append(value)
    
    def validate(self) -> Tuple[float, List[str]]:
        """Run all consistency checks."""
        issues = []
        
        for check in self.cross_checks:
            if check["type"] == "sum_equals":
                # Check that sum of parts equals total
                parts = check["metrics"][:-1]
                total = check["metrics"][-1]
                
                if all(p in self.metric_values for p in parts + [total]):
                    part_sums = [sum(self.metric_values[p]) for p in parts]
                    total_sum = sum(self.metric_values[total])
                    
                    if total_sum > 0:
                        ratio = sum(part_sums) / total_sum
                        if abs(ratio - 1.0) > 0.01:
                            issues.append(f"sum_mismatch:{check['name']}:ratio={ratio:.4f}")
            
            elif check["type"] == "correlation":
                # Check that two metrics are correlated
                m1, m2 = check["metrics"]
                min_corr = check["params"].get("min_correlation", 0.8)
                
                if m1 in self.metric_values and m2 in self.metric_values:
                    v1 = list(self.metric_values[m1])
                    v2 = list(self.metric_values[m2])
                    min_len = min(len(v1), len(v2))
                    
                    if min_len >= 30:
                        v1 = v1[-min_len:]
                        v2 = v2[-min_len:]
                        corr = self._correlation(v1, v2)
                        if corr < min_corr:
                            issues.append(f"low_correlation:{check['name']}:corr={corr:.4f}")
        
        if not issues:
            return 1.0, []
        
        score = max(1.0 - len(issues) * 0.15, 0.0)
        return score, issues
    
    def _correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = len(x)
        if n < 2:
            return 0.0
        
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        std_x = (sum((xi - mean_x) ** 2 for xi in x)) ** 0.5
        std_y = (sum((yi - mean_y) ** 2 for yi in y)) ** 0.5
        
        if std_x == 0 or std_y == 0:
            return 0.0
        
        return cov / (std_x * std_y)

class DataQualityAggregator:
    """Aggregates all DQ validators and produces overall quality scores."""
    
    WEIGHTS = {
        "completeness": 0.30,
        "accuracy": 0.25,
        "timeliness": 0.25,
        "consistency": 0.20
    }
    
    def __init__(self):
        self.completeness = CompletenessValidator()
        self.accuracy = AccuracyValidator()
        self.timeliness = TimelinessValidator()
        self.consistency = ConsistencyValidator()
        self.scores: Dict[str, DQScore] = {}
    
    def evaluate(self, metric_name: str) -> DQScore:
        """Evaluate overall data quality for a metric."""
        c_score, c_issues = self.completeness.validate()
        a_score, a_issues = self.accuracy.validate(metric_name, 0)  # Last value
        t_score, t_issues = self.timeliness.validate()
        s_score, s_issues = self.consistency.validate()
        
        overall = (
            c_score * self.WEIGHTS["completeness"] +
            a_score * self.WEIGHTS["accuracy"] +
            t_score * self.WEIGHTS["timeliness"] +
            s_score * self.WEIGHTS["consistency"]
        )
        
        all_issues = c_issues + a_issues + t_issues + s_issues
        grade = self._score_to_grade(overall)
        
        score = DQScore(
            metric_name=metric_name,
            completeness=c_score,
            accuracy=a_score,
            timeliness=t_score,
            consistency=s_score,
            overall=overall,
            grade=grade,
            issues=all_issues,
            timestamp=time.time()
        )
        
        self.scores[metric_name] = score
        return score
    
    def _score_to_grade(self, score: float) -> DQGrade:
        """Convert numeric score to letter grade."""
        pct = score * 100
        if pct >= 95:
            return DQGrade.A
        elif pct >= 85:
            return DQGrade.B
        elif pct >= 70:
            return DQGrade.C
        elif pct >= 50:
            return DQGrade.D
        else:
            return DQGrade.F
    
    def get_overall_health(self) -> dict:
        """Get overall data quality health."""
        if not self.scores:
            return {"status": "no_data", "overall_score": 0}
        
        scores = [s.overall for s in self.scores.values()]
        grades = [s.grade for s in self.scores.values()]
        
        grade_counts = {}
        for g in grades:
            grade_counts[g.value] = grade_counts.get(g.value, 0) + 1
        
        return {
            "overall_score": round(statistics.mean(scores), 4),
            "overall_grade": self._score_to_grade(statistics.mean(scores)).value,
            "metric_count": len(self.scores),
            "grade_distribution": grade_counts,
            "failing_metrics": [
                {"metric": s.metric_name, "score": s.overall, "issues": s.issues}
                for s in self.scores.values()
                if s.grade in (DQGrade.D, DQGrade.F)
            ],
            "timestamp": time.time()
        }
```

### 6.3 Data Quality Configuration

```yaml
# data_quality.config.yaml
data_quality:
  enabled: true
  
  validation:
    interval: 60  # Run validation every 60 seconds
    metrics: all  # Validate all metrics
    
    completeness:
      expected_interval_seconds: 15
      max_missing_ratio: 0.05
      max_staleness_seconds: 300
    
    accuracy:
      zscore_threshold: 4.0
      range_checks:
        llm_error_rate: [0, 1]
        llm_success_rate: [0, 1]
        llm_quality_score: [0, 1]
        toxicity_score: [0, 1]
        anomaly_score: [0, 1]
        agent_context_window_usage: [0, 1]
        guard_pass_rate: [0, 1]
        guard_false_positive_rate: [0, 1]
        guard_false_negative_rate: [0, 1]
    
    timeliness:
      max_delay_seconds: 60
      clock_skew_threshold_seconds: 1
    
    consistency:
      cross_checks:
        - name: "token_sum"
          type: sum_equals
          metrics:
            - lm_token_usage_total{type=input}
            - lm_token_usage_total{type=output}
            - lm_token_usage_total{type=total}
        
        - name: "cost_correlation"
          type: correlation
          metrics:
            - lm_token_usage_total
            - lm_cost_total
          min_correlation: 0.95
  
  scoring:
    weights:
      completeness: 0.30
      accuracy: 0.25
      timeliness: 0.25
      consistency: 0.20
    
    grades:
      A: { min: 95, description: "Excellent" }
      B: { min: 85, description: "Good" }
      C: { min: 70, description: "Fair" }
      D: { min: 50, description: "Poor" }
      F: { min: 0,  description: "Critical" }
  
  alerting:
    enabled: true
    rules:
      - name: "dq_grade_dropped"
        condition: "grade in [D, F]"
        severity: P2
        message: "Data quality for {{ metric }} is {{ grade }}"
      
      - name: "dq_score_dropped"
        condition: "overall < 0.7"
        severity: P2
        message: "Overall DQ score is {{ score }}"
      
      - name: "completeness_breach"
        condition: "completeness < 0.9"
        severity: P1
        message: "Data completeness for {{ metric }} is {{ value }}"
  
  remediation:
    auto_heal: true
    actions:
      - condition: "completeness < 0.8"
        action: "restart_collector"
      - condition: "accuracy < 0.6"
        action: "flag_for_review"
      - condition: "timeliness < 0.7"
        action: "increase_scrape_frequency"
      - condition: "consistency < 0.6"
        action: "run_diagnostic"
```

---

## 7. Monitoring System Self-Health

### 7.1 Self-Health Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                 Monitoring System Self-Health                        │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Pipeline    │  │  Storage     │  │  Alerting    │             │
│  │  Health      │  │  Health      │  │  Health      │             │
│  │              │  │              │  │              │             │
│  │ • Collector  │  │ • TSDB       │  │ • Alert      │             │
│  │   status     │  │   capacity   │  │   delivery   │             │
│  │ • Queue      │  │ • Write      │  │   success    │             │
│  │   depth      │  │   latency    │  │ • Routing    │             │
│  │ • Lag        │  │ • Query      │  │   accuracy   │             │
│  │   detection  │  │   latency    │  │ • Dedup      │             │
│  │ • Drop       │  │ • Retention  │  │   accuracy   │             │
│  │   rate       │  │   compliance │  │ • Flapping   │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                 │                      │
│         └────────────┬────┘                 │                      │
│                      │                      │                      │
│              ┌───────▼──────┐    ┌──────────▼──────────┐          │
│              │  Component   │    │  Self-Health        │          │
│              │  Health      │───→│  Aggregator         │          │
│              │  Monitors    │    │                     │          │
│              │              │    │ • Overall Health    │          │
│              │ • Prometheus │    │   Score             │          │
│              │ • Grafana    │    │ • Component Status  │          │
│              │ • Alert Mgr  │    │ • Self-Healing      │          │
│              │ • Kafka      │    │   Actions           │          │
│              │ • Langfuse   │    │ • Meta-Alerts       │          │
│              │ • Arize      │    │                     │          │
│              └──────────────┘    └─────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Self-Health Monitors

```python
# grc_claw/self_health.py
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import time
import statistics

class ComponentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DOWN = "down"

@dataclass
class ComponentHealth:
    name: str
    status: ComponentStatus
    health_score: float  # 0-1
    last_check: float
    metrics: Dict[str, float]
    issues: List[str]
    consecutive_failures: int

class PipelineHealthMonitor:
    """Monitors the health of the metric collection pipeline."""
    
    def __init__(self):
        self.collector_status: Dict[str, dict] = {}
        self.queue_depths: deque = deque(maxlen=1000)
        self.lag_measurements: deque = deque(maxlen=1000)
        self.drop_rates: deque = deque(maxlen=1000)
    
    def check_collector(self, name: str, last_success: float, 
                        failure_count: int) -> ComponentHealth:
        """Check health of a metric collector."""
        now = time.time()
        time_since_success = now - last_success
        
        issues = []
        status = ComponentStatus.HEALTHY
        score = 1.0
        
        if time_since_success > 300:
            status = ComponentStatus.DOWN
            score = 0.0
            issues.append(f"no_data_for_{time_since_success:.0f}s")
        elif time_since_success > 60:
            status = ComponentStatus.UNHEALTHY
            score = 0.3
            issues.append(f"delayed_data:{time_since_success:.0f}s")
        elif time_since_success > 30:
            status = ComponentStatus.DEGRADED
            score = 0.7
            issues.append(f"slow_data:{time_since_success:.0f}s")
        
        if failure_count > 5:
            status = ComponentStatus.UNHEALTHY
            score = min(score, 0.2)
            issues.append(f"high_failure_count:{failure_count}")
        elif failure_count > 0:
            score = min(score, 0.8)
            issues.append(f"failures:{failure_count}")
        
        return ComponentHealth(
            name=name,
            status=status,
            health_score=score,
            last_check=now,
            metrics={
                "time_since_success_seconds": time_since_success,
                "failure_count": failure_count
            },
            issues=issues,
            consecutive_failures=failure_count
        )
    
    def check_queue_health(self, queue_name: str, depth: int, 
                           max_depth: int) -> ComponentHealth:
        """Check health of a message queue."""
        self.queue_depths.append(depth)
        
        issues = []
        status = ComponentStatus.HEALTHY
        score = 1.0
        
        utilization = depth / max_depth if max_depth > 0 else 0
        
        if utilization > 0.95:
            status = ComponentStatus.DOWN
            score = 0.0
            issues.append(f"queue_full:{depth}/{max_depth}")
        elif utilization > 0.80:
            status = ComponentStatus.UNHEALTHY
            score = 0.3
            issues.append(f"queue_near_full:{depth}/{max_depth}")
        elif utilization > 0.60:
            status = ComponentStatus.DEGRADED
            score = 0.7
            issues.append(f"queue_elevated:{depth}/{max_depth}")
        
        # Check for growing trend
        if len(self.queue_depths) >= 10:
            recent = list(self.queue_depths)[-10:]
            if all(recent[i] <= recent[i+1] for i in range(len(recent)-1)):
                issues.append("queue_growing")
                score = min(score, 0.5)
        
        return ComponentHealth(
            name=f"queue:{queue_name}",
            status=status,
            health_score=score,
            last_check=time.time(),
            metrics={
                "depth": depth,
                "max_depth": max_depth,
                "utilization": utilization
            },
            issues=issues,
            consecutive_failures=0
        )
    
    def check_pipeline_lag(self, source: str, event_time: float, 
                           processing_time: float) -> ComponentHealth:
        """Check end-to-end pipeline lag."""
        lag = processing_time - event_time
        self.lag_measurements.append(lag)
        
        issues = []
        status = ComponentStatus.HEALTHY
        score = 1.0
        
        if lag > 300:
            status = ComponentStatus.UNHEALTHY
            score = 0.2
            issues.append(f"high_lag:{lag:.0f}s")
        elif lag > 60:
            status = ComponentStatus.DEGRADED
            score = 0.6
            issues.append(f"elevated_lag:{lag:.0f}s")
        elif lag > 15:
            score = 0.9
            issues.append(f"minor_lag:{lag:.0f}s")
        
        return ComponentHealth(
            name=f"lag:{source}",
            status=status,
            health_score=score,
            last_check=time.time(),
            metrics={"lag_seconds": lag},
            issues=issues,
            consecutive_failures=0
        )

class StorageHealthMonitor:
    """Monitors the health of monitoring storage systems."""
    
    def __init__(self):
        self.write_latencies: deque = deque(maxlen=1000)
        self.query_latencies: deque = deque(maxlen=1000)
        self.disk_usage: deque = deque(maxlen=100)
    
    def check_prometheus_health(self, write_latency: float, 
                                 query_latency: float,
                                 disk_usage_pct: float,
                                 retention_days: int) -> ComponentHealth:
        """Check Prometheus TSDB health."""
        self.write_latencies.append(write_latency)
        self.query_latencies.append(query_latency)
        self.disk_usage.append(disk_usage_pct)
        
        issues = []
        status = ComponentStatus.HEALTHY
        score = 1.0
        
        # Write latency
        if write_latency > 5.0:
            status = ComponentStatus.UNHEALTHY
            score = 0.2
            issues.append(f"high_write_latency:{write_latency:.1f}s")
        elif write_latency > 1.0:
            status = ComponentStatus.DEGRADED
            score = min(score, 0.6)
            issues.append(f"elevated_write_latency:{write_latency:.1f}s")
        
        # Query latency
        if query_latency > 10.0:
            status = ComponentStatus.UNHEALTHY
            score = min(score, 0.3)
            issues.append(f"high_query_latency:{query_latency:.1f}s")
        elif query_latency > 2.0:
            score = min(score, 0.7)
            issues.append(f"elevated_query_latency:{query_latency:.1f}s")
        
        # Disk usage
        if disk_usage_pct > 90:
            status = ComponentStatus.DOWN
            score = 0.0
            issues.append(f"disk_critical:{disk_usage_pct:.1f}%")
        elif disk_usage_pct > 80:
            status = ComponentStatus.DEGRADED
            score = min(score, 0.5)
            issues.append(f"disk_high:{disk_usage_pct:.1f}%")
        
        # Retention compliance
        if retention_days < 30:
            score = min(score, 0.5)
            issues.append(f"low_retention:{retention_days}d")
        
        return ComponentHealth(
            name="storage:prometheus",
            status=status,
            health_score=score,
            last_check=time.time(),
            metrics={
                "write_latency_seconds": write_latency,
                "query_latency_seconds": query_latency,
                "disk_usage_pct": disk_usage_pct,
                "retention_days": retention_days
            },
            issues=issues,
            consecutive_failures=0
        )

class AlertingHealthMonitor:
    """Monitors the health of the alerting system."""
    
    def __init__(self):
        self.delivery_results: deque = deque(maxlen=1000)
        self.alert_counts: deque = deque(maxlen=100)
        self.flapping_alerts: Dict[str, int] = {}
    
    def record_delivery(self, alert_id: str, channel: str, 
                        success: bool, latency: float):
        """Record an alert delivery attempt."""
        self.delivery_results.append({
            "alert_id": alert_id,
            "channel": channel,
            "success": success,
            "latency": latency,
            "timestamp": time.time()
        })
    
    def check_delivery_health(self) -> ComponentHealth:
        """Check alert delivery health."""
        issues = []
        status = ComponentStatus.HEALTHY
        score = 1.0
        
        if not self.delivery_results:
            return ComponentHealth(
                name="alerting:delivery",
                status=ComponentStatus.HEALTHY,
                health_score=1.0,
                last_check=time.time(),
                metrics={},
                issues=[],
                consecutive_failures=0
            )
        
        recent = [r for r in self.delivery_results 
                 if time.time() - r["timestamp"] < 3600]
        
        if not recent:
            return ComponentHealth(
                name="alerting:delivery",
                status=ComponentStatus.DEGRADED,
                health_score=0.5,
                last_check=time.time(),
                metrics={"recent_deliveries": 0},
                issues=["no_recent_deliveries"],
                consecutive_failures=0
            )
        
        success_rate = sum(1 for r in recent if r["success"]) / len(recent)
        avg_latency = statistics.mean([r["latency"] for r in recent])
        
        if success_rate < 0.95:
            status = ComponentStatus.UNHEALTHY
            score = 0.3
            issues.append(f"low_delivery_success:{success_rate:.2%}")
        elif success_rate < 0.99:
            status = ComponentStatus.DEGRADED
            score = 0.7
            issues.append(f"delivery_degraded:{success_rate:.2%}")
        
        if avg_latency > 30:
            score = min(score, 0.5)
            issues.append(f"high_delivery_latency:{avg_latency:.1f}s")
        
        return ComponentHealth(
            name="alerting:delivery",
            status=status,
            health_score=score,
            last_check=time.time(),
            metrics={
                "success_rate": success_rate,
                "avg_latency_seconds": avg_latency,
                "total_deliveries_1h": len(recent)
            },
            issues=issues,
            consecutive_failures=0
        )
    
    def check_flapping(self, alert_name: str, threshold: int = 10, 
                       window_hours: int = 1) -> Optional[ComponentHealth]:
        """Check for flapping alerts."""
        count = self.flapping_alerts.get(alert_name, 0)
        
        if count > threshold:
            return ComponentHealth(
                name=f"alerting:flapping:{alert_name}",
                status=ComponentStatus.DEGRADED,
                health_score=0.4,
                last_check=time.time(),
                metrics={"flap_count": count, "threshold": threshold},
                issues=[f"flapping_alert:{count}_in_{window_hours}h"],
                consecutive_failures=0
            )
        return None

class SelfHealthAggregator:
    """Aggregates all self-health monitors into overall system health."""
    
    def __init__(self):
        self.pipeline = PipelineHealthMonitor()
        self.storage = StorageHealthMonitor()
        self.alerting = AlertingHealthMonitor()
        self.component_health: Dict[str, ComponentHealth] = {}
    
    def register_component(self, name: str, health: ComponentHealth):
        """Register a component's health."""
        self.component_health[name] = health
    
    def get_overall_health(self) -> dict:
        """Calculate overall monitoring system health."""
        if not self.component_health:
            return {"status": "unknown", "score": 0}
        
        scores = [h.health_score for h in self.component_health.values()]
        overall_score = statistics.mean(scores)
        
        # Determine overall status
        statuses = [h.status for h in self.component_health.values()]
        if ComponentStatus.DOWN in statuses:
            overall_status = "down"
        elif ComponentStatus.UNHEALTHY in statuses:
            overall_status = "unhealthy"
        elif ComponentStatus.DEGRADED in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Collect all issues
        all_issues = []
        for h in self.component_health.values():
            all_issues.extend([f"{h.name}:{issue}" for issue in h.issues])
        
        return {
            "status": overall_status,
            "health_score": round(overall_score, 4),
            "component_count": len(self.component_health),
            "components": {
                name: {
                    "status": h.status.value,
                    "score": h.health_score,
                    "issues": h.issues
                }
                for name, h in self.component_health.items()
            },
            "all_issues": all_issues,
            "timestamp": time.time()
        }
    
    def get_self_healing_actions(self) -> List[dict]:
        """Generate self-healing actions based on health status."""
        actions = []
        
        for name, health in self.component_health.items():
            if health.status == ComponentStatus.DOWN:
                actions.append({
                    "component": name,
                    "action": "restart",
                    "priority": "critical",
                    "reason": f"Component is down: {health.issues}"
                })
            elif health.status == ComponentStatus.UNHEALTHY:
                actions.append({
                    "component": name,
                    "action": "investigate_and_heal",
                    "priority": "high",
                    "reason": f"Component unhealthy: {health.issues}"
                })
            elif health.status == ComponentStatus.DEGRADED:
                actions.append({
                    "component": name,
                    "action": "monitor_closely",
                    "priority": "medium",
                    "reason": f"Component degraded: {health.issues}"
                })
        
        return actions
```

### 7.3 Self-Health Configuration

```yaml
# self_health.config.yaml
self_health:
  enabled: true
  
  check_interval_seconds: 10
  
  components:
    collectors:
      - name: langfuse_collector
        type: collector
        health_check:
          max_time_since_success: 60
          max_failure_count: 3
      
      - name: arize_collector
        type: collector
        health_check:
          max_time_since_success: 300
          max_failure_count: 3
      
      - name: prometheus_collector
        type: collector
        health_check:
          max_time_since_success: 30
          max_failure_count: 5
      
      - name: datadog_collector
        type: collector
        health_check:
          max_time_since_success: 60
          max_failure_count: 3
    
    pipeline:
      - name: kafka_queue
        type: queue
        health_check:
          max_depth: 10000
          max_utilization: 0.80
          max_growth_rate: 100  # per minute
      
      - name: telemetry_bus
        type: queue
        health_check:
          max_depth: 50000
          max_utilization: 0.70
    
    storage:
      - name: prometheus_tsdb
        type: storage
        health_check:
          max_write_latency_seconds: 5
          max_query_latency_seconds: 10
          max_disk_usage_pct: 80
          min_retention_days: 30
      
      - name: langfuse_store
        type: storage
        health_check:
          max_write_latency_seconds: 10
          max_disk_usage_pct: 85
      
      - name: datadog_store
        type: storage
        health_check:
          max_write_latency_seconds: 5
    
    alerting:
      - name: alertmanager
        type: alerting
        health_check:
          min_delivery_success_rate: 0.95
          max_delivery_latency_seconds: 30
          max_flapping_alerts_per_hour: 10
  
  self_healing:
    enabled: true
    actions:
      restart:
        enabled: true
        max_restarts_per_hour: 3
        cooldown_seconds: 300
      
      scale_up:
        enabled: true
        trigger: "queue_utilization > 0.80 for 5m"
        max_scale_factor: 2
      
      circuit_break:
        enabled: true
        trigger: "failure_count > 5"
        timeout_seconds: 300
      
      failover:
        enabled: true
        trigger: "primary_down"
        auto_failover: true
  
  meta_alerts:
    enabled: true
    rules:
      - name: "monitoring_pipeline_down"
        condition: "overall_health_score < 0.3"
        severity: P0
        message: "Monitoring pipeline is critically unhealthy"
      
      - name: "monitoring_degraded"
        condition: "overall_health_score < 0.7"
        severity: P1
        message: "Monitoring system is degraded"
      
      - name: "data_loss_detected"
        condition: "completeness < 0.5"
        severity: P0
        message: "Significant data loss detected in monitoring pipeline"
      
      - name: "alert_delivery_failing"
        condition: "alert_delivery_success_rate < 0.9"
        severity: P1
        message: "Alert delivery is failing"
```

---

## 8. Monitoring Cost Optimization

### 8.1 Cost Optimization Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                Monitoring Cost Optimization Engine                    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Cost        │  │  Value       │  │  Optimization│             │
│  │  Analyzer    │  │  Assessor    │  │  Engine      │             │
│  │              │  │              │  │              │             │
│  │ • Per-metric │  │ • Alert      │  │ • Sampling   │             │
│  │   cost       │  │   value      │  │   tuning     │             │
│  │ • Per-source │  │ • Dashboard  │  │ • Retention  │             │
│  │   cost       │  │   usage      │  │   tuning     │             │
│  │ • Storage    │  │ • Metric     │  │ • Storage    │             │
│  │   cost       │  │   coverage   │  │   tiering    │             │
│  │ • Ingestion  │  │ • DQ score   │  │ • Query      │             │
│  │   cost       │  │   vs cost    │  │   optimization│            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                 │                      │
│         └────────────┬────┘                 │                      │
│                      │                      │                      │
│              ┌───────▼──────┐    ┌──────────▼──────────┐          │
│              │  Cost        │    │  Optimization       │          │
│              │  Aggregator  │───→│  Actions            │          │
│              │              │    │                     │          │
│              │ • Daily cost │    │ • Auto-apply        │          │
│              │ • Cost trend │    │ • Recommend          │          │
│              │ • Budget     │    │ • Approval          │          │
│              │   tracking   │    │   workflow          │          │
│              └──────────────┘    └─────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Cost Analyzer

```python
# grc_claw/cost_optimization.py
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import time
import statistics

@dataclass
class MetricCost:
    metric_name: str
    ingestion_cost_per_day: float
    storage_cost_per_day: float
    query_cost_per_day: float
    total_cost_per_day: float
    sample_count_per_day: int
    value_score: float  # 0-1, based on alert coverage and usage
    cost_efficiency: float  # value_score / total_cost

@dataclass
class CostBudget:
    daily_budget: float
    monthly_budget: float
    alert_budget_pct: float  # % of budget for alerting
    storage_budget_pct: float  # % of budget for storage
    ingestion_budget_pct: float  # % of budget for ingestion

class CostAnalyzer:
    """Analyzes monitoring costs across all dimensions."""
    
    # Cost rates (USD)
    COST_RATES = {
        "prometheus_ingestion_per_sample": 0.00001,
        "prometheus_storage_per_sample_day": 0.000001,
        "datadog_ingestion_per_sample": 0.0001,
        "datadog_storage_per_sample_day": 0.00001,
        "langfuse_trace": 0.001,
        "arize_prediction": 0.0005,
        "kafka_ingestion_per_message": 0.000001,
        "alert_delivery": 0.01,
        "dashboard_view": 0.10,  # per view
        "query_execution": 0.001,  # per query
    }
    
    def __init__(self, budget: CostBudget):
        self.budget = budget
        self.metric_costs: Dict[str, MetricCost] = {}
        self.daily_costs: deque = deque(maxlen=365)
        self.cost_by_category: Dict[str, float] = defaultdict(float)
        self.cost_by_source: Dict[str, float] = defaultdict(float)
    
    def calculate_metric_cost(self, metric_name: str, sample_count: int,
                              storage_size_bytes: float, query_count: int,
                              value_score: float) -> MetricCost:
        """Calculate total cost for a single metric."""
        ingestion_cost = sample_count * self.COST_RATES["prometheus_ingestion_per_sample"]
        storage_cost = storage_size_bytes * self.COST_RATES["prometheus_storage_per_sample_day"]
        query_cost = query_count * self.COST_RATES["query_execution"]
        
        total = ingestion_cost + storage_cost + query_cost
        
        return MetricCost(
            metric_name=metric_name,
            ingestion_cost_per_day=round(ingestion_cost, 4),
            storage_cost_per_day=round(storage_cost, 4),
            query_cost_per_day=round(query_cost, 4),
            total_cost_per_day=round(total, 4),
            sample_count_per_day=sample_count,
            value_score=value_score,
            cost_efficiency=round(value_score / max(total, 0.0001), 4)
        )
    
    def calculate_daily_cost(self, metrics_data: List[dict]) -> dict:
        """Calculate total daily monitoring cost."""
        total = 0.0
        by_category = defaultdict(float)
        by_source = defaultdict(float)
        
        for metric in metrics_data:
            cost = self.calculate_metric_cost(
                metric_name=metric["name"],
                sample_count=metric.get("sample_count", 0),
                storage_size_bytes=metric.get("storage_bytes", 0),
                query_count=metric.get("query_count", 0),
                value_score=metric.get("value_score", 0.5)
            )
            self.metric_costs[metric["name"]] = cost
            total += cost.total_cost_per_day
            
            by_category["ingestion"] += cost.ingestion_cost_per_day
            by_category["storage"] += cost.storage_cost_per_day
            by_category["query"] += cost.query_cost_per_day
            by_source[metric.get("source", "unknown")] += cost.total_cost_per_day
        
        self.daily_costs.append({
            "date": time.time(),
            "total": total,
            "by_category": dict(by_category),
            "by_source": dict(by_source)
        })
        
        return {
            "total_daily_cost": round(total, 2),
            "total_monthly_projected": round(total * 30, 2),
            "budget_utilization": round(total / self.budget.daily_budget, 4),
            "by_category": {k: round(v, 2) for k, v in by_category.items()},
            "by_source": {k: round(v, 2) for k, v in by_source.items()},
            "top_expensive_metrics": self._get_top_expensive(10),
            "least_efficient_metrics": self._get_least_efficient(10)
        }
    
    def _get_top_expensive(self, n: int) -> List[dict]:
        """Get top N most expensive metrics."""
        sorted_metrics = sorted(
            self.metric_costs.values(),
            key=lambda m: m.total_cost_per_day,
            reverse=True
        )
        return [
            {
                "metric": m.metric_name,
                "daily_cost": m.total_cost_per_day,
                "sample_count": m.sample_count_per_day,
                "cost_per_sample": round(m.total_cost_per_day / max(m.sample_count_per_day, 1), 6)
            }
            for m in sorted_metrics[:n]
        ]
    
    def _get_least_efficient(self, n: int) -> List[dict]:
        """Get top N least cost-efficient metrics."""
        sorted_metrics = sorted(
            self.metric_costs.values(),
            key=lambda m: m.cost_efficiency
        )
        return [
            {
                "metric": m.metric_name,
                "daily_cost": m.total_cost_per_day,
                "value_score": m.value_score,
                "efficiency": m.cost_efficiency
            }
            for m in sorted_metrics[:n]
        ]
    
    def get_cost_trend(self, days: int = 30) -> dict:
        """Get cost trend over time."""
        recent = list(self.daily_costs)[-days:]
        
        if len(recent) < 2:
            return {"trend": "insufficient_data"}
        
        costs = [r["total"] for r in recent]
        avg_cost = statistics.mean(costs)
        trend_slope = self._calculate_slope(costs)
        
        return {
            "period_days": len(recent),
            "average_daily_cost": round(avg_cost, 2),
            "trend_direction": "increasing" if trend_slope > 0.01 else 
                             "decreasing" if trend_slope < -0.01 else "stable",
            "trend_slope": round(trend_slope, 6),
            "projected_monthly": round(avg_cost * 30, 2),
            "budget_forecast": round(avg_cost * 30 / self.budget.monthly_budget, 4)
        }
    
    def _calculate_slope(self, values: List[float]) -> float:
        """Calculate linear trend slope."""
        n = len(values)
        if n < 2:
            return 0.0
        
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        
        return numerator / denominator if denominator != 0 else 0.0

class ValueAssessor:
    """Assesses the value of monitoring metrics relative to their cost."""
    
    def __init__(self):
        self.alert_coverage: Dict[str, int] = {}
        self.dashboard_usage: Dict[str, int] = {}
        self.query_frequency: Dict[str, int] = {}
        self.incident_correlation: Dict[str, int] = {}
    
    def calculate_value_score(self, metric_name: str) -> float:
        """Calculate value score (0-1) for a metric."""
        # Factors that contribute to value
        alert_count = self.alert_coverage.get(metric_name, 0)
        dashboard_views = self.dashboard_usage.get(metric_name, 0)
        query_count = self.query_frequency.get(metric_name, 0)
        incident_count = self.incident_correlation.get(metric_name, 0)
        
        # Weighted scoring
        score = 0.0
        
        # Alert coverage (0-0.4): metrics that trigger alerts are valuable
        if alert_count > 0:
            score += min(0.4, 0.1 * alert_count)
        
        # Dashboard usage (0-0.3): metrics viewed on dashboards
        if dashboard_views > 0:
            score += min(0.3, 0.05 * dashboard_views)
        
        # Query frequency (0-0.2): metrics queried regularly
        if query_count > 0:
            score += min(0.2, 0.02 * query_count)
        
        # Incident correlation (0-0.1): metrics correlated with incidents
        if incident_count > 0:
            score += min(0.1, 0.05 * incident_count)
        
        return min(score, 1.0)
    
    def get_low_value_metrics(self, threshold: float = 0.2) -> List[dict]:
        """Identify metrics with low value relative to cost."""
        low_value = []
        for metric_name in set(list(self.alert_coverage.keys()) + 
                               list(self.dashboard_usage.keys())):
            score = self.calculate_value_score(metric_name)
            if score < threshold:
                low_value.append({
                    "metric": metric_name,
                    "value_score": score,
                    "alert_count": self.alert_coverage.get(metric_name, 0),
                    "dashboard_views": self.dashboard_usage.get(metric_name, 0),
                    "query_count": self.query_frequency.get(metric_name, 0)
                })
        return sorted(low_value, key=lambda x: x["value_score"])

class OptimizationEngine:
    """Generates and applies cost optimization actions."""
    
    def __init__(self, cost_analyzer: CostAnalyzer, value_assessor: ValueAssessor):
        self.cost_analyzer = cost_analyzer
        self.value_assessor = value_assessor
        self.optimization_history: List[dict] = []
    
    def generate_recommendations(self) -> List[dict]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        # 1. Identify over-sampled metrics
        for metric_name, cost in self.cost_analyzer.metric_costs.items():
            if cost.sample_count_per_day > 100000 and cost.value_score < 0.3:
                recommendations.append({
                    "type": "reduce_sampling",
                    "metric": metric_name,
                    "current_samples_per_day": cost.sample_count_per_day,
                    "recommended_samples_per_day": int(cost.sample_count_per_day * 0.5),
                    "estimated_savings_per_day": round(cost.total_cost_per_day * 0.5, 2),
                    "impact": "low",
                    "reason": "High sample count with low value score"
                })
        
        # 2. Identify unused metrics
        low_value = self.value_assessor.get_low_value_metrics(threshold=0.1)
        for metric in low_value:
            cost = self.cost_analyzer.metric_costs.get(metric["metric"])
            if cost and cost.total_cost_per_day > 1.0:
                recommendations.append({
                    "type": "deprecate_metric",
                    "metric": metric["metric"],
                    "estimated_savings_per_day": cost.total_cost_per_day,
                    "impact": "low",
                    "reason": f"Value score {metric['value_score']:.2f} is very low"
                })
        
        # 3. Storage tiering recommendations
        for metric_name, cost in self.cost_analyzer.metric_costs.items():
            if cost.storage_cost_per_day > 10.0:
                recommendations.append({
                    "type": "tier_storage",
                    "metric": metric_name,
                    "current_storage_cost_per_day": cost.storage_cost_per_day,
                    "recommended_tier": "cold",
                    "estimated_savings_per_day": round(cost.storage_cost_per_day * 0.7, 2),
                    "impact": "medium",
                    "reason": "High storage cost — move to cold tier with lower resolution"
                })
        
        # 4. Query optimization
        for metric_name, cost in self.cost_analyzer.metric_costs.items():
            if cost.query_cost_per_day > 5.0:
                recommendations.append({
                    "type": "optimize_queries",
                    "metric": metric_name,
                    "current_query_cost_per_day": cost.query_cost_per_day,
                    "estimated_savings_per_day": round(cost.query_cost_per_day * 0.6, 2),
                    "impact": "low",
                    "reason": "High query cost — add caching or pre-aggregation"
                })
        
        # 5. Alert consolidation
        # Group similar alerts and recommend consolidation
        recommendations.append({
            "type": "consolidate_alerts",
            "description": "Consolidate similar alerts to reduce notification cost",
            "estimated_savings_per_day": 5.0,
            "impact": "low",
            "reason": "Alert fatigue and delivery costs can be reduced"
        })
        
        return sorted(recommendations, key=lambda x: -x.get("estimated_savings_per_day", 0))
    
    def apply_optimization(self, recommendation: dict, auto_apply: bool = False) -> dict:
        """Apply an optimization recommendation."""
        result = {
            "recommendation": recommendation,
            "applied": False,
            "timestamp": time.time(),
            "actual_savings": 0.0
        }
        
        if not auto_apply and recommendation.get("impact") != "low":
            result["status"] = "pending_approval"
            return result
        
        # Apply based on type
        if recommendation["type"] == "reduce_sampling":
            # Would integrate with sampling controller
            result["applied"] = True
            result["actual_savings"] = recommendation["estimated_savings_per_day"]
        
        elif recommendation["type"] == "tier_storage":
            # Would integrate with storage tiering
            result["applied"] = True
            result["actual_savings"] = recommendation["estimated_savings_per_day"]
        
        elif recommendation["type"] == "optimize_queries":
            # Would integrate with query cache
            result["applied"] = True
            result["actual_savings"] = recommendation["estimated_savings_per_day"]
        
        self.optimization_history.append(result)
        return result
    
    def get_optimization_report(self) -> dict:
        """Generate optimization effectiveness report."""
        if not self.optimization_history:
            return {"status": "no_optimizations_applied"}
        
        total_estimated = sum(
            r["recommendation"].get("estimated_savings_per_day", 0)
            for r in self.optimization_history
        )
        total_actual = sum(r.get("actual_savings", 0) for r in self.optimization_history)
        
        return {
            "total_optimizations": len(self.optimization_history),
            "applied_optimizations": sum(1 for r in self.optimization_history if r["applied"]),
            "total_estimated_savings_per_day": round(total_estimated, 2),
            "total_actual_savings_per_day": round(total_actual, 2),
            "optimization_accuracy": round(total_actual / max(total_estimated, 0.01), 4),
            "by_type": self._group_by_type()
        }
    
    def _group_by_type(self) -> dict:
        """Group optimization history by type."""
        by_type = defaultdict(lambda: {"count": 0, "savings": 0.0})
        for r in self.optimization_history:
            opt_type = r["recommendation"]["type"]
            by_type[opt_type]["count"] += 1
            by_type[opt_type]["savings"] += r.get("actual_savings", 0)
        return dict(by_type)
```

### 8.3 Cost Optimization Configuration

```yaml
# cost_optimization.config.yaml
cost_optimization:
  enabled: true
  
  budget:
    daily_usd: 100
    monthly_usd: 3000
    alert_allocation_pct: 10
    storage_allocation_pct: 40
    ingestion_allocation_pct: 50
  
  analysis:
    interval: 3600  # Run cost analysis every hour
    trend_window_days: 30
    low_value_threshold: 0.2
  
  recommendations:
    auto_apply:
      enabled: true
      max_impact_level: low  # Only auto-apply low-impact changes
      require_approval_for:
        - medium
        - high
    
    sampling_reduction:
      enabled: true
      min_value_score: 0.3
      max_reduction_pct: 50
      cooldown_hours: 24
    
    storage_tiering:
      enabled: true
      tiers:
        hot:
          retention_days: 7
          resolution: full
        warm:
          retention_days: 30
          resolution: 5m
        cold:
          retention_days: 365
          resolution: 1h
      auto_tier: true
    
    metric_deprecation:
      enabled: true
      min_value_score: 0.1
      min_cost_per_day: 1.0
      deprecation_period_days: 14
    
    query_optimization:
      enabled: true
      cache_ttl_seconds: 300
      pre_aggregation:
        enabled: true
        intervals: [1m, 5m, 1h]
  
  alerting:
    enabled: true
    rules:
      - name: "budget_threshold_80"
        condition: "daily_cost > budget * 0.8"
        severity: P3
        message: "Monitoring cost at 80% of daily budget"
      
      - name: "budget_threshold_95"
        condition: "daily_cost > budget * 0.95"
        severity: P2
        message: "Monitoring cost at 95% of daily budget"
      
      - name: "cost_spike"
        condition: "cost_increase_1h > 50%"
        severity: P2
        message: "Monitoring cost spike detected"
      
      - name: "low_value_high_cost"
        condition: "value_score < 0.2 and cost > $10/day"
        severity: P3
        message: "Low-value metric with high cost: {{ metric }}"
  
  reporting:
    enabled: true
    daily_summary: true
    weekly_report: true
    monthly_review: true
    include:
      - cost_trend
      - top_expensive_metrics
      - optimization_savings
      - budget_forecast
      - recommendations
```

---

## 9. Integration with Governance Feedback Loop

### 9.1 Monitoring Automation → Governance Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│         Monitoring Automation → Governance Feedback Loop              │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Auto        │  │  Anomaly     │  │  Predictive  │             │
│  │  Collection  │  │  Detection   │  │  Alerting    │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                 │                      │
│         └────────────┬────┘                 │                      │
│                      │                      │                      │
│              ┌───────▼──────┐    ┌──────────▼──────────┐          │
│              │  Data        │    │  Risk Engine        │          │
│              │  Quality     │───→│  (Enhanced)         │          │
│              │  Validator   │    │                     │          │
│              └──────────────┘    │ • DQ-aware scoring  │          │
│                                  │ • Anomaly-weighted  │          │
│  ┌──────────────┐               │   risk              │          │
│  │  Self-Health │               │ • Predictive risk   │          │
│  │  Monitor     │──────────────→│   forecasting       │          │
│  └──────────────┘               │ • Cost-risk         │          │
│                                  │   correlation       │          │
│  ┌──────────────┐               └──────────┬──────────┘          │
│  │  Cost        │                          │                      │
│  │  Optimizer   │──────────────────────────┘                      │
│  └──────────────┘                                                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Governance Decision Engine                       │ │
│  │                                                              │ │
│  │  Monitoring Health → Risk Score → Control Action            │ │
│  │  DQ Grade → Confidence Adjustment → Decision Quality        │ │
│  │  Cost Efficiency → Budget Reallocation → Resource Planning   │ │
│  │  Predictive Alerts → Proactive Controls → Prevention         │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Enhanced Risk Scoring with Monitoring Automation

```python
# grc_claw/enhanced_risk_engine.py
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class EnhancedRiskScore:
    overall: float
    level: str
    components: Dict[str, float]
    dq_adjusted: bool
    predictive_component: float
    cost_risk_component: float
    monitoring_health_component: float
    recommendations: List[str]

class EnhancedRiskEngine:
    """Risk engine enhanced with monitoring automation data."""
    
    def __init__(self, base_risk_engine, dq_aggregator, 
                 self_health, cost_optimizer):
        self.base = base_risk_engine
        self.dq = dq_aggregator
        self.health = self_health
        self.cost = cost_optimizer
    
    def calculate_enhanced_risk(self, metrics: dict) -> EnhancedRiskScore:
        """Calculate risk score with monitoring automation inputs."""
        
        # Base risk from standard metrics
        base_risk = self.base.calculate_risk(metrics)
        
        # DQ adjustment: reduce confidence if data quality is poor
        dq_health = self.dq.get_overall_health()
        dq_factor = dq_health.get("overall_score", 1.0)
        
        # Monitoring health adjustment
        health = self.health.get_overall_health()
        health_score = health.get("health_score", 1.0)
        
        # If monitoring is unhealthy, we have less confidence in our risk assessment
        confidence_factor = min(dq_factor, health_score)
        
        # Cost risk component
        cost_trend = self.cost.get_cost_trend()
        cost_risk = 0.0
        if cost_trend.get("budget_forecast", 0) > 1.0:
            cost_risk = min((cost_trend["budget_forecast"] - 1.0) * 50, 30)
        
        # Predictive component: factor in predictive alerts
        predictive_risk = 0.0
        # Would integrate with predictive alert generator
        
        # Adjusted overall score
        adjusted_overall = base_risk.overall * (0.7 + 0.3 * confidence_factor)
        adjusted_overall += cost_risk * 0.1
        adjusted_overall += predictive_risk * 0.1
        adjusted_overall = min(adjusted_overall, 100)
        
        # Generate enhanced recommendations
        recommendations = list(base_risk.recommendations)
        
        if dq_factor < 0.7:
            recommendations.append(
                f"MEDIUM: Data quality is degraded (score: {dq_factor:.2f}). "
                "Verify monitoring pipeline before making critical decisions."
            )
        
        if health_score < 0.5:
            recommendations.append(
                f"HIGH: Monitoring system health is poor (score: {health_score:.2f}). "
                "Risk assessment confidence is reduced."
            )
        
        if cost_risk > 10:
            recommendations.append(
                f"LOW: Monitoring costs trending over budget. "
                f"Projected utilization: {cost_trend.get('budget_forecast', 0):.1%}"
            )
        
        return EnhancedRiskScore(
            overall=round(adjusted_overall, 2),
            level=self.base._determine_level(adjusted_overall).value,
            components=base_risk.components,
            dq_adjusted=True,
            predictive_component=round(predictive_risk, 2),
            cost_risk_component=round(cost_risk, 2),
            monitoring_health_component=round(health_score, 2),
            recommendations=recommendations
        )
```

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
- [ ] Deploy adaptive sampling controller
- [ ] Implement auto-instrumentation library
- [ ] Set up collection self-healing
- [ ] Deploy basic data quality validators
- [ ] Create self-health monitoring for collectors

### Phase 2: Anomaly Detection (Weeks 5-8)
- [ ] Deploy real-time anomaly detectors (Z-Score, EWMA, CUSUM)
- [ ] Implement ensemble anomaly aggregator
- [ ] Set up anomaly correlation engine
- [ ] Create anomaly detection dashboards
- [ ] Integrate anomaly events with alert routing

### Phase 3: Predictive Alerting (Weeks 9-12)
- [ ] Deploy forecasting models (Holt-Winters, Linear Regression)
- [ ] Implement Monte Carlo threshold projection
- [ ] Set up early warning alert generator
- [ ] Create cost overrun prediction
- [ ] Integrate predictive alerts with governance feedback loop

### Phase 4: Data Quality & Self-Health (Weeks 13-16)
- [ ] Deploy full data quality validation pipeline
- [ ] Implement cross-metric consistency checks
- [ ] Deploy self-health monitors for all components
- [ ] Set up self-healing automation
- [ ] Create meta-monitoring dashboards

### Phase 5: Cost Optimization (Weeks 17-20)
- [ ] Deploy cost analyzer
- [ ] Implement value assessment engine
- [ ] Set up optimization recommendation engine
- [ ] Deploy storage tiering
- [ ] Create cost optimization dashboards and reports

### Phase 6: Production Hardening (Weeks 21-24)
- [ ] Load test all automation pipelines
- [ ] Implement high availability for automation components
- [ ] Create runbooks for all automation failures
- [ ] Conduct cost optimization review
- [ ] Achieve ISO 42001 surveillance audit readiness

---

## 11. Configuration Reference

### 11.1 Environment Variables

```bash
# Monitoring Automation
GRC_MONITORING_AUTO_COLLECTION_ENABLED=true
GRC_MONITORING_ADAPTIVE_SAMPLING_ENABLED=true
GRC_MONITORING_ANOMALY_DETECTION_ENABLED=true
GRC_MONITORING_PREDICTIVE_ALERTING_ENABLED=true
GRC_MONITORING_DATA_QUALITY_ENABLED=true
GRC_MONITORING_SELF_HEALTH_ENABLED=true
GRC_MONITORING_COST_OPTIMIZATION_ENABLED=true

# Sampling
GRC_SAMPLING_NORMAL_RATE=0.1
GRC_SAMPLING_ANOMALY_RATE=1.0
GRC_SAMPLING_MAX_PER_SECOND=10000

# Anomaly Detection
GRC_ANOMALY_ZSCORE_THRESHOLD=2.0
GRC_ANOMALY_EWMA_ALPHA=0.3
GRC_ANOMALY_CUSUM_THRESHOLD=4.0
GRC_ANOMALY_ENSEMBLE_MIN_DETECTORS=2
GRC_ANOMALY_CORRELATION_WINDOW_SECONDS=300

# Predictive Alerting
GRC_PREDICTION_HOLT_WINTERS_ENABLED=true
GRC_PREDICTION_LINEAR_REGRESSION_ENABLED=true
GRC_PREDICTION_MONTE_CARLO_SIMULATIONS=1000
GRC_PREDICTION_MIN_CONFIDENCE=0.5
GRC_PREDICTION_LOOKAHEAD_MINUTES=60

# Data Quality
GRC_DQ_VALIDATION_INTERVAL_SECONDS=60
GRC_DQ_COMPLETENESS_THRESHOLD=0.95
GRC_DQ_ACCURACY_ZSCORE_THRESHOLD=4.0
GRC_DQ_TIMELINESS_MAX_DELAY_SECONDS=60
GRC_DQ_ALERT_THRESHOLD=0.7

# Self-Health
GRC_SELF_HEALTH_CHECK_INTERVAL_SECONDS=10
GRC_SELF_HEALTH_MAX_FAILURE_COUNT=5
GRC_SELF_HEALTH_CIRCUIT_BREAKER_TIMEOUT_SECONDS=300
GRC_SELF_HEALTH_AUTO_HEAL_ENABLED=true

# Cost Optimization
GRC_COST_DAILY_BUDGET_USD=100
GRC_COST_MONTHLY_BUDGET_USD=3000
GRC_COST_AUTO_APPLY_ENABLED=true
GRC_COST_AUTO_APPLY_MAX_IMPACT=low
GRC_COST_LOW_VALUE_THRESHOLD=0.2
GRC_COST_STORAGE_TIERING_ENABLED=true
```

### 11.2 Prometheus Scrape Configuration (Extended)

```yaml
# prometheus.yml (extended)
scrape_configs:
  - job_name: 'grc-claw'
    static_configs:
      - targets: ['grc-claw:8000']
    metrics_path: /metrics
    scrape_interval: 15s
  
  - job_name: 'grc-claw-automation'
    static_configs:
      - targets: ['grc-claw:8000']
    metrics_path: /metrics/automation
    scrape_interval: 30s
  
  - job_name: 'grc-claw-dq'
    static_configs:
      - targets: ['grc-claw:8000']
    metrics_path: /metrics/data-quality
    scrape_interval: 60s
  
  - job_name: 'grc-claw-self-health'
    static_configs:
      - targets: ['grc-claw:8000']
    metrics_path: /metrics/self-health
    scrape_interval: 10s
  
  - job_name: 'grc-claw-cost'
    static_configs:
      - targets: ['grc-claw:8000']
    metrics_path: /metrics/cost
    scrape_interval: 300s
  
  - job_name: 'langfuse'
    static_configs:
      - targets: ['langfuse:3000']
    metrics_path: /api/public/metrics
    scrape_interval: 30s
  
  - job_name: 'arize'
    static_configs:
      - targets: ['arize:8080']
    metrics_path: /metrics
    scrape_interval: 30s
```

---

## 12. Appendices

### A. Monitoring Automation Metric Naming Convention

All automation metrics follow: `grc_auto_{module}_{metric}_{unit}`

| Module | Examples |
|--------|----------|
| `collection` | `grc_auto_collection_samples_total`, `grc_auto_collection_lag_seconds` |
| `sampling` | `grc_auto_sampling_rate`, `grc_auto_sampling_cost_per_day` |
| `anomaly` | `grc_auto_anomaly_events_total`, `grc_auto_anomaly_detection_latency_seconds` |
| `prediction` | `grc_auto_prediction_forecasts_total`, `grc_auto_prediction_accuracy` |
| `dq` | `grc_auto_dq_score`, `grc_auto_dq_grade` |
| `health` | `grc_auto_health_score`, `grc_auto_health_component_status` |
| `cost` | `grc_auto_cost_daily_total`, `grc_auto_cost_optimization_savings` |

### B. Data Quality Grades

| Grade | Score Range | Description | Action |
|-------|-------------|-------------|--------|
| A | 95-100 | Excellent | No action needed |
| B | 85-94 | Good | Monitor |
| C | 70-84 | Fair | Investigate |
| D | 50-69 | Poor | Remediate |
| F | 0-49 | Critical | Immediate action |

### C. Self-Health Component Status

| Status | Score | Description | Action |
|--------|-------|-------------|--------|
| Healthy | 0.8-1.0 | Operating normally | None |
| Degraded | 0.5-0.79 | Reduced capability | Monitor closely |
| Unhealthy | 0.1-0.49 | Significant issues | Investigate and heal |
| Down | 0.0 | Not functioning | Immediate restart |

### D. Cost Optimization Impact Levels

| Level | Description | Approval Required |
|-------|-------------|-------------------|
| Low | No impact on monitoring effectiveness | No (auto-apply) |
| Medium | Minor reduction in coverage | Yes |
| High | Significant change to monitoring | Yes + governance review |

### E. Glossary

- **Adaptive Sampling**: Dynamic adjustment of metric collection rates based on system state
- **Anomaly Detection**: Automated identification of unusual patterns in metric data
- **Predictive Alerting**: Early warning system that forecasts threshold breaches
- **Data Quality (DQ)**: Measure of completeness, accuracy, timeliness, and consistency of monitoring data
- **Self-Health**: Meta-monitoring of the monitoring system itself
- **Cost Optimization**: Automated tuning of monitoring resources to maximize value per dollar
- **Holt-Winters**: Exponential smoothing forecasting method with trend and seasonality
- **CUSUM**: Cumulative Sum control chart for detecting small persistent shifts
- **EWMA**: Exponentially Weighted Moving Average for trend detection
- **Monte Carlo Projection**: Simulation-based forecasting using random sampling
- **Circuit Breaker**: Pattern that stops calling a failing service to prevent cascade failures
- **Flapping**: Rapid alternating between alert firing and resolving states

---

**Document Control:**
- Next review date: 2026-11-01
- Owner: AI Governance Team
- Approver: Chief AI Officer
