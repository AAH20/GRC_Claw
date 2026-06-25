import type {
  FrameworkCode,
  RegulationAST,
  ASTControlNode,
  PolicyAST,
  PolicyAtom,
  ControlStatus,
  DriftEvent,
  RiskAssessment,
  ComplianceState,
} from '../types.js';

export interface ReasoningResult {
  control: string;
  decision: 'compliant' | 'non-compliant' | 'partial' | 'unknown';
  confidence: number;
  proof: string[];
  counterExample?: string;
  reasoningPath: string[];
  symbolicProof: SymbolicProof;
}

export interface SymbolicProof {
  obligations: ProofObligation[];
  discharged: string[];
  remaining: string[];
  valid: boolean;
}

export interface ProofObligation {
  id: string;
  formula: string;
  status: 'proven' | 'disproven' | 'unknown' | 'assumed';
  evidenceRef?: string;
}

export interface ReasoningContext {
  orgId: string;
  framework: FrameworkCode;
  currentEvidence: Map<string, EvidenceItem[]>;
  configurationState: ConfigurationState;
  riskTolerance: 'low' | 'medium' | 'high';
  previousState?: ComplianceState;
}

export interface EvidenceItem {
  id: string;
  controlId: string;
  type: string;
  hash: string;
  timestamp: string;
  valid: boolean;
  metadata?: Record<string, unknown>;
}

export interface ConfigurationState {
  iam: IAMState;
  network: NetworkState;
  data: DataState;
  monitoring: MonitoringState;
  physical: PhysicalState;
}

export interface IAMState {
  mfaEnabled: boolean;
  privilegedUsers: string[];
  sessionTimeout: number;
  lastPasswordRotation: string;
  rbacPolicyVersion: string;
  mfaEnforcementRate: number;
}

export interface NetworkState {
  firewallRules: number;
  segmentationEnabled: boolean;
  idsEnabled: boolean;
  tlsVersion: string;
  publicEndpoints: string[];
}

export interface DataState {
  encryptionAtRest: boolean;
  encryptionInTransit: boolean;
  backupEnabled: boolean;
  backupFrequency: string;
  lastBackup: string;
  retentionDays: number;
}

export interface MonitoringState {
  siemEnabled: boolean;
  logRetentionDays: number;
  alertingEnabled: boolean;
  mttr: number;
  monitoringCoverage: number;
}

export interface PhysicalState {
  accessControl: boolean;
  cctvEnabled: boolean;
  environmentalMonitoring: boolean;
  visitorManagement: boolean;
}

interface Z3Variable {
  name: string;
  type: 'bool' | 'int' | 'string';
  value?: unknown;
}

interface Z3Constraint {
  expression: string;
  variables: Z3Variable[];
}

export class NeuroSymbolicReasoner {
  private asts: Map<FrameworkCode, RegulationAST>;
  private constraintCache: Map<string, Z3Constraint[]> = new Map();

  constructor(asts: Map<FrameworkCode, RegulationAST>) {
    this.asts = asts;
  }

  async reason(context: ReasoningContext): Promise<ComplianceState> {
    const ast = this.asts.get(context.framework);
    if (!ast) throw new Error(`Framework ${context.framework} not compiled`);

    const controlStatuses: ControlStatus[] = [];
    const drift: DriftEvent[] = [];
    const risks: RiskAssessment[] = [];

    for (const control of ast.controls) {
      const result = this.evaluateControl(control, context);
      const evidence = context.currentEvidence.get(control.id) ?? [];

      controlStatuses.push({
        controlId: control.id,
        status: this.mapDecisionToStatus(result.decision),
        lastVerified: new Date().toISOString(),
        evidenceCount: evidence.length,
        score: result.confidence * 100,
        issues: result.decision === 'non-compliant'
          ? [{
              id: `issue-${control.id}-${Date.now()}`,
              severity: control.severity === 'CRITICAL' ? 'CRITICAL' : 'HIGH',
              description: `Control ${control.code} is non-compliant: ${result.proof.join('; ')}`,
              detectedAt: new Date().toISOString(),
            }]
          : [],
      });

      const risk = this.assessRisk(control, result, context);
      risks.push(risk);

      if (context.previousState) {
        const prevStatus = context.previousState.controlStatuses.find((s) => s.controlId === control.id);
        if (prevStatus && prevStatus.status === 'compliant' && result.decision !== 'compliant') {
          drift.push({
            id: `drift-${control.id}-${Date.now()}`,
            controlId: control.id,
            detectedAt: new Date().toISOString(),
            type: 'policy',
            before: prevStatus.status,
            after: result.decision,
            severity: control.severity ?? 'MEDIUM',
            autoRemediated: false,
          });
        }
      }
    }

    const compliant = controlStatuses.filter((s) => s.status === 'compliant').length;
    const total = controlStatuses.length;
    const overallScore = total > 0 ? (compliant / total) * 100 : 0;

    return {
      orgId: context.orgId,
      timestamp: new Date().toISOString(),
      framework: context.framework,
      overallScore,
      controlStatuses,
      drift,
      risks,
    };
  }

  evaluateControl(control: ASTControlNode, context: ReasoningContext): ReasoningResult {
    const proof: string[] = [];
    const reasoningPath: string[] = [];
    const obligations: ProofObligation[] = [];
    const discharged: string[] = [];
    const remaining: string[] = [];

    reasoningPath.push(`Evaluating control ${control.code}: ${control.title}`);

    const evidence = context.currentEvidence.get(control.id) ?? [];
    const validEvidence = evidence.filter((e) => e.valid);

    if (validEvidence.length === 0) {
      proof.push(`No valid evidence found for control ${control.code}`);
      remaining.push(`evidence-${control.id}`);
      return {
        control: control.id,
        decision: 'unknown',
        confidence: 0,
        proof,
        reasoningPath,
        symbolicProof: { obligations: [], discharged: [], remaining, valid: false },
      };
    }

    reasoningPath.push(`Found ${validEvidence.length} valid evidence items`);

    let satisfied = true;
    let partiallySatisfied = false;

    for (const obligation of this.symbolicCheck(control, context)) {
      obligations.push(obligation);
      if (obligation.status === 'proven') {
        discharged.push(obligation.id);
        proof.push(`Obligation ${obligation.id} proven: ${obligation.formula}`);
      } else if (obligation.status === 'disproven') {
        satisfied = false;
        proof.push(`Obligation ${obligation.id} violated: ${obligation.formula}`);
      } else {
        partiallySatisfied = true;
      }
    }

    const confidence = this.calculateConfidence(control, evidence, obligations, context);
    const decision = satisfied ? 'compliant' : partiallySatisfied ? 'partial' : 'non-compliant';

    return {
      control: control.id,
      decision,
      confidence,
      proof,
      reasoningPath,
      symbolicProof: { obligations, discharged, remaining, valid: satisfied },
    };
  }

  private symbolicCheck(control: ASTControlNode, context: ReasoningContext): ProofObligation[] {
    const obligations: ProofObligation[] = [];
    const { configurationState: state } = context;

    switch (control.code) {
      case 'A.8.2': // Privileged Access Rights
        obligations.push({
          id: 'priv-access-mfa',
          formula: 'all_privileged_users.mfa_enabled = true',
          status: state.iam.mfaEnabled ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'priv-access-count',
          formula: 'count(privileged_users) <= threshold',
          status: state.iam.privilegedUsers.length <= 10 ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'priv-access-rotation',
          formula: 'password_age <= 90_days',
          status: this.isPasswordFresh(state.iam.lastPasswordRotation, 90) ? 'proven' : 'disproven',
        });
        break;

      case 'A.8.5': // Secure Authentication
        obligations.push({
          id: 'auth-mfa',
          formula: 'mfa_enforcement_rate >= 95_percent',
          status: state.iam.mfaEnforcementRate >= 0.95 ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'auth-session',
          formula: 'session_timeout <= 15_minutes',
          status: state.iam.sessionTimeout <= 900 ? 'proven' : 'disproven',
        });
        break;

      case 'A.8.9': // Configuration Management
        obligations.push({
          id: 'config-firewall',
          formula: 'firewall_rules.count > 0',
          status: state.network.firewallRules > 0 ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'config-segmentation',
          formula: 'network_segmentation.enabled = true',
          status: state.network.segmentationEnabled ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'config-tls',
          formula: 'tls_version >= 1.2',
          status: ['1.2', '1.3'].includes(state.network.tlsVersion) ? 'proven' : 'disproven',
        });
        break;

      case 'A.8.16': // Monitoring Activities
        obligations.push({
          id: 'mon-siem',
          formula: 'siem.enabled = true',
          status: state.monitoring.siemEnabled ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'mon-retention',
          formula: 'log_retention_days >= 90',
          status: state.monitoring.logRetentionDays >= 90 ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'mon-alerting',
          formula: 'alerting.enabled = true',
          status: state.monitoring.alertingEnabled ? 'proven' : 'disproven',
        });
        break;

      case 'CC6.1': // SOC 2 Logical Access
        obligations.push({
          id: 'soc2-access-mfa',
          formula: 'mfa_enabled = true',
          status: state.iam.mfaEnabled ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'soc2-access-rbac',
          formula: 'rbac_policy_version != null',
          status: state.iam.rbacPolicyVersion.length > 0 ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'soc2-access-encryption',
          formula: 'encryption_in_transit = true',
          status: state.data.encryptionInTransit ? 'proven' : 'disproven',
        });
        break;

      case 'CC7.2': // SOC 2 Security Event Monitoring
        obligations.push({
          id: 'soc2-monitor-siem',
          formula: 'siem_enabled = true',
          status: state.monitoring.siemEnabled ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'soc2-monitor-coverage',
          formula: 'monitoring_coverage >= 80_percent',
          status: state.monitoring.monitoringCoverage >= 80 ? 'proven' : 'disproven',
        });
        break;

      case 'A.6.1': // ISO 42001 AI Risk Assessment
        obligations.push({
          id: 'ai-risk-assessment',
          formula: 'risk_assessment_documented = true',
          status: context.currentEvidence.has(control.id) ? 'proven' : 'disproven',
        });
        break;

      case 'PR.AC': // NIST CSF Identity Management
        obligations.push({
          id: 'nist-iam-mfa',
          formula: 'mfa_enforced = true',
          status: state.iam.mfaEnabled ? 'proven' : 'disproven',
        });
        obligations.push({
          id: 'nist-iam-session',
          formula: 'session_timeout <= 900',
          status: state.iam.sessionTimeout <= 900 ? 'proven' : 'disproven',
        });
        break;

      case 'DE.CM': // NIST CSF Continuous Monitoring
        obligations.push({
          id: 'nist-monitor',
          formula: 'siem_enabled AND alerting_enabled',
          status: (state.monitoring.siemEnabled && state.monitoring.alertingEnabled) ? 'proven' : 'disproven',
        });
        break;

      default:
        obligations.push({
          id: `default-${control.id}`,
          formula: 'evidence_count > 0',
          status: context.currentEvidence.has(control.id) ? 'proven' : 'disproven',
        });
    }

    return obligations;
  }

  private isPasswordFresh(rotationDate: string, maxAgeDays: number): boolean {
    const rotation = new Date(rotationDate);
    const now = new Date();
    const ageDays = (now.getTime() - rotation.getTime()) / (1000 * 60 * 60 * 24);
    return ageDays <= maxAgeDays;
  }

  private calculateConfidence(
    control: ASTControlNode,
    evidence: EvidenceItem[],
    obligations: ProofObligation[],
    _context: ReasoningContext
  ): number {
    let confidence = 0;

    const validEvidence = evidence.filter((e) => e.valid);
    const evidenceScore = Math.min(validEvidence.length / 3, 1) * 0.4;
    confidence += evidenceScore;

    const proven = obligations.filter((o) => o.status === 'proven').length;
    const total = obligations.length;
    const obligationScore = total > 0 ? (proven / total) * 0.5 : 0.5;
    confidence += obligationScore;

    const freshness = this.evidenceFreshnessScore(validEvidence);
    confidence += freshness * 0.1;

    return Math.min(confidence, 1);
  }

  private evidenceFreshnessScore(evidence: EvidenceItem[]): number {
    if (evidence.length === 0) return 0;
    const now = Date.now();
    const ages = evidence.map((e) => {
      const age = (now - new Date(e.timestamp).getTime()) / (1000 * 60 * 60 * 24);
      return age;
    });
    const avgAge = ages.reduce((a, b) => a + b, 0) / ages.length;
    if (avgAge <= 7) return 1;
    if (avgAge <= 30) return 0.8;
    if (avgAge <= 90) return 0.6;
    if (avgAge <= 365) return 0.4;
    return 0.2;
  }

  private mapDecisionToStatus(decision: string): ControlStatus['status'] {
    switch (decision) {
      case 'compliant': return 'compliant';
      case 'non-compliant': return 'non-compliant';
      case 'partial': return 'partial';
      default: return 'not-tested';
    }
  }

  private assessRisk(control: ASTControlNode, result: ReasoningResult, context: ReasoningContext): RiskAssessment {
    const severityMap = { LOW: 1, MEDIUM: 3, HIGH: 7, CRITICAL: 10 };
    const baseRisk = severityMap[control.severity as keyof typeof severityMap] ?? 3;

    const complianceRisk = result.decision === 'compliant' ? 0 : result.decision === 'partial' ? 3 : 7;
    const likelihood = complianceRisk / 10;

    const blastRadius = this.calculateBlastRadius(control, context);
    const impact = baseRisk * blastRadius;

    const riskScore = (likelihood * 50 + impact * 50) / 10;

    const factors: string[] = [];
    if (result.decision === 'non-compliant') factors.push('control_non_compliant');
    if (control.severity === 'CRITICAL') factors.push('critical_severity');
    if (blastRadius > 0.7) factors.push('high_blast_radius');
    if (context.previousState) {
      const prev = context.previousState.controlStatuses.find((s) => s.controlId === control.id);
      if (prev && prev.status === 'compliant') factors.push('regression_detected');
    }

    return {
      controlId: control.id,
      riskScore,
      blastRadius,
      likelihood,
      impact,
      factors,
    };
  }

  private calculateBlastRadius(control: ASTControlNode, context: ReasoningContext): number {
    const ast = this.asts.get(context.framework);
    if (!ast) return 0.5;

    const dependent = ast.controls.filter((c) => c.crossRefs.some((ref) => ref.includes(control.code)));
    const total = ast.controls.length;

    return Math.min(dependent.length / Math.max(total, 1) + 0.1, 1);
  }

  async detectDrift(context: ReasoningContext): Promise<DriftEvent[]> {
    if (!context.previousState) return [];

    const current = await this.reason(context);
    const drifts: DriftEvent[] = [];

    for (const prev of context.previousState.controlStatuses) {
      const curr = current.controlStatuses.find((s) => s.controlId === prev.controlId);
      if (curr && prev.status === 'compliant' && curr.status !== 'compliant') {
        drifts.push({
          id: `drift-${prev.controlId}-${Date.now()}`,
          controlId: prev.controlId,
          detectedAt: new Date().toISOString(),
          type: 'policy',
          before: prev.status,
          after: curr.status,
          severity: 'HIGH',
          autoRemediated: false,
        });
      }
    }

    return drifts;
  }

  async synthesizeRemediation(drift: DriftEvent): Promise<string> {
    return `REMEDIATION for ${drift.controlId}: Auto-remediation plan for ${drift.type} drift from ${drift.before} to ${drift.after}. Severity: ${drift.severity}. Apply configuration change and verify evidence.`;
  }
}
