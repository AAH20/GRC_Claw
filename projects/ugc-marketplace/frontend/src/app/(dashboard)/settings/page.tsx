"use client";

import { useState } from "react";
import { User, Bell, Shield, CreditCard, Globe, Palette } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Tabs } from "@/components/ui/Tabs";
import { useAuth } from "@/components/providers/AuthProvider";
import { useTheme } from "@/components/providers/ThemeProvider";
import { useToast } from "@/components/ui/Toast";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");

  const handleSave = () => {
    toast("success", "Settings saved", "Your changes have been applied.");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">Manage your account and preferences</p>
      </div>
      <Tabs
        tabs={[
          { id: "profile", label: "Profile", icon: User },
          { id: "notifications", label: "Notifications", icon: Bell },
          { id: "security", label: "Security", icon: Shield },
          { id: "billing", label: "Billing", icon: CreditCard },
          { id: "appearance", label: "Appearance", icon: Palette },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />
      {activeTab === "profile" && (
        <Card>
          <CardHeader>
            <CardTitle>Profile Settings</CardTitle>
            <CardDescription>Update your personal information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="settings-name" className="text-sm font-medium">Full Name</label>
              <Input id="settings-name" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <label htmlFor="settings-email" className="text-sm font-medium">Email</label>
              <Input id="settings-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <Button onClick={handleSave}>Save</Button>
          </CardContent>
        </Card>
      )}
      {activeTab === "notifications" && (
        <Card>
          <CardHeader>
            <CardTitle>Notification Preferences</CardTitle>
            <CardDescription>Choose what you want to be notified about</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {["Email notifications", "Push notifications", "SMS notifications", "Weekly digest"].map((pref) => (
              <div key={pref} className="flex items-center justify-between">
                <span className="text-sm">{pref}</span>
                <input type="checkbox" className="h-4 w-4 rounded border-input" defaultChecked />
              </div>
            ))}
            <Button onClick={handleSave}>Save</Button>
          </CardContent>
        </Card>
      )}
      {activeTab === "security" && (
        <Card>
          <CardHeader>
            <CardTitle>Security Settings</CardTitle>
            <CardDescription>Manage your account security</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Current Password</label>
              <Input type="password" placeholder="••••••••" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">New Password</label>
              <Input type="password" placeholder="••••••••" />
            </div>
            <Button onClick={handleSave}>Save</Button>
          </CardContent>
        </Card>
      )}
      {activeTab === "billing" && (
        <Card>
          <CardHeader>
            <CardTitle>Billing Information</CardTitle>
            <CardDescription>Manage your payment methods and billing details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Visa ending in 4242</p>
                  <p className="text-sm text-muted-foreground">Expires 12/2025</p>
                </div>
                <Button variant="outline" size="sm">Edit</Button>
              </div>
            </div>
            <Button variant="outline">Add Payment Method</Button>
          </CardContent>
        </Card>
      )}
      {activeTab === "appearance" && (
        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
            <CardDescription>Customize how the app looks</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Theme</label>
              <div className="flex gap-2">
                {(["light", "dark", "system"] as const).map((t) => (
                  <Button key={t} variant={theme === t ? "primary" : "outline"} onClick={() => setTheme(t)} className="capitalize">
                    {t}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
