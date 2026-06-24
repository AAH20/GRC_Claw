import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase18Tests() {
  console.log('=== GRC_Claw Phase 18: Structural Monopoly Architecture Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase18-test-session', policy);

  // TEST 1: WASM Policy Sandbox Spawning
  console.log('--- Test 1: WASM Policy Sandbox Spawning ---');
  const wasmSpawnInv: ToolInvocation = {
    tool: 'sandbox.spawn_wasm_policy_instance',
    args: { tenantId: 'tenant-navy-hq', policyVersion: 'v2.3' },
    agentRole: 'developer'
  };
  const dispatch1 = await dispatchBuiltinGrcTool(wasmSpawnInv.tool, wasmSpawnInv.args, deps);
  console.log('Status:', dispatch1.status);
  console.log('Isolation Level:', dispatch1.isolationLevel);
  console.log('Linear Memory Bytes:', dispatch1.linearMemoryBytes);
  if (dispatch1.ok && dispatch1.isolationLevel === 'PROCESS_ISOLATED' && dispatch1.linearMemoryBytes === 65536) {
    console.log('✅ Test 1 Passed: Ephemeral WASM sandbox spawned with process-level isolation.\n');
  } else { throw new Error('❌ Test 1 Failed!'); }

  // TEST 2: WASM Boundary Validation
  console.log('--- Test 2: WASM Boundary Validation ---');
  const wasmValidateInv: ToolInvocation = {
    tool: 'sandbox.validate_wasm_boundary',
    args: { instanceId: dispatch1.instanceId },
    agentRole: 'developer'
  };
  const dispatch2 = await dispatchBuiltinGrcTool(wasmValidateInv.tool, wasmValidateInv.args, deps);
  console.log('Status:', dispatch2.status);
  console.log('Cross-Tenant Access Attempts:', dispatch2.crossTenantAccessAttempts);
  if (dispatch2.ok && dispatch2.validated && dispatch2.crossTenantAccessAttempts === 0) {
    console.log('✅ Test 2 Passed: WASM boundary secure with zero cross-tenant access.\n');
  } else { throw new Error('❌ Test 2 Failed!'); }

  // TEST 3: Merkle DAG Evidence Notarization
  console.log('--- Test 3: Merkle DAG Evidence Notarization ---');
  const notarizeInv: ToolInvocation = {
    tool: 'evidence.notarize_merkle_dag',
    args: { controlId: 'AC.L2-3.1.13', evidencePayload: 'Remote access encryption verified via TLS 1.3 audit log' },
    agentRole: 'developer'
  };
  const dispatch3 = await dispatchBuiltinGrcTool(notarizeInv.tool, notarizeInv.args, deps);
  console.log('Status:', dispatch3.status);
  console.log('Content-Addressed CID:', dispatch3.cid);
  console.log('DAG Depth:', dispatch3.dagDepth);
  if (dispatch3.ok && dispatch3.notarized && dispatch3.cid.startsWith('bafy2bzace')) {
    console.log('✅ Test 3 Passed: Evidence notarized with content-addressed Merkle DAG CID.\n');
  } else { throw new Error('❌ Test 3 Failed!'); }

  // TEST 4: Merkle DAG Integrity Verification
  console.log('--- Test 4: Merkle DAG Integrity Verification ---');
  const verifyDagInv: ToolInvocation = {
    tool: 'evidence.verify_dag_integrity',
    args: { rootCid: 'bafy2bzaceroot000000aa' },
    agentRole: 'developer'
  };
  const dispatch4 = await dispatchBuiltinGrcTool(verifyDagInv.tool, verifyDagInv.args, deps);
  console.log('Status:', dispatch4.status);
  console.log('Nodes Verified:', dispatch4.nodesVerifiedCount);
  console.log('Tamper Detected:', dispatch4.tamperDetected);
  if (dispatch4.ok && dispatch4.verified && dispatch4.tamperDetected === false) {
    console.log('✅ Test 4 Passed: Full Merkle DAG integrity chain verified with zero tampering.\n');
  } else { throw new Error('❌ Test 4 Failed!'); }

  // TEST 5: GNN Behavioral Graph Embedding Score
  console.log('--- Test 5: GNN Behavioral Graph Embedding Scoring ---');
  const gnnScoreInv: ToolInvocation = {
    tool: 'security.score_behavioral_graph_embedding',
    args: { sessionId: 'phase18-test-session' },
    agentRole: 'developer'
  };
  const dispatch5 = await dispatchBuiltinGrcTool(gnnScoreInv.tool, gnnScoreInv.args, deps);
  console.log('Status:', dispatch5.status);
  console.log('Anomaly Score:', dispatch5.anomalyScore);
  console.log('Normal Distance (sigma):', dispatch5.normalDistanceSigma);
  if (dispatch5.ok && dispatch5.anomalyScore < 1.0 && dispatch5.normalDistanceSigma < 2.0) {
    console.log('✅ Test 5 Passed: Session behavioral embedding scored within normal distribution.\n');
  } else { throw new Error('❌ Test 5 Failed!'); }

  // TEST 6: GNN Behavioral Baseline Retraining
  console.log('--- Test 6: GNN Behavioral Baseline Retraining ---');
  const retrainInv: ToolInvocation = {
    tool: 'security.retrain_behavioral_baseline',
    args: { approvedSessionCount: 1200 },
    agentRole: 'developer'
  };
  const dispatch6 = await dispatchBuiltinGrcTool(retrainInv.tool, retrainInv.args, deps);
  console.log('Status:', dispatch6.status);
  console.log('Epochs Completed:', dispatch6.epochsCompleted);
  console.log('Model Version:', dispatch6.modelVersion);
  if (dispatch6.ok && dispatch6.retrained && dispatch6.baselineSamplesCount === 1200) {
    console.log('✅ Test 6 Passed: Behavioral GNN baseline retrained on approved sessions.\n');
  } else { throw new Error('❌ Test 6 Failed!'); }

  // TEST 7: Federated Compliance Credential Issuance
  console.log('--- Test 7: Federated Compliance Attestation Credential Issuance ---');
  const issueInv: ToolInvocation = {
    tool: 'attestation.issue_compliance_credential',
    args: { organizationDid: 'did:grc:org-a2z-soc', frameworkId: 'soc-2-type-ii', controlSubset: ['CC6.1', 'CC6.7', 'CC7.2'] },
    agentRole: 'developer'
  };
  const dispatch7 = await dispatchBuiltinGrcTool(issueInv.tool, issueInv.args, deps);
  console.log('Status:', dispatch7.status);
  console.log('Credential ID:', dispatch7.credentialId);
  console.log('ZK Proof Hash:', dispatch7.zkProofHash);
  if (dispatch7.ok && dispatch7.issued && dispatch7.credentialId.startsWith('vc-cac-')) {
    console.log('✅ Test 7 Passed: Compliance attestation credential issued with ZK proof.\n');
  } else { throw new Error('❌ Test 7 Failed!'); }

  // TEST 8: Vendor Credential Verification
  console.log('--- Test 8: Vendor Credential Verification ---');
  const verifyCredInv: ToolInvocation = {
    tool: 'attestation.verify_vendor_credential',
    args: { credentialId: dispatch7.credentialId, vendorDid: 'did:grc:vendor-acme-corp' },
    agentRole: 'developer'
  };
  const dispatch8 = await dispatchBuiltinGrcTool(verifyCredInv.tool, verifyCredInv.args, deps);
  console.log('Status:', dispatch8.status);
  console.log('ZK Proof Valid:', dispatch8.zkProofValid);
  console.log('Expiry Valid:', dispatch8.expiryValid);
  if (dispatch8.ok && dispatch8.verified && dispatch8.zkProofValid && dispatch8.expiryValid) {
    console.log('✅ Test 8 Passed: Vendor compliance credential cryptographically verified.\n');
  } else { throw new Error('❌ Test 8 Failed!'); }

  console.log('=== ALL PHASE 18 STRUCTURAL MONOPOLY ARCHITECTURE TESTS GREEN ===');
}

runPhase18Tests().catch(err => {
  console.error('Phase 18 test run failed:');
  console.error(err);
  process.exit(1);
});
