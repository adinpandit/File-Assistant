from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field , field_validator
from app.core.embeddings import embed_query
from app.core.vectorstore.qdrant_store import QdrantVectorStore
from app.core.llm import generate_answer,rewrite_query
from app.services.retrieval import build_citations,build_context
from app.core.auth import get_current_user
from app.services.conv_store import ConversationStore
from app.services.hybrid_retrieval import hybrid_search
from app.services.reranking import rerank_results
from app.services.doc_store import DocumentStore


router = APIRouter(
    prefix="/query",
    tags=["Query"],
)

conversation_store = ConversationStore()
document_store = DocumentStore()

class QueryRequest(BaseModel):

    query: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    document_id: str | None = None
    conversation_id: str | None = None

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "Query cannot be empty or whitespace-only"
            )

        return value

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

    if request.document_id is not None:

        try:
            document = document_store.get_document(document_id=request.document_id,user_id=user_id,)

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid document ID",
            ) from exc

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Unable to verify document access",
            ) from exc

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found",
            )

    if request.conversation_id is not None:

        try:
            conversation = conversation_store.get_conversation(conversation_id=request.conversation_id,user_id=user_id,)


        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid conversation ID",
            ) from exc

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Unable to verify conversation access",
            ) from exc

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

    conversation_history = ""

    if request.conversation_id is not None:

        try:
            messages = conversation_store.get_recent_messages(conversation_id=request.conversation_id,user_id=user_id,limit=10,)
        
            history_lines = []

            for message in messages:

                role = message.role.capitalize()

                history_lines.append(f"{role}: {message.content}")

            conversation_history = "\n".join(history_lines)

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid conversation history request",
            ) from exc

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Unable to load conversation history",
            ) from exc

    retrieval_query = request.query

    if request.conversation_id is not None:
        try:
            retrieval_query = rewrite_query(query=request.query,conversation_history=conversation_history,)

            if not (isinstance(retrieval_query, str) and retrieval_query.strip()):
                retrieval_query = request.query

        except Exception:
            retrieval_query = request.query

    try:
        query_embedding = embed_query(retrieval_query)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid query for embedding generation",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Query embedding failed: {exc}",
        ) from exc   

    try:

        vector_store = QdrantVectorStore()

        candidate_limit = min(max(request.limit*4,20),40,)

        dense_results = vector_store.search(query_embedding=query_embedding,limit=request.limit,document_id=request.document_id,user_id=user_id,)

        if hasattr(vector_store,"get_all_chunks"):
            corpus=vector_store.get_all_chunks(user_id=user_id , document_id=request.document_id,)

        else:
            corpus = dense_results

        hybrid_results = hybrid_search(query = retrieval_query , dense_results=dense_results , corpus=corpus , limit = candidate_limit,)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {exc}",
        ) from exc

    try:
        results = rerank_results(query=retrieval_query , results=hybrid_results , limit=request.limit,)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Result ranking failed",
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

        context = build_context(results)

        try:

            answer = generate_answer(
                query=request.query,
                context=context,
                conversation_history=conversation_history,
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid request for answer generation",
            ) from exc

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Answer generation failed: {exc}",
            ) from exc

        try:
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

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Citation generation failed",
            ) from exc


        sources = []

        for result in results:

            payload = (result.get("payload") or {})

            # Sources report vector similarity; rerank_score only orders results.
            source_score = result.get("score",0.0)

            sources.append(
                Source(
                    chunk_id=str(payload.get("chunk_id",result["id"],)),
                    document_id=str(payload.get("document_id","",)),
                    page_number=int(payload.get("page_number",0,)),
                    chunk_index=int(payload.get("chunk_index",0,)),
                    text=str(payload.get("text","",)),
                    score=float(source_score),
                )
            )

    if request.conversation_id is not None:

        try:
            conversation_store.add_message(conversation_id=request.conversation_id,user_id=user_id,role="user",content=request.query,)

            conversation_store.add_message(conversation_id=request.conversation_id,user_id=user_id,role="assistant",content=answer,)

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Unable to save conversation messages",
            ) from exc

    return QueryResponse(
        query=request.query,
        answer=answer,
        citations=citation_response,
        sources=sources,
    )