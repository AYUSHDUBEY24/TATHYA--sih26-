"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "@/lib/auth";
import { CASE_STATUSES, UserBrief } from "@/lib/api-types";
import { PageHeader } from "@/components/ui";
import { useToast } from "@/components/Toast";

export default function NewCasePage() {
  const router = useRouter();
  const { toast } = useToast();
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
      toast({ title: "Case created", variant: "success" });
      router.push(`/cases/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create case");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="Investigation"
        title="Create case"
        description="Register a new case. All authorization rules are enforced by the backend."
      />

      <form onSubmit={handleSubmit} className="card space-y-5 p-6">
        <div>
          <label className="label" htmlFor="title">
            Title
          </label>
          <input
            id="title"
            required
            minLength={3}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input"
            placeholder="Robbery at Central Market"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="crimeType">
              Crime type
            </label>
            <input
              id="crimeType"
              required
              value={crimeType}
              onChange={(e) => setCrimeType(e.target.value)}
              className="input"
              placeholder="ROBBERY"
            />
          </div>
          <div>
            <label className="label" htmlFor="policeStation">
              Police station
            </label>
            <input
              id="policeStation"
              required
              value={policeStation}
              onChange={(e) => setPoliceStation(e.target.value)}
              className="input"
              placeholder="Central Police Station"
            />
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="status">
              Status
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
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
            <label className="label" htmlFor="assignedIo">
              Assigned IO{" "}
              {officers.length === 0 && (
                <span className="font-normal text-slate-500">
                  (not available for your role)
                </span>
              )}
            </label>
            <select
              id="assignedIo"
              value={assignedIoId}
              onChange={(e) => setAssignedIoId(e.target.value)}
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

        <div>
          <label className="label" htmlFor="description">
            Description (optional)
          </label>
          <textarea
            id="description"
            rows={4}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input"
            placeholder="Synthetic demo case summary…"
          />
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
          >
            {error}
          </p>
        )}

        <div className="flex items-center gap-3 border-t border-slate-100 pt-4">
          <button type="submit" disabled={busy} className="btn btn-primary btn-md">
            {busy ? "Creating…" : "Create case"}
          </button>
          <Link href="/cases" className="btn btn-secondary btn-md">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
