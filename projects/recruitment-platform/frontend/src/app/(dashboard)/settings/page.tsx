"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Badge } from "@/components/Badge";
import { Avatar } from "@/components/Avatar";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { cn, getInitials } from "@/lib/utils";
import { User, Bell, Shield, Palette, Globe, Mail, Lock, Eye, Save, Moon, Sun, Monitor } from "lucide-react";

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const { theme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState("profile");
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [profile, setProfile] = useState({
    name: user?.name || "",
    email: user?.email || "",
    department: user?.department || "",
    phone: "",
    bio: "",
  });

  const [notifications, setNotifications] = useState({
    emailApplications: true,
    emailInterviews: true,
    emailMessages: true,
    pushApplications: true,
    pushInterviews: true,
    pushMessages: false,
    weeklyDigest: true,
  });

  const [security, setSecurity] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
    twoFactor: false,
  });

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((r) => setTimeout(r, 1000));
    updateUser({ name: profile.name, email: profile.email, department: profile.department });
    setIsSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const tabs = [
    { id: "profile", label: "Profile", icon: User },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "security", label: "Security", icon: Shield },
    { id: "appearance", label: "Appearance", icon: Palette },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Manage your account preferences</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar */}
        <Card padding="sm" className="lg:w-64 flex-shrink-0">
          <nav className="flex lg:flex-col gap-1 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap",
                  activeTab === tab.id
                    ? "bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400"
                    : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                )}
              >
                <tab.icon className="h-5 w-5" />
                {tab.label}
              </button>
            ))}
          </nav>
        </Card>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {activeTab === "profile" && (
            <Card variant="bordered" padding="lg">
              <CardHeader>
                <CardTitle>Profile Settings</CardTitle>
                <CardDescription>Update your personal information</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 mb-6">
                  <Avatar alt={profile.name} fallback={getInitials(profile.name)} size="xl" />
                  <div>
                    <Button variant="outline" size="sm">Change Avatar</Button>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">JPG, PNG or GIF. Max 2MB.</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input label="Full Name" value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} />
                    <Input label="Email" type="email" value={profile.email} onChange={(e) => setProfile({ ...profile, email: e.target.value })} />
                    <Input label="Department" value={profile.department} onChange={(e) => setProfile({ ...profile, department: e.target.value })} />
                    <Input label="Phone" type="tel" value={profile.phone} onChange={(e) => setProfile({ ...profile, phone: e.target.value })} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Bio</label>
                    <textarea rows={3} value={profile.bio} onChange={(e) => setProfile({ ...profile, bio: e.target.value })} placeholder="Tell us about yourself..." className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
                  </div>
                </div>
                <div className="flex items-center justify-end gap-3 mt-6">
                  {saved && <Badge variant="success">Saved!</Badge>}
                  <Button variant="outline">Cancel</Button>
                  <Button onClick={handleSave} isLoading={isSaving} leftIcon={<Save className="h-4 w-4" />}>Save Changes</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "notifications" && (
            <Card variant="bordered" padding="lg">
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>Choose how you want to be notified</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                      <Mail className="h-4 w-4" /> Email Notifications
                    </h3>
                    <div className="space-y-3">
                      {[
                        { key: "emailApplications", label: "New applications", desc: "Get notified when a new candidate applies" },
                        { key: "emailInterviews", label: "Interview reminders", desc: "Receive reminders before interviews" },
                        { key: "emailMessages", label: "Messages", desc: "Get notified about new messages" },
                      ].map((item) => (
                        <label key={item.key} className="flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50">
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.label}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{item.desc}</p>
                          </div>
                          <input
                            type="checkbox"
                            checked={notifications[item.key as keyof typeof notifications] as boolean}
                            onChange={(e) => setNotifications({ ...notifications, [item.key]: e.target.checked })}
                            className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                          />
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                      <Bell className="h-4 w-4" /> Push Notifications
                    </h3>
                    <div className="space-y-3">
                      {[
                        { key: "pushApplications", label: "New applications", desc: "Push notifications for new applications" },
                        { key: "pushInterviews", label: "Interview reminders", desc: "Push reminders before interviews" },
                        { key: "pushMessages", label: "Messages", desc: "Push notifications for messages" },
                      ].map((item) => (
                        <label key={item.key} className="flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50">
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.label}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{item.desc}</p>
                          </div>
                          <input
                            type="checkbox"
                            checked={notifications[item.key as keyof typeof notifications] as boolean}
                            onChange={(e) => setNotifications({ ...notifications, [item.key]: e.target.checked })}
                            className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                          />
                        </label>
                      ))}
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <Button onClick={handleSave} isLoading={isSaving} leftIcon={<Save className="h-4 w-4" />}>Save Preferences</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "security" && (
            <Card variant="bordered" padding="lg">
              <CardHeader>
                <CardTitle>Security Settings</CardTitle>
                <CardDescription>Manage your password and security preferences</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                      <Lock className="h-4 w-4" /> Change Password
                    </h3>
                    <div className="space-y-4 max-w-md">
                      <Input label="Current Password" type="password" value={security.currentPassword} onChange={(e) => setSecurity({ ...security, currentPassword: e.target.value })} />
                      <Input label="New Password" type="password" value={security.newPassword} onChange={(e) => setSecurity({ ...security, newPassword: e.target.value })} />
                      <Input label="Confirm New Password" type="password" value={security.confirmPassword} onChange={(e) => setSecurity({ ...security, confirmPassword: e.target.value })} />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                      <Shield className="h-4 w-4" /> Two-Factor Authentication
                    </h3>
                    <div className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Enable 2FA</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Add an extra layer of security to your account</p>
                      </div>
                      <Button variant={security.twoFactor ? "primary" : "outline"} size="sm" onClick={() => setSecurity({ ...security, twoFactor: !security.twoFactor })}>
                        {security.twoFactor ? "Enabled" : "Disabled"}
                      </Button>
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <Button onClick={handleSave} isLoading={isSaving} leftIcon={<Save className="h-4 w-4" />}>Update Security</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "appearance" && (
            <Card variant="bordered" padding="lg">
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
                <CardDescription>Customize how the app looks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                      <Palette className="h-4 w-4" /> Theme
                    </h3>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { value: "light", label: "Light", icon: Sun },
                        { value: "dark", label: "Dark", icon: Moon },
                        { value: "system", label: "System", icon: Monitor },
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => setTheme(option.value as "light" | "dark" | "system")}
                          className={cn(
                            "flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors",
                            theme === option.value
                              ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                              : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                          )}
                        >
                          <option.icon className="h-6 w-6 text-gray-700 dark:text-gray-300" />
                          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{option.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                      <Globe className="h-4 w-4" /> Language
                    </h3>
                    <select className="w-full max-w-xs rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm">
                      <option value="en">English</option>
                      <option value="es">Español</option>
                      <option value="fr">Français</option>
                      <option value="de">Deutsch</option>
                    </select>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
