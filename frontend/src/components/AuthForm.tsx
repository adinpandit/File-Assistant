"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError } from "@/api/client";
import { useAuth } from "@/hooks/useAuth";
import { Button, ErrorNotice, Spinner } from "@/components/ui";

// Limits from backend/app/models/auth.py (UserCreate).
const PASSWORD_MIN = 8;
const PASSWORD_MAX = 128;

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const { status, notice, login, register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "authenticated") router.replace("/");
  }, [status, router]);

  const isRegister = mode === "register";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (isRegister && password.length < PASSWORD_MIN) {
      setError(`Password must be at least ${PASSWORD_MIN} characters.`);
      return;
    }
    setSubmitting(true);
    try {
      if (isRegister) await register(email, password);
      else await login(email, password);
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 409) {
        setError("An account with this email already exists. Sign in instead.");
      } else {
        setError(cause instanceof ApiError ? cause.message : "Something went wrong. Please try again.");
      }
      setSubmitting(false);
    }
  }

  if (status !== "anonymous") {
    return (
      <main className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </main>
    );
  }

  return (
    <main className="flex min-h-dvh flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-[360px]">
        <p className="text-sm font-semibold tracking-tight">RAG Assistant</p>
        <h1 className="mt-6 text-xl font-semibold tracking-tight">
          {isRegister ? "Create your account" : "Sign in"}
        </h1>
        <p className="mt-1 text-sm text-ink-muted">
          {isRegister
            ? "Upload documents and ask questions answered from their contents."
            : "Continue to your documents and conversations."}
        </p>

        {notice && !isRegister && (
          <p role="status" className="mt-5 rounded-md border border-line bg-subtle px-3 py-2 text-sm text-ink-muted">
            {notice}
          </p>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              maxLength={255}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1.5 block h-10 w-full rounded-md border border-line-strong bg-surface px-3 text-sm outline-none transition-colors placeholder:text-ink-faint focus:border-accent focus:ring-2 focus:ring-accent/15 focus-visible:outline-none"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete={isRegister ? "new-password" : "current-password"}
              required
              minLength={isRegister ? PASSWORD_MIN : undefined}
              maxLength={PASSWORD_MAX}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              aria-describedby={isRegister ? "password-hint" : undefined}
              className="mt-1.5 block h-10 w-full rounded-md border border-line-strong bg-surface px-3 text-sm outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-accent/15 focus-visible:outline-none"
            />
            {isRegister && (
              <p id="password-hint" className="mt-1.5 text-xs text-ink-muted">
                At least {PASSWORD_MIN} characters.
              </p>
            )}
          </div>

          {error && <ErrorNotice message={error} />}

          <Button type="submit" variant="primary" loading={submitting} className="h-10 w-full">
            {isRegister ? "Create account" : "Sign in"}
          </Button>
        </form>

        <p className="mt-6 text-sm text-ink-muted">
          {isRegister ? "Already have an account? " : "New here? "}
          <Link
            href={isRegister ? "/login" : "/register"}
            className="font-medium text-accent underline-offset-2 hover:underline"
          >
            {isRegister ? "Sign in" : "Create an account"}
          </Link>
        </p>
      </div>
    </main>
  );
}
