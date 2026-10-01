# GRC_Claw RACI-Plus Framework — Detailed Role Descriptions & Competency Requirements

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Proposed for GRC_Claw Wave 2  
**Parent Document:** ai-governance-raci-plus-framework.md  
**Training Reference:** grc-claw-ai-training-framework.md

---

## 1. Role Responsibility Matrix

### 1.1 Chief AI Officer (CAIO)

| Attribute | Detail |
|---|---|
| **Primary Accountability** | AI strategy, governance program, board reporting |
| **Reports To** | CEO / Board AI Committee |
| **Direct Reports** | AI Governance Lead, AI Ethics Officer, AI Incident Manager |
| **Framework Mapping** | Forrester ✓ · CTAIO ✓ · COMPEL ✓ · ISO 42001 Top mgmt sponsor |

**Core Responsibilities:**
- Define and maintain enterprise AI strategy aligned with business objectives
- Own the AI governance charter and policy framework
- Serve as primary liaison between Board AI Committee and operational teams
- Approve all AI use cases at Gate 1 (concept) and Gate 2 (pre-build)
- Set governance standards, intake criteria, and risk classification thresholds
- Certify ISO 42001 conformance and manage certification cycle
- Convene emergency governance sessions when stop authority is exercised
- Report AI risk posture, program maturity, and incident trends to Board quarterly

**Decision Rights:**
- Approve/reject any AI use case at any gate
- Veto vendor model selection on governance grounds
- Require mandatory rollback of any AI system
- Declare AI incidents and trigger enterprise response
- Recommend policy exceptions to Board
- Approve budgets ≤$1M per system, ≤$5M per program

**Stop Authority:** Any AI system — governance non-compliance, risk appetite breach, regulatory exposure. Immediate effect.

---

### 1.2 Chief Information Security Officer (CISO)

| Attribute | Detail |
|---|---|
| **Primary Accountability** | AI security controls, model protection, incident response |
| **Reports To** | CEO / CIO |
| **Direct Reports** | Security engineering, SOC, threat intelligence |
| **Framework Mapping** | Forrester ✓ · CTAIO ✓ · COMPEL ✓ · ISO 42001 Information security |

**Core Responsibilities:**
- Define AI security architecture and control baseline (model encryption, access controls, API security)
- Lead security assessment of AI systems at Gate 2 and pre-deployment review
- Own adversarial ML defense: prompt injection, model extraction, data poisoning countermeasures
- Lead security incident response for AI systems (breach, adversarial attack, unauthorized access)
- Approve vendor/model security posture before procurement
- Maintain AI threat landscape monitoring and vulnerability management
- Define data residency and sovereignty requirements for AI workloads
- Conduct red-team exercises on production AI systems

**Decision Rights:**
- Block any deployment on security grounds
- Approve or reject vendor model security posture
- Trigger rollback for security incidents
- Declare security incidents
- Require security architecture review for high-risk systems

**Stop Authority:** Any AI system with security risk — active incident, data breach, adversarial attack, unauthorized access. Technical kill switch. Immediate effect.

---

### 1.3 Chief Risk Officer (CRO)

| Attribute | Detail |
|---|---|
| **Primary Accountability** | AI risk appetite, enterprise risk register |
| **Reports To** | CEO / Board Risk Committee |
| **Direct Reports** | Enterprise risk, operational risk, model risk |
| **Framework Mapping** | Forrester ✓ · CTAIO ✓ · COMPEL ✓ · ISO 42001 Risk management |

**Core Responsibilities:**
- Define and maintain enterprise AI risk appetite statement
- Own the AI risk register and ensure all systems are classified and tracked
- Assign risk tiers (Low/Medium/High/Critical) to all AI systems
- Monitor aggregated portfolio risk against appetite thresholds
- Require risk treatment plans for Medium and above risk systems
- Report risk posture, trend analysis, and appetite breaches to Board
- Define model risk validation standards for financial services use cases
- Lead quarterly risk review board meetings

**Decision Rights:**
- Assign risk tiers to all AI systems
- Accept residual risk at enterprise level
- Require portfolio review when aggregated risk exceeds appetite
- Tighten performance thresholds based on risk assessment
- Recommend risk appetite changes to Board
- Block deployment on risk grounds (joint with CAIO for Gate 1)

**Stop Authority:** Portfolio-level risk — aggregated risk exceeds appetite, systemic failure pattern. 24-hour window.

---

### 1.4 General Counsel (GC)

| Attribute | Detail |
|---|---|
| **Primary Accountability** | Regulatory compliance, legal risk, contracts |
| **Reports To** | CEO |
| **Direct Reports** | Legal team, compliance counsel, contracts |
| **Framework Mapping** | Forrester ✓ · CTAIO ✓ · COMPEL ✓ · ISO 42001 Legal/regulatory |

**Core Responsibilities:**
- Interpret AI regulations (EU AI Act, sectoral laws) and map to internal controls
- Approve all AI-related contracts, vendor agreements, and data processing agreements
- Approve regulatory notifications and manage regulator relationships
- Assess legal exposure of AI use cases at intake and pre-deployment
- Manage litigation hold and legal discovery for AI systems
- Approve customer-facing AI communications and disclosures
- Advise on IP, liability, and intellectual property issues in AI procurement
- Lead legal response to AI incidents with regulatory implications

**Decision Rights:**
- Approve or block any AI contract or vendor agreement
- Approve regulatory notifications
- Veto customer-facing features on legal grounds
- Approve policy exceptions with legal implications
- Issue litigation holds on AI systems
- Block deployment on regulatory violation grounds

**Stop Authority:** Any AI system with legal exposure — regulatory violation, litigation hold, contract breach. Legal hold. Immediate effect.

---

### 1.5 Data Protection Officer (DPO)

| Attribute | Detail |
|---|---|
| **Primary Accountability** | Privacy conformance, DPIA, data subject rights |
| **Reports To** | GC (functionally independent per GDPR) |
| **Direct Reports** | Privacy engineering, data governance |
| **Framework Mapping** | COMPEL ✓ · ISO 42001 Privacy |

**Core Responsibilities:**
- Conduct and review Data Protection Impact Assessments (DPIAs) for all AI systems processing personal data
- Define data residency and cross-border transfer requirements
- Manage data subject rights requests (access, erasure, portability) for AI systems
- Approve lawful basis for AI training and inference data processing
- Monitor compliance with GDPR, CCPA, and sectoral privacy regulations
- Liaise with data protection authorities on AI-related matters
- Define data minimization and purpose limitation controls for AI pipelines
- Review vendor data processing agreements for privacy compliance

**Decision Rights:**
- Block any dataset on privacy grounds
- Veto data residency decisions
- Approve or reject DPIAs
- Declare privacy incidents
- Require privacy engineering review for high-risk systems
- Approve privacy-specific regulatory notifications

**Stop Authority:** Any AI system processing personal data — unlawful processing, DPIA failure, data subject rights violation. Privacy block. Immediate effect.

---

### 1.6 AI Ethics Officer

| Attribute | Detail |
|---|---|
| **Primary Accountability** | Fairness, transparency, bias audits, model cards |
| **Reports To** | CAIO |
| **Direct Reports** | Ethics review board, fairness engineering |
| **Framework Mapping** | CTAIO ✓ |

**Core Responsibilities:**
- Define and maintain AI ethics principles and review criteria
- Conduct bias audits and fairness assessments for all High and Critical risk systems
- Review and approve model cards for completeness and accuracy
- Lead AI Ethics Committee meetings and stakeholder engagement
- Assess human rights impact of AI use cases at intake
- Define transparency and explainability requirements by risk tier
- Investigate ethics complaints and whistleblower reports
- Publish annual AI transparency report

**Decision Rights:**
- Block deployment on rights grounds (discriminatory output, rights violation)
- Veto use cases with unacceptable ethics risk
- Require human review for specific AI decisions
- Approve ethics principles and review criteria
- Request ethics impact assessment for any system

**Stop Authority:** Any AI system with rights impact — discriminatory output, rights violation, unethical use case. Before deployment only.

---

### 1.7 AI Governance Lead / CoE Lead

| Attribute | Detail |
|---|---|
| **Primary Accountability** | Governance operations, policy, standards, training |
| **Reports To** | CAIO |
| **Direct Reports** | Governance analysts, policy managers, training coordinators |
| **Framework Mapping** | Forrester ✓ · COMPEL ✓ · ISO 42001 AI governance lead |

**Core Responsibilities:**
- Operate the AI intake process and manage use-case pipeline
- Maintain governance policies, standards, and procedures
- Coordinate gate reviews and ensure timely decision-making
- Maintain the RACI-plus matrix and role assignments
- Design and deliver role-based training programs (per training framework)
- Manage governance tooling: ticketing, model registry, CI/CD gates
- Track governance metrics and report to CAIO and Board
- Manage policy exception process and documentation
- Coordinate internal and external audit responses

**Decision Rights:**
- Recommend use case approval/rejection to CAIO
- Block model cards on completeness grounds
- Require HITL threshold adjustments
- Recommend policy exceptions
- Suspend intake process for process improvement
- Escalate gate review overdue items to CAIO

**Stop Authority:** No direct stop authority — escalates to CAIO or relevant C-role.

---

### 1.8 Business Unit AI Owner

| Attribute | Detail |
|---|---|
| **Primary Accountability** | Business outcome, residual risk acceptance per system |
| **Reports To** | BU Head / CAIO (dotted line) |
| **Direct Reports** | ML Lead (technical), Product Manager (UX) |
| **Framework Mapping** | Forrester ✓ · CTAIO ✓ · COMPEL ✓ · ISO 42001 Model/product owner |

**Core Responsibilities:**
- Define business requirements and success metrics for AI systems
- Accept residual risk for owned AI systems (Low tier independently, Medium with CAIO)
- Approve datasets, model selection, and model cards for owned systems
- Trigger voluntary rollback when business risk or performance failure warrants
- Set HITL thresholds and performance thresholds for owned systems
- Approve customer-facing AI communications and disclosures
- Manage vendor relationships for AI system components
- Ensure business continuity and disaster recovery for AI systems
- Report system performance and business value to CAIO

**Decision Rights:**
- Approve datasets for owned systems
- Select and approve models for owned systems
- Approve model cards
- Accept residual risk (Low: independent; Medium: with CAIO)
- Trigger voluntary rollback
- Set HITL and performance thresholds
- Approve customer messaging (with GC for legal content)
- Approve budgets ≤$500K per system

**Stop Authority:** Own AI systems — business risk, performance failure, continuity threat. Voluntary rollback. Immediate effect.

---

### 1.9 ML / Data Engineering Lead

| Attribute | Detail |
|---|---|
| **Primary Accountability** | Model building, data pipelines, MLOps, evaluation |
| **Reports To** | BU AI Owner |
| **Direct Reports** | ML engineers, data engineers, MLOps engineers |
| **Framework Mapping** | Forrester ✓ · COMPEL ✓ · ISO 42001 Engineering lead |

**Core Responsibilities:**
- Design and build ML models and data pipelines for AI systems
- Execute model training, evaluation, and validation per governance standards
- Maintain MLOps infrastructure: CI/CD, model registry, monitoring
- Implement security and privacy controls in ML pipelines
- Produce and maintain model documentation and model cards
- Execute rollback procedures when triggered
- Investigate model anomalies and performance degradation
- Ensure data quality, provenance, and lineage for training data
- Implement monitoring for drift, bias, and performance metrics

**Decision Rights:**
- Technical model selection recommendations
- Technical execution budget allocation
- Anomaly investigation execution
- Rollback execution
- Monitoring configuration and alerting thresholds

**Stop Authority:** No direct stop authority — recommends to BU AI Owner or CISO.

---

### 1.10 Head of Compliance

| Attribute | Detail |
|---|---|
| **Primary Accountability** | Regulatory mapping, attestations, external reporting |
| **Reports To** | GC |
| **Direct Reports** | Compliance analysts, regulatory affairs |
| **Framework Mapping** | COMPEL ✓ |

**Core Responsibilities:**
- Map AI regulations to internal controls and maintain regulatory compliance matrix
- Prepare regulatory attestations and external reports for AI systems
- Manage relationships with sectoral regulators
- Monitor regulatory changes and assess impact on AI systems
- Prepare evidence for regulatory notifications (supports GC)
- Conduct compliance reviews of AI systems against regulatory requirements
- Maintain compliance documentation and evidence for audits
- Advise on sector-specific requirements (healthcare, financial services, employment)

**Decision Rights:**
- Prepare regulatory notifications (GC approves)
- Recommend compliance controls
- Flag regulatory non-compliance
- Request compliance reviews

**Stop Authority:** No direct stop authority — escalates to GC.

---

### 1.11 Head of Product

| Attribute | Detail |
|---|---|
| **Primary Accountability** | User-facing AI experience, disclosures, trust UX |
| **Reports To** | CPO / BU Head |
| **Direct Reports** | Product managers, UX designers, AI UX researchers |
| **Framework Mapping** | COMPEL ✓ |

**Core Responsibilities:**
- Design user-facing AI experiences with appropriate transparency and disclosures
- Implement consent mechanisms and user controls for AI features
- Define UX patterns for AI limitations, confidence indicators, and fallback options
- Ensure accessibility and inclusive design for AI features
- Collaborate with AI Ethics Officer on user trust and transparency
- Define product requirements for HITL interfaces and human oversight
- Monitor user feedback and trust metrics for AI features
- Approve user-facing AI feature descriptions and marketing claims

**Decision Rights:**
- Approve UX design and user-facing disclosures
- Define product requirements for AI features
- Approve user-facing communications (with GC for legal review)
- Request user research and usability testing

**Stop Authority:** No direct stop authority — escalates to BU AI Owner or GC.

---

### 1.12 Internal Audit

| Attribute | Detail |
|---|---|
| **Primary Accountability** | Independent assurance, control effectiveness |
| **Reports To** | Audit Committee (functionally), CAIO (administratively) |
| **Direct Reports** | IT auditors, data analytics auditors |
| **Framework Mapping** | COMPEL ✓ · ISO 42001 Internal audit |

**Core Responsibilities:**
- Plan and execute internal audits of AI governance controls
- Evaluate effectiveness of RACI-plus implementation and gate processes
- Assess compliance with AI policies, standards, and regulatory requirements
- Review model risk management and validation controls
- Report audit findings and recommendations to Audit Committee
- Track corrective action closure for audit findings
- Provide independent assurance on AI control effectiveness
- Support external audit and certification activities

**Decision Rights:**
- Define audit scope and plan
- Issue audit findings and recommendations
- Request corrective actions
- Access all AI governance records and evidence
- Escalate critical findings to Audit Committee

**Stop Authority:** No direct stop authority — recommends to Audit Committee or CAIO.

---

### 1.13 Board AI Committee

| Attribute | Detail |
|---|---|
| **Primary Accountability** | Enterprise risk appetite, policy approval, oversight |
| **Reports To** | Board of Directors |
| **Direct Reports** | None (governance body) |
| **Framework Mapping** | Forrester ✓ · CTAIO ✓ · COMPEL ✓ · ISO 42001 Top management |

**Core Responsibilities:**
- Approve enterprise AI policy and governance charter
- Set and revise AI risk appetite statement
- Approve High and Critical risk AI use cases
- Review AI strategy, program maturity, and incident trends
- Approve policy exceptions with enterprise impact
- Oversee AI governance effectiveness and CAIO performance
- Approve enterprise AI budget (> $1M per system)
- Receive and act on escalated incidents and risk breaches

**Decision Rights:**
- Approve/reject AI policy
- Set risk appetite
- Approve High/Critical risk use cases
- Approve policy exceptions
- Override CAIO decisions
- Approve enterprise AI budget
- Direct strategic redirection of AI program

**Stop Authority:** Any AI system — strategic risk, reputational threat, fiduciary concern. Board directive. Next board session.

---

### 1.14 AI Incident Manager

| Attribute | Detail |
|---|---|
| **Primary Accountability** | AI incident triage, coordination, escalation |
| **Reports To** | CAIO |
| **Direct Reports** | Incident response coordinators |
| **Framework Mapping** | ISO 42001 Incident manager |

**Core Responsibilities:**
- Maintain AI incident response plan and playbooks
- Triage and coordinate response to AI incidents
- Classify incident severity and activate appropriate response teams
- Manage incident timeline, evidence preservation, and communication
- Escalate incidents per escalation thresholds to CAIO, GC, Board
- Conduct post-incident reviews and lessons learned
- Maintain incident register and trend analysis
- Conduct tabletop exercises to test incident response readiness
- Coordinate with CISO on security incidents and DPO on privacy incidents

**Decision Rights:**
- Activate incident response teams
- Classify incident severity
- Request stop authority exercise by relevant roles
- Escalate incidents per thresholds
- Convene post-incident reviews

**Stop Authority:** No direct stop authority — coordinates with roles that have stop authority.

---

## 2. Competency Requirements Per Role

### 2.1 Competency Dimension Definitions

| Level | Definition | Evidence |
|---|---|---|
| **Awareness** | Can explain concepts and implications | Completion of awareness training, policy acknowledgment |
| **Working** | Can apply knowledge to governance decisions | Scenario assessment, supervised practice, artifact production |
| **Advanced** | Can design controls, lead initiatives, mentor others | Independent project delivery, control design, mentoring record |
| **Expert** | Can shape organizational strategy, represent externally, testify to regulators | Strategy authorship, external representation, regulatory testimony |

### 2.2 Detailed Competency Matrix

#### Chief AI Officer (CAIO)

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| AI Governance Frameworks | Expert | NIST AI RMF, EU AI Act, ISO 42001, board governance | Board presentation, strategy artifact review |
| AI Strategy | Expert | Competitive analysis, capability roadmap, investment prioritization | Strategy document, board approval record |
| ML Lifecycle | Working | Model development, deployment, monitoring concepts | Technical review participation |
| Risk Appetite | Expert | Risk quantification, appetite setting, board reporting | Risk appetite statement, board minutes |
| Regulatory Landscape | Expert | EU AI Act, sectoral regulations, enforcement trends | Regulatory update briefings |
| Executive Communication | Expert | Board reporting, stakeholder management, crisis communication | Board presentation evaluation |
| Budget Management | Advanced | Program budgeting, ROI analysis, vendor negotiation | Budget approval records |
| Organizational Leadership | Expert | Cross-functional influence, change management, talent development | 360-degree feedback, program outcomes |

#### Chief Information Security Officer (CISO)

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| AI Security Architecture | Expert | Model encryption, API security, adversarial ML defense | Security architecture review |
| Adversarial ML | Expert | Prompt injection, model extraction, data poisoning | Red-team exercise leadership |
| Security Regulations | Expert | GDPR security requirements, NIST 800-53, ISO 27001 | Compliance assessment |
| Incident Response | Expert | AI-specific incident response, forensics, crisis management | Incident response exercise |
| Cross-Functional Coordination | Advanced | Working with legal, engineering, governance teams | Incident coordination records |
| Threat Intelligence | Advanced | AI threat landscape, vulnerability management | Threat briefing quality |
| Security Tooling | Advanced | SIEM, DLP, model monitoring tools | Tool deployment and configuration |

#### Chief Risk Officer (CRO)

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| Enterprise Risk Management | Expert | ERM frameworks, risk appetite, risk culture | Risk framework documentation |
| AI Risk Taxonomy | Expert | AI-specific risk categories, classification, measurement | Risk register review |
| Model Risk | Working | Model validation, drift concepts, performance risk | Model risk assessment review |
| Risk Quantification | Expert | Quantitative risk analysis, scenario modeling | Risk quantification reports |
| Board Reporting | Advanced | Risk dashboard design, trend analysis, escalation | Board risk reports |
| Risk Culture Building | Advanced | Training, awareness, behavioral change | Training completion, culture survey |
| Portfolio Risk Management | Advanced | Aggregated risk monitoring, correlation analysis | Portfolio risk reports |

#### General Counsel (GC)

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| AI Regulation | Expert | EU AI Act, sectoral laws, liability, IP | Legal opinion quality |
| Contract Law | Expert | AI vendor contracts, data processing agreements | Contract review and negotiation |
| Regulatory Interpretation | Expert | Regulatory guidance analysis, enforcement trends | Regulatory update briefings |
| Litigation Management | Expert | Litigation hold, discovery, evidence preservation | Incident legal response |
| Executive Communication | Advanced | Board reporting, crisis communication | Board presentation evaluation |
| AI Capabilities Awareness | Awareness | Understanding of AI capabilities and limitations | Technical briefing participation |
| Cross-Functional Collaboration | Advanced | Working with engineering, product, governance | Incident coordination records |

#### Data Protection Officer (DPO)

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| Privacy Law | Expert | GDPR, CCPA, sectoral privacy regulations | DPIA quality, regulatory liaison |
| DPIA | Expert | Data protection impact assessment methodology | DPIA review and approval |
| Privacy by Design | Expert | Privacy engineering, data minimization, purpose limitation | Privacy architecture review |
| Data Pipelines | Working | Data flow mapping, training data lineage | Data flow documentation review |
| Data Subject Rights | Expert | Access, erasure, portability request handling | DSR response records |
| Regulator Liaison | Expert | Data protection authority relationships | Regulatory correspondence |
| Cross-Functional Integration | Advanced | Embedding privacy in engineering and product | Privacy review participation |

#### AI Ethics Officer

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| Fairness Frameworks | Expert | Fairness metrics, bias detection, mitigation strategies | Bias audit reports |
| Ethics Principles | Expert | AI ethics frameworks, human rights impact | Ethics review quality |
| Bias Metrics | Advanced | Statistical fairness, demographic parity, equalized odds | Bias assessment methodology |
| Explainability | Advanced | Model interpretability, transparency techniques | Model card review |
| Model Cards | Advanced | Documentation standards, completeness criteria | Model card approval records |
| Human Rights Impact | Advanced | Rights-based assessment, stakeholder engagement | HRIA reports |
| Stakeholder Engagement | Advanced | Community engagement, complaint handling | Stakeholder feedback |
| Training Delivery | Advanced | Ethics training design and delivery | Training effectiveness evaluation |

#### AI Governance Lead / CoE Lead

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| Governance Frameworks | Expert | NIST AI RMF, ISO 42001, policy design | Policy document quality |
| Policy Design | Expert | Policy drafting, standards development, procedure design | Policy approval records |
| ML Lifecycle | Working | Model development, deployment, monitoring concepts | Gate review participation |
| Compliance Mapping | Advanced | Regulatory mapping, control design, audit support | Compliance matrix quality |
| Program Management | Advanced | Program planning, stakeholder management, metrics | Program milestone delivery |
| Training Design | Advanced | Curriculum development, effectiveness evaluation | Training program outcomes |
| Tooling | Working | GRC platforms, ticketing, model registry | Tool configuration and operation |

#### Business Unit AI Owner

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| Governance Processes | Working | Intake, risk acceptance, gate review participation | Gate review records |
| System Capabilities | Working | AI system capabilities, limitations, performance metrics | System review participation |
| Business Risk | Advanced | Business impact assessment, continuity planning | Risk acceptance documentation |
| Business Case Development | Advanced | ROI analysis, benefit realization, value tracking | Business case approval records |
| Vendor Management | Working | Vendor selection, relationship management, SLA management | Vendor performance reviews |
| Cross-Functional Collaboration | Advanced | Working with ML, product, governance teams | Project delivery records |
| Risk Acceptance | Advanced | Residual risk evaluation, treatment plan oversight | Risk register entries |

#### ML / Data Engineering Lead

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| Model Development | Expert | ML algorithms, training, evaluation, optimization | Model performance metrics |
| MLOps | Expert | CI/CD, model registry, deployment automation | Pipeline deployment records |
| Data Engineering | Expert | Data pipelines, quality, provenance, lineage | Data quality metrics |
| Model Evaluation | Expert | Evaluation methodology, bias testing, robustness | Evaluation reports |
| Governance Requirements | Working | Documentation, model cards, compliance | Model card quality |
| Security Controls | Working | Secure coding, access controls, encryption | Security review participation |
| Technical Leadership | Advanced | Team leadership, mentoring, architecture decisions | Team feedback, architecture reviews |

#### Head of Compliance

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| Regulatory Obligations | Expert | AI regulations, sectoral requirements, control mapping | Compliance matrix quality |
| Control Mapping | Expert | Regulatory-to-control mapping, gap analysis | Control assessment reports |
| Attestations | Expert | Regulatory attestation preparation, evidence management | Attestation approval records |
| External Reporting | Expert | Regulatory reporting, disclosure management | Report quality and timeliness |
| AI System Types | Awareness | Understanding of AI system categories and risks | Technical briefing participation |
| Regulatory Relationships | Advanced | Regulator engagement, industry participation | Regulatory correspondence |
| Audit Support | Advanced | Audit evidence preparation, finding response | Audit support records |

#### Head of Product

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| AI UX Patterns | Working | Transparency patterns, confidence indicators, fallback UX | UX design review |
| User Trust | Advanced | Trust metrics, user research, feedback analysis | User trust survey results |
| Disclosure Requirements | Working | Regulatory disclosures, consent mechanisms | Disclosure compliance review |
| Governance Requirements | Working | Policy compliance, gate review participation | Gate review records |
| Cross-Functional Collaboration | Advanced | Working with engineering, governance, legal | Project delivery records |
| User Advocacy | Advanced | User-centered design, accessibility, inclusive design | Accessibility audit results |

#### Internal Audit

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| Audit Standards | Expert | IIA standards, ISO 19011, audit methodology | Audit plan and report quality |
| AI Controls | Working | AI governance controls, model risk, data governance | Control evaluation quality |
| Data Analytics | Working | Audit data analysis, anomaly detection, sampling | Analytics output quality |
| Control Evaluation | Expert | Control design and operating effectiveness | Audit finding quality |
| Independence | Expert | Objectivity, conflict management, ethical conduct | Independence declarations |
| Audit Committee Reporting | Advanced | Committee reporting, finding escalation | Committee presentation quality |
| AI Governance Frameworks | Expert | NIST AI RMF, ISO 42001, RACI-plus | Framework review quality |

#### Board AI Committee

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| Fiduciary Duty | Expert | Corporate governance, fiduciary responsibilities | Board decision quality |
| AI Oversight | Expert | AI risk oversight, strategy evaluation, performance monitoring | Board minutes quality |
| AI Capabilities | Awareness | Understanding of AI capabilities, risks, opportunities | Board education participation |
| Risk Appetite | Expert | Risk appetite setting, tolerance definition | Risk appetite statement quality |
| Regulatory Landscape | Expert | AI regulation trends, enforcement, liability | Regulatory update briefings |
| Governance Oversight | Expert | Governance effectiveness evaluation, CAIO performance | Governance review outcomes |

#### AI Incident Manager

| Competency | Level | Specific Requirements | Assessment Method |
|---|---|---|---|
| Incident Response Frameworks | Working | Incident classification, response playbooks, coordination | Incident response exercise |
| AI Failure Modes | Advanced | Model failure, drift, adversarial attack, data quality | Incident investigation quality |
| Forensics | Advanced | Log analysis, evidence preservation, root cause analysis | Forensic investigation reports |
| Notification Requirements | Advanced | Regulatory notification timelines, stakeholder communication | Notification timeliness records |
| Crisis Coordination | Expert | Cross-functional coordination, communication, decision-making | Incident coordination records |
| Tabletop Exercises | Advanced | Exercise design, facilitation, findings tracking | Exercise reports and closure |

---

## 3. Authority Calibration Guide

### 3.1 Budget Authority Matrix

| Role | Approval Limit | Delegation Authority | Reporting Requirement | Emergency Provision |
|---|---|---|---|---|
| **Board AI Committee** | Unlimited (enterprise AI budget) | Delegates to CAIO | Board approval required | Emergency session with 4-hour notice |
| **CAIO** | ≤$1M per system, ≤$5M per program | Delegates to BU AI Owner | Reports to Board quarterly | Can approve up to $2M with CFO concurrence |
| **BU AI Owner** | ≤$500K per system | Delegates to ML Lead (technical execution) | Reports to CAIO monthly | Can approve up to $750K with CAIO notification |
| **CFO** | >$1M per system | — | Reports to Board | — |
| **ML Lead** | Technical execution budget only | — | Reports to BU AI Owner | — |

**Budget Authority Rules:**
1. All budget approvals require documented business case
2. Emergency provisions require post-approval review within 5 business days
3. Delegation must be documented and is revocable
4. Budget overruns >15% auto-escalate to CAIO + CFO
5. Multi-system programs require CAIO approval regardless of individual system cost

### 3.2 Risk Acceptance Authority Matrix

| Risk Level | Acceptable By | Documentation Required | Review Frequency | Escalation Trigger |
|---|---|---|---|---|
| **Low** | BU AI Owner | Risk register entry | Annual | Any incident or material change |
| **Medium** | CAIO | Risk register + treatment plan | Semi-annual | Treatment plan failure or incident |
| **High** | CAIO + CRO | Risk register + treatment plan + Board notification | Quarterly | Any incident or appetite breach |
| **Critical** | Board | Board minute + risk assessment | Per incident | Immediate Board notification |

**Risk Acceptance Rules:**
1. Risk acceptance must be documented with rationale and conditions
2. Acceptance expires at review frequency if not reaffirmed
3. Any incident automatically triggers risk level review
4. Risk aggregation across systems is monitored by CRO
5. Risk appetite breaches escalate to Board within 24 hours

### 3.3 Decision Latency Standards

| Decision Type | Maximum Latency | Escalation if Exceeded | Authority for Extension | Documentation Required |
|---|---|---|---|---|
| **Incident response** | 1 hour | Auto-escalate to CAIO | CAIO (up to 2 hours) | Incident record with timeline |
| **Gate review (standard)** | 5 business days | Escalate to CAIO | CAIO (up to 5 additional days) | Gate tracking record |
| **Gate review (high-risk)** | 10 business days | Escalate to Board | Board (case-by-case) | Gate tracking + risk assessment |
| **Policy exception** | 10 business days | Escalate to Board | Board (case-by-case) | Exception request with rationale |
| **Vendor approval** | 15 business days | Escalate to CFO | CFO (up to 10 additional days) | Vendor assessment record |
| **Regulatory notification** | Per regulation (typically 72 hours) | Auto-escalate to GC + Board | GC (with regulator liaison) | Notification timeline record |
| **Stop authority review** | 5 business days | Escalate to Board | Board (case-by-case) | Stop record with review timeline |
| **Risk acceptance (Medium)** | 10 business days | Escalate to CAIO + CRO | CAIO (up to 10 additional days) | Risk assessment + treatment plan |
| **Risk acceptance (High)** | 5 business days | Escalate to Board | Board (case-by-case) | Risk assessment + Board notification |

### 3.4 Authority Conflict Resolution

| Conflict Scenario | Resolution Mechanism | Final Arbiter |
|---|---|---|
| CAIO vs. CRO on risk tier | Joint review with Board notification | Board AI Committee |
| CISO vs. BU AI Owner on security | CAIO mediates; CISO has stop authority | CAIO (uphold or override) |
| DPO vs. BU AI Owner on data use | GC mediates; DPO has privacy block | GC (uphold or override) |
| GC vs. CAIO on regulatory interpretation | Board notification | Board AI Committee |
| Ethics Officer vs. CAIO on rights | Board notification | Board AI Committee |
| ML Lead vs. CoE on model card | BU AI Owner mediates; CoE has block | BU AI Owner (uphold or override) |
| Any role vs. Board decision | Board decision stands | Board AI Committee |

---

## 4. Escalation Procedures

### 4.1 Risk-Based Escalation Procedures

#### Procedure R-1: High Risk Tier Escalation (EU AI Act Art. 6)

**Trigger:** Risk classification determines High risk tier

**Procedure:**
1. CoE Lead flags High risk classification at intake
2. CRO confirms risk tier assignment
3. CAIO notified within 1 business day
4. Board AI Committee notified at next meeting (or within 5 business days for urgent cases)
5. Enhanced due diligence required: extended DPIA, human oversight plan, robustness testing
6. Gate 1 and Gate 2 reviews require CAIO + CRO joint approval
7. Quarterly risk review mandatory

**Evidence Required:** Risk assessment, classification record, enhanced DPIA, human oversight plan

---

#### Procedure R-2: Prohibited Risk Tier Escalation (EU AI Act Art. 5)

**Trigger:** Use case falls under EU AI Act Art. 5 prohibited practices

**Procedure:**
1. CoE Lead identifies prohibited practice at intake
2. CAIO notified immediately
3. GC provides legal opinion within 2 business days
4. Board AI Committee convenes emergency session within 5 business days
5. Go/no-go vote by Board
6. If proceed: enhanced controls, legal opinion documentation, Board minute
7. If reject: use case rejected, documentation archived

**Evidence Required:** Legal opinion, risk assessment, Board minute

---

#### Procedure R-3: Special-Category Personal Data Escalation (GDPR Art. 9)

**Trigger:** AI system processes special-category personal data

**Procedure:**
1. DPO identifies special-category data at intake
2. DPO + BU AI Owner become joint Accountable
3. Enhanced DPIA required before Gate 1
4. Lawful basis determination documented
5. Data Protection Authority consultation may be required
6. Quarterly privacy review mandatory

**Evidence Required:** DPIA, lawful basis determination, data flow mapping

---

#### Procedure R-4: Regulated Industry Escalation

**Trigger:** AI system in regulated industry (medical, credit, employment)

**Procedure:**
1. Head of Compliance identifies regulatory jurisdiction at intake
2. GC + BU AI Owner become joint Accountable
3. Regulatory mapping completed before Gate 1
4. Sector-specific controls implemented
5. Regulator notification may be required before deployment
6. Compliance review at each gate

**Evidence Required:** Regulatory mapping, compliance assessment, regulator correspondence

---

#### Procedure R-5: Portfolio Risk Appetite Breach

**Trigger:** Aggregated portfolio risk exceeds appetite threshold

**Procedure:**
1. CRO identifies breach at quarterly review (or immediately if sudden)
2. CRO notifies CAIO within 1 business day
3. CAIO notifies Board within 24 hours
4. Risk Review Board convenes within 5 business days
5. Options: appetite revision, risk rebalancing, system retirement
6. Board decision on appetite revision
7. Implementation plan with timeline

**Evidence Required:** Portfolio risk report, trend analysis, Board minute

---

### 4.2 Incident-Based Escalation Procedures

#### Procedure I-1: Customer Harm from AI Output

**Trigger:** Customer reports harm from AI system output

**Procedure:**
1. AI Incident Manager triages within 1 hour
2. BU AI Owner notified immediately
3. CAIO + GC notified within 4 hours
4. Board notified within 24 hours for High/Critical risk systems
5. Customer communication approved by BU AI Owner + GC
6. Remediation plan developed within 5 business days
7. Post-incident review within 14 days
8. Lessons learned briefing within 14 days of closure

**Evidence Required:** Incident record, customer impact assessment, remediation plan, post-incident review

---

#### Procedure I-2: Regulator Inquiry or Complaint

**Trigger:** Regulator contacts organization about AI system

**Procedure:**
1. GC notified immediately upon receipt
2. CAIO notified within 1 business day
3. Board notified within 1 business day
4. Legal assessment completed within 2 business days
5. Response strategy developed by GC + CAIO
6. Regulatory notification if required (per regulation timeline)
7. All communications coordinated through GC

**Evidence Required:** Legal assessment, regulator communication records, response documentation

---

#### Procedure I-3: Data Breach Involving AI System

**Trigger:** Data breach affecting AI system data

**Procedure:**
1. CISO + DPO notified immediately
2. CAIO + GC notified within 1 hour
3. Board notified within 1 hour
4. Breach assessment completed within 24 hours
5. Regulatory notification within 72 hours (GDPR)
6. Customer notification if required
7. Forensic investigation initiated
8. Remediation plan within 5 business days

**Evidence Required:** Breach assessment, DPIA reference, notification records, forensic report

---

#### Procedure I-4: Model Failure with Safety Implications

**Trigger:** Model failure causing or risking safety harm

**Procedure:**
1. ML Lead detects failure and notifies BU AI Owner
2. BU AI Owner triggers immediate rollback if warranted
3. CAIO + CISO + CRO notified within 1 hour
4. Technical assessment completed within 24 hours
5. Root cause analysis within 5 business days
6. Remediation and re-gate required before redeployment
7. Post-incident review within 14 days

**Evidence Required:** Technical assessment, impact analysis, root cause analysis, re-gate record

---

#### Procedure I-5: Vendor Model Deprecation or Incident

**Trigger:** Vendor notifies of model deprecation, incident, or material change

**Procedure:**
1. BU AI Owner receives notification
2. Impact assessment completed within 2 business days
3. CAIO + CISO + GC joint triage within 3 business days
4. Decision: accept, mitigate, or replace
5. If replace: re-trigger Gate 2
6. Customer notification if required
7. Contract review for SLA remedies

**Evidence Required:** Vendor notification, impact assessment, triage record, decision documentation

---

#### Procedure I-6: Adversarial Attack on AI System

**Trigger:** Active adversarial attack detected

**Procedure:**
1. CISO detects attack via monitoring or threat intelligence
2. CISO activates incident response immediately
3. CAIO + GC notified within 1 hour
4. Technical containment within 4 hours
5. Forensic investigation initiated
6. Regulatory notification if data breach involved
7. Post-incident review within 14 days
8. Control improvements implemented

**Evidence Required:** Security assessment, attack analysis, forensic report, control improvement record

---

### 4.3 Change-Based Escalation Procedures

#### Procedure C-1: Material Model Change

**Trigger:** New base model, new training data class, or new deployment region

**Procedure:**
1. ML Lead identifies material change
2. Change assessment completed before implementation
3. Re-trigger Gate 2 with CAIO as Accountable
4. Updated model card required
5. Risk re-classification if new region or data class
6. Stakeholder notification per change impact

**Evidence Required:** Change assessment, updated model card, Gate 2 record

---

#### Procedure C-2: Budget Overrun

**Trigger:** Budget overrun >15% of approved amount

**Procedure:**
1. BU AI Owner identifies overrun
2. Variance analysis completed within 5 business days
3. CAIO + CFO notified
4. Options: additional funding, scope reduction, or system retirement
5. Decision documented with rationale
6. If additional funding: new budget approval per authority matrix

**Evidence Required:** Budget tracking, variance analysis, decision record

---

#### Procedure C-3: Gate Review Overdue

**Trigger:** Gate review overdue >30 days

**Procedure:**
1. CoE Lead identifies overdue gate
2. Remediation plan requested from BU AI Owner
3. CAIO + Audit Committee notified at 30-day mark
4. If unresolved at 60 days: escalate to Executive Sponsor
5. System may be suspended if critical

**Evidence Required:** Gate tracking, remediation plan, escalation record

---

#### Procedure C-4: Second Consecutive Gate Failure

**Trigger:** System fails gate review for second consecutive time

**Procedure:**
1. CoE Lead documents second failure
2. Executive Sponsor notified
3. Root cause analysis required
4. Remediation plan with timeline
5. Re-gate only after remediation verified
6. If third failure: system retirement recommended

**Evidence Required:** Gate records, remediation history, root cause analysis

---

#### Procedure C-5: Certification Nonconformity

**Trigger:** ISO 42001 major nonconformity identified

**Procedure:**
1. CoE Lead documents nonconformity
2. CAIO + Audit Committee notified within 5 business days
3. Corrective action plan developed within 10 business days
4. Implementation verified within agreed timeline
5. Certification body notified if required
6. Effectiveness review after implementation

**Evidence Required:** Audit finding, corrective action plan, verification record

---

#### Procedure C-6: New AI System Class

**Trigger:** First deployment of new AI system class (agentic, foundation model)

**Procedure:**
1. CAIO identifies new system class
2. Policy gap analysis completed
3. Board notified and policy update requested
4. Interim controls implemented
5. Full governance framework updated within 90 days
6. Retrospective review of first deployment

**Evidence Required:** Risk assessment, policy gap analysis, Board notification, interim controls

---

### 4.4 Escalation Documentation Requirements

Every escalation must be documented with:

| Field | Description |
|---|---|
| **Escalation ID** | Unique identifier |
| **Trigger** | Specific measurable trigger from escalation matrix |
| **Date/Time** | When trigger was identified |
| **From Role** | Default accountable role |
| **To Role** | Escalated accountable role |
| **Evidence** | Supporting documentation attached |
| **Decision** | Outcome of escalation |
| **Resolution** | How the situation was resolved |
| **Reversal** | Whether escalation was reversed and when |
| **Lessons Lear** | Process improvements identified |

---

## 5. Training Requirements

### 5.1 Training Framework Alignment

Training requirements are derived from the GRC_Claw AI Training & Awareness Framework (grc-claw-ai-training-framework.md) and mapped to ISO/IEC 42001:2023 Clauses 7.2 (Competence) and 7.3 (Awareness).

### 5.2 Role-Based Training Requirements

#### Tier 4: Leadership (CAIO, CISO, CRO, GC, Board AI Committee)

| Requirement | Standard | Duration | Frequency | Evidence |
|---|---|---|---|---|
| M12: AI Strategy & Risk Appetite | 7.2 + 7.3 | 4 hrs | Annual + at onboarding | Board paper + strategy artifact |
| GAICC Foundation | 7.2 | 16 hrs | Once + 3-year renewal | Certification |
| Executive AI Governance Briefing | 7.3 | 2 hrs | Semi-annual | Attendance record |
| Regulatory Landscape Update | 7.3 | 1 hr | Quarterly | Acknowledgment |
| Incident Tabletop Exercise | 7.2 | 2 hrs | Annual | Exercise participation |
| Board AI Oversight Workshop | 7.2 | 4 hrs | Annual | Workshop assessment |

**Total Annual Training:** ~29 hours + certification maintenance

---

#### Tier 3: Governance (AI Governance Lead, AI Ethics Officer, DPO, Head of Compliance, Internal Audit, AI Incident Manager)

| Requirement | Standard | Duration | Frequency | Evidence |
|---|---|---|---|---|
| M10: AIMS Implementation | 7.2 | 32 hrs | Once + 3-year renewal | GAICC Lead Implementer certification |
| M11: AIMS Internal Audit | 7.2 | 32 hrs | Once + 3-year renewal | GAICC Internal Auditor certification |
| M09: AI Risk Assessment | 7.2 | 4 hrs | Annual | Risk assessment artifact |
| M13: AI Incident Management | 7.2 + 7.3 | 2 hrs | Annual | Exercise participation |
| Policy Update Briefing | 7.3 | 30 min | Within 30 days of change | Acknowledgment |
| Incident Lessons Learned | 7.3 | 1 hr | Within 14 days of closure | Briefing record |
| Sectoral Regulation Deep-Dive | 7.2 | 4 hrs | Annual | Assessment |
| Ethics Review Workshop | 7.2 | 4 hrs | Annual | Workshop assessment |

**Total Annual Training:** ~80 hours (first year) + ~20 hours (annual refresh) + certification maintenance

---

#### Tier 2: Practitioners (ML Lead, BU AI Owner, Head of Product)

| Requirement | Standard | Duration | Frequency | Evidence |
|---|---|---|---|---|
| M06: Model Governance Fundamentals | 7.2 | 4 hrs | Annual | Workshop assessment + project artifact |
| M07: Data Provenance & Bias | 7.2 | 4 hrs | Annual | Bias assessment report |
| M08: Testing, Validation & Monitoring | 7.2 | 6 hrs | Annual | Evaluation report + monitoring plan |
| M09: AI Risk Assessment | 7.2 | 4 hrs | Annual | Risk assessment artifact |
| IAPP AIGP or GAICC Foundation | 7.2 | 24 hrs | Once + 2-3 year renewal | Certification |
| M13: AI Incident Management | 7.2 + 7.3 | 2 hrs | Annual | Exercise participation |
| Policy Update Briefing | 7.3 | 30 min | Within 30 days of change | Acknowledgment |
| Technical Policy Deep-Dive | 7.3 | 2 hrs | Annual | Acknowledgment |

**Total Annual Training:** ~46 hours (first year) + ~19 hours (annual refresh) + certification maintenance

---

#### Tier 1: AI Users (Business users, analysts, operations staff)

| Requirement | Standard | Duration | Frequency | Evidence |
|---|---|---|---|---|
| M03: AI in Your Role | 7.2 + 7.3 | 2 hrs | Annual + at role change | Scenario assessment + completion |
| M04: Output Validation & Escalation | 7.2 | 2 hrs | Annual | Lab exercise + assessment |
| M05: Data Handling & Classification | 7.2 + 7.3 | 1.5 hrs | Annual | Quiz score + case study |
| M13: AI Incident Management | 7.2 + 7.3 | 2 hrs | Annual | Exercise participation |
| Policy Update Briefing | 7.3 | 30 min | Within 30 days of change | Acknowledgment |
| Approved/Prohibited Use Cases | 7.3 | 1 hr | Annual + at role change | Acknowledgment |

**Total Annual Training:** ~10.5 hours

---

#### Tier 0: All Staff (Every employee, contractor, temporary worker)

| Requirement | Standard | Duration | Frequency | Evidence |
|---|---|---|---|---|
| M01: AI Awareness & Policy | 7.3 | 1 hr | Annual + at onboarding | Completion + policy acknowledgment |
| M02: Responsible AI Use | 7.3 | 1 hr | Annual + at onboarding | Quiz + acknowledgment |
| M13: AI Incident Management | 7.2 + 7.3 | 2 hrs | Annual | Exercise participation |
| Policy Update Briefing | 7.3 | 30 min | Within 30 days of change | Acknowledgment |
| AI Incident Lessons Learned | 7.3 | 30 min | Within 14 days of closure | Briefing record |
| New AI System Announcement | 7.3 | 30 min | At system launch | Communication record |

**Total Annual Training:** ~5 hours

---

### 5.3 Certification Requirements by Role

| Role | Required Certification | Renewal Cycle | Internal Equivalent |
|---|---|---|---|
| CAIO | GAICC Foundation | 3 years | GRC_Claw AI Leadership Badge |
| CISO | GAICC Foundation + security cert (CISSP/CISM) | 3 years | GRC_Claw AI Security Professional Badge |
| CRO | GAICC Foundation | 3 years | GRC_Claw AI Risk Professional Badge |
| GC | GAICC Foundation | 3 years | GRC_Claw AI Legal Professional Badge |
| DPO | GAICC Foundation + IAPP CIPP/E or CIPM | 2-3 years | GRC_Claw AI Privacy Professional Badge |
| AI Ethics Officer | IEEE CertifAIEd or GAICC Foundation | 3 years | GRC_Claw AI Ethics Professional Badge |
| AI Governance Lead | GAICC Lead Implementer | 3 years | GRC_Claw AIMS Professional Badge |
| BU AI Owner | GAICC Foundation | 3 years | GRC_Claw AI Practitioner Badge |
| ML Lead | IAPP AIGP or GAICC Foundation | 2-3 years | GRC_Claw AI Practitioner Badge |
| Head of Compliance | GAICC Foundation | 3 years | GRC_Claw AI Compliance Professional Badge |
| Head of Product | GAICC Foundation | 3 years | GRC_Claw AI Product Professional Badge |
| Internal Audit | GAICC Internal Auditor | 3 years | GRC_Claw AIMS Auditor Badge |
| Board AI Committee | GAICC Foundation (awareness) | 3 years | GRC_Claw AI Leadership Badge |
| AI Incident Manager | GAICC Foundation | 3 years | GRC_Claw AI Incident Professional Badge |

---

### 5.4 Competence Evidence Requirements

Per ISO/IEC 42001:2023 Clause 7.2, each role-holder must maintain:

| Evidence Type | Description | Storage | Retention |
|---|---|---|---|
| Competence matrix | Role-to-competency mapping with required levels | Controlled document | Duration of role + 3 years |
| Training records | Per person, per module: completion date, score, certificate | LMS | Duration of role + 3 years |
| Qualifications | External certifications (GAICC, IAPP, IEEE, CEET) | HR record | Duration of role + 3 years |
| Experience documentation | CV, project assignments, role history | HR record | Duration of role + 3 years |
| Assessed work | Artifacts produced (risk assessments, audit reports, bias evaluations) | GRC platform | Duration of role + 3 years |
| Effectiveness evaluations | Test scores, supervisor assessments, performance reviews | HR record | Duration of role + 3 years |
| Corrective action records | Gaps identified, actions taken, re-evaluation results | HR record | Duration of role + 3 years |

---

### 5.5 Awareness Evidence Requirements

Per ISO/IEC 42001:2023 Clause 7.3, each person must maintain:

| Evidence Type | Description | Storage | Retention |
|---|---|---|---|
| Awareness programme plan | Schedule, audience, content, delivery method | Controlled document | Duration of role + 3 years |
| Completion records | Per person, per awareness activity | LMS | Duration of role + 3 years |
| Policy acknowledgments | Signed/dated acknowledgments of AI policy | GRC platform | Duration of role + 3 years |
| Communication records | Emails, briefings, campaign materials | Document management | Duration of role + 3 years |
| Manager attestations | Confirmation that reinforcement conversations occurred | HR record | Duration of role + 3 years |
| Trigger-based update records | Evidence that policy changes reached affected staff | GRC platform | Duration of role + 3 years |

---

### 5.6 Training Effectiveness Evaluation

| Evaluation Method | Frequency | Audience | Evidence | Target |
|---|---|---|---|---|
| Knowledge test (quiz) | Per module | All | Score record | ≥80% pass rate |
| Scenario assessment | Per role-specific module | Tiers 1-3 | Assessment score + assessor notes | ≥85% pass rate |
| Practical artifact review | Per project | Tiers 2-3 | Artifact quality rating | ≥80% satisfactory |
| Supervisor observation | Semi-annual | Tiers 1-3 | Observation record | ≥90% satisfactory |
| 360-degree feedback | Annual | Tiers 2-3 | Feedback summary | ≥80% positive |
| Incident/audit finding review | Per event | Relevant roles | Finding + corrective action record | 100% closure |
| Training satisfaction survey | Per module | All | Survey results | ≥4.0/5.0 |

---

## 6. Performance Metrics Per Role

### 6.1 CAIO Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| R Program Maturity | AI governance maturity score (1-5) | ≥4.0 by Year 2 | Semi-annual | Maturity assessment |
| Board Reporting Timeliness | % of board reports delivered on time | 100% | Quarterly | Board calendar |
| Gate Decision Latency | Median time from gate submission to decision | ≤5 business days | Monthly | GRC platform |
| Policy Exception Rate | % of decisions requiring policy exception | <5% | Quarterly | GRC platform |
| Training Compliance | % of governance roles current on training | 100% | Quarterly | LMS |
| Incident Response Time | Median time from incident to CAIO engagement | ≤1 hour | Per incident | Incident register |
| Stakeholder Satisfaction | Governance stakeholder satisfaction score | ≥4.0/5.0 | Annual | Survey |

---

### 6.2 CISO Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| Security Assessment Coverage | % of AI systems with current security assessment | 100% | Quarterly | Security register |
| Vulnerability Remediation Time | Median time to remediate critical AI vulnerabilities | ≤7 days | Monthly | Vulnerability register |
| Adversarial Test Coverage | % of High/Critical systems with annual red-team test | 100% | Annual | Red-team report |
| Security Incident Response Time | Median time from detection to containment | ≤4 hours | Per incident | Incident register |
| Security Control Effectiveness | % of security controls passing effectiveness test | ≥95% | Semi-annual | Control test results |
| Vendor Security Review Timeliness | % of vendor security reviews completed within SLA | 100% | Per vendor | Vendor register |

---

### 6.3 CRO Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| Risk Classification Coverage | % of AI systems with current risk classification | 100% | Quarterly | Risk register |
| Risk Appetite Breach Response Time | Median time from breach to Board notification | ≤24 hours | Per breach | Escalation log |
| Risk Treatment Plan Completion | % of Medium+ risk systems with current treatment plan | 100% | Quarterly | Risk register |
| Portfolio Risk Trend | Aggregated portfolio risk score trend | Stable or decreasing | Quarterly | Portfolio risk report |
| Risk Review Board Attendance | % of risk review board meetings with quorum | ≥90% | Monthly | Meeting records |
| Risk Quantification Accuracy | Variance between predicted and actual risk events | ≤20% | Annual | Risk assessment review |

---

### 6.4 GC Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| Contract Review Timeliness | % of AI contracts reviewed within SLA | 100% | Per contract | Contract register |
| Regulatory Notification Timeliness | % of regulatory notifications within legal deadline | 100% | Per notification | Notification log |
| Legal Assessment Turnaround | Median time for legal assessment of AI use case | ≤3 business days | Per assessment | Legal register |
| Litigation Hold Compliance | % of litigation holds executed within 24 hours | 100% | Per hold | Legal hold log |
| Regulatory Change Response | % of regulatory changes assessed within 60 days | 100% | Per change | Regulatory tracking |
| Vendor Contract Risk | % of vendor contracts with AI-specific risk clauses | 100% | Per contract | Contract review |

---

### 6.5 DPO Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| DPIA Coverage | % of personal data systems with current DPIA | 100% | Quarterly | DPIA register |
| DPIA Turnaround | Median time from DPIA request to completion | ≤10 business days | Per DPIA | DPIA register |
| Data Subject Request Response | % of DSRs responded within legal deadline | 100% | Per request | DSR register |
| Privacy Incident Response Time | Median time from detection to notification | ≤72 hours | Per incident | Incident register |
| Privacy Training Completion | % of staff with current privacy training | 100% | Quarterly | LMS |
| Vendor Privacy Review | % of vendors with current privacy assessment | 100% | Per vendor | Vendor register |

---

### 6.6 AI Ethics Officer Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| Bias Audit Coverage | % of High/Critical systems with annual bias audit | 100% | Annual | Audit register |
| Ethics Review Turnaround | Median time for ethics review of use case | ≤5 business days | Per review | Ethics register |
| Model Card Quality | % of model cards meeting completeness criteria | ≥95% | Per model card | Model card review |
| Ethics Complaint Resolution | % of ethics complaints resolved within SLA | 100% | Per complaint | Complaint register |
| Stakeholder Engagement | Number of stakeholder engagement activities | ≥4 per year | Annual | Activity log |
| Transparency Report Publication | Annual transparency report published | 100% | Annual | Publication record |

---

### 6.7 AI Governance Lead / CoE Lead Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| Intake Processing Time | Median time from intake submission to Gate 1 | ≤10 business days | Monthly | GRC platform |
| Gate Review Timeliness | % of gate reviews completed within SLA | ≥90% | Monthly | GRC platform |
| Policy Exception Processing | % of policy exceptions processed within SLA | 100% | Per exception | GRC platform |
| Training Program Delivery | % of training modules delivered per schedule | 100% | Quarterly | LMS |
| RACI Coverage | % of activities with named R and A | 100% | Quarterly | RACI matrix |
| Stakeholder Satisfaction | Governance process satisfaction score | ≥4.0/5.0 | Annual | Survey |
| Audit Finding Closure | % of audit findings closed within SLA | ≥90% | Quarterly | Audit register |

---

### 6.8 Business Unit AI Owner Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| System Performance | AI system performance vs. agreed thresholds | ≥95% within thresholds | Monthly | Monitoring dashboard |
| Risk Acceptance Documentation | % of owned systems with current risk acceptance | 100% | Quarterly | Risk register |
| Incident Response Time | Median time from detection to rollback decision | ≤1 hour | Per incident | Incident register |
| Business Value Delivery | % of business case benefits realized | ≥80% | Semi-annual | Business case review |
| Vendor Management | % of vendors meeting SLA | ≥95% | Quarterly | Vendor register |
| Training Compliance | % of team members current on training | 100% | Quarterly | LMS |
| Model Card Currency | % of model cards updated within 30 days of change | 100% | Monthly | Model registry |

---

### 6.9 ML / Data Engineering Lead Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| Model Performance | Model accuracy/F1 score vs. baseline | ≥95% of baseline | Monthly | Monitoring dashboard |
| Drift Detection Time | Median time from drift onset to detection | ≤24 hours | Per drift event | Monitoring dashboard |
| Pipeline Deployment Frequency | Number of production deployments per month | Trend (stable or increasing) | Monthly | CI/CD logs |
| Rollback Execution Time | Median time from rollback decision to execution | ≤30 minutes | Per rollback | Incident register |
| Data Quality Score | % of training data passing quality checks | ≥98% | Per training run | Data quality report |
| Model Documentation | % of models with complete documentation | 100% | Monthly | Model registry |
| Security Control Implementation | % of security controls implemented per specification | 100% | Per release | Security review |

---

### 6.10 Head of Compliance Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| Regulatory Mapping Coverage | % of AI systems with current regulatory mapping | 100% | Quarterly | Compliance matrix |
| Attestation Timeliness | % of regulatory attestations submitted on time | 100% | Per attestation | Attestation register |
| Compliance Review Coverage | % of High/Critical systems with annual compliance review | 100% | Annual | Compliance register |
| Regulatory Change Response | % of regulatory changes assessed within 60 days | 100% | Per change | Regulatory tracking |
| Audit Support Timeliness | % of audit evidence requests fulfilled within SLA | 100% | Per request | Audit log |
| Training Completion | % of compliance staff current on training | 100% | Quarterly | LMS |

---

### 6.11 Head of Product Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| User Trust Score | AI feature user trust score | ≥4.0/5.0 | Quarterly | User survey |
| Disclosure Compliance | % of AI features with compliant disclosures | 100% | Per release | Disclosure review |
| Accessibility Compliance | % of AI features meeting accessibility standards | 100% | Per release | Accessibility audit |
| User Feedback Response | % of AI-related user feedback addressed within SLA | ≥90% | Monthly | Feedback register |
| Consent Mechanism Coverage | % of AI features with consent mechanism | 100% | Per release | Product review |
| Cross-Functional Collaboration | Product-governance collaboration satisfaction | ≥4.0/5.0 | Annual | Survey |

---

### 6.12 Internal Audit Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| Audit Plan Completion | % of planned audits completed | 100% | Annual | Audit plan |
| Finding Issuance Time | Median time from fieldwork completion to finding issuance | ≤10 business days | Per audit | Audit register |
| Corrective Action Verification | % of corrective actions verified within SLA | 100% | Per finding | Audit register |
| Audit Committee Reporting | % of audit reports delivered on time | 100% | Quarterly | Audit calendar |
| Independence Compliance | % of audits with independence declaration | 100% | Per audit | Audit plan |
| Audit Quality Score | External quality assessment score | ≥85% | Triennial | Quality assessment |

---

### 6.13 Board AI Committee Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| Meeting Cadence | % of scheduled meetings held | 100% | Quarterly | Board calendar |
| Quorum Achievement | % of meetings with quorum | ≥90% | Quarterly | Meeting records |
| Decision Timeliness | % of decisions made within meeting | ≥95% | Quarterly | Meeting minutes |
| Risk Appetite Review | Risk appetite reviewed annually | 100% | Annual | Board minutes |
| Escalation Response | % of escalations addressed within SLA | 100% | Per escalation | Escalation log |
| AI Literacy | % of members completing annual AI education | 100% | Annual | Training records |

---

### 6.14 AI Incident Manager Performance Metrics

| Metric | Definition | Target | Measurement Frequency | Data Source |
|---|---|---|---|---|
| Incident Triage Time | Median time from report to triage completion | ≤1 hour | Per incident | Incident register |
| Escalation Accuracy | % of incidents escalated to correct level | ≥95% | Per incident | Incident register |
| Response Team Activation | % of incidents with response team activated within SLA | 100% | Per incident | Incident register |
| Post-Incident Review Timeliness | % of post-incident reviews completed within 14 days | 100% | Per incident | Incident register |
| Lessons Learned Implementation | % of lessons learned implemented within SLA | ≥90% | Per incident | Lessons learned register |
| Tabletop Exercise Completion | % of planned tabletop exercises completed | 100% | Annual | Exercise register |
| Incident Trend Analysis | Monthly incident trend report published | 100% | Monthly | Incident register |

---

## 7. Role Interaction Protocols

### 7.1 Governance Forums

#### 7.1.1 AI Governance Board

| Attribute | Specification |
|---|---|
| **Chair** | CAIO |
| **Members** | CISO, CRO, GC, DPO, AI Ethics Officer, rotating BU AI Owner |
| **Cadence** | Monthly (full board), quarterly (deep-dive metrics) |
| **Quorum** | 4 of 7 members for decisions |
| **Voting** | Majority for standard; unanimity for policy exceptions |
| **Emergency sessions** | CAIO or CISO may convene with 4-hour notice |
| **Documentation** | Written decisions with rationale, dissenting opinions, follow-up items |

#### 7.1.2 AI Risk Review Board

| Attribute | Specification |
|---|---|
| **Chair** | CRO |
| **Members** | CAIO, CISO, DPO, GC, CoE Lead, relevant BU AI Owner |
| **Cadence** | Bi-weekly (risk review), ad-hoc (incident-driven) |
| **Scope** | Risk register review, exception decisions, incident escalation |
| **Escalation** | To Board AI Committee for risk appetite breaches |

#### 7.1.3 AI Ethics Committee

| Attribute | Specification |
|---|---|
| **Chair** | AI Ethics Officer |
| **Members** | GC, DPO, Head of Product, external stakeholder (rotating) |
| **Cadence** | Monthly |
| **Scope** | Ethics review, bias audit results, rights impact assessments |
| **Authority** | Can block deployment on rights grounds; escalates to Board for policy changes |

### 7.2 Role Interaction Matrix

The following matrix defines the primary interaction patterns between roles:

| Role | Primary Interactions | Interaction Type | Frequency |
|---|---|---|---|
| **CAIO** | Board, CISO, CRO, GC, DPO, CoE, BU Owners | Governance, Strategy, Escalation | Continuous |
| **CISO** | CAIO, ML Lead, BU Owners, AI Incident Manager | Security review, Incident response | Continuous |
| **CRO** | CAIO, Board, BU Owners, CoE | Risk assessment, Portfolio review | Bi-weekly |
| **GC** | CAIO, DPO, Head of Compliance, Board | Legal review, Regulatory notification | As needed |
| **DPO** | CAIO, GC, BU Owners, ML Lead | Privacy review, DPIA | As needed |
| **AI Ethics Officer** | CAIO, GC, DPO, Head of Product | Ethics review, Bias audit | Monthly |
| **AI Governance Lead / CoE** | CAIO, All roles | Governance operations, Policy, Training | Continuous |
| **BU AI Owner** | CAIO, ML Lead, CoE, CISO, DPO | System ownership, Risk acceptance | Continuous |
| **ML / Data Eng Lead** | BU Owner, CoE, CISO | Model development, Evaluation, Deployment | Continuous |
| **Head of Compliance** | CAIO, GC, CoE | Regulatory mapping, Attestations | As needed |
| **Head of Product** | BU Owner, AI Ethics Officer, CoE | User experience, Disclosures | Continuous |
| **Internal Audit** | CAIO, Audit Committee, All roles | Independent assurance, Control evaluation | Per audit cycle |
| **Board AI Committee** | CAIO, CRO, GC | Strategic oversight, Policy approval | Monthly/Quarterly |
| **AI Incident Manager** | CAIO, CISO, GC, DPO, BU Owners | Incident triage, Coordination | Per incident |

### 7.3 Communication Protocols

#### 7.3.1 Standard Communication

| Communication Type | Channels | Response Time | Documentation |
|---|---|---|---|
| Governance decisions | Email + ticketing system | Per decision latency standard | Decision record with rationale |
| Risk escalations | Email + incident management system | <24 hours | Escalation record |
| Policy updates | Email + intranet + acknowledgment system | Within 30 days | Acknowledgment record |
| Training notifications | Email + LMS | Per training schedule | Completion record |
| Incident alerts | Incident management system + phone | <1 hour | Incident record |
| Board reporting | Board portal + email | Per reporting cadence | Board report |

#### 7.3.2 Emergency Communication

| Scenario | Initial Notification | Follow-up | Documentation |
|---|---|---|---|
| Active security incident | CISO → CAIO (immediate) | CAIO → All C-suite (within 1 hour) | Incident record |
| Data breach | CISO + DPO → CAIO + GC (within 1 hour) | CAIO → Board (within 24 hours) | Breach assessment |
| Regulatory inquiry | GC → CAIO (immediate) | CAIO → Board (within 24 hours) | Legal assessment |
| Model failure with safety impact | BU Owner → CAIO + CISO + CRO (immediate) | Joint triage (within 1 hour) | Technical assessment |
| Ethics violation | AI Ethics Officer → CAIO (immediate) | CAIO → Board (within 24 hours) | Ethics assessment |

### 7.4 Decision-Making Protocols

#### 7.4.1 Standard Decision Process

```
1. Proposal Submitted (R role)
       │
       ▼
2. Consultation Phase (C roles)
       │
       ▼
3. Recommendation Compiled (CoE or R role)
       │
       ▼
4. Decision by Accountable Role (A role)
       │
       ▼
5. Notification (I roles)
       │
       ▼
6. Documentation & Implementation
```

#### 7.4.2 Blocking Decision Process

```
1. Block Raised by Authorized Role
       │
       ▼
2. Written Declaration with Rationale
       │
       ▼
3. Notification to CAIO (within 1 hour)
       │
       ▼
4. Evidence Preservation
       │
       ▼
5. Remediation Conditions Specified
       │
       ▼
6. Review by CAIO + Relevant C-roles (within 5 business days)
       │
       ▼
7. Resolution Documented
```

#### 7.4.3 Escalation Decision Process

```
1. Trigger Condition Detected
       │
       ▼
2. Default A Notified
       │
       ▼
3. Trigger Assessed Against Escalation Matrix
       │
       ▼
4. Escalation Decision Made
       │
       ▼
5. New A Engages Within Timing Standard
       │
       ▼
6. Resolution or Further Escalation
       │
       ▼
7. Documentation & Closure
```

### 7.5 Conflict Resolution Protocols

| Conflict Type | Resolution Process | Escalation Path |
|---|---|---|
| Risk acceptance disagreement | CRO and CAIO negotiate; document rationale | Board AI Committee |
| Security vs. speed | CISO and BU Owner negotiate; CAIO decides | Board AI Committee |
| Privacy vs. functionality | DPO and BU Owner negotiate; CAIO decides | Board AI Committee |
| Ethics vs. business | AI Ethics Officer and BU Owner negotiate; CAIO decides | Board AI Committee |
| Compliance vs. innovation | Head of Compliance and BU Owner negotiate; GC decides | Board AI Committee |
| Resource allocation | BU Owners negotiate; CAIO allocates | Board AI Committee |
| Policy interpretation | CoE interprets; GC reviews legal; CAIO decides | Board AI Committee |

### 7.6 Role Handover Protocols

| Scenario | Handover Requirements | Timeline | Documentation |
|---|---|---|---|
| Role vacancy | Interim A named; competency assessment | Within 5 business days | Interim assignment record |
| Role transition | Knowledge transfer; shadowing; handover checklist | 30 days | Handover checklist |
| Temporary absence | Deputy named; authority delegated | Immediate | Delegation record |
| Organizational change | RACI matrix updated; roles reassigned | Within 30 days | Updated RACI matrix |
| New AI system class | Role responsibilities assessed; training updated | Before deployment | Role impact assessment |

---

## 8. Implementation Notes

### 8.1 Role Assignment Rules

1. **One person, multiple roles:** Permitted for small organizations (< 20 AI systems), but accountability must be explicitly documented. Minimum coverage: CAIO + CISO + GC.
2. **Segregation of duties:** The same person cannot be both Responsible and Accountable for the same activity.
3. **Backup designation:** Each role must have a designated backup with current training and competence evidence.
4. **Role acceptance:** Each role-holder must sign a role acceptance document acknowledging responsibilities, authority, and accountability.

### 8.2 Competence Gap Management

| Gap Severity | Action | Timeline | Approval |
|---|---|---|---|
| Minor (single competency below target) | Targeted training | 30 days | Role-holder's manager |
| Moderate (multiple competencies below target) | Development plan + mentoring | 60 days | CAIO |
| Major (role cannot be performed effectively) | Reassignment or hire | Immediate | CAIO + HR |
| Critical (governance failure risk) | Immediate reassignment | 24 hours | CAIO + Board notification |

### 8.3 Annual Review Cycle

| Month | Activity | Responsible |
|---|---|---|
| January | Annual RACI review and role assignment confirmation | CAIO + CoE Lead |
| February | Competence gap analysis and training plan update | CoE Lead + HR |
| March | Authority calibration review (budget, risk, latency) | CAIO + CRO + CFO |
| April | Escalation threshold review and update | CoE Lead + CRO |
| May | Performance metric review and target setting | CAIO + all C-roles |
| June | Mid-year governance effectiveness assessment | Internal Audit |
| July | Training program effectiveness evaluation | CoE Lead |
| August | Role competency reassessment | CoE Lead + HR |
| September | Policy and procedure review | CoE Lead + GC |
| October | Annual tabletop exercise | AI Incident Manager |
| November | Board AI Committee annual review | CAIO + Board |
| December | Annual report and next-year planning | CAIO + CoE Lead |

---

## Appendix A: Role Assignment Template

```
Role: _______________________________
Role-Holder: ________________________
Backup: _____________________________
Effective Date: _____________________
Review Date: _______________________

Responsibilities Acknowledged:          ☐ Yes  ☐ No
Authority Understood:                   ☐ Yes  ☐ No
Stop Authority Understood:              ☐ Yes  ☐ No
Escalation Paths Understood:            ☐ Yes  ☐ No
Training Requirements Acknowledged:     ☐ Yes  ☐ No
Performance Metrics Acknowledged:       ☐ Yes  ☐ No

Signature: ___________________________
Date: _______________________________
```

---

## Appendix B: Document Control

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-10-01 | GRC_Claw Wave 2 | Initial detailed role descriptions, competency requirements, authority calibration, escalation procedures, training requirements, and performance metrics |

---

*This document is a companion to the AI Governance RACI-Plus Framework (ai-governance-raci-plus-framework.md) and the GRC_Claw AI Training & Awareness Framework (grc-claw-ai-training-framework.md). Review annually and on trigger: new regulation, material incident, new AI system class, or reorganization affecting named roles.*
