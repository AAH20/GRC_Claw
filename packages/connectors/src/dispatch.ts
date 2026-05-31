import type { ConnectorRegistry } from './registry.js';
import { chatViaProvider, type LlmChatRequest } from './llm.js';
import { callMcpTool } from './mcp.js';
import { parseLlmGatedToolName, parseMcpGatedToolName } from './names.js';

export interface ConnectorDispatchResult {
  kind: 'llm' | 'mcp' | 'none';
  output?: Record<string, unknown>;
}

export async function dispatchConnectorTool(
  registry: ConnectorRegistry,
  tool: string,
  args: Record<string, unknown>
): Promise<ConnectorDispatchResult> {
  const mcp = parseMcpGatedToolName(tool);
  if (mcp) {
    const result = await callMcpTool(registry, mcp.serverId, mcp.toolName, args);
    return { kind: 'mcp', output: result };
  }

  const llmId = parseLlmGatedToolName(tool);
  if (llmId) {
    const messages = (args.messages as LlmChatRequest['messages']) ?? [
      { role: 'user', content: String(args.prompt ?? args.message ?? '') },
    ];
    const result = await chatViaProvider(registry, llmId, {
      messages,
      model: typeof args.model === 'string' ? args.model : undefined,
      maxTokens: typeof args.maxTokens === 'number' ? args.maxTokens : undefined,
    });
    return {
      kind: 'llm',
      output: { content: result.content, model: result.model, providerId: result.providerId },
    };
  }

  return { kind: 'none' };
}

export function isConnectorTool(tool: string): boolean {
  return tool.startsWith('mcp.') || tool.startsWith('llm.');
}
