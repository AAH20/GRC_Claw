import { randomUUID } from "node:crypto";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Supported compliance frameworks. */
export type Framework =
  | "SOC2"
  | "ISO27001"
  | "NIST-CSF"
  | "NIST-800-53"
  | "HIPAA"
  | "PCI-DSS"
  | "GDPR"
  | "FedRAMP"
  | "CIS"
  | "custom";

/** Pricing tier for marketplace items. */
export type PricingTier = "free" | "standard" | "premium" | "enterprise";

/** Status of a marketplace listing. */
export type ListingStatus = "draft" | "pending" | "published" | "suspended" | "archived";

/** Payment method. */
export type PaymentMethod = "invoice" | "card" | "ach" | "wire";

/** Export format for compliance packs. */
export type ExportFormat = "json" | "yaml" | "csv";

/** A single compliance control within a pack. */
export interface ComplianceControl {
  id: string;
  name: string;
  description: string;
  framework: Framework;
  category: string;
  implementation: string;
  evidence: string[];
  automations: string[];
  tags: string[];
}

/** Review left by a user. */
export interface Review {
  id: string;
  userId: string;
  rating: number;
  comment: string;
  createdAt: Date;
}

/** Analytics for a marketplace item. */
export interface ItemAnalytics {
  views: number;
  installs: number;
  uninstalls: number;
  revenue: number;
  ratingDistribution: Record<number, number>;
  topReferrers: string[];
  monthlyTrend: { month: string; installs: number }[];
}

/** A marketplace item representing a compliance pack. */
export interface MarketplaceItem {
  id: string;
  name: string;
  description: string;
  author: string;
  version: string;
  price: number;
  tier: PricingTier;
  rating: number;
  downloads: number;
  tags: string[];
  framework: Framework;
  controls: ComplianceControl[];
  evidence: string[];
  reviews: Review[];
  createdAt: Date;
  updatedAt: Date;
}

/** A listing in the marketplace. */
export interface MarketplaceListing {
  item: MarketplaceItem;
  status: ListingStatus;
  createdAt: Date;
  updatedAt: Date;
  analytics: ItemAnalytics;
}

/** A publisher (author) of compliance packs. */
export interface Publisher {
  id: string;
  name: string;
  email: string;
  verified: boolean;
  rating: number;
  items: string[];
  createdAt: Date;
}

/** An installation record. */
export interface Installation {
  id: string;
  orgId: string;
  itemId: string;
  installedAt: Date;
  version: string;
  active: boolean;
}

/** Invoice for a purchase. */
export interface Invoice {
  id: string;
  orgId: string;
  items: { itemId: string; name: string; price: number }[];
  subtotal: number;
  discount: number;
  total: number;
  status: "pending" | "paid" | "cancelled";
  createdAt: Date;
}

/** Discount code. */
export interface DiscountCode {
  code: string;
  percentage: number;
  maxUses: number;
  usedCount: number;
  expiresAt: Date;
}

// ---------------------------------------------------------------------------
// Errors
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

// ---------------------------------------------------------------------------
// CompliancePack
// ---------------------------------------------------------------------------

/**
 * Represents a compliance pack that can be published to the marketplace.
 * Provides methods for building, validating, importing, exporting, and
 * comparing packs.
 */
export class CompliancePack {
  id: string;
  name: string;
  description: string;
  framework: Framework;
  version: string;
  controls: Map<string, ComplianceControl> = new Map();

  constructor(name: string, description: string, framework: Framework) {
    this.id = randomUUID();
    this.name = name;
    this.description = description;
    this.framework = framework;
    this.version = "1.0.0";
  }

  /**
   * Create a new compliance pack with initial controls.
   */
  static createPack(
    name: string,
    description: string,
    framework: Framework,
    controls: ComplianceControl[],
  ): CompliancePack {
    const pack = new CompliancePack(name, description, framework);
    for (const control of controls) {
      pack.addControl(control.id, control);
    }
    return pack;
  }

  /**
   * Add or update a control in the pack.
   */
  addControl(controlId: string, control: Omit<ComplianceControl, "id"> & { id?: string }): void {
    const fullControl: ComplianceControl = {
      ...control,
      id: controlId,
    };
    this.controls.set(controlId, fullControl);
  }

  /**
   * Validate that the pack is complete and ready for publishing.
   * Returns an array of validation errors (empty if valid).
   */
  validatePack(): string[] {
    const errors: string[] = [];

    if (!this.name.trim()) {
      errors.push("Pack name is required");
    }
    if (!this.description.trim()) {
      errors.push("Pack description is required");
    }
    if (this.controls.size === 0) {
      errors.push("Pack must contain at least one control");
    }

    for (const [id, control] of this.controls) {
      if (!control.name.trim()) {
        errors.push(`Control ${id} is missing a name`);
      }
      if (!control.implementation.trim()) {
        errors.push(`Control ${id} is missing an implementation`);
      }
      if (control.evidence.length === 0) {
        errors.push(`Control ${id} has no evidence requirements`);
      }
    }

    return errors;
  }

  /**
   * Export the pack to the specified format.
   */
  exportPack(format: ExportFormat): string {
    const data = {
      id: this.id,
      name: this.name,
      description: this.description,
      framework: this.framework,
      version: this.version,
      controls: Array.from(this.controls.values()),
    };

    switch (format) {
      case "json":
        return JSON.stringify(data, null, 2);
      case "yaml":
        return this.toYaml(data);
      case "csv":
        return this.toCsv(data.controls);
      default:
        throw new MarketplaceError(`Unsupported export format: ${format}`, "INVALID_FORMAT");
    }
  }

  /**
   * Import a pack from a JSON string.
   */
  static importPack(data: string): CompliancePack {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(data) as Record<string, unknown>;
    } catch {
      throw new MarketplaceError("Invalid JSON data for pack import", "INVALID_IMPORT");
    }

    const name = parsed.name as string;
    const description = parsed.description as string;
    const framework = parsed.framework as Framework;
    const controls = parsed.controls as ComplianceControl[];

    if (!name || !description || !framework) {
      throw new MarketplaceError("Import data missing required fields", "INVALID_IMPORT");
    }

    return CompliancePack.createPack(name, description, framework, controls ?? []);
  }

  /**
   * Compare this pack with another and return differences.
   */
  diffPack(other: CompliancePack): {
    added: ComplianceControl[];
    removed: ComplianceControl[];
    modified: { controlId: string; ours: ComplianceControl; theirs: ComplianceControl }[];
  } {
    const added: ComplianceControl[] = [];
    const removed: ComplianceControl[] = [];
    const modified: { controlId: string; ours: ComplianceControl; theirs: ComplianceControl }[] = [];

    for (const [id, theirs] of other.controls) {
      const ours = this.controls.get(id);
      if (!ours) {
        added.push(theirs);
      } else if (JSON.stringify(ours) !== JSON.stringify(theirs)) {
        modified.push({ controlId: id, ours, theirs });
      }
    }

    for (const [id] of this.controls) {
      if (!other.controls.has(id)) {
        removed.push(this.controls.get(id)!);
      }
    }

    return { added, removed, modified };
  }

  /**
   * Merge another pack into this one. Conflicts are resolved by taking
   * the other pack's version of a control.
   */
  mergePack(other: CompliancePack): CompliancePack {
    const merged = new CompliancePack(
      `${this.name} + ${other.name}`,
      `Merged pack combining ${this.name} and ${other.name}`,
      this.framework,
    );
    merged.version = this.version;

    for (const [id, control] of this.controls) {
      merged.controls.set(id, { ...control });
    }
    for (const [id, control] of other.controls) {
      merged.controls.set(id, { ...control });
    }

    return merged;
  }

  private toYaml(data: Record<string, unknown>, indent = 0): string {
    const lines: string[] = [];
    const prefix = "  ".repeat(indent);

    for (const [key, value] of Object.entries(data)) {
      if (Array.isArray(value)) {
        lines.push(`${prefix}${key}:`);
        for (const item of value) {
          if (typeof item === "object" && item !== null) {
            lines.push(`${prefix}  -`);
            for (const [k, v] of Object.entries(item)) {
              if (Array.isArray(v)) {
                lines.push(`${prefix}    ${k}:`);
                for (const sub of v) {
                  lines.push(`${prefix}      - ${sub}`);
                }
              } else {
                lines.push(`${prefix}    ${k}: ${v}`);
              }
            }
          } else {
            lines.push(`${prefix}  - ${item}`);
          }
        }
      } else if (typeof value === "object" && value !== null) {
        lines.push(`${prefix}${key}:`);
        lines.push(this.toYaml(value as Record<string, unknown>, indent + 1));
      } else {
        lines.push(`${prefix}${key}: ${value}`);
      }
    }

    return lines.join("\n");
  }

  private toCsv(controls: ComplianceControl[]): string {
    const headers = ["id", "name", "framework", "category", "implementation", "evidence", "tags"];
    const rows = controls.map((c) =>
      [c.id, c.name, c.framework, c.category, c.implementation, c.evidence.join(";"), c.tags.join(";")]
        .map((v) => `"${String(v).replace(/"/g, '""')}"`)
        .join(","),
    );
    return [headers.join(","), ...rows].join("\n");
  }
}

// ---------------------------------------------------------------------------
// PricingEngine
// ---------------------------------------------------------------------------

/**
 * Handles pricing calculations, discounts, and invoicing.
 */
export class PricingEngine {
  private discounts: Map<string, DiscountCode> = new Map();

  private readonly tierMultipliers: Record<PricingTier, number> = {
    free: 0,
    standard: 1,
    premium: 2.5,
    enterprise: 5,
  };

  /**
   * Calculate the price for a pack at the given tier.
   */
  calculatePrice(pack: CompliancePack, tier: PricingTier): number {
    if (tier === "free") return 0;

    const controlCount = pack.controls.size;
    const basePrice = controlCount * 10;
    const multiplier = this.tierMultipliers[tier];
    return Math.round(basePrice * multiplier * 100) / 100;
  }

  /**
   * Register a discount code.
   */
  registerDiscount(code: string, percentage: number, maxUses: number, expiresAt: Date): void {
    this.discounts.set(code.toUpperCase(), {
      code: code.toUpperCase(),
      percentage,
      maxUses,
      usedCount: 0,
      expiresAt,
    });
  }

  /**
   * Apply a discount code and return the discount percentage.
   * Throws if the code is invalid, expired, or exhausted.
   */
  applyDiscount(code: string): number {
    const discount = this.discounts.get(code.toUpperCase());
    if (!discount) {
      throw new MarketplaceError(`Invalid discount code: ${code}`, "INVALID_DISCOUNT");
    }
    if (discount.usedCount >= discount.maxUses) {
      throw new MarketplaceError("Discount code has been exhausted", "DISCOUNT_EXHAUSTED");
    }
    if (new Date() > discount.expiresAt) {
      throw new MarketplaceError("Discount code has expired", "DISCOUNT_EXPIRED");
    }
    discount.usedCount++;
    return discount.percentage;
  }

  /**
   * Generate an invoice for the given items.
   */
  generateInvoice(
    orgId: string,
    items: { itemId: string; name: string; price: number }[],
    discountCode?: string,
  ): Invoice {
    const subtotal = items.reduce((sum, i) => sum + i.price, 0);
    let discount = 0;

    if (discountCode) {
      try {
        const pct = this.applyDiscount(discountCode);
        discount = Math.round(subtotal * (pct / 100) * 100) / 100;
      } catch {
        // Invalid discount code — proceed without discount
      }
    }

    return {
      id: randomUUID(),
      orgId,
      items,
      subtotal,
      discount,
      total: subtotal - discount,
      status: "pending",
      createdAt: new Date(),
    };
  }

  /**
   * Process a payment for an invoice.
   */
  processPayment(invoiceId: string, _method: PaymentMethod): { success: boolean; transactionId: string } {
    // In production this would integrate with a payment provider.
    return {
      success: true,
      transactionId: `txn_${invoiceId}_${randomUUID().slice(0, 8)}`,
    };
  }
}

// ---------------------------------------------------------------------------
// MarketplaceRegistry
// ---------------------------------------------------------------------------

/**
 * Manages publishers — registration, verification, and analytics.
 */
export class MarketplaceRegistry {
  private publishers: Map<string, Publisher> = new Map();

  /**
   * Register a new publisher.
   */
  registerPublisher(publisher: Omit<Publisher, "verified" | "rating" | "items" | "createdAt">): Publisher {
    if (this.publishers.has(publisher.id)) {
      throw new MarketplaceError(`Publisher already registered: ${publisher.id}`, "DUPLICATE_PUBLISHER");
    }

    const full: Publisher = {
      ...publisher,
      verified: false,
      rating: 0,
      items: [],
      createdAt: new Date(),
    };
    this.publishers.set(publisher.id, full);
    return full;
  }

  /**
   * Mark a publisher as verified.
   */
  verifyPublisher(id: string): Publisher {
    const pub = this.publishers.get(id);
    if (!pub) {
      throw new MarketplaceError(`Publisher not found: ${id}`, "PUBLISHER_NOT_FOUND");
    }
    pub.verified = true;
    return pub;
  }

  /**
   * Get a publisher by ID.
   */
  getPublisher(id: string): Publisher {
    const pub = this.publishers.get(id);
    if (!pub) {
      throw new MarketplaceError(`Publisher not found: ${id}`, "PUBLISHER_NOT_FOUND");
    }
    return pub;
  }

  /**
   * List all registered publishers.
   */
  listPublishers(): Publisher[] {
    return Array.from(this.publishers.values());
  }

  /**
   * Get analytics for a specific publisher.
   */
  getPublisherAnalytics(id: string): { totalItems: number; verified: boolean; rating: number } {
    const pub = this.getPublisher(id);
    return {
      totalItems: pub.items.length,
      verified: pub.verified,
      rating: pub.rating,
    };
  }
}

// ---------------------------------------------------------------------------
// MarketplaceEngine
// ---------------------------------------------------------------------------

/**
 * Core engine powering the compliance marketplace.
 * Handles publishing, searching, installing, rating, and recommendations.
 */
export class MarketplaceEngine {
  private listings: Map<string, MarketplaceListing> = new Map();
  private installations: Map<string, Installation[]> = new Map();
  private registry: MarketplaceRegistry;
  private pricing: PricingEngine;

  constructor(registry?: MarketplaceRegistry, pricing?: PricingEngine) {
    this.registry = registry ?? new MarketplaceRegistry();
    this.pricing = pricing ?? new PricingEngine();
  }

  /**
   * Publish a compliance pack to the marketplace.
   */
  publishItem(pack: CompliancePack, authorId: string): MarketplaceListing {
    const errors = pack.validatePack();
    if (errors.length > 0) {
      throw new MarketplaceError(
        `Pack validation failed: ${errors.join(", ")}`,
        "VALIDATION_FAILED",
      );
    }

    const publisher = this.registry.getPublisher(authorId);

    const item: MarketplaceItem = {
      id: pack.id,
      name: pack.name,
      description: pack.description,
      author: publisher.name,
      version: pack.version,
      price: this.pricing.calculatePrice(pack, "standard"),
      tier: "standard",
      rating: 0,
      downloads: 0,
      tags: this.extractTags(pack),
      framework: pack.framework,
      controls: Array.from(pack.controls.values()),
      evidence: Array.from(pack.controls.values()).flatMap((c) => c.evidence),
      reviews: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    const listing: MarketplaceListing = {
      item,
      status: "published",
      createdAt: new Date(),
      updatedAt: new Date(),
      analytics: this.emptyAnalytics(),
    };

    this.listings.set(item.id, listing);
    publisher.items.push(item.id);

    return listing;
  }

  /**
   * Search marketplace items by query string and optional filters.
   */
  searchItems(
    query: string,
    filters?: {
      framework?: Framework;
      tags?: string[];
      minRating?: number;
      maxPrice?: number;
      tier?: PricingTier;
    },
  ): MarketplaceItem[] {
    const lowerQuery = query.toLowerCase();

    return Array.from(this.listings.values())
      .filter((l) => l.status === "published")
      .map((l) => l.item)
      .filter((item) => {
        const matchesQuery =
          !query ||
          item.name.toLowerCase().includes(lowerQuery) ||
          item.description.toLowerCase().includes(lowerQuery) ||
          item.tags.some((t) => t.toLowerCase().includes(lowerQuery));

        const matchesFramework = !filters?.framework || item.framework === filters.framework;
        const matchesTags =
          !filters?.tags || filters.tags.every((t) => item.tags.includes(t));
        const matchesRating = !filters?.minRating || item.rating >= filters.minRating;
        const matchesPrice = filters?.maxPrice === undefined || item.price <= filters.maxPrice;
        const matchesTier = !filters?.tier || item.tier === filters.tier;

        return matchesQuery && matchesFramework && matchesTags && matchesRating && matchesPrice && matchesTier;
      });
  }

  /**
   * Get a single item by ID.
   */
  getItem(id: string): MarketplaceItem {
    const listing = this.listings.get(id);
    if (!listing) {
      throw new MarketplaceError(`Item not found: ${id}`, "ITEM_NOT_FOUND");
    }
    return listing.item;
  }

  /**
   * Install an item. Alias for installItem.
   */
  install(orgIdOrItemId: string, itemId?: string): Installation {
    if (itemId) {
      return this.installItem(orgIdOrItemId, itemId);
    }
    return this.installItem("default-org", orgIdOrItemId);
  }

  /**
   * Install a marketplace item for an organization.
   */
  installItem(orgId: string, itemId: string): Installation {
    const listing = this.listings.get(itemId);
    if (!listing) {
      throw new MarketplaceError(`Item not found: ${itemId}`, "ITEM_NOT_FOUND");
    }

    const orgInstalls = this.installations.get(orgId) ?? [];
    const existing = orgInstalls.find((i) => i.itemId === itemId && i.active);
    if (existing) {
      throw new MarketplaceError("Item already installed for this organization", "ALREADY_INSTALLED");
    }

    const installation: Installation = {
      id: randomUUID(),
      orgId,
      itemId,
      installedAt: new Date(),
      version: listing.item.version,
      active: true,
    };

    orgInstalls.push(installation);
    this.installations.set(orgId, orgInstalls);

    listing.item.downloads++;
    listing.analytics.installs++;

    return installation;
  }

  /**
   * Rate and review a marketplace item.
   */
  rateItem(itemId: string, userId: string, rating: number, comment: string): Review {
    if (rating < 1 || rating > 5) {
      throw new MarketplaceError("Rating must be between 1 and 5", "INVALID_RATING");
    }

    const listing = this.listings.get(itemId);
    if (!listing) {
      throw new MarketplaceError(`Item not found: ${itemId}`, "ITEM_NOT_FOUND");
    }

    const existingReview = listing.item.reviews.find((r) => r.userId === userId);
    if (existingReview) {
      throw new MarketplaceError("User has already reviewed this item", "DUPLICATE_REVIEW");
    }

    const review: Review = {
      id: randomUUID(),
      userId,
      rating,
      comment,
      createdAt: new Date(),
    };

    listing.item.reviews.push(review);

    // Recalculate average rating
    const total = listing.item.reviews.reduce((sum, r) => sum + r.rating, 0);
    listing.item.rating = Math.round((total / listing.item.reviews.length) * 10) / 10;

    // Update distribution
    const dist = listing.analytics.ratingDistribution;
    dist[rating] = (dist[rating] ?? 0) + 1;

    return review;
  }

  /**
   * Get AI-powered recommendations for an organization based on their
   * existing installations and industry profile.
   */
  getRecommendations(orgId: string): MarketplaceItem[] {
    const installed = this.installations.get(orgId) ?? [];
    const installedFrameworks = new Set(
      installed.map((i) => this.listings.get(i.itemId)?.item.framework).filter(Boolean),
    );
    const installedTags = new Set(
      installed.flatMap((i) => this.listings.get(i.itemId)?.item.tags ?? []),
    );

    return Array.from(this.listings.values())
      .filter((l) => l.status === "published")
      .map((l) => l.item)
      .filter((item) => !installed.some((i) => i.itemId === item.id))
      .map((item) => {
        let score = 0;
        if (installedFrameworks.has(item.framework)) score += 3;
        score += item.tags.filter((t) => installedTags.has(t)).length;
        score += item.rating;
        return { item, score };
      })
      .sort((a, b) => b.score - a.score)
      .slice(0, 10)
      .map((r) => r.item);
  }

  /**
   * Get trending items based on recent downloads and ratings.
   */
  getTrending(): MarketplaceItem[] {
    return Array.from(this.listings.values())
      .filter((l) => l.status === "published")
      .map((l) => l.item)
      .sort((a, b) => b.downloads * b.rating - a.downloads * a.rating)
      .slice(0, 20);
  }

  /**
   * Browse items grouped by framework category.
   */
  getCategories(): Map<Framework, MarketplaceItem[]> {
    const categories = new Map<Framework, MarketplaceItem[]>();

    for (const listing of this.listings.values()) {
      if (listing.status !== "published") continue;
      const existing = categories.get(listing.item.framework) ?? [];
      existing.push(listing.item);
      categories.set(listing.item.framework, existing);
    }

    return categories;
  }

  /**
   * Get featured items (highest rated + most downloaded).
   */
  getFeatured(): MarketplaceItem[] {
    return Array.from(this.listings.values())
      .filter((l) => l.status === "published" && l.item.rating >= 4)
      .map((l) => l.item)
      .sort((a, b) => b.downloads - a.downloads)
      .slice(0, 10);
  }

  /**
   * Update a marketplace item's metadata.
   */
  updateItem(id: string, updates: Partial<Pick<MarketplaceItem, "name" | "description" | "tags" | "version">>): MarketplaceItem {
    const listing = this.listings.get(id);
    if (!listing) {
      throw new MarketplaceError(`Item not found: ${id}`, "ITEM_NOT_FOUND");
    }

    if (updates.name) listing.item.name = updates.name;
    if (updates.description) listing.item.description = updates.description;
    if (updates.tags) listing.item.tags = updates.tags;
    if (updates.version) listing.item.version = updates.version;
    listing.item.updatedAt = new Date();
    listing.updatedAt = new Date();

    return listing.item;
  }

  /**
   * Remove an item from the marketplace (archives it).
   */
  removeItem(id: string): void {
    const listing = this.listings.get(id);
    if (!listing) {
      throw new MarketplaceError(`Item not found: ${id}`, "ITEM_NOT_FOUND");
    }
    listing.status = "archived";
    listing.updatedAt = new Date();
  }

  /**
   * Get analytics for a specific item.
   */
  getAnalytics(itemId: string): ItemAnalytics {
    const listing = this.listings.get(itemId);
    if (!listing) {
      throw new MarketplaceError(`Item not found: ${itemId}`, "ITEM_NOT_FOUND");
    }
    return listing.analytics;
  }

  /**
   * Get marketplace statistics.
   */
  stats(): {
    totalItems: number;
    totalPacks: number;
    publishedItems: number;
    totalPublishers: number;
    totalInstalls: number;
  } {
    const published = Array.from(this.listings.values()).filter(l => l.status === "published");
    const totalInstalls = Array.from(this.listings.values()).reduce(
      (sum, l) => sum + l.analytics.installs, 0
    );
    return {
      totalItems: this.listings.size,
      totalPacks: this.listings.size,
      publishedItems: published.length,
      totalPublishers: this.registry.listPublishers().length,
      totalInstalls,
    };
  }

  /**
   * Search marketplace items with optional filters.
   */
  search(filters?: {
    query?: string;
    framework?: string;
    frameworks?: string[];
    industries?: string[];
    limit?: number;
  }): MarketplaceItem[] {
    let items = Array.from(this.listings.values())
      .filter(l => l.status === "published")
      .map(l => l.item);

    if (filters?.query) {
      const q = filters.query.toLowerCase();
      items = items.filter(item =>
        item.name.toLowerCase().includes(q) ||
        item.description.toLowerCase().includes(q)
      );
    }

    if (filters?.framework) {
      items = items.filter(item => item.framework === filters.framework);
    }

    if (filters?.frameworks && filters.frameworks.length > 0) {
      items = items.filter(item => filters.frameworks!.includes(item.framework));
    }

    if (filters?.limit) {
      items = items.slice(0, filters.limit);
    }

    return items;
  }

  /** Expose the registry for external use. */
  getRegistry(): MarketplaceRegistry {
    return this.registry;
  }

  /** Expose the pricing engine for external use. */
  getPricing(): PricingEngine {
    return this.pricing;
  }

  private extractTags(pack: CompliancePack): string[] {
    const tags = new Set<string>();
    tags.add(pack.framework.toLowerCase());
    for (const control of pack.controls.values()) {
      for (const tag of control.tags) {
        tags.add(tag);
      }
      tags.add(control.category.toLowerCase());
    }
    return Array.from(tags);
  }

  private emptyAnalytics(): ItemAnalytics {
    return {
      views: 0,
      installs: 0,
      uninstalls: 0,
      revenue: 0,
      ratingDistribution: {},
      topReferrers: [],
      monthlyTrend: [],
    };
  }
}

/** Alias for backward compatibility */
export { MarketplaceEngine as ComplianceMarketplace };
