export type VendorId = 'anthropic' | 'openai' | 'cursor' | 'openclaw';

export interface VendorGapRow {
  vendor: VendorId;
  area: string;
  strength: string;
  gapTheme: string;
  mitigation: string;
  grcClawControlIds?: string[];
}

export const VENDOR_GAP_MATRIX: VendorGapRow[] = [
  {
    vendor: 'anthropic',
    area: 'Safety research',
    strength: 'RSP, model evaluations',
    gapTheme: 'Customer-operated AIMS boundary unclear',
    mitigation: 'Contractual scope + customer-side logging via gateway',
    grcClawControlIds: ['aims-a.10.1', 'aims-a.12.1'],
  },
  {
    vendor: 'anthropic',
    area: 'API usage',
    strength: 'Policies, rate limits',
    gapTheme: 'Agent tool chains not visible to customer AIMS',
    mitigation: 'Gateway mediates all tool calls',
    grcClawControlIds: ['aims-a.12.2'],
  },
  {
    vendor: 'openai',
    area: 'Policies',
    strength: 'Usage policies, preparedness',
    gapTheme: 'Autonomous agent loops without per-action approval',
    mitigation: 'Exec policy + max calls per turn',
    grcClawControlIds: ['aims-a.12.3', 'aims-a.14.1'],
  },
  {
    vendor: 'openai',
    area: 'Tools',
    strength: 'Function calling, assistants',
    gapTheme: 'Destructive partner actions in composite apps',
    mitigation: 'Tier destructive tools + idempotency',
    grcClawControlIds: ['aims-a.12.3'],
  },
  {
    vendor: 'cursor',
    area: 'Product',
    strength: 'IDE-integrated agents',
    gapTheme: 'AIMS scope: local index vs cloud model routing',
    mitigation: 'Document processing locations in SoA',
    grcClawControlIds: ['aims-a.7.1', 'aims-a.13.1'],
  },
  {
    vendor: 'cursor',
    area: 'Extensibility',
    strength: 'Skills, MCP, rules',
    gapTheme: 'Supply chain: third-party MCP servers',
    mitigation: 'Curated MCP registry + signing (customer policy)',
    grcClawControlIds: ['aims-a.9.1'],
  },
  {
    vendor: 'openclaw',
    area: 'Architecture',
    strength: 'Gateway daemon, pairing, skills',
    gapTheme: 'Deployer accountable for operator AIMS',
    mitigation: 'Hardening guide + npm run doctor',
    grcClawControlIds: ['aims-a.12.1'],
  },
  {
    vendor: 'openclaw',
    area: 'Security',
    strength: 'Public vulnerability research',
    gapTheme: 'Default localhost-trust configurations',
    mitigation: 'TLS, token auth, pairing for non-local',
    grcClawControlIds: ['aims-a.12.1', 'aims-a.12.2'],
  },
];

export function listVendorGaps(vendor?: VendorId): VendorGapRow[] {
  if (!vendor) return [...VENDOR_GAP_MATRIX];
  return VENDOR_GAP_MATRIX.filter((r) => r.vendor === vendor);
}

export function listVendorGapSummary(): { vendor: VendorId; strength: string; gapTheme: string }[] {
  const vendors: VendorId[] = ['anthropic', 'openai', 'cursor', 'openclaw'];
  return vendors.map((vendor) => {
    const rows = listVendorGaps(vendor);
    return {
      vendor,
      strength: rows.map((r) => r.area).join('; '),
      gapTheme: rows[0]?.gapTheme ?? '',
    };
  });
}
