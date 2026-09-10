"""
Central configuration for the NGPiTECH RAG chatbot.
Every value here is overridable via environment variables (see .env.example),
so you never have to hunt through code to retune the pipeline.
"""
import os
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")  # silence Chroma's telemetry warnings

# --- LLM (Groq) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# openai/gpt-oss-20b: fast, free-tier eligible, good instruction-following for grounded RAG answers.
# (llama-3.1-8b-instant moved to Enterprise-only access, so it's no longer usable on a free key.)
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# --- Embeddings (run locally, free, no API calls -> zero token cost) ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# --- Vector store (Chroma) ---
CHROMA_PATH = os.getenv("CHROMA_PATH", "vector_store/chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ngpitech_kb")
DATA_DIR = os.getenv("DATA_DIR", "data/documents")

# --- Retrieval tuning ---
TOP_K_RETRIEVE = int(os.getenv("TOP_K_RETRIEVE", 10))     # broad first pass
TOP_K_FINAL = int(os.getenv("TOP_K_FINAL", 3))            # narrowed set sent to the LLM
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.35))  # below this -> "not in sources"

# --- Chunking ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))            # characters per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 120))

# --- Token-usage guardrails (this is what keeps each Groq call cheap) ---
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", 3000))  # hard cap on context sent to the LLM
MAX_ANSWER_TOKENS = int(os.getenv("MAX_ANSWER_TOKENS", 400))   # hard cap on generated answer length

# --- API ---
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
