export type IncidentSeverity = "critical" | "high" | "medium" | "low";
export type IncidentStatus = "detected" | "triaged" | "contained" | "eradicated" | "recovered" | "closed";
export type IncidentType = "data_breach" | "malware" | "phishing" | "ransomware" | "insider_threat" | "ddos" | "unauthorized_access" | "system_outage" | "other";

export interface Incident {
  id: string;
  title: string;
  type: IncidentType;
  severity: IncidentSeverity;
  status: IncidentStatus;
  description: string;
  detectedAt: string;
  reportedBy: string;
  assignee: string;
  timeline: TimelineEntry[];
  evidence: IncidentEvidence[];
  impact: ImpactAssessment;
  notifications: Notification[];
  remediationSteps: string[];
  rootCause?: string;
  closedAt?: string;
  createdAt: string;
}

export interface TimelineEntry {
  timestamp: string;
  action: string;
  actor: string;
}

export interface IncidentEvidence {
  id: string;
  type: "log" | "screenshot" | "forensic_image" | "network_capture" | "email" | "file";
  name: string;
  sha256: string;
  collectedAt: string;
  chainOfCustody: ChainEntry[];
}

export interface ChainEntry {
  timestamp: string;
  action: string;
  person: string;
}

export interface ImpactAssessment {
  dataRecordsAffected: number;
  systemsAffected: string[];
  businessImpact: string;
  financialImpact: number;
  regulatoryNotificationRequired: boolean;
  notificationDeadline?: string;
  jurisdictions: string[];
}

export interface Notification {
  id: string;
  type: "regulatory" | "customer" | "board" | "law_enforcement" | "media";
  recipient: string;
  sentAt?: string;
  content: string;
  status: "pending" | "sent" | "acknowledged";
}

export interface IncidentStats {
  total: number;
  open: number;
  closed: number;
  bySeverity: Record<IncidentSeverity, number>;
  byType: Record<string, number>;
  avgResolutionDays: number;
}
