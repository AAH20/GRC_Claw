'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Button from '@/components/Button';
import LoadingSpinner from '@/components/LoadingSpinner';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading: authLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await login({ email, password });
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-50 px-4 dark:bg-surface-900">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-600 text-xl font-bold text-white">
            GC
          </div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-white">Welcome back</h1>
          <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
            Sign in to manage your gated communities
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="Enter your password"
              required
              autoComplete="current-password"
            />
          </div>

          <Button type="submit" className="w-full" isLoading={isSubmitting}>
            Sign in
          </Button>

          <p className="text-center text-sm text-surface-500 dark:text-surface-400">
            Don&apos;t have an account?{' '}
            <a href="/register" className="font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400">
              Sign up
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
