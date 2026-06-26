export type PolicyStatus = "draft" | "under_review" | "approved" | "published" | "archived";
export type PolicyCategory = "security" | "privacy" | "compliance" | "operational" | "hr" | "financial";

export interface Policy {
  id: string;
  title: string;
  category: PolicyCategory;
  version: number;
  status: PolicyStatus;
  owner: string;
  approver: string;
  content: string;
  framework: string;
  effectiveDate: string;
  reviewDate: string;
  changeLog: PolicyChange[];
  attestations: Attestation[];
  createdAt: string;
  updatedAt: string;
}

export interface PolicyChange {
  version: number;
  changedBy: string;
  changedAt: string;
  summary: string;
}

export interface Attestation {
  id: string;
  employeeId: string;
  employeeName: string;
  acknowledgedAt: string;
  attestedVersion: number;
}

export interface PolicyTemplate {
  id: string;
  name: string;
  category: PolicyCategory;
  framework: string;
  content: string;
  isDefault: boolean;
  frameworkMappings?: string[];
  requiredSections?: string[];
}

export interface PolicyStats {
  totalPolicies: number;
  byStatus: Record<PolicyStatus, number>;
  byCategory: Record<PolicyCategory, number>;
  upcomingReviews: number;
  attestationsPending: number;
}
