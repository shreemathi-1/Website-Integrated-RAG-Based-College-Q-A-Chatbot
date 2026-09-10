# Website RAG Based College Q&A Chatbot

A source-grounded RAG (Retrieval-Augmented Generation) chatbot built for a college website. It answers student, parent, and visitor questions about academics, examinations, departments, campus facilities, and admissions — using only the college's own official documents. If the answer isn't in the source material, it says so instead of guessing.

> Built as a college project to explore how a real institution could deploy a safe, hallucination-resistant chatbot on its public website.

---

## Why this exists

Generic LLM chatbots confidently make things up. For a college website, a wrong answer about exam regulations, fees, or hostel rules isn't a minor bug — it's misinformation with real consequences for students.

This project enforces a strict rule at the architecture level, not just the prompt level: **the model is never allowed to answer from its own general knowledge.** It can only draw from chunks retrieved from the institution's approved documents, and if nothing relevant is found, it returns a fixed fallback response rather than an invented one.

## Features

* 🔒 **Grounded answers only** — retrieval + similarity threshold + strict system prompt combine to block hallucinated facts
* 📄 **Source citations** — every answer is returned with the document (and page, for PDFs) it came from
* ⚡ **Fast, low-cost inference** — local embeddings (no API cost) + Groq's LPU-hosted models for generation
* 🔁 **Simple re-ingestion workflow** — drop a new PDF/Markdown file into `data/documents/`, rerun one command, done
* 🧩 **Decoupled architecture** — the RAG backend is a standalone REST API; the same API powers a CLI tool, a chatbot widget, or any future frontend
* 💬 **Drop-in chat widget** — a floating chatbot bubble (HTML/CSS/JS) that can be embedded into any website with two script tags

## Tech Stack

| Layer        | Technology                                               | Why                                                          |
| ------------ | -------------------------------------------------------- | ------------------------------------------------------------ |
| Embeddings   | `sentence-transformers` (`all-MiniLM-L6-v2`)             | Runs locally, free, zero API cost per query                  |
| Vector Store | [Chroma](https://www.trychroma.com/)                     | Lightweight, file-persisted, no separate DB server           |
| LLM          | [Groq](https://console.groq.com/) (`openai/gpt-oss-20b`) | Fast, free-tier eligible, strong instruction-following       |
| Backend      | FastAPI                                                  | Clean REST boundary between RAG logic and any frontend       |
| Frontend     | Vanilla HTML/CSS/JS widget                               | Zero build step, embeddable anywhere                         |
| PDF Parsing  | `pypdf`                                                  | Ingests official college PDFs (regulations, circulars, etc.) |

## Architecture

```text
Website / Widget
      │
      │ POST /api/chat
      │ { "message": "..." }
      ▼
FastAPI
      │
      ▼
Retrieval
(Chroma, top-10 → filtered to top-3)
      │
      ▼
Similarity Threshold Check
      │
      ├── Below threshold
      │       │
      │       ▼
      │   Fixed fallback response
      │
      └── Above threshold
              │
              ▼
        Groq LLM
      (Grounded Generation)
              │
              ▼
    { "answer": "...", "sources": [...] }
```

Ingestion is a **separate offline process** — it never runs during a live query, so answering a question never triggers document re-processing:

```text
data/documents/*.md, *.pdf
        │
        ▼
Chunk
(paragraph-aware, with overlap)
        │
        ▼
Embed Locally
(MiniLM)
        │
        ▼
Upsert into Chroma
        │
        ▼
vector_store/chroma_db/
```

## Project Structure

```text
rag-chatbot/
├── data/documents/          # knowledge base, organized by category (source of truth)
├── vector_store/            # generated Chroma index (not committed — see .gitignore)
├── backend/
│   ├── main.py              # FastAPI app
│   ├── api/chat.py          # /api/chat, /api/health
│   ├── rag/                 # embeddings, retriever, generator, pipeline
│   ├── ingestion/           # chunker, PDF loader, ingest script
│   └── models/schemas.py    # request/response models
├── frontend/chatbot-widget/ # chatbot.js, chatbot.css, demo HTML page
├── cli.py                   # test the pipeline from the terminal
├── config.py                # every tunable setting (env-overridable)
├── requirements.txt
└── .env.example
```

## Getting Started

### 1. Clone and Install

```bash
git clone https://github.com/<your-username>/ngpit-rag.git
cd ngpit-rag

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Get a free Groq API key at [console.groq.com/keys](https://console.groq.com/keys) (no card required) and paste it into `.env`:

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

### 3. Ingest the Knowledge Base

```bash
python -m backend.ingestion.ingest
```

Rerun this any time a document under `data/documents/` is added, edited, or removed.

### 4. Test from the CLI

```bash
python cli.py "How can I apply for revaluation?"
```

### 5. Run the API

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Check health:

```text
GET http://localhost:8000/api/health
```

### 6. Try the Widget

Open:

```text
frontend/chatbot-widget/index.html
```

in a browser while the API is running.

## API Reference

### `POST /api/chat`

#### Request

```json
{
  "message": "What are the library facilities?"
}
```

#### Response

```json
{
  "answer": "The library offers 42,575 volumes across 10,023 titles...",
  "sources": [
    {
      "document": "campus_facilities.md",
      "page": null,
      "category": "facilities",
      "score": 0.81
    }
  ]
}
```

### `GET /api/health`

```json
{
  "status": "ok"
}
```

## Updating the Knowledge Base

1. Add or replace a file in `data/documents/<category>/`.
2. Optionally add YAML frontmatter for metadata — see any existing `.md` file for the format.
3. Rerun:

```bash
python -m backend.ingestion.ingest
```

No code changes are needed — the ingestion script rebuilds the entire index from whatever's on disk.

## Configuration Reference

All tunables live in `.env` (see `.env.example` for defaults):

| Variable                       | Purpose                                                     |
| ------------------------------ | ----------------------------------------------------------- |
| `TOP_K_RETRIEVE`               | How many chunks Chroma searches before filtering            |
| `TOP_K_FINAL`                  | How many chunks actually get sent to the LLM                |
| `SIMILARITY_THRESHOLD`         | Below this score, skip the LLM call and return the fallback |
| `MAX_CONTEXT_CHARS`            | Hard cap on context size sent per request                   |
| `MAX_ANSWER_TOKENS`            | Hard cap on generated answer length                         |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Chunking granularity                                        |

## Known Limitations / Roadmap

* [ ] Chroma is file-based — fine for a single server process; a production deployment with concurrent traffic should move to Postgres + pgvector
* [ ] No rate limiting on `/api/chat` yet
* [ ] Some departments' source pages had incomplete public content at extraction time (flagged inline in the relevant `data/documents/` files) — pending manual verification against official PDFs
* [ ] Google Drive ingestion (pull source PDFs directly from a Drive folder instead of manual copy)
* [ ] Admin UI for uploading/managing documents without touching the filesystem

## License

MIT — feel free to fork and adapt for your own institution.

## Acknowledgments

Built around publicly available institutional information. This is an independent academic project and is not an official institutional product.
