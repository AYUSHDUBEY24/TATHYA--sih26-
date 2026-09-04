"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiDownload, apiFetch, apiUpload } from "@/lib/auth";
import {
  CLASSIFICATIONS,
  DOCUMENT_TYPES,
  DocumentItem,
  DocumentVersion,
  IntegrityResult,
  BlockchainStatusResult,
  BlockchainVerifyResult,
} from "@/lib/api-types";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsSection({ caseId }: { caseId: string }) {
  const [docs, setDocs] = useState<DocumentItem[] | null>(null);
  const [selected, setSelected] = useState<DocumentItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    document_type: "FIR",
    classification: "RESTRICTED",
    description: "",
  });
  const fileInputRef = useRef<HTMLInputElement>(null);
  const versionInputRef = useRef<HTMLInputElement>(null);
  const [history, setHistory] = useState<DocumentVersion[] | null>(null);
  const [integrity, setIntegrity] = useState<IntegrityResult | null>(null);
  const [verifyBusy, setVerifyBusy] = useState(false);
  const [versionBusy, setVersionBusy] = useState(false);
  const [changeNote, setChangeNote] = useState("");
  const [bcStatus, setBcStatus] = useState<BlockchainStatusResult | null>(null);
  const [bcVerify, setBcVerify] = useState<BlockchainVerifyResult | null>(null);
  const [registerBusy, setRegisterBusy] = useState(false);
  const [bcVerifyBusy, setBcVerifyBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setDocs(await apiFetch<DocumentItem[]>(`/api/documents?case_id=${caseId}`));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load documents");
    }
  }, [caseId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      setError("Choose a file to upload");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("case_id", caseId);
      formData.append("document_type", uploadForm.document_type);
      formData.append("classification", uploadForm.classification);
      formData.append("description", uploadForm.description);
      await apiUpload<DocumentItem>("/api/documents/upload", formData);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setUploadForm((f) => ({ ...f, description: "" }));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleDownload(doc: DocumentItem) {
    setError(null);
    try {
      await apiDownload(`/api/documents/${doc.id}/download`, doc.file_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    }
  }

  const selectDoc = useCallback(
    (doc: DocumentItem) => {
      setSelected((prev) => (prev?.id === doc.id ? null : doc));
      setIntegrity(null);
      setHistory(null);
      setBcStatus(null);
      setBcVerify(null);
      apiFetch<DocumentVersion[]>(`/api/documents/${doc.id}/versions`)
        .then(setHistory)
        .catch(() => setHistory(null));
    },
    []
  );

  async function handleVerify(doc: DocumentItem) {
    setVerifyBusy(true);
    setError(null);
    try {
      setIntegrity(
        await apiFetch<IntegrityResult>(`/api/documents/${doc.id}/integrity`)
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setVerifyBusy(false);
    }
  }

  async function handleRegisterBc(doc: DocumentItem) {
    setRegisterBusy(true);
    setError(null);
    try {
      const result = await apiFetch<BlockchainStatusResult>(
        `/api/blockchain/register?document_id=${doc.id}`,
        { method: "POST" }
      );
      setBcStatus(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Blockchain registration failed");
    } finally {
      setRegisterBusy(false);
    }
  }

  async function handleBcVerify(doc: DocumentItem) {
    setBcVerifyBusy(true);
    setError(null);
    try {
      setBcVerify(
        await apiFetch<BlockchainVerifyResult>(
          `/api/blockchain/${doc.id}/verify`
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Blockchain verification failed");
    } finally {
      setBcVerifyBusy(false);
    }
  }

  async function handleBcStatus(doc: DocumentItem) {
    try {
      setBcStatus(
        await apiFetch<BlockchainStatusResult>(
          `/api/blockchain/${doc.id}/status`
        )
      );
    } catch {
      setBcStatus(null);
    }
  }

  async function handleNewVersion(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const file = versionInputRef.current?.files?.[0];
    if (!file) {
      setError("Choose a file for the new version");
      return;
    }
    setVersionBusy(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (changeNote) formData.append("change_note", changeNote);
      await apiUpload(`/api/documents/${selected.id}/versions`, formData);
      if (versionInputRef.current) versionInputRef.current.value = "";
      setChangeNote("");
      await load();
      selectDoc({ ...selected, current_version_number: (selected.current_version_number ?? 0) + 1 });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Version upload failed");
    } finally {
      setVersionBusy(false);
    }
  }

  async function handleDelete(doc: DocumentItem) {
    setError(null);
    try {
      await apiFetch(`/api/documents/${doc.id}`, { method: "DELETE" });
      if (selected?.id === doc.id) setSelected(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-sky-500";

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
      <h2 className="mb-4 text-lg font-semibold">Documents</h2>

      {error && (
        <p className="mb-4 rounded-lg border border-rose-800 bg-rose-950/60 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      )}

      {docs && docs.length === 0 && (
        <p className="mb-4 text-sm text-slate-400">
          No documents uploaded to this case yet.
        </p>
      )}

      {docs && docs.length > 0 && (
        <div className="mb-6 overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-3 py-2">File</th>
                <th className="px-3 py-2">Type</th>
                <th className="px-3 py-2">Classification</th>
                <th className="px-3 py-2">Uploaded by</th>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((doc) => (
                <tr key={doc.id} className="border-b border-slate-800/60">
                  <td className="px-3 py-2">
                    <button
                      onClick={() => selectDoc(doc)}
                      className="text-sky-400 underline"
                    >
                      {doc.file_name}
                    </button>
                  </td>
                  <td className="px-3 py-2 text-slate-400">{doc.document_type}</td>
                  <td className="px-3 py-2">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
                      {doc.classification}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-400">
                    {doc.uploader ? (doc.uploader.full_name ?? doc.uploader.username) : "—"}
                  </td>
                  <td className="px-3 py-2 text-slate-400">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-2">
                      <button onClick={() => handleDownload(doc)}
                        className="text-xs text-sky-400 underline">Download</button>
                      {doc.can_delete && (
                        <button onClick={() => handleDelete(doc)}
                          className="text-xs text-rose-400 underline">Delete</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Document detail (selected): version + integrity + history */}
      {selected && (
        <div className="mb-6 rounded-lg border border-slate-700 bg-slate-950/60 p-4 text-sm">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <p className="font-semibold text-slate-200">{selected.file_name}</p>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => handleVerify(selected)}
                disabled={verifyBusy}
                className="rounded-lg border border-sky-700 px-3 py-1 text-xs font-semibold text-sky-300 transition hover:bg-sky-950 disabled:opacity-50">
                {verifyBusy ? "Verifying…" : "Verify integrity"}
              </button>
              <button onClick={() => handleRegisterBc(selected)}
                disabled={registerBusy}
                className="rounded-lg border border-amber-700 px-3 py-1 text-xs font-semibold text-amber-300 transition hover:bg-amber-950 disabled:opacity-50"
                title="Anchor this document's hash on the local blockchain">
                {registerBusy ? "Anchoring…" : "Register on Blockchain"}
              </button>
              <button onClick={() => handleBcVerify(selected)}
                disabled={bcVerifyBusy}
                className="rounded-lg border border-violet-700 px-3 py-1 text-xs font-semibold text-violet-300 transition hover:bg-violet-950 disabled:opacity-50"
                title="Verify file + DB + blockchain hashes">
                {bcVerifyBusy ? "Verifying…" : "Verify Blockchain"}
              </button>
            </div>
          </div>

          {/* Blockchain anchor status */}
          <div className="mb-3 rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-300">Blockchain Integrity</span>
              <button onClick={() => handleBcStatus(selected)}
                className="text-xs text-sky-400 underline">Refresh</button>
            </div>
            {bcStatus ? (
              <div className="mt-1 space-y-0.5">
                <p>Status: <span className={
                  bcStatus.status === "CONFIRMED" ? "text-emerald-300" :
                  bcStatus.status === "FAILED" ? "text-rose-300" :
                  bcStatus.status === "PENDING" ? "text-amber-300" :
                  "text-slate-400"
                }>{bcStatus.status}</span></p>
                {bcStatus.transaction_hash && (
                  <p className="break-all font-mono">Tx: {bcStatus.transaction_hash}</p>
                )}
                {bcStatus.block_number != null && (
                  <p>Block: {bcStatus.block_number}</p>
                )}
                {bcStatus.anchored_at && (
                  <p>Anchored: {new Date(bcStatus.anchored_at).toLocaleString()}</p>
                )}
                {bcStatus.error_message && (
                  <p className="text-rose-300">Error: {bcStatus.error_message}</p>
                )}
              </div>
            ) : (
              <p className="mt-1 text-slate-400">Click "Register on Blockchain" to anchor, or "Refresh" to check status.</p>
            )}
          </div>

          {/* Blockchain verify result */}
          {bcVerify && (
            <div className={`mb-3 rounded-lg border px-3 py-2 text-xs ${
              bcVerify.status === "VERIFIED"
                ? "border-emerald-700 bg-emerald-950/40 text-emerald-300"
                : bcVerify.status === "BLOCKCHAIN_UNAVAILABLE"
                ? "border-amber-700 bg-amber-950/40 text-amber-300"
                : "border-rose-700 bg-rose-950/40 text-rose-300"
            }`}>
              <p className="font-semibold">
                {bcVerify.status === "VERIFIED" ? "✅ Blockchain VERIFIED" :
                 bcVerify.status === "FILE_INTEGRITY_FAILURE" ? "🚨 File integrity failure" :
                 bcVerify.status === "BLOCKCHAIN_MISMATCH" ? "🚨 Blockchain hash mismatch" :
                 bcVerify.status === "BLOCKCHAIN_UNAVAILABLE" ? "⚠️ Blockchain unavailable" :
                 "— Not anchored"}
              </p>
              {bcVerify.blockchain_hash && (
                <p className="mt-1 break-all font-mono">On-chain hash: {bcVerify.blockchain_hash}</p>
              )}
              {bcVerify.transaction_hash && (
                <p className="break-all font-mono">Tx: {bcVerify.transaction_hash}</p>
              )}
              {bcVerify.verified_at && (
                <p>Verified: {new Date(bcVerify.verified_at).toLocaleString()}</p>
              )}
            </div>
          )}

          {/* Integrity status */}
          {integrity && (
            <div
              className={`mb-3 rounded-lg border px-3 py-2 ${
                integrity.status === "VERIFIED"
                  ? "border-emerald-700 bg-emerald-950/40 text-emerald-300"
                  : "border-rose-700 bg-rose-950/40 text-rose-300"
              }`}
            >
              <p className="font-semibold">
                {integrity.status === "VERIFIED"
                  ? "✅ Integrity VERIFIED"
                  : "🚨 INTEGRITY FAILURE"}
                {" "}(v{integrity.version})
              </p>
              <p className="mt-1 break-all font-mono text-xs">
                Stored hash: {integrity.stored_hash}
              </p>
              <p className="break-all font-mono text-xs">
                Current hash: {integrity.current_hash}
              </p>
            </div>
          )}

          <dl className="grid grid-cols-[9rem_1fr] gap-y-1">
            <dt className="text-slate-400">Current version</dt>
            <dd>v{selected.current_version_number ?? "—"}</dd>
            <dt className="text-slate-400">Current hash</dt>
            <dd className="break-all font-mono text-xs">
              {selected.current_hash ?? "—"}
            </dd>
            <dt className="text-slate-400">Status</dt>
            <dd>{selected.status}</dd>
            <dt className="text-slate-400">Size</dt>
            <dd>{formatBytes(selected.size_bytes)}</dd>
            <dt className="text-slate-400">Description</dt>
            <dd className="text-slate-300">{selected.description ?? "—"}</dd>
          </dl>

          {/* Version history */}
          <p className="mt-4 mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
            Version history
          </p>
          {history && history.length > 0 && (
            <ul className="mb-3 space-y-1">
              {history.map((v) => (
                <li
                  key={v.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded border border-slate-800 bg-slate-900/60 px-3 py-1.5"
                >
                  <span>
                    <span className="font-semibold text-slate-200">v{v.version_number}</span>{" "}
                    — uploaded by {v.uploader ? (v.uploader.full_name ?? v.uploader.username) : "—"}{" "}
                    · {new Date(v.created_at).toLocaleDateString()}
                    {v.change_note && (
                      <span className="text-slate-400"> · {v.change_note}</span>
                    )}
                  </span>
                  <button
                    onClick={() => apiDownload(`/api/versions/${v.id}/download`, v.file_name)}
                    className="text-xs text-sky-400 underline"
                  >
                    Download
                  </button>
                </li>
              ))}
            </ul>
          )}

          {/* Upload new version */}
          <form onSubmit={handleNewVersion} className="mt-3 flex flex-wrap gap-2 border-t border-slate-800 pt-3">
            <input ref={versionInputRef} type="file" required className="flex-1 text-xs text-slate-300" />
            <input
              value={changeNote}
              onChange={(e) => setChangeNote(e.target.value)}
              placeholder="Change note (optional)"
              className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs outline-none focus:border-sky-500"
            />
            <button
              type="submit"
              disabled={versionBusy}
              className="rounded-lg bg-sky-600 px-3 py-2 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-50"
            >
              {versionBusy ? "Uploading…" : "Upload new version"}
            </button>
          </form>
        </div>
      )}

      {/* Upload form */}
      <form onSubmit={handleUpload} className="space-y-3 border-t border-slate-800 pt-4">
        <p className="text-sm font-medium text-slate-300">Upload document</p>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs text-slate-400">Document type</label>
            <select
              value={uploadForm.document_type}
              onChange={(e) =>
                setUploadForm({ ...uploadForm, document_type: e.target.value })
              }
              className={inputClass}
            >
              {DOCUMENT_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-400">Classification</label>
            <select
              value={uploadForm.classification}
              onChange={(e) =>
                setUploadForm({ ...uploadForm, classification: e.target.value })
              }
              className={inputClass}
            >
              {CLASSIFICATIONS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">
            File (PDF/image/document, max 50 MB)
          </label>
          <input ref={fileInputRef} type="file" required className={inputClass} />
        </div>
        <div>
          <label className="mb-1 block text-xs text-slate-400">Description (optional)</label>
          <input
            value={uploadForm.description}
            onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
            className={inputClass}
            placeholder="Short description…"
          />
        </div>
        <button
          type="submit"
          disabled={busy}
          className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-500 disabled:opacity-50"
        >
          {busy ? "Uploading…" : "Upload"}
        </button>
      </form>
    </div>
  );
}
