// Core domain types for Gated Communities

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'moderator' | 'member';
  reputation: number;
  joinedAt: string;
  lastActive: string;
}

export interface Community {
  id: string;
  name: string;
  slug: string;
  description: string;
  avatar?: string;
  banner?: string;
  tierCount: number;
  memberCount: number;
  createdAt: string;
  updatedAt: string;
  status: 'active' | 'archived' | 'draft';
  visibility: 'public' | 'private' | 'invite-only';
  tags: string[];
}

export interface Tier {
  id: string;
  communityId: string;
  name: string;
  slug: string;
  description: string;
  price: number;
  currency: string;
  billingPeriod: 'monthly' | 'yearly' | 'one-time';
  benefits: string[];
  memberCount: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  color: string;
  icon?: string;
}

export interface Member {
  id: string;
  communityId: string;
  userId: string;
  userName: string;
  userEmail: string;
  userAvatar?: string;
  tierId: string;
  tierName: string;
  role: 'owner' | 'admin' | 'moderator' | 'member';
  status: 'active' | 'pending' | 'suspended' | 'banned';
  reputation: number;
  joinedAt: string;
  lastActive: string;
  metadata: Record<string, unknown>;
}

export interface ModerationItem {
  id: string;
  communityId: string;
  type: 'report' | 'appeal' | 'flag' | 'review';
  status: 'pending' | 'in-review' | 'resolved' | 'dismissed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  reporterId: string;
  reporterName: string;
  targetId: string;
  targetName: string;
  reason: string;
  description: string;
  evidence?: string[];
  createdAt: string;
  updatedAt: string;
  resolvedBy?: string;
  resolution?: string;
}

export interface AnalyticsData {
  period: '7d' | '30d' | '90d' | '1y';
  totalMembers: number;
  activeMembers: number;
  newMembers: number;
  churnedMembers: number;
  revenue: number;
  mrr: number;
  arr: number;
  growthRate: number;
  memberGrowth: DataPoint[];
  revenueHistory: DataPoint[];
  tierDistribution: TierDistribution[];
  topCommunities: CommunityMetric[];
}

export interface DataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface TierDistribution {
  tierId: string;
  tierName: string;
  count: number;
  percentage: number;
  color: string;
}

export interface CommunityMetric {
  communityId: string;
  name: string;
  memberCount: number;
  growthRate: number;
  revenue: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  message: string;
  code: string;
  status: number;
  details?: Record<string, string[]>;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}
