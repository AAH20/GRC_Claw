import { randomUUID } from "node:crypto";

// ─── Task Types ───────────────────────────────────────────────────────

export type TaskStatus = "open" | "in_progress" | "completed" | "blocked" | "cancelled";
export type TaskPriority = "critical" | "high" | "medium" | "low";
export type TaskType = "gap_remediation" | "audit_finding" | "evidence_collection" | "control_update" | "policy_review" | "assessment" | "custom";

export interface ComplianceTask {
  id: string;
  title: string;
  description: string;
  type: TaskType;
  status: TaskStatus;
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
  startedAt?: string;
  completedAt?: string;
  estimatedHours?: number;
  actualHours?: number;
  dependencies: string[];
  tags: string[];
  comments: TaskComment[];
  attachments: TaskAttachment[];
  sla: TaskSLA;
  notifications: TaskNotification[];
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface TaskComment {
  id: string;
  taskId: string;
  authorId: string;
  authorName: string;
  content: string;
  createdAt: string;
}

export interface TaskAttachment {
  id: string;
  taskId: string;
  name: string;
  url: string;
  sha256: string;
  uploadedBy: string;
  uploadedAt: string;
}

// ─── SLA ──────────────────────────────────────────────────────────────

export interface TaskSLA {
  dueDate: string;
  warningDaysBefore: number;
  escalationDaysBefore: number;
  escalatedTo?: string;
  escalationEmail?: string;
  breachedAt?: string;
  isEscalated: boolean;
}

// ─── Notifications ────────────────────────────────────────────────────

export type NotificationTrigger =
  | "created"
  | "assigned"
  | "status_changed"
  | "due_soon"
  | "overdue"
  | "escalated"
  | "completed"
  | "dependency_resolved"
  | "comment_added";

export interface TaskNotification {
  id: string;
  taskId: string;
  trigger: NotificationTrigger;
  recipientId: string;
  recipientEmail: string;
  message: string;
  sentAt?: string;
  readAt?: string;
  createdAt: string;
}

// ─── Analytics / Reporting ────────────────────────────────────────────

export interface TaskAnalytics {
  totalTasks: number;
  byStatus: Record<TaskStatus, number>;
  byPriority: Record<TaskPriority, number>;
  byType: Record<TaskType, number>;
  byFramework: Record<string, number>;
  averageCompletionDays: number;
  overdueRate: number;
  slaComplianceRate: number;
  tasksCreatedLast30Days: number;
  tasksCompletedLast30Days: number;
  averageHoursToComplete: number;
  topAssignees: AssigneeLoad[];
}

export interface AssigneeLoad {
  assigneeId: string;
  assigneeName: string;
  totalTasks: number;
  openTasks: number;
  completedTasks: number;
  overdueTasks: number;
  averageCompletionDays: number;
}

// ─── Audit Finding Integration ────────────────────────────────────────

export interface AuditFinding {
  id: string;
  findingNumber: string;
  title: string;
  description: string;
  severity: "critical" | "high" | "medium" | "low";
  controlId: string;
  controlTitle: string;
  framework: string;
  remediation: string;
  status: "open" | "in_progress" | "remediated" | "accepted";
  dueDate: string;
  createdAt: string;
}

export interface TaskFromFinding {
  findingId: string;
  tasks: string[];
}

// ─── Search / Filter ──────────────────────────────────────────────────

export interface TaskSearchFilter {
  query?: string;
  status?: TaskStatus[];
  priority?: TaskPriority[];
  type?: TaskType[];
  framework?: string[];
  assigneeId?: string;
  tags?: string[];
  dueBefore?: string;
  dueAfter?: string;
  createdBefore?: string;
  createdAfter?: string;
  isOverdue?: boolean;
}

// ─── Helpers ──────────────────────────────────────────────────────────

export function newId(): string {
  return randomUUID();
}

export function nowIso(): string {
  return new Date().toISOString();
}
