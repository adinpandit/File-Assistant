
from app.core.vectorstore.qdrant_store import QdrantVectorStore

store = QdrantVectorStore()

print("Configured collection:", store.collection_name)
print("Collection exists:", store.collection_exists())
print("Total points:", store.count())

if not store.collection_exists():
    raise SystemExit("Configured collection does not exist.")

points, next_offset = store.client.scroll(
    collection_name=store.collection_name,
    limit=10,
    with_payload=True,
    with_vectors=False,
)

print("\nFirst 10 stored points:")

for point in points:
    payload = point.payload or {}

    print("-" * 60)
    print("Point ID:", point.id)
    print("Chunk ID:", payload.get("chunk_id"))
    print("User ID:", repr(payload.get("user_id")))
    print("Document ID:", repr(payload.get("document_id")))
    print("Text preview:", str(payload.get("text", ""))[:200])
