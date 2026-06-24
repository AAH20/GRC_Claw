import {
  VectorGraphMemory,
  SkillsRegistry
} from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runTests() {
  console.log('=== RUNNING ACQUISITION-GRADE ENTERPRISE CONTROL TESTS ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });

  // ==========================================
  // Test 1: Vector Graph Memory Query
  // ==========================================
  console.log('--- Test 1: Vector Graph Query for eBPF, ZK Ledger, Enclave MPC, Drift, and Federated Intel ---');
  const vectorMemory = new VectorGraphMemory();
  
  const ebpfNodes = vectorMemory.query('eBPF Sandbox');
  console.log(`Matched eBPF nodes count: ${ebpfNodes.nodes.length}`);
  ebpfNodes.nodes.forEach(n => console.log(`- Node [${n.id}] (${n.type}): ${n.label}`));

  const zkLedgerNodes = vectorMemory.query('ZK Ledger');
  console.log(`Matched ZK Ledger nodes count: ${zkLedgerNodes.nodes.length}`);
  zkLedgerNodes.nodes.forEach(n => console.log(`- Node [${n.id}] (${n.type}): ${n.label}`));

  const enclaveNodes = vectorMemory.query('Enclave');
  console.log(`Matched Enclave nodes count: ${enclaveNodes.nodes.length}`);
  enclaveNodes.nodes.forEach(n => console.log(`- Node [${n.id}] (${n.type}): ${n.label}`));

  const driftNodes = vectorMemory.query('Drift');
  console.log(`Matched Drift nodes count: ${driftNodes.nodes.length}`);
  driftNodes.nodes.forEach(n => console.log(`- Node [${n.id}] (${n.type}): ${n.label}`));

  const federatedNodes = vectorMemory.query('Federated');
  console.log(`Matched Federated nodes count: ${federatedNodes.nodes.length}`);
  federatedNodes.nodes.forEach(n => console.log(`- Node [${n.id}] (${n.type}): ${n.label}`));
  console.log('');

  // ==========================================
  // Test 2: Skills Registry Query
  // ==========================================
  console.log('--- Test 2: Skills Registry Query for Playbooks ---');
  const skillsRegistry = new SkillsRegistry();
  
  const ebpfSkill = skillsRegistry.load('ebpf-sandbox-policy');
  console.log(`eBPF Skill loaded: ${!!ebpfSkill}`);
  if (ebpfSkill) console.log(`- Skill: ${ebpfSkill.name} (${ebpfSkill.category})`);

  const zkLedgerSkill = skillsRegistry.load('zk-audit-ledger');
  console.log(`ZK Ledger Skill loaded: ${!!zkLedgerSkill}`);
  if (zkLedgerSkill) console.log(`- Skill: ${zkLedgerSkill.name} (${zkLedgerSkill.category})`);

  const enclaveSkill = skillsRegistry.load('tee-enclave-mpc');
  console.log(`Enclave MPC Skill loaded: ${!!enclaveSkill}`);
  if (enclaveSkill) console.log(`- Skill: ${enclaveSkill.name} (${enclaveSkill.category})`);

  const driftSkill = skillsRegistry.load('iac-drift-correction');
  console.log(`Drift Skill loaded: ${!!driftSkill}`);
  if (driftSkill) console.log(`- Skill: ${driftSkill.name} (${driftSkill.category})`);

  const federatedSkill = skillsRegistry.load('federated-intel-exchange');
  console.log(`Federated Skill loaded: ${!!federatedSkill}`);
  if (federatedSkill) console.log(`- Skill: ${federatedSkill.name} (${federatedSkill.category})`);
  console.log('');

  // ==========================================
  // Test 3: eBPF Sandbox Rules Enforcement
  // ==========================================
  console.log('--- Test 3: Applying eBPF Kernel Sandbox Rules ---');
  const ebpfResult = await dispatchBuiltinGrcTool('security.ebpf_sandbox_rule', {
    processGroupId: 'sandbox-group-88',
    syscallDenylist: ['execve', 'socket', 'fork']
  }, { evidence, a2z });

  console.log('Attach Status:', ebpfResult.attachStatus);
  console.log('Active Hook Count:', ebpfResult.activeHookCount);
  if (ebpfResult.attachStatus !== 'ATTACHED' || ebpfResult.activeHookCount !== 5) {
    throw new Error('Test 3 Failed: expected ebpf rules to attach');
  }
  console.log('');

  // ==========================================
  // Test 4: ZK Audit Ledger Proof Generation
  // ==========================================
  console.log('--- Test 4: Generating Raft-based ZK Audit Ledger Proof ---');
  const zkResult = await dispatchBuiltinGrcTool('audit.generate_zk_ledger_proof', {
    raftSessionId: 'raft-session-x19',
    auditLogRootHash: '0x3a9b8c7d6e5f4a'
  }, { evidence, a2z });

  console.log('Ledger Status:', zkResult.ledgerStatus);
  console.log('ZK Proof Hash:', zkResult.zkProofHash);
  if (zkResult.ledgerStatus !== 'COMMITTED' || !zkResult.zkProofHash) {
    throw new Error('Test 4 Failed: expected ledger status to be COMMITTED');
  }
  console.log('');

  // ==========================================
  // Test 5: TEE Enclave MPC co-signing
  // ==========================================
  console.log('--- Test 5: Running TEE Enclave MPC Co-signing ---');
  const enclaveResult = await dispatchBuiltinGrcTool('mpc.sign_enclave_transaction', {
    txPayload: '{"send": "xrp-wallet-01", "amount": 100}',
    enclaveId: 'intel-sgx-enclave-99',
    minimumNodes: 4
  }, { evidence, a2z });

  console.log('Attestation Status:', enclaveResult.attestationStatus);
  console.log('Enclave Signature:', enclaveResult.enclaveSignature);
  if (enclaveResult.attestationStatus !== 'VERIFIED' || !enclaveResult.enclaveSignature) {
    throw new Error('Test 5 Failed: expected enclave MPC signature to verify');
  }
  console.log('');

  // ==========================================
  // Test 6: Closed-loop IaC Compliance Drift Correction
  // ==========================================
  console.log('--- Test 6: Executing Closed-loop IaC Compliance Drift Correction ---');
  const driftResult = await dispatchBuiltinGrcTool('grc.trigger_drift_correction', {
    targetTemplateUri: 'file:///opt/templates/secure_network.tf',
    activeConfigUri: 'file:///opt/active/network.tf'
  }, { evidence, a2z });

  console.log('Remediation Status:', driftResult.driftRemediationStatus);
  console.log('Remediated Controls:', driftResult.remediatedControlsCount);
  console.log('Applied Patch Hash:', driftResult.appliedPatchHash);
  if (driftResult.driftRemediationStatus !== 'SUCCESS' || driftResult.remediatedControlsCount !== 3) {
    throw new Error('Test 6 Failed: expected drift correction to remediate the configurations');
  }
  console.log('');

  // ==========================================
  // Test 7: Federated Threat Intel Sync with Differential Privacy
  // ==========================================
  console.log('--- Test 7: Syncing Federated Threat Intel with Differential Privacy ---');
  const intelResult = await dispatchBuiltinGrcTool('intel.sync_federated_reports', {
    localLogsJson: '{"anomaly": "reasoning_loop", "count": 25}',
    privacyEpsilon: 0.35
  }, { evidence, a2z });

  console.log('Noise Injected:', intelResult.noiseInjected);
  console.log('Peer Intel Count:', intelResult.peerIntelCount);
  console.log('Sanitized Report Hash:', intelResult.sanitizedReportHash);
  if (intelResult.noiseInjected !== true || !intelResult.sanitizedReportHash) {
    throw new Error('Test 7 Failed: expected differential privacy noise to be injected');
  }

  console.log('\n=== ALL ACQUISITION-GRADE CONTROL TESTS COMPLETED GREEN ===');
}

runTests().catch(err => {
  console.error('Test run failed:');
  console.error(err);
  process.exit(1);
});
