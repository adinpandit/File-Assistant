from pathlib import Path
from fastapi import APIRouter,Depends,HTTPException
from app.config import settings
from app.core.auth import get_current_user
from app.core.vectorstore.qdrant_store import QdrantVectorStore
from app.models.document import DocumentDeleteResponse,DocumentListResponse,DocumentResponse
from app.services.doc_store import DocumentStore
from uuid import UUID


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

document_store = DocumentStore()
vector_store = QdrantVectorStore()

def validate_document_id(document_id: str) -> str:
    try:
        return str(UUID(document_id))

    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid document ID",
        ) from exc
    
@router.get("",response_model=DocumentListResponse,)
def list_documents(current_user=Depends(get_current_user),):
    try:
        documents = document_store.list_documents(user_id=str(current_user["user_id"]),)

        return DocumentListResponse(documents=documents,)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve documents",
        ) from exc

@router.get("/{document_id}",response_model=DocumentResponse,)
def get_document(document_id: str,current_user=Depends(get_current_user),):
    document_id = validate_document_id(document_id)
    user_id = str(current_user["user_id"])

    try:
        document = document_store.get_document(document_id=document_id,user_id=str(current_user["user_id"]),)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve document",
        ) from exc

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document

@router.delete("/{document_id}",response_model=DocumentDeleteResponse,)
def delete_document(document_id: str,current_user=Depends(get_current_user),):
    document_id = validate_document_id(document_id)
    user_id = str(current_user["user_id"])

    try:
        document = document_store.get_document(document_id=document_id,user_id=str(current_user["user_id"]),)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to verify document ownership",
        ) from exc
    
    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    try:
        vector_store.delete_document(document_id=document_id,user_id=str(current_user["user_id"]),)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to delete document vectors"
            ),
        ) from exc

    try:
        deleted = document_store.delete_document(document_id=document_id,user_id=str(current_user["user_id"]),)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document metadata",
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    upload_dir = Path(settings.upload_dir)

    file_path = upload_dir / (f"{document_id}_{document.filename}")

    try:
        if file_path.exists():
            file_path.unlink()

    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Document was deleted from storage, "
                "but its uploaded file could not be removed"
            ),
        ) from exc
    
    return DocumentDeleteResponse(
        document_id=document_id,
        status="deleted",
    )