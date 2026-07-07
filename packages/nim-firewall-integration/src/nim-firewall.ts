import { createHash, createHmac, randomBytes } from 'node:crypto';
import { PromptInjectionDetector } from './prompt-injection-detector.js';
import { DataBoundaryEnforcer } from './data-boundary-enforcer.js';
import { AuditLogger } from './audit-logger.js';
import type {
  NimRequest,
  NimResponse,
  FirewallDecision,
  PolicyRule,
  PolicyViolation,
  DataBoundary,
} from './types.js';

export interface NimFirewallConfig {
  secretKey: string;
  rules?: PolicyRule[];
  boundaries?: DataBoundary[];
  injectionThreshold?: number;
  auditSecretKey?: string;
  enableAudit?: boolean;
  enableInjectionDetection?: boolean;
  enableBoundaryEnforcement?: boolean;
}

const DEFAULT_RULES: PolicyRule[] = [
  {
    id: 'rule-no-exec',
    name: 'Block code execution prompts',
    conditions: [{ field: 'prompt', operator: 'regex', value: /exec\s*\(|eval\s*\(|system\s*\(/i }],
    action: 'block',
    priority: 100,
  },
  {
    id: 'rule-max-temp',
    name: 'Cap temperature at 0.9',
    conditions: [{ field: 'temperature', operator: 'gt', value: 0.9 }],
    action: 'block',
    priority: 50,
  },
  {
    id: 'rule-no-admin',
    name: 'Block admin-mode requests',
    conditions: [{ field: 'prompt', operator: 'regex', value: /admin\s+mode|root\s+access/i }],
    action: 'block',
    priority: 90,
  },
];

export class NimFirewall {
  private rules: PolicyRule[];
  private injectionDetector: PromptInjectionDetector;
  private boundaryEnforcer: DataBoundaryEnforcer;
  private auditLogger: AuditLogger | null;
  private enableInjectionDetection: boolean;
  private enableBoundaryEnforcement: boolean;
  private secretKey: string;

  constructor(config: NimFirewallConfig) {
    this.secretKey = config.secretKey;
    this.rules = [...DEFAULT_RULES, ...(config.rules ?? [])];
    this.rules.sort((a, b) => b.priority - a.priority);

    this.injectionDetector = new PromptInjectionDetector();
    this.boundaryEnforcer = new DataBoundaryEnforcer(config.boundaries);
    this.enableInjectionDetection = config.enableInjectionDetection ?? true;
    this.enableBoundaryEnforcement = config.enableBoundaryEnforcement ?? true;

    if (config.enableAudit ?? true) {
      this.auditLogger = new AuditLogger({
        secretKey: config.auditSecretKey ?? config.secretKey,
      });
    } else {
      this.auditLogger = null;
    }
  }

  evaluateRequest(request: NimRequest): FirewallDecision {
    const violations: PolicyViolation[] = [];
    let sandbox = false;
    let requiresApproval = false;

    for (const rule of this.rules) {
      if (rule.enabled === false) continue;

      const matched = rule.conditions.every((cond) =>
        this.evaluateCondition(request, cond)
      );

      if (matched) {
        violations.push({
          ruleId: rule.id,
          ruleName: rule.name,
          severity: this.actionToSeverity(rule.action),
          detail: `Rule '${rule.name}' triggered by request`,
        });

        if (rule.action === 'block') {
          return this.buildDecision(false, violations, request, true, false, sandbox);
        }
        if (rule.action === 'sandbox') sandbox = true;
        if (rule.action === 'approve') requiresApproval = true;
      }
    }

    if (this.enableInjectionDetection) {
      const injectionResult = this.injectionDetector.detect(
        request.prompt,
        request.systemPrompt
      );

      if (injectionResult.action === 'block') {
        violations.push({
          ruleId: 'injection-detector',
          ruleName: 'Prompt Injection Detected',
          severity: 'critical',
          detail: `Injection patterns: ${injectionResult.patterns.join(', ')} (score: ${injectionResult.score.toFixed(2)})`,
        });
        return this.buildDecision(false, violations, request, true, false, true);
      }

      if (injectionResult.action === 'flag') {
        violations.push({
          ruleId: 'injection-detector',
          ruleName: 'Suspicious Prompt',
          severity: 'high',
          detail: `Possible injection patterns: ${injectionResult.patterns.join(', ')} (score: ${injectionResult.score.toFixed(2)})`,
        });
        requiresApproval = true;
      }
    }

    if (this.enableBoundaryEnforcement) {
      const boundaryResult = this.boundaryEnforcer.enforceRequest(request);

      for (const v of boundaryResult.violations) {
        violations.push({
          ruleId: 'boundary-enforcer',
          ruleName: 'Data Boundary Violation',
          severity: 'high',
          detail: v,
        });
      }

      if (boundaryResult.requiresSandbox) sandbox = true;
      if (boundaryResult.requiresApproval) requiresApproval = true;

      if (violations.some((v) => v.ruleId === 'boundary-enforcer' && v.severity === 'high')) {
        return this.buildDecision(false, violations, request, true, requiresApproval, sandbox);
      }
    }

    const allowed = !violations.some((v) => v.severity === 'critical' || v.severity === 'high');
    return this.buildDecision(allowed, violations, request, false, requiresApproval, sandbox);
  }

  evaluateResponse(response: NimResponse, request: NimRequest): FirewallDecision {
    const violations: PolicyViolation[] = [];

    if (this.enableBoundaryEnforcement) {
      const detectedBoundaries = this.boundaryEnforcer.detectBoundaries(request.prompt);
      const boundaryResult = this.boundaryEnforcer.enforceResponse(response, detectedBoundaries);

      for (const v of boundaryResult.violations) {
        violations.push({
          ruleId: 'response-boundary',
          ruleName: 'Response Data Boundary Violation',
          severity: 'high',
          detail: v,
        });
      }
    }

    if (response.finishReason === 'safety') {
      violations.push({
        ruleId: 'safety-trigger',
        ruleName: 'Safety Filter Triggered',
        severity: 'medium',
        detail: 'Response was flagged by safety filter',
      });
    }

    const allowed = !violations.some((v) => v.severity === 'high');
    return this.buildDecision(allowed, violations, request, false, false, false);
  }

  blockPromptInjection(prompt: string): {
    detected: boolean;
    action: 'allow' | 'flag' | 'block';
    score: number;
    patterns: string[];
  } {
    return this.injectionDetector.detect(prompt);
  }

  enforceDataBoundary(request: NimRequest, boundary: DataBoundary): {
    allowed: boolean;
    violations: string[];
    requiresSandbox: boolean;
    requiresApproval: boolean;
  } {
    this.boundaryEnforcer.addBoundary(boundary);
    const result = this.boundaryEnforcer.enforceRequest(request);

    return {
      allowed: result.allowed,
      violations: result.violations,
      requiresSandbox: result.requiresSandbox,
      requiresApproval: result.requiresApproval,
    };
  }

  generateReceipt(
    request: NimRequest,
    decision: FirewallDecision
  ): { hash: string; previousHash: string; timestamp: string; signature: string } {
    const requestHash = createHash('sha256')
      .update(JSON.stringify(request))
      .digest('hex');

    const payload = {
      requestHash,
      decisionHash: createHash('sha256')
        .update(JSON.stringify(decision))
        .digest('hex'),
      timestamp: new Date().toISOString(),
    };

    const hash = createHash('sha256').update(JSON.stringify(payload)).digest('hex');
    const signature = createHmac('sha256', this.secretKey).update(hash).digest('hex');

    return {
      hash,
      previousHash: decision.receiptHash,
      timestamp: payload.timestamp,
      signature,
    };
  }

  logAction(
    request: NimRequest,
    decision: FirewallDecision,
    response?: NimResponse
  ): void {
    this.auditLogger?.log(request, decision, response);
  }

  addRule(rule: PolicyRule): void {
    this.rules.push(rule);
    this.rules.sort((a, b) => b.priority - a.priority);
  }

  removeRule(ruleId: string): void {
    this.rules = this.rules.filter((r) => r.id !== ruleId);
  }

  getRules(): PolicyRule[] {
    return [...this.rules];
  }

  getAuditLogger(): AuditLogger | null {
    return this.auditLogger;
  }

  private evaluateCondition(
    request: NimRequest,
    condition: { field: string; operator: string; value: unknown }
  ): boolean {
    const fieldValue = (request as Record<string, unknown>)[condition.field];

    switch (condition.operator) {
      case 'equals':
        return fieldValue === condition.value;
      case 'contains':
        return String(fieldValue).includes(String(condition.value));
      case 'matches':
        return (condition.value as RegExp).test(String(fieldValue));
      case 'regex':
        return (condition.value as RegExp).test(String(fieldValue));
      case 'gt':
        return typeof fieldValue === 'number' && fieldValue > (condition.value as number);
      case 'lt':
        return typeof fieldValue === 'number' && fieldValue < (condition.value as number);
      case 'in':
        return (condition.value as unknown[]).includes(fieldValue);
      default:
        return false;
    }
  }

  private buildDecision(
    allowed: boolean,
    violations: PolicyViolation[],
    request: NimRequest,
    sandbox: boolean,
    requiresApproval: boolean,
    sandboxForced: boolean
  ): FirewallDecision {
    const riskScore = this.calculateRiskScore(violations);

    const decision: FirewallDecision = {
      allowed,
      reason: violations.length > 0
        ? violations.map((v) => v.detail).join('; ')
        : 'All policy checks passed',
      sandbox: sandboxForced || sandbox,
      requiresApproval,
      receiptHash: '',
      violations,
      riskScore,
      timestamp: new Date().toISOString(),
      requestId: request.requestId ?? this.generateId(),
    };

    decision.receiptHash = this.computeReceiptHash(request, decision);

    if (this.auditLogger) {
      this.auditLogger.log(request, decision);
    }

    return decision;
  }

  private calculateRiskScore(violations: PolicyViolation[]): number {
    if (violations.length === 0) return 0;

    const severityWeights: Record<string, number> = {
      critical: 1.0,
      high: 0.75,
      medium: 0.5,
      low: 0.25,
    };

    const total = violations.reduce(
      (sum, v) => sum + (severityWeights[v.severity] ?? 0),
      0
    );

    return Math.min(1, total / Math.max(violations.length, 1));
  }

  private computeReceiptHash(request: NimRequest, decision: FirewallDecision): string {
    const payload = {
      requestId: request.requestId,
      model: request.model,
      allowed: decision.allowed,
      riskScore: decision.riskScore,
      timestamp: decision.timestamp,
      nonce: randomBytes(16).toString('hex'),
    };

    return createHash('sha256').update(JSON.stringify(payload)).digest('hex');
  }

  private actionToSeverity(action: string): PolicyViolation['severity'] {
    switch (action) {
      case 'block': return 'critical';
      case 'approve': return 'high';
      case 'sandbox': return 'medium';
      case 'redact': return 'medium';
      case 'log': return 'low';
      default: return 'low';
    }
  }

  private generateId(): string {
    return `req_${Date.now()}_${randomBytes(8).toString('hex')}`;
  }
}
