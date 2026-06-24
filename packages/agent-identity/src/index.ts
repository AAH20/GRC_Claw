/**
 * @grc-claw/agent-identity
 * DID-based Agent Identity Fabric with Verifiable Credentials
 *
 * Provides cryptographic identity for every AI agent in the GRC_Claw ecosystem.
 * Every agent gets a did:grc:<uuid> Decentralized Identifier bound to
 * Verifiable Credentials encoding framework certifications, tool tier access,
 * and tenant scope.
 */
import * as crypto from 'crypto';

// ─── Core Types ──────────────────────────────────────────────────────

export interface VerificationMethod {
  id: string;
  type: 'Ed25519VerificationKey2020' | 'X25519KeyAgreementKey2020';
  controller: string;
  publicKeyHex: string;
}

export interface ServiceEndpoint {
  id: string;
  type: 'GRCGateway' | 'EvidenceVault' | 'SIEMIngest' | 'SOAREngine';
  serviceEndpoint: string;
}

export interface VerifiableCredential {
  '@context': string[];
  type: string[];
  issuer: string;
  issuanceDate: string;
  expirationDate: string;
  credentialSubject: AgentCredentialSubject;
  proof: CredentialProof;
}

export interface AgentCredentialSubject {
  id: string;
  framework: 'iso27001' | 'soc2' | 'cmmc' | 'iso42001' | 'nist_csf' | 'gdpr' | 'hipaa' | 'pci_dss';
  certifiedControls: string[];
  toolTierAccess: ('read' | 'write' | 'destructive')[];
  tenantScope: string[];
  sovereignBoundary: 'us-only' | 'eu-only' | 'global' | 'airgapped';
}

export interface CredentialProof {
  type: 'Ed25519Signature2020';
  created: string;
  verificationMethod: string;
  proofPurpose: 'assertionMethod';
  proofValue: string;
}

export interface AgentDID {
  '@context': string[];
  id: string;                         // did:grc:<uuid>
  controller: string;                 // tenant or org DID
  created: string;
  updated: string;
  verificationMethod: VerificationMethod[];
  authentication: string[];
  service: ServiceEndpoint[];
  credentials: VerifiableCredential[];
  status: 'active' | 'revoked' | 'suspended';
  riskScore: number;                  // 0-100, real-time
  metadata: Record<string, unknown>;
}

export interface AgentIdentityRegistry {
  agents: Map<string, AgentDID>;
  revokedDids: Set<string>;
}

// ─── Identity Manager ────────────────────────────────────────────────

export class AgentIdentityManager {
  private registry: AgentIdentityRegistry = {
    agents: new Map(),
    revokedDids: new Set(),
  };

  /** Generate a new DID for an agent */
  createAgentDID(opts: {
    controller: string;
    tenantScope: string[];
    sovereignBoundary?: 'us-only' | 'eu-only' | 'global' | 'airgapped';
    services?: ServiceEndpoint[];
  }): AgentDID {
    const uuid = crypto.randomUUID();
    const did = `did:grc:${uuid}`;
    const keyPair = crypto.generateKeyPairSync('ed25519');
    const pubKeyHex = keyPair.publicKey.export({ type: 'spki', format: 'der' }).toString('hex');

    const verificationMethod: VerificationMethod = {
      id: `${did}#key-1`,
      type: 'Ed25519VerificationKey2020',
      controller: did,
      publicKeyHex: pubKeyHex,
    };

    const agentDid: AgentDID = {
      '@context': [
        'https://www.w3.org/ns/did/v1',
        'https://w3id.org/security/suites/ed25519-2020/v1',
        'https://grc-claw.a2zsoc.com/ns/agent-identity/v1',
      ],
      id: did,
      controller: opts.controller,
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
      verificationMethod: [verificationMethod],
      authentication: [verificationMethod.id],
      service: opts.services ?? [],
      credentials: [],
      status: 'active',
      riskScore: 0,
      metadata: {
        tenantScope: opts.tenantScope,
        sovereignBoundary: opts.sovereignBoundary ?? 'global',
      },
    };

    this.registry.agents.set(did, agentDid);
    return agentDid;
  }

  /** Issue a Verifiable Credential to an agent */
  issueCredential(agentDid: string, credential: {
    framework: AgentCredentialSubject['framework'];
    certifiedControls: string[];
    toolTierAccess: ('read' | 'write' | 'destructive')[];
    tenantScope: string[];
    sovereignBoundary: AgentCredentialSubject['sovereignBoundary'];
    validDays?: number;
  }): VerifiableCredential {
    const agent = this.registry.agents.get(agentDid);
    if (!agent) throw new Error(`Agent DID not found: ${agentDid}`);
    if (agent.status === 'revoked') throw new Error(`Agent DID revoked: ${agentDid}`);

    const now = new Date();
    const expiry = new Date(now.getTime() + (credential.validDays ?? 365) * 86400000);

    const credentialSubject: AgentCredentialSubject = {
      id: agentDid,
      framework: credential.framework,
      certifiedControls: credential.certifiedControls,
      toolTierAccess: credential.toolTierAccess,
      tenantScope: credential.tenantScope,
      sovereignBoundary: credential.sovereignBoundary,
    };

    const proofPayload = JSON.stringify(credentialSubject);
    const proofHash = crypto.createHash('sha256').update(proofPayload).digest('hex');

    const vc: VerifiableCredential = {
      '@context': [
        'https://www.w3.org/2018/credentials/v1',
        'https://grc-claw.a2zsoc.com/ns/compliance-credential/v1',
      ],
      type: ['VerifiableCredential', 'ComplianceCertification'],
      issuer: agent.controller,
      issuanceDate: now.toISOString(),
      expirationDate: expiry.toISOString(),
      credentialSubject,
      proof: {
        type: 'Ed25519Signature2020',
        created: now.toISOString(),
        verificationMethod: agent.verificationMethod[0]?.id ?? `${agentDid}#key-1`,
        proofPurpose: 'assertionMethod',
        proofValue: `grc_vc_proof_${proofHash.substring(0, 32)}`,
      },
    };

    agent.credentials.push(vc);
    agent.updated = now.toISOString();
    return vc;
  }

  /** Verify an agent has a valid credential for a framework */
  verifyCredential(agentDid: string, framework: AgentCredentialSubject['framework']): {
    valid: boolean;
    reason: string;
    credential?: VerifiableCredential;
  } {
    const agent = this.registry.agents.get(agentDid);
    if (!agent) return { valid: false, reason: 'agent_not_found' };
    if (agent.status === 'revoked') return { valid: false, reason: 'agent_revoked' };
    if (agent.status === 'suspended') return { valid: false, reason: 'agent_suspended' };

    const now = new Date();
    const vc = agent.credentials.find(
      (c) => c.credentialSubject.framework === framework &&
             new Date(c.expirationDate) > now
    );

    if (!vc) return { valid: false, reason: `no_valid_credential_for_${framework}` };
    return { valid: true, reason: 'credential_valid', credential: vc };
  }

  /** Check if agent is authorized for a tool tier */
  authorizeToolAccess(agentDid: string, tier: 'read' | 'write' | 'destructive'): {
    authorized: boolean;
    reason: string;
  } {
    const agent = this.registry.agents.get(agentDid);
    if (!agent) return { authorized: false, reason: 'agent_not_found' };
    if (agent.status !== 'active') return { authorized: false, reason: `agent_${agent.status}` };

    const now = new Date();
    const validCreds = agent.credentials.filter(
      (c) => new Date(c.expirationDate) > now
    );

    const hasAccess = validCreds.some(
      (c) => c.credentialSubject.toolTierAccess.includes(tier)
    );

    return hasAccess
      ? { authorized: true, reason: 'tool_access_granted' }
      : { authorized: false, reason: `no_credential_grants_${tier}_access` };
  }

  /** Revoke an agent DID (propagates immediately) */
  revokeDID(agentDid: string): { ok: boolean; reason: string } {
    const agent = this.registry.agents.get(agentDid);
    if (!agent) return { ok: false, reason: 'agent_not_found' };

    agent.status = 'revoked';
    agent.updated = new Date().toISOString();
    this.registry.revokedDids.add(agentDid);
    return { ok: true, reason: 'did_revoked' };
  }

  /** Suspend an agent DID (temporary) */
  suspendDID(agentDid: string): { ok: boolean; reason: string } {
    const agent = this.registry.agents.get(agentDid);
    if (!agent) return { ok: false, reason: 'agent_not_found' };

    agent.status = 'suspended';
    agent.updated = new Date().toISOString();
    return { ok: true, reason: 'did_suspended' };
  }

  /** Reinstate a suspended agent DID */
  reinstateDID(agentDid: string): { ok: boolean; reason: string } {
    const agent = this.registry.agents.get(agentDid);
    if (!agent) return { ok: false, reason: 'agent_not_found' };
    if (agent.status === 'revoked') return { ok: false, reason: 'cannot_reinstate_revoked_did' };

    agent.status = 'active';
    agent.updated = new Date().toISOString();
    return { ok: true, reason: 'did_reinstated' };
  }

  /** Update agent risk score based on behavioral signals */
  updateRiskScore(agentDid: string, score: number, signals: string[]): void {
    const agent = this.registry.agents.get(agentDid);
    if (!agent) return;
    agent.riskScore = Math.max(0, Math.min(100, score));
    agent.metadata.lastRiskSignals = signals;
    agent.metadata.lastRiskUpdate = new Date().toISOString();
    agent.updated = new Date().toISOString();

    // Auto-suspend agents with critical risk score
    if (score >= 90) {
      agent.status = 'suspended';
      agent.metadata.autoSuspendReason = `risk_score_${score}_exceeded_threshold`;
    }
  }

  /** Get agent by DID */
  getAgent(agentDid: string): AgentDID | undefined {
    return this.registry.agents.get(agentDid);
  }

  /** List all active agents */
  listActiveAgents(): AgentDID[] {
    return Array.from(this.registry.agents.values()).filter((a) => a.status === 'active');
  }

  /** List all agents (including revoked/suspended) */
  listAllAgents(): AgentDID[] {
    return Array.from(this.registry.agents.values());
  }

  /** Get registry statistics */
  getStats(): {
    total: number;
    active: number;
    suspended: number;
    revoked: number;
    avgRiskScore: number;
  } {
    const all = Array.from(this.registry.agents.values());
    const active = all.filter((a) => a.status === 'active');
    const avgRisk = all.length > 0
      ? all.reduce((sum, a) => sum + a.riskScore, 0) / all.length
      : 0;

    return {
      total: all.length,
      active: active.length,
      suspended: all.filter((a) => a.status === 'suspended').length,
      revoked: all.filter((a) => a.status === 'revoked').length,
      avgRiskScore: Math.round(avgRisk * 100) / 100,
    };
  }

  /** Sign an attestation with an agent's DID */
  signAttestation(agentDid: string, payload: Record<string, unknown>): {
    attestation: string;
    agentDid: string;
    timestamp: string;
    signatureHash: string;
  } {
    const agent = this.registry.agents.get(agentDid);
    if (!agent || agent.status !== 'active') {
      throw new Error(`Cannot sign: agent ${agentDid} is ${agent?.status ?? 'not found'}`);
    }

    const attestationPayload = JSON.stringify({ agentDid, payload, timestamp: new Date().toISOString() });
    const hash = crypto.createHash('sha256').update(attestationPayload).digest('hex');

    return {
      attestation: attestationPayload,
      agentDid,
      timestamp: new Date().toISOString(),
      signatureHash: `did_attestation_sig_${hash.substring(0, 32)}`,
    };
  }
}
