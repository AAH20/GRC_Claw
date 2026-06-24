import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase21Tests() {
  console.log('=== GRC_Claw Phase 21: Zero-Trust Synaptic Guardrails & Kernel-Level Socket Isolation Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  // TEST 1: eBPF Socket Block Application
  console.log('--- Test 1: eBPF Socket Block Application ---');
  const socketBlockInv: ToolInvocation = {
    tool: 'security.apply_ebpf_socket_block',
    args: { targetPid: process.pid, blockedIp: '10.0.0.99' },
    agentRole: 'developer'
  };
  const dispatch1 = await dispatchBuiltinGrcTool(socketBlockInv.tool, socketBlockInv.args, deps);
  console.log('Status:', dispatch1.status);
  console.log('Sockops Hook ID:', dispatch1.sockopsHookId);
  console.log('Quarantine Status:', dispatch1.quarantineStatus);
  if (dispatch1.ok && dispatch1.deployed && dispatch1.quarantineStatus === 'ACTIVE') {
    console.log('✅ Test 1 Passed: eBPF socket block active on target process.\n');
  } else { throw new Error('❌ Test 1 Failed!'); }

  // TEST 2: eBPF Socket Quarantine Verification
  console.log('--- Test 2: eBPF Socket Quarantine Verification ---');
  const verifyBlockInv: ToolInvocation = {
    tool: 'security.verify_socket_quarantine',
    args: { sockopsHookId: dispatch1.sockopsHookId },
    agentRole: 'developer'
  };
  const dispatch2 = await dispatchBuiltinGrcTool(verifyBlockInv.tool, verifyBlockInv.args, deps);
  console.log('Status:', dispatch2.status);
  console.log('Quarantine Active:', dispatch2.quarantineActive);
  console.log('Dropped Packets:', dispatch2.droppedPacketsCount);
  if (dispatch2.ok && dispatch2.verified && dispatch2.quarantineActive && dispatch2.droppedPacketsCount > 0) {
    console.log('✅ Test 2 Passed: Dynamic socket quarantine verified with packet drop trace.\n');
  } else { throw new Error('❌ Test 2 Failed!'); }

  // TEST 3: Homomorphic Vector RAG Query
  console.log('--- Test 3: Homomorphic Vector RAG Query ---');
  const queryInv: ToolInvocation = {
    tool: 'memory.query_homomorphic_vector',
    args: { encryptedQuery: '0xenc_query_11a88bceea98e' },
    agentRole: 'developer'
  };
  const dispatch3 = await dispatchBuiltinGrcTool(queryInv.tool, queryInv.args, deps);
  console.log('Status:', dispatch3.status);
  console.log('Encrypted Results Count:', dispatch3.encryptedResultsCount);
  console.log('Encrypted Payload Hash:', dispatch3.encryptedPayloadHash);
  if (dispatch3.ok && dispatch3.matched && dispatch3.encryptedResultsCount === 3 && String(dispatch3.encryptedPayloadHash).startsWith('0xenc_payload_')) {
    console.log('✅ Test 3 Passed: Homomorphic similarity query completed over encrypted vector space.\n');
  } else { throw new Error('❌ Test 3 Failed!'); }

  // TEST 4: Homomorphic Vector Decryption Verification
  console.log('--- Test 4: Homomorphic Vector Decryption Verification ---');
  const verifyDecInv: ToolInvocation = {
    tool: 'memory.verify_homomorphic_decryption',
    args: { encryptedPayloadHash: dispatch3.encryptedPayloadHash },
    agentRole: 'developer'
  };
  const dispatch4 = await dispatchBuiltinGrcTool(verifyDecInv.tool, verifyDecInv.args, deps);
  console.log('Status:', dispatch4.status);
  console.log('Decryption Successful:', dispatch4.decryptionSuccessful);
  console.log('Enclave Decrypted:', dispatch4.enclaveDecrypted);
  if (dispatch4.ok && dispatch4.verified && dispatch4.decryptionSuccessful && dispatch4.enclaveDecrypted) {
    console.log('✅ Test 4 Passed: Client enclave decryption validated with full payload integrity.\n');
  } else { throw new Error('❌ Test 4 Failed!'); }

  // TEST 5: BFT Reasoning Quorum Evaluation
  console.log('--- Test 5: BFT Reasoning Quorum Evaluation ---');
  const bftQuorumInv: ToolInvocation = {
    tool: 'consensus.evaluate_bft_quorum',
    args: { targetDecision: 'revoke_cert_auth', votes: ['approve', 'approve', 'approve', 'reject', 'approve'] },
    agentRole: 'developer'
  };
  const dispatch5 = await dispatchBuiltinGrcTool(bftQuorumInv.tool, bftQuorumInv.args, deps);
  console.log('Status:', dispatch5.status);
  console.log('Quorum Reached:', dispatch5.bftConsensusReached);
  console.log('Next BFT Step:', dispatch5.nextBftStep);
  if (dispatch5.ok && dispatch5.evaluated && dispatch5.bftConsensusReached && dispatch5.nextBftStep === 'EXECUTE') {
    console.log('✅ Test 5 Passed: Byzantine Fault Tolerant reasoning quorum evaluated successfully.\n');
  } else { throw new Error('❌ Test 5 Failed!'); }

  // TEST 6: BFT Signature Verification
  console.log('--- Test 6: BFT Signature Verification ---');
  const bftVerifyInv: ToolInvocation = {
    tool: 'consensus.verify_bft_signatures',
    args: { targetDecision: dispatch5.targetDecision },
    agentRole: 'developer'
  };
  const dispatch6 = await dispatchBuiltinGrcTool(bftVerifyInv.tool, bftVerifyInv.args, deps);
  console.log('Status:', dispatch6.status);
  console.log('Signatures Count:', dispatch6.signaturesCount);
  console.log('All Signatures Valid:', dispatch6.allSignaturesValid);
  if (dispatch6.ok && dispatch6.verified && dispatch6.allSignaturesValid && dispatch6.signaturesCount === 4) {
    console.log('✅ Test 6 Passed: Quorum validator signatures and consensus root verified.\n');
  } else { throw new Error('❌ Test 6 Failed!'); }

  // TEST 7: Synaptic LoRA Patch Compilation
  console.log('--- Test 7: Synaptic LoRA Patch Compilation ---');
  const loraCompInv: ToolInvocation = {
    tool: 'soverign.compile_synaptic_patch',
    args: { targetModelId: 'llama-3-8b', complianceConstraint: 'block_key_leakage' },
    agentRole: 'developer'
  };
  const dispatch7 = await dispatchBuiltinGrcTool(loraCompInv.tool, loraCompInv.args, deps);
  console.log('Status:', dispatch7.status);
  console.log('Patch ID:', dispatch7.patchId);
  console.log('Parameter Deltas:', dispatch7.estimatedParameterDeltaCount);
  if (dispatch7.ok && dispatch7.compiled && String(dispatch7.patchId).startsWith('lora-synaptic-')) {
    console.log('✅ Test 7 Passed: Synaptic parameter patch compiled for compliance boundary alignment.\n');
  } else { throw new Error('❌ Test 7 Failed!'); }

  // TEST 8: Runtime Synaptic Patch Application
  console.log('--- Test 8: Runtime Synaptic Patch Application ---');
  const loraApplyInv: ToolInvocation = {
    tool: 'soverign.apply_runtime_synaptic_patch',
    args: { patchId: dispatch7.patchId },
    agentRole: 'developer'
  };
  const dispatch8 = await dispatchBuiltinGrcTool(loraApplyInv.tool, loraApplyInv.args, deps);
  console.log('Status:', dispatch8.status);
  console.log('Patched Model Version:', dispatch8.patchedModelVersion);
  console.log('Steering Active:', dispatch8.steeringActive);
  if (dispatch8.ok && dispatch8.applied && dispatch8.steeringActive && dispatch8.patchedModelVersion === 'llama-3-8b-patched-v19.4') {
    console.log('✅ Test 8 Passed: Dynamic synaptic LoRA patch hot-plugged into inference server.\n');
  } else { throw new Error('❌ Test 8 Failed!'); }

  console.log('=== ALL PHASE 21 ZERO-TRUST KERNEL & SYNAPTIC GUARD TESTS GREEN ===');
}

runPhase21Tests().catch(err => {
  console.error('Phase 21 test run failed:');
  console.error(err);
  process.exit(1);
});
