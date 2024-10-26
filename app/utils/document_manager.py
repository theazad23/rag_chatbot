# app/utils/document_manager.py
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
        self.documents: Dict[str, Dict] = {}
        self.load_existing_documents()
        logger.info(f"Initialized DocumentManager with storage directory: {storage_dir}")

    def load_existing_documents(self):
        """Load existing document records from storage."""
        index_file = self.storage_dir / "document_index.json"
        if index_file.exists():
            with open(index_file, 'r') as f:
                self.documents = json.load(f)
                logger.info(f"Loaded {len(self.documents)} existing documents")

    def save_document_index(self):
        """Save the current document index to storage."""
        index_file = self.storage_dir / "document_index.json"
        with open(index_file, 'w') as f:
            json.dump(self.documents, f, indent=2)
        logger.debug("Saved document index")

    def add_document(self, 
                    content: str, 
                    filename: str, 
                    metadata: Optional[Dict] = None) -> Tuple[str, Dict]:
        """Add a new document with metadata."""
        doc_id = self._generate_doc_id(content)
        
        if metadata is None:
            metadata = {}
            
        document_info = {
            "filename": filename,
            "content_hash": doc_id,
            "metadata": {
                **metadata,
                "filename": filename,
                "added_at": datetime.now().isoformat(),
                "file_size": len(content),
                "content_type": self._get_content_type(filename)
            },
            "chunks": [],
            "embeddings_updated": None
        }
        
        # Save content to file
        content_file = self.storage_dir / f"{doc_id}.txt"
        with open(content_file, 'w') as f:
            f.write(content)
            
        self.documents[doc_id] = document_info
        self.save_document_index()
        
        logger.info(f"Added document: {filename} with ID: {doc_id}")
        return doc_id, document_info

    def update_chunks(self, 
                     doc_id: str, 
                     chunks: List[str], 
                     chunk_metadata: Optional[List[Dict]] = None) -> bool:
        """Update document chunks after processing."""
        if doc_id not in self.documents:
            logger.warning(f"Document {doc_id} not found")
            return False
            
        if chunk_metadata is None:
            chunk_metadata = [{"index": i} for i in range(len(chunks))]
            
        self.documents[doc_id]["chunks"] = [
            {
                "content": chunk,
                "metadata": metadata
            }
            for chunk, metadata in zip(chunks, chunk_metadata)
        ]
        
        self.documents[doc_id]["embeddings_updated"] = datetime.now().isoformat()
        self.save_document_index()
        
        logger.info(f"Updated chunks for document {doc_id}: {len(chunks)} chunks")
        return True

    def get_document_content(self, doc_id: str) -> Optional[str]:
        """Get the content of a document."""
        if doc_id not in self.documents:
            return None
            
        content_file = self.storage_dir / f"{doc_id}.txt"
        if not content_file.exists():
            logger.error(f"Content file missing for document {doc_id}")
            return None
            
        with open(content_file, 'r') as f:
            return f.read()

    def get_document_info(self, doc_id: str) -> Optional[Dict]:
        """Get information about a document."""
        return self.documents.get(doc_id)

    def list_documents(self) -> List[Dict]:
        """List all documents with their metadata."""
        return [
            {
                "doc_id": doc_id,
                "filename": info["filename"],
                "added_at": info["metadata"]["added_at"],
                "num_chunks": len(info["chunks"]),
                "embeddings_updated": info["embeddings_updated"]
            }
            for doc_id, info in self.documents.items()
        ]

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its content."""
        if doc_id not in self.documents:
            return False
            
        # Delete content file
        content_file = self.storage_dir / f"{doc_id}.txt"
        if content_file.exists():
            content_file.unlink()
            
        # Remove from index
        del self.documents[doc_id]
        self.save_document_index()
        
        logger.info(f"Deleted document {doc_id}")
        return True

    def _generate_doc_id(self, content: str) -> str:
        """Generate a unique document ID."""
        return hashlib.md5(content.encode()).hexdigest()

    def _get_content_type(self, filename: str) -> str:
        """Determine content type from filename."""
        extension = Path(filename).suffix.lower()
        content_types = {
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.json': 'application/json'
        }
        return content_types.get(extension, 'text/plain')