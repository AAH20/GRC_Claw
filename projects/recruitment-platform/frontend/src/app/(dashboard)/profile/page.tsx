"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Badge } from "@/components/Badge";
import { Avatar } from "@/components/Avatar";
import { useAuth } from "@/context/AuthContext";
import { cn, getInitials } from "@/lib/utils";
import { User, Mail, Phone, MapPin, Briefcase, Calendar, Edit, Save, Building, Globe, LinkIcon } from "lucide-react";

export default function ProfilePage() {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [profile, setProfile] = useState({
    name: user?.name || "John Doe",
    email: user?.email || "john.doe@company.com",
    phone: "+1 (555) 123-4567",
    location: "New York, NY",
    department: user?.department || "Engineering",
    role: user?.role || "Senior Recruiter",
    bio: "Passionate about connecting great talent with amazing opportunities. 5+ years of experience in technical recruiting.",
    website: "https://johndoe.com",
    linkedin: "linkedin.com/in/johndoe",
  });

  const handleSave = async () => {
    setIsSaving(true);
    await new Promise((r) => setTimeout(r, 1000));
    setIsSaving(false);
    setIsEditing(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Profile</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">View and manage your profile</p>
        </div>
        <div className="flex items-center gap-2">
          {saved && <Badge variant="success">Saved!</Badge>}
          {isEditing ? (
            <>
              <Button variant="outline" onClick={() => setIsEditing(false)}>Cancel</Button>
              <Button onClick={handleSave} isLoading={isSaving} leftIcon={<Save className="h-4 w-4" />}>Save</Button>
            </>
          ) : (
            <Button onClick={() => setIsEditing(true)} leftIcon={<Edit className="h-4 w-4" />}>Edit Profile</Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <Card variant="bordered" padding="lg" className="text-center">
          <div className="flex flex-col items-center">
            <Avatar alt={profile.name} fallback={getInitials(profile.name)} size="xl" />
            <h2 className="mt-4 text-xl font-semibold text-gray-900 dark:text-gray-100">{profile.name}</h2>
            <p className="text-gray-500 dark:text-gray-400">{profile.role}</p>
            <Badge variant="info" size="sm">{profile.department}</Badge>
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-300">{profile.bio}</p>
          </div>
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 space-y-3">
            <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
              <Mail className="h-4 w-4 text-gray-400" />
              <span>{profile.email}</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
              <Phone className="h-4 w-4 text-gray-400" />
              <span>{profile.phone}</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
              <MapPin className="h-4 w-4 text-gray-400" />
              <span>{profile.location}</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
              <Briefcase className="h-4 w-4 text-gray-400" />
              <span>{profile.department}</span>
            </div>
          </div>
        </Card>

        {/* Details */}
        <div className="lg:col-span-2 space-y-6">
          <Card variant="bordered" padding="lg">
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
              <CardDescription>Your basic profile information</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input label="Full Name" value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} disabled={!isEditing} />
                <Input label="Email" type="email" value={profile.email} onChange={(e) => setProfile({ ...profile, email: e.target.value })} disabled={!isEditing} />
                <Input label="Phone" type="tel" value={profile.phone} onChange={(e) => setProfile({ ...profile, phone: e.target.value })} disabled={!isEditing} />
                <Input label="Location" value={profile.location} onChange={(e) => setProfile({ ...profile, location: e.target.value })} disabled={!isEditing} />
                <Input label="Department" value={profile.department} onChange={(e) => setProfile({ ...profile, department: e.target.value })} disabled={!isEditing} />
                <Input label="Role" value={profile.role} onChange={(e) => setProfile({ ...profile, role: e.target.value })} disabled={!isEditing} />
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Bio</label>
                <textarea
                  rows={3}
                  value={profile.bio}
                  onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                  disabled={!isEditing}
                  className={cn(
                    "w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500",
                    !isEditing && "opacity-60 cursor-not-allowed"
                  )}
                />
              </div>
            </CardContent>
          </Card>

          <Card variant="bordered" padding="lg">
            <CardHeader>
              <CardTitle>Online Presence</CardTitle>
              <CardDescription>Your professional links</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Input label="Website" value={profile.website} onChange={(e) => setProfile({ ...profile, website: e.target.value })} disabled={!isEditing} leftIcon={<Globe className="h-4 w-4" />} />
                <Input label="LinkedIn" value={profile.linkedin} onChange={(e) => setProfile({ ...profile, linkedin: e.target.value })} disabled={!isEditing} leftIcon={<LinkIcon className="h-4 w-4" />} />
              </div>
            </CardContent>
          </Card>

          <Card variant="bordered" padding="lg">
            <CardHeader>
              <CardTitle>Account Statistics</CardTitle>
              <CardDescription>Your recruitment activity</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">156</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Candidates</p>
                </div>
                <div className="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">48</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Jobs Posted</p>
                </div>
                <div className="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">89</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Interviews</p>
                </div>
                <div className="text-center p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">23</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Hires</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
