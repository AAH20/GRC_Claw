import { createHash } from 'node:crypto';
import type {
  ModelIdentity,
  ModelRegistryEntry,
  PolicyGate,
  EnforcementReceipt,
  FederatedConsensus,
  ModelPolicyProposal,
  ConsensusVote,
  ComplianceStatus,
  ComplianceIssue,
  UsageStats,
} from '../types.js';
import { ModelProvenanceVerifier } from '../provenance/ModelProvenanceVerifier.js';

export class ModelRegistry {
  private entries: Map<string, ModelRegistryEntry> = new Map();
  private gates: Map<string, PolicyGate> = new Map();
  private consensusProposals: Map<string, FederatedConsensus> = new Map();
  private verifier: ModelProvenanceVerifier;

  constructor() {
    this.verifier = new ModelProvenanceVerifier();
    this.registerBuiltinGates();
  }

  async registerModel(model: ModelIdentity): Promise<ModelRegistryEntry> {
    const provenance = await this.verifier.generateAttestation(model.id, model.provider, 'intel_sgx');

    const entry: ModelRegistryEntry = {
      modelId: model.id,
      identity: model,
      provenance,
      registeredAt: new Date().toISOString(),
      status: 'active',
      complianceStatus: {
        frameworks: [],
        lastAudit: new Date().toISOString(),
        issues: [],
        overall: 'compliant',
      },
      riskScore: this.calculateInitialRisk(model),
      usageStats: {
        totalInvocations: 0,
        lastUsed: '',
        avgLatency: 0,
        errorRate: 0,
        costPerToken: 0,
      },
    };

    this.entries.set(model.id, entry);
    this.verifier.registerModel(model);
    return entry;
  }

  async deregisterModel(modelId: string, reason: string): Promise<boolean> {
    const entry = this.entries.get(modelId);
    if (!entry) return false;
    entry.status = 'revoked';
    entry.complianceStatus.issues.push({
      id: `deregister-${Date.now()}`,
      severity: 'critical',
      description: `Model deregistered: ${reason}`,
      detectedAt: new Date().toISOString(),
      remediation: 'No action required',
    });
    return true;
  }

  getModel(modelId: string): ModelRegistryEntry | undefined {
    return this.entries.get(modelId);
  }

  listModels(status?: ModelRegistryEntry['status']): ModelRegistryEntry[] {
    const models = Array.from(this.entries.values());
    return status ? models.filter((m) => m.status === status) : models;
  }

  searchModels(query: string): ModelRegistryEntry[] {
    const q = query.toLowerCase();
    return Array.from(this.entries.values()).filter(
      (e) =>
        e.modelId.toLowerCase().includes(q) ||
        e.identity.name.toLowerCase().includes(q) ||
        e.identity.provider.toLowerCase().includes(q)
    );
  }

  addPolicyGate(gate: PolicyGate): void {
    this.gates.set(gate.id, gate);
  }

  removePolicyGate(gateId: string): boolean {
    return this.gates.delete(gateId);
  }

  listPolicyGates(): PolicyGate[] {
    return Array.from(this.gates.values());
  }

  async enforceGates(
    modelId: string,
    context: { tool: string; args: Record<string, unknown>; role: string }
  ): Promise<EnforcementReceipt[]> {
    const receipts: EnforcementReceipt[] = [];
    const entry = this.entries.get(modelId);

    if (entry?.status === 'revoked') {
      receipts.push({
        gateId: 'revocation-check',
        modelId,
        decision: 'denied',
        timestamp: new Date().toISOString(),
        reason: `Model ${modelId} has been revoked`,
        conditions: [],
        attestationHash: createHash('sha256').update(modelId + 'revoked').digest('hex'),
      });
      return receipts;
    }

    for (const gate of this.gates.values()) {
      if (gate.type !== 'pre_execution') continue;

      const allPass = gate.conditions.every((condition) => {
        return this.evaluateCondition(condition, { modelId, ...context, entry });
      });

      receipts.push({
        gateId: gate.id,
        modelId,
        decision: allPass ? 'allowed' : gate.action === 'deny' ? 'denied' : 'warned',
        timestamp: new Date().toISOString(),
        reason: allPass ? `Gate ${gate.name} passed` : `Gate ${gate.name} failed`,
        conditions: gate.conditions,
        attestationHash: createHash('sha256').update(modelId + gate.id).digest('hex'),
      });
    }

    return receipts;
  }

  async submitProposal(proposal: ModelPolicyProposal): Promise<FederatedConsensus> {
    const consensus: FederatedConsensus = {
      proposalId: createHash('sha256').update(proposal.id + Date.now()).digest('hex'),
      proposal,
      votes: [],
      quorum: 3,
      threshold: 0.66,
      status: 'pending',
    };

    this.consensusProposals.set(consensus.proposalId, consensus);
    return consensus;
  }

  async vote(proposalId: string, vote: ConsensusVote): Promise<FederatedConsensus | undefined> {
    const consensus = this.consensusProposals.get(proposalId);
    if (!consensus || consensus.status !== 'pending') return undefined;

    consensus.votes.push(vote);

    const approveVotes = consensus.votes.filter((v) => v.decision === 'approve');
    const rejectVotes = consensus.votes.filter((v) => v.decision === 'reject');
    const totalWeight = consensus.votes.reduce((sum, v) => sum + v.weight, 0);

    if (totalWeight >= consensus.quorum) {
      const approveWeight = approveVotes.reduce((sum, v) => sum + v.weight, 0);
      consensus.status = approveWeight / totalWeight >= consensus.threshold ? 'approved' : 'rejected';
      consensus.finalizedAt = new Date().toISOString();
    }

    return consensus;
  }

  getConsensus(proposalId: string): FederatedConsensus | undefined {
    return this.consensusProposals.get(proposalId);
  }

  getStats(): { totalModels: number; active: number; revoked: number; gates: number; proposals: number } {
    const models = Array.from(this.entries.values());
    return {
      totalModels: models.length,
      active: models.filter((m) => m.status === 'active').length,
      revoked: models.filter((m) => m.status === 'revoked').length,
      gates: this.gates.size,
      proposals: this.consensusProposals.size,
    };
  }

  private registerBuiltinGates(): void {
    this.gates.set('sovereign-boundary', {
      id: 'sovereign-boundary',
      name: 'Sovereign Boundary Gate',
      description: 'Block non-sovereign LLMs from sensitive GRC tools',
      type: 'pre_execution',
      conditions: [
        { field: 'entry.identity.provider', operator: 'not_equals', value: 'zhipu-glm', description: 'Block Zhipu GLM' },
        { field: 'entry.identity.provider', operator: 'not_equals', value: 'moonshot-kimi', description: 'Block Moonshot Kimi' },
      ],
      action: 'deny',
      severity: 'critical',
    });

    this.gates.set('safety-rating', {
      id: 'safety-rating',
      name: 'Safety Rating Gate',
      description: 'Require minimum safety rating for production use',
      type: 'pre_execution',
      conditions: [
        { field: 'entry.identity.safetyRating.overall', operator: 'greater_than', value: 0.7, description: 'Minimum safety rating 0.7' },
      ],
      action: 'warn',
      severity: 'high',
    });

    this.gates.set('supply-chain', {
      id: 'supply-chain',
      name: 'Supply Chain Gate',
      description: 'Verify supply chain integrity before execution',
      type: 'pre_execution',
      conditions: [
        { field: 'entry.identity.supplyChain.buildReproducible', operator: 'equals', value: true, description: 'Build must be reproducible' },
        { field: 'entry.identity.supplyChain.dependencies', operator: 'contains', value: 'knownVulnerabilities', description: 'No known vulnerabilities' },
      ],
      action: 'deny',
      severity: 'critical',
    });
  }

  private evaluateCondition(condition: import('../types.js').GateCondition, context: Record<string, unknown>): boolean {
    const value = this.getNestedValue(context, condition.field);
    switch (condition.operator) {
      case 'equals': return value === condition.value;
      case 'not_equals': return value !== condition.value;
      case 'greater_than': return typeof value === 'number' && value > (condition.value as number);
      case 'less_than': return typeof value === 'number' && value < (condition.value as number);
      case 'contains': return String(value).includes(String(condition.value));
      case 'matches': return new RegExp(String(condition.value)).test(String(value));
      default: return false;
    }
  }

  private getNestedValue(obj: Record<string, unknown>, path: string): unknown {
    return path.split('.').reduce((current: unknown, key: string) => {
      if (current && typeof current === 'object' && key in current) {
        return (current as Record<string, unknown>)[key];
      }
      return undefined;
    }, obj);
  }

  private calculateInitialRisk(model: ModelIdentity): number {
    let risk = 0;
    if (!model.supplyChain.buildReproducible) risk += 0.3;
    if (model.supplyChain.dependencies.some((d) => d.knownVulnerabilities.length > 0)) risk += 0.2;
    if (model.safetyRating.overall < 0.7) risk += 0.3;
    if (model.safetyRating.toxicity > 0.3) risk += 0.1;
    if (model.safetyRating.bias > 0.3) risk += 0.1;
    return Math.min(risk, 1);
  }
}
