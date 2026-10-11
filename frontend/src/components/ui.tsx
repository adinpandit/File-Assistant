"use client";

import { forwardRef, useEffect, useId, useRef, useState } from "react";
import { Loader2 } from "lucide-react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-accent text-white hover:bg-accent-hover disabled:bg-accent/50",
  secondary: "border border-line-strong bg-surface text-ink hover:bg-subtle disabled:text-ink-faint",
  ghost: "text-ink-muted hover:bg-subtle hover:text-ink disabled:text-ink-faint",
  danger: "bg-danger text-white hover:bg-danger/90 disabled:bg-danger/50",
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "secondary", loading = false, className = "", children, disabled, type = "button", ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      className={`inline-flex h-9 items-center justify-center gap-2 rounded-md px-3.5 text-sm font-medium transition-colors disabled:cursor-not-allowed ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {loading && <Loader2 aria-hidden className="size-4 animate-spin" />}
      {children}
    </button>
  );
});

export function Spinner({ className = "", label }: { className?: string; label?: string }) {
  return (
    <span role="status" className={`inline-flex items-center gap-2 text-sm text-ink-muted ${className}`}>
      <Loader2 aria-hidden className="size-4 animate-spin" />
      {label ?? <span className="sr-only">Loading</span>}
    </span>
  );
}

export function ErrorNotice({
  message,
  onRetry,
  className = "",
}: {
  message: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={`flex flex-wrap items-center justify-between gap-3 rounded-md border border-danger/20 bg-danger-soft px-3 py-2 text-sm text-danger ${className}`}
    >
      <span>{message}</span>
      {onRetry && (
        <button type="button" onClick={onRetry} className="font-medium underline underline-offset-2 hover:no-underline">
          Try again
        </button>
      )}
    </div>
  );
}

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: React.ReactNode;
  confirmLabel: string;
  onConfirm: () => Promise<void>;
  onClose: () => void;
}

// Native <dialog> with showModal() gives focus trapping, Escape to close and
// an inert background without extra dependencies.
export function ConfirmDialog({ open, title, description, confirmLabel, onConfirm, onClose }: ConfirmDialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      await onConfirm();
      onClose();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <dialog
      ref={ref}
      onClose={() => {
        setError(null);
        onClose();
      }}
      onCancel={(event) => {
        if (busy) event.preventDefault();
      }}
      aria-labelledby={titleId}
      className="m-auto w-[calc(100%-2rem)] max-w-sm rounded-lg border border-line bg-surface p-5 text-ink shadow-lg"
    >
      <h2 id={titleId} className="text-base font-semibold">
        {title}
      </h2>
      <div className="mt-2 text-sm text-ink-muted">{description}</div>
      {error && <ErrorNotice message={error} className="mt-3" />}
      <div className="mt-5 flex justify-end gap-2">
        <Button onClick={onClose} disabled={busy}>
          Cancel
        </Button>
        <Button variant="danger" onClick={confirm} loading={busy}>
          {confirmLabel}
        </Button>
      </div>
    </dialog>
  );
}
