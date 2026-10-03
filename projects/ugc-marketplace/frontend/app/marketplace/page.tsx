'use client';

import React, { useState, useCallback, useMemo } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Listing {
  id: string;
  title: string;
  description: string;
  price: number;
  currency: string;
  category: string;
  tags: string[];
  seller: {
    id: string;
    name: string;
    avatar: string;
    rating: number;
    totalSales: number;
  };
  thumbnail: string;
  images: string[];
  createdAt: string;
  inStock: boolean;
  deliveryTime: string;
}

interface FilterState {
  category: string;
  priceRange: [number, number];
  sortBy: 'newest' | 'price-asc' | 'price-desc' | 'popular';
  inStockOnly: boolean;
}

interface PurchaseFormData {
  quantity: number;
  fullName: string;
  email: string;
  address: string;
  city: string;
  zipCode: string;
  cardNumber: string;
  expiryDate: string;
  cvv: string;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_LISTINGS: Listing[] = [
  {
    id: '1',
    title: 'Professional Product Photography',
    description: 'High-quality product photography for e-commerce. Includes 10 edited images with white background and lifestyle shots.',
    price: 149.99,
    currency: 'USD',
    category: 'Photography',
    tags: ['product', 'e-commerce', 'editing'],
    seller: { id: 's1', name: 'Visual Studio Pro', avatar: '/avatars/seller1.jpg', rating: 4.9, totalSales: 342 },
    thumbnail: '/listings/photo1.jpg',
    images: ['/listings/photo1.jpg', '/listings/photo2.jpg'],
    createdAt: '2026-09-15T10:00:00Z',
    inStock: true,
    deliveryTime: '3-5 business days',
  },
  {
    id: '2',
    title: 'Social Media Content Package',
    description: '30 days of curated social media content including graphics, captions, and hashtag research.',
    price: 299.0,
    currency: 'USD',
    category: 'Social Media',
    tags: ['content', 'instagram', 'marketing'],
    seller: { id: 's2', name: 'Content Kings', avatar: '/avatars/seller2.jpg', rating: 4.7, totalSales: 189 },
    thumbnail: '/listings/social1.jpg',
    images: ['/listings/social1.jpg'],
    createdAt: '2026-09-20T14:30:00Z',
    inStock: true,
    deliveryTime: '7 business days',
  },
  {
    id: '3',
    title: 'Custom Logo Design',
    description: 'Unique, memorable logo design with unlimited revisions. Includes vector files and brand guidelines.',
    price: 499.0,
    currency: 'USD',
    category: 'Design',
    tags: ['logo', 'branding', 'vector'],
    seller: { id: 's3', name: 'Pixel Perfect', avatar: '/avatars/seller3.jpg', rating: 5.0, totalSales: 567 },
    thumbnail: '/listings/logo1.jpg',
    images: ['/listings/logo1.jpg'],
    createdAt: '2026-08-28T09:00:00Z',
    inStock: true,
    deliveryTime: '5-7 business days',
  },
  {
    id: '4',
    title: 'Video Editing — 60s Promo',
    description: 'Professional video editing for promotional content. Color grading, sound design, and motion graphics included.',
    price: 199.0,
    currency: 'USD',
    category: 'Video',
    tags: ['editing', 'promo', 'motion'],
    seller: { id: 's4', name: 'Frame by Frame', avatar: '/avatars/seller4.jpg', rating: 4.8, totalSales: 234 },
    thumbnail: '/listings/video1.jpg',
    images: ['/listings/video1.jpg'],
    createdAt: '2026-09-10T16:00:00Z',
    inStock: false,
    deliveryTime: '5 business days',
  },
  {
    id: '5',
    title: 'SEO Blog Post (1500 words)',
    description: 'Well-researched, SEO-optimized blog post written by experienced content writers.',
    price: 79.0,
    currency: 'USD',
    category: 'Writing',
    tags: ['seo', 'blog', 'content'],
    seller: { id: 's5', name: 'WordSmith', avatar: '/avatars/seller5.jpg', rating: 4.6, totalSales: 412 },
    thumbnail: '/listings/blog1.jpg',
    images: ['/listings/blog1.jpg'],
    createdAt: '2026-09-25T11:00:00Z',
    inStock: true,
    deliveryTime: '2-3 business days',
  },
  {
    id: '6',
    title: 'Website UI/UX Audit',
    description: 'Comprehensive audit of your website usability with actionable recommendations.',
    price: 349.0,
    currency: 'USD',
    category: 'Design',
    tags: ['ui', 'ux', 'audit'],
    seller: { id: 's6', name: 'UX Masters', avatar: '/avatars/seller6.jpg', rating: 4.9, totalSales: 156 },
    thumbnail: '/listings/ux1.jpg',
    images: ['/listings/ux1.jpg'],
    createdAt: '2026-09-05T08:00:00Z',
    inStock: true,
    deliveryTime: '4 business days',
  },
  {
    id: '7',
    title: 'Influencer Outreach Campaign',
    description: 'Connect with 50+ micro-influencers in your niche. Includes campaign management.',
    price: 599.0,
    currency: 'USD',
    category: 'Marketing',
    tags: ['influencer', 'outreach', 'campaign'],
    seller: { id: 's7', name: 'ReachOut Media', avatar: '/avatars/seller7.jpg', rating: 4.5, totalSales: 98 },
    thumbnail: '/listings/influencer1.jpg',
    images: ['/listings/influencer1.jpg'],
    createdAt: '2026-09-18T13:00:00Z',
    inStock: true,
    deliveryTime: '10 business days',
  },
  {
    id: '8',
    title: 'Podcast Editing (per episode)',
    description: 'Full podcast editing including noise reduction, intro/outro, and show notes.',
    price: 89.0,
    currency: 'USD',
    category: 'Audio',
    tags: ['podcast', 'editing', 'audio'],
    seller: { id: 's8', name: 'SoundWave', avatar: '/avatars/seller8.jpg', rating: 4.8, totalSales: 276 },
    thumbnail: '/listings/podcast1.jpg',
    images: ['/listings/podcast1.jpg'],
    createdAt: '2026-09-22T15:00:00Z',
    inStock: true,
    deliveryTime: '3 business days',
  },
  {
    id: '9',
    title: 'Email Marketing Sequence',
    description: '5-email welcome sequence written and designed for your brand voice.',
    price: 179.0,
    currency: 'USD',
    category: 'Marketing',
    tags: ['email', 'sequence', 'copywriting'],
    seller: { id: 's9', name: 'ConvertCopy', avatar: '/avatars/seller9.jpg', rating: 4.7, totalSales: 203 },
    thumbnail: '/listings/email1.jpg',
    images: ['/listings/email1.jpg'],
    createdAt: '2026-09-12T10:00:00Z',
    inStock: true,
    deliveryTime: '4 business days',
  },
  {
    id: '10',
    title: 'Brand Identity Package',
    description: 'Complete brand identity including logo, color palette, typography, and brand guidelines.',
    price: 799.0,
    currency: 'USD',
    category: 'Design',
    tags: ['branding', 'identity', 'logo'],
    seller: { id: 's3', name: 'Pixel Perfect', avatar: '/avatars/seller3.jpg', rating: 5.0, totalSales: 567 },
    thumbnail: '/listings/brand1.jpg',
    images: ['/listings/brand1.jpg'],
    createdAt: '2026-08-30T09:00:00Z',
    inStock: true,
    deliveryTime: '10-14 business days',
  },
  {
    id: '11',
    title: 'TikTok Video Ads (5 pack)',
    description: 'Five scroll-stopping TikTok ad creatives optimized for conversions.',
    price: 249.0,
    currency: 'USD',
    category: 'Video',
    tags: ['tiktok', 'ads', 'creative'],
    seller: { id: 's4', name: 'Frame by Frame', avatar: '/avatars/seller4.jpg', rating: 4.8, totalSales: 234 },
    thumbnail: '/listings/tiktok1.jpg',
    images: ['/listings/tiktok1.jpg'],
    createdAt: '2026-09-28T12:00:00Z',
    inStock: true,
    deliveryTime: '5 business days',
  },
  {
    id: '12',
    title: 'Landing Page Copy',
    description: 'Conversion-focused landing page copy that turns visitors into customers.',
    price: 129.0,
    currency: 'USD',
    category: 'Writing',
    tags: ['copywriting', 'landing', 'conversion'],
    seller: { id: 's5', name: 'WordSmith', avatar: '/avatars/seller5.jpg', rating: 4.6, totalSales: 412 },
    thumbnail: '/listings/landing1.jpg',
    images: ['/listings/landing1.jpg'],
    createdAt: '2026-09-08T14:00:00Z',
    inStock: true,
    deliveryTime: '3 business days',
  },
];

const CATEGORIES = ['All', 'Photography', 'Social Media', 'Design', 'Video', 'Writing', 'Marketing', 'Audio'];
const ITEMS_PER_PAGE = 6;

// ─── Utility ─────────────────────────────────────────────────────────────────

function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(price);
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// ─── Components ──────────────────────────────────────────────────────────────

// SearchBar
function SearchBar({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="relative">
      <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        type="text"
        placeholder="Search listings..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
      />
    </div>
  );
}

// FilterBar
function FilterBar({
  filters,
  onChange,
}: {
  filters: FilterState;
  onChange: (f: FilterState) => void;
}) {
  return (
    <div className="flex flex-wrap gap-3 items-center">
      {/* Category */}
      <select
        value={filters.category}
        onChange={(e) => onChange({ ...filters, category: e.target.value })}
        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
      >
        {CATEGORIES.map((c) => (
          <option key={c} value={c}>{c === 'All' ? 'All Categories' : c}</option>
        ))}
      </select>

      {/* Price Range */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Price:</span>
        <input
          type="number"
          placeholder="Min"
          value={filters.priceRange[0] || ''}
          onChange={(e) => onChange({ ...filters, priceRange: [Number(e.target.value), filters.priceRange[1]] })}
          className="w-20 px-2 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <span className="text-gray-400">—</span>
        <input
          type="number"
          placeholder="Max"
          value={filters.priceRange[1] || ''}
          onChange={(e) => onChange({ ...filters, priceRange: [filters.priceRange[0], Number(e.target.value)] })}
          className="w-20 px-2 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Sort */}
      <select
        value={filters.sortBy}
        onChange={(e) => onChange({ ...filters, sortBy: e.target.value as FilterState['sortBy'] })}
        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
      >
        <option value="newest">Newest</option>
        <option value="price-asc">Price: Low → High</option>
        <option value="price-desc">Price: High → Low</option>
        <option value="popular">Most Popular</option>
      </select>

      {/* In Stock */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={filters.inStockOnly}
          onChange={(e) => onChange({ ...filters, inStockOnly: e.target.checked })}
          className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
        />
        <span className="text-sm text-gray-700">In Stock Only</span>
      </label>
    </div>
  );
}

// ListingCard
function ListingCard({ listing, onSelect }: { listing: Listing; onSelect: (l: Listing) => void }) {
  return (
    <div
      onClick={() => onSelect(listing)}
      className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow cursor-pointer group"
    >
      {/* Thumbnail */}
      <div className="aspect-[4/3] bg-gray-100 relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center text-gray-400">
          <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        {!listing.inStock && (
          <div className="absolute top-2 right-2 bg-red-500 text-white text-xs font-semibold px-2 py-1 rounded">
            Out of Stock
          </div>
        )}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
      </div>

      {/* Info */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-gray-900 text-sm leading-tight line-clamp-2">{listing.title}</h3>
          <span className="text-indigo-600 font-bold text-sm whitespace-nowrap">{formatPrice(listing.price, listing.currency)}</span>
        </div>
        <p className="text-gray-500 text-xs mt-1 line-clamp-2">{listing.description}</p>

        {/* Seller */}
        <div className="flex items-center gap-2 mt-3">
          <div className="h-6 w-6 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-semibold text-indigo-700">
            {listing.seller.name.charAt(0)}
          </div>
          <span className="text-xs text-gray-600">{listing.seller.name}</span>
          <span className="text-xs text-gray-400">★ {listing.seller.rating}</span>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1 mt-2">
          {listing.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">{tag}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

// Pagination
function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (p: number) => void;
}) {
  if (totalPages <= 1) return null;

  const pages: (number | '...')[] = [];
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || Math.abs(i - currentPage) <= 1) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== '...') {
      pages.push('...');
    }
  }

  return (
    <div className="flex items-center justify-center gap-1 mt-8">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50 transition"
      >
        ← Prev
      </button>
      {pages.map((p, i) =>
        p === '...' ? (
          <span key={`ellipsis-${i}`} className="px-2 text-gray-400">…</span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`px-3 py-2 text-sm rounded-lg transition ${
              p === currentPage
                ? 'bg-indigo-600 text-white font-semibold'
                : 'border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {p}
          </button>
        )
      )}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50 transition"
      >
        Next →
      </button>
    </div>
  );
}

// ListingDetailModal
function ListingDetailModal({
  listing,
  onClose,
  onPurchase,
}: {
  listing: Listing;
  onClose: () => void;
  onPurchase: (l: Listing) => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 rounded-full bg-white/80 hover:bg-gray-100 transition"
          aria-label="Close"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Image */}
        <div className="aspect-video bg-gray-100 rounded-t-2xl flex items-center justify-center">
          <svg className="h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">{listing.title}</h2>
              <p className="text-sm text-gray-500 mt-1">{listing.category} · {formatDate(listing.createdAt)}</p>
            </div>
            <span className="text-2xl font-bold text-indigo-600">{formatPrice(listing.price, listing.currency)}</span>
          </div>

          <p className="text-gray-700 mt-4 leading-relaxed">{listing.description}</p>

          {/* Seller Info */}
          <div className="flex items-center gap-3 mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center font-semibold text-indigo-700">
              {listing.seller.name.charAt(0)}
            </div>
            <div>
              <p className="font-medium text-gray-900">{listing.seller.name}</p>
              <p className="text-sm text-gray-500">★ {listing.seller.rating} · {listing.seller.totalSales} sales</p>
            </div>
          </div>

          {/* Meta */}
          <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
            <div>
              <span className="text-gray-500">Delivery:</span>{' '}
              <span className="font-medium text-gray-900">{listing.deliveryTime}</span>
            </div>
            <div>
              <span className="text-gray-500">Status:</span>{' '}
              <span className={`font-medium ${listing.inStock ? 'text-green-600' : 'text-red-600'}`}>
                {listing.inStock ? 'In Stock' : 'Out of Stock'}
              </span>
            </div>
          </div>

          {/* Tags */}
          <div className="flex flex-wrap gap-2 mt-4">
            {listing.tags.map((tag) => (
              <span key={tag} className="px-3 py-1 bg-indigo-50 text-indigo-700 text-sm rounded-full">{tag}</span>
            ))}
          </div>

          {/* CTA */}
          <div className="flex gap-3 mt-6">
            <button
              onClick={() => onPurchase(listing)}
              disabled={!listing.inStock}
              className="flex-1 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {listing.inStock ? 'Purchase Now' : 'Out of Stock'}
            </button>
            <button
              onClick={onClose}
              className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// PurchaseModal
function PurchaseModal({
  listing,
  onClose,
  onConfirm,
}: {
  listing: Listing;
  onClose: () => void;
  onConfirm: (data: PurchaseFormData) => void;
}) {
  const [step, setStep] = useState<1 | 2>(1);
  const [form, setForm] = useState<PurchaseFormData>({
    quantity: 1,
    fullName: '',
    email: '',
    address: '',
    city: '',
    zipCode: '',
    cardNumber: '',
    expiryDate: '',
    cvv: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof PurchaseFormData, string>>>({});

  const total = listing.price * form.quantity;

  const validateStep1 = (): boolean => {
    const e: typeof errors = {};
    if (!form.fullName.trim()) e.fullName = 'Required';
    if (!form.email.trim() || !/\S+@\S+\.\S+/.test(form.email)) e.email = 'Valid email required';
    if (!form.address.trim()) e.address = 'Required';
    if (!form.city.trim()) e.city = 'Required';
    if (!form.zipCode.trim()) e.zipCode = 'Required';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const validateStep2 = (): boolean => {
    const e: typeof errors = {};
    if (!form.cardNumber.trim() || form.cardNumber.replace(/\s/g, '').length < 16) e.cardNumber = 'Valid card number required';
    if (!form.expiryDate.trim()) e.expiryDate = 'Required';
    if (!form.cvv.trim() || form.cvv.length < 3) e.cvv = 'Required';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleNext = () => {
    if (validateStep1()) setStep(2);
  };

  const handleSubmit = () => {
    if (validateStep2()) onConfirm(form);
  };

  const update = (field: keyof PurchaseFormData, value: string | number) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Complete Purchase</h2>
            <p className="text-sm text-gray-500">{listing.title}</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100 transition" aria-label="Close">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Steps indicator */}
        <div className="flex items-center gap-2 px-6 pt-4">
          <div className={`h-1 flex-1 rounded ${step >= 1 ? 'bg-indigo-600' : 'bg-gray-200'}`} />
          <div className={`h-1 flex-1 rounded ${step >= 2 ? 'bg-indigo-600' : 'bg-gray-200'}`} />
        </div>

        <div className="p-6">
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900">Shipping Information</h3>

              {/* Quantity */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                <input
                  type="number"
                  min={1}
                  value={form.quantity}
                  onChange={(e) => update('quantity', Math.max(1, Number(e.target.value)))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={form.fullName}
                  onChange={(e) => update('fullName', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 ${errors.fullName ? 'border-red-500' : 'border-gray-300'}`}
                />
                {errors.fullName && <p className="text-red-500 text-xs mt-1">{errors.fullName}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => update('email', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 ${errors.email ? 'border-red-500' : 'border-gray-300'}`}
                />
                {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                <input
                  type="text"
                  value={form.address}
                  onChange={(e) => update('address', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 ${errors.address ? 'border-red-500' : 'border-gray-300'}`}
                />
                {errors.address && <p className="text-red-500 text-xs mt-1">{errors.address}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                  <input
                    type="text"
                    value={form.city}
                    onChange={(e) => update('city', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 ${errors.city ? 'border-red-500' : 'border-gray-300'}`}
                  />
                  {errors.city && <p className="text-red-500 text-xs mt-1">{errors.city}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ZIP Code</label>
                  <input
                    type="text"
                    value={form.zipCode}
                    onChange={(e) => update('zipCode', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 ${errors.zipCode ? 'border-red-500' : 'border-gray-300'}`}
                  />
                  {errors.zipCode && <p className="text-red-500 text-xs mt-1">{errors.zipCode}</p>}
                </div>
              </div>

              <button
                onClick={handleNext}
                className="w-full py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition mt-4"
              >
                Continue to Payment →
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900">Payment Details</h3>

              {/* Order Summary */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">{listing.title} × {form.quantity}</span>
                  <span className="font-medium">{formatPrice(total, listing.currency)}</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span className="text-gray-600">Shipping</span>
                  <span className="font-medium text-green-600">Free</span>
                </div>
                <hr className="my-2" />
                <div className="flex justify-between font-bold">
                  <span>Total</span>
                  <span className="text-indigo-600">{formatPrice(total, listing.currency)}</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Card Number</label>
                <input
                  type="text"
                  placeholder="4242 4242 4242 4242"
                  value={form.cardNumber}
                  onChange={(e) => update('cardNumber', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 ${errors.cardNumber ? 'border-red-500' : 'border-gray-300'}`}
                />
                {errors.cardNumber && <p className="text-red-500 text-xs mt-1">{errors.cardNumber}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Expiry</label>
                  <input
                    type="text"
                    placeholder="MM/YY"
                    value={form.expiryDate}
                    onChange={(e) => update('expiryDate', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 ${errors.expiryDate ? 'border-red-500' : 'border-gray-300'}`}
                  />
                  {errors.expiryDate && <p className="text-red-500 text-xs mt-1">{errors.expiryDate}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">CVV</label>
                  <input
                    type="text"
                    placeholder="123"
                    maxLength={4}
                    value={form.cvv}
                    onChange={(e) => update('cvv', e.target.value)}
                    className={`w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 ${errors.cvv ? 'border-red-500' : 'border-gray-300'}`}
                  />
                  {errors.cvv && <p className="text-red-500 text-xs mt-1">{errors.cvv}</p>}
                </div>
              </div>

              <div className="flex gap-3 mt-4">
                <button
                  onClick={() => setStep(1)}
                  className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  ← Back
                </button>
                <button
                  onClick={handleSubmit}
                  className="flex-1 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition"
                >
                  Pay {formatPrice(total, listing.currency)}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// SuccessModal
function SuccessModal({ listing, onClose }: { listing: Listing; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl max-w-sm w-full p-8 text-center">
        <div className="mx-auto h-16 w-16 bg-green-100 rounded-full flex items-center justify-center">
          <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-gray-900 mt-4">Order Confirmed!</h2>
        <p className="text-gray-600 mt-2">
          Your order for <span className="font-medium">{listing.title}</span> has been placed successfully.
        </p>
        <p className="text-sm text-gray-500 mt-1">A confirmation email has been sent to your inbox.</p>
        <button
          onClick={onClose}
          className="mt-6 px-6 py-2.5 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition"
        >
          Continue Shopping
        </button>
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function MarketplacePage() {
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<FilterState>({
    category: 'All',
    priceRange: [0, 0],
    sortBy: 'newest',
    inStockOnly: false,
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedListing, setSelectedListing] = useState<Listing | null>(null);
  const [purchasingListing, setPurchasingListing] = useState<Listing | null>(null);
  const [successListing, setSuccessListing] = useState<Listing | null>(null);

  // Filter + search + sort
  const filteredListings = useMemo(() => {
    let result = [...MOCK_LISTINGS];

    // Search
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (l) =>
          l.title.toLowerCase().includes(q) ||
          l.description.toLowerCase().includes(q) ||
          l.tags.some((t) => t.toLowerCase().includes(q)) ||
          l.seller.name.toLowerCase().includes(q)
      );
    }

    // Category
    if (filters.category !== 'All') {
      result = result.filter((l) => l.category === filters.category);
    }

    // Price range
    if (filters.priceRange[0] > 0) {
      result = result.filter((l) => l.price >= filters.priceRange[0]);
    }
    if (filters.priceRange[1] > 0) {
      result = result.filter((l) => l.price <= filters.priceRange[1]);
    }

    // In stock
    if (filters.inStockOnly) {
      result = result.filter((l) => l.inStock);
    }

    // Sort
    switch (filters.sortBy) {
      case 'price-asc':
        result.sort((a, b) => a.price - b.price);
        break;
      case 'price-desc':
        result.sort((a, b) => b.price - a.price);
        break;
      case 'popular':
        result.sort((a, b) => b.seller.totalSales - a.seller.totalSales);
        break;
      case 'newest':
      default:
        result.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
        break;
    }

    return result;
  }, [search, filters]);

  // Pagination
  const totalPages = Math.ceil(filteredListings.length / ITEMS_PER_PAGE);
  const paginatedListings = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredListings.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredListings, currentPage]);

  // Reset page on filter change
  const handleFilterChange = useCallback((f: FilterState) => {
    setFilters(f);
    setCurrentPage(1);
  }, []);

  const handleSearchChange = useCallback((v: string) => {
    setSearch(v);
    setCurrentPage(1);
  }, []);

  const handlePurchase = useCallback((listing: Listing) => {
    setSelectedListing(null);
    setPurchasingListing(listing);
  }, []);

  const handleConfirmPurchase = useCallback((_data: PurchaseFormData) => {
    if (purchasingListing) {
      setSuccessListing(purchasingListing);
      setPurchasingListing(null);
    }
  }, [purchasingListing]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              UGC <span className="text-indigo-600">Marketplace</span>
            </h1>
            <div className="flex items-center gap-4">
              <button className="relative p-2 text-gray-600 hover:text-gray-900 transition">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" />
                </svg>
                <span className="absolute -top-1 -right-1 h-5 w-5 bg-indigo-600 text-white text-xs rounded-full flex items-center justify-center">3</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search + Filters */}
        <div className="space-y-4 mb-8">
          <SearchBar value={search} onChange={handleSearchChange} />
          <FilterBar filters={filters} onChange={handleFilterChange} />
        </div>

        {/* Results count */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-gray-600">
            Showing <span className="font-medium">{paginatedListings.length}</span> of{' '}
            <span className="font-medium">{filteredListings.length}</span> results
          </p>
        </div>

        {/* Listing Grid */}
        {paginatedListings.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {paginatedListings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} onSelect={setSelectedListing} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No listings found</h3>
            <p className="mt-2 text-gray-500">Try adjusting your search or filter criteria.</p>
            <button
              onClick={() => {
                setSearch('');
                handleFilterChange({ category: 'All', priceRange: [0, 0], sortBy: 'newest', inStockOnly: false });
              }}
              className="mt-4 px-4 py-2 text-sm text-indigo-600 font-medium hover:text-indigo-800 transition"
            >
              Clear all filters
            </button>
          </div>
        )}

        {/* Pagination */}
        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
      </main>

      {/* Modals */}
      {selectedListing && (
        <ListingDetailModal
          listing={selectedListing}
          onClose={() => setSelectedListing(null)}
          onPurchase={handlePurchase}
        />
      )}

      {purchasingListing && (
        <PurchaseModal
          listing={purchasingListing}
          onClose={() => setPurchasingListing(null)}
          onConfirm={handleConfirmPurchase}
        />
      )}

      {successListing && (
        <SuccessModal
          listing={successListing}
          onClose={() => setSuccessListing(null)}
        />
      )}
    </div>
  );
}
