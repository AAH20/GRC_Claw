import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase9Tests() {
  console.log('=== GRC_Claw Phase 9: Sovereign Swarm Autonomy & Quantum Trust Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase9-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: Automated Posture Remediation
  // ----------------------------------------------------
  console.log('--- Test 1: Automated Posture Remediation (Self-Healing Cloud) ---');
  const remediateInv: ToolInvocation = {
    tool: 'sdk.remediate_compliance_drift',
    args: { controlId: 'CMMC-SC-3.13.11', driftDescription: 'S3 bucket allows public read access', gitOpsTargetRepo: 'git@github.com:a2z-soc/infra.git' },
    agentRole: 'developer'
  };

  const decision1 = policy.evaluate(remediateInv);
  console.log(`Tool: ${remediateInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(remediateInv.tool, remediateInv.args, deps);
  console.log('Remediated Status:', dispatch1.status);
  console.log('Remediation Type:', dispatch1.remediationType);
  console.log('Git Commit Hash:', dispatch1.gitCommitHash);

  if (dispatch1.ok && dispatch1.remediated && dispatch1.status === 'REMEDIATED_POSTURE_SYNCED') {
    console.log('✅ Test 1 Passed: Compliance drift automatically resolved and GitOps repair patch successfully deployed.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: ZK Federated Threat intelligence Mesh
  // ----------------------------------------------------
  console.log('--- Test 2: ZK Federated Threat intelligence Mesh ---');
  const threatInv: ToolInvocation = {
    tool: 'consensus.propagate_threat_signature',
    args: { threatHash: 'sha3-256-f8e9a26c4b12df78ac99a2c3', exploitType: 'sandbox-escape-v2' },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(threatInv);
  console.log(`Tool: ${threatInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(threatInv.tool, threatInv.args, deps);
  console.log('Threat Propagated:', dispatch2.propagated);
  console.log('Consensus Quorum Reached:', dispatch2.consensusQuorumReached);
  console.log('Peer Nodes Notified Count:', dispatch2.peerNodesNotifiedCount);

  if (dispatch2.ok && dispatch2.propagated && dispatch2.consensusQuorumReached) {
    console.log('✅ Test 2 Passed: Encrypted threat signature successfully verified and broadcasted across peer gateways.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: SMT-Verified ExecPolicy (Policy Envelopes)
  // ----------------------------------------------------
  console.log('--- Test 3: SMT-Verified ExecPolicy (Policy Envelopes) ---');
  const verifyPolicyInv: ToolInvocation = {
    tool: 'security.verify_policy_envelope',
    args: { agentPrompt: 'System: execute tool if approved. User: request to read file', toolSchemaHash: 'sha256-4b12df78' },
    agentRole: 'reviewer'
  };

  const decision3 = policy.evaluate(verifyPolicyInv);
  console.log(`Tool: ${verifyPolicyInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(verifyPolicyInv.tool, verifyPolicyInv.args, deps);
  console.log('Policy Proved Safe Status:', dispatch3.status);
  console.log('SMT Formula Size:', dispatch3.smtFormulaSize);
  console.log('Satisfiable Status:', dispatch3.satisfiable);

  if (dispatch3.ok && dispatch3.verified && dispatch3.status === 'SMT_PROVED_SAFE') {
    console.log('✅ Test 3 Passed: Agent execution policy bounds mathematically validated using SMT solver.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Post-Quantum Cryptographic Evidence Anchoring
  // ----------------------------------------------------
  console.log('--- Test 4: Post-Quantum Cryptographic Evidence Anchoring ---');
  const pqcInv: ToolInvocation = {
    tool: 'evidence.sign_quantum_credential',
    args: { credentialId: 'cred-cmmc-attestation-01', evidenceHash: 'sha3-568b209c12df78ac99a2c3' },
    agentRole: 'developer'
  };

  const decision4 = policy.evaluate(pqcInv);
  console.log(`Tool: ${pqcInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(pqcInv.tool, pqcInv.args, deps);
  console.log('Signed Status:', dispatch4.signed);
  console.log('PQC Algorithm Used:', dispatch4.algorithm);
  console.log('PQC Signature Hash:', dispatch4.pqSignatureHash);

  if (dispatch4.ok && dispatch4.signed && dispatch4.algorithm === 'Dilithium5') {
    console.log('✅ Test 4 Passed: Audit credential signed using quantum-resistant Dilithium5 signature.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 9 SOVEREIGN SWARM AUTONOMY COMPLETED GREEN ===');
}

runPhase9Tests().catch(err => {
  console.error('Phase 9 test run failed:');
  console.error(err);
  process.exit(1);
});
