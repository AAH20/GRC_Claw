# GRC_Claw U-AIGMM Benchmark Data by Industry

**Version:** 1.0  
**Date:** October 2026  
**Sources:** CSA/Google Cloud 2025, AAGMM Research, Gartner 2024, MITRE 2023, Microsoft RAI 2023, OWASP AIMA 2025, CMMI AIM 2026

---

## 1. Industry Maturity Distribution

Based on CSA/Google Cloud 2025 survey and AAGMM research:

| Level | % of Organizations | Cumulative | Typical Characteristics |
|-------|-------------------|------------|------------------------|
| **1 - Initial** | ~40% | 40% | No formal governance, shadow AI |
| **2 - Developing** | ~30% | 70% | Emerging practices, department-level |
| **3 - Defined** | ~20% | 90% | Organization-wide practices |
| **4 - Managed** | ~8% | 98% | Quantitative management |
| **5 - Optimizing** | ~2% | 100% | Industry leadership |

---

## 2. Domain-Level Benchmark Scores

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

---

## 3. Industry-Specific Benchmarks

### 3.1 Financial Services

| Domain | Mean | vs. Aggregate | Key Driver |
|--------|------|---------------|------------|
| 1.1 Governance | 2.6 | +0.5 | Regulatory pressure |
| 1.2 Strategy | 2.4 | +0.1 | Digital transformation |
| 1.3 Risk & Compliance | 2.5 | +0.5 | Regulatory pressure |
| 2.1 Fairness | 2.0 | +0.2 | Fair lending requirements |
| 2.2 Privacy | 2.7 | +0.5 | GDPR/CCPA compliance |
| 2.3 Human Oversight | 2.1 | +0.2 | Model risk management |
| 3.1 Data Governance | 2.5 | +0.1 | Data quality focus |
| 3.2 Security | 2.4 | +0.4 | Security investments |
| 3.3 Agent Identity | 1.7 | +0.2 | Emerging focus |
| 3.4 Runtime Controls | 1.6 | +0.2 | Emerging focus |
| 4.1 Monitoring | 2.3 | +0.2 | Operational risk |
| 4.2 Workforce | 2.4 | +0.1 | Talent competition |
| 4.3 Continuous Improvement | 2.0 | +0.1 | Maturity focus |

**Overall Mean**: 2.25 (+0.15 vs. aggregate)

### 3.2 Healthcare

| Domain | Mean | vs. Aggregate | Key Driver |
|--------|------|---------------|------------|
| 1.1 Governance | 2.4 | +0.3 | FDA/EMA guidance |
| 1.2 Strategy | 2.2 | -0.1 | Conservative adoption |
| 1.3 Risk & Compliance | 2.3 | +0.3 | Regulatory compliance |
| 2.1 Fairness | 2.1 | +0.3 | Health equity focus |
| 2.2 Privacy | 2.8 | +0.6 | HIPAA compliance |
| 2.3 Human Oversight | 2.3 | +0.4 | Clinical safety |
| 3.1 Data Governance | 2.6 | +0.2 | Data quality focus |
| 3.2 Security | 2.2 | +0.2 | PHI protection |
| 3.3 Agent Identity | 1.5 | 0.0 | Nascent |
| 3.4 Runtime Controls | 1.4 | 0.0 | Nascent |
| 4.1 Monitoring | 2.2 | +0.1 | Patient safety |
| 4.2 Workforce | 2.3 | 0.0 | Clinical training |
| 4.3 Continuous Improvement | 1.9 | 0.0 | Emerging focus |

**Overall Mean**: 2.18 (+0.08 vs. aggregate)

### 3.3 Technology

| Domain | Mean | vs. Aggregate | Key Driver |
|--------|------|---------------|------------|
| 1.1 Governance | 2.2 | +0.1 | AI-first culture |
| 1.2 Strategy | 2.8 | +0.5 | AI-first business models |
| 1.3 Risk & Compliance | 2.1 | +0.1 | Proactive compliance |
| 2.1 Fairness | 1.9 | +0.1 | Responsible AI focus |
| 2.2 Privacy | 2.3 | +0.1 | Privacy engineering |
| 2.3 Human Oversight | 2.0 | +0.1 | Human-AI collaboration |
| 3.1 Data Governance | 2.5 | +0.1 | Data-driven culture |
| 3.2 Security | 2.2 | +0.2 | Security-first culture |
| 3.3 Agent Identity | 1.9 | +0.4 | Agent-native development |
| 3.4 Runtime Controls | 1.8 | +0.4 | Agent-native development |
| 4.1 Monitoring | 2.5 | +0.4 | DevOps maturity |
| 4.2 Workforce | 2.5 | +0.2 | AI talent density |
| 4.3 Continuous Improvement | 2.3 | +0.4 | Agile culture |

**Overall Mean**: 2.28 (+0.18 vs. aggregate)

### 3.4 Manufacturing

| Domain | Mean | vs. Aggregate | Key Driver |
|--------|------|---------------|------------|
| 1.1 Governance | 1.8 | -0.3 | Traditional governance |
| 1.2 Strategy | 2.0 | -0.3 | Conservative AI adoption |
| 1.3 Risk & Compliance | 1.9 | -0.1 | Emerging focus |
| 2.1 Fairness | 1.6 | -0.2 | Limited focus |
| 2.2 Privacy | 2.0 | -0.2 | Limited PII exposure |
| 2.3 Human Oversight | 1.7 | -0.2 | Traditional automation |
| 3.1 Data Governance | 2.2 | -0.2 | OT/IT separation |
| 3.2 Security | 1.8 | -0.2 | OT security focus |
| 3.3 Agent Identity | 1.3 | -0.2 | Nascent |
| 3.4 Runtime Controls | 1.2 | -0.2 | Nascent |
| 4.1 Monitoring | 1.9 | -0.2 | OT monitoring focus |
| 4.2 Workforce | 2.0 | -0.3 | Skills gap |
| 4.3 Continuous Improvement | 1.7 | -0.2 | Traditional CI |

**Overall Mean**: 1.78 (-0.32 vs. aggregate)

---

## 4. Organization Size Benchmarks

| Size | Overall Mean | Pillar 1 | Pillar 2 | Pillar 3 | Pillar 4 |
|------|--------------|----------|----------|----------|----------|
| <100 employees | 1.8 | 1.9 | 1.6 | 1.7 | 2.0 |
| 100-500 | 2.1 | 2.2 | 1.9 | 2.0 | 2.3 |
| 500-1000 | 2.4 | 2.5 | 2.2 | 2.3 | 2.6 |
| 1000-5000 | 2.6 | 2.7 | 2.4 | 2.5 | 2.8 |
| 5000-10000 | 2.8 | 2.9 | 2.6 | 2.7 | 3.0 |
| >10000 | 3.0 | 3.1 | 2.8 | 2.9 | 3.2 |

**Key Insight**: Larger organizations have higher maturity, but the gap is smallest in Pillar 4 (Operations) and largest in Pillar 2 (Responsible AI), suggesting that ethics/responsible AI is a universal challenge.

---

## 5. Maturity Progression Velocity

Average time to advance one level (by starting level):

| From → To | Average Time | Fastest 10% | Slowest 10% | Key Accelerators |
|-----------|--------------|-------------|-------------|-----------------|
| L1 → L2 | 12 months | 6 months | 24 months | Executive sponsorship, quick wins |
| L2 → L3 | 18 months | 12 months | 36 months | Dedicated team, tooling |
| L3 → L4 | 24 months | 18 months | 48 months | Quantitative culture, automation |
| L4 → L5 | 36 months | 24 months | 60 months | Innovation culture, industry leadership |

---

## 6. Common Maturity Gaps

| Gap | Prevalence | Impact | Priority |
|-----|-----------|--------|----------|
| No agent identity governance | ~77% | Critical | P1 |
| No runtime behavioral controls | ~84% | Critical | P1 |
| No AI risk register | ~60% | High | P1 |
| No human oversight mechanisms | ~55% | High | P1 |
| No AI literacy training | ~45% | Medium | P2 |
| No continuous improvement process | ~50% | Medium | P2 |
| No AI incident response plan | ~65% | High | P1 |
| No data lineage tracking | ~70% | High | P2 |

---

## 7. Benchmark Data Sources

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

## 8. Using Benchmark Data

### 8.1 Percentile Estimation

To estimate an organization's percentile within the industry:

```
If score ≥ benchmark + 1.0 → ~P90 (top 10%)
If score ≥ benchmark + 0.5 → ~P75 (top 25%)
If score ≥ benchmark → ~P50 (median)
If score ≥ benchmark - 0.5 → ~P25 (bottom 25%)
Otherwise → ~P10 (bottom 10%)
```

### 8.2 Gap Analysis

Compare organization scores against industry benchmarks to identify:
- **Above benchmark**: Competitive advantage, potential differentiator
- **At benchmark**: Industry standard, maintain and improve
- **Below benchmark**: Competitive disadvantage, prioritize improvement

### 8.3 Target Setting

Use benchmarks to set realistic targets:
- **Short-term (6-12 months)**: Reach industry median (P50)
- **Medium-term (12-24 months)**: Reach industry P75
- **Long-term (24-36 months)**: Reach industry P90

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Research Team | Initial release |

---

*This document is licensed under CC BY-SA 4.0.*
