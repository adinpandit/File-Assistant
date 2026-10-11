
import pytest

from app.services.evaluation import (
    get_chunk_id,
    get_ranked_chunk_ids,
    precision_at_k,
    recall_at_k,
    reciprocal_rank_at_k,
    evaluate_ranked_results,
    mean_metrics,
)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def make_result(chunk_id, score=0.0):
    """Create a retrieval result in the expected format."""
    return {
        "id": chunk_id,
        "score": score,
        "payload": {
            "chunk_id": chunk_id,
            "text": f"Text for {chunk_id}",
        },
    }


# --------------------------------------------------
# get_chunk_id
# --------------------------------------------------

def test_get_chunk_id_from_payload():
    result = make_result("chunk-1")

    assert get_chunk_id(result) == "chunk-1"


def test_get_chunk_id_from_id_when_payload_missing():
    result = {"id": "chunk-1", "score": 0.8}

    assert get_chunk_id(result) == "chunk-1"


def test_get_chunk_id_returns_none_for_invalid_result():
    assert get_chunk_id({}) is None
    assert get_chunk_id(None) is None


# --------------------------------------------------
# get_ranked_chunk_ids
# --------------------------------------------------

def test_get_ranked_chunk_ids_preserves_order():
    results = [
        make_result("chunk-1"),
        make_result("chunk-2"),
        make_result("chunk-3"),
    ]

    assert get_ranked_chunk_ids(results) == [
        "chunk-1",
        "chunk-2",
        "chunk-3",
    ]


def test_get_ranked_chunk_ids_skips_invalid_results():
    results = [
        make_result("chunk-1"),
        {},
        make_result("chunk-2"),
    ]

    assert get_ranked_chunk_ids(results) == [
        "chunk-1",
        "chunk-2",
    ]


# --------------------------------------------------
# precision_at_k
# --------------------------------------------------

def test_precision_at_k_all_relevant():
    ranked_ids = ["chunk-1", "chunk-2", "chunk-3"]
    relevant_ids = {"chunk-1", "chunk-2", "chunk-3"}

    assert precision_at_k(ranked_ids, relevant_ids, 3) == pytest.approx(1.0)


def test_precision_at_k_half_relevant():
    ranked_ids = ["chunk-1", "chunk-2", "chunk-3", "chunk-4"]
    relevant_ids = {"chunk-1", "chunk-3"}

    assert precision_at_k(ranked_ids, relevant_ids, 4) == pytest.approx(0.5)


def test_precision_at_k_no_relevant_results():
    ranked_ids = ["chunk-1", "chunk-2"]
    relevant_ids = {"chunk-3"}

    assert precision_at_k(ranked_ids, relevant_ids, 2) == pytest.approx(0.0)


def test_precision_at_k_uses_only_top_k():
    ranked_ids = ["chunk-1", "chunk-2", "chunk-3"]
    relevant_ids = {"chunk-3"}

    assert precision_at_k(ranked_ids, relevant_ids, 2) == pytest.approx(0.0)


def test_precision_at_k_rejects_invalid_k():
    with pytest.raises(ValueError):
        precision_at_k(["chunk-1"], {"chunk-1"}, 0)


# --------------------------------------------------
# recall_at_k
# --------------------------------------------------

def test_recall_at_k_all_relevant_found():
    ranked_ids = ["chunk-1", "chunk-2", "chunk-3"]
    relevant_ids = {"chunk-1", "chunk-2"}

    assert recall_at_k(ranked_ids, relevant_ids, 3) == pytest.approx(1.0)


def test_recall_at_k_half_relevant_found():
    ranked_ids = ["chunk-1", "chunk-3"]
    relevant_ids = {"chunk-1", "chunk-2"}

    assert recall_at_k(ranked_ids, relevant_ids, 2) == pytest.approx(0.5)


def test_recall_at_k_no_relevant_found():
    ranked_ids = ["chunk-3", "chunk-4"]
    relevant_ids = {"chunk-1", "chunk-2"}

    assert recall_at_k(ranked_ids, relevant_ids, 2) == pytest.approx(0.0)


def test_recall_at_k_rejects_empty_relevant_set():
    with pytest.raises(ValueError):
        recall_at_k(["chunk-1"], set(), 1)


# --------------------------------------------------
# reciprocal_rank_at_k
# --------------------------------------------------

def test_reciprocal_rank_first_result_relevant():
    ranked_ids = ["chunk-1", "chunk-2", "chunk-3"]
    relevant_ids = {"chunk-1"}

    assert reciprocal_rank_at_k(
        ranked_ids, relevant_ids, 3
    ) == pytest.approx(1.0)


def test_reciprocal_rank_second_result_relevant():
    ranked_ids = ["chunk-1", "chunk-2", "chunk-3"]
    relevant_ids = {"chunk-2"}

    assert reciprocal_rank_at_k(
        ranked_ids, relevant_ids, 3
    ) == pytest.approx(0.5)


def test_reciprocal_rank_third_result_relevant():
    ranked_ids = ["chunk-1", "chunk-2", "chunk-3"]
    relevant_ids = {"chunk-3"}

    assert reciprocal_rank_at_k(
        ranked_ids, relevant_ids, 3
    ) == pytest.approx(1 / 3)


def test_reciprocal_rank_returns_zero_when_no_match():
    ranked_ids = ["chunk-1", "chunk-2"]
    relevant_ids = {"chunk-3"}

    assert reciprocal_rank_at_k(
        ranked_ids, relevant_ids, 2
    ) == pytest.approx(0.0)


# --------------------------------------------------
# evaluate_ranked_results
# --------------------------------------------------

def test_evaluate_ranked_results():
    ranked_ids = ["chunk-1", "chunk-2", "chunk-3"]
    relevant_ids = {"chunk-2", "chunk-3"}

    metrics = evaluate_ranked_results(
        ranked_ids,
        relevant_ids,
        k=3,
    )

    assert metrics["precision@3"] == pytest.approx(2 / 3)
    assert metrics["recall@3"] == pytest.approx(1.0)
    assert metrics["mrr@3"] == pytest.approx(0.5)


def test_evaluate_ranked_results_first_match():
    ranked_ids = ["chunk-2", "chunk-1", "chunk-3"]
    relevant_ids = {"chunk-2", "chunk-3"}

    metrics = evaluate_ranked_results(
        ranked_ids,
        relevant_ids,
        k=3,
    )

    assert metrics["mrr@3"] == pytest.approx(1.0)


# --------------------------------------------------
# mean_metrics
# --------------------------------------------------

def test_mean_metrics():
    results = [
        {
            "precision@5": 1.0,
            "recall@5": 0.5,
            "mrr@5": 1.0,
        },
        {
            "precision@5": 0.5,
            "recall@5": 1.0,
            "mrr@5": 0.5,
        },
    ]

    averages = mean_metrics(results)

    assert averages["precision@5"] == pytest.approx(0.75)
    assert averages["recall@5"] == pytest.approx(0.75)
    assert averages["mrr@5"] == pytest.approx(0.75)


def test_mean_metrics_empty_input():
    assert mean_metrics([]) == {}
