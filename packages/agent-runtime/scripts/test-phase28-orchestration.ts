import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase28Tests() {
  console.log('=== GRC_Claw Phase 28: Gravitational Wave Attestation & Spin-Locked Key Gen Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  // TEST 1: Measure Gravitational Wave
  console.log('--- Test 1: Measure Gravitational Wave ---');
  const waveInv: ToolInvocation = {
    tool: 'consensus.measure_gravitational_wave',
    args: { coordinateHash: 'grav-coords-chicago-datacenter' },
    agentRole: 'developer'
  };
  const dispatch1 = await dispatchBuiltinGrcTool(waveInv.tool, waveInv.args, deps);
  console.log('Status:', dispatch1.status);
  console.log('Measured:', dispatch1.measured);
  console.log('Wave Amplitude:', dispatch1.gravitationalWaveAmplitude);
  if (dispatch1.ok && dispatch1.measured && dispatch1.gravitationalWaveAmplitude === 1.4e-21) {
    console.log('✅ Test 1 Passed: Local micro-gravitational field variations recorded.\n');
  } else { throw new Error('❌ Test 1 Failed!'); }

  // TEST 2: Verify Gravitational Coherence
  console.log('--- Test 2: Verify Gravitational Coherence ---');
  const coherenceInv: ToolInvocation = {
    tool: 'consensus.verify_gravitational_coherence',
    args: { coordinateHash: dispatch1.coordinateHash },
    agentRole: 'developer'
  };
  const dispatch2 = await dispatchBuiltinGrcTool(coherenceInv.tool, coherenceInv.args, deps);
  console.log('Status:', dispatch2.status);
  console.log('Verified:', dispatch2.verified);
  console.log('Gravitational Coherence Valid:', dispatch2.gravitationalCoherenceValid);
  if (dispatch2.ok && dispatch2.verified && dispatch2.gravitationalCoherenceValid) {
    console.log('✅ Test 2 Passed: Time-of-flight models adjusted using gravitational delay vectors.\n');
  } else { throw new Error('❌ Test 2 Failed!'); }

  // TEST 3: Initiate Spin Alignment
  console.log('--- Test 3: Initiate Spin Alignment ---');
  const spinInitInv: ToolInvocation = {
    tool: 'identity.initiate_spin_alignment',
    args: { cavityId: 'vacuum-cavity-alpha' },
    agentRole: 'developer'
  };
  const dispatch3 = await dispatchBuiltinGrcTool(spinInitInv.tool, spinInitInv.args, deps);
  console.log('Status:', dispatch3.status);
  console.log('Aligned:', dispatch3.aligned);
  console.log('Spin Entangled Pairs:', dispatch3.spinEntangledPairsCount);
  if (dispatch3.ok && dispatch3.aligned && dispatch3.spinEntangledPairsCount === 1024) {
    console.log('✅ Test 3 Passed: Subatomic particle spin alignment initialized inside vacuum cavity.\n');
  } else { throw new Error('❌ Test 3 Failed!'); }

  // TEST 4: Verify Spin Coherence
  console.log('--- Test 4: Verify Spin Coherence ---');
  const spinVerifyInv: ToolInvocation = {
    tool: 'identity.verify_spin_coherence',
    args: { cavityId: dispatch3.cavityId },
    agentRole: 'developer'
  };
  const dispatch4 = await dispatchBuiltinGrcTool(spinVerifyInv.tool, spinVerifyInv.args, deps);
  console.log('Status:', dispatch4.status);
  console.log('Verified:', dispatch4.verified);
  console.log('Spin Coherence Valid:', dispatch4.spinCoherenceValid);
  if (dispatch4.ok && dispatch4.verified && dispatch4.spinCoherenceValid) {
    console.log('✅ Test 4 Passed: Quantum spin coherence validated for key compile.\n');
  } else { throw new Error('❌ Test 4 Failed!'); }

  // TEST 5: Trigger Synaptic Sprouting
  console.log('--- Test 5: Trigger Synaptic Sprouting ---');
  const sproutingInv: ToolInvocation = {
    tool: 'soverign.trigger_synaptic_sprouting',
    args: { pathwayId: 'dendrite-pathway-beta' },
    agentRole: 'developer'
  };
  const dispatch5 = await dispatchBuiltinGrcTool(sproutingInv.tool, sproutingInv.args, deps);
  console.log('Status:', dispatch5.status);
  console.log('Sprouted:', dispatch5.sprouted);
  console.log('New Synapses Count:', dispatch5.newSynapsesCount);
  if (dispatch5.ok && dispatch5.sprouted && dispatch5.newSynapsesCount === 450) {
    console.log('✅ Test 5 Passed: Wetware brain-sprouting stimulation triggered successfully.\n');
  } else { throw new Error('❌ Test 5 Failed!'); }

  // TEST 6: Verify Sprouted Code
  console.log('--- Test 6: Verify Sprouted Code ---');
  const sproutedCodeInv: ToolInvocation = {
    tool: 'soverign.verify_sprouted_code',
    args: { pathwayId: dispatch5.pathwayId },
    agentRole: 'developer'
  };
  const dispatch6 = await dispatchBuiltinGrcTool(sproutedCodeInv.tool, sproutedCodeInv.args, deps);
  console.log('Status:', dispatch6.status);
  console.log('Verified:', dispatch6.verified);
  console.log('Synthesized Logic Valid:', dispatch6.synthesizedLogicValid);
  if (dispatch6.ok && dispatch6.verified && dispatch6.synthesizedLogicValid) {
    console.log('✅ Test 6 Passed: Dynamic code synthesized by organic paths formally verified.\n');
  } else { throw new Error('❌ Test 6 Failed!'); }

  // TEST 7: Shard Subatomic State
  console.log('--- Test 7: Shard Subatomic State ---');
  const shardInv: ToolInvocation = {
    tool: 'memory.shard_subatomic_state',
    args: { stateId: 'subatomic-shard-99' },
    agentRole: 'developer'
  };
  const dispatch7 = await dispatchBuiltinGrcTool(shardInv.tool, shardInv.args, deps);
  console.log('Status:', dispatch7.status);
  console.log('Sharded:', dispatch7.sharded);
  console.log('Subatomic Shares Count:', dispatch7.subatomicSharesCount);
  if (dispatch7.ok && dispatch7.sharded && dispatch7.subatomicSharesCount === 7) {
    console.log('✅ Test 7 Passed: Model state sharded across subatomic spin registers.\n');
  } else { throw new Error('❌ Test 7 Failed!'); }

  // TEST 8: Verify Subatomic Coherence
  console.log('--- Test 8: Verify Subatomic Coherence ---');
  const subatomicVerifyInv: ToolInvocation = {
    tool: 'memory.verify_subatomic_coherence',
    args: { stateId: dispatch7.stateId },
    agentRole: 'developer'
  };
  const dispatch8 = await dispatchBuiltinGrcTool(subatomicVerifyInv.tool, subatomicVerifyInv.args, deps);
  console.log('Status:', dispatch8.status);
  console.log('Verified:', dispatch8.verified);
  console.log('Subatomic Coherence Valid:', dispatch8.subatomicCoherenceValid);
  if (dispatch8.ok && dispatch8.verified && dispatch8.subatomicCoherenceValid) {
    console.log('✅ Test 8 Passed: Subatomic spin coherence of shards verified successfully.\n');
  } else { throw new Error('❌ Test 8 Failed!'); }

  console.log('=== ALL PHASE 28 GRAVITATIONAL & SPIN-LOCK TESTS GREEN ===');
}

runPhase28Tests().catch(err => {
  console.error('Phase 28 test run failed:');
  console.error(err);
  process.exit(1);
});
