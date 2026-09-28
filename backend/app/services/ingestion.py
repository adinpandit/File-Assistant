from dataclasses import dataclass
from pathlib import Path
#import logging
from app.core.chunking import chunk , chunk_pages
from app.core.embeddings import embed_documents
from app.core.parsing import parse_document
from app.core.vectorstore.qdrant_store import QdrantVectorStore

#logger = logging.getLoggerClass(__name__)

@dataclass
class IngestionResult:
    document_id : str
    page_count : int
    chunk_count : int

def ingest_document(file_path:str|Path , document_id:str , user_id:str|None=None , vector_store:QdrantVectorStore|None=None,)->IngestionResult:
    path = Path(file_path)

    if not path.exists():
        raise FileExistsError(f"Document not found : {path}")

    #logger.info(
        #"Starting ingestion for document %s",
        document_id,
    #)

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

    #logger.info(
        #"Finished ingestion for document %s: %d pages, %d chunks",
        #document_id,
        #result.page_count,
        #result.chunk_count,
    #)

    #return result

