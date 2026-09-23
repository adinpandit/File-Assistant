from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "RAG Assistant"
    assert data["status"] == "running"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "api": "ok"
    }


def test_upload_endpoint():
    response = client.post("/api/upload")

    assert response.status_code == 200


def test_documents_endpoint():
    response = client.get("/api/documents")

    assert response.status_code == 200
    assert response.json()["documents"] == []


def test_history_endpoint():
    response = client.get("/api/history")

    assert response.status_code == 200
    assert response.json()["history"] == []


def test_query_endpoint():
    response = client.post("/api/query")

    assert response.status_code == 200