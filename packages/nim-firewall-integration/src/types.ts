export interface NimRequest {
  model: string;
  prompt: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
  metadata?: Record<string, unknown>;
  requestId?: string;
  timestamp?: string;
}

export interface NimResponse {
  text: string;
  tokens: { prompt: number; completion: number };
  latency: number;
  model: string;
  finishReason: 'stop' | 'length' | 'safety' | 'error';
  requestId?: string;
  timestamp?: string;
}

export interface FirewallDecision {
  allowed: boolean;
  reason: string;
  sandbox: boolean;
  requiresApproval: boolean;
  receiptHash: string;
  violations: PolicyViolation[];
  riskScore: number;
  timestamp: string;
  requestId: string;
}

export interface PolicyViolation {
  ruleId: string;
  ruleName: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  detail: string;
}

export interface PolicyRule {
  id: string;
  name: string;
  conditions: PolicyCondition[];
  action: PolicyAction;
  priority: number;
  enabled?: boolean;
}

export interface PolicyCondition {
  field: string;
  operator: 'equals' | 'contains' | 'matches' | 'gt' | 'lt' | 'in' | 'regex';
  value: unknown;
}

export type PolicyAction = 'allow' | 'block' | 'sandbox' | 'approve' | 'redact' | 'log';

export interface DataBoundary {
  type: 'CUI' | 'PHI' | 'PCI' | 'PII';
  classification: string;
  allowedModels: string[];
  requiresSandbox: boolean;
  requiresApproval: boolean;
  redactionPatterns: string[];
}

export interface InjectionDetectionResult {
  detected: boolean;
  score: number;
  patterns: string[];
  action: 'allow' | 'flag' | 'block';
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  requestId: string;
  request: NimRequest;
  response?: NimResponse;
  decision: FirewallDecision;
  injectedAt?: string;
}

export interface TrustReceipt {
  hash: string;
  previousHash: string;
  timestamp: string;
  requestId: string;
  requestHash: string;
  decision: FirewallDecision;
  signature: string;
}
