"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/auth";
import { CASE_STATUSES, UserBrief } from "@/lib/api-types";

export default function NewCasePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [crimeType, setCrimeType] = useState("");
  const [policeStation, setPoliceStation] = useState("");
  const [status, setStatus] = useState<string>("OPEN");
  const [description, setDescription] = useState("");
  const [assignedIoId, setAssignedIoId] = useState<string>("");
  const [officers, setOfficers] = useState<UserBrief[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // Officers list is only available to ADMIN/IO — ignore failures quietly.
    apiFetch<UserBrief[]>("/api/users/officers")
      .then(setOfficers)
      .catch(() => setOfficers([]));
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const created = await apiFetch<{ id: string }>("/api/cases", {
        method: "POST",
        body: JSON.stringify({
          title,
          crime_type: crimeType,
          police_station: policeStation,
          status,
          description: description || null,
          assigned_io_id: assignedIoId || null,
        }),
      });
      router.push(`/cases/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create case");
    } finally {
      setBusy(false);
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-sky-500";

  return (
    <main className="mx-auto min-h-screen max-w-2xl p-8">
      <Link href="/cases" className="text-sm text-sky-400 underline">
        ← Back to cases
      </Link>
      <h1 className="mb-6 mt-3 text-2xl font-bold">Create case</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-slate-400" htmlFor="title">Title</label>
          <input id="title" required minLength={3} value={title}
            onChange={(e) => setTitle(e.target.value)} className={inputClass}
            placeholder="Robbery at Central Market" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm text-slate-400" htmlFor="crimeType">Crime type</label>
            <input id="crimeType" required value={crimeType}
              onChange={(e) => setCrimeType(e.target.value)} className={inputClass}
              placeholder="ROBBERY" />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-400" htmlFor="policeStation">Police station</label>
            <input id="policeStation" required value={policeStation}
              onChange={(e) => setPoliceStation(e.target.value)} className={inputClass}
              placeholder="Central Police Station" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm text-slate-400" htmlFor="status">Status</label>
            <select id="status" value={status} onChange={(e) => setStatus(e.target.value)} className={inputClass}>
              {CASE_STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-400" htmlFor="assignedIo">
              Assigned IO {officers.length === 0 && "(not available for your role)"}
            </label>
            <select id="assignedIo" value={assignedIoId}
              onChange={(e) => setAssignedIoId(e.target.value)}
              className={inputClass} disabled={officers.length === 0}>
              <option value="">— Unassigned —</option>
              {officers.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.full_name ?? o.username}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-400" htmlFor="description">Description (optional)</label>
          <textarea id="description" rows={4} value={description}
            onChange={(e) => setDescription(e.target.value)} className={inputClass}
            placeholder="Synthetic demo case summary…" />
        </div>

        {error && (
          <p className="rounded-lg border border-rose-800 bg-rose-950/60 px-3 py-2 text-sm text-rose-300">
            {error}
          </p>
        )}

        <button type="submit" disabled={busy}
          className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-500 disabled:opacity-50">
          {busy ? "Creating…" : "Create case"}
        </button>
      </form>
    </main>
  );
}
