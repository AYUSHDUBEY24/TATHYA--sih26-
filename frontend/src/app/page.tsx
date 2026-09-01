"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthUser, clearAuth, getStoredUser } from "@/lib/auth";

export default function Home() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    setUser(getStoredUser());
    setChecked(true);
  }, []);

  function handleLogout() {
    clearAuth();
    setUser(null);
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900 p-10 shadow-xl">
        <p className="mb-2 text-sm font-medium uppercase tracking-widest text-sky-400">
          Smart India Hackathon 2026 · SIH26190
        </p>
        <h1 className="mb-4 text-3xl font-bold leading-tight">
          Secure Case, Evidence &amp; Legal Document Management System
        </h1>
        <p className="mb-8 text-slate-400">
          Next.js frontend is running. Phase 2 (Authentication + RBAC) — cases,
          documents and AI features arrive in later phases.
        </p>

        {/* Authentication status */}
        {checked && user && (
          <div className="mb-6 rounded-xl border border-emerald-800 bg-emerald-950/40 p-5">
            <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-emerald-400">
              Signed in
            </p>
            <dl className="space-y-1 text-sm">
              <div className="flex gap-2">
                <dt className="w-24 text-slate-400">Name</dt>
                <dd className="font-medium">{user.full_name ?? user.username}</dd>
              </div>
              <div className="flex gap-2">
                <dt className="w-24 text-slate-400">Email</dt>
                <dd>{user.email}</dd>
              </div>
              <div className="flex gap-2">
                <dt className="w-24 text-slate-400">Role</dt>
                <dd>
                  <span className="rounded-md bg-sky-900/80 px-2 py-0.5 text-xs font-semibold text-sky-300">
                    {user.role.name}
                  </span>
                </dd>
              </div>
            </dl>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                href="/cases"
                className="rounded-lg bg-sky-600 px-4 py-1.5 text-sm font-semibold text-white transition hover:bg-sky-500"
              >
                View cases
              </Link>
              {user.role.name === "ADMIN" && (
                <Link
                  href="/audit"
                  className="rounded-lg border border-slate-600 px-4 py-1.5 text-sm font-medium text-slate-200 transition hover:bg-slate-800"
                >
                  Audit logs
                </Link>
              )}
              <button
                onClick={handleLogout}
                className="rounded-lg border border-rose-800 px-4 py-1.5 text-sm font-medium text-rose-300 transition hover:bg-rose-950"
              >
                Log out
              </button>
            </div>
          </div>
        )}

        {checked && !user && (
          <div className="mb-6 rounded-xl border border-slate-700 bg-slate-950/60 p-5 text-sm">
            <p className="mb-3 text-slate-400">You are not signed in.</p>
            <Link
              href="/login"
              className="inline-block rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-500"
            >
              Go to login
            </Link>
          </div>
        )}

        <ul className="space-y-2 text-sm">
          <li className="flex items-center gap-2">
            <span className="text-emerald-400">●</span>
            Frontend: Next.js (App Router) + TypeScript + Tailwind CSS
          </li>
          <li className="flex items-center gap-2">
            <span className="text-amber-400">○</span>
            Backend API:{" "}
            <a
              className="text-sky-400 underline"
              href="http://localhost:8000/health"
              target="_blank"
              rel="noreferrer"
            >
              http://localhost:8000/health
            </a>
          </li>
        </ul>
      </div>
    </main>
  );
}
