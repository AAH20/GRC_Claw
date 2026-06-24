import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase13Tests() {
  console.log('=== GRC_Claw Phase 13: Sovereign Swarm Autonomy & Cognitive Alignment Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase13-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: DAO Policy Proposal
  // ----------------------------------------------------
  console.log('--- Test 1: DAO Policy Update Proposal ---');
  const proposalInv: ToolInvocation = {
    tool: 'consensus.propose_policy_update',
    args: { proposalId: 'prop-0x99fa2', targetRule: 'deny-outbound-webhooks' },
    agentRole: 'developer'
  };

  const decision1 = policy.evaluate(proposalInv);
  console.log(`Tool: ${proposalInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(proposalInv.tool, proposalInv.args, deps);
  console.log('Proposal Registered:', dispatch1.proposalId);
  console.log('Votes Needed:', dispatch1.votesNeeded);

  if (dispatch1.ok && dispatch1.proposalId && dispatch1.votesNeeded === 5) {
    console.log('✅ Test 1 Passed: Policy proposal registered successfully.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: DAO Voting Consensus
  // ----------------------------------------------------
  console.log('--- Test 2: DAO Policy Update Voting Quorum ---');
  const voteInv: ToolInvocation = {
    tool: 'consensus.vote_policy_update',
    args: { proposalId: 'prop-0x99fa2', voterDID: 'did:grc:operator-42' },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(voteInv);
  console.log(`Tool: ${voteInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(voteInv.tool, voteInv.args, deps);
  console.log('Voting Status:', dispatch2.status);
  console.log('Quorum Reached:', dispatch2.quorumReached);

  if (dispatch2.ok && dispatch2.quorumReached && dispatch2.voterDID === 'did:grc:operator-42') {
    console.log('✅ Test 2 Passed: Policy vote recorded and consensus quorum reached.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Analog Optoelectronic Airgap Actuation
  // ----------------------------------------------------
  console.log('--- Test 3: Optoelectronic Physical Airgap Actuation ---');
  const airgapInv: ToolInvocation = {
    tool: 'actuator.trigger_analog_airgap',
    args: { physicalPortId: 'opt-fiber-99' },
    agentRole: 'developer'
  };

  const decision3 = policy.evaluate(airgapInv, true);
  console.log(`Tool: ${airgapInv.tool}`);
  console.log(`Allowed (approvedDestructive): ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(airgapInv.tool, airgapInv.args, deps);
  console.log('Airgap Trigger Status:', dispatch3.status);
  console.log('Physical Port Isolated:', dispatch3.physicalPortId);

  if (dispatch3.ok && dispatch3.triggered && dispatch3.physicalPortId === 'opt-fiber-99') {
    console.log('✅ Test 3 Passed: Optoelectronic physical airgap successfully triggered.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Temporal Logic Model Checking Safety Invariant
  // ----------------------------------------------------
  console.log('--- Test 4: Temporal Safety Invariant Model Checking ---');
  const temporalInv: ToolInvocation = {
    tool: 'security.verify_temporal_invariants',
    args: { invariantFormula: 'G(read_pii -> ~F(outbound_webhook))' },
    agentRole: 'developer'
  };

  const decision4 = policy.evaluate(temporalInv);
  console.log(`Tool: ${temporalInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(temporalInv.tool, temporalInv.args, deps);
  console.log('Temporal Verification Status:', dispatch4.status);
  console.log('Temporal Safety Invariant Holds:', dispatch4.temporalSafetyInvariantHolds);

  if (dispatch4.ok && dispatch4.verified && dispatch4.temporalSafetyInvariantHolds) {
    console.log('✅ Test 4 Passed: Temporal safety invariant verified via model checker.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  // ----------------------------------------------------
  // TEST 5: Cognitive Synaptic Activation Patching
  // ----------------------------------------------------
  console.log('--- Test 5: Cognitive Synaptic Activation steering Hook ---');
  const steeringInv: ToolInvocation = {
    tool: 'sovereign.inject_activation_patch',
    args: { layerIndex: 24, patchMagnitude: 0.28 },
    agentRole: 'developer'
  };

  const decision5 = policy.evaluate(steeringInv);
  console.log(`Tool: ${steeringInv.tool}`);
  console.log(`Allowed: ${decision5.allowed}`);

  const dispatch5 = await dispatchBuiltinGrcTool(steeringInv.tool, steeringInv.args, deps);
  console.log('Steering Hook Status:', dispatch5.status);
  console.log('Steering Magnitude:', dispatch5.steeringVectorMagnitude);
  console.log('Modified Layer Count:', dispatch5.modifiedLayerCount);

  if (dispatch5.ok && dispatch5.patched && dispatch5.steeringVectorMagnitude === 0.28) {
    console.log('✅ Test 5 Passed: Synaptic activation patch successfully injected.\n');
  } else {
    throw new Error('❌ Test 5 Failed!');
  }

  console.log('=== ALL PHASE 13 SOVEREIGN SWARM AUTONOMY & ALIGNMENT TESTS COMPLETED GREEN ===');
}

runPhase13Tests().catch(err => {
  console.error('Phase 13 test run failed:');
  console.error(err);
  process.exit(1);
});
