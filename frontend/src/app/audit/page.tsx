"use client";

import {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { apiFetch, ApiError } from "@/lib/auth";
import { AuditLogEntry, CaseListItem } from "@/lib/api-types";
import { EmptyState, PageHeader, Skeleton } from "@/components/ui";
import { actionBadgeClass, formatDateTime, resultBadgeClass } from "@/lib/format";
import { IconLock } from "@/components/icons";

const RESULT_FILTERS = [
  { value: "", label: "All results" },
  { value: "SUCCESS", label: "Success" },
  { value: "FAILURE", label: "Failure" },
  { value: "DENIED", label: "Denied" },
];

interface ActorOption {
  id: string;
  label: string;
}

function formatMeta(meta: Record<string, unknown>): string {
  if (!meta || Object.keys(meta).length === 0) return "";
  try {
    return JSON.stringify(meta);
  } catch {
    return "";
  }
}

/**
 * Tathya Chronicle — the immutable audit trail. ADMIN-only via the backend;
 * the UI shows a friendly gate for other roles.
 *
 * Filters use the existing GET /api/audit parameters (action, actor_id,
 * case_id, result). Actor/case dropdowns are populated from existing
 * permitted data only: GET /api/users (ADMIN-only), GET /api/cases, plus
 * actors observed in the loaded audit entries. No fake values.
 */
export default function AuditPage() {
  const [entries, setEntries] = useState<AuditLogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);
  const [expandedMeta, setExpandedMeta] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    action: "",
    actor: "",
    case_id: "",
    result: "",
  });

  // Dropdown sources (existing APIs only)
  const [userOptions, setUserOptions] = useState<Array<{ id: string; label: string }>>([]);
  const [caseOptions, setCaseOptions] = useState<CaseListItem[]>([]);

  useEffect(() => {
    // Both endpoints are ADMIN-only, same audience as the audit log.
    // Failures degrade gracefully to the manual-UUID fallback below.
    apiFetch<Array<{ id: string; username: string; full_name: string | null }>>(
      "/api/users"
    )
      .then((users) =>
        setUserOptions(
          users.map((u) => ({ id: u.id, label: u.full_name ?? u.username }))
        )
      )
      .catch(() => setUserOptions([]));
    apiFetch<CaseListItem[]>("/api/cases")
      .then(setCaseOptions)
      .catch(() => setCaseOptions([]));
  }, []);

  const load = useCallback(async () => {
    setError(null);
    setForbidden(false);
    try {
      const params = new URLSearchParams();
      if (filters.action) params.set("action", filters.action);
      if (filters.actor) params.set("actor_id", filters.actor);
      if (filters.case_id) params.set("case_id", filters.case_id);
      if (filters.result) params.set("result", filters.result);
      const qs = params.toString();
      setEntries(await apiFetch<AuditLogEntry[]>(`/api/audit${qs ? `?${qs}` : ""}`));
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setForbidden(true);
        setEntries([]);
      } else {
        setError(err instanceof Error ? err.message : "Could not load audit log");
      }
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  // Merge dropdown sources: ADMIN user list + actors observed in loaded
  // entries (real data only, de-duplicated).
  const actorOptions: ActorOption[] = useMemo(() => {
    const map = new Map<string, string>();
    for (const u of userOptions) map.set(u.id, u.label);
    for (const e of entries ?? []) {
      if (e.actor_id && !map.has(e.actor_id)) {
        map.set(e.actor_id, e.actor_username ?? `${e.actor_id.slice(0, 8)}…`);
      }
    }
    return Array.from(map, ([id, label]) => ({ id, label })).sort((a, b) =>
      a.label.localeCompare(b.label)
    );
  }, [userOptions, entries]);

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow="Oversight"
        title="Tathya Chronicle — Activity Log"
        description="Immutable, append-only record of security-relevant activity. Administrator access only."
      />

      {/* Administrator gate — the API is ADMIN-only; show a friendly notice. */}
      {forbidden && (
        <div className="card flex items-start gap-3 p-6">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
            <IconLock className="h-5 w-5" />
          </span>
          <div>
            <p className="font-semibold text-slate-900">
              Administrator role required
            </p>
            <p className="mt-1 text-sm text-slate-600">
              The audit trail can only be viewed by administrator accounts. Sign
              in with an ADMIN account to review system-wide activity.
            </p>
          </div>
        </div>
      )}

      {!forbidden && (
        <>
          {/* Filter chips + dropdowns */}
          <div className="card mb-6 space-y-4 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="mr-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Result
              </span>
              {RESULT_FILTERS.map((f) => (
                <button
                  key={f.value}
                  onClick={() => setFilters({ ...filters, result: f.value })}
                  aria-pressed={filters.result === f.value}
                  className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                    filters.result === f.value
                      ? "border-blue-600 bg-blue-600 text-white"
                      : "border-slate-300 bg-white text-slate-600 hover:border-blue-400 hover:text-blue-600"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <div>
                <label className="label" htmlFor="filter-action">Action</label>
                <input
                  id="filter-action"
                  value={filters.action}
                  onChange={(e) => setFilters({ ...filters, action: e.target.value })}
                  placeholder="e.g. DOCUMENT_UPLOADED"
                  className="input"
                />
              </div>
              <div>
                <label className="label" htmlFor="filter-actor">Actor</label>
                {actorOptions.length > 0 ? (
                  <select
                    id="filter-actor"
                    value={filters.actor}
                    onChange={(e) => setFilters({ ...filters, actor: e.target.value })}
                    className="input"
                  >
                    <option value="">All actors</option>
                    {actorOptions.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <>
                    <input
                      id="filter-actor"
                      value={filters.actor}
                      onChange={(e) =>
                        setFilters({ ...filters, actor: e.target.value })
                      }
                      placeholder="Actor UUID"
                      className="input"
                    />
                    <p className="mt-1 text-[10px] text-slate-500">
                      User list unavailable — paste a user UUID.
                    </p>
                  </>
                )}
              </div>
              <div>
                <label className="label" htmlFor="filter-case">Case</label>
                {caseOptions.length > 0 ? (
                  <select
                    id="filter-case"
                    value={filters.case_id}
                    onChange={(e) => setFilters({ ...filters, case_id: e.target.value })}
                    className="input"
                  >
                    <option value="">All cases</option>
                    {caseOptions.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.case_number} — {c.title}
                      </option>
                    ))}
                  </select>
                ) : (
                  <>
                    <input
                      id="filter-case"
                      value={filters.case_id}
                      onChange={(e) =>
                        setFilters({ ...filters, case_id: e.target.value })
                      }
                      placeholder="Case UUID"
                      className="input"
                    />
                    <p className="mt-1 text-[10px] text-slate-500">
                      Case list unavailable — paste a case UUID.
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {error && (
            <div
              role="alert"
              className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
            >
              {error}
            </div>
          )}

          {entries === null && !error && (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          )}

          {entries && entries.length === 0 && !error && (
            <EmptyState
              title="No audit entries match the current filters"
              description="Try clearing a filter or widening your search."
            />
          )}

          {entries && entries.length > 0 && (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Actor</th>
                    <th>Action</th>
                    <th>Entity</th>
                    <th>Case</th>
                    <th>Result</th>
                    <th>IP</th>
                    <th>Metadata</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((e) => {
                    const metaJson = formatMeta(e.metadata);
                    const metaExpanded = expandedMeta === e.id;
                    return (
                      <Fragment key={e.id}>
                        <tr className="align-top">
                          <td className="whitespace-nowrap text-xs text-slate-600">
                            {formatDateTime(e.created_at)}
                          </td>
                          <td className="text-slate-900">
                            {e.actor_username ?? "Unknown"}
                          </td>
                          <td>
                            <span
                              title={e.action}
                              className={`block max-w-[9rem] truncate rounded-md px-2 py-0.5 font-mono text-[11px] font-semibold ${actionBadgeClass(e.action)}`}
                            >
                              {e.action}
                            </span>
                          </td>
                          <td className="text-slate-700">
                            {e.entity_type ?? "—"}
                            {e.entity_id && (
                              <span
                                title={e.entity_id}
                                className="block font-mono text-[10px] text-slate-400"
                              >
                                {e.entity_id.slice(0, 8)}…
                              </span>
                            )}
                          </td>
                          <td
                            title={e.case_id ?? undefined}
                            className="font-mono text-[10px] text-slate-500"
                          >
                            {e.case_id ? e.case_id.slice(0, 8) + "…" : "—"}
                          </td>
                          <td>
                            <span
                              className={`rounded-md px-2 py-0.5 text-[11px] font-semibold ${resultBadgeClass(e.result)}`}
                            >
                              {e.result}
                            </span>
                          </td>
                          <td className="font-mono text-xs text-slate-500">
                            {e.ip_address ?? "—"}
                          </td>
                          <td className="max-w-[220px]">
                            {metaJson ? (
                              <>
                                <p
                                  className={`break-all font-mono text-[10px] text-slate-500 ${
                                    metaExpanded ? "" : "line-clamp-1"
                                  }`}
                                >
                                  {metaJson}
                                </p>
                                <button
                                  onClick={() =>
                                    setExpandedMeta(metaExpanded ? null : e.id)
                                  }
                                  className="mt-0.5 text-[10px] font-medium text-blue-600 hover:underline"
                                >
                                  {metaExpanded ? "Hide" : "View full"}
                                </button>
                              </>
                            ) : (
                              <span className="text-slate-400">—</span>
                            )}
                          </td>
                        </tr>
                        {/* Expandable full-metadata row — keeps complete data inspectable */}
                        {metaExpanded && metaJson && (
                          <tr className="bg-slate-50">
                            <td colSpan={8} className="px-4 py-3">
                              <pre className="slim-scrollbar max-h-40 overflow-auto whitespace-pre-wrap break-all rounded-lg border border-slate-200 bg-white p-3 font-mono text-[10px] text-slate-700">
                                {JSON.stringify(e.metadata, null, 2)}
                              </pre>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
