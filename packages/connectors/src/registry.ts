import { readFileSync, existsSync } from 'node:fs';
import type {
  ConnectorsFile,
  LlmProviderConfig,
  LlmProviderPublic,
  McpServerConfig,
  McpServerPublic,
} from './types.js';

export class ConnectorRegistry {
  private llm: Map<string, LlmProviderConfig> = new Map();
  private mcp: Map<string, McpServerConfig> = new Map();
  private sourcePath: string | null = null;

  loadFromFile(path: string): void {
    if (!existsSync(path)) {
      throw new Error(`connectors config not found: ${path}`);
    }
    const raw = JSON.parse(readFileSync(path, 'utf8')) as ConnectorsFile;
    this.applyConfig(raw, path);
  }

  loadFromEnv(): void {
    const inline = process.env.GRC_CLAW_CONNECTORS_JSON?.trim();
    if (inline) {
      this.applyConfig(JSON.parse(inline) as ConnectorsFile, 'env:GRC_CLAW_CONNECTORS_JSON');
      return;
    }
    const path = process.env.GRC_CLAW_CONNECTORS_CONFIG?.trim();
    if (path) {
      this.loadFromFile(path);
      return;
    }
    this.applyConfig({ version: 1, llm: [], mcp: [] }, 'default');
  }

  applyConfig(file: ConnectorsFile, source: string): void {
    if (file.version !== 1) throw new Error('connectors config version must be 1');
    this.sourcePath = source;
    this.llm.clear();
    this.mcp.clear();
    for (const p of file.llm ?? []) {
      if (p.enabled === false) continue;
      this.llm.set(p.id, { ...p, enabled: true });
    }
    for (const s of file.mcp ?? []) {
      if (s.enabled === false) continue;
      this.mcp.set(s.id, { ...s, enabled: true, transport: 'http' });
    }
  }

  getLlm(id: string): LlmProviderConfig | undefined {
    return this.llm.get(id);
  }

  getMcp(id: string): McpServerConfig | undefined {
    return this.mcp.get(id);
  }

  listLlm(): LlmProviderConfig[] {
    return [...this.llm.values()];
  }

  listMcp(): McpServerConfig[] {
    return [...this.mcp.values()];
  }

  resolveApiKey(envName: string): string | undefined {
    const v = process.env[envName]?.trim();
    return v || undefined;
  }

  toPublicSummary(toolCounts: Record<string, number> = {}): {
    source: string | null;
    llm: LlmProviderPublic[];
    mcp: McpServerPublic[];
  } {
    return {
      source: this.sourcePath,
      llm: this.listLlm().map((p) => ({
        id: p.id,
        label: p.label,
        kind: p.kind,
        baseUrl: p.baseUrl,
        defaultModel: p.defaultModel,
        enabled: true,
        apiKeyConfigured: Boolean(this.resolveApiKey(p.apiKeyEnv)),
      })),
      mcp: this.listMcp().map((s) => ({
        id: s.id,
        label: s.label,
        transport: s.transport,
        url: s.url,
        enabled: true,
        apiKeyConfigured: s.apiKeyEnv ? Boolean(this.resolveApiKey(s.apiKeyEnv)) : true,
        defaultTier: s.defaultTier ?? 'read',
        destructiveTools: s.destructiveTools ?? [],
        toolCount: toolCounts[s.id],
      })),
    };
  }
}

let defaultRegistry: ConnectorRegistry | null = null;

export function getConnectorRegistry(): ConnectorRegistry {
  if (!defaultRegistry) {
    defaultRegistry = new ConnectorRegistry();
    defaultRegistry.loadFromEnv();
  }
  return defaultRegistry;
}

export function resetConnectorRegistryForTests(): void {
  defaultRegistry = null;
}
