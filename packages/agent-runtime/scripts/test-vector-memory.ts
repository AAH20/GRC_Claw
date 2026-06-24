import {
  VectorGraphMemory,
  SkillsRegistry
} from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runTests() {
  console.log('=== RUNNING COMPREHENSIVE VECTOR DB & CLOUD MEMORY TESTS ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });

  // ==========================================
  // Test 1: Vector Graph Memory Query
  // ==========================================
  console.log('--- Test 1: Vector Graph Query for Vector RAG & Cloud Memory ---');
  const vectorMemory = new VectorGraphMemory();
  const ragNodes = vectorMemory.query('Vector DB');
  console.log(`Matched RAG nodes count: ${ragNodes.nodes.length}`);
  ragNodes.nodes.forEach(n => {
    console.log(`- Node [${n.id}] (${n.type}): ${n.label}`);
  });

  const lockinNodes = vectorMemory.query('Cloud Memory');
  console.log(`Matched Lock-in nodes count: ${lockinNodes.nodes.length}`);
  lockinNodes.nodes.forEach(n => {
    console.log(`- Node [${n.id}] (${n.type}): ${n.label}`);
  });
  console.log('');

  // ==========================================
  // Test 2: Skills Registry Query
  // ==========================================
  console.log('--- Test 2: Skills Registry Query for Playbooks ---');
  const skillsRegistry = new SkillsRegistry();
  const vectorSkill = skillsRegistry.load('vector-db-integration');
  console.log(`Vector RAG skill loaded: ${!!vectorSkill}`);
  if (vectorSkill) {
    console.log(`- Skill: ${vectorSkill.name} (${vectorSkill.category})`);
    console.log(`  Source: ${vectorSkill.source}`);
  }

  const cloudSkill = skillsRegistry.load('cloud-memory-audit');
  console.log(`Cloud Audit skill loaded: ${!!cloudSkill}`);
  if (cloudSkill) {
    console.log(`- Skill: ${cloudSkill.name} (${cloudSkill.category})`);
    console.log(`  Source: ${cloudSkill.source}`);
  }
  console.log('');

  // ==========================================
  // Test 3: Local Vector DB Integration (Compliant)
  // ==========================================
  console.log('--- Test 3: Integrating Compliant Local Vector Database (Pinecone) ---');
  const localDb = await dispatchBuiltinGrcTool('memory.integrate_vector_db', {
    vectorDbProvider: 'pinecone',
    vectorDbEndpoint: 'http://localhost:8081',
    isLocalOnly: true,
    indexName: 'grc-claw-rag'
  }, { evidence, a2z });

  console.log('Local DB Integration Status:', localDb.integrationStatus);
  console.log('RAG Safety Clearance:', localDb.ragSafetyClearance);
  console.log('Issues:', localDb.issues);
  if (localDb.integrationStatus !== 'ACTIVE' || localDb.ragSafetyClearance !== 'GRANTED' || localDb.issues.length !== 0) {
    throw new Error('Test 3 Failed: expected local vector DB integration to be ACTIVE and GRANTED');
  }
  console.log('');

  // ==========================================
  // Test 4: External Vector DB Integration (Warning)
  // ==========================================
  console.log('--- Test 4: Integrating External Vector Database ---');
  const externalDb = await dispatchBuiltinGrcTool('memory.integrate_vector_db', {
    vectorDbProvider: 'pinecone',
    vectorDbEndpoint: 'https://external-cloud-pinecone.io',
    isLocalOnly: false,
    indexName: 'external-rag'
  }, { evidence, a2z });

  console.log('External DB Integration Status:', externalDb.integrationStatus);
  console.log('RAG Safety Clearance:', externalDb.ragSafetyClearance);
  console.log('Issues:', externalDb.issues);
  if (externalDb.ragSafetyClearance !== 'FLAGGED_WARNING' || externalDb.issues.length === 0) {
    throw new Error('Test 4 Failed: expected external DB integration to trigger FLAGGED_WARNING');
  }
  console.log('');

  // ==========================================
  // Test 5: Cloud Memory Audit with Large Swarm (OpenAI Dreaming V3)
  // ==========================================
  console.log('--- Test 5: Auditing Cloud Memory (OpenAI Dreaming V3) with 300-Agent Swarm ---');
  const cloudAudit = await dispatchBuiltinGrcTool('memory.audit_cloud_memory', {
    cloudProviderName: 'openai-dreaming-v3',
    agentCount: 300,
    monthlyTokenBudget: 15000
  }, { evidence, a2z });

  console.log('Compliance Status:', cloudAudit.complianceStatus);
  console.log('Vendor Lock-in Risk Score:', cloudAudit.lockInRiskScore);
  console.log('Lock-in Issues:', cloudAudit.lockInIssues);
  console.log('Cost Audit Notes:', cloudAudit.costAuditNotes);
  console.log('Portability Plan:', cloudAudit.portabilityPlan);
  console.log('Passed Checks:', cloudAudit.passedChecks);

  if (cloudAudit.complianceStatus !== 'NON_COMPLIANT' || cloudAudit.lockInRiskScore !== 88) {
    throw new Error('Test 5 Failed: expected OpenAI Dreaming V3 to be marked NON_COMPLIANT with risk score 88');
  }
  if (!cloudAudit.costAuditNotes.includes('Swarm Analysis: Orchestrating a swarm of 300 concurrent agents')) {
    throw new Error('Test 5 Failed: expected cost audit notes to highlight the 300-agent swarm scaling limits');
  }
  console.log('');

  // ==========================================
  // Test 6: Compliant Memory Audit (Local Memory)
  // ==========================================
  console.log('--- Test 6: Auditing Compliant Local Memory Config ---');
  const localAudit = await dispatchBuiltinGrcTool('memory.audit_cloud_memory', {
    cloudProviderName: 'local-memory-graph',
    agentCount: 12,
    monthlyTokenBudget: 500
  }, { evidence, a2z });

  console.log('Compliance Status:', localAudit.complianceStatus);
  console.log('Vendor Lock-in Risk Score:', localAudit.lockInRiskScore);
  console.log('Passed Checks:', localAudit.passedChecks);

  if (localAudit.complianceStatus !== 'COMPLIANT' || localAudit.lockInRiskScore !== 0) {
    throw new Error('Test 6 Failed: expected local memory configuration to be COMPLIANT');
  }

  console.log('\n=== ALL VECTOR DB & CLOUD MEMORY TESTS COMPLETED GREEN ===');
}

runTests().catch(err => {
  console.error('Test run failed:');
  console.error(err);
  process.exit(1);
});
