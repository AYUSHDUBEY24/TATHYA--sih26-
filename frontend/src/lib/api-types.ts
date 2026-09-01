/** Shared API payload types (mirror backend Pydantic schemas). */

export interface UserBrief {
  id: string;
  username: string;
  full_name: string | null;
}

export interface CaseMember {
  id: string;
  user_id: string;
  username: string;
  full_name: string | null;
  role_in_case: string;
  joined_at: string;
}

export interface CaseListItem {
  id: string;
  case_number: string;
  title: string;
  description: string | null;
  crime_type: string;
  police_station: string;
  status: string;
  created_by: string;
  assigned_io: UserBrief | null;
  created_at: string;
  updated_at: string;
}

export interface CaseDetail extends CaseListItem {
  members: CaseMember[];
  can_manage: boolean;
}

export const CASE_STATUSES = [
  "OPEN",
  "UNDER_INVESTIGATION",
  "UNDER_REVIEW",
  "CHARGESHEET_FILED",
  "COURT_STAGE",
  "CLOSED",
  "ARCHIVED",
] as const;

export function statusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    OPEN: "bg-sky-900/80 text-sky-300",
    UNDER_INVESTIGATION: "bg-amber-900/80 text-amber-300",
    UNDER_REVIEW: "bg-violet-900/80 text-violet-300",
    CHARGESHEET_FILED: "bg-orange-900/80 text-orange-300",
    COURT_STAGE: "bg-fuchsia-900/80 text-fuchsia-300",
    CLOSED: "bg-slate-800 text-slate-300",
    ARCHIVED: "bg-slate-800/60 text-slate-400",
  };
  return `rounded-md px-2 py-0.5 text-xs font-semibold ${map[status] ?? "bg-slate-800 text-slate-300"}`;
}

/* --- Documents (Phase 4) --- */

export const DOCUMENT_TYPES = [
  "FIR",
  "POLICE_REPORT",
  "INVESTIGATION_REPORT",
  "WITNESS_STATEMENT",
  "EVIDENCE_RECORD",
  "FORENSIC_REPORT",
  "CHARGE_SHEET",
  "COURT_FILING",
  "LEGAL_NOTICE",
  "JUDGMENT",
  "OTHER",
] as const;

export const CLASSIFICATIONS = [
  "PUBLIC",
  "INTERNAL",
  "RESTRICTED",
  "CONFIDENTIAL",
] as const;

export interface DocumentItem {
  id: string;
  case_id: string;
  file_name: string;
  document_type: string;
  classification: string;
  description: string | null;
  status: string;
  size_bytes: number;
  content_type: string;
  uploader: UserBrief | null;
  created_at: string;
  updated_at: string;
  current_version_number: number | null;
  current_hash: string | null;
  can_delete: boolean;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  version_number: number;
  file_name: string;
  hash: string;
  file_size: number;
  mime_type: string;
  change_note: string | null;
  created_at: string;
  uploader: UserBrief | null;
}

export interface IntegrityResult {
  status: "VERIFIED" | "INTEGRITY_FAILURE";
  document_id: string;
  version: number;
  stored_hash: string;
  current_hash: string;
  verified_at: string | null;
}

export interface AuditLogEntry {
  id: string;
  actor_id: string | null;
  actor_username: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  case_id: string | null;
  ip_address: string | null;
  result: string;
  metadata: Record<string, unknown>;
  created_at: string;
}
