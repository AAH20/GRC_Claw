# GRC_Claw U-AIGMM Assessment Methodology & Improvement Planning Expansion

## Detailed Assessment Methodology, Scoring Algorithms, and Automation

**Version:** 1.0  
**Date:** October 2026  
**Supersedes:** Sections 6-11 of GRC_Claw_Unified_AI_Governance_Maturity_Model.md  
**Companion to:** grc-claw-ci-framework.md  
**License:** Open Source (CC BY-SA 4.0)

---

## Table of Contents

1. [Assessment Questionnaire Design](#1-assessment-questionnaire-design)
2. [Scoring Algorithm](#2-scoring-algorithm)
3. [Maturity Level Definitions](#3-maturity-level-definitions)
4. [Improvement Roadmap Template](#4-improvement-roadmap-template)
5. [Benchmark Data](#5-benchmark-data)
6. [Assessment Automation](#6-assessment-automation)
7. [Appendices](#7-appendices)

---

## 1. Assessment Questionnaire Design

### 1.1 Design Principles

The U-AIGMM questionnaire is built on seven design principles derived from the source models:

| Principle | Source | Application |
|-----------|--------|-------------|
| **Cumulative progression** | MITRE, CMMI AIM | Each level presupposes all lower levels are met |
| **Dual-stream coverage** | OWASP AIMA | Every sub-dimension has Stream A (Create/Promote) and Stream B (Measure/Improve) questions |
| **Evidence-anchored** | OWASP AIMA, CMMI AIM | Each question maps to verifiable evidence artifacts |
| **Multi-rater capable** | Microsoft RAI MM | Questions are role-agnostic; rater perspective captured separately |
| **Perception-sensitive** | Microsoft RAI MM | Same question can be scored differently by different rater groups |
| **Outcome-linked** | AAGMM, Gartner | Questions connect to business outcome metrics |
| **Standards-mapped** | CMMI AIM, ISO 42001 | Every question traces to a standards clause |

### 1.2 Question Bank Architecture

The full question bank contains **180 questions** across 36 sub-dimensions (5 questions per sub-dimension: 3 Stream A, 2 Stream B).

```
Question Bank Structure:
├── Pillar 1: Governance & Strategy (45 questions)
│   ├── Domain 1.1: AI Governance Framework (15Q)
│   ├── Domain 1.2: AI Strategy & Value Alignment (15Q)
│   └── Domain 1.3: Risk & Compliance Management (15Q)
├── Pillar 2: Responsible AI & Ethics (45 questions)
│   ├── Domain 2.1: Fairness, Transparency & Explainability (15Q)
│   ├── Domain 2.2: Privacy & Data Protection (15Q)
│   └── Domain 2.3: Human Oversight & Accountability (15Q)
├── Pillar 3: Technical Foundation (60 questions)
│   ├── Domain 3.1: Data Governance & Quality (15Q)
│   ├── Domain 3.2: Model & Platform Security (15Q)
│   ├── Domain 3.3: Agent Identity & Access Governance (15Q)
│   └── Domain 3.4: Runtime Behavioral Controls (15Q)
└── Pillar 4: Operations & Performance (30 questions)
    ├── Domain 4.1: Monitoring & Incident Response (10Q)
    ├── Domain 4.2: Workforce & Organizational Readiness (10Q)
    └── Domain 4.3: Continuous Improvement & Innovation (10Q)
```

### 1.3 Question Format Specification

Each question follows a standardized format:

```
Question ID: [Pillar].[Domain].[Sub-dimension].[Stream].[Sequence]
Question Text: [Interrogative statement]
Response Type: [Ordinal 1-5 | Binary | Percentage | Count]
Evidence Required: [Artifact type]
Standards Mapping: [ISO/NIST/EU AI Act clause]
Rater Guidance: [Context for scoring]
```

#### 1.3.1 Response Types

| Response Type | Scale | Scoring | Example |
|---------------|-------|---------|---------|
| **Ordinal Maturity** | 1-5 | Direct mapping | "Rate your organization's practice" |
| **Binary** | Yes/No | Yes=next level, No=current level | "Is X documented?" |
| **Percentage** | 0-100% | Banded to 1-5 | "What % of systems have X?" |
| **Count** | Integer | Banded to 1-5 | "How many incidents occurred?" |
| **Frequency** | Never→Continuous | Banded to 1-5 | "How often is X reviewed?" |

#### 1.3.2 Evidence Requirements by Level

| Level | Evidence Type | Examples |
|-------|---------------|----------|
| **1** | Absence confirmation | "No policy document exists" — confirmed by search |
| **2** | Draft/informal artifact | Draft policy, informal process description, spreadsheet |
| **3** | Approved/formal artifact | Approved policy, published process, GRC tool record |
| **4** | Quantitative evidence | Metrics dashboard, automated reports, audit results |
| **5** | Predictive/innovative evidence | Predictive models, industry contributions, patents |

### 1.4 Rater Assignment Matrix

| Rater Role | Pillars | Domains | Question Count | Time Estimate |
|------------|---------|---------|----------------|---------------|
| **Executive Sponsor** | P1 | 1.1, 1.2, 1.3 | 45 | 2 hours |
| **Governance Lead** | P1, P4 | 1.1, 1.3, 4.1, 4.3 | 40 | 2 hours |
| **Ethics/Compliance Lead** | P2 | 2.1, 2.2, 2.3 | 45 | 2 hours |
| **Technical Lead** | P3 | 3.1, 3.2, 3.3, 3.4 | 60 | 3 hours |
| **Operations Lead** | P4 | 4.1, 4.2 | 20 | 1 hour |
| **Independent Assessor** | All | All | All (validation) | 8 hours |

### 1.5 Question Sequencing Rules

1. **Stream A before Stream B** within each sub-dimension (establish capability before measuring it)
2. **Lower levels before higher levels** within each question (cumulative logic)
3. **Pillar order**: 1 → 2 → 3 → 4 (governance enables responsible AI, which enables technical foundation, which enables operations)
4. **Skip logic**: If a Level N question is scored 1, all higher-level questions in that sub-dimension default to 1 (with rater confirmation)

### 1.6 Questionnaire Delivery Modes

| Mode | Tier | Platform | Features |
|------|------|----------|----------|
| **Self-service** | Tier 1 | Web form | Auto-scoring, basic heat map |
| **Facilitated** | Tier 2 | Workshop + tool | Multi-rater, divergence analysis, evidence upload |
| **Appraisal** | Tier 3 | CMMI-style | Full evidence review, interviews, observation |

---

## 2. Scoring Algorithm

### 2.1 Hierarchical Scoring Model

The U-AIGMM uses a bottom-up hierarchical scoring model with configurable weights.

#### 2.1.1 Base Formulas

```
Question Score (q_i) ∈ {1, 2, 3, 4, 5}

Sub-dimension Score (s_j) = Σ(q_i × w_i) / Σ(w_i)
  where w_i = question weight (default: 1.0)

Domain Score (d_k) = Σ(s_j × v_j) / Σ(v_j)
  where v_j = sub-dimension weight (default: 1.0)

Pillar Score (p_l) = Σ(d_k × x_k) / Σ(x_k)
  where x_k = domain weight (default: 1.0)

Overall Maturity Score (M) = Σ(p_l × y_l) / Σ(y_l)
  where y_l = pillar weight (default: 1.0)
```

#### 2.1.2 Stream Weighting

Each sub-dimension has Stream A and Stream B questions. The stream-weighted score:

```
Stream A Score (A_j) = Average of Stream A question scores in sub-dimension j
Stream B Score (B_j) = Average of Stream B question scores in sub-dimension j

Stream-Weighted Sub-dimension Score (s'_j) = (A_j × 0.6) + (B_j × 0.4)
```

**Rationale**: Stream A (Create & Promote) is weighted higher because establishing capabilities precedes measuring them. A organization that has implemented controls but doesn't measure them is more mature than one that measures non-existent controls.

#### 2.1.3 Partial Credit Calculation

When a sub-dimension meets all criteria at Level N but only some at Level N+1:

```
Partial Credit Score = N + (met_criteria_at_N+1 / total_criteria_at_N+1) × 0.5

Example: All Level 2 criteria met, 3 of 5 Level 3 criteria met
Score = 2 + (3/5) × 0.5 = 2.3
```

#### 2.1.4 Confidence Interval Calculation

For multi-rater assessments, each sub-dimension score includes a confidence interval:

```
Standard Error (SE) = σ / √n
  where σ = standard deviation of rater scores, n = number of raters

95% Confidence Interval = Score ± (1.96 × SE)

Interpretation:
- CI width < 0.3: High confidence, scores reliable
- CI width 0.3-0.6: Moderate confidence, consider additional evidence
- CI width > 0.6: Low confidence, facilitated discussion required
```

### 2.2 Weight Configuration

#### 2.2.1 Default Weights

| Level | Component | Weight | Rationale |
|-------|-----------|--------|-----------|
| Pillar | All 4 pillars | 1.0 each | Equal importance |
| Domain | All 12 domains | 1.0 each | Equal importance |
| Sub-dimension | All 36 sub-dimensions | 1.0 each | Equal importance |
| Stream | Stream A / Stream B | 0.6 / 0.4 | Capability-first |
| Question | All questions | 1.0 each | Equal importance |

#### 2.2.2 Custom Weight Profiles

Organizations can customize weights based on their context:

**Regulated Industry Profile** (Financial Services, Healthcare):
```
Pillar 2 (Responsible AI): 1.3×
Pillar 3 (Technical Foundation): 1.2×
Domain 2.2 (Privacy): 1.4×
Domain 3.2 (Security): 1.3×
Domain 1.3 (Risk & Compliance): 1.3×
```

**Startup/Scale-up Profile**:
```
Pillar 1 (Governance): 0.8×
Pillar 3 (Technical Foundation): 1.3×
Domain 3.3 (Agent Identity): 1.4×
Domain 3.4 (Runtime Controls): 1.4×
Domain 4.2 (Workforce): 0.7×
```

**Enterprise Transformation Profile**:
```
Pillar 4 (Operations): 1.3×
Pillar 1 (Governance): 1.2×
Domain 4.1 (Monitoring): 1.3×
Domain 4.3 (Continuous Improvement): 1.3×
Domain 1.1 (Governance Framework): 1.2×
```

### 2.3 Perception Divergence Scoring

When multiple raters assess the same sub-dimension:

```
Divergence Score (D) = |Rater_A_Score - Rater_B_Score|

Divergence Interpretation:
| Divergence | Level | Action |
|------------|-------|--------|
| D ≤ 0.5 | Negligible | No action needed |
| 0.5 < D ≤ 1.0 | Minor | Document and monitor |
| 1.0 < D ≤ 2.0 | Moderate | Facilitated discussion required |
| D > 2.0 | Severe | Executive escalation, alignment workshop |

Perception Divergence Index (PDI) = Average D across all sub-dimensions
PDI > 1.0 indicates systemic communication/alignment issues
```

### 2.4 Maturity Level Assignment

#### 2.4.1 Threshold-Based Assignment

| Level | Score Range | Label |
|-------|-------------|-------|
| 1 | 1.00 - 1.80 | Initial |
| 2 | 1.81 - 2.60 | Developing |
| 3 | 2.61 - 3.40 | Defined |
| 4 | 3.41 - 4.20 | Managed |
| 5 | 4.21 - 5.00 | Optimizing |

#### 2.4.2 Cumulative Gate Assignment

An alternative assignment method that enforces cumulative progression:

```
A sub-dimension is assigned Level N only if:
1. Average score ≥ threshold for Level N, AND
2. At least 80% of questions at Level N-1 are scored ≥ N-1, AND
3. At least 60% of questions at Level N-2 are scored ≥ N-2

This prevents "island of excellence" scoring where a few high scores
mask fundamental gaps.
```

#### 2.4.3 Mixed Method Assignment

The recommended approach combines both methods:

```
Final Level = min(Threshold-Based Level, Cumulative Gate Level)

Example: 
- Threshold-Based: 3.2 → Level 3
- Cumulative Gate: Level 2 (because only 50% of Level 1 questions met)
- Final: Level 2
```

### 2.5 Business Outcome Integration

Scores are linked to business outcome metrics for validation:

| Outcome Metric | Level 1 Range | Level 3 Range | Level 5 Range | Data Source |
|----------------|---------------|---------------|---------------|-------------|
| Agent Sprawl Index | >0.8 | 0.3-0.5 | <0.1 | Agent inventory |
| Risk Incident Rate (per 1K actions) | >10 | 2-5 | <0.5 | Incident management |
| Effective Task Completion Rate | <60% | 75-85% | >95% | Task tracking |
| Delegation Safety Rate | <70% | 85-92% | >98% | Oversight logs |
| Mean Time to Detect (MTTD) | >7 days | 1-7 days | <1 hour | Monitoring |
| Mean Time to Remediate (MTTR) | >7 days | 1-7 days | <1 hour | Incident records |
| Policy Violation Rate | >20/1K/month | 5-10/1K/month | <2/1K/month | Audit logs |
| AI Inventory Coverage | <50% | 75-90% | >95% | Discovery tools |

**Validation Rule**: If maturity score and outcome metrics diverge by >1 level, trigger evidence review.

### 2.6 Score Normalization

For benchmarking across organizations, scores are normalized:

```
Normalized Score = (Raw Score - 1) / 4 × 100

Example: Raw score 3.2 → Normalized (3.2-1)/4 × 100 = 55
```

This produces a 0-100 scale for easy comparison.

---

## 3. Maturity Level Definitions

### 3.1 Detailed Level Characteristics

Each level is defined across eight behavioral dimensions:

#### Level 1: Initial (Ad-Hoc)

| Dimension | Characteristic | Anti-Pattern | Evidence of Level |
|-----------|----------------|--------------|-------------------|
| **Governance** | No formal structure; decisions by individual discretion | "No one owns AI governance" | No governance document exists |
| **Strategy** | No AI strategy; isolated experimentation | "We're doing AI because everyone else is" | No strategy document |
| **Risk** | Risks unidentified; reactive response | "We didn't know that could happen" | No risk register |
| **Ethics** | No ethical guidelines; issues handled ad-hoc | "We'll deal with it if someone complains" | No ethics policy |
| **Data** | Data quality unknown; no governance | "We trust the data" | No data quality metrics |
| **Security** | Basic IT security; no AI-specific controls | "Our firewall protects us" | No AI threat model |
| **Agents** | No agent inventory; shadow agents proliferate | "I didn't know that agent existed" | No agent registry |
| **Monitoring** | No monitoring; incidents discovered externally | "The customer told us about the bug" | No monitoring dashboards |
| **People** | No AI training; skills gaps unaddressed | "We hire smart people, they'll figure it out" | No training records |
| **Improvement** | No continuous improvement process | "If it ain't broke, don't fix it" | No improvement initiatives |

**Typical Organization Profile**: Startups, small businesses, organizations beginning AI adoption. ~40% of organizations.

#### Level 2: Developing (Emerging)

| Dimension | Characteristic | Anti-Pattern | Evidence of Level |
|-----------|----------------|--------------|-------------------|
| **Governance** | Charter drafted; roles informally assigned | "We have a policy but it's not enforced" | Draft policy exists |
| **Strategy** | Department-level strategy; informal prioritization | "Each team does their own thing" | Department strategy doc |
| **Risk** | Risk register exists; qualitative assessment | "We know the risks but haven't quantified them" | Risk register spreadsheet |
| **Ethics** | Guidelines documented; awareness training begun | "We have guidelines but no enforcement" | Ethics guideline document |
| **Data** | Quality processes for critical datasets only | "We check data for important models" | Data quality checklist |
| **Security** | Threat modeling begun; basic controls deployed | "We did a security review once" | Threat model document |
| **Agents** | Inventory started; basic identity management | "We know about some of our agents" | Partial agent list |
| **Monitoring** | Basic logging; manual incident response | "We check logs when there's a problem" | Log aggregation |
| **People** | AI literacy programs launched; role-specific training | "We sent people to a conference" | Training attendance records |
| **Improvement** | Ad-hoc improvement initiatives | "We fix things when they break" | Improvement tickets |

**Typical Organization Profile**: Growing organizations with some AI maturity. ~30% of organizations.

#### Level 3: Defined (Managed)

| Dimension | Characteristic | Anti-Pattern | Evidence of Level |
|-----------|----------------|--------------|-------------------|
| **Governance** | Formal body established; policies approved | "We have a committee but it doesn't meet" | Committee charter, meeting minutes |
| **Strategy** | Enterprise strategy with value metrics | "We have a strategy but don't measure outcomes" | Strategy document with KPIs |
| **Risk** | Quantitative risk assessment; treatment plans tracked | "We assess risks but don't track mitigation" | Risk register with scores |
| **Ethics** | Ethics review board operational; fairness metrics measured | "We review ethics but don't measure impact" | Review board records, metrics |
| **Data** | Enterprise data governance; lineage tracking; quality SLAs | "We track lineage for some datasets" | Data catalog, lineage diagrams |
| **Security** | AI security in SDLC; regular testing | "We test security before release" | Security test reports |
| **Agents** | Agent registry complete; identity lifecycle managed | "We know all our agents" | Agent registry with metadata |
| **Monitoring** | Automated monitoring; defined playbooks | "We get alerts and have runbooks" | Monitoring dashboards, runbooks |
| **People** | Competency framework; cross-functional RAI teams | "We have a training program" | Competency matrix, team assignments |
| **Improvement** | Regular maturity assessments; roadmap tracked | "We assess maturity annually" | Assessment reports, roadmap |

**Typical Organization Profile**: Established organizations with mature AI practices. ~20% of organizations.

#### Level 4: Managed (Quantitatively Managed)

| Dimension | Characteristic | Anti-Pattern | Evidence of Level |
|-----------|----------------|--------------|-------------------|
| **Governance** | Integrated into enterprise GRC; board reporting | "We report to the board but they don't act" | Board meeting minutes |
| **Strategy** | Value realization measured; portfolio optimized | "We measure value but don't optimize" | Value dashboards |
| **Risk** | Predictive risk modeling; automated monitoring | "We predict risks but don't automate response" | Risk models, automated alerts |
| **Ethics** | Continuous fairness monitoring; explainability automated | "We monitor fairness but don't automate" | Fairness dashboards |
| **Data** | Predictive quality; automated lineage and provenance | "We predict data quality issues" | Predictive quality models |
| **Security** | AI red teaming; adversarial robustness; zero-trust agents | "We red team our AI systems" | Red team reports |
| **Agents** | Dynamic credential management; behavioral baselines | "We manage agent credentials dynamically" | Credential rotation logs |
| **Monitoring** | Real-time anomaly detection; automated response | "We detect anomalies in real-time" | Anomaly detection metrics |
| **People** | AI champions network; culture metrics tracked | "We have AI champions" | Champion network, culture surveys |
| **Improvement** | Metrics-driven optimization; benchmarking | "We benchmark against peers" | Benchmark reports |

**Typical Organization Profile**: Industry leaders with mature AI governance. ~8% of organizations.

#### Level 5: Optimizing (Leading)

| Dimension | Characteristic | Anti-Pattern | Evidence of Level |
|-----------|----------------|--------------|-------------------|
| **Governance** | Competitive advantage; industry leadership | "Our governance is our moat" | Industry awards, speaking engagements |
| **Strategy** | AI-native business model; ecosystem orchestration | "AI is our business model" | Business model documentation |
| **Risk** | Predictive risk intelligence; self-healing systems | "Our systems prevent risks automatically" | Self-healing incident logs |
| **Ethics** | Proactive ethical innovation; societal impact leadership | "We lead on ethical AI" | Published research, standards contributions |
| **Data** | Self-optimizing pipelines; federated governance | "Our data pipelines self-optimize" | Self-optimization metrics |
| **Security** | Autonomous threat response; predictive defense | "Our security responds autonomously" | Autonomous response logs |
| **Agents** | Self-governing agents with verified autonomy | "Our agents govern themselves" | Agent governance logs |
| **Monitoring** | Predictive operations; cognitive incident management | "We predict incidents before they happen" | Predictive incident metrics |
| **People** | AI-fluent organization; continuous learning culture | "Everyone is AI-fluent" | Culture assessment results |
| **Improvement** | Innovation-driven; standards contributions | "We drive industry standards" | Standards body participation |

**Typical Organization Profile**: Top-tier industry leaders. ~2% of organizations.

### 3.2 Level Transition Criteria

To advance from Level N to Level N+1, an organization must meet ALL of:

| Criterion | Requirement | Verification |
|-----------|-------------|--------------|
| **Score threshold** | Average score ≥ N+1 threshold | Automated scoring |
| **Coverage** | ≥80% of sub-dimensions at Level N+1 | Sub-dimension analysis |
| **No critical gaps** | No sub-dimension at Level < N | Gap analysis |
| **Evidence** | All claims supported by evidence | Evidence review |
| **Outcome validation** | Business metrics consistent with level | Outcome metric review |
| **Sustainability** | Practices documented and repeatable | Process documentation review |

### 3.3 Level-Specific Artifacts

| Level | Required Artifacts | Optional Artifacts |
|-------|--------------------|--------------------|
| **1** | None (absence is the evidence) | Informal notes, spreadsheets |
| **2** | Draft policies, risk register, training materials | Process diagrams, inventories |
| **3** | Approved policies, GRC tool records, metrics dashboards | Committee charters, competency frameworks |
| **4** | Board reports, predictive models, red team reports | Benchmark reports, value dashboards |
| **5** | Industry contributions, self-healing logs, innovation metrics | Published research, standards contributions |

---

## 4. Improvement Roadmap Template

### 4.1 Roadmap Structure

Each improvement initiative follows a structured template:

```yaml
initiative:
  id: "IMP-[YEAR]-[NNN]"
  title: "[Action-oriented title]"
  domain: "[Pillar.Domain.Sub-dimension]"
  current_level: N
  target_level: N+1
  priority: P1|P2|P3|P4
  
  business_case:
    problem_statement: "[Current state description]"
    risk_if_not_addressed: "[Consequence of inaction]"
    expected_outcome: "[Target state description]"
    business_value: "[Quantified value if possible]"
  
  scope:
    in_scope: "[What is included]"
    out_of_scope: "[What is excluded]"
    dependencies: "[Prerequisite initiatives]"
    constraints: "[Budget, resources, timeline]"
  
  workstreams:
    - name: "[Workstream name]"
      activities:
        - description: "[Activity description]"
          owner: "[Role]"
          effort: "[Person-weeks]"
          duration: "[Weeks]"
          deliverable: "[Output artifact]"
          dependencies: "[Prior activities]"
      milestones:
        - name: "[Milestone name]"
          date: "[Target date]"
          success_criteria: "[Measurable criteria]"
  
  resources:
    personnel:
      - role: "[Role]"
        allocation: "[FTE]"
        skills: "[Required skills]"
    tools:
      - name: "[Tool name]"
        purpose: "[Use case]"
        cost: "[License/usage cost]"
    budget:
      total: "[Total cost]"
      breakdown:
        personnel: "[Amount]"
        tools: "[Amount]"
        training: "[Amount]"
        other: "[Amount]"
  
  success_metrics:
    - metric: "[Metric name]"
      baseline: "[Current value]"
      target: "[Target value]"
      measurement: "[How measured]"
  
  risks:
    - risk: "[Risk description]"
      likelihood: High|Medium|Low
      impact: High|Medium|Low
      mitigation: "[Mitigation strategy]"
  
  approval:
    sponsor: "[Executive sponsor]"
    date: "[Approval date]"
    status: Draft|Approved|In Progress|Completed
```

### 4.2 Prioritization Algorithm

Initiatives are prioritized using a multi-factor scoring model:

```
Priority Score = (Risk_Score × 0.35) + (Value_Score × 0.30) + (Effort_Score × 0.20) + (Dependency_Score × 0.15)

Where:
- Risk_Score (1-5): Higher = more critical to address
- Value_Score (1-5): Higher = more business value
- Effort_Score (1-5): Higher = less effort (inverted)
- Dependency_Score (1-5): Higher = unblocks more initiatives

Priority Bands:
- P1 (Critical): Score ≥ 4.0 → 0-3 months
- P2 (High): Score 3.0-3.9 → 3-6 months
- P3 (Medium): Score 2.0-2.9 → 6-12 months
- P4 (Low): Score < 2.0 → 12-18 months
```

### 4.3 Level 1 → 2 Roadmap (Detailed)

| # | Initiative | Domain | Priority | Effort (pw) | Duration | Dependencies | Success Metric |
|---|-------------|--------|----------|-------------|----------|--------------|----------------|
| 1 | Draft AI governance policy | 1.1 | P1 | 2 | 4 weeks | None | Policy approved |
| 2 | Establish AI governance body | 1.1 | P1 | 1 | 4 weeks | #1 | Body chartered |
| 3 | Create AI system inventory | 1.1 | P1 | 4 | 8 weeks | None | 100% systems inventoried |
| 4 | Develop AI strategy document | 1.2 | P1 | 3 | 6 weeks | #1 | Strategy approved |
| 5 | Create AI risk register | 1.3 | P1 | 2 | 4 weeks | #3 | Risk register populated |
| 6 | Document fairness guidelines | 2.1 | P2 | 2 | 4 weeks | #1 | Guidelines published |
| 7 | Conduct privacy impact assessment | 2.2 | P1 | 3 | 6 weeks | #3 | PIA completed for high-risk |
| 8 | Define human oversight requirements | 2.3 | P1 | 2 | 4 weeks | #1 | Oversight requirements documented |
| 9 | Define data quality metrics | 3.1 | P2 | 3 | 6 weeks | #3 | Metrics defined for critical data |
| 10 | Conduct AI threat modeling | 3.2 | P1 | 3 | 6 weeks | #3 | Threat model completed |
| 11 | Create agent inventory | 3.3 | P1 | 4 | 8 weeks | None | 100% agents identified |
| 12 | Implement basic runtime guardrails | 3.4 | P2 | 4 | 8 weeks | #11 | Guardrails deployed |
| 13 | Develop AI incident response plan | 4.1 | P1 | 2 | 4 weeks | #3 | IR plan documented |
| 14 | Launch AI literacy training | 4.2 | P2 | 4 | 8 weeks | #1 | Training program launched |
| 15 | Establish CI process | 4.3 | P3 | 2 | 4 weeks | #1 | CI process documented |

**Total Effort**: 42 person-weeks  
**Total Duration**: 8 months (with parallel execution)  
**Critical Path**: #1 → #4 → #5 → #13

### 4.4 Level 2 → 3 Roadmap (Detailed)

| # | Initiative | Domain | Priority | Effort (pw) | Duration | Dependencies | Success Metric |
|---|-------------|--------|----------|-------------|----------|--------------|----------------|
| 1 | Integrate governance into enterprise GRC | 1.1 | P2 | 6 | 12 weeks | L2 complete | GRC integration live |
| 2 | Implement automated AI discovery | 1.1 | P3 | 8 | 16 weeks | #1 | Discovery automated |
| 3 | Implement AI portfolio management | 1.2 | P2 | 6 | 12 weeks | L2 complete | Portfolio process live |
| 4 | Implement quantitative risk assessment | 1.3 | P2 | 6 | 12 weeks | L2 complete | Risk scores automated |
| 5 | Establish ethics review board | 2.1 | P2 | 4 | 8 weeks | L2 complete | Board operational |
| 6 | Implement systematic bias testing | 2.1 | P2 | 8 | 16 weeks | #5 | Bias testing in CI/CD |
| 7 | Implement privacy by design in SDLC | 2.2 | P2 | 8 | 16 weeks | L2 complete | Privacy gates in SDLC |
| 8 | Implement automated approval gates | 2.3 | P3 | 8 | 16 weeks | L2 complete | Gates automated |
| 9 | Implement enterprise data lineage | 3.1 | P3 | 10 | 20 weeks | L2 complete | Lineage tracked for all AI data |
| 10 | Integrate AI security into SDLC | 3.2 | P2 | 8 | 16 weeks | L2 complete | Security gates in SDLC |
| 11 | Implement agent identity lifecycle | 3.3 | P2 | 8 | 16 weeks | L2 complete | Lifecycle automated |
| 12 | Implement real-time anomaly detection | 3.4 | P3 | 10 | 20 weeks | L2 complete | Anomaly detection live |
| 13 | Implement automated monitoring | 4.1 | P2 | 6 | 12 weeks | L2 complete | Monitoring automated |
| 14 | Establish AI competency framework | 4.2 | P3 | 6 | 12 weeks | L2 complete | Framework published |
| 15 | Implement metrics-driven improvement | 4.3 | P3 | 6 | 12 weeks | L2 complete | Improvement metrics tracked |

**Total Effent**: 100 person-weeks  
**Total Duration**: 18 months (with parallel execution)  
**Critical Path**: L2 → #1 → #2 → #11 → #12

### 4.5 Level 3 → 4 Roadmap (Detailed)

| # | Initiative | Domain | Priority | Effort (pw) | Duration | Dependencies | Success Metric |
|---|-------------|--------|----------|-------------|----------|--------------|----------------|
| 1 | Board-level AI governance reporting | 1.1 | P3 | 6 | 12 weeks | L3 complete | Board dashboard live |
| 2 | Real-time value dashboards | 1.2 | P3 | 8 | 16 weeks | L3 complete | Value dashboards live |
| 3 | Predictive risk modeling | 1.3 | P3 | 10 | 20 weeks | L3 complete | Risk models deployed |
| 4 | Continuous fairness monitoring | 2.1 | P3 | 8 | 16 weeks | L3 complete | Fairness monitoring live |
| 5 | Automated privacy compliance | 2.2 | P3 | 8 | 16 weeks | L3 complete | Compliance automated |
| 6 | Adaptive human oversight | 2.3 | P4 | 10 | 20 weeks | L3 complete | Adaptive oversight live |
| 7 | Predictive data quality management | 3.1 | P4 | 10 | 20 weeks | L3 complete | Quality prediction live |
| 8 | AI red teaming program | 3.2 | P3 | 8 | 16 weeks | L3 complete | Red team operational |
| 9 | Dynamic credential management | 3.3 | P3 | 8 | 16 weeks | L3 complete | Credentials dynamic |
| 10 | Predictive behavior analysis | 3.4 | P4 | 10 | 20 weeks | L3 complete | Behavior prediction live |
| 11 | Automated incident response | 4.1 | P3 | 8 | 16 weeks | L3 complete | IR automated |
| 12 | AI champions network | 4.2 | P3 | 6 | 12 weeks | L3 complete | Network established |
| 13 | Benchmarking against peers | 4.3 | P4 | 6 | 12 weeks | L3 complete | Benchmark report published |

**Total Effort**: 106 person-weeks  
**Total Duration**: 24 months (with parallel execution)

### 4.6 Level 4 → 5 Roadmap (Detailed)

| # | Initiative | Domain | Priority | Effort (pw) | Duration | Dependencies | Success Metric |
|---|-------------|--------|----------|-------------|----------|--------------|----------------|
| 1 | Governance as competitive advantage | 1.1 | P4 | 12 | 24 weeks | L4 complete | Industry recognition |
| 2 | AI-native business model innovation | 1.2 | P4 | 12 | 24 weeks | L4 complete | New revenue streams |
| 3 | Self-healing risk management | 1.3 | P4 | 12 | 24 weeks | L4 complete | Self-healing deployed |
| 4 | Proactive ethical innovation | 2.1 | P4 | 12 | 24 weeks | L4 complete | Ethics innovation published |
| 5 | Privacy-preserving AI techniques | 2.2 | P4 | 12 | 24 weeks | L4 complete | Privacy-preserving AI deployed |
| 6 | Self-governing oversight | 2.3 | P4 | 12 | 24 weeks | L4 complete | Self-governing oversight live |
| 7 | Self-optimizing data pipelines | 3.1 | P4 | 12 | 24 weeks | L4 complete | Pipelines self-optimize |
| 8 | Autonomous threat response | 3.2 | P4 | 12 | 24 weeks | L4 complete | Threat response autonomous |
| 9 | Self-sovereign agent identities | 3.3 | P4 | 12 | 24 weeks | L4 complete | Self-sovereign identities deployed |
| 10 | Self-governing agent behaviors | 3.4 | P4 | 12 | 24 weeks | L4 complete | Self-governing behaviors live |
| 11 | Predictive operations | 4.1 | P4 | 12 | 24 weeks | L4 complete | Predictive ops live |
| 12 | AI-fluent organizational culture | 4.2 | P4 | 12 | 24 weeks | L4 complete | Culture metrics at target |
| 13 | Drive industry standards | 4.3 | P4 | 12 | 24 weeks | L4 complete | Standards contributions |

**Total Effort**: 156 person-weeks  
**Total Duration**: 36 months (with parallel execution)

### 4.7 Quick Wins Catalog

High-impact, low-effort actions that can be completed in 0-3 months:

| # | Action | Domain | Effort | Impact | Quick Win Because |
|---|--------|--------|--------|--------|-------------------|
| 1 | Draft AI governance policy | 1.1 | 2 weeks | High | Template available, minimal stakeholder input |
| 2 | Establish AI governance body | 1.1 | 2 weeks | High | Can be done via executive appointment |
| 3 | Create AI system inventory | 1.1 | 4 weeks | High | Automated discovery tools available |
| 4 | Create AI risk register | 1.3 | 2 weeks | High | Template available, risk workshops can be rapid |
| 5 | Define human oversight requirements | 2.3 | 2 weeks | High | Policy decision, minimal implementation |
| 6 | Create agent inventory | 3.3 | 4 weeks | High | Automated discovery tools available |
| 7 | Develop AI incident response plan | 4.1 | 2 weeks | High | Template available, tabletop exercise |
| 8 | Launch AI literacy training | 4.2 | 4 weeks | Medium | Online courses available |
| 9 | Implement basic logging | 4.1 | 2 weeks | Medium | Open-source tools available |
| 10 | Create data quality checklist | 3.1 | 2 weeks | Medium | Template available |

---

## 5. Benchmark Data

### 5.1 Industry Maturity Distribution

Based on CSA/Google Cloud 2025 survey, AAGMM research, and Gartner 2024 data:

| Level | % of Organizations | Cumulative | Typical Characteristics |
|-------|-------------------|------------|------------------------|
| **1 - Initial** | ~40% | 40% | No formal governance, shadow AI |
| **2 - Developing** | ~30% | 70% | Emerging practices, department-level |
| **3 - Defined** | ~20% | 90% | Organization-wide practices |
| **4 - Managed** | ~8% | 98% | Quantitative management |
| **5 - Optimizing** | ~2% | 100% | Industry leadership |

### 5.2 Domain-Level Benchmark Scores

Average maturity scores by domain (industry aggregate):

| Domain | Mean Score | Std Dev | P25 | P50 | P75 | P90 |
|--------|------------|---------|-----|-----|-----|-----|
| 1.1 AI Governance Framework | 2.1 | 0.8 | 1.4 | 2.0 | 2.8 | 3.6 |
| 1.2 AI Strategy & Value | 2.3 | 0.9 | 1.5 | 2.2 | 3.0 | 3.8 |
| 1.3 Risk & Compliance | 2.0 | 0.8 | 1.3 | 1.9 | 2.6 | 3.4 |
| 2.1 Fairness & Transparency | 1.8 | 0.7 | 1.2 | 1.7 | 2.3 | 3.0 |
| 2.2 Privacy & Data Protection | 2.2 | 0.9 | 1.4 | 2.1 | 2.9 | 3.7 |
| 2.3 Human Oversight | 1.9 | 0.8 | 1.2 | 1.8 | 2.5 | 3.2 |
| 3.1 Data Governance | 2.4 | 0.9 | 1.6 | 2.3 | 3.1 | 3.9 |
| 3.2 Model & Platform Security | 2.0 | 0.8 | 1.3 | 1.9 | 2.6 | 3.4 |
| 3.3 Agent Identity & Access | 1.5 | 0.7 | 1.0 | 1.4 | 1.9 | 2.6 |
| 3.4 Runtime Behavioral Controls | 1.4 | 0.6 | 1.0 | 1.3 | 1.8 | 2.4 |
| 4.1 Monitoring & Incident Response | 2.1 | 0.8 | 1.4 | 2.0 | 2.7 | 3.5 |
| 4.2 Workforce & Readiness | 2.3 | 0.9 | 1.5 | 2.2 | 3.0 | 3.8 |
| 4.3 Continuous Improvement | 1.9 | 0.8 | 1.2 | 1.8 | 2.5 | 3.2 |

**Key Observations**:
- Agent-specific domains (3.3, 3.4) have the lowest maturity — confirming the gap U-AIGMM addresses
- Data Governance (3.1) has the highest maturity — reflecting existing data governance investments
- Ethics domains (2.1, 2.3) lag behind — indicating need for focused improvement

### 5.3 Industry-Specific Benchmarks

#### Financial Services

| Domain | Mean | vs. Aggregate | Key Driver |
|--------|------|---------------|------------|
| 1.1 Governance | 2.6 | +0.5 | Regulatory pressure |
| 1.3 Risk & Compliance | 2.5 | +0.5 | Regulatory pressure |
| 2.2 Privacy | 2.7 | +0.5 | GDPR/CCPA compliance |
| 3.2 Security | 2.4 | +0.4 | Security investments |
| 3.3 Agent Identity | 1.7 | +0.2 | Emerging focus |
| 3.4 Runtime Controls | 1.6 | +0.2 | Emerging focus |

#### Healthcare

| Domain | Mean | vs. Aggregate | Key Driver |
|--------|------|---------------|------------|
| 1.1 Governance | 2.4 | +0.3 | FDA/EMA guidance |
| 2.2 Privacy | 2.8 | +0.6 | HIPAA compliance |
| 2.3 Human Oversight | 2.3 | +0.4 | Clinical safety |
| 3.1 Data Governance | 2.6 | +0.2 | Data quality focus |
| 3.3 Agent Identity | 1.5 | 0.0 | Nascent |
| 3.4 Runtime Controls | 1.4 | 0.0 | Nascent |

#### Technology

| Domain | Mean | vs. Aggregate | Key Driver |
|--------|------|---------------|------------|
| 1.2 Strategy | 2.8 | +0.5 | AI-first business models |
| 3.3 Agent Identity | 1.9 | +0.4 | Agent-native development |
| 3.4 Runtime Controls | 1.8 | +0.4 | Agent-native development |
| 4.1 Monitoring | 2.5 | +0.4 | DevOps maturity |
| 4.3 Continuous Improvement | 2.3 | +0.4 | Agile culture |

#### Manufacturing

| Domain | Mean | vs. Aggregate | Key Driver |
|--------|------|---------------|------------|
| 1.1 Governance | 1.8 | -0.3 | Traditional governance |
| 3.1 Data Governance | 2.2 | -0.2 | OT/IT separation |
| 3.2 Security | 1.8 | -0.2 | OT security focus |
| 4.2 Workforce | 2.0 | -0.3 | Skills gap |
| 3.3 Agent Identity | 1.3 | -0.2 | Nascent |
| 3.4 Runtime Controls | 1.2 | -0.2 | Nascent |

### 5.4 Organization Size Benchmarks

| Size | Overall Mean | Pillar 1 | Pillar 2 | Pillar 3 | Pillar 4 |
|------|--------------|----------|----------|----------|----------|
| <100 employees | 1.8 | 1.9 | 1.6 | 1.7 | 2.0 |
| 100-500 | 2.1 | 2.2 | 1.9 | 2.0 | 2.3 |
| 500-1000 | 2.4 | 2.5 | 2.2 | 2.3 | 2.6 |
| 1000-5000 | 2.6 | 2.7 | 2.4 | 2.5 | 2.8 |
| 5000-10000 | 2.8 | 2.9 | 2.6 | 2.7 | 3.0 |
| >10000 | 3.0 | 3.1 | 2.8 | 2.9 | 3.2 |

**Key Insight**: Larger organizations have higher maturity, but the gap is smallest in Pillar 4 (Operations) and largest in Pillar 2 (Responsible AI), suggesting that ethics/responsible AI is a universal challenge.

### 5.5 Maturity Progression Velocity

Average time to advance one level (by starting level):

| From → To | Average Time | Fastest 10% | Slowest 10% | Key Accelerators |
|-----------|--------------|-------------|-------------|-----------------|
| L1 → L2 | 12 months | 6 months | 24 months | Executive sponsorship, quick wins |
| L2 → L3 | 18 months | 12 months | 36 months | Dedicated team, tooling |
| L3 → L4 | 24 months | 18 months | 48 months | Quantitative culture, automation |
| L4 → L5 | 36 months | 24 months | 60 months | Innovation culture, industry leadership |

### 5.6 Benchmark Data Sources

| Source | Year | Sample | Methodology | Access |
|--------|------|--------|-------------|--------|
| CSA/Google Cloud AI Security Survey | 2025 | 2,500+ | Online survey | Public report |
| AAGMM Research | 2026 | 500+ | Simulation-validated | arXiv:2604.16338 |
| Gartner AI MM | 2024 | 1,200+ | Online assessment | Client access |
| MITRE AI MM | 2023 | 800+ | Multiple-choice | Public tool |
| Microsoft RAI MM | 2023 | 600+ | Workshop-based | Research paper |
| OWASP AIMA | 2025 | 400+ | Yes/no worksheets | Open source |
| CMMI AIM | 2026 | 200+ | Formal appraisal | Licensed |

---

## 6. Assessment Automation

### 6.1 Automation Architecture

The U-AIGMM assessment can be automated at multiple levels:

```
┌─────────────────────────────────────────────────────────────┐
│                 ASSESSMENT AUTOMATION STACK                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LAYER 4: DECISION SUPPORT                          │   │
│  │  • Maturity trajectory prediction                   │   │
│  │  • Investment optimization                          │   │
│  │  • Risk forecasting                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ▲                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LAYER 3: ANALYTICS & VISUALIZATION                 │   │
│  │  • Heat map generation                              │   │
│  │  • Trend analysis                                   │   │
│  │  • Benchmark comparison                             │   │
│  │  • Gap analysis                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ▲                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LAYER 2: SCORING ENGINE                            │   │
│  │  • Hierarchical score calculation                   │   │
│  │  • Stream weighting                                 │   │
│  │  • Partial credit                                   │   │
│  │  • Confidence intervals                             │   │
│  │  • Perception divergence                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ▲                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LAYER 1: DATA COLLECTION                           │   │
│  │  • Questionnaire delivery                           │   │
│  │  • Evidence upload                                  │   │
│  │  • API integrations                                 │   │
│  │  • Automated evidence collection                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ▲                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LAYER 0: DATA SOURCES                              │   │
│  │  • GRC tools (ServiceNow, Archer, etc.)             │   │
│  │  • Cloud platforms (AWS, Azure, GCP)                │   │
│  │  • CI/CD pipelines (Jenkins, GitHub Actions)        │   │
│  │  • Monitoring tools (Datadog, Splunk)               │   │
│  │  • Agent platforms (LangChain, CrewAI, etc.)        │   │
│  │  • Identity providers (Okta, Azure AD)              │   │
│  │  • Data catalogs (Collibra, Alation)                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Automated Evidence Collection

#### 6.2.1 Evidence Sources by Domain

| Domain | Automated Source | Evidence Type | Collection Method |
|--------|-----------------|---------------|-------------------|
| 1.1 Governance | GRC tool | Policy documents, committee records | API query |
| 1.2 Strategy | Project portfolio tool | Strategy docs, value metrics | API query |
| 1.3 Risk | Risk register | Risk records, assessment scores | API query |
| 2.1 Fairness | ML platform | Bias test results, fairness metrics | API query |
| 2.2 Privacy | Privacy tool | DPIA records, consent logs | API query |
| 2.3 Oversight | Approval system | Approval logs, escalation records | API query |
| 3.1 Data | Data catalog | Lineage records, quality scores | API query |
| 3.2 Security | Security tool | Vulnerability scans, test results | API query |
| 3.3 Agent Identity | Identity provider | Agent credentials, access logs | API query |
| 3.4 Runtime Controls | Monitoring tool | Guardrail logs, anomaly alerts | API query |
| 4.1 Monitoring | Incident management | Incident records, response times | API query |
| 4.2 Workforce | LMS/HR system | Training records, competency assessments | API query |
| 4.3 Improvement | CI tool | Improvement metrics, assessment history | API query |

#### 6.2.2 Evidence Collection API

```python
# Pseudocode for automated evidence collection

class EvidenceCollector:
    def __init__(self, config):
        self.sources = {
            'grc': GRCConnector(config['grc']),
            'cloud': CloudConnector(config['cloud']),
            'cicd': CICDConnector(config['cicd']),
            'monitoring': MonitoringConnector(config['monitoring']),
            'identity': IdentityConnector(config['identity']),
            'data_catalog': DataCatalogConnector(config['data_catalog']),
        }
    
    def collect_domain_evidence(self, domain_id, start_date, end_date):
        """Collect all available evidence for a domain."""
        evidence = []
        
        for source_name, source in self.sources.items():
            try:
                source_evidence = source.query(
                    domain=domain_id,
                    start_date=start_date,
                    end_date=end_date
                )
                evidence.extend(source_evidence)
            except Exception as e:
                log.warning(f"Failed to collect from {source_name}: {e}")
        
        return self.deduplicate(evidence)
    
    def calculate_evidence_coverage(self, domain_id, required_evidence):
        """Calculate what percentage of required evidence is available."""
        available = self.collect_domain_evidence(domain_id)
        coverage = {}
        
        for evidence_type, required_count in required_evidence.items():
            available_count = len([e for e in available if e.type == evidence_type])
            coverage[evidence_type] = min(available_count / required_count, 1.0)
        
        return coverage
```

### 6.3 Continuous Assessment Model

Instead of point-in-time assessments, the U-AIGMM supports continuous assessment:

#### 6.3.1 Continuous Assessment Cycle

```
┌─────────────────────────────────────────────────────────────┐
│              CONTINUOUS ASSESSMENT CYCLE                     │
│                                                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐  │
│  │ COLLECT │──▶│ SCORE   │──▶│ ANALYZE │──▶│ REPORT  │  │
│  │         │   │         │   │         │   │         │  │
│  │Continuous│  │ Daily   │   │ Weekly  │   │ Monthly │  │
│  │(automated)│ │(automated)│ │(automated)│ │(automated)│ │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘  │
│       ▲                                            │      │
│       └────────────────────────────────────────────┘      │
│                    FEEDBACK LOOP                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 6.3.2 Continuous Assessment Metrics

| Metric | Collection Frequency | Scoring Frequency | Alert Threshold |
|--------|---------------------|-------------------|-----------------|
| AI Inventory Coverage | Real-time | Daily | <95% |
| Policy Violation Rate | Real-time | Daily | >5/1K/month |
| Agent Identity Coverage | Real-time | Daily | <100% |
| Model Drift Index | Hourly | Daily | >0.2 |
| Task Success Rate | Real-time | Daily | <90% |
| Harmful Output Rate | Real-time | Daily | >0.1% |
| Human Override Rate | Real-time | Weekly | Trending up |
| Incident MTTR | Per incident | Weekly | >24h |
| Risk Treatment Coverage | Weekly | Weekly | <100% |
| Corrective Action Closure | Weekly | Weekly | <90% in SLA |

### 6.4 Automated Scoring Engine

#### 6.4.1 Scoring Engine Architecture

```python
class MaturityScoringEngine:
    def __init__(self, config):
        self.weights = config.get('weights', DEFAULT_WEIGHTS)
        self.stream_weights = config.get('stream_weights', {'A': 0.6, 'B': 0.4})
        self.thresholds = config.get('thresholds', DEFAULT_THRESHOLDS)
    
    def score_question(self, question_id, response, evidence=None):
        """Score a single question response."""
        base_score = self._map_response_to_score(response)
        
        if evidence:
            evidence_bonus = self._calculate_evidence_bonus(evidence)
            base_score = min(base_score + evidence_bonus, 5.0)
        
        return base_score
    
    def score_sub_dimension(self, sub_dimension_id, question_scores):
        """Score a sub-dimension from question scores."""
        stream_a_scores = [s for s in question_scores if s.stream == 'A']
        stream_b_scores = [s for s in question_scores if s.stream == 'B']
        
        stream_a_avg = sum(stream_a_scores) / len(stream_a_scores) if stream_a_scores else 0
        stream_b_avg = sum(stream_b_scores) / len(stream_b_scores) if stream_b_scores else 0
        
        weighted_score = (
            stream_a_avg * self.stream_weights['A'] +
            stream_b_avg * self.stream_weights['B']
        )
        
        return {
            'score': weighted_score,
            'stream_a': stream_a_avg,
            'stream_b': stream_b_avg,
            'partial_credit': self._calculate_partial_credit(question_scores)
        }
    
    def score_domain(self, domain_id, sub_dimension_scores):
        """Score a domain from sub-dimension scores."""
        return sum(s['score'] for s in sub_dimension_scores) / len(sub_dimension_scores)
    
    def score_pillar(self, pillar_id, domain_scores):
        """Score a pillar from domain scores."""
        return sum(domain_scores) / len(domain_scores)
    
    def score_overall(self, pillar_scores):
        """Calculate overall maturity score."""
        return sum(pillar_scores) / len(pillar_scores)
    
    def assign_level(self, score, method='mixed'):
        """Assign maturity level based on score."""
        if method == 'threshold':
            return self._threshold_based_level(score)
        elif method == 'cumulative':
            return self._cumulative_gate_level(score)
        else:  # mixed
            threshold_level = self._threshold_based_level(score)
            cumulative_level = self._cumulative_gate_level(score)
            return min(threshold_level, cumulative_level)
    
    def calculate_divergence(self, rater_scores):
        """Calculate perception divergence between raters."""
        if len(rater_scores) < 2:
            return 0
        
        max_divergence = 0
        for i in range(len(rater_scores)):
            for j in range(i + 1, len(rater_scores)):
                divergence = abs(rater_scores[i] - rater_scores[j])
                max_divergence = max(max_divergence, divergence)
        
        return max_divergence
```

### 6.5 Integration with GRC_Claw CI Engine

The assessment automation integrates with the GRC_Claw CI Engine (from grc-claw-ci-framework.md):

| CI Engine Component | Assessment Integration | Data Flow |
|---------------------|----------------------|-----------|
| **KPI Dashboard** | Maturity scores as KPIs | Assessment → KPI Dashboard |
| **Feedback Loop** | Assessment triggers improvement | Assessment → 8-Stage Loop |
| **Maturity Staging** | Continuous level tracking | Assessment → Staging |
| **Automated Evidence** | Evidence collection | CI Engine → Assessment |
| **Self-Healing** | Auto-remediation of gaps | Assessment → CI Engine |

### 6.6 Assessment Automation Tools

| Tool | Purpose | Integration | Tier |
|------|---------|-------------|------|
| **U-AIGMM Assessment Platform** | Questionnaire, scoring, reporting | Web-based | 1-3 |
| **Evidence Collector** | Automated evidence gathering | API-based | 2-3 |
| **Scoring Engine** | Hierarchical score calculation | Library/API | 1-3 |
| **Heat Map Generator** | Visualization | Library | 1-3 |
| **Benchmark Comparison** | Industry comparison | API | 2-3 |
| **Roadmap Generator** | Improvement planning | Tool | 2-3 |
| **Continuous Monitor** | Ongoing assessment | Service | 3 |

### 6.7 Automation Maturity Levels

| Level | Description | Capabilities | Human Role |
|-------|-------------|--------------|------------|
| **0 - Manual** | Spreadsheet-based assessment | Basic scoring | Full manual |
| **1 - Assisted** | Online questionnaire with auto-scoring | Auto-scoring, basic heat map | Review and validate |
| **2 - Semi-Automated** | Evidence collection + scoring | Auto-evidence, multi-rater, divergence | Facilitate and interpret |
| **3 - Automated** | Continuous assessment + predictive | Continuous monitoring, predictive analytics | Governance and strategy |
| **4 - Self-Assessing** | AI-driven assessment | Self-identifying gaps, auto-remediation | Oversight and approval |

---

## 7. Appendices

### Appendix A: Scoring Workbook Template

```
Sub-dimension Scoring Worksheet
===============================

Sub-dimension: [ID] [Name]
Assessor: [Name] [Role]
Date: [Date]

Stream A: Create & Promote
---------------------------
| # | Question | Response | Score | Evidence | Notes |
|---|----------|----------|-------|----------|-------|
| 1 |          |          |       |          |       |
| 2 |          |          |       |          |       |
| 3 |          |          |       |          |       |
|   |          |          |       |          |       |
| Stream A Average |          |       |          |       |

Stream B: Measure & Improve
---------------------------
| # | Question | Response | Score | Evidence | Notes |
|---|----------|----------|-------|----------|-------|
| 1 |          |          |       |          |       |
| 2 |          |          |       |          |       |
|   |          |          |       |          |       |
| Stream B Average |          |       |          |       |

Stream-Weighted Score = (A × 0.6) + (B × 0.4) = _____

Partial Credit Calculation:
- All Level N criteria met? [Y/N]
- Level N+1 criteria met: ___ of ___
- Partial Credit = N + (___/___) × 0.5 = _____

Final Sub-dimension Score: _____
Assigned Level: _____

Confidence: [High/Medium/Low]
Notes: _________________________________
```

### Appendix B: Heat Map Template

```
Maturity Heat Map
=================

Domain                     | L1  | L2  | L3  | L4  | L5  | Score | Level
---------------------------|-----|-----|-----|-----|-----|-------|------
1.1 AI Governance Framework|     |     |     |     |     |       |
1.2 AI Strategy & Value    |     |     |     |     |     |       |
1.3 Risk & Compliance      |     |     |     |     |     |       |
2.1 Fairness & Transparency|     |     |     |     |     |       |
2.2 Privacy & Data Protect |     |     |     |     |     |       |
2.3 Human Oversight        |     |     |     |     |     |       |
3.1 Data Governance        |     |     |     |     |     |       |
3.2 Model & Platform Sec   |     |     |     |     |     |       |
3.3 Agent Identity & Access|     |     |     |     |     |       |
3.4 Runtime Behavioral Ctrl |     |     |     |     |     |       |
4.1 Monitoring & Incident  |     |     |     |     |     |       |
4.2 Workforce & Readiness  |     |     |     |     |     |       |
4.3 Continuous Improvement |     |     |     |     |     |       |
---------------------------|-----|-----|-----|-----|-----|-------|------
Pillar 1 Average           |     |     |     |     |     |       |
Pillar 2 Average           |     |     |     |     |     |       |
Pillar 3 Average           |     |     |     |     |     |       |
Pillar 4 Average           |     |     |     |     |     |       |
---------------------------|-----|-----|-----|-----|-----|-------|------
OVERALL                    |     |     |     |     |     |       |

Color Coding:
■ Red (<2.0)  ■ Yellow (2.0-2.9)  ■ Light Green (3.0-3.9)  ■ Green (4.0+)
```

### Appendix C: Assessment Report Template

```
AI Governance Maturity Assessment Report
========================================

Executive Summary
-----------------
Overall Maturity Score: [X.X] / 5.0
Overall Maturity Level: [N] - [Level Name]
Assessment Date: [Date]
Assessment Tier: [1/2/3]
Scope: [Enterprise/Department]

Key Findings:
1. [Top strength]
2. [Top strength]
3. [Top gap]
4. [Top gap]
5. [Top gap]

Pillar Summary
--------------
| Pillar | Score | Level | vs. Benchmark | Trend |
|--------|-------|-------|---------------|-------|
| 1. Governance & Strategy | | | | |
| 2. Responsible AI & Ethics | | | | |
| 3. Technical Foundation | | | | |
| 4. Operations & Performance | | | | |

Domain Details
--------------
[For each domain:]
- Score: [X.X]
- Level: [N]
- vs. Benchmark: [+/-X.X]
- Top Gaps:
  1. [Gap]
  2. [Gap]
- Top Strengths:
  1. [Strength]
  2. [Strength]

Perception Divergence Analysis
------------------------------
| Sub-dimension | Rater A | Rater B | Divergence | Action |
|---------------|---------|---------|------------|--------|
|               |         |         |            |        |

Improvement Roadmap Summary
---------------------------
| Priority | Initiative | Domain | Effort | Duration | Dependencies |
|----------|------------|--------|--------|----------|--------------|
| P1 | | | | | |
| P2 | | | | | |
| P3 | | | | | |

Recommendations
---------------
1. [Top recommendation]
2. [Second recommendation]
3. [Third recommendation]

Next Assessment: [Date]
```

### Appendix D: Glossary of Assessment Terms

| Term | Definition |
|------|------------|
| **Assessment Tier** | Level of formality: 1 (self-assessment), 2 (facilitated), 3 (formal appraisal) |
| **Confidence Interval** | Statistical range indicating score reliability |
| **Cumulative Gate** | Level assignment method requiring all lower levels to be met |
| **Divergence** | Difference in scores between raters |
| **Evidence** | Artifact supporting a maturity claim |
| **Heat Map** | Visual representation of maturity scores across domains |
| **Multi-Rater** | Assessment by multiple evaluators with different perspectives |
| **Partial Credit** | Score between levels when some but not all criteria are met |
| **Perception Divergence Index (PDI)** | Average divergence across all sub-dimensions |
| **Stream A** | Create & Promote — establishing capabilities |
| **Stream B** | Measure & Improve — measuring effectiveness |
| **Sub-dimension** | Specific aspect within a domain |
| **Threshold-Based** | Level assignment based on score ranges |

### Appendix E: References

1. MITRE. (2023). *AI Maturity Model and Organizational Assessment Tool Guide*.
2. Vorvoreanu, M., et al. (2023). *Responsible AI Maturity Model*. Microsoft Research.
3. Gartner. (2024). *AI Maturity Model*. Gartner Research.
4. OWASP. (2025). *AI Maturity Assessment (AIMA) v1.0*.
5. CMMI Institute. (2026). *CMMI AIM: Artificial Intelligence Maturity*.
6. Acharya, V. (2026). *Agentic AI Governance Maturity Model (AAGMM)*. arXiv:2604.16338.
7. Cloud Security Alliance. (2026). *Agentic AI Governance Maturity Model (AGMM)*.
8. Cloud Security Alliance & Google Cloud. (2025). *State of AI Security and Governance Survey Report*.
9. ISO/IEC. (2023). *ISO/IEC 42001:2023*.
10. NIST. (2023). *AI Risk Management Framework (AI RMF 1.0)*.
11. GRC_Claw. (2026). *Unified Continuous Improvement Framework*.

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Research Team | Initial release |

---

*This document is licensed under CC BY-SA 4.0. You are free to share and adapt it with attribution.*
