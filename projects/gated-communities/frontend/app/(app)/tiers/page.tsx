'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import type { Community, Tier } from '@/lib/types';
import TierManager from '@/components/TierManager';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmptyState from '@/components/EmptyState';

export default function TiersPage() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [selectedCommunity, setSelectedCommunity] = useState<string>('');
  const [tiers, setTiers] = useState<Tier[]>([]);
  const [isLoadingCommunities, setIsLoadingCommunities] = useState(true);
  const [isLoadingTiers, setIsLoadingTiers] = useState(false);
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

  const loadTiers = useCallback(async () => {
    if (!selectedCommunity) return;
    setIsLoadingTiers(true);
    try {
      const response = await apiClient.getTiers(selectedCommunity);
      setTiers(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tiers');
    } finally {
      setIsLoadingTiers(false);
    }
  }, [selectedCommunity]);

  useEffect(() => {
    loadTiers();
  }, [loadTiers]);

  const handleCreate = async (tier: Partial<Tier>) => {
    if (!selectedCommunity) return;
    await apiClient.createTier(selectedCommunity, tier);
    loadTiers();
  };

  const handleUpdate = async (tierId: string, tier: Partial<Tier>) => {
    if (!selectedCommunity) return;
    await apiClient.updateTier(selectedCommunity, tierId, tier);
    loadTiers();
  };

  const handleDelete = async (tierId: string) => {
    if (!selectedCommunity) return;
    if (!confirm('Are you sure you want to delete this tier?')) return;
    await apiClient.deleteTier(selectedCommunity, tierId);
    loadTiers();
  };

  if (isLoadingCommunities) return <LoadingSpinner className="py-20" />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-surface-900 dark:text-white">Membership Tiers</h2>
        <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
          Configure pricing and benefits for your communities
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
          description="Choose a community to manage its membership tiers."
        />
      ) : (
        <TierManager
          tiers={tiers}
          onCreate={handleCreate}
          onUpdate={handleUpdate}
          onDelete={handleDelete}
          isLoading={isLoadingTiers}
        />
      )}
    </div>
  );
}
