import type {
  ApiError,
  AuthResponse,
  AuthTokens,
  Community,
  Member,
  ModerationItem,
  PaginatedResponse,
  Tier,
  User,
  LoginRequest,
  RegisterRequest,
  AnalyticsData,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private tokenExpiry: number = 0;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setTokens(tokens: AuthTokens): void {
    this.accessToken = tokens.accessToken;
    this.refreshToken = tokens.refreshToken;
    this.tokenExpiry = tokens.expiresAt;
  }

  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    this.tokenExpiry = 0;
  }

  private isTokenExpired(): boolean {
    return Date.now() >= this.tokenExpiry - 60000; // 1 min buffer
  }

  private async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken: this.refreshToken }),
      });

      if (!response.ok) {
        this.clearTokens();
        return false;
      }

      const data: AuthResponse = await response.json();
      this.setTokens(data.tokens);
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    if (this.accessToken && this.isTokenExpired()) {
      const refreshed = await this.refreshAccessToken();
      if (!refreshed) {
        throw this.createError('Session expired. Please log in again.', 'AUTH_EXPIRED', 401);
      }
    }

    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    let response: Response;
    try {
      response = await fetch(url, { ...options, headers });
    } catch {
      throw this.createError('Network error. Please check your connection.', 'NETWORK_ERROR', 0);
    }

    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const error = data as ApiError | null;
      throw this.createError(
        error?.message || `Request failed with status ${response.status}`,
        error?.code || 'UNKNOWN_ERROR',
        response.status,
        error?.details
      );
    }

    return data as T;
  }

  private createError(
    message: string,
    code: string,
    status: number,
    details?: Record<string, string[]>
  ): ApiError {
    return { message, code, status, details };
  }

  // Auth
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    this.setTokens(response.tokens);
    return response;
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setTokens(response.tokens);
    return response;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.clearTokens();
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Communities
  async getCommunities(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    status?: string;
    visibility?: string;
  }): Promise<PaginatedResponse<Community>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.pageSize) searchParams.set('pageSize', String(params.pageSize));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.visibility) searchParams.set('visibility', params.visibility);
    const qs = searchParams.toString();
    return this.request<PaginatedResponse<Community>>(`/communities${qs ? `?${qs}` : ''}`);
  }

  async getCommunity(id: string): Promise<Community> {
    return this.request<Community>(`/communities/${id}`);
  }

  async createCommunity(data: Partial<Community>): Promise<Community> {
    return this.request<Community>('/communities', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateCommunity(id: string, data: Partial<Community>): Promise<Community> {
    return this.request<Community>(`/communities/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteCommunity(id: string): Promise<void> {
    return this.request<void>(`/communities/${id}`, { method: 'DELETE' });
  }

  // Tiers
  async getTiers(communityId: string): Promise<Tier[]> {
    return this.request<Tier[]>(`/communities/${communityId}/tiers`);
  }

  async createTier(communityId: string, data: Partial<Tier>): Promise<Tier> {
    return this.request<Tier>(`/communities/${communityId}/tiers`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTier(communityId: string, tierId: string, data: Partial<Tier>): Promise<Tier> {
    return this.request<Tier>(`/communities/${communityId}/tiers/${tierId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteTier(communityId: string, tierId: string): Promise<void> {
    return this.request<void>(`/communities/${communityId}/tiers/${tierId}`, {
      method: 'DELETE',
    });
  }

  // Members
  async getMembers(
    communityId: string,
    params?: { page?: number; pageSize?: number; search?: string; status?: string; tierId?: string }
  ): Promise<PaginatedResponse<Member>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.pageSize) searchParams.set('pageSize', String(params.pageSize));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.tierId) searchParams.set('tierId', params.tierId);
    const qs = searchParams.toString();
    return this.request<PaginatedResponse<Member>>(
      `/communities/${communityId}/members${qs ? `?${qs}` : ''}`
    );
  }

  async updateMemberStatus(
    communityId: string,
    memberId: string,
    status: Member['status']
  ): Promise<Member> {
    return this.request<Member>(`/communities/${communityId}/members/${memberId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  async removeMember(communityId: string, memberId: string): Promise<void> {
    return this.request<void>(`/communities/${communityId}/members/${memberId}`, {
      method: 'DELETE',
    });
  }

  // Moderation
  async getModerationQueue(
    communityId: string,
    params?: { page?: number; pageSize?: number; status?: string; priority?: string; type?: string }
  ): Promise<PaginatedResponse<ModerationItem>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.pageSize) searchParams.set('pageSize', String(params.pageSize));
    if (params?.status) searchParams.set('status', params.status);
    if (params?.priority) searchParams.set('priority', params.priority);
    if (params?.type) searchParams.set('type', params.type);
    const qs = searchParams.toString();
    return this.request<PaginatedResponse<ModerationItem>>(
      `/communities/${communityId}/moderation${qs ? `?${qs}` : ''}`
    );
  }

  async resolveModerationItem(
    communityId: string,
    itemId: string,
    resolution: string
  ): Promise<ModerationItem> {
    return this.request<ModerationItem>(
      `/communities/${communityId}/moderation/${itemId}/resolve`,
      { method: 'POST', body: JSON.stringify({ resolution }) }
    );
  }

  async dismissModerationItem(communityId: string, itemId: string): Promise<ModerationItem> {
    return this.request<ModerationItem>(
      `/communities/${communityId}/moderation/${itemId}/dismiss`,
      { method: 'POST' }
    );
  }

  // Analytics
  async getAnalytics(communityId: string, period: AnalyticsData['period'] = '30d'): Promise<AnalyticsData> {
    return this.request<AnalyticsData>(`/communities/${communityId}/analytics?period=${period}`);
  }

  async getGlobalAnalytics(period: AnalyticsData['period'] = '30d'): Promise<AnalyticsData> {
    return this.request<AnalyticsData>(`/analytics?period=${period}`);
  }
}

// Singleton instance
export const apiClient = new ApiClient(API_BASE_URL);
export default apiClient;
