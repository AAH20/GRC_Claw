"""
GRC_Claw Risk Monitoring
=========================
Implements the 4-layer continuous monitoring framework:
  L1: Signal Collection
  L2: Risk Scoring
  L3: Threshold Alerting
  L4: Trend Analysis

Includes KRI tracking, escalation matrix, and review cadence.
References GRC-RISK-001 §8.1-8.5.

Usage:
    from risk_monitoring import RiskMonitor, KRITracker, EscalationManager

    monitor = RiskMonitor()
    monitor.check_kris(register)
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional, Callable


# ─── Enums ───────────────────────────────────────────────────────────────────

class AlertSeverity(str, Enum):
    P1_CRITICAL = "P1-Critical"
    P2_HIGH = "P2-High"
    P3_MEDIUM = "P3-Medium"
    P4_LOW = "P4-Low"


class MonitoringLayer(str, Enum):
    L1_SIGNAL_COLLECTION = "L1: Signal Collection"
    L2_RISK_SCORING = "L2: Risk Scoring"
    L3_THRESHOLD_ALERTING = "L3: Threshold Alerting"
    L4_TREND_ANALYSIS = "L4: Trend Analysis"


class EscalationPath(str, Enum):
    P1 = "CISO → CTO → Risk Committee"
    P2 = "Security Lead → Risk Owner"
    P3 = "GRC Analyst → Risk Owner"
    P4 = "GRC Analyst"


# ─── KRI Definitions (GRC-RISK-001 §8.3) ─────────────────────────────────────

KRI_DEFINITIONS = {
    "open_critical_risks": {
        "name": "Open Critical Risks",
        "description": "Count of risks at Critical tier",
        "target": 0,
        "alert_threshold": 1,
        "source": "Risk Register",
    },
    "open_high_risks": {
        "name": "Open High Risks",
        "description": "Count of risks at High tier",
        "target": 0,
        "alert_threshold": 3,
        "source": "Risk Register",
    },
    "mean_risk_score": {
        "name": "Mean Risk Score",
        "description": "Average MDRS across all active risks",
        "target": 2.5,
        "alert_threshold": 3.0,
        "source": "Risk Engine",
    },
    "risk_treatment_overdue": {
        "name": "Risk Treatment Overdue",
        "description": "Count of treatments past due date",
        "target": 0,
        "alert_threshold": 1,
        "source": "Risk Register",
    },
    "control_failure_rate": {
        "name": "Control Failure Rate",
        "description": "% of controls failing effectiveness test",
        "target": 5.0,
        "alert_threshold": 10.0,
        "source": "Control Testing",
    },
    "risk_assessment_currency": {
        "name": "Risk Assessment Currency",
        "description": "% of assessments within review period",
        "target": 100.0,
        "alert_threshold": 90.0,
        "source": "Risk Register",
    },
    "vendor_risk_exposure": {
        "name": "Vendor Risk Exposure",
        "description": "Count of unassured high-risk vendors",
        "target": 0,
        "alert_threshold": 1,
        "source": "Vendor Mgmt",
    },
    "incident_recurrence": {
        "name": "Incident Recurrence",
        "description": "% of incidents that are recurring",
        "target": 10.0,
        "alert_threshold": 20.0,
        "source": "Incident Mgmt",
    },
}


# ─── Escalation Matrix (GRC-RISK-001 §8.5) ──────────────────────────────────

ESCALATION_MATRIX = {
    AlertSeverity.P1_CRITICAL: {
        "trigger": "Risk materializes with catastrophic impact",
        "response_time": "15 minutes",
        "escalation_path": EscalationPath.P1.value,
    },
    AlertSeverity.P2_HIGH: {
        "trigger": "Risk tier escalates to High",
        "response_time": "1 hour",
        "escalation_path": EscalationPath.P2.value,
    },
    AlertSeverity.P3_MEDIUM: {
        "trigger": "Risk tier escalates to Medium",
        "response_time": "4 hours",
        "escalation_path": EscalationPath.P3.value,
    },
    AlertSeverity.P4_LOW: {
        "trigger": "Risk tier increases within Low",
        "response_time": "24 hours",
        "escalation_path": EscalationPath.P4.value,
    },
}


# ─── Review Cadence (GRC-RISK-001 §8.4) ─────────────────────────────────────

REVIEW_CADENCE = {
    "continuous": {"frequency": "Real-time", "scope": "Critical risks, KRIs", "output": "Automated alerts"},
    "operational": {"frequency": "Weekly", "scope": "High and Medium risks", "output": "Status report"},
    "management": {"frequency": "Monthly", "scope": "All active risks", "output": "Risk dashboard"},
    "executive": {"frequency": "Quarterly", "scope": "Risk posture, trends, appetite", "output": "Board report"},
    "comprehensive": {"frequency": "Annually", "scope": "Full risk register, framework", "output": "Annual risk report"},
}


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class Signal:
    """L1: Raw monitoring signal."""
    signal_id: str
    source: str
    timestamp: str
    signal_type: str
    value: float
    metadata: dict = field(default_factory=dict)


@dataclass
class Alert:
    """L3: Threshold breach alert."""
    alert_id: str
    severity: AlertSeverity
    kri_name: str
    current_value: float
    threshold: float
    timestamp: str
    message: str
    acknowledged: bool = False
    acknowledged_by: str = ""
    escalation_triggered: bool = False


@dataclass
class TrendPoint:
    """L4: Single point in a trend series."""
    date: str
    value: float


@dataclass
class TrendAnalysis:
    """L4: Trend analysis result."""
    metric_name: str
    points: list[TrendPoint]
    trend_direction: str  # "increasing", "decreasing", "stable"
    change_pct: float
    anomaly_detected: bool
    anomaly_details: str = ""


# ─── KRI Tracker ─────────────────────────────────────────────────────────────

class KRITracker:
    """Tracks Key Risk Indicators against thresholds."""

    def __init__(self):
        self._history: dict[str, list[TrendPoint]] = {}

    def record(self, kri_name: str, value: float, timestamp: Optional[str] = None):
        """Record a KRI measurement."""
        ts = timestamp or datetime.utcnow().isoformat()
        if kri_name not in self._history:
            self._history[kri_name] = []
        self._history[kri_name].append(TrendPoint(date=ts, value=value))

    def check_threshold(self, kri_name: str, value: float) -> Optional[Alert]:
        """Check if a KRI value breaches its threshold."""
        kri = KRI_DEFINITIONS.get(kri_name)
        if not kri:
            return None

        threshold = kri["alert_threshold"]
        target = kri["target"]

        # Determine if breached (higher is worse for most KRIs)
        breached = value >= threshold if target <= threshold else value <= threshold

        if not breached:
            return None

        # Determine severity
        if kri_name in ("open_critical_risks", "mean_risk_score") and value >= threshold * 1.5:
            severity = AlertSeverity.P1_CRITICAL
        elif value >= threshold * 1.2:
            severity = AlertSeverity.P2_HIGH
        elif value >= threshold:
            severity = AlertSeverity.P3_MEDIUM
        else:
            severity = AlertSeverity.P4_LOW

        return Alert(
            alert_id=f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            severity=severity,
            kri_name=kri_name,
            current_value=value,
            threshold=threshold,
            timestamp=datetime.utcnow().isoformat(),
            message=f"KRI '{kri['name']}' breached: {value} (threshold: {threshold})",
        )

    def get_trend(self, kri_name: str, days: int = 30) -> list[TrendPoint]:
        """Get trend data for a KRI."""
        points = self._history.get(kri_name, [])
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return [p for p in points if p.date >= cutoff]

    def summary(self) -> dict:
        """Current KRI status summary."""
        result = {}
        for name, kri in KRI_DEFINITIONS.items():
            history = self._history.get(name, [])
            current = history[-1].value if history else None
            result[name] = {
                "name": kri["name"],
                "current": current,
                "target": kri["target"],
                "threshold": kri["alert_threshold"],
                "status": "breached" if current is not None and self._is_breached(name, current) else "ok",
            }
        return result

    def _is_breached(self, kri_name: str, value: float) -> bool:
        kri = KRI_DEFINITIONS[kri_name]
        threshold = kri["alert_threshold"]
        target = kri["target"]
        return value >= threshold if target <= threshold else value <= threshold


# ─── Escalation Manager ──────────────────────────────────────────────────────

class EscalationManager:
    """Manages risk escalation per the escalation matrix."""

    def __init__(self):
        self._escalations: list[dict] = []

    def evaluate_escalation(self, alert: Alert) -> dict:
        """Determine escalation path for an alert."""
        matrix = ESCALATION_MATRIX[alert.severity]
        escalation = {
            "alert_id": alert.alert_id,
            "severity": alert.severity.value,
            "trigger": matrix["trigger"],
            "response_time": matrix["response_time"],
            "escalation_path": matrix["escalation_path"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "escalated",
        }
        alert.escalation_triggered = True
        self._escalations.append(escalation)
        return escalation

    def get_escalations(self, severity: Optional[AlertSeverity] = None) -> list[dict]:
        if severity:
            return [e for e in self._escalations if e["severity"] == severity.value]
        return self._escalations.copy()


# ─── Risk Monitor (Main Engine) ──────────────────────────────────────────────

class RiskMonitor:
    """
    4-layer continuous monitoring engine.
    Orchestrates signal collection, risk scoring, threshold alerting, and trend analysis.
    """

    def __init__(self):
        self.kri_tracker = KRITracker()
        self.escalation_manager = EscalationManager()
        self._signals: list[Signal] = []
        self._alerts: list[Alert] = []
        self._trends: dict[str, TrendAnalysis] = {}

    # ── L1: Signal Collection ──────────────────────────────────────────

    def collect_signal(
        self, source: str, signal_type: str, value: float,
        metadata: Optional[dict] = None,
    ) -> Signal:
        """Collect a raw monitoring signal."""
        sig = Signal(
            signal_id=f"SIG-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            source=source,
            timestamp=datetime.utcnow().isoformat(),
            signal_type=signal_type,
            value=value,
            metadata=metadata or {},
        )
        self._signals.append(sig)
        return sig

    def get_signals(
        self, source: Optional[str] = None,
        signal_type: Optional[str] = None,
        since: Optional[str] = None,
    ) -> list[Signal]:
        """Query collected signals."""
        results = self._signals
        if source:
            results = [s for s in results if s.source == source]
        if signal_type:
            results = [s for s in results if s.signal_type == signal_type]
        if since:
            results = [s for s in results if s.timestamp >= since]
        return results

    # ── L2: Risk Scoring ───────────────────────────────────────────────

    def recalculate_risk_scores(self, register) -> list[dict]:
        """
        Recalculate MDRS for all active risks in the register.
        Returns list of changes detected.
        """
        changes = []
        for risk in register.all():
            if risk.risk_status.value in ("closed", "retired"):
                continue
            score = risk.residual_score or risk.inherent_score
            if score:
                self.kri_tracker.record("mean_risk_score", score.mdrs)
                changes.append({
                    "risk_id": risk.risk_id,
                    "mdrs": score.mdrs,
                    "tier": score.tier.value,
                })
        return changes

    # ── L3: Threshold Alerting ─────────────────────────────────────────

    def check_kris(self, register) -> list[Alert]:
        """
        Evaluate all KRIs against current register state.
        Returns list of generated alerts.
        """
        alerts = []

        # Open critical risks
        from risk_register import RiskTier as RT
        critical_count = len([r for r in register.all()
                             if (r.residual_score or r.inherent_score)
                             and (r.residual_score or r.inherent_score).tier == RT.CRITICAL])
        alert = self.kri_tracker.check_threshold("open_critical_risks", critical_count)
        if alert:
            alerts.append(alert)

        # Open high risks
        high_count = len([r for r in register.all()
                         if (r.residual_score or r.inherent_score)
                         and (r.residual_score or r.inherent_score).tier == RT.HIGH])
        alert = self.kri_tracker.check_threshold("open_high_risks", high_count)
        if alert:
            alerts.append(alert)

        # Mean risk score
        scores = [(r.residual_score or r.inherent_score).mdrs
                  for r in register.all()
                  if (r.residual_score or r.inherent_score)]
        if scores:
            mean_score = round(statistics.mean(scores), 2)
            alert = self.kri_tracker.check_threshold("mean_risk_score", mean_score)
            if alert:
                alerts.append(alert)

        # Overdue treatments
        overdue = len(register.overdue_reviews())
        alert = self.kri_tracker.check_threshold("risk_treatment_overdue", overdue)
        if alert:
            alerts.append(alert)

        # Assessment currency
        active = [r for r in register.all()
                  if r.risk_status.value not in ("closed", "retired")]
        if active:
            current = len([r for r in active
                          if r.review_date and r.review_date >= date.today().isoformat()])
            currency_pct = round(current / len(active) * 100, 1)
            alert = self.kri_tracker.check_threshold("risk_assessment_currency", currency_pct)
            if alert:
                alerts.append(alert)

        self._alerts.extend(alerts)

        # Auto-escalate
        for alert in alerts:
            self.escalation_manager.evaluate_escalation(alert)

        return alerts

    def get_alerts(
        self, severity: Optional[AlertSeverity] = None,
        acknowledged: Optional[bool] = None,
    ) -> list[Alert]:
        """Query alerts."""
        results = self._alerts
        if severity:
            results = [a for a in results if a.severity == severity]
        if acknowledged is not None:
            results = [a for a in results if a.acknowledged == acknowledged]
        return results

    def acknowledge_alert(self, alert_id: str, actor: str):
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = actor
                break

    # ── L4: Trend Analysis ─────────────────────────────────────────────

    def analyze_trend(self, metric_name: str, days: int = 30) -> TrendAnalysis:
        """Analyze trend for a metric over time."""
        points = self.kri_tracker.get_trend(metric_name, days)
        if len(points) < 2:
            return TrendAnalysis(
                metric_name=metric_name,
                points=points,
                trend_direction="insufficient_data",
                change_pct=0.0,
                anomaly_detected=False,
            )

        values = [p.value for p in points]
        first_val = values[0]
        last_val = values[-1]
        change_pct = round((last_val - first_val) / first_val * 100, 2) if first_val != 0 else 0.0

        # Simple trend direction
        if change_pct > 5:
            direction = "increasing"
        elif change_pct < -5:
            direction = "decreasing"
        else:
            direction = "stable"

        # Simple anomaly detection (values beyond 2 std devs)
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        anomalies = [v for v in values if std_val > 0 and abs(v - mean_val) > 2 * std_val]

        result = TrendAnalysis(
            metric_name=metric_name,
            points=points,
            trend_direction=direction,
            change_pct=change_pct,
            anomaly_detected=len(anomalies) > 0,
            anomaly_details=f"{len(anomalies)} anomalies detected" if anomalies else "",
        )
        self._trends[metric_name] = result
        return result

    # ── Monitoring Summary ─────────────────────────────────────────────

    def monitoring_summary(self) -> dict:
        """Complete monitoring status summary."""
        return {
            "layers": {
                "L1_signals_collected": len(self._signals),
                "L2_risks_scored": len(self.kri_tracker._history.get("mean_risk_score", [])),
                "L3_alerts_active": len([a for a in self._alerts if not a.acknowledged]),
                "L4_trends_analyzed": len(self._trends),
            },
            "kri_status": self.kri_tracker.summary(),
            "escalations": len(self.escalation_manager._escalations),
            "review_cadence": REVIEW_CADENCE,
        }


# ─── Demo / Self-Test ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from risk_register import RiskRegister, RiskTier

    register = RiskRegister()
    monitor = RiskMonitor()

    # Create some risks
    r1 = register.create_risk(
        title="Test critical risk", domain="SEC", category="SEC-02",
        likelihood=5, impact=5, detectability=4, velocity=5, persistence=4,
    )
    r2 = register.create_risk(
        title="Test high risk", domain="DAT", category="DAT-03",
        likelihood=4, impact=4, detectability=3, velocity=3, persistence=4,
    )

    # L1: Collect signals
    monitor.collect_signal("agent_telemetry", "goal_deviation", 0.85)
    monitor.collect_signal("audit_log", "policy_violation", 1)
    print(f"L1 Signals collected: {len(monitor.get_signals())}")

    # L2: Recalculate scores
    changes = monitor.recalculate_risk_scores(register)
    print(f"L2 Risk scores recalculated: {len(changes)}")

    # L3: Check KRIs
    alerts = monitor.check_kris(register)
    print(f"L3 Alerts generated: {len(alerts)}")
    for alert in alerts:
        print(f"  {alert.severity.value}: {alert.message}")

    # L4: Trend analysis
    # Record some historical data
    for i in range(10):
        monitor.kri_tracker.record("mean_risk_score", 2.0 + i * 0.1)
    trend = monitor.analyze_trend("mean_risk_score")
    print(f"L4 Trend: {trend.trend_direction} ({trend.change_pct}%)")

    # Summary
    summary = monitor.monitoring_summary()
    print(f"\nMonitoring Summary: {json.dumps(summary, indent=2, default=str)}")
