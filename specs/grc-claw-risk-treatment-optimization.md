# GRC_Claw Risk Treatment Optimization Framework

**Document ID:** GRC-RISK-002  
**Version:** 1.0  
**Date:** 2026-10-01  
**Owner:** GRC_Claw Architecture Team  
**Status:** Draft for Review  
**Supersedes:** N/A  
**References:** GRC-RISK-001 (Risk Assessment Framework), GRC-METRICS-001 (Unified Metrics Layer)

---

## Table of Contents

1. [Purpose & Scope](#1-purpose--scope)
2. [Risk Treatment Selection Algorithm](#2-risk-treatment-selection-algorithm)
3. [Risk Treatment Cost-Benefit Analysis](#3-risk-treatment-cost-benefit-analysis)
4. [Risk Treatment Effectiveness Measurement](#4-risk-treatment-effectiveness-measurement)
5. [Risk Appetite Framework](#5-risk-appetite-framework)
6. [Risk-Based Decision Making](#6-risk-based-decision-making)
7. [Risk Reporting & Escalation](#7-risk-reporting--escalation)
8. [Appendices](#8-appendices)

---

## 1. Purpose & Scope

### 1.1 Purpose

This document expands the GRC_Claw Risk Assessment Framework (GRC-RISK-001) with detailed risk treatment optimization methodology. It provides:

- A **deterministic selection algorithm** for choosing among Avoid, Transfer, Mitigate, and Accept strategies
- A **quantitative cost-benefit analysis** model for comparing treatment options
- An **effectiveness measurement** framework for continuous control improvement
- A **tiered risk appetite** framework with quantitative thresholds
- A **risk-based decision making** model for AI system deployment and operations
- An **integrated reporting and escalation** system aligned with the Unified Metrics Layer

### 1.2 Scope

| In Scope | Out of Scope |
|----------|-------------|
| Treatment strategy selection for all 40 risk categories | Insurance product design |
| Cost-benefit analysis of mitigation controls | Financial risk modeling |
| Control effectiveness measurement and feedback | Non-AI enterprise risk |
| Risk appetite definition and monitoring | Physical security controls |
| Risk-based deployment and operational decisions | |
| Risk reporting and escalation workflows | |

### 1.3 Design Principles

1. **Deterministic** — Treatment selection uses rule-based algorithms, not subjective judgment
2. **Quantified** — Every treatment decision has a numeric cost-benefit score
3. **Continuous** — Effectiveness is measured continuously, not point-in-time
4. **Aligned** — Risk appetite, treatment, and reporting are tightly coupled
5. **Auditable** — Every decision is traceable to inputs, rules, and evidence

---

## 2. Risk Treatment Selection Algorithm

### 2.1 Algorithm Overview

The Risk Treatment Selection Algorithm (RTSA) is a deterministic, multi-criteria decision model that selects the optimal treatment strategy for each risk based on MDRS score, risk domain, treatment cost, and organizational constraints.

```
┌─────────────────────────────────────────────────────────────────────┐
│              RISK TREATMENT SELECTION ALGORITHM (RTSA)               │
│                                                                       │
│  INPUTS:                                                              │
│  • MDRS score (1.00–5.00)                                            │
│  • Risk domain (GOV, DAT, MOD, SEC, HUM, OPS, TPR, CMP)            │
│  • Risk category (40 categories)                                     │
│  • Inherent risk dimensions (L, I, D, V, P)                         │
│  • Available treatment options with costs                            │
│  • Organizational risk appetite                                      │
│  • Regulatory constraints (EU AI Act, etc.)                          │
│                                                                       │
│  OUTPUTS:                                                             │
│  • Selected strategy (AVOID/TRANSFER/MITIGATE/ACCEPT)               │
│  • Confidence score (0–100%)                                         │
│  • Rationale (rule trace)                                            │
│  • Alternative strategies (ranked)                                   │
│  • Cost-benefit score                                                │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Decision Tree

The RTSA uses a hierarchical decision tree with four levels:

```
LEVEL 1: REGULATORY GATE
├── Is risk prohibited by regulation? (CMP-01)
│   ├── YES → AVOID (mandatory)
│   └── NO → Continue to Level 2
│
LEVEL 2: RISK TIER GATE
├── Is MDRS ≥ 4.50 (Critical)?
│   ├── YES → AVOID or MITIGATE (Risk Committee decision)
│   └── NO → Continue to Level 3
│
LEVEL 3: COST-BENEFIT GATE
├── Is mitigation cost < risk exposure × 0.3?
│   ├── YES → MITIGATE
│   └── NO → Continue to Level 4
│
LEVEL 4: TRANSFER FEASIBILITY GATE
├── Is risk transferable (insurable/contractible)?
│   ├── YES → TRANSFER (if cost-effective)
│   └── NO → ACCEPT (with documented approval)
```

### 2.3 Selection Rules (Deterministic)

#### Rule Set A: Regulatory Constraints (Highest Priority)

| Rule ID | Condition | Strategy | Authority | Rationale |
|---------|-----------|----------|-----------|-----------|
| A-01 | Risk category = CMP-01 (Prohibited Practice) | AVOID | Risk Committee | EU AI Act Art. 5 prohibition |
| A-02 | Risk category = CMP-02 AND MDRS ≥ 3.50 | MITIGATE | CISO/CTO | Misclassified high-risk system |
| A-03 | Risk category = CMP-03 AND MDRS ≥ 4.00 | MITIGATE | Compliance Officer | Conformity gap on high-risk system |
| A-04 | Risk category = CMP-04 AND cross-border conflict | MITIGATE | Compliance Officer | Legal exposure |

#### Rule Set B: Risk Tier-Based Selection

| Rule ID | MDRS Range | Default Strategy | Alternative | Max Acceptance |
|---------|------------|------------------|-------------|----------------|
| B-01 | 4.50–5.00 (Critical) | AVOID or MITIGATE | TRANSFER | 30 days with mitigation plan |
| B-02 | 3.50–4.49 (High) | MITIGATE | TRANSFER | 90 days |
| B-03 | 2.50–3.49 (Medium) | MITIGATE or ACCEPT | TRANSFER | 180 days |
| B-04 | 1.50–2.49 (Low) | ACCEPT or MITIGATE | — | 12 months |
| B-05 | 1.00–1.49 (Minimal) | ACCEPT | — | 12 months |

#### Rule Set C: Domain-Specific Overrides

| Rule ID | Domain | Condition | Override Strategy | Rationale |
|---------|--------|-----------|-------------------|-----------|
| C-01 | SEC | Any SEC risk with MDRS ≥ 3.50 | MITIGATE (mandatory) | Security risks require active controls |
| C-02 | HUM | Any HUM risk with I ≥ 4 | MITIGATE (mandatory) | High-impact human harm requires mitigation |
| C-03 | DAT | DAT-05 (Data Poisoning) with MDRS ≥ 3.00 | MITIGATE (mandatory) | Adversarial data risks are persistent |
| C-04 | TPR | TPR-01 with MDRS ≥ 4.00 | MITIGATE or TRANSFER | Vendor risk must be actively managed |
| C-05 | OPS | OPS-02 (Incident Response) with MDRS ≥ 3.50 | MITIGATE (mandatory) | Incident readiness is operational necessity |

#### Rule Set D: Cost-Benefit Override

| Rule ID | Condition | Override Strategy | Rationale |
|---------|-----------|-------------------|-----------|
| D-01 | Mitigation cost > Risk exposure × 0.5 | TRANSFER or ACCEPT | Mitigation not cost-effective |
| D-02 | Mitigation cost < Risk exposure × 0.1 | MITIGATE (mandatory) | Mitigation is highly cost-effective |
| D-03 | Transfer cost < Mitigation cost × 0.3 | TRANSFER | Transfer is significantly cheaper |
| D-04 | Residual risk after mitigation > Appetite | Add controls or AVOID | Mitigation insufficient |

### 2.4 Selection Algorithm Pseudocode

```python
def select_treatment_strategy(risk, options, appetite, regulations):
    """
    RTSA: Risk Treatment Selection Algorithm
    Returns: (strategy, confidence, rationale, alternatives)
    """
    
    # Level 1: Regulatory Gate
    if risk.category == "CMP-01":
        return AVOID, 100%, "EU AI Act Art. 5 prohibition", []
    
    if risk.category == "CMP-02" and risk.mdrs >= 3.50:
        return MITIGATE, 95%, "Misclassified high-risk system", [TRANSFER]
    
    # Level 2: Risk Tier Gate
    if risk.mdrs >= 4.50:
        # Critical: Avoid or Mitigate
        if risk.domain in ["SEC", "HUM"] and risk.impact >= 4:
            return AVOID, 90%, "Critical security/human risk", [MITIGATE]
        else:
            return MITIGATE, 85%, "Critical risk requires active mitigation", [AVOID, TRANSFER]
    
    # Level 3: Cost-Benefit Gate
    best_option = max(options, key=lambda o: o.cost_benefit_ratio)
    
    if best_option.cost_benefit_ratio > 3.0:
        # Highly cost-effective
        return MITIGATE, 80%, f"Mitigation highly cost-effective (CBR={best_option.cost_benefit_ratio})", 
               [TRANSFER, ACCEPT]
    
    # Level 4: Transfer Feasibility
    if risk.transferable and risk.domain in ["TPR", "OPS"]:
        transfer_cost = estimate_transfer_cost(risk)
        mitigation_cost = estimate_mitigation_cost(risk)
        if transfer_cost < mitigation_cost * 0.3:
            return TRANSFER, 75%, f"Transfer cost-effective ({transfer_cost} vs {mitigation_cost})", 
                   [MITIGATE, ACCEPT]
    
    # Default: Accept if within appetite
    if risk.mdrs <= appetite.threshold_for(risk.domain):
        return ACCEPT, 70%, f"Risk within appetite ({risk.mdrs} <= {appetite.threshold})", 
               [MITIGATE]
    
    # Fallback: Mitigate
    return MITIGATE, 65%, "Default: risk exceeds appetite, mitigation required", 
           [TRANSFER, ACCEPT]
```

### 2.5 Treatment Strategy Definitions

| Strategy | Definition | When Applied | Exit Criteria |
|----------|------------|--------------|---------------|
| **AVOID** | Do not deploy or use the AI system | Risk is prohibited or unacceptable | Risk eliminated or system decommissioned |
| **TRANSFER** | Shift risk to third party via insurance, contracts, or indemnification | Risk is insurable/contractible and transfer is cost-effective | Transfer agreement in place and verified |
| **MITIGATE** | Implement controls to reduce likelihood or impact | Risk exceeds appetite and mitigation is cost-effective | Residual risk within appetite |
| **ACCEPT** | Acknowledge residual risk with documented approval | Risk is within appetite or treatment is not cost-effective | Risk remains within appetite at review |

### 2.6 Multi-Strategy Treatment

Some risks require a combination of strategies. The RTSA supports multi-strategy treatment:

| Combination | Example | Application |
|-------------|---------|-------------|
| MITIGATE + TRANSFER | Implement security controls + cyber insurance | High-impact security risks |
| MITIGATE + ACCEPT | Implement controls + accept residual risk | Medium risks where full mitigation is impractical |
| TRANSFER + ACCEPT | Insurance + accept deductible | Low-frequency, high-impact risks |
| AVOID + TRANSFER | Decommission system + transfer data risks | Prohibited systems with legacy data |

---

## 3. Risk Treatment Cost-Benefit Analysis

### 3.1 Cost-Benefit Model

The Risk Treatment Cost-Benefit Analysis (RTCBA) quantifies the value of risk treatment by comparing the cost of treatment against the expected loss reduction.

```
┌─────────────────────────────────────────────────────────────────────┐
│              COST-BENEFIT ANALYSIS MODEL                             │
│                                                                       │
│  RISK EXPOSURE (RE)                                                  │
│  RE = Likelihood × Impact × Asset Value                              │
│                                                                       │
│  TREATMENT COST (TC)                                                 │
│  TC = Implementation Cost + Operating Cost × Time Horizon            │
│                                                                       │
│  RISK REDUCTION (RR)                                                 │
│  RR = RE × Control Effectiveness                                     │
│                                                                       │
│  NET BENEFIT (NB)                                                    │
│  NB = RR − TC                                                        │
│                                                                       │
│  COST-BENEFIT RATIO (CBR)                                            │
│  CBR = RR / TC                                                       │
│                                                                       │
│  RETURN ON RISK INVESTMENT (RORI)                                    │
│  RORI = (RR − TC) / TC × 100                                         │
│                                                                       │
│  PAYBACK PERIOD (PP)                                                 │
│  PP = TC / (RR / Time Horizon)                                       │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Risk Exposure Calculation

#### 3.2.1 Annualized Loss Expectancy (ALE)

```
ALE = SLE × ARO

Where:
  SLE = Single Loss Expectancy = Asset Value × Exposure Factor
  ARO = Annual Rate of Occurrence = Likelihood / 5 (normalized to 0.2–1.0)
```

#### 3.2.2 Risk Exposure by Domain

| Domain | Asset Value Factor | Exposure Factor | Typical ALE Range |
|--------|-------------------|-----------------|-------------------|
| GOV | $500K–$2M | 0.1–0.3 | $10K–$600K |
| DAT | $1M–$10M | 0.2–0.5 | $40K–$5M |
| MOD | $500K–$5M | 0.1–0.4 | $10K–$2M |
| SEC | $2M–$20M | 0.3–0.6 | $120K–$12M |
| HUM | $5M–$50M | 0.2–0.5 | $200K–$25M |
| OPS | $1M–$10M | 0.1–0.3 | $20K–$3M |
| TPR | $2M–$15M | 0.2–0.4 | $80K–$6M |
| CMP | $5M–$50M | 0.3–0.6 | $300K–$30M |

### 3.3 Treatment Cost Model

#### 3.3.1 Cost Components

| Cost Category | Description | Calculation |
|---------------|-------------|-------------|
| **Implementation Cost (IC)** | One-time cost to design and deploy controls | Labor + Tools + Infrastructure |
| **Operating Cost (OC)** | Recurring cost to maintain controls | Labor + Licensing + Maintenance |
| **Opportunity Cost (OpC)** | Cost of foregone opportunities due to controls | Delayed deployment + Reduced functionality |
| **Compliance Cost (CC)** | Cost of regulatory compliance activities | Assessment + Documentation + Audit |

#### 3.3.2 Total Cost of Ownership (TCO)

```
TCO = IC + (OC × Time Horizon) + OpC + CC

Where Time Horizon = 3 years (default)
```

#### 3.3.3 Cost Estimation by Control Type

| Control Type | Implementation Cost | Annual Operating Cost | Time to Implement |
|--------------|-------------------|----------------------|-------------------|
| Policy/Process | $10K–$50K | $5K–$20K | 2–8 weeks |
| Technical Control | $50K–$500K | $20K–$100K | 4–16 weeks |
| Organizational | $20K–$100K | $10K–$50K | 4–12 weeks |
| Third-Party Service | $30K–$200K | $30K–$150K | 2–8 weeks |
| Training Program | $10K–$80K | $10K–$40K | 4–12 weeks |

### 3.4 Cost-Benefit Decision Matrix

| CBR Range | Decision | Action |
|-----------|----------|--------|
| CBR > 5.0 | Strongly favorable | Implement immediately |
| CBR 3.0–5.0 | Favorable | Implement in current quarter |
| CBR 1.5–3.0 | Marginally favorable | Implement if resources available |
| CBR 1.0–1.5 | Break-even | Consider alternatives |
| CBR 0.5–1.0 | Unfavorable | Do not implement; consider transfer or accept |
| CBR < 0.5 | Strongly unfavorable | Do not implement; avoid if possible |

### 3.5 Cost-Benefit Analysis Example

**Risk:** SEC-02 Agent Goal Hijacking, MDRS 4.2 (High)

| Parameter | Value | Calculation |
|-----------|-------|-------------|
| Asset Value | $10M | Customer-facing agent system |
| Likelihood | 4/5 = 0.8 | Likely |
| Impact | 4/5 = 0.8 | Major |
| Exposure Factor | 0.4 | 40% of asset value at risk |
| SLE | $4M | $10M × 0.4 |
| ARO | 0.16 | 0.8 × 0.2 (adjusted for controls) |
| ALE (Inherent) | $640K | $4M × 0.16 |
| ALE (Residual) | $128K | With 80% effective controls |
| Risk Reduction (RR) | $512K/year | $640K − $128K |
| Implementation Cost | $200K | Goal integrity monitoring system |
| Annual Operating Cost | $80K | Maintenance + staffing |
| 3-Year TCO | $440K | $200K + ($80K × 3) |
| 3-Year RR | $1.536M | $512K × 3 |
| CBR | 3.49 | $1.536M / $440K |
| RORI | 249% | ($1.536M − $440K) / $440K × 100 |
| Payback Period | 10.2 months | $440K / ($512K / 12) |

**Decision:** CBR = 3.49 (Favorable) → Implement in current quarter

### 3.6 Portfolio-Level Cost-Benefit Optimization

When resources are constrained, treatments are prioritized using a portfolio optimization model:

```
Maximize: Σ (RR_i × x_i) for all risks i
Subject to:
  Σ (TC_i × x_i) ≤ Budget
  x_i ∈ {0, 1} for each risk i
  x_i = 1 for all regulatory-mandated risks
  x_i = 1 for all Critical tier risks
```

Where:
- RR_i = Risk reduction for risk i
- TC_i = Treatment cost for risk i
- x_i = Binary decision variable (1 = treat, 0 = don't treat)

**Prioritization Score:**

```
Priority Score = (MDRS × Domain Weight × Regulatory Factor) / TCO

Where:
  Domain Weight = SEC: 1.5, HUM: 1.4, DAT: 1.3, MOD: 1.2, OPS: 1.1, TPR: 1.0, CMP: 1.3, GOV: 0.9
  Regulatory Factor = 2.0 if EU AI Act applies, 1.5 if other regulation applies, 1.0 otherwise
```

---

## 4. Risk Treatment Effectiveness Measurement

### 4.1 Effectiveness Measurement Framework

```
┌─────────────────────────────────────────────────────────────────────┐
│         RISK TREATMENT EFFECTIVENESS MEASUREMENT FRAMEWORK           │
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   DESIGN     │───▶│  IMPLEMENT   │───▶│   MEASURE    │          │
│  │ EFFECTIVENESS│    │  & DEPLOY    │    │  & VERIFY    │          │
│  └──────────────┘    └──────────────┘    └──────┬───────┘          │
│                                                  │                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────▼───────┐          │
│  │   IMPROVE    │◀───│   ANALYZE    │◀───│   REPORT     │          │
│  │  & ADJUST    │    │  & IDENTIFY  │    │  & ESCALATE  │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Effectiveness Metrics

#### 4.2.1 Primary Effectiveness Metrics

| Metric | Formula | Target | Alert Threshold | Data Source |
|--------|---------|--------|-----------------|-------------|
| **Control Effectiveness (CE)** | (Inherent MDRS − Residual MDRS) / Inherent MDRS × 100 | ≥70% | <50% | Risk Register |
| **Risk Reduction Rate (RRR)** | (Inherent ALE − Residual ALE) / Inherent ALE × 100 | ≥60% | <40% | Risk Engine |
| **Control Coverage (CC)** | Controls implemented / Controls planned × 100 | 100% | <90% | Control Registry |
| **Control Reliability (CR)** | Successful control executions / Total control executions × 100 | ≥99% | <95% | Monitoring |
| **Mean Time to Detect (MTTD)** | Average time from risk signal to detection | <1 hour | >4 hours | Monitoring |
| **Mean Time to Respond (MTTR)** | Average time from detection to response | <4 hours | >24 hours | Incident Mgmt |
| **False Positive Rate (FPR)** | False positives / Total alerts × 100 | <5% | >15% | Monitoring |
| **Control Drift** | Change in control effectiveness over time | <5% per quarter | >10% per quarter | Risk Engine |

#### 4.2.2 Secondary Effectiveness Metrics

| Metric | Formula | Target | Data Source |
|--------|---------|--------|-------------|
| **Residual Risk Trend** | Change in residual MDRS over time | Stable or decreasing | Risk Register |
| **Treatment Adherence** | Treatments completed on time / Total treatments × 100 | ≥95% | GRC Platform |
| **Evidence Completeness** | Evidence artifacts complete / Total required × 100 | 100% | Evidence Store |
| **Stakeholder Satisfaction** | Survey score on risk treatment effectiveness | ≥4.0/5 | Survey |
| **Audit Findings** | Number of findings related to risk treatment | 0 | Audit Reports |
| **Recurring Incidents** | Incidents with same root cause / Total incidents × 100 | <10% | Incident Mgmt |

### 4.3 Effectiveness Measurement Methods

#### 4.3.1 Control Testing Methods

| Method | Description | Frequency | Applicability |
|--------|-------------|-----------|---------------|
| **Automated Testing** | Automated scripts test control functionality | Continuous | Technical controls |
| **Penetration Testing** | Simulated attacks test control resilience | Quarterly | Security controls |
| **Red Team Exercise** | Adversarial testing of AI system + controls | Per release + quarterly | Agentic AI controls |
| **Tabletop Exercise** | Scenario-based walkthrough of control response | Semi-annual | Process controls |
| **Audit Review** | Independent review of control design and operation | Annual | All controls |
| **Metrics Analysis** | Statistical analysis of control performance data | Continuous | All controls |
| **Self-Assessment** | Control owner assesses control effectiveness | Quarterly | All controls |

#### 4.3.2 Effectiveness Scoring

Each control receives an effectiveness score (0–100) based on:

```
Effectiveness Score = (Design Score × 0.3) + (Implementation Score × 0.3) + 
                      (Operational Score × 0.2) + (Outcome Score × 0.2)

Where:
  Design Score = How well the control is designed to address the risk
  Implementation Score = How well the control is implemented
  Operational Score = How reliably the control operates
  Outcome Score = How effective the control is at reducing risk
```

| Score Range | Rating | Action |
|-------------|--------|--------|
| 90–100 | Excellent | Maintain; share best practices |
| 75–89 | Good | Minor improvements |
| 60–74 | Adequate | Improvement plan required |
| 40–59 | Poor | Remediation required within 30 days |
| 0–39 | Critical | Immediate remediation; escalate |

### 4.4 Effectiveness Feedback Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│              EFFECTIVENESS FEEDBACK LOOP                              │
│                                                                       │
│  1. MEASURE                                                           │
│     • Collect control performance data                               │
│     • Calculate effectiveness metrics                                │
│     • Compare against targets                                        │
│                                                                       │
│  2. ANALYZE                                                           │
│     • Identify controls below target                                 │
│     • Root cause analysis of failures                                │
│     • Identify emerging risks                                         │
│                                                                       │
│  3. IMPROVE                                                           │
│     • Redesign ineffective controls                                  │
│     • Implement additional controls                                  │
│     • Update treatment plans                                         │
│                                                                       │
│  4. VERIFY                                                            │
│     • Re-test improved controls                                       │
│     • Confirm effectiveness improvement                              │
│     • Update risk register                                           │
│                                                                       │
│  5. REPORT                                                            │
│     • Report effectiveness to stakeholders                            │
│     • Escalate critical failures                                     │
│     • Update risk posture                                            │
│                                                                       │
│  Continuous cycle: Measure → Analyze → Improve → Verify → Report     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.5 Effectiveness Degradation Model

Control effectiveness degrades over time due to:

| Degradation Factor | Description | Typical Degradation Rate | Mitigation |
|-------------------|-------------|--------------------------|------------|
| **Environmental Change** | Changes in threat landscape or business context | 5–10% per year | Regular control review |
| **Technology Obsolescence** | Control technology becomes outdated | 10–20% per year | Technology refresh program |
| **Organizational Change** | Staff turnover, process changes | 5–15% per year | Training and documentation |
| **Control Fatigue** | Staff bypass controls over time | 3–8% per year | Automation and monitoring |
| **Adversarial Adaptation** | Attackers adapt to controls | 10–30% per year | Red team and threat intel |

**Predicted Effectiveness:**

```
Predicted Effectiveness(t) = Initial Effectiveness × (1 − Degradation Rate)^t

Where t = time in years since implementation
```

**Replacement Trigger:** When predicted effectiveness drops below 60%, the control must be redesigned or replaced.

---

## 5. Risk Appetite Framework

### 5.1 Risk Appetite Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│              RISK APPETITE FRAMEWORK                                 │
│                                                                       │
│  LEVEL 1: ENTERPRISE APPETITE                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Overall risk tolerance for the organization                 │    │
│  │  Set by: Board of Directors                                  │    │
│  │  Reviewed: Annually                                           │    │
│  │  Metric: Overall MDRS ≤ 3.0 (Medium)                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  LEVEL 2: DOMAIN APPETITE                                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Risk tolerance per risk domain (8 domains)                  │    │
│  │  Set by: Risk Committee                                       │    │
│  │  Reviewed: Semi-annually                                      │    │
│  │  Metric: Domain MDRS ≤ domain-specific threshold             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  LEVEL 3: CATEGORY APPETITE                                          │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Risk tolerance per risk category (40 categories)            │    │
│  │  Set by: Domain Owners                                        │    │
│  │  Reviewed: Quarterly                                          │    │
│  │  Metric: Category MDRS ≤ category-specific threshold         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  LEVEL 4: SYSTEM APPETITE                                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Risk tolerance per AI system                                 │    │
│  │  Set by: System Owners                                        │    │
│  │  Reviewed: Per release + quarterly                            │    │
│  │  Metric: System MDRS ≤ system-specific threshold             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Risk Appetite Statements

#### 5.2.1 Enterprise Risk Appetite Statement

> GRC_Claw accepts AI-related risk up to a **Medium** level (MDRS ≤ 3.49) with appropriate mitigation. Risks at **High** (MDRS 3.50–4.49) or **Critical** (MDRS ≥ 4.50) levels require executive approval and active treatment plans. The organization will not deploy AI systems that pose **unacceptable risk** to individuals, groups, or society, regardless of business benefit.

#### 5.2.2 Domain Risk Appetite Statements

| Domain | Appetite Statement | Max Acceptable MDRS | Rationale |
|--------|-------------------|---------------------|-----------|
| **GOV** | Low — Strong governance is foundational | 2.49 | Governance failures cascade to all other domains |
| **DAT** | Low-Medium — Data quality is critical | 2.99 | Data issues affect model performance and compliance |
| **MOD** | Medium — Model performance must meet standards | 3.49 | Model failures impact business outcomes |
| **SEC** | Very Low — Security is non-negotiable | 2.49 | Security breaches have catastrophic consequences |
| **HUM** | Very Low — Human harm is unacceptable | 2.49 | Human harm is ethically and legally unacceptable |
| **OPS** | Medium — Operational resilience required | 3.49 | Operational failures impact service delivery |
| **TPR** | Low-Medium — Vendor risk must be managed | 2.99 | Third-party failures can cascade |
| **CMP** | Very Low — Compliance is mandatory | 2.49 | Regulatory violations have legal consequences |

### 5.3 Risk Appetite Thresholds

#### 5.3.1 Quantitative Thresholds

| Appetite Level | MDRS Range | Color | Treatment Requirement | Approval Authority |
|---------------|------------|-------|----------------------|-------------------|
| **Conservative** | ≤1.49 | 🟢 | Accept | System Owner |
| **Cautious** | 1.50–2.49 | 🟢 | Accept or Mitigate | Business Unit Owner |
| **Balanced** | 2.50–3.49 | 🟡 | Mitigate preferred | Department Head |
| **Aggressive** | 3.50–4.49 | 🔴 | Mitigate mandatory | CISO/CTO |
| **Unacceptable** | ≥4.50 | 🔴 | Avoid or Mitigate | Risk Committee |

#### 5.3.2 Qualitative Appetite Dimensions

| Dimension | Conservative | Balanced | Aggressive |
|-----------|-------------|----------|------------|
| **Financial Impact** | ≤$100K per incident | ≤$1M per incident | ≤$10M per incident |
| **Reputational Impact** | No negative press | Limited negative press | Significant negative press acceptable |
| **Regulatory Impact** | Zero tolerance | Minor violations acceptable | Fines up to €1M acceptable |
| **Human Impact** | Zero tolerance | Minor impact reversible | Significant impact with remediation |
| **Operational Impact** | <1 hour downtime | <24 hours downtime | <72 hours downtime |
| **Data Impact** | No data loss | <1% data loss | <5% data loss |

### 5.4 Risk Appetite Monitoring

#### 5.4.1 Appetite Utilization Metrics

| Metric | Formula | Target | Alert Threshold |
|--------|---------|--------|-----------------|
| **Appetite Utilization** | Current MDRS / Appetite threshold × 100 | ≤80% | ≥100% |
| **Appetite Breach Count** | Number of risks exceeding appetite | 0 | ≥1 |
| **Appetite Headroom** | Appetite threshold − Current MDRS | ≥1.0 | <0.5 |
| **Near-Appetite Count** | Risks within 10% of appetite threshold | 0 | ≥3 |

#### 5.4.2 Appetite Escalation

| Utilization | Status | Action | Escalation |
|-------------|--------|--------|------------|
| <80% | Within appetite | Standard monitoring | None |
| 80–99% | Near appetite | Increased monitoring | Risk Owner notified |
| 100–109% | At appetite | Treatment required | Department Head notified |
| 110–124% | Above appetite | Mandatory treatment | CISO/CTO notified |
| ≥125% | Significantly above appetite | Immediate treatment | Risk Committee notified |

### 5.5 Risk Appetite Adjustment

Risk appetite may be adjusted based on:

| Factor | Adjustment | Approval | Documentation |
|--------|-----------|----------|---------------|
| **Business Growth** | Increase appetite for growth-related risks | Risk Committee | Board approval |
| **Regulatory Change** | Decrease appetite for new compliance risks | Compliance Officer | Risk Committee approval |
| **Incident History** | Decrease appetite for incident-prone domains | CISO | Risk Committee approval |
| **Maturity Improvement** | Increase appetite as controls mature | CAIO | Risk Committee approval |
| **Market Conditions** | Adjust appetite for competitive pressures | CEO | Board approval |

---

## 6. Risk-Based Decision Making

### 6.1 Decision Framework

```
┌─────────────────────────────────────────────────────────────────────┐
│              RISK-BASED DECISION MAKING FRAMEWORK                    │
│                                                                       │
│  ┌──────────────┐                                                    │
│  │ 1. IDENTIFY  │  What decision needs to be made?                  │
│  │   DECISION   │  What are the options?                             │
│  └──────┬───────┘                                                    │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                    │
│  │ 2. ASSESS    │  What risks are associated with each option?       │
│  │   RISKS      │  What is the MDRS for each option?                 │
│  └──────┬───────┘                                                    │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                    │
│  │ 3. EVALUATE  │  Compare risks against appetite                     │
│  │   OPTIONS    │  Evaluate cost-benefit of each option              │
│  └──────┬───────┘                                                    │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                    │
│  │ 4. DECIDE    │  Select option with best risk-adjusted value       │
│  │   & DOCUMENT │  Document rationale and approval                   │
│  └──────┬───────┘                                                    │
│         │                                                             │
│         ▼                                                             │
│  ┌──────────────┐                                                    │
│  │ 5. MONITOR   │  Track risk profile of chosen option               │
│  │   & REVIEW   │  Re-evaluate if risk profile changes               │
│  └──────────────┘                                                    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Decision Categories

#### 6.2.1 Deployment Decisions

| Decision | Risk Criteria | Approval Authority | Documentation |
|----------|--------------|-------------------|---------------|
| **Deploy to Production** | All risks ≤ Medium tier, no Critical risks open | System Owner | Deployment approval record |
| **Deploy with Conditions** | High risks with mitigation plans in place | Department Head | Conditional approval record |
| **Deploy to Staging Only** | Critical risks or unresolved High risks | CISO/CTO | Staging-only approval |
| **Do Not Deploy** | Prohibited risks or unacceptable residual risk | Risk Committee | Rejection record with rationale |

#### 6.2.2 Model Lifecycle Decisions

| Decision | Risk Criteria | Approval Authority | Documentation |
|----------|--------------|-------------------|---------------|
| **Approve Model for Training** | Data risks ≤ Medium, no DAT-05 open | Data Science Lead | Training approval |
| **Approve Model for Evaluation** | Training complete, performance meets baseline | ML Engineer | Evaluation approval |
| **Approve Model for Deployment** | All MOD risks ≤ Medium, robustness tests pass | CTO | Deployment approval |
| **Approve Model for Retirement** | End-of-life criteria met, data retention compliant | System Owner | Retirement approval |
| **Emergency Model Rollback** | Critical risk detected in production | On-call Engineer | Rollback record |

#### 6.2.3 Vendor Management Decisions

| Decision | Risk Criteria | Approval Authority | Documentation |
|----------|--------------|-------------------|---------------|
| **Approve Vendor Onboarding** | TPR risks ≤ Medium, due diligence complete | CPO | Vendor approval |
| **Approve Vendor for High-Risk Use** | TPR risks ≤ Low, enhanced due diligence complete | Risk Committee | High-risk vendor approval |
| **Reject Vendor** | TPR risks ≥ High or due diligence fails | CPO | Vendor rejection record |
| **Terminate Vendor Relationship** | Vendor risk becomes unacceptable | Risk Committee | Termination record |

#### 6.2.4 Incident Response Decisions

| Decision | Risk Criteria | Approval Authority | Documentation |
|----------|--------------|-------------------|---------------|
| **Declare AI Incident** | Any risk materializes with actual harm | AI Risk Officer | Incident record |
| **Activate Incident Response** | P1 or P2 incident | CISO | Incident activation record |
| **Escalate to Executive** | P1 incident or regulatory reportable | CISO → CTO | Escalation record |
| **Declare Emergency** | Existential risk to organization | CTO → CEO | Emergency declaration |
| **Close Incident** | Root cause addressed, residual risk acceptable | AI Risk Officer | Incident closure record |

### 6.3 Risk-Adjusted Decision Score

Each decision option is scored using a risk-adjusted value model:

```
Risk-Adjusted Value (RAV) = Business Value × (1 − Risk Penalty) − Risk Cost

Where:
  Business Value = Expected benefit of the option (quantified)
  Risk Penalty = MDRS / 5 × 0.5 (0 to 0.5 based on risk level)
  Risk Cost = Expected loss from risk materializing (ALE)
```

| RAV Range | Decision | Action |
|-----------|----------|--------|
| RAV > 0.8 × BV | Strongly favorable | Approve |
| RAV 0.6–0.8 × BV | Favorable | Approve with monitoring |
| RAV 0.4–0.6 × BV | Marginal | Approve with conditions |
| RAV 0.2–0.4 × BV | Unfavorable | Reject or redesign |
| RAV < 0.2 × BV | Strongly unfavorable | Reject |

### 6.4 Decision Documentation Template

```markdown
# Risk-Based Decision Record: [DECISION-ID]

## Decision Summary
- **Decision:** [description]
- **Decision Date:** [date]
- **Decision Maker:** [name, role]
- **Decision Category:** [Deployment/Model/Vendor/Incident]

## Options Considered
| Option | Description | Business Value | MDRS | RAV |
|--------|-------------|----------------|------|-----|
| Option 1 | ... | $X | Y | Z |
| Option 2 | ... | $X | Y | Z |

## Risk Assessment
- **Selected Option:** [option]
- **Risk Profile:** [MDRS, tier, key risks]
- **Risk Appetite:** [within/exceeds appetite]
- **Mitigation Required:** [yes/no, details]

## Decision Rationale
- **Why this option:** [explanation]
- **Why not alternatives:** [explanation]
- **Risk acceptance:** [if applicable]

## Approval
- **Approver:** [name, role, date]
- **Conditions:** [any conditions attached]
- **Review Date:** [date]

## Monitoring
- **KRIs to monitor:** [list]
- **Escalation triggers:** [list]
- **Next review:** [date]
```

### 6.5 Decision Review and Appeal

| Review Type | Trigger | Reviewer | Timeline |
|-------------|---------|----------|----------|
| **Routine Review** | Scheduled per decision type | Original decision maker | Per schedule |
| **Triggered Review** | Risk profile changes significantly | Next-level authority | Within 5 business days |
| **Appeal** | Decision maker disagrees with risk assessment | Risk Committee | Within 10 business days |
| **Post-Implementation Review** | After implementation | Independent reviewer | 30 days after implementation |

---

## 7. Risk Reporting & Escalation

### 7.1 Integrated Reporting Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│              RISK REPORTING & ESCALATION ARCHITECTURE                │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    DATA SOURCES                              │    │
│  │  Risk Register │ Monitoring │ Incidents │ Audits │ KRIs     │    │
│  └──────────────────────────┬──────────────────────────────────┘    │
│                              │                                        │
│                              ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                 RISK ANALYTICS ENGINE                        │    │
│  │  • Risk scoring (MDRS)    • Trend analysis                  │    │
│  │  • Appetite monitoring     • Predictive modeling             │    │
│  │  • Control effectiveness   • Portfolio optimization          │    │
│  └──────────────────────────┬──────────────────────────────────┘    │
│                              │                                        │
│              ┌───────────────┼───────────────┐                       │
│              │               │               │                        │
│              ▼               ▼               ▼                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │  OPERATIONAL │ │  MANAGEMENT  │ │  EXECUTIVE   │                │
│  │  REPORTING   │ │  REPORTING   │ │  REPORTING   │                │
│  │              │ │              │ │              │                │
│  │ • Real-time  │ │ • Weekly     │ │ • Quarterly  │                │
│  │ • Dashboard  │ │ • Program    │ │ • Board      │                │
│  │ • Alerts     │ │ • Domain     │ │ • Strategic  │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Report Types and Specifications

#### 7.2.1 Operational Risk Reports

| Report | Audience | Frequency | Format | Content |
|--------|----------|-----------|--------|---------|
| **Real-Time Risk Dashboard** | All stakeholders | Real-time | Web dashboard | Risk posture, KRIs, alerts, top risks |
| **Daily Risk Brief** | Risk owners, managers | Daily | Email + dashboard | New risks, tier changes, overdue treatments |
| **Weekly Risk Summary** | Risk owners, managers | Weekly | PDF + CSV | Risk register summary, treatment status, control effectiveness |
| **Incident Risk Report** | All stakeholders | Per incident | PDF + web | Incident details, risk analysis, response actions, lessons learned |

#### 7.2.2 Management Risk Reports

| Report | Audience | Frequency | Format | Content |
|--------|----------|-----------|--------|---------|
| **Monthly Risk Posture Report** | Department heads, CAIO | Monthly | PDF + dashboard | Risk posture by domain, trend analysis, appetite utilization, treatment progress |
| **Quarterly Risk Review** | Risk Committee, C-suite | Quarterly | PDF + presentation | Comprehensive risk review, appetite assessment, treatment effectiveness, recommendations |
| **Domain Risk Report** | Domain owners | Monthly | PDF + dashboard | Domain-specific risk analysis, control effectiveness, remediation status |

#### 7.2.3 Executive Risk Reports

| Report | Audience | Frequency | Format | Content |
|--------|----------|-----------|--------|---------|
| **Executive Risk Report** | C-suite, Board | Quarterly | PDF + interactive | Risk posture summary, material risks, treatment summary, control effectiveness, compliance posture, decisions required |
| **Annual Risk Report** | Board, Executive leadership | Annually | PDF + presentation | Annual risk review, framework effectiveness, maturity assessment, strategic recommendations |
| **Regulatory Risk Report** | Regulators, auditors | On-demand | Evidence pack | Compliance evidence, risk assessment documentation, treatment records |

### 7.3 Risk Dashboard Specifications

#### 7.3.1 Executive Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EXECUTIVE RISK DASHBOARD                          │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  OVERALL RISK POSTURE                                        │    │
│  │  MDRS: 2.85 (Medium)  │  Trend: ↓ 0.12  │  Appetite: 71%   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │Critical │ │  High   │ │ Medium  │ │  Low    │ │ Minimal │      │
│  │   2     │ │   5     │ │   12    │ │   28    │ │   43    │      │
│  │   🔴    │ │   🔴    │ │   🟡    │ │   🟢    │ │   🟢    │      │
│  │ ↑1      │ │ ↓2      │ │ ↔      │ │ ↓3      │ │ ↑5      │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  RISK POSTURE BY DOMAIN                                      │    │
│  │  GOV 2.1 🟢 │ DAT 3.2 🟡 │ MOD 2.8 🟡 │ SEC 3.5 🔴          │    │
│  │  HUM 2.9 🟡 │ OPS 2.4 🟢 │ TPR 3.1 🟡 │ CMP 2.6 🟢          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  TOP 5 MATERIAL RISKS                                        │    │
│  │  1. [SEC-02] Agent goal hijacking — MDRS 4.2 🔴 High        │    │
│  │  2. [DAT-03] Bias in loan model — MDRS 3.8 🔴 High          │    │
│  │  3. [TPR-01] Vendor concentration — MDRS 3.5 🔴 High        │    │
│  │  4. [MOD-02] Model drift detected — MDRS 3.2 🟡 Medium      │    │
│  │  5. [CMP-03] Conformity gap — MDRS 3.1 🟡 Medium           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  KEY RISK INDICATORS                                         │    │
│  │  Open Critical Risks: 2 🔴  │  Open High Risks: 5 🔴        │    │
│  │  Treatment Overdue: 1 🟡     │  Control Failure Rate: 3% 🟢   │    │
│  │  Assessment Currency: 95% 🟢 │  Vendor Risk Exposure: 0 🟢   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  DECISIONS REQUIRED: 3  │  APPETITE BREACHES: 0              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

#### 7.3.2 Program Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROGRAM RISK DASHBOARD                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  TREATMENT PROGRESS                                          │    │
│  │  Planned: 45  │  In Progress: 12  │  Implemented: 28        │    │
│  │  Verified: 25  │  Overdue: 1  │  Cancelled: 4               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  CONTROL EFFECTIVENESS                                       │    │
│  │  Excellent (90-100): 8  │  Good (75-89): 12                 │    │
│  │  Adequate (60-74): 5    │  Poor (40-59): 0  │  Critical: 0  │    │
│  │  Mean Effectiveness: 82%                                     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  RISK TREND (90-Day Rolling)                                 │    │
│  │  Overall: 3.10 → 2.95 → 2.85 (↓ 0.25)                       │    │
│  │  Critical: 3 → 2 → 2 (↓ 1)                                  │    │
│  │  High: 8 → 6 → 5 (↓ 3)                                      │    │
│  │  Medium: 15 → 14 → 12 (↓ 3)                                 │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  APPETITE UTILIZATION BY DOMAIN                              │    │
│  │  GOV: 68% 🟢 │ DAT: 85% 🟡 │ MOD: 72% 🟢 │ SEC: 92% 🔴      │    │
│  │  HUM: 78% 🟡 │ OPS: 64% 🟢 │ TPR: 77% 🟡 │ CMP: 72% 🟢      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.4 Escalation Framework

#### 7.4.1 Escalation Triggers

| Trigger | Description | Severity | Response Time | Escalation Path |
|---------|-------------|----------|---------------|-----------------|
| **Risk Materialization** | Risk event occurs with actual harm | P1 | 15 minutes | CISO → CTO → Risk Committee |
| **Tier Escalation** | Risk tier increases to Critical | P1 | 15 minutes | CISO → CTO → Risk Committee |
| **Tier Escalation** | Risk tier increases to High | P2 | 1 hour | Security Lead → Risk Owner |
| **Tier Escalation** | Risk tier increases to Medium | P3 | 4 hours | GRC Analyst → Risk Owner |
| **Appetite Breach** | Risk exceeds appetite threshold | P2 | 1 hour | Risk Owner → Department Head |
| **Control Failure** | Control effectiveness drops below 50% | P2 | 1 hour | Control Owner → Risk Owner |
| **Treatment Overdue** | Treatment plan past due date | P3 | 4 hours | Risk Owner → Department Head |
| **KRI Breach** | Key risk indicator crosses threshold | P3 | 4 hours | GRC Analyst → Risk Owner |
| **Regulatory Breach** | Regulatory requirement violated | P1 | 15 minutes | Compliance Officer → CISO → CTO |
| **Incident Recurrence** | Same incident type occurs again | P2 | 1 hour | AI Risk Officer → CISO |

#### 7.4.2 Escalation Procedures

**P1 – Critical Escalation:**
```
1. Detection (0-15 min)
   • Automated alert fires
   • On-call engineer acknowledges
   • Incident commander assigned

2. Initial Response (15-60 min)
   • Containment actions executed
   • CISO notified
   • CTO notified
   • Risk Committee notified

3. Assessment (1-4 hours)
   • Impact assessment completed
   • Root cause analysis initiated
   • Regulatory reporting assessment

4. Resolution (4-24 hours)
   • Corrective actions implemented
   • Risk Committee briefing
   • Regulatory notifications (if required)

5. Closure (24-72 hours)
   • Post-incident review
   • Lessons learned documented
   • Corrective action plan
   • Risk register updated
```

**P2 – High Escalation:**
```
1. Detection (0-1 hour)
   • Alert fires
   • Risk owner acknowledges

2. Assessment (1-4 hours)
   • Risk assessment completed
   • Treatment plan updated

3. Resolution (4-48 hours)
   • Treatment actions implemented
   • Effectiveness verified

4. Closure (48 hours - 1 week)
   • Residual risk assessed
   • Risk register updated
   • Lessons learned documented
```

#### 7.4.3 Escalation Matrix

| Risk Tier | Risk Owner | Department Head | CISO/CTO | Risk Committee | Board |
|-----------|-----------|-----------------|----------|----------------|-------|
| Critical | Notify immediately | Notify within 1 hour | Notify within 15 min | Notify within 15 min | Notify within 4 hours |
| High | Notify within 1 hour | Notify within 4 hours | Notify within 1 hour | Notify within 24 hours | — |
| Medium | Notify within 4 hours | Notify within 24 hours | — | — | — |
| Low | Notify within 24 hours | — | — | — | — |
| Minimal | Weekly summary | — | — | — | — |

### 7.5 Risk Reporting Calendar

| Report | Frequency | Audience | Owner | Delivery |
|--------|-----------|----------|-------|----------|
| Real-Time Dashboard | Continuous | All stakeholders | GRC Platform | Web |
| Daily Risk Brief | Daily (8:00 AM) | Risk owners, managers | GRC Analyst | Email |
| Weekly Risk Summary | Weekly (Monday) | Risk owners, managers | GRC Analyst | Email + PDF |
| Monthly Risk Posture | Monthly (1st business day) | Department heads, CAIO | AI Risk Officer | PDF + Dashboard |
| Domain Risk Report | Monthly (5th business day) | Domain owners | Domain Risk Lead | PDF + Dashboard |
| Quarterly Risk Review | Quarterly (1st month) | Risk Committee, C-suite | AI Risk Officer | PDF + Presentation |
| Executive Risk Report | Quarterly (1st month) | C-suite, Board | CAIO | PDF + Interactive |
| Annual Risk Report | Annually (January) | Board, Executive leadership | CAIO | PDF + Presentation |
| Regulatory Risk Report | On-demand | Regulators, auditors | Compliance Officer | Evidence Pack |

### 7.6 Risk Communication Standards

#### 7.6.1 Communication Principles

1. **Timely** — Report risks as soon as they are identified or change
2. **Accurate** — Ensure all risk data is verified and validated
3. **Relevant** — Tailor information to audience needs
4. **Actionable** — Include clear recommendations and decisions required
5. **Consistent** — Use standard formats and terminology
6. **Transparent** — Report both positive and negative risk developments

#### 7.6.2 Risk Communication Channels

| Channel | Use Case | Audience | Frequency |
|---------|----------|----------|-----------|
| **Risk Dashboard** | Real-time risk posture | All stakeholders | Continuous |
| **Email Alerts** | Urgent risk notifications | Risk owners, managers | As needed |
| **Risk Reports** | Detailed risk analysis | Management, executives | Scheduled |
| **Risk Committee Meetings** | Strategic risk discussions | Risk Committee | Monthly |
| **Board Presentations** | Executive risk reporting | Board | Quarterly |
| **Incident Notifications** | Incident communication | All stakeholders | Per incident |
| **Regulatory Filings** | Compliance reporting | Regulators | As required |

---

## 8. Appendices

### Appendix A: Risk Treatment Selection Algorithm — Complete Rule Catalog

| Rule ID | Priority | Condition | Strategy | Authority | Rationale |
|---------|----------|-----------|----------|-----------|-----------|
| A-01 | 1 | CMP-01 | AVOID | Risk Committee | EU AI Act Art. 5 |
| A-02 | 1 | CMP-02 AND MDRS ≥ 3.50 | MITIGATE | CISO/CTO | Misclassified high-risk |
| A-03 | 1 | CMP-03 AND MDRS ≥ 4.00 | MITIGATE | Compliance Officer | Conformity gap |
| A-04 | 1 | CMP-04 AND cross-border | MITIGATE | Compliance Officer | Legal exposure |
| B-01 | 2 | MDRS ≥ 4.50 | AVOID/MITIGATE | Risk Committee | Critical risk |
| B-02 | 2 | MDRS 3.50–4.49 | MITIGATE | CISO/CTO | High risk |
| B-03 | 2 | MDRS 2.50–3.49 | MITIGATE/ACCEPT | Department Head | Medium risk |
| B-04 | 2 | MDRS 1.50–2.49 | ACCEPT/MITIGATE | Business Unit Owner | Low risk |
| B-05 | 2 | MDRS 1.00–1.49 | ACCEPT | System Owner | Minimal risk |
| C-01 | 3 | SEC AND MDRS ≥ 3.50 | MITIGATE | CISO | Security mandatory |
| C-02 | 3 | HUM AND I ≥ 4 | MITIGATE | CAIO | Human harm mandatory |
| C-03 | 3 | DAT-05 AND MDRS ≥ 3.00 | MITIGATE | Data Science Lead | Data poisoning mandatory |
| C-04 | 3 | TPR-01 AND MDRS ≥ 4.00 | MITIGATE/TRANSFER | CPO | Vendor risk mandatory |
| C-05 | 3 | OPS-02 AND MDRS ≥ 3.50 | MITIGATE | CISO | Incident readiness mandatory |
| D-01 | 4 | Mitigation cost > Exposure × 0.5 | TRANSFER/ACCEPT | Risk Owner | Not cost-effective |
| D-02 | 4 | Mitigation cost < Exposure × 0.1 | MITIGATE | Risk Owner | Highly cost-effective |
| D-03 | 4 | Transfer cost < Mitigation × 0.3 | TRANSFER | Risk Owner | Transfer cheaper |
| D-04 | 4 | Residual > Appetite | Add controls/AVOID | Risk Owner | Mitigation insufficient |

### Appendix B: Cost-Benefit Analysis Worksheets

#### B.1 Risk Exposure Worksheet

| Field | Value | Notes |
|-------|-------|-------|
| Risk ID | RISK-2026-XXX | |
| Asset Value | $XXX,XXX | |
| Likelihood (1-5) | X | |
| Impact (1-5) | X | |
| Exposure Factor | 0.X | |
| SLE | $XXX,XXX | Asset Value × Exposure Factor |
| ARO | 0.XX | Likelihood / 5 × adjustment |
| ALE (Inherent) | $XXX,XXX | SLE × ARO |
| ALE (Residual) | $XXX,XXX | With controls |
| Risk Reduction | $XXX,XXX | Inherent ALE − Residual ALE |

#### B.2 Treatment Cost Worksheet

| Cost Category | Year 1 | Year 2 | Year 3 | Total |
|---------------|--------|--------|--------|-------|
| Implementation | $XXX,XXX | — | — | $XXX,XXX |
| Operating | $XXX,XXX | $XXX,XXX | $XXX,XXX | $XXX,XXX |
| Opportunity | $XXX,XXX | $XXX,XXX | $XXX,XXX | $XXX,XXX |
| Compliance | $XXX,XXX | $XXX,XXX | $XXX,XXX | $XXX,XXX |
| **Total** | $XXX,XXX | $XXX,XXX | $XXX,XXX | $XXX,XXX |

#### B.3 Cost-Benefit Summary

| Metric | Value |
|--------|-------|
| Risk Reduction (3-year) | $XXX,XXX |
| Treatment Cost (3-year) | $XXX,XXX |
| Net Benefit | $XXX,XXX |
| Cost-Benefit Ratio | X.XX |
| Return on Risk Investment | XXX% |
| Payback Period | X.X months |
| Decision | [Implement/Transfer/Accept/Reject] |

### Appendix C: Effectiveness Measurement Scorecard

| Control ID | Control Name | Design Score | Implementation Score | Operational Score | Outcome Score | Overall Score | Rating | Action |
|------------|-------------|-------------|---------------------|-------------------|---------------|---------------|--------|--------|
| CTRL-001 | Input sanitization | 90 | 85 | 88 | 82 | 86 | Good | Maintain |
| CTRL-002 | Goal integrity monitoring | 95 | 90 | 92 | 88 | 91 | Excellent | Maintain |
| CTRL-003 | Tool access controls | 80 | 75 | 70 | 65 | 72 | Adequate | Improve |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

### Appendix D: Risk Appetite Statement Template

```markdown
# Risk Appetite Statement — [Domain/Organization]

## Overall Appetite
- **Appetite Level:** [Conservative/Cautious/Balanced/Aggressive]
- **Maximum Acceptable MDRS:** [X.XX]
- **Review Frequency:** [Annual/Semi-annual/Quarterly]

## Domain Appetite
| Domain | Max MDRS | Appetite Level | Rationale |
|--------|----------|----------------|-----------|
| GOV | X.XX | [Level] | [Rationale] |
| DAT | X.XX | [Level] | [Rationale] |
| ... | ... | ... | ... |

## Qualitative Appetite
| Dimension | Threshold | Measurement |
|-----------|-----------|-------------|
| Financial Impact | ≤$XXX,XXX | Per incident |
| Reputational Impact | [Description] | Press monitoring |
| Regulatory Impact | [Description] | Compliance tracking |
| Human Impact | [Description] | Incident tracking |
| Operational Impact | ≤X hours | Downtime tracking |
| Data Impact | ≤X% | Data loss tracking |

## Appetite Adjustment Criteria
| Factor | Adjustment | Approval |
|--------|-----------|----------|
| Business Growth | [Criteria] | [Authority] |
| Regulatory Change | [Criteria] | [Authority] |
| Incident History | [Criteria] | [Authority] |
| Maturity Improvement | [Criteria] | [Authority] |

## Approval
- **Approved By:** [Name, Role]
- **Approval Date:** [Date]
- **Next Review:** [Date]
```

### Appendix E: Glossary

| Term | Definition |
|------|-----------|
| **RTSA** | Risk Treatment Selection Algorithm — deterministic model for selecting treatment strategy |
| **RTCBA** | Risk Treatment Cost-Benefit Analysis — quantitative model for comparing treatment options |
| **ALE** | Annualized Loss Expectancy — expected annual loss from risk |
| **SLE** | Single Loss Expectancy — loss from a single risk event |
| **ARO** | Annual Rate of Occurrence — frequency of risk events per year |
| **CBR** | Cost-Benefit Ratio — ratio of risk reduction to treatment cost |
| **RORI** | Return on Risk Investment — percentage return on treatment investment |
| **RAV** | Risk-Adjusted Value — business value adjusted for risk |
| **CE** | Control Effectiveness — measure of how well a control reduces risk |
| **RRR** | Risk Reduction Rate — percentage reduction in risk from controls |
| **Appetite Utilization** | Current risk level as percentage of appetite threshold |
| **Multi-Strategy Treatment** | Using multiple treatment strategies for a single risk |
| **Portfolio Optimization** | Allocating treatment resources across risks for maximum benefit |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial framework |

---

*This framework is a living document. It shall be reviewed and updated:*
- *After any significant AI incident*
- *When new AI regulations take effect*
- *When new AI use cases are introduced*
- *At minimum, annually*

---

*End of Framework*
