'use client';

import { useState } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// ─── Types ───────────────────────────────────────────────────────────────────

interface RevenueData {
  month: string;
  revenue: number;
  expenses: number;
  profit: number;
}

interface CreatorData {
  name: string;
  contentPieces: number;
  views: number;
  earnings: number;
}

interface EngagementData {
  week: string;
  likes: number;
  shares: number;
  comments: number;
  saves: number;
}

interface GrowthData {
  month: string;
  creators: number;
  brands: number;
  campaigns: number;
  transactions: number;
}

interface MetricCard {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  icon: string;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const revenueData: RevenueData[] = [
  { month: 'Jan', revenue: 42000, expenses: 18000, profit: 24000 },
  { month: 'Feb', revenue: 55000, expenses: 22000, profit: 33000 },
  { month: 'Mar', revenue: 48000, expenses: 20000, profit: 28000 },
  { month: 'Apr', revenue: 61000, expenses: 25000, profit: 36000 },
  { month: 'May', revenue: 72000, expenses: 28000, profit: 44000 },
  { month: 'Jun', revenue: 68000, expenses: 26000, profit: 42000 },
  { month: 'Jul', revenue: 85000, expenses: 32000, profit: 53000 },
  { month: 'Aug', revenue: 91000, expenses: 35000, profit: 56000 },
  { month: 'Sep', revenue: 78000, expenses: 30000, profit: 48000 },
  { month: 'Oct', revenue: 95000, expenses: 38000, profit: 57000 },
  { month: 'Nov', revenue: 102000, expenses: 40000, profit: 62000 },
  { month: 'Dec', revenue: 118000, expenses: 45000, profit: 73000 },
];

const creatorData: CreatorData[] = [
  { name: 'Sarah K.', contentPieces: 48, views: 1250000, earnings: 12400 },
  { name: 'Mike R.', contentPieces: 36, views: 980000, earnings: 9800 },
  { name: 'Lena P.', contentPieces: 42, views: 1100000, earnings: 11200 },
  { name: 'James T.', contentPieces: 28, views: 720000, earnings: 7600 },
  { name: 'Aria M.', contentPieces: 52, views: 1450000, earnings: 14800 },
  { name: 'Dev S.', contentPieces: 31, views: 850000, earnings: 8200 },
];

const engagementData: EngagementData[] = [
  { week: 'W1', likes: 12400, shares: 3200, comments: 1800, saves: 950 },
  { week: 'W2', likes: 15200, shares: 4100, comments: 2200, saves: 1100 },
  { week: 'W3', likes: 13800, shares: 3800, comments: 1950, saves: 1020 },
  { week: 'W4', likes: 18600, shares: 5200, comments: 2800, saves: 1450 },
  { week: 'W5', likes: 21000, shares: 6100, comments: 3200, saves: 1680 },
  { week: 'W6', likes: 19500, shares: 5600, comments: 2950, saves: 1520 },
  { week: 'W7', likes: 24200, shares: 7200, comments: 3800, saves: 1950 },
  { week: 'W8', likes: 26800, shares: 8100, comments: 4200, saves: 2200 },
];

const growthData: GrowthData[] = [
  { month: 'Jan', creators: 120, brands: 45, campaigns: 32, transactions: 890 },
  { month: 'Feb', creators: 158, brands: 52, campaigns: 41, transactions: 1120 },
  { month: 'Mar', creators: 195, brands: 61, campaigns: 48, transactions: 1380 },
  { month: 'Apr', creators: 242, brands: 73, campaigns: 55, transactions: 1650 },
  { month: 'May', creators: 298, brands: 85, campaigns: 67, transactions: 1980 },
  { month: 'Jun', creators: 345, brands: 98, campaigns: 78, transactions: 2340 },
  { month: 'Jul', creators: 412, brands: 115, campaigns: 92, transactions: 2890 },
  { month: 'Aug', creators: 478, brands: 132, campaigns: 105, transactions: 3420 },
  { month: 'Sep', creators: 534, brands: 148, campaigns: 118, transactions: 3980 },
  { month: 'Oct', creators: 612, brands: 167, campaigns: 135, transactions: 4650 },
  { month: 'Nov', creators: 689, brands: 185, campaigns: 152, transactions: 5340 },
  { month: 'Dec', creators: 782, brands: 210, campaigns: 175, transactions: 6280 },
];

const metricCards: MetricCard[] = [
  { title: 'Total Revenue', value: '$815,000', change: '+24.5%', trend: 'up', icon: '💰' },
  { title: 'Active Creators', value: '782', change: '+13.4%', trend: 'up', icon: '🎨' },
  { title: 'Content Pieces', value: '12,450', change: '+18.2%', trend: 'up', icon: '📝' },
  { title: 'Avg. Engagement', value: '8.7%', change: '+2.1%', trend: 'up', icon: '📊' },
  { title: 'Total Views', value: '48.2M', change: '+31.6%', trend: 'up', icon: '👁️' },
  { title: 'Conversion Rate', value: '3.2%', change: '-0.4%', trend: 'down', icon: '🎯' },
];

// ─── Components ──────────────────────────────────────────────────────────────

function MetricCardComponent({ card }: { card: MetricCard }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <span className="text-2xl">{card.icon}</span>
        <span
          className={`text-sm font-semibold px-2 py-1 rounded-full ${
            card.trend === 'up'
              ? 'text-emerald-700 bg-emerald-50'
              : 'text-red-700 bg-red-50'
          }`}
        >
          {card.change}
        </span>
      </div>
      <h3 className="text-sm font-medium text-gray-500 mb-1">{card.title}</h3>
      <p className="text-2xl font-bold text-gray-900">{card.value}</p>
    </div>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
      </div>
      <div className="w-full h-80">{children}</div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '12m'>('12m');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
              <p className="text-sm text-gray-500 mt-1">
                Track marketplace performance, revenue, and engagement metrics
              </p>
            </div>
            <div className="flex items-center gap-2">
              {(['7d', '30d', '90d', '12m'] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    timeRange === range
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {range === '12m' ? '12 Months' : range.replace('d', ' Days')}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
          {metricCards.map((card) => (
            <MetricCardComponent key={card.title} card={card} />
          ))}
        </div>

        {/* Revenue Chart */}
        <div className="mb-8">
          <ChartCard
            title="Revenue Overview"
            subtitle="Monthly revenue, expenses, and profit trends"
          >
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={revenueData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                  tickFormatter={(value) => `$${value / 1000}k`}
                />
                <Tooltip
                  formatter={(value: number) => [`$${value.toLocaleString()}`, undefined]}
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorRevenue)"
                  name="Revenue"
                />
                <Area
                  type="monotone"
                  dataKey="profit"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorProfit)"
                  name="Profit"
                />
                <Line
                  type="monotone"
                  dataKey="expenses"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  name="Expenses"
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Creator Performance & Engagement */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Creator Performance Chart */}
          <ChartCard
            title="Top Creator Performance"
            subtitle="Content output and earnings by creator"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={creatorData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                />
                <Legend />
                <Bar
                  dataKey="contentPieces"
                  fill="#6366f1"
                  radius={[4, 4, 0, 0]}
                  name="Content Pieces"
                />
                <Bar
                  dataKey="earnings"
                  fill="#10b981"
                  radius={[4, 4, 0, 0]}
                  name="Earnings ($)"
                />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Content Engagement Metrics */}
          <ChartCard
            title="Content Engagement"
            subtitle="Weekly likes, shares, comments, and saves"
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={engagementData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="week" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                  tickFormatter={(value) => `${value / 1000}k`}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="likes"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="Likes"
                />
                <Line
                  type="monotone"
                  dataKey="shares"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="Shares"
                />
                <Line
                  type="monotone"
                  dataKey="comments"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="Comments"
                />
                <Line
                  type="monotone"
                  dataKey="saves"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="Saves"
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Marketplace Growth Chart */}
        <div className="mb-8">
          <ChartCard
            title="Marketplace Growth"
            subtitle="Platform growth across creators, brands, campaigns, and transactions"
          >
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={growthData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCreators" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorBrands" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorCampaigns" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorTransactions" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="creators"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorCreators)"
                  name="Creators"
                />
                <Area
                  type="monotone"
                  dataKey="brands"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorBrands)"
                  name="Brands"
                />
                <Area
                  type="monotone"
                  dataKey="campaigns"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorCampaigns)"
                  name="Campaigns"
                />
                <Area
                  type="monotone"
                  dataKey="transactions"
                  stroke="#ef4444"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorTransactions)"
                  name="Transactions"
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-400 py-4">
          Analytics data refreshes every 15 minutes · Last updated: {new Date().toLocaleString()}
        </div>
      </div>
    </div>
  );
}
