from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Query
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

@app.post("/conversation/create")
async def create_conversation():
    """Create a new conversation."""
    conversation_id = memory_manager.create_conversation()
    return {"conversation_id": conversation_id}

@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation summary and history."""
    logger.info(conversation_id)
    return memory_manager.get_conversation_summary(conversation_id)

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
            conversation_context = memory_manager.get_conversation_context(request.conversation_id)
        
        # Retrieve relevant context from vector store
        context = vector_store.query(
            request.question,
            n_results=request.max_context
        )
        
        # Generate response using the chat model
        result = await chat_model.generate_response(
            question=request.question,
            context=context,
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
                context
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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