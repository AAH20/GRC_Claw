export type CheckStatus = 'pass' | 'fail' | 'warning' | 'unknown';
export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface ComplianceCheck {
  id: string;
  name: string;
  category: string;
  status: CheckStatus;
  severity: Severity;
  details: string;
  controlId?: string;
  framework?: string;
}

export interface DeviceEvidence {
  deviceId: string;
  hostname: string;
  os: string;
  osVersion: string;
  checks: ComplianceCheck[];
  overallScore: number;
  collectedAt: string;
}

export interface DeviceReport {
  deviceId: string;
  hostname: string;
  timestamp: string;
  checks: ComplianceCheck[];
  overallScore: number;
  frameworkScores: Record<string, number>;
  failedChecks: ComplianceCheck[];
}

export interface AgentConfig {
  deviceId: string;
  checksToRun: string[];
  reportingEndpoint?: string;
  collectionIntervalMs?: number;
}

export interface SystemAdapter {
  exec(cmd: string): Promise<string>;
  readFile(path: string): Promise<string>;
  platform(): string;
  hostname(): string;
}
