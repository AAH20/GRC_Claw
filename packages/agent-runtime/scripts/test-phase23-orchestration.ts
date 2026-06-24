import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase23Tests() {
  console.log('=== GRC_Claw Phase 23: DPU Cognitive Offloading & Hardware-Locked Enclave Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  // TEST 1: DPU Cognitive Filter Offloading
  console.log('--- Test 1: DPU Cognitive Filter Offloading ---');
  const dpuFilterOffloadInv: ToolInvocation = {
    tool: 'security.offload_dpu_cognitive_filter',
    args: { filterId: 'smartnic-filter-77' },
    agentRole: 'developer'
  };
  const dispatch1 = await dispatchBuiltinGrcTool(dpuFilterOffloadInv.tool, dpuFilterOffloadInv.args, deps);
  console.log('Status:', dispatch1.status);
  console.log('DPU Target:', dispatch1.dpuTarget);
  console.log('Deployed:', dispatch1.deployed);
  if (dispatch1.ok && dispatch1.deployed && dispatch1.dpuTarget === 'bluefield-3') {
    console.log('✅ Test 1 Passed: Cognitive filters successfully offloaded to DPU/SmartNIC hardware.\n');
  } else { throw new Error('❌ Test 1 Failed!'); }

  // TEST 2: DPU Offload Status Query
  console.log('--- Test 2: DPU Offload Status Query ---');
  const dpuStatusInv: ToolInvocation = {
    tool: 'security.query_dpu_offload_status',
    args: { filterId: dispatch1.filterId },
    agentRole: 'developer'
  };
  const dispatch2 = await dispatchBuiltinGrcTool(dpuStatusInv.tool, dpuStatusInv.args, deps);
  console.log('Status:', dispatch2.status);
  console.log('Hardware Status:', dispatch2.hardwareStatus);
  console.log('Throughput (Gbps):', dispatch2.throughputGbps);
  console.log('Latency (ns):', dispatch2.latencyNs);
  if (dispatch2.ok && dispatch2.hardwareStatus === 'ACTIVE' && dispatch2.throughputGbps > 50 && dispatch2.latencyNs <= 150) {
    console.log('✅ Test 2 Passed: DPU hardware status and packet latency metrics queried successfully.\n');
  } else { throw new Error('❌ Test 2 Failed!'); }

  // TEST 3: Lattice Ring Attestation Signing
  console.log('--- Test 3: Lattice Ring Attestation Signing ---');
  const signLatticeInv: ToolInvocation = {
    tool: 'consensus.sign_lattice_ring_attestation',
    args: { ringMembers: ['ciso-org1', 'ciso-org2', 'auditor-node'], statementHash: '0xabcde1234f' },
    agentRole: 'developer'
  };
  const dispatch3 = await dispatchBuiltinGrcTool(signLatticeInv.tool, signLatticeInv.args, deps);
  console.log('Status:', dispatch3.status);
  console.log('Signed:', dispatch3.signed);
  console.log('Signature Hex:', dispatch3.latticeSignatureHex);
  if (dispatch3.ok && dispatch3.signed && String(dispatch3.latticeSignatureHex).startsWith('0xdilithium5_sig_')) {
    console.log('✅ Test 3 Passed: Post-quantum lattice-based ring signature generated successfully.\n');
  } else { throw new Error('❌ Test 3 Failed!'); }

  // TEST 4: Lattice Ring Signature Verification
  console.log('--- Test 4: Lattice Ring Signature Verification ---');
  const verifyLatticeInv: ToolInvocation = {
    tool: 'consensus.verify_lattice_ring_attestation',
    args: { latticeSignatureHex: dispatch3.latticeSignatureHex },
    agentRole: 'developer'
  };
  const dispatch4 = await dispatchBuiltinGrcTool(verifyLatticeInv.tool, verifyLatticeInv.args, deps);
  console.log('Status:', dispatch4.status);
  console.log('Verified:', dispatch4.verified);
  console.log('Ring Valid:', dispatch4.ringValid);
  if (dispatch4.ok && dispatch4.verified && dispatch4.ringValid) {
    console.log('✅ Test 4 Passed: Anonymous post-quantum ring attestation verified successfully.\n');
  } else { throw new Error('❌ Test 4 Failed!'); }

  // TEST 5: Instantiate Secure Enclave
  console.log('--- Test 5: Instantiate Secure Enclave ---');
  const enclaveInv: ToolInvocation = {
    tool: 'soverign.instantiate_secure_enclave',
    args: { enclaveId: 'sev-snp-enclave-42' },
    agentRole: 'developer'
  };
  const dispatch5 = await dispatchBuiltinGrcTool(enclaveInv.tool, enclaveInv.args, deps);
  console.log('Status:', dispatch5.status);
  console.log('Enclave Instantiated:', dispatch5.enclaveInstantiated);
  console.log('Enclave Type:', dispatch5.enclaveType);
  console.log('Hardware Quote:', dispatch5.hardwareSignedQuote);
  if (dispatch5.ok && dispatch5.enclaveInstantiated && dispatch5.enclaveType === 'AMD_SEV_SNP') {
    console.log('✅ Test 5 Passed: Hardware-locked secure enclave instantiated successfully.\n');
  } else { throw new Error('❌ Test 5 Failed!'); }

  // TEST 6: Verify Enclave Quote
  console.log('--- Test 6: Verify Enclave Quote ---');
  const verifyQuoteInv: ToolInvocation = {
    tool: 'soverign.verify_enclave_quote',
    args: { hardwareSignedQuote: dispatch5.hardwareSignedQuote },
    agentRole: 'developer'
  };
  const dispatch6 = await dispatchBuiltinGrcTool(verifyQuoteInv.tool, verifyQuoteInv.args, deps);
  console.log('Status:', dispatch6.status);
  console.log('Verified:', dispatch6.verified);
  console.log('Quote Valid:', dispatch6.quoteValid);
  if (dispatch6.ok && dispatch6.verified && dispatch6.quoteValid) {
    console.log('✅ Test 6 Passed: Secure enclave hardware-signed quote verified successfully.\n');
  } else { throw new Error('❌ Test 6 Failed!'); }

  // TEST 7: Propose Formal Policy Evolution
  console.log('--- Test 7: Propose Formal Policy Evolution ---');
  const proposePolicyInv: ToolInvocation = {
    tool: 'sdk.propose_formal_policy_evolution',
    args: { frameworkId: 'NIST_AI_RMF_1_0', policyDelta: 'assert_isolation_boundary_always_active' },
    agentRole: 'developer'
  };
  const dispatch7 = await dispatchBuiltinGrcTool(proposePolicyInv.tool, proposePolicyInv.args, deps);
  console.log('Status:', dispatch7.status);
  console.log('Proposed:', dispatch7.proposed);
  console.log('Proposal ID:', dispatch7.proposalId);
  if (dispatch7.ok && dispatch7.proposed && dispatch7.proposalId === 'prop-formal-882') {
    console.log('✅ Test 7 Passed: Autonomous policy evolution proposal registered successfully.\n');
  } else { throw new Error('❌ Test 7 Failed!'); }

  // TEST 8: Verify Policy Formal Proof
  console.log('--- Test 8: Verify Policy Formal Proof ---');
  const verifyProofInv: ToolInvocation = {
    tool: 'sdk.verify_policy_formal_proof',
    args: { proposalId: dispatch7.proposalId },
    agentRole: 'developer'
  };
  const dispatch8 = await dispatchBuiltinGrcTool(verifyProofInv.tool, verifyProofInv.args, deps);
  console.log('Status:', dispatch8.status);
  console.log('Verified:', dispatch8.verified);
  console.log('SMT Solved:', dispatch8.smtSolved);
  console.log('Formal Proof Valid:', dispatch8.formalProofValid);
  if (dispatch8.ok && dispatch8.verified && dispatch8.smtSolved && dispatch8.formalProofValid) {
    console.log('✅ Test 8 Passed: Safety invariants formally verified via SMT solver.\n');
  } else { throw new Error('❌ Test 8 Failed!'); }

  console.log('=== ALL PHASE 23 DPU & SECURE ENCLAVE TESTS GREEN ===');
}

runPhase23Tests().catch(err => {
  console.error('Phase 23 test run failed:');
  console.error(err);
  process.exit(1);
});
