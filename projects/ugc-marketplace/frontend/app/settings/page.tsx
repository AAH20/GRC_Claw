'use client';

import React, { useState } from 'react';

// ─── Types ───────────────────────────────────────────────────────────────────

interface UserProfile {
  firstName: string;
  lastName: string;
  email: string;
  username: string;
  bio: string;
  avatarUrl: string;
  timezone: string;
  language: string;
}

interface NotificationPreferences {
  emailNotifications: boolean;
  pushNotifications: boolean;
  orderUpdates: boolean;
  newMessages: boolean;
  marketingEmails: boolean;
  weeklyDigest: boolean;
  securityAlerts: boolean;
  payoutNotifications: boolean;
}

interface PayoutSettings {
  payoutMethod: 'bank_transfer' | 'paypal' | 'stripe';
  bankName: string;
  accountNumber: string;
  routingNumber: string;
  paypalEmail: string;
  stripeAccountId: string;
  minimumPayout: number;
  currency: string;
  autoPayout: boolean;
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

// ─── Mock Data ───────────────────────────────────────────────────────────────

const initialProfile: UserProfile = {
  firstName: 'Ahmed',
  lastName: 'Hassan',
  email: 'ahmed@example.com',
  username: 'ahmedhassan',
  bio: 'Content creator and UGC specialist.',
  avatarUrl: '',
  timezone: 'Africa/Cairo',
  language: 'en',
};

const initialNotifications: NotificationPreferences = {
  emailNotifications: true,
  pushNotifications: true,
  orderUpdates: true,
  newMessages: true,
  marketingEmails: false,
  weeklyDigest: true,
  securityAlerts: true,
  payoutNotifications: true,
};

const initialPayout: PayoutSettings = {
  payoutMethod: 'bank_transfer',
  bankName: '',
  accountNumber: '',
  routingNumber: '',
  paypalEmail: '',
  stripeAccountId: '',
  minimumPayout: 50,
  currency: 'USD',
  autoPayout: false,
};

const initialApiKeys: ApiKey[] = [
  {
    id: '1',
    name: 'Production API',
    key: 'ugc_live_****************************a3f2',
    createdAt: '2025-01-15',
    lastUsed: '2026-10-01',
    permissions: ['read', 'write'],
    isActive: true,
  },
  {
    id: '2',
    name: 'Development API',
    key: 'ugc_test_****************************b7c1',
    createdAt: '2025-06-20',
    lastUsed: '2026-09-28',
    permissions: ['read'],
    isActive: true,
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
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        <p className="text-sm text-gray-500 mt-1">{description}</p>
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

interface InputFieldProps {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  helpText?: string;
}

function InputField({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  disabled = false,
  required = false,
  helpText,
}: InputFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-400 transition-colors"
      />
      {helpText && <p className="text-xs text-gray-500 mt-1">{helpText}</p>}
    </div>
  );
}

interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  disabled?: boolean;
}

function SelectField({ label, value, onChange, options, disabled = false }: SelectFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-400 transition-colors"
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

interface ToggleSwitchProps {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function ToggleSwitch({ label, description, checked, onChange }: ToggleSwitchProps) {
  return (
    <div className="flex items-center justify-between py-3">
      <div>
        <p className="text-sm font-medium text-gray-700">{label}</p>
        {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
          checked ? 'bg-blue-600' : 'bg-gray-200'
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}

// ─── Tab Navigation ──────────────────────────────────────────────────────────

type TabId = 'profile' | 'notifications' | 'payout' | 'api';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
}

const tabs: Tab[] = [
  {
    id: 'profile',
    label: 'Profile',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
  },
  {
    id: 'notifications',
    label: 'Notifications',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    ),
  },
  {
    id: 'payout',
    label: 'Payout',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
      </svg>
    ),
  },
  {
    id: 'api',
    label: 'API Keys',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
      </svg>
    ),
  },
];

// ─── Main Settings Page ──────────────────────────────────────────────────────

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>('profile');
  const [profile, setProfile] = useState<UserProfile>(initialProfile);
  const [notifications, setNotifications] = useState<NotificationPreferences>(initialNotifications);
  const [payout, setPayout] = useState<PayoutSettings>(initialPayout);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>(initialApiKeys);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyPermissions, setNewKeyPermissions] = useState<string[]>(['read']);
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  // ─── Handlers ─────────────────────────────────────────────────────────────

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage(null);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
    setSaveMessage({ type: 'success', text: 'Settings saved successfully!' });
    setTimeout(() => setSaveMessage(null), 3000);
  };

  const handleCreateApiKey = () => {
    if (!newKeyName.trim()) return;
    const key = `ugc_live_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`;
    const newKey: ApiKey = {
      id: Date.now().toString(),
      name: newKeyName,
      key: `${key.substring(0, 8)}****************************${key.substring(key.length - 4)}`,
      createdAt: new Date().toISOString().split('T')[0],
      lastUsed: 'Never',
      permissions: newKeyPermissions,
      isActive: true,
    };
    setApiKeys([...apiKeys, newKey]);
    setGeneratedKey(key);
    setNewKeyName('');
    setNewKeyPermissions(['read']);
  };

  const handleDeleteApiKey = (id: string) => {
    setApiKeys(apiKeys.filter((k) => k.id !== id));
    setShowDeleteConfirm(null);
  };

  const handleToggleApiKey = (id: string) => {
    setApiKeys(apiKeys.map((k) => (k.id === id ? { ...k, isActive: !k.isActive } : k)));
  };

  const toggleNewKeyPermission = (perm: string) => {
    setNewKeyPermissions((prev) =>
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm]
    );
  };

  // ─── Render Helpers ───────────────────────────────────────────────────────

  const renderProfileTab = () => (
    <div className="space-y-6">
      {/* Avatar Section */}
      <div className="flex items-center space-x-4">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold">
          {profile.firstName[0]}
          {profile.lastName[0]}
        </div>
        <div>
          <button className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
            Change Avatar
          </button>
          <p className="text-xs text-gray-500 mt-1">JPG, PNG or GIF. Max 2MB.</p>
        </div>
      </div>

      {/* Name Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InputField
          label="First Name"
          value={profile.firstName}
          onChange={(v) => setProfile({ ...profile, firstName: v })}
          required
        />
        <InputField
          label="Last Name"
          value={profile.lastName}
          onChange={(v) => setProfile({ ...profile, lastName: v })}
          required
        />
      </div>

      {/* Email & Username */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InputField
          label="Email Address"
          value={profile.email}
          onChange={(v) => setProfile({ ...profile, email: v })}
          type="email"
          required
        />
        <InputField
          label="Username"
          value={profile.username}
          onChange={(v) => setProfile({ ...profile, username: v })}
          required
        />
      </div>

      {/* Bio */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Bio</label>
        <textarea
          value={profile.bio}
          onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
          rows={3}
          maxLength={500}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
          placeholder="Tell us about yourself..."
        />
        <p className="text-xs text-gray-500 mt-1">{profile.bio.length}/500 characters</p>
      </div>

      {/* Timezone & Language */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SelectField
          label="Timezone"
          value={profile.timezone}
          onChange={(v) => setProfile({ ...profile, timezone: v })}
          options={[
            { value: 'Africa/Cairo', label: 'Africa/Cairo (EET)' },
            { value: 'UTC', label: 'UTC' },
            { value: 'America/New_York', label: 'Eastern Time (ET)' },
            { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
            { value: 'Europe/London', label: 'London (GMT)' },
            { value: 'Asia/Dubai', label: 'Dubai (GST)' },
          ]}
        />
        <SelectField
          label="Language"
          value={profile.language}
          onChange={(v) => setProfile({ ...profile, language: v })}
          options={[
            { value: 'en', label: 'English' },
            { value: 'ar', label: 'العربية' },
            { value: 'fr', label: 'Français' },
            { value: 'es', label: 'Español' },
          ]}
        />
      </div>
    </div>
  );

  const renderNotificationsTab = () => (
    <div className="space-y-6">
      {/* Master Toggles */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Master Controls</h3>
        <div className="divide-y divide-gray-200">
          <ToggleSwitch
            label="Email Notifications"
            description="Receive notifications via email"
            checked={notifications.emailNotifications}
            onChange={(v) => setNotifications({ ...notifications, emailNotifications: v })}
          />
          <ToggleSwitch
            label="Push Notifications"
            description="Receive push notifications in browser"
            checked={notifications.pushNotifications}
            onChange={(v) => setNotifications({ ...notifications, pushNotifications: v })}
          />
        </div>
      </div>

      {/* Notification Categories */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Notification Types</h3>
        <div className="divide-y divide-gray-200">
          <ToggleSwitch
            label="Order Updates"
            description="Get notified when orders are placed, completed, or cancelled"
            checked={notifications.orderUpdates}
            onChange={(v) => setNotifications({ ...notifications, orderUpdates: v })}
          />
          <ToggleSwitch
            label="New Messages"
            description="Get notified when you receive new messages"
            checked={notifications.newMessages}
            onChange={(v) => setNotifications({ ...notifications, newMessages: v })}
          />
          <ToggleSwitch
            label="Payout Notifications"
            description="Get notified about payout status and transfers"
            checked={notifications.payoutNotifications}
            onChange={(v) => setNotifications({ ...notifications, payoutNotifications: v })}
          />
          <ToggleSwitch
            label="Security Alerts"
            description="Get notified about security events and login attempts"
            checked={notifications.securityAlerts}
            onChange={(v) => setNotifications({ ...notifications, securityAlerts: v })}
          />
          <ToggleSwitch
            label="Marketing Emails"
            description="Receive promotional content and newsletters"
            checked={notifications.marketingEmails}
            onChange={(v) => setNotifications({ ...notifications, marketingEmails: v })}
          />
          <ToggleSwitch
            label="Weekly Digest"
            description="Receive a weekly summary of your activity"
            checked={notifications.weeklyDigest}
            onChange={(v) => setNotifications({ ...notifications, weeklyDigest: v })}
          />
        </div>
      </div>
    </div>
  );

  const renderPayoutTab = () => (
    <div className="space-y-6">
      {/* Payout Method */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Payout Method</label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {(['bank_transfer', 'paypal', 'stripe'] as const).map((method) => (
            <button
              key={method}
              type="button"
              onClick={() => setPayout({ ...payout, payoutMethod: method })}
              className={`p-4 border-2 rounded-lg text-left transition-all ${
                payout.payoutMethod === method
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <p className="text-sm font-medium text-gray-900 capitalize">
                {method.replace('_', ' ')}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {method === 'bank_transfer' && 'Direct bank deposit'}
                {method === 'paypal' && 'Pay to PayPal account'}
                {method === 'stripe' && 'Stripe Connect payout'}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Method-specific fields */}
      {payout.payoutMethod === 'bank_transfer' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InputField
            label="Bank Name"
            value={payout.bankName}
            onChange={(v) => setPayout({ ...payout, bankName: v })}
            placeholder="e.g., Chase Bank"
            required
          />
          <InputField
            label="Account Number"
            value={payout.accountNumber}
            onChange={(v) => setPayout({ ...payout, accountNumber: v })}
            placeholder="Account number"
            required
          />
          <InputField
            label="Routing Number"
            value={payout.routingNumber}
            onChange={(v) => setPayout({ ...payout, routingNumber: v })}
            placeholder="Routing number"
            required
          />
        </div>
      )}

      {payout.payoutMethod === 'paypal' && (
        <InputField
          label="PayPal Email"
          value={payout.paypalEmail}
          onChange={(v) => setPayout({ ...payout, paypalEmail: v })}
          type="email"
          placeholder="your@paypal.com"
          required
        />
      )}

      {payout.payoutMethod === 'stripe' && (
        <InputField
          label="Stripe Account ID"
          value={payout.stripeAccountId}
          onChange={(v) => setPayout({ ...payout, stripeAccountId: v })}
          placeholder="acct_xxxxxxxxxxxxx"
          required
        />
      )}

      {/* Payout Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InputField
          label="Minimum Payout Amount"
          value={payout.minimumPayout}
          onChange={(v) => setPayout({ ...payout, minimumPayout: Number(v) })}
          type="number"
          helpText="Minimum balance required to trigger a payout"
        />
        <SelectField
          label="Currency"
          value={payout.currency}
          onChange={(v) => setPayout({ ...payout, currency: v })}
          options={[
            { value: 'USD', label: 'USD - US Dollar' },
            { value: 'EUR', label: 'EUR - Euro' },
            { value: 'GBP', label: 'GBP - British Pound' },
            { value: 'EGP', label: 'EGP - Egyptian Pound' },
            { value: 'AED', label: 'AED - UAE Dirham' },
          ]}
        />
      </div>

      {/* Auto Payout */}
      <div className="bg-gray-50 rounded-lg p-4">
        <ToggleSwitch
          label="Auto Payout"
          description="Automatically send payout when minimum balance is reached"
          checked={payout.autoPayout}
          onChange={(v) => setPayout({ ...payout, autoPayout: v })}
        />
      </div>
    </div>
  );

  const renderApiTab = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Manage API keys for programmatic access to your account.
        </p>
        <button
          onClick={() => setShowNewKeyModal(true)}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          + New API Key
        </button>
      </div>

      {/* API Keys List */}
      <div className="space-y-3">
        {apiKeys.map((apiKey) => (
          <div
            key={apiKey.id}
            className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-gray-900">{apiKey.name}</h4>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      apiKey.isActive
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {apiKey.isActive ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1 font-mono">{apiKey.key}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                  <span>Created: {apiKey.createdAt}</span>
                  <span>Last used: {apiKey.lastUsed}</span>
                  <span>Permissions: {apiKey.permissions.join(', ')}</span>
                </div>
              </div>
              <div className="flex items-center gap-2 ml-4">
                <button
                  onClick={() => handleToggleApiKey(apiKey.id)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                    apiKey.isActive
                      ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                  }`}
                >
                  {apiKey.isActive ? 'Disable' : 'Enable'}
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(apiKey.id)}
                  className="px-3 py-1.5 text-xs font-medium bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {apiKeys.length === 0 && (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No API keys</h3>
          <p className="mt-1 text-sm text-gray-500">Create an API key to get started.</p>
        </div>
      )}
    </div>
  );

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your account settings and preferences</p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-1 bg-gray-100 p-1 rounded-xl overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.icon}
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Save Message */}
        {saveMessage && (
          <div
            className={`mb-6 p-4 rounded-lg ${
              saveMessage.type === 'success'
                ? 'bg-green-50 text-green-800 border border-green-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            <p className="text-sm font-medium">{saveMessage.text}</p>
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'profile' && (
          <SectionCard title="Profile Settings" description="Update your personal information and preferences">
            {renderProfileTab()}
          </SectionCard>
        )}

        {activeTab === 'notifications' && (
          <SectionCard title="Notification Preferences" description="Choose how and when you want to be notified">
            {renderNotificationsTab()}
          </SectionCard>
        )}

        {activeTab === 'payout' && (
          <SectionCard title="Payout Settings" description="Configure how and when you receive payments">
            {renderPayoutTab()}
          </SectionCard>
        )}

        {activeTab === 'api' && (
          <SectionCard title="API Key Management" description="Create and manage API keys for programmatic access">
            {renderApiTab()}
          </SectionCard>
        )}

        {/* Save Button */}
        <div className="mt-8 flex justify-end">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Saving...
              </span>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </div>

      {/* ─── New API Key Modal ─────────────────────────────────────────────── */}
      {showNewKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowNewKeyModal(false)} />
          <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New API Key</h3>

            {!generatedKey ? (
              <>
                <div className="space-y-4">
                  <InputField
                    label="Key Name"
                    value={newKeyName}
                    onChange={setNewKeyName}
                    placeholder="e.g., My App Integration"
                    required
                  />
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Permissions</label>
                    <div className="space-y-2">
                      {['read', 'write', 'delete'].map((perm) => (
                        <label key={perm} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={newKeyPermissions.includes(perm)}
                            onChange={() => toggleNewKeyPermission(perm)}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                          <span className="text-sm text-gray-700 capitalize">{perm}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="mt-6 flex justify-end gap-3">
                  <button
                    onClick={() => setShowNewKeyModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateApiKey}
                    disabled={!newKeyName.trim()}
                    className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Create Key
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-yellow-800 font-medium">API Key Created!</p>
                  <p className="text-xs text-yellow-700 mt-1">
                    Copy this key now. You won&apos;t be able to see it again.
                  </p>
                </div>
                <div className="bg-gray-100 rounded-lg p-3 font-mono text-sm text-gray-800 break-all">
                  {generatedKey}
                </div>
                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => {
                      setShowNewKeyModal(false);
                      setGeneratedKey(null);
                    }}
                    className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Done
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* ─── Delete Confirmation Modal ─────────────────────────────────────── */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowDeleteConfirm(null)} />
          <div className="relative bg-white rounded-xl shadow-xl max-w-sm w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete API Key</h3>
            <p className="text-sm text-gray-500 mb-6">
              Are you sure you want to delete this API key? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteApiKey(showDeleteConfirm)}
                className="px-4 py-2 text-sm font-medium bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
