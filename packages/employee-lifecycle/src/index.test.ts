import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { EmployeeLifecycleEngine } from './EmployeeLifecycleEngine.js';

describe('EmployeeLifecycleEngine', () => {
  let engine: EmployeeLifecycleEngine;

  beforeEach(() => {
    engine = new EmployeeLifecycleEngine();
  });

  // -------------------------------------------------------------------------
  // Employee CRUD
  // -------------------------------------------------------------------------

  describe('Employee CRUD', () => {
    it('should create an employee in prospect state', () => {
      const emp = engine.createEmployee({
        firstName: 'Alice',
        lastName: 'Wong',
        email: 'alice@example.com',
        department: 'Engineering',
        role: 'Senior Engineer',
      });

      assert.ok(emp.id);
      assert.equal(emp.firstName, 'Alice');
      assert.equal(emp.state, 'prospect');
      assert.ok(emp.createdAt);
    });

    it('should retrieve an employee by id', () => {
      const emp = engine.createEmployee({
        firstName: 'Bob',
        lastName: 'Jones',
        email: 'bob@example.com',
        department: 'Sales',
        role: 'Account Executive',
      });

      const retrieved = engine.getEmployee(emp.id);
      assert.ok(retrieved);
      assert.equal(retrieved.email, 'bob@example.com');
    });

    it('should return undefined for non-existent employee', () => {
      assert.equal(engine.getEmployee('non-existent'), undefined);
    });

    it('should list employees with filters', () => {
      engine.createEmployee({ firstName: 'A', lastName: '1', email: 'a@e.com', department: 'Eng', role: 'Dev' });
      engine.createEmployee({ firstName: 'B', lastName: '2', email: 'b@e.com', department: 'Sales', role: 'AE' });

      assert.equal(engine.listEmployees().length, 2);
      assert.equal(engine.listEmployees({ department: 'Eng' }).length, 1);
    });
  });

  // -------------------------------------------------------------------------
  // State transitions
  // -------------------------------------------------------------------------

  describe('State transitions', () => {
    it('should transition prospect → onboarding → active', () => {
      const emp = engine.createEmployee({ firstName: 'C', lastName: '3', email: 'c@e.com', department: 'Eng', role: 'Dev' });
      engine.transitionEmployeeState(emp.id, 'onboarding');
      engine.transitionEmployeeState(emp.id, 'active');
      assert.equal(engine.getEmployee(emp.id)?.state, 'active');
    });

    it('should transition active → offboarding → offboarded', () => {
      const emp = engine.createEmployee({ firstName: 'D', lastName: '4', email: 'd@e.com', department: 'Eng', role: 'Dev' });
      engine.transitionEmployeeState(emp.id, 'onboarding');
      engine.transitionEmployeeState(emp.id, 'active');
      engine.transitionEmployeeState(emp.id, 'offboarding');
      engine.transitionEmployeeState(emp.id, 'offboarded');
      assert.equal(engine.getEmployee(emp.id)?.state, 'offboarded');
    });

    it('should throw on invalid transition', () => {
      const emp = engine.createEmployee({ firstName: 'E', lastName: '5', email: 'e@e.com', department: 'Eng', role: 'Dev' });
      assert.throws(() => engine.transitionEmployeeState(emp.id, 'active'));
    });

    it('should set hireDate when becoming active', () => {
      const emp = engine.createEmployee({ firstName: 'F', lastName: '6', email: 'f@e.com', department: 'Eng', role: 'Dev' });
      engine.transitionEmployeeState(emp.id, 'onboarding');
      const active = engine.transitionEmployeeState(emp.id, 'active');
      assert.ok(active?.hireDate);
    });

    it('should set offboardDate when starting offboarding', () => {
      const emp = engine.createEmployee({ firstName: 'G', lastName: '7', email: 'g@e.com', department: 'Eng', role: 'Dev' });
      engine.transitionEmployeeState(emp.id, 'onboarding');
      engine.transitionEmployeeState(emp.id, 'active');
      const off = engine.transitionEmployeeState(emp.id, 'offboarding');
      assert.ok(off?.offboardDate);
    });

    it('should return undefined for non-existent employee', () => {
      assert.equal(engine.transitionEmployeeState('nope', 'onboarding'), undefined);
    });
  });

  // -------------------------------------------------------------------------
  // Onboarding workflow
  // -------------------------------------------------------------------------

  describe('Onboarding workflow', () => {
    it('should start an onboarding workflow', () => {
      const emp = engine.createEmployee({ firstName: 'H', lastName: '8', email: 'h@e.com', department: 'Eng', role: 'Dev' });
      const wf = engine.startOnboarding(emp.id);
      assert.ok(wf.id);
      assert.equal(wf.mfaVerified, false);
      assert.equal(wf.employeeId, emp.id);
      assert.equal(engine.getEmployee(emp.id)?.state, 'onboarding');
    });

    it('should complete individual onboarding steps', () => {
      const emp = engine.createEmployee({ firstName: 'I', lastName: '9', email: 'i@e.com', department: 'Eng', role: 'Dev' });
      engine.startOnboarding(emp.id);

      engine.completeMfaVerification(emp.id);
      engine.completeDeviceCompliance(emp.id);
      engine.acknowledgePolicies(emp.id);

      const wf = engine.getOnboardingWorkflow(emp.id);
      assert.ok(wf);
      assert.equal(wf.mfaVerified, true);
      assert.equal(wf.deviceCompliant, true);
      assert.equal(wf.policyAcknowledged, true);
      assert.equal(wf.securityTrainingCompleted, false);
      assert.equal(engine.getEmployee(emp.id)?.state, 'onboarding');
    });

    it('should auto-complete onboarding when all steps done', () => {
      const emp = engine.createEmployee({ firstName: 'J', lastName: '10', email: 'j@e.com', department: 'Eng', role: 'Dev' });
      engine.startOnboarding(emp.id);

      engine.completeMfaVerification(emp.id);
      engine.completeDeviceCompliance(emp.id);
      engine.acknowledgePolicies(emp.id);
      engine.completeSecurityTraining(emp.id);
      engine.completeBackgroundCheck(emp.id);

      assert.equal(engine.getEmployee(emp.id)?.state, 'active');
      const wf = engine.getOnboardingWorkflow(emp.id);
      assert.ok(wf?.completedAt);
    });

    it('should add compliance checks for each onboarding step', () => {
      const emp = engine.createEmployee({ firstName: 'K', lastName: '11', email: 'k@e.com', department: 'Eng', role: 'Dev' });
      engine.startOnboarding(emp.id);
      engine.completeMfaVerification(emp.id);

      const checks = engine.getEmployeeCompliance(emp.id);
      assert.equal(checks.length, 1);
      assert.equal(checks[0].area, 'mfa_enrollment');
      assert.equal(checks[0].compliant, true);
    });

    it('should throw when starting onboarding for non-existent employee', () => {
      assert.throws(() => engine.startOnboarding('nope'));
    });

    it('should return existing workflow if already in progress', () => {
      const emp = engine.createEmployee({ firstName: 'L', lastName: '12', email: 'l@e.com', department: 'Eng', role: 'Dev' });
      const wf1 = engine.startOnboarding(emp.id);
      const wf2 = engine.startOnboarding(emp.id);
      assert.equal(wf1.id, wf2.id);
    });
  });

  // -------------------------------------------------------------------------
  // Offboarding workflow
  // -------------------------------------------------------------------------

  describe('Offboarding workflow', () => {
    it('should start an offboarding workflow with default actions', () => {
      const emp = engine.createEmployee({ firstName: 'M', lastName: '13', email: 'm@e.com', department: 'Eng', role: 'Dev' });
      engine.transitionEmployeeState(emp.id, 'onboarding');
      engine.transitionEmployeeState(emp.id, 'active');

      const wf = engine.startOffboarding(emp.id);
      assert.ok(wf.id);
      assert.equal(wf.actions.length, 6);
      assert.ok(wf.actions.some(a => a.action === 'access_revocation'));
      assert.ok(wf.actions.some(a => a.action === 'device_wipe'));
      assert.equal(engine.getEmployee(emp.id)?.state, 'offboarding');
    });

    it('should complete offboarding actions individually', () => {
      const emp = engine.createEmployee({ firstName: 'N', lastName: '14', email: 'n@e.com', department: 'Eng', role: 'Dev' });
      engine.transitionEmployeeState(emp.id, 'onboarding');
      engine.transitionEmployeeState(emp.id, 'active');
      engine.startOffboarding(emp.id);

      engine.completeOffboardingAction(emp.id, 'access_revocation', 'completed');
      engine.completeOffboardingAction(emp.id, 'device_wipe', 'in_progress');

      const wf = engine.getOffboardingWorkflow(emp.id);
      assert.ok(wf);
      const accessAction = wf.actions.find(a => a.action === 'access_revocation');
      assert.equal(accessAction?.status, 'completed');
      assert.ok(accessAction?.completedAt);
    });

    it('should auto-complete offboarding when all actions done', () => {
      const emp = engine.createEmployee({ firstName: 'O', lastName: '15', email: 'o@e.com', department: 'Eng', role: 'Dev' });
      engine.transitionEmployeeState(emp.id, 'onboarding');
      engine.transitionEmployeeState(emp.id, 'active');
      engine.startOffboarding(emp.id);

      const actions: Array<['access_revocation' | 'device_wipe' | 'credential_rotation' | 'exit_interview' | 'license_reclaim' | 'knowledge_transfer', 'completed' | 'failed']> = [
        ['access_revocation', 'completed'],
        ['device_wipe', 'completed'],
        ['credential_rotation', 'completed'],
        ['exit_interview', 'completed'],
        ['license_reclaim', 'completed'],
        ['knowledge_transfer', 'completed'],
      ];
      for (const [action, status] of actions) {
        engine.completeOffboardingAction(emp.id, action, status);
      }

      assert.equal(engine.getEmployee(emp.id)?.state, 'offboarded');
      const wf = engine.getOffboardingWorkflow(emp.id);
      assert.ok(wf?.completedAt);
    });

    it('should handle failed actions as terminal', () => {
      const emp = engine.createEmployee({ firstName: 'P', lastName: '16', email: 'p@e.com', department: 'Eng', role: 'Dev' });
      engine.transitionEmployeeState(emp.id, 'onboarding');
      engine.transitionEmployeeState(emp.id, 'active');
      engine.startOffboarding(emp.id);

      const actions: Array<['access_revocation' | 'device_wipe' | 'credential_rotation' | 'exit_interview' | 'license_reclaim' | 'knowledge_transfer', 'completed' | 'failed']> = [
        ['access_revocation', 'completed'],
        ['device_wipe', 'failed'],
        ['credential_rotation', 'completed'],
        ['exit_interview', 'completed'],
        ['license_reclaim', 'completed'],
        ['knowledge_transfer', 'completed'],
      ];
      for (const [action, status] of actions) {
        engine.completeOffboardingAction(emp.id, action, status);
      }

      assert.equal(engine.getEmployee(emp.id)?.state, 'offboarded');
    });

    it('should return existing workflow if already in progress', () => {
      const emp = engine.createEmployee({ firstName: 'Q', lastName: '17', email: 'q@e.com', department: 'Eng', role: 'Dev' });
      engine.transitionEmployeeState(emp.id, 'onboarding');
      engine.transitionEmployeeState(emp.id, 'active');
      const wf1 = engine.startOffboarding(emp.id);
      const wf2 = engine.startOffboarding(emp.id);
      assert.equal(wf1.id, wf2.id);
    });
  });

  // -------------------------------------------------------------------------
  // Devices
  // -------------------------------------------------------------------------

  describe('Devices', () => {
    it('should register a device', () => {
      const emp = engine.createEmployee({ firstName: 'R', lastName: '18', email: 'r@e.com', department: 'Eng', role: 'Dev' });
      const dev = engine.registerDevice({
        employeeId: emp.id,
        type: 'laptop',
        assetTag: 'LT-001',
        encrypted: false,
      });

      assert.ok(dev.id);
      assert.equal(dev.enrolled, false);
      assert.equal(dev.compliant, false);
    });

    it('should enroll a device', () => {
      const emp = engine.createEmployee({ firstName: 'S', lastName: '19', email: 's@e.com', department: 'Eng', role: 'Dev' });
      const dev = engine.registerDevice({ employeeId: emp.id, type: 'laptop', assetTag: 'LT-002', encrypted: false });
      const enrolled = engine.enrollDevice(dev.id, true);

      assert.ok(enrolled);
      assert.equal(enrolled.enrolled, true);
      assert.equal(enrolled.compliant, true);
      assert.ok(enrolled.enrolledAt);
    });

    it('should list employee devices', () => {
      const emp = engine.createEmployee({ firstName: 'T', lastName: '20', email: 't@e.com', department: 'Eng', role: 'Dev' });
      engine.registerDevice({ employeeId: emp.id, type: 'laptop', assetTag: 'LT-003', encrypted: false });
      engine.registerDevice({ employeeId: emp.id, type: 'mobile', assetTag: 'MB-001', encrypted: false });

      assert.equal(engine.listEmployeeDevices(emp.id).length, 2);
    });

    it('should return undefined for non-existent device', () => {
      assert.equal(engine.enrollDevice('nope', true), undefined);
    });
  });

  // -------------------------------------------------------------------------
  // Training
  // -------------------------------------------------------------------------

  describe('Training', () => {
    it('should create and start a training record', () => {
      const emp = engine.createEmployee({ firstName: 'U', lastName: '21', email: 'u@e.com', department: 'Eng', role: 'Dev' });
      const record = engine.createTrainingRecord({
        employeeId: emp.id,
        courseId: 'SEC-101',
        courseName: 'Security Awareness',
      });
      assert.equal(record.status, 'not_started');

      const started = engine.startTraining(record.id);
      assert.equal(started?.status, 'in_progress');
    });

    it('should complete a training record', () => {
      const emp = engine.createEmployee({ firstName: 'V', lastName: '22', email: 'v@e.com', department: 'Eng', role: 'Dev' });
      const record = engine.createTrainingRecord({ employeeId: emp.id, courseId: 'SEC-102', courseName: 'Phishing' });
      engine.startTraining(record.id);
      const completed = engine.completeTraining(record.id, 95);

      assert.equal(completed?.status, 'completed');
      assert.equal(completed?.score, 95);
      assert.ok(completed?.completedAt);
      assert.ok(completed?.expiresAt);
    });

    it('should find expiring training', () => {
      const emp = engine.createEmployee({ firstName: 'W', lastName: '23', email: 'w@e.com', department: 'Eng', role: 'Dev' });
      const record = engine.createTrainingRecord({
        employeeId: emp.id,
        courseId: 'SEC-103',
        courseName: 'Data Handling',
      });
      engine.startTraining(record.id);
      engine.completeTraining(record.id, 80);

      const expiring = engine.getExpiringTraining(365);
      assert.ok(expiring.length >= 1);
    });

    it('should send training reminder', () => {
      const emp = engine.createEmployee({ firstName: 'X', lastName: '24', email: 'x@e.com', department: 'Eng', role: 'Dev' });
      const record = engine.createTrainingRecord({ employeeId: emp.id, courseId: 'SEC-104', courseName: 'Compliance' });
      engine.startTraining(record.id);
      const reminded = engine.sendTrainingReminder(record.id);
      assert.ok(reminded?.reminderSentAt);
    });

    it('should list employee training', () => {
      const emp = engine.createEmployee({ firstName: 'Y', lastName: '25', email: 'y@e.com', department: 'Eng', role: 'Dev' });
      engine.createTrainingRecord({ employeeId: emp.id, courseId: 'SEC-105', courseName: 'A' });
      engine.createTrainingRecord({ employeeId: emp.id, courseId: 'SEC-106', courseName: 'B' });
      assert.equal(engine.listEmployeeTraining(emp.id).length, 2);
    });
  });

  // -------------------------------------------------------------------------
  // Compliance checks
  // -------------------------------------------------------------------------

  describe('Compliance checks', () => {
    it('should add compliance checks', () => {
      const emp = engine.createEmployee({ firstName: 'Z', lastName: '26', email: 'z@e.com', department: 'Eng', role: 'Dev' });
      engine.addComplianceCheck(emp.id, 'mfa_enrollment', true);
      engine.addComplianceCheck(emp.id, 'device_compliance', true);

      const checks = engine.getEmployeeCompliance(emp.id);
      assert.equal(checks.length, 2);
    });

    it('should detect compliant employee', () => {
      const emp = engine.createEmployee({ firstName: 'AA', lastName: '27', email: 'aa@e.com', department: 'Eng', role: 'Dev' });
      engine.addComplianceCheck(emp.id, 'mfa_enrollment', true);
      engine.addComplianceCheck(emp.id, 'device_compliance', true);
      engine.addComplianceCheck(emp.id, 'policy_acknowledgment', true);
      engine.addComplianceCheck(emp.id, 'security_training', true);
      engine.addComplianceCheck(emp.id, 'background_check', true);
      engine.addComplianceCheck(emp.id, 'data_encryption', true);

      assert.equal(engine.isEmployeeCompliant(emp.id), true);
    });

    it('should detect non-compliant employee', () => {
      const emp = engine.createEmployee({ firstName: 'BB', lastName: '28', email: 'bb@e.com', department: 'Eng', role: 'Dev' });
      engine.addComplianceCheck(emp.id, 'mfa_enrollment', true);
      engine.addComplianceCheck(emp.id, 'device_compliance', false);

      assert.equal(engine.isEmployeeCompliant(emp.id), false);
    });

    it('should use latest check per area', () => {
      const emp = engine.createEmployee({ firstName: 'CC', lastName: '29', email: 'cc@e.com', department: 'Eng', role: 'Dev' });
      engine.addComplianceCheck(emp.id, 'mfa_enrollment', false);
      engine.addComplianceCheck(emp.id, 'mfa_enrollment', true);

      assert.equal(engine.isEmployeeCompliant(emp.id), false);
    });
  });

  // -------------------------------------------------------------------------
  // Access review campaigns
  // -------------------------------------------------------------------------

  describe('Access review campaigns', () => {
    it('should create a campaign', () => {
      const campaign = engine.createAccessReviewCampaign({
        name: 'Q1 2025 Review',
        quarter: '2025-Q1',
        startDate: '2025-01-01',
        dueDate: '2025-03-31',
      });
      assert.ok(campaign.id);
      assert.equal(campaign.status, 'active');
    });

    it('should add items to a campaign', () => {
      const campaign = engine.createAccessReviewCampaign({
        name: 'Q1 2025',
        quarter: '2025-Q1',
        startDate: '2025-01-01',
        dueDate: '2025-03-31',
      });
      const emp = engine.createEmployee({ firstName: 'DD', lastName: '30', email: 'dd@e.com', department: 'Eng', role: 'Dev' });

      const item = engine.addAccessReviewItem(campaign.id, {
        employeeId: emp.id,
        resourceType: 'database',
        resourceId: 'db-prod-1',
        resourceName: 'Production DB',
        accessLevel: 'read',
      });

      assert.ok(item);
      assert.equal(item.decision, 'pending');
    });

    it('should decide on access review items', () => {
      const campaign = engine.createAccessReviewCampaign({
        name: 'Q2 2025',
        quarter: '2025-Q2',
        startDate: '2025-04-01',
        dueDate: '2025-06-30',
      });
      const emp = engine.createEmployee({ firstName: 'EE', lastName: '31', email: 'ee@e.com', department: 'Eng', role: 'Dev' });

      const item = engine.addAccessReviewItem(campaign.id, {
        employeeId: emp.id,
        resourceType: 's3_bucket',
        resourceId: 'bucket-1',
        resourceName: 'Data Lake',
        accessLevel: 'write',
      });

      engine.decideAccessReviewItem(campaign.id, item!.id, 'revoked', 'reviewer-1');

      const items = engine.getCampaignItems(campaign.id);
      assert.equal(items[0].decision, 'revoked');
      assert.equal(items[0].reviewerId, 'reviewer-1');
    });

    it('should provide campaign summary', () => {
      const campaign = engine.createAccessReviewCampaign({
        name: 'Q3 2025',
        quarter: '2025-Q3',
        startDate: '2025-07-01',
        dueDate: '2025-09-30',
      });
      const emp = engine.createEmployee({ firstName: 'FF', lastName: '32', email: 'ff@e.com', department: 'Eng', role: 'Dev' });

      const item1 = engine.addAccessReviewItem(campaign.id, { employeeId: emp.id, resourceType: 'api', resourceId: 'api-1', resourceName: 'API', accessLevel: 'admin' });
      const item2 = engine.addAccessReviewItem(campaign.id, { employeeId: emp.id, resourceType: 'db', resourceId: 'db-1', resourceName: 'DB', accessLevel: 'read' });

      engine.decideAccessReviewItem(campaign.id, item1!.id, 'approved', 'reviewer-1');
      engine.decideAccessReviewItem(campaign.id, item2!.id, 'revoked', 'reviewer-1');

      const summary = engine.getCampaignSummary(campaign.id);
      assert.equal(summary.total, 2);
      assert.equal(summary.approved, 1);
      assert.equal(summary.revoked, 1);
      assert.equal(summary.pending, 0);
    });

    it('should return undefined for non-existent campaign', () => {
      const emp = engine.createEmployee({ firstName: 'GG', lastName: '33', email: 'gg@e.com', department: 'Eng', role: 'Dev' });
      const item = engine.addAccessReviewItem('nope', {
        employeeId: emp.id,
        resourceType: 'db',
        resourceId: 'db-1',
        resourceName: 'DB',
        accessLevel: 'read',
      });
      assert.equal(item, undefined);
    });
  });

  // -------------------------------------------------------------------------
  // HR integration
  // -------------------------------------------------------------------------

  describe('HR system integration', () => {
    it('should handle employee.created webhook', () => {
      const emp = engine.processHrWebhook({
        system: 'bamboohr',
        eventType: 'employee.created',
        payload: { id: 'hr-001', firstName: 'New', lastName: 'Hire', email: 'new@e.com', department: 'Eng', role: 'Dev' },
        receivedAt: new Date().toISOString(),
      });
      assert.ok(emp);
      assert.equal(emp?.firstName, 'New');
      assert.equal(emp?.state, 'prospect');
    });

    it('should handle employee.updated webhook', () => {
      engine.createEmployee({ firstName: 'Old', lastName: 'Name', email: 'old@e.com', department: 'Eng', role: 'Dev' });

      const updated = engine.processHrWebhook({
        system: 'rippling',
        eventType: 'employee.updated',
        payload: { email: 'old@e.com', department: 'Marketing' },
        receivedAt: new Date().toISOString(),
      });

      assert.ok(updated);
      assert.equal(updated?.department, 'Marketing');
    });

    it('should handle employee.terminated webhook by starting offboarding', () => {
      const emp = engine.createEmployee({ firstName: 'Term', lastName: 'Inee', email: 'term@e.com', department: 'Eng', role: 'Dev' });
      engine.transitionEmployeeState(emp.id, 'onboarding');
      engine.transitionEmployeeState(emp.id, 'active');

      engine.processHrWebhook({
        system: 'gusto',
        eventType: 'employee.terminated',
        payload: { email: 'term@e.com' },
        receivedAt: new Date().toISOString(),
      });

      assert.equal(engine.getEmployee(emp.id)?.state, 'offboarding');
    });

    it('should handle department_changed webhook', () => {
      engine.createEmployee({ firstName: 'Move', lastName: 'Person', email: 'move@e.com', department: 'Eng', role: 'Dev' });

      engine.processHrWebhook({
        system: 'bamboohr',
        eventType: 'employee.department_changed',
        payload: { email: 'move@e.com', newDepartment: 'Security' },
        receivedAt: new Date().toISOString(),
      });

      assert.equal(engine.getEmployee(Array.from(engine.listEmployees().values()).find(e => e.email === 'move@e.com')?.id ?? '')?.department, 'Security');
    });

    it('should return null for unknown event type', () => {
      const result = engine.processHrWebhook({
        system: 'bamboohr',
        eventType: 'employee.created' as 'employee.created',
        payload: {},
        receivedAt: new Date().toISOString(),
      });
      assert.equal(result, null);
    });
  });

  // -------------------------------------------------------------------------
  // Compliance dashboard
  // -------------------------------------------------------------------------

  describe('Compliance dashboard', () => {
    it('should generate dashboard data', () => {
      const emp1 = engine.createEmployee({ firstName: 'Dash', lastName: '1', email: 'd1@e.com', department: 'Eng', role: 'Dev' });
      const emp2 = engine.createEmployee({ firstName: 'Dash', lastName: '2', email: 'd2@e.com', department: 'Sales', role: 'AE' });

      engine.transitionEmployeeState(emp1.id, 'onboarding');
      engine.transitionEmployeeState(emp1.id, 'active');
      engine.transitionEmployeeState(emp2.id, 'onboarding');
      engine.transitionEmployeeState(emp2.id, 'active');

      engine.addComplianceCheck(emp1.id, 'mfa_enrollment', true);
      engine.addComplianceCheck(emp1.id, 'device_compliance', true);
      engine.addComplianceCheck(emp1.id, 'policy_acknowledgment', true);
      engine.addComplianceCheck(emp1.id, 'security_training', true);
      engine.addComplianceCheck(emp1.id, 'background_check', true);
      engine.addComplianceCheck(emp1.id, 'data_encryption', true);

      engine.addComplianceCheck(emp2.id, 'mfa_enrollment', true);
      engine.addComplianceCheck(emp2.id, 'device_compliance', false);

      const dashboard = engine.getComplianceDashboard();
      assert.ok(dashboard.totalEmployees >= 2);
      assert.ok(dashboard.complianceRate >= 0);
      assert.ok(dashboard.byArea.length === 6);
      assert.ok(Array.isArray(dashboard.recentActions));
    });

    it('should show zero employees when empty', () => {
      const dashboard = engine.getComplianceDashboard();
      assert.equal(dashboard.totalEmployees, 0);
      assert.equal(dashboard.complianceRate, 0);
    });
  });
});
