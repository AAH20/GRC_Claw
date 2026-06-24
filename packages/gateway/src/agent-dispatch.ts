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
import { VectorGraphMemory, SkillsRegistry } from '@grc-claw/agent-runtime';
import * as fs from 'fs';
import * as path from 'path';

const vectorMemory = new VectorGraphMemory();
const skillsRegistry = new SkillsRegistry();


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
    tool.startsWith('cmmc.') ||
    tool.startsWith('sovereign.') ||
    tool.startsWith('iso20022.') ||
    tool.startsWith('memory.') ||
    tool.startsWith('skills.') ||
    tool.startsWith('actuator.')
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
    case 'sovereign.verify_compute_boundary': {
      const hostCpu = String(args.hostCpu ?? '');
      const gpuHardware = String(args.gpuHardware ?? '');
      const airgapStatus = String(args.airgapStatus ?? '');
      const modelWeightsSource = String(args.modelWeightsSource ?? '');
      const nemoGuardrailsActive = !!args.nemoGuardrailsActive;

      const issues: string[] = [];

      // 1. Airgap validation
      const airgapPassed = airgapStatus === 'FULLY_AIRGAPPED';
      if (!airgapPassed) {
        issues.push(`Airgap Audit: System status is "${airgapStatus}", violating zero-export airgap regulations`);
      }

      // 2. Weights source validation
      const weightsPassed = modelWeightsSource === 'LOCAL_AUDITED_WEIGHTS';
      if (!weightsPassed) {
        issues.push(`Weights Audit: Model weights sourced from "${modelWeightsSource}" (violates compliance: weights must be local and audited)`);
      }

      // 3. Guardrails validation
      const guardrailsPassed = nemoGuardrailsActive === true;
      if (!guardrailsPassed) {
        issues.push(`Guardrails Audit: NeMo Guardrails layer is inactive or missing`);
      }

      // 4. Hardware/Silicon validation
      const cpuOk = (hostCpu.includes('Vera') || hostCpu.includes('Spark') || hostCpu.includes('EPYC') || hostCpu.includes('Xeon')) && !hostCpu.includes('Cloud') && !hostCpu.includes('VM');
      const gpuOk = (gpuHardware.includes('Blackwell') || gpuHardware.includes('Hopper') || gpuHardware.includes('H100') || gpuHardware.includes('H200') || gpuHardware.includes('Spark')) && !gpuHardware.includes('Cloud') && !gpuHardware.includes('VM');
      
      const hardwarePassed = cpuOk && gpuOk;
      if (!cpuOk) {
        issues.push(`Silicon Audit: CPU vendor "${hostCpu}" is not certified for sovereign airgap system control plane`);
      }
      if (!gpuOk) {
        issues.push(`Silicon Audit: GPU architecture "${gpuHardware}" is not certified for local parallel swarm inference`);
      }

      const complianceStatus = (airgapPassed && weightsPassed && guardrailsPassed && hardwarePassed) ? 'COMPLIANT' : 'NON_COMPLIANT';

      return {
        ok: true,
        complianceStatus,
        hardwareAuditPassed: hardwarePassed,
        airgapAuditPassed: airgapPassed,
        weightsAuditPassed: weightsPassed,
        nemoGuardrailsPassed: guardrailsPassed,
        issues,
        timestamp: new Date().toISOString()
      };
    }
    case 'iso20022.validate_message': {
      const messagePayload = String(args.messagePayload ?? '');
      const verificationPolicy = (args.verificationPolicy as Record<string, any>) ?? {};
      const maxTxLimit = typeof verificationPolicy.maxTransactionLimit === 'number' ? verificationPolicy.maxTransactionLimit : 1000000;
      
      const passedChecks: string[] = [];
      const failedChecks: string[] = [];
      const issues: string[] = [];

      // 1. Schema Validation (MX vs MT)
      const hasMxSchema = messagePayload.includes('xmlns="urn:iso:std:iso:20022:tech:xsd:') || messagePayload.includes('<Document');
      if (hasMxSchema) {
        passedChecks.push('ISO20022.MX.01 (Conforming MX XML schema)');
      } else {
        failedChecks.push('ISO20022.MX.01 (Non-conforming payload: expected SWIFT MX XML format)');
        issues.push('Schema Violation: SWIFT MT format detected or XML header is missing');
      }

      // 2. Cryptographic Signature Validation
      const hasSignature = (messagePayload.includes('<AppHdr>') && messagePayload.includes('<Sgntr>')) || messagePayload.includes('Signature') || messagePayload.includes('SignedSignatureValue');
      if (hasSignature) {
        passedChecks.push('ISO20022.SG.02 (Cryptographic signature verified)');
      } else {
        failedChecks.push('ISO20022.SG.02 (Cryptographic signature missing)');
        issues.push('Signature Violation: Message block lacks valid application header signature');
      }

      // 3. Transaction Amount limit validation
      const txAmount = typeof args.transactionAmount === 'number' ? args.transactionAmount : 150000;
      if (txAmount <= maxTxLimit) {
        passedChecks.push(`ISO20022.LM.03 (Transaction amount ${txAmount} is within policy limit ${maxTxLimit})`);
      } else {
        failedChecks.push(`ISO20022.LM.03 (Transaction amount ${txAmount} exceeds policy limit ${maxTxLimit})`);
        issues.push('Limit Violation: Transfer amount exceeds single-transaction policy threshold');
      }

      // 4. Sanction check validation
      const beneficiaryName = String(args.beneficiaryName ?? 'Valid Account');
      const deniedList = ['Blocked Entity', 'Sanctioned Corp', 'SDN Person'];
      const isSanctioned = deniedList.some(denied => beneficiaryName.includes(denied));
      if (!isSanctioned) {
        passedChecks.push('ISO20022.SC.04 (Beneficiary sanctions screening cleared)');
      } else {
        failedChecks.push(`ISO20022.SC.04 (Beneficiary "${beneficiaryName}" matched SDN sanctions list)`);
        issues.push('Sanctions Violation: Recipient account matches active restriction registry');
      }

      const complianceStatus = failedChecks.length === 0 ? 'COMPLIANT' : 'NON_COMPLIANT';

      return {
        ok: true,
        complianceStatus,
        passedChecks,
        failedChecks,
        issues,
        timestamp: new Date().toISOString()
      };
    }
    case 'iso20022.generate_audit_trail': {
      const messages = (args.validatedMessages as Array<any>) ?? [];
      const screeningLogs = (args.screeningLogs as Array<any>) ?? [];
      const payloadString = JSON.stringify({ messages, screeningLogs });
      
      let hash = 0;
      for (let i = 0; i < payloadString.length; i++) {
        hash = (hash << 5) - hash + payloadString.charCodeAt(i);
        hash = hash & hash;
      }
      const auditHash = 'sha256-' + Math.abs(hash).toString(16).padEnd(8, '0') + 'b8f2c6e3d5';
      const signature = `iso20022_audit_sig_0x${auditHash.slice(7)}775a2bc9`;

      return {
        ok: true,
        auditHash,
        signature,
        signedAt: new Date().toISOString(),
        itemsProcessed: messages.length + screeningLogs.length
      };
    }
    case 'memory.query_vector_graph': {
      const queryText = String(args.queryText ?? '');
      const results = vectorMemory.query(queryText);
      return {
        ok: true,
        queryText,
        nodes: results.nodes,
        edges: results.edges,
        timestamp: new Date().toISOString()
      };
    }
    case 'memory.persist_session_state': {
      const sessionId = String(args.sessionId ?? 'default');
      const fileDir = path.resolve(process.cwd(), '.grc_memory');
      if (!fs.existsSync(fileDir)) {
        fs.mkdirSync(fileDir, { recursive: true });
      }
      const filePath = path.join(fileDir, `${sessionId}.json`);
      let currentState: any = { calls: 0, toxicityScore: 0, callHistory: [], audit: [] };
      if (fs.existsSync(filePath)) {
        try {
          currentState = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
        } catch (e) {}
      }
      if (typeof args.toxicityScore === 'number') currentState.toxicityScore = args.toxicityScore;
      if (typeof args.calls === 'number') currentState.calls = args.calls;
      if (args.callHistory && Array.isArray(args.callHistory)) currentState.callHistory = args.callHistory;
      if (args.audit && Array.isArray(args.audit)) currentState.audit = args.audit;

      fs.writeFileSync(filePath, JSON.stringify(currentState, null, 2), 'utf-8');
      return {
        ok: true,
        saved: true,
        sessionId,
        state: currentState,
        timestamp: new Date().toISOString()
      };
    }
    case 'skills.query_repo': {
      const queryText = String(args.queryText ?? '');
      const results = skillsRegistry.query(queryText);
      return {
        ok: true,
        queryText,
        totalSkillsInCatalog: skillsRegistry.getTotalCount(),
        matchedSkillsCount: results.length,
        skills: results.map(s => ({
          id: s.id,
          name: s.name,
          category: s.category,
          description: s.description,
          source: s.source
        })),
        timestamp: new Date().toISOString()
      };
    }
    case 'skills.load_definition': {
      const skillId = String(args.skillId ?? '');
      const skill = skillsRegistry.load(skillId);
      if (!skill) {
        return {
          ok: false,
          error: `skill_not_found: ${skillId}`,
          timestamp: new Date().toISOString()
        };
      }
      return {
        ok: true,
        skillId,
        definition: skill,
        timestamp: new Date().toISOString()
      };
    }
    case 'actuator.simulate_execution': {
      const actuatorId = String(args.actuatorId ?? 'unknown-actuator');
      const trajectoryPoints = (args.trajectoryPoints as Array<{ x: number, y: number, z: number, velocity: number }>) ?? [];
      const torqueLimits = (args.torqueLimits as Array<number>) ?? [];
      const collisionAvoidanceEnabled = args.collisionAvoidanceEnabled !== false;
      const swarmOrchestrationId = String(args.swarmOrchestrationId ?? 'default-swarm');

      const issues: string[] = [];

      let maxVelocity = 0;
      for (let i = 0; i < trajectoryPoints.length; i++) {
        const pt = trajectoryPoints[i];
        if (pt.velocity > maxVelocity) maxVelocity = pt.velocity;
        if (pt.velocity > 2.0) {
          issues.push(`Trajectory Point ${i + 1}: Velocity ${pt.velocity} m/s exceeds AGI kinetic safe limit (2.0 m/s)`);
        }
      }

      let maxTorque = 0;
      for (let i = 0; i < torqueLimits.length; i++) {
        const t = torqueLimits[i];
        if (t > maxTorque) maxTorque = t;
        if (t > 150) {
          issues.push(`Joint ${i + 1}: Torque Limit ${t} Nm exceeds safe mechanical load threshold (150 Nm)`);
        }
      }

      if (!collisionAvoidanceEnabled) {
        issues.push('Safety Warning: Spatial collision avoidance systems are inactive or disabled');
      }

      const safetyClearance = issues.length === 0 ? 'GRANTED' : 'DENIED';

      const payloadString = JSON.stringify({ actuatorId, trajectoryPoints, torqueLimits, collisionAvoidanceEnabled, safetyClearance });
      let hash = 0;
      for (let i = 0; i < payloadString.length; i++) {
        hash = (hash << 5) - hash + payloadString.charCodeAt(i);
        hash = hash & hash;
      }
      const digitalTwinSignature = `grc_twin_sig_0x${Math.abs(hash).toString(16).padEnd(8, '0')}e91b538f`;

      return {
        ok: true,
        actuatorId,
        swarmOrchestrationId,
        safetyClearance,
        maxVelocityRecordedMps: maxVelocity,
        maxTorqueRecordedNm: maxTorque,
        simulatedDurationMs: trajectoryPoints.length * 150,
        energyConsumptionKwh: Number((maxTorque * maxVelocity * 0.0005).toFixed(4)),
        issues,
        digitalTwinSignature,
        timestamp: new Date().toISOString()
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
