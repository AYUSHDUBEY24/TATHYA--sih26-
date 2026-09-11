"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AUTH_CHANGED_EVENT,
  getToken,
  getStoredUser,
  clearAuth,
  saveAuth,
  apiFetch,
  AuthUser,
} from "./auth";

/**
 * Global auth state hook.
 *
 * Subscribes to the auth-changed event (login/logout/401 from ANY component)
 * so the header/AppShell never goes stale after client-side navigation, and
 * re-validates the stored user against /api/auth/me when a token exists.
 * All real authorization remains backend-enforced.
 */
export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    // Read the persisted session immediately (page refresh keeps login).
    setUser(getStoredUser());
    setLoading(false);

    // Re-read on login/logout/401 from any component or tab.
    function sync() {
      setUser(getStoredUser());
    }
    window.addEventListener(AUTH_CHANGED_EVENT, sync);
    window.addEventListener("storage", sync);

    // If a token exists, refresh the user from /api/auth/me so the header
    // reflects the CURRENT backend state (role/name changes, revoked users).
    // Never blocks the UI: the stored user is already rendered.
    if (getToken()) {
      apiFetch<AuthUser>("/api/auth/me")
        .then((me) => {
          if (!cancelled) {
            saveAuth(getToken() as string, me);
            setUser(me);
          }
        })
        .catch(() => {
          /* 401 already cleared auth + notified; other errors keep stored user */
        });
    }

    return () => {
      cancelled = true;
      window.removeEventListener(AUTH_CHANGED_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const login = useCallback((token: string, authUser: AuthUser) => {
    saveAuth(token, authUser);
    setUser(authUser);
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
    window.location.href = "/login";
  }, []);

  return { user, loading, login, logout };
}
