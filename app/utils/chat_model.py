# app/utils/chat_model.py
from typing import List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class ChatModel:
    def __init__(self):
        self.model = ChatOpenAI(
            model_name=settings.MODEL_NAME,
            temperature=0.7,
            streaming=False,
            openai_api_key=settings.OPENAI_API_KEY  # Explicitly pass the API key
        )
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant. Answer the question based on the provided context. 
            If the answer cannot be found in the context, say 'I don't have enough information to answer that.' 
            Be concise but thorough in your responses."""),
            ("human", "Context: {context}\n\nQuestion: {question}")
        ])
    
    def generate_response(self, question: str, context: List[str]) -> str:
        """Generate a response based on the question and context."""
        try:
            # Combine context chunks into a single string
            context_text = "\n".join(context)
            
            # Generate prompt
            prompt = self.prompt_template.format(
                context=context_text,
                question=question
            )
            
            # Get response from model
            response = self.model.invoke(prompt)
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise