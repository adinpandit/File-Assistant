"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/api/client";
import type { Conversation } from "@/types";

type LoadStatus = "loading" | "ready" | "error";

interface ConversationsContextValue {
  conversations: Conversation[];
  status: LoadStatus;
  error: string | null;
  refresh: () => Promise<void>;
  add: (conversation: Conversation) => void;
  remove: (conversationId: string) => Promise<void>;
}

const ConversationsContext = createContext<ConversationsContextValue | null>(null);

export function ConversationsProvider({ children }: { children: React.ReactNode }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [status, setStatus] = useState<LoadStatus>("loading");
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(
    () =>
      api.conversations.list().then(
        (response) => {
          setConversations(response.conversations);
          setStatus("ready");
          setError(null);
        },
        (cause: unknown) => {
          setStatus((previous) => (previous === "ready" ? previous : "error"));
          setError(cause instanceof ApiError ? cause.message : "Could not load conversations.");
        },
      ),
    [],
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const add = useCallback((conversation: Conversation) => {
    setConversations((current) => [
      conversation,
      ...current.filter((item) => item.conversation_id !== conversation.conversation_id),
    ]);
  }, []);

  const remove = useCallback(async (conversationId: string) => {
    await api.conversations.remove(conversationId);
    setConversations((current) => current.filter((item) => item.conversation_id !== conversationId));
  }, []);

  const value = useMemo<ConversationsContextValue>(
    () => ({ conversations, status, error, refresh, add, remove }),
    [conversations, status, error, refresh, add, remove],
  );

  return <ConversationsContext.Provider value={value}>{children}</ConversationsContext.Provider>;
}

export function useConversations(): ConversationsContextValue {
  const context = useContext(ConversationsContext);
  if (!context) throw new Error("useConversations must be used inside ConversationsProvider");
  return context;
}
