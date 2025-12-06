"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Plus,
  Phone,
  User,
  Search,
  Trash2,
  PhoneCall,
  Smartphone,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { usePatientStore } from "@/lib/store";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const patientSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters"),
  phone_number: z.string().min(10, "Please enter a valid phone number"),
});

type PatientForm = z.infer<typeof patientSchema>;

export default function PatientsPage() {
  const { patients, fetchPatients, addPatient, removePatient, isLoading } = usePatientStore();
  const [showAddForm, setShowAddForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [triggeringCall, setTriggeringCall] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PatientForm>({
    resolver: zodResolver(patientSchema),
  });

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  const onSubmit = async (data: PatientForm) => {
    setIsSubmitting(true);
    try {
      await addPatient(data);
      reset();
      setShowAddForm(false);
    } catch (error) {
      console.error("Failed to add patient:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm("Are you sure you want to remove this patient?")) {
      await removePatient(id);
    }
  };

  const handleTriggerCall = async (patient: any) => {
    if (!patient.has_device) {
      alert("Patient has not registered their device yet. They need to install the app first.");
      return;
    }
    
    setTriggeringCall(patient.id);
    try {
      await api.triggerCall(patient.id, patient.onboarding_completed ? "reminder" : "onboarding");
      alert("Call triggered! The patient will receive an incoming call on their app.");
      fetchPatients();
    } catch (error: any) {
      console.error("Failed to trigger call:", error);
      alert(error.message || "Failed to trigger call. Please try again.");
    } finally {
      setTriggeringCall(null);
    }
  };

  const filteredPatients = patients.filter((patient) =>
    patient.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    patient.phone_number.includes(searchQuery)
  );

  return (
    <div className="flex flex-col">
      <Header
        title="Patients"
        subtitle={`Managing ${patients.length} patient${patients.length !== 1 ? "s" : ""}`}
      />

      <div className="flex-1 space-y-6 p-6">
        {/* Actions Bar */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative max-w-sm flex-1">
            <Input
              placeholder="Search patients..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={<Search className="h-4 w-4" />}
            />
          </div>
          <Button onClick={() => setShowAddForm(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Patient
          </Button>
        </div>

        {/* Add Patient Form */}
        {showAddForm && (
          <Card className="border-2 border-primary/20 shadow-lg animate-fade-in">
            <CardHeader>
              <CardTitle>Add New Patient</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Full Name</label>
                    <Input
                      placeholder="John Doe"
                      icon={<User className="h-4 w-4" />}
                      error={errors.full_name?.message}
                      {...register("full_name")}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Phone Number</label>
                    <Input
                      placeholder="+1 (555) 000-0000"
                      icon={<Phone className="h-4 w-4" />}
                      error={errors.phone_number?.message}
                      {...register("phone_number")}
                    />
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button type="submit" isLoading={isSubmitting}>
                    Add Patient
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowAddForm(false);
                      reset();
                    }}
                  >
                    Cancel
                  </Button>
                </div>

                <p className="text-sm text-muted-foreground">
                  📱 After adding, the patient will need to install the Calla app on their phone. 
                  Once they register their device, you can trigger voice calls.
                </p>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Patients List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : filteredPatients.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="mb-4 rounded-full bg-muted p-4">
                <User className="h-8 w-8 text-muted-foreground" />
              </div>
              <p className="mb-2 text-lg font-medium">
                {searchQuery ? "No patients found" : "No patients yet"}
              </p>
              <p className="mb-4 text-sm text-muted-foreground">
                {searchQuery
                  ? "Try a different search term"
                  : "Add your first patient to get started"}
              </p>
              {!searchQuery && (
                <Button onClick={() => setShowAddForm(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Patient
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredPatients.map((patient, index) => (
              <Card
                key={patient.id}
                hover
                className="group animate-fade-in"
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <Link
                      href={`/dashboard/patients/${patient.id}`}
                      className="flex items-center gap-4"
                    >
                      <Avatar fallback={patient.full_name} size="lg" />
                      <div>
                        <h3 className="font-semibold group-hover:text-primary transition-colors">
                          {patient.full_name}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          {patient.phone_number}
                        </p>
                      </div>
                    </Link>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => handleTriggerCall(patient)}
                        disabled={triggeringCall === patient.id || !patient.has_device}
                        title={patient.has_device ? "Call patient" : "Patient needs to install app"}
                      >
                        <PhoneCall className={`h-4 w-4 ${triggeringCall === patient.id ? "animate-pulse" : ""} ${!patient.has_device ? "opacity-50" : ""}`} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive hover:text-destructive"
                        onClick={() => handleDelete(patient.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center justify-between gap-2 flex-wrap">
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
                      {patient.has_device ? "App" : "No App"}
                    </Badge>
                  </div>

                  <div className="mt-3 text-xs text-muted-foreground">
                    Added {formatDate(patient.created_at)}
                  </div>

                  {patient.onboarding_completed && (
                    <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                      {patient.wake_time && (
                        <div className="rounded-lg bg-muted/50 p-2">
                          <span className="text-muted-foreground">Wake:</span>{" "}
                          {patient.wake_time}
                        </div>
                      )}
                      {patient.breakfast_time && (
                        <div className="rounded-lg bg-muted/50 p-2">
                          <span className="text-muted-foreground">Breakfast:</span>{" "}
                          {patient.breakfast_time}
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
