export type CredentialType = "compliance" | "audit" | "risk" | "trust" | "framework";
export type ListingStatus = "active" | "sold" | "expired" | "revoked";

export interface TrustCredential {
  id: string;
  issuerOrgId: string;
  subjectOrgId: string;
  type: CredentialType;
  framework: string;
  score: number;
  issuedAt: string;
  expiresAt: string;
  zkProofId?: string;
  metadata: Record<string, unknown>;
}

export interface MarketplaceListing {
  id: string;
  credentialId: string;
  sellerOrgId: string;
  type: CredentialType;
  framework: string;
  price: number;
  currency: string;
  status: ListingStatus;
  listedAt: string;
  expiresAt: string;
}

export interface PurchaseResult {
  listingId: string;
  buyerOrgId: string;
  credential: TrustCredential;
  transactionId: string;
  timestamp: string;
}

export interface TrustScore {
  orgId: string;
  overallScore: number;
  dimensions: Record<string, number>;
  credentials: number;
  lastUpdated: string;
}
