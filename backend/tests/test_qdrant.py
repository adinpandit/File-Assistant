
import pytest

from app.core.chunking import chunk
from app.core.vectorstore.qdrant_store import (
    QdrantVectorStore,
)


# --------------------------------------------------
# FAKE QDRANT RESPONSE OBJECTS
# --------------------------------------------------

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


class FakeQueryResult:
    def __init__(
        self,
        points,
    ):
        self.points = points


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


# --------------------------------------------------
# FAKE QDRANT CLIENT
# --------------------------------------------------

class FakeClient:
    def __init__(self):
        self.created = False
        self.points = []
        self.last_query_filter = None
        self.last_delete_filter = None

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

    def query_points(
        self,
        collection_name,
        query,
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

        return FakeQueryResult(
            [
                FakeResult(
                    point.id,
                    0.95,
                    point.payload,
                )
                for point in results[:limit]
            ]
        )

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
        collection_name,
        points_selector,
        **kwargs,
    ):
        self.last_delete_filter = points_selector

        # Simulate Qdrant's filtered deletion. Qdrant accepts either a
        # Filter or a FilterSelector wrapping one.
        query_filter = getattr(
            points_selector,
            "filter",
            points_selector,
        )

        if getattr(query_filter, "must", None) is None:
            self.points = []
            return

        # "must" conditions are ANDed: delete only points matching all.
        self.points = [
            point
            for point in self.points
            if not all(
                point.payload.get(condition.key)
                == condition.match.value
                for condition in query_filter.must
            )
        ]


# --------------------------------------------------
# TEST HELPERS
# --------------------------------------------------

def create_test_store():
    store = QdrantVectorStore()

    store.client = FakeClient()
    store.vector_size = 3

    return store


def add_test_chunks(store):
    chunks = [
        chunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            user_id="user-1",
            chunk_index=0,
            page_number=1,
            text="Document one for user one",
        ),
        chunk(
            chunk_id="chunk-2",
            document_id="doc-2",
            user_id="user-1",
            chunk_index=0,
            page_number=1,
            text="Document two for user one",
        ),
        chunk(
            chunk_id="chunk-3",
            document_id="doc-3",
            user_id="user-2",
            chunk_index=0,
            page_number=1,
            text="Document belonging to user two",
        ),
    ]

    embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9],
    ]

    store.upsert_chunks(
        chunks,
        embeddings,
    )


def get_filter_conditions(query_filter):
    assert query_filter is not None

    return {
        condition.key: condition.match.value
        for condition in query_filter.must
    }


# --------------------------------------------------
# COLLECTION TESTS
# --------------------------------------------------

def test_collection_creation():
    store = create_test_store()

    assert store.collection_exists() is False

    store.ensure_collection()

    assert store.collection_exists() is True


# --------------------------------------------------
# UPSERT TESTS
# --------------------------------------------------

def test_upsert_chunks():
    store = create_test_store()

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

    store.upsert_chunks(
        chunks,
        embeddings,
    )

    assert store.count() == 1


# --------------------------------------------------
# USER-SCOPED SEARCH TESTS
# --------------------------------------------------

def test_search():
    store = create_test_store()

    add_test_chunks(store)

    results = store.search(
        query_embedding=[
            0.1,
            0.2,
            0.3,
        ],
        limit=5,
        user_id="user-1",
    )

    assert len(results) == 2

    assert all(
        result["payload"]["user_id"] == "user-1"
        for result in results
    )

    assert (
        results[0]["payload"]["text"]
        == "Document one for user one"
    )

    filters = get_filter_conditions(
        store.client.last_query_filter
    )

    assert filters["user_id"] == "user-1"


def test_search_with_document_filter():
    store = create_test_store()

    add_test_chunks(store)

    results = store.search(
        query_embedding=[
            0.1,
            0.2,
            0.3,
        ],
        limit=5,
        document_id="doc-1",
        user_id="user-1",
    )

    assert len(results) == 1

    assert (
        results[0]["payload"]["document_id"]
        == "doc-1"
    )

    assert (
        results[0]["payload"]["text"]
        == "Document one for user one"
    )

    filters = get_filter_conditions(
        store.client.last_query_filter
    )

    assert filters["user_id"] == "user-1"
    assert filters["document_id"] == "doc-1"


def test_search_does_not_return_another_users_chunks():
    store = create_test_store()

    add_test_chunks(store)

    results = store.search(
        query_embedding=[
            0.1,
            0.2,
            0.3,
        ],
        limit=10,
        user_id="user-1",
    )

    returned_user_ids = {
        result["payload"]["user_id"]
        for result in results
    }

    assert returned_user_ids == {"user-1"}

    assert all(
        result["payload"]["user_id"] != "user-2"
        for result in results
    )


def test_search_requires_user_id():
    store = create_test_store()

    add_test_chunks(store)

    with pytest.raises(ValueError):
        store.search(
            query_embedding=[
                0.1,
                0.2,
                0.3,
            ],
            limit=5,
            user_id="",
        )


# --------------------------------------------------
# USER-SCOPED DELETION TESTS
# --------------------------------------------------

def test_delete_document_requires_user_id():
    store = create_test_store()

    with pytest.raises(ValueError):
        store.delete_document(
            document_id="doc-1",
            user_id="",
        )


def test_delete_document_only_deletes_users_document():
    store = create_test_store()

    add_test_chunks(store)

    store.delete_document(
        document_id="doc-1",
        user_id="user-1",
    )

    remaining = store.client.points

    remaining_document_ids = {
        point.payload["document_id"]
        for point in remaining
    }

    assert "doc-1" not in remaining_document_ids

    # Other documents belonging to user-1 remain.
    assert "doc-2" in remaining_document_ids

    # Another user's document remains untouched.
    assert "doc-3" in remaining_document_ids

