from typing import List, Dict, Optional, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from app.config import settings
import json
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class PromptStrategy(str, Enum):
    STANDARD = "standard"
    ACADEMIC = "academic"
    CONCISE = "concise"
    CREATIVE = "creative"
    STEP_BY_STEP = "step_by_step"

class ResponseFormat(str, Enum):
    DEFAULT = "default"
    JSON = "json"
    MARKDOWN = "markdown"
    BULLET_POINTS = "bullet_points"

class ContextMode(str, Enum):
    STRICT = "strict"  # Only use provided context
    FLEXIBLE = "flexible"  # Allow going beyond context with clear indication

class ChatModelCallback(BaseCallbackHandler):
    """Callback handler for logging and monitoring chat model interactions."""
    
    def __init__(self):
        self.start_time = None
        self.total_tokens = 0
        
    def on_llm_start(self, *args, **kwargs):
        self.start_time = datetime.now()
        logger.info(f"Starting LLM call at {self.start_time}")
    
    def on_llm_end(self, *args, **kwargs):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        logger.info(f"LLM call completed in {duration:.2f} seconds")
    
    def on_llm_error(self, error: Exception, *args, **kwargs):
        logger.error(f"LLM error occurred: {str(error)}")

class ChatModel:
    """Enhanced chat model with configurable prompts and response formats."""
    
    def __init__(self):
        self.callbacks = [ChatModelCallback()]
        self.model = ChatOpenAI(
            model_name=settings.MODEL_NAME,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            model_kwargs={"top_p": settings.TOP_P},
            callbacks=self.callbacks
        )
        self._initialize_prompt_templates()

    def _get_system_prompt(self, context_mode: ContextMode) -> str:
        """Get the appropriate system prompt based on context mode."""
        if context_mode == ContextMode.STRICT:
            return """You are a helpful AI assistant that answers questions based strictly on the provided context. 
            The context will include two sections:
            1. 'Conversation History': Contains previous interactions that provide context for the current question
            2. 'Relevant Documents': Contains information to use in formulating your response
            
            Treat both sections as valid sources of information. When a question refers to something mentioned 
            in either the conversation history or relevant documents, use that information to provide an answer.
            
            If you cannot find a complete answer using either section, say 'I don't have enough information in 
            the provided context to answer that question.'
            
            Do not use any knowledge outside of these two context sections."""
        else:
            return """You are a helpful AI assistant that primarily answers questions based on the provided context. 
            The context includes both 'Conversation History' and 'Relevant Documents' sections - use both to 
            formulate your responses. When the answer can be found in either section, use that information first.
            
            When using information beyond the provided context, clearly indicate this by prefacing that part of 
            your response with '[Outside Context]:'. Always prioritize information from the provided context sections
            when available."""

    def _initialize_prompt_templates(self):
        """Initialize different prompt strategies with context mode support."""
        base_prompts = {
            PromptStrategy.STANDARD: {
                "human": "Context: {context}\n\nQuestion: {question}"
            },
            PromptStrategy.ACADEMIC: {
                "human": """Context: {context}

Question: {question}

Please provide a structured analysis with:
1. Main points
2. Supporting evidence from the context
3. Detailed explanation
4. If applicable, relevant information beyond the context (clearly marked)
5. Conclusion"""
            },
            PromptStrategy.CONCISE: {
                "human": "Context: {context}\n\nQuestion: {question}\n\nProvide a concise answer:"
            },
            PromptStrategy.CREATIVE: {
                "human": "Context: {context}\n\nQuestion: {question}"
            },
            PromptStrategy.STEP_BY_STEP: {
                "human": """Context: {context}

Question: {question}

Please break this down step by step:"""
            }
        }

        self.prompt_templates = {
            context_mode: {
                strategy: ChatPromptTemplate.from_messages([
                    ("system", self._get_system_prompt(context_mode)),
                    ("human", prompt["human"])
                ])
                for strategy, prompt in base_prompts.items()
            }
            for context_mode in ContextMode
        }

    def _format_context(self, context: List[str]) -> str:
        """Format context sections clearly for the model."""
        formatted_sections = []
        for section in context:
            if section.startswith('\nConversation History:'):
                formatted_sections.insert(0, section)  # Put conversation history first
            else:
                formatted_sections.append(section)
        return "\n\n".join(formatted_sections)

    def _format_response(self, response: str, format_type: ResponseFormat) -> str:
        """Format the response according to the specified format."""
        try:
            if format_type == ResponseFormat.DEFAULT:
                return response
            
            if format_type == ResponseFormat.JSON:
                sections = response.split('\n\n')
                return json.dumps({
                    "main_response": sections[0],
                    "additional_details": sections[1:] if len(sections) > 1 else [],
                    "generated_at": datetime.now().isoformat()
                }, indent=2)
                
            if format_type == ResponseFormat.MARKDOWN:
                lines = response.split('\n')
                formatted = []
                for line in lines:
                    if line.strip():
                        if line.startswith(('1.', '2.', '3.')):
                            formatted.append(f"\n{line}")
                        elif ':' in line:
                            title, content = line.split(':', 1)
                            formatted.append(f"### {title.strip()}\n{content.strip()}")
                        else:
                            formatted.append(line)
                return '\n\n'.join(formatted)
                
            if format_type == ResponseFormat.BULLET_POINTS:
                lines = response.split('\n')
                formatted = []
                for line in lines:
                    if line.strip():
                        if not line.startswith('•'):
                            formatted.append(f"• {line.strip()}")
                        else:
                            formatted.append(line)
                return '\n'.join(formatted)
                
            return response
            
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return response

    async def generate_response(
        self,
        question: str,
        context: List[str],
        strategy: PromptStrategy = PromptStrategy.STANDARD,
        response_format: ResponseFormat = ResponseFormat.DEFAULT,
        context_mode: ContextMode = ContextMode.STRICT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response with enhanced options and metadata.
        
        Args:
            question: The question to answer
            context: List of context strings
            strategy: The prompt strategy to use
            response_format: The desired response format
            context_mode: Whether to allow responses beyond the provided context
            metadata: Optional metadata to include in response
        
        Returns:
            Dict containing response and metadata
        """
        try:
            # Format context to clearly separate conversation history and documents
            formatted_context = self._format_context(context)
            
            # Log the formatted context for debugging
            logger.info(f"Formatted context:\n{formatted_context}")
            
            # Get the appropriate prompt template based on strategy and context mode
            prompt_template = self.prompt_templates[context_mode][strategy]
            
            # Generate prompt with formatted context
            prompt = prompt_template.format(
                context=formatted_context,
                question=question
            )
            
            # Get response from model
            response = self.model.invoke(prompt)
            
            # Format the response
            formatted_response = self._format_response(response.content, response_format)
            
            # Check if response contains outside context indicator
            uses_outside_context = "[Outside Context]:" in formatted_response
            
            # Prepare the result dictionary
            result = {
                "response": formatted_response,
                "metadata": {
                    "strategy": strategy,
                    "response_format": response_format,
                    "context_mode": context_mode,
                    "uses_outside_context": uses_outside_context,
                    "timestamp": datetime.now().isoformat(),
                    "model": settings.MODEL_NAME,
                    "context_chunks_used": len(context),
                    "has_conversation_history": any("Conversation History:" in c for c in context)
                }
            }
            
            # Add any additional metadata
            if metadata:
                result["metadata"].update(metadata)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
        
    def update_prompt_strategy(self, strategy: PromptStrategy, system_message: str, human_template: str):
        """
        Add or update a prompt strategy.
        
        Args:
            strategy: The strategy name to update
            system_message: The new system message
            human_template: The new human message template
        """
        try:
            self.prompt_templates[strategy] = ChatPromptTemplate.from_messages([
                ("system", system_message),
                ("human", human_template)
            ])
            logger.info(f"Successfully updated prompt strategy: {strategy}")
        except Exception as e:
            logger.error(f"Error updating prompt strategy: {e}")
            raise