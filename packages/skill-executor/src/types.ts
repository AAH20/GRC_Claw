export interface SkillEntry {
  id: string;
  name: string;
  description: string;
  path: string;
  scope: 'grc_claw' | 'workspace';
}

export interface LoadedSkill extends SkillEntry {
  body: string;
  contentLength: number;
}

export interface SkillStepRecord {
  index: number;
  type: 'llm' | 'tool' | 'final';
  tool?: string;
  content?: string;
  output?: Record<string, unknown>;
  blocked?: boolean;
  reason?: string;
}

export interface SkillRunResult {
  ok: boolean;
  skillId: string;
  task: string;
  steps: SkillStepRecord[];
  finalAnswer: string;
  error?: string;
}

export type SkillToolInvoker = (
  tool: string,
  args: Record<string, unknown>
) => Promise<{ output: Record<string, unknown>; blocked?: boolean; reason?: string }>;

export interface SkillRunOptions {
  skillId: string;
  task: string;
  llmProviderId?: string;
  maxSteps?: number;
  /** When true, only read-tier tools are invoked inside the loop (default true). */
  readOnlyTools?: boolean;
}
