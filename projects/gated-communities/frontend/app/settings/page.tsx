'use client';

import React, { useState } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface UserProfile {
  displayName: string;
  email: string;
  bio: string;
  avatarUrl: string;
}

interface NotificationPrefs {
  emailNotifications: boolean;
  pushNotifications: boolean;
  communityUpdates: boolean;
  weeklyDigest: boolean;
  mentionAlerts: boolean;
}

interface CommunitySettings {
  defaultVisibility: 'public' | 'private' | 'hidden';
  joinApproval: 'auto' | 'manual';
  contentModeration: 'strict' | 'moderate' | 'relaxed';
  allowInvites: boolean;
}

interface ApiKey {
  id: string;
  name: string;
  key: string;
  createdAt: string;
  lastUsed: string;
  permissions: string[];
}

// ─── Mock Data ───────────────────────────────────────────────────────────────

const initialProfile: UserProfile = {
  displayName: 'Ahmed Hassan',
  email: 'ahmed@example.com',
  bio: 'Community builder and open-source enthusiast.',
  avatarUrl: '',
};

const initialNotifications: NotificationPrefs = {
  emailNotifications: true,
  pushNotifications: true,
  communityUpdates: true,
  weeklyDigest: false,
  mentionAlerts: true,
};

const initialCommunity: CommunitySettings = {
  defaultVisibility: 'private',
  joinApproval: 'manual',
  contentModeration: 'moderate',
  allowInvites: true,
};

const initialApiKeys: ApiKey[] = [
  {
    id: '1',
    name: 'Production Key',
    key: 'gc_prod_****_****_****_a1b2c3',
    createdAt: '2025-09-15',
    lastUsed: '2026-10-01',
    permissions: ['read', 'write'],
  },
  {
    id: '2',
    name: 'Staging Key',
    key: 'gc_stag_****_****_****_d4e5f6',
    createdAt: '2025-08-20',
    lastUsed: '2026-09-28',
    permissions: ['read'],
  },
];

// ─── Reusable Components ─────────────────────────────────────────────────────

interface SectionCardProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

function SectionCard({ title, description, children }: SectionCardProps) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {description}
        </p>
      </div>
      {children}
    </section>
  );
}

interface ToggleProps {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function Toggle({ label, description, checked, onChange }: ToggleProps) {
  return (
    <label className="flex cursor-pointer items-center justify-between py-3">
      <div>
        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {label}
        </span>
        {description && (
          <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
            {description}
          </p>
        )}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
          checked ? 'bg-indigo-600' : 'bg-gray-300 dark:bg-gray-600'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </label>
  );
}

interface SelectFieldProps {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}

function SelectField({ label, value, options, onChange }: SelectFieldProps) {
  return (
    <div className="py-3">
      <label className="mb-1 block text-sm font-medium text-gray-900 dark:text-gray-100">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

interface InputFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
}

function InputField({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  disabled = false,
}: InputFieldProps) {
  return (
    <div className="py-3">
      <label className="mb-1 block text-sm font-medium text-gray-900 dark:text-gray-100">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:cursor-not-allowed disabled:bg-gray-100 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:disabled:bg-gray-800"
      />
    </div>
  );
}

// ─── Main Settings Page ──────────────────────────────────────────────────────

export default function SettingsPage() {
  const [profile, setProfile] = useState<UserProfile>(initialProfile);
  const [notifications, setNotifications] =
    useState<NotificationPrefs>(initialNotifications);
  const [community, setCommunity] =
    useState<CommunitySettings>(initialCommunity);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>(initialApiKeys);
  const [newKeyName, setNewKeyName] = useState('');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleCreateKey = () => {
    if (!newKeyName.trim()) return;
    const newKey: ApiKey = {
      id: Date.now().toString(),
      name: newKeyName.trim(),
      key: `gc_new_****_****_****_${Math.random().toString(36).slice(2, 8)}`,
      createdAt: new Date().toISOString().split('T')[0],
      lastUsed: 'Never',
      permissions: ['read'],
    };
    setApiKeys([...apiKeys, newKey]);
    setNewKeyName('');
  };

  const handleDeleteKey = (id: string) => {
    setApiKeys(apiKeys.filter((k) => k.id !== id));
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
        <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Settings
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage your account, notifications, communities, and API access.
          </p>
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
        {/* ── 1. User Profile ─────────────────────────────────────────── */}
        <SectionCard
          title="Profile"
          description="Update your personal information and public profile."
        >
          <div className="space-y-1">
            <InputField
              label="Display Name"
              value={profile.displayName}
              onChange={(v) => setProfile({ ...profile, displayName: v })}
            />
            <InputField
              label="Email"
              value={profile.email}
              onChange={(v) => setProfile({ ...profile, email: v })}
              type="email"
            />
            <div className="py-3">
              <label className="mb-1 block text-sm font-medium text-gray-900 dark:text-gray-100">
                Bio
              </label>
              <textarea
                value={profile.bio}
                onChange={(e) =>
                  setProfile({ ...profile, bio: e.target.value })
                }
                rows={3}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
              />
            </div>
          </div>
        </SectionCard>

        {/* ── 2. Notification Preferences ─────────────────────────────── */}
        <SectionCard
          title="Notifications"
          description="Choose how and when you want to be notified."
        >
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            <Toggle
              label="Email Notifications"
              description="Receive notifications via email."
              checked={notifications.emailNotifications}
              onChange={(v) =>
                setNotifications({ ...notifications, emailNotifications: v })
              }
            />
            <Toggle
              label="Push Notifications"
              description="Receive push notifications in your browser."
              checked={notifications.pushNotifications}
              onChange={(v) =>
                setNotifications({ ...notifications, pushNotifications: v })
              }
            />
            <Toggle
              label="Community Updates"
              description="Get notified about activity in your communities."
              checked={notifications.communityUpdates}
              onChange={(v) =>
                setNotifications({ ...notifications, communityUpdates: v })
              }
            />
            <Toggle
              label="Weekly Digest"
              description="Receive a weekly summary of community activity."
              checked={notifications.weeklyDigest}
              onChange={(v) =>
                setNotifications({ ...notifications, weeklyDigest: v })
              }
            />
            <Toggle
              label="Mention Alerts"
              description="Get notified when someone mentions you."
              checked={notifications.mentionAlerts}
              onChange={(v) =>
                setNotifications({ ...notifications, mentionAlerts: v })
              }
            />
          </div>
        </SectionCard>

        {/* ── 3. Community Settings ───────────────────────────────────── */}
        <SectionCard
          title="Community Settings"
          description="Configure defaults for communities you create or manage."
        >
          <div className="space-y-1">
            <SelectField
              label="Default Visibility"
              value={community.defaultVisibility}
              options={[
                { value: 'public', label: 'Public' },
                { value: 'private', label: 'Private' },
                { value: 'hidden', label: 'Hidden' },
              ]}
              onChange={(v) =>
                setCommunity({
                  ...community,
                  defaultVisibility: v as CommunitySettings['defaultVisibility'],
                })
              }
            />
            <SelectField
              label="Join Approval"
              value={community.joinApproval}
              options={[
                { value: 'auto', label: 'Automatic' },
                { value: 'manual', label: 'Manual Review' },
              ]}
              onChange={(v) =>
                setCommunity({
                  ...community,
                  joinApproval: v as CommunitySettings['joinApproval'],
                })
              }
            />
            <SelectField
              label="Content Moderation"
              value={community.contentModeration}
              options={[
                { value: 'strict', label: 'Strict' },
                { value: 'moderate', label: 'Moderate' },
                { value: 'relaxed', label: 'Relaxed' },
              ]}
              onChange={(v) =>
                setCommunity({
                  ...community,
                  contentModeration: v as CommunitySettings['contentModeration'],
                })
              }
            />
            <Toggle
              label="Allow Invites"
              description="Let members invite others to your communities."
              checked={community.allowInvites}
              onChange={(v) =>
                setCommunity({ ...community, allowInvites: v })
              }
            />
          </div>
        </SectionCard>

        {/* ── 4. API Key Management ───────────────────────────────────── */}
        <SectionCard
          title="API Keys"
          description="Create and manage API keys for programmatic access."
        >
          {/* Existing Keys */}
          <div className="space-y-3">
            {apiKeys.map((apiKey) => (
              <div
                key={apiKey.id}
                className="flex flex-col gap-3 rounded-lg border border-gray-200 p-4 sm:flex-row sm:items-center sm:justify-between dark:border-gray-600"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {apiKey.name}
                  </p>
                  <p className="mt-0.5 truncate font-mono text-xs text-gray-500 dark:text-gray-400">
                    {apiKey.key}
                  </p>
                  <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
                    Created {apiKey.createdAt} · Last used {apiKey.lastUsed}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                    {apiKey.permissions.join(', ')}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDeleteKey(apiKey.id)}
                    className="rounded-lg border border-red-300 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/20"
                  >
                    Revoke
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Create New Key */}
          <div className="mt-4 flex flex-col gap-2 border-t border-gray-100 pt-4 sm:flex-row dark:border-gray-700">
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="New key name"
              className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
            />
            <button
              type="button"
              onClick={handleCreateKey}
              disabled={!newKeyName.trim()}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Create Key
            </button>
          </div>
        </SectionCard>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleSave}
            className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            {saved ? '✓ Saved' : 'Save Changes'}
          </button>
        </div>
      </main>
    </div>
  );
}
