# Unified AI Governance Policy Template
## Cross-Framework: NIST AI RMF 1.0 + ISO/IEC 42001:2023 + EU AI Act (Reg. 2024/1689)

**Version:** 1.0  
**Date:** 2026-10-01  
**Classification:** Public  
**Supersedes:** All prior AI use policies  

---

## Framework Mapping Legend

| Code | Framework | Reference |
|------|-----------|-----------|
| **NIST-GV** | NIST AI RMF — Govern | Cross-cutting |
| **NIST-MP** | NIST AI RMF — Map | Context & risk identification |
| **NIST-MS** | NIST AI RMF — Measure | Metrics & monitoring |
| **NIST-MG** | NIST AI RMF — Manage | Risk treatment & response |
| **ISO-4** | ISO/IEC 42001 Clause 4 | Context of the organization |
| **ISO-5** | ISO/IEC 42001 Clause 5 | Leadership |
| **ISO-6** | ISO/IEC 42001 Clause 6 | Planning (risk & impact assessment) |
| **ISO-7** | ISO/IEC 42001 Clause 7 | Support |
| **ISO-8** | ISO/IEC 42001 Clause 8 | Operation |
| **ISO-9** | ISO/IEC 42001 Clause 9 | Performance evaluation |
| **ISO-10** | ISO/IEC 42001 Clause 10 | Improvement |
| **A.2–A.10** | ISO/IEC 42001 Annex A | 38 AI-specific controls |
| **EU-9** | EU AI Act Article 9 | Risk management system |
| **EU-10** | EU AI Act Article 10 | Data & data governance |
| **EU-11** | EU AI Act Article 11 | Technical documentation |
| **EU-12** | EU AI Act Article 12 | Record-keeping |
| **EU-13** | EU AI Act Article 13 | Transparency |
| **EU-14** | EU AI Act Article 14 | Human oversight |
| **EU-15** | EU AI Act Article 15 | Accuracy, robustness, cybersecurity |
| **EU-17** | EU AI Act Article 17 | Quality management system |
| **EU-26** | EU AI Act Article 26 | Deployer obligations |
| **EU-27** | EU AI Act Article 27 | Fundamental rights impact assessment |
| **EU-53** | EU AI Act Article 53 | GPAI provider obligations |
| **EU-55** | EU AI Act Article 55 | GPAI systemic risk obligations |

---

## Section 1: Purpose, Scope, and Definitions

**Maps to:** NIST-GV · ISO-4, ISO-5 · EU-17

### 1.1 Purpose

This policy establishes the governance framework for the design, development, procurement, deployment, operation, and decommissioning of all artificial intelligence systems at [ORGANIZATION]. It ensures that AI is used lawfully, ethically, and responsibly, in alignment with the organization's risk appetite and legal obligations.

This policy satisfies the requirement for a documented AI policy under ISO/IEC 42001 Clause 5.2 and supports conformity with the EU AI Act's quality management system obligations (Article 17).

### 1.2 Scope

**In scope:**
- All AI systems developed, procured, deployed, or used by [ORGANIZATION], including:
  - Generative AI (GenAI) tools and large language models (LLMs)
  - Agentic AI systems (autonomous agents that plan, use tools, and execute multi-step workflows)
  - AI features embedded in third-party software already licensed by [ORGANIZATION]
  - Internally developed models and externally procured AI services
- All personnel: employees, contractors, temporary staff, interns, volunteers, and third-party service providers acting on behalf of [ORGANIZATION]
- All data processed by AI systems, including personal data, confidential information, and regulated data (CUI, PHI, cardholder data, ITAR technical data)

**Out of scope:**
- AI systems used purely for personal purposes on personal devices with no connection to [ORGANIZATION] systems, accounts, or data
- AI research conducted under separate research ethics board approval

### 1.3 Definitions

| Term | Definition | Source |
|------|-----------|--------|
| **AI System** | A machine-based system that, for explicit or implicit objectives, infers from the input it receives how to generate outputs such as predictions, content, recommendations, or decisions that can influence physical or virtual environments. | ISO/IEC 22989; EU AI Act Art. 3(1) |
| **Agentic AI** | An AI system capable of autonomous goal pursuit, perception, action, iteration, adaptation, and termination (GPA+IAT properties), including the ability to invoke tools, spawn sub-agents, and execute multi-step workflows with minimal human intervention. | Bommarito et al.; TrustX ARC |
| **AI Model** | A computational representation learned from data that maps inputs to outputs. | ISO/IEC 22989 |
| **Deployer** | Any legal person, public agency, or other body using an AI system under its authority, except where the AI system is used in the course of a personal non-professional activity. | EU AI Act Art. 3(4) |
| **Provider** | A natural or legal person, public agency, or other body that develops an AI system or a general-purpose AI model and places it on the market or puts it into service under its own name or trademark. | EU AI Act Art. 3(3) |
| **High-Risk AI System** | An AI system listed in Annex III of the EU AI Act, or one that is a safety component of a product covered by Union harmonization legislation. | EU AI Act Art. 6, Annex III |
| **GPAI Model** | An AI model, including when trained with a large amount of data using self-supervision at scale, that displays significant generality and is capable to competently perform a wide range of distinct tasks regardless of the way the model is placed on the market. | EU AI Act Art. 3(63) |
| **Personal Data** | Any information relating to an identified or identifiable natural person. | GDPR Art. 4(1) |
| **AI Impact Assessment** | A documented assessment of the potential consequences of an AI system for individuals, groups of individuals, and society, conducted prior to deployment. | ISO/IEC 42001 Clause 6.1.4, 8.4 |
| **Autonomy Tier** | A classification of an agentic AI system's operational independence and the consequences of its potential failures, ranging from Tier 1 (fully supervised) to Tier 4 (full autonomy within constrained environment). | NIST AI RMF Agentic Profile; TrustX ARC |

---

## Section 2: Governance Structure and Accountability

**Maps to:** NIST-GV · ISO-5, A.3 · EU-17

### 2.1 AI Governance Committee

[ORGANIZATION] establishes an **AI Governance Committee** with the following composition and mandate:

| Role | Responsibility | Line of Defense |
|------|---------------|-----------------|
| **Executive Sponsor** (C-suite) | Owns the mandate, budget, and board connection; approves AI risk appetite | Leadership |
| **Committee Chair** (CAIO or equivalent) | Sets policy, makes go/no-go decisions on high-risk AI, handles escalation | Leadership |
| **AI Governance Lead** | Day-to-day program management, maintains AI inventory, coordinates reviews | 1st Line |
| **Data Protection Officer** | Advises on privacy, DPIA, and data protection compliance | 2nd Line |
| **CISO / Security Lead** | Advises on AI security, threat modeling, and incident response | 2nd Line |
| **Legal / Compliance Lead** | Advises on regulatory compliance, contract review, and legal risk | 2nd Line |
| **Business Unit Representatives** | Represent operational interests, own AI use cases in their domains | 1st Line |
| **Internal Audit** | Independent assurance of AI governance effectiveness | 3rd Line |

### 2.2 Accountability for Agentic AI

Each deployed agentic AI system must have:
- A named **Accountable Owner** (business owner responsible for the agent's behavior)
- A named **Technical Owner** (responsible for security posture and runtime controls)
- A documented **Delegation Authority Lineage** (which human principals authorized the agent's deployment and with what authorities)
- A defined **Oversight Boundary** specifying:
  - Actions the agent may take without human approval
  - Conditions requiring pause and escalation to human oversight
  - Scope of delegation authority (conditions for spawning/tasking sub-agents)
  - Accountability lineage connecting every agent action to a responsible human officer

### 2.3 Three Lines of Defense Model

| Line | Function | AI Governance Activities |
|------|----------|--------------------------|
| **1st Line** | Business operations | AI system operation, data input, output use, incident reporting |
| **2nd Line** | Risk & compliance | Policy oversight, risk assessment, compliance monitoring, vendor review |
| **3rd Line** | Internal audit | Independent assurance, control testing, governance effectiveness review |

---

## Section 3: AI System Classification and Risk Tiering

**Maps to:** NIST-MP · ISO-6, A.5 · EU-9, EU-26

### 3.1 Risk Classification Matrix

All AI systems must be classified into one of four risk tiers before deployment:

| Tier | Description | Examples | Governance Requirements |
|------|-------------|----------|------------------------|
| **Tier 1 — Minimal** | AI systems with no consequential impact on individuals or organizational operations | Grammar checkers, internal document formatting, non-sensitive data summarization | Basic registration, standard logging |
| **Tier 2 — Limited** | AI systems with limited consequential impact, operating on non-regulated data | Internal knowledge base Q&A, code completion, meeting transcription | Registration, data classification review, human review of outputs |
| **Tier 3 — Substantial** | AI systems with substantial impact on individuals or organizational decisions, or processing regulated data | Customer-facing chatbots, resume screening, document classification of confidential data | Full risk assessment, DPIA (if personal data), human oversight, bias testing, enhanced monitoring |
| **Tier 4 — High** | AI systems with high impact on fundamental rights, safety, or significant organizational decisions | Credit scoring, medical diagnosis support, autonomous agents with external effects, high-risk AI under EU AI Act Annex III | Full conformity assessment, FRIA (if deployer), continuous monitoring, board approval, kill-switch capability, quarterly recertification |

### 3.2 Agentic AI Autonomy Classification

Agentic AI systems must additionally be classified by autonomy level:

| Autonomy Level | Description | Human Oversight Requirement |
|---------------|-------------|---------------------------|
| **L1 — Operator** | User directs all actions; agent acts on command | Human approves each action |
| **L2 — Collaborator** | User and agent collaboratively plan and execute | Human reviews plan before execution |
| **L3 — Consultant** | Agent leads actions, consults user for expertise | Human available for consultation; agent pauses on uncertainty |
| **L4 — Approver** | Agent engages user only for specified risk scenarios | Human approval required for defined high-risk actions |
| **L5 — Observer** | Full autonomy; user can only monitor | Continuous monitoring, hard constraints, kill-switch, board oversight |

### 3.3 EU AI Act Classification

AI systems must be assessed against EU AI Act classification rules:
- **Prohibited practices** (Article 5): Social scoring, real-time remote biometric identification (with exceptions), emotion recognition in workplaces/educational institutions, etc.
- **High-risk systems** (Article 6 + Annex III): Safety components of regulated products, biometric identification, critical infrastructure management, employment/worker management, access to essential services, law enforcement, migration/asylum, administration of justice, democratic processes.
- **Limited risk** (Article 50): Transparency obligations for chatbots, deepfakes, emotion recognition (non-prohibited).
- **Minimal risk**: All other AI systems (no specific obligations).

---

## Section 4: Data Governance and AI

**Maps to:** NIST-MP · ISO-8, A.7 · EU-10, EU-13

### 4.1 Data Classification for AI Use

| Data Tier | Public AI Tools | Approved Enterprise AI Tools | What This Covers |
|-----------|----------------|------------------------------|------------------|
| **Public** | Permitted | Permitted | Already published or approved for publication |
| **Internal** | Not permitted | Permitted with standard controls | Internal memos, non-sensitive business data |
| **Confidential** | Not permitted | Permitted with masking or written approval | Client work, commercial terms, unpublished plans, source code |
| **Regulated** | Prohibited | Prohibited without enhanced controls and legal review | PHI, cardholder data, CUI, ITAR technical data, special category personal data |

### 4.2 Data Minimization and Purpose Limitation

- Only the minimum data necessary for the AI system's intended purpose may be entered into or processed by an AI system.
- Data entered into AI tools must be limited to what is required for the specific task.
- Personal data must not be entered into AI tools unless a lawful basis under GDPR (or applicable law) has been identified and documented.
- Data retention periods must be defined and enforced; AI system outputs must not be retained longer than necessary.

### 4.3 Training Data Governance

- AI systems must not be trained on [ORGANIZATION] data without explicit written approval from the AI Governance Committee.
- Vendor contracts must prohibit the use of [ORGANIZATION] inputs, outputs, prompts, or metadata for model training or fine-tuning without written consent.
- Training data provenance, quality, and bias must be documented for all internally developed AI systems (EU AI Act Article 10; ISO 42001 A.7).

### 4.4 Data Protection Impact Assessment (DPIA)

A DPIA must be completed before deploying any AI system that:
- Processes personal data on a large scale
- Uses special category data (health, biometrics, genetic, political opinions, etc.)
- Conducts systematic monitoring of publicly accessible areas
- Makes automated decisions with legal or significant effects

---

## Section 5: Human Oversight and Transparency

**Maps to:** NIST-GV, NIST-MG · ISO-8, A.9 · EU-13, EU-14

### 5.1 Human Oversight Requirements

All AI systems must have appropriate human oversight proportional to their risk tier:

| Risk Tier | Human Oversight Requirement |
|-----------|---------------------------|
| Tier 1 | Periodic review of outputs; no real-time oversight required |
| Tier 2 | Human review of outputs before consequential use; spot-checking |
| Tier 3 | Human-in-the-loop (HITL) for all consequential decisions; meaningful review with authority to override |
| Tier 4 | Human-on-the-loop (HOTL) with continuous monitoring; defined override authority; ability to halt operations |

### 5.2 Transparency and Disclosure

- **AI-generated content** must be clearly labeled when:
  - A person is interacting with an AI system and might reasonably believe they are interacting with a person
  - Content is submitted to a court, regulator, or public body with rules on AI-assisted submissions
  - A client contract or professional body rule requires disclosure
  - The content is AI-generated imagery, audio, or video (deepfake) that depicts real events
- **AI system documentation** must be maintained and made available to deployers and competent authorities upon request (EU AI Act Article 11, 13).
- **Model cards** must be maintained for all Tier 3 and Tier 4 AI systems, documenting intended use, limitations, training data, performance metrics, and ethical considerations.

### 5.3 Automated Decision-Making

- AI systems that make or significantly influence decisions with legal or similarly significant effects on individuals must:
  - Provide meaningful information about the logic involved
  - Ensure human review is available upon request
  - Allow individuals to contest the decision
  - Comply with GDPR Article 22 (or applicable local equivalent)

---

## Section 6: Agentic AI Governance

**Maps to:** NIST-GV, NIST-MP, NIST-MS, NIST-MG · ISO-8, A.6, A.9 · EU-9, EU-14

*This section addresses governance requirements specific to autonomous AI agents that are not covered by traditional AI use policies.*

### 6.1 Agent Registry

Every agentic AI system must be registered in the **Agent Registry** before deployment, containing:

| Field | Description |
|-------|-------------|
| Agent ID | Unique identifier |
| Agent Name | Descriptive name |
| Business Owner | Named accountable owner |
| Technical Owner | Named technical owner |
| Business Purpose | Documented purpose and intended use |
| Risk Tier | Tier 1–4 classification |
| Autonomy Level | L1–L5 classification |
| Tool Permissions | List of APIs, databases, external channels accessible |
| Data Scope | Data classifications the agent may access |
| Delegation Authority | Conditions for spawning/tasking sub-agents |
| Escalation Triggers | Conditions requiring human approval |
| Budget Caps | Monetary, API call, and message volume limits |
| Kill Switch | Mechanism for immediate deactivation |
| Review Date | Scheduled recertification date |

### 6.2 Tool Permission and Action Scope

- Agents operate under **deny-by-default** permissions: any tool or action not explicitly authorized is prohibited.
- Tool permissions must be scoped to the minimum necessary for the agent's intended purpose.
- Agents must not be granted permissions that exceed those of their authorizing human principal.
- Inter-agent communication must be explicitly authorized and logged.
- Agents must not acquire new tool capabilities without human approval.

### 6.3 Budget and Action Constraints

| Constraint | Requirement |
|-----------|-------------|
| **Monetary Budget** | Hard cap on spending per transaction, per day, per month |
| **API Call Budget** | Rate limits and volume caps per hour, day, month |
| **Message Volume** | Caps on external communications (emails, messages, posts) |
| **Time Horizon** | Maximum duration for autonomous operation without human check-in |
| **Action Scope** | Explicit list of action types the agent may perform autonomously |

### 6.4 Runtime Behavioral Monitoring

- All agent actions must be logged immutably, including: prompts, plans, tool calls, outputs, and delegation events.
- Logs must be retained for a minimum of 12–24 months (or longer if required by regulation).
- Behavioral analytics must detect:
  - Goal drift (deviation from intended purpose)
  - Permission escalation (attempting unauthorized actions)
  - Looping or cascading failures
  - Anomalous tool usage patterns
  - Data exfiltration attempts
- A **kill-switch** mechanism must be available and tested quarterly.

### 6.5 Agentic AI Incident Response

Agent-specific incident types include:
- **Goal hijacking**: Agent pursues objectives divergent from intended purpose
- **Tool misuse**: Agent uses tools in unauthorized ways or scopes
- **Identity abuse**: Agent impersonates unauthorized entities
- **Memory poisoning**: Agent's context/memory is manipulated to alter behavior
- **Cascading failures**: Errors propagate across delegation chains
- **Rogue agent**: Agent operates outside defined constraints

Incident response must include:
- Immediate kill-switch activation
- Forensic preservation of agent logs
- Impact assessment (actions taken, data accessed, external effects)
- Root cause analysis
- Corrective actions and control improvements
- Regulatory notification if required (EU AI Act Article 73 serious incident reporting)

### 6.6 Agent Lifecycle Management

| Phase | Governance Activity |
|-------|-------------------|
| **Design** | Risk classification, autonomy level assignment, tool permission design |
| **Development** | Security testing, bias testing, red teaming (prompt injection, excessive agency) |
| **Pre-Deployment** | Impact assessment, approval by AI Governance Committee, registry entry |
| **Deployment** | Monitoring activation, kill-switch testing, baseline behavior establishment |
| **Operation** | Continuous monitoring, behavioral analytics, periodic recertification |
| **Change** | Re-assessment on model update, tool change, or scope expansion |
| **Decommissioning** | Data deletion, access revocation, archive logs, registry update |

---

## Section 7: Third-Party and Vendor AI Governance

**Maps to:** NIST-MP, NIST-MG · ISO-8, A.10 · EU-26

### 7.1 Vendor Due Diligence

No AI vendor or AI-enabled product may be adopted for work involving Internal, Confidential, or Regulated data until it has passed a due diligence review covering:

1. Will our inputs, outputs, prompts, or metadata be used to train or fine-tune the vendor's models?
2. Where is our data processed and stored, and how long is it retained?
3. Which sub-processors and third-party AI services does the product rely on?
4. What data isolation, encryption, and access controls are in place?
5. Can the vendor provide a DPA, SOC 2 report, and BAA (where health data is involved)?
6. What is the breach notification commitment?
7. For consequential decisions, how is the model tested for bias, and can the vendor evidence it?
8. What is the vendor's AI governance maturity (ISO 42001 certification, NIST AI RMF alignment)?

### 7.2 Contract Requirements

Approved AI vendors must operate under a contract that:
- Prohibits the use of [ORGANIZATION] inputs, outputs, prompts, or metadata for model training without written consent
- Specifies data processing locations and retention periods
- Includes data processing agreements (DPA) where personal data is processed
- Requires breach notification within [24/48] hours
- Includes audit rights and compliance certifications
- Addresses AI-specific liability and indemnification

### 7.3 Embedded AI Features

- Users must not enable AI features in third-party software for work involving non-public data until [IT Security] has reviewed the feature's data handling.
- IT will monitor vendor terms-of-service changes for new AI data-use provisions.
- Embedded AI features must be assessed under the same risk tiering as standalone AI tools.

### 7.4 Ongoing Vendor Monitoring

- High-risk AI vendors must be reassessed annually and on event triggers (security incident, major product change, new sub-processor, change to data terms).
- Vendor risk ratings must be maintained and reviewed by the AI Governance Committee.

---

## Section 8: Risk Assessment and Impact Assessment

**Maps to:** NIST-MP, NIST-MS · ISO-6, A.5 · EU-9, EU-27

### 8.1 AI Risk Assessment Process

A documented AI risk assessment must be completed for all Tier 2 and above AI systems before deployment, and at planned intervals thereafter:

1. **Identify** known and reasonably foreseeable risks to health, safety, and fundamental rights
2. **Estimate** risks under intended use and reasonably foreseeable misuse
3. **Evaluate** risks against [ORGANIZATION]'s risk appetite and tolerance thresholds
4. **Treat** risks through avoidance, mitigation, transfer, or acceptance
5. **Document** the assessment, treatment decisions, and residual risk
6. **Review** at planned intervals and on significant changes

### 8.2 AI System Impact Assessment

An AI System Impact Assessment (AISIA) must be conducted before deploying any new AI system or significantly changing an existing one, evaluating:

| Impact Dimension | Assessment Questions |
|-----------------|---------------------|
| **Individuals** | Could the system cause physical, psychological, or economic harm to individuals? |
| **Groups** | Could the system discriminate against or disproportionately affect specific groups? |
| **Society** | Could the system affect democratic processes, public discourse, or social cohesion? |
| **Environment** | Could the system have significant environmental impacts? |
| **Fundamental Rights** | Could the system affect privacy, non-discrimination, freedom of expression, or other fundamental rights? |

### 8.3 Fundamental Rights Impact Assessment (FRIA)

For deployers of high-risk AI systems under EU AI Act Article 27, a FRIA must be conducted before deployment, assessing:
- The intended purpose and context of use
- The categories of affected persons and groups
- The potential impacts on fundamental rights
- The measures to mitigate identified risks

---

## Section 9: Monitoring, Enforcement, and Incident Management

**Maps to:** NIST-MS, NIST-MG · ISO-9, ISO-10 · EU-12, EU-15

### 9.1 Monitoring and Metrics

[ORGANIZATION] monitors AI system usage through:
- Network logs and DLP controls
- Access audits and usage reports from approved platforms
- Behavioral analytics for agentic AI systems
- Model performance metrics (accuracy, drift, bias indicators)
- Incident rates and governance KPIs

Key metrics reported to the AI Governance Committee:
- Number of AI systems by risk tier and autonomy level
- Policy violation rates
- Incident frequency and severity
- Vendor risk distribution
- Training completion rates
- Time to detect and respond to AI incidents

### 9.2 Enforcement

| Violation Category | Examples | Consequence |
|-------------------|----------|-------------|
| **Minor** | Using unapproved AI tool for non-sensitive data | Warning, retraining |
| **Moderate** | Entering confidential data into public AI tool | Suspension of AI access, formal warning |
| **Serious** | Entering regulated data into unauthorized AI tool; disabling AI security controls | Disciplinary action up to termination, legal review |
| **Critical** | Deliberate circumvention of AI governance controls; agentic AI operating outside constraints | Immediate suspension, legal action, regulatory notification |

### 9.3 Incident Management

AI-related incidents include:
- Data exposure through AI tool usage
- Harmful, biased, or discriminatory AI output
- Agentic AI operating outside defined constraints
- AI system compromise or adversarial manipulation
- Vendor AI service breach or data misuse

Incident response process:
1. **Detect and Report**: Any personnel who discover an AI-related incident must report it to [reporting contact] promptly. Good-faith reporting will not result in penalty.
2. **Contain**: Activate kill-switch for agentic AI; block access to affected AI tools; preserve evidence.
3. **Assess**: Determine scope, impact, and affected parties.
4. **Remediate**: Implement corrective actions, notify affected parties and regulators if required.
5. **Learn**: Conduct post-incident review, update controls, and share lessons learned.

### 9.4 Record-Keeping and Logging

- AI system logs must be maintained for all Tier 3 and Tier 4 systems (EU AI Act Article 12).
- Logs must include: inputs, outputs, decisions, human overrides, and system events.
- Logs must be tamper-evident and retained for the regulatory minimum period.
- Records of risk assessments, impact assessments, and approvals must be maintained as documented information under ISO 42001 Clause 7.5.

---

## Section 10: Training, Awareness, and Continuous Improvement

**Maps to:** NIST-GV · ISO-7, ISO-10 · EU-13 (AI literacy)

### 10.1 AI Literacy and Training

All personnel must complete AI awareness training before using AI tools for work, covering:
- This policy and its requirements
- Data classification and what may be entered into AI tools
- Recognizing AI-related risks (hallucination, bias, data exposure)
- Incident reporting procedures
- EU AI Act AI literacy obligations (applicable since February 2025)

Role-specific training:
- **AI system developers**: Secure AI development, bias testing, red teaming
- **AI system operators**: Human oversight requirements, output validation, incident response
- **AI Governance Committee**: Risk assessment, regulatory compliance, governance best practices
- **Agentic AI owners**: Agent-specific controls, runtime monitoring, kill-switch operation

### 10.2 Continuous Improvement

- This policy is reviewed [annually] by the AI Governance Committee, and additionally when:
  - A significant new AI tool or agent is adopted
  - The regulatory position changes
  - After any significant AI incident
  - On significant changes to the organization's AI estate
- Nonconformities and corrective actions are recorded and tracked to completion (ISO 42001 Clause 10).
- The AI management system is continually improved based on audit findings, incident lessons, and stakeholder feedback.

---

## Annex A: Approved AI Tool Register

| Tool Name | Vendor | Risk Tier | Approved Data Classifications | Approved Uses | Owner | Review Date |
|-----------|--------|-----------|------------------------------|---------------|-------|--------------|
| [Tool 1] | [Vendor] | [Tier] | [Data tiers] | [Uses] | [Owner] | [Date] |
| [Tool 2] | [Vendor] | [Tier] | [Data tiers] | [Uses] | [Owner] | [Date] |

## Annex B: Agent Registry

| Agent ID | Name | Owner | Risk Tier | Autonomy Level | Tool Permissions | Budget Caps | Review Date |
|----------|------|-------|-----------|---------------|-----------------|-------------|-------------|
| [ID] | [Name] | [Owner] | [Tier] | [L1-L5] | [Permissions] | [Caps] | [Date] |

## Annex C: Risk Tiering Matrix

| Use Case | Risk Tier | Autonomy Level | Required Controls | Approval Authority |
|----------|-----------|---------------|-------------------|-------------------|
| [Use case] | [Tier] | [Level] | [Controls] | [Authority] |

## Annex D: Incident Response Quick Reference

| Incident Type | Immediate Action | Escalation | Regulatory Notification |
|--------------|-----------------|------------|------------------------|
| Data exposure via AI tool | Block tool, preserve logs | DPO + CISO within 4 hours | If personal data: supervisory authority within 72 hours |
| Agentic AI out of constraints | Activate kill-switch | AI Governance Committee within 1 hour | If high-risk AI: competent authority per EU AI Act Art. 73 |
| Harmful/biased AI output | Halt distribution, assess impact | AI Governance Committee within 24 hours | If fundamental rights impact: assess FRIA obligations |
| Vendor AI breach | Suspend vendor access | Legal + CISO immediately | Contractual breach notification per DPA |

## Annex E: Framework Cross-Reference Matrix

| Policy Section | NIST AI RMF | ISO/IEC 42001 | EU AI Act |
|---------------|-------------|---------------|-----------|
| 1. Purpose, Scope, Definitions | GV.1, GV.2 | 4.1, 4.3, 5.2 | Art. 3 (definitions) |
| 2. Governance Structure | GV.2, GV.3, GV.4 | 5.1, 5.3, A.3 | Art. 17 (QMS) |
| 3. Risk Classification | MP.1, MP.2 | 6.1, A.5 | Art. 6, 9, 26 |
| 4. Data Governance | MP.3, MP.4 | 8.5, A.7 | Art. 10, 13 |
| 5. Human Oversight | GV.5, MG.1 | 8.5, A.9 | Art. 13, 14 |
| 6. Agentic AI Governance | GV.1–GV.6, MP.1–MP.4, MS.1–MS.4, MG.1–MG.4 | 8.5, A.6, A.9 | Art. 9, 14 |
| 7. Third-Party/Vendor | MP.4, MG.3 | 8.1, A.10 | Art. 26 |
| 8. Risk & Impact Assessment | MP.1, MP.2, MS.1 | 6.1, 8.2, 8.4, A.5 | Art. 9, 27 |
| 9. Monitoring & Incidents | MS.1–MS.4, MG.1–MG.4 | 9.1, 9.2, 9.3, 10.1, 10.2 | Art. 12, 15 |
| 10. Training & Improvement | GV.4, GV.6 | 7.2, 7.3, 10.1 | Art. 13 (AI literacy) |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | [Author] | Initial release |

**Approved by:** [Approving Body]  
**Effective date:** [Date]  
**Next review:** [Date + 12 months]  
**Document owner:** [Role]

---

*This template is provided as a starting point and should be adapted to the specific legal, regulatory, and operational context of [ORGANIZATION]. It does not constitute legal advice. Consult qualified legal counsel before adoption.*
