import {
  VectorGraphMemory,
  SkillsRegistry
} from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runTests() {
  console.log('=== RUNNING COMPREHENSIVE ADVANCED SECURITY CONTROL TESTS ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });

  // ==========================================
  // Test 1: Vector Graph Memory Query
  // ==========================================
  console.log('--- Test 1: Vector Graph Query for TEE, MPC, ZKP, and Containment ---');
  const vectorMemory = new VectorGraphMemory();
  
  const teeNodes = vectorMemory.query('TEE Hardware');
  console.log(`Matched TEE nodes count: ${teeNodes.nodes.length}`);
  teeNodes.nodes.forEach(n => console.log(`- Node [${n.id}] (${n.type}): ${n.label}`));

  const containmentNodes = vectorMemory.query('Active Containment');
  console.log(`Matched Containment nodes count: ${containmentNodes.nodes.length}`);
  containmentNodes.nodes.forEach(n => console.log(`- Node [${n.id}] (${n.type}): ${n.label}`));

  const zkpNodes = vectorMemory.query('Zero-Knowledge');
  console.log(`Matched ZKP nodes count: ${zkpNodes.nodes.length}`);
  zkpNodes.nodes.forEach(n => console.log(`- Node [${n.id}] (${n.type}): ${n.label}`));

  const mpcNodes = vectorMemory.query('Multi-Party');
  console.log(`Matched MPC nodes count: ${mpcNodes.nodes.length}`);
  mpcNodes.nodes.forEach(n => console.log(`- Node [${n.id}] (${n.type}): ${n.label}`));
  console.log('');

  // ==========================================
  // Test 2: Skills Registry Query
  // ==========================================
  console.log('--- Test 2: Skills Registry Query for Playbooks ---');
  const skillsRegistry = new SkillsRegistry();
  
  const teeSkill = skillsRegistry.load('tee-hardware-attestation');
  console.log(`TEE Skill loaded: ${!!teeSkill}`);
  if (teeSkill) console.log(`- Skill: ${teeSkill.name} (${teeSkill.category})`);

  const containmentSkill = skillsRegistry.load('active-containment-recovery');
  console.log(`Containment Skill loaded: ${!!containmentSkill}`);
  if (containmentSkill) console.log(`- Skill: ${containmentSkill.name} (${containmentSkill.category})`);

  const zkpSkill = skillsRegistry.load('zero-knowledge-audit');
  console.log(`ZKP Skill loaded: ${!!zkpSkill}`);
  if (zkpSkill) console.log(`- Skill: ${zkpSkill.name} (${zkpSkill.category})`);

  const mpcSkill = skillsRegistry.load('mpc-threshold-signing');
  console.log(`MPC Skill loaded: ${!!mpcSkill}`);
  if (mpcSkill) console.log(`- Skill: ${mpcSkill.name} (${mpcSkill.category})`);
  console.log('');

  // ==========================================
  // Test 3: TEE Hardware Attestation
  // ==========================================
  console.log('--- Test 3: Verifying Nvidia TEE Hardware Attestation ---');
  const teeResult = await dispatchBuiltinGrcTool('sovereign.verify_tee_attestation', {
    attestationReportHex: '00abcdef2233aa',
    cpuGpuVendor: 'nvidia'
  }, { evidence, a2z });

  console.log('Attestation Clearance:', teeResult.attestationClearance);
  console.log('Clearance Token Generated:', teeResult.clearanceToken);
  if (teeResult.attestationClearance !== 'VERIFIED' || !teeResult.clearanceToken) {
    throw new Error('Test 3 Failed: expected attestation to be VERIFIED');
  }
  console.log('');

  // ==========================================
  // Test 4: Active Container Containment
  // ==========================================
  console.log('--- Test 4: Triggering Active Sandbox Network Containment ---');
  const containmentResult = await dispatchBuiltinGrcTool('security.trigger_active_containment', {
    containerId: 'docker-sandbox-01',
    breachingSessionId: 'session-999'
  }, { evidence, a2z });

  console.log('Containment Status:', containmentResult.containmentStatus);
  console.log('Snapshot Saved to:', containmentResult.snapshotUri);
  console.log('Rollback Status:', containmentResult.rollbackStatus);
  if (containmentResult.containmentStatus !== 'SUCCESS' || containmentResult.rollbackStatus !== 'COMPLETED') {
    throw new Error('Test 4 Failed: expected active containment to isolate and complete rollback');
  }
  console.log('');

  // ==========================================
  // Test 5: Zero-Knowledge Compliance Proof
  // ==========================================
  console.log('--- Test 5: Generating ZK Compliance Proof for Auditor ---');
  const zkpResult = await dispatchBuiltinGrcTool('grc.generate_zkp_proof', {
    complianceInputsJson: '{"control": "iso-42001-a6", "compliance": true}',
    circuitParamsUri: 'file:///opt/circuits/compliance.circuit'
  }, { evidence, a2z });

  console.log('ZK Verification Status:', zkpResult.verificationStatus);
  console.log('Proof Output:', zkpResult.zkProofJson);
  if (zkpResult.verificationStatus !== 'VERIFIED' || !zkpResult.zkProofJson) {
    throw new Error('Test 5 Failed: expected compliance proof to be VERIFIED');
  }
  console.log('');

  // ==========================================
  // Test 6: MPC Threshold Secret Signing
  // ==========================================
  console.log('--- Test 6: Coordinating MPC Threshold Signature ---');
  const mpcResult = await dispatchBuiltinGrcTool('mpc.generate_threshold_signature', {
    transactionPayload: '{"amount": 500, "to": "xrp-wallet"}',
    thresholdNodesCount: 5,
    minimumQuorum: 3
  }, { evidence, a2z });

  console.log('Quorum Status:', mpcResult.quorumStatus);
  console.log('Active/Total Signers:', `${mpcResult.activeSigners}/${mpcResult.totalSigners}`);
  console.log('Reconstructed Signature:', mpcResult.reconstructedSignature);
  if (mpcResult.quorumStatus !== 'REACHED' || !mpcResult.reconstructedSignature) {
    throw new Error('Test 6 Failed: expected MPC quorum to be REACHED and signed');
  }

  console.log('\n=== ALL ADVANCED SECURITY TESTS COMPLETED GREEN ===');
}

runTests().catch(err => {
  console.error('Test run failed:');
  console.error(err);
  process.exit(1);
});
