# GRC_Claw Risk Assessment Framework — Quantitative Deepening

**Document ID:** GRC-RISK-002  
**Version:** 2.0  
**Date:** 2026-10-01  
**Owner:** GRC_Claw Architecture Team  
**Status:** Draft for Review  
**Supersedes:** GRC-RISK-001 (grc-claw-risk-assessment-framework.md)  
**References:** grc-claw-unified-metrics-layer.md (GRC-METRICS-001)

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Monte Carlo Risk Simulation Methodology](#2-monte-carlo-risk-simulation-methodology)
3. [Risk Correlation Modeling](#3-risk-correlation-modeling)
4. [Cascading Risk Propagation Algorithm](#4-cascading-risk-propagation-algorithm)
5. [Risk Appetite Quantification](#5-risk-appetite-quantification)
6. [Risk Treatment Optimization](#6-risk-treatment-optimization)
7. [Risk Reporting Automation with Trend Analysis](#7-risk-reporting-automation-with-trend-analysis)
8. [Integration with Existing Framework](#8-integration-with-existing-framework)
9. [Appendices](#9-appendices)

---

## 1. Purpose & Scope

### 1.1 Purpose

This document deepens the GRC_Claw Risk Assessment Framework (GRC-RISK-001) with six quantitative capabilities:

1. **Monte Carlo Risk Simulation** — Probabilistic modeling of risk outcomes beyond point estimates
2. **Risk Correlation Modeling** — Statistical dependencies between risks that amplify or dampen aggregate exposure
3. **Cascading Risk Propagation** — Algorithmic modeling of how risk materialization triggers downstream risks
4. **Risk Appetite Quantification** — Quantitative risk appetite metrics with economic grounding
5. **Risk Treatment Optimization** — Cost-benefit optimization of treatment portfolios under budget constraints
6. **Risk Reporting Automation** — Automated report generation with statistical trend analysis and anomaly detection

### 1.2 Design Principles

1. **Probabilistic, not deterministic** — Risk is modeled as distributions, not point estimates
2. **Systemic, not isolated** — Risk interdependencies are first-class citizens
3. **Economic, not abstract** — Risk appetite and treatment decisions are grounded in financial terms
4. **Automated, not manual** — Reporting and trend analysis run continuously without human intervention
5. **Auditable, not black-box** — Every simulation parameter and correlation assumption is documented and versioned

### 1.3 Relationship to GRC-RISK-001

This document **extends** GRC-RISK-001. The MDRS scoring (§4), taxonomy (§3), treatment workflow (§7), and monitoring framework (§8) from the original document remain authoritative. This document adds quantitative depth to those foundations.

---

## 2. Monte Carlo Risk Simulation Methodology

### 2.1 Overview

The MDRS score in GRC-RISK-001 is a **point estimate** — a single number representing expected risk. Monte Carlo simulation replaces point estimates with **probability distributions**, enabling:

- **Value-at-Risk (VaR)** — "What is the 95th percentile of aggregate risk?"
- **Expected Shortfall (ES)** — "If things go bad, how bad on average?"
- **Probability of threshold breach** — "What is the chance aggregate risk exceeds appetite?"
- **Sensitivity analysis** — "Which risks contribute most to tail outcomes?"

### 2.2 Input Distributions

Each MDRS dimension is modeled as a probability distribution rather than a fixed score:

| Dimension | Distribution | Parameters | Rationale |
|-----------|-------------|------------|-----------|
| **Likelihood (L)** | Beta(α, β) | α = L_score, β = 6 − L_score | Bounded [1,5], flexible shape |
| **Impact (I)** | Triangular(a, b, c) | a = max(1, I−1), b = I, c = min(5, I+1) | Bounded, mode at point estimate |
| **Detectability (D)** | Beta(α, β) | α = D_score, β = 6 − D_score | Bounded [1,5] |
| **Velocity (V)** | Triangular(a, b, c) | a = max(1, V−1), b = V, c = min(5, V+1) | Bounded, mode at point estimate |
| **Persistence (P)** | Beta(α, β) | α = P_score, β = 6 − P_score | Bounded [1,5] |

**Beta distribution** is used for dimensions where the point estimate is the most likely value (Likelihood, Detectability, Persistence). **Triangular distribution** is used for dimensions where the point estimate is the mode but uncertainty is symmetric (Impact, Velocity).

### 2.3 Simulation Algorithm

```
ALGORITHM: Monte Carlo Risk Simulation

INPUT:
  - risks[]: Array of N risks, each with MDRS dimension distributions
  - correlation_matrix: N×N correlation matrix (see §3)
  - n_simulations: Number of simulation iterations (default: 10,000)
  - time_horizon: Projection period in days (default: 365)

OUTPUT:
  - aggregate_risk_distribution: Simulated distribution of portfolio risk
  - var_95: 95th percentile Value-at-Risk
  - var_99: 99th percentile Value-at-Risk
  - expected_shortfall_95: Mean of outcomes exceeding VaR_95
  - probability_of_breach: P(aggregate risk > risk_appetite_threshold)
  - risk_contributions: Per-risk contribution to aggregate tail risk

PROCEDURE:
  1. FOR simulation = 1 TO n_simulations:
     a. FOR each risk i in risks:
        - Sample L_i ~ Beta(α_Li, β_Li)
        - Sample I_i ~ Triangular(a_Ii, b_Ii, c_Ii)
        - Sample D_i ~ Beta(α_Di, β_Di)
        - Sample V_i ~ Triangular(a_Vi, b_Vi, c_Vi)
        - Sample P_i ~ Beta(α_Pi, β_Pi)
        - Compute MDRS_i = (L_i × 0.25) + (I_i × 0.30) + (D_i × 0.15) + (V_i × 0.15) + (P_i × 0.15)
     
     b. Apply correlation adjustment:
        - Generate correlated normal variates Z ~ N(0, correlation_matrix)
        - Transform to uniform via Φ(Z)
        - Apply inverse CDF to each dimension distribution
        - Recompute MDRS_i with correlated samples
     
     c. Compute aggregate risk:
        - Portfolio_MDRS = Σ(MDRS_i × weight_i) / Σ(weight_i)
        - where weight_i = business_criticality(risk_i)
     
     d. Store Portfolio_MDRS in aggregate_risk_distribution
  
  2. Compute statistics from aggregate_risk_distribution:
     - var_95 = Percentile(aggregate_risk_distribution, 95)
     - var_99 = Percentile(aggregate_risk_distribution, 99)
     - expected_shortfall_95 = Mean(outcomes where outcome > var_95)
     - probability_of_breach = Count(outcomes > appetite_threshold) / n_simulations
  
  3. Compute risk contributions via Shapley value decomposition:
     - For each risk i, compute marginal contribution to VaR_95
     - risk_contributions[i] = ShapleyValue(risk_i, aggregate_risk_distribution)
  
  4. RETURN results
```

### 2.4 Simulation Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| n_simulations | 10,000 | 1,000–1,000,000 | More iterations = smoother tails, higher compute cost |
| time_horizon | 365 days | 30–1,825 days | Projection period for risk evolution |
| confidence_level | 95% | 90%–99% | VaR/ES confidence level |
| random_seed | Configurable | Any integer | Reproducibility control |
| correlation_method | Gaussian copula | Gaussian, t-copula, vine | Dependency structure model |

### 2.5 Output: Risk Simulation Report

```json
{
  "simulation_id": "SIM-2026-Q4-001",
  "timestamp": "2026-10-01T00:00:00Z",
  "parameters": {
    "n_simulations": 10000,
    "time_horizon_days": 365,
    "confidence_level": 0.95,
    "correlation_method": "gaussian_copula",
    "random_seed": 42
  },
  "portfolio_results": {
    "mean_aggregate_mdrs": 2.87,
    "median_aggregate_mdrs": 2.82,
    "std_deviation": 0.43,
    "var_95": 3.58,
    "var_99": 4.12,
    "expected_shortfall_95": 3.89,
    "probability_of_breach": 0.12,
    "appetite_threshold": 3.49
  },
  "risk_contributions": [
    {"risk_id": "RISK-2026-0001", "category": "DAT-03", "shapley_contribution": 0.18, "rank": 1},
    {"risk_id": "RISK-2026-0002", "category": "SEC-02", "shapley_contribution": 0.15, "rank": 2}
  ],
  "sensitivity_analysis": {
    "most_sensitive_dimension": "Impact",
    "elasticity": 1.32,
    "interpretation": "A 1% increase in Impact scores leads to 1.32% increase in aggregate MDRS"
  },
  "tail_scenarios": [
    {"scenario": "worst_1pct", "aggregate_mdrs": 4.12, "description": "Simultaneous materialization of top 5 correlated risks"}
  ]
}
```

### 2.6 Time-Evolved Simulation

For multi-period risk projection, the simulation incorporates **risk drift**:

```
MDRS_i(t) = MDRS_i(0) + drift_i × t + σ_i × √t × Z_t

Where:
  - drift_i = Expected change in MDRS per unit time (from trend analysis, §7)
  - σ_i = Volatility of MDRS (from historical variance)
  - Z_t = Standard Brownian motion increment
  - t = Time step
```

This produces a **risk trajectory distribution** rather than a single snapshot, enabling forward-looking risk planning.

---

## 3. Risk Correlation Modeling

### 3.1 Why Correlation Matters

GRC-RISK-001 §6.4 models risk interdependencies qualitatively (directed graph). This section formalizes the **quantitative correlation structure** that drives Monte Carlo simulation and cascading propagation.

**Key insight:** Risks that are positively correlated amplify tail outcomes. A portfolio of 10 risks each at MDRS 3.0 is far more dangerous if they are perfectly correlated (all materialize together) than if they are independent (materialization is diversified).

### 3.2 Correlation Sources

Risk correlations arise from three sources:

| Source | Description | Example |
|--------|-------------|---------|
| **Shared Causal Factor** | Common underlying cause | DAT-03 (Bias) and HUM-02 (Group Discrimination) both stem from training data |
| **Trigger Relationship** | One risk directly triggers another | SEC-01 (Prompt Injection) → SEC-02 (Goal Hijacking) |
| **Common Control Dependency** | Shared control failure | OPS-01 (Monitoring Gap) amplifies all SEC risks |

### 3.3 Correlation Matrix Construction

The N×N correlation matrix **R** is constructed from three components:

```
R = α × R_causal + β × R_trigger + γ × R_control

Where:
  - R_causal: Correlation from shared causal factors (domain-level)
  - R_trigger: Correlation from trigger relationships (category-level)
  - R_control: Correlation from shared control dependencies (control-level)
  - α + β + γ = 1.0 (weights sum to 1)
```

#### 3.3.1 Domain-Level Correlation (R_causal)

Risks within the same domain share causal factors:

| Domain Pair | Correlation | Rationale |
|-------------|-------------|-----------|
| DAT ↔ HUM | 0.45 | Data quality directly impacts human/societal outcomes |
| SEC ↔ OPS | 0.40 | Security incidents trigger operational failures |
| MOD ↔ DAT | 0.35 | Model performance depends on data quality |
| TPR ↔ SEC | 0.30 | Supply chain risks are security risks |
| CMP ↔ GOV | 0.35 | Compliance failures stem from governance gaps |
| HUM ↔ CMP | 0.25 | Human harm risks create compliance exposure |
| OPS ↔ MOD | 0.30 | Operational issues affect model performance |
| GOV ↔ TPR | 0.20 | Governance gaps enable third-party risks |

#### 3.3.2 Category-Level Correlation (R_trigger)

Specific category pairs with direct trigger relationships:

| Source Category | Target Category | Correlation | Mechanism |
|-----------------|-----------------|-------------|-----------|
| SEC-01 (Prompt Injection) | SEC-02 (Goal Hijacking) | 0.65 | Injection is the primary hijacking vector |
| SEC-02 (Goal Hijacking) | SEC-03 (Tool Misuse) | 0.60 | Hijacked goals drive tool abuse |
| SEC-03 (Tool Misuse) | DAT-04 (Privacy Violation) | 0.55 | Tool misuse enables data exfiltration |
| DAT-05 (Data Poisoning) | MOD-01 (Performance Degradation) | 0.50 | Poisoned data degrades model |
| DAT-05 (Data Poisoning) | MOD-06 (Hallucination) | 0.45 | Poisoned data increases hallucination |
| MOD-02 (Model Drift) | MOD-01 (Performance Degradation) | 0.55 | Drift leads to degradation |
| OPS-01 (Monitoring Gap) | All SEC categories | 0.30 | Undetected security risks persist |
| TPR-01 (Vendor AI Risk) | SEC-05 (Supply Chain Compromise) | 0.50 | Vendor risks are supply chain risks |
| GOV-02 (Accountability Gap) | All categories | 0.20 | Accountability gaps amplify all risks |
| CMP-01 (Prohibited Practice) | HUM-01 (Individual Harm) | 0.55 | Prohibited practices cause harm |

#### 3.3.3 Control-Level Correlation (R_control)

Risks sharing the same mitigation control are correlated through control failure:

| Shared Control | Affected Risks | Correlation |
|----------------|---------------|-------------|
| Input sanitization | SEC-01, SEC-02, SEC-06 | 0.40 |
| Monitoring system | OPS-01, MOD-01, MOD-02, SEC-07 | 0.35 |
| Data quality pipeline | DAT-01, DAT-03, DAT-05, MOD-01 | 0.30 |
| Identity management | SEC-04, OPS-04, TPR-01 | 0.35 |
| Human oversight | HUM-03, SEC-02, SEC-03 | 0.30 |

### 3.4 Correlation Matrix Validation

The correlation matrix must satisfy mathematical properties:

1. **Symmetry:** R[i][j] = R[j][i]
2. **Diagonal:** R[i][i] = 1.0
3. **Positive semi-definiteness:** All eigenvalues ≥ 0

**Validation procedure:**
```
1. Construct R from weighted components
2. Compute eigenvalues of R
3. If any eigenvalue < 0:
   a. Apply nearest correlation matrix algorithm (Higham, 2002)
   b. Document the correction applied
4. Store validated R in correlation registry with version
```

### 3.5 Dynamic Correlation Update

Correlations are not static. They are updated based on:

| Trigger | Update Method | Frequency |
|---------|--------------|-----------|
| New incident data | Bayesian update of correlation posterior | Per incident |
| Control implementation | Reduce correlation for risks sharing the new control | Per control deployment |
| Threat intelligence | Increase correlation for newly identified threat clusters | Continuous |
| Periodic review | Full recalibration from historical data | Quarterly |

### 3.6 Correlation Registry

```yaml
correlation_registry:
  version: "2026-Q4-v1"
  last_updated: "2026-10-01"
  method: "weighted_combination"
  weights:
    causal: 0.4
    trigger: 0.4
    control: 0.2
  matrix:
    # N×N correlation matrix stored as nested arrays
    # Indexed by risk_id
  validation:
    min_eigenvalue: 0.003
    is_positive_semi_definite: true
    correction_applied: "none"
  update_history:
    - date: "2026-10-01"
      trigger: "quarterly_review"
      changes: "Updated SEC-01→SEC-02 correlation from 0.60 to 0.65 based on Q3 incident data"
```

---

## 4. Cascading Risk Propagation Algorithm

### 4.1 Overview

GRC-RISK-001 §6.4 defines a simple cascading formula: `Effective MDRS = Base MDRS × (1 + 0.2 × Number of Active Upstream Risks)`. This section replaces that heuristic with a **formal propagation algorithm** that models:

- **Propagation probability** — Not all upstream risks trigger downstream risks
- **Propagation delay** — Cascading effects take time to materialize
- **Amplification/dampening** — Each hop can amplify or dampen the effect
- **Feedback loops** — Risks can cycle back and amplify themselves
- **Absorbing states** — Some risks terminate propagation

### 4.2 Risk Propagation Graph

The risk propagation graph is a **weighted directed graph** G = (V, E, W, P, D) where:

| Component | Type | Description |
|-----------|------|-------------|
| **V** | Set of nodes | Each risk in the register is a node |
| **E** | Set of edges | Directed edges represent propagation paths |
| **W** | Edge weights | Amplification factor per edge (0.0 to 2.0) |
| **P** | Edge probabilities | Probability of propagation per edge (0.0 to 1.0) |
| **D** | Edge delays | Time delay for propagation (in hours) |

### 4.3 Propagation Algorithm

```
ALGORITHM: Cascading Risk Propagation

INPUT:
  - G = (V, E, W, P, D): Risk propagation graph
  - initial_active: Set of initially materialized risk IDs
  - max_iterations: Maximum propagation rounds (default: 10)
  - convergence_threshold: Stop when score change < threshold (default: 0.01)

OUTPUT:
  - final_scores: Map of risk_id → effective MDRS after propagation
  - propagation_path: Ordered list of propagation events
  - cascade_depth: Maximum propagation depth reached
  - total_affected: Count of risks affected by cascade

PROCEDURE:
  1. Initialize:
     - active ← initial_active
     - effective_scores ← copy of base MDRS for all risks
     - propagation_path ← []
     - cascade_depth ← 0
     - changed ← true
     - iteration ← 0
  
  2. WHILE changed AND iteration < max_iterations:
     a. changed ← false
     b. iteration ← iteration + 1
     c. new_active ← ∅
     
     d. FOR each risk r in active:
        FOR each edge (r → s) in E:
          i. Compute propagation probability:
             P_prop = P(r→s) × (effective_scores[r] / 5.0)
             # Higher MDRS = higher propagation probability
          
          ii. IF random() < P_prop:
             - Compute amplification:
               amplification = W(r→s) × (effective_scores[r] / base_scores[r])
             - Compute time delay:
               delay = D(r→s) × (1 + log(effective_scores[r]))
             - Update effective score:
               new_score = effective_scores[s] × (1 + 0.1 × amplification)
               new_score = min(new_score, 5.0)  # Cap at 5.0
             
             - IF new_score - effective_scores[s] > convergence_threshold:
                 effective_scores[s] ← new_score
                 changed ← true
                 new_active ← new_active ∪ {s}
             
             - Record propagation event:
               propagation_path.append({
                 from: r,
                 to: s,
                 amplification: amplification,
                 delay_hours: delay,
                 new_score: new_score,
                 iteration: iteration
               })
     
     e. active ← new_active
     f. cascade_depth ← iteration
  
  3. total_affected ← count of risks where effective_scores[r] > base_scores[r]
  
  4. RETURN (effective_scores, propagation_path, cascade_depth, total_affected)
```

### 4.4 Propagation Edge Weights

Default edge weights based on empirical analysis of AI risk cascades:

| Source Category | Target Category | Weight (W) | Probability (P) | Delay (D) |
|-----------------|-----------------|------------|-----------------|-----------|
| SEC-01 | SEC-02 | 1.3 | 0.65 | 0.5h |
| SEC-02 | SEC-03 | 1.2 | 0.60 | 1.0h |
| SEC-03 | DAT-04 | 1.4 | 0.55 | 2.0h |
| SEC-03 | HUM-01 | 1.3 | 0.50 | 4.0h |
| DAT-05 | MOD-01 | 1.2 | 0.50 | 24h |
| DAT-05 | MOD-06 | 1.1 | 0.45 | 12h |
| MOD-02 | MOD-01 | 1.3 | 0.55 | 48h |
| MOD-01 | HUM-01 | 1.2 | 0.40 | 24h |
| OPS-01 | SEC-07 | 1.4 | 0.30 | 1.0h |
| OPS-02 | OPS-03 | 1.2 | 0.50 | 4.0h |
| TPR-01 | SEC-05 | 1.3 | 0.50 | 72h |
| TPR-03 | MOD-01 | 1.2 | 0.45 | 168h |
| GOV-02 | All categories | 1.1 | 0.20 | 168h |
| CMP-01 | HUM-01 | 1.5 | 0.55 | 24h |
| CMP-01 | HUM-05 | 1.4 | 0.50 | 72h |
| HUM-01 | CMP-03 | 1.2 | 0.40 | 72h |
| SEC-07 | OPS-03 | 1.3 | 0.60 | 2.0h |
| SEC-07 | OPS-02 | 1.2 | 0.55 | 1.0h |

### 4.5 Feedback Loop Detection

Some risk cascades form **feedback loops** (e.g., SEC-07 → OPS-02 → OPS-01 → SEC-07). The algorithm detects and handles these:

```
1. Build adjacency matrix from propagation graph
2. Detect strongly connected components (Tarjan's algorithm)
3. For each SCC with > 1 node:
   a. Compute loop gain = product of edge weights in cycle
   b. If loop_gain > 1.0: Mark as "amplifying loop" — scores can grow unbounded
   c. If loop_gain < 1.0: Mark as "dampening loop" — scores converge
   d. If loop_gain ≈ 1.0: Mark as "sustaining loop" — scores stabilize
4. For amplifying loops, apply damping factor of 0.9 per iteration to prevent divergence
```

### 4.6 Cascade Impact Assessment

For each cascade event, compute:

| Metric | Formula | Description |
|--------|---------|-------------|
| **Cascade Depth** | Max iterations reached | How far the cascade propagated |
| **Cascade Breadth** | Count of unique risks affected | How many risks were touched |
| **Cascade Velocity** | Cascade depth / total delay | Speed of propagation |
| **Cascade Amplification** | Final effective score / Initial base score | How much the cascade amplified risk |
| **Cascade Severity** | Σ(effective_scores − base_scores) for all affected risks | Total risk increase from cascade |

### 4.7 Integration with Risk Register

Each risk register entry is extended with cascade metadata:

```json
{
  "risk_id": "RISK-2026-0001",
  "cascade_profile": {
    "upstream_risks": ["RISK-2026-0003", "RISK-2026-0007"],
    "downstream_risks": ["RISK-2026-0012"],
    "propagation_probability_out": 0.65,
    "propagation_probability_in": 0.40,
    "max_cascade_depth": 3,
    "cascade_amplification_factor": 1.35,
    "feedback_loop_member": false,
    "cascade_risk_tier": "High"
  }
}
```

---

## 5. Risk Appetite Quantification

### 5.1 Beyond Thresholds: Economic Risk Appetite

GRC-RISK-001 §4.6 defines risk appetite as MDRS thresholds per domain. This section adds **economic quantification** — translating risk appetite into financial terms that the Board can act upon.

### 5.2 Risk Appetite Statement (Quantitative)

```
GRC_Claw Risk Appetite Statement (Quantitative):

1. AGGREGATE RISK APPETITE
   - The organization accepts a maximum portfolio VaR_95 of 3.50 MDRS
   - The organization accepts a maximum expected shortfall of 4.00 MDRS
   - Probability of exceeding appetite threshold must be < 10%

2. DOMAIN-LEVEL APPETITE
   - Each domain has a maximum acceptable mean MDRS
   - Domain appetite is allocated from aggregate appetite via risk budget

3. SINGLE-RISK APPETITE
   - No single risk may exceed MDRS 4.50 without Risk Committee approval
   - No single risk may exceed MDRS 5.00 under any circumstances

4. ECONOMIC APPETITE
   - Maximum annual expected loss from AI risk: $X (Board-defined)
   - Maximum tail loss (99th percentile): $Y (Board-defined)
   - Risk-adjusted return on AI investment must exceed governance cost by > 1.0
```

### 5.3 Risk Budget Allocation

The aggregate risk appetite is allocated to domains using a **risk budget** approach:

```
Risk Budget Allocation:

Total Risk Budget = Aggregate Appetite × Total Risk Exposure

Domain Budget = Total Risk Budget × Domain Weight

Where Domain Weight is determined by:
  - Business criticality of the domain (40%)
  - Historical incident frequency (30%)
  - Regulatory scrutiny level (20%)
  - Current control maturity (10%)
```

| Domain | Weight | Risk Budget (MDRS) | Current Exposure | Headroom | Status |
|--------|--------|-------------------|-----------------|----------|--------|
| GOV | 10% | 0.35 | 0.28 | +0.07 | 🟢 Within |
| DAT | 18% | 0.63 | 0.58 | +0.05 | 🟢 Within |
| MOD | 15% | 0.53 | 0.49 | +0.04 | 🟢 Within |
| SEC | 22% | 0.77 | 0.82 | −0.05 | 🔴 Exceeded |
| HUM | 12% | 0.42 | 0.35 | +0.07 | 🟢 Within |
| OPS | 10% | 0.35 | 0.31 | +0.04 | 🟢 Within |
| TPR | 8% | 0.28 | 0.24 | +0.04 | 🟢 Within |
| CMP | 5% | 0.18 | 0.15 | +0.03 | 🟢 Within |

### 5.4 Risk Appetite Metrics

| Metric | Formula | Target | Alert Threshold |
|--------|---------|--------|-----------------|
| **Risk Appetite Utilization** | Current Exposure / Risk Budget | <80% | ≥90% |
| **Risk Appetite Headroom** | Risk Budget − Current Exposure | >0 | ≤0 |
| **Risk-Adjusted Return** | (Value Delivered − Expected Loss) / Governance Cost | >1.0 | <0.8 |
| **Risk Concentration Index** | Herfindahl index of risk distribution across domains | <0.25 | >0.35 |
| **Tail Risk Ratio** | Expected Shortfall / VaR_95 | <1.15 | >1.30 |
| **Risk Appetite Drift** | Δ Utilization over time | Stable | >5pp per quarter |

### 5.5 Risk Appetite Stress Testing

The risk appetite is stress-tested against scenarios:

| Scenario | Description | Appetite Impact | Mitigation Required |
|----------|-------------|-----------------|---------------------|
| **Simultaneous SEC cascade** | 3+ SEC risks materialize together | SEC budget exceeded by 40% | Pre-approved SEC mitigation playbook |
| **Major vendor failure** | TPR-01 + TPR-03 materialize | TPR budget exceeded by 60% | Vendor diversification plan |
| **Regulatory reclassification** | System reclassified to higher tier | CMP budget exceeded by 80% | Emergency conformity assessment |
| **Model drift cascade** | MOD-02 → MOD-01 → HUM-01 | MOD + HUM budgets exceeded | Accelerated retraining + human oversight |
| **Data poisoning + bias** | DAT-05 + DAT-03 + HUM-02 | DAT + HUM budgets exceeded | Data audit + bias remediation |

### 5.6 Risk Appetite Governance

| Role | Appetite Authority | Review Frequency |
|------|-------------------|-----------------|
| **Board** | Set aggregate economic appetite ($X, $Y) | Annually |
| **Risk Committee** | Set domain risk budgets | Quarterly |
| **CISO** | Set SEC domain appetite | Monthly |
| **CTO** | Set MOD domain appetite | Monthly |
| **AI Risk Officer** | Monitor utilization, recommend adjustments | Continuous |

---

## 6. Risk Treatment Optimization

### 6.1 Overview

GRC-RISK-001 §7 defines 4 treatment strategies (Avoid, Transfer, Mitigate, Accept) with a decision matrix. This section adds **quantitative optimization** — selecting the optimal treatment portfolio under budget constraints to maximize risk reduction per dollar spent.

### 6.2 Treatment Optimization Model

```
OBJECTIVE: Maximize total risk reduction subject to budget constraint

MAXIMIZE: Σ (RiskReduction_i × x_i) for all risks i

SUBJECT TO:
  1. Σ (Cost_i × x_i) ≤ TotalBudget
  2. x_i ∈ {0, 1} for each risk i (binary: treat or not)
  3. If risk_i is treated, residual_mdrs_i ≤ appetite_threshold_i
  4. Treatment dependencies: if control A requires control B, x_A ≤ x_B
  5. Minimum treatment count per domain ≥ regulatory_minimum

WHERE:
  - RiskReduction_i = Inherent_MDRS_i − Residual_MDRS_i (if treated)
  - Cost_i = Implementation cost + Operating cost (annualized)
  - x_i = 1 if risk i is treated, 0 otherwise
```

### 6.3 Treatment Cost Model

Each treatment has a cost profile:

| Cost Component | Description | Typical Range |
|----------------|-------------|---------------|
| **Implementation Cost** | One-time setup (tooling, configuration, training) | $5K–$500K |
| **Annual Operating Cost** | Recurring cost (monitoring, maintenance, licensing) | $1K–$100K/year |
| **Opportunity Cost** | Business value foregone (e.g., Avoid strategy) | $10K–$1M/year |
| **Residual Risk Cost** | Expected loss from remaining risk | MDRS × Exposure Factor |

**Total Cost of Treatment (TCT):**
```
TCT = Implementation_Cost + NPV(Annual_Operating_Cost, 3 years) + Opportunity_Cost
```

### 6.4 Treatment Effectiveness Model

Each treatment reduces MDRS dimensions:

| Treatment Strategy | Likelihood Reduction | Impact Reduction | Detectability Improvement | Cost Effectiveness |
|-------------------|---------------------|------------------|--------------------------|-------------------|
| **Avoid** | −100% | −100% | N/A | N/A (risk eliminated) |
| **Transfer** | −20% to −50% | −30% to −70% | 0% | High for catastrophic risks |
| **Mitigate** | −10% to −60% | −10% to −50% | −20% to −60% | Medium (depends on control) |
| **Accept** | 0% | 0% | 0% | N/A (no treatment cost) |

### 6.5 Optimization Algorithm

```
ALGORITHM: Risk Treatment Portfolio Optimization

INPUT:
  - risks[]: Array of risks with inherent MDRS and treatment options
  - budget: Total available treatment budget
  - constraints: Regulatory minimums, dependencies, domain requirements

OUTPUT:
  - optimal_portfolio: Set of risks to treat with selected strategies
  - expected_residual_risk: Portfolio MDRS after treatment
  - total_cost: Total cost of optimal portfolio
  - risk_reduction_achieved: Total MDRS reduction

PROCEDURE:
  1. FOR each risk i:
     a. Generate treatment options:
        - Option 0: Accept (cost = 0, reduction = 0)
        - Option 1: Mitigate (cost = C_mit, reduction = R_mit)
        - Option 2: Transfer (cost = C_tr, reduction = R_tr)
        - Option 3: Avoid (cost = C_av, reduction = R_av)
     b. Compute cost-effectiveness ratio for each option:
        CE = Reduction / Cost
  
  2. Sort all (risk, option) pairs by CE ratio descending
  
  3. Greedy selection with constraint checking:
     - Iterate through sorted pairs
     - Select option if:
       a. Budget not exceeded
       b. Regulatory minimums still satisfiable
       c. Dependencies not violated
     - Skip otherwise
  
  4. Local search improvement:
     - For each selected treatment, check if upgrading to a
       higher-cost option improves total reduction within budget
     - For each unselected risk, check if swapping with a selected
       treatment improves total reduction
  
  5. RETURN optimal_portfolio
```

### 6.6 Treatment Portfolio Report

```json
{
  "optimization_id": "OPT-2026-Q4-001",
  "timestamp": "2026-10-01T00:00:00Z",
  "budget": 500000,
  "optimal_portfolio": {
    "total_cost": 487000,
    "budget_utilization": 0.974,
    "risk_reduction_achieved": 12.35,
    "cost_effectiveness": 0.0254,
    "treatments": [
      {
        "risk_id": "RISK-2026-0001",
        "category": "DAT-03",
        "strategy": "Mitigate",
        "cost": 75000,
        "mdrs_reduction": 1.2,
        "cost_effectiveness": 0.000016,
        "residual_mdrs": 2.45
      },
      {
        "risk_id": "RISK-2026-0002",
        "category": "SEC-02",
        "strategy": "Mitigate",
        "cost": 120000,
        "mdrs_reduction": 1.8,
        "cost_effectiveness": 0.000015,
        "residual_mdrs": 2.40
      }
    ],
    "accepted_risks": [
      {"risk_id": "RISK-2026-0015", "category": "GOV-01", "residual_mdrs": 1.85}
    ]
  },
  "comparison": {
    "baseline_portfolio_mdrs": 3.42,
    "optimized_portfolio_mdrs": 2.89,
    "improvement": "15.5% reduction in aggregate MDRS",
    "roi": "2.3x (risk reduction value / treatment cost)"
  }
}
```

### 6.7 Treatment Strategy Selection Matrix (Quantitative)

| Risk Tier | Budget Available | Optimal Strategy | Expected Residual MDRS | Cost per MDRS Point Reduced |
|-----------|-----------------|------------------|----------------------|---------------------------|
| Critical (4.5–5.0) | >$200K | Mitigate + Transfer | 2.5–3.0 | $50K–$100K |
| Critical (4.5–5.0) | <$200K | Transfer | 3.0–3.5 | $30K–$60K |
| High (3.5–4.49) | >$100K | Mitigate | 2.5–3.0 | $25K–$50K |
| High (3.5–4.49) | <$100K | Transfer or Accept | 3.0–3.5 | $15K–$30K |
| Medium (2.5–3.49) | >$50K | Mitigate | 2.0–2.5 | $10K–$25K |
| Medium (2.5–3.49) | <$50K | Accept | 2.5–3.0 | N/A |
| Low (1.5–2.49) | Any | Accept | 1.5–2.49 | N/A |
| Minimal (1.0–1.49) | Any | Accept | 1.0–1.49 | N/A |

---

## 7. Risk Reporting Automation with Trend Analysis

### 7.1 Overview

GRC-RISK-001 §9 defines six report types with manual generation. This section adds **automated report generation** with **statistical trend analysis** — detecting patterns, anomalies, and inflection points in risk data over time.

### 7.2 Automated Report Generation Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                 AUTOMATED RISK REPORTING PIPELINE                    │
│                                                                       │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │ COLLECT  │──▶│ COMPUTE  │──▶│ ANALYZE  │──▶│ GENERATE │   │
│  │          │   │          │   │          │   │          │   │
│  │• Risk    │   │• MDRS    │   │• Trend   │   │• Format  │   │
│  │  register│   │  re-score│   │  detect  │   │• Distrib.│   │
│  │• KRI     │   │• Monte   │   │• Anomaly │   │• Deliver │   │
│  │  metrics │   │  Carlo   │   │  detect  │   │• Archive │   │
│  │• Control │   │• Cascade │   │• Forecast│   │          │   │
│  │  tests   │   │  prop.   │   │• Correl. │   │          │   │
│  │• Incident│   │• Treat.  │   │  change  │   │          │   │
│  │  data    │   │  optim.  │   │          │   │          │   │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   │
│                                                                       │
│  Schedule:                                                            │
│  • Real-time: KRI monitoring, threshold alerts                        │
│  • Daily: Trend analysis, anomaly detection                           │
│  • Weekly: Risk register summary, treatment progress                  │
│  • Monthly: Executive report, Monte Carlo simulation                  │
│  • Quarterly: Full risk posture, optimization, Board report           │
│  • Annually: Comprehensive risk review, framework update              │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Trend Analysis Methods

#### 7.3.1 Moving Average Trends

| Method | Window | Use Case | Sensitivity |
|--------|--------|----------|-------------|
| **Simple Moving Average (SMA)** | 30/60/90 days | Smooth short-term noise | Low |
| **Exponential Moving Average (EMA)** | 30/60/90 days | Weight recent data more | Medium |
| **Weighted Moving Average (WMA)** | 30/60/90 days | Linear weight decay | Medium |
| **Holt-Winters** | 90/180/365 days | Seasonal patterns | High |

#### 7.3.2 Trend Detection Algorithms

| Algorithm | Purpose | Output |
|-----------|---------|--------|
| **Mann-Kendall Test** | Detect monotonic trend | Trend direction + significance (p-value) |
| **Change Point Detection** | Identify when risk shifted | Change point date + magnitude |
| **CUSUM** | Detect small sustained shifts | Alert when cumulative deviation exceeds threshold |
| **Bayesian Online Changepoint** | Real-time change detection | Probability of change at each time step |
| **STL Decomposition** | Separate trend/seasonal/residual | Trend component + confidence interval |

#### 7.3.3 Anomaly Detection

| Method | Type | Use Case |
|--------|------|----------|
| **Z-Score** | Statistical | Single-point anomalies |
| **Isolation Forest** | ML-based | Multivariate anomalies |
| **LOF (Local Outlier Factor)** | Density-based | Contextual anomalies |
| **Prophet** | Time series | Seasonal anomalies |
| **LSTM Autoencoder** | Deep learning | Complex pattern anomalies |

### 7.4 Trend Analysis Report

```json
{
  "trend_report_id": "TREND-2026-Q4-001",
  "period": {"start": "2026-07-01", "end": "2026-10-01"},
  "portfolio_trends": {
    "overall_mdrs": {
      "current": 2.87,
      "previous": 2.95,
      "change": -0.08,
      "trend_direction": "improving",
      "trend_significance": 0.03,
      "mann_kendall_tau": -0.42,
      "p_value": 0.001,
      "forecast_30d": 2.82,
      "forecast_90d": 2.75,
      "confidence_interval_95": [2.68, 2.82]
    },
    "by_domain": {
      "SEC": {"current": 3.42, "trend": "worsening", "change": +0.15, "anomaly": true},
      "DAT": {"current": 3.18, "trend": "improving", "change": -0.12, "anomaly": false},
      "MOD": {"current": 2.75, "trend": "stable", "change": +0.02, "anomaly": false}
    }
  },
  "detected_anomalies": [
    {
      "date": "2026-09-15",
      "risk_id": "RISK-2026-0002",
      "category": "SEC-02",
      "type": "spike",
      "severity": "high",
      "description": "Agent goal hijacking risk increased from 3.2 to 4.1 in 48 hours",
      "root_cause": "New prompt injection vector identified in red team exercise",
      "recommended_action": "Activate SEC-02 mitigation playbook"
    }
  ],
  "change_points": [
    {
      "date": "2026-08-20",
      "description": "Overall risk score shifted from improving to stable",
      "magnitude": 0.15,
      "likely_cause": "New vendor onboarding increased TPR exposure"
    }
  ],
  "correlation_shifts": [
    {
      "pair": ["SEC-01", "SEC-02"],
      "previous_correlation": 0.65,
      "current_correlation": 0.78,
      "change": +0.13,
      "significance": 0.02,
      "interpretation": "Prompt injection and goal hijacking are becoming more correlated"
    }
  ],
  "risk_forecast": {
    "horizon": "90 days",
    "expected_mdrs": 2.75,
    "var_95": 3.45,
    "probability_of_improvement": 0.68,
    "probability_of_deterioration": 0.22,
    "key_assumptions": [
      "No new critical vulnerabilities discovered",
      "Planned SEC controls implemented on schedule",
      "No major vendor incidents"
    ]
  }
}
```

### 7.5 Automated Alert Generation

Alerts are generated automatically based on trend analysis:

| Alert Type | Trigger Condition | Severity | Recipients | Response |
|------------|-------------------|----------|------------|----------|
| **Trend Reversal** | Risk trend changes direction (improving → worsening) | Medium | Risk Owner | Investigate cause |
| **Anomaly Detected** | Statistical anomaly in risk score | High | Risk Owner + AI Risk Officer | Immediate investigation |
| **Forecast Breach** | Forecasted risk exceeds appetite threshold | High | Risk Committee | Pre-emptive treatment |
| **Correlation Shift** | Risk correlation changes significantly | Medium | AI Risk Officer | Update simulation parameters |
| **Stagnation** | Risk score unchanged for >90 days | Low | Risk Owner | Verify risk is still relevant |
| **Acceleration** | Risk score increasing at increasing rate | High | Risk Owner + CISO | Emergency treatment |

### 7.6 Report Automation Configuration

```yaml
report_automation:
  schedules:
    daily:
      time: "06:00 UTC"
      reports: ["trend_analysis", "anomaly_detection", "kri_monitoring"]
      recipients: ["ai-risk-officer@org.com"]
    
    weekly:
      day: "Monday"
      time: "08:00 UTC"
      reports: ["risk_register_summary", "treatment_progress"]
      recipients: ["risk-owners@org.com", "department-heads@org.com"]
    
    monthly:
      day: 1
      time: "09:00 UTC"
      reports: ["executive_risk_report", "monte_carlo_simulation", "treatment_optimization"]
      recipients: ["c-suite@org.com", "risk-committee@org.com"]
    
    quarterly:
      day: 1
      month: [1, 4, 7, 10]
      time: "10:00 UTC"
      reports: ["board_risk_report", "risk_appetite_review", "framework_review"]
      recipients: ["board@org.com", "risk-committee@org.com"]
  
  delivery:
    channels: ["email", "dashboard", "slack", "pdf_archive"]
    formats: ["pdf", "json", "csv", "html"]
    retention: "7_years"
  
  quality_checks:
    - "All reports include data lineage and methodology references"
    - "All forecasts include confidence intervals"
    - "All anomalies include root cause analysis"
    - "All trend changes include statistical significance"
```

---

## 8. Integration with Existing Framework

### 8.1 Extended Risk Register Schema

The GRC-RISK-001 risk register schema (§5.3) is extended with quantitative fields:

```json
{
  "risk_id": "RISK-2026-0001",
  "risk_title": "Customer service agent may produce biased responses",
  
  "inherent_score": {
    "likelihood": 4, "impact": 4, "detectability": 3,
    "velocity": 3, "persistence": 4, "mdrs": 3.65, "tier": "High"
  },
  
  "quantitative_profile": {
    "dimension_distributions": {
      "likelihood": {"type": "beta", "alpha": 4, "beta": 2},
      "impact": {"type": "triangular", "a": 3, "b": 4, "c": 5},
      "detectability": {"type": "beta", "alpha": 3, "beta": 3},
      "velocity": {"type": "triangular", "a": 2, "b": 3, "c": 4},
      "persistence": {"type": "beta", "alpha": 4, "beta": 2}
    },
    "simulation_parameters": {
      "n_simulations": 10000,
      "confidence_level": 0.95
    },
    "cascade_profile": {
      "upstream_risks": ["RISK-2026-0003"],
      "downstream_risks": ["RISK-2026-0012"],
      "propagation_probability_out": 0.45,
      "propagation_probability_in": 0.30,
      "max_cascade_depth": 2,
      "cascade_amplification_factor": 1.25
    },
    "treatment_optimization": {
      "optimal_strategy": "Mitigate",
      "treatment_cost": 75000,
      "expected_residual_mdrs": 2.45,
      "cost_effectiveness": 0.000016,
      "roi": 2.1
    },
    "trend_profile": {
      "current_trend": "improving",
      "trend_significance": 0.03,
      "forecast_30d": 3.45,
      "forecast_90d": 3.20,
      "last_anomaly": null
    }
  }
}
```

### 8.2 Extended Monitoring Framework

GRC-RISK-001 §8 monitoring layers are extended:

| Layer | GRC-RISK-001 | GRC-RISK-002 Extension |
|-------|-------------|----------------------|
| **L1: Signal Collection** | Raw metrics, logs, events | + Simulation inputs, correlation data |
| **L2: Risk Scoring** | MDRS recalculation | + Monte Carlo simulation, cascade propagation |
| **L3: Threshold Alerting** | KPI breach detection | + Trend anomaly detection, forecast alerts |
| **L4: Trend Analysis** | Pattern and anomaly detection | + Statistical trend detection, correlation shift detection, automated forecasting |

### 8.3 Extended Escalation Matrix

GRC-RISK-001 §8.5 escalation is extended with quantitative triggers:

| Severity | GRC-RISK-001 Trigger | GRC-RISK-002 Additional Trigger |
|----------|---------------------|-------------------------------|
| P1 – Critical | Risk materializes with catastrophic impact | VaR_99 exceeds appetite by >20% |
| P2 – High | Risk tier escalates to High | Forecast shows breach within 30 days |
| P3 – Medium | Risk tier escalates to Medium | Anomaly detected with high severity |
| P4 – Low | Risk tier increases within Low | Trend reversal detected |

### 8.4 Extended Compliance Mapping

| Framework | GRC-RISK-001 Mapping | GRC-RISK-002 Extension |
|-----------|---------------------|----------------------|
| **NIST AI RMF** | GOVERN-MAP-MEASURE-MANAGE | + MEASURE 3.2 (risk tracking over time) via trend analysis |
| **ISO 42001** | Risk management per clause 8.2 | + 8.2 (quantitative risk evaluation) via Monte Carlo |
| **EU AI Act** | Art. 9 RMS | + Art. 9(2)(c) (evaluate risks from monitoring) via cascade propagation |

---

## 9. Appendices

### Appendix A: Monte Carlo Simulation Pseudocode (Python)

```python
import numpy as np
from scipy import stats

def simulate_portfolio_risk(risks, correlation_matrix, n_simulations=10000, 
                             confidence_level=0.95, random_seed=42):
    """
    Monte Carlo simulation of portfolio risk.
    
    Args:
        risks: List of dicts with keys: risk_id, likelihood, impact, 
               detectability, velocity, persistence, weight
        correlation_matrix: N×N numpy array
        n_simulations: Number of Monte Carlo iterations
        confidence_level: VaR confidence level
        random_seed: Reproducibility seed
    
    Returns:
        dict with simulation results
    """
    np.random.seed(random_seed)
    n_risks = len(risks)
    
    # Generate correlated normal variates
    L = np.linalg.cholesky(correlation_matrix)
    Z = np.random.standard_normal((n_simulations, n_risks))
    correlated_normals = Z @ L.T
    
    # Transform to uniform via CDF
    uniform_samples = stats.norm.cdf(correlated_normals)
    
    # Transform to dimension distributions
    mdrs_samples = np.zeros((n_simulations, n_risks))
    
    for i, risk in enumerate(risks):
        # Likelihood: Beta distribution
        L_samples = stats.beta.ppf(
            uniform_samples[:, i], 
            a=risk['likelihood'], 
            b=6 - risk['likelihood']
        )
        
        # Impact: Triangular distribution
        I_samples = stats.triang.ppf(
            uniform_samples[:, i],
            c=(risk['impact'] - 1) / 4,  # normalized to [0,1]
            loc=max(1, risk['impact'] - 1),
            scale=min(5, risk['impact'] + 1) - max(1, risk['impact'] - 1)
        )
        
        # Detectability: Beta distribution
        D_samples = stats.beta.ppf(
            uniform_samples[:, i],
            a=risk['detectability'],
            b=6 - risk['detectability']
        )
        
        # Velocity: Triangular distribution
        V_samples = stats.triang.ppf(
            uniform_samples[:, i],
            c=(risk['velocity'] - 1) / 4,
            loc=max(1, risk['velocity'] - 1),
            scale=min(5, risk['velocity'] + 1) - max(1, risk['velocity'] - 1)
        )
        
        # Persistence: Beta distribution
        P_samples = stats.beta.ppf(
            uniform_samples[:, i],
            a=risk['persistence'],
            b=6 - risk['persistence']
        )
        
        # Compute MDRS
        mdrs_samples[:, i] = (
            L_samples * 0.25 +
            I_samples * 0.30 +
            D_samples * 0.15 +
            V_samples * 0.15 +
            P_samples * 0.15
        )
    
    # Compute weighted portfolio MDRS
    weights = np.array([r['weight'] for r in risks])
    portfolio_mdrs = np.average(mdrs_samples, axis=1, weights=weights)
    
    # Compute statistics
    var_threshold = np.percentile(portfolio_mdrs, confidence_level * 100)
    tail_outcomes = portfolio_mdrs[portfolio_mdrs > var_threshold]
    
    results = {
        'mean': float(np.mean(portfolio_mdrs)),
        'median': float(np.median(portfolio_mdrs)),
        'std': float(np.std(portfolio_mdrs)),
        f'var_{int(confidence_level*100)}': float(var_threshold),
        f'expected_shortfall_{int(confidence_level*100)}': float(np.mean(tail_outcomes)),
        'distribution': portfolio_mdrs.tolist()
    }
    
    return results
```

### Appendix B: Correlation Matrix Construction Pseudocode

```python
import numpy as np
from scipy.optimize import minimize

def construct_correlation_matrix(risks, domain_pairs, category_pairs, control_pairs,
                                 weights=(0.4, 0.4, 0.2)):
    """
    Construct validated correlation matrix from three sources.
    
    Args:
        risks: List of risk dicts with 'risk_id', 'risk_domain', 'risk_category'
        domain_pairs: Dict of (domain_a, domain_b) -> correlation
        category_pairs: Dict of (category_a, category_b) -> correlation
        control_pairs: Dict of control_name -> list of categories
        weights: (causal, trigger, control) weights
    
    Returns:
        N×N validated correlation matrix
    """
    n = len(risks)
    R_causal = np.eye(n)
    R_trigger = np.eye(n)
    R_control = np.eye(n)
    
    # Build domain-level correlation
    for i in range(n):
        for j in range(i+1, n):
            domain_pair = (risks[i]['risk_domain'], risks[j]['risk_domain'])
            if domain_pair in domain_pairs:
                R_causal[i, j] = R_causal[j, i] = domain_pairs[domain_pair]
    
    # Build category-level correlation
    for i in range(n):
        for j in range(i+1, n):
            cat_pair = (risks[i]['risk_category'], risks[j]['risk_category'])
            if cat_pair in category_pairs:
                R_trigger[i, j] = R_trigger[j, i] = category_pairs[cat_pair]
    
    # Build control-level correlation
    for control, categories in control_pairs.items():
        for i in range(n):
            for j in range(i+1, n):
                if (risks[i]['risk_category'] in categories and 
                    risks[j]['risk_category'] in categories):
                    R_control[i, j] = R_control[j, i] = 0.30
    
    # Weighted combination
    R = (weights[0] * R_causal + 
         weights[1] * R_trigger + 
         weights[2] * R_control)
    
    # Ensure diagonal is 1.0
    np.fill_diagonal(R, 1.0)
    
    # Validate positive semi-definiteness
    eigenvalues = np.linalg.eigvalsh(R)
    if np.min(eigenvalues) < 0:
        R = nearest_correlation_matrix(R)
    
    return R

def nearest_correlation_matrix(A, max_iterations=100):
    """Find nearest positive semi-definite correlation matrix."""
    n = A.shape[0]
    Y = A.copy()
    X = np.zeros_like(A)
    
    for _ in range(max_iterations):
        R = Y - X
        # Projection onto PSD matrices
        eigvals, eigvecs = np.linalg.eigh(R)
        eigvals = np.maximum(eigvals, 0)
        Y = eigvecs @ np.diag(eigvals) @ eigvecs.T
        # Projection onto unit diagonal
        X = Y - R
        np.fill_diagonal(Y, 1.0)
        
        if np.max(np.abs(np.diag(Y) - 1.0)) < 1e-6:
            break
    
    return Y
```

### Appendix C: Cascading Propagation Pseudocode

```python
import networkx as nx
import random

def propagate_cascade(graph, initial_active, max_iterations=10, 
                      convergence_threshold=0.01, random_seed=42):
    """
    Propagate risk cascade through directed graph.
    
    Args:
        graph: NetworkX DiGraph with edge attributes:
               'weight' (amplification), 'probability', 'delay'
        initial_active: Set of initially materialized node IDs
        max_iterations: Maximum propagation rounds
        convergence_threshold: Stop when score change < threshold
        random_seed: Reproducibility seed
    
    Returns:
        dict with final scores, propagation path, cascade metrics
    """
    random.seed(random_seed)
    
    effective_scores = {node: graph.nodes[node]['base_mdrs'] 
                        for node in graph.nodes()}
    active = set(initial_active)
    propagation_path = []
    iteration = 0
    changed = True
    
    while changed and iteration < max_iterations:
        changed = False
        iteration += 1
        new_active = set()
        
        for risk in active:
            for _, target, edge_data in graph.out_edges(risk, data=True):
                # Propagation probability
                prop_prob = edge_data['probability'] * (effective_scores[risk] / 5.0)
                
                if random.random() < prop_prob:
                    # Amplification
                    amplification = edge_data['weight'] * (
                        effective_scores[risk] / graph.nodes[risk]['base_mdrs']
                    )
                    # Time delay
                    delay = edge_data['delay'] * (1 + np.log(effective_scores[risk]))
                    # New score
                    new_score = effective_scores[target] * (1 + 0.1 * amplification)
                    new_score = min(new_score, 5.0)
                    
                    if new_score - effective_scores[target] > convergence_threshold:
                        effective_scores[target] = new_score
                        changed = True
                        new_active.add(target)
                    
                    propagation_path.append({
                        'from': risk,
                        'to': target,
                        'amplification': amplification,
                        'delay_hours': delay,
                        'new_score': new_score,
                        'iteration': iteration
                    })
        
        active = new_active
    
    # Compute cascade metrics
    total_affected = sum(
        1 for node in graph.nodes() 
        if effective_scores[node] > graph.nodes[node]['base_mdrs']
    )
    
    return {
        'effective_scores': effective_scores,
        'propagation_path': propagation_path,
        'cascade_depth': iteration,
        'total_affected': total_affected,
        'cascade_severity': sum(
            effective_scores[node] - graph.nodes[node]['base_mdrs']
            for node in graph.nodes()
        )
    }
```

### Appendix D: Treatment Optimization Pseudocode

```python
from itertools import combinations

def optimize_treatment_portfolio(risks, budget, constraints=None):
    """
    Optimize treatment portfolio using greedy selection + local search.
    
    Args:
        risks: List of risk dicts with keys: risk_id, inherent_mdrs,
               treatment_options (list of dicts with strategy, cost, reduction)
        budget: Total available budget
        constraints: Dict with 'regulatory_minimums', 'dependencies'
    
    Returns:
        dict with optimal portfolio and metrics
    """
    # Generate all (risk, option) pairs with cost-effectiveness
    options = []
    for risk in risks:
        for opt in risk['treatment_options']:
            ce = opt['reduction'] / opt['cost'] if opt['cost'] > 0 else float('inf')
            options.append({
                'risk_id': risk['risk_id'],
                'strategy': opt['strategy'],
                'cost': opt['cost'],
                'reduction': opt['reduction'],
                'cost_effectiveness': ce
            })
    
    # Sort by cost-effectiveness descending
    options.sort(key=lambda x: x['cost_effectiveness'], reverse=True)
    
    # Greedy selection
    selected = []
    remaining_budget = budget
    treated_risks = set()
    
    for opt in options:
        if opt['risk_id'] in treated_risks:
            continue
        if opt['cost'] <= remaining_budget:
            selected.append(opt)
            remaining_budget -= opt['cost']
            treated_risks.add(opt['risk_id'])
    
    # Local search improvement
    improved = True
    while improved:
        improved = False
        for i, sel in enumerate(selected):
            # Try upgrading to a higher-cost option
            for opt in options:
                if (opt['risk_id'] == sel['risk_id'] and 
                    opt['cost'] > sel['cost'] and
                    opt['cost'] - sel['cost'] <= remaining_budget and
                    opt['reduction'] > sel['reduction']):
                    remaining_budget += sel['cost'] - opt['cost']
                    selected[i] = opt
                    improved = True
                    break
    
    total_cost = sum(s['cost'] for s in selected)
    total_reduction = sum(s['reduction'] for s in selected)
    
    return {
        'optimal_portfolio': selected,
        'total_cost': total_cost,
        'budget_utilization': total_cost / budget,
        'risk_reduction_achieved': total_reduction,
        'cost_effectiveness': total_reduction / total_cost if total_cost > 0 else 0
    }
```

### Appendix E: Glossary (Extended)

| Term | Definition |
|------|-----------|
| **Monte Carlo Simulation** | Computational algorithm that uses repeated random sampling to obtain numerical results for risk distributions |
| **Value-at-Risk (VaR)** | Maximum loss not exceeded with a given confidence level over a specific period |
| **Expected Shortfall (ES)** | Average loss exceeding VaR — measures tail risk beyond the VaR threshold |
| **Copula** | Statistical function that couples multivariate distribution functions to their one-dimensional marginal distributions |
| **Correlation Matrix** | Square matrix showing correlation coefficients between pairs of risks |
| **Positive Semi-Definite** | Matrix property ensuring all eigenvalues are non-negative — required for valid correlation matrices |
| **Cascading Risk** | Risk that propagates from one system/component to another through trigger relationships |
| **Propagation Probability** | Probability that a materialized upstream risk triggers a downstream risk |
| **Amplification Factor** | Multiplier representing how much a cascade increases downstream risk severity |
| **Risk Budget** | Allocation of aggregate risk appetite to individual domains or risk categories |
| **Risk Appetite Utilization** | Ratio of current risk exposure to allocated risk budget |
| **Treatment Optimization** | Process of selecting the optimal set of treatment actions to maximize risk reduction per unit cost |
| **Cost-Effectiveness Ratio** | Risk reduction achieved per dollar spent on treatment |
| **Trend Analysis** | Statistical analysis of risk data over time to detect patterns, shifts, and anomalies |
| **Change Point Detection** | Statistical method for identifying points in time where the probability distribution of a time series changes |
| **Mann-Kendall Test** | Non-parametric statistical test for detecting monotonic trends in time series data |
| **Anomaly Detection** | Identification of rare items, events, or observations that deviate significantly from the majority of the data |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial framework (GRC-RISK-001) |
| 2.0 | 2026-10-01 | GRC_Claw Architecture Team | Quantitative deepening: Monte Carlo, correlation, cascading, appetite, optimization, reporting |

---

*This framework is a living document. It shall be reviewed and updated:*
- *After any significant AI incident*
- *When new AI regulations take effect*
- *When new AI use cases are introduced*
- *At minimum, annually*

---

*End of Framework*
