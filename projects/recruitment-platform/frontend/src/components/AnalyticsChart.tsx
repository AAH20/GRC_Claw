"use client";

import React from "react";
import { AnalyticsData } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "./Card";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Users, Briefcase, FileText, Calendar } from "lucide-react";

interface AnalyticsChartProps {
  data: AnalyticsData;
  isLoading?: boolean;
}

function StatCard({ title, value, change, changeType, icon }: {
  title: string;
  value: string | number;
  change?: number;
  changeType?: "positive" | "negative";
  icon: React.ReactNode;
}) {
  return (
    <Card variant="bordered" padding="md">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{value}</p>
          {change !== undefined && (
            <div className={cn("flex items-center gap-1 mt-1 text-sm", changeType === "positive" ? "text-green-600" : "text-red-600")}>
              {changeType === "positive" ? <TrendingUp className="h-3.5 w-3.5" aria-hidden="true" /> : <TrendingDown className="h-3.5 w-3.5" aria-hidden="true" />}
              <span>{Math.abs(change)}% from last month</span>
            </div>
          )}
        </div>
        <div className="p-3 rounded-lg bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400">
          {icon}
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
      <div className="space-y-3" role="img" aria-label={`Bar chart: ${title}`}>
        {data.map((item) => (
          <div key={item.label} className="flex items-center gap-3">
            <span className="text-xs text-gray-500 dark:text-gray-400 w-20 truncate">{item.label}</span>
            <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 rounded-full transition-all duration-500"
                style={{ width: `${(item.value / max) * 100}%` }}
              />
            </div>
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300 w-8 text-right">{item.value}</span>
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
          <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90" role="img" aria-label={`Donut chart: ${title}`}>
            {data.map((item, i) => {
              const percentage = (item.value / total) * 100;
              const offset = cumulative;
              cumulative += percentage;
              return (
                <circle
                  key={i}
                  cx="18"
                  cy="18"
                  r="15.915"
                  fill="none"
                  stroke={item.color}
                  strokeWidth="3"
                  strokeDasharray={`${percentage} ${100 - percentage}`}
                  strokeDashoffset={-offset}
                  className="transition-all duration-500"
                />
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
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} aria-hidden="true" />
              <span className="text-xs text-gray-600 dark:text-gray-400 flex-1">{item.label}</span>
              <span className="text-xs font-medium text-gray-900 dark:text-gray-100">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

export function AnalyticsChart({ data, isLoading = false }: AnalyticsChartProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" aria-hidden="true">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  const statusColors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];
  const deptColors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];
  const sourceColors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Candidates" value={data.totalCandidates} change={12} changeType="positive" icon={<Users className="h-5 w-5" aria-hidden="true" />} />
        <StatCard title="Open Jobs" value={data.totalJobs} change={8} changeType="positive" icon={<Briefcase className="h-5 w-5" aria-hidden="true" />} />
        <StatCard title="Applications" value={data.totalApplications} change={-3} changeType="negative" icon={<FileText className="h-5 w-5" aria-hidden="true" />} />
        <StatCard title="Interviews" value={data.totalInterviews} change={15} changeType="positive" icon={<Calendar className="h-5 w-5" aria-hidden="true" />} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BarChart
          title="Applications by Month"
          data={data.applicationsByMonth.map((m) => ({ label: m.month, value: m.count }))}
        />
        <DonutChart
          title="Candidates by Status"
          data={data.candidatesByStatus.map((s, i) => ({ label: s.status, value: s.count, color: statusColors[i % statusColors.length] }))}
        />
        <BarChart
          title="Jobs by Department"
          data={data.jobsByDepartment.map((d) => ({ label: d.department, value: d.count }))}
        />
        <DonutChart
          title="Application Sources"
          data={data.sourceBreakdown.map((s, i) => ({ label: s.source, value: s.count, color: sourceColors[i % sourceColors.length] }))}
        />
      </div>
    </div>
  );
}
