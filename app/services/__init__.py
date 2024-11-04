from app.services.memory_manager import ConversationMemory
from app.services.document_manager import DocumentManager
from app.services.document_processor import DocumentProcessor
from app.services.code_processor import CodeProcessor
from app.services.vector_store import VectorStore
from app.services.chat_model import ChatModel

# Initialize service instances
memory_manager = ConversationMemory()
document_manager = DocumentManager()
document_processor = DocumentProcessor()
code_processor = CodeProcessor()
vector_store = VectorStore()
chat_model = ChatModel()

# Export instances
__all__ = [
    'memory_manager',
    'document_manager',
    'document_processor',
    'code_processor',
    'vector_store',
    'chat_model'
]