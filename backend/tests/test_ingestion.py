from pathlib import Path

from app.core.vectorstore.qdrant_store import QdrantVectorStore
from app.services.ingestion import ingest_document


class FakeResult:
    def __init__(self, point_id, score, payload):
        self.id = point_id
        self.score = score
        self.payload = payload


class FakeCountResult:
    def __init__(self, count):
        self.count = count


class FakeCollection:
    def __init__(self, name):
        self.name = name


class FakeCollections:
    def __init__(self, collections):
        self.collections = collections


class FakeClient:
    def __init__(self):
        self.created = False
        self.points = []

    def get_collections(self):
        if self.created:
            return FakeCollections(
                [FakeCollection("document_chunks")]
            )

        return FakeCollections([])

    def create_collection(self, **kwargs):
        self.created = True

    def upsert(self, collection_name, points):
        self.points.extend(points)

    def count(self, collection_name, exact):
        return FakeCountResult(len(self.points))

    def search(
        self,
        collection_name,
        query_vector,
        limit,
    ):
        return [
            FakeResult(
                point.id,
                0.95,
                point.payload,
            )
            for point in self.points[:limit]
        ]


def test_ingest_text_document(
    tmp_path: Path,
):
    document = tmp_path / "document.txt"

    document.write_text(
        "This is a test document for the RAG assistant.",
        encoding="utf-8",
    )

    vector_store = QdrantVectorStore()

    vector_store.client = FakeClient()

    result = ingest_document(
        file_path=document,
        document_id="doc-1",
        user_id="user-1",
        vector_store=vector_store,
    )

    assert result.document_id == "doc-1"
    assert result.page_count == 1
    assert result.chunk_count >= 1

    assert vector_store.count() == result.chunk_count