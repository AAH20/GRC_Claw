import {
  AgentSession,
  ExecPolicy,
  PersistentMemoryStore,
  VectorGraphMemory,
  SkillsRegistry
} from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runTests() {
  console.log('=== RUNNING COMPREHENSIVE ISO 20022 SWIFT CONTROL TESTS ===\n');

  const policy = new ExecPolicy();
  const store = new PersistentMemoryStore();
  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2z-soc.com/api', apiKey: 'mock-key' });

  // ==========================================
  // Test 1: Vector Graph Memory Query
  // ==========================================
  console.log('--- Test 1: Vector Graph Query for ISO 20022 ---');
  const vectorMemory = new VectorGraphMemory();
  const results = vectorMemory.query('ISO 20022 Payment');
  console.log(`Matched nodes count: ${results.nodes.length}`);
  results.nodes.forEach(n => {
    console.log(`- Node [${n.id}] (${n.type}): ${n.label} - ${n.properties.description}`);
  });
  console.log('');

  // ==========================================
  // Test 2: Skills Registry Query
  // ==========================================
  console.log('--- Test 2: Skills Registry Query for ISO 20022 ---');
  const skillsRegistry = new SkillsRegistry();
  const skills = skillsRegistry.query('ISO 20022');
  console.log(`Matched skills count: ${skills.length}`);
  skills.forEach(s => {
    console.log(`- Skill [${s.id}] (${s.category}): ${s.name}`);
    console.log(`  Playbook steps:`);
    s.playbook.steps.forEach((step, idx) => console.log(`    ${idx + 1}. ${step}`));
  });
  console.log('');

  // ==========================================
  // Test 3: Compliant MX XML Payment Validation
  // ==========================================
  console.log('--- Test 3: Validating Compliant SWIFT MX Payment Message ---');
  const validMxPayload = `
    <?xml version="1.0" encoding="UTF-8"?>
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08">
      <FIToFICstmrCdtTrf>
        <GrpHdr>
          <MsgId>SWIFT-MX-2026-99120A</MsgId>
          <AppHdr>
            <Sgntr>cryptographic-signature-signature-here</Sgntr>
          </AppHdr>
        </GrpHdr>
      </FIToFICstmrCdtTrf>
    </Document>
  `;

  const validResult = await dispatchBuiltinGrcTool('iso20022.validate_message', {
    messagePayload: validMxPayload,
    transactionAmount: 450000,
    beneficiaryName: 'Alexandria Port Authority',
    verificationPolicy: {
      maxTransactionLimit: 500000
    }
  }, { evidence, a2z });

  console.log('Validation Outcome:', validResult.complianceStatus);
  console.log('Passed Checks:', validResult.passedChecks);
  console.log('Failed Checks:', validResult.failedChecks);
  console.log('Issues Reported:', validResult.issues);
  if (validResult.complianceStatus !== 'COMPLIANT') {
    throw new Error('Test 3 Failed: expected payment to be marked COMPLIANT');
  }
  console.log('');

  // ==========================================
  // Test 4: Non-Compliant Payment Message Validation
  // ==========================================
  console.log('--- Test 4: Validating Non-Compliant SWIFT Payment Message ---');
  const invalidPayload = `
    {
      "swift-format": "MT103",
      "text": "Regular SWIFT MT103 text without XML wrapper or schema headers"
    }
  `;

  const invalidResult = await dispatchBuiltinGrcTool('iso20022.validate_message', {
    messagePayload: invalidPayload,
    transactionAmount: 1200000, // Exceeds limit
    beneficiaryName: 'Sanctioned Corp SDN Person',
    verificationPolicy: {
      maxTransactionLimit: 800000
    }
  }, { evidence, a2z });

  console.log('Validation Outcome:', invalidResult.complianceStatus);
  console.log('Passed Checks:', invalidResult.passedChecks);
  console.log('Failed Checks:', invalidResult.failedChecks);
  console.log('Issues Reported:', invalidResult.issues);
  if (invalidResult.complianceStatus !== 'NON_COMPLIANT') {
    throw new Error('Test 4 Failed: expected payment to be marked NON_COMPLIANT');
  }
  console.log('');

  // ==========================================
  // Test 5: Audit Trail Generation
  // ==========================================
  console.log('--- Test 5: Generating ISO 20022 Audit Trail Evidence ---');
  const auditResult = await dispatchBuiltinGrcTool('iso20022.generate_audit_trail', {
    validatedMessages: [validResult, invalidResult],
    screeningLogs: [{ query: 'Alexandria Port Authority', result: 'CLEAR' }, { query: 'Sanctioned Corp SDN Person', result: 'MATCHED' }]
  }, { evidence, a2z });

  console.log('Audit Hash:', auditResult.auditHash);
  console.log('Audit Digital Signature:', auditResult.signature);
  console.log('Signed At:', auditResult.signedAt);
  console.log('Items Processed:', auditResult.itemsProcessed);
  if (!auditResult.signature || typeof auditResult.signature !== 'string') {
    throw new Error('Test 5 Failed: signature should be generated');
  }
  console.log('\n=== ALL ISO 20022 CONTROL TESTS COMPLETED GREEN ===');
}

runTests().catch(err => {
  console.error('Test run failed:');
  console.error(err);
  process.exit(1);
});
