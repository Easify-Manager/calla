"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Pill, Plus, Clock, User } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { usePatientStore } from "@/lib/store";
import { api } from "@/lib/api";
import { formatTime } from "@/lib/utils";

interface MedicationWithPatient {
  medication: any;
  patient: any;
}

export default function MedicationsPage() {
  const { patients, fetchPatients, isLoading: patientsLoading } = usePatientStore();
  const [allMedications, setAllMedications] = useState<MedicationWithPatient[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  useEffect(() => {
    if (patients.length > 0) {
      loadAllMedications();
    } else if (!patientsLoading) {
      setIsLoading(false);
    }
  }, [patients, patientsLoading]);

  const loadAllMedications = async () => {
    setIsLoading(true);
    try {
      const medsPromises = patients.map(async (patient) => {
        const meds = await api.getPatientMedications(patient.id).catch(() => []);
        return meds.map((med: any) => ({ medication: med, patient }));
      });

      const results = await Promise.all(medsPromises);
      setAllMedications(results.flat());
    } catch (error) {
      console.error("Failed to load medications:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || patientsLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <Header
        title="Medications"
        subtitle={`${allMedications.length} medication${allMedications.length !== 1 ? "s" : ""} across ${patients.length} patient${patients.length !== 1 ? "s" : ""}`}
      />

      <div className="flex-1 space-y-6 p-6">
        {/* Quick Stats */}
        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Medications</p>
                  <p className="text-3xl font-bold">{allMedications.length}</p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
                  <Pill className="h-6 w-6 text-primary" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Patients on Meds</p>
                  <p className="text-3xl font-bold">
                    {new Set(allMedications.map((m) => m.patient.id)).size}
                  </p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary/10">
                  <User className="h-6 w-6 text-secondary" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Daily Reminders</p>
                  <p className="text-3xl font-bold">
                    {allMedications.reduce(
                      (acc, m) => acc + (m.medication.specific_times?.length || 0),
                      0
                    )}
                  </p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10">
                  <Clock className="h-6 w-6 text-accent" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Medications List */}
        <Card className="border-0 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Pill className="h-5 w-5 text-primary" />
              All Medications
            </CardTitle>
            <Link href="/dashboard/chat">
              <Button className="gap-2">
                <Plus className="h-4 w-4" />
                Add Medication
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {allMedications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="mb-4 rounded-full bg-muted p-4">
                  <Pill className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="mb-2 font-medium">No medications yet</p>
                <p className="mb-4 text-sm text-muted-foreground">
                  Add medications for your patients using the AI assistant
                </p>
                <Link href="/dashboard/chat">
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Medication
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {allMedications.map(({ medication, patient }, index) => (
                  <div
                    key={`${patient.id}-${medication.id}-${index}`}
                    className="flex items-center justify-between rounded-xl border border-border p-4 transition-colors hover:bg-muted/50"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                        <Pill className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold">{medication.drug_name}</h4>
                          {medication.dosage && (
                            <Badge variant="outline">{medication.dosage}</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {medication.frequency?.replace("_", " ")} •{" "}
                          {medication.timing_preference?.replace("_", " ")}
                        </p>
                        {medication.specific_times && medication.specific_times.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {medication.specific_times.map((time: string, i: number) => (
                              <Badge key={i} variant="secondary" className="text-xs">
                                <Clock className="mr-1 h-3 w-3" />
                                {formatTime(time)}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <Link
                      href={`/dashboard/patients/${patient.id}`}
                      className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2 transition-colors hover:bg-muted"
                    >
                      <Avatar fallback={patient.full_name} size="sm" />
                      <span className="text-sm font-medium">{patient.full_name}</span>
                    </Link>
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

