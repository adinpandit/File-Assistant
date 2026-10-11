
from app.core.vectorstore.qdrant_store import QdrantVectorStore


USER_ID = "593af9fd-1a1c-45eb-bd43-2f3a2420f078"
DOCUMENT_ID = "6814d8fb-55a8-4bd6-9488-c6b256922458"


def main():
    store = QdrantVectorStore()

    chunks = store.get_all_chunks(
        user_id=USER_ID,
        document_id=DOCUMENT_ID,
    )

    if not chunks:
        print("No chunks found.")
        print("Check your user_id, document_id, and Qdrant collection.")
        return

    print(f"Found {len(chunks)} chunks\n")

    for index, result in enumerate(chunks, start=1):
        payload = result.get("payload") or {}

        print("=" * 80)
        print(f"Result number: {index}")
        print(f"Chunk ID: {payload.get('chunk_id', result.get('id'))}")
        print(f"Page number: {payload.get('page_number')}")
        print(f"Chunk index: {payload.get('chunk_index')}")
        print("\nChunk text:")
        print(payload.get("text", ""))
        print()


if __name__ == "__main__":
    main()
