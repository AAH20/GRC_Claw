"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Badge } from "@/components/Badge";
import { Modal } from "@/components/Modal";
import { cn, formatCurrency, formatDate } from "@/lib/utils";
import { Search, Filter, Plus, MapPin, Clock, Users, Eye, DollarSign, Edit, Trash2, Briefcase } from "lucide-react";

const mockJobs = [
  { id: "1", title: "Senior Frontend Developer", department: "Engineering", location: "New York, NY", type: "full-time", salary: { min: 120000, max: 160000, currency: "USD" }, description: "We are looking for a Senior Frontend Developer to join our team and help build amazing user experiences.", requirements: ["React", "TypeScript", "Next.js", "Tailwind CSS"], status: "open", postedDate: "2024-01-10", applicants: 45, views: 234 },
  { id: "2", title: "Backend Developer", department: "Engineering", location: "San Francisco, CA", type: "full-time", salary: { min: 130000, max: 170000, currency: "USD" }, description: "Join our backend team to design and implement scalable APIs and services.", requirements: ["Python", "Django", "PostgreSQL", "Redis"], status: "open", postedDate: "2024-01-08", applicants: 32, views: 189 },
  { id: "3", title: "Product Manager", department: "Product", location: "Austin, TX", type: "full-time", salary: { min: 110000, max: 150000, currency: "USD" }, description: "Lead product strategy and roadmap for our core platform.", requirements: ["Strategy", "Agile", "Analytics", "Communication"], status: "open", postedDate: "2024-01-05", applicants: 67, views: 312 },
  { id: "4", title: "DevOps Engineer", department: "Engineering", location: "Seattle, WA", type: "remote", salary: { min: 125000, max: 165000, currency: "USD" }, description: "Help us build and maintain our cloud infrastructure and CI/CD pipelines.", requirements: ["AWS", "Docker", "Kubernetes", "Terraform"], status: "open", postedDate: "2024-01-03", applicants: 28, views: 156 },
  { id: "5", title: "UX Designer", department: "Design", location: "Chicago, IL", type: "full-time", salary: { min: 90000, max: 130000, currency: "USD" }, description: "Create beautiful and intuitive user experiences for our products.", requirements: ["Figma", "Sketch", "Prototyping", "User Research"], status: "on-hold", postedDate: "2023-12-28", applicants: 54, views: 278 },
  { id: "6", title: "Data Scientist", department: "Data", location: "Boston, MA", type: "full-time", salary: { min: 140000, max: 180000, currency: "USD" }, description: "Apply machine learning and statistical analysis to solve complex business problems.", requirements: ["Python", "ML", "TensorFlow", "SQL"], status: "closed", postedDate: "2023-12-20", applicants: 89, views: 445 },
];

const statusColors: Record<string, { variant: "success" | "error" | "warning" | "default"; label: string }> = {
  open: { variant: "success", label: "Open" },
  closed: { variant: "error", label: "Closed" },
  draft: { variant: "default", label: "Draft" },
  "on-hold": { variant: "warning", label: "On Hold" },
};

const typeLabels: Record<string, string> = {
  "full-time": "Full-time",
  "part-time": "Part-time",
  contract: "Contract",
  remote: "Remote",
};

export default function JobsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showModal, setShowModal] = useState(false);
  const [selectedJob, setSelectedJob] = useState<typeof mockJobs[0] | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  const filtered = mockJobs.filter((job) => {
    const matchesSearch = job.title.toLowerCase().includes(search.toLowerCase()) || job.department.toLowerCase().includes(search.toLowerCase()) || job.location.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || job.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Jobs</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage job postings and track applicants</p>
        </div>
        <Button onClick={() => setShowAddModal(true)} leftIcon={<Plus className="h-4 w-4" />}>
          Post New Job
        </Button>
      </div>

      {/* Filters */}
      <Card padding="md">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search jobs..."
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
              <option value="open">Open</option>
              <option value="closed">Closed</option>
              <option value="draft">Draft</option>
              <option value="on-hold">On Hold</option>
            </select>
          </div>
        </div>
      </Card>

      <p className="text-sm text-gray-500 dark:text-gray-400">{filtered.length} jobs found</p>

      {/* Jobs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((job) => {
          const status = statusColors[job.status];
          return (
            <Card key={job.id} variant="bordered" padding="md" className="hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{job.title}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{job.department}</p>
                </div>
                <Badge variant={status.variant} size="sm">{status.label}</Badge>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2 mb-3">{job.description}</p>
              <div className="flex flex-wrap gap-3 text-sm text-gray-500 dark:text-gray-400 mb-3">
                <span className="inline-flex items-center gap-1"><MapPin className="h-4 w-4" />{job.location}</span>
                <span className="inline-flex items-center gap-1"><Clock className="h-4 w-4" />{typeLabels[job.type]}</span>
                <span className="inline-flex items-center gap-1"><DollarSign className="h-4 w-4" />{formatCurrency(job.salary.min)} - {formatCurrency(job.salary.max)}</span>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {job.requirements.slice(0, 3).map((req) => (
                  <Badge key={req} variant="outline" size="sm">{req}</Badge>
                ))}
                {job.requirements.length > 3 && <Badge variant="outline" size="sm">+{job.requirements.length - 3}</Badge>}
              </div>
              <div className="pt-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                  <span className="inline-flex items-center gap-1"><Users className="h-4 w-4" />{job.applicants}</span>
                  <span className="inline-flex items-center gap-1"><Eye className="h-4 w-4" />{job.views}</span>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => setSelectedJob(job)}>
                    <Eye className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm"><Edit className="h-3.5 w-3.5" /></Button>
                  <Button variant="ghost" size="sm"><Trash2 className="h-3.5 w-3.5 text-red-500" /></Button>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <Card>
          <div className="py-12 text-center">
            <Briefcase className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-500 dark:text-gray-400">No jobs found</p>
          </div>
        </Card>
      )}

      {/* View Job Modal */}
      <Modal isOpen={!!selectedJob} onClose={() => setSelectedJob(null)} title="Job Details" size="lg">
        {selectedJob && (
          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">{selectedJob.title}</h3>
              <p className="text-gray-500 dark:text-gray-400">{selectedJob.department}</p>
              <Badge variant={statusColors[selectedJob.status].variant} size="sm">{statusColors[selectedJob.status].label}</Badge>
            </div>
            <p className="text-gray-600 dark:text-gray-300">{selectedJob.description}</p>
            <div className="grid grid-cols-2 gap-4">
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Location</p><p className="font-medium">{selectedJob.location}</p></div>
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Type</p><p className="font-medium">{typeLabels[selectedJob.type]}</p></div>
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Salary</p><p className="font-medium">{formatCurrency(selectedJob.salary.min)} - {formatCurrency(selectedJob.salary.max)}</p></div>
              <div><p className="text-sm text-gray-500 dark:text-gray-400">Posted</p><p className="font-medium">{formatDate(selectedJob.postedDate)}</p></div>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Requirements</p>
              <div className="flex flex-wrap gap-2">
                {selectedJob.requirements.map((req) => (
                  <Badge key={req} variant="outline">{req}</Badge>
                ))}
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setSelectedJob(null)}>Close</Button>
              <Button>View Applicants</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Add Job Modal */}
      <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Post New Job" size="lg">
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); setShowAddModal(false); }}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Job Title" placeholder="Senior Frontend Developer" required />
            <Input label="Department" placeholder="Engineering" required />
            <Input label="Location" placeholder="New York, NY" required />
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Type</label>
              <select className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm">
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="remote">Remote</option>
              </select>
            </div>
            <Input label="Min Salary" type="number" placeholder="120000" />
            <Input label="Max Salary" type="number" placeholder="160000" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Description</label>
            <textarea rows={3} placeholder="Job description..." className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Requirements</label>
            <input type="text" placeholder="React, TypeScript, Node.js" className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowAddModal(false)}>Cancel</Button>
            <Button type="submit">Post Job</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
