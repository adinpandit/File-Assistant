from datetime import datetime
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    document_id: str
    user_id: str
    filename: str
    file_type: str
    upload_time: datetime
    page_count: int
    chunk_count: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class DocumentDeleteResponse(BaseModel):
    document_id: str
    status: str