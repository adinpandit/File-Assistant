"use client";

import { citationLabel } from "@/lib/citations";

const base =
  "mx-0.5 inline-flex h-[1.2rem] min-w-[1.2rem] items-center justify-center rounded border px-1 align-[0.12em] text-[0.7rem] font-medium leading-none tabular-nums";

export function CitationChip({
  id,
  description,
  onSelect,
}: {
  id: string;
  description?: string;
  onSelect?: () => void;
}) {
  if (!onSelect) {
    return (
      <span
        className={`${base} border-line bg-subtle text-ink-faint`}
        title="Source details are not stored with conversation history"
      >
        {citationLabel(id)}
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={onSelect}
      title={description}
      aria-label={`Source ${citationLabel(id)}${description ? `: ${description}` : ""}`}
      className={`${base} border-line-strong bg-surface text-ink-muted transition-colors hover:border-accent hover:text-accent`}
    >
      {citationLabel(id)}
    </button>
  );
}
