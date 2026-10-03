'use client';

import React from 'react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && (
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-100 text-surface-400 dark:bg-surface-700 dark:text-surface-500">
          {icon}
        </div>
      )}
      <h3 className="mb-1 text-lg font-medium text-surface-900 dark:text-white">{title}</h3>
      {description && <p className="mb-4 max-w-sm text-sm text-surface-500 dark:text-surface-400">{description}</p>}
      {action}
    </div>
  );
}
