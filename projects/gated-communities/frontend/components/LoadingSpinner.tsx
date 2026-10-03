'use client';

import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-3',
  lg: 'h-12 w-12 border-4',
};

export default function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  return (
    <div className={`flex items-center justify-center ${className}`} role="status" aria-label="Loading">
      <div
        className={`${sizeClasses[size]} animate-spin rounded-full border-surface-200 border-t-primary-600 dark:border-surface-700 dark:border-t-primary-400`}
      />
      <span className="sr-only">Loading...</span>
    </div>
  );
}
