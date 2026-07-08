export type PhysicalAiFramework =
  | 'iso_42001'
  | 'nist_ai_rmf'
  | 'nist_csf'
  | 'nist_800_53'
  | 'soc2'
  | 'cmmc';

export type PhysicalAiReadiness = 'ready' | 'conditional' | 'blocked';

export type HumanoidVlaSource =
  | 'nvidia_isaac_groot'
  | 'isaac_lab'
  | 'isaac_sim'
  | 'humanoid_vla_manifest'
  | 'sample_manifest'
  | 'operator_upload';

export interface PhysicalAiModelMetadata {
  provider?: 'nvidia' | 'nvidia_compatible' | 'open_weight' | 'self_hosted' | 'other';
  modelFamily?: 'isaac_gr00t' | 'humanoid_vla' | 'foundation_vla' | 'other';
  modelId?: string;
  endpointMode?: 'managed_api' | 'self_hosted' | 'local' | 'offline';
  datasetBoundary?: string;
  toolAllowlist?: string[];
}

export interface PhysicalAiEmbodimentMetadata {
  robotClass?: 'humanoid' | 'legged' | 'mobile_manipulator' | 'industrial' | 'simulation_only' | 'other';
  sensors?: string[];
  actuatorClasses?: string[];
  autonomyMode?: 'simulation_only' | 'teleoperated' | 'supervised_autonomy' | 'bounded_autonomy';
  operatingDomain?: 'lab' | 'warehouse' | 'industrial' | 'critical_infrastructure' | 'defense_supplier_lab' | 'other';
  prohibitedActionClasses?: string[];
}

export interface PhysicalAiRuntimeMetadata {
  gpuProfile?: string;
  runtimeContainer?: string;
  deploymentZone?: string;
  networkBoundary?: string;
  loggingMode?: string;
  emergencyStop?: {
    present: boolean;
    mechanism?: string;
    lastTestedAt?: string;
  };
}

export interface PhysicalAiSystemInput {
  systemId: string;
  title: string;
  source: HumanoidVlaSource;
  scope: string;
  model?: PhysicalAiModelMetadata;
  embodiment?: PhysicalAiEmbodimentMetadata;
  runtime?: PhysicalAiRuntimeMetadata;
  simulationSummary?: string;
  evidenceHashes?: string[];
  controls?: PhysicalAiFramework[];
  humanApproval?: {
    required: boolean;
    approverRole?: string;
    approvalRecordId?: string;
  };
  limitations?: string[];
}

export interface PhysicalAiControlMapping {
  framework: PhysicalAiFramework;
  controlTheme: string;
  assuranceQuestion: string;
}

export interface PhysicalAiAssuranceEnvelope {
  schema: 'grc_claw.physical_ai_assurance.v1';
  generatedAt: string;
  assuranceType: 'physical_ai_humanoid_vla';
  systemId: string;
  title: string;
  source: HumanoidVlaSource;
  scope: string;
  model: Required<Pick<PhysicalAiModelMetadata, 'provider' | 'modelFamily' | 'modelId' | 'endpointMode'>>;
  embodiment: Required<Pick<PhysicalAiEmbodimentMetadata, 'robotClass' | 'autonomyMode' | 'operatingDomain'>>;
  runtime: PhysicalAiRuntimeMetadata;
  evidenceHashes: string[];
  controlMappings: PhysicalAiControlMapping[];
  riskScore: number;
  deploymentReadiness: PhysicalAiReadiness;
  requiredActions: string[];
  safetyBoundary: string[];
  a2zSocPayload: {
    artifactType: 'physical_ai_assurance_envelope';
    recommendedRoute: '/physical-ai-humanoid-assurance';
    tags: string[];
  };
}

export const PHYSICAL_AI_DEFAULT_CONTROLS: PhysicalAiFramework[] = [
  'iso_42001',
  'nist_ai_rmf',
  'nist_csf',
  'nist_800_53',
  'soc2',
  'cmmc',
];

export const PHYSICAL_AI_CONTROL_MAPPINGS: Record<PhysicalAiFramework, PhysicalAiControlMapping> = {
  iso_42001: {
    framework: 'iso_42001',
    controlTheme: 'AI management system accountability for embodied AI',
    assuranceQuestion: 'Is the humanoid VLA system scope, intended use, oversight model, lifecycle owner, and change process documented?',
  },
  nist_ai_rmf: {
    framework: 'nist_ai_rmf',
    controlTheme: 'Govern, map, measure, and manage physical AI risk',
    assuranceQuestion: 'Are model limitations, action boundaries, runtime risks, and human oversight obligations explicitly measured and managed?',
  },
  nist_csf: {
    framework: 'nist_csf',
    controlTheme: 'Cyber-physical asset, identity, detection, response, and recovery posture',
    assuranceQuestion: 'Can the operator trace robotics assets, credentials, network boundaries, logs, incidents, and response obligations?',
  },
  nist_800_53: {
    framework: 'nist_800_53',
    controlTheme: 'Federal control evidence for high-impact systems',
    assuranceQuestion: 'Are auditability, configuration management, access control, contingency planning, and system integrity facts retained?',
  },
  soc2: {
    framework: 'soc2',
    controlTheme: 'Security, availability, confidentiality, and processing integrity evidence',
    assuranceQuestion: 'Can the system produce auditor-readable evidence for model/runtime changes, operator approval, and cyber-physical safeguards?',
  },
  cmmc: {
    framework: 'cmmc',
    controlTheme: 'Defense supplier readiness and CUI-adjacent procurement posture',
    assuranceQuestion: 'Can the deployment boundary, evidence handling, access control, incident process, and supplier review support defense procurement?',
  },
};

const SAFETY_BOUNDARY = [
  'Assurance-only: no robot motion plans, tactical instructions, target selection, autonomous weapon control, or live actuator commands are generated.',
  'No combat optimization, evasion, breach, payload guidance, or operational attack guidance is produced.',
  'Human operator, safety officer, legal, and command authority remain external to the envelope.',
  'Private NVIDIA, customer, government, operator, or deployment data is not required for deterministic assessment.',
];

export function assessPhysicalAiSystem(input: PhysicalAiSystemInput): PhysicalAiAssuranceEnvelope {
  const evidenceHashes = [...new Set(input.evidenceHashes ?? [])].filter(Boolean);
  const controls = input.controls?.length ? input.controls : PHYSICAL_AI_DEFAULT_CONTROLS;
  const controlMappings = controls.map((framework) => PHYSICAL_AI_CONTROL_MAPPINGS[framework]);
  const requiredActions = buildRequiredActions(input, evidenceHashes);
  const riskScore = scoreRisk(input, evidenceHashes, requiredActions);

  return {
    schema: 'grc_claw.physical_ai_assurance.v1',
    generatedAt: new Date().toISOString(),
    assuranceType: 'physical_ai_humanoid_vla',
    systemId: input.systemId,
    title: input.title,
    source: input.source,
    scope: input.scope,
    model: {
      provider: input.model?.provider ?? 'nvidia',
      modelFamily: input.model?.modelFamily ?? sourceToModelFamily(input.source),
      modelId: input.model?.modelId ?? 'isaac-gr00t-or-humanoid-vla-compatible-model',
      endpointMode: input.model?.endpointMode ?? 'local',
    },
    embodiment: {
      robotClass: input.embodiment?.robotClass ?? 'humanoid',
      autonomyMode: input.embodiment?.autonomyMode ?? 'supervised_autonomy',
      operatingDomain: input.embodiment?.operatingDomain ?? 'lab',
    },
    runtime: input.runtime ?? {},
    evidenceHashes,
    controlMappings,
    riskScore,
    deploymentReadiness: readinessFromRisk(riskScore, requiredActions),
    requiredActions,
    safetyBoundary: [...SAFETY_BOUNDARY, ...(input.limitations ?? [])],
    a2zSocPayload: {
      artifactType: 'physical_ai_assurance_envelope',
      recommendedRoute: '/physical-ai-humanoid-assurance',
      tags: [
        'physical-ai',
        'humanoid-vla',
        input.source,
        input.model?.modelFamily ?? sourceToModelFamily(input.source),
        'assurance-envelope',
      ],
    },
  };
}

export function createSamplePhysicalAiAssuranceEnvelope(): PhysicalAiAssuranceEnvelope {
  return assessPhysicalAiSystem({
    systemId: 'sample-physical-ai-groot-001',
    title: 'Isaac-GR00T-style humanoid VLA assurance review',
    source: 'nvidia_isaac_groot',
    scope: 'Sample humanoid VLA manifest converted into cyber-physical governance and procurement evidence.',
    simulationSummary: 'Simulation-to-deployment evidence package with action-boundary, safety, runtime, and model-lifecycle facts.',
    model: {
      provider: 'nvidia',
      modelFamily: 'isaac_gr00t',
      modelId: 'isaac-gr00t-n1-or-compatible-vla',
      endpointMode: 'local',
      datasetBoundary: 'documented training and evaluation boundary',
      toolAllowlist: ['physical_ai.assess_system', 'physical_ai.generate_assurance_envelope', 'evidence.export'],
    },
    embodiment: {
      robotClass: 'humanoid',
      sensors: ['vision', 'proprioception', 'force-torque'],
      actuatorClasses: ['locomotion', 'manipulation'],
      autonomyMode: 'supervised_autonomy',
      operatingDomain: 'defense_supplier_lab',
      prohibitedActionClasses: ['weapon_control', 'target_selection', 'payload_guidance', 'live_tactical_command'],
    },
    runtime: {
      gpuProfile: 'NVIDIA accelerated robotics workstation or edge GPU',
      runtimeContainer: 'Isaac-compatible simulation / inference runtime',
      deploymentZone: 'lab / simulation / controlled pre-production range',
      networkBoundary: 'segmented robotics safety network',
      loggingMode: 'append-only model, operator, and safety event log',
      emergencyStop: { present: true, mechanism: 'hardware and software hold-to-run / e-stop gate' },
    },
    evidenceHashes: ['sha256:sample-groot-model-card', 'sha256:sample-isaac-sim-run', 'sha256:sample-safety-case'],
    humanApproval: { required: true, approverRole: 'Physical AI safety owner' },
    limitations: ['Sample envelope is for governance and evidence demonstration only.'],
  });
}

function buildRequiredActions(input: PhysicalAiSystemInput, evidenceHashes: string[]): string[] {
  const actions: string[] = [];
  if (!evidenceHashes.length) actions.push('Attach at least one signed model-card, simulation, runtime, safety-case, or deployment evidence hash.');
  if (!input.humanApproval?.required) actions.push('Define human approval before deployment, procurement sharing, or external evidence review.');
  if (!input.model?.toolAllowlist?.length) actions.push('Record the physical AI tool allowlist and prohibited robot/actuator actions.');
  if (!input.embodiment?.prohibitedActionClasses?.length) actions.push('Document prohibited action classes such as target selection, weapon control, payload guidance, and tactical command.');
  if (!input.runtime?.networkBoundary) actions.push('Document robotics runtime network boundary, identity boundary, and deployment zone.');
  if (!input.runtime?.emergencyStop?.present) actions.push('Attach emergency-stop / hold-to-run mechanism evidence and latest test status.');
  if (!input.limitations?.length) actions.push('Document known model, simulation, embodiment, and deployment limitations.');
  return actions;
}

function scoreRisk(input: PhysicalAiSystemInput, evidenceHashes: string[], requiredActions: string[]): number {
  let score = 24;
  score += requiredActions.length * 11;
  if (!evidenceHashes.length) score += 14;
  if (input.source === 'operator_upload') score += 10;
  if (input.embodiment?.operatingDomain === 'critical_infrastructure' || input.embodiment?.operatingDomain === 'defense_supplier_lab') score += 8;
  if (input.embodiment?.autonomyMode === 'bounded_autonomy') score += 10;
  if (input.humanApproval?.required && input.humanApproval.approverRole) score -= 8;
  if (input.model?.toolAllowlist?.length) score -= 6;
  if (input.embodiment?.prohibitedActionClasses?.length) score -= 6;
  if (input.runtime?.emergencyStop?.present) score -= 8;
  if (input.runtime?.networkBoundary) score -= 4;
  return Math.max(0, Math.min(100, score));
}

function readinessFromRisk(riskScore: number, requiredActions: string[]): PhysicalAiReadiness {
  if (riskScore >= 70 || requiredActions.length >= 5) return 'blocked';
  if (riskScore >= 30 || requiredActions.length > 0) return 'conditional';
  return 'ready';
}

function sourceToModelFamily(source: HumanoidVlaSource): Required<Pick<PhysicalAiModelMetadata, 'modelFamily'>>['modelFamily'] {
  if (source === 'nvidia_isaac_groot') return 'isaac_gr00t';
  if (source === 'isaac_lab' || source === 'isaac_sim') return 'humanoid_vla';
  return 'foundation_vla';
}
