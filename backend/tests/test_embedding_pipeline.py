from app.core.chunking import chunk_pages
from app.core.embeddings import embed_documents
from app.core.parsing.base import Page


def test_page_to_chunk_to_embedding():
    pages = [
        Page(
            number=1,
            text=(
                "Retrieval-Augmented Generation "
                "combines retrieval with generation."
            ),
        )
    ]

    chunks = chunk_pages(
        pages=pages,
        document_id="doc-1",
        user_id="user-1",
    )

    texts = [
        chunk.text
        for chunk in chunks
    ]

    embeddings = embed_documents(texts)

    assert len(chunks) == len(embeddings)

    for embedding in embeddings:
        assert len(embedding) == 384