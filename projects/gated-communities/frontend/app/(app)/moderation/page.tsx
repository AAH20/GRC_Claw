'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import type { Community, ModerationItem } from '@/lib/types';
import ModerationQueue from '@/components/ModerationQueue';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmptyState from '@/components/EmptyState';

export default function ModerationPage() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [selectedCommunity, setSelectedCommunity] = useState<string>('');
  const [items, setItems] = useState<ModerationItem[]>([]);
  const [isLoadingCommunities, setIsLoadingCommunities] = useState(true);
  const [isLoadingItems, setIsLoadingItems] = useState(false);
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

  const loadItems = useCallback(async () => {
    if (!selectedCommunity) return;
    setIsLoadingItems(true);
    try {
      const response = await apiClient.getModerationQueue(selectedCommunity, { pageSize: 100 });
      setItems(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load moderation queue');
    } finally {
      setIsLoadingItems(false);
    }
  }, [selectedCommunity]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  const handleResolve = async (itemId: string, resolution: string) => {
    if (!selectedCommunity) return;
    await apiClient.resolveModerationItem(selectedCommunity, itemId, resolution);
    loadItems();
  };

  const handleDismiss = async (itemId: string) => {
    if (!selectedCommunity) return;
    await apiClient.dismissModerationItem(selectedCommunity, itemId);
    loadItems();
  };

  if (isLoadingCommunities) return <LoadingSpinner className="py-20" />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-surface-900 dark:text-white">Moderation</h2>
        <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
          Review and resolve community reports and appeals
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
          description="Choose a community to view its moderation queue."
        />
      ) : (
        <ModerationQueue
          items={items}
          onResolve={handleResolve}
          onDismiss={handleDismiss}
          isLoading={isLoadingItems}
        />
      )}
    </div>
  );
}
