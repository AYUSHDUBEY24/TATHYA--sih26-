"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import DocumentsSection from "@/components/DocumentsSection";
import { apiFetch } from "@/lib/auth";
import {
  CASE_STATUSES,
  CaseDetail,
  statusBadgeClass,
  UserBrief,
} from "@/lib/api-types";

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const caseId = params?.id;

  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [officers, setOfficers] = useState<UserBrief[]>([]);
  const [newMemberEmail, setNewMemberEmail] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

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
      await load();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not add member");
    }
  }

  async function handleRemoveMember(userId: string) {
    setActionError(null);
    try {
      await apiFetch(`/api/cases/${caseId}/members/${userId}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not remove member");
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-sky-500";

  if (error) {
    return (
      <main className="mx-auto min-h-screen max-w-2xl p-8">
        <Link href="/cases" className="text-sm text-sky-400 underline">← Back to cases</Link>
        <p className="mt-6 rounded-lg border border-rose-800 bg-rose-950/60 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      </main>
    );
  }

  if (!detail) {
    return <main className="p-8 text-sm text-slate-400">Loading case…</main>;
  }

  return (
    <main className="mx-auto min-h-screen max-w-3xl p-8">
      <Link href="/cases" className="text-sm text-sky-400 underline">← Back to cases</Link>

      <div className="mt-3 mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-sm text-sky-400">{detail.case_number}</p>
          <h1 className="text-2xl font-bold">{detail.title}</h1>
        </div>
        <span className={statusBadgeClass(detail.status)}>{detail.status}</span>
      </div>

      {detail.can_manage && !editing && (
        <button onClick={() => setEditing(true)}
          className="mb-6 rounded-lg border border-slate-600 px-4 py-1.5 text-sm font-medium text-slate-200 transition hover:bg-slate-800">
          Edit case
        </button>
      )}

      {editing && (
        <form onSubmit={handleUpdate} className="mb-8 space-y-4 rounded-xl border border-slate-700 bg-slate-900 p-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm text-slate-400">Title</label>
              <input required value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-400">Status</label>
              <select value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })} className={inputClass}>
                {CASE_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-400">Crime type</label>
              <input required value={form.crime_type}
                onChange={(e) => setForm({ ...form, crime_type: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-400">Police station</label>
              <input required value={form.police_station}
                onChange={(e) => setForm({ ...form, police_station: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-400">Assigned IO</label>
              <select value={form.assigned_io_id}
                onChange={(e) => setForm({ ...form, assigned_io_id: e.target.value })}
                className={inputClass} disabled={officers.length === 0}>
                <option value="">— Unassigned —</option>
                {officers.map((o) => (
                  <option key={o.id} value={o.id}>{o.full_name ?? o.username}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-400">Description</label>
            <textarea rows={3} value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })} className={inputClass} />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500">
              Save changes
            </button>
            <button type="button" onClick={() => setEditing(false)}
              className="rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800">
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="mb-8 rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Case information</h2>
        <dl className="grid grid-cols-[10rem_1fr] gap-y-2 text-sm">
          <dt className="text-slate-400">Crime type</dt><dd>{detail.crime_type}</dd>
          <dt className="text-slate-400">Police station</dt><dd>{detail.police_station}</dd>
          <dt className="text-slate-400">Assigned IO</dt>
          <dd>{detail.assigned_io ? (detail.assigned_io.full_name ?? detail.assigned_io.username) : "—"}</dd>
          <dt className="text-slate-400">Created</dt><dd>{new Date(detail.created_at).toLocaleString()}</dd>
          <dt className="text-slate-400">Updated</dt><dd>{new Date(detail.updated_at).toLocaleString()}</dd>
          <dt className="text-slate-400">Description</dt>
          <dd className="text-slate-300">{detail.description ?? "—"}</dd>
        </dl>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Case members</h2>
        <ul className="mb-4 space-y-2 text-sm">
          {detail.members.map((m) => (
            <li key={m.id} className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
              <span>
                <span className="font-medium">{m.full_name ?? m.username}</span>{" "}
                <span className="text-slate-400">({m.username})</span>{" "}
                <span className="ml-2 rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
                  {m.role_in_case}
                </span>
              </span>
              {detail.can_manage && (
                <button onClick={() => handleRemoveMember(m.user_id)}
                  className="text-xs text-rose-400 underline hover:text-rose-300">
                  Remove
                </button>
              )}
            </li>
          ))}
        </ul>

        {detail.can_manage && (
          <form onSubmit={handleAddMember} className="flex gap-2">
            <input type="email" required value={newMemberEmail}
              onChange={(e) => setNewMemberEmail(e.target.value)}
              placeholder="user email to add…" className={inputClass} />
            <button type="submit" className="whitespace-nowrap rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500">
              Add member
            </button>
          </form>
        )}

        {actionError && (
          <p className="mt-3 rounded-lg border border-rose-800 bg-rose-950/60 px-3 py-2 text-sm text-rose-300">
            {actionError}
          </p>
        )}
      </div>

      {/* Documents (Phase 4): list, upload, download, delete */}
      <DocumentsSection caseId={detail.id} />
    </main>
  );
}
