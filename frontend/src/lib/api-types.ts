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

// Status badge styling lives in `components/ui.tsx` (StatusBadge) — the
// previous duplicate `statusBadgeClass` helper was removed during the
// redesign; use <StatusBadge status={...} /> instead.

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

/* --- Blockchain (Phase 7) --- */

export interface BlockchainStatusResult {
  document_id: string;
  version_id: string | null;
  version_number: number | null;
  blockchain_key: string | null;
  status: string;
  transaction_hash: string | null;
  block_number: number | null;
  anchored_at: string | null;
  error_message: string | null;
}

export interface BlockchainVerifyResult {
  status: string;
  document_id: string;
  version: number;
  file_hash: string;
  stored_hash: string;
  blockchain_hash: string | null;
  blockchain_key: string | null;
  transaction_hash: string | null;
  verified_at: string | null;
}

export interface SearchHit {
  document_id: string;
  case_id: string;
  case_number: string;
  case_title: string;
  file_name: string;
  document_type: string;
  classification: string;
  description: string | null;
  uploader_username: string | null;
  current_version_number: number | null;
  created_at: string;
  extraction_method: string | null;
  extraction_status: string | null;
  snippet: string | null;
  matched_text: boolean;
}

export interface SearchResponse {
  query: string;
  total: number;
  limit: number;
  offset: number;
  results: SearchHit[];
}

/* --- Recycle bin (soft delete / restore) --- */

export interface DeletedDocumentInfo extends DocumentItem {
  deleted_by: string | null;
  deleted_at: string | null;
}

/* --- Your Access (computed by the backend from enforced rules) --- */

export interface CaseAccess {
  role: string;
  case_role: string | null;
  can_read: boolean;
  can_upload: boolean;
  can_create_version: boolean;
  can_verify_integrity: boolean;
  can_delete_documents: boolean;
  can_manage_case: boolean;
  can_administer: boolean;
}

/* --- AI Assistant (Phase 9B) --- */

export interface AICitation {
  document_id: string;
  file_name: string | null;
  version: number | null;
  chunk_id: string | null;
  page_start: number | null;
  page_end: number | null;
  excerpt: string | null;
  score: number | null;
}

export interface AIQueryResponse {
  status: "answered" | "insufficient_context" | "provider_unavailable";
  answer: string;
  sources: AICitation[];
  provider: string;
}

/* --- Evidence / Chain of Custody --- */

export const EVIDENCE_ASSET_TYPES = [
  "LAPTOP",
  "MOBILE_PHONE",
  "USB_DRIVE",
  "DOCUMENT",
  "STORAGE_DEVICE",
  "OTHER",
] as const;

export const EVIDENCE_TRANSFER_ACTIONS = [
  "COLLECTED",
  "TRANSFERRED",
  "EXAMINED",
  "STORED",
  "RELEASED",
] as const;

export interface AssetTransfer {
  id: string;
  action: string;
  from_party: string | null;
  to_party: string | null;
  purpose: string | null;
  occurred_at: string;
  actor_id: string;
  actor_name: string;
}

export interface EvidenceAsset {
  id: string;
  case_id: string;
  asset_tag: string;
  name: string;
  asset_type: string;
  description: string | null;
  status: string;
  current_holder: string;
  registered_by: string;
  created_at: string;
  updated_at: string;
}

export interface EvidenceAssetDetail extends EvidenceAsset {
  transfers: AssetTransfer[];
}

export interface ChainOfCustody {
  asset: EvidenceAsset;
  case_number: string;
  case_title: string;
  transfers: AssetTransfer[];
}


