from app.core.chunking import chunk
from app.core.vectorstore.qdrant_store import (
    QdrantVectorStore,
)


class FakeResult:
    def __init__(
        self,
        point_id,
        score,
        payload,
    ):
        self.id = point_id
        self.score = score
        self.payload = payload


class FakeCountResult:
    def __init__(
        self,
        count,
    ):
        self.count = count


class FakeCollection:
    def __init__(
        self,
        name,
    ):
        self.name = name


class FakeCollections:
    def __init__(
        self,
        collections,
    ):
        self.collections = collections


class FakeClient:
    def __init__(self):
        self.created = False
        self.points = []
        self.last_query_filter = None

    def get_collections(self):
        if self.created:
            return FakeCollections(
                [
                    FakeCollection(
                        "document_chunks"
                    )
                ]
            )

        return FakeCollections([])

    def create_collection(
        self,
        **kwargs,
    ):
        self.created = True

    def upsert(
        self,
        collection_name,
        points,
    ):
        self.points.extend(points)

    def search(
        self,
        collection_name,
        query_vector,
        limit,
        query_filter=None,
    ):
        self.last_query_filter = query_filter

        results = self.points

        if query_filter is not None:
            for condition in query_filter.must:
                key = condition.key
                expected_value = condition.match.value

                results = [
                    point
                    for point in results
                    if point.payload.get(key)
                    == expected_value
                ]

        return [
            FakeResult(
                point.id,
                0.95,
                point.payload,
            )
            for point in results[:limit]
        ]

    def count(
        self,
        collection_name,
        exact,
    ):
        return FakeCountResult(
            len(self.points)
        )

    def delete(
        self,
        **kwargs,
    ):
        self.points = []


def test_collection_creation():
    store = QdrantVectorStore()

    store.client = FakeClient()

    assert (
        store.collection_exists()
        is False
    )

    store.ensure_collection()

    assert (
        store.collection_exists()
        is True
    )


def test_upsert_chunks():
    store = QdrantVectorStore()

    store.client = FakeClient()

    chunks = [
        chunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            user_id="user-1",
            chunk_index=0,
            page_number=1,
            text="Hello world",
        )
    ]

    embeddings = [
        [0.1, 0.2, 0.3]
    ]

    store.vector_size = 3

    store.upsert_chunks(
        chunks,
        embeddings,
    )

    assert store.count() == 1


def test_search():
    store = QdrantVectorStore()

    store.client = FakeClient()

    chunks = [
        chunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            user_id="user-1",
            chunk_index=0,
            page_number=1,
            text="Hello world",
        )
    ]

    embeddings = [
        [0.1, 0.2, 0.3]
    ]

    store.vector_size = 3

    store.upsert_chunks(
        chunks,
        embeddings,
    )

    results = store.search(
        query_embedding=[
            0.1,
            0.2,
            0.3,
        ],
        limit=5,
    )

    assert len(results) == 1

    assert (
        results[0]["payload"]["text"]
        == "Hello world"
    )


def test_search_with_document_filter():
    store = QdrantVectorStore()

    store.client = FakeClient()

    chunks = [
        chunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            user_id="user-1",
            chunk_index=0,
            page_number=1,
            text="Document one",
        ),
        chunk(
            chunk_id="chunk-2",
            document_id="doc-2",
            user_id="user-1",
            chunk_index=0,
            page_number=1,
            text="Document two",
        ),
    ]

    embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    store.vector_size = 3

    store.upsert_chunks(
        chunks,
        embeddings,
    )

    results = store.search(
        query_embedding=[
            0.1,
            0.2,
            0.3,
        ],
        limit=5,
        document_id="doc-1",
    )

    assert len(results) == 1

    assert (
        results[0]["payload"]["document_id"]
        == "doc-1"
    )

    assert (
        results[0]["payload"]["text"]
        == "Document one"
    )