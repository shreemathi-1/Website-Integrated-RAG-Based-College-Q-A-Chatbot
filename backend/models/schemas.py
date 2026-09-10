from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class Source(BaseModel):
    document: str
    page: Optional[int] = None
    category: Optional[str] = None
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []
