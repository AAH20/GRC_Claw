/**
 * Authentication module for the GRC Marketing TypeScript SDK.
 */

import type { AuthToken } from "./types.js";
import { AuthenticationError, NetworkError, TimeoutError } from "./errors.js";

export interface AuthenticatorConfig {
  baseUrl: string;
  apiKey?: string;
  clientId?: string;
  clientSecret?: string;
  tokenUrl?: string;
  timeout?: number;
}

export class Authenticator {
  public readonly baseUrl: string;
  public readonly apiKey?: string;
  public readonly clientId?: string;
  public readonly clientSecret?: string;
  private tokenUrl: string;
  private timeout: number;
  private token: AuthToken | null = null;

  constructor(config: AuthenticatorConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.apiKey = config.apiKey;
    this.clientId = config.clientId;
    this.clientSecret = config.clientSecret;
    this.tokenUrl = config.tokenUrl || `${this.baseUrl}/oauth/token`;
    this.timeout = config.timeout || 30_000;
  }

  get currentToken(): AuthToken | null {
    return this.token;
  }

  isAuthenticated(): boolean {
    if (!this.token) return false;
    const expiresAt = new Date(this.token.obtained_at).getTime() + this.token.expires_in * 1000;
    return Date.now() < expiresAt;
  }

  async authenticateApiKey(apiKey: string): Promise<AuthToken> {
    this.apiKey = apiKey;
    try {
      const response = await fetch(`${this.baseUrl}/auth/api-key`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey }),
        signal: AbortSignal.timeout(this.timeout),
      });

      if (!response.ok) {
        throw new AuthenticationError(
          `API key authentication failed: ${response.statusText}`,
        );
      }

      const data = (await response.json()) as Record<string, unknown>;
      this.token = this.parseToken(data);
      return this.token;
    } catch (err) {
      if (err instanceof AuthenticationError) throw err;
      if (err instanceof Error && err.name === "TimeoutError") {
        throw new TimeoutError("Request timed out", this.timeout / 1000);
      }
      throw new NetworkError(
        err instanceof Error ? err.message : "Network error",
        err instanceof Error ? err : undefined,
      );
    }
  }

  async authenticateOAuth2(
    clientId?: string,
    clientSecret?: string,
  ): Promise<AuthToken> {
    const cid = clientId || this.clientId;
    const csecret = clientSecret || this.clientSecret;

    if (!cid || !csecret) {
      throw new AuthenticationError(
        "client_id and client_secret are required for OAuth2 authentication",
      );
    }

    try {
      const response = await fetch(this.tokenUrl, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          grant_type: "client_credentials",
          client_id: cid,
          client_secret: csecret,
        }),
        signal: AbortSignal.timeout(this.timeout),
      });

      if (!response.ok) {
        throw new AuthenticationError(
          `OAuth2 authentication failed: ${response.statusText}`,
        );
      }

      const data = (await response.json()) as Record<string, unknown>;
      this.token = this.parseToken(data);
      return this.token;
    } catch (err) {
      if (err instanceof AuthenticationError) throw err;
      if (err instanceof Error && err.name === "TimeoutError") {
        throw new TimeoutError("Request timed out", this.timeout / 1000);
      }
      throw new NetworkError(
        err instanceof Error ? err.message : "Network error",
        err instanceof Error ? err : undefined,
      );
    }
  }

  async refreshToken(): Promise<AuthToken> {
    if (!this.token?.refresh_token) {
      throw new AuthenticationError("No refresh token available");
    }

    try {
      const response = await fetch(this.tokenUrl, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          grant_type: "refresh_token",
          refresh_token: this.token.refresh_token,
          client_id: this.clientId || "",
          client_secret: this.clientSecret || "",
        }),
        signal: AbortSignal.timeout(this.timeout),
      });

      if (!response.ok) {
        throw new AuthenticationError(
          `Token refresh failed: ${response.statusText}`,
        );
      }

      const data = (await response.json()) as Record<string, unknown>;
      this.token = this.parseToken(data);
      return this.token;
    } catch (err) {
      if (err instanceof AuthenticationError) throw err;
      if (err instanceof Error && err.name === "TimeoutError") {
        throw new TimeoutError("Request timed out", this.timeout / 1000);
      }
      throw new NetworkError(
        err instanceof Error ? err.message : "Network error",
        err instanceof Error ? err : undefined,
      );
    }
  }

  getAuthHeaders(): Record<string, string> {
    if (!this.isAuthenticated()) {
      throw new AuthenticationError(
        "Not authenticated. Call authenticateApiKey() or authenticateOAuth2() first.",
      );
    }
    return {
      Authorization: `${this.token!.token_type} ${this.token!.access_token}`,
    };
  }

  logout(): void {
    this.token = null;
  }

  private parseToken(data: Record<string, unknown>): AuthToken {
    return {
      access_token: data.access_token as string,
      token_type: (data.token_type as string) || "Bearer",
      expires_in: (data.expires_in as number) || 3600,
      refresh_token: data.refresh_token as string | undefined,
      scope: data.scope as string | undefined,
      obtained_at: new Date().toISOString(),
    };
  }
}
