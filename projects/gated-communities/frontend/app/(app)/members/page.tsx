'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import type { Community, Member } from '@/lib/types';
import MemberTable from '@/components/MemberTable';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmptyState from '@/components/EmptyState';

export default function MembersPage() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [selectedCommunity, setSelectedCommunity] = useState<string>('');
  const [members, setMembers] = useState<Member[]>([]);
  const [isLoadingCommunities, setIsLoadingCommunities] = useState(true);
  const [isLoadingMembers, setIsLoadingMembers] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadCommunities() {
      setIsLoadingCommunities(true);
      try {
        const response = await apiClient.getCommunities({ pageSize: 100 });
        setCommunities(response.data);
        if (response.data.length > 0 && !selectedCommunity) {
          setSelectedCommunity(response.data[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load communities');
      } finally {
        setIsLoadingCommunities(false);
      }
    }
    loadCommunities();
  }, []);

  const loadMembers = useCallback(async () => {
    if (!selectedCommunity) return;
    setIsLoadingMembers(true);
    try {
      const response = await apiClient.getMembers(selectedCommunity, { pageSize: 100 });
      setMembers(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load members');
    } finally {
      setIsLoadingMembers(false);
    }
  }, [selectedCommunity]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  const handleStatusChange = async (memberId: string, status: Member['status']) => {
    if (!selectedCommunity) return;
    await apiClient.updateMemberStatus(selectedCommunity, memberId, status);
    loadMembers();
  };

  const handleRemove = async (memberId: string) => {
    if (!selectedCommunity) return;
    if (!confirm('Are you sure you want to remove this member?')) return;
    await apiClient.removeMember(selectedCommunity, memberId);
    loadMembers();
  };

  if (isLoadingCommunities) return <LoadingSpinner className="py-20" />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-surface-900 dark:text-white">Members</h2>
        <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
          Manage community members and their status
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <select
          value={selectedCommunity}
          onChange={(e) => setSelectedCommunity(e.target.value)}
          className="input sm:max-w-xs"
        >
          <option value="">Select a community</option>
          {communities.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200">
          {error}
        </div>
      )}

      {!selectedCommunity ? (
        <EmptyState
          title="Select a community"
          description="Choose a community to view and manage its members."
        />
      ) : (
        <MemberTable
          members={members}
          onStatusChange={handleStatusChange}
          onRemove={handleRemove}
          isLoading={isLoadingMembers}
        />
      )}
    </div>
  );
}
