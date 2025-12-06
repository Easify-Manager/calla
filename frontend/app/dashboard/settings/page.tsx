"use client";

import { Settings, User, Bell, Phone, Shield } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar } from "@/components/ui/avatar";
import { useAuthStore } from "@/lib/store";

export default function SettingsPage() {
  const { caregiver } = useAuthStore();

  return (
    <div className="flex flex-col">
      <Header
        title="Settings"
        subtitle="Manage your account and preferences"
      />

      <div className="flex-1 space-y-6 p-6 max-w-3xl">
        {/* Profile Settings */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5 text-primary" />
              Profile
            </CardTitle>
            <CardDescription>
              Manage your account information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-6">
              <Avatar fallback={caregiver?.full_name || "User"} size="xl" />
              <div>
                <h3 className="font-semibold text-lg">{caregiver?.full_name}</h3>
                <p className="text-muted-foreground">{caregiver?.email}</p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Full Name</label>
                <Input defaultValue={caregiver?.full_name} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Email</label>
                <Input defaultValue={caregiver?.email} type="email" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Phone Number</label>
                <Input
                  defaultValue={caregiver?.phone_number || ""}
                  placeholder="+1 (555) 000-0000"
                />
              </div>
            </div>

            <Button>Save Changes</Button>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-secondary" />
              Notifications
            </CardTitle>
            <CardDescription>
              Configure how you receive alerts
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between rounded-xl border border-border p-4">
              <div>
                <p className="font-medium">Escalation Calls</p>
                <p className="text-sm text-muted-foreground">
                  Receive calls when patients miss medications
                </p>
              </div>
              <Button variant="outline" size="sm">
                Enabled
              </Button>
            </div>

            <div className="flex items-center justify-between rounded-xl border border-border p-4">
              <div>
                <p className="font-medium">Daily Summary</p>
                <p className="text-sm text-muted-foreground">
                  Get a daily email with adherence reports
                </p>
              </div>
              <Button variant="outline" size="sm">
                Disabled
              </Button>
            </div>

            <div className="flex items-center justify-between rounded-xl border border-border p-4">
              <div>
                <p className="font-medium">Refill Reminders</p>
                <p className="text-sm text-muted-foreground">
                  Alert when medications need refilling
                </p>
              </div>
              <Button variant="outline" size="sm">
                Enabled
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Voice Settings */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Phone className="h-5 w-5 text-accent" />
              Voice AI Settings
            </CardTitle>
            <CardDescription>
              Customize the AI voice assistant
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Default Voice</label>
              <select className="w-full rounded-xl border-2 border-border bg-card px-4 py-2 text-sm">
                <option value="friendly_female">Friendly Female (Jennifer)</option>
                <option value="friendly_male">Friendly Male (Davis)</option>
                <option value="professional_female">Professional Female</option>
                <option value="professional_male">Professional Male</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Call Retry Attempts</label>
              <select className="w-full rounded-xl border-2 border-border bg-card px-4 py-2 text-sm">
                <option value="2">2 attempts</option>
                <option value="3">3 attempts (default)</option>
                <option value="4">4 attempts</option>
                <option value="5">5 attempts</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Time Between Retries</label>
              <select className="w-full rounded-xl border-2 border-border bg-card px-4 py-2 text-sm">
                <option value="10">10 minutes</option>
                <option value="15">15 minutes (default)</option>
                <option value="20">20 minutes</option>
                <option value="30">30 minutes</option>
              </select>
            </div>

            <Button>Save Voice Settings</Button>
          </CardContent>
        </Card>

        {/* Security */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-emerald-500" />
              Security
            </CardTitle>
            <CardDescription>
              Manage your account security
            </CardDescription>
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
            <div className="space-y-2">
              <label className="text-sm font-medium">Confirm New Password</label>
              <Input type="password" placeholder="••••••••" />
            </div>

            <Button>Update Password</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

