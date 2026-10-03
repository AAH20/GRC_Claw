"use client";

import React, { useState } from "react";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Avatar } from "@/components/Avatar";
import { Modal } from "@/components/Modal";
import { cn, formatDate, getInitials } from "@/lib/utils";
import { Search, Filter, ChevronLeft, ChevronRight, Eye, Edit, Trash2, FileText } from "lucide-react";

const mockApplications = [
  { id: "1", candidateId: "1", candidateName: "Sarah Johnson", candidateEmail: "sarah@example.com", jobId: "1", jobTitle: "Senior Frontend Developer", status: "reviewing", appliedDate: "2024-01-15", updatedDate: "2024-01-16", source: "LinkedIn", rating: 4 },
  { id: "2", candidateId: "2", candidateName: "Michael Chen", candidateEmail: "michael@example.com", jobId: "2", jobTitle: "Backend Developer", status: "shortlisted", appliedDate: "2024-01-14", updatedDate: "2024-01-15", source: "Indeed", rating: 5 },
  { id: "3", candidateId: "3", candidateName: "Emily Davis", candidateEmail: "emily@example.com", jobId: "3", jobTitle: "Product Manager", status: "pending", appliedDate: "2024-01-13", updatedDate: "2024-01-13", source: "Referral", rating: 3 },
  { id: "4", candidateId: "4", candidateName: "James Wilson", candidateEmail: "james@example.com", jobId: "4", jobTitle: "DevOps Engineer", status: "hired", appliedDate: "2024-01-12", updatedDate: "2024-01-14", source: "LinkedIn", rating: 5 },
  { id: "5", candidateId: "5", candidateName: "Lisa Anderson", candidateEmail: "lisa@example.com", jobId: "5", jobTitle: "UX Designer", status: "rejected", appliedDate: "2024-01-11", updatedDate: "2024-01-13", source: "Glassdoor", rating: 2 },
  { id: "6", candidateId: "6", candidateName: "David Brown", candidateEmail: "david@example.com", jobId: "6", jobTitle: "Data Scientist", status: "pending", appliedDate: "2024-01-10", updatedDate: "2024-01-10", source: "Indeed", rating: 3 },
  { id: "7", candidateId: "7", candidateName: "Anna Martinez", candidateEmail: "anna@example.com", jobId: "1", jobTitle: "Senior Frontend Developer", status: "reviewing", appliedDate: "2024-01-09", updatedDate: "2024-01-12", source: "LinkedIn", rating: 4 },
  { id: "8", candidateId: "8", candidateName: "Robert Taylor", candidateEmail: "robert@example.com", jobId: "2", jobTitle: "Backend Developer", status: "shortlisted", appliedDate: "2024-01-08", updatedDate: "2024-01-11", source: "Referral", rating: 4 },
];

const statusColors: Record<string, { variant: "success" | "info" | "warning" | "error" | "default"; label: string }> = {
  pending: { variant: "warning", label: "Pending" },
  reviewing: { variant: "info", label: "Reviewing" },
  shortlisted: { variant: "default", label: "Shortlisted" },
  rejected: { variant: "error", label: "Rejected" },
  hired: { variant: "success", label: "Hired" },
};

export default function ApplicationsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [selectedApp, setSelectedApp] = useState<typeof mockApplications[0] | null>(null);
  const pageSize = 5;

  const filtered = mockApplications.filter((app) => {
    const matchesSearch = app.candidateName.toLowerCase().includes(search.toLowerCase()) || app.jobTitle.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || app.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalPages = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Applications</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Track and manage all job applications</p>
      </div>

      {/* Filters */}
      <Card padding="md">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search applications..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-10 pr-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="pl-10 pr-8 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none"
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
      </Card>

      {/* Table */}
      <Card padding="none">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Candidate</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Job</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Source</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Applied</th>
                <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
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
                      <select
                        value={app.status}
                        onChange={() => {}}
                        className={cn(
                          "text-xs rounded-full px-2.5 py-1 font-medium border-0 cursor-pointer",
                          status.variant === "success" && "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
                          status.variant === "info" && "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
                          status.variant === "warning" && "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
                          status.variant === "error" && "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
                          status.variant === "default" && "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                        )}
                      >
                        <option value="pending">Pending</option>
                        <option value="reviewing">Reviewing</option>
                        <option value="shortlisted">Shortlisted</option>
                        <option value="rejected">Rejected</option>
                        <option value="hired">Hired</option>
                      </select>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">{app.source}</td>
                    <td className="py-3 px-4 text-sm text-gray-500 dark:text-gray-400">{formatDate(app.appliedDate)}</td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="sm" onClick={() => setSelectedApp(app)}><Eye className="h-3.5 w-3.5" /></Button>
                        <Button variant="ghost" size="sm"><Edit className="h-3.5 w-3.5" /></Button>
                        <Button variant="ghost" size="sm"><Trash2 className="h-3.5 w-3.5 text-red-500" /></Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, filtered.length)} of {filtered.length}
            </p>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-gray-700 dark:text-gray-300">{page} / {totalPages}</span>
              <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* View Application Modal */}
      <Modal isOpen={!!selectedApp} onClose={() => setSelectedApp(null)} title="Application Details" size="lg">
        {selectedApp && (
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <Avatar alt={selectedApp.candidateName} fallback={getInitials(selectedApp.candidateName)} size="xl" />
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{selectedApp.candidateName}</h3>
                <p className="text-gray-500 dark:text-gray-400">{selectedApp.candidateEmail}</p>
                <Badge variant={statusColors[selectedApp.status].variant} size="sm">{statusColors[selectedApp.status].label}</Badge>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Position</p><p className="font-medium">{selectedApp.jobTitle}</p></div>
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Source</p><p className="font-medium">{selectedApp.source}</p></div>
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Applied Date</p><p className="font-medium">{formatDate(selectedApp.appliedDate)}</p></div>
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Last Updated</p><p className="font-medium">{formatDate(selectedApp.updatedDate)}</p></div>
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setSelectedApp(null)}>Close</Button>
              <Button>Move to Next Stage</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
