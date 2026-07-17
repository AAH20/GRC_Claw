export type InfraAgentFramework =
  | 'soc2'
  | 'iso_42001'
  | 'iso_27001'
  | 'dora'
  | 'nist_csf'
  | 'nist_800_53';

export type InfraAgentReadiness = 'ready' | 'conditional' | 'blocked';

export type InfraAgentActionTier = 'read' | 'write' | 'destructive' | 'provision' | 'decommission';

export type InfraAgentSource =
  | 'iac_generator'
  | 'k8s_operator'
  | 'ci_cd_agent'
  | 'devops_autopilot'
  | 'custom_agent'
  | 'operator_upload';

export type CredentialHandlingMethod =
  | 'secret_substitution'
  | 'vault_injected'
  | 'scoped_token'
  | 'plaintext_env'
  | 'unknown';

export interface InfraAgentModelMetadata {
  provider?: 'anthropic' | 'openai' | 'open_weight' | 'self_hosted' | 'other';
  modelId?: string;
  endpointMode?: 'managed_api' | 'self_hosted' | 'local' | 'offline';
  toolAllowlist?: string[];
}

export interface InfraAgentScopeMetadata {
  actionTiers?: InfraAgentActionTier[];
  targetEnvironment?: 'dev' | 'staging' | 'production' | 'multi_environment';
  credentialHandling?: CredentialHandlingMethod;
  secretExposureCount?: number;
  networkGuardrails?: string[];
  destructiveActionsBlocked?: boolean;
}

export interface InfraAgentRuntimeMetadata {
  deploymentZone?: string;
  loggingMode?: string;
  humanApprovalGate?: {
    present: boolean;
    mechanism?: string;
    lastTestedAt?: string;
  };
}

export interface InfraAgentSystemInput {
  systemId: string;
  title: string;
  source: InfraAgentSource;
  scope: string;
  model?: InfraAgentModelMetadata;
  actionScope?: InfraAgentScopeMetadata;
  runtime?: InfraAgentRuntimeMetadata;
  evidenceHashes?: string[];
  controls?: InfraAgentFramework[];
  humanApproval?: {
    required: boolean;
    approverRole?: string;
    approvalRecordId?: string;
  };
  limitations?: string[];
}

export interface InfraAgentControlMapping {
  framework: InfraAgentFramework;
  controlTheme: string;
  assuranceQuestion: string;
}

export interface InfraAgentAssuranceEnvelope {
  schema: 'grc_claw.infra_agent_assurance.v1';
  generatedAt: string;
  assuranceType: 'infra_agent_devops_autonomy';
  systemId: string;
  title: string;
  source: InfraAgentSource;
  scope: string;
  model: Required<Pick<InfraAgentModelMetadata, 'provider' | 'modelId' | 'endpointMode'>>;
  actionScope: Required<Pick<InfraAgentScopeMetadata, 'actionTiers' | 'targetEnvironment' | 'credentialHandling'>>;
  runtime: InfraAgentRuntimeMetadata;
  evidenceHashes: string[];
  controlMappings: InfraAgentControlMapping[];
  riskScore: number;
  deploymentReadiness: InfraAgentReadiness;
  requiredActions: string[];
  changeBoundary: string[];
  a2zSocPayload: {
    artifactType: 'infra_agent_assurance_envelope';
    recommendedRoute: '/infra-agent-assurance';
    tags: string[];
  };
}

export const INFRA_AGENT_DEFAULT_CONTROLS: InfraAgentFramework[] = [
  'soc2',
  'iso_42001',
  'iso_27001',
  'dora',
  'nist_csf',
  'nist_800_53',
];

export const INFRA_AGENT_CONTROL_MAPPINGS: Record<InfraAgentFramework, InfraAgentControlMapping> = {
  soc2: {
    framework: 'soc2',
    controlTheme: 'Change management and processing integrity evidence for autonomous infrastructure changes',
    assuranceQuestion: 'Can the agent produce auditor-readable evidence for every infrastructure change it made, who authorized it, and when?',
  },
  iso_42001: {
    framework: 'iso_42001',
    controlTheme: 'AI management system accountability for an autonomous infrastructure agent',
    assuranceQuestion: 'Is the agent\'s scope, intended use, oversight model, and change-approval process documented?',
  },
  iso_27001: {
    framework: 'iso_27001',
    controlTheme: 'Information security controls for credential handling and system access',
    assuranceQuestion: 'Does the agent handle credentials, secrets, and access scopes in a documented, least-privilege manner?',
  },
  dora: {
    framework: 'dora',
    controlTheme: 'ICT change and operational resilience risk for autonomous infrastructure actions',
    assuranceQuestion: 'Is every agent-driven infrastructure change classified, reversible, and reportable within the entity\'s incident and change-management process?',
  },
  nist_csf: {
    framework: 'nist_csf',
    controlTheme: 'Identity, detection, response, and recovery posture for infrastructure agents',
    assuranceQuestion: 'Can the operator trace the agent\'s identity, credentials, network boundary, logs, and incident response obligations?',
  },
  nist_800_53: {
    framework: 'nist_800_53',
    controlTheme: 'Federal control evidence for automated configuration management',
    assuranceQuestion: 'Are auditability, configuration management, access control, and system integrity facts retained for every agent action?',
  },
};

const CHANGE_BOUNDARY = [
  'Assurance-only: no infrastructure-as-code, deployment commands, or credential material are generated or executed.',
  'No production access, secret material, or live system state is required for deterministic assessment.',
  'Human operator, security, and change-approval authority remain external to the envelope.',
];

export function assessInfraAgentSystem(input: InfraAgentSystemInput): InfraAgentAssuranceEnvelope {
  const evidenceHashes = [...new Set(input.evidenceHashes ?? [])].filter(Boolean);
  const controls = input.controls?.length ? input.controls : INFRA_AGENT_DEFAULT_CONTROLS;
  const controlMappings = controls.map((framework) => INFRA_AGENT_CONTROL_MAPPINGS[framework]);
  const requiredActions = buildRequiredActions(input, evidenceHashes);
  const riskScore = scoreRisk(input, evidenceHashes, requiredActions);

  return {
    schema: 'grc_claw.infra_agent_assurance.v1',
    generatedAt: new Date().toISOString(),
    assuranceType: 'infra_agent_devops_autonomy',
    systemId: input.systemId,
    title: input.title,
    source: input.source,
    scope: input.scope,
    model: {
      provider: input.model?.provider ?? 'other',
      modelId: input.model?.modelId ?? 'unspecified-devops-agent-model',
      endpointMode: input.model?.endpointMode ?? 'self_hosted',
    },
    actionScope: {
      actionTiers: input.actionScope?.actionTiers ?? ['read'],
      targetEnvironment: input.actionScope?.targetEnvironment ?? 'dev',
      credentialHandling: input.actionScope?.credentialHandling ?? 'unknown',
    },
    runtime: input.runtime ?? {},
    evidenceHashes,
    controlMappings,
    riskScore,
    deploymentReadiness: readinessFromRisk(riskScore, requiredActions),
    requiredActions,
    changeBoundary: [...CHANGE_BOUNDARY, ...(input.limitations ?? [])],
    a2zSocPayload: {
      artifactType: 'infra_agent_assurance_envelope',
      recommendedRoute: '/infra-agent-assurance',
      tags: ['infra-agent', 'devops-autonomy', input.source, 'assurance-envelope'],
    },
  };
}

export function createSampleInfraAgentAssuranceEnvelope(): InfraAgentAssuranceEnvelope {
  return assessInfraAgentSystem({
    systemId: 'sample-infra-agent-001',
    title: 'Autonomous IaC/DevOps agent assurance review',
    source: 'devops_autopilot',
    scope: 'Sample autonomous infrastructure agent manifest converted into compliance and procurement evidence.',
    model: {
      provider: 'open_weight',
      modelId: 'devops-autopilot-or-compatible-agent',
      endpointMode: 'self_hosted',
      toolAllowlist: ['infra.generate_iac', 'infra.apply_change', 'infra.debug_cluster', 'evidence.export'],
    },
    actionScope: {
      actionTiers: ['read', 'write', 'provision'],
      targetEnvironment: 'production',
      credentialHandling: 'secret_substitution',
      secretExposureCount: 0,
      networkGuardrails: ['destructive-action-network-block', 'scoped-service-account'],
      destructiveActionsBlocked: true,
    },
    runtime: {
      deploymentZone: 'customer-owned infrastructure, no data leaves environment',
      loggingMode: 'append-only agent action and approval log',
      humanApprovalGate: { present: true, mechanism: 'human-in-the-loop approval for provision/decommission tiers' },
    },
    evidenceHashes: ['sha256:sample-agent-policy-firewall-receipt', 'sha256:sample-change-log'],
    humanApproval: { required: true, approverRole: 'Infrastructure change owner' },
    limitations: ['Sample envelope is for governance and evidence demonstration only.'],
  });
}

function buildRequiredActions(input: InfraAgentSystemInput, evidenceHashes: string[]): string[] {
  const actions: string[] = [];
  if (!evidenceHashes.length) actions.push('Attach at least one signed change-log, firewall receipt, or approval evidence hash.');
  if (!input.humanApproval?.required) actions.push('Define human approval for destructive, provision, or decommission-tier actions.');
  if (!input.model?.toolAllowlist?.length) actions.push('Record the infrastructure agent tool allowlist and prohibited actions.');
  if (!input.actionScope?.credentialHandling || input.actionScope.credentialHandling === 'unknown' || input.actionScope.credentialHandling === 'plaintext_env') {
    actions.push('Document credential handling method; plaintext or unknown credential exposure to the model is not acceptable for production-tier evidence.');
  }
  if (!input.actionScope?.networkGuardrails?.length) actions.push('Document network-level guardrails blocking unauthorized destructive actions.');
  if (!input.runtime?.humanApprovalGate?.present) actions.push('Attach human-approval-gate evidence and latest test status.');
  if (!input.limitations?.length) actions.push('Document known agent, model, and deployment limitations.');
  return actions;
}

function scoreRisk(input: InfraAgentSystemInput, evidenceHashes: string[], requiredActions: string[]): number {
  let score = 24;
  score += requiredActions.length * 11;
  if (!evidenceHashes.length) score += 14;
  if (input.source === 'operator_upload') score += 10;
  if (input.actionScope?.targetEnvironment === 'production' || input.actionScope?.targetEnvironment === 'multi_environment') score += 8;
  if (input.actionScope?.actionTiers?.includes('decommission')) score += 10;
  if (input.actionScope?.credentialHandling === 'plaintext_env') score += 16;
  if (input.actionScope?.credentialHandling === 'unknown') score += 10;
  if (input.humanApproval?.required && input.humanApproval.approverRole) score -= 8;
  if (input.model?.toolAllowlist?.length) score -= 6;
  if (input.actionScope?.credentialHandling === 'secret_substitution' || input.actionScope?.credentialHandling === 'vault_injected') score -= 8;
  if (input.actionScope?.destructiveActionsBlocked) score -= 6;
  if (input.runtime?.humanApprovalGate?.present) score -= 8;
  return Math.max(0, Math.min(100, score));
}

function readinessFromRisk(riskScore: number, requiredActions: string[]): InfraAgentReadiness {
  if (riskScore >= 70 || requiredActions.length >= 5) return 'blocked';
  if (riskScore >= 30 || requiredActions.length > 0) return 'conditional';
  return 'ready';
}
