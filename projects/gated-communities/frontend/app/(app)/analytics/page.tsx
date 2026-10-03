'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import type { Community, AnalyticsData } from '@/lib/types';
import ReputationChart from '@/components/ReputationChart';
import StatCard from '@/components/StatCard';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmptyState from '@/components/EmptyState';

type Period = AnalyticsData['period'];

export default function AnalyticsPage() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [selectedCommunity, setSelectedCommunity] = useState<string>('');
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [period, setPeriod] = useState<Period>('30d');
  const [isLoadingCommunities, setIsLoadingCommunities] = useState(true);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);
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

  const loadAnalytics = useCallback(async () => {
    if (!selectedCommunity) return;
    setIsLoadingAnalytics(true);
    try {
      const data = await apiClient.getAnalytics(selectedCommunity, period);
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setIsLoadingAnalytics(false);
    }
  }, [selectedCommunity, period]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  if (isLoadingCommunities) return <LoadingSpinner className="py-20" />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-surface-900 dark:text-white">Analytics</h2>
          <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
            Track growth, revenue, and engagement metrics
          </p>
        </div>
        <div className="flex gap-3">
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
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as Period)}
            className="input sm:w-32"
          >
            <option value="7d">7 days</option>
            <option value="30d">30 days</option>
            <option value="90d">90 days</option>
            <option value="1y">1 year</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200">
          {error}
        </div>
      )}

      {!selectedCommunity ? (
        <EmptyState
          title="Select a community"
          description="Choose a community to view its analytics."
        />
      ) : isLoadingAnalytics ? (
        <LoadingSpinner className="py-20" />
      ) : analytics ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Total Members"
              value={analytics.totalMembers.toLocaleString()}
              change={analytics.growthRate}
              changeLabel="growth"
              trend={analytics.growthRate > 0 ? 'up' : 'down'}
            />
            <StatCard
              title="Active Members"
              value={analytics.activeMembers.toLocaleString()}
              change={5.3}
              changeLabel="vs last period"
              trend="up"
            />
            <StatCard
              title="New Members"
              value={analytics.newMembers.toLocaleString()}
              change={12.1}
              changeLabel="vs last period"
              trend="up"
            />
            <StatCard
              title="Churned"
              value={analytics.churnedMembers.toLocaleString()}
              change={-2.4}
              changeLabel="vs last period"
              trend="down"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <StatCard
              title="Monthly Revenue"
              value={`$${analytics.mrr.toLocaleString()}`}
              change={8.7}
              changeLabel="vs last month"
              trend="up"
            />
            <StatCard
              title="Annual Revenue"
              value={`$${analytics.arr.toLocaleString()}`}
              change={15.2}
              changeLabel="vs last year"
              trend="up"
            />
          </div>

          <ReputationChart
            data={analytics.memberGrowth}
            tierDistribution={analytics.tierDistribution}
            title={`Member Growth — Last ${period === '7d' ? '7 Days' : period === '30d' ? '30 Days' : period === '90d' ? '90 Days' : 'Year'}`}
          />

          <ReputationChart
            data={analytics.revenueHistory}
            title="Revenue History"
            showLegend={false}
          />

          {analytics.topCommunities.length > 0 && (
            <div className="card">
              <h3 className="mb-4 font-semibold text-surface-900 dark:text-white">Top Communities</h3>
              <div className="space-y-3">
                {analytics.topCommunities.map((community) => (
                  <div key={community.communityId} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-surface-900 dark:text-white">{community.name}</p>
                      <p className="text-sm text-surface-500 dark:text-surface-400">
                        {community.memberCount.toLocaleString()} members
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-surface-900 dark:text-white">
                        ${community.revenue.toLocaleString()}
                      </p>
                      <p className={`text-sm ${community.growthRate > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {community.growthRate > 0 ? '+' : ''}{community.growthRate}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
