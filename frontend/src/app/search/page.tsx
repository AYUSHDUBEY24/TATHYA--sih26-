"use client";

import Link from "next/link";
import { useState } from "react";
import { apiFetch } from "@/lib/auth";
import type { SearchHit, SearchResponse } from "@/lib/api-types";

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
    <main className="mx-auto min-h-screen max-w-5xl p-8">
      <div className="mb-6">
        <p className="text-xs font-medium uppercase tracking-widest text-sky-400">
          SIH26190 · Search
        </p>
        <h1 className="text-2xl font-bold">Document search</h1>
        <p className="mt-1 text-sm text-slate-400">
          Searches document names, metadata and extracted document text — only
          within cases you are authorized to access.
        </p>
      </div>

      <form onSubmit={runSearch} className="mb-6 flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. forensic, FIR, fingerprint, CASE-2026-001"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm outline-none focus:border-sky-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-sky-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-sky-500 disabled:opacity-50"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {error && (
        <p className="mb-4 rounded-lg border border-rose-800 bg-rose-950/60 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      )}

      {loading && (
        <p className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-400">
          Searching authorized documents…
        </p>
      )}

      {!loading && searched && results && results.results.length === 0 && (
        <p className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-400">
          No documents matching “{results.query}” were found in your authorized
          cases.
        </p>
      )}

      {!loading && results && results.results.length > 0 && (
        <>
          <p className="mb-3 text-sm text-slate-400">
            {results.total} result{results.total === 1 ? "" : "s"} for “
            {results.query}”
          </p>
          <ul className="space-y-3">
            {results.results.map((hit) => (
              <li
                key={hit.document_id}
                className="rounded-xl border border-slate-800 bg-slate-900 p-5"
              >
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <Link
                    href={`/cases/${hit.case_id}`}
                    className="font-semibold text-sky-300 hover:underline"
                  >
                    {hit.file_name}
                  </Link>
                  <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
                    {hit.document_type}
                  </span>
                  <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
                    {hit.classification}
                  </span>
                  {hit.current_version_number !== null && (
                    <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
                      v{hit.current_version_number}
                    </span>
                  )}
                  {hit.matched_text && (
                    <span className="rounded-md bg-emerald-900/70 px-2 py-0.5 text-xs text-emerald-300">
                      text match
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-400">
                  Case{" "}
                  <Link
                    href={`/cases/${hit.case_id}`}
                    className="text-slate-300 hover:underline"
                  >
                    {hit.case_number}
                  </Link>{" "}
                  · {hit.case_title}
                  {hit.uploader_username && (
                    <> · uploaded by {hit.uploader_username}</>
                  )}
                </p>
                {hit.snippet && (
                  <p className="mt-2 border-l-2 border-slate-700 pl-3 text-sm italic text-slate-400">
                    …{hit.snippet}…
                  </p>
                )}
              </li>
            ))}
          </ul>
        </>
      )}

      {!searched && !loading && (
        <p className="rounded-xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-400">
          Enter a query above to search authorized case documents.
        </p>
      )}
    </main>
  );
}
