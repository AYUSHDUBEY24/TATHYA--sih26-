"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import DocumentsSection from "@/components/DocumentsSection";
import EvidenceSection from "@/components/EvidenceSection";
import { apiFetch } from "@/lib/auth";
import {
  AuditLogEntry,
  CASE_STATUSES,
  CaseAccess,
  CaseDetail,
  DeletedDocumentInfo,
  UserBrief,
} from "@/lib/api-types";
import { useAuth } from "@/lib/useAuth";
import { PageHeader, Skeleton, StatusBadge } from "@/components/ui";
import { useToast } from "@/components/Toast";
import { actionBadgeClass, formatDateTime, prettifyEnum, timeAgo } from "@/lib/format";
import { IconCheckCircle, IconHistory, IconRestore, IconXCircle } from "@/components/icons";

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const caseId = params?.id;
  const { user } = useAuth();
  const { toast } = useToast();
  const isAdmin = user?.role?.name === "ADMIN";

  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [officers, setOfficers] = useState<UserBrief[]>([]);
  const [newMemberEmail, setNewMemberEmail] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [caseAudit, setCaseAudit] = useState<AuditLogEntry[] | null>(null);
  // "Your Access" — computed by the backend from the enforced rules.
  const [access, setAccess] = useState<CaseAccess | null>(null);
  // Recycle bin for this case (soft-deleted documents).
  const [deletedDocs, setDeletedDocs] = useState<DeletedDocumentInfo[] | null>(null);

  const [form, setForm] = useState({
    title: "",
    crime_type: "",
    police_station: "",
    status: "OPEN",
    description: "",
    assigned_io_id: "",
  });

  const load = useCallback(async () => {
    if (!caseId) return;
    try {
      const data = await apiFetch<CaseDetail>(`/api/cases/${caseId}`);
      setDetail(data);
      setForm({
        title: data.title,
        crime_type: data.crime_type,
        police_station: data.police_station,
        status: data.status,
        description: data.description ?? "",
        assigned_io_id: data.assigned_io?.id ?? "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load case");
    }
  }, [caseId]);

  useEffect(() => {
    load();
    apiFetch<UserBrief[]>("/api/users/officers")
      .then(setOfficers)
      .catch(() => setOfficers([]));
  }, [load]);

  // Per-case audit trail — ADMIN only, hidden gracefully otherwise.
  useEffect(() => {
    if (!isAdmin || !caseId) return;
    apiFetch<AuditLogEntry[]>(`/api/audit?case_id=${caseId}&limit=25`)
      .then(setCaseAudit)
      .catch(() => setCaseAudit(null));
  }, [isAdmin, caseId]);

  // "Your Access" — real backend-computed permissions (never role-guessed).
  useEffect(() => {
    if (!caseId) return;
    apiFetch<CaseAccess>(`/api/cases/${caseId}/access`)
      .then(setAccess)
      .catch(() => setAccess(null));
  }, [caseId]);

  // Recycle bin listing for this case (soft-deleted documents).
  const loadDeleted = useCallback(async () => {
    if (!caseId) return;
    try {
      setDeletedDocs(
        await apiFetch<DeletedDocumentInfo[]>(
          `/api/documents/deleted?case_id=${caseId}`
        )
      );
    } catch {
      setDeletedDocs(null);
    }
  }, [caseId]);

  useEffect(() => {
    loadDeleted();
  }, [loadDeleted]);

  async function handleRestoreDeleted(doc: DeletedDocumentInfo) {
    setActionError(null);
    try {
      await apiFetch(`/api/documents/${doc.id}/restore`, { method: "POST" });
      toast({ title: "Document restored", description: doc.file_name, variant: "success" });
      await loadDeleted();
      await load();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not restore document");
    }
  }

  async function handleUpdate(event: FormEvent) {
    event.preventDefault();
    setActionError(null);
    try {
      await apiFetch<CaseDetail>(`/api/cases/${caseId}`, {
        method: "PUT",
        body: JSON.stringify({
          title: form.title,
          crime_type: form.crime_type,
          police_station: form.police_station,
          status: form.status,
          description: form.description || null,
          assigned_io_id: form.assigned_io_id || null,
        }),
      });
      setEditing(false);
      toast({ title: "Case updated", variant: "success" });
      await load();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Update failed");
    }
  }

  async function handleAddMember(event: FormEvent) {
    event.preventDefault();
    setActionError(null);
    try {
      await apiFetch(`/api/cases/${caseId}/members`, {
        method: "POST",
        body: JSON.stringify({ email: newMemberEmail }),
      });
      setNewMemberEmail("");
      toast({ title: "Member added", variant: "success" });
      await load();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not add member");
    }
  }

  async function handleRemoveMember(userId: string) {
    setActionError(null);
    try {
      await apiFetch(`/api/cases/${caseId}/members/${userId}`, { method: "DELETE" });
      toast({ title: "Member removed", variant: "success" });
      await load();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not remove member");
    }
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl">
        <Link href="/cases" className="text-sm font-medium text-blue-600 hover:underline">
          ← Back to cases
        </Link>
        <div
          role="alert"
          className="mt-6 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          {error}
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="mx-auto max-w-5xl space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 rounded-xl" />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      <nav className="mb-4 flex items-center gap-1 text-sm text-slate-500" aria-label="Breadcrumb">
        <Link href="/cases" className="hover:text-blue-600 hover:underline">
          Cases
        </Link>
        <span aria-hidden="true">/</span>
        <span className="font-mono text-slate-700">{detail.case_number}</span>
      </nav>

      <PageHeader
        title={detail.title}
        description={`${detail.crime_type} · ${detail.police_station}`}
        action={
          <>
            <StatusBadge status={detail.status} className="self-center" />
            {detail.can_manage && !editing && (
              <button onClick={() => setEditing(true)} className="btn btn-secondary btn-md">
                Edit case
              </button>
            )}
          </>
        }
      />

      {/* Edit form */}
      {editing && (
        <form onSubmit={handleUpdate} className="card mb-8 border-blue-200 p-6">
          <h2 className="mb-4 text-base font-semibold text-slate-900">Edit case</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="edit-title">Title</label>
              <input
                id="edit-title"
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="input"
              />
            </div>
            <div>
              <label className="label" htmlFor="edit-status">Status</label>
              <select
                id="edit-status"
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                className="input"
              >
                {CASE_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="edit-crime">Crime type</label>
              <input
                id="edit-crime"
                required
                value={form.crime_type}
                onChange={(e) => setForm({ ...form, crime_type: e.target.value })}
                className="input"
              />
            </div>
            <div>
              <label className="label" htmlFor="edit-station">Police station</label>
              <input
                id="edit-station"
                required
                value={form.police_station}
                onChange={(e) => setForm({ ...form, police_station: e.target.value })}
                className="input"
              />
            </div>
            <div>
              <label className="label" htmlFor="edit-io">Assigned IO</label>
              <select
                id="edit-io"
                value={form.assigned_io_id}
                onChange={(e) => setForm({ ...form, assigned_io_id: e.target.value })}
                className="input"
                disabled={officers.length === 0}
              >
                <option value="">— Unassigned —</option>
                {officers.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.full_name ?? o.username}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="mt-4">
            <label className="label" htmlFor="edit-desc">Description</label>
            <textarea
              id="edit-desc"
              rows={3}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="input"
            />
          </div>
          <div className="mt-4 flex gap-3">
            <button type="submit" className="btn btn-primary btn-md">
              Save changes
            </button>
            <button type="button" onClick={() => setEditing(false)} className="btn btn-secondary btn-md">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Case information */}
      <div className="card mb-8 p-6">
        <h2 className="mb-4 text-base font-semibold text-slate-900">Case information</h2>
        <dl className="grid grid-cols-[10rem_1fr] gap-y-2 text-sm">
          <dt className="text-slate-500">Case number</dt>
          <dd className="font-mono text-slate-900">{detail.case_number}</dd>
          <dt className="text-slate-500">Crime type</dt>
          <dd className="text-slate-900">{detail.crime_type}</dd>
          <dt className="text-slate-500">Police station</dt>
          <dd className="text-slate-900">{detail.police_station}</dd>
          <dt className="text-slate-500">Assigned IO</dt>
          <dd className="text-slate-900">
            {detail.assigned_io
              ? (detail.assigned_io.full_name ?? detail.assigned_io.username)
              : "—"}
          </dd>
          <dt className="text-slate-500">Created</dt>
          <dd className="text-slate-900">{formatDateTime(detail.created_at)}</dd>
          <dt className="text-slate-500">Updated</dt>
          <dd className="text-slate-900">{formatDateTime(detail.updated_at)}</dd>
          <dt className="text-slate-500">Description</dt>
          <dd className="text-slate-700">{detail.description ?? "—"}</dd>
        </dl>
      </div>

      {/* YOUR ACCESS — computed by the backend from the enforced rules */}
      {access && (
        <div className="card mb-8 p-6">
          <h2 className="text-base font-semibold text-slate-900">Your Access</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Effective permissions computed by the backend from your role and
            case membership — the same rules every API request enforces.
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            <span className="badge badge-info">Role: {prettifyEnum(access.role)}</span>
            {access.case_role && (
              <span className="badge badge-muted">In case: {prettifyEnum(access.case_role)}</span>
            )}
          </div>
          <ul className="mt-4 grid gap-x-6 gap-y-1.5 text-sm sm:grid-cols-2">
            {[
              { ok: access.can_read, label: "Read case & documents" },
              { ok: access.can_upload, label: "Upload documents" },
              { ok: access.can_create_version, label: "Create document versions" },
              { ok: access.can_verify_integrity, label: "Verify integrity & blockchain" },
              { ok: access.can_delete_documents, label: "Delete / restore documents" },
              { ok: access.can_manage_case, label: "Manage case & members" },
              { ok: access.can_administer, label: "System administration" },
            ].map((p) => (
              <li key={p.label} className="flex items-center gap-2">
                {p.ok ? (
                  <IconCheckCircle className="h-4 w-4 shrink-0 text-emerald-600" />
                ) : (
                  <IconXCircle className="h-4 w-4 shrink-0 text-slate-300" />
                )}
                <span className={p.ok ? "text-slate-800" : "text-slate-400"}>
                  {p.label}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Case members */}
      <div className="card mb-8 p-6">
        <h2 className="mb-4 text-base font-semibold text-slate-900">Case members</h2>
        <ul className="mb-4 space-y-2 text-sm">
          {detail.members.map((m) => (
            <li
              key={m.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-100 px-3 py-2"
            >
              <span>
                <span className="font-medium text-slate-900">
                  {m.full_name ?? m.username}
                </span>{" "}
                <span className="text-slate-500">({m.username})</span>{" "}
                <span className="badge badge-info ml-2">{m.role_in_case}</span>
              </span>
              {detail.can_manage && (
                <button
                  onClick={() => handleRemoveMember(m.user_id)}
                  className="text-xs font-medium text-rose-600 hover:underline"
                >
                  Remove
                </button>
              )}
            </li>
          ))}
        </ul>

        {detail.can_manage && (
          <form onSubmit={handleAddMember} className="flex flex-wrap gap-2">
            <input
              type="email"
              required
              value={newMemberEmail}
              onChange={(e) => setNewMemberEmail(e.target.value)}
              placeholder="user email to add…"
              className="input max-w-sm flex-1"
              aria-label="Member email"
            />
            <button type="submit" className="btn btn-primary btn-md">
              Add member
            </button>
          </form>
        )}

        {actionError && (
          <p
            role="alert"
            className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
          >
            {actionError}
          </p>
        )}
      </div>

      {/* Recently Deleted (recycle bin) — soft-deleted documents for this case */}
      {deletedDocs && deletedDocs.length > 0 && (
        <div className="card mb-8 p-6">
          <div className="flex items-center gap-2">
            <IconHistory className="h-4 w-4 text-slate-500" />
            <h2 className="text-base font-semibold text-slate-900">
              Recently Deleted
            </h2>
            <span className="badge badge-muted text-[10px]">
              files and version history are preserved
            </span>
          </div>
          <ul className="mt-4 space-y-2">
            {deletedDocs.map((d) => (
              <li
                key={d.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2.5 text-sm"
              >
                <div className="min-w-0">
                  <p
                    title={d.file_name}
                    className="truncate font-medium text-slate-800"
                  >
                    {d.file_name}
                  </p>
                  <p className="text-xs text-slate-500">
                    Case {detail.case_number} ·{" "}
                    {d.deleted_by
                      ? `Deleted by ${d.deleted_by}`
                      : "Deleted by unknown"}
                    {d.deleted_at ? ` · ${formatDateTime(d.deleted_at)}` : ""}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {d.can_delete && (
                    <button
                      onClick={() => handleRestoreDeleted(d)}
                      className="btn btn-secondary btn-sm"
                      title="Restore to the active document list (no new version)"
                    >
                      <IconRestore className="h-3.5 w-3.5" />
                      Restore
                    </button>
                  )}
                  {!d.can_delete && (
                    <span className="text-xs text-slate-400">
                      No restore permission
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Documents: list + upload (left) and detail/integrity/blockchain panel (right) */}
      <DocumentsSection caseId={detail.id} />

      {/* Evidence assets + chain of custody (vertical timeline) */}
      <EvidenceSection caseId={detail.id} />

      {/* Case audit timeline (ADMIN only — hidden for other roles) */}
      {isAdmin && (
        <div className="card mt-8 p-6">
          <h2 className="mb-4 text-base font-semibold text-slate-900">
            Case audit trail
          </h2>
          {caseAudit === null ? (
            <p className="text-sm text-slate-500">
              Audit trail for this case is unavailable.
            </p>
          ) : caseAudit.length === 0 ? (
            <p className="text-sm text-slate-500">
              No audit events for this case yet.
            </p>
          ) : (
            <ol className="space-y-2.5">
              {caseAudit.map((log) => (
                <li
                  key={log.id}
                  className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-100 px-3 py-2 text-sm"
                >
                  <span
                    className={`rounded-md px-2 py-0.5 font-mono text-[11px] font-semibold ${actionBadgeClass(log.action)}`}
                  >
                    {log.action}
                  </span>
                  <span className="text-slate-600">{log.actor_username ?? "system"}</span>
                  <span className="ml-auto text-xs text-slate-500">
                    {formatDateTime(log.created_at)}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
    </div>
  );
}
