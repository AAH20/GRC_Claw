import type { ConnectorRegistry } from '@grc-claw/connectors';
import { getSkillById, listSkills } from './loader.js';
import { runSkillLoop } from './executor.js';
import type { SkillRunOptions, SkillRunResult, SkillToolInvoker } from './types.js';

export interface ClawDispatchContext {
  registry: ConnectorRegistry;
  defaultLlmProviderId: string;
  invokeTool: SkillToolInvoker;
  toolManifest: string;
  runSkill: (options: SkillRunOptions) => Promise<SkillRunResult>;
}

export async function dispatchClawTool(
  tool: string,
  args: Record<string, unknown>,
  ctx: ClawDispatchContext
): Promise<Record<string, unknown>> {
  switch (tool) {
    case 'claw.list_skills': {
      const skills = listSkills().map((s) => ({
        id: s.id,
        name: s.name,
        description: s.description,
        scope: s.scope,
        path: s.path,
      }));
      return { skills, count: skills.length };
    }
    case 'claw.get_skill': {
      const skillId = String(args.skillId ?? args.id ?? '');
      const includeBody = args.includeBody !== false;
      const skill = getSkillById(skillId);
      if (!skill) return { ok: false, error: 'skill_not_found', skillId };
      if (!includeBody) {
        const { body: _b, contentLength, ...meta } = skill;
        return { ok: true, skill: { ...meta, contentLength } };
      }
      return { ok: true, skill };
    }
    case 'claw.run_skill': {
      const skillId = String(args.skillId ?? '');
      const task = String(args.task ?? args.prompt ?? args.message ?? '');
      if (!skillId || !task) {
        return { ok: false, error: 'skillId_and_task_required' };
      }
      const result = await ctx.runSkill({
        skillId,
        task,
        llmProviderId: typeof args.llmProviderId === 'string' ? args.llmProviderId : undefined,
        maxSteps: typeof args.maxSteps === 'number' ? args.maxSteps : undefined,
        readOnlyTools: args.readOnlyTools !== false,
      });
      return { ...result };
    }
    default:
      return { ok: false, error: 'unknown_claw_tool', tool };
  }
}
