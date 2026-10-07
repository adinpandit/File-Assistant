from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.core.embeddings import embed_query
from app.core.vectorstore.qdrant_store import QdrantVectorStore
from app.core.llm import generate_answer
from app.services.retrieval import build_citations,build_context
from app.core.auth import get_current_user
from app.services.conv_store import ConversationStore


router = APIRouter(
    prefix="/query",
    tags=["Query"],
)

conversation_store = ConversationStore()

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

    document_id: str | None = None
    conversation_id: str | None = None

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
    answer: str
    citations: list[CitationResponse]
    sources: list[Source]


@router.post("",response_model=QueryResponse,)
def query_documents(request: QueryRequest,current_user=Depends(get_current_user),):

    user_id = str(current_user["user_id"])

    if request.conversation_id is not None:

        conversation = conversation_store.get_conversation(conversation_id=request.conversation_id,user_id=user_id,)

        if conversation is None:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

    conversation_history = ""

    if request.conversation_id is not None:

        messages = conversation_store.get_recent_messages(conversation_id=request.conversation_id,user_id=user_id,limit=10,)
        
        history_lines = []

        for message in messages:

            role = message.role.capitalize()

            history_lines.append(f"{role}: {message.content}")

        conversation_history = "\n".join(history_lines)

    try:
        query_embedding = embed_query(request.query)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    try:

        vector_store = QdrantVectorStore()

        results = vector_store.search(query_embedding=query_embedding,limit=request.limit,document_id=request.document_id,user_id=user_id,)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {exc}",
        ) from exc

    if not results:

        answer = (
            "I could not find relevant "
            "information in the provided "
            "documents."
        )

        citation_response = []

        sources = []

    else:

        context = build_context(
            results
        )

        try:

            answer = generate_answer(
                query=request.query,
                context=context,
                conversation_history=conversation_history,
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
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

        sources = []

        for result in results:

            payload = (result.get("payload") or {})

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

    if request.conversation_id is not None:
        conversation_store.add_message(conversation_id=request.conversation_id,user_id=user_id,role="user",content=request.query,)

        conversation_store.add_message(conversation_id=request.conversation_id,user_id=user_id,role="assistant",content=answer,)

    return QueryResponse(
        query=request.query,
        answer=answer,
        citations=citation_response,
        sources=sources,
    )