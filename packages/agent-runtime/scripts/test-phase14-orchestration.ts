import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase14Tests() {
  console.log('=== GRC_Claw Phase 14: Zero-Knowledge Swarm Execution & Cross-Topology Alignment Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase14-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: zk-Swarm-Traces Session Proofs
  // ----------------------------------------------------
  console.log('--- Test 1: zk-Swarm-Traces Session Proof Generation ---');
  const sessionProofInv: ToolInvocation = {
    tool: 'grc.generate_session_zk_proof',
    args: { sessionId: 'session-cmmc-compliance-01', traceHash: 'sha256-trace-0x88f21bc' },
    agentRole: 'developer'
  };

  const decision1 = policy.evaluate(sessionProofInv);
  console.log(`Tool: ${sessionProofInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(sessionProofInv.tool, sessionProofInv.args, deps);
  console.log('Proof Status:', dispatch1.status);
  console.log('Generated Proof Hash:', dispatch1.proofHash);

  if (dispatch1.ok && dispatch1.proofGenerated && dispatch1.proofHash === '0xzkproof88a7c29ebe31fa882ca3a992bc') {
    console.log('✅ Test 1 Passed: zk-Swarm-Traces session compliance proof successfully generated.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Cross-Topology Activation Steering
  // ----------------------------------------------------
  console.log('--- Test 2: Cross-Topology Activation Steering ---');
  const steeringInv: ToolInvocation = {
    tool: 'sovereign.inject_multimodel_steering_patch',
    args: { targetModels: ['llama3-70b', 'nemotron-4-340b', 'mistral-large'], conceptVectorId: 'anti-exfiltration-vector' },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(steeringInv);
  console.log(`Tool: ${steeringInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(steeringInv.tool, steeringInv.args, deps);
  console.log('Steering Status:', dispatch2.status);
  console.log('Models Steered:', dispatch2.targetModels);
  console.log('Adapter Optimization Loss:', dispatch2.adapterLoss);

  if (dispatch2.ok && dispatch2.steered && dispatch2.adapterLoss === 0.02) {
    console.log('✅ Test 2 Passed: Cross-topology activation steering patch successfully generated and distributed.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: zk-RAG Encrypted Database Retrieval Gating
  // ----------------------------------------------------
  console.log('--- Test 3: zk-RAG Encrypted Vector Database Retrieval Gating ---');
  const ragInv: ToolInvocation = {
    tool: 'memory.verify_zk_rag_proof',
    args: { documentId: 'doc-confidential-cmmc-evidence-03', membershipProofHash: '0xmembership-hash-0x99a2c' },
    agentRole: 'developer'
  };

  const decision3 = policy.evaluate(ragInv);
  console.log(`Tool: ${ragInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(ragInv.tool, ragInv.args, deps);
  console.log('Encrypted Retrieval Status:', dispatch3.status);
  console.log('Membership Proven:', dispatch3.membershipProven);

  if (dispatch3.ok && dispatch3.verified && dispatch3.membershipProven) {
    console.log('✅ Test 3 Passed: zk-RAG encrypted retrieval validated via membership proof.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Consensus Threat Intelligence Rollups
  // ----------------------------------------------------
  console.log('--- Test 4: Consensus Threat Rollup Propagation ---');
  const rollupInv: ToolInvocation = {
    tool: 'consensus.propagate_threat_rollup',
    args: { batchId: 'batch-threats-westus-01', threatsCount: 42 },
    agentRole: 'developer'
  };

  const decision4 = policy.evaluate(rollupInv);
  console.log(`Tool: ${rollupInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(rollupInv.tool, rollupInv.args, deps);
  console.log('Rollup Propagation Status:', dispatch4.status);
  console.log('Aggregated Threats Count:', dispatch4.threatsCount);
  console.log('Rollup Root Hash:', dispatch4.rollupRootHash);

  if (dispatch4.ok && dispatch4.rollupPropagated && dispatch4.threatsCount === 42) {
    console.log('✅ Test 4 Passed: Consensus threat intelligence rollup propagated successfully.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 14 ZERO-KNOWLEDGE SWARM EXECUTION & CROSS-TOPOLOGY ALIGNMENT TESTS COMPLETED GREEN ===');
}

runPhase14Tests().catch(err => {
  console.error('Phase 14 test run failed:');
  console.error(err);
  process.exit(1);
});
