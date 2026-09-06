"use client";

import { DocumentItem } from "@/lib/api-types";
import { formatBytes, formatDate, prettifyEnum } from "@/lib/format";
import { IconDownload, IconFileText, IconTrash } from "./icons";

interface RowActions {
  onSelect: () => void;
  onDownload: () => void;
  onDelete?: () => void;
}

/**
 * One document row for the desktop case document table. Presentational only —
 * all actions (select / download / delete) are passed in by the parent,
 * which owns the real API handlers.
 */
export function DocumentRow({
  doc,
  selected,
  onSelect,
  onDownload,
  onDelete,
}: {
  doc: DocumentItem;
  selected: boolean;
  onSelect: () => void;
  onDownload: () => void;
  onDelete?: () => void;
}) {
  return (
    <tr
      className={`border-b border-slate-100 transition hover:bg-slate-50 ${
        selected ? "bg-blue-50/60" : ""
      }`}
    >
      <td className="px-4 py-3">
        <button
          onClick={onSelect}
          className="flex items-center gap-3 text-left"
          title="View details, versions and integrity"
        >
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            <IconFileText className="h-4 w-4" />
          </span>
          <span className="min-w-0">
            {/* Intelligent truncation: full filename via title tooltip */}
            <span
              title={doc.file_name}
              className="block max-w-[16rem] truncate text-sm font-medium text-slate-900"
            >
              {doc.file_name}
            </span>
            <span className="block text-xs text-slate-500">
              {formatBytes(doc.size_bytes)}
              {doc.current_version_number
                ? ` · v${doc.current_version_number}`
                : ""}
            </span>
          </span>
        </button>
      </td>
      <td className="px-4 py-3 text-sm text-slate-600">
        {prettifyEnum(doc.document_type)}
      </td>
      <td className="px-4 py-3">
        <span className="badge badge-muted">{doc.classification}</span>
      </td>
      <td className="px-4 py-3 text-sm text-slate-600">
        {doc.uploader
          ? (doc.uploader.full_name ?? doc.uploader.username)
          : "—"}
      </td>
      <td className="px-4 py-3 text-sm text-slate-500">
        {formatDate(doc.created_at)}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <button
            onClick={onDownload}
            title="Download (proxied through the backend)"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition hover:bg-blue-50 hover:text-blue-600"
            aria-label={`Download ${doc.file_name}`}
          >
            <IconDownload className="h-4 w-4" />
          </button>
          {doc.can_delete && onDelete && (
            <button
              onClick={onDelete}
              title="Delete document"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition hover:bg-rose-50 hover:text-rose-600"
              aria-label={`Delete ${doc.file_name}`}
            >
              <IconTrash className="h-4 w-4" />
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}

/**
 * Responsive card variant of the document row for small screens, where the
 * full table would force horizontal scrolling.
 */
export function DocumentCard({
  doc,
  selected,
  onSelect,
  onDownload,
  onDelete,
}: {
  doc: DocumentItem;
  selected: boolean;
  onSelect: () => void;
  onDownload: () => void;
  onDelete?: () => void;
}) {
  return (
    <div
      className={`flex items-center gap-3 p-4 transition ${
        selected ? "bg-blue-50/60" : "bg-white hover:bg-slate-50"
      }`}
    >
      <button
        onClick={onSelect}
        className="flex min-w-0 flex-1 items-center gap-3 text-left"
        title="View details, versions and integrity"
      >
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          <IconFileText className="h-5 w-5" />
        </span>
        <span className="min-w-0">
          <span
            title={doc.file_name}
            className="block truncate text-sm font-medium text-slate-900"
          >
            {doc.file_name}
          </span>
          <span className="mt-0.5 flex flex-wrap gap-x-2 text-[11px] text-slate-500">
            <span>{prettifyEnum(doc.document_type)}</span>
            <span aria-hidden="true">·</span>
            <span>{doc.classification}</span>
            <span aria-hidden="true">·</span>
            <span>{formatBytes(doc.size_bytes)}</span>
            {doc.current_version_number && (
              <>
                <span aria-hidden="true">·</span>
                <span>v{doc.current_version_number}</span>
              </>
            )}
          </span>
          <span className="mt-0.5 block text-[11px] text-slate-400">
            {doc.uploader
              ? (doc.uploader.full_name ?? doc.uploader.username)
              : "—"}{" "}
            · {formatDate(doc.created_at)}
          </span>
        </span>
      </button>
      <div className="flex shrink-0 items-center gap-1">
        <button
          onClick={onDownload}
          title="Download"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 transition hover:bg-blue-50 hover:text-blue-600"
          aria-label={`Download ${doc.file_name}`}
        >
          <IconDownload className="h-4 w-4" />
        </button>
        {doc.can_delete && onDelete && (
          <button
            onClick={onDelete}
            title="Delete document"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 transition hover:bg-rose-50 hover:text-rose-600"
            aria-label={`Delete ${doc.file_name}`}
          >
            <IconTrash className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
