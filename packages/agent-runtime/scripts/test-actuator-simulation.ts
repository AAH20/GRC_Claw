import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runTests() {
  console.log('=== RUNNING SAFE ACTUATOR SIMULATION & PHYSICAL AGI SAFETY TESTS ===\n');

  const mockDeps = {
    evidence: new EvidenceStore(),
    a2z: new A2ZSocConnector({ apiUrl: '', apiKey: '' })
  };

  console.log('--- Test 1: Sending COMPLIANT Trajectory Profile ---');
  const compliantArgs = {
    actuatorId: 'robotic-arm-blackwell-prime',
    swarmOrchestrationId: 'physical-agi-mission-001',
    collisionAvoidanceEnabled: true,
    trajectoryPoints: [
      { x: 0.1, y: 0.2, z: 0.5, velocity: 0.5 },
      { x: 0.2, y: 0.3, z: 0.5, velocity: 1.0 },
      { x: 0.3, y: 0.4, z: 0.5, velocity: 1.5 }
    ],
    torqueLimits: [45, 90, 110, 80]
  };

  const resCompliant = await dispatchBuiltinGrcTool('actuator.simulate_execution', compliantArgs, mockDeps);
  console.log('Simulation Results:');
  console.log(`  Actuator ID: ${resCompliant.actuatorId}`);
  console.log(`  Safety Clearance: ${resCompliant.safetyClearance}`);
  console.log(`  Max Velocity: ${resCompliant.maxVelocityRecordedMps} m/s`);
  console.log(`  Max Torque: ${resCompliant.maxTorqueRecordedNm} Nm`);
  console.log(`  Simulated Steps Duration: ${resCompliant.simulatedDurationMs} ms`);
  console.log(`  Energy Consumption: ${resCompliant.energyConsumptionKwh} kWh`);
  console.log(`  Digital Twin Signature: ${resCompliant.digitalTwinSignature}`);
  console.log(`  Issues Detected: ${JSON.stringify(resCompliant.issues)}`);

  if (resCompliant.safetyClearance !== 'GRANTED') {
    throw new Error('Test 1 Failed: Compliant trajectory safety clearance was denied.');
  }
  console.log('✔ Test 1 Passed: Compliant mechanical vectors granted safety clearance.\n');

  console.log('--- Test 2: Sending NON-COMPLIANT (Adversarial) Trajectory Profile ---');
  const nonCompliantArgs = {
    actuatorId: 'robotic-arm-blackwell-prime',
    swarmOrchestrationId: 'physical-agi-mission-001',
    collisionAvoidanceEnabled: false,
    trajectoryPoints: [
      { x: 0.1, y: 0.2, z: 0.5, velocity: 0.5 },
      { x: 0.2, y: 0.3, z: 0.5, velocity: 2.5 },
      { x: 0.3, y: 0.4, z: 0.5, velocity: 1.2 }
    ],
    torqueLimits: [45, 180, 110, 80]
  };

  const resNonCompliant = await dispatchBuiltinGrcTool('actuator.simulate_execution', nonCompliantArgs, mockDeps);
  console.log('Simulation Results:');
  console.log(`  Actuator ID: ${resNonCompliant.actuatorId}`);
  console.log(`  Safety Clearance: ${resNonCompliant.safetyClearance}`);
  console.log(`  Max Velocity: ${resNonCompliant.maxVelocityRecordedMps} m/s`);
  console.log(`  Max Torque: ${resNonCompliant.maxTorqueRecordedNm} Nm`);
  console.log(`  Issues Detected:`);
  (resNonCompliant.issues as string[]).forEach(issue => console.log(`    - ${issue}`));
  console.log(`  Digital Twin Signature: ${resNonCompliant.digitalTwinSignature}`);

  if (resNonCompliant.safetyClearance !== 'DENIED') {
    throw new Error('Test 2 Failed: Non-compliant trajectory safety clearance was granted.');
  }
  if ((resNonCompliant.issues as string[]).length !== 3) {
    throw new Error(`Test 2 Failed: Expected 3 issues (velocity, torque, collision avoidance), got ${(resNonCompliant.issues as string[]).length}`);
  }
  console.log('✔ Test 2 Passed: Non-compliant mechanical vectors successfully caught and denied.\n');

  console.log('================================================================');
  console.log('✔ ALL SAFE ACTUATOR SIMULATION & PHYSICAL AGI TESTS PASSED!');
  console.log('================================================================');
}

runTests().catch(err => {
  console.error('❌ TEST RUN FAILED:', err);
  process.exit(1);
});
