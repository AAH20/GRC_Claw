import { createHash } from 'node:crypto';
import type {
  ComplianceFinding,
  ComplianceRule,
  PRReview,
  PRInfo,
  PRReviewSummary,
  AutoFix,
  FileChange,
  Severity,
} from '../types.js';

interface RulePattern {
  pattern: RegExp;
  controlIds: string[];
  severity: Severity;
  message: string;
  description: string;
}

const COMPLIANCE_RULES: ComplianceRule[] = [
  { id: 'hardcoded-secret', name: 'Hardcoded Secret Detection', description: 'Detects hardcoded secrets, API keys, and credentials in source code', framework: 'iso27001', controlId: 'A.8.2', severity: 'error', pattern: '(password|secret|api[_-]?key|token|credential)\\s*[=:]\\s*["\'][^"\']{8,}["\']', checkType: 'pattern' },
  { id: 'mfa-bypass', name: 'MFA Bypass Detection', description: 'Detects code that bypasses or disables MFA requirements', framework: 'soc2', controlId: 'CC6.1', severity: 'error', pattern: '(mfa|two[_-]?factor|2fa)\\s*[=:]\\s*(false|disabled|off|skip)', checkType: 'pattern' },
  { id: 'weak-encryption', name: 'Weak Encryption Detection', description: 'Detects usage of weak or deprecated encryption algorithms', framework: 'iso27001', controlId: 'A.8.2', severity: 'error', pattern: '(md5|sha1|des|rc4|3des)\\b', checkType: 'pattern' },
  { id: 'sql-injection', name: 'SQL Injection Risk', description: 'Detects potential SQL injection vulnerabilities', framework: 'soc2', controlId: 'CC6.1', severity: 'warning', pattern: '(query|execute|raw)\\s*\\([^)]*\\+\\s*[^)]*\\)', checkType: 'pattern' },
  { id: 'missing-auth', name: 'Missing Authentication Check', description: 'Detects API routes without authentication middleware', framework: 'soc2', controlId: 'CC6.1', severity: 'warning', pattern: '(app|router)\\.(get|post|put|delete|patch)\\s*\\([^,]+\\s*,\\s*(?!.*auth)', checkType: 'pattern' },
  { id: 'logging-sensitive', name: 'Sensitive Data Logging', description: 'Detects logging of sensitive data like passwords or PII', framework: 'gdpr', controlId: 'Art.5', severity: 'warning', pattern: '(log|console\\.(log|warn|error))\\s*\\([^)]*(password|ssn|credit[_-]?card|api[_-]?key)', checkType: 'pattern' },
  { id: 'cors-wildcard', name: 'CORS Wildcard', description: 'Detects overly permissive CORS configurations', framework: 'iso27001', controlId: 'A.8.9', severity: 'warning', pattern: 'access[_-]?control[_-]?allow[_-]?origin.*\\*', checkType: 'pattern' },
  { id: 'insecure-deserialization', name: 'Insecure Deserialization', description: 'Detects unsafe deserialization of untrusted data', framework: 'soc2', controlId: 'CC6.1', severity: 'warning', pattern: '(eval|Function\\s*\\(|JSON\\.parse\\s*\\([^)]*req)', checkType: 'pattern' },
  { id: 'missing-encryption-config', name: 'Missing Encryption Configuration', description: 'Detects infrastructure configs without encryption at rest', framework: 'hipaa', controlId: '164.312', severity: 'error', pattern: '(storage|bucket|blob)\\s*\\{[^}]*encryption[^}]*false', checkType: 'pattern' },
  { id: 'excessive-permissions', name: 'Excessive Permissions', description: 'Detects IAM policies with overly broad permissions', framework: 'nist-csf', controlId: 'PR.AC', severity: 'warning', pattern: '"Action"\\s*:\\s*"\\*"', checkType: 'pattern' },
  { id: 'missing-audit-log', name: 'Missing Audit Logging', description: 'Detects services without audit logging enabled', framework: 'iso27001', controlId: 'A.8.16', severity: 'warning', pattern: '(audit|logging)\\s*[=:]\\s*(false|disabled|off)', checkType: 'pattern' },
  { id: 'insecure-tls', name: 'Insecure TLS Version', description: 'Detects usage of TLS versions below 1.2', framework: 'pci-dss', controlId: '4.1', severity: 'error', pattern: '(TLSv1|TLSv1\\.1|SSLv3|SSLv2)', checkType: 'pattern' },
];

const PATTERN_RULES: RulePattern[] = COMPLIANCE_RULES.filter((r) => r.checkType === 'pattern').map((r) => ({
  pattern: new RegExp(r.pattern, 'gi'),
  controlIds: [r.controlId],
  severity: r.severity,
  message: r.name,
  description: r.description,
}));

export class PRReviewEngine {
  private customRules: ComplianceRule[] = [];

  addCustomRule(rule: ComplianceRule): void {
    this.customRules.push(rule);
  }

  async reviewPR(pr: PRInfo): Promise<PRReview> {
    const findings: ComplianceFinding[] = [];

    for (const file of pr.files) {
      if (!file.patch) continue;
      const fileFindings = await this.reviewFile(file.path, file.patch);
      findings.push(...fileFindings);
    }

    const autoFixes = this.generateAutoFixes(findings);
    const summary = this.generateSummary(findings);

    return {
      pullRequest: pr,
      findings,
      summary,
      autoFixes,
      blocking: summary.errors > 0,
      checkedAt: new Date().toISOString(),
    };
  }

  async reviewFile(filePath: string, patch: string): Promise<ComplianceFinding[]> {
    const findings: ComplianceFinding[] = [];
    const lines = patch.split('\n');
    let currentLine = 0;

    for (const rule of PATTERN_RULES) {
      rule.pattern.lastIndex = 0;
      let match;
      while ((match = rule.pattern.exec(patch)) !== null) {
        const beforeMatch = patch.substring(0, match.index);
        currentLine = beforeMatch.split('\n').length;
        const column = match.index - beforeMatch.lastIndexOf('\n') - 1;

        findings.push({
          id: createHash('sha256').update(filePath + rule.message + currentLine).digest('hex').slice(0, 16),
          severity: rule.severity,
          controlId: rule.controlIds[0],
          framework: 'auto-detected',
          file: filePath,
          line: currentLine,
          column,
          message: rule.message,
          description: rule.description,
          confidence: 0.85,
          rule: COMPLIANCE_RULES.find((r) => r.name === rule.message) ?? {
            id: 'custom',
            name: rule.message,
            description: rule.description,
            framework: 'unknown',
            controlId: rule.controlIds[0],
            severity: rule.severity,
            checkType: 'pattern',
          },
        });
      }
    }

    for (const customRule of this.customRules) {
      if (customRule.pattern) {
        const regex = new RegExp(customRule.pattern, 'gi');
        let match;
        while ((match = regex.exec(patch)) !== null) {
          const beforeMatch = patch.substring(0, match.index);
          currentLine = beforeMatch.split('\n').length;

          findings.push({
            id: createHash('sha256').update(filePath + customRule.name + currentLine).digest('hex').slice(0, 16),
            severity: customRule.severity,
            controlId: customRule.controlId,
            framework: customRule.framework,
            file: filePath,
            line: currentLine,
            column: 0,
            message: customRule.name,
            description: customRule.description,
            confidence: 0.75,
            rule: customRule,
          });
        }
      }
    }

    return findings;
  }

  private generateAutoFixes(findings: ComplianceFinding[]): AutoFix[] {
    const fixes: AutoFix[] = [];

    for (const finding of findings) {
      if (finding.severity === 'error') {
        if (finding.rule.id === 'hardcoded-secret') {
          fixes.push({
            title: 'Replace hardcoded secret with environment variable',
            description: 'Move the hardcoded secret to an environment variable',
            changes: [{
              file: finding.file,
              startLine: finding.line,
              endLine: finding.line,
              oldContent: '// hardcoded secret detected',
              newContent: 'process.env.SECRET_KEY',
            }],
            riskLevel: 'medium',
            requiresApproval: true,
          });
        }

        if (finding.rule.id === 'weak-encryption') {
          fixes.push({
            title: 'Replace weak encryption with AES-256',
            description: 'Upgrade from deprecated encryption to AES-256-GCM',
            changes: [{
              file: finding.file,
              startLine: finding.line,
              endLine: finding.line,
              oldContent: '// weak encryption',
              newContent: "require('crypto').createCipheriv('aes-256-gcm', key, iv)",
            }],
            riskLevel: 'high',
            requiresApproval: true,
          });
        }

        if (finding.rule.id === 'cors-wildcard') {
          fixes.push({
            title: 'Replace CORS wildcard with specific origins',
            description: 'Restrict CORS to specific allowed origins',
            changes: [{
              file: finding.file,
              startLine: finding.line,
              endLine: finding.line,
              oldContent: "Access-Control-Allow-Origin: *",
              newContent: "Access-Control-Allow-Origin: https://yourdomain.com",
            }],
            riskLevel: 'low',
            requiresApproval: false,
          });
        }
      }
    }

    return fixes;
  }

  private generateSummary(findings: ComplianceFinding[]): PRReviewSummary {
    const errors = findings.filter((f) => f.severity === 'error').length;
    const warnings = findings.filter((f) => f.severity === 'warning').length;
    const infos = findings.filter((f) => f.severity === 'info').length;
    const controlsAffected = [...new Set(findings.map((f) => f.controlId))];
    const complianceScore = findings.length === 0 ? 100 : Math.max(0, 100 - errors * 20 - warnings * 5 - infos * 1);

    let recommendation: PRReviewSummary['recommendation'] = 'approve';
    if (errors > 0) recommendation = 'request_changes';
    else if (warnings > 3) recommendation = 'comment';

    return {
      totalFindings: findings.length,
      errors,
      warnings,
      infos,
      controlsAffected,
      complianceScore,
      recommendation,
    };
  }
}
