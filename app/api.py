from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
from app.utils.document_processor import DocumentProcessor
from app.utils.vector_store import VectorStore
from app.utils.chat_model import ChatModel
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Chatbot API")

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

class QuestionRequest(BaseModel):
    question: str
    max_context: Optional[int] = 3

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/status")
async def get_status():
    """Get the current status of the vector store."""
    try:
        stats = vector_store.get_collection_stats()
        return {
            "status": "healthy",
            "vector_store": stats,
            "model_info": {
                "language_model": settings.MODEL_NAME,
                "embedding_model": settings.EMBEDDING_MODEL
            }
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document."""
    try:
        if not file.filename.endswith(('.txt', '.md')):
            raise HTTPException(
                status_code=400,
                detail="Only .txt and .md files are supported"
            )
        
        chunks = await document_processor.process_upload(file)
        vector_store.add_texts(chunks)
        
        return {
            "message": "Document processed and stored successfully",
            "chunks_processed": len(chunks)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question about the uploaded documents."""
    try:
        # Retrieve relevant context from vector store
        context = vector_store.query(
            request.question,
            n_results=request.max_context
        )
        
        # Generate response using the chat model
        response = chat_model.generate_response(request.question, context)
        
        return {
            "response": response,
            "context_used": len(context)
        }
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")