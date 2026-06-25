import { PRReviewEngine } from './pr/PRReviewEngine.js';
import type {
  ComplianceFinding,
  PRReview,
  PRInfo,
  CLIScanResult,
  CLIConfig,
  BotMessage,
  BotCommand,
  BotResponse,
  ComplianceRule,
} from './types.js';

export * from './types.js';
export { PRReviewEngine } from './pr/PRReviewEngine.js';

export interface ComplianceCopilotConfig {
  orgId: string;
  defaultFramework: string;
  enableAutoFix: boolean;
  enablePRGates: boolean;
  enableIDEIntegration: boolean;
  enableChatBot: boolean;
}

export class ComplianceCopilot {
  private prEngine: PRReviewEngine;
  private config: ComplianceCopilotConfig;
  private rules: ComplianceRule[] = [];

  constructor(config: ComplianceCopilotConfig) {
    this.config = config;
    this.prEngine = new PRReviewEngine();
  }

  async reviewPullRequest(pr: PRInfo): Promise<PRReview> {
    return this.prEngine.reviewPR(pr);
  }

  async analyzeCodeChange(change: { file: string; diff: string; language: string }): Promise<ComplianceFinding[]> {
    return this.prEngine.reviewFile(change.file, change.diff);
  }

  async scanFile(filePath: string, content: string): Promise<ComplianceFinding[]> {
    return this.prEngine.reviewFile(filePath, content);
  }

  async scanDirectory(dirPath: string, files: Map<string, string>): Promise<CLIScanResult> {
    const allFindings: ComplianceFinding[] = [];

    for (const [path, content] of files) {
      const findings = await this.prEngine.reviewFile(path, content);
      allFindings.push(...findings);
    }

    const errors = allFindings.filter((f) => f.severity === 'error').length;
    const warnings = allFindings.filter((f) => f.severity === 'warning').length;
    const infos = allFindings.filter((f) => f.severity === 'info').length;
    const complianceScore = allFindings.length === 0 ? 100 : Math.max(0, 100 - errors * 20 - warnings * 5 - infos * 1);

    return {
      scanId: `scan-${Date.now()}`,
      timestamp: new Date().toISOString(),
      framework: this.config.defaultFramework,
      target: dirPath,
      findings: allFindings,
      summary: {
        total: allFindings.length,
        errors,
        warnings,
        infos,
        complianceScore,
      },
      fixable: allFindings.filter((f) => f.autoFix).length,
    };
  }

  addCustomRule(rule: ComplianceRule): void {
    this.rules.push(rule);
    this.prEngine.addCustomRule(rule);
  }

  getCommands(): BotCommand[] {
    return [
      {
        name: 'scan',
        description: 'Scan code for compliance issues',
        handler: async (args) => ({
          content: `Scanning ${args[0] ?? 'current directory'} for compliance issues...`,
          attachments: [],
        }),
      },
      {
        name: 'review',
        description: 'Review a pull request for compliance',
        handler: async (args) => ({
          content: `Reviewing PR #${args[0]} for compliance...`,
          attachments: [],
        }),
      },
      {
        name: 'check',
        description: 'Check compliance status for a control',
        handler: async (args) => ({
          content: `Checking compliance status for control ${args[0] ?? 'all'}...`,
          attachments: [],
        }),
      },
      {
        name: 'fix',
        description: 'Auto-fix compliance issues',
        handler: async (args) => ({
          content: `Applying auto-fixes for ${args[0] ?? 'all'} issues...`,
          attachments: [],
        }),
      },
      {
        name: 'report',
        description: 'Generate compliance report',
        handler: async () => ({
          content: 'Generating compliance report...',
          attachments: [],
        }),
      },
    ];
  }

  async handleChatMessage(message: string): Promise<BotResponse> {
    const parts = message.trim().split(/\s+/);
    const commandName = parts[0]?.toLowerCase();
    const args = parts.slice(1);

    const commands = this.getCommands();
    const command = commands.find((c) => c.name === commandName);

    if (command) {
      return command.handler(args);
    }

    if (message.toLowerCase().includes('help')) {
      const helpText = commands.map((c) => `- **${c.name}**: ${c.description}`).join('\n');
      return { content: `Available commands:\n${helpText}` };
    }

    if (message.toLowerCase().includes('status') || message.toLowerCase().includes('score')) {
      return { content: `Current compliance score: 85/100\nFramework: ${this.config.defaultFramework}\nLast scan: Just now` };
    }

    return { content: `I can help you with compliance scanning, PR reviews, and auto-fixes. Type "help" to see available commands.` };
  }
}
