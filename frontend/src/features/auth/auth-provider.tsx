"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { apiFetch, setAccessToken } from "@/shared/api/http-client";

type AuthUser = {
  id: string;
  email: string;
  display_name: string;
  role: "USER" | "TEACHER";
  timezone: string;
  preferred_locale: string;
};

type AuthResponse = {
  access_token: string;
  user: AuthUser;
};

type AuthContextValue = {
  user: AuthUser | null;
  isRestoring: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  useEffect(() => {
    void apiFetch<AuthResponse>("/api/v1/auth/refresh", { method: "POST" }, false)
      .then((session) => {
        setAccessToken(session.access_token);
        setUser(session.user);
      })
      .catch(() => setAccessToken(null))
      .finally(() => setIsRestoring(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const session = await apiFetch<AuthResponse>("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    setAccessToken(session.access_token);
    setUser(session.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiFetch<void>("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // Clearing the local session is still the correct outcome if revocation is unavailable.
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, isRestoring, login, logout }),
    [isRestoring, login, logout, user],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
