export type TriggerType = "schedule" | "event" | "manual";

export type TaskType =
  | "scan_controls"
  | "check_evidence"
  | "analyze_risk"
  | "generate_report";

export type ActionType =
  | "create_finding"
  | "update_status"
  | "send_notification"
  | "create_ticket";

export type AgentStatus = "idle" | "running" | "completed" | "failed" | "cancelled";
export type RunStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

// ─── Trigger ──────────────────────────────────────────────────────────

export interface Trigger {
  type: TriggerType;
  config: TriggerConfig;
}

export interface TriggerConfig {
  /** Cron expression for schedule triggers (e.g. "0 9 * * 1") */
  cron?: string;
  /** Event name for event triggers */
  eventName?: string;
  /** Webhook path for event triggers */
  webhookPath?: string;
  /** Manual trigger has no config needed */
  enabled?: boolean;
}

// ─── Task ─────────────────────────────────────────────────────────────

export interface Task {
  id: string;
  type: TaskType;
  label: string;
  params: Record<string, unknown>;
  dependsOn?: string[];
  timeoutMs?: number;
}

// ─── Action ───────────────────────────────────────────────────────────

export interface Action {
  id: string;
  type: ActionType;
  label: string;
  params: Record<string, unknown>;
  dependsOn?: string[];
}

// ─── Agent Definition ─────────────────────────────────────────────────

export interface AgentDefinition {
  id: string;
  name: string;
  description: string;
  version: string;
  trigger: Trigger;
  tasks: Task[];
  actions: Action[];
  tags: string[];
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

// ─── Agent Workflow (runtime) ─────────────────────────────────────────

export interface AgentWorkflow {
  id: string;
  agentId: string;
  agentName: string;
  status: AgentStatus;
  triggerType: TriggerType;
  context: Record<string, unknown>;
  taskResults: TaskResult[];
  actionResults: ActionResult[];
  startedAt: string;
  completedAt?: string;
  durationMs: number;
  error?: string;
}

// ─── Task Result ──────────────────────────────────────────────────────

export interface TaskResult {
  taskId: string;
  taskType: TaskType;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  startedAt: string;
  completedAt?: string;
  output: Record<string, unknown>;
  error?: string;
  durationMs: number;
}

// ─── Action Result ────────────────────────────────────────────────────

export interface ActionResult {
  actionId: string;
  actionType: ActionType;
  status: "pending" | "completed" | "failed" | "skipped";
  startedAt: string;
  completedAt?: string;
  output: Record<string, unknown>;
  error?: string;
  durationMs: number;
}

// ─── Agent Run ────────────────────────────────────────────────────────

export interface AgentRun {
  id: string;
  agentId: string;
  workflowId: string;
  status: RunStatus;
  triggeredBy: string;
  triggeredAt: string;
  completedAt?: string;
  context: Record<string, unknown>;
  summary: string;
}

// ─── Task Executor Interface ──────────────────────────────────────────

export interface TaskExecutor {
  execute(task: Task, context: Record<string, unknown>): Promise<Record<string, unknown>>;
}

// ─── Action Executor Interface ────────────────────────────────────────

export interface ActionExecutor {
  execute(action: Action, context: Record<string, unknown>): Promise<Record<string, unknown>>;
}

// ─── Agent Store Interface ────────────────────────────────────────────

export interface AgentStore {
  save(agent: AgentDefinition): void;
  get(id: string): AgentDefinition | undefined;
  list(): AgentDefinition[];
  delete(id: string): boolean;
}
