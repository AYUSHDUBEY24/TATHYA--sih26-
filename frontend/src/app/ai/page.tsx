"use client";

import React, { useEffect, useRef, useState } from "react";
import { apiFetch, ApiError } from "@/lib/auth";
import { AIQueryResponse, AICitation } from "@/lib/api-types";
import { IconSend, IconShield, IconSparkles } from "@/components/icons";
import { prettifyEnum } from "@/lib/format";

const AI_QUERY_URL = "/api/ai/query";

const SUGGESTED_PROMPTS = [
  "Summarize the current status of my most recent case",
  "What evidence has been collected so far?",
  "List all forensic findings across my authorized cases",
  "What do witness statements say about the incident?",
];

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  /** Present on assistant messages when the backend answered. */
  status?: AIQueryResponse["status"];
  sources?: AICitation[];
  provider?: string;
  /** True when the request itself failed (network/HTTP error). */
  isError?: boolean;
}

/**
 * AI research assistant over authorized case documents.
 * Preserves the exact POST /api/ai/query contract:
 *   request  { question: string }
 *   response { status: answered|insufficient_context|provider_unavailable,
 *              answer, sources[], provider }
 * Conversation history is session-only (no backend conversation API exists).
 */
export default function AIAssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const counter = useRef(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to newest message.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  async function ask(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    const userMsg: ChatMessage = { id: ++counter.current, role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);
    try {
      const response = await apiFetch<AIQueryResponse>(AI_QUERY_URL, {
        method: "POST",
        body: JSON.stringify({ question: trimmed }),
      });
      setMessages((prev) => [
        ...prev,
        {
          id: ++counter.current,
          role: "assistant",
          content: response.answer,
          status: response.status,
          sources: response.sources,
          provider: response.provider,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: ++counter.current,
          role: "assistant",
          content:
            err instanceof ApiError
              ? err.message
              : "An unexpected error occurred. Please try again.",
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    ask(question);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends, Shift+Enter adds a newline.
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask(question);
    }
  }

  return (
    <div className="mx-auto flex h-full max-w-4xl flex-col">
      {/* Header */}
      <div className="mb-4">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900">
          <IconSparkles className="h-6 w-6 text-blue-600" />
          Tathya Intelligence — Ask the Facts
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          A research assistant over your authorized case documents. Conversation
          is session-only; every answer carries source citations.
        </p>
      </div>

      {/* Conversation area */}
      <div
        ref={scrollRef}
        className="slim-scrollbar flex-1 space-y-4 overflow-y-auto rounded-xl border border-slate-200 bg-white p-5"
      >
        {messages.length === 0 && !loading && (
          <div className="flex h-full flex-col items-center justify-center py-10 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
              <IconSparkles className="h-7 w-7" />
            </div>
            <h2 className="mt-4 text-lg font-semibold text-slate-900">
              Research your case documents
            </h2>
            <p className="mt-1 max-w-md text-sm text-slate-600">
              Get grounded answers from the documents you are authorized to
              access — with source citations for every claim.
            </p>
            <div className="mt-6 grid w-full max-w-xl gap-2 sm:grid-cols-2">
              {SUGGESTED_PROMPTS.map((p) => (
                <button
                  key={p}
                  onClick={() => {
                    setQuestion(p);
                    inputRef.current?.focus();
                  }}
                  className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-left text-xs text-slate-700 transition hover:border-blue-300 hover:bg-blue-50 hover:text-slate-900"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="flex justify-end">
              <div className="max-w-[80%] rounded-2xl rounded-br-md bg-blue-600 px-4 py-2.5 text-sm text-white shadow-sm">
                <p className="whitespace-pre-wrap">{m.content}</p>
              </div>
            </div>
          ) : (
            <AssistantMessage key={m.id} message={m} />
          )
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-3 rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <span className="flex gap-1">
                <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:0ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:150ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-blue-500 [animation-delay:300ms]" />
              </span>
              <span className="text-xs text-slate-500">
                Searching authorized documents…
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Security indicator + fixed input area */}
      <div className="mt-4">
        <div className="mb-2 flex items-center gap-2 text-xs text-emerald-700">
          <IconShield className="h-3.5 w-3.5" />
          <span className="font-medium">Permission-aware retrieval</span>
          <span className="text-slate-500">
            — answers come only from documents you are authorized to access.
          </span>
        </div>
        <form
          onSubmit={handleSubmit}
          className="flex items-end gap-2 rounded-xl border border-slate-300 bg-white p-2 shadow-sm focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20"
        >
          <textarea
            ref={inputRef}
            rows={1}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your case documents…"
            className="max-h-32 min-h-[2.5rem] flex-1 resize-none border-0 bg-transparent px-2 py-2 text-sm text-slate-900 placeholder:text-slate-400 outline-none"
            maxLength={2000}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="btn btn-primary h-10 w-10 shrink-0 !px-0"
            aria-label="Send question"
          >
            <IconSend className="h-4 w-4" />
          </button>
        </form>
        <p className="mt-1.5 text-center text-[11px] text-slate-400">
          Enter to send · Shift + Enter for a new line
        </p>
      </div>
    </div>
  );
}

/** Assistant bubble: honest status handling + source citation cards. */
function AssistantMessage({ message }: { message: ChatMessage }) {
  if (message.isError) {
    return (
      <div className="flex justify-start">
        <div
          role="alert"
          className="max-w-[85%] rounded-2xl rounded-bl-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-3">
        {message.status === "insufficient_context" ? (
          <div className="rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Not found in authorized documents
            </p>
            <p className="mt-1.5 whitespace-pre-wrap text-sm text-slate-800">
              {message.content}
            </p>
          </div>
        ) : message.status === "provider_unavailable" ? (
          <div className="rounded-2xl rounded-bl-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">
              AI provider unavailable
            </p>
            <p className="mt-1.5">{message.content}</p>
          </div>
        ) : (
          <div className="rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 shadow-sm">
            <p className="whitespace-pre-wrap text-sm text-slate-800">
              {message.content}
            </p>
          </div>
        )}

        {message.status === "answered" &&
          message.sources &&
          message.sources.length > 0 && (
            <div className="space-y-2 pl-2">
              <p className="text-xs font-semibold text-slate-500">
                Sources ({message.sources.length})
              </p>
              {message.sources.map((source, idx) => (
                <CitationCard
                  key={source.chunk_id || idx}
                  citation={source}
                  index={idx + 1}
                />
              ))}
            </div>
          )}

        {message.status === "answered" && message.provider && (
          <p className="pl-2 text-[11px] text-slate-400">
            Provider: {prettifyEnum(message.provider)}
          </p>
        )}
      </div>
    </div>
  );
}

/** Source citation card: document name, version, page range, excerpt, score. */
function CitationCard({
  citation,
  index,
}: {
  citation: AICitation;
  index: number;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
      <div className="flex items-start gap-2.5">
        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-600 text-[10px] font-bold text-white">
          {index}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-semibold text-slate-900">
            {citation.file_name || "Unknown document"}
          </p>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {citation.version !== null && (
              <span className="rounded bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-600 ring-1 ring-slate-200">
                Version {citation.version}
              </span>
            )}
            {citation.page_start !== null && (
              <span className="rounded bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-600 ring-1 ring-slate-200">
                Page {citation.page_start}
                {citation.page_end !== null && citation.page_end !== citation.page_start
                  ? `–${citation.page_end}`
                  : ""}
              </span>
            )}
            {citation.score !== null && (
              <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700 ring-1 ring-emerald-200">
                {Math.round(citation.score * 100)}% match
              </span>
            )}
          </div>
          {citation.excerpt && (
            <p className="mt-1.5 border-l-2 border-slate-300 pl-2 text-xs italic text-slate-600 line-clamp-3">
              &ldquo;{citation.excerpt}&rdquo;
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
