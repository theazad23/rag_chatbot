from pydantic import BaseModel
from typing import Optional, List, Dict

class MessageResponse(BaseModel):
    """Schema for chat message responses"""
    role: str
    content: str
    timestamp: str
    metadata: Optional[dict] = None

class ConversationMessage(BaseModel):
    """Schema for messages in a conversation"""
    id: str
    role: str
    content: str
    timestamp: str
    metadata: Optional[dict] = None

class ConversationDetail(BaseModel):
    """Schema for detailed conversation information"""
    conversation_id: str
    title: Optional[str] = None
    created_at: str
    last_interaction: str
    total_messages: int
    messages: List[ConversationMessage]
    metadata: Optional[dict] = None

class MessageEditRequest(BaseModel):
    """Schema for editing a message in a conversation"""
    new_content: str
    preserve_history: bool = True

class MessageRetryRequest(BaseModel):
    """Schema for retrying a message or response"""
    preserve_history: bool = True
    modified_content: Optional[str] = None
