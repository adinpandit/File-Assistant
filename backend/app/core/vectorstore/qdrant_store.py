from typing import Any
from qdrant_client import QdrantClient
from qdrant_client.models import (Distance,PointStruct,VectorParams,FieldCondition,Filter,MatchValue)
from app.config import settings
from app.core.chunking import chunk

class QdrantVectorStore:
    def __init__(self , url:str|None=None , collection_name:str|None=None , vector_size:int|None=None,)->None:

        self.url = url or settings.qdrant_url
        self.collection_name = (collection_name or settings.qdrant_collection)
        self.vector_size = (vector_size or settings.embedding_dimension)
        self.client = QdrantClient(url=self.url)

    def collection_exists(self)->bool:
        collections = self.client.get_collections()

        return any(collection.name == self.collection_name 
                   for collection in collections.collections
        )

    def create_collection(self)->None:
        if self.collection_exists():
            return 

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size = self.vector_size , distance = Distance.COSINE),
        )

    def ensure_collection(self)->None:
        if not self.collection_exists():
            self.create_collection()

    def upsert_chunks(self , chunks:list[chunk] , embeddings:list[list[float]])->None:
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        if not chunks:
            return

        self.ensure_collection()

        points:list[PointStruct]=[]

        for chunk,embedding in zip(chunks , embeddings , strict=True):
            payload:dict[str,Any] = {
                "chunk_id":chunk.chunk_id,
                "document_id":chunk.document_id,
                "user_id":chunk.user_id,
                "chunk_index":chunk.chunk_index,
                "page_number":chunk.page_number,
                "text":chunk.text,
            }

            points.append(
                PointStruct(
                    id=chunk.chunk_id,
                    vector=embedding,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name = self.collection_name,
            points = points,
        )

    def search(self , query_embedding:list[float] , limit:int=5 , document_id:str|None=None , user_id:str|None=None,)->list[dict[str,Any]]:
        if not query_embedding:
            return []

        if limit  <= 0:
            raise ValueError("Limit must be greater than 0")

        self.ensure_collection()

        conditions:list[FieldCondition]=[]

        if document_id is not None:
            conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(
                        value=document_id,
                    ),
                )
            )

        if user_id is not None:
            conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(
                        value=user_id,
                    ),
                )
            )

        search_filter = None

        if conditions:
            search_filter = Filter(must=conditions,)

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            query_filter=search_filter,
            limit=limit,
        ).points

        return [
            {
                "id":result.id,
                "score":result.score,
                "payload":result.payload,
            }
            for result in results
        ]

    def get_all_chunks(self,user_id: str,document_id: str | None = None,page_size: int = 256,) -> list[dict[str, Any]]:
        
        if not user_id:
            raise ValueError("user_id cannot be empty")

        if page_size <= 0:
            raise ValueError("page_size must be greater than 0")

        if not self.collection_exists():
            return []

        conditions: list[FieldCondition] = [
            FieldCondition(
                key="user_id",
                match=MatchValue(value=user_id),
            )
        ]

        if document_id is not None:
            conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            )

        scroll_filter = Filter(must=conditions)

        all_chunks: list[dict[str, Any]] = []
        offset = None

        while True:
            points, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=page_size,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            for point in points:
                all_chunks.append(
                    {
                        "id": point.id,
                        "score": 0.0,
                        "payload": point.payload or {},
                    }
                )

            if next_offset is None:
                break

            offset = next_offset

        return all_chunks
    
    def delete_document(self , document_id:str,)->None:

        if not self.collection_exists():
            return

        self.client.delete(
            collection_name = self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(
                            value=document_id,
                        ),
                    )
                ]
            ),
        )

    def count(self)->int:
        if not self.collection_exists():
            return 0

        result = self.client.count(
            collection_name = self.collection_name,
            exact = True,
        )

        return result.count

            