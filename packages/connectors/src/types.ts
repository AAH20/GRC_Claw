import type { ToolTier } from '@grc-claw/agent-runtime';

export type LlmProviderKind = 'openai_compatible' | 'anthropic_messages';

export interface LlmProviderConfig {
  id: string;
  label: string;
  kind: LlmProviderKind;
  baseUrl: string;
  /** Environment variable holding the API key — never store secrets in config files */
  apiKeyEnv: string;
  defaultModel?: string;
  enabled?: boolean;
}

export type McpTransport = 'http';

export interface McpServerConfig {
  id: string;
  label: string;
  transport: McpTransport;
  url: string;
  apiKeyEnv?: string;
  headers?: Record<string, string>;
  enabled?: boolean;
  /** Default tier for tools discovered from this server */
  defaultTier?: ToolTier;
  /** MCP tool names that require approval (destructive) */
  destructiveTools?: string[];
}

export interface ConnectorsFile {
  version: 1;
  llm?: LlmProviderConfig[];
  mcp?: McpServerConfig[];
}

export interface LlmProviderPublic {
  id: string;
  label: string;
  kind: LlmProviderKind;
  baseUrl: string;
  defaultModel?: string;
  enabled: boolean;
  apiKeyConfigured: boolean;
}

export interface McpServerPublic {
  id: string;
  label: string;
  transport: McpTransport;
  url: string;
  enabled: boolean;
  apiKeyConfigured: boolean;
  defaultTier: ToolTier;
  destructiveTools: string[];
  toolCount?: number;
}

export interface McpToolDescriptor {
  name: string;
  description?: string;
  gatedName: string;
}
