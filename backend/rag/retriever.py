"""
Runtime query-side retrieval. Never rebuilds the index -- it only opens the
existing persisted Chroma collection and searches it. This keeps every chat
query cheap and fast.
"""
import chromadb

import config
from backend.rag.embeddings import embed_query

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def retrieve(query, top_k=None, where=None):
    """Returns a list of {text, metadata, score} dicts, best match first."""
    top_k = top_k or config.TOP_K_RETRIEVE
    collection = get_collection()

    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        where=where,
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    hits = []
    for doc, meta, distance in zip(docs, metas, distances):
        # cosine distance -> similarity score in [0, 1] (roughly)
        similarity = 1 - distance
        hits.append({"text": doc, "metadata": meta, "score": similarity})

    return hits
