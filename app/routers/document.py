from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from datetime import datetime
from app.services import document_manager, document_processor, vector_store
import json
import xml.etree.ElementTree as ET

router = APIRouter(prefix="/document", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(..., description="Document title"),
    description: str = Form(default="", description="Document description")
):
    """Upload and process a document."""
    try:
        # Determine file type
        filename = file.filename
        extension = filename.split('.')[-1].lower()
        
        # Read and process file content based on type
        content = await file.read()
        if extension == "txt" or extension == "md":
            text = content.decode("utf-8")
        elif extension == "json":
            json_data = json.loads(content)
            text = json.dumps(json_data, indent=2)  # Convert JSON to a string
        elif extension == "xml":
            tree = ET.ElementTree(ET.fromstring(content.decode("utf-8")))
            text = ET.tostring(tree.getroot(), encoding="unicode")  # Convert XML to string
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only .txt, .md, .json, and .xml files are supported."
            )
        
        # Metadata for the document
        metadata = {
            "title": title,
            "description": description,
            "filename": filename,
            "uploaded_at": datetime.now().isoformat()
        }
        
        # Add document and process
        doc_id = document_manager.add_document(text, metadata)
        chunks = document_processor.process_text(text)
        chunk_metadata = [{"index": i, "doc_id": doc_id} for i in range(len(chunks))]
        
        document_manager.update_chunks(doc_id, chunks, chunk_metadata)
        vector_store.add_texts(chunks)
        
        return {
            "message": "Document processed and stored successfully",
            "document_id": doc_id,
            "chunks_processed": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doc_id}")
async def get_document(doc_id: str):
    """Get document information."""
    doc_info = document_manager.get_document_info(doc_id)
    if not doc_info:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc_info

@router.get("")
async def list_documents():
    """List all documents."""
    return document_manager.list_documents()

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document."""
    success = document_manager.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted"}