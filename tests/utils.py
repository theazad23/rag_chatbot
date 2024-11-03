from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

def print_response_debug(response: Any, message: str = "Response Debug"):
    """Helper function to print formatted debug information about a response."""
    debug_info = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "content": None
    }
    
    try:
        debug_info["content"] = response.json()
    except Exception:
        debug_info["content"] = response.text
        
    print(f"\n=== {message} ===")
    print(json.dumps(debug_info, indent=2))
    print("=" * 50)
    
    return debug_info

async def create_test_conversation(client: Any) -> Dict[str, Any]:
    """Helper function to create a test conversation with initial message."""
    # Create conversation
    conv_response = await client.post("/conversation")
    assert conv_response.status_code == 200
    conv_data = conv_response.json()
    
    # Add test message
    message_response = await client.post(
        "/ask",
        json={
            "question": "test question",
            "conversation_id": conv_data["conversation_id"]
        }
    )
    assert message_response.status_code == 200
    
    return conv_data