// Types mirror the FastAPI response models in backend/app.

// models/auth.py
export interface UserResponse {
  user_id: string;
  email: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// models/document.py
export interface DocumentRecord {
  document_id: string;
  user_id: string;
  filename: string;
  file_type: string;
  upload_time: string;
  page_count: number;
  chunk_count: number;
}

export interface DocumentListResponse {
  documents: DocumentRecord[];
}

export interface DocumentDeleteResponse {
  document_id: string;
  status: string;
}

// api/routes/upload.py (untyped dict response)
export interface UploadResponse {
  document_id: string;
  filename: string;
  file_type: string;
  page_count: number;
  chunk_count: number;
  upload_time: string;
  status: string;
}

// api/routes/query.py
export interface QueryRequest {
  query: string;
  limit?: number;
  document_id?: string | null;
  conversation_id?: string | null;
}

export interface Citation {
  citation_id: string;
  document_id: string;
  chunk_id: string;
  page_number: number;
  chunk_index: number;
}

export interface Source {
  chunk_id: string;
  document_id: string;
  page_number: number;
  chunk_index: number;
  text: string;
  score: number;
}

export interface QueryResponse {
  query: string;
  answer: string;
  citations: Citation[];
  sources: Source[];
}

// models/history.py
export interface Conversation {
  conversation_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationListResponse {
  conversations: Conversation[];
}

export interface ConversationDeleteResponse {
  conversation_id: string;
  status: string;
}

export interface StoredMessage {
  message_id: string;
  conversation_id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface MessageListResponse {
  messages: StoredMessage[];
}

// Client-side chat state.
export type ChatMessage =
  | {
      id: string;
      role: "user";
      content: string;
      status: "sent" | "pending" | "failed";
      error?: string;
      documentId?: string | null;
    }
  | {
      id: string;
      role: "assistant";
      content: string;
      // Present only for answers produced in this session. The history API
      // stores message text only, so reloaded answers have no citations.
      citations?: Citation[];
      sources?: Source[];
    };
