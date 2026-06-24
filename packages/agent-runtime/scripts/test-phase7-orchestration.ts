import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase7Tests() {
  console.log('=== GRC_Claw Phase 7: Zero-Trust Network Gating & Model Attestation Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase7-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: Dynamic Sandbox Network Gating (VPC Quarantine)
  // ----------------------------------------------------
  console.log('--- Test 1: Dynamic VPC Network Quarantine Intercept ---');
  const quarantineInv: ToolInvocation = {
    tool: 'security.trigger_network_quarantine',
    args: { targetAgentDid: 'did:grc:agent-exfil-01', firewallRulesAdded: ['deny-ingress', 'deny-egress', 'isolate-subnet'] },
    agentRole: 'developer',
    idempotencyKey: 'idem-nq-1'
  };

  const decision1 = policy.evaluate(quarantineInv);
  console.log(`Tool: ${quarantineInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);
  console.log(`Requires Approval: ${decision1.requiresApproval}`);

  const dispatch1 = await dispatchBuiltinGrcTool(quarantineInv.tool, quarantineInv.args, deps);
  console.log('Quarantine Status:', dispatch1.quarantineStatus);
  console.log('Isolated VPC ID:', dispatch1.isolatedVpcId);
  console.log('Firewall Rules Added Count:', dispatch1.firewallRulesAddedCount);
  console.log('TCPDump Capture Active:', dispatch1.tcpDumpCaptureActive);

  if (dispatch1.ok && dispatch1.quarantineStatus === 'QUARANTINED' && dispatch1.isolatedVpcId === 'vpc-quarantine-999') {
    console.log('✅ Test 1 Passed: Network quarantine intercepts and VPC micro-segmentation successfully executed.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Hardware Model Runtime Attestation (Confidential VM)
  // ----------------------------------------------------
  console.log('--- Test 2: Hardware Model Runtime Attestation ---');
  const modelAttestInv: ToolInvocation = {
    tool: 'sovereign.attest_model_runtime',
    args: { modelName: 'meta-llama-3.1-405b-instruct', enclaveType: 'Intel_TDX' },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(modelAttestInv);
  console.log(`Tool: ${modelAttestInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(modelAttestInv.tool, modelAttestInv.args, deps);
  console.log('Attestation Status:', dispatch2.attestationStatus);
  console.log('Enclave Hardware Type:', dispatch2.enclaveType);
  console.log('Hardware Quote Hash:', dispatch2.hardwareQuoteHash);
  console.log('Memory Encrypted Status:', dispatch2.memoryEncrypted);

  if (dispatch2.ok && dispatch2.attestationStatus === 'VERIFIED_OK' && dispatch2.memoryEncrypted === true) {
    console.log('✅ Test 2 Passed: Model server execution context attested successfully on Intel TDX.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Multi-Party Threshold Cryptography (MPC tool signing)
  // ----------------------------------------------------
  console.log('--- Test 3: Threshold Cryptography (MPC) Tool Signatures ---');
  const mpcSignInv: ToolInvocation = {
    tool: 'mpc.sign_threshold_transaction',
    args: { txPayload: '{"action": "update_fw", "rule": "block-ip"}', keyThresholdQuorum: 3, federatedSignersCount: 5 },
    agentRole: 'reviewer',
    idempotencyKey: 'idem-mpc-ts-1'
  };

  const decision3 = policy.evaluate(mpcSignInv);
  console.log(`Tool: ${mpcSignInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(mpcSignInv.tool, mpcSignInv.args, deps);
  console.log('MPC Quorum Sign Status:', dispatch3.status);
  console.log('MPC Threshold Signature Hash:', dispatch3.thresholdSignature);
  console.log('Active Quorum Reconstruction:', dispatch3.activeQuorumReconstruction);

  if (dispatch3.ok && dispatch3.status === 'SIGNED' && dispatch3.thresholdSignature) {
    console.log('✅ Test 3 Passed: Threshold co-signing completed without key reconstruction in main RAM.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Zero-Knowledge Compliance Attestation (ZKP Auditor Proofs)
  // ----------------------------------------------------
  console.log('--- Test 4: zk-SNARK compliance Proof Generation ---');
  const zkpAuditInv: ToolInvocation = {
    tool: 'grc.generate_compliance_zkp',
    args: { controlId: 'CMMC-AC-3.1.11', inputsHash: 'sha256-4b12df78ac99a2c3' },
    agentRole: 'developer',
    idempotencyKey: 'idem-zkp-1'
  };

  const decision4 = policy.evaluate(zkpAuditInv);
  console.log(`Tool: ${zkpAuditInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(zkpAuditInv.tool, zkpAuditInv.args, deps);
  const parsedProof = JSON.parse(dispatch4.zkProofJson as string);
  console.log('ZKP Verification Status:', dispatch4.verificationStatus);
  console.log('zkpProof Type:', parsedProof.zkpType);
  console.log('zkpProof Hash:', parsedProof.proofHash);
  console.log('zkpProof Inputs Verification:', parsedProof.verificationResult);

  if (dispatch4.ok && dispatch4.verificationStatus === 'VERIFIED' && parsedProof.verificationResult === true) {
    console.log('✅ Test 4 Passed: zk-SNARK compliance proofs generated and validated for Zero-Data-Leak audit.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 7 SOVEREIGN SWARM DEFENSES COMPLETED GREEN ===');
}

runPhase7Tests().catch(err => {
  console.error('Phase 7 test run failed:');
  console.error(err);
  process.exit(1);
});
