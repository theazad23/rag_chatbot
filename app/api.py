from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging
from datetime import datetime

from app.utils.document_processor import DocumentProcessor
from app.utils.vector_store import VectorStore
from app.utils.chat_model import ChatModel, PromptStrategy, ResponseFormat, ContextMode
from app.utils.memory_manager import ConversationMemory
from app.utils.document_manager import DocumentManager

logger = logging.getLogger(__name__)

app = FastAPI(title="Enhanced RAG Chatbot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
document_processor = DocumentProcessor()
vector_store = VectorStore()
chat_model = ChatModel()
memory_manager = ConversationMemory()
document_manager = DocumentManager()

class QuestionRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    max_context: Optional[int] = 3
    strategy: Optional[PromptStrategy] = PromptStrategy.STANDARD
    response_format: Optional[ResponseFormat] = ResponseFormat.DEFAULT
    context_mode: Optional[ContextMode] = ContextMode.STRICT
    
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

@app.post("/conversation/create")
async def create_conversation():
    """Create a new conversation."""
    conversation_id = memory_manager.create_conversation()
    return {"conversation_id": conversation_id}

@app.get("/conversation/{conversation_id}/detail")
async def get_conversation_detail(
    conversation_id: str,
    message_limit: Optional[int] = Query(50, description="Maximum number of messages to return"),
    before_timestamp: Optional[str] = Query(None, description="Get messages before this timestamp")
) -> ConversationDetail:
    """
    Get detailed conversation information including message history.
    
    Args:
        conversation_id: The ID of the conversation
        message_limit: Maximum number of messages to return
        before_timestamp: Get messages before this timestamp (for pagination)
        
    Returns:
        Detailed conversation information including messages
    """
    try:
        # Get conversation history
        history = memory_manager.get_conversation_context(conversation_id, num_previous=message_limit)
        
        if not history:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        # Format messages for UI
        messages = []
        for interaction in history:
            # Add user question
            messages.append({
                "id": f"{conversation_id}_{len(messages)}",
                "role": "user",
                "content": interaction["question"],
                "timestamp": interaction["timestamp"],
                "metadata": {"type": "question"}
            })
            
            # Add assistant response
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
            
        # Get conversation summary
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
                "context_mode": "strict",  # or get from conversation settings
                "total_interactions": summary["total_interactions"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting conversation detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversation/{conversation_id}/continue")
async def continue_conversation(
    conversation_id: str,
    request: QuestionRequest
):
    """
    Continue an existing conversation.
    
    This endpoint ensures the conversation context is properly loaded
    before processing the new question.
    """
    try:
        # Verify conversation exists
        if not memory_manager.get_conversation_summary(conversation_id):
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        # Set the conversation_id in the request
        request.conversation_id = conversation_id
        
        # Use the existing ask endpoint logic
        return await ask_question(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error continuing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/conversation/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    title: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """
    Update conversation metadata (title, custom metadata, etc.)
    """
    try:
        # Get existing conversation
        conversation = memory_manager.get_conversation_summary(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        # Update conversation metadata
        updated = memory_manager.update_conversation_metadata(
            conversation_id,
            title=title,
            metadata=metadata
        )
        
        return {"message": "Conversation updated", "conversation": updated}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation summary and history."""
    return memory_manager.get_conversation_summary(conversation_id)

@app.get("/conversations")
async def list_conversations(
    limit: Optional[int] = Query(10, description="Maximum number of conversations to return"),
    offset: Optional[int] = Query(0, description="Number of conversations to skip"),
    sort_by: Optional[str] = Query("last_interaction", description="Field to sort by: 'last_interaction' or 'total_interactions'"),
    order: Optional[str] = Query("desc", description="Sort order: 'asc' or 'desc'")
):
    """
    List all conversations with pagination and sorting options.
    
    Args:
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip for pagination
        sort_by: Field to sort results by
        order: Sort order (ascending or descending)
        
    Returns:
        List of conversation summaries with metadata
    """
    try:
        # Get all conversations
        conversations = memory_manager.list_conversations()
        
        # Sort conversations
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
            
        # Apply pagination
        paginated_conversations = conversations[offset:offset + limit]
        
        # Get detailed information for each conversation
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
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    success = memory_manager.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted"}

@app.post("/document/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(..., description="Document title"),
    description: str = Form(default="", description="Document description")
):
    """Upload and process a document."""
    try:
        if not file.filename.endswith(('.txt', '.md')):
            raise HTTPException(
                status_code=400,
                detail="Only .txt and .md files are supported"
            )
        
        # Read and process document
        content = await file.read()
        text = content.decode()
        
        # Add to document manager
        metadata = {
            "title": title,
            "description": description,
            "filename": file.filename,
            "uploaded_at": datetime.now().isoformat()
        }
        doc_id = document_manager.add_document(text, metadata)
        
        # Process chunks
        chunks = document_processor.process_text(text)
        chunk_metadata = [{"index": i, "doc_id": doc_id} for i in range(len(chunks))]
        
        # Update document manager and vector store
        document_manager.update_chunks(doc_id, chunks, chunk_metadata)
        vector_store.add_texts(chunks)
        
        return {
            "message": "Document processed and stored successfully",
            "document_id": doc_id,
            "chunks_processed": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/document/{doc_id}")
async def get_document(doc_id: str):
    """Get document information."""
    doc_info = document_manager.get_document_info(doc_id)
    if not doc_info:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc_info

@app.get("/documents")
async def list_documents():
    """List all documents."""
    return document_manager.list_documents()

@app.delete("/document/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document."""
    success = document_manager.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted"}

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question with conversation history."""
    try:
        # Get conversation context if conversation_id is provided
        conversation_context = []
        if request.conversation_id:
            history = memory_manager.get_conversation_context(request.conversation_id)
            # Format previous interactions for context
            conversation_context = [
                f"Previous interaction {i+1}:\n"
                f"Question: {interaction['question']}\n"
                f"Answer: {interaction['response']['response']}"
                for i, interaction in enumerate(history)
            ]
        
        # Retrieve relevant context from vector store
        document_context = vector_store.query(
            request.question,
            n_results=request.max_context
        )
        
        # Combine both types of context
        combined_context = [
            "\nConversation History:\n" + "\n\n".join(conversation_context),
            "\nRelevant Documents:\n" + "\n\n".join(document_context)
        ] if conversation_context else document_context
        
        # Generate response using the chat model
        result = await chat_model.generate_response(
            question=request.question,
            context=combined_context,
            strategy=request.strategy,
            response_format=request.response_format,
            context_mode=request.context_mode,
            metadata={"conversation_id": request.conversation_id} if request.conversation_id else None
        )
        
        # Store interaction in conversation history
        if request.conversation_id:
            memory_manager.add_interaction(
                request.conversation_id,
                request.question,
                result,
                document_context  # Store only document context
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/maintenance/cleanup")
async def cleanup_old_conversations(
    max_age_days: int = Query(30, description="Delete conversations older than this many days")
):
    """Clean up old conversations."""
    deleted_count = memory_manager.cleanup_old_conversations(max_age_days)
    return {"message": f"Cleaned up {deleted_count} old conversations"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "vector_store": "operational",
            "document_manager": "operational",
            "memory_manager": "operational"
        }
    }