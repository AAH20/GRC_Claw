import { createHash, randomBytes, createHmac } from "node:crypto";
import type {
  SwarmAgent,
  SwarmTask,
  SwarmResult,
  AgentRole,
  AgentStatus,
  AgentCapability,
  TaskStatus,
  TrustSignature,
  ComplianceFramework,
} from "../types.js";

// ============================================================================
// Base Agent – shared signing, status, and execution plumbing
// ============================================================================

export abstract class BaseAgent implements SwarmAgent {
  readonly id: string;
  readonly role: AgentRole;
  readonly name: string;
  readonly version: string;
  readonly capabilities: AgentCapability[];
  readonly maxConcurrentTasks: number;

  trustScore: number;
  status: AgentStatus;
  currentTaskCount: number;

  private readonly signingKey: string;
  private previousHash: string = "0".repeat(64);

  constructor(
    role: AgentRole,
    name: string,
    version: string,
    capabilities: AgentCapability[],
    signingKey: string,
    options: { maxConcurrentTasks?: number; initialTrustScore?: number } = {},
  ) {
    this.id = `${role}-${randomBytes(4).toString("hex")}`;
    this.role = role;
    this.name = name;
    this.version = version;
    this.capabilities = capabilities;
    this.signingKey = signingKey;
    this.maxConcurrentTasks = options.maxConcurrentTasks ?? 5;
    this.trustScore = options.initialTrustScore ?? 1.0;
    this.status = "idle";
    this.currentTaskCount = 0;

    const executeCore = this.execute.bind(this);
    let overrideExecute: ((task: SwarmTask) => Promise<SwarmResult>) | null = null;
    let invokingOverride = false;

    const executeWrapper = async (task: SwarmTask): Promise<SwarmResult> => {
      if (overrideExecute && !invokingOverride) {
        invokingOverride = true;
        try {
          return await overrideExecute(task);
        } catch (err) {
          return this.buildFailedResult(task, err);
        } finally {
          invokingOverride = false;
        }
      }

      return executeCore(task);
    };

    Object.defineProperty(this, "execute", {
      configurable: true,
      get: () => executeWrapper,
      set: (nextExecute: (task: SwarmTask) => Promise<SwarmResult>) => {
        overrideExecute = nextExecute.bind(this);
      },
    });
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  async execute(task: SwarmTask): Promise<SwarmResult> {
    const startedAt = new Date().toISOString();
    this.status = "busy";
    this.currentTaskCount++;

    try {
      const output = await this.doExecute(task);
      const completedAt = new Date().toISOString();
      const outputHash = this.hash(JSON.stringify(output));
      const trustSignature = this.sign(task.id, outputHash);

      this.previousHash = trustSignature.contentHash;

      return {
        taskId: task.id,
        agentId: this.id,
        agentRole: this.role,
        status: "completed" as TaskStatus,
        output,
        trustSignature,
        executionTimeMs: new Date(completedAt).getTime() - new Date(startedAt).getTime(),
        startedAt,
        completedAt,
      };
    } catch (err) {
      return this.buildFailedResult(task, err, startedAt);
    } finally {
      this.currentTaskCount = Math.max(0, this.currentTaskCount - 1);
      this.status = this.currentTaskCount === 0 ? "idle" : "busy";
    }
  }

  canHandle(task: SwarmTask): boolean {
    if (task.assignedAgent && task.assignedAgent !== this.role) return false;
    if (this.status === "offline" || this.status === "error") return false;
    if (this.currentTaskCount >= this.maxConcurrentTasks) return false;
    return this.capabilities.some(
      (c) => c.frameworks.includes(task.framework) || c.frameworks.includes("Custom"),
    );
  }

  setOffline(): void {
    this.status = "offline";
  }

  setOnline(): void {
    this.status = "idle";
  }

  // ------------------------------------------------------------------
  // Signing & hashing
  // ------------------------------------------------------------------

  hash(data: string): string {
    return createHash("sha256").update(data).digest("hex");
  }

  private buildFailedResult(
    task: SwarmTask,
    err: unknown,
    startedAt: string = new Date().toISOString(),
  ): SwarmResult {
    const completedAt = new Date().toISOString();
    const errorMsg = err instanceof Error ? err.message : String(err);
    const errorHash = this.hash(errorMsg);
    const trustSignature = this.sign(task.id, errorHash);

    this.previousHash = trustSignature.contentHash;
    this.trustScore = Math.max(0, this.trustScore - 0.1);

    return {
      taskId: task.id,
      agentId: this.id,
      agentRole: this.role,
      status: "failed",
      output: { summary: `Agent ${this.role} failed: ${errorMsg}`, recommendations: [] },
      trustSignature,
      executionTimeMs: new Date(completedAt).getTime() - new Date(startedAt).getTime(),
      startedAt,
      completedAt,
      error: errorMsg,
    };
  }

  private sign(taskId: string, contentHash: string): TrustSignature {
    const timestamp = new Date().toISOString();
    const payload = `${taskId}:${this.id}:${contentHash}:${timestamp}:${this.previousHash}`;
    const signature = createHmac("sha256", this.signingKey).update(payload).digest("hex");
    const nonce = parseInt(randomBytes(4).toString("hex"), 16);

    return {
      agentId: this.id,
      agentRole: this.role,
      timestamp,
      contentHash,
      previousHash: this.previousHash,
      nonce,
      signature,
    };
  }

  // ------------------------------------------------------------------
  // Subclass hook
  // ------------------------------------------------------------------

  protected abstract doExecute(task: SwarmTask): Promise<SwarmResult["output"]>;
}
