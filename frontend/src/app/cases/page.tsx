"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/auth";
import { CaseListItem, statusBadgeClass } from "@/lib/api-types";

export default function CasesPage() {
  const [cases, setCases] = useState<CaseListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<CaseListItem[]>("/api/cases")
      .then(setCases)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <main className="mx-auto min-h-screen max-w-5xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest text-sky-400">
            SIH26190 · Cases
          </p>
          <h1 className="text-2xl font-bold">Cases</h1>
        </div>
        <Link
          href="/cases/new"
          className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-500"
        >
          + New case
        </Link>
      </div>

      {error && (
        <p className="mb-4 rounded-lg border border-rose-800 bg-rose-950/60 px-3 py-2 text-sm text-rose-300">
          {error}{" "}
          <Link href="/login" className="underline">
            Sign in
          </Link>
        </p>
      )}

      {cases && cases.length === 0 && (
        <p className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-400">
          No cases are visible to you yet. Cases you create, are assigned to, or
          are a member of will appear here.
        </p>
      )}

      {cases && cases.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3">Case number</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Crime type</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Assigned IO</th>
                <th className="px-4 py-3">Updated</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr
                  key={c.id}
                  className="border-b border-slate-800/60 transition hover:bg-slate-800/40"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/cases/${c.id}`}
                      className="font-mono text-sky-400 underline"
                    >
                      {c.case_number}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{c.title}</td>
                  <td className="px-4 py-3 text-slate-400">{c.crime_type}</td>
                  <td className="px-4 py-3">
                    <span className={statusBadgeClass(c.status)}>{c.status}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {c.assigned_io
                      ? (c.assigned_io.full_name ?? c.assigned_io.username)
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {new Date(c.updated_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
