'use client';

import { useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// ─── Types ───────────────────────────────────────────────────────────────────

interface TimeToHireData {
  month: string;
  avgDays: number;
  target: number;
}

interface SourceEffectiveness {
  source: string;
  applications: number;
  hires: number;
  conversionRate: number;
}

interface DiversityMetric {
  category: string;
  current: number;
  target: number;
  color: string;
}

interface CostPerHire {
  department: string;
  cost: number;
  budget: number;
}

interface DateRange {
  label: string;
  value: string;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const timeToHireData: TimeToHireData[] = [
  { month: 'Jan', avgDays: 32, target: 30 },
  { month: 'Feb', avgDays: 28, target: 30 },
  { month: 'Mar', avgDays: 35, target: 30 },
  { month: 'Apr', avgDays: 26, target: 30 },
  { month: 'May', avgDays: 24, target: 30 },
  { month: 'Jun', avgDays: 29, target: 30 },
  { month: 'Jul', avgDays: 31, target: 30 },
  { month: 'Aug', avgDays: 27, target: 30 },
  { month: 'Sep', avgDays: 25, target: 30 },
  { month: 'Oct', avgDays: 23, target: 30 },
  { month: 'Nov', avgDays: 28, target: 30 },
  { month: 'Dec', avgDays: 30, target: 30 },
];

const sourceEffectivenessData: SourceEffectiveness[] = [
  { source: 'LinkedIn', applications: 450, hires: 45, conversionRate: 10 },
  { source: 'Indeed', applications: 380, hires: 30, conversionRate: 7.9 },
  { source: 'Referrals', applications: 120, hires: 36, conversionRate: 30 },
  { source: 'Glassdoor', applications: 200, hires: 14, conversionRate: 7 },
  { source: 'Career Fair', applications: 300, hires: 18, conversionRate: 6 },
  { source: 'Agency', applications: 80, hires: 12, conversionRate: 15 },
];

const diversityMetricsData: DiversityMetric[] = [
  { category: 'Gender (Women)', current: 42, target: 50, color: '#8b5cf6' },
  { category: 'Ethnic Minorities', current: 28, target: 35, color: '#06b6d4' },
  { category: 'Veterans', current: 8, target: 10, color: '#f59e0b' },
  { category: 'Disability', current: 5, target: 7, color: '#10b981' },
  { category: 'LGBTQ+', current: 12, target: 15, color: '#ec4899' },
];

const costPerHireData: CostPerHire[] = [
  { department: 'Engineering', cost: 8500, budget: 10000 },
  { department: 'Sales', cost: 5200, budget: 6000 },
  { department: 'Marketing', cost: 6800, budget: 7500 },
  { department: 'HR', cost: 4500, budget: 5000 },
  { department: 'Finance', cost: 7200, budget: 8000 },
  { department: 'Operations', cost: 5800, budget: 6500 },
];

const dateRanges: DateRange[] = [
  { label: 'Last 30 Days', value: '30d' },
  { label: 'Last 90 Days', value: '90d' },
  { label: 'Last 6 Months', value: '6m' },
  { label: 'Last 12 Months', value: '12m' },
  { label: 'YTD', value: 'ytd' },
];

// ─── Components ──────────────────────────────────────────────────────────────

function StatCard({
  title,
  value,
  change,
  changeLabel,
  trend,
}: {
  title: string;
  value: string;
  change: string;
  changeLabel: string;
  trend: 'up' | 'down' | 'neutral';
}) {
  const trendColor =
    trend === 'up'
      ? 'text-emerald-600'
      : trend === 'down'
        ? 'text-red-600'
        : 'text-gray-500';
  const trendIcon = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→';

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      <p className={`mt-2 text-sm font-medium ${trendColor}`}>
        {trendIcon} {change}{' '}
        <span className="font-normal text-gray-400">{changeLabel}</span>
      </p>
    </div>
  );
}

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
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [selectedRange, setSelectedRange] = useState('12m');

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
            Recruitment Analytics
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Track hiring performance, source effectiveness, and diversity metrics
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {dateRanges.map((range) => (
            <button
              key={range.value}
              onClick={() => setSelectedRange(range.value)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                selectedRange === range.value
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Avg Time to Hire"
          value="27.5 days"
          change="3.2 days"
          changeLabel="vs last period"
          trend="down"
        />
        <StatCard
          title="Total Hires"
          value="155"
          change="12.3%"
          changeLabel="vs last period"
          trend="up"
        />
        <StatCard
          title="Cost per Hire"
          value="$6,240"
          change="$380"
          changeLabel="vs last period"
          trend="down"
        />
        <StatCard
          title="Offer Acceptance"
          value="87.2%"
          change="2.1%"
          changeLabel="vs last period"
          trend="up"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Time to Hire Chart */}
        <ChartCard
          title="Time to Hire"
          subtitle="Average days from application to offer acceptance"
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeToHireData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                  label={{
                    value: 'Days',
                    angle: -90,
                    position: 'insideLeft',
                    style: { fontSize: 12, fill: '#6b7280' },
                  }}
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
                  dataKey="avgDays"
                  name="Avg Days"
                  stroke="#4f46e5"
                  strokeWidth={2}
                  dot={{ fill: '#4f46e5', r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="target"
                  name="Target"
                  stroke="#9ca3af"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        {/* Source Effectiveness Chart */}
        <ChartCard
          title="Source Effectiveness"
          subtitle="Applications and hires by recruitment channel"
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sourceEffectivenessData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="source"
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                />
                <Legend />
                <Bar
                  dataKey="applications"
                  name="Applications"
                  fill="#c7d2fe"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="hires"
                  name="Hires"
                  fill="#4f46e5"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        {/* Diversity Metrics */}
        <ChartCard
          title="Diversity Metrics"
          subtitle="Current representation vs target goals"
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={diversityMetricsData}
                layout="vertical"
                margin={{ left: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  type="number"
                  domain={[0, 60]}
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                  label={{
                    value: 'Percentage (%)',
                    position: 'insideBottom',
                    offset: -5,
                    style: { fontSize: 12, fill: '#6b7280' },
                  }}
                />
                <YAxis
                  type="category"
                  dataKey="category"
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                  width={120}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                  formatter={(value: number, name: string) => [
                    `${value}%`,
                    name,
                  ]}
                />
                <Legend />
                <Bar
                  dataKey="current"
                  name="Current"
                  fill="#8b5cf6"
                  radius={[0, 4, 4, 0]}
                />
                <Bar
                  dataKey="target"
                  name="Target"
                  fill="#e5e7eb"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        {/* Cost per Hire Chart */}
        <ChartCard
          title="Cost per Hire"
          subtitle="Actual hiring cost vs budget by department"
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={costPerHireData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="department"
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  axisLine={{ stroke: '#e5e7eb' }}
                  tickFormatter={(value: number) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                  formatter={(value: number) => [
                    `$${value.toLocaleString()}`,
                    '',
                  ]}
                />
                <Legend />
                <Bar
                  dataKey="cost"
                  name="Actual Cost"
                  fill="#06b6d4"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="budget"
                  name="Budget"
                  fill="#e5e7eb"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>

      {/* Source Conversion Pie Chart */}
      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard
          title="Source Conversion Rates"
          subtitle="Hire conversion percentage by source"
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sourceEffectivenessData}
                  dataKey="conversionRate"
                  nameKey="source"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={40}
                  paddingAngle={2}
                  label={({ source, conversionRate }: { source: string; conversionRate: number }) =>
                    `${source}: ${conversionRate}%`
                  }
                  labelLine={true}
                >
                  {sourceEffectivenessData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][
                          index % 6
                        ]
                      }
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                  formatter={(value: number) => [`${value}%`, 'Conversion Rate']}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        {/* Diversity Breakdown */}
        <ChartCard
          title="Diversity Breakdown"
          subtitle="Detailed diversity composition"
        >
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={diversityMetricsData}
                  dataKey="current"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={40}
                  paddingAngle={2}
                  label={({ category, current }: { category: string; current: number }) =>
                    `${category}: ${current}%`
                  }
                  labelLine={true}
                >
                  {diversityMetricsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  }}
                  formatter={(value: number) => [`${value}%`, 'Representation']}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>
    </div>
  );
}
