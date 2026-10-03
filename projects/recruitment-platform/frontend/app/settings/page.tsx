'use client';

import React, { useState } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  role: string;
  avatarUrl: string;
  timezone: string;
  language: string;
}

interface NotificationPrefs {
  emailNotifications: boolean;
  pushNotifications: boolean;
  smsNotifications: boolean;
  newApplications: boolean;
  interviewReminders: boolean;
  statusUpdates: boolean;
  weeklyDigest: boolean;
  marketingEmails: boolean;
}

interface ApiKey {
  id: string;
  name: string;
  key: string;
  createdAt: string;
  lastUsed: string;
  permissions: string[];
  isActive: boolean;
}

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'recruiter' | 'hiring_manager' | 'viewer';
  status: 'active' | 'invited' | 'suspended';
  avatarUrl: string;
  joinedAt: string;
}

type TabId = 'profile' | 'notifications' | 'apiKeys' | 'team';

// ─── Mock Data ───────────────────────────────────────────────────────────────

const initialProfile: UserProfile = {
  firstName: 'Ahmed',
  lastName: 'Hassan',
  email: 'ahmed.hassan@recruitment.io',
  phone: '+1 (555) 123-4567',
  role: 'Senior Recruiter',
  avatarUrl: '',
  timezone: 'America/New_York',
  language: 'en',
};

const initialNotifications: NotificationPrefs = {
  emailNotifications: true,
  pushNotifications: true,
  smsNotifications: false,
  newApplications: true,
  interviewReminders: true,
  statusUpdates: true,
  weeklyDigest: true,
  marketingEmails: false,
};

const initialApiKeys: ApiKey[] = [
  {
    id: '1',
    name: 'Production API',
    key: 'rpk_live_51H7xYzAbCdEfGhIjKlMnOpQr',
    createdAt: '2025-01-15',
    lastUsed: '2026-10-02',
    permissions: ['read', 'write'],
    isActive: true,
  },
  {
    id: '2',
    name: 'Staging API',
    key: 'rpk_test_51H7xYzAbCdEfGhIjKlMnOpQr',
    createdAt: '2025-06-20',
    lastUsed: '2026-09-28',
    permissions: ['read'],
    isActive: true,
  },
];

const initialTeam: TeamMember[] = [
  {
    id: '1',
    name: 'Ahmed Hassan',
    email: 'ahmed.hassan@recruitment.io',
    role: 'admin',
    status: 'active',
    avatarUrl: '',
    joinedAt: '2024-01-10',
  },
  {
    id: '2',
    name: 'Sarah Chen',
    email: 'sarah.chen@recruitment.io',
    role: 'recruiter',
    status: 'active',
    avatarUrl: '',
    joinedAt: '2024-03-15',
  },
  {
    id: '3',
    name: 'Marcus Johnson',
    email: 'marcus.j@recruitment.io',
    role: 'hiring_manager',
    status: 'active',
    avatarUrl: '',
    joinedAt: '2024-05-22',
  },
  {
    id: '4',
    name: 'Emily Rodriguez',
    email: 'emily.r@recruitment.io',
    role: 'viewer',
    status: 'invited',
    avatarUrl: '',
    joinedAt: '2026-09-30',
  },
];

// ─── Reusable UI Components ──────────────────────────────────────────────────

interface ToggleProps {
  enabled: boolean;
  onChange: (value: boolean) => void;
  label: string;
  description?: string;
}

function Toggle({ enabled, onChange, label, description }: ToggleProps) {
  return (
    <div className="flex items-center justify-between py-3">
      <div className="flex-1 pr-4">
        <p className="text-sm font-medium text-gray-900">{label}</p>
        {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={enabled}
        onClick={() => onChange(!enabled)}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
          enabled ? 'bg-indigo-600' : 'bg-gray-200'
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            enabled ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
}

function Badge({ children, variant = 'default' }: BadgeProps) {
  const variants: Record<string, string> = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]}`}>
      {children}
    </span>
  );
}

// ─── Tab: Profile Settings ───────────────────────────────────────────────────

function ProfileSettings({
  profile,
  onSave,
}: {
  profile: UserProfile;
  onSave: (profile: UserProfile) => void;
}) {
  const [form, setForm] = useState<UserProfile>(profile);
  const [saving, setSaving] = useState(false);

  const handleChange = (field: keyof UserProfile, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    await new Promise((r) => setTimeout(r, 800));
    onSave(form);
    setSaving(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Profile Information</h3>
        <p className="text-sm text-gray-500 mt-1">Update your personal details and preferences.</p>
      </div>

      {/* Avatar */}
      <div className="flex items-center space-x-4">
        <div className="h-16 w-16 rounded-full bg-indigo-100 flex items-center justify-center">
          <span className="text-2xl font-semibold text-indigo-600">
            {form.firstName[0]}
            {form.lastName[0]}
          </span>
        </div>
        <div>
          <button
            type="button"
            className="px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
          >
            Change Avatar
          </button>
          <p className="text-xs text-gray-500 mt-1">JPG, PNG or GIF. Max 2MB.</p>
        </div>
      </div>

      {/* Name fields */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
            First Name
          </label>
          <input
            id="firstName"
            type="text"
            value={form.firstName}
            onChange={(e) => handleChange('firstName', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
          />
        </div>
        <div>
          <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
            Last Name
          </label>
          <input
            id="lastName"
            type="text"
            value={form.lastName}
            onChange={(e) => handleChange('lastName', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
          />
        </div>
      </div>

      {/* Email */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
          Email Address
        </label>
        <input
          id="email"
          type="email"
          value={form.email}
          onChange={(e) => handleChange('email', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
        />
      </div>

      {/* Phone */}
      <div>
        <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
          Phone Number
        </label>
        <input
          id="phone"
          type="tel"
          value={form.phone}
          onChange={(e) => handleChange('phone', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
        />
      </div>

      {/* Role */}
      <div>
        <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
          Role / Title
        </label>
        <input
          id="role"
          type="text"
          value={form.role}
          onChange={(e) => handleChange('role', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
        />
      </div>

      {/* Timezone & Language */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="timezone" className="block text-sm font-medium text-gray-700 mb-1">
            Timezone
          </label>
          <select
            id="timezone"
            value={form.timezone}
            onChange={(e) => handleChange('timezone', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
          >
            <option value="America/New_York">Eastern Time (ET)</option>
            <option value="America/Chicago">Central Time (CT)</option>
            <option value="America/Denver">Mountain Time (MT)</option>
            <option value="America/Los_Angeles">Pacific Time (PT)</option>
            <option value="Europe/London">London (GMT)</option>
            <option value="Europe/Berlin">Berlin (CET)</option>
            <option value="Asia/Dubai">Dubai (GST)</option>
            <option value="Asia/Tokyo">Tokyo (JST)</option>
          </select>
        </div>
        <div>
          <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
            Language
          </label>
          <select
            id="language"
            value={form.language}
            onChange={(e) => handleChange('language', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
          >
            <option value="en">English</option>
            <option value="es">Español</option>
            <option value="fr">Français</option>
            <option value="de">Deutsch</option>
            <option value="ar">العربية</option>
          </select>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end pt-4 border-t border-gray-200">
        <button
          type="submit"
          disabled={saving}
          className="px-6 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
}

// ─── Tab: Notification Preferences ───────────────────────────────────────────

function NotificationSettings({
  prefs,
  onSave,
}: {
  prefs: NotificationPrefs;
  onSave: (prefs: NotificationPrefs) => void;
}) {
  const [localPrefs, setLocalPrefs] = useState<NotificationPrefs>(prefs);
  const [saving, setSaving] = useState(false);

  const handleToggle = (field: keyof NotificationPrefs, value: boolean) => {
    setLocalPrefs((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    await new Promise((r) => setTimeout(r, 600));
    onSave(localPrefs);
    setSaving(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Notification Preferences</h3>
        <p className="text-sm text-gray-500 mt-1">Choose how and when you want to be notified.</p>
      </div>

      {/* Channel toggles */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Notification Channels</h4>
        <div className="divide-y divide-gray-200">
          <Toggle
            enabled={localPrefs.emailNotifications}
            onChange={(v) => handleToggle('emailNotifications', v)}
            label="Email Notifications"
            description="Receive notifications via email"
          />
          <Toggle
            enabled={localPrefs.pushNotifications}
            onChange={(v) => handleToggle('pushNotifications', v)}
            label="Push Notifications"
            description="Browser and mobile push notifications"
          />
          <Toggle
            enabled={localPrefs.smsNotifications}
            onChange={(v) => handleToggle('smsNotifications', v)}
            label="SMS Notifications"
            description="Text message alerts for urgent updates"
          />
        </div>
      </div>

      {/* Event toggles */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Notify Me About</h4>
        <div className="divide-y divide-gray-200">
          <Toggle
            enabled={localPrefs.newApplications}
            onChange={(v) => handleToggle('newApplications', v)}
            label="New Applications"
            description="When a candidate applies to a job posting"
          />
          <Toggle
            enabled={localPrefs.interviewReminders}
            onChange={(v) => handleToggle('interviewReminders', v)}
            label="Interview Reminders"
            description="Upcoming interview alerts and reminders"
          />
          <Toggle
            enabled={localPrefs.statusUpdates}
            onChange={(v) => handleToggle('statusUpdates', v)}
            label="Application Status Updates"
            description="When a candidate's status changes"
          />
          <Toggle
            enabled={localPrefs.weeklyDigest}
            onChange={(v) => handleToggle('weeklyDigest', v)}
            label="Weekly Digest"
            description="Summary of hiring activity every Monday"
          />
          <Toggle
            enabled={localPrefs.marketingEmails}
            onChange={(v) => handleToggle('marketingEmails', v)}
            label="Product Updates & Marketing"
            description="New features, tips, and promotional content"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end pt-4 border-t border-gray-200">
        <button
          type="submit"
          disabled={saving}
          className="px-6 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {saving ? 'Saving...' : 'Save Preferences'}
        </button>
      </div>
    </form>
  );
}

// ─── Tab: API Key Management ────────────────────────────────────────────────

function ApiKeyManagement({
  apiKeys,
  onSave,
}: {
  apiKeys: ApiKey[];
  onSave: (keys: ApiKey[]) => void;
}) {
  const [keys, setKeys] = useState<ApiKey[]>(apiKeys);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyPermissions, setNewKeyPermissions] = useState<string[]>(['read']);
  const [revealedKeys, setRevealedKeys] = useState<Set<string>>(new Set());
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const maskKey = (key: string) => {
    return `${key.slice(0, 8)}${'•'.repeat(20)}${key.slice(-4)}`;
  };

  const handleCopy = async (key: string, id: string) => {
    await navigator.clipboard.writeText(key);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleToggleKey = (id: string) => {
    setKeys((prev) =>
      prev.map((k) => (k.id === id ? { ...k, isActive: !k.isActive } : k))
    );
  };

  const handleDeleteKey = (id: string) => {
    setKeys((prev) => prev.filter((k) => k.id !== id));
  };

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    const newKey: ApiKey = {
      id: String(Date.now()),
      name: newKeyName,
      key: `rpk_live_${Math.random().toString(36).slice(2, 30)}`,
      createdAt: new Date().toISOString().split('T')[0],
      lastUsed: 'Never',
      permissions: newKeyPermissions,
      isActive: true,
    };
    setKeys((prev) => [...prev, newKey]);
    setShowNewKeyModal(false);
    setNewKeyName('');
    setNewKeyPermissions(['read']);
  };

  const togglePermission = (perm: string) => {
    setNewKeyPermissions((prev) =>
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm]
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">API Keys</h3>
          <p className="text-sm text-gray-500 mt-1">
            Manage API keys for integrations and programmatic access.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowNewKeyModal(true)}
          className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors"
        >
          + New API Key
        </button>
      </div>

      {/* Key list */}
      <div className="space-y-3">
        {keys.map((apiKey) => (
          <div
            key={apiKey.id}
            className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-gray-900">{apiKey.name}</h4>
                  <Badge variant={apiKey.isActive ? 'success' : 'default'}>
                    {apiKey.isActive ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono text-gray-700">
                    {revealedKeys.has(apiKey.id) ? apiKey.key : maskKey(apiKey.key)}
                  </code>
                  <button
                    type="button"
                    onClick={() => {
                      setRevealedKeys((prev) => {
                        const next = new Set(prev);
                        if (next.has(apiKey.id)) next.delete(apiKey.id);
                        else next.add(apiKey.id);
                        return next;
                      });
                    }}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                  >
                    {revealedKeys.has(apiKey.id) ? 'Hide' : 'Reveal'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleCopy(apiKey.key, apiKey.id)}
                    className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                  >
                    {copiedId === apiKey.id ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
                  <span>Created: {apiKey.createdAt}</span>
                  <span>Last used: {apiKey.lastUsed}</span>
                  <span>Permissions: {apiKey.permissions.join(', ')}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleToggleKey(apiKey.id)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                    apiKey.isActive
                      ? 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100'
                      : 'bg-green-50 text-green-700 hover:bg-green-100'
                  }`}
                >
                  {apiKey.isActive ? 'Disable' : 'Enable'}
                </button>
                <button
                  type="button"
                  onClick={() => handleDeleteKey(apiKey.id)}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-red-50 text-red-700 hover:bg-red-100 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* New Key Modal */}
      {showNewKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New API Key</h3>
            <form onSubmit={handleCreateKey} className="space-y-4">
              <div>
                <label htmlFor="keyName" className="block text-sm font-medium text-gray-700 mb-1">
                  Key Name
                </label>
                <input
                  id="keyName"
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g., Production API"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Permissions</label>
                <div className="space-y-2">
                  {['read', 'write', 'delete'].map((perm) => (
                    <label key={perm} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={newKeyPermissions.includes(perm)}
                        onChange={() => togglePermission(perm)}
                        className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="text-sm text-gray-700 capitalize">{perm}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewKeyModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Create Key
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Tab: Team Management ───────────────────────────────────────────────────

function TeamManagement({
  members,
  onSave,
}: {
  members: TeamMember[];
  onSave: (members: TeamMember[]) => void;
}) {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>(members);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<TeamMember['role']>('recruiter');

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    const newMember: TeamMember = {
      id: String(Date.now()),
      name: inviteEmail.split('@')[0],
      email: inviteEmail,
      role: inviteRole,
      status: 'invited',
      avatarUrl: '',
      joinedAt: new Date().toISOString().split('T')[0],
    };
    setTeamMembers((prev) => [...prev, newMember]);
    setShowInviteModal(false);
    setInviteEmail('');
    setInviteRole('recruiter');
  };

  const handleRemoveMember = (id: string) => {
    setTeamMembers((prev) => prev.filter((m) => m.id !== id));
  };

  const handleResendInvite = (id: string) => {
    // In a real app, this would trigger an API call
    console.log('Resending invite for', id);
  };

  const getRoleBadgeVariant = (role: TeamMember['role']): 'info' | 'success' | 'warning' | 'default' => {
    const map: Record<string, 'info' | 'success' | 'warning' | 'default'> = {
      admin: 'danger',
      recruiter: 'info',
      hiring_manager: 'warning',
      viewer: 'default',
    };
    return map[role] || 'default';
  };

  const getStatusBadgeVariant = (status: TeamMember['status']): 'success' | 'warning' | 'default' => {
    const map: Record<string, 'success' | 'warning' | 'default'> = {
      active: 'success',
      invited: 'warning',
      suspended: 'default',
    };
    return map[status] || 'default';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Team Management</h3>
          <p className="text-sm text-gray-500 mt-1">
            Manage team members, roles, and access permissions.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowInviteModal(true)}
          className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors"
        >
          + Invite Member
        </button>
      </div>

      {/* Team list */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Member
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Role
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Joined
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {teamMembers.map((member) => (
              <tr key={member.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
                      <span className="text-xs font-semibold text-indigo-600">
                        {member.name
                          .split(' ')
                          .map((n) => n[0])
                          .join('')
                          .slice(0, 2)
                          .toUpperCase()}
                      </span>
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{member.name}</p>
                      <p className="text-xs text-gray-500 truncate">{member.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <Badge variant={getRoleBadgeVariant(member.role)}>
                    {member.role.replace('_', ' ')}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <Badge variant={getStatusBadgeVariant(member.status)}>{member.status}</Badge>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">{member.joinedAt}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    {member.status === 'invited' && (
                      <button
                        type="button"
                        onClick={() => handleResendInvite(member.id)}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                      >
                        Resend
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => handleRemoveMember(member.id)}
                      className="text-xs text-red-600 hover:text-red-800 font-medium"
                    >
                      Remove
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Invite Team Member</h3>
            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label htmlFor="inviteEmail" className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  id="inviteEmail"
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="colleague@company.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  required
                />
              </div>
              <div>
                <label htmlFor="inviteRole" className="block text-sm font-medium text-gray-700 mb-1">
                  Role
                </label>
                <select
                  id="inviteRole"
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as TeamMember['role'])}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                >
                  <option value="admin">Admin — Full access</option>
                  <option value="recruiter">Recruiter — Manage candidates & jobs</option>
                  <option value="hiring_manager">Hiring Manager — View & approve</option>
                  <option value="viewer">Viewer — Read-only access</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Send Invite
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Settings Page ──────────────────────────────────────────────────────

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>('profile');
  const [profile, setProfile] = useState<UserProfile>(initialProfile);
  const [notifications, setNotifications] = useState<NotificationPrefs>(initialNotifications);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>(initialApiKeys);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>(initialTeam);

  const tabs: { id: TabId; label: string; icon: string }[] = [
    { id: 'profile', label: 'Profile', icon: '👤' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
    { id: 'apiKeys', label: 'API Keys', icon: '🔑' },
    { id: 'team', label: 'Team', icon: '👥' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage your account settings, notifications, and team.
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Navigation */}
          <nav className="lg:w-56 flex-shrink-0">
            <ul className="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
              {tabs.map((tab) => (
                <li key={tab.id}>
                  <button
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-lg whitespace-nowrap transition-colors ${
                      activeTab === tab.id
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <span className="text-base">{tab.icon}</span>
                    {tab.label}
                  </button>
                </li>
              ))}
            </ul>
          </nav>

          {/* Content Area */}
          <main className="flex-1 min-w-0">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              {activeTab === 'profile' && (
                <ProfileSettings profile={profile} onSave={setProfile} />
              )}
              {activeTab === 'notifications' && (
                <NotificationSettings prefs={notifications} onSave={setNotifications} />
              )}
              {activeTab === 'apiKeys' && (
                <ApiKeyManagement apiKeys={apiKeys} onSave={setApiKeys} />
              )}
              {activeTab === 'team' && (
                <TeamManagement members={teamMembers} onSave={setTeamMembers} />
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
