from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from app.models.conversation import (
    ConversationMessage, 
    ConversationDetail,
    MessageEditRequest,
    MessageRetryRequest
)
from app.models.chat import QuestionRequest
from app.services import memory_manager
from app.routers import chat as chat_router

router = APIRouter(prefix="/conversation", tags=["conversations"])

@router.post("")
async def create_conversation():
    """Create a new conversation."""
    conversation_id = memory_manager.create_conversation()
    return {"conversation_id": conversation_id}

@router.get("/{conversation_id}/detail")
async def get_conversation_detail(
    conversation_id: str,
    message_limit: Optional[int] = Query(50, description="Maximum number of messages to return"),
    before_timestamp: Optional[str] = Query(None, description="Get messages before this timestamp")
) -> ConversationDetail:
    """Get detailed conversation information including message history."""
    try:
        history = memory_manager.get_conversation_context(conversation_id, num_previous=message_limit)
        if not history:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        messages = []
        for interaction in history:
            messages.append({
                "id": f"{conversation_id}_{len(messages)}",
                "role": "user",
                "content": interaction["question"],
                "timestamp": interaction["timestamp"],
                "metadata": {"type": "question"}
            })
            
            messages.append({
                "id": f"{conversation_id}_{len(messages)}",
                "role": "assistant",
                "content": interaction["response"]["response"],
                "timestamp": interaction["timestamp"],
                "metadata": {
                    "type": "response",
                    **interaction["response"].get("metadata", {})
                }
            })
            
        summary = memory_manager.get_conversation_summary(conversation_id)
        
        return ConversationDetail(
            conversation_id=conversation_id,
            title=f"Conversation from {summary['start_time']}",
            created_at=summary["start_time"],
            last_interaction=summary["last_interaction"],
            total_messages=len(messages),
            messages=messages,
            metadata={
                "has_more": len(messages) >= message_limit,
                "context_mode": "strict",
                "total_interactions": summary["total_interactions"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation summary and history."""
    return memory_manager.get_conversation_summary(conversation_id)

@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    title: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Update conversation metadata."""
    try:
        conversation = memory_manager.get_conversation_summary(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        updated = memory_manager.update_conversation_metadata(
            conversation_id,
            title=title,
            metadata=metadata
        )
        
        return {"message": "Conversation updated", "conversation": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    success = memory_manager.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted"}

@router.get("")
async def list_conversations(
    limit: Optional[int] = Query(10, description="Maximum number of conversations to return"),
    offset: Optional[int] = Query(0, description="Number of conversations to skip"),
    sort_by: Optional[str] = Query("last_interaction", description="Field to sort by"),
    order: Optional[str] = Query("desc", description="Sort order: 'asc' or 'desc'")
):
    """List all conversations with pagination and sorting options."""
    try:
        conversations = memory_manager.list_conversations()
        
        if sort_by == "last_interaction":
            conversations.sort(
                key=lambda x: x["last_interaction"] if x["last_interaction"] else "",
                reverse=(order == "desc")
            )
        elif sort_by == "total_interactions":
            conversations.sort(
                key=lambda x: x["interactions"],
                reverse=(order == "desc")
            )
            
        paginated_conversations = conversations[offset:offset + limit]
        
        detailed_conversations = []
        for conv in paginated_conversations:
            conv_id = conv["conversation_id"]
            summary = memory_manager.get_conversation_summary(conv_id)
            if summary and "error" not in summary:
                detailed_conversations.append(summary)
                
        return {
            "conversations": detailed_conversations,
            "metadata": {
                "total": len(conversations),
                "returned": len(detailed_conversations),
                "offset": offset,
                "limit": limit,
                "sort_by": sort_by,
                "order": order
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{conversation_id}/messages/{message_id}/edit")
async def edit_message(
    conversation_id: str,
    message_id: str,
    request: MessageEditRequest
):
    """Edit a message in the conversation."""
    try:
        result = memory_manager.edit_message(
            conversation_id,
            message_id,
            request.new_content,
            request.preserve_history
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        if message_id.endswith("_user"):
            chat_request = QuestionRequest(
                question=request.new_content,
                conversation_id=conversation_id
            )
            return await chat_router.ask_question(chat_request)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{conversation_id}/messages/{message_id}/retry")
async def retry_message(
    conversation_id: str,
    message_id: str,
    request: MessageRetryRequest
):
    """Retry a message with optional modifications."""
    try:
        result = memory_manager.retry_message(
            conversation_id,
            message_id,
            request.modified_content,
            request.preserve_history
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        chat_request = QuestionRequest(
            question=request.modified_content or result["questions_asked"][-1],
            conversation_id=conversation_id
        )
        return await chat_router.ask_question(chat_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{conversation_id}/messages/{message_id}/retry-response")
async def retry_response(
    conversation_id: str,
    message_id: str,
    request: MessageRetryRequest
):
    """Retry generating a response for a specific message."""
    try:
        result = memory_manager.retry_response(
            conversation_id,
            message_id,
            request.preserve_history
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        original_question = result["questions_asked"][-1]
        chat_request = QuestionRequest(
            question=original_question,
            conversation_id=conversation_id
        )
        return await chat_router.ask_question(chat_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
