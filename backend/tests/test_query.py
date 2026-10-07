
import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import query


client = TestClient(app)


pytestmark = pytest.mark.usefixtures(
    "authenticated_user"
)


def test_query_documents(
    monkeypatch,
):

    def fake_embed_query(text):

        return [
            0.1,
            0.2,
            0.3,
        ]

    class FakeVectorStore:

        def search(
            self,
            query_embedding,
            limit,
            document_id=None,
            user_id=None,
        ):

            assert (
                query_embedding
                == [
                    0.1,
                    0.2,
                    0.3,
                ]
            )

            assert limit == 5

            return [
                {
                    "id": "chunk-1",
                    "score": 0.92,
                    "payload": {
                        "chunk_id": "chunk-1",
                        "document_id": "doc-1",
                        "page_number": 1,
                        "chunk_index": 0,
                        "text": (
                            "Python is a "
                            "programming language."
                        ),
                    },
                }
            ]

    monkeypatch.setattr(
        query,
        "embed_query",
        fake_embed_query,
    )

    monkeypatch.setattr(
        query,
        "QdrantVectorStore",
        FakeVectorStore,
    )

    def fake_generate_answer(
        query,
        context,
        conversation_history="",
    ):

        return (
            "Python is a programming "
            "language. [S1]"
        )

    monkeypatch.setattr(
        query,
        "generate_answer",
        fake_generate_answer,
    )

    response = client.post(
        "/api/query",
        json={
            "query": "What is Python?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["query"]
        == "What is Python?"
    )

    assert len(
        data["sources"]
    ) == 1

    source = data["sources"][0]

    assert (
        source["chunk_id"]
        == "chunk-1"
    )

    assert (
        source["document_id"]
        == "doc-1"
    )

    assert (
        source["page_number"]
        == 1
    )

    assert (
        source["text"]
        == (
            "Python is a "
            "programming language."
        )
    )

    assert (
        source["score"]
        == 0.92
    )


def test_query_with_conversation_history(
    monkeypatch,
):

    def fake_embed_query(text):

        return [
            0.1,
            0.2,
            0.3,
        ]

    class FakeVectorStore:

        def search(
            self,
            query_embedding,
            limit,
            document_id=None,
            user_id=None,
        ):

            return [
                {
                    "id": "chunk-1",
                    "score": 0.92,
                    "payload": {
                        "chunk_id": "chunk-1",
                        "document_id": "doc-1",
                        "page_number": 1,
                        "chunk_index": 0,
                        "text": (
                            "RAG combines "
                            "retrieval with "
                            "generation."
                        ),
                    },
                }
            ]

    class FakeMessage:

        def __init__(
            self,
            role,
            content,
        ):

            self.role = role
            self.content = content

    def fake_get_conversation(
        conversation_id,
        user_id,
    ):

        return object()

    def fake_get_recent_messages(
        conversation_id,
        user_id,
        limit,
    ):

        assert (
            conversation_id
            == "conversation-1"
        )

        assert (
            limit == 10
        )

        return [
            FakeMessage(
                role="user",
                content=(
                    "What is RAG?"
                ),
            ),
            FakeMessage(
                role="assistant",
                content=(
                    "RAG combines retrieval "
                    "with generation."
                ),
            ),
        ]

    captured = {}

    def fake_generate_answer(
        query,
        context,
        conversation_history,
    ):

        captured["query"] = query

        captured["context"] = context

        captured[
            "conversation_history"
        ] = conversation_history

        return (
            "RAG uses retrieval "
            "and generation. [S1]"
        )

    def fake_add_message(
        conversation_id,
        user_id,
        role,
        content,
    ):

        return None

    monkeypatch.setattr(
        query,
        "embed_query",
        fake_embed_query,
    )

    monkeypatch.setattr(
        query,
        "QdrantVectorStore",
        FakeVectorStore,
    )

    monkeypatch.setattr(
        query.conversation_store,
        "get_conversation",
        fake_get_conversation,
    )

    monkeypatch.setattr(
        query.conversation_store,
        "get_recent_messages",
        fake_get_recent_messages,
    )

    monkeypatch.setattr(
        query.conversation_store,
        "add_message",
        fake_add_message,
    )

    monkeypatch.setattr(
        query,
        "generate_answer",
        fake_generate_answer,
    )

    response = client.post(
        "/api/query",
        json={
            "query": (
                "Why is retrieval useful?"
            ),
            "conversation_id": (
                "conversation-1"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["query"]
        == "Why is retrieval useful?"
    )

    assert (
        captured["query"]
        == "Why is retrieval useful?"
    )

    assert (
        "User: What is RAG?"
        in captured[
            "conversation_history"
        ]
    )

    assert (
        "Assistant: RAG combines retrieval "
        "with generation."
        in captured[
            "conversation_history"
        ]
    )

    assert (
        "RAG combines retrieval"
        in captured["context"]
    )


def test_query_empty_string():

    response = client.post(
        "/api/query",
        json={
            "query": ""
        },
    )

    assert response.status_code == 422


def test_query_limit_validation():

    response = client.post(
        "/api/query",
        json={
            "query": "What is Python?",
            "limit": 0,
        },
    )

    assert response.status_code == 422
