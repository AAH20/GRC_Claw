import { randomUUID } from "node:crypto";
import type {
  ComplianceTask,
  TaskStatus,
  TaskPriority,
  TaskType,
  TaskComment,
  TaskAttachment,
  TaskSLA,
  TaskNotification,
  TaskAnalytics,
  AssigneeLoad,
  TaskSearchFilter,
  AuditFinding,
  TaskFromFinding,
  NotificationTrigger,
} from "./types.js";
import { newId, nowIso } from "./types.js";

// ─── ComplianceTaskEngine ─────────────────────────────────────────────

export class ComplianceTaskEngine {
  private tasks: Map<string, ComplianceTask> = new Map();
  private findings: Map<string, AuditFinding> = new Map();

  // ─── Task CRUD ───────────────────────────────────────────────────

  createTask(input: {
    title: string;
    description: string;
    type: TaskType;
    priority: TaskPriority;
    assigneeId: string;
    assigneeName: string;
    assigneeEmail: string;
    framework: string;
    controlId?: string;
    controlTitle?: string;
    gapId?: string;
    auditFindingId?: string;
    dueDate: string;
    estimatedHours?: number;
    dependencies?: string[];
    tags?: string[];
    createdBy: string;
    slaWarningDays?: number;
    slaEscalationDays?: number;
  }): ComplianceTask {
    const id = newId();
    const now = nowIso();

    const sla: TaskSLA = {
      dueDate: input.dueDate,
      warningDaysBefore: input.slaWarningDays ?? 3,
      escalationDaysBefore: input.slaEscalationDays ?? 1,
      isEscalated: false,
    };

    const task: ComplianceTask = {
      id,
      title: input.title,
      description: input.description,
      type: input.type,
      status: "open",
      priority: input.priority,
      assigneeId: input.assigneeId,
      assigneeName: input.assigneeName,
      assigneeEmail: input.assigneeEmail,
      framework: input.framework,
      controlId: input.controlId,
      controlTitle: input.controlTitle,
      gapId: input.gapId,
      auditFindingId: input.auditFindingId,
      dueDate: input.dueDate,
      estimatedHours: input.estimatedHours,
      dependencies: input.dependencies ?? [],
      tags: input.tags ?? [],
      comments: [],
      attachments: [],
      sla,
      notifications: [],
      createdBy: input.createdBy,
      createdAt: now,
      updatedAt: now,
    };

    this.tasks.set(id, task);

    this.sendNotification(task, "created");
    this.sendNotification(task, "assigned");

    return task;
  }

  getTask(id: string): ComplianceTask | undefined {
    return this.tasks.get(id);
  }

  listTasks(): ComplianceTask[] {
    return Array.from(this.tasks.values());
  }

  updateTask(id: string, updates: Partial<Pick<ComplianceTask, "title" | "description" | "priority" | "dueDate" | "estimatedHours" | "tags">>): ComplianceTask {
    const task = this.tasks.get(id);
    if (!task) throw new Error(`Task ${id} not found`);

    if (updates.title) task.title = updates.title;
    if (updates.description) task.description = updates.description;
    if (updates.priority) task.priority = updates.priority;
    if (updates.dueDate) {
      task.dueDate = updates.dueDate;
      task.sla.dueDate = updates.dueDate;
    }
    if (updates.estimatedHours !== undefined) task.estimatedHours = updates.estimatedHours;
    if (updates.tags) task.tags = updates.tags;
    task.updatedAt = nowIso();

    return task;
  }

  deleteTask(id: string): boolean {
    return this.tasks.delete(id);
  }

  // ─── Status Transitions ──────────────────────────────────────────

  startTask(id: string): ComplianceTask {
    const task = this.tasks.get(id);
    if (!task) throw new Error(`Task ${id} not found`);
    if (task.status !== "open") throw new Error(`Task must be open to start (current: ${task.status})`);

    task.status = "in_progress";
    task.startedAt = nowIso();
    task.updatedAt = nowIso();
    this.sendNotification(task, "status_changed");

    return task;
  }

  completeTask(id: string): ComplianceTask {
    const task = this.tasks.get(id);
    if (!task) throw new Error(`Task ${id} not found`);
    if (task.status !== "in_progress") throw new Error(`Task must be in_progress to complete (current: ${task.status})`);

    for (const depId of task.dependencies) {
      const dep = this.tasks.get(depId);
      if (dep && dep.status !== "completed") {
        throw new Error(`Dependency task ${depId} is not completed`);
      }
    }

    task.status = "completed";
    task.completedAt = nowIso();
    task.updatedAt = nowIso();
    this.sendNotification(task, "completed");

    for (const [, t] of this.tasks) {
      if (t.dependencies.includes(id) && t.status === "blocked") {
        const allDepsMet = t.dependencies.every((dId) => {
          const d = this.tasks.get(dId);
          return d && d.status === "completed";
        });
        if (allDepsMet) {
          t.status = "open";
          this.sendNotification(t, "dependency_resolved");
        }
      }
    }

    return task;
  }

  blockTask(id: string, reason?: string): ComplianceTask {
    const task = this.tasks.get(id);
    if (!task) throw new Error(`Task ${id} not found`);

    task.status = "blocked";
    task.updatedAt = nowIso();
    if (reason) {
      task.comments.push({
        id: newId(),
        taskId: id,
        authorId: task.assigneeId,
        authorName: task.assigneeName,
        content: `Task blocked: ${reason}`,
        createdAt: nowIso(),
      });
    }
    this.sendNotification(task, "status_changed");

    return task;
  }

  cancelTask(id: string): ComplianceTask {
    const task = this.tasks.get(id);
    if (!task) throw new Error(`Task ${id} not found`);

    task.status = "cancelled";
    task.updatedAt = nowIso();

    return task;
  }

  // ─── Comments & Attachments ──────────────────────────────────────

  addComment(taskId: string, authorId: string, authorName: string, content: string): TaskComment {
    const task = this.tasks.get(taskId);
    if (!task) throw new Error(`Task ${taskId} not found`);

    const comment: TaskComment = {
      id: newId(),
      taskId,
      authorId,
      authorName,
      content,
      createdAt: nowIso(),
    };
    task.comments.push(comment);
    task.updatedAt = nowIso();
    this.sendNotification(task, "comment_added");

    return comment;
  }

  addAttachment(taskId: string, name: string, url: string, sha256: string, uploadedBy: string): TaskAttachment {
    const task = this.tasks.get(taskId);
    if (!task) throw new Error(`Task ${taskId} not found`);

    const attachment: TaskAttachment = {
      id: newId(),
      taskId,
      name,
      url,
      sha256,
      uploadedBy,
      uploadedAt: nowIso(),
    };
    task.attachments.push(attachment);
    task.updatedAt = nowIso();

    return attachment;
  }

  // ─── SLA Enforcement ────────────────────────────────────────────

  enforceSLA(): ComplianceTask[] {
    const now = new Date();
    const escalated: ComplianceTask[] = [];

    for (const task of this.tasks.values()) {
      if (task.status === "completed" || task.status === "cancelled") continue;

      const dueDate = new Date(task.dueDate);
      const daysUntilDue = (dueDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);

      if (daysUntilDue < 0 && !task.sla.breachedAt) {
        task.sla.breachedAt = nowIso();
        task.updatedAt = nowIso();
        this.sendNotification(task, "overdue");
      }

      if (daysUntilDue <= task.sla.escalationDaysBefore && !task.sla.isEscalated) {
        task.sla.isEscalated = true;
        task.sla.escalatedTo = task.assigneeId;
        task.sla.escalationEmail = task.assigneeEmail;
        task.updatedAt = nowIso();
        this.sendNotification(task, "escalated");
        escalated.push(task);
      }

      if (daysUntilDue <= task.sla.warningDaysBefore && daysUntilDue > task.sla.escalationDaysBefore) {
        this.sendNotification(task, "due_soon");
      }
    }

    return escalated;
  }

  // ─── Audit Finding Integration ───────────────────────────────────

  createTaskFromFinding(finding: AuditFinding): ComplianceTask {
    this.findings.set(finding.id, finding);

    const priorityMap: Record<string, TaskPriority> = {
      critical: "critical",
      high: "high",
      medium: "medium",
      low: "low",
    };

    return this.createTask({
      title: `Remediate: ${finding.title}`,
      description: finding.description + "\n\nRemediation: " + finding.remediation,
      type: "audit_finding",
      priority: priorityMap[finding.severity] ?? "medium",
      assigneeId: "unassigned",
      assigneeName: "Unassigned",
      assigneeEmail: "",
      framework: finding.framework,
      controlId: finding.controlId,
      controlTitle: finding.controlTitle,
      auditFindingId: finding.id,
      dueDate: finding.dueDate,
      createdBy: "system",
    });
  }

  createTasksFromFindings(findings: AuditFinding[]): TaskFromFinding[] {
    return findings.map((f) => ({
      findingId: f.id,
      tasks: [this.createTaskFromFinding(f).id],
    }));
  }

  // ─── Notifications ───────────────────────────────────────────────

  private sendNotification(task: ComplianceTask, trigger: NotificationTrigger): void {
    const messages: Record<NotificationTrigger, string> = {
      created: `Task "${task.title}" has been created.`,
      assigned: `You have been assigned to task "${task.title}".`,
      status_changed: `Task "${task.title}" status changed to ${task.status}.`,
      due_soon: `Task "${task.title}" is due within ${task.sla.warningDaysBefore} days.`,
      overdue: `Task "${task.title}" is overdue.`,
      escalated: `Task "${task.title}" has been escalated.`,
      completed: `Task "${task.title}" has been completed.`,
      dependency_resolved: `A dependency for task "${task.title}" has been resolved.`,
      comment_added: `New comment on task "${task.title}".`,
    };

    const notification: TaskNotification = {
      id: newId(),
      taskId: task.id,
      trigger,
      recipientId: task.assigneeId,
      recipientEmail: task.assigneeEmail,
      message: messages[trigger],
      createdAt: nowIso(),
    };
    task.notifications.push(notification);
  }

  getUnreadNotifications(assigneeId: string): TaskNotification[] {
    const result: TaskNotification[] = [];
    for (const task of this.tasks.values()) {
      for (const n of task.notifications) {
        if (n.recipientId === assigneeId && !n.readAt) {
          result.push(n);
        }
      }
    }
    return result;
  }

  markNotificationRead(notificationId: string): void {
    for (const task of this.tasks.values()) {
      for (const n of task.notifications) {
        if (n.id === notificationId) {
          n.readAt = nowIso();
          return;
        }
      }
    }
  }

  // ─── Search & Filter ──────────────────────────────────────────────

  searchTasks(filter: TaskSearchFilter): ComplianceTask[] {
    let results = Array.from(this.tasks.values());

    if (filter.query) {
      const q = filter.query.toLowerCase();
      results = results.filter(
        (t) =>
          t.title.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q) ||
          t.tags.some((tag) => tag.toLowerCase().includes(q))
      );
    }
    if (filter.status && filter.status.length > 0) {
      results = results.filter((t) => filter.status!.includes(t.status));
    }
    if (filter.priority && filter.priority.length > 0) {
      results = results.filter((t) => filter.priority!.includes(t.priority));
    }
    if (filter.type && filter.type.length > 0) {
      results = results.filter((t) => filter.type!.includes(t.type));
    }
    if (filter.framework && filter.framework.length > 0) {
      results = results.filter((t) => filter.framework!.includes(t.framework));
    }
    if (filter.assigneeId) {
      results = results.filter((t) => t.assigneeId === filter.assigneeId);
    }
    if (filter.tags && filter.tags.length > 0) {
      results = results.filter((t) => filter.tags!.some((tag) => t.tags.includes(tag)));
    }
    if (filter.dueBefore) {
      results = results.filter((t) => t.dueDate <= filter.dueBefore!);
    }
    if (filter.dueAfter) {
      results = results.filter((t) => t.dueDate >= filter.dueAfter!);
    }
    if (filter.isOverdue) {
      const now = new Date();
      results = results.filter((t) => new Date(t.dueDate) < now && t.status !== "completed" && t.status !== "cancelled");
    }

    return results;
  }

  // ─── Analytics ───────────────────────────────────────────────────

  getAnalytics(): TaskAnalytics {
    const tasks = this.listTasks();
    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    const byStatus: Record<TaskStatus, number> = { open: 0, in_progress: 0, completed: 0, blocked: 0, cancelled: 0 };
    const byPriority: Record<TaskPriority, number> = { critical: 0, high: 0, medium: 0, low: 0 };
    const byType: Record<TaskType, number> = { gap_remediation: 0, audit_finding: 0, evidence_collection: 0, control_update: 0, policy_review: 0, assessment: 0, custom: 0 };
    const byFramework: Record<string, number> = {};

    let totalCompletionDays = 0;
    let completedCount = 0;
    let overdueCount = 0;
    let slaCompliant = 0;
    let slaTotal = 0;
    let createdLast30 = 0;
    let completedLast30 = 0;
    let totalActualHours = 0;
    let hoursCount = 0;

    const assigneeMap = new Map<string, { totalTasks: number; openTasks: number; completedTasks: number; overdueTasks: number; totalDays: number; completedWithDays: number }>();

    for (const t of tasks) {
      byStatus[t.status]++;
      byPriority[t.priority]++;
      byType[t.type]++;
      byFramework[t.framework] = (byFramework[t.framework] ?? 0) + 1;

      if (t.status === "completed" && t.completedAt) {
        const days = (new Date(t.completedAt).getTime() - new Date(t.createdAt).getTime()) / (1000 * 60 * 60 * 24);
        totalCompletionDays += days;
        completedCount++;
      }

      if (new Date(t.dueDate) < now && t.status !== "completed" && t.status !== "cancelled") {
        overdueCount++;
      }

      if (t.status === "completed" || t.status === "cancelled") {
        slaTotal++;
        if (!t.sla.breachedAt) slaCompliant++;
      }

      if (new Date(t.createdAt) >= thirtyDaysAgo) createdLast30++;
      if (t.completedAt && new Date(t.completedAt) >= thirtyDaysAgo) completedLast30++;

      if (t.actualHours) {
        totalActualHours += t.actualHours;
        hoursCount++;
      }

      const load = assigneeMap.get(t.assigneeId) ?? { totalTasks: 0, openTasks: 0, completedTasks: 0, overdueTasks: 0, totalDays: 0, completedWithDays: 0 };
      load.totalTasks++;
      if (t.status === "open" || t.status === "in_progress" || t.status === "blocked") load.openTasks++;
      if (t.status === "completed") load.completedTasks++;
      if (new Date(t.dueDate) < now && t.status !== "completed" && t.status !== "cancelled") load.overdueTasks++;
      if (t.status === "completed" && t.completedAt) {
        load.totalDays += (new Date(t.completedAt).getTime() - new Date(t.createdAt).getTime()) / (1000 * 60 * 60 * 24);
        load.completedWithDays++;
      }
      assigneeMap.set(t.assigneeId, load);
    }

    const topAssignees: AssigneeLoad[] = Array.from(assigneeMap.entries())
      .map(([id, load]) => ({
        assigneeId: id,
        assigneeName: tasks.find((t) => t.assigneeId === id)?.assigneeName ?? id,
        totalTasks: load.totalTasks,
        openTasks: load.openTasks,
        completedTasks: load.completedTasks,
        overdueTasks: load.overdueTasks,
        averageCompletionDays: load.completedWithDays > 0 ? Math.round((load.totalDays / load.completedWithDays) * 100) / 100 : 0,
      }))
      .sort((a, b) => b.totalTasks - a.totalTasks);

    return {
      totalTasks: tasks.length,
      byStatus,
      byPriority,
      byType,
      byFramework,
      averageCompletionDays: completedCount > 0 ? Math.round((totalCompletionDays / completedCount) * 100) / 100 : 0,
      overdueRate: tasks.length > 0 ? Math.round((overdueCount / tasks.length) * 10000) / 100 : 0,
      slaComplianceRate: slaTotal > 0 ? Math.round((slaCompliant / slaTotal) * 10000) / 100 : 0,
      tasksCreatedLast30Days: createdLast30,
      tasksCompletedLast30Days: completedLast30,
      averageHoursToComplete: hoursCount > 0 ? Math.round((totalActualHours / hoursCount) * 100) / 100 : 0,
      topAssignees,
    };
  }

  // ─── Overdue Query ───────────────────────────────────────────────

  getOverdueTasks(): ComplianceTask[] {
    const now = new Date();
    return this.listTasks().filter(
      (t) => new Date(t.dueDate) < now && t.status !== "completed" && t.status !== "cancelled"
    );
  }

  // ─── Tasks by Framework / Control ────────────────────────────────

  getTasksByFramework(framework: string): ComplianceTask[] {
    return this.listTasks().filter((t) => t.framework === framework);
  }

  getTasksByControl(controlId: string): ComplianceTask[] {
    return this.listTasks().filter((t) => t.controlId === controlId);
  }

  getTasksByAssignee(assigneeId: string): ComplianceTask[] {
    return this.listTasks().filter((t) => t.assigneeId === assigneeId);
  }
}
