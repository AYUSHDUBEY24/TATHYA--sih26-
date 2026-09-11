"use client";

/**
 * Evidence / Chain of Custody section for the case detail workspace.
 *
 * Lists evidence assets for the case, renders a vertical chain-of-custody
 * timeline from the REAL backend transfers (`/api/evidence/{id}/chain`),
 * and lets authorized case members register assets and record custody
 * events. All authorization is enforced by the backend; the UI only hides
 * what the user cannot do.
 */

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/auth";
import {
  ChainOfCustody,
  EVIDENCE_ASSET_TYPES,
  EVIDENCE_TRANSFER_ACTIONS,
  EvidenceAsset,
  EvidenceAssetDetail,
} from "@/lib/api-types";
import { useToast } from "@/components/Toast";
import { formatDateTime, prettifyEnum } from "@/lib/format";
import { IconCheckCircle, IconHistory } from "@/components/icons";

const STATUS_STYLES: Record<string, string> = {
  REGISTERED: "bg-slate-100 text-slate-700 border-slate-200",
  IN_CUSTODY: "bg-blue-50 text-blue-700 border-blue-200",
  UNDER_EXAMINATION: "bg-amber-50 text-amber-700 border-amber-200",
  STORED: "bg-emerald-50 text-emerald-700 border-emerald-200",
  RELEASED: "bg-slate-100 text-slate-500 border-slate-200",
};

function statusBadgeClass(status: string): string {
  return STATUS_STYLES[status] ?? "bg-slate-100 text-slate-700 border-slate-200";
}

export default function EvidenceSection({ caseId }: { caseId: string }) {
  const { toast } = useToast();
  const [assets, setAssets] = useState<EvidenceAsset[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [chain, setChain] = useState<ChainOfCustody | null>(null);

  // Register form state
  const [showRegister, setShowRegister] = useState(false);
  const [regName, setRegName] = useState("");
  const [regType, setRegType] = useState<string>("MOBILE_PHONE");
  const [regHolder, setRegHolder] = useState("");
  const [regError, setRegError] = useState<string | null>(null);
  const [regBusy, setRegBusy] = useState(false);

  // Custody event form state
  const [evAction, setEvAction] = useState<string>("TRANSFERRED");
  const [evFrom, setEvFrom] = useState("");
  const [evTo, setEvTo] = useState("");
  const [evPurpose, setEvPurpose] = useState("");
  const [evError, setEvError] = useState<string | null>(null);
  const [evBusy, setEvBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoadError(null);
      const list = await apiFetch<EvidenceAsset[]>(
        `/api/evidence?case_id=${caseId}`
      );
      setAssets(list);
    } catch (err) {
      setAssets([]);
      setLoadError(err instanceof Error ? err.message : "Could not load evidence");
    }
  }, [caseId]);

  useEffect(() => {
    load();
  }, [load]);

  const openChain = useCallback(async (assetId: string) => {
    setSelected(assetId);
    setChain(null);
    try {
      setChain(await apiFetch<ChainOfCustody>(`/api/evidence/${assetId}/chain`));
    } catch {
      setChain(null);
    }
  }, []);

  async function handleRegister(event: React.FormEvent) {
    event.preventDefault();
    setRegError(null);
    setRegBusy(true);
    try {
      const created = await apiFetch<EvidenceAssetDetail>(
        `/api/evidence?payload_case_id=${caseId}`,
        {
          method: "POST",
          body: JSON.stringify({
            name: regName,
            asset_type: regType,
            current_holder: regHolder,
          }),
        }
      );
      toast({
        title: "Evidence registered",
        description: `${created.asset_tag} — ${created.name}`,
        variant: "success",
      });
      setRegName("");
      setRegHolder("");
      setShowRegister(false);
      await load();
      await openChain(created.id);
    } catch (err) {
      setRegError(err instanceof Error ? err.message : "Could not register evidence");
    } finally {
      setRegBusy(false);
    }
  }

  async function handleCustodyEvent(event: React.FormEvent) {
    event.preventDefault();
    if (!selected) return;
    setEvError(null);
    setEvBusy(true);
    try {
      await apiFetch(`/api/evidence/${selected}/transfers`, {
        method: "POST",
        body: JSON.stringify({
          action: evAction,
          from_party: evFrom || undefined,
          to_party: evTo || undefined,
          purpose: evPurpose || undefined,
        }),
      });
      toast({ title: "Custody event recorded", variant: "success" });
      setEvFrom("");
      setEvTo("");
      setEvPurpose("");
      await load();
      await openChain(selected);
    } catch (err) {
      setEvError(err instanceof Error ? err.message : "Could not record custody event");
    } finally {
      setEvBusy(false);
    }
  }

  return (
    <div className="card mt-8 p-6">
      <div className="flex flex-wrap items-center gap-2">
        <IconHistory className="h-4 w-4 text-slate-500" />
        <h2 className="text-base font-semibold text-slate-900">
          Evidence &amp; Chain of Custody
        </h2>
        <span className="badge badge-muted text-[10px]">
          every transfer is recorded in the audit trail
        </span>
        <button
          onClick={() => setShowRegister((v) => !v)}
          className="btn btn-secondary btn-sm ml-auto"
        >
          {showRegister ? "Close" : "+ Register evidence"}
        </button>
      </div>

      {showRegister && (
        <form
          onSubmit={handleRegister}
          className="mt-4 grid gap-3 rounded-xl border border-slate-200 bg-slate-50/60 p-4 md:grid-cols-3"
        >
          <label className="block md:col-span-2">
            <span className="mb-1 block text-sm font-medium text-slate-700">
              Evidence name
            </span>
            <input
              className="input"
              required
              value={regName}
              onChange={(e) => setRegName(e.target.value)}
              placeholder="e.g. Seized Laptop (fictional demo item)"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-slate-700">Type</span>
            <select
              className="input"
              value={regType}
              onChange={(e) => setRegType(e.target.value)}
            >
              {EVIDENCE_ASSET_TYPES.map((t) => (
                <option key={t} value={t}>
                  {prettifyEnum(t)}
                </option>
              ))}
            </select>
          </label>
          <label className="block md:col-span-2">
            <span className="mb-1 block text-sm font-medium text-slate-700">
              Initial custodian (current holder)
            </span>
            <input
              className="input"
              required
              value={regHolder}
              onChange={(e) => setRegHolder(e.target.value)}
              placeholder="e.g. Investigating Officer"
            />
          </label>
          <div className="flex items-end md:col-span-1">
            <button
              type="submit"
              disabled={regBusy}
              className="btn btn-primary btn-md w-full"
            >
              {regBusy ? "Registering…" : "Register"}
            </button>
          </div>
          {regError && (
            <p role="alert" className="text-sm text-rose-700 md:col-span-3">
              {regError}
            </p>
          )}
        </form>
      )}

      {loadError && (
        <p role="alert" className="mt-3 text-sm text-rose-700">
          {loadError}
        </p>
      )}

      {assets !== null && assets.length === 0 && !loadError && (
        <p className="mt-4 text-sm text-slate-500">
          No evidence assets registered for this case yet.
        </p>
      )}

      {assets && assets.length > 0 && (
        <ul className="mt-4 space-y-2">
          {assets.map((a) => (
            <li
              key={a.id}
              className={`flex flex-wrap items-center justify-between gap-3 rounded-lg border px-3 py-2.5 text-sm ${
                selected === a.id
                  ? "border-blue-300 bg-blue-50/60"
                  : "border-slate-200 bg-slate-50/60"
              }`}
            >
              <div className="min-w-0">
                <p className="font-medium text-slate-800">
                  <span className="font-mono text-xs text-slate-500">{a.asset_tag}</span>{" "}
                  {a.name}
                </p>
                <p className="text-xs text-slate-500">
                  {prettifyEnum(a.asset_type)} · holder: {a.current_holder}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <span
                  className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold ${statusBadgeClass(a.status)}`}
                >
                  {prettifyEnum(a.status)}
                </span>
                <button
                  onClick={() => (selected === a.id ? setSelected(null) : openChain(a.id))}
                  className="btn btn-secondary btn-sm"
                >
                  {selected === a.id ? "Hide chain" : "Chain of custody"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {selected && (
        <div className="mt-4 rounded-xl border border-slate-200 p-4">
          {chain === null ? (
            <p className="text-sm text-slate-500">Loading custody chain…</p>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-semibold text-slate-900">
                  <span className="font-mono text-sm">{chain.asset.asset_tag}</span>{" "}
                  {chain.asset.name}
                </h3>
                <span
                  className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold ${statusBadgeClass(chain.asset.status)}`}
                >
                  {prettifyEnum(chain.asset.status)}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Case {chain.case_number} · {chain.case_title} · current holder:{" "}
                {chain.asset.current_holder}
              </p>

              {/* Vertical custody timeline (real transfer events only) */}
              <ol className="mt-4">
                {chain.transfers.map((t, i) => (
                  <li key={t.id} className="relative flex gap-3 pb-5">
                    {i < chain.transfers.length - 1 && (
                      <span
                        aria-hidden
                        className="absolute left-[11px] top-6 h-full w-0.5 bg-slate-200"
                      />
                    )}
                    <span
                      className={`mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 ${
                        i === chain.transfers.length - 1
                          ? "border-blue-500 bg-blue-500 text-white"
                          : "border-emerald-500 bg-emerald-50 text-emerald-600"
                      }`}
                    >
                      <IconCheckCircle className="h-3.5 w-3.5" />
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-800">
                        {prettifyEnum(t.action)}
                        {t.to_party && (
                          <span className="font-normal text-slate-600">
                            {" "}
                            → {t.to_party}
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-slate-500">
                        {formatDateTime(t.occurred_at)} · by {t.actor_name}
                        {t.from_party ? ` · from ${t.from_party}` : ""}
                      </p>
                      {t.purpose && (
                        <p className="mt-0.5 text-xs text-slate-600">{t.purpose}</p>
                      )}
                    </div>
                  </li>
                ))}
              </ol>

              {/* Record a custody event (backend enforces case membership) */}
              <form
                onSubmit={handleCustodyEvent}
                className="mt-2 grid gap-3 rounded-xl border border-slate-200 bg-slate-50/60 p-4 md:grid-cols-4"
              >
                <label className="block">
                  <span className="mb-1 block text-sm font-medium text-slate-700">
                    Action
                  </span>
                  <select
                    className="input"
                    value={evAction}
                    onChange={(e) => setEvAction(e.target.value)}
                  >
                    {EVIDENCE_TRANSFER_ACTIONS.map((a) => (
                      <option key={a} value={a}>
                        {prettifyEnum(a)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-1 block text-sm font-medium text-slate-700">
                    From (optional)
                  </span>
                  <input
                    className="input"
                    value={evFrom}
                    onChange={(e) => setEvFrom(e.target.value)}
                    placeholder={chain.asset.current_holder}
                  />
                </label>
                <label className="block">
                  <span className="mb-1 block text-sm font-medium text-slate-700">
                    To / custodian
                  </span>
                  <input
                    className="input"
                    value={evTo}
                    onChange={(e) => setEvTo(e.target.value)}
                    placeholder="e.g. Central Forensic Lab"
                  />
                </label>
                <label className="block">
                  <span className="mb-1 block text-sm font-medium text-slate-700">
                    Purpose (optional)
                  </span>
                  <input
                    className="input"
                    value={evPurpose}
                    onChange={(e) => setEvPurpose(e.target.value)}
                    placeholder="e.g. Forensic examination"
                  />
                </label>
                <div className="md:col-span-4">
                  <button
                    type="submit"
                    disabled={evBusy}
                    className="btn btn-primary btn-md"
                  >
                    {evBusy ? "Recording…" : "Record custody event"}
                  </button>
                  {evError && (
                    <p role="alert" className="mt-2 text-sm text-rose-700">
                      {evError}
                    </p>
                  )}
                </div>
              </form>
            </>
          )}
        </div>
      )}
    </div>
  );
}
