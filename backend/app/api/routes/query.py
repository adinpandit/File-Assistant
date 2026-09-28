from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.embeddings import embed_query
from app.core.vectorstore.qdrant_store import QdrantVectorStore
from app.core.llm import generate_answer
from app.services.retrieval import (build_citations,build_context,)

router = APIRouter(
    prefix="/query",
    tags=["Query"],
)


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )

class CitationResponse(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    page_number: int
    chunk_index: int

class Source(BaseModel):
    chunk_id: str
    document_id: str
    page_number: int
    chunk_index: int
    text: str
    score: float

class QueryResponse(BaseModel):
    query: str
    answer:str
    citations:list[CitationResponse]
    sources: list[Source]


@router.post("",response_model=QueryResponse,)
def query_documents(request: QueryRequest,):
    """
    Embed the user query and retrieve
    the most relevant document chunks.
    """

    try:
        query_embedding = embed_query(
            request.query
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    try:
        vector_store = QdrantVectorStore()

        results = vector_store.search(
            query_embedding=query_embedding,
            limit=request.limit,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {exc}",
        ) from exc

    if not results:
        return QueryResponse(
            query = request.query,
            answer = (
                "I could not find relevant "
                "information in the provided "
                "documents."
            ),
            citations = [],
            sources = [],
        )

    context = build_context(results)

    try:
        answer = generate_answer(query=request.query , context=context)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Answer generation failed: {exc}",
        ) from exc

    citations = build_citations(results)

    citation_response = [
        CitationResponse(
            citation_id=citation.citation_id,
            document_id=citation.document_id,
            chunk_id=citation.chunk_id,
            page_number=citation.page_number,
            chunk_index=citation.chunk_index,
        )
        for citation in citations
    ]

    sources: list[Source] = []

    for result in results:
        payload = result.get("payload") or {}

        sources.append(
            Source(
                chunk_id=str(payload.get("chunk_id",result["id"],)),

                document_id=str(payload.get("document_id","",)),

                page_number=int(payload.get("page_number",0,)),

                chunk_index=int(payload.get("chunk_index",0,)),

                text=str(payload.get("text","",)),

                score=float(result["score"]),
            )
        )

    return QueryResponse(
        query=request.query,
        answer=answer,
        citations=citation_response,
        sources=sources,
    )