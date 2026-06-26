// PackVerifier — cryptographic verification of registry pack integrity
import { createHash, createHmac } from 'node:crypto';
import type { RegistryPackManifest } from './types.js';

export class PackVerifier {
  private trustedPublishers: Set<string>;

  constructor(trustedPublishers: string[] = ['did:grc:node:a2zsoc-official']) {
    this.trustedPublishers = new Set(trustedPublishers);
  }

  computeContentHash(pack: Omit<RegistryPackManifest, 'contentHash' | 'signature'>): string {
    const canonical = JSON.stringify({
      name: pack.name,
      version: pack.version,
      framework: pack.framework,
      frameworkVersion: pack.frameworkVersion,
      controlCount: pack.controlCount,
      crosswalkCount: pack.crosswalkCount,
      publisher: pack.publisher,
      publishedAt: pack.publishedAt,
    });
    return createHash('sha256').update(canonical).digest('hex');
  }

  verifySignature(pack: RegistryPackManifest, publisherSecret: string): boolean {
    const expectedSig = createHmac('sha256', publisherSecret)
      .update(pack.contentHash + pack.publisher + pack.publishedAt)
      .digest('hex');
    return pack.signature === expectedSig;
  }

  isTrustedPublisher(publisherDid: string): boolean {
    return this.trustedPublishers.has(publisherDid);
  }

  auditPack(pack: RegistryPackManifest): { passed: boolean; checks: Array<{ check: string; passed: boolean; detail?: string }> } {
    const checks = [
      { check: 'name_format', passed: pack.name.startsWith('@grc-claw/'), detail: pack.name },
      { check: 'semver_version', passed: /^\d+\.\d+\.\d+/.test(pack.version), detail: pack.version },
      { check: 'content_hash_present', passed: Boolean(pack.contentHash), detail: pack.contentHash?.slice(0, 16) + '…' },
      { check: 'signature_present', passed: Boolean(pack.signature) },
      { check: 'trusted_publisher', passed: this.isTrustedPublisher(pack.publisher), detail: pack.publisher },
      { check: 'status_active', passed: pack.status === 'active', detail: pack.status },
      { check: 'controls_documented', passed: pack.controlCount > 0, detail: `${pack.controlCount} controls` },
    ];
    return { passed: checks.every((c) => c.passed), checks };
  }
}
