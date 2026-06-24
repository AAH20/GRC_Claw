import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase22Tests() {
  console.log('=== GRC_Claw Phase 22: MicroVM Guest-Kernel Sandboxing & Recursive ZK-Proof Aggregation Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  // TEST 1: MicroVM eBPF Sandbox Application
  console.log('--- Test 1: MicroVM eBPF Sandbox Application ---');
  const mvmSandboxInv: ToolInvocation = {
    tool: 'security.apply_microvm_ebpf_sandbox',
    args: { sandboxId: 'firecracker-mvm-42' },
    agentRole: 'developer'
  };
  const dispatch1 = await dispatchBuiltinGrcTool(mvmSandboxInv.tool, mvmSandboxInv.args, deps);
  console.log('Status:', dispatch1.status);
  console.log('Guest Kernel Hook ID:', dispatch1.guestKernelHookId);
  console.log('Filter Status:', dispatch1.kernelFilterStatus);
  if (dispatch1.ok && dispatch1.deployed && dispatch1.kernelFilterStatus === 'ACTIVE') {
    console.log('✅ Test 1 Passed: Guest-kernel eBPF hooks deployed inside the MicroVM sandbox.\n');
  } else { throw new Error('❌ Test 1 Failed!'); }

  // TEST 2: MicroVM Isolation Verification
  console.log('--- Test 2: MicroVM Isolation Verification ---');
  const verifyMvmInv: ToolInvocation = {
    tool: 'security.verify_microvm_isolation',
    args: { sandboxId: dispatch1.sandboxId },
    agentRole: 'developer'
  };
  const dispatch2 = await dispatchBuiltinGrcTool(verifyMvmInv.tool, verifyMvmInv.args, deps);
  console.log('Status:', dispatch2.status);
  console.log('Isolation Intact:', dispatch2.isolationIntact);
  console.log('Device Blocked Count:', dispatch2.deviceAccessBlockedCount);
  if (dispatch2.ok && dispatch2.verified && dispatch2.isolationIntact && dispatch2.deviceAccessBlockedCount > 0) {
    console.log('✅ Test 2 Passed: Guest-to-host containment and isolation verified successfully.\n');
  } else { throw new Error('❌ Test 2 Failed!'); }

  // TEST 3: Homomorphic Joint-Policy Auditing
  console.log('--- Test 3: Homomorphic Joint-Policy Auditing ---');
  const auditInv: ToolInvocation = {
    tool: 'audit.evaluate_homomorphic_joint_policy',
    args: { targetControlId: 'AC-3', queryMatrix: ['check_admin_mfa', 'verify_encryption_key'] },
    agentRole: 'developer'
  };
  const dispatch3 = await dispatchBuiltinGrcTool(auditInv.tool, auditInv.args, deps);
  console.log('Status:', dispatch3.status);
  console.log('Encrypted Report Hash:', dispatch3.encryptedReportHash);
  console.log('Evaluation Success:', dispatch3.evaluationSuccess);
  if (dispatch3.ok && dispatch3.evaluated && dispatch3.evaluationSuccess && String(dispatch3.encryptedReportHash).startsWith('0xenc_report_')) {
    console.log('✅ Test 3 Passed: Multi-party compliance query evaluated homomorphically over encrypted assets.\n');
  } else { throw new Error('❌ Test 3 Failed!'); }

  // TEST 4: Joint Policy Proof Verification
  console.log('--- Test 4: Joint Policy Proof Verification ---');
  const verifyProofInv: ToolInvocation = {
    tool: 'audit.verify_joint_policy_proof',
    args: { encryptedReportHash: dispatch3.encryptedReportHash },
    agentRole: 'developer'
  };
  const dispatch4 = await dispatchBuiltinGrcTool(verifyProofInv.tool, verifyProofInv.args, deps);
  console.log('Status:', dispatch4.status);
  console.log('ZK Proof Valid:', dispatch4.zkProofValid);
  console.log('Policy Compliant:', dispatch4.policyCompliant);
  if (dispatch4.ok && dispatch4.verified && dispatch4.zkProofValid && dispatch4.policyCompliant) {
    console.log('✅ Test 4 Passed: Cryptographic proof of homomorphic joint-policy audit verified.\n');
  } else { throw new Error('❌ Test 4 Failed!'); }

  // TEST 5: ZK Evidence Proofs Aggregation
  console.log('--- Test 5: ZK Evidence Proofs Aggregation ---');
  const aggregateInv: ToolInvocation = {
    tool: 'consensus.aggregate_zk_evidence_proofs',
    args: { proofCids: ['bafy_proof_ciso1', 'bafy_proof_auditor2', 'bafy_proof_client3'] },
    agentRole: 'developer'
  };
  const dispatch5 = await dispatchBuiltinGrcTool(aggregateInv.tool, aggregateInv.args, deps);
  console.log('Status:', dispatch5.status);
  console.log('Rollup Proof CID:', dispatch5.rollupProofCid);
  console.log('Aggregated Proofs Count:', dispatch5.aggregatedProofsCount);
  if (dispatch5.ok && dispatch5.aggregated && dispatch5.aggregatedProofsCount === 3 && String(dispatch5.rollupProofCid).startsWith('bafy2bzace_aggregated_')) {
    console.log('✅ Test 5 Passed: Multiple individual ZK proofs recursively aggregated into Halo2 rollup.\n');
  } else { throw new Error('❌ Test 5 Failed!'); }

  // TEST 6: Aggregated Rollup Verification
  console.log('--- Test 6: Aggregated Rollup Verification ---');
  const verifyRollupInv: ToolInvocation = {
    tool: 'consensus.verify_aggregated_rollup',
    args: { rollupProofCid: dispatch5.rollupProofCid },
    agentRole: 'developer'
  };
  const dispatch6 = await dispatchBuiltinGrcTool(verifyRollupInv.tool, verifyRollupInv.args, deps);
  console.log('Status:', dispatch6.status);
  console.log('Rollup Proof Valid:', dispatch6.rollupProofValid);
  console.log('Verification Time (ms):', dispatch6.aggregatedVerificationTimeMs);
  if (dispatch6.ok && dispatch6.verified && dispatch6.rollupProofValid) {
    console.log('✅ Test 6 Passed: Consolidated Halo2 rollup proof verified in millisecond scale.\n');
  } else { throw new Error('❌ Test 6 Failed!'); }

  // TEST 7: GPU Attention Entropy Tracking
  console.log('--- Test 7: GPU Attention Entropy Tracking ---');
  const trackInv: ToolInvocation = {
    tool: 'soverign.track_attention_entropy',
    args: { targetSessionId: 'session-adversary-trap' },
    agentRole: 'developer'
  };
  const dispatch7 = await dispatchBuiltinGrcTool(trackInv.tool, trackInv.args, deps);
  console.log('Status:', dispatch7.status);
  console.log('Attention Entropy Score:', dispatch7.attentionEntropyScore);
  console.log('Focus Steering Required:', dispatch7.focusSteeringRequired);
  if (dispatch7.ok && dispatch7.tracked && dispatch7.attentionEntropyScore > 0.5 && dispatch7.focusSteeringRequired) {
    console.log('✅ Test 7 Passed: GPU-level attention weight entropy and focal drift tracked.\n');
  } else { throw new Error('❌ Test 7 Failed!'); }

  // TEST 8: GPU Attention Redirection Steering
  console.log('--- Test 8: GPU Attention Redirection Steering ---');
  const steerInv: ToolInvocation = {
    tool: 'soverign.steer_attention_redirection',
    args: { targetSessionId: dispatch7.targetSessionId },
    agentRole: 'developer'
  };
  const dispatch8 = await dispatchBuiltinGrcTool(steerInv.tool, steerInv.args, deps);
  console.log('Status:', dispatch8.status);
  console.log('Active Steering Vectors:', dispatch8.activeSteeringVectorsCount);
  console.log('Generation Corrected:', dispatch8.generationCorrected);
  if (dispatch8.ok && dispatch8.steered && dispatch8.generationCorrected && dispatch8.activeSteeringVectorsCount === 8) {
    console.log('✅ Test 8 Passed: GPU attention weights dynamically overwritten to redirect model trajectory.\n');
  } else { throw new Error('❌ Test 8 Failed!'); }

  console.log('=== ALL PHASE 22 MICROVM & RECURSIVE CRYPTO TESTS GREEN ===');
}

runPhase22Tests().catch(err => {
  console.error('Phase 22 test run failed:');
  console.error(err);
  process.exit(1);
});
