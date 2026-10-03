'use client';

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import Button from '@/components/Button';

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const { theme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('profile');
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState('');

  const [profile, setProfile] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });

  const [notifications, setNotifications] = useState({
    emailDigest: true,
    newMembers: true,
    moderationAlerts: true,
    weeklyReport: false,
    productUpdates: true,
  });

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage('');
    try {
      // In a real app, this would call an API
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await refreshUser();
      setMessage('Profile updated successfully.');
    } catch {
      setMessage('Failed to update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile' },
    { id: 'notifications', label: 'Notifications' },
    { id: 'appearance', label: 'Appearance' },
    { id: 'api', label: 'API & Integrations' },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold text-surface-900 dark:text-white">Settings</h2>
        <p className="mt-1 text-sm text-surface-500 dark:text-surface-400">
          Manage your account and preferences
        </p>
      </div>

      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="w-full lg:w-56">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                    : 'text-surface-600 hover:bg-surface-100 dark:text-surface-300 dark:hover:bg-surface-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1">
          {message && (
            <div className={`mb-4 rounded-lg p-3 text-sm ${
              message.includes('success')
                ? 'bg-green-50 text-green-800 dark:bg-green-950/30 dark:text-green-200'
                : 'bg-red-50 text-red-800 dark:bg-red-950/30 dark:text-red-200'
            }`}>
              {message}
            </div>
          )}

          {activeTab === 'profile' && (
            <form onSubmit={handleSaveProfile} className="card space-y-4">
              <h3 className="font-semibold text-surface-900 dark:text-white">Profile Settings</h3>
              <div>
                <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
                  Full Name
                </label>
                <input
                  type="text"
                  value={profile.name}
                  onChange={(e) => setProfile((p) => ({ ...p, name: e.target.value }))}
                  className="input"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
                  Email
                </label>
                <input
                  type="email"
                  value={profile.email}
                  onChange={(e) => setProfile((p) => ({ ...p, email: e.target.value }))}
                  className="input"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
                  Role
                </label>
                <input
                  type="text"
                  value={user?.role || 'member'}
                  disabled
                  className="input opacity-50"
                />
              </div>
              <Button type="submit" isLoading={isSaving}>
                Save Changes
              </Button>
            </form>
          )}

          {activeTab === 'notifications' && (
            <div className="card space-y-4">
              <h3 className="font-semibold text-surface-900 dark:text-white">Notification Preferences</h3>
              {Object.entries(notifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-surface-900 dark:text-white">
                      {key.replace(/([A-Z])/g, ' $1').replace(/^./, (s) => s.toUpperCase())}
                    </p>
                    <p className="text-sm text-surface-500 dark:text-surface-400">
                      Receive notifications for {key.replace(/([A-Z])/g, ' $1').toLowerCase()}
                    </p>
                  </div>
                  <button
                    onClick={() => setNotifications((n) => ({ ...n, [key]: !value }))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      value ? 'bg-primary-600' : 'bg-surface-300 dark:bg-surface-600'
                    }`}
                    role="switch"
                    aria-checked={value}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        value ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="card space-y-4">
              <h3 className="font-semibold text-surface-900 dark:text-white">Appearance</h3>
              <div>
                <label className="mb-2 block text-sm font-medium text-surface-700 dark:text-surface-300">
                  Theme
                </label>
                <div className="flex gap-3">
                  {(['light', 'dark', 'system'] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => setTheme(t)}
                      className={`flex-1 rounded-lg border-2 p-4 text-center transition-colors ${
                        theme === t
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'border-surface-200 hover:border-surface-300 dark:border-surface-700'
                      }`}
                    >
                      <div className="mb-2 text-2xl">
                        {t === 'light' ? '☀️' : t === 'dark' ? '🌙' : '💻'}
                      </div>
                      <div className="text-sm font-medium capitalize text-surface-900 dark:text-white">
                        {t}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="card space-y-4">
              <h3 className="font-semibold text-surface-900 dark:text-white">API & Integrations</h3>
              <div>
                <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
                  API Base URL
                </label>
                <input
                  type="text"
                  value={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}
                  disabled
                  className="input opacity-50"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-surface-700 dark:text-surface-300">
                  API Key
                </label>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
                    disabled
                    className="input flex-1 opacity-50"
                  />
                  <Button variant="secondary" type="button">
                    Regenerate
                  </Button>
                </div>
              </div>
              <div className="rounded-lg bg-surface-50 p-4 dark:bg-surface-700/50">
                <h4 className="mb-2 text-sm font-medium text-surface-900 dark:text-white">Webhooks</h4>
                <p className="text-sm text-surface-500 dark:text-surface-400">
                  Configure webhook endpoints to receive real-time events from your communities.
                </p>
                <Button variant="secondary" size="sm" className="mt-3">
                  Add Webhook
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
