'use client';

import { useState } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

// ─── Types ───────────────────────────────────────────────────────────────────

interface EngagementData {
  date: string;
  messages: number;
  reactions: number;
  replies: number;
}

interface GrowthData {
  month: string;
  members: number;
  activeMembers: number;
  newMembers: number;
}

interface ActivityMetric {
  label: string;
  value: string;
  change: number;
  trend: 'up' | 'down' | 'stable';
}

interface HealthData {
  category: string;
  score: number;
  fullMark: number;
}

interface PieData {
  name: string;
  value: number;
  color: string;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const engagementData: EngagementData[] = [
  { date: 'Mon', messages: 145, reactions: 89, replies: 34 },
  { date: 'Tue', messages: 178, reactions: 102, replies: 45 },
  { date: 'Wed', messages: 162, reactions: 95, replies: 38 },
  { date: 'Thu', messages: 198, reactions: 118, replies: 52 },
  { date: 'Fri', messages: 210, reactions: 134, replies: 61 },
  { date: 'Sat', messages: 156, reactions: 87, replies: 29 },
  { date: 'Sun', messages: 134, reactions: 76, replies: 24 },
];

const growthData: GrowthData[] = [
  { month: 'Jan', members: 120, activeMembers: 85, newMembers: 15 },
  { month: 'Feb', members: 145, activeMembers: 102, newMembers: 25 },
  { month: 'Mar', members: 178, activeMembers: 128, newMembers: 33 },
  { month: 'Apr', members: 210, activeMembers: 155, newMembers: 32 },
  { month: 'May', members: 256, activeMembers: 189, newMembers: 46 },
  { month: 'Jun', members: 298, activeMembers: 220, newMembers: 42 },
  { month: 'Jul', members: 342, activeMembers: 258, newMembers: 44 },
  { month: 'Aug', members: 389, activeMembers: 295, newMembers: 47 },
  { month: 'Sep', members: 425, activeMembers: 320, newMembers: 36 },
  { month: 'Oct', members: 478, activeMembers: 365, newMembers: 53 },
];

const activityMetrics: ActivityMetric[] = [
  { label: 'Daily Active Users', value: '365', change: 12.5, trend: 'up' },
  { label: 'Avg. Session Duration', value: '18m 42s', change: 8.3, trend: 'up' },
  { label: 'Messages per User', value: '4.2', change: -2.1, trend: 'down' },
  { label: 'Retention Rate', value: '78%', change: 3.4, trend: 'up' },
  { label: 'Churn Rate', value: '2.1%', change: -0.8, trend: 'up' },
  { label: 'Avg. Response Time', value: '1.2h', change: -15.3, trend: 'up' },
];

const healthData: HealthData[] = [
  { category: 'Engagement', score: 82, fullMark: 100 },
  { category: 'Retention', score: 78, fullMark: 100 },
  { category: 'Growth', score: 91, fullMark: 100 },
  { category: 'Satisfaction', score: 74, fullMark: 100 },
  { category: 'Activity', score: 86, fullMark: 100 },
];

const memberDistribution: PieData[] = [
  { name: 'Highly Active', value: 28, color: '#6366f1' },
  { name: 'Active', value: 35, color: '#8b5cf6' },
  { name: 'Occasional', value: 22, color: '#a78bfa' },
  { name: 'Inactive', value: 15, color: '#c4b5fd' },
];

// ─── Components ──────────────────────────────────────────────────────────────

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {title}
        </h3>
        {subtitle && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {subtitle}
          </p>
        )}
      </div>
      {children}
    </div>
  );
}

function MetricCard({
  label,
  value,
  change,
  trend,
}: ActivityMetric) {
  const trendColor =
    trend === 'up'
      ? 'text-emerald-600 dark:text-emerald-400'
      : trend === 'down'
        ? 'text-red-600 dark:text-red-400'
        : 'text-gray-600 dark:text-gray-400';

  const trendIcon = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→';

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
        {label}
      </p>
      <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
        {value}
      </p>
      <p className={`mt-1 flex items-center gap-1 text-sm font-medium ${trendColor}`}>
        <span>{trendIcon}</span>
        <span>{Math.abs(change)}%</span>
        <span className="text-gray-400 dark:text-gray-500">vs last month</span>
      </p>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white sm:text-3xl">
                Community Analytics
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Track engagement, growth, and health metrics across your gated
                communities.
              </p>
            </div>
            <div className="flex gap-2">
              {(['7d', '30d', '90d', '1y'] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                    timeRange === range
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Activity Metrics Grid */}
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {activityMetrics.map((metric) => (
            <MetricCard key={metric.label} {...metric} />
          ))}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Engagement Chart */}
          <ChartCard
            title="Engagement Overview"
            subtitle="Messages, reactions, and replies over time"
          >
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={engagementData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#e5e7eb' }}
                  />
                  <YAxis
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#e5e7eb' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="messages"
                    stroke="#6366f1"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                    name="Messages"
                  />
                  <Line
                    type="monotone"
                    dataKey="reactions"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                    name="Reactions"
                  />
                  <Line
                    type="monotone"
                    dataKey="replies"
                    stroke="#a78bfa"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                    name="Replies"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          {/* Growth Chart */}
          <ChartCard
            title="Community Growth"
            subtitle="Total and active member trends"
          >
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={growthData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#e5e7eb' }}
                  />
                  <YAxis
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#e5e7eb' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="members"
                    stroke="#6366f1"
                    fill="#6366f1"
                    fillOpacity={0.1}
                    strokeWidth={2}
                    name="Total Members"
                  />
                  <Area
                    type="monotone"
                    dataKey="activeMembers"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.1}
                    strokeWidth={2}
                    name="Active Members"
                  />
                  <Area
                    type="monotone"
                    dataKey="newMembers"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.1}
                    strokeWidth={2}
                    name="New Members"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          {/* Community Health Chart */}
          <ChartCard
            title="Community Health Score"
            subtitle="Performance across key health dimensions"
          >
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={healthData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    type="number"
                    domain={[0, 100]}
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#e5e7eb' }}
                  />
                  <YAxis
                    type="category"
                    dataKey="category"
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    axisLine={{ stroke: '#e5e7eb' }}
                    width={100}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    }}
                  />
                  <Bar
                    dataKey="score"
                    fill="#6366f1"
                    radius={[0, 6, 6, 0]}
                    name="Health Score"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          {/* Member Distribution */}
          <ChartCard
            title="Member Activity Distribution"
            subtitle="Breakdown by activity level"
          >
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={memberDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {memberDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        </div>
      </div>
    </div>
  );
}
