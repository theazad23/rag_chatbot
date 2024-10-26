# app/utils/vector_store.py
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
    
    def get_next_id(self) -> int:
        """Get the next available ID based on existing documents."""
        try:
            # Get all existing IDs
            all_ids = self.collection.get()['ids']
            if not all_ids:
                return 0
            # Extract numbers from doc_X format
            existing_nums = [int(id.split('_')[1]) for id in all_ids]
            return max(existing_nums) + 1
        except Exception:
            return 0

    def add_texts(self, texts: List[str]) -> None:
        """Add texts to the vector store."""
        try:
            # Get the next available ID
            start_id = self.get_next_id()
            
            # Create unique IDs for each chunk
            ids = [f"doc_{i}" for i in range(start_id, start_id + len(texts))]
            
            # Add metadata about the chunks
            metadatas = [{"chunk_size": len(text), "chunk_index": i} for i, text in enumerate(texts)]
            
            self.collection.add(
                documents=texts,
                ids=ids,
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(texts)} documents to vector store. IDs from {ids[0]} to {ids[-1]}")
            
            # Log total documents in collection
            total_docs = len(self.collection.get()['ids'])
            logger.info(f"Total documents in collection: {total_docs}")
            
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {e}")
            raise
    
    def query(self, query_text: str, n_results: int = 3) -> List[str]:
        """Query the vector store for similar texts."""
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Log similarity scores and document IDs for debugging
            distances = results['distances'][0]
            ids = results.get('ids', [[]])[0]  # Get IDs of returned documents
            logger.info(f"Query: '{query_text}'")
            logger.info(f"Matching documents: {ids}")
            logger.info(f"Similarity scores: {distances}")
            
            return results['documents'][0]
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            raise

    def get_collection_stats(self) -> dict:
        """Get statistics about the current collection."""
        try:
            all_docs = self.collection.get()
            return {
                "total_documents": len(all_docs['ids']),
                "document_ids": all_docs['ids']
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise