from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def process_upload(self, file: UploadFile) -> List[str]:
        """Process an uploaded file."""
        try:
            content = await file.read()
            text = content.decode('utf-8')
            return self.process_text(text)
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding file: {e}")
            raise ValueError("File must be a valid text document")
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise
    
    def process_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        try:
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Successfully split text into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error splitting text: {e}")
            raise
