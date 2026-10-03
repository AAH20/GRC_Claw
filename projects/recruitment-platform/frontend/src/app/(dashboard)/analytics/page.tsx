"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Users, Briefcase, FileText, Calendar, Download, Filter } from "lucide-react";

const stats = [
  { label: "Total Candidates", value: "1,234", change: 12, icon: Users, color: "bg-blue-500" },
  { label: "Open Jobs", value: "48", change: 8, icon: Briefcase, color: "bg-green-500" },
  { label: "Applications", value: "3,567", change: -3, icon: FileText, color: "bg-purple-500" },
  { label: "Interviews", value: "156", change: 15, icon: Calendar, color: "bg-orange-500" },
];

const applicationsByMonth = [
  { month: "Jan", count: 245 },
  { month: "Feb", count: 312 },
  { month: "Mar", count: 289 },
  { month: "Apr", count: 378 },
  { month: "May", count: 421 },
  { month: "Jun", count: 356 },
];

const candidatesByStatus = [
  { status: "New", count: 234, color: "#3b82f6" },
  { status: "Screening", count: 189, color: "#f59e0b" },
  { status: "Interview", count: 156, color: "#8b5cf6" },
  { status: "Offer", count: 45, color: "#10b981" },
  { status: "Hired", count: 23, color: "#22c55e" },
  { status: "Rejected", count: 587, color: "#ef4444" },
];

const jobsByDepartment = [
  { department: "Engineering", count: 18 },
  { department: "Product", count: 8 },
  { department: "Design", count: 6 },
  { department: "Marketing", count: 5 },
  { department: "Sales", count: 7 },
  { department: "HR", count: 4 },
];

const sourceBreakdown = [
  { source: "LinkedIn", count: 1234, color: "#3b82f6" },
  { source: "Indeed", count: 890, color: "#10b981" },
  { source: "Referral", count: 567, color: "#f59e0b" },
  { source: "Glassdoor", count: 456, color: "#ef4444" },
  { source: "Other", count: 420, color: "#8b5cf6" },
];

function StatCard({ title, value, change, icon: Icon, color }: { title: string; value: string; change: number; icon: React.ElementType; color: string }) {
  return (
    <Card variant="bordered" padding="md">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{value}</p>
          <div className={cn("flex items-center gap-1 mt-1 text-sm", change >= 0 ? "text-green-600" : "text-red-600")}>
            {change >= 0 ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
            <span>{Math.abs(change)}% from last month</span>
          </div>
        </div>
        <div className={cn("p-3 rounded-lg text-white", color)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </Card>
  );
}

function BarChart({ data, title }: { data: { label: string; value: number }[]; title: string }) {
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <Card variant="bordered" padding="md">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">{title}</h3>
      <div className="space-y-3">
        {data.map((item) => (
          <div key={item.label} className="flex items-center gap-3">
            <span className="text-xs text-gray-500 dark:text-gray-400 w-16 truncate">{item.label}</span>
            <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-primary-500 rounded-full transition-all duration-500" style={{ width: `${(item.value / max) * 100}%` }} />
            </div>
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300 w-10 text-right">{item.value}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

function DonutChart({ data, title }: { data: { label: string; value: number; color: string }[]; title: string }) {
  const total = data.reduce((sum, d) => sum + d.value, 0) || 1;
  let cumulative = 0;
  return (
    <Card variant="bordered" padding="md">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">{title}</h3>
      <div className="flex items-center gap-6">
        <div className="relative w-32 h-32">
          <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
            {data.map((item, i) => {
              const percentage = (item.value / total) * 100;
              const offset = cumulative;
              cumulative += percentage;
              return (
                <circle key={i} cx="18" cy="18" r="15.915" fill="none" stroke={item.color} strokeWidth="3" strokeDasharray={`${percentage} ${100 - percentage}`} strokeDashoffset={-offset} className="transition-all duration-500" />
              );
            })}
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg font-bold text-gray-900 dark:text-gray-100">{total}</span>
          </div>
        </div>
        <div className="flex-1 space-y-2">
          {data.map((item, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="text-xs text-gray-600 dark:text-gray-400 flex-1">{item.label}</span>
              <span className="text-xs font-medium text-gray-900 dark:text-gray-100">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

export default function AnalyticsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Analytics</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Recruitment metrics and insights</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" leftIcon={<Filter className="h-4 w-4" />}>Filter</Button>
          <Button variant="outline" leftIcon={<Download className="h-4 w-4" />}>Export</Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BarChart title="Applications by Month" data={applicationsByMonth.map((m) => ({ label: m.month, value: m.count }))} />
        <DonutChart title="Candidates by Status" data={candidatesByStatus.map((s) => ({ label: s.status, value: s.count, color: s.color }))} />
        <BarChart title="Jobs by Department" data={jobsByDepartment.map((d) => ({ label: d.department, value: d.count }))} />
        <DonutChart title="Application Sources" data={sourceBreakdown.map((s) => ({ label: s.source, value: s.count, color: s.color }))} />
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card variant="bordered" padding="md">
          <p className="text-sm text-gray-500 dark:text-gray-400">Hire Rate</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">23.5%</p>
          <p className="text-xs text-green-600 mt-1">+2.3% from last quarter</p>
        </Card>
        <Card variant="bordered" padding="md">
          <p className="text-sm text-gray-500 dark:text-gray-400">Avg. Time to Hire</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">28 days</p>
          <p className="text-xs text-green-600 mt-1">-3 days from last quarter</p>
        </Card>
        <Card variant="bordered" padding="md">
          <p className="text-sm text-gray-500 dark:text-gray-400">Offer Acceptance</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">87%</p>
          <p className="text-xs text-green-600 mt-1">+5% from last quarter</p>
        </Card>
      </div>
    </div>
  );
}
