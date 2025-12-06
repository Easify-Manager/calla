"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  error?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, icon, error, ...props }, ref) => {
    return (
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            {icon}
          </div>
        )}
        <input
          type={type}
          className={cn(
            "flex h-11 w-full rounded-xl border-2 border-border bg-card px-4 py-2 text-sm transition-all duration-200",
            "placeholder:text-muted-foreground/60",
            "focus:border-primary/50 focus:outline-none focus:ring-4 focus:ring-primary/10",
            "disabled:cursor-not-allowed disabled:opacity-50",
            icon && "pl-10",
            error && "border-destructive focus:border-destructive focus:ring-destructive/10",
            className
          )}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="mt-1.5 text-xs text-destructive">{error}</p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };

