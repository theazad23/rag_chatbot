from typing import List, Dict, Union
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings
from fastapi import UploadFile
import json
import logging
from app.services.code_processor import CodeProcessor, CodeFile

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.code_processor = CodeProcessor()

    async def process_upload(self, file: UploadFile) -> List[str]:
        """Process an uploaded file."""
        try:
            content = await file.read()
            if file.filename.endswith('.json'):
                return self.process_json_content(content)
            text = content.decode('utf-8')
            return self.process_text(text)
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding file: {e}")
            raise ValueError("File must be a valid text document")
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise

    def process_json_content(self, content: Union[bytes, str]) -> List[str]:
        """Process JSON content, with special handling for code repositories."""
        try:
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            
            # Parse JSON content
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content

            # Check if this is a code repository JSON
            if "files" in data and isinstance(data["files"], list):
                processed_files = self.code_processor.process_codebase_json(data)
                return self._create_searchable_chunks(processed_files)
            
            # Handle regular JSON
            formatted_json = json.dumps(data, indent=2)
            return self.process_text(formatted_json)

        except Exception as e:
            logger.error(f"Error processing JSON content: {e}")
            raise

    def _create_searchable_chunks(self, processed_files: Dict[str, CodeFile]) -> List[str]:
        """Create searchable chunks from processed code files."""
        chunks = []
        
        # Add codebase structure chunk
        structure = self.code_processor.get_file_structure(processed_files)
        chunks.append(f"Codebase Structure:\n{json.dumps(structure, indent=2)}")
        
        # Process each file
        for path, file in processed_files.items():
            # Add file metadata chunk
            metadata_chunk = (
                f"File: {path}\n"
                f"Type: {file.file_type}\n"
                f"Size: {file.size} bytes\n"
                f"Functions: {', '.join(f['name'] for f in file.functions)}\n"
                f"Classes: {', '.join(c['name'] for c in file.classes)}\n"
                f"Imports: {', '.join(file.imports)}\n"
            )
            chunks.append(metadata_chunk)
            
            # Split file content into chunks
            content_chunks = self.text_splitter.split_text(file.content)
            for chunk in content_chunks:
                chunks.append(f"File: {path}\nContent:\n{chunk}")
        
        return chunks

    def process_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        try:
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Successfully split text into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error splitting text: {e}")
            raise