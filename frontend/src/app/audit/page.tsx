"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/auth";
import { AuditLogEntry } from "@/lib/api-types";

const RESULT_STYLES: Record<string, string> = {
  SUCCESS: "bg-emerald-900/70 text-emerald-300",
  FAILURE: "bg-rose-900/70 text-rose-300",
  DENIED: "bg-amber-900/70 text-amber-300",
};

function formatMeta(meta: Record<string, unknown>): string {
  if (!meta || Object.keys(meta).length === 0) return "—";
  try {
    return JSON.stringify(meta);
  } catch {
    return "—";
  }
}

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditLogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    action: "",
    actor: "",
    case_id: "",
    result: "",
  });

  const load = useCallback(async () => {
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filters.action) params.set("action", filters.action);
      if (filters.actor) params.set("actor_id", filters.actor);
      if (filters.case_id) params.set("case_id", filters.case_id);
      if (filters.result) params.set("result", filters.result);
      const qs = params.toString();
      setEntries(
        await apiFetch<AuditLogEntry[]>(`/api/audit${qs ? `?${qs}` : ""}`)
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load audit log");
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  const inputClass =
    "w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs outline-none focus:border-sky-500";

  return (
    <main className="mx-auto min-h-screen max-w-6xl p-8">
      <p className="text-xs font-medium uppercase tracking-widest text-sky-400">
        SIH26190 · Admin
      </p>
      <h1 className="mb-6 text-2xl font-bold">Audit Log</h1>

      {/* Filters */}
      <div className="mb-6 grid grid-cols-2 gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4 md:grid-cols-4">
        <div>
          <label className="mb-1 block text-xs text-slate-400">Action</label>
          <input
            value={filters.action}
            onChange={(e) => setFilters({ ...filters, action: e.target.value })}
            placeholder="e.g. DOCUMENT_UPLOADED"
            className={inputClass}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">Actor (user id)</label>
          <input
            value={filters.actor}
            onChange={(e) => setFilters({ ...filters, actor: e.target.value })}
            placeholder="UUID"
            className={inputClass}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">Case ID</label>
          <input
            value={filters.case_id}
            onChange={(e) => setFilters({ ...filters, case_id: e.target.value })}
            placeholder="UUID"
            className={inputClass}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">Result</label>
          <select
            value={filters.result}
            onChange={(e) => setFilters({ ...filters, result: e.target.value })}
            className={inputClass}
          >
            <option value="">Any</option>
            <option value="SUCCESS">SUCCESS</option>
            <option value="FAILURE">FAILURE</option>
            <option value="DENIED">DENIED</option>
          </select>
        </div>
      </div>

      {error && (
        <p className="mb-4 rounded-lg border border-rose-800 bg-rose-950/60 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      )}

      {entries && entries.length === 0 && (
        <p className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-400">
          No audit entries match the current filters.
        </p>
      )}

      {entries && entries.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-3 py-2">Timestamp</th>
                <th className="px-3 py-2">Actor</th>
                <th className="px-3 py-2">Action</th>
                <th className="px-3 py-2">Entity</th>
                <th className="px-3 py-2">Case</th>
                <th className="px-3 py-2">Result</th>
                <th className="px-3 py-2">IP</th>
                <th className="px-3 py-2">Metadata</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-b border-slate-800/60 align-top">
                  <td className="whitespace-nowrap px-3 py-2 text-xs">
                    {new Date(e.created_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2">{e.actor_username ?? "Unknown"}</td>
                  <td className="px-3 py-2 font-mono text-xs">{e.action}</td>
                  <td className="px-3 py-2">
                    {e.entity_type ?? "—"}
                    {e.entity_id ? (
                      <span className="block font-mono text-[10px] text-slate-500">
                        {e.entity_id.slice(0, 8)}…
                      </span>
                    ) : null}
                  </td>
                  <td className="px-3 py-2 font-mono text-[10px] text-slate-500">
                    {e.case_id ? e.case_id.slice(0, 8) + "…" : "—"}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-semibold ${
                        RESULT_STYLES[e.result] ?? "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {e.result}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-400">
                    {e.ip_address ?? "—"}
                  </td>
                  <td className="max-w-[220px] px-3 py-2 font-mono text-[10px] text-slate-400">
                    {formatMeta(e.metadata)}
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