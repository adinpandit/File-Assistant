import os
from uuid import uuid4

import pytest

from app.core.doc_store_initialize import (
    get_connection,
)
from app.services.doc_store import (
    DocumentStore,
)


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL"
)


pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason=(
        "TEST_DATABASE_URL is not configured"
    ),
)


@pytest.fixture
def document_store(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        TEST_DATABASE_URL,
    )

    from app.config import settings

    settings.database_url = (
        TEST_DATABASE_URL
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id UUID PRIMARY KEY,
                    email VARCHAR(255)
                    NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role VARCHAR(50)
                    NOT NULL,
                    created_at TIMESTAMPTZ
                    NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id UUID PRIMARY KEY,
                    user_id UUID NOT NULL
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,
                    filename VARCHAR(255)
                    NOT NULL,
                    file_type VARCHAR(20)
                    NOT NULL,
                    upload_time TIMESTAMPTZ
                    NOT NULL,
                    page_count INTEGER
                    NOT NULL,
                    chunk_count INTEGER
                    NOT NULL
                )
                """
            )

        connection.commit()

    finally:
        connection.close()

    return DocumentStore()


def create_test_user():
    user_id = uuid4()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (
                    user_id,
                    email,
                    password_hash,
                    role,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW()
                )
                """,
                (
                    user_id,
                    f"{user_id}@example.com",
                    "test-password-hash",
                    "USER",
                ),
            )

        connection.commit()

    finally:
        connection.close()

    return str(user_id)


def test_create_and_get_document(
    document_store,
):
    user_id = create_test_user()

    document_id = str(uuid4())

    created = document_store.create_document(
        document_id=document_id,
        user_id=user_id,
        filename="test.pdf",
        file_type="pdf",
        page_count=3,
        chunk_count=8,
    )

    assert created.document_id == document_id
    assert created.user_id == user_id
    assert created.filename == "test.pdf"

    retrieved = document_store.get_document(
        document_id=document_id,
        user_id=user_id,
    )

    assert retrieved is not None

    assert (
        retrieved.document_id
        == document_id
    )


def test_list_documents(
    document_store,
):
    user_id = create_test_user()

    document_store.create_document(
        document_id=str(uuid4()),
        user_id=user_id,
        filename="one.pdf",
        file_type="pdf",
        page_count=1,
        chunk_count=2,
    )

    document_store.create_document(
        document_id=str(uuid4()),
        user_id=user_id,
        filename="two.md",
        file_type="md",
        page_count=1,
        chunk_count=3,
    )

    documents = (
        document_store.list_documents(
            user_id=user_id,
        )
    )

    assert len(documents) == 2


def test_delete_document(
    document_store,
):
    user_id = create_test_user()

    document_id = str(uuid4())

    document_store.create_document(
        document_id=document_id,
        user_id=user_id,
        filename="test.pdf",
        file_type="pdf",
        page_count=1,
        chunk_count=2,
    )

    deleted = (
        document_store.delete_document(
            document_id=document_id,
            user_id=user_id,
        )
    )

    assert deleted is True

    document = (
        document_store.get_document(
            document_id=document_id,
            user_id=user_id,
        )
    )

    assert document is None