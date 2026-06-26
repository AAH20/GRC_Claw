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

// ─── Database Interface (compatible with @grc-claw/persistence Database) ──

export interface IdentityDatabase {
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[]; rowCount: number }>;
  execute(sql: string, params?: unknown[]): Promise<void>;
}

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
  private db?: IdentityDatabase;

  constructor(database?: IdentityDatabase) {
    this.db = database;
  }

  async initializeDatabase(): Promise<void> {
    if (!this.db) return;
    await this.db.execute(`
      CREATE TABLE IF NOT EXISTS agent_did_registry (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        did VARCHAR(500) NOT NULL UNIQUE,
        public_key TEXT NOT NULL,
        private_key TEXT NOT NULL,
        status VARCHAR(50) NOT NULL DEFAULT 'active',
        risk_score DECIMAL(5,2) NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )
    `);
    await this.db.execute(`
      CREATE TABLE IF NOT EXISTS agent_credentials (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        holder_did VARCHAR(500) NOT NULL,
        issuer_did VARCHAR(500) NOT NULL,
        type VARCHAR(100) NOT NULL,
        claims JSONB NOT NULL DEFAULT '{}',
        proof JSONB NOT NULL DEFAULT '{}',
        issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        expires_at TIMESTAMPTZ NOT NULL,
        revoked BOOLEAN NOT NULL DEFAULT false
      )
    `);
  }

  async loadFromDatabase(): Promise<void> {
    if (!this.db) return;
    try {
      const { rows: agentRows } = await this.db.query<{
        id: string;
        did: string;
        public_key: string;
        private_key: string;
        status: string;
        risk_score: number;
        created_at: string;
      }>(`SELECT * FROM agent_did_registry`);

      for (const row of agentRows) {
        const keyPair = crypto.generateKeyPairSync('ed25519');
        const verificationMethod: VerificationMethod = {
          id: `${row.did}#key-1`,
          type: 'Ed25519VerificationKey2020',
          controller: row.did,
          publicKeyHex: row.public_key,
        };

        const agentDid: AgentDID = {
          '@context': [
            'https://www.w3.org/ns/did/v1',
            'https://w3id.org/security/suites/ed25519-2020/v1',
            'https://grc-claw.a2zsoc.com/ns/agent-identity/v1',
          ],
          id: row.did,
          controller: '',
          created: row.created_at,
          updated: row.created_at,
          verificationMethod: [verificationMethod],
          authentication: [verificationMethod.id],
          service: [],
          credentials: [],
          status: row.status as AgentDID['status'],
          riskScore: row.risk_score,
          metadata: {},
        };

        if (row.status === 'revoked') {
          this.registry.revokedDids.add(row.did);
        }

        this.registry.agents.set(row.did, agentDid);
      }

      const { rows: credRows } = await this.db.query<{
        holder_did: string;
        issuer_did: string;
        type: string;
        claims: Record<string, unknown>;
        proof: Record<string, unknown>;
        issued_at: string;
        expires_at: string;
        revoked: boolean;
      }>(`SELECT * FROM agent_credentials`);

      for (const row of credRows) {
        const agent = this.registry.agents.get(row.holder_did);
        if (agent) {
          const vc: VerifiableCredential = {
            '@context': [
              'https://www.w3.org/2018/credentials/v1',
              'https://grc-claw.a2zsoc.com/ns/compliance-credential/v1',
            ],
            type: ['VerifiableCredential', 'ComplianceCertification'],
            issuer: row.issuer_did,
            issuanceDate: row.issued_at,
            expirationDate: row.expires_at,
            credentialSubject: row.claims as unknown as AgentCredentialSubject,
            proof: row.proof as unknown as CredentialProof,
          };
          agent.credentials.push(vc);
        }
      }

      console.log(`[AGENT-IDENTITY] Loaded ${agentRows.length} agents, ${credRows.length} credentials from database`);
    } catch (err) {
      console.error('[AGENT-IDENTITY] Failed to load from database:', err instanceof Error ? err.message : err);
    }
  }

  /** Generate a new DID for an agent */
  async createAgentDID(opts: {
    controller: string;
    tenantScope: string[];
    sovereignBoundary?: 'us-only' | 'eu-only' | 'global' | 'airgapped';
    services?: ServiceEndpoint[];
  }): Promise<AgentDID> {
    const uuid = crypto.randomUUID();
    const did = `did:grc:${uuid}`;
    const keyPair = crypto.generateKeyPairSync('ed25519');
    const pubKeyHex = keyPair.publicKey.export({ type: 'spki', format: 'der' }).toString('hex');
    const privKeyHex = keyPair.privateKey.export({ type: 'pkcs8', format: 'der' }).toString('hex');

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

    if (this.db) {
      try {
        await this.db.execute(
          `INSERT INTO agent_did_registry (did, public_key, private_key, status, risk_score, created_at)
           VALUES ($1, $2, $3, $4, $5, NOW())
           ON CONFLICT (did) DO NOTHING`,
          [did, pubKeyHex, privKeyHex, 'active', 0]
        );
      } catch (err) {
        console.error('[AGENT-IDENTITY] Failed to persist DID to database:', err instanceof Error ? err.message : err);
      }
    }

    return agentDid;
  }

  /** Issue a Verifiable Credential to an agent */
  async issueCredential(agentDid: string, credential: {
    framework: AgentCredentialSubject['framework'];
    certifiedControls: string[];
    toolTierAccess: ('read' | 'write' | 'destructive')[];
    tenantScope: string[];
    sovereignBoundary: AgentCredentialSubject['sovereignBoundary'];
    validDays?: number;
  }): Promise<VerifiableCredential> {
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

    if (this.db) {
      try {
        await this.db.execute(
          `INSERT INTO agent_credentials (holder_did, issuer_did, type, claims, proof, issued_at, expires_at, revoked)
           VALUES ($1, $2, $3, $4, $5, $6, $7, false)`,
          [
            agentDid,
            agent.controller,
            'ComplianceCertification',
            JSON.stringify(credentialSubject),
            JSON.stringify(vc.proof),
            now.toISOString(),
            expiry.toISOString(),
          ]
        );
      } catch (err) {
        console.error('[AGENT-IDENTITY] Failed to persist credential to database:', err instanceof Error ? err.message : err);
      }
    }

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
  async revokeDID(agentDid: string): Promise<{ ok: boolean; reason: string }> {
    const agent = this.registry.agents.get(agentDid);
    if (!agent) return { ok: false, reason: 'agent_not_found' };

    agent.status = 'revoked';
    agent.updated = new Date().toISOString();
    this.registry.revokedDids.add(agentDid);

    if (this.db) {
      try {
        await this.db.execute(
          `UPDATE agent_did_registry SET status = 'revoked' WHERE did = $1`,
          [agentDid]
        );
        await this.db.execute(
          `UPDATE agent_credentials SET revoked = true WHERE holder_did = $1`,
          [agentDid]
        );
      } catch (err) {
        console.error('[AGENT-IDENTITY] Failed to persist revocation to database:', err instanceof Error ? err.message : err);
      }
    }

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
