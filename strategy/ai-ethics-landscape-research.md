# AI Ethics Frameworks & Tools Landscape Research
## For GRC_Claw Positioning (ISO 42001 / Agentic AI Governance)

---

## 1. Major AI Ethics Frameworks

### 1.1 IEEE Ethically Aligned Design (EAD)
- **Published:** 2019 (First Edition)
- **Issuer:** IEEE Global Initiative on Ethics of Autonomous and Intelligent Systems
- **License:** Creative Commons Attribution-NonCommercial 4.0
- **Structure:** Three Pillars → General Principles → Chapter-specific Issues & Recommendations
  - **Three Pillars:**
    1. Universal Human Values (human rights, well-being, environmental sustainability)
    2. Political Self-Determination and Data Agency (democracy, individual control over data)
    3. Technical Reliability (trust, safety, auditability, certification)
  - **General Principles:** Human Rights, Well-being, Data Agency, Effectiveness, Transparency, Accountability, Awareness of Misuse, Competence
- **Key Output:** Inspired the IEEE P7000™ Standards Working Groups (P7001 Transparency, P7002 Data Privacy, P7008 Ethically Driven Nudging, P7009 Fail-Safe Design, P7010 Wellbeing Metrics)
- **Nature:** Non-binding, consensus-based, pragmatic guidance for technologists, educators, policymakers

### 1.2 EU Ethics Guidelines for Trustworthy AI
- **Published:** April 8, 2019
- **Issuer:** EU High-Level Expert Group on Artificial Intelligence (AI HLEG)
- **Follow-up:** ALTAI (Assessment List for Trustworthy AI) — July 2020, practical self-assessment web tool
- **Three Components of Trustworthy AI:**
  1. Lawful (compliance with EU law including GDPR)
  2. Ethical (adherence to ethical principles)
  3. Robust (technical and social perspective)
- **Four Ethical Principles:** Respect for human autonomy, Prevention of harm, Fairness, Explicability
- **Seven Key Requirements:**
  1. Human agency and oversight (human-in/on-the-loop, human-in-command)
  2. Technical robustness and safety
  3. Privacy and data governance
  4. Transparency (traceability, explainability, disclosure of AI interaction)
  5. Diversity, non-discrimination and fairness
  6. Societal and environmental well-being
  7. Accountability (auditability, redress mechanisms)
- **Nature:** Non-binding, risk-based, voluntary framework; designed to inform EU policy (now superseded by EU AI Act for binding obligations)

### 1.3 Montreal Declaration for Responsible AI
- **Published:** December 4, 2018
- **Issuer:** Université de Montréal, with Fonds de recherche du Québec
- **Process:** Year-long citizen deliberation — 15 workshops, 500+ citizens, experts, stakeholders
- **10 Principles:**
  1. Well-being (of all sentient beings)
  2. Respect for autonomy
  3. Protection of privacy and intimacy
  4. Solidarity (among people and generations)
  5. Democratic participation (intelligibility, justifiability, accessibility)
  6. Equity (just and equitable society)
  7. Diversity inclusion (social and cultural diversity)
  8. Prudence (anticipate adverse consequences)
  9. Responsibility (human responsibility must not be diminished)
  10. Sustainable development (environmental sustainability)
- **Nature:** Non-binding, civil-society-driven, democratic legitimacy; available in 10 languages

### 1.4 UNESCO Recommendation on the Ethics of AI
- **Published:** November 23, 2021
- **Issuer:** UNESCO General Conference (41st session)
- **Adoption:** Unanimous by 193 Member States — first global standard-setting instrument on AI ethics
- **Structure:** Four Values → Ten Principles → Eleven Policy Action Areas
  - **Four Values:** Human rights & dignity; Environment & ecosystem flourishing; Diversity & inclusiveness; Peaceful, just & interconnected societies
  - **Ten Principles:** Proportionality & do-no-harm; Safety & security; Fairness & non-discrimination; Sustainability; Privacy & data protection; Human oversight & determination; Transparency & explainability; Responsibility & accountability; Awareness & literacy; Multi-stakeholder & adaptive governance
- **Implementation Tools:** Readiness Assessment Methodology (RAM), Ethical Impact Assessment (EIA)
- **Nature:** Soft law / non-binding but authoritative; Member States report progress every 4 years

### 1.5 NIST AI Risk Management Framework (AI RMF 1.0)
- **Published:** January 26, 2023
- **Issuer:** U.S. National Institute of Standards and Technology
- **Structure:** Four Core Functions → 19 Categories → 72 Subcategories
  - **GOVERN** (cross-cutting): policies, accountability, culture, third-party oversight
  - **MAP**: context establishment, stakeholder impact, risk identification
  - **MEASURE**: metrics, evaluation, monitoring, feedback
  - **MANAGE**: risk treatment, incident response, communication
- **Seven Trustworthy AI Characteristics:** Valid & reliable; Safe; Secure & resilient; Accountable & transparent; Explainable & interpretable; Privacy-enhanced; Fair with harmful bias managed
- **Generative AI Profile:** NIST AI 600-1 (July 2024) — 12 GenAI-specific risk categories, 200+ suggested actions
- **Companion Resources:** AI RMF Playbook, Crosswalks (to ISO 42001, OECD, EU AI Act), AI Resource Center
- **Nature:** Voluntary, non-certifiable, sector-agnostic, rights-preserving

### 1.6 OECD AI Principles
- **Published:** May 2019 (updated 2024)
- **Adoption:** 47 countries (OECD members + partners)
- **Five Values-Based Principles:** Inclusive growth & sustainable development; Human-centered values & fairness; Transparency & explainability; Robustness, security & safety; Accountability
- **Five Policy Recommendations:** Investing in AI R&D; Fostering a digital ecosystem for AI; Shaping an enabling policy environment; Building human capacity & preparing for labour market transformation; International cooperation for trustworthy AI
- **Nature:** Intergovernmental standard, non-binding

---

## 2. AI Ethics Tools & Platforms

### 2.1 Open-Source Fairness/Bias Tools
| Tool | Issuer | Description |
|------|--------|-------------|
| **AI Fairness 360 (AIF360)** | IBM | 71+ bias metrics, 9 mitigation algorithms, extensible metric explanations, Apache 2.0 |
| **Fairlearn** | Microsoft | Python toolkit for assessing and mitigating fairness issues; sociotechnical approach |
| **Aequitas** | University of Chicago | Bias auditing toolkit for machine learning models |
| **Responsibly** | Responsibly AI | Fairness issues in data, models, word embeddings |
| **What-If Tool** | Google | Model interpretability and fairness analysis |
| **DEON** | Various | Ethical checklist for data science projects |

### 2.2 Privacy & Data Governance Tools
| Tool | Issuer | Description |
|------|--------|-------------|
| **Microsoft Presidio** | Microsoft | PII detection, anonymization, de-anonymization |
| **Opacus** | Meta | Differential privacy for PyTorch training |
| **TensorFlow Privacy** | Google | Differentially private optimizers and accounting |
| **Privacy Meter** | Various | ML model privacy attack auditing (membership inference) |

### 2.3 Commercial AI Governance Platforms
| Platform | Description |
|----------|-------------|
| **Credo AI** | AI risk and controls library, policy packs, Responsible AI Stack; covers LLMs, multi-agent systems |
| **Trustible** | AI intake, inventory, risk scoring, vendor review, control mapping, audit evidence |
| **OneTrust AI Governance** | AI system catalog, risk assessment, policy mapping, posture monitoring |
| **Fiddler AI** | AI observability, model/LLM/agentic monitoring |
| **Palo Alto Prisma AIRS** | AI asset discovery, posture management, model scanning, red teaming, runtime protection |
| **Fairmind** | Open-source ethical AI governance platform (bias detection, compliance, fairness testing) |

### 2.4 Assessment & Audit Frameworks
| Framework | Issuer | Description |
|-----------|--------|-------------|
| **ALTAI** | EU AI HLEG | Web-based self-assessment checklist for Trustworthy AI |
| **AI Verify** | Singapore IMDA | Open-source testing framework for responsible AI |
| **TAII Framework** | Socialtechlab | Trustworthy AI Implementation framework |
| **Data Ethics Framework** | UK ODI | Procedural framework for public sector data use |
| **AI Ethics Assessment Toolkit** | Open Robo Ethics | Assessment toolkit for AI ethics |
| **NIST AI RMF Playbook** | NIST | Suggested actions for each AI RMF subcategory |

### 2.5 OECD.AI Catalogue
- Maintains a comprehensive catalogue of 100+ tools and metrics for trustworthy AI
- Covers technical tools, procedural frameworks, and educational resources
- Includes tools for fairness, transparency, robustness, data governance, and safety

---

## 3. ISO/IEC 42001:2023 — The Certifiable Standard

### 3.1 Overview
- **Published:** December 18, 2023
- **Full Title:** ISO/IEC 42001:2023 — Information technology — Artificial intelligence — Management system
- **Status:** World's first AI management system standard
- **Certifiable:** Yes, by accredited bodies (ISO/IEC 42006:2025 provides certification requirements)
- **Methodology:** Plan-Do-Check-Act (PDCA) — same as ISO 27001, ISO 9001

### 3.2 Structure
- Clauses 4–10 (Context, Leadership, Planning, Support, Operation, Performance Evaluation, Improvement)
- **Annex A:** 38 controls across 9 objectives
- **Companion Standards:**
  - ISO/IEC 42005 — AI System Impact Assessment
  - ISO/IEC 23894 — AI Risk Management guidance
  - ISO/IEC 22989 — AI terminology and concepts
  - ISO/IEC 23053 — ML framework for describing AI systems

### 3.3 Core Principles
1. Ethical AI practices (human rights, bias avoidance)
2. Transparency (data, decisions, operations)
3. Accountability (clear responsibility lines)
4. Security and privacy
5. Continuous improvement

### 3.4 Relationship to Other Frameworks

| Dimension | ISO/IEC 42001 | NIST AI RMF | EU AI Act | IEEE EAD | EU Ethics Guidelines | Montreal Declaration | UNESCO |
|-----------|---------------|-------------|-----------|----------|---------------------|---------------------|---------|
| **Type** | Certifiable standard | Voluntary framework | Binding regulation | Non-binding guidance | Non-binding guidance | Civil society declaration | Soft law (193 states) |
| **Certifiable** | Yes | No | Conformity assessment | No | No | No | No |
| **Enforcement** | Customer/contractual | None | Fines up to €15M/3% | None | None | None | Reporting (4-year) |
| **Approach** | Management system (PDCA) | Risk-based (Govern/Map/Measure/Manage) | Risk-tiered regulation | Principles → Practice | Requirements + Assessment | Values-based principles | Values + Principles + Policy |
| **Scope** | Organization's AIMS | Any AI system | AI systems in EU market | Autonomous & intelligent systems | AI systems in EU | AI systems globally | AI systems globally |
| **GenAI Coverage** | General (all AI) | GenAI Profile (600-1) | Specific obligations | General | General | General | General |

### 3.5 Key Differentiators of ISO 42001
- **Only certifiable standard** among major AI governance frameworks
- **Management system approach** — integrates with existing ISO standards (27001, 9001)
- **38 Annex A controls** — concrete, auditable control objectives
- **Complements regulation** — helps meet EU AI Act, NIST AI RMF, and other frameworks
- **Customer-driven** — increasingly required in B2B contracts and procurement
- **Agentic AI ready** — covers autonomous and multi-agent systems through risk-based approach

### 3.6 How Frameworks Map to ISO 42001

| ISO 42001 Clause | NIST AI RMF | EU Ethics Guidelines | IEEE EAD | UNESCO |
|-----------------|-------------|---------------------|----------|--------|
| 5. Leadership | GOVERN | Accountability | General Principles | Responsibility & accountability |
| 6. Planning | MAP | Risk assessment | Issues & Recommendations | Proportionality & do-no-harm |
| 7. Support | GOVERN | Training, culture | Competence | Awareness & literacy |
| 8. Operation | MAP/MEASURE | All 7 requirements | Technical Reliability | All 10 principles |
| 9. Performance Evaluation | MEASURE | ALTAI assessment | Auditability | Monitoring & evaluation |
| 10. Improvement | MANAGE | Continuous improvement | Continuous learning | Adaptive governance |

---

## 4. Key Trends & Observations

1. **Convergence:** All major frameworks converge on similar principles — transparency, fairness, accountability, safety, human oversight, privacy
2. **From principles to practice:** Field is moving from high-level principles to operational tools, assessment methodologies, and certifiable standards
3. **Regulatory hardening:** EU AI Act (binding from 2027-2028) is converting voluntary guidelines into legal obligations
4. **GenAI gap:** Most pre-2023 frameworks were designed for traditional ML; NIST AI 600-1 and EU AI Act are first to specifically address generative AI risks
5. **Agentic AI gap:** Minimal governance frameworks specifically address autonomous multi-agent systems — opportunity for GRC_Claw
6. **Tooling explosion:** 130+ AI governance tools now exist (open-source and commercial), but fragmentation is high
7. **ISO 42001 as umbrella:** ISO 42001 is positioned as the certifiable umbrella that can operationalize principles from all other frameworks

---

## 5. Implications for GRC_Claw Positioning

- **Gap in agentic AI governance:** No comprehensive framework specifically addresses governance of autonomous, multi-agent AI systems
- **ISO 42001 as foundation:** GRC_Claw can position as the implementation layer for ISO 42001, bridging the gap between management system requirements and technical controls
- **Tool integration:** Opportunity to integrate with existing fairness/bias tools (AIF360, Fairlearn) and governance platforms (Credo AI, Trustible)
- **Framework mapping:** GRC_Claw can provide crosswalks between ISO 42001 controls and NIST AI RMF, EU AI Act, and other frameworks
- **Assessment automation:** ALTAI, AI Verify, and similar tools point to demand for automated compliance assessment
