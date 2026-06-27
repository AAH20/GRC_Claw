import { randomUUID } from "node:crypto";

// ─── Policy Lifecycle ─────────────────────────────────────────────────

export type PolicyStatus =
  | "draft"
  | "under_review"
  | "approved"
  | "published"
  | "under_attestation"
  | "revision_needed";

export type PolicyCategory =
  | "security"
  | "privacy"
  | "compliance"
  | "operational"
  | "hr"
  | "financial"
  | "it"
  | "safety";

export type ApprovalStatus = "pending" | "approved" | "rejected" | "escalated";
export type AttestationStatus = "pending" | "attested" | "overdue";

// ─── Core Policy ──────────────────────────────────────────────────────

export interface Policy {
  id: string;
  title: string;
  slug: string;
  category: PolicyCategory;
  status: PolicyStatus;
  version: number;
  content: string;
  summary: string;
  owner: string;
  department: string;
  framework: string;
  effectiveDate: string;
  reviewDate: string;
  nextReviewDate: string;
  approvalChain: ApprovalStep[];
  changeHistory: PolicyChange[];
  attestations: Attestation[];
  controlMappings: PolicyControlMapping[];
  evidenceIds: string[];
  tags: string[];
  createdAt: string;
  updatedAt: string;
  publishedAt?: string;
  archivedAt?: string;
}

export interface PolicyChange {
  id: string;
  version: number;
  changedBy: string;
  changedAt: string;
  summary: string;
  diff?: string;
  previousContent?: string;
}

export interface PolicyControlMapping {
  controlId: string;
  framework: string;
  controlTitle: string;
  mappedAt: string;
  mappedBy: string;
}

// ─── Approval Workflow ────────────────────────────────────────────────

export interface ApprovalStep {
  id: string;
  order: number;
  assigneeId: string;
  assigneeName: string;
  role: string;
  status: ApprovalStatus;
  comments?: string;
  decidedAt?: string;
  deadline?: string;
}

export interface ApprovalWorkflow {
  id: string;
  policyId: string;
  steps: ApprovalStep[];
  currentStep: number;
  initiatedBy: string;
  initiatedAt: string;
  completedAt?: string;
  isComplete: boolean;
}

// ─── Attestation ──────────────────────────────────────────────────────

export interface Attestation {
  id: string;
  policyId: string;
  policyVersion: number;
  employeeId: string;
  employeeName: string;
  employeeEmail: string;
  department: string;
  status: AttestationStatus;
  attestedAt?: string;
  dueDate: string;
  reminderCount: number;
  lastReminderAt?: string;
  createdAt: string;
}

// ─── Templates ────────────────────────────────────────────────────────

export interface PolicyTemplate {
  id: string;
  name: string;
  category: PolicyCategory;
  framework: string;
  description: string;
  content: string;
  sections: string[];
  tags: string[];
  isDefault: boolean;
  version: number;
  createdAt: string;
}

// ─── Search / Filter ──────────────────────────────────────────────────

export interface PolicySearchFilter {
  query?: string;
  status?: PolicyStatus[];
  category?: PolicyCategory[];
  framework?: string[];
  owner?: string;
  department?: string;
  tags?: string[];
  effectiveBefore?: string;
  effectiveAfter?: string;
  reviewBefore?: string;
  reviewAfter?: string;
}

// ─── Stats ────────────────────────────────────────────────────────────

export interface PolicyHubStats {
  totalPolicies: number;
  byStatus: Record<PolicyStatus, number>;
  byCategory: Record<PolicyCategory, number>;
  upcomingReviews: number;
  overdueReviews: number;
  pendingAttestations: number;
  overdueAttestations: number;
  pendingApprovals: number;
  averageApprovalTimeHours: number;
}

// ─── Events ───────────────────────────────────────────────────────────

export type PolicyEventKind =
  | "policy_created"
  | "policy_submitted_for_review"
  | "policy_approved"
  | "policy_rejected"
  | "policy_published"
  | "policy_revision_requested"
  | "policy_archived"
  | "attestation_assigned"
  | "attestation_completed"
  | "attestation_overdue"
  | "approval_step_completed";

export interface PolicyEvent {
  id: string;
  kind: PolicyEventKind;
  policyId: string;
  actor: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

// ─── Helpers ──────────────────────────────────────────────────────────

export function newId(): string {
  return randomUUID();
}

export function nowIso(): string {
  return new Date().toISOString();
}
