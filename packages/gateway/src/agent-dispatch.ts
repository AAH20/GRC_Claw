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
    tool.startsWith('chronicle.') ||
    tool.startsWith('uas.') ||
    tool.startsWith('cuas.') ||
    tool.startsWith('cmmc.')
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
    case 'uas.validate_telemetry': {
      const droneId = String(args.droneId ?? 'unknown-uas');
      const packets = (args.telemetryStream as Array<any>) ?? [];
      const issues: string[] = [];
      let verifiedPacketsCount = 0;

      for (const packet of packets) {
        verifiedPacketsCount++;
        if (packet.signatureEnabled !== true) {
          issues.push(`Packet ${verifiedPacketsCount}: MAVLink v2 cryptographic signing disabled`);
        }
        if (packet.firmwareHash && packet.firmwareHash !== '0xPX4v1_14') {
          issues.push(`Packet ${verifiedPacketsCount}: Firmware mismatch anomaly detected (${packet.firmwareHash})`);
        }
        if (packet.flightMode === 'UNAUTHORIZED_OFFBOARD') {
          issues.push(`Packet ${verifiedPacketsCount}: Unauthorized offboard flight mode control command override`);
        }
      }

      const complianceStatus = issues.length === 0 ? 'COMPLIANT' : 'NON_COMPLIANT';
      return {
        ok: true,
        droneId,
        complianceStatus,
        issues,
        verifiedPacketsCount,
        timestamp: new Date().toISOString()
      };
    }
    case 'cuas.audit_hardware_status': {
      const stationId = String(args.stationId ?? 'c-uas-edge-station');
      const jammingActive = !!args.jammingArrayActive;
      const energyLimitKw = Number(args.directedEnergyLimitKw ?? 0);
      const rfScanMhz = Number(args.rfScanSpanMhz ?? 0);

      const dewSafeStatus = energyLimitKw <= 50 ? 'SAFE' : 'EXCEEDED';
      const rfSpectrumStatus = rfScanMhz >= 400 && rfScanMhz <= 6000 ? 'AUTHORIZED' : 'UNAUTHORIZED';

      return {
        ok: true,
        stationId,
        jammingActive,
        directedEnergyLimitKw: energyLimitKw,
        dewSafeStatus,
        rfSpectrumStatus,
        complianceStatus: (dewSafeStatus === 'SAFE' && rfSpectrumStatus === 'AUTHORIZED') ? 'COMPLIANT' : 'NON_COMPLIANT',
        auditTimestamp: new Date().toISOString()
      };
    }
    case 'cmmc.validate_system_boundary': {
      const baseline = (args.systemBaseline as Record<string, any>) ?? {};
      const passedControls: string[] = [];
      const failedControls: string[] = [];

      if (baseline.mfaEnabled === true) {
        passedControls.push('IA.L1-3.5.1 (MFA enabled)');
      } else {
        failedControls.push('IA.L1-3.5.1 (MFA disabled)');
      }

      if (typeof baseline.sessionTimeoutSeconds === 'number' && baseline.sessionTimeoutSeconds <= 900) {
        passedControls.push('AC.L2-3.1.11 (Session timeout <= 15m)');
      } else {
        failedControls.push('AC.L2-3.1.11 (Session timeout exceeds 15m or not configured)');
      }

      if (baseline.remoteAccessEncrypted === true) {
        passedControls.push('AC.L2-3.1.13 (Remote access encryption enforced)');
      } else {
        failedControls.push('AC.L2-3.1.13 (Remote access encryption disabled)');
      }

      if (baseline.auditLogsForwarded === true) {
        passedControls.push('AU.L2-3.3.1 (Audit log forwarding active)');
      } else {
        failedControls.push('AU.L2-3.3.1 (Audit log forwarding inactive)');
      }

      const complianceStatus = failedControls.length === 0 ? 'COMPLIANT' : 'NON_COMPLIANT';
      return {
        ok: true,
        complianceStatus,
        passedControls,
        failedControls,
        timestamp: new Date().toISOString()
      };
    }
    case 'cmmc.generate_audit_evidence': {
      const logs = (args.sessionLogs as Array<any>) ?? [];
      const sods = (args.sodViolations as Array<any>) ?? [];
      const payloadString = JSON.stringify({ logs, sods });
      
      // Simple hash generation for mock purposes
      let hash = 0;
      for (let i = 0; i < payloadString.length; i++) {
        hash = (hash << 5) - hash + payloadString.charCodeAt(i);
        hash = hash & hash;
      }
      const evidenceHash = 'sha256-' + Math.abs(hash).toString(16).padEnd(8, '0') + 'f7b3c2d4a1';
      const signature = `grc_claw_sig_0x${evidenceHash.slice(7)}889acde1`;

      return {
        ok: true,
        evidenceHash,
        signature,
        signedAt: new Date().toISOString(),
        itemsHashed: logs.length + sods.length
      };
    }
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
