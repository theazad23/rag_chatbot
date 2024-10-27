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
