// ============================================================================
// @grc-claw/compliance-automation-marketplace
// Compliance automation marketplace for sharing, discovering, and monetizing
// compliance automations across frameworks, industries, and use cases.
// ============================================================================

// ---------------------------------------------------------------------------
// Types & Interfaces
// ---------------------------------------------------------------------------

export interface Automation {
  id: string;
  name: string;
  description: string;
  author: string;
  version: string;
  framework: ComplianceFramework[];
  industry: string[];
  useCase: string[];
  tags: string[];
  license: string;
  pricing: PricingModel;
  dependencies: AutomationDependency[];
  entryPoint: string;
  readme: string;
  icon?: string;
  repository?: string;
  homepage?: string;
  publishedAt: Date;
  updatedAt: Date;
  downloads: number;
  status: AutomationStatus;
  validation?: ValidationResult;
}

export interface AutomationVersion {
  version: string;
  automationId: string;
  publishedAt: Date;
  changelog: string;
  checksum: string;
  deprecated: boolean;
}

export interface AutomationDependency {
  id: string;
  name: string;
  versionRange: string;
  optional: boolean;
}

export interface PricingModel {
  type: "free" | "paid" | "freemium";
  price?: number;
  currency?: string;
  trialPeriodDays?: number;
}

export interface AutomationReview {
  id: string;
  automationId: string;
  author: string;
  rating: number;
  title: string;
  content: string;
  version: string;
  createdAt: Date;
  updatedAt: Date;
  helpful: number;
  verifiedPurchase: boolean;
}

export interface AutomationRatingSummary {
  automationId: string;
  averageRating: number;
  totalReviews: number;
  distribution: Record<number, number>;
}

export interface AutomationSearchQuery {
  query?: string;
  framework?: ComplianceFramework[];
  industry?: string[];
  useCase?: string[];
  tags?: string[];
  pricing?: "free" | "paid" | "freemium";
  minRating?: number;
  sortBy?: "relevance" | "rating" | "downloads" | "newest" | "updated";
  limit?: number;
  offset?: number;
}

export interface SearchResult {
  automations: Automation[];
  total: number;
  hasMore: boolean;
}

export interface PublisherProfile {
  id: string;
  name: string;
  email: string;
  bio: string;
  avatar?: string;
  automations: string[];
  totalDownloads: number;
  averageRating: number;
  joinedAt: Date;
}

export interface InstallationResult {
  automationId: string;
  version: string;
  installedAt: Date;
  path: string;
  resolvedDependencies: ResolvedDependency[];
}

export interface ResolvedDependency {
  id: string;
  name: string;
  version: string;
  resolvedFrom: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationItem[];
  warnings: ValidationWarning[];
  checkedAt: Date;
}

export interface ValidationItem {
  code: string;
  message: string;
  file?: string;
  line?: number;
}

export interface ValidationWarning {
  code: string;
  message: string;
  suggestion?: string;
}

export type ComplianceFramework =
  | "ISO27001"
  | "SOC2"
  | "NIST_CSF"
  | "NIST_800_53"
  | "PCI_DSS"
  | "HIPAA"
  | "GDPR"
  | "CCPA"
  | "ISO42001"
  | "ISO27701"
  | "CIS"
  | "COBIT"
  | "CUSTOM";

export type AutomationStatus =
  | "draft"
  | "published"
  | "deprecated"
  | "archived"
  | "suspended";

export type MarketplaceEvent =
  | { type: "automation:published"; automationId: string; author: string }
  | { type: "automation:updated"; automationId: string; version: string }
  | { type: "automation:installed"; automationId: string; installedBy: string }
  | { type: "automation:reviewed"; automationId: string; rating: number }
  | { type: "automation:downloaded"; automationId: string }
  | { type: "automation:deprecated"; automationId: string }
  | { type: "validation:completed"; automationId: string; valid: boolean };

export interface MarketplaceConfig {
  storagePath: string;
  maxUploadSizeMb: number;
  requiredFrameworks: boolean;
  enableMonetization: boolean;
  validationTimeoutMs: number;
  maxDependencies: number;
  reviewCooldownMs: number;
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class MarketplaceError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: Record<string, unknown>,
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

export class VersionConflictError extends MarketplaceError {
  constructor(id: string, version: string) {
    super(
      `Version conflict for automation ${id}: version ${version} already exists`,
      "VERSION_CONFLICT",
      { id, version },
    );
    this.name = "VersionConflictError";
  }
}

export class ValidationError extends MarketplaceError {
  constructor(errors: Array<{ code: string; message: string }>) {
    super("Validation failed", "VALIDATION_FAILED", { errors });
    this.name = "ValidationError";
  }
}

export class DependencyResolutionError extends MarketplaceError {
  constructor(dep: string, reason: string) {
    super(
      `Failed to resolve dependency ${dep}: ${reason}`,
      "DEPENDENCY_RESOLUTION_FAILED",
      { dep, reason },
    );
    this.name = "DependencyResolutionError";
  }
}

export class AccessDeniedError extends MarketplaceError {
  constructor(action: string, automationId: string) {
    super(
      `Access denied: cannot ${action} automation ${automationId}`,
      "ACCESS_DENIED",
      { action, automationId },
    );
    this.name = "AccessDeniedError";
  }
}

// ---------------------------------------------------------------------------
// AutomationPublisher
// ---------------------------------------------------------------------------

export class AutomationPublisher {
  private automations: Map<string, Automation> = new Map();
  private versions: Map<string, AutomationVersion[]> = new Map();
  private profiles: Map<string, PublisherProfile> = new Map();
  private eventLog: MarketplaceEvent[] = [];

  constructor(private config: MarketplaceConfig) {}

  /** Register a new publisher profile. */
  registerPublisher(
    profile: Omit<PublisherProfile, "automations" | "totalDownloads" | "averageRating">,
  ): PublisherProfile {
    const full: PublisherProfile = {
      ...profile,
      automations: [],
      totalDownloads: 0,
      averageRating: 0,
    };
    this.profiles.set(profile.id, full);
    return full;
  }

  /** Publish a new automation to the marketplace. */
  publish(automation: Omit<Automation, "downloads" | "status" | "validation" | "publishedAt" | "updatedAt">): Automation {
    if (this.automations.has(automation.id)) {
      throw new MarketplaceError(
        `Automation ${automation.id} already exists. Use update() instead.`,
        "ALREADY_EXISTS",
        { id: automation.id },
      );
    }

    if (
      this.config.requiredFrameworks &&
      automation.framework.length === 0
    ) {
      throw new MarketplaceError(
        "At least one compliance framework must be specified",
        "FRAMEWORK_REQUIRED",
      );
    }

    const now = new Date();
    const entry: Automation = {
      ...automation,
      downloads: 0,
      status: "published",
      publishedAt: now,
      updatedAt: now,
    };

    this.automations.set(automation.id, entry);

    const versionRecord: AutomationVersion = {
      version: automation.version,
      automationId: automation.id,
      publishedAt: now,
      changelog: "Initial release",
      checksum: this.computeChecksum(automation),
      deprecated: false,
    };
    this.versions.set(automation.id, [versionRecord]);

    // Update publisher profile
    const profile = this.profiles.get(automation.author);
    if (profile) {
      profile.automations.push(automation.id);
    }

    this.emit({
      type: "automation:published",
      automationId: automation.id,
      author: automation.author,
    });

    return entry;
  }

  /** Update an existing automation with a new version. */
  update(
    id: string,
    patch: Partial<Pick<Automation, "description" | "framework" | "industry" | "useCase" | "tags" | "entryPoint" | "readme" | "dependencies">>,
    newVersion: string,
    changelog: string,
  ): Automation {
    const existing = this.automations.get(id);
    if (!existing) {
      throw new AutomationNotFoundError(id);
    }

    const existingVersions = this.versions.get(id) ?? [];
    if (existingVersions.some((v) => v.version === newVersion)) {
      throw new VersionConflictError(id, newVersion);
    }

    const updated: Automation = {
      ...existing,
      ...patch,
      version: newVersion,
      updatedAt: new Date(),
    };
    this.automations.set(id, updated);

    const versionRecord: AutomationVersion = {
      version: newVersion,
      automationId: id,
      publishedAt: new Date(),
      changelog,
      checksum: this.computeChecksum(updated),
      deprecated: false,
    };
    const versions = existingVersions.concat(versionRecord);
    this.versions.set(id, versions);

    this.emit({
      type: "automation:updated",
      automationId: id,
      version: newVersion,
    });

    return updated;
  }

  /** Deprecate an automation. */
  deprecate(id: string, reason: string): void {
    const automation = this.automations.get(id);
    if (!automation) {
      throw new AutomationNotFoundError(id);
    }

    automation.status = "deprecated";
    automation.updatedAt = new Date();

    const versions = this.versions.get(id) ?? [];
    const latest = versions[versions.length - 1];
    if (latest) {
      latest.deprecated = true;
    }

    this.emit({ type: "automation:deprecated", automationId: id });
  }

  /** Retrieve an automation by id. */
  get(id: string): Automation {
    const automation = this.automations.get(id);
    if (!automation) {
      throw new AutomationNotFoundError(id);
    }
    return automation;
  }

  /** Get all versions of an automation. */
  getVersions(id: string): AutomationVersion[] {
    if (!this.automations.has(id)) {
      throw new AutomationNotFoundError(id);
    }
    return this.versions.get(id) ?? [];
  }

  /** Get a publisher profile. */
  getPublisher(id: string): PublisherProfile | undefined {
    return this.profiles.get(id);
  }

  /** List all automations by a given publisher. */
  listByPublisher(authorId: string): Automation[] {
    return Array.from(this.automations.values()).filter(
      (a) => a.author === authorId,
    );
  }

  private emit(event: MarketplaceEvent): void {
    this.eventLog.push(event);
  }

  private computeChecksum(automation: object): string {
    const payload = JSON.stringify(automation);
    let hash = 0;
    for (let i = 0; i < payload.length; i++) {
      const char = payload.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash |= 0;
    }
    return `sha256-${Math.abs(hash).toString(16)}`;
  }

  /** Expose event log for testing / audit. */
  getEventLog(): ReadonlyArray<MarketplaceEvent> {
    return this.eventLog;
  }

  /** Get internal automations map (for marketplace aggregation). */
  protected getAll(): Automation[] {
    return Array.from(this.automations.values());
  }
}

// ---------------------------------------------------------------------------
// AutomationDiscovery
// ---------------------------------------------------------------------------

export class AutomationDiscovery {
  constructor(private publisher: AutomationPublisher) {}

  /** Search automations with filtering, sorting, and pagination. */
  search(query: AutomationSearchQuery): SearchResult {
    let results = this.publisher["getAll"]();

    // Free-text search across name, description, tags
    if (query.query) {
      const q = query.query.toLowerCase();
      results = results.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          a.description.toLowerCase().includes(q) ||
          a.tags.some((t) => t.toLowerCase().includes(q)),
      );
    }

    // Framework filter
    if (query.framework && query.framework.length > 0) {
      results = results.filter((a) =>
        query.framework!.some((f) => a.framework.includes(f)),
      );
    }

    // Industry filter
    if (query.industry && query.industry.length > 0) {
      results = results.filter((a) =>
        query.industry!.some((i) => a.industry.includes(i)),
      );
    }

    // Use-case filter
    if (query.useCase && query.useCase.length > 0) {
      results = results.filter((a) =>
        query.useCase!.some((u) => a.useCase.includes(u)),
      );
    }

    // Tag filter
    if (query.tags && query.tags.length > 0) {
      results = results.filter((a) =>
        query.tags!.every((t) => a.tags.includes(t)),
      );
    }

    // Pricing filter
    if (query.pricing) {
      results = results.filter((a) => a.pricing.type === query.pricing);
    }

    // Rating filter
    if (query.minRating !== undefined) {
      results = results.filter((a) => {
        const rating = this.getAverageRating(a.id);
        return rating >= query.minRating!;
      });
    }

    // Only published & active
    results = results.filter((a) => a.status === "published");

    // Sort
    switch (query.sortBy) {
      case "rating":
        results.sort(
          (a, b) => this.getAverageRating(b.id) - this.getAverageRating(a.id),
        );
        break;
      case "downloads":
        results.sort((a, b) => b.downloads - a.downloads);
        break;
      case "newest":
        results.sort(
          (a, b) =>
            new Date(b.publishedAt).getTime() -
            new Date(a.publishedAt).getTime(),
        );
        break;
      case "updated":
        results.sort(
          (a, b) =>
            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
        );
        break;
      case "relevance":
      default:
        // Default: downloads as proxy for relevance
        results.sort((a, b) => b.downloads - a.downloads);
        break;
    }

    const total = results.length;
    const limit = query.limit ?? 20;
    const offset = query.offset ?? 0;
    const paginated = results.slice(offset, offset + limit);

    return {
      automations: paginated,
      total,
      hasMore: offset + limit < total,
    };
  }

  /** Browse automations by a specific framework. */
  browseByFramework(framework: ComplianceFramework): Automation[] {
    return this.search({ framework: [framework] }).automations;
  }

  /** Browse automations by industry vertical. */
  browseByIndustry(industry: string): Automation[] {
    return this.search({ industry: [industry] }).automations;
  }

  /** Browse automations by use case. */
  browseByUseCase(useCase: string): Automation[] {
    return this.search({ useCase: [useCase] }).automations;
  }

  /** Get trending automations (by recent downloads). */
  trending(limit: number = 10): Automation[] {
    return this.search({ sortBy: "downloads", limit }).automations;
  }

  /** Get newly published automations. */
  newest(limit: number = 10): Automation[] {
    return this.search({ sortBy: "newest", limit }).automations;
  }

  /** Get top-rated automations. */
  topRated(limit: number = 10): Automation[] {
    return this.search({ sortBy: "rating", minRating: 0, limit }).automations;
  }

  /** Get free automations. */
  free(limit: number = 20): Automation[] {
    return this.search({ pricing: "free", limit }).automations;
  }

  /** Get featured automations (top downloads with 4+ rating). */
  featured(limit: number = 5): Automation[] {
    const all = this.publisher["getAll"]();
    return all
      .filter((a) => a.status === "published")
      .map((a) => ({
        automation: a,
        score: this.getAverageRating(a.id) * 2 + Math.log2(a.downloads + 1),
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map((entry) => entry.automation);
  }

  /** Get related automations based on shared frameworks, industries, and tags. */
  related(automationId: string, limit: number = 5): Automation[] {
    const target = this.publisher.get(automationId);
    const all = this.publisher["getAll"]();

    return all
      .filter((a) => a.id !== automationId && a.status === "published")
      .map((a) => {
        let similarity = 0;
        for (const fw of target.framework) {
          if (a.framework.includes(fw)) similarity += 3;
        }
        for (const ind of target.industry) {
          if (a.industry.includes(ind)) similarity += 2;
        }
        for (const tag of target.tags) {
          if (a.tags.includes(tag)) similarity += 1;
        }
        return { automation: a, similarity };
      })
      .filter((entry) => entry.similarity > 0)
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit)
      .map((entry) => entry.automation);
  }

  private getAverageRating(automationId: string): number {
    // Delegate to the rating system if available; default to 0
    return 0;
  }
}

// ---------------------------------------------------------------------------
// AutomationRating
// ---------------------------------------------------------------------------

export class AutomationRating {
  private reviews: Map<string, AutomationReview[]> = new Map();
  private eventLog: MarketplaceEvent[] = [];

  constructor(private config: MarketplaceConfig) {}

  /** Submit a review for an automation. */
  submitReview(
    automationId: string,
    review: Omit<AutomationReview, "id" | "createdAt" | "updatedAt" | "helpful">,
  ): AutomationReview {
    if (review.rating < 1 || review.rating > 5) {
      throw new MarketplaceError(
        "Rating must be between 1 and 5",
        "INVALID_RATING",
        { rating: review.rating },
      );
    }

    const existing = this.reviews.get(automationId) ?? [];

    // Check cooldown: prevent same author from reviewing too frequently
    const lastReview = existing
      .filter((r) => r.author === review.author)
      .sort(
        (a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
      )[0];

    if (lastReview) {
      const elapsed = Date.now() - new Date(lastReview.createdAt).getTime();
      if (elapsed < this.config.reviewCooldownMs) {
        throw new MarketplaceError(
          "Review cooldown not met. Please wait before submitting another review.",
          "REVIEW_COOLDOWN",
          {
            nextAllowedAt: new Date(
              new Date(lastReview.createdAt).getTime() +
                this.config.reviewCooldownMs,
            ),
          },
        );
      }
    }

    const fullReview: AutomationReview = {
      ...review,
      id: this.generateId(),
      helpful: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    existing.push(fullReview);
    this.reviews.set(automationId, existing);

    this.eventLog.push({
      type: "automation:reviewed",
      automationId,
      rating: review.rating,
    });

    return fullReview;
  }

  /** Get all reviews for an automation. */
  getReviews(automationId: string): AutomationReview[] {
    return this.reviews.get(automationId) ?? [];
  }

  /** Get a summary of ratings for an automation. */
  getRatingSummary(automationId: string): AutomationRatingSummary {
    const reviews = this.reviews.get(automationId) ?? [];
    const distribution: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };

    for (const review of reviews) {
      distribution[review.rating] = (distribution[review.rating] ?? 0) + 1;
    }

    const totalReviews = reviews.length;
    const averageRating =
      totalReviews > 0
        ? reviews.reduce((sum, r) => sum + r.rating, 0) / totalReviews
        : 0;

    return {
      automationId,
      averageRating: Math.round(averageRating * 100) / 100,
      totalReviews,
      distribution,
    };
  }

  /** Mark a review as helpful. */
  markHelpful(reviewId: string, automationId: string): void {
    const reviews = this.reviews.get(automationId) ?? [];
    const review = reviews.find((r) => r.id === reviewId);
    if (review) {
      review.helpful += 1;
      review.updatedAt = new Date();
    }
  }

  /** Get top reviews for an automation (by helpfulness). */
  getTopReviews(automationId: string, limit: number = 5): AutomationReview[] {
    return this.getReviews(automationId)
      .sort((a, b) => b.helpful - a.helpful)
      .slice(0, limit);
  }

  /** Get reviews by a specific author. */
  getReviewsByAuthor(authorId: string): AutomationReview[] {
    const all: AutomationReview[] = [];
    for (const reviews of this.reviews.values()) {
      all.push(...reviews.filter((r) => r.author === authorId));
    }
    return all.sort(
      (a, b) =>
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    );
  }

  /** Delete a review (author or admin). */
  deleteReview(automationId: string, reviewId: string, requesterId: string): boolean {
    const reviews = this.reviews.get(automationId) ?? [];
    const index = reviews.findIndex((r) => r.id === reviewId);
    if (index === -1) return false;

    const review = reviews[index];
    if (review.author !== requesterId) {
      throw new AccessDeniedError("delete review", automationId);
    }

    reviews.splice(index, 1);
    this.reviews.set(automationId, reviews);
    return true;
  }

  private generateId(): string {
    return `rev_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
}

// ---------------------------------------------------------------------------
// AutomationInstaller
// ---------------------------------------------------------------------------

export class AutomationInstaller {
  private installed: Map<string, InstallationResult> = new Map();

  constructor(
    private publisher: AutomationPublisher,
    private config: MarketplaceConfig,
  ) {}

  /** Install an automation and its dependencies. */
  async install(
    automationId: string,
    targetPath: string,
  ): Promise<InstallationResult> {
    const automation = this.publisher.get(automationId);

    // Resolve dependency tree
    const resolved = await this.resolveDependencies(automationId, new Set());

    const now = new Date();
    const result: InstallationResult = {
      automationId,
      version: automation.version,
      installedAt: now,
      path: targetPath,
      resolvedDependencies: resolved,
    };

    this.installed.set(automationId, result);

    // Increment download count
    automation.downloads += 1;

    this.emit({
      type: "automation:installed",
      automationId,
      installedBy: targetPath,
    });

    return result;
  }

  /** Uninstall an automation. */
  uninstall(automationId: string): boolean {
    return this.installed.delete(automationId);
  }

  /** Check if an automation is installed. */
  isInstalled(automationId: string): boolean {
    return this.installed.has(automationId);
  }

  /** Get installation details. */
  getInstallation(automationId: string): InstallationResult | undefined {
    return this.installed.get(automationId);
  }

  /** List all installed automations. */
  listInstalled(): InstallationResult[] {
    return Array.from(this.installed.values());
  }

  /** Check for updates available for installed automations. */
  checkUpdates(): Array<{
    automationId: string;
    currentVersion: string;
    latestVersion: string;
  }> {
    const updates: Array<{
      automationId: string;
      currentVersion: string;
      latestVersion: string;
    }> = [];

    for (const [id, installation] of this.installed) {
      const automation = this.publisher.get(id);
      if (automation.version !== installation.version) {
        updates.push({
          automationId: id,
          currentVersion: installation.version,
          latestVersion: automation.version,
        });
      }
    }

    return updates;
  }

  /** Update an installed automation to the latest version. */
  async update(
    automationId: string,
    targetPath: string,
  ): Promise<InstallationResult> {
    const installation = this.installed.get(automationId);
    if (!installation) {
      throw new MarketplaceError(
        `Automation ${automationId} is not installed`,
        "NOT_INSTALLED",
      );
    }

    // Remove old installation
    this.installed.delete(automationId);

    // Re-install
    return this.install(automationId, targetPath);
  }

  private async resolveDependencies(
    automationId: string,
    visited: Set<string>,
  ): Promise<ResolvedDependency[]> {
    if (visited.has(automationId)) {
      throw new DependencyResolutionError(
        automationId,
        "Circular dependency detected",
      );
    }
    visited.add(automationId);

    if (visited.size > this.config.maxDependencies) {
      throw new DependencyResolutionError(
        automationId,
        `Maximum dependency depth of ${this.config.maxDependencies} exceeded`,
      );
    }

    const automation = this.publisher.get(automationId);
    const resolved: ResolvedDependency[] = [];

    for (const dep of automation.dependencies) {
      try {
        const depAutomation = this.publisher.get(dep.id);

        // Version range check (simplified semver)
        if (!this.satisfiesVersion(depAutomation.version, dep.versionRange)) {
          throw new DependencyResolutionError(
            dep.id,
            `Version ${depAutomation.version} does not satisfy range ${dep.versionRange}`,
          );
        }

        resolved.push({
          id: dep.id,
          name: depAutomation.name,
          version: depAutomation.version,
          resolvedFrom: automationId,
        });

        // Recursively resolve sub-dependencies
        const subDeps = await this.resolveDependencies(dep.id, visited);
        resolved.push(...subDeps);
      } catch (err) {
        if (dep.optional) continue;
        if (err instanceof DependencyResolutionError) throw err;
        throw new DependencyResolutionError(
          dep.id,
          err instanceof Error ? err.message : "Unknown error",
        );
      }
    }

    return resolved;
  }

  /** Simple version range check supporting ^, ~, >=, exact. */
  private satisfiesVersion(version: string, range: string): boolean {
    const parts = version.split(".").map(Number);
    const trimmed = range.trim();

    if (trimmed.startsWith("^")) {
      const target = trimmed.slice(1).split(".").map(Number);
      return parts[0] === target[0] && this.versionGte(parts, target);
    }

    if (trimmed.startsWith("~")) {
      const target = trimmed.slice(1).split(".").map(Number);
      return (
        parts[0] === target[0] &&
        parts[1] === target[1] &&
        this.versionGte(parts, target)
      );
    }

    if (trimmed.startsWith(">=")) {
      const target = trimmed.slice(2).split(".").map(Number);
      return this.versionGte(parts, target);
    }

    return version === trimmed;
  }

  private versionGte(a: number[], b: number[]): boolean {
    for (let i = 0; i < Math.max(a.length, b.length); i++) {
      const ai = a[i] ?? 0;
      const bi = b[i] ?? 0;
      if (ai > bi) return true;
      if (ai < bi) return false;
    }
    return true;
  }

  private emit(event: MarketplaceEvent): void {
    // Events could be forwarded to an event bus
    void event;
  }
}

// ---------------------------------------------------------------------------
// ComplianceAutomationMarketplace (Facade)
// ---------------------------------------------------------------------------

export class ComplianceAutomationMarketplace {
  readonly publisher: AutomationPublisher;
  readonly discovery: AutomationDiscovery;
  readonly rating: AutomationRating;
  readonly installer: AutomationInstaller;

  private static readonly DEFAULT_CONFIG: MarketplaceConfig = {
    storagePath: "./marketplace-data",
    maxUploadSizeMb: 50,
    requiredFrameworks: true,
    enableMonetization: true,
    validationTimeoutMs: 30_000,
    maxDependencies: 50,
    reviewCooldownMs: 24 * 60 * 60 * 1000, // 24 hours
  };

  constructor(config?: Partial<MarketplaceConfig>) {
    const fullConfig: MarketplaceConfig = {
      ...ComplianceAutomationMarketplace.DEFAULT_CONFIG,
      ...config,
    };

    this.publisher = new AutomationPublisher(fullConfig);
    this.discovery = new AutomationDiscovery(this.publisher);
    this.rating = new AutomationRating(fullConfig);
    this.installer = new AutomationInstaller(this.publisher, fullConfig);
  }

  /** Publish a new automation with automatic validation. */
  async publishAutomation(
    automation: Omit<
      Automation,
      | "downloads"
      | "status"
      | "validation"
      | "publishedAt"
      | "updatedAt"
    >,
  ): Promise<Automation> {
    const validation = await this.validateAutomation(automation);
    const result = this.publisher.publish(automation);
    result.validation = validation;
    return result;
  }

  /** Search for automations. */
  search(query: AutomationSearchQuery): SearchResult {
    return this.discovery.search(query);
  }

  /** Install an automation. */
  async installAutomation(
    automationId: string,
    targetPath: string,
  ): Promise<InstallationResult> {
    return this.installer.install(automationId, targetPath);
  }

  /** Submit a review for an automation. */
  submitReview(
    automationId: string,
    review: Omit<AutomationReview, "id" | "createdAt" | "updatedAt" | "helpful">,
  ): AutomationReview {
    return this.rating.submitReview(automationId, review);
  }

  /** Get rating summary for an automation. */
  getRatingSummary(automationId: string): AutomationRatingSummary {
    return this.rating.getRatingSummary(automationId);
  }

  /** Validate an automation before publishing. */
  async validateAutomation(
    automation: Pick<Automation, "id" | "name" | "entryPoint" | "framework" | "dependencies">,
  ): Promise<ValidationResult> {
    const errors: ValidationItem[] = [];
    const warnings: ValidationWarning[] = [];

    if (!automation.id || automation.id.trim().length === 0) {
      errors.push({ code: "MISSING_ID", message: "Automation ID is required" });
    }

    if (!automation.name || automation.name.trim().length === 0) {
      errors.push({ code: "MISSING_NAME", message: "Automation name is required" });
    }

    if (!automation.entryPoint || automation.entryPoint.trim().length === 0) {
      errors.push({
        code: "MISSING_ENTRY_POINT",
        message: "Entry point is required",
      });
    }

    if (automation.framework.length === 0) {
      warnings.push({
        code: "NO_FRAMEWORK",
        message: "No compliance framework specified",
        suggestion: "Add at least one framework for better discoverability",
      });
    }

    if (automation.dependencies.length > 10) {
      warnings.push({
        code: "MANY_DEPENDENCIES",
        message: `${automation.dependencies.length} dependencies detected`,
        suggestion: "Consider reducing dependencies for easier maintenance",
      });
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      checkedAt: new Date(),
    };
  }

  /** Get marketplace statistics. */
  getStats(): {
    totalAutomations: number;
    totalDownloads: number;
    automationsByFramework: Record<string, number>;
    automationsByPricing: Record<string, number>;
  } {
    const all = this.publisher["getAll"]();
    const byFramework: Record<string, number> = {};
    const byPricing: Record<string, number> = {};
    let totalDownloads = 0;

    for (const a of all) {
      totalDownloads += a.downloads;
      for (const fw of a.framework) {
        byFramework[fw] = (byFramework[fw] ?? 0) + 1;
      }
      byPricing[a.pricing.type] = (byPricing[a.pricing.type] ?? 0) + 1;
    }

    return {
      totalAutomations: all.length,
      totalDownloads,
      automationsByFramework: byFramework,
      automationsByPricing: byPricing,
    };
  }
}

// Re-export everything for convenience
export {
  type Automation as AutomationDTO,
  type MarketplaceConfig as Config,
};
