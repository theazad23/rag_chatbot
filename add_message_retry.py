#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directory(path: str) -> None:
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)

def update_file(file_path: str, content: str, mode: str = 'a') -> None:
    """Update a file with new content."""
    try:
        with open(file_path, mode) as f:
            f.write(content)
        logger.info(f"Updated {file_path}")
    except Exception as e:
        logger.error(f"Error updating {file_path}: {e}")
        raise

def main():
    # Define the base path for your project
    base_path = Path.cwd()
    app_path = base_path / "app"

    # Content for models/conversation.py additions
    conversation_models = """
# Add new models for message retry functionality
from pydantic import BaseModel
from typing import Optional, List, Dict

class MessageEditRequest(BaseModel):
    \"\"\"Schema for editing a message in a conversation\"\"\"
    new_content: str
    preserve_history: bool = True

class MessageRetryRequest(BaseModel):
    \"\"\"Schema for retrying a message or response\"\"\"
    preserve_history: bool = True
    modified_content: Optional[str] = None
"""

    # Content for memory_manager.py additions
    memory_manager_methods = """
    def edit_message(self, conversation_id: str, message_id: str, new_content: str, preserve_history: bool = True) -> Dict:
        \"\"\"Edit a message in the conversation history.\"\"\"
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found")
            return {"error": "Conversation not found"}

        try:
            msg_index = int(message_id.split('_')[1])
        except (IndexError, ValueError):
            return {"error": "Invalid message ID"}

        conversation = self.conversations[conversation_id]
        if msg_index >= len(conversation):
            return {"error": "Message not found"}

        if preserve_history:
            new_conversation = conversation[:msg_index]
            new_conversation[msg_index]["question"] = new_content
            self.conversations[conversation_id] = new_conversation
        else:
            conversation[msg_index]["question"] = new_content
            self.conversations[conversation_id] = conversation[:msg_index + 1]

        self._save_conversation(conversation_id)
        return self.get_conversation_summary(conversation_id)

    def retry_message(self, conversation_id: str, message_id: str, modified_content: Optional[str] = None, preserve_history: bool = True) -> Dict:
        \"\"\"Retry a message with optional modifications.\"\"\"
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found")
            return {"error": "Conversation not found"}

        try:
            msg_index = int(message_id.split('_')[1])
        except (IndexError, ValueError):
            return {"error": "Invalid message ID"}

        conversation = self.conversations[conversation_id]
        if msg_index >= len(conversation):
            return {"error": "Message not found"}

        original_message = conversation[msg_index]
        retry_content = modified_content if modified_content else original_message["question"]

        if preserve_history:
            new_conversation = conversation[:msg_index]
            new_interaction = {
                "timestamp": datetime.now().isoformat(),
                "question": retry_content,
                "previous_version": original_message.get("message_id"),
                "is_retry": True
            }
            new_conversation.append(new_interaction)
            self.conversations[conversation_id] = new_conversation
        else:
            conversation[msg_index]["question"] = retry_content
            conversation[msg_index]["timestamp"] = datetime.now().isoformat()
            conversation[msg_index]["is_retry"] = True
            self.conversations[conversation_id] = conversation[:msg_index + 1]

        self._save_conversation(conversation_id)
        return self.get_conversation_summary(conversation_id)

    def retry_response(self, conversation_id: str, message_id: str, preserve_history: bool = True) -> Dict:
        \"\"\"Retry generating a response for a specific message.\"\"\"
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found")
            return {"error": "Conversation not found"}

        try:
            msg_index = int(message_id.split('_')[1])
        except (IndexError, ValueError):
            return {"error": "Invalid message ID"}

        conversation = self.conversations[conversation_id]
        if msg_index >= len(conversation):
            return {"error": "Message not found"}

        original_message = conversation[msg_index]

        if preserve_history:
            new_conversation = conversation[:msg_index + 1]
            new_conversation[msg_index]["retry_count"] = original_message.get("retry_count", 0) + 1
            self.conversations[conversation_id] = new_conversation
        else:
            conversation[msg_index]["retry_count"] = original_message.get("retry_count", 0) + 1
            self.conversations[conversation_id] = conversation[:msg_index + 1]

        self._save_conversation(conversation_id)
        return self.get_conversation_summary(conversation_id)
"""

    # Content for new conversation endpoints
    conversation_endpoints = """
@router.patch("/{conversation_id}/messages/{message_id}/edit")
async def edit_message(
    conversation_id: str,
    message_id: str,
    request: MessageEditRequest
):
    \"\"\"Edit a message in the conversation.\"\"\"
    try:
        result = memory_manager.edit_message(
            conversation_id,
            message_id,
            request.new_content,
            request.preserve_history
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        if message_id.endswith("_user"):
            chat_request = QuestionRequest(
                question=request.new_content,
                conversation_id=conversation_id
            )
            return await chat_router.ask_question(chat_request)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{conversation_id}/messages/{message_id}/retry")
async def retry_message(
    conversation_id: str,
    message_id: str,
    request: MessageRetryRequest
):
    \"\"\"Retry a message with optional modifications.\"\"\"
    try:
        result = memory_manager.retry_message(
            conversation_id,
            message_id,
            request.modified_content,
            request.preserve_history
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        chat_request = QuestionRequest(
            question=request.modified_content or result["questions_asked"][-1],
            conversation_id=conversation_id
        )
        return await chat_router.ask_question(chat_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{conversation_id}/messages/{message_id}/retry-response")
async def retry_response(
    conversation_id: str,
    message_id: str,
    request: MessageRetryRequest
):
    \"\"\"Retry generating a response for a specific message.\"\"\"
    try:
        result = memory_manager.retry_response(
            conversation_id,
            message_id,
            request.preserve_history
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        original_question = result["questions_asked"][-1]
        chat_request = QuestionRequest(
            question=original_question,
            conversation_id=conversation_id
        )
        return await chat_router.ask_question(chat_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

    # Update files
    try:
        # Update models/conversation.py
        update_file(app_path / "models" / "conversation.py", conversation_models)

        # Update services/memory_manager.py
        memory_manager_path = app_path / "services" / "memory_manager.py"
        with open(memory_manager_path, 'r') as f:
            content = f.read()
        # Insert new methods before the last class closing bracket
        updated_content = content.replace("        return 0", f"        return 0\n{memory_manager_methods}")
        update_file(memory_manager_path, updated_content, 'w')

        # Update routers/conversation.py
        conversation_router_path = app_path / "routers" / "conversation.py"
        with open(conversation_router_path, 'r') as f:
            content = f.read()
        # Add new endpoints at the end of the file
        update_file(conversation_router_path, f"\n{conversation_endpoints}")

        logger.info("Successfully updated all files with message retry functionality")
        
    except Exception as e:
        logger.error(f"Error updating files: {e}")
        raise

if __name__ == "__main__":
    main()