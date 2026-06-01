import type { AgentSession, ExecPolicy } from '@grc-claw/agent-runtime';
import { BUILTIN_AGENT_TOOLS } from '@grc-claw/agent-runtime';
import type { ConnectorRegistry } from '@grc-claw/connectors';
import {
  CLAW_SKILL_TOOLS,
  runSkillLoop,
  type ClawDispatchContext,
  type SkillRunOptions,
} from '@grc-claw/skill-executor';
import { dispatchAgentTool } from './agent-dispatch.js';
import type { A2ZSocConnector } from '@grc-claw/a2z-connector';
import type { EvidenceStore } from '@grc-claw/evidence';

export function buildToolManifest(extraTools: { name: string; tier: string }[] = []): string {
  const lines = [...BUILTIN_AGENT_TOOLS, ...CLAW_SKILL_TOOLS, ...extraTools].map(
    (t) => `- ${t.name} (${t.tier})`
  );
  return lines.join('\n');
}

export function createClawDispatchContext(deps: {
  registry: ConnectorRegistry;
  evidence: EvidenceStore;
  a2z: A2ZSocConnector;
  defaultLlmProviderId: string;
  makeSession: (sessionId: string, policy: ExecPolicy) => AgentSession;
  getPolicy: () => ExecPolicy;
}): ClawDispatchContext {
  const toolManifest = buildToolManifest();
  const ctx = {} as ClawDispatchContext;

  ctx.registry = deps.registry;
  ctx.defaultLlmProviderId = deps.defaultLlmProviderId;
  ctx.toolManifest = toolManifest;

  ctx.invokeTool = async (tool, args) => {
    const policy = deps.getPolicy();
    const session = deps.makeSession(`skill-loop-${Date.now()}`, policy);
    const decision = await session.invoke({ tool, args });
    if (!decision.allowed) {
      return { output: {}, blocked: true, reason: decision.reason };
    }
    const output = await dispatchAgentTool(tool, args, {
      registry: deps.registry,
      evidence: deps.evidence,
      a2z: deps.a2z,
      claw: ctx,
    });
    return { output };
  };

  ctx.runSkill = async (options: SkillRunOptions) => {
    const llmId =
      options.llmProviderId ??
      deps.defaultLlmProviderId ??
      deps.registry.listLlm()[0]?.id ??
      'gemini';
    return runSkillLoop(options, {
      registry: deps.registry,
      llmProviderId: llmId,
      invokeTool: ctx.invokeTool,
      toolManifest,
    });
  };

  return ctx;
}
