"use client";

import { useEffect, useState, useRef } from "react";
import { useSearchParams } from "next/navigation";
import {
  Send,
  Bot,
  User,
  Pill,
  Sparkles,
  CheckCircle,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar } from "@/components/ui/avatar";
import { usePatientStore } from "@/lib/store";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
  medication_saved?: boolean;
}

export default function ChatPage() {
  const searchParams = useSearchParams();
  const preselectedPatientId = searchParams.get("patient");
  
  const { patients, fetchPatients } = usePatientStore();
  const [selectedPatient, setSelectedPatient] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  useEffect(() => {
    if (preselectedPatientId) {
      setSelectedPatient(preselectedPatientId);
    }
  }, [preselectedPatientId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !selectedPatient || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const allMessages = [...messages, userMessage].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await api.sendChatMessage(selectedPatient, allMessages);

      const assistantMessage: Message = {
        role: "assistant",
        content: response.message,
        medication_saved: response.medication_saved,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (response.medication_saved) {
        // Show success and reset after a moment
        setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: "Would you like to add another medication? Just tell me about it!",
            },
          ]);
        }, 1500);
      }
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "I'm sorry, I encountered an error. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startNewConversation = () => {
    setMessages([]);
  };

  return (
    <div className="flex flex-col h-screen">
      <Header
        title="AI Assistant"
        subtitle="Add medications through natural conversation"
      />

      <div className="flex-1 flex flex-col p-6 pb-0 overflow-hidden">
        {/* Patient Selection */}
        {!selectedPatient ? (
          <Card className="flex-1 border-0 shadow-lg flex items-center justify-center">
            <CardContent className="text-center py-12">
              <div className="mb-6 inline-flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-primary/20 to-secondary/20">
                <Sparkles className="h-10 w-10 text-primary" />
              </div>
              <h2 className="mb-2 text-2xl font-bold">AI Prescription Assistant</h2>
              <p className="mb-6 text-muted-foreground max-w-md mx-auto">
                I can help you add medications for your patients through natural conversation.
                Just tell me about the medication and I'll handle the rest.
              </p>

              <div className="max-w-sm mx-auto space-y-3">
                <p className="text-sm font-medium text-left">Select a patient:</p>
                {patients.map((patient) => (
                  <button
                    key={patient.id}
                    onClick={() => setSelectedPatient(patient.id)}
                    className="w-full flex items-center gap-3 rounded-xl border border-border p-4 transition-all hover:border-primary/30 hover:bg-primary/5 text-left"
                  >
                    <Avatar fallback={patient.full_name} size="md" />
                    <div>
                      <p className="font-medium">{patient.full_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {patient.phone_number}
                      </p>
                    </div>
                  </button>
                ))}

                {patients.length === 0 && (
                  <p className="text-sm text-muted-foreground py-4">
                    No patients yet. Add a patient first to use the AI assistant.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Selected Patient Banner */}
            <div className="mb-4 flex items-center justify-between rounded-xl bg-card border border-border p-4">
              <div className="flex items-center gap-3">
                <Avatar
                  fallback={patients.find((p) => p.id === selectedPatient)?.full_name || "P"}
                  size="md"
                />
                <div>
                  <p className="font-medium">
                    Adding medication for{" "}
                    {patients.find((p) => p.id === selectedPatient)?.full_name}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Describe the medication and I'll help you add it
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedPatient("");
                  startNewConversation();
                }}
              >
                Change Patient
              </Button>
            </div>

            {/* Chat Messages */}
            <Card className="flex-1 border-0 shadow-lg overflow-hidden flex flex-col">
              <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center">
                    <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                      <Bot className="h-8 w-8 text-primary" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">
                      How can I help you today?
                    </h3>
                    <p className="text-muted-foreground max-w-sm mb-6">
                      Tell me about the medication you want to add. For example:
                    </p>
                    <div className="space-y-2 text-sm">
                      <button
                        onClick={() => setInput("Add metformin 500mg twice daily")}
                        className="block w-full rounded-xl bg-muted/50 px-4 py-3 text-left hover:bg-muted transition-colors"
                      >
                        "Add metformin 500mg twice daily"
                      </button>
                      <button
                        onClick={() => setInput("My patient takes lisinopril with breakfast")}
                        className="block w-full rounded-xl bg-muted/50 px-4 py-3 text-left hover:bg-muted transition-colors"
                      >
                        "My patient takes lisinopril with breakfast"
                      </button>
                      <button
                        onClick={() => setInput("Add aspirin 81mg once a day")}
                        className="block w-full rounded-xl bg-muted/50 px-4 py-3 text-left hover:bg-muted transition-colors"
                      >
                        "Add aspirin 81mg once a day"
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    {messages.map((message, index) => (
                      <div
                        key={index}
                        className={cn(
                          "flex gap-3 animate-fade-in",
                          message.role === "user" ? "justify-end" : "justify-start"
                        )}
                      >
                        {message.role === "assistant" && (
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary to-secondary">
                            <Bot className="h-4 w-4 text-white" />
                          </div>
                        )}
                        <div
                          className={cn(
                            "max-w-[80%] rounded-2xl px-4 py-3",
                            message.role === "user"
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted"
                          )}
                        >
                          <p className="whitespace-pre-wrap">{message.content}</p>
                          {message.medication_saved && (
                            <div className="mt-2 flex items-center gap-2 text-emerald-600">
                              <CheckCircle className="h-4 w-4" />
                              <span className="text-sm font-medium">
                                Medication saved!
                              </span>
                            </div>
                          )}
                        </div>
                        {message.role === "user" && (
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                            <User className="h-4 w-4" />
                          </div>
                        )}
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary to-secondary">
                          <Bot className="h-4 w-4 text-white" />
                        </div>
                        <div className="rounded-2xl bg-muted px-4 py-3">
                          <div className="flex gap-1">
                            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40" />
                            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:0.2s]" />
                            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:0.4s]" />
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </CardContent>

              {/* Input */}
              <div className="border-t border-border p-4">
                <div className="flex gap-3">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Tell me about the medication..."
                    className="flex-1"
                    disabled={isLoading}
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!input.trim() || isLoading}
                    className="shrink-0"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}

