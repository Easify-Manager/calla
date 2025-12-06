"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Users,
  Pill,
  Calendar,
  Smartphone,
  MessageSquare,
  Settings,
  Flower2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Patients", href: "/dashboard/patients", icon: Users },
  { name: "Medications", href: "/dashboard/medications", icon: Pill },
  { name: "Schedule", href: "/dashboard/schedule", icon: Calendar },
  { name: "Voice Sessions", href: "/dashboard/calls", icon: Smartphone },
  { name: "Add Medication", href: "/dashboard/chat", icon: MessageSquare },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-border bg-card">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b border-border px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-secondary">
          <Flower2 className="h-6 w-6 text-white" />
        </div>
        <span className="text-xl font-bold tracking-tight">Calla</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-primary text-primary-foreground shadow-md"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <item.icon
                className={cn(
                  "h-5 w-5 shrink-0 transition-colors",
                  isActive
                    ? "text-primary-foreground"
                    : "text-muted-foreground group-hover:text-foreground"
                )}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-border p-4">
        <div className="rounded-xl bg-gradient-to-br from-primary/10 to-secondary/10 p-4">
          <p className="text-sm font-medium">Gemini 2.0 Powered</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Real-time voice AI via WebSocket
          </p>
        </div>
      </div>
    </aside>
  );
}
