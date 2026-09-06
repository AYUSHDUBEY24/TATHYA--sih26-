"use client";

import React from "react";
import { prettifyEnum } from "@/lib/format";

// --- Button ---
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "destructive" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className = "", ...props }, ref) => {
    const variants = {
      primary: "btn-primary",
      secondary: "btn-secondary",
      destructive: "btn-destructive",
      ghost: "btn-ghost",
    };
    const sizes = { sm: "btn-sm", md: "btn-md", lg: "btn-lg" };
    return (
      <button
        ref={ref}
        className={`btn ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

// --- Card ---
export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={`card ${className}`}>{children}</div>;
}

export function CardHeader({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`border-b border-slate-100 px-5 py-4 ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h3 className={`text-base font-semibold text-slate-900 ${className}`}>
      {children}
    </h3>
  );
}

export function CardContent({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={`px-5 py-4 ${className}`}>{children}</div>;
}

// --- Badge ---
export function Badge({
  variant = "default",
  children,
  className = "",
}: {
  variant?: "default" | "success" | "warning" | "destructive" | "info" | "muted";
  children: React.ReactNode;
  className?: string;
}) {
  const variants = {
    default: "badge-default",
    success: "badge-success",
    warning: "badge-warning",
    destructive: "badge-destructive",
    info: "badge-info",
    muted: "badge-muted",
  };
  return <span className={`badge ${variants[variant]} ${className}`}>{children}</span>;
}

// --- Input (white bg / slate-900 text / slate-400 placeholder / slate-300 border / blue focus) ---
export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className = "", ...props }, ref) => {
  return <input ref={ref} className={`input ${className}`} {...props} />;
});
Input.displayName = "Input";

// --- Select ---
export const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className = "", ...props }, ref) => {
  return <select ref={ref} className={`input ${className}`} {...props} />;
});
Select.displayName = "Select";

// --- Textarea ---
export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className = "", ...props }, ref) => {
  return <textarea ref={ref} className={`input ${className}`} {...props} />;
});
Textarea.displayName = "Textarea";

// --- Label ---
export function Label({
  children,
  htmlFor,
  className = "",
}: {
  children: React.ReactNode;
  htmlFor?: string;
  className?: string;
}) {
  return (
    <label htmlFor={htmlFor} className={`label ${className}`}>
      {children}
    </label>
  );
}

// --- Empty State ---
export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}) {
  return (
    <div className="empty-state">
      {icon && <div className="mb-3 text-slate-400">{icon}</div>}
      <h3 className="text-base font-medium text-slate-900">{title}</h3>
      {description && (
        <p className="mt-1 max-w-md text-sm text-slate-500">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// --- Loading Skeleton ---
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="table-container">
      <div className="space-y-3 p-4">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    </div>
  );
}

// --- Spinner ---
export function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <span
      className={`inline-block animate-spin rounded-full border-2 border-blue-500 border-t-transparent ${className}`}
      aria-hidden="true"
    />
  );
}

// --- Page Header ---
export function PageHeader({
  title,
  description,
  action,
  eyebrow,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  eyebrow?: string;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        {eyebrow && (
          <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
            {eyebrow}
          </p>
        )}
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-slate-600">{description}</p>
        )}
      </div>
      {action && <div className="flex flex-wrap gap-2">{action}</div>}
    </div>
  );
}

// --- Status Badge (single source of truth for status colors) ---
const STATUS_BADGE: Record<string, string> = {
  OPEN: "badge badge-info",
  UNDER_INVESTIGATION: "badge badge-warning",
  UNDER_REVIEW: "badge bg-violet-100 text-violet-700",
  CHARGESHEET_FILED: "badge bg-orange-100 text-orange-700",
  COURT_STAGE: "badge bg-fuchsia-100 text-fuchsia-700",
  CLOSED: "badge badge-muted",
  ARCHIVED: "badge badge-muted",
  VERIFIED: "badge badge-success",
  INTEGRITY_FAILURE: "badge badge-destructive",
  ACTIVE: "badge badge-success",
  PENDING: "badge badge-warning",
  FAILED: "badge badge-destructive",
  CONFIRMED: "badge badge-success",
};

export function StatusBadge({
  status,
  className = "",
}: {
  status: string;
  className?: string;
}) {
  const base = STATUS_BADGE[status] ?? "badge badge-muted";
  return <span className={`${base} ${className}`}>{prettifyEnum(status)}</span>;
}
