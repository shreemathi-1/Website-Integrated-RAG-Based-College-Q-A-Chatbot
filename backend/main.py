from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from backend.api.chat import router as chat_router

app = FastAPI(title="NGPiTECH RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "NGPiTECH RAG Chatbot API is running. POST questions to /api/chat"}
