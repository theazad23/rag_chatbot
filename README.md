# RAG Chatbot Project Summary

## Project Structure
```
rag_chatbot/
├── requirements.txt
├── .env
├── .gitignore
├── run.py
├── app/
│   ├── __init__.py
│   ├── api.py
│   ├── config.py
│   └── utils/
│       ├── __init__.py
│       ├── document_processor.py
│       ├── vector_store.py
│       ├── chat_model.py
│       ├── memory_manager.py
│       └── document_manager.py
├── document_storage/        # Added for document management
└── sample_data/            # Contains test documents
    ├── space_exploration.txt
    └── artificial_intelligence.txt
```

## Current Features
1. RAG (Retrieval Augmented Generation) functionality with:
   - Document processing and chunking
   - Vector storage using ChromaDB
   - GPT-4 Turbo for responses
   - text-embedding-3-large for embeddings

2. Multiple prompt strategies:
   - Standard
   - Academic
   - Concise
   - Creative
   - Step-by-Step

3. Different response formats:
   - Default
   - JSON
   - Markdown
   - Bullet Points

4. Context modes:
   - Strict (only uses provided context)
   - Flexible (can go beyond context with clear indication)

5. Document Management:
   - Document storage and retrieval
   - Metadata tracking
   - Chunk management

6. Conversation Memory:
   - Conversation history tracking
   - Context preservation
   - Conversation summaries

## Core Dependencies
```python
fastapi==0.109.2
uvicorn==0.27.1
python-dotenv==1.0.1
chromadb==0.4.22
langchain==0.1.9
langchain-openai==0.0.7
python-multipart==0.0.9
pydantic==2.6.1
pydantic-settings==2.1.0
openai==1.12.0
```

## Environment Variables
```
OPENAI_API_KEY=your-api-key-here
```

## Current API Endpoints
1. Document Management:
   - POST /document/upload
   - GET /document/{doc_id}
   - GET /documents
   - DELETE /document/{doc_id}

2. Conversation Management:
   - POST /conversation/create
   - GET /conversation/{conversation_id}
   - DELETE /conversation/{conversation_id}

3. Core Functionality:
   - POST /ask
   - GET /health

## Sample Usage
1. Upload Document:
```bash
curl -X POST \
  -F "file=@space_exploration.txt" \
  -F "title=Space Exploration Overview" \
  -F "description=Comprehensive guide about space exploration" \
  http://192.168.10.127:8000/document/upload
```

2. Create Conversation:
```bash
curl -X POST http://192.168.10.127:8000/conversation/create
```

3. Ask Question:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How is AI used in healthcare?",
    "conversation_id": "your-conversation-id",
    "strategy": "academic",
    "response_format": "markdown",
    "context_mode": "flexible"
  }' \
  http://192.168.10.127:8000/ask
```

## Recent Additions
- Conversation memory system
- Document management system
- Enhanced error handling
- Logging improvements
- Metadata tracking
- File-based document storage

## Potential Next Features
1. Analytics and Monitoring
2. API Rate Limiting
3. Source Attribution
4. Custom Plugins System
5. Streaming Responses
6. Caching System
7. Multi-Language Support
8. Enhanced Security Features

## Test Documents
The project includes two sample documents:
1. space_exploration.txt - Overview of space exploration history and future
2. artificial_intelligence.txt - Comprehensive overview of AI applications

## Running the Project
1. Set up virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Create .env file with OpenAI API key

4. Run the application:
```bash
python run.py
```

## In Depth Usage

### Conversation Management

#### Create New Conversation
```http
POST /conversation/create

Response:
{
    "conversation_id": "uuid-string"
}
```

#### Get Conversation Details
```http
GET /conversation/{conversation_id}/detail
Query Parameters:
- message_limit: int (default: 50)
- before_timestamp: string (optional)

Response:
{
    "conversation_id": "string",
    "title": "string",
    "created_at": "timestamp",
    "last_interaction": "timestamp",
    "total_messages": int,
    "messages": [
        {
            "id": "string",
            "role": "user" | "assistant",
            "content": "string",
            "timestamp": "string",
            "metadata": {}
        }
    ],
    "metadata": {
        "has_more": boolean,
        "context_mode": "string",
        "total_interactions": int
    }
}
```

#### Continue Conversation
```http
POST /conversation/{conversation_id}/continue
Body:
{
    "question": "string",
    "max_context": int (optional, default: 3),
    "strategy": "standard" | "academic" | "concise" | "creative" | "step_by_step",
    "response_format": "default" | "json" | "markdown" | "bullet_points",
    "context_mode": "strict" | "flexible"
}
```

#### Update Conversation
```http
PATCH /conversation/{conversation_id}
Body:
{
    "title": "string" (optional),
    "metadata": {} (optional)
}
```

#### List Conversations
```http
GET /conversations
Query Parameters:
- limit: int (default: 10)
- offset: int (default: 0)
- sort_by: "last_interaction" | "total_interactions"
- order: "asc" | "desc"

Response:
{
    "conversations": [...],
    "metadata": {
        "total": int,
        "returned": int,
        "offset": int,
        "limit": int,
        "sort_by": "string",
        "order": "string"
    }
}
```

#### Delete Conversation
```http
DELETE /conversation/{conversation_id}
```

### Document Management

#### Upload Document
```http
POST /document/upload
Form Data:
- file: File (.txt or .md)
- title: string
- description: string (optional)

Response:
{
    "message": "string",
    "document_id": "string",
    "chunks_processed": int
}
```

#### Get Document Info
```http
GET /document/{doc_id}

Response:
{
    "document_id": "string",
    "metadata": {
        "title": "string",
        "description": "string",
        "filename": "string",
        "uploaded_at": "timestamp"
    },
    "added_at": "timestamp",
    "num_chunks": int,
    "embeddings_updated": "timestamp"
}
```

#### List Documents
```http
GET /documents

Response:
[
    {
        "document_id": "string",
        "metadata": {...},
        "added_at": "timestamp"
    }
]
```

#### Delete Document
```http
DELETE /document/{doc_id}
```

### Question Answering

#### Ask Question
```http
POST /ask
Body:
{
    "question": "string",
    "conversation_id": "string" (optional),
    "max_context": int (optional, default: 3),
    "strategy": "standard" | "academic" | "concise" | "creative" | "step_by_step",
    "response_format": "default" | "json" | "markdown" | "bullet_points",
    "context_mode": "strict" | "flexible"
}

Response:
{
    "response": "string",
    "metadata": {
        "strategy": "string",
        "response_format": "string",
        "context_mode": "string",
        "uses_outside_context": boolean,
        "timestamp": "string",
        "model": "string",
        "context_chunks_used": int,
        "has_conversation_history": boolean,
        "conversation_id": "string" (if provided)
    }
}
```

## Best Practices

### 1. Conversation Management
- Create a new conversation for each distinct chat session
- Use conversation_id consistently for related questions
- Clean up old conversations periodically using the maintenance endpoint

### 2. Document Management
- Upload relevant documents before asking questions
- Use descriptive titles and metadata for documents
- Remove outdated documents to maintain knowledge base quality

### 3. Question Asking
- Choose appropriate prompt strategies:
  - `standard`: General purpose
  - `academic`: Detailed analysis
  - `concise`: Brief responses
  - `creative`: More engaging responses
  - `step_by_step`: Breaking down complex topics
- Select response format based on use case:
  - `default`: Natural text
  - `json`: Structured data
  - `markdown`: Formatted text
  - `bullet_points`: Listed items
- Use context modes appropriately:
  - `strict`: Only use provided context
  - `flexible`: Allow additional knowledge

### 4. Error Handling
- All endpoints return appropriate HTTP status codes
- Handle 404 for missing conversations/documents
- Check response metadata for context usage information

## Example Usage Flow

1. Create new conversation:
```http
POST /conversation/create
```

2. Upload knowledge base document:
```http
POST /document/upload
Form Data: {
    file: "space_exploration.txt",
    title: "Space Exploration Overview"
}
```

3. Ask initial question:
```http
POST /ask
{
    "question": "What are the major milestones in space exploration?",
    "conversation_id": "received-conversation-id",
    "strategy": "academic",
    "response_format": "markdown",
    "context_mode": "strict"
}
```

4. Ask follow-up question:
```http
POST /conversation/{conversation-id}/continue
{
    "question": "Can you elaborate on the Apollo program?",
    "strategy": "standard",
    "response_format": "default",
    "context_mode": "strict"
}
```

## Maintenance

### Cleanup Old Conversations
```http
POST /maintenance/cleanup
Query Parameters:
- max_age_days: int (default: 30)
```

### Health Check
```http
GET /health

Response:
{
    "status": "healthy",
    "components": {
        "vector_store": "operational",
        "document_manager": "operational",
        "memory_manager": "operational"
    }
}
```

