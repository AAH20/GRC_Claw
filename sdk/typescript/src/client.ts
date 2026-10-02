/**
 * Core API client for the GRC Marketing TypeScript SDK.
 */

import type { Authenticator } from "./auth.js";
import { GRCMarketingError, NetworkError, TimeoutError, raiseForStatus } from "./errors.js";

export interface APIClientConfig {
  baseUrl: string;
  authenticator: Authenticator;
  timeout?: number;
  maxRetries?: number;
}

export interface RequestOptions {
  params?: Record<string, unknown>;
  json?: Record<string, unknown>;
  headers?: Record<string, string>;
}

export class APIClient {
  private baseUrl: string;
  private authenticator: Authenticator;
  private timeout: number;
  private maxRetries: number;

  constructor(config: APIClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.authenticator = config.authenticator;
    this.timeout = config.timeout || 30_000;
    this.maxRetries = config.maxRetries || 3;
  }

  private buildUrl(path: string): string {
    return `${this.baseUrl}${path}`;
  }

  private getHeaders(additional?: Record<string, string>): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
    try {
      const authHeaders = this.authenticator.getAuthHeaders();
      Object.assign(headers, authHeaders);
    } catch {
      // Not authenticated yet
    }
    if (additional) {
      Object.assign(headers, additional);
    }
    return headers;
  }

  async request(
    method: string,
    path: string,
    options: RequestOptions = {},
  ): Promise<Record<string, unknown>> {
    const url = this.buildUrl(path);
    const headers = this.getHeaders(options.headers);

    let lastError: Error | null = null;
    let response: Response | null = null;

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        response = await fetch(url, {
          method: method.toUpperCase(),
          headers,
          body: options.json ? JSON.stringify(options.json) : undefined,
          signal: AbortSignal.timeout(this.timeout),
        });
        break;
      } catch (err) {
        lastError =
          err instanceof Error && err.name === "TimeoutError"
            ? new TimeoutError("Request timed out", this.timeout / 1000)
            : new NetworkError(
                err instanceof Error ? err.message : "Network error",
                err instanceof Error ? err : undefined,
              );
        if (attempt < this.maxRetries - 1) {
          await this.delay(2 ** attempt);
          continue;
        }
        throw lastError;
      }
    }

    if (!response) {
      throw lastError || new NetworkError("Request failed");
    }

    let responseBody: Record<string, unknown> = {};
    try {
      responseBody = (await response.json()) as Record<string, unknown>;
    } catch {
      // Non-JSON response
    }

    if (!response.ok) {
      raiseForStatus(response.status, responseBody);
    }

    return responseBody;
  }

  async get(
    path: string,
    params?: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.request("GET", path, { params });
  }

  async post(
    path: string,
    json?: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.request("POST", path, { json });
  }

  async put(
    path: string,
    json?: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.request("PUT", path, { json });
  }

  async patch(
    path: string,
    json?: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.request("PATCH", path, { json });
  }

  async delete(
    path: string,
    params?: Record<string, unknown>,
  ): Promise<Record<string, unknown>> {
    return this.request("DELETE", path, { params });
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
