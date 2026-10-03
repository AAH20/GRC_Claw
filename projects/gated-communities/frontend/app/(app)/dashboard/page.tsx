'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import type { Community, AnalyticsData } from '@/lib/types';
import StatCard from '@/components/StatCard';
import CommunityCard from '@/components/CommunityCard';
import ReputationChart from '@/components/ReputationChart';
import LoadingSpinner from '@/components/LoadingSpinner';

export default function DashboardPage() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadDashboard() {
      setIsLoading(true);
      try {
        const [communitiesRes, analyticsRes] = await Promise.all([
          apiClient.getCommunities({ pageSize: 5 }),
          apiClient.getGlobalAnalytics('30d'),
        ]);
        setCommunities(communitiesRes.data);
        setAnalytics(analyticsRes);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setIsLoading(false);
      }
    }
    loadDashboard();
  }, []);

  if (isLoading) return <LoadingSpinner className="py-20" />;

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-red-800 dark:bg-red-950/30 dark:text-red-200">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-surface-900 dark:text-white">Dashboard</h2>
        <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
          Overview of your gated communities
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Members"
          value={analytics?.totalMembers.toLocaleString() || '0'}
          change={analytics?.growthRate}
          changeLabel="vs last month"
          trend={analytics && analytics.growthRate > 0 ? 'up' : 'down'}
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
        />
        <StatCard
          title="Active Members"
          value={analytics?.activeMembers.toLocaleString() || '0'}
          change={12}
          changeLabel="vs last month"
          trend="up"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          }
        />
        <StatCard
          title="Monthly Revenue"
          value={`$${analytics?.mrr.toLocaleString() || '0'}`}
          change={8.2}
          changeLabel="vs last month"
          trend="up"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          title="Communities"
          value={communities.length.toString()}
          change={3}
          changeLabel="new this month"
          trend="up"
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
        />
      </div>

      {analytics && (
        <ReputationChart
          data={analytics.memberGrowth}
          tierDistribution={analytics.tierDistribution}
          title="Member Growth & Revenue"
        />
      )}

      <div>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-surface-900 dark:text-white">Recent Communities</h3>
          <a href="/communities" className="text-sm font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400">
            View all
          </a>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {communities.map((community) => (
            <CommunityCard key={community.id} community={community} />
          ))}
          {communities.length === 0 && (
            <div className="col-span-full py-12 text-center text-surface-500 dark:text-surface-400">
              <p className="mb-2 text-lg">No communities yet</p>
              <p className="text-sm">Create your first community to get started.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
