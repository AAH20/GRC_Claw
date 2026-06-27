export type AgentRiskLevel = 'critical' | 'high' | 'medium' | 'low' | 'none';

export type AgentDiscoverySource =
  | 'mcp_server'
  | 'cursor_config'
  | 'agent_config'
  | 'api_log'
  | 'codebase_scan'
  | 'package_dependency'
  | 'env_variable';

export interface DiscoveredAgent {
  id: string;
  name: string;
  source: AgentDiscoverySource;
  detectedAt: string;
  riskLevel: AgentRiskLevel;
  riskScore: number;
  details: Record<string, unknown>;
  indicators: string[];
}

export interface McpServerConnection {
  serverName: string;
  endpoint: string;
  transport: 'stdio' | 'sse' | 'streamable-http';
  connected: boolean;
  toolsExposed: string[];
  riskLevel: AgentRiskLevel;
  riskScore: number;
}

export interface CursorSkillEntry {
  path: string;
  name: string;
  description: string;
  hasBody: boolean;
  riskLevel: AgentRiskLevel;
}

export interface AgentConfigEntry {
  path: string;
  type: 'skill' | 'agent' | 'mcp_config' | 'policy';
  name: string;
  hasPermissions: boolean;
  hasToolAccess: boolean;
  riskLevel: AgentRiskLevel;
}

export interface ApiLogEntry {
  timestamp: string;
  endpoint: string;
  tool: string;
  agentId: string;
  sessionId: string;
  allowed: boolean;
  riskLevel: AgentRiskLevel;
}

export interface AgentInventoryReport {
  generatedAt: string;
  scanDurationMs: number;
  totalAgentsFound: number;
  overallRiskScore: number;
  overallRiskLevel: AgentRiskLevel;
  agents: DiscoveredAgent[];
  mcpServers: McpServerConnection[];
  cursorSkills: CursorSkillEntry[];
  agentConfigs: AgentConfigEntry[];
  apiLogEntries: ApiLogEntry[];
  riskBreakdown: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    none: number;
  };
  recommendations: string[];
}

export interface AgentDiscoveryConfig {
  scanPaths: string[];
  mcpConfigPaths: string[];
  cursorConfigPaths: string[];
  apiLogPath?: string;
  riskThresholds: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  excludePatterns: string[];
  tenantId?: number;
}

export interface DiscoveryScanResult {
  scanId: string;
  timestamp: string;
  config: AgentDiscoveryConfig;
  report: AgentInventoryReport;
}

export interface DiscoveryInventoryResult {
  agents: DiscoveredAgent[];
  totalCount: number;
  bySource: Record<AgentDiscoverySource, number>;
  byRiskLevel: Record<AgentRiskLevel, number>;
}

export interface RiskScoreResult {
  agentId: string;
  riskScore: number;
  riskLevel: AgentRiskLevel;
  factors: Array<{ factor: string; weight: number; score: number; description: string }>;
  computedAt: string;
}
