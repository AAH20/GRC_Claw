/**
 * GRC_Claw TypeScript SDK
 * ========================
 *
 * Complete TypeScript SDK for the GRC_Claw API.
 * Supports REST, GraphQL, and Webhook operations.
 *
 * Installation:
 *   npm install @grc-claw/sdk
 *
 * Usage:
 *   import { GRCClawClient } from '@grc-claw/sdk';
 *
 *   const client = new GRCClawClient({
 *     apiKey: 'grc_live_abc123...',
 *     tenantId: 'org-acme',
 *     environment: 'production',
 *   });
 *
 *   // Policy management
 *   const policy = await client.policies.create({
 *     policyKey: 'AI-ETHICS-001',
 *     name: 'Data Access Control Policy',
 *     category: 'privacy',
 *   });
 *
 *   // Enforcement decision
 *   const decision = await client.enforcement.decide({
 *     agentId: 'agent-42',
 *     action: 'read',
 *     resource: 's3://data/public/dataset.csv',
 *     context: { environment: 'production' },
 *   });
 */

// ============================================================
// Version
// ============================================================

export const VERSION = '1.0.0';

// ============================================================
// Enums
// ============================================================

export enum PolicyStatus {
  DRAFT = 'draft',
  REVIEW = 'review',
  ACTIVE = 'active',
  DEPRECATED = 'deprecated',
  ARCHIVED = 'archived',
}

export enum PolicyCategory {
  ETHICS = 'ethics',
  SAFETY = 'safety',
  PRIVACY = 'privacy',
  FAIRNESS = 'fairness',
}

export enum EvidenceType {
  ARTIFACT = 'artifact',
  OBSERVATION = 'observation',
  INTERVIEW = 'interview',
  ANALYSIS = 'analysis',
  LOG = 'log',
}

export enum VerificationLevel {
  L0 = 'L0',
  L1 = 'L1',
  L2 = 'L2',
  L3 = 'L3',
  L4 = 'L4',
}

export enum EnforcementVerdict {
  ALLOW = 'ALLOW',
  ALLOW_WITH_REDACTION = 'ALLOW_WITH_REDACTION',
  REQUIRE_APPROVAL = 'REQUIRE_APPROVAL',
  DENY = 'DENY',
  QUARANTINE = 'QUARANTINE',
}

export enum AssessmentType {
  RISK = 'risk',
  COMPLIANCE = 'compliance',
  MATURITY = 'maturity',
  READINESS = 'readiness',
}

export enum AssessmentStatus {
  PLANNED = 'planned',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export enum RiskTier {
  PROHIBITED = 'prohibited',
  HIGH = 'high',
  LIMITED = 'limited',
  MINIMAL = 'minimal',
}

export enum AgentLifecycleStage {
  PROPOSED = 'proposed',
  APPROVED = 'approved',
  ACTIVE = 'active',
  DEPRECATED = 'deprecated',
  TERMINATED = 'terminated',
}

export enum Environment {
  PRODUCTION = 'production',
  STAGING = 'staging',
  DEVELOPMENT = 'development',
}

// ============================================================
// Types
// ============================================================

export interface Pagination {
  nextCursor?: string;
  hasNext: boolean;
  total: number;
}

export interface Policy {
  id: string;
  policyKey: string;
  name: string;
  category: PolicyCategory;
  status: PolicyStatus;
  version: string;
  description?: string;
  frameworkTags: string[];
  effectiveDate?: string;
  expiryDate?: string;
  ownerId?: string;
  agentBindings: string[];
  metadata: Record<string, unknown>;
  createdAt?: string;
  updatedAt?: string;
}

export interface PolicyVersion {
  version: string;
  status: string;
  changeSummary?: string;
  createdAt?: string;
  createdBy?: string;
}

export interface PolicyDependency {
  targetPolicyId: string;
  targetPolicyName: string;
  relationType: string;
  description?: string;
}

export interface PolicyDependent {
  sourcePolicyId: string;
  sourcePolicyName: string;
  relationType: string;
  description?: string;
}

export interface PolicyDependencyGraph {
  policyId: string;
  dependencies: PolicyDependency[];
  dependents: PolicyDependent[];
}

export interface CompilationResult {
  policyId: string;
  compilationStatus: string;
  regoPolicy?: string;
  warnings: string[];
  errors: string[];
  compiledAt?: string;
}

export interface DryRunResultItem {
  inputIndex: number;
  decision: string;
  matchedRules: string[];
  evaluationTimeMs: number;
  reason?: string;
}

export interface DryRunSummary {
  total: number;
  allowed: number;
  denied: number;
  avgEvaluationTimeMs: number;
}

export interface DryRunResult {
  policyId: string;
  dryRunResults: DryRunResultItem[];
  summary: DryRunSummary;
}

export interface EvidenceSource {
  type: string;
  system: string;
  collectionMethod: string;
}

export interface EvidenceContent {
  format: string;
  data: string;
  hash?: string;
}

export interface EvidenceContext {
  environment: string;
  region?: string;
  timestamp?: string;
  metadata: Record<string, unknown>;
}

export interface ValidationStatus {
  status: string;
  validatedBy?: string;
  validatedAt?: string;
  confidenceScore: number;
}

export interface CustodyEvent {
  action: string;
  actor: string;
  timestamp?: string;
  hash?: string;
}

export interface Evidence {
  evidenceId: string;
  policyId?: string;
  assessmentId?: string;
  source?: EvidenceSource;
  evidenceType?: EvidenceType;
  content?: EvidenceContent;
  context?: EvidenceContext;
  validation?: ValidationStatus;
  verificationLevel?: VerificationLevel;
  chainOfCustody: CustodyEvent[];
  retentionClass?: string;
  createdAt?: string;
  expiresAt?: string;
}

export interface EvidenceVerification {
  evidenceId: string;
  verificationResult: Record<string, unknown>;
}

export interface ExportPackage {
  packageId: string;
  status: string;
  estimatedCompletion?: string;
  downloadUrl?: string;
  expiresAt?: string;
  packageHash?: string;
  manifest: Record<string, unknown>;
}

export interface EnforcementDecision {
  decisionId: string;
  verdict: EnforcementVerdict;
  policyId?: string;
  policyVersion?: string;
  agentId?: string;
  action?: string;
  resource?: string;
  context: Record<string, unknown>;
  evidenceHash?: string;
  timestamp?: string;
  ttl: number;
  signature?: string;
  matchedRules: string[];
  evaluationTimeMs: number;
  reason?: string;
}

export interface BatchSummary {
  total: number;
  allowed: number;
  denied: number;
  requireApproval: number;
  quarantined: number;
  avgEvaluationTimeMs: number;
}

export interface AssessmentFinding {
  id: string;
  findingKey: string;
  title: string;
  description?: string;
  severity?: string;
  category?: string;
  status?: string;
  policyId?: string;
  evidenceIds: string[];
  remediation?: string;
  remediatedBy?: string;
  remediatedAt?: string;
  dueDate?: string;
}

export interface Assessment {
  id: string;
  assessmentKey: string;
  title: string;
  assessmentType: AssessmentType;
  targetId: string;
  targetType: string;
  status: AssessmentStatus;
  description?: string;
  methodology?: string;
  score?: number;
  riskLevel?: string;
  startedAt?: string;
  completedAt?: string;
  nextAssessmentAt?: string;
  leadAssessor?: string;
  findings: AssessmentFinding[];
  metadata: Record<string, unknown>;
  createdAt?: string;
  updatedAt?: string;
}

export interface ComplianceFramework {
  id: string;
  frameworkKey: string;
  name: string;
  version: string;
  description?: string;
  authority?: string;
  effectiveDate?: string;
  controlCount: number;
}

export interface ComplianceControl {
  id: string;
  frameworkId?: string;
  controlKey?: string;
  title?: string;
  description?: string;
  category?: string;
  guidance?: string;
}

export interface ComplianceGap {
  controlId: string;
  controlTitle: string;
  status: string;
  severity?: string;
  evidenceCount: number;
  lastAssessed?: string;
}

export interface ComplianceTrend {
  direction: string;
  change: string;
  period: string;
}

export interface CompliancePosture {
  framework: string;
  targetId: string;
  targetType: string;
  controlsAssessed: number;
  controlsCompliant: number;
  controlsNonCompliant: number;
  controlsNotAssessed: number;
  complianceScore: number;
  gaps: ComplianceGap[];
  trend?: ComplianceTrend;
}

export interface ComplianceMapping {
  id: string;
  controlId: string;
  policyId?: string;
  assessmentId?: string;
  mappingType?: string;
  coverage?: string;
  notes?: string;
}

export interface AgentCapability {
  name: string;
  description?: string;
  permissions: string[];
  resourceScope?: string;
}

export interface AgentIdentity {
  spiffeId?: string;
  mtlsCert?: string;
  certExpiry?: string;
}

export interface TrustScore {
  value: number;
  grade: string;
  lastEvaluated?: string;
}

export interface Agent {
  id: string;
  name: string;
  type: string;
  framework: string;
  lifecycleStage: AgentLifecycleStage;
  riskTier: RiskTier;
  owner?: string;
  capabilities: AgentCapability[];
  identity?: AgentIdentity;
  trustScore?: TrustScore;
  policyBindings: string[];
  createdAt?: string;
  updatedAt?: string;
}

export interface AuditEvent {
  eventId: string;
  eventType: string;
  actor: Record<string, unknown>;
  resource: Record<string, unknown>;
  timestamp?: string;
  details: Record<string, unknown>;
  integrityHash?: string;
  previousEventHash?: string;
}

export interface AuditVerification {
  verificationStatus: string;
  eventsVerified: number;
  chainIntact: boolean;
  firstEventId?: string;
  lastEventId?: string;
  verifiedAt?: string;
}

export interface WebhookSubscription {
  subscriptionId: string;
  url: string;
  events: string[];
  secret: string;
  description?: string;
  active: boolean;
  metadata: Record<string, unknown>;
  createdAt?: string;
  deliveryStats: Record<string, unknown>;
}

export interface WebhookDelivery {
  deliveryId: string;
  subscriptionId: string;
  eventId: string;
  eventType: string;
  status: string;
  httpStatus?: number;
  responseTimeMs?: number;
  attempts: number;
  deliveredAt?: string;
  nextRetryAt?: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  components: Record<string, unknown>;
  timestamp?: string;
}

export interface ReadinessStatus {
  ready: boolean;
  checks: Record<string, unknown>;
}

// ============================================================
// Error Classes
// ============================================================

export class GRCClawError extends Error {
  code: string;
  status: number;
  requestId: string;

  constructor(message: string, code = '', status = 0, requestId = '') {
    super(message);
    this.name = 'GRCClawError';
    this.code = code;
    this.status = status;
    this.requestId = requestId;
  }
}

export class AuthenticationError extends GRCClawError {
  constructor(message: string, code = '', status = 401, requestId = '') {
    super(message, code, status, requestId);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends GRCClawError {
  constructor(message: string, code = '', status = 403, requestId = '') {
    super(message, code, status, requestId);
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends GRCClawError {
  constructor(message: string, code = '', status = 404, requestId = '') {
    super(message, code, status, requestId);
    this.name = 'NotFoundError';
  }
}

export class ConflictError extends GRCClawError {
  constructor(message: string, code = '', status = 409, requestId = '') {
    super(message, code, status, requestId);
    this.name = 'ConflictError';
  }
}

export class ValidationError extends GRCClawError {
  constructor(message: string, code = '', status = 400, requestId = '') {
    super(message, code, status, requestId);
    this.name = 'ValidationError';
  }
}

export class RateLimitError extends GRCClawError {
  retryAfter: number;

  constructor(message: string, retryAfter = 30, code = '', status = 429, requestId = '') {
    super(message, code, status, requestId);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

export class ServerError extends GRCClawError {
  constructor(message: string, code = '', status = 500, requestId = '') {
    super(message, code, status, requestId);
    this.name = 'ServerError';
  }
}

// ============================================================
// Webhook Verification
// ============================================================

export class WebhookVerifier {
  /**
   * Verify webhook signature.
   *
   * @param payloadBody - Raw request body string
   * @param signatureHeader - X-GRC-Signature header value (format: t=timestamp,v1=signature)
   * @param secret - Webhook secret
   * @returns True if signature is valid
   */
  static verify(payloadBody: string, signatureHeader: string, secret: string): boolean {
    const parts = signatureHeader.split(',');
    let timestamp: string | null = null;
    let signature: string | null = null;

    for (const part of parts) {
      const [key, ...rest] = part.split('=');
      const value = rest.join('=');
      if (key === 't') timestamp = value;
      if (key === 'v1') signature = value;
    }

    if (!timestamp || !signature) return false;

    // Check timestamp tolerance (5 minutes)
    const ts = parseInt(timestamp, 10);
    if (Math.abs(Date.now() / 1000 - ts) > 300) return false;

    const signedPayload = `${timestamp}.${payloadBody}`;
    const expected = createHmac('sha256', secret).update(signedPayload).digest('hex');

    return timingSafeEqual(signature, expected);
  }
}

// ============================================================
// Utility Functions
// ============================================================

import { createHmac, timingSafeEqual } from 'crypto';

function parseDateTime(value?: string): string | undefined {
  return value;
}

// ============================================================
// Base Client
// ============================================================

export interface ClientConfig {
  apiKey: string;
  tenantId: string;
  environment: Environment | string;
  timeout?: number;
  maxRetries?: number;
}

class BaseClient {
  protected apiKey: string;
  protected tenantId: string;
  protected environment: Environment;
  protected timeout: number;
  protected maxRetries: number;
  protected baseUrl: string;

  constructor(config: ClientConfig) {
    this.apiKey = config.apiKey;
    this.tenantId = config.tenantId;
    this.environment = typeof config.environment === 'string'
      ? Environment[config.environment.toUpperCase() as keyof typeof Environment]
      : config.environment;
    this.timeout = config.timeout ?? 30;
    this.maxRetries = config.maxRetries ?? 3;

    const baseUrls: Record<Environment, string> = {
      [Environment.PRODUCTION]: 'https://api.grc-claw.io',
      [Environment.STAGING]: 'https://api.staging.grc-claw.io',
      [Environment.DEVELOPMENT]: 'http://localhost:8080',
    };
    this.baseUrl = baseUrls[this.environment];
  }

  protected async request<T>(
    method: string,
    path: string,
    options: {
      params?: Record<string, unknown>;
      json?: Record<string, unknown>;
      headers?: Record<string, string>;
    } = {},
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`);
    if (options.params) {
      for (const [key, value] of Object.entries(options.params)) {
        if (value !== undefined && value !== null) {
          url.searchParams.set(key, String(value));
        }
      }
    }

    const headers: Record<string, string> = {
      'Authorization': `Bearer ${this.apiKey}`,
      'X-Tenant-ID': this.tenantId,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': `@grc-claw/sdk/${VERSION}`,
      ...options.headers,
    };

    let lastError: Error | null = null;

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout * 1000);

        const response = await fetch(url.toString(), {
          method,
          headers,
          body: options.json ? JSON.stringify(options.json) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        await this.handleError(response);

        if (response.status === 204) {
          return undefined as T;
        }

        return await response.json() as T;
      } catch (error) {
        lastError = error as Error;

        if (error instanceof RateLimitError) {
          if (attempt < this.maxRetries - 1) {
            await this.delay(error.retryAfter * 1000);
            continue;
          }
        }

        if (error instanceof ServerError) {
          if (attempt < this.maxRetries - 1) {
            await this.delay(Math.pow(2, attempt) * 1000);
            continue;
          }
        }

        if (error instanceof GRCClawError) {
          throw error;
        }

        throw error;
      }
    }

    throw lastError || new GRCClawError('Request failed after retries');
  }

  private async handleError(response: Response): Promise<void> {
    if (response.status < 400) return;

    let body: Record<string, unknown>;
    try {
      body = await response.json();
    } catch {
      body = { detail: response.statusText };
    }

    const code = (body.code as string) || 'UNKNOWN';
    const message = (body.detail as string) || 'Unknown error';
    const requestId = (body.request_id as string) || '';

    const errorMap: Record<number, new (msg: string, code: string, status: number, reqId: string) => GRCClawError> = {
      400: ValidationError,
      401: AuthenticationError,
      403: AuthorizationError,
      404: NotFoundError,
      409: ConflictError,
      422: ValidationError,
      429: RateLimitError,
    };

    const ErrorClass = errorMap[response.status] || ServerError;

    if (ErrorClass === RateLimitError) {
      const retryAfter = parseInt(response.headers.get('Retry-After') || '30', 10);
      throw new RateLimitError(message, retryAfter, code, response.status, requestId);
    }

    throw new ErrorClass(message, code, response.status, requestId);
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// ============================================================
// Policy Service
// ============================================================

export class PolicyService {
  private client: BaseClient;

  constructor(client: BaseClient) {
    this.client = client;
  }

  async list(options: {
    status?: PolicyStatus;
    category?: PolicyCategory;
    framework?: string;
    agentId?: string;
    limit?: number;
    cursor?: string;
  } = {}): Promise<{ data: Policy[]; pagination: Pagination }> {
    const params: Record<string, unknown> = { limit: options.limit ?? 50 };
    if (options.status) params.status = options.status;
    if (options.category) params.category = options.category;
    if (options.framework) params.framework = options.framework;
    if (options.agentId) params.agent_id = options.agentId;
    if (options.cursor) params.cursor = options.cursor;

    return this.client.request('GET', '/v1.0/policies', { params });
  }

  async create(input: {
    policyKey: string;
    name: string;
    category: PolicyCategory;
    description?: string;
    frameworkTags?: string[];
    cedarPolicy?: string;
    metadata?: Record<string, unknown>;
  }): Promise<Policy> {
    const body: Record<string, unknown> = {
      policy_key: input.policyKey,
      name: input.name,
      category: input.category,
    };
    if (input.description) body.description = input.description;
    if (input.frameworkTags) body.framework_tags = input.frameworkTags;
    if (input.cedarPolicy) body.cedar_policy = input.cedarPolicy;
    if (input.metadata) body.metadata = input.metadata;

    return this.client.request('POST', '/v1.0/policies', { json: body });
  }

  async get(policyId: string): Promise<Policy> {
    return this.client.request('GET', `/v1.0/policies/${policyId}`);
  }

  async update(policyId: string, input: {
    name?: string;
    description?: string;
    cedarPolicy?: string;
    metadata?: Record<string, unknown>;
  }): Promise<Policy> {
    const body: Record<string, unknown> = {};
    if (input.name) body.name = input.name;
    if (input.description) body.description = input.description;
    if (input.cedarPolicy) body.cedar_policy = input.cedarPolicy;
    if (input.metadata) body.metadata = input.metadata;

    return this.client.request('PUT', `/v1.0/policies/${policyId}`, { json: body });
  }

  async delete(policyId: string, force = false): Promise<void> {
    const params = force ? { force: 'true' } : undefined;
    return this.client.request('DELETE', `/v1.0/policies/${policyId}`, { params });
  }

  async compile(policyId: string): Promise<CompilationResult> {
    return this.client.request('POST', `/v1.0/policies/${policyId}/compile`);
  }

  async dryRun(policyId: string, testInputs: Record<string, unknown>[]): Promise<DryRunResult> {
    return this.client.request('POST', `/v1.0/policies/${policyId}/dry-run`, {
      json: { test_inputs: testInputs },
    });
  }

  async getVersions(policyId: string): Promise<{ data: PolicyVersion[] }> {
    return this.client.request('GET', `/v1.0/policies/${policyId}/versions`);
  }

  async getDependencies(policyId: string): Promise<PolicyDependencyGraph> {
    return this.client.request('GET', `/v1.0/policies/${policyId}/dependencies`);
  }
}

// ============================================================
// Evidence Service
// ============================================================

export class EvidenceService {
  private client: BaseClient;

  constructor(client: BaseClient) {
    this.client = client;
  }

  async search(options: {
    policyId?: string;
    assessmentId?: string;
    evidenceType?: EvidenceType;
    framework?: string;
    controlId?: string;
    verificationLevel?: VerificationLevel;
    environment?: string;
    dateFrom?: string;
    dateTo?: string;
    query?: string;
    limit?: number;
    cursor?: string;
  } = {}): Promise<{ data: Evidence[]; pagination: Pagination }> {
    const params: Record<string, unknown> = { limit: options.limit ?? 50 };
    if (options.policyId) params.policy_id = options.policyId;
    if (options.assessmentId) params.assessment_id = options.assessmentId;
    if (options.evidenceType) params.evidence_type = options.evidenceType;
    if (options.framework) params.framework = options.framework;
    if (options.controlId) params.control_id = options.controlId;
    if (options.verificationLevel) params.verification_level = options.verificationLevel;
    if (options.environment) params.environment = options.environment;
    if (options.dateFrom) params.date_from = options.dateFrom;
    if (options.dateTo) params.date_to = options.dateTo;
    if (options.query) params.query = options.query;
    if (options.cursor) params.cursor = options.cursor;

    return this.client.request('GET', '/v1.0/evidence', { params });
  }

  async submit(input: {
    source: { type: string; system: string; collectionMethod: string };
    evidenceType: EvidenceType;
    content: { format: string; data: string };
    policyId?: string;
    assessmentId?: string;
    context?: { environment: string; region?: string; metadata?: Record<string, unknown> };
    controlMapping?: { controlId: string; framework: string; controlTitle?: string };
  }): Promise<Evidence> {
    const body: Record<string, unknown> = {
      source: input.source,
      evidence_type: input.evidenceType,
      content: input.content,
    };
    if (input.policyId) body.policy_id = input.policyId;
    if (input.assessmentId) body.assessment_id = input.assessmentId;
    if (input.context) body.context = input.context;
    if (input.controlMapping) body.control_mapping = input.controlMapping;

    return this.client.request('POST', '/v1.0/evidence', { json: body });
  }

  async get(evidenceId: string): Promise<Evidence> {
    return this.client.request('GET', `/v1.0/evidence/${evidenceId}`);
  }

  async verify(evidenceId: string): Promise<EvidenceVerification> {
    return this.client.request('POST', `/v1.0/evidence/${evidenceId}/verify`);
  }

  async export(input: {
    framework: string;
    timeRange: { start: string; end: string };
    format?: string;
    includeChainOfCustody?: boolean;
  }): Promise<ExportPackage> {
    return this.client.request('POST', '/v1.0/evidence/export', {
      json: {
        framework: input.framework,
        time_range: input.timeRange,
        format: input.format ?? 'json',
        include_chain_of_custody: input.includeChainOfCustody ?? true,
      },
    });
  }

  async getExport(packageId: string): Promise<ExportPackage> {
    return this.client.request('GET', `/v1.0/evidence/export/${packageId}`);
  }
}

// ============================================================
// Enforcement Service
// ============================================================

export class EnforcementService {
  private client: BaseClient;

  constructor(client: BaseClient) {
    this.client = client;
  }

  async decide(input: {
    agentId: string;
    action: string;
    resource: string;
    context?: Record<string, unknown>;
    policyIds?: string[];
    includeEvidence?: boolean;
  }): Promise<EnforcementDecision> {
    const body: Record<string, unknown> = {
      agent_id: input.agentId,
      action: input.action,
      resource: input.resource,
      include_evidence: input.includeEvidence ?? true,
    };
    if (input.context) body.context = input.context;
    if (input.policyIds) body.policy_ids = input.policyIds;

    return this.client.request('POST', '/v1.0/enforcement/decide', { json: body });
  }

  async decideBatch(decisions: Array<{
    agentId: string;
    action: string;
    resource: string;
    context?: Record<string, unknown>;
  }>): Promise<{ results: EnforcementDecision[]; summary: BatchSummary }> {
    return this.client.request('POST', '/v1.0/enforcement/decide-batch', {
      json: { decisions },
    });
  }

  async get(decisionId: string): Promise<EnforcementDecision> {
    return this.client.request('GET', `/v1.0/enforcement/decisions/${decisionId}`);
  }

  async list(options: {
    agentId?: string;
    policyId?: string;
    verdict?: EnforcementVerdict;
    dateFrom?: string;
    dateTo?: string;
    limit?: number;
    cursor?: string;
  } = {}): Promise<{ data: EnforcementDecision[]; pagination: Pagination }> {
    const params: Record<string, unknown> = { limit: options.limit ?? 50 };
    if (options.agentId) params.agent_id = options.agentId;
    if (options.policyId) params.policy_id = options.policyId;
    if (options.verdict) params.verdict = options.verdict;
    if (options.dateFrom) params.date_from = options.dateFrom;
    if (options.dateTo) params.date_to = options.dateTo;
    if (options.cursor) params.cursor = options.cursor;

    return this.client.request('GET', '/v1.0/enforcement/decisions', { params });
  }
}

// ============================================================
// Assessment Service
// ============================================================

export class AssessmentService {
  private client: BaseClient;

  constructor(client: BaseClient) {
    this.client = client;
  }

  async list(options: {
    assessmentType?: AssessmentType;
    status?: AssessmentStatus;
    targetType?: string;
    targetId?: string;
    methodology?: string;
    limit?: number;
    cursor?: string;
  } = {}): Promise<{ data: Assessment[]; pagination: Pagination }> {
    const params: Record<string, unknown> = { limit: options.limit ?? 50 };
    if (options.assessmentType) params.assessment_type = options.assessmentType;
    if (options.status) params.status = options.status;
    if (options.targetType) params.target_type = options.targetType;
    if (options.targetId) params.target_id = options.targetId;
    if (options.methodology) params.methodology = options.methodology;
    if (options.cursor) params.cursor = options.cursor;

    return this.client.request('GET', '/v1.0/assessments', { params });
  }

  async create(input: {
    assessmentKey: string;
    title: string;
    assessmentType: AssessmentType;
    targetId: string;
    targetType: string;
    description?: string;
    methodology?: string;
    leadAssessor?: string;
    metadata?: Record<string, unknown>;
  }): Promise<Assessment> {
    const body: Record<string, unknown> = {
      assessment_key: input.assessmentKey,
      title: input.title,
      assessment_type: input.assessmentType,
      target_id: input.targetId,
      target_type: input.targetType,
    };
    if (input.description) body.description = input.description;
    if (input.methodology) body.methodology = input.methodology;
    if (input.leadAssessor) body.lead_assessor = input.leadAssessor;
    if (input.metadata) body.metadata = input.metadata;

    return this.client.request('POST', '/v1.0/assessments', { json: body });
  }

  async get(assessmentId: string): Promise<Assessment> {
    return this.client.request('GET', `/v1.0/assessments/${assessmentId}`);
  }

  async update(assessmentId: string, input: {
    title?: string;
    description?: string;
    status?: AssessmentStatus;
    methodology?: string;
    metadata?: Record<string, unknown>;
  }): Promise<Assessment> {
    const body: Record<string, unknown> = {};
    if (input.title) body.title = input.title;
    if (input.description) body.description = input.description;
    if (input.status) body.status = input.status;
    if (input.methodology) body.methodology = input.methodology;
    if (input.metadata) body.metadata = input.metadata;

    return this.client.request('PUT', `/v1.0/assessments/${assessmentId}`, { json: body });
  }

  async addFinding(assessmentId: string, input: {
    findingKey: string;
    title: string;
    severity: string;
    category: string;
    description?: string;
    policyId?: string;
    evidenceIds?: string[];
    remediation?: string;
    dueDate?: string;
  }): Promise<AssessmentFinding> {
    const body: Record<string, unknown> = {
      finding_key: input.findingKey,
      title: input.title,
      severity: input.severity,
      category: input.category,
    };
    if (input.description) body.description = input.description;
    if (input.policyId) body.policy_id = input.policyId;
    if (input.evidenceIds) body.evidence_ids = input.evidenceIds;
    if (input.remediation) body.remediation = input.remediation;
    if (input.dueDate) body.due_date = input.dueDate;

    return this.client.request('POST', `/v1.0/assessments/${assessmentId}/findings`, { json: body });
  }

  async generateReport(assessmentId: string, input: {
    format?: string;
    includeEvidence?: boolean;
    includeRemediation?: boolean;
  }): Promise<{ reportId: string; status: string }> {
    return this.client.request('POST', `/v1.0/assessments/${assessmentId}/report`, {
      json: {
        format: input.format ?? 'pdf',
        include_evidence: input.includeEvidence ?? true,
        include_remediation: input.includeRemediation ?? true,
      },
    });
  }
}

// ============================================================
// Compliance Service
// ============================================================

export class ComplianceService {
  private client: BaseClient;

  constructor(client: BaseClient) {
    this.client = client;
  }

  async listFrameworks(): Promise<{ data: ComplianceFramework[] }> {
    return this.client.request('GET', '/v1.0/compliance/frameworks');
  }

  async listControls(frameworkId: string, options: {
    category?: string;
    status?: string;
    targetId?: string;
  } = {}): Promise<{ data: ComplianceControl[] }> {
    const params: Record<string, unknown> = {};
    if (options.category) params.category = options.category;
    if (options.status) params.status = options.status;
    if (options.targetId) params.target_id = options.targetId;

    return this.client.request('GET', `/v1.0/compliance/frameworks/${frameworkId}/controls`, { params });
  }

  async getPosture(input: {
    framework: string;
    targetId: string;
    targetType: string;
  }): Promise<CompliancePosture> {
    return this.client.request('GET', '/v1.0/compliance/posture', {
      params: {
        framework: input.framework,
        target_id: input.targetId,
        target_type: input.targetType,
      },
    });
  }

  async createMapping(input: {
    controlId: string;
    mappingType: string;
    coverage: string;
    policyId?: string;
    assessmentId?: string;
    notes?: string;
  }): Promise<ComplianceMapping> {
    const body: Record<string, unknown> = {
      control_id: input.controlId,
      mapping_type: input.mappingType,
      coverage: input.coverage,
    };
    if (input.policyId) body.policy_id = input.policyId;
    if (input.assessmentId) body.assessment_id = input.assessmentId;
    if (input.notes) body.notes = input.notes;

    return this.client.request('POST', '/v1.0/compliance/mappings', { json: body });
  }

  async generateReport(input: {
    framework: string;
    timeRange: { start: string; end: string };
    format?: string;
    includeEvidence?: boolean;
    includeGaps?: boolean;
  }): Promise<{ reportId: string; status: string }> {
    return this.client.request('POST', '/v1.0/compliance/reports', {
      json: {
        framework: input.framework,
        time_range: input.timeRange,
        format: input.format ?? 'json',
        include_evidence: input.includeEvidence ?? true,
        include_gaps: input.includeGaps ?? true,
      },
    });
  }

  async crosswalk(options: {
    controlId?: string;
    framework?: string;
    targetFramework?: string;
  } = {}): Promise<Record<string, unknown>> {
    const params: Record<string, unknown> = {};
    if (options.controlId) params.control_id = options.controlId;
    if (options.framework) params.framework = options.framework;
    if (options.targetFramework) params.target_framework = options.targetFramework;

    return this.client.request('GET', '/v1.0/compliance/crosswalk', { params });
  }
}

// ============================================================
// Agent Service
// ============================================================

export class AgentService {
  private client: BaseClient;

  constructor(client: BaseClient) {
    this.client = client;
  }

  async list(options: {
    type?: string;
    framework?: string;
    lifecycleStage?: AgentLifecycleStage;
    riskTier?: RiskTier;
    trustScoreMin?: number;
    limit?: number;
    cursor?: string;
  } = {}): Promise<{ data: Agent[]; pagination: Pagination }> {
    const params: Record<string, unknown> = { limit: options.limit ?? 50 };
    if (options.type) params.type = options.type;
    if (options.framework) params.framework = options.framework;
    if (options.lifecycleStage) params.lifecycle_stage = options.lifecycleStage;
    if (options.riskTier) params.risk_tier = options.riskTier;
    if (options.trustScoreMin !== undefined) params.trust_score_min = options.trustScoreMin;
    if (options.cursor) params.cursor = options.cursor;

    return this.client.request('GET', '/v1.0/agents', { params });
  }

  async register(input: {
    name: string;
    type: string;
    framework: string;
    riskTier: RiskTier;
    owner?: string;
    capabilities?: Array<{ name: string; description?: string; permissions: string[]; resourceScope?: string }>;
  }): Promise<Agent> {
    const body: Record<string, unknown> = {
      name: input.name,
      type: input.type,
      framework: input.framework,
      risk_tier: input.riskTier,
    };
    if (input.owner) body.owner = input.owner;
    if (input.capabilities) body.capabilities = input.capabilities;

    return this.client.request('POST', '/v1.0/agents', { json: body });
  }

  async get(agentId: string): Promise<Agent> {
    return this.client.request('GET', `/v1.0/agents/${agentId}`);
  }

  async update(agentId: string, input: {
    name?: string;
    lifecycleStage?: AgentLifecycleStage;
    riskTier?: RiskTier;
    capabilities?: Array<{ name: string; description?: string; permissions: string[]; resourceScope?: string }>;
  }): Promise<Agent> {
    const body: Record<string, unknown> = {};
    if (input.name) body.name = input.name;
    if (input.lifecycleStage) body.lifecycle_stage = input.lifecycleStage;
    if (input.riskTier) body.risk_tier = input.riskTier;
    if (input.capabilities) body.capabilities = input.capabilities;

    return this.client.request('PUT', `/v1.0/agents/${agentId}`, { json: body });
  }

  async updateTrustScore(agentId: string, input: {
    value: number;
    grade: string;
    reason?: string;
  }): Promise<Agent> {
    const body: Record<string, unknown> = { value: input.value, grade: input.grade };
    if (input.reason) body.reason = input.reason;

    return this.client.request('POST', `/v1.0/agents/${agentId}/trust-score`, { json: body });
  }

  async bindPolicies(agentId: string, policyIds: string[]): Promise<Agent> {
    return this.client.request('POST', `/v1.0/agents/${agentId}/policy-bindings`, {
      json: { policy_ids: policyIds },
    });
  }
}

// ============================================================
// Audit Service
// ============================================================

export class AuditService {
  private client: BaseClient;

  constructor(client: BaseClient) {
    this.client = client;
  }

  async query(options: {
    eventType?: string;
    actorId?: string;
    resourceType?: string;
    resourceId?: string;
    dateFrom?: string;
    dateTo?: string;
    limit?: number;
  } = {}): Promise<{ data: AuditEvent[]; pagination: Pagination }> {
    const params: Record<string, unknown> = { limit: options.limit ?? 100 };
    if (options.eventType) params.event_type = options.eventType;
    if (options.actorId) params.actor_id = options.actorId;
    if (options.resourceType) params.resource_type = options.resourceType;
    if (options.resourceId) params.resource_id = options.resourceId;
    if (options.dateFrom) params.date_from = options.dateFrom;
    if (options.dateTo) params.date_to = options.dateTo;

    return this.client.request('GET', '/v1.0/audit', { params });
  }

  async verify(input: { fromEventId: string; toEventId: string }): Promise<AuditVerification> {
    return this.client.request('POST', '/v1.0/audit/verify', {
      json: { from_event_id: input.fromEventId, to_event_id: input.toEventId },
    });
  }
}

// ============================================================
// Webhook Service
// ============================================================

export class WebhookService {
  private client: BaseClient;

  constructor(client: BaseClient) {
    this.client = client;
  }

  async list(): Promise<{ data: WebhookSubscription[] }> {
    return this.client.request('GET', '/v1.0/webhooks/subscriptions');
  }

  async create(input: {
    url: string;
    events: string[];
    secret: string;
    description?: string;
    active?: boolean;
    metadata?: Record<string, unknown>;
  }): Promise<WebhookSubscription> {
    const body: Record<string, unknown> = {
      url: input.url,
      events: input.events,
      secret: input.secret,
      active: input.active ?? true,
    };
    if (input.description) body.description = input.description;
    if (input.metadata) body.metadata = input.metadata;

    return this.client.request('POST', '/v1.0/webhooks/subscriptions', { json: body });
  }

  async get(subscriptionId: string): Promise<WebhookSubscription> {
    return this.client.request('GET', `/v1.0/webhooks/subscriptions/${subscriptionId}`);
  }

  async update(subscriptionId: string, input: {
    url?: string;
    events?: string[];
    secret?: string;
    description?: string;
    active?: boolean;
    metadata?: Record<string, unknown>;
  }): Promise<WebhookSubscription> {
    const body: Record<string, unknown> = {};
    if (input.url) body.url = input.url;
    if (input.events) body.events = input.events;
    if (input.secret) body.secret = input.secret;
    if (input.description) body.description = input.description;
    if (input.active !== undefined) body.active = input.active;
    if (input.metadata) body.metadata = input.metadata;

    return this.client.request('PUT', `/v1.0/webhooks/subscriptions/${subscriptionId}`, { json: body });
  }

  async delete(subscriptionId: string): Promise<void> {
    return this.client.request('DELETE', `/v1.0/webhooks/subscriptions/${subscriptionId}`);
  }

  async test(subscriptionId: string): Promise<Record<string, unknown>> {
    return this.client.request('POST', `/v1.0/webhooks/subscriptions/${subscriptionId}/test`);
  }

  async getDeliveries(subscriptionId: string, options: {
    status?: string;
    dateFrom?: string;
    dateTo?: string;
  } = {}): Promise<{ data: WebhookDelivery[] }> {
    const params: Record<string, unknown> = {};
    if (options.status) params.status = options.status;
    if (options.dateFrom) params.date_from = options.dateFrom;
    if (options.dateTo) params.date_to = options.dateTo;

    return this.client.request('GET', `/v1.0/webhooks/subscriptions/${subscriptionId}/deliveries`, { params });
  }
}

// ============================================================
// System Service
// ============================================================

export class SystemService {
  private client: BaseClient;

  constructor(client: BaseClient) {
    this.client = client;
  }

  async health(): Promise<HealthStatus> {
    return this.client.request('GET', '/health');
  }

  async ready(): Promise<ReadinessStatus> {
    return this.client.request('GET', '/ready');
  }

  async metrics(): Promise<string> {
    const response = await fetch(`${(this.client as unknown as { baseUrl: string }).baseUrl}/metrics`, {
      headers: {
        'Authorization': `Bearer ${(this.client as unknown as { apiKey: string }).apiKey}`,
      },
    });
    return response.text();
  }
}

// ============================================================
// Main Client
// ============================================================

export class GRCClawClient {
  private baseClient: BaseClient;
  public policies: PolicyService;
  public evidence: EvidenceService;
  public enforcement: EnforcementService;
  public assessments: AssessmentService;
  public compliance: ComplianceService;
  public agents: AgentService;
  public audit: AuditService;
  public webhooks: WebhookService;
  public system: SystemService;

  constructor(config: ClientConfig) {
    this.baseClient = new BaseClient(config);
    this.policies = new PolicyService(this.baseClient);
    this.evidence = new EvidenceService(this.baseClient);
    this.enforcement = new EnforcementService(this.baseClient);
    this.assessments = new AssessmentService(this.baseClient);
    this.compliance = new ComplianceService(this.baseClient);
    this.agents = new AgentService(this.baseClient);
    this.audit = new AuditService(this.baseClient);
    this.webhooks = new WebhookService(this.baseClient);
    this.system = new SystemService(this.baseClient);
  }

  get tenantId(): string {
    return (this.baseClient as unknown as { tenantId: string }).tenantId;
  }

  get environment(): Environment {
    return (this.baseClient as unknown as { environment: Environment }).environment;
  }
}

// ============================================================
// Convenience Functions
// ============================================================

export function createClient(config: ClientConfig): GRCClawClient {
  return new GRCClawClient(config);
}

export function verifyWebhook(payloadBody: string, signatureHeader: string, secret: string): boolean {
  return WebhookVerifier.verify(payloadBody, signatureHeader, secret);
}

// ============================================================
// Exports
// ============================================================

export {
  VERSION,
  GRCClawClient,
  createClient,
  verifyWebhook,
  WebhookVerifier,
  BaseClient,
  PolicyService,
  EvidenceService,
  EnforcementService,
  AssessmentService,
  ComplianceService,
  AgentService,
  AuditService,
  WebhookService,
  SystemService,
  GRCClawError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  ConflictError,
  ValidationError,
  RateLimitError,
  ServerError,
};
