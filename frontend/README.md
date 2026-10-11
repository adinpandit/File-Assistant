# RAG Assistant — Frontend

Next.js (App Router) + TypeScript + Tailwind CSS client for the FastAPI backend in `../backend`.

## Setup

```bash
cd frontend
cp .env.example .env.local   # adjust NEXT_PUBLIC_API_BASE_URL if needed
npm install
npm run dev                  # http://localhost:3000
```

Start the backend separately (from `backend/`, e.g. `uvicorn app.main:app --port 8000`) along with Postgres and Qdrant (`docker compose up -d` at the repo root).

### Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Origin of the FastAPI backend, without `/api`. |

The backend does not enable CORS, so the browser never calls it directly. The Next.js server proxies `/api/*` to `NEXT_PUBLIC_API_BASE_URL` (see `next.config.ts`). The value is read when `next dev` starts or when `next build` runs, so restart or rebuild after changing it. No secrets belong in this file.

## Scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Development server |
| `npm run build` | Production build (`output: "standalone"`) |
| `npm run start` | Serve the production build |
| `npm run lint` | ESLint (`eslint-config-next`) |
| `npm run typecheck` | `tsc --noEmit` |

## Backend endpoints used

| Feature | Endpoint |
| --- | --- |
| Register / sign in | `POST /api/auth/register`, `POST /api/auth/login` (bearer JWT) |
| Documents | `GET /api/documents`, `POST /api/upload` (multipart `file`), `DELETE /api/documents/{id}` |
| Ask a question | `POST /api/query` (`query`, optional `document_id`, `conversation_id`) |
| History | `GET/POST /api/history/conversations`, `GET /api/history/conversations/{id}/messages`, `DELETE /api/history/conversations/{id}` |

## Structure

```
src/
  app/                 routes: /login, /register, / (new chat), /c/[id], /documents
  api/client.ts        the only place that talks to the backend
  hooks/               auth, documents, conversations and chat state (React context)
  components/          UI (AppShell, ChatWindow, MessageBubble, DocumentLibrary, …)
  lib/                 session token, citation parsing, formatting helpers
  types/               TypeScript mirrors of the backend response models
```

## Known backend limitations

- **Citations are not persisted.** `/api/query` returns `citations` and `sources`, but the history API stores message text only. Answers reopened from history show their `[S1]` markers without source details.
- **No "current user" endpoint.** The sidebar shows the email used to sign in and the role claim from the JWT.
- **Conversations cannot be renamed.** A new conversation is titled from its first question.
- **Upload size limit** is enforced by the backend (`MAX_FILE_SIZE_MB`, default 50); the UI reports the backend's error.
- **Tokens expire** after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60) and there is no refresh endpoint, so the user is asked to sign in again.
