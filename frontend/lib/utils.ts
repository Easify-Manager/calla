import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTime(time: string | null | undefined): string {
  if (!time) return "—";
  try {
    const [hours, minutes] = time.split(":");
    const h = parseInt(hours);
    const ampm = h >= 12 ? "PM" : "AM";
    const hour12 = h % 12 || 12;
    return `${hour12}:${minutes} ${ampm}`;
  } catch {
    return time;
  }
}

export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatDateTime(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function getAdherenceColor(rate: number): string {
  if (rate >= 90) return "text-emerald-500";
  if (rate >= 70) return "text-amber-500";
  return "text-rose-500";
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "confirmed":
      return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
    case "pending":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20";
    case "missed":
    case "escalated":
      return "bg-rose-500/10 text-rose-500 border-rose-500/20";
    case "calling":
      return "bg-sky-500/10 text-sky-500 border-sky-500/20";
    default:
      return "bg-slate-500/10 text-slate-500 border-slate-500/20";
  }
}

