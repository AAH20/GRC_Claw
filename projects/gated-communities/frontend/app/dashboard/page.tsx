'use client';

import React, { useState } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface StatCard {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: string;
}

interface ActivityItem {
  id: string;
  user: string;
  action: string;
  target: string;
  time: string;
  type: 'join' | 'message' | 'event' | 'milestone';
}

interface HealthData {
  name: string;
  health: number;
  members: number;
}

interface QuickAction {
  label: string;
  description: string;
  icon: string;
  href: string;
  color: string;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const stats: StatCard[] = [
  {
    title: 'Total Communities',
    value: '24',
    change: '+3 this month',
    changeType: 'positive',
    icon: '🏘️',
  },
  {
    title: 'Active Members',
    value: '1,847',
    change: '+12.5%',
    changeType: 'positive',
    icon: '👥',
  },
  {
    title: 'Events Hosted',
    value: '156',
    change: '+8 this week',
    changeType: 'positive',
    icon: '📅',
  },
  {
    title: 'Messages Sent',
    value: '12.4K',
    change: '-2.1%',
    changeType: 'negative',
    icon: '💬',
  },
];

const recentActivity: ActivityItem[] = [
  {
    id: '1',
    user: 'Sarah Chen',
    action: 'joined',
    target: 'DeFi Builders',
    time: '2 min ago',
    type: 'join',
  },
  {
    id: '2',
    user: 'Marcus Johnson',
    action: 'posted in',
    target: 'NFT Artists Guild',
    time: '15 min ago',
    type: 'message',
  },
  {
    id: '3',
    user: 'Elena Rodriguez',
    action: 'created event in',
    target: 'Web3 Gaming',
    time: '1 hr ago',
    type: 'event',
  },
  {
    id: '4',
    user: 'DeFi Builders',
    action: 'reached',
    target: '500 members milestone',
    time: '3 hrs ago',
    type: 'milestone',
  },
  {
    id: '5',
    user: 'Aisha Patel',
    action: 'joined',
    target: 'AI Researchers',
    time: '5 hrs ago',
    type: 'join',
  },
  {
    id: '6',
    user: 'Tom Williams',
    action: 'posted in',
    target: 'Crypto Traders',
    time: '6 hrs ago',
    type: 'message',
  },
];

const healthData: HealthData[] = [
  { name: 'DeFi Builders', health: 92, members: 512 },
  { name: 'NFT Artists', health: 78, members: 324 },
  { name: 'Web3 Gaming', health: 85, members: 445 },
  { name: 'AI Researchers', health: 67, members: 289 },
  { name: 'Crypto Traders', health: 94, members: 277 },
];

const quickActions: QuickAction[] = [
  {
    label: 'Create Community',
    description: 'Start a new gated community',
    icon: '➕',
    href: '/communities/new',
    color: 'bg-blue-600 hover:bg-blue-700',
  },
  {
    label: 'Invite Members',
    description: 'Grow your community',
    icon: '📨',
    href: '/invites',
    color: 'bg-emerald-600 hover:bg-emerald-700',
  },
  {
    label: 'Schedule Event',
    description: 'Plan your next gathering',
    icon: '📅',
    href: '/events/new',
    color: 'bg-purple-600 hover:bg-purple-700',
  },
  {
    label: 'View Analytics',
    description: 'Deep dive into metrics',
    icon: '📊',
    href: '/analytics',
    color: 'bg-amber-600 hover:bg-amber-700',
  },
];

// ─── Components ──────────────────────────────────────────────────────────────

function StatsCard({ stat }: { stat: StatCard }) {
  const changeColor =
    stat.changeType === 'positive'
      ? 'text-emerald-600'
      : stat.changeType === 'negative'
        ? 'text-red-600'
        : 'text-gray-500';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{stat.title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stat.value}</p>
        </div>
        <span className="text-3xl">{stat.icon}</span>
      </div>
      <div className="mt-4 flex items-center">
        <span className={`text-sm font-medium ${changeColor}`}>{stat.change}</span>
      </div>
    </div>
  );
}

function ActivityFeed({ items }: { items: ActivityItem[] }) {
  const typeIcon: Record<ActivityItem['type'], string> = {
    join: '🎉',
    message: '💬',
    event: '📅',
    milestone: '🏆',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
      <div className="space-y-4">
        {items.map((item) => (
          <div key={item.id} className="flex items-start gap-3">
            <span className="text-lg mt-0.5">{typeIcon[item.type]}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900">
                <span className="font-medium">{item.user}</span>{' '}
                <span className="text-gray-500">{item.action}</span>{' '}
                <span className="font-medium">{item.target}</span>
              </p>
              <p className="text-xs text-gray-400 mt-0.5">{item.time}</p>
            </div>
          </div>
        ))}
      </div>
      <button className="mt-4 w-full text-sm text-blue-600 hover:text-blue-700 font-medium">
        View all activity →
      </button>
    </div>
  );
}

function HealthChart({ data }: { data: HealthData[] }) {
  const maxMembers = Math.max(...data.map((d) => d.members));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Community Health</h2>
      <div className="space-y-4">
        {data.map((community) => (
          <div key={community.name}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">{community.name}</span>
              <span className="text-sm text-gray-500">{community.health}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className={`h-2.5 rounded-full transition-all duration-500 ${
                  community.health >= 80
                    ? 'bg-emerald-500'
                    : community.health >= 60
                      ? 'bg-amber-500'
                      : 'bg-red-500'
                }`}
                style={{ width: `${community.health}%` }}
              />
            </div>
            <p className="text-xs text-gray-400 mt-0.5">{community.members} members</p>
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500" /> Healthy (80%+)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-amber-500" /> At Risk (60-79%)
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-500" /> Critical (&lt;60%)
        </span>
      </div>
    </div>
  );
}

function QuickActions({ actions }: { actions: QuickAction[] }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {actions.map((action) => (
          <a
            key={action.label}
            href={action.href}
            className={`${action.color} text-white rounded-lg p-4 transition-colors group`}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{action.icon}</span>
              <div>
                <p className="font-medium">{action.label}</p>
                <p className="text-sm opacity-80">{action.description}</p>
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 1000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-sm text-gray-500 mt-0.5">
                Overview of your gated communities
              </p>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              {refreshing ? '⟳ Refreshing…' : '↻ Refresh'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {stats.map((stat) => (
            <StatsCard key={stat.title} stat={stat} />
          ))}
        </section>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Activity + Quick Actions */}
          <div className="lg:col-span-2 space-y-6">
            <ActivityFeed items={recentActivity} />
            <QuickActions actions={quickActions} />
          </div>

          {/* Right Column: Health Chart */}
          <div className="lg:col-span-1">
            <HealthChart data={healthData} />
          </div>
        </div>
      </main>
    </div>
  );
}
