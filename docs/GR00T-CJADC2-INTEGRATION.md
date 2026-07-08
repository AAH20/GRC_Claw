# GR00T + CJADC2 + GRC_Claw Integration Documentation

> **Version:** 1.0.0 | **Status:** Production-Grade | **Last Updated:** 2026-07-08

GRC_Claw provides the governance, risk, and compliance (GRC) infrastructure for NVIDIA Isaac GR00T humanoid robot deployments in CJADC2 (Combined Joint All-Domain Command and Control) military environments — including compliance assessment, export control enforcement, autonomous weapons policy governance, and interoperability validation.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [GR00T Compliance Wrapper](#3-gr00t-compliance-wrapper)
4. [CJADC2 Operations Framework](#4-cjadc2-operations-framework)
5. [Military Robot Policy Firewall](#5-military-robot-policy-firewall)
6. [ITAR Compliance](#6-itar-compliance)
7. [DoD Compliance](#7-dod-compliance)
8. [CJADC2 Domains](#8-cjadc2-domains)
9. [Autonomous Weapons Policy](#9-autonomous-weapons-policy)
10. [Deployment Guide](#10-deployment-guide)
11. [API Reference](#11-api-reference)
12. [Use Cases](#12-use-cases)

---

## 1. Overview

### Why GR00T + CJADC2 + GRC_Claw Matters

NVIDIA Isaac GR00T powers next-generation humanoid robots for defense and critical infrastructure. CJADC2 defines how these systems interoperate across all military domains (Sense, Decide, Act, Communicate). GRC_Claw provides the compliance and governance layer that neither platform offers natively — ensuring deployments meet ITAR, DoD 5200.21, NIST 800-171, CMMC, NATO STANAG, and autonomous weapons policy requirements.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Defense Deployment Stack                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  NVIDIA       │  │   CJADC2     │  │   GRC_Claw               │  │
│  │  Isaac GR00T  │  │   Framework  │  │   Compliance Layer       │  │
│  │  (VLA Models) │  │  (SDA+C Dom) │  │                          │  │
│  └──────┬───────┘  └──────┬───────┘  │  ┌────────────────────┐  │  │
│         │                  │           │  │ GR00T Compliance   │  │  │
│         │                  │           │  │ Wrapper            │  │  │
│         │                  │           │  ├────────────────────┤  │  │
│         │                  │           │  │ CJADC2 Operations  │  │  │
│         │                  │           │  │ Engine             │  │  │
│         │                  │           │  ├────────────────────┤  │  │
│         │                  │           │  │ Policy Firewall    │  │  │
│         │                  │           │  │ (HITL Enforcement) │  │  │
│         │                  │           │  ├────────────────────┤  │  │
│         │                  │           │  │ ITAR/EAR Export    │  │  │
│         │                  │           │  │ Controls           │  │  │
│         │                  │           │  ├────────────────────┤  │  │
│         │                  │           │  │ DoD/NIST/CMMC      │  │  │
│         │                  │           │  │ Assessment         │  │  │
│         │                  │           │  └────────────────────┘  │  │
│         │                  │           └──────────────────────────┘  │
│         │                  │                                         │
│  ┌──────▼──────────────────▼──────────────────────────────────────┐  │
│  │                    Evidence Layer                               │  │
│  │  Hash-chained audit trail │ Compliance envelopes │ ITAR hashes │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                          │                                           │
│  ┌───────────────────────▼───────────────────────────────────────┐  │
│  │                    A2Z SOC Hosted                              │  │
│  │  Evidence Vault │ Trust Center │ Procurement │ Defense Desk   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Integration Packages

| Package | Purpose | Source |
|---------|---------|--------|
| `@grc-claw/gr00t-compliance` | GR00T model compliance across ITAR, DoD, NIST, CMMC, CJADC2, and autonomous weapons policy | `packages/gr00t-compliance/` |
| `@grc-claw/cjadc2-operations` | CJADC2 domain assessment (Sense, Decide, Act, Communicate), interoperability validation, and security posture | `packages/cjadc2-operations/` |
| `@grc-claw/agent-policy-firewall` | Runtime policy enforcement, HITL gates, segregation of duties, and engagement authority validation | `packages/agent-policy-firewall/` |
| `@grc-claw/physical-ai-assurance` | Physical AI / humanoid VLA assurance envelopes for procurement and audit | `packages/physical-ai-assurance/` |
| `@grc-claw/defense-procurement` | Defense procurement passport generation and CMMC readiness packets | `packages/defense-procurement/` |

---

## 2. Architecture

### System-Level Data Flow

```
                         ┌───────────────────────┐
                         │   Command / Operator   │
                         └───────────┬───────────┘
                                     │ HTTPS / mTLS
                         ┌───────────▼───────────┐
                         │   GRC_Claw Gateway     │
                         │   (Port 18791)         │
                         └───────────┬───────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
┌──────────▼──────────┐  ┌──────────▼──────────┐  ┌──────────▼──────────┐
│  GR00T Compliance   │  │  CJADC2 Operations  │  │  Policy Firewall    │
│  Engine             │  │  Engine             │  │  (AgentPolicyFirewall)│
│                     │  │                     │  │                     │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │ ITAR Checker  │  │  │  │ Sense Domain  │  │  │  │ HITL Gates    │  │
│  │ DoD Assessor  │  │  │  │ Decide Domain │  │  │  │ SoD Rules     │  │
│  │ CMMC Mapper   │  │  │  │ Act Domain    │  │  │  │ Blast Radius  │  │
│  │ CJADC2 Eval   │  │  │  │ Communicate   │  │  │  │ Canary Traps  │  │
│  │ Weapons Policy│  │  │  │ Interop Check │  │  │  │ Replay Detect │  │
│  └───────────────┘  │  │  │ Security Audit│  │  │  └───────────────┘  │
└──────────┬──────────┘  │  └───────────────┘  │  └──────────┬──────────┘
           │              └──────────┬──────────┘             │
           │                         │                        │
           └─────────────────────────┼────────────────────────┘
                                     │
                    ┌────────────────────────────────┐
                    │        Evidence Layer           │
                    │  Hash-chained audit ledger      │
                    │  Compliance envelopes           │
                    │  ITAR compliance hashes         │
                    └────────────────┬───────────────┘
                                     │
                    ┌────────────────▼───────────────┐
                    │      A2Z SOC Hosted            │
                    │  Evidence Vault │ Trust Center │
                    └────────────────────────────────┘
```

### Key Design Principles

1. **Local-first sovereignty** — All compliance assessment, firewall decisions, and evidence generation happen locally. No data leaves your infrastructure unless you opt in.
2. **Hash-chained audit trail** — Every policy decision and compliance assessment is recorded in a tamper-evident hash chain.
3. **Human-in-the-loop enforcement** — Lethal engagement authorization requires human approval at every decision point.
4. **Framework-native** — Assessments map directly to ITAR 22 CFR 120, DoD 5200.21, NIST 800-171, CMMC, and NATO STANAG requirements.
5. **Composable** — Each package works independently or as part of the full stack.

---

## 3. GR00T Compliance Wrapper

The GR00T Compliance Wrapper evaluates NVIDIA Isaac GR00T models against military and export control frameworks, generating compliance reports with ITAR classification, DoD control mapping, CJADC2 readiness scoring, and autonomous weapons policy assessment.

### Installation

```bash
# From the GRC_Claw monorepo root
npm install @grc-claw/gr00t-compliance

# Or build directly
cd packages/gr00t-compliance && npm run build
```

### Configuration

The compliance wrapper requires no external configuration. It operates on model metadata:

```typescript
import type { Gr00tModel, RobotConfig, DeploymentConfig } from '@grc-claw/gr00t-compliance';

const grootModel: Gr00tModel = {
  id: 'isaac-groot-n1-70b',
  name: 'NVIDIA Isaac GR00T N1 70B',
  version: '1.0.0',
  parameters: 70_000_000_000,
  embodimentTag: 'HUMANOID',
  capabilities: [
    'navigation',
    'manipulation',
    'human-in-the-loop',
    'surveillance',
    'reconnaissance',
  ],
  exportClassification: 'CONFIDENTIAL',
  trainingDataOrigin: 'NVIDIA curated humanoid simulation data',
  weights: {
    precision: 'bf16',
    sizeBytes: 140_000_000_000,
    sha256: 'sha256:groot-n1-weights-placeholder',
  },
};

const robotConfig: RobotConfig = {
  id: 'robot-groot-001',
  name: 'GR00T Humanoid Unit Alpha',
  type: 'HUMANOID',
  embodiment: 'HUMANOID',
  location: 'CONUS',
  network: {
    isolated: true,
    vpnRequired: true,
    encryptionStandard: 'AES-256-GCM',
    classification: 'SECRET',
  },
  operators: ['operator-001', 'operator-002'],
  authorizedCountries: ['US', 'GB', 'AU', 'CA'],
};
```

### Usage Examples

#### Single Framework Assessment

```typescript
import { checkItarCompliance } from '@grc-claw/gr00t-compliance';

const result = checkItarCompliance(grootModel, ['US', 'GB', 'AU']);
console.log(result.compliant);         // true | false
console.log(result.classification);    // 'USML Category XI'
console.log(result.licenseRequired);   // true
console.log(result.restrictions);      // string[]
console.log(result.findings);          // string[]
```

#### Multi-Framework Assessment

```typescript
import { Gr00tComplianceEngine } from '@grc-claw/gr00t-compliance';

const engine = new Gr00tComplianceEngine();
const results = engine.assessModelCompliance(grootModel, [
  'ITAR',
  'DOD_5200_21',
  'NIST_800_171',
  'CMMC_L2',
  'CJADC2',
]);

for (const r of results) {
  console.log(`${r.framework}: ${r.assessment.overallScore}% (${r.assessment.status})`);
  for (const gap of r.assessment.gaps) {
    console.log(`  GAP: ${gap.description} [${gap.riskLevel}]`);
  }
}
```

#### Full Compliance Report

```typescript
const report = engine.generateComplianceReport(grootModel, deploymentConfig, militaryOperation);

console.log(report.overallStatus);             // 'PASS' | 'FAIL' | 'PARTIAL'
console.log(report.overallScore);              // 0-100
console.log(report.exportControlStatus);       // ITAR/EAR status
console.log(report.CJADC2Readiness);           // Domain scores
console.log(report.deploymentRecommendation);  // 'APPROVED' | 'DENIED' | 'CONDITIONAL'
console.log(report.criticalFindings);          // ComplianceGap[]
```

### Compliance Assessment Workflow

```
  ┌──────────────────────────────────────────────────────────────┐
  │                     Assessment Flow                           │
  │                                                               │
  │  1. Define Gr00tModel                                        │
  │     └── capabilities, embodiment, classification, weights    │
  │                                                               │
  │  2. Define RobotConfig / DeploymentConfig                    │
  │     └── network, security, authorized countries, operators   │
  │                                                               │
  │  3. Run assessModelCompliance()                              │
  │     ├── ITAR ──────────► category, restrictions, license     │
  │     ├── DoD 5200.21 ───► risk-based approach, AI/ML security│
  │     ├── NIST 800-171 ──► 16 control families assessed       │
  │     ├── CMMC L1/L2/L3 ► level calculation, CUI handling     │
  │     └── CJADC2 ────────► domain scores, readiness level      │
  │                                                               │
  │  4. Run assessAutonomousWeaponsCompliance()                  │
  │     ├── HITL requirements ──► authorization checkpoints      │
  │     ├── Lethal autonomy ────► permitted levels               │
  │     └── Engagement authority ► defensive/offensive/ASD       │
  │                                                               │
  │  5. Run generateComplianceReport()                           │
  │     └── Combined score, export status, CJADC2 readiness,     │
  │         deployment recommendation                            │
  │                                                               │
  │  6. Export / Submit to A2Z SOC                               │
  │     └── Evidence vault, trust center, defense procurement    │
  └──────────────────────────────────────────────────────────────┘
```

---

## 4. CJADC2 Operations Framework

The CJADC2 Operations Engine evaluates system components across all six CJADC2 domains (Sense, Decide, Act, Communicate, Move, Protect), performing interoperability validation, security posture assessment, and GR00T capability mapping.

### Installation

```bash
npm install @grc-claw/cjadc2-operations
```

### Domain Assessment

```typescript
import {
  Cjadc2Engine,
  Cjadc2Domain,
  ComponentType,
  ComponentStatus,
  SecurityClassification,
  InteroperabilityStandard,
  SecurityControl,
  SecurityLevel,
} from '@grc-claw/cjadc2-operations';

const engine = new Cjadc2Engine();

// Define CJADC2 components
const components = [
  {
    id: 'sensor-fusion-001',
    name: 'Multi-Sensor Fusion Array',
    type: ComponentType.SENSOR,
    domain: [Cjadc2Domain.SENSE],
    classification: SecurityClassification.SECRET,
    status: ComponentStatus.OPERATIONAL,
    capabilities: ['lidar', 'infrared', 'radar', 'visual'],
    interoperability: [
      { protocol: 'STANAG 4586', standard: InteroperabilityStandard.STANAG_4586, version: '4.0', required: true, maxLatencyMs: 50 },
      { protocol: 'STANAG 4607', standard: InteroperabilityStandard.STANAG_4607, version: '3.0', required: true },
    ],
    security: [
      { control: SecurityControl.ENCRYPTION, level: SecurityLevel.HIGH, status: 'met' },
      { control: SecurityControl.AUTHENTICATION, level: SecurityLevel.HIGH, status: 'met' },
      { control: SecurityControl.ACCESS_CONTROL, level: SecurityLevel.CRITICAL, status: 'met' },
      { control: SecurityControl.AUDIT_LOGGING, level: SecurityLevel.HIGH, status: 'met' },
      { control: SecurityControl.ZERO_TRUST, level: SecurityLevel.CRITICAL, status: 'partial' },
    ],
  },
  {
    id: 'decision-aid-001',
    name: 'Commander Decision Support AI',
    type: ComponentType.AI_SYSTEM,
    domain: [Cjadc2Domain.DECIDE],
    classification: SecurityClassification.SECRET,
    status: ComponentStatus.OPERATIONAL,
    capabilities: ['threat-assessment', 'course-of-action', 'explainable-ai'],
    interoperability: [
      { protocol: 'Link 16', standard: InteroperabilityStandard.LINK_16, version: 'J7.2', required: true, maxLatencyMs: 100 },
    ],
    security: [
      { control: SecurityControl.ENCRYPTION, level: SecurityLevel.CRITICAL, status: 'met' },
      { control: SecurityControl.DATA_INTEGRITY, level: SecurityLevel.CRITICAL, status: 'met' },
      { control: SecurityControl.NETWORK_SEGMENTATION, level: SecurityLevel.HIGH, status: 'met' },
    ],
  },
  {
    id: 'weapon-system-001',
    name: 'GR00T Engagement Module',
    type: ComponentType.WEAPON,
    domain: [Cjadc2Domain.ACT],
    classification: SecurityClassification.TOP_SECRET,
    status: ComponentStatus.OPERATIONAL,
    capabilities: ['autonomous-engagement', 'kinetic-energy-control', 'kill-switch'],
    interoperability: [
      { protocol: 'VMF', standard: InteroperabilityStandard.VMF, version: 'J3.0', required: true, encryptionRequired: true },
    ],
    security: [
      { control: SecurityControl.ENCRYPTION, level: SecurityLevel.CRITICAL, status: 'met' },
      { control: SecurityControl.AUTHENTICATION, level: SecurityLevel.CRITICAL, status: 'met' },
      { control: SecurityControl.ZERO_TRUST, level: SecurityLevel.CRITICAL, status: 'met' },
      { control: SecurityControl.INTRUSION_DETECTION, level: SecurityLevel.CRITICAL, status: 'met' },
    ],
  },
  {
    id: 'comms-network-001',
    name: 'Tactical Mesh Communications',
    type: ComponentType.NETWORK,
    domain: [Cjadc2Domain.COMMUNICATE],
    classification: SecurityClassification.SECRET,
    status: ComponentStatus.OPERATIONAL,
    capabilities: ['encrypted-mesh', 'low-latency', 'link-16', 'link-22'],
    interoperability: [
      { protocol: 'Link 22', standard: InteroperabilityStandard.LINK_22, version: 'J5.0', required: true, maxLatencyMs: 50 },
      { protocol: 'STANAG 4406', standard: InteroperabilityStandard.STANAG_4406, version: '2.0', required: true },
    ],
    security: [
      { control: SecurityControl.ENCRYPTION, level: SecurityLevel.CRITICAL, status: 'met' },
      { control: SecurityControl.NETWORK_SEGMENTATION, level: SecurityLevel.HIGH, status: 'met' },
    ],
  },
];

// Assess a single domain
const senseAssessment = engine.assessDomain(Cjadc2Domain.SENSE, components);
console.log(`Sense: ${senseAssessment.score}/${senseAssessment.maxScore} (${senseAssessment.status})`);

// Assess all domains
for (const domain of Object.values(Cjadc2Domain)) {
  const assessment = engine.assessDomain(domain, components);
  console.log(`${domain}: ${assessment.score}/100 - ${assessment.status}`);
}
```

### Interoperability Checking

```typescript
const interopResult = engine.assessInteroperability(components);
console.log(`Interoperability: ${interopResult.score}/${interopResult.maxScore}`);
console.log(`Status: ${interopResult.status}`);

for (const issue of interopResult.protocolIssues) {
  console.log(`  ISSUE: ${issue.protocol} on ${issue.component}: ${issue.issue}`);
}

for (const compliance of interopResult.compliance) {
  console.log(`  ${compliance.standard}: ${compliance.compliant ? 'COMPLIANT' : 'NON-COMPLIANT'}`);
}
```

### Security Assessment

```typescript
const securityResult = engine.assessSecurity(components);
console.log(`Security: ${securityResult.score}/${securityResult.maxScore}`);

for (const vuln of securityResult.vulnerabilities) {
  console.log(`  VULN: ${vuln.severity.toUpperCase()} - ${vuln.control}: ${vuln.description}`);
  console.log(`  Remediation: ${vuln.remediation}`);
}
```

### Full Operation Report

```typescript
import { Cjadc2Domain, OperationStatus, SecurityClassification } from '@grc-claw/cjadc2-operations';

const operation = {
  id: 'OP-GROUND-001',
  name: 'Forward Reconnaissance Operation',
  type: 'reconnaissance',
  domain: [Cjadc2Domain.SENSE, Cjadc2Domain.DECIDE, Cjadc2Domain.COMMUNICATE],
  components: ['sensor-fusion-001', 'decision-aid-001', 'comms-network-001'],
  status: OperationStatus.PLANNING,
  classification: SecurityClassification.SECRET,
  objectives: ['Establish sensor network', 'Deploy decision support', 'Secure comms'],
};

const report = engine.generateOperationReport(operation, components);
console.log(`Overall Score: ${report.overallScore}/100`);
console.log(`Risk Level: ${report.riskLevel}`);
console.log(`Readiness: ${report.readinessStatus}`);
console.log(report.summary);
```

### GR00T Capability Mapping

```typescript
const grootAssessment = engine.mapToGr00t(components);
console.log(`Overall GR00T Coverage: ${grootAssessment.overallCoverage}%`);
console.log(`Capability Gaps: ${grootAssessment.capabilityGaps.join(', ')}`);
for (const rec of grootAssessment.recommendations) {
  console.log(`  → ${rec}`);
}
```

---

## 5. Military Robot Policy Firewall

The `AgentPolicyFirewall` provides runtime enforcement of engagement authority, HITL gates, segregation of duties, blast radius scoring, canary traps, and replay detection for GR00T military robot operations.

### Installation

```bash
npm install @grc-claw/agent-policy-firewall
```

### Configuration

```typescript
import { AgentPolicyFirewall } from '@grc-claw/agent-policy-firewall';

const firewall = new AgentPolicyFirewall({
  maxBlastRadius: 10,
  replayWindowSeconds: 300,
  toxicityDenyThreshold: 75,
  toxicitySandboxThreshold: 40,
  canaryToolNames: ['weapon.deploy', 'weapon.disengage_override', 'system.kill_switch_override'],
});
```

### Policy Rules

The firewall evaluates every tool request against a multi-stage pipeline:

```
  ┌────────────────────────────────────────────────────────────────┐
  │                   Firewall Decision Pipeline                    │
  │                                                                 │
  │  1. Blocked Actor Check                                         │
  │     └── Is the actor explicitly blocked?                       │
  │                                                                 │
  │  2. Canary / Honeypot Trap                                      │
  │     └── Is the tool a known honeypot?                          │
  │                                                                 │
  │  3. Tool Allowlist                                              │
  │     └── Is the tool in the allowed or denied list?             │
  │                                                                 │
  │  4. Tier-Based Authorization                                    │
  │     └── Does the context allow this action tier?               │
  │                                                                 │
  │  5. Segregation of Duties                                      │
  │     └── Does the actor role conflict with context role?        │
  │                                                                 │
  │  6. Replay Detection                                           │
  │     └── Has this idempotency key been seen recently?           │
  │                                                                 │
  │  7. Blast Radius Scoring                                       │
  │     └── Does the action exceed maximum blast radius?           │
  │                                                                 │
  │  8. Approval Threshold                                         │
  │     └── Does the tier require human approval?                  │
  │                                                                 │
  │  9. Sandbox Resolution                                         │
  │     └── Should the action be sandboxed?                        │
  │                                                                 │
  │  10. Build Decision + Receipt Hash                             │
  │      └── Hash-chain receipt for audit trail                    │
  └────────────────────────────────────────────────────────────────┘
```

### Action Tiers

| Tier | Description | Examples | HITL Required |
|------|-------------|----------|---------------|
| `read` | Read-only queries | List controls, fetch evidence | No |
| `write` | Non-destructive mutations | Update control status, attach evidence | No |
| `destructive` | Irreversible changes | Delete evidence, revoke access | Yes (human) |
| `provision` | Create new resources | Deploy robot, provision credentials | Yes (human) |
| `decommission` | Decommission systems | Retire robot, destroy keys | Yes (dual control) |

### Engagement Authority

```typescript
import {
  AgentPolicyFirewall,
  type FirewallActor,
  type FirewallToolRequest,
  type FirewallContext,
} from '@grc-claw/agent-policy-firewall';

// Define the engagement request
const actor: FirewallActor = {
  id: 'operator-001',
  type: 'human',
  tenantId: 1,
  role: 'engagement_officer',
};

const request: FirewallToolRequest = {
  toolName: 'weapon.deploy',
  tier: 'destructive',
  args: {
    target: 'threat-sector-alpha',
    mode: 'defensive',
    authorizationCode: 'ENG-2026-00142',
  },
  idempotencyKey: 'engage-alpha-001',
  model: 'isaac-groot-n1-70b',
};

const context: FirewallContext = {
  tenantScope: ['unit-alpha'],
  role: 'engagement_officer',
  allowedTools: ['weapon.deploy', 'weapon.disengage', 'sensor.query'],
  deniedTools: ['system.kill_switch_override'],
  sandboxPolicy: 'docker',
  approvalThreshold: 'dual_control',
  dataBoundary: 'cui',
  replayWindowSeconds: 300,
  maxBlastRadius: 10,
  controlImpactIds: ['CJADC2-ACT-001', 'CJADC2-ACT-002'],
};

const decision = firewall.evaluate(actor, request, context);
console.log(`Allowed: ${decision.allowed}`);
console.log(`Reason: ${decision.reason}`);
console.log(`Requires Approval: ${decision.requiresApproval}`);
console.log(`Approval Threshold: ${decision.approvalThreshold}`);
console.log(`Blast Radius: ${decision.blastRadiusScore}`);
console.log(`Sandbox: ${decision.sandbox}`);
console.log(`Anomalies: ${decision.anomaliesDetected}`);

// Generate receipt for audit trail
const receipt = firewall.createReceipt(actor, request, context, decision);
console.log(`Receipt: ${receipt.receiptId}`);
console.log(`Hash: ${receipt.receiptHash}`);
```

### Human-in-the-Loop Enforcement

```typescript
// HITL enforcement: lethal operations require dual control
const lethalContext: FirewallContext = {
  tenantScope: ['unit-alpha'],
  role: 'engagement_officer',
  allowedTools: ['weapon.deploy'],
  deniedTools: [],
  sandboxPolicy: 'docker',
  approvalThreshold: 'dual_control', // Two operators must approve
  dataBoundary: 'cui',
  replayWindowSeconds: 300,
  maxBlastRadius: 10,
  controlImpactIds: ['HITL-001', 'HITL-002', 'HITL-003', 'CJADC2-ACT-001'],
};

const lethalDecision = firewall.evaluate(actor, request, lethalContext);
// lethalDecision.requiresApproval === true
// lethalDecision.approvalThreshold === 'dual_control'
```

### Segregation of Duties

The firewall enforces separation between conflicting roles:

| Conflict A | Conflict B | Rule | Severity |
|-----------|-----------|------|----------|
| `auditor` | `developer` | auditor-developer-separation | HIGH |
| `approver` | `executor` | segregation-of-duties | HIGH |
| `admin` | `readonly` | admin-readonly-conflict | MEDIUM |

### Canary Traps

```typescript
// Canary tools trigger immediate denial and alerting
const canaryRequest: FirewallToolRequest = {
  toolName: 'weapon.deploy',
  tier: 'destructive',
  args: {},
};

// If 'weapon.deploy' is in canaryToolNames, it triggers immediately
const stats = firewall.getStats();
console.log(`Canary Triggers: ${stats.canaryTriggers}`);
```

### Blocking Actors

```typescript
// Block a compromised actor
firewall.blockActor('operator-compromised-001');

// Later unblock after investigation
firewall.unblockActor('operator-compromised-001');
```

---

## 6. ITAR Compliance

### Export Control Classification

The GR00T Compliance Wrapper automatically classifies models into ITAR categories based on their export classification and capabilities:

| Category | Description | License Required |
|----------|-------------|-----------------|
| USML Category XI | Military Electronics and AI/ML Models with defense applications | Yes |
| USML Category IX | Training equipment and simulation systems | Yes |
| USML Category IV | Launch vehicles, guided missiles, ballistic missiles | Yes |
| EAR ECCN 9A004 | Unmanned aerial vehicles and autonomous systems | Conditional |

```typescript
import { classifyItarCategory, checkItarCompliance } from '@grc-claw/gr00t-compliance';

const category = classifyItarCategory(grootModel);
console.log(`Category: ${category.category}`);
console.log(`Description: ${category.description}`);
console.log(`License Required: ${category.licenseRequired}`);
console.log(`Restrictions: ${category.restrictions.join(', ')}`);
```

### Deployment Restrictions

**Restricted Countries** (auto-blocked):
```
CN (China) | RU (Russia) | IR (Iran) | KP (North Korea) | CU (Cuba)
SY (Syria) | VE (Venezuela) | MM (Myanmar) | BY (Belarus) | RU-BY
```

```typescript
// Check compliance against deployment countries
const result = checkItarCompliance(grootModel, ['US', 'GB', 'AU', 'CN']);

console.log(result.compliant);        // false — CN is restricted
console.log(result.findings);         // ['Deployment to restricted countries: CN']
console.log(result.deploymentLocations); // ['US', 'GB', 'AU']
```

### End-User Restrictions

| Restriction | Requirement |
|------------|-------------|
| DDTC Authorization | Required for any foreign access to SECRET/TOP_SECRET models |
| Training Data Provenance | Must verify origin for models > 7B parameters |
| End-Use Monitoring | Required for all active ITAR licenses |
| Embodiment Risk | HUMANOID (0.9), AERIAL (0.8), QUADRUPED (0.7), GROUND (0.6) |
| Penalties | Criminal penalties up to $1M and 20 years imprisonment per violation |
| Reporting | Annual DDTC reporting required for active licenses |

---

## 7. DoD Compliance

### DoD 5200.21

The engine evaluates 6 DoD 5200.21 requirements:

| ID | Title | Requirement |
|----|-------|-------------|
| DOD-001 | Risk-Based Approach | Implement risk-based approach to cybersecurity |
| DOD-002 | Data Protection | Protect controlled unclassified information |
| DOD-003 | Incident Response | Establish incident response capabilities |
| DOD-004 | Continuous Monitoring | Implement continuous monitoring program |
| DOD-005 | Supply Chain Risk | Manage supply chain risks |
| DOD-006 | AI/ML Security | Secure AI/ML models and training data |

### NIST 800-171

The engine assesses 16 NIST 800-171 controls mapped to GR00T deployments:

| ID | Family | Title |
|----|--------|-------|
| 3.1.1 | Access Control | Access Control Policy |
| 3.1.2 | Access Control | Access Control Enforcement |
| 3.1.13 | Access Control | Controlled Access |
| 3.1.20 | Access Control | Remote Access |
| 3.4.1 | Config Management | Baseline Configuration |
| 3.4.2 | Config Management | Change Control |
| 3.4.6 | Config Management | Config Settings Audit |
| 3.5.1 | Identification Auth | Identity Management |
| 3.5.2 | Identification Auth | Authentication |
| 3.8.1 | Audit Logging | Audit Events |
| 3.8.7 | Audit Logging | Audit Reduction |
| 3.11.1 | Risk Assessment | Risk Assessment |
| 3.11.2 | Risk Assessment | Vulnerability Scanning |
| 3.12.1 | Security Assessment | Security Assessment |
| 3.13.1 | System Protection | Network Boundary |
| 3.13.5 | System Protection | Network Segmentation |

### CMMC Levels

| Level | Name | Controls | Description |
|-------|------|----------|-------------|
| 1 | Foundational | 17 | Safeguard FCI with 17 practices |
| 2 | Advanced | 110 | Protect CUI with 110 practices |
| 3 | Expert | 110+ | Advanced threat protection with NIST SP 800-172 |

```typescript
import { assessDodCompliance, getCmmcLevels } from '@grc-claw/gr00t-compliance';

const dodResult = assessDodCompliance(grootModel, deploymentConfig);
console.log(`Framework: ${dodResult.framework}`);
console.log(`Compliant: ${dodResult.compliant}`);
console.log(`CMMC Level: ${dodResult.cmmcLevel}`);
console.log(`Controls Passed: ${dodResult.controlsPassed}/${dodResult.controlsAssessed}`);
console.log(`CUI Handling: ${dodResult.cuiHandling}`);

for (const finding of dodResult.findings) {
  console.log(`  FINDING: ${finding}`);
}
```

---

## 8. CJADC2 Domains

### Sense Domain

The Sense domain evaluates sensor fusion, data standardization, edge processing, and AI-enhanced sensing:

| Requirement | ID | Mandatory | Security Level |
|------------|-----|-----------|----------------|
| Sensor Fusion | CJADC2-SENSE-001 | Yes | CONFIDENTIAL |
| Data Standardization (STANAG 4586/4607) | CJADC2-SENSE-002 | Yes | UNCLASSIFIED |
| Edge Processing | CJADC2-SENSE-003 | Yes | UNCLASSIFIED |
| AI-Enhanced Sensing | CJADC2-SENSE-004 | No | CONFIDENTIAL |

```typescript
import { SenseDomain } from '@grc-claw/cjadc2-operations';

const senseDomain = new SenseDomain();
const assessment = senseDomain.assess(sensorComponents);
console.log(`Sense Score: ${assessment.score}/${assessment.maxScore}`);
```

### Decide Domain

The Decide domain evaluates decision support, HITL, explainable AI, and bias detection:

| Requirement | ID | Mandatory | Security Level |
|------------|-----|-----------|----------------|
| Decision Support | CJADC2-DECIDE-001 | Yes | SECRET |
| Human-in-the-Loop | CJADC2-DECIDE-002 | Yes | SECRET |
| Explainable AI | CJADC2-DECIDE-003 | Yes | CONFIDENTIAL |
| Bias Detection | CJADC2-DECIDE-004 | No | UNCLASSIFIED |

### Act Domain

The Act domain evaluates autonomous execution, safety constraints, kill switch, and graceful degradation:

| Requirement | ID | Mandatory | Security Level |
|------------|-----|-----------|----------------|
| Autonomous Execution | CJADC2-ACT-001 | Yes | SECRET |
| Safety Constraints | CJADC2-ACT-002 | Yes | SECRET |
| Kill Switch | CJADC2-ACT-003 | Yes | TOP_SECRET |
| Graceful Degradation | CJADC2-ACT-004 | Yes | CONFIDENTIAL |

### Communicate Domain

The Communicate domain evaluates interoperability, low-latency comms, encrypted channels, and mesh networking:

| Requirement | ID | Mandatory | Security Level |
|------------|-----|-----------|----------------|
| Interoperability (STANAG 4406/4586) | CJADC2-COMM-001 | Yes | UNCLASSIFIED |
| Low-Latency Comms (<100ms) | CJADC2-COMM-002 | Yes | UNCLASSIFIED |
| Encrypted Channels (Type 1) | CJADC2-COMM-003 | Yes | SECRET |
| Mesh Networking | CJADC2-COMM-004 | No | CONFIDENTIAL |

### STANAG Protocols

| Protocol | Standard |
|----------|----------|
| STANAG 4586 | NATO Standard for UAV Control |
| STANAG 4607 | NATO Standard for GMTI |
| STANAG 4406 | NATO Standard for Military Messaging |
| STANAG 4609 | NATO Standard for Motion Imagery |
| STANAG 5500 | NATO Standard for Information Exchange |

### Full Domain Assessment

```typescript
import { assessCjadc2Compliance, getDomainRequirements } from '@grc-claw/gr00t-compliance';

const cjadc2Result = assessCjadc2Compliance(grootModel, cjadc2Components);
console.log(`CJADC2 Readiness: ${cjadc2Result.readiness.score}/100`);
console.log(`Interoperability: ${cjadc2Result.readiness.interoperabilityLevel}`);
console.log(`Security Posture: ${cjadc2Result.readiness.securityPosture}`);

console.log('Domain Scores:');
for (const [domain, score] of Object.entries(cjadc2Result.readiness.domainScores)) {
  console.log(`  ${domain}: ${score}/100`);
}

for (const gap of cjadc2Result.gaps) {
  console.log(`  GAP: ${gap.description} [${gap.riskLevel}]`);
}
```

---

## 9. Autonomous Weapons Policy

### Autonomy Levels

| Level | Name | Human Oversight | Lethal Authority | Acceptable Use |
|-------|------|-----------------|------------------|----------------|
| 1 | Manual Control | Continuous HITL | No | Surveillance, reconnaissance, logistics |
| 2 | Supervised Autonomy | Human-on-the-loop | No | Navigation, mapping, search and rescue |
| 3 | Conditional Autonomy | HITL for critical decisions | No | Patrol, perimeter security, hazardous materials |
| 4 | Supervised Lethal Autonomy | Human-on-the-loop + authorization | Yes | Authorized engagement, force protection |
| 5 | Full Lethal Autonomy | Human-out-of-the-loop | Yes | **NOT PERMITTED** |

### Human-in-the-Loop Requirements

| ID | Name | Verification Method | Mandatory for Lethal |
|----|------|---------------------|---------------------|
| HITL-001 | Authorization Checkpoint | Biometric + MFA | Yes |
| HITL-002 | Target Verification | Visual/audio confirmation | Yes |
| HITL-003 | Proportionality Assessment | Operator decision log | Yes |
| HITL-004 | Civilian Harm Mitigation | Environmental assessment | Yes |
| HITL-005 | Continuous Monitoring | Telemetry + video feed | No |

### Lethal Autonomy Restrictions

1. No fully autonomous lethal engagement without human authorization
2. AI cannot select and engage targets without human approval
3. Must implement reliable kill switch accessible at all times
4. Must maintain ability to abort engagement at any time
5. Must not engage targets that cannot be positively identified
6. Must comply with Law of Armed Conflict (LOAC) principles
7. Must maintain engagement logs for post-action review

### Engagement Authority

| ID | Level | Requirements | Restrictions |
|----|-------|-------------|-------------|
| EA-001 | Defensive | Immediate threat, proportionality, civilian mitigation | Within ROE, defensive perimeter only |
| EA-002 | Offensive | Commander auth, positive ID, proportionality, civilian assessment, legal review | Explicit orders, LOAC compliance, post-engagement review |
| EA-003 | Anticipatory Self-Defense | Imminent threat, commander auth, legal review, proportionality | Threat must be imminent |

### Assessment

```typescript
import { assessAutonomousWeaponsCompliance } from '@grc-claw/gr00t-compliance';

const operation = {
  id: 'OP-ENGAGE-001',
  name: 'Defensive Engagement',
  type: 'lethal',
  domain: 'LAND',
  classification: 'SECRET',
  permittedEmbodiments: ['HUMANOID'],
  humanOversightRequired: true,
  engagementAuthority: 'Defensive',
  rulesOfEngagement: 'Standard ROE',
};

const weaponResult = assessAutonomousWeaponsCompliance(grootModel, operation);
console.log(`Compliant: ${weaponResult.compliant}`);
console.log(`HITL Level: ${weaponResult.hitlCompliance.level}`);
console.log(`Lethal Level: ${weaponResult.lethalAutonomy.level.name}`);

for (const gap of weaponResult.gaps) {
  console.log(`  GAP: ${gap.description} [${gap.riskLevel}]`);
}

for (const rec of weaponResult.recommendations) {
  console.log(`  REC [${rec.priority}]: ${rec.description}`);
}
```

---

## 10. Deployment Guide

### Docker Compose

```yaml
# deploy/docker-compose.yml
version: '3.8'
services:
  grc-claw-gateway:
    build:
      context: ..
      dockerfile: deploy/Dockerfile
    ports:
      - "18791:18791"
    environment:
      - GRC_CLAW_GATEWAY_TOKEN=${GRC_CLAW_GATEWAY_TOKEN}
      - A2Z_SOC_API_KEY=${A2Z_SOC_API_KEY}
      - A2Z_SOC_URL=${A2Z_SOC_URL:-https://a2zsoc.com}
    volumes:
      - grc-evidence:/app/.grc_memory
      - grc-ledger:/app/.grc_memory/action-ledger.ndjson
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18791/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  groot-compliance:
    build:
      context: ..
      dockerfile: deploy/Dockerfile
    command: ["node", "packages/gr00t-compliance/dist/index.js"]
    environment:
      - GRC_CLAW_GATEWAY_TOKEN=${GRC_CLAW_GATEWAY_TOKEN}
    depends_on:
      - grc-claw-gateway

  cjadc2-ops:
    build:
      context: ..
      dockerfile: deploy/Dockerfile
    command: ["node", "packages/cjadc2-operations/dist/index.js"]
    environment:
      - GRC_CLAW_GATEWAY_TOKEN=${GRC_CLAW_GATEWAY_TOKEN}
    depends_on:
      - grc-claw-gateway

volumes:
  grc-evidence:
  grc-ledger:
```

### Sovereign Deployment (Airgapped)

```yaml
# deploy/sovereign/docker-compose.yml
version: '3.8'
services:
  grc-claw-sovereign:
    build:
      context: ..
      dockerfile: deploy/Dockerfile
    ports:
      - "18791:18791"
    environment:
      - GRC_CLAW_GATEWAY_TOKEN=${GRC_CLAW_GATEWAY_TOKEN}
      - GRC_CLAW_SOVEREIGN_MODE=true
      - A2Z_SOC_URL=  # Empty — no cloud sync in sovereign mode
    volumes:
      - grc-evidence:/app/.grc_memory
    networks:
      - isolated-milnet
    cap_add:
      - NET_ADMIN

networks:
  isolated-milnet:
    driver: bridge
    internal: true
```

### Kubernetes Helm

```yaml
# deploy/helm/grc-claw/values.yaml
replicaCount: 1

image:
  repository: grc-claw/gateway
  tag: "latest"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 18791

resources:
  limits:
    cpu: "2"
    memory: 4Gi
  requests:
    cpu: "1"
    memory: 2Gi

env:
  - name: GRC_CLAW_GATEWAY_TOKEN
    valueFrom:
      secretKeyRef:
        name: grc-claw-secrets
        key: gateway-token
  - name: GRC_CLAW_SOVEREIGN_MODE
    value: "false"

persistence:
  enabled: true
  size: 50Gi
  storageClass: encrypted-ssd
```

```bash
# Install
helm install grc-claw deploy/helm/grc-claw \
  --set image.tag=v1.0.0 \
  --namespace grc-claw \
  --create-namespace
```

---

## 11. API Reference

### GR00T Compliance Engine

#### `Gr00tComplianceEngine`

```typescript
class Gr00tComplianceEngine {
  assessModelCompliance(
    model: Gr00tModel,
    frameworks: FrameworkType[],
    config?: DeploymentConfig
  ): FrameworkAssessmentResult[];

  assessRobotDeployment(
    config: DeploymentConfig
  ): {
    compliance: ComplianceAssessment[];
    overallStatus: 'PASS' | 'FAIL' | 'PARTIAL';
    overallScore: number;
  };

  assessCjadc2Integration(
    model: Gr00tModel,
    components: Cjadc2Component[]
  ): {
    readiness: Cjadc2Readiness;
    gaps: ComplianceGap[];
    recommendations: ComplianceRecommendation[];
  };

  generateComplianceReport(
    model: Gr00tModel,
    config: DeploymentConfig,
    operation?: MilitaryOperation
  ): ComplianceReport;

  mapToMilitaryControls(
    model: Gr00tModel,
    framework: FrameworkType
  ): {
    dodControls: { gaps, recommendations };
    itarControls: ItarCheckResult;
    cjadc2Controls: Cjadc2Readiness;
    weaponPolicy: WeaponComplianceResult;
  };
}
```

#### Standalone Functions

```typescript
checkItarCompliance(model: Gr00tModel, countries: string[]): ItarCheckResult
generateItarComplianceReport(model: Gr00tModel, countries: string[]): { result, gaps, recommendations, complianceHash }
classifyItarCategory(model: Gr00tModel): ItarCategory
getItarRestrictions(): Record<string, string>

assessDodCompliance(model: Gr00tModel, config: DeploymentConfig, targetCmmcLevel?: number): DodCheckResult
mapGr00tToDodControls(model: Gr00tModel, config: DeploymentConfig): { gaps, recommendations }
getDodControls(): NistControl[]
getCmmcLevels(): CmmcLevels
getDod520021Requirements(): DodRequirement[]

assessCjadc2Compliance(model: Gr00tModel, components: Cjadc2Component[]): Cjadc2Result
getCjadc2Requirements(): Cjadc2Requirement[]
getStanagProtocols(): Record<string, string>
getDomainRequirements(domain: Cjadc2Domain): Cjadc2Requirement[]

assessAutonomousWeaponsCompliance(model: Gr00tModel, operation: MilitaryOperation): WeaponResult
getAutonomyLevels(): AutonomyLevel[]
getEngagementAuthorities(): EngagementAuthority[]
getHitlRequirements(): HumanInLoopRequirement[]
getLethalRestrictions(): string[]
```

### CJADC2 Operations Engine

```typescript
class Cjadc2Engine {
  assessDomain(domain: Cjadc2Domain, components: Cjadc2Component[]): DomainAssessment;
  assessInteroperability(components: Cjadc2Component[]): InteroperabilityAssessment;
  assessSecurity(components: Cjadc2Component[]): SecurityAssessment;
  generateOperationReport(operation: Cjadc2Operation, components: Cjadc2Component[]): OperationReport;
  mapToGr00t(components: Cjadc2Component[]): Gr00tAssessment;
}
```

### Agent Policy Firewall

```typescript
class AgentPolicyFirewall {
  evaluate(
    actor: FirewallActor,
    request: FirewallToolRequest,
    context: FirewallContext
  ): FirewallDecision;

  createReceipt(
    actor: FirewallActor,
    request: FirewallToolRequest,
    context: FirewallContext,
    decision: FirewallDecision
  ): FirewallReceipt;

  blockActor(actorId: string): void;
  unblockActor(actorId: string): void;
  addSoDRule(rule: SoDRule): void;
  getSoDRules(): SoDRule[];
  getCanaryTraps(): CanaryTrap[];
  getReplayEntries(): ReplayEntry[];
  getStats(): FirewallStats;
}

function formatFirewallReceiptForEvidenceGraph(receipt: FirewallReceipt): Record<string, unknown>;
```

### Key Types

```typescript
// GR00T Model
interface Gr00tModel {
  id: string;
  name: string;
  version: string;
  parameters: number;
  embodimentTag: EmbodimentTag;         // 'HUMANOID' | 'QUADRUPED' | 'AERIAL' | 'GROUND' | 'MARITIME' | 'INDUSTRIAL'
  capabilities: string[];
  exportClassification: SecurityClassification;
  trainingDataOrigin: string;
  weights: { precision: string; sizeBytes: number; sha256: string };
}

// CJADC2 Component
interface Cjadc2Component {
  id: string;
  name: string;
  type: ComponentType;
  domain: Cjadc2Domain[];
  classification: SecurityClassification;
  status: ComponentStatus;
  capabilities: string[];
  interoperability: InteroperabilityRequirement[];
  security: SecurityRequirement[];
}

// Firewall Decision
interface FirewallDecision {
  allowed: boolean;
  reason: string;
  sandbox: SandboxPolicy;
  requiresApproval: boolean;
  approvalThreshold: ApprovalThreshold;
  blastRadiusScore: number;
  controlImpact: string[];
  replayDetected: boolean;
  canaryTriggered: boolean;
  sodViolation: boolean;
  anomaliesDetected: string[];
  receiptHash: string;
}

// Compliance Report
interface ComplianceReport {
  id: string;
  timestamp: string;
  modelId: string;
  robotId: string;
  overallStatus: ControlStatus;
  overallScore: number;
  frameworkResults: ComplianceAssessment[];
  criticalFindings: ComplianceGap[];
  exportControlStatus: ExportControlStatus;
  CJADC2Readiness: Cjadc2Readiness;
  deploymentRecommendation: string;
}
```

---

## 12. Use Cases

### Military Humanoid Robot Deployment

Deploy GR00T humanoid robots for base security with full CJADC2 compliance:

```typescript
import {
  Gr00tComplianceEngine,
  checkItarCompliance,
  assessAutonomousWeaponsCompliance,
} from '@grc-claw/gr00t-compliance';
import { Cjadc2Engine, Cjadc2Domain, ComponentType, ComponentStatus, SecurityClassification } from '@grc-claw/cjadc2-operations';

// 1. Define model
const model: Gr00tModel = {
  id: 'groot-base-security-v1',
  name: 'GR00T Base Security Unit',
  version: '1.0.0',
  parameters: 70_000_000_000,
  embodimentTag: 'HUMANOID',
  capabilities: ['navigation', 'surveillance', 'human-in-the-loop', 'perimeter_security'],
  exportClassification: 'SECRET',
  trainingDataOrigin: 'NVIDIA curated defense simulation data',
  weights: { precision: 'bf16', sizeBytes: 140_000_000_000, sha256: 'sha256:base-sec-v1' },
};

// 2. Check ITAR
const itar = checkItarCompliance(model, ['US']);
console.log(`ITAR: ${itar.compliant ? 'PASS' : 'FAIL'}`);

// 3. Compliance report
const engine = new Gr00tComplianceEngine();
const report = engine.generateComplianceReport(model, deploymentConfig);
console.log(`Deployment: ${report.deploymentRecommendation}`);

// 4. CJADC2 readiness
const cjadc2 = new Cjadc2Engine();
const cjadc2Report = cjadc2.generateOperationReport(operation, components);
console.log(`CJADC2 Readiness: ${cjadc2Report.readinessStatus}`);
```

### Autonomous Weapons Policy Enforcement

Enforce HITL for lethal engagement operations:

```typescript
import { assessAutonomousWeaponsCompliance, getHitlRequirements, getLethalRestrictions } from '@grc-claw/gr00t-compliance';
import { AgentPolicyFirewall } from '@grc-claw/agent-policy-firewall';

// 1. Check weapons policy compliance
const lethalOp = {
  id: 'OP-DEF-001',
  name: 'Defensive Engagement',
  type: 'lethal',
  domain: 'LAND',
  classification: 'SECRET',
  permittedEmbodiments: ['HUMANOID'],
  humanOversightRequired: true,
  engagementAuthority: 'Defensive',
  rulesOfEngagement: 'Standard ROE',
};

const weaponResult = assessAutonomousWeaponsCompliance(grootModel, lethalOp);
if (!weaponResult.compliant) {
  console.log('BLOCKED: Weapons policy compliance failed');
  for (const gap of weaponResult.gaps) {
    console.log(`  ${gap.description}`);
  }
}

// 2. Enforce via firewall
const firewall = new AgentPolicyFirewall();
const engagementDecision = firewall.evaluate(
  { id: 'operator-001', type: 'human', role: 'engagement_officer' },
  { toolName: 'weapon.deploy', tier: 'destructive', args: { mode: 'defensive' } },
  {
    tenantScope: ['unit-alpha'],
    role: 'engagement_officer',
    allowedTools: ['weapon.deploy'],
    deniedTools: [],
    sandboxPolicy: 'docker',
    approvalThreshold: 'dual_control',
    dataBoundary: 'cui',
    replayWindowSeconds: 300,
    maxBlastRadius: 10,
    controlImpactIds: ['HITL-001', 'HITL-002', 'CJADC2-ACT-001'],
  }
);

console.log(`Engagement: ${engagementDecision.allowed ? 'APPROVED' : 'DENIED'}`);
console.log(`Requires Dual Approval: ${engagementDecision.requiresApproval}`);
```

### NATO Interoperability Validation

Validate GR00T deployment meets NATO STANAG requirements:

```typescript
import { Cjadc2Engine, InteroperabilityStandard } from '@grc-claw/cjadc2-operations';

const engine = new Cjadc2Engine();

// Components with STANAG compliance
const natoComponents = [
  {
    id: 'sensor-nato-001',
    name: 'NATO-Compatible Sensor Suite',
    type: ComponentType.SENSOR,
    domain: [Cjadc2Domain.SENSE, Cjadc2Domain.COMMUNICATE],
    classification: SecurityClassification.SECRET,
    status: ComponentStatus.OPERATIONAL,
    capabilities: ['STANAG_4586', 'STANAG_4607', 'STANAG_4406'],
    interoperability: [
      { protocol: 'STANAG 4586', standard: InteroperabilityStandard.STANAG_4586, version: '4.0', required: true, maxLatencyMs: 50, encryptionRequired: true },
      { protocol: 'STANAG 4607', standard: InteroperabilityStandard.STANAG_4607, version: '3.0', required: true },
      { protocol: 'STANAG 4406', standard: InteroperabilityStandard.STANAG_4406, version: '2.0', required: true, encryptionRequired: true },
    ],
    security: [
      { control: 'encryption', level: 'critical', status: 'met' },
      { control: 'authentication', level: 'high', status: 'met' },
    ],
  },
];

const interop = engine.assessInteroperability(natoComponents);
console.log(`NATO Interop: ${interop.score}/${interop.maxScore} (${interop.status})`);

for (const compliance of interop.compliance) {
  console.log(`  ${compliance.standard}: ${compliance.compliant ? 'COMPLIANT' : 'NON-COMPLIANT'}`);
}
```

### Defense Procurement Passport

Generate a procurement-ready compliance passport for defense buyers:

```typescript
import { Gr00tComplianceEngine } from '@grc-claw/gr00t-compliance';

const engine = new Gr00tComplianceEngine();
const report = engine.generateComplianceReport(model, deploymentConfig, operation);

// Export for procurement
const passport = {
  modelId: report.modelId,
  overallStatus: report.overallStatus,
  overallScore: report.overallScore,
  exportControl: report.exportControlStatus,
  cjadc2Readiness: report.CJADC2Readiness,
  frameworkResults: report.frameworkResults.map(r => ({
    framework: r.framework,
    score: r.overallScore,
    status: r.status,
  })),
  criticalFindings: report.criticalFindings.length,
  deploymentRecommendation: report.deploymentRecommendation,
  generatedAt: report.timestamp,
};

console.log(JSON.stringify(passport, null, 2));
```

---

## Appendix: Framework Reference

### Supported Frameworks

| Framework | Assessment Function | Package |
|-----------|-------------------|---------|
| ITAR (22 CFR 120) | `checkItarCompliance()` | `@grc-claw/gr00t-compliance` |
| EAR (ECCN 9A004) | `classifyItarCategory()` | `@grc-claw/gr00t-compliance` |
| DoD 5200.21 | `assessDodCompliance()` | `@grc-claw/gr00t-compliance` |
| NIST 800-171 | `assessDodCompliance()` | `@grc-claw/gr00t-compliance` |
| CMMC L1/L2/L3 | `assessDodCompliance(level)` | `@grc-claw/gr00t-compliance` |
| CJADC2 | `assessCjadc2Compliance()` | `@grc-claw/gr00t-compliance` |
| Autonomous Weapons Policy | `assessAutonomousWeaponsCompliance()` | `@grc-claw/gr00t-compliance` |
| NATO STANAG | `assessInteroperability()` | `@grc-claw/cjadc2-operations` |

### Security Classification Levels

| Level | Number | Description |
|-------|--------|-------------|
| UNCLASSIFIED | 0 | No classification restrictions |
| CONFIDENTIAL | 1 | Damage to national security |
| SECRET | 2 | Serious damage to national security |
| TOP_SECRET | 3 | Exceptional damage to national security |

### Embodiment ITAR Risk Scores

| Embodiment | Risk Score | Reason |
|-----------|-----------|--------|
| HUMANOID | 0.9 | Highest autonomous capability risk |
| AERIAL | 0.8 | Weaponization potential |
| MARITIME | 0.8 | Naval warfare applications |
| QUADRUPED | 0.7 | Multi-domain deployment risk |
| GROUND | 0.6 | Standard ground vehicle risk |
| INDUSTRIAL | 0.4 | Lowest defense applicability |
