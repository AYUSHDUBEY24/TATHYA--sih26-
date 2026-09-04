"use client";

import React, { useState } from "react";
import { apiFetch, ApiError } from "@/lib/auth";
import { AIQueryResponse, AICitation } from "@/lib/api-types";
import { Button } from "@/components/ui";

const AI_QUERY_URL = "/api/ai/query";

export default function AIAssistantPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AIQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await apiFetch<AIQueryResponse>(AI_QUERY_URL, {
        method: "POST",
        body: JSON.stringify({ question: question.trim() }),
      });
      setResult(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">AI Document Assistant</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Ask questions about your authorized case documents. Answers are generated
          only from documents you have permission to access.
        </p>
      </div>

      <div className="mb-6 rounded-lg border border-border bg-card/50 p-4">
        <div className="flex gap-3">
          <div className="mt-0.5 text-primary">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </div>
          <div className="text-sm text-muted-foreground">
            <p className="font-medium text-foreground">Security Notice</p>
            <p className="mt-1">
              All retrieval is permission-aware. The AI can only access documents
              you are authorized to view. Answers include source citations for verification.
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What evidence was collected from the scene?"
            className="input flex-1"
            maxLength={2000}
          />
          <Button type="submit" disabled={loading || !question.trim()}>
            {loading ? "Asking..." : "Ask AI"}
          </Button>
        </div>
      </form>

      {loading && (
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <span className="text-sm text-muted-foreground">
              Searching authorized documents...
            </span>
          </div>
        </div>
      )}

      {error && !loading && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {result && !loading && (
        <div className="space-y-6">
          {result.status === "insufficient_context" && (
            <div className="rounded-lg border border-border bg-card p-6">
              <div className="flex gap-3">
                <div className="mt-0.5 text-muted-foreground">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="16" x2="12" y2="12"/>
                    <line x1="12" y1="8" x2="12.01" y2="8"/>
                  </svg>
                </div>
                <div>
                  <p className="font-medium text-foreground">No relevant information found</p>
                  <p className="mt-1 text-sm text-muted-foreground">{result.answer}</p>
                </div>
              </div>
            </div>
          )}

          {result.status === "provider_unavailable" && (
            <div className="rounded-lg border border-warning/50 bg-warning/10 p-4">
              <p className="text-sm text-foreground">
                <span className="font-medium">AI provider unavailable.</span>{" "}
                {result.answer}
              </p>
            </div>
          )}

          {result.status === "answered" && (
            <>
              <div className="rounded-lg border border-border bg-card p-6">
                <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  Answer
                </h2>
                <p className="whitespace-pre-wrap text-foreground">{result.answer}</p>
              </div>

              {result.sources.length > 0 && (
                <div className="rounded-lg border border-border bg-card p-6">
                  <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                    Sources ({result.sources.length})
                  </h2>
                  <div className="space-y-3">
                    {result.sources.map((source, idx) => (
                      <CitationCard key={source.chunk_id || idx} citation={source} index={idx + 1} />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {!result && !loading && !error && (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <h3 className="text-lg font-medium text-foreground">Ask about your documents</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Get answers from your authorized case documents with source citations.
          </p>
        </div>
      )}
    </div>
  );
}

function CitationCard({ citation, index }: { citation: AICitation; index: number }) {
  return (
    <div className="rounded-lg border border-border bg-background/50 p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
              {index}
            </span>
            <span className="font-medium text-foreground">
              {citation.file_name || "Unknown document"}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {citation.version && (
              <span className="rounded-md bg-secondary px-2 py-0.5 text-xs font-medium">
                Version {citation.version}
              </span>
            )}
            {citation.page_start && (
              <span className="rounded-md bg-secondary px-2 py-0.5 text-xs font-medium">
                Page {citation.page_start}
                {citation.page_end && citation.page_end !== citation.page_start
                  ? `-${citation.page_end}`
                  : ""}
              </span>
            )}
            {citation.score && (
              <span className="rounded-md bg-success/20 px-2 py-0.5 text-xs font-medium text-success">
                {Math.round(citation.score * 100)}% match
              </span>
            )}
          </div>
          {citation.excerpt && (
            <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
              &ldquo;{citation.excerpt}&rdquo;
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
