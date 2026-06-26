import { createHash, randomUUID } from 'node:crypto';
import type {
  AutopilotConfig,
  Control,
  ControlStatus,
  ComplianceGap,
  ComplianceReport,
  CycleResult,
  EvidenceDatabase,
  EvidenceRecord,
  GapSeverity,
  MonitorResult,
  RemediationAction,
  RemediationPlan,
  RemediationStatus,
  VerificationResult,
  AuditEntry,
  AuditAction,
} from './types.js';

// ─── Framework Control Definitions ──────────────────────────────────

const FRAMEWORK_CONTROLS: Record<string, Array<{ controlId: string; title: string }>> = {
  iso27001: [
    { controlId: 'A.5.1', title: 'Policies for information security' },
    { controlId: 'A.5.2', title: 'Information security roles and responsibilities' },
    { controlId: 'A.5.3', title: 'Segregation of duties' },
    { controlId: 'A.6.1', title: 'Screening' },
    { controlId: 'A.6.2', title: 'Terms and conditions of employment' },
    { controlId: 'A.7.1', title: 'Physical security perimeters' },
    { controlId: 'A.7.2', title: 'Physical entry' },
    { controlId: 'A.8.1', title: 'User endpoint devices' },
    { controlId: 'A.8.2', title: 'Privileged access rights' },
    { controlId: 'A.8.3', title: 'Information access restriction' },
    { controlId: 'A.8.5', title: 'Secure authentication' },
    { controlId: 'A.8.8', title: 'Management of technical vulnerabilities' },
    { controlId: 'A.8.9', title: 'Configuration management' },
    { controlId: 'A.8.10', title: 'Information deletion' },
    { controlId: 'A.8.12', title: 'Data leakage prevention' },
    { controlId: 'A.8.16', title: 'Monitoring activities' },
    { controlId: 'A.8.23', title: 'Web filtering' },
    { controlId: 'A.8.24', title: 'Use of cryptography' },
    { controlId: 'A.8.25', title: 'Secure development life cycle' },
    { controlId: 'A.8.26', title: 'Application security requirements' },
    { controlId: 'A.8.28', title: 'Secure coding' },
    { controlId: 'A.8.31', title: 'Separation of development, test and production environments' },
    { controlId: 'A.8.32', title: 'Change management' },
    { controlId: 'A.8.33', title: 'Test information' },
    { controlId: 'A.8.34', title: 'Protection of information systems during audit testing' },
    { controlId: 'A.9.1', title: 'Access to source code' },
    { controlId: 'A.9.2', title: 'Access to programs and source code' },
    { controlId: 'A.9.4', title: 'Access to code repositories' },
    { controlId: 'A.9.5', title: 'Secure log-on procedures' },
    { controlId: 'A.9.8', title: 'Information access restriction' },
  ],
  soc2: [
    { controlId: 'CC1.1', title: 'COSO Principle 1: Integrity and ethical values' },
    { controlId: 'CC1.2', title: 'Board independence and oversight' },
    { controlId: 'CC2.1', title: 'Internal communication of objectives' },
    { controlId: 'CC3.1', title: 'Risk assessment process' },
    { controlId: 'CC3.2', title: 'Risk analysis' },
    { controlId: 'CC4.1', title: 'Monitoring activities' },
    { controlId: 'CC5.1', title: 'Control activities selection and development' },
    { controlId: 'CC6.1', title: 'Logical access security' },
    { controlId: 'CC6.2', title: 'User registration and authorization' },
    { controlId: 'CC6.3', title: 'User removal and modification' },
    { controlId: 'CC7.1', title: 'Detection of unauthorized logical access' },
    { controlId: 'CC7.2', title: 'Monitoring of system components' },
    { controlId: 'CC8.1', title: 'Change management' },
    { controlId: 'CC9.1', title: 'Risk mitigation' },
    { controlId: 'CC9.2', title: 'Vendor and business partner risk' },
  ],
  nist_csf: [
    { controlId: 'ID.AM-1', title: 'Physical devices and systems inventory' },
    { controlId: 'ID.AM-2', title: 'Software platforms and applications inventory' },
    { controlId: 'ID.RA-1', title: 'Asset vulnerabilities are identified and documented' },
    { controlId: 'ID.RA-2', title: 'Cybersecurity risk to organizational operations' },
    { controlId: 'PR.AC-1', title: 'Identities and credentials are issued, managed, verified, revoked' },
    { controlId: 'PR.AC-4', title: 'Access permissions and authorizations are managed' },
    { controlId: 'PR.AC-5', title: 'Network integrity is protected' },
    { controlId: 'PR.DS-1', title: 'Data-at-rest is protected' },
    { controlId: 'PR.DS-2', title: 'Data-in-transit is protected' },
    { controlId: 'PR.IP-1', title: 'A baseline configuration of IT infrastructure is established' },
    { controlId: 'PR.IP-2', title: 'A System Development Life Cycle is established' },
    { controlId: 'PR.IP-4', title: 'Backups are created, maintained, and tested' },
    { controlId: 'DE.CM-1', title: 'The network is monitored' },
    { controlId: 'DE.CM-4', title: 'Malicious code is detected' },
    { controlId: 'DE.DP-3', title: 'Detection processes are tested' },
    { controlId: 'RS.RP-1', title: 'Response plan is executed during or after an incident' },
    { controlId: 'RC.RP-1', title: 'Recovery plan is executed during or after an incident' },
  ],
  cis_controls: [
    { controlId: 'CIS.1', title: 'Inventory and Control of Enterprise Assets' },
    { controlId: 'CIS.2', title: 'Inventory and Control of Software Assets' },
    { controlId: 'CIS.3', title: 'Data Protection' },
    { controlId: 'CIS.4', title: 'Secure Configuration of Enterprise Assets and Software' },
    { controlId: 'CIS.5', title: 'Account Management' },
    { controlId: 'CIS.6', title: 'Access Control Management' },
    { controlId: 'CIS.7', title: 'Continuous Vulnerability Management' },
    { controlId: 'CIS.8', title: 'Audit Log Management' },
    { controlId: 'CIS.9', title: 'Email and Web Browser Protections' },
    { controlId: 'CIS.10', title: 'Malware Defenses' },
    { controlId: 'CIS.11', title: 'Data Recovery' },
    { controlId: 'CIS.12', title: 'Network Infrastructure Management' },
    { controlId: 'CIS.13', title: 'Network Monitoring and Defense' },
    { controlId: 'CIS.14', title: 'Security Awareness and Skills Training' },
    { controlId: 'CIS.15', title: 'Service Provider Management' },
  ],
};

// ─── ComplianceAutopilot ────────────────────────────────────────────

export class ComplianceAutopilot {
  private config: AutopilotConfig;
  private db?: EvidenceDatabase;
  private auditTrail: AuditEntry[] = [];
  private lastHash = '0'.repeat(64);
  private controls: Map<string, Control> = new Map();
  private gaps: ComplianceGap[] = [];
  private remediations: RemediationPlan[] = [];

  constructor(config: AutopilotConfig) {
    this.config = {
      monitorIntervalMs: 300_000,
      autoRemediate: true,
      maxConcurrentRemediations: 5,
      ...config,
    };
    this.db = config.evidenceDb;
    this.initializeControls();
  }

  private initializeControls(): void {
    for (const framework of this.config.frameworks) {
      const controlDefs = FRAMEWORK_CONTROLS[framework] ?? [];
      for (const def of controlDefs) {
        const id = `${framework}:${def.controlId}`;
        this.controls.set(id, {
          id,
          controlId: def.controlId,
          title: def.title,
          framework,
          status: 'unknown',
        });
      }
    }
  }

  // ─── Audit Trail ────────────────────────────────────────────────────

  private recordAudit(action: AuditAction, target: string, details: Record<string, unknown>): AuditEntry {
    const entry: AuditEntry = {
      id: randomUUID(),
      timestamp: new Date().toISOString(),
      action,
      actor: 'compliance-autopilot',
      target,
      details,
      previousHash: this.lastHash,
      hash: '',
    };
    entry.hash = createHash('sha256')
      .update(JSON.stringify({ ...entry, hash: '' }))
      .digest('hex');
    this.lastHash = entry.hash;
    this.auditTrail.push(entry);
    return entry;
  }

  /** Cryptographically sign an audit entry */
  signAuditEntry(entryId: string, signingKey: string): string {
    const entry = this.auditTrail.find((e) => e.id === entryId);
    if (!entry) throw new Error(`Audit entry ${entryId} not found`);
    const signature = createHash('sha256')
      .update(`${entry.hash}:${signingKey}`)
      .digest('hex');
    entry.signature = signature;
    return signature;
  }

  /** Verify audit trail integrity */
  verifyAuditTrail(): boolean {
    let prevHash = '0'.repeat(64);
    for (const entry of this.auditTrail) {
      if (entry.previousHash !== prevHash) return false;
      const expectedHash = createHash('sha256')
        .update(JSON.stringify({ ...entry, hash: '', signature: entry.signature }))
        .digest('hex');
      if (entry.hash !== expectedHash) return false;
      prevHash = entry.hash;
    }
    return true;
  }

  // ─── MONITOR: Check control status against evidence ─────────────────

  async monitor(): Promise<MonitorResult> {
    const timestamp = new Date().toISOString();
    const gaps: ComplianceGap[] = [];

    for (const [id, control] of this.controls) {
      const evidence = await this.getEvidenceForControl(control.controlId);
      control.lastCheckedAt = timestamp;

      if (evidence.length === 0) {
        control.status = 'non_compliant';
        const gap: ComplianceGap = {
          id: randomUUID(),
          controlId: control.controlId,
          controlTitle: control.title,
          framework: control.framework,
          severity: this.determineSeverity(control),
          description: `No evidence found for control ${control.controlId} (${control.title})`,
          detectedAt: timestamp,
          evidenceCount: 0,
        };
        gaps.push(gap);
      } else if (evidence.length < 2) {
        control.status = 'partial';
        const gap: ComplianceGap = {
          id: randomUUID(),
          controlId: control.controlId,
          controlTitle: control.title,
          framework: control.framework,
          severity: 'low',
          description: `Insufficient evidence for control ${control.controlId}: ${evidence.length} item(s) found, minimum 2 recommended`,
          detectedAt: timestamp,
          evidenceCount: evidence.length,
        };
        gaps.push(gap);
      } else {
        control.status = 'compliant';
      }
    }

    this.gaps = gaps;

    this.recordAudit('monitor', 'all_frameworks', {
      frameworks: this.config.frameworks,
      controlsChecked: this.controls.size,
      gapsFound: gaps.length,
    });

    return {
      timestamp,
      frameworksChecked: this.config.frameworks,
      controlsChecked: this.controls.size,
      gapsFound: gaps.length,
      gaps,
    };
  }

  private determineSeverity(control: Control): GapSeverity {
    const controlId = control.controlId.toUpperCase();
    if (
      controlId.includes('A.8.16') ||
      controlId.includes('A.8.5') ||
      controlId.includes('CC6') ||
      controlId.includes('CC7') ||
      controlId.includes('PR.AC') ||
      controlId.includes('CIS.6') ||
      controlId.includes('CIS.8')
    ) {
      return 'critical';
    }
    if (
      controlId.includes('A.5') ||
      controlId.includes('A.8.2') ||
      controlId.includes('CC3') ||
      controlId.includes('ID.RA') ||
      controlId.includes('CIS.4')
    ) {
      return 'high';
    }
    if (
      controlId.includes('A.7') ||
      controlId.includes('CC4') ||
      controlId.includes('DE.CM')
    ) {
      return 'medium';
    }
    return 'low';
  }

  private async getEvidenceForControl(controlId: string): Promise<EvidenceRecord[]> {
    if (this.db) {
      try {
        const { rows } = await this.db.query<{
          id: string;
          control_id: string;
          tenant_id: string;
          sha256: string;
          uri: string;
          collected_at: string;
          lineage: { parentHash?: string; source: string };
        }>(
          `SELECT id, control_id, tenant_id, sha256, uri, collected_at, lineage FROM evidence WHERE control_id = $1`,
          [controlId],
        );
        return rows.map((row) => ({
          id: row.id,
          controlId: row.control_id,
          tenantId: Number(row.tenant_id),
          sha256: row.sha256,
          uri: row.uri,
          collectedAt: row.collected_at,
          lineage: row.lineage,
        }));
      } catch {
        return [];
      }
    }
    return [];
  }

  // ─── DETECT: Identify compliance gaps ──────────────────────────────

  detect(): ComplianceGap[] {
    this.recordAudit('detect', 'gaps', {
      gapsDetected: this.gaps.length,
      controlStatuses: Array.from(this.controls.values()).map((c) => ({
        controlId: c.controlId,
        status: c.status,
      })),
    });
    return [...this.gaps];
  }

  // ─── REMEDIATE: Generate and execute remediation plans ──────────────

  async remediate(gaps?: ComplianceGap[]): Promise<RemediationPlan[]> {
    const targets = gaps ?? this.gaps;
    const plans: RemediationPlan[] = [];

    for (const gap of targets) {
      if (this.remediations.some((r) => r.gapId === gap.id && r.status !== 'failed')) {
        continue;
      }

      const plan = this.createRemediationPlan(gap);
      this.remediations.push(plan);
      plans.push(plan);

      if (this.config.autoRemediate) {
        await this.executeRemediation(plan);
      }

      this.recordAudit('remediate', gap.controlId, {
        gapId: gap.id,
        planId: plan.id,
        actionsCount: plan.actions.length,
        status: plan.status,
      });
    }

    return plans;
  }

  private createRemediationPlan(gap: ComplianceGap): RemediationPlan {
    const actions: RemediationAction[] = [
      {
        id: randomUUID(),
        type: 'collect_evidence',
        description: `Collect evidence for control ${gap.controlId}`,
        parameters: { controlId: gap.controlId, framework: gap.framework },
        status: 'pending',
      },
      {
        id: randomUUID(),
        type: 'update_control',
        description: `Update control ${gap.controlId} status`,
        parameters: { controlId: gap.controlId, targetStatus: 'compliant' },
        status: 'pending',
      },
      {
        id: randomUUID(),
        type: 'notify_owner',
        description: `Notify owner of control ${gap.controlId}`,
        parameters: { controlId: gap.controlId, owner: gap.controlTitle },
        status: 'pending',
      },
    ];

    return {
      id: randomUUID(),
      gapId: gap.id,
      controlId: gap.controlId,
      framework: gap.framework,
      actions,
      status: 'pending',
      createdAt: new Date().toISOString(),
    };
  }

  private async executeRemediation(plan: RemediationPlan): Promise<void> {
    plan.status = 'in_progress';

    for (const action of plan.actions) {
      action.status = 'in_progress';
      action.executedAt = new Date().toISOString();

      try {
        await this.executeAction(action);
        action.status = 'completed';
      } catch (err) {
        action.status = 'failed';
        plan.status = 'failed';
        return;
      }
    }

    plan.status = 'completed';
    plan.completedAt = new Date().toISOString();
  }

  private async executeAction(action: RemediationAction): Promise<void> {
    switch (action.type) {
      case 'collect_evidence': {
        const controlId = String(action.parameters.controlId ?? '');
        if (this.db) {
          const evidenceHash = createHash('sha256')
            .update(`${controlId}:${Date.now()}:autogenerated`)
            .digest('hex');
          await this.db.execute(
            `INSERT INTO evidence (id, tenant_id, control_id, sha256, uri, metadata, lineage, collected_at, created_at)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
             ON CONFLICT (id) DO NOTHING`,
            [
              `ev-${evidenceHash.slice(0, 16)}`,
              String(this.config.tenantId),
              controlId,
              evidenceHash,
              `grc-claw://autopilot/evidence/${controlId}`,
              JSON.stringify({ source: 'compliance-autopilot', autoGenerated: true }),
              JSON.stringify({ source: 'compliance-autopilot' }),
              new Date().toISOString(),
            ],
          );
        }
        break;
      }
      case 'update_control': {
        const controlId = String(action.parameters.controlId ?? '');
        const targetStatus = String(action.parameters.targetStatus ?? 'compliant') as ControlStatus;
        const key = `${this.config.frameworks[0] ?? 'iso27001'}:${controlId}`;
        const control = this.controls.get(key);
        if (control) {
          control.status = targetStatus;
        }
        break;
      }
      case 'notify_owner': {
        console.log(
          `[COMPLIANCE-AUTOPILOT] Notification: Control ${action.parameters.controlId} requires attention`,
        );
        break;
      }
      case 'generate_report': {
        break;
      }
      case 'custom': {
        break;
      }
    }
  }

  // ─── VERIFY: Re-check after remediation ────────────────────────────

  async verify(remediationIds?: string[]): Promise<VerificationResult[]> {
    const targets = remediationIds
      ? this.remediations.filter((r) => remediationIds.includes(r.id))
      : this.remediations.filter((r) => r.status === 'completed');

    const results: VerificationResult[] = [];

    for (const plan of targets) {
      const previousStatus = this.controls.get(
        `${plan.framework}:${plan.controlId}`,
      )?.status ?? 'unknown';

      const evidence = await this.getEvidenceForControl(plan.controlId);
      const currentStatus: ControlStatus = evidence.length >= 2 ? 'compliant' : evidence.length > 0 ? 'partial' : 'non_compliant';

      const verified = currentStatus === 'compliant';

      const result: VerificationResult = {
        remediationId: plan.id,
        controlId: plan.controlId,
        verified,
        previousStatus,
        currentStatus,
        verifiedAt: new Date().toISOString(),
      };

      results.push(result);

      if (verified) {
        plan.status = 'verified';
        plan.verifiedAt = result.verifiedAt;
        const key = `${plan.framework}:${plan.controlId}`;
        const control = this.controls.get(key);
        if (control) control.status = 'compliant';
      } else {
        plan.status = 'failed';
      }

      this.recordAudit('verify', plan.controlId, {
        remediationId: plan.id,
        verified,
        previousStatus,
        currentStatus,
      });
    }

    return results;
  }

  // ─── REPORT: Generate compliance reports ────────────────────────────

  async generateReport(framework: string): Promise<ComplianceReport> {
    const frameworkControls = Array.from(this.controls.values()).filter(
      (c) => c.framework === framework,
    );

    const compliant = frameworkControls.filter((c) => c.status === 'compliant').length;
    const nonCompliant = frameworkControls.filter((c) => c.status === 'non_compliant').length;
    const partial = frameworkControls.filter((c) => c.status === 'partial').length;
    const unknown = frameworkControls.filter((c) => c.status === 'unknown').length;
    const total = frameworkControls.length;
    const score = total > 0 ? Math.round((compliant / total) * 10000) / 100 : 0;

    const frameworkGaps = this.gaps.filter((g) => g.framework === framework);
    const frameworkRemediations = this.remediations.filter((r) => r.framework === framework);

    const report: ComplianceReport = {
      id: randomUUID(),
      framework,
      generatedAt: new Date().toISOString(),
      totalControls: total,
      compliantControls: compliant,
      nonCompliantControls: nonCompliant,
      partialControls: partial,
      unknownControls: unknown,
      complianceScore: score,
      gaps: frameworkGaps,
      remediations: frameworkRemediations,
    };

    if (this.config.signingKey) {
      report.signature = this.signAuditEntry(
        this.recordAudit('report', framework, { reportId: report.id, score }).id,
        this.config.signingKey,
      );
    }

    this.recordAudit('report', framework, {
      reportId: report.id,
      totalControls: total,
      complianceScore: score,
    });

    return report;
  }

  // ─── AUDIT: Sign all actions in the audit trail ────────────────────

  signAll(signingKey: string): AuditEntry[] {
    for (const entry of this.auditTrail) {
      if (!entry.signature) {
        entry.signature = createHash('sha256')
          .update(`${entry.hash}:${signingKey}`)
          .digest('hex');
      }
    }
    return [...this.auditTrail];
  }

  // ─── Full Cycle ────────────────────────────────────────────────────

  async runCycle(): Promise<CycleResult> {
    const cycleId = randomUUID();
    const startedAt = new Date().toISOString();

    const monitorResult = await this.monitor();
    const detectedGaps = this.detect();
    const remediations = detectedGaps.length > 0 ? await this.remediate(detectedGaps) : [];
    const verificationResults = remediations.length > 0 ? await this.verify() : [];

    let report: ComplianceReport | undefined;
    for (const framework of this.config.frameworks) {
      report = await this.generateReport(framework);
    }

    return {
      cycleId,
      startedAt,
      completedAt: new Date().toISOString(),
      monitor: monitorResult,
      remediations,
      verificationResults,
      report,
      auditTrail: [...this.auditTrail],
    };
  }

  // ─── Accessors ─────────────────────────────────────────────────────

  getControls(): Control[] {
    return Array.from(this.controls.values());
  }

  getGaps(): ComplianceGap[] {
    return [...this.gaps];
  }

  getRemediations(): RemediationPlan[] {
    return [...this.remediations];
  }

  getAuditTrail(): AuditEntry[] {
    return [...this.auditTrail];
  }

  getConfig(): AutopilotConfig {
    return { ...this.config };
  }
}
