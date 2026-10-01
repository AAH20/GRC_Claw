# Open-Source AI Governance Landscape Report
## For GRC_Claw Competitive Positioning

---

## 1. FAIRNESS & BIAS TOOLKITS

### 1.1 Fairlearn (Microsoft)
- **License:** MIT
- **GitHub:** fairlearn/fairlearn
- **Capabilities:**
  - Fairness assessment metrics (demographic parity, equalized odds, equal opportunity, bounded group loss)
  - Mitigation algorithms: Reduction-based (ExponentiatedGradient, GridSearch) and Post-processing (ThresholdOptimizer)
  - Group fairness approach focused on allocation harms and quality-of-service harms
  - Jupyter widget dashboard for model comparison
  - Integrates with scikit-learn, pandas, TensorFlow, PyTorch
- **Limitations:** No regulatory mapping, no audit trail generation, no LLM support, no governance workflow

### 1.2 Aequitas (University of Chicago / Center for Data Science and Public Policy)
- **License:** MIT
- **GitHub:** dssg/aequitas (now GapData/aequitas)
- **Capabilities:**
  - Bias and fairness audit toolkit for ML models
  - Multiple reference group selection methods (min metric, major group, predefined)
  - Disparity calculations across population subgroups
  - Fairness determinations with configurable thresholds
  - Web application for non-technical users
  - Designed for data scientists, ML researchers, and policymakers
- **Limitations:** No mitigation algorithms, no regulatory compliance mapping, limited maintenance

### 1.3 AI Fairness 360 (IBM)
- **License:** Apache 2.0
- **GitHub:** Trusted-AI/AIF360
- **Capabilities:**
  - Comprehensive fairness metrics for datasets and models
  - 9+ bias mitigation algorithms across preprocessing, in-processing, and post-processing
  - Python and R support
  - Interactive web experience for guidance
  - Tutorials for credit scoring, medical expenditure, face classification
  - scikit-learn-compatible fit/predict paradigm
- **Limitations:** No regulatory mapping, no audit trail, no LLM support, no governance workflow, moved to LF AI foundation

---

## 2. EXPLAINABILITY TOOLS

### 2.1 SHAP (SHapley Additive exPlanations)
- **License:** MIT
- **GitHub:** shap/shap (~25,500 stars)
- **Capabilities:**
  - Game-theoretic feature attribution using Shapley values
  - Model-agnostic (KernelSHAP) and model-specific (TreeSHAP, DeepSHAP, LinearSHAP, GradientExplainer)
  - Supports tree ensembles, deep learning (PyTorch, TensorFlow/Keras), linear models, NLP transformers
  - Visualization: force plots, waterfall plots, beeswarm plots, dependence plots
  - Unifies LIME, DeepLIFT, Layer-Wise Relevance Propagation under one framework
  - Satisfies local accuracy, missingness, and consistency properties
- **Limitations:** No fairness metrics, no regulatory mapping, no governance workflow, no audit trail

### 2.2 LIME (Local Interpretable Model-Agnostic Explanations)
- **License:** MIT
- **GitHub:** marcotcr/lime (Python), tidymodels/lime (R port)
- **Capabilities:**
  - Local surrogate model explanations for individual predictions
  - Supports text, tabular, and image data
  - Model-agnostic approach
  - R package actively maintained (v0.5.4, Dec 2025)
  - Python reference implementation (last release June 2020 — largely unmaintained)
- **Limitations:** Python version unmaintained, no fairness metrics, no regulatory mapping, no governance workflow

### 2.3 InterpretML (Microsoft)
- **License:** MIT
- **GitHub:** interpretml/interpret
- **Capabilities:**
  - Explainable Boosting Machine (EBM) — glassbox model with high accuracy + interpretability
  - Blackbox explainers: SHAP Kernel Explainer, LIME, Morris Sensitivity Analysis, Partial Dependence
  - Glassbox models: EBM, APLR, Decision Tree, Decision Rule List, Linear/Logistic Regression
  - Interactive visualizations for global and local explanations
  - Model comparison capabilities
- **Limitations:** No fairness metrics, no regulatory mapping, no governance workflow, no audit trail

---

## 3. GOVERNANCE FRAMEWORKS & PLATFORMS

### 3.1 AI Verify (Singapore IMDA / AI Verify Foundation)
- **License:** Apache 2.0
- **Status:** World's first government-built AI governance testing framework
- **Capabilities:**
  - 11 governance principles across 5 focus areas (Transparency, Explainability, Safety & Resilience, Fairness, Governance & Accountability)
  - 85 testable criteria operationalizing the principles
  - 4 built-in technical test toolboxes: SHAP for explainability, robustness toolbox, fairness metrics for classification, fairness metrics for regression
  - Extensible plugin architecture
  - **Project Moonshot** (LLM evaluation): Red-teaming, benchmarking with 100+ datasets, automated evaluation, CI/CD integration
  - Web UI and Python library
  - Maps to OECD AI Principles, ISO/IEC 42001, EU AI Act, NIST AI RMF
- **Limitations:** Small community (~416 total GitHub stars), government-led rather than community-driven, limited enterprise features

### 3.2 Openlayer
- **License:** Commercial (open-core)
- **Capabilities:**
  - Centralized AI system inventory
  - Pre-built mappings for 8 frameworks (EU AI Act, ISO 42001, NIST AI RMF, OSFI E-23)
  - Runtime policy enforcement through guardrails
  - Automated evidence generation
  - Risk classification at intake
  - Trusted by Sun Life, Gallagher, Rogers, KPN, Comcast
  - SOC 2 Type II certified
- **Limitations:** Commercial platform, not fully open-source

### 3.3 Credo AI
- **License:** Commercial
- **Capabilities:**
  - Pre-built regulatory policy packs (EU AI Act, NIST AI RMF, ISO/IEC 42001)
  - AI and agent registries
  - Assessment and evidence workflows
  - Audit-ready documentation
- **Limitations:** Commercial, not open-source

### 3.4 VerifyWise
- **License:** Open-source
- **Capabilities:**
  - Self-hosted compliance tracking
  - EU AI Act, ISO 42001, NIST AI RMF support
- **Limitations:** Limited community, early stage

### 3.5 Holistic AI
- **License:** Apache 2.0 (library)
- **Capabilities:**
  - AI risk governance platform
  - 40+ risk dimensions
  - Auditing and mitigation
- **Limitations:** Library only, no full platform

### 3.6 Complior
- **License:** AGPLv3
- **Capabilities:**
  - CLI + TUI + MCP server for EU AI Act compliance
  - 5-layer static analysis (files, docs, dependencies, AST, LLM deep analysis)
  - 688 dynamic test probes (bias, hallucination, security)
  - 108 EU AI Act obligations mapped
  - 57+ AI frameworks detected
  - Auto-fix with 18 remediation strategies
  - Agent Passport (36-field identity card)
  - Cryptographic evidence chain (SHA-256 + Ed25519)
  - FRIA, AI Policy, Worker Notification generation
  - Runtime SDK with PII sanitization, content marking, prohibited content filter
  - Drift detection daemon
- **Limitations:** EU AI Act focused, AGPLv3 license may deter some enterprises

### 3.7 Bifrost (Maxim AI)
- **License:** Open-source
- **Capabilities:**
  - AI gateway for runtime enforcement
  - Virtual keys with budgets, rate limits, model permissions, MCP tool scoping
  - Guardrails integration (AWS Bedrock, Azure Content Safety, GraySwan, Patronus AI)
  - RBAC and data access control
  - Immutable audit logs with signature verification
  - SOC 2, GDPR, HIPAA, ISO 27001 evidence
- **Limitations:** Runtime enforcement only, no governance program features

### 3.8 ComplyEdge
- **License:** Open-source
- **Capabilities:**
  - EU AI Act Article 5 and Article 50 runtime enforcement
  - Python SDK with @compliance_check decorator
  - MCP server for compliance checks
  - 64 YAML rules + OPA/Rego policies
  - Offline CI linter (TrustLint)
  - Cryptographic evidence on every decision
- **Limitations:** EU AI Act focused, limited to runtime enforcement

### 3.9 Context Stack
- **License:** Apache 2.0
- **Capabilities:**
  - Deterministic agent governance harness
  - OPA/WASM compiled policy decisions
  - Ed25519 sealed receipts for every decision
  - MCP integration
  - 21 conformance scenarios
  - AARM-aligned strict-determinism profile
- **Limitations:** Early stage, narrow focus on agent governance

### 3.10 asago (Red Hat + partners)
- **License:** Open-source
- **Capabilities:**
  - AI safety and governance orchestration layer
  - Scenario generation and red teaming
  - Integration with existing eval/red-teaming frameworks
  - Recommender process for candidate fixes
  - Partners: IBM Research, Microsoft, MIT Lincoln Lab, NVIDIA, Alan Turing Institute
- **Limitations:** Very early stage, orchestration layer only

### 3.11 AI Trust Commons Governance Framework
- **License:** Open-source
- **Capabilities:**
  - Cross-provider policy enforcement
  - Standards mapping (OWASP MCP Top 10, NIST AI RMF, EU AI Act)
  - Policy-as-code with Cedar
  - OpenTelemetry-based audit trails
- **Limitations:** Very early stage (2 GitHub stars)

### 3.12 GAAI (AI Coding Governance Framework)
- **License:** Elastic License 2.0 (ELv2)
- **Capabilities:**
  - Governance layer for AI coding agents
  - Scope drift prevention
  - Backlog-as-contract pattern
  - Acceptance criteria enforcement
  - Persistent memory across sessions
  - Audit trail with ADRs
- **Limitations:** Focused on coding agents only, ELv2 license

### 3.13 AIGRC
- **License:** Open-source
- **Capabilities:**
  - AI framework detection and risk classification
  - EU AI Act risk tier mapping
  - Model card generation
  - Python and TypeScript SDKs
  - MCP server
- **Limitations:** Early stage, limited community

### 3.14 NVIDIA NeMo Guardrails
- **License:** Open-source
- **Capabilities:**
  - Programmable conversational rails
  - Topical, safety, and execution rails
  - Integration with Python LLM frameworks
- **Limitations:** LLM-focused only, no governance workflow

### 3.15 Open Policy Agent (OPA)
- **License:** Apache 2.0 (CNCF graduated)
- **Capabilities:**
  - General-purpose policy engine
  - Rego declarative policy language
  - Kubernetes, service mesh, CI/CD integration
- **Limitations:** Not AI-specific, no AI primitives out of the box

---

## 4. LLM EVALUATION & RED TEAMING TOOLS

### 4.1 Promptfoo
- **License:** MIT
- **Capabilities:**
  - LLM evaluation and red teaming CLI/library
  - 50+ vulnerability types
  - 50+ model providers supported
  - CI/CD integration via YAML
  - Local execution by default
  - Used by 127 Fortune 500 companies, 300,000+ developers
- **Limitations:** No regulatory mapping, no audit trail, no governance workflow

### 4.2 Giskard
- **License:** Open-source (library), commercial (Hub)
- **Capabilities:**
  - Automated performance, bias, and security testing
  - LLM RAG agent testing
  - RAGET toolkit for RAG evaluation
  - CI/CD integration
- **Limitations:** Enterprise features require paid Hub

### 4.3 Langfuse
- **License:** Open-source (MIT)
- **Capabilities:**
  - LLM observability and tracing
  - Prompt management
  - Evaluation scoring
  - Self-hostable via Docker
  - 6M+ SDK installs/month, 10,000+ GitHub stars
- **Limitations:** No compliance reporting, no regulatory evidence packaging

---

## 5. KEY GAPS IN THE LANDSCAPE

After reviewing all major open-source AI governance tools, the following gaps exist:

1. **No unified platform** combining fairness + explainability + compliance + audit trail generation
2. **No ISO 42001-specific** open-source governance chassis with full lifecycle coverage
3. **No agentic AI governance** framework that covers the full agent lifecycle (not just runtime enforcement)
4. **No integrated evidence chain** linking technical test results to regulatory obligations
5. **No cross-framework mapping** in a single open-source tool (NIST AI RMF + EU AI Act + ISO 42001 + OWASP)
6. **No governance orchestration** that connects assessment tools to compliance workflows
7. **Limited LLM governance** — most tools focus on traditional ML, not agentic AI systems
8. **No policy-as-code + technical testing + evidence generation** in a single platform

---

## 6. GRC_Claw DIFFERENTIATION OPPORTUNITIES

Based on the landscape analysis, GRC_Claw can differentiate through:

### 6.1 Unified Governance Chassis
- **Position:** The only open-source ISO 42001 governance chassis that unifies fairness, explainability, compliance, and audit trail generation
- **Differentiator:** While individual tools (Fairlearn, SHAP, AIF360) cover specific technical domains, and platforms (Openlayer, Credo AI) cover compliance workflows, no single open-source project combines all layers

### 6.2 Agentic AI Native
- **Position:** Purpose-built for agentic AI governance, not just traditional ML models
- **Differentiator:** Most existing tools (Fairlearn, AIF360, Aequitas) were designed for traditional ML. Even newer tools focus on LLM evaluation rather than full agent lifecycle governance

### 6.3 Integrated Evidence Chain
- **Position:** Cryptographic evidence chain linking technical test results to regulatory obligations
- **Differentiator:** Tools like Complior and ComplyEdge have evidence chains but are EU AI Act-specific. GRC_Claw can provide multi-framework evidence mapping

### 6.4 Cross-Framework Mapping
- **Position:** Single open-source tool mapping controls across NIST AI RMF, EU AI Act, ISO 42001, OWASP LLM Top 10
- **Differentiator:** AI Trust Commons attempts this but is very early stage. Most tools map to one framework only

### 6.5 Policy-as-Code + Technical Testing
- **Position:** Combining OPA/Rego policy enforcement with automated technical testing
- **Differentiator:** OPA provides policy engine but no AI-specific primitives. Complior combines both but is EU AI Act-specific

### 6.6 Full Lifecycle Coverage
- **Position:** From pre-deployment assessment through runtime monitoring to audit documentation
- **Differentiator:** Most tools cover one phase: Fairlearn (assessment), Bifrost (runtime), Credo AI (documentation). GRC_Claw can cover the full lifecycle

### 6.7 Open-Source with Enterprise Features
- **Position:** Self-hosted, open-source, with enterprise-grade features (RBAC, audit trails, evidence chains)
- **Differentiator:** Many open-source tools lack enterprise features, while enterprise tools are commercial. GRC_Claw can bridge this gap

---

## 7. COMPETITIVE POSITIONING SUMMARY

| Capability | Fairlearn | AIF360 | SHAP | AI Verify | Openlayer | Complior | GRC_Claw Opportunity |
|------------|-----------|--------|------|-----------|-----------|----------|---------------------|
| Fairness metrics | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Bias mitigation | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Explainability | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| LLM evaluation | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Regulatory mapping | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Audit trail | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Runtime enforcement | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Agentic AI governance | ❌ | ❌ | ❌ | Partial | Partial | Partial | ✅ |
| Cross-framework mapping | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| Open-source | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Self-hosted | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |

---

## 8. RECOMMENDATIONS

1. **Integrate, don't replace:** Build adapters for Fairlearn, SHAP, AIF360 rather than reimplementing their algorithms
2. **Focus on the glue:** The biggest gap is the integration layer connecting technical tools to compliance workflows
3. **Agentic AI first:** Position as the governance chassis for agentic AI, not just traditional ML
4. **ISO 42001 native:** Build ISO 42001 as the primary framework, with mappings to others
5. **Evidence chain:** Implement cryptographic evidence generation as a core differentiator
6. **Policy-as-code:** Support OPA/Rego for policy enforcement with AI-specific primitives
7. **Full lifecycle:** Cover assessment → enforcement → monitoring → audit in one platform

---

*Report generated: 2026-10-01*
*Sources: Web search across GitHub, project websites, and industry reports*
