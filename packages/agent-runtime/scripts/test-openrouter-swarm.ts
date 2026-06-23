import { ExecPolicy, AgentSession, ToolInvocation } from '../src/index.js';
import { dispatchBuiltinGrcTool } from '../../gateway/src/agent-dispatch.js';
import { EvidenceStore } from '@grc-claw/evidence';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';

async function runSwarmHarnessTest() {
  console.log('\x1b[36m=================================================================\x1b[0m');
  console.log('\x1b[36m   GRC_Claw OpenRouter Swarm & Anti-Swarm Harness Test Suite     \x1b[0m');
  console.log('\x1b[36m=================================================================\x1b[0m\n');

  const policy = new ExecPolicy();
  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector({
    baseUrl: 'http://127.0.0.1:3000',
    apiKey: 'mock-key',
    tenantId: 1,
    mode: 'demo'
  });
  const deps = { evidence, a2z };

  // ----------------------------------------------------
  // SCENARIO 1: Sovereign Boundary Compliance (CMMC / ITAR)
  // ----------------------------------------------------
  console.log('\x1b[35m--- Test Scenario 1: Sovereign Boundary Gating (CMMC/ITAR) ---\x1b[0m');
  
  // 1a. US-aligned model (OpenRouter Llama 3.1 70B or Nvidia Nemotron)
  console.log('\x1b[34m[Agent: Compliance Evaluator (nvidia-nemotron)]\x1b[0m requesting boundary audit...');
  const session1 = new AgentSession('sovereign-audit-session', policy);
  const boundaryInv: ToolInvocation = {
    tool: 'cmmc.validate_system_boundary',
    args: {
      systemBaseline: {
        mfaEnabled: true,
        sessionTimeoutSeconds: 600,
        remoteAccessEncrypted: true,
        auditLogsForwarded: true
      }
    },
    agentRole: 'reviewer',
    llmProviderId: 'nvidia-nemotron'
  };

  const decision1 = await session1.invoke(boundaryInv);
  console.log(`  LLM Provider: \x1b[32m${boundaryInv.llmProviderId}\x1b[0m`);
  console.log(`  Access Request to: \x1b[33m${boundaryInv.tool}\x1b[0m`);
  console.log(`  Harness Decision: Allowed=\x1b[32m${decision1.allowed}\x1b[0m, Sandbox=\x1b[32m${decision1.sandbox}\x1b[0m`);
  
  if (decision1.allowed) {
    const output1 = (await dispatchBuiltinGrcTool(boundaryInv.tool, boundaryInv.args, deps)) as any;
    console.log(`  Result output: \x1b[32m${output1.complianceStatus}\x1b[0m`);
  }

  // 1b. Non-US aligned model (Zhipu GLM-4) attempting access
  console.log('\n\x1b[34m[Agent: Local Chinese Translator (zhipu-glm)]\x1b[0m requesting boundary audit...');
  const session2 = new AgentSession('translation-session', policy);
  const boundaryInvChina: ToolInvocation = {
    tool: 'cmmc.validate_system_boundary',
    args: {
      systemBaseline: {
        mfaEnabled: true,
        sessionTimeoutSeconds: 600,
        remoteAccessEncrypted: true,
        auditLogsForwarded: true
      }
    },
    agentRole: 'translator',
    llmProviderId: 'zhipu-glm'
  };

  const decision2 = await session2.invoke(boundaryInvChina);
  console.log(`  LLM Provider: \x1b[31m${boundaryInvChina.llmProviderId}\x1b[0m`);
  console.log(`  Access Request to: \x1b[33m${boundaryInvChina.tool}\x1b[0m`);
  console.log(`  Harness Decision: Allowed=\x1b[31m${decision2.allowed}\x1b[0m, Reason: \x1b[31m${decision2.reason}\x1b[0m`);

  if (!decision1.allowed || decision2.allowed) {
    throw new Error('❌ Sovereign Boundary Gating Failed!');
  }
  console.log('\x1b[32m✅ Test Scenario 1 Passed: Sovereign boundary successfully gated non-US-aligned models from sensitive CMMC/ITAR data.\x1b[0m\n');

  // ----------------------------------------------------
  // SCENARIO 2: Swarm Segregation of Duties (SoD) Conflict
  // ----------------------------------------------------
  console.log('\x1b[35m--- Test Scenario 2: Swarm Segregation of Duties (SoD) Conflict ---\x1b[0m');
  const swarmSession = new AgentSession('multi-agent-swarm-session', policy);

  // Agent A (Developer role running via OpenRouter Llama 3.1 70B)
  console.log('\x1b[34m[Agent A: Developer (openrouter)]\x1b[0m attaching evidence to control...');
  const devInv: ToolInvocation = {
    tool: 'evidence.attach',
    args: { controlId: 'nist-3.1.1', hash: 'sha256-abcdef' },
    idempotencyKey: 'idem-dev-attach-100',
    agentRole: 'developer',
    llmProviderId: 'openrouter'
  };
  const devDecision = await swarmSession.invoke(devInv);
  console.log(`  Decision: Allowed=\x1b[32m${devDecision.allowed}\x1b[0m, Toxicity Score: ${swarmSession.getToxicityScore()}`);

  // Agent B (Reviewer role running via Nvidia Nemotron)
  console.log('\x1b[34m[Agent B: Reviewer (nvidia-nemotron)]\x1b[0m trying to approve the same control in the same turn...');
  const revInv: ToolInvocation = {
    tool: 'control.update_status',
    args: { controlId: 'nist-3.1.1', status: 'approved' },
    agentRole: 'reviewer',
    llmProviderId: 'nvidia-nemotron'
  };
  const revDecision = await swarmSession.invoke(revInv);
  console.log(`  Decision: Allowed=\x1b[31m${revDecision.allowed}\x1b[0m, Reason: \x1b[31m${revDecision.reason}\x1b[0m`);
  console.log(`  Anomalies Detected: \x1b[31m${JSON.stringify(revDecision.anomaliesDetected)}\x1b[0m`);
  console.log(`  Toxicity Score: \x1b[33m${swarmSession.getToxicityScore()}\x1b[0m`);

  if (!devDecision.allowed || revDecision.allowed || !revDecision.anomaliesDetected?.includes('SOD_CONFLICT_DETECTED')) {
    throw new Error('❌ Swarm Segregation of Duties Gating Failed!');
  }
  console.log('\x1b[32m✅ Test Scenario 2 Passed: Swarm harness successfully prevented Segregation of Duties role conflict between swarm members.\x1b[0m\n');

  // ----------------------------------------------------
  // SCENARIO 3: Anti-Swarm WAF Containment (Reasoning Loop & Canary Trap)
  // ----------------------------------------------------
  console.log('\x1b[35m--- Test Scenario 3: Anti-Swarm Loop and Honeypot Containment ---\x1b[0m');
  const loopSession = new AgentSession('loop-containment-session', policy);
  const loopInv: ToolInvocation = {
    tool: 'grc.get_compliance_score',
    args: { tenantId: 1 },
    agentRole: 'developer',
    llmProviderId: 'openrouter'
  };

  // Simulate a model that gets stuck in an execution loop
  console.log('\x1b[34m[Agent: Swarm Runner (openrouter)]\x1b[0m stuck in loop calling grc.get_compliance_score...');
  for (let i = 1; i <= 4; i++) {
    const decision = await loopSession.invoke(loopInv);
    console.log(`  Call #${i}: Allowed=\x1b[${decision.allowed ? '32mtrue' : '31mfalse'}\x1b[0m, Sandbox=\x1b[33m${decision.sandbox}\x1b[0m, Toxicity=\x1b[33m${loopSession.getToxicityScore()}\x1b[0m`);
  }

  // Honeypot Canary Trap
  console.log('\n\x1b[34m[Agent: Swarm Runner (openrouter)]\x1b[0m attempting to access a Canary Decoy Admin db tool...');
  const canaryInv: ToolInvocation = {
    tool: 'connector.admin_db_override',
    args: { target: 'all' },
    agentRole: 'developer',
    llmProviderId: 'openrouter'
  };
  const canaryDecision = await loopSession.invoke(canaryInv);
  console.log(`  Honeypot Access: Allowed=\x1b[31m${canaryDecision.allowed}\x1b[0m, Reason: \x1b[31m${canaryDecision.reason}\x1b[0m`);
  console.log(`  Final Toxicity: \x1b[31m${loopSession.getToxicityScore()}\x1b[0m`);

  if (loopSession.getToxicityScore() !== 100 || canaryDecision.allowed) {
    throw new Error('❌ Anti-Swarm Containment/Canary Trap Failed!');
  }
  console.log('\x1b[32m✅ Test Scenario 3 Passed: Loop anomaly and canary trap containment succeeded.\x1b[0m\n');

  console.log('\x1b[32m=================================================================\x1b[0m');
  console.log('\x1b[32m   All OpenRouter Swarm & Anti-Swarm Harness Tests PASSED!        \x1b[0m');
  console.log('\x1b[32m=================================================================\x1b[0m');
}

runSwarmHarnessTest().catch((err) => {
  console.error('\x1b[31mSwarm Harness Test Failure:\x1b[0m', err);
  process.exit(1);
});
