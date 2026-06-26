import type { AgentDefinition } from "../types.js";

export const POLICY_GUARDIAN: AgentDefinition = {
  id: "agent-policy-guardian",
  name: "Policy Guardian",
  description:
    "Monitors organizational policies for expiration, drift, and compliance alignment. Alerts when policies need review or update.",
  version: "1.0.0",
  trigger: {
    type: "schedule",
    config: { cron: "0 8 * * 1" }, // Every Monday at 8 AM
  },
  tasks: [
    {
      id: "scan-policies",
      type: "scan_controls",
      label: "Scan policy compliance",
      params: { scope: "policies", includeExpired: true, includeDraft: false },
    },
    {
      id: "check-evidence",
      type: "check_evidence",
      label: "Check policy evidence",
      params: { evidenceType: "policy_attestation", freshnessDays: 90 },
      dependsOn: ["scan-policies"],
    },
    {
      id: "analyze-risk",
      type: "analyze_risk",
      label: "Analyze policy risk",
      params: { riskModel: "policy_drift" },
      dependsOn: ["check-evidence"],
    },
  ],
  actions: [
    {
      id: "notify-review",
      type: "send_notification",
      label: "Notify policy owners",
      params: { channel: "#policy-compliance", severity: "medium" },
      dependsOn: ["analyze-risk"],
    },
    {
      id: "create-finding",
      type: "create_finding",
      label: "Create policy finding",
      params: { severity: "medium", category: "policy_governance" },
      dependsOn: ["analyze-risk"],
    },
  ],
  tags: ["policy", "governance", "compliance"],
  enabled: true,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

export const CONTROL_ASSESSMENT: AgentDefinition = {
  id: "agent-control-assessment",
  name: "Control Assessment",
  description:
    "Automated assessment of security controls against framework requirements. Evaluates implementation status and evidence quality.",
  version: "1.0.0",
  trigger: {
    type: "schedule",
    config: { cron: "0 6 1 * *" }, // 1st of every month at 6 AM
  },
  tasks: [
    {
      id: "scan-controls",
      type: "scan_controls",
      label: "Scan all controls",
      params: { frameworks: ["iso27001", "soc2", "nist-csf"], includePartial: true },
    },
    {
      id: "check-evidence",
      type: "check_evidence",
      label: "Validate evidence",
      params: { validateHash: true, checkFreshness: true, maxAgeDays: 365 },
      dependsOn: ["scan-controls"],
    },
    {
      id: "analyze-risk",
      type: "analyze_risk",
      label: "Risk analysis",
      params: { includeBlastRadius: true, quantificationModel: "monte_carlo" },
      dependsOn: ["check-evidence"],
    },
    {
      id: "generate-report",
      type: "generate_report",
      label: "Generate assessment report",
      params: { format: "detailed", includeRemediation: true },
      dependsOn: ["analyze-risk"],
    },
  ],
  actions: [
    {
      id: "create-findings",
      type: "create_finding",
      label: "Create control findings",
      params: { severity: "high", autoAssign: true },
      dependsOn: ["analyze-risk"],
    },
    {
      id: "update-status",
      type: "update_status",
      label: "Update compliance status",
      params: { statusField: "lastAssessment" },
      dependsOn: ["generate-report"],
    },
  ],
  tags: ["assessment", "controls", "audit"],
  enabled: true,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

export const EVIDENCE_ANALYZER: AgentDefinition = {
  id: "agent-evidence-analyzer",
  name: "Evidence Analyzer",
  description:
    "Analyzes collected evidence for completeness, integrity, and freshness. Flags stale or missing evidence for control compliance.",
  version: "1.0.0",
  trigger: {
    type: "event",
    config: { eventName: "evidence.collected", webhookPath: "/webhooks/evidence" },
  },
  tasks: [
    {
      id: "check-evidence",
      type: "check_evidence",
      label: "Analyze evidence quality",
      params: {
        validateIntegrity: true,
        checkCompleteness: true,
        verifyTimestamps: true,
        expectedEvidenceTypes: ["screenshot", "log", "config", "certificate"],
      },
    },
    {
      id: "analyze-risk",
      type: "analyze_risk",
      label: "Assess evidence gap risk",
      params: { model: "evidence_completeness" },
      dependsOn: ["check-evidence"],
    },
  ],
  actions: [
    {
      id: "notify-gap",
      type: "send_notification",
      label: "Notify evidence gap",
      params: { channel: "#evidence-tracking", severity: "high" },
      dependsOn: ["analyze-risk"],
    },
    {
      id: "ticket-gap",
      type: "create_ticket",
      label: "Create evidence ticket",
      params: { project: "COMPLIANCE", type: "evidence_gap", priority: "High" },
      dependsOn: ["analyze-risk"],
    },
  ],
  tags: ["evidence", "quality", "monitoring"],
  enabled: true,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

export const AUDIT_READINESS: AgentDefinition = {
  id: "agent-audit-readiness",
  name: "Audit Readiness",
  description:
    "Pre-audit readiness check that validates all controls, evidence, and documentation are audit-ready. Generates a readiness scorecard.",
  version: "1.0.0",
  trigger: {
    type: "manual",
    config: { enabled: true },
  },
  tasks: [
    {
      id: "scan-controls",
      type: "scan_controls",
      label: "Full control scan",
      params: { scope: "all", strict: true },
    },
    {
      id: "check-evidence",
      type: "check_evidence",
      label: "Evidence completeness check",
      params: { requireAll: true, strictValidation: true },
      dependsOn: ["scan-controls"],
    },
    {
      id: "analyze-risk",
      type: "analyze_risk",
      label: "Audit risk analysis",
      params: { model: "audit_readiness", includeGapAnalysis: true },
      dependsOn: ["check-evidence"],
    },
    {
      id: "generate-report",
      type: "generate_report",
      label: "Readiness scorecard",
      params: { format: "scorecard", includeActionPlan: true, includeTimeline: true },
      dependsOn: ["analyze-risk"],
    },
  ],
  actions: [
    {
      id: "update-status",
      type: "update_status",
      label: "Mark audit status",
      params: { field: "auditReadiness", values: ["ready", "needs_work", "not_ready"] },
      dependsOn: ["generate-report"],
    },
    {
      id: "notify-leadership",
      type: "send_notification",
      label: "Notify leadership",
      params: { channel: "#audit-readiness", includeScorecard: true },
      dependsOn: ["generate-report"],
    },
    {
      id: "create-findings",
      type: "create_finding",
      label: "Create readiness findings",
      params: { severity: "critical", category: "audit_gap" },
      dependsOn: ["analyze-risk"],
    },
  ],
  tags: ["audit", "readiness", "scorecard"],
  enabled: true,
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

export const PREBUILT_AGENTS: AgentDefinition[] = [
  POLICY_GUARDIAN,
  CONTROL_ASSESSMENT,
  EVIDENCE_ANALYZER,
  AUDIT_READINESS,
];
