// ---------------------------------------------------------------------------
// Employee Lifecycle – shared types
// ---------------------------------------------------------------------------

export type EmployeeState =
  | 'prospect'
  | 'onboarding'
  | 'active'
  | 'offboarding'
  | 'offboarded';

export type ComplianceArea =
  | 'mfa_enrollment'
  | 'device_compliance'
  | 'policy_acknowledgment'
  | 'security_training'
  | 'background_check'
  | 'data_encryption';

export type TrainingStatus = 'not_started' | 'in_progress' | 'completed' | 'expired';

export type OffboardingAction =
  | 'access_revocation'
  | 'device_wipe'
  | 'credential_rotation'
  | 'exit_interview'
  | 'license_reclaim'
  | 'knowledge_transfer';

export type HrSystemType = 'bamboohr' | 'rippling' | 'gusto';

export type OffboardingActionStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

// ---------------------------------------------------------------------------
// Core entities
// ---------------------------------------------------------------------------

export interface Employee {
  id: string;
  externalHrId?: string;
  firstName: string;
  lastName: string;
  email: string;
  department: string;
  role: string;
  state: EmployeeState;
  hireDate?: string;
  offboardDate?: string;
  managerId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface EmployeeDevice {
  id: string;
  employeeId: string;
  type: 'laptop' | 'desktop' | 'mobile' | 'tablet';
  assetTag: string;
  encrypted: boolean;
  enrolled: boolean;
  compliant: boolean;
  lastSeenAt: string;
  enrolledAt?: string;
}

export interface TrainingRecord {
  id: string;
  employeeId: string;
  courseId: string;
  courseName: string;
  status: TrainingStatus;
  startedAt?: string;
  completedAt?: string;
  expiresAt?: string;
  score?: number;
  reminderSentAt?: string;
}

export interface ComplianceCheck {
  id: string;
  employeeId: string;
  area: ComplianceArea;
  compliant: boolean;
  verifiedAt?: string;
  notes?: string;
}

export interface AccessReviewItem {
  id: string;
  campaignId: string;
  employeeId: string;
  resourceType: string;
  resourceId: string;
  resourceName: string;
  accessLevel: string;
  recommendedAction: 'retain' | 'revoke' | 'review';
  reviewerId?: string;
  decision?: 'approved' | 'revoked' | 'pending';
  decidedAt?: string;
}

export interface AccessReviewCampaign {
  id: string;
  name: string;
  quarter: string;
  startDate: string;
  dueDate: string;
  status: 'draft' | 'active' | 'completed' | 'overdue';
  createdAt: string;
}

export interface OffboardingWorkflow {
  id: string;
  employeeId: string;
  initiatedAt: string;
  targetDate: string;
  completedAt?: string;
  actions: OffboardingActionItem[];
}

export interface OffboardingActionItem {
  id: string;
  action: OffboardingAction;
  status: OffboardingActionStatus;
  assignedTo?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface OnboardingWorkflow {
  id: string;
  employeeId: string;
  startedAt: string;
  completedAt?: string;
  mfaVerified: boolean;
  deviceCompliant: boolean;
  policyAcknowledged: boolean;
  securityTrainingCompleted: boolean;
  backgroundCheckPassed: boolean;
}

// ---------------------------------------------------------------------------
// HR integration
// ---------------------------------------------------------------------------

export interface HrWebhookEvent {
  system: HrSystemType;
  eventType: 'employee.created' | 'employee.updated' | 'employee.terminated' | 'employee.department_changed';
  payload: Record<string, unknown>;
  receivedAt: string;
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export interface EmployeeComplianceDashboard {
  totalEmployees: number;
  compliantEmployees: number;
  nonCompliantEmployees: number;
  complianceRate: number;
  byArea: ComplianceAreaSummary[];
  recentActions: DashboardAction[];
  expiringTraining: TrainingRecord[];
}

export interface ComplianceAreaSummary {
  area: ComplianceArea;
  total: number;
  compliant: number;
  nonCompliant: number;
}

export interface DashboardAction {
  employeeId: string;
  employeeName: string;
  area: ComplianceArea;
  action: string;
  timestamp: string;
}
