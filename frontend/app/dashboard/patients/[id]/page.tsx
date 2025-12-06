"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Phone,
  Pill,
  Calendar,
  Clock,
  TrendingUp,
  Plus,
  PhoneCall,
  Trash2,
  Smartphone,
  AlertCircle,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { api } from "@/lib/api";
import { formatTime, formatDate, getAdherenceColor } from "@/lib/utils";

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = params.id as string;

  const [patient, setPatient] = useState<any>(null);
  const [medications, setMedications] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [triggeringCall, setTriggeringCall] = useState(false);

  useEffect(() => {
    loadPatientData();
  }, [patientId]);

  const loadPatientData = async () => {
    setIsLoading(true);
    try {
      const [patientData, medsData, statsData] = await Promise.all([
        api.getPatient(patientId),
        api.getPatientMedications(patientId).catch(() => []),
        api.getAdherenceStats(patientId).catch(() => null),
      ]);

      setPatient(patientData);
      setMedications(medsData);
      setStats(statsData);
    } catch (error) {
      console.error("Failed to load patient:", error);
      router.push("/dashboard/patients");
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerCall = async () => {
    if (!patient.has_device) {
      alert("Patient has not registered their device yet. They need to install the app first.");
      return;
    }
    
    setTriggeringCall(true);
    try {
      await api.triggerCall(patientId, patient.onboarding_completed ? "reminder" : "onboarding");
      alert("Call triggered! The patient will receive an incoming call on their app.");
      loadPatientData();
    } catch (error: any) {
      console.error("Failed to trigger call:", error);
      alert(error.message || "Failed to trigger call. Please try again.");
    } finally {
      setTriggeringCall(false);
    }
  };

  const handleDeleteMedication = async (medId: string) => {
    if (confirm("Are you sure you want to remove this medication?")) {
      try {
        await api.deleteMedication(medId);
        setMedications(medications.filter((m) => m.id !== medId));
      } catch (error) {
        console.error("Failed to delete medication:", error);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!patient) {
    return null;
  }

  return (
    <div className="flex flex-col">
      <Header
        title={patient.full_name}
        subtitle={patient.phone_number}
      />

      <div className="flex-1 space-y-6 p-6">
        {/* Back Button */}
        <Link href="/dashboard/patients">
          <Button variant="ghost" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Patients
          </Button>
        </Link>

        {/* Device Status Alert */}
        {!patient.has_device && (
          <div className="rounded-xl border-2 border-amber-500/50 bg-amber-500/10 p-4 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-amber-800">App Not Installed</p>
              <p className="text-sm text-amber-700">
                This patient hasn't installed the Calla app yet. They need to install the app 
                and register their device before they can receive voice calls.
              </p>
            </div>
          </div>
        )}

        {/* Patient Info Card */}
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2 border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Patient Information</CardTitle>
              <Button
                onClick={handleTriggerCall}
                isLoading={triggeringCall}
                disabled={!patient.has_device}
                className="gap-2"
              >
                <PhoneCall className="h-4 w-4" />
                {patient.onboarding_completed ? "Call Patient" : "Start Onboarding"}
              </Button>
            </CardHeader>
            <CardContent>
              <div className="flex items-start gap-6">
                <Avatar fallback={patient.full_name} size="xl" />
                <div className="flex-1 space-y-4">
                  <div className="flex items-center gap-3 flex-wrap">
                    <h2 className="text-2xl font-bold">{patient.full_name}</h2>
                    <Badge
                      variant={patient.onboarding_completed ? "success" : "warning"}
                    >
                      {patient.onboarding_completed ? "Active" : "Pending Onboarding"}
                    </Badge>
                    <Badge
                      variant={patient.has_device ? "success" : "warning"}
                      className="gap-1"
                    >
                      <Smartphone className="h-3 w-3" />
                      {patient.has_device ? "App Installed" : "No Device"}
                    </Badge>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Phone className="h-4 w-4" />
                      {patient.phone_number}
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Calendar className="h-4 w-4" />
                      Added {formatDate(patient.created_at)}
                    </div>
                  </div>

                  {patient.onboarding_completed && (
                    <div className="mt-4">
                      <h4 className="mb-3 font-semibold">Daily Routine</h4>
                      <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-5">
                        <div className="rounded-xl bg-muted/50 p-3 text-center">
                          <p className="text-xs text-muted-foreground">Wake Up</p>
                          <p className="font-medium">{formatTime(patient.wake_time)}</p>
                        </div>
                        <div className="rounded-xl bg-muted/50 p-3 text-center">
                          <p className="text-xs text-muted-foreground">Breakfast</p>
                          <p className="font-medium">{formatTime(patient.breakfast_time)}</p>
                        </div>
                        <div className="rounded-xl bg-muted/50 p-3 text-center">
                          <p className="text-xs text-muted-foreground">Lunch</p>
                          <p className="font-medium">{formatTime(patient.lunch_time)}</p>
                        </div>
                        <div className="rounded-xl bg-muted/50 p-3 text-center">
                          <p className="text-xs text-muted-foreground">Dinner</p>
                          <p className="font-medium">{formatTime(patient.dinner_time)}</p>
                        </div>
                        <div className="rounded-xl bg-muted/50 p-3 text-center">
                          <p className="text-xs text-muted-foreground">Bedtime</p>
                          <p className="font-medium">{formatTime(patient.sleep_time)}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Adherence Stats */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Adherence Stats
              </CardTitle>
            </CardHeader>
            <CardContent>
              {stats ? (
                <div className="space-y-4">
                  <div className="text-center">
                    <p
                      className={`text-5xl font-bold ${getAdherenceColor(
                        stats.adherence_rate
                      )}`}
                    >
                      {stats.adherence_rate}%
                    </p>
                    <p className="text-sm text-muted-foreground">
                      30-day adherence rate
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-xl bg-emerald-500/10 p-4 text-center">
                      <p className="text-2xl font-bold text-emerald-600">
                        {stats.total_taken}
                      </p>
                      <p className="text-xs text-muted-foreground">Taken</p>
                    </div>
                    <div className="rounded-xl bg-rose-500/10 p-4 text-center">
                      <p className="text-2xl font-bold text-rose-600">
                        {stats.total_missed}
                      </p>
                      <p className="text-xs text-muted-foreground">Missed</p>
                    </div>
                  </div>

                  <div className="rounded-xl bg-primary/10 p-4 text-center">
                    <p className="text-2xl font-bold text-primary">
                      {stats.streak_days} days
                    </p>
                    <p className="text-xs text-muted-foreground">Current streak</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No adherence data yet
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Medications */}
        <Card className="border-0 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Pill className="h-5 w-5 text-secondary" />
              Medications
            </CardTitle>
            <Link href={`/dashboard/chat?patient=${patientId}`}>
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Add Medication
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {medications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="mb-4 rounded-full bg-muted p-4">
                  <Pill className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="mb-2 font-medium">No medications yet</p>
                <p className="mb-4 text-sm text-muted-foreground">
                  Add medications using our AI chatbot
                </p>
                <Link href={`/dashboard/chat?patient=${patientId}`}>
                  <Button>Add Medication</Button>
                </Link>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {medications.map((med) => (
                  <div
                    key={med.id}
                    className="flex items-start justify-between rounded-xl border border-border p-4 transition-colors hover:bg-muted/50"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-secondary/10">
                        <Pill className="h-6 w-6 text-secondary" />
                      </div>
                      <div>
                        <h4 className="font-semibold">{med.drug_name}</h4>
                        <p className="text-sm text-muted-foreground">
                          {med.dosage} • {med.frequency?.replace("_", " ")}
                        </p>
                        {med.specific_times && med.specific_times.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {med.specific_times.map((time: string, i: number) => (
                              <Badge key={i} variant="outline" className="text-xs">
                                <Clock className="mr-1 h-3 w-3" />
                                {formatTime(time)}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {med.timing_preference && (
                          <p className="mt-1 text-xs text-muted-foreground">
                            {med.timing_preference.replace("_", " ")}
                          </p>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:text-destructive"
                      onClick={() => handleDeleteMedication(med.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
