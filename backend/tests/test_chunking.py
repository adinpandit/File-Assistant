from app.core.chunking import (
    chunck_overlap,
    chunk_size,
    chunk_pages,
)
from app.core.parsing.base import Page


def test_chunk_pages():
    text = "A" * 1000

    pages = [
        Page(
            number=1,
            text=text,
        )
    ]

    chunks = chunk_pages(
        pages=pages,
        document_id="document-1",
        user_id="user-1",
    )

    assert len(chunks) > 1

    for chunk in chunks:
        assert chunk.document_id == "document-1"
        assert chunk.user_id == "user-1"
        assert chunk.page_number == 1
        assert chunk.text


def test_chunk_metadata():
    pages = [
        Page(
            number=3,
            text="This is some document text.",
        )
    ]

    chunks = chunk_pages(
        pages=pages,
        document_id="doc-123",
        user_id="user-456",
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.chunk_id
    assert chunk.document_id == "doc-123"
    assert chunk.user_id == "user-456"
    assert chunk.chunk_index == 0
    assert chunk.page_number == 3


def test_empty_page():
    pages = [
        Page(
            number=1,
            text="",
        )
    ]

    chunks = chunk_pages(
        pages=pages,
        document_id="doc-1",
    )

    assert chunks == []


def test_multiple_pages():
    pages = [
        Page(
            number=1,
            text="First page content.",
        ),
        Page(
            number=2,
            text="Second page content.",
        ),
    ]

    chunks = chunk_pages(
        pages=pages,
        document_id="doc-1",
    )

    assert len(chunks) == 2

    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2


def test_invalid_chunk_size():
    pages = [
        Page(
            number=1,
            text="Some text",
        )
    ]

    try:
        chunk_pages(
            pages=pages,
            document_id="doc-1",
            chunk_size=0,
        )
        assert False
    except ValueError:
        assert True


def test_invalid_overlap():
    pages = [
        Page(
            number=1,
            text="Some text",
        )
    ]

    try:
        chunk_pages(
            pages=pages,
            document_id="doc-1",
            chunk_size=100,
            chunk_overlap=100,
        )
        assert False
    except ValueError:
        assert True