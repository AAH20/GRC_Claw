import type { ToolDefinition } from '@grc-claw/agent-runtime';
import { llmGatedToolName } from './names.js';
import type { ConnectorRegistry } from './registry.js';
import type { McpToolDescriptor } from './types.js';

/** Merge built-in GRC tools with BYOC LLM + discovered MCP tools */
export function buildConnectorToolDefinitions(
  registry: ConnectorRegistry,
  mcpToolsByServer: Record<string, McpToolDescriptor[]> = {}
): ToolDefinition[] {
  const tools: ToolDefinition[] = [];

  for (const llm of registry.listLlm()) {
    tools.push({
      name: llmGatedToolName(llm.id),
      tier: 'read',
    });
  }

  for (const server of registry.listMcp()) {
    const listed = mcpToolsByServer[server.id] ?? [];
    const destructive = new Set(server.destructiveTools ?? []);
    const defaultTier = server.defaultTier ?? 'read';

    if (listed.length === 0) {
      tools.push({
        name: `mcp.${server.id}._discovery`,
        tier: 'read',
      });
      continue;
    }

    for (const t of listed) {
      const tier = destructive.has(t.name) ? 'destructive' : defaultTier === 'write' ? 'write' : defaultTier;
      tools.push({ name: t.gatedName, tier });
    }
  }

  return tools;
}
