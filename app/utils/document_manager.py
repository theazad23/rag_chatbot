from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentManager:
    def __init__(self, storage_dir: str = "document_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.documents: Dict[str, Dict] = self._load_documents()
        
    def _load_documents(self) -> Dict:
        """Load existing documents from storage."""
        index_file = self.storage_dir / "document_index.json"
        if index_file.exists():
            with open(index_file, "r") as f:
                return json.load(f)
        return {}

    def _save_documents(self) -> None:
        """Save document index to storage."""
        index_file = self.storage_dir / "document_index.json"
        with open(index_file, "w") as f:
            json.dump(self.documents, f, indent=2)

    def add_document(self, content: str, metadata: Dict) -> str:
        """Add a new document with metadata."""
        doc_id = self._generate_doc_id(content)
        
        # Save document content
        doc_file = self.storage_dir / f"{doc_id}.txt"
        with open(doc_file, "w") as f:
            f.write(content)
        
        # Update document index
        self.documents[doc_id] = {
            "metadata": metadata,
            "added_at": datetime.now().isoformat(),
            "file_path": str(doc_file),
            "chunks": [],
            "embeddings_updated": None
        }
        
        self._save_documents()
        logger.info(f"Added document {doc_id} with metadata: {metadata}")
        return doc_id

    def update_chunks(self, doc_id: str, chunks: List[str], chunk_metadata: List[Dict]) -> None:
        """Update document chunks after processing."""
        if doc_id in self.documents:
            self.documents[doc_id]["chunks"] = list(zip(chunks, chunk_metadata))
            self.documents[doc_id]["embeddings_updated"] = datetime.now().isoformat()
            self._save_documents()
            logger.info(f"Updated chunks for document {doc_id}")

    def get_document_content(self, doc_id: str) -> Optional[str]:
        """Get the content of a document."""
        if doc_id not in self.documents:
            logger.warning(f"Document {doc_id} not found")
            return None
            
        file_path = Path(self.documents[doc_id]["file_path"])
        if file_path.exists():
            with open(file_path, "r") as f:
                return f.read()
        return None

    def get_document_info(self, doc_id: str) -> Dict:
        """Get information about a document."""
        if doc_id not in self.documents:
            logger.warning(f"Document {doc_id} not found")
            return {}
            
        doc = self.documents[doc_id]
        return {
            "document_id": doc_id,
            "metadata": doc["metadata"],
            "added_at": doc["added_at"],
            "num_chunks": len(doc["chunks"]),
            "embeddings_updated": doc["embeddings_updated"]
        }

    def list_documents(self) -> List[Dict]:
        """List all documents with their metadata."""
        return [
            {
                "document_id": doc_id,
                "metadata": doc["metadata"],
                "added_at": doc["added_at"]
            }
            for doc_id, doc in self.documents.items()
        ]

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its content."""
        if doc_id not in self.documents:
            return False
            
        # Delete content file
        file_path = Path(self.documents[doc_id]["file_path"])
        if file_path.exists():
            file_path.unlink()
            
        # Remove from index
        del self.documents[doc_id]
        self._save_documents()
        
        logger.info(f"Deleted document {doc_id}")
        return True

    def search_documents(self, query: Dict[str, any]) -> List[Dict]:
        """Search documents by metadata."""
        results = []
        for doc_id, doc in self.documents.items():
            match = all(
                key in doc["metadata"] and doc["metadata"][key] == value
                for key, value in query.items()
            )
            if match:
                results.append(self.get_document_info(doc_id))
        return results

    def _generate_doc_id(self, content: str) -> str:
        """Generate a unique document ID."""
        return hashlib.md5(content.encode()).hexdigest()