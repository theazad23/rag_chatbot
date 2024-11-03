import pytest
from httpx import AsyncClient
import json
from datetime import datetime
from typing import Dict, Any

pytestmark = pytest.mark.asyncio

# Helper functions
async def create_test_conversation(client: AsyncClient, initial_question: str = "What is RAG?") -> Dict[str, Any]:
    """Create a conversation and add initial message."""
    conv_response = await client.post("/conversation")
    assert conv_response.status_code == 200
    conv_data = conv_response.json()
    
    message_response = await client.post(
        "/ask",
        json={
            "question": initial_question,
            "conversation_id": conv_data["conversation_id"]
        }
    )
    assert message_response.status_code == 200
    
    return {
        "conversation_id": conv_data["conversation_id"],
        "first_response": message_response.json()
    }

# Conversation Flow Tests
async def test_full_conversation_flow(client: AsyncClient):
    """Test a complete conversation flow with multiple interactions."""
    # Start conversation
    conv_data = await create_test_conversation(client)
    conversation_id = conv_data["conversation_id"]
    
    # Follow-up questions to test context retention
    questions = [
        "Can you explain that in simpler terms?",
        "What are the main benefits?",
        "Can you give an example?"
    ]
    
    for question in questions:
        response = await client.post(
            "/ask",
            json={
                "question": question,
                "conversation_id": conversation_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        
        # Verify conversation detail after each interaction
        detail_response = await client.get(f"/conversation/{conversation_id}/detail")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert "messages" in detail_data
        assert len(detail_data["messages"]) >= 2  # At least one Q&A pair

# Document Management Tests
async def test_document_management(client: AsyncClient):
    """Test document upload, retrieval, and deletion."""
    # Upload document
    test_content = "This is a test document about RAG systems."
    files = {
        "file": ("test.txt", test_content.encode(), "text/plain"),
    }
    form_data = {
        "title": "Test Document",
        "description": "Test document for RAG system"
    }
    
    upload_response = await client.post(
        "/document/upload",
        files=files,
        data=form_data
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    doc_id = upload_data["document_id"]
    
    # Get document info
    info_response = await client.get(f"/document/{doc_id}")
    assert info_response.status_code == 200
    doc_info = info_response.json()
    assert doc_info["metadata"]["title"] == "Test Document"
    
    # List documents
    list_response = await client.get("/document")
    assert list_response.status_code == 200
    docs = list_response.json()
    assert len(docs) > 0
    assert any(doc["document_id"] == doc_id for doc in docs)
    
    # Ask question about uploaded document
    question_response = await client.post(
        "/ask",
        json={
            "question": "What is this document about?",
            "max_context": 3
        }
    )
    assert question_response.status_code == 200
    assert "RAG" in question_response.json()["response"]
    
    # Delete document
    delete_response = await client.delete(f"/document/{doc_id}")
    assert delete_response.status_code == 200

# Conversation Management Tests
async def test_conversation_management(client: AsyncClient):
    """Test conversation creation, listing, and deletion."""
    # Create multiple conversations
    conversations = []
    for i in range(3):
        conv_data = await create_test_conversation(
            client, 
            f"Test question {i+1}"
        )
        conversations.append(conv_data["conversation_id"])
    
    # List conversations
    list_response = await client.get("/conversation")
    assert list_response.status_code == 200
    conv_list = list_response.json()
    assert len(conv_list["conversations"]) >= len(conversations)
    
    # Test pagination and sorting
    paginated_response = await client.get(
        "/conversation",
        params={
            "limit": 2,
            "offset": 0,
            "sort_by": "last_interaction",
            "order": "desc"
        }
    )
    assert paginated_response.status_code == 200
    paginated_data = paginated_response.json()
    assert len(paginated_data["conversations"]) <= 2
    
    # Delete conversations
    for conv_id in conversations:
        delete_response = await client.delete(f"/conversation/{conv_id}")
        assert delete_response.status_code == 200

# Advanced Conversation Features
async def test_conversation_editing_and_retry(client: AsyncClient):
    """Test message editing, retry, and response regeneration."""
    # Create conversation
    conv_data = await create_test_conversation(client)
    conversation_id = conv_data["conversation_id"]
    
    # Get conversation detail
    detail_response = await client.get(f"/conversation/{conversation_id}/detail")
    assert detail_response.status_code == 200
    messages = detail_response.json()["messages"]
    
    # Edit a message
    first_message_id = messages[0]["id"]
    edit_response = await client.patch(
        f"/conversation/{conversation_id}/messages/{first_message_id}/edit",
        json={
            "new_content": "What are the key components of RAG?",
            "preserve_history": True
        }
    )
    assert edit_response.status_code == 200
    
    # Retry a message
    retry_response = await client.post(
        f"/conversation/{conversation_id}/messages/{first_message_id}/retry",
        json={"preserve_history": True}
    )
    assert retry_response.status_code == 200
    
    # Regenerate a response
    assistant_message = next(m for m in messages if m["role"] == "assistant")
    regen_response = await client.post(
        f"/conversation/{conversation_id}/messages/{assistant_message['id']}/retry-response",
        json={"preserve_history": True}
    )
    assert regen_response.status_code == 200

# Context and Response Format Tests
async def test_different_response_formats(client: AsyncClient):
    """Test different response formats and context modes."""
    conv_data = await create_test_conversation(client)
    conversation_id = conv_data["conversation_id"]
    
    formats = [
        ("default", None),
        ("json", "application/json"),
        ("markdown", "text/markdown"),
        ("bullet_points", "text/plain")
    ]
    
    for format_type, content_type in formats:
        response = await client.post(
            "/ask",
            json={
                "question": "What is RAG?",
                "conversation_id": conversation_id,
                "response_format": format_type
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        if format_type == "json":
            assert isinstance(json.loads(data["response"]), dict)

# Maintenance and Health Check Tests
async def test_maintenance_and_health(client: AsyncClient):
    """Test maintenance endpoints and health checks."""
    # Health check
    health_response = await client.get("/health")
    assert health_response.status_code == 200
    health_data = health_response.json()
    assert health_data["status"] == "healthy"
    assert all(v == "operational" for v in health_data["components"].values())
    
    # Create some old conversations
    conversations = []
    for _ in range(3):
        conv_data = await create_test_conversation(client)
        conversations.append(conv_data["conversation_id"])
    
    # Cleanup old conversations
    cleanup_response = await client.post(
        "/maintenance/cleanup",
        params={"max_age_days": 30}
    )
    assert cleanup_response.status_code == 200

# Error Handling Tests
async def test_error_handling(client: AsyncClient):
    """Test error handling for various scenarios."""
    error_cases = [
        # Invalid conversation ID
        {
            "endpoint": "/conversation/invalid-id/detail",
            "method": "get",
            "expected_status": 404
        },
        # Invalid question format
        {
            "endpoint": "/ask",
            "method": "post",
            "data": {"invalid": "request"},
            "expected_status": 422
        },
        # Invalid document ID
        {
            "endpoint": "/document/invalid-id",
            "method": "get",
            "expected_status": 404
        },
        # Invalid message retry
        {
            "endpoint": "/conversation/valid-id/messages/invalid-id/retry",
            "method": "post",
            "data": {"preserve_history": True},
            "expected_status": 404
        }
    ]
    
    for case in error_cases:
        if case["method"] == "get":
            response = await client.get(case["endpoint"])
        elif case["method"] == "post":
            response = await client.post(
                case["endpoint"],
                json=case.get("data", {})
            )
        
        assert response.status_code == case["expected_status"]
        error_data = response.json()
        assert "detail" in error_data