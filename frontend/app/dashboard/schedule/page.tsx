"use client";

import { useEffect, useState } from "react";
import { Calendar, Clock, CheckCircle, AlertCircle, Phone } from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { api } from "@/lib/api";
import { formatDateTime, getStatusColor } from "@/lib/utils";

export default function SchedulePage() {
  const [todayReminders, setTodayReminders] = useState<any[]>([]);
  const [upcomingReminders, setUpcomingReminders] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadReminders();
  }, []);

  const loadReminders = async () => {
    setIsLoading(true);
    try {
      const [today, upcoming] = await Promise.all([
        api.getTodayReminders().catch(() => []),
        api.getUpcomingReminders(7).catch(() => []),
      ]);
      setTodayReminders(today);
      setUpcomingReminders(upcoming.filter(
        (r: any) => new Date(r.scheduled_time).toDateString() !== new Date().toDateString()
      ));
    } catch (error) {
      console.error("Failed to load reminders:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMarkTaken = async (reminderId: string) => {
    try {
      await api.markReminderTaken(reminderId);
      loadReminders();
    } catch (error) {
      console.error("Failed to mark as taken:", error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "confirmed":
        return <CheckCircle className="h-4 w-4 text-emerald-500" />;
      case "missed":
      case "escalated":
        return <AlertCircle className="h-4 w-4 text-rose-500" />;
      case "calling":
        return <Phone className="h-4 w-4 text-sky-500 animate-pulse" />;
      default:
        return <Clock className="h-4 w-4 text-amber-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <Header
        title="Schedule"
        subtitle="Manage medication reminders for your patients"
      />

      <div className="flex-1 space-y-6 p-6">
        {/* Today's Schedule */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-primary" />
              Today's Schedule
              <Badge variant="outline" className="ml-2">
                {todayReminders.length} reminders
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {todayReminders.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="mb-4 rounded-full bg-muted p-4">
                  <Calendar className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="font-medium">No reminders scheduled for today</p>
                <p className="text-sm text-muted-foreground">
                  Add medications to patients to create reminder schedules
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {todayReminders.map((reminder, index) => (
                  <div
                    key={reminder.id || index}
                    className="flex items-center justify-between rounded-xl border border-border p-4 transition-colors hover:bg-muted/50"
                  >
                    <div className="flex items-center gap-4">
                      {getStatusIcon(reminder.status)}
                      <Avatar
                        fallback={reminder.patients?.full_name || "P"}
                        size="md"
                      />
                      <div>
                        <p className="font-medium">
                          {reminder.patients?.full_name || "Patient"}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {reminder.medications?.drug_name} •{" "}
                          {reminder.medications?.dosage}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="font-medium">
                          {formatDateTime(reminder.scheduled_time)}
                        </p>
                        <Badge className={getStatusColor(reminder.status)}>
                          {reminder.status}
                        </Badge>
                      </div>

                      {reminder.status === "pending" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMarkTaken(reminder.id)}
                        >
                          <CheckCircle className="mr-1 h-4 w-4" />
                          Mark Taken
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Upcoming Schedule */}
        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-secondary" />
              Upcoming (Next 7 Days)
              <Badge variant="outline" className="ml-2">
                {upcomingReminders.length} reminders
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {upcomingReminders.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="mb-4 rounded-full bg-muted p-4">
                  <Clock className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="font-medium">No upcoming reminders</p>
                <p className="text-sm text-muted-foreground">
                  Future reminders will appear here
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {upcomingReminders.slice(0, 10).map((reminder, index) => (
                  <div
                    key={reminder.id || index}
                    className="flex items-center justify-between rounded-xl border border-border p-4 transition-colors hover:bg-muted/50"
                  >
                    <div className="flex items-center gap-4">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <Avatar
                        fallback={reminder.patients?.full_name || "P"}
                        size="md"
                      />
                      <div>
                        <p className="font-medium">
                          {reminder.patients?.full_name || "Patient"}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {reminder.medications?.drug_name} •{" "}
                          {reminder.medications?.dosage}
                        </p>
                      </div>
                    </div>

                    <div className="text-right">
                      <p className="font-medium">
                        {formatDateTime(reminder.scheduled_time)}
                      </p>
                      <Badge variant="outline">{reminder.status}</Badge>
                    </div>
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

