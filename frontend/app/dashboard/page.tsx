"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  Pill,
  Phone,
  TrendingUp,
  Calendar,
  Clock,
  ArrowRight,
  CheckCircle,
  AlertCircle,
  PhoneCall,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { usePatientStore } from "@/lib/store";
import { api } from "@/lib/api";
import { formatDateTime, getStatusColor } from "@/lib/utils";

export default function DashboardPage() {
  const { patients, fetchPatients, isLoading: patientsLoading } = usePatientStore();
  const [reminders, setReminders] = useState<any[]>([]);
  const [calls, setCalls] = useState<any[]>([]);
  const [stats, setStats] = useState({
    totalPatients: 0,
    activeReminders: 0,
    adherenceRate: 0,
    callsToday: 0,
  });

  useEffect(() => {
    fetchPatients();
    loadDashboardData();
  }, [fetchPatients]);

  const loadDashboardData = async () => {
    try {
      const [todayReminders, voiceSessions] = await Promise.all([
        api.getTodayReminders().catch(() => []),
        api.getVoiceSessions(10).catch(() => []),
      ]);

      setReminders(todayReminders);
      setCalls(voiceSessions);

      // Calculate stats
      const confirmed = todayReminders.filter((r: any) => r.status === "confirmed").length;
      const total = todayReminders.length;

      setStats({
        totalPatients: patients.length,
        activeReminders: total,
        adherenceRate: total > 0 ? Math.round((confirmed / total) * 100) : 0,
        callsToday: voiceSessions.filter((s: any) => 
          new Date(s.created_at).toDateString() === new Date().toDateString()
        ).length,
      });
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
    }
  };

  useEffect(() => {
    setStats(prev => ({ ...prev, totalPatients: patients.length }));
  }, [patients]);

  return (
    <div className="flex flex-col">
      <Header 
        title="Dashboard" 
        subtitle="Overview of your patients and medication adherence" 
      />

      <div className="flex-1 space-y-6 p-6">
        {/* Stats Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 stagger-children">
          <Card className="border-0 shadow-lg shadow-primary/5">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Patients</p>
                  <p className="text-3xl font-bold">{stats.totalPatients}</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
                  <Users className="h-6 w-6 text-primary" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                <TrendingUp className="h-4 w-4 text-success" />
                <span>Active care</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg shadow-secondary/5">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Today's Reminders</p>
                  <p className="text-3xl font-bold">{stats.activeReminders}</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary/10">
                  <Calendar className="h-6 w-6 text-secondary" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>Scheduled for today</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg shadow-success/5">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Adherence Rate</p>
                  <p className="text-3xl font-bold">{stats.adherenceRate}%</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10">
                  <TrendingUp className="h-6 w-6 text-emerald-500" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                <CheckCircle className="h-4 w-4 text-success" />
                <span>Today's compliance</span>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg shadow-accent/5">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Calls Today</p>
                  <p className="text-3xl font-bold">{stats.callsToday}</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10">
                  <Phone className="h-6 w-6 text-accent" />
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                <PhoneCall className="h-4 w-4" />
                <span>Completed calls</span>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Today's Reminders */}
          <Card className="border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg font-semibold">Today's Reminders</CardTitle>
              <Link href="/dashboard/schedule">
                <Button variant="ghost" size="sm" className="gap-1">
                  View All
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {reminders.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <div className="mb-4 rounded-full bg-muted p-4">
                    <Calendar className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <p className="font-medium">No reminders today</p>
                  <p className="text-sm text-muted-foreground">
                    Add medications to patients to schedule reminders
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {reminders.slice(0, 5).map((reminder: any, index: number) => (
                    <div
                      key={reminder.id || index}
                      className="flex items-center justify-between rounded-xl border border-border p-4 transition-colors hover:bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        <Avatar 
                          fallback={reminder.patients?.full_name || "P"} 
                          size="md" 
                        />
                        <div>
                          <p className="font-medium">
                            {reminder.patient_name || "Patient"}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {reminder.medication_name || "Medication"} • {formatDateTime(reminder.scheduled_time)}
                          </p>
                        </div>
                      </div>
                      <Badge className={getStatusColor(reminder.status)}>
                        {reminder.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Patients */}
          <Card className="border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg font-semibold">Recent Patients</CardTitle>
              <Link href="/dashboard/patients">
                <Button variant="ghost" size="sm" className="gap-1">
                  View All
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {patientsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                </div>
              ) : patients.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <div className="mb-4 rounded-full bg-muted p-4">
                    <Users className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <p className="font-medium">No patients yet</p>
                  <p className="mb-4 text-sm text-muted-foreground">
                    Add your first patient to get started
                  </p>
                  <Link href="/dashboard/patients">
                    <Button size="sm">Add Patient</Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {patients.slice(0, 5).map((patient) => (
                    <Link
                      key={patient.id}
                      href={`/dashboard/patients/${patient.id}`}
                      className="flex items-center justify-between rounded-xl border border-border p-4 transition-colors hover:bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        <Avatar fallback={patient.full_name} size="md" />
                        <div>
                          <p className="font-medium">{patient.full_name}</p>
                          <p className="text-sm text-muted-foreground">
                            {patient.phone_number}
                          </p>
                        </div>
                      </div>
                      <Badge variant={patient.onboarding_completed ? "success" : "warning"}>
                        {patient.onboarding_completed ? "Active" : "Onboarding"}
                      </Badge>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Link href="/dashboard/patients">
                <Button 
                  variant="outline" 
                  className="h-auto w-full flex-col gap-2 p-6 hover:border-primary/30 hover:bg-primary/5"
                >
                  <Users className="h-8 w-8 text-primary" />
                  <span className="font-semibold">Add Patient</span>
                  <span className="text-xs text-muted-foreground">Register new patient</span>
                </Button>
              </Link>

              <Link href="/dashboard/chat">
                <Button 
                  variant="outline" 
                  className="h-auto w-full flex-col gap-2 p-6 hover:border-secondary/30 hover:bg-secondary/5"
                >
                  <Pill className="h-8 w-8 text-secondary" />
                  <span className="font-semibold">Add Medication</span>
                  <span className="text-xs text-muted-foreground">Via AI chatbot</span>
                </Button>
              </Link>

              <Link href="/dashboard/schedule">
                <Button 
                  variant="outline" 
                  className="h-auto w-full flex-col gap-2 p-6 hover:border-accent/30 hover:bg-accent/5"
                >
                  <Calendar className="h-8 w-8 text-accent" />
                  <span className="font-semibold">View Schedule</span>
                  <span className="text-xs text-muted-foreground">Manage reminders</span>
                </Button>
              </Link>

              <Link href="/dashboard/calls">
                <Button 
                  variant="outline" 
                  className="h-auto w-full flex-col gap-2 p-6 hover:border-emerald-500/30 hover:bg-emerald-500/5"
                >
                  <Phone className="h-8 w-8 text-emerald-500" />
                  <span className="font-semibold">Call History</span>
                  <span className="text-xs text-muted-foreground">View transcripts</span>
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

