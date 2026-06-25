import { randomUUID } from "node:crypto";
import type { TrustPage, TrustItem, TrustItemStatus } from "../types.js";

export class TrustCenter {
  private pages: Map<string, TrustPage> = new Map();

  createPage(slug: string, companyName: string): TrustPage {
    const page: TrustPage = {
      id: randomUUID(),
      slug,
      companyName,
      items: [],
      isPublic: false,
    };
    this.pages.set(page.id, page);
    return page;
  }

  getPage(id: string): TrustPage | undefined { return this.pages.get(id); }
  getPageBySlug(slug: string): TrustPage | undefined { return Array.from(this.pages.values()).find((p) => p.slug === slug); }

  addItem(pageId: string, item: Omit<TrustItem, "id">): TrustItem | null {
    const page = this.pages.get(pageId);
    if (!page) return null;
    const newItem: TrustItem = { ...item, id: randomUUID() };
    page.items.push(newItem);
    page.items.sort((a, b) => a.order - b.order);
    return newItem;
  }

  updateItemStatus(pageId: string, itemId: string, status: TrustItemStatus): boolean {
    const page = this.pages.get(pageId);
    if (!page) return false;
    const item = page.items.find((i) => i.id === itemId);
    if (!item) return false;
    item.status = status;
    return true;
  }

  publishPage(pageId: string): boolean {
    const page = this.pages.get(pageId);
    if (!page) return false;
    page.publishedAt = new Date().toISOString();
    page.isPublic = true;
    return true;
  }

  generatePublicJson(pageId: string): Record<string, unknown> | null {
    const page = this.pages.get(pageId);
    if (!page || !page.isPublic) return null;
    return {
      company: page.companyName,
      slug: page.slug,
      publishedAt: page.publishedAt,
      trustItems: page.items.filter((i) => i.status === "active").map((i) => ({
        type: i.type,
        name: i.name,
        description: i.description,
        framework: i.framework,
        summary: i.summary,
      })),
    };
  }
}
