/**
 * @grc-claw/compliance-marketplace
 *
 * Compliance-as-code marketplace for sharing, discovering, and monetizing
 * compliance rules, templates, and automation packs.
 */

import { randomUUID } from "node:crypto";

// ---------------------------------------------------------------------------
// Types & Enums
// ---------------------------------------------------------------------------

export type PackStatus = "draft" | "published" | "deprecated" | "yanked";
export type LicenseType = "MIT" | "Apache-2.0" | "Proprietary" | "Custom";
export type PackTier = "free" | "basic" | "professional" | "enterprise";

export interface PackAuthor {
  id: string;
  name: string;
  email?: string;
  url?: string;
}

export interface PackVersion {
  version: string;
  publishedAt: Date;
  checksum: string;
  tarballUrl?: string;
}

export interface PackDependency {
  packId: string;
  versionRange: string;
}

export interface PackMetadata {
  frameworks: string[];
  industries: string[];
  useCases: string[];
  tags: string[];
}

export interface PackRatingAggregate {
  packId: string;
  average: number;
  count: number;
  distribution: Record<1 | 2 | 3 | 4 | 5, number>;
}

export interface Review {
  id: string;
  packId: string;
  authorId: string;
  rating: 1 | 2 | 3 | 4 | 5;
  title: string;
  body: string;
  createdAt: Date;
  updatedAt: Date;
  helpful: number;
}

export interface ComplianceRule {
  id: string;
  name: string;
  description: string;
  framework: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  logic: Record<string, unknown>;
  remediation?: string;
  references?: string[];
}

export interface CompliancePack {
  id: string;
  name: string;
  slug: string;
  description: string;
  longDescription?: string;
  author: PackAuthor;
  status: PackStatus;
  tier: PackTier;
  price: number;
  license: LicenseType;
  metadata: PackMetadata;
  versions: PackVersion[];
  latestVersion: string;
  dependencies: PackDependency[];
  rules: ComplianceRule[];
  downloads: number;
  rating: PackRatingAggregate;
  createdAt: Date;
  updatedAt: Date;
}

export interface InstallResult {
  packId: string;
  version: string;
  installedAt: Date;
  rulesInstalled: number;
}

export interface PublishInput {
  name: string;
  description: string;
  longDescription?: string;
  author: PackAuthor;
  tier?: PackTier;
  price?: number;
  license?: LicenseType;
  metadata?: Partial<PackMetadata>;
  dependencies?: PackDependency[];
  rules: ComplianceRule[];
}

export interface DiscoveryFilter {
  frameworks?: string[];
  industries?: string[];
  useCases?: string[];
  tags?: string[];
  tier?: PackTier;
  minRating?: number;
  query?: string;
  sort?: "rating" | "downloads" | "newest" | "name";
  limit?: number;
  offset?: number;
}

export interface MarketplaceStats {
  totalPacks: number;
  totalDownloads: number;
  totalRules: number;
  totalReviews: number;
}

// ---------------------------------------------------------------------------
// Error helpers
// ---------------------------------------------------------------------------

export class MarketplaceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
  ) {
    super(message);
    this.name = "MarketplaceError";
  }
}

export class PackNotFoundError extends MarketplaceError {
  constructor(identifier: string) {
    super(`Pack not found: ${identifier}`, "PACK_NOT_FOUND");
    this.name = "PackNotFoundError";
  }
}

export class VersionConflictError extends MarketplaceError {
  constructor(
    packId: string,
    required: string,
    available: string,
  ) {
    super(
      `Version conflict for ${packId}: required ${required}, available ${available}`,
      "VERSION_CONFLICT",
    );
    this.name = "VersionConflictError";
  }
}

export class DependencyError extends MarketplaceError {
  constructor(message: string) {
    super(message, "DEPENDENCY_ERROR");
    this.name = "DependencyError";
  }
}

export class PublishError extends MarketplaceError {
  constructor(message: string) {
    super(message, "PUBLISH_ERROR");
    this.name = "PublishError";
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function parseSemver(version: string): [number, number, number] {
  const parts = version.split(".").map(Number);
  if (parts.length !== 3 || parts.some((p) => Number.isNaN(p) || p < 0)) {
    throw new MarketplaceError(`Invalid semver: ${version}`, "INVALID_SEMVER");
  }
  return parts as [number, number, number];
}

function satisfiesRange(version: string, range: string): boolean {
  const v = parseSemver(version);
  const cleanRange = range.trim();

  // Exact match
  if (cleanRange === v.join(".")) return true;

  // Major bump range (e.g. ^1.0.0)
  if (cleanRange.startsWith("^")) {
    const target = parseSemver(cleanRange.slice(1));
    return v[0] === target[0] && versionGreaterOrEqual(v, target);
  }

  // Minor range (e.g. ~1.2.0)
  if (cleanRange.startsWith("~")) {
    const target = parseSemver(cleanRange.slice(1));
    return (
      v[0] === target[0] &&
      v[1] === target[1] &&
      versionGreaterOrEqual(v, target)
    );
  }

  // Exact
  const target = parseSemver(cleanRange);
  return v[0] === target[0] && v[1] === target[1] && v[2] === target[2];
}

function versionGreaterOrEqual(
  a: [number, number, number],
  b: [number, number, number],
): boolean {
  if (a[0] !== b[0]) return a[0] > b[0];
  if (a[1] !== b[1]) return a[1] > b[1];
  return a[2] >= b[2];
}

function sortVersionsDescending(versions: PackVersion[]): PackVersion[] {
  return [...versions].sort((a, b) => {
    const pa = parseSemver(a.version);
    const pb = parseSemver(b.version);
    if (pa[0] !== pb[0]) return pb[0] - pa[0];
    if (pa[1] !== pb[1]) return pb[1] - pa[1];
    return pb[2] - pa[2];
  });
}

// ---------------------------------------------------------------------------
// CompliancePack model
// ---------------------------------------------------------------------------

export class CompliancePackModel implements CompliancePack {
  id: string;
  name: string;
  slug: string;
  description: string;
  longDescription?: string;
  author: PackAuthor;
  status: PackStatus;
  tier: PackTier;
  price: number;
  license: LicenseType;
  metadata: PackMetadata;
  versions: PackVersion[];
  latestVersion: string;
  dependencies: PackDependency[];
  rules: ComplianceRule[];
  downloads: number;
  rating: PackRatingAggregate;
  createdAt: Date;
  updatedAt: Date;

  constructor(input: PublishInput, id?: string) {
    this.id = id ?? randomUUID();
    this.name = input.name;
    this.slug = slugify(input.name);
    this.description = input.description;
    this.longDescription = input.longDescription;
    this.author = input.author;
    this.status = "draft";
    this.tier = input.tier ?? "free";
    this.price = input.price ?? 0;
    this.license = input.license ?? "MIT";
    this.metadata = {
      frameworks: input.metadata?.frameworks ?? [],
      industries: input.metadata?.industries ?? [],
      useCases: input.metadata?.useCases ?? [],
      tags: input.metadata?.tags ?? [],
    };
    this.versions = [];
    this.latestVersion = "";
    this.dependencies = input.dependencies ?? [];
    this.rules = [...input.rules];
    this.downloads = 0;
    this.rating = {
      packId: this.id,
      average: 0,
      count: 0,
      distribution: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 },
    };
    this.createdAt = new Date();
    this.updatedAt = new Date();
  }

  /** Publish a new version of this pack. */
  publishVersion(version: string, checksum: string, tarballUrl?: string): PackVersion {
    if (this.versions.some((v) => v.version === version)) {
      throw new PublishError(`Version ${version} already exists for pack ${this.slug}`);
    }

    const entry: PackVersion = {
      version,
      publishedAt: new Date(),
      checksum,
      tarballUrl,
    };
    this.versions.push(entry);
    this.latestVersion = version;
    this.status = "published";
    this.updatedAt = new Date();
    return entry;
  }

  /** Resolve a version by range or exact match. */
  resolveVersion(range?: string): PackVersion {
    const sorted = sortVersionsDescending(this.versions);
    if (sorted.length === 0) {
      throw new MarketplaceError(
        `No versions published for pack ${this.slug}`,
        "NO_VERSIONS",
      );
    }

    if (!range || range === "latest") return sorted[0];

    const match = sorted.find((v) => satisfiesRange(v.version, range));
    if (!match) {
      throw new VersionConflictError(this.id, range, this.latestVersion);
    }
    return match;
  }

  /** Check if a dependency range is satisfiable. */
  checkDependency(dep: PackDependency): void {
    // The pack itself is checked externally; here we just validate the range format.
    if (!dep.versionRange || dep.versionRange.trim().length === 0) {
      throw new DependencyError(
        `Empty version range for dependency ${dep.packId}`,
      );
    }
  }

  toJSON(): CompliancePack {
    return {
      id: this.id,
      name: this.name,
      slug: this.slug,
      description: this.description,
      longDescription: this.longDescription,
      author: this.author,
      status: this.status,
      tier: this.tier,
      price: this.price,
      license: this.license,
      metadata: this.metadata,
      versions: this.versions,
      latestVersion: this.latestVersion,
      dependencies: this.dependencies,
      rules: this.rules,
      downloads: this.downloads,
      rating: this.rating,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
    };
  }
}

// ---------------------------------------------------------------------------
// PackPublisher
// ---------------------------------------------------------------------------

export class PackPublisher {
  private packs = new Map<string, CompliancePackModel>();

  /** Register a new pack or overwrite an existing one. */
  register(pack: CompliancePackModel): CompliancePackModel {
    if (this.packs.has(pack.id)) {
      throw new PublishError(`Pack ${pack.slug} is already registered (id=${pack.id})`);
    }
    this.packs.set(pack.id, pack);
    return pack;
  }

  /** Get a pack by id. */
  getPack(id: string): CompliancePackModel | undefined {
    return this.packs.get(id);
  }

  /** Get all registered packs. */
  getAllPacks(): CompliancePackModel[] {
    return Array.from(this.packs.values());
  }

  /** Remove a pack from the registry. */
  unregister(id: string): boolean {
    return this.packs.delete(id);
  }
}

// ---------------------------------------------------------------------------
// PackDiscovery
// ---------------------------------------------------------------------------

export class PackDiscovery {
  constructor(private readonly publisher: PackPublisher) {}

  /** Search packs with filters. */
  search(filters: DiscoveryFilter = {}): CompliancePackModel[] {
    let results = this.publisher.getAllPacks().filter((p) => p.status === "published");

    if (filters.frameworks && filters.frameworks.length > 0) {
      results = results.filter((p) =>
        filters.frameworks!.some((f) => p.metadata.frameworks.includes(f)),
      );
    }

    if (filters.industries && filters.industries.length > 0) {
      results = results.filter((p) =>
        filters.industries!.some((i) => p.metadata.industries.includes(i)),
      );
    }

    if (filters.useCases && filters.useCases.length > 0) {
      results = results.filter((p) =>
        filters.useCases!.some((u) => p.metadata.useCases.includes(u)),
      );
    }

    if (filters.tags && filters.tags.length > 0) {
      results = results.filter((p) =>
        filters.tags!.some((t) => p.metadata.tags.includes(t)),
      );
    }

    if (filters.tier) {
      results = results.filter((p) => p.tier === filters.tier);
    }

    if (filters.minRating !== undefined) {
      results = results.filter((p) => p.rating.average >= filters.minRating!);
    }

    if (filters.query) {
      const q = filters.query.toLowerCase();
      results = results.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q) ||
          p.metadata.tags.some((t) => t.toLowerCase().includes(q)),
      );
    }

    // Sort
    const sortMode = filters.sort ?? "rating";
    results.sort((a, b) => {
      switch (sortMode) {
        case "rating":
          return b.rating.average - a.rating.average;
        case "downloads":
          return b.downloads - a.downloads;
        case "newest":
          return b.createdAt.getTime() - a.createdAt.getTime();
        case "name":
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });

    // Paginate
    const offset = filters.offset ?? 0;
    const limit = filters.limit ?? 20;
    return results.slice(offset, offset + limit);
  }

  /** Find a pack by slug or id. */
  findByIdentifier(identifier: string): CompliancePackModel | undefined {
    for (const pack of this.publisher.getAllPacks()) {
      if (pack.id === identifier || pack.slug === identifier) return pack;
    }
    return undefined;
  }

  /** List all packs for a given framework. */
  listByFramework(framework: string): CompliancePackModel[] {
    return this.search({ frameworks: [framework], limit: 100 });
  }

  /** List all packs for a given industry. */
  listByIndustry(industry: string): CompliancePackModel[] {
    return this.search({ industries: [industry], limit: 100 });
  }

  /** Get featured / top-rated packs. */
  featured(limit = 10): CompliancePackModel[] {
    return this.search({ sort: "rating", limit });
  }
}

// ---------------------------------------------------------------------------
// PackInstaller
// ---------------------------------------------------------------------------

export class PackInstaller {
  private installed = new Map<string, InstallResult>();

  constructor(
    private readonly publisher: PackPublisher,
    private readonly discovery: PackDiscovery,
  ) {}

  /**
   * Install a pack by id/slug, resolving dependencies recursively.
   * Returns the full list of packs that were installed.
   */
  install(
    identifier: string,
    versionRange?: string,
  ): InstallResult[] {
    const pack = this.discovery.findByIdentifier(identifier);
    if (!pack) throw new PackNotFoundError(identifier);

    const results: InstallResult[] = [];
    this.installWithDeps(pack, versionRange, results, new Set());
    return results;
  }

  /** Uninstall a pack by id/slug. */
  uninstall(identifier: string): boolean {
    return this.installed.delete(identifier);
  }

  /** Get all installed packs. */
  getInstalled(): InstallResult[] {
    return Array.from(this.installed.values());
  }

  /** Check if a pack is installed. */
  isInstalled(identifier: string): boolean {
    return this.installed.has(identifier);
  }

  // -- private --

  private installWithDeps(
    pack: CompliancePackModel,
    versionRange: string | undefined,
    results: InstallResult[],
    visited: Set<string>,
  ): void {
    if (visited.has(pack.id)) return;
    visited.add(pack.id);

    // Resolve dependencies first (depth-first)
    for (const dep of pack.dependencies) {
      const depPack = this.discovery.findByIdentifier(dep.packId);
      if (!depPack) {
        throw new DependencyError(
          `Dependency "${dep.packId}" not found for pack ${pack.slug}`,
        );
      }
      this.installWithDeps(depPack, dep.versionRange, results, visited);
    }

    const resolved = pack.resolveVersion(versionRange);

    // Increment download counter
    pack.downloads += 1;

    const result: InstallResult = {
      packId: pack.id,
      version: resolved.version,
      installedAt: new Date(),
      rulesInstalled: pack.rules.length,
    };

    this.installed.set(pack.id, result);
    results.push(result);
  }
}

// ---------------------------------------------------------------------------
// PackRating
// ---------------------------------------------------------------------------

export class PackRating {
  private reviews = new Map<string, Review[]>();

  /** Submit a review for a pack. */
  submitReview(
    packId: string,
    authorId: string,
    rating: 1 | 2 | 3 | 4 | 5,
    title: string,
    body: string,
  ): Review {
    const existing = this.reviews.get(packId) ?? [];
    const duplicate = existing.find((r) => r.authorId === authorId);
    if (duplicate) {
      throw new PublishError(
        `User ${authorId} has already reviewed pack ${packId}`,
      );
    }

    const review: Review = {
      id: randomUUID(),
      packId,
      authorId,
      rating,
      title,
      body,
      createdAt: new Date(),
      updatedAt: new Date(),
      helpful: 0,
    };

    existing.push(review);
    this.reviews.set(packId, existing);
    return review;
  }

  /** Update an existing review. */
  updateReview(
    reviewId: string,
    patch: Partial<Pick<Review, "rating" | "title" | "body">>,
  ): Review {
    for (const reviews of this.reviews.values()) {
      const review = reviews.find((r) => r.id === reviewId);
      if (review) {
        if (patch.rating !== undefined) review.rating = patch.rating;
        if (patch.title !== undefined) review.title = patch.title;
        if (patch.body !== undefined) review.body = patch.body;
        review.updatedAt = new Date();
        return review;
      }
    }
    throw new MarketplaceError(`Review not found: ${reviewId}`, "REVIEW_NOT_FOUND");
  }

  /** Delete a review. */
  deleteReview(reviewId: string): boolean {
    for (const [packId, reviews] of this.reviews.entries()) {
      const idx = reviews.findIndex((r) => r.id === reviewId);
      if (idx !== -1) {
        reviews.splice(idx, 1);
        this.reviews.set(packId, reviews);
        return true;
      }
    }
    return false;
  }

  /** Get all reviews for a pack. */
  getReviews(packId: string): Review[] {
    return this.reviews.get(packId) ?? [];
  }

  /** Get aggregate rating for a pack. */
  getAggregateRating(packId: string): PackRatingAggregate {
    const reviews = this.getReviews(packId);
    const distribution: Record<1 | 2 | 3 | 4 | 5, number> = {
      1: 0,
      2: 0,
      3: 0,
      4: 0,
      5: 0,
    };

    let sum = 0;
    for (const r of reviews) {
      distribution[r.rating] += 1;
      sum += r.rating;
    }

    return {
      packId,
      average: reviews.length > 0 ? sum / reviews.length : 0,
      count: reviews.length,
      distribution,
    };
  }

  /** Mark a review as helpful. */
  markHelpful(reviewId: string): void {
    for (const reviews of this.reviews.values()) {
      const review = reviews.find((r) => r.id === reviewId);
      if (review) {
        review.helpful += 1;
        return;
      }
    }
  }

  /** Get top reviews by helpfulness. */
  topReviews(packId: string, limit = 5): Review[] {
    return this.getReviews(packId)
      .sort((a, b) => b.helpful - a.helpful)
      .slice(0, limit);
  }
}

// ---------------------------------------------------------------------------
// ComplianceMarketplace (facade)
// ---------------------------------------------------------------------------

export class ComplianceMarketplace {
  readonly publisher: PackPublisher;
  readonly discovery: PackDiscovery;
  readonly installer: PackInstaller;
  readonly ratings: PackRating;

  constructor() {
    this.publisher = new PackPublisher();
    this.discovery = new PackDiscovery(this.publisher);
    this.installer = new PackInstaller(this.publisher, this.discovery);
    this.ratings = new PackRating();
  }

  // -- Publishing ----------------------------------------------------------

  /** Create, register, and optionally publish a new compliance pack. */
  publishPack(
    input: PublishInput,
    version = "1.0.0",
    checksum?: string,
  ): CompliancePackModel {
    const pack = new CompliancePackModel(input);
    this.publisher.register(pack);
    pack.publishVersion(version, checksum ?? randomUUID());
    this.syncRating(pack);
    return pack;
  }

  /** Publish a new version of an existing pack. */
  publishNewVersion(
    packId: string,
    version: string,
    checksum?: string,
    tarballUrl?: string,
  ): CompliancePackModel {
    const pack = this.publisher.getPack(packId);
    if (!pack) throw new PackNotFoundError(packId);
    pack.publishVersion(version, checksum ?? randomUUID(), tarballUrl);
    this.syncRating(pack);
    return pack;
  }

  /** Deprecate a pack. */
  deprecatePack(packId: string): void {
    const pack = this.publisher.getPack(packId);
    if (!pack) throw new PackNotFoundError(packId);
    pack.status = "deprecated";
    pack.updatedAt = new Date();
  }

  /** Yank (unpublish) a specific version. */
  yankVersion(packId: string, version: string): void {
    const pack = this.publisher.getPack(packId);
    if (!pack) throw new PackNotFoundError(packId);
    pack.versions = pack.versions.filter((v) => v.version !== version);
    if (pack.versions.length === 0) {
      pack.status = "yanked";
      pack.latestVersion = "";
    } else {
      const sorted = sortVersionsDescending(pack.versions);
      pack.latestVersion = sorted[0].version;
    }
    pack.updatedAt = new Date();
  }

  // -- Discovery -----------------------------------------------------------

  /** Search packs with filters. */
  search(filters?: DiscoveryFilter): CompliancePackModel[] {
    return this.discovery.search(filters);
  }

  /** Get a pack by id or slug. */
  getPack(identifier: string): CompliancePackModel | undefined {
    return this.discovery.findByIdentifier(identifier);
  }

  /** List packs for a framework. */
  listByFramework(framework: string): CompliancePackModel[] {
    return this.discovery.listByFramework(framework);
  }

  /** List packs for an industry. */
  listByIndustry(industry: string): CompliancePackModel[] {
    return this.discovery.listByIndustry(industry);
  }

  /** Get featured packs. */
  featured(limit?: number): CompliancePackModel[] {
    return this.discovery.featured(limit);
  }

  // -- Installation --------------------------------------------------------

  /** Install a pack by id or slug. */
  install(identifier: string, versionRange?: string): InstallResult[] {
    return this.installer.install(identifier, versionRange);
  }

  /** Uninstall a pack. */
  uninstall(identifier: string): boolean {
    return this.installer.uninstall(identifier);
  }

  /** List installed packs. */
  installedPacks(): InstallResult[] {
    return this.installer.getInstalled();
  }

  // -- Ratings -------------------------------------------------------------

  /** Submit a review. */
  reviewPack(
    packId: string,
    authorId: string,
    rating: 1 | 2 | 3 | 4 | 5,
    title: string,
    body: string,
  ): Review {
    const review = this.ratings.submitReview(packId, authorId, rating, title, body);
    const pack = this.publisher.getPack(packId);
    if (pack) this.syncRating(pack);
    return review;
  }

  /** Get reviews for a pack. */
  getReviews(packId: string): Review[] {
    return this.ratings.getReviews(packId);
  }

  /** Get aggregate rating. */
  getRating(packId: string): PackRatingAggregate {
    return this.ratings.getAggregateRating(packId);
  }

  // -- Analytics -----------------------------------------------------------

  /** Get overall marketplace statistics. */
  stats(): MarketplaceStats {
    const packs = this.publisher.getAllPacks();
    const totalDownloads = packs.reduce((sum, p) => sum + p.downloads, 0);
    const totalRules = packs.reduce((sum, p) => sum + p.rules.length, 0);
    let totalReviews = 0;
    for (const pack of packs) {
      totalReviews += this.ratings.getReviews(pack.id).length;
    }
    return {
      totalPacks: packs.length,
      totalDownloads,
      totalRules,
      totalReviews,
    };
  }

  // -- private -------------------------------------------------------------

  private syncRating(pack: CompliancePackModel): void {
    const agg = this.ratings.getAggregateRating(pack.id);
    pack.rating = agg;
    pack.updatedAt = new Date();
  }
}
