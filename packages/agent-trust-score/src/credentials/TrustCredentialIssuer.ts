import type { TrustCredential, CredentialType, TrustScoreDimensions, AgentTrustProfile } from "../types.js";
import { createHash, randomUUID } from "node:crypto";

export interface CredentialStore {
  store(credential: TrustCredential): Promise<void>;
  get(id: string): Promise<TrustCredential | undefined>;
  listByAgent(agentDid: string): Promise<TrustCredential[]>;
  revoke(id: string): Promise<boolean>;
}

export class TrustCredentialIssuer {
  private store: CredentialStore;
  private issuerId: string;

  constructor(store: CredentialStore, issuerId: string = "did:grc:trust-score") {
    this.store = store;
    this.issuerId = issuerId;
  }

  async issueIdentityCredential(agentDid: string, claims: Record<string, unknown>): Promise<TrustCredential> {
    return this.issueCredential(agentDid, "identity", {
      ...claims,
      verifiedAt: new Date().toISOString(),
      verificationMethod: "did:grc:key-1",
    });
  }

  async issueCapabilityCredential(agentDid: string, toolTierAccess: string[], frameworks: string[]): Promise<TrustCredential> {
    return this.issueCredential(agentDid, "capability", {
      toolTierAccess,
      frameworks,
      certifiedAt: new Date().toISOString(),
    });
  }

  async issueComplianceCredential(agentDid: string, dimensions: TrustScoreDimensions, complianceScore: number): Promise<TrustCredential> {
    return this.issueCredential(agentDid, "compliance", {
      dimensions,
      complianceScore,
      auditDate: new Date().toISOString(),
    });
  }

  async issueBehaviorCredential(agentDid: string, behavioralScore: number, anomalyCount: number): Promise<TrustCredential> {
    return this.issueCredential(agentDid, "behavior", {
      behavioralScore,
      anomalyCount,
      analysisDate: new Date().toISOString(),
    });
  }

  async issueCompositeCredential(
    agentDid: string,
    profile: AgentTrustProfile
  ): Promise<TrustCredential> {
    return this.issueCredential(agentDid, "composite", {
      overallScore: profile.overallTrustScore,
      dimensions: profile.dimensions,
      riskLevel: profile.riskLevel,
      generatedAt: profile.lastScoredAt,
    });
  }

  private async issueCredential(
    agentDid: string,
    type: CredentialType,
    claims: Record<string, unknown>
  ): Promise<TrustCredential> {
    const id = `vc-trust-${randomUUID()}`;
    const now = new Date();
    const expiresAt = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000);

    const credential: TrustCredential = {
      id,
      agentDid,
      type,
      claims,
      issuedAt: now.toISOString(),
      expiresAt: expiresAt.toISOString(),
      issuer: this.issuerId,
      signature: this.generateSignature(id, agentDid, type, claims),
      revoked: false,
    };

    await this.store.store(credential);
    return credential;
  }

  private generateSignature(
    credentialId: string,
    agentDid: string,
    type: CredentialType,
    claims: Record<string, unknown>
  ): string {
    const payload = JSON.stringify({ credentialId, agentDid, type, claims, issuer: this.issuerId });
    return createHash("sha256").update(payload).digest("hex");
  }

  async verifyCredential(credential: TrustCredential): Promise<{ valid: boolean; reason?: string }> {
    if (credential.revoked) return { valid: false, reason: "Credential revoked" };
    if (new Date(credential.expiresAt) < new Date()) return { valid: false, reason: "Credential expired" };

    const expectedSignature = this.generateSignature(
      credential.id,
      credential.agentDid,
      credential.type,
      credential.claims
    );

    if (credential.signature !== expectedSignature) {
      return { valid: false, reason: "Signature verification failed" };
    }

    return { valid: true };
  }

  async getCredentialSummary(agentDid: string): Promise<{
    total: number;
    valid: number;
    expired: number;
    revoked: number;
  }> {
    const credentials = await this.store.listByAgent(agentDid);
    const now = new Date();

    return {
      total: credentials.length,
      valid: credentials.filter((c) => !c.revoked && new Date(c.expiresAt) > now).length,
      expired: credentials.filter((c) => new Date(c.expiresAt) <= now).length,
      revoked: credentials.filter((c) => c.revoked).length,
    };
  }
}
