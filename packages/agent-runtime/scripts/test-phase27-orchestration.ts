import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase27Tests() {
  console.log('=== GRC_Claw Phase 27: Relativistic Space-Time & Silicon Substrate Self-Destruct Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  // TEST 1: Assert Spacetime Boundary
  console.log('--- Test 1: Assert Spacetime Boundary ---');
  const spacetimeInv: ToolInvocation = {
    tool: 'consensus.assert_spacetime_boundary',
    args: { coordinateHash: 'spacetime-coords-nyc-datacenter' },
    agentRole: 'developer'
  };
  const dispatch1 = await dispatchBuiltinGrcTool(spacetimeInv.tool, spacetimeInv.args, deps);
  console.log('Status:', dispatch1.status);
  console.log('Boundary Asserted:', dispatch1.boundaryAsserted);
  console.log('Propagation Delay Vector (ms):', dispatch1.propagationDelayVectorMs);
  if (dispatch1.ok && dispatch1.boundaryAsserted && dispatch1.propagationDelayVectorMs === 12.8) {
    console.log('✅ Test 1 Passed: Speed-of-light coordinate boundaries asserted in consensus.\n');
  } else { throw new Error('❌ Test 1 Failed!'); }

  // TEST 2: Verify Relativistic Proof
  console.log('--- Test 2: Verify Relativistic Proof ---');
  const verifyRelativisticInv: ToolInvocation = {
    tool: 'consensus.verify_relativistic_proof',
    args: { coordinateHash: dispatch1.coordinateHash },
    agentRole: 'developer'
  };
  const dispatch2 = await dispatchBuiltinGrcTool(verifyRelativisticInv.tool, verifyRelativisticInv.args, deps);
  console.log('Status:', dispatch2.status);
  console.log('Verified:', dispatch2.verified);
  console.log('Relativistic Time Sync Valid:', dispatch2.relativisticTimeSyncValid);
  if (dispatch2.ok && dispatch2.verified && dispatch2.relativisticTimeSyncValid) {
    console.log('✅ Test 2 Passed: Time-of-flight relativistic coordinate proof verified.\n');
  } else { throw new Error('❌ Test 2 Failed!'); }

  // TEST 3: Arm Substrate Triggers
  console.log('--- Test 3: Arm Substrate Triggers ---');
  const armTriggersInv: ToolInvocation = {
    tool: 'security.arm_substrate_triggers',
    args: { triggerId: 'tamper-destruct-unit-1' },
    agentRole: 'developer'
  };
  const dispatch3 = await dispatchBuiltinGrcTool(armTriggersInv.tool, armTriggersInv.args, deps);
  console.log('Status:', dispatch3.status);
  console.log('Armed:', dispatch3.armed);
  console.log('Tamper Sensor State:', dispatch3.tamperSensorState);
  if (dispatch3.ok && dispatch3.armed && dispatch3.tamperSensorState === 'HEALTHY') {
    console.log('✅ Test 3 Passed: Physical silicon self-destruct circuits armed successfully.\n');
  } else { throw new Error('❌ Test 3 Failed!'); }

  // TEST 4: Query Trigger Integrity
  console.log('--- Test 4: Query Trigger Integrity ---');
  const queryIntegrityInv: ToolInvocation = {
    tool: 'security.query_trigger_integrity',
    args: { triggerId: dispatch3.triggerId },
    agentRole: 'developer'
  };
  const dispatch4 = await dispatchBuiltinGrcTool(queryIntegrityInv.tool, queryIntegrityInv.args, deps);
  console.log('Status:', dispatch4.status);
  console.log('Sensor Status:', dispatch4.sensorStatus);
  console.log('Voltage Level (V):', dispatch4.voltageLevelVolts);
  if (dispatch4.ok && dispatch4.sensorStatus === 'ACTIVE_NO_TAMPER' && dispatch4.voltageLevelVolts > 1.0) {
    console.log('✅ Test 4 Passed: Anti-tamper trigger sensor health queried successfully.\n');
  } else { throw new Error('❌ Test 4 Failed!'); }

  // TEST 5: Stimulate Epigenetic State
  console.log('--- Test 5: Stimulate Epigenetic State ---');
  const stimulateInv: ToolInvocation = {
    tool: 'consensus.stimulate_epigenetic_state',
    args: { stimulusId: 'chemical-signal-v3' },
    agentRole: 'developer'
  };
  const dispatch5 = await dispatchBuiltinGrcTool(stimulateInv.tool, stimulateInv.args, deps);
  console.log('Status:', dispatch5.status);
  console.log('Stimulated:', dispatch5.stimulated);
  console.log('Target Cell Line:', dispatch5.targetCellLine);
  if (dispatch5.ok && dispatch5.stimulated && dispatch5.targetCellLine === 'HEK293-EPIGENETIC-01') {
    console.log('✅ Test 5 Passed: Biological methylation stimulus dispatched successfully.\n');
  } else { throw new Error('❌ Test 5 Failed!'); }

  // TEST 6: Sequence Epigenetic Signature
  console.log('--- Test 6: Sequence Epigenetic Signature ---');
  const sequenceInv: ToolInvocation = {
    tool: 'consensus.sequence_epigenetic_signature',
    args: { stimulusId: dispatch5.stimulusId },
    agentRole: 'developer'
  };
  const dispatch6 = await dispatchBuiltinGrcTool(sequenceInv.tool, sequenceInv.args, deps);
  console.log('Status:', dispatch6.status);
  console.log('Sequenced:', dispatch6.sequenced);
  console.log('Methylation Pattern Hash:', dispatch6.methylationPatternHash);
  if (dispatch6.ok && dispatch6.sequenced && String(dispatch6.methylationPatternHash).startsWith('0x')) {
    console.log('✅ Test 6 Passed: Mutating epigenetic cellular state sequenced successfully.\n');
  } else { throw new Error('❌ Test 6 Failed!'); }

  // TEST 7: Crystallize Epigenetic Code
  console.log('--- Test 7: Crystallize Epigenetic Code ---');
  const crystallizeInv: ToolInvocation = {
    tool: 'memory.crystallize_epigenetic_code',
    args: { codeId: 'epigenetic-code-99' },
    agentRole: 'developer'
  };
  const dispatch7 = await dispatchBuiltinGrcTool(crystallizeInv.tool, crystallizeInv.args, deps);
  console.log('Status:', dispatch7.status);
  console.log('Crystallized:', dispatch7.crystallized);
  console.log('Photonic Signature Hex:', dispatch7.photonicSignatureHex);
  if (dispatch7.ok && dispatch7.crystallized && dispatch7.photonicSignatureHex === '0xlaser_epigenetic_88ef') {
    console.log('✅ Test 7 Passed: Epigenetic key-state signatures locked into optical storage.\n');
  } else { throw new Error('❌ Test 7 Failed!'); }

  // TEST 8: Read Epigenetic Code
  console.log('--- Test 8: Read Epigenetic Code ---');
  const readInv: ToolInvocation = {
    tool: 'memory.read_epigenetic_code',
    args: { codeId: dispatch7.codeId },
    agentRole: 'developer'
  };
  const dispatch8 = await dispatchBuiltinGrcTool(readInv.tool, readInv.args, deps);
  console.log('Status:', dispatch8.status);
  console.log('Decoded:', dispatch8.decoded);
  console.log('Epigenetic State Restored:', dispatch8.epigeneticStateRestored);
  if (dispatch8.ok && dispatch8.decoded && dispatch8.epigeneticStateRestored) {
    console.log('✅ Test 8 Passed: Crystallized epigenetic signatures read and decoded successfully.\n');
  } else { throw new Error('❌ Test 8 Failed!'); }

  console.log('=== ALL PHASE 27 SPACETIME & SELF-DESTRUCT TESTS GREEN ===');
}

runPhase27Tests().catch(err => {
  console.error('Phase 27 test run failed:');
  console.error(err);
  process.exit(1);
});
