// The backend issues a bearer JWT from POST /api/auth/login and has no
// "current user" endpoint, so the session is the token plus the email the
// user signed in with, kept in localStorage.

const STORAGE_KEY = "rag-assistant.session";

export interface Session {
  token: string;
  email: string;
  role: string | null;
  expiresAt: number | null; // epoch milliseconds, from the token's exp claim
}

interface TokenClaims {
  sub?: string;
  role?: string;
  exp?: number;
}

function decodeClaims(token: string): TokenClaims | null {
  const payload = token.split(".")[1];
  if (!payload) return null;
  try {
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    return JSON.parse(atob(padded)) as TokenClaims;
  } catch {
    return null;
  }
}

export function createSession(token: string, email: string): Session {
  const claims = decodeClaims(token);
  return {
    token,
    email,
    role: typeof claims?.role === "string" ? claims.role : null,
    expiresAt: typeof claims?.exp === "number" ? claims.exp * 1000 : null,
  };
}

export function isExpired(session: Session): boolean {
  return session.expiresAt !== null && session.expiresAt <= Date.now();
}

export function loadSession(): Session | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<Session>;
    if (typeof parsed.token !== "string" || typeof parsed.email !== "string") return null;
    const session = createSession(parsed.token, parsed.email);
    return isExpired(session) ? null : session;
  } catch {
    return null;
  }
}

export function saveSession(session: Session): void {
  try {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ token: session.token, email: session.email }),
    );
  } catch {
    // Storage unavailable (private mode); the session lasts for this tab only.
  }
}

export function clearSession(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore.
  }
}
