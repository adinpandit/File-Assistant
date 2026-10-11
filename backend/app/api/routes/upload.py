import logging
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter , File , HTTPException , UploadFile , Depends
from fastapi.concurrency import run_in_threadpool
from app.services.ingestion import ingest_document
from app.config import settings
from app.services.doc_store import DocumentStore
from app.core.auth import get_current_user
from app.core.vectorstore.qdrant_store import QdrantVectorStore

logger = logging.getLogger(__name__)

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

    safe_filename = file.filename.replace("\\", "/").split("/")[-1].strip()

    if not safe_filename or safe_filename in {".", ".."}:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename",
        )

    extension = Path(safe_filename).suffix.lower()

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

    file_path = upload_dir / f"{document_id}_{safe_filename}"

    max_size = (settings.max_file_size_mb * 1024 * 1024)

    user_id = str(current_user["user_id"])

    # Set once ingestion has written vectors to Qdrant, so a later failure
    # (e.g. saving metadata to PostgreSQL) can remove them instead of
    # leaving vectors with no document record.
    vectors_written = False

    contents = b""

    try:
        contents = await file.read(max_size + 1)

        if len(contents) > max_size:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File size exceeds the "
                    f"{settings.max_file_size_mb} MB limit"
                ),
            )

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty",
            )
        
        file_path.write_bytes(contents)

        # Parsing and embedding are CPU-bound and can take minutes for large
        # PDFs. Running them in the threadpool keeps the event loop free, so
        # other requests (document list, history, health) are not blocked.
        result = await run_in_threadpool(
            ingest_document,
            file_path=file_path,
            document_id=document_id,
            user_id=user_id,
        )

        vectors_written = True

        document = document_store.create_document(
            document_id=document_id,
            user_id=user_id,
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
        # Log the cause server-side; the client gets a generic message so
        # internal paths, hostnames and driver errors are not exposed.
        logger.exception(
            "Upload failed for document %s (user %s, file type %s, %d bytes)",
            document_id,
            user_id,
            extension,
            len(contents),
        )

        if file_path.exists():
            file_path.unlink()

        if vectors_written:
            try:
                QdrantVectorStore().delete_document(document_id=document_id,user_id=user_id,)
            except Exception:
                logger.exception(
                    "Could not remove vectors for failed upload %s",
                    document_id,
                )

        raise HTTPException(
            status_code=500,
            detail = "Document ingestion failed. The file could not be processed.",
        ) from e

    finally:
        await file.close()

    return{
        "document_id": document.document_id,
        "filename": document.filename,
        "file_type": document.file_type,
        "page_count": document.page_count,
        "chunk_count": document.chunk_count,
        "upload_time": document.upload_time,
        "status": "ingested",
    }
