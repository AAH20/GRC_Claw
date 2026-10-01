# ISO/IEC 42001:2023 — Comprehensive Implementation Deep-Dive

> **For:** GRC_Claw — ISO 42001 implementation landscape research
> **Date:** October 2026
> **Standard:** ISO/IEC 42001:2023 (published 18 December 2023)
> **Price:** CHF 225 (PDF + ePub)

---

## 1. What Is ISO/IEC 42001:2023?

ISO/IEC 42001 is the **world's first international management system standard for artificial intelligence**. It specifies requirements for establishing, implementing, maintaining, and continually improving an **AI Management System (AIMS)** within an organization. It applies to any entity that develops, provides, or uses AI systems.

- **Published:** 18 December 2023
- **Technical Committee:** ISO/IEC JTC 1/SC 42 (Artificial Intelligence)
- **Structure:** 10 clauses + Annex A (normative controls) + Annex B (implementation guidance) + Annex C (AI objectives) + Annex D (mapping to ISO 27001/27701)
- **Certification:** Voluntary, via accredited certification bodies
- **Methodology:** Plan-Do-Check-Act (PDCA), Annex SL high-level structure

---

## 2. Clause-by-Clause Requirements (Clauses 4–10)

Clauses 1–3 are non-auditable (scope, normative references, terms). Clauses 4–10 carry the requirements.

### Clause 4 — Context of the Organization
| Sub-clause | Requirement |
|---|---|
| 4.1 | Understand the organization and its context (internal/external issues affecting AIMS) |
| 4.2 | Understand needs and expectations of interested parties |
| 4.3 | Determine the scope of the AI management system |
| 4.4 | Establish, implement, maintain, continually improve and document the AIMS |

### Clause 5 — Leadership
| Sub-clause | Requirement |
|---|---|
| 5.1 | Top management must demonstrate leadership and commitment to the AIMS |
| 5.2 | Establish an AI policy (approved by top management, aligned with organizational purpose) |
| 5.3 | Assign and communicate roles, responsibilities, and authorities |

### Clause 6 — Planning
| Sub-clause | Requirement |
|---|---|
| 6.1 | Address risks and opportunities (including AI risk assessment and AI impact assessment) |
| 6.1.2 | **AI impact assessment** — a unique requirement not found in ISO 27001 |
| 6.1.3 | Determine controls needed; compare with Annex A; justify in Statement of Applicability |
| 6.2 | Establish AI objectives and plan to achieve them |

### Clause 7 — Support
| Sub-clause | Requirement |
|---|---|
| 7.1 | Provide resources (human, infrastructure, technology) |
| 7.2 | Ensure competence of persons affecting AIMS performance |
| 7.3 | Awareness of AI policy and responsibilities |
| 7.4 | Communication (internal and external) |
| 7.5 | Documented information (control, retention, disposal) |

### Clause 8 — Operation
| Sub-clause | Requirement |
|---|---|
| 8.1 | Operational planning and control |
| 8.2 | **AI risk assessment** — perform at planned intervals or on significant change |
| 8.3 | **AI risk treatment** — implement risk treatment plan, manage residual risk |
| 8.4 | **AI impact assessment** — assess impacts on individuals, groups, and society |

### Clause 9 — Performance Evaluation
| Sub-clause | Requirement |
|---|---|
| 9.1 | Monitor, measure, analyze, and evaluate AIMS performance |
| 9.2 | Internal audit (planned intervals, impartial auditors) |
| 9.3 | Management review (top management reviews AIMS at planned intervals) |

### Clause 10 — Improvement
| Sub-clause | Requirement |
|---|---|
| 10.1 | Continual improvement of AIMS suitability, adequacy, and effectiveness |
| 10.2 | Nonconformity and corrective action |

---

## 3. Annex A — The 38 Reference Controls (9 Control Areas)

Annex A is **normative** — organizations select controls from it via the Statement of Applicability (SoA). Controls are numbered starting at .2 in each area (the .1 position holds the control objective).

### A.2 — Policies Related to AI (3 controls)
| Ref | Control |
|---|---|
| A.2.2 | AI policy |
| A.2.3 | Alignment with other organizational policies |
| A.2.4 | Review of the AI policy |

### A.3 — Internal Organization (2 controls)
| Ref | Control |
|---|---|
| A.3.2 | AI roles and responsibilities |
| A.3.3 | Reporting of concerns |

### A.4 — Resources for AI Systems (5 controls)
| Ref | Control |
|---|---|
| A.4.2 | Resource documentation |
| A.4.3 | Data resources |
| A.4.4 | Tooling resources |
| A.4.5 | System and computing resources |
| A.4.6 | Human resources |

### A.5 — Assessing Impacts of AI Systems (4 controls)
| Ref | Control |
|---|---|
| A.5.2 | AI system impact assessment process |
| A.5.3 | Documentation of AI system impact assessments |
| A.5.4 | Assessing AI system impact on individuals or groups |
| A.5.5 | Assessing societal impacts of AI systems |

### A.6 — AI System Life Cycle (9 controls — largest area)
| Ref | Control |
|---|---|
| A.6.1.2 | Objectives for responsible development of AI system |
| A.6.1.3 | Processes for responsible AI system design and development |
| A.6.2.2 | AI system requirements and specification |
| A.6.2.3 | Documentation of AI system design and development |
| A.6.2.4 | AI system verification and validation |
| A.6.2.5 | AI system deployment |
| A.6.2.6 | AI system operation and monitoring |
| A.6.2.7 | AI system technical documentation |
| A.6.2.8 | AI system recording of event logs |

### A.7 — Data for AI Systems (5 controls)
| Ref | Control |
|---|---|
| A.7.2 | Data for development and enhancement of AI system |
| A.7.3 | Acquisition of data |
| A.7.4 | Quality of data for AI systems |
| A.7.5 | Data provenance |
| A.7.6 | Data preparation |

### A.8 — Information for Interested Parties (4 controls)
| Ref | Control |
|---|---|
| A.8.2 | System documentation and information for users |
| A.8.3 | External reporting |
| A.8.4 | Communication of incidents |
| A.8.5 | Information for interested parties |

### A.9 — Use of AI Systems (3 controls)
| Ref | Control |
|---|---|
| A.9.2 | Processes for responsible use of AI systems |
| A.9.3 | Objectives for responsible use of AI system |
| A.9.4 | Intended use of the AI system |

### A.10 — Third-Party and Customer Relationships (3 controls)
| Ref | Control |
|---|---|
| A.10.2 | Allocating responsibilities |
| A.10.3 | Suppliers |
| A.10.4 | Customers |

**Total: 38 controls across 9 control areas (A.2–A.10)**

---

## 4. Relationship to ISO 27001 and ISO 27701

### Shared Architecture
All three standards use the **Annex SL / Harmonized Structure** — identical clause numbering (4–10), shared terminology, and the same PDCA cycle. This enables integrated management systems.

### What Each Protects
| Standard | Protects | Risk Model |
|---|---|---|
| ISO 27001 | Information assets (CIA) | Threats × vulnerabilities on assets |
| ISO 27701 | PII (extends 27001) | Privacy rights + regulatory compliance |
| ISO 42001 | Stakeholders affected by AI | Impact of AI decisions on individuals/groups/society |

### Integration Reality
- Organizations with a mature ISO 27001 ISMS already satisfy **~30–45%** of ISO 42001 effort
- The remaining **55–70%** is AI-specific: AI policy, AI impact assessment, AI risk assessment, Annex A controls
- **Annex D of ISO 42001** provides explicit mapping to ISO 27001 and 27701 controls
- Shared elements: context analysis, leadership, internal audit, management review, document control, competence/training, continual improvement
- Standard-specific: Annex A control inventories, AI impact assessments (42001) vs. privacy impact assessments (27701) vs. security risk assessments (27001)

### ISO 27701:2025 Update
The second edition of ISO 27701 (published 2025) is now a **standalone** management system standard — ISO 27001 is no longer a prerequisite, though integration remains typical.

---

## 5. ISO/IEC 42006:2025 — Certification Body Requirements

Published **7 July 2025**, this standard specifies additional requirements for bodies that audit and certify AIMS. It supplements ISO/IEC 17021-1 with:
- AI-specific auditor competence requirements
- Audit time calculation methods for AIMS
- Conflict of interest rules (certification bodies cannot consult on AIMS)
- Criteria for accreditation bodies assessing AIMS certifiers

---

## 6. Accredited Certification Bodies (as of mid-2026)

### ANAB (US) — Largest accreditor
| Body | Date | Notable Clients |
|---|---|---|
| Schellman | Sep 2024 (first) | AWS, Anthropic, IBM, Snowflake, Workday |
| A-LIGN | Oct 2024 | Synthesia, Writer, Autodesk |
| SGS | Apr 2025 | OrionStar Robotics |
| Coalfire | Apr 2025 | — |
| TÜV Rheinland NA | Sep 2025 | — |
| DEKRA | Nov 2025 | — |
| DQS | Feb 2026 | — |
| BSI | Mar 2026 | KPMG Australia, Darktrace, SAP |

### UKAS (UK)
| Body | Date |
|---|---|
| BSI | Late 2025 (first UKAS) |
| LRQA | Feb 2026 |
| NQA | 2026 |

### Other Accreditation Bodies
- **RvA** (Netherlands): BSI, DNV, TÜV NORD
- **JAS-ANZ** (Australia/NZ): Intertek SAI Global
- **SAC** (Singapore): TÜV SÜD PSB
- **IAS** (US): Mastermind Assurance
- **BELAC** (Belgium): BDO

### Notable Certified Organizations
KPMG Australia (first globally, Oct 2024), Synthesia, AWS, Google (Vertex AI, Gemini), Anthropic, Microsoft (Copilot), Workday, Cohere, Autodesk, IBM (Granite — first open-source model developer), Red Hat, SAP, CrowdStrike, Salesforce (Agentforce).

### Certification Process
1. **Gap analysis** (optional, 1–4 weeks)
2. **Implementation** (3–12 months)
3. **Stage 1 audit** (1–3 days) — documentation review
4. **Stage 2 audit** (3–10 days) — operational evidence, interviews, sampling
5. **Certificate** (valid 3 years, annual surveillance audits)
6. **Recertification** (every 3 years)

### Typical Costs
- Consulting: $10,000–$80,000
- Certification audit: $15,000–$50,000 (year one)
- Internal labor (50-person co.): 300–600 hours
- Annual surveillance: 25–40% of initial fees

---

## 7. ISO 42001 and the EU AI Act

### Critical Distinction
- **ISO 42001** is a voluntary, international **organization-level** management system standard
- **EU AI Act** is binding **product-level** regulation (Regulation (EU) 2024/1689)
- ISO 42001 certification does **NOT** confer presumption of conformity under Article 40

### Why No Presumption of Conformity
1. ISO 42001 was not developed under a Commission standardisation request
2. No harmonised standard has been cited in the OJEU for the AI Act (as of Oct 2026)
3. Architectural mismatch: ISO 42001 governs organizations; AI Act regulates individual AI systems as products

### The Harmonised Standards Pipeline
- **CEN-CENELEC JTC 21** is developing ~10 harmonised standards under Commission request M/613
- **prEN 18286** (AI QMS for AI Act) — entered public enquiry Oct 2025, publication targeted late 2026
- Once cited in OJEU, these will provide presumption of conformity with Article 17 (QMS) and Articles 8–15

### Practical Value of ISO 42001 for AI Act
- Provides management scaffolding that Article 17 assumes (policy, roles, competence, documented info, internal audit, continual improvement)
- Controls map closely to AI Act obligations (risk management Art. 9, data governance Art. 10, transparency Art. 13, human oversight Art. 14, accuracy/robustness Art. 15)
- Certified organizations will convert cleanly to presumption when harmonised standards land

---

## 8. Implementation Guides & Toolkits

### Free/Open-Source Toolkits

| Resource | Type | Link |
|---|---|---|
| **ISO 42001 Lead Implementer Toolkit** (icdfa) | GitHub — 4 case studies, complete implementer toolkit, templates, decision trees | github.com/icdfa/iso-42001-lead-implementer-toolkit |
| **ISO 42001 AI Governance Toolkit** (Ankit-Uniyal) | GitHub — all 10 clauses, 38 controls, SoA, ethics framework, legal register, GRC scripts | github.com/Ankit-Uniyal/iso-42001-ai-governance-toolkit |
| **ISO 42001 UK/EU Rapid Compliance** | GitHub — gap analysis CLI, EU AI Act scope checker, policy validator, risk register | github.com/uk-ai-compliance-os/iso42001-uk-eu-rapid-compliance |
| **ISO 42001 Visual Library** | GitHub — infographic cards for clauses, Annex A, audit readiness | github.com/nelsambrose/ISO-42001-Visual-Library |
| **ISO 42001 AIMS Links & Resources** | GitHub — curated vendor-agnostic resource collection | github.com/robertfels/iso-42001-aims-links-and-resources |
| **EU AI Act Crosswalk Tool** | GitHub — interactive mapping of EU AI Act to NIST AI RMF and ISO 42001 | github.com/SuhanaSayyad/eu-ai-act-crosswalk-tool |
| **ISMS CORE Platform** | GitHub — live compliance dashboard for ISO 27001/27701/42001, Docker, 44 connectors | github.com/isms-core-project/isms-core-platform |
| **GSDC Free Toolkit** | Free — gap analysis checklist, 100+ audit questionnaire, Book of Knowledge | gsdcouncil.org/toolkit/iso-42001-free-toolkit |
| **ISOCentral Gap Analysis Tool** | Free — self-assessment workbook, weighted scoring, auto-action plan | isocentral.org/resources/iso-42001-gap-analysis-tool |
| **Audit Workshop Free Templates** | Free — legal register, risk register, SoA, impact assessment, AI policy, gap analysis | auditworkshop.com/free-resources/iso-42001 |
| **Security Scientist Toolkit** | Free — gap assessment, risk register, roadmap, scope, policy, roles, impact assessment, lifecycle, data, transparency | securityscientist.net/blog/iso-42001-ai-management-toolkit |

### Commercial Toolkits

| Toolkit | Price | Contents |
|---|---|---|
| **ISO42001Toolkit.com** | $199+ | All 38 controls, SoA, 23 AIMS documents, risk register, audit checklist |
| **GovernanceDocs** | ~$200+ | 67 templates (policies, procedures, forms, registers) |
| **ISO-Toolkits.org** | $356 | 128 files across 12 folders |
| **Notion ISO 42001 Kit** | Marketplace | 32 editable Notion pages |
| **Apptega Compliance Guide** | PDF | Clause-by-clause with acceptance criteria, evidence, common failures |
| **GSDC Compliance Toolkit** | PDF | 38-page checklist, cost ranges, 12-month timeline |

### Paid Software Platforms
- **Modulos** — cross-framework mapping (implement once, satisfy 27001 + 42001)
- **Vanta** — compliance automation (ISO 42001 support)
- **Drata** — compliance automation
- **Sprinto** — compliance automation with ISO 42001 module

---

## 9. Key Implementation Documents Required

The standard mandates these documented information items:
1. AIMS scope statement
2. AI policy
3. AI objectives
4. AI risk assessment methodology
5. AI risk treatment plan
6. Statement of Applicability (SoA) — all 38 Annex A controls with status
7. AI impact assessment process and records
8. Interested parties register
9. Obligations register (legal/regulatory)
10. Competence requirements and records
11. Internal audit program and reports
12. Management review minutes
13. Incident and concern management records
14. Continual improvement records

---

## 10. Implementation Roadmap (Typical)

| Phase | Duration | Key Activities |
|---|---|---|
| 1. Mobilize | Months 1–2 | Executive sponsorship, scope, AI policy, steering committee, inventory existing 27001/27701 |
| 2. Design | Months 3–5 | Risk methodology, AI system inventory, impact assessment process, SoA |
| 3. Implement | Months 6–9 | Deploy controls, lifecycle gates, data governance, training |
| 4. Internal Audit | Month 10 | Full internal audit, management review, corrective actions |
| 5. Certification | Months 11–12 | Stage 1 + Stage 2 audits, certificate issuance |

**With existing ISO 27001:** 4–6 months typical
**From scratch:** 6–12 months typical
**Small organizations:** 3–4 months

---

## 11. Key Differences from ISO 27001

| Aspect | ISO 27001 | ISO 42001 |
|---|---|---|
| Annex A controls | 93 (4 themes) | 38 (9 areas) |
| Risk focus | Information security | AI-specific (bias, transparency, societal impact) |
| Unique requirement | — | AI impact assessment (Clause 6.1.2, 8.4) |
| Asset focus | Information assets | AI systems and their stakeholders |
| Supporting standard | ISO 27002 (implementation guidance) | Annex B (implementation guidance) |
| Product certification | No | Yes, via ISO/IEC 17065 + Annex A |

---

## 12. Related Standards in the ISO AI Ecosystem

| Standard | Purpose |
|---|---|
| ISO/IEC 22989 | AI concepts and terminology |
| ISO/IEC 23053 | Framework for AI systems using ML |
| ISO/IEC 23894 | AI risk management guidance |
| ISO/IEC 42001 | AI management system (certifiable) |
| ISO/IEC 42005 | AI system impact assessment |
| ISO/IEC 42006 | Requirements for AIMS audit/certification bodies |
| ISO/IEC 38500 | Corporate governance of IT |
| ISO/IEC 38507 | Governance implications of AI |

---

## Sources

1. [ISO/IEC 42001:2023 — Official ISO page](https://www.iso.org/standard/42001)
2. [ISO/IEC 42006:2025 — Requirements for AIMS audit and certification bodies](https://www.iso.org/standard/42006)
3. [ISO 42001 Explained — ISO](https://www.iso.org/en/home/insights-news/resources/iso-42001-explained-what-it-is.html)
4. [ISO 42001 vs ISO 27001 — Modulos](https://docs.modulos.ai/frameworks/comparison/iso-42001-vs-iso-27001)
5. [ISO 42001, 27001, 27701 Integrated Management — Zertia](https://zertia.ai/resources/brochures/iso-42001-27001-and-27701-building-an-integrated-management-system)
6. [ISO 42001 Certification Bodies — Atoro](https://atoro.io/iso-42001-certification-bodies)
7. [ISO 42001 Annex A Controls — DeepInspect](https://www.deepinspect.ai/blog/iso-42001-annex-a-controls)
8. [ISO 42001 Controls — Konfirmity](https://www.konfirmity.com/blog/iso-42001-controls)
9. [ISO 42001 and EU AI Act — Law and Technology](https://lawandtechnology.eu/en/iso-iec-42001-and-the-ai-act-why-certification-is-not-yet-a-presumption-of-conformity)
10. [ISO 42001 Implementation Guide — ISO42k](https://iso42k.com/guide)
11. [ISO 42001 Complete Guide — ISO42001Toolkit.com](https://iso42001toolkit.com/iso-42001-complete-guide.html)
12. [ISO 42001 Lead Implementer Toolkit — GitHub](https://github.com/icdfa/iso-42001-lead-implementer-toolkit)
13. [ISO 42001 AI Governance Toolkit — GitHub](https://github.com/Ankit-Uniyal/iso-42001-ai-governance-toolkit)
14. [ISO 42001 UK/EU Rapid Compliance — GitHub](https://github.com/uk-ai-compliance-os/iso42001-uk-eu-rapid-compliance)
15. [ISO 42001 Visual Library — GitHub](https://github.com/nelsambrose/ISO-42001-Visual-Library)
16. [ISO 42001 AIMS Links & Resources — GitHub](https://github.com/robertfels/iso-42001-aims-links-and-resources)
17. [EU AI Act Crosswalk Tool — GitHub](https://github.com/SuhanaSayyad/eu-ai-act-crosswalk-tool)
18. [ISMS CORE Platform — GitHub](https://github.com/isms-core-project/isms-core-platform)
19. [ISO 42001 Gap Analysis Tool — ISOCentral](https://isocentral.org/resources/iso-42001-gap-analysis-tool)
20. [ISO 42001 Free Templates — Audit Workshop](https://auditworkshop.com/free-resources/iso-42001)
21. [ISO 42001 AI Management Toolkit — Security Scientist](https://securityscientist.net/blog/iso-42001-ai-management-toolkit)
22. [ISO 42001 Compliance Guide — Apptega](https://cdn.prod.website-files.com/6572d2f981a1bbada672a306/6974066f2b04a98bf324f5ad_Apptega%20Compliance%20Guide%20-%20ISO%2042001%20draft%20v1.pdf)
23. [ISO 42001 Primer — GSDC](https://gsdcdata.gsdcouncil.org/gsdc/pdf/GSDC-ISO-42001-Primer-page.pdf)
24. [ISO 42001 Implementation Roadmap — GSDC](https://gsdcdata.gsdcouncil.org/gsdc/pdf/iso-42001-implementation-roadmap.pdf)
25. [ISO 42001 Clause-by-Clause — Certify Consulting](https://certify.consulting/blog/iso-42001-clause-by-clause-breakdown)
26. [ISO 42001 Requirements — Cloud Security Alliance](https://cloudsecurityalliance.org/articles/what-are-the-iso-42001-requirements)
27. [ISO 42001 vs EU AI Act — TCSA](https://tcsa.in/learn/iso-42001-vs-eu-ai-act)
28. [ISO 42001 Accreditation — TCSA](https://tcsa.in/learn/iso-42001-accredited-certification)
29. [ISO 42001 Certification Bodies — ISO42k](https://iso42k.com/certifiers)
30. [ISO 42001 Certification Bodies — ISO Central](https://isocentral.org/resources/accredited-iso-42001-certification-bodies)
