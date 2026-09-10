"""
The single entry point both the API and the CLI call.
Retrieve -> filter by similarity -> truncate for token budget -> generate -> cite.
"""
import config
from backend.rag.generator import generate_answer
from backend.rag.retriever import retrieve

NOT_FOUND_MSG = "It is not available in the sources."


def _truncate_for_budget(chunks, max_chars):
    """Keep adding chunks until the char budget would be exceeded."""
    selected, total = [], 0
    for chunk in chunks:
        if selected and total + len(chunk["text"]) > max_chars:
            break
        selected.append(chunk)
        total += len(chunk["text"])
    return selected


def answer_question(message):
    hits = retrieve(message, top_k=config.TOP_K_RETRIEVE)
    if not hits:
        return NOT_FOUND_MSG, []

    relevant = [h for h in hits if h["score"] >= config.SIMILARITY_THRESHOLD]
    if not relevant:
        return NOT_FOUND_MSG, []

    top_chunks = _truncate_for_budget(relevant[:config.TOP_K_FINAL], config.MAX_CONTEXT_CHARS)

    answer = generate_answer(message, top_chunks)

    if NOT_FOUND_MSG.lower() in answer.lower():
        return NOT_FOUND_MSG, []

    sources, seen = [], set()
    for chunk in top_chunks:
        meta = chunk["metadata"]
        key = (meta.get("source"), meta.get("page"))
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "document": meta.get("source", "unknown"),
            "page": meta.get("page"),
            "category": meta.get("category"),
            "score": round(chunk["score"], 3),
        })

    return answer, sources
