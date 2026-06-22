import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';

async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function runAntiSwarmTest() {
  console.log('=== GRC_Claw Swarm Harness & Anti-Swarm Test Suite ===\n');

  const policy = new ExecPolicy();
  const session = new AgentSession('anti-swarm-session-123', policy);

  // ----------------------------------------------------
  // TEST 1: Canary / Honeypot Tool Detection
  // ----------------------------------------------------
  console.log('--- Test 1: Canary/Honeypot Trigger ---');
  const canaryInv: ToolInvocation = {
    tool: 'connector.canary_override',
    args: { target: 'production_main_db' },
    agentRole: 'developer'
  };

  const decision1 = await session.invoke(canaryInv);
  console.log(`Called tool: ${canaryInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);
  console.log(`Reason: ${decision1.reason}`);
  console.log(`Sandbox: ${decision1.sandbox}`);
  console.log(`Toxicity Score: ${session.getToxicityScore()}`);
  console.log(`Anomalies: ${JSON.stringify(decision1.anomaliesDetected)}\n`);

  if (!decision1.allowed && decision1.reason === 'honeypot_triggered' && session.getToxicityScore() === 100) {
    console.log('✅ Test 1 Passed: Canary honeypot successfully derailed agent and maxed toxicity.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // Create a new session for subsequent clean state tests
  const activeSession = new AgentSession('active-monitoring-session-456', policy);

  // ----------------------------------------------------
  // TEST 2: Loop Anomaly Detection
  // ----------------------------------------------------
  console.log('--- Test 2: Loop Anomaly Detection ---');
  const loopInv: ToolInvocation = {
    tool: 'grc.list_controls',
    args: { includeAims: false },
    agentRole: 'developer'
  };

  console.log('Iteration 1:');
  const d2_1 = await activeSession.invoke(loopInv);
  console.log(`  Allowed: ${d2_1.allowed}, Toxicity: ${activeSession.getToxicityScore()}`);

  console.log('Iteration 2:');
  const d2_2 = await activeSession.invoke(loopInv);
  console.log(`  Allowed: ${d2_2.allowed}, Toxicity: ${activeSession.getToxicityScore()}`);

  console.log('Iteration 3 (Should trigger Loop Anomaly):');
  const d2_3 = await activeSession.invoke(loopInv);
  console.log(`  Allowed: ${d2_3.allowed}, Toxicity: ${activeSession.getToxicityScore()}`);
  console.log(`  Anomalies: ${JSON.stringify(d2_3.anomaliesDetected)}`);

  console.log('Iteration 4 (Should exceed toxicity threshold and get quarantined/blocked):');
  const d2_4 = await activeSession.invoke(loopInv);
  console.log(`  Allowed: ${d2_4.allowed}, Reason: ${d2_4.reason}, Sandbox: ${d2_4.sandbox}, Toxicity: ${activeSession.getToxicityScore()}\n`);

  if (d2_3.anomaliesDetected?.includes('LOOP_ANOMALY') && activeSession.getToxicityScore() >= 50 && !d2_4.allowed) {
    console.log('✅ Test 2 Passed: Reasoning loop identified, toxicity scaled, and containment forced block.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Rapid Discovery / Timing Anomaly Detection
  // ----------------------------------------------------
  console.log('--- Test 3: Rapid Discovery Anomaly ---');
  const rapidSession = new AgentSession('rapid-session-789', policy);
  const rapidInv1: ToolInvocation = {
    tool: 'grc.get_compliance_score',
    args: {},
    agentRole: 'developer'
  };
  const rapidInv2: ToolInvocation = {
    tool: 'evidence.read',
    args: { evidenceId: 'ev-001' },
    agentRole: 'developer'
  };

  const d3_1 = await rapidSession.invoke(rapidInv1);
  // Zero-delay invocation to trigger timing violation
  const d3_2 = await rapidSession.invoke(rapidInv2);

  console.log(`Call 1: Allowed=${d3_1.allowed}`);
  console.log(`Call 2 (Immediate): Allowed=${d3_2.allowed}, Toxicity=${rapidSession.getToxicityScore()}`);
  console.log(`Anomalies: ${JSON.stringify(d3_2.anomaliesDetected)}\n`);

  if (d3_2.anomaliesDetected?.includes('RAPID_DISCOVERY_ANOMALY') && rapidSession.getToxicityScore() > 0) {
    console.log('✅ Test 3 Passed: Rapid sub-50ms tool scanning flagged as timing anomaly.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Swarm Harness Segregation of Duties (SoD) Conflict
  // ----------------------------------------------------
  console.log('--- Test 4: Segregation of Duties (SoD) Conflict ---');
  const sodSession = new AgentSession('sod-session-999', policy);
  
  const devInv: ToolInvocation = {
    tool: 'evidence.attach',
    args: { controlId: 'iso-a.8.15', hash: 'sha256-abc' },
    idempotencyKey: 'idem-111',
    agentRole: 'developer'
  };

  const reviewInv: ToolInvocation = {
    tool: 'control.update_status',
    args: { controlId: 'iso-a.8.15', status: 'approved' },
    agentRole: 'reviewer'
  };

  console.log('Developer attaches evidence...');
  const d4_1 = await sodSession.invoke(devInv);
  console.log(`  Allowed: ${d4_1.allowed}, Toxicity: ${sodSession.getToxicityScore()}`);

  console.log('Reviewer reviews and updates status (Should trigger SoD conflict since developer and reviewer conflict)...');
  const d4_2 = await sodSession.invoke(reviewInv);
  console.log(`  Allowed: ${d4_2.allowed}`);
  console.log(`  Reason: ${d4_2.reason}`);
  console.log(`  Toxicity: ${sodSession.getToxicityScore()}`);
  console.log(`  Anomalies: ${JSON.stringify(d4_2.anomaliesDetected)}\n`);

  if (!d4_2.allowed && d4_2.anomaliesDetected?.includes('SOD_CONFLICT_DETECTED')) {
    console.log('✅ Test 4 Passed: Swarm harness successfully prevented Segregation of Duties role conflict.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== All Swarm & Anti-Swarm tests completed successfully! ===');
}

runAntiSwarmTest().catch((err) => {
  console.error(err);
  process.exit(1);
});
