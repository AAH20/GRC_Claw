#!/usr/bin/env python3
"""
GRC_Claw Risk Assessment Demo
==============================
Demonstrates the complete risk management workflow:
  1. SCORE    - Quantify risk using FAIR analysis and Monte Carlo simulation
  2. TREAT    - Apply risk treatment strategies (mitigate, transfer, accept, avoid)
  3. MONITOR  - Track risk trends and generate heat maps

Usage:
    python risk_assessment_demo.py
"""

import json
import math
import random
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# ── Enums & Types ──────────────────────────────────────────────────────────

class RiskLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class RiskStatus(Enum):
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    TREATED = "treated"
    ACCEPTED = "accepted"
    MONITORING = "monitoring"


class DistributionType(Enum):
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"
    BETA_PERT = "betaPERT"


class TreatmentStrategy(Enum):
    MITIGATE = "mitigate"
    TRANSFER = "transfer"
    ACCEPT = "accept"
    AVOID = "avoid"


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class DistributionParams:
    type: str
    mean: float = 0
    std_dev: float = 0
    min: float = 0
    max: float = 0
    mode: float = 0


@dataclass
class RiskScenario:
    id: str
    name: str
    threat: str
    vulnerability: str
    impact: DistributionParams
    probability: DistributionParams
    tags: list = field(default_factory=list)
    owner: str = ""


@dataclass
class FAIRModel:
    threat_event_frequency: float
    threat_capability: float
    vulnerability: float
    primary_loss: float
    secondary_loss_frequency: float
    secondary_loss_magnitude: float
    loss_event_frequency: float
    loss_magnitude: float
    annualized_loss_expectancy: float


@dataclass
class MonteCarloResult:
    iterations: int
    mean: float
    std_dev: float
    variance: float
    min: float
    max: float
    percentiles: dict = field(default_factory=dict)
    value_at_risk: dict = field(default_factory=dict)


@dataclass
class RiskQuantification:
    scenario: RiskScenario
    fair_model: FAIRModel
    monte_carlo_result: MonteCarloResult
    risk_score: float
    risk_level: str
    recommendation: str
    calculated_at: str = ""


@dataclass
class RiskRegisterEntry:
    scenario: RiskScenario
    quantification: Optional[RiskQuantification] = None
    status: str = "identified"
    treatment_strategy: str = ""
    treatment_plan: str = ""
    last_assessed: str = ""
    next_review: str = ""


# ── FAIR Calculator ───────────────────────────────────────────────────────

class FAIRCalculator:
    """FAIR (Factor Analysis of Information Risk) model implementation."""

    def __init__(self, scenario: RiskScenario, iterations: int = 10000, seed: int = 42):
        self.scenario = scenario
        self.iterations = iterations
        self.rng = random.Random(seed)

    def calculate(self) -> FAIRModel:
        """Calculate FAIR model components."""
        # Threat Event Frequency (TEF)
        tef = self.scenario.impact.mean * 52  # Annualized

        # Threat Capability (simplified)
        threat_capability = tef

        # Vulnerability
        vuln = self.scenario.probability.mean

        # Primary Loss
        primary_loss = self.scenario.impact.mean

        # Secondary Loss
        secondary_loss_freq = 0.15
        secondary_loss_mag = self.scenario.impact.mean * 0.2

        # Loss Event Frequency
        lef = tef * vuln

        # Loss Magnitude
        lm = primary_loss + secondary_loss_freq * secondary_loss_mag

        # Annualized Loss Expectancy
        ale = lef * lm

        return FAIRModel(
            threat_event_frequency=tef,
            threat_capability=threat_capability,
            vulnerability=vuln,
            primary_loss=primary_loss,
            secondary_loss_frequency=secondary_loss_freq,
            secondary_loss_magnitude=secondary_loss_mag,
            loss_event_frequency=lef,
            loss_magnitude=lm,
            annualized_loss_expectancy=ale,
        )


# ── Monte Carlo Engine ────────────────────────────────────────────────────

class MonteCarloEngine:
    """Monte Carlo simulation for risk quantification."""

    def __init__(self, scenario: RiskScenario, iterations: int = 10000, seed: int = 42):
        self.scenario = scenario
        self.iterations = iterations
        self.rng = random.Random(seed)

    def run(self) -> MonteCarloResult:
        """Run Monte Carlo simulation."""
        samples = []
        for _ in range(self.iterations):
            # Sample probability
            prob = self._sample_distribution(self.scenario.probability)
            # Sample impact
            impact = self._sample_distribution(self.scenario.impact)
            # Calculate loss
            loss = prob * impact
            samples.append(loss)

        samples.sort()
        n = len(samples)
        mean = sum(samples) / n
        variance = sum((s - mean) ** 2 for s in samples) / n
        std_dev = math.sqrt(variance)

        def percentile(p):
            idx = (p / 100) * (n - 1)
            lo = int(math.floor(idx))
            hi = int(math.ceil(idx))
            return samples[lo] * (1 - (idx - lo)) + samples[hi] * (idx - lo)

        return MonteCarloResult(
            iterations=self.iterations,
            mean=round(mean, 2),
            std_dev=round(std_dev, 2),
            variance=round(variance, 2),
            min=round(samples[0], 2),
            max=round(samples[-1], 2),
            percentiles={
                "P10": round(percentile(10), 2),
                "P25": round(percentile(25), 2),
                "P50": round(percentile(50), 2),
                "P75": round(percentile(75), 2),
                "P90": round(percentile(90), 2),
                "P95": round(percentile(95), 2),
                "P99": round(percentile(99), 2),
            },
            value_at_risk={
                "confidence95": round(percentile(95), 2),
                "confidence99": round(percentile(99), 2),
            },
        )

    def _sample_distribution(self, params: DistributionParams) -> float:
        """Sample from a distribution."""
        if params.type == DistributionType.NORMAL.value:
            return max(0, self.rng.gauss(params.mean, params.std_dev))
        elif params.type == DistributionType.LOGNORMAL.value:
            mu = math.log(params.mean ** 2 / math.sqrt(params.std_dev ** 2 + params.mean ** 2))
            sigma = math.sqrt(math.log(1 + params.std_dev ** 2 / params.mean ** 2))
            return math.exp(self.rng.gauss(mu, sigma))
        elif params.type == DistributionType.UNIFORM.value:
            return self.rng.uniform(params.min, params.max)
        elif params.type == DistributionType.TRIANGULAR.value:
            u = self.rng.random()
            fc = (params.mode - params.min) / (params.max - params.min)
            if u < fc:
                return params.min + math.sqrt(u * (params.max - params.min) * (params.mode - params.min))
            else:
                return params.max - math.sqrt((1 - u) * (params.max - params.min) * (params.max - params.mode))
        elif params.type == DistributionType.BETA_PERT.value:
            # Simplified PERT
            mu = (params.min + 4 * params.mode + params.max) / 6
            sigma = (params.max - params.min) / 6
            return max(params.min, min(params.max, self.rng.gauss(mu, sigma)))
        return params.mean


# ── Risk Register ─────────────────────────────────────────────────────────

class RiskRegister:
    """Manages risk scenarios, quantification, and treatment."""

    def __init__(self, iterations: int = 10000, seed: int = 42):
        self.entries: dict[str, RiskRegisterEntry] = {}
        self.iterations = iterations
        self.seed = seed
        self.trends: list = []

    def add_scenario(self, scenario: RiskScenario):
        """Add and quantify a risk scenario."""
        q = self.quantify(scenario)
        self.entries[scenario.id] = RiskRegisterEntry(
            scenario=scenario,
            quantification=q,
            status=RiskStatus.ASSESSED.value,
            last_assessed=datetime.utcnow().isoformat(),
            next_review=(datetime.utcnow() + timedelta(days=90)).isoformat(),
        )
        self.trends.append({
            "date": datetime.utcnow().isoformat(),
            "riskScore": q.risk_score,
            "ale": q.fair_model.annualized_loss_expectancy,
            "scenarioId": scenario.id,
        })

    def quantify(self, scenario: RiskScenario) -> RiskQuantification:
        """Quantify risk using FAIR and Monte Carlo."""
        fair_calc = FAIRCalculator(scenario, self.iterations, self.seed)
        fair_model = fair_calc.calculate()

        mc_engine = MonteCarloEngine(scenario, self.iterations, self.seed)
        mc_result = mc_engine.run()

        # Compute risk score
        score = self._compute_risk_score(
            fair_model.annualized_loss_expectancy,
            mc_result.value_at_risk["confidence95"],
            mc_result.iterations,
        )
        level = self._risk_level(score)
        recommendation = self._recommendation(level, fair_model.annualized_loss_expectancy)

        return RiskQuantification(
            scenario=scenario,
            fair_model=fair_model,
            monte_carlo_result=mc_result,
            risk_score=score,
            risk_level=level.value,
            recommendation=recommendation,
            calculated_at=datetime.utcnow().isoformat(),
        )

    def _compute_risk_score(self, ale: float, var95: float, iterations: int) -> float:
        ale_score = min(50, (math.log10(ale + 1) / 8) * 50)
        tail_score = min(30, (math.log10(var95 + 1) / 8) * 30)
        freq_score = min(20, (iterations > 0) * 20)
        return round(min(100, ale_score + tail_score + freq_score))

    def _risk_level(self, score: float) -> RiskLevel:
        if score >= 90:
            return RiskLevel.CRITICAL
        elif score >= 70:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        elif score >= 20:
            return RiskLevel.LOW
        return RiskLevel.NEGLIGIBLE

    def _recommendation(self, level: RiskLevel, ale: float) -> str:
        formatted = round(ale)
        if level == RiskLevel.CRITICAL:
            return f"CRITICAL: ALE of ${formatted:,} requires immediate mitigation."
        elif level == RiskLevel.HIGH:
            return f"HIGH: ALE of ${formatted:,} warrants priority treatment within 30 days."
        elif level == RiskLevel.MEDIUM:
            return f"MEDIUM: ALE of ${formatted:,} should be monitored with periodic reassessment."
        elif level == RiskLevel.LOW:
            return f"LOW: ALE of ${formatted:,} is within acceptable range. Monitor annually."
        return f"NEGLIGIBLE: ALE of ${formatted:,} poses minimal threat. Accept risk."

    def apply_treatment(self, scenario_id: str, strategy: TreatmentStrategy, plan: str) -> bool:
        """Apply a risk treatment strategy."""
        entry = self.entries.get(scenario_id)
        if not entry:
            return False

        entry.treatment_strategy = strategy.value
        entry.treatment_plan = plan
        entry.status = RiskStatus.TREATED.value
        return True

    def accept_risk(self, scenario_id: str, rationale: str) -> bool:
        """Accept a risk with documented rationale."""
        entry = self.entries.get(scenario_id)
        if not entry:
            return False

        entry.treatment_strategy = TreatmentStrategy.ACCEPT.value
        entry.treatment_plan = rationale
        entry.status = RiskStatus.ACCEPTED.value
        return True

    def get_portfolio_metrics(self) -> dict:
        """Get portfolio-level risk metrics."""
        active = [e for e in self.entries.values() if e.status in (RiskStatus.ASSESSED.value, RiskStatus.MONITORING.value)]
        total_ale = sum(e.quantification.fair_model.annualized_loss_expectancy for e in active if e.quantification)
        total_var95 = sum(e.quantification.monte_carlo_result.value_at_risk["confidence95"] for e in active if e.quantification)
        total_var99 = sum(e.quantification.monte_carlo_result.value_at_risk["confidence99"] for e in active if e.quantification)
        scores = [e.quantification.risk_score for e in active if e.quantification]
        critical = sum(1 for e in active if e.quantification and e.quantification.risk_level == RiskLevel.CRITICAL.value)
        high = sum(1 for e in active if e.quantification and e.quantification.risk_level == RiskLevel.HIGH.value)

        return {
            "totalALE": round(total_ale, 2),
            "totalVaR95": round(total_var95, 2),
            "totalVaR99": round(total_var99, 2),
            "meanRiskScore": round(sum(scores) / len(scores), 1) if scores else 0,
            "criticalCount": critical,
            "highCount": high,
            "scenarioCount": len(active),
        }

    def generate_heat_map(self, bins: int = 5) -> dict:
        """Generate risk heat map."""
        active = [e for e in self.entries.values() if e.quantification and e.status in (RiskStatus.ASSESSED.value, RiskStatus.MONITORING.value)]
        cells = []
        for l in range(bins):
            for i in range(bins):
                cells.append({"likelihood": l, "impact": i, "scenarios": [], "totalRisk": 0})

        max_ale = max((e.quantification.fair_model.annualized_loss_expectancy for e in active), default=1)

        for entry in active:
            q = entry.quantification
            likelihood_bin = min(bins - 1, int((q.fair_model.loss_event_frequency / 100) * bins))
            impact_bin = min(bins - 1, int((q.fair_model.loss_magnitude / (max_ale or 1)) * bins))
            idx = likelihood_bin * bins + impact_bin
            cells[idx]["scenarios"].append(entry.scenario.id)
            cells[idx]["totalRisk"] += q.fair_model.annualized_loss_expectancy

        return {"cells": cells, "axisLabels": {"x": "Impact", "y": "Likelihood"}}

    def assess_appetite(self, max_score: float = 70, max_ale: float = 1000000, max_var95: float = 2000000) -> dict:
        """Assess risk against appetite thresholds."""
        active = [e for e in self.entries.values() if e.quantification]
        tolerable = []
        exceedances = []

        for entry in active:
            q = entry.quantification
            over_score = q.risk_score > max_score
            over_ale = q.fair_model.annualized_loss_expectancy > max_ale
            over_var = q.monte_carlo_result.value_at_risk["confidence95"] > max_var95
            if over_score or over_ale or over_var:
                exceedances.append(entry.scenario.id)
            else:
                tolerable.append(entry.scenario.id)

        return {
            "maxRiskScore": max_score,
            "maxALE": max_ale,
            "maxVaR95": max_var95,
            "tolerableScenarios": tolerable,
            "boundaryExceedances": exceedances,
        }

    def top_risks(self, count: int = 10) -> list:
        """Get top risks by score."""
        active = [e for e in self.entries.values() if e.quantification]
        sorted_entries = sorted(active, key=lambda e: e.quantification.risk_score, reverse=True)
        return [e.quantification for e in sorted_entries[:count]]


# ── Demo Runner ────────────────────────────────────────────────────────────

def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_section(title: str):
    print(f"\n--- {title} ---")


def run_demo():
    print_header("GRC_Claw Risk Assessment Demo")
    print("Demonstrating: SCORE → TREAT → MONITOR")

    register = RiskRegister(iterations=10000, seed=42)

    # ════════════════════════════════════════════════════════════════════
    # PHASE 1: SCORE
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 1: SCORE — FAIR Analysis & Monte Carlo Simulation")

    print_section("Defining Risk Scenarios")

    scenarios = [
        RiskScenario(
            id="risk-001",
            name="Data Breach via Phishing",
            threat="Phishing attack targeting employees",
            vulnerability="Insufficient security awareness training",
            impact=DistributionParams(type="lognormal", mean=500000, std_dev=200000),
            probability=DistributionParams(type="normal", mean=0.3, std_dev=0.1),
            tags=["cyber", "data-breach"],
            owner="CISO",
        ),
        RiskScenario(
            id="risk-002",
            name="Ransomware Infection",
            threat="Ransomware delivered via email",
            vulnerability="Outdated endpoint protection",
            impact=DistributionParams(type="lognormal", mean=1000000, std_dev=500000),
            probability=DistributionParams(type="normal", mean=0.15, std_dev=0.05),
            tags=["cyber", "ransomware"],
            owner="CISO",
        ),
        RiskScenario(
            id="risk-003",
            name="Cloud Misconfiguration",
            threat="Public exposure of cloud storage",
            vulnerability="Lack of cloud security posture management",
            impact=DistributionParams(type="normal", mean=200000, std_dev=50000),
            probability=DistributionParams(type="normal", mean=0.4, std_dev=0.15),
            tags=["cloud", "misconfiguration"],
            owner="Cloud Architect",
        ),
        RiskScenario(
            id="risk-004",
            name="Insider Threat",
            threat="Malicious data exfiltration by employee",
            vulnerability="Insufficient DLP controls",
            impact=DistributionParams(type="lognormal", mean=800000, std_dev=300000),
            probability=DistributionParams(type="normal", mean=0.05, std_dev=0.02),
            tags=["insider", "data-loss"],
            owner="Security Director",
        ),
        RiskScenario(
            id="risk-005",
            name="Third-Party Breach",
            threat="Supply chain compromise via vendor",
            vulnerability="Inadequate vendor security assessment",
            impact=DistributionParams(type="lognormal", mean=600000, std_dev=250000),
            probability=DistributionParams(type="normal", mean=0.1, std_dev=0.05),
            tags=["supply-chain", "third-party"],
            owner="Vendor Manager",
        ),
        RiskScenario(
            id="risk-006",
            name="DDoS Attack",
            threat="Distributed denial of service",
            vulnerability="Insufficient DDoS mitigation capacity",
            impact=DistributionParams(type="normal", mean=150000, std_dev=50000),
            probability=DistributionParams(type="normal", mean=0.25, std_dev=0.1),
            tags=["availability", "ddos"],
            owner="Network Engineer",
        ),
        RiskScenario(
            id="risk-007",
            name="AI Model Poisoning",
            threat="Adversarial manipulation of training data",
            vulnerability="Lack of model integrity verification",
            impact=DistributionParams(type="lognormal", mean=400000, std_dev=150000),
            probability=DistributionParams(type="normal", mean=0.08, std_dev=0.03),
            tags=["ai", "model-security"],
            owner="AI Lead",
        ),
        RiskScenario(
            id="risk-008",
            name="Regulatory Fine",
            threat="GDPR violation penalty",
            vulnerability="Incomplete data mapping and consent management",
            impact=DistributionParams(type="uniform", min=100000, max=2000000),
            probability=DistributionParams(type="normal", mean=0.12, std_dev=0.04),
            tags=["compliance", "regulatory"],
            owner="DPO",
        ),
    ]

    for s in scenarios:
        print(f"  • {s.id}: {s.name} (Owner: {s.owner})")

    print_section("Running FAIR Analysis & Monte Carlo Simulation")
    for s in scenarios:
        register.add_scenario(s)
        q = register.entries[s.id].quantification
        level_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "negligible": "⚪"}.get(q.risk_level, "⚪")
        print(f"  {level_icon} {s.name}")
        print(f"     Score: {q.risk_score}/100 ({q.risk_level.upper()})")
        print(f"     ALE: ${q.fair_model.annualized_loss_expectancy:,.0f}")
        print(f"     VaR 95%: ${q.monte_carlo_result.value_at_risk['confidence95']:,.0f}")
        print(f"     LEF: {q.fair_model.loss_event_frequency:.2f}, LM: ${q.fair_model.loss_magnitude:,.0f}")

    # ════════════════════════════════════════════════════════════════════
    # PHASE 2: TREAT
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 2: TREAT — Risk Treatment Strategies")

    print_section("Applying Treatment Strategies")

    treatments = [
        ("risk-001", TreatmentStrategy.MITIGATE, "Deploy advanced email security gateway, implement security awareness training program, and deploy DMARC/DKIM/SPF"),
        ("risk-002", TreatmentStrategy.MITIGATE, "Upgrade endpoint protection to EDR, implement application whitelisting, and deploy network segmentation"),
        ("risk-003", TreatmentStrategy.MITIGATE, "Deploy CSPM tool, implement infrastructure-as-code with policy validation, and enable cloud audit logging"),
        ("risk-004", TreatmentStrategy.MITIGATE, "Deploy DLP solution, implement user behavior analytics, and enforce least-privilege access"),
        ("risk-005", TreatmentStrategy.TRANSFER, "Require cyber insurance for all critical vendors, include security requirements in contracts"),
        ("risk-006", TreatmentStrategy.MITIGATE, "Deploy DDoS mitigation service, implement rate limiting, and establish incident response playbook"),
        ("risk-007", TreatmentStrategy.MITIGATE, "Implement model integrity verification, deploy adversarial testing framework, and establish model monitoring"),
        ("risk-008", TreatmentStrategy.ACCEPT, "Risk accepted with current compliance program; annual review of data mapping and consent management"),
    ]

    for scenario_id, strategy, plan in treatments:
        register.apply_treatment(scenario_id, strategy, plan)
        entry = register.entries[scenario_id]
        print(f"  ✓ {entry.scenario.name}")
        print(f"     Strategy: {strategy.value.upper()}")
        print(f"     Plan: {plan[:80]}...")

    print_section("Risk Acceptance")
    register.accept_risk("risk-008", "Risk within appetite; annual review scheduled")
    print(f"  ✓ risk-008 accepted with documented rationale")

    # ════════════════════════════════════════════════════════════════════
    # PHASE 3: MONITOR
    # ════════════════════════════════════════════════════════════════════
    print_header("PHASE 3: MONITOR — Portfolio Metrics & Heat Maps")

    print_section("Portfolio Risk Metrics")
    metrics = register.get_portfolio_metrics()
    print(f"  Total ALE: ${metrics['totalALE']:,.0f}")
    print(f"  Total VaR 95%: ${metrics['totalVaR95']:,.0f}")
    print(f"  Total VaR 99%: ${metrics['totalVaR99']:,.0f}")
    print(f"  Mean Risk Score: {metrics['meanRiskScore']}/100")
    print(f"  Critical Risks: {metrics['criticalCount']}")
    print(f"  High Risks: {metrics['highCount']}")
    print(f"  Active Scenarios: {metrics['scenarioCount']}")

    print_section("Risk Heat Map (5x5)")
    heat_map = register.generate_heat_map(bins=5)
    print(f"  {'Impact→':>12} {'Low':>8} {'Med-L':>8} {'Medium':>8} {'Med-H':>8} {'High':>8}")
    for l in range(5):
        row_label = ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"][l]
        row = f"  {row_label:>12}"
        for i in range(5):
            idx = l * 5 + i
            cell = heat_map["cells"][idx]
            count = len(cell["scenarios"])
            row += f" {count:>8}"
        print(row)

    print_section("Risk Appetite Assessment")
    appetite = register.assess_appetite(max_score=70, max_ale=500000, max_var95=1000000)
    print(f"  Max Risk Score: {appetite['maxRiskScore']}")
    print(f"  Max ALE: ${appetite['maxALE']:,.0f}")
    print(f"  Max VaR 95%: ${appetite['maxVaR95']:,.0f}")
    print(f"  Tolerable: {len(appetite['tolerableScenarios'])} scenarios")
    print(f"  Exceedances: {len(appetite['boundaryExceedances'])} scenarios")
    if appetite['boundaryExceedances']:
        for eid in appetite['boundaryExceedances']:
            entry = register.entries[eid]
            print(f"    ⚠ {entry.scenario.name} (Score: {entry.quantification.risk_score})")

    print_section("Top 5 Risks")
    top = register.top_risks(5)
    for i, q in enumerate(top, 1):
        print(f"  {i}. {q.scenario.name}")
        print(f"     Score: {q.risk_score}/100 | ALE: ${q.fair_model.annualized_loss_expectancy:,.0f} | Level: {q.risk_level.upper()}")

    # ════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ════════════════════════════════════════════════════════════════════
    print_header("DEMO COMPLETE")
    print(f"""
Summary:
  • Scored {len(scenarios)} risk scenarios using FAIR analysis
  • Ran {register.iterations:,} Monte Carlo iterations per scenario
  • Applied {len(treatments)} treatment strategies (mitigate, transfer, accept)
  • Portfolio ALE: ${metrics['totalALE']:,.0f}
  • Critical risks: {metrics['criticalCount']}, High risks: {metrics['highCount']}
  • Generated 5x5 risk heat map
  • Assessed {len(appetite['boundaryExceedances'])} appetite exceedances

Key Capabilities Demonstrated:
  ✓ FAIR (Factor Analysis of Information Risk) modeling
  ✓ Monte Carlo simulation with 10,000 iterations
  ✓ Multiple distribution types (normal, lognormal, uniform, triangular, betaPERT)
  ✓ Risk scoring (0-100) with level classification
  ✓ Annualized Loss Expectancy (ALE) calculation
  ✓ Value at Risk (VaR) at 95% and 99% confidence
  ✓ Risk treatment strategies (mitigate, transfer, accept, avoid)
  ✓ Portfolio-level risk metrics
  ✓ Risk heat map generation
  ✓ Risk appetite assessment
  ✓ Top-N risk ranking
""")


if __name__ == "__main__":
    run_demo()
