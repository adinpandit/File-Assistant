"use client";

import { useLayoutEffect, useRef, useState } from "react";
import { ArrowUp } from "lucide-react";
import type { DocumentRecord } from "@/types";

// QueryRequest.query max_length in backend/app/api/routes/query.py.
const MAX_QUERY_LENGTH = 4000;

interface ComposerProps {
  documents: DocumentRecord[];
  scope: string | null;
  onScopeChange: (documentId: string | null) => void;
  onSend: (text: string) => void;
  busy: boolean;
  disabled?: boolean;
  disabledReason?: string;
}

export function Composer({ documents, scope, onScopeChange, onSend, busy, disabled, disabledReason }: ComposerProps) {
  const [text, setText] = useState("");
  const textarea = useRef<HTMLTextAreaElement>(null);
  const trimmed = text.trim();
  const canSend = !busy && !disabled && trimmed.length > 0 && text.length <= MAX_QUERY_LENGTH;

  // Grow with content up to a limit, then scroll.
  useLayoutEffect(() => {
    const element = textarea.current;
    if (!element) return;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 200)}px`;
  }, [text]);

  function submit() {
    if (!canSend) return;
    onSend(trimmed);
    setText("");
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
      className="rounded-lg border border-line-strong bg-surface shadow-[0_1px_2px_rgb(31_30_28/0.04)] transition-colors focus-within:border-accent/60"
    >
      <label htmlFor="composer" className="sr-only">
        Ask a question about your documents
      </label>
      <textarea
        id="composer"
        ref={textarea}
        rows={1}
        value={text}
        disabled={disabled}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault();
            submit();
          }
        }}
        placeholder={disabled ? disabledReason : "Ask a question about your documents…"}
        aria-describedby="composer-hint"
        className="block max-h-[200px] w-full resize-none bg-transparent px-3.5 pt-3 pb-1 text-[15px] outline-none placeholder:text-ink-faint focus-visible:outline-none disabled:cursor-not-allowed"
      />
      <div className="flex items-center gap-2 px-2 pb-2 pt-1">
        <label htmlFor="scope" className="sr-only">
          Documents to search
        </label>
        <select
          id="scope"
          value={scope ?? ""}
          disabled={disabled || documents.length === 0}
          onChange={(event) => onScopeChange(event.target.value || null)}
          className="h-8 min-w-0 max-w-[60%] truncate rounded-md border border-transparent bg-transparent px-1.5 text-sm text-ink-muted hover:bg-subtle focus:border-line-strong disabled:opacity-60 sm:max-w-xs"
        >
          <option value="">All documents</option>
          {documents.map((doc) => (
            <option key={doc.document_id} value={doc.document_id}>
              {doc.filename}
            </option>
          ))}
        </select>
        <span id="composer-hint" className="ml-auto hidden text-xs text-ink-faint sm:inline">
          {text.length > MAX_QUERY_LENGTH - 500
            ? `${text.length.toLocaleString()} / ${MAX_QUERY_LENGTH.toLocaleString()}`
            : "Enter to send · Shift + Enter for a new line"}
        </span>
        <button
          type="submit"
          disabled={!canSend}
          aria-label="Send"
          className="ml-auto flex size-8 shrink-0 items-center justify-center rounded-md bg-accent text-white transition-colors hover:bg-accent-hover disabled:bg-line-strong disabled:text-surface sm:ml-0"
        >
          <ArrowUp aria-hidden className="size-4" />
        </button>
      </div>
    </form>
  );
}
