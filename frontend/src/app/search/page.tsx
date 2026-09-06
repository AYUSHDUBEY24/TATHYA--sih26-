"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { apiFetch } from "@/lib/auth";
import type { SearchHit, SearchResponse } from "@/lib/api-types";
import { EmptyState, PageHeader, Skeleton } from "@/components/ui";
import { IconSearch } from "@/components/icons";
import { formatDate } from "@/lib/format";

/** Escape user input before building the snippet-highlight regex. */
function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function HighlightedSnippet({ snippet, query }: { snippet: string; query: string }) {
  const parts = useMemo(() => {
    const q = query.trim();
    if (!q) return [{ text: snippet, match: false }];
    try {
      return snippet
        .split(new RegExp(`(${escapeRegExp(q)})`, "ig"))
        .filter((p) => p !== "")
        .map((p) => ({ text: p, match: p.toLowerCase() === q.toLowerCase() }));
    } catch {
      return [{ text: snippet, match: false }];
    }
  }, [snippet, query]);

  return (
    <p className="mt-2 border-l-2 border-blue-200 pl-3 text-sm text-slate-600">
      …
      {parts.map((part, i) =>
        part.match ? (
          <mark key={i} className="rounded bg-amber-100 px-0.5 text-slate-900">
            {part.text}
          </mark>
        ) : (
          <span key={i}>{part.text}</span>
        )
      )}
      …
    </p>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  async function runSearch(e?: React.FormEvent) {
    e?.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setError("Enter a search term.");
      return;
    }
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const data = await apiFetch<SearchResponse>(
        `/api/search?q=${encodeURIComponent(trimmed)}&limit=20`
      );
      setResults(data);
    } catch (err) {
      setResults(null);
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        eyebrow="Investigation"
        title="Document search"
        description="Searches document names, metadata and extracted document text — only within cases you are authorized to access."
      />

      {/* Search bar */}
      <form onSubmit={runSearch} className="card mb-6 flex gap-3 p-4">
        <div className="relative flex-1">
          <IconSearch className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. forensic, FIR, fingerprint, CASE-2026-001"
            className="input pl-9"
            aria-label="Search documents"
          />
        </div>
        <button type="submit" disabled={loading} className="btn btn-primary btn-md">
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          {error}
        </div>
      )}

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      )}

      {!loading && searched && results && results.results.length === 0 && (
        <EmptyState
          title="No documents found"
          description={`No documents matching “${results.query}” were found in your authorized cases.`}
        />
      )}

      {!loading && results && results.results.length > 0 && (
        <>
          <p className="mb-3 text-sm text-slate-600">
            <span className="font-semibold text-slate-900">{results.total}</span>{" "}
            result{results.total === 1 ? "" : "s"} for &ldquo;{results.query}&rdquo;
          </p>
          <ul className="space-y-3">
            {results.results.map((hit) => (
              <ResultCard key={hit.document_id} hit={hit} query={results.query} />
            ))}
          </ul>
        </>
      )}

      {!searched && !loading && !error && (
        <EmptyState
          title="Search authorized case documents"
          description="Enter a query above to search document names, metadata and extracted text. Results are always limited to what your role permits."
        />
      )}
    </div>
  );
}

function ResultCard({ hit, query }: { hit: SearchHit; query: string }) {
  return (
    <li className="card p-5 transition hover:border-blue-300 hover:shadow-card-hover">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Link
          href={`/cases/${hit.case_id}`}
          className="text-sm font-semibold text-slate-900 hover:text-blue-600"
        >
          {hit.file_name}
        </Link>
        <span className="badge badge-info">{hit.document_type.replace(/_/g, " ")}</span>
        <span className="badge badge-muted">{hit.classification}</span>
        {hit.current_version_number !== null && (
          <span className="badge badge-muted">v{hit.current_version_number}</span>
        )}
        {hit.matched_text && <span className="badge badge-success">text match</span>}
      </div>
      <p className="text-sm text-slate-600">
        Case{" "}
        <Link
          href={`/cases/${hit.case_id}`}
          className="font-mono text-xs font-medium text-blue-600 hover:underline"
        >
          {hit.case_number}
        </Link>{" "}
        · {hit.case_title}
        {hit.uploader_username && <> · uploaded by {hit.uploader_username}</>}
        {hit.created_at && <> · {formatDate(hit.created_at)}</>}
      </p>
      {hit.snippet && <HighlightedSnippet snippet={hit.snippet} query={query} />}
    </li>
  );
}
