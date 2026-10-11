import type { Citation, Source } from "@/types";

// The backend labels retrieved chunks [S1], [S2], … in the LLM context
// (services/retrieval.py) and the system prompt asks the model to cite them in
// that form. Citations in the response carry the same IDs.
const MARKER = /\[(S\d+(?:\s*,\s*S\d+)*)\]/g;

export const CITATION_HREF_PREFIX = "#cite-";

/**
 * Turn citation markers into markdown links (#cite-S1) so the renderer can
 * swap them for interactive chips. Fenced and inline code are left untouched.
 */
export function linkCitationMarkers(markdown: string): string {
  return markdown
    .split(/(```[\s\S]*?```|`[^`\n]*`)/g)
    .map((part, index) =>
      index % 2 === 1
        ? part
        : part.replace(MARKER, (_match, ids: string) =>
            ids
              .split(",")
              .map((id) => `[${id.trim()}](${CITATION_HREF_PREFIX}${id.trim()})`)
              .join(""),
          ),
    )
    .join("");
}

export function citedIds(markdown: string): Set<string> {
  const ids = new Set<string>();
  for (const match of markdown.matchAll(MARKER)) {
    for (const id of match[1].split(",")) ids.add(id.trim());
  }
  return ids;
}

export interface SourceEntry {
  id: string | null; // citation ID such as "S1", when the backend supplied one
  documentId: string;
  pageNumber: number;
  source: Source | null;
}

/** Pair each citation with its retrieved source (matched by chunk_id). */
export function buildSourceEntries(citations: Citation[] = [], sources: Source[] = []): SourceEntry[] {
  const byChunk = new Map(sources.map((source) => [source.chunk_id, source]));
  const used = new Set<string>();
  const entries: SourceEntry[] = citations.map((citation) => {
    const source = byChunk.get(citation.chunk_id) ?? null;
    if (source) used.add(source.chunk_id);
    return { id: citation.citation_id, documentId: citation.document_id, pageNumber: citation.page_number, source };
  });
  for (const source of sources) {
    if (!used.has(source.chunk_id)) {
      entries.push({ id: null, documentId: source.document_id, pageNumber: source.page_number, source });
    }
  }
  return entries;
}

export function citationLabel(id: string): string {
  return id.replace(/^S/, "");
}
