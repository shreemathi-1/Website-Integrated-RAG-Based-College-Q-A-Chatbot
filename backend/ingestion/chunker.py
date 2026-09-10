"""
Turns a document's raw text into (a) metadata parsed from YAML-style frontmatter
and (b) a list of size-bounded, overlapping chunks ready for embedding.

Chunking splits on paragraph boundaries first (keeps related sentences together,
which gives the LLM cleaner context = fewer tokens wasted on fragments), and
only hard-splits a paragraph if it's longer than one chunk.
"""
import re


def parse_frontmatter(text):
    """Parse a leading '---\\n...\\n---' YAML-ish block into a flat dict."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text

    fm_text, body = match.group(1), match.group(2)
    metadata = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, body


def chunk_text(text, chunk_size=800, overlap=120):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if len(para) > chunk_size:
            # paragraph itself is too big (e.g. a big table) -- hard split it
            step = max(chunk_size - overlap, 1)
            for i in range(0, len(para), step):
                chunks.append(para[i:i + chunk_size])
            current = ""
        else:
            current = para

    if current:
        chunks.append(current)

    # stitch a small overlap onto the start of each chunk (except the first)
    # so context isn't lost right at a chunk boundary.
    if overlap > 0:
        stitched = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                stitched.append(chunk)
            else:
                tail = chunks[i - 1][-overlap:]
                stitched.append(f"{tail}\n{chunk}")
        return stitched

    return chunks
