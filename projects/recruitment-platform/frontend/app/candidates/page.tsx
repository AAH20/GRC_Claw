'use client';

import React, { useState, useMemo, useCallback } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Candidate {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  role: string;
  status: 'applied' | 'screening' | 'interview' | 'offer' | 'hired' | 'rejected';
  experience: number;
  skills: string[];
  location: string;
  appliedAt: string;
  avatarUrl?: string;
  notes?: string;
  expectedSalary?: number;
  linkedIn?: string;
}

interface CandidateFormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  role: string;
  experience: number;
  skills: string;
  location: string;
  expectedSalary: number;
  linkedIn: string;
  notes: string;
}

interface FilterState {
  search: string;
  status: Candidate['status'] | 'all';
  role: string;
  location: string;
  minExperience: number;
  maxExperience: number;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const PAGE_SIZE = 10;

const STATUS_LABELS: Record<Candidate['status'], string> = {
  applied: 'Applied',
  screening: 'Screening',
  interview: 'Interview',
  offer: 'Offer',
  hired: 'Hired',
  rejected: 'Rejected',
};

const STATUS_COLORS: Record<Candidate['status'], string> = {
  applied: 'bg-blue-100 text-blue-800',
  screening: 'bg-yellow-100 text-yellow-800',
  interview: 'bg-purple-100 text-purple-800',
  offer: 'bg-green-100 text-green-800',
  hired: 'bg-emerald-100 text-emerald-800',
  rejected: 'bg-red-100 text-red-800',
};

const EMPTY_FORM: CandidateFormData = {
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  role: '',
  experience: 0,
  skills: '',
  location: '',
  expectedSalary: 0,
  linkedIn: '',
  notes: '',
};

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_CANDIDATES: Candidate[] = [
  {
    id: '1',
    firstName: 'Sarah',
    lastName: 'Chen',
    email: 'sarah.chen@email.com',
    phone: '+1-555-0101',
    role: 'Senior Frontend Engineer',
    status: 'interview',
    experience: 7,
    skills: ['React', 'TypeScript', 'Next.js', 'GraphQL'],
    location: 'San Francisco, CA',
    appliedAt: '2026-09-15',
    expectedSalary: 160000,
    linkedIn: 'linkedin.com/in/sarahchen',
    notes: 'Strong portfolio, excellent communication skills.',
  },
  {
    id: '2',
    firstName: 'Marcus',
    lastName: 'Johnson',
    email: 'marcus.j@email.com',
    phone: '+1-555-0102',
    role: 'Backend Engineer',
    status: 'screening',
    experience: 5,
    skills: ['Node.js', 'Python', 'PostgreSQL', 'AWS'],
    location: 'Austin, TX',
    appliedAt: '2026-09-20',
    expectedSalary: 140000,
    linkedIn: 'linkedin.com/in/marcusj',
  },
  {
    id: '3',
    firstName: 'Priya',
    lastName: 'Patel',
    email: 'priya.patel@email.com',
    phone: '+1-555-0103',
    role: 'Product Designer',
    status: 'offer',
    experience: 6,
    skills: ['Figma', 'User Research', 'Prototyping', 'Design Systems'],
    location: 'New York, NY',
    appliedAt: '2026-08-28',
    expectedSalary: 135000,
    linkedIn: 'linkedin.com/in/priyapatel',
    notes: 'Impressive design system work at previous company.',
  },
  {
    id: '4',
    firstName: 'James',
    lastName: 'Rodriguez',
    email: 'j.rodriguez@email.com',
    phone: '+1-555-0104',
    role: 'DevOps Engineer',
    status: 'applied',
    experience: 4,
    skills: ['Docker', 'Kubernetes', 'Terraform', 'CI/CD'],
    location: 'Seattle, WA',
    appliedAt: '2026-10-01',
    expectedSalary: 145000,
  },
  {
    id: '5',
    firstName: 'Emily',
    lastName: 'Watson',
    email: 'emily.w@email.com',
    phone: '+1-555-0105',
    role: 'Data Scientist',
    status: 'hired',
    experience: 8,
    skills: ['Python', 'Machine Learning', 'SQL', 'TensorFlow'],
    location: 'Boston, MA',
    appliedAt: '2026-07-10',
    expectedSalary: 170000,
    linkedIn: 'linkedin.com/in/emilywatson',
  },
  {
    id: '6',
    firstName: 'David',
    lastName: 'Kim',
    email: 'david.kim@email.com',
    phone: '+1-555-0106',
    role: 'Senior Frontend Engineer',
    status: 'rejected',
    experience: 3,
    skills: ['React', 'JavaScript', 'CSS'],
    location: 'Chicago, IL',
    appliedAt: '2026-09-05',
    expectedSalary: 120000,
    notes: 'Not enough senior-level experience for this role.',
  },
  {
    id: '7',
    firstName: 'Aisha',
    lastName: 'Mohammed',
    email: 'aisha.m@email.com',
    phone: '+1-555-0107',
    role: 'Full Stack Developer',
    status: 'interview',
    experience: 6,
    skills: ['React', 'Node.js', 'MongoDB', 'TypeScript'],
    location: 'Denver, CO',
    appliedAt: '2026-09-12',
    expectedSalary: 150000,
    linkedIn: 'linkedin.com/in/aishamohammed',
  },
  {
    id: '8',
    firstName: 'Tom',
    lastName: 'Anderson',
    email: 'tom.a@email.com',
    phone: '+1-555-0108',
    role: 'Backend Engineer',
    status: 'screening',
    experience: 9,
    skills: ['Go', 'Microservices', 'gRPC', 'Redis'],
    location: 'Portland, OR',
    appliedAt: '2026-09-22',
    expectedSalary: 165000,
  },
  {
    id: '9',
    firstName: 'Lisa',
    lastName: 'Park',
    email: 'lisa.park@email.com',
    phone: '+1-555-0109',
    role: 'Product Manager',
    status: 'applied',
    experience: 5,
    skills: ['Product Strategy', 'Agile', 'Analytics', 'User Stories'],
    location: 'Los Angeles, CA',
    appliedAt: '2026-10-02',
    expectedSalary: 155000,
  },
  {
    id: '10',
    firstName: 'Alex',
    lastName: 'Novak',
    email: 'alex.n@email.com',
    phone: '+1-555-0110',
    role: 'DevOps Engineer',
    status: 'interview',
    experience: 7,
    skills: ['AWS', 'Azure', 'Jenkins', 'Ansible'],
    location: 'Miami, FL',
    appliedAt: '2026-09-18',
    expectedSalary: 148000,
    linkedIn: 'linkedin.com/in/alexnovak',
  },
  {
    id: '11',
    firstName: 'Nina',
    lastName: 'Kowalski',
    email: 'nina.k@email.com',
    phone: '+1-555-0111',
    role: 'UX Designer',
    status: 'offer',
    experience: 4,
    skills: ['Sketch', 'Figma', 'Wireframing', 'Usability Testing'],
    location: 'Minneapolis, MN',
    appliedAt: '2026-08-30',
    expectedSalary: 115000,
  },
  {
    id: '12',
    firstName: 'Carlos',
    lastName: 'Mendez',
    email: 'carlos.m@email.com',
    phone: '+1-555-0112',
    role: 'Full Stack Developer',
    status: 'applied',
    experience: 5,
    skills: ['Vue.js', 'Laravel', 'MySQL', 'Docker'],
    location: 'Phoenix, AZ',
    appliedAt: '2026-10-03',
    expectedSalary: 130000,
  },
];

// ─── Utility Functions ───────────────────────────────────────────────────────

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatSalary(salary: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(salary);
}

function getInitials(first: string, last: string): string {
  return `${first.charAt(0)}${last.charAt(0)}`.toUpperCase();
}

// ─── Components ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: Candidate['status'] }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}

function Avatar({ firstName, lastName }: { firstName: string; lastName: string }) {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700">
      {getInitials(firstName, lastName)}
    </div>
  );
}

function Pagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
}: {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}) {
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (currentPage > 3) pages.push('…');
      for (
        let i = Math.max(2, currentPage - 1);
        i <= Math.min(totalPages - 1, currentPage + 1);
        i++
      ) {
        pages.push(i);
      }
      if (currentPage < totalPages - 2) pages.push('…');
      pages.push(totalPages);
    }
    return pages;
  };

  return (
    <div className="flex flex-col items-center justify-between gap-4 border-t border-gray-200 bg-white px-4 py-3 sm:flex-row sm:px-6">
      <p className="text-sm text-gray-700">
        Showing <span className="font-medium">{startItem}</span> to{' '}
        <span className="font-medium">{endItem}</span> of{' '}
        <span className="font-medium">{totalItems}</span> candidates
      </p>
      <nav className="flex items-center gap-1" aria-label="Pagination">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="rounded-md px-3 py-2 text-sm font-medium text-gray-500 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Previous
        </button>
        {getPageNumbers().map((page, idx) =>
          page === '…' ? (
            <span key={`ellipsis-${idx}`} className="px-2 text-gray-400">
              …
            </span>
          ) : (
            <button
              key={page}
              onClick={() => onPageChange(page as number)}
              className={`rounded-md px-3 py-2 text-sm font-medium ${
                currentPage === page
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {page}
            </button>
          )
        )}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="rounded-md px-3 py-2 text-sm font-medium text-gray-500 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Next
        </button>
      </nav>
    </div>
  );
}

function CandidateDetailModal({
  candidate,
  onClose,
}: {
  candidate: Candidate;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`Candidate details for ${candidate.firstName} ${candidate.lastName}`}
    >
      <div
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-gray-200 p-6">
          <div className="flex items-center gap-4">
            <Avatar firstName={candidate.firstName} lastName={candidate.lastName} />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {candidate.firstName} {candidate.lastName}
              </h2>
              <p className="text-sm text-gray-500">{candidate.role}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Close modal"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="space-y-6 p-6">
          {/* Status & Meta */}
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={candidate.status} />
            <span className="text-sm text-gray-500">
              Applied {formatDate(candidate.appliedAt)}
            </span>
          </div>

          {/* Contact Info */}
          <div>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
              Contact Information
            </h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                {candidate.email}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                {candidate.phone}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {candidate.location}
              </div>
              {candidate.linkedIn && (
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <svg className="h-4 w-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                  </svg>
                  {candidate.linkedIn}
                </div>
              )}
            </div>
          </div>

          {/* Experience & Salary */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-500">Experience</p>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                {candidate.experience} years
              </p>
            </div>
            {candidate.expectedSalary && (
              <div className="rounded-lg bg-gray-50 p-4">
                <p className="text-sm text-gray-500">Expected Salary</p>
                <p className="mt-1 text-lg font-semibold text-gray-900">
                  {formatSalary(candidate.expectedSalary)}
                </p>
              </div>
            )}
          </div>

          {/* Skills */}
          <div>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
              Skills
            </h3>
            <div className="flex flex-wrap gap-2">
              {candidate.skills.map((skill) => (
                <span
                  key={skill}
                  className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-medium text-indigo-700"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Notes */}
          {candidate.notes && (
            <div>
              <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-500">
                Notes
              </h3>
              <p className="rounded-lg bg-yellow-50 p-4 text-sm text-gray-700">
                {candidate.notes}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 border-t border-gray-200 p-6">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Close
          </button>
          <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
            Move to Next Stage
          </button>
        </div>
      </div>
    </div>
  );
}

function AddCandidateModal({
  onClose,
  onSubmit,
}: {
  onClose: () => void;
  onSubmit: (data: CandidateFormData) => void;
}) {
  const [form, setForm] = useState<CandidateFormData>(EMPTY_FORM);
  const [errors, setErrors] = useState<Partial<Record<keyof CandidateFormData, string>>>({});

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof CandidateFormData, string>> = {};
    if (!form.firstName.trim()) newErrors.firstName = 'First name is required';
    if (!form.lastName.trim()) newErrors.lastName = 'Last name is required';
    if (!form.email.trim()) newErrors.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
      newErrors.email = 'Invalid email format';
    if (!form.phone.trim()) newErrors.phone = 'Phone is required';
    if (!form.role.trim()) newErrors.role = 'Role is required';
    if (form.experience < 0) newErrors.experience = 'Experience must be non-negative';
    if (!form.location.trim()) newErrors.location = 'Location is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(form);
    }
  };

  const updateField = (field: keyof CandidateFormData, value: string | number) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const inputClass = (field: keyof CandidateFormData) =>
    `w-full rounded-lg border px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
      errors[field] ? 'border-red-300 bg-red-50' : 'border-gray-300'
    }`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Add new candidate"
    >
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900">Add New Candidate</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Close modal"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                First Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.firstName}
                onChange={(e) => updateField('firstName', e.target.value)}
                className={inputClass('firstName')}
                placeholder="John"
              />
              {errors.firstName && (
                <p className="mt-1 text-xs text-red-600">{errors.firstName}</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Last Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.lastName}
                onChange={(e) => updateField('lastName', e.target.value)}
                className={inputClass('lastName')}
                placeholder="Doe"
              />
              {errors.lastName && (
                <p className="mt-1 text-xs text-red-600">{errors.lastName}</p>
              )}
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Email <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => updateField('email', e.target.value)}
              className={inputClass('email')}
              placeholder="john.doe@email.com"
            />
            {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email}</p>}
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Phone <span className="text-red-500">*</span>
              </label>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => updateField('phone', e.target.value)}
                className={inputClass('phone')}
                placeholder="+1-555-0100"
              />
              {errors.phone && <p className="mt-1 text-xs text-red-600">{errors.phone}</p>}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Role <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.role}
                onChange={(e) => updateField('role', e.target.value)}
                className={inputClass('role')}
                placeholder="Software Engineer"
              />
              {errors.role && <p className="mt-1 text-xs text-red-600">{errors.role}</p>}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Experience (years)
              </label>
              <input
                type="number"
                min="0"
                value={form.experience}
                onChange={(e) => updateField('experience', parseInt(e.target.value) || 0)}
                className={inputClass('experience')}
              />
              {errors.experience && (
                <p className="mt-1 text-xs text-red-600">{errors.experience}</p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Expected Salary (USD)
              </label>
              <input
                type="number"
                min="0"
                value={form.expectedSalary}
                onChange={(e) => updateField('expectedSalary', parseInt(e.target.value) || 0)}
                className={inputClass('expectedSalary')}
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Location <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.location}
              onChange={(e) => updateField('location', e.target.value)}
              className={inputClass('location')}
              placeholder="City, State"
            />
            {errors.location && (
              <p className="mt-1 text-xs text-red-600">{errors.location}</p>
            )}
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Skills (comma-separated)
            </label>
            <input
              type="text"
              value={form.skills}
              onChange={(e) => updateField('skills', e.target.value)}
              className={inputClass('skills')}
              placeholder="React, TypeScript, Node.js"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              LinkedIn URL
            </label>
            <input
              type="url"
              value={form.linkedIn}
              onChange={(e) => updateField('linkedIn', e.target.value)}
              className={inputClass('linkedIn')}
              placeholder="linkedin.com/in/johndoe"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => updateField('notes', e.target.value)}
              rows={3}
              className={`${inputClass('notes')} resize-none`}
              placeholder="Any additional notes about this candidate..."
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Add Candidate
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Main Page Component ────────────────────────────────────────────────────

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>(MOCK_CANDIDATES);
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    status: 'all',
    role: '',
    location: '',
    minExperience: 0,
    maxExperience: 50,
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // Derived unique values for filter dropdowns
  const uniqueRoles = useMemo(
    () => [...new Set(candidates.map((c) => c.role))].sort(),
    [candidates]
  );
  const uniqueLocations = useMemo(
    () => [...new Set(candidates.map((c) => c.location))].sort(),
    [candidates]
  );

  // Filtered candidates
  const filteredCandidates = useMemo(() => {
    return candidates.filter((c) => {
      const searchLower = filters.search.toLowerCase();
      const matchesSearch =
        !filters.search ||
        c.firstName.toLowerCase().includes(searchLower) ||
        c.lastName.toLowerCase().includes(searchLower) ||
        c.email.toLowerCase().includes(searchLower) ||
        c.role.toLowerCase().includes(searchLower) ||
        c.skills.some((s) => s.toLowerCase().includes(searchLower));

      const matchesStatus = filters.status === 'all' || c.status === filters.status;
      const matchesRole = !filters.role || c.role === filters.role;
      const matchesLocation = !filters.location || c.location === filters.location;
      const matchesExperience =
        c.experience >= filters.minExperience && c.experience <= filters.maxExperience;

      return matchesSearch && matchesStatus && matchesRole && matchesLocation && matchesExperience;
    });
  }, [candidates, filters]);

  // Paginated candidates
  const totalPages = Math.max(1, Math.ceil(filteredCandidates.length / PAGE_SIZE));
  const paginatedCandidates = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredCandidates.slice(start, start + PAGE_SIZE);
  }, [filteredCandidates, currentPage]);

  // Reset to page 1 when filters change
  const updateFilters = useCallback((updates: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...updates }));
    setCurrentPage(1);
  }, []);

  const handleAddCandidate = useCallback((formData: CandidateFormData) => {
    const newCandidate: Candidate = {
      id: String(Date.now()),
      firstName: formData.firstName,
      lastName: formData.lastName,
      email: formData.email,
      phone: formData.phone,
      role: formData.role,
      status: 'applied',
      experience: formData.experience,
      skills: formData.skills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      location: formData.location,
      appliedAt: new Date().toISOString().split('T')[0],
      expectedSalary: formData.expectedSalary || undefined,
      linkedIn: formData.linkedIn || undefined,
      notes: formData.notes || undefined,
    };
    setCandidates((prev) => [newCandidate, ...prev]);
    setShowAddModal(false);
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      search: '',
      status: 'all',
      role: '',
      location: '',
      minExperience: 0,
      maxExperience: 50,
    });
    setCurrentPage(1);
  }, []);

  const hasActiveFilters =
    filters.search ||
    filters.status !== 'all' ||
    filters.role ||
    filters.location ||
    filters.minExperience > 0 ||
    filters.maxExperience < 50;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Candidates</h1>
              <p className="mt-1 text-sm text-gray-500">
                Manage and track all candidate applications
              </p>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Candidate
            </button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Search & Filter Bar */}
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-4">
            {/* Search Input */}
            <div className="relative">
              <svg
                className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
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
                placeholder="Search by name, email, role, or skill..."
                value={filters.search}
                onChange={(e) => updateFilters({ search: e.target.value })}
                className="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-4 text-sm text-gray-900 placeholder-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            {/* Filter Row */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {/* Status Filter */}
              <select
                value={filters.status}
                onChange={(e) =>
                  updateFilters({ status: e.target.value as FilterState['status'] })
                }
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="all">All Statuses</option>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>

              {/* Role Filter */}
              <select
                value={filters.role}
                onChange={(e) => updateFilters({ role: e.target.value })}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="">All Roles</option>
                {uniqueRoles.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>

              {/* Location Filter */}
              <select
                value={filters.location}
                onChange={(e) => updateFilters({ location: e.target.value })}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="">All Locations</option>
                {uniqueLocations.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>

              {/* Experience Range */}
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="0"
                  placeholder="Min exp"
                  value={filters.minExperience || ''}
                  onChange={(e) =>
                    updateFilters({ minExperience: parseInt(e.target.value) || 0 })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <span className="text-gray-400">–</span>
                <input
                  type="number"
                  min="0"
                  placeholder="Max exp"
                  value={filters.maxExperience >= 50 ? '' : filters.maxExperience}
                  onChange={(e) =>
                    updateFilters({ maxExperience: parseInt(e.target.value) || 50 })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <div className="flex justify-end">
                <button
                  onClick={clearFilters}
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-4 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            {filteredCandidates.length} candidate{filteredCandidates.length !== 1 ? 's' : ''}{' '}
            found
          </p>
        </div>

        {/* Candidate List */}
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          {paginatedCandidates.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <svg
                className="mb-4 h-12 w-12 text-gray-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <p className="text-lg font-medium text-gray-900">No candidates found</p>
              <p className="mt-1 text-sm text-gray-500">
                Try adjusting your search or filter criteria
              </p>
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="mt-4 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                >
                  Clear Filters
                </button>
              )}
            </div>
          ) : (
            <>
              {/* Table Header (hidden on mobile) */}
              <div className="hidden border-b border-gray-200 bg-gray-50 px-6 py-3 lg:block">
                <div className="grid grid-cols-12 gap-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  <div className="col-span-3">Candidate</div>
                  <div className="col-span-2">Role</div>
                  <div className="col-span-2">Status</div>
                  <div className="col-span-2">Experience</div>
                  <div className="col-span-2">Location</div>
                  <div className="col-span-1">Applied</div>
                </div>
              </div>

              {/* Candidate Rows */}
              <ul className="divide-y divide-gray-200">
                {paginatedCandidates.map((candidate) => (
                  <li
                    key={candidate.id}
                    onClick={() => setSelectedCandidate(candidate)}
                    className="cursor-pointer transition-colors hover:bg-gray-50"
                  >
                    {/* Desktop Row */}
                    <div className="hidden px-6 py-4 lg:block">
                      <div className="grid grid-cols-12 items-center gap-4">
                        <div className="col-span-3 flex items-center gap-3">
                          <Avatar
                            firstName={candidate.firstName}
                            lastName={candidate.lastName}
                          />
                          <div>
                            <p className="font-medium text-gray-900">
                              {candidate.firstName} {candidate.lastName}
                            </p>
                            <p className="text-sm text-gray-500">{candidate.email}</p>
                          </div>
                        </div>
                        <div className="col-span-2 text-sm text-gray-700">
                          {candidate.role}
                        </div>
                        <div className="col-span-2">
                          <StatusBadge status={candidate.status} />
                        </div>
                        <div className="col-span-2 text-sm text-gray-700">
                          {candidate.experience} years
                        </div>
                        <div className="col-span-2 text-sm text-gray-700">
                          {candidate.location}
                        </div>
                        <div className="col-span-1 text-sm text-gray-500">
                          {formatDate(candidate.appliedAt)}
                        </div>
                      </div>
                    </div>

                    {/* Mobile Card */}
                    <div className="px-4 py-4 lg:hidden">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <Avatar
                            firstName={candidate.firstName}
                            lastName={candidate.lastName}
                          />
                          <div>
                            <p className="font-medium text-gray-900">
                              {candidate.firstName} {candidate.lastName}
                            </p>
                            <p className="text-sm text-gray-500">{candidate.role}</p>
                          </div>
                        </div>
                        <StatusBadge status={candidate.status} />
                      </div>
                      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500">
                        <span>{candidate.location}</span>
                        <span>•</span>
                        <span>{candidate.experience} years exp</span>
                        <span>•</span>
                        <span>Applied {formatDate(candidate.appliedAt)}</span>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>

              {/* Pagination */}
              {filteredCandidates.length > 0 && (
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  totalItems={filteredCandidates.length}
                  pageSize={PAGE_SIZE}
                  onPageChange={setCurrentPage}
                />
              )}
            </>
          )}
        </div>
      </div>

      {/* Candidate Detail Modal */}
      {selectedCandidate && (
        <CandidateDetailModal
          candidate={selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
        />
      )}

      {/* Add Candidate Modal */}
      {showAddModal && (
        <AddCandidateModal
          onClose={() => setShowAddModal(false)}
          onSubmit={handleAddCandidate}
        />
      )}
    </div>
  );
}
