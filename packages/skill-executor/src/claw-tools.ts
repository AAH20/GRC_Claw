import type { ToolDefinition } from '@grc-claw/agent-runtime';

/** OpenClaw-style claw.* tools for skill discovery and execution. */
export const CLAW_SKILL_TOOLS: ToolDefinition[] = [
  { name: 'claw.list_skills', tier: 'read' },
  { name: 'claw.get_skill', tier: 'read' },
  { name: 'claw.run_skill', tier: 'write' },
];

export function isClawTool(tool: string): boolean {
  return tool.startsWith('claw.');
}
