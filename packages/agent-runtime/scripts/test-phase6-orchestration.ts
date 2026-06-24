import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase6Tests() {
  console.log('=== GRC_Claw Phase 6: Sovereign Swarm Defenses & Consensus Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase6-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: Autonomous Swarm Red-Teaming (Chaos Compliance)
  // ----------------------------------------------------
  console.log('--- Test 1: Swarm Red-Team Exploit Simulation ---');
  const redteamInv: ToolInvocation = {
    tool: 'security.redteam_sandbox_exploit',
    args: { exploitPayload: 'prompt_injection_jailbreak_v4', targetAgentDid: 'did:grc:agent-999' },
    agentRole: 'developer',
    idempotencyKey: 'idem-rt-1'
  };

  const decision1 = policy.evaluate(redteamInv);
  console.log(`Tool: ${redteamInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(redteamInv.tool, redteamInv.args, deps);
  console.log('Exploit Status:', dispatch1.exploitStatus);
  console.log('Anomalies Blocked:', JSON.stringify(dispatch1.anomaliesDetected));
  console.log('Auto-Patch Generated:', dispatch1.patchGenerated);
  console.log('Remediation Action:', dispatch1.remediationAction);

  if (dispatch1.ok && dispatch1.exploitStatus === 'BLOCKED' && dispatch1.patchGenerated === true) {
    console.log('✅ Test 1 Passed: Autonomous red-team exploit blocked and remediation rules generated successfully.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Cryptographic Model Weight Verification
  // ----------------------------------------------------
  console.log('--- Test 2: Cryptographic Model Weight Verification ---');
  const modelVerifyInv: ToolInvocation = {
    tool: 'sovereign.verify_model_weights',
    args: { modelName: 'hermes-3-llama-3.1-70b', expectedFingerprint: '0xWEIGHT_FINGERPRINT_SHA256_2026' },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(modelVerifyInv);
  console.log(`Tool: ${modelVerifyInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(modelVerifyInv.tool, modelVerifyInv.args, deps);
  console.log('Weights Verified:', dispatch2.weightsVerified);
  console.log('Hardware Enclave Attestation:', dispatch2.enclaveHardwareAttestation);
  console.log('Attested Tensors status:', dispatch2.status);

  if (dispatch2.ok && dispatch2.weightsVerified === true && dispatch2.status === 'COMPLIANT') {
    console.log('✅ Test 2 Passed: Model weights successfully verified inside secure hardware enclave.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Confidential Enclaved RAG (SGX Vector DB)
  // ----------------------------------------------------
  console.log('--- Test 3: Confidential SGX Enclaved RAG Query ---');
  const enclaveRagInv: ToolInvocation = {
    tool: 'memory.query_enclaved_db',
    args: { queryText: 'retrieval_secret_policy_aims', secureSessionToken: '0xSGX_SESSION_42' },
    agentRole: 'developer'
  };

  const decision3 = policy.evaluate(enclaveRagInv);
  console.log(`Tool: ${enclaveRagInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(enclaveRagInv.tool, enclaveRagInv.args, deps);
  console.log('Enclave Search Status:', dispatch3.enclaveSearchStatus);
  console.log('Matches Count:', dispatch3.matchesCount);
  console.log('SGX Quote Hardware Proof:', dispatch3.hardwareProof.substring(0, 35));

  if (dispatch3.ok && dispatch3.enclaveSearchStatus === 'SUCCESS' && dispatch3.matchesCount === 2) {
    console.log('✅ Test 3 Passed: Confidential SGX enclaved vector RAG query executed and attested.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Cross-Tenant BFT Consensus State Sync
  // ----------------------------------------------------
  console.log('--- Test 4: Cross-Tenant BFT Consensus Sync ---');
  const bftConsensusInv: ToolInvocation = {
    tool: 'consensus.verify_cross_tenant_quorum',
    args: { sourceTenantId: 'tenant-acme', targetTenantId: 'tenant-globex', collaborativeAction: 'approve_soar_containment' },
    agentRole: 'reviewer'
  };

  const decision4 = policy.evaluate(bftConsensusInv);
  console.log(`Tool: ${bftConsensusInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(bftConsensusInv.tool, bftConsensusInv.args, deps);
  console.log('BFT Consensus Reached:', dispatch4.bftConsensusReached);
  console.log('Quorum Hash Signature:', dispatch4.signedQuorumHash);
  console.log('Quorum Signers Count:', dispatch4.signersCount);

  if (dispatch4.ok && dispatch4.bftConsensusReached === true && dispatch4.signersCount === 5) {
    console.log('✅ Test 4 Passed: Cross-tenant BFT state sync successfully verified under quorum consensus.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 6 SOVEREIGN SWARM DEFENSES COMPLETED GREEN ===');
}

runPhase6Tests().catch(err => {
  console.error('Phase 6 test run failed:');
  console.error(err);
  process.exit(1);
});
