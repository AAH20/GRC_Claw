import { ExecPolicy, AgentSession } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runUasGovernanceTest() {
  console.log('=== GRC_Claw Tactical UAS & C-UAS Swarm Governance Test ===\n');

  const policy = new ExecPolicy();
  const session = new AgentSession('tactical-uas-session-001', policy);
  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({
    baseUrl: 'http://127.0.0.1:3000',
    apiKey: 'mock-key',
    tenantId: 1,
    mode: 'demo'
  });
  const deps = { evidence, a2z };

  // ----------------------------------------------------
  // SCENARIO 1: Compliant UAS Swarm Drone
  // ----------------------------------------------------
  console.log('--- Scenario 1: Auditing Compliant UAS Drone ---');
  const compliantTele = {
    droneId: 'UAV-ALPHA-01',
    telemetryStream: [
      { packetType: 'HEARTBEAT', signatureEnabled: true, flightMode: 'HOLD', firmwareHash: '0xPX4v1_14' },
      { packetType: 'GLOBAL_POSITION_INT', signatureEnabled: true, flightMode: 'MISSION', firmwareHash: '0xPX4v1_14' }
    ]
  };

  const decision1 = await session.invoke({
    tool: 'uas.validate_telemetry',
    args: compliantTele,
    agentRole: 'reviewer'
  });

  console.log(`  Policy Evaluation: Allowed=${decision1.allowed}, Sandbox=${decision1.sandbox}`);

  const output1 = (await dispatchBuiltinGrcTool('uas.validate_telemetry', compliantTele, deps)) as any;
  console.log(`  Harness Verification Result: status=${output1.complianceStatus}, packets=${output1.verifiedPacketsCount}`);
  console.log(`  Issues: ${JSON.stringify(output1.issues)}\n`);

  if (decision1.allowed && output1.complianceStatus === 'COMPLIANT' && output1.issues.length === 0) {
    console.log('✅ Scenario 1 Passed: Compliant UAS swarm verified successfully.\n');
  } else {
    throw new Error('❌ Scenario 1 Failed!');
  }

  // ----------------------------------------------------
  // SCENARIO 2: Non-Compliant UAS Drone (Signature Disabled & Anomaly)
  // ----------------------------------------------------
  console.log('--- Scenario 2: Auditing Non-Compliant UAS Drone ---');
  const rogueTele = {
    droneId: 'UAV-BETA-02',
    telemetryStream: [
      { packetType: 'HEARTBEAT', signatureEnabled: false, flightMode: 'HOLD', firmwareHash: '0xPX4v1_14' },
      { packetType: 'COMMAND_LONG', signatureEnabled: true, flightMode: 'UNAUTHORIZED_OFFBOARD', firmwareHash: '0xBAD_FIRMWARE' }
    ]
  };

  const decision2 = await session.invoke({
    tool: 'uas.validate_telemetry',
    args: rogueTele,
    agentRole: 'reviewer'
  });

  console.log(`  Policy Evaluation: Allowed=${decision2.allowed}, Sandbox=${decision2.sandbox}`);

  const output2 = (await dispatchBuiltinGrcTool('uas.validate_telemetry', rogueTele, deps)) as any;
  console.log(`  Harness Verification Result: status=${output2.complianceStatus}, packets=${output2.verifiedPacketsCount}`);
  console.log(`  Issues identified:`);
  for (const issue of output2.issues) {
    console.log(`    - ${issue}`);
  }
  console.log('');

  if (decision2.allowed && output2.complianceStatus === 'NON_COMPLIANT' && output2.issues.length === 3) {
    console.log('✅ Scenario 2 Passed: MAVLink signature absence and unauthorized flight overrides successfully caught.\n');
  } else {
    throw new Error('❌ Scenario 2 Failed!');
  }

  // ----------------------------------------------------
  // SCENARIO 3: Compliant C-UAS DEW Hardware Status
  // ----------------------------------------------------
  console.log('--- Scenario 3: Auditing Compliant C-UAS Directed Energy System ---');
  const compliantDew = {
    stationId: 'CUAS-EDGESIELD-01',
    jammingArrayActive: true,
    directedEnergyLimitKw: 45, // Under 50kW safety regulation limit
    rfScanSpanMhz: 2400
  };

  const decision3 = await session.invoke({
    tool: 'cuas.audit_hardware_status',
    args: compliantDew,
    agentRole: 'reviewer'
  });

  const output3 = (await dispatchBuiltinGrcTool('cuas.audit_hardware_status', compliantDew, deps)) as any;
  console.log(`  Harness Verification Result: status=${output3.complianceStatus}, DEW Safe Status=${output3.dewSafeStatus}, RF Spectrum=${output3.rfSpectrumStatus}\n`);

  if (decision3.allowed && output3.complianceStatus === 'COMPLIANT' && output3.dewSafeStatus === 'SAFE') {
    console.log('✅ Scenario 3 Passed: Safe C-UAS hardware parameters confirmed.\n');
  } else {
    throw new Error('❌ Scenario 3 Failed!');
  }

  // ----------------------------------------------------
  // SCENARIO 4: Non-Compliant C-UAS DEW Hardware Status (Safety Limit Exceeded)
  // ----------------------------------------------------
  console.log('--- Scenario 4: Auditing Non-Compliant C-UAS Directed Energy System ---');
  const overlimitDew = {
    stationId: 'CUAS-EDGESIELD-02',
    jammingArrayActive: true,
    directedEnergyLimitKw: 85, // Exceeds 50kW safety regulation limit
    rfScanSpanMhz: 7200 // Out of band range
  };

  const decision4 = await session.invoke({
    tool: 'cuas.audit_hardware_status',
    args: overlimitDew,
    agentRole: 'reviewer'
  });

  const output4 = (await dispatchBuiltinGrcTool('cuas.audit_hardware_status', overlimitDew, deps)) as any;
  console.log(`  Harness Verification Result: status=${output4.complianceStatus}, DEW Safe Status=${output4.dewSafeStatus}, RF Spectrum=${output4.rfSpectrumStatus}`);
  console.log(`  Toxicity Level: ${session.getToxicityScore()}`);
  console.log(`  Anomalies: ${JSON.stringify(decision4.anomaliesDetected)}\n`);

  if (decision4.allowed && output4.complianceStatus === 'NON_COMPLIANT' && output4.dewSafeStatus === 'EXCEEDED' && output4.rfSpectrumStatus === 'UNAUTHORIZED') {
    console.log('✅ Scenario 4 Passed: DEW power level warning and RF spectrum violations detected and flagged.\n');
  } else {
    throw new Error('❌ Scenario 4 Failed!');
  }

  console.log('=== All Tactical UAS & C-UAS Swarm Governance tests completed successfully! ===');
}

runUasGovernanceTest().catch((err) => {
  console.error(err);
  process.exit(1);
});
