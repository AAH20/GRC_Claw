"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Badge } from "@/components/Badge";
import { Modal } from "@/components/Modal";
import { cn, formatCurrency, formatDate } from "@/lib/utils";
import { Search, Filter, Plus, MapPin, Clock, Users, Eye, DollarSign, Edit, Trash2, Briefcase } from "lucide-react";

interface Job {
  id: string;
  title: string;
  department: string;
  location: string;
  type: string;
  salary: { min: number; max: number; currency: string };
  description: string;
  requirements: string[];
  status: string;
  postedDate: string;
  applicants: number;
  views: number;
}

const initialJobs: Job[] = [
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
  const [jobs, setJobs] = useState<Job[]>(initialJobs);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [departmentFilter, setDepartmentFilter] = useState("all");
  const [showModal, setShowModal] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [jobToDelete, setJobToDelete] = useState<Job | null>(null);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const [formData, setFormData] = useState({
    title: "",
    department: "",
    location: "",
    type: "full-time",
    salaryMin: "",
    salaryMax: "",
    description: "",
    requirements: "",
    status: "open",
  });

  const departments = [...new Set(jobs.map((j) => j.department))];

  const filtered = jobs.filter((job) => {
    const matchesSearch = job.title.toLowerCase().includes(search.toLowerCase()) || job.department.toLowerCase().includes(search.toLowerCase()) || job.location.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || job.status === statusFilter;
    const matchesDepartment = departmentFilter === "all" || job.department === departmentFilter;
    return matchesSearch && matchesStatus && matchesDepartment;
  });

  const resetForm = () => {
    setFormData({ title: "", department: "", location: "", type: "full-time", salaryMin: "", salaryMax: "", description: "", requirements: "", status: "open" });
    setFormErrors({});
    setEditingJob(null);
  };

  const openAddModal = () => {
    resetForm();
    setShowAddModal(true);
  };

  const openEditModal = (job: Job) => {
    setFormData({
      title: job.title,
      department: job.department,
      location: job.location,
      type: job.type,
      salaryMin: String(job.salary.min),
      salaryMax: String(job.salary.max),
      description: job.description,
      requirements: job.requirements.join(", "),
      status: job.status,
    });
    setEditingJob(job);
    setShowAddModal(true);
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    if (!formData.title.trim()) errors.title = "Title is required";
    if (!formData.department.trim()) errors.department = "Department is required";
    if (!formData.location.trim()) errors.location = "Location is required";
    if (!formData.description.trim()) errors.description = "Description is required";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    const jobData: Job = {
      id: editingJob ? editingJob.id : String(Date.now()),
      title: formData.title,
      department: formData.department,
      location: formData.location,
      type: formData.type,
      salary: { min: Number(formData.salaryMin) || 0, max: Number(formData.salaryMax) || 0, currency: "USD" },
      description: formData.description,
      requirements: formData.requirements.split(",").map((r) => r.trim()).filter(Boolean),
      status: formData.status,
      postedDate: editingJob ? editingJob.postedDate : new Date().toISOString().split("T")[0],
      applicants: editingJob ? editingJob.applicants : 0,
      views: editingJob ? editingJob.views : 0,
    };

    if (editingJob) {
      setJobs((prev) => prev.map((j) => (j.id === editingJob.id ? jobData : j)));
    } else {
      setJobs((prev) => [jobData, ...prev]);
    }
    setShowAddModal(false);
    resetForm();
  };

  const handleDelete = (job: Job) => {
    setJobToDelete(job);
    setShowDeleteConfirm(true);
  };

  const confirmDelete = () => {
    if (jobToDelete) {
      setJobs((prev) => prev.filter((j) => j.id !== jobToDelete.id));
      if (selectedJob?.id === jobToDelete.id) setSelectedJob(null);
    }
    setShowDeleteConfirm(false);
    setJobToDelete(null);
  };

  const handleStatusChange = (job: Job, newStatus: string) => {
    setJobs((prev) => prev.map((j) => (j.id === job.id ? { ...j, status: newStatus } : j)));
    if (selectedJob?.id === job.id) setSelectedJob({ ...selectedJob, status: newStatus });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Jobs</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage job postings and track applicants</p>
        </div>
        <Button onClick={openAddModal} leftIcon={<Plus className="h-4 w-4" />}>
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
              aria-label="Department"
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="pl-10 pr-8 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none"
            >
              <option value="all">All Departments</option>
              {departments.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div className="relative">
            <select
              aria-label="Status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="pl-4 pr-8 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none"
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
                  <Button variant="ghost" size="sm" onClick={() => openEditModal(job)}>
                    <Edit className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(job)}>
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
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">Applicants</p>
              <p className="font-medium">{selectedJob.applicants} applicants</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Status</label>
              <select
                aria-label="Status"
                value={selectedJob.status}
                onChange={(e) => handleStatusChange(selectedJob, e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm"
              >
                <option value="open">Open</option>
                <option value="closed">Closed</option>
                <option value="draft">Draft</option>
                <option value="on-hold">On Hold</option>
              </select>
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setSelectedJob(null)}>Close</Button>
              <Button onClick={() => { openEditModal(selectedJob); setSelectedJob(null); }}>Edit</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Add/Edit Job Modal */}
      <Modal isOpen={showAddModal} onClose={() => { setShowAddModal(false); resetForm(); }} title={editingJob ? "Edit Job" : "Post New Job"} size="lg">
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="job-title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Title</label>
              <input id="job-title" className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm" value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} required />
              {formErrors.title && <p className="mt-1 text-sm text-red-500">{formErrors.title}</p>}
            </div>
            <div>
              <label htmlFor="job-department" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Department</label>
              <input id="job-department" className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm" value={formData.department} onChange={(e) => setFormData({ ...formData, department: e.target.value })} required />
              {formErrors.department && <p className="mt-1 text-sm text-red-500">{formErrors.department}</p>}
            </div>
            <div>
              <label htmlFor="job-location" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Location</label>
              <input id="job-location" className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm" value={formData.location} onChange={(e) => setFormData({ ...formData, location: e.target.value })} required />
              {formErrors.location && <p className="mt-1 text-sm text-red-500">{formErrors.location}</p>}
            </div>
            <div>
              <label htmlFor="job-type" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Type</label>
              <select id="job-type" className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm" value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value })}>
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="remote">Remote</option>
              </select>
            </div>
            <div>
              <label htmlFor="job-salary-min" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Min Salary</label>
              <input id="job-salary-min" type="number" className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm" value={formData.salaryMin} onChange={(e) => setFormData({ ...formData, salaryMin: e.target.value })} />
            </div>
            <div>
              <label htmlFor="job-salary-max" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Max Salary</label>
              <input id="job-salary-max" type="number" className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm" value={formData.salaryMax} onChange={(e) => setFormData({ ...formData, salaryMax: e.target.value })} />
            </div>
          </div>
          <div>
            <label htmlFor="job-description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Description</label>
            <textarea id="job-description" rows={3} className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} required />
            {formErrors.description && <p className="mt-1 text-sm text-red-500">{formErrors.description}</p>}
          </div>
          <div>
            <label htmlFor="job-requirements" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Requirements (comma-separated)</label>
            <input id="job-requirements" className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm" value={formData.requirements} onChange={(e) => setFormData({ ...formData, requirements: e.target.value })} placeholder="React, TypeScript, Node.js" />
          </div>
          <div>
            <label htmlFor="job-status" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Status</label>
            <select id="job-status" className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm" value={formData.status} onChange={(e) => setFormData({ ...formData, status: e.target.value })}>
              <option value="open">Open</option>
              <option value="closed">Closed</option>
              <option value="draft">Draft</option>
              <option value="on-hold">On Hold</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => { setShowAddModal(false); resetForm(); }}>Cancel</Button>
            <Button type="submit">{editingJob ? "Update Job" : "Post Job"}</Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={showDeleteConfirm} onClose={() => { setShowDeleteConfirm(false); setJobToDelete(null); }} title="Delete Job" size="sm">
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-300">Are you sure you want to delete &quot;{jobToDelete?.title}&quot;? This action cannot be undone.</p>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => { setShowDeleteConfirm(false); setJobToDelete(null); }}>Cancel</Button>
            <Button variant="destructive" onClick={confirmDelete}>Delete</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
