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
            openai_api_key=settings.OPENAI_API_KEY,  # Explicitly pass the API key
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            model_kwargs={"top_p": settings.TOP_P}  # Move top_p to model_kwargs to avoid warning
        )
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a highly knowledgeable AI assistant with expertise in analyzing and explaining complex topics. 
            Your responses should be comprehensive yet clear, drawing specifically from the provided context. 
            If the answer cannot be found in the context, say 'I don't have enough information in the provided context to answer that question.'
            Always maintain a confident, professional tone and organize your responses logically."""),
            ("human", """Context: {context}

Question: {question}

Please provide a well-structured response based on the context above. If possible, include specific details and examples from the provided context.""")
        ])
    
    def generate_response(self, question: str, context: List[str]) -> str:
        """Generate a response based on the question and context."""
        try:
            # Combine context chunks into a single string
            context_text = "\n\n".join(context)
            
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