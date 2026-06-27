import { randomUUID, createHash } from 'node:crypto';
import * as fs from 'node:fs';
import * as path from 'node:path';
import type {
  AgentDiscoveryConfig,
  AgentDiscoverySource,
  AgentInventoryReport,
  AgentRiskLevel,
  ApiLogEntry,
  CursorSkillEntry,
  AgentConfigEntry,
  DiscoveredAgent,
  DiscoveryInventoryResult,
  DiscoveryScanResult,
  McpServerConnection,
  RiskScoreResult,
} from './types.js';

const DEFAULT_CONFIG: AgentDiscoveryConfig = {
  scanPaths: ['.cursor/skills', '.cursor', '.grc_memory', 'packages'],
  mcpConfigPaths: ['.cursor/mcp.json', 'mcp.json', '.mcp/servers.json'],
  cursorConfigPaths: ['.cursor/settings.json', '.cursor/rules'],
  riskThresholds: { critical: 90, high: 70, medium: 40, low: 20 },
  excludePatterns: ['node_modules', 'dist', '.git', '*.test.ts', '*.spec.ts'],
};

function classifyRisk(score: number, thresholds: AgentDiscoveryConfig['riskThresholds']): AgentRiskLevel {
  if (score >= thresholds.critical) return 'critical';
  if (score >= thresholds.high) return 'high';
  if (score >= thresholds.medium) return 'medium';
  if (score >= thresholds.low) return 'low';
  return 'none';
}

function fileExists(p: string): boolean {
  try { return fs.statSync(p).isFile(); } catch { return false; }
}

function readJsonSafe(p: string): Record<string, unknown> | null {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8')) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function listDirSafe(p: string): string[] {
  try { return fs.readdirSync(p); } catch { return []; }
}

function isExcluded(filePath: string, patterns: string[]): boolean {
  return patterns.some((pattern) => {
    if (pattern.startsWith('*')) {
      return filePath.endsWith(pattern.slice(1));
    }
    return filePath.includes(pattern);
  });
}

export class AgentDiscoveryScanner {
  private config: AgentDiscoveryConfig;
  private discoveredAgents: DiscoveredAgent[] = [];
  private mcpServers: McpServerConnection[] = [];
  private cursorSkills: CursorSkillEntry[] = [];
  private agentConfigs: AgentConfigEntry[] = [];
  private apiLogEntries: ApiLogEntry[] = [];

  constructor(config?: Partial<AgentDiscoveryConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  async scan(rootPath?: string): Promise<DiscoveryScanResult> {
    const start = Date.now();
    const scanId = randomUUID();
    const base = rootPath ?? process.cwd();

    this.discoveredAgents = [];
    this.mcpServers = [];
    this.cursorSkills = [];
    this.agentConfigs = [];
    this.apiLogEntries = [];

    this.scanMcpServers(base);
    this.scanCursorSkills(base);
    this.scanAgentConfigs(base);
    this.scanCodebase(base);
    this.scanApiLogs(base);

    const report = this.buildReport(start);

    return { scanId, timestamp: new Date().toISOString(), config: this.config, report };
  }

  inventory(): DiscoveryInventoryResult {
    const bySource: Record<AgentDiscoverySource, number> = {
      mcp_server: 0, cursor_config: 0, agent_config: 0,
      api_log: 0, codebase_scan: 0, package_dependency: 0, env_variable: 0,
    };
    const byRiskLevel: Record<AgentRiskLevel, number> = {
      critical: 0, high: 0, medium: 0, low: 0, none: 0,
    };

    for (const agent of this.discoveredAgents) {
      bySource[agent.source]++;
      byRiskLevel[agent.riskLevel]++;
    }

    return {
      agents: [...this.discoveredAgents],
      totalCount: this.discoveredAgents.length,
      bySource,
      byRiskLevel,
    };
  }

  riskScore(agentId: string): RiskScoreResult | null {
    const agent = this.discoveredAgents.find((a) => a.id === agentId);
    if (!agent) return null;

    const factors: RiskScoreResult['factors'] = [];

    const sourceWeights: Record<AgentDiscoverySource, number> = {
      mcp_server: 30, cursor_config: 15, agent_config: 20,
      api_log: 25, codebase_scan: 10, package_dependency: 15, env_variable: 20,
    };
    const sourceWeight = sourceWeights[agent.source];
    const sourceScore = agent.riskScore * (sourceWeight / 100);
    factors.push({
      factor: 'discovery_source',
      weight: sourceWeight,
      score: sourceScore,
      description: `Agent discovered via ${agent.source}`,
    });

    const indicatorCount = agent.indicators.length;
    const indicatorScore = Math.min(indicatorCount * 10, 30);
    factors.push({
      factor: 'risk_indicators',
      weight: 30,
      score: indicatorScore,
      description: `${indicatorCount} risk indicator(s) found`,
    });

    const totalScore = Math.round(factors.reduce((sum, f) => sum + f.score, 0));

    return {
      agentId,
      riskScore: totalScore,
      riskLevel: classifyRisk(totalScore, this.config.riskThresholds),
      factors,
      computedAt: new Date().toISOString(),
    };
  }

  private scanMcpServers(basePath: string): void {
    for (const configPath of this.config.mcpConfigPaths) {
      const fullPath = path.join(basePath, configPath);
      const data = readJsonSafe(fullPath);
      if (!data) continue;

      const mcpServers = (data['mcpServers'] ?? data['servers'] ?? data) as Record<string, Record<string, unknown>> | Array<Record<string, unknown>>;

      if (Array.isArray(mcpServers)) {
        for (const server of mcpServers) {
          this.processMcpServer(server, configPath);
        }
      } else if (typeof mcpServers === 'object') {
        for (const [name, server] of Object.entries(mcpServers)) {
          if (typeof server === 'object' && server !== null) {
            this.processMcpServer({ ...server, name }, configPath);
          }
        }
      }
    }
  }

  private processMcpServer(server: Record<string, unknown>, configPath: string): void {
    const name = String(server['name'] ?? server['serverName'] ?? 'unknown');
    const command = String(server['command'] ?? '');
    const args = Array.isArray(server['args']) ? server['args'].map(String) : [];
    const endpoint = command ? `${command} ${args.join(' ')}` : String(server['endpoint'] ?? server['url'] ?? 'unknown');
    const transport = (String(server['transport'] ?? 'stdio') as McpServerConnection['transport']);

    const riskIndicators: string[] = [];
    let riskScore = 10;

    if (command.includes('npx') || command.includes('pip')) {
      riskIndicators.push('Uses package runner (auto-installs dependencies)');
      riskScore += 15;
    }
    if (endpoint.includes('http') && !endpoint.includes('localhost') && !endpoint.includes('127.0.0.1')) {
      riskIndicators.push('Remote MCP server endpoint detected');
      riskScore += 20;
    }
    const toolsExposed = Array.isArray(server['tools']) ? server['tools'].map(String) : [];
    if (toolsExposed.length > 5) {
      riskIndicators.push(`High tool count: ${toolsExposed.length} tools exposed`);
      riskScore += 10;
    }
    if (toolsExposed.some((t) => t.includes('write') || t.includes('execute') || t.includes('run') || t.includes('delete'))) {
      riskIndicators.push('Destructive or write tools exposed');
      riskScore += 20;
    }

    const riskLevel = classifyRisk(riskScore, this.config.riskThresholds);

    const connection: McpServerConnection = {
      serverName: name,
      endpoint,
      transport,
      connected: false,
      toolsExposed,
      riskLevel,
      riskScore,
    };
    this.mcpServers.push(connection);

    this.discoveredAgents.push({
      id: randomUUID(),
      name: `mcp:${name}`,
      source: 'mcp_server',
      detectedAt: new Date().toISOString(),
      riskLevel,
      riskScore,
      details: { configPath, command, args, transport, toolsExposed },
      indicators: riskIndicators,
    });
  }

  private scanCursorSkills(basePath: string): void {
    for (const scanPath of this.config.scanPaths) {
      if (!scanPath.includes('cursor')) continue;
      const fullPath = path.join(basePath, scanPath);
      const entries = listDirSafe(fullPath);

      for (const entry of entries) {
        if (isExcluded(entry, this.config.excludePatterns)) continue;
        const entryPath = path.join(fullPath, entry);
        const stat = fs.statSync(entryPath);

        if (stat.isFile() && entry.endsWith('.md')) {
          const content = fs.readFileSync(entryPath, 'utf8');
          const nameMatch = content.match(/^#\s+(.+)/m);
          const descMatch = content.match(/^>\s*(.+)/m);

          let riskScore = 5;
          const indicators: string[] = [];

          if (content.includes('tool') || content.includes('execute') || content.includes('run')) {
            riskScore += 10;
            indicators.push('Skill references tool execution');
          }

          const riskLevel = classifyRisk(riskScore, this.config.riskThresholds);

          this.cursorSkills.push({
            path: entryPath,
            name: nameMatch?.[1] ?? entry.replace('.md', ''),
            description: descMatch?.[1] ?? '',
            hasBody: content.length > 100,
            riskLevel,
          });

          this.discoveredAgents.push({
            id: randomUUID(),
            name: `cursor_skill:${entry}`,
            source: 'cursor_config',
            detectedAt: new Date().toISOString(),
            riskLevel,
            riskScore,
            details: { path: entryPath, name: nameMatch?.[1], description: descMatch?.[1] },
            indicators,
          });
        }

        if (stat.isDirectory()) {
          const subEntries = listDirSafe(entryPath);
          for (const subEntry of subEntries) {
            if (subEntry.endsWith('.md') || subEntry.endsWith('.json') || subEntry.endsWith('.yaml') || subEntry.endsWith('.yml')) {
              const subPath = path.join(entryPath, subEntry);
              let riskScore = 5;
              const indicators: string[] = [];

              if (subEntry.endsWith('.json')) {
                const data = readJsonSafe(subPath);
                if (data && (data['tools'] || data['permissions'] || data['execute'])) {
                  riskScore += 15;
                  indicators.push('Agent config defines tools or permissions');
                }
              }

              const riskLevel = classifyRisk(riskScore, this.config.riskThresholds);

              this.discoveredAgents.push({
                id: randomUUID(),
                name: `cursor_skill_dir:${entry}/${subEntry}`,
                source: 'cursor_config',
                detectedAt: new Date().toISOString(),
                riskLevel,
                riskScore,
                details: { path: subPath, parentDir: entry },
                indicators,
              });
            }
          }
        }
      }
    }
  }

  private scanAgentConfigs(basePath: string): void {
    const configPatterns = [
      'agent.json', 'agent.yaml', 'agent.yml',
      'agents.json', 'agents.yaml', 'agents.yml',
      '.agent', 'mcp.json', 'mcp.yaml',
    ];

    const self = this;
    function walk(dir: string, depth: number): void {
      if (depth > 5) return;
      const entries = listDirSafe(dir);
      for (const entry of entries) {
        if (isExcluded(entry, DEFAULT_CONFIG.excludePatterns)) continue;
        const fullPath = path.join(dir, entry);
        try {
          const stat = fs.statSync(fullPath);
          if (stat.isDirectory()) {
            walk(fullPath, depth + 1);
          } else if (configPatterns.includes(entry)) {
            const data = readJsonSafe(fullPath);
            if (!data) continue;

            let riskScore = 10;
            const indicators: string[] = [];

            if (data['tools'] || data['allowedTools'] || data['execute']) {
              riskScore += 15;
              indicators.push('Agent config defines tool access');
            }
            if (data['permissions'] || data['scopes']) {
              riskScore += 10;
              indicators.push('Agent config defines permissions/scopes');
            }
            if (data['autoApprove'] || data['autoExecute']) {
              riskScore += 20;
              indicators.push('Agent config has auto-approve/auto-execute enabled');
            }

            const riskLevel = classifyRisk(riskScore, self.config.riskThresholds);

            self.agentConfigs.push({
              path: fullPath,
              type: entry.startsWith('mcp') ? 'mcp_config' : 'agent',
              name: String(data['name'] ?? entry),
              hasPermissions: Boolean(data['permissions'] || data['scopes']),
              hasToolAccess: Boolean(data['tools'] || data['allowedTools'] || data['execute']),
              riskLevel,
            });

            self.discoveredAgents.push({
              id: randomUUID(),
              name: `config:${String(data['name'] ?? entry)}`,
              source: 'agent_config',
              detectedAt: new Date().toISOString(),
              riskLevel,
              riskScore,
              details: { path: fullPath, configKeys: Object.keys(data) },
              indicators,
            });
          }
        } catch {
          continue;
        }
      }
    }

    for (const scanPath of this.config.scanPaths) {
      const fullPath = path.join(basePath, scanPath);
      if (fs.existsSync(fullPath)) {
        walk(fullPath, 0);
      }
    }
  }

  private scanCodebase(basePath: string): void {
    const indicators: string[] = [];
    let riskScore = 5;

    const envVars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'HF_TOKEN', 'COHERE_API_KEY'];
    const envPath = path.join(basePath, '.env');
    const foundEnvVars: string[] = [];
    if (fileExists(envPath)) {
      const content = fs.readFileSync(envPath, 'utf8');
      for (const envVar of envVars) {
        if (content.includes(envVar)) {
          indicators.push(`Environment variable ${envVar} found in .env`);
          foundEnvVars.push(envVar);
          riskScore += 5;
        }
      }
    }

    if (indicators.length > 0) {
      const riskLevel = classifyRisk(riskScore, this.config.riskThresholds);
      this.discoveredAgents.push({
        id: randomUUID(),
        name: 'codebase:ai_dependencies',
        source: 'codebase_scan',
        detectedAt: new Date().toISOString(),
        riskLevel,
        riskScore,
        details: { envVars: foundEnvVars },
        indicators,
      });
    }
  }

  private scanApiLogs(basePath: string): void {
    const logPath = this.config.apiLogPath ?? path.join(basePath, '.grc_memory', 'action-ledger.ndjson');
    if (!fileExists(logPath)) return;

    try {
      const content = fs.readFileSync(logPath, 'utf8');
      const lines = content.split('\n').filter(Boolean).slice(-200);

      for (const line of lines) {
        try {
          const entry = JSON.parse(line) as Record<string, unknown>;
          const tool = String(entry['tool'] ?? '');
          const agentId = String(entry['agentId'] ?? entry['agentDid'] ?? 'system');
          const allowed = entry['allowed'] !== false;

          let riskLevel: AgentRiskLevel = 'none';
          const riskIndicators: string[] = [];

          if (tool.includes('delete') || tool.includes('destroy') || tool.includes('revoke')) {
            riskLevel = 'high';
            riskIndicators.push('Destructive tool invoked');
          } else if (tool.includes('write') || tool.includes('update') || tool.includes('create')) {
            riskLevel = 'medium';
            riskIndicators.push('Write tool invoked');
          }

          this.apiLogEntries.push({
            timestamp: String(entry['timestamp'] ?? entry['createdAt'] ?? ''),
            endpoint: String(entry['endpoint'] ?? ''),
            tool,
            agentId,
            sessionId: String(entry['sessionId'] ?? ''),
            allowed,
            riskLevel,
          });

          if (riskLevel !== 'none' && !this.discoveredAgents.some((a) => a.name === `log_agent:${agentId}`)) {
            this.discoveredAgents.push({
              id: randomUUID(),
              name: `log_agent:${agentId}`,
              source: 'api_log',
              detectedAt: new Date().toISOString(),
              riskLevel,
              riskScore: riskLevel === 'high' ? 75 : riskLevel === 'medium' ? 50 : 25,
              details: { agentId, recentTools: [tool] },
              indicators: riskIndicators,
            });
          }
        } catch {
          continue;
        }
      }
    } catch {
      return;
    }
  }

  private buildReport(startMs: number): AgentInventoryReport {
    const riskBreakdown: AgentInventoryReport['riskBreakdown'] = { critical: 0, high: 0, medium: 0, low: 0, none: 0 };
    for (const agent of this.discoveredAgents) {
      riskBreakdown[agent.riskLevel]++;
    }

    const overallRiskScore = this.discoveredAgents.length > 0
      ? Math.round(this.discoveredAgents.reduce((sum, a) => sum + a.riskScore, 0) / this.discoveredAgents.length)
      : 0;

    const recommendations: string[] = [];
    if (riskBreakdown.critical > 0) {
      recommendations.push(`URGENT: ${riskBreakdown.critical} critical-risk agent(s) detected. Review and remediate immediately.`);
    }
    if (this.mcpServers.length > 3) {
      recommendations.push('High MCP server count detected. Consider consolidating or removing unused servers.');
    }
    const autoApproveAgents = this.discoveredAgents.filter((a) => a.indicators.some((i) => i.includes('auto-approve')));
    if (autoApproveAgents.length > 0) {
      recommendations.push(`${autoApproveAgents.length} agent(s) have auto-approve enabled. Disable for production environments.`);
    }
    if (this.discoveredAgents.filter((a) => a.source === 'api_log' && a.riskLevel !== 'none').length > 5) {
      recommendations.push('Multiple risky tool invocations detected in logs. Review API audit trail.');
    }
    if (recommendations.length === 0) {
      recommendations.push('No significant risks detected. Continue regular scanning schedule.');
    }

    return {
      generatedAt: new Date().toISOString(),
      scanDurationMs: Date.now() - startMs,
      totalAgentsFound: this.discoveredAgents.length,
      overallRiskScore,
      overallRiskLevel: classifyRisk(overallRiskScore, this.config.riskThresholds),
      agents: [...this.discoveredAgents],
      mcpServers: [...this.mcpServers],
      cursorSkills: [...this.cursorSkills],
      agentConfigs: [...this.agentConfigs],
      apiLogEntries: this.apiLogEntries.slice(-100),
      riskBreakdown,
      recommendations,
    };
  }
}
