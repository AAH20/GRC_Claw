import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase15Tests() {
  console.log('=== GRC_Claw Phase 15: Absolute Monopoly & Hardware-Locked Sovereign Trust Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase15-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: Regulation Compilation to AST
  // ----------------------------------------------------
  console.log('--- Test 1: Self-Assembling Compliance Compiler ---');
  const compileInv: ToolInvocation = {
    tool: 'sdk.compile_regulation_ast',
    args: { regulationDocName: 'eu-ai-act-2026.pdf' },
    agentRole: 'developer'
  };

  const decision1 = policy.evaluate(compileInv);
  console.log(`Tool: ${compileInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(compileInv.tool, compileInv.args, deps);
  console.log('Compilation Status:', dispatch1.status);
  console.log('Rules Extracted Count:', dispatch1.ruleCount);
  console.log('AST Output Hash:', dispatch1.astHash);

  if (dispatch1.ok && dispatch1.compiled && dispatch1.ruleCount === 24) {
    console.log('✅ Test 1 Passed: Regulation compiled successfully to AST rules.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Hardware-Level Side-Channel Anomaly Detection
  // ----------------------------------------------------
  console.log('--- Test 2: Neuromorphic Side-Channel Swarm Shield ---');
  const sidechannelInv: ToolInvocation = {
    tool: 'security.detect_sidechannel_anomaly',
    args: {},
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(sidechannelInv);
  console.log(`Tool: ${sidechannelInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(sidechannelInv.tool, sidechannelInv.args, deps);
  console.log('Side-Channel Status:', dispatch2.status);
  console.log('Anomaly Detected:', dispatch2.anomalyDetected);
  console.log('Cache Miss Rate:', dispatch2.cacheMissRate);

  if (dispatch2.ok && !dispatch2.anomalyDetected && dispatch2.cacheMissRate === 0.12) {
    console.log('✅ Test 2 Passed: Side-channel performance counter anomalies checked cleanly.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Homomorphic Ledger Query
  // ----------------------------------------------------
  console.log('--- Test 3: Fully Homomorphic Consensus Ledger Query ---');
  const auditQueryInv: ToolInvocation = {
    tool: 'audit.query_fhe_ledger',
    args: { queryPayloadEncrypted: '0xencryptedpayload88a2c3' },
    agentRole: 'developer'
  };

  const decision3 = policy.evaluate(auditQueryInv);
  console.log(`Tool: ${auditQueryInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(auditQueryInv.tool, auditQueryInv.args, deps);
  console.log('FHE Ledger Status:', dispatch3.status);
  console.log('Matching Encrypted Records:', dispatch3.matchingEncryptedRecordsCount);

  if (dispatch3.ok && dispatch3.queried && dispatch3.matchingEncryptedRecordsCount === 150) {
    console.log('✅ Test 3 Passed: FHE query verified on encrypted ledger pages.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Inline Token Steering
  // ----------------------------------------------------
  console.log('--- Test 4: Real-Time Cognitive Synaptic steering (Inline Attention) ---');
  const steerInv: ToolInvocation = {
    tool: 'sovereign.steer_cognitive_drift_inline',
    args: { tokensEvaluatedCount: 200, steeringVectorMagnitude: 0.12 },
    agentRole: 'developer'
  };

  const decision4 = policy.evaluate(steerInv);
  console.log(`Tool: ${steerInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(steerInv.tool, steerInv.args, deps);
  console.log('Inline Steering Status:', dispatch4.status);
  console.log('Steering Vector Magnitude:', dispatch4.steeringVectorMagnitude);
  console.log('Attention Heads Patched:', dispatch4.attentionHeadsModifiedCount);

  if (dispatch4.ok && dispatch4.steered && dispatch4.steeringVectorMagnitude === 0.12) {
    console.log('✅ Test 4 Passed: Inline attention steering successfully applied to model forward pass.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 15 ABSOLUTE MONOPOLY & HARDWARE-LOCKED TRUST TESTS COMPLETED GREEN ===');
}

runPhase15Tests().catch(err => {
  console.error('Phase 15 test run failed:');
  console.error(err);
  process.exit(1);
});
