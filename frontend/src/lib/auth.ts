/**
 * Client-side auth helpers (Phase 2 prototype).
 *
 * The JWT is stored in localStorage for simplicity. All real authorization is
 * enforced by the backend — the frontend only reflects state.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  role: { name: string };
}

const TOKEN_KEY = "sih26190_token";
const USER_KEY = "sih26190_user";

/**
 * Fired on window whenever the auth state changes (login/logout/401). This is
 * the root-cause fix for the stale header: useAuth instances mounted elsewhere
 * (e.g. AppShell) subscribe to this instead of reading localStorage only once
 * at mount — client-side navigation after login never remounts them.
 */
export const AUTH_CHANGED_EVENT = "tathya:auth-changed";

function notifyAuthChanged(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
  }
}

export function saveAuth(token: string, user: AuthUser): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  notifyAuthChanged();
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  notifyAuthChanged();
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/**
 * Fetch helper that attaches the JWT and handles 401 (session expired).
 * All real authorization is enforced by the backend; this only improves UX.
 */
export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) ?? {}),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearAuth();
    throw new ApiError(401, "Session expired. Please sign in again.");
  }
  const data = (await res.json().catch(() => null)) as
    | (T & { detail?: unknown })
    | null;
  if (!res.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail;
    const message =
      typeof detail === "string" ? detail : `Request failed (${res.status})`;
    throw new ApiError(res.status, message);
  }
  return data as T;
}

/** Upload helper (multipart — must NOT set Content-Type manually). */
export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (res.status === 401) {
    clearAuth();
    throw new ApiError(401, "Session expired. Please sign in again.");
  }
  const data = (await res.json().catch(() => null)) as
    | (T & { detail?: unknown })
    | null;
  if (!res.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail;
    const message =
      typeof detail === "string" ? detail : `Upload failed (${res.status})`;
    throw new ApiError(res.status, message);
  }
  return data as T;
}

/** Authenticated download: fetches the bytes and triggers a save dialog. */
export async function apiDownload(path: string, filename: string): Promise<void> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}${path}`, { headers });
  if (!res.ok) throw new Error(`Download failed (${res.status})`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
