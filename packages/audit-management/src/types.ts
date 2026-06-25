export type AuditType = "internal" | "external" | "regulatory" | "sox" | "iso27001" | "soc2";
export type AuditStatus = "planning" | "fieldwork" | "review" | "reporting" | "closed";
export type FindingSeverity = "critical" | "high" | "medium" | "low";
export type FindingStatus = "open" | "in_progress" | "remediated" | "verified" | "closed";

export interface Audit {
  id: string;
  name: string;
  type: AuditType;
  status: AuditStatus;
  scope: string[];
  framework: string;
  leadAuditor: string;
  team: string[];
  startDate: string;
  endDate: string;
  findings: Finding[];
  workpapers: Workpaper[];
  report?: AuditReport;
  createdAt: string;
}

export interface Finding {
  id: string;
  severity: FindingSeverity;
  status: FindingStatus;
  title: string;
  description: string;
  affectedControls: string[];
  evidence: string[];
  rootCause?: string;
  remediation?: string;
  remediationOwner?: string;
  dueDate?: string;
  remediatedAt?: string;
  verifiedAt?: string;
}

export interface Workpaper {
  id: string;
  controlId: string;
  description: string;
  evidence: string;
  conclusion: "satisfactory" | "needs_improvement" | "unsatisfactory";
  auditor: string;
  createdAt: string;
}

export interface AuditReport {
  id: string;
  executiveSummary: string;
  totalFindings: number;
  criticalFindings: number;
  highFindings: number;
  mediumFindings: number;
  lowFindings: number;
  overallOpinion: "unqualified" | "qualified" | "adverse" | "disclaimer";
  generatedAt: string;
}

export interface CAPA {
  id: string;
  findingId: string;
  type: "corrective" | "preventive";
  description: string;
  owner: string;
  dueDate: string;
  status: "open" | "in_progress" | "completed" | "verified";
  completedAt?: string;
}
