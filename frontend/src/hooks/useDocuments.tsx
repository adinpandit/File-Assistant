"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError } from "@/api/client";
import type { DocumentRecord } from "@/types";

// Mirrors allowed_extensions in backend/app/api/routes/upload.py.
export const SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md"] as const;

export function fileExtension(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot === -1 ? "" : name.slice(dot).toLowerCase();
}

export interface UploadItem {
  id: string;
  name: string;
  size: number;
  // "uploading": bytes in flight; "processing": server is parsing and embedding.
  status: "queued" | "uploading" | "processing" | "done" | "failed";
  progress: number; // 0..1, upload bytes only
  error?: string;
}

type LoadStatus = "loading" | "ready" | "error";

interface DocumentsContextValue {
  documents: DocumentRecord[];
  status: LoadStatus;
  error: string | null;
  refresh: () => Promise<void>;
  remove: (documentId: string) => Promise<void>;
  uploads: UploadItem[];
  enqueueUploads: (files: File[]) => void;
  dismissUpload: (id: string) => void;
  findDocument: (documentId: string) => DocumentRecord | undefined;
}

const DocumentsContext = createContext<DocumentsContextValue | null>(null);

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

export function DocumentsProvider({ children }: { children: React.ReactNode }) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [status, setStatus] = useState<LoadStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const queue = useRef<{ id: string; file: File }[]>([]);
  const draining = useRef(false);

  const refresh = useCallback(
    () =>
      api.documents.list().then(
        (response) => {
          setDocuments(response.documents);
          setStatus("ready");
          setError(null);
        },
        (cause: unknown) => {
          setStatus((previous) => (previous === "ready" ? previous : "error"));
          setError(errorMessage(cause, "Could not load documents."));
        },
      ),
    [],
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const remove = useCallback(async (documentId: string) => {
    await api.documents.remove(documentId);
    setDocuments((current) => current.filter((doc) => doc.document_id !== documentId));
  }, []);

  const updateUpload = useCallback((id: string, patch: Partial<UploadItem>) => {
    setUploads((current) => current.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }, []);

  // Uploads run one at a time: each upload is parsed and embedded synchronously
  // by the backend, so parallel requests would only compete for the same worker.
  const drain = useCallback(async () => {
    if (draining.current) return;
    draining.current = true;
    try {
      let next = queue.current.shift();
      while (next) {
        const { id, file } = next;
        updateUpload(id, { status: "uploading", progress: 0 });
        try {
          const uploaded = await api.documents.upload(file, ({ loaded, total }) => {
            const progress = total > 0 ? loaded / total : 0;
            updateUpload(id, progress >= 1 ? { status: "processing", progress: 1 } : { progress });
          });
          updateUpload(id, { status: "done", progress: 1 });
          setDocuments((current) => [
            {
              document_id: uploaded.document_id,
              user_id: "",
              filename: uploaded.filename,
              file_type: uploaded.file_type,
              upload_time: uploaded.upload_time,
              page_count: uploaded.page_count,
              chunk_count: uploaded.chunk_count,
            },
            ...current.filter((doc) => doc.document_id !== uploaded.document_id),
          ]);
        } catch (cause) {
          updateUpload(id, { status: "failed", error: errorMessage(cause, "Upload failed.") });
        }
        next = queue.current.shift();
      }
    } finally {
      draining.current = false;
    }
    // Reconcile with the server's view (user_id and ordering).
    void refresh();
  }, [refresh, updateUpload]);

  const enqueueUploads = useCallback(
    (files: File[]) => {
      const items: UploadItem[] = [];
      for (const file of files) {
        const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const extension = fileExtension(file.name);
        if (!(SUPPORTED_EXTENSIONS as readonly string[]).includes(extension)) {
          items.push({
            id,
            name: file.name,
            size: file.size,
            status: "failed",
            progress: 0,
            error: `Unsupported file type${extension ? ` ${extension}` : ""}. Use PDF, TXT, or Markdown.`,
          });
          continue;
        }
        if (file.size === 0) {
          items.push({ id, name: file.name, size: 0, status: "failed", progress: 0, error: "The file is empty." });
          continue;
        }
        items.push({ id, name: file.name, size: file.size, status: "queued", progress: 0 });
        queue.current.push({ id, file });
      }
      setUploads((current) => [...items, ...current]);
      void drain();
    },
    [drain],
  );

  const dismissUpload = useCallback((id: string) => {
    setUploads((current) => current.filter((item) => item.id !== id));
  }, []);

  const findDocument = useCallback(
    (documentId: string) => documents.find((doc) => doc.document_id === documentId),
    [documents],
  );

  const value = useMemo<DocumentsContextValue>(
    () => ({ documents, status, error, refresh, remove, uploads, enqueueUploads, dismissUpload, findDocument }),
    [documents, status, error, refresh, remove, uploads, enqueueUploads, dismissUpload, findDocument],
  );

  return <DocumentsContext.Provider value={value}>{children}</DocumentsContext.Provider>;
}

export function useDocuments(): DocumentsContextValue {
  const context = useContext(DocumentsContext);
  if (!context) throw new Error("useDocuments must be used inside DocumentsProvider");
  return context;
}
