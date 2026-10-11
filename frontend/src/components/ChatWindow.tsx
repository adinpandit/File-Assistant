"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import Link from "next/link";
import { useChat } from "@/hooks/useChat";
import { useDocuments } from "@/hooks/useDocuments";
import { useConversations } from "@/hooks/useConversations";
import { Composer } from "@/components/Composer";
import { MessageBubble } from "@/components/MessageBubble";
import { ErrorNotice, Spinner } from "@/components/ui";

export function ChatWindow({ conversationId }: { conversationId: string | null }) {
  const chat = useChat();
  const { open } = chat;
  const { documents, status: documentsStatus } = useDocuments();
  const { conversations } = useConversations();
  const [scopeChoice, setScopeChoice] = useState<string | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  // Layout effect so a previously open conversation never flashes on screen.
  useLayoutEffect(() => {
    open(conversationId);
  }, [conversationId, open]);

  // A new chat (route "/") keeps showing its messages after the conversation is
  // created, until the URL catches up to /c/<id>.
  const inSync = conversationId === null || chat.conversationId === conversationId;
  const messages = inSync ? chat.messages : [];
  const load = inSync ? chat.load : "loading";

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [messages.length, chat.pending]);

  // Fall back to all documents if the selected one was deleted.
  const scope = scopeChoice && documents.some((doc) => doc.document_id === scopeChoice) ? scopeChoice : null;
  const noDocuments = documentsStatus === "ready" && documents.length === 0;
  const title = conversations.find((item) => item.conversation_id === conversationId)?.title;

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {title && (
        <div className="hidden h-12 shrink-0 items-center border-b border-line px-6 md:flex">
          <h1 className="truncate text-sm font-medium">{title}</h1>
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
          {load === "loading" && (
            <div className="flex justify-center py-16">
              <Spinner label="Loading conversation…" />
            </div>
          )}

          {load === "not-found" && (
            <div className="py-16 text-center">
              <h1 className="text-base font-semibold">Conversation not found</h1>
              <p className="mt-1 text-sm text-ink-muted">It may have been deleted, or the link is incorrect.</p>
              <Link href="/" className="mt-4 inline-block text-sm font-medium text-accent underline-offset-2 hover:underline">
                Start a new conversation
              </Link>
            </div>
          )}

          {load === "error" && (
            <ErrorNotice message={chat.loadError ?? "Could not load this conversation."} onRetry={chat.reload} />
          )}

          {(load === "idle" || load === "ready") && messages.length === 0 && (
            <EmptyState noDocuments={noDocuments} documentCount={documents.length} />
          )}

          {messages.length > 0 && (
            <ol className="space-y-8" aria-label="Messages">
              {messages.map((message) => (
                <li key={message.id}>
                  <MessageBubble message={message} onRetry={chat.pending ? undefined : chat.retry} />
                </li>
              ))}
              {chat.pending && (
                <li>
                  <Spinner label="Searching your documents and writing an answer…" />
                </li>
              )}
            </ol>
          )}
          <div ref={bottom} />
        </div>
      </div>

      {load !== "not-found" && (
        <div className="shrink-0 bg-canvas px-4 pb-4 sm:px-6">
          <div className="mx-auto w-full max-w-3xl">
            <Composer
              documents={documents}
              scope={scope}
              onScopeChange={setScopeChoice}
              onSend={(text) => void chat.send(text, scope)}
              busy={chat.pending || load === "loading"}
              disabled={noDocuments || load === "error"}
              disabledReason={noDocuments ? "Upload a document to start asking questions" : undefined}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function EmptyState({ noDocuments, documentCount }: { noDocuments: boolean; documentCount: number }) {
  return (
    <div className="pt-[12vh] text-center">
      <h1 className="text-lg font-semibold tracking-tight">Ask about your documents</h1>
      {noDocuments ? (
        <p className="mx-auto mt-2 max-w-md text-sm text-ink-muted">
          Answers are generated only from documents you upload.{" "}
          <Link href="/documents" className="font-medium text-accent underline-offset-2 hover:underline">
            Upload a PDF, text, or Markdown file
          </Link>{" "}
          to get started.
        </p>
      ) : (
        <p className="mx-auto mt-2 max-w-md text-sm text-ink-muted">
          Answers are drawn from your {documentCount > 0 ? `${documentCount} ` : ""}
          {documentCount === 1 ? "document" : "documents"}, with numbered citations linking to the passages used. Choose
          a single document below to narrow the search.
        </p>
      )}
    </div>
  );
}
