/**
 * Lead client for the GRC Marketing TypeScript SDK.
 */

import type { APIClient } from "./client.js";
import type {
  Lead,
  LeadCreatePayload,
  LeadUpdatePayload,
  ListResponse,
} from "./types.js";

export interface ListLeadsParams {
  page?: number;
  per_page?: number;
  status?: string;
  source?: string;
  sort_by?: string;
  sort_order?: string;
}

export class LeadClient {
  private client: APIClient;

  constructor(apiClient: APIClient) {
    this.client = apiClient;
  }

  async list(params: ListLeadsParams = {}): Promise<ListResponse<Lead>> {
    const queryParams: Record<string, unknown> = {
      page: params.page ?? 1,
      per_page: params.per_page ?? 20,
      sort_by: params.sort_by ?? "created_at",
      sort_order: params.sort_order ?? "desc",
    };
    if (params.status) queryParams.status = params.status;
    if (params.source) queryParams.source = params.source;

    const response = (await this.client.get("/leads", queryParams)) as Record<
      string,
      unknown
    >;
    return {
      data: (response.data as Lead[]) || [],
      total: (response.total as number) || 0,
      page: (response.page as number) || 1,
      per_page: (response.per_page as number) || 20,
      total_pages: (response.total_pages as number) || 0,
    };
  }

  async get(leadId: string): Promise<Lead> {
    const response = (await this.client.get(`/leads/${leadId}`)) as Record<
      string,
      unknown
    >;
    return response.data as Lead;
  }

  async create(payload: LeadCreatePayload): Promise<Lead> {
    const response = (await this.client.post("/leads", payload)) as Record<
      string,
      unknown
    >;
    return response.data as Lead;
  }

  async update(leadId: string, payload: LeadUpdatePayload): Promise<Lead> {
    const response = (await this.client.patch(
      `/leads/${leadId}`,
      payload,
    )) as Record<string, unknown>;
    return response.data as Lead;
  }

  async delete(leadId: string): Promise<void> {
    await this.client.delete(`/leads/${leadId}`);
  }

  async qualify(leadId: string): Promise<Lead> {
    return this.update(leadId, { status: "qualified" });
  }

  async convert(leadId: string): Promise<Lead> {
    return this.update(leadId, { status: "converted" });
  }

  async markLost(leadId: string): Promise<Lead> {
    return this.update(leadId, { status: "lost" });
  }
}
