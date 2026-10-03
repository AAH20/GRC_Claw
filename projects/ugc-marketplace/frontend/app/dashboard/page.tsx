'use client';

import { useState } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface StatCardProps {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
}

interface ActivityItem {
  id: string;
  user: string;
  action: string;
  target: string;
  time: string;
  type: 'upload' | 'purchase' | 'join' | 'review';
}

interface RevenueDataPoint {
  month: string;
  revenue: number;
}

interface QuickAction {
  label: string;
  description: string;
  icon: React.ReactNode;
  href: string;
  color: string;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const stats = [
  {
    title: 'Total Creators',
    value: '2,847',
    change: '+12.5%',
    changeType: 'positive' as const,
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
  {
    title: 'Total Content',
    value: '18,492',
    change: '+8.2%',
    changeType: 'positive' as const,
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    title: 'Revenue',
    value: '$124,580',
    change: '+23.1%',
    changeType: 'positive' as const,
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    title: 'Active Users',
    value: '5,231',
    change: '-2.4%',
    changeType: 'negative' as const,
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
  },
];

const recentActivity: ActivityItem[] = [
  {
    id: '1',
    user: 'Sarah Chen',
    action: 'uploaded',
    target: 'Summer Collection Photos',
    time: '2 min ago',
    type: 'upload',
  },
  {
    id: '2',
    user: 'Marcus Johnson',
    action: 'purchased',
    target: 'Brand Ambassador Package',
    time: '15 min ago',
    type: 'purchase',
  },
  {
    id: '3',
    user: 'Emily Rodriguez',
    action: 'joined as a',
    target: 'Content Creator',
    time: '1 hour ago',
    type: 'join',
  },
  {
    id: '4',
    user: 'David Kim',
    action: 'left a review on',
    target: 'Product Showcase Video',
    time: '2 hours ago',
    type: 'review',
  },
  {
    id: '5',
    user: 'Lisa Thompson',
    action: 'uploaded',
    target: 'Unboxing Experience',
    time: '3 hours ago',
    type: 'upload',
  },
  {
    id: '6',
    user: 'James Wilson',
    action: 'purchased',
    target: 'Social Media Bundle',
    time: '4 hours ago',
    type: 'purchase',
  },
];

const revenueData: RevenueDataPoint[] = [
  { month: 'Jan', revenue: 8200 },
  { month: 'Feb', revenue: 9800 },
  { month: 'Mar', revenue: 11500 },
  { month: 'Apr', revenue: 10200 },
  { month: 'May', revenue: 13400 },
  { month: 'Jun', revenue: 15800 },
  { month: 'Jul', revenue: 14200 },
  { month: 'Aug', revenue: 16900 },
  { month: 'Sep', revenue: 18500 },
  { month: 'Oct', revenue: 17200 },
  { month: 'Nov', revenue: 19800 },
  { month: 'Dec', revenue: 22400 },
];

const quickActions: QuickAction[] = [
  {
    label: 'Add Creator',
    description: 'Onboard a new content creator',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
      </svg>
    ),
    href: '/dashboard/creators/new',
    color: 'bg-blue-500',
  },
  {
    label: 'Upload Content',
    description: 'Add new content to marketplace',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
    ),
    href: '/dashboard/content/upload',
    color: 'bg-green-500',
  },
  {
    label: 'View Analytics',
    description: 'Detailed performance metrics',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    href: '/dashboard/analytics',
    color: 'bg-purple-500',
  },
  {
    label: 'Manage Orders',
    description: 'Process and track orders',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
    href: '/dashboard/orders',
    color: 'bg-orange-500',
  },
];

// ─── Components ──────────────────────────────────────────────────────────────

function StatCard({ title, value, change, changeType, icon }: StatCardProps) {
  const changeColor =
    changeType === 'positive'
      ? 'text-green-600 bg-green-50'
      : changeType === 'negative'
      ? 'text-red-600 bg-red-50'
      : 'text-gray-600 bg-gray-50';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className="p-3 bg-indigo-50 rounded-lg text-indigo-600">
          {icon}
        </div>
      </div>
      <div className="mt-4 flex items-center">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${changeColor}`}>
          {change}
        </span>
        <span className="ml-2 text-sm text-gray-500">vs last month</span>
      </div>
    </div>
  );
}

function ActivityFeed() {
  const typeColors: Record<ActivityItem['type'], string> = {
    upload: 'bg-blue-100 text-blue-600',
    purchase: 'bg-green-100 text-green-600',
    join: 'bg-purple-100 text-purple-600',
    review: 'bg-yellow-100 text-yellow-600',
  };

  const typeLabels: Record<ActivityItem['type'], string> = {
    upload: 'Upload',
    purchase: 'Purchase',
    join: 'New Creator',
    review: 'Review',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
        <button className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
          View All
        </button>
      </div>
      <div className="space-y-4">
        {recentActivity.map((item) => (
          <div key={item.id} className="flex items-start space-x-3">
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${typeColors[item.type]}`}>
              {item.user.split(' ').map((n) => n[0]).join('')}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900">
                <span className="font-medium">{item.user}</span>{' '}
                <span className="text-gray-500">{item.action}</span>{' '}
                <span className="font-medium">{item.target}</span>
              </p>
              <p className="text-xs text-gray-400 mt-1">{item.time}</p>
            </div>
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${typeColors[item.type]}`}>
              {typeLabels[item.type]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RevenueChart() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const maxRevenue = Math.max(...revenueData.map((d) => d.revenue));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Revenue Overview</h2>
          <p className="text-sm text-gray-500 mt-1">Monthly revenue for 2024</p>
        </div>
        <select className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500">
          <option>Last 12 months</option>
          <option>Last 6 months</option>
          <option>Last 30 days</option>
        </select>
      </div>
      <div className="relative h-64">
        <div className="absolute inset-0 flex items-end justify-between gap-2 px-2">
          {revenueData.map((point, index) => {
            const heightPercent = (point.revenue / maxRevenue) * 100;
            const isHovered = hoveredIndex === index;
            return (
              <div
                key={point.month}
                className="flex-1 flex flex-col items-center justify-end h-full relative group"
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
              >
                {isHovered && (
                  <div className="absolute -top-10 bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                    ${point.revenue.toLocaleString()}
                  </div>
                )}
                <div
                  className={`w-full rounded-t-md transition-all duration-200 ${
                    isHovered ? 'bg-indigo-600' : 'bg-indigo-400'
                  }`}
                  style={{ height: `${heightPercent}%` }}
                />
                <span className="text-xs text-gray-400 mt-2 font-medium">
                  {point.month}
                </span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">Total Revenue</p>
          <p className="text-2xl font-bold text-gray-900">$124,580</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Avg. Monthly</p>
          <p className="text-lg font-semibold text-gray-900">$10,382</p>
        </div>
      </div>
    </div>
  );
}

function QuickActions() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Quick Actions</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {quickActions.map((action) => (
          <a
            key={action.label}
            href={action.href}
            className="flex items-center space-x-4 p-4 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-colors group"
          >
            <div className={`p-2.5 rounded-lg text-white ${action.color} group-hover:scale-110 transition-transform`}>
              {action.icon}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">{action.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{action.description}</p>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}

// ─── Main Dashboard Page ────────────────────────────────────────────────────

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              <p className="mt-1 text-sm text-gray-500">
                Welcome back! Here&apos;s what&apos;s happening with your marketplace.
              </p>
            </div>
            <div className="mt-4 sm:mt-0 flex items-center space-x-3">
              <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors">
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Export
              </button>
              <button className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition-colors shadow-sm">
                <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Campaign
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => (
            <StatCard key={stat.title} {...stat} />
          ))}
        </div>

        {/* Charts & Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <RevenueChart />
          </div>
          <div className="lg:col-span-1">
            <QuickActions />
          </div>
        </div>

        {/* Activity Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ActivityFeed />
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Top Creators</h2>
            <div className="space-y-4">
              {[
                { name: 'Sarah Chen', content: 142, revenue: '$12,400', avatar: 'SC' },
                { name: 'Marcus Johnson', content: 98, revenue: '$9,800', avatar: 'MJ' },
                { name: 'Emily Rodriguez', content: 87, revenue: '$8,200', avatar: 'ER' },
                { name: 'David Kim', content: 76, revenue: '$7,100', avatar: 'DK' },
                { name: 'Lisa Thompson', content: 65, revenue: '$6,500', avatar: 'LT' },
              ].map((creator, index) => (
                <div key={creator.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-bold text-gray-400 w-5">
                      {index + 1}
                    </span>
                    <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold">
                      {creator.avatar}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{creator.name}</p>
                      <p className="text-xs text-gray-500">{creator.content} items</p>
                    </div>
                  </div>
                  <span className="text-sm font-semibold text-gray-900">
                    {creator.revenue}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
