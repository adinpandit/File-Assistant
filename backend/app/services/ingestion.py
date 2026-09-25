from dataclasses import dataclass
from pathlib import Path
from app.core.chunking import chunk , chunk_pages
from app.core.embeddings import embed_documents
from app.core.parsing import parse_document
from app.core.vectorstore.qdrant_store import QdrantVectorStore

@dataclass
class IngestionResult:
    document_id : str
    page_count : int
    chunk_count : int

def ingest_document(file_path:str|Path , document_id:str , user_id:str|None=None , vector_store:QdrantVectorStore|None=None,)->IngestionResult:
    path = Path(file_path)

    if not path.exists():
        raise FileExistsError(f"Document not found : {path}")

    pages = parse_document(path)

    chunks:list[chunk]=chunk_pages(pages=pages , document_id=document_id , user_id=user_id)

    texts = [
        chunk.text
        for chunk in chunks
    ]

    embeddings = embed_documents(texts)

    if vector_store is None:
        vector_store = QdrantVectorStore()

    vector_store.upsert_chunks(chunks=chunks , embeddings=embeddings)

    return IngestionResult(
        document_id=document_id,
        page_count=len(pages),
        chunk_count=len(chunks),
    )

