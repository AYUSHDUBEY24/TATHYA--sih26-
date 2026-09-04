"use client";

import React from "react";

// --- Button ---
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "destructive" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className = "", ...props }, ref) => {
    const base = "btn";
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
        className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
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
    <div className={`border-b border-border px-6 py-4 ${className}`}>{children}</div>
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
    <h3 className={`text-lg font-semibold text-foreground ${className}`}>
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
  return <div className={`px-6 py-4 ${className}`}>{children}</div>;
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
  return (
    <span className={`${variants[variant]} ${className}`}>{children}</span>
  );
}

// --- Input ---
export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className = "", ...props }, ref) => {
  return <input ref={ref} className={`input ${className}`} {...props} />;
});
Input.displayName = "Input";

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
      {icon && <div className="mb-4 text-muted-foreground">{icon}</div>}
      <h3 className="text-lg font-medium text-foreground">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
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

// --- Stat Card ---
export function StatCard({
  label,
  value,
  icon,
  trend,
}: {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: { value: string; positive?: boolean };
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        {icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
            {icon}
          </div>
        )}
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          {trend && (
            <p
              className={`text-xs ${trend.positive ? "text-success" : "text-destructive"}`}
            >
              {trend.value}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// --- Page Header ---
export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold text-foreground">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {action && <div className="flex gap-2">{action}</div>}
    </div>
  );
}

// --- Status Badge Helper ---
export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  let variant: "default" | "success" | "warning" | "destructive" | "info" | "muted" = "default";
  if (["verified", "active", "open", "completed", "success"].includes(normalized)) {
    variant = "success";
  } else if (["pending", "under_investigation", "under_review", "processing"].includes(normalized)) {
    variant = "warning";
  } else if (["failed", "closed", "archived", "rejected"].includes(normalized)) {
    variant = "destructive";
  } else if (["chargesheet_filed", "court_stage"].includes(normalized)) {
    variant = "info";
  }
  return <Badge variant={variant}>{status.replace(/_/g, " ")}</Badge>;
}
