from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter , File , HTTPException , UploadFile , Depends
from app.services.ingestion import ingest_document
from app.config import settings
from app.services.doc_store import DocumentStore
from app.core.auth import get_current_user

router = APIRouter(
    prefix = "/upload",
    tags = ["Upload"],
)

upload_dir = Path("uploads")

document_store = DocumentStore()

allowed_extensions = {".pdf" , ".txt" , ".md"}

@router.post("")
async def upload_document(file: UploadFile = File(...),current_user=Depends(get_current_user),):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail = "Filename is required",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {extension}. "
                "Supported types : .pdf , .txt , .md"
            ),
        )
    upload_dir = Path(settings.upload_dir)

    upload_dir.mkdir(parents=True , exist_ok=True)

    document_id = str(uuid4())

    safe_filename = Path(file.filename).name

    file_path = upload_dir/(f"{document_id}_{safe_filename}")

    try:
        contents = await file.read()

        max_size = (
            settings.max_file_size_mb
            * 1024
            * 1024
        )

        if len(contents) > max_size:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File size exceeds the "
                    f"{settings.max_file_size_mb} MB limit"
                ),
            )
        
        file_path.write_bytes(contents)

        result = ingest_document(
            file_path=file_path,
            document_id=document_id,
            user_id=str(
                current_user["user_id"]
            ),
        )

        document = document_store.create_document(
            document_id=document_id,
            user_id=str(
                current_user["user_id"]
            ),
            filename=safe_filename,
            file_type=extension.lstrip("."),
            page_count=result.page_count,
            chunk_count=result.chunk_count,
        )
        
    except HTTPException:
        if file_path.exists():
            file_path.unlink()
        raise

    except Exception as e:
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail = f"Document ingestion failed: {e}",
        ) from e

    return{
        "document_id": document.document_id,
        "filename": document.filename,
        "file_type": document.file_type,
        "page_count": document.page_count,
        "chunk_count": document.chunk_count,
        "upload_time": document.upload_time,
        "status": "ingested",
    }
