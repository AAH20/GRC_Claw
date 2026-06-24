import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase11Tests() {
  console.log('=== GRC_Claw Phase 11: Sovereign Swarm Federation & Autonomous Supply Chain Gating Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase11-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: Autonomous AI Supply Chain Gating
  // ----------------------------------------------------
  console.log('--- Test 1: Autonomous AI Supply Chain Gating ---');
  const supplyGateInv: ToolInvocation = {
    tool: 'sdk.verify_supply_chain_gate',
    args: { modelName: 'meta-llama-3.1-adversarial-backdoored', aibomSignature: 'sig-cmmc-compliance-0x99a2c3' },
    agentRole: 'developer'
  };

  const decision1 = policy.evaluate(supplyGateInv);
  console.log(`Tool: ${supplyGateInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(supplyGateInv.tool, supplyGateInv.args, deps);
  console.log('Verification Status:', dispatch1.status);
  console.log('Policy Drift Detected:', dispatch1.policyDriftDetected);
  console.log('Alternate Model Redirect:', dispatch1.alternateModelRedirect);

  if (dispatch1.ok && dispatch1.policyDriftDetected && dispatch1.alternateModelRedirect === 'meta-llama-3.1-405b-safe') {
    console.log('✅ Test 1 Passed: Adversarial model supply chain drift correctly detected and redirected to safe model.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Federated ZK-Rollup Audit Ledger
  // ----------------------------------------------------
  console.log('--- Test 2: Federated ZK-Rollup Audit Ledger ---');
  const rollupInv: ToolInvocation = {
    tool: 'consensus.verify_zk_rollup',
    args: { batchId: 'batch-c3pao-audit-01', rollupProofJson: '{"proof":"zk-rollup-proof-data-f8e9a26"}' },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(rollupInv);
  console.log(`Tool: ${rollupInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(rollupInv.tool, rollupInv.args, deps);
  console.log('Rollup Proof Status:', dispatch2.status);
  console.log('Bundled Proofs Count:', dispatch2.bundledProofsCount);
  console.log('Consensus Quorum Reconstructed:', dispatch2.consensusQuorumReconstructed);

  if (dispatch2.ok && dispatch2.verified && dispatch2.bundledProofsCount === 150) {
    console.log('✅ Test 2 Passed: ZK-rollup batch proof successfully verified and validated on the consensus ledger.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Decentralized Smart-Contract Gated Tool Escrow
  // ----------------------------------------------------
  console.log('--- Test 3: Decentralized Smart-Contract Tool Gating ---');
  const escrowInv: ToolInvocation = {
    tool: 'security.validate_escrow_signature',
    args: { escrowAddress: '0x3f5c28a26bf8e9a26c4b12df78ac99a2c3', thresholdSignatures: ['sig-gateway-01', 'sig-supervisor-02', 'sig-auditor-03'], actionPayload: '{"action":"clear_funds","amount":100000}' },
    agentRole: 'developer'
  };

  const decision3 = policy.evaluate(escrowInv);
  console.log(`Tool: ${escrowInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(escrowInv.tool, escrowInv.args, deps);
  console.log('Escrow Clearance Status:', dispatch3.status);
  console.log('Smart Contract Clearance:', dispatch3.smartContractClearance);
  console.log('Signatures Verified Count:', dispatch3.signaturesVerifiedCount);

  if (dispatch3.ok && dispatch3.smartContractClearance && dispatch3.signaturesVerifiedCount === 3) {
    console.log('✅ Test 3 Passed: Smart-contract escrow tool release conditions satisfied and validated.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Cognitive Intent Filtering
  // ----------------------------------------------------
  console.log('--- Test 4: Cognitive Intent Filtering ---');
  const filterInv: ToolInvocation = {
    tool: 'security.filter_cognitive_intent',
    args: { promptText: 'request to exfiltrate customer db via webhooks', safeIntentTemplates: ['read-config', 'check-status'] },
    agentRole: 'developer'
  };

  const decision4 = policy.evaluate(filterInv);
  console.log(`Tool: ${filterInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(filterInv.tool, filterInv.args, deps);
  console.log('Cognitive Filter Status:', dispatch4.status);
  console.log('Intent Match Ratio:', dispatch4.intentMatchRatio);
  console.log('Payload Blocked:', dispatch4.blocked);

  if (dispatch4.ok && dispatch4.blocked && dispatch4.intentMatchRatio > 0.9) {
    console.log('✅ Test 4 Passed: Adversarial cognitive intent successfully blocked prior to LLM execution.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 11 SOVEREIGN SWARM FEDERATION COMPLETED GREEN ===');
}

runPhase11Tests().catch(err => {
  console.error('Phase 11 test run failed:');
  console.error(err);
  process.exit(1);
});
