import { randomUUID } from "node:crypto";
import type { TrustCredential, MarketplaceListing, PurchaseResult, TrustScore, CredentialType, ListingStatus } from "../types.js";

export class TrustMarketplace {
  private listings: Map<string, MarketplaceListing> = new Map();
  private credentials: Map<string, TrustCredential> = new Map();
  private transactions: PurchaseResult[] = [];

  issueCredential(input: {
    issuerOrgId: string;
    subjectOrgId: string;
    type: CredentialType;
    framework: string;
    score: number;
    zkProofId?: string;
  }): TrustCredential {
    const credential: TrustCredential = {
      id: randomUUID(),
      issuerOrgId: input.issuerOrgId,
      subjectOrgId: input.subjectOrgId,
      type: input.type,
      framework: input.framework,
      score: input.score,
      issuedAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
      zkProofId: input.zkProofId,
      metadata: {},
    };
    this.credentials.set(credential.id, credential);
    return credential;
  }

  listCredential(credentialId: string, price: number, currency: string = "USD"): MarketplaceListing | null {
    const credential = this.credentials.get(credentialId);
    if (!credential) return null;

    const listing: MarketplaceListing = {
      id: randomUUID(),
      credentialId,
      sellerOrgId: credential.subjectOrgId,
      type: credential.type,
      framework: credential.framework,
      price,
      currency,
      status: "active",
      listedAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    };

    this.listings.set(listing.id, listing);
    return listing;
  }

  purchaseCredential(listingId: string, buyerOrgId: string): PurchaseResult | null {
    const listing = this.listings.get(listingId);
    if (!listing || listing.status !== "active") return null;

    const credential = this.credentials.get(listing.credentialId);
    if (!credential) return null;

    listing.status = "sold";

    const result: PurchaseResult = {
      listingId,
      buyerOrgId,
      credential: { ...credential, subjectOrgId: buyerOrgId },
      transactionId: randomUUID(),
      timestamp: new Date().toISOString(),
    };

    this.transactions.push(result);
    return result;
  }

  getOrgTrustScore(orgId: string): TrustScore {
    const orgCredentials = Array.from(this.credentials.values()).filter(
      (c) => c.subjectOrgId === orgId || c.issuerOrgId === orgId
    );

    const overallScore = orgCredentials.length > 0
      ? orgCredentials.reduce((sum, c) => sum + c.score, 0) / orgCredentials.length
      : 0;

    return {
      orgId,
      overallScore: Math.round(overallScore),
      dimensions: { credentials: orgCredentials.length },
      credentials: orgCredentials.length,
      lastUpdated: new Date().toISOString(),
    };
  }

  getActiveListings(): MarketplaceListing[] {
    return Array.from(this.listings.values()).filter((l) => l.status === "active");
  }

  getListingsByFramework(framework: string): MarketplaceListing[] {
    return Array.from(this.listings.values()).filter((l) => l.framework === framework && l.status === "active");
  }

  getTransactions(): PurchaseResult[] {
    return this.transactions;
  }
}
