"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Badge } from "@/components/Badge";
import { Avatar } from "@/components/Avatar";
import { Modal } from "@/components/Modal";
import { Skeleton } from "@/components/Skeleton";
import { cn, formatDate, getInitials } from "@/lib/utils";
import { Search, Filter, Plus, Mail, Phone, MapPin, Briefcase, Star, MoreVertical, Edit, Trash2, Eye } from "lucide-react";

const mockCandidates = [
  { id: "1", name: "Sarah Johnson", email: "sarah@example.com", phone: "+1 234 567 890", location: "New York, NY", role: "Frontend Developer", status: "interview", skills: ["React", "TypeScript", "Node.js"], experience: 5, rating: 4, appliedDate: "2024-01-15", jobId: "1" },
  { id: "2", name: "Michael Chen", email: "michael@example.com", phone: "+1 234 567 891", location: "San Francisco, CA", role: "Backend Developer", status: "screening", skills: ["Python", "Django", "PostgreSQL"], experience: 7, rating: 5, appliedDate: "2024-01-14", jobId: "2" },
  { id: "3", name: "Emily Davis", email: "emily@example.com", phone: "+1 234 567 892", location: "Austin, TX", role: "Product Manager", status: "new", skills: ["Strategy", "Agile", "Analytics"], experience: 4, rating: 3, appliedDate: "2024-01-13", jobId: "3" },
  { id: "4", name: "James Wilson", email: "james@example.com", phone: "+1 234 567 893", location: "Seattle, WA", role: "DevOps Engineer", status: "offer", skills: ["AWS", "Docker", "Kubernetes"], experience: 6, rating: 5, appliedDate: "2024-01-12", jobId: "4" },
  { id: "5", name: "Lisa Anderson", email: "lisa@example.com", phone: "+1 234 567 894", location: "Chicago, IL", role: "UX Designer", status: "hired", skills: ["Figma", "Sketch", "Prototyping"], experience: 3, rating: 4, appliedDate: "2024-01-11", jobId: "5" },
  { id: "6", name: "David Brown", email: "david@example.com", phone: "+1 234 567 895", location: "Boston, MA", role: "Data Scientist", status: "rejected", skills: ["Python", "ML", "TensorFlow"], experience: 8, rating: 2, appliedDate: "2024-01-10", jobId: "6" },
];

const statusColors: Record<string, { variant: "success" | "info" | "warning" | "error" | "default"; label: string }> = {
  new: { variant: "info", label: "New" },
  screening: { variant: "warning", label: "Screening" },
  interview: { variant: "default", label: "Interview" },
  offer: { variant: "success", label: "Offer" },
  hired: { variant: "success", label: "Hired" },
  rejected: { variant: "error", label: "Rejected" },
};

export default function CandidatesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showModal, setShowModal] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<typeof mockCandidates[0] | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  const filtered = mockCandidates.filter((c) => {
    const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) || c.email.toLowerCase().includes(search.toLowerCase()) || c.role.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Candidates</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage your candidate pipeline</p>
        </div>
        <Button onClick={() => setShowAddModal(true)} leftIcon={<Plus className="h-4 w-4" />}>
          Add Candidate
        </Button>
      </div>

      {/* Filters */}
      <Card padding="md">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search candidates..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="pl-10 pr-8 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none"
            >
              <option value="all">All Status</option>
              <option value="new">New</option>
              <option value="screening">Screening</option>
              <option value="interview">Interview</option>
              <option value="offer">Offer</option>
              <option value="hired">Hired</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Results count */}
      <p className="text-sm text-gray-500 dark:text-gray-400">{filtered.length} candidates found</p>

      {/* Candidates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((candidate) => {
          const status = statusColors[candidate.status];
          return (
            <Card key={candidate.id} variant="bordered" padding="md" className="hover:shadow-md transition-shadow">
              <div className="flex items-start gap-3">
                <Avatar alt={candidate.name} fallback={getInitials(candidate.name)} size="lg" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{candidate.name}</h3>
                    <Badge variant={status.variant} size="sm">{status.label}</Badge>
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{candidate.role}</p>
                  <div className="space-y-1 text-xs text-gray-500 dark:text-gray-400">
                    <div className="flex items-center gap-1"><Mail className="h-3 w-3" />{candidate.email}</div>
                    <div className="flex items-center gap-1"><Phone className="h-3 w-3" />{candidate.phone}</div>
                    <div className="flex items-center gap-1"><MapPin className="h-3 w-3" />{candidate.location}</div>
                    <div className="flex items-center gap-1"><Briefcase className="h-3 w-3" />{candidate.experience} years</div>
                  </div>
                </div>
                <div className="flex items-center gap-0.5">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star key={i} className={cn("h-3.5 w-3.5", i < candidate.rating ? "text-yellow-400 fill-yellow-400" : "text-gray-300 dark:text-gray-600")} />
                  ))}
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {candidate.skills.map((skill) => (
                  <Badge key={skill} variant="outline" size="sm">{skill}</Badge>
                ))}
              </div>
              <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <span className="text-xs text-gray-400 dark:text-gray-500">Applied {formatDate(candidate.appliedDate)}</span>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => setSelectedCandidate(candidate)}>
                    <Eye className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Edit className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Trash2 className="h-3.5 w-3.5 text-red-500" />
                  </Button>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <Card>
          <div className="py-12 text-center">
            <Users className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">No candidates found</p>
          </div>
        </Card>
      )}

      {/* View Candidate Modal */}
      <Modal isOpen={!!selectedCandidate} onClose={() => setSelectedCandidate(null)} title="Candidate Details" size="lg">
        {selectedCandidate && (
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <Avatar alt={selectedCandidate.name} fallback={getInitials(selectedCandidate.name)} size="xl" />
              <div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{selectedCandidate.name}</h3>
                <p className="text-gray-500 dark:text-gray-400">{selectedCandidate.role}</p>
                <Badge variant={statusColors[selectedCandidate.status].variant} size="sm">{statusColors[selectedCandidate.status].label}</Badge>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Email</p><p className="font-medium">{selectedCandidate.email}</p></div>
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Phone</p><p className="font-medium">{selectedCandidate.phone}</p></div>
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Location</p><p className="font-medium">{selectedCandidate.location}</p></div>
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Experience</p><p className="font-medium">{selectedCandidate.experience} years</p></div>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Skills</p>
              <div className="flex flex-wrap gap-2">
                {selectedCandidate.skills.map((skill) => (
                  <Badge key={skill} variant="outline">{skill}</Badge>
                ))}
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setSelectedCandidate(null)}>Close</Button>
              <Button>Schedule Interview</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Add Candidate Modal */}
      <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Add New Candidate" size="lg">
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); setShowAddModal(false); }}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Full Name" placeholder="John Doe" required />
            <Input label="Email" type="email" placeholder="john@example.com" required />
            <Input label="Phone" type="tel" placeholder="+1 234 567 890" />
            <Input label="Location" placeholder="New York, NY" />
            <Input label="Role" placeholder="Frontend Developer" required />
            <Input label="Experience (years)" type="number" placeholder="5" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Skills</label>
            <input type="text" placeholder="React, TypeScript, Node.js" className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowAddModal(false)}>Cancel</Button>
            <Button type="submit">Add Candidate</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

function Users(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
