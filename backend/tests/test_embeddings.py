from app.core.embeddings import (
    embed_documents,
    embed_query,
    embedding_dimension,
)


def test_embedding_dimension():
    dimension = embedding_dimension()

    assert dimension == 384


def test_embed_documents():
    texts = [
        "FastAPI is a Python web framework.",
        "Qdrant is a vector database.",
    ]

    embeddings = embed_documents(texts)

    assert len(embeddings) == 2

    for embedding in embeddings:
        assert len(embedding) == 384


def test_embed_query():
    query = "What is FastAPI?"

    embedding = embed_query(query)

    assert len(embedding) == 384


def test_empty_documents():
    embeddings = embed_documents([])

    assert embeddings == []


def test_empty_query():
    try:
        embed_query("")
        assert False
    except ValueError:
        assert True