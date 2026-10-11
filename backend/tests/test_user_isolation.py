
import pytest

from app.core.vectorstore.qdrant_store import (
    QdrantVectorStore,
)


# --------------------------------------------------
# SEARCH USER-ISOLATION TESTS
# --------------------------------------------------

def test_search_accepts_user_filter():
    store = QdrantVectorStore(
        url="http://localhost:6333",
    )

    assert hasattr(store, "search")


def test_search_rejects_missing_user_id():
    store = QdrantVectorStore(
        url="http://localhost:6333",
    )

    with pytest.raises(ValueError):
        store.search(
            query_embedding=[0.1, 0.2, 0.3],
            limit=5,
            user_id="",
        )


def test_search_rejects_none_user_id():
    store = QdrantVectorStore(
        url="http://localhost:6333",
    )

    with pytest.raises(ValueError):
        store.search(
            query_embedding=[0.1, 0.2, 0.3],
            limit=5,
            user_id=None,
        )


# --------------------------------------------------
# DOCUMENT DELETION ISOLATION TESTS
# --------------------------------------------------

def test_delete_document_requires_user_id():
    store = QdrantVectorStore(
        url="http://localhost:6333",
    )

    with pytest.raises(ValueError):
        store.delete_document(
            document_id="document-1",
            user_id="",
        )


def test_delete_document_rejects_none_user_id():
    store = QdrantVectorStore(
        url="http://localhost:6333",
    )

    with pytest.raises(ValueError):
        store.delete_document(
            document_id="document-1",
            user_id=None,
        )


def test_delete_document_method_exists():
    store = QdrantVectorStore(
        url="http://localhost:6333",
    )

    assert hasattr(store, "delete_document")
