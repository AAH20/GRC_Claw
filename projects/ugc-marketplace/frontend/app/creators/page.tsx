'use client';

import React, { useState, useMemo, useCallback } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Creator {
  id: string;
  name: string;
  username: string;
  avatar: string;
  bio: string;
  category: string;
  followers: number;
  engagement: number;
  verified: boolean;
  email: string;
  joinedDate: string;
  totalPosts: number;
  avgLikes: number;
}

interface CreatorFormData {
  name: string;
  username: string;
  email: string;
  bio: string;
  category: string;
}

type SortOption = 'followers' | 'engagement' | 'name' | 'joinedDate';

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_CREATORS: Creator[] = [
  {
    id: '1',
    name: 'Sarah Chen',
    username: '@sarahchen',
    avatar: 'SC',
    bio: 'Lifestyle & travel content creator based in NYC. Sharing authentic moments and hidden gems.',
    category: 'Lifestyle',
    followers: 125000,
    engagement: 4.8,
    verified: true,
    email: 'sarah@example.com',
    joinedDate: '2024-01-15',
    totalPosts: 342,
    avgLikes: 6000,
  },
  {
    id: '2',
    name: 'Marcus Johnson',
    username: '@marcusj',
    avatar: 'MJ',
    bio: 'Fitness coach and wellness advocate. Helping you build sustainable healthy habits.',
    category: 'Fitness',
    followers: 89000,
    engagement: 5.2,
    verified: true,
    email: 'marcus@example.com',
    joinedDate: '2024-02-20',
    totalPosts: 218,
    avgLikes: 4500,
  },
  {
    id: '3',
    name: 'Emily Rodriguez',
    username: '@emilyr',
    avatar: 'ER',
    bio: 'Food blogger and recipe developer. Making gourmet cooking accessible to everyone.',
    category: 'Food',
    followers: 67000,
    engagement: 3.9,
    verified: false,
    email: 'emily@example.com',
    joinedDate: '2024-03-10',
    totalPosts: 156,
    avgLikes: 2600,
  },
  {
    id: '4',
    name: 'David Kim',
    username: '@davidkim',
    avatar: 'DK',
    bio: 'Tech reviewer and gadget enthusiast. Unboxing the future, one device at a time.',
    category: 'Technology',
    followers: 234000,
    engagement: 6.1,
    verified: true,
    email: 'david@example.com',
    joinedDate: '2023-11-05',
    totalPosts: 512,
    avgLikes: 14200,
  },
  {
    id: '5',
    name: 'Aisha Patel',
    username: '@aishap',
    avatar: 'AP',
    bio: 'Fashion influencer and sustainable style advocate. Ethical fashion for the modern woman.',
    category: 'Fashion',
    followers: 156000,
    engagement: 4.3,
    verified: true,
    email: 'aisha@example.com',
    joinedDate: '2024-01-28',
    totalPosts: 289,
    avgLikes: 6700,
  },
  {
    id: '6',
    name: 'James Wilson',
    username: '@jamesw',
    avatar: 'JW',
    bio: 'Photography and visual storytelling. Capturing life through a different lens.',
    category: 'Photography',
    followers: 45000,
    engagement: 3.5,
    verified: false,
    email: 'james@example.com',
    joinedDate: '2024-04-12',
    totalPosts: 98,
    avgLikes: 1600,
  },
  {
    id: '7',
    name: 'Luna Martinez',
    username: '@lunam',
    avatar: 'LM',
    bio: 'Beauty and makeup artist. Creating looks that empower and inspire confidence.',
    category: 'Beauty',
    followers: 198000,
    engagement: 5.7,
    verified: true,
    email: 'luna@example.com',
    joinedDate: '2023-12-01',
    totalPosts: 423,
    avgLikes: 11300,
  },
  {
    id: '8',
    name: 'Ryan O\'Brien',
    username: '@ryanob',
    avatar: 'RO',
    bio: 'Travel vlogger exploring 50+ countries. Adventure is out there — come find it with me.',
    category: 'Travel',
    followers: 312000,
    engagement: 7.2,
    verified: true,
    email: 'ryan@example.com',
    joinedDate: '2023-09-15',
    totalPosts: 678,
    avgLikes: 22500,
  },
  {
    id: '9',
    name: 'Priya Sharma',
    username: '@priyas',
    avatar: 'PS',
    bio: 'DIY and home decor enthusiast. Transforming spaces on a budget with creative ideas.',
    category: 'Home & Decor',
    followers: 78000,
    engagement: 4.1,
    verified: false,
    email: 'priya@example.com',
    joinedDate: '2024-02-08',
    totalPosts: 134,
    avgLikes: 3200,
  },
  {
    id: '10',
    name: 'Alex Turner',
    username: '@alext',
    avatar: 'AT',
    bio: 'Gaming streamer and esports commentator. Live every day on Twitch and YouTube.',
    category: 'Gaming',
    followers: 445000,
    engagement: 8.3,
    verified: true,
    email: 'alex@example.com',
    joinedDate: '2023-08-20',
    totalPosts: 1024,
    avgLikes: 37000,
  },
  {
    id: '11',
    name: 'Nina Kowalski',
    username: '@ninak',
    avatar: 'NK',
    bio: 'Yoga instructor and mindfulness coach. Finding peace in a busy world, one breath at a time.',
    category: 'Wellness',
    followers: 92000,
    engagement: 4.6,
    verified: true,
    email: 'nina@example.com',
    joinedDate: '2024-03-22',
    totalPosts: 187,
    avgLikes: 4200,
  },
  {
    id: '12',
    name: 'Omar Hassan',
    username: '@omarh',
    avatar: 'OH',
    bio: 'Automotive journalist and car reviewer. Driving the world\'s most exciting vehicles.',
    category: 'Automotive',
    followers: 167000,
    engagement: 5.4,
    verified: true,
    email: 'omar@example.com',
    joinedDate: '2024-01-05',
    totalPosts: 256,
    avgLikes: 9000,
  },
];

const CATEGORIES = [
  'All',
  'Lifestyle',
  'Fitness',
  'Food',
  'Technology',
  'Fashion',
  'Photography',
  'Beauty',
  'Travel',
  'Home & Decor',
  'Gaming',
  'Wellness',
  'Automotive',
];

const ITEMS_PER_PAGE = 6;

// ─── Utility Functions ───────────────────────────────────────────────────────

function formatNumber(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

// ─── Sub-Components ──────────────────────────────────────────────────────────

interface CreatorCardProps {
  creator: Creator;
  onSelect: (creator: Creator) => void;
}

const CreatorCard: React.FC<CreatorCardProps> = ({ creator, onSelect }) => (
  <div
    onClick={() => onSelect(creator)}
    className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-indigo-200 transition-all duration-200 cursor-pointer group"
  >
    <div className="flex items-start gap-4">
      <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shrink-0">
        {creator.avatar}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900 truncate group-hover:text-indigo-600 transition-colors">
            {creator.name}
          </h3>
          {creator.verified && (
            <svg className="w-5 h-5 text-blue-500 shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          )}
        </div>
        <p className="text-sm text-gray-500">{creator.username}</p>
        <p className="text-sm text-gray-600 mt-1 line-clamp-2">{creator.bio}</p>
      </div>
    </div>
    <div className="mt-4 flex items-center justify-between">
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700">
        {creator.category}
      </span>
      <div className="flex items-center gap-4 text-sm text-gray-500">
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          {formatNumber(creator.followers)}
        </span>
        <span className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
          {creator.engagement}%
        </span>
      </div>
    </div>
  </div>
);

interface CreatorDetailModalProps {
  creator: Creator;
  onClose: () => void;
}

const CreatorDetailModal: React.FC<CreatorDetailModalProps> = ({ creator, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-lg font-semibold text-gray-900">Creator Profile</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-2xl">
              {creator.avatar}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold text-gray-900">{creator.name}</h3>
                {creator.verified && (
                  <svg className="w-6 h-6 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <p className="text-gray-500">{creator.username}</p>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 mt-1">
                {creator.category}
              </span>
            </div>
          </div>

          <p className="text-gray-700 mb-6">{creator.bio}</p>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">{formatNumber(creator.followers)}</p>
              <p className="text-sm text-gray-500">Followers</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">{creator.engagement}%</p>
              <p className="text-sm text-gray-500">Engagement</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">{creator.totalPosts}</p>
              <p className="text-sm text-gray-500">Total Posts</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">{formatNumber(creator.avgLikes)}</p>
              <p className="text-sm text-gray-500">Avg. Likes</p>
            </div>
          </div>

          <div className="border-t border-gray-100 pt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Email</span>
              <span className="text-gray-900 font-medium">{creator.email}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Joined</span>
              <span className="text-gray-900 font-medium">{formatDate(creator.joinedDate)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

interface AddCreatorFormProps {
  onSubmit: (data: CreatorFormData) => void;
  onCancel: () => void;
}

const AddCreatorForm: React.FC<AddCreatorFormProps> = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState<CreatorFormData>({
    name: '',
    username: '',
    email: '',
    bio: '',
    category: '',
  });
  const [errors, setErrors] = useState<Partial<CreatorFormData>>({});

  const validate = useCallback((): boolean => {
    const newErrors: Partial<CreatorFormData> = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.username.trim()) newErrors.username = 'Username is required';
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }
    if (!formData.bio.trim()) newErrors.bio = 'Bio is required';
    if (!formData.category) newErrors.category = 'Category is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  const handleChange = (field: keyof CreatorFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onCancel} />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-lg font-semibold text-gray-900">Add New Creator</h2>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="Close form"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Full Name <span className="text-red-500">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow ${
                errors.name ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              placeholder="Enter full name"
            />
            {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name}</p>}
          </div>

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
              Username <span className="text-red-500">*</span>
            </label>
            <input
              id="username"
              type="text"
              value={formData.username}
              onChange={(e) => handleChange('username', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow ${
                errors.username ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              placeholder="@username"
            />
            {errors.username && <p className="mt-1 text-xs text-red-600">{errors.username}</p>}
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email <span className="text-red-500">*</span>
            </label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow ${
                errors.email ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              placeholder="creator@example.com"
            />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email}</p>}
          </div>

          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
              Category <span className="text-red-500">*</span>
            </label>
            <select
              id="category"
              value={formData.category}
              onChange={(e) => handleChange('category', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow ${
                errors.category ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
            >
              <option value="">Select a category</option>
              {CATEGORIES.filter((c) => c !== 'All').map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
            {errors.category && <p className="mt-1 text-xs text-red-600">{errors.category}</p>}
          </div>

          <div>
            <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-1">
              Bio <span className="text-red-500">*</span>
            </label>
            <textarea
              id="bio"
              value={formData.bio}
              onChange={(e) => handleChange('bio', e.target.value)}
              rows={3}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow resize-none ${
                errors.bio ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              placeholder="Tell us about this creator..."
            />
            {errors.bio && <p className="mt-1 text-xs text-red-600">{errors.bio}</p>}
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
            >
              Add Creator
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── Main Page Component ─────────────────────────────────────────────────────

export default function CreatorsPage() {
  const [creators, setCreators] = useState<Creator[]>(MOCK_CREATORS);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [sortBy, setSortBy] = useState<SortOption>('followers');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedCreator, setSelectedCreator] = useState<Creator | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  // Filter and sort creators
  const filteredCreators = useMemo(() => {
    let result = [...creators];

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (c) =>
          c.name.toLowerCase().includes(query) ||
          c.username.toLowerCase().includes(query) ||
          c.bio.toLowerCase().includes(query)
      );
    }

    // Category filter
    if (selectedCategory !== 'All') {
      result = result.filter((c) => c.category === selectedCategory);
    }

    // Sort
    result.sort((a, b) => {
      switch (sortBy) {
        case 'followers':
          return b.followers - a.followers;
        case 'engagement':
          return b.engagement - a.engagement;
        case 'name':
          return a.name.localeCompare(b.name);
        case 'joinedDate':
          return new Date(b.joinedDate).getTime() - new Date(a.joinedDate).getTime();
        default:
          return 0;
      }
    });

    return result;
  }, [creators, searchQuery, selectedCategory, sortBy]);

  // Pagination
  const totalPages = Math.ceil(filteredCreators.length / ITEMS_PER_PAGE);
  const paginatedCreators = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredCreators.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredCreators, currentPage]);

  // Reset to page 1 when filters change
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedCategory, sortBy]);

  const handleAddCreator = useCallback((formData: CreatorFormData) => {
    const newCreator: Creator = {
      id: String(Date.now()),
      name: formData.name,
      username: formData.username.startsWith('@') ? formData.username : `@${formData.username}`,
      avatar: formData.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2),
      bio: formData.bio,
      category: formData.category,
      followers: 0,
      engagement: 0,
      verified: false,
      email: formData.email,
      joinedDate: new Date().toISOString().split('T')[0],
      totalPosts: 0,
      avgLikes: 0,
    };
    setCreators((prev) => [newCreator, ...prev]);
    setShowAddForm(false);
  }, []);

  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Creators</h1>
              <p className="text-sm text-gray-500 mt-1">
                Discover and manage content creators for your campaigns
              </p>
            </div>
            <button
              onClick={() => setShowAddForm(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Creator
            </button>
          </div>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row gap-3">
            {/* Search Input */}
            <div className="relative flex-1">
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
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search creators by name, username, or bio..."
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
              />
            </div>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow bg-white"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat === 'All' ? 'All Categories' : cat}
                </option>
              ))}
            </select>

            {/* Sort */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow bg-white"
            >
              <option value="followers">Most Followers</option>
              <option value="engagement">Highest Engagement</option>
              <option value="name">Name (A-Z)</option>
              <option value="joinedDate">Newest First</option>
            </select>
          </div>
        </div>
      </div>

      {/* Creator Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {paginatedCreators.length > 0 ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {paginatedCreators.map((creator) => (
                <CreatorCard key={creator.id} creator={creator} onSelect={setSelectedCreator} />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 flex items-center justify-center gap-2">
                <button
                  onClick={() => goToPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => goToPage(page)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      currentPage === page
                        ? 'bg-indigo-600 text-white'
                        : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                ))}
                <button
                  onClick={() => goToPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-16">
            <svg
              className="mx-auto w-16 h-16 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No creators found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search or filter criteria
            </p>
          </div>
        )}
      </div>

      {/* Creator Detail Modal */}
      {selectedCreator && (
        <CreatorDetailModal creator={selectedCreator} onClose={() => setSelectedCreator(null)} />
      )}

      {/* Add Creator Form Modal */}
      {showAddForm && (
        <AddCreatorForm onSubmit={handleAddCreator} onCancel={() => setShowAddForm(false)} />
      )}
    </div>
  );
}
