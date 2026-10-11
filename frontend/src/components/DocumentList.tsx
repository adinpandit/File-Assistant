"use client";

import { useState } from "react";
import { FileText, Trash2 } from "lucide-react";
import { useDocuments } from "@/hooks/useDocuments";
import { formatDate } from "@/lib/format";
import { ConfirmDialog, ErrorNotice, Spinner } from "@/components/ui";
import type { DocumentRecord } from "@/types";

const TYPE_LABELS: Record<string, string> = { pdf: "PDF", txt: "Text", md: "Markdown" };

function plural(count: number, word: string): string {
  return `${count.toLocaleString()} ${word}${count === 1 ? "" : "s"}`;
}

export function DocumentList() {
  const { documents, status, error, refresh, remove } = useDocuments();
  const [pendingDelete, setPendingDelete] = useState<DocumentRecord | null>(null);

  if (status === "loading") {
    return (
      <div className="py-10 text-center">
        <Spinner label="Loading documents…" />
      </div>
    );
  }

  if (status === "error") {
    return <ErrorNotice message={error ?? "Could not load documents."} onRetry={() => void refresh()} />;
  }

  if (documents.length === 0) {
    return (
      <div className="rounded-lg border border-line px-4 py-10 text-center">
        <p className="text-sm font-medium">No documents yet</p>
        <p className="mt-1 text-sm text-ink-muted">Uploaded files will be listed here once they’re indexed.</p>
      </div>
    );
  }

  return (
    <>
      {error && <ErrorNotice message={error} onRetry={() => void refresh()} className="mb-3" />}
      <div className="overflow-hidden rounded-lg border border-line bg-surface">
        <table className="w-full text-sm">
          <caption className="sr-only">Your documents</caption>
          <thead className="hidden border-b border-line bg-subtle/60 text-left text-xs font-medium text-ink-muted sm:table-header-group">
            <tr>
              <th scope="col" className="px-3.5 py-2 font-medium">Name</th>
              <th scope="col" className="px-3 py-2 font-medium">Type</th>
              <th scope="col" className="px-3 py-2 text-right font-medium">Pages</th>
              <th scope="col" className="px-3 py-2 text-right font-medium">Chunks</th>
              <th scope="col" className="px-3 py-2 font-medium">Uploaded</th>
              <th scope="col" className="w-12 px-2 py-2">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {documents.map((doc) => (
              <tr key={doc.document_id} className="group align-middle hover:bg-canvas">
                <td className="max-w-0 px-3.5 py-2.5">
                  <div className="flex items-center gap-2.5">
                    <FileText aria-hidden className="size-4 shrink-0 text-ink-faint" />
                    <div className="min-w-0">
                      <p className="truncate font-medium" title={doc.filename}>
                        {doc.filename}
                      </p>
                      {/* Compact metadata line on small screens */}
                      <p className="truncate text-xs text-ink-muted sm:hidden">
                        {TYPE_LABELS[doc.file_type] ?? doc.file_type} · {plural(doc.page_count, "page")} ·{" "}
                        {plural(doc.chunk_count, "chunk")} · {formatDate(doc.upload_time)}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="hidden px-3 py-2.5 text-ink-muted sm:table-cell">
                  {TYPE_LABELS[doc.file_type] ?? doc.file_type}
                </td>
                <td className="hidden px-3 py-2.5 text-right tabular-nums text-ink-muted sm:table-cell">
                  {doc.page_count.toLocaleString()}
                </td>
                <td className="hidden px-3 py-2.5 text-right tabular-nums text-ink-muted sm:table-cell">
                  {doc.chunk_count.toLocaleString()}
                </td>
                <td className="hidden whitespace-nowrap px-3 py-2.5 text-ink-muted sm:table-cell">
                  {formatDate(doc.upload_time)}
                </td>
                <td className="w-12 px-2 py-2.5 text-right">
                  <button
                    type="button"
                    onClick={() => setPendingDelete(doc)}
                    aria-label={`Delete ${doc.filename}`}
                    className="rounded-md p-1.5 text-ink-faint transition-colors hover:bg-danger-soft hover:text-danger"
                  >
                    <Trash2 aria-hidden className="size-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete document?"
        description={
          <>
            <span className="font-medium text-ink">{pendingDelete?.filename}</span> will be removed from your library and
            its passages will no longer be used to answer questions. This can’t be undone.
          </>
        }
        confirmLabel="Delete document"
        onConfirm={async () => {
          if (pendingDelete) await remove(pendingDelete.document_id);
        }}
        onClose={() => setPendingDelete(null)}
      />
    </>
  );
}
