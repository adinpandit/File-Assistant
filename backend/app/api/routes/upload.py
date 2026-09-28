from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter , File , HTTPException , UploadFile
from app.services.ingestion import ingest_document

router = APIRouter(
    prefix = "/upload",
    tags = ["Upload"],
)

upload_dir = Path("uploads")

allowed_extensions = {".pdf" , ".txt" , ".md"}

@router.post("")
async def upload_document(file: UploadFile = File(...),):

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

    upload_dir.mkdir(parents=True , exist_ok=True)

    document_id = str(uuid4())

    safe_filename = Path(file.filename).name

    file_path = upload_dir/(f"{document_id}_{safe_filename}")

    try:
        contents = await file.read()

        file_path.write_bytes(contents)

        result = ingest_document(
            file_path=file_path,
            document_id=document_id,
        )

    except Exception as e:
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail = f"Document ingestion failed: {e}",
        ) from e

    return{
        "document_id": result.document_id,
        "filename": safe_filename,
        "page_count": result.page_count,
        "chunk_count": result.chunk_count,
        "status": "ingested",
    }
