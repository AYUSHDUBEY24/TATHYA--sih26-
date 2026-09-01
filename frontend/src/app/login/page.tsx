"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { API_BASE_URL, AuthUser, saveAuth } from "@/lib/auth";

const ROLES = [
  "ADMIN",
  "INVESTIGATING_OFFICER",
  "SUPERVISOR",
  "FORENSIC_OFFICER",
  "PROSECUTOR",
] as const;

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<string>("INVESTIGATING_OFFICER");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function loginRequest(emailValue: string, passwordValue: string) {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: emailValue, password: passwordValue }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(typeof data.detail === "string" ? data.detail : "Login failed");
    }
    return data as { access_token: string; user: AuthUser };
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") {
        const result = await loginRequest(email, password);
        saveAuth(result.access_token, result.user);
        router.push("/");
        return;
      }

      // Register, then auto-login with the new credentials.
      const registerRes = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          username,
          password,
          full_name: fullName || null,
          role,
        }),
      });
      const registerData = await registerRes.json().catch(() => ({}));
      if (!registerRes.ok) {
        throw new Error(
          typeof registerData.detail === "string"
            ? registerData.detail
            : "Registration failed"
        );
      }

      const result = await loginRequest(email, password);
      saveAuth(result.access_token, result.user);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-xl">
        <p className="mb-1 text-xs font-medium uppercase tracking-widest text-sky-400">
          SIH26190 · Secure Document Management System
        </p>
        <h1 className="mb-6 text-2xl font-bold">
          {mode === "login" ? "Sign in" : "Create an account"}
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-slate-400" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-sky-500"
              placeholder="officer@example.gov.in"
            />
          </div>

          {mode === "register" && (
            <>
              <div>
                <label className="mb-1 block text-sm text-slate-400" htmlFor="username">
                  Username
                </label>
                <input
                  id="username"
                  required
                  minLength={3}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-sky-500"
                  placeholder="jane.officer"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-400" htmlFor="fullName">
                  Full name (optional)
                </label>
                <input
                  id="fullName"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-sky-500"
                  placeholder="Jane Officer"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-400" htmlFor="role">
                  Role (prototype demo)
                </label>
                <select
                  id="role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-sky-500"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}

          <div>
            <label className="mb-1 block text-sm text-slate-400" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={mode === "register" ? 8 : 1}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-sky-500"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="rounded-lg border border-rose-800 bg-rose-950/60 px-3 py-2 text-sm text-rose-300">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-500 disabled:opacity-50"
          >
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Register"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-400">
          {mode === "login" ? "No account yet?" : "Already registered?"}{" "}
          <button
            type="button"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError(null);
            }}
            className="text-sky-400 underline"
          >
            {mode === "login" ? "Register" : "Sign in"}
          </button>
        </p>
      </div>
    </main>
  );
}
