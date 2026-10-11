"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useSyncExternalStore } from "react";
import { api, configureAuth } from "@/api/client";
import { clearSession, createSession, isExpired, loadSession, saveSession, type Session } from "@/lib/session";

// Session store read through useSyncExternalStore so the server render and the
// first client render agree ("loading") before localStorage is consulted.

interface AuthSnapshot {
  session: Session | null;
  notice: string | null;
}

let snapshot: AuthSnapshot | null = null;
const listeners = new Set<() => void>();

function readSnapshot(): AuthSnapshot {
  if (snapshot === null) snapshot = { session: loadSession(), notice: null };
  return snapshot;
}

function setSnapshot(next: AuthSnapshot): void {
  snapshot = next;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function endSession(notice: string | null): void {
  clearSession();
  setSnapshot({ session: null, notice });
}

configureAuth(
  () => readSnapshot().session?.token ?? null,
  () => {
    if (readSnapshot().session) endSession("Your session has expired. Sign in again to continue.");
  },
);

type AuthStatus = "loading" | "authenticated" | "anonymous";

interface AuthContextValue {
  status: AuthStatus;
  session: Session | null;
  notice: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const current = useSyncExternalStore(subscribe, readSnapshot, () => null);

  const login = useCallback(async (email: string, password: string) => {
    const normalized = email.trim().toLowerCase();
    const { access_token } = await api.auth.login(normalized, password);
    const session = createSession(access_token, normalized);
    saveSession(session);
    setSnapshot({ session, notice: null });
  }, []);

  const register = useCallback(
    async (email: string, password: string) => {
      await api.auth.register(email.trim().toLowerCase(), password);
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(() => endSession(null), []);

  // Sign out when the token's exp claim passes rather than waiting for a 401.
  const expiresAt = current?.session?.expiresAt ?? null;
  useEffect(() => {
    if (expiresAt === null) return;
    const timer = window.setTimeout(
      () => {
        const session = readSnapshot().session;
        if (session && isExpired(session)) endSession("Your session has expired. Sign in again to continue.");
      },
      Math.max(expiresAt - Date.now(), 0) + 1000,
    );
    return () => window.clearTimeout(timer);
  }, [expiresAt]);

  const value = useMemo<AuthContextValue>(
    () => ({
      status: current === null ? "loading" : current.session ? "authenticated" : "anonymous",
      session: current?.session ?? null,
      notice: current?.notice ?? null,
      login,
      register,
      logout,
    }),
    [current, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
