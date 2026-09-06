"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/auth";
import { CASE_STATUSES, CaseListItem } from "@/lib/api-types";
import { CaseCard } from "@/components/CaseCard";
import { EmptyState, PageHeader, Skeleton, StatusBadge } from "@/components/ui";
import { IconLayoutGrid, IconList, IconPlus, IconSearch } from "@/components/icons";
import { formatDateTime } from "@/lib/format";

/**
 * Cases list — search/status filters run client-side over the already
 * loaded (permission-filtered by the backend) case list. No fake data.
 */
export default function CasesPage() {
  const [cases, setCases] = useState<CaseListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [view, setView] = useState<"grid" | "list">("grid");

  useEffect(() => {
    apiFetch<CaseListItem[]>("/api/cases")
      .then(setCases)
      .catch((err: Error) => setError(err.message));
  }, []);

  const filtered = useMemo(() => {
    if (!cases) return null;
    const q = query.trim().toLowerCase();
    return cases.filter((c) => {
      if (statusFilter !== "ALL" && c.status !== statusFilter) return false;
      if (!q) return true;
      return (
        c.case_number.toLowerCase().includes(q) ||
        c.title.toLowerCase().includes(q) ||
        (c.crime_type ?? "").toLowerCase().includes(q) ||
        (c.police_station ?? "").toLowerCase().includes(q)
      );
    });
  }, [cases, query, statusFilter]);

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow="Investigation"
        title="Cases"
        description="All cases you are authorized to access, based on your role and assignments."
        action={
          <Link href="/cases/new" className="btn btn-primary btn-md">
            <IconPlus className="h-4 w-4" />
            New case
          </Link>
        }
      />

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          {error}{" "}
          <Link href="/login" className="font-medium underline">
            Sign in
          </Link>
        </div>
      )}

      {/* Search / filter toolbar */}
      <div className="card mb-6 flex flex-col gap-3 p-4 md:flex-row md:items-center">
        <div className="relative flex-1">
          <IconSearch className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by case number, title, crime type or police station…"
            className="input pl-9"
            aria-label="Search cases"
          />
        </div>
        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input md:w-52"
            aria-label="Filter by status"
          >
            <option value="ALL">All statuses</option>
            {CASE_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
          {/* Grid / list toggle */}
          <div className="flex overflow-hidden rounded-lg border border-slate-300">
            <button
              onClick={() => setView("grid")}
              className={`flex h-10 w-10 items-center justify-center transition ${
                view === "grid"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-slate-500 hover:bg-slate-50"
              }`}
              aria-label="Grid view"
              aria-pressed={view === "grid"}
            >
              <IconLayoutGrid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setView("list")}
              className={`flex h-10 w-10 items-center justify-center border-l border-slate-300 transition ${
                view === "list"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-slate-500 hover:bg-slate-50"
              }`}
              aria-label="List view"
              aria-pressed={view === "list"}
            >
              <IconList className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Loading */}
      {!cases && !error && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-44 rounded-xl" />
          ))}
        </div>
      )}

      {/* Empty states */}
      {filtered && filtered.length === 0 && cases && cases.length > 0 && (
        <EmptyState
          title="No cases match your filters"
          description="Try a different search term or clear the status filter."
          action={
            <button
              onClick={() => {
                setQuery("");
                setStatusFilter("ALL");
              }}
              className="btn btn-secondary btn-md"
            >
              Clear filters
            </button>
          }
        />
      )}

      {cases && cases.length === 0 && (
        <EmptyState
          title="No cases are visible to you yet"
          description="Cases you create, are assigned to, or are a member of will appear here."
          action={
            <Link href="/cases/new" className="btn btn-primary btn-md">
              <IconPlus className="h-4 w-4" />
              Create your first case
            </Link>
          }
        />
      )}

      {/* Grid view */}
      {filtered && filtered.length > 0 && view === "grid" && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((c) => (
            <CaseCard key={c.id} item={c} />
          ))}
        </div>
      )}

      {/* List view */}
      {filtered && filtered.length > 0 && view === "list" && (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Case number</th>
                <th>Title</th>
                <th>Crime type</th>
                <th>Status</th>
                <th>Assigned IO</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link
                      href={`/cases/${c.id}`}
                      className="font-mono text-sm font-medium text-blue-600 hover:underline"
                    >
                      {c.case_number}
                    </Link>
                  </td>
                  <td className="max-w-[20rem] truncate text-slate-900">{c.title}</td>
                  <td className="text-slate-600">{c.crime_type}</td>
                  <td>
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="text-slate-600">
                    {c.assigned_io
                      ? (c.assigned_io.full_name ?? c.assigned_io.username)
                      : "—"}
                  </td>
                  <td className="whitespace-nowrap text-slate-500">
                    {formatDateTime(c.updated_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
