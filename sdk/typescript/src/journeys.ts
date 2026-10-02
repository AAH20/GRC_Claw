/**
 * Journey client for the GRC Marketing TypeScript SDK.
 */

import type { APIClient } from "./client.js";
import type {
  Journey,
  JourneyCreatePayload,
  JourneyUpdatePayload,
  ListResponse,
} from "./types.js";

export interface ListJourneysParams {
  page?: number;
  per_page?: number;
  status?: string;
  sort_by?: string;
  sort_order?: string;
}

export class JourneyClient {
  private client: APIClient;

  constructor(apiClient: APIClient) {
    this.client = apiClient;
  }

  async list(params: ListJourneysParams = {}): Promise<ListResponse<Journey>> {
    const queryParams: Record<string, unknown> = {
      page: params.page ?? 1,
      per_page: params.per_page ?? 20,
      sort_by: params.sort_by ?? "created_at",
      sort_order: params.sort_order ?? "desc",
    };
    if (params.status) queryParams.status = params.status;

    const response = (await this.client.get("/journeys", queryParams)) as Record<
      string,
      unknown
    >;
    return {
      data: (response.data as Journey[]) || [],
      total: (response.total as number) || 0,
      page: (response.page as number) || 1,
      per_page: (response.per_page as number) || 20,
      total_pages: (response.total_pages as number) || 0,
    };
  }

  async get(journeyId: string): Promise<Journey> {
    const response = (await this.client.get(
      `/journeys/${journeyId}`,
    )) as Record<string, unknown>;
    return response.data as Journey;
  }

  async create(payload: JourneyCreatePayload): Promise<Journey> {
    const response = (await this.client.post("/journeys", payload)) as Record<
      string,
      unknown
    >;
    return response.data as Journey;
  }

  async update(journeyId: string, payload: JourneyUpdatePayload): Promise<Journey> {
    const response = (await this.client.patch(
      `/journeys/${journeyId}`,
      payload,
    )) as Record<string, unknown>;
    return response.data as Journey;
  }

  async delete(journeyId: string): Promise<void> {
    await this.client.delete(`/journeys/${journeyId}`);
  }

  async activate(journeyId: string): Promise<Journey> {
    return this.update(journeyId, { status: "active" });
  }

  async pause(journeyId: string): Promise<Journey> {
    return this.update(journeyId, { status: "paused" });
  }

  async complete(journeyId: string): Promise<Journey> {
    return this.update(journeyId, { status: "completed" });
  }
}
