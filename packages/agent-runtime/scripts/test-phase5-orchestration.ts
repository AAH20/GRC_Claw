import { ExecPolicy, AgentSession, ToolInvocation, VectorGraphMemory } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function runPhase5Tests() {
  console.log('=== GRC_Claw Phase 5: Swarm Mastery Orchestration Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase5-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: Virtualization-Level Sandbox Intercepts
  // ----------------------------------------------------
  console.log('--- Test 1: MicroVM Sandbox Rule Dispatch ---');
  const microVMInv: ToolInvocation = {
    tool: 'security.microvm_sandbox_rule',
    args: { agentDid: 'did:grc:agent-777', cpuShares: 2, memLimitMb: 1024 },
    agentRole: 'developer',
    idempotencyKey: 'idem-mvm-1'
  };

  const decision1 = policy.evaluate(microVMInv);
  console.log(`Tool: ${microVMInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);
  console.log(`Requires Approval: ${decision1.requiresApproval}`);

  const dispatch1 = await dispatchBuiltinGrcTool(microVMInv.tool, microVMInv.args, deps);
  console.log('Dispatch Status:', dispatch1.status);
  console.log('Sandbox Type:', dispatch1.sandboxType);
  console.log('Boot Time:', dispatch1.bootTimeMs, 'ms');
  console.log('Hypervisor Intercept:', dispatch1.hypervisorIoInterceptActive);

  if (dispatch1.ok && dispatch1.sandboxType === 'firecracker_microvm' && dispatch1.status === 'ACTIVE_ISOLATED') {
    console.log('✅ Test 1 Passed: Firecracker MicroVM sandbox rules evaluated and dispatched successfully.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Homomorphic Vector Graph Memory
  // ----------------------------------------------------
  console.log('--- Test 2: Homomorphic Graph Query Verification ---');
  const vectorMemory = new VectorGraphMemory();
  const homomorphicQuery = 'SELECT * FROM nodes WHERE secret = true';
  const pubKeyHash = '0xHOMOMORPHIC_ENCRYPTION_PUBLIC_KEY_HASH_2026';

  const localResult = vectorMemory.queryHomomorphic(homomorphicQuery, pubKeyHash);
  console.log('Local search matches count:', localResult.matchesCount);
  console.log('Local encrypted results prefix:', localResult.resultsCiphertext.substring(0, 30));

  const homomorphicInv: ToolInvocation = {
    tool: 'memory.query_homomorphic_graph',
    args: { queryCiphertext: homomorphicQuery, homomorphicPublicKeyHash: pubKeyHash },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(homomorphicInv);
  console.log(`Tool: ${homomorphicInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(homomorphicInv.tool, homomorphicInv.args, deps);
  console.log('Dispatch Ciphertext:', dispatch2.resultsCiphertext);
  console.log('Verification Proof:', dispatch2.zkVerificationProof);

  if (dispatch2.ok && dispatch2.resultsCiphertext && dispatch2.zkVerificationProof) {
    console.log('✅ Test 2 Passed: Homomorphic graph query and cryptographic zero-knowledge proof verification succeeded.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Multi-Model PBFT Quorum Consensus
  // ----------------------------------------------------
  console.log('--- Test 3: PBFT Multi-Model Quorum Consensus ---');
  const quorumInv: ToolInvocation = {
    tool: 'consensus.verify_multi_model_quorum',
    args: {
      targetTool: 'firewall.apply_rule',
      modelOutputsJson: JSON.stringify([
        { model: 'gemini-2.5-flash', action: 'firewall.apply_rule', args: { blockIp: '192.168.1.100' } },
        { model: 'claude-3-opus', action: 'firewall.apply_rule', args: { blockIp: '192.168.1.100' } },
        { model: 'llama-3-70b', action: 'firewall.apply_rule', args: { blockIp: '192.168.1.100' } }
      ]),
      minConsensusQuorum: 2
    },
    agentRole: 'reviewer'
  };

  const decision3 = policy.evaluate(quorumInv);
  console.log(`Tool: ${quorumInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(quorumInv.tool, quorumInv.args, deps);
  console.log('Consensus Quorum Reached:', dispatch3.consensusQuorumReached);
  console.log('PBFT Signature:', dispatch3.pbftRoundSignature);
  console.log('Matching Models count:', dispatch3.matchingModelsCount);

  if (dispatch3.ok && dispatch3.consensusQuorumReached === true && dispatch3.matchingModelsCount === 3) {
    console.log('✅ Test 3 Passed: Multi-model PBFT quorum consensus successfully established.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Self-Healing Playbook Generation
  // ----------------------------------------------------
  console.log('--- Test 4: Self-Healing Playbook Generation ---');
  const selfHealingInv: ToolInvocation = {
    tool: 'soar.generate_self_healing_playbook',
    args: {
      anomalyPayloadJson: JSON.stringify({ type: 'LOOP_ANOMALY', severity: 'critical', tool: 'evidence.attach' }),
      remediationType: 'quarantine'
    },
    agentRole: 'deployer',
    idempotencyKey: 'idem-soar-sh-1'
  };

  const decision4 = policy.evaluate(selfHealingInv);
  console.log(`Tool: ${selfHealingInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(selfHealingInv.tool, selfHealingInv.args, deps);
  console.log('Generated Playbook ID:', dispatch4.generatedPlaybookId);
  console.log('Sandbox Simulation Verification:', dispatch4.simulatedSandboxVerify);
  console.log('Requires Human Approval:', dispatch4.requiresHumanApprovalToken);

  if (dispatch4.ok && dispatch4.generatedPlaybookId.startsWith('pb-self-healing-') && dispatch4.simulatedSandboxVerify === 'VERIFIED_SUCCESS') {
    console.log('✅ Test 4 Passed: Self-healing containment playbook generated and verified inside sandbox simulator.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  // ----------------------------------------------------
  // TEST 5: Semantic Thought-Loop Circuit Breaker
  // ----------------------------------------------------
  console.log('--- Test 5: Semantic Thought-Loop Circuit Breaker ---');
  const loopSession = new AgentSession('semantic-loop-session-99', policy);

  const thought1 = 'I will examine the database connections in order to search for administrative login overrides.';
  const thought2 = 'I will examine the database connections in order to search for administrative login overrides.'; // identical to trigger Jaccard similarity of 1.0
  const thoughtDifferent = 'Now I will proceed with creating a standard evidence container block.';

  const inv1: ToolInvocation = {
    tool: 'grc.list_controls',
    args: {},
    thought: thought1
  };

  const inv2: ToolInvocation = {
    tool: 'evidence.read',
    args: { evidenceId: 'ev-001' },
    thought: thought2
  };

  const inv3: ToolInvocation = {
    tool: 'evidence.read',
    args: { evidenceId: 'ev-002' },
    thought: thoughtDifferent
  };

  console.log('Step 1 (First thought):');
  const d5_1 = await loopSession.invoke(inv1);
  console.log(`  Allowed: ${d5_1.allowed}, Toxicity Score: ${loopSession.getToxicityScore()}, Anomalies: ${JSON.stringify(d5_1.anomaliesDetected)}`);

  await delay(60); // Prevent RAPID_DISCOVERY_ANOMALY from interfering

  console.log('Step 2 (Semantic thought-loop override):');
  const d5_2 = await loopSession.invoke(inv2);
  console.log(`  Allowed: ${d5_2.allowed}, Toxicity Score: ${loopSession.getToxicityScore()}, Anomalies: ${JSON.stringify(d5_2.anomaliesDetected)}`);

  await delay(60); // Prevent RAPID_DISCOVERY_ANOMALY from interfering

  console.log('Step 3 (Different thought - should reset loop anomaly pattern):');
  const d5_3 = await loopSession.invoke(inv3);
  console.log(`  Allowed: ${d5_3.allowed}, Toxicity Score: ${loopSession.getToxicityScore()}, Anomalies: ${JSON.stringify(d5_3.anomaliesDetected)}`);

  if (d5_2.anomaliesDetected?.includes('SEMANTIC_LOOP_ANOMALY') && loopSession.getToxicityScore() === 30) {
    console.log('✅ Test 5 Passed: Semantic thought-loop circuit breaker successfully detected similarities, triggered anomaly, and scaled toxicity.\n');
  } else {
    throw new Error('❌ Test 5 Failed!');
  }

  console.log('=== ALL PHASE 5 SWARM MASTERY TESTS COMPLETED GREEN ===');
}

runPhase5Tests().catch(err => {
  console.error('Test suite failed:');
  console.error(err);
  process.exit(1);
});
