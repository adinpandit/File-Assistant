"use client";

import { useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, Upload, X } from "lucide-react";
import { SUPPORTED_EXTENSIONS, useDocuments, type UploadItem } from "@/hooks/useDocuments";
import { formatBytes } from "@/lib/format";

export function UploadDropzone() {
  const { enqueueUploads, uploads, dismissUpload } = useDocuments();
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handleFiles(list: FileList | null) {
    if (list && list.length > 0) enqueueUploads(Array.from(list));
  }

  return (
    <div>
      <div
        onDragEnter={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          handleFiles(event.dataTransfer.files);
        }}
        className={`flex flex-col items-center justify-center rounded-lg border border-dashed px-4 py-8 text-center transition-colors ${
          dragging ? "border-accent bg-accent-soft/50" : "border-line-strong bg-surface"
        }`}
      >
        <Upload aria-hidden className="size-5 text-ink-faint" />
        <p className="mt-2 text-sm">
          <button
            type="button"
            onClick={() => input.current?.click()}
            className="font-medium text-accent underline-offset-2 hover:underline"
          >
            Choose files
          </button>{" "}
          <span className="text-ink-muted">or drag them here</span>
        </p>
        <p className="mt-1 text-xs text-ink-faint">PDF, TXT, or Markdown · up to 50 MB each (server default)</p>
        <input
          ref={input}
          type="file"
          multiple
          accept={SUPPORTED_EXTENSIONS.join(",")}
          className="sr-only"
          tabIndex={-1}
          aria-hidden
          onChange={(event) => {
            handleFiles(event.target.files);
            event.target.value = "";
          }}
        />
      </div>

      {uploads.length > 0 && (
        <ul className="mt-3 divide-y divide-line rounded-lg border border-line bg-surface" aria-label="Uploads">
          {uploads.map((item) => (
            <UploadRow key={item.id} item={item} onDismiss={() => dismissUpload(item.id)} />
          ))}
        </ul>
      )}
    </div>
  );
}

function UploadRow({ item, onDismiss }: { item: UploadItem; onDismiss: () => void }) {
  const finished = item.status === "done" || item.status === "failed";
  const statusText: Record<UploadItem["status"], string> = {
    queued: "Waiting…",
    uploading: `Uploading · ${Math.round(item.progress * 100)}%`,
    processing: "Processing — extracting text and indexing…",
    done: "Added to your library",
    failed: item.error ?? "Upload failed",
  };

  return (
    <li className="flex items-center gap-3 px-3.5 py-2.5 text-sm">
      <span className="shrink-0">
        {item.status === "done" ? (
          <CheckCircle2 aria-hidden className="size-4 text-accent" />
        ) : item.status === "failed" ? (
          <AlertCircle aria-hidden className="size-4 text-danger" />
        ) : (
          <Loader2 aria-hidden className="size-4 animate-spin text-ink-faint" />
        )}
      </span>
      <div className="min-w-0 flex-1">
        <p className="flex items-baseline gap-2">
          <span className="truncate font-medium">{item.name}</span>
          <span className="shrink-0 text-xs text-ink-faint">{formatBytes(item.size)}</span>
        </p>
        <p role={item.status === "failed" ? "alert" : undefined} className={`text-xs ${item.status === "failed" ? "text-danger" : "text-ink-muted"}`}>
          {statusText[item.status]}
        </p>
        {item.status === "uploading" && (
          <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-subtle" aria-hidden>
            <div className="h-full bg-accent transition-[width]" style={{ width: `${item.progress * 100}%` }} />
          </div>
        )}
      </div>
      {finished && (
        <button
          type="button"
          onClick={onDismiss}
          aria-label={`Dismiss ${item.name}`}
          className="shrink-0 rounded p-1 text-ink-faint hover:bg-subtle hover:text-ink"
        >
          <X aria-hidden className="size-4" />
        </button>
      )}
    </li>
  );
}
