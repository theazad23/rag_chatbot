from typing import List
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.EMBEDDING_MODEL
        )
        
        self.client = chromadb.Client(
            ChromaSettings(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                is_persistent=True
            )
        )
        self.collection = self.get_or_create_collection()
    
    def get_or_create_collection(self):
        """Get existing collection or create a new one."""
        try:
            return self.client.get_collection(
                name=settings.COLLECTION_NAME,
                embedding_function=self.embedding_function
            )
        except ValueError:
            return self.client.create_collection(
                name=settings.COLLECTION_NAME,
                embedding_function=self.embedding_function
            )
    
    def add_texts(self, texts: List[str]) -> None:
        """Add texts to the vector store."""
        try:
            # Create unique IDs for each chunk
            ids = [f"doc_{i}" for i in range(len(texts))]
            
            self.collection.add(
                documents=texts,
                ids=ids
            )
            logger.info(f"Successfully added {len(texts)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {e}")
            raise
    
    def query(self, query_text: str, n_results: int = 3) -> List[str]:
        """Query the vector store for similar texts."""
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results['documents'][0]
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            raise
