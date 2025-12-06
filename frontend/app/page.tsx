"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Phone, Shield, Clock, Users, ArrowRight, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/store";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  return (
    <div className="min-h-screen mesh-gradient">
      {/* Navigation */}
      <nav className="fixed top-0 z-50 w-full border-b border-border/50 bg-card/50 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-secondary shadow-lg shadow-primary/25">
              <Phone className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold gradient-text">MedVoice</span>
          </div>
          
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative flex min-h-screen flex-col items-center justify-center px-6 pt-16">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 right-0 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
          <div className="absolute -bottom-40 left-0 h-96 w-96 rounded-full bg-secondary/10 blur-3xl" />
        </div>

        <div className="relative z-10 mx-auto max-w-4xl text-center stagger-children">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-2 text-sm text-primary">
            <span className="flex h-2 w-2 rounded-full bg-primary animate-pulse" />
            Voice-First Medication Adherence
          </div>

          <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight md:text-6xl lg:text-7xl">
            Patients just answer
            <br />
            <span className="gradient-text">the phone</span>
          </h1>

          <p className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground md:text-xl">
            MedVoice uses AI-powered phone calls to remind patients to take their medications. 
            No apps to learn. No notifications to dismiss. Just friendly voice reminders that work.
          </p>

          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link href="/register">
              <Button size="lg" className="gap-2 text-base">
                Start Free Trial
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="gap-2 text-base">
              Watch Demo
            </Button>
          </div>

          {/* Social proof */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-8 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-success" />
              <span>HIPAA Compliant</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-success" />
              <span>No Patient App Required</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-success" />
              <span>Setup in 5 Minutes</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-24 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold md:text-4xl">
              Why phone calls beat notifications
            </h2>
            <p className="mx-auto max-w-2xl text-muted-foreground">
              Push notifications have a 10% open rate. Phone calls have near-100% attention capture.
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3 stagger-children">
            <div className="group rounded-2xl border border-border bg-card p-8 transition-all duration-300 hover:border-primary/30 hover:shadow-xl hover:shadow-primary/5">
              <div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5">
                <Phone className="h-7 w-7 text-primary" />
              </div>
              <h3 className="mb-3 text-xl font-semibold">Voice-First Design</h3>
              <p className="text-muted-foreground">
                Patients interact through natural phone conversations. No apps, no accounts, 
                no learning curve. Just answer the phone.
              </p>
            </div>

            <div className="group rounded-2xl border border-border bg-card p-8 transition-all duration-300 hover:border-secondary/30 hover:shadow-xl hover:shadow-secondary/5">
              <div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-secondary/20 to-secondary/5">
                <Shield className="h-7 w-7 text-secondary" />
              </div>
              <h3 className="mb-3 text-xl font-semibold">Caregiver Escalation</h3>
              <p className="text-muted-foreground">
                If a patient doesn't answer after 3 attempts, we automatically alert their 
                caregiver. Peace of mind for families.
              </p>
            </div>

            <div className="group rounded-2xl border border-border bg-card p-8 transition-all duration-300 hover:border-accent/30 hover:shadow-xl hover:shadow-accent/5">
              <div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-accent/20 to-accent/5">
                <Clock className="h-7 w-7 text-accent" />
              </div>
              <h3 className="mb-3 text-xl font-semibold">Habit-Aware Scheduling</h3>
              <p className="text-muted-foreground">
                Our AI learns patient routines through conversation. Medications are scheduled 
                around breakfast, lunch, and dinner times.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-24 px-6">
        <div className="mx-auto max-w-4xl">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary to-secondary p-12 text-center text-white shadow-2xl shadow-primary/25">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzBoLTZ2Nmg2di02em0wLTEyaC02djZoNnYtNnoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-30" />
            
            <div className="relative z-10">
              <h2 className="mb-4 text-3xl font-bold md:text-4xl">
                Ready to improve medication adherence?
              </h2>
              <p className="mx-auto mb-8 max-w-xl text-white/80">
                Join caregivers who trust MedVoice to keep their patients on track. 
                Start your free trial today.
              </p>
              <Link href="/register">
                <Button size="lg" className="bg-white text-primary hover:bg-white/90 shadow-xl">
                  Get Started Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12 px-6">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 md:flex-row">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-secondary">
              <Phone className="h-4 w-4 text-white" />
            </div>
            <span className="font-semibold">MedVoice</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2024 MedVoice. Built for Tech Award Hackathon.
          </p>
        </div>
      </footer>
    </div>
  );
}
