# NIST AI RMF Deep-Dive: Implementation Landscape & ISO 42001 Mapping

**Prepared for:** GRC_Claw positioning as a bridge between NIST AI RMF and ISO 42001  
**Date:** October 2026  
**Sources:** NIST AI 100-1, NIST AI 600-1, NIST AI RMF Playbook, NIST-AIRC Crosswalks, ISO/IEC 42001:2023, practitioner implementations

---

## 1. NIST AI RMF 1.0 — Core Structure

**Published:** January 26, 2023 (NIST AI 100-1)  
**Status:** Voluntary, non-sector-specific, use-case-agnostic  
**Authority:** National Artificial Intelligence Initiative Act of 2020 (P.L. 116-283)

### 1.1 Trustworthy AI Characteristics (Section 3)

The AI RMF defines seven characteristics of trustworthy AI systems:

| # | Characteristic | Focus |
|---|---|---|
| 1 | Valid and Reliable | Accuracy, robustness, generalizability |
| 2 | Safe | Physical, psychological, environmental safety |
| 3 | Secure and Resilient | Cybersecurity, adversarial resilience |
| 4 | Accountable and Transparent | Auditability, explainability, documentation |
| 5 | Explainable and Interpretable | Human-understandable reasoning |
| 6 | Privacy-Enhanced | Data protection, confidentiality |
| 7 | Fair — with Harmful Bias Managed | Non-discrimination, equity |

### 1.2 The Four Core Functions

The AI RMF Core is organized into **4 functions → 19 categories → 72 subcategories**:

#### GOVERN (Cross-cutting, 6 categories, 17 subcategories)
*Policies, processes, procedures, and practices across the organization related to mapping, measuring, and managing AI risks.*

| Category | Focus |
|---|---|
| GOVERN 1 | Policies, processes, procedures, and practices are in place |
| GOVERN 2 | Roles, responsibilities, and lines of communication are documented |
| GOVERN 3 | Workforce diversity and interdisciplinary collaboration |
| GOVERN 4 | Organizational culture — critical thinking, safety-first mindset |
| GOVERN 5 | Feedback mechanisms from external stakeholders |
| GOVERN 6 | Third-party risk management |

**Key subcategories:** GV-1.1 (legal/regulatory compliance), GV-1.3 (risk tolerance), GV-2.1 (roles & responsibilities), GV-2.3 (executive accountability), GV-4.1 (safety culture), GV-6.1 (third-party IP risk)

#### MAP (5 categories, 16 subcategories)
*Establishes context to frame risks related to an AI system.*

| Category | Focus |
|---|---|
| MAP 1 | Intended purpose, context, laws, norms, settings |
| MAP 2 | AI system tasks, methods, knowledge limits |
| MAP 3 | Benefits, costs, scope, risk tolerance |
| MAP 4 | Third-party components, legal/IP risks |
| MAP 5 | Likelihood and magnitude of impacts |

**Key subcategories:** MP-1.1 (intended use documentation), MP-1.5 (risk tolerance), MP-2.2 (knowledge limits), MP-3.5 (human oversight), MP-5.1 (impact likelihood/magnitude)

#### MEASURE (4 categories, 22 subcategories)
*Analyzes, quantifies, or tracks enumerated risks.*

| Category | Focus |
|---|---|
| MEASURE 1 | Approaches and metrics for risk measurement |
| MEASURE 2 | Testing, evaluation, validation, verification (TEVV) |
| MEASURE 3 | Risk tracking, emergent risk identification |
| MEASURE 4 | Context-informed measurement with domain experts |

**Key subcategories:** MS-1.1 (metric selection), MS-2.3 (performance criteria), MS-2.5 (validity & reliability), MS-2.6 (safety evaluation), MS-2.7 (security & resilience), MS-2.11 (fairness & bias), MS-3.1 (emergent risk tracking)

#### MANAGE (4 categories, 17 subcategories)
*Acts on risks — implements controls and response procedures.*

| Category | Focus |
|---|---|
| MANAGE 1 | Risk treatment decisions (avoid, mitigate, transfer, accept) |
| MANAGE 2 | Resource allocation, sustaining value |
| MANAGE 3 | Third-party and pre-trained model monitoring |
| MANAGE 4 | Post-deployment monitoring, incident response, continual improvement |

**Key subcategories:** MG-1.1 (go/no-go decision), MG-1.3 (risk response planning), MG-1.4 (residual risk documentation), MG-2.4 (deactivation mechanisms), MG-4.1 (post-deployment monitoring), MG-4.3 (incident communication)

### 1.3 Implementation Tiers

NIST defines **4 Implementation Tiers** (adapted from NIST CSF):

| Tier | Name | Description |
|---|---|---|
| 1 | Partial | Ad-hoc, reactive, case-by-case |
| 2 | Risk-Informed | Risk management practices approved but not standardized |
| 3 | Repeatable | Formal policies, standardized across organization |
| 4 | Adaptive | Continuous improvement, real-time monitoring, automated response |

Tiers are **not maturity levels** — they are tools for internal communication and priority-setting. Organizations select the tier appropriate to their risk context.

### 1.4 AI RMF Playbook

- **Published:** March 30, 2023 (first complete version)
- **Purpose:** Suggested actions, references, and guidance for each of the 72 subcategories
- **Nature:** Voluntary, not a checklist — organizations borrow as many or few suggestions as apply
- **Structure:** Aligned to each subcategory within the four functions
- **Status:** Will be updated after AI RMF 1.0 is revised (revision underway per White House AI Action Plan)

---

## 2. NIST AI 600-1 — Generative AI Profile

**Published:** July 26, 2024  
**Authority:** Executive Order 14110, Section 4.1(a)(i)(A)  
**Status:** Voluntary companion profile to AI RMF 1.0

### 2.1 Purpose

AI 600-1 adapts the four-function framework to the specific characteristics of generative AI systems. It is **cumulative, not substitutive** — organizations implement AI RMF 1.0's ~72 outcomes as the baseline, then layer the GenAI Profile's additions on top.

### 2.2 Twelve GenAI Risk Categories

| # | Risk Category | Trustworthy AI Characteristics |
|---|---|---|
| 1 | CBRN Information or Capabilities | Safe, Explainable & Interpretable |
| 2 | Confabulation | Valid & Reliable, Safe |
| 3 | Dangerous, Violent, or Hateful Content | Safe |
| 4 | Data Privacy | Privacy-Enhanced |
| 5 | Environmental Impacts | Safe |
| 6 | Harmful Bias or Homogenization | Fair |
| 7 | Human-AI Configuration | Safe, Accountable & Transparent |
| 8 | Information Integrity | Valid & Reliable, Accountable & Transparent |
| 9 | Information Security | Secure & Resilient |
| 10 | Intellectual Property | Accountable & Transparent |
| 11 | Obscene, Degrading, and/or Abusive Content | Safe |
| 12 | Value Chain and Component Integration | Accountable & Transparent, Secure & Resilient |

### 2.3 Suggested Actions

- **200+ suggested actions** organized across the four RMF functions
- Each action tagged with: Action ID (e.g., GV-1.1-001), GAI Risks, AI Actor Tasks
- Actions differentiated by actor type: **developer**, **deployer**, or **user**
- Four primary considerations from the GAI Public Working Group:
  1. **Governance** — authority, not just policy
  2. **Content Provenance** — traceability of outputs
  3. **Pre-deployment Testing** — use-case-specific evaluation
  4. **Incident Disclosure** — AI failures as reportable events

### 2.4 Key GenAI-Specific Additions

- **Content provenance infrastructure** — metadata, watermarking for AI-generated content
- **Incident response for emergent harms** — rapid content filter updates, user communication
- **User reporting mechanisms** — for harmful or incorrect outputs
- **Confabulation policies** — acceptable use cases with documented rationale
- **Autonomy level documentation** — which actions require human confirmation
- **Quarterly red-teaming** — for prompt injection and jailbreaking
- **Third-party AI component register** — foundation models, plugins, tool endpoints

### 2.5 Legal and Regulatory Citations

Though voluntary, AI 600-1 is cited in:
- US federal procurement requirements
- Colorado SB 24-205 safe harbor provisions
- Executive Order 14110

This creates a **de facto obligation** for organizations with US-facing exposure.

---

## 3. NIST AI RMF ↔ ISO/IEC 42001 Mapping

### 3.1 Structural Comparison

| Dimension | NIST AI RMF 1.0 | ISO/IEC 42001:2023 |
|---|---|---|
| **Type** | Voluntary framework | Certifiable management system standard |
| **Structure** | 4 functions, 19 categories, 72 subcategories | 10 clauses (4-10 normative), 38 Annex A controls |
| **Approach** | Iterative, lifecycle-centric, socio-technical | Top-down, PDCA (Plan-Do-Check-Act), Annex SL |
| **Certification** | None — self-attestation only | Third-party accredited certification (ISO 17021-1) |
| **Focus** | Risk identification, measurement, treatment | Management system establishment, maintenance, improvement |
| **AI Role** | AI actors (developer, deployer, user) | AI provider, AI producer, AI customer (ISO 22989) |
| **Key Artifact** | AI Risk Profile | Statement of Applicability (SoA) |
| **Geographic** | US-origin, international alignment | International standard |

### 3.2 Clause-by-Clause Mapping (from NIST Crosswalk)

#### ISO 42001 Clause 4 (Context) → NIST AI RMF
| ISO Sub-clause | NIST Mapping |
|---|---|
| 4.1 Understanding organization & context | GV-1.1, MP-1.3, MP-1.4 |
| 4.2 Interested parties | GV-5.1, MP-5.2 |
| 4.3 Scope of AIMS | MP-3.3 |
| 4.4 AI management system | GV-1.2, GV-1.4 |

#### ISO 42001 Clause 5 (Leadership) → NIST AI RMF
| ISO Sub-clause | NIST Mapping |
|---|---|
| 5.1 Leadership and commitment | GV-2.3, MP-1.4 |
| 5.2 AI Policy | GV-1.1, GV-1.2, MP-1.3 |
| 5.3 Roles, responsibilities, authorities | GV-2.1, GV-3.2 |

#### ISO 42001 Clause 6 (Planning) → NIST AI RMF
| ISO Sub-clause | NIST Mapping |
|---|---|
| 6.1.2 AI risk assessment | GV-1.3, GV-1.4, MP-5.1, MS-1.1 |
| 6.1.3 AI risk treatment | GV-1.3, GV-1.4, MG-1.2, MG-1.3 |
| 6.1.4 AI system impact assessment | MP-1.1, MP-3.1, MP-3.2, MP-5.1 |
| 6.2 AI objectives | MP-1.3, MP-1.4 |

#### ISO 42001 Clause 7 (Support) → NIST AI RMF
| ISO Sub-clause | NIST Mapping |
|---|---|
| 7.1 Resources | GV-1.6, MG-2.1 |
| 7.2 Competence | GV-2.2, MP-1.2, MP-3.4 |
| 7.3 Awareness | MP-1.3 |
| 7.4 Communication | GV-4.2, GV-5.1 |
| 7.5 Documented information | MP-1.1, MP-2.3 |

#### ISO 42001 Clause 8 (Operation) → NIST AI RMF
| ISO Sub-clause | NIST Mapping |
|---|---|
| 8.1 Operational planning & control | MG-1.1, MG-1.3 |
| 8.2 AI risk assessment (execution) | MS-1.1, MS-1.2, MS-2.3, MS-2.5, MS-2.6 |
| 8.3 AI risk treatment (execution) | MG-1.2, MG-1.3, MG-2.2 |
| 8.4 AI system impact assessment (execution) | MP-3.1, MP-3.2, MP-5.1 |

#### ISO 42001 Clause 9 (Performance Evaluation) → NIST AI RMF
| ISO Sub-clause | NIST Mapping |
|---|---|
| 9.1 Monitoring, measurement, analysis, evaluation | MS-1.2, MS-2.4, MS-4.1, MS-4.2 |
| 9.2 Internal audit | MS-1.3 |
| 9.3 Management review | GV-2.3, MG-1.2, MG-4.2, MG-4.3 |

#### ISO 42001 Clause 10 (Improvement) → NIST AI RMF
| ISO Sub-clause | NIST Mapping |
|---|---|
| 10.1 Continual improvement | MS-3.2, MG-2.2, MG-4.2 |
| 10.2 Nonconformity and corrective action | MG-2.3 |

### 3.3 Annex A Control Mapping (Key Controls)

| ISO Annex A Control | NIST AI RMF Subcategories |
|---|---|
| A.2 AI Policies (3 controls) | GV-1.1, GV-1.2, GV-1.4 |
| A.3 Internal Organization (2 controls) | GV-2.1, GV-3.2 |
| A.4 Resources for AI Systems (5 controls) | GV-1.6, MG-2.1, MP-2.1 |
| A.5 Assessing Impacts of AI Systems (4 controls) | MP-1.1, MP-3.1, MP-3.2, MP-5.1 |
| A.6 AI System Lifecycle (9 controls) | MP-2.1, MP-2.2, MP-2.3, MS-2.5, MS-2.6, MG-2.4 |
| A.7 Data for AI Systems (5 controls) | MP-2.3, MS-2.3, MS-2.10 |
| A.8 Information for Interested Parties (4 controls) | GV-4.2, GV-5.1, MG-4.3 |
| A.9 Use of AI Systems (3 controls) | GV-3.2, MP-3.5, MG-2.4 |
| A.10 Third-Party & Customer Relationships (3 controls) | GV-6.1, GV-6.2, MG-3.1 |

### 3.4 Terminology Reconciliation

| ISO 42001 Term | NIST AI RMF Term |
|---|---|
| AI Management System (AIMS) | AI Risk Profile |
| Interested Party | Affected Community / AI Actor |
| AI Provider / Producer / Customer | AI Developer / Deployer / User |
| Statement of Applicability | Risk Treatment Plan |
| Nonconformity | Risk Event / Incident |
| Management Review | Executive Risk Review |

### 3.5 Complementary Relationship

**ISO 42001 provides:**
- Auditable, certifiable governance backbone (the "operating system")
- Mandatory documented policies, internal audit cycles, structured management reviews
- Third-party accreditation and surveillance audits
- Formal AI role determination (Clause 4.1)
- AI system impact assessment requirement (Clause 6.1.4/8.4) — no ISO 27001 equivalent

**NIST AI RMF provides:**
- Granular, context-sensitive risk identification and evaluation methodology (the "diagnostic layer")
- Socio-technical perspective on AI harm
- Trustworthiness characteristics taxonomy
- Iterative, lifecycle-centric risk management process
- Implementation tiers for maturity calibration
- Playbook with 72 subcategories of suggested actions

**Practitioner consensus:** ISO 42001 = certifiable backbone; NIST AI RMF = risk intelligence layer. They are mutually reinforcing, not redundant.

---

## 4. Tools & Frameworks Implementing NIST AI RMF

### 4.1 Official NIST Resources

| Resource | Description |
|---|---|
| **AI RMF Playbook** | Suggested actions for all 72 subcategories; filterable, tailorable |
| **AI RMF Roadmap** | Future development priorities including crosswalks, profiles, effectiveness measurement |
| **AI RMF Crosswalks** | Official mappings to ISO/IEC 42001, ISO/IEC 23894, OECD AI, EU AI Act |
| **AIRC (AI Resource Center)** | Operational support, use cases, community resources |
| **AI RMF Generative AI Profile (AI 600-1)** | 200+ GenAI-specific suggested actions |
| **AI RMF Critical Infrastructure Profile** | Concept note released April 2026 |
| **Translations** | Arabic, Japanese (more planned) |

### 4.2 Open-Source & Community Tools

| Tool | Description | Link |
|---|---|---|
| **NIST AI RMF Cookbook** | Operational governance for small teams: 130+ model cards, policy stack, risk scenarios, YAML schemas. Integrates NIST AI RMF + CIS-RAM + CIS Controls v8.1 + Colorado SB-24-205 | github.com/vintagedon/nist-ai-rmf-cookbook |
| **NIST RMF Platform (robomotic)** | Django web app for managing AI RMF: Govern, Map, Measure, Manage functions | github.com/robomotic/nistrmf |
| **AI Governance Framework Tools** | NIST-to-ISO 42001 gap analysis Excel template, migration playbook | github.com/BinaryVerseAI/ai-governance-framework-tools |
| **AIROM** | AI component/dependency scanner: inventories models, datasets, frameworks; maps to regulatory frameworks | airom.dev |
| **VerifyWise** | AI governance platform with NIST AI RMF API (14 endpoints), model inventory, risk management, compliance frameworks | verifywise.ai |

### 4.3 Commercial Platforms

| Platform | NIST AI RMF Capabilities |
|---|---|
| **VerifyWise** | Full NIST AI RMF API, progress tracking, subcategory risk mapping, EU AI Act + ISO 27001 + ISO 42001 compliance |
| **Acuna GRC** | ISO 42001 implementation, clause-by-clause guidance, EU AI Act mapping |
| **Konfirmity** | ISO 42001 requirements guide, clause-by-clause implementation |
| **Cytra** | ISO 42001 clause-by-clause implementation guidance |

### 4.4 Maturity Models

| Model | Description |
|---|---|
| **NIST Implementation Tiers** | 4-tier model (Partial → Risk-Informed → Repeatable → Adaptive) |
| **Academic Maturity Model** | 5-level scale (1-5) scoring coverage, robustness, input diversity per RMF category (arXiv:2401.15229) |

### 4.5 Agentic AI Profile (Emerging)

The **NIST AI RMF Agentic Profile** (proposed by Cloud Security Alliance, 2026) extends RMF for autonomous agents:
- **GOVERN extension:** Formal autonomy tier classification with oversight obligations
- **MAP extension:** Tool-use risk modeling, action-consequence mapping
- **MEASURE extension:** Runtime behavioral metrics, autonomy calibration, delegation chain monitoring
- **MANAGE extension:** Agent compromise response, behavioral drift correction, principled decommissioning

NIST has acknowledged these gaps through its **February 2026 AI Agent Standards Initiative** (CAISI), with an **AI Agent Interoperability Profile** planned for Q4 2026.

---

## 5. Gaps & Limitations

### 5.1 Structural Gaps in NIST AI RMF

| Gap | Description |
|---|---|
| **No certification mechanism** | Voluntary only — no audit standard, no compliance badge. "We follow NIST AI RMF" requires self-generated evidence. ISO 42001 fills this gap. |
| **Risk measurement immaturity** | NIST acknowledges (Section 1.2.1) that poorly defined AI risks are difficult to measure. Pre-deployment testing may be inadequate or mismatched to deployment contexts. |
| **No prescribed risk tolerance** | Framework explicitly doesn't prescribe risk tolerance (Section 1.2.2). Organizations without mature risk programs face significant ambiguity. |
| **Generative AI coverage arrived late** | Base framework (Jan 2023) didn't comprehensively address GenAI. AI 600-1 arrived 18 months later (Jul 2024), leaving early adopters without guidance during peak GenAI deployment. |
| **No prescriptive implementation path** | Playbook provides suggestions, but organizations determine sequencing, staffing, tooling, and integration themselves. Implementation quality varies significantly. |
| **Ecosystem-level risks hard to capture** | Cross-system, compounding, and societal-scale risks remain difficult to manage within the framework's structure. |
| **Agentic AI not addressed** | Neither RMF 1.0 nor AI 600-1 contemplated agents with tool-use capabilities executing autonomously. NIST's Agentic Profile is not yet released. |
| **SME resource barriers** | Small and medium-sized enterprises face disproportionate resource barriers. Only 9% of companies document AI model data; only 2% maintain AI incident logs. |

### 5.2 Gaps in ISO 42001

| Gap | Description |
|---|---|
| **Shallow risk metrics** | Certified management system may lack granular, context-sensitive risk measurement. NIST AI RMF fills this. |
| **No trustworthiness characteristics** | ISO 42001 doesn't define specific AI trustworthiness characteristics (validity, reliability, fairness, etc.). NIST AI RMF provides this taxonomy. |
| **No implementation tiers** | No maturity calibration mechanism. NIST's 4-tier model provides this. |
| **No GenAI-specific guidance** | ISO 42001 is technology-agnostic. NIST AI 600-1 provides GenAI-specific risk categories and actions. |
| **No Playbook equivalent** | ISO 42001 has no companion suggested-actions document comparable to the AI RMF Playbook. |

### 5.3 Mapping Gaps (Where Neither Framework Fully Covers)

| Area | NIST AI RMF | ISO 42001 | Gap |
|---|---|---|---|
| **Agentic AI governance** | Agentic Profile proposed but not released | Not addressed | No framework fully covers autonomous agent risk |
| **Content provenance standards** | Suggested actions only | Not addressed | No technical standard for provenance implementation |
| **Real-time behavioral monitoring** | MEASURE 2.4 covers monitoring | Clause 9.1 covers monitoring | Neither provides concrete technical implementation |
| **Cross-border regulatory alignment** | Crosswalks to EU AI Act, OECD | International standard | No unified global AI governance framework |
| **AI incident reporting** | MG-4.3 covers incident communication | Clause 10.2 covers nonconformity | Neither defines AI-specific incident severity classification |
| **Supply chain transparency** | GV-6.1, MG-3.1 cover third-party risk | A.10 covers third-party relationships | Neither provides AI bill of materials (AI-BOM) standard |
| **Environmental impact measurement** | MS-2.12 covers assessment | Not addressed | No standardized carbon accounting for AI training/inference |
| **Human-AI teaming guidance** | MP-3.5, GV-3.2 cover oversight | A.9 covers use of AI systems | Neither provides detailed human factors engineering guidance |

### 5.4 Implementation Gap

The most significant gap is not in framework design but in **organizational implementation**:

- **Documentation vs. operation:** Organizations produce compliance narratives (mapping documents) without operational controls (monitoring, incident response, threshold-based alerts)
- **Inventory incompleteness:** AI system inventories consistently miss AI features embedded in SaaS platforms (Salesforce Einstein, Workday AI, Microsoft Copilot)
- **Training deficit:** Over 60% of firms cite training deficiencies; only 2% maintain incident logs
- **Policy without enforcement:** AI risk policies exist on paper but lack operational specificity, escalation processes, and decision authority
- **Framework translation problem:** RMF language doesn't automatically become role-usable, cross-level, authority-connected governance

---

## 6. Strategic Implications for GRC_Claw

### 6.1 Positioning Opportunity

GRC_Claw can position as the **operational bridge** between NIST AI RMF and ISO 42001:

1. **Translate NIST AI RMF's 72 subcategories into ISO 42001's 38 Annex A controls** — automated crosswalk with gap analysis
2. **Operationalize the Playbook** — turn suggested actions into executable workflows, evidence collection, and audit trails
3. **Close the implementation gap** — provide the tooling layer that converts framework language into operational controls
4. **Cover the agentic AI gap** — implement the proposed Agentic Profile extensions before NIST formally releases them
5. **Unify risk vocabulary** — reconcile NIST terminology (AI Risk Profile, Affected Community) with ISO 42001 terminology (AIMS, Interested Party)

### 6.2 Key Differentiators to Develop

| Capability | NIST AI RMF | ISO 42001 | GRC_Claw Opportunity |
|---|---|---|---|
| Automated crosswalk | Manual PDF crosswalk | N/A | Real-time bidirectional mapping with gap detection |
| Risk measurement | Suggested metrics | Clause 9.1 requires monitoring | Automated metric collection, threshold alerting |
| GenAI risk detection | AI 600-1 suggested actions | Not addressed | Automated confabulation, bias, provenance detection |
| Agentic AI governance | Not yet released | Not addressed | First-mover advantage in agent autonomy tiering |
| Evidence collection | Playbook suggestions | Clause 7.5 documented information | Automated evidence packaging for audit readiness |
| Maturity assessment | 4 tiers (self-assessed) | Certification (external) | Continuous maturity scoring with certification readiness |

### 6.3 Recommended Architecture

```
┌─────────────────────────────────────────────────────┐
│                  GRC_Claw Platform                   │
├─────────────────────────────────────────────────────┤
│  Framework Layer                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ NIST AI RMF  │  │ ISO 42001    │  │ AI 600-1   │ │
│  │ 4 functions  │  │ 10 clauses   │  │ 12 risks   │ │
│  │ 72 subcats   │  │ 38 controls  │  │ 200+ actions│ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │        │
│  ┌──────▼─────────────────▼─────────────────▼──────┐ │
│  │         Unified Risk Engine                     │ │
│  │  • Crosswalk engine (NIST ↔ ISO ↔ GenAI)       │ │
│  │  • Gap analyzer (bidirectional)                 │ │
│  │  • Maturity scorer (4-tier + continuous)        │ │
│  │  • Evidence collector (audit-ready packaging)   │ │
│  └──────────────────────┬──────────────────────────┘ │
│                         │                            │
│  ┌──────────────────────▼──────────────────────────┐ │
│  │         Operational Layer                        │ │
│  │  • AI system inventory (incl. SaaS-embedded AI)  │ │
│  │  • Risk register with treatment workflows        │ │
│  │  • Incident response with AI-specific triggers   │ │
│  │  • Monitoring & metrics dashboard                │ │
│  │  • Policy manager with version control           │ │
│  │  • Third-party AI component register             │ │
│  │  • Agent autonomy tier classification            │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 7. Key Takeaways

1. **NIST AI RMF is the de facto US standard** for AI risk management — voluntary but increasingly cited in regulation and procurement
2. **ISO 42001 is the certifiable international standard** — provides the auditable backbone that NIST lacks
3. **The frameworks are complementary, not competing** — ISO 42001 = management system; NIST AI RMF = risk methodology
4. **AI 600-1 is the operational profile for GenAI** — 12 risks, 200+ actions, de facto obligation for US-facing organizations
5. **The biggest gap is implementation, not framework design** — organizations struggle to translate framework language into operational controls
6. **Agentic AI is the next frontier** — neither framework fully covers autonomous agent risk; NIST's Agentic Profile is planned for Q4 2026
7. **GRC_Claw's opportunity** is to be the tooling layer that bridges the two frameworks, automates the crosswalk, and closes the implementation gap

---

## References

1. NIST AI 100-1 — Artificial Intelligence Risk Management Framework (AI RMF 1.0), January 2023
2. NIST AI 600-1 — Generative Artificial Intelligence Profile, July 2024
3. NIST AI RMF Playbook, March 2023
4. NIST AI RMF to ISO/IEC FDIS 42001 Crosswalk, NIST AIRC
5. ISO/IEC 42001:2023 — AI Management System Standard, December 2023
6. ISO/IEC 42006:2025 — AI-specific competence and audit time requirements, July 2025
7. NIST AI RMF Roadmap
8. NIST AI RMF Agentic Profile (Cloud Security Alliance proposal, 2026)
9. NIST AI Agent Standards Initiative (CAISI, February 2026)
10. "Evolving AI Risk Management: A Maturity Model based on NIST AI RMF" (arXiv:2401.15229)
11. "Why AI Governance Frameworks Are Hard to Adopt" (arXiv:2608.12352)
12. NIST AI RMF Cookbook (github.com/vintagedon/nist-ai-rmf-cookbook)
13. ISO 42001 + NIST AI RMF: The Practitioner Mapping Guide (aigl.blog)
