"use client";

import { useState, useEffect, useCallback } from "react";
import {
  getToken,
  getStoredUser,
  clearAuth,
  saveAuth,
  AuthUser,
} from "./auth";

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = getStoredUser();
    setUser(storedUser);
    setLoading(false);
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
