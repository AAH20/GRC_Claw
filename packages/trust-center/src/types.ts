export type TrustItemType = "certification" | "audit_report" | "security_control" | "privacy_policy" | "subprocessor" | "uptime_sla" | "penetration_test" | "bug_bounty";
export type TrustItemStatus = "active" | "expired" | "pending" | "in_review";

export interface TrustItem {
  id: string;
  type: TrustItemType;
  name: string;
  description: string;
  status: TrustItemStatus;
  documentUrl?: string;
  issuedAt?: string;
  expiresAt?: string;
  framework?: string;
  summary: string;
  order: number;
}

export interface TrustPage {
  id: string;
  slug: string;
  companyName: string;
  logoUrl?: string;
  items: TrustItem[];
  customHtml?: string;
  publishedAt?: string;
  isPublic: boolean;
}

export interface SecurityQuestion {
  id: string;
  question: string;
  category: string;
  autoAnswered: boolean;
  response: string;
  confidence: number;
  evidenceUrl?: string;
}

export interface QuestionnaireTemplate {
  id: string;
  name: string;
  framework: string;
  questions: string[];
}
