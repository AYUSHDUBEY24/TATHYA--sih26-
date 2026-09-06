"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, apiFetch } from "@/lib/auth";
import {
  AuditLogEntry,
  CASE_STATUSES,
  CaseListItem,
  DocumentItem,
} from "@/lib/api-types";
import { useAuth } from "@/lib/useAuth";
import { parseBackendDate } from "@/lib/format";
import { ActivityTimeline, KpiCard, StatusBreakdown } from "@/components/dashboard";
import { CaseCard } from "@/components/CaseCard";
import { EmptyState, PageHeader, Skeleton } from "@/components/ui";
import {
  IconAlertTriangle,
  IconCheckCircle,
  IconFolder,
  IconFileText,
  IconPlus,
} from "@/components/icons";

/**
 * ACTIVE statuses per the case lifecycle (OPEN → COURT_STAGE).
 * CLOSED / ARCHIVED are excluded from "Active Cases".
 */
const ACTIVE_STATUSES = new Set([
  "OPEN",
  "UNDER_INVESTIGATION",
  "UNDER_REVIEW",
  "CHARGESHEET_FILED",
  "COURT_STAGE",
]);

/**
 * Dashboard — all numbers are derived from existing, permitted endpoints:
 *   /api/cases, /api/documents, /api/audit (ADMIN only).
 * There is intentionally NO /api/dashboard call (the backend does not
 * expose one) and no fabricated statistics.
 */
export default function Dashboard() {
  const { user } = useAuth();
  const isAdmin = user?.role?.name === "ADMIN";

  const [cases, setCases] = useState<CaseListItem[] | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[] | null>(null);
  const [recentActivity, setRecentActivity] = useState<AuditLogEntry[] | null>(null);
  const [integrityAlerts, setIntegrityAlerts] = useState<number | null>(null);
  const [auditRestricted, setAuditRestricted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      // Wait for the stored user so the ADMIN branch is evaluated correctly.
      if (!user) return;
      try {
        const [casesData, docsData] = await Promise.all([
          apiFetch<CaseListItem[]>("/api/cases"),
          apiFetch<DocumentItem[]>("/api/documents"),
        ]);
        if (cancelled) return;
        setCases(casesData);
        setDocuments(docsData);

        if (isAdmin) {
          const [alertsRes, activityRes] = await Promise.allSettled([
            apiFetch<AuditLogEntry[]>("/api/audit?action=INTEGRITY_FAILED&limit=200"),
            apiFetch<AuditLogEntry[]>("/api/audit?limit=10"),
          ]);
          if (cancelled) return;
          if (alertsRes.status === "fulfilled") {
            setIntegrityAlerts(alertsRes.value.length);
          }
          if (activityRes.status === "fulfilled") {
            setRecentActivity(activityRes.value);
          } else {
            setAuditRestricted(true);
          }
        } else {
          setAuditRestricted(true);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load dashboard");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [user, isAdmin]);

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl">
        <div className="mb-6 flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-52" />
            <Skeleton className="h-4 w-80" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          <Skeleton className="h-64 rounded-xl lg:col-span-2" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl">
        <div
          role="alert"
          className="rounded-xl border border-amber-200 bg-amber-50 p-6"
        >
          <div className="flex items-start gap-3">
            <IconAlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
            <div>
              <p className="font-semibold text-amber-900">
                Could not load dashboard
              </p>
              <p className="mt-1 text-sm text-amber-800">{error}</p>
              <Link
                href="/login"
                className="mt-3 inline-block text-sm font-medium text-blue-600 underline-offset-2 hover:underline"
              >
                Sign in
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const totalCases = cases?.length ?? 0;
  const activeCases =
    cases?.filter((c) => ACTIVE_STATUSES.has(c.status)).length ?? 0;
  const totalDocuments = documents?.length ?? 0;

  const statusCounts: Record<string, number> = {};
  for (const status of CASE_STATUSES) statusCounts[status] = 0;
  for (const c of cases ?? []) {
    if (statusCounts[c.status] !== undefined) statusCounts[c.status] += 1;
  }

  const recentCases = [...(cases ?? [])]
    .sort(
      (a, b) =>
        (parseBackendDate(b.updated_at)?.getTime() ?? 0) -
        (parseBackendDate(a.updated_at)?.getTime() ?? 0)
    )
    .slice(0, 6);

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        title="Tathya Dashboard — Case Overview"
        description="Where Facts Find Forever — an overview of cases, documents and integrity across data you are authorized to access."
        action={
          <Link href="/cases/new" className="btn btn-primary btn-md">
            <IconPlus className="h-4 w-4" />
            New Case
          </Link>
        }
      />

      {/* Honest KPI cards — real data only */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Active Cases"
          value={activeCases}
          tone="blue"
          icon={<IconFolder className="h-5 w-5" />}
          hint="OPEN → COURT_STAGE lifecycle"
        />
        <KpiCard
          label="Total Cases"
          value={totalCases}
          tone="slate"
          icon={<IconCheckCircle className="h-5 w-5" />}
          hint="Visible to your role"
        />
        <KpiCard
          label="Total Documents"
          value={totalDocuments}
          tone="emerald"
          icon={<IconFileText className="h-5 w-5" />}
          hint="Across your authorized cases"
        />
        {integrityAlerts === null ? (
          <KpiCard
            label="Integrity Alerts"
            value="—"
            tone="amber"
            icon={<IconAlertTriangle className="h-5 w-5" />}
            hint="Available to administrators only"
          />
        ) : (
          <KpiCard
            label="Integrity Alerts"
            value={integrityAlerts}
            tone="rose"
            icon={<IconAlertTriangle className="h-5 w-5" />}
            hint="INTEGRITY_FAILED audit events"
          />
        )}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <div className="space-y-8 lg:col-span-2">
          <StatusBreakdown counts={statusCounts} total={totalCases} />

          {/* Recent cases from actual /api/cases data */}
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900">
                Recent Cases
              </h2>
              <Link
                href="/cases"
                className="text-sm font-medium text-blue-600 hover:underline"
              >
                View all →
              </Link>
            </div>
            {recentCases.length === 0 ? (
              <EmptyState
                title="No cases yet"
                description="Cases you create, are assigned to, or are a member of will appear here."
                action={
                  <Link href="/cases/new" className="btn btn-primary btn-md">
                    <IconPlus className="h-4 w-4" />
                    Create your first case
                  </Link>
                }
              />
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                {recentCases.map((c) => (
                  <CaseCard key={c.id} item={c} />
                ))}
              </div>
            )}
          </section>
        </div>

        <ActivityTimeline events={recentActivity} restricted={auditRestricted} />
      </div>
    </div>
  );
}
