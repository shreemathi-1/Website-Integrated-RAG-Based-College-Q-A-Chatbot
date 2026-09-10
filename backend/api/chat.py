from fastapi import APIRouter, HTTPException

from backend.models.schemas import ChatRequest, ChatResponse, Source
from backend.rag.pipeline import answer_question

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message must not be empty")

    try:
        answer, sources = answer_question(message)
    except RuntimeError as e:
        # e.g. missing GROQ_API_KEY -- surface a clean 500 instead of a stack trace
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(answer=answer, sources=[Source(**s) for s in sources])


@router.get("/health")
def health():
    return {"status": "ok"}
