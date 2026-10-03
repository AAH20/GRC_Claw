'use client';

import React, { useState, useMemo, useCallback, useEffect } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Community {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  category: string;
  isPrivate: boolean;
  createdAt: string;
  avatarUrl?: string;
  tags: string[];
}

interface CreateCommunityFormData {
  name: string;
  description: string;
  category: string;
  isPrivate: boolean;
  tags: string[];
}

interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}

interface FilterState {
  search: string;
  category: string;
  visibility: 'all' | 'public' | 'private';
  sortBy: 'name' | 'members' | 'recent';
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_COMMUNITIES: Community[] = [
  {
    id: '1',
    name: 'React Developers',
    description: 'A community for React developers to share knowledge, ask questions, and collaborate on projects.',
    memberCount: 12450,
    category: 'Technology',
    isPrivate: false,
    createdAt: '2024-01-15T10:30:00Z',
    tags: ['react', 'javascript', 'frontend'],
  },
  {
    id: '2',
    name: 'Design Systems',
    description: 'Exploring the art and science of design systems, component libraries, and UI consistency.',
    memberCount: 8320,
    category: 'Design',
    isPrivate: false,
    createdAt: '2024-02-20T14:00:00Z',
    tags: ['design', 'ui', 'components'],
  },
  {
    id: '3',
    name: 'AI Research Lab',
    description: 'Private group for AI researchers to discuss papers, share findings, and collaborate.',
    memberCount: 456,
    category: 'Research',
    isPrivate: true,
    createdAt: '2024-03-10T09:15:00Z',
    tags: ['ai', 'ml', 'research'],
  },
  {
    id: '4',
    name: 'Startup Founders',
    description: 'Connect with fellow founders, share experiences, and navigate the startup journey together.',
    memberCount: 3210,
    category: 'Business',
    isPrivate: false,
    createdAt: '2024-01-05T08:00:00Z',
    tags: ['startup', 'entrepreneurship', 'business'],
  },
  {
    id: '5',
    name: 'Open Source Contributors',
    description: 'A welcoming space for open source contributors of all skill levels.',
    memberCount: 15670,
    category: 'Technology',
    isPrivate: false,
    createdAt: '2023-12-01T12:00:00Z',
    tags: ['open-source', 'github', 'collaboration'],
  },
  {
    id: '6',
    name: 'Product Managers',
    description: 'Discuss product strategy, roadmaps, user research, and cross-functional collaboration.',
    memberCount: 5890,
    category: 'Business',
    isPrivate: false,
    createdAt: '2024-02-01T11:30:00Z',
    tags: ['product', 'strategy', 'management'],
  },
  {
    id: '7',
    name: 'Data Science Hub',
    description: 'Everything data science: statistics, machine learning, visualization, and analytics.',
    memberCount: 9870,
    category: 'Technology',
    isPrivate: false,
    createdAt: '2024-01-20T16:45:00Z',
    tags: ['data', 'python', 'analytics'],
  },
  {
    id: '8',
    name: 'UX Research Collective',
    description: 'Private community for UX researchers to share methodologies and insights.',
    memberCount: 234,
    category: 'Research',
    isPrivate: true,
    createdAt: '2024-04-01T10:00:00Z',
    tags: ['ux', 'research', 'usability'],
  },
  {
    id: '9',
    name: 'DevOps & SRE',
    description: 'Infrastructure, CI/CD, monitoring, and site reliability engineering discussions.',
    memberCount: 6540,
    category: 'Technology',
    isPrivate: false,
    createdAt: '2024-03-15T13:20:00Z',
    tags: ['devops', 'sre', 'infrastructure'],
  },
  {
    id: '10',
    name: 'Content Creators',
    description: 'Tips, strategies, and support for content creators across all platforms.',
    memberCount: 11200,
    category: 'Creative',
    isPrivate: false,
    createdAt: '2024-02-10T09:00:00Z',
    tags: ['content', 'writing', 'social-media'],
  },
  {
    id: '11',
    name: 'Cybersecurity Forum',
    description: 'Discuss security best practices, threat intelligence, and vulnerability research.',
    memberCount: 4320,
    category: 'Technology',
    isPrivate: false,
    createdAt: '2024-01-25T15:30:00Z',
    tags: ['security', 'privacy', 'hacking'],
  },
  {
    id: '12',
    name: 'Indie Hackers',
    description: 'For bootstrapped founders building profitable products and businesses.',
    memberCount: 7890,
    category: 'Business',
    isPrivate: false,
    createdAt: '2024-03-01T08:45:00Z',
    tags: ['indie', 'bootstrapping', 'saas'],
  },
];

const CATEGORIES = ['All', 'Technology', 'Design', 'Business', 'Research', 'Creative'];

// ─── Utility Functions ───────────────────────────────────────────────────────

function formatMemberCount(count: number): string {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`;
  }
  return count.toString();
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

// ─── Components ──────────────────────────────────────────────────────────────

interface CommunityCardProps {
  community: Community;
  onSelect: (community: Community) => void;
}

const CommunityCard: React.FC<CommunityCardProps> = ({ community, onSelect }) => {
  return (
    <div
      onClick={() => onSelect(community)}
      className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-lg hover:border-blue-300 transition-all duration-200 cursor-pointer group"
    >
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shrink-0">
          {community.name.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors truncate">
              {community.name}
            </h3>
            {community.isPrivate && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 shrink-0">
                🔒 Private
              </span>
            )}
          </div>
          <p className="text-sm text-gray-600 line-clamp-2 mb-3">
            {community.description}
          </p>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              {formatMemberCount(community.memberCount)} members
            </span>
            <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
              {community.category}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-3">
            {community.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 rounded-full text-xs bg-blue-50 text-blue-700"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

interface PaginationProps {
  pagination: PaginationState;
  onPageChange: (page: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({ pagination, onPageChange }) => {
  const totalPages = Math.ceil(pagination.total / pagination.pageSize);
  const { page } = pagination;

  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (page > 3) pages.push('...');
      for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
        pages.push(i);
      }
      if (page < totalPages - 2) pages.push('...');
      pages.push(totalPages);
    }
    return pages;
  };

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-2 mt-8">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
        className="px-3 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        ← Prev
      </button>
      {getPageNumbers().map((p, idx) =>
        p === '...' ? (
          <span key={`ellipsis-${idx}`} className="px-2 text-gray-400">
            …
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p as number)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              p === page
                ? 'bg-blue-600 text-white'
                : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            {p}
          </button>
        )
      )}
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages}
        className="px-3 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Next →
      </button>
    </div>
  );
};

interface CommunityDetailModalProps {
  community: Community | null;
  onClose: () => void;
}

const CommunityDetailModal: React.FC<CommunityDetailModalProps> = ({ community, onClose }) => {
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (community) {
      document.addEventListener('keydown', handleEsc);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = '';
    };
  }, [community, onClose]);

  if (!community) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="relative h-32 bg-gradient-to-r from-blue-500 to-purple-600 rounded-t-2xl">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center text-white transition-colors"
          >
            ✕
          </button>
        </div>
        <div className="px-6 pb-6">
          <div className="flex items-end gap-4 -mt-10 mb-4">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-2xl border-4 border-white shadow-lg">
              {community.name.charAt(0)}
            </div>
            <div className="pb-1">
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-gray-900">{community.name}</h2>
                {community.isPrivate && (
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                    🔒 Private
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500">{community.category}</p>
            </div>
          </div>

          <p className="text-gray-700 mb-4">{community.description}</p>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-gray-900">{formatMemberCount(community.memberCount)}</p>
              <p className="text-xs text-gray-500">Members</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-gray-900">{formatDate(community.createdAt)}</p>
              <p className="text-xs text-gray-500">Created</p>
            </div>
          </div>

          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Tags</h4>
            <div className="flex flex-wrap gap-2">
              {community.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 rounded-full text-sm bg-blue-50 text-blue-700"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">
              Join Community
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

interface CreateCommunityModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateCommunityFormData) => void;
}

const CreateCommunityModal: React.FC<CreateCommunityModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState<CreateCommunityFormData>({
    name: '',
    description: '',
    category: 'Technology',
    isPrivate: false,
    tags: [],
  });
  const [tagInput, setTagInput] = useState('');
  const [errors, setErrors] = useState<Partial<Record<keyof CreateCommunityFormData, string>>>({});

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof CreateCommunityFormData, string>> = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (formData.name.length > 50) newErrors.name = 'Name must be 50 characters or less';
    if (!formData.description.trim()) newErrors.description = 'Description is required';
    if (formData.description.length > 500) newErrors.description = 'Description must be 500 characters or less';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
      setFormData({ name: '', description: '', category: 'Technology', isPrivate: false, tags: [] });
      setTagInput('');
      setErrors({});
      onClose();
    }
  };

  const addTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !formData.tags.includes(tag) && formData.tags.length < 5) {
      setFormData((prev) => ({ ...prev, tags: [...prev.tags, tag] }));
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData((prev) => ({ ...prev, tags: prev.tags.filter((t) => t !== tagToRemove) }));
  };

  const handleTagKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  };

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Create Community</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-500 transition-colors"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          <div>
            <label htmlFor="community-name" className="block text-sm font-medium text-gray-700 mb-1">
              Community Name <span className="text-red-500">*</span>
            </label>
            <input
              id="community-name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="Enter community name"
              className={`w-full px-3 py-2 rounded-lg border ${errors.name ? 'border-red-500' : 'border-gray-300'} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors`}
              maxLength={50}
            />
            {errors.name && <p className="mt-1 text-xs text-red-500">{errors.name}</p>}
            <p className="mt-1 text-xs text-gray-400">{formData.name.length}/50</p>
          </div>

          <div>
            <label htmlFor="community-desc" className="block text-sm font-medium text-gray-700 mb-1">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              id="community-desc"
              value={formData.description}
              onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
              placeholder="Describe your community"
              rows={3}
              className={`w-full px-3 py-2 rounded-lg border ${errors.description ? 'border-red-500' : 'border-gray-300'} focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors resize-none`}
              maxLength={500}
            />
            {errors.description && <p className="mt-1 text-xs text-red-500">{errors.description}</p>}
            <p className="mt-1 text-xs text-gray-400">{formData.description.length}/500</p>
          </div>

          <div>
            <label htmlFor="community-category" className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              id="community-category"
              value={formData.category}
              onChange={(e) => setFormData((prev) => ({ ...prev, category: e.target.value }))}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors bg-white"
            >
              {CATEGORIES.filter((c) => c !== 'All').map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tags (up to 5)</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagKeyDown}
                placeholder="Add a tag"
                className="flex-1 px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
              />
              <button
                type="button"
                onClick={addTag}
                className="px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              >
                Add
              </button>
            </div>
            {formData.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm bg-blue-50 text-blue-700"
                  >
                    #{tag}
                    <button
                      type="button"
                      onClick={() => removeTag(tag)}
                      className="hover:text-blue-900 transition-colors"
                    >
                      ✕
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="community-private"
              checked={formData.isPrivate}
              onChange={(e) => setFormData((prev) => ({ ...prev, isPrivate: e.target.checked }))}
              className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="community-private" className="text-sm text-gray-700">
              Make this community private
            </label>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Create Community
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── Main Page Component ─────────────────────────────────────────────────────

export default function CommunitiesPage() {
  const [communities, setCommunities] = useState<Community[]>(MOCK_COMMUNITIES);
  const [selectedCommunity, setSelectedCommunity] = useState<Community | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    category: 'All',
    visibility: 'all',
    sortBy: 'members',
  });
  const [pagination, setPagination] = useState<PaginationState>({
    page: 1,
    pageSize: 6,
    total: MOCK_COMMUNITIES.length,
  });

  const filteredCommunities = useMemo(() => {
    let result = [...communities];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(
        (c) =>
          c.name.toLowerCase().includes(searchLower) ||
          c.description.toLowerCase().includes(searchLower) ||
          c.tags.some((t) => t.includes(searchLower))
      );
    }

    // Category filter
    if (filters.category !== 'All') {
      result = result.filter((c) => c.category === filters.category);
    }

    // Visibility filter
    if (filters.visibility === 'public') {
      result = result.filter((c) => !c.isPrivate);
    } else if (filters.visibility === 'private') {
      result = result.filter((c) => c.isPrivate);
    }

    // Sort
    switch (filters.sortBy) {
      case 'name':
        result.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case 'members':
        result.sort((a, b) => b.memberCount - a.memberCount);
        break;
      case 'recent':
        result.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
        break;
    }

    return result;
  }, [communities, filters]);

  const paginatedCommunities = useMemo(() => {
    const start = (pagination.page - 1) * pagination.pageSize;
    return filteredCommunities.slice(start, start + pagination.pageSize);
  }, [filteredCommunities, pagination.page, pagination.pageSize]);

  useEffect(() => {
    setPagination((prev) => ({
      ...prev,
      total: filteredCommunities.length,
      page: 1,
    }));
  }, [filteredCommunities.length]);

  const handlePageChange = useCallback((page: number) => {
    setPagination((prev) => ({ ...prev, page }));
  }, []);

  const handleFilterChange = useCallback(<K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleCreateCommunity = useCallback((data: CreateCommunityFormData) => {
    const newCommunity: Community = {
      id: Date.now().toString(),
      name: data.name,
      description: data.description,
      category: data.category,
      isPrivate: data.isPrivate,
      memberCount: 1,
      createdAt: new Date().toISOString(),
      tags: data.tags,
    };
    setCommunities((prev) => [newCommunity, ...prev]);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Communities</h1>
              <p className="text-sm text-gray-500 mt-0.5">
                Discover and join communities that match your interests
              </p>
            </div>
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create Community
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Search and Filter Bar */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search Input */}
            <div className="flex-1 relative">
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                type="text"
                placeholder="Search communities by name, description, or tag..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
              />
            </div>

            {/* Category Filter */}
            <select
              value={filters.category}
              onChange={(e) => handleFilterChange('category', e.target.value)}
              className="px-3 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors bg-white min-w-[140px]"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat === 'All' ? 'All Categories' : cat}
                </option>
              ))}
            </select>

            {/* Visibility Filter */}
            <select
              value={filters.visibility}
              onChange={(e) => handleFilterChange('visibility', e.target.value as FilterState['visibility'])}
              className="px-3 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors bg-white min-w-[130px]"
            >
              <option value="all">All Visibility</option>
              <option value="public">Public</option>
              <option value="private">Private</option>
            </select>

            {/* Sort */}
            <select
              value={filters.sortBy}
              onChange={(e) => handleFilterChange('sortBy', e.target.value as FilterState['sortBy'])}
              className="px-3 py-2.5 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors bg-white min-w-[140px]"
            >
              <option value="members">Most Members</option>
              <option value="name">Name A-Z</option>
              <option value="recent">Most Recent</option>
            </select>
          </div>

          {/* Active Filters Summary */}
          <div className="flex items-center gap-2 mt-3 text-sm text-gray-500">
            <span>
              Showing {paginatedCommunities.length} of {filteredCommunities.length} communities
            </span>
            {filters.search && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">
                Search: &quot;{filters.search}&quot;
                <button
                  onClick={() => handleFilterChange('search', '')}
                  className="hover:text-blue-900"
                >
                  ✕
                </button>
              </span>
            )}
          </div>
        </div>

        {/* Community List */}
        {paginatedCommunities.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {paginatedCommunities.map((community) => (
              <CommunityCard
                key={community.id}
                community={community}
                onSelect={setSelectedCommunity}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <svg
              className="w-16 h-16 mx-auto text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No communities found</h3>
            <p className="text-gray-500">Try adjusting your search or filter criteria</p>
          </div>
        )}

        {/* Pagination */}
        <Pagination pagination={pagination} onPageChange={handlePageChange} />
      </main>

      {/* Community Detail Modal */}
      <CommunityDetailModal
        community={selectedCommunity}
        onClose={() => setSelectedCommunity(null)}
      />

      {/* Create Community Modal */}
      <CreateCommunityModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateCommunity}
      />
    </div>
  );
}
