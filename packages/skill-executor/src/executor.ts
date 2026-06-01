import type { ConnectorRegistry } from '@grc-claw/connectors';
import { chatViaProvider } from '@grc-claw/connectors';
import { getSkillById } from './loader.js';
import { parseFinalAnswer, parseToolCall } from './parse-tool-calls.js';
import type { SkillRunOptions, SkillRunResult, SkillToolInvoker } from './types.js';

const DEFAULT_MAX_STEPS = 8;
const MAX_SKILL_BODY_CHARS = 24_000;

function buildExecutorSystemPrompt(
  skillBody: string,
  toolManifest: string,
  task: string
): string {
  const trimmed =
    skillBody.length > MAX_SKILL_BODY_CHARS
      ? `${skillBody.slice(0, MAX_SKILL_BODY_CHARS)}\n\n[…skill truncated for token budget…]`
      : skillBody;

  return [
    'You are the GRC_Claw skill executor. Follow the skill playbook below.',
    'When you need live gateway data, emit exactly one line then stop:',
    'TOOL_CALL: {"tool":"<tool_name>","args":{...}}',
    'When finished, emit:',
    'FINAL_ANSWER: <your complete reply>',
    '',
    '## Available gateway tools',
    toolManifest,
    '',
    '## Skill playbook',
    trimmed,
    '',
    '## Operator task',
    task,
  ].join('\n');
}

export async function runSkillLoop(
  options: SkillRunOptions,
  deps: {
    registry: ConnectorRegistry;
    llmProviderId: string;
    invokeTool: SkillToolInvoker;
    toolManifest: string;
  }
): Promise<SkillRunResult> {
  const skill = getSkillById(options.skillId);
  if (!skill) {
    return {
      ok: false,
      skillId: options.skillId,
      task: options.task,
      steps: [],
      finalAnswer: '',
      error: `skill_not_found:${options.skillId}`,
    };
  }

  const maxSteps = options.maxSteps ?? DEFAULT_MAX_STEPS;
  const readOnlyTools = options.readOnlyTools !== false;
  const steps: SkillRunResult['steps'] = [];
  const messages: { role: 'user' | 'assistant'; content: string }[] = [
    {
      role: 'user',
      content: buildExecutorSystemPrompt(skill.body, deps.toolManifest, options.task),
    },
  ];

  for (let i = 0; i < maxSteps; i++) {
    const llm = await chatViaProvider(deps.registry, deps.llmProviderId, {
      messages: [{ role: 'system', content: 'Follow TOOL_CALL / FINAL_ANSWER protocol exactly.' }, ...messages],
      maxTokens: 4096,
      temperature: 0.3,
    });
    const content = llm.content.trim();
    steps.push({ index: i, type: 'llm', content });

    const final = parseFinalAnswer(content);
    if (final) {
      steps.push({ index: i, type: 'final', content: final });
      return {
        ok: true,
        skillId: options.skillId,
        task: options.task,
        steps,
        finalAnswer: final,
      };
    }

    const call = parseToolCall(content);
    if (!call) {
      return {
        ok: true,
        skillId: options.skillId,
        task: options.task,
        steps,
        finalAnswer: content,
      };
    }

    if (readOnlyTools && call.tool.startsWith('claw.run_skill')) {
      steps.push({
        index: i,
        type: 'tool',
        tool: call.tool,
        blocked: true,
        reason: 'nested_run_skill_not_allowed_in_loop',
      });
      messages.push({
        role: 'assistant',
        content,
      });
      messages.push({
        role: 'user',
        content: `Tool blocked: ${call.tool}. Use read-tier tools only, then FINAL_ANSWER.`,
      });
      continue;
    }

    const invoked = await deps.invokeTool(call.tool, call.args);
    steps.push({
      index: i,
      type: 'tool',
      tool: call.tool,
      output: invoked.output,
      blocked: invoked.blocked,
      reason: invoked.reason,
    });

    messages.push({ role: 'assistant', content });
    messages.push({
      role: 'user',
      content: invoked.blocked
        ? `Tool ${call.tool} blocked: ${invoked.reason}. Continue with allowed tools or FINAL_ANSWER.`
        : `Tool ${call.tool} result:\n${JSON.stringify(invoked.output, null, 2)}`,
    });
  }

  return {
    ok: false,
    skillId: options.skillId,
    task: options.task,
    steps,
    finalAnswer: '',
    error: 'max_steps_exceeded',
  };
}
