"use client";

import { IconCheckCircle, IconXCircle, IconShield } from "./icons";
import { formatDateTime } from "@/lib/format";

/**
 * Integrity badge for a SHA-256 verification result.
 * VERIFIED → emerald · INTEGRITY_FAILURE → rose · unknown → muted.
 */
export function IntegrityBadge({
  status,
  verifiedAt,
}: {
  status?: string | null;
  verifiedAt?: string | null;
}) {
  if (!status) {
    return (
      <span className="badge badge-muted">
        <IconShield className="h-3 w-3" />
        Not verified yet
      </span>
    );
  }
  if (status === "VERIFIED") {
    return (
      <span className="badge badge-success">
        <IconCheckCircle className="h-3 w-3" />
        Integrity Verified
      </span>
    );
  }
  if (status === "INTEGRITY_FAILURE") {
    return (
      <span className="badge badge-destructive">
        <IconXCircle className="h-3 w-3" />
        Integrity Failure — possible tampering
      </span>
    );
  }
  return <span className="badge badge-warning">{status}</span>;
}

/** Blockchain anchor status badge (CONFIRMED / PENDING / FAILED / …). */
export function BlockchainStatusBadge({ status }: { status?: string | null }) {
  if (!status) {
    return <span className="badge badge-muted">Not anchored</span>;
  }
  if (status === "CONFIRMED") {
    return (
      <span className="badge badge-success">
        <IconCheckCircle className="h-3 w-3" />
        Blockchain Confirmed
      </span>
    );
  }
  if (status === "PENDING") {
    return (
      <span className="badge badge-warning">
        Anchor Pending
      </span>
    );
  }
  if (status === "FAILED") {
    return (
      <span className="badge badge-destructive">
        <IconXCircle className="h-3 w-3" />
        Anchor Failed
      </span>
    );
  }
  return <span className="badge badge-muted">{status}</span>;
}

/** Small inline hint showing when the verification last ran. */
export function VerifiedAt({ at }: { at?: string | null }) {
  if (!at) return null;
  return (
    <span className="text-xs text-slate-500">Last verified {formatDateTime(at)}</span>
  );
}
