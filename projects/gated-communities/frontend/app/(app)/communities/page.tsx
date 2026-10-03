'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import type { Community } from '@/lib/types';
import CommunityCard from '@/components/CommunityCard';
import Button from '@/components/Button';
import Modal from '@/components/Modal';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmptyState from '@/components/EmptyState';

export default function CommunitiesPage() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    description: '',
    visibility: 'public' as Community['visibility'],
    tags: '',
  });

  const loadCommunities = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.getCommunities({
        search: search || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        pageSize: 50,
      });
      setCommunities(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load communities');
    } finally {
      setIsLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    loadCommunities();
  }, [loadCommunities]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.createCommunity({
        name: formData.name,
        slug: formData.slug || formData.name.toLowerCase().replace(/\s+/g, '-'),
        description: formData.description,
        visibility: formData.visibility,
        tags: formData.tags.split(',').map((t) => t.trim()).filter(Boolean),
      });
      setIsCreateModalOpen(false);
      setFormData({ name: '', slug: '', description: '', visibility: 'public', tags: '' });
      loadCommunities();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create community');
    }
  };

  const handleDelete = async (community: Community) => {
    if (!confirm(`Are you sure you want to delete "${community.name}"?`)) return;
    setIsDeleting(community.id);
    try {
      await apiClient.deleteCommunity(community.id);
      setCommunities((prev) => prev.filter((c) => c.id !== community.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete community');
    } finally {
      setIsDeleting(null);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-surface-900 dark:text-white">Communities</h2>
          <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
            Manage your gated communities
          </p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Community
        </Button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          type="text"
          placeholder="Search communities..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input flex-1"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input sm:w-48"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
          <option value="draft">Draft</option>
        </select>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200">
          {error}
        </div>
      )}

      {isLoading ? (
        <LoadingSpinner className="py-20" />
      ) : communities.length === 0 ? (
        <EmptyState
          title="No communities found"
          description="Create your first community to start building your gated membership platform."
          action={<Button onClick={() => setIsCreateModalOpen(true)}>Create Community</Button>}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {communities.map((community) => (
            <CommunityCard
              key={community.id}
              community={community}
              onDelete={handleDelete}
              isLoading={isDeleting === community.id}
            />
          ))}
        </div>
      )}

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Community"
        size="lg"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
              Community Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData((p) => ({ ...p, name: e.target.value }))}
              className="input"
              placeholder="My Awesome Community"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
              Slug
            </label>
            <input
              type="text"
              value={formData.slug}
              onChange={(e) => setFormData((p) => ({ ...p, slug: e.target.value }))}
              className="input"
              placeholder="my-awesome-community"
            />
            <p className="mt-1 text-xs text-surface-400">Leave empty to auto-generate from name</p>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData((p) => ({ ...p, description: e.target.value }))}
              className="input"
              rows={3}
              placeholder="Describe your community..."
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
              Visibility
            </label>
            <select
              value={formData.visibility}
              onChange={(e) => setFormData((p) => ({ ...p, visibility: e.target.value as Community['visibility'] }))}
              className="input"
            >
              <option value="public">Public</option>
              <option value="private">Private</option>
              <option value="invite-only">Invite Only</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
              Tags
            </label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData((p) => ({ ...p, tags: e.target.value }))}
              className="input"
              placeholder="technology, gaming, education"
            />
            <p className="mt-1 text-xs text-surface-400">Comma-separated tags</p>
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="submit">Create Community</Button>
            <Button type="button" variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
