'use client';

import React, { useState } from 'react';
import type { Tier } from '@/lib/types';

interface TierManagerProps {
  tiers: Tier[];
  onCreate?: (tier: Partial<Tier>) => Promise<void>;
  onUpdate?: (tierId: string, tier: Partial<Tier>) => Promise<void>;
  onDelete?: (tierId: string) => Promise<void>;
  isLoading?: boolean;
}

const colorOptions = [
  '#3b82f6', '#8b5cf6', '#ec4899', '#f43f5e',
  '#f97316', '#eab308', '#22c55e', '#14b8a6',
  '#06b6d4', '#6366f1',
];

export default function TierManager({ tiers, onCreate, onUpdate, onDelete, isLoading }: TierManagerProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: 0,
    currency: 'USD',
    billingPeriod: 'monthly' as Tier['billingPeriod'],
    benefits: [''],
    color: colorOptions[0],
    isActive: true,
  });

  const resetForm = () => {
    setFormData({ name: '', description: '', price: 0, currency: 'USD', billingPeriod: 'monthly', benefits: [''], color: colorOptions[0], isActive: true });
    setIsCreating(false);
    setEditingId(null);
  };

  const startEdit = (tier: Tier) => {
    setFormData({
      name: tier.name,
      description: tier.description,
      price: tier.price,
      currency: tier.currency,
      billingPeriod: tier.billingPeriod,
      benefits: tier.benefits.length > 0 ? tier.benefits : [''],
      color: tier.color,
      isActive: tier.isActive,
    });
    setEditingId(tier.id);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const benefits = formData.benefits.filter((b) => b.trim() !== '');
    const payload = { ...formData, benefits };

    if (editingId && onUpdate) {
      await onUpdate(editingId, payload);
    } else if (onCreate) {
      await onCreate(payload);
    }
    resetForm();
  };

  const addBenefit = () => setFormData((prev) => ({ ...prev, benefits: [...prev.benefits, ''] }));
  const removeBenefit = (index: number) =>
    setFormData((prev) => ({ ...prev, benefits: prev.benefits.filter((_, i) => i !== index) }));
  const updateBenefit = (index: number, value: string) =>
    setFormData((prev) => ({
      ...prev,
      benefits: prev.benefits.map((b, i) => (i === index ? value : b)),
    }));

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
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-surface-900 dark:text-white">Membership Tiers</h2>
        {!isCreating && !editingId && (
          <button
            onClick={() => setIsCreating(true)}
            className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700"
          >
            + Add Tier
          </button>
        )}
      </div>

      {(isCreating || editingId) && (
        <form onSubmit={handleSubmit} className="rounded-xl border border-surface-200 bg-white p-6 dark:border-surface-700 dark:bg-surface-800">
          <h3 className="mb-4 font-medium text-surface-900 dark:text-white">
            {editingId ? 'Edit Tier' : 'Create New Tier'}
          </h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData((p) => ({ ...p, name: e.target.value }))}
                className="w-full rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm text-surface-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-surface-600 dark:bg-surface-700 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">Price</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={formData.price}
                  onChange={(e) => setFormData((p) => ({ ...p, price: parseFloat(e.target.value) || 0 }))}
                  className="w-full rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm text-surface-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-surface-600 dark:bg-surface-700 dark:text-white"
                  min="0"
                  step="0.01"
                />
                <select
                  value={formData.currency}
                  onChange={(e) => setFormData((p) => ({ ...p, currency: e.target.value }))}
                  className="rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm dark:border-surface-600 dark:bg-surface-700 dark:text-white"
                >
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">Billing Period</label>
              <select
                value={formData.billingPeriod}
                onChange={(e) => setFormData((p) => ({ ...p, billingPeriod: e.target.value as Tier['billingPeriod'] }))}
                className="w-full rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm dark:border-surface-600 dark:bg-surface-700 dark:text-white"
              >
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
                <option value="one-time">One-time</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">Color</label>
              <div className="flex gap-2">
                {colorOptions.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setFormData((p) => ({ ...p, color }))}
                    className={`h-8 w-8 rounded-full border-2 transition-transform ${formData.color === color ? 'scale-110 border-surface-900 dark:border-white' : 'border-transparent'}`}
                    style={{ backgroundColor: color }}
                    aria-label={`Select color ${color}`}
                  />
                ))}
              </div>
            </div>
          </div>
          <div className="mt-4">
            <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData((p) => ({ ...p, description: e.target.value }))}
              className="w-full rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm text-surface-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-surface-600 dark:bg-surface-700 dark:text-white"
              rows={2}
            />
          </div>
          <div className="mt-4">
            <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">Benefits</label>
            {formData.benefits.map((benefit, index) => (
              <div key={index} className="mb-2 flex gap-2">
                <input
                  type="text"
                  value={benefit}
                  onChange={(e) => updateBenefit(index, e.target.value)}
                  className="w-full rounded-lg border border-surface-300 bg-white px-3 py-2 text-sm text-surface-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-surface-600 dark:bg-surface-700 dark:text-white"
                  placeholder="Enter a benefit"
                />
                {formData.benefits.length > 1 && (
                  <button type="button" onClick={() => removeBenefit(index)} className="rounded-lg p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
            <button type="button" onClick={addBenefit} className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400">
              + Add benefit
            </button>
          </div>
          <div className="mt-4 flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.isActive}
              onChange={(e) => setFormData((p) => ({ ...p, isActive: e.target.checked }))}
              className="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500"
            />
            <label className="text-sm text-surface-700 dark:text-surface-300">Active</label>
          </div>
          <div className="mt-6 flex gap-3">
            <button type="submit" className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700">
              {editingId ? 'Update Tier' : 'Create Tier'}
            </button>
            <button type="button" onClick={resetForm} className="rounded-lg border border-surface-300 px-4 py-2 text-sm font-medium text-surface-700 hover:bg-surface-50 dark:border-surface-600 dark:text-surface-300 dark:hover:bg-surface-700">
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="space-y-3">
        {tiers.map((tier) => (
          <div
            key={tier.id}
            className="flex items-center justify-between rounded-lg border border-surface-200 bg-white p-4 dark:border-surface-700 dark:bg-surface-800"
          >
            <div className="flex items-center gap-4">
              <div className="h-10 w-1.5 rounded-full" style={{ backgroundColor: tier.color }} />
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-surface-900 dark:text-white">{tier.name}</h3>
                  {!tier.isActive && (
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-300">Inactive</span>
                  )}
                </div>
                <p className="text-sm text-surface-500 dark:text-surface-400">{tier.description}</p>
                <div className="mt-1 flex items-center gap-3 text-xs text-surface-400 dark:text-surface-500">
                  <span>{tier.memberCount} members</span>
                  <span>·</span>
                  <span>{tier.benefits.length} benefits</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="font-semibold text-surface-900 dark:text-white">
                  ${tier.price.toFixed(2)}
                </div>
                <div className="text-xs text-surface-500 dark:text-surface-400">
                  / {tier.billingPeriod}
                </div>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => startEdit(tier)}
                  className="rounded-md p-2 text-surface-400 hover:bg-surface-100 hover:text-surface-600 dark:hover:bg-surface-700 dark:hover:text-surface-200"
                  aria-label="Edit tier"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                {onDelete && (
                  <button
                    onClick={() => onDelete(tier.id)}
                    className="rounded-md p-2 text-surface-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
                    aria-label="Delete tier"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
        {tiers.length === 0 && !isCreating && (
          <div className="py-12 text-center text-surface-500 dark:text-surface-400">
            <p className="mb-2 text-lg">No tiers yet</p>
            <p className="text-sm">Create your first membership tier to get started.</p>
          </div>
        )}
      </div>
    </div>
  );
}
