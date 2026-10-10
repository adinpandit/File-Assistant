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
        assert text == "What is Python?"

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
            assert query_embedding == [
                0.1,
                0.2,
                0.3,
            ]

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

    def fake_generate_answer(
        query,
        context,
        conversation_history="",
    ):
        assert query == "What is Python?"

        return (
            "Python is a programming "
            "language. [S1]"
        )

    def fail_rewrite_query(*args, **kwargs):
        pytest.fail(
            "rewrite_query should not be called "
            "without a conversation."
        )

    monkeypatch.setattr(
        query,
        "embed_query",
        fake_embed_query,
    )

    monkeypatch.setattr(
        query,
        "rewrite_query",
        fail_rewrite_query,
    )

    monkeypatch.setattr(
        query,
        "QdrantVectorStore",
        FakeVectorStore,
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

    assert data["query"] == "What is Python?"

    assert len(data["sources"]) == 1

    source = data["sources"][0]

    assert source["chunk_id"] == "chunk-1"
    assert source["document_id"] == "doc-1"
    assert source["page_number"] == 1
    assert source["chunk_index"] == 0

    assert (
        source["text"]
        == "Python is a programming language."
    )

    assert source["score"] == 0.92


def test_query_with_conversation_history(
    monkeypatch,
):
    original_query = "Why is retrieval useful?"

    rewritten_query = (
        "Why is retrieval useful in "
        "retrieval-augmented generation?"
    )

    def fake_rewrite_query(
        query,
        conversation_history="",
    ):
        assert query == original_query

        assert (
            "User: What is RAG?"
            in conversation_history
        )

        assert (
            "Assistant: RAG combines retrieval "
            "with generation."
            in conversation_history
        )

        return rewritten_query

    def fake_embed_query(text):
        # Retrieval must use the rewritten query.
        assert text == rewritten_query

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
            assert query_embedding == [
                0.1,
                0.2,
                0.3,
            ]

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
                            "RAG combines retrieval "
                            "with generation."
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
        assert conversation_id == "conversation-1"

        return object()

    def fake_get_recent_messages(
        conversation_id,
        user_id,
        limit,
    ):
        assert conversation_id == "conversation-1"
        assert limit == 10

        return [
            FakeMessage(
                role="user",
                content="What is RAG?",
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
        conversation_history="",
    ):
        # Answer generation must retain the original question.
        captured["query"] = query
        captured["context"] = context
        captured["conversation_history"] = (
            conversation_history
        )

        return "RAG uses retrieval and generation. [S1]"

    saved_messages = []

    def fake_add_message(
        conversation_id,
        user_id,
        role,
        content,
    ):
        saved_messages.append(
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "role": role,
                "content": content,
            }
        )

    monkeypatch.setattr(
        query,
        "rewrite_query",
        fake_rewrite_query,
    )

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
            "query": original_query,
            "conversation_id": "conversation-1",
        },
    )

    assert response.status_code == 200

    data = response.json()

    # API response retains the original query.
    assert data["query"] == original_query

    # Answer generation receives the original query.
    assert captured["query"] == original_query

    # Conversation history reaches answer generation.
    assert (
        "User: What is RAG?"
        in captured["conversation_history"]
    )

    assert (
        "Assistant: RAG combines retrieval "
        "with generation."
        in captured["conversation_history"]
    )

    # Retrieved context reaches answer generation.
    assert (
        "RAG combines retrieval"
        in captured["context"]
    )

    # Original user query and generated answer are persisted.
    assert len(saved_messages) == 2

    assert saved_messages[0]["role"] == "user"
    assert saved_messages[0]["content"] == original_query

    assert saved_messages[1]["role"] == "assistant"
    assert (
        saved_messages[1]["content"]
        == "RAG uses retrieval and generation. [S1]"
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
