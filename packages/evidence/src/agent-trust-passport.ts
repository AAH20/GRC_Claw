import { createHash } from 'node:crypto';
import type { AssuranceEnvelope } from './assurance-envelope.js';
import { hashAssuranceEnvelope, verifyAssuranceEnvelope } from './assurance-envelope.js';

export type AgentTrustPassportClaimStatus = 'evidenced' | 'limited_evidence' | 'not_observed';

export interface AgentTrustPassportSystem {
  organization: string;
  systemName: string;
  environment: 'local' | 'development' | 'staging' | 'production' | 'regulated' | 'defense_supplier';
  owner: string;
  dataBoundary: 'public' | 'tenant_confidential' | 'cui' | 'phi' | 'pci' | 'gdpr' | 'sovereign' | 'airgapped';
}

export interface AgentTrustPassportAgent {
  id: string;
  name: string;
  provider: string;
  model?: string;
  adapter: 'cursor' | 'codex' | 'claude_code' | 'github_actions' | 'terraform' | 'kubernetes' | 'stakpak_style_devops_agent' | 'custom';
  toolAllowlist: string[];
  approvalMode: 'none' | 'human' | 'dual_control' | 'change_board';
}

export interface AgentTrustPassportControlMapping {
  framework: 'ISO_42001' | 'NIST_AI_RMF' | 'SOC_2' | 'ISO_27001' | 'NIST_800_171' | 'CMMC' | 'CIS_K8S' | 'CUSTOM';
  controlId: string;
  status: AgentTrustPassportClaimStatus;
  evidenceRefs: string[];
  limitation?: string;
}

export interface AgentTrustPassportRisk {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  mitigation: string;
  owner?: string;
}

export interface AgentTrustPassport {
  version: 'agent-trust-passport/v1';
  passportId: string;
  generatedAt: string;
  system: AgentTrustPassportSystem;
  agents: AgentTrustPassportAgent[];
  summary: {
    totalAgents: number;
    totalEnvelopes: number;
    evidencedClaims: number;
    limitedClaims: number;
    notObservedClaims: number;
    deniedActions: number;
    approvalRequiredActions: number;
    verifiedEnvelopeCount: number;
  };
  evidence: Array<{
    actionId: string;
    tool: string;
    envelopeHash: string;
    policyState?: string;
    allowed?: boolean;
    requiresApproval?: boolean;
    evidenceId?: string;
    controlId?: string;
  }>;
  controlMappings: AgentTrustPassportControlMapping[];
  risks: AgentTrustPassportRisk[];
  buyerPacket: {
    positioning: string;
    buyerQuestionsAnswered: string[];
    limitations: string[];
    recommendedOffer: string;
  };
  verification: {
    ok: boolean;
    passportHash: string;
    checkedAt: string;
    errors: string[];
  };
}

export interface AgentTrustPassportInput {
  system: AgentTrustPassportSystem;
  agents: AgentTrustPassportAgent[];
  envelopes: AssuranceEnvelope[];
  controlMappings: AgentTrustPassportControlMapping[];
  risks?: AgentTrustPassportRisk[];
  generatedAt?: string;
}

function stableSerialize(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableSerialize(item)).join(',')}]`;
  }
  if (value && typeof value === 'object') {
    return `{${Object.entries(value as Record<string, unknown>)
      .filter(([, item]) => item !== undefined)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, item]) => `${JSON.stringify(key)}:${stableSerialize(item)}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}

export function hashAgentTrustPassport(passport: Omit<AgentTrustPassport, 'verification'>): string {
  return createHash('sha256').update(stableSerialize(passport)).digest('hex');
}

function passportIdFor(input: AgentTrustPassportInput, generatedAt: string): string {
  return `atp_${createHash('sha256')
    .update(`${input.system.organization}|${input.system.systemName}|${generatedAt}`)
    .digest('hex')
    .slice(0, 16)}`;
}

function countMappings(mappings: AgentTrustPassportControlMapping[], status: AgentTrustPassportClaimStatus): number {
  return mappings.filter((mapping) => mapping.status === status).length;
}

export function createAgentTrustPassport(input: AgentTrustPassportInput): AgentTrustPassport {
  const generatedAt = input.generatedAt ?? new Date().toISOString();
  const envelopeVerifications = input.envelopes.map(verifyAssuranceEnvelope);
  const errors = envelopeVerifications.flatMap((verification) =>
    verification.ok ? [] : verification.errors.map((error) => `${verification.actionId}:${error}`)
  );
  const evidence = input.envelopes.map((envelope) => ({
    actionId: envelope.actionId,
    tool: envelope.tool,
    envelopeHash: hashAssuranceEnvelope(envelope),
    policyState: envelope.policy?.executionState,
    allowed: envelope.policy?.allowed,
    requiresApproval: envelope.policy?.requiresApproval,
    evidenceId: envelope.result?.evidenceId,
    controlId: envelope.assurance?.controlId,
  }));
  const deniedActions = input.envelopes.filter((envelope) => envelope.policy?.allowed === false).length;
  const approvalRequiredActions = input.envelopes.filter((envelope) => envelope.policy?.requiresApproval === true).length;
  const limitations = [
    'This passport is a readiness and evidence packet, not a third-party certification.',
    'Claims marked limited_evidence or not_observed require owner review before external reliance.',
    'Raw prompts, secrets, tokens, command payloads, and private outputs are represented by hashes only.',
  ];

  const body: Omit<AgentTrustPassport, 'verification'> = {
    version: 'agent-trust-passport/v1',
    passportId: passportIdFor(input, generatedAt),
    generatedAt,
    system: input.system,
    agents: input.agents,
    summary: {
      totalAgents: input.agents.length,
      totalEnvelopes: input.envelopes.length,
      evidencedClaims: countMappings(input.controlMappings, 'evidenced'),
      limitedClaims: countMappings(input.controlMappings, 'limited_evidence'),
      notObservedClaims: countMappings(input.controlMappings, 'not_observed'),
      deniedActions,
      approvalRequiredActions,
      verifiedEnvelopeCount: envelopeVerifications.filter((verification) => verification.ok).length,
    },
    evidence,
    controlMappings: input.controlMappings,
    risks: input.risks ?? [],
    buyerPacket: {
      positioning:
        'Portable Agent Trust Passport for AI, DevSecOps, and infrastructure agents that need CISO, auditor, procurement, or defense-supplier review.',
      buyerQuestionsAnswered: [
        'Which agents and models touched the system?',
        'Which tools were allowed, denied, or approval-gated?',
        'Which evidence artifacts support the governance claims?',
        'Which controls are evidenced, limited, or not observed?',
        'What must be remediated before procurement or audit reliance?',
      ],
      limitations,
      recommendedOffer: 'A2Z SOC AI Agent Trust Passport: $2,500 setup plus $3,500/mo managed evidence desk.',
    },
  };
  const passportHash = hashAgentTrustPassport(body);

  return {
    ...body,
    verification: {
      ok: errors.length === 0,
      passportHash,
      checkedAt: new Date().toISOString(),
      errors,
    },
  };
}

