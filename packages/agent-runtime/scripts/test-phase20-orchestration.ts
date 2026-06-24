import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase20Tests() {
  console.log('=== GRC_Claw Phase 20: Cognitive Decoy Sandboxing & eBPF Runtime Containment Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  // TEST 1: Decoy Honey-Enclave Spawning
  console.log('--- Test 1: Decoy Honey-Enclave Spawning ---');
  const enclaveInv: ToolInvocation = {
    tool: 'sandbox.spawn_honey_enclave',
    args: { targetWorkspace: 'intel-database' },
    agentRole: 'developer'
  };
  const dispatch1 = await dispatchBuiltinGrcTool(enclaveInv.tool, enclaveInv.args, deps);
  console.log('Status:', dispatch1.status);
  console.log('Enclave ID:', dispatch1.enclaveId);
  console.log('Simulated Vault Active:', dispatch1.simulatedVaultActive);
  if (dispatch1.ok && dispatch1.spawned && dispatch1.simulatedVaultActive && String(dispatch1.enclaveId).startsWith('honey-enclave-')) {
    console.log('✅ Test 1 Passed: Ephemeral honey-enclave successfully spawned.\n');
  } else { throw new Error('❌ Test 1 Failed!'); }

  // TEST 2: Decoy Containment Verification
  console.log('--- Test 2: Decoy Containment Verification ---');
  const verifyDecoyInv: ToolInvocation = {
    tool: 'sandbox.verify_decoy_containment',
    args: { enclaveId: dispatch1.enclaveId },
    agentRole: 'developer'
  };
  const dispatch2 = await dispatchBuiltinGrcTool(verifyDecoyInv.tool, verifyDecoyInv.args, deps);
  console.log('Status:', dispatch2.status);
  console.log('Contained:', dispatch2.contained);
  console.log('Syscalls Captured:', dispatch2.attackerSyscallsCapturedCount);
  if (dispatch2.ok && dispatch2.verified && dispatch2.contained && dispatch2.redirectSucceeded) {
    console.log('✅ Test 2 Passed: Attacker successfully routed and contained within decoy enclave.\n');
  } else { throw new Error('❌ Test 2 Failed!'); }

  // TEST 3: Multi-Model Consensus Quorum Submission
  console.log('--- Test 3: Multi-Model Consensus Quorum Submission ---');
  const quorumInv: ToolInvocation = {
    tool: 'consensus.submit_multi_model_quorum',
    args: { targetDecision: 'revoke_compromised_admin_keys' },
    agentRole: 'developer'
  };
  const dispatch3 = await dispatchBuiltinGrcTool(quorumInv.tool, quorumInv.args, deps);
  console.log('Status:', dispatch3.status);
  console.log('Consensus Reached:', dispatch3.consensusQuorumReached);
  console.log('ZK Proof Hash:', dispatch3.zkQuorumProofHash);
  if (dispatch3.ok && dispatch3.submitted && dispatch3.consensusQuorumReached && String(dispatch3.zkQuorumProofHash).startsWith('0xzkp_quorum_')) {
    console.log('✅ Test 3 Passed: Multi-model consensus reached and vote registered.\n');
  } else { throw new Error('❌ Test 3 Failed!'); }

  // TEST 4: Multi-Model ZK Proof Verification
  console.log('--- Test 4: Multi-Model ZK Proof Verification ---');
  const verifyZkInv: ToolInvocation = {
    tool: 'consensus.verify_multi_model_zk_proof',
    args: { zkQuorumProofHash: dispatch3.zkQuorumProofHash },
    agentRole: 'developer'
  };
  const dispatch4 = await dispatchBuiltinGrcTool(verifyZkInv.tool, verifyZkInv.args, deps);
  console.log('Status:', dispatch4.status);
  console.log('ZK Proof Valid:', dispatch4.zkProofValid);
  console.log('Consensus Integrity:', dispatch4.consensusIntegrityVerified);
  if (dispatch4.ok && dispatch4.verified && dispatch4.zkProofValid) {
    console.log('✅ Test 4 Passed: Zero-Knowledge proof of multi-model consensus verified.\n');
  } else { throw new Error('❌ Test 4 Failed!'); }

  // TEST 5: eBPF Session Filter Deployment
  console.log('--- Test 5: eBPF Session Filter Deployment ---');
  const deployEbpfInv: ToolInvocation = {
    tool: 'security.deploy_ebpf_session_filter',
    args: { targetPid: process.pid, syscallAllowlist: ['read', 'write', 'exit_group'] },
    agentRole: 'developer'
  };
  const dispatch5 = await dispatchBuiltinGrcTool(deployEbpfInv.tool, deployEbpfInv.args, deps);
  console.log('Status:', dispatch5.status);
  console.log('Kernel Filter Status:', dispatch5.kernelFilterStatus);
  console.log('eBPF Hook ID:', dispatch5.ebpfHookId);
  if (dispatch5.ok && dispatch5.deployed && dispatch5.kernelFilterStatus === 'ACTIVE') {
    console.log('✅ Test 5 Passed: Dynamic eBPF system call filter active in host kernel.\n');
  } else { throw new Error('❌ Test 5 Failed!'); }

  // TEST 6: eBPF Session Logs Auditing
  console.log('--- Test 6: eBPF Session Logs Auditing ---');
  const auditEbpfInv: ToolInvocation = {
    tool: 'security.query_ebpf_session_logs',
    args: { ebpfHookId: dispatch5.ebpfHookId },
    agentRole: 'developer'
  };
  const dispatch6 = await dispatchBuiltinGrcTool(auditEbpfInv.tool, auditEbpfInv.args, deps);
  console.log('Status:', dispatch6.status);
  console.log('Blocked Syscalls:', dispatch6.blockedSyscallsCount);
  console.log('Logs Length:', dispatch6.logs.length);
  if (dispatch6.ok && dispatch6.audited && dispatch6.blockedSyscallsCount === 0) {
    console.log('✅ Test 6 Passed: Kernel-level eBPF logs successfully audited.\n');
  } else { throw new Error('❌ Test 6 Failed!'); }

  // TEST 7: Biometric TPM Gate Request
  console.log('--- Test 7: Biometric TPM Gate Request ---');
  const bioGateInv: ToolInvocation = {
    tool: 'identity.request_biometric_gate',
    args: { operatorDid: 'did:grc:op-chief-ciso', criticalAction: 'rollback_network_containment' },
    agentRole: 'developer'
  };
  const dispatch7 = await dispatchBuiltinGrcTool(bioGateInv.tool, bioGateInv.args, deps);
  console.log('Status:', dispatch7.status);
  console.log('Challenge ID:', dispatch7.challengeId);
  console.log('Biometric Approval Pending:', dispatch7.biometricApprovalPending);
  if (dispatch7.ok && dispatch7.requested && dispatch7.biometricApprovalPending) {
    console.log('✅ Test 7 Passed: Biometric TouchID/FaceID gate request created.\n');
  } else { throw new Error('❌ Test 7 Failed!'); }

  // TEST 8: Biometric Signature Verification
  console.log('--- Test 8: Biometric Signature Verification ---');
  const verifyBioInv: ToolInvocation = {
    tool: 'identity.verify_biometric_signature',
    args: { challengeId: dispatch7.challengeId, biometricSignature: '0xbiosig_77fa2cb9efde' },
    agentRole: 'developer'
  };
  const dispatch8 = await dispatchBuiltinGrcTool(verifyBioInv.tool, verifyBioInv.args, deps);
  console.log('Status:', dispatch8.status);
  console.log('Biometric Signature Valid:', dispatch8.biometricSignatureValid);
  console.log('TPM Hardware Attestation Valid:', dispatch8.tpmHardwareAttestationValid);
  if (dispatch8.ok && dispatch8.verified && dispatch8.biometricSignatureValid && dispatch8.tpmHardwareAttestationValid) {
    console.log('✅ Test 8 Passed: Biometric operator signature and TPM hardware attestation verified.\n');
  } else { throw new Error('❌ Test 8 Failed!'); }

  console.log('=== ALL PHASE 20 COGNITIVE SANDBOXING & EBPF KERNEL TESTS GREEN ===');
}

runPhase20Tests().catch(err => {
  console.error('Phase 20 test run failed:');
  console.error(err);
  process.exit(1);
});
