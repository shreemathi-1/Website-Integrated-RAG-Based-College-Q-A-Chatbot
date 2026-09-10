"""
Calls Groq to turn (question + retrieved context) into a grounded answer.

Token-usage notes:
 - Only TOP_K_FINAL chunks are ever sent (default 3), further capped by
   MAX_CONTEXT_CHARS -- see pipeline.py.
 - MAX_ANSWER_TOKENS caps the completion length.
 - System prompt is intentionally short: strict but not padded with examples.
"""
from groq import Groq

import config

SYSTEM_PROMPT = """You are the NGPiTECH Information Assistant for Dr. N.G.P. Institute of Technology's website.

Rules:
1. Answer ONLY using the provided source context. Never use outside/general knowledge for college-specific facts (regulations, dates, fees, contacts, procedures, facilities, staff, policies).
2. Never invent or guess any detail that is not present in the context.
3. If the context does not contain enough information to answer, reply with exactly: It is not available in the sources.
4. Be concise: 2-4 sentences, or a short list if the question needs one.
5. Answer naturally, as the college's assistant -- don't mention "context", "chunks", or retrieval."""


def _client():
    if not config.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file (see .env.example)."
        )
    return Groq(api_key=config.GROQ_API_KEY)


def build_user_prompt(question, context_chunks):
    context_text = "\n\n---\n\n".join(
        f"[Source: {c['metadata'].get('source', 'unknown')}]\n{c['text']}"
        for c in context_chunks
    )
    return f"Context:\n{context_text}\n\nQuestion: {question}\n\nAnswer using only the context above."


def generate_answer(question, context_chunks):
    client = _client()
    user_prompt = build_user_prompt(question, context_chunks)

    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=config.MAX_ANSWER_TOKENS,
    )
    return response.choices[0].message.content.strip()
