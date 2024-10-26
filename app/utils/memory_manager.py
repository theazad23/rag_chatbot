# app/utils/memory_manager.py
from typing import List, Dict, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

class ConversationMemory:
    def __init__(self, max_history: int = 5):
        self.conversations: Dict[str, List[Dict]] = {}
        self.max_history = max_history
        logger.info(f"Initialized ConversationMemory with max_history={max_history}")

    def start_conversation(self) -> str:
        """Start a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = []
        logger.info(f"Started new conversation with ID: {conversation_id}")
        return conversation_id

    def add_interaction(self, 
                       conversation_id: str, 
                       question: str, 
                       response: Dict, 
                       context_used: List[str]) -> None:
        """Add a new interaction to the conversation history."""
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found. Starting new conversation.")
            self.conversations[conversation_id] = []
            
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response["response"],
            "context_used": context_used,
            "metadata": response.get("metadata", {})
        }
        
        self.conversations[conversation_id].append(interaction)
        
        # Keep only the most recent interactions
        if len(self.conversations[conversation_id]) > self.max_history:
            self.conversations[conversation_id].pop(0)
            
        logger.debug(f"Added interaction to conversation {conversation_id}. "
                    f"Total interactions: {len(self.conversations[conversation_id])}")

    def get_conversation_context(self, 
                               conversation_id: str, 
                               num_previous: int = 3) -> List[Dict]:
        """Get previous interactions for context."""
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not found")
            return []
        
        history = self.conversations[conversation_id][-num_previous:]
        return [
            {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": item["question"] if i % 2 == 0 else item["response"]
            }
            for i, item in enumerate(history)
        ]

    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get a summary of the conversation."""
        if conversation_id not in self.conversations:
            return {"error": "Conversation not found"}
            
        conversation = self.conversations[conversation_id]
        if not conversation:
            return {"error": "Empty conversation"}
            
        return {
            "conversation_id": conversation_id,
            "total_interactions": len(conversation),
            "start_time": conversation[0]["timestamp"],
            "last_interaction": conversation[-1]["timestamp"],
            "questions_asked": [item["question"] for item in conversation]
        }

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        return False