export interface PageExplain {
  what: string;
  why: string;
  how: string[];
  a2zRole: string;
}

export interface CursorAutoHint {
  endpoint: string;
  method: string;
  auth: boolean;
  description: string;
  exampleBody?: string;
  agentInstruction: string;
}

export interface PageMeta {
  id: string;
  title: string;
  subtitle: string;
  explain: PageExplain;
  cursor: CursorAutoHint;
}

export const PAGE_META: Record<string, PageMeta> = {
  dashboard: {
    id: 'dashboard',
    title: 'Control plane dashboard',
    subtitle:
      'Live view of the GRC_Claw gateway — capabilities, BYOC connectors, and Private A2Z SOC bridge status.',
    explain: {
      what: 'The dashboard is your operator home screen. It polls the gateway health endpoint and summarizes which security modules are active.',
      why: 'Before running ingest, agent tools, or compliance workflows, confirm the gateway is reachable and paired with your A2Z SOC tenant.',
      how: [
        'Start the gateway with GRC_CLAW_GATEWAY_TOKEN set.',
        'Save the same token in Settings so authenticated API calls succeed.',
        'Use Refresh to re-check health after changing env vars or connectors.',
        'Run A2Z SOC sync from here when A2Z_SOC_MODE=private is configured.',
      ],
      a2zRole:
        'When connected to Private A2Z SOC, health shows a2z_soc_mode and sync pulls the last hour of security_events into GRC impact mapping.',
    },
    cursor: {
      endpoint: '/health',
      method: 'GET',
      auth: false,
      description: 'Gateway liveness and capability flags.',
      agentInstruction:
        'Call GET /health first. If ok, read a2z_soc_mode, llm_providers, and cloud_sources before deeper API calls.',
    },
  },
  frameworks: {
    id: 'frameworks',
    title: 'Compliance framework packs',
    subtitle:
      'Audit-ready starter controls for ISO 27001, NIST CSF, SOC 2, and ISO/IEC 42001 — mapped for continuous monitoring.',
    explain: {
      what: 'Framework packs are structured control libraries shipped in-repo. Each control has an ID, code, title, and domain for GRC workflows.',
      why: 'Auditors and CISOs need a canonical control baseline before evidence collection or SIEM-to-control mapping.',
      how: [
        'Filter by framework code to focus on one standard.',
        'Use control IDs when attaching evidence or mapping ingest events.',
        'ISO 42001 AIMS pack complements the dedicated AIMS vendor-gap page.',
      ],
      a2zRole:
        'A2Z SOC stores org-scoped compliance_controls; GRC_Claw packs align with what the bridge returns from GET /api/grc/controls.',
    },
    cursor: {
      endpoint: '/api/frameworks',
      method: 'GET',
      auth: false,
      description: 'List all framework packs and controls.',
      agentInstruction:
        'Fetch frameworks to resolve control IDs before calling ingest or agent tools that reference iso-* or nist-* codes.',
    },
  },
  ingest: {
    id: 'ingest',
    title: 'SIEM & cloud alert ingest',
    subtitle:
      'Normalize Wazuh, Suricata, Snort, Elastic, UFW, and AWS/Azure/GCP security signals into canonical GRC events.',
    explain: {
      what: 'Ingest accepts raw vendor JSON and returns a canonical security event plus complianceImpact — which controls are affected.',
      why: 'Continuous control monitoring requires one event schema across OSS SIEM, IDS/IPS, firewalls, and multi-cloud alerts.',
      how: [
        'Pick OSS or Cloud tab, then select the source_system that matches your payload shape.',
        'Edit the JSON sample or paste a live alert from your SIEM.',
        'POST normalize — review eventType, severity, and complianceImpact.controlIds.',
        'In production, A2Z SOC receives mapped events via the bridge automatically.',
      ],
      a2zRole:
        'Each normalized event is mapped through mapSecurityEventToControls() and can be pushed to A2Z SOC security_events and analyst queues.',
    },
    cursor: {
      endpoint: '/api/ingest/normalize',
      method: 'POST',
      auth: true,
      description: 'Normalize a vendor payload to canonical event + compliance impact.',
      exampleBody: '{"source":"suricata","tenantId":1,"payload":{"alert":{"severity":1},"src_ip":"10.0.0.1"}}',
      agentInstruction:
        'Always set source to a known ingest source, tenantId from settings, and valid vendor JSON in payload. Read complianceImpact from the response.',
    },
  },
  agent: {
    id: 'agent',
    title: 'Agent runtime & exec policy',
    subtitle:
      'Policy-gated tool invocation — read, write, and destructive tiers with approvals, idempotency, and full audit trail.',
    explain: {
      what: 'The agent runtime executes tools through ExecPolicy. Read tools auto-run; write needs idempotency; destructive needs approvalToken.',
      why: 'Agentic AI in GRC must not bypass human gates for SOAR playbooks, firewall changes, or evidence writes.',
      how: [
        'Select a tool and review its tier badge.',
        'Provide sessionId for audit correlation.',
        'For write tools, set a unique idempotencyKey.',
        'For destructive tools (soar.run_playbook, firewall.apply_rule), supply approvalToken.',
      ],
      a2zRole:
        'Tools like soc.query_events and grc.list_controls call the A2Z bridge when A2Z_SOC_MODE=private — same tenant scope as your SOC workspace.',
    },
    cursor: {
      endpoint: '/api/agent/invoke',
      method: 'POST',
      auth: true,
      description: 'Invoke a gated agent tool with optional approval and idempotency.',
      exampleBody:
        '{"sessionId":"cursor-auto","tool":"grc.list_controls","args":{"tenantId":1}}',
      agentInstruction:
        'Never call destructive tools without explicit user approval and approvalToken. Prefer read-tier tools first. Check decision.allowed in the response.',
    },
  },
  aims: {
    id: 'aims',
    title: 'ISO/IEC 42001 AIMS',
    subtitle:
      'AI Management System alignment — vendor gap matrix and technical controls for Anthropic, OpenAI, Cursor, and OpenClaw.',
    explain: {
      what: 'AIMS APIs expose ISO 42001 clause mapping, technical controls tied to GRC_Claw components, and vendor-specific AI governance gaps.',
      why: 'Regulated orgs adopting agentic AI need documented gaps against ISO 42001 before procurement or deployment.',
      how: [
        'Vendor gaps tab — compare AI vendor posture across critical/high findings.',
        'Filter by vendor (including Cursor) for supply-chain reviews.',
        'Technical controls tab — scope template, clauses 4–10, and TC-* mappings.',
      ],
      a2zRole:
        'AIMS scope references a2z-soc.com as the production SOC anchor; trust badge reflects continuous compliance posture on A2Z SOC.',
    },
    cursor: {
      endpoint: '/api/aims/vendor-gaps',
      method: 'GET',
      auth: false,
      description: 'Vendor gap summary and details; optional ?vendor=cursor filter.',
      agentInstruction:
        'Use vendor-gaps for AI vendor due diligence. Use /api/aims/technical-controls for clause-to-component mapping in audit writeups.',
    },
  },
  connectors: {
    id: 'connectors',
    title: 'BYOC — LLM & MCP connectors',
    subtitle:
      'Bring your own model providers and MCP servers — registered on the gateway and gated by the same exec policy as built-in tools.',
    explain: {
      what: 'BYOC lets you attach OpenAI, Anthropic, Ollama LLMs and MCP servers without forking GRC_Claw. Tools appear in agent policy after reload.',
      why: 'Enterprises keep API keys and MCP endpoints in their environment while still enforcing read/write/destructive tiers.',
      how: [
        'Configure GRC_CLAW_LLM_* and GRC_CLAW_MCP_* env vars on the gateway.',
        'Reload connectors after env changes.',
        'Test LLM chat and MCP tool listing from this page.',
        'Agent invoke can dispatch connector tools when registered.',
      ],
      a2zRole:
        'Cursor Auto Mode can call MCP tools exposed here while GRC_Claw enforces policy — pair with A2Z SOC for production SIEM context.',
    },
    cursor: {
      endpoint: '/api/connectors',
      method: 'GET',
      auth: false,
      description: 'List registered LLM and MCP connectors.',
      agentInstruction:
        'List connectors first. For MCP calls use POST /api/connectors/mcp/:id/call with {name, arguments}. For LLM use POST /api/connectors/llm/:id/chat.',
    },
  },
  settings: {
    id: 'settings',
    title: 'Console & integration settings',
    subtitle:
      'Gateway auth, A2Z SOC trust profile, tenant scope, and Cursor Auto Mode — machine-readable API access for agents.',
    explain: {
      what: 'Settings persist locally: gateway token, base URL, tenant ID, A2Z trust tenant for the badge, and whether Cursor Auto panels show on each page.',
      why: 'Operators and Cursor agents share the same gateway — token and tenant must match your Private A2Z SOC deployment.',
      how: [
        'Set X-GRC-Claw-Token to match GRC_CLAW_GATEWAY_TOKEN.',
        'Enable Cursor Auto Mode to show agent API hints on every page.',
        'Configure A2Z trust tenant ID for the Secured by A2Z SOC badge.',
        'Test /health and WebSocket connect handshake.',
      ],
      a2zRole:
        'Point A2Z_SOC_BASE_URL at your Private A2Z SOC instance on the gateway host; the console badge links to your public trust profile.',
    },
    cursor: {
      endpoint: '/health',
      method: 'GET',
      auth: false,
      description: 'Verify connectivity after updating settings.',
      agentInstruction:
        'Read settings from localStorage key grc-claw-console-settings. Use X-GRC-Claw-Token header on all authenticated routes. See /llms.txt for full API map.',
    },
  },
};
