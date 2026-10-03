'use client';

import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Post {
  id: string;
  title: string;
  content: string;
  author: {
    id: string;
    name: string;
    avatar: string;
  };
  community: {
    id: string;
    name: string;
  };
  tags: string[];
  createdAt: string;
  updatedAt: string;
  likes: number;
  comments: number;
  isLiked: boolean;
  isPinned: boolean;
}

interface CreatePostFormData {
  title: string;
  content: string;
  communityId: string;
  tags: string[];
}

interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

type SortOption = 'latest' | 'oldest' | 'popular' | 'most-commented';
type TimeFilter = 'all' | 'today' | 'week' | 'month' | 'year';

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_COMMUNITIES = [
  { id: 'c1', name: 'General' },
  { id: 'c2', name: 'Announcements' },
  { id: 'c3', name: 'Introductions' },
  { id: 'c4', name: 'Feedback' },
  { id: 'c5', name: 'Events' },
];

const MOCK_POSTS: Post[] = [
  {
    id: 'p1',
    title: 'Welcome to Gated Communities!',
    content:
      'This is the first post in our gated community platform. We are excited to have you here. Feel free to introduce yourself and share your thoughts on what you would like to see in this space.\n\nOur goal is to create a safe and productive environment for meaningful discussions.',
    author: { id: 'u1', name: 'Admin User', avatar: '/avatars/admin.png' },
    community: { id: 'c2', name: 'Announcements' },
    tags: ['welcome', 'meta'],
    createdAt: '2026-10-01T10:00:00Z',
    updatedAt: '2026-10-01T10:00:00Z',
    likes: 42,
    comments: 15,
    isLiked: false,
    isPinned: true,
  },
  {
    id: 'p2',
    title: 'Best practices for community engagement',
    content:
      'After running several communities over the years, here are my top tips:\n\n1. Be consistent with your posting schedule\n2. Ask open-ended questions\n3. Acknowledge every response\n4. Use polls to drive participation\n5. Create weekly threads for recurring topics\n\nWhat has worked for you?',
    author: { id: 'u2', name: 'Sarah Chen', avatar: '/avatars/sarah.png' },
    community: { id: 'c1', name: 'General' },
    tags: ['tips', 'engagement'],
    createdAt: '2026-10-02T14:30:00Z',
    updatedAt: '2026-10-02T14:30:00Z',
    likes: 28,
    comments: 12,
    isLiked: true,
    isPinned: false,
  },
  {
    id: 'p3',
    title: 'October Community Event — Save the Date!',
    content:
      'We are hosting our monthly community meetup on October 15th at 7 PM UTC.\n\nAgenda:\n- Community updates\n- Member spotlight\n- Q&A session\n- Networking\n\nRSVP by replying to this post!',
    author: { id: 'u3', name: 'Mike Johnson', avatar: '/avatars/mike.png' },
    community: { id: 'c5', name: 'Events' },
    tags: ['event', 'meetup', 'october'],
    createdAt: '2026-10-03T09:15:00Z',
    updatedAt: '2026-10-03T09:15:00Z',
    likes: 35,
    comments: 22,
    isLiked: false,
    isPinned: false,
  },
  {
    id: 'p4',
    title: 'Feature Request: Dark Mode',
    content:
      'I would love to see a dark mode option for the platform. Many of us browse communities late at night and the bright interface can be harsh on the eyes.\n\nWould anyone else find this useful?',
    author: { id: 'u4', name: 'Alex Rivera', avatar: '/avatars/alex.png' },
    community: { id: 'c4', name: 'Feedback' },
    tags: ['feature-request', 'ui'],
    createdAt: '2026-10-03T16:45:00Z',
    updatedAt: '2026-10-03T16:45:00Z',
    likes: 19,
    comments: 8,
    isLiked: false,
    isPinned: false,
  },
  {
    id: 'p5',
    title: 'Introducing myself — new member',
    content:
      'Hi everyone! I am Alex, a software developer with a passion for open source and community building. I have been following this community for a while and finally decided to join.\n\nLooking forward to contributing and learning from all of you!',
    author: { id: 'u4', name: 'Alex Rivera', avatar: '/avatars/alex.png' },
    community: { id: 'c3', name: 'Introductions' },
    tags: ['introduction'],
    createdAt: '2026-10-03T18:00:00Z',
    updatedAt: '2026-10-03T18:00:00Z',
    likes: 14,
    comments: 6,
    isLiked: false,
    isPinned: false,
  },
  {
    id: 'p6',
    title: 'Weekly Discussion Thread — Oct 3',
    content:
      'This is our weekly discussion thread. Share what you are working on, ask for help, or just chat with fellow community members.\n\nKeep it friendly and on-topic!',
    author: { id: 'u1', name: 'Admin User', avatar: '/avatars/admin.png' },
    community: { id: 'c1', name: 'General' },
    tags: ['weekly', 'discussion'],
    createdAt: '2026-10-03T08:00:00Z',
    updatedAt: '2026-10-03T08:00:00Z',
    likes: 11,
    comments: 34,
    isLiked: false,
    isPinned: false,
  },
  {
    id: 'p7',
    title: 'Platform Update: New Moderation Tools',
    content:
      'We have rolled out new moderation tools to help community managers keep discussions healthy.\n\nNew features:\n- Auto-flag for spam\n- User warning system\n- Post approval queues\n- Activity reports\n\nCheck the docs for details on how to enable these for your community.',
    author: { id: 'u1', name: 'Admin User', avatar: '/avatars/admin.png' },
    community: { id: 'c2', name: 'Announcements' },
    tags: ['update', 'moderation', 'platform'],
    createdAt: '2026-10-02T11:00:00Z',
    updatedAt: '2026-10-02T11:00:00Z',
    likes: 56,
    comments: 18,
    isLiked: true,
    isPinned: false,
  },
  {
    id: 'p8',
    title: 'What are you reading this month?',
    content:
      'Share what books, articles, or blogs you are currently reading. I will start: I am reading "The Pragmatic Programmer" for the third time and still finding new insights.\n\nWhat about you?',
    author: { id: 'u2', name: 'Sarah Chen', avatar: '/avatars/sarah.png' },
    community: { id: 'c1', name: 'General' },
    tags: ['books', 'reading', 'monthly'],
    createdAt: '2026-10-01T20:00:00Z',
    updatedAt: '2026-10-01T20:00:00Z',
    likes: 23,
    comments: 27,
    isLiked: false,
    isPinned: false,
  },
  {
    id: 'p9',
    title: 'Community Guidelines Update',
    content:
      'We have updated our community guidelines to better reflect our values and expectations. Key changes:\n\n- Clearer rules on self-promotion\n- Updated code of conduct\n- New process for reporting violations\n\nPlease take a moment to review the updated guidelines.',
    author: { id: 'u1', name: 'Admin User', avatar: '/avatars/admin.png' },
    community: { id: 'c2', name: 'Announcements' },
    tags: ['guidelines', 'rules', 'update'],
    createdAt: '2026-09-30T12:00:00Z',
    updatedAt: '2026-09-30T12:00:00Z',
    likes: 31,
    comments: 9,
    isLiked: false,
    isPinned: false,
  },
  {
    id: 'p10',
    title: 'Showcase: My home lab setup',
    content:
      'I finally organized my home lab and wanted to share the setup:\n\n- Rack-mounted server with Proxmox\n- 3-node Kubernetes cluster\n- NAS with 40TB storage\n- Ubiquiti networking gear\n\nHappy to answer any questions about the setup!',
    author: { id: 'u3', name: 'Mike Johnson', avatar: '/avatars/mike.png' },
    community: { id: 'c1', name: 'General' },
    tags: ['showcase', 'homelab', 'tech'],
    createdAt: '2026-09-29T15:30:00Z',
    updatedAt: '2026-09-29T15:30:00Z',
    likes: 47,
    comments: 20,
    isLiked: true,
    isPinned: false,
  },
  {
    id: 'p11',
    title: 'Poll: Preferred meeting times',
    content:
      'We want to schedule our community calls at a time that works for everyone. Please vote on your preferred time slot:\n\n- Morning (9 AM UTC)\n- Afternoon (2 PM UTC)\n- Evening (7 PM UTC)\n\nThe most popular time will be used for future events.',
    author: { id: 'u1', name: 'Admin User', avatar: '/avatars/admin.png' },
    community: { id: 'c5', name: 'Events' },
    tags: ['poll', 'scheduling'],
    createdAt: '2026-09-28T10:00:00Z',
    updatedAt: '2026-09-28T10:00:00Z',
    likes: 16,
    comments: 41,
    isLiked: false,
    isPinned: false,
  },
  {
    id: 'p12',
    title: 'Tips for writing better documentation',
    content:
      'Documentation is often an afterthought, but good docs can make or break a project. Here are my tips:\n\n1. Write for your audience\n2. Use examples liberally\n3. Keep it up-to-date\n4. Make it searchable\n5. Include troubleshooting sections\n\nWhat are your documentation best practices?',
    author: { id: 'u2', name: 'Sarah Chen', avatar: '/avatars/sarah.png' },
    community: { id: 'c1', name: 'General' },
    tags: ['documentation', 'writing', 'tips'],
    createdAt: '2026-09-27T14:00:00Z',
    updatedAt: '2026-09-27T14:00:00Z',
    likes: 38,
    comments: 14,
    isLiked: false,
    isPinned: false,
  },
];

// ─── Utility Functions ───────────────────────────────────────────────────────

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function isWithinTimeFilter(dateString: string, filter: TimeFilter): boolean {
  if (filter === 'all') return true;
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = diffMs / 86400000;

  switch (filter) {
    case 'today':
      return diffDays < 1;
    case 'week':
      return diffDays < 7;
    case 'month':
      return diffDays < 30;
    case 'year':
      return diffDays < 365;
    default:
      return true;
  }
}

// ─── Components ──────────────────────────────────────────────────────────────

// ── Search & Filter Bar ──────────────────────────────────────────────────────

interface SearchFilterBarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedCommunity: string;
  onCommunityChange: (communityId: string) => void;
  sortBy: SortOption;
  onSortChange: (sort: SortOption) => void;
  timeFilter: TimeFilter;
  onTimeFilterChange: (filter: TimeFilter) => void;
  onCreatePost: () => void;
}

function SearchFilterBar({
  searchQuery,
  onSearchChange,
  selectedCommunity,
  onCommunityChange,
  sortBy,
  onSortChange,
  timeFilter,
  onTimeFilterChange,
  onCreatePost,
}: SearchFilterBarProps) {
  const [showFilters, setShowFilters] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6 shadow-sm">
      {/* Top row: Search + Create button */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Search posts..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-colors text-sm"
          />
        </div>
        <button
          onClick={onCreatePost}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors whitespace-nowrap"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Post
        </button>
      </div>

      {/* Filter toggle for mobile */}
      <button
        onClick={() => setShowFilters(!showFilters)}
        className="sm:hidden mt-3 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
          />
        </svg>
        {showFilters ? 'Hide Filters' : 'Show Filters'}
      </button>

      {/* Filter row */}
      <div className={`${showFilters ? 'flex' : 'hidden'} sm:flex flex-col sm:flex-row gap-3 mt-3 sm:mt-0`}>
        <select
          value={selectedCommunity}
          onChange={(e) => onCommunityChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white"
        >
          <option value="all">All Communities</option>
          {MOCK_COMMUNITIES.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value as SortOption)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white"
        >
          <option value="latest">Latest</option>
          <option value="oldest">Oldest</option>
          <option value="popular">Most Popular</option>
          <option value="most-commented">Most Commented</option>
        </select>

        <select
          value={timeFilter}
          onChange={(e) => onTimeFilterChange(e.target.value as TimeFilter)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white"
        >
          <option value="all">All Time</option>
          <option value="today">Today</option>
          <option value="week">This Week</option>
          <option value="month">This Month</option>
          <option value="year">This Year</option>
        </select>
      </div>
    </div>
  );
}

// ── Post Card ────────────────────────────────────────────────────────────────

interface PostCardProps {
  post: Post;
  onPostClick: (post: Post) => void;
  onLike: (postId: string) => void;
}

function PostCard({ post, onPostClick, onLike }: PostCardProps) {
  return (
    <article
      className="bg-white border border-gray-200 rounded-xl p-5 hover:shadow-md transition-shadow cursor-pointer group"
      onClick={() => onPostClick(post)}
    >
      {/* Pinned indicator */}
      {post.isPinned && (
        <div className="flex items-center gap-1.5 text-xs text-amber-600 font-medium mb-2">
          <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L11 4.323V3a1 1 0 011-1z" />
          </svg>
          Pinned
        </div>
      )}

      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
          {post.author.name.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm text-gray-900">{post.author.name}</span>
            <span className="text-gray-400">·</span>
            <span className="text-xs text-gray-500">{formatDate(post.createdAt)}</span>
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700">
              {post.community.name}
            </span>
          </div>
        </div>
      </div>

      {/* Content */}
      <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-indigo-600 transition-colors line-clamp-2">
        {post.title}
      </h3>
      <p className="text-sm text-gray-600 mb-3 line-clamp-3">{post.content}</p>

      {/* Tags */}
      {post.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {post.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center gap-4 pt-3 border-t border-gray-100">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onLike(post.id);
          }}
          className={`inline-flex items-center gap-1.5 text-sm transition-colors ${
            post.isLiked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'
          }`}
        >
          <svg
            className="w-4 h-4"
            fill={post.isLiked ? 'currentColor' : 'none'}
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
            />
          </svg>
          {post.likes}
        </button>
        <button className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          {post.comments}
        </button>
        <button className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 transition-colors ml-auto">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
            />
          </svg>
          Share
        </button>
      </div>
    </article>
  );
}

// ── Pagination ───────────────────────────────────────────────────────────────

interface PaginationProps {
  meta: PaginationMeta;
  onPageChange: (page: number) => void;
}

function Pagination({ meta, onPageChange }: PaginationProps) {
  const { page, totalPages } = meta;

  const getPageNumbers = useCallback(() => {
    const pages: (number | string)[] = [];
    const delta = 2;

    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= page - delta && i <= page + delta)) {
        pages.push(i);
      } else if (pages[pages.length - 1] !== '...') {
        pages.push('...');
      }
    }
    return pages;
  }, [page, totalPages]);

  if (totalPages <= 1) return null;

  return (
    <nav className="flex items-center justify-center gap-1 mt-8" aria-label="Pagination">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
        className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Previous
      </button>

      {getPageNumbers().map((p, idx) =>
        p === '...' ? (
          <span key={`ellipsis-${idx}`} className="px-3 py-2 text-sm text-gray-500">
            ...
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p as number)}
            className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              p === page
                ? 'bg-indigo-600 text-white'
                : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {p}
          </button>
        )
      )}

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages}
        className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Next
      </button>
    </nav>
  );
}

// ── Post Detail Modal ────────────────────────────────────────────────────────

interface PostDetailModalProps {
  post: Post | null;
  onClose: () => void;
  onLike: (postId: string) => void;
}

function PostDetailModal({ post, onClose, onLike }: PostDetailModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const [commentText, setCommentText] = useState('');
  const [comments, setComments] = useState<
    { id: string; author: string; content: string; createdAt: string }[]
  >([]);

  useEffect(() => {
    if (post) {
      setComments([
        {
          id: 'cm1',
          author: 'Sarah Chen',
          content: 'Great post! Thanks for sharing.',
          createdAt: '2026-10-02T15:00:00Z',
        },
        {
          id: 'cm2',
          author: 'Mike Johnson',
          content: 'I agree with the points raised here. Looking forward to more discussions.',
          createdAt: '2026-10-02T16:30:00Z',
        },
      ]);
    }
  }, [post]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (post) {
      document.addEventListener('keydown', handleEsc);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = '';
    };
  }, [post, onClose]);

  if (!post) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  const handleSubmitComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    setComments((prev) => [
      ...prev,
      {
        id: `cm-${Date.now()}`,
        author: 'You',
        content: commentText.trim(),
        createdAt: new Date().toISOString(),
      },
    ]);
    setCommentText('');
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="post-detail-title"
    >
      <div
        ref={modalRef}
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Modal header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 id="post-detail-title" className="text-lg font-semibold text-gray-900 truncate pr-4">
            {post.title}
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Author info */}
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-sm font-semibold">
              {post.author.name.charAt(0)}
            </div>
            <div>
              <div className="font-medium text-sm text-gray-900">{post.author.name}</div>
              <div className="text-xs text-gray-500">
                {formatDate(post.createdAt)} · {post.community.name}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="prose prose-sm max-w-none text-gray-700 mb-4 whitespace-pre-wrap">
            {post.content}
          </div>

          {/* Tags */}
          {post.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-4">
              {post.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-4 py-3 border-t border-b border-gray-100 mb-4">
            <button
              onClick={() => onLike(post.id)}
              className={`inline-flex items-center gap-1.5 text-sm font-medium transition-colors ${
                post.isLiked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'
              }`}
            >
              <svg
                className="w-5 h-5"
                fill={post.isLiked ? 'currentColor' : 'none'}
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
              {post.likes} Likes
            </button>
            <span className="inline-flex items-center gap-1.5 text-sm text-gray-500">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              {post.comments} Comments
            </span>
          </div>

          {/* Comments section */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Comments</h3>

            {/* Comment form */}
            <form onSubmit={handleSubmitComment} className="mb-4">
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-teal-500 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
                  Y
                </div>
                <div className="flex-1">
                  <textarea
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    placeholder="Write a comment..."
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
                  />
                  <div className="flex justify-end mt-2">
                    <button
                      type="submit"
                      disabled={!commentText.trim()}
                      className="px-4 py-1.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Post Comment
                    </button>
                  </div>
                </div>
              </div>
            </form>

            {/* Comment list */}
            <div className="space-y-3">
              {comments.map((comment) => (
                <div key={comment.id} className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-300 to-gray-400 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
                    {comment.author.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">{comment.author}</span>
                      <span className="text-xs text-gray-500">{formatDate(comment.createdAt)}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-0.5">{comment.content}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Create Post Form ─────────────────────────────────────────────────────────

interface CreatePostFormProps {
  onClose: () => void;
  onSubmit: (data: CreatePostFormData) => void;
}

function CreatePostForm({ onClose, onSubmit }: CreatePostFormProps) {
  const [formData, setFormData] = useState<CreatePostFormData>({
    title: '',
    content: '',
    communityId: '',
    tags: [],
  });
  const [tagInput, setTagInput] = useState('');
  const [errors, setErrors] = useState<Partial<Record<keyof CreatePostFormData, string>>>({});

  const validate = useCallback((): boolean => {
    const newErrors: Partial<Record<keyof CreatePostFormData, string>> = {};
    if (!formData.title.trim()) newErrors.title = 'Title is required';
    if (formData.title.length > 200) newErrors.title = 'Title must be under 200 characters';
    if (!formData.content.trim()) newErrors.content = 'Content is required';
    if (!formData.communityId) newErrors.communityId = 'Please select a community';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    onSubmit({
      ...formData,
      title: formData.title.trim(),
      content: formData.content.trim(),
    });
  };

  const addTag = useCallback(() => {
    const tag = tagInput.trim().toLowerCase().replace(/[^a-z0-9-]/g, '');
    if (tag && !formData.tags.includes(tag) && formData.tags.length < 5) {
      setFormData((prev) => ({ ...prev, tags: [...prev.tags, tag] }));
    }
    setTagInput('');
  }, [tagInput, formData.tags]);

  const removeTag = useCallback((tagToRemove: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.filter((t) => t !== tagToRemove),
    }));
  }, []);

  const handleTagKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-post-title"
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 id="create-post-title" className="text-lg font-semibold text-gray-900">
            Create New Post
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close form"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {/* Community select */}
          <div>
            <label htmlFor="community" className="block text-sm font-medium text-gray-700 mb-1">
              Community <span className="text-red-500">*</span>
            </label>
            <select
              id="community"
              value={formData.communityId}
              onChange={(e) => setFormData((prev) => ({ ...prev, communityId: e.target.value }))}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white ${
                errors.communityId ? 'border-red-300' : 'border-gray-300'
              }`}
            >
              <option value="">Select a community</option>
              {MOCK_COMMUNITIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            {errors.communityId && <p className="mt-1 text-xs text-red-500">{errors.communityId}</p>}
          </div>

          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              id="title"
              type="text"
              value={formData.title}
              onChange={(e) => setFormData((prev) => ({ ...prev, title: e.target.value }))}
              placeholder="Enter a descriptive title..."
              maxLength={200}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none ${
                errors.title ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            <div className="flex justify-between mt-1">
              {errors.title ? (
                <p className="text-xs text-red-500">{errors.title}</p>
              ) : (
                <span />
              )}
              <p className="text-xs text-gray-400">{formData.title.length}/200</p>
            </div>
          </div>

          {/* Content */}
          <div>
            <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-1">
              Content <span className="text-red-500">*</span>
            </label>
            <textarea
              id="content"
              value={formData.content}
              onChange={(e) => setFormData((prev) => ({ ...prev, content: e.target.value }))}
              placeholder="Write your post content..."
              rows={6}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-y ${
                errors.content ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.content && <p className="mt-1 text-xs text-red-500">{errors.content}</p>}
          </div>

          {/* Tags */}
          <div>
            <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-1">
              Tags <span className="text-gray-400 font-normal">(up to 5)</span>
            </label>
            <div className="flex gap-2">
              <input
                id="tags"
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagKeyDown}
                placeholder="Type a tag and press Enter..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              />
              <button
                type="button"
                onClick={addTag}
                disabled={!tagInput.trim() || formData.tags.length >= 5}
                className="px-3 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Add
              </button>
            </div>
            {formData.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {formData.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700"
                  >
                    #{tag}
                    <button
                      type="button"
                      onClick={() => removeTag(tag)}
                      className="hover:text-indigo-900 transition-colors"
                      aria-label={`Remove tag ${tag}`}
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors"
            >
              Publish Post
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Main Page Component ─────────────────────────────────────────────────────

export default function PostsPage() {
  const [posts, setPosts] = useState<Post[]>(MOCK_POSTS);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCommunity, setSelectedCommunity] = useState('all');
  const [sortBy, setSortBy] = useState<SortOption>('latest');
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  const POSTS_PER_PAGE = 5;

  // Filter and sort posts
  const filteredPosts = useMemo(() => {
    let result = [...posts];

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (post) =>
          post.title.toLowerCase().includes(query) ||
          post.content.toLowerCase().includes(query) ||
          post.author.name.toLowerCase().includes(query) ||
          post.tags.some((tag) => tag.toLowerCase().includes(query))
      );
    }

    // Community filter
    if (selectedCommunity !== 'all') {
      result = result.filter((post) => post.community.id === selectedCommunity);
    }

    // Time filter
    result = result.filter((post) => isWithinTimeFilter(post.createdAt, timeFilter));

    // Sort
    switch (sortBy) {
      case 'latest':
        result.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
        break;
      case 'oldest':
        result.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
        break;
      case 'popular':
        result.sort((a, b) => b.likes - a.likes);
        break;
      case 'most-commented':
        result.sort((a, b) => b.comments - a.comments);
        break;
    }

    // Pinned posts always first
    result.sort((a, b) => (b.isPinned ? 1 : 0) - (a.isPinned ? 1 : 0));

    return result;
  }, [posts, searchQuery, selectedCommunity, sortBy, timeFilter]);

  // Pagination
  const paginationMeta: PaginationMeta = useMemo(() => {
    const total = filteredPosts.length;
    const totalPages = Math.ceil(total / POSTS_PER_PAGE);
    return {
      page: currentPage,
      limit: POSTS_PER_PAGE,
      total,
      totalPages,
    };
  }, [filteredPosts, currentPage]);

  const paginatedPosts = useMemo(() => {
    const start = (currentPage - 1) * POSTS_PER_PAGE;
    return filteredPosts.slice(start, start + POSTS_PER_PAGE);
  }, [filteredPosts, currentPage]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedCommunity, sortBy, timeFilter]);

  // Handlers
  const handleLike = useCallback((postId: string) => {
    setPosts((prev) =>
      prev.map((post) =>
        post.id === postId
          ? {
              ...post,
              isLiked: !post.isLiked,
              likes: post.isLiked ? post.likes - 1 : post.likes + 1,
            }
          : post
      )
    );
    // Also update selected post if it's the one being liked
    setSelectedPost((prev) =>
      prev && prev.id === postId
        ? {
            ...prev,
            isLiked: !prev.isLiked,
            likes: prev.isLiked ? prev.likes - 1 : prev.likes + 1,
          }
        : prev
    );
  }, []);

  const handleCreatePost = useCallback(
    (data: CreatePostFormData) => {
      const community = MOCK_COMMUNITIES.find((c) => c.id === data.communityId);
      const newPost: Post = {
        id: `p-${Date.now()}`,
        title: data.title,
        content: data.content,
        author: { id: 'u-you', name: 'You', avatar: '/avatars/you.png' },
        community: community || { id: 'c1', name: 'General' },
        tags: data.tags,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        likes: 0,
        comments: 0,
        isLiked: false,
        isPinned: false,
      };
      setPosts((prev) => [newPost, ...prev]);
      setShowCreateForm(false);
    },
    []
  );

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Posts</h1>
          <p className="mt-1 text-sm text-gray-500">
            Discover and discuss topics across all communities
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Search & Filter Bar */}
        <SearchFilterBar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selectedCommunity={selectedCommunity}
          onCommunityChange={setSelectedCommunity}
          sortBy={sortBy}
          onSortChange={setSortBy}
          timeFilter={timeFilter}
          onTimeFilterChange={setTimeFilter}
          onCreatePost={() => setShowCreateForm(true)}
        />

        {/* Results count */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-gray-500">
            {filteredPosts.length} {filteredPosts.length === 1 ? 'post' : 'posts'} found
          </p>
        </div>

        {/* Post feed */}
        {paginatedPosts.length > 0 ? (
          <div className="space-y-4">
            {paginatedPosts.map((post) => (
              <PostCard key={post.id} post={post} onPostClick={setSelectedPost} onLike={handleLike} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <svg
              className="mx-auto w-12 h-12 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
              />
            </svg>
            <h3 className="mt-4 text-sm font-medium text-gray-900">No posts found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search or filter criteria
            </p>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedCommunity('all');
                setSortBy('latest');
                setTimeFilter('all');
              }}
              className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
            >
              Clear all filters
            </button>
          </div>
        )}

        {/* Pagination */}
        <Pagination meta={paginationMeta} onPageChange={handlePageChange} />
      </div>

      {/* Post Detail Modal */}
      <PostDetailModal post={selectedPost} onClose={() => setSelectedPost(null)} onLike={handleLike} />

      {/* Create Post Form */}
      {showCreateForm && (
        <CreatePostForm onClose={() => setShowCreateForm(false)} onSubmit={handleCreatePost} />
      )}
    </div>
  );
}
