import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase12Tests() {
  console.log('=== GRC_Claw Phase 12: Sovereign Swarm Validation & Post-Quantum MPC Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase12-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: Decentralized Compliance Oracle PBFT Consensus
  // ----------------------------------------------------
  console.log('--- Test 1: Decentralized Compliance Oracle Consensus ---');
  const oracleInv: ToolInvocation = {
    tool: 'consensus.verify_decentralized_oracle',
    args: { feedUrl: 'https://feeds.cisa.gov/vuln-feed', oracleSignature: 'sig-cisa-vuln-0x89abef' },
    agentRole: 'developer'
  };

  const decision1 = policy.evaluate(oracleInv);
  console.log(`Tool: ${oracleInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(oracleInv.tool, oracleInv.args, deps);
  console.log('Consensus Quorum Reached:', dispatch1.consensusQuorumReached);
  console.log('Consensus Nodes Count:', dispatch1.consensusNodesCount);

  if (dispatch1.ok && dispatch1.verified && dispatch1.consensusQuorumReached && dispatch1.consensusNodesCount === 7) {
    console.log('✅ Test 1 Passed: Decentralized compliance feed PBFT consensus verified.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Post-Quantum Lattice Threshold Signing
  // ----------------------------------------------------
  console.log('--- Test 2: Post-Quantum Lattice MPC Threshold Co-signing ---');
  const mpcInv: ToolInvocation = {
    tool: 'sovereign.sign_lattice_mpc',
    args: { payloadHash: 'sha256-block-c3pao-0x99238f', thresholdSharesCount: 5 },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(mpcInv);
  console.log(`Tool: ${mpcInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(mpcInv.tool, mpcInv.args, deps);
  console.log('Signing Status:', dispatch2.status);
  console.log('Algorithm Used:', dispatch2.algorithm);
  console.log('Keyshare Enclaves Active:', dispatch2.keyshareEnclavesActive);

  if (dispatch2.ok && dispatch2.signed && dispatch2.algorithm === 'ML-DSA-87') {
    console.log('✅ Test 2 Passed: Lattice-based MPC threshold co-signing successful.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Symbolic Graph Flow Boundary Proofs
  // ----------------------------------------------------
  console.log('--- Test 3: Symbolic Graph Flow Boundary Verification ---');
  const flowInv: ToolInvocation = {
    tool: 'security.verify_symbolic_graph_flow',
    args: { graphRootNode: 'Users-ahmedhassan-Downloads-a2z-soc-main-2', targetComplianceBoundary: 'iso-42001-aims' },
    agentRole: 'developer'
  };

  const decision3 = policy.evaluate(flowInv);
  console.log(`Tool: ${flowInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(flowInv.tool, flowInv.args, deps);
  console.log('Graph Flow Status:', dispatch3.status);
  console.log('Flow Paths Analyzed:', dispatch3.flowPathsAnalyzedCount);
  console.log('Leaks Detected:', dispatch3.leaksDetectedCount);

  if (dispatch3.ok && dispatch3.verified && dispatch3.leaksDetectedCount === 0) {
    console.log('✅ Test 3 Passed: Symbolic graph flow verified secure (boundary holds).\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Cognitive WAF RLHF Adaptive Tuning
  // ----------------------------------------------------
  console.log('--- Test 4: Cognitive WAF RLHF Feedback Loop Tuning ---');
  const tuneInv: ToolInvocation = {
    tool: 'security.rlhf_tune_cognitive_intent',
    args: { bypassLogs: ['bypass-log-01', 'bypass-log-02'], correctedClassification: 'malicious' },
    agentRole: 'developer'
  };

  const decision4 = policy.evaluate(tuneInv);
  console.log(`Tool: ${tuneInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(tuneInv.tool, tuneInv.args, deps);
  console.log('Tuning Loop Status:', dispatch4.status);
  console.log('Boundary Shift Ratio:', dispatch4.intentBoundaryShift);
  console.log('New DPO Training Epoch:', dispatch4.newDpoEpoch);

  if (dispatch4.ok && dispatch4.tuned && dispatch4.intentBoundaryShift < 0) {
    console.log('✅ Test 4 Passed: RLHF intent boundary tuning completed.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 12 SOVEREIGN SWARM VALIDATION TESTS COMPLETED GREEN ===');
}

runPhase12Tests().catch(err => {
  console.error('Phase 12 test run failed:');
  console.error(err);
  process.exit(1);
});
