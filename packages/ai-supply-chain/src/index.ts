import { ModelProvenanceVerifier } from './provenance/ModelProvenanceVerifier.js';
import { ModelRegistry } from './governance/ModelRegistry.js';
import type {
  ModelIdentity,
  ModelRegistryEntry,
  PolicyGate,
  EnforcementReceipt,
  FederatedConsensus,
  ModelPolicyProposal,
  ConsensusVote,
} from './types.js';

export * from './types.js';
export { ModelProvenanceVerifier } from './provenance/ModelProvenanceVerifier.js';
export { ModelRegistry } from './governance/ModelRegistry.js';
export type { ProvenanceVerificationResult, ProvenanceIssue, VerificationDetail } from './provenance/ModelProvenanceVerifier.js';

export interface AISupplyChainConfig {
  orgId: string;
  enableTEE: boolean;
  enableZK: boolean;
  enableFederatedConsensus: boolean;
  minSafetyRating: number;
  requireReproducibleBuilds: boolean;
}

export class AISupplyChainSovereignty {
  private registry: ModelRegistry;
  private verifier: ModelProvenanceVerifier;
  private config: AISupplyChainConfig;

  constructor(config: AISupplyChainConfig) {
    this.config = config;
    this.registry = new ModelRegistry();
    this.verifier = new ModelProvenanceVerifier();
  }

  async registerModel(model: ModelIdentity): Promise<ModelRegistryEntry> {
    return this.registry.registerModel(model);
  }

  async deregisterModel(modelId: string, reason: string): Promise<boolean> {
    return this.registry.deregisterModel(modelId, reason);
  }

  async verifyModelProvenance(modelId: string) {
    return this.verifier.verifyProvenance(modelId);
  }

  async enforceRuntimePolicy(
    modelId: string,
    context: { tool: string; args: Record<string, unknown>; role: string }
  ): Promise<EnforcementReceipt[]> {
    return this.registry.enforceGates(modelId, context);
  }

  async submitPolicyProposal(proposal: ModelPolicyProposal): Promise<FederatedConsensus> {
    return this.registry.submitProposal(proposal);
  }

  async voteOnProposal(proposalId: string, vote: ConsensusVote): Promise<FederatedConsensus | undefined> {
    return this.registry.vote(proposalId, vote);
  }

  getModel(modelId: string): ModelRegistryEntry | undefined {
    return this.registry.getModel(modelId);
  }

  listModels(status?: ModelRegistryEntry['status']): ModelRegistryEntry[] {
    return this.registry.listModels(status);
  }

  getStats() {
    return this.registry.getStats();
  }
}
