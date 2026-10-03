export interface Creator {
  id: string;
  name: string;
  username: string;
  avatar: string;
  bio: string;
  followers: number;
  engagement_rate: number;
  total_earnings: number;
  content_count: number;
  verified: boolean;
  status: "active" | "pending" | "suspended";
  joined_at: string;
  categories: string[];
  social_links: {
    instagram?: string;
    tiktok?: string;
    youtube?: string;
    twitter?: string;
  };
}

export interface Content {
  id: string;
  creator_id: string;
  creator_name: string;
  creator_avatar: string;
  title: string;
  description: string;
  type: "video" | "image" | "story" | "reel" | "blog";
  thumbnail: string;
  status: "draft" | "pending_review" | "approved" | "rejected" | "published";
  views: number;
  likes: number;
  shares: number;
  comments: number;
  created_at: string;
  published_at?: string;
  tags: string[];
  monetization_enabled: boolean;
  earnings: number;
}

export interface Listing {
  id: string;
  creator_id: string;
  creator_name: string;
  title: string;
  description: string;
  content_ids: string[];
  price: number;
  currency: string;
  status: "draft" | "active" | "paused" | "sold" | "expired";
  category: string;
  impressions: number;
  clicks: number;
  conversions: number;
  revenue: number;
  created_at: string;
  expires_at?: string;
}

export interface Transaction {
  id: string;
  type: "sale" | "purchase" | "refund" | "payout" | "fee";
  amount: number;
  currency: string;
  status: "pending" | "completed" | "failed" | "cancelled";
  from_user: string;
  to_user: string;
  listing_id?: string;
  content_id?: string;
  created_at: string;
  completed_at?: string;
  payment_method: string;
  description: string;
}

export interface AnalyticsData {
  total_revenue: number;
  total_transactions: number;
  active_creators: number;
  total_content: number;
  revenue_growth: number;
  creator_growth: number;
  content_growth: number;
  transaction_growth: number;
  revenue_by_month: { month: string; revenue: number }[];
  top_creators: { id: string; name: string; earnings: number }[];
  content_performance: { type: string; count: number; views: number }[];
  recent_activity: { id: string; action: string; user: string; timestamp: string }[];
}

export interface ModerationItem {
  id: string;
  type: "content" | "creator" | "listing" | "dispute";
  target_id: string;
  target_name: string;
  reason: string;
  status: "pending" | "approved" | "rejected" | "escalated";
  priority: "low" | "medium" | "high" | "critical";
  reported_by: string;
  created_at: string;
  resolved_at?: string;
  resolved_by?: string;
  notes: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar: string;
  role: "admin" | "creator" | "buyer" | "moderator";
  status: "active" | "suspended" | "pending";
  created_at: string;
  last_login: string;
}

export interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  link?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  message: string;
  code: string;
  details?: Record<string, string[]>;
}
