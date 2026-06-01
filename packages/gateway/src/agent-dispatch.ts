import type { A2ZSocConnector } from '@grc-claw/a2z-connector';
import { listClauseMap, listTechnicalControls, listVendorGaps } from '@grc-claw/aims';
import type { EvidenceStore } from '@grc-claw/evidence';
import { listFrameworkPacks } from '@grc-claw/frameworks';
import {
  dispatchConnectorTool,
  isConnectorTool,
  type ConnectorRegistry,
} from '@grc-claw/connectors';
import { dispatchClawTool, isClawTool, type ClawDispatchContext } from '@grc-claw/skill-executor';

export function isBuiltinGrcTool(tool: string): boolean {
  return (
    tool.startsWith('grc.') ||
    tool.startsWith('evidence.') ||
    tool.startsWith('soc.') ||
    tool.startsWith('control.') ||
    tool.startsWith('soar.') ||
    tool.startsWith('firewall.') ||
    tool.startsWith('sentinel.') ||
    tool.startsWith('aws.') ||
    tool.startsWith('chronicle.')
  );
}

export async function dispatchBuiltinGrcTool(
  tool: string,
  args: Record<string, unknown>,
  deps: { evidence: EvidenceStore; a2z: A2ZSocConnector }
): Promise<Record<string, unknown>> {
  const tenantId = Number(args.tenantId ?? 1);

  switch (tool) {
    case 'grc.list_controls': {
      const packs = listFrameworkPacks();
      return {
        tenantId,
        packs: packs.map((p) => ({
          code: p.code,
          name: p.name,
          controlCount: p.controls.length,
        })),
        mode: process.env.A2Z_SOC_MODE ?? 'demo',
      };
    }
    case 'grc.get_compliance_score':
      return {
        tenantId,
        score: 0.86,
        trend: 'stable',
        evaluatedAt: new Date().toISOString(),
        mode: 'demo',
      };
    case 'evidence.read': {
      const evidenceId = String(args.evidenceId ?? '');
      const items = deps.evidence.listByControl(evidenceId);
      return { evidenceId, items, count: items.length };
    }
    case 'soc.query_events':
      return {
        tenantId,
        events: [],
        note: 'Use POST /api/ingest/normalize or A2Z sync for live events; demo query stub.',
        limit: Number(args.limit ?? 10),
      };
    case 'control.update_status':
      return {
        ok: true,
        controlId: args.controlId,
        status: args.status,
        tenantId,
        mode: 'demo',
      };
    case 'evidence.attach':
      return { ok: true, attached: true, tenantId, mode: 'demo' };
    case 'soar.run_playbook':
    case 'firewall.apply_rule':
    case 'sentinel.run_playbook':
    case 'chronicle.soar.run_playbook':
      return { ok: true, executed: true, tool, mode: 'demo', argsKeys: Object.keys(args) };
    case 'sentinel.get_incident':
      return { incidentId: args.incidentId ?? 'demo', status: 'New', severity: 'High' };
    case 'aws.guardduty.list_findings':
      return { findings: [], region: args.region ?? 'us-east-1', mode: 'demo' };
    default:
      return { ok: false, error: 'builtin_tool_stub', tool };
  }
}

export async function dispatchAgentTool(
  tool: string,
  args: Record<string, unknown>,
  deps: {
    registry: ConnectorRegistry;
    evidence: EvidenceStore;
    a2z: A2ZSocConnector;
    claw: ClawDispatchContext;
  }
): Promise<Record<string, unknown>> {
  if (isClawTool(tool)) {
    return dispatchClawTool(tool, args, deps.claw);
  }
  if (isConnectorTool(tool)) {
    const result = await dispatchConnectorTool(deps.registry, tool, args);
    return result.output ?? { kind: result.kind };
  }
  if (isBuiltinGrcTool(tool)) {
    if (tool === 'grc.list_controls' && args.includeAims === true) {
      const base = await dispatchBuiltinGrcTool(tool, args, deps);
      return {
        ...base,
        aims: {
          vendorGaps: listVendorGaps(),
          technicalControls: listTechnicalControls(),
          clauses: listClauseMap(),
        },
      };
    }
    return dispatchBuiltinGrcTool(tool, args, deps);
  }
  return { ok: false, error: 'unknown_tool', tool };
}
