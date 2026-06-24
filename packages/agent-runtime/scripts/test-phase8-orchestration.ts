import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase8Tests() {
  console.log('=== GRC_Claw Phase 8: Sovereign Swarm Resilience & Cognitive Mediation Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase8-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: Tiered Semantic Approval Delegation
  // ----------------------------------------------------
  console.log('--- Test 1: Tiered Semantic Approval Delegation ---');
  const approvalInv: ToolInvocation = {
    tool: 'security.evaluate_semantic_approval',
    args: { intentPayload: 'Request to rotate developer SSH credentials', thresholdRisk: 0.8 },
    agentRole: 'developer'
  };

  const decision1 = policy.evaluate(approvalInv);
  console.log(`Tool: ${approvalInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(approvalInv.tool, approvalInv.args, deps);
  console.log('Approved:', dispatch1.approved);
  console.log('Delegation Tier:', dispatch1.delegationTier);
  console.log('Required Approvers Count:', dispatch1.requiredApproversCount);
  console.log('Confidence Score:', dispatch1.confidenceScore);

  if (dispatch1.ok && dispatch1.approved === false && dispatch1.delegationTier === 'QUORUM') {
    console.log('✅ Test 1 Passed: Tiered semantic approval correctly routed high-risk requests to multi-operator quorum.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Distributed Semantic Lock Manager (DSLM)
  // ----------------------------------------------------
  console.log('--- Test 2: Distributed Semantic Lock Manager (DSLM) ---');
  const acquireInv: ToolInvocation = {
    tool: 'sovereign.acquire_semantic_lock',
    args: { resourceUri: 'urn:grc:aws:vpc-firewall', leaseDurationMs: 10000, requesterDid: 'did:grc:agent-01' },
    agentRole: 'developer'
  };

  const dispatch2Acquire = await dispatchBuiltinGrcTool(acquireInv.tool, acquireInv.args, deps);
  console.log('Lock Acquired:', dispatch2Acquire.lockAcquired);
  console.log('Lock Token:', dispatch2Acquire.lockToken);
  console.log('Lease Expires At:', dispatch2Acquire.leaseExpiresAt);

  const releaseInv: ToolInvocation = {
    tool: 'sovereign.release_semantic_lock',
    args: { resourceUri: 'urn:grc:aws:vpc-firewall', lockToken: dispatch2Acquire.lockToken },
    agentRole: 'developer'
  };

  const dispatch2Release = await dispatchBuiltinGrcTool(releaseInv.tool, releaseInv.args, deps);
  console.log('Lock Released:', dispatch2Release.lockReleased);

  if (dispatch2Acquire.ok && dispatch2Acquire.lockAcquired && dispatch2Release.ok && dispatch2Release.lockReleased) {
    console.log('✅ Test 2 Passed: Distributed semantic lease acquired and released successfully.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Cascading Poison Isolation & Rollback
  // ----------------------------------------------------
  console.log('--- Test 3: Cascading Poison Isolation & Rollback ---');
  const rollbackInv: ToolInvocation = {
    tool: 'security.rollback_poison_cascade',
    args: { sourceAgentDid: 'did:grc:agent-compromised-03', infectionWindowSec: 120 },
    agentRole: 'reviewer',
    idempotencyKey: 'idem-rb-pc-1'
  };

  const decision3 = policy.evaluate(rollbackInv);
  console.log(`Tool: ${rollbackInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);
  console.log(`Requires Approval: ${decision3.requiresApproval}`);

  const dispatch3 = await dispatchBuiltinGrcTool(rollbackInv.tool, rollbackInv.args, deps);
  console.log('Poison Cascade Rollback Status:', dispatch3.status);
  console.log('Cascade Traced Count:', dispatch3.cascadeTracedCount);
  console.log('Quarantined Agent DIDs:', dispatch3.quarantinedAgentDids);
  console.log('Rollbacked Snapshots Count:', dispatch3.rollbackedSnapshotsCount);

  if (dispatch3.ok && dispatch3.status === 'ISOLATED_ROLLBACK_COMPLETE' && dispatch3.rollbackedSnapshotsCount === 3) {
    console.log('✅ Test 3 Passed: Cascading prompt-injection traced, and compromised nodes successfully rolled back.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Hierarchical Context Compression
  // ----------------------------------------------------
  console.log('--- Test 4: Hierarchical Context Compression ---');
  const compressInv: ToolInvocation = {
    tool: 'memory.compress_context_diff',
    args: { rawContextLogs: ['agent-thought: check config', 'tool-call: read-file', 'agent-thought: evaluate safety'], targetCompressionRatio: 0.3 },
    agentRole: 'developer'
  };

  const decision4 = policy.evaluate(compressInv);
  console.log(`Tool: ${compressInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(compressInv.tool, compressInv.args, deps);
  console.log('Compressed Diff JSON:', dispatch4.compressedDiffJson);
  console.log('Compression Ratio:', dispatch4.compressionRatio);
  console.log('Token Savings Count:', dispatch4.tokenSavingsCount);

  if (dispatch4.ok && dispatch4.tokenSavingsCount > 0 && dispatch4.compressedDiffJson) {
    console.log('✅ Test 4 Passed: Context log history abstracted into compressed state diffs.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 8 SOVEREIGN SWARM RESILIENCE COMPLETED GREEN ===');
}

runPhase8Tests().catch(err => {
  console.error('Phase 8 test run failed:');
  console.error(err);
  process.exit(1);
});
