export type AiRanFramework =
  | 'iso_42001'
  | 'nist_ai_rmf'
  | 'nist_csf'
  | 'nist_800_53'
  | 'soc2'
  | 'cmmc';

export type AiRanReadiness = 'ready' | 'conditional' | 'blocked';

export interface AiRanRuntimeMetadata {
  gpuProfile?: string;
  runtimeContainer?: string;
  deploymentZone?: string;
  tenantBoundary?: string;
  edgeProfile?: string;
}

export interface AiRanModelMetadata {
  provider?: 'nvidia_nim' | 'nim_compatible' | 'self_hosted' | 'openrouter' | 'other';
  modelFamily?: 'nemotron' | 'llama_nemotron' | 'other';
  modelId?: string;
  endpointMode?: 'managed_api' | 'self_hosted_nim' | 'local' | 'offline';
  reasoningBudget?: string;
  toolAllowlist?: string[];
}

export interface AiRanExperimentInput {
  experimentId: string;
  title: string;
  source:
    | 'nvidia_sionna'
    | 'nvidia_ai_aerial'
    | 'aerial_omniverse_digital_twin'
    | 'aerial_cuda_accelerated_ran'
    | 'sample_manifest'
    | 'operator_upload';
  scope: string;
  simulationSummary?: string;
  ranStack?: string;
  oranInterfaces?: string[];
  model?: AiRanModelMetadata;
  runtime?: AiRanRuntimeMetadata;
  evidenceHashes?: string[];
  controls?: AiRanFramework[];
  humanApproval?: {
    required: boolean;
    approverRole?: string;
    approvalRecordId?: string;
  };
  limitations?: string[];
}

export interface AiRanControlMapping {
  framework: AiRanFramework;
  controlTheme: string;
  assuranceQuestion: string;
}

export interface AiRanAssuranceEnvelope {
  schema: 'grc_claw.ai_ran_assurance.v1';
  generatedAt: string;
  assuranceType: 'ai_ran_6g';
  experimentId: string;
  title: string;
  source: AiRanExperimentInput['source'];
  scope: string;
  ranStack: string;
  model: Required<Pick<AiRanModelMetadata, 'provider' | 'modelFamily' | 'modelId' | 'endpointMode'>>;
  runtime: AiRanRuntimeMetadata;
  evidenceHashes: string[];
  controlMappings: AiRanControlMapping[];
  riskScore: number;
  deploymentReadiness: AiRanReadiness;
  requiredActions: string[];
  safetyBoundary: string[];
  a2zSocPayload: {
    artifactType: 'ai_ran_assurance_envelope';
    recommendedRoute: '/ai-ran-6g-assurance';
    tags: string[];
  };
}

export const AI_RAN_DEFAULT_CONTROLS: AiRanFramework[] = [
  'iso_42001',
  'nist_ai_rmf',
  'nist_csf',
  'nist_800_53',
  'soc2',
  'cmmc',
];

export const AI_RAN_CONTROL_MAPPINGS: Record<AiRanFramework, AiRanControlMapping> = {
  iso_42001: {
    framework: 'iso_42001',
    controlTheme: 'AI management system and model lifecycle accountability',
    assuranceQuestion: 'Is the AI-RAN model/system scope, owner, intended use, oversight, and change process documented?',
  },
  nist_ai_rmf: {
    framework: 'nist_ai_rmf',
    controlTheme: 'Govern, map, measure, and manage AI risk',
    assuranceQuestion: 'Are AI-RAN assumptions, limitations, runtime risks, and monitoring obligations explicitly measured and managed?',
  },
  nist_csf: {
    framework: 'nist_csf',
    controlTheme: 'Critical infrastructure cybersecurity posture',
    assuranceQuestion: 'Can the operator trace AI-RAN assets, dependencies, events, controls, and response obligations?',
  },
  nist_800_53: {
    framework: 'nist_800_53',
    controlTheme: 'Federal control evidence for systems and organizations',
    assuranceQuestion: 'Are auditability, configuration, access, contingency, and system integrity facts retained for assessor review?',
  },
  soc2: {
    framework: 'soc2',
    controlTheme: 'Security, availability, confidentiality, and processing integrity evidence',
    assuranceQuestion: 'Can the system produce auditor-readable evidence without relying on screenshots or unverifiable claims?',
  },
  cmmc: {
    framework: 'cmmc',
    controlTheme: 'Defense supplier readiness and CUI-adjacent procurement posture',
    assuranceQuestion: 'Can the deployment boundary, evidence handling, access control, and incident process support defense procurement review?',
  },
};

const SAFETY_BOUNDARY = [
  'Assurance-only: no live RAN optimization commands are generated.',
  'No RF interference, jamming, interception, exploitation, or spectrum-control guidance is produced.',
  'Human operator authority remains external to the envelope.',
  'Private NVIDIA, operator, government, or customer data is not required for deterministic assessment.',
];

export function assessAiRanExperiment(input: AiRanExperimentInput): AiRanAssuranceEnvelope {
  const evidenceHashes = [...new Set(input.evidenceHashes ?? [])].filter(Boolean);
  const controls = input.controls?.length ? input.controls : AI_RAN_DEFAULT_CONTROLS;
  const controlMappings = controls.map((framework) => AI_RAN_CONTROL_MAPPINGS[framework]);
  const requiredActions = buildRequiredActions(input, evidenceHashes);
  const riskScore = scoreRisk(input, evidenceHashes, requiredActions);

  return {
    schema: 'grc_claw.ai_ran_assurance.v1',
    generatedAt: new Date().toISOString(),
    assuranceType: 'ai_ran_6g',
    experimentId: input.experimentId,
    title: input.title,
    source: input.source,
    scope: input.scope,
    ranStack: input.ranStack ?? sourceToRanStack(input.source),
    model: {
      provider: input.model?.provider ?? 'nvidia_nim',
      modelFamily: input.model?.modelFamily ?? 'nemotron',
      modelId: input.model?.modelId ?? 'nemotron-or-nim-compatible-model',
      endpointMode: input.model?.endpointMode ?? 'managed_api',
    },
    runtime: input.runtime ?? {},
    evidenceHashes,
    controlMappings,
    riskScore,
    deploymentReadiness: readinessFromRisk(riskScore, requiredActions),
    requiredActions,
    safetyBoundary: [...SAFETY_BOUNDARY, ...(input.limitations ?? [])],
    a2zSocPayload: {
      artifactType: 'ai_ran_assurance_envelope',
      recommendedRoute: '/ai-ran-6g-assurance',
      tags: ['ai-ran', '6g', input.source, input.model?.modelFamily ?? 'nemotron', 'assurance-envelope'],
    },
  };
}

export function createSampleAiRanAssuranceEnvelope(): AiRanAssuranceEnvelope {
  return assessAiRanExperiment({
    experimentId: 'sample-ai-ran-sionna-nim-001',
    title: 'Sionna-to-NIM AI-RAN assurance review',
    source: 'nvidia_sionna',
    scope: 'Sample 6G research manifest converted into procurement-safe assurance evidence.',
    simulationSummary: 'Link-level / system-level simulation metadata with AI receiver assumptions and deployment limits.',
    ranStack: 'NVIDIA Sionna + NVIDIA AI Aerial reference workflow',
    oranInterfaces: ['O-RAN 7.2x evidence context'],
    model: {
      provider: 'nvidia_nim',
      modelFamily: 'nemotron',
      modelId: 'nemotron-governance-agent',
      endpointMode: 'managed_api',
      reasoningBudget: 'bounded',
      toolAllowlist: ['ai_ran.assess_experiment', 'evidence.export', 'grc.list_controls'],
    },
    runtime: {
      gpuProfile: 'NVIDIA accelerated research or edge GPU',
      runtimeContainer: 'NIM-compatible inference container',
      deploymentZone: 'lab / digital twin / pre-production edge',
      tenantBoundary: 'single tenant evidence scope',
    },
    evidenceHashes: ['sha256:sample-sionna-manifest', 'sha256:sample-nim-model-card'],
    humanApproval: { required: true, approverRole: 'AI-RAN assurance owner' },
  });
}

function buildRequiredActions(input: AiRanExperimentInput, evidenceHashes: string[]): string[] {
  const actions: string[] = [];
  if (!evidenceHashes.length) actions.push('Attach at least one signed simulation, model-card, runtime, or deployment evidence hash.');
  if (!input.humanApproval?.required) actions.push('Define human approval before deployment or external evidence sharing.');
  if (!input.model?.toolAllowlist?.length) actions.push('Record the NIM/Nemotron agent tool allowlist and prohibited actions.');
  if (!input.runtime?.tenantBoundary) actions.push('Document runtime tenant boundary, edge zone, or lab/deployment scope.');
  if (!input.limitations?.length) actions.push('Document known model, simulation, and deployment limitations.');
  return actions;
}

function scoreRisk(input: AiRanExperimentInput, evidenceHashes: string[], requiredActions: string[]): number {
  let score = 22;
  score += requiredActions.length * 12;
  if (!evidenceHashes.length) score += 14;
  if (input.source === 'operator_upload') score += 10;
  if (input.model?.endpointMode === 'managed_api' && !input.runtime?.tenantBoundary) score += 8;
  if (input.humanApproval?.required && input.humanApproval.approverRole) score -= 8;
  if (input.model?.toolAllowlist?.length) score -= 6;
  if (input.runtime?.runtimeContainer) score -= 4;
  return Math.max(0, Math.min(100, score));
}

function readinessFromRisk(riskScore: number, requiredActions: string[]): AiRanReadiness {
  if (riskScore >= 70 || requiredActions.length >= 4) return 'blocked';
  if (riskScore >= 35 || requiredActions.length > 0) return 'conditional';
  return 'ready';
}

function sourceToRanStack(source: AiRanExperimentInput['source']): string {
  switch (source) {
    case 'nvidia_sionna':
      return 'NVIDIA Sionna research workflow';
    case 'nvidia_ai_aerial':
      return 'NVIDIA AI Aerial workflow';
    case 'aerial_omniverse_digital_twin':
      return 'NVIDIA Aerial Omniverse Digital Twin workflow';
    case 'aerial_cuda_accelerated_ran':
      return 'NVIDIA Aerial CUDA-Accelerated RAN workflow';
    case 'operator_upload':
      return 'Operator-provided AI-RAN manifest';
    case 'sample_manifest':
    default:
      return 'Sample AI-RAN assurance manifest';
  }
}
