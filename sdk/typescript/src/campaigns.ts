/**
 * Campaign client for the GRC Marketing TypeScript SDK.
 */

import type { APIClient } from "./client.js";
import type {
  Campaign,
  CampaignCreatePayload,
  CampaignUpdatePayload,
  ListResponse,
} from "./types.js";

export interface ListCampaignsParams {
  page?: number;
  per_page?: number;
  status?: string;
  channel?: string;
  sort_by?: string;
  sort_order?: string;
}

export class CampaignClient {
  private client: APIClient;

  constructor(apiClient: APIClient) {
    this.client = apiClient;
  }

  async list(params: ListCampaignsParams = {}): Promise<ListResponse<Campaign>> {
    const queryParams: Record<string, unknown> = {
      page: params.page ?? 1,
      per_page: params.per_page ?? 20,
      sort_by: params.sort_by ?? "created_at",
      sort_order: params.sort_order ?? "desc",
    };
    if (params.status) queryParams.status = params.status;
    if (params.channel) queryParams.channel = params.channel;

    const response = (await this.client.get("/campaigns", queryParams)) as Record<
      string,
      unknown
    >;
    return {
      data: (response.data as Campaign[]) || [],
      total: (response.total as number) || 0,
      page: (response.page as number) || 1,
      per_page: (response.per_page as number) || 20,
      total_pages: (response.total_pages as number) || 0,
    };
  }

  async get(campaignId: string): Promise<Campaign> {
    const response = (await this.client.get(
      `/campaigns/${campaignId}`,
    )) as Record<string, unknown>;
    return response.data as Campaign;
  }

  async create(payload: CampaignCreatePayload): Promise<Campaign> {
    const response = (await this.client.post("/campaigns", payload)) as Record<
      string,
      unknown
    >;
    return response.data as Campaign;
  }

  async update(campaignId: string, payload: CampaignUpdatePayload): Promise<Campaign> {
    const response = (await this.client.patch(
      `/campaigns/${campaignId}`,
      payload,
    )) as Record<string, unknown>;
    return response.data as Campaign;
  }

  async delete(campaignId: string): Promise<void> {
    await this.client.delete(`/campaigns/${campaignId}`);
  }

  async activate(campaignId: string): Promise<Campaign> {
    return this.update(campaignId, { status: "active" });
  }

  async pause(campaignId: string): Promise<Campaign> {
    return this.update(campaignId, { status: "paused" });
  }

  async complete(campaignId: string): Promise<Campaign> {
    return this.update(campaignId, { status: "completed" });
  }

  async archive(campaignId: string): Promise<Campaign> {
    return this.update(campaignId, { status: "archived" });
  }
}
