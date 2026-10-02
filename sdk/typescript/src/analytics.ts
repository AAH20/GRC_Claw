/**
 * Analytics client for the GRC Marketing TypeScript SDK.
 */

import type { APIClient } from "./client.js";
import type { AnalyticsReport } from "./types.js";

export interface GetReportParams {
  start_date?: string;
  end_date?: string;
  metrics?: string[];
  dimensions?: string[];
  filters?: Record<string, unknown>;
}

export interface GetCampaignPerformanceParams {
  start_date?: string;
  end_date?: string;
  campaign_ids?: string[];
}

export interface GetLeadFunnelParams {
  start_date?: string;
  end_date?: string;
}

export interface GetChannelPerformanceParams {
  start_date?: string;
  end_date?: string;
}

export interface GetJourneyAnalyticsParams {
  journey_id: string;
  start_date?: string;
  end_date?: string;
}

export class AnalyticsClient {
  private client: APIClient;

  constructor(apiClient: APIClient) {
    this.client = apiClient;
  }

  async getReport(params: GetReportParams = {}): Promise<AnalyticsReport> {
    const payload: Record<string, unknown> = {};
    if (params.start_date) payload.start_date = params.start_date;
    if (params.end_date) payload.end_date = params.end_date;
    if (params.metrics) payload.metrics = params.metrics;
    if (params.dimensions) payload.dimensions = params.dimensions;
    if (params.filters) payload.filters = params.filters;

    const response = (await this.client.post(
      "/analytics/report",
      payload,
    )) as Record<string, unknown>;
    return response.data as AnalyticsReport;
  }

  async getCampaignPerformance(
    params: GetCampaignPerformanceParams = {},
  ): Promise<AnalyticsReport> {
    const payload: Record<string, unknown> = {
      metrics: ["impressions", "clicks", "conversions", "spend", "revenue"],
      dimensions: ["campaign_id", "campaign_name"],
    };
    if (params.start_date) payload.start_date = params.start_date;
    if (params.end_date) payload.end_date = params.end_date;
    if (params.campaign_ids) payload.filters = { campaign_id: params.campaign_ids };

    const response = (await this.client.post(
      "/analytics/campaigns",
      payload,
    )) as Record<string, unknown>;
    return response.data as AnalyticsReport;
  }

  async getLeadFunnel(
    params: GetLeadFunnelParams = {},
  ): Promise<AnalyticsReport> {
    const payload: Record<string, unknown> = {
      metrics: ["total_leads", "qualified_leads", "converted_leads", "conversion_rate"],
      dimensions: ["stage"],
    };
    if (params.start_date) payload.start_date = params.start_date;
    if (params.end_date) payload.end_date = params.end_date;

    const response = (await this.client.post(
      "/analytics/lead-funnel",
      payload,
    )) as Record<string, unknown>;
    return response.data as AnalyticsReport;
  }

  async getChannelPerformance(
    params: GetChannelPerformanceParams = {},
  ): Promise<AnalyticsReport> {
    const payload: Record<string, unknown> = {
      metrics: ["impressions", "clicks", "conversions", "spend", "revenue", "roas"],
      dimensions: ["channel"],
    };
    if (params.start_date) payload.start_date = params.start_date;
    if (params.end_date) payload.end_date = params.end_date;

    const response = (await this.client.post(
      "/analytics/channels",
      payload,
    )) as Record<string, unknown>;
    return response.data as AnalyticsReport;
  }

  async getJourneyAnalytics(
    params: GetJourneyAnalyticsParams,
  ): Promise<AnalyticsReport> {
    const payload: Record<string, unknown> = {
      metrics: ["enrollments", "completions", "drop_offs", "conversion_rate"],
      dimensions: ["step"],
      filters: { journey_id: params.journey_id },
    };
    if (params.start_date) payload.start_date = params.start_date;
    if (params.end_date) payload.end_date = params.end_date;

    const response = (await this.client.post(
      "/analytics/journeys",
      payload,
    )) as Record<string, unknown>;
    return response.data as AnalyticsReport;
  }
}
