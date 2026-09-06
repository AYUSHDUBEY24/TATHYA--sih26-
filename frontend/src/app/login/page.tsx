"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { API_BASE_URL, AuthUser, saveAuth } from "@/lib/auth";
import {
  IconLock,
  IconScale,
  IconShield,
  IconUser,
  LogoBlock,
  LogoMark,
} from "@/components/icons";

const ROLES = [
  "ADMIN",
  "INVESTIGATING_OFFICER",
  "SUPERVISOR",
  "FORENSIC_OFFICER",
  "PROSECUTOR",
] as const;

const HIGHLIGHTS = [
  {
    icon: IconLock,
    title: "Role-based access control",
    text: "Every request is authorized server-side against your role and case assignments.",
  },
  {
    icon: IconShield,
    title: "SHA-256 + blockchain integrity",
    text: "Document versions are hash-anchored and tamper-evident.",
  },
  {
    icon: IconScale,
    title: "Complete audit trail",
    text: "Every document action is recorded and reviewable.",
  },
];

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
    <main className="flex min-h-screen">
      {/* Brand / trust panel */}
      <div className="hidden w-[42%] flex-col justify-between bg-gradient-to-b from-[#0f172a] to-[#1e293b] p-10 lg:flex">
        <LogoBlock size="lg" />

        <div>
          <h2 className="text-3xl font-bold leading-tight text-white">
            Secure digital document management for legal and investigation
            workflows.
          </h2>
          <div className="mt-8 space-y-5">
            {HIGHLIGHTS.map(({ icon: Icon, title, text }) => (
              <div key={title} className="flex gap-3">
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10 text-blue-300">
                  <Icon className="h-4 w-4" />
                </span>
                <div>
                  <p className="text-sm font-medium text-white">{title}</p>
                  <p className="mt-0.5 text-xs text-slate-400">{text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="text-[11px] text-slate-500">
          SIH26190 · Smart India Hackathon 2026 prototype — synthetic demo data
          only.
        </p>
      </div>

      {/* Auth form */}
      <div className="flex flex-1 items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-card">
          <div className="mb-4 lg:hidden">
            <LogoMark className="h-10 w-10" />
          </div>
          <p className="text-xs font-semibold uppercase tracking-widest text-blue-600">
            TATHYA · Secure Document Management
          </p>
          <h1 className="mb-6 mt-1 text-2xl font-bold text-slate-900">
            {mode === "login" ? "Sign in to your account" : "Create an account"}
          </h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="officer@example.gov.in"
              />
            </div>

            {mode === "register" && (
              <>
                <div>
                  <label className="label" htmlFor="username">
                    <span className="inline-flex items-center gap-1">
                      <IconUser className="h-3.5 w-3.5 text-slate-400" />
                      Username
                    </span>
                  </label>
                  <input
                    id="username"
                    required
                    minLength={3}
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="input"
                    placeholder="jane.officer"
                  />
                </div>
                <div>
                  <label className="label" htmlFor="fullName">
                    Full name (optional)
                  </label>
                  <input
                    id="fullName"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="input"
                    placeholder="Jane Officer"
                  />
                </div>
                <div>
                  <label className="label" htmlFor="role">
                    Role (prototype demo)
                  </label>
                  <select
                    id="role"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="input"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r.replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}

            <div>
              <label className="label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                minLength={mode === "register" ? 8 : 1}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p
                role="alert"
                className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="btn btn-primary btn-md w-full"
            >
              {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Register"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-600">
            {mode === "login" ? "No account yet?" : "Already registered?"}{" "}
            <button
              type="button"
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setError(null);
              }}
              className="font-medium text-blue-600 underline-offset-2 hover:underline"
            >
              {mode === "login" ? "Register" : "Sign in"}
            </button>
          </p>
          <p className="mt-4 text-center text-[11px] text-slate-400">
            Prototype demo environment — accounts are provisioned by the backend
            seed script.
          </p>
        </div>
      </div>
    </main>
  );
}
