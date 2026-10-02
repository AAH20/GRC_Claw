export type Severity = 'low' | 'medium' | 'high' | 'critical';

export type ControlStatus =
  | 'not_started'
  | 'in_progress'
  | 'implemented'
  | 'not_applicable'
  | 'failed';

export interface ComplianceControl {
  id: string;
  controlCode: string;
  title: string;
  frameworkCode: string;
  domain?: string;
  orgStatus?: ControlStatus;
}

export interface ComplianceImpact {
  controlIds: string[];
  rationale: string;
  suggestedSeverity?: Severity;
}

/** Aligns with A2Z SOC security_events canonical shape */
export interface SecurityEventCanonical {
  eventUuid: string;
  eventType: string;
  severity: Severity;
  sourceSystem: string;
  tenantId: number;
  correlationId?: string;
  complianceImpact?: ComplianceImpact;
  eventData: Record<string, unknown>;
}

export interface ComplianceScore {
  tenantId: number;
  frameworkCode: string;
  scorePercent: number;
  failingControls: number;
  totalControls: number;
}

export interface GRCEngineFacade {
  getComplianceScore(tenantId: number, frameworkCode: string): Promise<ComplianceScore>;
  listControls(tenantId: number, frameworkCode?: string): Promise<ComplianceControl[]>;
  attachEvidence(
    tenantId: number,
    controlId: string,
    payload: { hash: string; uri: string; collectedAt: string },
    idempotencyKey: string
  ): Promise<{ evidenceId: string }>;
  mapSecurityEventToControls(event: SecurityEventCanonical): Promise<ComplianceImpact>;
}

export function createEventUuid(parts: string[]): string {
  const data = parts.join('|');
  let h = 0;
  for (let i = 0; i < data.length; i++) h = (Math.imul(31, h) + data.charCodeAt(i)) | 0;
  return `grc-${Math.abs(h).toString(16).padStart(8, '0')}-${Date.now().toString(36)}`;
}
