// GRC Registry — type definitions

export type PackTier = 'community' | 'verified' | 'enterprise' | 'sovereign';
export type PackStatus = 'active' | 'deprecated' | 'draft' | 'withdrawn';

export interface RegistryPackManifest {
  name: string;               // e.g. '@grc-claw/framework-gdpr'
  version: string;            // semver
  framework: string;          // e.g. 'gdpr'
  frameworkVersion: string;   // e.g. '2016/679 as amended'
  displayName: string;
  description: string;
  jurisdiction: string;
  industry?: string[];
  controlCount: number;
  crosswalkCount: number;     // mappings to other frameworks
  tier: PackTier;
  status: PackStatus;
  publisher: string;          // DID of publisher node
  publishedAt: string;
  contentHash: string;        // SHA-256 of pack content
  signatureAlgorithm: string;
  signature: string;          // publisher signature
  trustScore?: number;        // 0-100, based on publisher history
  downloadCount?: number;
  pricing?: PackPricing;
  dependencies?: string[];    // other pack names this depends on
  tags: string[];
}

export interface PackPricing {
  model: 'free' | 'paid' | 'enterprise_only';
  priceUsdPerYear?: number;
  trialDays?: number;
  purchaseUrl?: string;
}

export interface RegistrySearchResult {
  packs: RegistryPackManifest[];
  total: number;
  page: number;
  pageSize: number;
  query?: string;
}

export interface RegistryStats {
  totalPacks: number;
  totalDownloads: number;
  frameworks: string[];
  jurisdictions: string[];
  publishers: number;
  lastUpdated: string;
}
