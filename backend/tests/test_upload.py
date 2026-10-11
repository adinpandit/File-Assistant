from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import upload
from app.models.document import DocumentResponse


client = TestClient(app)

pytestmark = pytest.mark.usefixtures("authenticated_user")


def test_upload_txt_document(
    monkeypatch,
    tmp_path,
):
    def fake_ingest_document(
        file_path,
        document_id,
        user_id=None,
    ):
        result_document_id = document_id

        class Result:
            document_id = result_document_id
            page_count = 1
            chunk_count = 1

        return Result()

    def fake_create_document(**kwargs):
        return DocumentResponse(
            upload_time=datetime.now(timezone.utc),
            **kwargs,
        )

    monkeypatch.setattr(
        upload,
        "ingest_document",
        fake_ingest_document,
    )

    monkeypatch.setattr(
        upload.document_store,
        "create_document",
        fake_create_document,
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

def _fake_result(document_id, page_count, chunk_count):
    class Result:
        pass

    result = Result()
    result.document_id = document_id
    result.page_count = page_count
    result.chunk_count = chunk_count
    return result


@pytest.fixture(autouse=True)
def isolated_upload_dir(monkeypatch, tmp_path):
    # Keep files written by the endpoint out of the working tree.
    monkeypatch.setattr(upload.settings, "upload_dir", str(tmp_path))


def _fake_create_document(**kwargs):
    return DocumentResponse(
        upload_time=datetime.now(timezone.utc),
        **kwargs,
    )


def test_upload_pdf_runs_ingestion_off_the_event_loop(monkeypatch):
    # Regression: ingestion used to run inline in the async endpoint, which
    # blocked every other request for the minutes a large PDF takes to embed.
    import asyncio

    calls = {}

    def fake_ingest_document(file_path, document_id, user_id=None):
        try:
            asyncio.get_running_loop()
            calls["on_event_loop"] = True
        except RuntimeError:
            calls["on_event_loop"] = False

        return _fake_result(document_id, page_count=444, chunk_count=2774)

    monkeypatch.setattr(upload, "ingest_document", fake_ingest_document)
    monkeypatch.setattr(upload.document_store, "create_document", _fake_create_document)

    response = client.post(
        "/api/upload",
        files={"file": ("book.pdf", b"%PDF-1.4 test", "application/pdf")},
    )

    assert response.status_code == 200
    assert calls["on_event_loop"] is False

    data = response.json()

    assert data["filename"] == "book.pdf"
    assert data["file_type"] == "pdf"
    assert data["page_count"] == 444
    assert data["chunk_count"] == 2774
    assert data["status"] == "ingested"
    assert {"document_id", "upload_time"} <= data.keys()


def test_upload_ingestion_error_does_not_leak_internal_details(monkeypatch):
    def failing_ingest_document(file_path, document_id, user_id=None):
        raise RuntimeError(
            "connection to qdrant at http://internal-host:6333 refused"
        )

    monkeypatch.setattr(upload, "ingest_document", failing_ingest_document)

    response = client.post(
        "/api/upload",
        files={"file": ("book.pdf", b"%PDF-1.4 test", "application/pdf")},
    )

    assert response.status_code == 500

    detail = response.json()["detail"]

    assert detail == "Document ingestion failed. The file could not be processed."
    assert "internal-host" not in detail
    assert "qdrant" not in detail.lower()


def test_upload_metadata_failure_removes_written_vectors(monkeypatch):
    deleted = []

    class FakeVectorStore:
        def delete_document(self, document_id, user_id):
            deleted.append((document_id, user_id))

    def fake_ingest_document(file_path, document_id, user_id=None):
        return _fake_result(document_id, page_count=1, chunk_count=3)

    def failing_create_document(**kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(upload, "ingest_document", fake_ingest_document)
    monkeypatch.setattr(upload.document_store, "create_document", failing_create_document)
    monkeypatch.setattr(upload, "QdrantVectorStore", FakeVectorStore)

    response = client.post(
        "/api/upload",
        files={"file": ("notes.md", b"# Notes", "text/markdown")},
    )

    assert response.status_code == 500
    assert "database" not in response.json()["detail"]
    assert len(deleted) == 1
    assert deleted[0][1] == "00000000-0000-0000-0000-000000000001"


def test_upload_parse_failure_does_not_touch_vectors(monkeypatch):
    deleted = []

    class FakeVectorStore:
        def delete_document(self, document_id, user_id):
            deleted.append(document_id)

    def failing_ingest_document(file_path, document_id, user_id=None):
        raise ValueError("Could not read PDF")

    monkeypatch.setattr(upload, "ingest_document", failing_ingest_document)
    monkeypatch.setattr(upload, "QdrantVectorStore", FakeVectorStore)

    response = client.post(
        "/api/upload",
        files={"file": ("broken.pdf", b"not a pdf", "application/pdf")},
    )

    assert response.status_code == 500
    assert deleted == []


def test_upload_requires_authentication():
    from app.core.auth import get_current_user

    app.dependency_overrides.pop(get_current_user, None)

    response = client.post(
        "/api/upload",
        files={"file": ("notes.md", b"# Notes", "text/markdown")},
    )

    assert response.status_code == 403
