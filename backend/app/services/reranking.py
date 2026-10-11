
import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker = None


def _get_reranker() -> Any:
    """Load the cross-encoder only when reranking is first requested."""
    global _reranker

    if _reranker is None:
        from sentence_transformers import CrossEncoder

        _reranker = CrossEncoder(DEFAULT_RERANKER_MODEL)

    return _reranker


def rerank_results(
    query: str,
    results: list[dict[str, Any]],
    limit: int = 5,
    scorer: Any | None = None,
) -> list[dict[str, Any]]:
    """Rerank retrieved chunks by query–chunk relevance.

    Args:
        query: The query used for retrieval.
        results: Candidate chunks from hybrid retrieval.
        limit: Maximum number of results to return.
        scorer: Optional injected scorer, useful for unit tests.

    Returns:
        Results ordered by descending cross-encoder score.
        Original result fields are preserved.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if limit < 1:
        raise ValueError("Limit must be greater than zero.")

    if not results:
        return []

    # Ignore candidates without usable text.
    candidates: list[dict[str, Any]] = []

    for result in results:
        payload = result.get("payload") or {}
        text = payload.get("text")

        if isinstance(text, str) and text.strip():
            candidates.append(result)

    if not candidates:
        return []

    try:
        model = scorer if scorer is not None else _get_reranker()

        pairs = [
            (query.strip(), result["payload"]["text"])
            for result in candidates
        ]

        scores = model.predict(pairs)

        if len(scores) != len(candidates):
            raise ValueError(
                "Reranker returned a different number of scores "
                "than candidate chunks."
            )

        ranked: list[tuple[float, int, dict[str, Any]]] = []

        for index, (result, score) in enumerate(
            zip(candidates, scores, strict=True)
        ):
            reranked_result = dict(result)
            reranked_result["payload"] = dict(result.get("payload") or {})
            reranked_result["rerank_score"] = float(score)

            ranked.append(
                (float(score), index, reranked_result)
            )

        # Preserve the original order when scores are tied.
        ranked.sort(key=lambda item: (-item[0], item[1]))

        return [
            result
            for _, _, result in ranked[:limit]
        ]

    except Exception:
        # Retrieval should remain usable if the reranker is unavailable.
        logger.exception(
            "Cross-encoder reranking failed; using hybrid ranking."
        )
        return candidates[:limit]
