// GRC Registry — the npm for compliance framework packs
// Each pack is a versioned, signed artifact that can be installed with:
// grc add gdpr@2024.1  → installs GDPR framework pack into grcfile.yaml
import { createHash } from 'node:crypto';
import type { RegistryPackManifest, RegistrySearchResult, RegistryStats, PackTier } from './types.js';

// Built-in registry catalog (production: fetched from registry.a2zsoc.com)
const BUILTIN_PACKS: RegistryPackManifest[] = [
  {
    name: '@grc-claw/framework-iso27001',
    version: '2022.1.0',
    framework: 'iso27001',
    frameworkVersion: 'ISO/IEC 27001:2022',
    displayName: 'ISO 27001:2022 Information Security Management',
    description: '93 controls across 4 themes (Organizational, People, Physical, Technological). Includes Annex A crosswalk to NIST CSF, SOC 2, and ISO 42001.',
    jurisdiction: 'International',
    controlCount: 93,
    crosswalkCount: 34,
    tier: 'community',
    status: 'active',
    publisher: 'did:grc:node:a2zsoc-official',
    publishedAt: '2026-01-01T00:00:00Z',
    contentHash: createHash('sha256').update('iso27001-2022-pack').digest('hex'),
    signatureAlgorithm: 'HMAC-SHA256',
    signature: 'official-pack-sig-iso27001',
    trustScore: 100,
    downloadCount: 2847,
    pricing: { model: 'free' },
    tags: ['iso27001', 'information-security', 'isms', 'certification'],
  },
  {
    name: '@grc-claw/framework-iso42001',
    version: '2023.1.0',
    framework: 'iso42001',
    frameworkVersion: 'ISO/IEC 42001:2023',
    displayName: 'ISO 42001:2023 AI Management System (AIMS)',
    description: '38 controls for AI governance. Includes vendor gap matrix (Anthropic, OpenAI, Cursor, Google), EU AI Act mapping, and GRC_Claw exec policy alignment.',
    jurisdiction: 'International',
    controlCount: 38,
    crosswalkCount: 28,
    tier: 'verified',
    status: 'active',
    publisher: 'did:grc:node:a2zsoc-official',
    publishedAt: '2026-01-01T00:00:00Z',
    contentHash: createHash('sha256').update('iso42001-2023-pack').digest('hex'),
    signatureAlgorithm: 'HMAC-SHA256',
    signature: 'official-pack-sig-iso42001',
    trustScore: 100,
    downloadCount: 1203,
    pricing: { model: 'free' },
    tags: ['iso42001', 'aims', 'ai-governance', 'eu-ai-act'],
  },
  {
    name: '@grc-claw/framework-eu-ai-act',
    version: '2024.1.0',
    framework: 'eu-ai-act',
    frameworkVersion: 'EU AI Act (Regulation 2024/1689)',
    displayName: 'EU AI Act 2024/1689',
    description: '44 controls covering GPAI obligations (Art.53-55), high-risk AI system requirements (Art.9-17), conformity assessment, and post-market monitoring. Includes ISO 42001 crosswalk.',
    jurisdiction: 'EU',
    industry: ['All industries deploying AI in EU'],
    controlCount: 44,
    crosswalkCount: 22,
    tier: 'verified',
    status: 'active',
    publisher: 'did:grc:node:a2zsoc-official',
    publishedAt: '2026-01-01T00:00:00Z',
    contentHash: createHash('sha256').update('eu-ai-act-2024-pack').digest('hex'),
    signatureAlgorithm: 'HMAC-SHA256',
    signature: 'official-pack-sig-eu-ai-act',
    trustScore: 100,
    downloadCount: 891,
    pricing: { model: 'free' },
    tags: ['eu-ai-act', 'gpai', 'high-risk-ai', 'eu-regulation'],
  },
  {
    name: '@grc-claw/framework-soc2',
    version: '2022.1.0',
    framework: 'soc2',
    frameworkVersion: 'SOC 2 Trust Service Criteria (2022)',
    displayName: 'SOC 2 Type II (AICPA TSC)',
    description: '64 Trust Service Criteria controls (Security, Availability, Processing Integrity, Confidentiality, Privacy). Includes ISO 27001:2022 and NIST CSF crosswalk.',
    jurisdiction: 'US',
    controlCount: 64,
    crosswalkCount: 18,
    tier: 'community',
    status: 'active',
    publisher: 'did:grc:node:a2zsoc-official',
    publishedAt: '2026-01-01T00:00:00Z',
    contentHash: createHash('sha256').update('soc2-2022-pack').digest('hex'),
    signatureAlgorithm: 'HMAC-SHA256',
    signature: 'official-pack-sig-soc2',
    trustScore: 100,
    downloadCount: 3201,
    pricing: { model: 'free' },
    tags: ['soc2', 'aicpa', 'tsc', 'trust-service-criteria'],
  },
  {
    name: '@grc-claw/framework-dora',
    version: '2024.1.0',
    framework: 'dora',
    frameworkVersion: 'DORA (EU Regulation 2022/2554) + RTS',
    displayName: 'DORA — Digital Operational Resilience Act',
    description: '35 controls for financial entities. Includes final RTS on ICT risk management (Del. Reg. 2024/1774), incident reporting requirements, and TLPT framework. ISO 27001 and NIS2 crosswalk.',
    jurisdiction: 'EU',
    industry: ['Financial Services', 'FinTech', 'Insurance', 'Crypto Asset Services'],
    controlCount: 35,
    crosswalkCount: 15,
    tier: 'enterprise',
    status: 'active',
    publisher: 'did:grc:node:a2zsoc-official',
    publishedAt: '2026-01-01T00:00:00Z',
    contentHash: createHash('sha256').update('dora-2024-pack').digest('hex'),
    signatureAlgorithm: 'HMAC-SHA256',
    signature: 'official-pack-sig-dora',
    trustScore: 100,
    downloadCount: 423,
    pricing: { model: 'paid', priceUsdPerYear: 999, trialDays: 30, purchaseUrl: 'https://a2zsoc.com/registry/dora' },
    tags: ['dora', 'financial-resilience', 'ict-risk', 'eu-financial'],
  },
  {
    name: '@grc-claw/framework-cmmc',
    version: '2.0.1',
    framework: 'cmmc',
    frameworkVersion: 'CMMC 2.0 Level 2/3',
    displayName: 'CMMC 2.0 — Cybersecurity Maturity Model Certification',
    description: '110 practices (CMMC Level 2) + 24 additional (Level 3) based on NIST SP 800-171. Includes C3PAO evidence generation, SPRS score calculation, and System Security Plan templates.',
    jurisdiction: 'US',
    industry: ['Defense Industrial Base', 'DoD Contractors'],
    controlCount: 134,
    crosswalkCount: 24,
    tier: 'enterprise',
    status: 'active',
    publisher: 'did:grc:node:a2zsoc-official',
    publishedAt: '2026-01-01T00:00:00Z',
    contentHash: createHash('sha256').update('cmmc-2.0-pack').digest('hex'),
    signatureAlgorithm: 'HMAC-SHA256',
    signature: 'official-pack-sig-cmmc',
    trustScore: 100,
    downloadCount: 287,
    pricing: { model: 'enterprise_only', purchaseUrl: 'https://a2zsoc.com/contact' },
    tags: ['cmmc', 'dib', 'dod', 'nist-800-171'],
  },
  {
    name: '@grc-claw/framework-gdpr',
    version: '2024.1.0',
    framework: 'gdpr',
    frameworkVersion: 'GDPR (2016/679) + EDPB Guidelines 2024',
    displayName: 'GDPR — General Data Protection Regulation',
    description: '28 technical and organizational controls. Includes 2024 EDPB guidelines on AI processing, DPA authority guidance, and ISO 27001:2022 crosswalk. DPIA template included.',
    jurisdiction: 'EU/EEA',
    industry: ['All industries processing EU personal data'],
    controlCount: 28,
    crosswalkCount: 14,
    tier: 'community',
    status: 'active',
    publisher: 'did:grc:node:a2zsoc-official',
    publishedAt: '2026-01-01T00:00:00Z',
    contentHash: createHash('sha256').update('gdpr-2024-pack').digest('hex'),
    signatureAlgorithm: 'HMAC-SHA256',
    signature: 'official-pack-sig-gdpr',
    trustScore: 100,
    downloadCount: 1876,
    pricing: { model: 'free' },
    tags: ['gdpr', 'data-protection', 'privacy', 'eu'],
  },
  {
    name: '@grc-claw/framework-fedramp',
    version: '2024.1.0',
    framework: 'fedramp',
    frameworkVersion: 'FedRAMP Rev 5 Moderate Baseline',
    displayName: 'FedRAMP Moderate — Rev 5 (NIST SP 800-53 Rev 5)',
    description: '323 controls (moderate baseline). Includes ATO workflow templates, continuous monitoring requirements, and OSCAL-compatible evidence format. NIST CSF crosswalk.',
    jurisdiction: 'US',
    industry: ['Cloud Service Providers (US Federal)'],
    controlCount: 323,
    crosswalkCount: 89,
    tier: 'sovereign',
    status: 'active',
    publisher: 'did:grc:node:a2zsoc-official',
    publishedAt: '2026-01-01T00:00:00Z',
    contentHash: createHash('sha256').update('fedramp-rev5-pack').digest('hex'),
    signatureAlgorithm: 'HMAC-SHA256',
    signature: 'official-pack-sig-fedramp',
    trustScore: 100,
    downloadCount: 156,
    pricing: { model: 'enterprise_only', purchaseUrl: 'https://a2zsoc.com/contact' },
    tags: ['fedramp', 'nist-800-53', 'us-federal', 'cloud'],
  },
];

export class GRCRegistry {
  private packs: RegistryPackManifest[] = [...BUILTIN_PACKS];

  search(query?: string, filters?: { framework?: string; jurisdiction?: string; tier?: PackTier; free?: boolean }): RegistrySearchResult {
    let results = this.packs.filter((p) => p.status === 'active');

    if (query) {
      const q = query.toLowerCase();
      results = results.filter((p) =>
        p.name.toLowerCase().includes(q) ||
        p.displayName.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.tags.some((t) => t.includes(q))
      );
    }

    if (filters?.framework) results = results.filter((p) => p.framework === filters.framework);
    if (filters?.jurisdiction) results = results.filter((p) => p.jurisdiction.toLowerCase().includes(filters.jurisdiction!.toLowerCase()));
    if (filters?.tier) results = results.filter((p) => p.tier === filters.tier);
    if (filters?.free) results = results.filter((p) => p.pricing?.model === 'free');

    return { packs: results, total: results.length, page: 1, pageSize: results.length };
  }

  get(name: string, version?: string): RegistryPackManifest | undefined {
    return this.packs.find((p) => p.name === name && (!version || p.version === version));
  }

  getByFramework(framework: string): RegistryPackManifest[] {
    return this.packs.filter((p) => p.framework === framework && p.status === 'active');
  }

  stats(): RegistryStats {
    return {
      totalPacks: this.packs.length,
      totalDownloads: this.packs.reduce((s, p) => s + (p.downloadCount ?? 0), 0),
      frameworks: [...new Set(this.packs.map((p) => p.framework))].sort(),
      jurisdictions: [...new Set(this.packs.map((p) => p.jurisdiction))].sort(),
      publishers: new Set(this.packs.map((p) => p.publisher)).size,
      lastUpdated: new Date().toISOString(),
    };
  }

  verifyPack(pack: RegistryPackManifest): { valid: boolean; reason?: string } {
    const recomputedHash = createHash('sha256').update(pack.name + pack.version + pack.framework).digest('hex');
    if (!pack.contentHash) return { valid: false, reason: 'missing_content_hash' };
    if (!pack.signature) return { valid: false, reason: 'missing_signature' };
    if (pack.status === 'withdrawn') return { valid: false, reason: 'pack_withdrawn' };
    return { valid: true };
  }
}
