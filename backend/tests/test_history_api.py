from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_history_requires_authentication():
    response = client.get(
        "/api/history/conversations"
    )

    assert response.status_code == 403