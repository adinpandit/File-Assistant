"use client";

import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/api/client";
import { useConversations } from "@/hooks/useConversations";
import type { ChatMessage, StoredMessage } from "@/types";

type LoadStatus = "idle" | "loading" | "ready" | "not-found" | "error";

interface ChatState {
  conversationId: string | null;
  messages: ChatMessage[];
  load: LoadStatus;
  loadError: string | null;
}

interface ChatContextValue extends ChatState {
  pending: boolean;
  open: (conversationId: string | null) => void;
  reload: () => void;
  send: (text: string, documentId: string | null) => Promise<void>;
  retry: (messageId: string) => void;
}

const EMPTY: ChatState = { conversationId: null, messages: [], load: "idle", loadError: null };

const ChatContext = createContext<ChatContextValue | null>(null);

let localCounter = 0;
function localId(): string {
  localCounter += 1;
  return `local-${Date.now()}-${localCounter}`;
}

function titleFrom(text: string): string {
  const singleLine = text.replace(/\s+/g, " ").trim();
  return singleLine.length > 80 ? `${singleLine.slice(0, 79).trimEnd()}…` : singleLine;
}

function fromStored(message: StoredMessage): ChatMessage {
  return message.role === "user"
    ? { id: message.message_id, role: "user", content: message.content, status: "sent" }
    : { id: message.message_id, role: "assistant", content: message.content };
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { add: addConversation, refresh: refreshConversations } = useConversations();
  const [state, setState] = useState<ChatState>(EMPTY);

  // Which conversation the view currently shows, and a counter bumped on every
  // switch so responses that arrive after the user moved on are discarded.
  const activeId = useRef<string | null>(null);
  const generation = useRef(0);

  const loadMessages = useCallback(async (conversationId: string, gen: number) => {
    try {
      const { messages } = await api.conversations.messages(conversationId);
      if (gen !== generation.current) return;
      setState({ conversationId, messages: messages.map(fromStored), load: "ready", loadError: null });
    } catch (cause) {
      if (gen !== generation.current) return;
      const notFound = cause instanceof ApiError && (cause.status === 404 || cause.status === 400);
      setState({
        conversationId,
        messages: [],
        load: notFound ? "not-found" : "error",
        loadError: errorMessage(cause, "Could not load this conversation."),
      });
    }
  }, []);

  const open = useCallback(
    (conversationId: string | null) => {
      if (conversationId === activeId.current) return;
      activeId.current = conversationId;
      generation.current += 1;
      if (conversationId === null) {
        setState(EMPTY);
        return;
      }
      setState({ conversationId, messages: [], load: "loading", loadError: null });
      void loadMessages(conversationId, generation.current);
    },
    [loadMessages],
  );

  const reload = useCallback(() => {
    const conversationId = activeId.current;
    if (!conversationId) return;
    generation.current += 1;
    setState({ conversationId, messages: [], load: "loading", loadError: null });
    void loadMessages(conversationId, generation.current);
  }, [loadMessages]);

  const markUser = useCallback((id: string, patch: { status: "sent" | "failed"; error?: string }) => {
    setState((current) => ({
      ...current,
      messages: current.messages.map((message) =>
        message.id === id && message.role === "user" ? { ...message, ...patch } : message,
      ),
    }));
  }, []);

  const send = useCallback(
    async (text: string, documentId: string | null) => {
      const query = text.trim();
      if (!query) return;
      const gen = generation.current;
      const userMessage: ChatMessage = { id: localId(), role: "user", content: query, status: "pending", documentId };
      setState((current) => ({ ...current, load: "ready", messages: [...current.messages, userMessage] }));

      // A new chat becomes a stored conversation on its first question, so the
      // backend persists the exchange and it appears in history.
      let conversationId = activeId.current;
      if (!conversationId) {
        try {
          const conversation = await api.conversations.create(titleFrom(query));
          addConversation(conversation);
          if (gen !== generation.current) return;
          conversationId = conversation.conversation_id;
          activeId.current = conversationId;
          setState((current) => ({ ...current, conversationId }));
          router.replace(`/c/${conversationId}`);
        } catch (cause) {
          if (gen === generation.current) {
            markUser(userMessage.id, {
              status: "failed",
              error: errorMessage(cause, "Could not start a conversation."),
            });
          }
          return;
        }
      }

      try {
        const response = await api.query({
          query,
          conversation_id: conversationId,
          document_id: documentId ?? undefined,
        });
        void refreshConversations();
        if (gen !== generation.current) return;
        setState((current) => ({
          ...current,
          messages: [
            ...current.messages.map((message) =>
              message.id === userMessage.id && message.role === "user"
                ? { ...message, status: "sent" as const }
                : message,
            ),
            {
              id: localId(),
              role: "assistant",
              content: response.answer,
              citations: response.citations,
              sources: response.sources,
            },
          ],
        }));
      } catch (cause) {
        if (gen !== generation.current) return;
        markUser(userMessage.id, { status: "failed", error: errorMessage(cause, "The answer could not be generated.") });
      }
    },
    [addConversation, markUser, refreshConversations, router],
  );

  const retry = useCallback(
    (messageId: string) => {
      const failed = state.messages.find(
        (message) => message.id === messageId && message.role === "user" && message.status === "failed",
      );
      if (!failed || failed.role !== "user") return;
      setState((current) => ({ ...current, messages: current.messages.filter((message) => message.id !== messageId) }));
      void send(failed.content, failed.documentId ?? null);
    },
    [send, state.messages],
  );

  const pending = state.messages.some((message) => message.role === "user" && message.status === "pending");

  const value = useMemo<ChatContextValue>(
    () => ({ ...state, pending, open, reload, send, retry }),
    [state, pending, open, reload, send, retry],
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat(): ChatContextValue {
  const context = useContext(ChatContext);
  if (!context) throw new Error("useChat must be used inside ChatProvider");
  return context;
}
