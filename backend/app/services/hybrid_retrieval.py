import re
from collections import defaultdict
from  typing import Any 
from rank_bm25 import BM25Okapi

def tokenize(text:str)->list[str]:

    if not text:
        return []

    return re.findall(r"\b\w+\b", text.lower())

def _result_key(result:dict[str,Any])->str:

    payload = result.get("payload") or {}

    chunk_id = payload.get("chunk_id")

    if chunk_id is not None:
        return str(chunk_id)

    return str(result.get("id",""))

def hybrid_search(query:str , dense_results:list[dict[str,Any]] , corpus:list[dict[str,Any]] , limit:int = 5 , rrf_k:int = 60,)->list[dict[str, Any]]:

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if limit < 1:
        raise ValueError("Limit must be greater than zero.")

    if rrf_k < 1:
        raise ValueError("rrf_k must be greater than zero.")

    dense_ranked = []

    for result in dense_results:
        if _result_key(result):
            dense_ranked.append(result)

    valid_corpus = []

    for result in corpus:
        payload = result.get("payload") or {}
        text = payload.get("text","")

        if not isinstance(text,str) or not text.strip():
            continue

        tokens = tokenize(text)

        if not tokens:
            continue

        if not _result_key(result):
            continue

        valid_corpus.append((result,tokens))

    if not valid_corpus:
        return dense_ranked[:limit]

    tokenized_corpus = []

    for _, tokens in valid_corpus:
        tokenized_corpus.append(tokens)

    bm25 = BM25Okapi(tokenized_corpus)
    query_tokens = tokenize(query)

    if query_tokens:
        bm25_scores = bm25.get_scores(query_tokens)
    else:
        bm25_scores = []

    lexical_scored = []

    for index, score in enumerate(bm25_scores):
        if score <= 0:
            continue

        result = valid_corpus[index][0]
        lexical_scored.append((result, float(score)))

    lexical_scored.sort(key=lambda item: item[1],reverse=True,)

    lexical_candidates = []

    for result, score in lexical_scored[:max(limit * 4, 20)]:
        lexical_candidates.append(result)

    fused_results: dict[str, dict[str, Any]] = {}
    fused_scores: defaultdict[str, float] = defaultdict(float)

    def add_ranked_results(ranked_results: list[dict[str, Any]],) -> None:
        for rank, result in enumerate(ranked_results, start=1):
            key = _result_key(result)

            if not key:
                continue

            if key not in fused_results:
                fused_results[key] = {
                    "id": result.get("id", key),
                    "score": result.get("score", 0.0),
                    "payload": dict(result.get("payload") or {}),
                }

            fused_scores[key] += 1.0 / (rrf_k + rank)

    add_ranked_results(dense_ranked)
    add_ranked_results(lexical_candidates)

    ordered_keys = sorted(fused_results , key=lambda key: fused_scores[key] , reverse=True,)

    return [
        fused_results[key]
        for key in ordered_keys[:limit]
    ]