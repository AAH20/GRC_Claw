'use client';

import React from 'react';

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
  type: 'application' | 'interview' | 'hire' | 'note';
  message: string;
  timestamp: string;
  candidateName?: string;
  position?: string;
}

interface FunnelStage {
  stage: string;
  count: number;
  percentage: number;
}

interface QuickAction {
  label: string;
  icon: string;
  href: string;
  color: string;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const stats: StatCard[] = [
  {
    title: 'Open Positions',
    value: '24',
    change: '+3 this month',
    changeType: 'positive',
    icon: 'briefcase',
  },
  {
    title: 'Active Candidates',
    value: '147',
    change: '+12 this week',
    changeType: 'positive',
    icon: 'users',
  },
  {
    title: 'Interviews Scheduled',
    value: '18',
    change: '5 today',
    changeType: 'neutral',
    icon: 'calendar',
  },
  {
    title: 'Avg. Time-to-Hire',
    value: '23 days',
    change: '-2 days',
    changeType: 'positive',
    icon: 'clock',
  },
];

const recentActivity: ActivityItem[] = [
  {
    id: '1',
    type: 'application',
    message: 'New application received for Senior Frontend Developer',
    timestamp: '5 min ago',
    candidateName: 'Sarah Chen',
    position: 'Senior Frontend Developer',
  },
  {
    id: '2',
    type: 'interview',
    message: 'Interview scheduled with Michael Torres',
    timestamp: '1 hour ago',
    candidateName: 'Michael Torres',
    position: 'Product Manager',
  },
  {
    id: '3',
    type: 'hire',
    message: 'Offer accepted by Priya Sharma',
    timestamp: '3 hours ago',
    candidateName: 'Priya Sharma',
    position: 'UX Designer',
  },
  {
    id: '4',
    type: 'note',
    message: 'Interview feedback submitted for David Kim',
    timestamp: '5 hours ago',
    candidateName: 'David Kim',
    position: 'Backend Engineer',
  },
  {
    id: '5',
    type: 'application',
    message: 'New application received for Data Scientist',
    timestamp: 'Yesterday',
    candidateName: 'Alex Rivera',
    position: 'Data Scientist',
  },
  {
    id: '6',
    type: 'interview',
    message: 'Phone screen completed with Emma Wilson',
    timestamp: 'Yesterday',
    candidateName: 'Emma Wilson',
    position: 'DevOps Engineer',
  },
];

const funnelStages: FunnelStage[] = [
  { stage: 'Applied', count: 342, percentage: 100 },
  { stage: 'Screened', count: 186, percentage: 54 },
  { stage: 'Interviewed', count: 74, percentage: 22 },
  { stage: 'Offered', count: 28, percentage: 8 },
  { stage: 'Hired', count: 18, percentage: 5 },
];

const quickActions: QuickAction[] = [
  {
    label: 'Post New Job',
    icon: 'plus',
    href: '/jobs/new',
    color: 'bg-blue-600 hover:bg-blue-700',
  },
  {
    label: 'Add Candidate',
    icon: 'user-plus',
    href: '/candidates/new',
    color: 'bg-emerald-600 hover:bg-emerald-700',
  },
  {
    label: 'Schedule Interview',
    icon: 'calendar-plus',
    href: '/interviews/new',
    color: 'bg-purple-600 hover:bg-purple-700',
  },
  {
    label: 'View Reports',
    icon: 'chart-bar',
    href: '/reports',
    color: 'bg-amber-600 hover:bg-amber-700',
  },
];

// ─── Icon Component ──────────────────────────────────────────────────────────

function Icon({ name, className = 'w-5 h-5' }: { name: string; className?: string }) {
  const icons: Record<string, React.ReactNode> = {
    briefcase: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    users: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
    calendar: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
    clock: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    plus: (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
      </svg>
    ),
    'user-plus': (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
      </svg>
    ),
    'calendar-plus': (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2zM12 14v4m-2-2h4" />
      </svg>
    ),
    'chart-bar': (
      <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  };

  return <>{icons[name] ?? null}</>;
}

// ─── Activity Icon ───────────────────────────────────────────────────────────

function ActivityIcon({ type }: { type: ActivityItem['type'] }) {
  const config: Record<ActivityItem['type'], { bg: string; icon: string }> = {
    application: { bg: 'bg-blue-100 text-blue-600', icon: 'briefcase' },
    interview: { bg: 'bg-purple-100 text-purple-600', icon: 'calendar' },
    hire: { bg: 'bg-emerald-100 text-emerald-600', icon: 'users' },
    note: { bg: 'bg-amber-100 text-amber-600', icon: 'chart-bar' },
  };

  const { bg, icon } = config[type];

  return (
    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${bg}`}>
      <Icon name={icon} className="w-4 h-4" />
    </div>
  );
}

// ─── Components ──────────────────────────────────────────────────────────────

function StatsCard({ stat }: { stat: StatCard }) {
  const changeColors = {
    positive: 'text-emerald-600',
    negative: 'text-red-600',
    neutral: 'text-gray-500',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{stat.title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{stat.value}</p>
        </div>
        <div className="w-12 h-12 rounded-lg bg-gray-50 flex items-center justify-center text-gray-400">
          <Icon name={stat.icon} className="w-6 h-6" />
        </div>
      </div>
      <p className={`text-sm mt-3 font-medium ${changeColors[stat.changeType]}`}>
        {stat.change}
      </p>
    </div>
  );
}

function ActivityFeed() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
      <div className="space-y-4">
        {recentActivity.map((item) => (
          <div key={item.id} className="flex items-start gap-3">
            <ActivityIcon type={item.type} />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-700">{item.message}</p>
              <p className="text-xs text-gray-400 mt-1">{item.timestamp}</p>
            </div>
          </div>
        ))}
      </div>
      <button className="mt-4 w-full text-sm text-blue-600 hover:text-blue-700 font-medium py-2 rounded-lg hover:bg-blue-50 transition-colors">
        View All Activity
      </button>
    </div>
  );
}

function PipelineFunnel() {
  const maxCount = funnelStages[0]?.count ?? 1;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Hiring Pipeline</h2>
      <div className="space-y-3">
        {funnelStages.map((stage, index) => {
          const widthPercentage = (stage.count / maxCount) * 100;
          const barColors = [
            'bg-blue-500',
            'bg-indigo-500',
            'bg-purple-500',
            'bg-pink-500',
            'bg-emerald-500',
          ];

          return (
            <div key={stage.stage} className="group">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">{stage.stage}</span>
                <span className="text-sm text-gray-500">
                  {stage.count} <span className="text-gray-400">({stage.percentage}%)</span>
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full rounded-full ${barColors[index]} transition-all duration-500 group-hover:opacity-80`}
                  style={{ width: `${widthPercentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Overall conversion</span>
          <span className="font-semibold text-gray-900">
            {((funnelStages[funnelStages.length - 1]?.count ?? 0) / maxCount * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
}

function QuickActions() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {quickActions.map((action) => (
          <a
            key={action.label}
            href={action.href}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg text-white font-medium text-sm transition-colors ${action.color}`}
          >
            <Icon name={action.icon} className="w-4 h-4" />
            {action.label}
          </a>
        ))}
      </div>
    </div>
  );
}

// ─── Dashboard Page ──────────────────────────────────────────────────────────

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-sm text-gray-500 mt-1">
                Welcome back! Here&apos;s your recruiting overview.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-500">
                {new Date().toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => (
            <StatsCard key={stat.title} stat={stat} />
          ))}
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Activity + Quick Actions */}
          <div className="lg:col-span-2 space-y-6">
            <ActivityFeed />
            <QuickActions />
          </div>

          {/* Right Column: Pipeline Funnel */}
          <div className="lg:col-span-1">
            <PipelineFunnel />
          </div>
        </div>
      </div>
    </div>
  );
}
