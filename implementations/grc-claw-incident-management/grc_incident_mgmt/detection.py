"""
GRC_Claw Automated Incident Detection Pipeline (§12 of GRC-AIM-001)

Implements the 5-stage detection pipeline:
    Ingest → Enrich → Detect → Correlate → Alert & Route

Stages:
    1. Data Ingestion — multi-source signal collection
    2. Data Enrichment — contextual enrichment
    3. Detection Engines — signature, anomaly, ML, behavioral, semantic, policy
    4. Signal Correlation — temporal, causal, asset, actor, campaign
    5. Alerting & Routing — severity-based alert generation and routing
"""

from __future__ import annotations

import hashlib
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Optional

from .models import DetectionSignal, Incident, IncidentStatus
from .taxonomy import IncidentCategory, Severity, SUBCATEGORIES, MINIMUM_SEVERITY


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 1: Data Ingestion (§12.2.1)
# ═══════════════════════════════════════════════════════════════════════════════

class SignalSource(str, Enum):
    AI_RISK_RADAR = "ai_risk_radar"
    POLICY_ENGINE = "policy_engine"
    MODEL_INFERENCE_LOGS = "model_inference_logs"
    AUDIT_TRAILS = "audit_trails"
    USER_REPORTS = "user_reports"
    EXTERNAL_FEEDS = "external_feeds"
    RED_TEAM = "red_team"
    INFRASTRUCTURE_METRICS = "infrastructure_metrics"


@dataclass
class RawSignal:
    """Raw signal before enrichment."""
    source: SignalSource
    data: dict[str, Any]
    timestamp: str = ""
    signal_id: str = ""


class DataIngestionStage:
    """
    Stage 1: Data Ingestion (§12.2.1)

    Collects raw signals from multiple sources:
    - AI-Risk-Radar: streaming input/output risk signals
    - Policy Engine: policy violation events
    - Model Inference Logs: request/response metadata
    - Audit Trails: action logs, access records
    - User Reports: manual incident reports
    - External Feeds: threat intel, vendor advisories, CVE feeds
    - Red Team Results: adversarial test findings
    - Infrastructure Metrics: CPU, memory, GPU, network, API latency
    """

    def __init__(self) -> None:
        self._buffer: list[RawSignal] = []
        self._source_counts: dict[SignalSource, int] = defaultdict(int)

    def ingest(self, source: SignalSource, data: dict[str, Any], timestamp: str = "") -> RawSignal:
        """Ingest a raw signal from a source."""
        sig = RawSignal(
            source=source,
            data=data,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            signal_id=hashlib.sha256(f"{source.value}:{timestamp}:{str(data)}".encode()).hexdigest()[:16],
        )
        self._buffer.append(sig)
        self._source_counts[source] += 1
        return sig

    def ingest_batch(self, source: SignalSource, items: list[dict[str, Any]]) -> list[RawSignal]:
        """Ingest multiple signals from the same source."""
        return [self.ingest(source, item) for item in items]

    def get_buffer(self) -> list[RawSignal]:
        return list(self._buffer)

    def clear_buffer(self) -> None:
        self._buffer.clear()

    def get_source_stats(self) -> dict[str, int]:
        return {k.value: v for k, v in self._source_counts.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2: Data Enrichment (§12.2.2)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EnrichmentContext:
    """Enrichment data attached to each signal."""
    asset_context: dict[str, Any] = field(default_factory=dict)
    user_context: dict[str, Any] = field(default_factory=dict)
    historical_context: dict[str, Any] = field(default_factory=dict)
    threat_context: dict[str, Any] = field(default_factory=dict)
    temporal_context: dict[str, Any] = field(default_factory=dict)
    data_classification: str = "internal"  # public | internal | confidential | restricted


class DataEnrichmentStage:
    """
    Stage 2: Data Enrichment (§12.2.2)

    Enriches raw signals with contextual information:
    1. Asset Context — map to registered AI assets
    2. User Context — identify affected users, roles, data access
    3. Historical Context — correlate with recent incidents, known issues
    4. Threat Context — MITRE ATLAS technique mappings
    5. Temporal Context — time-of-day, day-of-week, seasonal patterns
    6. Data Classification — tag with data sensitivity levels
    """

    def __init__(self, asset_inventory: Optional[dict[str, dict[str, Any]]] = None) -> None:
        self._asset_inventory = asset_inventory or {}
        self._recent_incidents: list[dict[str, Any]] = []
        self._threat_intel: dict[str, Any] = {}

    def register_asset(self, asset_id: str, metadata: dict[str, Any]) -> None:
        self._asset_inventory[asset_id] = metadata

    def add_recent_incident(self, incident: dict[str, Any]) -> None:
        self._recent_incidents.append(incident)

    def update_threat_intel(self, intel: dict[str, Any]) -> None:
        self._threat_intel.update(intel)

    def enrich(self, raw: RawSignal) -> DetectionSignal:
        """Enrich a raw signal into a DetectionSignal."""
        data = raw.data

        # Asset context
        asset_id = data.get("asset_id", "")
        asset_ctx = self._asset_inventory.get(asset_id, {})

        # User context
        user_ctx = {
            "user_id": data.get("user_id", ""),
            "role": data.get("role", ""),
            "data_access_level": data.get("data_access_level", ""),
        }

        # Historical context
        hist_ctx = {
            "recent_similar_incidents": [
                i for i in self._recent_incidents
                if i.get("category") == data.get("category")
            ][-5:],
            "known_issue_active": data.get("known_issue_id", "") != "",
        }

        # Threat context (MITRE ATLAS mapping)
        threat_ctx = {
            "atlas_technique": data.get("atlas_technique", ""),
            "threat_actor": data.get("threat_actor", ""),
            "ttp_match": data.get("ttp_match", False),
        }

        # Temporal context
        ts = datetime.fromisoformat(raw.timestamp.replace("Z", "+00:00")) if raw.timestamp else datetime.now(timezone.utc)
        temporal_ctx = {
            "hour_of_day": ts.hour,
            "day_of_week": ts.weekday(),
            "is_business_hours": 9 <= ts.hour < 17,
            "is_weekend": ts.weekday() >= 5,
        }

        # Data classification
        data_class = data.get("data_classification", "internal")

        # Map category
        category = None
        cat_str = data.get("category", "")
        if cat_str:
            try:
                category = IncidentCategory(cat_str)
            except ValueError:
                pass

        return DetectionSignal(
            signal_id=raw.signal_id,
            source=raw.source.value,
            category=category,
            subcategory_code=data.get("subcategory_code", ""),
            confidence=float(data.get("confidence", 0.0)),
            raw_data=data,
            timestamp=raw.timestamp,
            asset_id=asset_id,
            environment=data.get("environment", "production"),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 3: Detection Engines (§12.2.3)
# ═══════════════════════════════════════════════════════════════════════════════

class DetectionEngine:
    """Base class for detection engines."""

    def detect(self, signal: DetectionSignal) -> Optional[DetectionSignal]:
        raise NotImplementedError


class SignatureEngine(DetectionEngine):
    """
    Signature Engine — pattern matching, regex, YARA rules.
    Categories: PI, MP, SC
    Latency: <50ms
    """

    def __init__(self) -> None:
        self._patterns: dict[str, list[re.Pattern]] = {
            "PI-1": [
                re.compile(r"ignore\s+(previous|all|above)\s+instructions", re.IGNORECASE),
                re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.IGNORECASE),
                re.compile(r"system\s+prompt\s*[:=]", re.IGNORECASE),
                re.compile(r"DAN|jailbreak|developer\s+mode", re.IGNORECASE),
            ],
            "PI-3": [
                re.compile(r"ignore\s+.*\s+safety", re.IGNORECASE),
                re.compile(r"bypass\s+.*\s+filter", re.IGNORECASE),
                re.compile(r"no\s+restrictions?\s+(mode|enabled)", re.IGNORECASE),
            ],
            "MP-3": [
                re.compile(r"backdoor|trigger\s+pattern", re.IGNORECASE),
            ],
            "SC-3": [
                re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE),
            ],
        }

    def add_pattern(self, subcategory: str, pattern: str) -> None:
        if subcategory not in self._patterns:
            self._patterns[subcategory] = []
        self._patterns[subcategory].append(re.compile(pattern, re.IGNORECASE))

    def detect(self, signal: DetectionSignal) -> Optional[DetectionSignal]:
        text = str(signal.raw_data.get("text", ""))
        if not text:
            return None

        for sub_code, patterns in self._patterns.items():
            for pat in patterns:
                if pat.search(text):
                    signal.subcategory_code = sub_code
                    signal.confidence = max(signal.confidence, 0.85)
                    signal.raw_data["signature_match"] = pat.pattern
                    return signal
        return None


class AnomalyEngine(DetectionEngine):
    """
    Anomaly Engine — statistical baselines, z-score, isolation forest.
    Categories: DL, WA, AM
    Latency: <200ms
    """

    def __init__(self, z_threshold: float = 3.0) -> None:
        self._z_threshold = z_threshold
        self._baselines: dict[str, list[float]] = defaultdict(list)

    def set_baseline(self, metric: str, values: list[float]) -> None:
        self._baselines[metric] = values

    def detect(self, signal: DetectionSignal) -> Optional[DetectionSignal]:
        metric = signal.raw_data.get("metric_name", "")
        value = signal.raw_data.get("metric_value")
        if metric and value is not None and metric in self._baselines:
            baseline = self._baselines[metric]
            if len(baseline) >= 10:
                mean = statistics.mean(baseline)
                stdev = statistics.stdev(baseline) if len(baseline) > 1 else 0
                if stdev > 0:
                    z_score = abs(value - mean) / stdev
                    if z_score > self._z_threshold:
                        signal.confidence = min(0.99, 0.5 + (z_score / 10))
                        signal.raw_data["z_score"] = z_score
                        signal.raw_data["baseline_mean"] = mean
                        signal.raw_data["baseline_stdev"] = stdev
                        return signal
        return None


class MLClassifierEngine(DetectionEngine):
    """
    ML Classifier Engine — supervised models trained on labeled incidents.
    Categories: HO, HL, DL
    Latency: <100ms

    In production, this wraps a trained model (e.g., XGBoost, transformer).
    For this implementation, we use a configurable scoring function.
    """

    def __init__(self, scoring_fn: Optional[Callable[[DetectionSignal], float]] = None) -> None:
        self._scoring_fn = scoring_fn or self._default_scoring

    def _default_scoring(self, signal: DetectionSignal) -> float:
        """Default scoring based on signal features."""
        score = 0.0
        raw = signal.raw_data
        if raw.get("toxicity_score", 0) > 0.8:
            score = max(score, 0.9)
        if raw.get("grounding_score", 1.0) < 0.3:
            score = max(score, 0.85)
        if raw.get("pii_detected", False):
            score = max(score, 0.8)
        if raw.get("confidence_calibration_gap", 0) > 0.5:
            score = max(score, 0.75)
        return score

    def detect(self, signal: DetectionSignal) -> Optional[DetectionSignal]:
        score = self._scoring_fn(signal)
        if score > 0.6:
            signal.confidence = max(signal.confidence, score)
            signal.raw_data["ml_score"] = score
            return signal
        return None


class BehavioralEngine(DetectionEngine):
    """
    Behavioral Engine — sequence analysis, Markov chains, LSTM.
    Categories: AM, WA
    Latency: <500ms
    """

    def __init__(self) -> None:
        self._action_sequences: dict[str, list[list[str]]] = defaultdict(list)

    def register_normal_sequence(self, agent_id: str, sequence: list[str]) -> None:
        self._action_sequences[agent_id].append(sequence)

    def detect(self, signal: DetectionSignal) -> Optional[DetectionSignal]:
        agent_id = signal.raw_data.get("agent_id", "")
        current_seq = signal.raw_data.get("action_sequence", [])
        if agent_id and current_seq and agent_id in self._action_sequences:
            normal_seqs = self._action_sequences[agent_id]
            # Simple anomaly: check if current sequence deviates from normal
            max_similarity = max(
                self._sequence_similarity(current_seq, ns) for ns in normal_seqs
            ) if normal_seqs else 0
            if max_similarity < 0.3:
                signal.confidence = max(signal.confidence, 0.8)
                signal.raw_data["behavioral_anomaly"] = True
                signal.raw_data["sequence_similarity"] = max_similarity
                return signal
        return None

    @staticmethod
    def _sequence_similarity(a: list[str], b: list[str]) -> float:
        """Jaccard-like similarity between action sequences."""
        if not a or not b:
            return 0.0
        set_a, set_b = set(a), set(b)
        return len(set_a & set_b) / len(set_a | set_b)


class SemanticEngine(DetectionEngine):
    """
    Semantic Engine — embedding similarity, semantic drift detection.
    Categories: HL, PI
    Latency: <300ms
    """

    def __init__(self, similarity_threshold: float = 0.3) -> None:
        self._threshold = similarity_threshold
        self._reference_embeddings: dict[str, list[float]] = {}

    def register_reference(self, key: str, embedding: list[float]) -> None:
        self._reference_embeddings[key] = embedding

    def detect(self, signal: DetectionSignal) -> Optional[DetectionSignal]:
        embedding = signal.raw_data.get("embedding")
        ref_key = signal.raw_data.get("reference_key", "")
        if embedding and ref_key in self._reference_embeddings:
            ref = self._reference_embeddings[ref_key]
            sim = self._cosine_similarity(embedding, ref)
            if sim < self._threshold:
                signal.confidence = max(signal.confidence, 0.75)
                signal.raw_data["semantic_drift"] = True
                signal.raw_data["similarity_score"] = sim
                return signal
        return None

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class PolicyEngine(DetectionEngine):
    """
    Policy Engine — rule-based policy evaluation.
    Categories: All
    Latency: Real-time
    """

    def __init__(self) -> None:
        self._policies: list[dict[str, Any]] = []

    def add_policy(self, policy: dict[str, Any]) -> None:
        """
        Policy format:
        {
            "id": "POL-001",
            "name": "No PII in outputs",
            "condition": {"field": "output_contains_pii", "op": "eq", "value": True},
            "action": "alert",
            "severity": "S2",
            "category": "DL"
        }
        """
        self._policies.append(policy)

    def detect(self, signal: DetectionSignal) -> Optional[DetectionSignal]:
        for policy in self._policies:
            if self._evaluate_policy(policy, signal):
                signal.confidence = max(signal.confidence, 0.9)
                signal.raw_data["policy_violation"] = policy["id"]
                signal.raw_data["policy_severity"] = policy.get("severity", "")
                if policy.get("category"):
                    try:
                        signal.category = IncidentCategory(policy["category"])
                    except ValueError:
                        pass
                return signal
        return None

    def _evaluate_policy(self, policy: dict[str, Any], signal: DetectionSignal) -> bool:
        cond = policy.get("condition", {})
        field = cond.get("field", "")
        op = cond.get("op", "eq")
        value = cond.get("value")
        actual = signal.raw_data.get(field)

        if actual is None:
            return False
        if op == "eq":
            return actual == value
        if op == "gt":
            return float(actual) > float(value)
        if op == "lt":
            return float(actual) < float(value)
        if op == "contains":
            return value in str(actual)
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 4: Signal Correlation (§12.2.4)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CorrelationRule:
    """Correlation rule definition (§12.2.4)."""
    rule_id: str
    name: str
    condition: Callable[[list[DetectionSignal]], bool]
    action: str
    severity: Optional[Severity] = None
    description: str = ""


class SignalCorrelationStage:
    """
    Stage 4: Signal Correlation (§12.2.4)

    Correlates individual signals to reduce false positives and identify
    multi-stage attacks:
    1. Temporal Correlation — signals within configurable time window
    2. Causal Correlation — signals linked by causal relationships
    3. Asset Correlation — signals affecting the same AI asset
    4. Actor Correlation — signals from the same user/IP/session
    5. Campaign Correlation — signals matching known attack patterns
    """

    DEFAULT_TIME_WINDOW = timedelta(minutes=5)

    def __init__(self, time_window: Optional[timedelta] = None) -> None:
        self._time_window = time_window or self.DEFAULT_TIME_WINDOW
        self._rules: list[CorrelationRule] = []
        self._correlation_groups: dict[str, list[DetectionSignal]] = defaultdict(list)
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Set up default correlation rules from §12.2.4."""
        self._rules.extend([
            CorrelationRule(
                "CORR-001", "Escalating Injection",
                lambda sigs: (
                    sum(1 for s in sigs if s.subcategory_code.startswith("PI-")) >= 3
                    and self._time_span(sigs) <= timedelta(minutes=10)
                ),
                "escalate_s2", Severity.S2_HIGH,
                "≥3 PI signals in 10 min from same source"
            ),
            CorrelationRule(
                "CORR-002", "Data Exfiltration Pattern",
                lambda sigs: (
                    any(s.subcategory_code.startswith("DL-") for s in sigs)
                    and any(s.raw_data.get("api_call_volume", 0) > 1000 for s in sigs)
                    and any(s.raw_data.get("off_hours_access", False) for s in sigs)
                ),
                "escalate_s1_auto_contain", Severity.S1_CRITICAL,
                "DL signal + unusual API call volume + off-hours access"
            ),
            CorrelationRule(
                "CORR-003", "Agent Cascade Failure",
                lambda sigs: (
                    any(s.subcategory_code.startswith("WA-") for s in sigs)
                    and any(s.raw_data.get("downstream_error_spike", False) for s in sigs)
                    and any(s.raw_data.get("resource_exhaustion", False) for s in sigs)
                ),
                "escalate_s1_kill_switch", Severity.S1_CRITICAL,
                "WA signal + downstream error spike + resource exhaustion"
            ),
            CorrelationRule(
                "CORR-004", "Model Degradation",
                lambda sigs: (
                    sum(1 for s in sigs if s.subcategory_code.startswith("HL-")) >= 3
                    and any(s.raw_data.get("confidence_dropping", False) for s in sigs)
                    and any(s.raw_data.get("user_complaints", 0) > 5 for s in sigs)
                ),
                "escalate_s3_review", Severity.S3_MEDIUM,
                "HL signals increasing + confidence scores dropping + user complaints"
            ),
            CorrelationRule(
                "CORR-005", "Supply Chain Cascade",
                lambda sigs: (
                    any(s.subcategory_code.startswith("SC-") for s in sigs)
                    and sum(1 for s in sigs if s.raw_data.get("dependent_system_affected", False)) >= 2
                ),
                "escalate_s2_notify_procurement", Severity.S2_HIGH,
                "SC signal + multiple dependent systems affected"
            ),
        ])

    def add_rule(self, rule: CorrelationRule) -> None:
        self._rules.append(rule)

    def correlate(self, signals: list[DetectionSignal]) -> list[DetectionSignal]:
        """Run correlation on a batch of signals."""
        if not signals:
            return signals

        # Group by asset
        asset_groups: dict[str, list[DetectionSignal]] = defaultdict(list)
        for sig in signals:
            if sig.asset_id:
                asset_groups[sig.asset_id].append(sig)

        # Group by actor (user/IP/session)
        actor_groups: dict[str, list[DetectionSignal]] = defaultdict(list)
        for sig in signals:
            actor = sig.raw_data.get("user_id", "") or sig.raw_data.get("ip", "") or sig.raw_data.get("session_id", "")
            if actor:
                actor_groups[actor].append(sig)

        # Apply correlation rules
        all_groups = list(asset_groups.values()) + list(actor_groups.values())
        for group in all_groups:
            for rule in self._rules:
                if rule.condition(group):
                    group_id = hashlib.sha256(f"{rule.rule_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]
                    for sig in group:
                        sig.correlated = True
                        sig.correlation_group_id = group_id
                        sig.raw_data["correlation_rule"] = rule.rule_id
                        sig.raw_data["correlation_action"] = rule.action
                        if rule.severity:
                            sig.raw_data["correlation_severity"] = rule.severity.value
                    self._correlation_groups[group_id] = group

        return signals

    def get_correlation_groups(self) -> dict[str, list[DetectionSignal]]:
        return dict(self._correlation_groups)

    @staticmethod
    def _time_span(signals: list[DetectionSignal]) -> timedelta:
        timestamps = []
        for s in signals:
            try:
                ts = datetime.fromisoformat(s.timestamp.replace("Z", "+00:00"))
                timestamps.append(ts)
            except (ValueError, AttributeError):
                pass
        if len(timestamps) < 2:
            return timedelta(0)
        return max(timestamps) - min(timestamps)


# ═══════════════════════════════════════════════════════════════════════════════
# Stage 5: Alerting and Routing (§12.2.5)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Alert:
    """Generated alert from the detection pipeline."""
    alert_id: str
    signal: DetectionSignal
    severity: Severity
    confidence: float
    action: str
    notifications: list[str]
    timestamp: str = ""


class AlertingStage:
    """
    Stage 5: Alerting and Routing (§12.2.5)

    Generates alerts based on correlation results and routes to responders:
    - ≥0.95 confidence, S1/S2: auto-classify, auto-contain, immediate alert
    - 0.80–0.94: auto-classify, alert human for containment decision
    - 0.60–0.79: flag for human review, queue for analyst triage
    - <0.60: log for pattern analysis, no immediate action
    """

    def __init__(self) -> None:
        self._alerts: list[Alert] = []

    def process(self, signal: DetectionSignal) -> Optional[Alert]:
        """Process a correlated signal and generate an alert if warranted."""
        conf = signal.confidence

        if conf < 0.60:
            return None  # Log only, no alert

        # Determine severity from signal or correlation
        severity = self._resolve_severity(signal)

        if conf >= 0.95 and severity in (Severity.S1_CRITICAL, Severity.S2_HIGH):
            action = "auto_classify_auto_contain_immediate_alert"
            notifications = ["pagerduty", "sms", "slack", "email"]
        elif conf >= 0.80:
            action = "auto_classify_alert_human"
            notifications = ["slack", "email"]
        else:
            action = "flag_for_human_review"
            notifications = ["slack_low_priority"]

        alert = Alert(
            alert_id=hashlib.sha256(f"{signal.signal_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:16],
            signal=signal,
            severity=severity,
            confidence=conf,
            action=action,
            notifications=notifications,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._alerts.append(alert)
        return alert

    def get_alerts(self) -> list[Alert]:
        return list(self._alerts)

    def _resolve_severity(self, signal: DetectionSignal) -> Severity:
        """Resolve severity from signal data, correlation, or minimum severity."""
        # Check correlation severity
        corr_sev = signal.raw_data.get("correlation_severity", "")
        if corr_sev:
            try:
                return Severity(corr_sev)
            except ValueError:
                pass

        # Check subcategory minimum severity
        if signal.subcategory_code:
            min_sev = MINIMUM_SEVERITY.get(signal.subcategory_code)
            if min_sev:
                return min_sev

        # Default based on confidence
        if signal.confidence >= 0.95:
            return Severity.S1_CRITICAL
        elif signal.confidence >= 0.80:
            return Severity.S2_HIGH
        elif signal.confidence >= 0.60:
            return Severity.S3_MEDIUM
        return Severity.S4_LOW


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

class DetectionPipeline:
    """
    Complete 5-stage detection pipeline (§12.1).

    Orchestrates: Ingest → Enrich → Detect → Correlate → Alert
    """

    def __init__(self) -> None:
        self.ingestion = DataIngestionStage()
        self.enrichment = DataEnrichmentStage()
        self.engines: list[DetectionEngine] = []
        self.correlation = SignalCorrelationStage()
        self.alerting = AlertingStage()

    def register_engine(self, engine: DetectionEngine) -> None:
        self.engines.append(engine)

    def process_signal(self, source: SignalSource, data: dict[str, Any]) -> Optional[Alert]:
        """Process a single signal through the full pipeline."""
        # Stage 1: Ingest
        raw = self.ingestion.ingest(source, data)

        # Stage 2: Enrich
        signal = self.enrichment.enrich(raw)

        # Stage 3: Detect (run all engines)
        for engine in self.engines:
            result = engine.detect(signal)
            if result is not None:
                signal = result

        # Stage 4: Correlate (single signal — batch correlation done separately)
        # For single signals, we still check correlation rules
        correlated = self.correlation.correlate([signal])

        # Stage 5: Alert
        for sig in correlated:
            alert = self.alerting.process(sig)
            if alert:
                return alert

        return None

    def process_batch(self, source: SignalSource, items: list[dict[str, Any]]) -> list[Alert]:
        """Process a batch of signals through the full pipeline."""
        # Stage 1: Ingest
        raws = self.ingestion.ingest_batch(source, items)

        # Stage 2: Enrich
        signals = [self.enrichment.enrich(r) for r in raws]

        # Stage 3: Detect
        detected: list[DetectionSignal] = []
        for signal in signals:
            for engine in self.engines:
                result = engine.detect(signal)
                if result is not None:
                    signal = result
            detected.append(signal)

        # Stage 4: Correlate
        correlated = self.correlation.correlate(detected)

        # Stage 5: Alert
        alerts: list[Alert] = []
        for sig in correlated:
            alert = self.alerting.process(sig)
            if alert:
                alerts.append(alert)

        return alerts

    def get_pipeline_stats(self) -> dict[str, Any]:
        """Get pipeline health metrics (§12.4)."""
        return {
            "ingestion": self.ingestion.get_source_stats(),
            "engines_registered": len(self.engines),
            "correlation_groups": len(self.correlation.get_correlation_groups()),
            "alerts_generated": len(self.alerting.get_alerts()),
        }
