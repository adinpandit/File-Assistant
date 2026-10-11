
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from app.core.embeddings import embed_query
from app.core.vectorstore.qdrant_store import QdrantVectorStore
from app.services.hybrid_retrieval import hybrid_search
from app.services.reranking import rerank_results
from app.services.evaluation import (
    evaluate_ranked_results,
    mean_metrics,
)


PIPELINES = ("dense", "hybrid", "reranked")


def load_dataset(path: Path) -> dict[str, Any]:
    """Load and validate the evaluation dataset."""
    with path.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    if not isinstance(dataset, dict):
        raise ValueError("Dataset must be a JSON object")

    k = dataset.get("k", 5)

    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("Dataset k must be a positive integer")

    cases = dataset.get("cases")

    if not isinstance(cases, list) or not cases:
        raise ValueError("Dataset must contain a non-empty cases list")

    required_fields = {
        "user_id",
        "document_id",
        "query",
        "relevant_chunk_ids",
    }

    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"Case {index} must be an object")

        missing = required_fields - case.keys()

        if missing:
            raise ValueError(
                f"Case {index} is missing fields: "
                f"{', '.join(sorted(missing))}"
            )

        for field in ("user_id", "document_id", "query"):
            value = case[field]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Case {index}: {field} cannot be empty"
                )

            if value.startswith("REPLACE_WITH_"):
                raise ValueError(
                    f"Case {index}: replace the placeholder in {field}"
                )

        relevant_ids = case["relevant_chunk_ids"]

        if not isinstance(relevant_ids, list) or not relevant_ids:
            raise ValueError(
                f"Case {index} needs relevant_chunk_ids"
            )

        if any(
            not isinstance(chunk_id, str) or not chunk_id.strip()
            for chunk_id in relevant_ids
        ):
            raise ValueError(
                f"Case {index} contains an invalid chunk ID"
            )

        if any(
            chunk_id.startswith("REPLACE_WITH_")
            for chunk_id in relevant_ids
        ):
            raise ValueError(
                f"Case {index}: replace relevant chunk ID placeholders"
            )

    return dataset


def evaluate_case(
    case: dict[str, Any],
    k: int,
    vector_store: QdrantVectorStore,
) -> dict[str, Any]:
    """Evaluate all three retrieval pipelines for one question."""
    query = case["query"]
    user_id = case["user_id"]
    document_id = case["document_id"]
    relevant_ids = set(case["relevant_chunk_ids"])

    # Fetch extra candidates before selecting the final top K.
    candidate_limit = min(max(k * 4, 20), 40)

    # Embed once and use the same query embedding for dense retrieval.
    start = time.perf_counter()
    query_embedding = embed_query(query)
    embedding_seconds = time.perf_counter() - start

    # Stage 1: dense retrieval.
    start = time.perf_counter()

    dense_results = vector_store.search(
        query_embedding=query_embedding,
        limit=candidate_limit,
        document_id=document_id,
        user_id=user_id,
    )

    dense_seconds = time.perf_counter() - start

    # Load only this user's eligible document corpus for BM25.
    start = time.perf_counter()

    corpus = vector_store.get_all_chunks(
        user_id=user_id,
        document_id=document_id,
    )

    corpus_seconds = time.perf_counter() - start

    # Stage 2: hybrid retrieval.
    start = time.perf_counter()

    hybrid_results = hybrid_search(
        query=query,
        dense_results=dense_results,
        corpus=corpus,
        limit=candidate_limit,
    )

    hybrid_seconds = time.perf_counter() - start

    # Stage 3: reranking.
    start = time.perf_counter()

    reranked_results = rerank_results(
        query=query,
        results=hybrid_results,
        limit=candidate_limit,
    )

    rerank_seconds = time.perf_counter() - start

    # Evaluate the same final K results from each pipeline.
    dense_metrics = evaluate_ranked_results(
        dense_results,
        relevant_ids,
        k,
    )

    hybrid_metrics = evaluate_ranked_results(
        hybrid_results,
        relevant_ids,
        k,
    )

    reranked_metrics = evaluate_ranked_results(
        reranked_results,
        relevant_ids,
        k,
    )

    return {
        "name": case.get("name", query),
        "query": query,
        "dense": dense_metrics,
        "hybrid": hybrid_metrics,
        "reranked": reranked_metrics,
        "latency_seconds": {
            "embedding": embedding_seconds,
            "dense_search": dense_seconds,
            "corpus_loading": corpus_seconds,
            "hybrid_fusion": hybrid_seconds,
            "reranking": rerank_seconds,
            "dense_total": embedding_seconds + dense_seconds,
            "hybrid_total": (
                embedding_seconds
                + dense_seconds
                + corpus_seconds
                + hybrid_seconds
            ),
            "reranked_total": (
                embedding_seconds
                + dense_seconds
                + corpus_seconds
                + hybrid_seconds
                + rerank_seconds
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare dense, hybrid, and reranked RAG retrieval."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evaluation_dataset.json"),
        help="Path to the evaluation dataset JSON file",
    )

    args = parser.parse_args()

    try:
        dataset = load_dataset(args.dataset)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Could not load dataset: {exc}", file=sys.stderr)
        return 1

    k = dataset.get("k", 5)
    vector_store = QdrantVectorStore()

    per_query = []
    metric_groups = {
        pipeline: []
        for pipeline in PIPELINES
    }

    latency_groups = {
        pipeline: []
        for pipeline in PIPELINES
    }

    for index, case in enumerate(dataset["cases"], start=1):
        try:
            result = evaluate_case(
                case=case,
                k=k,
                vector_store=vector_store,
            )
        except Exception as exc:
            print(
                f"Evaluation failed for case {index} "
                f"({case.get('name', case.get('query', 'unknown'))}): "
                f"{exc}",
                file=sys.stderr,
            )
            return 1

        per_query.append(result)

        for pipeline in PIPELINES:
            metric_groups[pipeline].append(result[pipeline])

        latency = result["latency_seconds"]

        latency_groups["dense"].append(latency["dense_total"])
        latency_groups["hybrid"].append(latency["hybrid_total"])
        latency_groups["reranked"].append(latency["reranked_total"])

        print(f"\n{index}. {result['name']}")

        for pipeline in PIPELINES:
            metrics = result[pipeline]

            print(
                f"  {pipeline:8} "
                f"Precision@{k}={metrics[f'precision@{k}']:.3f}  "
                f"Recall@{k}={metrics[f'recall@{k}']:.3f}  "
                f"MRR@{k}={metrics[f'mrr@{k}']:.3f}"
            )

        print(
            "  Latency: "
            f"dense={latency['dense_total']:.3f}s, "
            f"hybrid={latency['hybrid_total']:.3f}s, "
            f"reranked={latency['reranked_total']:.3f}s"
        )

    summary = {
        pipeline: mean_metrics(metric_groups[pipeline])
        for pipeline in PIPELINES
    }

    average_latency = {
        pipeline: (
            sum(values) / len(values) if values else 0.0
        )
        for pipeline, values in latency_groups.items()
    }

    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {len(per_query)} queries, K={k}")
    print(f"{'=' * 70}")

    for pipeline in PIPELINES:
        metrics = summary[pipeline]

        print(
            f"{pipeline:8} "
            f"Precision@{k}={metrics[f'precision@{k}']:.3f}  "
            f"Recall@{k}={metrics[f'recall@{k}']:.3f}  "
            f"MRR@{k}={metrics[f'mrr@{k}']:.3f}  "
            f"Latency={average_latency[pipeline]:.3f}s"
        )

    output = {
        "k": k,
        "query_count": len(per_query),
        "summary": summary,
        "average_latency_seconds": average_latency,
        "per_query": per_query,
    }

    output_path = args.dataset.with_name("evaluation_results.json")

    try:
        output_path.write_text(
            json.dumps(output, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"Could not save results: {exc}", file=sys.stderr)
        return 1

    print(f"\nDetailed results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
