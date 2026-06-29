/**
 * @grc-claw/compliance-automation-marketplace
 *
 * Compliance automation marketplace for sharing, discovering, and monetizing
 * compliance automations with ratings, versioning, and validation.
 *
 * @example
 * ```ts
 * import { ComplianceAutomationMarketplace } from "@grc-claw/compliance-automation-marketplace";
 *
 * const marketplace = new ComplianceAutomationMarketplace();
 *
 * // Publish an automation
 * const automation = await marketplace.publisher.publish({
 *   name: "SOC2 Access Review Automation",
 *   description: "Automates quarterly access reviews for SOC 2 CC6.1",
 *   author: { id: "vendor-1", name: "SecurityCorp" },
 *   frameworks: ["SOC2"],
 *   industries: ["technology", "saas"],
 *   useCases: ["access_review", "quarterly_audit"],
 *   price: 0,
 *   license: "MIT",
 * });
 *
 * // Discover automations
 * const results = await marketplace.discovery.search({
 *   frameworks: ["SOC2"],
 *   query: "access review",
 * });
 *
 * // Rate an automation
 * await marketplace.rating.rate({
 *   automationId: automation.id,
 *   reviewerId: "user-1",
 *   score: 5,
 *   comment: "Excellent automation, saved us hours",
 * });
 *
 * // Install an automation
 * const installed = await marketplace.installer.install(automation.id, {
 *   version: "1.0.0",
 *   targetEnvironment: "production",
 * });
 * ```
 */

import { randomUUID, createHash } from "node:crypto";

// ---------------------------------------------------------------------------
// Types & Enums
// ---------------------------------------------------------------------------

export type AutomationStatus = "draft" | "published" | "deprecated" | "yanked";
export type AutomationTier = "free" | "basic" | "professional" | "enterprise";
export type LicenseType = "MIT" | "Apache-2.0" | "GPL-3.0" | "Proprietary" | "Custom";
export type Framework = "SOC2" | "ISO27001" | "NIST_CSF" | "HIPAA" | "PCI_DSS" | "GDPR" | "CIS" | "ISO42001" | "NIST_AI_RMF";
export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type ValidationStatus = "pending" | "passed" | "failed" | "skipped";

export interface AutomationAuthor {
  id: string;
  name: string;
  email?: string;
  url?: string;
  avatarUrl?: string;
}

export interface AutomationVersion {
  version: string;
  publishedAt: Date;
  checksum: string;
  tarballUrl?: string;
  changelog?: string;
}

export interface AutomationDependency {
  automationId: string;
  versionRange: string;
  optional?: boolean;
}

export interface AutomationMetadata {
  frameworks: Framework[];
  industries: string[];
  useCases: string[];
  tags: string[];
  minPlatformVersion?: string;
}

export interface AutomationRatingAggregate {
  automationId: string;
  average: number;
  count: number;
  distribution: Record<1 | 2 | 3 | 4 | 5, number>;
}

export interface Review {
  id: string;
  automationId: string;
  reviewerId: string;
  reviewerName: string;
  score: 1 | 2 | 3 | 4 | 5;
  title: string;
  comment: string;
  createdAt: Date;
  updatedAt: Date;
  helpful: number;
  verified: boolean;
}

export interface ComplianceRule {
  id: string;
  name: string;
  description: string;
  framework: Framework;
  controlIds: string[];
  severity: Severity;
  logic: Record<string, unknown>;
  remediation?: string;
  references?: string[];
}

export interface Automation {
  id: string;
  name: string;
  slug: string;
  description: string;
  longDescription?: string;
  author: AutomationAuthor;
  status: AutomationStatus;
  tier: AutomationTier;
  price: number;
  license: LicenseType;
  metadata: AutomationMetadata;
  versions: AutomationVersion[];
  latestVersion: string;
  dependencies: AutomationDependency[];
  rules: ComplianceRule[];
  downloads: number;
  rating: AutomationRatingAggregate;
  validationStatus: ValidationStatus;
  createdAt: Date;
  updatedAt: Date;
}

export interface PublishInput {
  name: string;
  description: string;
  longDescription?: string;
  author: AutomationAuthor;
  frameworks: Framework[];
  industries?: string[];
  useCases?: string[];
  tags?: string[];
  tier?: AutomationTier;
  price?: number;
  license?: LicenseType;
  rules?: ComplianceRule[];
  dependencies?: AutomationDependency[];
  minPlatformVersion?: string;
}

export interface SearchFilters {
  query?: string;
  frameworks?: Framework[];
  industries?: string[];
  useCases?: string[];
  tags?: string[];
  tier?: AutomationTier;
  minRating?: number;
  maxPrice?: number;
  status?: AutomationStatus;
  sortBy?: "relevance" | "rating" | "downloads" | "newest" | "price_asc" | "price_desc";
  limit?: number;
  offset?: number;
}

export interface RateInput {
  automationId: string;
  reviewerId: string;
  reviewerName: string;
  score: 1 | 2 | 3 | 4 | 5;
  title: string;
  comment: string;
}

export interface InstallInput {
  version?: string;
  targetEnvironment?: string;
  config?: Record<string, unknown>;
}

export interface InstallResult {
  automationId: string;
  version: string;
  installedAt: Date;
  rulesInstalled: number;
  config: Record<string, unknown>;
}

export interface ValidationResult {
  automationId: string;
  status: ValidationStatus;
  passedChecks: string[];
  failedChecks: string[];
  warnings: string[];
  validatedAt: Date;
  duration: number;
}

export interface MarketplaceStats {
  totalAutomations: number;
  automationsByFramework: Record<Framework, number>;
  automationsByTier: Record<AutomationTier, number>;
  totalDownloads: number;
  totalReviews: number;
  averageRating: number;
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class MarketplaceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "MarketplaceError";
  }
}

export class AutomationNotFoundError extends MarketplaceError {
  constructor(id: string) {
    super(`Automation not found: ${id}`, "AUTOMATION_NOT_FOUND", { id });
    this.name = "AutomationNotFoundError";
  }
}

export class ValidationError extends MarketplaceError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, "VALIDATION_ERROR", details);
    this.name = "ValidationError";
  }
}

export class DuplicateError extends MarketplaceError {
  constructor(message: string) {
    super(message, "DUPLICATE");
    this.name = "DuplicateError";
  }
}

export class DependencyError extends MarketplaceError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(message, "DEPENDENCY_ERROR", details);
    this.name = "DependencyError";
  }
}

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function hashChecksum(data: unknown): string {
  const payload = JSON.stringify(data, Object.keys(data as Record<string, unknown>).sort());
  return `sha256:${createHash("sha256").update(payload).digest("hex")}`;
}

function parseVersion(version: string): [number, number, number] {
  const parts = version.split(".").map(Number) as [number, number, number];
  if (parts.some((p) => isNaN(p) || p < 0)) {
    throw new ValidationError(`Invalid version format: ${version}`);
  }
  return parts;
}

function satisfiesRange(version: string, range: string): boolean {
  const [vMaj, vMin, vPat] = parseVersion(version);
  const rangeParts = range.replace(/\s/g, "").split(",");

  for (const part of rangeParts) {
    const trimmed = part.trim();
    if (trimmed.startsWith(">=")) {
      const [rMaj, rMin, rPat] = parseVersion(trimmed.slice(2));
      if (vMaj < rMaj || (vMaj === rMaj && vMin < rMin) || (vMaj === rMaj && vMin === rMin && vPat < rPat)) return false;
    } else if (trimmed.startsWith("^")) {
      const [rMaj, rMin, rPat] = parseVersion(trimmed.slice(1));
      if (vMaj !== rMaj || vMin < rMin || (vMin === rMin && vPat < rPat)) return false;
    } else if (trimmed.startsWith("~")) {
      const [rMaj, rMin, rPat] = parseVersion(trimmed.slice(1));
      if (vMaj !== rMaj || vMin !== rMin || vPat < rPat) return false;
    } else if (trimmed.includes("-")) {
      const [low, high] = trimmed.split("-").map((v) => parseVersion(v));
      const [hMaj, hMin, hPat] = high;
      if (vMaj < low[0] || (vMaj === low[0] && vMin < low[1]) || (vMaj === low[0] && vMin === low[1] && vPat < low[2])) return false;
      if (vMaj > hMaj || (vMaj === hMaj && vMin > hMin) || (vMaj === hMaj && vMin === hMin && vPat > hPat)) return false;
    } else if (trimmed === "*") {
      return true;
    } else {
      if (version !== trimmed) return false;
    }
  }
  return true;
}

function createEmptyRating(automationId: string): AutomationRatingAggregate {
  return {
    automationId,
    average: 0,
    count: 0,
    distribution: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 },
  };
}

// ---------------------------------------------------------------------------
// AutomationPublisher
// ---------------------------------------------------------------------------

export class AutomationPublisher {
  private automations = new Map<string, Automation>();

  async publish(input: PublishInput): Promise<Automation> {
    const existingBySlug = [...this.automations.values()].find(
      (a) => slugify(a.name) === slugify(input.name) && a.author.id === input.author.id
    );
    if (existingBySlug) {
      throw new DuplicateError(`Automation with name "${input.name}" already exists for this author`);
    }

    const now = new Date();
    const id = `ca-${randomUUID()}`;
    const slug = slugify(input.name);
    const version = "1.0.0";

    const automation: Automation = {
      id,
      name: input.name,
      slug,
      description: input.description,
      longDescription: input.longDescription,
      author: input.author,
      status: "published",
      tier: input.tier ?? "free",
      price: input.price ?? 0,
      license: input.license ?? "MIT",
      metadata: {
        frameworks: input.frameworks,
        industries: input.industries ?? [],
        useCases: input.useCases ?? [],
        tags: input.tags ?? [],
        minPlatformVersion: input.minPlatformVersion,
      },
      versions: [
        {
          version,
          publishedAt: now,
          checksum: hashChecksum(input),
          changelog: "Initial release",
        },
      ],
      latestVersion: version,
      dependencies: input.dependencies ?? [],
      rules: input.rules ?? [],
      downloads: 0,
      rating: createEmptyRating(id),
      validationStatus: "pending",
      createdAt: now,
      updatedAt: now,
    };

    this.automations.set(id, automation);
    return { ...automation };
  }

  async update(
    automationId: string,
    patch: Partial<Pick<PublishInput, "description" | "longDescription" | "tags" | "tier" | "price" | "license">>
  ): Promise<Automation> {
    const automation = this.automations.get(automationId);
    if (!automation) throw new AutomationNotFoundError(automationId);

    if (patch.description !== undefined) automation.description = patch.description;
    if (patch.longDescription !== undefined) automation.longDescription = patch.longDescription;
    if (patch.tags !== undefined) automation.metadata.tags = patch.tags;
    if (patch.tier !== undefined) automation.tier = patch.tier;
    if (patch.price !== undefined) automation.price = patch.price;
    if (patch.license !== undefined) automation.license = patch.license;
    automation.updatedAt = new Date();

    return { ...automation };
  }

  async publishVersion(
    automationId: string,
    input: { version: string; changelog?: string; rules?: ComplianceRule[]; dependencies?: AutomationDependency[] }
  ): Promise<Automation> {
    const automation = this.automations.get(automationId);
    if (!automation) throw new AutomationNotFoundError(automationId);

    const existingVersions = automation.versions.map((v) => v.version);
    if (existingVersions.includes(input.version)) {
      throw new DuplicateError(`Version ${input.version} already exists`);
    }

    const latestParts = parseVersion(automation.latestVersion);
    const newParts = parseVersion(input.version);
    if (newParts[0] < latestParts[0] || (newParts[0] === latestParts[0] && newParts[1] < latestParts[1]) || (newParts[0] === latestParts[0] && newParts[1] === latestParts[1] && newParts[2] < latestParts[2])) {
      throw new ValidationError(`Version ${input.version} is older than current latest ${automation.latestVersion}`);
    }

    automation.versions.push({
      version: input.version,
      publishedAt: new Date(),
      checksum: hashChecksum(input),
      changelog: input.changelog,
    });

    automation.latestVersion = input.version;
    if (input.rules) automation.rules = input.rules;
    if (input.dependencies) automation.dependencies = input.dependencies;
    automation.updatedAt = new Date();

    return { ...automation };
  }

  async deprecate(automationId: string, reason?: string): Promise<Automation> {
    const automation = this.automations.get(automationId);
    if (!automation) throw new AutomationNotFoundError(automationId);
    automation.status = "deprecated";
    automation.updatedAt = new Date();
    return { ...automation };
  }

  async yank(automationId: string, version?: string): Promise<void> {
    const automation = this.automations.get(automationId);
    if (!automation) throw new AutomationNotFoundError(automationId);

    if (version) {
      const idx = automation.versions.findIndex((v) => v.version === version);
      if (idx === -1) throw new ValidationError(`Version ${version} not found`);
      automation.versions.splice(idx, 1);
    } else {
      automation.status = "yanked";
    }
    automation.updatedAt = new Date();
  }

  get(id: string): Automation | undefined {
    return this.automations.has(id) ? { ...this.automations.get(id)! } : undefined;
  }

  getAll(): Automation[] {
    return [...this.automations.values()].map((a) => ({ ...a }));
  }

  getByAuthor(authorId: string): Automation[] {
    return this.getAll().filter((a) => a.author.id === authorId);
  }

  list(): Automation[] {
    return this.getAll();
  }

  /** Internal access for other sub-modules */
  _store(): Map<string, Automation> {
    return this.automations;
  }
}

// ---------------------------------------------------------------------------
// AutomationDiscovery
// ---------------------------------------------------------------------------

export class AutomationDiscovery {
  constructor(private publisher: AutomationPublisher) {}

  async search(filters: SearchFilters): Promise<{ results: Automation[]; total: number }> {
    let items = this.publisher.list().filter((a) => a.status === "published");

    if (filters.query) {
      const q = filters.query.toLowerCase();
      items = items.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          a.description.toLowerCase().includes(q) ||
          a.metadata.tags.some((t) => t.toLowerCase().includes(q))
      );
    }

    if (filters.frameworks?.length) {
      items = items.filter((a) => filters.frameworks!.some((f) => a.metadata.frameworks.includes(f)));
    }

    if (filters.industries?.length) {
      items = items.filter((a) => filters.industries!.some((i) => a.metadata.industries.includes(i)));
    }

    if (filters.useCases?.length) {
      items = items.filter((a) => filters.useCases!.some((u) => a.metadata.useCases.includes(u)));
    }

    if (filters.tags?.length) {
      items = items.filter((a) => filters.tags!.some((t) => a.metadata.tags.includes(t)));
    }

    if (filters.tier) {
      items = items.filter((a) => a.tier === filters.tier);
    }

    if (filters.minRating !== undefined) {
      items = items.filter((a) => a.rating.average >= filters.minRating!);
    }

    if (filters.maxPrice !== undefined) {
      items = items.filter((a) => a.price <= filters.maxPrice!);
    }

    const total = items.length;

    const sortBy = filters.sortBy ?? "relevance";
    switch (sortBy) {
      case "rating":
        items.sort((a, b) => b.rating.average - a.rating.average);
        break;
      case "downloads":
        items.sort((a, b) => b.downloads - a.downloads);
        break;
      case "newest":
        items.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
        break;
      case "price_asc":
        items.sort((a, b) => a.price - b.price);
        break;
      case "price_desc":
        items.sort((a, b) => b.price - a.price);
        break;
    }

    const offset = filters.offset ?? 0;
    const limit = filters.limit ?? 20;
    items = items.slice(offset, offset + limit);

    return { results: items.map((a) => ({ ...a })), total };
  }

  async getByFramework(framework: Framework): Promise<Automation[]> {
    return this.search({ frameworks: [framework] }).then((r) => r.results);
  }

  async getByIndustry(industry: string): Promise<Automation[]> {
    return this.search({ industries: [industry] }).then((r) => r.results);
  }

  async getPopular(limit = 10): Promise<Automation[]> {
    return this.search({ sortBy: "downloads", limit }).then((r) => r.results);
  }

  async getTopRated(limit = 10): Promise<Automation[]> {
    return this.search({ sortBy: "rating", minRating: 1, limit }).then((r) => r.results);
  }

  async getFeatured(limit = 5): Promise<Automation[]> {
    return this.search({ sortBy: "rating", minRating: 4, limit }).then((r) => r.results);
  }

  async getCategories(): Promise<{ frameworks: Framework[]; industries: string[]; useCases: string[]; tags: string[] }> {
    const all = this.publisher.list().filter((a) => a.status === "published");
    const frameworks = new Set<Framework>();
    const industries = new Set<string>();
    const useCases = new Set<string>();
    const tags = new Set<string>();

    for (const a of all) {
      a.metadata.frameworks.forEach((f) => frameworks.add(f));
      a.metadata.industries.forEach((i) => industries.add(i));
      a.metadata.useCases.forEach((u) => useCases.add(u));
      a.metadata.tags.forEach((t) => tags.add(t));
    }

    return {
      frameworks: [...frameworks],
      industries: [...industries],
      useCases: [...useCases],
      tags: [...tags],
    };
  }

  async getStats(): Promise<MarketplaceStats> {
    const all = this.publisher.list().filter((a) => a.status === "published");
    const automationsByFramework = {} as Record<Framework, number>;
    const automationsByTier = {} as Record<AutomationTier, number>;
    let totalDownloads = 0;
    let totalReviews = 0;
    let totalRating = 0;

    for (const a of all) {
      for (const f of a.metadata.frameworks) {
        automationsByFramework[f] = (automationsByFramework[f] ?? 0) + 1;
      }
      automationsByTier[a.tier] = (automationsByTier[a.tier] ?? 0) + 1;
      totalDownloads += a.downloads;
      totalReviews += a.rating.count;
      totalRating += a.rating.average * a.rating.count;
    }

    return {
      totalAutomations: all.length,
      automationsByFramework,
      automationsByTier,
      totalDownloads,
      totalReviews,
      averageRating: totalReviews > 0 ? totalRating / totalReviews : 0,
    };
  }

  async resolveDependencies(automationId: string, version?: string): Promise<Automation[]> {
    const automation = this.publisher.get(automationId);
    if (!automation) throw new AutomationNotFoundError(automationId);

    const resolved: Automation[] = [];
    const visited = new Set<string>();

    const resolve = (id: string, range: string) => {
      if (visited.has(id)) return;
      visited.add(id);

      const dep = this.publisher.get(id);
      if (!dep) {
        throw new DependencyError(`Dependency not found: ${id}`);
      }

      const targetVersion = version ?? dep.latestVersion;
      const matchingVersion = dep.versions.find((v) => satisfiesRange(v.version, range));
      if (!matchingVersion) {
        throw new DependencyError(`No version of ${id} satisfies ${range}`);
      }

      resolved.push(dep);

      for (const d of dep.dependencies) {
        resolve(d.automationId, d.versionRange);
      }
    };

    const targetVersion = version ?? automation.latestVersion;
    const target = automation.versions.find((v) => v.version === targetVersion);
    if (!target) throw new ValidationError(`Version ${targetVersion} not found for ${automationId}`);

    for (const dep of automation.dependencies) {
      resolve(dep.automationId, dep.versionRange);
    }

    return resolved;
  }
}

// ---------------------------------------------------------------------------
// AutomationRating
// ---------------------------------------------------------------------------

export class AutomationRating {
  private reviews = new Map<string, Review[]>();
  private ratings = new Map<string, AutomationRatingAggregate>();

  constructor(private publisher: AutomationPublisher) {}

  async rate(input: RateInput): Promise<Review> {
    const automation = this.publisher.get(input.automationId);
    if (!automation) throw new AutomationNotFoundError(input.automationId);

    if (input.score < 1 || input.score > 5) {
      throw new ValidationError("Score must be between 1 and 5");
    }

    const existingReviews = this.reviews.get(input.automationId) ?? [];
    const existing = existingReviews.find((r) => r.reviewerId === input.reviewerId);
    if (existing) {
      throw new DuplicateError(`User ${input.reviewerId} has already reviewed this automation`);
    }

    const now = new Date();
    const review: Review = {
      id: `rev-${randomUUID()}`,
      automationId: input.automationId,
      reviewerId: input.reviewerId,
      reviewerName: input.reviewerName,
      score: input.score,
      title: input.title,
      comment: input.comment,
      createdAt: now,
      updatedAt: now,
      helpful: 0,
      verified: false,
    };

    if (!this.reviews.has(input.automationId)) {
      this.reviews.set(input.automationId, []);
    }
    this.reviews.get(input.automationId)!.push(review);

    this.recomputeRating(input.automationId);

    return { ...review };
  }

  async updateReview(reviewId: string, automationId: string, patch: Partial<Pick<Review, "score" | "title" | "comment">>): Promise<Review> {
    const reviews = this.reviews.get(automationId);
    if (!reviews) throw new AutomationNotFoundError(automationId);

    const review = reviews.find((r) => r.id === reviewId);
    if (!review) throw new ValidationError(`Review ${reviewId} not found`);

    if (patch.score !== undefined) review.score = patch.score;
    if (patch.title !== undefined) review.title = patch.title;
    if (patch.comment !== undefined) review.comment = patch.comment;
    review.updatedAt = new Date();

    this.recomputeRating(automationId);
    return { ...review };
  }

  async deleteReview(reviewId: string, automationId: string): Promise<void> {
    const reviews = this.reviews.get(automationId);
    if (!reviews) throw new AutomationNotFoundError(automationId);

    const idx = reviews.findIndex((r) => r.id === reviewId);
    if (idx === -1) throw new ValidationError(`Review ${reviewId} not found`);

    reviews.splice(idx, 1);
    this.recomputeRating(automationId);
  }

  async markHelpful(reviewId: string, automationId: string): Promise<Review> {
    const reviews = this.reviews.get(automationId);
    if (!reviews) throw new AutomationNotFoundError(automationId);

    const review = reviews.find((r) => r.id === reviewId);
    if (!review) throw new ValidationError(`Review ${reviewId} not found`);

    review.helpful += 1;
    return { ...review };
  }

  async getReviews(automationId: string, options?: { sortBy?: "newest" | "oldest" | "helpful" | "highest" | "lowest"; limit?: number }): Promise<Review[]> {
    const reviews = this.reviews.get(automationId) ?? [];
    const sorted = [...reviews];

    switch (options?.sortBy) {
      case "newest":
        sorted.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
        break;
      case "oldest":
        sorted.sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime());
        break;
      case "helpful":
        sorted.sort((a, b) => b.helpful - a.helpful);
        break;
      case "highest":
        sorted.sort((a, b) => b.score - a.score);
        break;
      case "lowest":
        sorted.sort((a, b) => a.score - b.score);
        break;
      default:
        sorted.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
    }

    const limit = options?.limit ?? 20;
    return sorted.slice(0, limit).map((r) => ({ ...r }));
  }

  async getRating(automationId: string): Promise<AutomationRatingAggregate> {
    return this.ratings.get(automationId) ?? createEmptyRating(automationId);
  }

  async getReviewCount(automationId: string): Promise<number> {
    return (this.reviews.get(automationId) ?? []).length;
  }

  private recomputeRating(automationId: string): void {
    const reviews = this.reviews.get(automationId) ?? [];
    const distribution: Record<1 | 2 | 3 | 4 | 5, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    let total = 0;

    for (const r of reviews) {
      distribution[r.score] += 1;
      total += r.score;
    }

    this.ratings.set(automationId, {
      automationId,
      average: reviews.length > 0 ? total / reviews.length : 0,
      count: reviews.length,
      distribution,
    });
  }
}

// ---------------------------------------------------------------------------
// AutomationInstaller
// ---------------------------------------------------------------------------

export class AutomationInstaller {
  private installed = new Map<string, InstallResult>();

  constructor(private publisher: AutomationPublisher) {}

  async install(automationId: string, input?: InstallInput): Promise<InstallResult> {
    const automation = this.publisher.get(automationId);
    if (!automation) throw new AutomationNotFoundError(automationId);

    if (automation.status !== "published") {
      throw new ValidationError(`Cannot install automation with status "${automation.status}"`);
    }

    const version = input?.version ?? automation.latestVersion;
    const versionEntry = automation.versions.find((v) => v.version === version);
    if (!versionEntry) {
      throw new ValidationError(`Version ${version} not found for automation ${automationId}`);
    }

    // Validate dependencies
    if (automation.dependencies.length > 0) {
      for (const dep of automation.dependencies) {
        const depAutomation = this.publisher.get(dep.automationId);
        if (!depAutomation) {
          throw new DependencyError(`Required dependency not found: ${dep.automationId}`);
        }
        const matchingVersion = depAutomation.versions.find((v) => satisfiesRange(v.version, dep.versionRange));
        if (!matchingVersion) {
          throw new DependencyError(
            `Dependency ${dep.automationId} has no version satisfying ${dep.versionRange}`,
            { required: dep.versionRange, available: depAutomation.versions.map((v) => v.version) }
          );
        }
      }
    }

    if (automation.tier !== "free" && automation.price > 0) {
      // In a real implementation, this would trigger payment processing
    }

    // Increment downloads
    automation.downloads += 1;
    this.publisher._store().set(automationId, automation);

    const result: InstallResult = {
      automationId,
      version,
      installedAt: new Date(),
      rulesInstalled: automation.rules.length,
      config: input?.config ?? {},
    };

    this.installed.set(`${automationId}@${version}`, result);
    return { ...result };
  }

  async uninstall(automationId: string): Promise<void> {
    const keys = [...this.installed.keys()].filter((k) => k.startsWith(`${automationId}@`));
    for (const key of keys) {
      this.installed.delete(key);
    }
  }

  async isInstalled(automationId: string): Promise<boolean> {
    return [...this.installed.keys()].some((k) => k.startsWith(`${automationId}@`));
  }

  async getInstalledVersion(automationId: string): Promise<InstallResult | undefined> {
    const key = [...this.installed.keys()].find((k) => k.startsWith(`${automationId}@`));
    return key ? { ...this.installed.get(key)! } : undefined;
  }

  async listInstalled(): Promise<InstallResult[]> {
    return [...this.installed.values()].map((r) => ({ ...r }));
  }

  async update(automationId: string): Promise<InstallResult> {
    const existing = await this.getInstalledVersion(automationId);
    if (!existing) {
      throw new ValidationError(`Automation ${automationId} is not installed`);
    }

    const automation = this.publisher.get(automationId);
    if (!automation) throw new AutomationNotFoundError(automationId);

    if (existing.version === automation.latestVersion) {
      return existing;
    }

    return this.install(automationId, {
      version: automation.latestVersion,
      config: existing.config,
    });
  }
}

// ---------------------------------------------------------------------------
// ComplianceAutomationMarketplace (Facade)
// ---------------------------------------------------------------------------

/**
 * Main marketplace facade that orchestrates publishing, discovery, ratings,
 * and installation of compliance automations.
 */
export class ComplianceAutomationMarketplace {
  readonly publisher: AutomationPublisher;
  readonly discovery: AutomationDiscovery;
  readonly rating: AutomationRating;
  readonly installer: AutomationInstaller;

  constructor() {
    this.publisher = new AutomationPublisher();
    this.discovery = new AutomationDiscovery(this.publisher);
    this.rating = new AutomationRating(this.publisher);
    this.installer = new AutomationInstaller(this.publisher);
  }

  /**
   * Register an automation for validation.
   * Returns a validation result that can be polled for status.
   */
  async validateAutomation(automationId: string): Promise<ValidationResult> {
    const automation = this.publisher.get(automationId);
    if (!automation) throw new AutomationNotFoundError(automationId);

    const start = Date.now();
    const passedChecks: string[] = [];
    const failedChecks: string[] = [];
    const warnings: string[] = [];

    // Check: has rules
    if (automation.rules.length > 0) {
      passedChecks.push("has_rules");
    } else {
      warnings.push("no_rules_defined");
    }

    // Check: has description
    if (automation.description && automation.description.length >= 10) {
      passedChecks.push("has_description");
    } else {
      failedChecks.push("insufficient_description");
    }

    // Check: has frameworks
    if (automation.metadata.frameworks.length > 0) {
      passedChecks.push("has_frameworks");
    } else {
      failedChecks.push("no_frameworks");
    }

    // Check: dependencies exist
    for (const dep of automation.dependencies) {
      const depAutomation = this.publisher.get(dep.automationId);
      if (depAutomation) {
        passedChecks.push(`dependency_${dep.automationId}_exists`);
      } else {
        failedChecks.push(`dependency_${dep.automationId}_missing`);
      }
    }

    // Check: version format
    try {
      parseVersion(automation.latestVersion);
      passedChecks.push("valid_version_format");
    } catch {
      failedChecks.push("invalid_version_format");
    }

    const status: ValidationStatus = failedChecks.length === 0 ? "passed" : "failed";

    // Update automation validation status
    automation.validationStatus = status;
    this.publisher._store().set(automationId, automation);

    return {
      automationId,
      status,
      passedChecks,
      failedChecks,
      warnings,
      validatedAt: new Date(),
      duration: Date.now() - start,
    };
  }

  /**
   * Get complete marketplace statistics.
   */
  async getStats(): Promise<MarketplaceStats> {
    return this.discovery.getStats();
  }

  /**
   * Bulk import automations from a JSON-like source.
   */
  async bulkImport(automations: PublishInput[]): Promise<{ published: number; errors: string[] }> {
    let published = 0;
    const errors: string[] = [];

    for (const input of automations) {
      try {
        await this.publisher.publish(input);
        published++;
      } catch (err) {
        errors.push(err instanceof Error ? err.message : String(err));
      }
    }

    return { published, errors };
  }

  /**
   * Export all published automations as serializable data.
   */
  async exportAll(): Promise<Automation[]> {
    return this.publisher.list().filter((a) => a.status === "published");
  }
}
