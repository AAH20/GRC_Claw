import type { EndpointDefinition, GeneratorConfig, OpenApiSpec } from './types.js';

const DEFAULT_CONFIG: GeneratorConfig = {
  title: 'GRC_Claw Gateway API',
  version: '1.0.0',
  description: 'GRC_Claw supervised control-plane gateway — ISO 42001-compliant agentic AI chassis for GRC, compliance automation, and security operations',
  baseUrl: 'http://localhost:3000',
};

function yamlEscape(s: string): string {
  if (s.includes(':') || s.includes('#') || s.includes("'") || s.includes('"') || s.includes('\n') || s.startsWith(' ') || s.endsWith(' ')) {
    return `"${s.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
  }
  return s;
}

function buildSchema(type: string, description?: string): Record<string, unknown> {
  const schema: Record<string, unknown> = { type };
  if (description) schema['description'] = description;
  return schema;
}

function buildOkResponse(schema?: Record<string, unknown>): Record<string, unknown> {
  return {
    description: 'Successful response',
    content: {
      'application/json': {
        schema: schema ?? {
          type: 'object',
          properties: {
            ok: { type: 'boolean' },
          },
        },
      },
    },
  };
}

function buildErrorResponse(): Record<string, unknown> {
  return {
    description: 'Error response',
    content: {
      'application/json': {
        schema: {
          type: 'object',
          properties: {
            error: { type: 'string' },
          },
        },
      },
    },
  };
}

function buildAuthResponse(): Record<string, unknown> {
  return {
    description: 'Unauthorized',
    content: {
      'application/json': {
        schema: {
          type: 'object',
          properties: {
            error: { type: 'string', example: 'unauthorized' },
          },
        },
      },
    },
  };
}

function buildSecurity(authenticated: boolean): Array<Record<string, string[]>> | undefined {
  return authenticated ? [{ BearerAuth: [] }] : undefined;
}

export class OpenAPIGenerator {
  private config: GeneratorConfig;
  private endpoints: EndpointDefinition[] = [];

  constructor(config?: Partial<GeneratorConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  addEndpoint(endpoint: EndpointDefinition): void {
    this.endpoints.push(endpoint);
  }

  addEndpoints(endpoints: EndpointDefinition[]): void {
    this.endpoints.push(...endpoints);
  }

  generate(): OpenApiSpec {
    const paths: OpenApiSpec['paths'] = {};
    const tagsSet = new Set<string>();

    for (const endpoint of this.endpoints) {
      const pathKey = endpoint.path;
      if (!paths[pathKey]) paths[pathKey] = {};

      const responses: Record<string, Record<string, unknown>> = {};
      for (const [code, resp] of Object.entries(endpoint.responses)) {
        const respObj = resp as { description: string; contentType?: string; schema?: Record<string, unknown> };
        responses[code] = {
          description: respObj.description,
          content: respObj.contentType
            ? { [respObj.contentType]: { schema: respObj.schema ?? {} } }
            : undefined,
        };
      }

      const parameters: Array<Record<string, unknown>> = [];
      if (endpoint.queryParams) {
        for (const param of endpoint.queryParams) {
          parameters.push({
            name: param.name,
            in: param.in,
            required: param.required,
            schema: param.schema,
            description: param.description,
          });
        }
      }

      const operation: Record<string, unknown> = {
        summary: endpoint.summary,
        description: endpoint.description,
        operationId: endpoint.operationId,
        tags: endpoint.tags,
        security: buildSecurity(endpoint.authenticated),
        responses,
      };

      if (parameters.length > 0) operation['parameters'] = parameters;
      if (endpoint.requestBody) {
        operation['requestBody'] = {
          required: true,
          content: {
            [endpoint.requestBody.contentType]: {
              schema: endpoint.requestBody.schema,
            },
          },
        };
      }

      paths[pathKey]![endpoint.method.toLowerCase()] = operation;
      for (const tag of endpoint.tags) tagsSet.add(tag);
    }

    const tags = [...tagsSet].map((name) => ({
      name,
      description: `${name} endpoints for GRC_Claw Gateway`,
    }));

    return {
      openapi: '3.0.3',
      info: {
        title: this.config.title,
        version: this.config.version,
        description: this.config.description,
        license: { name: 'MIT', url: 'https://opensource.org/licenses/MIT' },
      },
      servers: [
        { url: this.config.baseUrl, description: 'GRC_Claw Gateway' },
      ],
      paths,
      components: {
        securitySchemes: {
          BearerAuth: {
            type: 'http',
            scheme: 'bearer',
            bearerFormat: 'API Token',
            description: 'GRC_Claw gateway token — pass via Authorization: Bearer <token> or X-GRC-Claw-Token header',
          },
        },
        schemas: {},
      },
      tags,
    };
  }

  toJson(): string {
    return JSON.stringify(this.generate(), null, 2);
  }

  toYaml(): string {
    const spec = this.generate();
    return this.specToYaml(spec, 0);
  }

  private specToYaml(obj: unknown, indent: number): string {
    const pad = '  '.repeat(indent);

    if (obj === null || obj === undefined) return 'null';
    if (typeof obj === 'boolean') return String(obj);
    if (typeof obj === 'number') return String(obj);
    if (typeof obj === 'string') return yamlEscape(obj);

    if (Array.isArray(obj)) {
      if (obj.length === 0) return '[]';
      const items = obj.map((item) => {
        const yaml = this.specToYaml(item, indent + 1);
        if (typeof item === 'object' && item !== null && !Array.isArray(item)) {
          const firstLine = yaml.split('\n')[0]!;
          const rest = yaml.split('\n').slice(1).join('\n');
          return `${pad}- ${firstLine.trimStart()}\n${rest}`;
        }
        return `${pad}- ${yaml}`;
      });
      return items.join('\n');
    }

    if (typeof obj === 'object') {
      const entries = Object.entries(obj as Record<string, unknown>);
      if (entries.length === 0) return '{}';
      const lines = entries.map(([key, value]) => {
        const yamlValue = this.specToYaml(value, indent + 1);
        if (typeof value === 'object' && value !== null) {
          if (Array.isArray(value) && value.length > 0) {
            return `${pad}${yamlEscape(key)}:\n${yamlValue}`;
          }
          if (!Array.isArray(value) && Object.keys(value as Record<string, unknown>).length > 0) {
            return `${pad}${yamlEscape(key)}:\n${yamlValue}`;
          }
          return `${pad}${yamlEscape(key)}: ${yamlValue}`;
        }
        return `${pad}${yamlEscape(key)}: ${yamlValue}`;
      });
      return lines.join('\n');
    }

    return String(obj);
  }

  static buildGatewayEndpoints(): EndpointDefinition[] {
    return [
      {
        path: '/health',
        method: 'GET',
        summary: 'Health check',
        description: 'Returns gateway health status, connected services, and configuration',
        tags: ['System'],
        operationId: 'getHealth',
        authenticated: false,
        responses: {
          '200': { description: 'Gateway is healthy', contentType: 'application/json' },
        },
      },
      {
        path: '/metrics',
        method: 'GET',
        summary: 'Prometheus metrics',
        description: 'Returns gateway metrics in Prometheus exposition format',
        tags: ['System'],
        operationId: 'getMetrics',
        authenticated: false,
        responses: {
          '200': { description: 'Metrics in Prometheus format', contentType: 'text/plain' },
        },
      },
      {
        path: '/api/frameworks',
        method: 'GET',
        summary: 'List framework packs',
        description: 'Returns all available compliance framework packs and their controls',
        tags: ['Frameworks'],
        operationId: 'listFrameworks',
        authenticated: false,
        responses: {
          '200': { description: 'Framework packs', contentType: 'application/json' },
        },
      },
      {
        path: '/api/aims/vendor-gaps',
        method: 'GET',
        summary: 'AI vendor gaps',
        description: 'Returns AIMS vendor gap analysis for AI providers (Anthropic, OpenAI, Cursor, OpenClaw)',
        tags: ['AIMS'],
        operationId: 'getVendorGaps',
        authenticated: false,
        queryParams: [
          { name: 'vendor', in: 'query', required: false, schema: { type: 'string', enum: ['anthropic', 'openai', 'cursor', 'openclaw'] }, description: 'Filter by vendor ID' },
        ],
        responses: {
          '200': { description: 'Vendor gap summary', contentType: 'application/json' },
        },
      },
      {
        path: '/api/aims/technical-controls',
        method: 'GET',
        summary: 'Technical controls',
        description: 'Returns AIMS scope template, clause map, and technical controls',
        tags: ['AIMS'],
        operationId: 'getTechnicalControls',
        authenticated: false,
        responses: {
          '200': { description: 'AIMS technical controls', contentType: 'application/json' },
        },
      },
      {
        path: '/api/agent/invoke',
        method: 'POST',
        summary: 'Invoke agent tool',
        description: 'Invoke a tool via the agent session with assurance envelope, idempotency, and audit trail',
        tags: ['Agent'],
        operationId: 'invokeAgentTool',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            required: ['tool'],
            properties: {
              tool: { type: 'string', description: 'Tool name to invoke' },
              args: { type: 'object', description: 'Tool arguments' },
              sessionId: { type: 'string', description: 'Session identifier' },
              agentId: { type: 'string', description: 'Agent DID or identifier' },
              idempotencyKey: { type: 'string', description: 'Idempotency key' },
              approvalToken: { type: 'string', description: 'Approval token for destructive actions' },
              tenantId: { type: 'number', description: 'Tenant ID' },
            },
          },
        },
        responses: {
          '200': { description: 'Tool execution result', contentType: 'application/json' },
          '401': { description: 'Unauthorized', contentType: 'application/json' },
          '403': { description: 'Tool denied by policy', contentType: 'application/json' },
        },
      },
      {
        path: '/api/skills',
        method: 'GET',
        summary: 'List skills',
        description: 'Returns all registered GRC_Claw skills',
        tags: ['Skills'],
        operationId: 'listSkills',
        authenticated: false,
        responses: {
          '200': { description: 'Skill catalog', contentType: 'application/json' },
        },
      },
      {
        path: '/api/skills/{skillId}',
        method: 'GET',
        summary: 'Get skill detail',
        description: 'Returns details for a specific skill by ID',
        tags: ['Skills'],
        operationId: 'getSkill',
        authenticated: false,
        responses: {
          '200': { description: 'Skill details', contentType: 'application/json' },
          '404': { description: 'Skill not found', contentType: 'application/json' },
        },
      },
      {
        path: '/api/skills/run',
        method: 'POST',
        summary: 'Run a skill',
        description: 'Execute a skill with a given task via the Claw dispatch context',
        tags: ['Skills'],
        operationId: 'runSkill',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            required: ['skillId', 'task'],
            properties: {
              skillId: { type: 'string' },
              task: { type: 'string' },
              sessionId: { type: 'string' },
              llmProviderId: { type: 'string' },
              maxSteps: { type: 'number' },
              readOnlyTools: { type: 'boolean' },
              idempotencyKey: { type: 'string' },
            },
          },
        },
        responses: {
          '200': { description: 'Skill execution result', contentType: 'application/json' },
          '403': { description: 'Skill denied', contentType: 'application/json' },
        },
      },
      {
        path: '/api/action-ledger',
        method: 'GET',
        summary: 'Action ledger',
        description: 'Returns the action ledger events with integrity verification',
        tags: ['Audit'],
        operationId: 'getActionLedger',
        authenticated: true,
        queryParams: [
          { name: 'limit', in: 'query', required: false, schema: { type: 'integer', default: 100 } },
        ],
        responses: {
          '200': { description: 'Ledger events', contentType: 'application/json' },
        },
      },
      {
        path: '/api/assurance',
        method: 'GET',
        summary: 'Assurance summary',
        description: 'Returns the assurance graph summary for agent actions',
        tags: ['Assurance'],
        operationId: 'getAssurance',
        authenticated: true,
        responses: {
          '200': { description: 'Assurance summary', contentType: 'application/json' },
        },
      },
      {
        path: '/api/ingest/normalize',
        method: 'POST',
        summary: 'Normalize security event',
        description: 'Ingest and normalize a security event from a cloud or SIEM source',
        tags: ['Ingest'],
        operationId: 'normalizeEvent',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            required: ['source'],
            properties: {
              source: { type: 'string', description: 'Ingest source identifier' },
              tenantId: { type: 'number' },
              payload: { type: 'object' },
            },
          },
        },
        responses: {
          '200': { description: 'Normalized event', contentType: 'application/json' },
          '400': { description: 'Normalize failed', contentType: 'application/json' },
        },
      },
      {
        path: '/api/risk/monte-carlo',
        method: 'POST',
        summary: 'Monte Carlo simulation',
        description: 'Run a Monte Carlo risk simulation for a scenario',
        tags: ['Risk'],
        operationId: 'runMonteCarlo',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            properties: {
              scenario: { type: 'object' },
              iterations: { type: 'number' },
              seed: { type: 'number' },
            },
          },
        },
        responses: {
          '200': { description: 'Simulation result', contentType: 'application/json' },
        },
      },
      {
        path: '/api/risk/fair',
        method: 'POST',
        summary: 'FAIR risk calculation',
        description: 'Calculate risk using the FAIR (Factor Analysis of Information Risk) model',
        tags: ['Risk'],
        operationId: 'calculateFair',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            properties: {
              scenario: { type: 'object' },
              iterations: { type: 'number' },
              seed: { type: 'number' },
            },
          },
        },
        responses: {
          '200': { description: 'FAIR calculation result', contentType: 'application/json' },
        },
      },
      {
        path: '/api/risk/register',
        method: 'GET',
        summary: 'Risk register',
        description: 'Returns the risk register entries and portfolio metrics',
        tags: ['Risk'],
        operationId: 'getRiskRegister',
        authenticated: true,
        responses: {
          '200': { description: 'Risk register', contentType: 'application/json' },
        },
      },
      {
        path: '/api/risk/heatmap',
        method: 'GET',
        summary: 'Risk heatmap',
        description: 'Generate a risk heatmap from the register',
        tags: ['Risk'],
        operationId: 'getRiskHeatmap',
        authenticated: true,
        responses: {
          '200': { description: 'Risk heatmap', contentType: 'application/json' },
        },
      },
      {
        path: '/api/entities',
        method: 'GET',
        summary: 'List entities',
        description: 'List all organizational entities',
        tags: ['Entities'],
        operationId: 'listEntities',
        authenticated: true,
        responses: {
          '200': { description: 'Entity list', contentType: 'application/json' },
        },
      },
      {
        path: '/api/entities',
        method: 'POST',
        summary: 'Create entity',
        description: 'Create a new organizational entity',
        tags: ['Entities'],
        operationId: 'createEntity',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            properties: {
              name: { type: 'string' },
              type: { type: 'string' },
              parentId: { type: 'string' },
            },
          },
        },
        responses: {
          '201': { description: 'Entity created', contentType: 'application/json' },
        },
      },
      {
        path: '/api/entities/consolidated-report',
        method: 'GET',
        summary: 'Consolidated compliance report',
        description: 'Get a consolidated compliance report across all entities',
        tags: ['Entities'],
        operationId: 'getConsolidatedReport',
        authenticated: true,
        responses: {
          '200': { description: 'Consolidated report', contentType: 'application/json' },
        },
      },
      {
        path: '/api/integrations',
        method: 'GET',
        summary: 'List integrations',
        description: 'List enabled integration marketplace connectors',
        tags: ['Integrations'],
        operationId: 'listIntegrations',
        authenticated: true,
        responses: {
          '200': { description: 'Integration list', contentType: 'application/json' },
        },
      },
      {
        path: '/api/integrations/collect',
        method: 'POST',
        summary: 'Collect from all integrations',
        description: 'Trigger evidence collection from all enabled integration connectors',
        tags: ['Integrations'],
        operationId: 'collectAllIntegrations',
        authenticated: true,
        responses: {
          '200': { description: 'Collection jobs', contentType: 'application/json' },
        },
      },
      {
        path: '/api/integrations/jobs',
        method: 'GET',
        summary: 'Integration collection jobs',
        description: 'List recent integration collection jobs',
        tags: ['Integrations'],
        operationId: 'listIntegrationJobs',
        authenticated: true,
        responses: {
          '200': { description: 'Job list', contentType: 'application/json' },
        },
      },
      {
        path: '/api/policies',
        method: 'GET',
        summary: 'List policies',
        description: 'List all managed policies',
        tags: ['Policies'],
        operationId: 'listPolicies',
        authenticated: true,
        responses: {
          '200': { description: 'Policy list', contentType: 'application/json' },
        },
      },
      {
        path: '/api/policies/create',
        method: 'POST',
        summary: 'Create policy',
        description: 'Create a new policy',
        tags: ['Policies'],
        operationId: 'createPolicy',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: { type: 'object' },
        },
        responses: {
          '201': { description: 'Policy created', contentType: 'application/json' },
        },
      },
      {
        path: '/api/policies/stats',
        method: 'GET',
        summary: 'Policy statistics',
        description: 'Get policy management statistics',
        tags: ['Policies'],
        operationId: 'getPolicyStats',
        authenticated: true,
        responses: {
          '200': { description: 'Policy stats', contentType: 'application/json' },
        },
      },
      {
        path: '/api/vendor-risk/vendors',
        method: 'GET',
        summary: 'List vendors',
        description: 'List all vendor risk assessments',
        tags: ['Vendor Risk'],
        operationId: 'listVendorRiskVendors',
        authenticated: true,
        responses: {
          '200': { description: 'Vendor list', contentType: 'application/json' },
        },
      },
      {
        path: '/api/vendor-risk/vendors',
        method: 'POST',
        summary: 'Create vendor',
        description: 'Create a new vendor risk assessment',
        tags: ['Vendor Risk'],
        operationId: 'createVendorRiskVendor',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: { type: 'object' },
        },
        responses: {
          '201': { description: 'Vendor created', contentType: 'application/json' },
        },
      },
      {
        path: '/api/vendor-risk/dashboard',
        method: 'GET',
        summary: 'Vendor risk dashboard',
        description: 'Get the vendor risk management dashboard',
        tags: ['Vendor Risk'],
        operationId: 'getVendorRiskDashboard',
        authenticated: true,
        responses: {
          '200': { description: 'Vendor risk dashboard', contentType: 'application/json' },
        },
      },
      {
        path: '/api/employees',
        method: 'GET',
        summary: 'List employees',
        description: 'List all employees in the lifecycle engine',
        tags: ['Employees'],
        operationId: 'listEmployees',
        authenticated: true,
        queryParams: [
          { name: 'state', in: 'query', required: false, schema: { type: 'string' } },
          { name: 'department', in: 'query', required: false, schema: { type: 'string' } },
        ],
        responses: {
          '200': { description: 'Employee list', contentType: 'application/json' },
        },
      },
      {
        path: '/api/employees',
        method: 'POST',
        summary: 'Create employee',
        description: 'Create a new employee record',
        tags: ['Employees'],
        operationId: 'createEmployee',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: { type: 'object' },
        },
        responses: {
          '201': { description: 'Employee created', contentType: 'application/json' },
        },
      },
      {
        path: '/api/employees/compliance-dashboard',
        method: 'GET',
        summary: 'Employee compliance dashboard',
        description: 'Get the employee lifecycle compliance dashboard',
        tags: ['Employees'],
        operationId: 'getEmployeeComplianceDashboard',
        authenticated: true,
        responses: {
          '200': { description: 'Compliance dashboard', contentType: 'application/json' },
        },
      },
      {
        path: '/api/tasks',
        method: 'GET',
        summary: 'List tasks',
        description: 'List all compliance tasks',
        tags: ['Tasks'],
        operationId: 'listTasks',
        authenticated: true,
        responses: {
          '200': { description: 'Task list', contentType: 'application/json' },
        },
      },
      {
        path: '/api/tasks',
        method: 'POST',
        summary: 'Create task',
        description: 'Create a new compliance task',
        tags: ['Tasks'],
        operationId: 'createTask',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: { type: 'object' },
        },
        responses: {
          '201': { description: 'Task created', contentType: 'application/json' },
        },
      },
      {
        path: '/api/tasks/analytics',
        method: 'GET',
        summary: 'Task analytics',
        description: 'Get compliance task analytics',
        tags: ['Tasks'],
        operationId: 'getTaskAnalytics',
        authenticated: true,
        responses: {
          '200': { description: 'Task analytics', contentType: 'application/json' },
        },
      },
      {
        path: '/api/autopilot/run-cycle',
        method: 'POST',
        summary: 'Run autopilot cycle',
        description: 'Execute a full compliance autopilot cycle (monitor, detect, remediate, verify)',
        tags: ['Autopilot'],
        operationId: 'runAutopilotCycle',
        authenticated: true,
        responses: {
          '200': { description: 'Cycle result', contentType: 'application/json' },
        },
      },
      {
        path: '/api/autopilot/status',
        method: 'GET',
        summary: 'Autopilot status',
        description: 'Get the current compliance autopilot status and control overview',
        tags: ['Autopilot'],
        operationId: 'getAutopilotStatus',
        authenticated: true,
        responses: {
          '200': { description: 'Autopilot status', contentType: 'application/json' },
        },
      },
      {
        path: '/api/autopilot/audit-trail',
        method: 'GET',
        summary: 'Autopilot audit trail',
        description: 'Get the compliance autopilot audit trail with integrity verification',
        tags: ['Autopilot'],
        operationId: 'getAutopilotAuditTrail',
        authenticated: true,
        responses: {
          '200': { description: 'Audit trail', contentType: 'application/json' },
        },
      },
      {
        path: '/api/drift/capture-baseline',
        method: 'POST',
        summary: 'Capture drift baseline',
        description: 'Capture a new compliance baseline snapshot for drift detection',
        tags: ['Drift'],
        operationId: 'captureBaseline',
        authenticated: true,
        responses: {
          '200': { description: 'Baseline captured', contentType: 'application/json' },
        },
      },
      {
        path: '/api/drift/detect',
        method: 'POST',
        summary: 'Detect drift',
        description: 'Run a drift detection cycle against the current baseline',
        tags: ['Drift'],
        operationId: 'detectDrift',
        authenticated: true,
        responses: {
          '200': { description: 'Drift detection result', contentType: 'application/json' },
        },
      },
      {
        path: '/api/drift/history',
        method: 'GET',
        summary: 'Drift history',
        description: 'Get the drift event history',
        tags: ['Drift'],
        operationId: 'getDriftHistory',
        authenticated: true,
        responses: {
          '200': { description: 'Drift history', contentType: 'application/json' },
        },
      },
      {
        path: '/api/drift/alerts',
        method: 'GET',
        summary: 'Drift alerts',
        description: 'Get drift detection alert history',
        tags: ['Drift'],
        operationId: 'getDriftAlerts',
        authenticated: true,
        responses: {
          '200': { description: 'Drift alerts', contentType: 'application/json' },
        },
      },
      {
        path: '/api/evidence/collect',
        method: 'POST',
        summary: 'Collect evidence',
        description: 'Collect compliance evidence for a specific control and framework',
        tags: ['Evidence'],
        operationId: 'collectEvidence',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            properties: {
              framework: { type: 'string' },
              category: { type: 'string' },
              controlId: { type: 'string' },
            },
          },
        },
        responses: {
          '200': { description: 'Evidence collected', contentType: 'application/json' },
        },
      },
      {
        path: '/api/evidence/inventory',
        method: 'GET',
        summary: 'Evidence inventory',
        description: 'Get the full evidence inventory',
        tags: ['Evidence'],
        operationId: 'getEvidenceInventory',
        authenticated: true,
        responses: {
          '200': { description: 'Evidence inventory', contentType: 'application/json' },
        },
      },
      {
        path: '/api/accm/detect-gaps',
        method: 'POST',
        summary: 'Detect ACCM gaps',
        description: 'Detect compliance gaps for a framework via the ACCM engine',
        tags: ['ACCM'],
        operationId: 'detectAccmGaps',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            properties: {
              frameworkCode: { type: 'string', default: 'iso27001' },
            },
          },
        },
        responses: {
          '200': { description: 'Gaps detected', contentType: 'application/json' },
        },
      },
      {
        path: '/api/accm/full-cycle',
        method: 'POST',
        summary: 'ACCM full cycle',
        description: 'Run a full ACCM compliance cycle: detect gaps, remediate, and verify',
        tags: ['ACCM'],
        operationId: 'accmFullCycle',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            properties: {
              frameworkCode: { type: 'string', default: 'iso27001' },
            },
          },
        },
        responses: {
          '200': { description: 'Full cycle report', contentType: 'application/json' },
        },
      },
      {
        path: '/api/agents',
        method: 'GET',
        summary: 'List agents',
        description: 'List all registered agents in the agent builder',
        tags: ['Agents'],
        operationId: 'listAgents',
        authenticated: true,
        responses: {
          '200': { description: 'Agent list', contentType: 'application/json' },
        },
      },
      {
        path: '/api/agents',
        method: 'POST',
        summary: 'Create agent',
        description: 'Create a new agent definition',
        tags: ['Agents'],
        operationId: 'createAgent',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: { type: 'object' },
        },
        responses: {
          '201': { description: 'Agent created', contentType: 'application/json' },
        },
      },
      {
        path: '/api/agents/{agentId}/trigger',
        method: 'POST',
        summary: 'Trigger agent',
        description: 'Trigger an agent execution run',
        tags: ['Agents'],
        operationId: 'triggerAgent',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: { type: 'object' },
        },
        responses: {
          '200': { description: 'Agent run result', contentType: 'application/json' },
        },
      },
      {
        path: '/api/crosswalk/{source}/{target}',
        method: 'GET',
        summary: 'Framework crosswalk',
        description: 'Generate a crosswalk report between two compliance frameworks',
        tags: ['Crosswalk'],
        operationId: 'getCrosswalk',
        authenticated: true,
        responses: {
          '200': { description: 'Crosswalk report', contentType: 'application/json' },
        },
      },
      {
        path: '/api/crosswalk/overlaps',
        method: 'GET',
        summary: 'Framework overlaps',
        description: 'Find control overlaps between supported framework pairs',
        tags: ['Crosswalk'],
        operationId: 'getOverlaps',
        authenticated: true,
        responses: {
          '200': { description: 'Overlap data', contentType: 'application/json' },
        },
      },
      {
        path: '/api/chat',
        method: 'POST',
        summary: 'Chat with GRC assistant',
        description: 'Send a message to the GRC chat assistant',
        tags: ['Chat'],
        operationId: 'chatMessage',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            required: ['message'],
            properties: {
              message: { type: 'string' },
              context: { type: 'object' },
              sessionId: { type: 'string' },
            },
          },
        },
        responses: {
          '200': { description: 'Chat response', contentType: 'application/json' },
        },
      },
      {
        path: '/api/reporting/board',
        method: 'GET',
        summary: 'Board report',
        description: 'Generate a board-level compliance report',
        tags: ['Reporting'],
        operationId: 'getBoardReport',
        authenticated: true,
        queryParams: [
          { name: 'type', in: 'query', required: false, schema: { type: 'string', default: 'board_summary' } },
          { name: 'period', in: 'query', required: false, schema: { type: 'string' } },
        ],
        responses: {
          '200': { description: 'Board report', contentType: 'application/json' },
        },
      },
      {
        path: '/api/reporting/dashboard',
        method: 'GET',
        summary: 'Executive dashboard',
        description: 'Get the executive compliance dashboard',
        tags: ['Reporting'],
        operationId: 'getExecutiveDashboard',
        authenticated: true,
        responses: {
          '200': { description: 'Executive dashboard', contentType: 'application/json' },
        },
      },
      {
        path: '/api/traces',
        method: 'GET',
        summary: 'List traces',
        description: 'List observability traces with stats',
        tags: ['Observability'],
        operationId: 'listTraces',
        authenticated: true,
        queryParams: [
          { name: 'limit', in: 'query', required: false, schema: { type: 'integer', default: 50 } },
        ],
        responses: {
          '200': { description: 'Trace list', contentType: 'application/json' },
        },
      },
      {
        path: '/api/traces/metrics',
        method: 'GET',
        summary: 'Trace metrics',
        description: 'Get observability trace metrics',
        tags: ['Observability'],
        operationId: 'getTraceMetrics',
        authenticated: true,
        responses: {
          '200': { description: 'Trace metrics', contentType: 'application/json' },
        },
      },
      {
        path: '/api/audit-trail',
        method: 'GET',
        summary: 'Agent audit trail',
        description: 'Get the agent audit trail records',
        tags: ['Audit'],
        operationId: 'getAuditTrail',
        authenticated: true,
        queryParams: [
          { name: 'limit', in: 'query', required: false, schema: { type: 'integer', default: 100 } },
        ],
        responses: {
          '200': { description: 'Audit trail records', contentType: 'application/json' },
        },
      },
      {
        path: '/api/audit-trail/verify',
        method: 'POST',
        summary: 'Verify audit trail',
        description: 'Verify the integrity of the agent audit trail',
        tags: ['Audit'],
        operationId: 'verifyAuditTrail',
        authenticated: true,
        responses: {
          '200': { description: 'Integrity verification result', contentType: 'application/json' },
        },
      },
      {
        path: '/api/zk/prove',
        method: 'POST',
        summary: 'Generate ZK proof',
        description: 'Generate a zero-knowledge compliance proof for a control',
        tags: ['ZK Compliance'],
        operationId: 'generateZkProof',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: {
            type: 'object',
            properties: {
              controlId: { type: 'string' },
              frameworkCode: { type: 'string' },
              controlStatus: { type: 'string' },
              evidenceHashes: { type: 'array', items: { type: 'string' } },
            },
          },
        },
        responses: {
          '200': { description: 'ZK proof', contentType: 'application/json' },
        },
      },
      {
        path: '/api/zk/verify',
        method: 'POST',
        summary: 'Verify ZK proof',
        description: 'Verify a zero-knowledge compliance proof',
        tags: ['ZK Compliance'],
        operationId: 'verifyZkProof',
        authenticated: true,
        requestBody: {
          contentType: 'application/json',
          schema: { type: 'object' },
        },
        responses: {
          '200': { description: 'Verification result', contentType: 'application/json' },
        },
      },
      {
        path: '/api/dashboard/realtime',
        method: 'GET',
        summary: 'Real-time compliance dashboard',
        description: 'Get real-time compliance posture data from drift detector, autopilot, and evidence store. WebSocket-backed via ws://host/ws compliance_updates channel.',
        tags: ['Dashboard'],
        operationId: 'getRealtimeDashboard',
        authenticated: true,
        responses: {
          '200': {
            description: 'Real-time compliance data with framework breakdown, autopilot status, drift info, and WebSocket subscription details',
            contentType: 'application/json',
          },
        },
      },
      {
        path: '/api/dashboard/trends',
        method: 'GET',
        summary: 'Compliance trends',
        description: 'Get compliance trend data over a configurable period (default 30 days)',
        tags: ['Dashboard'],
        operationId: 'getComplianceTrends',
        authenticated: true,
        queryParams: [
          { name: 'days', in: 'query', required: false, schema: { type: 'integer', default: 30, description: 'Number of days to look back (30, 60, or 90)' } },
        ],
        responses: {
          '200': { description: 'Compliance trend data', contentType: 'application/json' },
        },
      },
      {
        path: '/api/dashboard/alerts',
        method: 'GET',
        summary: 'Compliance alerts',
        description: 'Get active compliance alerts from drift detector, autopilot gaps, and failed remediations',
        tags: ['Dashboard'],
        operationId: 'getComplianceAlerts',
        authenticated: true,
        responses: {
          '200': { description: 'Active compliance alerts sorted by priority', contentType: 'application/json' },
        },
      },
      {
        path: '/api/dashboard/kpis',
        method: 'GET',
        summary: 'Compliance KPIs',
        description: 'Get key performance indicators: compliance scores, autopilot metrics, drift stats, and activity counts',
        tags: ['Dashboard'],
        operationId: 'getComplianceKpis',
        authenticated: true,
        responses: {
          '200': { description: 'Compliance KPIs', contentType: 'application/json' },
        },
      },
      {
        path: '/api/openapi.json',
        method: 'GET',
        summary: 'OpenAPI spec (JSON)',
        description: 'Returns the complete OpenAPI 3.0 specification in JSON format',
        tags: ['API Spec'],
        operationId: 'getOpenApiJson',
        authenticated: false,
        responses: {
          '200': { description: 'OpenAPI 3.0 JSON specification', contentType: 'application/json' },
        },
      },
      {
        path: '/api/openapi.yaml',
        method: 'GET',
        summary: 'OpenAPI spec (YAML)',
        description: 'Returns the complete OpenAPI 3.0 specification in YAML format',
        tags: ['API Spec'],
        operationId: 'getOpenApiYaml',
        authenticated: false,
        responses: {
          '200': { description: 'OpenAPI 3.0 YAML specification', contentType: 'text/yaml' },
        },
      },
    ];
  }
}
