import * as crypto from "crypto";
import { listFrameworkPacks } from "@grc-claw/frameworks";
import { EvidenceStore } from "@grc-claw/evidence";
import { SecurityGraph } from "@grc-claw/security-graph";
import { BoardReportGenerator } from "@grc-claw/board-reporting";
import type {
  AgentDefinition,
  AgentWorkflow,
  AgentRun,
  Task,
  Action,
  TaskResult,
  ActionResult,
  TaskExecutor,
  ActionExecutor,
  AgentStore,
} from "./types.js";
import { PREBUILT_AGENTS } from "./prebuilt/index.js";

// ─── Built-in Task Executors ──────────────────────────────────────────

export class ScanControlsExecutor implements TaskExecutor {
  async execute(task: Task, _context: Record<string, unknown>): Promise<Record<string, unknown>> {
    const frameworkFilter = String(task.params.frameworks ?? "").split(",").filter(Boolean);
    const packs = listFrameworkPacks();
    const filteredPacks = frameworkFilter.length > 0
      ? packs.filter((p) => frameworkFilter.includes(p.code))
      : packs;

    let totalControls = 0;
    let compliant = 0;
    let nonCompliant = 0;
    let partialCompliance = 0;
    const evidenceStore = (_context.evidence as EvidenceStore) ?? new EvidenceStore();

    for (const pack of filteredPacks) {
      for (const ctrl of pack.controls) {
        totalControls++;
        const items = evidenceStore.listByControl(ctrl.id);
        if (items.length > 0) {
          compliant++;
        } else {
          nonCompliant++;
          partialCompliance++;
        }
      }
    }

    return {
      frameworks: filteredPacks.map((p) => p.code),
      scope: String(task.params.scope ?? "all"),
      controlsScanned: totalControls,
      compliant,
      nonCompliant,
      partialCompliance,
      scanTimestamp: new Date().toISOString(),
    };
  }
}

export class CheckEvidenceExecutor implements TaskExecutor {
  async execute(task: Task, _context: Record<string, unknown>): Promise<Record<string, unknown>> {
    const evidenceType = String(task.params.evidenceType ?? "all");
    const freshnessDays = Number(task.params.freshnessDays ?? 365);
    const evidenceStore = (_context.evidence as EvidenceStore) ?? new EvidenceStore();
    const packs = listFrameworkPacks();

    let totalEvidence = 0;
    let validEvidence = 0;
    const cutoffMs = freshnessDays * 86_400_000;
    const now = Date.now();

    for (const pack of packs) {
      for (const ctrl of pack.controls) {
        const items = evidenceStore.listByControl(ctrl.id);
        for (const item of items) {
          totalEvidence++;
          const age = now - new Date(item.collectedAt).getTime();
          if (age <= cutoffMs) validEvidence++;
        }
      }
    }

    const staleEvidence = totalEvidence - validEvidence;

    return {
      evidenceType,
      freshnessDays,
      totalEvidence,
      validEvidence,
      staleEvidence,
      completenessScore: totalEvidence > 0 ? validEvidence / totalEvidence : 1,
      checkedAt: new Date().toISOString(),
    };
  }
}

export class AnalyzeRiskExecutor implements TaskExecutor {
  async execute(task: Task, _context: Record<string, unknown>): Promise<Record<string, unknown>> {
    const model = String(task.params.model ?? "default");
    const graph = (_context.securityGraph as SecurityGraph) ?? new SecurityGraph();
    const agentDid = String(_context.agentDid ?? "did:grc:agent-default");
    const assessment = graph.assessAgentRisk(agentDid);

    return {
      model,
      overallRisk: assessment.overallRisk,
      criticalRisks: assessment.riskFactors.filter((f) => f.score >= 30).length,
      highRisks: assessment.riskFactors.filter((f) => f.score >= 15 && f.score < 30).length,
      recommendations: assessment.recommendedActions,
      riskScore: assessment.overallRisk,
      riskFactors: assessment.riskFactors,
      analyzedAt: new Date().toISOString(),
    };
  }
}

export class GenerateReportExecutor implements TaskExecutor {
  async execute(task: Task, _context: Record<string, unknown>): Promise<Record<string, unknown>> {
    const format = String(task.params.format ?? "summary");
    const reportType = (String(task.params.reportType ?? "board_summary") as import("@grc-claw/board-reporting").ReportType) ?? "board_summary";
    const generator = new BoardReportGenerator();
    const period = String(task.params.period ?? new Date().toISOString().slice(0, 7));
    const report = generator.generateReport(reportType, period);

    return {
      reportId: report.id,
      title: report.title,
      type: report.type,
      format,
      period,
      generatedAt: report.generatedAt,
      sections: report.sections.map((s) => s.title),
      summary: report.summary,
      recommendations: report.recommendations,
      pageCount: format === "detailed" ? report.sections.length * 3 : report.sections.length,
    };
  }
}

// ─── Built-in Action Executors ────────────────────────────────────────

export class CreateFindingExecutor implements ActionExecutor {
  async execute(action: Action, _context: Record<string, unknown>): Promise<Record<string, unknown>> {
    const findingId = `FIND-${Date.now().toString(36).toUpperCase()}`;
    return {
      findingId,
      severity: action.params.severity ?? "medium",
      category: action.params.category ?? "general",
      status: "open",
      createdAt: new Date().toISOString(),
    };
  }
}

export class UpdateStatusExecutor implements ActionExecutor {
  async execute(action: Action, _context: Record<string, unknown>): Promise<Record<string, unknown>> {
    return {
      field: action.params.statusField ?? action.params.field ?? "status",
      newValue: action.params.value ?? "updated",
      updatedAt: new Date().toISOString(),
      updatedBy: "agent-builder",
    };
  }
}

export class SendNotificationExecutor implements ActionExecutor {
  async execute(action: Action, _context: Record<string, unknown>): Promise<Record<string, unknown>> {
    const channel = String(action.params.channel ?? "#general");
    return {
      channel,
      sent: true,
      notificationId: `notif-${crypto.randomUUID().substring(0, 8)}`,
      timestamp: new Date().toISOString(),
    };
  }
}

export class CreateTicketExecutor implements ActionExecutor {
  async execute(action: Action, _context: Record<string, unknown>): Promise<Record<string, unknown>> {
    const ticketKey = `${action.params.project ?? "OPS"}-${Date.now().toString(36).toUpperCase()}`;
    return {
      ticketKey,
      project: action.params.project ?? "OPS",
      type: action.params.type ?? "task",
      priority: action.params.priority ?? "Medium",
      status: "Created",
      createdAt: new Date().toISOString(),
    };
  }
}

// ─── Default Executors ────────────────────────────────────────────────

const DEFAULT_TASK_EXECUTORS: Record<string, TaskExecutor> = {
  scan_controls: new ScanControlsExecutor(),
  check_evidence: new CheckEvidenceExecutor(),
  analyze_risk: new AnalyzeRiskExecutor(),
  generate_report: new GenerateReportExecutor(),
};

const DEFAULT_ACTION_EXECUTORS: Record<string, ActionExecutor> = {
  create_finding: new CreateFindingExecutor(),
  update_status: new UpdateStatusExecutor(),
  send_notification: new SendNotificationExecutor(),
  create_ticket: new CreateTicketExecutor(),
};

// ─── In-Memory Agent Store ────────────────────────────────────────────

class InMemoryAgentStore implements AgentStore {
  private agents: Map<string, AgentDefinition> = new Map();

  save(agent: AgentDefinition): void {
    this.agents.set(agent.id, agent);
  }

  get(id: string): AgentDefinition | undefined {
    return this.agents.get(id);
  }

  list(): AgentDefinition[] {
    return Array.from(this.agents.values());
  }

  delete(id: string): boolean {
    return this.agents.delete(id);
  }
}

// ─── Agent Builder ────────────────────────────────────────────────────

export interface AgentBuilderConfig {
  defaultTimeoutMs: number;
  maxConcurrentRuns: number;
  evidenceRequired: boolean;
}

const DEFAULT_BUILDER_CONFIG: AgentBuilderConfig = {
  defaultTimeoutMs: 60_000,
  maxConcurrentRuns: 10,
  evidenceRequired: true,
};

export class AgentBuilder {
  private store: AgentStore;
  private taskExecutors: Map<string, TaskExecutor>;
  private actionExecutors: Map<string, ActionExecutor>;
  private runs: Map<string, AgentRun> = new Map();
  private workflows: Map<string, AgentWorkflow> = new Map();
  private config: AgentBuilderConfig;

  constructor(config: Partial<AgentBuilderConfig> = {}) {
    this.config = { ...DEFAULT_BUILDER_CONFIG, ...config };
    this.store = new InMemoryAgentStore();
    this.taskExecutors = new Map(Object.entries(DEFAULT_TASK_EXECUTORS));
    this.actionExecutors = new Map(Object.entries(DEFAULT_ACTION_EXECUTORS));

    // Register pre-built agents
    for (const agent of PREBUILT_AGENTS) {
      this.store.save(agent);
    }
  }

  /** Register a custom task executor */
  registerTaskExecutor(type: string, executor: TaskExecutor): void {
    this.taskExecutors.set(type, executor);
  }

  /** Register a custom action executor */
  registerActionExecutor(type: string, executor: ActionExecutor): void {
    this.actionExecutors.set(type, executor);
  }

  /** Create a new agent from a definition */
  createAgent(definition: AgentDefinition): AgentDefinition {
    const agent: AgentDefinition = {
      ...definition,
      id: definition.id || `agent-${crypto.randomUUID().substring(0, 12)}`,
      createdAt: definition.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // Validate the definition
    this.validateDefinition(agent);

    this.store.save(agent);
    return agent;
  }

  /** List all defined agents */
  listAgents(): AgentDefinition[] {
    return this.store.list();
  }

  /** Get agent by ID */
  getAgent(id: string): AgentDefinition | undefined {
    return this.store.get(id);
  }

  /** Delete an agent */
  deleteAgent(id: string): boolean {
    return this.store.delete(id);
  }

  /** Trigger an agent run with context */
  async triggerAgent(id: string, context: Record<string, unknown> = {}): Promise<AgentRun> {
    const agent = this.store.get(id);
    if (!agent) throw new Error(`Agent not found: ${id}`);
    if (!agent.enabled) throw new Error(`Agent is disabled: ${id}`);

    const runId = `run-${crypto.randomUUID().substring(0, 12)}`;
    const workflowId = `wf-${crypto.randomUUID().substring(0, 12)}`;

    const run: AgentRun = {
      id: runId,
      agentId: id,
      workflowId,
      status: "running",
      triggeredBy: "manual",
      triggeredAt: new Date().toISOString(),
      context,
      summary: "",
    };

    this.runs.set(runId, run);

    const workflow: AgentWorkflow = {
      id: workflowId,
      agentId: id,
      agentName: agent.name,
      status: "running",
      triggerType: agent.trigger.type,
      context,
      taskResults: [],
      actionResults: [],
      startedAt: new Date().toISOString(),
      durationMs: 0,
    };

    this.workflows.set(workflowId, workflow);

    try {
      // Execute tasks in dependency order
      await this.executeTasks(agent, workflow);

      // Execute actions in dependency order
      await this.executeActions(agent, workflow);

      const duration = Date.now() - new Date(workflow.startedAt).getTime();
      workflow.durationMs = duration;
      workflow.completedAt = new Date().toISOString();
      workflow.status = "completed";

      run.status = "completed";
      run.completedAt = new Date().toISOString();
      run.summary = `Agent ${agent.name} completed: ${workflow.taskResults.length} tasks, ${workflow.actionResults.length} actions executed.`;
    } catch (err) {
      workflow.status = "failed";
      workflow.error = err instanceof Error ? err.message : String(err);
      workflow.completedAt = new Date().toISOString();

      run.status = "failed";
      run.completedAt = new Date().toISOString();
      run.summary = `Agent ${agent.name} failed: ${workflow.error}`;
    }

    return run;
  }

  /** Get a run by ID */
  getRun(id: string): AgentRun | undefined {
    return this.runs.get(id);
  }

  /** Get all runs for an agent */
  getAgentRuns(agentId: string): AgentRun[] {
    return Array.from(this.runs.values()).filter((r) => r.agentId === agentId);
  }

  /** Get workflow by ID */
  getWorkflow(id: string): AgentWorkflow | undefined {
    return this.workflows.get(id);
  }

  // ─── Private Helpers ──────────────────────────────────────────────

  private validateDefinition(agent: AgentDefinition): void {
    if (!agent.name || agent.name.trim().length === 0) {
      throw new Error("Agent definition must have a name");
    }
    if (!agent.trigger || !agent.trigger.type) {
      throw new Error("Agent definition must have a trigger");
    }
    if (!Array.isArray(agent.tasks)) {
      throw new Error("Agent definition must have a tasks array");
    }
    if (!Array.isArray(agent.actions)) {
      throw new Error("Agent definition must have an actions array");
    }

    // Validate task dependencies
    const taskIds = new Set(agent.tasks.map((t) => t.id));
    for (const task of agent.tasks) {
      if (task.dependsOn) {
        for (const dep of task.dependsOn) {
          if (!taskIds.has(dep)) {
            throw new Error(`Task ${task.id} depends on unknown task: ${dep}`);
          }
        }
      }
    }

    // Validate action dependencies
    const actionIds = new Set(agent.actions.map((a) => a.id));
    for (const action of agent.actions) {
      if (action.dependsOn) {
        for (const dep of action.dependsOn) {
          if (!actionIds.has(dep)) {
            throw new Error(`Action ${action.id} depends on unknown action: ${dep}`);
          }
        }
      }
    }
  }

  private async executeTasks(agent: AgentDefinition, workflow: AgentWorkflow): Promise<void> {
    const completedTasks = new Set<string>();

    // Topological sort based on dependencies
    const sortedTasks = this.topologicalSortTasks(agent.tasks);

    for (const task of sortedTasks) {
      // Check dependencies
      if (task.dependsOn && task.dependsOn.length > 0) {
        const allDepsMet = task.dependsOn.every((dep) => completedTasks.has(dep));
        if (!allDepsMet) {
          workflow.taskResults.push({
            taskId: task.id,
            taskType: task.type,
            status: "skipped",
            startedAt: new Date().toISOString(),
            output: { reason: "dependency_not_met" },
            durationMs: 0,
          });
          continue;
        }
      }

      const executor = this.taskExecutors.get(task.type);
      if (!executor) {
        workflow.taskResults.push({
          taskId: task.id,
          taskType: task.type,
          status: "failed",
          startedAt: new Date().toISOString(),
          output: {},
          error: `No executor for task type: ${task.type}`,
          durationMs: 0,
        });
        continue;
        }

      const startMs = Date.now();
      const result: TaskResult = {
        taskId: task.id,
        taskType: task.type,
        status: "running",
        startedAt: new Date(startMs).toISOString(),
        output: {},
        durationMs: 0,
      };

      try {
        const output = await executor.execute(task, workflow.context);
        result.output = output;
        result.status = "completed";
        completedTasks.add(task.id);
      } catch (err) {
        result.error = err instanceof Error ? err.message : String(err);
        result.status = "failed";
      }

      result.completedAt = new Date().toISOString();
      result.durationMs = Date.now() - startMs;
      workflow.taskResults.push(result);
    }
  }

  private async executeActions(agent: AgentDefinition, workflow: AgentWorkflow): Promise<void> {
    const completedActions = new Set<string>();

    const sortedActions = this.topologicalSortActions(agent.actions);

    for (const action of sortedActions) {
      // Check dependencies (can depend on other actions)
      if (action.dependsOn && action.dependsOn.length > 0) {
        const allDepsMet = action.dependsOn.every((dep) => completedActions.has(dep));
        if (!allDepsMet) {
          workflow.actionResults.push({
            actionId: action.id,
            actionType: action.type,
            status: "skipped",
            startedAt: new Date().toISOString(),
            output: { reason: "dependency_not_met" },
            durationMs: 0,
          });
          continue;
        }
      }

      const executor = this.actionExecutors.get(action.type);
      if (!executor) {
        workflow.actionResults.push({
          actionId: action.id,
          actionType: action.type,
          status: "failed",
          startedAt: new Date().toISOString(),
          output: {},
          error: `No executor for action type: ${action.type}`,
          durationMs: 0,
        });
        continue;
      }

      const startMs = Date.now();
      const result: ActionResult = {
        actionId: action.id,
        actionType: action.type,
        status: "completed",
        startedAt: new Date(startMs).toISOString(),
        output: {},
        durationMs: 0,
      };

      try {
        result.output = await executor.execute(action, workflow.context);
        completedActions.add(action.id);
      } catch (err) {
        result.error = err instanceof Error ? err.message : String(err);
        result.status = "failed";
      }

      result.completedAt = new Date().toISOString();
      result.durationMs = Date.now() - startMs;
      workflow.actionResults.push(result);
    }
  }

  private topologicalSortTasks(tasks: Task[]): Task[] {
    const taskMap = new Map(tasks.map((t) => [t.id, t]));
    const visited = new Set<string>();
    const sorted: Task[] = [];

    const visit = (task: Task) => {
      if (visited.has(task.id)) return;
      visited.add(task.id);

      if (task.dependsOn) {
        for (const depId of task.dependsOn) {
          const dep = taskMap.get(depId);
          if (dep) visit(dep);
        }
      }

      sorted.push(task);
    };

    for (const task of tasks) {
      visit(task);
    }

    return sorted;
  }

  private topologicalSortActions(actions: Action[]): Action[] {
    const actionMap = new Map(actions.map((a) => [a.id, a]));
    const visited = new Set<string>();
    const sorted: Action[] = [];

    const visit = (action: Action) => {
      if (visited.has(action.id)) return;
      visited.add(action.id);

      if (action.dependsOn) {
        for (const depId of action.dependsOn) {
          const dep = actionMap.get(depId);
          if (dep) visit(dep);
        }
      }

      sorted.push(action);
    };

    for (const action of actions) {
      visit(action);
    }

    return sorted;
  }
}
