import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase17Tests() {
  console.log('=== GRC_Claw Phase 17: Sovereign Quantum-Safe Attestation & Hardware-Locked Cognitive Shielding Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase17-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: Post-Quantum Lattice-Based DID Attestation
  // ----------------------------------------------------
  console.log('--- Test 1: Post-Quantum Lattice Credentials ---');
  const latticeSignInv: ToolInvocation = {
    tool: 'identity.sign_lattice_credential',
    args: { agentDid: 'did:grc:agent-navy-hq' },
    agentRole: 'developer'
  };

  const decision1 = policy.evaluate(latticeSignInv);
  console.log(`Tool: ${latticeSignInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(latticeSignInv.tool, latticeSignInv.args, deps);
  console.log('Attestation Signature:', dispatch1.signature);
  console.log('Algorithm Used:', dispatch1.algorithm);
  console.log('Status:', dispatch1.status);

  if (dispatch1.ok && dispatch1.signed && dispatch1.algorithm === 'ML-DSA-65') {
    console.log('✅ Test 1 Passed: Quantum-safe lattice-based credential attestation successful.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Hardware-Enclaved Model Weight Sanitation
  // ----------------------------------------------------
  console.log('--- Test 2: Hardware-Enclaved Model Weight Sanitation ---');
  const sanitizeInv: ToolInvocation = {
    tool: 'sovereign.sanitize_enclave_weights',
    args: { modelIdentifier: 'meta-llama-3.1-405b-enclave' },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(sanitizeInv);
  console.log(`Tool: ${sanitizeInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(sanitizeInv.tool, sanitizeInv.args, deps);
  console.log('Scan Status:', dispatch2.status);
  console.log('Scanned Weight Layers:', dispatch2.scannedWeightsLayersCount);
  console.log('Backdoors Found:', dispatch2.backdoorsDetectedCount);

  if (dispatch2.ok && dispatch2.sanitized && dispatch2.scannedWeightsLayersCount === 32) {
    console.log('✅ Test 2 Passed: TEE weight layers sanitized without security leaks.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Homomorphic Joint-Policy Threat Analysis
  // ----------------------------------------------------
  console.log('--- Test 3: Homomorphic Joint-Policy Threat Analysis ---');
  const jointThreatInv: ToolInvocation = {
    tool: 'security.evaluate_joint_fhe_threat',
    args: { jointIndicatorHashes: ['sha256-hash-01', 'sha256-hash-02', 'sha256-hash-03'] },
    agentRole: 'developer'
  };

  const decision3 = policy.evaluate(jointThreatInv);
  console.log(`Tool: ${jointThreatInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(jointThreatInv.tool, jointThreatInv.args, deps);
  console.log('FHE Thread Evaluation Status:', dispatch3.status);
  console.log('Matching Threat Correlated Count:', dispatch3.matchingThreatsCount);

  if (dispatch3.ok && dispatch3.evaluated && dispatch3.matchingThreatsCount === 0) {
    console.log('✅ Test 3 Passed: Multi-tenant FHE threat correlation evaluation completed.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Self-Healing Cognitive Attention Steering
  // ----------------------------------------------------
  console.log('--- Test 4: Self-Healing Cognitive Attention Steering ---');
  const steerInv: ToolInvocation = {
    tool: 'sovereign.steer_cognitive_attention_feedback',
    args: { stepsCount: 5, steeringScale: 2.0 },
    agentRole: 'developer'
  };

  const decision4 = policy.evaluate(steerInv);
  console.log(`Tool: ${steerInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(steerInv.tool, steerInv.args, deps);
  console.log('Steering Adjustment Status:', dispatch4.status);
  console.log('Feedback Steps Evaluated:', dispatch4.stepsCount);
  console.log('Modifications Active Count:', dispatch4.attentionModificationsAppliedCount);

  if (dispatch4.ok && dispatch4.steered && dispatch4.stepsCount === 5) {
    console.log('✅ Test 4 Passed: Step-by-step cognitive attention steering feedback applied successfully.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 17 SOVEREIGN QUANTUM-SAFE ATTESTATION & COGNITIVE SHIELDING TESTS GREEN ===');
}

runPhase17Tests().catch(err => {
  console.error('Phase 17 test run failed:');
  console.error(err);
  process.exit(1);
});
