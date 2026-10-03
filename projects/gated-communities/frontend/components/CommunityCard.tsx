'use client';

import React from 'react';
import type { Community } from '@/lib/types';

interface CommunityCardProps {
  community: Community;
  onClick?: (community: Community) => void;
  onEdit?: (community: Community) => void;
  onDelete?: (community: Community) => void;
  isLoading?: boolean;
}

const statusColors: Record<Community['status'], string> = {
  active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  archived: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  draft: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
};

const visibilityIcons: Record<Community['visibility'], string> = {
  public: '🌍',
  private: '🔒',
  'invite-only': '✉️',
};

export default function CommunityCard({ community, onClick, onEdit, onDelete, isLoading }: CommunityCardProps) {
  if (isLoading) {
    return (
      <div className="animate-pulse rounded-xl border border-surface-200 bg-white p-6 dark:border-surface-700 dark:bg-surface-800">
        <div className="mb-4 h-6 w-3/4 rounded bg-surface-200 dark:bg-surface-700" />
        <div className="mb-2 h-4 w-full rounded bg-surface-200 dark:bg-surface-700" />
        <div className="mb-4 h-4 w-2/3 rounded bg-surface-200 dark:bg-surface-700" />
        <div className="flex gap-2">
          <div className="h-6 w-16 rounded-full bg-surface-200 dark:bg-surface-700" />
          <div className="h-6 w-16 rounded-full bg-surface-200 dark:bg-surface-700" />
        </div>
      </div>
    );
  }

  return (
    <div
      className="group relative rounded-xl border border-surface-200 bg-white p-6 transition-all hover:border-primary-300 hover:shadow-lg dark:border-surface-700 dark:bg-surface-800 dark:hover:border-primary-600 cursor-pointer"
      onClick={() => onClick?.(community)}
    >
      <div className="mb-3 flex items-start justify-between">
        <div className="flex items-center gap-3">
          {community.avatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={community.avatar}
              alt={community.name}
              className="h-12 w-12 rounded-lg object-cover"
            />
          ) : (
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary-100 text-xl font-bold text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
              {community.name.charAt(0).toUpperCase()}
            </div>
          )}
          <div>
            <h3 className="font-semibold text-surface-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">
              {community.name}
            </h3>
            <p className="text-sm text-surface-500 dark:text-surface-400">/{community.slug}</p>
          </div>
        </div>
        <span className="text-lg" title={community.visibility}>
          {visibilityIcons[community.visibility]}
        </span>
      </div>

      <p className="mb-4 line-clamp-2 text-sm text-surface-600 dark:text-surface-300">
        {community.description}
      </p>

      <div className="mb-4 flex flex-wrap gap-1.5">
        {community.tags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="rounded-full bg-surface-100 px-2.5 py-0.5 text-xs font-medium text-surface-600 dark:bg-surface-700 dark:text-surface-300"
          >
            {tag}
          </span>
        ))}
        {community.tags.length > 3 && (
          <span className="rounded-full bg-surface-100 px-2.5 py-0.5 text-xs text-surface-500 dark:bg-surface-700 dark:text-surface-400">
            +{community.tags.length - 3}
          </span>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-surface-500 dark:text-surface-400">
          <span>{community.memberCount.toLocaleString()} members</span>
          <span>{community.tierCount} tiers</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[community.status]}`}>
            {community.status}
          </span>
          {(onEdit || onDelete) && (
            <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
              {onEdit && (
                <button
                  onClick={(e) => { e.stopPropagation(); onEdit(community); }}
                  className="rounded-md p-1.5 text-surface-400 hover:bg-surface-100 hover:text-surface-600 dark:hover:bg-surface-700 dark:hover:text-surface-200"
                  aria-label="Edit community"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
              )}
              {onDelete && (
                <button
                  onClick={(e) => { e.stopPropagation(); onDelete(community); }}
                  className="rounded-md p-1.5 text-surface-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
                  aria-label="Delete community"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
