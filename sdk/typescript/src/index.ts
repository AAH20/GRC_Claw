/**
 * GRC Marketing SDK — TypeScript client library.
 *
 * Provides a high-level, typed interface to the GRC Marketing API for managing
 * campaigns, leads, journeys, and analytics.
 */

import { Authenticator } from "./auth.js";
import { APIClient } from "./client.js";
import { CampaignClient } from "./campaigns.js";
import { LeadClient } from "./leads.js";
import { JourneyClient } from "./journeys.js";
import { AnalyticsClient } from "./analytics.js";
import { ConfigurationError } from "./errors.js";
import type { AuthToken } from "./types.js";

export { Authenticator } from "./auth.js";
export { APIClient } from "./client.js";
export { CampaignClient } from "./campaigns.js";
export { LeadClient } from "./leads.js";
export { JourneyClient } from "./journeys.js";
export { AnalyticsClient } from "./analytics.js";
export * from "./errors.js";
export * from "./types.js";

export interface GRCMarketingConfig {
  baseUrl: string;
  apiKey?: string;
  clientId?: string;
  clientSecret?: string;
  tokenUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

export class GRCMarketing {
  public readonly authenticator: Authenticator;
  public readonly campaigns: CampaignClient;
  public readonly leads: LeadClient;
  public readonly journeys: JourneyClient;
  public readonly analytics: AnalyticsClient;

  private apiClient: APIClient;

  constructor(config: GRCMarketingConfig) {
    this.authenticator = new Authenticator({
      baseUrl: config.baseUrl,
      apiKey: config.apiKey,
      clientId: config.clientId,
      clientSecret: config.clientSecret,
      tokenUrl: config.tokenUrl,
      timeout: config.timeout,
    });

    this.apiClient = new APIClient({
      baseUrl: config.baseUrl,
      authenticator: this.authenticator,
      timeout: config.timeout,
      maxRetries: config.maxRetries,
    });

    this.campaigns = new CampaignClient(this.apiClient);
    this.leads = new LeadClient(this.apiClient);
    this.journeys = new JourneyClient(this.apiClient);
    this.analytics = new AnalyticsClient(this.apiClient);
  }

  async authenticate(): Promise<AuthToken> {
    if (this.authenticator["apiKey"]) {
      return this.authenticator.authenticateApiKey(this.authenticator["apiKey"]);
    }
    if (this.authenticator["clientId"] && this.authenticator["clientSecret"]) {
      return this.authenticator.authenticateOAuth2();
    }
    throw new ConfigurationError(
      "No credentials configured. Provide apiKey or clientId/clientSecret.",
    );
  }

  isAuthenticated(): boolean {
    return this.authenticator.isAuthenticated();
  }

  logout(): void {
    this.authenticator.logout();
  }
}
