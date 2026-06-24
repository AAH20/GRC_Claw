import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase16Tests() {
  console.log('=== GRC_Claw Phase 16: Zero-Knowledge Policies & Speculative Barriers Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase16-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: zk-Policies invariant verification
  // ----------------------------------------------------
  console.log('--- Test 1: Zero-Knowledge Policy Invariant Proofs ---');
  const policyZkInv: ToolInvocation = {
    tool: 'grc.verify_zk_policy_envelope',
    args: { envelopeId: 'env-zkp-ITAR-03' },
    agentRole: 'developer'
  };

  const decision1 = policy.evaluate(policyZkInv);
  console.log(`Tool: ${policyZkInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(policyZkInv.tool, policyZkInv.args, deps);
  console.log('ZK Verification Status:', dispatch1.status);
  console.log('Circuit Constraints checked:', dispatch1.circuitConstraintsCount);

  if (dispatch1.ok && dispatch1.verified && dispatch1.circuitConstraintsCount === 2048) {
    console.log('✅ Test 1 Passed: zk-Policies invariant proof verified.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Hardware Speculative Execution barrier VM Intercepts
  // ----------------------------------------------------
  console.log('--- Test 2: Hardware Speculative Execution Barriers ---');
  const speculationInv: ToolInvocation = {
    tool: 'security.trigger_speculative_barrier',
    args: { activeProcessors: ['cpu-0', 'cpu-1', 'cpu-2', 'cpu-3'] },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(speculationInv);
  console.log(`Tool: ${speculationInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(speculationInv.tool, speculationInv.args, deps);
  console.log('Speculation Barrier Status:', dispatch2.status);
  console.log('Speculative Barrier Flags Set:', dispatch2.flagsSet);
  console.log('Target CPU Cores Active:', dispatch2.activeProcessors);

  if (dispatch2.ok && dispatch2.barrierConfigured && dispatch2.flagsSet.includes('LFENCE')) {
    console.log('✅ Test 2 Passed: CPU hardware speculation barriers set inside VM intercepts.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Multi-Party Collaborative Homomorphic vector search
  // ----------------------------------------------------
  console.log('--- Test 3: Collaborative Multi-Party Homomorphic Vector Search ---');
  const multipartyQueryInv: ToolInvocation = {
    tool: 'memory.query_multiparty_fhe_vector',
    args: { tenantIds: ['tenant-eu-defense-01', 'tenant-us-navy-02'] },
    agentRole: 'developer'
  };

  const decision3 = policy.evaluate(multipartyQueryInv);
  console.log(`Tool: ${multipartyQueryInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(multipartyQueryInv.tool, multipartyQueryInv.args, deps);
  console.log('Collaborative FHE RAG Status:', dispatch3.status);
  console.log('Matching Private Vector Matches:', dispatch3.matchingEmbeddingsCount);

  if (dispatch3.ok && dispatch3.sharedKeyEstablished && dispatch3.matchingEmbeddingsCount === 12) {
    console.log('✅ Test 3 Passed: Collaborative homomorphic vector retrieval search completed.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Dynamic Synaptic LoRA Gradient patches
  // ----------------------------------------------------
  console.log('--- Test 4: Dynamic Synaptic Weight Gradient Patching (Inline LoRA) ---');
  const gradientPatchInv: ToolInvocation = {
    tool: 'sovereign.apply_dynamic_gradient_patch',
    args: { loraRank: 16, loraAlpha: 32 },
    agentRole: 'developer'
  };

  const decision4 = policy.evaluate(gradientPatchInv);
  console.log(`Tool: ${gradientPatchInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(gradientPatchInv.tool, gradientPatchInv.args, deps);
  console.log('Dynamic Weight Update Status:', dispatch4.status);
  console.log('LoRA Adaptation Rank:', dispatch4.loraRank);
  console.log('Updated Synaptic Adapter Parameters:', dispatch4.adapterWeightsUpdatedCount);

  if (dispatch4.ok && dispatch4.patched && dispatch4.loraRank === 16) {
    console.log('✅ Test 4 Passed: Low-latency synaptic gradient weight patches applied successfully.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 16 ZERO-KNOWLEDGE POLICIES & HARDWARE DEFENSES COMPLETED GREEN ===');
}

runPhase16Tests().catch(err => {
  console.error('Phase 16 test run failed:');
  console.error(err);
  process.exit(1);
});
