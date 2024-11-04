from pydantic import BaseModel
from typing import Optional, List, Dict

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: str
    metadata: Optional[dict] = None

class ConversationMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    metadata: Optional[dict] = None

class ConversationDetail(BaseModel):
    conversation_id: str
    title: Optional[str] = None
    created_at: str
    last_interaction: str
    total_messages: int
    messages: List[ConversationMessage]
    metadata: Optional[dict] = None

class MessageEditRequest(BaseModel):
    new_content: str
    preserve_history: bool = True

class MessageRetryRequest(BaseModel):
    preserve_history: bool = True
    modified_content: Optional[str] = None
