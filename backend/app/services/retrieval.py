from dataclasses import dataclass
from typing import Any


@dataclass
class Citation:
    citation_id: str
    document_id: str
    chunk_id: str
    page_number: int
    chunk_index: int


def build_context(results: list[dict[str, Any]],) -> str:
    """
    Build structured context for the LLM.

    Each retrieved chunk receives a stable citation ID.
    """

    if not results:
        return ""

    context_parts: list[str] = []

    for index, result in enumerate(results,start=1,):
        payload = result.get("payload") or {}

        text = str(payload.get("text","",))

        if not text.strip():
            continue

        document_id = str(payload.get("document_id","",))

        chunk_id = str(payload.get("chunk_id",result.get("id","",),))

        page_number = int(payload.get("page_number",0,))

        chunk_index = int(payload.get("chunk_index",0,))

        context_parts.append(
            f"[S{index}]\n"
            f"Document ID: {document_id}\n"
            f"Chunk ID: {chunk_id}\n"
            f"Page: {page_number}\n"
            f"Content:\n{text}"
        )

    return "\n\n".join(context_parts)


def build_citations(results: list[dict[str, Any]],) -> list[Citation]:
    """
    Convert retrieved chunks into structured citations.
    """

    citations: list[Citation] = []

    for index, result in enumerate(results,start=1,):
        payload = result.get("payload") or {}

        document_id = str(payload.get("document_id","",))

        chunk_id = str(payload.get("chunk_id",result.get("id","",),))

        page_number = int(payload.get("page_number",0,))

        chunk_index = int(payload.get("chunk_index",0,))

        citations.append(
            Citation(
                citation_id=f"S{index}",
                document_id=document_id,
                chunk_id=chunk_id,
                page_number=page_number,
                chunk_index=chunk_index,
            )
        )

    return citations