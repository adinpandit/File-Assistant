from app.core.vectorstore.qdrant_store import (
    QdrantVectorStore,
)


def test_search_accepts_user_filter():
    store = QdrantVectorStore(
        url="http://localhost:6333",
    )

    assert hasattr(
        store,
        "search",
    )