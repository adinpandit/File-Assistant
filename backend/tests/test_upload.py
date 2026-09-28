from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import upload


client = TestClient(app)


def test_upload_txt_document(
    monkeypatch,
    tmp_path,
):
    def fake_ingest_document(
        file_path,
        document_id,
    ):
        result_document_id = document_id

        class Result:
            document_id = result_document_id
            page_count = 1
            chunk_count = 1

        return Result()

    monkeypatch.setattr(
        upload,
        "ingest_document",
        fake_ingest_document,
    )

    monkeypatch.setattr(
        upload,
        "upload_dir",
        tmp_path,
    )

    response = client.post(
        "/api/upload",
        files={
            "file": (
                "test.txt",
                b"Hello from the test document.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "test.txt"
    assert data["page_count"] == 1
    assert data["chunk_count"] == 1
    assert data["status"] == "ingested"


def test_upload_unsupported_file():
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "test.exe",
                b"invalid",
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert "Unsupported file type" in data["detail"]


def test_upload_without_filename():
    response = client.post(
        "/api/upload",
        files={
            "file": (
                "",
                b"test",
                "text/plain",
            )
        },
    )

    # A part with an empty filename is parsed as a plain form field,
    # not a file, so FastAPI rejects it during validation.
    assert response.status_code == 422