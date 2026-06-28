import { randomUUID } from 'node:crypto';
import { createHash } from 'node:crypto';

// ─── Channel Configuration ──────────────────────────────────────────

export type NotificationChannel = 'slack' | 'email' | 'teams';

export interface SlackConfig {
  webhookUrl: string;
  channel?: string;
  username?: string;
  iconEmoji?: string;
}

export interface EmailConfig {
  smtpHost: string;
  smtpPort: number;
  smtpUser: string;
  smtpPass: string;
  fromAddress: string;
  useTls?: boolean;
}

export interface TeamsConfig {
  webhookUrl: string;
}

export interface ChannelConfig {
  slack?: SlackConfig;
  email?: EmailConfig;
  teams?: TeamsConfig;
}

// ─── Notification Types ─────────────────────────────────────────────

export type NotificationSeverity = 'info' | 'warning' | 'critical';

export type NotificationTemplate =
  | 'compliance_alert'
  | 'drift_alert'
  | 'remediation_complete'
  | 'incident_created'
  | 'risk_threshold_exceeded'
  | 'custom';

export interface NotificationPayload {
  template: NotificationTemplate;
  severity: NotificationSeverity;
  title: string;
  message: string;
  channels: NotificationChannel[];
  data?: Record<string, unknown>;
  tags?: string[];
}

export interface ResolvedPayload {
  title: string;
  body: string;
  slack?: { text: string; blocks?: unknown[] };
  email?: { subject: string; html: string; text: string };
  teams?: { text: string; themeColor?: string; facts?: { name: string; value: string }[] };
}

// ─── Delivery Status ────────────────────────────────────────────────

export type DeliveryStatus = 'pending' | 'sent' | 'failed' | 'rate_limited' | 'retrying';

export interface DeliveryRecord {
  id: string;
  channel: NotificationChannel;
  status: DeliveryStatus;
  payload: NotificationPayload;
  resolvedPayload: ResolvedPayload;
  attempts: number;
  lastError?: string;
  createdAt: string;
  updatedAt: string;
  sentAt?: string;
}

// ─── Rate Limiting ──────────────────────────────────────────────────

export interface RateLimitConfig {
  maxPerMinute: number;
  maxPerHour: number;
  maxPerDay: number;
}

export interface RateLimitState {
  minuteCount: number;
  hourCount: number;
  dayCount: number;
  minuteWindowStart: number;
  hourWindowStart: number;
  dayWindowStart: number;
}

// ─── Retry Config ───────────────────────────────────────────────────

export interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

export const DEFAULT_RATE_LIMIT: RateLimitConfig = {
  maxPerMinute: 10,
  maxPerHour: 100,
  maxPerDay: 500,
};

export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 30000,
};

// ─── Helpers ────────────────────────────────────────────────────────

export function generateId(): string {
  return randomUUID();
}

export function hashData(data: string): string {
  return createHash('sha256').update(data).digest('hex');
}
