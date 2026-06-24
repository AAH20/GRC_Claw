import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase25Tests() {
  console.log('=== GRC_Claw Phase 25: Photonic ZK Attestation & DNA-Locked Wet-Storage Encryption Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  // TEST 1: Deploy Photonic Gate
  console.log('--- Test 1: Deploy Photonic Gate ---');
  const deployGateInv: ToolInvocation = {
    tool: 'security.deploy_photonic_gate',
    args: { gateId: 'photonic-verifier-109' },
    agentRole: 'developer'
  };
  const dispatch1 = await dispatchBuiltinGrcTool(deployGateInv.tool, deployGateInv.args, deps);
  console.log('Status:', dispatch1.status);
  console.log('Deployed:', dispatch1.deployed);
  console.log('Optical Channels Count:', dispatch1.opticalChannelsCount);
  if (dispatch1.ok && dispatch1.deployed && dispatch1.opticalChannelsCount === 16) {
    console.log('✅ Test 1 Passed: Optical channels configured on photonic processing unit.\n');
  } else { throw new Error('❌ Test 1 Failed!'); }

  // TEST 2: Verify Photonic Proof
  console.log('--- Test 2: Verify Photonic Proof ---');
  const verifyPhotonicInv: ToolInvocation = {
    tool: 'security.verify_photonic_proof',
    args: { gateId: dispatch1.gateId },
    agentRole: 'developer'
  };
  const dispatch2 = await dispatchBuiltinGrcTool(verifyPhotonicInv.tool, verifyPhotonicInv.args, deps);
  console.log('Status:', dispatch2.status);
  console.log('Verified:', dispatch2.verified);
  console.log('Interference Pattern Valid:', dispatch2.interferencePatternValid);
  console.log('Verification Time (ns):', dispatch2.verificationTimeNs);
  if (dispatch2.ok && dispatch2.verified && dispatch2.interferencePatternValid && dispatch2.verificationTimeNs <= 50) {
    console.log('✅ Test 2 Passed: Photonic compliance verification evaluated at light-speed.\n');
  } else { throw new Error('❌ Test 2 Failed!'); }

  // TEST 3: Generate DNA Key Share
  console.log('--- Test 3: Generate DNA Key Share ---');
  const generateDnaInv: ToolInvocation = {
    tool: 'consensus.generate_dna_key_share',
    args: { keyId: 'dna-key-mesh-01' },
    agentRole: 'developer'
  };
  const dispatch3 = await dispatchBuiltinGrcTool(generateDnaInv.tool, generateDnaInv.args, deps);
  console.log('Status:', dispatch3.status);
  console.log('Key Share Generated:', dispatch3.keyShareGenerated);
  console.log('Nucleotide Sequence:', dispatch3.nucleotideSequence);
  if (dispatch3.ok && dispatch3.keyShareGenerated && dispatch3.nucleotideSequence === 'ATCGGGCTAAGCTTA') {
    console.log('✅ Test 3 Passed: Cryptographic key share successfully encoded into synthetic DNA.\n');
  } else { throw new Error('❌ Test 3 Failed!'); }

  // TEST 4: Authorize DNA Signature
  console.log('--- Test 4: Authorize DNA Signature ---');
  const authDnaInv: ToolInvocation = {
    tool: 'consensus.auth_dna_signature',
    args: { keyId: dispatch3.keyId },
    agentRole: 'developer'
  };
  const dispatch4 = await dispatchBuiltinGrcTool(authDnaInv.tool, authDnaInv.args, deps);
  console.log('Status:', dispatch4.status);
  console.log('Authenticated:', dispatch4.authenticated);
  console.log('Bio-Signature Valid:', dispatch4.bioSignatureValid);
  if (dispatch4.ok && dispatch4.authenticated && dispatch4.bioSignatureValid) {
    console.log('✅ Test 4 Passed: Biological wet-storage signature authorized successfully.\n');
  } else { throw new Error('❌ Test 4 Failed!'); }

  // TEST 5: Propose Code Self-Assembly
  console.log('--- Test 5: Propose Code Self-Assembly ---');
  const proposeAssemblyInv: ToolInvocation = {
    tool: 'soverign.propose_code_self_assembly',
    args: { componentId: 'self-heal-patch-99' },
    agentRole: 'developer'
  };
  const dispatch5 = await dispatchBuiltinGrcTool(proposeAssemblyInv.tool, proposeAssemblyInv.args, deps);
  console.log('Status:', dispatch5.status);
  console.log('Proposed:', dispatch5.proposed);
  console.log('Diff Lines Count:', dispatch5.diffLinesCount);
  if (dispatch5.ok && dispatch5.proposed && dispatch5.diffLinesCount === 42) {
    console.log('✅ Test 5 Passed: Local codebase self-assembly mutation proposed successfully.\n');
  } else { throw new Error('❌ Test 5 Failed!'); }

  // TEST 6: Verify Self-Assembled Logic
  console.log('--- Test 6: Verify Self-Assembled Logic ---');
  const verifyLogicInv: ToolInvocation = {
    tool: 'soverign.verify_self_assembled_logic',
    args: { componentId: dispatch5.componentId },
    agentRole: 'developer'
  };
  const dispatch6 = await dispatchBuiltinGrcTool(verifyLogicInv.tool, verifyLogicInv.args, deps);
  console.log('Status:', dispatch6.status);
  console.log('Verified:', dispatch6.verified);
  console.log('CompCert Compiled:', dispatch6.compcertCompiled);
  console.log('Safety Invariants Verified:', dispatch6.safetyInvariantsVerified);
  if (dispatch6.ok && dispatch6.verified && dispatch6.compcertCompiled && dispatch6.safetyInvariantsVerified) {
    console.log('✅ Test 6 Passed: Synthesized code formally verified inside enclave.\n');
  } else { throw new Error('❌ Test 6 Failed!'); }

  // TEST 7: Crystallize Photonic State
  console.log('--- Test 7: Crystallize Photonic State ---');
  const crystallizeInv: ToolInvocation = {
    tool: 'memory.crystallize_photonic_state',
    args: { stateId: 'context-crystallize-7' },
    agentRole: 'developer'
  };
  const dispatch7 = await dispatchBuiltinGrcTool(crystallizeInv.tool, crystallizeInv.args, deps);
  console.log('Status:', dispatch7.status);
  console.log('Crystallized:', dispatch7.crystallized);
  console.log('Optical State Hash:', dispatch7.opticalStateHash);
  if (dispatch7.ok && dispatch7.crystallized && dispatch7.opticalStateHash === '0xlaser_state_ee9922a1') {
    console.log('✅ Test 7 Passed: Active memory state crystallized into optical structures.\n');
  } else { throw new Error('❌ Test 7 Failed!'); }

  // TEST 8: Read Photonic State
  console.log('--- Test 8: Read Photonic State ---');
  const readPhotonicInv: ToolInvocation = {
    tool: 'memory.read_photonic_state',
    args: { stateId: dispatch7.stateId },
    agentRole: 'developer'
  };
  const dispatch8 = await dispatchBuiltinGrcTool(readPhotonicInv.tool, readPhotonicInv.args, deps);
  console.log('Status:', dispatch8.status);
  console.log('Decoded:', dispatch8.decoded);
  console.log('State Restored:', dispatch8.stateRestored);
  if (dispatch8.ok && dispatch8.decoded && dispatch8.stateRestored) {
    console.log('✅ Test 8 Passed: Crystallized photonic memory successfully read and restored.\n');
  } else { throw new Error('❌ Test 8 Failed!'); }

  console.log('=== ALL PHASE 25 PHOTONIC & DNA TESTS GREEN ===');
}

runPhase25Tests().catch(err => {
  console.error('Phase 25 test run failed:');
  console.error(err);
  process.exit(1);
});
