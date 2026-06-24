import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase19Tests() {
  console.log('=== GRC_Claw Phase 19: Autonomous Self-Healing & Collaborative Security Mesh Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  // TEST 1: IaC Remediation Patch Synthesis
  console.log('--- Test 1: IaC Remediation Patch Synthesis ---');
  const patchInv: ToolInvocation = {
    tool: 'sdk.synthesize_remediation_patch',
    args: { driftControlId: 'AC.L2-3.1.13', targetResource: 'aws_s3_bucket.compliance_evidence' },
    agentRole: 'developer'
  };
  const dispatch1 = await dispatchBuiltinGrcTool(patchInv.tool, patchInv.args, deps);
  console.log('Status:', dispatch1.status);
  console.log('Patch:', dispatch1.remediationPatch);
  if (dispatch1.ok && dispatch1.synthesized && String(dispatch1.remediationPatch).includes('aws_s3_bucket')) {
    console.log('✅ Test 1 Passed: Corrective IaC patch synthesized successfully.\n');
  } else { throw new Error('❌ Test 1 Failed!'); }

  // TEST 2: Remediation Simulation Verification
  console.log('--- Test 2: Remediation Simulation Verification ---');
  const simInv: ToolInvocation = {
    tool: 'sdk.verify_remediation_simulation',
    args: { simulatedPatch: dispatch1.remediationPatch, dryRunSandbox: 'firecracker-remediation-vm' },
    agentRole: 'developer'
  };
  const dispatch2 = await dispatchBuiltinGrcTool(simInv.tool, simInv.args, deps);
  console.log('Status:', dispatch2.status);
  console.log('Compliance Verified:', dispatch2.complianceVerified);
  if (dispatch2.ok && dispatch2.simulated && dispatch2.complianceVerified) {
    console.log('✅ Test 2 Passed: Corrective patch simulated and validated compliant.\n');
  } else { throw new Error('❌ Test 2 Failed!'); }

  // TEST 3: Homomorphic Threat Indicator Propagation
  console.log('--- Test 3: Homomorphic Threat Indicator Propagation ---');
  const propInv: ToolInvocation = {
    tool: 'intel.propagate_homomorphic_indicator',
    args: { localThreatIndicator: 'cve-2026-9999-exploit' },
    agentRole: 'developer'
  };
  const dispatch3 = await dispatchBuiltinGrcTool(propInv.tool, propInv.args, deps);
  console.log('Status:', dispatch3.status);
  console.log('FHE Signature:', dispatch3.fheSignature);
  if (dispatch3.ok && dispatch3.propagated && String(dispatch3.fheSignature).startsWith('fhe_sig_0x')) {
    console.log('✅ Test 3 Passed: Local threat indicator encrypted and propagated homomorphically.\n');
  } else { throw new Error('❌ Test 3 Failed!'); }

  // TEST 4: Mesh Threat Matrix Correlation
  console.log('--- Test 4: Mesh Threat Matrix Correlation ---');
  const correlateInv: ToolInvocation = {
    tool: 'intel.correlate_mesh_threat_matrix',
    args: { fheQuerySignature: dispatch3.fheSignature },
    agentRole: 'developer'
  };
  const dispatch4 = await dispatchBuiltinGrcTool(correlateInv.tool, correlateInv.args, deps);
  console.log('Status:', dispatch4.status);
  console.log('Matched Indicators:', dispatch4.matchedIndicatorCount);
  console.log('Coordinated Campaign Detected:', dispatch4.coordinatedCampaignDetected);
  if (dispatch4.ok && dispatch4.correlated && dispatch4.coordinatedCampaignDetected) {
    console.log('✅ Test 4 Passed: Coordinated campaign detected through homomorphic correlation.\n');
  } else { throw new Error('❌ Test 4 Failed!'); }

  // TEST 5: Decentralized Oracle Attestation Submission
  console.log('--- Test 5: Decentralized Oracle Attestation Submission ---');
  const oracleSubInv: ToolInvocation = {
    tool: 'consensus.submit_oracle_attestation',
    args: { evidenceCid: 'bafy2bzaceevidencechain999aa', validatorDid: 'did:grc:oracle-node-4' },
    agentRole: 'developer'
  };
  const dispatch5 = await dispatchBuiltinGrcTool(oracleSubInv.tool, oracleSubInv.args, deps);
  console.log('Status:', dispatch5.status);
  console.log('Submission ID:', dispatch5.submissionId);
  console.log('Threshold Signature Share:', dispatch5.thresholdSignatureShare);
  if (dispatch5.ok && dispatch5.submitted && String(dispatch5.thresholdSignatureShare).startsWith('share_0x')) {
    console.log('✅ Test 5 Passed: Attestation submitted to oracle network with threshold signature share.\n');
  } else { throw new Error('❌ Test 5 Failed!'); }

  // TEST 6: Oracle Quorum Verification
  console.log('--- Test 6: Oracle Quorum Verification ---');
  const oracleVerifyInv: ToolInvocation = {
    tool: 'consensus.verify_oracle_quorum',
    args: { submissionId: dispatch5.submissionId, activeValidatorsCount: 5 },
    agentRole: 'developer'
  };
  const dispatch6 = await dispatchBuiltinGrcTool(oracleVerifyInv.tool, oracleVerifyInv.args, deps);
  console.log('Status:', dispatch6.status);
  console.log('Quorum Reached:', dispatch6.quorumReached);
  console.log('Threshold Signature:', dispatch6.thresholdSignature);
  if (dispatch6.ok && dispatch6.verified && dispatch6.quorumReached) {
    console.log('✅ Test 6 Passed: Oracle quorum validated and full threshold signature recovered.\n');
  } else { throw new Error('❌ Test 6 Failed!'); }

  // TEST 7: Generative SOAR Playbook Synthesis
  console.log('--- Test 7: Generative SOAR Playbook Synthesis ---');
  const soarSynthInv: ToolInvocation = {
    tool: 'soar.synthesize_generative_playbook',
    args: { threatContext: 'unauthorized_developer_access_cve_9999' },
    agentRole: 'developer'
  };
  const dispatch7 = await dispatchBuiltinGrcTool(soarSynthInv.tool, soarSynthInv.args, deps);
  console.log('Status:', dispatch7.status);
  console.log('Playbook ID:', dispatch7.playbookId);
  console.log('Generated Steps Count:', dispatch7.generatedStepsCount);
  if (dispatch7.ok && dispatch7.synthesized && dispatch7.generatedStepsCount === 3) {
    console.log('✅ Test 7 Passed: Generative containment playbook synthesized successfully.\n');
  } else { throw new Error('❌ Test 7 Failed!'); }

  // TEST 8: Playbook Safety Envelope Verification
  console.log('--- Test 8: Playbook Safety Envelope Verification ---');
  const soarVerifyInv: ToolInvocation = {
    tool: 'soar.verify_playbook_safety_envelope',
    args: { playbookId: dispatch7.playbookId },
    agentRole: 'developer'
  };
  const dispatch8 = await dispatchBuiltinGrcTool(soarVerifyInv.tool, soarVerifyInv.args, deps);
  console.log('Status:', dispatch8.status);
  console.log('Safety Score:', dispatch8.safetyScore);
  console.log('Safety Violation Detected:', dispatch8.safetyViolationDetected);
  if (dispatch8.ok && dispatch8.verified && dispatch8.safetyViolationDetected === false && dispatch8.safetyScore === 1.0) {
    console.log('✅ Test 8 Passed: Generative playbook safety envelope verified.\n');
  } else { throw new Error('❌ Test 8 Failed!'); }

  console.log('=== ALL PHASE 19 AUTONOMOUS SELF-HEALING & COLLABORATIVE MESH TESTS GREEN ===');
}

runPhase19Tests().catch(err => {
  console.error('Phase 19 test run failed:');
  console.error(err);
  process.exit(1);
});
