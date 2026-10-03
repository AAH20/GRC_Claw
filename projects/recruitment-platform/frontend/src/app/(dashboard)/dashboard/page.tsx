"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Avatar } from "@/components/Avatar";
import { Skeleton } from "@/components/Skeleton";
import { cn, formatDate, getInitials, formatRelativeTime } from "@/lib/utils";
import { Users, Briefcase, FileText, Calendar, TrendingUp, Clock, MapPin, Star } from "lucide-react";
import Link from "next/link";

const stats = [
  { label: "Total Candidates", value: "1,234", change: "+12%", icon: Users, color: "bg-blue-500" },
  { label: "Open Jobs", value: "48", change: "+5%", icon: Briefcase, color: "bg-green-500" },
  { label: "Applications", value: "3,567", change: "+23%", icon: FileText, color: "bg-purple-500" },
  { label: "Interviews", value: "156", change: "+8%", icon: Calendar, color: "bg-orange-500" },
];

const recentCandidates = [
  { id: "1", name: "Sarah Johnson", email: "sarah@example.com", role: "Frontend Developer", status: "interview", rating: 4, appliedDate: "2024-01-15" },
  { id: "2", name: "Michael Chen", email: "michael@example.com", role: "Backend Developer", status: "screening", rating: 5, appliedDate: "2024-01-14" },
  { id: "3", name: "Emily Davis", email: "emily@example.com", role: "Product Manager", status: "new", rating: 3, appliedDate: "2024-01-13" },
  { id: "4", name: "James Wilson", email: "james@example.com", role: "DevOps Engineer", status: "offer", rating: 5, appliedDate: "2024-01-12" },
];

const upcomingInterviews = [
  { id: "1", candidate: "Sarah Johnson", job: "Frontend Developer", date: "2024-01-16", time: "10:00 AM", type: "video" },
  { id: "2", candidate: "Michael Chen", job: "Backend Developer", date: "2024-01-16", time: "2:00 PM", type: "onsite" },
  { id: "3", candidate: "Emily Davis", job: "Product Manager", date: "2024-01-17", time: "11:00 AM", type: "phone" },
];

const statusColors: Record<string, { variant: "success" | "info" | "warning" | "error" | "default"; label: string }> = {
  new: { variant: "info", label: "New" },
  screening: { variant: "warning", label: "Screening" },
  interview: { variant: "default", label: "Interview" },
  offer: { variant: "success", label: "Offer" },
  hired: { variant: "success", label: "Hired" },
  rejected: { variant: "error", label: "Rejected" },
};

export default function DashboardPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Welcome back! Here&apos;s your recruitment overview.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label} variant="bordered" padding="md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-1">{stat.value}</p>
                <div className="flex items-center gap-1 mt-1 text-sm text-green-600">
                  <TrendingUp className="h-3.5 w-3.5" />
                  <span>{stat.change}</span>
                </div>
              </div>
              <div className={cn("p-3 rounded-lg text-white", stat.color)}>
                <stat.icon className="h-5 w-5" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Candidates */}
        <Card padding="none" className="lg:col-span-2">
          <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
            <h2 className="font-semibold text-gray-900 dark:text-gray-100">Recent Candidates</h2>
            <Link href="/candidates">
              <Button variant="ghost" size="sm">View All</Button>
            </Link>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {recentCandidates.map((candidate) => {
              const status = statusColors[candidate.status];
              return (
                <div key={candidate.id} className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <Avatar alt={candidate.name} fallback={getInitials(candidate.name)} size="md" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{candidate.name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{candidate.role}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="hidden sm:flex items-center gap-0.5">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star key={i} className={cn("h-3.5 w-3.5", i < candidate.rating ? "text-yellow-400 fill-yellow-400" : "text-gray-300 dark:text-gray-600")} />
                      ))}
                    </div>
                    <Badge variant={status.variant} size="sm">{status.label}</Badge>
                    <span className="text-xs text-gray-400 dark:text-gray-500">{formatRelativeTime(candidate.appliedDate)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Upcoming Interviews */}
        <Card padding="none">
          <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
            <h2 className="font-semibold text-gray-900 dark:text-gray-100">Upcoming Interviews</h2>
            <Link href="/interviews">
              <Button variant="ghost" size="sm">View All</Button>
            </Link>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {upcomingInterviews.map((interview) => (
              <div key={interview.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <div className="flex items-center gap-3">
                  <Avatar alt={interview.candidate} fallback={getInitials(interview.candidate)} size="sm" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{interview.candidate}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{interview.job}</p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-gray-400 dark:text-gray-500">
                      <Clock className="h-3 w-3" />
                      <span>{interview.date} at {interview.time}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card variant="bordered" padding="md">
        <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Link href="/candidates?action=new">
            <Button variant="outline" className="w-full justify-start" leftIcon={<Users className="h-4 w-4" />}>
              Add Candidate
            </Button>
          </Link>
          <Link href="/jobs?action=new">
            <Button variant="outline" className="w-full justify-start" leftIcon={<Briefcase className="h-4 w-4" />}>
              Post Job
            </Button>
          </Link>
          <Link href="/interviews?action=schedule">
            <Button variant="outline" className="w-full justify-start" leftIcon={<Calendar className="h-4 w-4" />}>
              Schedule Interview
            </Button>
          </Link>
          <Link href="/analytics">
            <Button variant="outline" className="w-full justify-start" leftIcon={<TrendingUp className="h-4 w-4" />}>
              View Reports
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
