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
import { Button, Skeleton } from "./ui";
import { DocumentCard, DocumentRow } from "./DocumentRow";
import {
  BlockchainStatusBadge,
  IntegrityBadge,
  VerifiedAt,
} from "./IntegrityBadge";
import { Modal } from "./Modal";
import { useToast } from "./Toast";
import { IconAlertTriangle, IconFileText, IconShield } from "./icons";
import { copyText, formatBytes, formatDateTime, shortHash } from "@/lib/format";

/**
 * Case documents & evidence section.
 *
 * ALL API handlers (upload, download, delete, new version, integrity
 * verification, blockchain register/verify/status) are preserved from the
 * original implementation with identical request/response contracts.
 */
export default function DocumentsSection({ caseId }: { caseId: string }) {
  const { toast } = useToast();
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
  const [deleteTarget, setDeleteTarget] = useState<DocumentItem | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);
  // Demo tampering test (demo-only feature, see /api/demo endpoints)
  const [demoConfirmOpen, setDemoConfirmOpen] = useState(false);
  const [demoBusy, setDemoBusy] = useState<"tamper" | "restore" | null>(null);
  const [demoTampered, setDemoTampered] = useState(false);

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
      // The upload endpoint returns the created document — use it to surface
      // the new document immediately (list refresh + detail panel selection).
      const created = await apiUpload<DocumentItem>(
        "/api/documents/upload",
        formData
      );
      if (fileInputRef.current) fileInputRef.current.value = "";
      setUploadForm((f) => ({ ...f, description: "" }));
      toast({
        title: "Document uploaded",
        description: "SHA-256 recorded and audit event created.",
        variant: "success",
      });
      await load();
      if (created?.id) {
        selectDoc(created);
      }
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
      setDemoTampered(false);
      setDemoConfirmOpen(false);
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

  // --- DEMO tampering test (demo-only backend feature; verification itself
  // stays entirely in the existing real endpoints — nothing is faked). ---
  async function handleDemoTamper(doc: DocumentItem) {
    setDemoBusy("tamper");
    setError(null);
    try {
      await apiFetch(`/api/demo/${doc.id}/tamper`, { method: "POST" });
      setDemoTampered(true);
      setDemoConfirmOpen(false);
      // Stale results must not linger — the user re-runs the REAL checks.
      setIntegrity(null);
      setBcVerify(null);
      toast({
        title: "Demo tampering applied",
        description:
          "The stored file was modified without a new version. Run Verify integrity / Verify Blockchain to see the real detection.",
        variant: "info",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo tampering failed");
      setDemoConfirmOpen(false);
    } finally {
      setDemoBusy(null);
    }
  }

  async function handleDemoRestore(doc: DocumentItem) {
    setDemoBusy("restore");
    setError(null);
    try {
      await apiFetch(`/api/demo/${doc.id}/restore`, { method: "POST" });
      setDemoTampered(false);
      setIntegrity(null);
      setBcVerify(null);
      toast({
        title: "Original restored",
        description:
          "The exact original bytes were restored. Verification should report VERIFIED again.",
        variant: "success",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo restore failed");
    } finally {
      setDemoBusy(null);
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
      toast({ title: "New version uploaded", variant: "success" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Version upload failed");
    } finally {
      setVersionBusy(false);
    }
  }

  // Delete is only performed after explicit confirmation in the modal.
  async function performDelete(doc: DocumentItem) {
    setDeleteBusy(true);
    setError(null);
    try {
      await apiFetch(`/api/documents/${doc.id}`, { method: "DELETE" });
      if (selected?.id === doc.id) setSelected(null);
      setDeleteTarget(null);
      toast({ title: "Document deleted", variant: "success" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeleteBusy(false);
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-2">
        <IconFileText className="h-5 w-5 text-slate-500" />
        <h2 className="text-lg font-semibold text-slate-900">
          Documents &amp; Evidence
        </h2>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          {error}
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-5">
        {/* LEFT: document list + preview + upload */}
        <div className="space-y-4 xl:col-span-3">
          <div className="card overflow-hidden">
            <div className="border-b border-slate-100 px-5 py-3">
              <h3 className="text-sm font-semibold text-slate-900">
                Case documents {docs ? `(${docs.length})` : ""}
              </h3>
            </div>
            {docs === null ? (
              <div className="space-y-3 p-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : docs.length === 0 ? (
              <p className="px-5 py-6 text-sm text-slate-500">
                No documents uploaded to this case yet.
              </p>
            ) : (
              <>
                {/* Desktop: compact table */}
                <div className="hidden overflow-x-auto md:block">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>File</th>
                        <th>Type</th>
                        <th>Classification</th>
                        <th>Uploaded by</th>
                        <th>Date</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {docs.map((doc) => (
                        <DocumentRow
                          key={doc.id}
                          doc={doc}
                          selected={selected?.id === doc.id}
                          onSelect={() => selectDoc(doc)}
                          onDownload={() => handleDownload(doc)}
                          onDelete={
                            doc.can_delete ? () => setDeleteTarget(doc) : undefined
                          }
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
                {/* Mobile: card list (no forced horizontal scroll) */}
                <ul className="divide-y divide-slate-100 md:hidden">
                  {docs.map((doc) => (
                    <li key={doc.id}>
                      <DocumentCard
                        doc={doc}
                        selected={selected?.id === doc.id}
                        onSelect={() => selectDoc(doc)}
                        onDownload={() => handleDownload(doc)}
                        onDelete={
                          doc.can_delete ? () => setDeleteTarget(doc) : undefined
                        }
                      />
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>

          {/* Upload form */}
          <form onSubmit={handleUpload} className="card space-y-3 p-5">
            <div>
              <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <IconFileText className="h-4 w-4 text-slate-500" />
                Tathya Ingest — Secure Document Entry
              </h3>
              <p className="mt-0.5 text-xs text-slate-500">
                Uploaded files are stored securely, hashed with SHA-256 and
                recorded in the audit trail.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="label" htmlFor="upload-type">Document type</label>
                <select
                  id="upload-type"
                  value={uploadForm.document_type}
                  onChange={(e) =>
                    setUploadForm({ ...uploadForm, document_type: e.target.value })
                  }
                  className="input"
                >
                  {DOCUMENT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label" htmlFor="upload-class">Classification</label>
                <select
                  id="upload-class"
                  value={uploadForm.classification}
                  onChange={(e) =>
                    setUploadForm({ ...uploadForm, classification: e.target.value })
                  }
                  className="input"
                >
                  {CLASSIFICATIONS.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="label" htmlFor="upload-file">
                File (PDF/image/document, max 50 MB)
              </label>
              <input
                ref={fileInputRef}
                id="upload-file"
                type="file"
                required
                className="input file:mr-3 file:rounded-md file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-blue-700"
              />
            </div>
            <div>
              <label className="label" htmlFor="upload-desc">Description (optional)</label>
              <input
                id="upload-desc"
                value={uploadForm.description}
                onChange={(e) =>
                  setUploadForm({ ...uploadForm, description: e.target.value })
                }
                className="input"
                placeholder="Short description…"
              />
            </div>
            <button type="submit" disabled={busy} className="btn btn-primary btn-md">
              {busy ? "Uploading…" : "Upload document"}
            </button>
          </form>
        </div>

        {/* RIGHT: selected document detail — metadata, integrity, versions, blockchain */}
        <div className="xl:col-span-2">
          {selected ? (
            <div className="card space-y-5 p-5 xl:sticky xl:top-6">
              {/* Document summary */}
              <div>
                <div className="flex items-start gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                    <IconFileText className="h-5 w-5" />
                  </span>
                  <div className="min-w-0">
                    <p className="break-words text-sm font-semibold text-slate-900">
                      {selected.file_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatBytes(selected.size_bytes)} ·{" "}
                      {selected.content_type || "unknown type"}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDownload(selected)}
                  className="btn btn-secondary btn-sm mt-3 w-full"
                >
                  Download to view
                </button>
              </div>

              {/* Metadata */}
              <dl className="grid grid-cols-[8rem_1fr] gap-y-1.5 text-xs">
                <dt className="text-slate-500">Document type</dt>
                <dd className="text-slate-900">{selected.document_type.replace(/_/g, " ")}</dd>
                <dt className="text-slate-500">Classification</dt>
                <dd><span className="badge badge-muted">{selected.classification}</span></dd>
                <dt className="text-slate-500">Status</dt>
                <dd className="text-slate-900">{selected.status}</dd>
                <dt className="text-slate-500">Current version</dt>
                <dd className="text-slate-900">v{selected.current_version_number ?? "—"}</dd>
                <dt className="text-slate-500">Uploaded by</dt>
                <dd className="text-slate-900">
                  {selected.uploader
                    ? (selected.uploader.full_name ?? selected.uploader.username)
                    : "—"}
                </dd>
                <dt className="text-slate-500">Created</dt>
                <dd className="text-slate-900">{formatDateTime(selected.created_at)}</dd>
                <dt className="text-slate-500">Updated</dt>
                <dd className="text-slate-900">{formatDateTime(selected.updated_at)}</dd>
                <dt className="text-slate-500">Description</dt>
                <dd className="text-slate-700">{selected.description ?? "—"}</dd>
              </dl>

              {/* SHA-256 */}
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-slate-700">SHA-256 hash</p>
                  {selected.current_hash && (
                    <button
                      onClick={async () => {
                        const ok = await copyText(selected.current_hash!);
                        toast({
                          title: ok ? "Hash copied to clipboard" : "Copy failed",
                          variant: ok ? "success" : "error",
                        });
                      }}
                      className="text-xs font-medium text-blue-600 hover:underline"
                    >
                      Copy
                    </button>
                  )}
                </div>
                <p className="mt-1 break-all font-mono text-[11px] text-slate-700">
                  {selected.current_hash ?? "—"}
                </p>
              </div>

              {/* Integrity verification */}
              <div>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-slate-700">
                    Tathya Verify — Integrity Check
                  </p>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleVerify(selected)}
                    disabled={verifyBusy}
                  >
                    {verifyBusy ? "Verifying…" : "Verify integrity"}
                  </Button>
                </div>
                <div className="mt-2">
                  <IntegrityBadge
                    status={integrity?.status ?? null}
                    verifiedAt={integrity?.verified_at}
                  />
                </div>

                {/* Prominent tamper alert — only shown when the real
                    verification API reports a hash mismatch. */}
                {integrity?.status === "INTEGRITY_FAILURE" && (
                  <div
                    role="alert"
                    className="mt-2 rounded-lg border-2 border-rose-300 bg-rose-50 p-3"
                  >
                    <p className="flex items-center gap-1.5 text-sm font-bold text-rose-700">
                      <IconAlertTriangle className="h-4 w-4" />
                      INTEGRITY FAILURE — POSSIBLE TAMPERING
                    </p>
                    <p className="mt-1 text-[11px] text-rose-700">
                      The file content no longer matches the recorded hash. The
                      result has been written to the audit trail.
                    </p>
                    <div className="mt-2 space-y-1 text-[11px]">
                      <p className="text-slate-700">
                        <span className="font-semibold">Expected hash:</span>{" "}
                        <span className="break-all font-mono">
                          {integrity.stored_hash}
                        </span>
                      </p>
                      <p className="text-slate-700">
                        <span className="font-semibold">Actual hash:</span>{" "}
                        <span className="break-all font-mono">
                          {integrity.current_hash}
                        </span>
                      </p>
                    </div>
                    <VerifiedAt at={integrity.verified_at} />
                  </div>
                )}

                {integrity && integrity.status !== "INTEGRITY_FAILURE" && (
                  <div className="mt-2 rounded-lg border border-slate-200 bg-white p-3 text-[11px]">
                    <p className="font-semibold text-slate-800">
                      Version v{integrity.version} ·{" "}
                      {integrity.status === "VERIFIED"
                        ? "hash matches recorded SHA-256"
                        : integrity.status}
                    </p>
                    <p className="mt-1 break-all font-mono text-slate-600">
                      Stored: {integrity.stored_hash}
                    </p>
                    <p className="break-all font-mono text-slate-600">
                      Current: {integrity.current_hash}
                    </p>
                    <VerifiedAt at={integrity.verified_at} />
                  </div>
                )}
              </div>

              {/* Blockchain anchoring */}
              <div className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
                    <IconShield className="h-3.5 w-3.5 text-violet-600" />
                    Blockchain anchoring
                  </p>
                  <button
                    onClick={() => handleBcStatus(selected)}
                    className="text-xs font-medium text-blue-600 hover:underline"
                  >
                    Refresh
                  </button>
                </div>
                <div className="mt-2">
                  <BlockchainStatusBadge status={bcStatus?.status ?? null} />
                </div>
                {bcStatus ? (
                  <div className="mt-2 space-y-0.5 text-[11px] text-slate-600">
                    {bcStatus.blockchain_key && (
                      <p className="break-all font-mono">
                        Key: {shortHash(bcStatus.blockchain_key, 14, 6)}
                      </p>
                    )}
                    {bcStatus.transaction_hash && (
                      <p className="break-all font-mono">
                        Tx: {shortHash(bcStatus.transaction_hash, 14, 6)}
                      </p>
                    )}
                    {bcStatus.block_number != null && (
                      <p>Block: {bcStatus.block_number}</p>
                    )}
                    {bcStatus.anchored_at && (
                      <p>Anchored: {formatDateTime(bcStatus.anchored_at)}</p>
                    )}
                    {bcStatus.error_message && (
                      <p className="text-rose-600">Error: {bcStatus.error_message}</p>
                    )}
                  </div>
                ) : (
                  <p className="mt-1.5 text-[11px] text-slate-500">
                    Anchor this version&apos;s hash on the local blockchain, or
                    refresh to check anchor status.
                  </p>
                )}
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleRegisterBc(selected)}
                    disabled={registerBusy}
                    title="Anchor this document's hash on the local blockchain"
                  >
                    {registerBusy ? "Anchoring…" : "Register hash"}
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleBcVerify(selected)}
                    disabled={bcVerifyBusy}
                    title="Verify file + DB + blockchain hashes"
                  >
                    {bcVerifyBusy ? "Verifying…" : "Verify blockchain"}
                  </Button>
                </div>
                {bcVerify && (
                  <div
                    className={`mt-2 rounded-lg border p-2.5 text-[11px] ${
                      bcVerify.status === "VERIFIED"
                        ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                        : bcVerify.status === "BLOCKCHAIN_UNAVAILABLE"
                        ? "border-amber-200 bg-amber-50 text-amber-800"
                        : "border-2 border-rose-300 bg-rose-50 text-rose-800"
                    }`}
                  >
                    <p className="font-bold">
                      {bcVerify.status === "VERIFIED"
                        ? "✅ BLOCKCHAIN VERIFIED"
                        : bcVerify.status === "FILE_INTEGRITY_FAILURE"
                        ? "🚨 TAMPERED / INTEGRITY FAILURE"
                        : bcVerify.status === "BLOCKCHAIN_MISMATCH"
                        ? "🚨 TAMPERED / BLOCKCHAIN MISMATCH"
                        : bcVerify.status === "BLOCKCHAIN_UNAVAILABLE"
                        ? "⚠️ Blockchain unavailable"
                        : "— Not anchored"}
                    </p>
                    {bcVerify.status !== "VERIFIED" &&
                      bcVerify.status !== "BLOCKCHAIN_UNAVAILABLE" &&
                      bcVerify.status !== "NOT_ANCHORED" && (
                        <div className="mt-1.5 space-y-0.5">
                          <p className="break-all font-mono">
                            Expected hash: {shortHash(bcVerify.stored_hash)}
                          </p>
                          <p className="break-all font-mono">
                            Actual hash: {shortHash(bcVerify.file_hash)}
                          </p>
                          {bcVerify.blockchain_hash && (
                            <p className="break-all font-mono">
                              Blockchain hash: {shortHash(bcVerify.blockchain_hash)}
                            </p>
                          )}
                        </div>
                      )}
                    {bcVerify.blockchain_hash && bcVerify.status === "VERIFIED" && (
                      <p className="mt-1 break-all font-mono">
                        On-chain: {shortHash(bcVerify.blockchain_hash)}
                      </p>
                    )}
                    {bcVerify.transaction_hash && (
                      <p className="break-all font-mono">
                        Tx: {shortHash(bcVerify.transaction_hash)}
                      </p>
                    )}
                    {bcVerify.verified_at && (
                      <p>Verified: {formatDateTime(bcVerify.verified_at)}</p>
                    )}
                  </div>
                )}
              </div>

              {/* DEMO TAMPERING TEST — clearly labeled demo control, never a
                  production editing feature. The real verification endpoints
                  remain the only source of truth. */}
              <div className="rounded-lg border-2 border-dashed border-amber-300 bg-amber-50/60 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-amber-800">
                    Demo Tampering Test
                  </p>
                  <span className="rounded bg-amber-200 px-1.5 py-0.5 text-[10px] font-bold tracking-wide text-amber-900">
                    DEMO / TEST
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-amber-800">
                  Intentionally modify this document to test whether TATHYA
                  detects unauthorized changes.
                </p>
                <p className="mt-1 text-[10px] text-amber-700">
                  No new version is created; the stored hash and blockchain
                  record stay untouched — only the underlying file bytes change,
                  so the real verification must report the mismatch.
                </p>
                <div className="mt-2.5 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setDemoConfirmOpen(true)}
                    disabled={demoBusy !== null}
                    title="DEMO: modify the stored file so verification detects it"
                  >
                    {demoBusy === "tamper" ? "Modifying…" : "Simulate Tampering"}
                  </Button>
                  {demoTampered && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => selected && handleDemoRestore(selected)}
                      disabled={demoBusy !== null}
                      title="DEMO: restore the exact original bytes"
                    >
                      {demoBusy === "restore" ? "Restoring…" : "Restore Original"}
                    </Button>
                  )}
                </div>
                {demoTampered && (
                  <p className="mt-2 text-[11px] font-medium text-rose-700">
                    ⚠ File is currently modified — run “Verify integrity” or
                    “Verify blockchain” above to see the real INTEGRITY FAILURE.
                  </p>
                )}
              </div>

              {/* Version history — makes explicit that originals are never
                  overwritten: each version is stored separately. */}
              <div>
                <p className="text-xs font-semibold text-slate-700">Version history</p>
                <p className="mt-0.5 text-[10px] italic text-slate-500">
                  Original version preserved. New versions are stored separately.
                </p>
                {history === null ? (
                  <div className="mt-2 space-y-2">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                ) : history.length === 0 ? (
                  <p className="mt-1.5 text-[11px] text-slate-500">
                    No versions recorded yet.
                  </p>
                ) : (
                  (() => {
                    const originalVersion = Math.min(
                      ...history.map((v) => v.version_number)
                    );
                    const currentVersion = Math.max(
                      ...history.map((v) => v.version_number)
                    );
                    return (
                      <ul className="mt-2 space-y-1.5">
                        {history.map((v) => {
                          const isOriginal = v.version_number === originalVersion;
                          const isCurrent = v.version_number === currentVersion;
                          return (
                            <li
                              key={v.id}
                              className={`rounded-lg border px-3 py-2 text-xs ${
                                isCurrent
                                  ? "border-blue-200 bg-blue-50/50"
                                  : "border-slate-200 bg-white"
                              }`}
                            >
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <span className="flex flex-wrap items-center gap-1.5">
                                  <span className="font-semibold text-slate-900">
                                    v{v.version_number}
                                  </span>
                                  {isCurrent && (
                                    <span className="badge bg-blue-100 text-[10px] text-blue-700">
                                      CURRENT
                                    </span>
                                  )}
                                  {isOriginal && (
                                    <span className="badge badge-muted text-[10px]">
                                      ORIGINAL
                                    </span>
                                  )}
                                </span>
                                <button
                                  onClick={() =>
                                    apiDownload(
                                      `/api/versions/${v.id}/download`,
                                      v.file_name
                                    )
                                  }
                                  className="text-xs font-medium text-blue-600 hover:underline"
                                >
                                  Download
                                </button>
                              </div>
                              <p className="mt-0.5 text-[11px] text-slate-500">
                                uploaded by{" "}
                                {v.uploader
                                  ? (v.uploader.full_name ?? v.uploader.username)
                                  : "—"}{" "}
                                · {formatDateTime(v.created_at)}
                              </p>
                              {v.change_note && (
                                <p className="truncate text-[11px] text-slate-500">
                                  {v.change_note}
                                </p>
                              )}
                              <p
                                title={v.hash}
                                className="mt-0.5 break-all font-mono text-[10px] text-slate-400"
                              >
                                SHA-256: {shortHash(v.hash)}
                              </p>
                            </li>
                          );
                        })}
                      </ul>
                    );
                  })()
                )}
              </div>

              {/* Upload new version */}
              <form
                onSubmit={handleNewVersion}
                className="space-y-2 border-t border-slate-100 pt-4"
              >
                <p className="text-xs font-semibold text-slate-700">
                  Upload new version
                </p>
                <input
                  ref={versionInputRef}
                  type="file"
                  required
                  className="input file:mr-3 file:rounded-md file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-blue-700"
                />
                <input
                  value={changeNote}
                  onChange={(e) => setChangeNote(e.target.value)}
                  placeholder="Change note (optional)"
                  className="input"
                />
                <button
                  type="submit"
                  disabled={versionBusy}
                  className="btn btn-primary btn-sm w-full"
                >
                  {versionBusy ? "Uploading…" : "Upload new version"}
                </button>
              </form>
            </div>
          ) : (
            <div className="card flex h-full flex-col items-center justify-center p-8 text-center">
              <IconFileText className="h-8 w-8 text-slate-300" />
              <p className="mt-3 text-sm font-medium text-slate-700">
                Select a document
              </p>
              <p className="mt-1 text-xs text-slate-500">
                View metadata, SHA-256 hash, integrity verification, version
                history and blockchain anchoring status.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* DEMO tampering confirmation modal — required before any modification */}
      <Modal
        open={demoConfirmOpen}
        onClose={() => (demoBusy ? undefined : setDemoConfirmOpen(false))}
        title="Simulate Document Tampering?"
        description="DEMO / TEST control — this is not a production editing feature."
        footer={
          <>
            <button
              onClick={() => setDemoConfirmOpen(false)}
              disabled={demoBusy !== null}
              className="btn btn-secondary btn-md"
            >
              Cancel
            </button>
            <button
              onClick={() => selected && handleDemoTamper(selected)}
              disabled={demoBusy !== null}
              className="btn btn-destructive btn-md"
            >
              {demoBusy === "tamper" ? "Modifying…" : "Simulate Tampering"}
            </button>
          </>
        }
      >
        <p>
          This will intentionally modify the stored document without creating a
          new version. The next integrity/blockchain verification should detect
          the change.
        </p>
        <p className="mt-2 text-xs text-slate-500">
          The database hash and blockchain record are not touched, and
          “Restore Original” can bring back the exact original bytes.
        </p>
      </Modal>

      {/* Delete confirmation modal */}
      <Modal
        open={deleteTarget !== null}
        onClose={() => (deleteBusy ? undefined : setDeleteTarget(null))}
        title="Delete document?"
        description="This action cannot be undone from the interface."
        footer={
          <>
            <button
              onClick={() => setDeleteTarget(null)}
              disabled={deleteBusy}
              className="btn btn-secondary btn-md"
            >
              Cancel
            </button>
            <button
              onClick={() => deleteTarget && performDelete(deleteTarget)}
              disabled={deleteBusy}
              className="btn btn-destructive btn-md"
            >
              {deleteBusy ? "Deleting…" : "Delete permanently"}
            </button>
          </>
        }
      >
        {deleteTarget && (
          <p>
            <span className="font-medium text-slate-900">{deleteTarget.file_name}</span>{" "}
            will be removed from case records. All actions are recorded in the
            audit trail.
          </p>
        )}
      </Modal>
    </section>
  );
}
