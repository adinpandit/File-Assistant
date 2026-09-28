from app.services.retrieval import (
    build_citations,
    build_context,
)


def test_build_context():
    results = [
        {
            "id": "chunk-1",
            "score": 0.95,
            "payload": {
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "page_number": 2,
                "chunk_index": 4,
                "text": "Python is a programming language.",
            },
        }
    ]

    context = build_context(
        results
    )

    assert "[S1]" in context
    assert "doc-1" in context
    assert "Page: 2" in context
    assert "Python is a programming language." in context


def test_build_context_empty():
    context = build_context([])

    assert context == ""


def test_build_citations():
    results = [
        {
            "id": "chunk-1",
            "score": 0.95,
            "payload": {
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "page_number": 2,
                "chunk_index": 4,
                "text": "Python is a programming language.",
            },
        },
        {
            "id": "chunk-2",
            "score": 0.90,
            "payload": {
                "chunk_id": "chunk-2",
                "document_id": "doc-2",
                "page_number": 5,
                "chunk_index": 8,
                "text": "FastAPI is a Python framework.",
            },
        },
    ]

    citations = build_citations(
        results
    )

    assert len(citations) == 2

    assert citations[0].citation_id == "S1"
    assert citations[0].document_id == "doc-1"
    assert citations[0].chunk_id == "chunk-1"
    assert citations[0].page_number == 2

    assert citations[1].citation_id == "S2"
    assert citations[1].document_id == "doc-2"
    assert citations[1].page_number == 5