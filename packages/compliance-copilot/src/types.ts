export type Severity = 'error' | 'warning' | 'info';

export interface ComplianceFinding {
  id: string;
  severity: Severity;
  controlId: string;
  framework: string;
  file: string;
  line: number;
  column: number;
  message: string;
  description: string;
  autoFix?: AutoFix;
  evidence?: FindingEvidence;
  confidence: number;
  rule: ComplianceRule;
}

export interface AutoFix {
  title: string;
  description: string;
  changes: FileChange[];
  riskLevel: 'low' | 'medium' | 'high';
  requiresApproval: boolean;
}

export interface FileChange {
  file: string;
  startLine: number;
  endLine: number;
  oldContent: string;
  newContent: string;
}

export interface FindingEvidence {
  type: 'config' | 'code' | 'log' | 'policy';
  source: string;
  hash: string;
  timestamp: string;
}

export interface ComplianceRule {
  id: string;
  name: string;
  description: string;
  framework: string;
  controlId: string;
  severity: Severity;
  pattern?: string;
  astPattern?: string;
  checkType: 'pattern' | 'ast' | 'semantic' | 'config' | 'external';
}

export interface PRReview {
  pullRequest: PRInfo;
  findings: ComplianceFinding[];
  summary: PRReviewSummary;
  autoFixes: AutoFix[];
  blocking: boolean;
  checkedAt: string;
}

export interface PRInfo {
  number: number;
  title: string;
  branch: string;
  base: string;
  author: string;
  files: PRFile[];
}

export interface PRFile {
  path: string;
  additions: number;
  deletions: number;
  patch?: string;
  status: 'added' | 'modified' | 'removed' | 'renamed';
}

export interface PRReviewSummary {
  totalFindings: number;
  errors: number;
  warnings: number;
  infos: number;
  controlsAffected: string[];
  complianceScore: number;
  recommendation: 'approve' | 'request_changes' | 'comment';
}

export interface CodeChange {
  file: string;
  diff: string;
  language: string;
}

export interface ComplianceAnalysis {
  findings: ComplianceFinding[];
  riskScore: number;
  affectedControls: string[];
  recommendations: string[];
  estimatedRemediationTime: string;
}

export interface CLIScanResult {
  scanId: string;
  timestamp: string;
  framework: string;
  target: string;
  findings: ComplianceFinding[];
  summary: {
    total: number;
    errors: number;
    warnings: number;
    infos: number;
    complianceScore: number;
  };
  fixable: number;
}

export interface CLIConfig {
  framework: string;
  severity: Severity[];
  autoFix: boolean;
  outputFormat: 'json' | 'text' | 'github-actions';
  excludePatterns: string[];
}

export interface BotMessage {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: string;
  attachments?: BotAttachment[];
}

export interface BotAttachment {
  type: 'finding' | 'report' | 'config' | 'evidence';
  title: string;
  content: unknown;
}

export interface BotCommand {
  name: string;
  description: string;
  handler: (args: string[]) => Promise<BotResponse>;
}

export interface BotResponse {
  content: string;
  attachments?: BotAttachment[];
}
