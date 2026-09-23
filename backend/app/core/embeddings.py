from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings

@lru_cache(maxsize=1)
def get_embedding_model()->SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def embed_documents(texts:list[str],)->list[list[float]]:

    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.encode(texts , normalize_embeddings = True , convert_to_numpy = True , show_progress_bar = False,)

    return embeddings.astype(np.float32).tolist()

def embed_query(query:str)->list[float]:

    if not query or not query.strip():
        raise ValueError(f"Query cannot be empty")

    model = get_embedding_model()

    embeddings = model.encode(query , normalize_embeddings = True , convert_to_numpy = True , show_progress_bar = False,)
    
    return embeddings.astype(np.float32).tolist()

def embedding_dimension()->int:

    model = get_embedding_model()

    return model.get_embedding_dimension()
