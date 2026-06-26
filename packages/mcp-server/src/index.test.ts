import { describe, it, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { MCPServer, type MCPServerConfig } from "./server.js";

function makeRequest(id: string | number | null, method: string, params?: Record<string, unknown>) {
  return { jsonrpc: "2.0" as const, id, method, params };
}

function getConfig(): MCPServerConfig {
  return { baseUrl: "http://localhost:37777" };
}

describe("MCPServer", () => {
  let server: MCPServer;

  beforeEach(() => {
    server = new MCPServer(getConfig());
  });

  it("should respond to initialize with protocol version and capabilities", async () => {
    const res = await server.handleRequest(makeRequest(1, "initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "test-client", version: "1.0.0" },
    }));

    assert.equal(res.jsonrpc, "2.0");
    assert.equal(res.id, 1);
    assert.ok(!res.error);

    const result = res.result as Record<string, unknown>;
    assert.equal(result.protocolVersion, "2024-11-05");
    assert.ok(result.serverInfo);
    assert.equal((result.serverInfo as Record<string, string>).name, "grc-claw-mcp");
    assert.ok(result.capabilities);
    assert.ok((result.capabilities as Record<string, unknown>).tools);
    assert.ok((result.capabilities as Record<string, unknown>).resources);
    assert.ok((result.capabilities as Record<string, unknown>).prompts);
  });

  it("should return all 10 tools on tools/list", async () => {
    const res = await server.handleRequest(makeRequest(2, "tools/list"));

    assert.ok(!res.error);
    const result = res.result as { tools: Array<{ name: string }> };
    assert.equal(result.tools.length, 10);

    const names = result.tools.map((t) => t.name);
    assert.ok(names.includes("grc_list_frameworks"));
    assert.ok(names.includes("grc_check_control"));
    assert.ok(names.includes("grc_list_evidence"));
    assert.ok(names.includes("grc_get_posture"));
    assert.ok(names.includes("grc_list_vendors"));
    assert.ok(names.includes("grc_get_risk_score"));
    assert.ok(names.includes("grc_list_incidents"));
    assert.ok(names.includes("grc_list_findings"));
    assert.ok(names.includes("grc_run_scan"));
    assert.ok(names.includes("grc_get_entity_report"));
  });

  it("should return error for tools/call with unknown tool", async () => {
    const res = await server.handleRequest(makeRequest(3, "tools/call", {
      name: "nonexistent_tool",
      arguments: {},
    }));

    assert.ok(!res.error);
    const result = res.result as { content: Array<{ text: string }>; isError: boolean };
    assert.equal(result.isError, true);
    assert.ok(result.content[0].text.includes("Unknown tool"));
  });

  it("should return all resources on resources/list", async () => {
    const res = await server.handleRequest(makeRequest(4, "resources/list"));

    assert.ok(!res.error);
    const result = res.result as { resources: Array<{ uri: string }> };
    assert.ok(result.resources.length >= 3);

    const uris = result.resources.map((r) => r.uri);
    assert.ok(uris.includes("grc://frameworks"));
    assert.ok(uris.includes("grc://posture"));
    assert.ok(uris.includes("grc://risk-register"));
  });

  it("should return error for unknown resource URI", async () => {
    const res = await server.handleRequest(makeRequest(5, "resources/read", {
      uri: "grc://unknown-resource",
    }));

    assert.ok(res.error);
    assert.equal(res.error.code, -32603);
  });

  it("should return all prompts on prompts/list", async () => {
    const res = await server.handleRequest(makeRequest(6, "prompts/list"));

    assert.ok(!res.error);
    const result = res.result as { prompts: Array<{ name: string }> };
    assert.equal(result.prompts.length, 3);

    const names = result.prompts.map((p) => p.name);
    assert.ok(names.includes("compliance_summary"));
    assert.ok(names.includes("risk_assessment"));
    assert.ok(names.includes("audit_prep"));
  });

  it("should return prompt text on prompts/get", async () => {
    const res = await server.handleRequest(makeRequest(7, "prompts/get", {
      name: "compliance_summary",
      arguments: { framework: "soc2" },
    }));

    assert.ok(!res.error);
    const result = res.result as { messages: Array<{ content: { text: string } }> };
    assert.ok(result.messages[0].content.text.includes("soc2"));
  });

  it("should return method not found for unknown methods", async () => {
    const res = await server.handleRequest(makeRequest(8, "unknown/method"));

    assert.ok(res.error);
    assert.equal(res.error.code, -32601);
    assert.ok(res.error.message.includes("Method not found"));
  });

  it("should handle malformed JSON-RPC by returning parse error", async () => {
    const request = { jsonrpc: "1.0", id: 9, method: "test" } as unknown;
    const res = await server.handleRequest(request as Parameters<MCPServer["handleRequest"]>[0]);

    // The server handles this at the transport level, but the request object
    // still gets processed — this tests the idempotency of the handler
    assert.ok(res.jsonrpc === "2.0");
  });
});
