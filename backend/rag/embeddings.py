"""
Embeddings run locally via sentence-transformers -- no API calls, no token cost.
This is the single place that loads the model, so it's loaded once and reused
across every ingestion run and every query.
"""
from functools import lru_cache
from sentence_transformers import SentenceTransformer

import config


@lru_cache(maxsize=1)
def get_embedder():
    return SentenceTransformer(config.EMBEDDING_MODEL)


def embed_texts(texts):
    """Embed a list of strings. Returns a list of float vectors."""
    model = get_embedder()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def embed_query(text):
    """Embed a single query string."""
    return embed_texts([text])[0]
