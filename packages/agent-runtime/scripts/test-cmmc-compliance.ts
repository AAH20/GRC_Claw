import { ExecPolicy, AgentSession } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runCmmcComplianceTest() {
  console.log('=== GRC_Claw CMMC 2.0 & NIST SP 800-171 Compliance Test ===\n');

  const policy = new ExecPolicy();
  const session = new AgentSession('cmmc-compliance-session-001', policy);
  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({
    baseUrl: 'http://127.0.0.1:3000',
    apiKey: 'mock-key',
    tenantId: 1,
    mode: 'demo'
  });
  const deps = { evidence, a2z };

  // ----------------------------------------------------
  // TEST 1: Compliant CMMC Level 2 Boundary Configuration
  // ----------------------------------------------------
  console.log('--- Test 1: Auditing Compliant CMMC Level 2 Boundary ---');
  const compliantBaseline = {
    systemBaseline: {
      mfaEnabled: true,
      sessionTimeoutSeconds: 600, // 10 minutes (<= 15 minutes limit)
      remoteAccessEncrypted: true,
      auditLogsForwarded: true
    }
  };

  const decision1 = await session.invoke({
    tool: 'cmmc.validate_system_boundary',
    args: compliantBaseline,
    agentRole: 'reviewer'
  });

  console.log(`  Policy Evaluation: Allowed=${decision1.allowed}, Sandbox=${decision1.sandbox}`);

  const output1 = (await dispatchBuiltinGrcTool('cmmc.validate_system_boundary', compliantBaseline, deps)) as any;
  console.log(`  Harness Verification Result: status=${output1.complianceStatus}`);
  console.log(`  Passed Controls:`);
  for (const ctrl of output1.passedControls) {
    console.log(`    - ${ctrl}`);
  }
  console.log('');

  if (decision1.allowed && output1.complianceStatus === 'COMPLIANT' && output1.failedControls.length === 0) {
    console.log('✅ Test 1 Passed: Compliant CMMC boundary validated successfully.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Non-Compliant Gaps (Failing MFA & Session Timeouts)
  // ----------------------------------------------------
  console.log('--- Test 2: Auditing Non-Compliant CMMC Level 2 Gaps ---');
  const gapBaseline = {
    systemBaseline: {
      mfaEnabled: false,
      sessionTimeoutSeconds: 1800, // 30 minutes (violates 15m timeout rule)
      remoteAccessEncrypted: false,
      auditLogsForwarded: true
    }
  };

  const decision2 = await session.invoke({
    tool: 'cmmc.validate_system_boundary',
    args: gapBaseline,
    agentRole: 'reviewer'
  });

  const output2 = (await dispatchBuiltinGrcTool('cmmc.validate_system_boundary', gapBaseline, deps)) as any;
  console.log(`  Harness Verification Result: status=${output2.complianceStatus}`);
  console.log(`  Failed Controls (Non-Compliance Gaps):`);
  for (const ctrl of output2.failedControls) {
    console.log(`    - ${ctrl}`);
  }
  console.log('');

  if (decision2.allowed && output2.complianceStatus === 'NON_COMPLIANT' && output2.failedControls.length === 3) {
    console.log('✅ Test 2 Passed: CMMC/NIST SP 800-171 gaps successfully detected.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Generate Signed Compliance Audit Evidence
  // ----------------------------------------------------
  console.log('--- Test 3: Generating Cryptographically Signed C3PAO Evidence ---');
  const evidencePayload = {
    sessionLogs: [
      { sessionId: 'session-abc-123', actionsCount: 8 },
      { sessionId: 'session-xyz-456', actionsCount: 12 }
    ],
    sodViolations: [
      { ruleName: 'Dev-Review SoD Conflict', timestamp: new Date().toISOString() }
    ]
  };

  const decision3 = await session.invoke({
    tool: 'cmmc.generate_audit_evidence',
    args: evidencePayload,
    idempotencyKey: 'idem-cmmc-ev-999',
    agentRole: 'reviewer'
  });

  const output3 = (await dispatchBuiltinGrcTool('cmmc.generate_audit_evidence', evidencePayload, deps)) as any;
  console.log(`  Policy Evaluation: Allowed=${decision3.allowed}`);
  console.log(`  Evidence Generated:`);
  console.log(`    - Root Hash: ${output3.evidenceHash}`);
  console.log(`    - Signature: ${output3.signature}`);
  console.log(`    - Signed At: ${output3.signedAt}`);
  console.log(`    - Total items hashed: ${output3.itemsHashed}\n`);

  if (decision3.allowed && output3.ok && output3.evidenceHash && output3.signature) {
    console.log('✅ Test 3 Passed: Signed audit evidence package generated successfully.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  console.log('=== All GRC_Claw CMMC 2.0 & NIST SP 800-171 Compliance tests completed successfully! ===');
}

runCmmcComplianceTest().catch((err) => {
  console.error(err);
  process.exit(1);
});
