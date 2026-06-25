import { createHash } from 'node:crypto';

export type ProviderType = 'openai_compatible' | 'anthropic_messages' | 'gemini_generate' | 'ollama' | 'local';

export interface ModelIdentity {
  id: string;
  name: string;
  provider: string;
  providerType: ProviderType;
  version: string;
  architecture: string;
  parameterCount: string;
  trainingDataCutoff: string;
  license: string;
  safetyRating: SafetyRating;
  supplyChain: SupplyChainInfo;
}

export interface SafetyRating {
  overall: number;
  toxicity: number;
  bias: number;
  hallucination: number;
  reasoning: number;
  evaluatedAt: string;
  evaluator: string;
}

export interface SupplyChainInfo {
  trainingDataHash: string;
  weightsHash: string;
  framework: string;
  dependencies: Dependency[];
  buildReproducible: boolean;
  signedBy: string[];
  sbom: SBOMEntry[];
}

export interface Dependency {
  name: string;
  version: string;
  hash: string;
  type: 'direct' | 'transitive';
  source: string;
  license: string;
  knownVulnerabilities: string[];
}

export interface SBOMEntry {
  type: 'model' | 'framework' | 'tool' | 'data';
  name: string;
  version: string;
  hash: string;
  source: string;
  verified: boolean;
}

export interface ModelProvenanceAttestation {
  modelId: string;
  providerId: string;
  attestationType: 'tee' | 'zk' | 'mpc' | 'combined';
  attestationData: AttestationData;
  verifiedAt: string;
  validUntil: string;
  chain: ProvenanceChain[];
  zkProof?: string;
  teeQuote?: TEEQuote;
}

export interface AttestationData {
  weightsIntegrity: boolean;
  trainingDataVerified: boolean;
  computeEnvironment: string;
  executionMode: 'cloud' | 'local' | 'hybrid' | 'enclave';
  auditTrail: AuditEntry[];
}

export interface AuditEntry {
  timestamp: string;
  action: string;
  actor: string;
  hash: string;
  metadata: Record<string, unknown>;
}

export interface ProvenanceChain {
  step: number;
  action: string;
  actor: string;
  timestamp: string;
  hash: string;
  signature: string;
}

export interface TEEQuote {
  teeType: 'intel_sgx' | 'amd_sev' | 'nvidia_cca' | 'arm TrustZone';
  quoteVersion: string;
  enclaveHash: string;
  publicKey: string;
  signature: string;
  _tcbLevel: string;
  pceSvn: string;
  mrEnclave: string;
  mrSigner: string;
  isvProdId: number;
  isvSvn: number;
}

export interface ModelRegistryEntry {
  modelId: string;
  identity: ModelIdentity;
  provenance: ModelProvenanceAttestation;
  registeredAt: string;
  status: 'active' | 'deprecated' | 'revoked' | 'suspended';
  complianceStatus: ComplianceStatus;
  riskScore: number;
  usageStats: UsageStats;
}

export interface ComplianceStatus {
  frameworks: string[];
  lastAudit: string;
  issues: ComplianceIssue[];
  overall: 'compliant' | 'non_compliant' | 'partial';
}

export interface ComplianceIssue {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  detectedAt: string;
  remediation: string;
}

export interface UsageStats {
  totalInvocations: number;
  lastUsed: string;
  avgLatency: number;
  errorRate: number;
  costPerToken: number;
}

export interface PolicyGate {
  id: string;
  name: string;
  description: string;
  type: 'pre_execution' | 'post_execution' | 'continuous';
  conditions: GateCondition[];
  action: 'allow' | 'deny' | 'warn' | 'require_approval';
  severity: 'critical' | 'high' | 'medium' | 'low';
}

export interface GateCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'matches';
  value: unknown;
  description: string;
}

export interface EnforcementReceipt {
  gateId: string;
  modelId: string;
  decision: 'allowed' | 'denied' | 'warned' | 'pending_approval';
  timestamp: string;
  reason: string;
  conditions: GateCondition[];
  attestationHash: string;
}

export interface FederatedConsensus {
  proposalId: string;
  proposal: ModelPolicyProposal;
  votes: ConsensusVote[];
  quorum: number;
  threshold: number;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  finalizedAt?: string;
}

export interface ModelPolicyProposal {
  id: string;
  title: string;
  description: string;
  modelId: string;
  action: 'approve' | 'restrict' | 'deprecate' | 'remove';
  policy: Record<string, unknown>;
  proposedBy: string;
  proposedAt: string;
}

export interface ConsensusVote {
  orgId: string;
  voter: string;
  decision: 'approve' | 'reject' | 'abstain';
  signature: string;
  timestamp: string;
  weight: number;
}
