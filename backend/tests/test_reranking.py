
import pytest

from app.services.reranking import rerank_results


class FakeScorer:
    """Deterministic scorer for testing reranking behavior."""

    def predict(self, pairs):
        scores = []

        for query, text in pairs:
            text = text.lower()

            if "postgresql 16" in text:
                scores.append(10.0)
            elif "database" in text:
                scores.append(5.0)
            else:
                scores.append(1.0)

        return scores


def make_result(chunk_id: str, text: str) -> dict:
    return {
        "id": chunk_id,
        "score": 0.5,
        "payload": {
            "chunk_id": chunk_id,
            "document_id": "doc-1",
            "user_id": "user-1",
            "page_number": 1,
            "chunk_index": 0,
            "text": text,
        },
    }


def test_reranker_places_most_relevant_chunk_first():
    results = [
        make_result("chunk-1", "General information about databases."),
        make_result("chunk-2", "PostgreSQL 16 supports this feature."),
        make_result("chunk-3", "Some unrelated documentation."),
    ]

    reranked = rerank_results(
        query="What does PostgreSQL 16 support?",
        results=results,
        limit=3,
        scorer=FakeScorer(),
    )

    assert [item["id"] for item in reranked] == [
        "chunk-2",
        "chunk-1",
        "chunk-3",
    ]


def test_reranker_respects_limit():
    results = [
        make_result("chunk-1", "Database documentation."),
        make_result("chunk-2", "PostgreSQL 16 documentation."),
        make_result("chunk-3", "Unrelated documentation."),
    ]

    reranked = rerank_results(
        query="PostgreSQL 16",
        results=results,
        limit=2,
        scorer=FakeScorer(),
    )

    assert len(reranked) == 2
    assert reranked[0]["id"] == "chunk-2"


def test_reranker_preserves_original_fields():
    results = [
        make_result("chunk-1", "PostgreSQL 16 documentation.")
    ]

    reranked = rerank_results(
        query="PostgreSQL 16",
        results=results,
        scorer=FakeScorer(),
    )

    assert reranked[0]["id"] == "chunk-1"
    assert reranked[0]["score"] == 0.5
    assert reranked[0]["payload"]["document_id"] == "doc-1"
    assert reranked[0]["rerank_score"] == 10.0


def test_reranker_returns_empty_for_no_results():
    assert rerank_results(
        query="PostgreSQL",
        results=[],
        scorer=FakeScorer(),
    ) == []


def test_reranker_skips_chunks_without_text():
    results = [
        {"id": "empty", "payload": {"text": ""}},
        make_result("valid", "PostgreSQL 16 documentation."),
        {"id": "missing", "payload": {}},
    ]

    reranked = rerank_results(
        query="PostgreSQL 16",
        results=results,
        scorer=FakeScorer(),
    )

    assert [item["id"] for item in reranked] == ["valid"]


def test_reranker_rejects_empty_query():
    with pytest.raises(ValueError, match="Query cannot be empty"):
        rerank_results(
            query=" ",
            results=[make_result("chunk-1", "Some text.")],
            scorer=FakeScorer(),
        )


def test_reranker_rejects_invalid_limit():
    with pytest.raises(ValueError, match="Limit must be greater than zero"):
        rerank_results(
            query="PostgreSQL",
            results=[make_result("chunk-1", "Some text.")],
            limit=0,
            scorer=FakeScorer(),
        )


def test_reranker_falls_back_when_scorer_fails():
    class BrokenScorer:
        def predict(self, pairs):
            raise RuntimeError("Scoring failed")

    results = [
        make_result("chunk-1", "First chunk."),
        make_result("chunk-2", "Second chunk."),
    ]

    reranked = rerank_results(
        query="Some question",
        results=results,
        limit=1,
        scorer=BrokenScorer(),
    )

    # Original hybrid order is preserved when reranking fails.
    assert [item["id"] for item in reranked] == ["chunk-1"]
