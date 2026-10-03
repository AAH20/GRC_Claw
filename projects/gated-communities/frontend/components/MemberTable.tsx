'use client';

import React, { useState, useMemo } from 'react';
import type { Member } from '@/lib/types';

interface MemberTableProps {
  members: Member[];
  onStatusChange?: (memberId: string, status: Member['status']) => Promise<void>;
  onRemove?: (memberId: string) => Promise<void>;
  onViewProfile?: (member: Member) => void;
  isLoading?: boolean;
  pageSize?: number;
}

const statusColors: Record<Member['status'], string> = {
  active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  suspended: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  banned: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
};

const roleColors: Record<Member['role'], string> = {
  owner: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  admin: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  moderator: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-300',
  member: 'bg-surface-100 text-surface-600 dark:bg-surface-700 dark:text-surface-300',
};

export default function MemberTable({ members, onStatusChange, onRemove, onViewProfile, isLoading, pageSize = 10 }: MemberTableProps) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedMembers, setSelectedMembers] = useState<Set<string>>(new Set());

  const filteredMembers = useMemo(() => {
    return members.filter((m) => {
      const matchesSearch =
        m.userName.toLowerCase().includes(search.toLowerCase()) ||
        m.userEmail.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = statusFilter === 'all' || m.status === statusFilter;
      const matchesRole = roleFilter === 'all' || m.role === roleFilter;
      return matchesSearch && matchesStatus && matchesRole;
    });
  }, [members, search, statusFilter, roleFilter]);

  const totalPages = Math.ceil(filteredMembers.length / pageSize);
  const paginatedMembers = filteredMembers.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const toggleSelect = (id: string) => {
    setSelectedMembers((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedMembers.size === paginatedMembers.length) {
      setSelectedMembers(new Set());
    } else {
      setSelectedMembers(new Set(paginatedMembers.map((m) => m.id)));
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="animate-pulse flex items-center gap-4 rounded-lg border border-surface-200 bg-white p-4 dark:border-surface-700 dark:bg-surface-800">
            <div className="h-10 w-10 rounded-full bg-surface-200 dark:bg-surface-700" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-1/4 rounded bg-surface-200 dark:bg-surface-700" />
              <div className="h-3 w-1/3 rounded bg-surface-200 dark:bg-surface-700" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 gap-3">
          <input
            type="text"
            placeholder="Search members..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setCurrentPage(1); }}
            className="flex-1 rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm text-surface-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-surface-600 dark:bg-surface-700 dark:text-white"
          />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
            className="rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm dark:border-surface-600 dark:bg-surface-700 dark:text-white"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="pending">Pending</option>
            <option value="suspended">Suspended</option>
            <option value="banned">Banned</option>
          </select>
          <select
            value={roleFilter}
            onChange={(e) => { setRoleFilter(e.target.value); setCurrentPage(1); }}
            className="rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm dark:border-surface-600 dark:bg-surface-700 dark:text-white"
          >
            <option value="all">All Roles</option>
            <option value="owner">Owner</option>
            <option value="admin">Admin</option>
            <option value="moderator">Moderator</option>
            <option value="member">Member</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-surface-200 dark:border-surface-700">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-surface-200 bg-surface-50 dark:border-surface-700 dark:bg-surface-800/50">
            <tr>
              <th className="px-4 py-3">
                <input
                  type="checkbox"
                  checked={selectedMembers.size === paginatedMembers.length && paginatedMembers.length > 0}
                  onChange={toggleSelectAll}
                  className="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
                />
              </th>
              <th className="px-4 py-3 font-medium text-surface-700 dark:text-surface-300">Member</th>
              <th className="px-4 py-3 font-medium text-surface-700 dark:text-surface-300">Tier</th>
              <th className="px-4 py-3 font-medium text-surface-700 dark:text-surface-300">Role</th>
              <th className="px-4 py-3 font-medium text-surface-700 dark:text-surface-300">Status</th>
              <th className="px-4 py-3 font-medium text-surface-700 dark:text-surface-300">Reputation</th>
              <th className="px-4 py-3 font-medium text-surface-700 dark:text-surface-300">Joined</th>
              <th className="px-4 py-3 font-medium text-surface-700 dark:text-surface-300">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-200 dark:divide-surface-700">
            {paginatedMembers.map((member) => (
              <tr key={member.id} className="bg-white hover:bg-surface-50 dark:bg-surface-800 dark:hover:bg-surface-700/50">
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedMembers.has(member.id)}
                    onChange={() => toggleSelect(member.id)}
                    className="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
                  />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    {member.userAvatar ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={member.userAvatar} alt={member.userName} className="h-8 w-8 rounded-full object-cover" />
                    ) : (
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-xs font-medium text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
                        {member.userName.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <div>
                      <div className="font-medium text-surface-900 dark:text-white">{member.userName}</div>
                      <div className="text-xs text-surface-500 dark:text-surface-400">{member.userEmail}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-surface-600 dark:text-surface-300">{member.tierName}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${roleColors[member.role]}`}>
                    {member.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[member.status]}`}>
                    {member.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <span className="font-medium text-surface-900 dark:text-white">{member.reputation}</span>
                    <span className="text-xs text-surface-400">pts</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-surface-500 dark:text-surface-400">
                  {new Date(member.joinedAt).toLocaleDateString()}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    {onViewProfile && (
                      <button
                        onClick={() => onViewProfile(member)}
                        className="rounded-md p-1.5 text-surface-400 hover:bg-surface-100 hover:text-surface-600 dark:hover:bg-surface-700 dark:hover:text-surface-200"
                        aria-label="View profile"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      </button>
                    )}
                    {onStatusChange && member.status !== 'active' && (
                      <button
                        onClick={() => onStatusChange(member.id, 'active')}
                        className="rounded-md p-1.5 text-surface-400 hover:bg-green-50 hover:text-green-600 dark:hover:bg-green-950/30 dark:hover:text-green-400"
                        aria-label="Activate member"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </button>
                    )}
                    {onStatusChange && member.status === 'active' && (
                      <button
                        onClick={() => onStatusChange(member.id, 'suspended')}
                        className="rounded-md p-1.5 text-surface-400 hover:bg-orange-50 hover:text-orange-600 dark:hover:bg-orange-950/30 dark:hover:text-orange-400"
                        aria-label="Suspend member"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                        </svg>
                      </button>
                    )}
                    {onRemove && (
                      <button
                        onClick={() => onRemove(member.id)}
                        className="rounded-md p-1.5 text-surface-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
                        aria-label="Remove member"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-surface-500 dark:text-surface-400">
            Showing {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, filteredMembers.length)} of {filteredMembers.length}
          </p>
          <div className="flex gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="rounded-lg border border-surface-300 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-surface-600 dark:text-surface-300"
            >
              Previous
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                onClick={() => setCurrentPage(page)}
                className={`rounded-lg px-3 py-1.5 text-sm ${
                  currentPage === page
                    ? 'bg-primary-600 text-white'
                    : 'border border-surface-300 text-surface-700 hover:bg-surface-50 dark:border-surface-600 dark:text-surface-300 dark:hover:bg-surface-700'
                }`}
              >
                {page}
              </button>
            ))}
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="rounded-lg border border-surface-300 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-surface-600 dark:text-surface-300"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {filteredMembers.length === 0 && (
        <div className="py-12 text-center text-surface-500 dark:text-surface-400">
          <p className="text-lg">No members found</p>
          <p className="text-sm">Try adjusting your search or filters.</p>
        </div>
      )}
    </div>
  );
}
