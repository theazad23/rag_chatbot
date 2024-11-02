from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import conversation, document, chat, maintenance, health

app = FastAPI(title="Enhanced RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversation.router)
app.include_router(document.router)
app.include_router(chat.router)
app.include_router(maintenance.router)
app.include_router(health.router)