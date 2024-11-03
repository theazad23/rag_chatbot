from typing import List, Dict, Optional
from datetime import datetime
import uuid
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ConversationMemory:
    def __init__(self, storage_dir: str = "conversation_storage", max_history: int = 5):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict]] = self._load_conversations()
        
    def _get_conversation_path(self, conversation_id: str) -> Path:
        """Get the file path for a specific conversation."""
        return self.storage_dir / f"conversation_{conversation_id}.json"
        
    def _load_conversations(self) -> Dict[str, List[Dict]]:
        """Load all conversations from storage."""
        conversations = {}
        try:
            # Load each conversation file
            for conv_file in self.storage_dir.glob("conversation_*.json"):
                conv_id = conv_file.stem.replace("conversation_", "")
                with open(conv_file, "r") as f:
                    conversations[conv_id] = json.load(f)
            logger.info(f"Loaded {len(conversations)} conversations from storage")
            return conversations
        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
            return {}

    def _save_conversation(self, conversation_id: str) -> None:
        """Save a specific conversation to disk."""
        try:
            file_path = self._get_conversation_path(conversation_id)
            with open(file_path, "w") as f:
                json.dump(self.conversations[conversation_id], f, indent=2)
            logger.info(f"Saved conversation {conversation_id} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving conversation {conversation_id}: {e}")
            raise

    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = []
        self._save_conversation(conversation_id)
        logger.info(f"Created new conversation with ID: {conversation_id}")
        return conversation_id

    def add_interaction(self, conversation_id: str, question: str, response: Dict, context_used: List[str]) -> None:
        """Add a new interaction to the conversation history."""
        if conversation_id not in self.conversations:
            conversation_id = self.create_conversation()
            
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response,
            "context_used": context_used
        }
        
        self.conversations[conversation_id].append(interaction)
        
        # Keep only the most recent interactions
        if len(self.conversations[conversation_id]) > self.max_history:
            self.conversations[conversation_id].pop(0)
        
        # Save the updated conversation
        self._save_conversation(conversation_id)
        logger.info(f"Added interaction to conversation {conversation_id}")

    def get_conversation_context(self, conversation_id: str, num_previous: int = 3) -> List[Dict]:
        """Get previous interactions for context."""
        try:
            if conversation_id not in self.conversations:
                logger.warning(f"Conversation {conversation_id} not found")
                return []

            conversation = self.conversations[conversation_id]
            if not conversation:
                return []

            history = conversation[-num_previous:]
            logger.info(f"Retrieved {len(history)} previous interactions for conversation {conversation_id}")
            return history
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return []

    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get a summary of the conversation."""
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found")
            return {"error": "Conversation not found"}

        conversation = self.conversations[conversation_id]
        
        if not conversation:
            return {"error": "Empty conversation"}

        first_interaction = conversation[0]
        last_interaction = conversation[-1]
        
        return {
            "conversation_id": conversation_id,
            "total_interactions": len(conversation),
            "start_time": first_interaction["timestamp"],
            "last_interaction": last_interaction["timestamp"],
            "questions_asked": [inter["question"] for inter in conversation]
        }
        
    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get a summary of the conversation."""
        try:
            if conversation_id not in self.conversations:
                logger.warning(f"Conversation {conversation_id} not found")
                return {"error": "Conversation not found"}

            conversation = self.conversations[conversation_id]
            if not conversation:
                return {
                    "conversation_id": conversation_id,
                    "total_interactions": 0,
                    "start_time": datetime.now().isoformat(),
                    "last_interaction": datetime.now().isoformat(),
                    "questions_asked": []
                }

            first_interaction = conversation[0]
            last_interaction = conversation[-1]

            return {
                "conversation_id": conversation_id,
                "total_interactions": len(conversation),
                "start_time": first_interaction["timestamp"],
                "last_interaction": last_interaction["timestamp"],
                "questions_asked": [inter["question"] for inter in conversation]
            }
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {"error": f"Error getting conversation summary: {str(e)}"}    

    def list_conversations(self) -> List[Dict]:
        """List all conversations with their summaries."""
        return [
            {
                "conversation_id": conv_id,
                "interactions": len(conv),
                "last_interaction": conv[-1]["timestamp"] if conv else None
            }
            for conv_id, conv in self.conversations.items()
        ]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its storage."""
        if conversation_id not in self.conversations:
            return False
            
        # Delete the conversation file
        file_path = self._get_conversation_path(conversation_id)
        if file_path.exists():
            file_path.unlink()
            
        # Remove from memory
        del self.conversations[conversation_id]
        logger.info(f"Deleted conversation {conversation_id}")
        return True

    def cleanup_old_conversations(self, max_age_days: int = 30) -> int:
        """Clean up conversations older than specified days."""
        try:
            current_time = datetime.now()
            deleted_count = 0

            for conv_id in list(self.conversations.keys()):
                conversation = self.conversations[conv_id]
                if not conversation:  # Handle empty conversations
                    self.delete_conversation(conv_id)
                    deleted_count += 1
                    continue

                last_interaction = conversation[-1]["timestamp"]
                last_time = datetime.fromisoformat(last_interaction)
                age = (current_time - last_time).days

                if age > max_age_days:
                    self.delete_conversation(conv_id)
                    deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old conversations")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during conversation cleanup: {e}")
            return 0

    def edit_message(self, conversation_id: str, message_id: str, new_content: str, preserve_history: bool = True) -> Dict:
        """Edit a message in the conversation history."""
        try:
            if conversation_id not in self.conversations:
                logger.warning(f"Conversation {conversation_id} not found")
                return {"error": "Conversation not found"}

            msg_index = int(message_id.split('_')[1])
            conversation = self.conversations[conversation_id]
            
            if msg_index >= len(conversation):
                return {"error": "Message not found"}

            if preserve_history:
                new_conversation = conversation[:msg_index + 1]
                new_conversation[msg_index]["question"] = new_content
                new_conversation[msg_index]["edited_at"] = datetime.now().isoformat()
                self.conversations[conversation_id] = new_conversation
            else:
                conversation[msg_index]["question"] = new_content
                conversation[msg_index]["edited_at"] = datetime.now().isoformat()
                self.conversations[conversation_id] = conversation[:msg_index + 1]

            self._save_conversation(conversation_id)
            return self.get_conversation_summary(conversation_id)
            
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return {"error": str(e)}

    def retry_message(self, conversation_id: str, message_id: str, modified_content: Optional[str] = None, preserve_history: bool = True) -> Dict:
        """Retry a message with optional modifications."""
        try:
            if conversation_id not in self.conversations:
                return {"error": "Conversation not found"}

            conversation = self.conversations[conversation_id]
            msg_index = int(message_id.split('_')[1])

            if msg_index >= len(conversation):
                return {"error": "Message not found"}

            retry_content = modified_content if modified_content else conversation[msg_index].get("question", "")

            if preserve_history:
                new_conversation = conversation[:msg_index + 1]
                new_interaction = {
                    "timestamp": datetime.now().isoformat(),
                    "question": retry_content,
                    "response": {"response": ""},  # Initialize empty response
                    "previous_version": message_id,
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

        except Exception as e:
            logger.error(f"Error retrying message: {e}")
            return {"error": str(e)}

    def retry_response(self, conversation_id: str, message_id: str, preserve_history: bool = True) -> Dict:
        """Retry generating a response for a specific message."""
        try:
            if conversation_id not in self.conversations:
                return {"error": "Conversation not found"}

            conversation = self.conversations[conversation_id]
            msg_index = int(message_id.split('_')[1])

            if msg_index >= len(conversation):
                return {"error": "Message not found"}

            # Find the corresponding question
            question_index = msg_index - 1 if msg_index % 2 == 1 else msg_index
            if question_index < 0 or question_index >= len(conversation):
                return {"error": "Invalid message ID for response retry"}

            original_question = conversation[question_index]["question"]

            if preserve_history:
                new_conversation = conversation[:msg_index + 1]
                new_interaction = {
                    "timestamp": datetime.now().isoformat(),
                    "question": original_question,
                    "response": {"response": ""},  # Initialize empty response
                    "is_retry": True,
                    "previous_version": message_id
                }
                new_conversation.append(new_interaction)
                self.conversations[conversation_id] = new_conversation
            else:
                conversation[msg_index]["retry_count"] = conversation[msg_index].get("retry_count", 0) + 1
                conversation[msg_index]["timestamp"] = datetime.now().isoformat()
                self.conversations[conversation_id] = conversation[:msg_index + 1]

            self._save_conversation(conversation_id)
            return self.get_conversation_summary(conversation_id)

        except Exception as e:
            logger.error(f"Error retrying response: {e}")
            return {"error": str(e)}