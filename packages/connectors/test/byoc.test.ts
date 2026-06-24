import assert from 'node:assert/strict';
import { describe, it, beforeEach } from 'node:test';
import { BUILTIN_AGENT_TOOLS } from '@grc-claw/agent-runtime';
import {
  ConnectorRegistry,
  buildConnectorToolDefinitions,
  isConnectorTool,
  llmGatedToolName,
  mcpGatedToolName,
  parseLlmGatedToolName,
  parseMcpGatedToolName,
  resetConnectorRegistryForTests,
} from '@grc-claw/connectors';

describe('BYOC connectors (@grc-claw/connectors)', () => {
  beforeEach(() => resetConnectorRegistryForTests());

  it('loads registry from inline JSON env shape', () => {
    const reg = new ConnectorRegistry();
    reg.applyConfig(
      {
        version: 1,
        llm: [
          {
            id: 'openai',
            label: 'OpenAI',
            kind: 'openai_compatible',
            baseUrl: 'https://api.openai.com',
            apiKeyEnv: 'OPENAI_API_KEY',
          },
        ],
        mcp: [
          {
            id: 'grc-docs',
            label: 'GRC docs MCP',
            transport: 'http',
            url: 'http://127.0.0.1:9999/mcp',
            destructiveTools: ['delete_all'],
          },
        ],
      },
      'test'
    );
    assert.equal(reg.listLlm().length, 1);
    assert.equal(reg.listMcp().length, 1);
    const pub = reg.toPublicSummary({ 'grc-docs': 3 });
    assert.equal(pub.mcp[0]!.toolCount, 3);
  });

  it('mcp and llm gated tool names round-trip', () => {
    const mcp = mcpGatedToolName('my-server', 'search_controls');
    assert.equal(mcp, 'mcp.my-server.search_controls');
    assert.deepEqual(parseMcpGatedToolName(mcp), {
      serverId: 'my-server',
      toolName: 'search_controls',
    });
    const llm = llmGatedToolName('anthropic');
    assert.equal(llm, 'llm.anthropic.complete');
    assert.equal(parseLlmGatedToolName(llm), 'anthropic');
  });

  it('buildConnectorToolDefinitions marks destructive MCP tools', () => {
    const reg = new ConnectorRegistry();
    reg.applyConfig(
      {
        version: 1,
        mcp: [
          {
            id: 'soc',
            label: 'SOC MCP',
            transport: 'http',
            url: 'http://localhost/mcp',
            destructiveTools: ['run_playbook'],
          },
        ],
      },
      'test'
    );
    const tools = buildConnectorToolDefinitions(reg, {
      soc: [
        { name: 'query', gatedName: mcpGatedToolName('soc', 'query') },
        { name: 'run_playbook', gatedName: mcpGatedToolName('soc', 'run_playbook') },
      ],
    });
    const playbook = tools.find((t) => t.name.endsWith('run_playbook'));
    assert.equal(playbook?.tier, 'destructive');
    const query = tools.find((t) => t.name.endsWith('query'));
    assert.equal(query?.tier, 'read');
  });

  it('requires approval for every credit-consuming marketing MCP tool', () => {
    const reg = new ConnectorRegistry();
    reg.applyConfig(
      {
        version: 1,
        mcp: [
          {
            id: 'higgsfield',
            label: 'Higgsfield MCP',
            transport: 'http',
            url: 'https://mcp.higgsfield.ai/mcp',
            authMode: 'oauth',
            requiresApproval: true,
          },
        ],
      },
      'test'
    );
    const tools = buildConnectorToolDefinitions(reg, {
      higgsfield: [{ name: 'generate_image', gatedName: mcpGatedToolName('higgsfield', 'generate_image') }],
    });
    assert.equal(tools[0]?.tier, 'destructive');
    assert.equal(reg.toPublicSummary().mcp[0]?.authMode, 'oauth');
    assert.equal(reg.toPublicSummary().mcp[0]?.requiresApproval, true);
  });

  it('isConnectorTool detects BYOC prefixes', () => {
    assert.equal(isConnectorTool('mcp.soc.query'), true);
    assert.equal(isConnectorTool('llm.openai.complete'), true);
    assert.equal(isConnectorTool('grc.list_controls'), false);
  });

  it('merges with builtin agent tools for gateway policy', () => {
    const reg = new ConnectorRegistry();
    reg.applyConfig(
      {
        version: 1,
        llm: [
          {
            id: 'openai',
            label: 'OpenAI',
            kind: 'openai_compatible',
            baseUrl: 'https://api.openai.com',
            apiKeyEnv: 'OPENAI_API_KEY',
          },
        ],
      },
      'test'
    );
    const merged = [...BUILTIN_AGENT_TOOLS, ...buildConnectorToolDefinitions(reg)];
    assert.ok(merged.some((t) => t.name === 'llm.openai.complete'));
    assert.ok(merged.some((t) => t.name === 'soar.run_playbook'));
  });
});
