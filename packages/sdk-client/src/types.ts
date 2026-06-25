export interface GrcClientConfig {
  baseUrl: string;
  token: string;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

export interface SecurityEvent {
  eventUuid: string;
  eventType: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  sourceSystem: string;
  tenantId: number;
  eventData: Record<string, unknown>;
  timestamp?: string;
}

export interface ComplianceResult {
  framework: string;
  score: number;
  controls: { controlId: string; status: string; evidence?: string }[];
}

export interface AuditReport {
  id: string;
  framework: string;
  status: 'draft' | 'in_progress' | 'completed' | 'failed';
  findings: Finding[];
  createdAt: string;
  updatedAt: string;
}

export interface Finding {
  id: string;
  severity: string;
  description: string;
  control: string;
  recommendation?: string;
  status: 'open' | 'remediated' | 'accepted';
}

export interface Vendor {
  id: string;
  name: string;
  riskScore: number;
  status: 'pending' | 'approved' | 'rejected' | 'under_review';
  services: string[];
  createdAt: string;
}

export interface TrustPage {
  id: string;
  slug: string;
  company: string;
  published: boolean;
  publishedAt?: string;
  createdAt: string;
}

export interface Incident {
  id: string;
  title: string;
  severity: string;
  status: 'open' | 'investigating' | 'contained' | 'resolved' | 'closed';
  reportedAt: string;
  updatedAt: string;
}

export interface Policy {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'draft' | 'archived';
  createdAt: string;
  updatedAt: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface ApiResponse<T> {
  ok: boolean;
  data?: T;
  error?: string;
  message?: string;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
