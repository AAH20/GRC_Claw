"use client";

import React, { useState } from "react";
import { Application } from "@/lib/types";
import { Card } from "./Card";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { Avatar } from "./Avatar";
import { cn, formatDate, getInitials } from "@/lib/utils";
import { ChevronLeft, ChevronRight, Search, Filter } from "lucide-react";

interface ApplicationTableProps {
  applications: Application[];
  isLoading?: boolean;
  onView?: (application: Application) => void;
  onStatusChange?: (id: string, status: Application["status"]) => void;
  pageSize?: number;
}

const statusColors: Record<Application["status"], { variant: "success" | "info" | "warning" | "error" | "default"; label: string }> = {
  pending: { variant: "warning", label: "Pending" },
  reviewing: { variant: "info", label: "Reviewing" },
  shortlisted: { variant: "default", label: "Shortlisted" },
  rejected: { variant: "error", label: "Rejected" },
  hired: { variant: "success", label: "Hired" },
};

export function ApplicationTable({
  applications,
  isLoading = false,
  onView,
  onStatusChange,
  pageSize = 10,
}: ApplicationTableProps) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const filtered = applications.filter((app) => {
    const matchesSearch =
      app.candidateName.toLowerCase().includes(search.toLowerCase()) ||
      app.jobTitle.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || app.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalPages = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  if (isLoading) {
    return (
      <Card>
        <div className="animate-pulse space-y-4" aria-hidden="true">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card padding="none">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
            <input
              type="text"
              placeholder="Search applications..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-10 pr-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
              aria-label="Search applications"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" aria-hidden="true" />
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="pl-10 pr-8 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 appearance-none"
              aria-label="Filter by status"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="reviewing">Reviewing</option>
              <option value="shortlisted">Shortlisted</option>
              <option value="rejected">Rejected</option>
              <option value="hired">Hired</option>
            </select>
          </div>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th scope="col" className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Candidate</th>
              <th scope="col" className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Job</th>
              <th scope="col" className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
              <th scope="col" className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Source</th>
              <th scope="col" className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Applied</th>
              <th scope="col" className="text-right py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {paginated.map((app) => {
              const status = statusColors[app.status];
              return (
                <tr key={app.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      <Avatar alt={app.candidateName} fallback={getInitials(app.candidateName)} size="sm" />
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{app.candidateName}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{app.candidateEmail}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-700 dark:text-gray-300">{app.jobTitle}</td>
                  <td className="py-3 px-4">
                    <Badge variant={status.variant} size="sm">{status.label}</Badge>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">{app.source}</td>
                  <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">{formatDate(app.appliedDate)}</td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {onView && <Button variant="ghost" size="sm" onClick={() => onView(app)} aria-label={`View application from ${app.candidateName}`}>View</Button>}
                      {onStatusChange && (
                        <select
                          value={app.status}
                          onChange={(e) => onStatusChange(app.id, e.target.value as Application["status"])}
                          className="text-xs rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2 py-1"
                          aria-label={`Change status for ${app.candidateName}`}
                        >
                          <option value="pending">Pending</option>
                          <option value="reviewing">Reviewing</option>
                          <option value="shortlisted">Shortlisted</option>
                          <option value="rejected">Rejected</option>
                          <option value="hired">Hired</option>
                        </select>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {paginated.length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-500 dark:text-gray-400">
                  No applications found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, filtered.length)} of {filtered.length}
          </p>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} aria-label="Previous page">
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            </Button>
            <span className="text-sm text-gray-700 dark:text-gray-300" aria-live="polite">Page {page} of {totalPages}</span>
            <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} aria-label="Next page">
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}
