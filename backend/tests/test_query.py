from fastapi.testclient import TestClient
from app.main import app
from app.api.routes import query


client = TestClient(app)


def test_query_documents(
    monkeypatch,
):
    def fake_embed_query(text):
        return [0.1, 0.2, 0.3]

    class FakeVectorStore:
        def search(
            self,
            query_embedding,
            limit,
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
                        "text": "Python is a programming language.",
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

    def fake_generate_answer(query, context):
        return "Python is a programming language. [S1]"

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
    assert source["text"] == (
        "Python is a programming language."
    )
    assert source["score"] == 0.92


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