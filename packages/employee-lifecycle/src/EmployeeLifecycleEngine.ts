import type {
  Employee,
  EmployeeState,
  EmployeeDevice,
  TrainingRecord,
  ComplianceCheck,
  ComplianceArea,
  AccessReviewCampaign,
  AccessReviewItem,
  OnboardingWorkflow,
  OffboardingWorkflow,
  OffboardingActionItem,
  OffboardingAction,
  HrWebhookEvent,
  HrSystemType,
  EmployeeComplianceDashboard,
  ComplianceAreaSummary,
  DashboardAction,
} from './types.js';

function generateId(prefix: string): string {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).substring(2, 10);
  return `${prefix}-${ts}-${rand}`;
}

const VALID_TRANSITIONS: Record<EmployeeState, EmployeeState[]> = {
  prospect: ['onboarding'],
  onboarding: ['active'],
  active: ['offboarding'],
  offboarding: ['offboarded'],
  offboarded: [],
};

const REQUIRED_COMPLIANCE_AREAS: ComplianceArea[] = [
  'mfa_enrollment',
  'device_compliance',
  'policy_acknowledgment',
  'security_training',
  'background_check',
  'data_encryption',
];

// ---------------------------------------------------------------------------
// Employee Lifecycle Engine
// ---------------------------------------------------------------------------

export class EmployeeLifecycleEngine {
  private employees: Map<string, Employee> = new Map();
  private devices: Map<string, EmployeeDevice> = new Map();
  private trainingRecords: Map<string, TrainingRecord> = new Map();
  private complianceChecks: Map<string, ComplianceCheck[]> = new Map();
  private onboardingWorkflows: Map<string, OnboardingWorkflow> = new Map();
  private offboardingWorkflows: Map<string, OffboardingWorkflow> = new Map();
  private accessReviewCampaigns: Map<string, AccessReviewCampaign> = new Map();
  private accessReviewItems: Map<string, AccessReviewItem[]> = new Map();

  // -------------------------------------------------------------------------
  // Employee CRUD
  // -------------------------------------------------------------------------

  createEmployee(input: Omit<Employee, 'id' | 'state' | 'createdAt' | 'updatedAt'>): Employee {
    const now = new Date().toISOString();
    const employee: Employee = {
      ...input,
      id: generateId('emp'),
      state: 'prospect',
      createdAt: now,
      updatedAt: now,
    };
    this.employees.set(employee.id, employee);
    return employee;
  }

  getEmployee(id: string): Employee | undefined {
    return this.employees.get(id);
  }

  listEmployees(filter?: { state?: EmployeeState; department?: string }): Employee[] {
    let result = Array.from(this.employees.values());
    if (filter?.state) result = result.filter(e => e.state === filter.state);
    if (filter?.department) result = result.filter(e => e.department === filter.department);
    return result;
  }

  // -------------------------------------------------------------------------
  // State transitions
  // -------------------------------------------------------------------------

  transitionEmployeeState(employeeId: string, targetState: EmployeeState): Employee | undefined {
    const employee = this.employees.get(employeeId);
    if (!employee) return undefined;

    const allowed = VALID_TRANSITIONS[employee.state];
    if (!allowed.includes(targetState)) {
      throw new Error(
        `Invalid transition: ${employee.state} → ${targetState}. Allowed: ${allowed.join(', ') || 'none'}`,
      );
    }

    const now = new Date().toISOString();
    const updated: Employee = { ...employee, state: targetState, updatedAt: now };

    if (targetState === 'active') {
      updated.hireDate = employee.hireDate ?? now;
    } else if (targetState === 'offboarding') {
      updated.offboardDate = now;
    }

    this.employees.set(employeeId, updated);
    return updated;
  }

  // -------------------------------------------------------------------------
  // Onboarding workflow
  // -------------------------------------------------------------------------

  startOnboarding(employeeId: string): OnboardingWorkflow {
    const employee = this.employees.get(employeeId);
    if (!employee) throw new Error(`Employee ${employeeId} not found`);

    const existing = this.getOnboardingWorkflow(employeeId);
    if (existing && !existing.completedAt) return existing;

    const workflow: OnboardingWorkflow = {
      id: generateId('onb'),
      employeeId,
      startedAt: new Date().toISOString(),
      mfaVerified: false,
      deviceCompliant: false,
      policyAcknowledged: false,
      securityTrainingCompleted: false,
      backgroundCheckPassed: false,
    };

    this.onboardingWorkflows.set(workflow.id, workflow);
    this.transitionEmployeeState(employeeId, 'onboarding');
    return workflow;
  }

  getOnboardingWorkflow(employeeId: string): OnboardingWorkflow | undefined {
    return Array.from(this.onboardingWorkflows.values()).find(w => w.employeeId === employeeId);
  }

  getActiveOnboardingWorkflow(employeeId: string): OnboardingWorkflow | undefined {
    return Array.from(this.onboardingWorkflows.values()).find(w => w.employeeId === employeeId && !w.completedAt);
  }

  completeMfaVerification(employeeId: string): OnboardingWorkflow | undefined {
    const wf = this.getActiveOnboardingWorkflow(employeeId);
    if (!wf) return undefined;
    const updated = { ...wf, mfaVerified: true };
    this.onboardingWorkflows.set(wf.id, updated);
    this.addComplianceCheck(employeeId, 'mfa_enrollment', true);
    this.tryCompleteOnboarding(updated);
    return updated;
  }

  completeDeviceCompliance(employeeId: string): OnboardingWorkflow | undefined {
    const wf = this.getActiveOnboardingWorkflow(employeeId);
    if (!wf) return undefined;
    const updated = { ...wf, deviceCompliant: true };
    this.onboardingWorkflows.set(wf.id, updated);
    this.addComplianceCheck(employeeId, 'device_compliance', true);
    this.tryCompleteOnboarding(updated);
    return updated;
  }

  acknowledgePolicies(employeeId: string): OnboardingWorkflow | undefined {
    const wf = this.getActiveOnboardingWorkflow(employeeId);
    if (!wf) return undefined;
    const updated = { ...wf, policyAcknowledged: true };
    this.onboardingWorkflows.set(wf.id, updated);
    this.addComplianceCheck(employeeId, 'policy_acknowledgment', true);
    this.tryCompleteOnboarding(updated);
    return updated;
  }

  completeSecurityTraining(employeeId: string): OnboardingWorkflow | undefined {
    const wf = this.getActiveOnboardingWorkflow(employeeId);
    if (!wf) return undefined;
    const updated = { ...wf, securityTrainingCompleted: true };
    this.onboardingWorkflows.set(wf.id, updated);
    this.addComplianceCheck(employeeId, 'security_training', true);
    this.tryCompleteOnboarding(updated);
    return updated;
  }

  completeBackgroundCheck(employeeId: string): OnboardingWorkflow | undefined {
    const wf = this.getActiveOnboardingWorkflow(employeeId);
    if (!wf) return undefined;
    const updated = { ...wf, backgroundCheckPassed: true };
    this.onboardingWorkflows.set(wf.id, updated);
    this.addComplianceCheck(employeeId, 'background_check', true);
    this.tryCompleteOnboarding(updated);
    return updated;
  }

  private tryCompleteOnboarding(wf: OnboardingWorkflow): void {
    if (
      wf.mfaVerified &&
      wf.deviceCompliant &&
      wf.policyAcknowledged &&
      wf.securityTrainingCompleted &&
      wf.backgroundCheckPassed
    ) {
      const completed = { ...wf, completedAt: new Date().toISOString() };
      this.onboardingWorkflows.set(wf.id, completed);
      this.transitionEmployeeState(wf.employeeId, 'active');
    }
  }

  // -------------------------------------------------------------------------
  // Offboarding workflow
  // -------------------------------------------------------------------------

  startOffboarding(employeeId: string, targetDate?: string): OffboardingWorkflow {
    const employee = this.employees.get(employeeId);
    if (!employee) throw new Error(`Employee ${employeeId} not found`);

    const existing = this.getOffboardingWorkflow(employeeId);
    if (existing && !existing.completedAt) return existing;

    const now = new Date().toISOString();
    const actions: OffboardingActionItem[] = [
      { id: generateId('off-act'), action: 'access_revocation', status: 'pending' },
      { id: generateId('off-act'), action: 'device_wipe', status: 'pending' },
      { id: generateId('off-act'), action: 'credential_rotation', status: 'pending' },
      { id: generateId('off-act'), action: 'exit_interview', status: 'pending' },
      { id: generateId('off-act'), action: 'license_reclaim', status: 'pending' },
      { id: generateId('off-act'), action: 'knowledge_transfer', status: 'pending' },
    ];

    const workflow: OffboardingWorkflow = {
      id: generateId('offb'),
      employeeId,
      initiatedAt: now,
      targetDate: targetDate ?? now,
      actions,
    };

    this.offboardingWorkflows.set(workflow.id, workflow);
    this.transitionEmployeeState(employeeId, 'offboarding');
    return workflow;
  }

  getOffboardingWorkflow(employeeId: string): OffboardingWorkflow | undefined {
    return Array.from(this.offboardingWorkflows.values()).find(w => w.employeeId === employeeId);
  }

  getActiveOffboardingWorkflow(employeeId: string): OffboardingWorkflow | undefined {
    return Array.from(this.offboardingWorkflows.values()).find(w => w.employeeId === employeeId && !w.completedAt);
  }

  completeOffboardingAction(
    employeeId: string,
    action: OffboardingAction,
    status: 'in_progress' | 'completed' | 'failed',
  ): OffboardingWorkflow | undefined {
    const wf = this.getActiveOffboardingWorkflow(employeeId);
    if (!wf) return undefined;

    const now = new Date().toISOString();
    const updatedActions: OffboardingActionItem[] = wf.actions.map(a => {
      if (a.action !== action) return a;
      if (status === 'in_progress') return { ...a, status: 'in_progress' as const, startedAt: a.startedAt ?? now };
      if (status === 'completed') return { ...a, status: 'completed' as const, completedAt: now };
      return { ...a, status: 'failed' as const };
    });

    const updated: OffboardingWorkflow = { ...wf, actions: updatedActions };
    this.offboardingWorkflows.set(wf.id, updated);

    if (action === 'access_revocation' && status === 'completed') {
      this.addComplianceCheck(employeeId, 'mfa_enrollment', false);
    }

    this.tryCompleteOffboarding(updated);
    return updated;
  }

  private tryCompleteOffboarding(wf: OffboardingWorkflow): void {
    const allDone = wf.actions.every(a => a.status === 'completed' || a.status === 'failed');
    if (allDone) {
      const completed = { ...wf, completedAt: new Date().toISOString() };
      this.offboardingWorkflows.set(wf.id, completed);
      this.transitionEmployeeState(wf.employeeId, 'offboarded');
    }
  }

  // -------------------------------------------------------------------------
  // Devices
  // -------------------------------------------------------------------------

  registerDevice(input: Omit<EmployeeDevice, 'id' | 'enrolled' | 'compliant' | 'lastSeenAt'>): EmployeeDevice {
    const device: EmployeeDevice = {
      ...input,
      id: generateId('dev'),
      enrolled: false,
      compliant: false,
      lastSeenAt: new Date().toISOString(),
    };
    this.devices.set(device.id, device);
    return device;
  }

  enrollDevice(deviceId: string, encrypted: boolean): EmployeeDevice | undefined {
    const device = this.devices.get(deviceId);
    if (!device) return undefined;
    const now = new Date().toISOString();
    const updated: EmployeeDevice = {
      ...device,
      enrolled: true,
      encrypted,
      compliant: encrypted,
      enrolledAt: now,
      lastSeenAt: now,
    };
    this.devices.set(deviceId, updated);
    return updated;
  }

  listEmployeeDevices(employeeId: string): EmployeeDevice[] {
    return Array.from(this.devices.values()).filter(d => d.employeeId === employeeId);
  }

  // -------------------------------------------------------------------------
  // Training
  // -------------------------------------------------------------------------

  createTrainingRecord(input: Omit<TrainingRecord, 'id' | 'status'>): TrainingRecord {
    const record: TrainingRecord = {
      ...input,
      id: generateId('trn'),
      status: 'not_started',
    };
    this.trainingRecords.set(record.id, record);
    return record;
  }

  startTraining(recordId: string): TrainingRecord | undefined {
    const record = this.trainingRecords.get(recordId);
    if (!record || record.status !== 'not_started') return undefined;
    const updated: TrainingRecord = { ...record, status: 'in_progress', startedAt: new Date().toISOString() };
    this.trainingRecords.set(recordId, updated);
    return updated;
  }

  completeTraining(recordId: string, score?: number): TrainingRecord | undefined {
    const record = this.trainingRecords.get(recordId);
    if (!record || record.status !== 'in_progress') return undefined;
    const now = new Date().toISOString();
    const updated: TrainingRecord = {
      ...record,
      status: 'completed',
      completedAt: now,
      score,
      expiresAt: record.expiresAt ?? new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
    };
    this.trainingRecords.set(recordId, updated);
    return updated;
  }

  getExpiringTraining(withinDays: number = 30): TrainingRecord[] {
    const cutoff = Date.now() + withinDays * 24 * 60 * 60 * 1000;
    return Array.from(this.trainingRecords.values()).filter(
      r => r.status === 'completed' && r.expiresAt && new Date(r.expiresAt).getTime() <= cutoff,
    );
  }

  sendTrainingReminder(recordId: string): TrainingRecord | undefined {
    const record = this.trainingRecords.get(recordId);
    if (!record) return undefined;
    const updated: TrainingRecord = { ...record, reminderSentAt: new Date().toISOString() };
    this.trainingRecords.set(recordId, updated);
    return updated;
  }

  listEmployeeTraining(employeeId: string): TrainingRecord[] {
    return Array.from(this.trainingRecords.values()).filter(r => r.employeeId === employeeId);
  }

  // -------------------------------------------------------------------------
  // Compliance checks
  // -------------------------------------------------------------------------

  addComplianceCheck(employeeId: string, area: ComplianceArea, compliant: boolean, notes?: string): ComplianceCheck {
    const check: ComplianceCheck = {
      id: generateId('chk'),
      employeeId,
      area,
      compliant,
      verifiedAt: new Date().toISOString(),
      notes,
    };
    const existing = this.complianceChecks.get(employeeId) ?? [];
    existing.push(check);
    this.complianceChecks.set(employeeId, existing);
    return check;
  }

  getEmployeeCompliance(employeeId: string): ComplianceCheck[] {
    return this.complianceChecks.get(employeeId) ?? [];
  }

  isEmployeeCompliant(employeeId: string): boolean {
    const checks = this.getEmployeeCompliance(employeeId);
    for (const area of REQUIRED_COMPLIANCE_AREAS) {
      const latest = [...checks].reverse().find(c => c.area === area);
      if (!latest || !latest.compliant) return false;
    }
    return true;
  }

  // -------------------------------------------------------------------------
  // Access review campaigns
  // -------------------------------------------------------------------------

  createAccessReviewCampaign(input: Omit<AccessReviewCampaign, 'id' | 'status' | 'createdAt'>): AccessReviewCampaign {
    const campaign: AccessReviewCampaign = {
      ...input,
      id: generateId('arc'),
      status: 'active',
      createdAt: new Date().toISOString(),
    };
    this.accessReviewCampaigns.set(campaign.id, campaign);
    return campaign;
  }

  addAccessReviewItem(
    campaignId: string,
    input: Omit<AccessReviewItem, 'id' | 'campaignId' | 'recommendedAction' | 'decision'>,
  ): AccessReviewItem | undefined {
    if (!this.accessReviewCampaigns.has(campaignId)) return undefined;
    const item: AccessReviewItem = {
      ...input,
      id: generateId('ari'),
      campaignId,
      recommendedAction: 'review',
      decision: 'pending',
    };
    const existing = this.accessReviewItems.get(campaignId) ?? [];
    existing.push(item);
    this.accessReviewItems.set(campaignId, existing);
    return item;
  }

  decideAccessReviewItem(
    campaignId: string,
    itemId: string,
    decision: 'approved' | 'revoked',
    reviewerId: string,
  ): AccessReviewItem | undefined {
    const items = this.accessReviewItems.get(campaignId);
    if (!items) return undefined;
    const item = items.find(i => i.id === itemId);
    if (!item) return undefined;
    const updated: AccessReviewItem = {
      ...item,
      decision,
      reviewerId,
      decidedAt: new Date().toISOString(),
      recommendedAction: decision === 'approved' ? 'retain' : 'revoke',
    };
    const idx = items.indexOf(item);
    items[idx] = updated;
    return updated;
  }

  getCampaignItems(campaignId: string): AccessReviewItem[] {
    return this.accessReviewItems.get(campaignId) ?? [];
  }

  getCampaignSummary(campaignId: string): { total: number; approved: number; revoked: number; pending: number } {
    const items = this.getCampaignItems(campaignId);
    return {
      total: items.length,
      approved: items.filter(i => i.decision === 'approved').length,
      revoked: items.filter(i => i.decision === 'revoked').length,
      pending: items.filter(i => i.decision === 'pending').length,
    };
  }

  // -------------------------------------------------------------------------
  // HR system integration
  // -------------------------------------------------------------------------

  processHrWebhook(event: HrWebhookEvent): Employee | null {
    const payload = event.payload;
    const email = payload.email as string | undefined;

    switch (event.eventType) {
      case 'employee.created': {
        if (!email) return null;
        return this.createEmployee({
          externalHrId: (payload.id as string) ?? undefined,
          firstName: (payload.firstName as string) ?? '',
          lastName: (payload.lastName as string) ?? '',
          email,
          department: (payload.department as string) ?? '',
          role: (payload.role as string) ?? '',
          hireDate: (payload.hireDate as string) ?? undefined,
        });
      }
      case 'employee.updated': {
        const emp = email ? this.findEmployeeByEmail(email) : undefined;
        if (!emp) return null;
        const updated = { ...emp, updatedAt: new Date().toISOString() };
        if (payload.department) updated.department = payload.department as string;
        if (payload.role) updated.role = payload.role as string;
        this.employees.set(emp.id, updated);
        return updated;
      }
      case 'employee.terminated': {
        const emp = email ? this.findEmployeeByEmail(email) : undefined;
        if (!emp) return null;
        if (emp.state === 'active') {
          this.startOffboarding(emp.id);
        }
        return this.employees.get(emp.id) ?? null;
      }
      case 'employee.department_changed': {
        const emp = email ? this.findEmployeeByEmail(email) : undefined;
        if (!emp) return null;
        const updated = { ...emp, department: (payload.newDepartment as string) ?? emp.department, updatedAt: new Date().toISOString() };
        this.employees.set(emp.id, updated);
        return updated;
      }
      default:
        return null;
    }
  }

  private findEmployeeByEmail(email: string): Employee | undefined {
    return Array.from(this.employees.values()).find(e => e.email === email);
  }

  // -------------------------------------------------------------------------
  // Employee compliance dashboard
  // -------------------------------------------------------------------------

  getComplianceDashboard(): EmployeeComplianceDashboard {
    const employees = Array.from(this.employees.values()).filter(e => e.state !== 'prospect');
    let compliant = 0;
    let nonCompliant = 0;

    for (const emp of employees) {
      if (this.isEmployeeCompliant(emp.id)) {
        compliant++;
      } else {
        nonCompliant++;
      }
    }

    const byArea: ComplianceAreaSummary[] = REQUIRED_COMPLIANCE_AREAS.map(area => {
      let areaTotal = 0;
      let areaCompliant = 0;
      for (const emp of employees) {
        const checks = this.getEmployeeCompliance(emp.id);
        const latest = [...checks].reverse().find(c => c.area === area);
        if (latest) {
          areaTotal++;
          if (latest.compliant) areaCompliant++;
        }
      }
      return {
        area,
        total: areaTotal,
        compliant: areaCompliant,
        nonCompliant: areaTotal - areaCompliant,
      };
    });

    const recentActions: DashboardAction[] = [];
    for (const emp of employees) {
      const checks = this.getEmployeeCompliance(emp.id);
      for (const check of checks.slice(-3)) {
        recentActions.push({
          employeeId: emp.id,
          employeeName: `${emp.firstName} ${emp.lastName}`,
          area: check.area,
          action: check.compliant ? 'Verified compliant' : 'Flagged non-compliant',
          timestamp: check.verifiedAt ?? '',
        });
      }
    }
    recentActions.sort((a, b) => b.timestamp.localeCompare(a.timestamp));

    return {
      totalEmployees: employees.length,
      compliantEmployees: compliant,
      nonCompliantEmployees: nonCompliant,
      complianceRate: employees.length > 0 ? (compliant / employees.length) * 100 : 0,
      byArea,
      recentActions: recentActions.slice(0, 20),
      expiringTraining: this.getExpiringTraining(30),
    };
  }
}
