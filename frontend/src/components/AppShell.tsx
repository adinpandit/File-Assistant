"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FileText, LogOut, Menu, Plus, X } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { ChatProvider } from "@/hooks/useChat";
import { ConversationsProvider } from "@/hooks/useConversations";
import { DocumentsProvider, useDocuments } from "@/hooks/useDocuments";
import { HistoryPanel } from "@/components/HistoryPanel";
import { Spinner } from "@/components/ui";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { status } = useAuth();

  useEffect(() => {
    if (status === "anonymous") router.replace("/login");
  }, [status, router]);

  if (status !== "authenticated") {
    return (
      <main className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </main>
    );
  }

  return (
    <DocumentsProvider>
      <ConversationsProvider>
        <ChatProvider>
          <Workspace>{children}</Workspace>
        </ChatProvider>
      </ConversationsProvider>
    </DocumentsProvider>
  );
}

function Workspace({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const closeButton = useRef<HTMLButtonElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const close = () => {
    setDrawerOpen(false);
    menuButton.current?.focus();
  };

  useEffect(() => {
    if (!drawerOpen) return;
    closeButton.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDrawerOpen(false);
        menuButton.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  return (
    <div className="flex h-dvh overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-line bg-subtle md:flex md:flex-col">
        <Sidebar />
      </aside>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            tabIndex={-1}
            onClick={close}
            className="absolute inset-0 bg-ink/30"
          />
          <aside
            id="mobile-nav"
            aria-label="Navigation"
            className="absolute inset-y-0 left-0 flex w-[min(18rem,85vw)] flex-col border-r border-line bg-subtle shadow-xl"
          >
            <button
              ref={closeButton}
              type="button"
              onClick={close}
              aria-label="Close navigation"
              className="absolute right-2 top-2.5 rounded-md p-1.5 text-ink-muted hover:bg-line/60 hover:text-ink"
            >
              <X aria-hidden className="size-4" />
            </button>
            <Sidebar onNavigate={close} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b border-line bg-canvas px-2 md:hidden">
          <button
            ref={menuButton}
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open navigation"
            aria-expanded={drawerOpen}
            aria-controls="mobile-nav"
            className="rounded-md p-2 text-ink-muted hover:bg-subtle hover:text-ink"
          >
            <Menu aria-hidden className="size-5" />
          </button>
          <span className="text-sm font-semibold tracking-tight">RAG Assistant</span>
        </header>
        <main className="flex min-h-0 flex-1 flex-col">{children}</main>
      </div>
    </div>
  );
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { session, logout } = useAuth();
  const { documents, status: documentsStatus } = useDocuments();
  const onDocuments = pathname === "/documents";

  return (
    <>
      <div className="flex h-12 shrink-0 items-center px-4">
        <Link href="/" onClick={onNavigate} className="text-sm font-semibold tracking-tight">
          RAG Assistant
        </Link>
      </div>

      <nav aria-label="Main" className="space-y-px px-2">
        <Link
          href="/"
          onClick={onNavigate}
          aria-current={pathname === "/" ? "page" : undefined}
          className={`flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-colors ${
            pathname === "/" ? "bg-line/70 font-medium text-ink" : "text-ink-muted hover:bg-line/40 hover:text-ink"
          }`}
        >
          <Plus aria-hidden className="size-4" />
          New conversation
        </Link>
        <Link
          href="/documents"
          onClick={onNavigate}
          aria-current={onDocuments ? "page" : undefined}
          className={`flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-colors ${
            onDocuments ? "bg-line/70 font-medium text-ink" : "text-ink-muted hover:bg-line/40 hover:text-ink"
          }`}
        >
          <FileText aria-hidden className="size-4" />
          <span className="flex-1">Documents</span>
          {documentsStatus === "ready" && (
            <span className="text-xs tabular-nums text-ink-faint">{documents.length}</span>
          )}
        </Link>
      </nav>

      <HistoryPanel onNavigate={onNavigate} />

      <div className="flex items-center gap-2 border-t border-line px-3 py-3">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm text-ink" title={session?.email}>
            {session?.email}
          </p>
          {session?.role && session.role !== "USER" && (
            <p className="text-xs text-ink-faint">{session.role.toLowerCase()}</p>
          )}
        </div>
        <button
          type="button"
          onClick={logout}
          className="flex shrink-0 items-center gap-1.5 rounded-md px-2 py-1.5 text-sm text-ink-muted hover:bg-line/50 hover:text-ink"
        >
          <LogOut aria-hidden className="size-4" />
          Sign out
        </button>
      </div>
    </>
  );
}
