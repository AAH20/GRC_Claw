import { createInterface } from "node:readline";
import type {
  MCPTool,
  MCPResource,
  MCPPrompt,
  JSONRPCRequest,
  JSONRPCResponse,
  InitializeResult,
  ToolCallParams,
  ToolResult,
  PromptGetParams,
} from "./types.js";

export interface MCPServerConfig {
  baseUrl: string;
  token?: string;
}

const SERVER_INFO = { name: "grc-claw-mcp", version: "0.1.0" };
const PROTOCOL_VERSION = "2024-11-05";

const TOOLS: MCPTool[] = [
  {
    name: "grc_list_frameworks",
    description: "List all compliance frameworks managed by GRC_Claw",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "grc_check_control",
    description: "Check the status of a specific compliance control",
    inputSchema: {
      type: "object",
      properties: {
        controlId: { type: "string", description: "Control identifier (e.g. A.5.1.1)" },
        framework: { type: "string", description: "Framework name (e.g. iso27001, soc2)" },
      },
      required: ["controlId"],
    },
  },
  {
    name: "grc_list_evidence",
    description: "List evidence artifacts for a specific control",
    inputSchema: {
      type: "object",
      properties: {
        controlId: { type: "string", description: "Control identifier" },
      },
      required: ["controlId"],
    },
  },
  {
    name: "grc_get_posture",
    description: "Get the current compliance posture summary",
    inputSchema: {
      type: "object",
      properties: {
        framework: { type: "string", description: "Framework to filter by" },
      },
    },
  },
  {
    name: "grc_list_vendors",
    description: "List third-party vendors and their risk ratings",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "grc_get_risk_score",
    description: "Get the current risk score for the organization",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "grc_list_incidents",
    description: "List security incidents",
    inputSchema: {
      type: "object",
      properties: {
        status: { type: "string", description: "Filter by status (open, investigating, resolved)" },
      },
    },
  },
  {
    name: "grc_list_findings",
    description: "List audit findings",
    inputSchema: {
      type: "object",
      properties: {
        severity: { type: "string", description: "Filter by severity (critical, high, medium, low)" },
      },
    },
  },
  {
    name: "grc_run_scan",
    description: "Run a compliance scan against a framework",
    inputSchema: {
      type: "object",
      properties: {
        framework: { type: "string", description: "Framework to scan against" },
      },
      required: ["framework"],
    },
  },
  {
    name: "grc_get_entity_report",
    description: "Get a compliance report for a specific entity",
    inputSchema: {
      type: "object",
      properties: {
        entityId: { type: "string", description: "Entity identifier" },
      },
      required: ["entityId"],
    },
  },
  // v2.0 tools
  {
    name: "grc_scan_repo",
    description: "Run a compliance and PQC scan against a local repository path",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string", description: "Directory path to scan (default: current directory)" },
        framework: { type: "string", description: "Framework to check against (iso27001, soc2, nist-csf, iso42001)" },
        pqc: { type: "boolean", description: "Also scan for deprecated cryptography (PQC readiness)" },
      },
    },
  },
  {
    name: "grc_create_evidence",
    description: "Store a new evidence artifact linked to a compliance control",
    inputSchema: {
      type: "object",
      properties: {
        controlId: { type: "string", description: "Control identifier (e.g. A.9.4.2)" },
        framework: { type: "string", description: "Framework code (iso27001, soc2, nist-csf)" },
        evidenceType: { type: "string", description: "Type: configuration, policy, log, certificate, screenshot" },
        content: { type: "string", description: "Evidence content or description" },
        source: { type: "string", description: "Evidence source (e.g. aws-iam, github, okta)" },
      },
      required: ["controlId", "content"],
    },
  },
  {
    name: "grc_get_regulatory_alerts",
    description: "Get latest regulatory change alerts affecting your compliance frameworks",
    inputSchema: {
      type: "object",
      properties: {
        framework: { type: "string", description: "Filter by framework (eu-ai-act, dora, nis2, gdpr, nist-csf, iso42001)" },
        impact: { type: "string", description: "Filter by impact level (critical, significant, moderate)" },
        action_required: { type: "boolean", description: "Only return alerts requiring action" },
      },
    },
  },
  {
    name: "grc_pqc_scan",
    description: "Scan code for deprecated cryptographic patterns that must be migrated before NIST PQC mandates (FedRAMP 2027)",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string", description: "Directory to scan (default: current directory)" },
        severity: { type: "string", description: "Filter by severity: critical, high, medium" },
      },
    },
  },
  {
    name: "grc_verify_zk_proof",
    description: "Verify a Zero-Knowledge compliance attestation proof for an organization",
    inputSchema: {
      type: "object",
      properties: {
        orgSlug: { type: "string", description: "Organization slug" },
        framework: { type: "string", description: "Framework to verify (soc2, iso27001, nist-csf, iso42001)" },
      },
      required: ["orgSlug", "framework"],
    },
  },
  {
    name: "grc_get_trust_score",
    description: "Get the behavioral trust score for an AI agent",
    inputSchema: {
      type: "object",
      properties: {
        agentId: { type: "string", description: "Agent identifier (DID or name)" },
      },
      required: ["agentId"],
    },
  },
];

const RESOURCES: MCPResource[] = [
  {
    uri: "grc://frameworks",
    name: "Framework Definitions",
    mimeType: "application/json",
    text: JSON.stringify({ description: "All compliance frameworks managed by GRC_Claw" }),
  },
  {
    uri: "grc://posture",
    name: "Compliance Posture",
    mimeType: "application/json",
    text: JSON.stringify({ description: "Current compliance posture across all frameworks" }),
  },
  {
    uri: "grc://risk-register",
    name: "Risk Register",
    mimeType: "application/json",
    text: JSON.stringify({ description: "Organization risk register" }),
  },
];

const PROMPTS: MCPPrompt[] = [
  {
    name: "compliance_summary",
    description: "Generate a compliance summary for a given framework",
    arguments: [
      { name: "framework", description: "Framework name (e.g. iso27001, soc2)", required: true },
    ],
  },
  {
    name: "risk_assessment",
    description: "Generate a risk assessment based on current findings",
    arguments: [],
  },
  {
    name: "audit_prep",
    description: "Prepare an audit readiness checklist for a framework",
    arguments: [
      { name: "framework", description: "Framework to prepare for", required: true },
    ],
  },
];

function rpcResponse(id: string | number | null | undefined, result: unknown): JSONRPCResponse {
  return { jsonrpc: "2.0", id: id ?? null, result };
}

function rpcError(id: string | number | null | undefined, code: number, message: string, data?: unknown): JSONRPCResponse {
  return { jsonrpc: "2.0", id: id ?? null, error: { code, message, data } };
}

async function gatewayFetch(config: MCPServerConfig, path: string, init?: RequestInit): Promise<unknown> {
  const url = `${config.baseUrl}${path}`;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (config.token) headers["Authorization"] = `Bearer ${config.token}`;

  const res = await fetch(url, { ...init, headers: { ...headers, ...init?.headers } });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Gateway ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

async function handleToolCall(name: string, args: Record<string, unknown> | undefined, config: MCPServerConfig): Promise<ToolResult> {
  try {
    let result: unknown;
    switch (name) {
      case "grc_list_frameworks":
        result = await gatewayFetch(config, "/api/frameworks");
        break;
      case "grc_check_control":
        result = await gatewayFetch(config, "/api/agent/invoke", {
          method: "POST",
          body: JSON.stringify({
            tool: "frameworks.check_control",
            args: {
              controlCode: args?.controlId,
              frameworkCode: args?.framework,
            },
          }),
        });
        break;
      case "grc_list_evidence":
        result = await gatewayFetch(config, "/api/agent/invoke", {
          method: "POST",
          body: JSON.stringify({
            tool: "evidence.read",
            args: { evidenceId: args?.controlId },
          }),
        });
        break;
      case "grc_get_posture":
        result = await gatewayFetch(config, "/api/agent/invoke", {
          method: "POST",
          body: JSON.stringify({
            tool: "compliance.get_posture",
            args: { framework: args?.framework },
          }),
        });
        break;
      case "grc_list_vendors":
        result = await gatewayFetch(config, "/api/agent/invoke", {
          method: "POST",
          body: JSON.stringify({ tool: "cloud.list_connectors", args: {} }),
        });
        break;
      case "grc_get_risk_score":
        result = await gatewayFetch(config, "/api/risk/register");
        break;
      case "grc_list_incidents":
        result = await gatewayFetch(config, "/api/agent/invoke", {
          method: "POST",
          body: JSON.stringify({
            tool: "audit.list_findings",
            args: { severity: args?.status },
          }),
        });
        break;
      case "grc_list_findings":
        result = await gatewayFetch(config, "/api/agent/invoke", {
          method: "POST",
          body: JSON.stringify({
            tool: "audit.list_findings",
            args: { severity: args?.severity },
          }),
        });
        break;
      case "grc_run_scan":
        result = await gatewayFetch(config, "/api/agent/invoke", {
          method: "POST",
          body: JSON.stringify({
            tool: "compliance.run_scan",
            args: { frameworkCode: args?.framework },
          }),
        });
        break;
      case "grc_get_entity_report":
        result = await gatewayFetch(config, `/api/entities/${args?.entityId}/compliance`);
        break;
      // v2.0 tools — call A2Z SOC platform API
      case "grc_scan_repo":
        result = await gatewayFetch(config, "/api/agent/invoke", {
          method: "POST",
          body: JSON.stringify({ tool: "compliance.run_scan", args: { frameworkCode: args?.framework ?? "iso27001", path: args?.path ?? ".", includePqc: args?.pqc ?? false } }),
        });
        break;
      case "grc_create_evidence":
        result = await gatewayFetch(config, "/api/agent/invoke", {
          method: "POST",
          body: JSON.stringify({ tool: "evidence.attach", args: { controlId: args?.controlId, framework: args?.framework ?? "iso27001", type: args?.evidenceType ?? "configuration", content: args?.content, source: args?.source ?? "mcp" } }),
        });
        break;
      case "grc_get_regulatory_alerts": {
        const params = new URLSearchParams();
        if (args?.framework) params.set("framework", String(args.framework));
        if (args?.impact) params.set("impact", String(args.impact));
        if (args?.action_required) params.set("action_required", "true");
        result = await fetch(`https://a2zsoc.com/api/platform/regulatory-intelligence/alerts?${params}`, { headers: { "Content-Type": "application/json" } }).then(r => r.json());
        break;
      }
      case "grc_pqc_scan": {
        const pqcParams = new URLSearchParams();
        if (args?.severity) pqcParams.set("severity", String(args.severity));
        result = await fetch(`https://a2zsoc.com/api/platform/pqc-scan?${pqcParams}`, { headers: { "Content-Type": "application/json" } }).then(r => r.json());
        break;
      }
      case "grc_verify_zk_proof":
        result = await fetch(`https://a2zsoc.com/api/platform/verify/${encodeURIComponent(String(args?.orgSlug))}/${encodeURIComponent(String(args?.framework))}`, { headers: { "Content-Type": "application/json" } }).then(r => r.json());
        break;
      case "grc_get_trust_score":
        result = await fetch(`https://a2zsoc.com/api/platform/agent-trust/score/${encodeURIComponent(String(args?.agentId))}`, { headers: { "Content-Type": "application/json" } }).then(r => r.json());
        break;
      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
    }
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  } catch (err) {
    return { content: [{ type: "text", text: `Error: ${err instanceof Error ? err.message : String(err)}` }], isError: true };
  }
}

async function handleResourceRead(uri: string, config: MCPServerConfig): Promise<string> {
  if (uri === "grc://frameworks") {
    const data = await gatewayFetch(config, "/api/frameworks");
    return JSON.stringify(data, null, 2);
  }
  if (uri === "grc://posture") {
    const data = await gatewayFetch(config, "/api/agent/invoke", {
      method: "POST",
      body: JSON.stringify({ tool: "compliance.get_posture", args: {} }),
    });
    return JSON.stringify(data, null, 2);
  }
  if (uri === "grc://risk-register") {
    const data = await gatewayFetch(config, "/api/risk/register");
    return JSON.stringify(data, null, 2);
  }
  const frameworkMatch = uri.match(/^grc:\/\/controls\/(.+)$/);
  if (frameworkMatch) {
    const data = await gatewayFetch(config, `/api/frameworks/${frameworkMatch[1]}/controls`);
    return JSON.stringify(data, null, 2);
  }
  const evidenceMatch = uri.match(/^grc:\/\/evidence\/(.+)$/);
  if (evidenceMatch) {
    const data = await gatewayFetch(config, "/api/agent/invoke", {
      method: "POST",
      body: JSON.stringify({ tool: "evidence.read", args: { evidenceId: evidenceMatch[1] } }),
    });
    return JSON.stringify(data, null, 2);
  }
  throw new Error(`Unknown resource: ${uri}`);
}

function handlePromptGet(name: string, args: Record<string, unknown> | undefined): string {
  switch (name) {
    case "compliance_summary":
      return `Provide a compliance summary for the ${args?.framework ?? "all"} framework. Include overall status, control coverage, gaps, and recommendations.`;
    case "risk_assessment":
      return "Analyze the current risk landscape. Include top risks, risk scores, mitigations in place, and open gaps.";
    case "audit_prep":
      return `Prepare an audit readiness checklist for ${args?.framework ?? "ISO 27001"}. Include evidence requirements, common findings, and preparation timeline.`;
    default:
      throw new Error(`Unknown prompt: ${name}`);
  }
}

export class MCPServer {
  private config: MCPServerConfig;
  private initialized = false;

  constructor(config: MCPServerConfig) {
    this.config = config;
  }

  async handleRequest(request: JSONRPCRequest): Promise<JSONRPCResponse> {
    const { id, method, params } = request;

    try {
      switch (method) {
        case "initialize":
          this.initialized = true;
          return rpcResponse(id, {
            protocolVersion: PROTOCOL_VERSION,
            capabilities: {
              tools: {},
              resources: { listChanged: true },
              prompts: {},
            },
            serverInfo: SERVER_INFO,
          } satisfies InitializeResult);

        case "notifications/initialized":
          return rpcResponse(id, {});

        case "tools/list":
          return rpcResponse(id, { tools: TOOLS });

        case "tools/call": {
          const { name, arguments: args } = params as unknown as ToolCallParams;
          const result = await handleToolCall(name, args as Record<string, unknown> | undefined, this.config);
          return rpcResponse(id, result);
        }

        case "resources/list":
          return rpcResponse(id, { resources: RESOURCES });

        case "resources/read": {
          const { uri } = params as unknown as { uri: string };
          const text = await handleResourceRead(uri, this.config);
          return rpcResponse(id, { contents: [{ uri, mimeType: "application/json", text }] });
        }

        case "prompts/list":
          return rpcResponse(id, { prompts: PROMPTS });

        case "prompts/get": {
          const { name, arguments: args } = params as unknown as PromptGetParams;
          const text = handlePromptGet(name, args as Record<string, unknown> | undefined);
          return rpcResponse(id, { description: `Generated prompt for ${name}`, messages: [{ role: "user", content: { type: "text", text } }] });
        }

        default:
          return rpcError(id, -32601, `Method not found: ${method}`);
      }
    } catch (err) {
      return rpcError(id, -32603, err instanceof Error ? err.message : String(err));
    }
  }

  start(): void {
    const rl = createInterface({ input: process.stdin });
    rl.on("line", async (line) => {
      const trimmed = line.trim();
      if (!trimmed) return;

      let request: JSONRPCRequest;
      try {
        request = JSON.parse(trimmed) as JSONRPCRequest;
      } catch {
        const response = rpcError(null, -32700, "Parse error");
        process.stdout.write(JSON.stringify(response) + "\n");
        return;
      }

      const response = await this.handleRequest(request);
      process.stdout.write(JSON.stringify(response) + "\n");
    });

    rl.on("close", () => process.exit(0));
  }
}
