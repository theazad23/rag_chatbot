from pydantic import BaseModel
from typing import Optional
from app.services.chat_model import PromptStrategy, ResponseFormat, ContextMode  # Updated import path

class QuestionRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    max_context: Optional[int] = 3
    strategy: Optional[PromptStrategy] = PromptStrategy.STANDARD
    response_format: Optional[ResponseFormat] = ResponseFormat.DEFAULT
    context_mode: Optional[ContextMode] = ContextMode.STRICT