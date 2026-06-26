import type { SecurityGraph, SecurityNode, SecurityEdge } from './index.js';

export interface FrameworkPack {
  code: string;
  name: string;
  version: string;
  controls: { id: string; controlCode: string; title: string; frameworkCode: string; domain?: string }[];
}

const INFRASTRUCTURE_TARGETS = [
  'prod-auth-db', 'core-api-gateway', 'aws-s3-compliance', 'k8s-cluster-prod',
  'ci-runner-pool', 'vault-secrets', 'redis-session-cache', 'cdn-edge-proxy',
  'postgres-primary', 'elasticsearch-logs', 'sqs-event-queue', 'ec2-bastion-host',
];

const AGENT_DIDS = [
  'did:grc:agent-grc-auditor', 'did:grc:agent-compliance-scanner', 'did:grc:agent-evidence-collector',
  'did:grc:agent-incident-responder', 'did:grc:agent-policy-enforcer', 'did:grc:agent-risk-analyst',
  'did:grc:agent-soar-orchestrator', 'did:grc:agent-cloud-security', 'did:grc:agent-identity-mgr',
  'did:grc:agent-vuln-scanner', 'did:grc:agent-log-analyzer', 'did:grc:agent-crypto-guard',
];

const TOOL_IDS = [
  'tool-wazuh-siem', 'tool-suricata-ids', 'tool-elastic-stack', 'tool-snort-ips',
  'tool-aws-guardduty', 'tool-azure-sentinel', 'tool-gcp-chronicle',
  'tool-vault-secrets', 'tool-terraform-iac', 'tool-trivy-scanner',
  'tool-caldera-redteam', 'tool-openvas-vuln', 'tool-splunk-hec',
];

const POLICY_IDS = [
  'policy-acceptable-use', 'policy-access-control', 'policy-data-classification',
  'policy-incident-response', 'policy-bcp-dr', 'policy-change-management',
  'policy-vendor-risk', 'policy-encryption-standards', 'policy-logging-monitoring',
  'policy-remote-access', 'policy-mobile-device', 'policy-physical-security',
];

function pick<T>(arr: T[], i: number): T {
  return arr[i % arr.length]!;
}

function riskFromIndex(i: number, max = 100): number {
  return ((i * 7 + 13) % max);
}

export class SecurityGraphSeeder {
  constructor(private graph: SecurityGraph) {}

  seedFromFrameworks(frameworks: FrameworkPack[]): void {
    const frameworkNodeIds: string[] = [];

    for (const pack of frameworks) {
      const fwId = `fw-${pack.code}`;
      this.graph.addNode({
        id: fwId, type: 'framework', name: pack.name,
        riskScore: 5,
        properties: { code: pack.code, version: pack.version, controlCount: pack.controls.length },
        tags: [pack.code],
      });
      frameworkNodeIds.push(fwId);

      for (let ci = 0; ci < pack.controls.length; ci++) {
        const ctrl = pack.controls[ci]!;
        const ctrlId = `ctrl-${ctrl.id}`;
        this.graph.addNode({
          id: ctrlId, type: 'control', name: ctrl.title,
          riskScore: riskFromIndex(ci + frameworks.indexOf(pack) * 17),
          properties: { controlCode: ctrl.controlCode, domain: ctrl.domain ?? 'unknown', frameworkCode: ctrl.frameworkCode },
          tags: [pack.code, ctrl.domain ?? 'general'],
        });

        this.graph.addEdge({
          source: fwId, target: ctrlId, relationship: 'depends_on',
          metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.9, details: `Framework ${pack.code} owns control ${ctrl.controlCode}` },
        });

        if (ci % 3 === 0) {
          const evidenceId = `ev-${ctrl.id}-evidence`;
          this.graph.addNode({
            id: evidenceId, type: 'evidence', name: `Evidence for ${ctrl.controlCode}`,
            riskScore: Math.max(0, 40 - riskFromIndex(ci)),
            properties: { controlId: ctrlId, sha256: `sha256_evidence_${ctrl.id}`, status: ci % 5 === 0 ? 'pending' : 'collected' },
            tags: [pack.code, 'evidence'],
          });
          this.graph.addEdge({
            source: evidenceId, target: ctrlId, relationship: 'produced',
            metadata: { timestamp: new Date().toISOString(), result: ci % 5 === 0 ? 'pending' : 'pass', confidence: 0.85, details: `Evidence produced for control ${ctrl.controlCode}` },
          });
        }

        if (ci % 4 === 0) {
          const riskId = `risk-${ctrl.id}-risk`;
          this.graph.addNode({
            id: riskId, type: 'alert', name: `Risk: ${ctrl.title}`,
            riskScore: riskFromIndex(ci + 50),
            properties: { controlId: ctrlId, severity: ci % 3 === 0 ? 'high' : 'medium', description: `Compliance risk for ${ctrl.controlCode}` },
            tags: [pack.code, 'risk'],
          });
          this.graph.addEdge({
            source: riskId, target: ctrlId, relationship: 'violated',
            metadata: { timestamp: new Date().toISOString(), result: 'fail', confidence: 0.7, details: `Risk detected against control ${ctrl.controlCode}` },
          });
        }
      }
    }

    for (let i = 0; i < INFRASTRUCTURE_TARGETS.length; i++) {
      this.graph.addNode({
        id: `infra-${INFRASTRUCTURE_TARGETS[i]}`, type: 'infrastructure', name: INFRASTRUCTURE_TARGETS[i]!,
        riskScore: riskFromIndex(i + 100),
        properties: { host: INFRASTRUCTURE_TARGETS[i], environment: 'production', region: i % 2 === 0 ? 'us-east-1' : 'eu-west-1' },
        tags: ['infrastructure', 'production'],
      });
    }

    for (let i = 0; i < AGENT_DIDS.length; i++) {
      const agentId = AGENT_DIDS[i]!;
      this.graph.addNode({
        id: agentId, type: 'agent', name: agentId.split(':').pop()!,
        riskScore: riskFromIndex(i + 200),
        properties: { did: agentId, role: i % 3 === 0 ? 'admin' : 'operator', tenantScope: ['1'] },
        tags: ['agent', 'did:grc'],
      });
    }

    for (let i = 0; i < TOOL_IDS.length; i++) {
      this.graph.addNode({
        id: TOOL_IDS[i]!, type: 'tool', name: TOOL_IDS[i]!,
        riskScore: riskFromIndex(i + 300),
        properties: { provider: i % 3 === 0 ? 'aws' : i % 3 === 1 ? 'oss' : 'azure', tier: i % 4 === 0 ? 'destructive' : 'read' },
        tags: ['tool'],
      });
    }

    for (let i = 0; i < POLICY_IDS.length; i++) {
      this.graph.addNode({
        id: POLICY_IDS[i]!, type: 'policy', name: POLICY_IDS[i]!,
        riskScore: riskFromIndex(i + 400) % 30,
        properties: { policyType: 'organizational', version: '2026.1' },
        tags: ['policy'],
      });
    }

    this.seedEdges(frameworkNodeIds);
  }

  private seedEdges(frameworkNodeIds: string[]): void {
    const allControlNodes = this.graph.getNodesByType('control');
    const allAgentNodes = this.graph.getNodesByType('agent');
    const allToolNodes = this.graph.getNodesByType('tool');
    const allInfraNodes = this.graph.getNodesByType('infrastructure');
    const allPolicyNodes = this.graph.getNodesByType('policy');
    const allRiskNodes = this.graph.getNodesByType('alert');

    for (let ai = 0; ai < allAgentNodes.length; ai++) {
      const agent = allAgentNodes[ai]!;
      const toolCount = 2 + (ai % 3);
      for (let t = 0; t < toolCount; t++) {
        const tool = pick(allToolNodes, ai * 3 + t);
        this.graph.addEdge({
          source: agent.id, target: tool.id, relationship: 'invoked',
          metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.95, details: `Agent ${agent.name} invokes ${tool.name}` },
        });
      }

      const certCount = 1 + (ai % 4);
      for (let c = 0; c < certCount; c++) {
        const fw = pick(frameworkNodeIds, ai + c);
        this.graph.addEdge({
          source: agent.id, target: fw, relationship: 'certified_by',
          metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.88, details: `Agent ${agent.name} certified for framework` },
        });
      }
    }

    for (let ci = 0; ci < allControlNodes.length; ci++) {
      const ctrl = allControlNodes[ci]!;
      if (ci % 2 === 0 && allControlNodes.length > ci + 1) {
        const dep = allControlNodes[ci + 1]!;
        this.graph.addEdge({
          source: ctrl.id, target: dep.id, relationship: 'depends_on',
          metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.82, details: 'Control dependency chain' },
        });
      }

      if (ci % 5 === 0) {
        const infra = pick(allInfraNodes, ci);
        this.graph.addEdge({
          source: ctrl.id, target: infra.id, relationship: 'scoped_to',
          metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.75, details: `Control scoped to infrastructure ${infra.name}` },
        });
      }

      if (ci % 3 === 0) {
        const policy = pick(allPolicyNodes, ci);
        this.graph.addEdge({
          source: policy.id, target: ctrl.id, relationship: 'mitigates',
          metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.8, details: `Policy mitigates risk for control` },
        });
      }

      if (ci % 7 === 0 && allInfraNodes.length > 0) {
        const infra = pick(allInfraNodes, ci);
        this.graph.addEdge({
          source: infra.id, target: ctrl.id, relationship: 'owns',
          metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.7, details: `Infrastructure ${infra.name} implements control` },
        });
      }
    }

    for (let ri = 0; ri < allRiskNodes.length; ri++) {
      const risk = allRiskNodes[ri]!;
      if (ri % 3 === 0) {
        const agent = pick(allAgentNodes, ri);
        this.graph.addEdge({
          source: agent.id, target: risk.id, relationship: 'detected',
          metadata: { timestamp: new Date().toISOString(), result: 'fail', confidence: 0.6, details: 'Agent detected risk event' },
        });
      }
      if (ri % 4 === 0) {
        const infra = pick(allInfraNodes, ri);
        this.graph.addEdge({
          source: risk.id, target: infra.id, relationship: 'violated',
          metadata: { timestamp: new Date().toISOString(), result: 'fail', confidence: 0.65, details: 'Risk violates infrastructure boundary' },
        });
      }
    }
  }

  seedAttackPaths(): void {
    const agents = this.graph.getNodesByType('agent');
    const tools = this.graph.getNodesByType('tool');
    const infra = this.graph.getNodesByType('infrastructure');
    const controls = this.graph.getNodesByType('control');

    const entryPoints = agents.slice(0, 5);
    for (const entry of entryPoints) {
      const tool1 = tools[0];
      const tool2 = tools[1];
      const targetInfra = infra[0];
      const targetControl = controls[0];

      if (tool1) {
        this.graph.addEdge({
          source: entry.id, target: tool1.id, relationship: 'invoked',
          metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 1.0, details: 'Attack path: initial credential compromise via tool invocation' },
        });
      }
      if (tool1 && tool2) {
        this.graph.addEdge({
          source: tool1.id, target: tool2.id, relationship: 'depends_on',
          metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.8, details: 'Attack path: lateral movement through tool chain' },
        });
      }
      if (tool2 && targetInfra) {
        this.graph.addEdge({
          source: tool2.id, target: targetInfra.id, relationship: 'scoped_to',
          metadata: { timestamp: new Date().toISOString(), result: 'fail', confidence: 0.7, details: 'Attack path: infrastructure compromise via lateral movement' },
        });
      }
      if (targetInfra && targetControl) {
        this.graph.addEdge({
          source: targetInfra.id, target: targetControl.id, relationship: 'violated',
          metadata: { timestamp: new Date().toISOString(), result: 'fail', confidence: 0.6, details: 'Attack path: control bypass after infrastructure compromise' },
        });
      }
    }
  }

  seedRiskNetwork(): void {
    const agents = this.graph.getNodesByType('agent');
    const infra = this.graph.getNodesByType('infrastructure');
    const policies = this.graph.getNodesByType('policy');
    const controls = this.graph.getNodesByType('control');

    for (let i = 0; i < infra.length; i++) {
      const host = infra[i]!;
      const nextHost = infra[(i + 1) % infra.length];
      this.graph.addEdge({
        source: host.id, target: nextHost.id, relationship: 'depends_on',
        metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.75, details: `Network spread: ${host.name} -> ${nextHost.name}` },
      });
    }

    for (let i = 0; i < 6; i++) {
      const agent = agents[i % agents.length];
      const host = infra[i % infra.length];
      this.graph.addEdge({
        source: agent.id, target: host.id, relationship: 'authenticated_by',
        metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.85, details: 'Agent authenticated to host' },
      });
    }

    for (let i = 0; i < Math.min(policies.length, controls.length); i++) {
      const policy = policies[i]!;
      const control = controls[i * 7 % controls.length]!;
      this.graph.addEdge({
        source: policy.id, target: control.id, relationship: 'mitigates',
        metadata: { timestamp: new Date().toISOString(), result: 'pass', confidence: 0.78, details: 'Policy mitigates control risk' },
      });
    }
  }
}
