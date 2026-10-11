
import pytest

from app.services.hybrid_retrieval import (
    hybrid_search,
    tokenize,
)


def make_result(
    chunk_id: str,
    text: str,
    score: float = 0.0,
) -> dict:
    return {
        "id": chunk_id,
        "score": score,
        "payload": {
            "chunk_id": chunk_id,
            "document_id": "doc-1",
            "user_id": "user-1",
            "page_number": 1,
            "chunk_index": 0,
            "text": text,
        },
    }


def test_tokenize_lowercases_and_removes_punctuation():
    assert tokenize("Python, RAG!") == [
        "python",
        "rag",
    ]


def test_hybrid_search_includes_dense_and_lexical_results():
    dense = [
        make_result(
            "dense-1",
            "Semantic retrieval finds relevant meaning.",
            0.90,
        )
    ]

    corpus = [
        dense[0],
        make_result(
            "lexical-1",
            "Qdrant supports BM25 keyword retrieval.",
        ),
        make_result(
            "unrelated-1",
            "Cooking pasta requires boiling water.",
        ),
    ]

    results = hybrid_search(
        query="BM25 keyword retrieval",
        dense_results=dense,
        corpus=corpus,
        limit=2,
    )

    result_ids = [
        result["payload"]["chunk_id"]
        for result in results
    ]

    assert len(results) == 2
    assert "dense-1" in result_ids
    assert "lexical-1" in result_ids


def test_rrf_favors_a_chunk_ranked_by_both_methods():
    shared = make_result(
        "shared",
        "Python supports vector search and keyword retrieval.",
        0.8,
    )

    dense = [
        shared,
        make_result(
            "dense-only",
            "Other semantic content.",
            0.7,
        ),
    ]

    corpus = [
        shared,
        make_result(
            "lexical-only",
            "Python supports vector search and keyword retrieval.",
        ),
    ]

    results = hybrid_search(
        query="Python vector search keyword retrieval",
        dense_results=dense,
        corpus=corpus,
        limit=3,
    )

    assert results[0]["payload"]["chunk_id"] == "shared"


def test_hybrid_search_deduplicates_chunks():
    shared = make_result(
        "same-chunk",
        "Python retrieval.",
        0.9,
    )

    results = hybrid_search(
        query="Python retrieval",
        dense_results=[shared, shared],
        corpus=[shared],
        limit=5,
    )

    ids = [
        result["payload"]["chunk_id"]
        for result in results
    ]

    assert ids.count("same-chunk") == 1


def test_empty_corpus_falls_back_to_dense_results():
    dense = [
        make_result(
            "dense-1",
            "Python is a programming language.",
            0.9,
        )
    ]

    results = hybrid_search(
        query="Python",
        dense_results=dense,
        corpus=[],
        limit=5,
    )

    assert results == dense


def test_empty_query_raises_value_error():
    with pytest.raises(ValueError):
        hybrid_search(
            query=" ",
            dense_results=[],
            corpus=[],
        )


def test_invalid_limit_raises_value_error():
    with pytest.raises(ValueError):
        hybrid_search(
            query="Python",
            dense_results=[],
            corpus=[],
            limit=0,
        )
