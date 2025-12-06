"use client";

import { useEffect, useState } from "react";
import {
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  Clock,
  FileText,
  X,
  Smartphone,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { api } from "@/lib/api";
import { formatDateTime, getStatusColor } from "@/lib/utils";

export default function VoiceSessionsPage() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedSession, setSelectedSession] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const data = await api.getVoiceSessions(100);
      setSessions(data);
    } catch (error) {
      console.error("Failed to load voice sessions:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getSessionTypeLabel = (type: string) => {
    switch (type) {
      case "onboarding":
        return "Onboarding";
      case "reminder":
        return "Reminder";
      case "escalation":
        return "Escalation";
      default:
        return type;
    }
  };

  const getSessionTypeColor = (type: string) => {
    switch (type) {
      case "onboarding":
        return "bg-secondary/10 text-secondary";
      case "reminder":
        return "bg-primary/10 text-primary";
      case "escalation":
        return "bg-destructive/10 text-destructive";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "pending":
        return "Pending";
      case "active":
        return "In Progress";
      case "completed":
        return "Completed";
      case "missed":
        return "Missed";
      case "declined":
        return "Declined";
      default:
        return status;
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
        title="Voice Sessions"
        subtitle="View all voice conversations and transcripts"
      />

      <div className="flex-1 p-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Session List */}
          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="h-5 w-5 text-primary" />
                Recent Sessions
                <Badge variant="outline" className="ml-2">
                  {sessions.length} total
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {sessions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="mb-4 rounded-full bg-muted p-4">
                    <Phone className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <p className="font-medium">No voice sessions yet</p>
                  <p className="text-sm text-muted-foreground">
                    Voice sessions will appear here when patients answer calls
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {sessions.map((session, index) => (
                    <button
                      key={session.id || index}
                      onClick={() => setSelectedSession(session)}
                      className={`w-full flex items-center justify-between rounded-xl border p-4 text-left transition-all ${
                        selectedSession?.id === session.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:bg-muted/50"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                          <Smartphone className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">
                            {session.patient_name || "Unknown"}
                          </p>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Badge className={getSessionTypeColor(session.session_type)}>
                              {getSessionTypeLabel(session.session_type)}
                            </Badge>
                            <span>•</span>
                            <span>{formatDateTime(session.created_at)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {session.duration_seconds && (
                          <span className="text-sm text-muted-foreground">
                            {Math.floor(session.duration_seconds / 60)}:{(session.duration_seconds % 60).toString().padStart(2, "0")}
                          </span>
                        )}
                        <Badge className={getStatusColor(session.status)}>
                          {getStatusLabel(session.status)}
                        </Badge>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Transcript Viewer */}
          <Card className="border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-secondary" />
                Session Details
              </CardTitle>
              {selectedSession && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedSession(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {!selectedSession ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="mb-4 rounded-full bg-muted p-4">
                    <FileText className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <p className="font-medium">Select a session</p>
                  <p className="text-sm text-muted-foreground">
                    Click on a session to view its transcript
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Session Info */}
                  <div className="rounded-xl bg-muted/50 p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <Avatar
                        fallback={selectedSession.patient_name || "P"}
                        size="lg"
                      />
                      <div>
                        <p className="font-semibold">
                          {selectedSession.patient_name || "Unknown"}
                        </p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Badge className={getSessionTypeColor(selectedSession.session_type)}>
                            {getSessionTypeLabel(selectedSession.session_type)}
                          </Badge>
                          <Badge className={getStatusColor(selectedSession.status)}>
                            {getStatusLabel(selectedSession.status)}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Started</p>
                        <p className="font-medium">
                          {selectedSession.started_at 
                            ? formatDateTime(selectedSession.started_at)
                            : "Not started"}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Duration</p>
                        <p className="font-medium">
                          {selectedSession.duration_seconds
                            ? `${Math.floor(selectedSession.duration_seconds / 60)}:${(selectedSession.duration_seconds % 60).toString().padStart(2, "0")}`
                            : "N/A"}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Transcript */}
                  <div className="space-y-2">
                    <h4 className="font-semibold">Transcript</h4>
                    <div className="rounded-xl border border-border p-4 max-h-64 overflow-y-auto">
                      {selectedSession.transcript ? (
                        <p className="text-sm whitespace-pre-wrap">
                          {selectedSession.transcript}
                        </p>
                      ) : (
                        <p className="text-sm text-muted-foreground italic">
                          No transcript available
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Extracted Data */}
                  {selectedSession.extracted_data && Object.keys(selectedSession.extracted_data).length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-semibold">Extracted Data</h4>
                      <div className="rounded-xl border border-border p-4">
                        <pre className="text-xs overflow-x-auto">
                          {JSON.stringify(selectedSession.extracted_data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
