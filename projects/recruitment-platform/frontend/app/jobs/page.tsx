'use client';

import React, { useState, useMemo, useCallback } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Job {
  id: string;
  title: string;
  department: string;
  location: string;
  type: 'full-time' | 'part-time' | 'contract' | 'internship';
  salary: { min: number; max: number; currency: string };
  description: string;
  requirements: string[];
  postedAt: string;
  status: 'open' | 'closed' | 'draft';
  applicants: number;
}

interface JobFormData {
  title: string;
  department: string;
  location: string;
  type: Job['type'];
  salaryMin: string;
  salaryMax: string;
  description: string;
  requirements: string;
}

interface FilterState {
  search: string;
  department: string;
  location: string;
  type: string;
  status: string;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_JOBS: Job[] = [
  {
    id: '1',
    title: 'Senior Frontend Engineer',
    department: 'Engineering',
    location: 'Remote',
    type: 'full-time',
    salary: { min: 120000, max: 160000, currency: 'USD' },
    description: 'Build and maintain our recruitment platform frontend using React, Next.js, and TypeScript.',
    requirements: ['5+ years React experience', 'TypeScript proficiency', 'Next.js experience', 'Tailwind CSS'],
    postedAt: '2026-09-15',
    status: 'open',
    applicants: 24,
  },
  {
    id: '2',
    title: 'Backend Developer',
    department: 'Engineering',
    location: 'Cairo, Egypt',
    type: 'full-time',
    salary: { min: 80000, max: 110000, currency: 'USD' },
    description: 'Design and implement scalable APIs and microservices for the recruitment platform.',
    requirements: ['Node.js / Python', 'PostgreSQL', 'REST & GraphQL', 'Docker'],
    postedAt: '2026-09-18',
    status: 'open',
    applicants: 18,
  },
  {
    id: '3',
    title: 'UX Designer',
    department: 'Design',
    location: 'Remote',
    type: 'contract',
    salary: { min: 60000, max: 85000, currency: 'USD' },
    description: 'Create intuitive and accessible user experiences for recruiters and candidates.',
    requirements: ['Figma', 'User research', 'Design systems', 'Prototyping'],
    postedAt: '2026-09-20',
    status: 'open',
    applicants: 12,
  },
  {
    id: '4',
    title: 'HR Coordinator',
    department: 'Human Resources',
    location: 'Dubai, UAE',
    type: 'full-time',
    salary: { min: 45000, max: 60000, currency: 'USD' },
    description: 'Support recruitment operations, onboarding, and employee relations.',
    requirements: ['HR degree', '2+ years experience', 'Communication skills', 'HRIS tools'],
    postedAt: '2026-09-22',
    status: 'open',
    applicants: 31,
  },
  {
    id: '5',
    title: 'Data Analyst',
    department: 'Analytics',
    location: 'Riyadh, Saudi Arabia',
    type: 'full-time',
    salary: { min: 70000, max: 95000, currency: 'USD' },
    description: 'Analyze recruitment metrics and build dashboards for stakeholders.',
    requirements: ['SQL', 'Python / R', 'Tableau / Power BI', 'Statistics'],
    postedAt: '2026-09-25',
    status: 'open',
    applicants: 9,
  },
  {
    id: '6',
    title: 'DevOps Engineer',
    department: 'Engineering',
    location: 'Remote',
    type: 'full-time',
    salary: { min: 100000, max: 140000, currency: 'USD' },
    description: 'Manage CI/CD pipelines, cloud infrastructure, and monitoring.',
    requirements: ['AWS / GCP', 'Kubernetes', 'Terraform', 'CI/CD'],
    postedAt: '2026-09-28',
    status: 'open',
    applicants: 15,
  },
  {
    id: '7',
    title: 'Marketing Specialist',
    department: 'Marketing',
    location: 'Cairo, Egypt',
    type: 'part-time',
    salary: { min: 30000, max: 45000, currency: 'USD' },
    description: 'Drive employer branding and recruitment marketing campaigns.',
    requirements: ['Digital marketing', 'Content creation', 'Social media', 'Analytics'],
    postedAt: '2026-10-01',
    status: 'open',
    applicants: 7,
  },
  {
    id: '8',
    title: 'QA Engineer',
    department: 'Engineering',
    location: 'Remote',
    type: 'contract',
    salary: { min: 55000, max: 75000, currency: 'USD' },
    description: 'Ensure product quality through automated and manual testing.',
    requirements: ['Test automation', 'Cypress / Playwright', 'API testing', 'Agile'],
    postedAt: '2026-10-02',
    status: 'open',
    applicants: 11,
  },
  {
    id: '9',
    title: 'Product Manager',
    department: 'Product',
    location: 'Dubai, UAE',
    type: 'full-time',
    salary: { min: 110000, max: 150000, currency: 'USD' },
    description: 'Lead product strategy and roadmap for the recruitment platform.',
    requirements: ['5+ years PM', 'B2B SaaS', 'Agile / Scrum', 'Data-driven'],
    postedAt: '2026-10-03',
    status: 'open',
    applicants: 20,
  },
  {
    id: '10',
    title: 'Intern – Software Engineering',
    department: 'Engineering',
    location: 'Cairo, Egypt',
    type: 'internship',
    salary: { min: 10000, max: 15000, currency: 'USD' },
    description: 'Summer internship program for aspiring software engineers.',
    requirements: ['CS student', 'Basic programming', 'Eagerness to learn', 'Team player'],
    postedAt: '2026-10-03',
    status: 'open',
    applicants: 45,
  },
  {
    id: '11',
    title: 'Recruitment Consultant',
    department: 'Human Resources',
    location: 'Riyadh, Saudi Arabia',
    type: 'full-time',
    salary: { min: 50000, max: 70000, currency: 'USD' },
    description: 'Manage end-to-end recruitment for enterprise clients.',
    requirements: ['3+ years recruiting', 'Client management', 'Sourcing strategies', 'Negotiation'],
    postedAt: '2026-09-10',
    status: 'closed',
    applicants: 38,
  },
  {
    id: '12',
    title: 'Mobile Developer',
    department: 'Engineering',
    location: 'Remote',
    type: 'full-time',
    salary: { min: 90000, max: 130000, currency: 'USD' },
    description: 'Build cross-platform mobile apps for candidates and recruiters.',
    requirements: ['React Native / Flutter', 'iOS & Android', 'API integration', 'App Store deployment'],
    postedAt: '2026-09-05',
    status: 'closed',
    applicants: 22,
  },
];

const JOBS_PER_PAGE = 6;

// ─── Utility ─────────────────────────────────────────────────────────────────

function formatSalary(salary: Job['salary']): string {
  return `$${(salary.min / 1000).toFixed(0)}k – $${(salary.max / 1000).toFixed(0)}k`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

// ─── Components ──────────────────────────────────────────────────────────────

// Pagination Component
function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  const pages = useMemo(() => {
    const items: (number | string)[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) items.push(i);
    } else {
      items.push(1);
      if (currentPage > 3) items.push('…');
      for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
        items.push(i);
      }
      if (currentPage < totalPages - 2) items.push('…');
      items.push(totalPages);
    }
    return items;
  }, [currentPage, totalPages]);

  return (
    <nav className="flex items-center justify-center gap-1 mt-8" aria-label="Pagination">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Previous
      </button>
      {pages.map((page, idx) =>
        typeof page === 'string' ? (
          <span key={`ellipsis-${idx}`} className="px-3 py-2 text-sm text-gray-500">
            …
          </span>
        ) : (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              page === currentPage
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {page}
          </button>
        )
      )}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Next
      </button>
    </nav>
  );
}

// Job Card Component
function JobCard({ job, onView }: { job: Job; onView: (job: Job) => void }) {
  const statusColors: Record<Job['status'], string> = {
    open: 'bg-green-100 text-green-800',
    closed: 'bg-red-100 text-red-800',
    draft: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg hover:border-blue-300 transition-all duration-200 cursor-pointer group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors truncate">
            {job.title}
          </h3>
          <p className="text-sm text-gray-500 mt-1">{job.department}</p>
        </div>
        <span className={`ml-3 px-2.5 py-0.5 text-xs font-medium rounded-full whitespace-nowrap ${statusColors[job.status]}`}>
          {job.status}
        </span>
      </div>
      <div className="flex flex-wrap gap-2 mb-4">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
          {job.type}
        </span>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-700">
          {job.location}
        </span>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700">
          {formatSalary(job.salary)}
        </span>
      </div>
      <p className="text-sm text-gray-600 line-clamp-2 mb-4">{job.description}</p>
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">Posted {formatDate(job.postedAt)}</span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">{job.applicants} applicants</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onView(job);
            }}
            className="text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
          >
            View Details →
          </button>
        </div>
      </div>
    </div>
  );
}

// Job Detail Modal Component
function JobDetailModal({ job, onClose }: { job: Job; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-xl font-bold text-gray-900">{job.title}</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="px-6 py-5 space-y-6">
          <div className="flex flex-wrap gap-2">
            <span className="px-3 py-1 text-sm font-medium bg-blue-50 text-blue-700 rounded-full">{job.department}</span>
            <span className="px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full">{job.location}</span>
            <span className="px-3 py-1 text-sm font-medium bg-amber-50 text-amber-700 rounded-full">{formatSalary(job.salary)}</span>
            <span className="px-3 py-1 text-sm font-medium bg-green-50 text-green-700 rounded-full">{job.type}</span>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-2">Description</h3>
            <p className="text-gray-600 leading-relaxed">{job.description}</p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-2">Requirements</h3>
            <ul className="space-y-2">
              {job.requirements.map((req, idx) => (
                <li key={idx} className="flex items-start gap-2 text-gray-600">
                  <svg className="w-5 h-5 text-blue-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {req}
                </li>
              ))}
            </ul>
          </div>
          <div className="flex items-center justify-between pt-4 border-t border-gray-100">
            <div className="text-sm text-gray-500">
              <span className="font-medium text-gray-700">{job.applicants}</span> applicants · Posted{' '}
              {formatDate(job.postedAt)}
            </div>
            <button className="px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
              Apply Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Create Job Form Component
function CreateJobForm({
  onClose,
  onSubmit,
}: {
  onClose: () => void;
  onSubmit: (data: JobFormData) => void;
}) {
  const [formData, setFormData] = useState<JobFormData>({
    title: '',
    department: '',
    location: '',
    type: 'full-time',
    salaryMin: '',
    salaryMax: '',
    description: '',
    requirements: '',
  });

  const [errors, setErrors] = useState<Partial<Record<keyof JobFormData, string>>>({});

  const validate = useCallback((): boolean => {
    const newErrors: Partial<Record<keyof JobFormData, string>> = {};
    if (!formData.title.trim()) newErrors.title = 'Title is required';
    if (!formData.department.trim()) newErrors.department = 'Department is required';
    if (!formData.location.trim()) newErrors.location = 'Location is required';
    if (!formData.salaryMin || Number(formData.salaryMin) <= 0) newErrors.salaryMin = 'Valid minimum salary is required';
    if (!formData.salaryMax || Number(formData.salaryMax) <= 0) newErrors.salaryMax = 'Valid maximum salary is required';
    if (Number(formData.salaryMin) >= Number(formData.salaryMax)) newErrors.salaryMax = 'Max must exceed min';
    if (!formData.description.trim()) newErrors.description = 'Description is required';
    if (!formData.requirements.trim()) newErrors.requirements = 'At least one requirement is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  const inputClass = (field: keyof JobFormData) =>
    `w-full px-4 py-2.5 border rounded-lg text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
      errors[field] ? 'border-red-300 bg-red-50' : 'border-gray-300 bg-white'
    }`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-xl font-bold text-gray-900">Create New Job</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Job Title *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className={inputClass('title')}
                placeholder="e.g. Senior Frontend Engineer"
              />
              {errors.title && <p className="mt-1 text-xs text-red-600">{errors.title}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Department *</label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className={inputClass('department')}
                placeholder="e.g. Engineering"
              />
              {errors.department && <p className="mt-1 text-xs text-red-600">{errors.department}</p>}
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Location *</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className={inputClass('location')}
                placeholder="e.g. Remote, Cairo, Dubai"
              />
              {errors.location && <p className="mt-1 text-xs text-red-600">{errors.location}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Job Type *</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value as Job['type'] })}
                className={inputClass('type')}
              >
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Min Salary (USD) *</label>
              <input
                type="number"
                value={formData.salaryMin}
                onChange={(e) => setFormData({ ...formData, salaryMin: e.target.value })}
                className={inputClass('salaryMin')}
                placeholder="50000"
              />
              {errors.salaryMin && <p className="mt-1 text-xs text-red-600">{errors.salaryMin}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Salary (USD) *</label>
              <input
                type="number"
                value={formData.salaryMax}
                onChange={(e) => setFormData({ ...formData, salaryMax: e.target.value })}
                className={inputClass('salaryMax')}
                placeholder="80000"
              />
              {errors.salaryMax && <p className="mt-1 text-xs text-red-600">{errors.salaryMax}</p>}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className={inputClass('description')}
              placeholder="Describe the role, responsibilities, and impact..."
            />
            {errors.description && <p className="mt-1 text-xs text-red-600">{errors.description}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Requirements * <span className="text-gray-400 font-normal">(one per line)</span>
            </label>
            <textarea
              value={formData.requirements}
              onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
              rows={4}
              className={inputClass('requirements')}
              placeholder="5+ years React experience&#10;TypeScript proficiency&#10;Next.js experience"
            />
            {errors.requirements && <p className="mt-1 text-xs text-red-600">{errors.requirements}</p>}
          </div>
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Job
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Main Page Component ─────────────────────────────────────────────────────

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>(MOCK_JOBS);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    department: '',
    location: '',
    type: '',
    status: '',
  });

  // Derived filter options
  const departments = useMemo(() => [...new Set(jobs.map((j) => j.department))], [jobs]);
  const locations = useMemo(() => [...new Set(jobs.map((j) => j.location))], [jobs]);

  // Filtered jobs
  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      const searchLower = filters.search.toLowerCase();
      const matchesSearch =
        !searchLower ||
        job.title.toLowerCase().includes(searchLower) ||
        job.description.toLowerCase().includes(searchLower) ||
        job.department.toLowerCase().includes(searchLower);
      const matchesDepartment = !filters.department || job.department === filters.department;
      const matchesLocation = !filters.location || job.location === filters.location;
      const matchesType = !filters.type || job.type === filters.type;
      const matchesStatus = !filters.status || job.status === filters.status;
      return matchesSearch && matchesDepartment && matchesLocation && matchesType && matchesStatus;
    });
  }, [jobs, filters]);

  // Pagination
  const totalPages = Math.ceil(filteredJobs.length / JOBS_PER_PAGE);
  const paginatedJobs = useMemo(() => {
    const start = (currentPage - 1) * JOBS_PER_PAGE;
    return filteredJobs.slice(start, start + JOBS_PER_PAGE);
  }, [filteredJobs, currentPage]);

  // Reset to page 1 when filters change
  const updateFilters = useCallback((updates: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...updates }));
    setCurrentPage(1);
  }, []);

  const handleCreateJob = useCallback(
    (formData: JobFormData) => {
      const newJob: Job = {
        id: String(Date.now()),
        title: formData.title,
        department: formData.department,
        location: formData.location,
        type: formData.type,
        salary: { min: Number(formData.salaryMin), max: Number(formData.salaryMax), currency: 'USD' },
        description: formData.description,
        requirements: formData.requirements.split('\n').map((r) => r.trim()).filter(Boolean),
        postedAt: new Date().toISOString().split('T')[0],
        status: 'open',
        applicants: 0,
      };
      setJobs((prev) => [newJob, ...prev]);
      setShowCreateForm(false);
    },
    []
  );

  const clearFilters = useCallback(() => {
    setFilters({ search: '', department: '', location: '', type: '', status: '' });
    setCurrentPage(1);
  }, []);

  const hasActiveFilters = filters.search || filters.department || filters.location || filters.type || filters.status;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
            <p className="text-sm text-gray-500 mt-0.5">{filteredJobs.length} positions found</p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span className="hidden sm:inline">Post a Job</span>
            <span className="sm:hidden">Post</span>
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Search & Filter Bar */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 space-y-4">
          {/* Search Input */}
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => updateFilters({ search: e.target.value })}
              placeholder="Search by title, description, or department..."
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            />
          </div>
          {/* Filter Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <select
              value={filters.department}
              onChange={(e) => updateFilters({ department: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            <select
              value={filters.location}
              onChange={(e) => updateFilters({ location: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">All Locations</option>
              {locations.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
            <select
              value={filters.type}
              onChange={(e) => updateFilters({ type: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">All Types</option>
              <option value="full-time">Full-time</option>
              <option value="part-time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
            </select>
            <select
              value={filters.status}
              onChange={(e) => updateFilters({ status: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="closed">Closed</option>
              <option value="draft">Draft</option>
            </select>
          </div>
          {hasActiveFilters && (
            <div className="flex justify-end">
              <button
                onClick={clearFilters}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                Clear all filters
              </button>
            </div>
          )}
        </div>

        {/* Job List */}
        {paginatedJobs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {paginatedJobs.map((job) => (
              <JobCard key={job.id} job={job} onView={setSelectedJob} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <svg
              className="mx-auto w-12 h-12 text-gray-300 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No jobs found</h3>
            <p className="text-sm text-gray-500">Try adjusting your search or filter criteria.</p>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
        )}
      </main>

      {/* Job Detail Modal */}
      {selectedJob && <JobDetailModal job={selectedJob} onClose={() => setSelectedJob(null)} />}

      {/* Create Job Form Modal */}
      {showCreateForm && (
        <CreateJobForm onClose={() => setShowCreateForm(false)} onSubmit={handleCreateJob} />
      )}
    </div>
  );
}
