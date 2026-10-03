"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/components/providers/AuthProvider";
import { formatDate } from "@/lib/utils";

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Profile</h1>
        <p className="text-muted-foreground">Your personal information</p>
      </div>
      <Card>
        <CardContent className="flex items-center gap-6 pt-6">
          <Avatar data-testid="user-avatar" src={user?.avatar} alt={user?.name} size="xl" />
          <div>
            <h2 data-testid="user-name" className="text-2xl font-bold">{user?.name}</h2>
            <p className="text-muted-foreground">{user?.email}</p>
            <div className="mt-2 flex items-center gap-2">
              <Badge variant="default">{user?.role}</Badge>
              <Badge variant="success">{user?.status}</Badge>
            </div>
            <p data-testid="user-bio" className="mt-2 text-muted-foreground">No bio available</p>
          </div>
        </CardContent>
      </Card>
      <Button>Edit Profile</Button>
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Account Details</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between"><span className="text-muted-foreground">Member since</span><span>{formatDate(user?.created_at ?? "")}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Last login</span><span>{formatDate(user?.last_login ?? "")}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Role</span><span className="capitalize">{user?.role}</span></div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Activity Summary</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between"><span className="text-muted-foreground">Content created</span><span>0</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Total earnings</span><span>$0</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Active listings</span><span>0</span></div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
