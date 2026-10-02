/**
 * Type definitions for the GRC Marketing TypeScript SDK.
 */

// ─── Enums ──────────────────────────────────────────────────────────────────

export enum CampaignStatus {
  DRAFT = "draft",
  ACTIVE = "active",
  PAUSED = "paused",
  COMPLETED = "completed",
  ARCHIVED = "archived",
}

export enum LeadStatus {
  NEW = "new",
  CONTACTED = "contacted",
  QUALIFIED = "qualified",
  CONVERTED = "converted",
  LOST = "lost",
}

export enum JourneyStatus {
  DRAFT = "draft",
  ACTIVE = "active",
  PAUSED = "paused",
  COMPLETED = "completed",
}

export enum Channel {
  EMAIL = "email",
  SMS = "sms",
  PUSH = "push",
  SOCIAL = "social",
  WEB = "web",
}

// ─── Payload types ──────────────────────────────────────────────────────────

export interface CampaignCreatePayload {
  name: string;
  description?: string;
  channel?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  budget?: number;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface CampaignUpdatePayload {
  name?: string;
  description?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  budget?: number;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface LeadCreatePayload {
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  company?: string;
  source?: string;
  status?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface LeadUpdatePayload {
  email?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  company?: string;
  source?: string;
  status?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface JourneyCreatePayload {
  name: string;
  description?: string;
  status?: string;
  steps?: Record<string, unknown>[];
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface JourneyUpdatePayload {
  name?: string;
  description?: string;
  status?: string;
  steps?: Record<string, unknown>[];
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface AnalyticsQuery {
  start_date?: string;
  end_date?: string;
  metrics?: string[];
  dimensions?: string[];
  filters?: Record<string, unknown>;
}

export interface PaginationParams {
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: string;
}

export interface ListResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// ─── Entity types ───────────────────────────────────────────────────────────

export interface Campaign {
  id: string;
  name: string;
  description: string;
  channel: Channel;
  status: CampaignStatus;
  start_date?: string;
  end_date?: string;
  budget: number;
  tags: string[];
  metadata: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface Lead {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  company: string;
  source: string;
  status: LeadStatus;
  tags: string[];
  metadata: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface Journey {
  id: string;
  name: string;
  description: string;
  status: JourneyStatus;
  steps: Record<string, unknown>[];
  tags: string[];
  metadata: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface AnalyticsReport {
  metrics: Record<string, unknown>;
  dimensions: Record<string, unknown>;
  start_date?: string;
  end_date?: string;
  total_records: number;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  scope?: string;
  obtained_at: string;
}
