import { ExecPolicy, AgentSession } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runSovereignComputeTest() {
  console.log('\x1b[36m=================================================================\x1b[0m');
  console.log('\x1b[36m   GRC_Claw Sovereign Airgapped Compute Compliance Test Suite     \x1b[0m');
  console.log('\x1b[36m=================================================================\x1b[0m\n');

  const policy = new ExecPolicy();
  const session = new AgentSession('sovereign-compute-session-999', policy);
  
  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({
    baseUrl: 'http://127.0.0.1:3000',
    apiKey: 'mock-key',
    tenantId: 1,
    mode: 'demo'
  });
  const deps = { evidence, a2z };

  // ----------------------------------------------------
  // TEST 1: Sovereign Airgapped Node (Flagship Blackwell + Vera CPU)
  // ----------------------------------------------------
  console.log('\x1b[35m--- Test Scenario 1: Compliant Sovereign Compute Node ---\x1b[0m');
  
  const compliantConfig = {
    hostCpu: 'Nvidia Vera ARM CPU',
    gpuHardware: 'Nvidia Blackwell GB200 NVL72',
    airgapStatus: 'FULLY_AIRGAPPED',
    modelWeightsSource: 'LOCAL_AUDITED_WEIGHTS',
    nemoGuardrailsActive: true
  };

  const decision1 = await session.invoke({
    tool: 'sovereign.verify_compute_boundary',
    args: compliantConfig,
    agentRole: 'reviewer'
  });

  console.log(`  Policy Gate Allowed: \x1b[32m${decision1.allowed}\x1b[0m`);
  
  const output1 = (await dispatchBuiltinGrcTool('sovereign.verify_compute_boundary', compliantConfig, deps)) as any;
  console.log(`  Harness Verification Result: status=\x1b[32m${output1.complianceStatus}\x1b[0m`);
  console.log(`  Hardware Audit: \x1b[32m${output1.hardwareAuditPassed ? 'PASSED' : 'FAILED'}\x1b[0m`);
  console.log(`  Airgap Audit: \x1b[32m${output1.airgapAuditPassed ? 'PASSED' : 'FAILED'}\x1b[0m`);
  console.log(`  Weights Audit: \x1b[32m${output1.weightsAuditPassed ? 'PASSED' : 'FAILED'}\x1b[0m`);
  console.log(`  NeMo Guardrails: \x1b[32m${output1.nemoGuardrailsPassed ? 'PASSED' : 'FAILED'}\x1b[0m`);
  console.log(`  Detected Issues Count: \x1b[32m${output1.issues.length}\x1b[0m\n`);

  if (decision1.allowed && output1.complianceStatus === 'COMPLIANT' && output1.issues.length === 0) {
    console.log('✅ Test Scenario 1 Passed: Sovereign local silicon config validated successfully.\n');
  } else {
    throw new Error('❌ Test Scenario 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Non-Sovereign Shared Cloud VM AI Node (EPYC + Cloud GPU Rental)
  // ----------------------------------------------------
  console.log('\x1b[35m--- Test Scenario 2: Non-Sovereign Cloud AI Rental Node ---\x1b[0m');
  
  const cloudRentalConfig = {
    hostCpu: 'AMD EPYC Node (Cloud VM)',
    gpuHardware: 'Cloud GPU Instance (Transient Shared)',
    airgapStatus: 'CONNECTED_TO_CLOUD',
    modelWeightsSource: 'CLOUD_API_RENTAL',
    nemoGuardrailsActive: false
  };

  const decision2 = await session.invoke({
    tool: 'sovereign.verify_compute_boundary',
    args: cloudRentalConfig,
    agentRole: 'reviewer'
  });

  console.log(`  Policy Gate Allowed: \x1b[32m${decision2.allowed}\x1b[0m`);
  
  const output2 = (await dispatchBuiltinGrcTool('sovereign.verify_compute_boundary', cloudRentalConfig, deps)) as any;
  console.log(`  Harness Verification Result: status=\x1b[31m${output2.complianceStatus}\x1b[0m`);
  console.log(`  Detected Issues:`);
  for (const issue of output2.issues) {
    console.log(`    - \x1b[31m${issue}\x1b[0m`);
  }
  console.log('');

  if (decision2.allowed && output2.complianceStatus === 'NON_COMPLIANT' && output2.issues.length === 5) {
    console.log('✅ Test Scenario 2 Passed: GRC_Claw successfully flagged and logged all cloud AI rental sovereignty gaps.\n');
  } else {
    throw new Error('❌ Test Scenario 2 Failed!');
  }

  console.log('\x1b[32m=================================================================\x1b[0m');
  console.log('\x1b[32m   All GRC_Claw Sovereign Airgapped Compute Tests PASSED!         \x1b[0m');
  console.log('\x1b[32m=================================================================\x1b[0m');
}

runSovereignComputeTest().catch((err) => {
  console.error('\x1b[31mSovereign Compute Test Failure:\x1b[0m', err);
  process.exit(1);
});
