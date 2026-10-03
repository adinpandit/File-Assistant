from pathlib import Path
from fastapi import APIRouter,Depends,HTTPException
from app.config import settings
from app.core.auth import get_current_user
from app.core.vectorstore.qdrant_store import QdrantVectorStore
from app.models.document import DocumentDeleteResponse,DocumentListResponse,DocumentResponse
from app.services.doc_store import DocumentStore


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

document_store = DocumentStore()
vector_store = QdrantVectorStore()


@router.get("",response_model=DocumentListResponse,)
def list_documents(current_user=Depends(get_current_user),):
    documents = document_store.list_documents(user_id=str(current_user["user_id"]),)

    return DocumentListResponse(documents=documents,)

@router.get("/{document_id}",response_model=DocumentResponse,)
def get_document(document_id: str,current_user=Depends(get_current_user),):
    document = document_store.get_document(document_id=document_id,user_id=str(current_user["user_id"]),)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document


@router.delete("/{document_id}",response_model=DocumentDeleteResponse,)
def delete_document(document_id: str,current_user=Depends(get_current_user),):
    document = document_store.get_document(document_id=document_id,user_id=str(current_user["user_id"]),)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    try:
        vector_store.delete_document(document_id,)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to delete document vectors"
            ),
        ) from exc

    deleted = document_store.delete_document(document_id=document_id,user_id=str(current_user["user_id"]),)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    upload_dir = Path(settings.upload_dir)

    file_path = upload_dir / (f"{document_id}_{document.filename}")

    if file_path.exists():
        file_path.unlink()

    return DocumentDeleteResponse(
        document_id=document_id,
        status="deleted",
    )