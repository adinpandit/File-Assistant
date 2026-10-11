// Run with `npm test` (Node's built-in test runner; Node strips the types).
import assert from "node:assert/strict";
import { afterEach, beforeEach, describe, it } from "node:test";
import { api, ApiError, configureAuth, UPLOAD_NO_RESPONSE_MESSAGE } from "./client.ts";

// Response captured from POST /api/upload for aw_pgsql_book.pdf.
const UPLOAD_RESPONSE = {
  document_id: "a639abce-0b38-4469-ad90-3fec27445060",
  filename: "aw_pgsql_book.pdf",
  file_type: "pdf",
  page_count: 444,
  chunk_count: 2774,
  upload_time: "2026-10-11T11:57:00.005063+00:00",
  status: "ingested",
};

interface FakeReply {
  status: number;
  body: string;
}

let xhrReply: FakeReply;
const sentRequests: FakeXhr[] = [];
const lastXhr = () => sentRequests.at(-1);

class FakeXhr {
  status = 0;
  responseText = "";
  method = "";
  url = "";
  headers: Record<string, string> = {};
  sent: unknown = null;
  upload: { onprogress: ((event: { lengthComputable: boolean; loaded: number; total: number }) => void) | null } = {
    onprogress: null,
  };
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;

  open(method: string, url: string) {
    this.method = method;
    this.url = url;
  }

  setRequestHeader(name: string, value: string) {
    this.headers[name] = value;
  }

  send(body: unknown) {
    this.sent = body;
    sentRequests.push(this);
    queueMicrotask(() => {
      this.upload.onprogress?.({ lengthComputable: true, loaded: 100, total: 100 });
      this.status = xhrReply.status;
      this.responseText = xhrReply.body;
      this.onload?.();
    });
  }
}

const realXhr = (globalThis as { XMLHttpRequest?: unknown }).XMLHttpRequest;
const realFetch = globalThis.fetch;
let authFailures = 0;

function pdf(): File {
  return new File([new Uint8Array([0x25, 0x50, 0x44, 0x46])], "aw_pgsql_book.pdf", { type: "application/pdf" });
}

beforeEach(() => {
  (globalThis as { XMLHttpRequest?: unknown }).XMLHttpRequest = FakeXhr;
  authFailures = 0;
  configureAuth(
    () => "test-token",
    () => {
      authFailures += 1;
    },
  );
});

afterEach(() => {
  (globalThis as { XMLHttpRequest?: unknown }).XMLHttpRequest = realXhr;
  globalThis.fetch = realFetch;
  sentRequests.length = 0;
});

describe("api.documents.upload", () => {
  it("resolves with the backend's upload response and sends the file with the bearer token", async () => {
    xhrReply = { status: 200, body: JSON.stringify(UPLOAD_RESPONSE) };
    const progress: number[] = [];

    const result = await api.documents.upload(pdf(), ({ loaded, total }) => progress.push(loaded / total));

    assert.deepEqual(result, UPLOAD_RESPONSE);
    assert.equal(lastXhr()?.method, "POST");
    assert.equal(lastXhr()?.url, "/api/upload");
    assert.equal(lastXhr()?.headers.Authorization, "Bearer test-token");
    assert.ok(lastXhr()?.sent instanceof FormData);
    assert.equal(((lastXhr()?.sent as FormData).get("file") as File).name, "aw_pgsql_book.pdf");
    assert.deepEqual(progress, [1]);
  });

  it("reports a proxy-level failure (plain-text 500) as a possibly still-processing upload", async () => {
    // What the Next.js rewrite proxy returns when the backend times out or drops.
    xhrReply = { status: 500, body: "Internal Server Error" };

    await assert.rejects(api.documents.upload(pdf()), (error: unknown) => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.status, 500);
      assert.equal(error.fromBackend, false);
      assert.equal(error.message, UPLOAD_NO_RESPONSE_MESSAGE);
      return true;
    });
  });

  it("shows the backend's own error detail for ingestion failures", async () => {
    xhrReply = {
      status: 500,
      body: JSON.stringify({ detail: "Document ingestion failed. The file could not be processed." }),
    };

    await assert.rejects(api.documents.upload(pdf()), (error: unknown) => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.fromBackend, true);
      assert.equal(error.message, "Document ingestion failed. The file could not be processed.");
      return true;
    });
  });

  it("shows validation errors such as the size limit", async () => {
    xhrReply = { status: 413, body: JSON.stringify({ detail: "File size exceeds the 50 MB limit" }) };

    await assert.rejects(api.documents.upload(pdf()), { message: "File size exceeds the 50 MB limit" });
  });

  it("signals an expired session on 401", async () => {
    xhrReply = { status: 401, body: JSON.stringify({ detail: "Invalid or expired token" }) };

    await assert.rejects(api.documents.upload(pdf()), { status: 401 });
    assert.equal(authFailures, 1);
  });
});

describe("api.documents.list", () => {
  it("returns the documents after an upload", async () => {
    const record = { ...UPLOAD_RESPONSE, user_id: "00000000-0000-0000-0000-000000000001" };
    let requested: { url: string; auth: string | undefined } | null = null;
    globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
      requested = { url: String(input), auth: (init?.headers as Record<string, string>).Authorization };
      return new Response(JSON.stringify({ documents: [record] }), { status: 200 });
    }) as typeof fetch;

    const response = await api.documents.list();

    assert.deepEqual(response.documents, [record]);
    assert.deepEqual(requested, { url: "/api/documents", auth: "Bearer test-token" });
  });

  it("distinguishes a missing backend response from a backend error", async () => {
    globalThis.fetch = (async () => new Response("Internal Server Error", { status: 500 })) as typeof fetch;

    await assert.rejects(api.documents.list(), (error: unknown) => {
      assert.ok(error instanceof ApiError);
      assert.equal(error.fromBackend, false);
      assert.match(error.message, /^No response from the backend \(HTTP 500\)/);
      return true;
    });
  });
});
