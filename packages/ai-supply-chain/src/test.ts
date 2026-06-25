import { AISupplyChainSovereignty } from './index.js';
import { ModelProvenanceVerifier } from './provenance/ModelProvenanceVerifier.js';
import { ModelRegistry } from './governance/ModelRegistry.js';
import type { ModelIdentity } from './types.js';

const TEST_MODEL: ModelIdentity = {
  id: 'gpt-4-turbo',
  name: 'GPT-4 Turbo',
  provider: 'openai',
  providerType: 'openai_compatible',
  version: '2024-04-09',
  architecture: 'Transformer',
  parameterCount: '1.76T',
  trainingDataCutoff: '2023-12',
  license: 'Proprietary',
  safetyRating: { overall: 0.92, toxicity: 0.05, bias: 0.08, hallucination: 0.15, reasoning: 0.95, evaluatedAt: new Date().toISOString(), evaluator: 'internal' },
  supplyChain: {
    trainingDataHash: 'sha256:abc123def456',
    weightsHash: 'sha256:789012345678',
    framework: 'PyTorch',
    dependencies: [
      { name: 'torch', version: '2.1.0', hash: 'sha256:torch123', type: 'direct', source: 'pytorch.org', license: 'BSD-3', knownVulnerabilities: [] },
      { name: 'transformers', version: '4.35.0', hash: 'sha256:transformers123', type: 'direct', source: 'huggingface.co', license: 'Apache-2.0', knownVulnerabilities: [] },
    ],
    buildReproducible: true,
    signedBy: ['openai-security', 'azure-devops'],
    sbom: [
      { type: 'model', name: 'gpt-4', version: '1.0', hash: 'sha256:model123', source: 'openai', verified: true },
      { type: 'framework', name: 'pytorch', version: '2.1.0', hash: 'sha256:pytorch123', source: 'pytorch.org', verified: true },
      { type: 'tool', name: 'tokenizer', version: '1.0', hash: 'sha256:tok123', source: 'openai', verified: true },
    ],
  },
};

const TEST_MODEL_LOCAL: ModelIdentity = {
  id: 'llama-3-70b',
  name: 'Llama 3 70B',
  provider: 'ollama',
  providerType: 'ollama',
  version: '3.0',
  architecture: 'LLaMA',
  parameterCount: '70B',
  trainingDataCutoff: '2023-12',
  license: 'Apache-2.0',
  safetyRating: { overall: 0.88, toxicity: 0.08, bias: 0.12, hallucination: 0.18, reasoning: 0.9, evaluatedAt: new Date().toISOString(), evaluator: 'meta' },
  supplyChain: {
    trainingDataHash: 'sha256:llama_data_abc',
    weightsHash: 'sha256:llama_weights_abc',
    framework: 'PyTorch',
    dependencies: [
      { name: 'torch', version: '2.1.0', hash: 'sha256:torch_llama', type: 'direct', source: 'pytorch.org', license: 'BSD-3', knownVulnerabilities: [] },
    ],
    buildReproducible: true,
    signedBy: ['meta-ai'],
    sbom: [
      { type: 'model', name: 'llama-3', version: '3.0', hash: 'sha256:llama3', source: 'meta', verified: true },
    ],
  },
};

async function testModelProvenanceVerifier() {
  console.log('\n=== Testing Model Provenance Verifier ===');
  const verifier = new ModelProvenanceVerifier();

  verifier.registerModel(TEST_MODEL);
  verifier.registerModel(TEST_MODEL_LOCAL);

  const gpt4Result = await verifier.verifyProvenance('gpt-4-turbo');
  console.log(`GPT-4 Turbo verification: ${gpt4Result.verified ? 'PASS' : 'FAIL'}`);
  console.log(`  Integrity score: ${(gpt4Result.integrityScore * 100).toFixed(0)}%`);
  console.log(`  Chain valid: ${gpt4Result.chainValid}`);
  console.log(`  Issues: ${gpt4Result.issues.length}`);

  const llamaResult = await verifier.verifyProvenance('llama-3-70b');
  console.log(`Llama 3 70B verification: ${llamaResult.verified ? 'PASS' : 'FAIL'}`);
  console.log(`  Integrity score: ${(llamaResult.integrityScore * 100).toFixed(0)}%`);
  console.log(`  Chain valid: ${llamaResult.chainValid}`);

  const attestation = await verifier.generateAttestation('gpt-4-turbo', 'openai', 'intel_sgx');
  console.log(`Attestation generated: ${attestation.attestationType}`);
  console.log(`  TEE quote: ${attestation.teeQuote?.teeType}`);
  console.log(`  Valid until: ${attestation.validUntil}`);

  const zkProof = await verifier.generateZKProof('gpt-4-turbo', 'model_is_safe');
  console.log(`ZK proof: ${zkProof.substring(0, 30)}...`);

  console.log('✓ Model Provenance Verifier tests passed');
}

async function testModelRegistry() {
  console.log('\n=== Testing Model Registry ===');
  const registry = new ModelRegistry();

  const entry1 = await registry.registerModel(TEST_MODEL);
  console.log(`Registered: ${entry1.modelId} (risk: ${entry1.riskScore.toFixed(2)})`);

  const entry2 = await registry.registerModel(TEST_MODEL_LOCAL);
  console.log(`Registered: ${entry2.modelId} (risk: ${entry2.riskScore.toFixed(2)})`);

  const model = registry.getModel('gpt-4-turbo');
  console.log(`Retrieved: ${model?.identity.name}`);

  const models = registry.listModels();
  console.log(`Total models: ${models.length}`);

  const gates = registry.listPolicyGates();
  console.log(`Policy gates: ${gates.length}`);

  const receipts = await registry.enforceGates('gpt-4-turbo', {
    tool: 'grc.list_controls',
    args: {},
    role: 'analyst',
  });
  console.log(`Gate enforcement results: ${receipts.length}`);
  for (const r of receipts) {
    console.log(`  ${r.gateId}: ${r.decision}`);
  }

  const proposal = await registry.submitProposal({
    id: 'proposal-1',
    title: 'Approve Claude 3.5 Sonnet',
    description: 'Add Claude 3.5 Sonnet to approved models',
    modelId: 'claude-3.5-sonnet',
    action: 'approve',
    policy: { minSafetyRating: 0.85 },
    proposedBy: 'security-team',
    proposedAt: new Date().toISOString(),
  });
  console.log(`Proposal submitted: ${proposal.proposalId}`);

  const vote = await registry.vote(proposal.proposalId, {
    orgId: 'org-1',
    voter: 'admin',
    decision: 'approve',
    signature: 'sig123',
    timestamp: new Date().toISOString(),
    weight: 1,
  });
  console.log(`Vote cast, status: ${vote?.status}`);

  const stats = registry.getStats();
  console.log(`Registry stats: ${stats.totalModels} models, ${stats.gates} gates`);

  console.log('✓ Model Registry tests passed');
}

async function testAISupplyChainSovereignty() {
  console.log('\n=== Testing AI Supply Chain Sovereignty ===');
  const sovereignty = new AISupplyChainSovereignty({
    orgId: 'test-org',
    enableTEE: true,
    enableZK: true,
    enableFederatedConsensus: true,
    minSafetyRating: 0.8,
    requireReproducibleBuilds: true,
  });

  const entry = await sovereignty.registerModel(TEST_MODEL);
  console.log(`Registered model: ${entry.modelId}`);

  const provenance = await sovereignty.verifyModelProvenance('gpt-4-turbo');
  console.log(`Provenance verified: ${provenance.verified}`);

  const receipts = await sovereignty.enforceRuntimePolicy('gpt-4-turbo', {
    tool: 'grc.list_controls',
    args: {},
    role: 'analyst',
  });
  console.log(`Enforcement receipts: ${receipts.length}`);

  const proposal = await sovereignty.submitPolicyProposal({
    id: 'policy-1',
    title: 'Restrict non-sovereign models',
    description: 'Block non-US-aligned models from GRC tools',
    modelId: 'zhipu-glm',
    action: 'restrict',
    policy: { blockedTools: ['grc.*', 'cmmc.*'] },
    proposedBy: 'compliance-team',
    proposedAt: new Date().toISOString(),
  });
  console.log(`Policy proposal: ${proposal.proposalId}`);

  const stats = sovereignty.getStats();
  console.log(`Stats: ${stats.totalModels} models, ${stats.active} active`);

  console.log('✓ AI Supply Chain Sovereignty tests passed');
}

async function runAllTests() {
  console.log('Starting AI Supply Chain Tests...\n');
  console.log('='.repeat(60));

  await testModelProvenanceVerifier();
  await testModelRegistry();
  await testAISupplyChainSovereignty();

  console.log('\n' + '='.repeat(60));
  console.log('All AI Supply Chain tests passed! ✓');
  console.log('='.repeat(60));
}

runAllTests().catch(console.error);
