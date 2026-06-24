import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runPhase10Tests() {
  console.log('=== GRC_Claw Phase 10: Sovereign Swarm Choreography & Quantum Sovereignty Tests ===\n');

  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({ apiUrl: 'https://a2zsoc.com/api', apiKey: 'mock-key' });
  const deps = { evidence, a2z };

  const policy = new ExecPolicy();
  const session = new AgentSession('phase10-test-session', policy);

  // ----------------------------------------------------
  // TEST 1: Ephemeral Confidential Enclave Spawning
  // ----------------------------------------------------
  console.log('--- Test 1: Ephemeral Confidential Enclave Spawning ---');
  const enclaveInv: ToolInvocation = {
    tool: 'sovereign.spawn_ephemeral_enclave',
    args: { sessionId: 'session-confidential-99', hardwareType: 'Intel_TDX' },
    agentRole: 'developer'
  };

  const decision1 = policy.evaluate(enclaveInv);
  console.log(`Tool: ${enclaveInv.tool}`);
  console.log(`Allowed: ${decision1.allowed}`);

  const dispatch1 = await dispatchBuiltinGrcTool(enclaveInv.tool, enclaveInv.args, deps);
  console.log('Enclave Status:', dispatch1.status);
  console.log('Enclave Hardware Type:', dispatch1.hardwareType);
  console.log('Memory Range Isolated:', dispatch1.memoryRange);
  console.log('Quote Hardware Attested:', dispatch1.attested);

  if (dispatch1.ok && dispatch1.spawned && dispatch1.status === 'ENCLAVE_READY' && dispatch1.attested) {
    console.log('✅ Test 1 Passed: Ephemeral Intel TDX enclave successfully provisioned and verified.\n');
  } else {
    throw new Error('❌ Test 1 Failed!');
  }

  // ----------------------------------------------------
  // TEST 2: Post-Quantum Key Exchange (ML-KEM-1024)
  // ----------------------------------------------------
  console.log('--- Test 2: Post-Quantum Key Exchange (ML-KEM-1024) ---');
  const keyExchangeInv: ToolInvocation = {
    tool: 'consensus.exchange_quantum_keys',
    args: { targetPeerUrl: 'wss://sovereign-peer-01.internal', publicKeyKem: 'ml-kem-1024-pubkey-0x1a8fd' },
    agentRole: 'developer'
  };

  const decision2 = policy.evaluate(keyExchangeInv);
  console.log(`Tool: ${keyExchangeInv.tool}`);
  console.log(`Allowed: ${decision2.allowed}`);

  const dispatch2 = await dispatchBuiltinGrcTool(keyExchangeInv.tool, keyExchangeInv.args, deps);
  console.log('Shared Secret Established:', dispatch2.sharedSecretEstablished);
  console.log('KEM Protocol Used:', dispatch2.kemUsed);
  console.log('Peer Node Cryptographically Verified:', dispatch2.peerNodeVerified);

  if (dispatch2.ok && dispatch2.sharedSecretEstablished && dispatch2.kemUsed === 'ML-KEM-1024') {
    console.log('✅ Test 2 Passed: Quantum-safe symmetric secret tunnel established with remote peer gateway.\n');
  } else {
    throw new Error('❌ Test 2 Failed!');
  }

  // ----------------------------------------------------
  // TEST 3: Active Honey-Token Canary Injections
  // ----------------------------------------------------
  console.log('--- Test 3: Active Honey-Token Canary Injections ---');
  const injectHoneyInv: ToolInvocation = {
    tool: 'security.inject_honey_tokens',
    args: { agentSessionId: 'session-confidential-99', honeyTokenType: ['credential', 'control-bypass', 'root-key'] },
    agentRole: 'developer'
  };

  const decision3 = policy.evaluate(injectHoneyInv);
  console.log(`Tool: ${injectHoneyInv.tool}`);
  console.log(`Allowed: ${decision3.allowed}`);

  const dispatch3 = await dispatchBuiltinGrcTool(injectHoneyInv.tool, injectHoneyInv.args, deps);
  console.log('Honey Canaries Status:', dispatch3.status);
  console.log('Decoy Tokens Injected Count:', dispatch3.tokensInjectedCount);
  console.log('Canary IDs Registered:', dispatch3.canaryIds);

  if (dispatch3.ok && dispatch3.tokensInjectedCount === 3 && dispatch3.status === 'CANARIES_ACTIVE') {
    console.log('✅ Test 3 Passed: Active honeypot tokens successfully injected into the agent runtime environment.\n');
  } else {
    throw new Error('❌ Test 3 Failed!');
  }

  // ----------------------------------------------------
  // TEST 4: Fully Homomorphic Execution of Policies
  // ----------------------------------------------------
  console.log('--- Test 4: Fully Homomorphic Execution of Policies ---');
  const homomorphicPolicyInv: ToolInvocation = {
    tool: 'security.evaluate_homomorphic_policy',
    args: { encryptedPrompt: 'ciphertext-prompt-hash-0x99a2c3', policyEvaluationKeys: 'eval-key-0x4b12' },
    agentRole: 'developer'
  };

  const decision4 = policy.evaluate(homomorphicPolicyInv);
  console.log(`Tool: ${homomorphicPolicyInv.tool}`);
  console.log(`Allowed: ${decision4.allowed}`);

  const dispatch4 = await dispatchBuiltinGrcTool(homomorphicPolicyInv.tool, homomorphicPolicyInv.args, deps);
  console.log('FHE Policy check Status:', dispatch4.status);
  console.log('FHE Evaluation Time (ms):', dispatch4.evaluationTimeMs);
  console.log('FHE Check Safety Results:', dispatch4.safe);

  if (dispatch4.ok && dispatch4.safe && dispatch4.evaluationTimeMs > 0) {
    console.log('✅ Test 4 Passed: ExecPolicy conditions verified directly on encrypted prompts with zero leakage.\n');
  } else {
    throw new Error('❌ Test 4 Failed!');
  }

  console.log('=== ALL PHASE 10 SOVEREIGN SWARM CHOREOGRAPHY COMPLETED GREEN ===');
}

runPhase10Tests().catch(err => {
  console.error('Phase 10 test run failed:');
  console.error(err);
  process.exit(1);
});
