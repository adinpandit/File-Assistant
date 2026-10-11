"use client";

import { useId, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";
import { useConversations } from "@/hooks/useConversations";
import { formatRelative } from "@/lib/format";
import { ConfirmDialog, Spinner } from "@/components/ui";
import type { Conversation } from "@/types";

export function HistoryPanel({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const { conversations, status, error, refresh, remove } = useConversations();
  const headingId = useId();
  const [pendingDelete, setPendingDelete] = useState<Conversation | null>(null);

  async function confirmDelete() {
    if (!pendingDelete) return;
    const id = pendingDelete.conversation_id;
    await remove(id);
    if (pathname === `/c/${id}`) router.replace("/");
  }

  return (
    <section aria-labelledby={headingId} className="flex min-h-0 flex-1 flex-col">
      <h2 id={headingId} className="px-3 pb-1 pt-4 text-xs font-medium text-ink-faint">
        Conversations
      </h2>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
        {status === "loading" && <Spinner className="px-2 py-2" label="Loading…" />}

        {status === "error" && (
          <div className="px-2 py-2 text-sm text-ink-muted">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => void refresh()}
              className="mt-1 font-medium text-accent underline-offset-2 hover:underline"
            >
              Try again
            </button>
          </div>
        )}

        {status === "ready" && conversations.length === 0 && (
          <p className="px-2 py-2 text-sm text-ink-muted">Your conversations will appear here.</p>
        )}

        {conversations.length > 0 && (
          <ul className="space-y-px">
            {conversations.map((conversation) => {
              const href = `/c/${conversation.conversation_id}`;
              const selected = pathname === href;
              return (
                <li key={conversation.conversation_id} className="group relative">
                  <Link
                    href={href}
                    onClick={onNavigate}
                    aria-current={selected ? "page" : undefined}
                    className={`block rounded-md py-1.5 pl-2.5 pr-9 text-sm transition-colors ${
                      selected ? "bg-line/70 text-ink" : "text-ink-muted hover:bg-line/40 hover:text-ink"
                    }`}
                  >
                    <span className="block truncate">{conversation.title}</span>
                    <span className="block text-xs text-ink-faint">{formatRelative(conversation.updated_at)}</span>
                  </Link>
                  <button
                    type="button"
                    onClick={() => setPendingDelete(conversation)}
                    aria-label={`Delete conversation “${conversation.title}”`}
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded p-1.5 text-ink-faint opacity-0 transition hover:bg-line hover:text-danger focus-visible:opacity-100 group-hover:opacity-100 [@media(hover:none)]:opacity-100"
                  >
                    <Trash2 aria-hidden className="size-3.5" />
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete conversation?"
        description={
          <>
            <span className="font-medium text-ink">{pendingDelete?.title}</span> and all of its messages will be
            permanently deleted.
          </>
        }
        confirmLabel="Delete"
        onConfirm={confirmDelete}
        onClose={() => setPendingDelete(null)}
      />
    </section>
  );
}
