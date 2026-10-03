'use client';

import React, { useState, useMemo } from 'react';
import type { ModerationItem } from '@/lib/types';

interface ModerationQueueProps {
  items: ModerationItem[];
  onResolve?: (itemId: string, resolution: string) => Promise<void>;
  onDismiss?: (itemId: string) => Promise<void>;
  onViewDetails?: (item: ModerationItem) => void;
  isLoading?: boolean;
}

const priorityColors: Record<ModerationItem['priority'], string> = {
  low: 'bg-surface-100 text-surface-600 dark:bg-surface-700 dark:text-surface-300',
  medium: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  high: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  critical: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
};

const statusColors: Record<ModerationItem['status'], string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  'in-review': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  resolved: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  dismissed: 'bg-surface-100 text-surface-600 dark:bg-surface-700 dark:text-surface-300',
};

const typeIcons: Record<ModerationItem['type'], string> = {
  report: '🚨',
  appeal: '📢',
  flag: '🚩',
  review: '🔍',
};

export default function ModerationQueue({ items, onResolve, onDismiss, onViewDetails, isLoading }: ModerationQueueProps) {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [resolution, setResolution] = useState('');

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
      const matchesPriority = priorityFilter === 'all' || item.priority === priorityFilter;
      const matchesType = typeFilter === 'all' || item.type === typeFilter;
      return matchesStatus && matchesPriority && matchesType;
    });
  }, [items, statusFilter, priorityFilter, typeFilter]);

  const handleResolve = async (itemId: string) => {
    if (!resolution.trim() || !onResolve) return;
    setResolvingId(itemId);
    try {
      await onResolve(itemId, resolution);
      setResolution('');
      setResolvingId(null);
    } catch {
      setResolvingId(null);
    }
  };

  const stats = useMemo(() => ({
    pending: items.filter((i) => i.status === 'pending').length,
    inReview: items.filter((i) => i.status === 'in-review').length,
    resolved: items.filter((i) => i.status === 'resolved').length,
    critical: items.filter((i) => i.priority === 'critical' && i.status !== 'resolved').length,
  }), [items]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse rounded-lg border border-surface-200 bg-white p-4 dark:border-surface-700 dark:bg-surface-800">
            <div className="mb-2 h-5 w-1/3 rounded bg-surface-200 dark:bg-surface-700" />
            <div className="mb-2 h-4 w-2/3 rounded bg-surface-200 dark:bg-surface-700" />
            <div className="h-4 w-1/4 rounded bg-surface-200 dark:bg-surface-700" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-lg border border-surface-200 bg-white p-4 dark:border-surface-700 dark:bg-surface-800">
          <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.pending}</div>
          <div className="text-sm text-surface-500 dark:text-surface-400">Pending</div>
        </div>
        <div className="rounded-lg border border-surface-200 bg-white p-4 dark:border-surface-700 dark:bg-surface-800">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.inReview}</div>
          <div className="text-sm text-surface-500 dark:text-surface-400">In Review</div>
        </div>
        <div className="rounded-lg border border-surface-200 bg-white p-4 dark:border-surface-700 dark:bg-surface-800">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.resolved}</div>
          <div className="text-sm text-surface-500 dark:text-surface-400">Resolved</div>
        </div>
        <div className="rounded-lg border border-surface-200 bg-white p-4 dark:border-surface-700 dark:bg-surface-800">
          <div className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.critical}</div>
          <div className="text-sm text-surface-500 dark:text-surface-400">Critical</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm dark:border-surface-600 dark:bg-surface-700 dark:text-white"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="in-review">In Review</option>
          <option value="resolved">Resolved</option>
          <option value="dismissed">Dismissed</option>
        </select>
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm dark:border-surface-600 dark:bg-surface-700 dark:text-white"
        >
          <option value="all">All Priorities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm dark:border-surface-600 dark:bg-surface-700 dark:text-white"
        >
          <option value="all">All Types</option>
          <option value="report">Report</option>
          <option value="appeal">Appeal</option>
          <option value="flag">Flag</option>
          <option value="review">Review</option>
        </select>
      </div>

      <div className="space-y-3">
        {filteredItems.map((item) => (
          <div
            key={item.id}
            className="rounded-lg border border-surface-200 bg-white p-4 dark:border-surface-700 dark:bg-surface-800"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <span className="text-xl">{typeIcons[item.type]}</span>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-surface-900 dark:text-white">{item.reason}</h3>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${priorityColors[item.priority]}`}>
                      {item.priority}
                    </span>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[item.status]}`}>
                      {item.status}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-surface-600 dark:text-surface-300">{item.description}</p>
                  <div className="mt-2 flex items-center gap-4 text-xs text-surface-500 dark:text-surface-400">
                    <span>Reporter: {item.reporterName}</span>
                    <span>Target: {item.targetName}</span>
                    <span>{new Date(item.createdAt).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {onViewDetails && (
                  <button
                    onClick={() => onViewDetails(item)}
                    className="rounded-md p-1.5 text-surface-400 hover:bg-surface-100 hover:text-surface-600 dark:hover:bg-surface-700 dark:hover:text-surface-200"
                    aria-label="View details"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                )}
              </div>
            </div>

            {(item.status === 'pending' || item.status === 'in-review') && (onResolve || onDismiss) && (
              <div className="mt-4 border-t border-surface-200 pt-4 dark:border-surface-700">
                {resolvingId === item.id ? (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={resolution}
                      onChange={(e) => setResolution(e.target.value)}
                      placeholder="Enter resolution..."
                      className="flex-1 rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm text-surface-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-surface-600 dark:bg-surface-700 dark:text-white"
                    />
                    <button
                      onClick={() => handleResolve(item.id)}
                      disabled={!resolution.trim()}
                      className="rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      Submit
                    </button>
                    <button
                      onClick={() => { setResolvingId(null); setResolution(''); }}
                      className="rounded-lg border border-surface-300 px-3 py-2 text-sm text-surface-700 hover:bg-surface-50 dark:border-surface-600 dark:text-surface-300 dark:hover:bg-surface-700"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    {onResolve && (
                      <button
                        onClick={() => setResolvingId(item.id)}
                        className="rounded-lg bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700"
                      >
                        Resolve
                      </button>
                    )}
                    {onDismiss && (
                      <button
                        onClick={() => onDismiss?.(item.id)}
                        className="rounded-lg border border-surface-300 px-3 py-1.5 text-sm text-surface-700 hover:bg-surface-50 dark:border-surface-600 dark:text-surface-300 dark:hover:bg-surface-700"
                      >
                        Dismiss
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {filteredItems.length === 0 && (
          <div className="py-12 text-center text-surface-500 dark:text-surface-400">
            <p className="text-lg">No moderation items</p>
            <p className="text-sm">All caught up! No items match your filters.</p>
          </div>
        )}
      </div>
    </div>
  );
}
