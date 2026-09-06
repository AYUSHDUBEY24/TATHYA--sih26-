import Link from "next/link";
import { AuditLogEntry, CASE_STATUSES } from "@/lib/api-types";
import { actionBadgeClass, formatDateTime } from "@/lib/format";
import { IconLock } from "./icons";

/**
 * Dashboard building blocks. All values passed in are derived from real
 * backend API responses — this module never invents numbers.
 */

const KPI_TONES: Record<string, { bg: string; color: string }> = {
  blue: { bg: "bg-blue-50", color: "text-blue-600" },
  emerald: { bg: "bg-emerald-50", color: "text-emerald-600" },
  amber: { bg: "bg-amber-50", color: "text-amber-600" },
  rose: { bg: "bg-rose-50", color: "text-rose-600" },
  slate: { bg: "bg-slate-100", color: "text-slate-600" },
};

export function KpiCard({
  label,
  value,
  tone = "blue",
  icon,
  hint,
}: {
  label: string;
  value: number | string;
  tone?: keyof typeof KPI_TONES;
  icon?: React.ReactNode;
  hint?: string;
}) {
  const toneStyle = KPI_TONES[tone] ?? KPI_TONES.blue;
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {label}
          </p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
            {value}
          </p>
          {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
        </div>
        {icon && (
          <span
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${toneStyle.bg} ${toneStyle.color}`}
          >
            {icon}
          </span>
        )}
      </div>
    </div>
  );
}

const STATUS_BAR_COLORS: Record<string, string> = {
  OPEN: "bg-blue-500",
  UNDER_INVESTIGATION: "bg-amber-500",
  UNDER_REVIEW: "bg-violet-500",
  CHARGESHEET_FILED: "bg-orange-500",
  COURT_STAGE: "bg-fuchsia-500",
  CLOSED: "bg-slate-400",
  ARCHIVED: "bg-slate-300",
};

/** Case status visualization derived from actual /api/cases data. */
export function StatusBreakdown({
  counts,
  total,
}: {
  counts: Record<string, number>;
  total: number;
}) {
  const present = CASE_STATUSES.filter((s) => (counts[s] ?? 0) > 0);
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900">Case Status</h2>
        <Link href="/cases" className="text-sm font-medium text-blue-600 hover:underline">
          View all cases →
        </Link>
      </div>
      <div className="card p-5">
        {total === 0 ? (
          <p className="text-sm text-slate-500">
            No cases visible to you yet — the status mix will appear here once
            cases exist.
          </p>
        ) : (
          <>
            {/* Stacked proportion bar */}
            <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
              {present.map((status) => (
                <div
                  key={status}
                  className={STATUS_BAR_COLORS[status] ?? "bg-slate-300"}
                  style={{ width: `${((counts[status] ?? 0) / total) * 100}%` }}
                  title={`${status}: ${counts[status]}`}
                />
              ))}
            </div>
            {/* Legend chips */}
            <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2">
              {present.map((status) => (
                <span key={status} className="flex items-center gap-1.5 text-xs text-slate-600">
                  <span
                    className={`inline-block h-2.5 w-2.5 rounded-full ${
                      STATUS_BAR_COLORS[status] ?? "bg-slate-300"
                    }`}
                  />
                  {status.replace(/_/g, " ")}
                  <span className="font-semibold text-slate-900">
                    {counts[status]}
                  </span>
                </span>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

/**
 * Recent activity from the ADMIN-only audit API.
 * `restricted` = the current user is not an administrator, so we show an
 * honest explanation instead of pretending there is no activity.
 */
export function ActivityTimeline({
  events,
  restricted,
}: {
  events: AuditLogEntry[] | null;
  restricted: boolean;
}) {
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900">Recent Activity</h2>
        <Link href="/audit" className="text-sm font-medium text-blue-600 hover:underline">
          Open audit log →
        </Link>
      </div>
      <div className="card p-5">
        {restricted ? (
          <div className="flex items-start gap-3 text-sm text-slate-600">
            <IconLock className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
            <p>
              The detailed activity timeline is drawn from the audit trail,
              which is available to administrator accounts only.
            </p>
          </div>
        ) : events === null ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton h-10 w-full" />
            ))}
          </div>
        ) : events.length === 0 ? (
          <p className="text-sm text-slate-500">
            No audit events recorded yet.
          </p>
        ) : (
          <ol className="space-y-2.5">
            {events.map((log) => (
              <li
                key={log.id}
                className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-100 px-3 py-2 text-sm transition hover:bg-slate-50"
              >
                <span
                  className={`rounded-md px-2 py-0.5 font-mono text-[11px] font-semibold ${actionBadgeClass(
                    log.action
                  )}`}
                >
                  {log.action}
                </span>
                <span className="text-slate-600">
                  {log.actor_username ?? "system"}
                </span>
                <span className="ml-auto text-xs text-slate-500">
                  {formatDateTime(log.created_at)}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}
