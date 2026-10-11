"use client";

import { useEffect, useId, useMemo, useState } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { AlertCircle, ChevronRight, RotateCcw } from "lucide-react";
import { useDocuments } from "@/hooks/useDocuments";
import {
  buildSourceEntries,
  CITATION_HREF_PREFIX,
  citationLabel,
  citedIds,
  linkCitationMarkers,
  type SourceEntry,
} from "@/lib/citations";
import { CitationChip } from "@/components/CitationChip";
import type { ChatMessage, DocumentRecord } from "@/types";

type UserMessage = Extract<ChatMessage, { role: "user" }>;
type AssistantMessage = Extract<ChatMessage, { role: "assistant" }>;

export function MessageBubble({ message, onRetry }: { message: ChatMessage; onRetry?: (id: string) => void }) {
  return message.role === "user" ? (
    <UserBubble message={message} onRetry={onRetry} />
  ) : (
    <AssistantAnswer message={message} />
  );
}

function UserBubble({ message, onRetry }: { message: UserMessage; onRetry?: (id: string) => void }) {
  const { findDocument } = useDocuments();
  const scope = message.documentId ? findDocument(message.documentId) : undefined;

  return (
    <div className="flex flex-col items-end">
      <div className="max-w-[85%] whitespace-pre-wrap break-words rounded-lg bg-line/60 px-3.5 py-2 text-ink">
        {message.content}
      </div>
      {scope && <p className="mt-1 text-xs text-ink-faint">Asked about {scope.filename}</p>}
      {message.status === "failed" && (
        <div role="alert" className="mt-2 flex max-w-[85%] items-start gap-2 text-sm text-danger">
          <AlertCircle aria-hidden className="mt-0.5 size-4 shrink-0" />
          <p>
            {message.error ?? "The answer could not be generated."}{" "}
            {onRetry && (
              <button
                type="button"
                onClick={() => onRetry(message.id)}
                className="inline-flex items-center gap-1 font-medium underline underline-offset-2 hover:no-underline"
              >
                <RotateCcw aria-hidden className="size-3.5" />
                Retry
              </button>
            )}
          </p>
        </div>
      )}
    </div>
  );
}

function describeEntry(entry: SourceEntry, document: DocumentRecord | undefined): string {
  const name = document?.filename ?? "Unavailable document";
  return showPage(entry, document) ? `${name}, page ${entry.pageNumber}` : name;
}

// Text and Markdown files are ingested as a single page, so a page number only
// carries information for PDFs (or when the document type is unknown).
function showPage(entry: SourceEntry, document: DocumentRecord | undefined): boolean {
  return entry.pageNumber > 0 && (!document || document.file_type === "pdf");
}

function AssistantAnswer({ message }: { message: AssistantMessage }) {
  const { findDocument } = useDocuments();
  const panelId = useId();
  const [open, setOpen] = useState(false);
  // tick re-triggers scrolling when the same citation is selected again.
  const [focus, setFocus] = useState<{ id: string; tick: number } | null>(null);
  const highlight = focus?.id ?? null;

  const hasSourceData = message.citations !== undefined || message.sources !== undefined;
  const entries = useMemo(
    () => buildSourceEntries(message.citations, message.sources),
    [message.citations, message.sources],
  );
  const cited = useMemo(() => citedIds(message.content), [message.content]);
  const markdown = useMemo(() => linkCitationMarkers(message.content), [message.content]);
  const entryById = useMemo(() => new Map(entries.filter((e) => e.id).map((e) => [e.id as string, e])), [entries]);

  const anchorId = (id: string) => `${panelId}-${id}`;

  useEffect(() => {
    if (!focus) return;
    document.getElementById(`${panelId}-${focus.id}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [focus, panelId]);

  const components: Components = {
    a({ href, children, ...props }) {
      if (href?.startsWith(CITATION_HREF_PREFIX)) {
        const id = href.slice(CITATION_HREF_PREFIX.length);
        const entry = entryById.get(id);
        if (!hasSourceData || !entry) return <CitationChip id={id} />;
        return (
          <CitationChip
            id={id}
            description={describeEntry(entry, findDocument(entry.documentId))}
            onSelect={() => {
              setOpen(true);
              setFocus((previous) => ({ id, tick: (previous?.tick ?? 0) + 1 }));
            }}
          />
        );
      }
      return (
        <a href={href} target="_blank" rel="noreferrer noopener" {...props}>
          {children}
        </a>
      );
    },
  };

  return (
    <div>
      <div className="answer prose prose-sm max-w-none break-words sm:prose-base prose-headings:font-semibold prose-headings:tracking-tight prose-h1:text-xl prose-h2:text-lg prose-h3:text-base prose-p:leading-relaxed">
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
          {markdown}
        </ReactMarkdown>
      </div>

      {!hasSourceData && cited.size > 0 && (
        <p className="mt-2 text-xs text-ink-faint">Source details aren’t stored with conversation history.</p>
      )}

      {entries.length > 0 && (
        <div className="mt-3">
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            aria-expanded={open}
            aria-controls={panelId}
            className="-ml-1.5 inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-sm text-ink-muted transition-colors hover:bg-subtle hover:text-ink"
          >
            <ChevronRight aria-hidden className={`size-4 transition-transform ${open ? "rotate-90" : ""}`} />
            {entries.length === 1 ? "1 source" : `${entries.length} sources`}
          </button>

          {open && (
            <ol id={panelId} className="mt-2 divide-y divide-line overflow-hidden rounded-lg border border-line bg-surface">
              {entries.map((entry, index) => (
                <SourceItem
                  key={entry.source?.chunk_id ?? `${entry.id}-${index}`}
                  anchorId={entry.id ? anchorId(entry.id) : undefined}
                  entry={entry}
                  document={findDocument(entry.documentId)}
                  cited={entry.id !== null && cited.has(entry.id)}
                  highlighted={entry.id !== null && entry.id === highlight}
                />
              ))}
            </ol>
          )}
        </div>
      )}
    </div>
  );
}

function SourceItem({
  anchorId,
  entry,
  document,
  cited,
  highlighted,
}: {
  anchorId?: string;
  entry: SourceEntry;
  document: DocumentRecord | undefined;
  cited: boolean;
  highlighted: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const text = entry.source?.text.trim() ?? "";
  const long = text.length > 280;

  return (
    <li
      id={anchorId}
      className={`scroll-mt-4 px-3.5 py-3 text-sm transition-colors ${highlighted ? "bg-accent-soft/60" : ""}`}
    >
      <div className="flex items-baseline gap-2">
        {entry.id && (
          <span
            className={`inline-flex h-5 min-w-5 shrink-0 items-center justify-center rounded border px-1 text-[0.7rem] font-medium tabular-nums ${
              cited ? "border-accent/40 text-accent" : "border-line-strong text-ink-faint"
            }`}
          >
            {citationLabel(entry.id)}
          </span>
        )}
        <div className="min-w-0 flex-1">
          <p className="flex flex-wrap items-baseline gap-x-2">
            <span className="truncate font-medium text-ink" title={document?.filename}>
              {document?.filename ?? "Unavailable document"}
            </span>
            {showPage(entry, document) && <span className="text-ink-muted">Page {entry.pageNumber}</span>}
            {entry.id && !cited && <span className="text-xs text-ink-faint">Not cited in answer</span>}
          </p>
          {!document && (
            <p className="text-xs text-ink-faint">This document is no longer in your library.</p>
          )}
        </div>
        {entry.source && (
          <span
            className="shrink-0 text-xs tabular-nums text-ink-faint"
            title="Vector similarity reported by the retriever"
          >
            {entry.source.score.toFixed(2)}
          </span>
        )}
      </div>

      {text ? (
        <div className={entry.id ? "mt-1.5 sm:pl-7" : "mt-1.5"}>
          <p className={`whitespace-pre-line break-words text-ink-muted ${expanded ? "" : "line-clamp-3"}`}>{text}</p>
          {long && (
            <button
              type="button"
              onClick={() => setExpanded((value) => !value)}
              className="mt-1 text-xs font-medium text-accent underline-offset-2 hover:underline"
            >
              {expanded ? "Show less" : "Show full excerpt"}
            </button>
          )}
        </div>
      ) : (
        <p className={`mt-1 text-xs text-ink-faint ${entry.id ? "sm:pl-7" : ""}`}>No excerpt was returned for this source.</p>
      )}
    </li>
  );
}
