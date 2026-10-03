'use client';

import React, { useState, useMemo, useCallback } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Member {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'moderator' | 'member';
  status: 'active' | 'pending' | 'suspended';
  joinedAt: string;
  avatarUrl?: string;
  bio?: string;
  location?: string;
  lastActiveAt?: string;
}

interface InviteFormData {
  email: string;
  role: 'admin' | 'moderator' | 'member';
  message?: string;
}

interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const MOCK_MEMBERS: Member[] = [
  { id: '1', name: 'Alice Johnson', email: 'alice@example.com', role: 'admin', status: 'active', joinedAt: '2024-01-15', bio: 'Community founder and lead organizer.', location: 'New York, USA', lastActiveAt: '2024-06-10' },
  { id: '2', name: 'Bob Smith', email: 'bob@example.com', role: 'moderator', status: 'active', joinedAt: '2024-02-20', bio: 'Moderator and event coordinator.', location: 'London, UK', lastActiveAt: '2024-06-09' },
  { id: '3', name: 'Carol Williams', email: 'carol@example.com', role: 'member', status: 'active', joinedAt: '2024-03-10', location: 'Berlin, Germany', lastActiveAt: '2024-06-08' },
  { id: '4', name: 'David Brown', email: 'david@example.com', role: 'member', status: 'pending', joinedAt: '2024-06-01' },
  { id: '5', name: 'Eva Martinez', email: 'eva@example.com', role: 'member', status: 'active', joinedAt: '2024-04-05', bio: 'Active contributor and mentor.', location: 'Madrid, Spain', lastActiveAt: '2024-06-10' },
  { id: '6', name: 'Frank Lee', email: 'frank@example.com', role: 'moderator', status: 'active', joinedAt: '2024-01-28', location: 'Tokyo, Japan', lastActiveAt: '2024-06-07' },
  { id: '7', name: 'Grace Kim', email: 'grace@example.com', role: 'member', status: 'suspended', joinedAt: '2024-05-12' },
  { id: '8', name: 'Henry Patel', email: 'henry@example.com', role: 'member', status: 'active', joinedAt: '2024-03-22', location: 'Mumbai, India', lastActiveAt: '2024-06-06' },
  { id: '9', name: 'Iris Chen', email: 'iris@example.com', role: 'member', status: 'active', joinedAt: '2024-02-14', bio: 'Designer and UX enthusiast.', location: 'Taipei, Taiwan', lastActiveAt: '2024-06-10' },
  { id: '10', name: 'Jack Wilson', email: 'jack@example.com', role: 'member', status: 'pending', joinedAt: '2024-06-05' },
  { id: '11', name: 'Karen Davis', email: 'karen@example.com', role: 'member', status: 'active', joinedAt: '2024-04-18', location: 'Sydney, Australia', lastActiveAt: '2024-06-09' },
  { id: '12', name: 'Leo Garcia', email: 'leo@example.com', role: 'member', status: 'active', joinedAt: '2024-05-01', bio: 'Full-stack developer.', location: 'Mexico City, Mexico', lastActiveAt: '2024-06-08' },
];

// ─── Utility ─────────────────────────────────────────────────────────────────

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

// ─── Components ──────────────────────────────────────────────────────────────

const roleColors: Record<Member['role'], string> = {
  admin: 'bg-purple-100 text-purple-800',
  moderator: 'bg-blue-100 text-blue-800',
  member: 'bg-gray-100 text-gray-800',
};

const statusColors: Record<Member['status'], string> = {
  active: 'bg-green-100 text-green-800',
  pending: 'bg-yellow-100 text-yellow-800',
  suspended: 'bg-red-100 text-red-800',
};

// ─── Member Avatar ───────────────────────────────────────────────────────────

function MemberAvatar({ member, size = 'md' }: { member: Member; size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-16 h-16 text-xl',
  };

  if (member.avatarUrl) {
    return (
      <img
        src={member.avatarUrl}
        alt={member.name}
        className={`${sizeClasses[size]} rounded-full object-cover`}
      />
    );
  }

  return (
    <div
      className={`${sizeClasses[size]} rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-semibold`}
    >
      {getInitials(member.name)}
    </div>
  );
}

// ─── Member Detail Modal ─────────────────────────────────────────────────────

interface MemberDetailModalProps {
  member: Member;
  onClose: () => void;
  onRoleChange: (memberId: string, newRole: Member['role']) => void;
  onStatusChange: (memberId: string, newStatus: Member['status']) => void;
}

function MemberDetailModal({ member, onClose, onRoleChange, onStatusChange }: MemberDetailModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Member Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close modal"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Profile Section */}
          <div className="flex items-center gap-4">
            <MemberAvatar member={member} size="lg" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{member.name}</h3>
              <p className="text-sm text-gray-500">{member.email}</p>
            </div>
          </div>

          {/* Info Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Role</label>
              <select
                value={member.role}
                onChange={(e) => onRoleChange(member.id, e.target.value as Member['role'])}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="admin">Admin</option>
                <option value="moderator">Moderator</option>
                <option value="member">Member</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Status</label>
              <select
                value={member.status}
                onChange={(e) => onStatusChange(member.id, e.target.value as Member['status'])}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="active">Active</option>
                <option value="pending">Pending</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Joined</label>
              <p className="text-sm text-gray-900">{formatDate(member.joinedAt)}</p>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Last Active</label>
              <p className="text-sm text-gray-900">{member.lastActiveAt ? formatDate(member.lastActiveAt) : 'Never'}</p>
            </div>
          </div>

          {/* Bio */}
          {member.bio && (
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Bio</label>
              <p className="text-sm text-gray-700">{member.bio}</p>
            </div>
          )}

          {/* Location */}
          {member.location && (
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Location</label>
              <p className="text-sm text-gray-700 flex items-center gap-1">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {member.location}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Invite Member Form ──────────────────────────────────────────────────────

interface InviteMemberFormProps {
  onInvite: (data: InviteFormData) => void;
  onCancel: () => void;
}

function InviteMemberForm({ onInvite, onCancel }: InviteMemberFormProps) {
  const [formData, setFormData] = useState<InviteFormData>({
    email: '',
    role: 'member',
    message: '',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof InviteFormData, string>>>({});

  const validate = useCallback((): boolean => {
    const newErrors: Partial<Record<keyof InviteFormData, string>> = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData.email]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onInvite(formData);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50" onClick={onCancel} />
      <div className="relative bg-white rounded-xl shadow-2xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Invite Member</h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close form"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label htmlFor="invite-email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address <span className="text-red-500">*</span>
            </label>
            <input
              id="invite-email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="colleague@example.com"
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                errors.email ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email}</p>}
          </div>

          <div>
            <label htmlFor="invite-role" className="block text-sm font-medium text-gray-700 mb-1">
              Role
            </label>
            <select
              id="invite-role"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as InviteFormData['role'] })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="member">Member</option>
              <option value="moderator">Moderator</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div>
            <label htmlFor="invite-message" className="block text-sm font-medium text-gray-700 mb-1">
              Personal Message <span className="text-gray-400">(optional)</span>
            </label>
            <textarea
              id="invite-message"
              value={formData.message}
              onChange={(e) => setFormData({ ...formData, message: e.target.value })}
              placeholder="Add a personal note to the invitation..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Send Invite
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Pagination Component ────────────────────────────────────────────────────

interface PaginationProps {
  pagination: PaginationState;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

function Pagination({ pagination, onPageChange, onPageSizeChange }: PaginationProps) {
  const totalPages = Math.ceil(pagination.total / pagination.pageSize);
  const startItem = (pagination.page - 1) * pagination.pageSize + 1;
  const endItem = Math.min(pagination.page * pagination.pageSize, pagination.total);

  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (pagination.page > 3) pages.push('...');
      for (let i = Math.max(2, pagination.page - 1); i <= Math.min(totalPages - 1, pagination.page + 1); i++) {
        pages.push(i);
      }
      if (pagination.page < totalPages - 2) pages.push('...');
      pages.push(totalPages);
    }
    return pages;
  };

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-gray-200">
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <span>Showing {startItem}-{endItem} of {pagination.total}</span>
        <select
          value={pagination.pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="ml-2 px-2 py-1 border border-gray-300 rounded text-sm"
        >
          <option value={5}>5 / page</option>
          <option value={10}>10 / page</option>
          <option value={25}>25 / page</option>
          <option value={50}>50 / page</option>
        </select>
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(pagination.page - 1)}
          disabled={pagination.page === 1}
          className="px-3 py-1 text-sm rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
        >
          Previous
        </button>
        {getPageNumbers().map((page, idx) =>
          page === '...' ? (
            <span key={`ellipsis-${idx}`} className="px-2 text-gray-400">...</span>
          ) : (
            <button
              key={page}
              onClick={() => onPageChange(page as number)}
              className={`px-3 py-1 text-sm rounded border ${
                pagination.page === page
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'border-gray-300 hover:bg-gray-50'
              }`}
            >
              {page}
            </button>
          )
        )}
        <button
          onClick={() => onPageChange(pagination.page + 1)}
          disabled={pagination.page === totalPages}
          className="px-3 py-1 text-sm rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}

// ─── Main Page Component ─────────────────────────────────────────────────────

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>(MOCK_MEMBERS);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<Member['role'] | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<Member['status'] | 'all'>('all');
  const [pagination, setPagination] = useState<PaginationState>({
    page: 1,
    pageSize: 5,
    total: MOCK_MEMBERS.length,
  });
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState(false);

  // Filtered members
  const filteredMembers = useMemo(() => {
    return members.filter((member) => {
      const matchesSearch =
        member.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        member.email.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesRole = roleFilter === 'all' || member.role === roleFilter;
      const matchesStatus = statusFilter === 'all' || member.status === statusFilter;
      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [members, searchQuery, roleFilter, statusFilter]);

  // Paginated members
  const paginatedMembers = useMemo(() => {
    const start = (pagination.page - 1) * pagination.pageSize;
    return filteredMembers.slice(start, start + pagination.pageSize);
  }, [filteredMembers, pagination.page, pagination.pageSize]);

  // Update total when filters change
  React.useEffect(() => {
    setPagination((prev) => ({ ...prev, total: filteredMembers.length, page: 1 }));
  }, [filteredMembers.length]);

  const handlePageChange = (page: number) => {
    setPagination((prev) => ({ ...prev, page }));
  };

  const handlePageSizeChange = (pageSize: number) => {
    setPagination((prev) => ({ ...prev, pageSize, page: 1 }));
  };

  const handleRoleChange = (memberId: string, newRole: Member['role']) => {
    setMembers((prev) =>
      prev.map((m) => (m.id === memberId ? { ...m, role: newRole } : m))
    );
    setSelectedMember((prev) => (prev && prev.id === memberId ? { ...prev, role: newRole } : prev));
  };

  const handleStatusChange = (memberId: string, newStatus: Member['status']) => {
    setMembers((prev) =>
      prev.map((m) => (m.id === memberId ? { ...m, status: newStatus } : m))
    );
    setSelectedMember((prev) => (prev && prev.id === memberId ? { ...prev, status: newStatus } : prev));
  };

  const handleInvite = (formData: InviteFormData) => {
    const newMember: Member = {
      id: String(members.length + 1),
      name: formData.email.split('@')[0],
      email: formData.email,
      role: formData.role,
      status: 'pending',
      joinedAt: new Date().toISOString().split('T')[0],
    };
    setMembers((prev) => [...prev, newMember]);
    setShowInviteForm(false);
    setInviteSuccess(true);
    setTimeout(() => setInviteSuccess(false), 3000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Members</h1>
              <p className="mt-1 text-sm text-gray-500">
                Manage community members, roles, and invitations.
              </p>
            </div>
            <button
              onClick={() => setShowInviteForm(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Invite Member
            </button>
          </div>
        </div>
      </div>

      {/* Success Toast */}
      {inviteSuccess && (
        <div className="fixed top-4 right-4 z-50 bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-slide-in">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Invitation sent successfully!
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search and Filter Bar */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search Input */}
            <div className="flex-1">
              <div className="relative">
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Role Filter */}
            <div className="w-full md:w-40">
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value as Member['role'] | 'all')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">All Roles</option>
                <option value="admin">Admin</option>
                <option value="moderator">Moderator</option>
                <option value="member">Member</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="w-full md:w-40">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as Member['status'] | 'all')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="pending">Pending</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
          </div>
        </div>

        {/* Members Table/Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Desktop Table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Member</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Joined</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedMembers.map((member) => (
                  <tr
                    key={member.id}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => setSelectedMember(member)}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <MemberAvatar member={member} size="sm" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{member.name}</p>
                          <p className="text-xs text-gray-500">{member.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${roleColors[member.role]}`}>
                        {member.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${statusColors[member.status]}`}>
                        {member.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {formatDate(member.joinedAt)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedMember(member);
                        }}
                        className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Cards */}
          <div className="md:hidden divide-y divide-gray-200">
            {paginatedMembers.map((member) => (
              <div
                key={member.id}
                className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => setSelectedMember(member)}
              >
                <div className="flex items-center gap-3">
                  <MemberAvatar member={member} size="md" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{member.name}</p>
                    <p className="text-xs text-gray-500 truncate">{member.email}</p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${roleColors[member.role]}`}>
                      {member.role}
                    </span>
                    <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${statusColors[member.status]}`}>
                      {member.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Empty State */}
          {paginatedMembers.length === 0 && (
            <div className="p-12 text-center">
              <svg className="mx-auto w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <p className="mt-4 text-sm text-gray-500">No members found matching your criteria.</p>
            </div>
          )}

          {/* Pagination */}
          <Pagination
            pagination={pagination}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
          />
        </div>
      </div>

      {/* Member Detail Modal */}
      {selectedMember && (
        <MemberDetailModal
          member={selectedMember}
          onClose={() => setSelectedMember(null)}
          onRoleChange={handleRoleChange}
          onStatusChange={handleStatusChange}
        />
      )}

      {/* Invite Member Form */}
      {showInviteForm && (
        <InviteMemberForm
          onInvite={handleInvite}
          onCancel={() => setShowInviteForm(false)}
        />
      )}
    </div>
  );
}
