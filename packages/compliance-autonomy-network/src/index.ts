// ============================================================================
// Compliance Autonomy Network (CAN) – Main Entry Point
//
// Multi-agent swarm orchestrator for autonomous compliance across
// SOC 2, ISO 27001, NIST CSF, PCI DSS, HIPAA, GDPR, CCPA, SOX,
// FedRAMP, and custom frameworks.
// ============================================================================

// --- Types ---
export type {
  ComplianceFramework,
  TaskPriority,
  AgentRole,
  TaskStatus,
  EvidenceKind,
  RiskLevel,
  TrustSignature,
  TrustChainLink,
  SwarmTask,
  TaskType,
  TaskInput,
  EvidenceCriteria,
  RiskScope,
  AuditWindow,
  RemediationPlanInput,
  SwarmAgent,
  AgentStatus,
  AgentCapability,
  SwarmResult,
  TaskOutput,
  EvidenceItem,
  ControlStatus,
  Finding,
  RiskAssessment,
  FrameworkRiskBreakdown,
  RiskItem,
  AuditPackage,
  AuditSection,
  AuditGap,
  RemediationResult,
  VerificationResult,
  CrossFrameworkMapping,
  AgentMessage,
  MessageType,
  MessagePayload,
  TaskDelegationPayload,
  TaskCompletedPayload,
  TaskFailedPayload,
  EvidenceSharedPayload,
  RiskAlertPayload,
  StatusUpdatePayload,
  PolicyViolationPayload,
  CoordinationRequestPayload,
  AuditReadyPayload,
  ComplianceGoal,
  GoalDecomposition,
  ExecutionPlan,
  ExecutionPhase,
  ComplianceReport,
  EvidenceSummary,
  RemediationSummary,
  SwarmCoordinatorConfig,
} from "./types.js";

// --- Agents ---
export { BaseAgent } from "./agents/base-agent.js";
export { EvidenceCollector } from "./agents/evidence-collector.js";
export { ControlTester } from "./agents/control-tester.js";
export { RiskQuantifier } from "./agents/risk-quantifier.js";
export { AuditPreparer } from "./agents/audit-preparer.js";
export { RemediationExecutorAgent } from "./agents/remediation-executor.js";
export { Verifier } from "./agents/verifier.js";

// --- Coordinator ---
export { SwarmCoordinator } from "./swarm-coordinator.js";

// --- Convenience re-export of types as values for runtime checks ---
import type {
  ComplianceFramework,
  AgentRole,
  TaskPriority,
  TaskStatus,
  RiskLevel,
  SwarmCoordinatorConfig,
} from "./types.js";

/**
 * Factory helper – create a pre-configured SwarmCoordinator.
 */
export async function createSwarm(config?: Partial<SwarmCoordinatorConfig>): Promise<
  InstanceType<typeof import("./swarm-coordinator.js").SwarmCoordinator>
> {
  const { SwarmCoordinator } = await import("./swarm-coordinator.js");
  return new SwarmCoordinator(config);
}

/**
 * All supported compliance frameworks.
 */
export const SUPPORTED_FRAMEWORKS: ComplianceFramework[] = [
  "SOC2",
  "ISO27001",
  "NIST_CSF",
  "PCI_DSS",
  "HIPAA",
  "GDPR",
  "CCPA",
  "SOX",
  "FedRAMP",
  "Custom",
];

/**
 * All agent roles in the CAN swarm.
 */
export const AGENT_ROLES: AgentRole[] = [
  "evidence-collector",
  "control-tester",
  "risk-quantifier",
  "audit-preparer",
  "remediation-executor",
  "verifier",
];
