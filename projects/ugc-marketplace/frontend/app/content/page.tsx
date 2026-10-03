'use client';

import React, { useState, useCallback, useMemo } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface ContentItem {
  id: string;
  title: string;
  description: string;
  type: 'image' | 'video' | 'audio' | 'text';
  thumbnailUrl: string;
  author: string;
  createdAt: string;
  likes: number;
  views: number;
  tags: string[];
  status: 'published' | 'draft' | 'pending';
}

interface UploadFormData {
  title: string;
  description: string;
  type: 'image' | 'video' | 'audio' | 'text';
  tags: string;
  file: File | null;
}

interface FilterState {
  search: string;
  type: 'all' | 'image' | 'video' | 'audio' | 'text';
  status: 'all' | 'published' | 'draft' | 'pending';
  sortBy: 'newest' | 'oldest' | 'popular' | 'mostViewed';
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_CONTENT: ContentItem[] = [
  {
    id: '1',
    title: 'Summer Campaign Hero Shot',
    description: 'High-energy summer campaign visual featuring vibrant colors and dynamic composition.',
    type: 'image',
    thumbnailUrl: 'https://picsum.photos/seed/1/400/300',
    author: 'Sarah Chen',
    createdAt: '2026-09-15T10:30:00Z',
    likes: 234,
    views: 1520,
    tags: ['summer', 'campaign', 'hero'],
    status: 'published',
  },
  {
    id: '2',
    title: 'Product Launch Teaser',
    description: 'Short teaser video for the upcoming product launch event.',
    type: 'video',
    thumbnailUrl: 'https://picsum.photos/seed/2/400/300',
    author: 'Mike Johnson',
    createdAt: '2026-09-14T08:00:00Z',
    likes: 189,
    views: 2340,
    tags: ['product', 'launch', 'teaser'],
    status: 'published',
  },
  {
    id: '3',
    title: 'Brand Story Podcast Ep.12',
    description: 'Behind-the-scenes look at our brand journey and future vision.',
    type: 'audio',
    thumbnailUrl: 'https://picsum.photos/seed/3/400/300',
    author: 'Emma Wilson',
    createdAt: '2026-09-13T14:20:00Z',
    likes: 98,
    views: 890,
    tags: ['podcast', 'brand', 'story'],
    status: 'published',
  },
  {
    id: '4',
    title: 'User Testimonial - Acme Corp',
    description: 'Written testimonial from Acme Corp about their experience with our platform.',
    type: 'text',
    thumbnailUrl: 'https://picsum.photos/seed/4/400/300',
    author: 'David Park',
    createdAt: '2026-09-12T16:45:00Z',
    likes: 67,
    views: 456,
    tags: ['testimonial', 'enterprise'],
    status: 'published',
  },
  {
    id: '5',
    title: 'Autumn Collection Moodboard',
    description: 'Curated moodboard for the autumn collection featuring warm tones and textures.',
    type: 'image',
    thumbnailUrl: 'https://picsum.photos/seed/5/400/300',
    author: 'Lisa Martinez',
    createdAt: '2026-09-11T09:15:00Z',
    likes: 312,
    views: 1890,
    tags: ['autumn', 'moodboard', 'collection'],
    status: 'published',
  },
  {
    id: '6',
    title: 'Tutorial: Getting Started',
    description: 'Step-by-step video tutorial for new users on platform basics.',
    type: 'video',
    thumbnailUrl: 'https://picsum.photos/seed/6/400/300',
    author: 'James Lee',
    createdAt: '2026-09-10T11:00:00Z',
    likes: 445,
    views: 5670,
    tags: ['tutorial', 'onboarding'],
    status: 'published',
  },
  {
    id: '7',
    title: 'Customer Success Story',
    description: 'Detailed case study on how customer X achieved 3x growth.',
    type: 'text',
    thumbnailUrl: 'https://picsum.photos/seed/7/400/300',
    author: 'Anna Kim',
    createdAt: '2026-09-09T13:30:00Z',
    likes: 156,
    views: 1230,
    tags: ['case-study', 'growth'],
    status: 'draft',
  },
  {
    id: '8',
    title: 'Holiday Promo Audio Ad',
    description: 'Radio-ready audio advertisement for the holiday promotion.',
    type: 'audio',
    thumbnailUrl: 'https://picsum.photos/seed/8/400/300',
    author: 'Tom Brown',
    createdAt: '2026-09-08T07:45:00Z',
    likes: 78,
    views: 567,
    tags: ['holiday', 'promo', 'audio'],
    status: 'pending',
  },
  {
    id: '9',
    title: 'Influencer Collab - Beach Day',
    description: 'Lifestyle content from influencer partnership at Malibu beach.',
    type: 'image',
    thumbnailUrl: 'https://picsum.photos/seed/9/400/300',
    author: 'Nina Patel',
    createdAt: '2026-09-07T15:20:00Z',
    likes: 567,
    views: 8900,
    tags: ['influencer', 'lifestyle', 'collab'],
    status: 'published',
  },
  {
    id: '10',
    title: 'Webinar Recording: Q3 Review',
    description: 'Full recording of the quarterly business review webinar.',
    type: 'video',
    thumbnailUrl: 'https://picsum.photos/seed/10/400/300',
    author: 'Robert Taylor',
    createdAt: '2026-09-06T10:00:00Z',
    likes: 234,
    views: 3450,
    tags: ['webinar', 'quarterly', 'review'],
    status: 'published',
  },
  {
    id: '11',
    title: 'Blog Post: Industry Trends 2026',
    description: 'In-depth analysis of emerging industry trends and predictions.',
    type: 'text',
    thumbnailUrl: 'https://picsum.photos/seed/11/400/300',
    author: 'Karen White',
    createdAt: '2026-09-05T12:00:00Z',
    likes: 189,
    views: 2340,
    tags: ['blog', 'trends', 'analysis'],
    status: 'published',
  },
  {
    id: '12',
    title: 'Unboxing Video - Premium Tier',
    description: 'Satisfying unboxing experience of our premium subscription box.',
    type: 'video',
    thumbnailUrl: 'https://picsum.photos/seed/12/400/300',
    author: 'Chris Evans',
    createdAt: '2026-09-04T09:30:00Z',
    likes: 678,
    views: 12000,
    tags: ['unboxing', 'premium', 'subscription'],
    status: 'published',
  },
];

const ITEMS_PER_PAGE = 6;

// ─── Utility Functions ───────────────────────────────────────────────────────

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatNumber(num: number): string {
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}k`;
  }
  return num.toString();
}

// ─── Components ──────────────────────────────────────────────────────────────

const TypeBadge: React.FC<{ type: ContentItem['type'] }> = ({ type }) => {
  const colors: Record<ContentItem['type'], string> = {
    image: 'bg-blue-100 text-blue-800',
    video: 'bg-purple-100 text-purple-800',
    audio: 'bg-green-100 text-green-800',
    text: 'bg-orange-100 text-orange-800',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[type]}`}>
      {type.charAt(0).toUpperCase() + type.slice(1)}
    </span>
  );
};

const StatusBadge: React.FC<{ status: ContentItem['status'] }> = ({ status }) => {
  const colors: Record<ContentItem['status'], string> = {
    published: 'bg-emerald-100 text-emerald-800',
    draft: 'bg-gray-100 text-gray-800',
    pending: 'bg-yellow-100 text-yellow-800',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

const ContentCard: React.FC<{
  item: ContentItem;
  onSelect: (item: ContentItem) => void;
}> = ({ item, onSelect }) => {
  return (
    <div
      className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onSelect(item)}
    >
      <div className="relative aspect-video bg-gray-100">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={item.thumbnailUrl}
          alt={item.title}
          className="w-full h-full object-cover"
        />
        <div className="absolute top-2 left-2">
          <TypeBadge type={item.type} />
        </div>
      </div>
      <div className="p-4">
        <h3 className="text-sm font-semibold text-gray-900 line-clamp-1">{item.title}</h3>
        <p className="mt-1 text-xs text-gray-500 line-clamp-2">{item.description}</p>
        <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
          <span>{item.author}</span>
          <span>{formatDate(item.createdAt)}</span>
        </div>
        <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" />
            </svg>
            {formatNumber(item.likes)}
          </span>
          <span className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
              <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
            </svg>
            {formatNumber(item.views)}
          </span>
        </div>
      </div>
    </div>
  );
};

const Pagination: React.FC<{
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}> = ({ currentPage, totalPages, onPageChange }) => {
  const pages = useMemo(() => {
    const items: (number | string)[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) items.push(i);
    } else {
      items.push(1);
      if (currentPage > 3) items.push('...');
      for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
        items.push(i);
      }
      if (currentPage < totalPages - 2) items.push('...');
      items.push(totalPages);
    }
    return items;
  }, [currentPage, totalPages]);

  return (
    <nav className="flex items-center justify-center gap-1 mt-8" aria-label="Pagination">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-l-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Previous
      </button>
      {pages.map((page, idx) =>
        typeof page === 'string' ? (
          <span key={`ellipsis-${idx}`} className="px-3 py-2 text-sm text-gray-500">
            ...
          </span>
        ) : (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`px-3 py-2 text-sm font-medium border ${
              page === currentPage
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'text-gray-700 bg-white border-gray-300 hover:bg-gray-50'
            }`}
          >
            {page}
          </button>
        )
      )}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-r-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </nav>
  );
};

const ContentDetailModal: React.FC<{
  item: ContentItem | null;
  onClose: () => void;
}> = ({ item, onClose }) => {
  if (!item) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Content Details</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-6">
          <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden mb-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={item.thumbnailUrl}
              alt={item.title}
              className="w-full h-full object-cover"
            />
          </div>
          <div className="flex items-center gap-2 mb-3">
            <TypeBadge type={item.type} />
            <StatusBadge status={item.status} />
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">{item.title}</h3>
          <p className="text-gray-600 mb-4">{item.description}</p>
          <div className="grid grid-cols-2 gap-4 mb-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Author</p>
              <p className="text-sm font-medium text-gray-900">{item.author}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Created</p>
              <p className="text-sm font-medium text-gray-900">{formatDate(item.createdAt)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Likes</p>
              <p className="text-sm font-medium text-gray-900">{formatNumber(item.likes)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Views</p>
              <p className="text-sm font-medium text-gray-900">{formatNumber(item.views)}</p>
            </div>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Tags</p>
            <div className="flex flex-wrap gap-2">
              {item.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2.5 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Close
          </button>
          <button className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700">
            Download
          </button>
        </div>
      </div>
    </div>
  );
};

const UploadContentModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: UploadFormData) => void;
}> = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState<UploadFormData>({
    title: '',
    description: '',
    type: 'image',
    tags: '',
    file: null,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
    setFormData({ title: '', description: '', type: 'image', tags: '', file: null });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Upload Content</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label htmlFor="upload-title" className="block text-sm font-medium text-gray-700 mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              id="upload-title"
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              placeholder="Enter content title"
            />
          </div>
          <div>
            <label htmlFor="upload-description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="upload-description"
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
              placeholder="Describe your content"
            />
          </div>
          <div>
            <label htmlFor="upload-type" className="block text-sm font-medium text-gray-700 mb-1">
              Content Type <span className="text-red-500">*</span>
            </label>
            <select
              id="upload-type"
              required
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as UploadFormData['type'] })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            >
              <option value="image">Image</option>
              <option value="video">Video</option>
              <option value="audio">Audio</option>
              <option value="text">Text</option>
            </select>
          </div>
          <div>
            <label htmlFor="upload-tags" className="block text-sm font-medium text-gray-700 mb-1">
              Tags
            </label>
            <input
              id="upload-tags"
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              placeholder="Comma-separated tags"
            />
          </div>
          <div>
            <label htmlFor="upload-file" className="block text-sm font-medium text-gray-700 mb-1">
              File <span className="text-red-500">*</span>
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors">
              <input
                id="upload-file"
                type="file"
                required
                onChange={(e) => setFormData({ ...formData, file: e.target.files?.[0] || null })}
                className="hidden"
              />
              <label htmlFor="upload-file" className="cursor-pointer">
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <p className="mt-2 text-sm text-gray-600">
                  {formData.file ? formData.file.name : 'Click to upload or drag and drop'}
                </p>
                <p className="mt-1 text-xs text-gray-500">PNG, JPG, GIF, MP4, MP3 up to 50MB</p>
              </label>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
            >
              Upload
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── Main Page Component ─────────────────────────────────────────────────────

export default function ContentPage() {
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    type: 'all',
    status: 'all',
    sortBy: 'newest',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const filteredContent = useMemo(() => {
    let result = [...MOCK_CONTENT];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(
        (item) =>
          item.title.toLowerCase().includes(searchLower) ||
          item.description.toLowerCase().includes(searchLower) ||
          item.author.toLowerCase().includes(searchLower) ||
          item.tags.some((tag) => tag.toLowerCase().includes(searchLower))
      );
    }

    // Type filter
    if (filters.type !== 'all') {
      result = result.filter((item) => item.type === filters.type);
    }

    // Status filter
    if (filters.status !== 'all') {
      result = result.filter((item) => item.status === filters.status);
    }

    // Sort
    switch (filters.sortBy) {
      case 'newest':
        result.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
        break;
      case 'oldest':
        result.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
        break;
      case 'popular':
        result.sort((a, b) => b.likes - a.likes);
        break;
      case 'mostViewed':
        result.sort((a, b) => b.views - a.views);
        break;
    }

    return result;
  }, [filters]);

  const totalPages = Math.ceil(filteredContent.length / ITEMS_PER_PAGE);
  const paginatedContent = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredContent.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredContent, currentPage]);

  const handleFilterChange = useCallback(<K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  }, []);

  const handleUpload = useCallback((data: UploadFormData) => {
    console.log('Upload submitted:', data);
    setIsUploadOpen(false);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Content Library</h1>
              <p className="mt-1 text-sm text-gray-500">
                Browse, search, and manage all your content assets
              </p>
            </div>
            <button
              onClick={() => setIsUploadOpen(true)}
              className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Upload Content
            </button>
          </div>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search Input */}
            <div className="flex-1">
              <div className="relative">
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search by title, author, or tag..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
              </div>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-3">
              <select
                value={filters.type}
                onChange={(e) => handleFilterChange('type', e.target.value as FilterState['type'])}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              >
                <option value="all">All Types</option>
                <option value="image">Images</option>
                <option value="video">Videos</option>
                <option value="audio">Audio</option>
                <option value="text">Text</option>
              </select>

              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value as FilterState['status'])}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              >
                <option value="all">All Status</option>
                <option value="published">Published</option>
                <option value="draft">Draft</option>
                <option value="pending">Pending</option>
              </select>

              <select
                value={filters.sortBy}
                onChange={(e) => handleFilterChange('sortBy', e.target.value as FilterState['sortBy'])}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="popular">Most Popular</option>
                <option value="mostViewed">Most Viewed</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Content Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <p className="text-sm text-gray-600">
            Showing <span className="font-medium">{paginatedContent.length}</span> of{' '}
            <span className="font-medium">{filteredContent.length}</span> items
          </p>
        </div>

        {paginatedContent.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {paginatedContent.map((item) => (
              <ContentCard key={item.id} item={item} onSelect={setSelectedContent} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="mt-4 text-sm font-medium text-gray-900">No content found</h3>
            <p className="mt-1 text-sm text-gray-500">Try adjusting your search or filter criteria.</p>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        )}
      </div>

      {/* Modals */}
      <ContentDetailModal item={selectedContent} onClose={() => setSelectedContent(null)} />
      <UploadContentModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSubmit={handleUpload}
      />
    </div>
  );
}
