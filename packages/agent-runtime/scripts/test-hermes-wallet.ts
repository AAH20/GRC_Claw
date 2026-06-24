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
  console.log('=== RUNNING COMPREHENSIVE HERMES & WALLET GATING TESTS ===\n');

  const policy = new ExecPolicy();
  const store = new PersistentMemoryStore();
  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });

  // ==========================================
  // Test 1: Vector Graph Memory Query
  // ==========================================
  console.log('--- Test 1: Vector Graph Query for Hermes & Wallet ---');
  const vectorMemory = new VectorGraphMemory();
  const hermesNodes = vectorMemory.query('Hermes Local');
  console.log(`Matched Hermes nodes count: ${hermesNodes.nodes.length}`);
  hermesNodes.nodes.forEach(n => {
    console.log(`- Node [${n.id}] (${n.type}): ${n.label}`);
  });

  const walletNodes = vectorMemory.query('Wallet Gating');
  console.log(`Matched Wallet nodes count: ${walletNodes.nodes.length}`);
  walletNodes.nodes.forEach(n => {
    console.log(`- Node [${n.id}] (${n.type}): ${n.label}`);
  });
  console.log('');

  // ==========================================
  // Test 2: Skills Registry Query
  // ==========================================
  console.log('--- Test 2: Skills Registry Query ---');
  const skillsRegistry = new SkillsRegistry();
  const hermesSkill = skillsRegistry.load('hermes-task-execution');
  console.log(`Hermes skill loaded: ${!!hermesSkill}`);
  if (hermesSkill) {
    console.log(`- Skill: ${hermesSkill.name} (${hermesSkill.category})`);
    console.log(`  Source: ${hermesSkill.source}`);
  }

  const walletSkill = skillsRegistry.load('multi-ledger-wallet-gating');
  console.log(`Wallet skill loaded: ${!!walletSkill}`);
  if (walletSkill) {
    console.log(`- Skill: ${walletSkill.name} (${walletSkill.category})`);
    console.log(`  Source: ${walletSkill.source}`);
  }
  console.log('');

  // ==========================================
  // Test 3: Compliant Wallet Transaction (Solana)
  // ==========================================
  console.log('--- Test 3: Compliant Solana Transaction (45 SOL) ---');
  const solValid = await dispatchBuiltinGrcTool('wallet.sign_transaction', {
    ledgerType: 'solana',
    transactionAmount: 45,
    beneficiaryName: 'Cairo Technology Park'
  }, { evidence, a2z });

  console.log('Solana Valid Status:', solValid.complianceStatus);
  console.log('Co-signature Generated:', solValid.coSignature);
  if (solValid.complianceStatus !== 'APPROVED' || !solValid.coSignature) {
    throw new Error('Test 3 Failed: expected Solana payment to be APPROVED with co-signature');
  }
  console.log('');

  // ==========================================
  // Test 4: Limit Violation Wallet Transaction (Solana)
  // ==========================================
  console.log('--- Test 4: Over-limit Solana Transaction (80 SOL) ---');
  const solOver = await dispatchBuiltinGrcTool('wallet.sign_transaction', {
    ledgerType: 'solana',
    transactionAmount: 80,
    beneficiaryName: 'Cairo Technology Park'
  }, { evidence, a2z });

  console.log('Solana Over-limit Status:', solOver.complianceStatus);
  console.log('Issues:', solOver.issues);
  if (solOver.complianceStatus !== 'BLOCKED') {
    throw new Error('Test 4 Failed: expected Solana payment to be BLOCKED');
  }
  console.log('');

  // ==========================================
  // Test 5: Compliant Ripple XRP Transaction
  // ==========================================
  console.log('--- Test 5: Compliant Ripple XRP Transaction (3500 XRP) ---');
  const xrpValid = await dispatchBuiltinGrcTool('wallet.sign_transaction', {
    ledgerType: 'xrp',
    transactionAmount: 3500,
    beneficiaryName: 'National Bank of Egypt'
  }, { evidence, a2z });

  console.log('XRP Valid Status:', xrpValid.complianceStatus);
  console.log('Co-signature Generated:', xrpValid.coSignature);
  if (xrpValid.complianceStatus !== 'APPROVED' || !xrpValid.coSignature) {
    throw new Error('Test 5 Failed: expected XRP payment to be APPROVED');
  }
  console.log('');

  // ==========================================
  // Test 6: Limit Violation Ripple XRP Transaction
  // ==========================================
  console.log('--- Test 6: Over-limit Ripple XRP Transaction (6500 XRP) ---');
  const xrpOver = await dispatchBuiltinGrcTool('wallet.sign_transaction', {
    ledgerType: 'xrp',
    transactionAmount: 6500,
    beneficiaryName: 'National Bank of Egypt'
  }, { evidence, a2z });

  console.log('XRP Over-limit Status:', xrpOver.complianceStatus);
  console.log('Issues:', xrpOver.issues);
  if (xrpOver.complianceStatus !== 'BLOCKED') {
    throw new Error('Test 6 Failed: expected XRP payment to be BLOCKED');
  }
  console.log('');

  // ==========================================
  // Test 7: Blocked Ethereum / ERC-20 Transaction
  // ==========================================
  console.log('--- Test 7: Blocked Ethereum / ERC-20 Transaction (10 ETH) ---');
  const ethBlock = await dispatchBuiltinGrcTool('wallet.sign_transaction', {
    ledgerType: 'ethereum',
    transactionAmount: 10,
    beneficiaryName: 'Valid Developer'
  }, { evidence, a2z });

  console.log('Ethereum Status:', ethBlock.complianceStatus);
  console.log('Issues:', ethBlock.issues);
  if (ethBlock.complianceStatus !== 'BLOCKED') {
    throw new Error('Test 7 Failed: expected Ethereum payment to be BLOCKED');
  }
  console.log('');

  // ==========================================
  // Test 8: Sanctions Screen Blocked Transaction
  // ==========================================
  console.log('--- Test 8: Sanctioned Recipient GRC Gating (0.01 BTC to SDN Person) ---');
  const sdnBlock = await dispatchBuiltinGrcTool('wallet.sign_transaction', {
    ledgerType: 'bitcoin',
    transactionAmount: 0.01,
    beneficiaryName: 'Blocked Entity SDN Person'
  }, { evidence, a2z });

  console.log('SDN Gating Status:', sdnBlock.complianceStatus);
  console.log('Issues:', sdnBlock.issues);
  if (sdnBlock.complianceStatus !== 'BLOCKED') {
    throw new Error('Test 8 Failed: expected SDN Person transaction to be BLOCKED');
  }
  console.log('');

  // ==========================================
  // Test 9: Compliant Hermes Execution (Fully Airgapped)
  // ==========================================
  console.log('--- Test 9: Hermes Local Execution (Airgapped Compute) ---');
  const hermesValid = await dispatchBuiltinGrcTool('hermes.execute_autonomous_task', {
    taskId: 'hermes-task-99',
    taskDescription: 'Parse network router rules and check local ports for exposure',
    localModel: 'llama3-8b-local',
    airgapStatus: 'FULLY_AIRGAPPED'
  }, { evidence, a2z });

  console.log('Execution Status:', hermesValid.executionStatus);
  console.log('Logs Output:');
  hermesValid.executionLogs.forEach((log: string) => console.log(`  ${log}`));
  console.log('Output Verification Hash:', hermesValid.outputHash);
  console.log('API Cost Equivalent:', hermesValid.apiCostEquivalent, 'USD');
  if (hermesValid.executionStatus !== 'COMPLETED' || hermesValid.apiCostEquivalent !== 0) {
    throw new Error('Test 9 Failed: expected Hermes task to complete successfully with 0.00 cost');
  }
  console.log('');

  // ==========================================
  // Test 10: Non-Compliant Hermes Execution (Not Airgapped)
  // ==========================================
  console.log('--- Test 10: Hermes Execution Gating (Not Airgapped Compute) ---');
  const hermesOver = await dispatchBuiltinGrcTool('hermes.execute_autonomous_task', {
    taskId: 'hermes-task-101',
    taskDescription: 'Parse router rules',
    airgapStatus: 'CONNECTED_TO_INTERNET'
  }, { evidence, a2z });

  console.log('Execution Status:', hermesOver.executionStatus);
  console.log('Issues:', hermesOver.issues);
  if (hermesOver.executionStatus !== 'FAILED') {
    throw new Error('Test 10 Failed: expected non-airgapped Hermes execution to FAILED');
  }

  console.log('\n=== ALL HERMES & WALLET GATING TESTS COMPLETED GREEN ===');
}

runTests().catch(err => {
  console.error('Test run failed:');
  console.error(err);
  process.exit(1);
});
