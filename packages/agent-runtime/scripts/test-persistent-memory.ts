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
import * as fs from 'fs';
import * as path from 'path';

async function runTests() {
  console.log('=== RUNNING COMPREHENSIVE PERSISTENT MEMORY & SKILLS REGISTRY TESTS ===\n');

  // Clear previous test states if any
  const testSessionId = 'test-persist-session-999';
  const memoryDir = path.resolve(process.cwd(), '.grc_memory');
  const filePath = path.join(memoryDir, `${testSessionId}.json`);
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
  }

  // Define policy
  const policy = new ExecPolicy();
  const store = new PersistentMemoryStore();

  // ==========================================
  // Test 1: Session State Persistence & Restoration
  // ==========================================
  console.log('--- Test 1: Testing Session State Persistence ---');
  let session = new AgentSession(testSessionId, policy, store);

  // Invoke a few tools to alter session state
  await session.invoke({ tool: 'grc.list_controls', args: { tenantId: 1 } });
  await session.invoke({ tool: 'grc.get_compliance_score', args: { tenantId: 1 } });

  // Simulate a loop anomaly to increase toxicity score
  await session.invoke({ tool: 'control.update_status', args: { controlId: 'CMMC-1', status: 'Passed' } });
  await session.invoke({ tool: 'control.update_status', args: { controlId: 'CMMC-1', status: 'Passed' } });
  await session.invoke({ tool: 'control.update_status', args: { controlId: 'CMMC-1', status: 'Passed' } });

  const initialToxicity = session.getToxicityScore();
  const initialCalls = session.getState().calls;
  console.log(`Initial Calls: ${initialCalls}`);
  console.log(`Initial Toxicity Score: ${initialToxicity}%`);
  console.log(`Session file exists: ${fs.existsSync(filePath)}`);

  if (!fs.existsSync(filePath)) {
    throw new Error('Test 1 Failed: Persistent state file was not created.');
  }

  console.log('\n--- Restoring Session from Disk ---');
  // Create a brand new session object with same ID - should auto-restore
  const restoredSession = new AgentSession(testSessionId, policy, store);
  const restoredState = restoredSession.getState();
  console.log(`Restored Calls: ${restoredState.calls}`);
  console.log(`Restored Toxicity Score: ${restoredSession.getToxicityScore()}%`);

  if (restoredState.calls !== initialCalls || restoredSession.getToxicityScore() !== initialToxicity) {
    throw new Error('Test 1 Failed: Restored session metrics do not match initial state.');
  }
  console.log('✔ Test 1 Passed: Session state successfully saved and restored across lifecycles.\n');

  // ==========================================
  // Test 2: Vector Graph Memory Queries
  // ==========================================
  console.log('--- Test 2: Querying Vector Graph Memory ---');
  const vectorMemory = new VectorGraphMemory();
  const isoResults = vectorMemory.query('ISO 42001');
  console.log(`Query "ISO 42001" matched ${isoResults.nodes.length} nodes and ${isoResults.edges.length} edges.`);
  console.log('Matched Nodes:');
  isoResults.nodes.forEach(n => console.log(`  - [${n.type.toUpperCase()}] ${n.id}: ${n.label}`));

  const cmmcResults = vectorMemory.query('CMMC Session Terminate');
  console.log(`Query "CMMC Session Terminate" matched ${cmmcResults.nodes.length} nodes.`);
  cmmcResults.nodes.forEach(n => console.log(`  - [${n.type.toUpperCase()}] ${n.id}: ${n.label}`));

  if (isoResults.nodes.length === 0 || cmmcResults.nodes.length === 0) {
    throw new Error('Test 2 Failed: Vector graph queries returned empty results.');
  }
  console.log('✔ Test 2 Passed: Vector Graph successfully resolved semantic and keyword terms.\n');

  // ==========================================
  // Test 3: Skills Registry (skills.sh 852K database integration)
  // ==========================================
  console.log('--- Test 3: Querying skills.sh Registry ---');
  const registry = new SkillsRegistry();
  console.log(`Total skills available in skills.sh catalog: ${registry.getTotalCount()}`);

  const roboticsSkills = registry.query('Robotics Safe Actuation');
  console.log(`Query "Robotics Safe Actuation" matched ${roboticsSkills.length} skill(s).`);
  if (roboticsSkills.length === 0) {
    throw new Error('Test 3 Failed: Could not locate AGI robotics safe actuation skill.');
  }

  const robotSkill = roboticsSkills[0];
  console.log(`Loaded Skill Playbook for: "${robotSkill.name}"`);
  console.log(`  Category: ${robotSkill.category}`);
  console.log(`  Source: ${robotSkill.source}`);
  console.log('  Playbook Steps:');
  robotSkill.playbook.steps.forEach(s => console.log(`    - ${s}`));

  if (registry.getTotalCount() !== 852000) {
    throw new Error('Test 3 Failed: Skills registry count was not 852K.');
  }
  console.log('✔ Test 3 Passed: Successfully queried and loaded skills from skills.sh repository.\n');

  // ==========================================
  // Test 4: Gateway Dispatch Integration for memory.* and skills.*
  // ==========================================
  console.log('--- Test 4: Gateway Tool Dispatching ---');
  const mockDeps = {
    evidence: new EvidenceStore(),
    a2z: new A2ZSocConnector({ apiUrl: '', apiKey: '' })
  };

  // Test memory.query_vector_graph via Gateway
  console.log('Dispatching memory.query_vector_graph...');
  const gwVectorRes = await dispatchBuiltinGrcTool('memory.query_vector_graph', { queryText: 'CMMC Level 2' }, mockDeps);
  console.log(`Gateway matched ${(gwVectorRes.nodes as any[]).length} nodes.`);

  // Test memory.persist_session_state via Gateway
  console.log('Dispatching memory.persist_session_state...');
  const gwPersistRes = await dispatchBuiltinGrcTool('memory.persist_session_state', {
    sessionId: testSessionId,
    toxicityScore: 85,
    calls: 10
  }, mockDeps);
  console.log(`Gateway Saved Toxicity: ${(gwPersistRes.state as any).toxicityScore}%`);

  // Test skills.query_repo via Gateway
  console.log('Dispatching skills.query_repo...');
  const gwSkillsQuery = await dispatchBuiltinGrcTool('skills.query_repo', { queryText: 'Kubernetes' }, mockDeps);
  console.log(`Gateway matched ${(gwSkillsQuery.skills as any[]).length} skill.`);

  // Test skills.load_definition via Gateway
  console.log('Dispatching skills.load_definition...');
  const gwSkillLoad = await dispatchBuiltinGrcTool('skills.load_definition', { skillId: 'iso-42001-audit' }, mockDeps);
  console.log(`Gateway loaded skill source: ${(gwSkillLoad.definition as any).source}`);

  if (!gwVectorRes.ok || !gwPersistRes.ok || !gwSkillsQuery.ok || !gwSkillLoad.ok) {
    throw new Error('Test 4 Failed: One of the gateway dispatches failed.');
  }
  console.log('✔ Test 4 Passed: Gateway dispatcher handled memory and skills tools flawlessly.\n');

  console.log('===============================================================');
  console.log('✔ ALL PERSISTENT MEMORY & SKILLS REGISTRY TESTS PASSED SUCCESSFULLY!');
  console.log('===============================================================');
}

runTests().catch(err => {
  console.error('❌ TEST RUN FAILED:', err);
  process.exit(1);
});
