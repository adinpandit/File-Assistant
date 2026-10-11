import type {
  Conversation,
  ConversationDeleteResponse,
  ConversationListResponse,
  DocumentDeleteResponse,
  DocumentListResponse,
  MessageListResponse,
  QueryRequest,
  QueryResponse,
  TokenResponse,
  UploadResponse,
  UserResponse,
} from "@/types";

// Requests go to same-origin /api/* and are proxied to NEXT_PUBLIC_API_BASE_URL
// by next.config.ts (the backend does not allow cross-origin requests).
const API_PREFIX = "/api";

export class ApiError extends Error {
  readonly status: number;
  /**
   * False when the response did not come from FastAPI (no JSON body), e.g. the
   * Next.js proxy answering with a plain-text 500 because the backend was
   * unreachable or did not respond within the proxy timeout.
   */
  readonly fromBackend: boolean;

  constructor(message: string, status: number, fromBackend = true) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fromBackend = fromBackend;
  }

  /** True when the backend rejected or did not receive credentials. */
  get isAuthError(): boolean {
    // core/auth.py: 401 for invalid/expired tokens, 403 "Not authenticated"
    // when the Authorization header is missing.
    return this.status === 401 || this.status === 403;
  }
}

type TokenProvider = () => string | null;
type AuthFailureHandler = () => void;

let getToken: TokenProvider = () => null;
let onAuthFailure: AuthFailureHandler = () => {};

export function configureAuth(provider: TokenProvider, handler: AuthFailureHandler): void {
  getToken = provider;
  onAuthFailure = handler;
}

interface FastApiValidationIssue {
  msg?: string;
  loc?: (string | number)[];
}

function messageFromBody(body: unknown, status: number): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    // FastAPI 422 validation errors: [{ loc, msg, type }]
    if (Array.isArray(detail)) {
      const messages = (detail as FastApiValidationIssue[])
        .map((issue) => issue.msg?.replace(/^Value error, /, ""))
        .filter((msg): msg is string => Boolean(msg));
      if (messages.length > 0) return messages.join(". ");
    }
  }
  if (status === 404) return "The requested resource was not found.";
  if (status >= 500 && body === null) {
    return `No response from the backend (HTTP ${status}). It may be offline, or the request took too long.`;
  }
  if (status >= 500) return "The server could not complete the request. Check that the backend is running.";
  return `Request failed with status ${status}.`;
}

function parseBody(text: string): unknown {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function handleFailure(status: number, body: unknown, authenticated: boolean): never {
  const error = new ApiError(messageFromBody(body, status), status, body !== null);
  if (authenticated && error.isAuthError) onAuthFailure();
  throw error;
}

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE";
  body?: unknown;
  auth?: boolean;
  signal?: AbortSignal;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, signal } = options;
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_PREFIX}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === "AbortError") throw cause;
    throw new ApiError("Could not reach the server. Check your connection and that the backend is running.", 0);
  }

  const parsed = parseBody(await response.text());
  if (!response.ok) handleFailure(response.status, parsed, auth);
  return parsed as T;
}

export interface UploadProgress {
  loaded: number;
  total: number;
}

// The backend parses and embeds the file before it responds, so a proxy-level
// failure can happen after the file was received and while (or after) it is
// being stored. Say so, rather than implying the upload never happened.
export const UPLOAD_NO_RESPONSE_MESSAGE =
  "The server didn't respond to this upload. Large files can take several minutes to process, " +
  "so the document may still appear in your library — check before uploading it again.";

// fetch() cannot report upload progress, so uploads use XMLHttpRequest.
function uploadFile(
  file: File,
  onProgress?: (progress: UploadProgress) => void,
): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_PREFIX}/upload`);
    xhr.setRequestHeader("Accept", "application/json");
    const token = getToken();
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.({ loaded: event.loaded, total: event.total });
    };
    xhr.onerror = () =>
      reject(new ApiError("Could not reach the server. Check your connection and that the backend is running.", 0));
    xhr.onload = () => {
      const parsed = parseBody(xhr.responseText);
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(parsed as UploadResponse);
        return;
      }
      if (xhr.status >= 500 && parsed === null) {
        reject(new ApiError(UPLOAD_NO_RESPONSE_MESSAGE, xhr.status, false));
        return;
      }
      try {
        handleFailure(xhr.status, parsed, true);
      } catch (error) {
        reject(error);
      }
    };

    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}

export const api = {
  auth: {
    register: (email: string, password: string) =>
      request<UserResponse>("/auth/register", { method: "POST", body: { email, password }, auth: false }),
    login: (email: string, password: string) =>
      request<TokenResponse>("/auth/login", { method: "POST", body: { email, password }, auth: false }),
  },
  documents: {
    list: () => request<DocumentListResponse>("/documents"),
    upload: uploadFile,
    remove: (documentId: string) =>
      request<DocumentDeleteResponse>(`/documents/${encodeURIComponent(documentId)}`, { method: "DELETE" }),
  },
  query: (payload: QueryRequest, signal?: AbortSignal) =>
    request<QueryResponse>("/query", { method: "POST", body: payload, signal }),
  conversations: {
    list: () => request<ConversationListResponse>("/history/conversations"),
    create: (title: string) =>
      request<Conversation>("/history/conversations", { method: "POST", body: { title } }),
    get: (conversationId: string) =>
      request<Conversation>(`/history/conversations/${encodeURIComponent(conversationId)}`),
    messages: (conversationId: string) =>
      request<MessageListResponse>(`/history/conversations/${encodeURIComponent(conversationId)}/messages`),
    remove: (conversationId: string) =>
      request<ConversationDeleteResponse>(`/history/conversations/${encodeURIComponent(conversationId)}`, {
        method: "DELETE",
      }),
  },
};
