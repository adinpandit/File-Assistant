
from typing import Any


def get_chunk_id(result: dict[str, Any] | None) -> str | None:
    """Extract the chunk ID from a retrieval result, or None if absent."""
    if not isinstance(result, dict):
        return None

    payload = result.get("payload") or {}
    chunk_id = payload.get("chunk_id")

    if chunk_id is not None:
        return str(chunk_id)

    result_id = result.get("id")

    if result_id is not None:
        return str(result_id)

    return None


def get_ranked_chunk_ids(
    results: list[dict[str, Any] | str],
) -> list[str]:
    """Return unique chunk IDs in retrieval order.

    Accepts retrieval-result dicts or plain chunk ID strings.
    """
    chunk_ids: list[str] = []
    seen: set[str] = set()

    for result in results:
        if isinstance(result, str):
            chunk_id = result
        else:
            chunk_id = get_chunk_id(result)

        if not chunk_id or chunk_id in seen:
            continue

        seen.add(chunk_id)
        chunk_ids.append(chunk_id)

    return chunk_ids


def _validate_inputs(
    relevant_chunk_ids: set[str],
    k: int,
) -> None:
    if k < 1:
        raise ValueError("k must be greater than zero")

    if not relevant_chunk_ids:
        raise ValueError("Relevant chunk IDs cannot be empty")


def precision_at_k(
    results: list[dict[str, Any] | str],
    relevant_chunk_ids: set[str],
    k: int = 5,
) -> float:
    """Calculate Precision@K: relevant results divided by K."""
    _validate_inputs(relevant_chunk_ids, k)

    ranked_ids = get_ranked_chunk_ids(results)[:k]

    relevant_found = sum(
        chunk_id in relevant_chunk_ids
        for chunk_id in ranked_ids
    )

    return relevant_found / k


def recall_at_k(
    results: list[dict[str, Any] | str],
    relevant_chunk_ids: set[str],
    k: int = 5,
) -> float:
    """Calculate Recall@K: relevant results found / all relevant results."""
    _validate_inputs(relevant_chunk_ids, k)

    ranked_ids = get_ranked_chunk_ids(results)[:k]

    relevant_found = sum(
        chunk_id in relevant_chunk_ids
        for chunk_id in ranked_ids
    )

    return relevant_found / len(relevant_chunk_ids)


def reciprocal_rank_at_k(
    results: list[dict[str, Any] | str],
    relevant_chunk_ids: set[str],
    k: int = 5,
) -> float:
    """Calculate Reciprocal Rank@K for the first relevant result."""
    _validate_inputs(relevant_chunk_ids, k)

    ranked_ids = get_ranked_chunk_ids(results)[:k]

    for rank, chunk_id in enumerate(ranked_ids, start=1):
        if chunk_id in relevant_chunk_ids:
            return 1.0 / rank

    return 0.0


def evaluate_ranked_results(
    results: list[dict[str, Any] | str],
    relevant_chunk_ids: set[str],
    k: int = 5,
) -> dict[str, float]:
    """Calculate all retrieval metrics for a single question."""
    return {
        f"precision@{k}": precision_at_k(
            results,
            relevant_chunk_ids,
            k,
        ),
        f"recall@{k}": recall_at_k(
            results,
            relevant_chunk_ids,
            k,
        ),
        f"mrr@{k}": reciprocal_rank_at_k(
            results,
            relevant_chunk_ids,
            k,
        ),
    }


def mean_metrics(
    evaluations: list[dict[str, float]],
) -> dict[str, float]:
    """Calculate average metrics across evaluation questions.

    Every evaluation must report the same metric names.
    """
    if not evaluations:
        return {}

    metric_names = list(evaluations[0])

    for evaluation in evaluations:
        if set(evaluation) != set(metric_names):
            raise ValueError(
                "All evaluations must contain the same metrics"
            )

    return {
        metric_name: sum(
            evaluation[metric_name]
            for evaluation in evaluations
        ) / len(evaluations)
        for metric_name in metric_names
    }
