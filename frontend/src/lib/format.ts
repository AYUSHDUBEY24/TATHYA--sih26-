/** Shared formatting utilities for the frontend. */

/**
 * Parse a backend timestamp correctly.
 *
 * The backend (FastAPI/SQLAlchemy) stores naive UTC datetimes and serializes
 * them WITHOUT a timezone designator (e.g. "2026-02-14T10:30:00"). JS `new
 * Date()` treats such strings as *local* time, which shifts every displayed
 * timestamp. Strings without an explicit offset are therefore interpreted as
 * UTC; strings that already carry "Z"/±hh:mm are used as-is. Formatting then
 * happens in the browser's local timezone via toLocaleString().
 */
export function parseBackendDate(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const hasTz = /[Zz]$|[+-]\d{2}:?\d{2}$/.test(iso);
  const d = hasTz ? new Date(iso) : new Date(`${iso}Z`);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDateTime(iso: string | null | undefined): string {
  const d = parseBackendDate(iso);
  return d ? d.toLocaleString() : "—";
}

export function formatDate(iso: string | null | undefined): string {
  const d = parseBackendDate(iso);
  return d ? d.toLocaleDateString() : "—";
}

/** Relative time like "just now", "12m ago", "3h ago", "5d ago". */
export function timeAgo(iso: string | null | undefined): string {
  const d = parseBackendDate(iso);
  if (!d) return "—";
  const seconds = Math.floor((Date.now() - d.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return d.toLocaleDateString();
}

/** Truncate a long hash for display: head…tail. */
export function shortHash(
  hash: string | null | undefined,
  head = 10,
  tail = 6
): string {
  if (!hash) return "—";
  if (hash.length <= head + tail + 1) return hash;
  return `${hash.slice(0, head)}…${hash.slice(-tail)}`;
}

/** "UNDER_INVESTIGATION" → "Under investigation"-style label. */
export function prettifyEnum(value: string): string {
  if (!value) return "—";
  const text = value.replace(/_/g, " ").toLowerCase();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

/* --- Audit badge color helpers (shared by dashboard, case detail, audit) --- */

export type AuditCategory =
  | "document"
  | "integrity"
  | "blockchain"
  | "auth"
  | "permission"
  | "case"
  | "ai"
  | "search"
  | "other";

export function auditCategory(action: string): AuditCategory {
  if (action.startsWith("DOCUMENT_")) return "document";
  if (action.startsWith("INTEGRITY_")) return "integrity";
  if (action.startsWith("BLOCKCHAIN_")) return "blockchain";
  if (action.startsWith("LOGIN") || action === "LOGOUT") return "auth";
  if (action.startsWith("PERMISSION_") || action === "ROLE_CHANGED")
    return "permission";
  if (action.startsWith("CASE_")) return "case";
  if (action.startsWith("AI_")) return "ai";
  if (action.startsWith("SEARCH_") || action.startsWith("RAG_")) return "search";
  return "other";
}

/** Tailwind classes for an audit action badge, color-coded by category. */
export function actionBadgeClass(action: string): string {
  const map: Record<AuditCategory, string> = {
    document: "bg-blue-100 text-blue-700",
    integrity: "bg-emerald-100 text-emerald-700",
    blockchain: "bg-violet-100 text-violet-700",
    auth: "bg-slate-200 text-slate-700",
    permission: "bg-amber-100 text-amber-700",
    case: "bg-sky-100 text-sky-700",
    ai: "bg-fuchsia-100 text-fuchsia-700",
    search: "bg-teal-100 text-teal-700",
    other: "bg-slate-100 text-slate-600",
  };
  return map[auditCategory(action)] ?? map.other;
}

/** Tailwind classes for an audit result badge. */
export function resultBadgeClass(result: string): string {
  switch (result) {
    case "SUCCESS":
      return "bg-emerald-100 text-emerald-700";
    case "FAILURE":
      return "bg-rose-100 text-rose-700";
    case "DENIED":
      return "bg-amber-100 text-amber-700";
    default:
      return "bg-slate-100 text-slate-600";
  }
}
