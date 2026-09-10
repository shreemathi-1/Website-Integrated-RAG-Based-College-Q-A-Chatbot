"""
Offline/admin ingestion process.

Run this ONLY when you add or update documents under data/documents/.
It rebuilds the Chroma collection from scratch each time, so there's never a
mismatch between what's on disk and what the chatbot can retrieve.

Usage (from the project root):
    python -m backend.ingestion.ingest
"""
import glob
import hashlib
import os

import chromadb

import config
from backend.ingestion.chunker import chunk_text, parse_frontmatter
from backend.ingestion.pdf_loader import load_pdf
from backend.rag.embeddings import embed_texts


def make_id(source, suffix):
    return hashlib.md5(f"{source}-{suffix}".encode()).hexdigest()


def ingest_markdown_file(path, docs, metas, ids):
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    metadata, body = parse_frontmatter(raw)
    chunks = chunk_text(body, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    source_name = os.path.basename(path)

    for idx, chunk in enumerate(chunks):
        docs.append(chunk)
        meta = {k: v for k, v in metadata.items() if v}  # drop empty values (Chroma dislikes None)
        meta["source"] = source_name
        meta["chunk_index"] = idx
        metas.append(meta)
        ids.append(make_id(source_name, idx))


def ingest_pdf_file(path, docs, metas, ids):
    source_name = os.path.basename(path)
    for page_num, page_text in load_pdf(path):
        chunks = chunk_text(page_text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        for idx, chunk in enumerate(chunks):
            docs.append(chunk)
            metas.append({
                "source": source_name,
                "page": page_num,
                "chunk_index": idx,
                "category": os.path.basename(os.path.dirname(path)),
            })
            ids.append(make_id(f"{source_name}-p{page_num}", idx))


def collect_documents():
    docs, metas, ids = [], [], []

    files = sorted(
        glob.glob(os.path.join(config.DATA_DIR, "**", "*.md"), recursive=True)
        + glob.glob(os.path.join(config.DATA_DIR, "**", "*.pdf"), recursive=True)
    )

    if not files:
        print(f"No documents found under {config.DATA_DIR}/ -- nothing to ingest.")
        return docs, metas, ids

    for path in files:
        print(f"  reading {path}")
        if path.endswith(".md"):
            ingest_markdown_file(path, docs, metas, ids)
        elif path.endswith(".pdf"):
            ingest_pdf_file(path, docs, metas, ids)

    return docs, metas, ids


def run():
    print("Scanning documents...")
    docs, metas, ids = collect_documents()
    if not docs:
        return

    print(f"Embedding {len(docs)} chunks locally (no API cost)...")
    embeddings = embed_texts(docs)

    client = chromadb.PersistentClient(path=config.CHROMA_PATH)
    collection = client.get_or_create_collection(
        config.COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Wipe and rebuild so stale/removed documents never linger in the index.
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)

    batch_size = 100
    for i in range(0, len(docs), batch_size):
        collection.add(
            documents=docs[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            metadatas=metas[i:i + batch_size],
            ids=ids[i:i + batch_size],
        )

    print(f"Done. Ingested {len(docs)} chunks into Chroma collection '{config.COLLECTION_NAME}' "
          f"at {config.CHROMA_PATH}/")


if __name__ == "__main__":
    run()
