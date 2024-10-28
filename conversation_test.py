import requests
import json
import time

class ConversationTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.conversation_id = None
        
    def print_response(self, response_data):
        """Pretty print the chatbot's response"""
        print("\nChatbot Response:")
        print("-" * 50)
        if isinstance(response_data, dict):
            print(response_data.get('response', 'No response found'))
            print("\nMetadata:")
            print(json.dumps(response_data.get('metadata', {}), indent=2))
        else:
            print(response_data)
        print("-" * 50)

    def run_context_test(self):
        """Run a sequence of tests to verify conversation context usage"""
        print("Starting Conversation Context Test...")
        
        # Step 1: Create a new conversation
        print("\n1. Creating new conversation...")
        response = requests.post(f"{self.base_url}/conversation/create")
        self.conversation_id = response.json()["conversation_id"]
        print(f"Conversation ID: {self.conversation_id}")
        
        # Step 2: Initial question setting context about AI in healthcare
        print("\n2. Setting initial context about AI in healthcare...")
        question1 = {
            "question": "What are the applications of AI in medical imaging and diagnosis?",
            "conversation_id": self.conversation_id,
            "strategy": "concise",
            "context_mode": "strict"
        }
        response = requests.post(f"{self.base_url}/ask", json=question1)
        self.print_response(response.json())
        
        # Step 3: Direct follow-up about accuracy
        print("\n3. Asking about accuracy of the medical imaging AI...")
        question2 = {
            "question": "How accurate is the AI at detecting diseases in medical images compared to human doctors?",
            "conversation_id": self.conversation_id,
            "strategy": "concise",
            "context_mode": "strict"
        }
        response = requests.post(f"{self.base_url}/ask", json=question2)
        self.print_response(response.json())
        
        # Step 4: Verify conversation history
        print("\n4. Checking conversation history...")
        response = requests.get(f"{self.base_url}/conversation/{self.conversation_id}")
        print("\nConversation Summary:")
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    tester = ConversationTester()
    tester.run_context_test()