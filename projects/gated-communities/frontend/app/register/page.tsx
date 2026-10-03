'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Button from '@/components/Button';
import LoadingSpinner from '@/components/LoadingSpinner';

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading: authLoading } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    setIsSubmitting(true);

    try {
      await register({ name, email, password, confirmPassword });
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
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
          <h1 className="text-2xl font-bold text-surface-900 dark:text-white">Create your account</h1>
          <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
            Start building gated communities
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="name" className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
              Full Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="John Doe"
              required
              autoComplete="name"
            />
          </div>

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
              placeholder="At least 8 characters"
              required
              autoComplete="new-password"
              minLength={8}
            />
          </div>

          <div>
            <label htmlFor="confirmPassword" className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="input"
              placeholder="Confirm your password"
              required
              autoComplete="new-password"
            />
          </div>

          <Button type="submit" className="w-full" isLoading={isSubmitting}>
            Create account
          </Button>

          <p className="text-center text-sm text-surface-500 dark:text-surface-400">
            Already have an account?{' '}
            <a href="/login" className="font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400">
              Sign in
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
