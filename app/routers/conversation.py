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
import logging

logger = logging.getLogger(__name__)

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
        summary = memory_manager.get_conversation_summary(conversation_id)
        
        if not summary or "error" in summary:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = []
        for index, interaction in enumerate(history):
            # Add question message
            messages.append(ConversationMessage(
                id=f"{conversation_id}_{index*2}",
                role="user",
                content=interaction["question"],
                timestamp=interaction["timestamp"],
                metadata={"type": "question"}
            ))
            
            # Add response message
            messages.append(ConversationMessage(
                id=f"{conversation_id}_{index*2+1}",
                role="assistant",
                content=interaction["response"]["response"],
                timestamp=interaction["timestamp"],
                metadata={
                    "type": "response",
                    **interaction["response"].get("metadata", {})
                }
            ))

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation detail: {e}")
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
        summary = memory_manager.get_conversation_summary(conversation_id)
        if not summary or "error" in summary:
            raise HTTPException(status_code=404, detail="Conversation not found")

        updated_metadata = {}
        if title:
            updated_metadata["title"] = title
        if metadata:
            updated_metadata.update(metadata)

        if not updated_metadata:
            return {"message": "No updates provided", "conversation": summary}

        summary.setdefault("metadata", {})
        summary["metadata"].update(updated_metadata)

        memory_manager._save_conversation(conversation_id)

        return {
            "message": "Conversation updated",
            "conversation": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation {conversation_id}: {e}")
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
        # First check if conversation exists
        conversation = memory_manager.get_conversation_summary(conversation_id)
        if not conversation or "error" in conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Try to retry the message
        result = memory_manager.retry_message(
            conversation_id,
            message_id,
            request.modified_content,
            request.preserve_history
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        # Get the question to retry
        original_question = request.modified_content
        if not original_question:
            msg_index = int(message_id.split('_')[1])
            conversation = memory_manager.get_conversation_context(conversation_id)
            if msg_index < len(conversation):
                original_question = conversation[msg_index]["question"]
            else:
                raise HTTPException(status_code=404, detail="Message not found")

        # Create a new chat request
        chat_request = QuestionRequest(
            question=original_question,
            conversation_id=conversation_id
        )

        # Send the chat request
        return await chat_router.ask_question(chat_request)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{conversation_id}/messages/{message_id}/retry-response")
async def retry_response(
    conversation_id: str,
    message_id: str,
    request: MessageRetryRequest
):
    """Retry generating a response for a specific message."""
    try:
        # First verify the conversation exists
        summary = memory_manager.get_conversation_summary(conversation_id)
        if not summary or "error" in summary:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get the conversation history
        history = memory_manager.get_conversation_context(conversation_id)
        if not history:
            raise HTTPException(status_code=404, detail="Conversation history not found")

        # Parse the message index from the ID
        msg_parts = message_id.split('_')
        if len(msg_parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid message ID format")
            
        try:
            msg_index = int(msg_parts[1])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid message ID format")

        # Find the corresponding question
        interaction_index = msg_index // 2  # Each interaction has a question and response
        if interaction_index >= len(history):
            raise HTTPException(status_code=404, detail="Message not found")

        # Get the original question for this response
        original_question = history[interaction_index]["question"]

        # Create a mock response for testing
        # In production, this would trigger the actual AI model
        response_data = {
            "response": f"Regenerated response for: {original_question}",
            "metadata": {
                "is_retry": True,
                "original_message_id": message_id,
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id
            }
        }

        if request.preserve_history:
            # Add this as a new interaction
            memory_manager.add_interaction(
                conversation_id,
                original_question,
                response_data,
                []  # No context used for retry
            )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying response: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")