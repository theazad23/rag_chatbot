from typing import List, Dict, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class ConversationMemory:
    def __init__(self, max_history: int = 5):
        self.conversations: Dict[str, List[Dict]] = {}
        self.max_history = max_history

    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = []
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
        
        logger.info(f"Added interaction to conversation {conversation_id}")

    def get_conversation_context(self, conversation_id: str, num_previous: int = 3) -> List[Dict]:
        """Get previous interactions for context."""
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found")
            return []
        
        history = self.conversations[conversation_id][-num_previous:]
        logger.info(f"Retrieved {len(history)} previous interactions for conversation {conversation_id}")
        return history

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
        """Delete a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        return False